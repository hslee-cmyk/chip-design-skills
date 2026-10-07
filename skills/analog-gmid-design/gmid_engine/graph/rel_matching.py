"""정합 관계 엣지 -- matching_ratio·l_class·matching_offset (설계 design_mod3_structure_u2_u5 3.2, 계획 N3.3).

진입점: `s1_rel_matching` -- core `@compute_block`(writer `S1_REL_MATCHING_WRITER`, reads `REL_MATCHING_READS`,
writes `graph.rel_matching_ratio`·`graph.rel_l_class`·`graph.rel_matching_offset`).

    snapshot = s1_rel_matching(snapshot)

* `rel_matching_ratio`(domain dc, derived) = gate 가 레일이 아닌 `graph.gs_groups` 묶음(전류 미러)마다 하나. 비율 값은 θ/W 몫.
* `rel_l_class`(domain geom, **proposed**, basis J-U4-a) = 같은 묶음마다 하나(미러 묶음 = L 동치류 제안).
* `rel_matching_offset`(domain dc_to_ss, basis J-U4-b) = 차동쌍 후보: 같은 kind, 같은 **비레일** source 넷인 MOS 묶음 중
  gate 넷이 둘 이상으로 갈리는 것. 멤버가 정확히 2개면 derived, 3개 이상이면 review_needed. gate 가 모두 같은 묶음은
  gs_groups(equal_vgs) 쪽이라 여기 넣지 않는다.
"""
from gmid_engine.core import compute_block, sorted_items

from .s1_values import (
    DOMAIN_DC,
    DOMAIN_DC_TO_SS,
    DOMAIN_GEOM,
    ELEMENT_MOS,
    GRAPH_KEY,
    J_DIFF_PAIR,
    J_L_CLASS,
    MOS_GATE,
    MOS_SOURCE,
    REL_L_CLASS,
    REL_MATCHING_OFFSET,
    REL_MATCHING_RATIO,
    REL_MATCHING_READS,
    REL_MATCHING_WRITES,
    S1_REL_MATCHING_WRITER,
    STATUS_DERIVED,
    STATUS_PROPOSED,
    STATUS_REVIEW_NEEDED,
    Evidence,
    RelEdge,
)


@compute_block(S1_REL_MATCHING_WRITER, reads=REL_MATCHING_READS, writes=REL_MATCHING_WRITES)
def s1_rel_matching(projection):
    rails = frozenset(net for net, flag in projection.column("node", "is_rail") if flag)
    mirrors = tuple(g for g in projection.value("graph", GRAPH_KEY, "gs_groups") if g.gate not in rails)
    ratio = tuple(RelEdge(REL_MATCHING_RATIO, DOMAIN_DC, g.members, STATUS_DERIVED,
                          Evidence(REL_MATCHING_RATIO, (g.gate, g.source))) for g in mirrors)
    l_class = tuple(RelEdge(REL_L_CLASS, DOMAIN_GEOM, g.members, STATUS_PROPOSED,
                            Evidence(REL_L_CLASS, (g.gate, g.source), (), (J_L_CLASS,))) for g in mirrors)
    kind = dict(projection.column("device", "kind"))
    pins = dict(projection.column("device", "pins"))
    by_source = {}
    for name, cls in projection.column("device", "element_class"):
        if cls == ELEMENT_MOS:
            net = dict(pins[name])
            if net[MOS_SOURCE] not in rails:
                by_source.setdefault((kind[name], net[MOS_SOURCE]), []).append((name, net[MOS_GATE]))
    offset = []
    for (_, source), entries in sorted_items(by_source):
        gates = sorted_items({gate for _, gate in entries})
        if len(gates) > 1:
            members = tuple(sorted(name for name, _ in entries))
            status = STATUS_DERIVED if len(members) - 1 == 1 else STATUS_REVIEW_NEEDED
            offset.append(RelEdge(REL_MATCHING_OFFSET, DOMAIN_DC_TO_SS, members, status,
                                  Evidence(REL_MATCHING_OFFSET, (source,) + gates, (), (J_DIFF_PAIR,))))
    return {("graph", "rel_matching_ratio"): {GRAPH_KEY: ratio}, ("graph", "rel_l_class"): {GRAPH_KEY: l_class},
            ("graph", "rel_matching_offset"): {GRAPH_KEY: tuple(offset)}}
