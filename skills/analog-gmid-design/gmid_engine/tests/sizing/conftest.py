"""tests/sizing 공용 픽스처 -- `gmid_engine/sizing/CONTRACT.md`(+ core·lut·graph·authoring 계약)만 근거로 만든 입력과
독립 계산. sizing `.py` 소스는 열람하지 않았다.

- toy LUT: 이 파일이 정한 해석식으로 npz 를 직접 쓴다(nmos·pmos 한 폭 슬라이스씩). lut r5(4.2·7절)는 VGS·VDS 축이 저장 기울기
  (GM/ID·GDS/ID)를 쓰는 2점 cubic-Hermite 이고 Fritsch–Carlson 단조 조건을 검사하므로, 기울기가 자료와 정확히 맞는 식을 쓴다:
      ln ID[L, VGS, VDS, VS] = ln(W/L) + ln I0[kind] + B·VGS − C·VGS²/2 + LAM·VDS − A·VS²
      GM/ID = B − C·VGS (= d lnID/dVGS),  GDS/ID = LAM (= d lnID/dVDS),  VTH = 0.4
  VGS 방향은 2차, VDS 방향은 1차라 cubic-Hermite 가 정확히 재현한다(칸 안 값·미분 모두 닫힌 식). VS 축은 선형 보간이라 VS 항은
  격자 위 −A·VS² 의 구간 선형 -- 그래서 tol_V id_equivalent 는 VS 축 LOO(A·h²) / 2^2(Richardson, lut 5절) 만 남는다. VS 축은 음수 점
  (−0.45)을 포함해 봉인 6(bulk 역바이어스) 위반을 LUT 축 안에서 만들 수 있다.
- 손 회로: topology JSON 을 이 파일에서 dict 로 만들어 authoring `load_topology` 로 읽는다(입력 생성용 공개 API).
- 기대값: `Oracle` 이 npz 배열(numpy 로 직접 읽음)·닫힌 식으로 계산한다. 피검 함수로 기대값을 만들지 않는다.
"""
from __future__ import annotations

import bisect
import dataclasses
import hashlib
import json
import math
import random
from fractions import Fraction
from pathlib import Path

import numpy as np
import pytest

from gmid_engine.authoring import load_topology
from gmid_engine.graph import build_s1
from gmid_engine.lut import LutMemo, LutSpec, load_lut_set
from gmid_engine.search import open_run
from gmid_engine.sizing import KERNEL_KEY, PLAN_WRITERS, DcInputs, LutAccess, build_kernel_context
from toy_bins import write_toy_bins

HERE = Path(__file__).resolve().parent
SKILL_DIR = HERE.parents[2]
LIBRARY = SKILL_DIR / "assets" / "library"

# ---------------------------------------------------------------------------
# toy LUT 해석식 (이 test 가 정한 값)
# ---------------------------------------------------------------------------
W_M = 1e-6                      # 슬라이스 폭 -> w_key 100 (grid 1e-8)
W_KEY = 100
GRID_M = 1e-8
TOY_L = (1e-6, 2e-6)
TOY_VGS = tuple(round(0.1 * i, 10) for i in range(19))          # 0.0 .. 1.8
TOY_VDS = tuple(round(0.3 * i, 10) for i in range(7))           # 0.0 .. 1.8
TOY_VS = (-0.45, 0.0, 0.45, 0.9, 1.35, 1.8)
I0 = {"nmos": 1e-11, "pmos": 5e-12}
B = 20.0                        # gm/ID(VGS = 0)
C = 8.0                         # gm/ID 기울기: gm/ID = B − C·VGS (1.8 V 에서 5.6 > 0)
LAM = 0.1
A = 2.0
DEVICE_OF = {"nmos": "toyn", "pmos": "toyp"}
SUFFIX = {"nmos": "_n", "pmos": "_p"}
TOY_SPEC = LutSpec(GRID_M, (("nmos", 1e-6), ("pmos", 1e-6)), (("toyn", "nmos"), ("toyp", "pmos")),
                   (("nmos", "_n"), ("pmos", "_p")))
EPS = np.finfo(float).eps


def toy_arrays(kind):
    Lg = np.asarray(TOY_L)[:, None, None, None]
    G = np.asarray(TOY_VGS)[None, :, None, None]
    D = np.asarray(TOY_VDS)[None, None, :, None]
    S = np.asarray(TOY_VS)[None, None, None, :]
    ID = (W_M / Lg) * I0[kind] * np.exp(B * G - 0.5 * C * G * G + LAM * D - A * S * S)
    GM = ID * (B - C * G)
    return {
        "W": np.float64(W_M),
        "L": np.asarray(TOY_L), "VGS": np.asarray(TOY_VGS), "VDS": np.asarray(TOY_VDS), "VS": np.asarray(TOY_VS),
        "ID": ID, "GM": GM, "GDS": ID * LAM, "VTH": np.full(ID.shape, 0.4),
        "meta_json": np.str_('{"model_files_sha256": {}}'),
        "corner": np.str_("tt"), "temp_c": np.float64(27.0),
    }


def _sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def _stamp(a, tb, kind):
    """[WB-1 §4] 합성 모델 기록(meta)을 배열 dict 에 적는다."""
    a["meta_json"] = np.str_(json.dumps(tb.meta(kind, root=False)))     # pdk_root 는 적재 인자(폴더 무관 내용)
    return a


def bin_rule_of(manifest):
    """합성 LUT 폴더의 bin 선언 경로(`write_toy_bins` 가 manifest 와 같은 폴더에 쓴다)."""
    return str(Path(manifest).parent / "bin_rule.json")


def pdk_of(manifest):
    """합성 LUT 폴더의 모델 루트(`write_toy_bins` 가 manifest 와 같은 폴더 아래 pdk 에 쓴다)."""
    return str(Path(manifest).parent / "pdk")


def write_toy_lut(root: Path, w_ref_m=W_M, extra_width=None):
    root.mkdir(parents=True, exist_ok=True)
    tb = write_toy_bins(root, ("nmos", "pmos"), TOY_L, (W_M,) if extra_width is None else (W_M, extra_width),
                        grid_m=GRID_M)
    entries = []
    for kind in ("nmos", "pmos"):
        p = root / ("toy_%s.npz" % kind)
        np.savez(p, **_stamp(toy_arrays(kind), tb, kind))
        entries.append({"device": DEVICE_OF[kind], "file": p.name, "sha256": _sha(p)})
        if extra_width is not None:                      # 같은 식, 폭만 다른 슬라이스(ID·GM·GDS × 폭 비)
            a = _stamp(toy_arrays(kind), tb, kind)
            k = extra_width / W_M
            a.update(W=np.float64(extra_width), ID=a["ID"] * k, GM=a["GM"] * k, GDS=a["GDS"] * k)
            p2 = root / ("toy_%s_w2.npz" % kind)
            np.savez(p2, **a)
            entries.append({"device": DEVICE_OF[kind], "file": p2.name, "sha256": _sha(p2)})
    (root / "manifest.json").write_text(json.dumps({"generator_sha256": "0" * 64, "slices": entries}),
                                        encoding="utf-8")
    shp = (len(TOY_L), len(TOY_VGS), len(TOY_VDS), len(TOY_VS))
    cap = {"L": np.asarray(TOY_L), "VGS": np.asarray(TOY_VGS), "VDS": np.asarray(TOY_VDS), "VS": np.asarray(TOY_VS),
           "w_ref_m": np.float64(w_ref_m), "corner": np.str_("tt"), "temp_c": np.float64(27.0),
           "meta_json": np.str_(json.dumps(tb.cap_meta(root=False)))}
    for kind in ("nmos", "pmos"):
        cap["CGG" + SUFFIX[kind]] = np.full(shp, 1e-15)
        cap["CGD" + SUFFIX[kind]] = np.full(shp, 2e-16)
    np.savez(root / "cap.npz", **cap)
    return root / "manifest.json", root / "cap.npz"


# ---------------------------------------------------------------------------
# [r4] VDSAT 열·꺼진 VDS 열이 있는 toy LUT (sizing CONTRACT r4 6절 봉인 7, 5.4 VDS 정의역 하한)
# ---------------------------------------------------------------------------
# 격자는 2진 분수(0.125·0.25 V 간격)라 VDSAT 선형 보간·LOO 차·Richardson 1/4 가 모두 부동소수 정확 -> 봉인 7 경계(±1 ulp)를
# 손으로 정확히 만들 수 있다. ID 식은 위 toy 와 같다(VGS 2차·VDS 1차 -> Hermite 정확).
R4_L = (1e-6, 2e-6)
R4_VGS = tuple(0.125 * i for i in range(17))          # 0 .. 2.0
R4_VDS = tuple(0.25 * i for i in range(9))            # 0 .. 2.0
R4_VS = tuple(-0.5 + 0.25 * i for i in range(11))     # -0.5 .. 2.0
# VDSAT[kind] = c0 + c1·VGS + c2·VGS² + cs·VS + cl·(L index)  (VDS 무관). VGS 축 LOO 차 = c2·h² (h = 0.125) 정확,
# 다른 축은 1차라 LOO 0, L 축은 bin 지도가 없어 LOO 없음 -> lut 5.2 셀 vdsat_v = c2·h²/2² (모든 셀 같음).
R4_VDSAT = {"nmos": (0.0625, 0.25, 0.25, 0.125, 0.0625), "pmos": (0.125, 0.25, 0.5, 0.0625, 0.125)}


def r4_vdsat_grid(kind, iL, vgs, vs):
    """VDSAT 열 값(격자점 vgs·vs 에서 정확)."""
    c0, c1, c2, cs, cl = R4_VDSAT[kind]
    return c0 + c1 * vgs + c2 * vgs * vgs + cs * vs + cl * iL


def r4_tol_vdsat(kind):
    """lut 5.2: 선형 LOO 차 c2·h²(VGS 축 내부점 모두 같음) / 2^2. h = VGS 간격."""
    h = R4_VGS[1] - R4_VGS[0]
    return R4_VDSAT[kind][2] * h * h / 4.0


R4_GRIDS = (R4_L, R4_VGS, R4_VDS, R4_VS)


def r4_arrays(kind, vdsat=True, off_cols=0, off_points=(), grids=R4_GRIDS):
    """off_cols: VDS index 0..off_cols-1 열 전부 꺼짐(ID = GM = GDS = 0 -- LUT v2 의 VDS = 0 열 모양).
    off_points: (iL, iG, k, s) 점의 GM = 0(ID > 0 유지 -> on_mask 거짓). grids = (L, VGS, VDS, VS)."""
    gL, gG, gD, gS = (np.asarray(g, dtype=float) for g in grids)
    Lg = gL[:, None, None, None]
    G = gG[None, :, None, None]
    D = gD[None, None, :, None]
    S = gS[None, None, None, :]
    ID = (W_M / Lg) * I0[kind] * np.exp(B * G - 0.5 * C * G * G + LAM * D - A * S * S)
    GM = ID * (B - C * G)
    GDS = ID * LAM
    if off_cols:
        ID[:, :, :off_cols, :] = 0.0
        GM[:, :, :off_cols, :] = 0.0
        GDS[:, :, :off_cols, :] = 0.0
    for p in off_points:
        GM[p] = 0.0
    out = {"W": np.float64(W_M), "L": gL, "VGS": gG, "VDS": gD,
           "VS": gS, "ID": ID, "GM": GM, "GDS": GDS, "VTH": np.full(ID.shape, 0.4),
           "meta_json": np.str_('{"model_files_sha256": {}}'), "corner": np.str_("tt"), "temp_c": np.float64(27.0)}
    if vdsat:
        c0, c1, c2, cs, cl = R4_VDSAT[kind]
        iL = np.arange(len(gL), dtype=float)[:, None, None, None]
        out["VDSAT"] = (c0 + c1 * G + c2 * G * G + cs * S + cl * iL) + np.zeros(ID.shape)
    return out


def r4_vds_floor(arrays):
    """[r4] 5.4 VDS 정의역 하한의 독립 계산: on_mask = (ID > 0) & (GM > 0) 가 그 VDS 열부터 마지막 열까지 모든
    (L, VGS, VS) 점에서 참인 첫 VDS 격자점, 없으면 VDS 격자 최소."""
    on = (arrays["ID"] > 0) & (arrays["GM"] > 0)
    vds = arrays["VDS"]
    for k in range(len(vds)):
        if on[:, :, k:, :].all():
            return float(vds[k])
    return float(vds[0])


def write_r4_lut(root: Path, vdsat=("nmos", "pmos"), off_cols=None, off_points=None, grids=R4_GRIDS, cap_vdsat=(), cdd=False):
    """vdsat = VDSAT 슬라이스 열을 가진 kind. off_cols / off_points = {kind: ...}(r4_arrays 인자).
    cap_vdsat = 기준 LUT(cap.npz)에 `VDSAT<접미사>` 열(r4 VDSAT 식)을 더할 kind(기본 () = 더하지 않음 -- 기존 호출 동작 그대로). -> LutSet."""
    root.mkdir(parents=True, exist_ok=True)
    off_cols = dict(off_cols or {})
    off_points = dict(off_points or {})
    tb = write_toy_bins(root, ("nmos", "pmos"), tuple(grids[0]), (W_M,), grid_m=GRID_M)
    entries = []
    for kind in ("nmos", "pmos"):
        p = root / ("r4_%s.npz" % kind)
        np.savez(p, **_stamp(r4_arrays(kind, kind in vdsat, off_cols.get(kind, 0), off_points.get(kind, ()), grids),
                             tb, kind))
        entries.append({"device": DEVICE_OF[kind], "file": p.name, "sha256": _sha(p)})
    (root / "manifest.json").write_text(json.dumps({"generator_sha256": "0" * 64, "slices": entries}),
                                        encoding="utf-8")
    gL, gG, gD, gS = (np.asarray(g, dtype=float) for g in grids)
    shp = (len(gL), len(gG), len(gD), len(gS))
    cap = {"L": gL, "VGS": gG, "VDS": gD, "VS": gS,
           "w_ref_m": np.float64(W_M), "corner": np.str_("tt"), "temp_c": np.float64(27.0),
           "meta_json": np.str_(json.dumps(tb.cap_meta(root=False)))}
    for kind in ("nmos", "pmos"):
        cap["CGG" + SUFFIX[kind]] = np.full(shp, 1e-15)
        cap["CGD" + SUFFIX[kind]] = np.full(shp, 2e-16)
        if cdd:      # [WB-1 E-18] drain 용량은 CDD 열의 양(cgd 대체 없음) -- 구조·매크로 경로를 통과하는 test 용 합성 열(기본 False = 기존 호출 불변)
            cap["CDD" + SUFFIX[kind]] = np.full(shp, 2e-16)
    for kind in cap_vdsat:
        cap["VDSAT" + SUFFIX[kind]] = r4_arrays(kind, True, 0, (), grids)["VDSAT"]
    np.savez(root / "cap.npz", **cap)
    return load_lut_set(str(root / "manifest.json"), str(root / "cap.npz"), TOY_SPEC, bin_rule=tb.bin_rule,
                         pdk_root=tb.pdk_root)


def r4_vs_term(vsb):
    return _lin(R4_VS, [-A * v * v for v in R4_VS], vsb)


def r4_ln_idu(kind, vgs, vds, vsb):
    """r4 toy 의 ln IDu(L 무관). VS 항 = R4_VS 격자 위 −A·VS² 의 구간 선형. vds 는 켜진 VDS 칸 안이어야 한다."""
    return math.log(I0[kind]) + Oracle.f(vgs) + LAM * vds + r4_vs_term(vsb)


def r4_vgs_of(kind, ln_idu, vds, vsb):
    r = ln_idu - math.log(I0[kind]) - LAM * vds - r4_vs_term(vsb)
    return (B - math.sqrt(B * B - 2.0 * C * r)) / C


def r4_vdsat_at(kind, L, vgs, vsb):
    """lut 4.3 vdsat 의 독립 계산: npz 열을 모든 축 선형(VDS 무관 열이라 VDS 가중 생략, L 은 앵커만)."""
    arr = r4_arrays(kind)["VDSAT"]
    iL = R4_L.index(L)
    col = arr[iL, :, 0, :]
    i = min(max(bisect.bisect_right(R4_VGS, vgs) - 1, 0), len(R4_VGS) - 2)
    t = (vgs - R4_VGS[i]) / (R4_VGS[i + 1] - R4_VGS[i])
    j = min(max(bisect.bisect_right(R4_VS, vsb) - 1, 0), len(R4_VS) - 2)
    u = (vsb - R4_VS[j]) / (R4_VS[j + 1] - R4_VS[j])
    v = 0.0
    for a, wa in ((i, 1 - t), (i + 1, t)):
        for b, wb in ((j, 1 - u), (j + 1, u)):
            if wa * wb != 0.0:
                v += wa * wb * float(col[a, b])
    return v


@pytest.fixture(scope="session")
def r4_lut_root(tmp_path_factory):
    """r4 toy LUT 파일을 쓴 폴더 -> (LutSet, 폴더). 폴더의 `r4_<kind>.npz` 는 기대값을 LUT 파일에서 직접 읽는 test 가 연다."""
    root = tmp_path_factory.mktemp("r4_lut")
    return write_r4_lut(root), root


@pytest.fixture(scope="session")
def r4_lut(r4_lut_root):
    """VDSAT 열(nmos·pmos), 모든 점 켜짐."""
    return r4_lut_root[0]


def r4_npz(root, kind):
    """`write_r4_lut(root)` 가 쓴 kind 슬라이스 파일 경로."""
    return Path(root) / ("r4_%s.npz" % kind)


def toy_npz(manifest_path, kind):
    """`write_toy_lut` 가 쓴 kind 기본 슬라이스 파일 경로(manifest 와 같은 폴더)."""
    return Path(manifest_path).parent / ("toy_%s.npz" % kind)


def lut_file_gm_id(npz_path, L, vgs, vds, vsb):
    """[U17 ①, 설계 40 §3.7-3] 동작점 (L, VGS, VDS, VSB) 의 LUT gm/ID 를 **LUT 파일에서 직접** 읽는다(피검 lut·sizing 함수 없음).

    npz 의 GM·ID 배열로 GM/ID 격자를 만들고 네 축(L, VGS, VDS, VS) 다선형 보간한다. 이 test 들이 쓰는 toy·r4 파일은 GM/ID 열이
    VGS 에 대해 1차이고 다른 축에 대해 상수다(파일에서 그 성질을 확인한 뒤 보간한다) -- 그러면 다선형 보간이 정확한 값이고, LUT 의
    다른 보간법(ln ID 의 Hermite 기울기 등)과도 같은 값이 된다. 축 밖 점은 test 입력 결함이라 AssertionError."""
    with np.load(npz_path) as z:
        axes = [np.asarray(z[k], dtype=float) for k in ("L", "VGS", "VDS", "VS")]
        g = np.asarray(z["GM"], dtype=float) / np.asarray(z["ID"], dtype=float)
    # 파일 성질 확인: VGS 2차 차분 0(1차), L·VDS·VS 방향 상수
    assert np.allclose(np.diff(g, 2, axis=1), 0.0, atol=1e-9), "LUT GM/ID 열이 VGS 에 1차가 아니다 -- 이 helper 의 전제가 깨짐"
    for ax in (0, 2, 3):
        assert np.allclose(np.diff(g, 1, axis=ax), 0.0, atol=1e-9), "LUT GM/ID 열이 축 %d 방향 상수가 아니다" % ax
    brackets = []
    for xs, x in zip(axes, (L, vgs, vds, vsb)):
        assert xs[0] <= x <= xs[-1], "축 밖 동작점 %r (축 %r..%r)" % (x, xs[0], xs[-1])
        i = min(max(bisect.bisect_right(list(xs), x) - 1, 0), len(xs) - 2)
        t = (x - xs[i]) / (xs[i + 1] - xs[i])
        brackets.append(((i, 1.0 - t), (i + 1, t)))
    total = 0.0
    for a, wa in brackets[0]:
        for b, wb in brackets[1]:
            for c, wc in brackets[2]:
                for d, wd in brackets[3]:
                    w = wa * wb * wc * wd
                    if w != 0.0:
                        total += w * float(g[a, b, c, d])
    return total


def hand_dc_gm(npz_of_kind, op):
    """설계 40 §3.7-3 `dc_gm` 의 독립 계산: 그 소자 ID(`dc_op.current`) × 그 동작점(L, VGS, VDS, VSB)의 LUT 파일 gm/ID.
    `npz_of_kind(kind)` -> npz 경로. dc_op 에서 읽는 것은 동작점 좌표와 전류(피검 블록의 입력)뿐이고 gm_id 칸은 읽지 않는다."""
    return op.current * lut_file_gm_id(npz_of_kind(op.kind), op.L, op.vgs, op.vds, op.vsb)


@pytest.fixture(scope="session")
def r4_access(r4_lut):
    return new_access(r4_lut)


# ---------------------------------------------------------------------------
# [r4] 실데이터 LUT v2 (lut CONTRACT 1.8 '쓰는 법') -- 없으면 skip 이 아니라 FAIL
# ---------------------------------------------------------------------------
REALDATA_MARKER = "sizing_realdata"
LOCATION_CONFIG = SKILL_DIR / "assets" / "lut_v2_location.json"
_DEFAULT_TLEF = r"C:/pdk/sky130_fd_sc_hd/tech/sky130_fd_sc_hd.tlef"
REAL_DEVICE_KINDS = (("nfet_01v8", "nmos"), ("pfet_01v8", "pmos"))
REAL_CAP_SUFFIX = (("nmos", "_n"), ("pmos", "_p"))


def pytest_configure(config):
    config.addinivalue_line("markers", REALDATA_MARKER + ": 실 LUT v2(설정 파일·tlef) sizing test -- 데이터가 없으면 FAIL")


@pytest.fixture(scope="session")
def real_lut_v2():
    """-> (LutSet, {(kind, w_key): 슬라이스 npz 경로}). grid = tlef MANUFACTURINGGRID, min_finger = kind 별 슬라이스 최소 W."""
    import os
    import re
    from gmid_engine.core import SchemaRejectedError
    from gmid_engine.lut import resolve_lut_location
    try:
        loc = resolve_lut_location(str(LOCATION_CONFIG), os.environ)
    except SchemaRejectedError as e:
        pytest.fail("LUT v2 데이터 위치를 풀지 못함(실데이터 test 는 skip 하지 않는다): %r" % (e.record.detail,),
                    pytrace=False)
    tlef = os.environ.get("GMID_PDK_TLEF") or _DEFAULT_TLEF
    if not Path(tlef).is_file():
        pytest.fail("PDK tlef 없음: %s" % tlef, pytrace=False)
    m = re.search(r"^\s*MANUFACTURINGGRID\s+([0-9.eE+-]+)\s*;", Path(tlef).read_text(encoding="utf-8", errors="replace"),
                  re.M)
    grid = float(m.group(1)) * 1e-6
    man = json.loads(Path(loc.manifest_path).read_text(encoding="utf-8"))
    dk = dict(REAL_DEVICE_KINDS)
    from pdk_min_w import min_finger_w_m
    mins = min_finger_w_m(kind for _, kind in REAL_DEVICE_KINDS)      # PDK 선언 양(card 20261104-wb1)
    files = {}
    for s in man["slices"]:
        p = Path(loc.manifest_path).parent / s["file"]
        with np.load(p) as z:
            W = float(z["W"])
        kind = dk[s["device"]]
        files[(kind, int(round(W / grid)))] = p
    spec = LutSpec(grid, tuple(sorted(mins.items())), REAL_DEVICE_KINDS, REAL_CAP_SUFFIX)
    lut = load_lut_set(loc.manifest_path, loc.cap_npz_path, spec, pdk_root=loc.pdk_root,
                       verify_midpoints=loc.midpoints_paths, bin_rule=loc.bin_rule_path)
    return lut, files


@pytest.fixture(scope="session")
def toy_lut_paths(tmp_path_factory):
    return write_toy_lut(tmp_path_factory.mktemp("sizing_toy_lut"))


@pytest.fixture(scope="session")
def toy_lut(toy_lut_paths):
    m, c = toy_lut_paths
    return load_lut_set(str(m), str(c), TOY_SPEC, bin_rule=bin_rule_of(m), pdk_root=pdk_of(m))


def new_access(lut, n=4096):
    return LutAccess(LutMemo(lut, point=n, curve=n, root=n))


@pytest.fixture(scope="session")
def toy_access(toy_lut):
    """세션 공용 LutAccess(memo 하나 -- tol_V 표가 프로세스당 1회 계산되게)."""
    return new_access(toy_lut)


# ---------------------------------------------------------------------------
# 독립 oracle (npz 배열 직접 + 닫힌 식)
# ---------------------------------------------------------------------------

def _lin(xs, ys, x):
    xs = list(xs)
    if x == xs[-1]:
        return float(ys[-1])
    i = min(max(bisect.bisect_right(xs, x) - 1, 0), len(xs) - 2)
    t = (x - xs[i]) / (xs[i + 1] - xs[i])
    return float(ys[i] + (ys[i + 1] - ys[i]) * t)


def _hermite(y0, y1, m0, m1, h, t):
    """2점 cubic-Hermite(lut 4.2 식 그대로, 독립 구현)."""
    h00 = 2 * t ** 3 - 3 * t ** 2 + 1
    h10 = t ** 3 - 2 * t ** 2 + t
    h01 = -2 * t ** 3 + 3 * t ** 2
    h11 = t ** 3 - t ** 2
    return y0 * h00 + h * m0 * h10 + y1 * h01 + h * m1 * h11


class Oracle:
    """toy LUT 의 독립 계산(r5). VGS·VDS 는 Hermite 가 정확히 재현하는 2차·1차 식이라 닫힌 식, VS 항은 VS 격자 위
    −A·VS² 의 구간 선형 보간."""

    @staticmethod
    def vs_term(vsb):
        return _lin(TOY_VS, [-A * v * v for v in TOY_VS], vsb)

    @staticmethod
    def f(vgs):
        return B * vgs - 0.5 * C * vgs * vgs

    @staticmethod
    def ln_idu(kind, vgs, vds, vsb):
        # IDu = ID·L/w_m = I0·exp(...)  (L 무관)
        return math.log(I0[kind]) + Oracle.f(vgs) + LAM * vds + Oracle.vs_term(vsb)

    @staticmethod
    def vgs_of(kind, ln_idu, vds, vsb):
        """좌표 역산: f(vgs) = ln IDu − ln I0 − LAM·vds − vs_term, f 증가 가지(vgs < B/C)의 근."""
        r = ln_idu - math.log(I0[kind]) - LAM * vds - Oracle.vs_term(vsb)
        return (B - math.sqrt(B * B - 2.0 * C * r)) / C

    @staticmethod
    def gm_id(vgs):
        return B - C * vgs

    @staticmethod
    def tol_v():
        """tol_v_table(...).at(L, vds, "id_equivalent") -- lut 계약 5절 r5 정의(운영과 같은 방법 LOO: VGS 축 Hermite(기울기
        GM/ID)·VDS 축 Hermite(기울기 GDS/ID)·VS 축 선형, Richardson 2^p 환산 p = 4/4/2, L 축은 모델 bin 지도 없음 -> 없음)를
        npz 배열에 직접 적용한 셀 최댓값."""
        arr = toy_arrays("nmos")
        lnI = np.log(arr["ID"])
        g = arr["GM"] / arr["ID"]
        sd = arr["GDS"] / arr["ID"]
        best = 0.0
        grids = (arr["L"], arr["VGS"], arr["VDS"], arr["VS"])
        for ax, slope, p in ((1, g, 4), (2, sd, 4), (3, None, 2)):
            x = grids[ax]
            for j in range(1, len(x) - 1):
                H = x[j + 1] - x[j - 1]
                t = (x[j] - x[j - 1]) / H
                sm, sj, sp = [slice(None)] * 4, [slice(None)] * 4, [slice(None)] * 4
                sm[ax], sj[ax], sp[ax] = j - 1, j, j + 1
                y0, y1 = lnI[tuple(sm)], lnI[tuple(sp)]
                if slope is None:
                    loo = y0 + t * (y1 - y0)
                else:
                    loo = _hermite(y0, y1, slope[tuple(sm)], slope[tuple(sp)], H, t)
                val = np.abs(loo - lnI[tuple(sj)]) / g[tuple(sj)] / 2 ** p
                best = max(best, float(val.max()))
        return best


def rel_close(a, b, rtol=1e-9, atol=0.0):
    return abs(a - b) <= max(atol, rtol * max(abs(a), abs(b)))


# ---------------------------------------------------------------------------
# 손 회로 topology
# ---------------------------------------------------------------------------

def mos(name, kind, d, g, s, bulk=None):
    e = {"name": name, "kind": kind, "drain": d, "gate": g, "source": s}
    if bulk is not None:
        e["bulk"] = bulk
    return e


def two(name, kind, a, b):
    return {"name": name, "kind": kind, "terminals": [a, b]}


def topo(name, netlist, ports, passives=(), sources=(), rails=("vdd", "gnd"), bias=()):
    """bias = authoring CONTRACT 9절 `bias_inputs`(gate 전용 외부 바이어스 넷) -- 회로마다 손으로 정한 리터럴(입력 선언, 기대값 아님).
    비면 키를 쓰지 않는다(키 없음 = 빈 선언)."""
    d = {"schema_version": "2.0", "topology_name": name, "netlist": list(netlist), "supply_nets": list(rails),
         "ports": {k: {"direction": v[0], "role": v[1]} for k, v in ports.items()},
         "passive_elements": list(passives)}
    if sources:
        d["ideal_sources"] = list(sources)
    if bias:
        d["bias_inputs"] = list(bias)
    return d


def load_doc(tmp_path: Path, doc: dict):
    p = Path(tmp_path) / (doc["topology_name"] + ".topology.json")
    p.write_text(json.dumps(doc, indent=2), encoding="utf-8")
    return load_topology(str(p))


SUPPLIES = {"vdd": 1.8, "gnd": 0.0}


def circuit_cs_pmos_load():
    """C: M1 nmos (out, in, gnd) + M2 pmos (out, pb, vdd). out 은 drain 만 -> G_vgs 밖 W4. 순환 SCC 없음."""
    return topo("hand_cs_pload",
                [mos("M1", "nmos", "out", "in", "gnd"), mos("M2", "pmos", "out", "pb", "vdd")],
                {"in": ("input", "single_ended_input"), "out": ("output", "single_ended_output")},
                bias=["pb"])                                  # pb: M2 gate 에만


def circuit_cs_res(bulk_m1=None):
    """A: M1 nmos (out, in, gnd) + R1 (vdd, out). out = resistor_drop(known vdd = t0)."""
    return topo("hand_cs_res",
                [mos("M1", "nmos", "out", "in", "gnd", bulk_m1)],
                {"in": ("input", "single_ended_input"), "out": ("output", "single_ended_output")},
                passives=[two("R1", "resistor", "vdd", "out")])


def circuit_empty_window():
    """D: x 는 drain 만(G_vgs 밖 W4). MA nmos (x, vdd, vdd): lo >= V(vdd); MB pmos (x, gnd, gnd): hi <= V(gnd)."""
    return topo("hand_empty_window",
                [mos("MA", "nmos", "x", "vdd", "vdd"), mos("MB", "pmos", "x", "gnd", "gnd"),
                 mos("MC", "nmos", "x", "inp", "gnd")],
                {"inp": ("input", "single_ended_input"), "x": ("output", "single_ended_output")})


def build_ctx(tmp_path, doc, access, supplies=None, **inputs_kw):
    """(S1, DcInputs, KernelContext). [XRUN-F1 card B C0·C6] 실행 하나 = 이 호출 하나 -- 스스로 open_run() 한 쌍을 S1·커널 컨텍스트에 쓴다."""
    donors, counters = open_run()
    td = load_doc(tmp_path, doc)
    sup = dict(SUPPLIES if supplies is None else supplies)
    s1 = build_s1(td, sup, donors=donors, counters=counters)
    inputs = DcInputs(tuple(sorted(sup.items())), **inputs_kw)
    return s1, inputs, build_kernel_context(s1, inputs, access, donors=donors, counters=counters)


def detail(exc):
    return dict(exc.record.detail)


def run_of(ctx):
    """[XRUN-F1 card B C4·C6] ctx 의 실행 두 객체를 블록 호출 키워드로(`block(snap, ..., **run_of(ctx))`) -- 단위 test 는 그 실행 하나 안에서 부른다."""
    return dict(donors=ctx.donors, counters=ctx.counters)


COUNT_FIELDS = ("calls", "reuses", "grafts", "replays", "computes", "recomputes_same_input")


def block_row(counters, name):
    """[card B C1] 실행 계수 (name, "*") 행의 여섯 칸 tuple(COUNT_FIELDS 순서), 기록이 없으면 0 여섯."""
    for r in counters.snapshot().blocks:
        if (r.block, r.part) == (name, "*"):
            return tuple(getattr(r, f) for f in COUNT_FIELDS)
    return (0,) * len(COUNT_FIELDS)


def row_delta(after, before):
    return tuple(a - b for a, b in zip(after, before))


# [XRUN-F1 card B 규칙 M M-d] KernelContext 는 실행의 두 객체를 칸으로 쥔다(C6) -- test 하나보다 긴 범위 fixture 에 두지 않는다(function 범위).
@pytest.fixture
def ctx_c(tmp_path_factory, toy_access):
    """회로 C 의 (S1, DcInputs, KernelContext)."""
    return build_ctx(tmp_path_factory.mktemp("ctx_c"), circuit_cs_pmos_load(), toy_access)


@pytest.fixture
def ev_c(ctx_c):
    from gmid_engine.sizing import size_and_seal
    return size_and_seal(ctx_c[2], theta_c())


@pytest.fixture
def ctx_r4c(tmp_path_factory, r4_access):
    """회로 C 를 VDSAT 열이 있는 r4 toy LUT 로 만든 KernelContext."""
    return build_ctx(tmp_path_factory.mktemp("ctx_r4c"), circuit_cs_pmos_load(), r4_access)[2]


def theta_r4c(y=0.5, v1=0.6, v2=0.7, l1=1e-6, l2=2e-6, i2=1e-5):
    """r4 toy 회로 C 의 θ: M1 vgs = v1, M2 vgs = v2 가 나오는 좌표(VDS = y·1.8 / 1.8 − y·1.8, VSB 0)."""
    vout = y * 1.8
    return {("L", "M1"): l1, ("L", "M2"): l2, ("ln_idu", "M1"): r4_ln_idu("nmos", v1, vout, 0.0),
            ("ln_idu", "M2"): r4_ln_idu("pmos", v2, 1.8 - vout, 0.0), ("current", "M2"): i2, ("y", "out"): y}


@pytest.fixture
def ctx_a(tmp_path_factory, toy_access):
    """회로 A(저항 부하) -- R1 값은 θ resistance."""
    return build_ctx(tmp_path_factory.mktemp("ctx_a"), circuit_cs_res(), toy_access)


def theta_a(i=1e-5, r=9e4, vgs=0.6, l1=1e-6):
    """회로 A: V(out) = 1.8 − I·R, x1 = vgs 가 나오는 좌표(VDS = V(out), VSB 0)."""
    vout = 1.8 - i * r
    return {("L", "M1"): l1, ("ln_idu", "M1"): Oracle.ln_idu("nmos", vgs, vout, 0.0),
            ("current", "R1"): i, ("resistance", "R1"): r}


NINE = ("common_gate_amplifier", "current_reuse_telescopic_ota", "folded_cascode", "ngcc_3stage_ff",
        "nmcnr_amplifier", "pushpull_follower_buffer", "sf_pushpull_output_opamp", "two_stage_ota",
        "two_stage_ota_sf")


# SPEC_CONTRACT 5절 픽스처 이름표 중 MOD5 레지스트리(metrics.metric_catalog)에 아직 없는 이름(7절 S2 + area 축 예산 metric).
# 나머지는 실제 레지스트리를 그대로 쓴다(이름표를 두 곳에 정의하지 않는다).
def _registry_gaps():
    from gmid_engine.core import MetricSignature as M
    # [U5 2026-10-08] 옛 mismatch_sigma_mv·mirror_ratio_error_mv 는 옛 이름 표로 거부되는 이름이라(설계 40 §3.8-8) 보충에서 뺐다 --
    # 새 이름 11개는 metric_catalog() 의 계산 대기 서명에 있다.
    return {"area_layout_m2": M("m2", "geom", None, "area")}


def spec_catalog():
    from gmid_engine.metrics import metric_catalog
    cat = dict(metric_catalog())
    for k, v in _registry_gaps().items():
        assert k not in cat, "레지스트리에 생긴 이름은 test 쪽 보충에서 지운다: %s" % k
        cat[k] = v
    return cat


_LIB = {}


def library_ctx(name, access):
    """library 회로: (topology raw dict, TopologyDoc, SizingSpecDoc, DcInputs, S1Graph, KernelContext).
    입력·S1 은 프로세스당 1회(_LIB). [XRUN-F1 card B 규칙 M M-d] KernelContext 는 실행의 두 객체를 칸으로 쥐므로(C6) 모듈 캐시에 두지 않고
    부를 때마다 새 open_run() 쌍으로 만든다(실행 하나 = 이 호출 하나). S1 은 지역 쌍으로 만든 스냅샷이라 두 객체를 담지 않는다."""
    if name not in _LIB:
        from gmid_engine.authoring import load_sizing_spec
        from gmid_engine.sizing import dc_inputs_from_spec
        raw = json.loads((LIBRARY / (name + ".topology.json")).read_text(encoding="utf-8"))
        td = load_topology(str(LIBRARY / (name + ".topology.json")))
        spec = load_sizing_spec(str(LIBRARY / (name + ".sizing_spec.json")), td, spec_catalog())
        inputs = dc_inputs_from_spec(spec)
        s1_donors, s1_counters = open_run()
        s1 = build_s1(td, dict(inputs.supplies_v), donors=s1_donors, counters=s1_counters)
        _LIB[name] = (raw, td, spec, inputs, s1)
    raw, td, spec, inputs, s1 = _LIB[name]
    donors, counters = open_run()
    return raw, td, spec, inputs, s1, build_kernel_context(s1, inputs, access, donors=donors, counters=counters)


def free_currents(ctx, targets):
    """손으로 정한 원소 전류 전체(KCL 을 만족하는 값)에서 θ current 성분(기저 free 원소)만 고른다."""
    from gmid_engine.sizing import DC_KEY
    basis = ctx.base.value("graph", DC_KEY, "dc_current_basis")
    return {("current", k): targets[k] for k in basis.free}


def theta_c(x1=None, x2=None, y=0.5, i2=1e-5, l1=1e-6, l2=2e-6):
    """회로 C 의 θ(dict). 기본 x1·x2 = vgs 0.6·0.7 이 나오도록 oracle 로 정한 좌표(VDS = y·1.8, VSB 0)."""
    vout = y * 1.8
    if x1 is None:
        x1 = Oracle.ln_idu("nmos", 0.6, vout, 0.0)
    if x2 is None:
        x2 = Oracle.ln_idu("pmos", 0.7, 1.8 - vout, 0.0)
    return {("L", "M1"): l1, ("L", "M2"): l2, ("ln_idu", "M1"): x1, ("ln_idu", "M2"): x2,
            ("current", "M2"): i2, ("y", "out"): y}


def column_dict(snapshot, kind, field):
    return dict(snapshot.column(kind, field))


def tamper(snapshot, writer, kind, field, updates, version="tampered"):
    """같은 열 전체를 (기존 값 + updates)로 다시 쓴다(core write 열 교체 의미). writer 는 권한표의 그 필드 writer."""
    col = column_dict(snapshot, kind, field)
    col.update(updates)
    return snapshot.write(writer, version, {(kind, field): col})


def seal_item(snapshot, n):
    from gmid_engine.sizing import DC_KEY
    return snapshot.value("graph", DC_KEY, "dc_seal_%d" % n)


def sign_of(kind):
    return 1.0 if kind == "nmos" else -1.0


def mos_table(snap):
    """{MOS: (kind, d, g, s, b)} -- S1 필드(입력)."""
    out = {}
    for name, cls in snap.column("device", "element_class"):
        if cls == "mos":
            p = dict(snap.value("device", name, "pins"))
            out[name] = (snap.value("device", name, "kind"), p["d"], p["g"], p["s"],
                         snap.value("device", name, "bulk").net)
    return out


def terminal_mag(kind, V, d, g, s, b):
    sg = sign_of(kind)
    return sg * (V[g] - V[s]), sg * (V[d] - V[s]), sg * (V[s] - V[b])


def expected_columns(snap, theta, fixed_values=(), resistor_values=()):
    """순환 SCC 가 없는 회로의 dc_solve 노드 풀이 독립 계산(CONTRACT 5.4 writer 식 + 창). 스냅샷에서는 계획 결과
    (dc_writer·dc_scc_order·dc_current(저항 강하 전류 포함, WB-1)·dc_L·dc_rail_v)와 S1 필드만 입력으로 읽는다.
    반환: (V, windows, ln_idu)."""
    from gmid_engine.sizing import DC_KEY
    th = dict(theta)
    writers = dict(snap.column("node", "dc_writer"))
    V = dict(snap.column("node", "dc_rail_v"))
    fixed = dict(fixed_values)
    for n, w in writers.items():
        if w.relation in ("declared_target", "input_dc"):
            V[n] = fixed[n]
    mt = mos_table(snap)
    L = dict(snap.column("device", "dc_L"))
    drop = dict(snap.column("device", "dc_current"))                # WB-1: 저항 강하 전류는 dc_current 가 담는다(전도 방향 양수)
    rvals = dict(resistor_values)
    rails = [v for _, v in snap.column("node", "dc_rail_v")]
    windows = {}
    entries = snap.value("graph", DC_KEY, "dc_scc_order")
    for e in entries:
        assert not e.cyclic, "expected_columns 는 비순환 회로만"
        (x,) = e.nodes
        w = writers[x]
        if w.relation in ("vgs_gate", "vgs_source"):
            kind, d, g, s, b = mt[w.element]
            # 아직 모르는 x 자신은 vgs 계산에 쓰이지 않는다(vds·vsb 는 d·s·b 만)
            vds = sign_of(kind) * (V[d] - V[s]) if x not in (d, s) else None
            vsb = sign_of(kind) * (V[s] - V[b]) if x not in (s, b) else None
            vgs = Oracle.vgs_of(kind, th[("ln_idu", w.element)], vds, vsb)
            V[x] = V[w.known] + sign_of(kind) * vgs if w.relation == "vgs_gate" else V[w.known] - sign_of(kind) * vgs
        elif w.relation == "resistor_drop":
            r = th.get(("resistance", w.element), rvals.get(w.element))
            i = drop[w.element]
            t0 = dict(snap.value("device", w.element, "pins"))["t0"]
            delta = 0.0 if i == 0 else (-i * r if w.known == t0 else i * r)
            V[x] = V[w.known] + delta
        elif w.relation == "free_window":
            lo, hi = min(rails), max(rails)
            for m, (kind, d, g, s, b) in mt.items():
                for term, other in (("d", s), ("s", d)):
                    node = d if term == "d" else s
                    if node != x:
                        continue
                    exits = (kind == "nmos" and term == "d") or (kind == "pmos" and term == "s")
                    if exits:
                        lo = max(lo, V[other])
                    else:
                        hi = min(hi, V[other])
            windows[x] = (lo, hi)
            V[x] = lo + th[("y", w.y_key)] * (hi - lo)
        else:
            raise AssertionError(w.relation)
    ln = {}
    for m, (kind, d, g, s, b) in mt.items():
        coord = snap.value("device", m, "dc_coord")
        if coord.role == "writer":
            ln[m] = th[("ln_idu", m)]
        else:
            vgs, vds, vsb = terminal_mag(kind, V, d, g, s, b)
            ln[m] = Oracle.ln_idu(kind, vgs, vds, vsb)
    return V, windows, ln


def run_blocks(ctx, theta, upto="widths"):
    """size_and_seal 의 평가 블록 셋(dc_currents -> dc_lengths -> dc_solve, WB-1 §3)을 호출 순서대로 직접 부른다(봉인 전 스냅샷).
    `dc_solve` 가 옛 `dc_solve`(노드 풀이)와 `dc_solve`(W)를 합친 블록이라 `upto` 의 "columns"·"widths" 는 같은 스냅샷을 낸다.
    `geometry`·`realized` 는 dc_solve 의 두 선택 인자(기본 None = 탐색 평가)."""
    from gmid_engine.sizing import dc_currents, dc_lengths, dc_solve
    run = dict(donors=ctx.donors, counters=ctx.counters)          # [card B C6] ctx 의 실행(두 객체) 그대로
    th = dict(theta)
    snap = dc_currents(ctx.base, tuple(sorted((k, v) for (t, k), v in th.items() if t == "current")), **run)
    snap = dc_lengths(snap, tuple(sorted((k, v) for (t, k), v in th.items() if t == "L")), **run)
    if upto == "lengths":
        return snap
    items = tuple(sorted(((t, k), v) for (t, k), v in th.items() if t in ("ln_idu", "resistance", "y")))
    return dc_solve(snap, items, kfixed(ctx), kres(ctx), ctx.lut, **run)


def eval_calls(ctx, theta):
    """평가 블록 셋(dc_currents, dc_lengths, dc_solve) 호출 목록 ((block, extras), ...) 과 그 결과 스냅샷(봉인 전).
    `calls` 형식은 계약에 적혀 있지 않아 공개 함수 `seal_versions` 가 받는 형식((블록, extras tuple), ...)을 쓴다."""
    from gmid_engine.sizing import dc_currents, dc_lengths, dc_solve
    th = dict(theta)
    cur = tuple(sorted((k, v) for (t, k), v in th.items() if t == "current"))
    ls = tuple(sorted((k, v) for (t, k), v in th.items() if t == "L"))
    items = tuple(sorted(((t, k), v) for (t, k), v in th.items() if t in ("ln_idu", "resistance", "y")))
    calls = ((dc_currents, (cur,)), (dc_lengths, (ls,)),
             (dc_solve, (items, kfixed(ctx), kres(ctx), ctx.lut)))
    snap = ctx.base
    for blk, ex in calls:
        snap = blk(snap, *ex, donors=ctx.donors, counters=ctx.counters)
    return snap, calls


def with_tol(ctx, theta):
    from gmid_engine.sizing import dc_tolerances
    snap, calls = eval_calls(ctx, theta)
    return dc_tolerances(snap, ctx.lut, donors=ctx.donors, counters=ctx.counters), calls


def resistances_of(ctx, theta):
    return tuple(kres(ctx)) + tuple(sorted((k, v) for (t, k), v in dict(theta).items()
                                                     if t == "resistance"))


def judge_expect(rows):
    """CONTRACT 6절 judge 의 독립 구현. rows = [(대상, 크기, tol|None, devices, nodes)].
    반환 dict: status, magnitude, tol, margin, devices, nodes, n_checked, n_undefined, worst."""
    def margin(mag, tol):
        return math.inf if tol == 0 else mag / tol
    defined = [r for r in rows if r[2] is not None]
    fails = [r for r in defined if r[1] > r[2]]
    undef = [r for r in rows if r[2] is None]
    if fails:
        status, tgt = "fail", fails
    elif undef:
        status, tgt = "undefined", undef
    else:
        status, tgt = "pass", []
    pool = fails if fails else defined
    out = {"status": status, "n_checked": len(rows), "n_undefined": len(undef),
           "devices": tuple(sorted({d for r in tgt for d in r[3]})),
           "nodes": tuple(sorted({n for r in tgt for n in r[4]}))}
    if pool:
        w = max(pool, key=lambda r: margin(r[1], r[2]))
        best = margin(w[1], w[2])
        # 최대 margin 동률 행들(동률 tie-break 은 계약에 없음 -> 어느 것이든 허용)
        out["ties"] = {r[0]: (r[1], r[2]) for r in pool if margin(r[1], r[2]) == best}
        out.update(magnitude=w[1], tol=w[2], margin=best, worst=w[0])
    else:
        out.update(magnitude=None, tol=None, margin=None, worst=None, ties={})
    return out


def assert_item(item, exp, n, rtol=1e-9, atol=1e-300, check_devices=True, check_nodes=True):
    from gmid_engine.sizing import SealItem
    assert isinstance(item, SealItem) and item.item == n
    assert item.status == exp["status"]
    det = dict(item.detail)
    assert [k for k, _ in item.detail] == sorted(det)
    assert det["n_checked"] == exp["n_checked"]
    assert det["n_undefined"] == exp["n_undefined"]
    if exp["status"] != "pass":
        if check_devices:
            assert item.devices == exp["devices"]
        if check_nodes:
            assert item.nodes == exp["nodes"]
    if exp["status"] == "undefined":
        return
    if exp["magnitude"] is None:
        assert item.magnitude is None and item.margin is None
        return
    assert det["worst"] in exp["ties"], (det["worst"], exp["ties"])
    mag_e, tol_e = exp["ties"][det["worst"]]
    for a, b in ((item.magnitude, mag_e), (item.tol, tol_e)):
        assert rel_close(a, b, rtol, atol), (a, b)
    if math.isinf(exp["margin"]):
        assert math.isinf(item.margin)
    elif exp["status"] == "fail":
        assert rel_close(item.margin, exp["margin"], rtol), (item.margin, exp["margin"])


def node_voltages(snap):
    V = dict(snap.column("node", "dc_rail_v"))
    V.update(dict(snap.column("node", "dc_v")))
    return V


def wl_colours(snap):
    """CONTRACT 3.0 구조 색(1-WL)의 독립 구현. 입력은 S1 필드만. 반환 ({노드: 색}, {원소: 색}).
    [U17 ①-d] 설계 40 v1.6 §6-8 D-2: 1-WL 색 `wl` 도 정준 위치·생성자와 같은 그래프 하나에서 정하고, 그 그래프에서 MOS 의 d·s 엣지는 같은 라벨
    `c`(채널)다 -- 그래서 여기 MOS 링크도 d·s -> c."""
    nodes = list(snap.keys("node"))
    elems = list(snap.keys("device"))
    sig0 = {}
    for e in elems:
        f = snap.field("device", e, "is_diode")
        sig0[("e", e)] = ("e", snap.value("device", e, "element_class"), snap.value("device", e, "kind"),
                          bool(f.value) if f is not None else False)
    for n in nodes:
        pd = snap.value("node", n, "port_direction")
        sig0[("n", n)] = ("n", bool(snap.value("node", n, "is_rail")), pd if pd is not None else "")
    adj = {v: [] for v in sig0}
    for e in elems:
        cls = snap.value("device", e, "element_class")
        kind = snap.value("device", e, "kind")
        pins = dict(snap.value("device", e, "pins"))
        links = []
        if cls == "mos":
            links = [("c", pins["d"]), ("g", pins["g"]), ("c", pins["s"])]
            bf = snap.field("device", e, "bulk")
            if bf is not None and bf.value is not None and bf.value.net is not None:
                links.append(("b", bf.value.net))
        elif cls == "ideal_source" and kind == "current_source":
            links = [("t0", pins["t0"]), ("t1", pins["t1"])]
        else:
            links = [("t", pins["t0"]), ("t", pins["t1"])]
        for lab, net in links:
            adj[("e", e)].append((lab, ("n", net)))
            adj[("n", net)].append((lab, ("e", e)))

    def rank(sig):
        order = {s: i for i, s in enumerate(sorted(set(sig.values())))}
        return {v: order[s] for v, s in sig.items()}
    col = rank(sig0)
    while True:
        sig = {v: (col[v], tuple(sorted((lab, col[u]) for lab, u in adj[v]))) for v in col}
        new = rank(sig)
        if len(set(new.values())) <= len(set(col.values())):
            break
        col = new
    return ({k[1]: c for k, c in col.items() if k[0] == "n"}, {k[1]: c for k, c in col.items() if k[0] == "e"})


def rref_free(columns, rows):
    """정확 유리수 RREF(열 왼쪽부터 pivot). rows = [{col: coef}]. -> (pivot 열 목록, free 열 목록, {pivot: {free: coef}})."""
    M = [[Fraction(r.get(c, 0)) for c in columns] for r in rows]
    piv = []
    r = 0
    for ci in range(len(columns)):
        p = next((i for i in range(r, len(M)) if M[i][ci] != 0), None)
        if p is None:
            continue
        M[r], M[p] = M[p], M[r]
        inv = M[r][ci]
        M[r] = [v / inv for v in M[r]]
        for i in range(len(M)):
            if i != r and M[i][ci] != 0:
                f = M[i][ci]
                M[i] = [a - f * b for a, b in zip(M[i], M[r])]
        piv.append(ci)
        r += 1
    free = [c for i, c in enumerate(columns) if i not in piv]
    expr = {}
    for ri, ci in enumerate(piv):
        expr[columns[ci]] = {columns[j]: -M[ri][j] for j in range(len(columns)) if j not in piv and M[ri][j] != 0}
    return [columns[i] for i in piv], free, expr


# ---------------------------------------------------------------------------
# [U4] sizing 보강 공용 입력 (설계 40 §3.7, 41 §5.3·§4.6) -- 입력 생성용. 기대값은 각 test 의 닫힌 식·독립 풀이.
# ---------------------------------------------------------------------------

class LClassStub:
    """U1 `S1v.l_classes` 원소의 자리(CONTRACT 14.1: 이 모듈은 `owner`·`members`·`status` 속성만 읽는다).
    [U17 ①-b] L 동치류는 이제 S0 수준 필드 `graph/s1v: l_classes`(설계 40 v1.9.1 §2.4.8 D1)에서 읽힌다(`build_kernel_context(l_classes=)` 삭제,
    §2.4.7 KernelContext 행). `inject_l_classes` 가 이 자리 값을 graph `LClass` 로 바꿔 그 필드에 넣는다(test 입력)."""
    __slots__ = ("owner", "members", "status")

    def __init__(self, owner, members, status="derived"):
        self.owner, self.members, self.status = owner, tuple(members), status


def inject_l_classes(s1, l_classes):
    """[U17 ①-b] test 입력: S1Graph 에 S1v 필드 `graph/s1v: l_classes`(writer `build_s1v`, 설계 40 v1.9.1 §2.4.8 D1)를 넣은 S1Graph.
    손 회로 test 가 L 동치류를 직접 정하던 옛 `build_kernel_context(l_classes=)` 입력의 자리 -- 커널 구조 파생 블록(`kernel_fields`)이 이 필드를
    읽는다(§2.4.7·§2.4.8 '커널 컨텍스트 구조 파생'). 빈 묶음이면 S1 그대로(S1v 필드 없음 = 소자마다 L). owner_rule 은 kernel 이 읽지 않는 칸이라
    자리 표시 문자열."""
    if not l_classes:
        return s1
    from gmid_engine.graph import S1V_KEY, S1V_WRITERS, BUILD_S1V_WRITER, LClass, S1Graph
    values = tuple(LClass(tuple(c.members), c.owner, "test_injected", c.status) for c in l_classes)
    snap = s1.snapshot.widen(S1V_WRITERS).write(BUILD_S1V_WRITER, "test-injected-l-classes",
                                                {("graph", "l_classes"): {S1V_KEY: values}})
    return S1Graph(s1.key, snap)


def kschema(ctx):
    """[U17 ①-b] θ 스키마 = S0 수준 필드 `graph/kernel: theta_schema`(설계 40 v1.9.1 §2.4.7 KernelContext 행·§2.4.8 D8, 옛 `ctx.schema`)."""
    return ctx.base.value("graph", KERNEL_KEY, "theta_schema")


def kfixed(ctx):
    """`graph/kernel: fixed_values`(옛 `ctx.fixed_values`)."""
    return ctx.base.value("graph", KERNEL_KEY, "fixed_values")


def kres(ctx):
    """`graph/kernel: resistor_values`(옛 `ctx.resistor_values`)."""
    return ctx.base.value("graph", KERNEL_KEY, "resistor_values")


def kties(ctx):
    """`graph/kernel: l_ties`(옛 `ctx.l_ties`)."""
    return ctx.base.value("graph", KERNEL_KEY, "l_ties")


def kplan(ctx):
    """옛 `ctx.plan_versions` 대체 -- 쓰기 계획 블록의 block_version 읽기(설계 40 §2.4.7 'plan_versions 는 … block_version 읽기로 대체')."""
    return tuple((w, ctx.base.block_version(w)) for w in PLAN_WRITERS)


def build_ctx_u4(tmp_path, doc, access, l_classes=(), supplies=None, **inputs_kw):
    """`build_ctx` 와 같되 U4 인자(l_classes)를 넘긴다. [TB-1] 순서 힌트 인자는 없어졌다(종속 멤버는 θ 분류·구조 위치가 정한다).
    [U17 ①-b] l_classes 는 `inject_l_classes` 로 S1 의 `graph/s1v: l_classes` 필드에 넣는다. 반환 (S1Graph, KernelContext)."""
    Path(tmp_path).mkdir(parents=True, exist_ok=True)
    donors, counters = open_run()          # [card B C0] 실행 하나 = 이 호출 하나
    td = load_doc(tmp_path, doc)
    sup = dict(SUPPLIES if supplies is None else supplies)
    s1 = inject_l_classes(build_s1(td, sup, donors=donors, counters=counters), tuple(l_classes))
    inputs = DcInputs(tuple(sorted(sup.items())), **inputs_kw)
    return s1, build_kernel_context(s1, inputs, access, donors=donors, counters=counters)


def circuit_mirror(names=("M1", "M2", "M3", "I1"), nets=("nb", "out", "in")):
    """nmos diode M1(nb, nb, gnd) + 거울 M2(out, nb, gnd) + pmos 부하 M3(out, in, vdd), 이상 전류원 I1(vdd -> nb). bulk = source 레일.
    names·nets 로 이름 전단사를 만든다(구조 동일). 기둥 둘: {I1, M1}·{M3, M2}."""
    m1, m2, m3, i1 = names
    nb, out, inn = nets
    net = [mos(m1, "nmos", nb, nb, "gnd", "gnd"), mos(m2, "nmos", out, nb, "gnd", "gnd"),
           mos(m3, "pmos", out, inn, "vdd", "vdd")]
    return topo("u4_mirror", net, {inn: ("input", "x"), out: ("output", "y")},
                sources=[two(i1, "current_source", "vdd", nb)])


def theta_mirror(names=("M1", "M2", "M3", "I1"), out="out", vgs1=0.6, vgs3=0.7, y=0.5, l=(1e-6, 1e-6, 1e-6), i=1e-5):
    """circuit_mirror 의 θ (I1 = i 선언, l = (M1, M2, M3) L). M1 diode 좌표 = vgs1 이 근(VDS = VGS)인 r4 좌표, M3 좌표 = vgs3 at
    VDS = 1.8 − y·1.8."""
    m1, m2, m3, _ = names
    return {("L", m1): l[0], ("L", m2): l[1], ("L", m3): l[2], ("current", m3): i,
            ("ln_idu", m1): r4_ln_idu("nmos", vgs1, vgs1, 0.0), ("ln_idu", m3): r4_ln_idu("pmos", vgs3, 1.8 - y * 1.8, 0.0),
            ("y", out): y}


def with_hand_ss(ev, gm_scale=None):
    """평가 `ev` 에 손 `ss_dev`(gm = gm_scale[m]·dc_op.gm_id·dc_op.current, 기본 배율 1 -> 그 점의 gm 과 정합)를 써서 S2p parent 를
    만든다(metrics `ss_dev` 계산 블록의 자리 -- 권한표 writer 로 쓴다). 반환 DcEvaluation(봉인 점이면 sealed = 같은 스냅샷)."""
    from gmid_engine.metrics import SsDevice
    from gmid_engine.sizing import S2_WRITERS, DcEvaluation, SealedSnapshot
    scale = dict(gm_scale or {})
    ops = dict(ev.snapshot.column("device", "dc_op"))
    col = {m: SsDevice(scale.get(m, 1.0) * o.gm_id * o.current, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0,
                       "hand", "hand", "hand") for m, o in ops.items()}
    snap = ev.snapshot.write(S2_WRITERS.writer_of("device", "ss_dev"), "hand_ss", {("device", "ss_dev"): col})
    return DcEvaluation(snap, ev.report, SealedSnapshot(snap, ev.report) if ev.sealed is not None else None)


# [U17 ①-d] 옛 test_struct_colour.py(원본 sizing/struct_colour.py 삭제로 tests/graph/test_s1_symmetry.py 로 옮김)의 입력 구성 helper --
# test_writer_plan·test_theta_schema 가 쓰므로 공용 conftest 로 옮겼다(기대값 아님, 이름 전단사 입력 생성).
def rename(doc, seed):
    """넷·원소 이름 전단사 σ(무작위). 반환 (새 doc, σ_net, σ_el)."""
    d = json.loads(json.dumps(doc))
    nets = set(d["supply_nets"]) | {k for k in d["ports"] if not k.startswith("_")}
    for e in d["netlist"]:
        nets |= {e["drain"], e["gate"], e["source"]} | ({e["bulk"]} if e.get("bulk") else set())
    for key in ("passive_elements", "ideal_sources"):
        for e in d.get(key) or []:
            nets |= set(e["terminals"])
    els = [e["name"] for e in d["netlist"]] + [e["name"] for k in ("passive_elements", "ideal_sources")
                                                for e in (d.get(k) or [])]
    rng = random.Random(seed)
    nl = sorted(nets)
    tn = ["n%03d_%d" % (i, seed) for i in range(len(nl))]
    rng.shuffle(tn)
    sn = dict(zip(nl, tn))
    te = ["E%03d_%d" % (i, seed) for i in range(len(els))]
    rng.shuffle(te)
    se = dict(zip(sorted(els), te))
    for e in d["netlist"]:
        e["name"] = se[e["name"]]
        for k in ("drain", "gate", "source", "bulk"):
            if k in e:
                e[k] = sn[e[k]]
    for key in ("passive_elements", "ideal_sources"):
        for e in d.get(key) or []:
            e["name"] = se[e["name"]]
            e["terminals"] = [sn[t] for t in e["terminals"]]
    d["supply_nets"] = [sn[n] for n in d["supply_nets"]]
    d["ports"] = {(k if k.startswith("_") else sn[k]): v for k, v in d["ports"].items()}
    for k in list(d):
        if k in ("device_roles", "symmetry", "sizing_roles", "compensation") or (k.startswith("_") and k != "_comment"):
            d.pop(k)
    if "bias_inputs" in d:                                   # authoring 9절 선언도 같은 σ 로 옮긴다(이름 전단사의 일부)
        d["bias_inputs"] = [sn[n] for n in d["bias_inputs"]]
    d["topology_name"] = d["topology_name"] + "_r%d" % seed
    return d, sn, se


def rename_inputs(inputs, sn, se):
    """DcInputs 의 이름 자리(레일·노드 목표·원소 값·영역 선언 regions·engine 원소)를 σ 로 옮긴다(입력 구성, 기대값 아님)."""
    return DcInputs(tuple(sorted((sn[k], v) for k, v in inputs.supplies_v)), inputs.input_dc_v,
                    tuple(sorted((sn[k], v) for k, v in inputs.node_targets)),
                    tuple(sorted((se[k], v) for k, v in inputs.element_values)),
                    tuple(sorted((dataclasses.replace(r, device=se[r.device]) for r in inputs.regions), key=lambda r: r.device)),
                    inputs.pending,
                    tuple(sorted(se[k] for k in inputs.engine_elements)))


def mirror_w_nat(vgs1=0.6, y=0.5, i=1e-5, l=1e-6):
    """circuit_mirror 종속 소자 M2 의 '그 전류에 맞는 W'(닫힌 식, CONTRACT 14.3): W = ID·L / IDu_forward(V(nb) = vgs1 -- θ 구성상
    M1 diode 근, VDS = V(out) = y·1.8, VSB 0). theta_mirror 의 기본 θ 와 같은 인자."""
    return i * l / math.exp(r4_ln_idu("nmos", vgs1, y * 1.8, 0.0))


# [U17 ①, 설계 40 §3.7-3] 종속 소자 M2 에 W 를 요청하면 봉인 3 이 그 어긋남 δ = W_req/W_nat − 1 을 판정한다: 잔차 = δ·ID ≤ tol_I =
# tol_V × max(dc_gm(M2), dc_gm(M3)), dc_gm = (B − C·VGS)·ID(r4 닫힌 식) -> δ_max = tol_V × max(B − C·0.6, B − C·0.7) = tol_V × 15.2.
# r4 toy 의 tol_V 셀(dc_tol_v 입력, 모든 셀 같음)은 1/128 V 라 δ_max = 0.11875. 옛 상계(곡선 격자 최대 gm)에서는 δ 0.27(요청 3e-5)도
# 통과했지만 자기 동작점 gm 에서는 거부된다(판정 변화 -- 설계 §2.4.12 Q7 기록 대상). 봉인되는 요청은 δ < δ_max 로 잡는다.
MIRROR_W_DELTA = 0.05


def mirror_w_request(delta=MIRROR_W_DELTA, **kw):
    """봉인 3 허용오차 안의 종속 소자 M2 W 요청값 = (1 + delta)·W_nat. delta 는 δ_max(위 주석, test 가 dc_tol_v 입력으로 재확인) 아래."""
    return (1.0 + delta) * mirror_w_nat(**kw)


def mirror_delta_max(snapshot):
    """δ_max = max_{m ∈ M2, M3} tol_V(m) × (B − C·VGS(m))(설계 40 §3.7-3 tol_I = tol_V × max dc_gm 을 ID 로 나눈 것 -- M2·M3 의 ID 는
    out 노드 KCL 로 같다) -- 입력은 스냅샷의 dc_tol_v 셀과 동작점 VGS(피검 블록의 입력), gm/ID 는 r4 닫힌 식."""
    tol = dict(snapshot.column("device", "dc_tol_v"))
    ops = dict(snapshot.column("device", "dc_op"))
    return max(tol[m] * (B - C * ops[m].vgs) for m in ("M2", "M3"))


# ---------------------------------------------------------------------------
# [LM-1e §5] toy R(r4 꼴, pmos 의 VDS index 0 열 꺼짐) + J-a 상태 -- 셀 결합 test(J-a·J-b·J-c·P-1)의 공통 입력.
# 격자 R4_VDS = 0, 0.25, ...: pmos 슬라이스의 tol 셀 VDS index 0 = None(켜진 격자점 없음 -- 정의상), index 1 이상은 값.
# ---------------------------------------------------------------------------

def r_off_access(root):
    """toy R LUT(pmos VDS index 0 열 꺼짐)의 LutAccess."""
    return new_access(write_r4_lut(Path(root), off_cols={"pmos": 1}))


def ja_theta(ctx, y1, y2):
    """`_scc_s_doc`(M1 nmos (vin, nb1, gnd), M2 nmos (vout, nb2, vin), M3 pmos (vout, pb, vdd)) 의 θ: 선형 SCC 닫힌 해
    vout = 1.8·y2 / (1 − y1(1 − y2)), vin = y1·vout 에서 각 소자의 VGS 가 0.6·0.7·0.7 이 되는 ln_idu(r4 닫힌 식)."""
    vout = 1.8 * y2 / (1.0 - y1 * (1.0 - y2))
    vin = y1 * vout
    th = {("L", "M1"): 1e-6, ("L", "M2"): 1e-6, ("L", "M3"): 1e-6,
          ("ln_idu", "M1"): r4_ln_idu("nmos", 0.6, vin, 0.0), ("ln_idu", "M2"): r4_ln_idu("nmos", 0.7, vout - vin, vin),
          ("ln_idu", "M3"): r4_ln_idu("pmos", 0.7, 1.8 - vout, 0.0), ("y", "vin"): y1, ("y", "vout"): y2}
    th.update(free_currents(ctx, {"M1": 1e-5, "M2": 1e-5, "M3": 1e-5}))
    assert set(th) == set(kschema(ctx).components)
    return th, vin, vout


def ja_state(tmp_path, y1=0.6, y2=0.4, vds=0.1):
    """J-a 입력: toy R + `_scc_s_doc` + 손 θ(y1, y2) 를 `run_blocks(upto="columns")` 까지 돌린 스냅샷에서 **`dc_op["M3"]` 의 `vds` 만 vds 로
    바꾼** 스냅샷(`dataclasses.replace` + `tamper`; `dc_tol_v` 는 주입하지 않는다)에 `dc_tolerances` 를 적용한다.
    반환 (ctx, th, 바꾼 스냅샷, dc_tolerances 뒤 스냅샷). 기본 (y1, y2) = (0.6, 0.4) -> vout = 1.125 V, 바꾸기 전 M3 의 |VDS| = 0.675 V(켜진 칸)."""
    from gmid_engine.sizing import dc_tolerances
    from sizing.test_block_dc import _scc_s_doc
    root = Path(tmp_path)
    (root / "ctx").mkdir(parents=True, exist_ok=True)
    ctx = build_ctx(root / "ctx", _scc_s_doc(), r_off_access(root / "lut"))[2]
    th, _vin, _vout = ja_theta(ctx, y1, y2)
    snap = run_blocks(ctx, th, upto="columns")
    op = dict(snap.column("device", "dc_op"))["M3"]
    changed = tamper(snap, "dc_solve", "device", "dc_op", {"M3": dataclasses.replace(op, vds=vds)})
    return ctx, th, changed, dc_tolerances(changed, ctx.lut, **run_of(ctx))
