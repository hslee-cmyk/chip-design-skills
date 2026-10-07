"""LUT 축 범위 검사 -- 축 밖 입력을 클램프·외삽하지 않고 실패로 (설계 MOD1 2.3 공통 규칙, 계획 LR3·DF-27).

진입점: `check_axes`.
"""
from ._helpers_fail import seal_violation


def check_axes(grids, names, point, context=()):
    """`point` 의 축마다 `grids[축][0] <= 값 <= grids[축][-1]` 인지 본다(NaN 도 밖). 모두 안이면 None.

    밖이면 첫 위반 축으로 `SealViolationError`(detail: reason "lut_axis_out_of_range", axis, value, lo, hi,
    + `context` 의 (키, 값) 쌍 -- 보통 kind·w_key).
    """
    for grid, name, value in zip(grids, names, point):
        lo, hi = grid[0], grid[-1]
        if not lo <= value <= hi:
            raise seal_violation("lut_axis_out_of_range", axis=name, value=float(value), lo=float(lo),
                                 hi=float(hi), **dict(context))
