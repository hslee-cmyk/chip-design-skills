"""MOD7 W 허용오차 (계획 N3.17 LY1, design_mod7_layout.md L1, 사용자 결정 2026-10-07 Q4 (iv)).

진입점: `w_tolerance(gm_id, tol_v, finger_w_m, grid_m) -> WTolerance`.

* 상한 `|dW/W_need| <= tol_V x (gm/ID)` -- tol_V 는 그 폭 슬라이스의 LUT tol_V `id_equivalent` 셀 값(N3.6 ID 환산 지표,
  tol_I = tol_V x gm 과 같은 식). 다른 지표는 없다(tol_V 지표는 id_equivalent 하나).
* 실현 하한 `MANUFACTURINGGRID / (2 x finger_w)` -- 제조 격자는 PDK tlef 선언(LUT spec 이 들고 온다).
* 실효 허용오차 = max(상한, 하한). 하한 > 상한이면 `grid_dominated`(격자 지배 -- 보간 정합보다 격자가 거칠다)로 기록한다.
상수 없음: 식의 입력은 LUT·PDK·sizing 값이다. 이 허용오차는 후보 순위 기준이다(합격 판정은 레이아웃 뒤 재검증, Q4 (ii)).
"""
from .contract_output import WTolerance


def w_tolerance(gm_id, tol_v, finger_w_m, grid_m):
    """`WTolerance(lower, upper, effective, grid_dominated)` 상대값."""
    upper = tol_v * gm_id
    lower = grid_m / (2 * finger_w_m)
    return WTolerance(lower, upper, max(upper, lower), lower > upper)
