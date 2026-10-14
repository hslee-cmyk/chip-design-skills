"""CONTRACT 3.22 [r11, 사용자 결정 11, 2026-10-08] `passive_area_decl(dc_ctx, spec, pdk_decl) -> PassiveAreaDecl` (`area_decl.py`)
+ 면적 축 area_search_m2 의 수동소자 항(metrics CONTRACT 7.5 `area_decl`) + core 9.4 `mim_cap_density_f_per_m2`.

oracle:
- (a) 구성으로 정해진 합성 입력: toy PDK 의 MIM 단위 면적 용량(conftest `TOY_MIM_DENSITY` = 4e-3 F/m², 이 test 가 고른 값)과 spec 에 적은
  커패시터 값 -> 커패시터 면적 = 값 / 밀도. MOS 면적 Σ W·L 은 결과 스냅샷 입력 열 dc_op 에서 이 test 가 더한다(conftest
  `expected_objectives`). 측정 부하(measurement_load) 표지 유무만 다른 두 spec 의 면적 차 = 그 부하 값 / 밀도.
- (d) 사용자 결정 11 / core CONTRACT 9.4 표 값 2.0e-3 F/m², 그리고 PDK 원본 파일 줄을 이 test 가 직접 파싱한 값(피검 read_pdk_decl 아님).
- 저항: PDK 선언에 poly 저항 양(`poly_res_*`, core 9.7 resistor_types)이 없으면 면적에 넣지 않고 `passive_area_undeclared` 로 보고(3.22).
  [U3] 사용자 결정 Q9(설계 40 §7.1)가 구현돼 그 양이 있으면 본체 W_min²/R□·값 + 머리 면적이 들어간다 -- 파일 끝 '[U3] 저항 면적' 절.
"""
import hashlib
import math
import os
import re
from pathlib import Path

import pytest

from gmid_engine.core import BoundedLRU, read_pdk_decl
from gmid_engine.metrics import PassiveAreaDecl
from gmid_engine.search import STATUS_PENDING_SEAL7, STATUS_SEALED, evaluate

from .conftest import area_decl_of  # [U17 ①-b] graph/kernel: passive_area_decl 필드 읽기
from .conftest import (
    CELLS_C,
    TOY_MIM_DENSITY,
    Z_ELEMENTS,
    build_case,
    circuit_z,
    expected_objectives,
    snap_of,
    theta_z,
    two,
    write_decls,
    write_decls_mim,
)

SKILL_DIR = Path(__file__).resolve().parents[3]
CL_F = 1e-12                    # 측정 부하 값(구성 입력)
CZ_F = 2e-12                    # θ 커패시터 값(구성 입력)
RB, CB = (1e2, 1e6), (1e-14, 1e-10)


def circuit_zl():
    """회로 ZL: 회로 Z(M1·M2 + engine Rz·Cz) + 값 있는 부하 CL (out, gnd)."""
    d = circuit_z()
    d["passive_elements"] = list(d["passive_elements"]) + [two("CL", "capacitor", "out", "gnd")]
    return d


ZL_ELEMENTS = Z_ELEMENTS + (("CL", "capacitor", CL_F),)


def _case(tmp, lut, pdk_rule=None, ml=()):
    pdk, rule = pdk_rule if pdk_rule is not None else write_decls_mim(Path(tmp) / "pdk_mim")
    return build_case(tmp, circuit_zl(), lut, elements=ZL_ELEMENTS, rbounds=RB, cbounds=CB, pdk=pdk, rule=rule,
                      measurement_loads=ml)


def _eval(case):
    return evaluate(case.sctx, tuple(sorted(theta_z(case.dc, cz=CZ_F).items())), CELLS_C)


# ---------------------------------------------------------------- passive_area_decl 결과 (3.22)

def test_unit_area_is_inverse_density_for_capacitors_only(tmp_path, lut_sealed):
    """측정 부하 없음: unit_area = 회로 안 커패시터 전부(CL·Cz)에 1/밀도, 저항 Rz 는 없음(미선언), excluded 없음."""
    case = _case(tmp_path, lut_sealed)
    d = area_decl_of(case.dc, case.spec, case.pdk)
    assert isinstance(d, PassiveAreaDecl)
    assert [n for n, _ in d.unit_area] == ["CL", "Cz"]
    for _, u in d.unit_area:
        assert u == pytest.approx(1.0 / TOY_MIM_DENSITY, rel=1e-12)
    assert tuple(d.excluded) == ()
    assert case.sctx.area_decl == d                       # build_search_context 가 같은 선언을 싣는다


def test_measurement_load_goes_to_excluded(tmp_path, lut_sealed):
    """spec measurement_load CL -> excluded = (CL,), unit_area 에서 빠진다(이름이 아니라 선언이 정한다)."""
    case = _case(tmp_path, lut_sealed, ml=("CL",))
    d = area_decl_of(case.dc, case.spec, case.pdk)
    assert tuple(d.excluded) == ("CL",)
    assert [n for n, _ in d.unit_area] == ["Cz"]
    assert d.unit_area[0][1] == pytest.approx(1.0 / TOY_MIM_DENSITY, rel=1e-12)


def test_measurement_load_on_theta_capacitor_also_excluded(tmp_path, lut_sealed):
    """표지는 이름·값 출처와 무관: engine(θ) 커패시터 Cz 에 표지를 달아도 excluded (측정 부하 선언이 정한다)."""
    case = _case(tmp_path, lut_sealed, ml=("Cz",))
    d = area_decl_of(case.dc, case.spec, case.pdk)
    assert tuple(d.excluded) == ("Cz",)
    assert [n for n, _ in d.unit_area] == ["CL"]


def test_pdk_without_mim_quantity_reports_capacitors_undeclared(tmp_path, lut_sealed):
    """PDK 선언에 mim_cap_density_f_per_m2 가 없으면 거부가 아니라 커패시터도 미선언(unit_area 빈 tuple), 제외는 그대로."""
    case = _case(tmp_path, lut_sealed, pdk_rule=write_decls(tmp_path / "pdk_plain"), ml=("CL",))
    d = area_decl_of(case.dc, case.spec, case.pdk)
    assert (tuple(d.unit_area), tuple(d.excluded)) == ((), ("CL",))
    r = _eval(case)
    assert r.status == STATUS_SEALED
    e = expected_objectives(snap_of(r))
    assert r.objectives.area_m2 == pytest.approx(e["gate_area"], rel=1e-12)
    assert tuple(r.objectives.passive_area_undeclared) == ("Cz", "Rz")


# ---------------------------------------------------------------- 면적 축 값 (evaluate 경로, 3.22 + metrics 7.5)

def test_area_equals_gate_area_plus_capacitance_over_density(tmp_path, lut_sealed):
    """area_search_m2 = Σ W·L(스냅샷 dc_op) + (CL + Cz)/밀도, 저항 Rz 는 미선언 보고. gate_area_m2 = Σ W·L."""
    case = _case(tmp_path, lut_sealed)
    r = _eval(case)
    assert r.status == STATUS_SEALED
    e = expected_objectives(snap_of(r))
    want = e["gate_area"] + (CL_F + CZ_F) / TOY_MIM_DENSITY
    assert r.objectives.area_m2 == pytest.approx(want, rel=1e-12)
    assert r.objectives.gate_area_m2 == pytest.approx(e["gate_area"], rel=1e-12)
    assert tuple(r.objectives.passive_area_undeclared) == ("Rz",)


def test_measurement_load_does_not_affect_area(tmp_path, lut_sealed):
    """측정 부하 CL 표지: 면적 = Σ W·L + Cz/밀도(CL 항 없음, 미선언 목록에도 없음). 표지 없는 같은 회로·같은 θ 와의 차 = CL/밀도,
    MOS 면적·전력은 같다(측정 부하 선언은 면적만 바꾼다)."""
    plain = _case(tmp_path / "plain", lut_sealed)
    ml = _case(tmp_path / "ml", lut_sealed, ml=("CL",))
    r0, r1 = _eval(plain), _eval(ml)
    assert r0.status == r1.status == STATUS_SEALED
    e1 = expected_objectives(snap_of(r1))
    assert r1.objectives.area_m2 == pytest.approx(e1["gate_area"] + CZ_F / TOY_MIM_DENSITY, rel=1e-12)
    assert tuple(r1.objectives.passive_area_undeclared) == ("Rz",)
    assert r1.objectives.gate_area_m2 == r0.objectives.gate_area_m2
    assert r1.objectives.power_w == r0.objectives.power_w
    assert r0.objectives.area_m2 - r1.objectives.area_m2 == pytest.approx(CL_F / TOY_MIM_DENSITY, rel=1e-9)


def test_cl_value_change_moves_area_only_without_measurement_load(tmp_path, lut_sealed):
    """측정 부하로 표시한 CL 은 값이 10 배가 되어도 면적이 그대로, 표지가 없으면 면적이 (10−1)·CL/밀도 만큼 는다."""
    def run(sub, cl, ml):
        pdk, rule = write_decls_mim(tmp_path / sub / "pdk")
        case = build_case(tmp_path / sub, circuit_zl(), lut_sealed, elements=Z_ELEMENTS + (("CL", "capacitor", cl),),
                          rbounds=RB, cbounds=CB, pdk=pdk, rule=rule, measurement_loads=ml)
        return _eval(case).objectives.area_m2
    assert run("a", CL_F, ("CL",)) == run("b", 10 * CL_F, ("CL",))
    assert run("d", 10 * CL_F, ()) - run("c", CL_F, ()) == pytest.approx(9 * CL_F / TOY_MIM_DENSITY, rel=1e-9)


def test_pending_point_same_area_rule(tmp_path, lut_sealed, lut_pending):
    """3.22: area_decl 은 봉인 점(ss_evaluate)과 그 밖 점(metrics_dc) 둘 다에 들어간다 -- 봉인 7 대기 점도 같은 면적 규칙
    (Σ W·L + Cz/밀도, CL 제외, Rz 미선언)."""
    case = _case(tmp_path, lut_pending, ml=("CL",))
    r = _eval(case)
    assert r.status == STATUS_PENDING_SEAL7, r.status
    e = expected_objectives(snap_of(r))
    assert r.objectives.area_m2 == pytest.approx(e["gate_area"] + CZ_F / TOY_MIM_DENSITY, rel=1e-12)
    assert tuple(r.objectives.passive_area_undeclared) == ("Rz",)


def test_area_constraint_row_uses_full_area(tmp_path, lut_sealed):
    """예산 행 spec:area_search_m2<= 의 c = (A − 면적)/b_A 이고 면적은 수동 커패시터 항을 포함한 area_search_m2 다(3.22)."""
    pdk, rule = write_decls_mim(tmp_path / "pdk")
    A = 1e-9
    case = build_case(tmp_path, circuit_zl(), lut_sealed, elements=ZL_ELEMENTS, rbounds=RB, cbounds=CB, pdk=pdk, rule=rule,
                      measurement_loads=("CL",), constraints=(("area_search_m2", "<=", A, None),))
    r = _eval(case)
    e = expected_objectives(snap_of(r))
    area = e["gate_area"] + CZ_F / TOY_MIM_DENSITY
    (row,) = [x for x in r.constraints if x.name == "spec:area_search_m2<="]
    assert row.c == pytest.approx((A - area) / case.sctx.domain.area_resolution_m2, rel=1e-9)


# ---------------------------------------------------------------- sky130 선언값 (core 9.4, 사용자 결정 11)

_PDK_DECL = SKILL_DIR / "assets" / "sky130_pdk_decl.json"
_RC_FILE = "C:/pdk/sky130_fd_pr/models/r+c/res_typical__cap_typical__lin.spice"


@pytest.mark.skipif(not os.path.isfile(_RC_FILE), reason="sky130 r+c 원본 없음")
def test_sky130_mim_density_read_from_pdk_file():
    """선언값 = 원본 파일의 `+ camimc= 2.00e-15  $ Units: farad/micrometer^2` 줄을 이 test 가 직접 파싱해 µm² -> m²(1e12) 로 바꾼 값
    = 2.0e-3 F/m²(core CONTRACT 9.4 표, 공개 문서 ~2 fF/µm²). 줄은 파일에 정확히 한 번."""
    text = Path(_RC_FILE).read_text(encoding="utf-8")
    hits = [ln for ln in text.splitlines() if re.match(r"^\+\s*camimc\s*=", ln, re.IGNORECASE)]
    assert len(hits) == 1
    m = re.match(r"^\+\s*camimc\s*=\s*([0-9.eE+-]+)\s*\$\s*Units:\s*farad/micrometer\^2", hits[0])
    assert m, hits[0]
    parsed = float(m.group(1)) * 1e12          # F/µm² x (1e6 µm/m)² -- 단위 정의
    assert parsed == pytest.approx(2.0e-3, rel=1e-12)
    decl = read_pdk_decl(str(_PDK_DECL), BoundedLRU(8))
    assert decl.value("mim_cap_density_f_per_m2") == pytest.approx(parsed, rel=1e-12)
    q = decl.quantity("mim_cap_density_f_per_m2")
    assert q.expression == "camimc"
    (rule,) = q.rules
    # [U17 ①-b 3차, 결정 7] 출처 파일 = 경로 대신 내용: 규칙의 원본 이름이 선언에서 이 r+c 파일을 가리키는 항목이고, 규칙 sha256 =
    # 이 test 가 _RC_FILE 바이트를 직접 해시한 값(같은 파일이 아니면 다르다). 원본 이름 'mim_cap_params' 는 선언 파일 sources 키.
    rc_sha = hashlib.sha256(Path(_RC_FILE).read_bytes()).hexdigest()
    assert rule.source == "mim_cap_params"
    assert rule.sha256 == rc_sha
    assert dict(decl.sources)["mim_cap_params"] == rc_sha
    lines = text.splitlines()
    assert rule.line >= 1 and re.match(r"^\+\s*camimc\s*=", lines[rule.line - 1])
    assert math.isfinite(decl.value("mim_cap_density_f_per_m2"))


# ---------------------------------------------------------------- [U3] 저항 면적 (설계 40 §7.1 결정 Q9, core 9.7 resistor_types)
#   oracle (a) 구성: toy PDK 저항 원본(이 test 가 쓴 R□ = 50 Ω/□, W_min = 0.4 µm, 머리 1e-12 m²) -> Ω당 면적 = W_min²/R□ = 3.2e-15 m²/Ω
#   (40 §7.1 '단위 면적 유도: R·W_R²/R□ + 머리'), 저항마다 머리 한 번. 측정 부하 저항은 면적에서 뺀다.

TOY_R_SHEET = 50.0
TOY_R_WMIN = 4e-7
TOY_R_HEAD = 1e-12
RZ_OHM = 1e4                    # theta_z 기본 rz (구성 입력)


def write_decls_mim_res(root):
    """write_decls_mim + 원본 `toy_res`(`+ rsh=50`, `+ wmin=4e-7`, `+ head=1e-12`)와 resistor_types 후보 하나."""
    import hashlib
    import json
    from gmid_engine.core import BoundedLRU
    from .conftest import TOY_CAMIMC_F_PER_UM2, _decl_paths
    pp, rp = _decl_paths(root)
    root = Path(root)
    rc = root / "toy_rc.spice"                                   # write_decls_mim 과 같은 MIM 원본(구성 입력)
    rc.write_text("* toy r+c\n.param\n+ camimc=  %s  $ Units: farad/micrometer^2\n" % TOY_CAMIMC_F_PER_UM2,
                  encoding="utf-8")
    res = root / "toy_res.spice"
    res.write_text("* toy poly resistor\n.param\n+ rsh=%r\n+ wmin=%r\n+ head=%r\n" % (TOY_R_SHEET, TOY_R_WMIN, TOY_R_HEAD),
                   encoding="utf-8")
    decl = json.loads(Path(pp).read_text(encoding="utf-8"))
    decl["sources"]["toy_rc"] = {"path": "toy_rc.spice", "sha256": hashlib.sha256(rc.read_bytes()).hexdigest(),
                                 "format": "spice_instance_line", "encoding": "utf-8",
                                 "line_pattern": r"^\+\s*(camimc\s*=\s*[^\s$]+)", "units_m": {"": 1e12}}
    decl["quantities"]["mim_cap_density_f_per_m2"] = {"source": "toy_rc", "expression": "camimc", "basis": "toy MIM"}
    decl["sources"]["toy_res"] = {"path": "toy_res.spice", "sha256": hashlib.sha256(res.read_bytes()).hexdigest(),
                                  "format": "spice_instance_line", "encoding": "utf-8",
                                  "line_pattern": r"^\+\s*(\w+\s*=\s*[^\s$]+)", "units_m": {"": 1.0}}
    for q, e in (("toy_res_sheet", "rsh"), ("toy_res_w", "wmin"), ("toy_res_head", "head")):
        decl["quantities"][q] = {"source": "toy_res", "expression": e, "basis": "toy poly resistor"}
    decl["resistor_types"] = {"selected_as": "poly_res", "candidates": {"toy": {
        "sheet_ohm_per_sq": "toy_res_sheet", "min_w_m": "toy_res_w", "head_area_m2": "toy_res_head"}}}
    Path(pp).write_text(json.dumps(decl), encoding="utf-8")
    memo = BoundedLRU(8)
    return read_pdk_decl(pp, memo), read_pdk_decl(rp, memo)


def test_resistor_unit_area_and_head(tmp_path, lut_sealed):
    case = _case(tmp_path, lut_sealed, pdk_rule=write_decls_mim_res(tmp_path / "pdk_res"))
    d = area_decl_of(case.dc, case.spec, case.pdk)
    unit = dict(d.unit_area)
    assert set(unit) == {"CL", "Cz", "Rz"}
    assert unit["Rz"] == pytest.approx(TOY_R_WMIN ** 2 / TOY_R_SHEET, rel=1e-12)
    assert dict(d.head_area) == {"Rz": pytest.approx(TOY_R_HEAD, rel=1e-12)}


def test_resistor_area_enters_area_axis(tmp_path, lut_sealed):
    """area_search_m2 = Σ W·L + (CL + Cz)/밀도 + Rz·W_min²/R□ + 머리, 미선언 목록 비어 있음."""
    case = _case(tmp_path, lut_sealed, pdk_rule=write_decls_mim_res(tmp_path / "pdk_res"))
    r = _eval(case)
    assert r.status == STATUS_SEALED
    e = expected_objectives(snap_of(r))
    want = e["gate_area"] + (CL_F + CZ_F) / TOY_MIM_DENSITY + RZ_OHM * TOY_R_WMIN ** 2 / TOY_R_SHEET + TOY_R_HEAD
    assert r.objectives.area_m2 == pytest.approx(want, rel=1e-12)
    assert tuple(r.objectives.passive_area_undeclared) == ()


def test_resistor_measurement_load_excluded(tmp_path, lut_sealed):
    """측정 부하 표지 저항은 본체·머리 모두 면적에서 빠진다(40 §7.1 '측정 부하 제외')."""
    case = _case(tmp_path, lut_sealed, pdk_rule=write_decls_mim_res(tmp_path / "pdk_res"), ml=("Rz",))
    d = area_decl_of(case.dc, case.spec, case.pdk)
    assert "Rz" in d.excluded and "Rz" not in dict(d.unit_area) and dict(d.head_area) == {}
    r = _eval(case)
    e = expected_objectives(snap_of(r))
    assert r.objectives.area_m2 == pytest.approx(e["gate_area"] + (CL_F + CZ_F) / TOY_MIM_DENSITY, rel=1e-12)
