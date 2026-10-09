"""`effective_placement(layout, grid_m) -> (placements, unplaced)` (CONTRACT 2절, 계획 LY3·LY7).

oracle (a) 구성으로 정답이 정해진 합성 입력: 손으로 만든 `LayoutResult`(놓인 소자·미배치 소자·W_request 응답 대기 그룹)의 필드에서
기대 Placement 를 손으로 읽는다. 폭 키 = finger_w / 격자 를 가장 가까운 정수로(손으로 고른 값이 정수 근처라 반올림 방향이 자명).
"""
from __future__ import annotations

from gmid_engine.convergence import Placement, effective_placement

from .conftest import GRID, attempt, dlay, dunplaced, glay, layout


def test_placed_devices_take_layout_realized_values():
    # M_b: finger 1.0e-6 (키 100), nf 3, 실현 W 3e-6, 실효 허용오차 0.02 / M_a: finger 2.5e-7 (키 25), nf 8, W 2e-6
    lay = layout(devices=(dlay("M_b", 1.0e-6, 3, 3e-6, tol=0.02), dlay("M_a", 2.5e-7, 8, 2e-6, tol=0.05)))
    placements, unplaced = effective_placement(lay, GRID)
    assert unplaced == ()
    assert placements == (Placement("M_a", 25, 2.5e-7, 8, 2e-6, False, 0.05),       # 이름순
                          Placement("M_b", 100, 1.0e-6, 3, 3e-6, False, 0.02))
    assert all(isinstance(p.key, int) for p in placements)


def test_unplaced_devices_are_reported_sorted_and_not_placed():
    lay = layout(devices=(dunplaced("Z9"), dlay("M1", 1e-6, 1, 1e-6), dunplaced("A0")))
    placements, unplaced = effective_placement(lay, GRID)
    assert unplaced == ("A0", "Z9")
    assert [p.name for p in placements] == ["M1"]


def test_pending_group_members_use_requested_key_and_nf_from_last_attempt():
    # 그룹 (P, Q) 이 W_request 응답 대기: 레이아웃은 잠정 배치(finger 9.9e-7)만 했다(LY3) -- MOD8 은 마지막 시도의 요청 (키, nf) 로 평가한다.
    # 마지막 시도 finger 1.234e-6 -> 키 round(123.4) = 123, finger 123 x 1e-8 = 1.23e-6, nf (2, 3) -> W = 2 x 1.23e-6, 3 x 1.23e-6
    first = attempt(2.0e-6, (1, 1))
    last = attempt(1.234e-6, (2, 3))
    group = glay("g", "diff_pair", ("P", "Q"), pending=True, attempts=(first, last))
    lay = layout(devices=(dlay("P", 9.9e-7, 4, 3.96e-6, tol=0.03), dlay("Q", 9.9e-7, 4, 3.96e-6, tol=0.04), dlay("R", 1e-6, 2, 2e-6)),
                 groups=(group,))
    placements, unplaced = effective_placement(lay, GRID)
    by = {p.name: p for p in placements}
    fw = 123 * GRID
    assert by["P"] == Placement("P", 123, fw, 2, 2 * fw, True, 0.03)
    assert by["Q"] == Placement("Q", 123, fw, 3, 3 * fw, True, 0.04)
    assert by["R"].pending is False and by["R"].key == 100
    assert unplaced == ()


def test_non_pending_group_does_not_override_layout_values():
    group = glay("g", "diff_pair", ("P", "Q"), pattern="common_centroid", pending=False, attempts=(attempt(5e-6, (7, 7)),))
    lay = layout(devices=(dlay("P", 1e-6, 2, 2e-6), dlay("Q", 1e-6, 2, 2e-6)), groups=(group,))
    placements, _ = effective_placement(lay, GRID)
    assert [(p.key, p.n_fingers, p.W_m, p.pending) for p in placements] == [(100, 2, 2e-6, False)] * 2
