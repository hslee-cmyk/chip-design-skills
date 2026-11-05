"""앵커 2개 bin 의 L 보간 오차 -- 검증 중점 파일(LUT 축이 아닌 bin 안 L 점)과 운영 L 보간의 차 (lut/CONTRACT.md 5.1, r6;
lut_regen_plan.md 2절 K2', 계획 N3.6).

진입점: `midpoint_l_bin_checks`.

* 앵커 2개 bin 은 L 방향 LOO 가 정의되지 않는다. 그래서 그 bin 안 중점 L_m 에서 SPICE 로 잰 값(`LutSet.midpoints`)과 운영 보간
  (두 앵커 a0 < L_m < a1 의 L 선형, VGS·VDS·VS 는 격자점이라 4.2 의 마디 값 그대로)을 비교한 오차를 그 bin 의 외부 값으로 낸다.
  운영 보간의 칸 안 오차 그 자체라 Richardson 환산을 하지 않는다(tol 표 5절).
* [r6, 오케스트레이터 결정 A] 두 값은 **VDS 격자점마다**의 최댓값 tuple(길이 = VDS 격자 수, 그 VDS 에 점·목표가 없으면 None) --
  내부 LOO 셀 (앵커, VDS_k) 와 같은 해상도. bin 에 스칼라 하나(최댓값)를 두면 행 전체를 덮어 너무 거칠다.
* 지표(tol 표와 같은 정의, t = (L_m − a0)/(a1 − a0), 아래 max 는 그 VDS_k 의 VGS·VS 점·목표에 대해):
  - `id_equivalent_v` = max |lnID_a0 + t·(lnID_a1 − lnID_a0) − ln ID_m| / (GM/ID)_m, 점 = 중점 on(ID > 0, GM > 0)이고 두 앵커 on_mask.
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
from .lut_types import MidpointChecks, MidpointRow

_PAIR = len(LINEAR_CONDITIONS)   # L 선형 보간의 점 수 = 앵커 2개 bin 의 앵커 수


def _vds_max(values, mask):
    """[VGS, VDS, VS] 점 값 -> VDS 격자점마다 mask 참 점의 최댓값 tuple(점 없으면 None)."""
    return tuple(float(values[:, k, :][mask[:, k, :]].max()) if mask[:, k, :].any() else None
                 for k in range(values.shape[1]))


def _vdsat(memo, kind, w_key, mt, m, i0, i1, t, n_vds):
    src = column_source(memo.lut, kind, w_key, "VDSAT", required=False)
    if src is None or mt.VDSAT is None or tuple(src.grids[1:]) != tuple(mt.grids):
        return (None,) * n_vds
    mask = mt.on_mask[m]
    if src.on_mask is not None:
        mask = mask & src.on_mask[i0] & src.on_mask[i1]
    est = src.array[i0] + t * (src.array[i1] - src.array[i0])
    return _vds_max(np.abs(est - mt.VDSAT[m]), mask)


def _merge(a, b):
    """VDS 별 tuple 두 개의 원소별 최댓값(None 은 무시)."""
    return tuple(y if x is None else x if y is None else max(x, y) for x, y in zip(a, b))


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
        grid_m, rule = memo.lut.spec.manufacturing_grid_m, memo.lut.bin_rule
        skipped, per_model = [], {}
        for m, L_m in enumerate(mt.L_points):
            if mt.w_key != w_key:
                skipped.append((L_m, "width_differs", None))
                continue
            if not bins.bins:
                skipped.append((L_m, "bins_unavailable", None))
                continue
            if math.isfinite(L_m) and any(round(L_m / grid_m) == round(a / grid_m) for a in l_grid):
                skipped.append((L_m, "is_anchor", None))
                continue
            b = bin_index(tuple((x.lmin, x.lmax) for x in bins.bins), L_m, grid_m, rule)
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
                eq = _vds_max(np.abs(lid - mt.log_ID[m]) / mt.gm_id[m], on)
            vd = _vdsat(memo, kind, w_key, mt, m, i0, i1, t, len(sl.grids[2]))
            prev = per_model.get(model)
            if prev is None:
                per_model[model] = ((L_m,), eq, vd)
            else:
                per_model[model] = (prev[0] + (L_m,), _merge(prev[1], eq), _merge(prev[2], vd))
        rows = tuple(MidpointRow(model, *vals) for model, vals in sorted(per_model.items()))
        return MidpointChecks(kind, w_key, rows, tuple(skipped), mt.sha256)

    return memo.lookup("derived", "midpoint_l_bin_checks", (kind, w_key), compute)
