"""body 트랜스컨덕턴스 gmb -- 같은 보간면의 VS 방향 해석 미분 (설계 MOD1 2.8, 계획 N3.8 'MOD1 수치미분').

진입점: `gmb`.

VS 축은 선형 보간 축이다(DEC-87 -- GMBS 열이 생기기 전). 그래서 조회점이 든 VS 칸 [vs_k, vs_k+1] (`cell` 규칙,
마지막 격자점은 마지막 칸) 안에서 ln ID 는 VS 에 대해 선형이고 `d ln ID / d vsb = (lnID(vs_k+1) − lnID(vs_k)) /
(vs_k+1 − vs_k)` 다. 두 끝 ln ID 는 같은 (L, VGS, VDS) 의 `op_point`(같은 곡면 -- VGS·VDS Hermite) 에서 읽는다
(IDu 의 정규화 L/w_m 은 차에서 지워진다). gmb = dID/dVBS = −dID/dVSB = −ID · d ln ID / d vsb. 스텝 상수 없음.
값은 슬라이스 폭 w_m 기준(A/V); 소자 총 폭 W 의 값은 부르는 쪽이 `× W / w_m`.
"""
import math

from ._helpers_anchor import l_position
from ._helpers_interp import cell
from .axis_guard import check_axes
from .lut_types import AXES
from .point_query import op_point


def gmb(memo, kind, w_key, L, vgs, vds, vsb):
    """(kind, w_key) 슬라이스의 `L`, (vgs, vds, vsb) 에서 gmb(A/V, 폭 w_m 기준). memo 영역 point.

    실패: L 이 앵커도 같은 bin 보간도 아님·축 밖 -> `SealViolationError`(op_point 와 같은 사유), 폭 키 없음 -> `KeyError`.
    """
    sl = memo.lut.slice_map[(kind, w_key)]
    context = (("kind", kind), ("w_key", w_key))
    lo, hi, l_val = l_position(sl.grids[0], sl.l_bins, L, context)
    rest = (float(vgs), float(vds), float(vsb))
    check_axes(sl.grids[1:], AXES[1:], rest, context)

    def compute():
        vs = sl.grids[AXES.index("VS")]
        k, _ = cell(vs, rest[-1])
        lo_op, hi_op, here = (op_point(memo, kind, w_key, L, rest[0], rest[1], x) for x in (vs[k], vs[k + 1], rest[-1]))
        slope = (math.log(hi_op.IDu) - math.log(lo_op.IDu)) / (vs[k + 1] - vs[k])
        return -here.IDu * sl.w_m / l_val * slope

    return memo.lookup("point", "gmb", (kind, w_key, lo, hi, l_val) + rest, compute)
