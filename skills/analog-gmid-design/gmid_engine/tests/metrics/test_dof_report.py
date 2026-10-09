"""metrics/dof_report.py -- `dof_report(variables, equations) -> DofReport` (metrics CONTRACT 10.7, 설계 41 4.5, D-GB4e).

oracle (a) 구성으로 정답이 정해진 합성 입력: 변수·등식 이분 그래프를 손으로 만들고, 최대 이분 매칭 크기(구조 rank)·매칭 안 되는
등식(과제약)·매칭 안 되는 변수(자유도)를 손으로 센다(쾨니그 정리 수준의 작은 그래프 -- 모든 매칭을 눈으로 열거할 수 있다).
피검 함수를 기대값 생성에 쓰지 않는다.
"""
from __future__ import annotations

import itertools

import pytest

from gmid_engine.metrics import DofReport, dof_report


def _max_matching_bruteforce(variables, equations):
    """oracle (b) 다른 방법(전수 탐색): 등식마다 '변수 하나 또는 없음' 배정을 모두 열거해 서로 다른 변수만 쓰는 배정의 최대 크기."""
    eqs = sorted(equations)
    best = 0
    choices = [list(equations[e]) + [None] for e in eqs]
    for pick in itertools.product(*choices):
        used = [p for p in pick if p is not None]
        if len(used) == len(set(used)):
            best = max(best, len(used))
    return best


def test_square_system_has_full_rank_and_no_free_variable():
    # 변수 {a, b}, 등식 e1(a), e2(a, b): 매칭 e1-a, e2-b (손) -> rank 2, 남는 변수·등식 없음
    r = dof_report(("a", "b"), {"e1": ("a",), "e2": ("a", "b")})
    assert isinstance(r, DofReport)
    assert r.structural_rank == 2
    assert (r.n_variables, r.n_equations) == (2, 2)
    assert r.status == "square"
    assert tuple(r.unmatched_equations) == () and tuple(r.free_variables) == ()


def test_two_equations_competing_for_one_variable_is_overconstrained():
    # 변수 {a}, 등식 e1(a), e2(a): 한 변수를 두 등식이 겨룬다 -> rank 1, 등식 하나 남음 = 과제약(41 4.5 INFEASIBLE_TARGET 근거)
    r = dof_report(("a",), {"e1": ("a",), "e2": ("a",)})
    assert r.structural_rank == 1
    assert r.status == "overconstrained"
    assert len(r.unmatched_equations) == 1 and r.unmatched_equations[0] in ("e1", "e2")
    # competing_pairs = (매칭 못 한 등식, 그 변수를 가져간 등식) -- 순서 무관하게 {e1, e2}
    assert [set(p) for p in r.competing_pairs] == [{"e1", "e2"}]
    assert tuple(r.free_variables) == ()


def test_free_variables_are_listed():
    # 변수 {a, b, c}, 등식 e1(a): rank 1, 남는 변수 b, c(탐색 자유도)
    r = dof_report(("a", "b", "c"), {"e1": ("a",)})
    assert r.structural_rank == 1
    assert r.status == "free_dof"
    assert sorted(r.free_variables) == ["b", "c"]
    assert tuple(r.unmatched_equations) == ()


def test_augmenting_path_is_used_not_greedy():
    # e1(a, b), e2(a): 탐욕(이름 순 e1 -> a)이면 e2 가 막히지만 증가 경로 e2-a, e1-b 로 rank 2 (Kuhn, 계약 10.7 '최대 이분 매칭')
    r = dof_report(("a", "b"), {"e1": ("a", "b"), "e2": ("a",)})
    assert r.structural_rank == 2
    assert r.status == "square"
    assert tuple(r.unmatched_equations) == ()


def test_variable_absent_from_equations_and_isolated_equation_counts():
    # e2 는 변수가 없다(손: 매칭 불가) -> 과제약; v2 는 아무 등식도 읽지 않는다 -> 자유
    r = dof_report(("v1", "v2"), {"e1": ("v1",), "e2": ()})
    assert r.structural_rank == 1
    assert r.status == "overconstrained"
    assert list(r.unmatched_equations) == ["e2"]
    assert list(r.free_variables) == ["v2"]


@pytest.mark.parametrize("seed", range(6))
def test_rank_equals_bruteforce_maximum_matching(seed):
    # oracle (b): 작은 무작위 이분 그래프에서 전수 탐색 최대 매칭과 같다
    import random
    rnd = random.Random(seed)
    variables = ["v%d" % i for i in range(rnd.randint(2, 5))]
    equations = {"e%d" % j: tuple(sorted(rnd.sample(variables, rnd.randint(0, len(variables)))))
                 for j in range(rnd.randint(1, 5))}
    r = dof_report(variables, equations)
    best = _max_matching_bruteforce(variables, equations)
    assert r.structural_rank == best
    assert len(r.unmatched_equations) == len(equations) - best
    assert len(r.free_variables) == len(variables) - best
    assert r.status == ("overconstrained" if best < len(equations) else ("square" if best == len(variables) else "free_dof"))


def test_numeric_rank_is_left_to_stage_b():
    # 계약 10.7: 수치 rank(41 4.5 B2)는 평가 커널 표본이 필요한 단계 B 몫 -> numeric_ranks = ()
    assert tuple(dof_report(("a",), {"e": ("a",)}).numeric_ranks) == ()


def test_deterministic_and_name_bijection_invariant():
    vs = ("a", "b", "c", "d")
    eqs = {"e1": ("a", "b"), "e2": ("b",), "e3": ("b", "c"), "e4": ("b",)}
    r1 = dof_report(vs, eqs)
    r2 = dof_report(vs, eqs)
    assert r1 == r2
    ren_v = {"a": "q", "b": "z", "c": "m", "d": "b"}
    ren_e = {"e1": "x9", "e2": "a0", "e3": "k", "e4": "e"}
    r3 = dof_report(tuple(ren_v[v] for v in reversed(vs)),
                    {ren_e[e]: tuple(ren_v[v] for v in vv) for e, vv in reversed(list(eqs.items()))})
    # 이름이 바뀌어도 구조 수치는 같다(매칭 크기·남는 개수·상태)
    assert (r3.structural_rank, r3.status, len(r3.unmatched_equations), len(r3.free_variables)) == \
        (r1.structural_rank, r1.status, len(r1.unmatched_equations), len(r1.free_variables))
    # 손: b 를 e2·e4 가 겨루고(e1 -> a, e3 -> c 가능) -> rank 3, 남는 등식 1, 남는 변수 d
    assert r1.structural_rank == 3 and len(r1.unmatched_equations) == 1 and list(r1.free_variables) == ["d"]
