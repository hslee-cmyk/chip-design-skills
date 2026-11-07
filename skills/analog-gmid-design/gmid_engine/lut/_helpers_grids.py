"""npz 축 읽기 공용 helper -- 슬라이스·기준 LUT·잡음 r1·mismatch r1 파일이 같은 (L, VGS, VDS, VS) 축 읽기를 쓴다
(`lut_set`·`noise_set`·`mismatch_set`)."""
import numpy as np

from ._helpers_fail import schema_rejected
from .lut_types import AXES


def npz_grids(npz, *, reason, path):
    """npz 의 축 `AXES` 마다 float tuple -- ((L...), (VGS...), (VDS...), (VS...)).

    축 키(`AXES` 가운데 하나라도)가 파일에 없으면 부르는 자리가 넘긴 축 사유 `reason` 으로 `SchemaRejectedError`
    detail `{reason, path, axis}`(axis = 없는 키 가운데 `AXES` 순서 첫 것). 축 키 판정은 이 helper 하나다."""
    for axis in AXES:
        if axis not in npz.files:
            raise schema_rejected(reason, path=path, axis=axis)
    return tuple(tuple(float(x) for x in np.asarray(npz[axis], dtype=float)) for axis in AXES)


def npz_condition_mismatch(npz, conditions):
    """npz 의 측정 조건(corner·temp_c)이 기준 조건 `conditions`(키 정렬 쌍 tuple, `recorded` 포함)와 다르면 (키, npz 값, 기준 값),
    같거나 기준이 기록 없음이면 None."""
    want = dict(conditions)
    if not want.get("recorded"):
        return None
    for key, cast in (("corner", str), ("temp_c", float)):
        if key in want and (key not in npz.files or cast(npz[key]) != want[key]):
            return key, (cast(npz[key]) if key in npz.files else None), want[key]
    return None
