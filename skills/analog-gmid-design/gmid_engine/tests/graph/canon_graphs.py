"""정준형·자기동형 test 공용(graph CONTRACT 4.7 [r11]) -- 입력 구성과 독립 oracle. graph `.py` 소스는 열람하지 않았다.

- `Circuit`: `canonical_form` 의 `source`(= `.column(kind, field)` 를 가진 것) 를 손으로 만든 회로 목록에서 만든다. 열 형식은 S1Graph 실측
  형식(`pins` = ((단자, 넷), ...), `bulk` = `.net` 을 가진 값, MOS 만 `is_diode`·`bulk`)을 따른다. 키 정렬 tuple.
- `labeled_graph`: 4.7 문장 그대로의 그래프 -- 정점 ("n", 넷)·("e", 원소), 엣지 라벨 MOS c·g·b(drain·source 는 같은 라벨 c), 이상 전류원 t0·t1(방향),
  그 밖 2단자 t(무향), 처음 색 = (종류, element_class, kind, is_diode, 표시) / (종류, is_rail, port_direction, 표시).
  [U17 ①-d] 설계 40 v1.6 §6-8 D-2: "그 그래프에서 MOS의 `d`·`s` 엣지는 같은 라벨 `c`(채널)다. `g`·`b` 라벨, 원소 처음 색(kind, is_diode,
  선언 표시), 노드 색(레일, 포트 role, 선언 표시)은 그대로다" -- 정준 위치·1-WL 색·자기동형 생성자를 모두 이 그래프 하나에서 정한다.
- `flip_ds`: MOS 하나의 drain·source 표기를 맞바꾼 사본(§6-8 비트 동일 metamorphic 입력).
- oracle (b): `brute_orbits`(역추적 전수 자기동형: 처음 색·라벨 엣지 다중도 보존 전단사), `wl_classes`(1-WL, sizing 3.0 문장).
"""
from __future__ import annotations

import random
from types import SimpleNamespace


class Circuit:
    """elements = [(이름, element_class, kind, {단자: 넷}, is_diode, bulk 넷 | None)], rails, ports {넷: 방향}."""

    def __init__(self, elements, rails=(), ports=None, extra_nets=()):
        self.elements = list(elements)
        self.rails = set(rails)
        self.ports = dict(ports or {})
        nets = set(extra_nets) | self.rails | set(self.ports)
        for e in self.elements:
            nets |= set(e[3].values())
            if e[5] is not None:
                nets.add(e[5])
        self.nets = sorted(nets)

    def column(self, kind, field):
        if kind == "node":
            if field == "is_rail":
                return tuple((n, n in self.rails) for n in self.nets)
            if field == "port_direction":
                return tuple((n, self.ports.get(n)) for n in self.nets)
            raise KeyError((kind, field))
        out = []
        for name, cls, k, pins, diode, bulk in sorted(self.elements, key=lambda e: e[0]):
            if field == "element_class":
                out.append((name, cls))
            elif field == "kind":
                out.append((name, k))
            elif field == "pins":
                order = ("d", "g", "s") if cls == "mos" else ("t0", "t1")
                out.append((name, tuple((t, pins[t]) for t in order)))
            elif field == "is_diode":
                if cls == "mos":
                    out.append((name, bool(diode)))
            elif field == "bulk":
                if cls == "mos":
                    out.append((name, SimpleNamespace(net=bulk, origin="test", reason=None)))
            else:
                raise KeyError((kind, field))
        return tuple(out)

    def flip_ds(self, name):
        """MOS `name` 의 drain·source 표기를 맞바꾼 사본(연결은 같다). is_diode 는 S1 정의(gate == drain)대로 다시 정한다 --
        gate 가 drain·source 어느 쪽도 아닌 MOS 만 물리적으로 같은 회로다(호출부가 고른다)."""
        els = []
        for n, c, k, p, d, b in self.elements:
            if n == name:
                p = dict(p, d=p["s"], s=p["d"])
                d = p["d"] == p["g"]
            els.append((n, c, k, dict(p), d, b))
        return Circuit(els, set(self.rails), dict(self.ports), list(self.nets))

    def renamed(self, sig):
        f = lambda n: sig.get(n, n)                                        # noqa: E731
        els = [(f(n), c, k, {t: f(x) for t, x in p.items()}, d, None if b is None else f(b)) for n, c, k, p, d, b in self.elements]
        return Circuit(els, {f(r) for r in self.rails}, {f(k): v for k, v in self.ports.items()}, [f(n) for n in self.nets])


def cap(name, a, b):
    return (name, "passive", "capacitor", {"t0": a, "t1": b}, False, None)


def res(name, a, b):
    return (name, "passive", "resistor", {"t0": a, "t1": b}, False, None)


def isrc(name, a, b):
    return (name, "ideal_source", "current_source", {"t0": a, "t1": b}, False, None)


def mosd(name, kind, d, g, s, bulk=None):
    return (name, "mos", kind, {"d": d, "g": g, "s": s}, d == g, bulk)


def marks_dict(marks):
    return {name: tuple(m) for name, m in marks}


def labeled_graph(c, element_marks=(), node_marks=()):
    em, nm = marks_dict(element_marks), marks_dict(node_marks)
    col, nb = {}, {}
    for n in c.nets:
        v = ("n", n)
        col[v] = ("n", n in c.rails, c.ports.get(n) or "", nm.get(n, ()))
        nb[v] = []
    for name, cls, k, pins, diode, bulk in c.elements:
        v = ("e", name)
        col[v] = ("e", cls, k, bool(diode) if cls == "mos" else False, em.get(name, ()))
        nb[v] = []
        if cls == "mos":
            links = [("c", pins["d"]), ("g", pins["g"]), ("c", pins["s"])] + ([("b", bulk)] if bulk is not None else [])
        elif cls == "ideal_source" and k == "current_source":
            links = [("t0", pins["t0"]), ("t1", pins["t1"])]
        else:
            links = [("t", pins["t0"]), ("t", pins["t1"])]
        for lab, net in links:
            nb[v].append((lab, ("n", net)))
            nb[("n", net)].append((lab, v))
    return col, {v: tuple(x) for v, x in nb.items()}


def wl_classes(colour, nb):
    def rank(sig):
        order = {s: i for i, s in enumerate(sorted(set(sig.values()), key=repr))}
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


def is_automorphism(colour, nb, mapping):
    """전체 사상(dict, 빠진 정점은 고정)이 처음 색·라벨 엣지 다중도를 보존하는 전단사인가."""
    f = {v: mapping.get(v, v) for v in colour}
    if sorted(f.values(), key=repr) != sorted(colour, key=repr):
        return False
    if any(colour[v] != colour[f[v]] for v in colour):
        return False
    cnt = _edge_count(nb)
    return all(cnt.get((f[a], lab, f[b]), 0) == k for (a, lab, b), k in cnt.items())


def _extends(colour, nb, cnt, start):
    vs = sorted(colour, key=repr)
    labels = {lab for v in vs for lab, _ in nb[v]}
    deg = {v: tuple(sorted(lab for lab, _ in nb[v])) for v in vs}
    mapping, used = {}, set()

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
    # BFS 순서(이미 사상된 정점에서 가까운 순): 이웃이 사상돼 있으면 후보 = 그 상의 이웃만(가지치기, 결과는 같은 전수 탐색)
    todo, seen = [], set(mapping)
    frontier = list(mapping)
    while len(seen) < len(vs):
        if not frontier:
            nxt = next(v for v in vs if v not in seen)
            seen.add(nxt)
            todo.append(nxt)
            frontier = [nxt]
        new_frontier = []
        for v in frontier:
            for _, u in sorted(nb[v], key=repr):
                if u not in seen:
                    seen.add(u)
                    todo.append(u)
                    new_frontier.append(u)
        frontier = new_frontier

    def cands(a):
        for _, b in nb[a]:
            if b in mapping:
                return sorted({u for _, u in nb[mapping[b]]}, key=repr)
        return vs

    def rec(i):
        if i == len(todo):
            return True
        a = todo[i]
        for fa in cands(a):
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
    cnt = _edge_count(nb)
    vs = sorted(colour, key=repr)
    parent = {v: v for v in vs}

    def find(x):
        while parent[x] != x:
            x = parent[x]
        return x
    for i, v in enumerate(vs):
        for w in vs[i + 1:]:
            if find(v) != find(w) and _extends(colour, nb, cnt, {v: w}):
                parent[find(w)] = find(v)
    groups = {}
    for v in vs:
        groups.setdefault(find(v), set()).add(v)
    return {frozenset(g) for g in groups.values()}


def partition(orb):
    groups = {}
    for v, o in orb.items():
        groups.setdefault(o, set()).add(v)
    return {frozenset(g) for g in groups.values()}


def cert(colour, nb, position):
    inv = {p: v for v, p in position.items()}
    return (tuple(colour[inv[i]] for i in range(len(inv))),
            tuple(sorted((position[v], lab, position[u]) for v in nb for lab, u in nb[v])))


def sigma_of(c, seed, prefix="z"):
    rng = random.Random(seed)
    names = c.nets + [e[0] for e in c.elements]
    new = ["%s%03d_%d" % (prefix, i, seed) for i in range(len(names))]
    rng.shuffle(new)
    return dict(zip(names, new))


def vertex_map(sig):
    return lambda v: (v[0], sig.get(v[1], v[1]))


# ---------------------------------------------------------------- 손 그래프(수동소자 = 무향 엣지 -> 넷 그래프의 엣지)

def edge_circuit(n, edges, kind="cap"):
    """넷 0..n-1 과 엣지마다 2단자 원소 하나. 2단자는 무향이라 넷 그래프 G 의 자기동형 = 회로 자기동형(넷 궤도 = G 궤도, 원소 궤도 = 엣지 궤도)."""
    mk = cap if kind == "cap" else res
    return Circuit([mk("E%02d" % i, "N%02d" % a, "N%02d" % b) for i, (a, b) in enumerate(edges)],
                   extra_nets=["N%02d" % i for i in range(n)])


def ring(n):
    return edge_circuit(n, [(i, (i + 1) % n) for i in range(n)])


def path(n):
    return edge_circuit(n, [(i, i + 1) for i in range(n - 1)])


def c6_2c3():
    e = [(i, (i + 1) % 6) for i in range(6)] + [(6, 7), (7, 8), (8, 6), (9, 10), (10, 11), (11, 9)]
    return edge_circuit(12, e)


def cube():
    return edge_circuit(8, [(u, u ^ (1 << b)) for u in range(8) for b in range(3) if u < u ^ (1 << b)])


def petersen():
    return edge_circuit(10, [(i, (i + 1) % 5) for i in range(5)] + [(i, i + 5) for i in range(5)]
                        + [(5 + i, 5 + (i + 2) % 5) for i in range(5)])


def nets_of(n, idx):
    return frozenset(("n", "N%02d" % i) for i in idx)


def random_circuit(seed, n_nets=None, n_el=None):
    """무작위 회로(커패시터·저항·이상 전류원·MOS, 레일 하나·포트 하나 가능)."""
    rng = random.Random(seed)
    n = n_nets or rng.randint(3, 5)
    nets = ["q%d" % i for i in range(n)]
    els = []
    for i in range(n_el or rng.randint(3, 6)):
        t = rng.choice(("cap", "res", "src", "nmos", "pmos"))
        if t in ("nmos", "pmos"):
            d, g, s = (rng.choice(nets) for _ in range(3))
            els.append(mosd("X%d" % i, t, d, g, s, rng.choice([None, nets[0]])))
        else:
            a, b = rng.sample(nets, 2)
            els.append({"cap": cap, "res": res, "src": isrc}[t]("X%d" % i, a, b))
    rails = (nets[0],) if rng.random() < 0.5 else ()
    ports = {nets[-1]: "output"} if rng.random() < 0.5 else {}
    return Circuit(els, rails, ports, nets)


HAND = {"ring3": ring(3), "ring5": ring(5), "ring6": ring(6), "ring8": ring(8), "path5": path(5), "c6_2c3": c6_2c3(),
        "cube": cube(), "petersen": petersen()}
