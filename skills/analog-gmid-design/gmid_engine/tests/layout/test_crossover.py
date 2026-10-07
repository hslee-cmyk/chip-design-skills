"""layout/crossover.py -- `find_min_crossover_layout`(+ helper 8개) 복사.

기대값: 손계산 -- 연결 그래프의 홀수 차수 노드 2m 개(m>=1)이면 trail m 개, crossover = m-1(T-join), 0개/2개면 crossover 0;
segment 마다 유효한 walk, finger 총합 보존. + 옛 SD 대조(같은 입력 같은 출력, 같은 프로세스 = 같은 PYTHONHASHSEED;
seed 0·1·2 별도 프로세스도).
"""
from __future__ import annotations

from collections import Counter

import pytest

from gmid_engine.layout.crossover import find_min_crossover_layout
from gmid_engine.layout.transistor import Transistor


def T(name, s, d, nf=1):
    return Transistor(name, "nmos", source=s, drain=d, n_fingers=nf)


def hubleaf(spec):
    return [T(n, "hub", "d" + n, nf) for n, nf in spec]


def assert_segments_valid(devs, out):
    ends = {t.name: {t.source, t.drain} for t in devs}
    total = Counter()
    for seg in out["segments"]:
        ts, ns = seg["transistor_sequence"], seg["node_sequence"]
        assert ts, "빈 segment"
        assert len(ns) == len(ts) + 1
        for i, name in enumerate(ts):
            assert {ns[i], ns[i + 1]} == ends[name]
        total.update(ts)
    assert total == Counter({t.name: t.n_fingers for t in devs})


def test_hand_euler_path_zero_crossover():
    devs = hubleaf([("A", 1), ("B", 1)])
    out = find_min_crossover_layout(devs)
    assert out["crossover_count"] == 0
    assert out["segments"] == [{"transistor_sequence": ["A", "B"], "node_sequence": ["dA", "hub", "dB"]}]
    assert out["odd_nodes"] == ["dA", "dB"]
    assert out["node_pairing_fallback_used"] is None


# (소자, 손계산 홀수 노드, crossover = 홀수/2 - 1)
ODD_CASES = [
    ([("A", 1), ("B", 1), ("C", 1)], ["dA", "dB", "dC", "hub"], 1),      # hub 차수 3
    ([("A", 1), ("B", 1), ("C", 1), ("D", 1)], ["dA", "dB", "dC", "dD"], 1),
    ([("A", 1), ("B", 1), ("C", 1), ("D", 1), ("E", 1), ("F", 1)], ["dA", "dB", "dC", "dD", "dE", "dF"], 2),
    ([("A", 3), ("B", 1), ("C", 2), ("D", 1), ("E", 1)], ["dA", "dB", "dD", "dE"], 1),   # hub 8, dC 2 짝수
]


@pytest.mark.parametrize("spec,odd,xc", ODD_CASES)
def test_hand_t_join_crossover_count(spec, odd, xc):
    assert len(odd) == 2 * (xc + 1)                          # 손계산 표 자체 일관성(홀수 >= 4 = impossible 입력)
    devs = hubleaf(spec)
    out = find_min_crossover_layout(devs)
    assert out["odd_nodes"] == odd
    assert out["crossover_count"] == xc
    assert len(out["segments"]) == xc + 1
    assert_segments_valid(devs, out)


def test_with_matching_pairs_and_general_group():
    # hub-leaf 가 아닌 일반 그룹: matching_pairs 가 있으면 hub 공유 제약이 풀린다.
    devs = [T("A", "s1", "x"), T("B", "s2", "x"), T("C", "s1", "y"), T("D", "s2", "y")]
    # 손: s1 2, s2 2, x 2, y 2 -> circuit, crossover 0
    out = find_min_crossover_layout(devs, matching_pairs=[("A", "B"), ("C", "D")])
    assert out["crossover_count"] == 0
    assert_segments_valid(devs, out)
    devs4 = hubleaf([("A", 1), ("B", 1), ("C", 1), ("D", 1)])
    out4 = find_min_crossover_layout(devs4, matching_pairs=[("A", "B")])
    assert out4["crossover_count"] == 1
    assert isinstance(out4["node_pairing_fallback_used"], bool)
    assert_segments_valid(devs4, out4)


def test_errors():
    with pytest.raises(ValueError):
        find_min_crossover_layout([])
    with pytest.raises(ValueError):                               # hub 다름(matching_pairs 없음)
        find_min_crossover_layout([T("A", "h1", "x"), T("B", "h2", "y")])
    with pytest.raises(ValueError):                               # leaf 중복
        find_min_crossover_layout([T("A", "h", "x"), T("B", "h", "x")])


ORACLE_INPUTS = [
    ("odd4_nopair", [("A", "hub", "dA", 1), ("B", "hub", "dB", 1), ("C", "hub", "dC", 1), ("D", "hub", "dD", 1)], None, None),
    ("odd4_pair1", [("A", "hub", "dA", 1), ("B", "hub", "dB", 1), ("C", "hub", "dC", 1), ("D", "hub", "dD", 1)],
     [("A", "B")], None),
    ("odd6_pairs_sens", [(n, "hub", "d" + n, 1) for n in "ABCDEF"], [("A", "B"), ("C", "D"), ("E", "F")],
     {("A", "B"): "offset", ("C", "D"): "ratio"}),
    ("mixed_nf", [("A", "hub", "dA", 3), ("B", "hub", "dB", 1), ("C", "hub", "dC", 2), ("D", "hub", "dD", 1),
                  ("E", "hub", "dE", 1)], None, None),
    ("general_mirror", [("A", "vx", "o1", 1), ("B", "vx", "o2", 1), ("C", "o1", "g", 1), ("D", "o2", "g", 1),
                        ("E", "vx", "t", 1), ("F", "t", "g", 1), ("G", "vx", "q", 1), ("H", "vx", "r", 1)],
     [("A", "B"), ("C", "D")], {("C", "D"): "offset"}),   # 손: 홀수 g3 q1 r1 vx5 -> crossover 1
]


@pytest.mark.parametrize("name,specs,pairs,sens", ORACLE_INPUTS, ids=[x[0] for x in ORACLE_INPUTS])
def test_same_as_oracle(name, specs, pairs, sens, sd, serialize):
    new = find_min_crossover_layout([T(n, s, d, nf) for n, s, d, nf in specs], pairs, sens)
    old = sd.find_min_crossover_layout(
        [sd.Transistor(n, "nmos", source=s, drain=d, n_fingers=nf) for n, s, d, nf in specs], pairs, sens)
    assert new["crossover_count"] == ORACLE_XC[name]           # 손계산(홀수/2 - 1): crossover 경로를 실제로 탄다
    assert serialize(new) == serialize(old)


ORACLE_XC = {"odd4_nopair": 1, "odd4_pair1": 1, "odd6_pairs_sens": 2, "mixed_nf": 1, "general_mirror": 1}


SEED_CODE = r"""
from gmid_engine.layout.crossover import find_min_crossover_layout
from gmid_engine.layout.transistor import Transistor
sd = load_sd()
spec = [(n, "hub", "d" + n, 1) for n in "ABCD"] + [("E", "hub", "dE", 2)]
pairs = [("A", "B")]
new = find_min_crossover_layout([Transistor(n, "nmos", source=s, drain=d, n_fingers=k) for n, s, d, k in spec], pairs)
old = sd.find_min_crossover_layout([sd.Transistor(n, "nmos", source=s, drain=d, n_fingers=k) for n, s, d, k in spec], pairs)
RESULT = [repr(ser(new)), repr(ser(old)), new["crossover_count"]]
"""


@pytest.mark.parametrize("seed", [0, 1, 2])
def test_same_as_oracle_per_hashseed(seed, seed_runner):
    new, old, xc = seed_runner(SEED_CODE, seed)
    assert xc == 1                                                 # 손: 홀수 dA..dD 4개 -> crossover 1
    assert new == old
