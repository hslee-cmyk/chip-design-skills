"""CONTRACT 3.11: output_resistance -- 구동 진폭 0·전류는 관측 노드에만인 열에서 rout = DC 극한 관측값 / I(부호 그대로).
열 조건 위반 ValueError, DC 극한 정의 불가는 None + 사유."""
import pytest

from gmid_engine.metrics import (
    Capacitor,
    Excitation,
    MosSmallSignal,
    OutputResistance,
    Resistor,
    Sense,
    SmallSignalCircuit,
    build_mna,
    metric_value,
    output_resistance,
    solve_responses,
)

from .conftest import STAMP_FUNCS, codes, count_calls, ex2_amp


def test_ex2_rout_is_ro():
    (r,) = solve_responses((ex2_amp(),))
    o = output_resistance(r, 1)
    assert isinstance(o, OutputResistance)
    assert o.column == 1
    assert o.rout_ohm == pytest.approx(1e5, rel=1e-12)
    assert o.undefined == ()


def test_sign_of_current_kept():
    ck = SmallSignalCircuit(resistors=(Resistor(2, 0, 2e3),), ac_ground=(0,))
    s = build_mna(ck, (Excitation("i", currents=((2, -0.5),)),), (Sense(2),))
    (r,) = solve_responses((s,))
    assert output_resistance(r, 0).rout_ohm == pytest.approx(2e3, rel=1e-12)


def test_differential_rout():
    ck = SmallSignalCircuit(resistors=(Resistor(2, 0, 1e3), Resistor(3, 0, 2e3), Resistor(2, 3, 6e3)),
                            ac_ground=(0,))
    s = build_mna(ck, (Excitation("id", currents=((2, 1.0), (3, -1.0))),), (Sense(2, 3),))
    (r,) = solve_responses((s,))
    # 2–3 사이 본 저항: 6k ‖ (1k + 2k) = 2k
    assert output_resistance(r, 0).rout_ohm == pytest.approx(2e3, rel=1e-12)


def test_column_with_voltage_drive_rejected():
    (r,) = solve_responses((ex2_amp(),))
    with pytest.raises(ValueError):
        output_resistance(r, 0)


def test_current_at_non_sense_node_rejected():
    ck = SmallSignalCircuit(resistors=(Resistor(2, 0, 1e3), Resistor(3, 2, 1e3)), ac_ground=(0,))
    s = build_mna(ck, (Excitation("i", currents=((3, 1.0),)),), (Sense(2),))
    (r,) = solve_responses((s,))
    with pytest.raises(ValueError):
        output_resistance(r, 0)


def test_differential_unbalanced_rejected():
    ck = SmallSignalCircuit(resistors=(Resistor(2, 0, 1e3), Resistor(3, 0, 2e3)), ac_ground=(0,))
    s = build_mna(ck, (Excitation("id", currents=((2, 1.0), (3, 1.0))),), (Sense(2, 3),))
    (r,) = solve_responses((s,))
    with pytest.raises(ValueError):
        output_resistance(r, 0)


def test_dc_undefined_gives_none_with_reason():
    # 관측 노드가 용량 전용: DC 전류 주입 -> 극한 발산
    ck = SmallSignalCircuit(capacitors=(Capacitor(2, 0, 1e-12),), ac_ground=(0,))
    s = build_mna(ck, (Excitation("i", currents=((2, 1.0),)),), (Sense(2),))
    (r,) = solve_responses((s,))
    o = output_resistance(r, 0)
    assert o.rout_ohm is None
    assert "dc_charge_injection" in codes(o.undefined)


def test_no_restamp():
    (r,) = solve_responses((ex2_amp(),))
    with count_calls(*STAMP_FUNCS, build_mna) as n:
        output_resistance(r, 1)
    assert n == {"mos_stamps": 0, "two_terminal_stamps": 0, "build_mna": 0}


# ---------- 7a: 출력 포트 감지 뷰 = 감지 노드 단위 전류 열의 ω -> 0 극한 (3.11), 음의 rout = 정의 불가 ----------

def _port_system(mos, res, cap, ac_ground, vin_node, out_node, sense_node=None):
    """포트 전달 계(입력 포트 전압 열 vin) + 감지 노드 단위 전류 열 iout. 감지 넷이 출력 포트와 다르면 관측 행을 하나 더
    (행 0 = 출력 포트, 행 1 = 감지 넷) -- 같은 계, 조립 1회(3.11)."""
    ck = SmallSignalCircuit(mos=mos, resistors=res, capacitors=cap, ac_ground=ac_ground)
    sn = out_node if sense_node is None else sense_node
    senses = (Sense(out_node),) if sense_node is None else (Sense(out_node), Sense(sense_node))
    exc = (Excitation("vin", voltages=((vin_node, 1.0),)), Excitation("iout", currents=((sn, 1.0),)))
    (r,) = solve_responses((build_mna(ck, exc, senses),))
    return r


def test_cs_rout_is_rl_parallel_ro():
    """CS: 입력 포트 0 V 고정(vin 열 밖에서는 0 V), 출력 = RL ‖ ro. CL 은 DC 극한에 영향 없음."""
    gm, gds, rl = 1e-3, 1e-5, 2e4
    r = _port_system((MosSmallSignal(2, 1, 0, 0, gm, 0.0, gds),), (Resistor(2, 0, rl),), (Capacitor(2, 0, 1e-12),),
                     (0,), 1, 2)
    o = output_resistance(r, 1)
    assert o.rout_ohm == pytest.approx(1.0 / (gds + 1.0 / rl), rel=1e-12)
    assert o.undefined == ()


def test_source_follower_rout_includes_gmb():
    """SF: d 교류접지, g = 입력 포트(고정), 출력 s: rout = 1/(gm + gmb + gds + 1/RL)."""
    gm, gmb, gds, rl = 1e-3, 2e-4, 1e-5, 1e4
    r = _port_system((MosSmallSignal(9, 1, 2, 0, gm, gmb, gds),), (Resistor(2, 0, rl),), (), (0, 9), 1, 2)
    assert output_resistance(r, 1).rout_ohm == pytest.approx(1.0 / (gm + gmb + gds + 1.0 / rl), rel=1e-12)


def test_sense_net_other_than_output_uses_row():
    """감지 넷(2)이 출력 포트(3)와 다르다: 관측 행 1 = 감지. rout(2) = 1/(gds + 1/(R23 + RL)).
    같은 열을 출력 포트 행(0)으로 읽으면 전류가 관측 노드에 없으므로 ValueError, 행 범위 밖도 ValueError."""
    gm, gds, r23, rl = 1e-3, 1e-5, 5e3, 2e4
    r = _port_system((MosSmallSignal(2, 1, 0, 0, gm, 0.0, gds),), (Resistor(2, 3, r23), Resistor(3, 0, rl)), (),
                     (0,), 1, 3, sense_node=2)
    assert output_resistance(r, 1, row=1).rout_ohm == pytest.approx(1.0 / (gds + 1.0 / (r23 + rl)), rel=1e-12)
    with pytest.raises(ValueError):
        output_resistance(r, 1, row=0)
    with pytest.raises(ValueError):
        output_resistance(r, 1, row=2)


def _cross_coupled(gm2):
    """양되먹임: M1(d=3,g=2), M2(d=2,g=3), RL(2,0) = R3(3,0) = 10k, gm1 = 1e-3. 노드 2 에 I:
    v3 = −gm1·R3·v2, I = v2·(1/RL − gm1·gm2·R3) -> rout = 1/(1/RL − gm1·gm2·R3)."""
    ck = SmallSignalCircuit(mos=(MosSmallSignal(3, 2, 0, 0, 1e-3, 0.0, 0.0), MosSmallSignal(2, 3, 0, 0, gm2, 0.0, 0.0)),
                            resistors=(Resistor(2, 0, 1e4), Resistor(3, 0, 1e4)), ac_ground=(0,))
    (r,) = solve_responses((build_mna(ck, (Excitation("i", currents=((2, 1.0),)),), (Sense(2),)),))
    return r, 1.0 / (1.0 / 1e4 - 1e-3 * gm2 * 1e4)


def test_positive_feedback_below_unity_positive_value():
    r, exp = _cross_coupled(5e-6)
    assert exp == pytest.approx(2e4, rel=1e-12)
    assert output_resistance(r, 0).rout_ohm == pytest.approx(exp, rel=1e-12)


def test_negative_rout_is_undefined_value():
    """루프 이득 > 1: rout 손계산 −101.0101 Ω -> None + negative_output_resistance(definitional, detail value_ohm).
    값을 내지 않으므로 'rout_ss_ohm <= x' 판정이 통과할 수 없다."""
    r, exp = _cross_coupled(1e-3)
    assert exp == pytest.approx(-1.0 / 9.9e-3, rel=1e-12)
    o = output_resistance(r, 0)
    assert o.rout_ohm is None
    (u,) = [u for u in o.undefined if u.code == "negative_output_resistance"]
    assert u.category == "definitional"
    assert dict(u.detail)["value_ohm"] == pytest.approx(exp, rel=1e-12)
    m = metric_value("rout_ss_ohm", o)
    assert m.value is None and "negative_output_resistance" in codes(m.undefined)
    passes_le = m.value is not None and m.value <= 5000.0
    assert passes_le is False
