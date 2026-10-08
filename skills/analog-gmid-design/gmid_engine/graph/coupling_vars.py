"""GB3 결합 변수 y (설계 40 §3.3, 계획 DEC-71 (2)(7), N3.7 결합 표, 41 §5.5 조립의 입력).

진입점: `coupling_vars(s1, s1v) -> Coupling`  (`Coupling(vars, column_block_map)`; 매핑표는 `column_block_map` 가 만들고 여기서 같이 돌려준다).

블록 경계를 넘는 관계를 S1 관계 엣지·S1v 블록·기둥↔블록 매핑표를 대조해 `CouplingVar` 로 모은다. '블록 경계를 넘는다'는 **한 뷰 안에서** 관계에 든 소자들의 블록이 서로 다르다는 뜻이다
(`_crosses`: 그 뷰에 블록이 있는 소자가 둘 이상이고 그 소자들의 블록 키 합집합이 교집합과 다를 때) -- 같은 키 블록도 뷰가 다르면 다른 블록이라 `BlockRef` 가 뷰 id 를 가진다.
블록을 갖지 않은 소자의 블록은 매핑표의 기둥 이웃 귀속(`column_mate`)을 쓴다.

* K1: S1 mirror matching 그룹 또는 S1v L 동치류의 멤버 중 부하 소자(블록 AC 역할 load·mirror·diode_load)가 있고 그 류가 블록을 가로지른다. 영역 dc(mirror)·geom(L 동치류).
* K2: S1 `equal_vgs` 관계 엣지가 블록을 가로지른다(공유 VGS). 영역 dc.
* K3: 비레일 넷에서 MOS e 의 drain 과 MOS d 의 source 가 만나고(d 의 vsb 가 e 가 정한 노드전압에 종속 = `stacked_vsb`) 둘의 블록이 다르다. members = (e, d), nets = (그 넷). 영역 dc.
* K4: 한 가지(S1 branch)가 지나가는 기둥들의 소자가 블록을 가로지른다(블록이 공유하는 가지·기둥의 노드전압). members = 가지의 소자, nets = 가지 양 끝. 영역 dc.
* K7: 소자가 둘 이상 뷰의 블록 멤버다(블록 멤버 행 기준). 영역 dc.
* K8: 셀 c 의 DC 역할이 바이어스 전류원이고 AC 셀이 gate 로 신호를 받는 CS 이며, drain 노드 k 에 신호 CD 셀의 source 가 붙고, c 의 gate 가 그 CD 입력 넷에서 CD 엣지로 닿지
  않고, k 가 이득 블록의 출력노드가 아니다(40 §3.3 K8 정의). members = (c, 그 CD 셀들), nets = (k). 영역 dc.

결과 `vars` 는 (kind, members, nets, domain) 순 정렬이고 같은 (kind, members, nets, domain)은 한 번만 낸다. 호출자: 파이프라인 단계 A4(`run_stage_a`, 보고서 `coupling` 키).
소비자는 U15 층 0 조립(41 §5.5)이다.
"""
from .column_block_map import column_block_map
from .coupling_values import (
    BASIS_BLOCK_MEMBER,
    INIT_CLASS_OWNER,
    INIT_COMMON_VGS,
    INIT_SHARED_NODE,
    INIT_SIDE_INJECTION,
    INIT_STACK_KVL,
    INIT_VIEW_SPLIT,
    KIND_K1,
    KIND_K2,
    KIND_K3,
    KIND_K4,
    KIND_K7,
    KIND_K8,
    BlockRef,
    Coupling,
    CouplingVar,
)
from .net_model import net_model
from .s1_values import DOMAIN_DC, DOMAIN_GEOM, GRAPH_KEY, MATCH_MIRROR, REL_EQUAL_VGS, ROLE_BIAS
from .s1v_values import BLOCK_GAIN, CELL_CD, CELL_CS, ROLE_DIODE_LOAD, ROLE_LOAD, ROLE_MIRROR

LOAD_ROLES = (ROLE_LOAD, ROLE_MIRROR, ROLE_DIODE_LOAD)


def _keys_by_view(cbm):
    """{소자: {뷰 id: 블록 키 frozenset}} -- 매핑표의 블록 귀속(멤버 + 기둥 이웃)."""
    table = {}
    for row in cbm.rows:
        if row.block is not None:
            table.setdefault(row.device, {}).setdefault(row.block.view, set()).add(row.block.key)
    return table


def _crosses(members, keys_by_view):
    """members 가 블록을 가로지르는 뷰들의 BlockRef 정렬 tuple(없으면 빈 tuple)."""
    per_view = {}
    for name in members:
        for view, keys in keys_by_view.get(name, {}).items():
            per_view.setdefault(view, []).append(keys)
    refs = []
    for view, groups in per_view.items():
        if len(groups) > 1 and frozenset().union(*groups) != frozenset.intersection(*map(frozenset, groups)):
            refs.extend(BlockRef(view, key) for key in frozenset().union(*groups))
    return tuple(sorted(refs))


def _roles(s1v):
    return {(name, BlockRef(view.id, block.key)): role for view in s1v.views for block in view.blocks for name, role in block.roles}


def _classes(s1, s1v):
    """K1 후보 류: (members, domain) -- mirror matching 그룹(dc)과 L 동치류(geom)."""
    mirrors = tuple((g.members, DOMAIN_DC) for g in s1.value("graph", GRAPH_KEY, "matching_groups") if g.kind == MATCH_MIRROR)
    return mirrors + tuple((c.members, DOMAIN_GEOM) for c in s1v.l_classes)


def _k1_k2(s1, s1v, keys, roles):
    out = []
    for members, domain in _classes(s1, s1v):
        refs = _crosses(members, keys)
        if refs and any(roles.get((name, ref)) in LOAD_ROLES for name in members for ref in refs):
            out.append(CouplingVar(KIND_K1, tuple(members), refs, domain, INIT_CLASS_OWNER))
    for edge in s1.value("graph", GRAPH_KEY, "rel_equal_vgs"):
        refs = _crosses(edge.members, keys)
        if refs:
            out.append(CouplingVar(KIND_K2, tuple(edge.members), refs, edge.domain, INIT_COMMON_VGS, tuple(edge.evidence.nets)))
    return out


def _k3(model, keys):
    out = []
    for e in model.mos:
        if e.d in model.rails:
            continue
        for d in model.by_source.get(e.d, ()):
            refs = _crosses((e.name, d.name), keys) if d.name != e.name else ()
            if refs:
                out.append(CouplingVar(KIND_K3, (e.name, d.name), refs, DOMAIN_DC, INIT_STACK_KVL, (e.d,)))
    return out


def _k4(s1, keys):
    branches = {b.id: b for b in s1.value("graph", GRAPH_KEY, "branches")}
    members_of = {bid: tuple(sorted({e for seg in b.segments for e in seg.elements})) for bid, b in branches.items()}
    through = {}
    for column in s1.value("graph", GRAPH_KEY, "columns"):
        devices = {name for bid in column.branch_order for name in members_of[bid]}
        for bid in column.branch_order:
            through.setdefault(bid, set()).update(devices)
    out = []
    for bid, devices in sorted(through.items()):
        refs = _crosses(sorted(devices), keys)
        if refs:
            out.append(CouplingVar(KIND_K4, members_of[bid], refs, DOMAIN_DC, INIT_SHARED_NODE, tuple(sorted(branches[bid].ends))))
    return out


def _k7(cbm):
    refs = {}
    for row in cbm.rows:
        if row.basis == BASIS_BLOCK_MEMBER:
            refs.setdefault(row.device, set()).add(row.block)
    return [CouplingVar(KIND_K7, (name,), tuple(sorted(found)), DOMAIN_DC, INIT_VIEW_SPLIT)
            for name, found in sorted(refs.items()) if len({ref.view for ref in found}) > 1]


def _cd_reach(cds, model, start):
    """start 넷에서 신호 CD 셀(gate -> source)을 따라 닿는 넷 집합."""
    edges = {}
    for cell in cds:
        edges.setdefault(model.mos_by_name[cell.dev].g, []).append(cell.out)
    seen = {start}
    todo = [start]
    while todo:
        for net in edges.get(todo.pop(), ()):
            if net not in seen:
                seen.add(net)
                todo.append(net)
    return seen


def _k8(model, s1v, keys):
    out = []
    for view in s1v.views:
        gain_outputs = {net for b in view.blocks if b.kind == BLOCK_GAIN for net in b.outputs}
        cds = tuple(c for c in view.cells if c.kind == CELL_CD)
        for cell in view.cells:
            c = model.mos_by_name[cell.dev]
            if cell.kind != CELL_CS or c.dc_role != ROLE_BIAS or c.g not in view.signal_nets or c.d in gain_outputs:
                continue
            injected = tuple(sorted(x.dev for x in cds if x.out == c.d and c.g not in _cd_reach(cds, model, model.mos_by_name[x.dev].g)))
            if injected:
                members = (c.name,) + injected
                refs = tuple(sorted({BlockRef(v, k) for name in members for v, found in keys.get(name, {}).items() for k in found}))
                out.append(CouplingVar(KIND_K8, members, refs, DOMAIN_DC, INIT_SIDE_INJECTION, (c.d,)))
    return out


def coupling_vars(s1, s1v):
    cbm = column_block_map(s1, s1v)
    model = net_model(s1)
    keys = _keys_by_view(cbm)
    found = _k1_k2(s1, s1v, keys, _roles(s1v)) + _k3(model, keys) + _k4(s1, keys) + _k7(cbm) + _k8(model, s1v, keys)
    unique = {(v.kind, v.members, v.nets, v.domain): v for v in found}
    return Coupling(tuple(unique[k] for k in sorted(unique)), cbm)
