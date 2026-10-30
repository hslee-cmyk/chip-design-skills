"""tests/lut 공용 픽스처 -- lut/CONTRACT.md 만 근거로 만든 입력·독립 계산(피검 조회 함수를 쓰지 않는다).

- toy LUT: CONTRACT 7절 그대로(폭 1e-6·2e-6 슬라이스, 기준 LUT, LutSpec). 로드 거부 test 용으로 배열·manifest 를 바꿔 쓸 수 있다.
- 실데이터: [r6] 기본 = LUT v2(CONTRACT 1.8 -- 저장소 설정 `assets/lut_v2_location.json` 을 `resolve_lut_location(설정,
  os.environ)` 으로 풀어 manifest·기준 LUT·검증 중점 파일·pdk_root 를 얻고 `load_lut_set` 에 `pdk_root`·`verify_midpoints` 를 넘긴다).
  LUT 파일은 위치 선언 하나로만 읽는다(O-180: LUT 를 가리키는 환경 덮어쓰기 없음. 데이터 루트 위치는 선언의 env 뿐이고
  sha256 이 같은 파일만 받는다). PDK tech LEF(`GMID_PDK_TLEF`)는 LUT 가 아니라 유지.
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
import subprocess
from pathlib import Path

import numpy as np
import pytest

from gmid_engine.core import SchemaRejectedError
from gmid_engine.lut import LutMemo, LutSpec, load_lut_set, resolve_lut_location

HERE = Path(__file__).resolve().parent
ENGINE_ROOT = HERE.parents[1]                       # .../gmid_engine
SKILL_DIR = ENGINE_ROOT.parent                      # .../analog-gmid-design
LUT_SRC = ENGINE_ROOT / "lut"
LEGACY_SR = SKILL_DIR / "legacy" / "sizing_recipe.py"

REALDATA_MARKER = "lut_realdata"

# [r6] CONTRACT 1.8 저장소 설정(LUT v2 위치, sha256 고정)
LOCATION_CONFIG = SKILL_DIR / "assets" / "lut_v2_location.json"
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
# [r5] CONTRACT 7.2 r4 toy (FC 위반 예시) -- [r7 2026-10-09 단위 검사 복원(1.4)] 기울기 자료가 ln ID 와 평균값 정리로 맞는 판으로 교체.
#   옛 판(ID 마디 (1e-7, 1e-6, 1e-5)·GM/ID (20, 10, 4)·GDS = ID/10, ID 는 VDS 무관)은 VGS 칸 0 의 현 기울기 ln10/0.5 = 4.61 이 끝 기울기
#   [10, 20] 밖이고 VDS 칸은 현 0 인데 끝 기울기 0.1 이라 1.4 단위 검사(현이 두 끝 기울기 사이) 위반 -> 로드 거부(GDS 18/18 칸).
#   새 판(oracle (a) 구성): 칸마다 현 기울기가 두 끝 기울기 사이(모순 0 칸)인데도 FC 위반은 그대로 남게 골랐다(손계산, CONTRACT 1.4 식):
#   VGS 칸 0: Δln ID = ln10, m = (20, 4), h 0.5 -> 현 4.605 ∈ [4, 20]; b0 = 10, b2 = 2, b1 = 3·ln10 − 12 = −5.09, b1² = 25.9 > 20 -> 위반.
#   VGS 칸 1: Δln ID = 1.5, m = (4, 1.5) -> 현 3 ∈ [1.5, 4]; b0 = 2, b2 = 0.75, b1 = 4.5 − 2.75 = 1.75 ≥ 0 -> 단조.
#   VDS 칸: Δln ID = 0.01, m = GDS/ID = (0.1, 0.01) -> 현 0.02 ∈ [0.01, 0.1]; b0 = 0.05, b2 = 0.005, b1 = 0.03 − 0.055 = −0.025,
#   b1² = 6.25e-4 > 2.5e-4 -> 위반. 그래서 hermite_fc = (("VDS", 18, 18), ("VGS", 24, 12), ("VS", 0, 0)) 는 옛 판과 같다.
R4_ID_VGS = (1e-7, 1e-6, 1e-6 * math.exp(1.5))
R4_GM_RATIO = (20.0, 4.0, 1.5)
R4_LNID_VDS = (0.0, 0.01)                         # ln ID 의 VDS 몫(VDS 격자 0.5, 1.0)
R4_GDS_RATIO = (0.1, 0.01)                        # GDS/ID (VDS 격자 0.5, 1.0)


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
    """[r7] r4 toy 슬라이스(FC 위반 예시, 기울기 자료 일관 -- 위 R4_* 주석): ID = (1e-6/L)·R4_ID_VGS·exp(R4_LNID_VDS)·(1, 0.5)[VS],
    GM = ID·R4_GM_RATIO[VGS], GDS = ID·R4_GDS_RATIO[VDS]."""
    ID = np.empty((3, 3, 2, 2))
    for iL, L in enumerate(TOY_L):
        for iG in range(3):
            for k in range(2):
                for s in range(2):
                    ID[iL, iG, k, s] = (1e-6 / L) * R4_ID_VGS[iG] * math.exp(R4_LNID_VDS[k]) * TOY_VS_FACTOR[s]
    ID = ID * scale
    GM = ID * np.asarray(R4_GM_RATIO)[None, :, None, None]
    return _toy_dict(W, ID, GM, ID * np.asarray(R4_GDS_RATIO)[None, None, :, None])


def r5_toy_lnid(v, d, s_vs, L=1e-6):
    """CONTRACT 7.1 닫힌 식(폭 1e-6): ln ID(v, d, vsb) -- VS 선형 = ln(0.5)·vsb/0.5."""
    return (math.log(1e-6 / L) + math.log(1e-7) + R5_A * v - R5_B * v * v + R5_C * d
            + math.log(0.5) * s_vs / 0.5)


CURVE_L = (1e-6, 2e-6)
CURVE_VDS = (0.5, 1.0)
CURVE_VS = (0.0, 0.5)


CURVE_VDS_FACTOR = (1.0, 2.0)                      # ID(VDS 1.0) = 2·ID(VDS 0.5) -- 2 의 거듭제곱이라 배열 비 계산이 정확
CURVE_GDS_PER_ID = 2.0 * math.log(2.0)             # = d ln ID/d VDS = ln 2 / 0.5 (위 배수와 같은 직선 -- 1.4 단위 검사 일관)


def chord_ids(vgs, gm_over_id, id0, lam=0.6):
    """[r7] 기울기 자료와 맞는 마디 ID(oracle (a) 구성): 칸 [j, j+1] 의 ln ID 현 기울기 = lam·g_j + (1 − lam)·g_(j+1)
    (두 끝 기울기의 볼록 결합이라 CONTRACT 1.4 단위 검사 '현이 두 끝 기울기 사이' 를 만족한다). lam ∈ [1/3, 2/3] 이면
    현 ≥ (g_j + g_(j+1))/3 이라 b1 = 3·Δln ID − (g_j + g_(j+1))·h ≥ 0 -> 양의 기울기 칸은 FC 단조. lam = 1/2(사다리꼴)이면 칸 안
    Hermite 미분이 g 의 선형 보간과 같아지므로(옛 2점 규칙과 근이 같아 판별력이 없다) 기본값은 0.6."""
    out = [float(id0)]
    for j in range(len(vgs) - 1):
        h = float(vgs[j + 1]) - float(vgs[j])
        out.append(out[-1] * math.exp(h * (lam * gm_over_id[j] + (1.0 - lam) * gm_over_id[j + 1])))
    return tuple(out)


def chord_outside_fraction(vgs, ids, gm_over_id):
    """CONTRACT 1.4 단위 검사를 이 곡선(VGS 한 줄)에 대해 독립으로: 두 끝 정의(ID > 0, GM/ID > 0) 칸 중 현 기울기가 두 끝 기울기
    [min, max] 밖인 칸의 (수, 칸 수). 허용분은 계약 식(eps·(|y0| + |y1|)/Δx + eps·(|m0| + |m1|))."""
    eps = np.finfo(float).eps
    out = n = 0
    for j in range(len(vgs) - 1):
        i0, i1, g0, g1 = ids[j], ids[j + 1], gm_over_id[j], gm_over_id[j + 1]
        if not (i0 > 0 and i1 > 0 and g0 > 0 and g1 > 0):
            continue
        y0, y1, h = math.log(i0), math.log(i1), float(vgs[j + 1]) - float(vgs[j])
        c = (y1 - y0) / h
        tol = eps * (abs(y0) + abs(y1)) / h + eps * (abs(g0) + abs(g1))
        n += 1
        out += not (min(g0, g1) - tol <= c <= max(g0, g1) + tol)
    return out, n


def curve_slice_arrays(W, vgs, ids, gm_over_id):
    """임의 곡선 슬라이스: (L, VDS, VS) 2점씩, 그 위에서 같은 VGS 곡선. GM = ID·gm_over_id.
    [r7] VDS 방향: ID(VDS 0.5) = ids, ID(VDS 1.0) = 2·ids, GDS = ID·2ln2(= d ln ID/d VDS -- 1.4 단위 검사 일관; 옛 판의 GDS = ID/10 은
    ID 가 VDS 무관이라 VDS 칸 현 0 대 끝 기울기 0.1 로 모든 칸 위반 -> 로드 거부)."""
    n = len(vgs)
    ID = np.empty((2, n, 2, 2))
    ID[...] = (np.asarray(ids, dtype=float)[None, :, None, None]
               * np.asarray(CURVE_VDS_FACTOR)[None, None, :, None])
    GM = ID * np.asarray(gm_over_id, dtype=float)[None, :, None, None]
    return {
        "W": np.float64(W),
        "L": np.asarray(CURVE_L), "VGS": np.asarray(vgs, dtype=float),
        "VDS": np.asarray(CURVE_VDS), "VS": np.asarray(CURVE_VS),
        "ID": ID, "GM": GM, "GDS": ID * CURVE_GDS_PER_ID, "VTH": np.full(ID.shape, 0.4),
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


def hermite_der2(y0, y1, m0, m1, h, t):
    """p''(x) = d²p/dt² / h²."""
    return (y0 * (12 * t - 6) + h * m0 * (6 * t - 4) + y1 * (-12 * t + 6) + h * m1 * (6 * t - 2)) / (h * h)


def hermite_der_absterms(y0, y1, m0, m1, h, t):
    """p'(x) 계산의 항 크기 합 Σ|항|/h (반올림 오차 상한의 척도)."""
    t2 = t * t
    return (abs(y0 * (6 * t2 - 6 * t)) + abs(h * m0 * (3 * t2 - 4 * t + 1))
            + abs(y1 * (-6 * t2 + 6 * t)) + abs(h * m1 * (3 * t2 - 2 * t))) / h


def casteljau_der_absterms(y0, y1, m0, m1, h, t):
    """[r6 유도 보완] 엔진 경로(4.2: Bernstein 제어점 c = (y0, y0 + m0·h/3, y1 − m1·h/3, y1) 의 de Casteljau) 미분의 항 크기 합:
    p'(x) = 3/h·[(1−t)²(c1 − c0) + 2t(1−t)(c2 − c1) + t²(c3 − c2)] -- 각 차 (c_{i+1} − c_i) 의 반올림은 |c_i| + |c_{i+1}| 에 비례하고
    t 가 칸 끝이어도 0 이 되지 않는다(기저 형태의 Σ|항| 은 t → 0 에서 y 항이 사라져 이 경로의 오차를 덮지 못한다 -- v2 실데이터
    pmos 0.7 µm 의 칸 끝 근에서 실측 5.2e-13 > 옛 상한 3.0e-13)."""
    c0, c1, c2, c3 = abs(y0), abs(y0) + abs(m0) * h / 3, abs(y1) + abs(m1) * h / 3, abs(y1)
    s = 1 - t
    return 3.0 / h * (s * s * (c0 + c1) + 2 * t * s * (c1 + c2) + t * t * (c2 + c3))


def hermite_val_absterms(y0, y1, m0, m1, h, t):
    """p(x) 계산의 항 크기 합 Σ|항|."""
    t2 = t * t
    t3 = t2 * t
    return (abs(y0 * (2 * t3 - 3 * t2 + 1)) + abs(h * m0 * (t3 - 2 * t2 + t))
            + abs(y1 * (-2 * t3 + 3 * t2)) + abs(h * m1 * (t3 - t2)))


# [r5] 근 비교 허용 차의 유도(임의 상수 없음 -- 오케스트레이터 지시 2026-10-07):
#  - 3절: 두 경로(엔진·이 파일) 모두 bisection 을 부동소수 분해능(K_max = ceil(log2(칸 폭 / ulp(max(|v0|, |v1|)))))까지 돌린다
#    -> 각 경로의 근은 자기 residual 부호 변화점에서 ulp(max(|v0|, |v1|)) 이내.
#  - residual 의 경로별 반올림 오차 ≤ γ_n·(Σ|항| + |목표|) (표준 전진 오차 상한), γ_n = n·u/(1 − n·u), u = 2^-53(단위 반올림),
#    n = 한 번의 평가에서 결과까지 이어지는 부동소수 연산 깊이의 상한. 이 파일의 기저 함수 경로: 기저 다항식 4(t², ·, 계수, 합)
#    + 인자 곱 2 + 네 항 합 3 + h 나눔 1 + 목표 뺌 1 = 11. 엔진의 de Casteljau 미분(제어점 2 + 2단 보간 각 3 + ·3/h 2 + 뺌 1 = 11)도
#    같은 깊이 -> n = 11.
#  - 근 차 상한 = 2·γ_n·(Σ|항| + |목표|) / |residual 기울기(근)| + 2·ulp(max(|v0|, |v1|))
#    (두 경로 오차 합 / 근에서 residual 의 기울기 + 두 경로의 분해능).
GAMMA_DEPTH = 11
UNIT_ROUNDOFF = 2.0 ** -53


def gamma_n(n=GAMMA_DEPTH):
    return n * UNIT_ROUNDOFF / (1 - n * UNIT_ROUNDOFF)


def node_err_term(h, t, dV0=0.0, dV1=0.0, dS0=0.0, dS1=0.0):
    """마디 값·기울기 자체가 경로마다 반올림된 계산값일 때(격자 밖 곡선) p'(x) 로 전파되는 차의 상한:
    Σ |∂p'/∂마디|·(두 경로 마디 차 상한). 마디 차 상한은 호출부가 같은 γ_n 규칙으로 낸다(격자점 마디는 0)."""
    t2 = t * t
    return (abs((6 * t2 - 6 * t) / h) * dV0 + abs((-6 * t2 + 6 * t) / h) * dV1
            + abs(3 * t2 - 4 * t + 1) * dS0 + abs(3 * t2 - 2 * t) * dS1)


def hermite_root_bound(x0, x1, V0, V1, S0, S1, target, root, dV0=0.0, dV1=0.0, dS0=0.0, dS1=0.0):
    """vgs 역산(p'(v) = 목표) 근 차 상한(V) -- 위 유도. residual 기울기 = p''(근)."""
    h = x1 - x0
    t = (root - x0) / h
    # 두 경로: 이 파일(기저 형태) + 엔진(de Casteljau, [r6 유도 보완])
    err = gamma_n() * (hermite_der_absterms(V0, V1, S0, S1, h, t) + casteljau_der_absterms(V0, V1, S0, S1, h, t)
                       + 2 * abs(target))
    err += node_err_term(h, t, dV0, dV1, dS0, dS1)
    slope = abs(hermite_der2(V0, V1, S0, S1, h, t))
    res = 2 * math.ulp(max(abs(x0), abs(x1)))
    return (err / slope if slope > 0 else math.inf) + res


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
        # [r7] VS 축 Hermite 보조(CONTRACT 1.4 [r7], 계획 DEC-87 'GMBS 열이 생기면 기울기 −GMBS/ID 의 Hermite'):
        # vs_ok = GMBS/ID 가 유한·양수인 격자점(GMBS 열이 없으면 전부 거짓), 기울기 d lnID/dVS = −GMBS/ID.
        self.has_gmbs = "GMBS" in z
        if self.has_gmbs:
            GMBS = np.asarray(z["GMBS"], dtype=float)
            with np.errstate(divide="ignore", invalid="ignore"):
                r = np.where(ID > 0, GMBS / np.where(ID > 0, ID, 1.0), np.nan)
            self.vs_ok = np.isfinite(r) & (r > 0)
            self.vsslope = np.where(self.vs_ok, -r, 0.0)
        else:
            self.vs_ok = np.zeros(ID.shape, dtype=bool)
            self.vsslope = np.zeros(ID.shape)
        hs = np.diff(np.asarray(self.grids[3]))[None, None, None, :]
        self.herm_vs = self.vs_ok[..., :-1] & self.vs_ok[..., 1:]
        self.fc_vs = np.where(self.herm_vs, fc_ok(self.lI[..., :-1], self.lI[..., 1:], self.vsslope[..., :-1],
                                                  self.vsslope[..., 1:], hs), True)

    def hermite_fc(self):
        """CONTRACT 1.4 `hermite_fc`([r7] 세 번째 항 VS -- GMBS 열이 없으면 ("VS", 0, 0))."""
        return (("VDS", int(self.herm_vds.sum()), int((~self.fc_vds).sum())),
                ("VGS", int(self.herm_vgs.sum()), int((~self.fc_vgs).sum())),
                ("VS", int(self.herm_vs.sum()), int((~self.fc_vs).sum())))

    def vs_y(self, Lw, a, nodes_b, vsb):
        """[r7] CONTRACT 4.2 2단계 VS 축: VDS 마디 b(nodes_b)마다 L 선형 가중 후 VS 칸 Hermite(끝 값 lnID, 끝 기울기
        −GMBS/ID)로 y_b. 조건(가중치 ≠ 0 인 L 모서리·VDS 마디 모두에서 두 VS 끝 vs_ok 이고 fc_vs 참)이 거짓이면 L·VS 선형.
        반환 ({b: y_b}, VS Hermite 여부 또는 None(VS 격자점 -- 보간 없음))."""
        VS = self.grids[3]
        s0, ts = axis_cell_r5(VS, vsb)
        lI = self.lI
        if ts == 0.0 or ts == 1.0:
            s = s0 if ts == 0.0 else s0 + 1
            return {b: sum(wl * lI[iL, a, b, s] for iL, wl in Lw) for b in nodes_b}, None
        herm = all(bool(self.vs_ok[iL, a, b, s0] and self.vs_ok[iL, a, b, s0 + 1] and self.fc_vs[iL, a, b, s0])
                   for iL, _ in Lw for b in nodes_b)
        hs = VS[s0 + 1] - VS[s0]
        out = {}
        for b in nodes_b:
            y0 = sum(wl * lI[iL, a, b, s0] for iL, wl in Lw)
            y1 = sum(wl * lI[iL, a, b, s0 + 1] for iL, wl in Lw)
            if herm:
                m0 = sum(wl * self.vsslope[iL, a, b, s0] for iL, wl in Lw)
                m1 = sum(wl * self.vsslope[iL, a, b, s0 + 1] for iL, wl in Lw)
                out[b] = hermite_val(y0, y1, m0, m1, hs, ts)
            else:
                out[b] = y0 + ts * (y1 - y0)
        return out, herm

    # --- 4.2 마디 값·기울기 -------------------------------------------------
    def node(self, Lw, a, vds, vsb):
        """VGS 마디 a 의 (V_a, S_a). Lw = ((L index, 가중치), ...)."""
        VDS = self.grids[2]
        k, td = axis_cell_r5(VDS, vds)
        Sw = axis_weights(self.grids[3], vsb)
        Dw = axis_weights(VDS, vds)
        on = self.on
        if td == 0.0 or td == 1.0:
            b = k if td == 0.0 else k + 1
            V = self.vs_y(Lw, a, (b,), vsb)[0][b]
        else:
            ys, _ = self.vs_y(Lw, a, (k, k + 1), vsb)
            yk, yk1 = ys[k], ys[k + 1]
            mk = mk1 = 0.0
            herm = True
            for iL, wl in Lw:
                for s, ws in Sw:
                    w = wl * ws
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

    def vs_fallback(self, Lw, vgs, vds, vsb):
        """[r7] CONTRACT 4.1 `OpPoint.fallbacks` 의 VS 항 독립 판정: VS 가 격자점 사이이고 Hermite 조건이 거짓이면 사유
        ('slope_undefined' = 두 VS 끝 기울기 중 정의 안 된 것이 있음, 아니면 'fc_violation'), 아니면 None."""
        VS = self.grids[3]
        s0, ts = axis_cell_r5(VS, vsb)
        if ts in (0.0, 1.0):
            return None
        a, tg = axis_cell_r5(self.grids[1], vgs)
        nodes_a = (a,) if tg == 0.0 else (a + 1,) if tg == 1.0 else (a, a + 1)
        k, td = axis_cell_r5(self.grids[2], vds)
        nodes_b = (k,) if td == 0.0 else (k + 1,) if td == 1.0 else (k, k + 1)
        corners = [(iL, aa, b) for iL, _ in Lw for aa in nodes_a for b in nodes_b]
        if not all(bool(self.vs_ok[iL, aa, b, s0] and self.vs_ok[iL, aa, b, s0 + 1]) for iL, aa, b in corners):
            return "slope_undefined"
        if not all(bool(self.fc_vs[iL, aa, b, s0]) for iL, aa, b in corners):
            return "fc_violation"
        return None

    def op(self, Lw, Lval, vgs, vds, vsb):
        """op_point 기대값 dict(CONTRACT 4.1 표 [r5])."""
        lnid, gmid, herm = self.lnid_gmid(Lw, vgs, vds, vsb)
        lnD = self.lin4(self.lD, Lw, vgs, vds, vsb)
        return {"IDu": math.exp(lnid) * Lval / self.w_m, "gm_over_id": gmid,
                "gm_gds": gmid * math.exp(lnid - lnD), "gds_per_w": math.exp(lnD) / self.w_m,
                "vth": self.lin4(self.vth, Lw, vgs, vds, vsb), "lnID": lnid, "vgs_hermite": herm}

    def curve_err(self, Lw, vds, vsb):
        """마디별 두 경로 차 상한 (dV, dS): 마디 = 가중합(+ VDS Hermite) 이라 경로마다 반올림 ≤ γ_n·Σ|항|, 두 경로 -> 2γ_n.
        격자점(L 앵커·VDS·VS 격자)은 가중치 1 하나라 0. Σ|항| 은 Hermite 기저 크기 ≤ 1 로 위에서 묶는다."""
        g2 = 2 * gamma_n()
        Dw = axis_weights(self.grids[2], vds)
        Sw = axis_weights(self.grids[3], vsb)
        n = len(self.grids[1])
        dV, dS = np.zeros(n), np.zeros(n)
        if len(Lw) == 1 and len(Dw) == 1 and len(Sw) == 1:
            return dV, dS
        k, td = axis_cell_r5(self.grids[2], vds)
        hd = self.grids[2][k + 1] - self.grids[2][k]
        s0, ts = axis_cell_r5(self.grids[3], vsb)
        hs = self.grids[3][s0 + 1] - self.grids[3][s0]
        vs_off = ts not in (0.0, 1.0)
        nodes_b = (k if td == 0.0 else k + 1,) if td in (0.0, 1.0) else (k, k + 1)
        for a in range(n):
            A = 0.0
            for iL, wl in Lw:
                for s, ws in Sw:
                    w = abs(wl * ws)
                    if td in (0.0, 1.0):
                        A += w * abs(self.lI[iL, a, k if td == 0.0 else k + 1, s])
                    else:
                        A += w * (abs(self.lI[iL, a, k, s]) + abs(self.lI[iL, a, k + 1, s])
                                  + hd * abs(self.gdsid[iL, a, k, s]) + hd * abs(self.gdsid[iL, a, k + 1, s]))
                # [r7] VS Hermite 기울기 항의 크기(VS 격자 밖일 때) -- 같은 γ_n 상한에 더한다
                if vs_off:
                    A += abs(wl) * sum(hs * (abs(self.vsslope[iL, a, b, s0]) + abs(self.vsslope[iL, a, b, s0 + 1]))
                                       for b in nodes_b)
            B = sum(abs(wl * wd * ws) * self.gmid[iL, a, b, s] for iL, wl in Lw for b, wd in Dw for s, ws in Sw)
            dV[a], dS[a] = g2 * A, g2 * B
        return dV, dS

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


def sir_ref_b(vgs, V, S, target, cell_ok=None, with_residual=False, dV=None, dS=None):
    """sir_ref + 근 차 상한(hermite_root_bound) [+ 왕복 gm/ID 차 상한]. 반환 (상태, v, 상한[, 왕복 상한]).
    dV·dS: 마디별 두 경로 차 상한(격자 밖 곡선, RefSlice.curve_err) -- 없으면 0(격자점 마디)."""
    st, v = sir_ref(vgs, V, S, target, cell_ok)
    if st != "ok":
        return (st, v, None, None) if with_residual else (st, v, None)
    i = min(max(bisect.bisect_right([float(x) for x in vgs], v) - 1, 0), len(vgs) - 2)
    if v == float(vgs[i]) and i > 0:
        S_ = np.asarray(S, dtype=float)
        # 칸 끝에 놓인 근: 고른 칸은 가장 오른쪽 후보 -- 왼쪽 칸의 위 끝일 수 있다
        d = S_ - target
        cand = [c for c in range(int(np.argmax(S_)), len(S_) - 1) if d[c] * d[c + 1] <= 0.0]
        i = cand[-1]
    nd = {} if dV is None else dict(dV0=float(dV[i]), dV1=float(dV[i + 1]), dS0=float(dS[i]), dS1=float(dS[i + 1]))
    b = hermite_root_bound(float(vgs[i]), float(vgs[i + 1]), float(V[i]), float(V[i + 1]),
                           float(S[i]), float(S[i + 1]), target, v, **nd)
    if with_residual:
        return st, v, b, hermite_residual_bound(float(vgs[i]), float(vgs[i + 1]), float(V[i]), float(V[i + 1]),
                                                float(S[i]), float(S[i + 1]), target, v)
    return st, v, b


def hermite_residual_bound(x0, x1, V0, V1, S0, S1, target, root):
    """왕복 상한: 엔진 근 v_e 에서 엔진이 낸 gm/ID 와 목표의 차 ≤ (엔진 근의 bisection 분해능 2 ulp 동안의 p' 변화) +
    (p' 평가 반올림, 두 번: 근 찾기 residual·op_point 평가) -- hermite_root_bound 와 같은 γ_n 유도.
    (엔진 안에서는 역산과 op_point 가 같은 마디를 쓰므로 마디 차 항이 없다 -- 4.2 '같은 곡면')"""
    h = x1 - x0
    t = (root - x0) / h
    # [r6 유도 보완] 두 번의 평가(근 찾기 residual·op_point)는 모두 엔진 경로(de Casteljau) -> 그 항 크기 합으로
    err = 2 * gamma_n() * (max(hermite_der_absterms(V0, V1, S0, S1, h, t), casteljau_der_absterms(V0, V1, S0, S1, h, t))
                           + abs(target))
    return err + abs(hermite_der2(V0, V1, S0, S1, h, t)) * 2 * math.ulp(max(abs(x0), abs(x1)))


def target_root_bound(x0, x1, V0, V1, S0, S1, quantity, lt_total, root, dV0=0.0, dV1=0.0, dS0=0.0, dS1=0.0):
    """gm_id_for_target (근 차 상한 V, 왕복 ln 차 상한): residual f = p(v) [+ ln p'(v)] − (ln 목표 − ln(W/w_m)) --
    hermite_root_bound 와 같은 유도. gm 의 ln p' 항 오차 = p' 의 상대 오차 γ_n·Σ|항|/|p'|. residual 기울기 = p' [+ p''/p'].
    dV·dS = 마디의 두 경로 차 상한(격자 밖 곡선) -- 값 기저 크기로 p 에, node_err_term/|p'| 로 ln p' 에 전파."""
    h = x1 - x0
    t = (root - x0) / h
    g = gamma_n()
    err = g * (hermite_val_absterms(V0, V1, S0, S1, h, t) + abs(lt_total))
    t2 = t * t
    t3 = t2 * t
    node = (abs(2 * t3 - 3 * t2 + 1) * dV0 + abs(-2 * t3 + 3 * t2) * dV1
            + h * abs(t3 - 2 * t2 + t) * dS0 + h * abs(t3 - t2) * dS1)
    slope = hermite_der(V0, V1, S0, S1, h, t)
    if quantity == "gm":
        d1 = slope
        err += g * hermite_der_absterms(V0, V1, S0, S1, h, t) / abs(d1)
        node += node_err_term(h, t, dV0, dV1, dS0, dS1) / abs(d1)
        slope = d1 + hermite_der2(V0, V1, S0, S1, h, t) / d1
    res = 2 * math.ulp(max(abs(x0), abs(x1)))
    root_b = ((2 * err + node) / abs(slope) if slope != 0 else math.inf) + res
    # 왕복(ln 결과 − ln 목표) 상한: 엔진 근에서 엔진 residual 의 반올림(2 경로분 -- 근 찾기·op_point/exp 재평가) + 분해능 동안 변화
    trip_b = 2 * err + abs(slope) * res
    return root_b, trip_b


def target_ref(vgs, V, S, cell_ok, w_m, W, quantity, target, with_bound=False, dV=None, dS=None):
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
        return ("ok", float(vgs[e]), 0.0, 0.0) if with_bound else ("ok", float(vgs[e]))
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
    if with_bound:
        nd = {} if dV is None else dict(dV0=float(dV[j]), dV1=float(dV[j + 1]), dS0=float(dS[j]), dS1=float(dS[j + 1]))
        return ("ok", lo) + target_root_bound(x0, x1, float(V[j]), float(V[j + 1]), float(S[j]), float(S[j + 1]),
                                           quantity, abs(math.log(target)) + abs(math.log(W / w_m)), lo, **nd)
    return "ok", lo


def tol_cell_ref(rs, i, k, anchor_bin=None, with_roots=True):
    """CONTRACT 5절 [r5] 셀 (i, k) 독립 구현. 반환 dict(inv, eq, inv_loo, eq_loo, n_t, n_f).
    anchor_bin: 그 슬라이스 L 앵커의 bin index tuple(빈 지도면 None -- L 방향 LOO 없음)."""
    Lg, VGS, VDS, VS = (np.asarray(g) for g in rs.grids)
    nL, nG, nV, nS = len(Lg), len(VGS), len(VDS), len(VS)
    lI, on, gmid, gdsid, vds_ok = rs.lI, rs.on, rs.gmid, rs.gdsid, rs.vds_ok
    l_int = (anchor_bin is not None and len(anchor_bin) == nL and 0 < i < nL - 1
             and anchor_bin[i - 1] == anchor_bin[i] == anchor_bin[i + 1])
    eq_s, eq_r, eq_sb, eq_rb = [], [], [], []
    g2 = 2 * gamma_n()

    def add(err, A, cc, gmv, cond, scale):
        # 점 허용 차(두 경로 반올림, 위 유도와 같은 γ_n): 추정 Σ|항| A 와 |ln ID| 의 뺄셈 오차 / gm/ID + 나눗셈 상대 오차
        bnd = g2 * (A + np.abs(cc)) / gmv + g2 * err
        eq_r.extend(err[cond])
        eq_s.extend((err / scale)[cond] if np.ndim(scale) else err[cond] / scale)
        eq_rb.extend(bnd[cond])
        eq_sb.extend((bnd / scale)[cond] if np.ndim(scale) else bnd[cond] / scale)

    def lin_abs(lo_, hi_, t):
        return (1 + np.abs(t)) * np.abs(lo_) + np.abs(t) * np.abs(hi_)
    # --- id_equivalent ---
    c = lI[i, :, k, :]
    o = on[i, :, k, :]
    gm = gmid[i, :, k, :]
    if nG > 2:
        H = (VGS[2:] - VGS[:-2])[:, None]
        t = ((VGS[1:-1] - VGS[:-2]) / (VGS[2:] - VGS[:-2]))[:, None]
        est = hermite_val(c[:-2], c[2:], gm[:-2], gm[2:], H, t)
        A = hermite_val_absterms(c[:-2], c[2:], gm[:-2], gm[2:], H, t)
        cond = o[:-2] & o[1:-1] & o[2:]
        err = np.abs(est - c[1:-1]) / gm[1:-1]
        add(err, A, c[1:-1], gm[1:-1], cond, 2.0 ** 4)
    if 0 < k < nV - 1:
        H = VDS[k + 1] - VDS[k - 1]
        t = (VDS[k] - VDS[k - 1]) / H
        lo_, hi_ = lI[i, :, k - 1, :], lI[i, :, k + 1, :]
        herm = vds_ok[i, :, k - 1, :] & vds_ok[i, :, k + 1, :]
        est = np.where(herm, hermite_val(lo_, hi_, gdsid[i, :, k - 1, :], gdsid[i, :, k + 1, :], H, t),
                       lo_ + t * (hi_ - lo_))
        A = np.where(herm, hermite_val_absterms(lo_, hi_, gdsid[i, :, k - 1, :], gdsid[i, :, k + 1, :], H, t),
                     lin_abs(lo_, hi_, t))
        cond = on[i, :, k - 1, :] & o & on[i, :, k + 1, :]
        err = np.abs(est - c) / gm
        add(err, A, c, gm, cond, np.where(herm, 2.0 ** 4, 2.0 ** 2))
    if nS > 2:
        # [r7] CONTRACT 5절: VS 축 id_equivalent LOO 도 운영 보간과 같은 방법 -- 두 이웃 vs_ok 이면 Hermite(기울기 −GMBS/ID,
        # p = 4), 아니면 선형(p = 2). GMBS 열이 없으면 vs_ok 전부 거짓 -> r6 와 같은 선형.
        H = (VS[2:] - VS[:-2])[None, :]
        t = ((VS[1:-1] - VS[:-2]) / (VS[2:] - VS[:-2]))[None, :]
        vsl, vok = rs.vsslope[i, :, k, :], rs.vs_ok[i, :, k, :]
        herm = vok[:, :-2] & vok[:, 2:]
        est = np.where(herm, hermite_val(c[:, :-2], c[:, 2:], vsl[:, :-2], vsl[:, 2:], H, t),
                       c[:, :-2] + t * (c[:, 2:] - c[:, :-2]))
        A = np.where(herm, hermite_val_absterms(c[:, :-2], c[:, 2:], vsl[:, :-2], vsl[:, 2:], H, t),
                     lin_abs(c[:, :-2], c[:, 2:], t))
        cond = o[:, :-2] & o[:, 1:-1] & o[:, 2:]
        err = np.abs(est - c[:, 1:-1]) / gm[:, 1:-1]
        add(err, A, c[:, 1:-1], gm[:, 1:-1], cond, np.where(herm, 2.0 ** 4, 2.0 ** 2))
    if l_int:
        t = (Lg[i] - Lg[i - 1]) / (Lg[i + 1] - Lg[i - 1])
        lo_, hi_ = lI[i - 1, :, k, :], lI[i + 1, :, k, :]
        est = lo_ + t * (hi_ - lo_)
        cond = on[i - 1, :, k, :] & o & on[i + 1, :, k, :]
        err = np.abs(est - c) / gm
        add(err, lin_abs(lo_, hi_, t), c, gm, cond, 2.0 ** 2)
    # --- gm_id_inverse ---
    inv_s, inv_r, n_t, n_f = [], [], 0, 0
    inv_sb, inv_rb = [], []
    for s in range(nS):
        if not o[:, s].all():
            continue
        V, g = c[:, s], gm[:, s]
        p = int(np.argmax(g))
        side = []                                         # (V 곡선, S 곡선, 2^p, dV, dS)
        if 0 < k < nV - 1 and on[i, :, k - 1, s].all() and on[i, :, k + 1, s].all():
            H = VDS[k + 1] - VDS[k - 1]
            t = (VDS[k] - VDS[k - 1]) / H
            lo_, hi_ = lI[i, :, k - 1, s], lI[i, :, k + 1, s]
            herm = vds_ok[i, :, k - 1, s] & vds_ok[i, :, k + 1, s]
            m0_, m1_ = gdsid[i, :, k - 1, s], gdsid[i, :, k + 1, s]
            Vl = np.where(herm, hermite_val(lo_, hi_, m0_, m1_, H, t), lo_ + t * (hi_ - lo_))
            g0_, g1_ = gmid[i, :, k - 1, s], gmid[i, :, k + 1, s]
            Sl = g0_ + t * (g1_ - g0_)
            dV = g2 * np.where(herm, hermite_val_absterms(lo_, hi_, m0_, m1_, H, t), lin_abs(lo_, hi_, t))
            side.append((Vl, Sl, 2.0 ** 2, dV, g2 * lin_abs(g0_, g1_, t)))
        if 0 < s < nS - 1 and o[:, s - 1].all() and o[:, s + 1].all():
            # [r7] CONTRACT 5절: gm_id_inverse VS 축 곡선 -- ln ID 는 두 이웃의 VS Hermite(두 이웃 vs_ok 인 마디), gm/ID 는 선형,
            # 환산 차수 p = 2(표 'gm_id_inverse VS linear p 2').
            H = VS[s + 1] - VS[s - 1]
            t = (VS[s] - VS[s - 1]) / H
            lo_, hi_ = c[:, s - 1], c[:, s + 1]
            m0_, m1_ = rs.vsslope[i, :, k, s - 1], rs.vsslope[i, :, k, s + 1]
            herm = rs.vs_ok[i, :, k, s - 1] & rs.vs_ok[i, :, k, s + 1]
            Vl = np.where(herm, hermite_val(lo_, hi_, m0_, m1_, H, t), lo_ + t * (hi_ - lo_))
            dV = g2 * np.where(herm, hermite_val_absterms(lo_, hi_, m0_, m1_, H, t), lin_abs(lo_, hi_, t))
            side.append((Vl, gm[:, s - 1] + t * (gm[:, s + 1] - gm[:, s - 1]), 2.0 ** 2,
                         dV, g2 * lin_abs(gm[:, s - 1], gm[:, s + 1], t)))
        if l_int and on[i - 1, :, k, s].all() and on[i + 1, :, k, s].all():
            t = (Lg[i] - Lg[i - 1]) / (Lg[i + 1] - Lg[i - 1])
            lo_, hi_ = lI[i - 1, :, k, s], lI[i + 1, :, k, s]
            g0_, g1_ = gmid[i - 1, :, k, s], gmid[i + 1, :, k, s]
            side.append((lo_ + t * (hi_ - lo_), g0_ + t * (g1_ - g0_), 2.0 ** 2,
                         g2 * lin_abs(lo_, hi_, t), g2 * lin_abs(g0_, g1_, t)))
        for j in range(p, nG):
            if not all(g[j] > g[r] for r in range(j + 1, nG)):
                continue
            tg = float(g[j])
            curves = []
            if 0 < j < nG - 1:                                       # 격자 마디 그대로 -> 마디 차 0
                curves.append((np.delete(VGS, j), np.delete(V, j), np.delete(g, j), 2.0 ** 3, None, None))
            curves += [(VGS,) + sd for sd in side]
            for xs, cv, cs, w, dV_, dS_ in curves:
                n_t += 1
                if not with_roots:
                    sc = np.asarray(cs)
                    pp = int(np.argmax(sc))
                    dd = sc - tg
                    if not np.any(dd[pp:-1] * dd[pp + 1:] <= 0.0):
                        n_f += 1
                    continue
                st, root, rb = sir_ref_b(xs, cv, cs, tg, dV=dV_, dS=dS_)
                if st != "ok":
                    n_f += 1
                    continue
                inv_r.append(abs(root - VGS[j]))
                inv_s.append(abs(root - VGS[j]) / w)
                # 시도 값의 허용 차 = 근 차 상한 + |근 − VGS_j| 뺄셈 반올림(1 ulp). 셀 값은 최댓값이라
                # |max a − max b| ≤ max |a_i − b_i| -- 셀 허용 차 = 시도 허용 차의 최댓값.
                bnd = rb + math.ulp(max(abs(root), abs(float(VGS[j]))))
                inv_rb.append(bnd)
                inv_sb.append(bnd / w)
    mx = lambda xs: float(max(xs)) if xs else None
    return {"inv": mx(inv_s), "eq": mx(eq_s), "inv_loo": mx(inv_r), "eq_loo": mx(eq_r), "n_t": n_t, "n_f": n_f,
            "inv_bound": mx(inv_sb), "inv_loo_bound": mx(inv_rb), "eq_bound": mx(eq_sb), "eq_loo_bound": mx(eq_rb)}


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
    p = os.environ.get(env, default) if env else default
    if not p or not Path(p).is_file():
        pytest.fail("실데이터 없음: %s (%s=%r). 실데이터 test 는 skip 하지 않는다 -- 경로를 주거나 파일을 놓을 것"
                    % (what, env, p), pytrace=False)
    return p


@pytest.fixture(scope="session")
def real_location():
    """[r6] CONTRACT 1.8 '쓰는 법' 그대로: resolve_lut_location(저장소 설정, os.environ). 실패는 FAIL(skip 아님)."""
    if not LOCATION_CONFIG.is_file():
        pytest.fail("LUT v2 위치 설정 없음: %s" % LOCATION_CONFIG, pytrace=False)
    try:
        return resolve_lut_location(str(LOCATION_CONFIG), os.environ)
    except SchemaRejectedError as e:
        pytest.fail("LUT v2 데이터 위치를 풀지 못함(실데이터 test 는 skip 하지 않는다): %r" % (e.record.detail,),
                    pytrace=False)


@pytest.fixture(scope="session")
def real_paths(real_location):
    """[r6] LUT v2(위치 선언 파일) 하나. 다른 LUT 로 덮어쓰는 환경변수는 없다(O-180)."""
    loc = real_location
    if not loc.midpoints_path:
        pytest.fail("설정에 verify_midpoints 가 없다: %s" % LOCATION_CONFIG, pytrace=False)
    return {
        "manifest": _need(None, loc.manifest_path, "폭 슬라이스 manifest.json"),
        "cap": _need(None, loc.cap_npz_path, "기준 LUT npz"),
        "midpoints": loc.midpoints_path,
        "pdk_root": loc.pdk_root,
        "tlef": _need("GMID_PDK_TLEF", _DEFAULT_TLEF, "PDK tech LEF"),
    }


def load_real(paths, spec, **kw):
    """[r6] 1.8 '쓰는 법': load_lut_set(manifest, cap, spec, pdk_root=, verify_midpoints=). kw 로 덮어쓴다."""
    args = {"pdk_root": paths.get("pdk_root"), "verify_midpoints": paths.get("midpoints")}
    args.update(kw)
    return load_lut_set(paths["manifest"], paths["cap"], spec, **args)


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
    return load_real(real_paths, real_spec)


@pytest.fixture
def real_memo(real_lut):
    return new_memo(real_lut, 4096)


@functools.lru_cache(maxsize=6)
def _load_raw(path):
    with np.load(path) as z:
        return {k: np.array(z[k]) for k in z.files}


def _slice_files(manifest_path, grid):
    with open(manifest_path, encoding="utf-8") as f:
        man = json.load(f)
    dk = dict(REAL_DEVICE_KINDS)
    base = Path(manifest_path).parent
    out = []
    for s in man["slices"]:
        p = base / s["file"]
        with np.load(p) as z:
            W = float(z["W"])
        out.append((dk[s["device"]], s["device"], W, int(round(W / grid)), str(p)))
    return sorted(out, key=lambda t: (t[0], t[3]))


def _raw_getter(files):
    table = {(k, wk): p for k, _, _, wk, p in files}

    def get(kind, w_key):
        return _load_raw(table[(kind, w_key)])
    return get


@pytest.fixture(scope="session")
def raw_slice(real_slice_files):
    """raw_slice(kind, w_key) -> npz 배열 dict(직접 읽음)."""
    return _raw_getter(real_slice_files)


@pytest.fixture(scope="session")
def raw_cap(real_paths):
    return _load_raw(real_paths["cap"])


@pytest.fixture(scope="session")
def raw_mid(real_paths):
    """[r6] 검증 중점 파일 배열(직접 읽음)."""
    return _load_raw(real_paths["midpoints"])


def copy_tree(src_dir, dst_dir):
    shutil.copytree(src_dir, dst_dir)
    return Path(dst_dir)


def rel_close(a, b, rel):
    return abs(a - b) <= rel * max(abs(a), abs(b))


def ulp_steps_off_grid(W, grid):
    r = W / grid
    return abs(r - round(r)) / math.ulp(r)


# ---------------------------------------------------------------------------
# [r4] bin toy -- CONTRACT 1.2·1.3·1.4·4.0·4.0.1·5절·7절 끝 문단: meta 에 pdk_root·model_files_sha256 을 적고,
# 그 루트 아래 `.model` 블록(lmin·lmax·wmin·wmax)을 가진 작은 모델 파일을 둔다. 기대 bin 은 아래 표에서 손으로 정한다.
#
#   L 앵커(µm)   1   1.5   2  |  3   4  |  (C: 4~5, 앵커 0) | 빈틈 5~6 |  7   8  |  9
#   W 아래 범위 [0.5, 1] µm (폭 1e-6 슬라이스 = 경계 wmax -> 이 범위):
#     A = toyn__model.0 [1, 2]   B = .1 (2, 4]   C = .2 (4, 5]   D = .3 (6, 8]   E = .4 (8, 10]
#     anchor_bin = (0, 0, 0, 1, 1, 3, 3, 4)  (bins 정렬 = A, B, C, D, E)
#   W 위 범위 (1, 3] µm (폭 2e-6 슬라이스):  A' = .5 [1, 4]   D' = .6 (4, 10]  -> anchor_bin = (0, 0, 0, 0, 0, 1, 1, 1)
# ---------------------------------------------------------------------------

BIN_L = (1e-6, 1.5e-6, 2e-6, 3e-6, 4e-6, 7e-6, 8e-6, 9e-6)
BIN_MODEL_REL = "models/toy.pm3.spice"
BIN_W_LO = (0.5e-6, 1e-6)
BIN_W_HI = (1e-6, 3e-6)
BIN_BLOCKS = (
    ("toyn__model.0", 1e-6, 2e-6) + BIN_W_LO,
    ("toyn__model.1", 2e-6, 4e-6) + BIN_W_LO,
    ("toyn__model.2", 4e-6, 5e-6) + BIN_W_LO,
    ("toyn__model.3", 6e-6, 8e-6) + BIN_W_LO,
    ("toyn__model.4", 8e-6, 10e-6) + BIN_W_LO,
    ("toyn__model.5", 1e-6, 4e-6) + BIN_W_HI,
    ("toyn__model.6", 4e-6, 10e-6) + BIN_W_HI,
)
BIN_ANCHOR_BIN_LO = (0, 0, 0, 1, 1, 3, 3, 4)
BIN_ANCHOR_BIN_HI = (0, 0, 0, 0, 0, 1, 1, 1)


def bin_model_text(blocks=BIN_BLOCKS, extra=""):
    """sky130 pm3 모양 모델 파일: 블록마다 `.model 이름 nmos` + `+ lmin = .. lmax = .. wmin = .. wmax = ..` 연속 줄.
    값은 repr(float)(왕복 정확). bin 아닌 `.model` 블록 하나를 앞에 둔다(무시돼야 한다)."""
    out = ["* toy binned model file (test)", ".param toy_vth = 0.4",
           ".model toyn__plain nmos", "+ level = 54 vth0 = 0.4"]
    for name, lmin, lmax, wmin, wmax in blocks:
        out += [".model %s nmos" % name,
                "+ level = 54",
                "+ lmin = %r lmax = %r wmin = %r wmax = %r" % (lmin, lmax, wmin, wmax),
                "+ vth0 = 0.4 rdsw = 100.0"]
    if extra:
        out.append(extra)
    return "\n".join(out) + "\n"


def bin_slice_arrays(W, scale, meta, L=BIN_L, n_vgs=3, consistent=False):
    """bin toy 슬라이스(Lu = L/µm, VTH = 0.4 + 0.01·Lu² -- L 에 비선형이라 선형 보간과 정확값이 갈린다).
    n_vgs = 2 면 VGS 앞 두 점만(내부 VGS 격자점 없음).
    [r7 2026-10-09 단위 검사 복원(CONTRACT 1.4)] 기울기 자료를 ln ID 의 편미분에서 만든다(oracle (a) 구성 -- 닫힌 식 하나에서 ID·GM·GDS):
      ln ID = −ln Lu + ln 1e-7 + c·P(v) + k(L)·(d − d²/4) + ln (1, 0.5)[VS] + ln scale,
      GM/ID = c·P'(v),  GDS/ID = k(L)·(1 − d/2),  k(L) = 0.2 − 0.01·Lu (L 에 선형 -> L 방향 LOO 에 몫이 없다).
      VDS 몫이 2차식이라 VDS 칸 현 기울기 k·(1 − 3/8) 가 두 끝 기울기 k·(0.75, 0.5) 사이(경계 위가 아니다) -- VDS Hermite 정확.
    기본(consistent=False) = r4 toy 의 VGS 자료를 c 배: P = (0, ln10, ln10 + 1.5)[VGS], P' = (20, 4, 1.5) -- 칸 0 FC 위반·칸 1 단조
      (현·기울기를 같은 c 배 해도 FC 의 b 계수가 c 배라 판정이 같다), 현은 두 끝 기울기 사이(R4_* 주석 손계산).
      c = 1 + 0.01·Lu²(L 에 2차): L 방향 LOO 의 gm/ID 추정이 참값과 유한하게 다르다 -- c 가 L 에 선형이면 추정 곡선의 마디 gm/ID 가
      목표(그 행의 마디 gm/ID)와 반올림 수준으로만 달라 3절 칸 선택(편차 곱 ≤ 0)이 반올림 부호로 갈리고, 이웃 칸이 FC 위반이면
      근이 칸 하나만큼 달라진다(독립 구현과 엔진이 같은 규칙인데 반올림만으로 갈리는 잘 정의되지 않은 입력).
      옛 판(ID 마디 (1e-7, 1e-6, 1e-5), GM/ID = (20, 10, 4)·c, GDS = ID/(10·Lu), ID 는 VDS 무관)은 VDS 칸 모두·VGS 칸 과반이 1.4 위반.
    consistent=True: c = 1 + 0.1·Lu, P = 20v − 6v², P' = 20 − 12v (VGS 2차식 -- Hermite 정확, FC 위반 없음; c 가 L 에 선형이라
      L 방향 LOO 에서 VGS 몫이 정확 -- test_tolerance 손계산)."""
    nL = len(L)
    Lu = np.asarray(L) / 1e-6
    c_L = 1.0 + 0.1 * Lu if consistent else 1.0 + 0.01 * Lu ** 2
    k_L = 0.2 - 0.01 * Lu
    v_ = np.asarray(TOY_VGS[:n_vgs])
    d_ = np.asarray(TOY_VDS)
    if consistent:
        P = R5_A * v_ - R5_B * v_ ** 2
        dP = R5_A - 2 * R5_B * v_
    else:
        P = np.log(np.asarray(R4_ID_VGS[:n_vgs]) / R4_ID_VGS[0])
        dP = np.asarray(R4_GM_RATIO[:n_vgs])
    lnID = (-np.log(Lu)[:, None, None, None] + math.log(1e-7) + c_L[:, None, None, None] * P[None, :, None, None]
            + k_L[:, None, None, None] * (d_ - 0.25 * d_ ** 2)[None, None, :, None]
            + np.log(np.asarray(TOY_VS_FACTOR))[None, None, None, :])
    ID = np.exp(lnID) * scale
    GM = ID * (c_L[:, None, None, None] * dP[None, :, None, None])
    GDS = ID * (k_L[:, None, None, None] * (1.0 - 0.5 * d_)[None, None, :, None])
    VTH = np.empty_like(ID)
    VTH[...] = (0.4 + 0.01 * Lu ** 2)[:, None, None, None]
    return {
        "W": np.float64(W),
        "L": np.asarray(L), "VGS": np.asarray(TOY_VGS[:n_vgs]), "VDS": np.asarray(TOY_VDS), "VS": np.asarray(TOY_VS),
        "ID": ID, "GM": GM, "GDS": GDS, "VTH": VTH,
        "meta_json": np.str_(json.dumps(meta)),
        "corner": np.str_("tt"), "temp_c": np.float64(27.0),
    }


def bin_cap_arrays(L=BIN_L, n_vgs=3):
    Lu = np.asarray(L) / 1e-6
    shp = (len(L), n_vgs, 2, 2)
    CGG = np.empty(shp)
    CGG[...] = (1e-15 * Lu ** 2)[:, None, None, None]
    CGD = np.empty(shp)
    CGD[...] = (2e-16 * Lu)[:, None, None, None]
    return {
        "L": np.asarray(L), "VGS": np.asarray(TOY_VGS[:n_vgs]), "VDS": np.asarray(TOY_VDS), "VS": np.asarray(TOY_VS),
        "CGG_n": CGG, "CGD_n": CGD,
        "w_ref_m": np.float64(1e-6), "corner": np.str_("tt"), "temp_c": np.float64(27.0),
    }


class BinToy:
    """bin toy 를 tmp 폴더에 쓴다. pdk 루트 = <root>/pdk, 모델 파일 = BIN_MODEL_REL. 슬라이스 2장(폭 1e-6·2e-6).

    meta_fn(meta) -> meta: 기록을 바꿔 거부 경로를 만든다. model_text=None 이면 모델 파일을 쓰지 않는다."""

    def __init__(self, root, model_text, meta_fn=None, L=BIN_L, widths=((1e-6, 1.0), (2e-6, 2.0)), n_vgs=3,
                 consistent=False):
        self.root = Path(root)
        self.pdk = self.root / "pdk"
        self.model_path = self.pdk / BIN_MODEL_REL
        self.model_path.parent.mkdir(parents=True, exist_ok=True)
        if model_text is not None:
            self.model_path.write_text(model_text, encoding="utf-8")
            sha = sha256_file(self.model_path)
        else:
            sha = "e" * 64
        meta = {"pdk_root": str(self.pdk), "model_files_sha256": {BIN_MODEL_REL: sha}}
        if meta_fn is not None:
            meta = meta_fn(meta)
        self.meta = meta
        slices = [("bin_w%d.npz" % i, "toyn", bin_slice_arrays(W, sc, meta, L, n_vgs, consistent))
                  for i, (W, sc) in enumerate(widths)]
        self.build = ToyBuild(self.root / "lut", slices, bin_cap_arrays(L, n_vgs))
        self.slice_paths = [self.build.root / s[0] for s in slices]

    def load(self, spec=TOY_SPEC):
        return self.build.load(spec)


@pytest.fixture
def bin_toy_build(tmp_path):
    """bin_toy_build(sub, blocks=BIN_BLOCKS, extra="", model_text=None, meta_fn=None, L=BIN_L) -> BinToy."""
    def make(sub="bt", blocks=BIN_BLOCKS, extra="", model_text=None, meta_fn=None, **kw):
        if model_text is None:
            model_text = bin_model_text(blocks, extra)
        elif model_text is False:
            model_text = None
        return BinToy(tmp_path / sub, model_text, meta_fn, **kw)
    return make


@pytest.fixture
def bin_toy(bin_toy_build):
    return bin_toy_build().load()


@pytest.fixture
def bin_memo(bin_toy):
    return new_memo(bin_toy)


def bin_toy_raw(scale=1.0, W=1e-6, consistent=False):
    """bin toy 슬라이스 배열(독립 기대값 계산용 -- meta 는 값 계산에 쓰지 않는다)."""
    return bin_slice_arrays(W, scale, {}, consistent=consistent)


def two_sheet(L_grid, L):
    """같은 bin 보간의 L 장: (k−1, k), k = bisect_right(L 격자, L)."""
    k = bisect.bisect_right(list(L_grid), L)
    return k - 1, k


def sheet_interp(z, name, L, vgs, vds, vs, log=True):
    """4.0 같은 bin 보간의 독립 구현: L 격자 = (below, above) 두 장, (L, VGS, VDS, VS) 다중선형.
    log=True 면 ln(clip(배열, 최소 양수))(1.4) 공간 값을 돌려준다."""
    lo, hi = two_sheet(z["L"], L)
    arr = np.asarray(z[name], dtype=float)
    if log:
        arr, _ = log_floor(arr)
    sub = arr[lo:hi + 1]
    grids = ((float(z["L"][lo]), float(z["L"][hi])), tuple(z["VGS"]), tuple(z["VDS"]), tuple(z["VS"]))
    return interp4(grids, sub, (L, vgs, vds, vs))


def expected_op(z, L, vgs, vds, vs):
    """op_point 의 독립 기대값 -- [r5] 4.2 축별 보간(RefSlice: VGS·VDS Hermite, VS·L 선형, ln GDS·VTH 선형)을
    4.0 같은 bin 보간의 L 장 (below, above) 에서. (r4 의 4축 다중선형 `sheet_interp` 대체; 용량은 여전히 sheet_interp.)"""
    lo, hi = two_sheet(z["L"], L)
    Lg = [float(x) for x in z["L"]]
    t = (L - Lg[lo]) / (Lg[hi] - Lg[lo])
    Lw = tuple((i, w) for i, w in ((lo, 1.0 - t), (hi, t)) if w != 0.0)
    r = RefSlice(z).op(Lw, L, vgs, vds, vs)
    return {f: r[f] for f in ("IDu", "gm_over_id", "gm_gds", "gds_per_w", "vth")}


# ---------------------------------------------------------------------------
# [r4] ngspice showmod -- 시뮬레이터가 실제로 고른 bin(lmin, lmax, wmin, wmax). 엔진과 독립인 bin 소속의 참값.
# ---------------------------------------------------------------------------

_DEFAULT_NGSPICE = r"C:\ngspice\Spice64\bin\ngspice_con.exe"


def parse_model_bins(path):
    """모델 파일의 `.model 이름` 블록 -> {이름: (lmin, lmax, wmin, wmax)} (test 쪽 독립 파서, 키는 단어 경계)."""
    text = Path(path).read_text(encoding="utf-8", errors="replace")
    out = {}
    for m in re.finditer(r"^\.model\s+(\S+)(.*?)(?=^\.model|\Z)", text, re.S | re.I | re.M):
        vals = {}
        for key in ("lmin", "lmax", "wmin", "wmax"):
            mm = re.search(r"(?<![A-Za-z0-9_])%s\s*=\s*([-+0-9.eE]+)" % key, m.group(2), re.I)
            if mm:
                vals[key] = float(mm.group(1))
        if len(vals) == 4:
            out[m.group(1)] = (vals["lmin"], vals["lmax"], vals["wmin"], vals["wmax"])
    return out


class NgspiceBins:
    """showmod 로 (device, W µm, L µm) 의 실제 bin 을 잰다. 한 device 의 점들은 한 번의 ngspice 실행(인스턴스 여러 개)."""

    def __init__(self, exe, workdir, real_manifest, manifest_path):
        self.exe = exe
        self.workdir = Path(workdir)
        self.cache = {}
        self.files = {}
        base = Path(manifest_path).parent
        for s in real_manifest["slices"]:
            if s["device"] in self.files:
                continue
            with np.load(base / s["file"]) as z:
                meta = json.loads(str(z["meta_json"]))
            self.files[s["device"]] = [os.path.join(meta["pdk_root"], rel) for rel in meta["model_files_sha256"]
                                       if rel.endswith(".spice")]

    def pm3(self, device):
        return [f for f in self.files[device] if f.endswith(".pm3.spice")][0]

    def query(self, device, pts):
        """pts: [(W µm, L µm)] -> [(lmin, lmax, wmin, wmax) | None(유효 모델 없음)] (m)."""
        todo = sorted({p for p in pts if (device, p) not in self.cache})
        if todo:
            lines = ["* showmod bin probe"] + ['.include "%s"' % f for f in self.files[device]]
            lines.append("vd d 0 dc 0")
            for n, (w, l) in enumerate(todo):
                lines.append("x%d d d 0 0 sky130_fd_pr__%s l=%.6fu w=%.6fu nf=1" % (n, device, l, w))
            lines += [".control", "op"]
            for n in range(len(todo)):
                lines.append("echo BINPT %d" % n)
                lines.append("showmod m.x%d.msky130_fd_pr__%s : lmin lmax wmin wmax" % (n, device))
            lines += ["quit", ".endc", ".end"]
            cir = self.workdir / ("probe_%s_%d.cir" % (device, len(self.cache)))
            cir.write_text("\n".join(lines) + "\n", encoding="utf-8")
            r = subprocess.run([self.exe, "-b", str(cir)], capture_output=True, text=True, timeout=600)
            (self.workdir / (cir.name + ".log")).write_text(r.stdout + "\n--stderr--\n" + r.stderr, encoding="utf-8")
            got = {}
            cur = None
            for ln in r.stdout.splitlines():
                t = ln.split()
                if len(t) == 2 and t[0] == "BINPT":
                    cur = int(t[1])
                    got[cur] = {}
                elif cur is not None and len(t) == 2 and t[0] in ("lmin", "lmax", "wmin", "wmax"):
                    got[cur][t[0]] = float(t[1])
            if not got:
                pytest.fail("ngspice showmod 출력을 못 읽음: %s" % cir, pytrace=False)
            for n, p in enumerate(todo):
                v = got.get(n, {})
                self.cache[(device, p)] = (v["lmin"], v["lmax"], v["wmin"], v["wmax"]) if len(v) == 4 else None
        return [self.cache[(device, p)] for p in pts]


@pytest.fixture(scope="session")
def ngspice_bins(real_paths, real_manifest, tmp_path_factory):
    exe = os.environ.get("GMID_NGSPICE", _DEFAULT_NGSPICE)
    if not Path(exe).is_file():
        pytest.fail("ngspice 없음 (GMID_NGSPICE=%r) -- bin 참값 test 는 skip 하지 않는다" % exe, pytrace=False)
    return NgspiceBins(exe, tmp_path_factory.mktemp("ngspice_bins"), real_manifest, real_paths["manifest"])


def same_bounds(a, b, rel=1e-9):
    return a is not None and b is not None and all(abs(x - y) <= rel * max(abs(x), abs(y)) for x, y in zip(a, b))


def um(x):
    """m -> µm 6자리(ngspice 인스턴스 값과 같은 표기)."""
    return round(x * 1e6, 6)


# ---------------------------------------------------------------------------
# [r6] 선택 열·검증 중점 파일 toy 와 독립 기대값 경로 (CONTRACT 1.2·1.7·4.3·4.4·5.1·5.2·7.1 r6 표)
# ---------------------------------------------------------------------------

def width_key_ref(w_m, grid):
    """CONTRACT 1.3 폭 키 규칙의 독립 구현: (round(W/grid), |W/grid − 키| ≤ 2·ulp(W/grid))."""
    r = w_m / grid
    k = int(round(r))
    return k, abs(r - k) <= 2 * math.ulp(r)


def r6_toy_cap_arrays():
    """CONTRACT 7.1 r6 표 마지막 행: r5 toy 기준 LUT + GMBS_n = 0.25·ID_n, ID_n = 폭 1e-6 슬라이스 ID,
    VDSAT_n = 0.1 + 0.2·VGS (축 broadcast). GM_n 은 없다(-> CapTable.on_mask None)."""
    cap = toy_cap_arrays()
    ID = toy_id(1.0)
    cap["ID_n"] = ID
    cap["GMBS_n"] = 0.25 * ID
    V = np.empty(ID.shape)
    V[...] = (0.1 + 0.2 * np.asarray(TOY_VGS))[None, :, None, None]
    cap["VDSAT_n"] = V
    return cap


# 중점 toy (bin toy 와 같은 모델 파일·L 앵커 BIN_L·bin 표):
#   [r7 2026-10-09 단위 검사 복원(CONTRACT 1.4)] ln ID 닫힌 식 하나에서 GM·GDS·GMBS 를 편미분으로 만든다(oracle (a) 구성):
#   ln ID = −ln Lu + ln 1e-7 + c(L)·(20v − 6v²) + 0.1·d − 0.3·[(1 + 0.1·v + 0.2·d)·s + 0.025·s²] + ln scale,
#           c(L) = 1 + MID_ALPHA·Lu²  (Lu = L/µm)
#   GM/ID = c(L)·(20 − 12v) − 0.03·s,  GDS/ID = 0.1 − 0.06·s,  GMBS/ID = −∂lnID/∂s = 0.3·(1 + 0.1·v + 0.2·d + 0.05·s)
#   (GMBS/ID 가 모든 축 선형 -> gmb 의 r 보간이 정확 -- 옛 판과 같은 GMBS/ID; 옛 판은 ln ID 의 VS 몫이 ln(1, 0.5) 라 VS 칸 현 −1.39 가
#   −GMBS/ID ≈ −0.3~−0.4 와 모순, 1.4 단위 검사로 모든 VS 칸 위반 -> 로드 거부), VTH 0.4, FC 위반 없음(VGS 2차·VDS 1차·VS 2차).
#   VDSAT = 0.1 + 0.2·v + 0.05·Lu²·(1 + d)        (L 에 2차 -> 중점 선형 보간 오차 = 0.05·(Lu_m − Lu0)(Lu1 − Lu_m)·(1 + d))
# c(L) 이 L 에 2차라 중점의 gm/ID 곡선 L 선형 보간도 참값과 갈린다(gm_id_inverse 가 0 이 아님 -- 판별력).
MID_ALPHA = 0.01
MID_GMBS0 = 0.3


def mid_toy_arrays(W, scale, meta, L=BIN_L, cols=("GMBS", "VDSAT"), n_vgs=3):
    Lu = np.asarray(L, dtype=float) / 1e-6
    c = 1.0 + MID_ALPHA * Lu ** 2
    v = np.asarray(TOY_VGS[:n_vgs])
    d = np.asarray(TOY_VDS)
    s = np.asarray(TOY_VS)
    q = R5_A * v - R5_B * v * v
    v4, d4, s4 = v[None, :, None, None], d[None, None, :, None], s[None, None, None, :]
    lnID = (-np.log(Lu)[:, None, None, None] + math.log(1e-7) + c[:, None, None, None] * q[None, :, None, None]
            + R5_C * d4 - MID_GMBS0 * ((1 + 0.1 * v4 + 0.2 * d4) * s4 + 0.025 * s4 * s4))
    ID = np.exp(lnID) * scale
    GM = ID * (c[:, None, None, None] * (R5_A - 2 * R5_B * v4) - MID_GMBS0 * 0.1 * s4)
    GDS = ID * (R5_C - MID_GMBS0 * 0.2 * s4)
    out = {
        "W": np.float64(W),
        "L": np.asarray(L, dtype=float), "VGS": v.copy(), "VDS": d.copy(), "VS": s.copy(),
        "ID": ID, "GM": GM, "GDS": GDS, "VTH": np.full(ID.shape, 0.4),
        "meta_json": np.str_(json.dumps(meta)), "corner": np.str_("tt"), "temp_c": np.float64(27.0),
    }
    if "VDSAT" in cols:
        out["VDSAT"] = mid_vdsat(L, n_vgs)
    if "GMBS" in cols:
        out["GMBS"] = ID * mid_gmbs_per_id(len(L), n_vgs)
    return out


def mid_vdsat(L, n_vgs=3):
    Lu = np.asarray(L, dtype=float) / 1e-6
    v = np.asarray(TOY_VGS[:n_vgs])
    d = np.asarray(TOY_VDS)
    V = (0.1 + 0.2 * v[None, :, None, None] + 0.05 * (Lu ** 2)[:, None, None, None] * (1 + d)[None, None, :, None])
    return np.broadcast_to(V, (len(L), n_vgs, len(d), len(TOY_VS))).copy()


def mid_gmbs_per_id(nL, n_vgs=3):
    v = np.asarray(TOY_VGS[:n_vgs])
    d = np.asarray(TOY_VDS)
    s = np.asarray(TOY_VS)
    r = MID_GMBS0 * (1 + 0.1 * v[:, None, None] + 0.2 * d[None, :, None] + 0.05 * s[None, None, :])
    return np.broadcast_to(r[None], (nL, n_vgs, len(d), len(s))).copy()


def mid_point_arrays(L_points, w_ref_m=1e-6, scale=1.0, kinds=(("nmos", "_n"),), l_source=None, vdsat=True,
                     drop=(), corner="tt", temp_c=27.0, axes=None):
    """CONTRACT 1.7 검증 중점 파일 형식: L(중점)·VGS·VDS·VS, kind 마다 ID<접미사>·GM<접미사>(·VDSAT<접미사>), w_ref_m,
    corner·temp_c, meta_json L_source. 값 = 중점 toy 식을 L_points 에서(폭 w_ref_m = scale·1e-6)."""
    z = mid_toy_arrays(w_ref_m, scale, {}, L=L_points, cols=("VDSAT",) if vdsat else ())
    out = {"L": np.asarray(L_points, dtype=float), "VGS": z["VGS"], "VDS": z["VDS"], "VS": z["VS"],
           "corner": np.str_(corner), "temp_c": np.float64(temp_c)}
    if axes:
        out.update(axes)
    if w_ref_m is not None:
        out["w_ref_m"] = np.float64(w_ref_m)
    for _, suf in kinds:
        out["ID" + suf] = z["ID"]
        out["GM" + suf] = z["GM"]
        if vdsat:
            out["VDSAT" + suf] = z["VDSAT"]
    for k in drop:
        out.pop(k, None)
    meta = {"generator": "test"}
    if l_source is not None:
        meta["L_source"] = l_source
    out["meta_json"] = np.str_(json.dumps(meta))
    return out


MID_L_SOURCE = {"kind": "json", "path": "approved_L.json", "sha256": "a" * 64, "key": "verification_midpoints_um"}


class MidToy:
    """중점 toy: bin toy 모델 파일(BIN_BLOCKS) + 중점 toy 슬라이스(폭 1e-6·2e-6) + 기준 LUT(bin_cap_arrays + 선택 열)
    + 검증 중점 파일. slice_cols: 슬라이스 선택 열, cap_extra: 기준 LUT 에 더할 배열 dict, cap_meta: 기준 LUT meta_json."""

    def __init__(self, root, slice_cols=("GMBS", "VDSAT"), cap_extra=None, cap_meta=None, mid=None,
                 widths=((1e-6, 1.0), (2e-6, 2.0)), model_text=None, slice_mod=None):
        self.root = Path(root)
        self.pdk = self.root / "pdk"
        mp = self.pdk / BIN_MODEL_REL
        mp.parent.mkdir(parents=True, exist_ok=True)
        mp.write_text(bin_model_text() if model_text is None else model_text, encoding="utf-8")
        meta = {"pdk_root": str(self.pdk), "model_files_sha256": {BIN_MODEL_REL: sha256_file(mp)}}
        slices = [("mid_w%d.npz" % i, "toyn", mid_toy_arrays(W, sc, meta, cols=slice_cols))
                  for i, (W, sc) in enumerate(widths)]
        if slice_mod is not None:
            slice_mod([s[2] for s in slices])
        self.slice_arrays = [s[2] for s in slices]
        cap = bin_cap_arrays()
        if cap_extra:
            cap.update(cap_extra)
        if cap_meta is not None:
            cap["meta_json"] = np.str_(json.dumps(cap_meta))
        self.build = ToyBuild(self.root / "lut", slices, cap)
        self.mid_path = None
        if mid is not None:
            self.mid_path = self.root / "lut" / "midpoints.npz"
            np.savez(self.mid_path, **mid)

    def load(self, spec=TOY_SPEC, **kw):
        if self.mid_path is not None and "verify_midpoints" not in kw:
            kw["verify_midpoints"] = str(self.mid_path)
        return load_lut_set(str(self.build.manifest), str(self.build.cap), spec, **kw)


@pytest.fixture
def mid_toy_build(tmp_path):
    def make(sub="mt", **kw):
        return MidToy(tmp_path / sub, **kw)
    return make


# --- 독립 구현: 4.0.1 bin 소속, 5.1 중점 외부 값, 5.2 VDSAT LOO -----------------------------------------------

def bin_index_ref(bounds, x):
    """CONTRACT 4.0.1: lo ≤ x ≤ hi(양끝 닫힘, 경계 1 ulp 이내 같은 값), 둘 다 품으면 lo 가 작은 구간. bounds 는 lo 오름차순."""
    for i, (lo, hi) in enumerate(bounds):
        if (x >= lo or abs(x - lo) <= math.ulp(lo)) and (x <= hi or abs(x - hi) <= math.ulp(hi)):
            return i
    return None


def lin_cell_weights(grid, x):
    """4.2 칸 규칙의 선형 가중치(가중치 0 인 마디 제외)."""
    return axis_weights(grid, x)


def lin_point_ref(grids, arr, Lw, vgs, vds, vsb):
    """모든 축 선형(값 공간) -- Lw = ((L index, 가중치), ...), 나머지 축은 grids[1:] 위 4.2 칸 규칙."""
    tot = 0.0
    for iL, wl in Lw:
        for g, wg in axis_weights(grids[1], vgs):
            for b, wd in axis_weights(grids[2], vds):
                for s, ws in axis_weights(grids[3], vsb):
                    tot += wl * wg * wd * ws * float(arr[iL, g, b, s])
    return tot


def gmb_column_ref(z, Lw, vgs, vds, vsb, gmbs=None, idcol=None, grids=None):
    """CONTRACT 4.4 [r6] gmb 정본(GMBS 열)의 독립 구현: gmb = ID(점) × r, ID(점) = exp(4.2 축별 보간 lnID)(= IDu·w_m/L),
    r = GMBS/ID(ID > 0, 아니면 NaN) 의 L 장 + 모든 축 선형 보간; r 이 NaN 이면 gmb = GMBS 의 같은 선형 보간
    ([해석] 그 값이 곧 gmb -- GMBS 는 A/V 라 ID 를 다시 곱하지 않는다).
    gmbs·idcol·grids: 열 출처 표의 배열·축(없으면 슬라이스 z 의 GMBS·ID·축 -- origin "slice")."""
    rs = RefSlice(z)
    idp = math.exp(rs.op(Lw, 1.0, vgs, vds, vsb)["lnID"])
    G = np.asarray(z["GMBS"] if gmbs is None else gmbs, dtype=float)
    I = np.asarray(z["ID"] if idcol is None else idcol, dtype=float)
    gr = rs.grids if grids is None else grids
    with np.errstate(divide="ignore", invalid="ignore"):
        R = np.where(I > 0, G / np.where(I > 0, I, 1.0), np.nan)
    r = lin_point_ref(gr, R, Lw, vgs, vds, vsb)
    if math.isnan(r):
        return lin_point_ref(gr, G, Lw, vgs, vds, vsb)
    return idp * r


def branch_targets_ref(g):
    """5절 목표 규칙: 정점 이후 index 중 오른쪽 모든 점보다 g_j 가 큰 점."""
    g = np.asarray(g, dtype=float)
    p = int(np.argmax(g))
    return [j for j in range(p, len(g)) if all(g[j] > g[r] for r in range(j + 1, len(g)))]


def midpoint_ref(slice_z, mid_z, suffix, L_m_index, i0, i1, vdsat_src=None, src_on=None):
    """CONTRACT 5.1 한 중점(L 축 index L_m_index)의 세 값(VDS 격자점 k 마다)과 목표·실패 수 -- numpy 직접.
    slice_z: 슬라이스 npz 배열, mid_z: 중점 npz 배열, i0·i1: 감싸는 앵커 index, vdsat_src: 출처 VDSAT 배열(4.3 규칙으로 고른 것)
    또는 None, src_on: 출처 on_mask(없으면 None -> 생략). 반환 dict(inv, eq, vdsat: k 별 list(값 또는 None), n_t, n_f, bound_*)."""
    Lg = np.asarray(slice_z["L"], dtype=float)
    VGS = np.asarray(slice_z["VGS"], dtype=float)
    nV = len(slice_z["VDS"])
    nS = len(slice_z["VS"])
    L_m = float(mid_z["L"][L_m_index])
    t = (L_m - Lg[i0]) / (Lg[i1] - Lg[i0])
    lI = log_floor(slice_z["ID"])[0]
    lG = log_floor(slice_z["GM"])[0]
    on = (slice_z["ID"] > 0) & (slice_z["GM"] > 0)
    gmid_a = np.exp(lG - lI)
    Im = np.asarray(mid_z["ID" + suffix][L_m_index], dtype=float)
    Gm = np.asarray(mid_z["GM" + suffix][L_m_index], dtype=float)
    mon = (Im > 0) & (Gm > 0)
    with np.errstate(divide="ignore", invalid="ignore"):
        lIm = np.where(Im > 0, np.log(np.where(Im > 0, Im, 1.0)), np.nan)
        gm_m = np.where(Im > 0, Gm / np.where(Im > 0, Im, 1.0), np.nan)
    mask = mon & on[i0] & on[i1]                                     # [VGS, VDS, VS]
    est = lI[i0] + t * (lI[i1] - lI[i0])
    g2 = 2 * gamma_n()
    eq, eqb, inv, invb, vd = [], [], [], [], []
    n_t = n_f = 0
    for k in range(nV):
        mk = mask[:, k, :]
        if mk.any():
            e = np.abs(est[:, k, :] - lIm[:, k, :]) / gm_m[:, k, :]
            A = (1 + abs(t)) * np.abs(lI[i0][:, k, :]) + abs(t) * np.abs(lI[i1][:, k, :]) + np.abs(lIm[:, k, :])
            eq.append(float(e[mk].max()))
            eqb.append(float((g2 * A / gm_m[:, k, :] + g2 * e)[mk].max()))
        else:
            eq.append(None)
            eqb.append(None)
        best = None
        bb = None
        for s in range(nS):
            if not mask[:, k, s].all():
                continue
            gcur = gm_m[:, k, s]
            Vc = est[:, k, s]
            Sc = gmid_a[i0][:, k, s] + t * (gmid_a[i1][:, k, s] - gmid_a[i0][:, k, s])
            dV = g2 * ((1 + abs(t)) * np.abs(lI[i0][:, k, s]) + abs(t) * np.abs(lI[i1][:, k, s]))
            dS = g2 * ((1 + abs(t)) * np.abs(gmid_a[i0][:, k, s]) + abs(t) * np.abs(gmid_a[i1][:, k, s]))
            for j in branch_targets_ref(gcur):
                n_t += 1
                st, root, rb = sir_ref_b(VGS, Vc, Sc, float(gcur[j]), dV=dV, dS=dS)
                if st != "ok":
                    n_f += 1
                    continue
                val = abs(root - VGS[j])
                b = rb + math.ulp(max(abs(root), abs(float(VGS[j]))))
                if best is None or val > best:
                    best = val
                bb = b if bb is None else max(bb, b)
        inv.append(best)
        invb.append(bb)
        if vdsat_src is not None and ("VDSAT" + suffix) in mid_z:
            Vm = np.asarray(mid_z["VDSAT" + suffix][L_m_index], dtype=float)
            vm = mon[:, k, :].copy()
            if src_on is not None:
                vm &= src_on[i0][:, k, :] & src_on[i1][:, k, :]
            if vm.any():
                ve = vdsat_src[i0][:, k, :] + t * (vdsat_src[i1][:, k, :] - vdsat_src[i0][:, k, :])
                vd.append(float(np.abs(ve - Vm[:, k, :])[vm].max()))
            else:
                vd.append(None)
        else:
            vd.append(None)
    return {"inv": inv, "eq": eq, "vdsat": vd, "n_t": n_t, "n_f": n_f, "inv_bound": invb, "eq_bound": eqb}


def vdsat_loo_cell_ref(grids, V, on, i, k, l_int):
    """CONTRACT 5.2 셀 (i, k) 독립 구현: 축마다 내부 격자점을 빼고 두 이웃 선형 추정, 점 조건 = 그 점·축 방향 두 이웃이 on
    (on None 이면 모든 점), L 축은 l_int(bin 안 내부 앵커)일 때만. 반환 (환산 전 셀 최댓값, 환산 후 = /2^2 의 최댓값, 상한)."""
    Lg, VGS, VDS, VS = (np.asarray(g, dtype=float) for g in grids)
    allon = np.ones(V.shape, dtype=bool) if on is None else on
    vals, bnds = [], []
    c = V[i, :, k, :]
    o = allon[i, :, k, :]
    g2 = 2 * gamma_n()

    def add(est, ref, lo_, hi_, t, cond):
        err = np.abs(est - ref)
        bnd = g2 * ((1 + np.abs(t)) * np.abs(lo_) + np.abs(t) * np.abs(hi_) + np.abs(ref))
        vals.extend(np.broadcast_to(err, cond.shape)[cond])
        bnds.extend(np.broadcast_to(bnd, cond.shape)[cond])
    if len(VGS) > 2:
        t = ((VGS[1:-1] - VGS[:-2]) / (VGS[2:] - VGS[:-2]))[:, None]
        add(c[:-2] + t * (c[2:] - c[:-2]), c[1:-1], c[:-2], c[2:], t, o[:-2] & o[1:-1] & o[2:])
    if 0 < k < len(VDS) - 1:
        t = (VDS[k] - VDS[k - 1]) / (VDS[k + 1] - VDS[k - 1])
        lo_, hi_ = V[i, :, k - 1, :], V[i, :, k + 1, :]
        add(lo_ + t * (hi_ - lo_), c, lo_, hi_, t, allon[i, :, k - 1, :] & o & allon[i, :, k + 1, :])
    if len(VS) > 2:
        t = ((VS[1:-1] - VS[:-2]) / (VS[2:] - VS[:-2]))[None, :]
        add(c[:, :-2] + t * (c[:, 2:] - c[:, :-2]), c[:, 1:-1], c[:, :-2], c[:, 2:], t, o[:, :-2] & o[:, 1:-1] & o[:, 2:])
    if l_int:
        t = (Lg[i] - Lg[i - 1]) / (Lg[i + 1] - Lg[i - 1])
        lo_, hi_ = V[i - 1, :, k, :], V[i + 1, :, k, :]
        add(lo_ + t * (hi_ - lo_), c, lo_, hi_, t, allon[i - 1, :, k, :] & o & allon[i + 1, :, k, :])
    if not vals:
        return None, None, None
    return float(max(vals)), float(max(vals)) / 4.0, float(max(bnds))


# ---------------------------------------------------------------------------
# [r7] 잡음·mismatch toy (CONTRACT 9.1·9.6·10.1·10.4) -- 입력은 이 파일이 닫힌 식으로 만든다(피검 함수 미사용).
#   기준 LUT = r5 toy 기준 LUT(축 TOY_*, w_ref_m 1e-6 -> 폭 키 100) + 잡음에 필요한 열(GM·SVG2_1HZ·SVG2_HF, CGD 는 인자).
#   잡음 r1 = 이분 점 f_hz 마다 SVG2_F<접미사>[f, L, VGS, VDS, VS]. meta 는 cap_npz_sha256 + base_frequencies_hz.
# ---------------------------------------------------------------------------

# [r7] VS 축 Hermite toy (계획 DEC-87 'VS 축 = GMBS 열이 생기면 기울기 −GMBS/ID 의 Hermite', CONTRACT 4.2 [r7]):
#   ln ID = r5 toy 의 VGS·VDS 부분 − s − s² (VS 의 2차식) -> d lnID/dVS = −(1 + 2s), GMBS = ID·(1 + 2s)(정확한 기울기 자료).
#   VS 격자 (0, 0.5) 한 칸이라 Hermite 가 2차식을 정확히 재현하고 선형은 칸 중앙에서 ln 으로 0.0625 어긋난다(판별력).

# [r7 2026-10-09] VS FC 위반 판(vs_fc=True): ln ID 의 VS 몫 = −(μ/λ)·(e^(λs) − 1), GMBS/ID = μ·e^(λs) (정확한 기울기 -- 1.4 단위 검사 일관),
#   μ = 0.1, λ = 10, VS 칸 [0, 0.5](h 0.5): 끝 기울기 −(0.1, 0.1·e^5 = 14.84), Δln ID = −0.01·(e^5 − 1) = −1.474, 현 −2.948 은 두 끝 사이.
#   FC(CONTRACT 1.4 식, 손계산): b0 = −0.05, b2 = −7.421, b1 = 3·(−1.474) + 0.05 + 7.421 = 3.049 > 0, b1² = 9.30 > b0·b2 = 0.371 -> 위반.
#   (옛 판은 GMBS 를 1000 배 해 FC 위반을 만들었다 -- 기울기가 ln ID 와 모순이라 1.4 로 로드 거부. 그 입력은 이제 거부 test 의 입력이다.)
VS_FC_MU = 0.1
VS_FC_LAMBDA = 10.0


def _vs_part(s, vs_fc):
    if vs_fc:
        return -(VS_FC_MU / VS_FC_LAMBDA) * (np.exp(VS_FC_LAMBDA * s) - 1.0)
    return -s - s * s


def vs_toy_lnid(v, d, s, L=1e-6, vs_fc=False):
    return (math.log(1e-6 / L) + math.log(1e-7) + R5_A * v - R5_B * v * v + R5_C * d
            + float(_vs_part(np.float64(s), vs_fc)))


def vs_toy_slice_arrays(W, scale=1.0, gmbs_mult=1.0, gmbs_mutate=None, vs_fc=False):
    """gmbs_mult ≠ 1·gmbs_mutate 는 기울기 열을 ln ID 와 모순되게 만드는 입력(1.4 단위 검사 거부 test·기울기 정의 안 됨 test 용)."""
    L, v, d, s = (np.asarray(TOY_L)[:, None, None, None], np.asarray(TOY_VGS)[None, :, None, None],
                  np.asarray(TOY_VDS)[None, None, :, None], np.asarray(TOY_VS)[None, None, None, :])
    ID = scale * np.exp(np.log(1e-6 / L) + math.log(1e-7) + R5_A * v - R5_B * v * v + R5_C * d + _vs_part(s, vs_fc))
    out = _toy_dict(W, ID, ID * (R5_A - 2 * R5_B * v), ID * R5_C)
    G = ID * (VS_FC_MU * np.exp(VS_FC_LAMBDA * s) if vs_fc else (1.0 + 2.0 * s)) * gmbs_mult
    out["GMBS"] = gmbs_mutate(G) if gmbs_mutate else G
    return out


def vs_toy_slices(**kw):
    return [("vs_w100.npz", "toyn", vs_toy_slice_arrays(1e-6, 1.0, **kw)),
            ("vs_w200.npz", "toyn", vs_toy_slice_arrays(2e-6, 2.0, **kw))]


NOISE_F_LO = 1.0
NOISE_F_HI = 1e4
NOISE_F_MID = (10.0, 100.0, 1000.0)
TOY_SHAPE = (len(TOY_L), len(TOY_VGS), len(TOY_VDS), len(TOY_VS))
TOY_NOISE_SPEC = LutSpec(1e-8, (("nmos", 1.5e-6),), (("toyn", "nmos"),), (("nmos", "_n"),), noise_ef=(("nmos", 1.0),))


def toy_grid_mesh():
    """(L, VGS, VDS, VS) broadcast 격자(모양 TOY_SHAPE)."""
    return np.meshgrid(np.asarray(TOY_L), np.asarray(TOY_VGS), np.asarray(TOY_VDS), np.asarray(TOY_VS), indexing="ij")


def noise_spectrum(A, B, f, ef=1.0, cgd=0.0, gm=1e-3):
    """측정 모형(합성 입력): S_vg(f) = A/f^EF + B/(1 + (2π f Cgd/gm)²) -- 피드스루가 열잡음 평탄값을 깎는 물리 모형
    (CONTRACT 9.2 괄호: '측정값이 B/(1 + (ωCgd/gm)²) 로 작아진다'). cgd = 0 이면 정확히 A/f^EF + B."""
    return A / f ** ef + B / (1.0 + (2.0 * math.pi * f * cgd / gm) ** 2)


class NoiseToy:
    """잡음 toy 를 폴더에 쓴다. A·B: TOY_SHAPE 배열(점마다 A0·B0), cgd·gm: 상수, f_mid: 이분 점."""

    def __init__(self, root, A, B, cgd=0.0, gm=1e-3, f_mid=NOISE_F_MID, f_hi=NOISE_F_HI, ef=1.0,
                 cap_mutate=None, noise_mutate=None, meta_mutate=None, write_noise=True):
        self.root = Path(root)
        cap = toy_cap_arrays()
        cap["CGD_n"] = np.full(TOY_SHAPE, float(cgd))
        cap["GM_n"] = np.full(TOY_SHAPE, float(gm))
        cap["SVG2_1HZ_n"] = noise_spectrum(A, B, NOISE_F_LO, ef, cgd, gm)
        cap["SVG2_HF_n"] = noise_spectrum(A, B, f_hi, ef, cgd, gm)
        if cap_mutate:
            cap_mutate(cap)
        self.build = ToyBuild(self.root, standard_toy_slices(), cap)
        self.cap_arrays = cap
        self.path = self.root / "noise_r1.npz"
        S = np.stack([noise_spectrum(A, B, f, ef, cgd, gm) for f in f_mid])
        meta = {"cap_npz_sha256": sha256_file(self.build.cap),
                "base_frequencies_hz": {"NOISE_F_PROBE": NOISE_F_LO, "F_TEST": f_hi}}
        if meta_mutate:
            meta_mutate(meta)
        arrays = {"L": np.asarray(TOY_L), "VGS": np.asarray(TOY_VGS), "VDS": np.asarray(TOY_VDS),
                  "VS": np.asarray(TOY_VS), "w_ref_m": np.float64(1e-6), "corner": np.str_("tt"),
                  "temp_c": np.float64(27.0), "f_hz": np.asarray(f_mid, dtype=float), "SVG2_F_n": S,
                  "meta_json": np.str_(json.dumps(meta))}
        if noise_mutate:
            noise_mutate(arrays)
        if write_noise:
            np.savez(self.path, **arrays)

    def load(self, spec=TOY_NOISE_SPEC, **kw):
        return load_lut_set(str(self.build.manifest), str(self.build.cap), spec, noise_npz=str(self.path), **kw)


MISMATCH_PARAMS = ("toxe", "voff", "vth0")
MISMATCH_SLOPE_REF = {"vth0": 3e-3, "toxe": 2e-3, "voff": 1e-3}


def mismatch_slope_ref_meta(values=None, model="toy_model.1"):
    vals = dict(MISMATCH_SLOPE_REF if values is None else values)
    rec = {"model": model}
    for p, v in vals.items():
        rec[p] = None if v is None else {"slope": "toy_%s_slope" % p, "value": v}
    return {"toyn": {"%g" % (L * 1e6): dict(rec) for L in TOY_L}}


class MismatchToy:
    """mismatch toy 를 폴더에 쓴다. dvgs = {변수: TOY_SHAPE 배열(V)}."""

    def __init__(self, root, dvgs, slope_ref=None, cap_mutate=None, mm_mutate=None, meta_mutate=None):
        self.root = Path(root)
        cap = toy_cap_arrays()
        if cap_mutate:
            cap_mutate(cap)
        self.build = ToyBuild(self.root, standard_toy_slices(), cap)
        self.path = self.root / "mismatch_r1.npz"
        meta = {"cap_npz_sha256": sha256_file(self.build.cap), "sigma_unit": 1e-6,
                "variables": {"toyn": sorted(dvgs)},
                "slope_ref": mismatch_slope_ref_meta(slope_ref)}
        if meta_mutate:
            meta_mutate(meta)
        arrays = {"L": np.asarray(TOY_L), "VGS": np.asarray(TOY_VGS), "VDS": np.asarray(TOY_VDS),
                  "VS": np.asarray(TOY_VS), "w_ref_m": np.float64(1e-6), "corner": np.str_("tt"),
                  "temp_c": np.float64(27.0), "meta_json": np.str_(json.dumps(meta))}
        for p, arr in dvgs.items():
            arrays["DVGS_%s_n" % p] = np.asarray(arr, dtype=float)
        if mm_mutate:
            mm_mutate(arrays)
        np.savez(self.path, **arrays)

    def load(self, spec=TOY_SPEC, **kw):
        return load_lut_set(str(self.build.manifest), str(self.build.cap), spec, mismatch_npz=str(self.path), **kw)


# --- [r7] 실데이터 잡음·mismatch (CONTRACT 1.8 설정 `files.noise`·`files.mismatch`, EF = PDK 선언 noise_ef_*) ----------

PDK_DECL_PATH = SKILL_DIR / "assets" / "sky130_pdk_decl.json"


@pytest.fixture(scope="session")
def real_pdk_decl():
    from gmid_engine.core import BoundedLRU, read_pdk_decl
    if not PDK_DECL_PATH.is_file():
        pytest.fail("PDK 선언 없음: %s" % PDK_DECL_PATH, pytrace=False)
    return read_pdk_decl(str(PDK_DECL_PATH), BoundedLRU(4))


@pytest.fixture(scope="session")
def real_nm_paths(real_location, real_paths):
    loc = real_location
    if not loc.noise_path or not loc.mismatch_path:
        pytest.fail("설정에 noise·mismatch 항목이 없다: %s" % LOCATION_CONFIG, pytrace=False)
    return dict(real_paths, noise=loc.noise_path, mismatch=loc.mismatch_path)


@pytest.fixture(scope="session")
def real_nm_spec(real_spec, real_pdk_decl):
    """LutSpec.noise_ef = PDK 선언 noise_ef_nmos·noise_ef_pmos(CONTRACT 9 '부르는 쪽이 PDK 선언에서 채운다')."""
    q = dict(real_pdk_decl.quantities)
    return LutSpec(real_spec.manufacturing_grid_m, real_spec.min_finger_w_m, real_spec.device_kinds,
                   real_spec.cap_column_suffix,
                   noise_ef=(("nmos", q["noise_ef_nmos"].value_m), ("pmos", q["noise_ef_pmos"].value_m)))


@pytest.fixture(scope="session")
def real_nm_lut(real_nm_paths, real_nm_spec):
    return load_real(real_nm_paths, real_nm_spec, noise_npz=real_nm_paths["noise"],
                     mismatch_npz=real_nm_paths["mismatch"])


@pytest.fixture
def real_nm_memo(real_nm_lut):
    from gmid_engine.lut import TableCache
    return LutMemo(real_nm_lut, point=4096, curve=512, root=512, table_cache=TableCache(None))


@pytest.fixture(scope="session")
def raw_noise(real_nm_paths):
    return _load_raw(real_nm_paths["noise"])


@pytest.fixture(scope="session")
def raw_mismatch(real_nm_paths):
    return _load_raw(real_nm_paths["mismatch"])
