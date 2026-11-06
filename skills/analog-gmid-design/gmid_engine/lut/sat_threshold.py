"""포화 기준 VDsat 정본 함수 -- 그 점의 (VDsat, tol, 사유) 를 내는 유일한 곳 (card HC-S, HC-D §3, 사용자 결정 O-15 (C)·O-44 (2)·O-183·O-185·O-204).

진입점: `sat_threshold(memo, kind, w_key, L, vgs, vds, vsb) -> SatBound`. `SatBound(vdsat_v, tol_v, reason)`: `vdsat_v` = `vdsat`(V, 크기) 또는 None, `tol_v` = 그 점
셀의 `tol_vdsat_table(...).at(L, vds)`(V, **'구별 불가' 기록 전용 -- 판정·절단에 쓰지 않는다**) 또는 None, `reason` = 값이 없는 사유 또는 None.

위에서 아래로 첫 맞는 행:

| # | 조건 | vdsat_v | tol_v | reason |
|---|---|---|---|---|
| 1 | vds < 0 (LUT 조회 0) | None | None | `reverse_vds` |
| 2 | VDSAT 열 없음 | None | None | `vdsat_column_unavailable` |
| 3 | L 위치·축 밖 | None | None | `lut_domain` |
| 4 | 값 있음, tol 셀 None | `vdsat(...)` | None | None |
| 5 | 값 있음 | `vdsat(...)` | tol 셀 | None |

역방향 VDS 는 LUT 축 오류가 아니라 '포화 아님' 사유다(행 1). 슬라이스 없음(`KeyError`)과 위 둘 밖의 LUT 실패 사유는 그대로 다시 던진다(0 으로 바꾸지 않는다).
`REASON_OFF_DECLARED` 는 필드 `device.dc_sat_v` 쪽에서만 쓰는 사유다(`off` 선언 소자 -- 이 함수는 내지 않는다). 새 memo 자리 없음: `vdsat`·`tol_vdsat_table` 의 memo 를 탄다.
"""
import dataclasses

from gmid_engine.core import SealViolationError

from .vdsat_query import vdsat
from .vdsat_tolerance import tol_vdsat_table

REASON_REVERSE_VDS = "reverse_vds"
REASON_VDSAT_COLUMN_UNAVAILABLE = "vdsat_column_unavailable"
REASON_LUT_DOMAIN = "lut_domain"
REASON_OFF_DECLARED = "off_declared"                      # 필드 쪽에서만(`dc_solve`)

_COLUMN_UNAVAILABLE = "lut_column_unavailable"             # lut CONTRACT 4.3 열 출처 규칙 3
_DOMAIN_REASONS = ("lut_axis_out_of_range", "lut_l_not_anchor", "lut_l_outside_model_bins", "lut_l_bin_unbracketed", "lut_l_cross_bin")   # lut CONTRACT 4.0 축·L 위치 밖


@dataclasses.dataclass(frozen=True)
class SatBound:
    """포화 기준 한 점: `vdsat_v`(V) · `tol_v`(V, 기록 전용) · `reason`(값 없음 사유, 값이 있으면 None)."""

    vdsat_v: object
    tol_v: object
    reason: object


def sat_threshold(memo, kind, w_key, L, vgs, vds, vsb):
    if vds < 0:
        return SatBound(None, None, REASON_REVERSE_VDS)
    try:
        value = vdsat(memo, kind, w_key, L, vgs, vds, vsb)
    except SealViolationError as exc:
        reason = dict(exc.record.detail).get("reason")
        if reason == _COLUMN_UNAVAILABLE:
            return SatBound(None, None, REASON_VDSAT_COLUMN_UNAVAILABLE)
        if reason in _DOMAIN_REASONS:
            return SatBound(None, None, REASON_LUT_DOMAIN)
        raise
    return SatBound(value, tol_vdsat_table(memo, kind, w_key).at(L, vds), None)
