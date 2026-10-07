"""S1 구조 필드 계산 블록 (설계 design_mod3_s1_graph 5.2 단계 1~5, 규칙 C: 이 파일의 계산 블록 하나).

진입점: `s1_structure` -- core `@compute_block`(writer `S1_STRUCTURE_WRITER`, reads 없음, writes `STRUCTURE_WRITES`).

    snapshot = s1_structure(snapshot, devices, passives, sources, rails, ports)

추가 인자 = TopologyDoc 의 연결 투영(소자·수동소자·이상원·정렬 레일 tuple·포트) -- `connectivity_fp` 가 덮는 것과 같은
내용이라, `_` 주석만 바뀐 파일은 입력 버전이 같아 재계산하지 않는다. 쓰는 필드:

* node(넷마다 -- 단자 넷 ∪ 선언 bulk 넷 ∪ 레일): `terminals`((원소, 단자) 정렬 tuple, bulk 제외), `is_rail`,
  `port_direction`·`port_role`(포트 아니면 None), `ac_ground_class`(레일은 단자 유무와 무관하게 `AC_GROUND_RAIL`, 그 밖은 `static_ac_ground`,
  단자 없는 넷은 None).
* device(원소 이름마다, MOS·수동소자·이상원 모두): `element_class`, `kind`, `pins`(((단자, 넷), ...)).
  MOS 만: `bulk_declared`(넷 | None), `is_diode`(gate == drain). 2단자만: `value_key`, `value`.
  지원 kind 밖 원소만: `unsupported`(분기 이름, DEC-59 기록만 -- 정지는 그 원소를 쓰는 소비자가 낸다).
"""
from gmid_engine.authoring import INPUT_DIRECTION, TWO_TERMINAL_NAMES
from gmid_engine.core import compute_block

from .ac_ground_static import static_ac_ground
from .s1_index import terminal_index
from .s1_values import (
    AC_GROUND_RAIL,
    ELEMENT_MOS,
    ELEMENT_PASSIVE,
    ELEMENT_SOURCE,
    MOS_KINDS,
    MOS_TERMINAL_NAMES,
    S1_STRUCTURE_WRITER,
    STRUCTURE_WRITES,
    SUPPORTED_PASSIVE_KINDS,
    SUPPORTED_SOURCE_KINDS,
    UNSUPPORTED_BRANCHES,
)


@compute_block(S1_STRUCTURE_WRITER, writes=STRUCTURE_WRITES)
def s1_structure(projection):
    devices, passives, sources, rails, ports = projection.extras
    columns = {kind_field: {} for kind_field in STRUCTURE_WRITES}

    def put(kind, field, key, value):
        columns[(kind, field)][key] = value

    index = terminal_index(devices, passives, sources)
    port_of = {p.net: p for p in ports}
    input_nets = frozenset(p.net for p in ports if p.direction == INPUT_DIRECTION)
    ac_class = dict(static_ac_ground(index, rails, input_nets))
    pins_of = dict(index)
    nets = set(pins_of) | set(rails) | {x.bulk for x in devices if x.bulk is not None}
    for net in nets:
        port = port_of.get(net)
        put("node", "terminals", net, pins_of.get(net, ()))
        put("node", "is_rail", net, net in rails)
        put("node", "port_direction", net, None if port is None else port.direction)
        put("node", "port_role", net, None if port is None else port.role)
        put("node", "ac_ground_class", net, AC_GROUND_RAIL if net in rails else ac_class.get(net))

    branch_of = dict(UNSUPPORTED_BRANCHES)
    for x in devices:
        put("device", "element_class", x.name, ELEMENT_MOS)
        put("device", "kind", x.name, x.kind)
        put("device", "pins", x.name, tuple(zip(MOS_TERMINAL_NAMES, (x.d, x.g, x.s))))
        put("device", "bulk_declared", x.name, x.bulk)
        put("device", "is_diode", x.name, x.g == x.d)
        if x.kind not in MOS_KINDS:
            put("device", "unsupported", x.name, branch_of[ELEMENT_MOS])
    for element_class, elements, supported in ((ELEMENT_PASSIVE, passives, SUPPORTED_PASSIVE_KINDS),
                                               (ELEMENT_SOURCE, sources, SUPPORTED_SOURCE_KINDS)):
        for x in elements:
            put("device", "element_class", x.name, element_class)
            put("device", "kind", x.name, x.kind)
            put("device", "pins", x.name, tuple(zip(TWO_TERMINAL_NAMES, x.terminals)))
            put("device", "value_key", x.name, x.value_key)
            put("device", "value", x.name, x.value)
            if x.kind not in supported:
                put("device", "unsupported", x.name, branch_of[element_class])
    return columns
