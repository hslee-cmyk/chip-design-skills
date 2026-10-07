"""CONTRACT r4 3.6 `objective_values(snapshot) -> Objectives`: 값은 `graph.metrics_dc` MetricBundle 에서, b_P = Σ_레일 |V_k|·tol_I,k
(tol_I,k = 채널 끝이 레일 k 인 MOS 의 dc_tol_v·(current·gm_id) 최댓값), 합 0·행 없음 -> None.

기대값: 스냅샷 입력 열(dc_current_basis·dc_current·dc_rail_v·dc_op·dc_tol_v)로 test 가 KCL·전력·면적·b_P 를 직접 계산한다.
"""

import pytest

from gmid_engine.metrics import metrics_dc
from gmid_engine.search import Objectives, objective_values
from gmid_engine.sizing import size_and_seal

from .conftest import PENDING, build_case, expected_objectives, circuit_c, circuit_n, circuit_p, theta_n, theta_p, theta_r4c


def _check(o, e, passive_area=0.0):
    assert isinstance(o, Objectives)
    assert o.power_w == pytest.approx(e["power"], rel=1e-12)
    assert [k for k, _ in o.per_rail] == [k for k, _ in e["per_rail"]]
    for (_, a), (_, b) in zip(o.per_rail, e["per_rail"]):
        assert a == pytest.approx(b, rel=1e-12, abs=1e-30)
    assert o.kcl_residual_a == pytest.approx(e["kcl"], abs=1e-18)
    assert o.gate_area_m2 == pytest.approx(e["gate_area"], rel=1e-12)
    assert o.area_m2 == pytest.approx(e["gate_area"] + passive_area, rel=1e-12)
    if e["bp"] is None:
        assert o.power_resolution_w is None
    else:
        assert o.power_resolution_w == pytest.approx(e["bp"], rel=1e-12)


def test_circuit_c_two_rails(tmp_path, lut_sealed):
    case = build_case(tmp_path, circuit_c(), lut_sealed)
    ev = size_and_seal(case.dc, theta_r4c(i2=2e-5, y=0.6))
    snap = metrics_dc(ev.snapshot, (), ())
    e = expected_objectives(snap)
    o = objective_values(snap)
    _check(o, e)
    # 손 확인: P = 1.8 V × 20 µA (gnd 0 V), gnd 행 0 기여 -> b_P = 1.8·tol(M2)·gm(M2).
    assert o.power_w == pytest.approx(1.8 * 2e-5, rel=1e-12)
    assert o.passive_area_undeclared == () and o.passive_value_undetermined == ()


def test_resistor_circuit_bp_uses_only_mos_on_rails(tmp_path, lut_sealed):
    """회로 P: vdd 에 M1 채널, gnd 에는 R1 만 -> b_P = 1.8·tol(M1)·gm(M1)."""
    case = build_case(tmp_path, circuit_p(), lut_sealed, elements=(("R1", "resistor", None),),
                      rbounds=(1e3, 1e6))
    th = theta_p(case.dc)
    ev = size_and_seal(case.dc, th)
    snap = metrics_dc(ev.snapshot, (("R1", th[("resistance", "R1")]),), ())
    o = objective_values(snap)
    _check(o, expected_objectives(snap))
    assert o.power_resolution_w is not None and o.power_resolution_w > 0


def test_zero_volt_rail_only_gives_none(tmp_path, lut_sealed):
    """회로 N: 채널이 레일에 닿는 MOS 는 0 V gnd 의 M1 뿐 -> 합 0 -> b_P None."""
    case = build_case(tmp_path, circuit_n(), lut_sealed, elements=(("R1", "resistor", None),),
                      rbounds=(1e3, 1e6))
    th = theta_n(case.dc)
    ev = size_and_seal(case.dc, th)
    snap = metrics_dc(ev.snapshot, (("R1", th[("resistance", "R1")]),), ())
    o = objective_values(snap)
    assert o.power_resolution_w is None
    assert o.power_w == pytest.approx(expected_objectives(snap)["power"], rel=1e-12)


def test_passive_without_value_is_undetermined(tmp_path, lut_sealed):
    case = build_case(tmp_path, circuit_c(with_cap=True), lut_sealed, elements=(("CL", "capacitor", PENDING),))
    ev = size_and_seal(case.dc, theta_r4c())
    o = objective_values(metrics_dc(ev.snapshot, (), ()))
    assert o.passive_value_undetermined == ("CL",)


def test_passive_with_value_but_no_unit_area_is_undeclared(tmp_path, lut_sealed):
    case = build_case(tmp_path, circuit_c(with_cap=True), lut_sealed, elements=(("CL", "capacitor", 1e-12),))
    ev = size_and_seal(case.dc, theta_r4c())
    snap = metrics_dc(ev.snapshot, (("CL", 1e-12),), ())
    o = objective_values(snap)
    assert o.passive_area_undeclared == ("CL",)
    assert o.passive_value_undetermined == ()
    _check(o, expected_objectives(snap))          # 단위 면적 None -> 면적에 수동소자 0 기여


def test_requires_metrics_dc_field(tmp_path, lut_sealed):
    """r4: 값은 metrics_dc 필드에서만 읽는다(다시 계산하지 않는다) -- 필드 없는 스냅샷은 거부."""
    case = build_case(tmp_path, circuit_c(), lut_sealed)
    ev = size_and_seal(case.dc, theta_r4c())
    with pytest.raises((ValueError, KeyError, LookupError)):
        objective_values(ev.snapshot)
