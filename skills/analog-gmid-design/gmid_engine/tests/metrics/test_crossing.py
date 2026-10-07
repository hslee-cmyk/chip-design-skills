"""CONTRACT 3.8: find_crossing -- |T| = level 교차. |T(0)| ≤ level -> dc_not_above_level, 격자 끝 너머는 상계로 상단 괄호 유도,
극점 수 < 영점 수 또는 같고 |K| ≥ level -> no_crossing_above, 정의 불가는 Crossing.undefined(quantity = 인자)."""
import math

import numpy as np
import pytest

from gmid_engine.metrics import (
    Crossing,
    Excitation,
    Factor,
    Resistor,
    Sense,
    SmallSignalCircuit,
    build_mna,
    find_crossing,
    solve_responses,
)

from .conftest import closed_miller, closed_single_pole, ex1_rc, ex2_amp, ex2_beta_res, ex3_miller


def _t(factors):
    out = None
    for f in factors:
        col = np.asarray(f.response.values)[:, f.column]
        out = col if out is None else out * col
    return out


def _cross(factors, level, q="q"):
    om = np.asarray(factors[0].response.omegas)
    return find_crossing(factors, om, _t(factors), level, q)


def test_rc_inside_grid():
    (r,) = solve_responses((ex1_rc(),))
    c = _cross((Factor(r, 0),), 0.5)
    assert isinstance(c, Crossing)
    assert c.undefined is None
    assert c.level == 0.5
    assert c.omega == pytest.approx(math.sqrt(3.0) * 1e6, rel=1e-10)   # |1/(1+jωRC)| = 1/2
    assert abs(c.value) == pytest.approx(0.5, rel=1e-10)
    assert c.lo <= c.omega <= c.hi


def test_rc_beyond_grid_end_upper_bracket():
    (r,) = solve_responses((ex1_rc(),))
    assert np.asarray(r.omegas)[-1] < 1e7          # 교차가 격자 밖
    c = _cross((Factor(r, 0),), 0.01)
    assert c.undefined is None
    assert c.omega == pytest.approx(math.sqrt(1e4 - 1.0) * 1e6, rel=1e-10)


def test_miller_unity_crossing():
    ref = closed_miller()
    (r,) = solve_responses((ex3_miller(),))
    c = _cross((Factor(r, 0),), 1.0)
    assert c.omega / (2 * math.pi) == pytest.approx(ref["ugf_hz"], rel=1e-9)
    assert c.omega / (2 * math.pi) == pytest.approx(30592376.7006, rel=1e-9)


def test_two_factor_product_crossing():
    a0, wp = closed_single_pole()
    ra, rb = solve_responses((ex2_amp(), ex2_beta_res()))
    c = _cross((Factor(ra, 0), Factor(rb, 0)), 1.0)
    assert c.omega == pytest.approx(wp * math.sqrt(624.0), rel=1e-10)


@pytest.mark.parametrize("level", [1.0, 1.5])
def test_dc_not_above_level(level):
    (r,) = solve_responses((ex1_rc(),))
    c = _cross((Factor(r, 0),), level, q="my_quantity")
    assert c.omega is None
    assert c.undefined is not None
    assert c.undefined.code == "dc_not_above_level"
    assert c.undefined.category == "definitional"
    assert c.undefined.quantity == "my_quantity"


def test_no_crossing_above_flat_response():
    ck = SmallSignalCircuit(resistors=(Resistor(1, 2, 1e3), Resistor(2, 0, 1e3)), ac_ground=(0,))
    s = build_mna(ck, (Excitation("v", voltages=((1, 1.0),)),), Sense(2))
    (r,) = solve_responses((s,))
    c = _cross((Factor(r, 0),), 0.25, q="flat")
    assert c.omega is None
    assert c.undefined.code == "no_crossing_above"
    assert c.undefined.quantity == "flat"
