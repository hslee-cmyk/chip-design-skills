"""배치된 손가락 폭이 가리키는 슬라이스 키 (FS-1, interface §2) -- w_f 칸 키·레이아웃 뒤 소자·`off` 소자가 쓴다.

진입점: `slice_of_finger`.

`slice_of_finger(lut, kind, w_f_m)`: 손가락 폭 `w_f_m` 의 격자 정수 키가 `widths(lut, kind)`(= W_min 이상 슬라이스 = w_f 후보 집합)에 있으면 그 키.
격자 밖이거나 후보가 아니면 `SealViolationError`(reason `slice_missing`, detail `kind`, `w_f_m`). LUT 값 조회 0.
"""
from ._helpers_fail import seal_violation
from ._helpers_width import width_key
from .widths import widths


def slice_of_finger(lut, kind, w_f_m):
    """손가락 폭 `w_f_m`(m) -> 슬라이스 키(정수)."""
    key, on_grid = width_key(w_f_m, lut.spec.manufacturing_grid_m)
    if not on_grid or key not in widths(lut, kind):
        raise seal_violation("slice_missing", kind=kind, w_f_m=w_f_m)
    return key
