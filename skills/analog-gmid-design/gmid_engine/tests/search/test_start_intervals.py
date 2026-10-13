"""search/start_intervals.py -- `start_intervals(s1v, ach, kctx, spec, pdk_decl, domain) -> StartIntervals` + 층 0 배선
[U17 ①-b] 계산 블록 `start_intervals(snapshot, spec, inputs, pdk_decl, lut)` -> S0 수준 필드 `device: start.row·start.point`, `graph/start: conflicts·inactive·macro·
rungs·records·area_est_m2·area_fraction·uncovered`(설계 40 v1.9.1 §2.4.8 D3). 옛 `StartIntervals` 칸은 u13_hand `StartRead` 가 그 필드에서 읽는다
(theta·cells·current_ref = rungs 칸 0, ladder = rungs). 'S1v 가 없으면 start None' = S1v 뷰 필드가 없는 S0 수준 스냅샷이면 `graph/start` 레코드가 없다.
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
import dataclasses
import json
import math

import pytest

from gmid_engine.search import ACCEPTED_STATUSES, build_search_context, evaluate, layer0_start

from .conftest import CODE_FP
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


def test_without_s1v_start_is_none_and_layer0_uses_box_centre(tmp_path):
    # [U17 ①-b] S1v 필드가 없는 S0 수준 스냅샷(build_s1 만) -> 출발 구간 블록을 부르지 않아 graph/start 레코드·사다리가 없다.
    from gmid_engine.authoring import load_topology
    from gmid_engine.graph import build_s1
    from gmid_engine.sizing import build_kernel_context, dc_inputs_from_spec
    from metrics.gb4_hand import write_case
    from .u13_hand import start_of
    c = toy_case(cs_chain(2), elements=TOY_ELS, constraints=TOY_CONS)
    tp, _sp = write_case(tmp_path, cs_chain(2), elements=TOY_ELS, constraints=TOY_CONS, count_budget=10 ** 6)
    inputs = dc_inputs_from_spec(c.spec)
    kctx = build_kernel_context(build_s1(load_topology(str(tp)), dict(inputs.supplies_v)), inputs, c.kctx.lut)
    sctx = build_search_context(kctx, c.spec, c.settings, None, c.pdk, c.rule, code_fp=CODE_FP)
    assert start_of(sctx) is None and sctx.rungs is None
    res = layer0_start(sctx)
    assert res.origin_point in (None, "centre") or res.origin_point.startswith(("halton:", "repair:"))
    assert not str(res.origin_point).startswith("ladder")


def _reachable_dataclass_types(roots, skip=()):
    """값들에서 닿는 dataclass 인스턴스의 타입 집합(필드 값·tuple·list·frozenset·dict 값을 따라 내려간다). `skip` 타입은 세지 않고 안으로만 간다."""
    import dataclasses as _dc
    seen, found, stack = set(), set(), list(roots)
    while stack:
        v = stack.pop()
        if id(v) in seen:
            continue
        seen.add(id(v))
        if _dc.is_dataclass(v) and not isinstance(v, type):
            if type(v) not in skip:
                found.add(type(v))
            stack.extend(getattr(v, f.name) for f in _dc.fields(v))
        elif isinstance(v, (tuple, list, frozenset, set)):
            stack.extend(v)
        elif hasattr(v, "items") and hasattr(v, "keys"):
            stack.extend(v.values())
            stack.extend(v.keys())
    return found


# ---------- [U17 ①-a 통합] metrics·search 묶음을 필드로 풀었을 때 닿는 값 형식이 등록부에 있다(design 40 §2.4.2·§2.4.3) ----------
# 묶음 Achievability(GB4)·StartIntervals(출발 구간)는 필드로 풀고, 그 필드 값에서 닿는 frozen dataclass 는 코덱이 받아야 한다(목록 밖 = 거부).
# 독립 도출: 실제 단계 A·B·출발 구간 산출물을 걸어 닿는 타입을 모은다(구현 등록 목록을 쓰지 않는다).


# [U17 ①-b] 묶음은 없어졌다 -- 필드 목록은 설계 40 v1.9.1 §2.4.8 GB4 행(D2)·출발 구간 행(D3) 그대로(구현 목록을 쓰지 않는다).
ACH_FIELDS = ("curve_checks", "gain_checks", "area_bound", "headroom_rows", "buffer_window_report", "warnings", "reasons", "verdict", "dof",
              "count_budget", "local_inputs")
START_GRAPH_FIELDS = ("conflicts", "inactive", "macro", "rungs", "records", "area_est_m2", "area_fraction", "uncovered")
START_DEVICE_FIELDS = ("start.row", "start.point")


def _assert_bundle_values_registered(ach, start):
    import gmid_engine.pipeline  # noqa: F401
    from gmid_engine.core.type_registry import type_registry
    names = set(type_registry().names())
    values = [ach.value("graph", "ach", f) for f in ACH_FIELDS]
    values += [start.snapshot.value("graph", "start", f) for f in START_GRAPH_FIELDS]
    values += [v for f in START_DEVICE_FIELDS for _n, v in start.snapshot.column("device", f)]
    reach = _reachable_dataclass_types(values)
    missing = sorted(t.__module__ + "." + t.__qualname__ for t in reach if t.__module__ + "." + t.__qualname__ not in names)
    assert not missing, "S0 수준 필드 값 형식인데 등록부에 없다(코덱이 거부): %s" % missing
    return reach


def test_toy_ach_and_start_value_types_are_registered():
    c = toy_case(cs_chain(2), elements=TOY_ELS, constraints=TOY_CONS)
    reach = _assert_bundle_values_registered(c.ach, c.start)
    assert {t.__name__ for t in reach} >= {"StartRow"}, sorted(t.__name__ for t in reach)


@pytest.mark.parametrize("name", REAL)
def test_real_ach_and_start_value_types_are_registered(name):
    c = real_case(name)
    _assert_bundle_values_registered(c.ach, c.start)
