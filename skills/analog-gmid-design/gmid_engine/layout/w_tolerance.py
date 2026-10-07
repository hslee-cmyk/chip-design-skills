"""MOD7 총 W 허용오차 (계획 N3.17 LY1, design_mod7_layout.md L1).

진입점: `w_tolerance(gm_id, tol_v, finger_w_m, grid_m) -> (lower, upper)`.

* 상한 `|dW/W| <= tol_V x (gm/ID)` -- tol_V 는 LUT leave-one-out 의 ID 환산 지표 셀 값(N3.6, tol_I = tol_V x gm 과 같은 식).
* 실현 하한 `MANUFACTURINGGRID / (2 x finger_w)` -- 제조 격자는 PDK tlef 선언(LUT spec 이 들고 온다).
상수 없음: 두 식의 입력은 LUT·PDK·sizing 값이다.
"""


def w_tolerance(gm_id, tol_v, finger_w_m, grid_m):
    """(실현 하한, 상한) 상대값. 하한 > 상한이면 그 finger_w 는 쓸 수 없다(LY1 -- 다른 finger_w·nf, 안 되면 W_request)."""
    upper = tol_v * gm_id
    lower = grid_m / (2 * finger_w_m)
    return lower, upper
