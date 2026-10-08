"""구조 색 -- 이름을 쓰지 않는 결정론적 정준 키(1-WL 색 정제) 계산 블록 (사용자 대원칙 topology 독립·이름 분기 금지,
계획 DEC-95 (3) '대칭 궤도 대표 -> 그래도 동률일 때만 이름', 설계 3.1 2·3).

진입점: `dc_struct_colour`(`@compute_block`) -- `dc_struct_colour(snapshot)`. θ 무관(S0 당 1회).

* 그래프(`_colour_graph`): 정점 = 노드(넷) ∪ 원소(MOS·수동소자·이상원), 엣지 = 원소–넷 연결에 단자 라벨: MOS `d`·`g`·`s`·`b`(bulk 넷이
  정해졌으면), 이상 전류원 `t0`·`t1`(전류 방향이 있다), 저항·커패시터 등 그 밖 2단자는 방향 없는 `t`.
* 처음 색: 원소 = (element_class, kind, is_diode), 노드 = (is_rail, port_direction). 이름·문서 순서를 쓰지 않는다.
* 정제: 새 색 = (옛 색, (라벨, 이웃 옛 색) 정렬 다중집합). 서명을 정렬해 0부터 순위를 매긴 정수가 색이다. 색 종류 수가 더
  늘지 않으면 멈춘다(최대 정점 수 회 -- 매 회 늘거나 멈추므로 유한).
* 성질: 이름 전단사·원소 순서 섞기에 대해 색 함수가 그대로 옮겨진다(이름을 읽지 않으므로). 같은 색 = 1-WL 로 구별되지 않는
  정점 -- 자기동형 궤도이면 이름 tie-break 로 고른 쪽과 다른 쪽이 자기동형으로 대응해 결과(θ 사상 후)가 같다. 1-WL 이
  자기동형이 아닌 정점을 같은 색으로 남기는 드문 경우(정규 그래프류)는 소비자가 `TieBreak` 로 기록한다.
* writes `node.dc_colour`·`device.dc_colour`(int).
"""
from gmid_engine.core import compute_block
from gmid_engine.graph import ELEMENT_MOS, ELEMENT_SOURCE, GRAPH_KEY, MOS_TERMINAL_NAMES

from ._helpers_colour import refine_colours
from .s2_values import DC_STRUCT_COLOUR_WRITER, RESISTOR
from .struct_canon import canonical_labeling

READS = (
    ("device", "element_class"), ("device", "kind"), ("device", "is_diode"), ("device", "pins"), ("device", "bulk"),
    ("node", "is_rail"), ("node", "port_direction"), ("device", "dc_nets"), ("graph", "dc_pruned"),
)
WRITES = (("node", "dc_colour"), ("device", "dc_colour"), ("node", "dc_orbit"), ("device", "dc_orbit"))
_BULK = "b"
_UNDIRECTED = "t"
_NODE, _ELEMENT = ("n", "e")


def _edges(classes, pins, bulk, directed):
    edges = []
    for name, cls in classes.items():
        p = dict(pins[name])
        if cls == ELEMENT_MOS:
            edges.extend((name, t, p[t]) for t in MOS_TERMINAL_NAMES)
            net = getattr(bulk.get(name), "net", None)
            if net is not None:
                edges.append((name, _BULK, net))
        elif cls == ELEMENT_SOURCE:
            edges.extend((name, t, net) for t, net in p.items())
        elif name in directed:
            # 직류 전류가 흐르는 저항: 전류 부호 규약이 단자 이름 순서(t0 -> t1)를 읽으므로 정준 라벨링의 자기동형은 끝 방향을 보존해야 한다
            # (끝을 뒤집어 그린 저항은 대칭 짝이 아니다 -- 같은 θ 전류가 부호 반대 값이 된다)
            edges.extend((name, term, net) for term, net in sorted(p.items()))
        else:
            edges.extend((name, _UNDIRECTED, net) for net in p.values())
    return edges


def _colour_graph(projection, element_marks=(), node_marks=(), directed=frozenset()):
    """(처음 색, 이웃). 정점 키 = ("n", 넷) | ("e", 원소). 처음 색: 원소 = (종류, element_class, kind, is_diode, 선언 표시), 노드 = (종류, is_rail,
    port_direction, 선언 표시) -- 선언 표시가 비면 종래 색과 같은 순서다. 이웃 = {정점: [(단자 라벨, 이웃 정점)]}."""
    classes = dict(projection.column("device", "element_class"))
    kinds = dict(projection.column("device", "kind"))
    diode = dict(projection.column("device", "is_diode"))
    pins = dict(projection.column("device", "pins"))
    bulk = dict(projection.column("device", "bulk"))
    direction = dict(projection.column("node", "port_direction"))
    emarks, nmarks = dict(element_marks), dict(node_marks)
    colour = {(_ELEMENT, e): (_ELEMENT, classes[e], kinds[e], bool(diode.get(e)), emarks.get(e, ())) for e in classes}
    colour.update({(_NODE, n): (_NODE, bool(r), direction.get(n) or "", nmarks.get(n, ()))
                   for n, r in projection.column("node", "is_rail")})
    neighbours = {v: [] for v in colour}
    for element, label, net in _edges(classes, pins, bulk, directed):
        neighbours[(_ELEMENT, element)].append((label, (_NODE, net)))
        neighbours[(_NODE, net)].append((label, (_ELEMENT, element)))
    return colour, neighbours


def _rank(signature):
    order = {s: i for i, s in enumerate(sorted(set(signature.values())))}
    return {v: order[s] for v, s in signature.items()}


@compute_block(DC_STRUCT_COLOUR_WRITER, reads=READS, writes=WRITES)
def dc_struct_colour(projection):
    element_marks, node_marks = projection.extras
    wl = refine_colours(*_colour_graph(projection))                      # 1-WL 색(선언 표시 없음) -- 서로 다른 색 사이의 순서
    pruned = {element for element, _round in projection.value("graph", GRAPH_KEY, "dc_pruned")}
    kinds = dict(projection.column("device", "kind"))
    # 직류 전류가 흐르는 저항(가지치기되지 않은 DC 원소)의 끝 방향은 전류 부호 규약(t0 -> t1)이 읽으므로 자기동형이 보존해야 한다
    directed = frozenset(name for name, nets in projection.column("device", "dc_nets")
                         if nets is not None and kinds[name] == RESISTOR and name not in pruned)
    marked, neighbours = _colour_graph(projection, element_marks, node_marks, directed)
    position, orbit = canonical_labeling(marked, neighbours)             # 선언을 보존하는 정준 위치·자기동형 궤도
    colour = _rank({v: (wl[v], position[v]) for v in wl})                # 같은 1-WL 색 안은 정준 위치로 -- 이름이 순서를 정하지 않는다
    return {
        ("node", "dc_colour"): {key: c for (tag, key), c in colour.items() if tag == _NODE},
        ("device", "dc_colour"): {key: c for (tag, key), c in colour.items() if tag == _ELEMENT},
        ("node", "dc_orbit"): {key: o for (tag, key), o in orbit.items() if tag == _NODE},
        ("device", "dc_orbit"): {key: o for (tag, key), o in orbit.items() if tag == _ELEMENT},
    }
