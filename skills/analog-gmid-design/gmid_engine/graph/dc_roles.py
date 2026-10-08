"""소자 DC 역할 (설계 design_mod3_structure_u2_u5 2.2, 계획 용어집 91행 (1)~(5), DEC-57, 41 §1.12.1, 40 §3.2-3).

진입점: `s1_dc_roles` -- core `@compute_block`(writer `S1_DC_ROLES_WRITER`, reads `DC_ROLES_READS`, writes `device.dc_role`).

    snapshot = s1_dc_roles(snapshot, dc_facts)

MOS 레코드에만 `DcRole(role, status, evidence)`(수동소자·이상원은 필드 없음). 지원 밖 MOS kind 가 있으면
`mos_kind_unsupported` 정지(core `StructureUnresolvedError`, detail reason `unsupported_rule_branch`).
`dc_facts` = ratified `dc_role` 사실 tuple ((소자, 값, approval_id, 근거 넷), ...) -- `build_s1` 이 넘긴다(없으면 빈 tuple).

'모든 뷰에서 교류접지' = `node.ac_ground_class` 가 rail 또는 gate_only_undriven(뷰 무관 (1)(2)). 뷰마다 다시 정하는 바이어스
종속 넷 (4)는 넣지 않는다(J-U3-a 기본안 -- 이 술어에 기댄 판정은 evidence.basis 에 J-U3-a).

1. `is_diode` -> diode_reference(rule "1").
1c. **복합 diode 소자**(`composite_diode.composite_diodes`, 41 §1.12.1) -> diode_reference(rule "1c", evidence.group = 묶음 멤버, basis[0] =
   `diode_reference_composite`(기준) | `diode_reference_composite_cascode`(캐스코드 기준 멤버)). 규칙 2 가 이 소자를 '기준'으로 읽어 같은 gate·source 묶음의
   나머지 멤버가 바이어스 전류원으로 갈린다(J-U3-c 를 구조로 푸는 경로).
2. `graph.gs_groups` 묶음마다: diode 기준 멤버가 있거나 gate 넷이 모든 뷰에서 교류접지면 기준 아닌 멤버 = bias_current_source
   (rule "2"). 기준이 없으면 멤버 전부 signal + status review_needed(rule "2", evidence.group = 멤버, basis J-U3-c).
3. 남은 소자 중 gate 넷이 모든 뷰에서 교류접지이고 source 넷이 레일이면 bias_current_source(rule "3").
5. 나머지 signal(rule "5").
4. (상속) ratified `dc_role` 사실(40 §3.2-3): 유도 결과가 J-U3-c review_needed 인 소자는 **override**(status ratified, rule "4", basis (approval_id, 값)),
   그 밖은 **confirm** -- 유도 값(diode_reference_composite* 구분 포함)과 같으면 status ratified + basis 에 approval_id, 다르면 status review_needed + basis
   (`structure_fact_mismatch`, 유도 값). 소자가 없는 사실(고아)은 S1 에 기록할 곳이 없어 `build_s1v` 가 `structure_fact_orphan` 으로 올린다.
"""
from gmid_engine.core import StructureUnresolvedError, compute_block, sorted_items

from .composite_diode import composite_diodes

from .s1_values import (
    AC_GROUND_GATE_ONLY,
    AC_GROUND_RAIL,
    BASIS_FACT_MISMATCH,
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
    ROLE_DIODE_COMPOSITE,
    ROLE_DIODE_COMPOSITE_CASCODE,
    ROLE_RULE_COMPOSITE,
    ROLE_RULE_DIODE,
    ROLE_RULE_FACT,
    ROLE_RULE_GATE_GROUND,
    ROLE_RULE_GS_GROUP,
    ROLE_RULE_REST,
    ROLE_SIGNAL,
    S1_DC_ROLES_WRITER,
    STATUS_DERIVED,
    STATUS_RATIFIED,
    STATUS_REVIEW_NEEDED,
    UNSUPPORTED_RULE_BRANCH,
    DcRole,
    Evidence,
)


@compute_block(S1_DC_ROLES_WRITER, reads=DC_ROLES_READS, writes=DC_ROLES_WRITES)
def s1_dc_roles(projection):
    dc_facts = projection.extras[0] if projection.extras else ()      # extras 없이 부르면(옛 호출) 사실 0
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
    for composite in composite_diodes(projection):
        for name in composite.reference + composite.cascode_members:
            nets = (pins[name][MOS_GATE], pins[name][MOS_SOURCE])
            tag = ROLE_DIODE_COMPOSITE if name in composite.reference else ROLE_DIODE_COMPOSITE_CASCODE
            roles[name] = DcRole(ROLE_DIODE, STATUS_DERIVED, Evidence(ROLE_RULE_COMPOSITE, nets, composite.members, (tag,)))
    for group in projection.value("graph", GRAPH_KEY, "gs_groups"):
        nets = (group.gate, group.source)
        has_diode = any(name in roles for name in group.members)
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
    for device, value, approval, _ in dc_facts:
        if device in roles:
            roles[device] = _with_fact(roles[device], value, approval)
    return {("device", "dc_role"): dict(sorted_items(roles))}


def _derived_value(role):
    """`dc_role` 사실 어휘에서의 유도 값 -- 복합 diode 소자는 묶음 안 위치(기준·캐스코드)로 구분한다."""
    if role.evidence.rule == ROLE_RULE_COMPOSITE:
        return role.evidence.basis[0]
    if role.evidence.rule == ROLE_RULE_FACT:
        return role.evidence.basis[1]
    return role.role


def _with_fact(derived, value, approval):
    """ratified 사실 하나를 유도 레코드에 적용한다(override | confirm | mismatch)."""
    evidence = derived.evidence
    if derived.status == STATUS_REVIEW_NEEDED:                     # J-U3-c 구조로 못 가르는 그룹 -> 사실이 정한다
        role = ROLE_DIODE if value in (ROLE_DIODE_COMPOSITE, ROLE_DIODE_COMPOSITE_CASCODE) else value
        return DcRole(role, STATUS_RATIFIED, Evidence(ROLE_RULE_FACT, evidence.nets, evidence.group, (approval, value)))
    if value == _derived_value(derived):
        return DcRole(derived.role, STATUS_RATIFIED, Evidence(evidence.rule, evidence.nets, evidence.group,
                                                              evidence.basis + (approval,)))
    return DcRole(derived.role, STATUS_REVIEW_NEEDED, Evidence(evidence.rule, evidence.nets, evidence.group,
                                                               evidence.basis + (BASIS_FACT_MISMATCH, _derived_value(derived))))
