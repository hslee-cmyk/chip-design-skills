"""gm/ID 구간의 LUT 역산 정의역 -- 커널이 쓸 수 있는 전류밀도 창 (설계 41 §6.2 '곡선', lut/CONTRACT.md 3.1 `vgs_for_current_density`; D-SIa).

진입점: `domain_bounds(ctx, lengths, vds_budget) -> DomainBounds`.

쓰기 소자의 반전 좌표 ln IDu 는 커널이 `vgs_for_current_density` 로 VGS 를 되구한다. 그 역산은 (L, VDS, VSB) 곡선의 강반전 분지에서 **ln ID 가 엄격히 증가하는 첫 구간 [정점, 단조 끝]** 안의
목표만 받는다(밖은 `lut_target_out_of_range`). 곡선 정점의 위치는 VDS 에 따라 움직이므로(약반전 쪽 끝 = 정점 IDu) 출발 구간은 소자가 놓일 수 있는 VDS 들에서 모두 역산되는 창이어야 한다:

  ln IDu ∈ [ max_VDS ln IDu(정점), min_VDS ln IDu(단조 끝) ]

VDS 탐침 = 그 gm/ID 마디의 포화 경계 VDS(VDSAT + tol_vdsat 을 격자 위로 올림 -- 포화에 머물 수 있는 가장 낮은 VDS)와 헤드룸 VDS 예산(`headroom_bounds` 의 `budgets[(소자, vds)]` 를 레일 범위로
자른 값의 격자점) -- 소자가 놓일 수 있는 VDS 범위의 양 끝이다. 기준 점 곡선의 gm/ID 마디마다 그 마디의 ln IDu 가 두 탐침의 창 안이면 쓸 수 있는 마디이고, 쓸 수 있는 마디의 [최소 gm/ID, 최대 gm/ID] 가
`DomainBounds.bounds` 다. 출발 점이 정점 근처의 약반전 극단이나 VGS 격자 끝의
강반전 극단에 놓여 커널의 DC 풀이가 첫 평가에서 `lut_query_failed` 로 죽는 것을 막는 구조적 구간이다(경험 상수가 아니다 -- 같은 LUT 역산이 정의역을 정한다).
곡선이 정의되지 않은 탐침은 건너뛰고(기록 없음), 창이 비면 자르지 않고 충돌 레코드로 남긴다(41 §6.6).
"""
import dataclasses
import math

import numpy as np

from .iv_curves import QUANTITY_IDU, QUANTITY_VDSAT
from .start_values import QUANTITY_GM_ID, SIDE_HI, SIDE_LO, SRC_LUT_DOMAIN, Bound, StartConflict


@dataclasses.dataclass(frozen=True)
class DomainBounds:
    """`bounds` = {소자: (Bound, ...)}(gm/ID 하한·상한), `conflicts` = StartConflict tuple."""

    bounds: object
    conflicts: tuple


def _monotone_end(values):
    """정점(0 번 마디)에서 시작해 IDu 가 엄격히 증가하는 마지막 마디 index."""
    end = 0
    while end + 1 < values.size and values[end + 1] > values[end]:
        end += 1
    return end


def _window(ctx, cache, kind, L, vds):
    """(kind, L, VDS) 곡선의 ln IDu 역산 창 (정점 ln IDu, 단조 끝 ln IDu). 곡선이 정의되지 않으면 None. 같은 인자는 한 번만."""
    key = (kind, L, vds)
    if key not in cache:
        curve = ctx.curves.curve(QUANTITY_IDU, kind, L, vds)
        if curve is None:
            cache[key] = None
        else:
            values = np.asarray(curve.values, dtype=float)
            cache[key] = (math.log(values[0]), math.log(values[_monotone_end(values)]))
    return cache[key]


def domain_bounds(ctx, lengths, vds_budget):
    bounds, conflicts, cache = {}, [], {}
    for d in ctx.devices:
        L = lengths[d.name]
        ref = ctx.curves.bundle_of(d.name, d.kind, L)
        if ref is None:
            continue
        curve, vdsat = ref[QUANTITY_IDU], ref[QUANTITY_VDSAT]
        top = ctx.curves.snap_vds(d.kind, min(vds_budget[d.name], max(ctx.curves.vds_grid(d.kind)))) if vds_budget.get(d.name) is not None else None
        usable = []
        for j in range(len(curve.gm_id)):
            # 그 gm/ID 의 포화 경계 VDS(VDSAT + tol_vdsat, 격자 위로 올림) -- 그보다 낮은 VDS 에서는 소자가 포화에 있지 않으므로 탐침이 아니다
            lowest = ctx.curves.snap_up_vds(d.kind, float(vdsat.values[j]) + ctx.curves.tol_vdsat(d.kind, L, vdsat.vds))
            probes = {lowest} | ({top} if top is not None and top >= lowest else set())
            windows = [_window(ctx, cache, d.kind, L, v) for v in sorted(probes)]
            if any(w is None for w in windows):
                continue
            ln_idu = math.log(float(curve.values[j]))
            if max(w[0] for w in windows) <= ln_idu <= min(w[1] for w in windows):
                usable.append(float(curve.gm_id[j]))
        if usable:
            bounds[d.name] = (Bound(QUANTITY_GM_ID, SIDE_LO, SRC_LUT_DOMAIN, min(usable)), Bound(QUANTITY_GM_ID, SIDE_HI, SRC_LUT_DOMAIN, max(usable)))
        else:
            conflicts.append(StartConflict(d.name, QUANTITY_GM_ID, ((SRC_LUT_DOMAIN, math.nan),), math.nan))
    return DomainBounds(bounds, tuple(conflicts))
