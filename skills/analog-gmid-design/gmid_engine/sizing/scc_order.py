"""읽기 의존 그래프와 순환 블록(SCC) 위상 순서, 기둥 이웃 (설계 3.1 4, 계획 SC-c, DEC-71 (1) 기둥).

진입점: `dc_scc_order`(`@compute_block`) -- `dc_scc_order(snapshot)`. θ 무관(S0 당 1회).

* 노드 x 의 writer 가 읽는 노드(고정 노드 제외)로 방향 엣지 x -> 읽는 노드:
  `vgs_gate`(소자 m, 아는 쪽 source) = {source, drain, bulk}(drain 이 x 면 자기 참조 = diode),
  `vgs_source`(아는 쪽 gate) = {gate, drain, bulk, x}(VDS·VSB 가 x 를 읽는다), `resistor_drop` = {아는 쪽},
  `free_window`(W4) = x 에 채널이 닿는 MOS 의 반대 채널 단자(창 = 인접
  전도 MOS 의 VDS ≥ 0 순서 제약).
* Tarjan SCC(반복형) -- 의존이 먼저 나오는 순서 그대로 풀이 순서다. SCC 안 노드는 쓰기 계획 순번 순.
  `cyclic` = 크기 > 1 또는 자기 참조. `devices` = 단자가 SCC 노드에 닿는 MOS(허용오차 조회 대상).
* `node.dc_column_nbrs` = S1 기둥(레일 쌍 노드-단순 경로)마다 그 노드의 앞·뒤 노드와 위치 -- 순환 블록 시작값(레일 사이
  위치 비례)만 읽는다. 노드-단순 경로는 전류 방향을 따르지 않을 수 있어(분기 노드에서 위로 돌아가는 경로) 창에는 쓰지 않는다.
"""
from gmid_engine.core import compute_block
from gmid_engine.graph import ELEMENT_MOS, GRAPH_KEY, MOS_TERMINAL_NAMES

from .s2_values import (
    DC_KEY,
    DC_SCC_ORDER_WRITER,
    REL_INPUT_DC,
    REL_RAIL,
    REL_RESISTOR,
    REL_TARGET,
    REL_VGS_GATE,
    REL_VGS_SOURCE,
    REL_WINDOW,
    ColumnNeighbor,
    SccEntry,
)

READS = (
    ("node", "dc_writer"), ("device", "pins"), ("device", "bulk"), ("device", "element_class"),
    ("graph", "columns"), ("graph", "branches"),
)
WRITES = (("graph", "dc_scc_order"), ("node", "dc_column_nbrs"))
FIXED_RELATIONS = (REL_RAIL, REL_TARGET, REL_INPUT_DC)


def _column_path(column, branches):
    current = column.rails[0]
    path = [current]
    for bid in column.branch_order:
        branch = branches[bid]
        segments = branch.segments if branch.ends[0] == current else tuple(reversed(branch.segments))
        for segment in segments:
            a, b = segment.nets
            current = b if a == current else a
            path.append(current)
    return path


def _neighbors(columns, branches):
    out = {}
    for column in columns:
        path = _column_path(column, branches)
        last = len(path) - 1
        for i in range(1, last):
            out.setdefault(path[i], set()).add(ColumnNeighbor(column.rails, path[i - 1], path[i + 1], i, last))
    return {net: tuple(sorted(items, key=lambda c: (c.rails, c.pred, c.succ, c.position, c.length)))
            for net, items in out.items()}


def _tarjan(nodes, deps):
    index = {}
    low = {}
    stack = []
    on_stack = set()
    result = []
    counter = 0
    for start in nodes:
        if start in index:
            continue
        work = [(start, iter(deps[start]))]
        index[start] = low[start] = counter
        counter += 1
        stack.append(start)
        on_stack.add(start)
        while work:
            node, children = work[-1]
            child = next(children, None)
            if child is None:
                work.pop()
                if work:
                    parent = work[-1][0]
                    low[parent] = min(low[parent], low[node])
                if low[node] == index[node]:
                    component = []
                    while True:
                        top = stack.pop()
                        on_stack.discard(top)
                        component.append(top)
                        if top == node:
                            break
                    result.append(component)
                continue
            if child not in index:
                index[child] = low[child] = counter
                counter += 1
                stack.append(child)
                on_stack.add(child)
                work.append((child, iter(deps[child])))
            elif child in on_stack:
                low[node] = min(low[node], index[child])
    return result


@compute_block(DC_SCC_ORDER_WRITER, reads=READS, writes=WRITES)
def dc_scc_order(projection):
    writers = dict(projection.column("node", "dc_writer"))
    pins = {name: dict(p) for name, p in projection.column("device", "pins")}
    bulk = dict(projection.column("device", "bulk"))
    classes = dict(projection.column("device", "element_class"))
    columns = projection.value("graph", GRAPH_KEY, "columns")
    branches = {b.id: b for b in projection.value("graph", GRAPH_KEY, "branches")}
    neighbors = _neighbors(columns, branches)
    channel = {name: (p[MOS_TERMINAL_NAMES[0]], p[MOS_TERMINAL_NAMES[-1]]) for name, p in pins.items()
               if classes.get(name) == ELEMENT_MOS}
    fixed = {net for net, w in writers.items() if w.relation in FIXED_RELATIONS}
    deps = {}
    for net, w in writers.items():
        if net in fixed:
            continue
        if w.relation in (REL_VGS_GATE, REL_VGS_SOURCE):
            drain, gate, source = (pins[w.element][t] for t in MOS_TERMINAL_NAMES)
            read = {source, drain, bulk[w.element].net, w.known}
            if w.relation == REL_VGS_SOURCE:
                read.add(net)
        elif w.relation in (REL_RESISTOR,):
            read = {w.known}
        else:
            read = {other for m in channel for a, other in (channel[m], channel[m][::-1]) if a == net}
        deps[net] = tuple(n for n in read if n not in fixed)          # 정렬은 아래(계획 순서 키로 -- 이름이 DFS 순서를 정하지 않게)
    deps = {net: tuple(sorted(items, key=lambda n: writers[n].order)) for net, items in deps.items()}
    order = sorted(deps, key=lambda n: writers[n].order)
    entries = []
    for component in _tarjan(order, deps):
        nodes = tuple(sorted(component, key=lambda n: writers[n].order))
        cyclic = len(nodes) > 1 or nodes[0] in deps[nodes[0]]
        touched = set(nodes)
        devices = tuple(sorted(name for name, p in pins.items() if classes.get(name) == ELEMENT_MOS
                               and any(p[t] in touched for t in MOS_TERMINAL_NAMES)))
        entries.append(SccEntry(len(entries), nodes, cyclic, devices))
    return {("graph", "dc_scc_order"): {DC_KEY: tuple(entries)}, ("node", "dc_column_nbrs"): neighbors}
