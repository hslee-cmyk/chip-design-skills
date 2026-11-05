"""포화 기준 VDsat 격자 입구 -- 한 슬라이스의 VDSAT 격자 배열 (card HC-S, HC-D §3 J2).

진입점: `sat_threshold_grid(memo, kind, w_key) -> ndarray | None` -- 축 (L, VGS, VDS, VS) 의 VDSAT 격자(V). 격자점에서 `sat_threshold(...).vdsat_v` 는 이 배열 원소와 같다
(4.3 '격자점에서는 저장값 그대로'). 열 출처는 `column_source`(슬라이스 열 우선, 아니면 같은 폭 키의 기준 LUT 열). 열이 없으면 None(대체값 없음).
격자를 한 번 읽어 쓰는 소비자(`edge_costs` 등)가 점 입구를 격자점마다 다시 부르지 않게 한다 -- 배열은 LUT 가 가진 읽기 전용 배열 그대로이고 사본·저장 자리를 새로 두지 않는다.
열 격자가 슬라이스 격자와 다르면(기준 LUT 열이 다른 축을 가진 경우) 배열을 슬라이스 격자로 읽을 수 없어 `SchemaRejectedError`(reason `vdsat_grid_not_slice_grid`) -- 다른 격자의 값으로 대신하지 않는다.
"""
import numpy as np

from gmid_engine.core import SchemaRejectedError, SealViolationError

from ._helpers_columns import column_source

_COLUMN_UNAVAILABLE = "lut_column_unavailable"


def sat_threshold_grid(memo, kind, w_key):
    try:
        src = column_source(memo.lut, kind, w_key, "VDSAT")
    except SealViolationError as exc:
        if dict(exc.record.detail).get("reason") == _COLUMN_UNAVAILABLE:
            return None
        raise
    slice_grids = memo.lut.slice_map[(kind, w_key)].grids
    if len(src.grids) != len(slice_grids) or any(not np.array_equal(a, b) for a, b in zip(src.grids, slice_grids)):
        raise SchemaRejectedError(detail={"reason": "vdsat_grid_not_slice_grid", "kind": kind, "w_key": str(w_key), "origin": src.origin})
    return src.array
