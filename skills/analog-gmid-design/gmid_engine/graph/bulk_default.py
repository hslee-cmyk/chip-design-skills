"""bulk 기본 규칙 계산 블록 (DEC-61, 사용자 확정 2026-10-07 6번, 설계 design_mod3_s1_graph 2.2 `bulk_default.py`).

진입점: `s1_bulk` -- core `@compute_block`(writer `S1_BULK_WRITER`, reads `BULK_READS`, writes `device.bulk`).

    snapshot = s1_bulk(snapshot, supplies)      # supplies = supplies_declaration 결과(tuple | None)

MOS 원소마다 `BulkResult`:
1. 선언 bulk 가 있으면 그 넷(`declared`).
2. kind 가 nmos·pmos 밖이면 `undetermined(unsupported_kind)`.
3. `supplies` 가 None 이면 `undetermined(needs_supplies_v)`.
4. 그 밖 `default_rule`: nmos = supplies 의 **최저 전위** 레일, pmos = **최고 전위** 레일(이름이 아니라 전위 값으로).

기본 규칙(4)을 쓸 소자가 하나라도 있으면 먼저 회로 전체를 검사하고, 조용히 묶지 않고 core `StructureUnresolvedError`
(detail reason = `unsupported_rule_branch`)로 정지한다:
* `bulk_rail_potential_tie` -- 최저 또는 최고 전위를 가진 레일이 둘 이상(어느 레일인지 전위로 정할 수 없다).
* `bulk_multi_domain` -- 전원 도메인이 여러 개: MOS(nmos·pmos) 채널 단자(d·s)가 닿는 레일 집합이
  {최저 전위 레일, 최고 전위 레일} 안에 들지 않는다(중간 전위 레일이나 최저/최고가 아닌 레일에 채널이 붙음 -- 예:
  pmos source 가 서로 다른 고전위 레일 둘에 붙음). 커패시터만 붙은 레일(agnd 같은 교류 기준)은 채널 레일이 아니라
  걸리지 않는다. detail: channel_rails, bulk_rails(최저, 최고), outside_rails; devices = 바깥 레일에 채널이 닿는 소자.
"""
from gmid_engine.core import StructureUnresolvedError, compute_block, sorted_items

from .s1_values import (
    BRANCH_MULTI_DOMAIN,
    BRANCH_POTENTIAL_TIE,
    BULK_DECLARED,
    BULK_DEFAULT_RULE,
    BULK_NEEDS_SUPPLIES,
    BULK_READS,
    BULK_UNDETERMINED,
    BULK_UNSUPPORTED_KIND,
    BULK_WRITES,
    ELEMENT_MOS,
    MOS_CHANNEL_TERMINALS,
    MOS_KINDS,
    NMOS,
    S1_BULK_WRITER,
    UNSUPPORTED_RULE_BRANCH,
    BulkResult,
)


@compute_block(S1_BULK_WRITER, reads=BULK_READS, writes=BULK_WRITES)
def s1_bulk(projection):
    (supplies,) = projection.extras
    element_class = dict(projection.column("device", "element_class"))
    kind = dict(projection.column("device", "kind"))
    declared = dict(projection.column("device", "bulk_declared"))
    pins = dict(projection.column("device", "pins"))
    rails = frozenset(net for net, flag in projection.column("node", "is_rail") if flag)
    mos = tuple(name for name, cls in sorted_items(element_class) if cls == ELEMENT_MOS)
    needs_rule = any(declared[name] is None and kind[name] in MOS_KINDS for name in mos)
    extremes = None
    if needs_rule and supplies is not None:
        supported = tuple(name for name in mos if kind[name] in MOS_KINDS)
        extremes = _bulk_rails(supplies, rails, supported, pins)
    result = {}
    for name in mos:
        if declared[name] is not None:
            bulk = BulkResult(declared[name], BULK_DECLARED)
        elif kind[name] not in MOS_KINDS:
            bulk = BulkResult(None, BULK_UNDETERMINED, BULK_UNSUPPORTED_KIND)
        elif extremes is None:
            bulk = BulkResult(None, BULK_UNDETERMINED, BULK_NEEDS_SUPPLIES)
        else:
            lowest, highest = extremes
            bulk = BulkResult(lowest if kind[name] == NMOS else highest, BULK_DEFAULT_RULE)
        result[name] = bulk
    return {BULK_WRITES[0]: result}


def _bulk_rails(supplies, rails, devices, pins):
    """(최저 전위 레일, 최고 전위 레일). 동률·다중 도메인이면 StructureUnresolvedError."""
    potential = dict(supplies)
    lowest = _unique_extreme(potential, min)
    highest = _unique_extreme(potential, max)
    channel_on = {}
    for name in devices:
        for term, net in pins[name]:
            if term in MOS_CHANNEL_TERMINALS and net in rails:
                channel_on.setdefault(net, set()).add(name)
    outside = tuple(net for net, _ in sorted_items(channel_on) if net not in (lowest, highest))
    if outside:
        raise StructureUnresolvedError(
            devices=tuple(name for net in outside for name in channel_on[net]),
            detail={"reason": UNSUPPORTED_RULE_BRANCH, "rule_branch": BRANCH_MULTI_DOMAIN,
                    "channel_rails": sorted_items(channel_on.keys()), "bulk_rails": (lowest, highest),
                    "outside_rails": outside},
        )
    return lowest, highest


def _unique_extreme(potential, pick):
    """`pick`(min | max) 전위를 가진 레일이 정확히 하나면 그 넷. 둘 이상(또는 레일 0)이면 정지."""
    value = pick(potential.values()) if potential else None
    nets = tuple(net for net, v in sorted_items(potential) if v == value)
    if len(nets) != 1:
        raise StructureUnresolvedError(detail={"reason": UNSUPPORTED_RULE_BRANCH, "rule_branch": BRANCH_POTENTIAL_TIE,
                                               "rails": nets, "potential": value})
    return nets[0]
