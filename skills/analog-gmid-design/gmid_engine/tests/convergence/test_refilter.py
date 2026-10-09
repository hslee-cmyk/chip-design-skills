"""`refilter(points) -> (kept, dominated, folded)` -- 판정 축 재필터 (CONTRACT 8절, DEC-79·DEC-95 (2), CONTRACT 11절 불변식 7).

oracle (a): 손으로 고른 (전력, 레이아웃 면적, bbox) 에서 지배·동률을 손으로 판정한다.
* 동률 폭(DEC-79): 전력 = 두 점 b_P 중 큰 값, 면적 ΔA_tie = 제조 격자 x max(두 점 bbox 변 4개).
* 지배(search pareto 계약 -- 탐색 축 필터와 같은 규칙): 어느 축도 폭 넘게 나쁘지 않고 한 축 이상 폭 넘게 나음. 모든 축 동률이면 먼저 남은 점으로 접힘.
  남기는 순서 = 전력 오름차순 -> slack 큰 쪽 -> id, 그 순서로 넣으며 판정(지배자 = 그때 남아 있는 점 중 앞의 것).
"""
from __future__ import annotations

import itertools

from gmid_engine.convergence import refilter

from .conftest import GRID, converged

U = 1e-12           # 면적 단위: 격자 1e-8 x bbox 변 1e-4 = 1e-12 (작은 bbox 점끼리 ΔA_tie)
B = 1e-4            # 작은 bbox 변
BIG = 1e-3          # 큰 bbox 변 -> 그 점이 낀 쌍의 ΔA_tie = 1e-8 x 1e-3 = 1e-11 = 10 U
BP = 1e-6           # 전력 동률 폭 b_P


def test_hand_derived_dominance_with_bbox_dependent_area_tie():
    pts = (
        converged("P1", 1.0e-3, 10.0 * U, B, b_p=BP),
        converged("P2", 1.0e-3 + 0.5 * BP, 10.5 * U, B, b_p=BP),     # P1 대비 전력 0.5 b_P, 면적 0.5 U -- 모두 동률 -> P1 로 접힘
        converged("P3", 2.0e-3, 5.0 * U, B, b_p=BP),                 # P1 대비 면적 5 U 나음 -> 비지배
        converged("P4", 3.0e-3, 4.1 * U, B, b_p=BP),                 # P3 대비 면적 0.9 U(< 폭 1 U, 동률), 전력 나쁨 -> P3 이 지배
        converged("P5", 2.0e-3 + 0.5 * BP, 7.0 * U, B, b_p=BP),      # P3 대비 전력 동률, 면적 2 U 나쁨 -> P3 이 지배
        converged("P6", 4.0e-3, 3.5 * U, BIG, b_p=BP),               # P1 대비 면적 6.5 U < 쌍 폭 10 U(큰 bbox) -> 동률, 전력 나쁨 -> P1 이 지배
    )
    # 손 판정 확인(위 주석의 산수)
    assert abs(10.5 - 10.0) * U <= GRID * B and (10.0 - 5.0) * U > GRID * B
    assert (10.0 - 3.5) * U <= GRID * BIG
    kept, dominated, folded = refilter(pts)
    assert kept == ("P1", "P3")
    assert folded == (("P2", "P1"),)
    assert dominated == (("P4", "P3"), ("P5", "P3"), ("P6", "P1"))


def test_old_grid_squared_tie_would_keep_p6():
    # 대조: ΔA_tie 가 grid^2(옛 식)였다면 P6 은 면적이 6.5 U 나아 비지배였다 -- 큰 bbox 하나로 결과가 갈리는 것을 확인(DEC-95 (2))
    pts = (converged("P1", 1.0e-3, 10.0 * U, B, b_p=BP), converged("P6", 4.0e-3, 3.5 * U, BIG, b_p=BP))
    assert (10.0 - 3.5) * U > GRID * GRID
    kept, dominated, _folded = refilter(pts)
    assert kept == ("P1",) and dominated == (("P6", "P1"),)


def test_kept_points_are_mutually_nondominated_on_judged_axis():
    # 불변식 7: kept 끼리 판정 축 값으로 서로 지배하지 않는다(동률 폭 안은 접힘) -- 격자 점 9개 전수
    pts = tuple(converged("Q%d" % i, (1 + (i % 3)) * 1e-3, (10 - 3 * (i // 3) + (i % 2)) * U, B, b_p=BP) for i in range(9))
    kept, dominated, folded = refilter(pts)
    by = {p.point_id: p for p in pts}
    assert sorted(kept + tuple(i for i, _ in dominated) + tuple(i for i, _ in folded)) == sorted(by)
    for a, b in itertools.permutations(kept, 2):
        pa, pb = by[a], by[b]
        tie_p, tie_a = max(pa.power_resolution_w, pb.power_resolution_w), GRID * B
        better = (pa.power_w < pb.power_w - tie_p) + (pa.layout_area_m2 < pb.layout_area_m2 - tie_a)
        worse = (pb.power_w < pa.power_w - tie_p) + (pb.layout_area_m2 < pa.layout_area_m2 - tie_a)
        assert not (better and not worse), (a, b)
        assert better or worse, (a, b)         # 모든 축 동률이면 접혔어야 한다


def test_power_tie_uses_larger_resolution_of_the_pair():
    # P_b 의 b_P 가 커서 쌍 폭 = 3e-6: 전력 차 2e-6 은 동률 -> 면적이 나은 P_b 가 P_a 를 지배
    pts = (converged("Pa", 1.0e-3, 10 * U, B, b_p=1e-7), converged("Pb", 1.0e-3 + 2e-6, 5 * U, B, b_p=3e-6))
    kept, dominated, _ = refilter(pts)
    assert kept == ("Pb",) and dominated == (("Pa", "Pb"),)
