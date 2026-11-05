"""뷰 하나의 SP1 분석 -- 파이프라인 한 줄 (설계 41 §1.1~1.9, 이 뷰의 모든 단계를 순서대로 부른다).

진입점: `analyze_view(model, seed, view_id, count_budget, ratified, exceptions=frozenset(), pm_declared=False) -> ViewResult`.

순서(41 §0 단계 A, 뷰마다 한 번): 뷰별 교류접지(`view_ac_ground`) -> 신호 넷·순방향(`signal_reach`) -> 셀(`classify_cells`) -> 구동 종류
(`drive_kinds`) -> 0-1 BFS(`stage_bfs`) -> 이득 블록(`build_blocks`) -> feedforward 분해(`feedforward_cells`) -> 버퍼 블록(`buffer_bundles`) -> 복합 블록(`composite_blocks`) ->
극점 노드(`pole_nodes`) -> 출력 방향(`output_directions`) -> 루프(`enumerate_loops`·`classify_loops`·`loop_polarity`·`loop_cut_candidates`·`loop_roles`).

* `exceptions` = 이 뷰에서만 교류접지로 두는 넷(ratified `ac_ground_exception` 사실, 호출자가 뷰 id 로 걸러 넘긴다, 41 §1.12.6).
* `pm_declared` = 이 전달 뷰에 전체 안정도 제약 `pm_ss_deg` 가 선언돼 있는가(`compensation_internal` 의 근거, 41 §1.12.3).

**축약과 비축약**: 전달 뷰의 여기가 기모드(두 넷, 가중 합 0)이고 회로 자기동형이 있으면(`virtual_ground`) 자기대응 넷을 접지로 본 **축약 뷰**가
셀·구동 종류·블록·극점 노드의 기준이다(CMFB 같은 공통모드 경로가 차동 전달 뷰 신호 경로에 들지 않는다). 루프 탐지는 가상접지를 접지로 보지 않는
**비축약 뷰**에서 한다(공통모드 되먹임은 가상접지를 지난다). 두 뷰에서 셀 판독이 다른 소자는 `unreduced_diff` 로 낸다(41 §1 불변식 측정).
**feedforward 분해**(41 §1.12.2): 전달 뷰는 이득 블록 구성 뒤 `feedforward_cells` 로 주경로와 feedforward 묶음을 가르고, 묶음이 있으면 그 소자를 뺀 모형(`_without`)에서 셀·구동 종류·
0-1 BFS·블록·버퍼·복합 블록을 다시 구한다(주경로 블록 사슬). 묶음 소자의 셀 판독은 1회차 값을 그대로 `cells` 에 남긴다. 루프 탐지는 항상 전체 모형(비축약 1회차)에서 한다.
**루프 역할**(41 §1.12.1·3·4): `classify_loops` 가 복합 diode 내부 루프(`composite_diode_internal`)를 가르고, 전달 뷰는 `loop_roles` 로 중첩 Miller 내부 루프(`compensation_internal`)를
가려 그 루프의 끊는 점을 루프 뷰 후보에서 뺀다. 루프 뷰 후보의 DC 사이클 극성·`ac_only` 사이클 커패시터는 `ViewResult.cut_polarity` 로 낸다(루프 뷰의 극성 판정은 `build_s1v`).
**루프 뷰**: 전달 뷰의 (3) 루프를 끊는 점(소자, gate 넷)별로 한 뷰씩 -- 모든 포트를 교류접지로 두고 끊는 소자의 채널 넷(drain·source)에만 신호를 주입하며,
감지는 그 gate 넷(되먹임으로 돌아온 응답), BFS 시작은 그 gate 넷이다. 같은 끊는 점의 루프는 한 뷰로 묶는다(뷰 키 (여기, 감지)가 같다).
"""
import collections
import dataclasses
import types

from gmid_engine.authoring import DC_CONDUCTING_PASSIVE_KINDS
from gmid_engine.core import sorted_items

from .ac_ground_view import view_ac_ground
from .blocks import build_blocks
from .buffer_bundles import buffer_bundles
from .cells import classify_cells
from .composite_blocks import composite_blocks
from .drive_kind import drive_kinds
from .feedforward_cells import feedforward_cells
from .loop_classify import classify_loops
from .loop_cuts import loop_cut_candidates
from .loop_roles import loop_roles
from .loops import enumerate_loops
from .node_impedance import node_impedance
from .output_direction import output_directions
from .polarity import loop_polarity
from .pole_nodes import pole_nodes
from .s1v_values import (
    F_LOOP_NO_CUT,
    F_UNDECLARED_LOOP,
    LOOP_COMPENSATION_INTERNAL,
    LOOP_SOURCE,
    LOOP_VIEW,
    REASON_COMPENSATION_NEEDS_PM,
    SEVERITY_REVIEW,
    SEVERITY_UNSUPPORTED,
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
    지나는 노드 합집합} -- 호출자가 포트쌍 CM 루프 대응(R31)을 판정한다. `cut_polarity` = {끊는 점: (DC 사이클 극성 정렬 tuple(중복 없음), `ac_only` 사이클의 커패시터 이름 tuple)}
    -- 루프 뷰의 극성(그 뷰의 DC 사이클 극성, 41 §1.12.4)을 호출자가 정한다."""

    view: object
    loop_seeds: tuple
    cut_nodes: object
    cut_polarity: object = types.MappingProxyType({})


@dataclasses.dataclass(frozen=True)
class _Analysis:
    reach: object
    cells: object
    drive: object
    stage: object


@dataclasses.dataclass(frozen=True)
class _LoopsInfo:
    loops: tuple
    groups: object
    findings: tuple
    roles: tuple
    polarity: object
    capacitors: tuple


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


def _without(model, names):
    """`names` 소자를 뺀 모형(feedforward 묶음을 뺀 주경로 모형, 41 §1.12.2-3). 수동소자·넷 목록·`mos_by_name`·복합 diode 정보는 그대로다."""
    mos = tuple(m for m in model.mos if m.name not in names)

    def group(net_of):
        table = {}
        for m in mos:
            table.setdefault(net_of(m), []).append(m)
        return types.MappingProxyType({net: tuple(ms) for net, ms in sorted_items(table)})

    return dataclasses.replace(model, mos=mos, by_gate=group(lambda m: m.g), by_drain=group(lambda m: m.d),
                               by_source=group(lambda m: m.s))


def _loops(model, ground, base, exclude, count_budget, view_id, forward_cells, pm_declared, with_roles):
    enumerated = enumerate_loops(model, ground, base.reach, base.cells, exclude, count_budget, view_id)
    dist = dict(base.stage.dist)
    classified = classify_loops(enumerated.cycles, base.reach.forward, base.cells, dist, view_id, model.composite_bundles)
    findings = list(enumerated.findings) + list(classified.findings)
    candidates = [loop_cut_candidates(cycle, base.cells, dist) if LOOP_VIEW in classes else ()
                  for cycle, (classes, _) in zip(enumerated.cycles, classified.entries)]
    frequency = collections.Counter(cut for cuts in candidates for cut in cuts)
    capacitors = frozenset(p.name for p in model.passives if p.kind not in DC_CONDUCTING_PASSIVE_KINDS)
    loops = []
    for cycle, (classes, _), cuts in zip(enumerated.cycles, classified.entries, candidates):
        polarity = loop_polarity(cycle, base.cells)
        cut = min(cuts, key=lambda c: (-frequency[c], c)) if cuts else ()
        loops.append(Loop(tuple(e.src for e in cycle), tuple(e.element for e in cycle), classes, cut, polarity, False, polarity == 0))
    roles = ()
    if with_roles:
        roles = loop_roles(((view_id, tuple(loops)),), ((view_id, forward_cells),), frozenset((view_id,)) if pm_declared else frozenset())
        internal = {r.loop_id: r for r in roles if r.role == LOOP_COMPENSATION_INTERNAL}
        loops = [dataclasses.replace(loop, classes=tuple(LOOP_COMPENSATION_INTERNAL if c == LOOP_VIEW else c for c in loop.classes))
                 if loop.cut and LOOP_VIEW in loop.classes and "loop:" + loop.cut[0] + ":" + loop.cut[1] in internal else loop
                 for loop in loops]
        for role in internal.values():
            if role.reason == REASON_COMPENSATION_NEEDS_PM:
                findings.append(Finding(F_UNDECLARED_LOOP, SEVERITY_UNSUPPORTED, view_id, (role.loop_id.rsplit(":", 1)[1],),
                                        role.reason + ": 중첩 Miller 내부 루프의 안정도는 전달 뷰의 전체 pm_ss_deg 가 덮는데 선언되지 않았다",
                                        ("41 §1.12.3", "U-24")))
    groups = {}
    polarity_by_cut = {}
    for loop in loops:
        if LOOP_VIEW not in loop.classes:
            continue
        if not loop.cut:
            findings.append(Finding(F_LOOP_NO_CUT, SEVERITY_REVIEW, view_id, tuple(sorted(set(loop.nodes))),
                                    "루프 뷰를 만드는 루프에 끊는 점 후보(루프 위 gate 엣지를 가진 CS 셀)가 없다", ("N3.2-2",)))
            continue
        groups.setdefault(loop.cut, set()).update(loop.nodes)
        dc, ac = polarity_by_cut.setdefault(loop.cut, (set(), set()))
        if loop.ac_only:
            ac.update(name for name in loop.devices if name in capacitors)
        else:
            dc.add(loop.polarity)
    polarity = types.MappingProxyType({cut: (tuple(sorted(dc)), tuple(sorted(ac))) for cut, (dc, ac) in sorted_items(polarity_by_cut)})
    compensation = tuple(sorted({name for loop in loops if loop.ac_only for name in loop.devices if name in capacitors}))
    return _LoopsInfo(tuple(loops), groups, tuple(findings), roles, polarity, compensation)


def analyze_view(model, seed, view_id, count_budget, ratified, exceptions=frozenset(), pm_declared=False):
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
    ag = view_ac_ground(model, reach_seeds, sense, virtual, exceptions)
    ground = ag.nets
    reduced_ground = ground | virtual
    primary = _analysis(model, reduced_ground, reach_seeds, sense, stage_seeds, drive_excite, view_id, ratified)
    base = primary if not virtual else _analysis(model, ground, reach_seeds, sense, stage_seeds, drive_excite, view_id, ratified)
    impedance = node_impedance(model, ground, frozenset(name for b in primary.cells.bundles for name in b.members))
    gain = build_blocks(model, ground, primary.cells, primary.drive, primary.stage, impedance, sense, view_id)
    ff = None if is_loop else feedforward_cells(model, seed, gain, primary.cells, primary.stage)
    main = primary
    cell_infos = primary.cells.cells
    slim = model
    findings = list(primary.cells.findings)
    if ff is not None and ff.cells:
        dropped = frozenset(name for f in ff.cells for name in f.cells + f.bias_cells + f.load_cells)
        slim = _without(model, dropped)
        main = _analysis(slim, reduced_ground, reach_seeds, sense, stage_seeds, drive_excite, view_id, ratified)
        gain = build_blocks(slim, ground, main.cells, main.drive, main.stage, impedance, sense, view_id)
        kept = {c.dev for c in main.cells.cells}
        cell_infos = sorted_items(tuple(main.cells.cells) + tuple(c for c in primary.cells.cells if c.dev not in kept),
                                  key=lambda c: c.dev)
    buffers = buffer_bundles(slim, reduced_ground, main.cells, main.stage, impedance, view_id)
    composite = composite_blocks(slim, gain, buffers, main.cells, count_budget, view_id)
    poles = pole_nodes(model, ground, composite.blocks, impedance, main.drive)
    outputs = set(sense) | {net for block in composite.blocks for net in block.outputs}
    directions = output_directions(model, ground, primary.reach, outputs)
    info = _loops(model, ground, base, loop_exclude, count_budget, view_id, tuple(main.cells.cells), pm_declared, not is_loop)
    cuts = tuple((dev, net) for (dev, net) in sorted(info.groups))
    findings += list(main.drive.findings + gain.findings + buffers.findings + composite.findings) + list(info.findings)
    if ff is not None:
        findings += [dataclasses.replace(f, view=view_id) for f in ff.findings]
    view = ViewS1v(
        view_id, seed.kind, seed.excite, tuple(sense), tuple(sorted(ground)), ag.bias_dependent, ag.moving,
        tuple(sorted(virtual)), tuple(sorted(primary.reach.signal)), tuple(sorted(primary.reach.forward)),
        tuple(cell_infos), main.cells.bundles, main.drive.drive, main.stage.dist, main.stage.stage_dist,
        main.stage.starts, main.drive.mirror_inputs, composite.blocks, composite.composites, poles, directions,
        info.loops, cuts, False, _cell_diff(model, primary, base) if virtual else (), _unique_findings(findings),
        () if ff is None else ff.main_path, () if ff is None else ff.cells, () if ff is None else ff.ratio_candidates,
        info.roles, 0, info.capacitors, ag.exceptions, seed.default_port)
    seeds = () if is_loop else tuple(ViewSeed(VIEW_LOOP, ((cut[1], 1.0),), (cut[1],), LOOP_SOURCE, cut) for cut in sorted(info.groups))
    return ViewResult(view, seeds, types.MappingProxyType({cut: tuple(sorted(nodes)) for cut, nodes in sorted_items(info.groups)}),
                      info.polarity)
