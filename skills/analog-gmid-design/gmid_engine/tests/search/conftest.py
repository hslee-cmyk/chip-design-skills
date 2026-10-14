"""tests/search 공용 -- `gmid_engine/search/CONTRACT.md`(r4) + sizing·metrics·core·lut 계약만 근거로 만든 입력과 독립 계산.
search `.py` 소스는 열람하지 않았다(작성자 ≠ 검증자).

- toy LUT: sizing conftest 의 r4 toy(VDSAT 열 있음 -> 봉인 7 실판정, `write_r4_lut`)와 VDSAT 열 없는 변형(봉인 7 undefined ->
  `pending_seal_7` 경로)을 그대로 쓴다. 격자는 2진 분수라 손계산이 정확하다.
- toy PDK 선언: core 9.1 형식(lef_statement 원본 하나)으로 `manufacturing_grid_m`·`min_finger_w_m` 을 선언한다.
- 손 회로: 회로 C(nmos M1 + pmos 부하 M2, sizing conftest), 회로 P(pmos M1 + θ 저항 R1 -> gnd).
- 기대값: npz 배열·스냅샷 입력 열·닫힌 식으로 이 파일/test 가 계산한다. 비지배 필터·ε 격자는 독립 구현(`ref_*`).
- S3 root 는 Windows 경로 길이(계약 6절) 때문에 %TEMP% 바로 아래 짧은 폴더(`short_root`)를 쓴다.
"""
from __future__ import annotations

import hashlib
import json
import math
import os
import shutil
import tempfile
from pathlib import Path
from types import SimpleNamespace

import numpy as np
import pytest

from gmid_engine.core import engine_code_fp

# [U17 ①-a] build_search_context(code_fp=) 필수 -- 단계 A 가 실행마다 한 번 잰 엔진 코드 지문(설계 40 §2.4.3 (iii)).
# 단계 A 를 거치지 않는 test 는 같은 공개 함수 core.engine_code_fp() 를 모듈 import 때 한 번 재서 넘긴다.
CODE_FP = engine_code_fp()

from sizing.conftest import (  # noqa: F401  (다른 test 파일이 여기서 가져간다)
    R4_GRIDS,
    R4_L,
    R4_VDS,
    R4_VGS,
    R4_VS,
    SUPPLIES,
    W_M,
    circuit_cs_pmos_load,
    mos,
    r4_arrays,
    r4_ln_idu,
    real_lut_v2,
    rel_close,
    tamper,
    theta_r4c,
    topo,
    two,
    write_r4_lut,
)
from sizing.conftest import I0, LAM, r4_vs_term  # noqa: E402
from metrics.conftest import spec_json, toy_junction_decls  # noqa: E402

HERE = Path(__file__).resolve().parent
SKILL_DIR = HERE.parents[2]
TESTS_DIR = HERE.parent

GRID_UM = "0.01"        # toy PDK 제조 격자 0.01 µm = 1e-8 m (toy LUT 격자와 같음)
MINW_UM = "0.5"         # toy PDK 최소 finger 폭 0.5 µm
GRID = 1e-8
W_MIN = 5e-7
SRC = (("front_budget_s", "test_fixture"),)


# ---------------------------------------------------------------- toy PDK 선언 (core 9.1)


# [U17 ①-b] 설계 40 v1.9.1 §2.4.7 KernelContext 행: θ 스키마·L 묶음은 칸이 아니라 S0 수준 필드 `graph/kernel: theta_schema·l_ties`(§2.4.8, D8) --
# test 는 커널 컨텍스트의 `base` 스냅샷에서 그 필드를 읽는다(사본 없음).
def schema_of(dc):
    from gmid_engine.sizing import KERNEL_KEY
    return dc.base.value("graph", KERNEL_KEY, "theta_schema")


def l_ties_of(dc):
    from gmid_engine.sizing import KERNEL_KEY
    return dc.base.value("graph", KERNEL_KEY, "l_ties")


def domain_of(dc, settings, pdk_decl, spec_bounds=(), area_budget_m2=None, untie=()):
    """[U17 ①-b] 탐색 정의역 읽기 -- `search_domain` 은 계산 블록이 됐다(설계 40 §2.4.7 'SearchContext 칸 배정' `domain` 행, §2.4.8: S0 수준 필드
    `graph/kernel: search_domain`, extras = 실행 설정의 θ 수동소자 상자·PDK 선언·spec 상자·면적 예산·untie). 커널 컨텍스트 `base` 를 S0 수준 권한표로 넓혀 블록을
    부르고 그 필드를 읽는다(옛 `search_domain(dc_ctx, settings, pdk_decl, spec_bounds, area_budget_m2, untie) -> SearchDomain` 의 같은 입력)."""
    from gmid_engine.search import search_domain
    from gmid_engine.search.s0_fields import S0_WRITERS
    from gmid_engine.sizing import KERNEL_KEY
    snap = search_domain(dc.base.widen(S0_WRITERS), dc.lut, settings.resistance_bounds_ohm, settings.capacitance_bounds_f, pdk_decl,
                         tuple(spec_bounds), area_budget_m2, tuple(untie))
    return snap.value("graph", KERNEL_KEY, "search_domain")


def area_decl_of(dc, spec, pdk_decl):
    """[U17 ①-b] 수동소자 면적 선언 읽기 -- `passive_area_decl` 은 계산 블록이 됐다(설계 40 §2.4.7 'SearchContext 칸 배정' `area_decl` 행: S0 수준 필드
    `graph/kernel: passive_area_decl`). extras = spec 측정 부하 원소 이름(build_search_context 와 같은 spec 읽기: element_values 중 measurement_load)·PDK 선언."""
    from gmid_engine.search.area_decl import passive_area_decl
    from gmid_engine.search.s0_fields import S0_WRITERS
    from gmid_engine.sizing import KERNEL_KEY
    loads = tuple(sorted(e.name for e in spec.element_values if e.measurement_load))
    return passive_area_decl(dc.base.widen(S0_WRITERS), loads, pdk_decl).value("graph", KERNEL_KEY, "passive_area_decl")


def _decl_paths(root, grid_um=GRID_UM, minw_um=MINW_UM, with_minw=True):
    """[r6] toy PDK 선언 = metrics conftest 의 toy 접합 선언(모델 카드 27 양 × kind) + lef 원본의 격자·최소 finger 폭,
    LUT 생성 규칙 선언 = metrics conftest 의 toy 규칙 선언(core 9.1 형식, metrics 8.5 소비). 반환 (pdk 경로, 규칙 경로)."""
    root = Path(root)
    root.mkdir(parents=True, exist_ok=True)
    pp, rp = toy_junction_decls(root)
    decl = json.loads(Path(pp).read_text(encoding="utf-8"))
    lef = root / "toy.lef"
    lef.write_text("MANUFACTURINGGRID %s ;\nMINW %s ;\n" % (grid_um, minw_um), encoding="utf-8")
    sha = hashlib.sha256(lef.read_bytes()).hexdigest()
    decl["sources"]["lef"] = {"path": "toy.lef", "sha256": sha, "format": "lef_statement", "encoding": "utf-8",
                              "units_m": {"": 1e-6}}
    decl["quantities"]["manufacturing_grid_m"] = {"source": "lef", "expression": "MANUFACTURINGGRID", "basis": "toy grid"}
    if with_minw:
        decl["quantities"]["min_finger_w_m"] = {"source": "lef", "expression": "MINW", "basis": "toy min finger"}
    Path(pp).write_text(json.dumps(decl), encoding="utf-8")
    return pp, rp


# [U17 ①-b 3차, 사용자 결정 2026-10-14 "(가) 경로 인자 필수"] run_stage_a(pdk_decl_path=, lut_rule_decl_path=) 필수 -- PdkDecl 값에는 경로가
# 없으므로(결정 7) toy 선언을 만든 helper 가 '그 선언 바이트를 가진 파일' 을 기록해 두고 단계 A 를 부르는 helper 가 `decl_path(decl)` 로 찾는다.
# 키 = decl_sha256(선언 파일 원본 바이트 sha256, core 9.2). 찾은 파일은 매번 바이트를 다시 해시해 같은지 확인한다(다르면 실패 -- 조용한 틀린 경로 없음).
_DECL_FILES = {}
_REPO_DECL_FILES = (SKILL_DIR / "assets" / "sky130_pdk_decl.json", SKILL_DIR / "assets" / "sky130_lut_rule_decl.json")


def _read_recorded(path, memo):
    from gmid_engine.core import read_pdk_decl
    decl = read_pdk_decl(str(path), memo)
    _DECL_FILES[decl.decl_sha256] = str(path)
    return decl


def decl_path(decl):
    """선언 값 `decl` 을 읽어 온 파일 경로(입력 준비 -- 기대값 아님): toy helper 가 기록한 파일, 없으면 저장소 선언 원본 중 바이트 sha 가 같은 것."""
    cands = [_DECL_FILES[decl.decl_sha256]] if decl.decl_sha256 in _DECL_FILES else [str(p) for p in _REPO_DECL_FILES]
    for c in cands:
        if hashlib.sha256(Path(c).read_bytes()).hexdigest() == decl.decl_sha256:
            return c
    raise AssertionError("선언 sha %s 의 파일을 찾지 못했다" % decl.decl_sha256)


def write_decls(root, **kw):
    """-> (PdkDecl, LUT 규칙 PdkDecl)."""
    from gmid_engine.core import BoundedLRU
    pp, rp = _decl_paths(root, **kw)
    memo = BoundedLRU(8)
    return _read_recorded(pp, memo), _read_recorded(rp, memo)


def write_pdk(root, **kw):
    return write_decls(root, **kw)[0]


# [결정 11, 2026-10-08] toy MIM 단위 면적 원본 -- core 9.1 `spice_instance_line` 형식(sky130 선언의 mim_cap_params 와 같은 모양:
# `.param` 다음 줄 `+ camimc= <F/µm²>  $ 주석`, units_m "" = 1e12 (µm² -> m²)). 값은 test 가 고르는 구성 입력.
TOY_CAMIMC_F_PER_UM2 = "4.0e-15"
TOY_MIM_DENSITY = 4.0e-3                # F/m² = 4.0e-15 F/µm² x 1e12 µm²/m² (단위 환산, 구성 값)


def write_decls_mim(root, camimc=TOY_CAMIMC_F_PER_UM2, **kw):
    """write_decls + PDK 선언에 원본 `toy_rc` 와 quantity `mim_cap_density_f_per_m2`(식 `camimc`) 추가. -> (PdkDecl, 규칙 PdkDecl)."""
    from gmid_engine.core import BoundedLRU
    pp, rp = _decl_paths(root, **kw)
    root = Path(root)
    rc = root / "toy_rc.spice"
    rc.write_text("* toy r+c\n.param\n+ camimc=  %s  $ Units: farad/micrometer^2\n+ cpwell=  1.0e-15\n" % camimc,
                  encoding="utf-8")
    decl = json.loads(Path(pp).read_text(encoding="utf-8"))
    decl["sources"]["toy_rc"] = {"path": "toy_rc.spice", "sha256": hashlib.sha256(rc.read_bytes()).hexdigest(),
                                 "format": "spice_instance_line", "encoding": "utf-8",
                                 "line_pattern": r"^\+\s*(camimc\s*=\s*[^\s$]+)", "units_m": {"": 1e12}}
    decl["quantities"]["mim_cap_density_f_per_m2"] = {"source": "toy_rc", "expression": "camimc", "basis": "toy MIM"}
    Path(pp).write_text(json.dumps(decl), encoding="utf-8")
    memo = BoundedLRU(8)
    return _read_recorded(pp, memo), _read_recorded(rp, memo)


# ---------------------------------------------------------------- LUT

@pytest.fixture(scope="session")
def lut_sealed(tmp_path_factory):
    """VDSAT 열(nmos·pmos) -> 봉인 7 판정."""
    return write_r4_lut(tmp_path_factory.mktemp("s_lut_sealed"))


@pytest.fixture(scope="session")
def lut_pending(tmp_path_factory):
    """VDSAT 열 없음 -> 봉인 7 undefined(lut_vdsat_column_missing) -> pending_seal_7."""
    return write_r4_lut(tmp_path_factory.mktemp("s_lut_pending"), vdsat=())


def new_access(lut):
    from gmid_engine.lut import LutMemo
    from gmid_engine.sizing import pre_layout_lut_access
    return pre_layout_lut_access(LutMemo(lut, point=4096, curve=4096, root=4096))


@pytest.fixture
def short_root():
    """S3 root -- %TEMP% 바로 아래 짧은 폴더(지문 두 개 64자 + 파일 이름이 260자 안에 들게)."""
    d = tempfile.mkdtemp(prefix="s6", dir=os.environ.get("TEMP") or None)
    yield d
    shutil.rmtree(d, ignore_errors=True)


# ---------------------------------------------------------------- 손 회로

def circuit_c(with_cap=False):
    """회로 C: M1 nmos (out, in, gnd) + M2 pmos (out, pb, vdd). with_cap: CL (out, gnd) 값은 spec 에서."""
    d = circuit_cs_pmos_load()
    if with_cap:
        d["passive_elements"] = [two("CL", "capacitor", "out", "gnd")]
    return d


def circuit_p():
    """회로 P: M1 pmos (out, in, vdd) + R1 (out, gnd), R1 값은 θ resistance(spec engine). V(out) = I·R."""
    return topo("hand_pres", [mos("M1", "pmos", "out", "in", "vdd")],
                {"in": ("input", "single_ended_input"), "out": ("output", "single_ended_output")},
                passives=[two("R1", "resistor", "out", "gnd")])


def theta_p(dc, i=1e-5, r=9e4, vgs=0.6, l1=1e-6):
    """회로 P 의 θ. 전류 성분 키는 스키마(입력)에서 읽는다(기저 free 원소가 M1/R1 중 무엇이든 같은 전류)."""
    comps = dict.fromkeys(schema_of(dc).components)
    th = {("L", "M1"): l1, ("ln_idu", "M1"): r4_ln_idu("pmos", vgs, 1.8 - i * r, 0.0), ("resistance", "R1"): r}
    for k in comps:
        if k[0] == "current":
            th[k] = i
    assert set(th) == set(comps), (sorted(th), sorted(comps))
    return th


def circuit_n():
    """회로 N: M1 nmos (out, in, gnd) + R1 (vdd, out), R1 = θ resistance. 레일에 채널이 닿는 MOS 는 gnd(0 V) 의 M1 뿐 ->
    b_P = |0|·tol_I = 0 -> 계약 3.6 '합이 0 이면 None'."""
    return topo("hand_nres", [mos("M1", "nmos", "out", "in", "gnd")],
                {"in": ("input", "single_ended_input"), "out": ("output", "single_ended_output")},
                passives=[two("R1", "resistor", "vdd", "out")])


def theta_n(dc, i=1e-5, r=9e4, vgs=0.6, l1=1e-6):
    comps = dict.fromkeys(schema_of(dc).components)
    th = {("L", "M1"): l1, ("ln_idu", "M1"): r4_ln_idu("nmos", vgs, 1.8 - i * r, 0.0), ("resistance", "R1"): r}
    for k in comps:
        if k[0] == "current":
            th[k] = i
    assert set(th) == set(comps), (sorted(th), sorted(comps))
    return th


def on_mask(a):
    return (a["ID"] > 0) & (a["GM"] > 0)


def expect_box(pre_arr, all_arrs):
    """3.19 의 독립 계산. pre_arr = 레이아웃 전 슬라이스 배열, all_arrs = 그 kind 의 모든 슬라이스 배열."""
    vgs = np.asarray(pre_arr["VGS"], dtype=float)
    tol = math.ulp(max(abs(vgs[0]), abs(vgs[-1])))
    z = [i for i, v in enumerate(vgs) if abs(v) <= tol]
    assert z, "test 입력에 VGS 0 이 있어야 한다"
    i0 = z[0]
    ID, GM = pre_arr["ID"][:, i0], pre_arr["GM"][:, i0]
    m = (ID > 0) & (GM > 0)
    i_off = float(ID[m].min())
    i_max = max(float(a["ID"][on_mask(a)].max()) for a in all_arrs)
    return i_off, i_max


def expect_ln_idu_bounds(a, w_m=W_M):
    """3.7 ln_idu 포락선의 독립 계산: hi = on_mask 점 ln(ID·L/w_m) 최대, lo = (L, VDS, VS) 곡선마다 gm/ID 최대 VGS 점(그
    점이 on_mask 인 곡선만)의 ln IDu 중 최소."""
    ID, GM = a["ID"], a["GM"]
    Ls = np.asarray(a["L"], dtype=float)
    m = on_mask(a)
    lnu = np.full(ID.shape, -np.inf)
    lnu[m] = np.log(ID[m] * np.broadcast_to(Ls[:, None, None, None], ID.shape)[m] / w_m)
    hi = float(lnu[m].max())
    lo = math.inf
    nL, nG, nD, nS = ID.shape
    for i in range(nL):
        for k in range(nD):
            for s in range(nS):
                with np.errstate(divide="ignore", invalid="ignore"):
                    g = GM[i, :, k, s] / ID[i, :, k, s]
                g = np.where(np.isfinite(g), g, -np.inf)
                j = int(np.argmax(g))
                if m[i, j, k, s]:
                    lo = min(lo, float(lnu[i, j, k, s]))
    return lo, hi


def circuit_z():
    """회로 Z: 회로 C + Rz (out, x) + Cz (x, gnd), 둘 다 spec engine. DC 전류 0 저항(가지치기) + 커패시터 -> sizing r5
    θ `ss_resistance` Rz(영점 상쇄 구조 규칙이 정하지 못하는 망 -- sizing 10.3 toy 와 같은 모양)·`capacitance` Cz."""
    d = circuit_cs_pmos_load()
    d["passive_elements"] = [two("Rz", "resistor", "out", "x"), two("Cz", "capacitor", "x", "gnd")]
    return d


Z_ELEMENTS = (("Rz", "resistor", None), ("Cz", "capacitor", None))


def theta_z(dc, cz=1e-12, rz=1e4, **kw):
    """회로 Z 의 θ: 회로 C 의 θ + 수동소자 θ. y 키는 스키마(입력)에서 읽는다(W4 뿌리 이름)."""
    th = dict(theta_r4c(**kw))
    y = th.pop(("y", "out"))
    ykeys = [k for k in schema_of(dc).components if k[0] == "y"]
    assert len(ykeys) == 1
    th[ykeys[0]] = y
    th[("capacitance", "Cz")] = cz
    th[("ss_resistance", "Rz")] = rz
    assert set(th) == set(schema_of(dc).components), (sorted(th), schema_of(dc).components)
    return th


CELLS_C = (0, 1)        # 회로 C: M1 L = 1e-6 -> 칸 0, M2 L = 2e-6 -> 칸 1 (l_cells 는 L 앵커 오름차순, 이름순 MOS)
CELLS_P = (0,)


def peak_floor(a, lo, hi, w_m=None):
    """[r8] 3.22 칸 정점 하한의 독립 계산(npz 배열 a, 칸 [lo, hi]): 칸 안 L 앵커(± spacing) × VDS·VS 전 격자 곡선마다 GM/ID 최대 VGS
    마디(비유한 -> −inf), 그 마디가 on_mask 인 곡선만 lnID + ln L − ln w_m, 그 최댓값. w_m = 슬라이스 폭(기본 a["W"])."""
    w_m = float(a["W"]) if w_m is None else w_m
    Ls = np.asarray(a["L"], dtype=float)
    ID, GM = np.asarray(a["ID"], dtype=float), np.asarray(a["GM"], dtype=float)
    m = on_mask({"ID": ID, "GM": GM})
    best = -math.inf
    for i, L in enumerate(Ls):
        if not (lo - np.spacing(lo) <= L <= hi + np.spacing(hi)):
            continue
        for k in range(ID.shape[2]):
            for s in range(ID.shape[3]):
                with np.errstate(divide="ignore", invalid="ignore"):
                    g = GM[i, :, k, s] / ID[i, :, k, s]
                g = np.where(np.isfinite(g), g, -np.inf)
                j = int(np.argmax(g))
                if m[i, j, k, s]:
                    best = max(best, math.log(ID[i, j, k, s]) + math.log(L) - math.log(w_m))
    return best


def tol_v_at(lut, kind, w_key):
    """[r9] 3.22 전도 하한의 입력 tol = lut `tol_v_table(memo, kind, w_key).at(L_a, VDS_k, "id_equivalent")` -- lut 계약·lut test 소관의
    공개 API 를 입력으로만 쓴다(피검 search 함수 아님). 새 memo 하나(피검 sctx 캐시와 무관)."""
    from gmid_engine.lut import LutMemo, tol_v_table
    table = tol_v_table(LutMemo(lut, point=4096, curve=4096, root=4096), kind, w_key)
    return lambda L, vds: table.at(L, vds, "id_equivalent")


def conduction_floor(a, lo, hi, tol_at, w_m=None):
    """[r9] 3.22 칸 전도 하한의 독립 계산(npz 배열 a, 칸 [lo, hi], tol_at(L, VDS) -> tol 또는 None). 계약 문장 그대로:
    칸 안 L 앵커 a(± spacing) × VDS k × VS s 곡선마다 -- tol None·0 이면 (a, k) 곡선 제외, VGS 0 마디 z(|VGS| ≤ spacing(max|VGS|),
    없으면 None)가 on_mask 인 곡선만 -- f_i = ln GM[a, i, k, s] + ln tol − ln ID[a, z, k, s]; on_mask 이고 f ≥ 0 인 첫 마디 j 가
    있고 j > 0 이고 j − 1 도 on_mask 이면 근 = lnID[j−1] + t·(lnID[j] − lnID[j−1]) + ln L_a − ln w_m, t = −f[j−1]/(f[j] − f[j−1]).
    결과 = 근의 최댓값(곡선이 없으면 None). 봉인 9 margin = 1 ⇔ f = 0(sizing r8) 이 근거라 f 는 그 조건을 격자에서 다시 쓴 것."""
    w_m = float(a["W"]) if w_m is None else w_m
    Ls = np.asarray(a["L"], dtype=float)
    vgs = np.asarray(a["VGS"], dtype=float)
    vds = np.asarray(a["VDS"], dtype=float)
    ID, GM = np.asarray(a["ID"], dtype=float), np.asarray(a["GM"], dtype=float)
    zs = [i for i, v in enumerate(vgs) if abs(v) <= np.spacing(float(np.max(np.abs(vgs))))]
    if not zs:
        return None
    z = zs[0]
    m = on_mask({"ID": ID, "GM": GM})
    best = None
    for i, L in enumerate(Ls):
        if not (lo - np.spacing(lo) <= L <= hi + np.spacing(hi)):
            continue
        for k in range(ID.shape[2]):
            tol = tol_at(float(L), float(vds[k]))
            if tol is None or tol == 0:
                continue
            for s in range(ID.shape[3]):
                if not m[i, z, k, s]:
                    continue
                with np.errstate(divide="ignore", invalid="ignore"):
                    f = np.log(GM[i, :, k, s]) + math.log(tol) - math.log(ID[i, z, k, s])
                    lnid = np.log(ID[i, :, k, s])
                js = [j for j in range(ID.shape[1]) if m[i, j, k, s] and f[j] >= 0]
                if not js:
                    continue
                j = js[0]
                if j == 0 or not m[i, j - 1, k, s]:
                    continue
                t = -f[j - 1] / (f[j] - f[j - 1])
                root = float(lnid[j - 1] + t * (lnid[j] - lnid[j - 1]) + math.log(L) - math.log(w_m))
                best = root if best is None else max(best, root)
    return best


def expected_floor(cond, peak):
    """[r9] 3.22 성분별 하한 = max(칸 전도 하한(None 아니면), 칸 정점 하한(적용될 때 -- 아니면 None)), 둘 다 없으면 None."""
    vals = [x for x in (cond, peak) if x is not None and x != -math.inf]
    return max(vals) if vals else None


def circuit_diode():
    """[r8] M1 nmos diode (out, out, gnd) + M2 pmos (out, in, vdd). out = M1 vgs_gate(known gnd) 이고 M1 의 drain -> 1변수 노드
    (3.22 one_var_only = {M1}). in = M2 vgs_gate(known vdd), in 은 M2 의 gate -> 1변수 아님."""
    return topo("hand_diode", [mos("M1", "nmos", "out", "out", "gnd"), mos("M2", "pmos", "out", "in", "vdd")],
                {"in": ("input", "single_ended_input"), "out": ("output", "single_ended_output")})


PENDING = "pending"     # elements 값 자리 표지: spec 에 {"pending": "SP-1"} (값 없음·engine 아님 -> 수동소자 값 미선언)


def load_spec(tmp, topo_doc, elements=(), constraints=(), measurement_loads=()):
    """metrics conftest `spec_json` 으로 spec 을 만들고 PENDING 원소만 결정 대기 표지로 바꿔 authoring 로더로 읽는다.
    [결정 11] measurement_loads = 그 원소 항목에 `"measurement_load": true` 를 적는다(SPEC_CONTRACT 측정 부하 표지)."""
    from gmid_engine.authoring import load_sizing_spec, load_topology
    from gmid_engine.metrics import metric_catalog
    tmp = Path(tmp)
    tmp.mkdir(parents=True, exist_ok=True)
    tp = tmp / (topo_doc["topology_name"] + ".topology.json")
    tp.write_text(json.dumps(topo_doc, indent=1), encoding="utf-8")
    td = load_topology(str(tp))
    els = [(n, k, None if v == PENDING else v) for n, k, v in elements]
    doc = spec_json(td, SUPPLIES, els, (), constraints)
    for n, _, v in elements:
        if v == PENDING:
            doc["human"]["element_values"][n] = {"pending": "SP-1"}
    for n in measurement_loads:
        doc["human"]["element_values"][n]["measurement_load"] = True
    sp = tmp / (topo_doc["topology_name"] + ".sizing_spec.json")
    sp.write_text(json.dumps(doc, indent=1), encoding="utf-8")
    return td, load_sizing_spec(str(sp), td, metric_catalog())


def build_case(tmp, topo_doc, lut, constraints=(), elements=(), budget_s=600.0, eval_budget=40, rbounds=None,
               archive_root=None, pdk=None, sources=SRC, cbounds=None, rule=None, measurement_loads=()):
    """topology·spec -> KernelContext -> SearchContext([r6] PDK 선언 + LUT 규칙 선언).
    반환 SimpleNamespace(td, spec, dc, acc, pdk, rule, settings, sctx)."""
    from gmid_engine.graph import build_s1
    from gmid_engine.search import SearchSettings, build_search_context
    from gmid_engine.sizing import build_kernel_context, dc_inputs_from_spec
    tmp = Path(tmp)
    acc = new_access(lut)
    td, spec = load_spec(tmp / "case", topo_doc, elements=elements, constraints=constraints,
                         measurement_loads=measurement_loads)
    inputs = dc_inputs_from_spec(spec)
    s1 = build_s1(td, dict(inputs.supplies_v))
    dc = build_kernel_context(s1, inputs, acc)
    if pdk is None or rule is None:
        p2, r2 = write_decls(tmp / "pdk")
        pdk = p2 if pdk is None else pdk
        rule = r2 if rule is None else rule
    settings = SearchSettings(budget_s, eval_budget, rbounds, tuple(sources), cbounds)
    sctx = build_search_context(dc, spec, settings, archive_root, pdk, rule, code_fp=CODE_FP)
    return SimpleNamespace(td=td, spec=spec, dc=dc, acc=acc, pdk=pdk, rule=rule, settings=settings, sctx=sctx)


# ---------------------------------------------------------------- 스냅샷 읽기 (입력 열)

def col(snap, kind, field):
    return dict(snap.column(kind, field))


def with_passive_value(snap, pairs):
    """[U17 ①] 손 수동소자 값을 S2 필드 `device.passive_value`(설계 40 §2.4.8, writer = 권한표 writer_of)로 쓴 스냅샷 --
    metrics_dc 는 이 필드를 읽는다(사본 extras 없음). 블록 입력 버전은 읽는 열 값의 지문이라 version 표지는 임의."""
    from gmid_engine.sizing import S2_WRITERS
    pairs = tuple(sorted(pairs))
    return snap.write(S2_WRITERS.writer_of("device", "passive_value"), "hand_pv:%r" % (pairs,),
                      {("device", "passive_value"): {n: float(v) for n, v in pairs}})


def node_v(snap):
    v = col(snap, "node", "dc_rail_v")
    v.update(col(snap, "node", "dc_v"))
    return v


def snap_of(result):
    """EvalResult.evaluation -> 봉인/대기 DcEvaluation 의 스냅샷."""
    return result.evaluation.snapshot


def to_theta_fn(variables, fixed):
    """x(로그 변수는 ln) -> θ dict. fixed = 변수 밖 성분 dict(L 등)."""
    def f(x):
        th = dict(fixed)
        for v, xv in zip(variables, x):
            th[v.component] = math.exp(xv) if v.log else xv
        return th
    return f


def x_of(variables, theta):
    th = dict(theta)
    return tuple(math.log(th[v.component]) if v.log else th[v.component] for v in variables)


def fixed_l(theta):
    return {k: v for k, v in dict(theta).items() if k[0] == "L"}


def expected_fd_steps(sctx, base, vgs_grid=R4_VGS, vds_grid=R4_VDS):
    """3.11 스텝 식의 독립 계산(base 스냅샷 입력 열 + LUT 격자). -> [h | None] (sctx.domain.variables 순서, 부호 전)."""
    import bisect
    snap = snap_of(base)
    ops = col(snap, "device", "dc_op")
    tol = col(snap, "device", "dc_tol_v")
    writers = col(snap, "node", "dc_writer")
    windows = col(snap, "node", "dc_window")
    drop = col(snap, "device", "dc_drop_current")
    th = dict(base.theta)
    cone = dict(schema_of(sctx.dc).current_cone)
    out = []
    for v in sctx.domain.variables:
        t, key = v.component
        if t == "ln_idu":
            op = ops[key]
            g = list(vgs_grid)
            i = min(max(bisect.bisect_right(g, op.vgs) - 1, 0), len(g) - 2)
            out.append((g[i + 1] - g[i]) * op.gm_id)
        elif t == "y":
            node = [n for n, w in writers.items() if w.y_key == key and n in windows][0]
            w = windows.get(node)
            d = min(b - a for a, b in zip(vds_grid, vds_grid[1:]))
            out.append(None if w is None or w.hi - w.lo == 0 else d / (w.hi - w.lo))
        elif t == "current":
            ms = [m for m, terms in cone.items() if any(tt.source == key for tt in terms) and tol.get(m) is not None]
            if not ms:
                ms = [m for m in ops if tol.get(m) is not None]
            out.append(min(tol[m] * ops[m].gm_id for m in ms) if ms else None)
        elif t in ("capacitance", "ss_resistance"):         # [r6] DEC-92 θ: 전 MOS dc_tol_v·gm_id 최솟값
            out.append(min(tol[m] * ops[m].gm_id for m in ops if tol.get(m) is not None))
        elif t == "resistance":
            tmin = min(x for x in tol.values() if x is not None)
            i = abs(drop[key])
            out.append(0.0 if i == 0 else tmin / (i * th[("resistance", key)]))
        else:
            raise AssertionError(v)
    return out


# ---------------------------------------------------------------- 독립 비지배 필터 (계약 3.1 문장 그대로)

def ref_nondominated(points, ties):
    """points = ((id, (축...), slack), ...), ties = 축마다 폭 또는 width(id_p, id_q). -> (kept, folded, dominated) index."""
    def w(ax, p, q):
        t = ties[ax]
        return t(p[0], q[0]) if callable(t) else t

    def rel(p, q):
        better = worse = 0
        for ax, (a, b) in enumerate(zip(p[1], q[1])):
            wd = w(ax, p, q)
            if abs(a - b) <= wd:
                continue
            if a < b - wd:
                better += 1
            else:
                worse += 1
        return better, worse

    order = sorted(range(len(points)), key=lambda i: (points[i][1][0], -points[i][2], points[i][0]))
    kept, folded, dominated = [], [], []
    for i in order:
        p = points[i]
        fold_to = dom_by = None
        for k in kept:
            b, wo = rel(p, points[k])
            if b == 0 and wo == 0:
                fold_to = k
                break
            if b == 0 and wo >= 1 and dom_by is None:
                dom_by = k
        if fold_to is not None:
            folded.append((i, fold_to))
            continue
        if dom_by is not None:
            dominated.append((i, dom_by))
            continue
        for k in list(kept):
            b, wo = rel(p, points[k])
            if wo == 0 and b >= 1:
                kept.remove(k)
                dominated.append((k, i))
        kept.append(i)
    pos = {i: n for n, i in enumerate(order)}
    return tuple(sorted(kept, key=pos.get)), tuple(sorted(folded)), tuple(sorted(dominated))


def dominates(p, q, wp, wa):
    """p, q = (power, area). 폭 wp·wa 로 p 가 q 를 지배."""
    better = worse = 0
    for a, b, wd in ((p[0], q[0], wp), (p[1], q[1], wa)):
        if abs(a - b) <= wd:
            continue
        if a < b - wd:
            better += 1
        else:
            worse += 1
    return worse == 0 and better >= 1


def all_tied(p, q, wp, wa):
    return abs(p[0] - q[0]) <= wp and abs(p[1] - q[1]) <= wa


# ---------------------------------------------------------------- ε 격자 (계약 3.15 문장 그대로)

def ref_eps_count(lo, hi, gap):
    """열린 구간 (lo, hi) 안의 hi − k·gap (k ≥ 1) 점 수."""
    if not hi > lo or gap <= 0:
        return 0
    n = 0
    k = 1
    while hi - k * gap > lo:
        n += 1
        k += 1
    return n


def ref_eps_values(lo, hi, gap):
    out = []
    k = 1
    while hi - k * gap > lo:
        out.append(hi - k * gap)
        k += 1
    return out


# ---------------------------------------------------------------- 스냅샷 -> 기대 목적·제약 (3.6·3.8 독립 계산)

def _dc_key():
    from gmid_engine.sizing import DC_KEY
    return DC_KEY


def expected_objectives(snap):
    basis = snap.value("graph", _dc_key(), "dc_current_basis")
    rails = col(snap, "node", "dc_rail_v")
    cur = col(snap, "device", "dc_current")
    cur_in = {k: 0.0 for k in rails}
    for el, a, b in basis.ends:
        if el not in cur:
            continue
        if a in cur_in:
            cur_in[a] += cur[el]
        if b in cur_in:
            cur_in[b] -= cur[el]
    ops = col(snap, "device", "dc_op")
    tol = col(snap, "device", "dc_tol_v")
    bp = 0.0
    rows = False
    for k, v in rails.items():
        cands = [tol[el] * ops[el].current * ops[el].gm_id for el, a, b in basis.ends
                 if el in ops and k in (a, b) and tol.get(el) is not None]
        if cands:
            rows = True
            bp += abs(v) * max(cands)
    return {
        "power": sum(rails[k] * cur_in[k] for k in rails),
        # [r12] metrics CONTRACT 7.x: 레일 나열 순서 = (dc_colour, 이름)(종래 이름순) -- 색은 스냅샷 입력 열
        "per_rail": tuple(sorted(cur_in.items(), key=lambda kv: (col(snap, "node", "dc_colour").get(kv[0], -1), kv[0]))),
        "kcl": sum(cur_in.values()),
        "gate_area": sum(o.W * o.L for o in ops.values()),
        "bp": bp if rows and bp != 0 else None,
    }


def expected_rows(snap, w_min, grid):
    ops = col(snap, "device", "dc_op")
    tol = col(snap, "device", "dc_tol_v")
    coord = col(snap, "device", "dc_coord")
    rows, undefined = [], []
    for m in [k for k, _ in snap.column("device", "dc_op")]:
        op = ops[m]
        rows.append(("w_min:%s" % m, (op.W - w_min) / grid))
        t = tol.get(m)
        if t is None or t <= 0:
            undefined.append(m)
            continue
        rows.append(("seal6_bulk:%s" % m, (min(op.vsb, op.vds + op.vsb) + t) / t))
        if coord[m].role == "writer":
            r_peak = math.log(I0[op.kind]) + LAM * op.vds + r4_vs_term(op.vsb)
            rows.append(("inversion_floor:%s" % m, (op.ln_idu - r_peak) * op.gm_id / t))
    return rows, sorted(undefined)


# ---------------------------------------------------------------- I-8 결정론 탐침 (subprocess 에서 부른다)

def front_signature(fr):
    """SearchFront -> 비교용 JSON 가능 값(점 id·θ hex·목적 hex)."""
    def pts(seq):
        return [[p.point_id, [float(v).hex() for _, v in p.result.theta],
                 float(p.result.objectives.power_w).hex(), float(p.result.objectives.area_m2).hex()] for p in seq]
    return {"front": pts(fr.front), "pending": pts(fr.pending_front), "unmeasured": pts(fr.unmeasured_front)}


def determinism_probe(tmpdir, eval_budget=40):
    """회로 C + VDSAT toy LUT, 선언 E_B 로 find_front 한 번 -> JSON 문자열(front 서명·kernel·run_id·벽시계 정지)."""
    from gmid_engine.search import find_front
    tmp = Path(tmpdir)
    lut = write_r4_lut(tmp / "lut")
    case = build_case(tmp, circuit_c(), lut, constraints=(("gain_ss_db", ">=", 10.0, None),),
                      eval_budget=eval_budget, budget_s=600.0)
    fr = find_front(case.sctx, [theta_r4c()])
    perf = dict(fr.perf)
    out = front_signature(fr)
    out.update(kernel=perf["kernel_calls"], run_id=fr.run_id, wall=perf["stops_wall_budget"])
    return json.dumps(out, sort_keys=True)
