"""graph CONTRACT 4.7 [r11] `automorphism_orbits(canon) -> {정점: 궤도 id}` -- 성질 (a)~(h).

(옛 sizing `canonical_labeling` 궤도 test·`_helpers_colour` test 를 graph 로 옮김 -- U2 에서 이동·삭제, rule H.)
oracle:
- (a) 구성: 손 그래프(2단자 원소 = 무향 엣지)의 기지 군 -- 링 C_n(넷 1 궤도·원소 1 궤도), 경로 P5(넷 {0,4},{1,3},{2}), C6 ⊔ 2×C3(1-WL 한 색이지만
  넷 궤도 2), 정육면체 Q3·Petersen(넷 1 궤도). 차동쌍: 완전 차동 = 같은 궤도, 단일 종단(미러 부하) = 다른 궤도.
- (b) 전수 역추적 자기동형(`brute_orbits`) 대조, 독립 1-WL(`wl_classes`)로 전제 확인.
- (d) 사용자 결정 '대칭 묶음 방식: b': 저항 terminals 순서를 뒤집어도 궤도 분할 동일.
- [U17 ①-d] 설계 40 v1.6 §6-8(사용자 결정 2026-10-12 "6. 가", D-2·D-3): "자기동형은 한 MOS의 drain을 상 MOS의 source로 보낼 수 있다(자기
  자신으로 가며 d/s를 맞바꾸는 것 포함)", d·s = 같은 라벨 c(oracle `labeled_graph` 를 그대로 고침 -> 위 brute-force 대조가 이 규칙으로 바뀐다),
  "궤도 ⊆ `wl` 클래스"가 맞바꿈 궤도에서도 성립, d/s 표기를 뒤집은 입력의 궤도가 비트 동일.
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


# ---------------------------------------------------------------- [U17 ①-d] 설계 40 v1.6 §6-8 MOS d/s 맞바꿈

def _drain_to_source_pair():
    """Ma(d=a, s=gnd)·Mb(d=gnd, s=b) -- 같은 gate vb, 출력 a·b 에 같은 커패시터. a<->b, Ma<->Mb 는 Ma 의 drain(a)을 Mb 의 source(b)로
    보내야만 자기동형이다(옛 d·s 라벨 그래프에서는 아니다)."""
    els = [mosd("Ma", "nmos", "a", "vb", "gnd"), mosd("Mb", "nmos", "gnd", "vb", "b"), cap("CA", "a", "vdd"), cap("CB", "b", "vdd")]
    return Circuit(els, ("vdd", "gnd"), {"a": "output", "b": "output"})


def test_drain_may_map_to_source_of_image():
    o = orbits(_drain_to_source_pair())
    assert o[("e", "Ma")] == o[("e", "Mb")] and o[("n", "a")] == o[("n", "b")] and o[("e", "CA")] == o[("e", "CB")]
    assert partition(o) == brute_orbits(*labeled_graph(_drain_to_source_pair()))


def _pass_device():
    """U11 `pass_device` 변형(tests/metrics conftest cm_variant): 완전 차동 M1~M4 + 평균 저항 R1(op, c)·R2(c, om) + 두 출력 사이 통과 MOS
    Mx(d=op, g=vbx, s=om). op<->om 반사는 Mx 를 자기 자신으로 보내며 d/s 를 맞바꾼다(§6-8 '자기 자신으로 가며 d/s를 맞바꾸는 것')."""
    els = [mosd("M1", "nmos", "op", "ip", "gnd"), mosd("M2", "nmos", "om", "im", "gnd"),
           mosd("M3", "pmos", "op", "c", "vdd"), mosd("M4", "pmos", "om", "c", "vdd"),
           res("R1", "op", "c"), res("R2", "c", "om"), mosd("Mx", "nmos", "op", "vbx", "om")]
    return Circuit(els, ("vdd", "gnd"), {"ip": "input", "im": "input", "op": "output", "om": "output"})


def test_self_ds_swap_is_automorphism():
    c = _pass_device()
    canon = canonical_form(c)
    o = automorphism_orbits(canon)
    assert o[("n", "op")] == o[("n", "om")] and o[("e", "M1")] == o[("e", "M2")] and o[("e", "R1")] == o[("e", "R2")]
    assert partition(o) == brute_orbits(*labeled_graph(c))
    # 군은 반사 하나(Z2) -- 그 생성자는 op<->om 을 움직이고 Mx 는 고정한다(= Mx 자기 d/s 맞바꿈)
    moved = [dict(g) for g in canon.generators]
    assert any(("n", "op") in g and ("e", "Mx") not in g for g in moved)


@pytest.mark.parametrize("seed", range(30))
def test_ds_flip_orbits_bit_identical_random(seed):
    """§6-8 D-3: d/s 표기를 뒤집은 입력(gate 가 d·s 가 아닌 MOS 하나씩)의 궤도 dict 가 비트 동일."""
    c = random_circuit(900 + seed)
    base = orbits(c)
    for e in c.elements:
        if e[1] == "mos" and e[3]["g"] not in (e[3]["d"], e[3]["s"]):
            assert orbits(c.flip_ds(e[0])) == base, e[0]


def test_ds_swap_orbits_refine_wl():
    """§6-8 '궤도 ⊆ `wl` 클래스'가 맞바꿈 궤도에서도 성립(독립 1-WL, c 라벨)."""
    for c in (_drain_to_source_pair(), _pass_device()):
        col, nb = labeled_graph(c)
        wl = wl_classes(col, nb)
        assert all(len({wl[v] for v in g}) == 1 for g in partition(orbits(c)))
