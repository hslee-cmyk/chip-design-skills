"""0-1 BFS 거리와 stage 시작 셀 (설계 41 §1.6, 계획 N3.2-4·5).

진입점: `stage_bfs(model, ground, reach, cells, drive, excite) -> StageResult`.

**엣지와 비용**(셀 기반 -- 소자 단위 gate->source->drain 우회로는 셀 우선순위가 막는다):

| 엣지 | 비용 |
|---|---|
| gate -> drain (CS) | 1. gate 가 diode 연결 단자(미러 입력 등 AC 1/gm 노드)면 0 |
| gate -> source (CS·CD·diode 소자) | 0 |
| source -> drain (CG) | 0. source 가 전압 구동이면 1 |
| pass 묶음 두 노드, 수동소자 두 단자 | 0 (양방향, 열린 항목 ⑬) |

여기 포트 넷에서 0-1 BFS 최소 비용이 거리(`dist`)다. 비용은 순서만 정하고 stage 경계를 정하지 않는다 -- 경계는 구동 종류 하나다.
보상 수동소자(Miller 커패시터 등)가 비용 0 지름길을 만들어 출력 거리를 앞 stage 와 같게 만들 수 있으므로(수동소자 비용 0 은 복귀 경로
판정용 동률 규칙이다), **stage 번호용 거리 `stage_dist`는 수동소자 엣지를 뺀 같은 BFS** 로 따로 잰다. 블록의 stage 는 `stage_dist` 다.

**stage 시작 셀**(순방향 셀만): 입력이 전압 구동인 CS(gate 의 구동 종류), source 가 전압 구동인 CG. 단 (가) DC 역할이 바이어스 전류원인
셀(측면 주입 K8)과 (나) gate 가 미러 입력 노드인 셀(⑧: 규칙 9 (c) 의 diode 미러 갈래를 stage 시작보다 먼저 적용)은 시작하지 않는다.
CD 는 stage 를 올리지 않는다(버퍼 구간).
"""
import collections
import dataclasses

from gmid_engine.core import sorted_items

from .s1_values import ROLE_BIAS
from .s1v_values import CELL_CD, CELL_CG, CELL_CS, CELL_DIODE_LOAD, DRIVE_VOLTAGE


@dataclasses.dataclass(frozen=True)
class StageResult:
    """`dist` = 수동소자 엣지를 포함한 (넷, 거리), `stage_dist` = 수동소자 엣지를 뺀 (넷, 거리)(둘 다 이름순, 도달하지 못한 신호 넷은
    없음), `starts` = stage 시작 셀 이름순."""

    dist: tuple
    stage_dist: tuple
    starts: tuple


def _edges(model, ground, cells, drive, with_passives):
    info = {c.dev: c for c in cells.cells}
    voltage = {d.net for d in drive.drive if d.kind == DRIVE_VOLTAGE}
    edges = {}

    def add(a, b, cost):
        if a != b and a not in ground and b not in ground:
            edges.setdefault(a, []).append((b, cost))

    for m in model.mos:
        kind = info[m.name].kind
        if kind == CELL_CS:
            add(m.g, m.d, 0 if m.g in model.diode_nodes else 1)
            add(m.g, m.s, 0)
        elif kind in (CELL_CD, CELL_DIODE_LOAD):
            add(m.g, m.s, 0)
        elif kind == CELL_CG:
            add(m.s, m.d, 1 if m.s in voltage else 0)
    for bundle in cells.bundles:
        add(bundle.nodes[0], bundle.nodes[1], 0)
        add(bundle.nodes[1], bundle.nodes[0], 0)
    for p in (model.passives if with_passives else ()):
        add(p.a, p.b, 0)
        add(p.b, p.a, 0)
    return edges


def _distances(edges, seeds):
    dist = {net: 0 for net in seeds}
    queue = collections.deque(sorted(dist))
    while queue:
        net = queue.popleft()
        for nxt, cost in sorted(edges.get(net, ())):
            if nxt not in dist or dist[net] + cost < dist[nxt]:
                dist[nxt] = dist[net] + cost
                (queue.append if cost else queue.appendleft)(nxt)
    return dist


def stage_bfs(model, ground, reach, cells, drive, excite):
    seeds = [net for net in excite if net not in ground]
    dist = _distances(_edges(model, ground, cells, drive, True), seeds)
    stage_dist = _distances(_edges(model, ground, cells, drive, False), seeds)
    info = {c.dev: c for c in cells.cells}
    voltage = {d.net for d in drive.drive if d.kind == DRIVE_VOLTAGE}
    starts = []
    for m in model.mos:
        cell = info[m.name]
        if not cell.forward or m.dc_role == ROLE_BIAS:
            continue
        if cell.kind == CELL_CS and m.g in voltage and m.g not in drive.mirror_inputs:
            starts.append(m.name)
        elif cell.kind == CELL_CG and m.s in voltage:
            starts.append(m.name)
    return StageResult(sorted_items(dist), sorted_items(stage_dist), tuple(starts))
