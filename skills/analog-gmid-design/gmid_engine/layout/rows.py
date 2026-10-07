"""MOD7 물리 행 구성 계산 블록 -- 패턴 행 검산·행 Euler·box 행 접기 (design_mod7_layout.md 3절 4·5단계, LY1·LY6).

진입점: `compose_rows` -- core `@compute_block`(writer `ly_rows`, reads device `ly_device`·`ly_finger`, graph `ly_groups`·
`ly_groups_in`·`ly_row_groups`·`ly_pdk`·`ly_box_ratio`, writes graph `ly_rows`).

1. 행 그룹(행 그룹 id 순)마다: 패턴으로 배치된 matching 그룹의 패턴 행은 그대로 물리 행(`<행그룹>/<그룹>/<i>`)이 되고
   `check_walk_sequence` 로 segment 마다 검산한다. 나머지 소자는 finger_w 폭 키별로 한 물리 행(`<행그룹>/w<폭 키>`)이 되어
   `row_euler`(Euler -> 거울대칭 -> 최소 crossover)로 순서를 정한다. 행 안 matching 쌍 = 같은 그룹 멤버를 이름 순으로
   두 개씩 묶은 쌍, 민감도 = 차동쌍 "offset", 나머지 "ratio".
2. box(`box_verdict`, 행 폭 = sum(nf x (L + PDK finger 여유)), 높이 = finger_w): FAIL 이고 가장 넓은 행이 패턴 행이 아니면
   그 행을 `apply_explicit_row_split` 로 n = 2, 3, ... 행으로 접어 행 폭 비가 줄어드는 동안만 진행(상한 = 그 행 최대 nf,
   리터럴 없음), 가장 줄어든 n 을 적용하고 접은 행은 다시 `row_euler`. 개선이 없으면 멈추고 FAIL 을 그대로 남긴다
   (W 를 바꾸지 않는다 -- 접기는 총 W 불변). 패턴 행은 접지 않는다(matching 배치 보존).
"""
from collections import Counter

from gmid_engine.core import compute_block

from ._ly_fields import (
    DEVICE,
    F_BOX_RATIO,
    F_DEVICE,
    F_FINGER,
    F_GROUPS,
    F_GROUPS_IN,
    F_PDK,
    F_ROW_GROUPS,
    F_ROWS,
    GRAPH,
    GRAPH_KEY,
    WRITER_ROWS,
)
from .box_shape import box_verdict
from .contract_input import ROLE_DIFF_PAIR
from .contract_output import RowLayout, RowsLayout
from .mirror_trail import check_walk_sequence
from .row_euler import row_euler
from .row_fold import apply_explicit_row_split
from .transistor import Transistor

_SENS_DIFF = "offset"
_SENS_OTHER = "ratio"


class _Rows:
    """블록 호출 하나의 행 구성 상태(같은 행 내용의 Euler 는 한 번만)."""

    def __init__(self, devices, fingers, groups_in, pdk):
        self.devices = devices
        self.fingers = fingers
        self.overhead = pdk.finger_pitch_overhead_m
        self.pairs = []
        self.sens = {}
        for g in sorted(groups_in, key=lambda g: g.gid):
            members = sorted(g.members)
            for a, b in zip(members[0::2], members[1::2]):
                self.pairs.append((a, b))
                self.sens[(a, b)] = _SENS_DIFF if g.role == ROLE_DIFF_PAIR else _SENS_OTHER
        self.euler = {}

    def transistor(self, name, n_fingers):
        d = self.devices[name]
        return Transistor(name, d.kind, source=d.source, drain=d.drain, n_fingers=n_fingers,
                          finger_w=self.fingers[name].finger_w_m, l=d.L_m, gate=d.gate)

    def width(self, counts):
        return sum(nf * (self.devices[name].L_m + self.overhead) for name, nf in counts)

    def pattern_row(self, row_id, rid, kind, group, prow):
        counts = tuple(sorted(Counter(prow.transistor_sequence).items()))
        walk_ok = True
        for seg_seq, _ in prow.segments:
            seg_trs = [self.transistor(n, nf) for n, nf in sorted(Counter(seg_seq).items())]
            walk_ok = walk_ok and check_walk_sequence(list(seg_seq), seg_trs).ok
        return RowLayout(row_id, rid, kind, group.finger_w_key, group.finger_w_m, self.width(counts), counts,
                         prow.transistor_sequence, prow.node_sequence, prow.segments, "pattern:" + group.method,
                         len(prow.crossover_after), 1, walk_ok, group.gid)

    def euler_row(self, row_id, rid, kind, trs):
        content = tuple((t.name, t.n_fingers) for t in sorted(trs, key=lambda t: t.name))
        if content not in self.euler:
            self.euler[content] = row_euler(sorted(trs, key=lambda t: t.name), self.pairs, self.sens)
        res = self.euler[content]
        key = self.fingers[trs[0].name].finger_w_key
        segments = tuple((tuple(s["transistor_sequence"]), tuple(s["node_sequence"])) for s in res["segments"])
        return RowLayout(row_id, rid, kind, key, self.fingers[trs[0].name].finger_w_m, self.width(content), content,
                         tuple(res["transistor_sequence"]), tuple(res["node_sequence"]), segments, res["method"],
                         res["crossover_count"], res["n_components"], True, None)


def _box_rows(rows):
    return [(r.row_id, r.width_m, r.finger_w_m) for r in rows]


def _fold(state, rows, foldable, max_ratio):
    """box FAIL 동안 가장 넓은 비패턴 행을 접는다. 반환 (행, 접기 기록, 판정)."""
    folds = []
    verdict = box_verdict(_box_rows(rows), max_ratio, folds)
    while not verdict.ok and verdict.widest_row in foldable:
        rid = verdict.widest_row
        target = next(r for r in rows if r.row_id == rid)
        trs = foldable[rid]
        best = None
        for extra in range(1, max(t.n_fingers for t in trs)):
            n_rows = extra + 1
            split = apply_explicit_row_split({rid: trs}, {rid: n_rows})
            new_rows = [state.euler_row(sid, target.row_group, target.kind, split[sid]) for sid in sorted(split)]
            trial = [r for r in rows if r.row_id != rid] + new_rows
            ratio = box_verdict(_box_rows(trial), max_ratio, folds).width_ratio
            if best is not None and ratio >= best[0]:
                break
            best = (ratio, n_rows, trial)
        del foldable[rid]
        if best is None or best[0] >= verdict.width_ratio:
            break
        rows = best[2]
        folds.append((rid, best[1]))
        verdict = box_verdict(_box_rows(rows), max_ratio, folds)
    return rows, verdict


@compute_block(
    WRITER_ROWS,
    reads=((DEVICE, F_DEVICE), (DEVICE, F_FINGER), (GRAPH, F_GROUPS), (GRAPH, F_GROUPS_IN), (GRAPH, F_ROW_GROUPS),
           (GRAPH, F_PDK), (GRAPH, F_BOX_RATIO)),
    writes=((GRAPH, F_ROWS),),
)
def compose_rows(projection):
    """물리 행 전부(행 id 정렬)와 box 판정 = `RowsLayout`."""
    devices = dict(projection.column(DEVICE, F_DEVICE))
    fingers = dict(projection.column(DEVICE, F_FINGER))
    placed = [g for g in projection.value(GRAPH, GRAPH_KEY, F_GROUPS) if g.pattern is not None]
    state = _Rows(devices, fingers, projection.value(GRAPH, GRAPH_KEY, F_GROUPS_IN), projection.value(GRAPH, GRAPH_KEY, F_PDK))
    in_pattern = {m for g in placed for m in g.members}
    rows = []
    foldable = {}
    for rg in sorted(projection.value(GRAPH, GRAPH_KEY, F_ROW_GROUPS), key=lambda r: r.rid):
        members = set(rg.members)
        for g in placed:
            if set(g.members) <= members:
                for i, prow in enumerate(g.rows):
                    rows.append(state.pattern_row(rg.rid + "/" + g.gid + "/" + str(i), rg.rid, rg.kind, g, prow))
        by_key = {}
        for name in sorted(members - in_pattern):
            by_key.setdefault(fingers[name].finger_w_key, []).append(state.transistor(name, fingers[name].n_fingers))
        for key in sorted(by_key):
            row_id = rg.rid + "/w" + str(key)
            rows.append(state.euler_row(row_id, rg.rid, rg.kind, by_key[key]))
            foldable[row_id] = by_key[key]
    rows, verdict = _fold(state, rows, foldable, projection.value(GRAPH, GRAPH_KEY, F_BOX_RATIO))
    return {(GRAPH, F_ROWS): {GRAPH_KEY: RowsLayout(tuple(sorted(rows, key=lambda r: r.row_id)), verdict)}}
