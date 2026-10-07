"""동작점 1점 조회 -- 슬라이스 4축 다중선형 보간 1회로 IDu·gm/ID·gm/gds·gds/W·vth (설계 MOD1 2.3, 옛 `_sizing_bundle`/`_query_multi`).

진입점: `op_point`.

* 보간 공간(옛 B15 규칙 그대로): ID·GM·GDS 는 로그공간, VTH 는 선형.
* 정규화: `IDu = ID·L / w_m`(옛 `raw*L/W_ref` 와 같은 식, W_ref 자리에 슬라이스 폭), `gds_per_w = GDS / w_m`.
"""
import math

from ._helpers_interp import multilinear_interp_point_multi
from .axis_guard import check_axes
from .lut_types import AXES, OpPoint


def op_point(memo, kind, w_key, L, vgs, vds, vsb):
    """(kind, w_key) 슬라이스의 (L, vgs, vds, vsb) 동작점 `OpPoint`. memo 영역 point.

    실패: 축 밖 -> `SealViolationError`(lut_axis_out_of_range), 폭 키 없음 -> `KeyError`.
    """
    sl = memo.lut.slice_map[(kind, w_key)]
    point = (float(L), float(vgs), float(vds), float(vsb))
    check_axes(sl.grids, AXES, point, (("kind", kind), ("w_key", w_key)))

    def compute():
        log_id, log_gm, log_gds, vth = multilinear_interp_point_multi(
            sl.grids_list, (sl.log_ID, sl.log_GM, sl.log_GDS, sl.VTH), point)
        return OpPoint(
            math.exp(log_id) * point[0] / sl.w_m,
            math.exp(log_gm - log_id),
            math.exp(log_gm - log_gds),
            math.exp(log_gds) / sl.w_m,
            vth,
        )

    return memo.lookup("point", "op_point", (kind, w_key) + point, compute)
