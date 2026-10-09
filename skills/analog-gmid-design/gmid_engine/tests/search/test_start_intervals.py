"""search/start_intervals.py -- `start_intervals(s1v, ach, kctx, spec, pdk_decl, domain) -> StartIntervals` + 층 0 배선
(설계 41 §6.1·§6.6, 40 §11 U13·§7.1, search CONTRACT U13.1~U13.3; D-SIa~g).

oracle:
- (d) 사용자 결정 11: library spec 의 `area_search_m2 <= A`(사용자 선언값) -- 실경로 층 0 출발점(봉인)의 면적 목적 ≤ A.
- (d) 봉인: 층 0 출발점 평가 상태 = sealed(search ACCEPTED 중 봉인 8항목 pass).
- (a) 구간 = 경계들의 교집합(start_values `Bound` 정의): 행 하한 ≥ 그 행 하한 경계의 최댓값, 상한 ≤ 상한 경계의 최솟값, 선택값은 [하한, 상한] 안(충돌 행 제외 -- 41 §6.6).
- (d) CONTRACT U13.3: 사다리 칸 0 = 선택점(theta·cells·current_ref), t 는 칸마다 절반; s1v 를 안 주면 ctx.start None(종전 상자 중심).
- (d) 41 §6.6 불변식: 같은 입력이면 같은 표(새로 만든 두 결과 비교), 이름 전단사는 행 이름만 바꾼다(SLSQP 풀이가 들어가므로 상대 1e-7: 반복 풀이의 수렴 허용오차
  √ε ≈ 1.5e-8 를 넘는 반올림 증폭만 허용 -- 소자 순회가 구조 색 순서라 이론상 비트 동일이고, 이름순 tuple 을 쓰는 하위 단계의 합산 순서 차이만 남는다).
- (d) CONTRACT U13 '비활성 사유는 조용히 빠지지 않는다': 조건부 경계 식마다 경계·충돌·비활성 사유 중 하나로 보고에 나온다.
실경로 = 실 LUT v2(noise·mismatch 포함, lut CONTRACT 1.8 정본 로드) + library two_stage_ota·common_gate_amplifier(u13_real).
"""
import json
import math

import pytest

from gmid_engine.search import ACCEPTED_STATUSES, build_search_context, evaluate, layer0_start

from .u13_hand import all_inactive, cs_chain, rows_by_name, toy_case
from .u13_real import LIBRARY, real_case

REAL = ("two_stage_ota", "common_gate_amplifier")
CONDITIONAL = ("gain_l_6.4_1", "matching_l_6.4_2", "offset_guard_6.4_2a", "flicker_l_6.4_3", "thermal_c_7.5", "noise_guard_7.5",
               "area_l_6.4_5", "area_gm_id_6.4_5")
TOY_ELS = (("C1", "capacitor", 1e-12), ("C2", "capacitor", 2e-12))
TOY_CONS = (("gbw_ss_hz", ">=", 1e6), ("pm_ss_deg", ">=", 60.0))


def _budget(name):
    spec = json.loads((LIBRARY / (name + ".sizing_spec.json")).read_text(encoding="utf-8"))
    vals = [c["value"] for c in spec["human"]["constraints"] if c.get("metric") == "area_search_m2" and c.get("op") == "<="]
    assert vals, name
    return min(float(v) for v in vals)


@pytest.mark.parametrize("name", REAL)
def test_real_layer0_start_is_sealed_within_area_budget(name):
    case = real_case(name)
    assert case.start is not None
    res = layer0_start(case.sctx)
    assert res.start is not None, (res.start_status, res.start_failure)
    assert res.start_status == "sealed"
    assert res.origin_point == "centre" or res.origin_point.startswith(("ladder:", "ladder_repair:"))
    e = evaluate(case.sctx, dict(res.start.theta), res.start.cells)
    assert e.status == "sealed" and e.status in ACCEPTED_STATUSES
    assert e.objectives.area_m2 <= _budget(name)


@pytest.mark.parametrize("name", REAL)
def test_real_start_area_estimate_within_budget(name):
    st = real_case(name).start
    assert st.area_budget_m2 == pytest.approx(_budget(name))
    assert st.area_est_m2 <= st.area_budget_m2 or any(c.quantity == "area" for c in st.conflicts)


def _interval_invariants(st):
    conflicted = {c.device for c in st.conflicts} | {c.device for r in st.rows for c in r.conflicts}
    for r in st.rows:
        if r.device in conflicted:
            continue
        g_lo = [b.value for b in r.sources if b.quantity == "gm_id" and b.side == "lo"]
        g_hi = [b.value for b in r.sources if b.quantity == "gm_id" and b.side == "hi"]
        l_lo = [b.value for b in r.sources if b.quantity == "L" and b.side == "lo"]
        l_hi = [b.value for b in r.sources if b.quantity == "L" and b.side == "hi"]
        assert r.gm_id_lo >= max(g_lo) * (1 - 1e-12), r.device
        assert r.gm_id_hi <= min(g_hi) * (1 + 1e-12), r.device
        assert r.gm_id_lo * (1 - 1e-12) <= r.gm_id_chosen <= r.gm_id_hi * (1 + 1e-12), r.device
        assert r.l_lo >= max(l_lo) * (1 - 1e-12) and r.l_hi <= min(l_hi) * (1 + 1e-12), r.device
        assert r.l_lo * (1 - 1e-12) <= r.l_chosen <= r.l_hi * (1 + 1e-12), r.device


@pytest.mark.parametrize("name", REAL)
def test_real_rows_are_intersections_of_bounds(name):
    _interval_invariants(real_case(name).start)


def test_toy_rows_are_intersections_of_bounds():
    _interval_invariants(toy_case(cs_chain(2), elements=TOY_ELS, constraints=TOY_CONS).start)


@pytest.mark.parametrize("name", REAL)
def test_real_ladder_invariants(name):
    st = real_case(name).start
    assert st.ladder
    first = st.ladder[0]
    assert first.theta == st.theta and first.cells == st.cells and first.current_ref == st.current_ref
    assert first.t == st.area_fraction
    for a, b in zip(st.ladder, st.ladder[1:]):
        assert b.t == pytest.approx(a.t / 2, rel=1e-15)


@pytest.mark.parametrize("name", REAL)
def test_real_start_widths_at_least_minimum(name):
    # CONTRACT U13 '최소 폭 W ≥ W_min'(gm/ID 하한 w_min_gm_id + current_ref 자리값) -- 보고 행의 출발 폭. W_min = search 정의역 `w_min_m`(PDK 선언).
    case = real_case(name)
    w_min = case.sctx.domain.w_min_m
    low = [(r.device, r.w_m) for r in case.start.rows if r.w_m < w_min * (1 - 1e-9)]
    assert not low, (w_min, low)


def _silent(st):
    seen = set(src for src, _ in all_inactive(st))
    for r in st.rows:
        seen.update(b.source for b in r.sources)
        seen.update(s for c in r.conflicts for s, _ in c.bounds)
    seen.update(s for c in st.conflicts for s, _ in c.bounds)
    return [s for s in CONDITIONAL if s not in seen]


@pytest.mark.parametrize("name", REAL)
def test_real_inactive_reasons_never_silently_missing(name):
    assert _silent(real_case(name).start) == []


def test_toy_inactive_reasons_never_silently_missing():
    assert _silent(toy_case(cs_chain(2), elements=TOY_ELS, constraints=TOY_CONS).start) == []


def _table(st):
    return (st.rows, st.conflicts, st.inactive, st.theta, st.cells, st.ladder, st.current_ref, st.area_est_m2, st.records)


def test_determinism_same_input_same_table():
    a = toy_case(cs_chain(2), elements=TOY_ELS, constraints=TOY_CONS, fresh=True).start
    b = toy_case(cs_chain(2), elements=TOY_ELS, constraints=TOY_CONS, fresh=True).start
    assert repr(_table(a)) == repr(_table(b))


REN = {"n1": "zq", "out": "ab", "in": "yy", "pb1": "k2", "pb2": "k1", "MN1": "X7", "MN2": "X1", "MP1": "X9", "MP2": "X0",
       "C1": "Cz", "C2": "Ca"}


def _close(a, b):
    if a is None or b is None:
        return a is b
    return math.isclose(a, b, rel_tol=1e-7, abs_tol=0.0)


def test_name_bijection_changes_only_row_names():
    orig = toy_case(cs_chain(2), elements=TOY_ELS, constraints=TOY_CONS).start
    ren = toy_case(cs_chain(2, name="u13cs2ren", ren=REN), elements=(("Cz", "capacitor", 1e-12), ("Ca", "capacitor", 2e-12)),
                   constraints=TOY_CONS).start
    ro, rr = rows_by_name(orig), rows_by_name(ren)
    assert set(rr) == {REN[n] for n in ro}
    for n, r in ro.items():
        s = rr[REN[n]]
        for f in ("gm_id_lo", "gm_id_hi", "gm_id_chosen", "l_lo", "l_hi", "l_chosen", "i_start", "ln_idu", "w_m"):
            assert _close(getattr(r, f), getattr(s, f)), (n, f, getattr(r, f), getattr(s, f))
        assert r.bin == s.bin
        assert sorted(b.source for b in r.sources) == sorted(b.source for b in s.sources)
        assert r.inactive_reasons == s.inactive_reasons
    assert _close(orig.area_est_m2, ren.area_est_m2)
    assert [x.t for x in orig.ladder] == [x.t for x in ren.ladder]


def test_without_s1v_start_is_none_and_layer0_uses_box_centre():
    c = toy_case(cs_chain(2), elements=TOY_ELS, constraints=TOY_CONS)
    sctx = build_search_context(c.kctx, c.spec, c.settings, None, c.pdk, c.rule)
    assert sctx.start is None
    res = layer0_start(sctx)
    assert res.origin_point in (None, "centre") or res.origin_point.startswith(("halton:", "repair:"))
    assert not str(res.origin_point).startswith("ladder")
