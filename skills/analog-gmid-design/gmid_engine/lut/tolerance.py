"""tol_V 표 -- 보간 축(VGS·VDS·VS) leave-one-out 보간 오차를 VGS 단위로, 셀((kind, w_key, L 앵커, VDS))별
(계획 N3.6 사용자 확정 2026-10-07, 설계 MOD1 2.7).

진입점: `tol_v_table`.

* L 은 앵커 이산값만 쓰고 보간하지 않으므로(계획 LR3) L 축은 leave-one-out 대상이 아니다. 모든 L 앵커가 셀을 가진다.
* 축 a ∈ (VGS, VDS, VS) 의 **내부** 격자점 x_j(0 < j < n_a - 1)를 빼고 이웃 x_{j-1}·x_{j+1} 로 같은 선형 보간
  (운영 보간 `multilinear_interp` 의 1축 2점 경우와 같은 식: lnX_{j-1} + t·(lnX_{j+1} - lnX_{j-1}), t = (x_j - x_{j-1}) / (x_{j+1} - x_{j-1}),
  ln ID·ln GM 로그공간)한 값을 그 점의 LUT 값과 비교한다. 양끝 격자점은 그 축 방향 추정이 없다(다른 축 방향은 있다).
* 셀별 값만 낸다(전역 최댓값 하나로 줄이지 않는다). 두 지표(`TOL_V_METRICS`) -- 소비자 배정은 계획 N3.6:
  - `id_equivalent`(KCL·W 보존·소자 경고): 점마다 |ln ID_loo - ln ID| / (gm/ID). 그 점과 축 방향 두 이웃이 모두 on_mask.
  - `gm_id_inverse`(봉인 2 VGS 정합): 곡선 (L 앵커, VDS_k, VS_s) 이 on_mask 전부 참일 때, 목표 j = 정점 이후 격자점 중
    오른쪽 모든 점보다 gm/ID 가 큰 점(VGS_j 가 그 곡선의 강반전 분지 해). LOO 곡선:
    VGS 축 = 그 곡선의 j 점 값만 이웃 보간값으로 바꾼 곡선(j 가 VGS 양끝이면 없음),
    VDS 축 = 곡선 VDS_{k-1}·VDS_{k+1} 로 보간한 곡선(k 내부, 두 곡선 on_mask 전부 참일 때),
    VS 축 = 곡선 VS_{s-1}·VS_{s+1} 로 보간한 곡선(같은 조건). 값 = |strong_inversion_root(LOO 곡선, g_j) - VGS_j|,
    해가 없으면 값에 넣지 않고 `n_inverse_failed` 로 센다.
* 셀 값 = 그 (L 앵커 i, VDS_k) 안의 모든 VGS·VS·목표·축 최댓값, 없으면 None. `n_targets` = 그 셀의 gm/ID 역산 시도 수
  ((목표, 축) 쌍), `n_inverse_failed` = 그중 해 없음 수.
"""
import bisect

import numpy as np

from ._helpers_anchor import l_anchor_index
from ._helpers_root import peak_index, strong_inversion_root
from .axis_guard import check_axes
from .lut_types import AXES, TOL_V_METRICS, TolVCell


def _loo(arr, axis, grid):
    """축 `axis` 내부 격자점마다 이웃 두 점 선형 보간값(배열 모양 그대로, 양끝 = NaN)."""
    x = np.asarray(grid, dtype=float)
    t = (x[1:-1] - x[:-2]) / (x[2:] - x[:-2])
    a = np.moveaxis(arr, axis, 0)
    out = np.full(a.shape, np.nan)
    out[1:-1] = a[:-2] + t.reshape((-1,) + (1,) * (a.ndim - 1)) * (a[2:] - a[:-2])
    return np.moveaxis(out, 0, axis)


def _neighbors_on(mask, axis):
    """축 `axis` 방향으로 자기와 두 이웃이 모두 on 인 점(양끝 = 거짓)."""
    m = np.moveaxis(mask, axis, 0)
    out = np.zeros(m.shape, dtype=bool)
    out[1:-1] = m[:-2] & m[1:-1] & m[2:]
    return np.moveaxis(out, 0, axis)


def _id_equivalent(sl):
    """[L, VDS] 셀 최댓값 배열(정의 없음 = NaN)."""
    gm_id = np.exp(sl.log_GM - sl.log_ID)
    best = np.full(sl.on_mask.shape, np.nan)
    for axis in range(AXES.index("VGS"), len(AXES)):
        est = _loo(sl.log_ID, axis, sl.grids[axis])
        ok = _neighbors_on(sl.on_mask, axis)
        err = np.where(ok, np.abs(est - sl.log_ID) / gm_id, np.nan)
        best = np.fmax(best, err)
    per_cell = np.moveaxis(best, (AXES.index("L"), AXES.index("VDS")), (0, 1))
    flat = per_cell.reshape(per_cell.shape[0], per_cell.shape[1], -1)
    out = np.full(flat.shape[:-1], np.nan)
    has = ~np.isnan(flat).all(axis=-1)
    out[has] = np.nanmax(flat[has], axis=-1)
    return out


def _targets(g):
    p = peak_index(g)
    out = []
    right_max = -np.inf
    for j in range(len(g) - 1, p - 1, -1):
        if g[j] > right_max:
            out.append(j)
        right_max = max(right_max, g[j])
    return out


def _curve_loo(sl, i, k, s, axis, idx):
    """VDS·VS 축(`axis`, 그 축 index `idx`) 방향 LOO 곡선 gm/ID, 정의 안 되면 None."""
    if not 0 < idx < len(sl.grids[axis]) - 1:
        return None
    pos = [i, slice(None), k, s]
    lo_pos, hi_pos = list(pos), list(pos)
    lo_pos[axis], hi_pos[axis] = idx - 1, idx + 1
    if not (sl.on_mask[tuple(lo_pos)].all() and sl.on_mask[tuple(hi_pos)].all()):
        return None
    x = sl.grids[axis]
    t = (x[idx] - x[idx - 1]) / (x[idx + 1] - x[idx - 1])
    lid = sl.log_ID[tuple(lo_pos)] + t * (sl.log_ID[tuple(hi_pos)] - sl.log_ID[tuple(lo_pos)])
    lgm = sl.log_GM[tuple(lo_pos)] + t * (sl.log_GM[tuple(hi_pos)] - sl.log_GM[tuple(lo_pos)])
    return np.exp(lgm - lid)


def _inverse_cell(sl, i, k):
    vgs = sl.VGS_grid
    x = sl.grids[1]
    worst = None
    n_try = n_failed = 0
    for s in range(len(sl.grids[3])):
        if not sl.on_mask[i, :, k, s].all():
            continue
        lid = sl.log_ID[i, :, k, s]
        lgm = sl.log_GM[i, :, k, s]
        g = np.exp(lgm - lid)
        curves = [c for c in (_curve_loo(sl, i, k, s, AXES.index("VDS"), k), _curve_loo(sl, i, k, s, AXES.index("VS"), s))
                  if c is not None]
        for j in _targets(g):
            loo = list(curves)
            if 0 < j < len(vgs) - 1:
                t = (x[j] - x[j - 1]) / (x[j + 1] - x[j - 1])
                gv = g.copy()
                gv[j] = np.exp((lgm[j - 1] + t * (lgm[j + 1] - lgm[j - 1])) - (lid[j - 1] + t * (lid[j + 1] - lid[j - 1])))
                loo.append(gv)
            for c in loo:
                n_try += 1
                est = strong_inversion_root(c, vgs, g[j])
                if est is None:
                    n_failed += 1
                    continue
                e = abs(est - vgs[j])
                worst = e if worst is None else max(worst, e)
    return worst, n_try, n_failed


class TolVTable:
    """(kind, w_key) 슬라이스의 tol_V 표. `cells[i_L][i_vds]` = TolVCell, 축은 `L_anchors`·`vds_grid`."""

    def __init__(self, kind, w_key, L_anchors, vds_grid, cells):
        self.kind = kind
        self.w_key = w_key
        self.L_anchors = L_anchors
        self.vds_grid = vds_grid
        self.cells = cells

    def at(self, L, vds, metric):
        """조회점 (L 앵커, vds) 의 tol_V(V): L 은 앵커 이산 키(1 ulp 이내 일치), VDS 가 든 격자 칸 [k, k+1]
        (`bisect_right - 1`, 마지막 격자점은 마지막 칸) 의 두 셀 중 정의된 값의 최댓값. 정의된 값이 없으면 None.

        실패: `metric` 이 `TOL_V_METRICS` 밖 -> `ValueError`, L 이 앵커가 아님·축 밖 -> `SealViolationError`.
        """
        if metric not in TOL_V_METRICS:
            raise ValueError("TolVTable.at: metric 은 %s 중 하나" % (TOL_V_METRICS,))
        context = (("kind", self.kind), ("table", "tol_v"), ("w_key", self.w_key))
        i = l_anchor_index(self.L_anchors, L, context)
        vds = float(vds)
        check_axes((self.vds_grid,), (AXES[2],), (vds,), context)
        k = min(bisect.bisect_right(self.vds_grid, vds) - 1, len(self.vds_grid) - 2)
        field = metric + "_v"
        vals = [getattr(self.cells[i][b], field) for b in (k, k + 1)]
        vals = [v for v in vals if v is not None]
        return max(vals) if vals else None


def tol_v_table(memo, kind, w_key):
    """(kind, w_key) 슬라이스의 `TolVTable`. memo 영역 derived(슬라이스당 1회 계산). 폭 키 없음 -> `KeyError`."""
    sl = memo.lut.slice_map[(kind, w_key)]

    def compute():
        eq = _id_equivalent(sl)
        cells = []
        for i in range(len(sl.grids[0])):
            row = []
            for k in range(len(sl.grids[2])):
                inv, n_try, n_failed = _inverse_cell(sl, i, k)
                e = eq[i, k]
                row.append(TolVCell(None if inv is None else float(inv), None if np.isnan(e) else float(e),
                                    n_try, n_failed))
            cells.append(tuple(row))
        return TolVTable(kind, w_key, sl.grids[0], sl.grids[2], tuple(cells))

    return memo.lookup("derived", "tol_v_table", (kind, w_key), compute)
