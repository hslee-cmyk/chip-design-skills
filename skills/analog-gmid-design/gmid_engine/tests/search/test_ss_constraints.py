"""CONTRACT r4 3.20 `ss_constraint_rows(bundle, declared) -> (rows, unmeasured)`.

- declared 비면 ((), ()). bundle None -> 행 0, 선언마다 (metric, op, "ss_requires_sealed_snapshot") (I-12).
- 값 None -> (metric, op, Undefined code '+' 연결). 값 있음 -> 행 `ss:<k>:<metric><op>`, c = (값 − 목표)/|목표|(>=) 또는
  (목표 − 값)/|목표|(<=), 목표 0 이면 분모 1, active False.
기대값은 손으로 만든 MetricBundle 값으로 test 가 계산한다. 선언 형식은 build_search_context 가 넘기는 `ss_constraints`
(r4 3.9: ConstraintDecl, 문서 순서) 를 그대로 쓴다.
"""
import re

import pytest

from gmid_engine.metrics import MetricBundle, MetricRequest, MetricResult, Undefined
from gmid_engine.search import ConstraintRow, ss_constraint_rows

from .conftest import build_case, circuit_c

CONS = (("gain_ss_db", ">=", 20.0, None), ("rout_ss_ohm", "<=", 5e4, None), ("ugf_ss_hz", ">=", 0.0, None))
NAME = re.compile(r"^ss:(\d+):([a-z_0-9]+)(>=|<=)$")


@pytest.fixture
def declared(tmp_path, lut_sealed):
    case = build_case(tmp_path, circuit_c(), lut_sealed, constraints=CONS)
    d = tuple(case.sctx.ss_constraints)
    assert [(c.metric, c.op, c.value) for c in d] == [c[:3] for c in CONS]
    return d


def _bundle(declared, values):
    entries = []
    seen = set()
    for c in declared:
        key = (c.metric, c.view)
        if key in seen:
            continue
        seen.add(key)
        v = values[c.metric]
        if isinstance(v, tuple):
            entries.append((MetricRequest(c.metric, c.view), MetricResult(c.metric, None, v)))
        else:
            entries.append((MetricRequest(c.metric, c.view), MetricResult(c.metric, v, ())))
    return MetricBundle(tuple(entries))


def test_empty_declared():
    assert ss_constraint_rows(None, ()) == ((), ())
    assert tuple(map(tuple, ss_constraint_rows(MetricBundle(()), ()))) == ((), ())


def test_no_sealed_bundle_all_unmeasured(declared):
    rows, un = ss_constraint_rows(None, declared)
    assert tuple(rows) == ()
    assert tuple(tuple(u) for u in un) == tuple((c.metric, c.op, "ss_requires_sealed_snapshot") for c in declared)


def test_values_become_normalised_rows(declared):
    rows, un = ss_constraint_rows(_bundle(declared, {"gain_ss_db": 30.0, "rout_ss_ohm": 1e5, "ugf_ss_hz": 30.0}), declared)
    assert tuple(un) == ()
    assert len(rows) == 3 and all(isinstance(r, ConstraintRow) for r in rows)
    exp = [(30.0 - 20.0) / 20.0, (5e4 - 1e5) / 5e4, (30.0 - 0.0) / 1.0]
    ks = []
    for r, c, e in zip(rows, declared, exp):
        m = NAME.match(r.name)
        assert m, r.name
        assert (m.group(2), m.group(3)) == (c.metric, c.op)
        ks.append(int(m.group(1)))
        assert r.c == pytest.approx(e, rel=1e-15)
        assert r.active is False
    assert len(set(ks)) == 3 and ks == sorted(ks)      # 선언마다 다른 k, 선언 순서


def test_undefined_value_joins_codes(declared):
    und = (Undefined("gain_ss_db", "passive_value_undeclared", "definitional"),
           Undefined("gain_ss_db", "no_crossing_above", "definitional"))
    rows, un = ss_constraint_rows(_bundle(declared, {"gain_ss_db": und, "rout_ss_ohm": 4e4, "ugf_ss_hz": und}), declared)
    un = [tuple(u) for u in un]
    # 연결 순서는 계약에 없다(모호점 보고) -- code 집합으로 비교.
    assert [(m, op) for m, op, _ in un] == [("gain_ss_db", ">="), ("ugf_ss_hz", ">=")]
    assert all(set(r.split("+")) == {"passive_value_undeclared", "no_crossing_above"} for _, _, r in un)
    assert len(rows) == 1
    assert rows[0].c == pytest.approx((5e4 - 4e4) / 5e4, rel=1e-15)
