# design 41 v1.12.10(IT-2b) 독립 검증 (2026-10-22, 읽기 전용)

- 대상: `wt/design-it2b`(design/it2b), `33228e46`·`9890855f`. 부모는 master `52b9dd81`. 파일 하나(`docs/02-design/features/gain-budget-gmid-sizing.41-gain-budget.design.md`)가 바뀌었다.
- numstat은 34/34이다. 줄 수는 1992로 같다(옛판·새판 줄 단위 대조 결과 길이 같음). 바뀐 줄은 브리핑 목록(3·4·17·688·694·695·697·705-715·721·724·737·759-762·780·786·788·804·807·810·814·817·834·835)과 같다.
- 정본과 근거
  - 계획 v6.33: 같은 worktree `plan.md`의 1514(N6.6 범위 1), 1524(완료 조건 (0)~(12)), 1937·1941(N6.20 범위 (4)·완료 조건 (8)(e)).
  - 사용자 결정: `_drafts/user_decisions.md` 727-745(O-98·O-100·O-101·O-102·O-103).
  - 분석: `it2b_test_gaps.md`, `it2b_code_disputes.md`.
  - 오케스트레이터 실측: scratchpad `yend/out/yends.jsonl`(52행). 대조용으로 판정 agent 실측 `wt/_scratch_it2b_disp/out/yends.jsonl`(162행)도 읽었다.
  - 엔진: `wt/it2b-code` `85847b49`. test: `wt/it2b-test` `88335ef6`. master 엔진 비교: `52b9dd81:…/sizing/block_columns.py`.
- 실행한 것: git show·diff·grep, 파일 읽기, jsonl 집계뿐이다. 엔진·test는 실행하지 않았다.

## 점수: 84 / 100

| 구분 | 건수 | 요지 |
|---|---|---|
| G(계획 반영) | 1 | (S4-가) D에서 (8)(e)(iii) 변화표 몫이 인용 괄호에만 있다(작음) |
| S(사실·정합, 고쳐야 함) | 5 | 4.7-8 (8) 측정 근거(파일·base 1회 누락), L12 (e) (i) 기존 단언 오기, D (d) 측정 꼴(docstring) 미정, design 40 미갱신, IT-2c `Circuit` 접근이 실제로 막힘 |
| N(가독성·정확도, 권장) | 7 | 아래 표 |

계획 v6.33 반영은 대체로 빠짐없고 다르지 않다. O-98 묶음 (가)~(라), 갈래를 한 번 정하고 병합 순서를 고정한 것, (S4-나) 기간 동작, (9)(a)~(d)가 모두 들어 있다. 감점은 사실 인용 정확도와 IT-2c로 넘긴 미정 한 건에서 나왔다.

---

## G -- 계획 반영

### 검사 1 결과 (항목별 대조)

| 계획 v6.33 요소 | 계획 위치 | design 위치 | 판정 |
|---|---|---|---|
| O-98 묶음 (가) 노드 풀이 블록 불일치 상태·소자 열 쓰기, 판정 함수 = 공용 전도 판정 함수, 행 여유 부호 판정 금지 | 1514 | 706·711·712·713 | 같음 |
| 불일치 종류 셋(triode 포화·triode 꺼짐·off 전도) | 1514 | 710 | 같음 |
| 불일치 상태 값·소자 열 칸도 묶음에 듦(이름은 design) | 1514 | 688 'S-4 갈래 몫의 꼴'·713 | 같음(이름 `"op_mismatch"`·`status_detail`) |
| (나) 같은 점 봉인 거부, (다) 세 metric code definitional, (라) 불일치 toy | 1514 | 706·713·786·810 | 같음 |
| 공용 함수 없이 (가)를 넣지 않음(규칙 1) | 1514 | 706 | 같음 |
| 갈래 정의 (S4-가)/(S4-나) | 1514 | 707·708 | 같음 |
| 갈래는 IT-2b 착수 때 한 번, IT-2b~IT-2d 같은 갈래, 기록 = card 재동결 | 1514 | 709 | 같음 |
| (S4-나)면 EO-1은 IT-1+IT-2 통합 병합 뒤(`off` 행도 같음, N6.1) | 1514 | 709·835 | 같음 |
| (S4-나)에서 IT-2에 남는 것(triode 행 영 교차, 행 종류 {포화, triode}, 전도·문턱 계산 0, 불일치 정의 0, 상태 칸은 IT-2 범위) | 1514 | 688·708·810 | 같음 |
| (S4-나) 기간 동작(O-100, 원래 취지와 다름(작음, 발동 0), 특별 처리 0, x₀ 밖·lo > hi 가능, 봉인 미차단) | 1514 | 715 | 같음(거의 원문) |
| 완료 조건 (9)(a) 전제 단언 + 영 교차 = 창 끝(커널·다듬은 창, 손계산) | 1524 (9) | 810 (a) | 같음('다듬은 창은 IT-2d' 덧붙임은 card 나눔 표시라 맞음) |
| (9)(b) 경계 행 종류 = {포화, triode} | 1524 (9) | 810 (b) | 같음 |
| (9)(c) 정적 AST만, (i)~(iii), 새 계수기·monkeypatch 없음 | 1524 (9) | 810 (c) | 같음 |
| (9)(d) 불일치 상태 값·소자 열 칸·metric code 정의 포함 0(`git grep`, 문자열·상수 이름) | 1524 (9) | 810 (d) | 같음. 측정 꼴은 S-3 |
| (S4-가)면 IT-2가 N6.20 (8)(e)(i)~(iii)와 같은 단언 | 1524 (9)·1941 (8)(e) | 707·810 | (i)(ii)는 펼쳐 적었다. (iii)은 괄호 인용뿐이다. G-1 |
| N6.20 (8)(b) 호출 자리 수에 블록 판정 호출 하나가 더해짐 | 1941 (8)(b) | 707 | 같음 |

### G-1 (작음) (S4-가) D에 (8)(e)(iii) 변화표 몫이 펼쳐 적혀 있지 않다
- 위치: 41:810 '(S4-가)이면 D가 더 진다(계획 (9) -- N6.20 (8)(e)(i)~(iii)와 같은 단언)'.
- 근거: 뒤에 펼친 목록은 `off` toy와 불일치 toy 셋의 (가)~(라)뿐이다. 계획 1941 (8)(e)(iii) '변화표(위 (d))에 노드 풀이 블록 출력의 불일치 상태 행 변화와 원인'은 4.7-8에도 D에도 없다.
- 수정 제안: 810 (S4-가) 목록 끝이나 4.7-8 동작 변경 목록에 '(S4-가)면 변화표에 `dc_columns` 출력 불일치 상태 행 변화·원인' 한 구절을 더한다. 줄 추가 없이 된다.
- 원칙 적합: 계획 반영 보완이다. 새 규칙·상수가 없다.

---

## S -- 사실·정합 (고쳐야 함)

### S-1 4.7-8 (8)의 측정 근거가 인용 파일과 맞지 않고, O-103 기록의 'base 1회'가 빠졌다 (검사 5)
- 위치: 41:817 (8) '9회로 탐색의 y 끝점 방문 head 0회, 봉인 7 거부율 변화 0. … 측정 근거 = 오케스트레이터 실측(… 봉인점 6개 y 0·1 재평가) `…/scratchpad/yend/out/yends.jsonl`'.
- 실측(jsonl 집계)
  - 오케스트레이터 파일(52행)에는 **2회로만** 있다(common_gate_amplifier, two_stage_ota_sf).
    - 탐색: common_gate head(호출 34, y_exact_1 = 0), common_gate base(호출 43, **y_exact_1 = 1**, 봉인 7 실패 0), two_stage_ota_sf head·base(끝점 0).
    - 재평가: common_gate y = 1은 head·base 모두 5/6 거부(−7.95e-12). common_gate y = 0은 head 6/6 거부(−4.76e-13 ~ −3.60e-12), base 0/6. two_stage_ota_sf y = 0은 head 6/6 거부(−6.553e-6), base 0/6. two_stage_ota_sf y = 1은 둘 다 0/6.
  - '9회로 탐색' 수치는 판정 agent 파일 `wt/_scratch_it2b_disp/out/yends.jsonl`(162행)에 있다. 9회로 head 끝점 0, base는 common_gate y = 1 한 번이다. 봉인 7 실패 수는 9회로 모두 head = base이다.
  - O-103 원문(`user_decisions.md:745`)은 '탐색 끝점 방문 **head 0·base 1**'이다.
- 판정
  - 수치 자체(slack 값, 거부율 변화 0)는 맞다.
  - 그러나 (가) '9회로'의 근거 파일을 잘못 인용했다. 인용한 파일에는 2회로만 있다. (나) base 1회가 빠졌다. 이것은 **오도할 소지가 있다**. base는 같은 예산(40)에서 실제로 y 상자 경계(y = 1)에 갔다. SLSQP가 경계에 닿는 일이 실제로 일어남을 보이는 유일한 관측이다. head 0회만 적으면 '끝점 방문 = 구조적으로 0'처럼 읽혀 '발동 0'을 과장한다. head 0회는 궤적이 바뀐 결과로 보는 것이 맞다(common_gate 호출 수 34 대 43). 큰 예산이나 경계 최적점에서의 발생률은 판정 agent도 '미확인'으로 남겼다.
  - (다) 인용한 경로는 세션 임시 폴더(`AppData/Local/Temp/claude/…/scratchpad`)이다. 세션이 끝나면 근거가 사라진다.
  - (라) 'common_gate y = 1, head·base 모두 slack −7.9e-12'는 6점 중 5점이다(src 4는 봉인). '모두'는 회로 둘(head·base)을 뜻하는 말로 읽히도록 '5/6점'을 덧붙이는 편이 정확하다.
- 수정 제안(같은 줄 안에서)
  - '탐색의 y 끝점 방문 head 0회·base 1회(common_gate y = 1, base 봉인 -- IT-2b가 바꾸지 않는 끝; 9회로·eval_budget 40), 봉인 7 실패 수 9회로 head = base; 큰 예산·경계 최적점의 발생률 미측정'으로 고친다.
  - 측정 근거를 두 파일로 나눈다. 9회로 탐색 = 판정 agent `wt/_scratch_it2b_disp/out/yends.jsonl`, 2회로 6점 재평가 = 오케스트레이터 파일.
  - 두 파일은 `wt/_drafts/evidence/2026-10-22/` 아래로 복사해 그 경로를 인용한다.
- 원칙 적합: 사실 정정만 한다. 새 규칙·상수가 없다. '원래 취지와 다름' 보고(O-103)와 같은 방향이고, 그 크기를 과장하지 않게 한다.

### S-2 L12 (e) (i) '내부 y는 봉인과 독립 여유 ≥ 0 그대로'는 기존 test 단언과 다르다 (검사 4)
- 위치: 41:814 (e).
- 기존 test(근거)
  - `wt/it2b-test` `88335ef6` `tests/sizing/test_input_window.py:325-344` `test_off_mid_window_maps_y_and_ends_saturated`는 y ∈ {0, 0.125, 0.25, 0.5, 0.75, 0.875, 1.0} **모두**에 대해 다음을 단언한다.
    - 봉인 7 pass(`:333`)
    - `min(_oracle_slacks(ev)) >= -1e-12`(`:344`)
  - master `52b9dd81` 판에서도 `:278`·`:288`이 같다. 끝점 test `test_mid_window_ends_have_nonnegative_saturation_slack`(`:347-358`)도 `>= -1e-12`이고, 거기에 `|vin − 정확한 끝| ≤ tol_v`가 더 있다.
- 판정
  - **(i)은 기존 단언을 옮긴 것이 아니다.** 기존 내부 y 기준은 '≥ −1e-12'이고 '≥ 0'이 아니다. '그대로'라고 적으면서 내부 점 기준을 0으로 강화한 셈이다. 0은 발명한 상수는 아니다. 그러나 부동소수점 잡음(1e-13급)이 있는 내부 점에서 test가 이유 없이 빨개질 수 있다. 출처는 판정 agent 권고 `it2b_code_disputes.md` §1 권고 (a)의 문구('내부 y(0 < y < 1)는 봉인과 여유 ≥ 0을 유지')이다. 그 문구가 이미 test를 잘못 옮겼고, design이 그것을 그대로 받았다. O-103 원문에는 이 구절이 없다(O-103은 'test 기대 = 봉인 또는 봉인 7 거부 & |slack| ≤ tol_V'뿐이다).
  - **(ii) '봉인이면 독립 여유 ≥ −1e-12'는 기존 test 단언 그대로이다**(`:344`·`:355`, master `:278`·`:288`). 상수 발명이 아니다. 판정 agent 권고 §1 '어느 쪽이든 … ≥ −1e-12는 유지'와도 같다.
  - 덧붙여, '|slack| ≤ tol_V'의 slack이 무엇인지 적혀 있지 않다. 봉인 7 기록의 여유인지, test 독립 oracle 여유(`_oracle_slacks`)인지가 비어 있다. 영향받는 test가 둘(`…maps_y_and_ends_saturated` y = 0·1, `…ends_have_nonnegative_saturation_slack`)이라는 점도 적혀 있지 않다.
- 수정 제안: (e)를 다음처럼 고친다. "기존 끝점 test 둘(`test_off_mid_window_maps_y_and_ends_saturated`의 y = 0·1, `test_mid_window_ends_have_nonnegative_saturation_slack`)의 기대 = 내부 y는 기존 단언 그대로(봉인 7 pass, 독립 여유 ≥ −1e-12); 끝점 y는 '봉인(이면 기존 단언 그대로) 또는 봉인 7 거부이면서 test 독립 oracle 여유 |slack| ≤ tol_V(`Window.tol_v`)'; 기대 갱신은 test 작성 주체 몫". 이렇게 하면 design이 test 수치를 새로 정하지 않고 기존 단언과 O-103만 인용한다.
- 원칙 적합: 작성자≠검증자 원칙에 맞는다. design은 기준을 새로 강화하거나 약화하지 않고 사용자 결정(O-103)만 옮긴다. 상수 발명이 없다.

### S-3 D (d) '정의 포함 0'의 측정 꼴이 정해져 있지 않아, 지금 code·test가 서로 빨개진다
- 위치: 41:810 (d) '비test 엔진 소스 `git grep` -- 문자열과 상수 이름 모두: `"op_mismatch"`·`status_detail`·`input_window_operating_point_mismatch`'. 계획 1524 (9)(d)도 같은 문언이다.
- 실측
  - `git -C wt/it2b-code grep 85847b49`(tests 제외)에서 `skills/…/sizing/s2_values.py:363`이 걸린다(`Window` docstring `(\`op_mismatch\`·\`status_detail\` 은 EO-1 묶음 몫…)`). `block_columns.py:40` docstring에도 `op_mismatch`가 있다. `sizing/CONTRACT.md:1026`에도 있지만 .py는 아니다.
  - test `88335ef6` `test__helpers_dc_solve.py:94-106` `test_it2b_d_no_operating_point_mismatch_vocabulary_in_engine_sources`는 `.py` 전체 텍스트 검색이다(docstring 포함). 그래서 지금 code에서 빨개진다. code 작성자는 '없다'는 사실을 docstring에 적었을 뿐이고 정의는 0이다.
  - (c)는 'docstring·주석 제외 AST'로 정했다. (d)는 텍스트 검색이라 같은 D 안에서 측정 꼴이 다르다.
- 판정: '정의 포함 0'의 취지(만들면 배선, 죽은 코드 없음)는 정의·참조가 0이라는 뜻이다. 그러나 문언이 텍스트 검색으로 읽히고 test가 그렇게 구현했다. code는 docstring에 언급을 남겼다. 이 어긋남을 design이 정하지 않으면 card 판정이 갈린다.
- 수정 제안(둘 가운데 하나를 design에 명시, 오케스트레이터 결정)
  - (가) **권고**: (c)와 같은 꼴로 정한다. 정적 AST로 문자열 상수(docstring 제외)·식별자(Name·Attribute·arg·keyword·dataclass 필드·대입 대상)에서 세 이름이 0이다. 취지(정의 0)와 정확히 맞고, D 안에서 측정 꼴이 하나가 된다. test는 AST 검사로 고친다.
  - (나) 텍스트 검색(docstring·주석 포함)을 유지한다. 그러면 code가 docstring 언급 둘을 지워야 한다. 더 엄격하지만 '없음' 설명을 소스에 둘 수 없다.
  - 계획 (9)(d) 문언 '`git grep`'과의 관계: (가)도 '정의 포함 0'의 측정법을 좁히는 것이라 계획 위반은 아니다. 다만 design↔계획 gap 분석에서 '계획보다 측정 꼴을 정함'으로 적는다.
- 원칙 적합: fail-closed다(정의가 하나라도 있으면 빨강). 새 상수가 없다. graph와 무관하다.

### S-4 design 40이 같은 판으로 갱신되지 않아 `Window` 칸·상태 어휘가 41과 충돌한다 (검사 8)
- 위치: 40(같은 worktree `9890855f`) `gain-budget-gmid-sizing.40-engine.design.md:550`. 그 줄은 '`node: dc_window` = `Window(lo, hi, constraints, input_status, tol_v, status_detail)`', '`input_status` ∈ {…, `op_mismatch`, …}(어휘·우선순위 정본 = 41 §4.7-2 '값 형식')'이다. 40 머리는 여전히 `version: 1.12.9`이다.
- 판정: 41 v1.12.10 4.7-2(688)는 IT-2 `Window`를 칸 다섯으로 줄이고 `op_mismatch`·`status_detail`을 S-4 갈래 몫으로 옮겼다. 40:550은 칸 목록을 직접 적고 있어 '정본 = 41'이라는 표시로 덮이지 않는다. v1.12.4~v1.12.9는 '40·42 같은 판'으로 함께 고쳤는데 이번 판은 41만 고쳤다.
- 수정 제안: 40:550의 `Window` 칸 목록과 어휘에 '(S-4 갈래 몫: `op_mismatch`·`status_detail` -- 41 4.7-2)' 표시를 하거나 둘을 뺀다. 40 머리를 1.12.10 / 6.33으로 올린다. 줄 추가 없이 된다.
- 원칙 적합: 같은 정의의 양을 한 자리에만 두는 규칙 3의 문서판이다. 정의를 두 문서에 다르게 두지 않는다.

### S-5 IT-2c `icm_config`의 `Circuit` 접근은 '미정'이 아니라 지금 설계대로는 막혀 있다 (검사 6)
- 위치: 41:760 '미정(IT-2c 착수 전 확인)', 41:734 (2)·(4)(변경 없음 -- '`_helpers_dc_solve.Circuit`의 θ 고정 선형 연립', '`region_rows`로 행을 세우고 `saturation_window`를 부른다').
- 근거
  - 순서는 계획 v6.33에서 IT-2b → IT-2c → IT-2d로 고정되어 있다(41:834). v1.12.10은 helper 이동을 IT-2d로 미뤘다(760). 그래서 IT-2c 시점에 `_helpers_dc_solve.py`는 **없다**. 734가 가리키는 모듈이 IT-2c에 존재하지 않는다.
  - `icm_config`는 `E/metrics/icm_config.py`(metrics, 층 5)에 있다. 규칙 C(`tests/structure/README.md` 규칙 표 C (3))에 따라 다른 하위 패키지 import는 `from gmid_engine.sizing import <이름>`이고, 이름은 `sizing/__init__.__all__` 안에 있어야 한다. 파일 직접 import(`from gmid_engine.sizing.block_columns import …`)는 금지이다.
  - 규칙 B는 다른 파일의 `_` 이름 import를 막는다. 그래서 `sizing/__init__`이 `block_columns._Circuit`을 재수출할 수도 없다.
  - 규칙 A 보충 (3)(`structure_checks.py:320-359`)은 같은 하위 패키지(`sizing`) 안 사용자만 센다. 공개 **함수**만 세고 클래스는 세지 않는다.
  - 결론: v1.12.10 대로라면 IT-2c는 `region_rows`(행의 단일 생산자)와 θ 고정 연립을 부를 합법 경로가 없다. 734의 행 셋을 `icm_config` 안에서 다시 만들면 둘째 생산자가 된다(규칙 1).
- 판정: '막히면 멈추고 보고'라는 처리는 fail-closed이긴 하다. 그러나 막힌다는 것이 이미 확정된 사실이다. 그래서 '미정'으로 두면 IT-2c card를 동결할 수 없고, design 개정 한 바퀴가 예정된 채로 남는다. 734 문언도 IT-2c 시점에 없는 모듈을 가리켜 v1.12.10 안에서 모순이다. 최소한 734에 '이동 시점 = 760' 표시가 필요하고, 가능하면 지금 정한다.
- 오케스트레이터가 정할 선택지와 원칙 점검

| 안 | 내용 | 규칙 A·B·C | graph 정본 | 만들면 배선 | 필요한 개정 | 평가 |
|---|---|---|---|---|---|---|
| (가) | IT-2c가 **`Circuit` 클래스만** `_helpers_dc_solve.py`로 옮기고 `sizing.__all__`에 `Circuit`을 올린다. `solve`·`FAILURES`·`window_refine`의 import는 IT-2d | A: 실사용자 둘(`block_columns`·`icm_config`)이 실제로 생기는 변경이라 취지를 충족한다(검사기는 클래스를 세지 않으므로 이것은 근거 판정이지 빈틈 이용이 아니다 -- IT-2b의 (가)를 기각한 사유인 '사용자 하나'가 IT-2c에는 없다). B·C 충족 | 행·연립 생산자 = `Circuit` 하나 그대로 | `Circuit` 공개와 둘째 사용자가 같은 변경 | 760 '옮기는 범위' 문언을 두 시점(IT-2c `Circuit`, IT-2d `solve`·`FAILURES`)으로 나눔. 734·807·837 경로 표시. `sizing.__all__`에 `Circuit`을 넣는 공개 API 결정 | **기본안 권고**. 단 `Circuit`이 sizing 공개 API가 되는 것은 design 결정으로 명시해야 한다 |
| (나) | `icm_config`가 `Circuit`을 쓰지 않는다. follower 행은 `graph.ss_nodal`(봉인점 컨덕턴스 계)로 풀고, 행 셋만 sizing 공개 함수 하나로 받는다 | 새 공개 진입점 하나(규칙 A 개념 1). B·C 충족 | 계획 1514는 '봉인점 컨덕턴스 계(DC 야코비안)로 반전 입력 식별·follower 행·영역 경계 행을 함께 푼다'고 적는다. 그래서 734 (2) 'Circuit θ 고정 연립'과 계획 문언이 같은 행렬인지가 **미확인**이다. 같지 않다면 (나)가 계획에 더 가깝다 | 새 진입점 소비자 = `icm_config` | 734 (2)(4) 재작성, 계획과 대조 필요 | 계획 정합 확인이 먼저다. 확인 결과에 따라 (가)보다 맞을 수 있다 |
| (다) | IT-2c를 IT-2d 뒤로 | -- | -- | -- | 계획 v6.33 순서 개정 + 사용자 결정 | 순서 고정(O-101 승인)을 깬다. 권하지 않는다 |
| (라) | `icm_config`가 `block_columns._Circuit`을 직접 import | B·C 위반 | -- | -- | -- | 금지 |
| (마) | 감도 연립·행을 `dc_columns`가 graph 필드로 쓰고 `icm_config`가 READS | 위반 없음 | 규칙 4(단계 사이 전달 = graph 필드)에 맞다. 그러나 정본 자리가 계획에 없으므로 규칙 6에 따라 계획부터 고쳐야 한다. θ마다 행렬 필드를 두는 비용이 든다 | 소비자 = `icm_config` | 계획 개정 | 지금 고르기에는 범위가 크다 |

  - 권고: IT-2b card 재동결 전에 (가)와 (나) 가운데 하나를 design에서 정한다. (나)의 전제(계획 1514 '봉인점 컨덕턴스 계'와 734 (2) 연립의 동일성)를 먼저 확인하고, 다르면 계획 문언과의 gap부터 정리한다(S-7 계획 먼저). 같다면 (가)가 최소 변경이다. 지금처럼 '미정'으로 둔다면 760에 'IT-2c 착수 조건: 접근 경로 결정(선택지 (가)·(나))'를 적고, 734에 '경로 = 760 이동 시점'을 표시한다.
- 원칙 적합: 위 표의 원칙 점검과 같다. 어느 안도 새 cache·사본을 만들지 않는다. (라)는 금지이다.

---

## N -- 권장 (정확도·가독성)

| # | 위치 | 내용 | 수정 제안 | 원칙 |
|---|---|---|---|---|
| N-1 | 697 '(as-built `Circuit.writer_head`)', 705 '`_helpers_dc_solve.Circuit.saturation_rows`', 807 | v1.12.10의 IT-2b 배치(helper 미이동)에서는 `block_columns._Circuit.writer_head`이다. 705·807은 괄호로 이동 전 이름을 적었지만 697은 적지 않았다. **부수 사실**: `85847b49`는 이미 helper를 옮겼다(`_helpers_dc_solve.py:103 class Circuit`, `:191 writer_head`, `block_columns.py:50` import). test `88335ef6` `test__helpers_dc_solve.py:109-` `test_it2b_d_helper_module_public_names_replace_block_columns_privates`도 이동을 단언한다. 둘 다 v1.12.10 4.7-4 '이동 시점'과 다르므로 code 되돌림과 test 재배치가 필요하다(판정 agent 권고 2 (나)와 같다) | 697에 '(IT-2d 이동 전 `block_columns._Circuit.writer_head`)'를 더한다. 오케스트레이터가 code·test 재작업을 card에 적는다 | 만들면 배선(사용자 하나인 helper 금지) |
| N-2 | 694 'A6 b 도달 조건' | (1) '모든 **전도** MOS'라고 적었지만 code `region_rows`(`_helpers_dc_solve.py:199-220`)·`_tolerance`(`block_columns.py:129-136`)는 `device.dc_coord`의 MOS 전부를 돈다(전도 거르기 없음). (2) '슬라이스에 VDSAT 열이 있으면 두 tol은 함께 정의되거나 함께 미정'은 반대 방향 예외가 있다. 앵커 2개 bin에서 중점 파일에 VDSAT 열이 없거나 격자가 다르면(`midpoint_checks.py:70-73` `_vdsat` → None) tol_V는 정의되고 tol_VDsat는 미정이다(A6 a 쪽). A6 b 방향(tol_VDsat 정의·tol_V 미정)에 대해서는 같은 슬라이스 안에서 갈리는 길이 코드 읽기로 보이지 않는다(점 조건 `ok = on[:-2] & on[1:-1] & on[2:]`가 같다, `tolerance.py:84-85`·`vdsat_tolerance.py` 머리) | '모든 MOS(`device.dc_coord`)'로 고친다. '함께'를 'A6 b 방향으로는 갈리지 않는다'로 한 방향만 적는다 | 사실 정확도 |
| N-3 | 760 '메서드 `saturation_rows`·`input_windows`…', 837 'HC-S가 고칠 `…Circuit.saturation_rows`' | 705가 `saturation_rows`를 `region_rows`로 넓혔다(as-built `85847b49`도 `region_rows`). 760·837의 메서드 이름이 낡았다 | `region_rows`(옛 `saturation_rows`)로 고친다 | 이름 정본 하나 |
| N-4 | 817 (8) | IT-2b가 θ → V 사상 자체를 바꾼다는 사실이 동작 변경 목록에 명시되어 있지 않다. 판정 agent 실측: common_gate src 4 vin hi가 head 1.6957364591335347, base 1.6957364591379647이다. 그래서 뿌리 lo·hi와 `fd_jacobian` y 스텝이 비트 동일이 아니고, 탐색 궤적도 바뀐다(호출 34 대 43). '끝점 거부'만 적혀 있다 | (8)에 '뿌리 `lo`·`hi`(다듬지 않은 끝)와 그것을 읽는 θ y 사상·`fd_jacobian` y 스텝 값이 바뀜(비트 동일 아님) -- card '무동작 판정 입력'에서 뺌'을 덧붙인다 | 동작 변경 정직 기록(O-34) |
| N-5 | 814 (e) '|slack| ≤ tol_V' | 이 상한의 근거(A6 수렴 판정 tol이 뿌리 전압 차라서 slack 오차 ≈ 행 기울기 × δx)가 적혀 있지 않다. 행 기울기가 1보다 크면 tol_V보다 클 수 있다. 사용자 결정 O-103의 값이라 발명은 아니다 | 출처 'O-103'만 명시하고 유도는 백로그 B70 쪽으로 넘긴다 | 상수 발명 아님(사용자 결정 인용) |
| N-6 | 17(머리) | 머리 bullet이 v1.12.10 변경 (1)~(7)로 더 길어졌다. 줄 수 유지 방침에 따른 알려진 가독성 부채이다(v1.12.9 재검증 N-Q2와 같다) | 방침 유지. history H로 옮길 때 정리한다 | 계획서/이력 분리 |
| N-7 | 같은 worktree의 card (`specs/20261021-it2-common.md:73·117·237·259·289`, `it2b-kernel-window.interface.md:9·20·33`, `.spec.md:21·25·35`, `it2d-refine-front.interface.md:52`) | `status_detail`·`op_mismatch`·`_refine_ends` 삭제 시점·helper 이동 시점이 v1.12.10 이전 문언이다. test `88335ef6` `test_block_columns.py:1048 w.status_detail == ()`도 O-98과 어긋난다(이 칸은 없으므로 AttributeError가 난다) | card 재동결 때 고친다(design 범위 밖, 오케스트레이터 몫). test 결함은 test 작성 주체에게 넘긴다 | 만들면 배선, 작성자≠검증자 |

---

## 검사 2 -- 인용한 엔진 줄·이름 재측정 (`85847b49`)

| 인용 | design 위치 | 실측 | 판정 |
|---|---|---|---|
| `Circuit.writer_head` | 697 | `sizing/_helpers_dc_solve.py:191-197`. `FIXED_RELATIONS` 또는 `REL_WINDOW`까지 `known`을 거슬러 올라간다. 호출처는 `block_columns.py:270`(`_windows`)이고 `:271` `relation in FIXED_RELATIONS`이면 `f_component_undeclared`이다. 선언 포트(`REL_INPUT_DC`)는 `:268`에서 건너뛴다 | 맞음. IT-2b 배치에서는 `_Circuit`이다(N-1) |
| `FIXED_RELATIONS` (`E/sizing/scc_order.py`) | 697 | `scc_order.py:37` `(REL_RAIL, REL_TARGET, REL_INPUT_DC)` | 맞음 |
| `from .k_max import k_max` (`block_columns.py:52`) | 762·814 | `block_columns.py:52` 맞음. 같은 파일 `_interior_solution` `:145`·`_solve_input_window` `:235`·`_refine_ends` `:179`가 읽는다. `85847b49`에서는 자기참조 bisection이 `_helpers_dc_solve.py:23`의 자기 import를 쓴다. v1.12.10 IT-2b 배치(이동 전)에서는 master처럼 `block_columns`의 `k_max`를 읽는다(master `:406`). 그래서 814의 'IT-2d 이동 전에는 `SccLog.k_max`도 같은 이름' 단서는 설계 배치 기준으로 맞다 | 맞음 |
| `_root_windows` 호출자 = `_refine_ends` 하나 | 761 | `block_columns.py:161` 정의, 호출 `:188`(`_refine_ends` 안) 하나 | 맞음 |
| `_refine_ends` 호출처 | 761 | `:172` 정의뿐이다. 엔진 호출 0(죽은 코드). IT-2b 삭제가 맞다 | 맞음 |
| `column_source` | 694 | `lut/_helpers_columns.py:13-35`. 슬라이스 열 → 같은 폭 키 기준 LUT(`cap.w_key == w_key`) → `lut_column_unavailable`. 사용처: `vdsat_query.py:26`, `vdsat_tolerance.py:106`, `midpoint_checks.py:70`, `gmb.py:35·50` | 맞음 |
| tol_V는 늘 `slice_map` | 694 | `lut/tolerance.py:257` `sl = memo.lut.slice_map[(kind, w_key)]`. 열 출처 분기가 없다 | 맞음 |
| `vdsat_query.py` | 694 | `:5` 'LUT v2에서는 기준 LUT에만 있다', `:26` `column_source(…, "VDSAT")` | 맞음('LUT v2 운영 꼴' 표현의 근거) |
| `Circuit.tolerance` '하나라도 정의되면 최솟값', `tol_v_undefined`는 전부 미정일 때 | 694 | `_helpers_dc_solve.py:511-524` | 맞음 |
| `Window` 칸 다섯 | 688 | `s2_values.py:360-369` `(lo, hi, constraints, input_status=None, tol_v=None)` | 맞음 |
| `INPUT_STATUS_*` 넷 | 688 | `s2_values.py:116-119`(`OUTPUT_*` `:114-115` 옆) | 맞음 |

---

## 검사 3 -- A6 b '조건부 도달 가능' 판정

- **코드 경로는 실제로 갈린다.**
  - 행 셋은 `region_rows`(`_helpers_dc_solve.py:199-220`)에서 만든다. `vdsat()`(`vdsat_query.py:26`)와 `tol_vdsat_table`(`vdsat_tolerance.py:106`)이 모두 `column_source`를 거친다. 슬라이스에 VDSAT 열이 없으면 같은 폭 키의 `CapTable`에서 축·bin·on_mask·값을 읽는다.
  - 되풀이 판정 tol은 `_tolerance` → `Circuit.tolerance` → `tol_v_cell` → `tol_v_table`이고, 늘 슬라이스(`slice_map`)에서 읽는다.
  - 그래서 '기준 LUT VDSAT 셀 정의 + 슬라이스 id_equivalent 셀 미정'이면 `_solve_input_window`가 `tol is None` 갈래(`block_columns.py:229-233`)로 가서 `"unsettled"`를 낸다. 다만 y = 1/2 풀이가 성공해야 하고, 순환 SCC·자기참조 노드가 없어야 한다(있으면 `tolerance`가 풀이 안에서 예외를 낸다). design 694의 조건과 같다.
- **픽스처를 만들 수 있는가: 원리상 가능하지만 새 픽스처가 필요하다(실행 미확인).**
  - `tests/lut/conftest.py:46·1328`에 '결정 B 이전 v2 슬라이스(GMBS·VDSAT 없음) + v2 기준 LUT' 픽스처가 있고, `test_vdsat_tolerance.py:63-66·355-359`가 `origin == "cap_table"`를 확인한다. 열 출처 갈래 자체는 test 도구로 이미 만들 수 있다.
  - 다만 그 픽스처의 슬라이스는 L 18·VS 10으로 내부점이 있어 tol_V가 정의된다. A6 b에는 다음 조합이 필요하다.
    - 슬라이스: VGS·VDS·VS 2점 격자(내부점 없음 -- `test_block_columns.py:881`의 `tol_v_undefined` 최소 구성과 같은 꼴), 중점 파일 없음.
    - 기준 LUT: 같은 `w_key`, VDSAT 열과 내부점이 있음.
  - 이 조합은 `tests/lut/conftest.py`의 fixture가 `tests/sizing`에 보이지 않으므로 sizing conftest에 새로 만들어야 한다. 2점 슬라이스에서 비순환 toy가 풀리는지는 미확인이다.
  - design의 '만들 수 없으면 test 작성 주체가 멈추고 보고'는 적절하다.
- **test 작성자 측정과 모순되는가: 아니다.**
  - 작성자 측정('모든 구성에서 함께 None 또는 함께 정의')은 VDSAT 열이 슬라이스에 있는 sizing 픽스처(r4·toy LUT) 구성에 대한 것으로 읽힌다. cap_table 출처 구성은 sizing 픽스처에 없다.
  - 같은 슬라이스 안에서는 A6 b 방향으로 갈리지 않는다는 코드 읽기와도 맞는다(N-2 (2)).
  - 작성자 측정이 cap_table 출처 구성을 포함했는지는 **미확인**이다(측정 기록을 찾지 못했다).

---

## 검사 7 -- 원칙

| 원칙 | 판정 | 근거 |
|---|---|---|
| graph 단일 정본 | 적합 | 새 필드·cache·사본 없음. `Window` 칸을 줄였다. 불일치 판정은 공용 함수 하나만 쓰고 행 여유 판정을 금지했다(712). 커널 끝을 다시 푸는 안을 둘째 생산자로 기각했다(817). S-5 선택지 중 (라)·행 셋 재구성만 위반이다 |
| 만들면 배선 | 적합 | (S4-나) 정의 0(688·708·810 (d)), `_refine_ends`·`_root_windows` IT-2b 삭제(761), 사용자 하나인 helper 금지(760). 남은 것: code `85847b49`가 이미 helper를 옮겼다(N-1) |
| fail-closed | 적합 | A6 b·c → `"unsettled"`, 끝점 봉인 7 거부 유지(기준 완화 없음 -- B70 백로그). (S4-나) 기간의 미차단은 O-100으로 승인되었고 '원래 취지와 다름(작음)'이 표시되어 있다 |
| 상수 발명 없음 | 대체로 적합 | 1e-12는 기존 test 상수이다(S-2 (ii)). '약 1e-12 V'는 측정 서술이다. tol_V 상한은 O-103 값이다. S-2 (i) '≥ 0'은 발명은 아니지만 기존 단언과 다른 기준이다 |
| 회로 이름 없음 | 적합 | 회로 이름은 design의 측정 서술과 승인 분류표 대조 범위(721·724·817)에만 있다. 엔진 규칙은 일반형('쓰기 계획이 정지하는 회로')이다 |
| as-built 결정 없음 | 적합(표시됨) | `INPUT_STATUS_*` 이름과 writer 사슬 끝 판정은 as-built를 문서에 반영한 것이라고 명시했다. 동작·규칙 변경이 아님을 표시했다(688·697). 판정 agent 부수 확인 1과 같다 |
| 줄 수 유지 | 적합 | numstat 34/34, 총 1992줄 동일 |

## 검사 8 -- IT-2a·B69(v1.12.9) 문장과의 충돌

- 41 안: 충돌을 찾지 못했다.
  - 4.7-3c(753·756)와 L11 (d)(e)(813)는 바뀌지 않았다.
  - L12 (a)의 'tol 미정 toy는 실패 예외 `partial`로 읽지 않고 `run_blocks(upto="columns")`'(814)는 B69 규칙(실패 블록 필드는 부분 스냅샷에서 빠짐)과 맞는다.
  - R2 괄호(804)는 L11 (e) 주입 범위를 그대로 두고 L12 (a)만 더했다.
  - 4.7-9 판정 단위(834)는 IT-2e를 유지한다.
- 41 밖: design 40:550이 v1.12.9 상태로 남아 41 v1.12.10과 충돌한다(S-4).

## 미확인

- A6 b 픽스처(2점 슬라이스 + 같은 폭 키 기준 LUT VDSAT)에서 비순환 toy가 실제로 풀리고 `"unsettled"`가 나오는지(엔진 실행 안 함).
- test 작성자의 '함께 None/함께 정의' 측정이 cap_table 출처 구성을 포함했는지(기록 미발견).
- 계획 1514 '봉인점 컨덕턴스 계(DC 야코비안)'와 design 734 (2) '`Circuit` θ 고정 선형 연립'이 같은 행렬인지(S-5 (나)의 전제).
- `device.dc_coord`에 꺼진 MOS가 들어가는지(N-2 (1)의 실제 영향).
- 탐색 예산이 크거나 경계 최적점인 회로에서 y 끝 거부 발생률(판정 agent와 같은 미확인).

## 작업 기록(가드)

- git은 `git -C`로 show·diff·grep·log만 썼다. reset·checkout·stash·push는 하지 않았다.
- 저장소 파일은 고치지 않았다.
- 결과 파일 밖에 쓴 것: 대조용 임시 파일을 세션 scratchpad에 만들었다(diff 추출, 옛판·새판 41 사본, 단어 diff 스크립트·출력, master `block_columns.py` 사본). `/tmp/bc_master.py`에도 시도했다. 이 파일들은 보고 뒤 지웠다(아래 보고 참조).
