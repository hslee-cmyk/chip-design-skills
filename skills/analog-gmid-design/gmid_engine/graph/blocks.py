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


def _grow(model, ground, cells, drive, owners, members, starts):
    info = {c.dev: c for c in cells.cells}
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


def _outputs(model, members, info, sense):
    readers = {}
    for name, (bid, role) in members.items():
        cell = info[name]
        m = model.mos_by_name[name]
        if cell.kind in (CELL_CS, CELL_CG):
            readers.setdefault(_input_net(m, cell.kind), set()).add(bid)
        if cell.kind == CELL_CS:
            readers.setdefault(m.s, set()).add(bid)
    out = {}
    for name, (bid, role) in members.items():
        cell = info[name]
        if cell.kind not in (CELL_CS, CELL_CG) or role == ROLE_LOAD:
            continue
        net = cell.out
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
    members = _grow(model, ground, cells, drive, owners, members, starts)
    members = {name: (owners.find(bid), role) for name, (bid, role) in members.items()}
    nodes = {owners.find(bid): set() for bid in stage_of}
    for net, bid in owners.owner.items():
        nodes[owners.find(bid)].add(net)
    for bid, nets in owners.shared.items():
        nodes[owners.find(bid)].update(nets)
    outputs = _outputs(model, members, info, sense)
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
    conflicts = tuple((net, tuple(sorted({owners.find(b) for b in ids}))) for net, ids in sorted_items(owners.conflicts))
    return BlocksResult(tuple(blocks), tuple(sorted(nodes)), conflicts, tuple((bid, tuple(sorted(nodes[bid]))) for bid in sorted(nodes)),
                        tuple(findings))
