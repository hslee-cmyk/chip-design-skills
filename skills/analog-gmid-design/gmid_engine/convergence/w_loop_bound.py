"""W_request 루프 반복 상한 K_max (계획 N3.6 허용오차 식 `K_max = ceil(log2(구간폭 / tol))`, 설계 40 §3.9 (3) '구간 = W 변경 비', LR9).

진입점: `w_loop_bound(placements, sized_w) -> (k_max, max_dlnw, tol)`.

* 구간폭 = 사이징 W(`sized_w` = {소자: W})에서 레이아웃이 요구한 실현 W 까지의 상대 변화 크기 `max |ln(W_실현 / W_사이징)|`(로그 W 축의 구간 -- W 비는 무차원).
* tol = 그 배치 소자들의 레이아웃 실효 W 허용오차(LY1, 상대, 소자별 `tol_V(id_equivalent) x gm/ID` 또는 격자 하한) 중 최솟값 -- 가장 엄격한 소자가 반복 수를 정한다.
* `k_max` = sizing `k_max(구간폭, tol)`(같은 구간을 bisection 으로 tol 까지 좁히는 횟수, 고정점도 그 이하여야 한다). 구간폭이 tol 이하이면 한 번 평가로 판정(1).
  새 상수 없음. 배치 소자가 없으면 (1, 0.0, 0.0).
"""
import math

from gmid_engine.sizing import k_max


def w_loop_bound(placements, sized_w):
    if not placements:
        return 1, 0.0, 0.0
    width = max(abs(math.log(p.W_m / sized_w[p.name])) for p in placements)
    tol = min(p.tol_effective for p in placements)
    if width <= tol:
        return 1, width, tol
    return k_max(width, tol), width, tol
