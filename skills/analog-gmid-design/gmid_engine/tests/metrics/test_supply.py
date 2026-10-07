"""CONTRACT 3.13·예 4·I-8: supply_currents -- I_k = 채널 + 저항 + 이상원, supply_current_dc = Σ counted, power = Σ V_k I_k,
잔차 = Σ I_k. 전위 원점 이동: power 변화 = Δ·잔차, supply 불변. 합산 레일 선언 위반 ValueError."""
import pytest

from gmid_engine.metrics import (
    ChannelCurrent,
    CurrentSource,
    DcOperatingPoint,
    RailBias,
    Resistor,
    SupplyCurrents,
    supply_currents,
)


def _op(shift=0.0, nm=None):
    m = (lambda n: n) if nm is None else (lambda n: nm[n])
    return DcOperatingPoint(
        rails=(RailBias(m(10), 1.8 + shift), RailBias(m(0), 0.0 + shift)),
        node_v=((m(6), 0.8 + shift),),
        channels=(ChannelCurrent(m(5), m(0), 10e-6), ChannelCurrent(m(5), m(10), -10e-6), ChannelCurrent(m(7), m(0), 5e-6)),
        resistors=(Resistor(m(10), m(6), 1e5), Resistor(m(6), m(0), 8e4)),
        sources=(CurrentSource(m(10), m(7), 5e-6),),
    )


def test_ex4_hand_values():
    # I_10 = +10µ(PMOS 부하 source=10, −(−10µ)) + (1.8−0.8)/100k + 5µ(이상원 from) = 25 µA
    # I_0  = −10µ − 5µ(채널 source=0) + (0−0.8)/80k = −25 µA
    s = supply_currents(_op(), (10,))
    assert isinstance(s, SupplyCurrents)
    per = dict(s.per_rail)
    assert per[10] == pytest.approx(25e-6, rel=1e-12)
    assert per[0] == pytest.approx(-25e-6, rel=1e-12)
    assert s.counted_rails == (10,)
    assert s.supply_current_dc == pytest.approx(25e-6, rel=1e-12)
    assert s.power_dc_w == pytest.approx(45e-6, rel=1e-12)
    assert s.kcl_residual_amp == pytest.approx(0.0, abs=1e-18)


@pytest.mark.parametrize("delta", [1.0, -0.6, 3.3])
def test_potential_shift_invariance(delta):
    base = supply_currents(_op(), (10,))
    sh = supply_currents(_op(shift=delta), (10,))
    assert sh.supply_current_dc == pytest.approx(base.supply_current_dc, rel=1e-12)
    assert sh.power_dc_w - base.power_dc_w == pytest.approx(delta * base.kcl_residual_amp, abs=1e-15)
    assert sh.power_dc_w == pytest.approx(45e-6, rel=1e-9)


def test_unbalanced_residual_moves_power_by_delta_times_residual():
    # 레일 0 쪽 경로를 빼서 잔차를 만든다: 이상원 10 -> 7 만 (7 은 레일 아님)
    op = DcOperatingPoint(rails=(RailBias(10, 1.8), RailBias(0, 0.0)), sources=(CurrentSource(10, 7, 5e-6),))
    s0 = supply_currents(op, (10,))
    assert s0.kcl_residual_amp == pytest.approx(5e-6, rel=1e-12)
    op2 = DcOperatingPoint(rails=(RailBias(10, 2.8), RailBias(0, 1.0)), sources=(CurrentSource(10, 7, 5e-6),))
    s1 = supply_currents(op2, (10,))
    assert s1.power_dc_w - s0.power_dc_w == pytest.approx(1.0 * 5e-6, rel=1e-9)
    assert s1.supply_current_dc == pytest.approx(s0.supply_current_dc, rel=1e-12)


def test_counted_both_rails_sum():
    s = supply_currents(_op(), (0, 10))
    assert s.supply_current_dc == pytest.approx(0.0, abs=1e-18)


def test_renumbered_same():
    nm = {10: 3, 0: 99, 5: 1, 6: 42, 7: 8}
    s = supply_currents(_op(nm=nm), (3,))
    assert s.supply_current_dc == pytest.approx(25e-6, rel=1e-12)
    assert s.power_dc_w == pytest.approx(45e-6, rel=1e-12)


@pytest.mark.parametrize("counted", [(), (5,), (10, 10)], ids=["empty", "not_a_rail", "duplicate"])
def test_bad_counted_rails_value_error(counted):
    with pytest.raises(ValueError):
        supply_currents(_op(), counted)


def test_string_rail_type_error():
    with pytest.raises(TypeError):
        supply_currents(_op(), ("vdd",))
