"""입력 노드 구동 종류 (설계 41 §1.5, 계획 용어집 '입력 노드 구동 종류'·N3.2-5).

진입점: `drive_kinds(model, ground, reach, cells, excite, view_id, ratified) -> DriveResult`.

신호가 넷 n 으로 **들어오는 방식**(진입)을 순방향 셀에서 모은다.
* 진입: 여기 포트(`port`), 신호 gate 를 받는 셀의 drain(CS 의 drain 진입)·source(CS degeneration·공통 소스, CD 출력, diode 의 source)
  진입, CG 의 drain 진입. pass 묶음과 수동소자는 진입이 아니라 **상속** 관계다.
* 규칙 1: drain 진입만이면 전류 구동 후보, source·포트 진입이면 전압 구동.
* 규칙 3(전류 진입 노드): 신호가 나가는 쪽으로 가른다 -- gate 로만 나가면 전압, 채널(CG source·pass)로만 나가면 전류, 둘 다면 gate 쪽
  셀의 출력이 F 위일 때 전압(stage 경계), 아니면 **tap**(전류 구동으로 기록하고 gate 로 갈라진 셀은 규칙 9 (a) `gate_on_current_node`
  기록만). 나가는 곳이 없으면 전류(종단 노드).
* 규칙 4(혼재 = drain 진입과 source·포트 진입이 한 노드에): drain 쪽 소자의 DC 역할이 바이어스 전류원이면 전압, 신호 소자면
  `mixed_drive_signal_drain`(review_needed), 구조로 못 가르는 그룹(S1 dc_role status review_needed)이면 잠정 전압 +
  `mixed_drive_unresolved_group`(review_needed, 열린 항목 ③).
* 규칙 2·5: 저항(DC 를 통하는 수동소자)·pass 묶음으로만 들어오는 넷은 이웃의 종류를 상속한다(저항은 `value_dependent` 표시, pass 는
  아님). 커패시터는 구동 종류를 정하지 않는다.
  상속이 모순이거나 근거가 없는 순환이면 `drive_inherit_cycle`(review_needed).
* ratified 사실(`ratified` = {넷: 종류})이 있으면 그 넷은 그 값을 쓴다(근거 `ratified_fact`).
`mirror_inputs` = diode 연결 단자이고 그 넷을 gate 로 읽는 다른 순방향 셀이 있는 넷(미러 입력, 블록 내부 노드 -- 규칙 9 (c)·⑧).
"""
import dataclasses

from gmid_engine.authoring import DC_CONDUCTING_PASSIVE_KINDS
from gmid_engine.core import sorted_items

from .s1_values import ROLE_BIAS, STATUS_REVIEW_NEEDED
from .s1v_values import (
    BASIS_DRAIN_CHANNEL_EXIT,
    BASIS_DRAIN_GATE_EXIT,
    BASIS_DRAIN_STAGE_BOUNDARY,
    BASIS_DRAIN_TAP,
    BASIS_DRAIN_TERMINAL,
    BASIS_INHERIT_PASS,
    BASIS_INHERIT_PASSIVE,
    BASIS_MIXED_BIAS,
    BASIS_MIXED_SIGNAL,
    BASIS_PORT,
    BASIS_RATIFIED,
    BASIS_SOURCE_ENTRY,
    BASIS_UNDRIVEN,
    CELL_CD,
    CELL_CG,
    CELL_CS,
    CELL_DIODE_LOAD,
    DRIVE_CURRENT,
    DRIVE_VOLTAGE,
    F_DRIVE_CYCLE,
    F_GATE_ON_CURRENT,
    F_MIXED_SIGNAL,
    F_MIXED_UNRESOLVED,
    SEVERITY_REVIEW,
    SEVERITY_UNSUPPORTED,
    DriveInfo,
    Finding,
)


@dataclasses.dataclass(frozen=True)
class DriveResult:
    """`drive` = DriveInfo 넷 이름순, `mirror_inputs` = 미러 입력 넷 정렬 tuple, `findings` = 기록."""

    drive: tuple
    mirror_inputs: tuple
    findings: tuple


def _entries(model, ground, reach, cells, excite):
    """넷 -> {'port': bool, 'drain': [소자], 'source': [소자]} (순방향 셀과 신호 gate 의 diode 에서만)."""
    table = {}

    def at(net):
        return table.setdefault(net, {"port": False, "drain": [], "source": []})

    for net in excite:
        at(net)["port"] = True
    for cell in cells.cells:
        m = model.mos_by_name[cell.dev]
        if cell.kind == CELL_CS and cell.forward:
            at(m.d)["drain"].append(m.name)
            if m.s not in ground:
                at(m.s)["source"].append(m.name)
        elif cell.kind == CELL_CD and cell.forward:
            at(m.s)["source"].append(m.name)
        elif cell.kind == CELL_CG and cell.forward:
            at(m.d)["drain"].append(m.name)
        elif cell.kind == CELL_DIODE_LOAD:
            if m.s not in ground:
                at(m.s)["source"].append(m.name)
            if m.s in reach.signal and m.d in reach.forward and m.name not in at(m.d)["source"]:
                at(m.d)["drain"].append(m.name)
    return table


def _exits(model, cells, net):
    """(gate 로 읽는 순방향 CS·CD, gate 로 읽는 비순방향 셀, 채널로 나가는 순방향 CG 소스·pass)."""
    info = {c.dev: c for c in cells.cells}
    gate_fwd = [m.name for m in model.by_gate.get(net, ())
                if info[m.name].kind in (CELL_CS, CELL_CD) and info[m.name].forward]
    gate_dead = [m.name for m in model.by_gate.get(net, ())
                 if info[m.name].kind in (CELL_CS, CELL_CD) and not info[m.name].forward]
    channel = [m.name for m in model.by_source.get(net, ()) if info[m.name].kind == CELL_CG and info[m.name].forward]
    channel += [name for b in cells.bundles if net in b.nodes for name in b.members]
    return gate_fwd, gate_dead, channel


def _current_split(model, cells, net, view_id):
    gate_fwd, gate_dead, channel = _exits(model, cells, net)
    if gate_fwd and channel:
        return DRIVE_VOLTAGE, False, BASIS_DRAIN_STAGE_BOUNDARY, None
    if gate_fwd:
        return DRIVE_VOLTAGE, False, BASIS_DRAIN_GATE_EXIT, None
    if channel and gate_dead:
        note = Finding(F_GATE_ON_CURRENT, SEVERITY_UNSUPPORTED, view_id, tuple(sorted(gate_dead)) + (net,),
                       "채널 쪽만 순방향을 잇는 tap 노드에서 gate 로 갈라진 셀", ("N3.2-9a", "DEC-59"))
        return DRIVE_CURRENT, True, BASIS_DRAIN_TAP, note
    if channel:
        return DRIVE_CURRENT, False, BASIS_DRAIN_CHANNEL_EXIT, None
    return DRIVE_CURRENT, False, BASIS_DRAIN_TERMINAL, None


def _mixed(model, entry, net, view_id):
    devices = [model.mos_by_name[name] for name in entry["drain"]]
    unresolved = [m.name for m in devices if m.dc_status == STATUS_REVIEW_NEEDED]
    signal = [m.name for m in devices if m.dc_role != ROLE_BIAS and m.dc_status != STATUS_REVIEW_NEEDED]
    if unresolved:
        note = Finding(F_MIXED_UNRESOLVED, SEVERITY_REVIEW, view_id, tuple(sorted(unresolved)) + (net,),
                       "혼재 노드의 drain 쪽 소자가 구조로 못 가르는 DC 역할 그룹이라 잠정 전압 구동", ("N3.2-5", "J12-d"))
        return DRIVE_VOLTAGE, BASIS_MIXED_SIGNAL, note
    if signal:
        note = Finding(F_MIXED_SIGNAL, SEVERITY_REVIEW, view_id, tuple(sorted(signal)) + (net,),
                       "혼재 노드의 drain 쪽이 신호 소자라 구동 종류를 구조로 못 가른다", ("N3.2-5", "J12-d"))
        return DRIVE_VOLTAGE, BASIS_MIXED_SIGNAL, note
    return DRIVE_VOLTAGE, BASIS_MIXED_BIAS, None


def _base_kinds(model, ground, cells, table, ratified, view_id):
    kinds = {}
    findings = []
    for net, entry in sorted_items(table):
        if net in ratified:
            kinds[net] = DriveInfo(net, ratified[net], False, False, BASIS_RATIFIED)
        elif entry["drain"] and (entry["source"] or entry["port"]):
            kind, basis, note = _mixed(model, entry, net, view_id)
            kinds[net] = DriveInfo(net, kind, False, False, basis)
            findings.extend(() if note is None else (note,))
        elif entry["drain"]:
            kind, tap, basis, note = _current_split(model, cells, net, view_id)
            kinds[net] = DriveInfo(net, kind, False, tap, basis)
            findings.extend(() if note is None else (note,))
        else:
            kinds[net] = DriveInfo(net, DRIVE_VOLTAGE, False, False, BASIS_PORT if entry["port"] else BASIS_SOURCE_ENTRY)
    return kinds, findings


def _inherit(model, ground, reach, cells, kinds, view_id):
    """진입 없는 신호 넷이 수동소자·pass 묶음 이웃에서 종류를 물려받는다(고정점)."""
    links = {}
    for p in model.passives:
        if p.kind in DC_CONDUCTING_PASSIVE_KINDS and p.a in reach.signal and p.b in reach.signal:
            links.setdefault(p.a, []).append((p.b, BASIS_INHERIT_PASSIVE))
            links.setdefault(p.b, []).append((p.a, BASIS_INHERIT_PASSIVE))
    for b in cells.bundles:
        links.setdefault(b.nodes[0], []).append((b.nodes[1], BASIS_INHERIT_PASS))
        links.setdefault(b.nodes[1], []).append((b.nodes[0], BASIS_INHERIT_PASS))
    findings = []
    pending = sorted(net for net in reach.forward if net not in kinds)
    progressed = True
    while pending and progressed:
        progressed = False
        for net in tuple(pending):
            donors = sorted((nbr, basis) for nbr, basis in links.get(net, ()) if nbr in kinds)
            if not donors:
                continue
            values = {kinds[nbr].kind for nbr, _ in donors}
            if len(values) > 1:
                findings.append(Finding(F_DRIVE_CYCLE, SEVERITY_REVIEW, view_id, tuple(sorted({net, *(n for n, _ in donors)})),
                                        "수동소자·pass 이웃의 구동 종류가 서로 달라 상속이 모순이다", ("N3.2-5", "DEC-63")))
            nbr, basis = donors[0]
            kinds[net] = DriveInfo(net, kinds[nbr].kind, basis == BASIS_INHERIT_PASSIVE, False, basis)
            pending.remove(net)
            progressed = True
    for net in pending:
        findings.append(Finding(F_DRIVE_CYCLE, SEVERITY_REVIEW, view_id, (net,),
                                "신호가 들어오는 근거가 없고 이웃에서 상속할 종류도 없다", ("N3.2-5",)))
        kinds[net] = DriveInfo(net, DRIVE_CURRENT, False, False, BASIS_UNDRIVEN)
    return findings


def _mirror_inputs(model, cells):
    info = {c.dev: c for c in cells.cells}
    return tuple(sorted(
        net for net in model.diode_nodes
        if any(m.g == net and m.d != net and info[m.name].kind in (CELL_CS, CELL_CD) and info[m.name].forward
               for m in model.by_gate.get(net, ()))))


def drive_kinds(model, ground, reach, cells, excite, view_id, ratified):
    table = _entries(model, ground, reach, cells, excite)
    kinds, findings = _base_kinds(model, ground, cells, table, dict(ratified), view_id)
    findings.extend(_inherit(model, ground, reach, cells, kinds, view_id))
    return DriveResult(tuple(kinds[net] for net in sorted(kinds)), _mirror_inputs(model, cells), tuple(findings))
