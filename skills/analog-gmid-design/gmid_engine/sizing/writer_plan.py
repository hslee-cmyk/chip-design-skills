"""쓰기 계획 컴파일 -- 노드마다 writer 하나, MOS 마다 좌표 역할(쓰기/종속) (설계 3.1 1~3, 계획 N3.4·DEC-64·DEC-95 (3)).

진입점: `dc_writer_plan`(`@compute_block`) -- `dc_writer_plan(snapshot, target_nets, input_dc_declared)`. θ 무관(S0 당 1회).

1. 고정 노드 F = 레일(W0) ∪ spec 노드 목표(W3) ∪ (입력 DC 가 선언되면) 입력 포트(W2 (d)). 우선순위 W0 > W3 > W2.
2. G_vgs(용어집) = MOS (gate, source) 엣지 + 저항 (t0, t1) 엣지(잎 가지치기된 저항 포함 -- 전류 0 이라 강하 0)
   + 입력 DC 가 선언되지 않은 입력 포트끼리의 '같은 DC' 엣지(DEC-64 v1 '입력 DC 동일 가정', U2 기본안 (a)).
3. F 를 한 점으로 묶은 G_vgs 의 최소 신장 숲(Kruskal). 엣지 순위 = (같은 DC 엣지, 저항, diode MOS, 그 밖 MOS) 다음 원소
   이름(결정론 tie-break). 신장 숲의 순환 성질상 각 기본 사이클에서 순위가 가장 낮은(비 diode·이름 뒤) 엣지가 비트리가
   된다 = DEC-95 (3) 구조 우선순위의 앞 두 단계(ratified 선택·diode 독립). 'GB5 gm 요구·뒤 stage·대칭 궤도' 단계는 그
   정보를 내는 S1v/GB5 가 아직 없어 적용하지 않는다(CONTRACT 열린 질문).
4. 트리 엣지 = writer: F 와 각 성분 뿌리에서 BFS 로 먼 쪽 노드를 쓴다. MOS 가 source 에서 gate 를 쓰면 `vgs_gate`
   (diode 면 W1), gate 에서 source 를 쓰면 `vgs_source`(W2), 저항은 `resistor_drop`(W2), 같은 DC 엣지는 `input_tie`(W2).
5. F 가 없는 성분의 뿌리 = 그 성분의 입력 포트(있으면, 이름순 첫 것, y 키 `input_common_mode`) 아니면 이름순 첫 노드
   (y 키 = 넷) -- W4. G_vgs 에 없는 노드(채널 drain·이상원 단자만 닿는 노드) = W4(y 키 = 넷).
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
    TIER_W0,
    TIER_W1,
    TIER_W2,
    TIER_W3,
    TIER_W4,
    DeviceCoord,
    NodeWrite,
)

READS = (
    ("device", "element_class"), ("device", "is_diode"), ("device", "kind"), ("device", "pins"),
    ("node", "is_rail"), ("node", "port_direction"),
)
WRITES = (("node", "dc_writer"), ("device", "dc_coord"))
_FIXED = ("",)                                          # F 한 점(넷 이름이 될 수 없는 tuple 키)
_TIE, _RES, _DIODE, _MOS = (0, 1, 1 + 1, 1 + 1 + 1)    # 엣지 순위


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


def _edges(classes, kinds, pins, diode, free_inputs):
    edges = []
    for i, (a, b) in enumerate(zip(free_inputs, free_inputs[1:])):
        edges.append(((_TIE, i, ""), _TIE, None, a, b))
    for name, cls in classes.items():
        p = dict(pins[name])
        if cls == ELEMENT_PASSIVE and kinds[name] == RESISTOR:
            t0, t1 = (net for _t, net in sorted(p.items()))
            edges.append(((_RES, 0, name), _RES, name, t0, t1))
        elif cls == ELEMENT_MOS:
            _d, gate, source = (p[t] for t in MOS_TERMINAL_NAMES)
            rank = _DIODE if diode.get(name) else _MOS
            edges.append(((rank, 0, name), rank, name, gate, source))
    return sorted(edges)


@compute_block(DC_WRITER_PLAN_WRITER, reads=READS, writes=WRITES)
def dc_writer_plan(projection):
    target_nets, input_dc_declared = projection.extras
    classes = dict(projection.column("device", "element_class"))
    kinds = dict(projection.column("device", "kind"))
    pins = dict(projection.column("device", "pins"))
    diode = dict(projection.column("device", "is_diode"))
    nodes = tuple(net for net, _r in projection.column("node", "is_rail"))
    rails = tuple(net for net, is_rail in projection.column("node", "is_rail") if is_rail)
    inputs = tuple(net for net, d in projection.column("node", "port_direction") if d == INPUT_DIRECTION)
    plan = _Plan()
    fixed = {}
    for net in rails:
        fixed[net] = (TIER_W0, REL_RAIL)
    for net in target_nets:
        fixed.setdefault(net, (TIER_W3, REL_TARGET))
    if input_dc_declared:
        for net in inputs:
            fixed.setdefault(net, (TIER_W2, REL_INPUT_DC))
    for net in sorted(fixed):
        plan.put(net, *fixed[net])
    free_inputs = tuple(net for net in inputs if net not in fixed)
    parent = {}
    tree = []
    coords = {}
    for _key, rank, name, a, b in _edges(classes, kinds, pins, diode, free_inputs):
        ra = _find(parent, _FIXED if a in fixed else a)
        rb = _find(parent, _FIXED if b in fixed else b)
        if ra != rb:
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
    adjacency = {}
    for edge in tree:
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

    walk(sorted(fixed))
    for net in sorted(adjacency):
        if net in plan.writes:
            continue
        component = _component(adjacency, net)
        ports = sorted(n for n in component if n in free_inputs)
        root = ports[0] if ports else min(component)
        plan.put(root, TIER_W4, REL_WINDOW, None, None, INPUT_GROUP_KEY if ports else root)
        walk((root,))
    for net in nodes:
        if net not in plan.writes:
            plan.put(net, TIER_W4, REL_WINDOW, None, None, net)
    return {("node", "dc_writer"): plan.writes, ("device", "dc_coord"): coords}


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
