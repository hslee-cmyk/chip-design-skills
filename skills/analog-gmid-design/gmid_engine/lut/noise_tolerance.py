"""잡음 허용오차 표 -- 잡음 면(ln S_vg(1 Hz)·ln B)의 leave-one-out 선형 오차를 Richardson 환산한 상대오차, 셀((kind, L 앵커, VDS))별
(설계 41 §7.2 `tol_noise`, lut/CONTRACT.md 9.4).

진입점: `tol_noise_table`.

* 지표 `flicker` = ln S_vg(f_lo)(= A 를 지배하는 flicker 면)의 LOO 오차, `thermal` = ln B(B 가 known 인 점끼리)의 LOO 오차. 둘 다 `_helpers_loo.linear_loo_cells`
  (네 축 선형 LOO ÷ 2^2, L 축은 같은 bin 안 내부 앵커만) -- 값이 로그라 오차는 상대오차(무차원)다. 가장 높은 피드스루 무관 점을 고르는 판정(`noise_planes`)이
  `flicker` 를 쓴다(같은 표 값, 순환 없음). 앵커 2개 bin 의 외부 L 값(검증 중점)은 잡음에 없다 -- 그 bin 은 L 방향 오차가 비어 있다(`l_loo` 상태 기록).
* 디스크 캐시 대상(derived).
"""
from operator import attrgetter

import numpy as np

from ._helpers_loo import l_interior, l_loo_report, linear_loo_cells, opt, table_at
from .lut_types import AXES, TOL_NOISE_METRICS, TolNoiseCell
from .noise_planes import STATUS_KNOWN, noise_planes


class TolNoiseTable:
    """(kind) 잡음 허용오차 표. `cells[i_L][i_vds]` = TolNoiseCell, 축은 `L_anchors`·`vds_grid`. `l_bins`·`l_loo`·`l_loo_bins`: tol_V 표와 같은 뜻."""

    def __init__(self, kind, w_key, L_anchors, vds_grid, cells, l_bins, grid_m, rule, l_loo, l_loo_bins):
        self.kind = kind
        self.w_key = w_key
        self.L_anchors = L_anchors
        self.vds_grid = vds_grid
        self.cells = cells
        self.l_bins = l_bins
        self.grid_m = grid_m
        self.rule = rule
        self.l_loo = l_loo
        self.l_loo_bins = l_loo_bins

    def at(self, L, vds, metric):
        """조회점 (L, vds) 의 상대 허용오차(`TolVTable.at` 와 같은 행·칸·셀 결합 규칙 `table_at` -- 결합 셀 가운데 None 이 하나라도 있으면 None).
        실패: `metric` 이 `TOL_NOISE_METRICS` 밖 -> `ValueError`, L 위치·VDS 축 -> `SealViolationError`(table "tol_noise")."""
        if metric not in TOL_NOISE_METRICS:
            raise ValueError("TolNoiseTable.at: metric 은 %s 중 하나" % (TOL_NOISE_METRICS,))
        context = (("kind", self.kind), ("table", "tol_noise"), ("w_key", self.w_key))
        return table_at(self, attrgetter(metric), L, vds, context)


def tol_noise_table(memo, kind):
    """kind 의 `TolNoiseTable`. memo 영역 derived. 잡음 r1 파일이 없는 LutSet -> `KeyError`."""
    table = memo.lut.noise[kind]
    planes = noise_planes(memo, kind)

    def compute():
        interior = l_interior(table.l_bins, len(table.grids[0]))
        l_loo, l_loo_bins, _ = l_loo_report(table.l_bins, interior, {}, "tol_noise_table")
        ln_b = np.where(planes.status == STATUS_KNOWN, planes.ln_b, np.nan)
        b_cells = linear_loo_cells(ln_b, table.grids, interior)
        cells = tuple(tuple(TolNoiseCell(opt(planes.tol_a[i, k]), opt(b_cells[i, k])) for k in range(len(table.grids[2])))
                      for i in range(len(table.grids[0])))
        return TolNoiseTable(kind, table.w_key, table.grids[0], table.grids[2], cells, table.l_bins, memo.lut.spec.manufacturing_grid_m, memo.lut.bin_rule, l_loo, l_loo_bins)

    return memo.lookup_persistent("derived", "tol_noise_table", (kind,), compute, (table.sha256, planes), (AXES, TOL_NOISE_METRICS))
