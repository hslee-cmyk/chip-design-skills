"""MOD7 물리 행 구성 계산 블록 -- 패턴 행 검산·행 Euler·hub 병합·면적 목적 행 접기/재구성·floorplan
(design_mod7_layout.md 3절 4~6단계, LY1·LY6, 사용자 결정 2026-10-07 Q8 (v)~(viii)).

진입점: `compose_rows` -- core `@compute_block`(writer `ly_rows`, reads device `ly_point`(kind·L_m)·`ly_pins`·`ly_finger`,
graph `ly_groups`·`ly_groups_in`·`ly_row_groups`·`ly_pdk`·`ly_passives`·`ly_canon_rows`(정준 별칭표), writes graph `ly_rows`·`ly_floorplan`·`ly_diffusion`).

1. 행 그룹(행 그룹 id 순)마다: 패턴으로 배치된 matching 그룹의 패턴 행은 그대로 물리 행(`<행그룹>/<그룹>/<i>`)이 되고
   `check_walk_sequence` 로 segment 마다 검산한다. 나머지 소자는 finger_w 폭 키별로 한 물리 행(`<행그룹>/w<폭 키>`)이 되어
   `row_euler`(Euler -> 거울대칭 -> 최소 crossover)로 순서를 정한다. 행 안 matching 쌍 = 레이아웃 matching 그룹 멤버를
   이름 순으로 두 개씩 묶은 쌍, 민감도 = 차동쌍 "offset", 나머지 "ratio". 레이아웃 matching 그룹 멤버가 든 행은 `matching`.
2. stage 를 넘는 hub 병합(Q8 (viii)): matching 없는 Euler 행 중 같은 (kind, body, 폭 키)인 행들의 소자로 복사 함수
   `find_hub_merge_candidates` 를 불러 공유 source/drain 넷 후보를 찾고, 그 넷을 가진 행들(서로 다른 행 그룹)을 한 행으로
   합친 `row_euler` 결과로 판정 축 외곽 면적이 줄면 채택한다. 노이즈 결합 우려는 기록만 한다(`MergeDecision.note`).
3. box 개선(Q8 (v)(vi)) -- 목적 = 판정 축 외곽 면적(`floorplan_of`), 하드 box 게이트 없음. 행을 폭 내림차순으로 한 번씩:
   * matching 없는 행: `apply_explicit_row_split` 로 n = 2, 3, ..., (그 행 최대 nf) 행으로 접어 조각마다 `row_euler`,
     면적이 직전 n 보다 줄지 않으면 멈추고, 가장 작은 면적이 현재보다 작을 때만 적용(`folds` 에 (행 id, n)).
   * matching 패턴 행(common-centroid·행 swap): 그 그룹을 패턴 함수(`common_centroid_layout(n_rows=k)` /
     `row_swap_layout(n_rows=k)`)로 k = 현재 행 수 + 1, ... 로 재구성하고 Euler(walk)·matching(dx·dy)을 다시 잰다.
     walk 실패이거나 무게중심이 나빠지면(max(dx, dy) 증가) 거부, 나머지는 면적으로 같은 규칙. interdigitation 행·패턴 없는
     matching 행은 자동으로 접지 않는다(기록).
   모든 시도는 `FoldAttempt` 로 남는다. 행 폭 비는 `box_verdict` 로 기록만 한다.
4. floorplan = 최종 행의 `floorplan_of`(수동소자 블록 포함 -- 판정 축 면적, 면적 계산은 행 집합 내용으로 memo -- 같은 행 집합은
   다시 패킹하지 않는다). `ly.diffusion` = 최종 행의 `diffusion_geometry`(LY8).
"""
import dataclasses
from collections import Counter

from gmid_engine.core import compute_block

from ._helpers_pattern import device_views, offsets, orient, pattern_rows
from ._ly_fields import (
    DEVICE,
    F_CANON_ROWS,
    F_DIFFUSION,
    F_FINGER,
    F_FLOORPLAN,
    F_GROUPS,
    F_GROUPS_IN,
    F_PASSIVES,
    F_PDK,
    F_PINS,
    F_POINT,
    F_ROW_GROUPS,
    F_ROWS,
    GRAPH,
    GRAPH_KEY,
    WRITER_ROWS,
)
from .box_shape import box_verdict
from .contract_input import LAYOUT_ROLES, PATTERN_COMMON_CENTROID, ROLE_BRANCH_SYMMETRIC, ROLE_DIFF_PAIR
from .contract_output import MERGE_NOISE_NOTE, FoldAttempt, GroupRebuild, MergeDecision, RowLayout, RowsLayout
from .diffusion import diffusion_geometry
from .floorplan import floorplan_of
from .canonical_naming import canonical_names
from .hub_candidates import find_hub_merge_candidates
from .mirror_trail import check_walk_sequence
from .patterns_common_centroid import common_centroid_layout
from .patterns_row_swap import row_swap_layout
from .row_euler import row_euler
from .row_fold import apply_explicit_row_split
from .transistor import Transistor

_SENS_DIFF = "offset"
_SENS_OTHER = "ratio"
_MERGE_SEP = "+"


class _Rows:
    """블록 호출 하나의 행 구성 상태(같은 행 내용의 Euler·같은 행 집합의 면적은 한 번만)."""

    def __init__(self, devices, fingers, groups_in, row_groups, pdk, passives=()):
        self.devices = devices
        self.passives = passives
        self.fingers = fingers
        self.pdk = pdk
        self.overhead = pdk.finger_pitch_overhead_m
        self.bodies = {rg.rid: rg.body_net for rg in row_groups}
        self.layout_groups = {g.gid: g for g in groups_in if g.role in LAYOUT_ROLES}
        self.matched = {m for g in self.layout_groups.values() for m in g.members}
        self.pairs = []
        self.sens = {}
        for g in sorted(self.layout_groups.values(), key=lambda g: g.gid):
            members = sorted(g.members)
            for a, b in zip(members[0::2], members[1::2]):
                self.pairs.append((a, b))
                self.sens[(a, b)] = _SENS_DIFF if g.role == ROLE_DIFF_PAIR else _SENS_OTHER
        self.euler = {}
        self.areas = {}

    def transistor(self, name, n_fingers):
        d = self.devices[name]
        return Transistor(name, d.kind, source=d.source, drain=d.drain, n_fingers=n_fingers,
                          finger_w=self.fingers[name].finger_w_m, l=d.L_m, gate=d.gate)

    def width(self, counts):
        return sum(nf * (self.devices[name].L_m + self.overhead) for name, nf in counts)

    def pattern_row(self, row_id, rid, kind, group, method, prow):
        counts = tuple(sorted(Counter(prow.transistor_sequence).items()))
        walk_ok = True
        for seg_seq, _ in prow.segments:
            seg_trs = [self.transistor(n, nf) for n, nf in sorted(Counter(seg_seq).items())]
            walk_ok = walk_ok and check_walk_sequence(list(seg_seq), seg_trs).ok
        return RowLayout(row_id, rid, kind, group.finger_w_key, group.finger_w_m, self.width(counts), counts,
                         prow.transistor_sequence, prow.node_sequence, prow.segments, "pattern:" + method,
                         len(prow.crossover_after), 1, walk_ok, group.gid, True)

    def euler_row(self, row_id, rid, kind, trs):
        content = tuple((t.name, t.n_fingers) for t in sorted(trs, key=lambda t: t.name))
        if content not in self.euler:
            self.euler[content] = row_euler(sorted(trs, key=lambda t: t.name), self.pairs, self.sens)
        res = self.euler[content]
        key = self.fingers[trs[0].name].finger_w_key
        segments = tuple((tuple(s["transistor_sequence"]), tuple(s["node_sequence"])) for s in res["segments"])
        return RowLayout(row_id, rid, kind, key, self.fingers[trs[0].name].finger_w_m, self.width(content), content,
                         tuple(res["transistor_sequence"]), tuple(res["node_sequence"]), segments, res["method"],
                         res["crossover_count"], res["n_components"], True, None,
                         any(name in self.matched for name, _ in content))

    def row_transistors(self, row):
        return [self.transistor(name, nf) for name, nf in row.devices]

    def area(self, rows):
        """판정 축 외곽 면적(m^2) -- 같은 행 집합 내용이면 memo."""
        key = tuple(sorted((r.row_id, r.row_group, r.width_m, r.finger_w_m, r.transistor_sequence) for r in rows))
        if key not in self.areas:
            self.areas[key] = floorplan_of(rows, self.bodies, self.pdk, self.passives)
        return self.areas[key]


def _initial_rows(state, row_groups, placed, fingers):
    rows = []
    in_pattern = {m for g in placed for m in g.members}
    for rg in sorted(row_groups, key=lambda r: r.rid):
        members = set(rg.members)
        for g in placed:
            if set(g.members) <= members:
                for i, prow in enumerate(g.rows):
                    rows.append(state.pattern_row(rg.rid + "/" + g.gid + "/" + str(i), rg.rid, rg.kind, g, g.method, prow))
        by_key = {}
        for name in sorted(n for n in members - in_pattern if n in fingers):
            by_key.setdefault(fingers[name].finger_w_key, []).append(state.transistor(name, fingers[name].n_fingers))
        for key in sorted(by_key):
            rows.append(state.euler_row(rg.rid + "/w" + str(key), rg.rid, rg.kind, by_key[key]))
    return rows


def _merge_hubs(state, rows):
    """stage 를 넘는 hub 병합 -- (rows, MergeDecision tuple)."""
    decisions = []
    plain = [r for r in rows if r.group is None and not r.matching]
    parts = {}
    for r in plain:
        parts.setdefault((r.kind, state.bodies[r.row_group], r.finger_w_key), []).append(r.row_id)
    for part in sorted(parts):
        if len(parts[part]) <= 1:
            continue
        live = {r.row_id: r for r in rows}
        trs = [t for rid in parts[part] for t in state.row_transistors(live[rid])]
        candidates = find_hub_merge_candidates(trs)
        for (_, net) in sorted(candidates, key=lambda kn: kn[1]):
            live = {r.row_id: r for r in rows}
            row_of = {name: r.row_id for r in rows for name, _ in r.devices}
            names = {t.name for t in candidates[(part[0], net)]}
            involved = sorted({row_of[n] for n in names if n in row_of})
            if len(involved) <= 1:
                continue
            before = state.area(rows).outline_area_m2
            merged_trs = [t for rid in involved for t in state.row_transistors(live[rid])]
            first = live[involved[0]]
            merged = state.euler_row(_MERGE_SEP.join(involved), first.row_group, first.kind, merged_trs)
            trial = [r for r in rows if r.row_id not in involved] + [merged]
            after = state.area(trial).outline_area_m2
            adopt = after < before
            decisions.append(MergeDecision(tuple(involved), net, adopt,
                                           "area_decreased" if adopt else "area_not_decreased", before, after,
                                           MERGE_NOISE_NOTE))
            if adopt:
                rows = trial
    return rows, tuple(decisions)


def _group_transistors(state, group_in, layout):
    devices = state.devices
    if group_in.role == ROLE_BRANCH_SYMMETRIC:
        ends = tuple((n, devices[n].source, devices[n].drain) for n in group_in.members)
    else:
        ends, _ = orient(group_in, devices)
    nf_of = dict(layout.n_fingers)
    return [Transistor(n, devices[n].kind, source=s, drain=d, n_fingers=nf_of[n]) for n, s, d in ends]


def _rebuild(state, rows, layout, current, attempts):
    """matching 패턴 행 재구성 -- (rows, current, GroupRebuild 또는 None)."""
    group_in = state.layout_groups[layout.gid]
    old = [r for r in rows if r.group == layout.gid]
    rid, kind = old[0].row_group, old[0].kind
    tag = rid + "/" + layout.gid
    if layout.pattern != PATTERN_COMMON_CENTROID:
        attempts.append(FoldAttempt(tag, "rebuild", len(old), current, None, None, False, "pattern_not_rebuildable"))
        return rows, current, None
    trs = _group_transistors(state, group_in, layout)
    total = sum(t.n_fingers for t in trs)
    old_dx, old_dy = offsets(old, layout.members)
    old_xo = max(r.crossover_count for r in old)
    best = None
    for extra in range(len(old), max(t.n_fingers for t in trs)):
        k = extra + 1
        if group_in.role == ROLE_BRANCH_SYMMETRIC:
            result = row_swap_layout(trs, k, state.pairs, state.sens)
        else:
            result = common_centroid_layout(trs, n_rows=k, max_candidates=total)
        prows = pattern_rows(result, trs)
        dx, dy = offsets(prows, layout.members)
        new = [state.pattern_row(tag + "/" + str(i), rid, kind, layout, result["method"], p) for i, p in enumerate(prows)]
        trial = [r for r in rows if r.group != layout.gid] + new
        area = state.area(trial).outline_area_m2
        worse = (not all(r.walk_ok for r in new) or max(dx, dy) > max(old_dx, old_dy)
                 or max(r.crossover_count for r in new) > old_xo)
        attempts.append(FoldAttempt(tag, "rebuild", k, area, float(dx), float(dy), False,
                                    "matching_worse" if worse else "evaluated"))
        if worse:
            continue
        if best is not None and area >= best[0]:
            break
        best = (area, k, trial, len(attempts) - 1, result["method"], dx, dy)
    if best is None or best[0] >= current:
        return rows, current, None
    attempts[best[3]] = dataclasses.replace(attempts[best[3]], adopted=True, reason="adopted")
    return best[2], best[0], GroupRebuild(layout.gid, best[1], best[4], float(best[5]), float(best[6]))


def _fold(state, rows, target, current, attempts):
    """matching 없는 행 접기 -- (rows, current, 적용한 n 또는 None)."""
    trs = state.row_transistors(target)
    best = None
    for extra in range(1, max(t.n_fingers for t in trs)):
        n_rows = extra + 1
        split = apply_explicit_row_split({target.row_id: trs}, {target.row_id: n_rows})
        new = [state.euler_row(sid, target.row_group, target.kind, split[sid]) for sid in split]
        trial = [r for r in rows if r.row_id != target.row_id] + new
        area = state.area(trial).outline_area_m2
        attempts.append(FoldAttempt(target.row_id, "fold", n_rows, area, None, None, False, "evaluated"))
        if best is not None and area >= best[0]:
            break
        best = (area, n_rows, trial, len(attempts) - 1)
    if best is None or best[0] >= current:
        return rows, current, None
    attempts[best[3]] = dataclasses.replace(attempts[best[3]], adopted=True, reason="adopted")
    return best[2], best[0], best[1]


def _improve(state, rows, placed):
    """면적 목적 box 개선 -- (rows, FoldAttempt tuple, folds, GroupRebuild tuple)."""
    layouts = {g.gid: g for g in placed}
    attempts, folds, rebuilds, done = [], [], [], set()
    current = state.area(rows).outline_area_m2
    for target in sorted(rows, key=lambda r: (-r.width_m, r.row_id)):
        if target.group is not None:
            if target.group in done:
                continue
            done.add(target.group)
            rows, current, rebuilt = _rebuild(state, rows, layouts[target.group], current, attempts)
            if rebuilt is not None:
                rebuilds.append(rebuilt)
        elif target.matching:
            attempts.append(FoldAttempt(target.row_id, "fold", 1, current, None, None, False,
                                        "matching_row_not_auto_folded"))
        else:
            rows, current, n_rows = _fold(state, rows, target, current, attempts)
            if n_rows is not None:
                folds.append((target.row_id, n_rows))
    return rows, tuple(attempts), tuple(folds), tuple(rebuilds)


@compute_block(
    WRITER_ROWS,
    reads=((DEVICE, F_POINT), (DEVICE, F_PINS), (DEVICE, F_FINGER), (GRAPH, F_GROUPS), (GRAPH, F_GROUPS_IN), (GRAPH, F_ROW_GROUPS),
           (GRAPH, F_PDK), (GRAPH, F_PASSIVES), (GRAPH, F_CANON_ROWS)),
    writes=((GRAPH, F_ROWS), (GRAPH, F_FLOORPLAN), (GRAPH, F_DIFFUSION)),
)
@canonical_names(rows=True)
def compose_rows(projection):
    """물리 행 전부(행 id 정렬)·행 폭 비 기록·시도 기록 = `RowsLayout`, 최종 행의 `FloorplanSummary`, 최종 행의 `ly.diffusion`."""
    devices = device_views(projection)
    fingers = dict(projection.column(DEVICE, F_FINGER))
    placed = [g for g in projection.value(GRAPH, GRAPH_KEY, F_GROUPS) if g.pattern is not None]
    row_groups = projection.value(GRAPH, GRAPH_KEY, F_ROW_GROUPS)
    state = _Rows(devices, fingers, projection.value(GRAPH, GRAPH_KEY, F_GROUPS_IN), row_groups,
                  projection.value(GRAPH, GRAPH_KEY, F_PDK), projection.value(GRAPH, GRAPH_KEY, F_PASSIVES))
    rows = _initial_rows(state, row_groups, placed, fingers)
    if not rows:
        raise ValueError("compose_rows: 배치할 소자가 없다(모든 소자에 사용 가능한 폭 슬라이스가 없음 -- ly_slices 사유 참조)")
    rows, merges = _merge_hubs(state, rows)
    rows, attempts, folds, rebuilds = _improve(state, rows, placed)
    rows = tuple(sorted(rows, key=lambda r: r.row_id))
    box = box_verdict([(r.row_id, r.width_m, r.finger_w_m) for r in rows], folds)
    return {(GRAPH, F_ROWS): {GRAPH_KEY: RowsLayout(rows, box, attempts, merges, rebuilds)},
            (GRAPH, F_FLOORPLAN): {GRAPH_KEY: state.area(rows)},
            (GRAPH, F_DIFFUSION): {GRAPH_KEY: diffusion_geometry(rows, devices, state.pdk)}}
