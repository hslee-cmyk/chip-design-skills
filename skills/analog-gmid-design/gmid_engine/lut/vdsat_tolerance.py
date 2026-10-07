"""VDsat 허용오차 표 -- VDSAT 열 leave-one-out(운영 보간과 같은 방법 = 모든 축 선형) 오차의 Richardson 환산, 셀((kind, w_key,
L 앵커, VDS))별 (lut/CONTRACT.md 5.2, r6; sizing 계약 12절 O1 (b) `tol_VDsat`).

진입점: `tol_vdsat_table`.

* tol_V 표(5절)와 같은 틀(`_helpers_loo`): 축 a 의 내부 격자점을 빼고 두 이웃의 **선형** 추정(운영 `vdsat` 보간과 같은 방법 --
  VDSAT 은 모든 축 선형, 4.3)과 저장값의 차 |VDSAT_loo − VDSAT|. 점 조건 = 그 점과 축 방향 두 이웃이 열 출처 표의 on_mask
  ((ID > 0) & (GM > 0), 표에 ID·GM 이 없으면 모든 점). L 축은 같은 bin 안 내부 앵커만.
* Richardson: 선형 값 보간 차수 p = 조건 수 2 → 셀 후보 = LOO / 2^2(`LOO_ORDERS`, 네 축 모두). 환산 전 최댓값도 셀에 둔다.
* 앵커 2개 bin: 외부 값 `l_bin_checks = ((model, vdsat_v), ...)`(V, 환산 안 함; vdsat_v = VDS 격자점마다의 수열 또는 수 하나 --
  셀 (앵커, VDS_k) 에 k 번째 값). None(기본) = 검증 중점 파일 값
  (`midpoint_l_bin_checks` 의 `vdsat_v`), `()` = 없음 -- 받지 못한 bin 은 "missing_external" 로 남긴다.
* 열 출처는 `column_source`(슬라이스 열 또는 같은 폭 키의 기준 LUT 열, 없으면 `lut_column_unavailable`).
"""
import numpy as np

from ._helpers_columns import column_source
from ._helpers_loo import (
    LINEAR_ORDER,
    cell_max,
    external_by_model,
    l_interior,
    l_loo_report,
    loo_estimate,
    opt,
    per_vds,
    table_at,
    with_external,
)
from .lut_types import AXES, TOL_VDSAT_METRICS, TolVdsatCell
from .midpoint_checks import midpoint_l_bin_checks

LOO_ORDERS = tuple(("vdsat", axis, "linear", LINEAR_ORDER) for axis in sorted(AXES))
_EXTERNAL_FIELDS = ("vdsat_v",)


class TolVdsatTable:
    """(kind, w_key) 의 VDsat 허용오차 표. `cells[i_L][i_vds]` = TolVdsatCell, 축은 `L_anchors`·`vds_grid`(열 출처 표의 축).

    `origin`: 열 출처("slice"·"cap_table"). `l_bins`·`l_loo`·`l_loo_bins`: tol_V 표와 같은 뜻(열 출처 표의 bin 지도).
    `loo_orders`: ((지표, 축, 방법, p, 2^-p), ...). `l_bin_checks`: 실제로 쓴 외부 값((model, vdsat_v), ...).
    """

    def __init__(self, kind, w_key, origin, L_anchors, vds_grid, cells, l_bins, l_loo, l_loo_bins, loo_orders,
                 l_bin_checks):
        self.kind = kind
        self.w_key = w_key
        self.origin = origin
        self.L_anchors = L_anchors
        self.vds_grid = vds_grid
        self.cells = cells
        self.l_bins = l_bins
        self.l_loo = l_loo
        self.l_loo_bins = l_loo_bins
        self.loo_orders = loo_orders
        self.l_bin_checks = l_bin_checks

    def at(self, L, vds, metric="vdsat"):
        """조회점 (L, vds) 의 tol_VDsat(V) -- `TolVTable.at` 와 같은 행·칸 규칙(`table_at`), 정의된 값이 없으면 None.

        실패: `metric` 이 `TOL_VDSAT_METRICS` 밖 -> `ValueError`, L 위치·VDS 축 -> `SealViolationError`(table "tol_vdsat").
        """
        if metric not in TOL_VDSAT_METRICS:
            raise ValueError("TolVdsatTable.at: metric 은 %s 중 하나" % (TOL_VDSAT_METRICS,))
        context = (("kind", self.kind), ("table", "tol_vdsat"), ("w_key", self.w_key))
        return table_at(self, metric + "_v", L, vds, context)


def _loo_cells(values, on_mask, grids, interior):
    """([L, VDS] 환산 셀 최댓값, 환산 전 셀 최댓값) -- 축마다 선형 LOO, 점 조건 = 그 점·두 이웃 on, L 은 bin 안 내부만."""
    best = np.full(values.shape, np.nan)
    raw_best = np.full(values.shape, np.nan)
    on_all = np.ones(values.shape, dtype=bool) if on_mask is None else on_mask
    in_bin = np.asarray(interior, dtype=bool).reshape((-1,) + (1,) * (values.ndim - 1))
    for axis, name in enumerate(AXES):
        est, order = loo_estimate(values, None, None, axis, grids[axis], False)
        mid = np.moveaxis(values, axis, 0)[1:-1]
        on = np.moveaxis(on_all, axis, 0)
        ok = on[:-2] & on[1:-1] & on[2:]
        if name == "L":
            ok = ok & np.moveaxis(np.broadcast_to(in_bin, values.shape), axis, 0)[1:-1]
        raw = np.where(ok, np.abs(est - mid), np.nan)
        for target, value in ((raw_best, raw), (best, raw / 2.0 ** order)):
            view = np.moveaxis(target, axis, 0)
            view[1:-1] = np.fmax(view[1:-1], value)
    return cell_max(best), cell_max(raw_best)


def _checks_of(memo, kind, w_key, n_vds, l_bin_checks):
    """None -> 중점 파일 값(LutSet 에 중점 표가 없으면 조회 없이 ()), 아니면 주어진 값 -- 정규화(model 정렬, 값 칸은
    `per_vds` 로 VDS 별 tuple)."""
    if l_bin_checks is None and not memo.lut.midpoints:
        l_bin_checks = ()
    if l_bin_checks is None:
        rows = midpoint_l_bin_checks(memo, kind, w_key).rows
        l_bin_checks = tuple((r.model, r.vdsat_v) for r in rows)
    return tuple(sorted((str(m), per_vds(v, n_vds, "tol_vdsat_table")) for m, v in l_bin_checks))


def tol_vdsat_table(memo, kind, w_key, l_bin_checks=None):
    """(kind, w_key) 의 `TolVdsatTable`. memo 영역 derived(같은 인자당 1회 계산).

    실패: VDSAT 열 없음 -> `SealViolationError` `lut_column_unavailable`, 슬라이스 없음 -> `KeyError`,
    `l_bin_checks` 오류(중복 model·앵커 2개 bin 이 아닌 model·지도 없는 표에 값) -> `ValueError`.
    """
    src = column_source(memo.lut, kind, w_key, "VDSAT")
    checks = _checks_of(memo, kind, w_key, len(src.grids[2]), l_bin_checks)

    def compute():
        interior = l_interior(src.l_bins, len(src.grids[0]))
        external = external_by_model(checks, _EXTERNAL_FIELDS, "tol_vdsat_table")
        l_loo, l_loo_bins, ext_rows = l_loo_report(src.l_bins, interior, external, "tol_vdsat_table")
        best, raw = _loo_cells(np.asarray(src.array, dtype=float), src.on_mask, src.grids, interior)
        cells = tuple(
            tuple(TolVdsatCell(with_external(opt(best[i, k]), ext_rows[i]["vdsat_v"][k] if i in ext_rows else None),
                               opt(raw[i, k]))
                  for k in range(len(src.grids[2])))
            for i in range(len(src.grids[0])))
        orders = tuple((m, a, meth, p, 2.0 ** -p) for m, a, meth, p in LOO_ORDERS)
        return TolVdsatTable(kind, w_key, src.origin, src.grids[0], src.grids[2], cells, src.l_bins, l_loo, l_loo_bins,
                             orders, checks)

    return memo.lookup("derived", "tol_vdsat_table", (kind, w_key, checks), compute)
