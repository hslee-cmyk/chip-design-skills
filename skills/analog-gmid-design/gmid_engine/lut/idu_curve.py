"""전류밀도 곡선 표 -- 강반전 분지 VGS 마디의 IDu = ID·L/w_m (설계 40 §2.3, 41 §6.4 L 구간·전류 환산, lut/CONTRACT.md 4.5).

진입점: `idu_curve`. 값 = 마디 ID(`gm_id_curve`)에 L/w_m 을 곱한 정규화 전류(A, `op_point(...).IDu` 와 같은 양). 소자 전류 I 의 폭은 W = I·L/IDu.
"""
import numpy as np

from ._helpers_anchor import l_position
from ._helpers_gmid_axis import axis_curve


def idu_curve(memo, kind, w_key, L, vds, vsb):
    """`GmIdAxisCurve`(quantity "idu_a", A). 실패: `gm_id_curve` 사유."""
    sl = memo.lut.slice_map[(kind, w_key)]
    l_val = l_position(sl.grids[0], sl.l_bins, L, (("kind", kind), ("w_key", w_key)))[2]

    def values(curve, nodes):
        return np.asarray(curve.id_vals[nodes]) * l_val / sl.w_m

    return axis_curve(memo, "idu_a", kind, w_key, L, vds, vsb, values)
