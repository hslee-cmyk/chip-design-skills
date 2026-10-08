"""f_T 곡선 표 -- 강반전 분지 VGS 마디의 f_T = gm / (2π·Cgg) (설계 40 §2.3, 41 §6.3 속도 상한, lut/CONTRACT.md 4.5).

진입점: `ft_curve`.

gm = (gm/ID)·ID(마디, 슬라이스 폭 w_m), Cgg = `caps(W = w_m).cgg`(같은 마디의 기준 LUT 용량 -- 폭에 비례하므로 f_T 는 폭과 무관). 2π = 한 바퀴 `math.tau`.
Cgg ≤ 0 인 마디는 실패(`lut_curve_undefined`). 곡선에서 gm/ID 축으로 역산해 gm/ID_k,hi 를 얻는 것은 소비자(출발 구간)의 일이다.
"""
import math

import numpy as np

from ._helpers_fail import seal_violation
from ._helpers_gmid_axis import axis_curve
from .cap_query import caps


def ft_curve(memo, kind, w_key, L, vds, vsb):
    """`GmIdAxisCurve`(quantity "ft_hz", Hz). 실패: `gm_id_curve`/`caps` 사유, Cgg ≤ 0 -> `lut_curve_undefined`."""
    w_m = memo.lut.slice_map[(kind, w_key)].w_m

    def values(curve, nodes):
        out = []
        for j in nodes:
            cgg = caps(memo, kind, L, float(curve.vgs_grid[j]), vds, vsb, w_m).cgg
            if not cgg > 0:
                raise seal_violation("lut_curve_undefined", quantity="ft_hz", cgg=float(cgg), vgs=float(curve.vgs_grid[j]),
                                     kind=kind, w_key=w_key, L=float(L), vds=float(vds), vsb=float(vsb))
            out.append(curve.gm_id_vals[j] * curve.id_vals[j] / (math.tau * cgg))
        return np.asarray(out)

    return axis_curve(memo, "ft_hz", kind, w_key, L, vds, vsb, values)
