"""S1 -> 뷰 계산용 읽기 전용 모형 (설계 41 §1, 개념당 정의 하나: 단자 인덱스 질의는 여기서 한 번 만든다).

진입점: `net_model(s1) -> NetModel`(파생 술어 네 칸을 계산 -- 부르는 자리는 writer `s1v_fields` 하나), `net_index(s1)`(파생 술어 네 칸이 빈 색인 모형 -- 소비자 `coupling_vars` 가 그 네 칸을 S1v 필드에서 읽어 채운다).

S1 필드만 읽는다(`device.{element_class, kind, pins, dc_role}`(복합 diode 묶음 = dc_role evidence rule 1c 의 group, 41 §1.12.1), `node.{is_rail, port_direction, port_role, ac_ground_class}`).
SP1 의 모든 파일이 같은 모형 위에서 계산하므로 소자 목록을 파일마다 다시 풀지 않는다(S0 당 1회). 지원 밖 원소는 S1
`s1_dc_conduction` 이 이미 정지시켰으므로 여기서는 MOS·수동소자(저항·커패시터)·이상 전류원만 온다. 모든 모음은 이름순이다.
"""
import dataclasses
import types

from gmid_engine.authoring import INPUT_DIRECTION, TWO_TERMINAL_NAMES
from gmid_engine.core import sorted_items

from .s1_values import (
    ELEMENT_MOS,
    ELEMENT_PASSIVE,
    ELEMENT_SOURCE,
    MOS_DRAIN,
    MOS_GATE,
    MOS_SOURCE,
    ROLE_RULE_COMPOSITE,
    S1V_KEY,
)
from .s1v_values import Mos, NetModel, TwoTerm

def _group(items, net_of):
    table = {}
    for item in items:
        table.setdefault(net_of(item), []).append(item)
    return types.MappingProxyType({net: tuple(group) for net, group in sorted_items(table)})


DERIVED_FIELDS = ("diode_nodes", "composite_mos", "composite_bundles", "composite_internal")    # S1v 필드(writer s1v_fields)


def net_model(s1):
    """전체 모형 -- 파생 술어 넷(`DERIVED_FIELDS`)을 여기서 계산한다. 부르는 자리는 그 필드의 writer `s1v_fields` 하나다."""
    base = net_index(s1)
    dc_role = dict(s1.column("device", "dc_role"))
    mos, passives, rails = base.mos, base.passives, base.rails
    bundles = tuple(sorted({tuple(sorted(dc_role[m.name].evidence.group)) for m in mos
                           if dc_role[m.name].evidence.rule == ROLE_RULE_COMPOSITE}))
    members = frozenset(name for bundle in bundles for name in bundle)
    touching = {}
    for m in mos:
        for net in (m.d, m.g, m.s):
            touching.setdefault(net, set()).add(m.name)
    for passive in passives:
        for net in (passive.a, passive.b):
            touching.setdefault(net, set()).add(passive.name)
    composite_gates = frozenset(m.g for m in mos if dc_role[m.name].evidence.rule == ROLE_RULE_COMPOSITE)
    return dataclasses.replace(
        base, diode_nodes=frozenset(m.g for m in mos if m.g == m.d) | composite_gates,
        composite_mos=frozenset(name for bundle in bundles for name in bundle if name in base.mos_by_name),
        composite_bundles=tuple(frozenset(bundle) for bundle in bundles),
        composite_internal=frozenset(net for net, names in touching.items() if names <= members and net not in rails))


def net_index(s1):
    """S1 색인 모형 -- 파생 술어 네 칸(`DERIVED_FIELDS`)은 비어 있다(채우는 자리: `net_model` 계산, 소비자는 S1v 필드 읽기)."""
    element_class = dict(s1.column("device", "element_class"))
    kind = dict(s1.column("device", "kind"))
    pins = {name: dict(value) for name, value in s1.column("device", "pins")}
    dc_role = dict(s1.column("device", "dc_role"))
    mos = tuple(Mos(name, kind[name], pins[name][MOS_DRAIN], pins[name][MOS_GATE], pins[name][MOS_SOURCE],
                    dc_role[name].role, dc_role[name].status)
                for name, cls in sorted_items(element_class) if cls == ELEMENT_MOS)

    def two_terms(wanted):
        return tuple(TwoTerm(name, kind[name], *(pins[name][terminal] for terminal in TWO_TERMINAL_NAMES))
                     for name, cls in sorted_items(element_class) if cls == wanted)

    passives = two_terms(ELEMENT_PASSIVE)
    sources = two_terms(ELEMENT_SOURCE)
    rails = frozenset(net for net, flag in s1.column("node", "is_rail") if flag)
    static_ground = frozenset(net for net, cls in s1.column("node", "ac_ground_class") if cls is not None)
    direction = dict(s1.column("node", "port_direction"))
    role = dict(s1.column("node", "port_role"))
    inputs = tuple((net, role[net]) for net in sorted(direction) if direction[net] == INPUT_DIRECTION)
    outputs = tuple((net, role[net]) for net in sorted(direction)
                    if direction[net] is not None and direction[net] != INPUT_DIRECTION)
    by_passive = {}
    for passive in passives:
        for net in (passive.a, passive.b):
            by_passive.setdefault(net, []).append(passive)
    mos_by_name = types.MappingProxyType({m.name: m for m in mos})
    return NetModel(                                   # 파생 술어 네 칸은 비워 둔다 -- 채우는 자리는 `net_model`(계산)·`net_model_from_fields`(읽기)
        mos=mos, passives=passives, sources=sources, rails=rails, static_ground=static_ground,
        inputs=inputs, outputs=outputs, nets=tuple(net for net, _ in s1.column("node", "is_rail")),
        by_gate=_group(mos, lambda m: m.g), by_drain=_group(mos, lambda m: m.d), by_source=_group(mos, lambda m: m.s),
        by_passive=types.MappingProxyType({net: tuple(group) for net, group in sorted_items(by_passive)}), mos_by_name=mos_by_name,
        diode_nodes=frozenset())
