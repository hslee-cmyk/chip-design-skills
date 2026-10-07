"""tol_V 표 -- L 앵커 leave-one-out 보간 오차를 VGS 단위로, 셀((kind, w_key, L 앵커, VDS))별 (계획 N3.6, 설계 MOD1 2.7).

진입점: `tol_v_table`.

* 셀별 값만 낸다. 전역 최댓값 하나로 줄이지 않는다(tol_V 실측: 전역 최댓값이면 판정이 무력해진다).
* 두 지표를 모두 계산한다(어느 지표를 어디에 쓸지는 사용자 결정 대기 -- 고르지 않는다, `TOL_V_METRICS`):
  - `gm_id_inverse`: 내부 앵커 i 를 빼고 i-1·i+1 로 보간한 곡선(운영 보간과 같은 `multilinear_interp`, 로그공간)에서
    목표 gm/ID 를 강반전 분지 규칙(`strong_inversion_root`)으로 역산한 VGS 와 참 VGS 의 차.
  - `id_equivalent`: 같은 VGS 에서 |ln ID_loo - ln ID| / (gm/ID) -- 전류 보간 오차를 VGS 로 환산한 값.
* 목표: 앵커 i 의 (VDS, VS) 곡선마다, 정점 이후 격자점 j 중 오른쪽 모든 점의 gm/ID 가 g_j 보다 작은 점
  (= 그 곡선에서 VGS_j 가 강반전 분지 해) 의 g_j. 참 VGS = VGS_j(정확). 곡선 i-1·i·i+1 중 ID·GM 에 0 이하 격자점이
  있으면 그 (VDS, VS) 는 목표 없음. LOO 곡선에 해가 없으면 오차값에 넣지 않고 `n_inverse_failed` 로 센다.
* 셀 값 = 그 (L 앵커, VDS) 의 VS·목표 전체 최댓값. 양끝 앵커는 LOO 가 정의되지 않아 None.
"""
import bisect

import numpy as np

from ._helpers_interp import multilinear_interp
from ._helpers_root import peak_index, strong_inversion_root
from .axis_guard import check_axes
from .lut_types import AXES, TOL_V_METRICS, TolVCell


def _targets(g):
    p = peak_index(g)
    out = []
    right_max = -np.inf
    for j in range(len(g) - 1, p - 1, -1):
        if g[j] > right_max:
            out.append(j)
        right_max = max(right_max, g[j])
    return out


def _loo_curve(sl, i, k, s, pts):
    pair = (sl.grids[0][i - 1], sl.grids[0][i + 1])
    grids = (pair, sl.grids[1])
    lid = multilinear_interp(grids, sl.log_ID[[i - 1, i + 1], :, k, s], pts)
    lgm = multilinear_interp(grids, sl.log_GM[[i - 1, i + 1], :, k, s], pts)
    return lid, np.exp(lgm - lid)


def _cell(sl, i, k):
    vgs = sl.VGS_grid
    pts = np.column_stack([np.full(len(vgs), sl.grids[0][i]), vgs])
    inv = eq = None
    n_targets = n_failed = 0
    for s in range(len(sl.grids[3])):
        if not sl.on_mask[i - 1:i + 2, :, k, s].all():
            continue
        lid_t = sl.log_ID[i, :, k, s]
        g_t = np.exp(sl.log_GM[i, :, k, s] - lid_t)
        lid_loo, g_loo = _loo_curve(sl, i, k, s, pts)
        for j in _targets(g_t):
            n_targets += 1
            e = abs(lid_loo[j] - lid_t[j]) / g_t[j]
            eq = e if eq is None else max(eq, e)
            est = strong_inversion_root(g_loo, vgs, g_t[j])
            if est is None:
                n_failed += 1
                continue
            e = abs(est - vgs[j])
            inv = e if inv is None else max(inv, e)
    return TolVCell(None if inv is None else float(inv), None if eq is None else float(eq), n_targets, n_failed)


class TolVTable:
    """(kind, w_key) 슬라이스의 tol_V 표. `cells[i_L][i_vds]` = TolVCell, 축은 `L_anchors`·`vds_grid`."""

    def __init__(self, kind, w_key, L_anchors, vds_grid, cells):
        self.kind = kind
        self.w_key = w_key
        self.L_anchors = L_anchors
        self.vds_grid = vds_grid
        self.cells = cells

    def at(self, L, vds, metric):
        """조회점 (L, vds) 의 tol_V(V): L 이 든 앵커 칸 [j, j+1] 과 VDS 가 든 격자 칸 [k, k+1] 의 네 셀 중 정의된 값의
        최댓값(칸 = `bisect_right - 1`, 마지막 격자점은 마지막 칸). 정의된 값이 없으면 None.

        실패: `metric` 이 `TOL_V_METRICS` 밖 -> `ValueError`, 축 밖 -> `SealViolationError`(lut_axis_out_of_range).
        """
        if metric not in TOL_V_METRICS:
            raise ValueError("TolVTable.at: metric 은 %s 중 하나" % (TOL_V_METRICS,))
        L, vds = float(L), float(vds)
        check_axes((self.L_anchors, self.vds_grid), (AXES[0], AXES[2]), (L, vds),
                   (("kind", self.kind), ("w_key", self.w_key), ("table", "tol_v")))
        j = min(bisect.bisect_right(self.L_anchors, L) - 1, len(self.L_anchors) - 2)
        k = min(bisect.bisect_right(self.vds_grid, vds) - 1, len(self.vds_grid) - 2)
        field = metric + "_v"
        vals = [getattr(self.cells[a][b], field) for a in (j, j + 1) for b in (k, k + 1)]
        vals = [v for v in vals if v is not None]
        return max(vals) if vals else None


def tol_v_table(memo, kind, w_key):
    """(kind, w_key) 슬라이스의 `TolVTable`. memo 영역 derived(슬라이스당 1회 계산). 폭 키 없음 -> `KeyError`."""
    sl = memo.lut.slice_map[(kind, w_key)]

    def compute():
        n_l, n_vds = len(sl.grids[0]), len(sl.grids[2])
        empty = TolVCell(None, None, 0, 0)
        cells = tuple(
            tuple(_cell(sl, i, k) if 0 < i < n_l - 1 else empty for k in range(n_vds))
            for i in range(n_l))
        return TolVTable(kind, w_key, sl.grids[0], sl.grids[2], cells)

    return memo.lookup("derived", "tol_v_table", (kind, w_key), compute)
