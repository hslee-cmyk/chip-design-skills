"""PDK 모델 bin 소속 판정 공용 helper -- 로드(앵커·W 의 bin 배정, `lut_set`)와 조회(조회 L 의 bin, `_helpers_anchor`)가
같은 규칙을 쓰게 한 곳에 둔다(사용자 결정 2026-10-07: L 보간은 같은 bin 안에서만).

bin 규칙(WB-1 범위 0, DEC-105 (2), lut/CONTRACT.md 4.0.1): 구간 끝과 x 를 모두 제조 격자 정수 `round(값 / grid_m)` 로 바꿔
정수끼리 비교한다(float 근접 허용폭 없음). 값 x 는 `lo <= x <= hi` 인 구간에 든다(양끝 닫힘). 경계를 공유한 두 구간이
모두 x 를 품으면 선언 규칙 `rule` 이 고른다 -- `"lower"` = 앞(lo 가 작은) 구간, `"upper"` = 뒤 구간. 규칙은 LUT 세트의 bin 선언
(`LutSet.bin_rule`)에서 오고 이 함수에 기본값이 없다.
"""

import math

RULES = ("lower", "upper")


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
