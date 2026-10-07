"""같은 VGS 묶음 -- (kind, gate 넷, source 넷)이 같은 MOS 2개 이상 (설계 design_mod3_structure_u2_u5 2.1, 용어집 91행 (2)).

진입점: `s1_gs_groups` -- core `@compute_block`(writer `S1_GS_GROUPS_WRITER`, reads `GS_GROUPS_READS`, writes `graph.gs_groups`).

    snapshot = s1_gs_groups(snapshot)

`graph.gs_groups` = `GsGroup(kind, gate, source, members)` tuple, (kind, gate, source) 순, members 이름순. 레일 gate 묶음도
포함한 원자료다. U3 DC 역할 (2)와 U4 `equal_vgs`·`matching_ratio`·`l_class` 가 **이 필드 하나**를 읽는다(개념당 정의 하나).
"""
from gmid_engine.core import compute_block, sorted_items

from .s1_values import (
    ELEMENT_MOS,
    GRAPH_KEY,
    GS_GROUPS_READS,
    GS_GROUPS_WRITES,
    MOS_GATE,
    MOS_SOURCE,
    S1_GS_GROUPS_WRITER,
    GsGroup,
)


@compute_block(S1_GS_GROUPS_WRITER, reads=GS_GROUPS_READS, writes=GS_GROUPS_WRITES)
def s1_gs_groups(projection):
    kind = dict(projection.column("device", "kind"))
    pins = dict(projection.column("device", "pins"))
    by_key = {}
    for name, cls in projection.column("device", "element_class"):
        if cls == ELEMENT_MOS:
            net = dict(pins[name])
            by_key.setdefault((kind[name], net[MOS_GATE], net[MOS_SOURCE]), []).append(name)
    groups = tuple(GsGroup(k, g, s, tuple(sorted(names))) for (k, g, s), names in sorted_items(by_key)
                   if len(names) > 1)
    return {("graph", "gs_groups"): {GRAPH_KEY: groups}}
