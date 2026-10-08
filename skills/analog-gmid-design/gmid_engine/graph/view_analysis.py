"""뷰 하나의 SP1 분석 -- 파이프라인 한 줄 (설계 41 §1.1~1.9, 이 뷰의 모든 단계를 순서대로 부른다).

진입점: `analyze_view(model, seed, view_id, count_budget, ratified) -> ViewResult`.

순서(41 §0 단계 A, 뷰마다 한 번): 뷰별 교류접지(`view_ac_ground`) -> 신호 넷·순방향(`signal_reach`) -> 셀(`classify_cells`) -> 구동 종류
(`drive_kinds`) -> 0-1 BFS(`stage_bfs`) -> 이득 블록(`build_blocks`) -> 버퍼 블록(`buffer_bundles`) -> 복합 블록(`composite_blocks`) ->
극점 노드(`pole_nodes`) -> 출력 방향(`output_directions`) -> 루프(`enumerate_loops`·`classify_loops`·`loop_polarity`·`loop_cut_candidates`).

**축약과 비축약**: 전달 뷰의 여기가 기모드(두 넷, 가중 합 0)이고 회로 자기동형이 있으면(`virtual_ground`) 자기대응 넷을 접지로 본 **축약 뷰**가
셀·구동 종류·블록·극점 노드의 기준이다(CMFB 같은 공통모드 경로가 차동 전달 뷰 신호 경로에 들지 않는다). 루프 탐지는 가상접지를 접지로 보지 않는
**비축약 뷰**에서 한다(공통모드 되먹임은 가상접지를 지난다). 두 뷰에서 셀 판독이 다른 소자는 `unreduced_diff` 로 낸다(41 §1 불변식 측정).
**루프 뷰**: 전달 뷰의 (3) 루프를 끊는 점(소자, gate 넷)별로 한 뷰씩 -- 모든 포트를 교류접지로 두고 끊는 소자의 채널 넷(drain·source)에만 신호를 주입하며,
감지는 그 gate 넷(되먹임으로 돌아온 응답), BFS 시작은 그 gate 넷이다. 같은 끊는 점의 루프는 한 뷰로 묶는다(뷰 키 (여기, 감지)가 같다).
"""
import collections
import dataclasses
import types

from gmid_engine.core import sorted_items

from .ac_ground_view import view_ac_ground
from .blocks import build_blocks
from .buffer_bundles import buffer_bundles
from .cells import classify_cells
from .composite_blocks import composite_blocks
from .drive_kind import drive_kinds
from .loop_classify import classify_loops
from .loop_cuts import loop_cut_candidates
from .loops import enumerate_loops
from .node_impedance import node_impedance
from .output_direction import output_directions
from .polarity import loop_polarity
from .pole_nodes import pole_nodes
from .s1v_values import (
    F_LOOP_NO_CUT,
    F_LOOP_POLARITY,
    LOOP_SOURCE,
    LOOP_VIEW,
    SEVERITY_REVIEW,
    VIEW_LOOP,
    Finding,
    Loop,
    ViewS1v,
    ViewSeed,
)
from .signal_reach import signal_reach
from .stage_bfs import stage_bfs
from .virtual_ground import virtual_ground


@dataclasses.dataclass(frozen=True)
class ViewResult:
    """`view` = ViewS1v, `loop_seeds` = 이 뷰의 (3) 루프가 만든 루프 뷰 씨앗(끊는 점마다 하나, 이름순), `cut_nodes` = {끊는 점: 그 점의 루프들이
    지나는 노드 합집합} -- 호출자가 포트쌍 CM 루프 대응(R31)을 판정한다."""

    view: object
    loop_seeds: tuple
    cut_nodes: object


@dataclasses.dataclass(frozen=True)
class _Analysis:
    reach: object
    cells: object
    drive: object
    stage: object


def _analysis(model, ground, reach_seeds, sense, stage_seeds, drive_excite, view_id, ratified):
    reach = signal_reach(model, ground, reach_seeds, sense)
    cells = classify_cells(model, ground, reach, sense, view_id)
    drive = drive_kinds(model, ground, reach, cells, drive_excite, view_id, ratified)
    return _Analysis(reach, cells, drive, stage_bfs(model, ground, reach, cells, drive, stage_seeds))


def _unique_findings(findings):
    """같은 기록(분기·뷰·대상·근거)은 한 번만, 코드·뷰·대상 순."""
    return sorted_items(set(findings), key=lambda f: (f.code, f.view, f.subject, f.detail))


def _cell_diff(model, reduced, unreduced):
    old = {c.dev: (c.kind, c.forward) for c in reduced.cells.cells}
    new = {c.dev: (c.kind, c.forward) for c in unreduced.cells.cells}
    return tuple((name, old[name], new[name]) for name in sorted(old)
                 if old[name] != new[name] and (old[name][1] or new[name][1]))


def _loops(model, ground, base, exclude, count_budget, view_id):
    enumerated = enumerate_loops(model, ground, base.reach, base.cells, exclude, count_budget, view_id)
    classified = classify_loops(enumerated.cycles, base.reach.forward, base.cells, dict(base.stage.dist), view_id)
    findings = list(enumerated.findings) + list(classified.findings)
    dist = dict(base.stage.dist)
    candidates = [loop_cut_candidates(cycle, base.cells, dist) if LOOP_VIEW in classes else ()
                  for cycle, (classes, _) in zip(enumerated.cycles, classified.entries)]
    frequency = collections.Counter(cut for cuts in candidates for cut in cuts)
    loops = []
    groups = {}
    for cycle, (classes, reason), cuts in zip(enumerated.cycles, classified.entries, candidates):
        polarity = loop_polarity(cycle, base.cells)
        cut = min(cuts, key=lambda c: (-frequency[c], c)) if cuts else ()
        nodes = tuple(e.src for e in cycle)
        loops.append(Loop(nodes, tuple(e.element for e in cycle), classes, cut, polarity, False))
        if LOOP_VIEW in classes:
            if not cut:
                findings.append(Finding(F_LOOP_NO_CUT, SEVERITY_REVIEW, view_id, tuple(sorted(set(nodes))),
                                        "루프 뷰를 만드는 루프에 끊는 점 후보(루프 위 gate 엣지를 가진 CS 셀)가 없다", ("N3.2-2",)))
            else:
                groups.setdefault(cut, set()).update(nodes)
                if polarity == 0:
                    findings.append(Finding(F_LOOP_POLARITY, SEVERITY_REVIEW, view_id, tuple(sorted(set(nodes))),
                                            "커패시터를 지나 저주파 경로가 없어 극성이 정의되지 않는다(Cc-Rz 직렬 루프는 J7)", ("N3.2-7",)))
    return tuple(loops), groups, tuple(findings)


def analyze_view(model, seed, view_id, count_budget, ratified):
    is_loop = seed.kind == VIEW_LOOP
    sense = seed.sense
    if is_loop:
        device = model.mos_by_name[seed.cut[0]]
        reach_seeds = (device.d, device.s)
        stage_seeds = (seed.cut[1],)
        drive_excite = (seed.cut[1],)
        loop_exclude = ()
        virtual = frozenset()
    else:
        reach_seeds = tuple(net for net, _ in seed.excite)
        stage_seeds = drive_excite = loop_exclude = reach_seeds
        virtual = virtual_ground(model, seed.excite)
    ag = view_ac_ground(model, reach_seeds, sense, virtual)
    ground = ag.nets
    reduced_ground = ground | virtual
    primary = _analysis(model, reduced_ground, reach_seeds, sense, stage_seeds, drive_excite, view_id, ratified)
    base = primary if not virtual else _analysis(model, ground, reach_seeds, sense, stage_seeds, drive_excite, view_id, ratified)
    impedance = node_impedance(model, ground, frozenset(name for b in primary.cells.bundles for name in b.members))
    gain = build_blocks(model, ground, primary.cells, primary.drive, primary.stage, impedance, sense, view_id)
    buffers = buffer_bundles(model, reduced_ground, primary.cells, primary.stage, impedance, view_id)
    composite = composite_blocks(model, gain, buffers, primary.cells, count_budget, view_id)
    poles = pole_nodes(model, ground, composite.blocks, impedance, primary.drive)
    outputs = set(sense) | {net for block in composite.blocks for net in block.outputs}
    directions = output_directions(model, ground, primary.reach, outputs)
    loops, groups, loop_findings = _loops(model, ground, base, loop_exclude, count_budget, view_id)
    cuts = tuple((dev, net) for (dev, net) in sorted(groups))
    findings = (primary.cells.findings + primary.drive.findings + gain.findings + buffers.findings + composite.findings
                + loop_findings)
    view = ViewS1v(
        view_id, seed.kind, seed.excite, tuple(sense), tuple(sorted(ground)), ag.bias_dependent, ag.moving,
        tuple(sorted(virtual)), tuple(sorted(primary.reach.signal)), tuple(sorted(primary.reach.forward)),
        primary.cells.cells, primary.cells.bundles, primary.drive.drive, primary.stage.dist, primary.stage.stage_dist,
        primary.stage.starts, primary.drive.mirror_inputs, composite.blocks, composite.composites, poles, directions,
        loops, cuts, False, _cell_diff(model, primary, base) if virtual else (), _unique_findings(findings))
    seeds = () if is_loop else tuple(ViewSeed(VIEW_LOOP, ((cut[1], 1.0),), (cut[1],), LOOP_SOURCE, cut) for cut in sorted(groups))
    return ViewResult(view, seeds, types.MappingProxyType({cut: tuple(sorted(nodes)) for cut, nodes in sorted_items(groups)}))
