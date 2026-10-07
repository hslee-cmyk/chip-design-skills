"""DC 가지 -- segment 그래프의 분기 노드와 닻 사이 극대 직렬 사슬 (설계 design_mod3_structure_u2_u5 1.2 단계 4, DEC-71 (1)).

진입점: `s1_branches` -- core `@compute_block`(writer `S1_BRANCHES_WRITER`, reads `BRANCHES_READS`,
writes `graph.branches`·`node.dc_branch_node`).

    snapshot = s1_branches(snapshot)

* segment 그래프: 노드 = 넷, 엣지 = `graph.dc_segments` 의 Segment(병렬 합침 뒤).
* 분기 노드 = 레일이 아니고 segment 차수가 3 이상인 넷(직렬 넷은 들어오는 segment 하나·나가는 segment 하나뿐이다).
  `node.dc_branch_node` = 모든 node 레코드에 bool.
* 닻 = 레일 ∪ 분기 노드 ∪ 차수 1 넷. 가지 = 닻 사이 극대 직렬 segment 사슬. 닻을 이름순, 각 닻의 segment 를
  (반대 넷, 원소) 순으로 훑어 아직 안 쓴 segment 에서 사슬을 뻗는다. `Branch(id, ends, segments, has_ideal_source)` --
  id 는 생성 순번, `has_ideal_source` = 이상원(element_class ideal_source) 원소 포함(J13-d: 그 전압 강하는 기둥 KVL 자유 변수 --
  소비자 GB7 몫, 여기서는 표시만).
* 닻이 없는 고리(레일·분기 노드·잎 없는 순환 사슬)에 남은 segment 가 있으면 `dc_isolated_loop` 정지(core
  `StructureUnresolvedError`, detail reason `unsupported_rule_branch`, devices = 남은 segment 의 원소).
"""
from gmid_engine.core import StructureUnresolvedError, compute_block, sorted_items

from .s1_values import (
    BRANCH_DC_ISOLATED_LOOP,
    BRANCHES_READS,
    BRANCHES_WRITES,
    ELEMENT_SOURCE,
    GRAPH_KEY,
    S1_BRANCHES_WRITER,
    UNSUPPORTED_RULE_BRANCH,
    Branch,
)


@compute_block(S1_BRANCHES_WRITER, reads=BRANCHES_READS, writes=BRANCHES_WRITES)
def s1_branches(projection):
    segments = projection.value("graph", GRAPH_KEY, "dc_segments")
    element_class = dict(projection.column("device", "element_class"))
    is_rail = dict(projection.column("node", "is_rail"))
    adjacency = {}
    for index, seg in enumerate(segments):
        a, b = seg.nets
        adjacency.setdefault(a, []).append((b, seg.elements, index))
        adjacency.setdefault(b, []).append((a, seg.elements, index))
    for entries in adjacency.values():
        entries.sort()
    branch_nodes = frozenset(net for net, entries in adjacency.items()
                             if not is_rail.get(net) and len(entries) - 1 > 1)
    anchors = tuple(net for net, entries in sorted_items(adjacency)
                    if is_rail.get(net) or net in branch_nodes or len(entries) == 1)
    anchor_set = frozenset(anchors)
    used = set()
    branches = []
    for anchor in anchors:
        for other, _, index in adjacency[anchor]:
            if index in used:
                continue
            chain = [index]
            used.add(index)
            here = other
            while here not in anchor_set:
                (index,) = tuple(i for _, _, i in adjacency[here] if i not in used)
                chain.append(index)
                used.add(index)
                a, b = segments[index].nets
                here = b if a == here else a
            members = tuple(segments[i] for i in chain)
            has_source = any(element_class[name] == ELEMENT_SOURCE for seg in members for name in seg.elements)
            branches.append(Branch(len(branches), (anchor, here), members, has_source))
    left = tuple(i for i in range(len(segments)) if i not in used)
    if left:
        raise StructureUnresolvedError(
            devices=tuple(name for i in left for name in segments[i].elements),
            detail={"reason": UNSUPPORTED_RULE_BRANCH, "rule_branch": BRANCH_DC_ISOLATED_LOOP,
                    "nets": sorted_items({net for i in left for net in segments[i].nets})})
    return {("graph", "branches"): {GRAPH_KEY: tuple(branches)},
            ("node", "dc_branch_node"): {net: net in branch_nodes for net in is_rail}}
