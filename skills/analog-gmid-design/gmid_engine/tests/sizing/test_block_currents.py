"""`dc_currents(snapshot, theta_currents)` -- CONTRACT 5.2: reads graph.dc_current_basis.

- 키 집합 ≠ free -> ValueError. 원소 전류 = Σ (num/den)·전류(원천)(유리수 합 뒤 float).
- MOS 전류 ≤ 0 -> SealViolationError(devices = 그 MOS 이름순, margin None, reason device_current_nonpositive, detail currents).
- writes dc_current(+ 가지치기 저항 0.0), dc_drop_current(= dc_current 중 resistors ∪ pruned).
기대값은 conftest 의 독립 RREF 와 손계산.
"""
from fractions import Fraction

import pytest

from gmid_engine.core import SealViolationError
from gmid_engine.sizing import dc_currents

from .conftest import build_ctx, detail, mos, topo, two


def two_src_circuit():
    """n 넷: I1·I2(고정) 가 들어오고 M1·M2 가 나간다 -> M1 = I1 + I2 − M2."""
    return topo("hand_two_src_cur",
                [mos("M1", "nmos", "n", "in", "gnd"), mos("M2", "nmos", "n", "b2", "gnd")],
                {"in": ("input", "x"), "n": ("output", "y")},
                sources=[two("I1", "current_source", "vdd", "n"), two("I2", "current_source", "vdd", "n")])


@pytest.fixture
def ctx2(tmp_path, toy_access):
    return build_ctx(tmp_path, two_src_circuit(), toy_access, element_values=(("I1", 1e-5), ("I2", 2e-5)))[2]


def test_currents_from_basis(ctx2):
    out = dc_currents(ctx2.base, (("M2", 1e-5),))
    cur = dict(out.column("device", "dc_current"))
    exp_m1 = float(Fraction(1e-5) + Fraction(2e-5) - Fraction(1e-5))
    assert cur == {"I1": 1e-5, "I2": 2e-5, "M1": exp_m1, "M2": 1e-5}
    assert dict(out.column("device", "dc_drop_current")) == {}          # 저항 없음


def test_rational_sum_then_float(ctx2):
    # 1e-5 + 2e-5 − 3e-5 를 float 로 차례로 더하면 0 이 아니지만(부동소수), 유리수 합은 정확히 같은 수의 차.
    i2 = 3e-5 - 1e-6
    out = dc_currents(ctx2.base, (("M2", i2),))
    m1 = dict(out.column("device", "dc_current"))["M1"]
    assert m1 == float(Fraction(1e-5) + Fraction(2e-5) - Fraction(i2))


def test_nonpositive_mos_current(ctx2):
    with pytest.raises(SealViolationError) as ei:
        dc_currents(ctx2.base, (("M2", 4e-5),))                         # M1 = −1e-5
    d = detail(ei.value)
    assert d["reason"] == "device_current_nonpositive"
    assert "currents" in d
    assert ei.value.record.devices == ("M1",)
    assert ei.value.record.margin is None


def test_zero_mos_current_rejected(ctx2):
    with pytest.raises(SealViolationError) as ei:
        dc_currents(ctx2.base, (("M2", 0.0),))
    assert ei.value.record.devices == ("M2",)


def test_key_set_must_equal_free(ctx2):
    with pytest.raises(ValueError):
        dc_currents(ctx2.base, ())
    with pytest.raises(ValueError):
        dc_currents(ctx2.base, (("M2", 1e-5), ("M1", 1e-5)))
    with pytest.raises(ValueError):
        dc_currents(ctx2.base, (("I1", 1e-5),))


def test_resistor_and_pruned_drop_currents(tmp_path, toy_access):
    doc = topo("hand_pruned_cur", [mos("M1", "nmos", "out", "in", "gnd")],
               {"in": ("input", "x"), "out": ("output", "y")},
               passives=[two("R1", "resistor", "vdd", "out"), two("R2", "resistor", "out", "leaf"),
                         two("C1", "capacitor", "out", "gnd")])
    ctx = build_ctx(tmp_path, doc, toy_access)[2]
    out = dc_currents(ctx.base, (("R1", 2e-5),))
    assert dict(out.column("device", "dc_current")) == {"M1": 2e-5, "R1": 2e-5, "R2": 0.0}
    assert dict(out.column("device", "dc_drop_current")) == {"R1": 2e-5, "R2": 0.0}
    for name in ("M1", "R1", "R2"):
        assert out.field("device", name, "dc_current").writer == "dc_currents"


def test_negative_resistor_current_allowed_when_mos_positive(tmp_path, toy_access):
    """R1 (out, vdd) 방향: M1 = −R1 -> θ R1 < 0 이어야 MOS 양수(저항 전류 부호는 제한 없음)."""
    doc = topo("hand_rev_cur", [mos("M1", "nmos", "out", "in", "gnd")],
               {"in": ("input", "x"), "out": ("output", "y")}, passives=[two("R1", "resistor", "out", "vdd")])
    ctx = build_ctx(tmp_path, doc, toy_access)[2]
    out = dc_currents(ctx.base, (("R1", -2e-5),))
    assert dict(out.column("device", "dc_current")) == {"M1": 2e-5, "R1": -2e-5}
    with pytest.raises(SealViolationError):
        dc_currents(ctx.base, (("R1", 2e-5),))


def test_reuse_same_input(ctx2):
    dc_currents.reset_stats()
    a = dc_currents(ctx2.base, (("M2", 1e-5),))
    b = dc_currents(a, (("M2", 1e-5),))
    assert b is a
    st = dc_currents.stats()
    assert (st.computes, st.reuses) == (1, 1)
