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
from gmid_engine.graph import automorphism_orbits, canonical_form

from .s2_values import DC_KEY, DC_STRUCT_COLOUR_WRITER

READS = (
    ("device", "element_class"), ("device", "kind"), ("device", "is_diode"), ("device", "pins"), ("device", "bulk"),
    ("node", "is_rail"), ("node", "port_direction"),
)
WRITES = (("node", "dc_colour"), ("device", "dc_colour"), ("node", "dc_orbit"), ("device", "dc_orbit"),
          ("graph", "dc_symmetry"))
_NODE, _ELEMENT = ("n", "e")


def _rank(signature):
    order = {s: i for i, s in enumerate(sorted(set(signature.values())))}
    return {v: order[s] for v, s in signature.items()}


@compute_block(DC_STRUCT_COLOUR_WRITER, reads=READS, writes=WRITES)
def dc_struct_colour(projection):
    element_marks, node_marks = projection.extras
    canon = canonical_form(projection, element_marks, node_marks)        # graph 정준형: 1-WL 색·정준 위치·자기동형 생성자
    orbit = automorphism_orbits(canon)
    # 서로 다른 1-WL 색 사이의 순서는 종래 그대로, 같은 1-WL 색 안은 정준 위치로 -- 이름이 순서를 정하지 않는다
    colour = _rank({v: (canon.wl[v], canon.position[v]) for v in canon.wl})
    return {
        ("node", "dc_colour"): {key: c for (tag, key), c in colour.items() if tag == _NODE},
        ("device", "dc_colour"): {key: c for (tag, key), c in colour.items() if tag == _ELEMENT},
        ("node", "dc_orbit"): {key: o for (tag, key), o in orbit.items() if tag == _NODE},
        ("device", "dc_orbit"): {key: o for (tag, key), o in orbit.items() if tag == _ELEMENT},
        ("graph", "dc_symmetry"): {DC_KEY: canon.generators},
    }
