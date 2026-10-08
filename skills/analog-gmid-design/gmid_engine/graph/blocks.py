"""이득 블록 구성 (설계 41 §1.7 1~3, 계획 N3.2-6 '출력노드 = stage 안에서 신호가 마지막으로 도달해 ...').

진입점: `build_blocks(model, ground, cells, drive, stage, impedance, sense, view_id) -> BlocksResult`. `ground` 는 진짜 교류접지(정적·여기
밖 입력·바이어스 종속)이고, 대칭 가상접지 넷은 접지가 아니라 소유 가능한 side 노드다(공통 소스를 공유하는 두 반쪽이 한 차동 블록으로 합쳐진다).

stage 시작 셀(`stage_bfs`)마다 블록 하나를 열고 **소유 관계**를 고정점으로 넓힌다:
* 시작 셀: 출력 넷(CS·CG = drain)과 CS 의 source(degeneration·공통 소스) 넷을 소유한다.
* 시작이 아닌 순방향 CS·CG 는 입력 넷(CS = gate, CG = source)을 소유한 블록의 멤버가 되고, 자기 출력 넷과 source 넷을 같은 블록이 소유한다 --
  캐스코드 사슬(CG)·미러 연장(미러 입력 노드를 gate 로 읽는 CS)이 이렇게 한 블록으로 이어진다. diode 소자(소유한 노드)·pass 묶음도 따라온다.
* 같은 넷을 두 블록이 소유하면: **stage 번호가 같으면 합친다**(차동 블록 ⑩: 반쪽 둘이 공통 소스·출력을 공유, 병렬 셀 ①). stage 가 다르면 합치지
  않고 `conflicts` 에 남긴다 -- 합류 노드가 출력노드면 복합 블록(`composite_blocks`, DEC-81), 아니면 노드 배타 위반.
블록 = (멤버 소자와 AC 역할, 소유 넷 + 입력 넷 = 노드 집합, 출력노드 = 멤버 CS·CG 의 출력 중 같은 블록 멤버가 입력으로 다시 읽지 않는 넷(감지 넷이면
항상), 입력 = 시작 셀의 입력 넷). 블록 키 = 출력노드 이름 정렬 tuple(JSON 에서는 배열, 40·41 §1.7-3).
소자 역할: input(시작 CS·CG), cascode(CG), mirror(미러 입력을 gate 로 읽는 CS), diode_load(소유 노드의 diode 소자), pass, tail(DC 역할이
바이어스 전류원이고 drain 이 블록 안 둘 이상 멤버 source 인 소자), load(그 밖에 블록 소유 노드에 단자가 닿는 MOS·수동소자).
복합 diode 묶음(41 §1.12.1)의 MOS 멤버는 묶음의 gate 넷(미러 입력)을 소유한 블록의 `diode_load` 멤버이고(`_composite_members`) 소유 넷은 늘리지 않는다 -- 묶음 내부 넷까지 소유하면 그 gate 를 읽는
측면 주입 미러 출력(K8)이 블록으로 딸려 들어온다. feedforward 묶음 소자는 호출자가 모형에서 뺀 뒤 부른다(`view_analysis`, 41 §1.12.2).
복합 diode 묶음 내부 gate 넷을 읽는 셀은 진입 넷 소유 블록으로 이어진다(`_owner_of`; 미러 출력이 낮은 임피던스 노드로 들어가면 K8 이라 이어지지 않는다). 다른 stage 블록이 겹친 넷을 한 블록 멤버가 입력으로 읽으면 내부 노드 측면 주입(K8)이라 읽는 블록에 합친다(`_absorb_side_injections`).
규칙 9 (c): 출력노드 임피던스 등급이 낮으면 `cs_output_low_impedance`(기록만, 항상 DEC-59 정지) -- 순방향 위 출력노드에만 건다.
"""
import dataclasses

from gmid_engine.core import sorted_items

from .s1_values import ROLE_BIAS, STATUS_DERIVED
from .s1v_values import (
    CELL_CG,
    CELL_CS,
    CELL_DIODE_LOAD,
    CELL_PASS,
    F_CS_LOW_IMPEDANCE,
    IMP_LOW,
    ROLE_CASCODE,
    ROLE_DIODE_LOAD,
    ROLE_INPUT,
    ROLE_LOAD,
    ROLE_MIRROR,
    ROLE_PASS,
    ROLE_TAIL,
    SEVERITY_UNSUPPORTED,
    BLOCK_GAIN,
    Block,
    Finding,
)


@dataclasses.dataclass(frozen=True)
class BlocksResult:
    """`blocks` = 블록 id 순 Block, `ids` = 같은 순서의 블록 id(키가 같은 블록이 둘 이상일 수 있다 -- 복합 블록 후보), `conflicts` = 서로
    다른 stage 블록이 공유한 넷 ((넷, (블록 id, ...)), ...), `owned` = ((블록 id, 소유 넷 tuple), ...), `findings` = 기록. 블록 id = 시작 셀 이름 중 이름순 첫째. stage = 시작 셀 입력 넷의 `stage_dist` + 1(출력 거리의 최소값은 다른 경로에 끌려가므로 쓰지 않는다)."""

    blocks: tuple
    ids: tuple
    conflicts: tuple
    owned: tuple
    findings: tuple


class _Owners:
    """블록 id 합병(union-find)과 소유 표. 이 파일 안에서만 쓴다."""

    def __init__(self, stage_of):
        self.parent = {bid: bid for bid in stage_of}
        self.stage_of = stage_of
        self.owner = {}
        self.shared = {}
        self.conflicts = {}

    def find(self, bid):
        while self.parent[bid] != bid:
            self.parent[bid] = self.parent[self.parent[bid]]
            bid = self.parent[bid]
        return bid

    def union(self, a, b):
        ra, rb = self.find(a), self.find(b)
        if ra != rb:
            keep, drop = sorted((ra, rb))
            self.parent[drop] = keep
            self.stage_of[keep] = min(self.stage_of[keep], self.stage_of[drop])
        return True

    def claim(self, net, bid):
        """넷을 블록이 소유하게 한다. 새로 소유하거나 합병이 일어나면 True."""
        current = self.owner.get(net)
        if current is None:
            self.owner[net] = bid
            return True
        if self.find(current) == self.find(bid):
            return False
        if self.stage_of[self.find(current)] == self.stage_of[self.find(bid)]:
            return self.union(current, bid)
        self.conflicts.setdefault(net, set()).update((self.find(current), self.find(bid)))
        self.shared.setdefault(bid, set()).add(net)
        return False


def _input_net(m, kind):
    return m.g if kind == CELL_CS else m.s


def _bundle_gates(model):
    """복합 diode 묶음마다 그 MOS 멤버의 gate 넷 집합 -- 묶음 내부 넷(미러 입력)을 읽는 셀의 소유 블록을 묶음 진입 넷의 소유자로 풀기 위한 표."""
    return tuple(frozenset(model.mos_by_name[name].g for name in sorted(bundle) if name in model.mos_by_name)
                 for bundle in model.composite_bundles)


def _owner_of(net, owners, gates):
    """넷을 소유한 블록 id. 소유자가 없는 복합 diode 묶음 gate 넷이면 같은 묶음의 다른 gate 넷(진입 넷) 소유자 -- 블록이 미러 출력 쪽으로 이어진다(41 §1.12.1-2)."""
    bid = owners.owner.get(net)
    if bid is None:
        for nets in gates:
            if net in nets:
                bid = next((owners.owner[n] for n in sorted(nets) if n in owners.owner), None)
                if bid is not None:
                    break
    return bid


def _grow(model, ground, cells, drive, owners, members, starts, impedance):
    info = {c.dev: c for c in cells.cells}
    gates = _bundle_gates(model)
    changed = True
    while changed:
        changed = False
        for m in model.mos:
            cell = info[m.name]
            if m.name in members:
                continue
            if cell.kind in (CELL_CS, CELL_CG) and cell.forward and m.name not in starts:
                bid = owners.owner.get(_input_net(m, cell.kind))
                if bid is None:
                    bid = _owner_of(_input_net(m, cell.kind), owners, gates)
                    if bid is not None and cell.kind == CELL_CS and impedance.get(m.d) == IMP_LOW:
                        bid = None         # 묶음 내부 넷을 읽는 미러 출력이 다른 셀이 구동하는 낮은 임피던스 노드(예 팔로워 출력)로 들어가면 측면 주입(K8)이다 -- 블록이 그쪽으로 이어지지 않는다
                if bid is None:
                    continue
                role = ROLE_CASCODE if cell.kind == CELL_CG else (
                    ROLE_MIRROR if m.g in drive.mirror_inputs else ROLE_LOAD)
                members[m.name] = (bid, role)
                owners.claim(m.d, bid)
                if m.s not in ground:
                    owners.claim(m.s, bid)
                changed = True
            elif cell.kind == CELL_DIODE_LOAD and m.d in owners.owner:
                members[m.name] = (owners.owner[m.d], ROLE_DIODE_LOAD)
                if m.s not in ground:
                    owners.claim(m.s, owners.owner[m.d])
                changed = True
        for bundle in cells.bundles:
            first, second = bundle.nodes
            for src, dst in ((first, second), (second, first)):
                if src in owners.owner and bundle.members[0] not in members:
                    for name in bundle.members:
                        members[name] = (owners.owner[src], ROLE_PASS)
                    owners.claim(dst, owners.owner[src])
                    changed = True
    return members


def _absorb_side_injections(owners, members, info, model):
    """측면 주입(K8, 41 §1.12.2-2): 다른 stage 블록이 소유를 겹친 넷을 한 블록의 멤버(CS gate·CG source)가 입력으로 읽으면 그 넷은 읽는 블록의 **내부 노드**다. 겹친
    블록은 그 내부 노드로 전류를 주입하는 쪽이므로 읽는 블록에 합쳐지고 읽는 블록의 stage 를 유지한다(복합 블록 합류는 출력노드에서만 -- `composite_blocks`)."""
    readers = {}
    for name, (bid, _) in members.items():
        cell = info[name]
        if cell.kind in (CELL_CS, CELL_CG):
            readers.setdefault(_input_net(model.mos_by_name[name], cell.kind), set()).add(owners.find(bid))
    for net, ids in sorted_items(owners.conflicts):
        roots = {owners.find(b) for b in ids}
        inner = sorted(roots & readers.get(net, set()))
        if len(roots) == 1 or len(inner) != 1:
            continue
        keep = inner[0]
        stage = owners.stage_of[keep]
        for other in sorted(roots - {keep}):
            owners.union(keep, other)
        owners.stage_of[owners.find(keep)] = stage
    return members


def _composite_members(model, owners, members):
    """복합 diode 묶음(41 §1.12.1)의 MOS 멤버는 묶음의 gate 넷(미러 입력)을 소유한 블록의 `diode_load` 멤버다. 소유 넷은 늘리지 않는다 -- 묶음 내부 넷이 블록 노드로 들어오면
    그 gate 를 읽는 미러 출력(측면 주입 K8 포함)까지 따라 들어오기 때문이다."""
    for bundle in model.composite_bundles:
        mos = [model.mos_by_name[name] for name in sorted(bundle) if name in model.mos_by_name]
        anchor = next((owners.owner[m.g] for m in mos if m.g in owners.owner), None)
        for m in mos:
            if anchor is not None and m.name not in members:
                members[m.name] = (anchor, ROLE_DIODE_LOAD)
    return members


def _through_pass(net, bid, members, bundles, inputs):
    """출력 후보 넷이 같은 블록 pass 묶음의 한 끝이면 반대 끝으로 따라간다(41 §1.7-1, 계획 N3.2-6 'CD·pass 로 끝나면 그 소자의 출력 단자
    노드'). 입력 넷이거나 이미 지난 넷으로 되돌아가지는 않는다."""
    seen = {net}
    moved = True
    while moved:
        moved = False
        for bundle in bundles:
            if net not in bundle.nodes or any(members.get(n, (None, None))[0] != bid for n in bundle.members):
                continue
            other = bundle.nodes[1] if bundle.nodes[0] == net else bundle.nodes[0]
            if other not in seen and other not in inputs:
                seen.add(other)
                net = other
                moved = True
                break
    return net


def _outputs(model, members, info, sense, bundles):
    readers = {}
    for name, (bid, role) in members.items():
        cell = info[name]
        m = model.mos_by_name[name]
        if cell.kind in (CELL_CS, CELL_CG):
            readers.setdefault(_input_net(m, cell.kind), set()).add(bid)
        if cell.kind == CELL_CS:
            readers.setdefault(m.s, set()).add(bid)
    inputs = set(readers)
    for nets in _bundle_gates(model):          # 복합 diode 묶음의 gate 넷 하나를 블록 멤버가 읽으면 묶음 전체(진입 넷 포함)가 그 블록 안으로 이어진 내부 노드다
        reading = set().union(*(readers.get(n, ()) for n in nets))
        for net in nets:
            readers.setdefault(net, set()).update(reading)
    out = {}
    for name, (bid, role) in members.items():
        cell = info[name]
        if cell.kind not in (CELL_CS, CELL_CG) or role == ROLE_LOAD:
            continue
        net = _through_pass(cell.out, bid, members, bundles, inputs - {cell.out})
        read_by_same = any(owners_root == bid for owners_root in readers.get(net, ()))
        if net in sense or not read_by_same:
            out.setdefault(bid, set()).add(net)
    return out


def _attach(model, ground, members, info, nodes):
    """블록 소유 노드에 단자가 닿는 비멤버 MOS·수동소자의 역할(tail·load)."""
    extra = {}
    source_count = {}
    for name, (bid, _) in members.items():
        cell = info[name]
        if cell.kind in (CELL_CS, CELL_CG):
            net = model.mos_by_name[name].s
            source_count[(bid, net)] = source_count.get((bid, net), 0) + 1
    for m in model.mos:
        if m.name in members:
            continue
        for bid, owned in nodes.items():
            touches = (m.d in owned) or (m.s in owned and m.s not in ground)
            if not touches:
                continue
            is_tail = m.dc_role == ROLE_BIAS and source_count.get((bid, m.d), 0) > 1
            extra.setdefault(bid, {})[m.name] = ROLE_TAIL if is_tail else ROLE_LOAD
    for p in model.passives:
        for bid, owned in nodes.items():
            if p.a in owned or p.b in owned:
                extra.setdefault(bid, {})[p.name] = ROLE_LOAD
    return extra


def build_blocks(model, ground, cells, drive, stage, impedance, sense, view_id):
    info = {c.dev: c for c in cells.cells}
    stage_dist = dict(stage.stage_dist)
    starts = frozenset(stage.starts)
    stage_of = {name: stage_dist.get(_input_net(model.mos_by_name[name], info[name].kind), 0) + 1 for name in starts}
    owners = _Owners(stage_of)
    members = {}
    for name in sorted(starts):
        m = model.mos_by_name[name]
        members[name] = (name, ROLE_INPUT)
        owners.claim(m.d, name)
        if info[name].kind == CELL_CS and m.s not in ground:
            owners.claim(m.s, name)
    members = _grow(model, ground, cells, drive, owners, members, starts, impedance)
    members = _absorb_side_injections(owners, members, info, model)
    members = _composite_members(model, owners, members)
    members = {name: (owners.find(bid), role) for name, (bid, role) in members.items()}
    nodes = {owners.find(bid): set() for bid in stage_of}
    for net, bid in owners.owner.items():
        nodes[owners.find(bid)].add(net)
    for bid, nets in owners.shared.items():
        nodes[owners.find(bid)].update(nets)
    outputs = _outputs(model, members, info, sense, cells.bundles)
    extra = _attach(model, ground, members, info, nodes)
    blocks = []
    findings = []
    for bid in sorted(nodes):
        roles = {name: role for name, (b, role) in members.items() if b == bid}
        roles.update(extra.get(bid, {}))
        inputs = sorted({_input_net(model.mos_by_name[n], info[n].kind) for n in starts if members[n][0] == bid})
        outs = tuple(sorted(outputs.get(bid, ())))
        table = tuple((net, impedance[net]) for net in outs if net in impedance)
        for net, level in table:
            if level == IMP_LOW:
                findings.append(Finding(F_CS_LOW_IMPEDANCE, SEVERITY_UNSUPPORTED, view_id, (net,),
                                        "이득 블록 출력노드의 임피던스 등급이 낮다(CS 버퍼·종단 diode 부하)", ("N3.2-9c", "DEC-59")))
        blocks.append(Block(outs, BLOCK_GAIN, owners.stage_of[bid], tuple(inputs), outs,
                            sorted_items(roles), tuple(sorted(nodes[bid] | set(inputs))), table, STATUS_DERIVED))
    roots = tuple((net, tuple(sorted({owners.find(b) for b in ids}))) for net, ids in sorted_items(owners.conflicts))
    conflicts = tuple((net, ids) for net, ids in roots if len(ids) > 1)     # 측면 주입 합치기(`_absorb_side_injections`) 뒤 한 블록으로 모인 겹침은 최종 블록 집합에서 겹침이 아니다
    return BlocksResult(tuple(blocks), tuple(sorted(nodes)), conflicts, tuple((bid, tuple(sorted(nodes[bid]))) for bid in sorted(nodes)),
                        tuple(findings))
