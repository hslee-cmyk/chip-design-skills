"""`admit_candidates(survivors, candidates)` -- 교대 재실행 후보 (CONTRACT 9절, DEC-79 '순위가 뒤집힌 점에서는 MOD8 을 다시 돈다').

oracle (a): 후보 = (전력, 탐색 축 면적 -- 대리값), 남은 점 = (전력, 레이아웃 면적). 동률 폭: 전력 = 두 점 b_P 큰 값, 면적 = 남은 점 floorplan 의
ΔA_tie(후보끼리는 남은 점 자기 쌍 폭의 최솟값). 손으로 지배 판정한다.
"""
from __future__ import annotations

from gmid_engine.convergence import admit_candidates

from .conftest import candidate, converged

U = 1e-12           # 격자 1e-8 x bbox 1e-4
B = 1e-4
BP = 1e-6


def test_hand_derived_admission():
    s1 = converged("S1", 1.0e-3, 10 * U, B, b_p=BP)
    c_alive = candidate("C1", 2.0e-3, 5 * U, b_p=BP)               # S1 대비 면적 5 U 나음 -> 비지배
    c_dom = candidate("C2", 2.0e-3, 10.5 * U, b_p=BP)              # S1 대비 면적 동률(0.5 U), 전력 나쁨 -> 지배당함
    c_fold = candidate("C3", 2.0e-3 + 0.5 * BP, 5.5 * U, b_p=BP)   # C1 대비 모든 축 동률(후보끼리 폭 = S1 자기 폭 1 U) -> C1 로 접힘
    c_first = candidate("C0", 0.5e-3, 30 * U, b_p=BP)              # 전력이 가장 낮음 -> 비지배
    out = admit_candidates((s1,), (c_alive, c_dom, c_fold, c_first))
    assert [c.point_id for c in out] == ["C1", "C0"]               # 후보 입력 순서
    assert out[0] is c_alive


def test_empty_inputs_give_nothing():
    s1 = converged("S1", 1.0e-3, 10 * U, B)
    assert admit_candidates((), (candidate("C", 1e-4, 1 * U),)) == ()
    assert admit_candidates((s1,), ()) == ()


def test_candidate_dominating_survivor_is_admitted():
    s1 = converged("S1", 2.0e-3, 10 * U, B, b_p=BP)
    c = candidate("C", 1.0e-3, 5 * U, b_p=BP)
    assert [x.point_id for x in admit_candidates((s1,), (c,))] == ["C"]
