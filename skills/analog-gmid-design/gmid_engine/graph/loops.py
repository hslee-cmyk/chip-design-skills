"""루프 탐지 -- 방향 신호 그래프의 단순 사이클 전수 열거 (설계 41 §1.8, 계획 N3.2-2 '루프 뷰').

진입점: `enumerate_loops(model, ground, reach, cells, excite, count_budget, view_id) -> LoopsResult`.

**그래프**: 노드 = 이 뷰의 신호 넷에서 교류접지와 여기 포트(고정 넷)를 뺀 것. 방향 엣지:
* 신호 gate 를 가진 MOS 마다 gate->drain, gate->source (자기 엣지 gate == drain 은 폐경로가 아니다),
* source->drain: CG 셀, 또는 source 넷에 순방향 신호 셀의 drain 이 들어오는(= 전류 진입이 있는) MOS(구동 종류 판정을 쓰지 않는다 -- 소신호에서
  채널은 source 에 신호가 있으면 drain 으로 흘리기 때문이다),
* 수동소자(저항·커패시터)는 양방향, pass 묶음은 두 노드 사이 양방향(묶음 한 개로 센다).
세지 않는 것: 수동소자 하나·pass 묶음 하나의 왕복(같은 원소로 되돌아오는 길), 자기 엣지, 교류접지·여기 포트를 지나는 경로, 능동
엣지(MOS)가 하나도 없는 사이클(수동소자만의 고리는 신호 흐름 루프가 아니다 -- 병렬 R·C 쌍 등).
**열거**: 사이클을 노드 이름 정렬로 가장 작은 노드에서 시작하는 표현 하나로 정확히 한 번씩 센다(회전 불변 결정론). 같은 노드 쌍을 잇는 서로 다른
엣지(다른 소자)는 서로 다른 사이클이다. SCC 로 가지치기하고, **사이클 수와 탐색 걸음 수가 둘 다 `count_budget`(N_S, 시간 무관)을 넘으면**
`cycle_enumeration_over_budget`(기록만) 으로 멈춘다.
"""
import dataclasses

from gmid_engine.authoring import DC_CONDUCTING_PASSIVE_KINDS
from gmid_engine.core import sorted_items

from .s1v_values import (
    CELL_CG,
    CELL_CS,
    EDGE_CAPACITOR,
    EDGE_GATE_DRAIN,
    EDGE_GATE_SOURCE,
    EDGE_PASS,
    EDGE_RESISTOR,
    EDGE_SOURCE_DRAIN,
    F_CYCLE_BUDGET,
    PASSIVE_EDGES,
    SEVERITY_UNSUPPORTED,
    Finding,
    LoopEdge,
)


@dataclasses.dataclass(frozen=True)
class LoopsResult:
    """`nodes` = 루프 그래프 노드, `edges` = LoopEdge 전체, `cycles` = 사이클마다 LoopEdge 열(시작 노드 = 사이클 최소 노드), `findings` = 기록."""

    nodes: tuple
    edges: tuple
    cycles: tuple
    findings: tuple


def _graph_edges(model, nodes, cells):
    info = {c.dev: c for c in cells.cells}
    current_entry = {c.out for c in cells.cells if c.kind in (CELL_CS, CELL_CG) and c.forward}
    pass_members = {name for b in cells.bundles for name in b.members}
    edges = []
    for m in model.mos:
        if m.name in pass_members:
            continue
        if m.g in nodes:
            if m.d in nodes and m.d != m.g:
                edges.append(LoopEdge(m.g, m.d, m.name, EDGE_GATE_DRAIN))
            if m.s in nodes and m.s != m.g:
                edges.append(LoopEdge(m.g, m.s, m.name, EDGE_GATE_SOURCE))
        if m.s in nodes and m.d in nodes and m.s != m.d and m.g != m.d:
            if info[m.name].kind == CELL_CG or m.s in current_entry:
                edges.append(LoopEdge(m.s, m.d, m.name, EDGE_SOURCE_DRAIN))
    for p in model.passives:
        if p.a in nodes and p.b in nodes and p.a != p.b:
            etype = EDGE_RESISTOR if p.kind in DC_CONDUCTING_PASSIVE_KINDS else EDGE_CAPACITOR
            edges.append(LoopEdge(p.a, p.b, p.name, etype))
            edges.append(LoopEdge(p.b, p.a, p.name, etype))
    for b in cells.bundles:
        if b.nodes[0] in nodes and b.nodes[1] in nodes:
            edges.append(LoopEdge(b.nodes[0], b.nodes[1], b.members, EDGE_PASS))
            edges.append(LoopEdge(b.nodes[1], b.nodes[0], b.members, EDGE_PASS))
    return sorted_items(edges, key=lambda e: (e.src, e.dst, e.etype, str(e.element)))


def _components(nodes, adjacency):
    """강연결 성분 (Tarjan, 반복형)."""
    index = {}
    low = {}
    stack = []
    on_stack = set()
    comps = []
    counter = [0]
    for root in nodes:
        if root in index:
            continue
        work = [(root, iter(adjacency.get(root, ())))]
        index[root] = low[root] = counter[0]
        counter[0] += 1
        stack.append(root)
        on_stack.add(root)
        while work:
            node, it = work[-1]
            advanced = False
            for edge in it:
                nxt = edge.dst
                if nxt not in index:
                    index[nxt] = low[nxt] = counter[0]
                    counter[0] += 1
                    stack.append(nxt)
                    on_stack.add(nxt)
                    work.append((nxt, iter(adjacency.get(nxt, ()))))
                    advanced = True
                    break
                if nxt in on_stack:
                    low[node] = min(low[node], index[nxt])
            if advanced:
                continue
            work.pop()
            if work:
                parent = work[-1][0]
                low[parent] = min(low[parent], low[node])
            if low[node] == index[node]:
                comp = []
                while True:
                    top = stack.pop()
                    on_stack.discard(top)
                    comp.append(top)
                    if top == node:
                        break
                comps.append(frozenset(comp))
    return comps


def _reverses(previous, edge):
    return previous.element == edge.element and previous.etype == edge.etype and previous.src == edge.dst \
        and previous.dst == edge.src


def enumerate_loops(model, ground, reach, cells, excite, count_budget, view_id):
    nodes = tuple(sorted(reach.signal - ground - frozenset(excite)))
    edges = _graph_edges(model, frozenset(nodes), cells)
    adjacency = {}
    for e in edges:
        adjacency.setdefault(e.src, []).append(e)
    cycles = []
    steps = 0
    over = False
    for comp in _components(nodes, adjacency):
        if len(comp) == 1 and not any(e.dst == e.src for e in adjacency.get(next(iter(comp)), ())):
            continue
        order = sorted(comp)
        for start in order:
            allowed = {n for n in order if n >= start}
            path = []
            visited = {start}

            def walk(node):
                nonlocal steps, over
                for edge in adjacency.get(node, ()):
                    if over:
                        return
                    if edge.dst not in allowed or (path and _reverses(path[-1], edge)):
                        continue
                    steps += 1
                    if steps > count_budget:
                        over = True
                        return
                    if edge.dst == start:
                        cycle = tuple(path) + (edge,)
                        if any(e.etype not in PASSIVE_EDGES for e in cycle):
                            cycles.append(cycle)
                            if len(cycles) > count_budget:
                                over = True
                                return
                    elif edge.dst not in visited:
                        visited.add(edge.dst)
                        path.append(edge)
                        walk(edge.dst)
                        path.pop()
                        visited.discard(edge.dst)

            walk(start)
            if over:
                break
        if over:
            break
    findings = ()
    if over:
        findings = (Finding(F_CYCLE_BUDGET, SEVERITY_UNSUPPORTED, view_id, (), "단순 사이클 열거가 계수 예산 N_S 를 넘었다(시간 무관)",
                            ("N3.2-2", "review-M14")),)
    return LoopsResult(nodes, edges, tuple(cycles), findings)
