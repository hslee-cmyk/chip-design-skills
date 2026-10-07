"""layout/euler_graph.py -- `build_graph`(+`StackGraph`) 복사. 기대값: 손계산(노드·간선·라운드로빈 순서) + 옛 SD 대조."""
from __future__ import annotations

import pytest

from gmid_engine.layout.euler_graph import StackGraph, build_graph
from gmid_engine.layout.transistor import Transistor


def T(name, s, d, nf=1, kind="nmos"):
    return Transistor(name, kind, source=s, drain=d, n_fingers=nf)


def test_empty_stackgraph_defaults():
    g = StackGraph()
    assert g.nodes == set() and g.edges == {}
    assert g.adjacency["x"] == []          # defaultdict(list)


def test_round_robin_edge_order_and_adjacency():
    g = build_graph([T("A", "h", "da", 2), T("B", "h", "db", 1)])
    assert g.nodes == {"h", "da", "db"}
    assert list(g.edges) == ["A#0", "B#0", "A#1"]          # finger 를 소자별 1개씩 돌아가며
    assert g.edges["A#0"] == ("A", "h", "da")
    assert g.edges["B#0"] == ("B", "h", "db")
    assert g.adjacency["h"] == [("A#0", "da"), ("B#0", "db"), ("A#1", "da")]
    assert g.adjacency["da"] == [("A#0", "h"), ("A#1", "h")]
    assert g.adjacency["db"] == [("B#0", "h")]


def test_degree_sum_is_twice_edges():
    devs = [T("A", "h", "da", 3), T("B", "h", "db", 2), T("C", "x", "h", 1)]
    g = build_graph(devs)
    assert len(g.edges) == 6
    assert sum(len(v) for v in g.adjacency.values()) == 12


def test_self_loop_device():
    g = build_graph([T("S", "n", "n", 1)])
    assert g.nodes == {"n"}
    assert g.adjacency["n"] == [("S#0", "n"), ("S#0", "n")]


def test_mixed_kind_rejected():
    with pytest.raises(ValueError):
        build_graph([T("A", "h", "da", kind="nmos"), T("B", "h", "db", kind="pmos")])


def test_empty_input():
    g = build_graph([])
    assert g.nodes == set() and g.edges == {}


@pytest.mark.parametrize("specs", [
    [("A", "h", "da", 2), ("B", "h", "db", 1)],
    [("A", "h", "da", 4), ("B", "h", "db", 4), ("C", "h", "dc", 2)],
    [("A", "x", "y", 1), ("B", "y", "z", 3), ("C", "z", "x", 2)],
])
def test_same_as_oracle(specs, sd, serialize):
    new = build_graph([T(*s) for s in specs])
    old = sd.build_graph([sd.Transistor(n, "nmos", source=s, drain=d, n_fingers=nf) for n, s, d, nf in specs])
    assert serialize(new.edges) == serialize(old.edges)
    assert serialize(dict(new.adjacency)) == serialize(dict(old.adjacency))
    assert new.nodes == old.nodes
