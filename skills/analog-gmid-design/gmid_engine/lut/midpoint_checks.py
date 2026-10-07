"""앵커 2개 bin 의 L 보간 오차 -- 검증 중점 파일(LUT 축이 아닌 bin 안 L 점)과 운영 L 보간의 차 (lut/CONTRACT.md 5.1, r6;
lut_regen_plan.md 2절 K2', 계획 N3.6).

진입점: `midpoint_l_bin_checks`.

* 앵커 2개 bin 은 L 방향 LOO 가 정의되지 않는다. 그래서 그 bin 안 중점 L_m 에서 SPICE 로 잰 값(`LutSet.midpoints`)과 운영 보간
  (두 앵커 a0 < L_m < a1 의 L 선형, VGS·VDS·VS 는 격자점이라 4.2 의 마디 값 그대로)을 비교한 오차를 그 bin 의 외부 값으로 낸다.
  운영 보간의 칸 안 오차 그 자체라 Richardson 환산을 하지 않는다(tol 표 5절).
* 지표(tol 표와 같은 정의, t = (L_m − a0)/(a1 − a0)):
  - `id_equivalent_v` = max |lnID_a0 + t·(lnID_a1 − lnID_a0) − ln ID_m| / (GM/ID)_m, 점 = 중점 on(ID > 0, GM > 0)이고 두 앵커 on_mask.
  - `gm_id_inverse_v` = max |strong_inversion_root(보간 곡선, g_j) − VGS_j|, 곡선 (VDS_k, VS_s) 마다 중점·두 앵커 곡선이 VGS 전부 on,
    보간 곡선 = (ln ID, gm/ID) 를 L 선형(운영 `gm_id_curve` 의 마디 값), 목표 j = 중점 곡선의 분지 목표(`branch_targets`).
    해 없음은 값에 넣지 않고 센다.
  - `vdsat_v` = max |VDSAT_a0 + t·(VDSAT_a1 − VDSAT_a0) − VDSAT_m|, VDSAT 열 출처(`column_source`)와 중점 파일에 열이 있고 두 표의
    VGS·VDS·VS 축이 같을 때(점 = 중점 on 이고 출처 표 두 앵커 on), 아니면 None.
* 쓰지 않는 중점은 이유와 함께 `skipped` 에 남긴다(조용히 버리지 않음): "width_differs"(중점 파일 폭 키 ≠ w_key -- 다른 폭으로
  옮기지 않는다), "bins_unavailable", "is_anchor", "outside_model_bins", "single_point"(그 bin 의 앵커 1개 -- 조회 자체가
  `lut_l_bin_unbracketed`), "bin_has_interior_anchors"(앵커 3개 이상 -- L 방향 LOO 가 있다), "not_bracketed"(bin 안이지만
  두 앵커 바깥 -- 조회가 거부되는 L).
"""
import math

import numpy as np

from ._helpers_bins import bin_index
from ._helpers_columns import column_source
from ._helpers_interp import LINEAR_CONDITIONS
from ._helpers_loo import branch_targets
from ._helpers_root import strong_inversion_root
from .lut_types import MidpointChecks, MidpointRow

_PAIR = len(LINEAR_CONDITIONS)   # L 선형 보간의 점 수 = 앵커 2개 bin 의 앵커 수


def _nanmax(values, mask):
    sel = values[mask]
    return float(sel.max()) if sel.size else None


def _curves(arr):
    """[VGS, VDS, VS] -> (VDS·VS 곡선, VGS)."""
    return np.moveaxis(arr, 0, -1).reshape(-1, arr.shape[0])


def _inverse(sl, mt, m, i0, i1, t):
    """(최대 오차 또는 None, 시도 수, 실패 수) -- gm/ID 역산 지표."""
    y = sl.log_ID[i0] + t * (sl.log_ID[i1] - sl.log_ID[i0])
    g_a = [np.exp(sl.log_GM[i] - sl.log_ID[i]) for i in (i0, i1)]
    g = g_a[0] + t * (g_a[1] - g_a[0])
    on = _curves(mt.on_mask[m] & sl.on_mask[i0] & sl.on_mask[i1]).all(axis=1)
    truth = _curves(np.where(mt.on_mask[m], mt.gm_id[m], -np.inf))
    c, j = branch_targets(truth, on)
    if not c.size:
        return None, 0, 0
    v = np.asarray(sl.VGS_grid)
    root, _ = strong_inversion_root(np.broadcast_to(v, (c.size, v.size)), _curves(y)[c], _curves(g)[c], truth[c, j])
    found = np.isfinite(root)
    worst = float(np.abs(root[found] - v[j[found]]).max()) if found.any() else None
    return worst, int(c.size), int(np.count_nonzero(~found))


def _vdsat(memo, kind, w_key, mt, m, i0, i1, t):
    src = column_source(memo.lut, kind, w_key, "VDSAT", required=False)
    if src is None or mt.VDSAT is None or tuple(src.grids[1:]) != tuple(mt.grids):
        return None
    mask = mt.on_mask[m]
    if src.on_mask is not None:
        mask = mask & src.on_mask[i0] & src.on_mask[i1]
    est = src.array[i0] + t * (src.array[i1] - src.array[i0])
    return _nanmax(np.abs(est - mt.VDSAT[m]), mask)


def _merge(a, b):
    if a is None or b is None:
        return b if a is None else a
    return max(a, b)


def midpoint_l_bin_checks(memo, kind, w_key):
    """(kind, w_key) 슬라이스의 앵커 2개 bin 외부 값 `MidpointChecks`. memo 영역 derived(같은 인자당 1회).

    중점 파일이 없거나 그 kind 표가 없으면 rows·skipped 모두 빈 값. 슬라이스 없음 -> `KeyError`.
    """
    sl = memo.lut.slice_map[(kind, w_key)]

    def compute():
        mt = memo.lut.midpoints.get(kind)
        if mt is None:
            return MidpointChecks(kind, w_key, (), (), None)
        l_grid = sl.grids[0]
        bins = sl.l_bins
        skipped, per_model = [], {}
        for m, L_m in enumerate(mt.L_points):
            if mt.w_key != w_key:
                skipped.append((L_m, "width_differs", None))
                continue
            if not bins.bins:
                skipped.append((L_m, "bins_unavailable", None))
                continue
            if any(abs(L_m - a) <= math.ulp(a) for a in l_grid):
                skipped.append((L_m, "is_anchor", None))
                continue
            b = bin_index(tuple((x.lmin, x.lmax) for x in bins.bins), L_m)
            if b is None:
                skipped.append((L_m, "outside_model_bins", None))
                continue
            model = bins.bins[b].model
            members = tuple(i for i, a in enumerate(bins.anchor_bin) if a == b)
            if len(members) != _PAIR:
                skipped.append((L_m, "single_point" if len(members) < _PAIR else "bin_has_interior_anchors", model))
                continue
            i0, i1 = members
            if not l_grid[i0] < L_m < l_grid[i1]:
                skipped.append((L_m, "not_bracketed", model))
                continue
            t = (L_m - l_grid[i0]) / (l_grid[i1] - l_grid[i0])
            lid = sl.log_ID[i0] + t * (sl.log_ID[i1] - sl.log_ID[i0])
            on = mt.on_mask[m] & sl.on_mask[i0] & sl.on_mask[i1]
            with np.errstate(invalid="ignore"):
                eq = _nanmax(np.abs(lid - mt.log_ID[m]) / mt.gm_id[m], on)
            inv, n_try, n_failed = _inverse(sl, mt, m, i0, i1, t)
            vd = _vdsat(memo, kind, w_key, mt, m, i0, i1, t)
            prev = per_model.get(model)
            if prev is None:
                per_model[model] = ((L_m,), inv, eq, vd, n_try, n_failed)
            else:
                per_model[model] = (prev[0] + (L_m,), _merge(prev[1], inv), _merge(prev[2], eq), _merge(prev[3], vd),
                                    prev[4] + n_try, prev[5] + n_failed)
        rows = tuple(MidpointRow(model, *vals) for model, vals in sorted(per_model.items()))
        return MidpointChecks(kind, w_key, rows, tuple(skipped), mt.sha256)

    return memo.lookup("derived", "midpoint_l_bin_checks", (kind, w_key), compute)
