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


# =====================================================================================================================
# [CM 0e487b3] 결정 A(사용자 2026-10-08 "A는 제안대로 해") -- search CONTRACT 3.20 [CM]·I-19~I-21.
# view_kind cm_loop metric(pm_cm_ss_deg)의 dc_not_above_level(detail dc_magnitude = m, resolution = s) -> 위반 행 c = 20·log10(m)/s
# (s None·0 -> /1), m = 0 -> −∞, active True. 기대값은 test 가 그 식으로 계산(oracle (d) 계약 식 + (a) 수치). 선언은 build_search_context
# 대신 ConstraintDecl 을 직접 만든다(이 함수가 읽는 칸 metric·op·value·view 만 -- 회로 픽스처와 무관).
# =====================================================================================================================

import math  # noqa: E402

from gmid_engine.authoring import ConstraintDecl, SpecSource, ViewDecl  # noqa: E402

_CM_VIEW = ViewDecl("cm_output", weights=(("om", 0.5), ("op", 0.5)))
_US = SpecSource("user_spec")


def _cm_decl(metric="pm_cm_ss_deg", value=60.0, view=_CM_VIEW):
    return (ConstraintDecl(metric, ">=", value, True, view, _US),)


def _cm_bundle(decl, undefined, resolution=None, value=None):
    c = decl[0]
    return MetricBundle(((MetricRequest(c.metric, c.view), MetricResult(c.metric, value, undefined, resolution)),))


def _dna(m):
    return (Undefined("phase_margin_deg", "dc_not_above_level", "definitional", (("dc_magnitude", m),)),)


@pytest.mark.parametrize("m,s", [(0.01075805, 3.2), (0.5, 0.25), (1.0, 2.0), (0.3, None), (0.3, 0.0)],
                         ids=["contract_example", "half", "exactly_one", "s_none", "s_zero"])
def test_cm_dc_not_above_level_is_violation_row_i19(m, s):
    decl = _cm_decl()
    rows, un = ss_constraint_rows(_cm_bundle(decl, _dna(m), s), decl)
    assert tuple(un) == ()
    assert len(rows) == 1
    r = rows[0]
    assert r.name == "ss:0:pm_cm_ss_deg>="
    want = 20.0 * math.log10(m) / (s if s else 1.0)
    assert r.c == pytest.approx(want, rel=1e-15, abs=0.0)
    assert r.active is True


def test_cm_contract_example_m_s_i19():
    """계약 I-19 예의 입력(m = 0.01075805, s = 3.2)을 식으로 계산: 20·log10(0.01075805)/3.2 = −12.30167 (손계산).
    [계약 결함 보고] I-19 표의 'c = −12.3037 (실측 −12.303697098427348)' 은 이 m·s 와 맞지 않는다(m 을 반올림해 적은 것으로 보임) --
    숫자 리터럴 대조는 하지 않고 식만 확인한다."""
    decl = _cm_decl()
    rows, _ = ss_constraint_rows(_cm_bundle(decl, _dna(0.01075805), 3.2), decl)
    assert rows[0].c == pytest.approx(-12.30167, abs=5e-6)



def test_cm_zero_magnitude_is_minus_infinity_i19():
    decl = _cm_decl()
    rows, un = ss_constraint_rows(_cm_bundle(decl, _dna(0.0), 3.2), decl)
    assert tuple(un) == () and len(rows) == 1
    assert rows[0].c == -math.inf and rows[0].active is True


def test_cm_violation_monotone_in_magnitude_i21():
    """I-21: 같은 s 에서 c 는 |T_cm(0)| 에 단조 증가(0 dB 쪽으로)."""
    decl = _cm_decl()
    cs = [ss_constraint_rows(_cm_bundle(decl, _dna(m), 1.5), decl)[0][0].c for m in (1e-4, 1e-2, 0.1, 0.5, 0.999)]
    assert cs == sorted(cs) and len(set(cs)) == len(cs)
    assert all(c < 0 for c in cs)


def test_cm_valued_pm_row_unchanged_i21():
    """I-21: 값이 있는 CM PM 은 기존 의미 c = (값 − 목표)/s."""
    decl = _cm_decl()
    rows, un = ss_constraint_rows(_cm_bundle(decl, (), 0.5, 65.0), decl)
    assert tuple(un) == ()
    assert rows[0].name == "ss:0:pm_cm_ss_deg>=" and rows[0].c == pytest.approx((65.0 - 60.0) / 0.5, rel=1e-15)


def test_cm_rhp_stays_unmeasured_i20():
    """I-20: cm_loop 의 loop_open_rhp_poles 는 기존대로 unmeasured(행 0)."""
    decl = _cm_decl()
    und = (Undefined("phase_margin_deg", "loop_open_rhp_poles", "definitional",
                     (("rhp_pole_count", 1), ("rhp_poles", ((1.0, 0.0),)))),)
    rows, un = ss_constraint_rows(_cm_bundle(decl, und, 0.5), decl)
    assert tuple(rows) == ()
    assert tuple(tuple(u) for u in un) == (("pm_cm_ss_deg", ">=", "loop_open_rhp_poles"),)


def test_differential_pm_dc_not_above_level_stays_unmeasured_i20():
    """I-20: view_kind loop 인 pm_ss_deg 의 dc_not_above_level 은 행 0·unmeasured 1(차동 PM 의미 불변)."""
    decl = _cm_decl("pm_ss_deg", 60.0, ViewDecl("loop", beta="declared", cuts=(("Cf", "in"),), weights=(("in", 1.0),)))
    rows, un = ss_constraint_rows(_cm_bundle(decl, _dna(0.5), 0.5), decl)
    assert tuple(rows) == ()
    assert tuple(tuple(u) for u in un) == (("pm_ss_deg", ">=", "dc_not_above_level"),)
