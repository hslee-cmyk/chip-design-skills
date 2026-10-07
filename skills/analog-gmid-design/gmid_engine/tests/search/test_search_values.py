"""CONTRACT 2절 -- `search_values` 값 형식·어휘(상태·단계·축·제약 접두). 기준은 계약 문장."""
import dataclasses

import pytest

import gmid_engine.search as S


def test_status_vocabulary():
    assert S.STATUS_SEALED == "sealed"
    assert S.STATUS_PENDING_SEAL7 == "pending_seal_7"
    assert S.STATUS_UNDEFINED == "seal_undefined"
    assert S.STATUS_FAILED == "failed"
    assert S.STATUS_OUTSIDE_DOMAIN == "outside_domain"
    assert tuple(S.ACCEPTED_STATUSES) == ("sealed", "pending_seal_7")


def test_axes_and_stage_names():
    assert S.AXIS_POWER == "power_dc_w"
    assert S.AXIS_AREA == "area_search_m2"
    assert tuple(S.AXES) == ("power_dc_w", "area_search_m2")
    stages = {S.STAGE_START, S.STAGE_SLSQP, S.STAGE_FD, S.STAGE_L_SEARCH}
    assert len(stages) == 4 and all(isinstance(s, str) and s for s in stages)


def test_constraint_prefixes():
    assert S.CON_SEAL6 == "seal6_bulk"
    assert S.CON_INVERSION == "inversion_floor"
    assert S.CON_CONE == "current_cone"
    assert S.CON_EPS == "eps"


def test_con_wmin_is_public():
    """[r3] 2절: 제약 이름 접두 `CON_WMIN`("w_min") -- 다른 접두와 같은 공개 어휘(계약 머리: test 는 공개 이름만 쓴다)."""
    assert "CON_WMIN" in S.__all__, "CON_WMIN 이 gmid_engine.search.__all__ 에 없다"
    assert S.CON_WMIN == "w_min"


@pytest.mark.parametrize("cls, args", [
    (S.Variable, (("y", "out"), False, 0.0, 1.0)),
    (S.ConstraintRow, ("x", 1.0, False)),
    (S.StartPoint, ("s1", (), (), "given")),
    (S.NodeRow, ("p", "sealed", 0.5, None, ())),
    (S.ParetoResult, ((), (), ())),
])
def test_frozen(cls, args):
    v = cls(*args)
    f = dataclasses.fields(v)[0].name
    with pytest.raises(dataclasses.FrozenInstanceError):
        setattr(v, f, None)


def test_defaults():
    o = S.Objectives(1.0, 2.0, (), 0.0, 2.0, (), ())
    assert o.power_resolution_w is None
    r = S.SolveResult(None, None, "power_dc_w", 0, 0, "x", ())
    assert r.aborts == () and r.frozen == ()
    fp = S.FrontPoint("p", None, ())
    assert fp.dominated_by is None
    sf = S.SearchFront("r", (), (), (), (), (), ())
    assert sf.unmeasured_front == ()
    d = S.SearchDomain((), (), 1.0, (), 2.0, 3.0)
    assert (d.area_resolution_m2, d.w_min_m, d.grid_m) == (1.0, 2.0, 3.0)


def test_eval_result_identity_equality():
    """EvalResult 는 eq=False -- 같은 필드여도 다른 객체는 같지 않다(캐시 적중은 `is` 로 판정)."""
    k = S.EvalKey("c", "s", (0,), None, ("0x1p+0",))
    a = S.EvalResult(k, (), "sealed", None, None, (), (), None, 1)
    b = S.EvalResult(k, (), "sealed", None, None, (), (), None, 1)
    assert a.unmeasured == ()
    assert a != b and a == a
