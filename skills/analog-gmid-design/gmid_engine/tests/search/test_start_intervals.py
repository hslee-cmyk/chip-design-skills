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
    from gmid_engine.search import open_run
    donors, counters = open_run()          # [XRUN-F1 card B C0·C6] S1v 없는 커널 컨텍스트 = 새 실행 하나
    kctx = build_kernel_context(build_s1(load_topology(str(tp)), dict(inputs.supplies_v), donors=donors, counters=counters), inputs,
                                c.kctx.lut, donors=donors, counters=counters)
    sctx = build_search_context(kctx, c.spec, c.settings, None, c.pdk, c.rule, code_fp=CODE_FP)
    assert start_of(sctx) is None and sctx.rungs is None
    res = layer0_start(sctx)
    assert res.origin_point in (None, "centre") or res.origin_point.startswith(("halton:", "repair:"))
    assert not str(res.origin_point).startswith("ladder")


# =====================================================================================================================
# [FS-1 §3.2·§3.3·§3.4] w_f 칸 폐포·출발 선택 `wf_start_value`, KVL 짝 `kvl_partner`, 멤버 출발 W `member_start_w`, 출발 블록 통합 `wf_start`·`initial_wf`.
# oracle: (손) interface card 20261107-fs1 §3.2~§3.4 표의 손 값 (선택 규칙 (i)(ii)(iii) 를 입력 숫자에서 손으로 적용 -- 피검 함수로 기대값을 만들지 않는다).
# =====================================================================================================================
from gmid_engine.core import StructureUnresolvedError  # noqa: E402
from gmid_engine.search import initial_wf, kvl_partner, member_start_w, wf_start_value  # noqa: E402
from gmid_engine.sizing import WfCell  # noqa: E402

_S_GROUPS = (("mirror", ("B", "A"), "derived"), ("mirror", ("B", "C"), "derived"))
_S_MOS = ("A", "B", "C", "D")
_S_POS = {"A": 0, "B": 1, "C": 2, "D": 3}
_S_KIND = {n: "nmos" for n in _S_MOS}
_S_W = {"A": 3.0e-6, "B": 1.5e-6, "C": 2.5e-6, "D": 0.5e-6}
_S_CAND = {"nmos": (50, 100, 200), "pmos": (50, 100, 200)}


def _wsv(groups=_S_GROUPS, pos=None, kinds=None, start_w=None, defined=None):
    return wf_start_value(groups, _S_MOS, dict(pos or _S_POS), dict(kinds or _S_KIND), dict(start_w or _S_W), _S_CAND,
                          defined or (lambda name, key: True), grid_m=1e-8)


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


# ---------------------------------------------------------------- K-1~K-4 kvl_partner
def _kp(name="B", gate=None, source=None, bulk=None, writers=("A",), kind=None):
    g = gate or {"A": "g", "B": "g"}
    s = source or {"A": "s", "B": "s"}
    b = bulk or {"A": "s0", "B": "s0"}
    return kvl_partner(name, ("A", "B"), g, s, b, kind or {"A": "nmos", "B": "nmos"}, set(writers))


def test_k1_partner_is_writer_with_same_gate_source_bulk_kind():
    assert _kp() == "A"


def test_k2_gate_only_shared_has_no_partner():
    assert _kp() == "A"                                                                  # 양성 대조
    assert _kp(source={"A": "s", "B": "s2"}) is None


def test_k3_declared_bulk_differs_has_no_partner():
    assert _kp(bulk={"A": "s0", "B": "s1"}) is None


def test_k4_no_writers_no_partner():
    assert _kp(writers=()) is None


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


def test_w2_no_partner_is_no_member_density():
    out = _msw(partner={"B": None})
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
        assert c.w_key in widths(fs1_case.kctx.lut, kinds[c.members[0]])


def test_sb2_second_start_intervals_computes_nothing(fs1_case, tmp_path):
    """S-B2: 같은 donors·counters 로 단계 B 를 한 번 더 -> start_intervals 계산 0 (reuse), wf_start 같음."""
    from gmid_engine.pipeline import run_stage_b
    from .u13_hand import memo_of, toy_env
    env = toy_env()
    a, base = fs1_case.a, fs1_case.sctx.dc.base

    def row():
        rows = [r for r in a.counters.snapshot().blocks if (r.block, r.part) == ("start_intervals", "*")]
        assert len(rows) == 1
        return rows[0]
    r1 = row()
    assert r1.computes >= 1
    b2 = run_stage_b(a, memo_of(env.lut), env.decls[0], output_dir=tmp_path, settings=fs1_case.settings)
    r2 = row()
    assert r2.computes == r1.computes and r2.reuses >= r1.reuses                          # 계산 0
    assert repr(b2.s1.snapshot.value("graph", "start", "wf_start")) == repr(base.value("graph", "start", "wf_start"))


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


def _spy_start_calls(monkeypatch):
    import inspect
    import sys
    mod = sys.modules["gmid_engine.search.start_intervals"]
    log = {"member_start_w": [], "wf_start_value": [], "matching_bounds": []}
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
    # (d) 손 선택: 거울 칸 W_c = min 멤버 출발 W, 가장 큰 key·grid <= W_c (모두 정의 -- 전제)
    cand = wargs["candidates"]["pmos"]
    assert tuple(cand) == tuple(widths(case.kctx.lut, "pmos"))
    assert all(wargs["defined"](n, k) for n in ("MP1", "MP2") for k in cand)
    w_c = min(out["MP1"], out["MP2"])
    ok = [k for k in cand if k * wargs["grid_m"] <= w_c]
    want = max(ok) if ok else min(cand)
    got = {c.members: c.w_key for c in base.value("graph", "start", "wf_start")}
    assert got[("MP1", "MP2")] == want


# [FS-1 A-178/A-182 보고] S-B6 (gate만 공유 칸, 운영 경로) 는 쓰지 않았다: 전제 '정합 묶음 멤버 C 가 쓰기 멤버와 gate 만 공유하고 source 가 다른 mirror 묶음'이
# 손 회로로 서지 않는다(실측 -- 퇴화 거울(source 저항)은 matching_groups 가 비고, 캐스코드 거울의 branch_symmetric 은 둘 다 writer). 보고서 참조(skip 아님).

# [xrun] 옛 '[U17 ①-a 통합] 묶음 필드 값 형식이 타입 등록부에 있다' test 2개(toy·실경로)와 그 helper 를 지웠다 -- 설계 40 v1.10 §2.4.3
# '타입 등록부' 삭제 행과 test 변경 목록('타입 등록부 이름을 읽는 단언 search/test_start_intervals.py:216-217 ... 그 단언을 지운다'):
# 등록부의 소비자는 디스크 S0 코덱뿐이었고 코덱이 없어졌다.
