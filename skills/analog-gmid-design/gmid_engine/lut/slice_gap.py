"""슬라이스 조회 불능 사유 판정 (WB-1, interface §2, J-3) -- `w_of` 를 만드는 쪽이 후보 제외와 오류를 가르는 정의 하나.

진입점: `is_slice_gap`.

조회 불능 = 그 슬라이스가 이 (L, 전압) 점을 표현하지 못하는 사유 다섯(`SLICE_GAP_REASONS`). 그 밖 사유(`lut_column_unavailable` 등)는 후보 제외가 아니라 오류다.
"""
from gmid_engine.core import SealViolationError

SLICE_GAP_REASONS = ("lut_axis_out_of_range", "lut_l_not_anchor", "lut_l_outside_model_bins", "lut_l_bin_unbracketed",
                     "lut_l_cross_bin")


def is_slice_gap(exc):
    """`exc` 가 `SealViolationError` 이고 reason 이 `SLICE_GAP_REASONS` 에 들면 참."""
    return isinstance(exc, SealViolationError) and dict(exc.record.detail).get("reason") in SLICE_GAP_REASONS
