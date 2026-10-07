"""CONTRACT 3.12·예 6: response_ratio -- ratio_db = 20·log10|H_num(0)/H_den(0)|, 같은 계 두 열, 분자·분모 0 은 num_zero·den_zero."""
import math

import pytest

from gmid_engine.metrics import (
    Excitation,
    Resistor,
    ResponseRatio,
    Sense,
    SmallSignalCircuit,
    build_mna,
    response_ratio,
    solve_responses,
)

from .conftest import RENUMBER, STAMP_FUNCS, codes, count_calls, ex6_ratio


def test_ex6_twenty_db():
    (r,) = solve_responses((ex6_ratio(),))
    q = response_ratio(r, 0, 1)
    assert isinstance(q, ResponseRatio)
    assert (q.num_column, q.den_column) == (0, 1)
    assert q.ratio_db == pytest.approx(20.0 * math.log10(1e4 / 1e3), rel=1e-12)
    assert q.ratio_db == pytest.approx(20.0, rel=1e-12)
    assert q.undefined == ()


def test_swapped_columns_negative():
    (r,) = solve_responses((ex6_ratio(),))
    assert response_ratio(r, 1, 0).ratio_db == pytest.approx(-20.0, rel=1e-12)


def test_renumbered_same():
    (r,) = solve_responses((ex6_ratio(nm=RENUMBER),))
    assert response_ratio(r, 0, 1).ratio_db == pytest.approx(20.0, rel=1e-12)


def _zero_column_system(zero_first):
    ck = SmallSignalCircuit(resistors=(Resistor(1, 2, 1e3), Resistor(2, 3, 1e4)), ac_ground=(0,))
    good = Excitation("good", voltages=((1, 1.0),))
    zero = Excitation("zero", voltages=((3, 0.0),))
    return build_mna(ck, (zero, good) if zero_first else (good, zero), (Sense(2),))


def test_den_zero_is_value_not_exception():
    (r,) = solve_responses((_zero_column_system(False),))
    q = response_ratio(r, 0, 1)
    assert q.ratio_db is None
    assert "den_zero" in codes(q.undefined)


def test_num_zero_is_value_not_exception():
    (r,) = solve_responses((_zero_column_system(True),))
    q = response_ratio(r, 0, 1)
    assert q.ratio_db is None
    assert "num_zero" in codes(q.undefined)


def test_no_restamp():
    (r,) = solve_responses((ex6_ratio(),))
    with count_calls(*STAMP_FUNCS, build_mna) as n:
        response_ratio(r, 0, 1)
    assert n == {"mos_stamps": 0, "two_terminal_stamps": 0, "build_mna": 0}
