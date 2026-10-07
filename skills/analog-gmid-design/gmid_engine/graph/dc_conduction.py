"""DC 전도 그래프 -- 잎 저항 가지치기와 병렬 합침 segment (설계 design_mod3_structure_u2_u5 1.2 단계 1~3, DEC-70).

진입점: `s1_dc_conduction` -- core `@compute_block`(writer `S1_DC_CONDUCTION_WRITER`, reads `DC_CONDUCTION_READS`,
writes `graph.dc_pruned`·`graph.dc_segments`, graph 레코드 key `GRAPH_KEY`).

    snapshot = s1_dc_conduction(snapshot)

1. 엣지 = `device.dc_nets`(C1, authoring `dc_edges_unpruned` 의 유일 정의)가 None 아닌 원소. 먼저 정지 검사:
   * `device.unsupported` 가 붙은 원소가 있으면 정지(`rule_branch` = 그 원소의 unsupported 분기 이름). 지원 밖 MOS·이상원은
     DC 엣지이고, 지원 밖 수동 kind(인덕터 등)는 DC 를 통하는지 정의에 없어 엣지 여부를 정할 수 없다 -- 모두 조용히 넘기지 않는다.
   * 양 끝이 같은 넷인 엣지 -> `dc_self_loop` 정지.
2. 잎 가지치기(DEC-70, J13-b 기본안 = 열거 전에): 레일·포트가 아닌 넷 중 DC 엣지가 **저항 하나뿐**(element_class
   passive)인 넷과 그 저항을 지운다. 라운드마다 그 라운드 시작 시점의 잎 넷을 이름순으로 처리하고, 지울 때 이웃 넷의 차수만
   줄인다(큐 방식). `dc_pruned` = ((원소, 라운드), ...) (라운드, 원소) 순, 라운드는 1부터.
3. 병렬 합침(사용자 확정 10, J13-a 기본안): 남은 엣지를 같은 무향 넷 쌍끼리 `Segment(nets, elements)` 하나로 묶는다(종류
   무관). `dc_segments` = nets 순 tuple.

정지는 core `StructureUnresolvedError`(detail reason `unsupported_rule_branch`, `rule_branch`, `nets`; devices = 해당 원소).
"""
from gmid_engine.core import StructureUnresolvedError, compute_block, sorted_items

from .s1_values import (
    BRANCH_DC_SELF_LOOP,
    DC_CONDUCTION_READS,
    DC_CONDUCTION_WRITES,
    ELEMENT_PASSIVE,
    GRAPH_KEY,
    S1_DC_CONDUCTION_WRITER,
    UNSUPPORTED_RULE_BRANCH,
    Segment,
)


@compute_block(S1_DC_CONDUCTION_WRITER, reads=DC_CONDUCTION_READS, writes=DC_CONDUCTION_WRITES)
def s1_dc_conduction(projection):
    unsupported = dict(projection.column("device", "unsupported"))
    if unsupported:
        first = sorted_items(unsupported)[0][1]
        _stop(first, tuple(name for name, branch in sorted_items(unsupported) if branch == first), ())
    element_class = dict(projection.column("device", "element_class"))
    edges = tuple((name, nets) for name, nets in projection.column("device", "dc_nets") if nets is not None)
    loops = tuple((name, a) for name, (a, b) in edges if a == b)
    if loops:
        _stop(BRANCH_DC_SELF_LOOP, tuple(name for name, _ in loops), sorted_items({net for _, net in loops}))
    keep = frozenset(net for net, flag in projection.column("node", "is_rail") if flag) | frozenset(
        net for net, direction in projection.column("node", "port_direction") if direction is not None)
    pruned = _prune(edges, element_class, keep)
    gone = frozenset(name for name, _ in pruned)
    by_pair = {}
    for name, nets in edges:
        if name not in gone:
            by_pair.setdefault(nets, []).append(name)
    segments = tuple(Segment(nets, tuple(sorted(names))) for nets, names in sorted_items(by_pair))
    return {("graph", "dc_pruned"): {GRAPH_KEY: pruned}, ("graph", "dc_segments"): {GRAPH_KEY: segments}}


def _prune(edges, element_class, keep):
    """((원소, 라운드), ...). 차수는 처음 한 번 세고 지울 때 이웃만 줄인다."""
    at_net = {}
    for name, nets in edges:
        for net in nets:
            at_net.setdefault(net, set()).add(name)
    nets_of = dict(edges)

    def is_leaf(net):
        live = at_net.get(net, ())
        return (net not in keep and len(live) == 1
                and element_class[next(iter(live))] == ELEMENT_PASSIVE)

    pruned = []
    round_no = 1
    frontier = tuple(net for net, _ in sorted_items(at_net) if is_leaf(net))
    while frontier:
        touched = set()
        for net in frontier:
            if not is_leaf(net):                       # 같은 라운드에서 앞 넷이 이미 그 저항을 지움
                continue
            (name,) = tuple(at_net[net])
            pruned.append((name, round_no))
            for end in nets_of[name]:
                at_net[end].discard(name)
                touched.add(end)
        round_no += 1
        frontier = tuple(net for net in sorted(touched) if is_leaf(net))
    return tuple(sorted(pruned, key=lambda pair: (pair[1], pair[0])))


def _stop(rule_branch, devices, nets):
    raise StructureUnresolvedError(
        devices=devices, detail={"reason": UNSUPPORTED_RULE_BRANCH, "rule_branch": rule_branch, "nets": nets})
