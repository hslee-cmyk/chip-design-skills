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


# ---------------------------------------------------------------------------
# [r2] θ 전류 정의역 = current_cone (5.1·4.4)
# ---------------------------------------------------------------------------

from gmid_engine.sizing import CurrentTerm  # noqa: E402

CONE_COMPONENTS = (("current", "M2"), ("y", "n"))
# 손 기저: n 행 M1 + M2 = I1(고정 3e-5) -> M1 = I1 − M2, M2 = M2
CONE = (("M1", (CurrentTerm("I1", 1, 1), CurrentTerm("M2", -1, 1))), ("M2", (CurrentTerm("M2", 1, 1),)))
CONE_SCHEMA = ThetaSchema(CONE_COMPONENTS, CONE, (("I1", 3e-5),))


def test_cone_inside_accepted():
    t = check_theta(CONE_SCHEMA, {("current", "M2"): 1e-5, ("y", "n"): 0.5})
    assert dict(t.values)[("current", "M2")] == 1e-5


@pytest.mark.parametrize("i2", [3e-5, 4e-5, 0.0, -1e-6])
def test_cone_outside_rejected(i2):
    """M2 = 3e-5 -> M1 = 0 (유리수 정확 0, ≤ 0), 4e-5 -> M1 < 0, M2 ≤ 0 -> 상자 하한."""
    with pytest.raises(ValueError) as ei:
        check_theta(CONE_SCHEMA, {("current", "M2"): i2, ("y", "n"): 0.5})
    assert ("M1" in str(ei.value)) or ("M2" in str(ei.value))


def test_cone_uses_exact_rationals():
    """경계에서 1 ulp: θ = I1 이면 M1 = 0 정확 -> 거부, θ = I1 의 바로 아래 float 이면 M1 > 0 -> 통과."""
    import math
    below = math.nextafter(3e-5, 0.0)
    check_theta(CONE_SCHEMA, {("current", "M2"): below, ("y", "n"): 0.5})
    with pytest.raises(ValueError):
        check_theta(CONE_SCHEMA, {("current", "M2"): 3e-5, ("y", "n"): 0.5})
    with pytest.raises(ValueError):
        check_theta(CONE_SCHEMA, {("current", "M2"): math.nextafter(3e-5, 1.0), ("y", "n"): 0.5})


def test_cone_in_real_context(ctx_c):
    from .conftest import kschema, theta_c  # [U17 ①-b] kschema = graph/kernel theta_schema 읽기(설계 40 v1.9.1 §2.4.7)
    ctx = ctx_c[2]
    th = theta_c()
    check_theta(kschema(ctx), th)
    th[("current", "M2")] = -1e-6
    with pytest.raises(ValueError):
        check_theta(kschema(ctx), th)


def test_ln_idu_may_be_any_finite_sign():
    v = good()
    v[("ln_idu", "M1")] = 3.0
    assert dict(check_theta(SCHEMA, v).values)[("ln_idu", "M1")] == 3.0
