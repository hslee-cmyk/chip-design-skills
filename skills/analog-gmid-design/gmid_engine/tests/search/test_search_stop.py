"""XRUN-F1 card C interface card C2 -- `search_stop(sctx) -> "eval_budget" | "wall_budget" | None` (C-T3).

oracle: (손) 구성으로 정해진 합성 입력. 선언 E_B = 10 -> 탐색 예산 10(정의 1절). kernel_calls = 9(예산 − 1)이면 정지 아님, = 10(예산)이면 eval_budget.
deadline 은 지난 값(perf_counter − 1 s)이면 wall_budget, 먼 미래 값이면 정지 아님. 피검 함수·식을 다시 쓰지 않는다.
"""
import time

import pytest

from gmid_engine.search import search_stop

from .conftest import build_case, circuit_c

E_B = 10


def _case(tmp_path, lut):
    s = build_case(tmp_path, circuit_c(), lut, eval_budget=E_B).sctx
    assert s.eval_budget_source == "declared" and s.eval_budget == E_B       # 전제: 선언 실행
    return s


def test_search_stop_below_budget_none(tmp_path, lut_sealed):
    s = _case(tmp_path, lut_sealed)
    s.deadline = None
    s.counters["kernel_calls"] = E_B - 1                                      # 경계 −1
    assert search_stop(s) is None


@pytest.mark.parametrize("kc", [E_B, E_B + 1])
def test_search_stop_at_or_above_budget_eval_budget(tmp_path, lut_sealed, kc):
    s = _case(tmp_path, lut_sealed)
    s.deadline = None
    s.counters["kernel_calls"] = kc                                           # 경계 0 (그리고 + 1)
    assert search_stop(s) == "eval_budget"


def test_search_stop_deadline_passed_wall_budget(tmp_path, lut_sealed):
    s = _case(tmp_path, lut_sealed)
    s.counters["kernel_calls"] = E_B - 1
    s.deadline = time.perf_counter() - 1.0
    assert search_stop(s) == "wall_budget"


def test_search_stop_deadline_future_none(tmp_path, lut_sealed):
    s = _case(tmp_path, lut_sealed)
    s.counters["kernel_calls"] = 0
    s.deadline = time.perf_counter() + 3600.0
    assert search_stop(s) is None


def test_search_stop_no_deadline_zero_calls_none(tmp_path, lut_sealed):
    s = _case(tmp_path, lut_sealed)
    s.deadline = None
    assert search_stop(s) is None


def test_search_stop_uses_derived_search_budget_d_minus_reserve(tmp_path, lut_sealed):
    # oracle (손): 유도 실행(전이 뒤)의 탐색 예산 = D − R (정의 1절). D = E_B + R 로 구성하면 탐색 예산 = E_B = 10.
    s = _case(tmp_path, lut_sealed)
    r = 2 * len(s.domain.variables)
    s.eval_budget = E_B + r
    s.eval_budget_source = "derived_once:floor(B/median_t_eval)@n_evals=%d" % (len(s.domain.variables) + 1)
    s.deadline = None
    s.counters["kernel_calls"] = E_B - 1
    assert search_stop(s) is None
    s.counters["kernel_calls"] = E_B
    assert search_stop(s) == "eval_budget"
