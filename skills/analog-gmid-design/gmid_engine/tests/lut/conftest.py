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
TOY_VS_FACTOR = (1.0, 0.5)
TOY_SPEC = LutSpec(1e-8, (("nmos", 1.5e-6),), (("toyn", "nmos"),), (("nmos", "_n"),))

# [r5] CONTRACT 7.1 r5 toy: ID = (1e-6/L)·1e-7·exp(20v − 6v²)·exp(0.1·VDS)·(1, 0.5)[s], GM = ID·(20 − 12v), GDS = ID·0.1
R5_A, R5_B, R5_C = 20.0, 6.0, 0.1                  # lnID = ln1e-7 + A·v − B·v² + C·d
# [r5] CONTRACT 7.2 r4 toy (FC 위반 예시)
R4_ID_VGS = (1e-7, 1e-6, 1e-5)
R4_GM_RATIO = (20.0, 10.0, 4.0)


def toy_id(scale=1.0):
    """r5 toy ID (CONTRACT 7.1)."""
    ID = np.empty((3, 3, 2, 2))
    for iL, L in enumerate(TOY_L):
        for iG, v in enumerate(TOY_VGS):
            for k, d in enumerate(TOY_VDS):
                for s in range(2):
                    ID[iL, iG, k, s] = ((1e-6 / L) * 1e-7 * math.exp(R5_A * v - R5_B * v * v)
                                        * math.exp(R5_C * d) * TOY_VS_FACTOR[s])
    return ID * scale


def _toy_dict(W, ID, GM, GDS):
    return {
        "W": np.float64(W),
        "L": np.asarray(TOY_L), "VGS": np.asarray(TOY_VGS), "VDS": np.asarray(TOY_VDS), "VS": np.asarray(TOY_VS),
        "ID": ID, "GM": GM, "GDS": GDS, "VTH": np.full(ID.shape, 0.4),
        "meta_json": np.str_('{"model_files_sha256": {}}'),
        "corner": np.str_("tt"), "temp_c": np.float64(27.0),
    }


def toy_slice_arrays(W, scale=1.0):
    """[r5] CONTRACT 7.1 r5 toy 슬라이스. scale = 폭 배수(ID·GM·GDS 에 곱함)."""
    ID = toy_id(scale)
    GM = ID * (R5_A - 2 * R5_B * np.asarray(TOY_VGS))[None, :, None, None]
    return _toy_dict(W, ID, GM, ID * R5_C)


def r4_toy_slice_arrays(W, scale=1.0):
    """[r5] CONTRACT 7.2 r4 toy 슬라이스(FC 위반 예시): ID 는 VDS 무관, GM = ID·(20, 10, 4), GDS = ID/10."""
    ID = np.empty((3, 3, 2, 2))
    for iL, L in enumerate(TOY_L):
        for iG in range(3):
            for k in range(2):
                for s in range(2):
                    ID[iL, iG, k, s] = (1e-6 / L) * R4_ID_VGS[iG] * TOY_VS_FACTOR[s]
    ID = ID * scale
    GM = ID * np.asarray(R4_GM_RATIO)[None, :, None, None]
    return _toy_dict(W, ID, GM, ID / 10.0)


def r5_toy_lnid(v, d, s_vs, L=1e-6):
    """CONTRACT 7.1 닫힌 식(폭 1e-6): ln ID(v, d, vsb) -- VS 선형 = ln(0.5)·vsb/0.5."""
    return (math.log(1e-6 / L) + math.log(1e-7) + R5_A * v - R5_B * v * v + R5_C * d
            + math.log(0.5) * s_vs / 0.5)


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


def r4_toy_slices():
    return [("toy_w100.npz", "toyn", r4_toy_slice_arrays(1e-6, 1.0)),
            ("toy_w200.npz", "toyn", r4_toy_slice_arrays(2e-6, 2.0))]


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


@pytest.fixture
def r4toy(toy_build):
    """[r5] CONTRACT 7.2 r4 toy(FC 위반 예시) LutSet."""
    return toy_build("r4toy", slices=r4_toy_slices()).load()


@pytest.fixture
def r4toy_memo(r4toy):
    return new_memo(r4toy)


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
# [r5] 독립 Hermite 경로 (CONTRACT 1.4·3절·4.2·5절의 식을 이 파일에서 따로 구현 -- 피검 함수 미사용)
#  - 엔진은 같은 다항식을 Bernstein 제어점의 de Casteljau 로 계산한다(4.2). 여기서는 기저 함수 h00..h11 형태로
#    계산해 계산 경로가 다르다(격자 밖 비교는 상대 1e-12 수준, 격자점은 비트 단위).
# ---------------------------------------------------------------------------

HERMITE_N = 3                                   # CONTRACT 1.4: n = Hermite 차수 = 3


def hermite_val(y0, y1, m0, m1, h, t):
    """CONTRACT 4.2: p = y0·h00 + h·m0·h10 + y1·h01 + h·m1·h11."""
    t2 = t * t
    t3 = t2 * t
    return (y0 * (2 * t3 - 3 * t2 + 1) + h * m0 * (t3 - 2 * t2 + t)
            + y1 * (-2 * t3 + 3 * t2) + h * m1 * (t3 - t2))


def hermite_der(y0, y1, m0, m1, h, t):
    """CONTRACT 4.2: p'(x) = dp/dt / h."""
    t2 = t * t
    return (y0 * (6 * t2 - 6 * t) + h * m0 * (3 * t2 - 4 * t + 1)
            + y1 * (-6 * t2 + 6 * t) + h * m1 * (3 * t2 - 2 * t)) / h


def fc_ok(y0, y1, m0, m1, h):
    """CONTRACT 1.4 Fritsch–Carlson 단조 조건(필요충분, 원소마다, numpy 가능)."""
    b0 = m0 * h
    b2 = m1 * h
    b1 = HERMITE_N * (y1 - y0) - b0 - b2
    q = b1 * b1 <= b0 * b2
    inc = (b0 >= 0) & (b2 >= 0) & ((b1 >= 0) | q)
    dec = (b0 <= 0) & (b2 <= 0) & ((b1 <= 0) | q)
    return inc | dec


def axis_cell_r5(grid, x):
    """CONTRACT 4.2 칸 규칙: i = min(max(bisect_right − 1, 0), n − 2), t = (x − g_i)/(g_{i+1} − g_i)."""
    g = list(grid)
    i = min(max(bisect.bisect_right(g, x) - 1, 0), len(g) - 2)
    return i, (x - g[i]) / (g[i + 1] - g[i])


def axis_weights(grid, x):
    """선형 가중치 ((index, w), ...) -- 가중치 0 인 마디는 뺀다(읽지 않음)."""
    i, t = axis_cell_r5(grid, x)
    return tuple((j, w) for j, w in ((i, 1.0 - t), (i + 1, t)) if w != 0.0)


class RefSlice:
    """npz 배열 dict -> 독립 계산용 로그 배열·마스크·FC 표(CONTRACT 1.4 [r5] 보조 필드의 독립 구현)."""

    def __init__(self, z):
        self.grids = tuple(tuple(float(x) for x in np.asarray(z[a], dtype=float)) for a in AXES_T)
        self.w_m = float(z["W"])
        ID, GM, GDS = (np.asarray(z[x], dtype=float) for x in ("ID", "GM", "GDS"))
        self.lI, self.lG, self.lD = log_floor(ID)[0], log_floor(GM)[0], log_floor(GDS)[0]
        self.vth = np.asarray(z["VTH"], dtype=float)
        self.on = (ID > 0) & (GM > 0)
        self.vds_ok = (ID > 0) & (GDS > 0)
        self.gmid = np.exp(self.lG - self.lI)
        self.gdsid = np.exp(self.lD - self.lI)
        VGS, VDS = np.asarray(self.grids[1]), np.asarray(self.grids[2])
        hg = np.diff(VGS)[None, :, None, None]
        hd = np.diff(VDS)[None, None, :, None]
        self.herm_vgs = self.on[:, :-1] & self.on[:, 1:]
        self.fc_vgs = np.where(self.herm_vgs, fc_ok(self.lI[:, :-1], self.lI[:, 1:], self.gmid[:, :-1],
                                                    self.gmid[:, 1:], hg), True)
        self.herm_vds = self.vds_ok[:, :, :-1] & self.vds_ok[:, :, 1:]
        self.fc_vds = np.where(self.herm_vds, fc_ok(self.lI[:, :, :-1], self.lI[:, :, 1:], self.gdsid[:, :, :-1],
                                                    self.gdsid[:, :, 1:], hd), True)

    def hermite_fc(self):
        return (("VDS", int(self.herm_vds.sum()), int((~self.fc_vds).sum())),
                ("VGS", int(self.herm_vgs.sum()), int((~self.fc_vgs).sum())))

    # --- 4.2 마디 값·기울기 -------------------------------------------------
    def node(self, Lw, a, vds, vsb):
        """VGS 마디 a 의 (V_a, S_a). Lw = ((L index, 가중치), ...)."""
        VDS = self.grids[2]
        k, td = axis_cell_r5(VDS, vds)
        Sw = axis_weights(self.grids[3], vsb)
        Dw = axis_weights(VDS, vds)
        lI, on = self.lI, self.on
        if td == 0.0 or td == 1.0:
            b = k if td == 0.0 else k + 1
            V = 0.0
            for iL, wl in Lw:
                for s, ws in Sw:
                    V += wl * ws * lI[iL, a, b, s]
        else:
            yk = yk1 = mk = mk1 = 0.0
            herm = True
            for iL, wl in Lw:
                for s, ws in Sw:
                    w = wl * ws
                    yk += w * lI[iL, a, k, s]
                    yk1 += w * lI[iL, a, k + 1, s]
                    mk += w * self.gdsid[iL, a, k, s]
                    mk1 += w * self.gdsid[iL, a, k + 1, s]
                    herm = herm and bool(self.vds_ok[iL, a, k, s] and self.vds_ok[iL, a, k + 1, s]
                                         and self.fc_vds[iL, a, k, s])
            hd = VDS[k + 1] - VDS[k]
            V = hermite_val(yk, yk1, mk, mk1, hd, td) if herm else yk + td * (yk1 - yk)
        S = 0.0
        for iL, wl in Lw:
            for b, wd in Dw:
                for s, ws in Sw:
                    if not on[iL, a, b, s]:
                        return float(V), float("nan")
                    S += wl * wd * ws * self.gmid[iL, a, b, s]
        return float(V), float(S)

    def vgs_cell_fc(self, Lw, a, vds, vsb):
        """VGS 칸 a 의 단조 조건(가중치 ≠ 0 인 (L, VDS, VS) 모서리의 fc_vgs 전부 참)."""
        Dw = axis_weights(self.grids[2], vds)
        Sw = axis_weights(self.grids[3], vsb)
        return all(bool(self.fc_vgs[iL, a, b, s]) for iL, _ in Lw for b, _ in Dw for s, _ in Sw)

    def lin4(self, arr, Lw, vgs, vds, vsb):
        tot = 0.0
        for iL, wl in Lw:
            for g, wg in axis_weights(self.grids[1], vgs):
                for b, wd in axis_weights(self.grids[2], vds):
                    for s, ws in axis_weights(self.grids[3], vsb):
                        tot += wl * wg * wd * ws * float(arr[iL, g, b, s])
        return tot

    def lnid_gmid(self, Lw, vgs, vds, vsb):
        """4.2 조회점의 (lnID, gm/ID, VGS Hermite 칸 여부)."""
        VGS = self.grids[1]
        a, tg = axis_cell_r5(VGS, vgs)
        if tg == 0.0:
            V, S = self.node(Lw, a, vds, vsb)
            return V, S, None
        if tg == 1.0:
            V, S = self.node(Lw, a + 1, vds, vsb)
            return V, S, None
        V0, S0 = self.node(Lw, a, vds, vsb)
        V1, S1 = self.node(Lw, a + 1, vds, vsb)
        h = VGS[a + 1] - VGS[a]
        herm = math.isfinite(S0) and math.isfinite(S1) and self.vgs_cell_fc(Lw, a, vds, vsb)
        if herm:
            return hermite_val(V0, V1, S0, S1, h, tg), hermite_der(V0, V1, S0, S1, h, tg), True
        return V0 + tg * (V1 - V0), (V1 - V0) / h, False

    def op(self, Lw, Lval, vgs, vds, vsb):
        """op_point 기대값 dict(CONTRACT 4.1 표 [r5])."""
        lnid, gmid, herm = self.lnid_gmid(Lw, vgs, vds, vsb)
        lnD = self.lin4(self.lD, Lw, vgs, vds, vsb)
        return {"IDu": math.exp(lnid) * Lval / self.w_m, "gm_over_id": gmid,
                "gm_gds": gmid * math.exp(lnid - lnD), "gds_per_w": math.exp(lnD) / self.w_m,
                "vth": self.lin4(self.vth, Lw, vgs, vds, vsb), "lnID": lnid, "vgs_hermite": herm}

    def curve(self, Lw, vds, vsb):
        """gm_id_curve 기대값: (V 마디, S 마디, cell_ok)."""
        n = len(self.grids[1])
        VS_ = [self.node(Lw, a, vds, vsb) for a in range(n)]
        V = np.array([v for v, _ in VS_])
        S = np.array([s for _, s in VS_])
        ok = tuple(self.vgs_cell_fc(Lw, a, vds, vsb) for a in range(n - 1))
        return V, S, ok


AXES_T = ("L", "VGS", "VDS", "VS")


def anchor_w(i):
    return ((i, 1.0),)


def l_weights(L_grid, anchor_bin, L):
    """CONTRACT 4.0 L 위치의 독립 구현: 앵커(1 ulp) -> (((i, 1.0),), 앵커 값), 같은 bin 양옆 앵커 사이 ->
    (((k−1, 1−t), (k, t)), L), 그 밖 None. anchor_bin = LBinMap.anchor_bin(빈 지도면 ())."""
    Lg = [float(x) for x in L_grid]
    for i, a in enumerate(Lg):
        if abs(L - a) <= math.ulp(a):
            return ((i, 1.0),), a
    if not (Lg[0] < L < Lg[-1]):
        return None
    k = bisect.bisect_right(Lg, L)
    if anchor_bin and anchor_bin[k - 1] == anchor_bin[k]:
        t = (L - Lg[k - 1]) / (Lg[k] - Lg[k - 1])
        return ((k - 1, 1.0 - t), (k, t)), L
    return None


def hermite_cell_root(x0, x1, V0, V1, S0, S1, target):
    """CONTRACT 3절 칸 안의 근(p'(v) = target), 독립 bisection. 끝 residual = 마디 기울기 − 목표."""
    r0, r1 = S0 - target, S1 - target
    if r1 == 0.0:
        return x1
    if (r0 > 0) == (r1 > 0) and r0 != 0.0:
        return x0 if abs(r0) < abs(r1) else x1
    h = x1 - x0
    lo, hi = x0, x1
    s_hi = r1 > 0
    for _ in range(400):
        mid = 0.5 * (lo + hi)
        if mid <= lo or mid >= hi:
            break
        r = hermite_der(V0, V1, S0, S1, h, (mid - x0) / h) - target
        if r == 0.0:
            return mid
        if (r > 0) == s_hi:
            hi = mid
        else:
            lo = mid
    return lo


def sir_ref(vgs, V, S, target, cell_ok=None):
    """CONTRACT 3절 정본 규칙(칸 선택 + 칸 안 Hermite 미분 근). 반환 ("ok", v) / ("none", None) / ("nonmono", i)."""
    S = np.asarray(S, dtype=float)
    p = int(np.argmax(S))
    d = S - target
    cand = [i for i in range(p, len(S) - 1) if d[i] * d[i + 1] <= 0.0]
    if not cand:
        return "none", None
    i = cand[-1]
    if cell_ok is not None and not cell_ok[i]:
        return "nonmono", i
    return "ok", hermite_cell_root(float(vgs[i]), float(vgs[i + 1]), float(V[i]), float(V[i + 1]),
                                   float(S[i]), float(S[i + 1]), target)


def target_ref(vgs, V, S, cell_ok, w_m, W, quantity, target):
    """CONTRACT 4.1 gm_id_for_target 의 vgs 기대값. 반환 ("ok", vgs) 또는 (사유 키, 정보)."""
    V = np.asarray(V, dtype=float)
    S = np.asarray(S, dtype=float)
    idv = np.exp(V)
    Q = idv * W / w_m if quantity == "current" else idv * S * W / w_m
    p = int(np.argmax(S))
    e = p
    while e + 1 < len(Q) and Q[e + 1] > Q[e]:
        e += 1
    if not (Q[p] <= target <= Q[e]):
        if float(Q[p:].min()) <= target <= float(Q[p:].max()):
            return "lut_target_non_monotonic", (float(Q[p]), float(Q[e]))
        return "lut_target_out_of_range", (float(Q[p:].min()), float(Q[p:].max()))
    j = p + max(int(np.searchsorted(Q[p:e + 1], target, side="left")) - 1, 0)
    if j == e:
        return "ok", float(vgs[e])
    if not cell_ok[j]:
        return "lut_hermite_nonmonotone_cell", (float(vgs[j]), float(vgs[j + 1]))
    x0, x1 = float(vgs[j]), float(vgs[j + 1])
    h = x1 - x0
    lt = math.log(target) - math.log(W / w_m)

    def f(x):
        t = (x - x0) / h
        val = hermite_val(V[j], V[j + 1], S[j], S[j + 1], h, t)
        if quantity == "gm":
            val += math.log(hermite_der(V[j], V[j + 1], S[j], S[j + 1], h, t))
        return val - lt
    lo, hi = x0, x1
    for _ in range(400):
        mid = 0.5 * (lo + hi)
        if mid <= lo or mid >= hi:
            break
        if f(mid) > 0:
            hi = mid
        else:
            lo = mid
    return "ok", lo


def tol_cell_ref(rs, i, k, anchor_bin=None, with_roots=True):
    """CONTRACT 5절 [r5] 셀 (i, k) 독립 구현. 반환 dict(inv, eq, inv_loo, eq_loo, n_t, n_f).
    anchor_bin: 그 슬라이스 L 앵커의 bin index tuple(빈 지도면 None -- L 방향 LOO 없음)."""
    Lg, VGS, VDS, VS = (np.asarray(g) for g in rs.grids)
    nL, nG, nV, nS = len(Lg), len(VGS), len(VDS), len(VS)
    lI, on, gmid, gdsid, vds_ok = rs.lI, rs.on, rs.gmid, rs.gdsid, rs.vds_ok
    l_int = (anchor_bin is not None and len(anchor_bin) == nL and 0 < i < nL - 1
             and anchor_bin[i - 1] == anchor_bin[i] == anchor_bin[i + 1])
    eq_s, eq_r = [], []
    # --- id_equivalent ---
    c = lI[i, :, k, :]
    o = on[i, :, k, :]
    gm = gmid[i, :, k, :]
    if nG > 2:
        H = (VGS[2:] - VGS[:-2])[:, None]
        t = ((VGS[1:-1] - VGS[:-2]) / (VGS[2:] - VGS[:-2]))[:, None]
        est = hermite_val(c[:-2], c[2:], gm[:-2], gm[2:], H, t)
        cond = o[:-2] & o[1:-1] & o[2:]
        err = np.abs(est - c[1:-1]) / gm[1:-1]
        eq_r += list(err[cond])
        eq_s += list(err[cond] / 2.0 ** 4)
    if 0 < k < nV - 1:
        H = VDS[k + 1] - VDS[k - 1]
        t = (VDS[k] - VDS[k - 1]) / H
        lo_, hi_ = lI[i, :, k - 1, :], lI[i, :, k + 1, :]
        herm = vds_ok[i, :, k - 1, :] & vds_ok[i, :, k + 1, :]
        est = np.where(herm, hermite_val(lo_, hi_, gdsid[i, :, k - 1, :], gdsid[i, :, k + 1, :], H, t),
                       lo_ + t * (hi_ - lo_))
        cond = on[i, :, k - 1, :] & o & on[i, :, k + 1, :]
        err = np.abs(est - c) / gm
        eq_r += list(err[cond])
        eq_s += list((err / np.where(herm, 2.0 ** 4, 2.0 ** 2))[cond])
    if nS > 2:
        t = ((VS[1:-1] - VS[:-2]) / (VS[2:] - VS[:-2]))[None, :]
        est = c[:, :-2] + t * (c[:, 2:] - c[:, :-2])
        cond = o[:, :-2] & o[:, 1:-1] & o[:, 2:]
        err = np.abs(est - c[:, 1:-1]) / gm[:, 1:-1]
        eq_r += list(err[cond])
        eq_s += list(err[cond] / 2.0 ** 2)
    if l_int:
        t = (Lg[i] - Lg[i - 1]) / (Lg[i + 1] - Lg[i - 1])
        lo_, hi_ = lI[i - 1, :, k, :], lI[i + 1, :, k, :]
        est = lo_ + t * (hi_ - lo_)
        cond = on[i - 1, :, k, :] & o & on[i + 1, :, k, :]
        err = np.abs(est - c) / gm
        eq_r += list(err[cond])
        eq_s += list(err[cond] / 2.0 ** 2)
    # --- gm_id_inverse ---
    inv_s, inv_r, n_t, n_f = [], [], 0, 0
    for s in range(nS):
        if not o[:, s].all():
            continue
        V, g = c[:, s], gm[:, s]
        p = int(np.argmax(g))
        side = []                                         # (V 곡선, S 곡선, 2^p)
        if 0 < k < nV - 1 and on[i, :, k - 1, s].all() and on[i, :, k + 1, s].all():
            H = VDS[k + 1] - VDS[k - 1]
            t = (VDS[k] - VDS[k - 1]) / H
            lo_, hi_ = lI[i, :, k - 1, s], lI[i, :, k + 1, s]
            herm = vds_ok[i, :, k - 1, s] & vds_ok[i, :, k + 1, s]
            Vl = np.where(herm, hermite_val(lo_, hi_, gdsid[i, :, k - 1, s], gdsid[i, :, k + 1, s], H, t),
                          lo_ + t * (hi_ - lo_))
            Sl = gmid[i, :, k - 1, s] + t * (gmid[i, :, k + 1, s] - gmid[i, :, k - 1, s])
            side.append((Vl, Sl, 2.0 ** 2))
        if 0 < s < nS - 1 and o[:, s - 1].all() and o[:, s + 1].all():
            t = (VS[s] - VS[s - 1]) / (VS[s + 1] - VS[s - 1])
            side.append((c[:, s - 1] + t * (c[:, s + 1] - c[:, s - 1]),
                         gm[:, s - 1] + t * (gm[:, s + 1] - gm[:, s - 1]), 2.0 ** 2))
        if l_int and on[i - 1, :, k, s].all() and on[i + 1, :, k, s].all():
            t = (Lg[i] - Lg[i - 1]) / (Lg[i + 1] - Lg[i - 1])
            side.append((lI[i - 1, :, k, s] + t * (lI[i + 1, :, k, s] - lI[i - 1, :, k, s]),
                         gmid[i - 1, :, k, s] + t * (gmid[i + 1, :, k, s] - gmid[i - 1, :, k, s]), 2.0 ** 2))
        for j in range(p, nG):
            if not all(g[j] > g[r] for r in range(j + 1, nG)):
                continue
            tg = float(g[j])
            curves = []
            if 0 < j < nG - 1:
                curves.append((np.delete(VGS, j), np.delete(V, j), np.delete(g, j), 2.0 ** 3))
            curves += [(VGS, a, b, w) for a, b, w in side]
            for xs, cv, cs, w in curves:
                n_t += 1
                if not with_roots:
                    sc = np.asarray(cs)
                    pp = int(np.argmax(sc))
                    dd = sc - tg
                    if not np.any(dd[pp:-1] * dd[pp + 1:] <= 0.0):
                        n_f += 1
                    continue
                st, root = sir_ref(xs, cv, cs, tg)
                if st != "ok":
                    n_f += 1
                    continue
                inv_r.append(abs(root - VGS[j]))
                inv_s.append(abs(root - VGS[j]) / w)
    mx = lambda xs: float(max(xs)) if xs else None
    return {"inv": mx(inv_s), "eq": mx(eq_s), "inv_loo": mx(inv_r), "eq_loo": mx(eq_r), "n_t": n_t, "n_f": n_f}


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


def lut_package_window_hashes(n):
    """[r5] 패키지 lut/*.py 의 모든 문장 목록(중첩 포함)에서 연속 n 문장 창의 AST 해시 -> {해시: [(파일, 첫 문장 줄)]}.
    함수 본문은 docstring 을 뺀 목록도 넣는다. 복사본이 패키지에서 빠졌는지(CONTRACT 6절 [r5]) 확인용."""
    out = {}
    for path in sorted(LUT_SRC.glob("*.py")):
        tree = ast.parse(path.read_text(encoding="utf-8"))
        for node in ast.walk(tree):
            for field in ("body", "orelse", "finalbody"):
                stmts = getattr(node, field, None)
                if not isinstance(stmts, list) or not stmts or not isinstance(stmts[0], ast.stmt):
                    continue
                lists = [stmts]
                if field == "body" and isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    lists.append(_strip_doc(stmts))
                for lst in lists:
                    for a in range(0, len(lst) - n + 1):
                        out.setdefault(ast_sha(lst[a:a + n]), []).append((path.name, lst[a].lineno))
    return out


def lut_package_function_names():
    names = set()
    for path in sorted(LUT_SRC.glob("*.py")):
        for node in ast.walk(ast.parse(path.read_text(encoding="utf-8"))):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                names.add(node.name)
    return names


LEGACY_REF_HASHES = (
    ("_multilinear_interp", "d6bfc65c25e6e68f6b5f820c3a5a53ed6ed2429db00dc640ba15615dc7d69c54", 8),
    ("_multilinear_interp_point_multi", "76e24d9d66e06b760dc79b9d69ac51143cec7238046f9ed3ffd27a4b624c7cba", 7),
)


@functools.lru_cache(maxsize=1)
def legacy_reference_functions():
    """[r5] CONTRACT 6절: 기대값 비교 참조 = 옛 파일 원본의 정의. AST 해시(본문, docstring 제외)로 원본이 계약 표와
    같음을 확인한 뒤 그 정의만 떼어 실행한다. 반환 {이름: 함수}."""
    ns = {"np": np, "math": math}
    for name, sha, n in LEGACY_REF_HASHES:
        node = find_function(LEGACY_SR, name)
        body = _strip_doc(node.body)
        assert len(body) == n, (name, len(body))
        assert ast_sha(body) == sha, "옛 파일 원본의 %s 가 계약 6절 해시와 다르다" % name
        mod = ast.Module(body=[node], type_ignores=[])
        exec(compile(ast.fix_missing_locations(mod), str(LEGACY_SR), "exec"), ns)
    return {name: ns[name] for name, _, _ in LEGACY_REF_HASHES}


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
