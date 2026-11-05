"""XRUN-F1 card C interface card C1 -- `search_ceiling(sctx, *, final=False)`: 탐색 예산, 유도 전이, 전이 경계 (C-T1, C-T2).

정의(interface 1절): n_θ = len(sctx.domain.variables), R = 2 n_θ. 선언 실행의 탐색 예산 = E_B. 유도 실행은 D = ⌊front_budget_s / 평가 시간 중앙값⌋,
탐색 예산 = D − R. 유도 뒤 sctx.eval_budget = D.

oracle: (손) 구성으로 정답이 정해진 합성 입력. 평가 시간은 test 가 정한다(균일 0.5 s, 예산 B = 100 s -> 중앙값 0.5 -> D = ⌊100/0.5⌋ = 200;
이진 부동소수로 정확히 표현되는 값이라 바닥 연산에 반올림 오차가 없다). 경계값은 정의에서 손으로 낸다(D − R, D − R − 1, D − R + 1).
'첫 n_θ + 1개만 쓴다'는 뒤쪽에 큰 값(5.0 s)을 붙여 전체 중앙값이 달라지게 해서 가른다 -- 첫 n_θ + 1개 중앙값 0.5 -> D = 200,
전체 중앙값이었다면 값이 달라진다(구성). 피검 함수·식을 다시 쓰지 않는다. 가짜 sctx 는 쓰지 않고 build_case 가 만든 sctx 의 interface 칸만 바꾼다.
"""
import re

import pytest

from gmid_engine.search import search_ceiling

from .conftest import build_case, circuit_c

B_S = 100.0                  # 선언한 front_budget_s (build_case budget_s)
T_EVAL = 0.5                 # 평가 시간 균일값 (손): D = ⌊100 / 0.5⌋ = 200
D = 200
SRC_RE = re.compile(r"derived_once:floor\(B/median_t_eval\)@n_evals=\d+")      # C11: n_evals 값은 단언하지 않는다


def _derived_case(tmp_path, lut, n_times, extra=()):
    """eval_budget None 실행. 평가 시간 = 앞 n_times 개 0.5 + extra (test 가 채운다). -> (sctx, n_θ, R)."""
    case = build_case(tmp_path, circuit_c(), lut, eval_budget=None, budget_s=B_S)
    s = case.sctx
    n = len(s.domain.variables)
    s.eval_times.extend([T_EVAL] * n_times)
    s.eval_times.extend(extra)
    return s, n, 2 * n


@pytest.mark.parametrize("e_b", [1, 2, 7, 40])
def test_search_ceiling_declared_returns_e_b_even_when_small(tmp_path, lut_sealed, e_b):
    # oracle (손): C1 '선언: E_B 그대로. 작은 E_B도 거부 없음.'
    case = build_case(tmp_path, circuit_c(), lut_sealed, eval_budget=40)
    s = case.sctx
    assert s.eval_budget_source == "declared"          # 전제: 선언 실행
    s.eval_budget = e_b
    assert search_ceiling(s) == e_b
    assert search_ceiling(s, final=True) == e_b


def test_search_ceiling_before_derivation_none_and_state_unchanged(tmp_path, lut_sealed):
    # oracle (손): C1 'eval_budget None, 평가 시간 < n_θ + 1개, final=False: None, 상태 불변.' n_θ 개(= n_θ + 1 − 1)까지 시험.
    case = build_case(tmp_path, circuit_c(), lut_sealed, eval_budget=None, budget_s=B_S)
    s = case.sctx
    n = len(s.domain.variables)
    src0 = s.eval_budget_source
    for k in range(n + 1):                              # 평가 시간 0 .. n_θ 개
        del s.eval_times[:]
        s.eval_times.extend([T_EVAL] * k)
        assert search_ceiling(s) is None, k
        assert s.eval_budget is None and s.eval_budget_source == src0, k
        assert len(s.eval_times) == k, k                # 평가 시간 목록도 불변


def test_search_ceiling_derives_from_first_n_plus_one_times_only(tmp_path, lut_sealed):
    # oracle (손): C1 '평가 시간 ≥ n_θ + 1개: 첫 n_θ + 1개로 D를 내(더 많아도 같은 값)'. 뒤에 5.0 s 를 10개 붙여도 D = 200, 탐색 예산 = D − R.
    exact, n, r = _derived_case(tmp_path / "exact", lut_sealed, 0)
    exact.eval_times.extend([T_EVAL] * (n + 1))
    assert search_ceiling(exact) == D - r
    assert exact.eval_budget == D
    assert SRC_RE.fullmatch(exact.eval_budget_source), exact.eval_budget_source
    more, n2, r2 = _derived_case(tmp_path / "more", lut_sealed, n + 1, extra=[5.0] * 10)
    assert search_ceiling(more) == D - r2              # 더 많아도 같은 값(전체 중앙값이면 달라진다)
    assert more.eval_budget == D
    assert SRC_RE.fullmatch(more.eval_budget_source), more.eval_budget_source


def test_search_ceiling_after_derivation_is_stable(tmp_path, lut_sealed):
    # oracle (손): 전이 뒤 호출은 같은 D − R (평가 시간이 더 늘어도 D 를 다시 내지 않는다 -- 유도는 한 번).
    s, n, r = _derived_case(tmp_path, lut_sealed, 0)
    s.eval_times.extend([T_EVAL] * (n + 1))
    assert search_ceiling(s) == D - r
    src = s.eval_budget_source
    s.eval_times.extend([5.0] * 20)
    assert search_ceiling(s) == D - r
    assert s.eval_budget == D and s.eval_budget_source == src


# ---------------------------------------------------------------- C-T2 전이 경계

def test_search_ceiling_transition_kernel_calls_at_search_budget_value_error(tmp_path, lut_sealed):
    # oracle (손): C1 '그 전이 호출: kernel_calls ≥ D − R -> ValueError(메시지에 time_budget_below_search_reserve)'. 경계 = D − R.
    s, n, r = _derived_case(tmp_path, lut_sealed, 0)
    s.eval_times.extend([T_EVAL] * (n + 1))
    s.counters["kernel_calls"] = D - r
    with pytest.raises(ValueError, match="time_budget_below_search_reserve"):
        search_ceiling(s)


def test_search_ceiling_transition_above_boundary_value_error(tmp_path, lut_sealed):
    # oracle (손): 같은 문장, 경계 + 1.
    s, n, r = _derived_case(tmp_path, lut_sealed, 0)
    s.eval_times.extend([T_EVAL] * (n + 1))
    s.counters["kernel_calls"] = D - r + 1
    with pytest.raises(ValueError, match="time_budget_below_search_reserve"):
        search_ceiling(s)


def test_search_ceiling_transition_one_below_boundary_passes(tmp_path, lut_sealed):
    # oracle (손): C1 '= D − R − 1 -> 통과, 반환 D − R'.
    s, n, r = _derived_case(tmp_path, lut_sealed, 0)
    s.eval_times.extend([T_EVAL] * (n + 1))
    s.counters["kernel_calls"] = D - r - 1
    assert search_ceiling(s) == D - r
    assert s.eval_budget == D


def test_search_ceiling_after_transition_above_budget_runtime_error(tmp_path, lut_sealed):
    # oracle (손): C1 '전이 뒤 호출: kernel_calls > 탐색 예산 -> RuntimeError. = 탐색 예산은 정상.'
    s, n, r = _derived_case(tmp_path, lut_sealed, 0)
    s.eval_times.extend([T_EVAL] * (n + 1))
    assert search_ceiling(s) == D - r                  # 전이(kernel_calls 0)
    s.counters["kernel_calls"] = D - r                 # = 탐색 예산: 정상
    assert search_ceiling(s) == D - r
    s.counters["kernel_calls"] = D - r + 1             # > 탐색 예산: 주입
    with pytest.raises(RuntimeError):
        search_ceiling(s)


# ---------------------------------------------------------------- final=True

def test_search_ceiling_final_derives_from_all_available_times(tmp_path, lut_sealed):
    # oracle (손): C1 'final=True: eval_budget None 이고 평가 시간 ≥ 1개면 그 전부로 유도.' 1개(< n_θ + 1)여도 D = ⌊100/0.5⌋ = 200.
    s, n, r = _derived_case(tmp_path, lut_sealed, 1)
    assert n + 1 > 1                                   # 전제: 1개는 n_θ + 1 미만
    assert search_ceiling(s) is None                   # final=False 는 아직 None
    assert search_ceiling(s, final=True) == D - r
    assert s.eval_budget == D
    assert SRC_RE.fullmatch(s.eval_budget_source), s.eval_budget_source


def test_search_ceiling_final_boundary(tmp_path, lut_sealed):
    # oracle (손): C1 'final=True: kernel_calls = D − R 통과, + 1 ValueError'.
    ok, n, r = _derived_case(tmp_path / "ok", lut_sealed, 1)
    ok.counters["kernel_calls"] = D - r
    assert search_ceiling(ok, final=True) == D - r
    bad, n2, r2 = _derived_case(tmp_path / "bad", lut_sealed, 1)
    bad.counters["kernel_calls"] = D - r2 + 1
    with pytest.raises(ValueError, match="time_budget_below_search_reserve"):
        search_ceiling(bad, final=True)


def test_search_ceiling_final_without_times_none(tmp_path, lut_sealed):
    # oracle (손): C1 '평가 시간 0개면 None'.
    s, n, r = _derived_case(tmp_path, lut_sealed, 0)
    assert search_ceiling(s, final=True) is None
    assert s.eval_budget is None
