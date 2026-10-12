"""정준형 -- 회로 그래프의 완전 정준 라벨링과 자기동형 생성자 (설계 40 §6, 사용자 결정 2026-10-08 '정준 라벨링 + 대칭 변수 묶음').

진입점: `canonical_form(source, element_marks=(), node_marks=()) -> Canonical`. `source` = `.column(kind, field)` 를 가진 것(S1Graph, sizing 계산 블록의
Projection 모두 된다). θ 무관.

* 그래프: 정점 = 넷 `("n", 넷)` ∪ 원소 `("e", 원소)`, 엣지 = 원소-넷 연결에 단자 라벨: MOS 의 drain·source 는 **같은 채널 라벨 `c`**(MOS 는 d/s 에 대해
  물리적으로 대칭이다 -- 사용자 결정 2026-10-12 "6. 가"·D-3, 40 §6-8), gate `g`, bulk `b`(bulk 넷이 정해졌으면), 이상원 단자 라벨 `t0`·`t1`(전류 방향이 있다),
  저항·커패시터 등 그 밖 2단자는 **방향 없는** `t`(단자 순서는 색에 넣지 않는다 -- 사용자 결정 '대칭 묶음 방식: b'). 그래서 자기동형은 한 MOS 의 drain 을
  상 MOS 의 source 로 보낼 수 있다(gate·bulk 넷과 모든 선언이 보존될 때만).
* 처음 색: 원소 = (원소 종류, element_class, kind, is_diode, 선언 표시), 노드 = (넷 종류, is_rail, port_direction, 선언 표시). 선언 표시
  `element_marks`·`node_marks` = ((이름, ((표시 이름, 수), ...)), ...)(표시 이름순 정렬): 자기동형이 선언 값(레일 전위·노드 목표·입력 DC·값 선언·engine·
  선형 영역)을 보존하게 한다. 이름을 읽지 않는다.
* **그래프 하나**(D-2, 40 §6-8): `wl`·`position`·`generators` 를 모두 선언 표시를 넣은 같은 그래프 하나에서 정한다(두 번 탐색하지 않는다).
  `wl` = 그 그래프의 1-WL 색 정제(새 색 = (옛 색, (라벨, 이웃 옛 색) 정렬 다중집합)의 정렬 순위, 색 종류 수가 더 늘지 않으면 멈춤) -- 서로 다른 색 사이의
  순서(`dc_colour` 순서)의 근거. 같은 그래프라 궤도 ⊆ `wl` 클래스(CONTRACT 4.7 (h))가 맞바꿈 궤도에서도 성립한다.
* 정준 라벨링(individualization-refinement, nauty 식): 선언 표시를 넣은 그래프의 평형 분할에서 색 순위가 가장 앞선 비단일 칸을 대상 칸으로, 칸의 정점을
  하나씩 개별화한 뒤 다시 정제한다. 이산 분할(잎)의 위치 함수로 그래프를 다시 쓴 증명서 cert 가 최소인 잎의 위치가 `position`(0..n−1). 같은 cert 의 두 잎
  사이 위치 대응이 자기동형이다 -- 마디마다 지역 union-find 로 (a) 같은 궤도 자식 건너뛰기 (b) 최저 공통 선조 마디 아래 가지치기. 찾은 자기동형(움직인
  정점만)이 `generators` 다(군을 생성한다). 탐색 순서(칸 안 정점 순서)는 이름을 보지만 `position` 의 증명서·생성자가 만드는 군은 이름과 무관하다.
* 성질: 이름 전단사·원소 순서 섞기에 대해 정준 그래프(위치로 다시 쓴 그래프)가 같다. 남는 동률 = 정확히 자기동형 궤도.
"""
import dataclasses

from .s1_values import ELEMENT_MOS, ELEMENT_SOURCE, MOS_DRAIN, MOS_GATE, MOS_SOURCE

_BULK = "b"
_CHANNEL = "c"
_UNDIRECTED = "t"
NODE, ELEMENT = ("n", "e")


@dataclasses.dataclass(frozen=True)
class Canonical:
    """`wl`·`position` = {정점: int}, `generators` = 자기동형 생성자 tuple, 각 생성자 = ((정점, 상), ...) 움직인 정점만 정점 키 순."""

    wl: dict
    position: dict
    generators: tuple


def _edges(classes, pins, bulk):
    edges = []
    for name, cls in classes.items():
        p = dict(pins[name])
        if cls == ELEMENT_MOS:
            edges.extend(((name, _CHANNEL, p[MOS_DRAIN]), (name, MOS_GATE, p[MOS_GATE]), (name, _CHANNEL, p[MOS_SOURCE])))
            net = getattr(bulk.get(name), "net", None)
            if net is not None:
                edges.append((name, _BULK, net))
        elif cls == ELEMENT_SOURCE:
            edges.extend((name, t, net) for t, net in p.items())
        else:
            edges.extend((name, _UNDIRECTED, net) for net in p.values())
    return edges


def _graph(source, element_marks, node_marks):
    classes = dict(source.column("device", "element_class"))
    kinds = dict(source.column("device", "kind"))
    diode = dict(source.column("device", "is_diode"))
    pins = dict(source.column("device", "pins"))
    bulk = dict(source.column("device", "bulk"))
    direction = dict(source.column("node", "port_direction"))
    emarks, nmarks = dict(element_marks), dict(node_marks)
    colour = {(ELEMENT, e): (ELEMENT, classes[e], kinds[e], bool(diode.get(e)), emarks.get(e, ())) for e in classes}
    colour.update({(NODE, n): (NODE, bool(r), direction.get(n) or "", nmarks.get(n, ()))
                   for n, r in source.column("node", "is_rail")})
    neighbours = {v: [] for v in colour}
    for element, label, net in _edges(classes, pins, bulk):
        neighbours[(ELEMENT, element)].append((label, (NODE, net)))
        neighbours[(NODE, net)].append((label, (ELEMENT, element)))
    return colour, neighbours


def _rank(signature):
    order = {s: i for i, s in enumerate(sorted(set(signature.values())))}
    return {v: order[s] for v, s in signature.items()}


def _refine(colour, neighbours):
    colour = _rank(colour)
    for _round in range(len(colour)):
        signature = {v: (colour[v], tuple(sorted((label, colour[u]) for label, u in neighbours[v]))) for v in colour}
        refined = _rank(signature)
        if len(set(refined.values())) == len(set(colour.values())):
            break
        colour = refined
    return colour


class _Union:
    def __init__(self, items):
        self.parent = {v: v for v in items}

    def find(self, v):
        while self.parent[v] != v:
            self.parent[v] = self.parent[self.parent[v]]
            v = self.parent[v]
        return v

    def union(self, a, b):
        ra, rb = self.find(a), self.find(b)
        if ra != rb:
            self.parent[rb] = ra


def _search(colour0, neighbours, start):
    """`start` = `colour0` 의 1-WL 평형 분할(`wl`, 다시 계산하지 않는다) -> (정준 위치 {정점: int}, 자기동형 생성자 list[dict])."""
    vertices = sorted(colour0, key=repr)                   # 탐색 순서만 정한다(결과 불변)
    base_rank = _rank(colour0)                             # 처음 색의 순위(정제 전)
    best = []                                              # [(cert, pos)]
    generators = {}                                        # 중복 제거: 정렬한 (정점, 상) 쌍 -> dict
    frames = []                                            # 마디마다 {"seen": {cert: pos}, "union": _Union}

    def certificate(pos):
        order = sorted(vertices, key=lambda v: pos[v])
        edges = sorted((pos[v], label, pos[u]) for v in vertices for label, u in neighbours[v])
        return tuple(base_rank[v] for v in order), tuple(edges)

    def individualize(colour, vertex):
        return _refine({v: (c, v != vertex) for v, c in colour.items()}, neighbours)

    def visit(colour):
        """반환: None(정상) 또는 가지치기로 돌아갈 마디 깊이."""
        classes = {}
        for v in vertices:
            classes.setdefault(colour[v], []).append(v)
        if len(classes) == len(vertices):
            cert = certificate(colour)
            if not best or cert < best[0][0]:
                best[:] = [(cert, dict(colour))]
            for d in range(len(frames) - 1, -1, -1):
                other = frames[d]["seen"].get(cert)
                if other is not None:
                    inverse = {p: v for v, p in other.items()}
                    moved = {v: inverse[p] for v, p in colour.items() if inverse[p] != v}
                    if moved:
                        generators.setdefault(tuple(sorted(moved.items(), key=repr)), moved)
                    for k in range(d + 1):
                        for v, image in moved.items():
                            frames[k]["union"].union(v, image)
                    return d
            for fr in frames:
                fr["seen"][cert] = dict(colour)
            return None
        target = classes[min(c for c, members in classes.items() if len(members) > 1)]
        frames.append({"seen": {}, "union": _Union(vertices)})
        here = len(frames) - 1
        explored = []
        for v in target:
            union = frames[here]["union"]
            if any(union.find(v) == union.find(w) for w in explored):
                continue
            ret = visit(individualize(colour, v))
            explored.append(v)
            if ret is not None and ret < here:
                frames.pop()
                return ret
        frames.pop()
        return None

    visit(start)
    return best[0][1], list(generators)


def canonical_form(source, element_marks=(), node_marks=()):
    marked, neighbours = _graph(source, element_marks, node_marks)        # 그래프 하나(D-2): 선언 표시를 넣은 색 그래프
    wl = _refine(marked, neighbours)                       # 1-WL 색 -- 서로 다른 색 사이의 순서
    position, generators = _search(marked, neighbours, wl)  # 같은 그래프의 정준 위치·자기동형 생성자(평형 분할 = wl)
    return Canonical(wl, position, tuple(sorted(generators)))
