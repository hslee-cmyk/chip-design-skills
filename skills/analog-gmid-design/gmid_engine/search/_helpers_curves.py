"""출발 구간 공용 곡선 helper -- U3 gm/ID 축 곡선(`ft_curve`·`intrinsic_gain_curve`·`vdsat_curve`·`idu_curve`)을 읽고 보간한다 (설계 41 §6, `iv_*` 가 함께 쓴다;
40 §2.4.7 `CurveBook` 행 v1.9.1 D10 -- 옛 `CurveBook` 객체를 없애고 LUT 파생은 LUT memo 함수 `lut.derived`, 소자 동작점은 S0 수준 필드 `device: start.point`).

곡선 읽기 함수는 출발 구간 블록의 작업 값 `v`(`StartView` -- `memo`·`w_keys`·`points` 칸)를 첫 인자로 받는다. 상태를 담지 않는다: 곡선은 `LutMemo` curve 영역이,
기준 VDS·tol_vdsat·엣지 비용은 LUT 파생(`lut.derived`)이 memo 한다.

* `_curve_of(v, quantity, kind, L, vds=None, vsb=None)` -> `GmIdAxisCurve` | None: vds 를 안 주면 VDS 격자 중 엣지 비용 VDS 이상에서 처음 정의된 곡선, vsb 를 안 주면 첫 VS 격자점.
* `_ref_vds(v, kind, L)`: (kind, L) 의 기준 VDS(포화 경계 이상 격자점 중 vdsat 곡선이 처음 정의된 점) -- `lut.derived("reference_vds")`. 없으면 None.
* `curve_bundle(v, kind, L, vds=None, vsb=None)` -> {양: 곡선} | None, `curve_bundle_of(v, name, kind, L)` -> 소자 동작점(`v.points`)의 묶음(없거나 정의 안 되면 기준 점 묶음).
* `edge_cost(v, kind)`(`lut.derived("edge_costs")`), `tol_vdsat(v, kind, L, vds)`(`lut.derived("tol_vdsat_max")`), `slice_of`·`l_anchors`·`vds_grid`·`vsb_ref`·`snap_vds`·`snap_up_vds`.
* `curve_value(bundle, quantity, g)`(idu·ft 는 log 보간, 나머지는 선형, `QUANTITY_VGS` 는 VGS 마디), `curve_range(bundle)` = 분지 gm/ID (최솟값, 최댓값).
* `_at_gm_id(gm_id, values, g, log=False)`: 곡선 마디 값을 gm/ID = g 에서 선형(또는 log) 보간. 마디 gm/ID 는 분지에서 내려가는 순서(`GmIdAxisCurve`), 정의역 밖은 끝 값.
  비단조 곡선(중반전 상승)은 g 를 품는 칸 중 가장 오른쪽(강반전 쪽)에서 읽는다(lut 3절).
* `hull(gm_id, values, level, below=True)`: {g : values(g) ≤ level}(below) 또는 {g : values(g) ≥ level} 의 gm/ID 폭 (최소, 최대). 마디 사이는 선형 교차점이고
  비단조 곡선(격자 전용 칸)도 모든 칸을 센다. 비면 None -- 단조 가정으로 역산하지 않는 이유다(41 §4.1 해법 매핑).
"""
import math

import numpy as np

from gmid_engine.core import SchemaRejectedError, SealViolationError
from gmid_engine.lut import derived, ft_curve, idu_curve, intrinsic_gain_curve, vdsat_curve

QUANTITY_FT = "ft"
QUANTITY_GAIN = "intrinsic_gain"
QUANTITY_VDSAT = "vdsat"
QUANTITY_IDU = "idu"
QUANTITY_VGS = "vgs"
_CURVE_FN = ((QUANTITY_FT, ft_curve), (QUANTITY_GAIN, intrinsic_gain_curve), (QUANTITY_VDSAT, vdsat_curve), (QUANTITY_IDU, idu_curve))
_UNDEFINED = (SealViolationError, SchemaRejectedError, KeyError, ValueError)
_LOG_QUANTITIES = (QUANTITY_FT, QUANTITY_IDU)


def _at_gm_id(gm_id, values, g, log=False):
    xs = np.asarray(gm_id, dtype=float)
    ys = np.asarray(values, dtype=float)
    if log:
        ys = np.log(ys)
    # 가장 오른쪽(VGS 가 큰, 강반전 쪽) 마디 칸에서 보간한다 -- lut 3절 분지 규칙(`vgs_for_gm_id`)과 같다. 단조 곡선이면 칸이 하나뿐이라 선형 보간과 같고,
    # 중반전에서 gm/ID 가 한 번 올라가는 곡선(pmos)에서는 g 가 여러 칸에 있어도 강반전 쪽 값을 읽는다(np.interp 는 단조를 가정해 엉뚱한 칸을 읽는다).
    a, b = xs[:-1], xs[1:]
    hit = np.flatnonzero(((a - g) * (b - g) <= 0) & (a != b))
    if hit.size:
        j = int(hit[-1])
        out = ys[j] + (g - a[j]) / (b[j] - a[j]) * (ys[j + 1] - ys[j])
    else:                                              # 정의역 밖 -- 끝 값(g 가 최대 gm/ID 보다 크면 그 마디, 작으면 마지막 마디)
        out = ys[int(np.argmax(xs))] if g > xs.max() else ys[-1]
    return float(math.exp(out)) if log else float(out)


def hull(gm_id, values, level, below=True):
    g = np.asarray(gm_id, dtype=float)
    v = np.asarray(values, dtype=float)
    ok = (v <= level) if below else (v >= level)
    points = []
    for j in range(g.size):
        if ok[j]:
            points.append(float(g[j]))
        if j + 1 < g.size and ok[j] != ok[j + 1] and v[j + 1] != v[j]:
            t = (level - v[j]) / (v[j + 1] - v[j])
            points.append(float(g[j] + t * (g[j + 1] - g[j])))
    return (min(points), max(points)) if points else None


# ---------------------------------------------------------------- LUT 격자
def slice_of(v, kind):
    return v.memo.lut.slice_map[(kind, v.w_keys[kind])]


def l_anchors(v, kind):
    return tuple(float(a) for a in slice_of(v, kind).grids[0])


def _vds_grid(v, kind):
    return tuple(float(a) for a in slice_of(v, kind).grids[2])


def _vsb_ref(v, kind):
    return float(slice_of(v, kind).grids[3][0])


def edge_cost(v, kind):
    return derived(v.memo, "edge_costs", kind, v.w_keys[kind])


def snap_vds(v, kind, target):
    """LUT VDS 격자 중 `target` 에 가장 가까운 점(같으면 큰 쪽)."""
    grid = _vds_grid(v, kind)
    return min(grid, key=lambda x: (abs(x - target), -x))


def tol_vdsat(v, kind, L, vds):
    """VDSAT 허용오차 tol_vdsat(L, VDS 칸) -- L 을 감싸는 두 앵커와 VDS 가 든 격자 칸 중 정의된 것의 최댓값(보수). 표를 못 만들면 0."""
    return derived(v.memo, "tol_vdsat_max", kind, v.w_keys[kind], float(L), float(vds))


# ---------------------------------------------------------------- 곡선
def _try(v, fn, kind, L, vds, vsb):
    try:
        return fn(v.memo, kind, v.w_keys[kind], float(L), float(vds), float(vsb))
    except _UNDEFINED:
        return None


def _curve_of(v, quantity, kind, L, vds=None, vsb=None):
    """`GmIdAxisCurve` 또는 None(정의 안 됨). vds 를 안 주면 기준 VDS 부터 위 격자점으로 올리며 처음 정의된 곡선."""
    vsb = _vsb_ref(v, kind) if vsb is None else vsb
    fn = dict(_CURVE_FN)[quantity]
    if vds is not None:
        return _try(v, fn, kind, L, vds, vsb)
    floor = edge_cost(v, kind).vds_min_v
    for x in _vds_grid(v, kind):
        if x < floor:
            continue
        found = _try(v, fn, kind, L, x, vsb)
        if found is not None:
            return found
    return None


def _ref_vds(v, kind, L):
    """(kind, L) 의 기준 VDS: vdsat 곡선이 처음 정의된 포화 경계 이상 격자점. 없으면 None."""
    return derived(v.memo, "reference_vds", kind, v.w_keys[kind], float(L))


def curve_bundle(v, kind, L, vds=None, vsb=None):
    """같은 (L, VDS, VSB) 의 곡선 묶음 {양: GmIdAxisCurve}. 하나라도 정의되지 않으면 None. (vds, vsb) 를 안 주면 기준 점(포화 경계 VDS, 첫 VS 격자점)."""
    vds = _ref_vds(v, kind, L) if vds is None else vds
    if vds is None:
        return None
    out = {}
    for quantity, _fn in _CURVE_FN:
        curve = _curve_of(v, quantity, kind, L, vds, vsb)
        if curve is None:
            return None
        out[quantity] = curve
    return out


def curve_bundle_of(v, name, kind, L):
    """소자 `name` 의 동작점(`v.points`)에서의 곡선 묶음. 동작점이 없거나 그 점에서 곡선이 정의되지 않으면 기준 점 묶음."""
    point = v.points.get(name)
    found = None if point is None else curve_bundle(v, kind, L, point[0], point[1])
    return curve_bundle(v, kind, L) if found is None else found


# ---------------------------------------------------------------- 값 읽기
def curve_value(bundle, quantity, g):
    """묶음의 `quantity` 를 gm/ID = g 에서 읽는다(idu·ft 는 log 보간, 나머지는 선형, QUANTITY_VGS 는 VGS 마디)."""
    if quantity == QUANTITY_VGS:
        curve = bundle[QUANTITY_FT]
        return _at_gm_id(curve.gm_id, curve.vgs, g)
    curve = bundle[quantity]
    return _at_gm_id(curve.gm_id, curve.values, g, log=quantity in _LOG_QUANTITIES)
