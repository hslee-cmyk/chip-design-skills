"""L 상한·gm/ID 상한(면적 예산)과 gm/ID 하한(최소 폭) (설계 41 §6.4-5, 결정 11, 40 §7.1 면적 예산 출발점; D-SIc).

진입점: `area_bounds(ctx, currents, lengths, gm_id_lo) -> AreaBounds`.

**gm 이 고정된 전류 모델**: 1회차(`gm_id_lo`)의 소자 전류 I_k 에서 gm_k = I_k·gm/ID_lo,k 를 정하고, gm/ID = g 일 때 전류는 I_k(g) = gm_k / g 다(매크로 모델이 정하는 것은 gm 이고 전류는 gm/ID 에 반비례한다 --
전류를 고정하면 gm/ID 를 올릴 때 gm 이 따라 올라가 매크로의 UGF 를 깬다). 소자 폭 W(g) = I_k(g)·L / IDu(g, L), 면적 W·L = I_k(g)·L² / IDu(g, L)(IDu 는 gm/ID 가 높을수록 급히 떨어져 g·IDu 도 떨어진다 --
면적은 g 에 대해 증가하고 W 도 증가한다).

* **gm/ID 하한 -- 최소 폭**: W(g) ≥ W_min(PDK 최소 finger 폭 `min_finger_w_m`, W 하한 제약 S-18) 인 g 의 최솟값. 강반전(g 작음)에서는 같은 gm 이 아주 작은 W 로 나와 W_min 아래로 내려간다.
  예산과 무관하다.
* 예산 `area_search_m2 <= A` 가 선언된 회로에서만 활성이다(없으면 비활성 `constraint_not_declared`). **'나머지는 최소로 두고 k 가 가질 수 있는 최대'** 규약(41 §6.2 와 같다):
  A_j,min = gm_j·L_j² / (g_lo,j·IDu(g_lo,j, L_j))(g 가 가장 낮을 때 면적이 최소), 수동소자 최소 = 값이 정해진 소자의 값(없으면 θ 상자 하한) × 단위 면적,
  A_k,avail = A − Σ_{j≠k} A_j,min − A_passive,min.
  * **L 상한**: 41 식 L ≤ √(A·IDu/I) -- gm_k·L² / (g_lo,k·IDu(g_lo,k, L)) ≤ A_k,avail 인 LUT L 앵커 중 최댓값.
  * **gm/ID 상한**(U13 의 면적 출발점 -- U11 의 임시 `fit_to_area_budget`(예산을 넘는 시작점의 ln IDu 를 모두 같은 Δ만큼 옮기던 방식)을 대체한다): 선택된 L 에서
    gm_k·L² / (g·IDu(g, L)) ≤ A_k,avail 인 g 의 최댓값(마디 사이 선형 교차 `hull`).
* 상한(곡선 gm/ID 끝)까지 올려도 W < W_min 이면 충돌 레코드(`w_min_gm_id`, gap = ln(W_min/W_최대) 무차원)로 남기고 하한을 W 최대 마디로 닫는다(자르지 않는다).
* 소자 전류 I_k 를 모르면(매크로·전파가 정하지 못함) 그 소자는 경계를 만들지 않고 비활성 `stage_current_unavailable` 로 남는다.
* A_k,avail 이 최소 면적에도 못 미치면(예산 < 하한) 자르지 않고 충돌 레코드로 남긴다(41 §6.6 'A_est > 예산(보고만)'; 같은 사실의 정지 판정은 U9 `area_lower_bound` 의 몫).
출발값 전용(EP-7): 레이아웃 타당성(W 격자·nf)은 외층 제약 행이 판정한다.
"""
import dataclasses
import math

import numpy as np

from ._helpers_area import area_estimate
from ._helpers_curves import hull
from .iv_curves import QUANTITY_IDU
from .start_values import (
    QUANTITY_AREA,
    QUANTITY_GM_ID,
    QUANTITY_L,
    SIDE_HI,
    SIDE_LO,
    SRC_AREA_GM_ID,
    SRC_AREA_L,
    SRC_W_MIN,
    WHY_NO_CURRENT,
    WHY_NO_TARGET,
    Bound,
    StartConflict,
)


@dataclasses.dataclass(frozen=True)
class AreaBounds:
    """`bounds` = {소자: (Bound, ...)}(gm/ID 하한: 최소 폭, L 상한·gm/ID 상한: 면적), `conflicts`, `inactive` = ((경계 식, 사유), ...), `minimum_m2` = 추정 최소 면적(MOS 최소 합 + 수동소자 최소; 예산이 없으면 None)."""

    bounds: object
    conflicts: tuple
    inactive: tuple
    minimum_m2: object


def _per_amp(ctx, name, kind, L, currents, gm_id_lo):
    """gm = I·gm/ID_lo 일 때의 (gm/ID 마디 배열, IDu 마디 배열, gm). 전류를 모르면 None."""
    if currents.get(name) is None:
        return None
    bundle = ctx.curves.bundle_of(name, kind, L)
    curve = bundle[QUANTITY_IDU]
    return np.asarray(curve.gm_id, dtype=float), np.asarray(curve.values, dtype=float), currents[name] * gm_id_lo[name]


def area_bounds(ctx, currents, lengths, gm_id_lo):
    bounds, conflicts, inactive = {}, [], []
    for d in ctx.devices:
        nodes = _per_amp(ctx, d.name, d.kind, lengths[d.name], currents, gm_id_lo)
        if nodes is None:
            continue
        g, idu, gm = nodes
        width = gm * lengths[d.name] / (g * idu)                       # W(g) -- g·IDu 가 급히 떨어져 g 에 대해 증가한다
        low = hull(g, np.log(width), math.log(ctx.w_min_m), below=False)      # IDu 는 log 보간 -- log W 위에서 교차를 구한다
        if low is not None:
            bounds[d.name] = (Bound(QUANTITY_GM_ID, SIDE_LO, SRC_W_MIN, low[0]),)
        else:
            # gm/ID 를 곡선 상한까지 올려도 W < W_min -- 충돌 레코드로 남기고(41 §6.6) 요구 방향으로 닫는다: 하한 = W 가 가장 큰 마디. gap = ln(W_min/W_최대)(무차원, > 0)
            best = int(np.argmax(width))
            gap = math.log(ctx.w_min_m) - float(np.log(width[best]))
            conflicts.append(StartConflict(d.name, QUANTITY_GM_ID, ((SRC_W_MIN, float(g[best])),), gap))
            bounds[d.name] = (Bound(QUANTITY_GM_ID, SIDE_LO, SRC_W_MIN, float(g[best])),)
    if ctx.area_budget_m2 is None:
        return AreaBounds(bounds, (), ((SRC_AREA_L, WHY_NO_TARGET), (SRC_AREA_GM_ID, WHY_NO_TARGET)), None)
    inactive = [(SRC_AREA_GM_ID + ":" + d.name, WHY_NO_CURRENT) for d in ctx.devices if currents.get(d.name) is None]
    # 최소 면적: 소자는 gm/ID 하한(면적 최소)에서, 수동소자는 값이 선언되면 그 값 아니면 θ 상자 하한(`area_estimate` 와 같은 구성)
    low_values = {name: lo for name, (lo, _hi) in ctx.theta_bounds.items()}
    _total, per_device, passive = area_estimate(ctx, currents, gm_id_lo, lengths, low_values, low_values)
    minimum = {name: value for name, value in per_device.items() if value is not None}
    base = sum(minimum.values()) + passive
    for d in ctx.devices:
        if d.name not in minimum:
            continue
        avail = ctx.area_budget_m2 - (base - minimum[d.name])
        if not avail >= minimum[d.name]:
            conflicts.append(StartConflict(d.name, QUANTITY_AREA, (("area_budget", ctx.area_budget_m2), ("minimum_area", base)), base - ctx.area_budget_m2))
            continue
        gm = currents[d.name] * gm_id_lo[d.name]
        found = []
        reach = []
        for L in ctx.curves.l_anchors(d.kind):
            anchor = ctx.curves.bundle_of(d.name, d.kind, L)
            if anchor is not None and gm * L ** 2 / (gm_id_lo[d.name] * ctx.curves.value(anchor, QUANTITY_IDU, gm_id_lo[d.name])) <= avail:
                reach.append(L)
        if reach:
            found.append(Bound(QUANTITY_L, SIDE_HI, SRC_AREA_L, max(reach)))
        g, idu, gm_k = _per_amp(ctx, d.name, d.kind, lengths[d.name], currents, gm_id_lo)
        top = hull(g, gm_k * lengths[d.name] ** 2 / (g * idu), avail, below=True)
        if top is not None:
            found.append(Bound(QUANTITY_GM_ID, SIDE_HI, SRC_AREA_GM_ID, top[1]))
        bounds[d.name] = tuple(found) + bounds.get(d.name, ())
    return AreaBounds(bounds, tuple(conflicts), tuple(inactive), base)
