"""graph CONTRACT 4.7 [r11] `automorphism_orbits(canon) -> {정점: 궤도 id}` -- 성질 (a)~(h).

(옛 sizing `canonical_labeling` 궤도 test·`_helpers_colour` test 를 graph 로 옮김 -- U2 에서 이동·삭제, rule H.)
oracle:
- (a) 구성: 손 그래프(2단자 원소 = 무향 엣지)의 기지 군 -- 링 C_n(넷 1 궤도·원소 1 궤도), 경로 P5(넷 {0,4},{1,3},{2}), C6 ⊔ 2×C3(1-WL 한 색이지만
  넷 궤도 2), 정육면체 Q3·Petersen(넷 1 궤도). 차동쌍: 완전 차동 = 같은 궤도, 단일 종단(미러 부하) = 다른 궤도.
- (b) 전수 역추적 자기동형(`brute_orbits`) 대조, 독립 1-WL(`wl_classes`)로 전제 확인.
- (d) 사용자 결정 '대칭 묶음 방식: b': 저항 terminals 순서를 뒤집어도 궤도 분할 동일.
graph `.py` 소스는 열람하지 않았다.
"""
from __future__ import annotations

import random

import pytest

from gmid_engine.graph import automorphism_orbits, canonical_form

from canon_graphs import (HAND, Circuit, brute_orbits, c6_2c3, cap, cube, isrc, labeled_graph, mosd, nets_of, partition,
                           path, petersen, random_circuit, res, ring, sigma_of, vertex_map, wl_classes)


def orbits(c, em=(), nm=()):
    return automorphism_orbits(canonical_form(c, em, nm))


def net_part(orb):
    return {g for g in partition(orb) if all(v[0] == "n" for v in g)}


@pytest.mark.parametrize("n", [3, 4, 5, 6, 7, 8])
def test_ring_one_net_orbit_one_element_orbit(n):
    o = orbits(ring(n))
    assert net_part(o) == {nets_of(n, range(n))}
    assert len({o[("e", "E%02d" % i)] for i in range(n)}) == 1


def test_path5():
    assert net_part(orbits(path(5))) == {nets_of(5, (0, 4)), nets_of(5, (1, 3)), nets_of(5, (2,))}


def test_c6_2c3_two_net_orbits_though_wl_equal():
    c = c6_2c3()
    col, nb = labeled_graph(c)
    wl = wl_classes(col, nb)
    assert len({wl[("n", "N%02d" % i)] for i in range(12)}) == 1             # 전제: 1-WL 로 구별 안 됨
    assert net_part(orbits(c)) == {nets_of(12, range(6)), nets_of(12, range(6, 12))}


@pytest.mark.parametrize("make, n", [(cube, 8), (petersen, 10)])
def test_vertex_transitive(make, n):
    assert net_part(orbits(make())) == {nets_of(n, range(n))}


@pytest.mark.parametrize("name", sorted(HAND))
def test_hand_equals_brute_force(name):
    c = HAND[name]
    assert partition(orbits(c)) == brute_orbits(*labeled_graph(c))


@pytest.mark.parametrize("seed", range(40))
def test_random_equals_brute_force(seed):
    c = random_circuit(seed)
    assert partition(orbits(c)) == brute_orbits(*labeled_graph(c))


@pytest.mark.parametrize("name", sorted(HAND))
def test_orbit_id_is_min_position(name):
    canon = canonical_form(HAND[name])
    o = automorphism_orbits(canon)
    assert set(o) == set(canon.position)
    for g in partition(o):
        assert {o[v] for v in g} == {min(canon.position[v] for v in g)}


def test_no_generators_each_vertex_own_position():
    canon = canonical_form(Circuit([cap("C1", "r", "a"), cap("C2", "a", "b")], rails=("r",)))
    assert canon.generators == ()
    assert automorphism_orbits(canon) == canon.position


@pytest.mark.parametrize("seed", range(20))
def test_orbits_refine_wl(seed):
    c = random_circuit(400 + seed)
    o = orbits(c)
    col, nb = labeled_graph(c)
    wl = wl_classes(col, nb)
    assert all(len({wl[v] for v in g}) == 1 for g in partition(o))


@pytest.mark.parametrize("name", sorted(HAND))
@pytest.mark.parametrize("seed", [1, 2])
def test_relabeling_and_order_invariant(name, seed):
    c = HAND[name]
    sig = sigma_of(c, seed)
    c2 = c.renamed(sig)
    random.Random(seed).shuffle(c2.elements)
    f = vertex_map(sig)
    assert {f(v): k for v, k in orbits(c).items()} == orbits(c2)


@pytest.mark.parametrize("seed", range(20))
def test_relabeling_invariant_random(seed):
    c = random_circuit(600 + seed)
    sig = sigma_of(c, seed)
    f = vertex_map(sig)
    assert {f(v): k for v, k in orbits(c).items()} == orbits(c.renamed(sig))


def _diff(full=True):
    els = [mosd("M1", "nmos", "o1", "inp", "t"), mosd("M2", "nmos", "o2", "inn", "t"), mosd("M5", "nmos", "t", "vb", "gnd")]
    if full:
        els += [mosd("M3", "pmos", "o1", "pb", "vdd"), mosd("M4", "pmos", "o2", "pb", "vdd")]
    else:                                                                     # 미러 부하(단일 종단)
        els += [mosd("M3", "pmos", "o1", "o1", "vdd"), mosd("M4", "pmos", "o2", "o1", "vdd")]
    ports = {"inp": "input", "inn": "input", "o2": "output"}
    if full:
        ports["o1"] = "output"
    return Circuit(els, ("vdd", "gnd"), ports)


def test_full_differential_pair_same_orbit_single_ended_not():
    o = orbits(_diff(True))
    assert o[("e", "M1")] == o[("e", "M2")] and o[("e", "M3")] == o[("e", "M4")] and o[("n", "o1")] == o[("n", "o2")]
    s = orbits(_diff(False))
    assert s[("e", "M1")] != s[("e", "M2")] and s[("n", "o1")] != s[("n", "o2")]


def test_resistor_terminal_order_irrelevant():
    """4.7 (e) / 사용자 결정 (b): 부하 저항 R2 를 뒤집어 그려도 궤도 분할 동일, R1·R2 같은 궤도."""
    base = [mosd("M1", "nmos", "o1", "inp", "t"), mosd("M2", "nmos", "o2", "inn", "t"), mosd("M5", "nmos", "t", "vb", "gnd")]
    ports = {"inp": "input", "inn": "input", "o1": "output", "o2": "output"}
    a = Circuit(base + [res("R1", "vdd", "o1"), res("R2", "vdd", "o2")], ("vdd", "gnd"), ports)
    b = Circuit(base + [res("R1", "vdd", "o1"), res("R2", "o2", "vdd")], ("vdd", "gnd"), ports)
    oa, ob = orbits(a), orbits(b)
    assert partition(oa) == partition(ob)
    assert ob[("e", "R1")] == ob[("e", "R2")] and ob[("e", "M1")] == ob[("e", "M2")]


def test_current_source_direction_kept():
    """이상 전류원 t0·t1 은 방향: a→b 전류원은 a·b 를 구별, 같은 자리 커패시터는 구별 안 함."""
    base = [mosd("M1", "nmos", "a", "in", "gnd"), mosd("M2", "nmos", "b", "in", "gnd")]
    s = orbits(Circuit(base + [isrc("I1", "a", "b")], ("gnd",)))
    c = orbits(Circuit(base + [cap("C1", "a", "b")], ("gnd",)))
    assert s[("n", "a")] != s[("n", "b")]
    assert c[("n", "a")] == c[("n", "b")]


def test_marks_split_orbits():
    """4.7 (f): 선언 표시가 다른 두 원소·넷은 다른 궤도, 같은 표시면 같은 궤도."""
    c = _diff(True)
    c = Circuit(c.elements + [cap("CL1", "o1", "gnd"), cap("CL2", "o2", "gnd")], ("vdd", "gnd"), c.ports)
    same = orbits(c, (("CL1", (("value", 1e-12),)), ("CL2", (("value", 1e-12),))), ())
    diff = orbits(c, (("CL1", (("value", 1e-12),)), ("CL2", (("value", 2e-12),))), ())
    assert same[("e", "CL1")] == same[("e", "CL2")] and same[("e", "M1")] == same[("e", "M2")]
    assert diff[("e", "CL1")] != diff[("e", "CL2")] and diff[("e", "M1")] != diff[("e", "M2")]
    tgt = orbits(c, (), (("o1", (("target_v", 0.9),)), ("o2", (("target_v", 1.0),))))
    assert tgt[("n", "o1")] != tgt[("n", "o2")]


def test_deterministic():
    c = c6_2c3()
    assert orbits(c) == orbits(c)
