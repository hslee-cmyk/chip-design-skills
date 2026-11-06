"""배치된 손가락 폭이 가리키는 슬라이스 키 (WB-1, interface §2) -- 레이아웃 뒤 소자와 `off` 소자가 쓴다.

진입점: `slice_of_finger`.

`slice_of_finger(lut, kind, L, w_f_m)`: 손가락 폭 `w_f_m` 의 격자 정수 키가 `widths(lut, kind)`(= W_min 이상 슬라이스)에 있으면 그 키.
격자 밖이거나 슬라이스가 아니거나 W_min 밖이면 `SealViolationError`(reason `slice_missing`, detail `kind`, `L`, `w_f_m`). w_hi·`w_of` 를 쓰지 않는다(LUT 값 조회 0).
"""
from ._helpers_fail import seal_violation
from ._helpers_width import width_key
from .widths import widths


def slice_of_finger(lut, kind, L, w_f_m):
    """손가락 폭 `w_f_m`(m) -> 슬라이스 키(정수)."""
    key, on_grid = width_key(w_f_m, lut.spec.manufacturing_grid_m)
    if not on_grid or key not in widths(lut, kind):
        raise seal_violation("slice_missing", kind=kind, L=L, w_f_m=w_f_m)
    return key
