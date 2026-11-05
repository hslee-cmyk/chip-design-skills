"""쓰기 계획 컴파일 -- 노드마다 writer 하나, MOS 마다 좌표 역할(쓰기/종속) (설계 3.1 1~3, 계획 N3.4·DEC-64·DEC-95 (3), card 20261104-tb1-theta-class).

진입점: `dc_writer_plan`(`@compute_block`) -- `dc_writer_plan(snapshot, target_nets, input_dc_declared)`. θ 무관(S0 당 1회).

모든 순서 결정의 키에는 **이름이 없다**. 구조 색(`dc_colour` -- graph 대칭 블록 `s1_symmetry`, 이름을 읽지 않는 1-WL 색 + 정준 위치, 정점마다 유일)이 정준 위치 키다.
같은 키가 트리/비트리로 갈린 경우(`dc_colour` 가 유일하지 않을 때만 가능)는 `graph.dc_tie_breaks` 에 `TieBreak` 로 남긴다.

1. 고정 노드 F = 레일(W0) ∪ spec 노드 목표(W3) ∪ (입력 DC 가 선언되면) 입력 포트(W2 (d)). 우선순위 W0 > W3 > W2.
2. G_vgs(용어집) = MOS (gate, source) 엣지 + 저항 (t0, t1) 엣지(잎 가지치기된 저항 포함 -- 전류 0 이라 강하 0)
   ('같은 DC' 엣지는 없다 -- 계획 K-3: 입력 DC 가 선언되지 않아도 입력 포트는 MOS·저항으로만 G_vgs 에 닿는다).
3. 종속 멤버 선택(설계 40 §3.7-4, 두 단계). 입력은 graph 필드뿐이다: `device.theta_class`(S·B·F)·`device.dc_colour`·`graph.orbits`·S1v
   `graph.views`(stage)·`graph.dependent_facts`(ratified 사실).
   (1) **같은 kind·같은 (gate, source) 평행 관계**(고리 밖 비트리): 독립 유지 순위 'ratified override -> diode -> S·뒤 stage -> 대칭 궤도 대표 -> 정준 위치(작은 쪽)' 의 첫째가
       대표(독립), 나머지는 종속 `parallel_vgs`(짝 = 대표). 대표는 다른 등식에서 후보가 아니다(이미 독립으로 묶였다).
   (2) 대표만 남은 그래프(F 를 한 점으로 묶은 G_vgs 다중 그래프)에서 최소 신장 숲(Kruskal), 순환 성질상 각 기본 사이클(고리)에서 키가 가장 큰 엣지가 비트리(종속). 키 =
       (종류: 저항 < MOS, 묶임: 평행 대표 < 그 밖 < B 인 고리 멤버, 하위 키). 하위 키는 B 가 아닌 엣지 'diode -> 뒤 stage -> 정준 위치(작은 쪽)' 순으로 앞이 독립(평행 대표만
       'diode -> S·뒤 stage -> 궤도 대표 -> 정준 위치'), B 엣지는 반대로 'diode -> 궤도 대표 -> 소스 사슬 하류 -> 정준 위치(작은 쪽)' 순으로 앞이 먼저 종속이다.
       그래서 고리에 B 멤버가 있으면 B 가 종속이고, 없으면 독립 유지 순위의 마지막이 종속이다. 소스 사슬 하류 = source 넷(고정 아님)이 다른 MOS 의 gate 넷(= 그 VGS 로 정해지는 전압).
       레일 둘이 한 점 F 로 묶이므로 레일 사이 소자 쌍도 고리다(`graph.rel_kvl_branch` 는 이를 평행 v0 으로 접어 쓰지 않는다 -- 이 단계가 고리를 직접 센다).
   ratified `dependent_member` 사실: 평행 관계 사실은 override(value 가 종속), 고리 사실(그 기본 사이클의 멤버와 같은 subject)은 confirm(유도 종속과 다르면 `structure_fact_mismatch` 정지),
   value 가 멤버가 아니면 `structure_fact_mismatch`, 어떤 관계와도 멤버가 같지 않으면 `structure_fact_orphan`.
4. 트리 엣지 = writer: F 와 각 성분 뿌리에서 BFS 로 먼 쪽 노드를 쓴다. MOS 가 source 에서 gate 를 쓰면 `vgs_gate`
   (diode 면 W1), gate 에서 source 를 쓰면 `vgs_source`(W2), 저항은 `resistor_drop`(W2).
5. F 가 없는 성분의 뿌리 = 그 성분의 입력 포트가 있으면 그중 구조 색 최소(y 키 = 그 뿌리 넷), 없으면 성분 노드 중 구조 색 최소(y 키 = 넷) -- W4. 뿌리 후보(성분 안 후보와
   성분들의 뿌리 사이 모두)의 구조 색이 같으면 `StructureUnresolvedError`(rule_branch `dc_colour_not_unique`) -- 이름으로 깨지 않는다. G_vgs 에 없는 노드 = W4(y 키 = 넷).
   [DEC-106 입력 점] 입력 DC 미선언이고 입력 포트가 둘이며 role 이 `differential_input_p`·`differential_input_n` 각 하나이면 두 포트를 Kruskal·성분
   계산에서 한 점으로 묶는다(`_input_point`). 점이 F 에 닿지 않으면 W4 뿌리 = p 포트 하나(두 포트 모두 relation `input_point`, y 키 = p 포트 넷), F 에
   닿으면 v_cm 은 KVL 종속(y 성분 0): 먼저 쓰인 포트가 MOS·저항 관계를, 다른 포트가 `input_point`(known = 먼저 쓰인 포트)를 받는다.
6. 비트리 MOS 엣지 = 종속 소자(좌표는 노드 VGS 순방향). 분류: gate·source 가 둘 다 고정 -> `fixed_vgs`, 같은 kind·같은
   (gate, source) 대표가 있으면 `parallel_vgs`(v0, partner), 나머지 `cycle_vgs`(v1·v2).
7. [U17 ①-b, 설계 40 §2.4.8 '1변수 writer 집합'] `device.dc_self_referential` = MOS 마다 그 소자가 쓰는 노드가 자기 d·s·bulk 중 하나인가(diode 의 gate 쓰기,
   소스 추종의 source 쓰기 -- 1변수 방정식 노드). 쓰기 계획의 파생이라 S0 수준 필드이고(θ 무관), 평가 커널 `dc_columns`·탐색 상자 `cell_floor` 가 읽기만 한다.
(출력 포트 구조 분류 필드는 두지 않는다 -- 측정 구성은 출력 꼴과 무관하게 봉인점 KCL 로 잰다, 계획 N3.8 'ICMR servo 감도 -- KCL', 카드 IT-2c.)
정지: 입력 DC 미선언이고 입력 포트(G_vgs 밖 고립 입력 포트 포함)가 둘 이상인데 차동쌍 하나가 아니다 -> `StructureUnresolvedError`(rule_branch
`input_cm_undefined`, ports = 그 포트 넷들, 탐색 전 정지 -- DEC-106). 비트리 저항 엣지(값이 정해진 저항 루프 -- 저항을 종속시키는 규칙이 없음) -> `StructureUnresolvedError`
(`unsupported_rule_branch`, rule_branch `dc_resistor_cycle`).
"""
from collections import deque

from gmid_engine.authoring import REGION_OFF, INPUT_DIRECTION, ROLE_DIFFERENTIAL_INPUT_N, ROLE_DIFFERENTIAL_INPUT_P
from gmid_engine.core import StructureUnresolvedError, compute_block
from gmid_engine.graph import (AC_GROUND_GATE_ONLY, ELEMENT_MOS, ELEMENT_PASSIVE, F_FACT_MISMATCH, F_FACT_ORPHAN, GRAPH_KEY,
                               MOS_TERMINAL_NAMES, S1V_KEY, UNSUPPORTED_RULE_BRANCH, VIEW_TRANSFER)

from .s2_values import (
    BRANCH_DC_COLOUR_NOT_UNIQUE,
    BRANCH_INPUT_CM_UNDEFINED,
    BRANCH_INPUT_TARGET_ONE_PORT,
    BRANCH_OFF_ONLY_NODE,
    BRANCH_RESISTOR_CYCLE,
    COORD_DEPENDENT,
    CURRENT_SOURCE,
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
    THETA_CLASS_B,
    THETA_CLASS_S,
    TIE_KRUSKAL,
    TIER_W0,
    TIER_W1,
    TIER_W2,
    TIER_W3,
    TIER_W4,
    DeviceCoord,
    NodeWrite,
    TieBreak,
)

READS = (
    ("device", "element_class"), ("device", "is_diode"), ("device", "kind"), ("device", "pins"),
    ("node", "is_rail"), ("node", "port_direction"), ("node", "port_role"), ("node", "dc_colour"), ("device", "dc_colour"),
    ("device", "bulk"), ("graph", "gvgs_summary"), ("device", "region_decl"), ("device", "dc_nets"), ("node", "ac_ground_class"),
    ("device", "theta_class"), ("graph", "orbits"), ("graph", "views"), ("graph", "dependent_facts"),
)
WRITES = (("node", "dc_writer"), ("device", "dc_coord"), ("graph", "dc_tie_breaks"), ("device", "dc_self_referential"))
_SELF_RELATIONS = (REL_VGS_GATE, REL_VGS_SOURCE)
_DIFF_ROLES = (ROLE_DIFFERENTIAL_INPUT_P, ROLE_DIFFERENTIAL_INPUT_N)     # 입력 점이 되는 차동 입력쌍 role
_FIXED = ("",)                                          # F 한 점(넷 이름이 될 수 없는 tuple 키)
_RES, _DIODE, _MOS = (1, 1 + 1, 1 + 1 + 1)              # 엣지 순위
_KIND_RES, _KIND_MOS = (0, 1)                          # 엣지 키의 종류 칸(저항 < MOS)
_PINNED, _FREE, _LOOP_B = (0, 1, 1 + 1)                # 엣지 키의 묶임 칸: 평행 대표 < 그 밖 < 고리 안 B


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


def _stop_fact(reason, members, **detail):
    raise StructureUnresolvedError(devices=tuple(sorted(members)), detail={"reason": reason, "concept": "dependent_member", **detail})


def _stages(views):
    """{MOS: S1v stage 번호(전달 뷰 블록 중 최소)} -- 큰 쪽이 뒤 stage. S1v 가 없으면 비어 있다."""
    stage = {}
    for view in views:
        if view.kind == VIEW_TRANSFER:
            for block in view.blocks:
                for name, _role in block.roles:
                    stage[name] = min(block.stage, stage.get(name, block.stage))
    return stage


def _off_undetermined_nets(off, kinds, pins, dc_nets, seeds):
    """전압 결정 넷(`seeds` = 레일·고정 넷·선언 bias·입력 포트)에서 BFS 로 닿지 않는 넷 중 `off` 소자 d·g·s 가 닿는 넷(정렬).
    전도 엣지 = 정본 `device.dc_nets`(None 아닌 원소)에서 `off` 소자와 전류원을 뺀 것. 게이트·전류원·off 채널은 전압을 정하지 못한다. `off` 선언이 없으면 빈 결과."""
    if not off:
        return []
    adj = {}
    for name, nets in dc_nets.items():
        if nets is None or name in off or kinds[name] == CURRENT_SOURCE:
            continue
        adj.setdefault(nets[0], set()).add(nets[1])
        adj.setdefault(nets[1], set()).add(nets[0])
    reached = set(seeds)
    queue = deque(reached)
    while queue:
        for nxt in adj.get(queue.popleft(), ()):
            if nxt not in reached:
                reached.add(nxt)
                queue.append(nxt)
    touched = {net for name in off for net in dict(pins[name]).values()}
    return sorted(touched - reached)


@compute_block(DC_WRITER_PLAN_WRITER, reads=READS, writes=WRITES)
def dc_writer_plan(projection):
    target_nets, input_dc_declared = projection.extras
    off = frozenset(m for m, r in projection.column("device", "region_decl") if r.region == REGION_OFF)      # `off` 선언 소자(READS `device.region_decl`) -- 쓰기 계획 엣지·좌표가 없다
    classes = {n: c for n, c in projection.column("device", "element_class") if n not in off}
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
    on_gates = {dict(pins[m])[MOS_TERMINAL_NAMES[1]] for m, c in classes.items() if c == ELEMENT_MOS}      # 켜진 MOS 의 gate 넷(`classes` 는 off 제외)
    bias = {net for net, cls in projection.column("node", "ac_ground_class") if cls == AC_GROUND_GATE_ONLY and net in on_gates}     # 선언 bias(gate 전용 미구동 넷, S1 정본) 중 켜진 소자 VGS 가 전위를 정하는 넷
    only_off = _off_undetermined_nets(off, kinds, pins, dict(projection.column("device", "dc_nets")), set(fixed) | set(inputs) | bias)
    if only_off:      # 전압 결정 넷(고정 넷·입력 포트)에 전도 엣지(`dc_nets`−off−전류원)로 닿지 않는 넷에 off d·g·s 가 닿으면 전위 결정자가 없어 θ 변수가 된다 -- W4 로 두지 않고 정지(물리 관문)
        raise StructureUnresolvedError(devices=tuple(sorted(m for m in off if set(dict(pins[m]).values()) & set(only_off))),
                                       detail={"reason": UNSUPPORTED_RULE_BRANCH, "rule_branch": BRANCH_OFF_ONLY_NODE, "nets": tuple(only_off)})
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
    edges, parallel, facts = _edges(projection, classes, kinds, pins, diode, dcolour, fixed, point, same_gs, coords)
    cyclic = []
    for key, rank, name, a, b in edges:
        ra = _find(parent, _FIXED if a in fixed else canon(a, point))
        rb = _find(parent, _FIXED if b in fixed else canon(b, point))
        is_tree = ra != rb
        groups.setdefault(key, []).append((name, is_tree))
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
        coords[name] = DeviceCoord(COORD_DEPENDENT, DEP_CYCLE)
        cyclic.append((name, a, b))
    for _key, members in sorted(groups.items()):
        decided = {is_tree for _n, is_tree in members}
        if len(decided) > 1:
            ties.append(TieBreak(TIE_KRUSKAL, tuple(sorted(n for n, _t in members)),
                                 tuple(sorted(n for n, t in members if t))))
    for rep, twins in parallel.items():
        for name in twins:
            coords[name] = DeviceCoord(COORD_DEPENDENT, DEP_PARALLEL, rep)
    _confirm_facts(facts, tree, cyclic, parallel, fixed, point)
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

    root_colours = {}

    def root_write(root):
        """F 에 닿지 않는 성분의 뿌리를 쓴다 -- 입력 점이면 뿌리는 p 포트(관계 `input_point`, y 키 = p 포트 넷), 그 밖은 `free_window`(y 키 = 넷).
        뿌리끼리 구조 색이 같으면 처리 순서가 이름이 되므로 정지한다."""
        if point is not None and root in point:
            plan.put(point[0], TIER_W4, REL_INPUT_POINT, None, None, point[0])
            return point[0]
        if ncolour[root] in root_colours:
            _stop_colour_tie((root_colours[ncolour[root]], root))
        root_colours[ncolour[root]] = root
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
                _stop_colour_tie(tied)
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


def _stop_colour_tie(nets):
    raise StructureUnresolvedError(devices=(), detail={"reason": UNSUPPORTED_RULE_BRANCH, "rule_branch": BRANCH_DC_COLOUR_NOT_UNIQUE,
                                                       "nets": tuple(sorted(nets))})


def _edges(projection, classes, kinds, pins, diode, colour, fixed, point, same_gs, coords):
    """(키, 순위, 원소, a, b) 키 순 -- Kruskal 입력. `coords` 에 g = s·둘 다 고정 소자의 `fixed_vgs` 를 쓰고(엣지 없음), 두 번째 반환값 = {평행 대표: 종속 짝 tuple}.
    키는 이름이 없고(저항 `(종류, 0, 색)`), MOS 는 `(종류, 묶임, 하위 키...)` -- 모듈 머리말 3."""
    theta = {m: v.kind for m, v in projection.column("device", "theta_class")}
    orbit = dict(projection.value("graph", GRAPH_KEY, "orbits").devices)
    stage = _stages(dict(projection.column("graph", "views")).get(S1V_KEY, ()))
    facts = {tuple(sorted(subject)): (subject, value) for subject, value, _approval in dict(projection.column("graph", "dependent_facts")).get(S1V_KEY, ())}
    mos = {}
    for name, cls in classes.items():
        if cls == ELEMENT_MOS:
            _d, gate, source = (dict(pins[name])[t] for t in MOS_TERMINAL_NAMES)
            if name in same_gs or (gate in fixed and source in fixed):        # g = s 소자: VGS = 0 으로 고정(좌표 ln_idu 성분 없음)
                coords[name] = DeviceCoord(COORD_DEPENDENT, DEP_FIXED)
            else:
                mos[name] = (gate, source)
    size, first = {}, {}
    for name, o in orbit.items():
        size[o] = size.get(o, 0) + 1
        first[o] = min(first.get(o, colour[name]), colour[name])
    orbit_rep = {m: size[orbit[m]] > 1 and colour[m] == first[orbit[m]] for m in mos}
    gate_of = {}
    for m, (gate, _source) in mos.items():
        gate_of.setdefault(canon(gate, point), set()).add(m)
    downstream = {m: source not in fixed and any(o != m for o in gate_of.get(canon(source, point), ())) for m, (_g, source) in mos.items()}
    strong = {m: theta[m] == THETA_CLASS_S for m in mos}
    late = {m: (m not in stage, -stage.get(m, 0)) for m in mos}          # 뒤 stage 가 앞(독립)
    pairs = {}
    for m, (gate, source) in sorted(mos.items()):
        pairs.setdefault((kinds[m], canon(gate, point), canon(source, point)), []).append(m)
    reps, twins, forced = {}, {}, {}
    for members in pairs.values():
        if len(members) > 1:
            subject = tuple(sorted(members))
            if subject in facts:
                forced[subject] = facts[subject][1]
    for members in pairs.values():
        override = forced.get(tuple(sorted(members)))
        if override is not None and override not in members:
            _stop_fact(F_FACT_MISMATCH, members, subject=tuple(sorted(members)), ratified=override)
        ranked = sorted(members, key=lambda m: (m == override, not diode[m], not strong[m], late[m], not orbit_rep[m], colour[m]))
        reps[ranked[0]] = members
        twins[ranked[0]] = tuple(ranked[1:])
    edges = []
    for name, cls in classes.items():
        if cls == ELEMENT_PASSIVE and kinds[name] == RESISTOR:
            t0, t1 = (net for _t, net in sorted(dict(pins[name]).items()))
            edges.append(((_KIND_RES, 0, (colour[name],)), _RES, name, t0, t1))
    for rep, members in reps.items():
        gate, source = mos[rep]
        pinned = len(members) > 1
        looped = not pinned        # 평행 대표가 아닌 엣지는 고리 안 엣지다(그 비트리 관계가 고리)
        if looped and theta[rep] == THETA_CLASS_B:
            sub = (_LOOP_B, diode[rep], orbit_rep[rep], downstream[rep], -colour[rep])       # 고리 안 B: 앞이 먼저 종속(키가 클수록 비트리)
        else:
            sub = (_PINNED if pinned else _FREE, not diode[rep], not (strong[rep] and not looped), late[rep], not (orbit_rep[rep] and not looped), colour[rep])
        edges.append(((_KIND_MOS,) + sub, _DIODE if diode.get(rep) else _MOS, rep, gate, source))
    for subject, (names, value) in sorted(facts.items()):
        if value not in subject:
            _stop_fact(F_FACT_MISMATCH, subject, subject=names, ratified=value)
    return sorted(edges, key=lambda e: (e[0], e[2])), twins, facts


def _confirm_facts(facts, tree, cyclic, twins, fixed, point):
    """ratified `dependent_member` 사실 대조(Kruskal 뒤): 평행 관계(override, 이미 적용)나 어느 기본 사이클의 멤버와 같은 subject 만 관계가 있다(없으면 orphan).
    고리 사실은 confirm -- 그 기본 사이클의 비트리 엣지(= 유도 종속, 평행 짝은 대표로 본다)가 value 와 다르면 `structure_fact_mismatch`."""
    if not facts:
        return
    parallel = {tuple(sorted((rep,) + group)) for rep, group in twins.items() if group}
    rep_of = {twin: rep for rep, group in twins.items() for twin in group}

    def vertex(net):
        return _FIXED if net in fixed else canon(net, point)

    forest = {}
    for rank, name, a, b in tree:
        forest.setdefault(vertex(a), []).append((vertex(b), name, rank))
        forest.setdefault(vertex(b), []).append((vertex(a), name, rank))
    cycles = {}
    for name, a, b in cyclic:
        previous = {vertex(a): None}
        queue = deque((vertex(a),))
        while queue:
            u = queue.popleft()
            for v, edge, rank in forest.get(u, ()):
                if v not in previous:
                    previous[v] = (u, edge, rank)
                    queue.append(v)
        members, here = [name], vertex(b)
        while previous.get(here) is not None:
            here, edge, rank = previous[here][0], previous[here][1], previous[here][2]
            if rank != _RES:
                members.append(edge)
        cycles[tuple(sorted(members))] = name
    for subject, (names, value) in sorted(facts.items()):
        if subject in cycles:
            if cycles[subject] != rep_of.get(value, value):
                _stop_fact(F_FACT_MISMATCH, subject, subject=names, ratified=value, derived=cycles[subject])
        elif subject not in parallel:
            _stop_fact(F_FACT_ORPHAN, subject, subject=names, ratified=value)


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
