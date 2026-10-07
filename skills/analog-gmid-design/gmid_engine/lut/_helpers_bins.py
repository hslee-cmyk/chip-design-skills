"""PDK 모델 bin 소속 판정 공용 helper -- 로드(앵커·W 의 bin 배정, `lut_set`)와 조회(조회 L 의 bin, `_helpers_anchor`)가
같은 규칙을 쓰게 한 곳에 둔다(사용자 결정 2026-10-07: L 보간은 같은 bin 안에서만).

bin 규칙(ngspice-46 실측, lut/CONTRACT.md 4.0): 값 x 는 `lo <= x <= hi` 인 구간에 든다(양끝 닫힘). 두 구간이 경계를
공유해 둘 다 x 를 품으면 **아래 구간(lo 가 작은 쪽)** 이 이긴다 -- 경계값 L = lmax 는 아래 bin 이다(`lmin <= L < lmax`
가 아니다). 경계 비교는 그 경계값의 1 ulp 이내를 같은 값으로 본다(패키지의 L 앵커·폭 키와 같은 원리 -- LUT 의
L 은 `um × 1e-6` 곱이라 경계와 1 ulp 어긋날 수 있다).
"""
import math


def _on_or_inside(x, bound, inside):
    """x 가 경계 `bound` 위(1 ulp 이내)이거나 `inside` 쪽에 있다."""
    return inside or abs(x - bound) <= math.ulp(bound)


def bin_index(intervals, x):
    """`intervals`((lo, hi) 쌍, lo 오름차순) 중 x 를 품는 첫 구간의 index(아래 구간 우선), 없으면 None."""
    for j, (lo, hi) in enumerate(intervals):
        if _on_or_inside(x, lo, x >= lo) and _on_or_inside(x, hi, x <= hi):
            return j
    return None
