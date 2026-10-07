"""tests/lut 공용 픽스처 -- lut/CONTRACT.md 만 근거로 만든 입력·독립 계산(피검 조회 함수를 쓰지 않는다).

- toy LUT: CONTRACT 7절 그대로(폭 1e-6·2e-6 슬라이스, 기준 LUT, LutSpec). 로드 거부 test 용으로 배열·manifest 를 바꿔 쓸 수 있다.
- 실데이터: 폭 슬라이스 manifest(`GMID_LUT_MANIFEST`), 기준 LUT npz(`GMID_LUT_CAP_NPZ`), PDK tech LEF(`GMID_PDK_TLEF`).
  경로가 없으면 skip 이 아니라 명시적 FAIL(데이터가 없어 검증을 못 했다는 사실을 숨기지 않는다). 마커 `lut_realdata`.
- 독립 경로: npz 를 numpy 로 직접 열어 격자점 값을 꺼내고, 보간·역보간·옛 `_solve_vgs` 규칙은 이 파일에서 따로 구현한다.
"""
from __future__ import annotations

import ast
import bisect
import functools
import hashlib
import json
import math
import os
import re
import shutil
from pathlib import Path

import numpy as np
import pytest

from gmid_engine.lut import LutMemo, LutSpec, load_lut_set

HERE = Path(__file__).resolve().parent
ENGINE_ROOT = HERE.parents[1]                       # .../gmid_engine
SKILL_DIR = ENGINE_ROOT.parent                      # .../analog-gmid-design
LUT_SRC = ENGINE_ROOT / "lut"
LEGACY_SR = SKILL_DIR / "legacy" / "sizing_recipe.py"

REALDATA_MARKER = "lut_realdata"

_DEFAULT_MANIFEST = r"C:\Users\HSLEE\Documents\Todoc\fpga\wt\_drafts\engine\lut_slices\manifest.json"
_DEFAULT_CAP = str(SKILL_DIR / "assets" / "sky130_nfet_pfet_lut_sample.npz")
_DEFAULT_TLEF = r"C:/pdk/sky130_fd_sc_hd/tech/sky130_fd_sc_hd.tlef"

# 실데이터 선언(test 쪽 PDK 선언): manifest device 이름 -> kind, kind -> 기준 LUT 열 접미사(기준 npz 의 열 이름 ID_n·CGG_p 등)
REAL_DEVICE_KINDS = (("nfet_01v8", "nmos"), ("pfet_01v8", "pmos"))
REAL_CAP_SUFFIX = (("nmos", "_n"), ("pmos", "_p"))


def pytest_configure(config):
    config.addinivalue_line(
        "markers",
        REALDATA_MARKER + ": 실데이터(폭 슬라이스·기준 LUT·PDK tlef) test -- 경로가 없으면 FAIL",
    )


# ---------------------------------------------------------------------------
# 공통: 실패 detail
# ---------------------------------------------------------------------------

def detail_of(exc):
    """실패 예외의 record.detail(키 정렬 쌍 tuple)을 dict 로. 정렬·형식도 함께 확인한다."""
    rec = exc.record
    det = rec.detail
    assert isinstance(det, tuple)
    keys = [k for k, _ in det]
    assert keys == sorted(keys), "detail 이 키 정렬 쌍 tuple 이 아니다: %r" % (det,)
    assert rec.devices == ()
    assert rec.margin is None
    return dict(det)


# ---------------------------------------------------------------------------
# toy LUT (CONTRACT 7절)
# ---------------------------------------------------------------------------

TOY_L = (1e-6, 2e-6, 3e-6)
TOY_VGS = (0.0, 0.5, 1.0)
TOY_VDS = (0.5, 1.0)
TOY_VS = (0.0, 0.5)
TOY_ID_VGS = (1e-7, 1e-6, 1e-5)
TOY_GM_RATIO = (20.0, 10.0, 4.0)
TOY_VS_FACTOR = (1.0, 0.5)
TOY_SPEC = LutSpec(1e-8, (("nmos", 1.5e-6),), (("toyn", "nmos"),), (("nmos", "_n"),))


def toy_id(scale=1.0, id_vgs=TOY_ID_VGS):
    ID = np.empty((3, 3, 2, 2))
    for iL, L in enumerate(TOY_L):
        for iG in range(3):
            for k in range(2):
                for s in range(2):
                    ID[iL, iG, k, s] = (1e-6 / L) * id_vgs[iG] * TOY_VS_FACTOR[s]
    return ID * scale


def toy_slice_arrays(W, scale=1.0, id_vgs=TOY_ID_VGS):
    """CONTRACT 7절 슬라이스. scale = 폭 배수(ID·GM·GDS 에 곱함)."""
    ID = toy_id(scale, id_vgs)
    GM = ID * np.asarray(TOY_GM_RATIO)[None, :, None, None]
    return {
        "W": np.float64(W),
        "L": np.asarray(TOY_L), "VGS": np.asarray(TOY_VGS), "VDS": np.asarray(TOY_VDS), "VS": np.asarray(TOY_VS),
        "ID": ID, "GM": GM, "GDS": ID / 10.0, "VTH": np.full(ID.shape, 0.4),
        "meta_json": np.str_('{"model_files_sha256": {}}'),
        "corner": np.str_("tt"), "temp_c": np.float64(27.0),
    }


CURVE_L = (1e-6, 2e-6)
CURVE_VDS = (0.5, 1.0)
CURVE_VS = (0.0, 0.5)


def curve_slice_arrays(W, vgs, ids, gm_over_id):
    """임의 곡선 슬라이스: (L, VDS, VS) 2점씩, 그 위에서 같은 VGS 곡선. GM = ID·gm_over_id."""
    n = len(vgs)
    ID = np.empty((2, n, 2, 2))
    ID[...] = np.asarray(ids, dtype=float)[None, :, None, None]
    GM = ID * np.asarray(gm_over_id, dtype=float)[None, :, None, None]
    return {
        "W": np.float64(W),
        "L": np.asarray(CURVE_L), "VGS": np.asarray(vgs, dtype=float),
        "VDS": np.asarray(CURVE_VDS), "VS": np.asarray(CURVE_VS),
        "ID": ID, "GM": GM, "GDS": ID / 10.0, "VTH": np.full(ID.shape, 0.4),
        "meta_json": np.str_('{"model_files_sha256": {}}'),
        "corner": np.str_("tt"), "temp_c": np.float64(27.0),
    }


def curve_cap_arrays(vgs):
    shp = (2, len(vgs), 2, 2)
    return {
        "L": np.asarray(CURVE_L), "VGS": np.asarray(vgs, dtype=float), "VDS": np.asarray(CURVE_VDS),
        "VS": np.asarray(CURVE_VS), "CGG_n": np.full(shp, 1e-15), "CGD_n": np.full(shp, 2e-16),
        "w_ref_m": np.float64(1e-6), "corner": np.str_("tt"), "temp_c": np.float64(27.0),
    }


@pytest.fixture
def curve_lut(toy_build):
    """curve_lut(vgs, ids, gm_over_id) -> (LutMemo, 독립 계산한 격자 곡선 g). 폭 키 100(W 1e-6) 한 장."""
    count = [0]

    def make(vgs, ids, gm_over_id):
        count[0] += 1
        a = curve_slice_arrays(1e-6, vgs, ids, gm_over_id)
        b = toy_build("curve%d" % count[0], slices=[("c.npz", "toyn", a)], cap=curve_cap_arrays(vgs))
        lut = b.load()
        lI, _ = log_floor(a["ID"])
        lG, _ = log_floor(a["GM"])
        g = np.exp(lG[0, :, 0, 0] - lI[0, :, 0, 0])
        return new_memo(lut), g
    return make


def toy_cap_arrays():
    shp = (3, 3, 2, 2)
    return {
        "L": np.asarray(TOY_L), "VGS": np.asarray(TOY_VGS), "VDS": np.asarray(TOY_VDS), "VS": np.asarray(TOY_VS),
        "CGG_n": np.full(shp, 1e-15), "CGD_n": np.full(shp, 2e-16),
        "w_ref_m": np.float64(1e-6), "corner": np.str_("tt"), "temp_c": np.float64(27.0),
    }


def sha256_file(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


class ToyBuild:
    """toy LUT 를 폴더에 쓴다. slices: [(file 이름, device, 배열 dict)], cap: 배열 dict 또는 None(파일 안 씀)."""

    def __init__(self, root, slices, cap, generator_sha256="0" * 64, sha_override=None, manifest_slices=None):
        self.root = Path(root)
        self.root.mkdir(parents=True, exist_ok=True)
        entries = []
        for fname, device, arrays in slices:
            p = self.root / fname
            if arrays is not None:
                np.savez(p, **arrays)
            entries.append({"device": device, "file": fname,
                            "sha256": sha256_file(p) if p.exists() else "f" * 64})
        if sha_override:
            for i, v in sha_override.items():
                entries[i]["sha256"] = v
        if manifest_slices is not None:
            entries = manifest_slices(entries)
        self.manifest = self.root / "manifest.json"
        with open(self.manifest, "w", encoding="utf-8") as f:
            json.dump({"generator_sha256": generator_sha256, "slices": entries, "ignored_key": 1}, f)
        self.cap = self.root / "cap_ref.npz"
        if cap is not None:
            np.savez(self.cap, **cap)

    def load(self, spec=TOY_SPEC):
        return load_lut_set(str(self.manifest), str(self.cap), spec)


def standard_toy_slices():
    return [("toy_w100.npz", "toyn", toy_slice_arrays(1e-6, 1.0)),
            ("toy_w200.npz", "toyn", toy_slice_arrays(2e-6, 2.0))]


@pytest.fixture
def toy_build(tmp_path):
    """toy_build(sub, slices=None, cap=None, ...) -> ToyBuild. 기본은 CONTRACT 7절 그대로."""
    def make(sub="toy", slices=None, cap="default", **kw):
        if slices is None:
            slices = standard_toy_slices()
        if isinstance(cap, str) and cap == "default":
            cap = toy_cap_arrays()
        return ToyBuild(tmp_path / sub, slices, cap, **kw)
    return make


@pytest.fixture
def toy(toy_build):
    return toy_build().load()


def new_memo(lut, n=256):
    return LutMemo(lut, point=n, curve=n, root=n)


@pytest.fixture
def toy_memo(toy):
    return new_memo(toy)


# ---------------------------------------------------------------------------
# 독립 수치 경로 (피검 함수 미사용)
# ---------------------------------------------------------------------------

def log_floor(arr):
    """CONTRACT 1.4: ln(clip(배열, 그 배열의 최소 양수값))."""
    arr = np.asarray(arr, dtype=float)
    floor = float(arr[arr > 0].min())
    return np.log(np.clip(arr, floor, None)), floor


def axis_cell(grid, x):
    """다중선형 보간의 축 칸 (i, f) -- 축 안 x 만."""
    g = list(grid)
    n = len(g)
    if x == g[-1]:
        return n - 2, 1.0
    i = bisect.bisect_right(g, x) - 1
    i = min(max(i, 0), n - 2)
    return i, (x - g[i]) / (g[i + 1] - g[i])


def interp4(grids, arr, point):
    """4축 다중선형 보간(독립 구현)."""
    cells = [axis_cell(g, x) for g, x in zip(grids, point)]
    total = 0.0
    for corner in range(16):
        w = 1.0
        idx = []
        for d in range(4):
            b = (corner >> d) & 1
            i, f = cells[d]
            w *= f if b else (1.0 - f)
            idx.append(i + b)
        total += w * float(arr[tuple(idx)])
    return total


def legacy_solve_vgs(g, vgs_grid, gm_id):
    """옛 `_solve_vgs` 구간 선택(전 구간 가장 오른쪽) + 2점 역보간 -- legacy/sizing_recipe.py 문장 그대로 옮김."""
    g = np.asarray(g, dtype=float)
    vgs_grid = np.asarray(vgs_grid, dtype=float)
    d = g - gm_id
    idx = np.flatnonzero(d[:-1] * d[1:] <= 0.0)
    if idx.size == 0:
        raise ValueError("no root")
    i = int(idx[-1])
    return _two_point(g, vgs_grid, i, gm_id)


def _two_point(g, vgs_grid, i, gm_id):
    ga, gb = g.item(i), g.item(i + 1)
    va, vb = vgs_grid.item(i), vgs_grid.item(i + 1)
    if ga <= gb:
        x0, x1, y0, y1 = ga, gb, va, vb
    else:
        x0, x1, y0, y1 = gb, ga, vb, va
    if x1 == x0:
        return vb
    return (y1 - y0) / (x1 - x0) * (gm_id - x0) + y0


def branch_solve_vgs(g, vgs_grid, gm_id):
    """CONTRACT 3절 정본 규칙의 독립 구현: 정점 p 이상 구간 중 가장 오른쪽, 없으면 None."""
    g = np.asarray(g, dtype=float)
    vgs_grid = np.asarray(vgs_grid, dtype=float)
    p = int(np.argmax(g))
    d = g - gm_id
    cand = [i for i in range(p, len(g) - 1) if d[i] * d[i + 1] <= 0.0]
    if not cand:
        return None
    return _two_point(g, vgs_grid, cand[-1], gm_id)


def lin_interp(xs, ys, x):
    """오름차순 xs 위 단순 선형 보간(독립)."""
    xs = list(xs)
    i = min(max(bisect.bisect_right(xs, x) - 1, 0), len(xs) - 2)
    return ys[i] + (ys[i + 1] - ys[i]) * (x - xs[i]) / (xs[i + 1] - xs[i])


# ---------------------------------------------------------------------------
# AST 해시 (CONTRACT 6절)
# ---------------------------------------------------------------------------

def _strip_doc(body):
    if body and isinstance(body[0], ast.Expr) and isinstance(getattr(body[0], "value", None), ast.Constant) \
            and isinstance(body[0].value.value, str):
        return list(body[1:])
    return list(body)


def find_function(path, name):
    tree = ast.parse(Path(path).read_text(encoding="utf-8"))
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and node.name == name:
            return node
    raise AssertionError("%s 에 함수 %s 없음" % (path, name))


def function_body(path, name):
    return _strip_doc(find_function(path, name).body)


def anchored_block(path, func, first, last):
    """함수 안 문장 목록(중첩 포함)에서 unparse 가 first 로 시작하는 문장 ~ last 로 시작하는 문장."""
    fn = find_function(path, func)
    for node in ast.walk(fn):
        for field in ("body", "orelse", "finalbody", "handlers"):
            stmts = getattr(node, field, None)
            if not isinstance(stmts, list) or not stmts or not isinstance(stmts[0], ast.stmt):
                continue
            srcs = [ast.unparse(s) for s in stmts]
            a = [i for i, s in enumerate(srcs) if s.startswith(first)]
            if not a:
                continue
            b = [i for i, s in enumerate(srcs) if s.startswith(last) and i >= a[0]]
            if b:
                return stmts[a[0]:b[0] + 1]
    raise AssertionError("%s:%s 에서 앵커 (%r, %r) 구간을 못 찾음" % (path, func, first, last))


class _Rename(ast.NodeTransformer):
    def __init__(self, names, attrs):
        self.names, self.attrs = names, attrs

    def visit_Name(self, node):
        if node.id in self.names:
            node.id = self.names[node.id]
        return node

    def visit_Attribute(self, node):
        self.generic_visit(node)
        if node.attr in self.attrs:
            node.attr = self.attrs[node.attr]
        return node


def ast_sha(stmts, names=None, attrs=None):
    mod = ast.Module(body=list(stmts), type_ignores=[])
    if names or attrs:
        mod = _Rename(names or {}, attrs or {}).visit(mod)
    return hashlib.sha256(ast.dump(mod, include_attributes=False).encode("utf-8")).hexdigest()


# ---------------------------------------------------------------------------
# 실데이터
# ---------------------------------------------------------------------------

def _need(env, default, what):
    p = os.environ.get(env, default)
    if not p or not Path(p).is_file():
        pytest.fail("실데이터 없음: %s (%s=%r). 실데이터 test 는 skip 하지 않는다 -- 경로를 주거나 파일을 놓을 것"
                    % (what, env, p), pytrace=False)
    return p


@pytest.fixture(scope="session")
def real_paths():
    return {
        "manifest": _need("GMID_LUT_MANIFEST", _DEFAULT_MANIFEST, "폭 슬라이스 manifest.json"),
        "cap": _need("GMID_LUT_CAP_NPZ", _DEFAULT_CAP, "기준 LUT npz"),
        "tlef": _need("GMID_PDK_TLEF", _DEFAULT_TLEF, "PDK tech LEF"),
    }


def manufacturing_grid_m(tlef_path):
    """tlef 의 MANUFACTURINGGRID(µm, DATABASE MICRONS) -> m."""
    text = Path(tlef_path).read_text(encoding="utf-8", errors="replace")
    m = re.search(r"^\s*MANUFACTURINGGRID\s+([0-9.eE+-]+)\s*;", text, re.M)
    assert m, "tlef 에 MANUFACTURINGGRID 없음"
    return float(m.group(1)) * 1e-6


@pytest.fixture(scope="session")
def real_manifest(real_paths):
    with open(real_paths["manifest"], encoding="utf-8") as f:
        return json.load(f)


@pytest.fixture(scope="session")
def real_slice_files(real_paths, real_manifest):
    """[(kind, device, W, w_key, path)] -- npz 의 W 를 직접 읽어 w_key = round(W / grid)."""
    grid = manufacturing_grid_m(real_paths["tlef"])
    dk = dict(REAL_DEVICE_KINDS)
    base = Path(real_paths["manifest"]).parent
    out = []
    for s in real_manifest["slices"]:
        p = base / s["file"]
        with np.load(p) as z:
            W = float(z["W"])
        out.append((dk[s["device"]], s["device"], W, int(round(W / grid)), str(p)))
    return sorted(out, key=lambda t: (t[0], t[3]))


@pytest.fixture(scope="session")
def real_spec(real_paths, real_slice_files):
    """grid = tlef MANUFACTURINGGRID, min_finger_w_m = kind 별 슬라이스 최소 W(데이터에서 유도)."""
    grid = manufacturing_grid_m(real_paths["tlef"])
    mins = {}
    for kind, _, W, _, _ in real_slice_files:
        mins[kind] = min(W, mins.get(kind, W))
    return LutSpec(grid, tuple(sorted(mins.items())), REAL_DEVICE_KINDS, REAL_CAP_SUFFIX)


@pytest.fixture(scope="session")
def real_lut(real_paths, real_spec):
    return load_lut_set(real_paths["manifest"], real_paths["cap"], real_spec)


@pytest.fixture
def real_memo(real_lut):
    return new_memo(real_lut, 4096)


@functools.lru_cache(maxsize=6)
def _load_raw(path):
    with np.load(path) as z:
        return {k: np.array(z[k]) for k in z.files}


@pytest.fixture(scope="session")
def raw_slice(real_slice_files):
    """raw_slice(kind, w_key) -> npz 배열 dict(직접 읽음)."""
    table = {(k, wk): p for k, _, _, wk, p in real_slice_files}

    def get(kind, w_key):
        return _load_raw(table[(kind, w_key)])
    return get


@pytest.fixture(scope="session")
def raw_cap(real_paths):
    return _load_raw(real_paths["cap"])


def copy_tree(src_dir, dst_dir):
    shutil.copytree(src_dir, dst_dir)
    return Path(dst_dir)


def rel_close(a, b, rel):
    return abs(a - b) <= rel * max(abs(a), abs(b))


def ulp_steps_off_grid(W, grid):
    r = W / grid
    return abs(r - round(r)) / math.ulp(r)
