"""목표 gm/ID -> VGS (강반전 분지의 가장 큰 VGS 해) (설계 MOD1 2.3, 옛 `vgs_for_gm_id`/`_solve_vgs`, DEC-11·DEC-87).

진입점: `vgs_for_gm_id`.

분지 규칙은 `_helpers_root`(정점 오른쪽만, 그 안에서 가장 오른쪽 칸, 칸 안은 Hermite 미분 = 목표인 VGS). 곡선은
`gm_id_curve`(op_point 와 같은 곡면)라 결과 VGS 에서 `op_point(...).gm_over_id` 가 목표와 같다(bisection 분해능 안).
분지 안에 해가 없으면 실패한다 -- 옛 엔진처럼 누설 분지(VGS≈0) 해를 돌려주지 않는다(lut/CONTRACT.md 3절).
고른 칸이 단조 위반(`Curve.cell_ok` 거짓)이거나 곡선에 기울기가 정의되지 않은 마디(gm/ID NaN)가 있으면 실패한다.
"""
import numpy as np

from ._helpers_fail import seal_violation
from ._helpers_root import peak_index, strong_inversion_root
from .gm_id_curve import gm_id_curve


def vgs_for_gm_id(memo, kind, w_key, gm_id, L, vds, vsb):
    """`L`(앵커 또는 같은 모델 bin 안 보간, CONTRACT 4.0)의 (vds, vsb) 곡선에서 gm/ID = `gm_id` 인 강반전 분지의 VGS(V).
    memo 영역 root.

    실패(`SealViolationError`): L·축 -> CONTRACT 4.0 사유 / lut_axis_out_of_range, 곡선에 정의 안 된 마디 ->
    "lut_curve_undefined", 분지 안 해 없음 -> "lut_no_strong_inversion_root"(detail 에 목표·분지 gm/ID 범위·정점 VGS),
    고른 칸 단조 위반 -> "lut_hermite_nonmonotone_cell". 폭 키 없음 -> `KeyError`.
    """
    gm_id, L, vds, vsb = float(gm_id), float(L), float(vds), float(vsb)
    curve = gm_id_curve(memo, kind, w_key, L, vds, vsb)

    def compute():
        g = curve.gm_id_vals
        detail = dict(kind=kind, w_key=w_key, gm_id=gm_id, L=L, vds=vds, vsb=vsb)
        undefined = int(np.count_nonzero(~np.isfinite(g)))
        if undefined:
            raise seal_violation("lut_curve_undefined", n_undefined=undefined, **detail)
        vgs, cell = strong_inversion_root(curve.vgs_grid[None, :], curve.log_id_vals[None, :], g[None, :],
                                          np.asarray([gm_id]))
        if cell[0] < 0:
            p = peak_index(g)
            branch = g[p:]
            raise seal_violation("lut_no_strong_inversion_root", branch_gm_id_min=float(branch.min()),
                                 branch_gm_id_max=float(branch.max()), peak_vgs=float(curve.vgs_grid[p]), **detail)
        j = int(cell[0])
        if not curve.cell_ok[j]:
            raise seal_violation("lut_hermite_nonmonotone_cell", axis="VGS", cell_lo=float(curve.vgs_grid[j]),
                                 cell_hi=float(curve.vgs_grid[j + 1]), **detail)
        return float(vgs[0])

    return memo.lookup("root", "vgs_for_gm_id", (kind, w_key, gm_id, L, vds, vsb), compute)
