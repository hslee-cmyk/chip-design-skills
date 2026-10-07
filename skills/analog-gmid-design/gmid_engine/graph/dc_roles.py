"""소자 DC 역할 (설계 design_mod3_structure_u2_u5 2.2, 계획 용어집 91행 (1)~(5), DEC-57).

진입점: `s1_dc_roles` -- core `@compute_block`(writer `S1_DC_ROLES_WRITER`, reads `DC_ROLES_READS`, writes `device.dc_role`).

    snapshot = s1_dc_roles(snapshot)

MOS 레코드에만 `DcRole(role, status, evidence)`(수동소자·이상원은 필드 없음). 지원 밖 MOS kind 가 있으면
`mos_kind_unsupported` 정지(core `StructureUnresolvedError`, detail reason `unsupported_rule_branch`).

'모든 뷰에서 교류접지' = `node.ac_ground_class` 가 rail 또는 gate_only_undriven(뷰 무관 (1)(2)). 뷰마다 다시 정하는 바이어스
종속 넷 (4)는 넣지 않는다(J-U3-a 기본안 -- 이 술어에 기댄 판정은 evidence.basis 에 J-U3-a).

1. `is_diode` -> diode_reference(rule "1").
2. `graph.gs_groups` 묶음마다: diode 멤버가 있거나 gate 넷이 모든 뷰에서 교류접지면 diode 아닌 멤버 = bias_current_source
   (rule "2"). 기준이 없으면 멤버 전부 signal + status review_needed(rule "2", evidence.group = 멤버, basis J-U3-c).
3. 남은 소자 중 gate 넷이 모든 뷰에서 교류접지이고 source 넷이 레일이면 bias_current_source(rule "3").
4. (상속) ratified `structure.json` 사실만 쓴다 -- 지금 ratified 사실이 없어(로더 없음) 발동 0, 구현하지 않는다(J-U3-b).
5. 나머지 signal(rule "5").
"""
from gmid_engine.core import StructureUnresolvedError, compute_block, sorted_items

from .s1_values import (
    AC_GROUND_GATE_ONLY,
    AC_GROUND_RAIL,
    BRANCH_MOS_KIND,
    DC_ROLES_READS,
    DC_ROLES_WRITES,
    ELEMENT_MOS,
    GRAPH_KEY,
    J_ALL_VIEW_GROUND,
    J_UNRESOLVED_GROUP,
    MOS_GATE,
    MOS_KINDS,
    MOS_SOURCE,
    ROLE_BIAS,
    ROLE_DIODE,
    ROLE_RULE_DIODE,
    ROLE_RULE_GATE_GROUND,
    ROLE_RULE_GS_GROUP,
    ROLE_RULE_REST,
    ROLE_SIGNAL,
    S1_DC_ROLES_WRITER,
    STATUS_DERIVED,
    STATUS_REVIEW_NEEDED,
    UNSUPPORTED_RULE_BRANCH,
    DcRole,
    Evidence,
)


@compute_block(S1_DC_ROLES_WRITER, reads=DC_ROLES_READS, writes=DC_ROLES_WRITES)
def s1_dc_roles(projection):
    kind = dict(projection.column("device", "kind"))
    mos = tuple(name for name, cls in projection.column("device", "element_class") if cls == ELEMENT_MOS)
    bad = tuple(name for name in mos if kind[name] not in MOS_KINDS)
    if bad:
        raise StructureUnresolvedError(devices=bad, detail={"reason": UNSUPPORTED_RULE_BRANCH,
                                                            "rule_branch": BRANCH_MOS_KIND})
    is_diode = dict(projection.column("device", "is_diode"))
    pins = {name: dict(p) for name, p in projection.column("device", "pins")}
    grounded = frozenset(net for net, cls in projection.column("node", "ac_ground_class")
                         if cls in (AC_GROUND_RAIL, AC_GROUND_GATE_ONLY))
    rails = frozenset(net for net, flag in projection.column("node", "is_rail") if flag)
    roles = {}
    for name in mos:
        if is_diode[name]:
            nets = (pins[name][MOS_GATE], pins[name][MOS_SOURCE])
            roles[name] = DcRole(ROLE_DIODE, STATUS_DERIVED, Evidence(ROLE_RULE_DIODE, nets))
    for group in projection.value("graph", GRAPH_KEY, "gs_groups"):
        nets = (group.gate, group.source)
        has_diode = any(is_diode[name] for name in group.members)
        if has_diode or group.gate in grounded:
            basis = () if has_diode else (J_ALL_VIEW_GROUND,)
            for name in group.members:
                if name not in roles:
                    roles[name] = DcRole(ROLE_BIAS, STATUS_DERIVED,
                                         Evidence(ROLE_RULE_GS_GROUP, nets, group.members, basis))
        else:
            for name in group.members:
                roles[name] = DcRole(ROLE_SIGNAL, STATUS_REVIEW_NEEDED,
                                     Evidence(ROLE_RULE_GS_GROUP, nets, group.members, (J_UNRESOLVED_GROUP,)))
    for name in mos:
        if name in roles:
            continue
        nets = (pins[name][MOS_GATE], pins[name][MOS_SOURCE])
        if nets[0] in grounded and nets[1] in rails:
            roles[name] = DcRole(ROLE_BIAS, STATUS_DERIVED,
                                 Evidence(ROLE_RULE_GATE_GROUND, nets, (), (J_ALL_VIEW_GROUND,)))
        else:
            roles[name] = DcRole(ROLE_SIGNAL, STATUS_DERIVED, Evidence(ROLE_RULE_REST, nets))
    return {("device", "dc_role"): dict(sorted_items(roles))}
