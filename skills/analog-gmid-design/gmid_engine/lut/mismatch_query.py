"""mismatch 감도 조회 -- 변수별 1σ 섭동 DVGS_k 와 기준 bin slope (설계 41 §6.4-2b API, lut/CONTRACT.md 10.2).

진입점: `mismatch_dvgs`.

* 데이터: `LutSet.mismatch[kind]`(생성기 mismatch 모드 산출 -- 변수의 `*_slope_spectre` 를 0 → 1σ 로 바꾼 섭동 곡선이 기준 곡선 칸의 ID 에서 내는 |VGS| 차).
  면은 기준 LUT 폭 `w_ref_m` 에서 잰 것이라 (kind, w_key) 의 폭 키가 기준 LUT 폭 키와 같을 때만 읽는다(다른 폭으로 대신하지 않는다,
  `lut_column_unavailable` `column` = "DVGS"). 소자 폭·bin 이 다를 때의 환산은 `mismatch_sigma_vgs`.
* 보간: (L, VGS, VDS, VS) 모든 축 선형(L 은 4.0 규칙). 기울기 자료가 없다(섭동 곡선의 도함수 열이 없다). 정의 안 된 칸(섭동 곡선이 격자 밖·기준 ID ≤ 0)이
  가중치 0 이 아닌 모서리에 있으면 실패한다.
* `slope_ref` = 조회 L 이 든 bin(앵커 하한 쪽 앵커의 기록 -- 같은 bin 이라 같다)에서 기준 폭이 쓴 slope 값(그 bin 이 변수를 안 쓰면 0.0).
* 실패(`SealViolationError`): mismatch 파일 없음 `lut_mismatch_unavailable`, 폭 키 불일치 `lut_column_unavailable`, 정의 안 된 칸 `lut_mismatch_undefined`,
  L·축 -> CONTRACT 4.0·4.1 사유(context table "mismatch").
"""
import math
import types

from ._helpers_anchor import l_position
from ._helpers_fail import seal_violation
from ._helpers_interp import linear_point
from .axis_guard import check_axes
from .lut_types import AXES, MismatchSens


def mismatch_dvgs(memo, kind, w_key, L, vgs, vds, vsb):
    """(kind, w_key) 의 `L`, (vgs, vds, vsb) 에서 `MismatchSens`(기준 폭 `w_m`). memo 영역 point."""
    table = memo.lut.mismatch.get(kind)
    if table is None:
        raise seal_violation("lut_mismatch_unavailable", kind=kind, w_key=w_key)
    if table.w_key != w_key:
        raise seal_violation("lut_column_unavailable", column="DVGS", kind=kind, w_key=w_key, cap_w_key=table.w_key)
    context = (("kind", kind), ("table", "mismatch"), ("w_key", w_key))
    lo, hi, l_val = l_position(table.grids[0], table.l_bins, L, context)
    rest = (float(vgs), float(vds), float(vsb))
    check_axes(table.grids[1:], AXES[1:], rest, context)

    def compute():
        part = slice(lo, hi + 1)
        values = linear_point((table.grids[0][part],) + tuple(table.grids[1:]),
                              tuple(table.dvgs[p][part] for p in table.params), (l_val,) + rest)
        undefined = tuple(p for p, v in zip(table.params, values) if not math.isfinite(v))
        if undefined:
            raise seal_violation("lut_mismatch_undefined", parameters=undefined, L=float(l_val), vgs=rest[0], vds=rest[1],
                                 vsb=rest[2], kind=kind, w_key=w_key)
        slopes = {p: (0.0 if value is None else value) for p, _ident, value in table.slope_ref[lo]}
        return MismatchSens(types.MappingProxyType(dict(zip(table.params, (float(v) for v in values)))),
                            types.MappingProxyType(slopes), table.w_ref_m)

    return memo.lookup("point", "mismatch_dvgs", (kind, w_key, lo, hi, l_val) + rest, compute)
