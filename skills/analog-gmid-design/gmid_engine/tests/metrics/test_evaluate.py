"""CONTRACT 3.15·2절·I-2·I-10: metric_value(name, source) -- 항상 MetricResult(name, value, undefined). 미등록 KeyError,
형식 다르면 TypeError. 값 의존 정의 불가는 예외가 아니라 value None + 그 필드의 Undefined."""
import math

import pytest

from gmid_engine.metrics import (
    AreaSearch,
    Capacitor,
    Excitation,
    Factor,
    GateArea,
    MetricResult,
    PassiveArea,
    Resistor,
    Sense,
    SmallSignalCircuit,
    analyze_loop,
    area_search,
    build_mna,
    metric_value,
    output_resistance,
    response_ratio,
    solve_responses,
    supply_currents,
)

from .conftest import closed_miller, closed_single_pole_loop, codes, ex1_rc, ex2_amp, ex2c_beta_cap, ex2d_sc_loop, ex3_miller, ex6_ratio
from .test_supply import _op

R = 1e-9


def test_ex1_values_and_undefined_as_value():
    (r,) = solve_responses((ex1_rc(),))
    la = analyze_loop((Factor(r, 0),))
    g = metric_value("gain_ss_db", la)
    assert isinstance(g, MetricResult) and g.name == "gain_ss_db"
    assert g.value == pytest.approx(0.0, abs=1e-12) and g.undefined == ()
    b = metric_value("gbw_ss_hz", la)
    assert b.value == pytest.approx(159154.943, rel=1e-8)
    for name in ("ugf_ss_hz", "pm_ss_deg", "parasitic_pm_ss_deg"):
        m = metric_value(name, la)
        assert isinstance(m, MetricResult)
        assert m.value is None
        assert "dc_not_above_level" in codes(m.undefined)


def test_ex2_loop_metrics_share_one_analysis():
    gain, ugf, gbw, pm = closed_single_pole_loop(0.25)
    ra, rc = solve_responses((ex2_amp(), ex2c_beta_cap()))
    la = analyze_loop((Factor(ra, 0), Factor(rc, 0)))
    vals = {n: metric_value(n, la).value for n in ("gain_ss_db", "ugf_ss_hz", "gbw_ss_hz", "pm_ss_deg")}
    assert vals["gain_ss_db"] == pytest.approx(gain, rel=R)
    assert vals["ugf_ss_hz"] == pytest.approx(ugf, rel=R)
    assert vals["gbw_ss_hz"] == pytest.approx(gbw, rel=R)
    assert vals["pm_ss_deg"] == pytest.approx(pm, rel=R)
    # I-2: metric 은 같은 LoopAnalysis 의 필드를 그대로 읽는다
    assert vals["ugf_ss_hz"] == la.ugf_hz and vals["pm_ss_deg"] == la.phase_margin_deg


def test_ex2_beta_one_parasitic_pm_equals_pm():
    _, _, _, pm = closed_single_pole_loop(1.0)
    (ra,) = solve_responses((ex2_amp(),))
    la = analyze_loop((Factor(ra, 0),))
    assert metric_value("parasitic_pm_ss_deg", la).value == pytest.approx(90.5729673449, rel=R)
    assert metric_value("pm_ss_deg", la).value == pytest.approx(pm, rel=R)


def test_ex3_miller_metrics():
    ref = closed_miller()
    (r,) = solve_responses((ex3_miller(),))
    la = analyze_loop((Factor(r, 0),))
    assert metric_value("gain_ss_db", la).value == pytest.approx(80.0, rel=R)
    assert metric_value("ugf_ss_hz", la).value == pytest.approx(ref["ugf_hz"], rel=R)
    assert metric_value("gbw_ss_hz", la).value == pytest.approx(ref["gbw_hz"], rel=R)
    assert metric_value("pm_ss_deg", la).value == pytest.approx(ref["pm_deg"], rel=R)


def test_rout_ratio_share_same_dc_solution():
    (ra,) = solve_responses((ex2_amp(),))
    assert metric_value("rout_ss_ohm", output_resistance(ra, 1)).value == pytest.approx(1e5, rel=1e-12)
    (r6,) = solve_responses((ex6_ratio(),))
    assert metric_value("ratio_ss_db", response_ratio(r6, 0, 1)).value == pytest.approx(20.0, rel=1e-12)


def test_metric_value_does_not_compute_resolution():
    """3.15·9.0: metric_value 단독 호출은 분해능을 계산하지 않는다 -- 값이 있어도 resolution None(분해능은 metrics_ss 가 붙인다)."""
    (r,) = solve_responses((ex3_miller(),))
    la = analyze_loop((Factor(r, 0),))
    (ra,) = solve_responses((ex2_amp(),))
    for name, src in (("gain_ss_db", la), ("ugf_ss_hz", la), ("pm_ss_deg", la), ("gbw_ss_hz", la),
                      ("rout_ss_ohm", output_resistance(ra, 1))):
        m = metric_value(name, src)
        assert m.value is not None and m.resolution is None, name
    s = supply_currents(_op(), (10,))
    assert metric_value("power_dc_w", s).resolution is None
    assert MetricResult("x", 1.0, ()).resolution is None            # 기본값 None(3칸 생성자)


def test_supply_and_area_metrics():
    s = supply_currents(_op(), (10,))
    assert metric_value("supply_current_dc", s).value == pytest.approx(25e-6, rel=1e-12)
    assert metric_value("power_dc_w", s).value == pytest.approx(45e-6, rel=1e-12)
    a = area_search((GateArea(10e-6, 0.5e-6), GateArea(4e-6, 1e-6)),
                    (PassiveArea("cc", 0.5e-12, 5e2), PassiveArea("rz", 5e3, None)))
    assert metric_value("area_search_m2", a).value == pytest.approx(2.59e-10, rel=1e-12)


def test_unknown_name_key_error():
    (r,) = solve_responses((ex1_rc(),))
    la = analyze_loop((Factor(r, 0),))
    with pytest.raises(KeyError):
        metric_value("gain_db", la)
    with pytest.raises(KeyError):
        metric_value("", la)


@pytest.mark.parametrize("name", ["gain_ss_db", "rout_ss_ohm", "ratio_ss_db", "power_dc_w", "area_search_m2"])
def test_wrong_source_type_error(name):
    s = supply_currents(_op(), (10,))
    a = area_search((), ())
    src = a if name != "area_search_m2" else s
    with pytest.raises(TypeError):
        metric_value(name, src)


# ---------- I-10: 값 의존 정의 불가에서 예외 0 ----------

def _undefined_sources():
    out = []
    (r,) = solve_responses((ex1_rc(),))                      # |H(0)| = 1: ugf·pm 정의 불가
    out.append(("ugf_ss_hz", analyze_loop((Factor(r, 0),))))
    (r2d,) = solve_responses((ex2d_sc_loop(),))              # 주입 열 NaN
    la = analyze_loop((Factor(r2d, 1),))
    out += [(n, la) for n in ("gain_ss_db", "ugf_ss_hz", "gbw_ss_hz", "pm_ss_deg", "parasitic_pm_ss_deg")]
    ck = SmallSignalCircuit(capacitors=(Capacitor(2, 0, 1e-12),), ac_ground=(0,))
    s = build_mna(ck, (Excitation("i", currents=((2, 1.0),)),), (Sense(2),))
    (rc,) = solve_responses((s,))
    out.append(("rout_ss_ohm", output_resistance(rc, 0)))
    ck6 = SmallSignalCircuit(resistors=(Resistor(1, 2, 1e3), Resistor(2, 3, 1e4)), ac_ground=(0,))
    s6 = build_mna(ck6, (Excitation("g", voltages=((1, 1.0),)), Excitation("z", voltages=((3, 0.0),))), (Sense(2),))
    (r6,) = solve_responses((s6,))
    out.append(("ratio_ss_db", response_ratio(r6, 0, 1)))
    ckd = SmallSignalCircuit(resistors=(Resistor(1, 2, 1e3), Resistor(2, 0, 1e3)), ac_ground=(0,))
    sd = build_mna(ckd, (Excitation("v", voltages=((1, 1.0),)),), (Sense(5),))   # isolated_node
    (rd,) = solve_responses((sd,))
    lad = analyze_loop((Factor(rd, 0),))
    out += [(n, lad) for n in ("gain_ss_db", "gbw_ss_hz")]
    return out


def test_undefined_never_raises_always_metric_result():
    for name, src in _undefined_sources():
        m = metric_value(name, src)
        assert isinstance(m, MetricResult), name
        assert m.name == name
        assert m.value is None, name
        assert len(m.undefined) >= 1, name
        for u in m.undefined:
            assert u.category in ("structural", "definitional", "numeric")
            assert isinstance(u.code, str) and u.code
