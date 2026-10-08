"""소자 잡음 계수 조회 -- 게이트 환산 S_vg(f) = A/f^EF + B 의 A·B·EF (설계 41 §7.2 API, lut/CONTRACT.md 9.3).

진입점: `noise_params`.

* 데이터: `LutSet.noise[kind]`(기준 LUT 의 `SVG2_1HZ`·`SVG2_HF` + 잡음 r1 파일의 로그 이분 점)을 `noise_planes` 가 A·B 면으로 분해한 것. 면은 기준 LUT
  폭 `w_ref_m` 에서 잰 것이라 (kind, w_key) 의 폭 키가 기준 LUT 폭 키와 같을 때만 읽는다 -- 다른 폭으로 대신하지 않는다(`lut_column_unavailable`,
  `column` = "SVG2"). 폭 W 소자는 호출부가 두 값을 `w_m`/W 배 한다(S_vg 는 gm 에 반비례, 같은 전류밀도에서 폭에 반비례).
* 보간: ln A·ln B 를 (L, VGS, VDS, VS) 모든 축 선형(L 은 4.0 규칙 -- 앵커 또는 같은 bin 안 두 앵커 사이). 가중치 0 이 아닌 모서리 중 B 미상(`no_feedthrough_free_point`
  ·`nonpositive`)이 하나라도 있으면 그 점의 B 는 미상 -- `b_status` 에 사유, `B` = None, `A` 는 면의 값(미상 모서리는 S_vg(1 Hz) 기준)을 그대로 보간한다.
* 실패(`SealViolationError`): 잡음 파일 없음 `lut_noise_unavailable`, 폭 키 불일치 `lut_column_unavailable`, L·축 -> CONTRACT 4.0·4.1 사유(context table "noise").
"""
import math

from ._helpers_anchor import l_position
from ._helpers_fail import seal_violation
from ._helpers_interp import linear_point
from .axis_guard import check_axes
from .lut_types import AXES, NOISE_B_STATUS, NoiseParams
from .noise_planes import STATUS_NO_POINT, STATUS_NONPOSITIVE, noise_planes


def noise_params(memo, kind, w_key, L, vgs, vds, vsb):
    """(kind, w_key) 의 `L`, (vgs, vds, vsb) 에서 `NoiseParams`(기준 폭 `w_m`). memo 영역 point."""
    table = memo.lut.noise.get(kind)
    if table is None:
        raise seal_violation("lut_noise_unavailable", kind=kind, w_key=w_key)
    if table.w_key != w_key:
        raise seal_violation("lut_column_unavailable", column="SVG2", kind=kind, w_key=w_key, cap_w_key=table.w_key)
    context = (("kind", kind), ("table", "noise"), ("w_key", w_key))
    lo, hi, l_val = l_position(table.grids[0], table.l_bins, L, context)
    rest = (float(vgs), float(vds), float(vsb))
    check_axes(table.grids[1:], AXES[1:], rest, context)
    planes = noise_planes(memo, kind)

    def compute():
        part = slice(lo, hi + 1)
        grids = (table.grids[0][part],) + tuple(table.grids[1:])
        ln_a, ln_b, bad_point, bad_sign = linear_point(
            grids, (planes.ln_a[part], planes.ln_b_filled[part], planes.flag_no_point[part], planes.flag_nonpositive[part]),
            (l_val,) + rest)
        status = NOISE_B_STATUS[0]
        if bad_sign > 0:
            status = NOISE_B_STATUS[STATUS_NONPOSITIVE]
        elif bad_point > 0:
            status = NOISE_B_STATUS[STATUS_NO_POINT]
        known = status == NOISE_B_STATUS[0]
        return NoiseParams(math.exp(ln_a), math.exp(ln_b) if known else None, table.ef, status, table.w_ref_m)

    return memo.lookup("point", "noise_params", (kind, w_key, lo, hi, l_val) + rest, compute)
