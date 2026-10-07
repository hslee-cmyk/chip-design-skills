"""노드전압 목표 `human.node_voltage_targets_v` (설계 design_spec_format 1.6, N3.4 W3, CI-15).

진입점: `node_target_declaration(raw, topology) -> (tuple[(넷, V)] | PendingMark | None, tuple[SchemaHit])`.

모양: `{"pending": <ID>}` / `{}`(W3 목표 없음의 명시 선언) / `{<넷>: {"value_v": V, "source"}}`. 위반: `type`(형식·비유한 수),
`node_target_net`(넷이 어느 단자에도 없거나 레일이다 -- 레일 전압은 `supplies_v` 몫). 받는 키 밖은 `key_hits`.
`topology` 가 None 이면 넷 교차 검사를 하지 않는다.
"""
from ._spec_fields import COMMENT_PREFIX, at, finite_number, is_pending, key_hits, pending_decision
from ._terminal_nets import mos_terminal_nets, two_terminal_nets
from .spec_model import PendingMark
from .spec_sources import source_declaration_checks
from .topology_model import SchemaHit

SECTION = "node_voltage_targets_v"
WHERE = "human.node_voltage_targets_v"


def node_target_declaration(raw, topology):
    if is_pending(raw):
        return PendingMark(WHERE, pending_decision(raw)), ()
    if not isinstance(raw, dict):
        return None, (SchemaHit("type", WHERE, "node_voltage_targets_v 는 객체(넷 -> 목표)여야 한다: "
                              + type(raw).__name__),)
    hits = []
    nets = None
    if topology is not None:
        nets = (mos_terminal_nets(topology.devices) | two_terminal_nets(topology.passives + topology.sources)) \
            - topology.rails
    out = []
    for net in raw:
        if net.startswith(COMMENT_PREFIX):
            continue
        where = at(WHERE, net)
        entry = raw[net]
        if not isinstance(entry, dict):
            hits.append(SchemaHit("type", where, "노드 목표는 {value_v, source} 객체여야 한다", (net,)))
            continue
        hits.extend(key_hits(entry, ("value_v", "source"), where, (net,)))
        _source, source_hits = source_declaration_checks(entry.get("source"), where, SECTION)
        hits.extend(source_hits)
        if not finite_number(entry.get("value_v")):
            hits.append(SchemaHit("type", at(where, "value_v"), "value_v 는 유한 수여야 한다", (net,)))
        else:
            out.append((net, float(entry["value_v"])))
        if nets is not None and net not in nets:
            hits.append(SchemaHit("node_target_net", where, "넷 " + repr(net) + " 이 레일이 아닌 단자 넷이 아니다", (net,)))
    if hits:
        return None, tuple(hits)
    return tuple(sorted(out)), ()
