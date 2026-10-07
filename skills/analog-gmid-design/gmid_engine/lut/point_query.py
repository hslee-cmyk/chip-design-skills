"""동작점 1점 조회 -- L 앵커 하나에서 (VGS, VDS, VS) 3축 다중선형 보간 1회로 IDu·gm/ID·gm/gds·gds/W·vth
(설계 MOD1 2.3, 옛 `_sizing_bundle`/`_query_multi`; L 은 앵커 이산 키 -- 계획 LR3).

진입점: `op_point`.

* 보간 공간(옛 B15 규칙 그대로): ID·GM·GDS 는 로그공간, VTH 는 선형. L 방향 보간 없음.
* 정규화: `IDu = ID·L / w_m`(L = 앵커 값), `gds_per_w = GDS / w_m`.
"""
import math

from ._helpers_anchor import l_anchor_index
from ._helpers_interp import multilinear_interp_point_multi
from .axis_guard import check_axes
from .lut_types import AXES, OpPoint


def op_point(memo, kind, w_key, L, vgs, vds, vsb):
    """(kind, w_key) 슬라이스의 L 앵커 `L` 에서 (vgs, vds, vsb) 동작점 `OpPoint`. memo 영역 point.

    실패: L 이 앵커가 아님·축 밖 -> `SealViolationError`(lut_l_not_anchor / lut_axis_out_of_range), 폭 키 없음 -> `KeyError`.
    """
    sl = memo.lut.slice_map[(kind, w_key)]
    context = (("kind", kind), ("w_key", w_key))
    i = l_anchor_index(sl.grids[0], L, context)
    rest = (float(vgs), float(vds), float(vsb))
    check_axes(sl.grids[1:], AXES[1:], rest, context)
    l_anchor = sl.grids[0][i]

    def compute():
        log_id, log_gm, log_gds, vth = multilinear_interp_point_multi(
            sl.grids_list[1:], (sl.log_ID[i], sl.log_GM[i], sl.log_GDS[i], sl.VTH[i]), rest)
        return OpPoint(
            math.exp(log_id) * l_anchor / sl.w_m,
            math.exp(log_gm - log_id),
            math.exp(log_gm - log_gds),
            math.exp(log_gds) / sl.w_m,
            vth,
        )

    return memo.lookup("point", "op_point", (kind, w_key, i) + rest, compute)
