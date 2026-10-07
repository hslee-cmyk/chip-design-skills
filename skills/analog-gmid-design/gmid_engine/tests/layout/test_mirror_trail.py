"""layout/mirror_trail.py -- `mirror_symmetric_trail`(+`build_mirror_symmetric_pattern`, `WalkVerdict`, `check_walk_sequence`) 복사.

기대값: 손계산(거울 반사 = 절반 + 중심 + 역순 대응, walk 검산) + 옛 SD 대조.
"""
from __future__ import annotations

import pytest

from gmid_engine.layout.mirror_trail import (WalkVerdict, build_mirror_symmetric_pattern, check_walk_sequence,
                                             mirror_symmetric_trail)
from gmid_engine.layout.transistor import Transistor


def T(name, s, d, nf=1):
    return Transistor(name, "nmos", source=s, drain=d, n_fingers=nf)


# ---- build_mirror_symmetric_pattern ----
def test_pattern_hand():
    pm = {"A": "C", "B": "D", "C": "A", "D": "B", "X": "X"}
    assert build_mirror_symmetric_pattern(["A", "B", "B"], pm) == ["A", "B", "B", "D", "D", "C"]
    assert build_mirror_symmetric_pattern(["A", "B", "B"], pm, center="X") == ["A", "B", "B", "X", "D", "D", "C"]
    assert build_mirror_symmetric_pattern(["A", "P"], {"A": "B", "P": None}) == ["A", "P", "B"]   # None = 다리, 미러 제외
    assert build_mirror_symmetric_pattern([], {}) == []


# ---- check_walk_sequence ----
AB = [T("A", "hub", "da"), T("B", "hub", "db")]


def test_walk_ok_hand():
    v = check_walk_sequence(["A", "B"], AB)
    assert isinstance(v, WalkVerdict)
    assert v.ok is True and v.node_path == ["da", "hub", "db"] and v.finger_count_mismatch == {}


def test_walk_break_hand():
    devs = AB + [T("C", "x", "y")]
    v = check_walk_sequence(["A", "C", "B"], devs)
    assert v.ok is False and v.break_index == 1 and v.node_path == []


def test_walk_count_mismatch_hand():
    v = check_walk_sequence(["A"], [T("A", "hub", "da", 2)])
    assert v.ok is False
    assert v.finger_count_mismatch == {"A": {"expected": 2, "actual": 1}}
    assert v.node_path in (["hub", "da"], ["da", "hub"])            # 경로 자체는 이어진다


def test_walk_unknown_first_and_empty():
    v = check_walk_sequence(["Z"], AB)
    assert v.ok is False and v.break_index == 0
    assert check_walk_sequence([], []).ok is True
    e = check_walk_sequence([], AB)
    assert e.ok is False and e.finger_count_mismatch == {"A": {"expected": 1, "actual": 0},
                                                          "B": {"expected": 1, "actual": 0}}


def test_walkverdict_defaults():
    v = WalkVerdict(ok=True)
    assert (v.node_path, v.break_index, v.break_reason, v.finger_count_mismatch) == ([], None, "", {})


# ---- mirror_symmetric_trail ----
def test_trail_hand_pair_nf2():
    # 절반 = A x2 (hub-x 이중 간선, circuit, 시작 hub) -> [A,A]; 반사 -> [A,A,B,B]; walk 시작은 hub 만 성립.
    out = mirror_symmetric_trail([T("A", "hub", "x", 2), T("B", "hub", "y", 2)], [("A", "B")])
    assert out == {"node_sequence": ["hub", "x", "hub", "y", "hub"], "transistor_sequence": ["A", "A", "B", "B"]}


def test_trail_hand_pair_nf1():
    out = mirror_symmetric_trail([T("A", "vx", "o1"), T("B", "vx", "o2")], [("A", "B")])
    assert out == {"node_sequence": ["o1", "vx", "o2"], "transistor_sequence": ["A", "B"]}


def test_trail_none_cases():
    assert mirror_symmetric_trail([T("A", "h", "x", 2), T("B", "h", "y", 1)], [("A", "B")]) is None   # nf 다름
    assert mirror_symmetric_trail([T("A", "s1", "x"), T("B", "s2", "y")], [("A", "B")]) is None       # 공유 넷 없음


ORACLE_GROUPS = [
    ("pair_nf2", [("A", "hub", "x", 2), ("B", "hub", "y", 2)], [("A", "B")]),
    ("pair_plus_even_self", [("A", "vx", "o1", 2), ("B", "vx", "o2", 2), ("P", "vx", "t", 2)], [("A", "B")]),
    ("bridge_odd_self", [("A", "g", "vy", 1), ("B", "g", "vz", 1), ("M5", "gnd", "vy", 1), ("M6", "gnd", "vz", 1),
                         ("K", "g", "k", 1)], [("A", "B"), ("M5", "M6")]),
    ("two_pairs", [("A", "s", "x", 1), ("B", "s", "y", 1), ("C", "x", "t", 1), ("D", "y", "t", 1)], [("A", "B"), ("C", "D")]),
    ("pair_out_of_group_ignored", [("A", "h", "x", 2), ("B", "h", "y", 2)], [("A", "B"), ("Q", "R")]),
]


@pytest.mark.parametrize("name,specs,pairs", ORACLE_GROUPS, ids=[g[0] for g in ORACLE_GROUPS])
def test_trail_same_as_oracle(name, specs, pairs, sd, serialize):
    new = mirror_symmetric_trail([T(n, s, d, nf) for n, s, d, nf in specs], pairs)
    old = sd.mirror_symmetric_trail([sd.Transistor(n, "nmos", source=s, drain=d, n_fingers=nf)
                                     for n, s, d, nf in specs], pairs)
    assert serialize(new) == serialize(old)


def test_oracle_inputs_not_all_none(sd):
    # 공허 통과 방지: 대조 입력 중 성공(None 아님) 결과가 실제로 있다
    got = [mirror_symmetric_trail([T(n, s, d, nf) for n, s, d, nf in specs], pairs) for _, specs, pairs in ORACLE_GROUPS]
    assert sum(r is not None for r in got) >= 3


@pytest.mark.parametrize("seq,devs", [
    (["A", "B"], [("A", "hub", "da", 1), ("B", "hub", "db", 1)]),
    (["A", "C", "B"], [("A", "hub", "da", 1), ("B", "hub", "db", 1), ("C", "x", "y", 1)]),
    (["A", "A", "B"], [("A", "hub", "da", 1), ("B", "hub", "db", 1)]),
])
def test_walk_same_as_oracle(seq, devs, sd, serialize):
    new = check_walk_sequence(seq, [T(*d) for d in devs])
    old = sd.check_walk_sequence(seq, [sd.Transistor(n, "nmos", source=s, drain=d, n_fingers=nf) for n, s, d, nf in devs])
    assert serialize(new) == serialize(old)


SEED_CODE = r"""
from gmid_engine.layout.mirror_trail import mirror_symmetric_trail
from gmid_engine.layout.transistor import Transistor
sd = load_sd()
spec = [("A", "vx", "o1", 2), ("B", "vx", "o2", 2), ("P", "vx", "t", 2), ("C", "o1", "g", 1), ("D", "o2", "g", 1)]
pairs = [("A", "B"), ("C", "D")]
new = mirror_symmetric_trail([Transistor(n, "nmos", source=s, drain=d, n_fingers=k) for n, s, d, k in spec], pairs)
old = sd.mirror_symmetric_trail([sd.Transistor(n, "nmos", source=s, drain=d, n_fingers=k) for n, s, d, k in spec], pairs)
RESULT = [repr(ser(new)), repr(ser(old)), new is None]
"""


@pytest.mark.parametrize("seed", [0, 1, 2])
def test_trail_same_as_oracle_per_hashseed(seed, seed_runner):
    new, old, is_none = seed_runner(SEED_CODE, seed)
    assert new == old
