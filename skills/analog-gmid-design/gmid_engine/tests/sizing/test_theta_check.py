"""`check_theta(schema, values) -> Theta` -- CONTRACT 5.1.

schema 가 ThetaSchema 아님 -> TypeError. 키 집합 ≠ components -> ValueError. 값이 bool·비실수·비유한 -> ValueError.
y ∉ [0, 1], L ≤ 0, resistance ≤ 0 -> ValueError. 반환 = 키 정렬 (((kind, key), float), ...).
(θ 전류 부호 정의역은 theta_schema 변경 대상이라 이번 판에서 판정하지 않는다.)
"""
import math

import pytest

from gmid_engine.sizing import Theta, ThetaSchema, check_theta

COMPONENTS = (("L", "M1"), ("L", "M2"), ("current", "M2"), ("ln_idu", "M1"), ("resistance", "R1"), ("y", "out"))
SCHEMA = ThetaSchema(COMPONENTS)


def good():
    return {("y", "out"): 0.5, ("L", "M2"): 2e-6, ("ln_idu", "M1"): -13.5, ("current", "M2"): 1e-5,
            ("L", "M1"): 1e-6, ("resistance", "R1"): 9e4}


def test_returns_sorted_theta_of_floats():
    t = check_theta(SCHEMA, good())
    assert isinstance(t, Theta)
    keys = [k for k, _ in t.values]
    assert keys == sorted(good())
    assert all(isinstance(v, float) for _, v in t.values)
    assert dict(t.values) == good()


def test_int_values_become_float():
    v = good()
    v[("resistance", "R1")] = 90000
    t = check_theta(SCHEMA, v)
    r = dict(t.values)[("resistance", "R1")]
    assert isinstance(r, float) and r == 90000.0


def test_insertion_order_irrelevant():
    a = check_theta(SCHEMA, good())
    b = check_theta(SCHEMA, dict(reversed(list(good().items()))))
    assert a == b


@pytest.mark.parametrize("bad", [None, COMPONENTS, {"components": COMPONENTS}])
def test_type_error_schema(bad):
    with pytest.raises(TypeError):
        check_theta(bad, good())


def test_missing_key():
    v = good()
    del v[("y", "out")]
    with pytest.raises(ValueError):
        check_theta(SCHEMA, v)


def test_extra_key():
    v = good()
    v[("y", "other")] = 0.5
    with pytest.raises(ValueError):
        check_theta(SCHEMA, v)


@pytest.mark.parametrize("val", [True, False, "1e-6", None, math.nan, math.inf, -math.inf, complex(1, 0)])
def test_bad_value_types(val):
    v = good()
    v[("ln_idu", "M1")] = val
    with pytest.raises(ValueError):
        check_theta(SCHEMA, v)


@pytest.mark.parametrize("key,val", [
    (("y", "out"), -1e-12), (("y", "out"), 1.0 + 1e-12), (("y", "out"), 2.0),
    (("L", "M1"), 0.0), (("L", "M1"), -1e-6),
    (("resistance", "R1"), 0.0), (("resistance", "R1"), -5.0),
])
def test_domain_rejections(key, val):
    v = good()
    v[key] = val
    with pytest.raises(ValueError):
        check_theta(SCHEMA, v)


@pytest.mark.parametrize("y", [0.0, 1.0, 0.25])
def test_y_closed_interval_accepted(y):
    v = good()
    v[("y", "out")] = y
    assert dict(check_theta(SCHEMA, v).values)[("y", "out")] == y


def test_ln_idu_may_be_any_finite_sign():
    v = good()
    v[("ln_idu", "M1")] = 3.0
    assert dict(check_theta(SCHEMA, v).values)[("ln_idu", "M1")] == 3.0
