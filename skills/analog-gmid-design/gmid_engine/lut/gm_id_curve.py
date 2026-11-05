"""고정 (L, VDS, VS) 의 gm/ID 곡선 -- VGS 격자 마디의 (ln ID, gm/ID) 와 칸별 Hermite 사용 가능 여부 (설계 MOD1 2.1,
lut/CONTRACT.md 4.2).

진입점: `gm_id_curve`.

L 은 앵커이거나 같은 모델 bin 안 두 앵커 사이만(`l_position`, lut/CONTRACT.md 4.0). 마디 값은 `node_values`
(op_point 와 같은 텐서곱의 (1)(2) 단계: ln ID = VS Hermite(GMBS 열이 있을 때)·VDS Hermite·L 선형, gm/ID = 저장 GM/ID 의 L·VDS·VS
선형)이고,
마디 사이 곡선은 그 마디 값·기울기의 VGS Hermite 다 -- 그래서 이 곡선 위 역산(`vgs_for_gm_id`·`gm_id_for_target`)과
`op_point` 가 같은 곡면이다. 옛 `_gm_id_curve` 블록 복사(다선형 보간 2회)는 r5 에서 없어졌다(CONTRACT 6절).
"""
import numpy as np

from ._helpers_anchor import l_position
from ._helpers_interp import REASON_FC, REASON_SLOPE, node_values
from .axis_guard import check_axes
from .lut_types import AXES, CLASS_HERMITE, Curve


def gm_id_curve(memo, kind, w_key, L, vds, vsb):
    """(kind, w_key) 슬라이스의 `L`, 고정 (vds, vsb) 곡선 `Curve`(읽기 전용 배열). memo 영역 curve.

    `id_vals` 는 슬라이스 폭 w_m 에서의 ID(A). `cell_ok`[j] 가 거짓인 칸(단조 위반)은 역산 함수가 쓰지 않는다.
    실패: L 이 앵커도 같은 bin 보간도 아님·축 밖 -> `SealViolationError`, 폭 키 없음 -> `KeyError`.
    """
    sl = memo.lut.slice_map[(kind, w_key)]
    context = (("kind", kind), ("w_key", w_key))
    lo, hi, l_val = l_position(sl.grids[0], sl.l_bins, L, memo.lut.spec.manufacturing_grid_m, memo.lut.bin_rule, context)
    vds, vsb = float(vds), float(vsb)
    check_axes((sl.grids[2], sl.grids[3]), (AXES[2], AXES[3]), (vds, vsb), context)

    def compute():
        log_id, gm_id, cell_fc_ok, _ = node_values(sl, lo, hi, l_val, vds, vsb, range(len(sl.grids[1])))
        arrays = (np.exp(log_id), gm_id, log_id, cell_fc_ok)
        for arr in arrays:
            arr.setflags(write=False)
        finite = np.isfinite(gm_id)
        defined = finite[:-1] & finite[1:]
        classes = tuple(CLASS_HERMITE if ok and fin else (REASON_FC if fin else REASON_SLOPE)
                        for ok, fin in zip(cell_fc_ok, defined))
        return Curve(sl.VGS_grid, arrays[0], arrays[1], arrays[2], arrays[3], classes)

    return memo.lookup("curve", "gm_id_curve", (kind, w_key, lo, hi, l_val, vds, vsb), compute)
