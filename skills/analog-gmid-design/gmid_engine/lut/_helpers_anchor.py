"""L 앵커 이산 키 공용 helper -- L 은 LUT L 앵커 값만 쓴다(계획 LR3, 사용자 확정 2026-10-07; 폭 이산 키와 같은 원리).

L 방향 보간은 하지 않는다. 조회 L 은 앵커 하나와 1 ulp(그 앵커의 `math.ulp`) 이내로 같아야 한다. 허용은 대칭이다 --
앵커 일치 검사를 범위 검사보다 먼저 하므로 격자 양끝 앵커도 바깥쪽 1 ulp 까지 그 앵커로 받는다.
"""
import bisect
import math

from ._helpers_fail import seal_violation
from .axis_guard import check_axes


def l_anchor_index(l_grid, L, context=()):
    """`L` 과 1 ulp 이내로 같은 앵커의 index(양방향 대칭, 양끝 앵커 포함).

    앵커 일치가 없을 때: 격자 범위 밖 -> `SealViolationError`(lut_axis_out_of_range, axis "L"),
    범위 안 -> `SealViolationError`(reason "lut_l_not_anchor", value, below, above + context).
    """
    L = float(L)
    i = bisect.bisect_left(l_grid, L)
    for j in (i - 1, i):
        if 0 <= j < len(l_grid) and abs(L - l_grid[j]) <= math.ulp(l_grid[j]):
            return j
    check_axes((l_grid,), ("L",), (L,), context)
    k = bisect.bisect_right(l_grid, L)
    raise seal_violation("lut_l_not_anchor", value=L, below=float(l_grid[k - 1]), above=float(l_grid[k]),
                         **dict(context))
