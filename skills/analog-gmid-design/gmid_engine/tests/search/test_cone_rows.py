"""CONTRACT 3.5 `cone_rows`: MOS 마다 c = Σ항 / Σ|항|(유리수, fixed 포함), 항 합 0 -> 0, active False, c ≤ 0 ⇔ check_theta 거부.
기대값은 test 가 Fraction 으로 손계산한다."""
from fractions import Fraction

import pytest

from gmid_engine.search import CON_CONE, ConstraintRow, cone_rows
from gmid_engine.sizing import CurrentTerm, ThetaSchema, check_theta

from .conftest import schema_of  # [U17 ①-b] graph/kernel 필드 읽기
from .conftest import build_case, circuit_c, theta_r4c

CT = CurrentTerm


def _schema():
    comps = (("current", "Ia"), ("current", "Ib"))
    cone = (("M1", (CT("I1", 1, 1), CT("Ia", -1, 1))),
            ("M2", (CT("Ib", 1, 2),)),
            ("M3", (CT("Ia", 1, 1), CT("Ib", -1, 1))))
    return ThetaSchema(comps, cone, (("I1", 1e-5),))


def _expect(schema, theta):
    vals = dict(theta)
    vals.update({("current", k): v for k, v in schema.fixed})
    out = []
    for m, terms in schema.current_cone:
        parts = [Fraction(t.num, t.den) * Fraction(vals[("current", t.source)]) for t in terms]
        s, a = sum(parts), sum(abs(p) for p in parts)
        out.append((m, 0.0 if s == 0 else float(s / a)))
    return out


def _theta(ia, ib):
    return ((("current", "Ia"), ia), (("current", "Ib"), ib))


@pytest.mark.parametrize("ia, ib", [(3e-6, 1e-6), (1e-6, 3e-6), (2e-6, 2e-6)])
def test_rows_match_rational_hand_calc(ia, ib):
    sch = _schema()
    rows = cone_rows(sch, _theta(ia, ib))
    assert all(isinstance(r, ConstraintRow) for r in rows)
    exp = _expect(sch, _theta(ia, ib))
    assert [r.name for r in rows] == ["%s:%s" % (CON_CONE, m) for m, _ in exp]
    for r, (_, c) in zip(rows, exp):
        assert r.c == pytest.approx(c, rel=1e-15, abs=0.0)
        assert r.active is False


def test_zero_sum_row_is_zero():
    rows = dict((r.name, r.c) for r in cone_rows(_schema(), _theta(2e-6, 2e-6)))
    assert rows["%s:M3" % CON_CONE] == 0.0


def test_fixed_values_enter_the_row():
    # M1 = I1(fixed 1e-5) − Ia: Ia = 3e-6 -> 7/13.
    rows = dict((r.name, r.c) for r in cone_rows(_schema(), _theta(3e-6, 1e-6)))
    assert rows["%s:M1" % CON_CONE] == pytest.approx(7.0 / 13.0, rel=1e-15)


def test_positive_rational_rounding_to_float_zero_is_arithmetic_error():
    big = 10 ** 400
    sch = ThetaSchema((("current", "Ia"), ("current", "Ib")),
                      (("M1", (CT("Ia", 1, 1), CT("Ib", -(big - 1), big))),), ())
    # c = (1 − (1 − 10^-400)) / (2 − 10^-400) > 0 이지만 float 0.
    with pytest.raises(ArithmeticError):
        cone_rows(sch, _theta(1.0, 1.0))


def test_nonpositive_row_iff_check_theta_rejects(tmp_path, lut_sealed):
    case = build_case(tmp_path, circuit_c(), lut_sealed)
    schema = schema_of(case.dc)
    for i2, ok in ((1e-5, True), (-1e-5, False)):
        th = tuple(sorted(theta_r4c(i2=i2).items()))
        rows = cone_rows(schema, th)
        assert (min(r.c for r in rows) > 0) == ok
        if ok:
            check_theta(schema, dict(th))
        else:
            with pytest.raises(ValueError):
                check_theta(schema, dict(th))
