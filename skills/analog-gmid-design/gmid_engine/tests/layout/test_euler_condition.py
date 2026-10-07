"""layout/euler_condition.py -- `check_euler_condition`(+`EulerVerdict`) 복사.

기대값: 손계산 -- 연결 + 홀수 차수 노드 0개 = circuit(시작 = 간선 있는 노드 중 정렬 최소), 2개 = path(시작·끝 = 정렬한
홀수 노드), 4개 이상 또는 비연결 = impossible. + 옛 SD 대조.
"""
from __future__ import annotations

import pytest

from gmid_engine.layout.euler_condition import EulerVerdict, check_euler_condition
from gmid_engine.layout.euler_graph import StackGraph, build_graph
from gmid_engine.layout.transistor import Transistor


def T(name, s, d, nf=1):
    return Transistor(name, "nmos", source=s, drain=d, n_fingers=nf)


# (설명, 소자, kind, odd_nodes, connected, start, end) -- 전부 손계산
HAND = [
    ("A x2 h-da: 차수 h2 da2", [T("A", "h", "da", 2)], "circuit", [], True, "da", "da"),
    ("A,B hub-leaf: da1 db1 h2", [T("A", "h", "da"), T("B", "h", "db")], "path", ["da", "db"], True, "da", "db"),
    ("A x3: h3 da3", [T("A", "h", "da", 3)], "path", ["da", "h"], True, "da", "h"),
    ("사슬 x-y-z", [T("A", "x", "y"), T("B", "y", "z")], "path", ["x", "z"], True, "x", "z"),
    ("hub-leaf 3개 x1: h3 + leaf 1x3 = 홀수 4", [T("A", "h", "da"), T("B", "h", "db"), T("C", "h", "dc")],
     "impossible", ["da", "db", "dc", "h"], True, None, None),
    ("hub-leaf 4개 x1: leaf 4개 홀수", [T(n, "h", "d" + n) for n in "ABCD"],
     "impossible", ["dA", "dB", "dC", "dD"], True, None, None),
    ("비연결 두 덩어리, 차수 전부 짝수", [T("A", "a", "b", 2), T("B", "c", "d", 2)], "impossible", [], False, None, None),
    ("삼각형 x-y-z-x: 전부 차수 2", [T("A", "x", "y"), T("B", "y", "z"), T("C", "z", "x")], "circuit", [], True, "x", "x"),
]


@pytest.mark.parametrize("desc,devs,kind,odd,connected,start,end", HAND, ids=[h[0] for h in HAND])
def test_hand(desc, devs, kind, odd, connected, start, end):
    v = check_euler_condition(build_graph(devs))
    assert isinstance(v, EulerVerdict)
    assert (v.kind, v.odd_nodes, v.connected, v.start, v.end) == (kind, odd, connected, start, end)


def test_odd_count_rule_matches_degree_parity():
    # 오일러 조건 자체를 독립 계산해 대조: 홀수 차수 노드 수 0/2 + 연결 <=> impossible 아님
    devs = [T("A", "h", "da", 2), T("B", "h", "db", 1), T("C", "h", "dc", 1)]
    g = build_graph(devs)
    deg = {n: len(g.adjacency[n]) for n in g.nodes}
    odd = sorted(n for n, d in deg.items() if d % 2)
    assert odd == ["db", "dc"]                       # 손: h=4, da=2, db=1, dc=1
    v = check_euler_condition(g)
    assert v.kind == "path" and v.odd_nodes == odd


def test_empty_graph_is_trivial_circuit():
    v = check_euler_condition(StackGraph())
    assert (v.kind, v.odd_nodes, v.connected, v.start) == ("circuit", [], True, None)


def test_isolated_node_ignored_for_connectivity():
    g = build_graph([T("A", "h", "da", 2)])
    g.nodes.add("lonely")                                   # 간선 없는 노드
    v = check_euler_condition(g)
    assert v.kind == "circuit" and v.connected is True and v.start == "da"


@pytest.mark.parametrize("desc,devs,kind,odd,connected,start,end", HAND, ids=[h[0] for h in HAND])
def test_same_as_oracle(desc, devs, kind, odd, connected, start, end, sd, serialize):
    old_devs = [sd.Transistor(t.name, t.kind, source=t.source, drain=t.drain, n_fingers=t.n_fingers) for t in devs]
    assert serialize(check_euler_condition(build_graph(devs))) == serialize(sd.check_euler_condition(sd.build_graph(old_devs)))
