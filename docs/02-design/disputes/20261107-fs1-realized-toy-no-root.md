---
id: 20261107-fs1-realized-toy-no-root
spec_card: docs/02-design/specs/20261107-fs1.spec.md
test_id: skills/analog-gmid-design/gmid_engine/tests/sizing/test_block_dc.py::test_dc_solve_realized_eval_uses_hand_oracle_m
test_id: skills/analog-gmid-design/gmid_engine/tests/sizing/test_block_dc.py::test_dc_solve_layout_reseal_uses_request_rows_and_base_fingers
---
## 문제의 test

* D-5/D-6 `test_dc_solve_realized_eval_uses_hand_oracle_m`: `mirror_setup` toy, 정합 칸(M1, M2) 키 200 · M3 키 100 으로 탐색 평가 뒤 `size_and_seal(ctx, th, wf, realized=RealizeInput(ev.snapshot))` 가 성공해 `dc_finger.m` = 손 oracle 이어야 한다.
* D-7 `test_dc_solve_layout_reseal_uses_request_rows_and_base_fingers`: 같은 toy 에서 기준(실현) 점 뒤 `RealizedGeometry(w_request=(("M2", (3, 2e-6)),))` 로 `size_and_seal(..., layout=geom)` 가 성공해야 한다.

## 근거(oracle 또는 사용자 원문)

두 test 의 입력으로 만들어지는 **실현 W' 고정 KCL 이 이 toy 에서 레일(0 ~ 1.8 V) 안에 근이 없다**. 그래서 `dc_solve` 의 재풀이가 interface/계획이 정한 fail-closed 로 끝난다
(`NonconvergentError` reason `newton_line_search`; 계획 DEC-105 (2) '푼 노드가 레일 밖 = 후보 실패', spec '거부해야 할 입력'). 구현 선택과 무관한 사실이다.

실측(code worktree; toy LUT `write_r4_bins_lut(widths=(1e-6, 2e-6))`, `mirror_setup` 의 I1 = 4.913473791448256e-07, M3 게이트 0.7 V; LUT `op_point` 로 읽은 전류, out 노드 KCL = I(M3, pmos 공급) − I(M2, nmos) = 0):

* D-5: 손 oracle m 은 (M1, M2, M3) = (1, 3, 2) → W' = (2e-6, 6e-6, 2e-6). 다이오드 vgs = 0.56690. out ∈ [0, 1.8] 전 구간에서 I(M3) > I(M2): out = 0 에서 2.0280e-06 > 1.3928e-06, out = 1.8 에서 1.6940e-06 > 1.6675e-06 (격자 0.1 V 19점 전부 부호 같음) → 근 없음.
  ((1, 2, …) 로는 이 칸의 쌍 비 오차 E1 이 0.667 이라 interface §1 의 사전식 최소가 아니다 -- 정수화 자체는 R-1/P 시리즈와 같은 함수가 낸다.)
* D-7: 기준 점의 M1 = 1e-6, M2 = 4e-6 에서 M2 만 W' = 3·2e-6 = 6e-6 으로 바꾼다. 다이오드 vgs = 0.61195 고정, out ∈ [0, 1.8] 전 구간에서 I(M2) > I(M3): out = 0 에서 2.7731e-06 > 2.0280e-06, out = 1.8 에서 3.3200e-06 > 1.6940e-06 → 근 없음.
* 대조(근이 있는 경우): 모든 칸 키 100(D-5 와 같은 함수·같은 입력 꼴, m = (1, 4, 2))이면 재풀이가 수렴해 `dc_finger.m` = 손 oracle, `residual` = `m·w_f/W_θ − 1`(M2: −8.13e-07), 근 out ≈ 0.46 V 에서 I(M2) = I(M3).

## 요청

두 test 의 입력을 근이 있는 구성으로 고친다(예: D-5 는 모든 칸 키 100, 또는 M3 전류를 손 oracle W' 에서 KCL 이 닫히게 정하는 θ; D-7 은 요청 행 (nf, finger_w) 를 기준 W' 와 같은 전류 균형이 가능한 값으로). 또는 interface 가
'이 toy 의 실현 재풀이는 근이 없을 수 있다 → 후보 실패(lost)' 를 기대값으로 정하게 한다. 구현이 레일 안 근을 만들어 내도록 요구하는 것은 fail-closed(spec '거부해야 할 입력')와 모순이라 코드 쪽으로는 맞출 수 없다.
