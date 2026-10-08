"""`canonical_labeling(colour, neighbours) -> (위치 {정점: 0..n-1}, 궤도 id {정점: int})` -- sizing CONTRACT 3.0b [r11].

입력 형식(struct_canon docstring): colour = {정점: 처음 색 int}, neighbours = {정점: ((라벨, 이웃), ...)}(무향 엣지는 양쪽에 같은 라벨).
sizing `.py` 소스는 열람하지 않았다.

oracle:
- (a) 구성으로 자기동형군이 정해진 손 그래프: 링 C_n(회전·반사 -> 궤도 1), 경로 P_5(반사 -> {0,4},{1,3},{2} 궤도 3),
  C6 ⊔ 2×C3(모든 정점 차수 2라 1-WL 색 하나지만 C6 정점과 C3 정점은 자기동형으로 대응하지 않는다 -> 궤도 2), 정육면체 Q3(정점 추이 -> 궤도 1),
  Petersen(정점 추이 -> 궤도 1).
- (b) 독립 구현: 이 파일의 역추적 자기동형 전수 탐색(`brute_orbits` -- 라벨 엣지 다중도 보존 전단사를 하나씩 세움)과 1-WL 정제(`wl_classes`,
  CONTRACT 3.0 문장 그대로). 무작위 작은 그래프(n ≤ 8)에서 궤도 분할이 전수 탐색과 같아야 한다.
- 정준성(3.0b '정준 그래프는 이름 치환·원소 순서에 불변'): 위치로 다시 쓴 그래프 cert(위치 순 처음 색 열 + (pos v, 라벨, pos u) 정렬 열)가
  무작위 이름 전단사·이웃 순서·dict 삽입 순서 섞기에 같다. 궤도 id 는 그 전단사로 옮겨진다(값 불변).
"""
from __future__ import annotations

import itertools
import random

import pytest

from gmid_engine.sizing import canonical_labeling


# ---------------------------------------------------------------- 그래프 구성 (입력)

def graph(n_or_vertices, edges, colour=None):
    """edges = (u, v) 또는 (u, v, 라벨). -> (colour0, neighbours). 무향: 양쪽에 같은 라벨."""
    vs = list(range(n_or_vertices)) if isinstance(n_or_vertices, int) else list(n_or_vertices)
    nb = {v: [] for v in vs}
    for e in edges:
        u, v = e[0], e[1]
        lab = e[2] if len(e) > 2 else "e"
        nb[u].append((lab, v))
        nb[v].append((lab, u))
    col = {v: (0 if colour is None else colour[v]) for v in vs}
    return col, {v: tuple(x) for v, x in nb.items()}


def ring(n):
    return graph(n, [(i, (i + 1) % n) for i in range(n)])


def path(n):
    return graph(n, [(i, i + 1) for i in range(n - 1)])


def c6_2c3():
    """C6(0..5) ⊔ C3(6,7,8) ⊔ C3(9,10,11). 모든 정점 차수 2 -> 1-WL 로 한 색."""
    e = [(i, (i + 1) % 6) for i in range(6)]
    e += [(6, 7), (7, 8), (8, 6), (9, 10), (10, 11), (11, 9)]
    return graph(12, e)


def cube():
    """Q3: 정점 = 3비트, 한 비트 다른 정점끼리 엣지."""
    return graph(8, [(u, u ^ (1 << b)) for u in range(8) for b in range(3) if u < u ^ (1 << b)])


def petersen():
    outer = [(i, (i + 1) % 5) for i in range(5)]
    spokes = [(i, i + 5) for i in range(5)]
    inner = [(5 + i, 5 + (i + 2) % 5) for i in range(5)]
    return graph(10, outer + spokes + inner)


# ---------------------------------------------------------------- 독립 oracle (b)

def wl_classes(colour, nb):
    """CONTRACT 3.0 1-WL: 서명 = (옛 색, ((라벨, 이웃 옛 색), ...) 정렬), 순위; 색 수가 늘지 않으면 직전 색."""
    def rank(sig):
        order = {s: i for i, s in enumerate(sorted(set(sig.values())))}
        return {v: order[s] for v, s in sig.items()}
    col = rank(dict(colour))
    while True:
        new = rank({v: (col[v], tuple(sorted((lab, col[u]) for lab, u in nb[v]))) for v in col})
        if len(set(new.values())) <= len(set(col.values())):
            return col
        col = new


def _edge_count(nb):
    cnt = {}
    for v, lst in nb.items():
        for lab, u in lst:
            cnt[(v, lab, u)] = cnt.get((v, lab, u), 0) + 1
    return cnt


def _extends(colour, nb, cnt, start):
    """start 사상(dict)을 라벨 엣지 다중도·처음 색 보존 전단사로 확장할 수 있나(역추적 전수)."""
    vs = sorted(colour, key=repr)
    labels = {lab for v in vs for lab, _ in nb[v]}
    deg = {v: tuple(sorted(lab for lab, _ in nb[v])) for v in vs}
    mapping = {}
    used = set()

    def ok(a, fa):
        if colour[a] != colour[fa] or deg[a] != deg[fa]:
            return False
        for lab in labels:
            if cnt.get((a, lab, a), 0) != cnt.get((fa, lab, fa), 0):
                return False
            for b, fb in mapping.items():
                if cnt.get((a, lab, b), 0) != cnt.get((fa, lab, fb), 0):
                    return False
        return True

    for a, fa in start.items():
        if fa in used or not ok(a, fa):
            return False
        mapping[a] = fa
        used.add(fa)
    todo = [v for v in vs if v not in mapping]

    def rec(i):
        if i == len(todo):
            return True
        a = todo[i]
        for fa in vs:
            if fa in used or not ok(a, fa):
                continue
            mapping[a] = fa
            used.add(fa)
            if rec(i + 1):
                return True
            del mapping[a]
            used.discard(fa)
        return False
    return rec(0)


def brute_orbits(colour, nb):
    """자기동형 궤도 분할(frozenset 들의 집합) -- v 와 w 가 같은 궤도 ⇔ v -> w 로 시작하는 자기동형이 있다."""
    cnt = _edge_count(nb)
    vs = sorted(colour, key=repr)
    parent = {v: v for v in vs}

    def find(x):
        while parent[x] != x:
            x = parent[x]
        return x
    for i, v in enumerate(vs):
        for w in vs[i + 1:]:
            if find(v) == find(w):
                continue
            if _extends(colour, nb, cnt, {v: w}):
                parent[find(w)] = find(v)
    groups = {}
    for v in vs:
        groups.setdefault(find(v), set()).add(v)
    return {frozenset(g) for g in groups.values()}


def orbit_partition(orb):
    groups = {}
    for v, o in orb.items():
        groups.setdefault(o, set()).add(v)
    return {frozenset(g) for g in groups.values()}


def cert(colour, nb, pos):
    """정준 그래프: 위치 순 처음 색 열 + (pos v, 라벨, pos u) 정렬 열(이름 없음)."""
    inv = {p: v for v, p in pos.items()}
    return (tuple(colour[inv[i]] for i in range(len(inv))),
            tuple(sorted((pos[v], lab, pos[u]) for v in nb for lab, u in nb[v])))


def relabel(colour, nb, seed, prefix="x"):
    """무작위 이름 전단사 σ + dict 삽입 순서·이웃 순서 섞기. -> (colour', nb', σ)."""
    rng = random.Random(seed)
    vs = list(colour)
    names = ["%s%d_%d" % (prefix, i, seed) for i in range(len(vs))]
    rng.shuffle(names)
    sig = dict(zip(vs, names))
    order = list(vs)
    rng.shuffle(order)
    col2 = {sig[v]: colour[v] for v in order}
    nb2 = {}
    for v in order:
        lst = [(lab, sig[u]) for lab, u in nb[v]]
        rng.shuffle(lst)
        nb2[sig[v]] = tuple(lst)
    return col2, nb2, sig


def random_graph(seed, n=None, labels=("e",), colours=1, p=0.4):
    rng = random.Random(seed)
    n = n or rng.randint(3, 8)
    edges = [(u, v, rng.choice(labels)) for u, v in itertools.combinations(range(n), 2) if rng.random() < p]
    col = {v: rng.randrange(colours) for v in range(n)}
    return graph(n, edges, col)


HAND = {
    "ring3": ring(3), "ring5": ring(5), "ring6": ring(6), "ring8": ring(8),
    "path5": path(5), "c6_2c3": c6_2c3(), "cube": cube(), "petersen": petersen(),
}


# ---------------------------------------------------------------- 기지 궤도 (oracle a)

@pytest.mark.parametrize("n", [3, 4, 5, 6, 7, 8])
def test_ring_one_orbit(n):
    """(a) C_n 은 회전으로 정점 추이 -> 궤도 1, 궤도 id = 구성원 위치 최솟값 = 0."""
    col, nb = ring(n)
    pos, orb = canonical_labeling(col, nb)
    assert orbit_partition(orb) == {frozenset(range(n))}
    assert set(orb.values()) == {0}


def test_path5_three_orbits():
    """(a) P_5 의 자기동형 = 항등·반사 -> {0,4}, {1,3}, {2}."""
    col, nb = path(5)
    _, orb = canonical_labeling(col, nb)
    assert orbit_partition(orb) == {frozenset({0, 4}), frozenset({1, 3}), frozenset({2})}


def test_c6_2c3_two_orbits_though_wl_equal():
    """(a) C6 ⊔ 2×C3: 1-WL 은 12 정점을 한 색으로 남기지만(전제 확인), C6 정점과 C3 정점은 자기동형으로 대응하지 않는다 -> 궤도 2."""
    col, nb = c6_2c3()
    assert len(set(wl_classes(col, nb).values())) == 1                    # 전제: 1-WL 로 구별 안 됨
    _, orb = canonical_labeling(col, nb)
    assert orbit_partition(orb) == {frozenset(range(6)), frozenset(range(6, 12))}


def test_cube_one_orbit():
    """(a) Q3 는 정점 추이(비트 xor 평행이동) -> 궤도 1."""
    col, nb = cube()
    _, orb = canonical_labeling(col, nb)
    assert orbit_partition(orb) == {frozenset(range(8))}


def test_petersen_one_orbit():
    col, nb = petersen()
    _, orb = canonical_labeling(col, nb)
    assert orbit_partition(orb) == {frozenset(range(10))}


def test_initial_colour_splits_ring():
    """(a) C6 에서 정점 0 만 다른 처음 색: 자기동형 = 0 을 고정하는 반사 -> {0}, {1,5}, {2,4}, {3}."""
    col, nb = graph(6, [(i, (i + 1) % 6) for i in range(6)], {0: 1, 1: 0, 2: 0, 3: 0, 4: 0, 5: 0})
    _, orb = canonical_labeling(col, nb)
    assert orbit_partition(orb) == {frozenset({0}), frozenset({1, 5}), frozenset({2, 4}), frozenset({3})}


def test_edge_label_splits_path():
    """(a) 경로 0 -a- 1 -b- 2: 라벨이 달라 반사가 자기동형이 아니다 -> 궤도 3(모두 단일)."""
    col, nb = graph(3, [(0, 1, "a"), (1, 2, "b")])
    _, orb = canonical_labeling(col, nb)
    assert orbit_partition(orb) == {frozenset({0}), frozenset({1}), frozenset({2})}


# ---------------------------------------------------------------- 전수 탐색 대조 (oracle b)

@pytest.mark.parametrize("seed", range(40))
def test_orbits_equal_brute_force_random(seed):
    col, nb = random_graph(seed, labels=("a", "b") if seed % 2 else ("e",), colours=1 + seed % 3)
    _, orb = canonical_labeling(col, nb)
    assert orbit_partition(orb) == brute_orbits(col, nb)


@pytest.mark.parametrize("name", ["ring6", "path5", "c6_2c3", "cube", "petersen"])
def test_hand_orbits_equal_brute_force(name):
    col, nb = HAND[name]
    _, orb = canonical_labeling(col, nb)
    assert orbit_partition(orb) == brute_orbits(col, nb)


# ---------------------------------------------------------------- 형식·성질

@pytest.mark.parametrize("name", sorted(HAND))
def test_positions_are_bijection_and_orbit_id_is_min_position(name):
    col, nb = HAND[name]
    pos, orb = canonical_labeling(col, nb)
    assert set(pos) == set(col) and set(orb) == set(col)
    assert sorted(pos.values()) == list(range(len(col)))
    for g in orbit_partition(orb):
        assert {orb[v] for v in g} == {min(pos[v] for v in g)}            # 궤도 id = 구성원 정준 위치 최솟값(3.0b)


@pytest.mark.parametrize("name", sorted(HAND))
def test_orbits_refine_wl_classes(name):
    """궤도 ⊆ 1-WL 색 클래스(3.0b 성질 (3)) -- 독립 1-WL(b)."""
    col, nb = HAND[name]
    _, orb = canonical_labeling(col, nb)
    wl = wl_classes(col, nb)
    for g in orbit_partition(orb):
        assert len({wl[v] for v in g}) == 1


@pytest.mark.parametrize("seed", range(20))
def test_orbits_refine_wl_classes_random(seed):
    col, nb = random_graph(100 + seed, n=8, labels=("a", "b"), colours=2)
    _, orb = canonical_labeling(col, nb)
    wl = wl_classes(col, nb)
    for g in orbit_partition(orb):
        assert len({wl[v] for v in g}) == 1


def test_different_initial_colour_never_same_orbit():
    for seed in range(15):
        col, nb = random_graph(200 + seed, n=7, colours=3)
        _, orb = canonical_labeling(col, nb)
        for g in orbit_partition(orb):
            assert len({col[v] for v in g}) == 1


@pytest.mark.parametrize("name", sorted(HAND))
@pytest.mark.parametrize("seed", [1, 2, 3])
def test_relabeling_invariance(name, seed):
    """이름 전단사·순서 섞기: 정준 그래프(cert) 같고, 궤도 id 가 전단사로 옮겨진다(3.0b 성질 (1))."""
    col, nb = HAND[name]
    pos, orb = canonical_labeling(col, nb)
    col2, nb2, sig = relabel(col, nb, seed)
    pos2, orb2 = canonical_labeling(col2, nb2)
    assert cert(col, nb, pos) == cert(col2, nb2, pos2)
    assert {sig[v]: o for v, o in orb.items()} == orb2


@pytest.mark.parametrize("seed", range(25))
def test_relabeling_invariance_random(seed):
    col, nb = random_graph(300 + seed, labels=("d", "g", "s"), colours=2)
    pos, orb = canonical_labeling(col, nb)
    col2, nb2, sig = relabel(col, nb, seed + 7)
    pos2, orb2 = canonical_labeling(col2, nb2)
    assert cert(col, nb, pos) == cert(col2, nb2, pos2)
    assert {sig[v]: o for v, o in orb.items()} == orb2


def test_isomorphic_relabelled_ring_same_cert_as_other_ring_drawing():
    """같은 C6 를 다른 엣지 나열로 그려도(0-2-4-1-3-5-0) 정준 그래프가 같다(정준 라벨링 = 동형류의 대표)."""
    a = ring(6)
    order = [0, 2, 4, 1, 3, 5]
    b = graph(6, [(order[i], order[(i + 1) % 6]) for i in range(6)])
    pa, _ = canonical_labeling(*a)
    pb, _ = canonical_labeling(*b)
    assert cert(*a, pa) == cert(*b, pb)


def test_non_isomorphic_graphs_have_different_cert():
    """C6 와 2×C3 는 동형이 아니다 -> 정준 그래프가 다르다."""
    a = ring(6)
    b = graph(6, [(0, 1), (1, 2), (2, 0), (3, 4), (4, 5), (5, 3)])
    pa, _ = canonical_labeling(*a)
    pb, _ = canonical_labeling(*b)
    assert cert(*a, pa) != cert(*b, pb)


@pytest.mark.parametrize("name", sorted(HAND))
def test_deterministic(name):
    """같은 입력 -> 같은 출력(3.0b 성질 (6)(8), 비트·dict 동일)."""
    col, nb = HAND[name]
    r1 = canonical_labeling(col, nb)
    r2 = canonical_labeling(dict(col), {k: tuple(v) for k, v in nb.items()})
    assert r1 == r2
    assert list(r1[0].items()) == list(r2[0].items()) and list(r1[1].items()) == list(r2[1].items())


def test_input_not_mutated():
    col, nb = cube()
    c0, n0 = dict(col), {k: tuple(v) for k, v in nb.items()}
    canonical_labeling(col, nb)
    assert col == c0 and nb == n0
