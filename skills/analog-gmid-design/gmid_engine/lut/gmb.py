"""body 트랜스컨덕턴스 gmb (설계 MOD1 2.8, 계획 N3.8, lut/CONTRACT.md 4.1 표·4.4, r6).

진입점: `gmb`.

* [r6] **정본 = LUT GMBS 열**(BSIM `gmbs`, 오라클 SPICE 가 쓰는 정의): 그 (kind, w_key) 에 GMBS 열이 있으면(`column_source`
  규칙 -- LUT v2 는 기준 LUT 폭 w_ref 에만 있다) gmb = ID(점) × r, r = 파생 열 GMBS_PER_ID(= GMBS/ID, 로드 1회)의 모든 축
  선형 보간, ID(점) = 같은 (L, vgs, vds, vsb) 의 `op_point`(Hermite 곡면, ID = IDu·w_m/L). GMBS/ID 는 gm/ID 처럼 매끈한 비라
  ID 를 곱하면 약반전에서 GMBS 를 값 공간 선형으로 잇는 것보다 정확하다(격자점에서는 저장 GMBS 그대로). 가중치 0 이 아닌
  모서리에 ID ≤ 0 인 점(VDS = 0 열)이 있어 r 이 정의되지 않으면 GMBS 열의 값 공간 선형 보간을 쓴다.
* 열이 없으면(옛 12-L 세트, w_ref 가 아닌 폭) r5 의 정의 -- 보간면의 VS 방향 해석 미분: VS 칸 [vs_k, vs_k+1] (`cell` 규칙)
  안에서 ln ID 는 VS 에 선형이라 `d ln ID / d vsb = (lnID(vs_k+1) − lnID(vs_k)) / (vs_k+1 − vs_k)`(두 끝은 같은 (L, VGS, VDS)
  의 `op_point`), gmb = −ID · d ln ID / d vsb. 스텝 상수 없음. 이 할선은 칸 경계에서 계단이다(정본과의 차는 CONTRACT 4.4 실측).
* 값은 슬라이스 폭 w_m 기준(A/V); 소자 총 폭 W 의 값은 부르는 쪽이 `× W / w_m`.
"""
import math

from ._helpers_anchor import l_position
from ._helpers_columns import column_source
from ._helpers_interp import cell, linear_point
from .axis_guard import check_axes
from .lut_types import AXES
from .point_query import op_point


def _from_column(memo, kind, w_key, L, rest, ratio_src, id_point):
    """GMBS 열 정의: ID(점) × (GMBS/ID 선형 보간), 비가 정의 안 되면 GMBS 값 공간 선형."""
    context = (("kind", kind), ("table", ratio_src.origin), ("w_key", w_key))
    lo, hi, l_val = l_position(ratio_src.grids[0], ratio_src.l_bins, L, context)
    check_axes(ratio_src.grids[1:], AXES[1:], rest, context)
    part = slice(lo, hi + 1)
    grids = (ratio_src.grids[0][part],) + tuple(ratio_src.grids[1:])
    (ratio,) = linear_point(grids, (ratio_src.array[part],), (l_val,) + rest)
    if math.isfinite(ratio):
        return id_point * ratio
    value_src = column_source(memo.lut, kind, w_key, "GMBS")
    (value,) = linear_point(grids, (value_src.array[part],), (l_val,) + rest)
    return float(value)


def gmb(memo, kind, w_key, L, vgs, vds, vsb):
    """(kind, w_key) 슬라이스의 `L`, (vgs, vds, vsb) 에서 gmb(A/V, 폭 w_m 기준). memo 영역 point.

    실패: L 이 앵커도 같은 bin 보간도 아님·축 밖 -> `SealViolationError`(op_point 와 같은 사유), 폭 키 없음 -> `KeyError`.
    """
    sl = memo.lut.slice_map[(kind, w_key)]
    context = (("kind", kind), ("w_key", w_key))
    lo, hi, l_val = l_position(sl.grids[0], sl.l_bins, L, context)
    rest = (float(vgs), float(vds), float(vsb))
    check_axes(sl.grids[1:], AXES[1:], rest, context)
    ratio_src = column_source(memo.lut, kind, w_key, "GMBS_PER_ID", required=False)

    def compute():
        here = op_point(memo, kind, w_key, L, *rest)
        id_point = here.IDu * sl.w_m / l_val
        if ratio_src is not None:
            return _from_column(memo, kind, w_key, L, rest, ratio_src, id_point)
        vs = sl.grids[AXES.index("VS")]
        k, _ = cell(vs, rest[-1])
        lo_op, hi_op = (op_point(memo, kind, w_key, L, rest[0], rest[1], x) for x in (vs[k], vs[k + 1]))
        slope = (math.log(hi_op.IDu) - math.log(lo_op.IDu)) / (vs[k + 1] - vs[k])
        return -id_point * slope

    return memo.lookup("point", "gmb", (kind, w_key, lo, hi, l_val) + rest, compute)
