"""`key_exclusion(pdk, row_groups, placements, sized_w, excluded, colour) -> ((행 그룹 rid, 폭 키), new_excluded | None)` (interface 20261104-wb1 §8
'레이아웃 뒤', 설계 40 §3.7-A 6 '키 제외 규칙 재정의').

oracle (a/d): 손 입력과 손 비교 -- 어긋남 |ln(W_실현/W_사이징)| 이 가장 큰 소자가 속한 행 그룹의 지금 finger 폭 후보(그 소자 배치 키)만 뺀다.
toy: 두 행 그룹, 어긋남 0.1·0.3 근방(ln 1.1 = 0.0953 < ln 1.35 = 0.3001) -> 둘째 그룹의 후보만 줄고 첫 그룹 후보는 그대로.
동률은 구조 색 `colour` 순이고 이름이 정하지 않는다(이름만 바꾼 쌍에서 같은 색 쪽 그룹이 뽑힌다 -- 변성).
"""
from __future__ import annotations

import math

from gmid_engine.convergence import key_exclusion
from gmid_engine.layout import RowGroup

from .conftest import pdk, placement


def groups(*specs):
    return tuple(RowGroup(rid, "nmos", "gnd", tuple(members)) for rid, members in specs)


def test_group_with_largest_shift_loses_only_its_own_key():
    base = pdk((("nmos", (10, 20, 30)),))
    rg = groups(("R1", ("N1",)), ("R2", ("N2",)))
    pl = (placement("N1", 10, 11, 1.1e-6), placement("N2", 20, 3, 1.35e-6))
    sized = {"N1": 1e-6, "N2": 1e-6}
    assert math.log(1.35) > math.log(1.1) > 0                                   # 손: 0.3001 > 0.0953
    got, new_excluded = key_exclusion(base, rg, pl, sized, (), {"N1": 0, "N2": 1})
    assert got == ("R2", 20)
    assert new_excluded == (("R2", (20,)),)                                     # R1 의 후보는 그대로 (항목 없음)
    assert rg[0].excluded_keys == () and rg[1].excluded_keys == ()              # 입력 불변


def test_shrinking_w_counts_by_absolute_log_ratio():
    # N1: 0.5 / 1.0 -> |ln 0.5| = 0.693 > N2: ln 1.5 = 0.405 -> 첫 그룹
    base = pdk((("nmos", (10, 20)),))
    rg = groups(("R1", ("N1",)), ("R2", ("N2",)))
    pl = (placement("N1", 20, 1, 0.5e-6), placement("N2", 10, 1, 1.5e-6))
    got, new_excluded = key_exclusion(base, rg, pl, {"N1": 1e-6, "N2": 1e-6}, (), {"N1": 0, "N2": 1})
    assert got == ("R1", 20)
    assert new_excluded == (("R1", (20,)),)


def test_previously_excluded_keys_accumulate_sorted_and_last_candidate_gives_none():
    base = pdk((("nmos", (10, 20, 30)),))
    rg = groups(("R1", ("N1",)))
    pl = (placement("N1", 20, 1, 3e-6),)
    sized = {"N1": 1e-6}
    got, new_excluded = key_exclusion(base, rg, pl, sized, (("R1", (30,)),), {"N1": 0})
    assert got == ("R1", 20) and new_excluded == (("R1", (20, 30)),)            # 후보 10 이 남는다 -> 계속
    got2, none = key_exclusion(base, rg, pl, sized, (("R1", (10, 30)),), {"N1": 0})
    assert got2 == ("R1", 20) and none is None                                  # 20 을 빼면 후보 0 -> 더 시도할 폭 없음


def test_other_groups_candidates_survive_when_one_group_runs_out():
    base = pdk((("nmos", (10, 20)),))
    rg = groups(("R1", ("N1",)), ("R2", ("N2",)))
    pl = (placement("N1", 10, 1, 1.2e-6), placement("N2", 20, 1, 3e-6))
    got, new_excluded = key_exclusion(base, rg, pl, {"N1": 1e-6, "N2": 1e-6}, (("R2", (10,)),), {"N1": 0, "N2": 1})
    assert got == ("R2", 20) and new_excluded is None                           # R2 후보 소진이지만 R1 후보는 남아 있음 -- 이 호출의 판정은 어긋남 큰 그룹 기준


def test_tie_is_broken_by_structural_colour_not_name():
    base = pdk((("nmos", (10, 20)),))
    pl = (placement("A", 10, 1, 2e-6), placement("B", 20, 1, 2e-6))             # 둘 다 ln 2
    sized = {"A": 1e-6, "B": 1e-6}
    rg = groups(("R1", ("A",)), ("R2", ("B",)))
    first, _ = key_exclusion(base, rg, pl, sized, (), {"A": 0, "B": 1})
    # 같은 구조에서 이름만 바꾼다: A <-> B (색은 구조 자리에 붙어 있다)
    pl2 = (placement("B", 10, 1, 2e-6), placement("A", 20, 1, 2e-6))
    rg2 = groups(("R1", ("B",)), ("R2", ("A",)))
    second, _ = key_exclusion(base, rg2, pl2, sized, (), {"B": 0, "A": 1})
    assert first == second                                                      # 이름 순서가 반대여도 같은 구조 자리 그룹
    assert first[0] in ("R1", "R2")
