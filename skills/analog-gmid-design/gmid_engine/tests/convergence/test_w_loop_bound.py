"""`w_loop_bound(placements, sized_w) -> (k_max, max_dlnw, tol)` (CONTRACT 5절, 계획 N3.6 K_max = ceil(log2(구간폭 / tol)), LR9).

oracle (d)+(a): 계획 N3.6 의 K_max 정의(구간을 bisection 으로 tol 까지 좁히는 횟수)와 손으로 고른 W 비. 반복 상한은 "2^K * tol >= 구간폭 인 최소 K"
로 손으로 센다(log2 식을 그대로 옮기지 않고 2의 거듭제곱 표로 센다).
"""
from __future__ import annotations

import math

import pytest

from gmid_engine.convergence import w_loop_bound

from .conftest import placement


def halvings(width, tol):
    """구간 width 를 반씩 줄여 tol 이하가 되는 횟수(bisection 정의, 계획 N3.6)."""
    k = 0
    while width > tol:
        width /= 2.0
        k += 1
    return max(k, 1)


def test_k_max_from_largest_log_ratio_and_smallest_tolerance():
    # W 비 2.0 (ln 2 = 0.6931) 와 1.1 ; tol 0.01 과 0.05 -> 구간 0.6931, tol 0.01 -> 0.6931 / 2^7 = 0.0054 <= 0.01, 2^6 -> 0.0108 > 0.01 -> 7
    pl = (placement("A", 100, 2, 2e-6, tol=0.05), placement("B", 100, 1, 1.1e-6, tol=0.01))
    k, width, tol = w_loop_bound(pl, {"A": 1e-6, "B": 1e-6})
    assert width == pytest.approx(math.log(2.0), rel=1e-15)
    assert tol == 0.01
    assert k == 7 == halvings(math.log(2.0), 0.01)


def test_shrinking_w_counts_by_absolute_value():
    pl = (placement("A", 100, 1, 0.25e-6, tol=0.1),)                 # |ln 0.25| = 1.386 -> 1.386/2^4 = 0.0866 <= 0.1 -> 4
    k, width, tol = w_loop_bound(pl, {"A": 1e-6})
    assert width == pytest.approx(math.log(4.0), rel=1e-15) and tol == 0.1
    assert k == 4


def test_within_tolerance_is_one_evaluation():
    pl = (placement("A", 100, 1, 1.005e-6, tol=0.01),)              # ln 1.005 = 0.00499 <= 0.01
    k, width, tol = w_loop_bound(pl, {"A": 1e-6})
    assert k == 1 and width <= tol


def test_exact_size_gives_zero_width_and_one():
    pl = (placement("A", 100, 1, 1e-6, tol=0.01),)
    assert w_loop_bound(pl, {"A": 1e-6}) == (1, 0.0, 0.01)


def test_no_placements():
    assert w_loop_bound((), {}) == (1, 0.0, 0.0)
