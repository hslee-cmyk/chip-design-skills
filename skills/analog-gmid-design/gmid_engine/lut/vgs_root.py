"""목표 gm/ID -> VGS (강반전 분지의 가장 큰 VGS 해) (설계 MOD1 2.3, 옛 `vgs_for_gm_id`/`_solve_vgs`, DEC-11).

진입점: `vgs_for_gm_id`.

분지 규칙은 `_helpers_root`(정점 오른쪽만, 그 안에서 가장 오른쪽 구간). 분지 안에 해가 없으면 실패한다 --
옛 엔진처럼 누설 분지(VGS≈0) 해를 돌려주지 않는다(lut/CONTRACT.md 3절).
"""
from ._helpers_fail import seal_violation
from ._helpers_root import peak_index, strong_inversion_root
from .gm_id_curve import gm_id_curve


def vgs_for_gm_id(memo, kind, w_key, gm_id, L, vds, vsb):
    """`L`(앵커 또는 같은 모델 bin 안 보간, CONTRACT 4.0)의 (vds, vsb) 곡선에서 gm/ID = `gm_id` 인 강반전 분지의 VGS(V).
    memo 영역 root.

    실패: L 이 앵커도 같은 bin 보간도 아님·축 밖 -> `SealViolationError`(CONTRACT 4.0 사유 / lut_axis_out_of_range), 분지 안 해 없음 -> `SealViolationError`
    (reason "lut_no_strong_inversion_root", detail 에 목표·분지 gm/ID 범위·정점 VGS), 폭 키 없음 -> `KeyError`.
    """
    gm_id, L, vds, vsb = float(gm_id), float(L), float(vds), float(vsb)
    curve = gm_id_curve(memo, kind, w_key, L, vds, vsb)

    def compute():
        g = curve.gm_id_vals
        vgs = strong_inversion_root(g, curve.vgs_grid, gm_id)
        if vgs is None:
            p = peak_index(g)
            branch = g[p:]
            raise seal_violation("lut_no_strong_inversion_root", kind=kind, w_key=w_key, gm_id=gm_id, L=L,
                                 vds=vds, vsb=vsb, branch_gm_id_min=float(branch.min()),
                                 branch_gm_id_max=float(branch.max()), peak_vgs=float(curve.vgs_grid[p]))
        return float(vgs)

    return memo.lookup("root", "vgs_for_gm_id", (kind, w_key, gm_id, L, vds, vsb), compute)
