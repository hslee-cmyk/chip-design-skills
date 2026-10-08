"""진성 이득 곡선 표 -- 강반전 분지 VGS 마디의 gm/gds (설계 40 §2.3, 41 §6.4-1 이득 하한, lut/CONTRACT.md 4.5).

진입점: `intrinsic_gain_curve`. 값 = 마디의 `op_point(...).gm_gds`(무차원, 폭 무관).
"""
import numpy as np

from ._helpers_gmid_axis import axis_curve
from .point_query import op_point


def intrinsic_gain_curve(memo, kind, w_key, L, vds, vsb):
    """`GmIdAxisCurve`(quantity "intrinsic_gain"). 실패: `gm_id_curve`/`op_point` 사유."""

    def values(curve, nodes):
        return np.asarray([op_point(memo, kind, w_key, L, float(curve.vgs_grid[j]), vds, vsb).gm_gds for j in nodes])

    return axis_curve(memo, "intrinsic_gain", kind, w_key, L, vds, vsb, values)
