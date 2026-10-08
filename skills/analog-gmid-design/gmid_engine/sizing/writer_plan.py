"""쓰기 계획 컴파일 -- 노드마다 writer 하나, MOS 마다 좌표 역할(쓰기/종속) (설계 3.1 1~3, 계획 N3.4·DEC-64·DEC-95 (3)).

진입점: `dc_writer_plan`(`@compute_block`) -- `dc_writer_plan(snapshot, target_nets, input_dc_declared, order_hints=NO_ORDER_HINTS)`. θ 무관(S0 당 1회).

모든 순서 결정의 키는 **구조 색 먼저**(`dc_struct_colour`, 이름을 읽지 않는 1-WL 정준 색) 그다음 이름이다. 이름이 실제로
결정을 가른 경우(같은 구조 색 후보가 서로 다른 결과로 갈린 경우)는 `graph.dc_tie_breaks` 에 `TieBreak` 로 남긴다.

1. 고정 노드 F = 레일(W0) ∪ spec 노드 목표(W3) ∪ (입력 DC 가 선언되면) 입력 포트(W2 (d)). 우선순위 W0 > W3 > W2.
2. G_vgs(용어집) = MOS (gate, source) 엣지 + 저항 (t0, t1) 엣지(잎 가지치기된 저항 포함 -- 전류 0 이라 강하 0)
   + 입력 DC 가 선언되지 않은 입력 포트끼리의 '같은 DC' 엣지(DEC-64 v1 '입력 DC 동일 가정', U2 기본안 (a)) -- 포트를
   (구조 색, 이름) 순으로 이웃끼리 잇는다(같은 색 포트가 둘 이상이면 `input_tie_order` 기록).
3. F 를 한 점으로 묶은 G_vgs 의 최소 신장 숲(Kruskal). 엣지 키 = (종류: 같은 DC < 저항 < MOS, [MOS 만] ratified 독립 선택 < 그 밖,
   diode < 그 밖, GB5 gm 요구 < 그 밖, 뒤 stage < 앞 stage, 원소 구조 색, 이름). 순환 성질상 각 기본 사이클에서 키가 가장 큰
   엣지가 비트리(종속)가 된다 = DEC-95 (3) 전체 순서 'ratified 선택 -> diode -> GB5 가 gm 을 요구하는 소자·뒤 stage 소자는 독립
   유지 -> 대칭 궤도 대표(같은 궤도 = 같은 구조 색) -> 이름'. 앞 세 단계 중 ratified·gm 요구·stage 는 `order_hints`(U1 S1v·
   `structure.json` ratified 로더가 채운다, 생략하면 없는 것 -- diode·색·이름만). 같은 (키 - 이름) 묶음이 트리/비트리로 갈리면
   `writer_edge` 기록(묶음 처리 뒤 성분 분할은 묶음 안 순서와 무관하므로 이름이 가르는 것은 그 묶음 안의 선택뿐이다).
4. 트리 엣지 = writer: F 와 각 성분 뿌리에서 BFS 로 먼 쪽 노드를 쓴다. MOS 가 source 에서 gate 를 쓰면 `vgs_gate`
   (diode 면 W1), gate 에서 source 를 쓰면 `vgs_source`(W2), 저항은 `resistor_drop`(W2), 같은 DC 엣지는 `input_tie`(W2).
5. F 가 없는 성분의 뿌리 = 그 성분의 입력 포트가 있으면 그중 (구조 색, 이름) 최소(y 키 `input_common_mode`), 없으면 성분 노드
   중 (구조 색, 이름) 최소(y 키 = 넷) -- W4. 최소 색 후보가 둘 이상이면 `w4_root` 기록. G_vgs 에 없는 노드 = W4(y 키 = 넷).
6. 비트리 MOS 엣지 = 종속 소자(좌표는 노드 VGS 순방향). 분류: gate·source 가 둘 다 고정 -> `fixed_vgs`, 같은 kind·같은
   (gate, source) 트리 엣지가 있으면 `parallel_vgs`(v0, partner), 나머지 `cycle_vgs`(v1·v2).
정지: 비트리 저항 엣지(값이 정해진 저항 루프 -- 저항을 종속시키는 규칙이 없음) -> `StructureUnresolvedError`
(`unsupported_rule_branch`, rule_branch `dc_resistor_cycle`).
"""
from collections import deque

from gmid_engine.authoring import INPUT_DIRECTION
from gmid_engine.core import StructureUnresolvedError, compute_block
from gmid_engine.graph import ELEMENT_MOS, ELEMENT_PASSIVE, MOS_TERMINAL_NAMES, UNSUPPORTED_RULE_BRANCH

from .s2_values import (
    BRANCH_RESISTOR_CYCLE,
    COORD_DEPENDENT,
    COORD_WRITER,
    DC_KEY,
    DC_WRITER_PLAN_WRITER,
    DEP_CYCLE,
    DEP_FIXED,
    DEP_PARALLEL,
    DEP_TREE,
    INPUT_GROUP_KEY,
    REL_INPUT_DC,
    REL_RAIL,
    REL_RESISTOR,
    REL_TARGET,
    REL_TIE,
    REL_VGS_GATE,
    REL_VGS_SOURCE,
    REL_WINDOW,
    RESISTOR,
    TIE_INPUT_ORDER,
    TIE_KRUSKAL,
    TIE_ROOT,
    TIER_W0,
    TIER_W1,
    TIER_W2,
    TIER_W3,
    TIER_W4,
    DeviceCoord,
    NodeWrite,
    NO_ORDER_HINTS,
    TieBreak,
)

READS = (
    ("device", "element_class"), ("device", "is_diode"), ("device", "kind"), ("device", "pins"),
    ("node", "is_rail"), ("node", "port_direction"), ("node", "dc_colour"), ("device", "dc_colour"),
)
WRITES = (("node", "dc_writer"), ("device", "dc_coord"), ("graph", "dc_tie_breaks"))
_FIXED = ("",)                                          # F 한 점(넷 이름이 될 수 없는 tuple 키)
_TIE, _RES, _DIODE, _MOS = (0, 1, 1 + 1, 1 + 1 + 1)    # 엣지 순위
_KIND_TIE, _KIND_RES, _KIND_MOS = (0, 1, 1 + 1)          # 엣지 키의 종류 칸(같은 DC < 저항 < MOS)


def _find(parent, x):
    while parent.setdefault(x, x) != x:
        parent[x] = parent[parent[x]]
        x = parent[x]
    return x


class _Plan:
    def __init__(self):
        self.writes = {}
        self.order = 0

    def put(self, net, tier, relation, element=None, known=None, y_key=None):
        self.writes[net] = NodeWrite(tier, relation, element, known, y_key, self.order)
        self.order += 1


def _edges(classes, kinds, pins, diode, colour, free_inputs, hints):
    """(키, 순위, 원소, a, b) 키 순. 같은 DC 엣지의 키 색 = 두 포트 색 정렬, 원소 = None. 키 = (종류, ratified, diode, gm 요구,
    -stage, 색, 이름) -- 종류 0 같은 DC / 1 저항 / 2 MOS, 나머지 칸은 MOS 만 값을 갖고(작을수록 독립으로 남는다) 힌트가 없으면
    ratified = gm 요구 = stage 칸이 모두 같아 종래 (diode < 그 밖, 색, 이름) 순서다."""
    independent, required = frozenset(hints.independent), frozenset(hints.gm_required)
    stage = dict(hints.stage)
    edges = []
    for i, (a, b) in enumerate(zip(free_inputs, free_inputs[1:])):
        edges.append(((_KIND_TIE, 0, 0, 0, 0, (), str(i)), _TIE, None, a, b))
    for name, cls in classes.items():
        p = dict(pins[name])
        if cls == ELEMENT_PASSIVE and kinds[name] == RESISTOR:
            t0, t1 = (net for _t, net in sorted(p.items()))
            edges.append(((_KIND_RES, 0, 0, 0, 0, (colour[name],), name), _RES, name, t0, t1))
        elif cls == ELEMENT_MOS:
            _d, gate, source = (p[t] for t in MOS_TERMINAL_NAMES)
            rank = _DIODE if diode.get(name) else _MOS
            key = (_KIND_MOS, 0 if name in independent else 1, 0 if diode.get(name) else 1, 0 if name in required else 1,
                   -stage[name] if name in stage else 1, (colour[name],), name)
            edges.append((key, rank, name, gate, source))
    return sorted(edges)


def _same_colour_groups(keys, items):
    """items(이름 tuple)를 keys[이름] 이 같은 묶음으로. 2개 이상인 묶음만."""
    groups = {}
    for item in items:
        groups.setdefault(keys[item], []).append(item)
    return [tuple(sorted(g)) for _k, g in sorted(groups.items()) if len(g) > 1]


@compute_block(DC_WRITER_PLAN_WRITER, reads=READS, writes=WRITES)
def dc_writer_plan(projection):
    target_nets, input_dc_declared, *rest = projection.extras
    hints = rest[0] if rest else NO_ORDER_HINTS
    classes = dict(projection.column("device", "element_class"))
    kinds = dict(projection.column("device", "kind"))
    pins = dict(projection.column("device", "pins"))
    diode = dict(projection.column("device", "is_diode"))
    ncolour = dict(projection.column("node", "dc_colour"))
    dcolour = dict(projection.column("device", "dc_colour"))

    def node_key(net):
        return ncolour[net], net

    nodes = tuple(sorted((net for net, _r in projection.column("node", "is_rail")), key=node_key))
    rails = tuple(net for net, is_rail in projection.column("node", "is_rail") if is_rail)
    inputs = tuple(net for net, d in projection.column("node", "port_direction") if d == INPUT_DIRECTION)
    plan = _Plan()
    ties = []
    fixed = {}
    for net in rails:
        fixed[net] = (TIER_W0, REL_RAIL)
    for net in target_nets:
        fixed.setdefault(net, (TIER_W3, REL_TARGET))
    if input_dc_declared:
        for net in inputs:
            fixed.setdefault(net, (TIER_W2, REL_INPUT_DC))
    for net in sorted(fixed, key=node_key):
        plan.put(net, *fixed[net])
    free_inputs = tuple(sorted((net for net in inputs if net not in fixed), key=node_key))
    for group in _same_colour_groups(ncolour, free_inputs):
        ties.append(TieBreak(TIE_INPUT_ORDER, group, group))
    parent = {}
    tree = []
    coords = {}
    groups = {}
    for key, rank, name, a, b in _edges(classes, kinds, pins, diode, dcolour, free_inputs, hints):
        ra = _find(parent, _FIXED if a in fixed else a)
        rb = _find(parent, _FIXED if b in fixed else b)
        is_tree = ra != rb
        if name is not None:
            groups.setdefault(key[:-1], []).append((name, is_tree))
        if is_tree:
            parent[ra] = rb
            tree.append((rank, name, a, b))
            if name is not None and rank != _RES:
                coords[name] = DeviceCoord(COORD_WRITER, DEP_TREE)
            continue
        if rank == _RES:
            raise StructureUnresolvedError(devices=(name,), detail={"reason": UNSUPPORTED_RULE_BRANCH,
                                                                    "rule_branch": BRANCH_RESISTOR_CYCLE,
                                                                    "nets": (a, b)})
        coords[name] = (a, b)
    for _key, members in sorted(groups.items()):
        decided = {is_tree for _n, is_tree in members}
        if len(decided) > 1:
            ties.append(TieBreak(TIE_KRUSKAL, tuple(sorted(n for n, _t in members)),
                                 tuple(sorted(n for n, t in members if t))))
    pairs = {(kinds[n], a, b): n for rank, n, a, b in tree if rank in (_DIODE, _MOS)}
    for name, value in tuple(coords.items()):
        if isinstance(value, DeviceCoord):
            continue
        gate, source = value
        if gate in fixed and source in fixed:
            coords[name] = DeviceCoord(COORD_DEPENDENT, DEP_FIXED)
        elif (kinds[name], gate, source) in pairs:
            coords[name] = DeviceCoord(COORD_DEPENDENT, DEP_PARALLEL, pairs[(kinds[name], gate, source)])
        else:
            coords[name] = DeviceCoord(COORD_DEPENDENT, DEP_CYCLE)
    edge_key = {(rank, name, a, b): (rank, -1 if name is None else dcolour[name], name or "", a, b)
                for rank, name, a, b in tree}
    adjacency = {}
    for edge in sorted(tree, key=edge_key.get):
        _rank, _name, a, b = edge
        adjacency.setdefault(a, []).append(edge)
        adjacency.setdefault(b, []).append(edge)

    def walk(start):
        queue = deque(start)
        while queue:
            u = queue.popleft()
            for rank, name, a, b in adjacency.get(u, ()):
                v = b if u == a else a
                if v in plan.writes:
                    continue
                if rank == _TIE:
                    plan.put(v, TIER_W2, REL_TIE, None, u)
                elif rank == _RES:
                    plan.put(v, TIER_W2, REL_RESISTOR, name, u)
                elif v == a:
                    plan.put(v, TIER_W1 if diode.get(name) else TIER_W2, REL_VGS_GATE, name, u)
                else:
                    plan.put(v, TIER_W2, REL_VGS_SOURCE, name, u)
                queue.append(v)

    walk(sorted(fixed, key=node_key))
    for net in sorted(adjacency, key=node_key):
        if net in plan.writes:
            continue
        component = _component(adjacency, net)
        ports = sorted((n for n in component if n in free_inputs), key=node_key)
        candidates = ports or sorted(component, key=node_key)
        root = candidates[0]
        tied = tuple(sorted(n for n in candidates if ncolour[n] == ncolour[root]))
        if len(tied) > 1:
            ties.append(TieBreak(TIE_ROOT, tied, (root,)))
        plan.put(root, TIER_W4, REL_WINDOW, None, None, INPUT_GROUP_KEY if ports else root)
        walk((root,))
    for net in nodes:
        if net not in plan.writes:
            plan.put(net, TIER_W4, REL_WINDOW, None, None, net)
    return {("node", "dc_writer"): plan.writes, ("device", "dc_coord"): coords,
            ("graph", "dc_tie_breaks"): {DC_KEY: tuple(ties)}}


def _component(adjacency, start):
    seen = {start}
    queue = deque((start,))
    while queue:
        u = queue.popleft()
        for _rank, _name, a, b in adjacency.get(u, ()):
            v = b if u == a else a
            if v not in seen:
                seen.add(v)
                queue.append(v)
    return seen
