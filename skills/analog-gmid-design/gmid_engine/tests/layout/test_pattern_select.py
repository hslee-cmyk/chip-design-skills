"""CONTRACT 4.5 `pattern_select`(@compute_block) -- graph `ly_groups`·`ly_dispositions`.

4.15 손계산 오라클(차동쌍 g1·branch_symmetric g2·bias_distribution g3) + 전제 실패 + 완화 순서(LY5) + mirror 정렬 키 첫 칸
(interdigitation 성립, Q8 (ii)) + 제외 role 사유(Q8 (iii)). dx·dy 는 행 순서에서 독립 계산해 대조한다.
"""
from __future__ import annotations

import pytest

from gmid_engine.layout.contract_output import GroupLayout, MatchingDisposition, WRequest
from gmid_engine.layout.pattern_select import pattern_select

from .conftest import centroid_offsets, dev, graph_value, make_input, mg, new_memo, rg, staged_snapshot, toy_pdk

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
    assert g.reason == "cc_same_W" and g.ok is True and g.relaxed is False and g.pending is False
    assert g.w_requests == ()
    check_offsets(g)
    # attempts: 조합 순서 = 행 폭 칸 수 오름차순 -> 키 200 nf 1(200칸, cc_precondition) 다음 키 100 nf 2(400칸)
    assert [(a.step, a.n_fingers, a.reason) for a in g.attempts] == [
        ("cc_same_W", (1, 1), "cc_precondition"), ("cc_same_W", (2, 2), "evaluated")]
    assert g.attempts[0].method is None and g.attempts[0].dx is None and g.attempts[0].dy is None


def test_diff_pair_w_request_pending(toy_lut):
    g = one(toy_lut, dp(1e-6), mg("g1", ("A", "B"), "diff_pair", "h"))
    assert g.pattern is None                                    # (i) 최선 없음(cc_precondition 뿐)
    assert (g.pending, g.relaxed, g.reason) == (True, False, "w_request_pending")
    assert len(g.w_requests) == 2
    for w, name in zip(g.w_requests, ("A", "B")):
        assert isinstance(w, WRequest)
        assert (w.device, w.reason, w.group) == (name, "cc_nf", "g1")
        assert w.W_old_m == pytest.approx(1e-6, rel=1e-9)        # W_need(키*)
        assert w.W_new_m == pytest.approx(2e-6, rel=1e-12)       # n x 키* x 격자 = 2 x 100 x 1e-8
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
    assert (g.pending, g.provisional, g.relaxed, g.reason) == (True, True, False, "w_request_pending")
    assert (g.pattern, g.method, g.dx) == ("common_centroid", "row_swap", 1.0)
    assert [(w.device, w.reason, w.group) for w in g.w_requests] == [("E", "cc_nf", "g2"), ("F", "cc_nf", "g2")]
    assert all(w.W_new_m == pytest.approx(2e-6) for w in g.w_requests)
    assert g.attempts[-1].step == "w_request"


def test_diff_pair_not_adjustable_relaxes_to_interdigitation(toy_lut):
    g = one(toy_lut, dp(1e-6, adj=False), mg("g1", ("A", "B"), "diff_pair", "h"))
    steps = [(a.step, a.reason) for a in g.attempts]
    assert steps[0] == ("cc_same_W", "cc_precondition")
    assert ("w_request", "w_not_adjustable") in steps
    i_w = steps.index(("w_request", "w_not_adjustable"))
    i_r = [s for s, _ in steps].index("relax")
    assert i_w < i_r                                                    # LY5: 완화 전에 cc·W 요청 시도가 기록
    assert (g.pattern, g.method) == ("interdigitation", "pattern_table")
    assert [r.transistor_sequence for r in g.rows] == [("A", "B")]
    assert (g.dx, g.dy) == (1.0, 0.0)
    assert g.relaxed is True and g.ok is False and g.pending is False
    assert g.reason == "relaxed:w_not_adjustable"
    check_offsets(g)


def test_diff_pair_rejected_request(toy_lut):
    g = one(toy_lut, dp(1e-6), mg("g1", ("A", "B"), "diff_pair", "h"), rejected=("A",))
    assert ("w_request", "w_request_rejected") in [(a.step, a.reason) for a in g.attempts]
    assert g.reason == "relaxed:w_request_rejected" and g.relaxed is True
    assert g.w_requests == ()


def test_diff_pair_no_relax_without_interdigitation(toy_lut):
    g = one(toy_lut, dp(1e-6, adj=False), mg("g1", ("A", "B"), "diff_pair", "h", patterns=("common_centroid",)))
    assert g.pattern is None and g.relaxed is False
    assert g.reason == "w_not_adjustable"                                  # 후보가 있으면 (iii) 사유
    assert "relax" not in [a.step for a in g.attempts if a.pattern == "interdigitation" and a.reason == "evaluated"]


def test_diff_pair_no_usable_slice(toy_lut):
    devs = [dev("A", "h", "da", 2e-6, L=1.5e-6), dev("B", "h", "db", 2e-6, L=1.5e-6), dev("Z", "u", "v", 1e-6)]
    groups, _ = select(toy_lut, devs, [mg("g1", ("A", "B"), "diff_pair", "h")])
    g = groups[0]
    assert ("w_request", "no_usable_slice") in [(a.step, a.reason) for a in g.attempts]
    assert g.pattern is None and g.relaxed is False and g.pending is False
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


def test_branch_symmetric_gate_differs(toy_lut):
    g = one(toy_lut, bs(2e-6, gate_f="gx"), mg("g2", ("E", "F"), "branch_symmetric", None))
    assert g.pattern is None and g.ok is False and g.reason == "branch_gate_differs"
    assert len(g.attempts) == 1
    a = g.attempts[0]
    assert a.step == "precondition" and (a.method, a.dx, a.dy) == (None, None, None)


def test_branch_symmetric_relax_records_uncentred_row_swap(toy_lut):
    # ID 1e-6 만 ok(키 100 nf 1) -> 행 swap 2행 요청이지만 조각 행 1개 -> dx 1.0 -> 조정 불가 -> relax(row_swap_uncentred)
    g = one(toy_lut, bs(1e-6, adj=False), mg("g2", ("E", "F"), "branch_symmetric", None))
    steps = [a.step for a in g.attempts]
    assert steps.index("w_request") < steps.index("relax")
    last = g.attempts[-1]
    assert (last.step, last.pattern, last.method, last.ok, last.reason) == (
        "relax", "common_centroid", "row_swap", False, "row_swap_uncentred")
    assert (last.dx, last.dy) == (1.0, 0.0)
    assert g.relaxed is True and g.reason == "relaxed:w_not_adjustable"
    assert (g.method, g.dx) == ("row_swap", 1.0)
    assert "interdigitation" not in [a.pattern for a in g.attempts]        # 공유 hub 없음 -> interdigitation 평가 없음


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
    pattern_select.reset_stats()
    inp = make_input(dp(2e-6), [mg("g1", ("A", "B"), "diff_pair", "h")], [rg("r1", ("A", "B"))], toy_pdk(toy_lut))
    snap = staged_snapshot(inp, new_memo(toy_lut), "pattern_select")
    assert pattern_select(snap) is snap
    st = pattern_select.stats()
    assert st.recomputes_same_input == 0 and st.reuses == 1
