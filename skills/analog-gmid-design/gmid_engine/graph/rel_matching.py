"""정합 관계 엣지 -- matching_ratio·l_class (설계 design_mod3_structure_u2_u5 3.2, 계획 N3.3).

진입점: `s1_rel_matching` -- core `@compute_block`(writer `S1_REL_MATCHING_WRITER`, reads `REL_MATCHING_READS`,
writes `graph.rel_matching_ratio`·`graph.rel_l_class`).

    snapshot = s1_rel_matching(snapshot)

* `rel_matching_ratio`(domain dc, derived) = gate 가 레일이 아닌 `graph.gs_groups` 묶음(전류 미러)마다 하나. 비율 값은 θ/W 몫.
  DC 전류비 관계라 레이아웃 matching 분류(bias_distribution·feedback_shared)와 무관하게 묶음 전체를 담는다.
* `rel_l_class`(domain geom, **proposed**, basis J-U4-a) = 같은 묶음마다 하나(미러 묶음 = L 동치류 제안).
* 차동쌍 후보 `rel_matching_offset` 은 바이어스 형제 제외가 블록·가지 정보를 써서 `s1_matching_groups`
  (matching_groups.py)가 쓴다(SYNTHESIS Q8 (iii)).
"""
from gmid_engine.core import compute_block

from .s1_values import (
    DOMAIN_DC,
    DOMAIN_GEOM,
    GRAPH_KEY,
    J_L_CLASS,
    REL_L_CLASS,
    REL_MATCHING_RATIO,
    REL_MATCHING_READS,
    REL_MATCHING_WRITES,
    S1_REL_MATCHING_WRITER,
    STATUS_DERIVED,
    STATUS_PROPOSED,
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
    return {("graph", "rel_matching_ratio"): {GRAPH_KEY: ratio}, ("graph", "rel_l_class"): {GRAPH_KEY: l_class}}
