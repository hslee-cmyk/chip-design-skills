"""layout/euler_trail.py -- `hierholzer` 복사. 기대값: 손계산(trail 성질 + 작은 그래프 정확값) + 옛 SD 대조."""
from __future__ import annotations

from collections import Counter

import pytest

from gmid_engine.layout.euler_condition import check_euler_condition
from gmid_engine.layout.euler_graph import build_graph
from gmid_engine.layout.euler_trail import hierholzer
from gmid_engine.layout.transistor import Transistor


def T(name, s, d, nf=1):
    return Transistor(name, "nmos", source=s, drain=d, n_fingers=nf)


def assert_valid_trail(devs, nodes, trs, start):
    """손 정의: 길이 = finger 수 + 1, 매 단계 소자가 두 노드를 잇고, 소자별 사용 횟수 = n_fingers, 시작 노드 = start."""
    ends = {t.name: {t.source, t.drain} for t in devs}
    assert len(nodes) == len(trs) + 1
    assert nodes[0] == start
    for i, name in enumerate(trs):
        assert {nodes[i], nodes[i + 1]} == ends[name] or (nodes[i] == nodes[i + 1] and ends[name] == {nodes[i]})
    assert Counter(trs) == Counter({t.name: t.n_fingers for t in devs})


def test_hand_path_exact():
    devs = [T("A", "hub", "da"), T("B", "hub", "db")]
    g = build_graph(devs)
    assert hierholzer(g, "da") == (["da", "hub", "db"], ["A", "B"])


def test_hand_circuit_exact():
    g = build_graph([T("A", "h", "da", 2)])
    assert hierholzer(g, "da") == (["da", "h", "da"], ["A", "A"])


GRAPHS = [
    [T("A", "h", "da", 2), T("B", "h", "db", 2)],
    [T("A", "h", "da", 4), T("B", "h", "db", 2), T("C", "h", "dc", 1), T("D", "h", "dd", 1)],
    [T("A", "x", "y"), T("B", "y", "z"), T("C", "z", "x")],
    [T("A", "x", "y", 3)],
    [T("A", "h", "da", 3), T("B", "h", "db", 2), T("C", "h", "dc", 3)],
]


@pytest.mark.parametrize("devs", GRAPHS)
def test_valid_trail_from_verdict_start(devs):
    g = build_graph(devs)
    v = check_euler_condition(g)
    assert v.kind in ("circuit", "path")                      # 입력이 실제로 오일러 가능(공허 통과 방지)
    nodes, trs = hierholzer(g, v.start)
    assert_valid_trail(devs, nodes, trs, v.start)
    assert nodes[-1] == v.end


def test_does_not_mutate_graph():
    g = build_graph([T("A", "h", "da", 2), T("B", "h", "db", 2)])
    before = {k: list(v) for k, v in g.adjacency.items()}
    hierholzer(g, "da")
    assert {k: list(v) for k, v in g.adjacency.items()} == before


@pytest.mark.parametrize("devs", GRAPHS)
def test_same_as_oracle(devs, sd):
    old_devs = [sd.Transistor(t.name, t.kind, source=t.source, drain=t.drain, n_fingers=t.n_fingers) for t in devs]
    og = sd.build_graph(old_devs)
    ov = sd.check_euler_condition(og)
    g = build_graph(devs)
    assert hierholzer(g, check_euler_condition(g).start) == sd.hierholzer(og, ov.start)
