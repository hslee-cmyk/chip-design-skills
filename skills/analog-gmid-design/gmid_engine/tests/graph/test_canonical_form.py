"""graph CONTRACT 4.7 [r11] `canonical_form(source, element_marks=(), node_marks=()) -> Canonical(wl, position, generators)`.

(옛 sizing `canonical_labeling` test 를 graph 로 옮김 -- U2 에서 정준 라벨링이 graph 로 이동, rule H.)
oracle:
- (b) 독립 구현(`canon_graphs`): 4.7 그래프 그대로의 라벨 그래프, 1-WL 분할(`wl_classes`), 생성자 검증(`is_automorphism` -- 처음 색·라벨 엣지
  다중도 보존 전단사).
- 정준성: 위치로 다시 쓴 그래프(cert)가 이름 전단사·원소/넷 순서 섞기에 같고, 같은 그래프를 다르게 그려도 같고, 비동형이면 다르다.
- (a) 구성: 손 그래프(2단자 원소 = 무향 엣지)의 동형 관계.
graph `.py` 소스는 열람하지 않았다.
"""
from __future__ import annotations

import random

import pytest

from gmid_engine.graph import Canonical, canonical_form

from canon_graphs import (HAND, Circuit, cap, cert, edge_circuit, is_automorphism, labeled_graph, partition,
                           random_circuit, ring, sigma_of, vertex_map, wl_classes)


def _cf(c, em=(), nm=()):
    return canonical_form(c, em, nm)


@pytest.mark.parametrize("name", sorted(HAND))
def test_shape_positions_bijection(name):
    c = HAND[name]
    r = _cf(c)
    assert isinstance(r, Canonical)
    col, nb = labeled_graph(c)
    assert set(r.position) == set(col) and set(r.wl) == set(col)
    assert sorted(r.position.values()) == list(range(len(col)))
    assert all(isinstance(v, int) for v in r.wl.values())


@pytest.mark.parametrize("name", sorted(HAND))
def test_wl_partition_equals_independent_1wl(name):
    """wl = 선언 표시 없는 1-WL 색 -- 분할이 독립 1-WL 분할과 같다(정수 값은 서명 정렬에 달려 분할로 본다)."""
    c = HAND[name]
    col, nb = labeled_graph(c)
    assert partition(_cf(c).wl) == partition(wl_classes(col, nb))


@pytest.mark.parametrize("seed", range(25))
def test_wl_partition_random(seed):
    c = random_circuit(seed)
    col, nb = labeled_graph(c)
    assert partition(_cf(c).wl) == partition(wl_classes(col, nb))


@pytest.mark.parametrize("name", sorted(HAND))
def test_generators_are_automorphisms(name):
    """4.7 (b): 생성자는 모두 자기동형(움직인 정점만 적힘)."""
    c = HAND[name]
    col, nb = labeled_graph(c)
    gens = _cf(c).generators
    assert gens                                                             # 손 그래프는 모두 비자명 군(구성)
    for g in gens:
        m = dict(g)
        assert m and all(v != w for v, w in m.items())                      # 움직인 정점만
        assert is_automorphism(col, nb, m)


@pytest.mark.parametrize("seed", range(30))
def test_generators_are_automorphisms_random(seed):
    c = random_circuit(100 + seed)
    col, nb = labeled_graph(c)
    assert all(is_automorphism(col, nb, dict(g)) for g in _cf(c).generators)


def test_asymmetric_circuit_no_generators():
    """레일 r -C1- a -C2- b: 자명군 -> 생성자 없음."""
    c = Circuit([cap("C1", "r", "a"), cap("C2", "a", "b")], rails=("r",))
    assert _cf(c).generators == ()


@pytest.mark.parametrize("name", sorted(HAND))
@pytest.mark.parametrize("seed", [1, 2, 3])
def test_relabeling_invariant_cert(name, seed):
    c = HAND[name]
    c2 = c.renamed(sigma_of(c, seed))
    random.Random(seed).shuffle(c2.elements)
    col, nb = labeled_graph(c)
    col2, nb2 = labeled_graph(c2)
    assert cert(col, nb, _cf(c).position) == cert(col2, nb2, _cf(c2).position)


@pytest.mark.parametrize("seed", range(25))
def test_relabeling_invariant_cert_random(seed):
    c = random_circuit(200 + seed)
    sig = sigma_of(c, seed)
    c2 = c.renamed(sig)
    random.Random(seed).shuffle(c2.elements)
    col, nb = labeled_graph(c)
    col2, nb2 = labeled_graph(c2)
    r, r2 = _cf(c), _cf(c2)
    assert cert(col, nb, r.position) == cert(col2, nb2, r2.position)
    f = vertex_map(sig)
    assert {f(v): w for v, w in r.wl.items()} == r2.wl                      # wl 은 이름 없는 값 -> 전단사로 그대로 옮겨짐


def test_same_ring_drawn_differently_same_cert():
    a = ring(6)
    order = [0, 2, 4, 1, 3, 5]
    b = edge_circuit(6, [(order[i], order[(i + 1) % 6]) for i in range(6)])
    ca, na = labeled_graph(a)
    cb, nbb = labeled_graph(b)
    assert cert(ca, na, _cf(a).position) == cert(cb, nbb, _cf(b).position)


def test_non_isomorphic_different_cert():
    a = ring(6)
    b = edge_circuit(6, [(0, 1), (1, 2), (2, 0), (3, 4), (4, 5), (5, 3)])
    ca, na = labeled_graph(a)
    cb, nbb = labeled_graph(b)
    assert cert(ca, na, _cf(a).position) != cert(cb, nbb, _cf(b).position)


def test_resistor_terminal_order_not_in_cert():
    """2단자 수동소자는 무향 t(4.7): 저항 끝을 뒤집어 그려도 정준 그래프가 같다."""
    a = edge_circuit(4, [(0, 1), (1, 2), (2, 3)], kind="res")
    b = edge_circuit(4, [(1, 0), (2, 1), (2, 3)], kind="res")
    ca, na = labeled_graph(a)
    cb, nbb = labeled_graph(b)
    assert cert(ca, na, _cf(a).position) == cert(cb, nbb, _cf(b).position)


@pytest.mark.parametrize("name", sorted(HAND))
def test_deterministic(name):
    c = HAND[name]
    r1, r2 = _cf(c), _cf(c)
    assert r1 == r2
    assert list(r1.position.items()) == list(r2.position.items())


def test_marks_enter_initial_colour_not_wl():
    """선언 표시는 처음 색에만: wl(표시 없는 1-WL)은 같고, 표시된 원소는 어떤 생성자도 움직이지 않는다(링에서 홀로 표시)."""
    c = ring(4)
    em = (("E00", (("value", 1e-12),)),)
    plain, marked = _cf(c), _cf(c, em, ())
    assert marked.wl == plain.wl
    col, nb = labeled_graph(c, em, ())
    assert all(is_automorphism(col, nb, dict(g)) for g in marked.generators)
    assert ("e", "E00") not in {v for g in marked.generators for v, _ in g}
