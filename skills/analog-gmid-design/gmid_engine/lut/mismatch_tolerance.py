"""mismatch 허용오차 표 `tol_mismatch` -- DVGS_k 면의 leave-one-out 선형 오차를 Richardson 환산한 V 단위 절대오차, 셀((kind, L 앵커, VDS))·변수별
(설계 41 §6.4-2b, lut/CONTRACT.md 10.3).

진입점: `tol_mismatch_table`.

* `_helpers_loo.linear_loo_cells`(네 축 선형 LOO ÷ 2^2, L 축은 같은 bin 안 내부 앵커만) -- 감도 열은 도함수 자료가 없어 운영 보간(`mismatch_dvgs`)과 같은 방법이 선형이다.
  DVGS 가 NaN 인 점과 그 이웃은 빠진다. 값의 단위가 V 라 오차도 V 다. 앵커 2개 bin 의 외부 L 값은 없다(`l_loo` 상태에 남는다).
* 디스크 캐시 대상(derived).
"""
from ._helpers_loo import l_interior, l_loo_report, linear_loo_cells, opt, table_at
from .lut_types import AXES, TolMismatchCell


class TolMismatchTable:
    """(kind) mismatch 허용오차 표. `cells[i_L][i_vds]` = TolMismatchCell, 축은 `L_anchors`·`vds_grid`. `l_bins`·`l_loo`·`l_loo_bins`: tol_V 표와 같은 뜻."""

    def __init__(self, kind, w_key, params, L_anchors, vds_grid, cells, l_bins, grid_m, rule, l_loo, l_loo_bins):
        self.kind = kind
        self.w_key = w_key
        self.params = params
        self.L_anchors = L_anchors
        self.vds_grid = vds_grid
        self.cells = cells
        self.l_bins = l_bins
        self.grid_m = grid_m
        self.rule = rule
        self.l_loo = l_loo
        self.l_loo_bins = l_loo_bins

    def at(self, L, vds, param):
        """조회점 (L, vds) 의 변수 `param` 의 tol(V): L 위치(앵커 행 또는 같은 bin 보간 양옆 앵커 두 행)·VDS 칸의 결합 셀이 모두 정의되면 그 값의 최댓값,
        하나라도 None 이면 None(셀 결합 규칙 = `_helpers_loo.table_at` 하나 -- tol_V·tol_VDsat·잡음 tol 표와 같다).
        실패: `param` 이 `params` 밖 -> `ValueError`, L 위치·VDS 축 -> `SealViolationError`(table "tol_mismatch")."""
        if param not in self.params:
            raise ValueError("TolMismatchTable.at: param 은 %s 중 하나" % (self.params,))
        context = (("kind", self.kind), ("table", "tol_mismatch"), ("w_key", self.w_key))
        j = self.params.index(param)
        return table_at(self, lambda cell: cell.params[j][1], L, vds, context)


def tol_mismatch_table(memo, kind):
    """kind 의 `TolMismatchTable`. memo 영역 derived. mismatch r1 파일이 없는 LutSet -> `KeyError`."""
    table = memo.lut.mismatch[kind]

    def compute():
        interior = l_interior(table.l_bins, len(table.grids[0]))
        l_loo, l_loo_bins, _ = l_loo_report(table.l_bins, interior, {}, "tol_mismatch_table")
        per_param = [linear_loo_cells(table.dvgs[p], table.grids, interior) for p in table.params]
        cells = tuple(
            tuple(TolMismatchCell(tuple((p, opt(cells_p[i, k])) for p, cells_p in zip(table.params, per_param)))
                  for k in range(len(table.grids[2])))
            for i in range(len(table.grids[0])))
        return TolMismatchTable(kind, table.w_key, table.params, table.grids[0], table.grids[2], cells, table.l_bins,
                                memo.lut.spec.manufacturing_grid_m, memo.lut.bin_rule, l_loo, l_loo_bins)

    return memo.lookup_persistent("derived", "tol_mismatch_table", (kind,), compute, table, (AXES,))
