"""허용오차 표 공용 helper -- leave-one-out(LOO) 추정·셀 최댓값·L 방향 bin 상태·외부 bin 값·셀 조회
(`tol_v_table`·`tol_vdsat_table`·`midpoint_l_bin_checks` 가 같은 규칙을 쓰게 한 곳에 둔다, lut/CONTRACT.md 5절·5.1·5.2).

* LOO(축 a, 내부 격자점 x_j, 이웃 x_{j-1}·x_{j+1}, H = x_{j+1} − x_{j-1}, t = (x_j − x_{j-1})/H): 선형 `y_{j-1} + t·(y_{j+1} − y_{j-1})`,
  Hermite 축이면 두 이웃 기울기 자료가 다 있을 때 2점 cubic-Hermite(운영 보간과 같은 방법, DEC-87). 차수 p = 조건 수
  (선형 2, Hermite 4), Hermite 미분 = 4 − 1 = 3 -- Richardson 환산 ÷ 2^p 에 쓴다(`LINEAR_ORDER` 등).
* L 축: 앵커 i 의 양옆 앵커가 모두 i 와 같은 모델 bin 일 때만(bin 안 내부 앵커). 앵커 2개 bin 은 외부 값(검증 중점)을 받는다.
* 셀 = (L 앵커, VDS 격자). 셀 값 = 그 셀 안 점(VGS·VS·축)의 최댓값, 정의된 점이 없으면 None.
"""
import bisect

import numpy as np

from ._helpers_anchor import l_position
from ._helpers_interp import HERMITE_CONDITIONS, LINEAR_CONDITIONS, hermite
from .axis_guard import check_axes
from .lut_types import AXES

LINEAR_ORDER = len(LINEAR_CONDITIONS)
HERMITE_ORDER = len(HERMITE_CONDITIONS)
HERMITE_SLOPE_ORDER = HERMITE_ORDER - 1


def l_interior(l_bins, n):
    """앵커마다 bin 안 내부(양옆 앵커가 같은 bin) 여부 tuple. 지도가 없으면 모두 거짓."""
    if not l_bins.bins:
        return (False,) * n
    ab = l_bins.anchor_bin
    return tuple(0 < i < n - 1 and ab[i - 1] == ab[i] == ab[i + 1] for i in range(n))


def external_by_model(l_bin_checks, fields, table_name):
    """`l_bin_checks` ((model, 값...), ...) -> {model: {필드: 값 또는 None}} (`fields` = 값 칸 이름 순서).
    같은 model 두 번 -> ValueError."""
    out = {}
    for row in l_bin_checks:
        model, values = row[0], row[1:]
        if model in out:
            raise ValueError("%s: l_bin_checks 에 bin %r 가 두 번 있다" % (table_name, model))
        out[model] = {f: None if v is None else float(v) for f, v in zip(fields, values)}
    return out


def l_loo_report(l_bins, interior, external, table_name):
    """(앵커별 상태 tuple, bin 별 (model, 앵커 index tuple, 상태) tuple, {앵커 index: 외부 값 dict}).

    bin 상태: 내부 앵커 있음(앵커 3개 이상) "computed", 앵커 1개 "single_point"(그 bin 안 L 보간 자체가 없다 --
    거부 `lut_l_bin_unbracketed`), 그 밖(앵커 2개) 외부 값이 있으면 "external", 없으면 "missing_external".
    외부 값은 앵커 2개 bin 에만 받는다 -- 다른 bin·지도에 없는 model 이면 ValueError(조용히 버리지 않음).
    """
    if not l_bins.bins:
        if external:
            raise ValueError("%s: bin 지도가 없는 슬라이스에 l_bin_checks 가 주어졌다: %r" % (table_name, sorted(external)))
        return ("bins_unavailable",) * len(interior), (), {}
    ab = l_bins.anchor_bin
    has_interior = {b for b, inner in zip(ab, interior) if inner}
    status, per_bin, ext_rows = {}, [], {}
    for b in sorted(set(ab)):
        model = l_bins.bins[b].model
        members = tuple(i for i, m in enumerate(ab) if m == b)
        if b in has_interior:
            status[b] = "computed"
        elif len(members) <= 1:
            status[b] = "single_point"
        elif model in external:
            status[b] = "external"
            ext_rows.update({i: external[model] for i in members})
        else:
            status[b] = "missing_external"
        per_bin.append((model, members, status[b]))
    allowed = {model for model, _, st in per_bin if st == "external"}
    unused = sorted(set(external) - allowed)
    if unused:
        raise ValueError("%s: l_bin_checks 는 앵커 2개 bin 에만 준다 -- 해당 없는 bin: %r" % (table_name, unused))
    anchor_status = {"computed": "bin_edge", "single_point": "bin_single_point", "external": "bin_external",
                     "missing_external": "bin_missing_external"}
    per_anchor = tuple("in_bin_interior" if inner else anchor_status[status[b]] for b, inner in zip(ab, interior))
    return per_anchor, tuple(per_bin), ext_rows


def _pairs(arr, axis):
    """축 `axis` 방향 (이전 이웃, 다음 이웃) 보기(첫 축으로 옮긴 모양, 길이 n − 2)."""
    a = np.moveaxis(arr, axis, 0)
    return a[:-2], a[2:]


def loo_estimate(values, slope, slope_ok, axis, grid, hermite_axis):
    """축 `axis` 내부 격자점의 LOO 추정과 점마다 차수 p (첫 축으로 옮긴 모양, 길이 n − 2).

    `hermite_axis` 이고 두 이웃의 기울기 자료(`slope_ok`)가 다 있으면 Hermite(차수 HERMITE_ORDER), 아니면 선형(LINEAR_ORDER).
    선형 축이면 `slope`·`slope_ok` 는 쓰지 않는다(None 가능)."""
    x = np.asarray(grid, dtype=float)
    shape = (-1,) + (1,) * (values.ndim - 1)
    h = (x[2:] - x[:-2]).reshape(shape)
    t = ((x[1:-1] - x[:-2]) / (x[2:] - x[:-2])).reshape(shape)
    y0, y1 = _pairs(values, axis)
    linear = y0 + t * (y1 - y0)
    if not hermite_axis:
        return linear, np.full(linear.shape, LINEAR_ORDER)
    m0, m1 = _pairs(slope, axis)
    ok0, ok1 = _pairs(slope_ok, axis)
    use = ok0 & ok1
    with np.errstate(invalid="ignore", over="ignore"):
        herm, _ = hermite(y0, y1, m0, m1, h, t)
    return np.where(use, herm, linear), np.where(use, HERMITE_ORDER, LINEAR_ORDER)


def cell_max(per_point):
    """점별 값 배열([L, VGS, VDS, VS], 정의 없음 = NaN) -> [L, VDS] 셀 최댓값(정의 없음 = NaN)."""
    per_cell = np.moveaxis(per_point, (AXES.index("L"), AXES.index("VDS")), (0, 1))
    flat = per_cell.reshape(per_cell.shape[0], per_cell.shape[1], -1)
    out = np.full(flat.shape[:-1], np.nan)
    has = ~np.isnan(flat).all(axis=-1)
    out[has] = np.nanmax(flat[has], axis=-1)
    return out


def branch_targets(g, on_curve):
    """(곡선 index, VGS index) 목표 쌍: 정점 이후이고 오른쪽 모든 점보다 gm/ID 가 큰 점(그 VGS 가 그 곡선의 강반전 분지 해).
    `g` 모양 (곡선, VGS), `on_curve` 모양 (곡선,)."""
    right = np.full(g.shape, -np.inf)
    right[:, :-1] = np.maximum.accumulate(g[:, :0:-1], axis=1)[:, ::-1]
    cols = np.arange(g.shape[1])
    mask = (g > right) & (cols[None, :] >= np.argmax(g, axis=1)[:, None]) & on_curve[:, None]
    return np.nonzero(mask)


def with_external(value, ext):
    """셀 값과 외부 bin 값의 최댓값. 셀 값이 None(그 셀에 켜진 격자점 없음)이면 None 그대로."""
    if value is None or ext is None:
        return value
    return max(value, ext)


def opt(x):
    """NaN·None -> None, 그 밖 float."""
    return None if x is None or np.isnan(x) else float(x)


def table_at(table, field, L, vds, context):
    """표 `table`(속성 L_anchors·l_bins·vds_grid·cells)의 조회점 (L, vds) 값: L 이 앵커면 그 행, 같은 bin 보간이면 양옆
    앵커 두 행(CONTRACT 4.0), VDS 칸 [k, k+1] (`bisect_right − 1`, 마지막 격자점은 마지막 칸) -- 그 셀들의 `field` 중 정의된
    값의 최댓값(없으면 None). 실패: L 위치·VDS 축 -> `SealViolationError`(context 를 detail 에)."""
    lo, hi, _ = l_position(table.L_anchors, table.l_bins, L, context)
    vds = float(vds)
    check_axes((table.vds_grid,), (AXES[2],), (vds,), context)
    k = min(bisect.bisect_right(table.vds_grid, vds) - 1, len(table.vds_grid) - 2)
    vals = [getattr(table.cells[i][b], field) for i in sorted({lo, hi}) for b in (k, k + 1)]
    vals = [v for v in vals if v is not None]
    return max(vals) if vals else None
