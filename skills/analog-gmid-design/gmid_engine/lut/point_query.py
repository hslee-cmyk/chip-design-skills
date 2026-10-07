"""동작점 1점 조회 -- (L, VGS, VDS, VS) 다중선형 보간 1회로 IDu·gm/ID·gm/gds·gds/W·vth (설계 MOD1 2.3,
옛 `_sizing_bundle`/`_query_multi`). L 은 앵커이거나 같은 모델 bin 안 두 앵커 사이만(lut/CONTRACT.md 4.0).

진입점: `op_point`.

* 보간 공간(옛 B15 규칙 그대로): ID·GM·GDS 는 로그공간, VTH 는 선형. L 방향은 `l_position` 이 고른 L 격자 조각
  (앵커 1장 또는 같은 bin 의 이웃 앵커 2장)에서만 보간한다 -- 앵커 1장이면 L 가중치 (1, 0) 이라 앵커 값 그대로.
* 정규화: `IDu = ID·L / w_m`(L = 앵커 값 또는 보간 조회 L), `gds_per_w = GDS / w_m`.
"""
import math

from ._helpers_anchor import l_position
from ._helpers_interp import multilinear_interp_point_multi
from .axis_guard import check_axes
from .lut_types import AXES, OpPoint


def op_point(memo, kind, w_key, L, vgs, vds, vsb):
    """(kind, w_key) 슬라이스의 `L`, (vgs, vds, vsb) 동작점 `OpPoint`. memo 영역 point.

    실패: L 이 앵커도 같은 bin 보간도 아님·축 밖 -> `SealViolationError`(CONTRACT 4.0 사유 / lut_axis_out_of_range),
    폭 키 없음 -> `KeyError`.
    """
    sl = memo.lut.slice_map[(kind, w_key)]
    context = (("kind", kind), ("w_key", w_key))
    lo, hi, l_val = l_position(sl.grids[0], sl.l_bins, L, context)
    rest = (float(vgs), float(vds), float(vsb))
    check_axes(sl.grids[1:], AXES[1:], rest, context)

    def compute():
        part = slice(lo, hi + 1)
        log_id, log_gm, log_gds, vth = multilinear_interp_point_multi(
            (sl.grids[0][part],) + tuple(sl.grids_list[1:]),
            (sl.log_ID[part], sl.log_GM[part], sl.log_GDS[part], sl.VTH[part]), (l_val,) + rest)
        return OpPoint(
            math.exp(log_id) * l_val / sl.w_m,
            math.exp(log_gm - log_id),
            math.exp(log_gm - log_gds),
            math.exp(log_gds) / sl.w_m,
            vth,
        )

    return memo.lookup("point", "op_point", (kind, w_key, lo, hi, l_val) + rest, compute)
