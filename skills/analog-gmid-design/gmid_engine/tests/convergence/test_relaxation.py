"""`relaxation_decision(snapshot, relaxed) -> (relax, not_relaxable)` (CONTRACT 6절, 계획 LY5, U12 인계).

oracle (a)+(d): 계획 LY5 '(i) nf 조정 (ii) W 조정이 모두 불가능할 때만 완화' -- 대상 = CC 요구 role(diff_pair·branch_symmetric) ∧ pattern None ∧ 응답 대기 아님
∧ 아직 완화 안 함. hub 넷이 있으면 interdigitation 경로(relax), 없으면 not_relaxable. 손으로 만든 그룹마다 조건을 손으로 판정한다.
[U17 1-e] 그룹 결과는 `ly_groups`, hub 넷은 입력 그룹 필드 `ly_groups_in` -- 둘 다 `LayoutResult.snapshot` 에서 읽는다(CONTRACT 6절).
"""
from __future__ import annotations

from gmid_engine.convergence import relaxation_decision

from .conftest import glay, groups_in, layout


def test_only_unplaced_non_pending_cc_groups_are_judged():
    groups = (
        glay("g5_dp_hub", "diff_pair", ("A", "B")),                      # 대상, hub 있음 -> relax
        glay("g2_bs", "branch_symmetric", ("C", "D")),                   # 대상, hub 없음 -> not_relaxable
        glay("g3_pending", "diff_pair", ("E", "F"), pending=True),       # (ii) 진행 중 -> 아님
        glay("g4_placed", "diff_pair", ("G", "H"), pattern="common_centroid"),
        glay("g6_mirror", "mirror", ("I", "J")),                         # CC 요구 아님
        glay("g1_done", "diff_pair", ("K", "L")),                        # 이미 완화 -> 다시 판정 안 함
        glay("g0_dp_hub", "diff_pair", ("M", "N")),                      # 대상, hub 있음 -> relax (gid 순 앞)
    )
    gi = groups_in(("g5_dp_hub", "tail"), ("g2_bs", None), ("g3_pending", "t3"), ("g4_placed", "t4"), ("g6_mirror", "vdd"),
                   ("g1_done", "t1"), ("g0_dp_hub", "tail2"))
    relax, not_relaxable = relaxation_decision(layout(groups=groups, groups_in=gi).snapshot, frozenset({"g1_done"}))
    assert relax == ("g0_dp_hub", "g5_dp_hub")
    assert not_relaxable == ("g2_bs",)


def test_nothing_to_relax():
    groups = (glay("a", "diff_pair", ("A", "B"), pattern="common_centroid"),)
    assert relaxation_decision(layout(groups=groups, groups_in=groups_in(("a", "tail"))).snapshot, frozenset()) == ((), ())


def test_hubbed_branch_symmetric_is_relaxable():
    # 판정은 role 이름이 아니라 hub 넷 유무다(CONTRACT 6절) -- hub 를 가진 branch_symmetric 그룹이 오면 relax
    groups = (glay("a", "branch_symmetric", ("A", "B")),)
    assert relaxation_decision(layout(groups=groups, groups_in=groups_in(("a", "n1"))).snapshot, frozenset()) == (("a",), ())
