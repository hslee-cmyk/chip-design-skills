"""VGS 관계 엣지 -- equal_vgs·vds_eq_vgs (설계 design_mod3_structure_u2_u5 3.2, 계획 N3.3 엣지 스키마).

진입점: `s1_rel_vgs` -- core `@compute_block`(writer `S1_REL_VGS_WRITER`, reads `REL_VGS_READS`,
writes `graph.rel_equal_vgs`·`graph.rel_vds_eq_vgs`).

    snapshot = s1_rel_vgs(snapshot)

* `rel_equal_vgs` = `graph.gs_groups` 묶음마다 `RelEdge(equal_vgs, dc, members, derived, evidence(nets = (gate, source)))`.
* `rel_vds_eq_vgs` = diode(`is_diode`) MOS 마다 `RelEdge(vds_eq_vgs, dc, (소자,), derived, evidence(nets = (drain, source)))`.
"""
from gmid_engine.core import compute_block

from .s1_values import (
    DOMAIN_DC,
    GRAPH_KEY,
    MOS_DRAIN,
    MOS_SOURCE,
    REL_EQUAL_VGS,
    REL_VDS_EQ_VGS,
    REL_VGS_READS,
    REL_VGS_WRITES,
    S1_REL_VGS_WRITER,
    STATUS_DERIVED,
    Evidence,
    RelEdge,
)


@compute_block(S1_REL_VGS_WRITER, reads=REL_VGS_READS, writes=REL_VGS_WRITES)
def s1_rel_vgs(projection):
    equal = tuple(RelEdge(REL_EQUAL_VGS, DOMAIN_DC, g.members, STATUS_DERIVED,
                          Evidence(REL_EQUAL_VGS, (g.gate, g.source)))
                  for g in projection.value("graph", GRAPH_KEY, "gs_groups"))
    pins = dict(projection.column("device", "pins"))
    diode = tuple(RelEdge(REL_VDS_EQ_VGS, DOMAIN_DC, (name,), STATUS_DERIVED,
                          Evidence(REL_VDS_EQ_VGS, (dict(pins[name])[MOS_DRAIN], dict(pins[name])[MOS_SOURCE])))
                  for name, flag in projection.column("device", "is_diode") if flag)
    return {("graph", "rel_equal_vgs"): {GRAPH_KEY: equal}, ("graph", "rel_vds_eq_vgs"): {GRAPH_KEY: diode}}
