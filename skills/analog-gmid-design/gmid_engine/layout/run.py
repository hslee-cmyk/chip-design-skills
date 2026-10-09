"""MOD7 레이아웃 공개 진입점 (design_mod7_layout.md 1절 `run.py`, 3절 7단계, 4절 graph 필드, 사용자 결정 2026-10-07 Q4·Q8).

진입점: `run_layout(layout_input, memo, previous=None) -> LayoutResult`.

1. 계약 `LayoutInput` 을 graph 입력 필드(writer `ly_input`)로 쓴다. `previous`(앞 호출의 `LayoutResult`)를 주면 그 스냅샷
   위에 쓴다 -- 바뀌지 않은 입력 열만 읽는 블록은 다시 계산하지 않는다(필드 = 캐시, core `compute_block`).
2. 폭 슬라이스별 보존량 실현(`slice_density`, LUT 조회는 `memo` = MOD1 `LutMemo`)을 device `ly_slices`(writer
   `ly_slice_density`)로 쓴다. 입력 버전 = (LUT 지문, 폭 키, 소자별 (kind, L, ID, gm/ID, VDS, VSB)) -- 같으면 다시 조회하지 않는다.
   같은 보존량·동작점의 소자는 한 번만 조회한다. `memo.lut.fp` 가 `pdk.source_fp` 와 다르면 `ValueError`.
3. 계산 블록을 차례로: `finger_candidates` -> `pattern_select` -> `finger_geometry` -> `compose_rows`(행 + floorplan).
4. 결과: `review_needed`(배치 못 한 차동쌍·branch_symmetric -- LY5 는 즉시 완화하지 않고 판정을 MOD8 에 맡긴다, dx·dy) 맨 앞, coverage(`check_stick_diagram_coverage`),
   W_requests 모음(그룹 요청 + finger_quantization + 사용 가능 폭이 없는 소자 `no_usable_slice`), 불변식, 재검증 요청
   (`Revalidation` -- W_request 유무와 관계없이 항상 required, 평가 커널·봉인이 엔진에 생길 때까지 status pending_wiring).
"""
from gmid_engine.core import GraphSnapshot, fp_of

from ._ly_fields import (
    DEVICE,
    F_DEVICE,
    F_DIFFUSION,
    F_DISPOSITIONS,
    F_FINGER,
    F_FLOORPLAN,
    F_GROUPS,
    F_GROUPS_IN,
    F_PASSIVES,
    F_PDK,
    F_REJECTED,
    F_ROW_GROUPS,
    F_ROWS,
    F_SLICES,
    GRAPH,
    GRAPH_KEY,
    LY_WRITERS,
    WRITER_INPUT,
    WRITER_SLICES,
)
from .contract_input import CC_REQUIRED_ROLES
from .contract_output import (
    REVALIDATION_CONSUMER,
    REVALIDATION_PENDING,
    REVALIDATION_PENDING_REASON,
    REVALIDATION_SEALS,
    DeviceLayout,
    LayoutResult,
    RealizedDevice,
    Revalidation,
    ReviewItem,
    WRequest,
)
from .coverage import check_stick_diagram_coverage
from .finger_candidates import finger_candidates
from .finger_geometry import finger_geometry
from .pattern_select import pattern_select
from .rows import compose_rows
from .slice_density import slice_density

_BLOCKS = (finger_candidates, pattern_select, finger_geometry, compose_rows)
_NO_SLICE = "no_usable_slice"


def _input_columns(layout_input):
    return {
        (DEVICE, F_DEVICE): {d.name: d for d in layout_input.devices},
        (GRAPH, F_PDK): {GRAPH_KEY: layout_input.pdk},
        (GRAPH, F_GROUPS_IN): {GRAPH_KEY: layout_input.matching_groups},
        (GRAPH, F_ROW_GROUPS): {GRAPH_KEY: layout_input.row_groups},
        (GRAPH, F_REJECTED): {GRAPH_KEY: tuple(sorted(layout_input.rejected_requests))},
        (GRAPH, F_PASSIVES): {GRAPH_KEY: tuple(sorted(layout_input.passives, key=lambda p: p.name))},
    }


def _point(d):
    return (d.kind, d.L_m, d.ID_A, d.gm_id, d.vds_V, d.vsb_V)


def _write_slices(snapshot, layout_input, memo):
    """(스냅샷, 이번에 계산했는지)."""
    keys_of = dict(layout_input.pdk.slice_width_keys)
    version = fp_of((memo.lut.fp, layout_input.pdk.slice_width_keys,
                     tuple((d.name,) + _point(d) for d in layout_input.devices)))
    if snapshot.block_version(WRITER_SLICES) == version:
        return snapshot, False
    by_point = {}
    out = {}
    for d in layout_input.devices:
        point = _point(d)
        if point not in by_point:
            by_point[point] = slice_density(memo, d, keys_of[d.kind])
        out[d.name] = by_point[point]
    return snapshot.write(WRITER_SLICES, version, {(DEVICE, F_SLICES): out}), True


def _review(groups, rebuilds):
    final = {r.gid: r for r in rebuilds}
    out = []
    for g in groups:
        if g.role not in CC_REQUIRED_ROLES or not (g.pattern is None and not g.pending):
            continue
        dx, dy = (final[g.gid].dx, final[g.gid].dy) if g.gid in final else (g.dx, g.dy)
        out.append(ReviewItem(g.gid, g.role, g.reason, dx, dy))
    return tuple(out)


def run_layout(layout_input, memo, previous=None):
    """레이아웃을 graph 필드로 실행하고 `LayoutResult` 를 돌려준다(`snapshot` = 다음 호출의 캐시)."""
    if memo.lut.fp != layout_input.pdk.source_fp:
        raise ValueError("run_layout: LUT memo 지문이 pdk.source_fp 와 다르다(다른 LUT 로 만든 PDK 폭 키)")
    snapshot = GraphSnapshot.empty(LY_WRITERS) if previous is None else previous.snapshot
    snapshot = snapshot.write(WRITER_INPUT, fp_of(layout_input), _input_columns(layout_input))
    snapshot, sliced = _write_slices(snapshot, layout_input, memo)
    computed = [WRITER_SLICES] if sliced else []
    for block in _BLOCKS:
        before = snapshot.block_version(block.name)
        snapshot = block(snapshot)
        if snapshot.block_version(block.name) != before:
            computed.append(block.name)

    slices = dict(snapshot.column(DEVICE, F_SLICES))
    fingers = dict(snapshot.column(DEVICE, F_FINGER))
    groups = snapshot.value(GRAPH, GRAPH_KEY, F_GROUPS)
    rows_layout = snapshot.value(GRAPH, GRAPH_KEY, F_ROWS)
    diffusion = snapshot.value(GRAPH, GRAPH_KEY, F_DIFFUSION)
    diffusion_of = {x.name: x for x in diffusion}
    per_device = {}
    for row in rows_layout.rows:
        for name, n_fingers in row.devices:
            per_device.setdefault(name, []).append((row.row_id, n_fingers))

    requests = [r for g in groups for r in g.w_requests]
    requests += [f.w_request for _, f in sorted(fingers.items()) if f.w_request is not None]
    requests += [WRequest(d.name, d.W_m, d.W_m, _NO_SLICE, None) for d in layout_input.devices if d.name not in fingers]
    requests = tuple(sorted(requests, key=lambda r: (r.device, r.reason)))
    requested = {r.device for r in requests}

    devices = []
    realized = []
    invariant = True
    for d in layout_input.devices:
        excluded = tuple((s.finger_w_key, s.reason) for s in slices[d.name] if s.reason)
        f = fingers.get(d.name)
        if f is None:
            invariant = False
            devices.append(DeviceLayout(d.name, None, None, (), d.W_m, None, None, None, None, None, None, None, None,
                                        excluded))
            continue
        placed = tuple(sorted(per_device.get(d.name, ())))
        invariant = invariant and sum(n for _, n in placed) == f.n_fingers
        invariant = invariant and (f.err_rel <= f.tol_effective or d.name in requested)
        devices.append(DeviceLayout(d.name, f.finger_w_m, f.n_fingers, placed, d.W_m, f.W_need_m, f.W_realized_m,
                                    f.err_rel, f.lower, f.upper, f.tol_effective, f.grid_dominated, f.origin, excluded))
        realized.append(RealizedDevice(d.name, d.kind, f.finger_w_key, f.finger_w_m, f.n_fingers, f.W_need_m,
                                       f.W_realized_m, d.ID_A, d.gm_id, d.L_m, d.vds_V, d.vsb_V, not d.diode, True,
                                       diffusion_of.get(d.name)))
    coverage = check_stick_diagram_coverage([d.name for d in layout_input.devices],
                                            {r.row_id: [n for n, _ in r.devices] for r in rows_layout.rows})
    revalidation = Revalidation(True, REVALIDATION_PENDING, REVALIDATION_SEALS, tuple(realized), REVALIDATION_CONSUMER,
                                REVALIDATION_PENDING_REASON)
    return LayoutResult(_review(groups, rows_layout.rebuilt_groups), tuple(devices), groups,
                        snapshot.value(GRAPH, GRAPH_KEY, F_DISPOSITIONS), rows_layout.rows, rows_layout.box,
                        rows_layout.fold_attempts, rows_layout.merge_decisions,
                        snapshot.value(GRAPH, GRAPH_KEY, F_FLOORPLAN), diffusion, coverage.ok, tuple(sorted(coverage.missing)),
                        requests, invariant, revalidation, tuple(computed), snapshot)
