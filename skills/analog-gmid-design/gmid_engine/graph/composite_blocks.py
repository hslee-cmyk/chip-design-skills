"""복합 블록 -- 합류 노드를 공유하는 병렬 경로 묶음 (설계 41 §1.9, 계획 DEC-81·N3.7 판정 순서 ②).

진입점: `composite_blocks(model, blocks, buffers, cells, count_budget, view_id) -> CompositeResult`.

판정 순서 ①(입력 기준: 같은 입력·pass 묶음·캐스코드 합류·미러 합류 = 한 블록)은 `build_blocks` 가 이미 끝냈다. 여기서는 **그렇게 한 블록이 되지
않은 합류** 즉 서로 다른 stage 의 블록이 같은 넷을 공유한 경우(`BlocksResult.conflicts`)를 본다:
* 합류 노드가 어느 블록의 **출력노드** 이거나 전류 구동(두 셀 drain 전류 합산)이면 그 노드를 공유하는 블록들과 그 사이 경로에 놓인 블록들(합류 블록
  집합에서 도달하고 합류 블록 집합으로 이어지는 블록)을 복합 블록 하나로 묶는다. 합류 노드가 아닌 곳의 공유는 노드 배타 위반 `block_node_overlap`(review_needed).
* 묶은 뒤 블록 DAG 가 사슬이 아니면(묶음 바깥에서 묶음 입력을 만드는 블록이 서로 다른 stage 에 걸림) `composite_dag_not_chain`(기록만).
* 경로별 기여: 묶음 입력 넷에서 출력노드까지 셀 엣지(CS gate->drain = -1, CG source->drain·CD gate->source·pass·diode gate->source = +1)를 따라
  가는 단순 경로와 부호 곱. 경로 수가 계수 예산 `count_budget`(N_S)을 넘으면 `composite_over_budget`(기록만).
  묶음 크기 Π(= 격자 곱)는 LUT 축이 필요한 U9 몫이다 -- 여기서는 밑(`cells`)만 기록한다.
* J12 ratify 전에는 검증 발동 0 이라 모든 복합 블록은 `review_needed`(`composite_block_pending_ratify`, DEC-59 안전망)로 남는다.
묶음 뒤 `blocks` 는 복합 블록이 멤버를 대체한 목록(kind composite)이다.
"""
import dataclasses

from gmid_engine.core import sorted_items

from .s1_values import STATUS_REVIEW_NEEDED
from .s1v_values import (
    BLOCK_COMPOSITE,
    CELL_CD,
    CELL_CG,
    CELL_CS,
    CELL_DIODE_LOAD,
    CELL_PASS,
    F_COMPOSITE_BRANCH,
    F_COMPOSITE_BUDGET,
    F_COMPOSITE_PENDING,
    F_NODE_OVERLAP,
    SEVERITY_REVIEW,
    SEVERITY_UNSUPPORTED,
    Block,
    CompositeBlock,
    Finding,
)


@dataclasses.dataclass(frozen=True)
class CompositeResult:
    """`blocks` = 복합 블록이 멤버를 대체한 Block 목록, `composites` = CompositeBlock 기록, `findings` = 기록."""

    blocks: tuple
    composites: tuple
    findings: tuple


def _edges(model, cells, members):
    """묶음 멤버 소자의 신호 엣지 (from, to, sign)."""
    info = {c.dev: c for c in cells.cells}
    edges = []
    for name in members:
        m = model.mos_by_name[name]
        kind = info[name].kind
        if kind == CELL_CS:
            edges.append((m.g, m.d, -1))
        elif kind == CELL_CG:
            edges.append((m.s, m.d, 1))
        elif kind in (CELL_CD, CELL_DIODE_LOAD):
            edges.append((m.g, m.s, 1))
    for bundle in cells.bundles:
        if all(name in members for name in bundle.members):
            edges.extend(((bundle.nodes[0], bundle.nodes[1], 1), (bundle.nodes[1], bundle.nodes[0], 1)))
    return edges


def _paths(edges, sources, sinks, budget):
    """단순 경로 (넷 열, 부호) 와 예산 초과 여부."""
    out = []
    successors = {}
    for a, b, sign in edges:
        successors.setdefault(a, []).append((b, sign))
    over = False

    def walk(net, trail, sign):
        nonlocal over
        if over:
            return
        if net in sinks and len(trail) > 1:
            out.append((tuple(trail), sign))
            if len(out) > budget:
                over = True
                return
        for nxt, edge_sign in sorted(successors.get(net, ())):
            if nxt not in trail:
                walk(nxt, trail + [nxt], sign * edge_sign)

    for source in sorted(sources):
        walk(source, [source], 1)
    return tuple(out), over


def _groups(blocks_res, all_blocks):
    parent = {bid: bid for bid in range(len(all_blocks))}

    def find(x):
        while parent[x] != x:
            parent[x] = parent[parent[x]]
            x = parent[x]
        return x

    index = {bid: i for i, bid in enumerate(blocks_res.ids)}
    pending_nodes = []
    overlaps = []
    for net, ids in blocks_res.conflicts:
        involved = {index[bid] for bid in ids}
        involved |= {i for i, b in enumerate(all_blocks) if net in b.outputs}
        outputs_somewhere = any(net in all_blocks[i].outputs for i in involved)
        if not outputs_somewhere:
            overlaps.append((net, tuple(sorted(all_blocks[i].key for i in involved))))
            continue
        first = min(involved)
        for i in involved:
            parent[find(i)] = find(first)
        pending_nodes.append((first, net))
    merge_nodes = {}
    for first, net in pending_nodes:
        merge_nodes.setdefault(find(first), set()).add(net)
    return find, merge_nodes, overlaps


def composite_blocks(model, blocks, buffers, cells, count_budget, view_id):
    all_blocks = list(blocks.blocks)
    find, merge_nodes, overlaps = _groups(blocks, all_blocks)
    findings = [Finding(F_NODE_OVERLAP, SEVERITY_REVIEW, view_id, (net, *map(str, keys)),
                        "서로 다른 stage 블록이 합류 노드가 아닌 넷을 공유한다", ("N3.2-6",)) for net, keys in overlaps]
    # 블록 DAG(입력 넷 <- 출력노드)와 사이 경로 블록 포함
    produced = {}
    for i, b in enumerate(all_blocks):
        for net in b.outputs:
            produced.setdefault(net, set()).add(i)
    feeds = {i: {j for net in all_blocks[i].inputs for j in produced.get(net, ()) if j != i} for i in range(len(all_blocks))}
    reach_from = {}

    def downstream(i):
        if i not in reach_from:
            seen = set()
            pending = [j for j, preds in feeds.items() if i in preds]
            while pending:
                j = pending.pop()
                if j not in seen:
                    seen.add(j)
                    pending.extend(k for k, preds in feeds.items() if j in preds)
            reach_from[i] = seen
        return reach_from[i]

    def feeds_into(j, group):
        return any(j in feeds[i] for i in group)

    composites = []
    replaced = {}
    for root, nets in sorted_items(merge_nodes):
        group = {i for i in range(len(all_blocks)) if find(i) == root}
        between = {j for j in range(len(all_blocks)) if j not in group
                   and any(j in downstream(a) for a in group) and any(b in downstream(j) for b in group)}
        group |= between
        outputs = sorted({net for i in group for net in all_blocks[i].outputs}
                         - {net for j in group for net in all_blocks[j].inputs} | set(nets))
        inputs = sorted({net for i in group for net in all_blocks[i].inputs} - {net for j in group for net in all_blocks[j].outputs})
        names = {name for i in group for name, _ in all_blocks[i].roles}
        member_mos = {n for n in names if n in model.mos_by_name}
        paths, over = _paths(_edges(model, cells, member_mos), inputs, set(outputs), count_budget)
        members = tuple(sorted(all_blocks[i].key for i in group))
        outside_stages = {all_blocks[j].stage for j in range(len(all_blocks)) if j not in group and feeds_into(j, group)}
        chain_ok = len(outside_stages) <= 1
        if over:
            findings.append(Finding(F_COMPOSITE_BUDGET, SEVERITY_UNSUPPORTED, view_id, tuple(outputs),
                                    "복합 블록 경로 수가 계수 예산 N_S 를 넘는다", ("DEC-81", "N3.7")))
        if not chain_ok:
            findings.append(Finding(F_COMPOSITE_BRANCH, SEVERITY_UNSUPPORTED, view_id, tuple(outputs),
                                    "복합 블록으로 묶은 뒤에도 앞 블록이 서로 다른 stage 에서 갈라져 들어와 사슬이 아니다", ("DEC-81",)))
        findings.append(Finding(F_COMPOSITE_PENDING, SEVERITY_REVIEW, view_id, tuple(outputs),
                                "복합 블록 묶음 경계는 J12 ratify 전이다(검증 발동 0, DEC-59)", ("DEC-81", "J12")))
        composites.append(CompositeBlock(tuple(sorted(nets)), members, tuple(inputs), tuple(outputs), paths, len(member_mos),
                                         chain_ok, STATUS_REVIEW_NEEDED))
        merged_roles = sorted_items({name: role for i in group for name, role in all_blocks[i].roles})
        merged_nodes = tuple(sorted({n for i in group for n in all_blocks[i].nodes}))
        merged_imp = tuple(sorted({(n, level) for i in group for n, level in all_blocks[i].impedance if n in outputs}))
        stage = min(all_blocks[i].stage for i in group)
        merged = Block(tuple(outputs), BLOCK_COMPOSITE, stage, tuple(inputs), tuple(outputs), merged_roles, merged_nodes,
                       merged_imp, STATUS_REVIEW_NEEDED)
        replaced.update({i: (merged if i == min(group) else None) for i in group})
    final = [replaced[i] if i in replaced else b for i, b in enumerate(all_blocks) if replaced.get(i, b) is not None]
    return CompositeResult(tuple(final) + tuple(buffers.blocks), tuple(composites), tuple(findings))
