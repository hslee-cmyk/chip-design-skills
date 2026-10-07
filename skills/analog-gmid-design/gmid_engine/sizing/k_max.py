"""반복 상한 K_max (계획 N3.6 허용오차 식, DEC-32, 설계 3.4).

진입점: `k_max(width, tol) -> int`.

K_max = ceil(log2(width / tol)) -- 폭 `width` 구간을 bisection 으로 `tol` 까지 좁히는 반복 수. 고정점 반복도 같은 상한을
쓴다(그보다 느린 고정점은 bisection 보다 나쁘다). width ≤ tol 이면 1(한 번 평가로 판정). 상수 없음.
"""
import math


def k_max(width, tol):
    """`width`·`tol` 은 양의 유한 수(V). 아니면 `ValueError`."""
    width = float(width)
    tol = float(tol)
    if not (math.isfinite(width) and math.isfinite(tol) and width > 0 and tol > 0):
        raise ValueError("k_max: width·tol 은 양의 유한 수여야 한다: " + repr((width, tol)))
    if width <= tol:
        return 1
    return math.ceil(math.log2(width / tol))
