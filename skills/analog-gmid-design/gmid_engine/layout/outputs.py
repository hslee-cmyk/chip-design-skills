"""MOD7 레이아웃 필드 -> 출력 계약 파생 항목 (계획 N3.17 출력 계약, 사용자 결정 2026-10-07 Q4·Q8, 설계 40 v1.6 §2.4.7 `LayoutResult` 행).

진입점: `layout_outputs(snapshot) -> LayoutOutputs`.

`snapshot` = `run_layout` 이 레이아웃 `ly_*` 필드를 쓴 설계점 스냅샷(`LayoutResult.snapshot`). 값은 필드에서만 읽고 저장하지 않는다(반환값):
* `review_needed`(맨 앞): 배치 못 한 차동쌍·branch_symmetric(LY5 는 즉시 완화하지 않고 판정을 MOD8 에 맡긴다) -- `ly_groups` 중
  `CC_REQUIRED_ROLES` 이고 패턴 없음·응답 대기 아님, dx·dy 는 `ly_rows.rebuilt_groups` 의 최종 값(없으면 그룹 값).
* `devices`: 소자 이름순 `DeviceLayout` -- `ly_device`·`ly_finger`·`ly_slices`(제외 슬라이스)·`ly_rows`(행별 finger 수).
* coverage(`check_stick_diagram_coverage`): `ly_device` 이름 전부가 `ly_rows` 물리 행에 있는지.
* `w_requests`: 그룹 요청(`ly_groups`) + finger_quantization(`ly_finger`) + `ly_finger` 값이 없는 소자마다 `no_usable_slice`.
* `w_invariant_ok`: 모든 소자가 `ly_finger` 를 갖고 행별 finger 합 == nf 이고 (오차 <= 실효 허용오차 또는 그 소자의 W_request 있음).
* `revalidation`: W_request 유무와 관계없이 required, status 는 늘 pending_wiring(소비 결과는 MOD8 `convergence.ConvergedPoint`).
"""
from ._ly_fields import DEVICE, F_DEVICE, F_DIFFUSION, F_FINGER, F_GROUPS, F_ROWS, F_SLICES, GRAPH, GRAPH_KEY
from .contract_input import CC_REQUIRED_ROLES
from .contract_output import (
    REVALIDATION_CONSUMER,
    REVALIDATION_PENDING,
    REVALIDATION_PENDING_REASON,
    REVALIDATION_SEALS,
    DeviceLayout,
    LayoutOutputs,
    RealizedDevice,
    Revalidation,
    ReviewItem,
    WRequest,
)
from .coverage import check_stick_diagram_coverage

_NO_SLICE = "no_usable_slice"


def _review(groups, rebuilds):
    final = {r.gid: r for r in rebuilds}
    out = []
    for g in groups:
        if g.role not in CC_REQUIRED_ROLES or not (g.pattern is None and not g.pending):
            continue
        dx, dy = (final[g.gid].dx, final[g.gid].dy) if g.gid in final else (g.dx, g.dy)
        out.append(ReviewItem(g.gid, g.role, g.reason, dx, dy))
    return tuple(out)


def layout_outputs(snapshot):
    devices_in = snapshot.column(DEVICE, F_DEVICE)
    slices = dict(snapshot.column(DEVICE, F_SLICES))
    fingers = dict(snapshot.column(DEVICE, F_FINGER))
    groups = snapshot.value(GRAPH, GRAPH_KEY, F_GROUPS)
    rows_layout = snapshot.value(GRAPH, GRAPH_KEY, F_ROWS)
    diffusion_of = {x.name: x for x in snapshot.value(GRAPH, GRAPH_KEY, F_DIFFUSION)}
    per_device = {}
    for row in rows_layout.rows:
        for name, n_fingers in row.devices:
            per_device.setdefault(name, []).append((row.row_id, n_fingers))

    requests = [r for g in groups for r in g.w_requests]
    requests += [f.w_request for _, f in sorted(fingers.items()) if f.w_request is not None]
    requests += [WRequest(name, d.W_m, d.W_m, _NO_SLICE, None) for name, d in devices_in if name not in fingers]
    requests = tuple(sorted(requests, key=lambda r: (r.device, r.reason)))
    requested = {r.device for r in requests}

    devices = []
    realized = []
    invariant = True
    for name, d in devices_in:
        excluded = tuple((s.finger_w_key, s.reason) for s in slices[name] if s.reason)
        f = fingers.get(name)
        if f is None:
            invariant = False
            devices.append(DeviceLayout(name, None, None, (), d.W_m, None, None, None, None, None, None, None, None, excluded))
            continue
        placed = tuple(sorted(per_device.get(name, ())))
        invariant = invariant and sum(n for _, n in placed) == f.n_fingers
        invariant = invariant and (f.err_rel <= f.tol_effective or name in requested)
        devices.append(DeviceLayout(name, f.finger_w_m, f.n_fingers, placed, d.W_m, f.W_need_m, f.W_realized_m,
                                    f.err_rel, f.lower, f.upper, f.tol_effective, f.grid_dominated, f.origin, excluded))
        realized.append(RealizedDevice(name, d.kind, f.finger_w_key, f.finger_w_m, f.n_fingers, f.W_need_m,
                                       f.W_realized_m, d.ID_A, d.gm_id, d.L_m, d.vds_V, d.vsb_V, not d.diode, True,
                                       diffusion_of.get(name)))
    coverage = check_stick_diagram_coverage([name for name, _ in devices_in],
                                            {r.row_id: [n for n, _ in r.devices] for r in rows_layout.rows})
    revalidation = Revalidation(True, REVALIDATION_PENDING, REVALIDATION_SEALS, tuple(realized), REVALIDATION_CONSUMER,
                                REVALIDATION_PENDING_REASON)
    return LayoutOutputs(_review(groups, rows_layout.rebuilt_groups), tuple(devices), coverage.ok, tuple(sorted(coverage.missing)),
                         requests, invariant, revalidation)
