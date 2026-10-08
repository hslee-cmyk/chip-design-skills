"""feedforward 셀 -- 주경로(D_max·slack)와 feedforward 묶음 (설계 41 §1.12.2, J-A).

진입점: `feedforward_cells(model, view, blocks, cells, stage) -> FeedforwardResult`  (전달 뷰마다 블록 구성(§1.7) 뒤, 복합 블록(§1.9) 앞에서 부른다).

* `view` = `ViewSeed`(여기·감지), `blocks` = `build_blocks` 결과(`BlocksResult` -- 주경로 **블록 출력노드**를 읽는다), `cells` = `classify_cells` 결과, `stage` = `stage_bfs` 결과
  (`StageResult.edges` = §1.6 비용의 능동 셀 엣지 -- 비용 정의를 이 파일이 다시 만들지 않는다).

**주경로**: G_f = 순방향 능동 셀 엣지(수동소자 제외)의 그래프. SCC 는 응축한다. D_max(n) = 여기에서 n 까지의 **최대** 비용(지나는 stage 시작 수의 최댓값; 0-1 BFS 의 최소와 다른
양). slack(e = u->v) = D_max(v) - D_max(u) - cost(e) >= 0. **주경로 셀** = 여기에서 감지까지 slack 0 엣지만으로 이어진 경로 위의 셀.

**feedforward 묶음**: 주경로 밖 신호 셀 c 가 주경로 넷 m 으로 들어가는 엣지(slack > 0)이고 m 이 주경로 **블록 출력노드**이면(측면 주입 K8 과의 구분), c 에서 거꾸로 주경로
넷(탭)에 닿을 때까지의 비주경로 신호 셀 전부가 묶음이다. 묶음 내부 넷에 drain 이 붙은 바이어스 전류원(`bias_cells`)과 diode 부하(`load_cells`)를 함께 묶는다.
**우회 조건**: 탭에서 m 까지 slack 0 경로가 지나는 블록 출력노드 중 묶음이 지나지 않는 것이 하나 이상 있어야 한다(없으면 FF 가 아니고 §1.7 병렬 합류로 처리). 산출은 탭마다
`FeedforwardCell(id=<탭>-><merge>, tap, merge, cells, bias_cells, load_cells, bypassed_blocks(우회한 블록 키, 앞 stage 부터), sign)`.
`ratio_candidates` = 묶음마다 r_ff = G_ff / gm_in(B_b) = 1 영점 상쇄 조건 후보(출처 기록) -- 값은 사용자 몫이고 spec 이 선언할 때만 제약이 된다.
주경로 최장 경로가 둘 이상이고 셀 집합이 다르면 `main_path_ambiguous`(review_needed) -- feedforward 후보가 있을 때만 본다(후보가 없으면 주경로 선택이 결과를 바꾸지 않는다).
"""
import dataclasses

from gmid_engine.core import sorted_items

from .s1_values import ROLE_BIAS
from .s1v_values import (
    CELL_CS,
    CELL_DIODE_LOAD,
    F_MAIN_PATH_AMBIGUOUS,
    SEVERITY_REVIEW,
    FeedforwardCell,
    FfRatioCandidate,
    Finding,
)

RATIO_RELATION = "r_ff = G_ff / gm_in(B_b) = 1"
RATIO_SOURCE = ("You, Embabi, Sanchez-Sinencio, IEEE JSSC 32(12), 1997; Leung & Mok, IEEE TCAS-I 48(9), 2001")


@dataclasses.dataclass(frozen=True)
class FeedforwardResult:
    """`main_path` = 주경로 셀 이름순, `cells` = FeedforwardCell(id 순), `ratio_candidates` = FfRatioCandidate, `findings` = 기록."""

    main_path: tuple
    cells: tuple
    ratio_candidates: tuple
    findings: tuple


def _components(nodes, successors):
    """강연결 성분 id {넷: 성분 번호} (Tarjan, 반복형, 노드·이웃 이름순)."""
    index = {}
    low = {}
    stack = []
    on_stack = set()
    comp = {}
    counter = 0
    for root in sorted(nodes):
        if root in index:
            continue
        work = [(root, iter(sorted(successors.get(root, ()))))]
        index[root] = low[root] = counter
        counter += 1
        stack.append(root)
        on_stack.add(root)
        while work:
            node, it = work[-1]
            pushed = False
            for nxt in it:
                if nxt not in index:
                    index[nxt] = low[nxt] = counter
                    counter += 1
                    stack.append(nxt)
                    on_stack.add(nxt)
                    work.append((nxt, iter(sorted(successors.get(nxt, ())))))
                    pushed = True
                    break
                if nxt in on_stack:
                    low[node] = min(low[node], index[nxt])
            if pushed:
                continue
            work.pop()
            if work:
                low[work[-1][0]] = min(low[work[-1][0]], low[node])
            if low[node] == index[node]:
                number = len(set(comp.values()))
                while True:
                    top = stack.pop()
                    on_stack.discard(top)
                    comp[top] = number
                    if top == node:
                        break
    return comp


def _longest(edges, sources, comp):
    """응축 DAG 위 최대 비용 {성분: D_max}. 여기 성분에서 도달 가능한 성분만 든다."""
    out = {}
    indegree = {}
    for a, b, cost, _ in edges:
        if comp[a] != comp[b]:
            out.setdefault(comp[a], []).append((comp[b], cost))
            indegree[comp[b]] = indegree.get(comp[b], 0) + 1
    depth = {comp[n]: 0 for n in sources if n in comp}
    ready = sorted(c for c in set(comp.values()) if not indegree.get(c))
    while ready:
        here = ready.pop()
        for nxt, cost in out.get(here, ()):
            if here in depth:
                depth[nxt] = max(depth.get(nxt, 0), depth[here] + cost)
            indegree[nxt] -= 1
            if not indegree[nxt]:
                ready.append(nxt)
    return depth


def _reach(start, adjacency):
    seen = set(start)
    pending = list(start)
    while pending:
        net = pending.pop()
        for nxt in adjacency.get(net, ()):
            if nxt not in seen:
                seen.add(nxt)
                pending.append(nxt)
    return seen


def _sign(model, cells_by_name, devices, edges, tap, merge):
    """탭에서 merge 까지 묶음 셀 엣지의 부호 곱(CS gate->drain = -1, 그 밖 +1). 경로마다 다르면 0."""
    signs = {tap: 1}
    pending = [tap]
    while pending:
        net = pending.pop()
        for a, b, _, devs in edges:
            if a != net or not set(devs) <= devices:
                continue
            m = model.mos_by_name.get(devs[0])
            flip = m is not None and len(devs) == 1 and cells_by_name[m.name].kind == CELL_CS and a == m.g and b == m.d
            value = signs[net] * (-1 if flip else 1)
            if b not in signs:
                signs[b] = value
                pending.append(b)
            elif signs[b] != value:
                signs[b] = 0
    return signs.get(merge, 0)


def _path_counts(main_edges, sources, comp):
    """응축 DAG 위 여기 성분에서 각 성분까지 서로 다른 엣지 열 수."""
    out = {}
    indegree = {}
    for a, b, _, _ in main_edges:
        if comp[a] != comp[b]:
            out.setdefault(comp[a], []).append(comp[b])
            indegree[comp[b]] = indegree.get(comp[b], 0) + 1
    count = {comp[n]: 1 for n in sources if n in comp}
    ready = sorted(c for c in set(comp.values()) if not indegree.get(c))
    while ready:
        here = ready.pop()
        for nxt in out.get(here, ()):
            count[nxt] = count.get(nxt, 0) + count.get(here, 0)
            indegree[nxt] -= 1
            if not indegree[nxt]:
                ready.append(nxt)
    return count


def feedforward_cells(model, view, blocks, cells, stage):
    info = {c.dev: c for c in cells.cells}
    edges = tuple(e for e in stage.edges if all(info[name].forward for name in e[3]))
    excite = tuple(net for net, _ in view.excite)
    sense = tuple(view.sense)
    nodes = {n for a, b, _, _ in edges for n in (a, b)}
    successors = {}
    for a, b, _, _ in edges:
        successors.setdefault(a, set()).add(b)
    comp = _components(nodes, successors)
    depth = _longest(edges, excite, comp)
    slack = {}
    for edge in edges:
        a, b, cost, _ = edge
        if comp[a] == comp[b]:
            slack[edge] = 0
        elif comp[a] in depth and comp[b] in depth:
            slack[edge] = depth[comp[b]] - depth[comp[a]] - cost
    zero = tuple(e for e in edges if slack.get(e) == 0)
    forward = {}
    backward = {}
    for a, b, _, _ in zero:
        forward.setdefault(a, set()).add(b)
        backward.setdefault(b, set()).add(a)
    on_path = _reach([n for n in excite if n in nodes], forward) & _reach([n for n in sense if n in nodes], backward)
    main_edges = tuple(e for e in zero if e[0] in on_path and e[1] in on_path)
    main_cells = {name for e in main_edges for name in e[3]}
    outputs = {net: b for b in blocks.blocks for net in b.outputs}
    internal = {}
    entries = []
    for edge in edges:
        a, b, _, devs = edge
        if slack.get(edge, 0) > 0 and not set(devs) & main_cells and b in on_path and b in outputs:
            entries.append(edge)
    found = []
    for edge in entries:
        bundle = set(edge[3])
        nets = set()
        taps = set()
        pending = [edge[0]]
        while pending:
            net = pending.pop()
            if net in on_path:
                taps.add(net)
                continue
            if net in nets:
                continue
            nets.add(net)
            for a, b, _, devs in edges:
                if b == net and not set(devs) & main_cells:
                    bundle.update(devs)
                    pending.append(a)
        for tap in sorted(taps):
            found.append((tap, edge[1], bundle, nets))
    groups = {}
    for tap, merge, bundle, nets in found:
        record = groups.setdefault((tap, merge), (set(), set()))
        record[0].update(bundle)
        record[1].update(nets)
    result = []
    for (tap, merge), (bundle, nets) in sorted_items(groups):
        between = (_reach([tap], forward) & _reach([merge], backward)) - {tap, merge}
        bypassed = sorted(((depth[comp[net]], tuple(sorted(set(outputs[net].outputs) & between)))
                           for net in between if net in outputs and comp[net] in depth), key=lambda p: (p[0], p[1]))
        keys = []
        for _, key in bypassed:
            if key and key not in keys:
                keys.append(key)
        if not keys:
            continue
        bias = sorted(m.name for m in model.mos if m.d in nets and m.name not in bundle and m.name not in main_cells
                      and m.dc_role == ROLE_BIAS and info[m.name].kind != CELL_DIODE_LOAD)
        load = sorted(m.name for m in model.mos if m.d in nets and m.name not in bundle and m.name not in main_cells
                      and info[m.name].kind == CELL_DIODE_LOAD)
        result.append(FeedforwardCell(tap + "->" + merge, tap, merge, tuple(sorted(bundle)), tuple(bias), tuple(load), tuple(keys),
                                      _sign(model, info, bundle, edges, tap, merge)))
    findings = ()
    if result:
        ambiguous = False
        for source in (n for n in excite if n in on_path):          # 입력마다 따로 센다(차동 입력의 두 반쪽은 서로 다른 입력)
            counts = _path_counts(main_edges, [source], comp)
            ambiguous = ambiguous or any(counts.get(comp[n], 0) > 1 for n in sense if n in comp and n in on_path)
        if ambiguous:
            findings = (Finding(F_MAIN_PATH_AMBIGUOUS, SEVERITY_REVIEW, "", tuple(sorted(main_cells)),
                                "주경로 최장 경로가 둘 이상이고 셀 집합이 달라 feedforward 분해의 기준이 모호하다", ("41 §1.12.2",)),)
    ratios = tuple(FfRatioCandidate(f.id, f.bypassed_blocks[0], RATIO_RELATION, RATIO_SOURCE) for f in result)
    return FeedforwardResult(tuple(sorted(main_cells)), tuple(result), ratios, findings)
