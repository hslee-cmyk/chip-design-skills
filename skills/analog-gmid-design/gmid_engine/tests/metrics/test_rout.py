"""CONTRACT 3.11: output_resistance -- 구동 진폭 0·전류는 관측 노드에만인 열에서 rout = DC 극한 관측값 / I(부호 그대로).
열 조건 위반 ValueError, DC 극한 정의 불가는 None + 사유."""
import pytest

from gmid_engine.metrics import (
    Capacitor,
    Excitation,
    OutputResistance,
    Resistor,
    Sense,
    SmallSignalCircuit,
    build_mna,
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
