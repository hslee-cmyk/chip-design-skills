"""search/eval_budget.py -- `EvalBudget(wall_s, times, reserve_evals=0)` (설계 41 §5.8 DEC-34 식 N_T = ⌊(B − T_used − T_reserve)/t_eval⌋).

oracle (a) 손계산(정의 식): t_eval = 평가 시간 중앙값, 첫 평가 전에는 정의되지 않음(None), limit = ⌊B/t_eval⌋ − reserve(이미 쓴 평가 포함 총 한도),
remaining = max(0, limit − 평가 수) -- 시간이 균일하면 §5.8 식 ⌊(B − T_used − reserve·t_eval)/t_eval⌋ 와 같다. 외층 예약분은 한 번만 뺀다(N4).
"""
import math

import pytest

from gmid_engine.search import EvalBudget


def test_undefined_before_first_evaluation():
    b = EvalBudget(10.0, [])
    assert b.t_eval() is None and b.limit() is None and b.remaining() is None


def test_limit_and_remaining_hand_computed():
    b = EvalBudget(10.0, [1.0, 3.0, 2.0])
    assert b.t_eval() == 2.0
    assert b.limit() == 5                     # ⌊10/2⌋
    assert b.remaining() == 2                 # 5 − 3


def test_even_count_median_and_reserve_subtracted_once():
    b = EvalBudget(10.0, [1.0, 2.0, 3.0, 4.0], reserve_evals=1)
    assert b.t_eval() == 2.5
    assert b.limit() == 3                     # ⌊10/2.5⌋ − 1
    assert b.remaining() == 0                 # max(0, 3 − 4)


@pytest.mark.parametrize("n", [1, 4, 7])
def test_uniform_times_match_design_formula(n):
    t, wall, reserve = 0.5, 20.0, 3
    b = EvalBudget(wall, [t] * n, reserve_evals=reserve)
    assert b.remaining() == max(0, math.floor((wall - n * t - reserve * t) / t))


def test_times_list_is_read_live():
    times = [1.0]
    b = EvalBudget(4.0, times)
    assert b.remaining() == 3
    times.extend([1.0, 1.0])
    assert b.remaining() == 1
