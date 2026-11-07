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

from gmid_engine.search import ACCEPTED_STATUSES, build_search_context, layer0_start
from .conftest import evaluate      # [FS-1 서명 맞춤] 손 wf 를 끼운 evaluate 래퍼

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


def test_without_s1v_view_wf_start_still_exists_and_initial_wf_is_defined(tmp_path):
    # [FS-1 A-196 판정 S2·#8-1(a)] 옛 `test_without_s1v_start_is_none_and_layer0_uses_box_centre` 는 RETIRED(대상 소멸: 옛 단언 '뷰 없음 -> graph/start 없음·상자 중심'은
    # as-built 동작이었고 DEC-108 상 w_f 는 모든 평가의 입력이라 `start_intervals` 가 뷰 유무와 무관하게 늘 돈다 -- interface §3.4, 원래 취지와 다름).
    # 대체 단언: S1v 뷰 없는 회로에도 `wf_start` 가 있고 `initial_wf` != None, 층 0 출발은 상자 중심 또는 출발 사다리(oracle (d): 판정 S2 결론).
    # [U17 ①-b] S1v 필드가 없는 S0 수준 스냅샷(build_s1 만).
    from gmid_engine.authoring import load_topology
    from gmid_engine.graph import build_s1
    from gmid_engine.sizing import build_kernel_context, dc_inputs_from_spec
    from metrics.gb4_hand import write_case
    from .u13_hand import start_of
    c = toy_case(cs_chain(2), elements=TOY_ELS, constraints=TOY_CONS)
    tp, _sp = write_case(tmp_path, cs_chain(2), elements=TOY_ELS, constraints=TOY_CONS, count_budget=10 ** 6)
    inputs = dc_inputs_from_spec(c.spec)
    from gmid_engine.search import open_run
    donors, counters = open_run()          # [XRUN-F1 card B C0·C6] S1v 없는 커널 컨텍스트 = 새 실행 하나
    kctx = build_kernel_context(build_s1(load_topology(str(tp)), dict(inputs.supplies_v), donors=donors, counters=counters), inputs,
                                c.kctx.lut, donors=donors, counters=counters)
    sctx = build_search_context(kctx, c.spec, c.settings, None, c.pdk, c.rule, code_fp=CODE_FP)
    wf = initial_wf(sctx.dc.base)
    assert wf is not None and wf.cells_ref is sctx.dc.base.value("graph", "start", "wf_start")
    assert wf.keys == tuple(c.w_key for c in wf.cells_ref)
    res = layer0_start(sctx)
    assert res.start is not None and res.start.wf.keys == wf.keys
    assert res.origin_point == "centre" or res.origin_point.startswith(("ladder:", "ladder_repair:", "halton:", "repair:"))


# =====================================================================================================================
# [FS-1 §3.2·§3.3·§3.4] w_f 칸 폐포·출발 선택 `wf_start_value`, KVL 짝 `kvl_partner`, 멤버 출발 W `member_start_w`, 출발 블록 통합 `wf_start`·`initial_wf`.
# oracle: (손) interface card 20261107-fs1 §3.2~§3.4 표의 손 값 (선택 규칙 (i)(ii)(iii) 를 입력 숫자에서 손으로 적용 -- 피검 함수로 기대값을 만들지 않는다).
# =====================================================================================================================
from gmid_engine.core import StructureUnresolvedError  # noqa: E402
from gmid_engine.search import find_front, initial_wf, member_start_w, start_partner, wf_start_value  # noqa: E402
from gmid_engine.sizing import WfCell  # noqa: E402

_S_GROUPS = (("mirror", ("B", "A"), "derived"), ("mirror", ("B", "C"), "derived"))
_S_MOS = ("A", "B", "C", "D")
_S_POS = {"A": 0, "B": 1, "C": 2, "D": 3}
_S_KIND = {n: "nmos" for n in _S_MOS}
_S_W = {"A": 3.0e-6, "B": 1.5e-6, "C": 2.5e-6, "D": 0.5e-6}
_S_CAND = {"nmos": (50, 100, 200), "pmos": (50, 100, 200)}
_S_REF = {"nmos": 100, "pmos": 100}      # [v6.39.5] S-1~S-10 공통 추가 인자: reference = 그 행의 kind 마다 100, l_defined = 늘 True (그 행들에 "no_partner" 없음 -> 기대 불변)


def _wsv(groups=_S_GROUPS, pos=None, kinds=None, start_w=None, defined=None, reference=None, l_defined=None):
    return wf_start_value(groups, _S_MOS, dict(pos or _S_POS), dict(kinds or _S_KIND), dict(start_w or _S_W), _S_CAND,
                          defined or (lambda name, key: True), dict(_S_REF if reference is None else reference),
                          l_defined or (lambda name, key: True), grid_m=1e-8)


def _cells(out):
    return tuple((c.members, c.w_key) for c in out[0])


def test_s1_closure_of_overlapping_groups_and_selection():
    """S-1: 묶음 (B,A)·(B,C) 폐포 {A,B,C} 한 칸 + D 단독. 손: 칸 (A,B,C) W_c = min(3.0, 1.5, 2.5) µm = 1.5 µm -> key·1e-8 <= 1.5e-6 인 가장 큰 후보 100;
    D: W_c = 0.5 µm -> 50 (50·1e-8 = 5e-7 <= 5e-7)."""
    out = _wsv()
    assert _cells(out) == ((("A", "B", "C"), 100), (("D",), 50)) and out[1] == ()
    assert all(isinstance(c, WfCell) for c in out[0])


def test_s2_not_ratified_groups_are_not_cells():
    """S-2: status review_needed -> 칸 넷 (A,)(B,)(C,)(D,), 키 (200, 100, 200, 50) (각자 W_c 이하 가장 큰 후보)."""
    out = _wsv(groups=tuple((r, m, "review_needed") for r, m, _ in _S_GROUPS))
    assert _cells(out) == ((("A",), 200), (("B",), 100), (("C",), 200), (("D",), 50))
    assert _cells(_wsv())[0][0] == ("A", "B", "C")                                       # 양성 대조: derived 면 폐포


def test_s3_cell_order_follows_canonical_position_not_names():
    """S-3: position 을 뒤집으면 칸 목록 = 첫 멤버 position 오름차순, 멤버 = position 오름차순 (이름 바꿈과 같은 효과)."""
    out = _wsv(pos={"A": 3, "B": 2, "C": 1, "D": 0})
    assert _cells(out) == ((("D",), 50), (("C", "B", "A"), 100))


def test_s4_skip_undefined_candidates():
    """S-4: defined(name, 100) = False -> 칸 (A,B,C): W_c 이하 정의 후보는 50 -> WfCell((A,B,C), 50)."""
    out = _wsv(defined=lambda n, k: k != 100)
    assert _cells(out) == ((("A", "B", "C"), 50), (("D",), 50))


def test_s5_narrower_than_all_candidates_takes_narrowest_defined():
    """S-5: D 의 start_w = 0.3e-6 (모든 후보보다 좁음) -> (ii) 가장 좁은 정의 후보 50."""
    out = _wsv(start_w={**_S_W, "D": 0.3e-6})
    assert _cells(out)[1] == (("D",), 50) and out[1] == ()


def test_s6_no_defined_candidate_is_none_with_record():
    """S-6: S-5 + defined(D, ·) 늘 False -> D 칸 None, records = (("wf_start_undefined", {"members": ("D",), "why": "no_defined_candidate"}),)."""
    out = _wsv(start_w={**_S_W, "D": 0.3e-6}, defined=lambda n, k: n != "D")
    assert _cells(out)[1] == (("D",), None)
    assert out[1] == (("wf_start_undefined", {"members": ("D",), "why": "no_defined_candidate"}),)


@pytest.mark.parametrize("who,why", [("C", "no_member_density"), ("A", "reference_slice_undefined")])
def test_s7_s8_member_why_makes_cell_undefined(who, why):
    """S-7·S-8: 칸 멤버 하나의 start_w 가 why 문자열이면 그 칸 None, 기록 why = 그 문자열 (D 칸은 영향 없음)."""
    out = _wsv(start_w={**_S_W, who: why})
    assert _cells(out) == ((("A", "B", "C"), None), (("D",), 50))
    assert out[1] == (("wf_start_undefined", {"members": ("A", "B", "C"), "why": why}),)


def test_s9_mixed_kind_cell_is_structure_unresolved():
    """S-9: kinds[C] = pmos -> StructureUnresolvedError reason wf_cell_kind_mixed, members (A, B, C)."""
    assert _cells(_wsv())[0][1] == 100                                                   # 양성 대조
    with pytest.raises(StructureUnresolvedError) as ei:
        _wsv(kinds={**_S_KIND, "C": "pmos"})
    d = dict(ei.value.record.detail)
    assert d["reason"] == "wf_cell_kind_mixed" and tuple(d["members"]) == ("A", "B", "C")


def test_s10_deterministic():
    assert _wsv() == _wsv() and _wsv()[1] == ()


# ---------------------------------------------------------------- [v6.39.5] S-11~S-16 짝 없는 단일 멤버 칸 = 기준 폭 슬라이스 출발
# oracle (식) interface §3.2 선택 1·2·3 + 기록 꼴: 입력 숫자에서 손으로 적용(피검 함수로 기대값을 만들지 않는다). 대조값: S-1 의 D 칸 W 기준 선택은 50(0.5 µm) 이므로
# 기준 폭(100)과 값이 갈린다 -- '기준 폭을 썼다'를 W 기준 선택과 구별한다.
_S_NOPARTNER_D = {**_S_W, "D": "no_partner"}


def test_s11_single_member_no_partner_cell_starts_at_reference_slice_without_voltage_judgement():
    """S-11: D(단일 멤버, no_partner) 칸 = reference[nmos] = 100, defined(D, ·) 가 모두 False 여도 기준 폭(전압 판정을 쓰지 않음). A·B·C 칸은 S-1 그대로(100)."""
    out = _wsv(start_w=_S_NOPARTNER_D, defined=lambda n, k: n != "D", reference={"nmos": 100}, l_defined=lambda n, k: True)
    assert _cells(out) == ((("A", "B", "C"), 100), (("D",), 100))
    assert out[1] == (("wf_start_reference", {"members": ("D",), "w_key": 100}),)
    assert _cells(_wsv())[1] == (("D",), 50)                                              # 대조: D 의 W 기준 선택(S-1)은 50 -- 기준 폭과 다르다


def test_s12_reference_outside_candidates_is_undefined():
    """S-12: reference = {nmos: 150} (candidates (50, 100, 200) 밖) -> D 칸 None, why reference_start_undefined."""
    out = _wsv(start_w=_S_NOPARTNER_D, reference={"nmos": 150})
    assert _cells(out) == ((("A", "B", "C"), 100), (("D",), None))
    assert out[1] == (("wf_start_undefined", {"members": ("D",), "why": "reference_start_undefined"}),)


def test_s13_reference_slice_outside_l_axis_is_undefined():
    """S-13: l_defined(D, 100) = False -> S-12 와 같은 D 칸·기록."""
    out = _wsv(start_w=_S_NOPARTNER_D, reference={"nmos": 100}, l_defined=lambda n, k: not (n == "D" and k == 100))
    assert _cells(out) == ((("A", "B", "C"), 100), (("D",), None))
    assert out[1] == (("wf_start_undefined", {"members": ("D",), "why": "reference_start_undefined"}),)


def test_s14_multi_member_cell_without_partner_is_undefined_not_reference():
    """S-14: 다멤버 칸 (A,B,C) 에서 C 가 no_partner -> 칸 None, why no_member_partner (기준 폭 대체 0: wf_start_reference 기록 0). D 칸 = 50 (S-1 그대로)."""
    out = _wsv(start_w={**_S_W, "C": "no_partner"}, reference={"nmos": 100}, l_defined=lambda n, k: True)
    assert _cells(out) == ((("A", "B", "C"), None), (("D",), 50))
    assert out[1] == (("wf_start_undefined", {"members": ("A", "B", "C"), "why": "no_member_partner"}),)
    assert not [r for r in out[1] if r[0] == "wf_start_reference"]


def test_s15_no_current_is_not_a_reference_start():
    """S-15: D 의 start_w = no_member_density (전류 없음) -> D 칸 None, why no_member_density -- l_defined 가 True 여도 기준 폭 대체 0."""
    out = _wsv(start_w={**_S_W, "D": "no_member_density"}, reference={"nmos": 100}, l_defined=lambda n, k: True)
    assert _cells(out) == ((("A", "B", "C"), 100), (("D",), None))
    assert out[1] == (("wf_start_undefined", {"members": ("D",), "why": "no_member_density"}),)


def test_s16_reference_start_uses_l_defined_once_and_never_defined():
    """S-16 (구조): S-11 을 호출 기록 spy(test 쪽 함수)로 -> l_defined 호출 = ((D, 100),) 한 번, defined 호출 인자에 이름 D 0 (A·B·C 는 호출됨 -- 양성 대조)."""
    l_calls, d_calls = [], []

    def l_defined(name, key):
        l_calls.append((name, key))
        return True

    def defined(name, key):
        d_calls.append((name, key))
        return name != "D"
    out = _wsv(start_w=_S_NOPARTNER_D, defined=defined, reference={"nmos": 100}, l_defined=l_defined)
    assert _cells(out) == ((("A", "B", "C"), 100), (("D",), 100))
    assert l_calls == [("D", 100)]
    assert d_calls and not [c for c in d_calls if c[0] == "D"] and {c[0] for c in d_calls} == {"A", "B", "C"}


# ---------------------------------------------------------------- [v6.39.5] K-1~K-7·Y-1~Y-6 start_partner (KVL 짝 ∪ 대칭 짝)
# oracle (식) interface §3.3 정의: KVL 후보 = writers 에 들고 gate·source·bulk·kind 가 name 과 모두 같고 length 가 `==` 인 o (position 최소), 없을 때만 대칭 후보
# (role diff_pair/branch_symmetric ∧ status derived/ratified 인 묶음의 다른 멤버 가운데 writers, position 최소). 입력 숫자에서 손으로 적용한 값.
_K_POS = {"A": 0, "B": 1, "C": 2, "E": 3, "P": 4, "Q": 5, "R": 6}


def _sp(name, mos, *, gate=None, source=None, bulk=None, kind=None, length=None, writers=(), groups=(), position=None):
    """공통 입력(표기 없으면): position = _K_POS 의 그 행 mos 몫, kind 모두 nmos, bulk 모두 s0, length 모두 1e-6, groups = (). gate·source 는 호출 쪽이 정한다(없으면 모두 g·s)."""
    mos = tuple(mos)
    return start_partner(name, mos, dict(position or {n: _K_POS[n] for n in mos}), dict(gate or {n: "g" for n in mos}),
                         dict(source or {n: "s" for n in mos}), dict(bulk or {n: "s0" for n in mos}), dict(kind or {n: "nmos" for n in mos}),
                         dict(length or {n: 1e-6 for n in mos}), set(writers), tuple(groups))


def test_k1_partner_is_writer_with_same_gate_source_bulk_kind():
    assert _sp("B", ("A", "B"), writers={"A"}) == "A"


def test_k2_gate_only_shared_has_no_partner():
    assert _sp("B", ("A", "B"), writers={"A"}) == "A"                                    # 양성 대조
    assert _sp("B", ("A", "B"), writers={"A"}, source={"A": "s", "B": "s2"}) is None


def test_k3_declared_bulk_differs_has_no_partner():
    assert _sp("B", ("A", "B"), writers={"A"}, bulk={"A": "s0", "B": "s1"}) is None


def test_k3b_kind_differs_has_no_partner():
    """interface §3.3 'gate·source·bulk·kind 가 name 과 모두 같고' 의 kind 항."""
    assert _sp("B", ("A", "B"), writers={"A"}, kind={"A": "nmos", "B": "pmos"}) is None


def test_k4_no_writers_no_partner():
    assert _sp("B", ("A", "B"), writers=()) is None


def test_k5_length_differs_has_no_partner():
    """K-5 (c) L 만 다름: length[A] = 2e-6 -> None."""
    assert _sp("B", ("A", "B"), writers={"A"}) == "A"                                    # 양성 대조
    assert _sp("B", ("A", "B"), writers={"A"}, length={"A": 2e-6, "B": 1e-6}) is None


def test_k5b_length_comparison_has_zero_tolerance():
    """K-5b (c) 허용오차 0: length[A] = nextafter(1e-6, 1.0) (1 ulp 위) -> None."""
    assert _sp("B", ("A", "B"), writers={"A"}, length={"A": math.nextafter(1e-6, 1.0), "B": 1e-6}) is None


def test_k6_partner_is_not_limited_to_the_cell():
    """K-6 (c) 칸 무관: A 는 B 가 든 칸 ((B, C) mirror) 밖이어도 KVL 짝이다."""
    assert _sp("B", ("A", "B", "C"), writers={"A"}, groups=(("mirror", ("B", "C"), "derived"),)) == "A"


def test_k7_canonical_order_picks_minimum_position_not_name():
    """K-7: 후보 A·E 모두 KVL 짝 -> position 최소. position {A: 2, B: 1, E: 0} 이면 E, {A: 0, B: 1, E: 2} 이면 A (이름 무관 -- 위치만)."""
    assert _sp("B", ("A", "B", "E"), writers={"A", "E"}, position={"A": 2, "B": 1, "E": 0}) == "E"
    assert _sp("B", ("A", "B", "E"), writers={"A", "E"}, position={"A": 0, "B": 1, "E": 2}) == "A"


_Y_GATE = {"P": "g1", "Q": "g2"}
_Y_SRC = {"P": "s", "Q": "s"}


def test_y1_diff_pair_symmetric_partner_when_no_kvl_candidate():
    """Y-1: 차동쌍 (P, Q) derived, gate 다름(KVL 후보 0), writers {P}, name Q -> P."""
    assert _sp("Q", ("P", "Q"), gate=_Y_GATE, source=_Y_SRC, writers={"P"}, groups=(("diff_pair", ("P", "Q"), "derived"),)) == "P"


def test_y2_branch_symmetric_role_gives_symmetric_partner():
    assert _sp("Q", ("P", "Q"), gate=_Y_GATE, source=_Y_SRC, writers={"P"}, groups=(("branch_symmetric", ("P", "Q"), "derived"),)) == "P"


def test_y2b_ratified_status_gives_symmetric_partner():
    assert _sp("Q", ("P", "Q"), gate=_Y_GATE, source=_Y_SRC, writers={"P"}, groups=(("diff_pair", ("P", "Q"), "ratified"),)) == "P"


def test_y3_review_needed_status_gives_no_symmetric_partner():
    assert _sp("Q", ("P", "Q"), gate=_Y_GATE, source=_Y_SRC, writers={"P"}, groups=(("diff_pair", ("P", "Q"), "derived"),)) == "P"   # 양성 대조
    assert _sp("Q", ("P", "Q"), gate=_Y_GATE, source=_Y_SRC, writers={"P"}, groups=(("diff_pair", ("P", "Q"), "review_needed"),)) is None


def test_y4_mirror_role_is_not_a_symmetric_partner():
    assert _sp("Q", ("P", "Q"), gate=_Y_GATE, source=_Y_SRC, writers={"P"}, groups=(("mirror", ("P", "Q"), "derived"),)) is None


def test_y5_kvl_partner_wins_over_symmetric_partner():
    """Y-5: KVL 짝 R (Q 와 gate g2·source s 같음) vs 대칭 짝 P (position 이 앞섬) -> R."""
    got = _sp("Q", ("P", "Q", "R"), gate={"P": "g1", "Q": "g2", "R": "g2"}, source={"P": "s", "Q": "s", "R": "s"}, writers={"P", "R"},
              groups=(("diff_pair", ("P", "Q"), "derived"),), position={"P": 0, "Q": 1, "R": 2})
    assert got == "R"


def test_y6_symmetric_candidates_pick_minimum_position():
    """Y-6: branch_symmetric (Q, P, R) ratified, writers {P, R}, position {P: 5, Q: 0, R: 1} -> 위치 최소 R (멤버 나열 순서·이름 무관)."""
    got = _sp("Q", ("P", "Q", "R"), gate={"P": "g1", "Q": "g2", "R": "g3"}, source={"P": "s", "Q": "s", "R": "s"}, writers={"P", "R"},
              groups=(("branch_symmetric", ("Q", "P", "R"), "ratified"),), position={"P": 5, "Q": 0, "R": 1})
    assert got == "R"


# ---------------------------------------------------------------- W-1~W-4 member_start_w
def _msw(partner=None, current=None, ln_idu=None):
    return member_start_w(("A", "B"), {"A"}, {"B": "A"} if partner is None else partner,
                          {"A": 1e-6, "B": 2e-6} if current is None else current, {"A": 1e-6, "B": 1e-6},
                          {"A": math.log(4.0)} if ln_idu is None else ln_idu)


def test_w1_dependent_member_uses_partner_density():
    """W-1: 쓰기 A = I·L/exp(ln IDu), 종속 B = I_B·L_B/exp(ln IDu_A) (이 연산 순서, 비교 `==`)."""
    out = _msw()
    assert out == {"A": 1e-6 * 1e-6 / math.exp(math.log(4.0)), "B": 2e-6 * 1e-6 / math.exp(math.log(4.0))}
    assert out["B"] == pytest.approx(5e-13, rel=1e-12)


def test_w2_no_partner_is_the_no_partner_marker():
    """W-2 [v6.39.5 기대 바뀜]: partner = {B: None}(gate만 공유 -- K-2 꼴) -> B = "no_partner"(옛 기대 "no_member_density" 아님), A 값 그대로."""
    out = _msw(partner={"B": None})
    assert out["B"] == "no_partner" and out["A"] == 1e-6 * 1e-6 / math.exp(math.log(4.0))


def test_w5_missing_current_is_checked_before_missing_partner():
    """W-5: W-2 입력에서 current[B] = None 이기도 하면 -> B = "no_member_density"(전류 없음이 먼저)."""
    out = _msw(partner={"B": None}, current={"A": 1e-6, "B": None})
    assert out["B"] == "no_member_density" and out["A"] == 1e-6 * 1e-6 / math.exp(math.log(4.0))


def test_w3_missing_current_is_no_member_density():
    assert _msw()["B"] != "no_member_density"                                            # 양성 대조
    assert _msw(current={"A": 1e-6, "B": None})["B"] == "no_member_density"


def test_w4_reference_slice_undefined_propagates_to_dependent():
    out = _msw(ln_idu={"A": "reference_slice_undefined"})
    assert out == {"A": "reference_slice_undefined", "B": "reference_slice_undefined"}


# ---------------------------------------------------------------- S-B 출발 블록 통합 (운영 경로)
# 손 toy: 거울 부하 증폭단 -- MN1 nmos (a, in, gnd), MP1 pmos 다이오드 (a, a, vdd), MP2 pmos (out, a, vdd), MN2 nmos 싱크 (out, nb, gnd), CL (out, gnd).
# 실측(탐색 때 스냅샷): graph.matching_groups = mirror (MP1, MP2) derived, dc_coord MP1 writer·MP2 dependent(partner MP1). 이 전제는 test 안에서 단언한다.
FS1_PORTS = {"in": ("input", "single_ended_input"), "out": ("output", "single_ended_output")}
FS1_ELS = (("CL", "capacitor", 1e-12),)


def fs1_mirror_load():
    from metrics.gb4_hand import mos_e, topology, two_e
    devs = [mos_e("MN1", "nmos", "a", "in", "gnd"), mos_e("MP1", "pmos", "a", "a", "vdd"),
            mos_e("MP2", "pmos", "out", "a", "vdd"), mos_e("MN2", "nmos", "out", "nb", "gnd")]
    return topology("fs1mir", devs, ports=FS1_PORTS, passives=[two_e("CL", "capacitor", "out", "gnd")], bias=["nb"])


def _hand_closure(base):
    """손 폐포: matching_groups(role ∈ mirror/diff_pair/branch_symmetric, status ∈ derived/ratified) 소자 공유 합집합 + 묶음 밖 MOS 하나씩 -> frozenset 집합."""
    from gmid_engine.graph import GRAPH_KEY
    names = [n for n, k in base.column("device", "kind") if k in ("nmos", "pmos")]
    parent = {n: n for n in names}

    def find(x):
        while parent[x] != x:
            x = parent[x]
        return x
    for g in base.value("graph", GRAPH_KEY, "matching_groups"):
        if g.kind in ("mirror", "diff_pair", "branch_symmetric") and g.status in ("derived", "ratified"):
            for m in g.members[1:]:
                parent[find(m)] = find(g.members[0])
    comps = {}
    for n in names:
        comps.setdefault(find(n), set()).add(n)
    return {frozenset(v) for v in comps.values()}


@pytest.fixture(scope="module")
def fs1_case():
    return toy_case(fs1_mirror_load(), elements=FS1_ELS, constraints=TOY_CONS, fresh=True)


def test_sb1_wf_start_cells_are_the_matching_closure(fs1_case):
    """S-B1: wf_start 가 있고 칸 구조 = graph.matching_groups 폐포(손), 모든 칸 w_key ∈ 그 kind widths."""
    from gmid_engine.lut import widths
    base = fs1_case.sctx.dc.base
    wf = base.value("graph", "start", "wf_start")
    kinds = dict(base.column("device", "kind"))
    want = _hand_closure(base)
    assert any(len(c) == 2 for c in want)                                                 # 전제: 거울 칸이 있다
    assert {frozenset(c.members) for c in wf} == want
    assert len(wf) == len(want)
    for c in wf:
        assert c.w_key in widths(fs1_case.kctx.lut.memo.lut, kinds[c.members[0]])      # kctx.lut = LutAccess(memo) -- LUT 집합은 memo.lut (M-1)


def test_sb2_second_start_intervals_computes_nothing(fs1_case, tmp_path):
    """S-B2: 같은 donors·counters 로 컨텍스트를 한 번 더 -> start_intervals 계산 0 (reuse), wf_start 같음.
    [FS-1 A-196 판정 #8-2] 출발 블록을 부르는 자리는 단계 B(`run_stage_b`)가 아니라 탐색 컨텍스트 생성이다 -> 둘째 `build_search_context`(같은 donors·counters)로 본다."""
    from .u13_hand import contexts_of, recipe_of
    a, base = fs1_case.a, fs1_case.sctx.dc.base

    def row():
        rows = [r for r in a.counters.snapshot().blocks if (r.block, r.part) == ("start_intervals", "*")]
        assert len(rows) == 1
        return rows[0]
    r1 = row()
    assert r1.computes >= 1
    case2 = contexts_of(recipe_of(a, fs1_case.b, (fs1_case.pdk, fs1_case.rule), fs1_case.settings, fs1_case.lut),
                        kernel=dict(donors=a.donors, counters=a.counters))
    r2 = row()
    assert r2.computes == r1.computes and r2.reuses >= r1.reuses                          # 계산 0
    assert repr(case2.sctx.dc.base.value("graph", "start", "wf_start")) == repr(base.value("graph", "start", "wf_start"))


def test_sb3_initial_wf_reads_the_field_object(fs1_case):
    """S-B3: initial_wf(snapshot).cells_ref is wf_start 값 객체, keys == tuple(c.w_key for c in cells_ref)."""
    base = fs1_case.sctx.dc.base
    got = initial_wf(base)
    cells = base.value("graph", "start", "wf_start")
    assert got is not None and got.cells_ref is cells
    assert got.keys == tuple(c.w_key for c in cells)


def test_sb4_initial_wf_none_when_a_cell_is_undefined(fs1_case):
    """S-B4: wf_start 에 None 칸이 있는 스냅샷 -> initial_wf None (S-6 꼴 입력: 한 칸 w_key None)."""
    base = fs1_case.sctx.dc.base
    cells = base.value("graph", "start", "wf_start")
    broken = (WfCell(cells[0].members, None),) + tuple(cells[1:])

    class Stub:
        def __init__(self, real):
            self._real = real

        def value(self, *path):
            return broken if path == ("graph", "start", "wf_start") else self._real.value(*path)

        def __getattr__(self, name):
            return getattr(self._real, name)
    assert initial_wf(base) is not None                                                   # 양성 대조
    assert initial_wf(Stub(base)) is None


def test_initial_wf_missing_field_is_a_lookup_error_fail_closed(fs1_case):
    """필드 부재는 fail-closed: wf_start 가 없는 스냅샷(단계 A 의 S1 수준) 에서 initial_wf 는 None 으로 넘기지 않고 기존 스냅샷 조회 오류(KeyError)다 (판정 minor 7).
    None 은 칸 None(start_undefined, interface §5) 경우만이다."""
    assert initial_wf(fs1_case.sctx.dc.base) is not None                                  # 양성 대조: 출발 단계를 거친 스냅샷
    with pytest.raises(LookupError):                                                      # KeyError ⊂ LookupError (판정 n-3)
        initial_wf(fs1_case.a.s1.snapshot)


def _spy_start_calls(monkeypatch):
    import inspect
    import sys
    mod = sys.modules["gmid_engine.search.start_intervals"]
    log = {"member_start_w": [], "wf_start_value": [], "matching_bounds": [], "start_partner": []}      # [v6.39.5] 관찰 지점 `.start_partner` (interface §9)
    for name in log:
        orig = getattr(mod, name)
        sig = inspect.signature(orig)

        def make(orig=orig, sig=sig, name=name):
            def spy(*a, **k):
                r = orig(*a, **k)
                log[name].append((dict(sig.bind(*a, **k).arguments), r))
                return r
            return spy
        monkeypatch.setattr(mod, name, make())
    return log


def test_sb5_dependent_mirror_member_start_w_operational_path(monkeypatch):
    """S-B5: 운영 경로 -- (a) member_start_w 1회, 그 current 인자 is matching_bounds 첫 호출의 currents 인자, partner[MP2] == MP1
    (b) 출력[MP2] == current[MP2]·length[MP2]/exp(ln_idu[MP1]) (잡힌 인자로 손 계산 ==) (c) wf_start_value 의 start_w 인자 is member_start_w 출력
    (d) 그 칸 wf_start 키 = 잡힌 start_w·그 kind widths·defined 로 §3.2 선택 규칙을 손으로 적용한 키."""
    from gmid_engine.lut import widths
    log = _spy_start_calls(monkeypatch)
    case = toy_case(fs1_mirror_load(), elements=FS1_ELS, constraints=TOY_CONS, fresh=True)
    base = case.sctx.dc.base
    # 전제 (안 서면 멈추고 보고): 거울 묶음 (MP1, MP2), MP2 종속(partner MP1)
    coord = {n: v for n, v in base.column("device", "dc_coord")}
    assert coord["MP2"].role == "dependent" and coord["MP2"].partner == "MP1" and coord["MP1"].role == "writer"
    assert len(log["member_start_w"]) == 1
    args, out = log["member_start_w"][0]
    assert len(log["matching_bounds"]) >= 1
    assert args["current"] is log["matching_bounds"][0][0]["currents"]                   # (a) 같은 dict 객체
    assert args["partner"]["MP2"] == "MP1"
    cur, length, ln = args["current"], args["length"], args["ln_idu"]
    assert cur["MP2"] is not None
    assert out["MP2"] == cur["MP2"] * length["MP2"] / math.exp(ln["MP1"])                # (b)
    assert len(log["wf_start_value"]) == 1
    wargs, (wcells, _recs) = log["wf_start_value"][0]
    assert wargs["start_w"] is out                                                       # (c)
    # [v6.39.5 보강] start_partner 배선: B(MP2) 호출 한 번, mos 인자 = 그 스냅샷 MOS 전부(칸으로 거르지 않음), length 인자 is member_start_w 의 length 인자,
    # groups 인자 is wf_start_value 의 groups 인자(판정 m-6: 같은 객체), 답 = MP1. 전제 length[MP1] == length[MP2] (안 서면 멈추고 보고).
    sp = [(a, r) for a, r in log["start_partner"] if a["name"] == "MP2"]
    assert len(sp) == 1
    sp_args, sp_out = sp[0]
    all_mos = [n for n, k in base.column("device", "kind") if k in ("nmos", "pmos")]
    assert len(all_mos) == 4 and set(sp_args["mos"]) == set(all_mos) and len(sp_args["mos"]) == len(all_mos)
    assert length["MP1"] == length["MP2"]                                                 # 전제
    assert sp_out == "MP1" and args["partner"]["MP2"] == sp_out
    assert sp_args["length"] is args["length"]
    assert sp_args["groups"] is wargs["groups"]
    # (d) 손 선택: 거울 칸 W_c = min 멤버 출발 W, 가장 큰 key·grid <= W_c (모두 정의 -- 전제)
    cand = wargs["candidates"]["pmos"]
    assert tuple(cand) == tuple(widths(case.kctx.lut.memo.lut, "pmos"))      # M-1
    assert all(wargs["defined"](n, k) for n in ("MP1", "MP2") for k in cand)
    w_c = min(out["MP1"], out["MP2"])
    ok = [k for k in cand if k * wargs["grid_m"] <= w_c]
    want = max(ok) if ok else min(cand)
    got = {c.members: c.w_key for c in base.value("graph", "start", "wf_start")}
    # [FS-1 A-196 판정 #8-3, interface §3.2 S-3] 칸 멤버 순서 = 정준 위치(`dc_colour`) 오름차순이지 이름 순이 아니다: 기대 키를 그 스냅샷 colour 로 손 정렬해 만든다.
    colour = dict(base.column("device", "dc_colour"))
    assert colour["MP1"] != colour["MP2"]
    assert got[tuple(sorted(("MP1", "MP2"), key=lambda n: colour[n]))] == want


# ---------------------------------------------------------------- [v6.39.5] S-B6 짝 없는 다멤버 칸 (운영 경로)
# 옛 S-B6 (gate만 공유 mirror 멤버) 는 손 회로로 서지 않았다(A-178/A-182). v6.39.5 의 새 전제(interface §3.4 S-B6): '칸 멤버 둘 이상 + start_partner 답 None'.
# 이 전제를 만드는 입력 = 거울 부하 증폭단 fs1_mirror_load 의 거울 출력 MP2 에 **선언 bulk 를 따로 둔 별도 레일**(vb2 = 1.5 V, 전원 아래)을 준 toy:
# 단계 A·B 는 base 에서 통과하고 matching_groups = mirror (MP1, MP2) derived·dc_coord MP2 dependent(partner MP1) 로 남는다(base 실측, 격리 복제본 2026-11-08) --
# 짝 정의(KVL 짝은 실효 bulk 넷이 같아야 함, §3.3 K-3)가 MP1(실효 bulk vdd) 과 MP2(vb2) 를 가른다. 그래도 전제가 서지 않으면 단언이 멈춘다.
FS1_SUP_BULK = {"vdd": 1.8, "gnd": 0.0, "vb2": 1.5}


def fs1_mirror_bulk():
    from metrics.gb4_hand import mos_e, topology, two_e
    devs = [mos_e("MN1", "nmos", "a", "in", "gnd"), mos_e("MP1", "pmos", "a", "a", "vdd"),
            dict(mos_e("MP2", "pmos", "out", "a", "vdd"), bulk="vb2"), mos_e("MN2", "nmos", "out", "nb", "gnd")]
    return topology("fs1mirb", devs, ports=FS1_PORTS, passives=[two_e("CL", "capacitor", "out", "gnd")], bias=["nb"], rails=("vdd", "gnd", "vb2"))


def test_sb6_multi_member_cell_without_partner_is_undefined_not_reference_start(monkeypatch):
    """S-B6: (전제) C(MP2) 가 든 칸은 멤버 둘 이상, start_partner spy 의 C 호출 답 = None (회로 전체에 같은 gate·source·bulk·kind·L 쓰기 소자 없음, diff_pair·branch_symmetric 에 안 듦).
    기대: member_start_w 출력[C] == "no_partner", 그 칸 wf_start w_key is None, graph/start records 에 ("wf_start_undefined", (("members", 칸 멤버), ("why", "no_member_partner")))
    (쌍 튜플 꼴 -- m-2; 다멤버 칸이라 기준 폭 대체 0: wf_start_reference 기록에 그 칸 없음), initial_wf -> None, 그 sctx 로 find_front -> O-2 꼴(평가 0)."""
    log = _spy_start_calls(monkeypatch)
    case = toy_case(fs1_mirror_bulk(), elements=FS1_ELS, constraints=TOY_CONS, fresh=True, supplies=FS1_SUP_BULK)
    base = case.sctx.dc.base
    # 전제 (안 서면 멈추고 보고)
    assert len(log["member_start_w"]) == 1
    args, out = log["member_start_w"][0]
    sp = [r for a, r in log["start_partner"] if a["name"] == "MP2"]
    assert sp == [None]                                                                   # start_partner spy 의 C 호출 답 = None
    sp_args = [a for a, _r in log["start_partner"] if a["name"] == "MP2"][0]
    assert not [o for o in sp_args["writers"] if o != "MP2" and sp_args["gate"][o] == sp_args["gate"]["MP2"]
                and sp_args["source"][o] == sp_args["source"]["MP2"] and sp_args["bulk"][o] == sp_args["bulk"]["MP2"]
                and sp_args["kind"][o] == sp_args["kind"]["MP2"] and sp_args["length"][o] == sp_args["length"]["MP2"]]    # 손: KVL 후보 0
    assert not [g for g in sp_args["groups"] if g[0] in ("diff_pair", "branch_symmetric") and "MP2" in g[1]]
    cell = [c for c in base.value("graph", "start", "wf_start") if "MP2" in c.members]
    assert len(cell) == 1 and len(cell[0].members) >= 2
    # 기대
    assert out["MP2"] == "no_partner"
    assert cell[0].w_key is None
    records = case.start.records
    assert ("wf_start_undefined", (("members", cell[0].members), ("why", "no_member_partner"))) in records
    assert not [r for r in records if r[0] == "wf_start_reference" and "MP2" in dict(r[1])["members"]]
    assert initial_wf(base) is None
    k0 = dict(case.sctx.counters)["kernel_calls"]
    fr = find_front(case.sctx, [])
    assert dict(case.sctx.counters)["kernel_calls"] == k0 == 0
    assert [n for n in (dict(x) for x in fr.notes) if n.get("verdict") == "start_undefined"]
    assert fr.front == () and fr.pending_front == () and fr.unmeasured_front == ()


# ---------------------------------------------------------------- [v6.39.5] S-B7 짝 없는 단일 멤버 칸 (운영 경로, A-205 입력 = library 회로)
# toy 에는 이 칸이 없다(고리 등식 종속 소자는 library 회로에서만 생긴다 -- 측정 evidence/2026-11-08/fs1_lcond_measure.md: 7/82칸). 입력 = pushpull_follower_buffer(실 LUT 실경로), X = M2(pmos).
def test_sb7_reference_start_for_single_member_cell_without_partner_operational_path(monkeypatch):
    """S-B7: (전제, 안 서면 멈춤) X(M2) 칸 멤버 1개·비쓰기·start_partner 답 None·current[X] != None; k_ref = lut.cap_map[kind].w_key ∈ widths(lut, kind);
    length[X] 가 lut.slice_map[(kind, k_ref)].grids[0](L 축)의 원소(앵커). 기대: member_start_w 출력[X] == "no_partner", wf_start 칸 (X,) w_key == k_ref,
    graph/start records 에 ("wf_start_reference", (("members", (X,)), ("w_key", k_ref))) 하나, initial_wf 키의 그 칸 값 = k_ref."""
    from gmid_engine.lut import widths
    from .u13_real import real_case
    log = _spy_start_calls(monkeypatch)
    case = real_case("pushpull_follower_buffer")
    base = case.sctx.dc.base
    X, kind = "M2", "pmos"
    lut = case.kctx.lut.memo.lut
    assert dict(base.column("device", "kind"))[X] == kind
    assert log["member_start_w"], "출발 블록이 이 실행에서 계산되지 않았다"
    args, out = log["member_start_w"][-1]
    sp = [(a, r) for a, r in log["start_partner"] if a["name"] == X]
    assert sp, "start_partner 가 X 에 불리지 않았다"
    sp_args, sp_out = sp[-1]
    wf = base.value("graph", "start", "wf_start")
    cell = [c for c in wf if X in c.members]
    assert len(cell) == 1 and cell[0].members == (X,)                                    # 전제: 칸 멤버 1개
    assert X not in sp_args["writers"] and sp_out is None                                # 전제: 비쓰기, 짝 없음
    assert args["current"][X] is not None
    k_ref = lut.cap_map[kind].w_key
    assert k_ref in widths(lut, kind)
    assert any(l == args["length"][X] for l in lut.slice_map[(kind, k_ref)].grids[0])    # 전제: 앵커
    # 기대
    assert out[X] == "no_partner"
    assert cell[0].w_key == k_ref
    recs = [r for r in case.start.records if r[0] == "wf_start_reference" and dict(r[1])["members"] == (X,)]
    assert recs == [("wf_start_reference", (("members", (X,)), ("w_key", k_ref)))]
    got = initial_wf(base)
    assert got is not None and got.keys[list(wf).index(cell[0])] == k_ref

# ---------------------------------------------------------------- [v6.39.5] S-B8 뷰 없는 회로 (늘 실행)
# 입력: 선언 이상 전류원 둘(I1, I2)로만 바이어스가 정해지는 toy -- 직렬 가지 M1(drain out)·M2(source gnd)는 I1 하나를 나르고, M3(입력 CS)는 I2 를 나른다.
# 입력 포트 in 은 M3 게이트, 출력 포트 out 은 M1 드레인이라 in -> out 신호 경로가 없다(base 실측: S1v views = transfer:0 한 개, blocks 비어 있음).
FS1_I1, FS1_I2 = 2e-6, 1e-6


def fs1_no_view_toy():
    from metrics.gb4_hand import mos_e, topology, two_e
    devs = [mos_e("M1", "nmos", "out", "vb1", "m"), mos_e("M2", "nmos", "m", "vb2", "gnd"), mos_e("M3", "nmos", "d3", "in", "gnd")]
    srcs = [{"name": "I1", "kind": "current_source", "terminals": ["vdd", "out"]}, {"name": "I2", "kind": "current_source", "terminals": ["vdd", "d3"]}]
    return topology("fs1nov", devs, ports=FS1_PORTS, passives=[two_e("CL", "capacitor", "out", "gnd")], sources=srcs, bias=["vb1", "vb2"])


FS1_NOV_ELS = (("CL", "capacitor", 1e-12), ("I1", "current_source", FS1_I1), ("I2", "current_source", FS1_I2))


def test_sb8_circuit_without_a_transfer_view_still_has_a_wf_start(monkeypatch):
    """S-B8 (d): (전제) transfer 뷰(blocks 비어 있지 않은 것) 0; 모든 MOS 에서 member_start_w spy 의 current[n] == 손 KCL 값(직렬 가지 = 그 이상원 값 그대로, 자리값이 끼면 멈춤).
    기대 (a) start_intervals 블록 계산 1회 (b) wf_start 칸 구조 = 손 폐포, 모든 칸 w_key is not None (c) initial_wf 가 None 아님, keys == tuple(c.w_key ...)
    (d) 그 sctx 의 층 0 출발점 wf.keys = (c) keys, find_front 는 O-2 꼴(평가 0)이 아님 (e) graph/start inactive 에 뷰 의존 비활성 항목 기록, 5a 관련 비활성 0.
    (e) 기록 이름(card A-205 확정): (v1) `pole0_view_inactive`, (v2) `gain_l_6.4_1`, (v3) `speed_view_inactive`, (v4) `macro_inactive`, (v5) `noise_guard_7.5`, (v6) `ff_start_view_inactive`."""
    log = _spy_start_calls(monkeypatch)
    case = toy_case(fs1_no_view_toy(), elements=FS1_NOV_ELS, constraints=TOY_CONS, fresh=True)
    base = case.sctx.dc.base
    # 전제
    assert not [v for v in case.s1v.views if v.id.startswith("transfer") and v.blocks]
    assert len(log["member_start_w"]) == 1
    cur = log["member_start_w"][0][0]["current"]
    hand_kcl = {"M1": FS1_I1, "M2": FS1_I1, "M3": FS1_I2}                                  # 손 KCL: 직렬 M1·M2 = I1, M3 = I2 (미러 분기 없음)
    assert {n: cur[n] for n in hand_kcl} == hand_kcl and set(cur) == set(hand_kcl)
    # (a) 같은 sctx 조립에서 블록 계산 1회
    rows = [r for r in case.a.counters.snapshot().blocks if (r.block, r.part) == ("start_intervals", "*")]
    assert len(rows) == 1 and rows[0].computes == 1
    # (b)
    wf = base.value("graph", "start", "wf_start")
    assert {frozenset(c.members) for c in wf} == _hand_closure(base) and len(wf) == 3
    assert all(c.w_key is not None for c in wf)
    # (c)
    got = initial_wf(base)
    assert got is not None and got.keys == tuple(c.w_key for c in wf)
    # (d)
    from gmid_engine.search import layer0_start
    res = layer0_start(case.sctx)
    assert res.start is not None and res.start.wf.keys == got.keys
    fr = find_front(case.sctx, [])
    assert dict(case.sctx.counters)["kernel_calls"] > 0
    assert not [n for n in (dict(x) for x in fr.notes) if n.get("verdict") == "start_undefined"]
    # (e)
    inactive = case.start.inactive
    names = {n for n, _r in inactive}
    # [A-205] card 가 정한 이름 정확 단언: (v1) pole0_view_inactive (v2) gain_l_6.4_1 (v3) speed_view_inactive (v4) macro_inactive (v5) noise_guard_7.5 (v6) ff_start_view_inactive
    assert {"pole0_view_inactive", "gain_l_6.4_1", "speed_view_inactive", "noise_guard_7.5", "ff_start_view_inactive"} <= names
    assert "macro_inactive" in names | {r[0] for r in case.start.records}
    assert not [n for n in names if "wf" in str(n)]


# ---------------------------------------------------------------- [v6.39.5] S-B9 대칭 짝 (운영 경로)
# 입력: 차동 입력(inp/inn) 5T OTA -- 차동쌍 MN1·MN2 (게이트 다름, 공통 소스 t), 거울 부하 MP1·MP2, 꼬리 MT. base 실측(격리 복제본 2026-11-08): matching_groups =
# mirror (MP1, MP2) derived + diff_pair (MN1, MN2) derived, dc_coord MN2 dependent(partner MN1), MN1 writer. MN2 와 gate·source 가 같은 쓰기 소자는 회로에 없다
# (MN1 게이트 inp, MT 소스 gnd) -> KVL 후보 0, 대칭 짝 = MN1.
def fs1_diff_ota():
    from metrics.gb4_hand import mos_e, topology, two_e
    ports = {"inp": ("input", "differential_input_p"), "inn": ("input", "differential_input_n"), "out": ("output", "single_ended_output")}
    devs = [mos_e("MN1", "nmos", "a", "inp", "t"), mos_e("MN2", "nmos", "out", "inn", "t"), mos_e("MP1", "pmos", "a", "a", "vdd"),
            mos_e("MP2", "pmos", "out", "a", "vdd"), mos_e("MT", "nmos", "t", "nb", "gnd")]
    return topology("fs1dota", devs, ports=ports, passives=[two_e("CL", "capacitor", "out", "gnd")], bias=["nb"])


def test_sb9_symmetric_partner_gives_the_dependent_pair_member_a_start_width(monkeypatch):
    """S-B9: (전제) diff_pair 묶음의 한 멤버 Q(MN2) 비쓰기·다른 멤버 P(MN1) 쓰기, Q 와 gate·source·bulk·kind·L 이 같은 쓰기 소자 없음.
    기대: start_partner spy 의 Q 답 = "P", member_start_w 출력[Q] == current[Q]·length[Q]/exp(ln_idu[P]) (잡힌 인자로 ==), 그 칸 w_key is not None (출발 불능 0)."""
    log = _spy_start_calls(monkeypatch)
    case = toy_case(fs1_diff_ota(), elements=FS1_ELS, constraints=TOY_CONS, fresh=True)
    base = case.sctx.dc.base
    coord = dict(base.column("device", "dc_coord"))
    assert coord["MN2"].role == "dependent" and coord["MN1"].role == "writer"             # 전제
    assert len(log["member_start_w"]) == 1
    args, out = log["member_start_w"][0]
    sp = [(a, r) for a, r in log["start_partner"] if a["name"] == "MN2"]
    assert len(sp) == 1
    sp_args, sp_out = sp[0]
    assert not [o for o in sp_args["writers"] if o != "MN2" and sp_args["gate"][o] == sp_args["gate"]["MN2"]
                and sp_args["source"][o] == sp_args["source"]["MN2"] and sp_args["bulk"][o] == sp_args["bulk"]["MN2"]
                and sp_args["kind"][o] == sp_args["kind"]["MN2"] and sp_args["length"][o] == sp_args["length"]["MN2"]]    # 전제: KVL 후보 0 (손)
    assert [g for g in sp_args["groups"] if g[0] == "diff_pair" and set(g[1]) == {"MN1", "MN2"}]                          # 전제: 대칭 묶음
    assert "MN1" in sp_args["writers"] and "MN2" not in sp_args["writers"]
    # 기대
    assert sp_out == "MN1" and args["partner"]["MN2"] == "MN1"
    cur, length, ln = args["current"], args["length"], args["ln_idu"]
    assert cur["MN2"] is not None and not isinstance(ln["MN1"], str)
    assert out["MN2"] == cur["MN2"] * length["MN2"] / math.exp(ln["MN1"])
    cell = [c for c in base.value("graph", "start", "wf_start") if "MN2" in c.members]
    assert len(cell) == 1 and cell[0].w_key is not None

# [xrun] 옛 '[U17 ①-a 통합] 묶음 필드 값 형식이 타입 등록부에 있다' test 2개(toy·실경로)와 그 helper 를 지웠다 -- 설계 40 v1.10 §2.4.3
# '타입 등록부' 삭제 행과 test 변경 목록('타입 등록부 이름을 읽는 단언 search/test_start_intervals.py:216-217 ... 그 단언을 지운다'):
# 등록부의 소비자는 디스크 S0 코덱뿐이었고 코덱이 없어졌다.
