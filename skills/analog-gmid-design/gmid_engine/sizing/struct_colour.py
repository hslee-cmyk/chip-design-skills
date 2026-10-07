"""구조 색 -- 이름을 쓰지 않는 결정론적 정준 키(1-WL 색 정제) 계산 블록 (사용자 대원칙 topology 독립·이름 분기 금지,
계획 DEC-95 (3) '대칭 궤도 대표 -> 그래도 동률일 때만 이름', 설계 3.1 2·3).

진입점: `dc_struct_colour`(`@compute_block`) -- `dc_struct_colour(snapshot)`. θ 무관(S0 당 1회).

* 그래프: 정점 = 노드(넷) ∪ 원소(MOS·수동소자·이상원), 엣지 = 원소–넷 연결에 단자 라벨: MOS `d`·`g`·`s`·`b`(bulk 넷이
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
from gmid_engine.graph import ELEMENT_MOS, ELEMENT_SOURCE, MOS_TERMINAL_NAMES

from .s2_values import DC_STRUCT_COLOUR_WRITER

READS = (
    ("device", "element_class"), ("device", "kind"), ("device", "is_diode"), ("device", "pins"), ("device", "bulk"),
    ("node", "is_rail"), ("node", "port_direction"),
)
WRITES = (("node", "dc_colour"), ("device", "dc_colour"))
_BULK = "b"
_UNDIRECTED = "t"
_NODE, _ELEMENT = ("n", "e")


def _edges(classes, pins, bulk):
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
        else:
            edges.extend((name, _UNDIRECTED, net) for net in p.values())
    return edges


@compute_block(DC_STRUCT_COLOUR_WRITER, reads=READS, writes=WRITES)
def dc_struct_colour(projection):
    classes = dict(projection.column("device", "element_class"))
    kinds = dict(projection.column("device", "kind"))
    diode = dict(projection.column("device", "is_diode"))
    pins = dict(projection.column("device", "pins"))
    bulk = dict(projection.column("device", "bulk"))
    direction = dict(projection.column("node", "port_direction"))
    colour = {(_ELEMENT, e): (_ELEMENT, classes[e], kinds[e], bool(diode.get(e))) for e in classes}
    colour.update({(_NODE, n): (_NODE, bool(r), direction.get(n) or "") for n, r in projection.column("node", "is_rail")})
    neighbours = {v: [] for v in colour}
    for element, label, net in _edges(classes, pins, bulk):
        neighbours[(_ELEMENT, element)].append((label, (_NODE, net)))
        neighbours[(_NODE, net)].append((label, (_ELEMENT, element)))
    colour = _ranked(colour)
    for _round in range(len(colour)):
        signature = {v: (colour[v], tuple(sorted((label, colour[u]) for label, u in neighbours[v]))) for v in colour}
        refined = _ranked(signature)
        if len(set(refined.values())) == len(set(colour.values())):
            break
        colour = refined
    return {
        ("node", "dc_colour"): {key: c for (tag, key), c in colour.items() if tag == _NODE},
        ("device", "dc_colour"): {key: c for (tag, key), c in colour.items() if tag == _ELEMENT},
    }


def _ranked(signature):
    order = {s: i for i, s in enumerate(sorted(set(signature.values())))}
    return {v: order[s] for v, s in signature.items()}
