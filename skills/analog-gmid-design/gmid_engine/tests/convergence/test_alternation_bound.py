"""`alternation_bound(points) -> int` -- 교대 상한 K_alt (CONTRACT 9절, DEC-79·LR9 '교대 반복 상한은 N3.6 K_max 규칙을 그대로 쓴다').

oracle (d)+(a): K_max 정의(구간을 tol 까지 반으로 줄이는 횟수, 계획 N3.6) -- 구간 = 수렴 점 레이아웃 면적 범위, tol = 쌍 ΔA_tie 최솟값.
손으로 고른 면적·bbox 로 반감 횟수를 센다.
"""
from __future__ import annotations

from gmid_engine.convergence import alternation_bound

from .conftest import converged

U = 1e-12           # 격자 1e-8 x bbox 1e-4


def test_range_over_smallest_pair_tie():
    # 면적 10 U, 30 U, 20 U, bbox 모두 1e-4 -> tol 1 U, 범위 20 U -> 20/2^5 = 0.625 <= 1, 20/2^4 = 1.25 > 1 -> 5
    pts = (converged("a", 1e-3, 10 * U, 1e-4), converged("b", 2e-3, 30 * U, 1e-4), converged("c", 3e-3, 20 * U, 1e-4))
    assert alternation_bound(pts) == 5


def test_tol_is_minimum_over_pairs():
    # bbox 1e-4 두 점 + bbox 1e-3 한 점: 쌍 폭 = (1 U, 10 U, 10 U) -> 최솟값 1 U ; 범위 = 40 U -> 40/2^6 = 0.625 -> 6
    pts = (converged("a", 1e-3, 10 * U, 1e-4), converged("b", 2e-3, 50 * U, 1e-4), converged("c", 3e-3, 20 * U, 1e-3))
    assert alternation_bound(pts) == 6


def test_range_within_tie_is_one():
    pts = (converged("a", 1e-3, 10 * U, 1e-4), converged("b", 2e-3, 10.8 * U, 1e-4))
    assert alternation_bound(pts) == 1


def test_single_or_no_point_is_one():
    assert alternation_bound((converged("a", 1e-3, 10 * U, 1e-4),)) == 1
    assert alternation_bound(()) == 1
