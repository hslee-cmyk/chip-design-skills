"""KCL 묶음 관계 엣지 -- 가지 하나 = 직렬 전류 하나 (설계 design_mod3_structure_u2_u5 3.2, 계획 N3.3).

진입점: `s1_rel_kcl` -- core `@compute_block`(writer `S1_REL_KCL_WRITER`, reads `graph.branches`, writes `graph.rel_kcl_group`).

    snapshot = s1_rel_kcl(snapshot)

`rel_kcl_group` = segment 가 2개 이상인 가지마다 `RelEdge(kcl_group, dc, members, derived, evidence(nets = 가지 ends))`.
members = 가지의 segment 원소 tuple 들(걷는 순서) -- 같은 segment 안 병렬 원소는 전류를 나누므로 segment 단위로 같은 전류다.
병렬 합침 segment 에 기대므로 evidence.basis = (J13-a,).
"""
from gmid_engine.core import compute_block

from .s1_values import (
    DOMAIN_DC,
    GRAPH_KEY,
    J_PARALLEL_MERGE,
    REL_KCL_GROUP,
    REL_KCL_READS,
    REL_KCL_WRITES,
    S1_REL_KCL_WRITER,
    STATUS_DERIVED,
    Evidence,
    RelEdge,
)


@compute_block(S1_REL_KCL_WRITER, reads=REL_KCL_READS, writes=REL_KCL_WRITES)
def s1_rel_kcl(projection):
    groups = tuple(RelEdge(REL_KCL_GROUP, DOMAIN_DC, tuple(seg.elements for seg in b.segments), STATUS_DERIVED,
                           Evidence(REL_KCL_GROUP, b.ends, (), (J_PARALLEL_MERGE,)))
                   for b in projection.value("graph", GRAPH_KEY, "branches") if len(b.segments) > 1)
    return {("graph", "rel_kcl_group"): {GRAPH_KEY: groups}}
