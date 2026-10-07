"""고정 (L, VDS, VS) 의 gm/ID 곡선 -- VGS 격자 위 (ID, gm/ID) (설계 MOD1 2.1 `_gm_id_curve` 블록 복사).

진입점: `gm_id_curve`.

`_curve_arrays` 의 문장은 옛 `SemiEmpiricalGmIdLUT._gm_id_curve`(SR:455) 의 알고리즘 구간(캐시 줄 제외)을 그대로
옮긴 것이다. 이름 바꿈만 있다: `self` -> `sl`(DcSlice), `_multilinear_interp` -> `multilinear_interp`,
`_grids_list`·`_log_ID`·`_log_GM` -> `grids_list`·`log_ID`·`log_GM`(대조 규칙은 CONTRACT.md 6절).
"""
import numpy as np

from ._helpers_interp import multilinear_interp
from .axis_guard import check_axes
from .lut_types import AXES, Curve


def _curve_arrays(sl, L, vds, vsb):
    n = len(sl.VGS_grid)
    pts = np.column_stack([
        np.full(n, L), sl.VGS_grid, np.full(n, vds), np.full(n, vsb),
    ])
    log_id = np.asarray(multilinear_interp(sl.grids_list, sl.log_ID, pts))
    # 2026-09-08(B15) -- GM도 로그공간에서 보간해 ID와 **같은 공간**에서 나눈다.
    log_gm = np.asarray(multilinear_interp(sl.grids_list, sl.log_GM, pts))
    id_vals = np.exp(log_id)
    gm_id_vals = np.exp(log_gm - log_id)
    result = (id_vals, gm_id_vals)
    return result


def gm_id_curve(memo, kind, w_key, L, vds, vsb):
    """(kind, w_key) 슬라이스의 고정 (L, vds, vsb) 곡선 `Curve`(읽기 전용 배열). memo 영역 curve.

    `id_vals` 는 슬라이스 폭 w_m 에서의 ID(A). 실패: 축 밖 -> `SealViolationError`, 폭 키 없음 -> `KeyError`.
    """
    sl = memo.lut.slice_map[(kind, w_key)]
    L, vds, vsb = float(L), float(vds), float(vsb)
    check_axes((sl.grids[0], sl.grids[2], sl.grids[3]), (AXES[0], AXES[2], AXES[3]), (L, vds, vsb),
               (("kind", kind), ("w_key", w_key)))

    def compute():
        id_vals, gm_id_vals = _curve_arrays(sl, L, vds, vsb)
        id_vals.setflags(write=False)
        gm_id_vals.setflags(write=False)
        return Curve(sl.VGS_grid, id_vals, gm_id_vals)

    return memo.lookup("curve", "gm_id_curve", (kind, w_key, L, vds, vsb), compute)
