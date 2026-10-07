"""열 출처 판정 공용 helper -- (kind, w_key) 에서 선택 열(VDSAT·GMBS 등)을 어느 표에서 읽는지 한 곳에서 정한다
(lut/CONTRACT.md 4.3, r6). `vdsat`·`gmb`·`tol_vdsat_table`·`midpoint_l_bin_checks` 가 같은 규칙을 쓴다.

규칙(열은 그 열을 **저장한 표**에서만 읽는다 -- 폭을 건너 옮기지 않는다):
1. 그 폭 슬라이스(`DcSlice.columns`)에 열이 있으면 슬라이스(origin "slice").
2. 아니면 기준 LUT(`CapTable`)의 폭 키 `w_key` 가 조회 폭 키와 같고 그 열이 있으면 기준 LUT(origin "cap_table").
3. 아니면 `SealViolationError` `lut_column_unavailable` -- 다른 폭의 값으로 대신하지 않는다(폭 의존 가정을 박지 않음).
"""
from ._helpers_fail import seal_violation
from .lut_types import ColumnSource


def column_source(lut, kind, w_key, column, required=True):
    """(kind, w_key) 의 `column` 을 읽을 `ColumnSource`. 슬라이스 없음 -> `KeyError`(폭은 `widths()` 에서만 고른다).

    실패: 위 규칙 3 -> `required` 면 `lut_column_unavailable`(detail `column, kind, w_key, cap_w_key, slice_columns,
    cap_columns`), 아니면 None(열이 없을 때의 정의가 따로 있는 호출부 -- `gmb` 의 VS 할선).
    """
    sl = lut.slice_map[(kind, w_key)]
    if column in sl.columns:
        return ColumnSource("slice", column, kind, w_key, sl.w_m, sl.grids, sl.columns[column], sl.l_bins, sl.on_mask)
    cap = lut.cap_map.get(kind)
    if cap is not None and cap.w_key == w_key and column in cap.columns:
        return ColumnSource("cap_table", column, kind, w_key, cap.w_ref_m, cap.grids, cap.columns[column], cap.l_bins,
                            cap.on_mask)
    if not required:
        return None
    raise seal_violation("lut_column_unavailable", column=column, kind=kind, w_key=w_key,
                         cap_w_key=None if cap is None else cap.w_key, slice_columns=tuple(sorted(sl.columns)),
                         cap_columns=() if cap is None else tuple(sorted(cap.columns)))
