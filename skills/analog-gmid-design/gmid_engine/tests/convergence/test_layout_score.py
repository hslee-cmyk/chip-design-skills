"""`layout_score(snapshot, unplaced) -> tuple` (CONTRACT 3절): (놓지 못한 소자 수, 배치 못 한 CC 요구 그룹 수(pattern None ∧ not pending),
pending 그룹 수, 외곽 면적) -- 작을수록 좋은 사전식.

oracle (a): 손으로 만든 그룹 목록에서 각 칸을 손으로 센다. CC 요구 role = diff_pair·branch_symmetric(layout CONTRACT 4.1).
[U17 1-e] 입력은 `LayoutResult.snapshot`(그룹 `ly_groups`, 면적 `ly_floorplan`).
"""
from __future__ import annotations

from gmid_engine.convergence import layout_score

from .conftest import floorplan, glay, layout


def test_score_counts_each_component():
    groups = (
        glay("a", "diff_pair", ("A1", "A2")),                                   # CC 요구, 배치 없음, 대기 아님 -> 2칸 +1
        glay("b", "branch_symmetric", ("B1", "B2")),                            # 같음 -> +1
        glay("c", "diff_pair", ("C1", "C2"), pending=True),                     # 대기 -> 3칸 +1 (2칸 아님)
        glay("d", "mirror", ("D1", "D2")),                                      # CC 요구 아님 -> 0
        glay("e", "diff_pair", ("E1", "E2"), pattern="common_centroid"),        # 배치됨 -> 0
        glay("f", "bias_distribution", ("F1", "F2")),                           # 제외 role -> 0
    )
    lay = layout(groups=groups, plan=floorplan(2e-5, 3e-5, area=7.5e-10))
    assert layout_score(lay.snapshot, ("U1", "U2", "U3")) == (3, 2, 1, 7.5e-10)


def test_score_orders_lexicographically():
    good = layout(groups=(glay("a", "diff_pair", ("A1", "A2"), pattern="common_centroid"),), plan=floorplan(1e-4, 1e-4))
    worse_cc = layout(groups=(glay("a", "diff_pair", ("A1", "A2")),), plan=floorplan(1e-6, 1e-6))
    # 면적이 훨씬 작아도 CC 그룹 미배치가 먼저 진다
    assert layout_score(good.snapshot, ()) < layout_score(worse_cc.snapshot, ())
    # 놓지 못한 소자가 있으면 무엇보다 나쁘다
    assert layout_score(worse_cc.snapshot, ()) < layout_score(good.snapshot, ("X",))
