"""LUT 슬라이스 축 끝 읽기 (EO-1 범위 4, 설계 41 §4.8 `domain_edge`).

진입점: `lut_axis_bounds(memo, kind, w_key) -> ((축, 첫 값, 끝 값), ...)` -- 축 = `AXES` 순서(L, VGS, VDS, VS).

LUT 세트가 이미 가진 격자(`DcSlice.grids`)의 끝 값을 그대로 읽는 순수 읽기다. 값 사본·memo 를 만들지 않고 `memo.lookup` 도 부르지 않는다.
없는 (kind, w_key) 슬라이스는 `KeyError`(폭은 `widths()` 에서만 고른다 -- `column_source` 와 같은 규칙).
"""
from .lut_types import AXES


def lut_axis_bounds(memo, kind, w_key):
    sl = memo.lut.slice_map[(kind, w_key)]
    return tuple((name, float(grid[0]), float(grid[-1])) for name, grid in zip(AXES, sl.grids))
