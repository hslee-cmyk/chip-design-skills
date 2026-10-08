"""VDsat 곡선 표 -- 강반전 분지 VGS 마디의 VDSAT(V) (설계 40 §2.3, 41 §6.2 헤드룸 gm/ID 하한, lut/CONTRACT.md 4.5).

진입점: `vdsat_curve`. 값 = 마디의 `vdsat(...)`(LUT VDSAT 열, 오라클 `@m[vdsat]` 과 같은 양). 열이 없는 (kind, w_key) 는 `lut_column_unavailable`.
"""
import numpy as np

from ._helpers_gmid_axis import axis_curve
from .vdsat_query import vdsat


def vdsat_curve(memo, kind, w_key, L, vds, vsb):
    """`GmIdAxisCurve`(quantity "vdsat_v", V). 실패: `gm_id_curve`/`vdsat` 사유."""

    def values(curve, nodes):
        return np.asarray([vdsat(memo, kind, w_key, L, float(curve.vgs_grid[j]), vds, vsb) for j in nodes])

    return axis_curve(memo, "vdsat_v", kind, w_key, L, vds, vsb, values)
