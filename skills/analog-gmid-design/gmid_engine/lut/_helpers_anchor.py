"""조회 L 의 위치 공용 helper -- L 앵커이거나, 같은 PDK 모델 bin 안 두 이웃 앵커 사이(사용자 결정 2026-10-07).

* 앵커: 조회 L 이 앵커 하나와 1 ulp(그 앵커의 `math.ulp`) 이내면 그 앵커(보간 없음, 앵커 값을 L 로 쓴다). 허용은 대칭 --
  앵커 일치 검사를 범위 검사보다 먼저 하므로 격자 양끝 앵커도 바깥쪽 1 ulp 까지 그 앵커로 받는다.
* 보간: 앵커가 아니고 격자 범위 안이면 양옆 앵커 (below, above) 가 **같은 bin**(`LBinMap.anchor_bin`)일 때만 그 둘로
  L 방향 선형 보간한다. bin 은 구간이라 두 앵커가 같은 bin 이면 그 사이 L 도 그 bin 이다.
* 거부(bin 경계를 건너는 보간 금지): bin 지도가 없으면 `lut_l_not_anchor`, 조회 L 을 품는 모델 bin 이 없으면
  `lut_l_outside_model_bins`, 조회 L 의 bin 에 LUT 앵커가 1개 이하면 `lut_l_bin_unbracketed`, 2개 이상이지만 L 이
  그 앵커들 바깥(양옆 앵커가 서로 다른 bin)이면 `lut_l_cross_bin`. lut/CONTRACT.md 4.0.
"""
import bisect
import math

from ._helpers_bins import bin_index
from ._helpers_fail import seal_violation
from .axis_guard import check_axes


def l_position(l_grid, l_bins, L, context=()):
    """`(lo, hi, l_value)`: 앵커면 `(i, i, l_grid[i])`, 같은 bin 보간이면 `(k − 1, k, L)`(L 은 float 그대로).

    `l_bins` = 그 표의 `LBinMap`. 실패: 격자 범위 밖 -> `lut_axis_out_of_range`(axis "L"), 그 밖은 모듈 docstring 의
    사유 키(`SealViolationError`, detail `value, below, above` + bin 정보 + `context`).
    """
    L = float(L)
    i = bisect.bisect_left(l_grid, L)
    for j in (i - 1, i):
        if 0 <= j < len(l_grid) and abs(L - l_grid[j]) <= math.ulp(l_grid[j]):
            return j, j, l_grid[j]
    check_axes((l_grid,), ("L",), (L,), context)
    k = bisect.bisect_right(l_grid, L)
    detail = dict(context, value=L, below=float(l_grid[k - 1]), above=float(l_grid[k]))
    if not l_bins.bins:
        raise seal_violation("lut_l_not_anchor", bins="unavailable", **detail)
    b_lo, b_hi = l_bins.anchor_bin[k - 1], l_bins.anchor_bin[k]
    if b_lo == b_hi:
        return k - 1, k, L
    detail.update(below_bin=l_bins.bins[b_lo].model, above_bin=l_bins.bins[b_hi].model)
    b = bin_index(tuple((x.lmin, x.lmax) for x in l_bins.bins), L)
    if b is None:
        raise seal_violation("lut_l_outside_model_bins", **detail)
    members = tuple(float(a) for a, m in zip(l_grid, l_bins.anchor_bin) if m == b)
    detail.update(bin=l_bins.bins[b].model, bin_lmin=l_bins.bins[b].lmin, bin_lmax=l_bins.bins[b].lmax,
                  bin_anchors=members)
    raise seal_violation("lut_l_bin_unbracketed" if len(members) <= 1 else "lut_l_cross_bin", **detail)
