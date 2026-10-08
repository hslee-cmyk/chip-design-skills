"""follower 묶음 R(u)와 버퍼 블록 (설계 41 §1.9, 계획 DEC-63).

진입점: `buffer_bundles(model, ground, cells, stage, impedance, view_id) -> BuffersResult`.

전압 구동 넷 u(입력 포트 또는 이득 블록 출력노드 -- CD 셀의 출력이 아닌 CD gate 넷)에서 **CD 셀의 입력(gate)->출력(source) 엣지만** 따라 도달하는
노드 집합 R(u)를 모은다. gate 가 신호 경로 밖인 pass 셀은 넣지 않고(pass 구간은 뒤 이득 블록이 흡수하거나 기록만), CS·CG 를 만나면 묶음이
끝난다(그 셀은 새 이득 블록을 연다).
* R(u) 안에서 더 이상 CD 입력으로 쓰이지 않는 노드(싱크)가 정확히 하나(합류 노드 v)면 버퍼 블록 = {입력 u, 노드 R(u), 출력노드 v} -- `Block`
  (kind buffer, 역할 follower). 상보 CD 합류·CD 사슬이 한 블록이 된다.
* 싱크가 둘 이상이면 다출력 버퍼로 `buffer_multi_output`(기록만, DEC-59 정지).
버퍼 블록은 gain stage 번호를 올리지 않는다: stage = u 의 `stage_dist`(없으면 0). 출력노드 임피던스 등급은 `node_impedance` 표에서 읽는다(싱크는 CD 의 source 라
낮음). 규칙 9 (c)는 이득 블록에만 적용한다.
"""
import dataclasses

from .s1_values import STATUS_DERIVED
from .s1v_values import (
    BLOCK_BUFFER,
    CELL_CD,
    F_BUFFER_MULTI_OUTPUT,
    ROLE_FOLLOWER,
    SEVERITY_UNSUPPORTED,
    Block,
    Finding,
)


@dataclasses.dataclass(frozen=True)
class BuffersResult:
    """`blocks` = 버퍼 Block(입력 u 순), `findings` = 기록."""

    blocks: tuple
    findings: tuple


def buffer_bundles(model, ground, cells, stage, impedance, view_id):
    cds = [model.mos_by_name[c.dev] for c in cells.cells if c.kind == CELL_CD and c.forward]
    gate_nets = {m.g for m in cds}
    out_nets = {m.s for m in cds}
    stage_dist = dict(stage.stage_dist)
    blocks = []
    findings = []
    for root in sorted(gate_nets - out_nets):
        reached = set()
        devices = []
        pending = [root]
        while pending:
            net = pending.pop()
            for m in cds:
                if m.g == net and m.name not in devices:
                    devices.append(m.name)
                    if m.s not in reached:
                        reached.add(m.s)
                        pending.append(m.s)
        sinks = sorted(net for net in reached if net not in gate_nets)
        if len(sinks) != 1:
            findings.append(Finding(F_BUFFER_MULTI_OUTPUT, SEVERITY_UNSUPPORTED, view_id, (root, *sinks),
                                    "follower 묶음 R(u)의 싱크가 " + str(len(sinks)) + "개라 다출력 버퍼다", ("DEC-63", "DEC-59")))
        blocks.append(Block(tuple(sinks), BLOCK_BUFFER, stage_dist.get(root, 0), (root,), tuple(sinks),
                            tuple((name, ROLE_FOLLOWER) for name in sorted(devices)), tuple(sorted(reached | {root})),
                            tuple((net, impedance[net]) for net in sinks if net in impedance), STATUS_DERIVED))
    return BuffersResult(tuple(blocks), tuple(findings))
