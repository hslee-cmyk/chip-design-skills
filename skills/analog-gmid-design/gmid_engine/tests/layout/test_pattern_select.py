"""CONTRACT 4.5 `pattern_select`(@compute_block) -- graph `ly_groups`·`ly_dispositions`.

4.15 손계산 오라클(차동쌍 g1·branch_symmetric g2·bias_distribution g3) + 전제 실패 + 즉시 완화 없음(LY5 마지막 문장, U12 D-LY2/R21:
옛 interdigitation 완화·무게중심 불일치 행 swap 채택과 `relaxed` 필드 삭제) + LY4 `l_mismatch` 기록 + mirror 정렬 키 첫 칸
(interdigitation 성립, Q8 (ii)) + 제외 role 사유(Q8 (iii)). dx·dy 는 행 순서에서 독립 계산해 대조한다.
"""
from __future__ import annotations

import pytest

from gmid_engine.layout.contract_output import GroupLayout, MatchingDisposition, WRequest
from gmid_engine.layout.pattern_select import pattern_select

from .conftest import centroid_offsets, dev, graph_value, make_input, mg, new_memo, rg, staged_snapshot, toy_pdk
from .conftest import block_row, fresh_run  # [XRUN-F1 card B C0·C1]

BIAS_REASON = ("gate shared by a diode reference and consumers in other blocks: bias distribution, not a matched pair "
               "(Q8 (iii))")
FEEDBACK_REASON = "loop signal gate shared: feedback sharing, not a matched pair (Q8 (iii))"


def select(toy_lut, devices, groups, rgs=None, rejected=()):
    rgs = rgs or [rg("r1", [d.name for d in devices])]
    inp = make_input(devices, groups, rgs, toy_pdk(toy_lut), rejected)
    snap = staged_snapshot(inp, new_memo(toy_lut), "pattern_select")
    return graph_value(snap, "ly_groups"), graph_value(snap, "ly_dispositions")


def one(toy_lut, devices, group, **kw):
    groups, disp = select(toy_lut, devices, [group], **kw)
    assert disp == ()
    assert len(groups) == 1 and isinstance(groups[0], GroupLayout)
    return groups[0]


def check_offsets(g):
    if g.pattern is None:
        return
    dx, dy = centroid_offsets([r.transistor_sequence for r in g.rows], g.members)
    assert g.dx == pytest.approx(float(dx), abs=1e-12) and g.dy == pytest.approx(float(dy), abs=1e-12)


def dp(ID, adj=True):
    return [dev("A", "h", "da", ID, adj=adj), dev("B", "h", "db", ID, adj=adj)]


# --- 4.15 차동쌍 ------------------------------------------------------------------------------------------------------

def test_diff_pair_cc_same_w(toy_lut):
    g = one(toy_lut, dp(2e-6), mg("g1", ("A", "B"), "diff_pair", "h"))
    assert (g.pattern, g.method, g.finger_w_key, g.n_fingers) == ("common_centroid", "rotation_exact", 100, (("A", 2), ("B", 2)))
    assert [r.transistor_sequence for r in g.rows] == [("A", "B"), ("B", "A")]
    assert (g.dx, g.dy) == (0.0, 0.0)
    assert g.reason == "cc_same_W" and g.ok is True and g.pending is False
    assert g.w_requests == ()
    assert g.l_mismatch == ()                                   # 멤버 L 같음 -> 기록 없음(LY4)
    check_offsets(g)
    # attempts: 조합 순서 = 행 폭 칸 수 오름차순 -> 키 200 nf 1(200칸, cc_precondition) 다음 키 100 nf 2(400칸)
    assert [(a.step, a.n_fingers, a.reason) for a in g.attempts] == [
        ("cc_same_W", (1, 1), "cc_precondition"), ("cc_same_W", (2, 2), "evaluated")]
    assert g.attempts[0].method is None and g.attempts[0].dx is None and g.attempts[0].dy is None


def test_diff_pair_w_request_pending(toy_lut):
    g = one(toy_lut, dp(1e-6), mg("g1", ("A", "B"), "diff_pair", "h"))
    assert g.pattern is None                                    # (i) 최선 없음(cc_precondition 뿐)
    assert (g.pending, g.reason) == (True, "w_request_pending")
    assert len(g.w_requests) == 2
    for w, name in zip(g.w_requests, ("A", "B")):
        assert isinstance(w, WRequest)
        assert (w.device, w.reason, w.group) == (name, "cc_nf", "g1")
        assert w.W_old_m == pytest.approx(1e-6, rel=1e-9)        # W_need(키*)
        assert w.W_new_m == pytest.approx(2e-6, rel=1e-12)       # n x 키* x 격자 = 2 x 100 x 1e-8
        # [dispute 8.4] 요청 손가락 (nf, finger_w_m) = 마지막 시도의 (n, 키* x 격자), W_new = nf x finger_w_m
        assert w.nf == 2 and w.finger_w_m == pytest.approx(1e-6, rel=1e-12)
        assert w.W_new_m == pytest.approx(w.nf * w.finger_w_m, rel=1e-12)
    last = g.attempts[-1]
    assert last.step == "w_request" and last.reason == "cc_nf"
    assert last.finger_w_m == pytest.approx(1e-6) and last.n_fingers == (2, 2)
    assert [a.step for a in g.attempts][0] == "cc_same_W"


def test_w_request_pending_is_provisional_without_placement(toy_lut):
    # 4.5 6 (ii): "`pending=True`, `provisional=True`, `reason="w_request_pending"`" -- 배치 유무 조건 없이 provisional=True
    g = one(toy_lut, dp(1e-6), mg("g1", ("A", "B"), "diff_pair", "h"))
    assert g.pattern is None and g.pending is True
    assert g.provisional is True


def test_w_request_pending_keeps_best_cc_placement_provisional(toy_lut):
    # branch_symmetric ID 1e-6: (i) 최선 = 조각 행 1개 행 swap(dx 1.0, 중심 불일치) -> 조정 가능 -> 요청 + 배치 = (i) 최선
    g = one(toy_lut, bs(1e-6), mg("g2", ("E", "F"), "branch_symmetric", None))
    assert (g.pending, g.provisional, g.reason) == (True, True, "w_request_pending")
    assert (g.pattern, g.method, g.dx) == ("common_centroid", "row_swap", 1.0)
    assert [(w.device, w.reason, w.group) for w in g.w_requests] == [("E", "cc_nf", "g2"), ("F", "cc_nf", "g2")]
    assert all(w.W_new_m == pytest.approx(2e-6) for w in g.w_requests)
    assert g.attempts[-1].step == "w_request"


def test_diff_pair_not_adjustable_no_immediate_relax(toy_lut):
    # [U12] CONTRACT 4.15 예(oracle (d) 계약 손계산): W_adjustable=False -> attempts cc_same_W(cc_precondition) -> w_request(w_not_adjustable),
    # 이후 완화 없음: pattern None, reason "w_not_adjustable"(키 100 nf 1 조합이 있으므로 (iii) 사유). 판정은 MOD8 몫(LY5 마지막 문장).
    g = one(toy_lut, dp(1e-6, adj=False), mg("g1", ("A", "B"), "diff_pair", "h"))
    assert [(a.step, a.reason) for a in g.attempts] == [("cc_same_W", "cc_precondition"), ("w_request", "w_not_adjustable")]
    assert "relax" not in [a.step for a in g.attempts]
    assert "interdigitation" not in [a.pattern for a in g.attempts]        # 옛 interdigitation 완화 평가 없음
    assert g.pattern is None and g.ok is False
    assert (g.pending, g.provisional) == (False, False)
    assert g.reason == "w_not_adjustable"
    assert g.w_requests == ()
    assert not hasattr(g, "relaxed")


def test_diff_pair_rejected_request(toy_lut):
    g = one(toy_lut, dp(1e-6), mg("g1", ("A", "B"), "diff_pair", "h"), rejected=("A",))
    assert [(a.step, a.reason) for a in g.attempts][-1] == ("w_request", "w_request_rejected")
    assert g.pattern is None and g.ok is False and g.pending is False
    assert g.reason == "w_request_rejected"                                # [U12] 옛 "relaxed:w_request_rejected" 아님
    assert g.w_requests == ()


def test_not_adjustable_result_independent_of_allowed_patterns(toy_lut):
    # [U12] CONTRACT 4.15: "(`allowed_patterns` 와 무관 -- 옛 interdigitation 완화는 지웠다)"
    both = one(toy_lut, dp(1e-6, adj=False), mg("g1", ("A", "B"), "diff_pair", "h"))
    cc_only = one(toy_lut, dp(1e-6, adj=False), mg("g1", ("A", "B"), "diff_pair", "h", patterns=("common_centroid",)))
    assert cc_only.pattern is None and cc_only.reason == "w_not_adjustable"
    assert (cc_only.attempts, cc_only.reason, cc_only.pattern, cc_only.ok) == (both.attempts, both.reason, both.pattern, both.ok)


def test_diff_pair_no_usable_slice(toy_lut):
    devs = [dev("A", "h", "da", 2e-6, L=1.5e-6), dev("B", "h", "db", 2e-6, L=1.5e-6), dev("Z", "u", "v", 1e-6)]
    groups, _ = select(toy_lut, devs, [mg("g1", ("A", "B"), "diff_pair", "h")])
    g = groups[0]
    assert ("w_request", "no_usable_slice") in [(a.step, a.reason) for a in g.attempts]
    assert g.pattern is None and g.pending is False
    assert g.reason == "no_common_finger_w"                               # 후보 없음 -> 7 의 사유


def test_cc_stops_after_all_zero_head(toy_lut):
    # ID 4e-6: 키 200 nf 2(400칸) rotation_exact 중심 일치 -> 머리 모두 0 -> 키 100 nf 4(800칸)는 평가하지 않음
    g = one(toy_lut, dp(4e-6), mg("g1", ("A", "B"), "diff_pair", "h"))
    assert g.finger_w_key == 200 and g.method == "rotation_exact"
    assert all(a.finger_w_m != pytest.approx(1e-6) for a in g.attempts)


# --- branch_symmetric -----------------------------------------------------------------------------------------------

def bs(ID, gate_f="gc", adj=True):
    return [dev("E", "p", "q", ID, gate="gc", adj=adj), dev("F", "r", "t", ID, gate=gate_f, adj=adj)]


def test_branch_symmetric_row_swap(toy_lut):
    g = one(toy_lut, bs(2e-6), mg("g2", ("E", "F"), "branch_symmetric", None, patterns=("common_centroid",)))
    assert (g.pattern, g.method, g.finger_w_key) == ("common_centroid", "row_swap", 100)
    assert [r.transistor_sequence for r in g.rows] == [("E", "F"), ("F", "E")]
    assert (g.dx, g.dy) == (0.0, 0.0) and g.reason == "cc_same_W" and g.ok
    check_offsets(g)
    # 4.15 [r5]: 키 200 nf (1,1) 조합(200칸)이 먼저 평가 -- 조각 행 1개라 중심 불일치 -- 그다음 키 100 nf (2,2)
    ev = [(a.finger_w_m, a.n_fingers, a.method, a.reason) for a in g.attempts]
    assert ev[0][1:] == ((1, 1), "row_swap", "evaluated") and ev[0][0] == pytest.approx(2e-6)
    assert (g.attempts[0].dx, g.attempts[0].dy) == (1.0, 0.0)
    assert ev[1][1:] == ((2, 2), "row_swap", "evaluated") and ev[1][0] == pytest.approx(1e-6)


def test_branch_symmetric_gate_differs(toy_lut):
    g = one(toy_lut, bs(2e-6, gate_f="gx"), mg("g2", ("E", "F"), "branch_symmetric", None))
    assert g.pattern is None and g.ok is False and g.reason == "branch_gate_differs"
    assert len(g.attempts) == 1
    a = g.attempts[0]
    assert a.step == "precondition" and (a.method, a.dx, a.dy) == (None, None, None)


def test_branch_symmetric_not_adjustable_no_uncentred_adoption(toy_lut):
    # ID 1e-6 만 ok(키 100 nf 1) -> 행 swap 2행 요청이지만 조각 행 1개 -> dx 1.0 -> 조정 불가.
    # [U12] 옛 동작(무게중심 불일치 행 swap 채택, step "relax" row_swap_uncentred)은 지웠다: pattern None, (i) 시도의 dx·dy 는 attempts 에 남는다.
    g = one(toy_lut, bs(1e-6, adj=False), mg("g2", ("E", "F"), "branch_symmetric", None))
    steps = [a.step for a in g.attempts]
    assert "relax" not in steps
    assert (g.attempts[-1].step, g.attempts[-1].reason) == ("w_request", "w_not_adjustable")
    first = g.attempts[0]
    assert (first.step, first.method, first.reason) == ("cc_same_W", "row_swap", "evaluated")
    assert (first.dx, first.dy) == (1.0, 0.0)                              # 손계산: 조각 행 1개 (E, F) -> 중심 차 1 피치
    assert g.pattern is None and g.ok is False and g.pending is False
    assert g.reason == "w_not_adjustable"
    assert "interdigitation" not in [a.pattern for a in g.attempts]        # 공유 hub 없음 -> interdigitation 평가 없음


# --- [U12] LY4 matching_L_mismatch (CONTRACT 4.5 6·7) -- oracle (a) 구성: 입력 L 을 다르게 준 그대로가 기록값 ------------------

@pytest.mark.parametrize("role, hub, devs", [
    ("diff_pair", "h", (("A", "h", "da", "g"), ("B", "h", "db", "g"))),          # 6 경로
    ("mirror", "h", (("A", "h", "da", "g"), ("B", "h", "db", "g"))),             # 7 경로
    ("branch_symmetric", None, (("A", "p", "q", "gc"), ("B", "r", "t", "gx"))),  # 6 전제 실패 경로(branch_gate_differs)
])
def test_l_mismatch_recorded_on_every_path(toy_lut, role, hub, devs):
    Ls = {"A": 1e-6, "B": 2e-6}
    ds = [dev(n, s, d, 2e-6, gate=gt, L=Ls[n]) for n, s, d, gt in devs]
    g = one(toy_lut, ds, mg("g1", ("A", "B"), role, hub))
    assert g.l_mismatch == (("A", 1e-6), ("B", 2e-6))                     # 멤버 순서, 입력 L 그대로


def test_l_mismatch_follows_member_order(toy_lut):
    ds = [dev("A", "h", "da", 2e-6, L=2e-6), dev("B", "h", "db", 2e-6, L=1e-6)]
    g = one(toy_lut, ds, mg("g1", ("B", "A"), "diff_pair", "h"))
    assert g.l_mismatch == (("B", 1e-6), ("A", 2e-6))


def test_l_mismatch_empty_when_equal_l(toy_lut):
    for role, hub in (("diff_pair", "h"), ("mirror", "h")):
        g = one(toy_lut, [dev("A", "h", "da", 2e-6, L=2e-6), dev("B", "h", "db", 2e-6, L=2e-6)], mg("g1", ("A", "B"), role, hub))
        assert g.l_mismatch == ()


# --- 전제(hub-leaf) ---------------------------------------------------------------------------------------------------

@pytest.mark.parametrize("hub, devs, reason", [
    (None, (("A", "h", "da"), ("B", "h", "db")), "no_hub_net"),
    ("h", (("A", "h", "da"), ("B", "x", "db")), "member_not_on_hub:B"),
    ("h", (("A", "h", "d1"), ("B", "h", "d1")), "leaf_net_shared"),
])
@pytest.mark.parametrize("role", ["diff_pair", "mirror"])
def test_hub_leaf_precondition(toy_lut, hub, devs, reason, role):
    ds = [dev(n, s, d, 2e-6) for n, s, d in devs]
    g = one(toy_lut, ds, mg("g1", ("A", "B"), role, hub))
    assert g.pattern is None and g.ok is False and g.reason == reason
    assert [a.step for a in g.attempts] == ["precondition"]


def test_hub_as_drain_is_flipped(toy_lut):
    ds = [dev("A", "da", "h", 2e-6), dev("B", "db", "h", 2e-6)]
    g = one(toy_lut, ds, mg("g1", ("A", "B"), "diff_pair", "h"))
    assert g.reason == "cc_same_W" and g.method == "rotation_exact"
    assert g.rows[0].node_sequence == ("da", "h", "db")


# --- mirror: 정렬 키 첫 칸 = interdigitation 성립 ----------------------------------------------------------------------

def test_mirror_prefers_feasible_interdigitation(toy_lut):
    # ID 2e-6: 키 100 nf 2 에서 cc rotation_exact(중심 일치)와 interdigitation(ABBA, crossover 0, 중심 일치)가 같은 꼬리 칸.
    # mirror 머리 첫 칸이 없으면 패턴 이름 순으로 cc 가 이긴다 -> mirror 는 interdigitation 을 골라야 한다.
    g = one(toy_lut, dp(2e-6), mg("g1", ("A", "B"), "mirror", "h"))
    assert g.reason == "selected"
    assert g.pattern == "interdigitation" and g.crossover_count == 0
    cc = [a for a in g.attempts if a.pattern == "common_centroid" and a.reason == "evaluated" and a.dx == 0 and a.dy == 0]
    assert cc, "비교 대상(중심 일치 cc 후보)이 평가되지 않았다"
    check_offsets(g)


def test_mirror_no_common_finger_w(toy_lut):
    ds = [dev("A", "h", "da", 2e-6, gm_id=25.0), dev("B", "h", "db", 2e-6, gm_id=25.0), dev("Z", "u", "v", 1e-6)]
    groups, _ = select(toy_lut, ds, [mg("g1", ("A", "B"), "mirror", "h")])
    assert groups[0].pattern is None and groups[0].reason == "no_common_finger_w"


# --- 제외 role(Q8 (iii)) ---------------------------------------------------------------------------------------------

def test_excluded_roles_dispositions(toy_lut):
    ds = [dev("C", "x", "y", 1e-6, gate="gb"), dev("D", "y", "z", 1e-6, gate="gb"),
          dev("K", "k1", "k2", 1e-6, gate="fb"), dev("M", "m1", "m2", 1e-6, gate="fb")] + dp(2e-6)
    groups, disp = select(toy_lut, ds, [mg("g3", ("C", "D"), "bias_distribution", "y"),
                                        mg("g4", ("K", "M"), "feedback_shared", None),
                                        mg("g1", ("A", "B"), "diff_pair", "h")],
                          rgs=[rg("r1", ("A", "B", "C", "D")), rg("r2", ("K", "M"))])
    assert [g.gid for g in groups] == ["g1"]
    assert all(isinstance(d, MatchingDisposition) for d in disp)
    assert [(d.gid, d.role, tuple(d.members), d.disposition, d.reason) for d in disp] == [
        ("g3", "bias_distribution", ("C", "D"), "excluded_from_layout_matching", BIAS_REASON),
        ("g4", "feedback_shared", ("K", "M"), "excluded_from_layout_matching", FEEDBACK_REASON),
    ]


def test_groups_sorted_by_gid_all_judged(toy_lut):
    ds = dp(2e-6) + bs(2e-6, gate_f="gx")
    groups, _ = select(toy_lut, ds, [mg("z9", ("E", "F"), "branch_symmetric", None), mg("a1", ("A", "B"), "diff_pair", "h")])
    assert [g.gid for g in groups] == ["a1", "z9"]                           # 실패 그룹도 결과에 남는다(LY6)


def test_block_reuse(toy_lut):
    # oracle 대조: card B C4 판정 1 -- 같은 실행(run)에서 같은 lineage 재호출 = reuse, 같은 입력 재계산 0(C1 행)
    run = fresh_run()
    inp = make_input(dp(2e-6), [mg("g1", ("A", "B"), "diff_pair", "h")], [rg("r1", ("A", "B"))], toy_pdk(toy_lut))
    snap = staged_snapshot(inp, new_memo(toy_lut), "pattern_select", run=run)
    assert pattern_select(snap, **run) is snap
    st = block_row(run["counters"], pattern_select.name)
    assert st[5] == 0 and st[1] == 1


def test_reads_declaration():
    # oracle (d): design 40 v1.11.2 §2.4.8 '세 블록 READS' 행(O-36 (3) (a)·O-39 (2)) -- `ly_pattern_select` READS device `ly_point`(kind·L_m)·
    # `ly_pins`·`ly_w_adjustable`·`ly_fw_cand`, graph `ly_pdk`·`ly_groups_in`·`ly_rejected`·`ly_canon`. `ly_attrs`(참고 W)·`ly_canon_rows` 는 읽지 않는다.
    assert set(pattern_select.reads) == {("device", "ly_point"), ("device", "ly_pins"), ("device", "ly_w_adjustable"),
                                         ("device", "ly_fw_cand"), ("graph", "ly_pdk"), ("graph", "ly_groups_in"),
                                         ("graph", "ly_rejected"), ("graph", "ly_canon")}


def _staged_w(toy_lut, wa, wb, wc, upto):
    ds = [dev("A", "h", "da", 2e-6, W=wa), dev("B", "h", "db", 2e-6, W=wb), dev("C", "x", "y", 0.75e-6, W=wc)]
    inp = make_input(ds, [mg("g1", ("A", "B"), "diff_pair", "h")], [rg("r1", ("A", "B")), rg("r2", ("C",))], toy_pdk(toy_lut))
    return staged_snapshot(inp, new_memo(toy_lut), upto)


def test_uniform_exact_w_doubling_keeps_input_version(toy_lut):
    # 완료 조건 W-1 블록 단위(구성): 모든 W_m 정확히 2배 -> 정준 별칭표 값 같음(순위·동률 보존) -> 이 블록 입력 버전 같음(재계산 0)
    a = _staged_w(toy_lut, 4e-6, 4e-6, 3e-6, "finger_candidates")
    b = _staged_w(toy_lut, 8e-6, 8e-6, 6e-6, "finger_candidates")
    assert pattern_select.input_version(a) == pattern_select.input_version(b)
