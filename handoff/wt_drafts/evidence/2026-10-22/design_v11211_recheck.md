# design 41 v1.12.11 둘째 커밋 재검증 (2026-10-22, 읽기 전용)

- 대상: `wt/design-it2b2` `4ab049bf`(부모 `4f27ac87`, master `8ca838d6`).
- code: `wt/it2b-code` `615ef68b`(`c4506f47` 대비 5파일, `block_columns.py` +8/−5).
- 앞 검증: `design_v11211_validation.md`(78/100).
- 실행한 것: git show·diff·log, 파일 읽기뿐이다. 임시 파일은 만들지 않았다.
- numstat: 이번 커밋 4/4, master 기준 누적 8/8. 줄 수 1993으로 같다. 바뀐 줄은 17·694·721·817이다.

## 점수: 95 / 100

## 1. 오케스트레이터 판정대로 들어갔는지 (줄 단위)

| 지적 | 오케스트레이터 판정 | 반영 위치 | 판정 |
|---|---|---|---|
| S-1 E-3 동작 변경 | 문언 유지 + 4.7-8 (9)·red test·변화표 | 694 끝 '동작 변경 4.7-8 (9)', 817 (9) | **반영.** (9)는 바뀌는 것 넷을 적었다(수렴 회차·마지막 창(θ y → V), `measured`/`unsettled`, `Window.tol_v`, 되풀이 중 tol None 갈래). 원인 = IT-2b 구현이 design 688·702와 달랐음(gap A5), 판정 = red test(해마다 tol이 다른 toy, test 작성 주체 몫)와 검증자 9회로 변화표. '원래 취지와 다름 아님(design 정의 회복)' 판단도 앞 검증 S-1 근거(688이 이미 정의)와 맞다 |
| S-2 G7 | 721을 공백 표시로 되돌림 | 721 | **반영.** 규칙 문장('걷기 전에 `kvl_fixed`', 'G_vgs 밖 갈래보다 먼저')이 빠졌다. 그 자리에 '계획 O-64 (1)이 정하지 않은 공백 / as-built `writer_plan.py:134`(`c4506f47`)는 `kvl_fixed` / 계획·사용자 공동분석 대기 / design은 우선순위·물리 판단을 정하지 않는다 / 13회로 발동 = 감사 측정 대기, 1 이상이면 724대로 멈춤'이 들어갔다. 기존 규칙 문장('F′에 닿으면 … G_vgs 밖이면 `high_impedance`')은 v1.12.10 그대로 남았다 |
| N-2 E-2 회차·`tol_v` | 반영 | 694 | **반영.** '첫 측정 뒤 어느 회차든', '`tol_v` = 마지막으로 잰 창을 잰 해의 tol, None이면 None' |
| G-1 머리말 | 반영 | 17 | **반영.** 'E-1·E-2·G6·G7은 사실 정정·빈칸, E-3은 승인된 정의를 code에 적용하는 동작 변경 -- 4.7-8 (9)', G7 = '계획 O-64 (1) 공백 표시(as-built `kvl_fixed`, 공동분석 대기)'. '동작 규칙 불변' 표기가 사라졌다 |

## 2. code `615ef68b`와 E-3·(9)의 대조 (`block_columns.py` `_solve_input_window`)

| design 문언 | code | 판정 |
|---|---|---|
| `k_max`는 첫 해의 tol(694) | `for _ in range(k_max(c.hi - c.lo, tol))`, tol = 첫 측정 해의 `_tolerance(c, values)` | 맞음 |
| 판정 tol = 매 측정 해의 `tolerance`(694·688·702) | 회차마다 `tol = _tolerance(c, again.values)` 뒤 `settled = all(abs(a − b) <= tol …)` | 맞음 |
| 되풀이 중 tol None → A6 b처럼 `unsettled`, `tol_v` None(694·702) | `if tol is None: break`. `settled`는 False로 남고(그 전 회차에 수렴했다면 이미 break), `_Kernel(…, UNSETTLED, tol=None, measured)` | 맞음 |
| 재측정 실패 → 마지막 창 y 범위, `unsettled`, `tol_v` = 마지막 창을 잰 해의 tol(694 E-2) | `again is None → break`. `measured`·`tol`은 직전 회차 값이고, 마지막 `override = measured.window` | 맞음 |
| 첫 해 tol None → A6 b(기존) | 그대로 | 맞음 |
| (9) `Window.tol_v` 값이 바뀜 | `_Kernel(…, tol, …)`의 tol이 마지막 측정 해 값 → `_windows`가 `Window(…, kernel.tol)`로 싣는다 | 맞음 |

결론: **code는 E-3·E-2·(9) 문언과 맞다.**

## 3. 새 발견

| # | 구분 | 위치 | 내용 | 수정 제안 | 원칙 적합 |
|---|---|---|---|---|---|
| N-1 | N | 694 '판정 tol' | 회차마다 비교하는 두 창(직전 창·새 창) 가운데 어느 해의 tol로 판정하는지 문언에 없다. code는 **새 해**의 tol을 쓴다. 정의 '매 측정 해의 tol'과 모순은 아니다 | '판정 tol = 새로 잰 창의 해의 tol'로 한 구절 명시. 규칙 변경은 아니다 | 적합(빈칸 채움) |
| N-2 | N | 4.7-7 test 목록 | (9) red test(해마다 tol이 다른 toy)가 4.7-8에만 있고, 4.7-7(L12 등 test 목록)에는 행이 없다. card 동결 때 test 작성 주체가 찾을 자리가 하나 더 필요하다 | L12 (a) 끝이나 card 동결에서 'L12 (f) 판정 tol 매 해 red 변형'을 지시한다. 줄 추가 없이 가능하다 | 적합(작성자≠검증자: 기대값은 test 작성 주체가 정함) |
| N-3 | N(절차) | -- | code `615ef68b`가 design 둘째 커밋 재검증보다 먼저 들어갔다. 다만 첫 커밋(`4f27ac87`)이 이미 'code를 이 정의로 고친다'를 적었고, 승인된 정의(688·702)를 따른 수정이다. 내용 위험은 없다. bkit 단계 보고에서 '구현이 design 승인 전'으로 표시할 것 | 보고 표에 표시 | 적합(절차 투명성) |

새 S(고쳐야 할 결함)는 없다.

## 4. 원칙 점검

| 원칙 | 판정 |
|---|---|
| graph 단일 정본 | 적합. 새 필드·cache 없음. `tol_v`는 기존 칸의 정의를 회복했다 |
| 만들면 배선 | 적합 |
| fail-closed | 적합. 되풀이 중 tol None → `unsettled`(metric 정의 불능) |
| 상수 발명 | 없음 |
| as-built 결정 금지 | 적합. G7 규칙 문장이 빠지고 공백 표시만 남았다. `k_max` 첫 해 tol은 사실상 유일한 선택이다 |
| 줄 수 유지 | 적합(1993, numstat 균형) |

## 미확인

- (9) red test의 존재와 결과(test 작성 주체 몫, 이번에 보지 않음).
- 검증자 9회로 변화표(감사 몫).
- 13회로에서 출력 ∈ F′의 발동 수(감사 측정 대기).
