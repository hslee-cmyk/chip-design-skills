"""전류밀도 좌표 ln IDu -> VGS (강반전 분지 위 단조 역산) (계획 DEC-88, 설계 40 §2.3, lut/CONTRACT.md 3.1).

진입점: `vgs_for_current_density`.

쓰기 소자의 독립 좌표는 반전 좌표 `ln IDu`(IDu = ID·L/w_m, DEC-88)이고 VGS 는 그 좌표의 역산으로 나온다. 곡선은 `gm_id_curve`(op_point 와 같은
곡면): 강반전 분지(정점 index p 이상)에서 마디 ln ID 가 엄격히 증가하는 첫 구간 [p, e] 만 역산 대상이다. 목표 ln ID = ln IDu + ln w_m − ln L
(L = 앵커 값 또는 같은 bin 보간 L). 목표가 [y_p, y_e] 안(양끝은 exp·log 왕복 반올림 2 ulp 허용)이면 목표를 품는 칸 j 를 고르고 그 칸의 VGS Hermite(값 ln ID, 기울기 gm/ID)에서
`hermite_root` 로 푼다 -- 그래서 결과 VGS 의 `op_point(...).IDu` 는 목표와 부동소수 분해능 안에서 같다(한 곡면).

옛 경로(`gm_id_for_target(W = w_m, current = IDu·w_m/L)` 로 같은 양을 푸는 sizing 의 임시 우회)를 대체한다. 실패(`SealViolationError`):
곡선에 정의 안 된 마디 `lut_curve_undefined`, 목표가 분지 값 밖 `lut_target_out_of_range`, 범위 안이나 단조 구간 밖 `lut_target_non_monotonic`,
고른 칸 단조 위반 `lut_hermite_nonmonotone_cell`(detail 에 `quantity` = "ln_idu", `target` = 목표 ln ID, `branch_min`·`branch_max` = 분지 ln ID
범위, `ln_idu` = 입력 좌표).
"""
import math

import numpy as np

from ._helpers_anchor import l_position
from ._helpers_fail import seal_violation
from ._helpers_interp import hermite_root
from ._helpers_root import monotone_end, peak_index
from .gm_id_curve import gm_id_curve

QUANTITY = "ln_idu"


def vgs_for_current_density(memo, kind, w_key, ln_idu, L, vds, vsb):
    """(kind, w_key) 슬라이스의 `L`, (vds, vsb) 곡선에서 반전 좌표 ln IDu = `ln_idu` 인 강반전 분지의 VGS(V). memo 영역 root.

    폭 키 없음 -> `KeyError`, L 이 앵커도 같은 bin 보간도 아님·축 밖 -> CONTRACT 4.0 사유 / lut_axis_out_of_range."""
    ln_idu, L, vds, vsb = float(ln_idu), float(L), float(vds), float(vsb)
    curve = gm_id_curve(memo, kind, w_key, L, vds, vsb)
    sl = memo.lut.slice_map[(kind, w_key)]
    l_val = l_position(sl.grids[0], sl.l_bins, L, (("kind", kind), ("w_key", w_key)))[2]

    def compute():
        detail = dict(kind=kind, w_key=w_key, quantity=QUANTITY, target=ln_idu, L=L, vds=vds, vsb=vsb)
        g, y, v = curve.gm_id_vals, curve.log_id_vals, curve.vgs_grid
        undefined = int(np.count_nonzero(~np.isfinite(g)))
        if undefined:
            raise seal_violation("lut_curve_undefined", n_undefined=undefined, **detail)
        goal = ln_idu + math.log(sl.w_m) - math.log(l_val)
        detail.update(target=goal, ln_idu=ln_idu)                  # target = 목표 ln ID(슬라이스 폭 w_m 기준, 분지 값과 같은 단위)
        p = peak_index(g)
        end = monotone_end(y, p)
        slack = 2 * math.ulp(max(abs(y[p]), abs(y[end]), abs(goal)))     # exp·log 왕복 반올림(분지 양끝 마디 좌표가 입력일 때)
        if y[p] - slack <= goal <= y[end] + slack:
            goal = min(max(goal, float(y[p])), float(y[end]))
        detail.update(branch_min=float(y[p:].min()), branch_max=float(y[p:].max()), monotone_lo=float(y[p]),
                      monotone_hi=float(y[end]))
        if not y[p] <= goal <= y[end]:
            inside = y[p:].min() <= goal <= y[p:].max()
            raise seal_violation("lut_target_non_monotonic" if inside else "lut_target_out_of_range", **detail)
        j = p + max(int(np.searchsorted(y[p:end + 1], goal, side="left")) - 1, 0)
        if j == end:
            return float(v[end])
        if not curve.cell_ok[j]:
            raise seal_violation("lut_hermite_nonmonotone_cell", axis="VGS", cell_lo=float(v[j]),
                                 cell_hi=float(v[j + 1]), **detail)
        return float(hermite_root(v[j], v[j + 1], y[j], y[j + 1], g[j], g[j + 1], lambda value, slope: value - goal))

    return memo.lookup("root", "vgs_for_current_density", (kind, w_key, ln_idu, L, vds, vsb), compute)
