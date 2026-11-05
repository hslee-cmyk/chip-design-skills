"""폭 W 가 정해진 소자에서 목표 gm 또는 목표 ID 를 만드는 동작점 역산 (설계 MOD1 2.3, 옛 `solve_id_for_target_gm`·
`_invert_gm_id_for_current` 대체, DF-10, DEC-87).

진입점: `gm_id_for_target`.

옛 함수는 gm/ID 범위 상수(2~30)·허용오차 상수로 이분 탐색하면서 단조성을 검사하지 않았다(DF-10). 여기서는:
0. L 은 앵커이거나 같은 모델 bin 안 두 앵커 사이(lut/CONTRACT.md 4.0) -- `gm_id_curve`·`op_point` 가 검사한다.
   `id_a = IDu·W/L` 의 L 은 앵커 값(앵커 조회) 또는 조회 L(보간).
1. 같은 곡선(`gm_id_curve`)의 VGS 마디에서 목표량 Q(VGS) = ID·W/w_m (current) 또는 gm·W/w_m (gm) 를 만든다.
2. 강반전 분지(정점 index p 부터)에서 마디 Q 가 **엄격히 증가하는 첫 구간** [p, q] 만 역산 대상으로 둔다.
3. 목표가 Q[p]..Q[q] 안이면 목표를 품는 칸 [j, j+1] 을 마디 값으로 고르고, 그 칸 안에서 곡선의 VGS Hermite
   (값 ln ID, 기울기 gm/ID -- op_point 와 같은 곡면)로 ln Q(VGS) = ln 목표를 bisection 으로 푼다
   (current: ln Q = ln ID + ln(W/w_m), gm: ln Q = ln ID + ln(gm/ID) + ln(W/w_m), gm/ID = Hermite 미분).
   그 VGS 에서 `op_point` 로 gm/ID 를 읽는다. 상수 없음.
4. 목표가 분지 값 범위 밖이면 "lut_target_out_of_range", 범위 안이지만 단조 구간 밖에서만 닿으면
   "lut_target_non_monotonic"(해가 여럿일 수 있음 -- 고르지 않고 실패). 곡선에 정의 안 된 마디 -> "lut_curve_undefined",
   고른 칸이 단조 위반 -> "lut_hermite_nonmonotone_cell".
"""
import math

import numpy as np

from ._helpers_anchor import l_position
from ._helpers_fail import seal_violation
from ._helpers_interp import hermite_root
from ._helpers_root import monotone_end, peak_index
from .gm_id_curve import gm_id_curve
from .lut_types import TargetSolution
from .point_query import op_point


def gm_id_for_target(memo, kind, w_key, L, vds, vsb, *, W, gm=None, current=None):
    """총 폭 `W`(m) 소자가 (L, vds, vsb) 에서 `gm`(S) 또는 `current`(A) 를 내는 `TargetSolution`. memo 영역 root.

    `gm`·`current` 중 정확히 하나, `W > 0` 이 아니면 `ValueError`(호출 계약 위반). 실패: 축 밖·범위 밖·비단조·
    정의 안 된 곡선·단조 위반 칸 -> `SealViolationError`(reason 은 CONTRACT.md 4절), 폭 키 없음 -> `KeyError`.
    """
    if (gm is None) == (current is None):
        raise ValueError("gm_id_for_target: gm 과 current 중 정확히 하나를 준다")
    W = float(W)
    if not W > 0:
        raise ValueError("gm_id_for_target: W 는 양수여야 한다")
    quantity = "gm" if gm is not None else "current"
    target = float(gm if gm is not None else current)
    L, vds, vsb = float(L), float(vds), float(vsb)
    curve = gm_id_curve(memo, kind, w_key, L, vds, vsb)
    sl = memo.lut.slice_map[(kind, w_key)]

    def compute():
        scale = W / sl.w_m
        context = dict(kind=kind, w_key=w_key, quantity=quantity, target=target, L=L, vds=vds, vsb=vsb, W=W)
        undefined = int(np.count_nonzero(~np.isfinite(curve.gm_id_vals)))
        if undefined:
            raise seal_violation("lut_curve_undefined", n_undefined=undefined, **context)
        q = curve.id_vals * scale if quantity == "current" else curve.id_vals * curve.gm_id_vals * scale
        p = peak_index(curve.gm_id_vals)
        end = monotone_end(q, p)
        context.update(branch_min=float(q[p:].min()), branch_max=float(q[p:].max()),
                       monotone_lo=float(q[p]), monotone_hi=float(q[end]))
        if not q[p] <= target <= q[end]:
            inside = q[p:].min() <= target <= q[p:].max()
            raise seal_violation("lut_target_non_monotonic" if inside else "lut_target_out_of_range", **context)
        seg = q[p:end + 1]
        j = p + max(int(np.searchsorted(seg, target, side="left")) - 1, 0)
        v = curve.vgs_grid
        if j == end:
            vgs = float(v[end])
        else:
            if not curve.cell_ok[j]:
                raise seal_violation("lut_hermite_nonmonotone_cell", axis="VGS", cell_lo=float(v[j]),
                                     cell_hi=float(v[j + 1]), **context)
            goal = math.log(target / scale)
            if quantity == "current":
                def residual(value, slope):
                    return value - goal
            else:
                def residual(value, slope):
                    with np.errstate(divide="ignore", invalid="ignore"):
                        return value + np.log(slope) - goal
            y, m = curve.log_id_vals, curve.gm_id_vals
            vgs = float(hermite_root(v[j], v[j + 1], y[j], y[j + 1], m[j], m[j + 1], residual))
        op = op_point(memo, kind, w_key, L, vgs, vds, vsb)
        id_a = op.IDu * W / l_position(sl.grids[0], sl.l_bins, L, memo.lut.spec.manufacturing_grid_m, memo.lut.bin_rule)[-1]
        return TargetSolution(vgs, op.gm_over_id, id_a, op.gm_over_id * id_a)

    return memo.lookup("root", "gm_id_for_target", (kind, w_key, quantity, target, L, vds, vsb, W), compute)
