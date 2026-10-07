"""CONTRACT 3.20 + r5 명확화 + r6 S-19 `ss_constraint_rows(bundle, declared, model_error=())`.

- declared 비면 ((), ()). bundle None -> 행 0, 선언마다 (metric, op, "ss_requires_sealed_snapshot") (I-12).
- 값 None -> (metric, op, Undefined code 집합을 정렬해 '+' 로 이은 것; code 없으면 "undefined") (r5).
- 값 있음: 분모 s = MetricResult.resolution (r6). s None -> unmeasured "resolution_undefined", s 0(모델 오차 선언 없음) ->
  unmeasured "resolution_zero_model_error_undeclared"(0 나누기 없음). 그 밖 행 `ss:<k>:<metric><op>`(k = ss_constraints 안 0 부터
  위치, r5), c = (값 − 목표)/s (>=) 또는 (목표 − 값)/s (<=), active = c ≤ 1.
기대값은 손으로 만든 MetricBundle 값으로 test 가 계산한다. 선언 = build_search_context 의 `ss_constraints`(ConstraintDecl).
"""
import pytest

from gmid_engine.metrics import MetricBundle, MetricRequest, MetricResult, Undefined
from gmid_engine.search import ConstraintRow, ss_constraint_rows

from .conftest import build_case, circuit_c

CONS = (("gain_ss_db", ">=", 20.0, None), ("rout_ss_ohm", "<=", 5e4, None), ("ugf_ss_hz", ">=", 0.0, None))


@pytest.fixture
def declared(tmp_path, lut_sealed):
    case = build_case(tmp_path, circuit_c(), lut_sealed, constraints=CONS)
    d = tuple(case.sctx.ss_constraints)
    assert [(c.metric, c.op, c.value) for c in d] == [c[:3] for c in CONS]
    return d


def _bundle(declared, values):
    """values[metric] = (값, resolution) 또는 Undefined tuple."""
    entries = []
    for c in declared:
        v = values[c.metric]
        if isinstance(v, tuple) and v and isinstance(v[0], Undefined) or v == ():
            entries.append((MetricRequest(c.metric, c.view), MetricResult(c.metric, None, v)))
        else:
            entries.append((MetricRequest(c.metric, c.view), MetricResult(c.metric, v[0], (), v[1])))
    return MetricBundle(tuple(entries))


def test_empty_declared():
    assert ss_constraint_rows(None, ()) == ((), ())
    assert tuple(map(tuple, ss_constraint_rows(MetricBundle(()), ()))) == ((), ())


def test_no_sealed_bundle_all_unmeasured(declared):
    rows, un = ss_constraint_rows(None, declared)
    assert tuple(rows) == ()
    assert tuple(tuple(u) for u in un) == tuple((c.metric, c.op, "ss_requires_sealed_snapshot") for c in declared)


def test_rows_normalised_by_resolution(declared):
    vals = {"gain_ss_db": (30.0, 0.5), "rout_ss_ohm": (5.02e4, 40.0), "ugf_ss_hz": (3e6, 1e3)}
    rows, un = ss_constraint_rows(_bundle(declared, vals), declared)
    assert tuple(un) == ()
    assert all(isinstance(r, ConstraintRow) for r in rows)
    exp = [("ss:0:gain_ss_db>=", (30.0 - 20.0) / 0.5), ("ss:1:rout_ss_ohm<=", (5e4 - 5.02e4) / 40.0),
           ("ss:2:ugf_ss_hz>=", (3e6 - 0.0) / 1e3)]
    assert [r.name for r in rows] == [n for n, _ in exp]
    for r, (_, c) in zip(rows, exp):
        assert r.c == pytest.approx(c, rel=1e-15)
        assert r.active == (r.c <= 1)


@pytest.mark.parametrize("value, active", [(20.4, True), (20.5, True), (20.6, False), (19.0, True)])
def test_active_iff_c_le_one(declared, value, active):
    vals = {"gain_ss_db": (value, 0.5), "rout_ss_ohm": (1.0, 1.0), "ugf_ss_hz": (1.0, 1.0)}
    rows, _ = ss_constraint_rows(_bundle(declared, vals), declared)
    r = rows[0]
    assert r.c == pytest.approx((value - 20.0) / 0.5, rel=1e-15)
    assert r.active is active


def test_resolution_none_and_zero_are_unmeasured(declared):
    vals = {"gain_ss_db": (30.0, None), "rout_ss_ohm": (4e4, 0.0), "ugf_ss_hz": (3e6, 1e3)}
    rows, un = ss_constraint_rows(_bundle(declared, vals), declared)
    assert [tuple(u) for u in un] == [("gain_ss_db", ">=", "resolution_undefined"),
                                      ("rout_ss_ohm", "<=", "resolution_zero_model_error_undeclared")]
    assert [r.name for r in rows] == ["ss:2:ugf_ss_hz>="]          # k 는 선언 위치 그대로
    assert rows[0].c == pytest.approx(3e6 / 1e3, rel=1e-15)


def test_undefined_value_codes_sorted_joined(declared):
    und = (Undefined("gain_ss_db", "passive_value_undeclared", "definitional"),
           Undefined("gain_ss_db", "no_crossing_above", "definitional"))
    vals = {"gain_ss_db": und, "rout_ss_ohm": (4e4, 100.0), "ugf_ss_hz": ()}
    rows, un = ss_constraint_rows(_bundle(declared, vals), declared)
    assert [tuple(u) for u in un] == [("gain_ss_db", ">=", "no_crossing_above+passive_value_undeclared"),
                                      ("ugf_ss_hz", ">=", "undefined")]
    assert len(rows) == 1 and rows[0].name == "ss:1:rout_ss_ohm<="
    assert rows[0].c == pytest.approx((5e4 - 4e4) / 100.0, rel=1e-15)
