"""쓰기 계획 컴파일 -- 노드마다 writer 하나, MOS 마다 좌표 역할(쓰기/종속) (설계 3.1 1~3, 계획 N3.4·DEC-64·DEC-95 (3)).

진입점: `dc_writer_plan`(`@compute_block`) -- `dc_writer_plan(snapshot, target_nets, input_dc_declared, order_hints=NO_ORDER_HINTS)`. θ 무관(S0 당 1회).

모든 순서 결정의 키는 **구조 색 먼저**(`dc_colour` -- graph 대칭 블록 `s1_symmetry`, 이름을 읽지 않는 1-WL 색 + 정준 위치) 그다음 이름이다. 이름이 실제로
결정을 가른 경우(같은 구조 색 후보가 서로 다른 결과로 갈린 경우)는 `graph.dc_tie_breaks` 에 `TieBreak` 로 남긴다.

1. 고정 노드 F = 레일(W0) ∪ spec 노드 목표(W3) ∪ (입력 DC 가 선언되면) 입력 포트(W2 (d)). 우선순위 W0 > W3 > W2.
2. G_vgs(용어집) = MOS (gate, source) 엣지 + 저항 (t0, t1) 엣지(잎 가지치기된 저항 포함 -- 전류 0 이라 강하 0)
   ('같은 DC' 엣지는 없다 -- 계획 K-3: 입력 DC 가 선언되지 않아도 입력 포트는 MOS·저항으로만 G_vgs 에 닿는다).
3. F 를 한 점으로 묶은 G_vgs 의 최소 신장 숲(Kruskal). 엣지 키 = (종류: 저항 < MOS, [MOS 만] ratified 독립 선택 < 그 밖,
   diode < 그 밖, GB5 gm 요구 < 그 밖, 뒤 stage < 앞 stage, 원소 구조 색, 이름). 순환 성질상 각 기본 사이클에서 키가 가장 큰
   엣지가 비트리(종속)가 된다 = DEC-95 (3) 전체 순서 'ratified 선택 -> diode -> GB5 가 gm 을 요구하는 소자·뒤 stage 소자는 독립
   유지 -> 대칭 궤도 대표(같은 궤도 = 같은 구조 색) -> 이름'. 앞 세 단계 중 ratified·gm 요구·stage 는 `order_hints`(U1 S1v·
   `structure.json` ratified 로더가 채운다, 생략하면 없는 것 -- diode·색·이름만). 같은 (키 - 이름) 묶음이 트리/비트리로 갈리면
   `writer_edge` 기록(묶음 처리 뒤 성분 분할은 묶음 안 순서와 무관하므로 이름이 가르는 것은 그 묶음 안의 선택뿐이다).
4. 트리 엣지 = writer: F 와 각 성분 뿌리에서 BFS 로 먼 쪽 노드를 쓴다. MOS 가 source 에서 gate 를 쓰면 `vgs_gate`
   (diode 면 W1), gate 에서 source 를 쓰면 `vgs_source`(W2), 저항은 `resistor_drop`(W2).
5. F 가 없는 성분의 뿌리 = 그 성분의 입력 포트가 있으면 그중 (구조 색, 이름) 최소(y 키 = 그 뿌리 넷), 없으면 성분 노드
   중 (구조 색, 이름) 최소(y 키 = 넷) -- W4. 최소 색 후보가 둘 이상이면 `w4_root` 기록. G_vgs 에 없는 노드 = W4(y 키 = 넷).
   [DEC-106 입력 점] 입력 DC 미선언이고 입력 포트가 둘이며 role 이 `differential_input_p`·`differential_input_n` 각 하나이면 두 포트를 Kruskal·성분
   계산에서 한 점으로 묶는다(`_input_point`). 점이 F 에 닿지 않으면 W4 뿌리 = p 포트 하나(두 포트 모두 relation `input_point`, y 키 = p 포트 넷), F 에
   닿으면 v_cm 은 KVL 종속(y 성분 0): 먼저 쓰인 포트가 MOS·저항 관계를, 다른 포트가 `input_point`(known = 먼저 쓰인 포트)를 받는다.
6. 비트리 MOS 엣지 = 종속 소자(좌표는 노드 VGS 순방향). 분류: gate·source 가 둘 다 고정 -> `fixed_vgs`, 같은 kind·같은
   (gate, source) 트리 엣지가 있으면 `parallel_vgs`(v0, partner), 나머지 `cycle_vgs`(v1·v2).
7. [U17 ①-b, 설계 40 §2.4.8 '1변수 writer 집합'] `device.dc_self_referential` = MOS 마다 그 소자가 쓰는 노드가 자기 d·s·bulk 중 하나인가(diode 의 gate 쓰기,
   소스 추종의 source 쓰기 -- 1변수 방정식 노드). 쓰기 계획의 파생이라 S0 수준 필드이고(θ 무관), 평가 커널 `dc_columns`·탐색 상자 `cell_floor` 가 읽기만 한다.
(출력 포트 구조 분류 필드는 두지 않는다 -- 측정 구성은 출력 꼴과 무관하게 봉인점 KCL 로 잰다, 계획 N3.8 'ICMR servo 감도 -- KCL', 카드 IT-2c.)
정지: 입력 DC 미선언이고 입력 포트(G_vgs 밖 고립 입력 포트 포함)가 둘 이상인데 차동쌍 하나가 아니다 -> `StructureUnresolvedError`(rule_branch
`input_cm_undefined`, ports = 그 포트 넷들, 탐색 전 정지 -- DEC-106). 비트리 저항 엣지(값이 정해진 저항 루프 -- 저항을 종속시키는 규칙이 없음) -> `StructureUnresolvedError`
(`unsupported_rule_branch`, rule_branch `dc_resistor_cycle`).
"""
from collections import deque

from gmid_engine.authoring import INPUT_DIRECTION, ROLE_DIFFERENTIAL_INPUT_N, ROLE_DIFFERENTIAL_INPUT_P
from gmid_engine.core import StructureUnresolvedError, compute_block
from gmid_engine.graph import ELEMENT_MOS, ELEMENT_PASSIVE, GRAPH_KEY, MOS_TERMINAL_NAMES, UNSUPPORTED_RULE_BRANCH

from .s2_values import (
    BRANCH_INPUT_CM_UNDEFINED,
    BRANCH_INPUT_TARGET_ONE_PORT,
    BRANCH_RESISTOR_CYCLE,
    COORD_DEPENDENT,
    COORD_WRITER,
    DC_KEY,
    DC_WRITER_PLAN_WRITER,
    DEP_CYCLE,
    DEP_FIXED,
    DEP_PARALLEL,
    DEP_TREE,
    REL_INPUT_DC,
    REL_INPUT_POINT,
    REL_RAIL,
    REL_RESISTOR,
    REL_TARGET,
    REL_VGS_GATE,
    REL_VGS_SOURCE,
    REL_WINDOW,
    RESISTOR,
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
    ("node", "is_rail"), ("node", "port_direction"), ("node", "port_role"), ("node", "dc_colour"), ("device", "dc_colour"),
    ("device", "bulk"), ("graph", "gvgs_summary"),
)
WRITES = (("node", "dc_writer"), ("device", "dc_coord"), ("graph", "dc_tie_breaks"), ("device", "dc_self_referential"))
_SELF_RELATIONS = (REL_VGS_GATE, REL_VGS_SOURCE)
_DIFF_ROLES = (ROLE_DIFFERENTIAL_INPUT_P, ROLE_DIFFERENTIAL_INPUT_N)     # 입력 점이 되는 차동 입력쌍 role
_FIXED = ("",)                                          # F 한 점(넷 이름이 될 수 없는 tuple 키)
_RES, _DIODE, _MOS = (1, 1 + 1, 1 + 1 + 1)              # 엣지 순위
_KIND_RES, _KIND_MOS = (0, 1)                          # 엣지 키의 종류 칸(저항 < MOS)


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


def _edges(classes, kinds, pins, diode, colour, hints):
    """(키, 순위, 원소, a, b) 키 순. 키 = (종류, ratified, diode, gm 요구,
    -stage, 색, 이름) -- 종류 0 저항 / 1 MOS, 나머지 칸은 MOS 만 값을 갖고(작을수록 독립으로 남는다) 힌트가 없으면
    ratified = gm 요구 = stage 칸이 모두 같아 종래 (diode < 그 밖, 색, 이름) 순서다."""
    independent, required = frozenset(hints.independent), frozenset(hints.gm_required)
    stage = dict(hints.stage)
    edges = []
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
    roles = dict(projection.column("node", "port_role"))
    if not input_dc_declared:
        _stop_if_one_port_targeted(inputs, target_nets, roles)
    point = _input_point(free_inputs, roles)     # (p 포트, n 포트) 또는 None
    twin = {} if point is None else {point[0]: point[1], point[1]: point[0]}
    same_gs = frozenset(projection.value("graph", GRAPH_KEY, "gvgs_summary").gate_source_same)   # g = s 판정 정본 = s1_gvgs (O-210 RR-6)
    parent = {}
    tree = []
    coords = {}
    groups = {}
    edges = _edges(classes, kinds, pins, diode, dcolour, hints)
    for key, rank, name, a, b in edges:
        ra = _find(parent, _FIXED if a in fixed else canon(a, point))
        rb = _find(parent, _FIXED if b in fixed else canon(b, point))
        is_tree = ra != rb
        groups.setdefault(key[:-1], []).append((name, is_tree))
        if is_tree:
            parent[ra] = rb
            tree.append((rank, name, a, b))
            if rank != _RES:
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
    pairs = {(kinds[n], canon(a, point), canon(b, point)): n for rank, n, a, b in tree if rank in (_DIODE, _MOS)}
    for name, value in tuple(coords.items()):
        if isinstance(value, DeviceCoord):
            continue
        gate, source = value
        pair = (kinds[name], canon(gate, point), canon(source, point))
        if name in same_gs or (gate in fixed and source in fixed):        # g = s 소자: VGS = 0 으로 고정(좌표 ln_idu 성분 없음)
            coords[name] = DeviceCoord(COORD_DEPENDENT, DEP_FIXED)
        elif pair in pairs:
            coords[name] = DeviceCoord(COORD_DEPENDENT, DEP_PARALLEL, pairs[pair])
        else:
            coords[name] = DeviceCoord(COORD_DEPENDENT, DEP_CYCLE)
    edge_key = {(rank, name, a, b): (rank, dcolour[name], name, a, b)
                for rank, name, a, b in tree}
    adjacency = {}
    for edge in sorted(tree, key=edge_key.get):
        _rank, _name, a, b = edge
        adjacency.setdefault(a, []).append(edge)
        adjacency.setdefault(b, []).append(edge)

    def settle(net, queue):
        """`net` 을 큐에 넣고, 입력 점의 짝 포트가 아직 안 쓰였으면 같은 전압(KVL)으로 쓴다(known = net; 점이 W4 뿌리면 y 키도 같다)."""
        queue.append(net)
        mate = twin.get(net)
        if mate is not None and mate not in plan.writes:
            y_key = plan.writes[net].y_key if plan.writes[net].relation == REL_INPUT_POINT else None
            plan.put(mate, TIER_W2 if y_key is None else TIER_W4, REL_INPUT_POINT, None, net, y_key)
            queue.append(mate)

    def walk(start):
        queue = deque()
        for net in start:
            settle(net, queue)
        while queue:
            u = queue.popleft()
            for rank, name, a, b in adjacency.get(u, ()):
                v = b if u == a else a
                if v in plan.writes:
                    continue
                if rank == _RES:
                    plan.put(v, TIER_W2, REL_RESISTOR, name, u)
                elif v == a:
                    plan.put(v, TIER_W1 if diode.get(name) else TIER_W2, REL_VGS_GATE, name, u)
                else:
                    plan.put(v, TIER_W2, REL_VGS_SOURCE, name, u)
                settle(v, queue)

    def root_write(root):
        """F 에 닿지 않는 성분의 뿌리를 쓴다 -- 입력 점이면 뿌리는 p 포트(관계 `input_point`, y 키 = p 포트 넷), 그 밖은 `free_window`(y 키 = 넷)."""
        if point is not None and root in point:
            plan.put(point[0], TIER_W4, REL_INPUT_POINT, None, None, point[0])
            return point[0]
        plan.put(root, TIER_W4, REL_WINDOW, None, None, root)
        return root

    walk(sorted(fixed, key=node_key))
    for net in sorted(adjacency, key=node_key):
        if net in plan.writes:
            continue
        component = _component(adjacency, net, twin)
        ports = sorted((n for n in component if n in free_inputs), key=node_key)
        candidates = ports or sorted(component, key=node_key)
        root = candidates[0]
        if point is None or root not in point:
            tied = tuple(sorted(n for n in candidates if ncolour[n] == ncolour[root]))
            if len(tied) > 1:
                ties.append(TieBreak(TIE_ROOT, tied, (root,)))
        walk((root_write(root),))
    for net in nodes:
        if net not in plan.writes:
            walk((root_write(net),))
    bulk = {n: b.net for n, b in projection.column("device", "bulk")}
    self_ref = {m: False for m, c in classes.items() if c == ELEMENT_MOS}
    for net, w in plan.writes.items():
        if w.relation in _SELF_RELATIONS:
            terminals = dict(pins[w.element])
            self_ref[w.element] = self_ref[w.element] or net in (terminals["d"], terminals["s"], bulk[w.element])
    return {("node", "dc_writer"): plan.writes, ("device", "dc_coord"): coords,
            ("graph", "dc_tie_breaks"): {DC_KEY: tuple(ties)}, ("device", "dc_self_referential"): self_ref}


def _component(adjacency, start, twin):
    """`start` 의 G_vgs 성분 -- 입력 점의 두 포트(`twin`)는 한 점이라 한쪽에 닿으면 다른 쪽 성분도 이어진다."""
    seen = {start}
    queue = deque((start,))
    while queue:
        u = queue.popleft()
        neighbours = [b if u == a else a for _rank, _name, a, b in adjacency.get(u, ())]
        if u in twin:
            neighbours.append(twin[u])
        for v in neighbours:
            if v not in seen:
                seen.add(v)
                queue.append(v)
    return seen


def canon(net, point):
    """입력 점의 n 포트는 p 포트와 한 점이다(Kruskal·평행 판정의 대표 넷)."""
    return point[0] if point is not None and net == point[1] else net


def _stop_if_one_port_targeted(inputs, target_nets, roles):
    """입력 DC 미선언에서 차동 입력 두 포트(p·n 각 하나) 중 한 포트만 `node_voltage_targets_v` 로 선언 -> 탐색 전 정지(입력 점이 안 묶여 ΔV 가
    θ 함수가 된다 -- DEC-106). `input_cm_undefined` 와 같은 층·같은 분류 꼴, detail ports = 선언한 포트·선언 안 한 포트."""
    diff = {roles.get(net): net for net in inputs if roles.get(net) in _DIFF_ROLES}
    if len(diff) != len(_DIFF_ROLES) or sum(1 for net in inputs if roles.get(net) in _DIFF_ROLES) != len(_DIFF_ROLES):
        return
    declared = tuple(net for net in sorted(diff.values()) if net in target_nets)
    if len(declared) == 1:
        raise StructureUnresolvedError(devices=(), detail={"reason": UNSUPPORTED_RULE_BRANCH,
                                                           "rule_branch": BRANCH_INPUT_TARGET_ONE_PORT,
                                                           "ports": tuple(sorted(diff.values())), "declared": declared})


def _input_point(free_inputs, roles):
    """입력 DC 미선언 입력 점(DEC-106): 자유 입력 포트가 둘이고 role 이 차동 입력 p·n 각 하나이면 (p 포트, n 포트), 하나 이하면 None(옛 규칙),
    그 밖(차동쌍 둘, 차동쌍 없는 입력 둘 이상, 차동쌍 + 다른 입력)은 탐색 전 정지 -- 입력 공통모드가 정해지지 않는다."""
    if len(free_inputs) < len(_DIFF_ROLES):
        return None
    by_role = {roles.get(net): net for net in free_inputs}
    if len(free_inputs) == len(_DIFF_ROLES) and set(by_role) == set(_DIFF_ROLES):
        return by_role[ROLE_DIFFERENTIAL_INPUT_P], by_role[ROLE_DIFFERENTIAL_INPUT_N]
    raise StructureUnresolvedError(devices=(), detail={"reason": UNSUPPORTED_RULE_BRANCH,
                                                       "rule_branch": BRANCH_INPUT_CM_UNDEFINED,
                                                       "ports": tuple(free_inputs)})
