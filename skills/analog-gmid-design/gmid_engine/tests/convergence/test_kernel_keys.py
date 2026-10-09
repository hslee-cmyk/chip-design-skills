"""`kernel_keys(placements, kinds, current) -> (keys, conflicts)` (CONTRACT 3절, 설계 40 §3.9 gap (a)).

oracle (a): 커널 LUT 손잡이는 kind 마다 슬라이스 하나(sizing 계약) -- 한 kind 가 둘 이상 키를 쓰면 충돌. 손으로 고른 배치에서 kind 별 사용 키 집합을 읽는다.
"""
from __future__ import annotations

from gmid_engine.convergence import kernel_keys

from .conftest import placement


def test_single_key_per_kind_replaces_current_and_no_conflict():
    pl = (placement("M1", 30, 2, 6e-7), placement("M2", 30, 4, 1.2e-6), placement("M3", 77, 1, 7.7e-7))
    kinds = {"M1": "nmos", "M2": "nmos", "M3": "pmos"}
    keys, conflicts = kernel_keys(pl, kinds, (("pmos", 1000), ("nmos", 1000)))
    assert keys == (("nmos", 30), ("pmos", 77))           # kind 순
    assert conflicts == ()


def test_kind_without_placed_device_keeps_current_key():
    pl = (placement("M1", 30, 2, 6e-7),)
    keys, conflicts = kernel_keys(pl, {"M1": "nmos"}, (("nmos", 1000), ("pmos", 555)))
    assert keys == (("nmos", 30), ("pmos", 555))
    assert conflicts == ()


def test_two_keys_in_one_kind_is_a_conflict_sorted_ascending():
    pl = (placement("A", 40, 1, 4e-7), placement("B", 12, 1, 1.2e-7), placement("C", 40, 2, 8e-7), placement("D", 9, 1, 9e-8))
    kinds = {"A": "nmos", "B": "nmos", "C": "nmos", "D": "pmos"}
    keys, conflicts = kernel_keys(pl, kinds, (("nmos", 1), ("pmos", 2)))
    assert conflicts == (("nmos", (12, 40)),)
    assert dict(keys)["pmos"] == 9
    assert dict(keys)["nmos"] in (12, 40)                 # 충돌 kind 자리는 사용 키 중 하나(의미 없음, CONTRACT 3절)
