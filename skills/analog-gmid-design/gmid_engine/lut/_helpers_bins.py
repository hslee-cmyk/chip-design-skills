"""PDK 모델 bin 소속 판정 공용 helper -- 로드(앵커·W 의 bin 배정, `lut_set`)와 조회(조회 L 의 bin, `_helpers_anchor`)가
같은 규칙을 쓰게 한 곳에 둔다(사용자 결정 2026-10-07: L 보간은 같은 bin 안에서만).

bin 규칙(WB-1 범위 0, DEC-105 (2), lut/CONTRACT.md 4.0.1): 구간 끝과 x 를 모두 제조 격자 정수 `round(값 / grid_m)` 로 바꿔
정수끼리 비교한다(float 근접 허용폭 없음). 값 x 는 `lo <= x <= hi` 인 구간에 든다(양끝 닫힘). 경계를 공유한 두 구간이
모두 x 를 품으면 선언 규칙 `rule` 이 고른다 -- `"lower"` = 앞(lo 가 작은) 구간, `"upper"` = 뒤 구간. 규칙은 LUT 세트의 bin 선언
(`LutSet.bin_rule`)에서 오고 이 함수에 기본값이 없다.
"""

import math

from ._helpers_interp import LINEAR_CONDITIONS

RULES = ("lower", "upper")
_PAIR = len(LINEAR_CONDITIONS)   # 앵커 2개 bin = 두 앵커 사이 L 선형 보간의 점 수(선형 보간 조건 정의 1곳에서 유도)


def bin_index(intervals, x, grid_m, rule):
    """`intervals`((lo, hi) 쌍, lo 오름차순) 중 x 를 품는 구간의 index, 품는 구간이 없으면 None.

    품는 구간이 둘이면 `rule`("lower" 앞 구간, "upper" 뒤 구간)이 고른다. `rule` 이 어휘 밖이면 `ValueError`.
    """
    if rule not in RULES:
        raise ValueError("bin_index: rule 은 %s 중 하나" % (RULES,))
    if not math.isfinite(x):
        return None
    xi = round(x / grid_m)
    hits = [j for j, (lo, hi) in enumerate(intervals) if round(lo / grid_m) <= xi <= round(hi / grid_m)]
    if not hits:
        return None
    return hits[0] if rule == "lower" else hits[-1]


def midpoint_bracket(l_grid, l_bins, L_m, grid_m, rule):
    """중점 L 하나 `L_m` 이 앵커 2개 bin 의 두 앵커 사이인지의 판별 `(bin index | None, 사유 | None)` -- 정의 1곳(LM-1e, D40 (v)):
    `midpoint_l_bin_checks` 의 skipped 사유와 `load_lut_set` 의 D7 적재 거부(`bin_missing_external`)가 둘 다 이 함수를 부른다. 순수 함수(memo 없음).

    `l_grid` = 슬라이스 L 앵커 tuple, `l_bins` = 그 `LBinMap`. 위에서 아래로 첫 맞는 행: bin 지도 비어 있음 `(None, "bins_unavailable")`,
    앵커와 같은 격자 정수 `(None, "is_anchor")`, 어느 bin 에도 없음 `(None, "outside_model_bins")`, 그 bin 앵커 1개 `(b, "single_point")`,
    3개 이상 `(b, "bin_has_interior_anchors")`, 앵커 2개지만 두 앵커 사이 아님 `(b, "not_bracketed")`, 두 앵커 사이 `(b, None)`.
    """
    if not l_bins.bins:
        return None, "bins_unavailable"
    if math.isfinite(L_m) and any(round(L_m / grid_m) == round(a / grid_m) for a in l_grid):
        return None, "is_anchor"
    b = bin_index(tuple((x.lmin, x.lmax) for x in l_bins.bins), L_m, grid_m, rule)
    if b is None:
        return None, "outside_model_bins"
    members = tuple(i for i, a in enumerate(l_bins.anchor_bin) if a == b)
    if len(members) != _PAIR:
        return b, "single_point" if len(members) < _PAIR else "bin_has_interior_anchors"
    i0, i1 = members
    if not l_grid[i0] < L_m < l_grid[i1]:
        return b, "not_bracketed"
    return b, None
