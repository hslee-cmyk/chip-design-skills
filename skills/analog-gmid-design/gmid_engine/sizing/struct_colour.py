"""구조 색 -- 이름을 쓰지 않는 결정론적 정준 키 계산 블록 (사용자 대원칙 topology 독립·이름 분기 금지, 계획 DEC-95 (3), 설계 3.1 2·3, 40 §6).

진입점: `dc_struct_colour`(`@compute_block`) -- `dc_struct_colour(snapshot, element_marks, node_marks)`. θ 무관(S0 당 1회).

* 계산은 graph `canonical_form`(완전 정준 라벨링: 1-WL 색 `wl`·정준 위치·자기동형 생성자)과 `automorphism_orbits` 가 한다. 그래프는 정점 = 노드 ∪ 원소, 단자 라벨 엣지, 2단자 수동소자는
  방향 없음. `element_marks`·`node_marks` = 선언 표시(sizing CONTRACT 3.0b).
* `dc_colour` = (`wl`, 정준 위치) 쌍의 정렬 순위 -- 서로 다른 1-WL 색 사이의 순서는 종래와 같고, 같은 색 안은 정준 위치가 정해 **정점마다 유일**하다(이름이 순서를 정하지 않는다).
* `dc_orbit` = 자기동형 궤도 id(구성원의 정준 위치 최솟값), `graph.dc_symmetry` = 자기동형 생성자(search `current_symmetry` 의 근거).
* writes `node.dc_colour`·`device.dc_colour`·`node.dc_orbit`·`device.dc_orbit`(int), `graph.dc_symmetry`.
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
