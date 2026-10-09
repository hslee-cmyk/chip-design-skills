"""gm/ID 상한과 L 상한 -- 속도에서 (설계 41 §6.3, §6.4-4; D-SIb).

진입점: `speed_bounds(ctx, dominant, lengths, gm_id_lo) -> SpeedBounds`.

* **전제**: 보상 목표 `gbw_target_hz` 가 있어야 한다(없으면 비활성 `gbw_target_missing`). `pm_target_deg` 가 없으면 PM 하한 대신 2극점 근사의 경계 PM = atan(1) = 45°(`PM_FLOOR_DEG`: 비주극점이
  UGF 에 놓이는 f_np = GBW)를 쓴다 -- 비주극점이 UGF 아래로 내려가면 GBW 라는 양이 성립하지 않는 경계라 구조에서 나온 값이며, `SpeedBounds.pm_floor` 로 보고한다. 41 §6.3 은 PM 이 없으면 비활성이라 쓰지만
  그러면 gm/ID 상한이 LUT 정점(약반전, f_T ≈ 0)에 머물러 속도를 전혀 거르지 못해 출발점이 쓸모없다(설계 공백으로 보고).
* **비주극점 조건**: 2극점 근사에서 PM = atan(f_np / GBW) 이므로 PM ≥ PM_target 이려면 f_np ≥ GBW / tan(90° − PM) = GBW · tan(PM_target).
* **대상 노드**: gain 제약 전달 뷰의 극점 노드 중 주극점 노드(`dominant_node`)를 뺀 것 가운데 임피던스 등급이 '낮음'인 노드. 그 노드에 낮은 등급 단자를 주는 소자 --
  소스가 그 노드이거나(1/gm 단자: 캐스코드·입력쌍·팔로어) diode 연결(드레인 = 게이트 = 그 노드)인 MOS -- 는 f_T(gm/ID, L) ≥ f_np 여야 한다. 노드 극점은
  gm_c / C_node ≤ gm_c / Cgg_c = 2π f_T,c 라서 이 조건은 필요조건이다.
* **gm/ID 상한**: `ft_curve` 위에서 {g : f_T(g, L) ≥ f_np} 의 최댓값 -- f_T 는 gm/ID 가 높을수록(약반전) 떨어진다.
* **L 상한**(§6.4-4): f_T(gm/ID_lo, L) ≥ f_np 인 LUT L 앵커 중 최댓값. gm/ID_lo = 헤드룸 하한(없으면 곡선 최솟값).
* 곡선에서 f_np 에 닿는 gm/ID 가 없으면(전 구간 f_T < f_np) 자르지 않고 충돌 레코드로 남긴다(41 §6.6; gap = f_np / 곡선 최대 f_T).
"""
import dataclasses
import math

from ._helpers_curves import at_gm_id, hull
from .iv_curves import QUANTITY_FT
from .start_values import (
    PM_FLOOR_DEG,
    QUANTITY_GM_ID,
    QUANTITY_L,
    SIDE_HI,
    SRC_SPEED_FT,
    SRC_SPEED_L,
    WHY_NO_DOMINANT,
    WHY_NO_GBW,
    Bound,
    StartConflict,
)

_IMPEDANCE_LOW = "low"


@dataclasses.dataclass(frozen=True)
class SpeedBounds:
    """`bounds` = {소자: (Bound, ...)}(gm/ID 상한, L 상한), `conflicts`, `inactive` = ((경계 식, 사유), ...), `f_np_hz` = 필요 비주극점 주파수(비활성이면 None), `providers` = 대상 소자 이름 tuple,
    `pm_floor` = PM 목표가 없어 경계 PM 을 쓴 경우 True."""

    bounds: object
    conflicts: tuple
    inactive: tuple
    f_np_hz: object
    providers: tuple
    pm_floor: bool = False


def _providers(ctx, dominant):
    low = {p.net for p in ctx.transfer.pole_nodes if p.impedance == _IMPEDANCE_LOW and p.net not in dominant.nets}
    return tuple(d for d in ctx.devices if d.source in low or (d.drain == d.gate and d.drain in low))


def speed_bounds(ctx, dominant, lengths, gm_id_lo):
    if ctx.gbw_hz is None:
        return SpeedBounds({}, (), ((SRC_SPEED_FT, WHY_NO_GBW),), None, ())
    if ctx.transfer is None or not dominant.nets:
        return SpeedBounds({}, (), ((SRC_SPEED_FT, WHY_NO_DOMINANT),), None, ())
    pm = PM_FLOOR_DEG if ctx.pm_deg is None else ctx.pm_deg
    f_np = ctx.gbw_hz * math.tan(math.radians(pm))
    bounds, conflicts, names = {}, [], []
    for d in _providers(ctx, dominant):
        names.append(d.name)
        found = []
        bundle = ctx.curves.bundle_of(d.name, d.kind, lengths[d.name])
        if bundle is not None:
            curve = bundle[QUANTITY_FT]
            top = hull(curve.gm_id, curve.values, f_np, below=False)
            if top is None:
                conflicts.append(StartConflict(d.name, QUANTITY_GM_ID, ((SRC_SPEED_FT, f_np),), f_np / float(max(curve.values))))
            else:
                found.append(Bound(QUANTITY_GM_ID, SIDE_HI, SRC_SPEED_FT, top[1]))
        reach = []
        for L in ctx.curves.l_anchors(d.kind):
            anchor = ctx.curves.bundle_of(d.name, d.kind, L)
            if anchor is None:
                continue
            ft = anchor[QUANTITY_FT]
            g = min(max(gm_id_lo.get(d.name, float(min(ft.gm_id))), float(min(ft.gm_id))), float(max(ft.gm_id)))
            if at_gm_id(ft.gm_id, ft.values, g, log=True) >= f_np:
                reach.append(L)
        if reach:
            found.append(Bound(QUANTITY_L, SIDE_HI, SRC_SPEED_L, max(reach)))
        else:
            conflicts.append(StartConflict(d.name, QUANTITY_L, ((SRC_SPEED_L, f_np),), f_np))
        bounds[d.name] = tuple(found)
    return SpeedBounds(bounds, tuple(conflicts), (), f_np, tuple(names), ctx.pm_deg is None)
