# IT-2b code 작성자 미결 세 가지 판정 (2026-10-22, 읽기 전용 판정 agent)

- 대상: worktree `wt/it2b-code` 커밋 `85847b49`(구현)·`34a2a249`(dispute), base 비교 = `53d50aea`(IT-2b test 병합, 엔진은 IT-2b 전).
- 기준 문서: design 41 v1.12.9(master `52b9dd81`) 4.7-3 1~5(693-702), 4.7-4(759-762), 4.7-1a(718-727), 633·680·817; card `wt/integ-it12/docs/02-design/specs/20261021-it2b-kernel-window.spec.md`; 계획 v6.33 N6.6 범위 1(plan.md:1514)·완료 조건 (0)(:1524).
- 엔진 실행: `wt/_scratch_it2b_disp/`(clone `--no-local --no-checkout`, remote 제거, `git archive`로 head·base 두 벌 풀기, APPDATA export, 순차 실행). 스크립트 `scripts/yends.py`·`scripts/stopreason.py`, 결과 `out/yends.jsonl`·`out/stop/*.json`. 관찰 래퍼는 `search.kernel.size_and_seal`을 감싸 반환값과 예외를 바꾸지 않는다.
- 판정 원칙: 물리를 먼저 보고 가장 일반적인 형태로 판단한다. graph 단일 정본을 지킨다. fail-closed로 판단한다. 상수를 발명하지 않는다. design에 있는 결정은 그대로 따르고, design에 없는 것은 '결정 필요'로 올린다.

---

## 1. y = 0 끝에서 봉인 7이 거부함

### 판정
**의도된 동작이다(design 4.7-3 1의 직접 결과이고 구현 결함이 아니다).** 그래서 기존 test 기대를 바꾸는 것은 약화가 아니라 승인된 결정(O-33 (3))이 낳은 **정당한 동작 변경**이다. 다만 이 결과가 design 4.7-8 변화표와 card '무동작 판정 입력'에 적혀 있지 않다. 이것은 **design·card 문언 결함**이다. J-E의 원래 약속('y ∈ [0, 1]이 모두 봉인된다')이 깨지므로 **'원래 취지와 다름'으로 보고할 대상**이다.

### 근거
1. **design이 커널 끝을 선형 추정으로 정했다.**
   - 41:694는 "`_refine_ends`는 커널에서 부르지 않는다. 마지막 풀이의 `override` = 마지막으로 잰 선형 창"이라고 적는다.
   - 41:633은 "경계의 층별 정밀도(O-33 (3)): 평가 커널에서는 그 해에서 잰 선형 감도 끝(손계산, '추정' 표기)이고, 끝 풀이로 다듬은 **봉인 시점 값은 수락 반복·front에서만** 낸다"고 적는다.
   - 41:691은 커널 창을 손계산 '추정'으로 적는다.
   - 계획 plan.md:1524 완료 조건 (0)은 "커널 평가 중 `_refine_ends` 호출 0(G-10 계수)"이다.
   - 즉 '봉인 시점 값'(다듬은 끝)을 커널 y 범위로 쓰지 않는다는 것이 사용자가 승인한 결정이다.
2. **A6 수렴 조건과 tol 정의에서도 같은 결론이 나온다.**
   - 되풀이는 연속한 두 창 끝의 차가 tol 이하이면 멈춘다(`block_columns.py:236-243`, `abs(a − b) <= tol`, 대칭 조건).
   - tol = 그 해의 소자 tol_V 셀 최솟값이다(41:702 `tol_v`, '판정 분해능').
   - 그래서 수렴한 끝도 정확한 경계에서 **분해능(tol_V) 안의 오차**를 갖는다. 오차의 부호는 정해지지 않는다(선형 외삽의 2차 오차는 곡률 방향을 따른다).
   - 봉인 7은 `slack = VDS − VDsat − tol_VDsat ≥ 0`을 엄격히 판정한다(`seal_saturation.py:9-13`, margin > 1 ⇔ slack < 0이면 위반). 따라서 끝이 경계를 분해능보다 작게 넘어도 거부된다.
   - 측정된 크기는 −1.79e-6 V(toy), −6.55e-6 V, −5e-13~−8e-12 V이다. 모두 tol_V(예: common_gate 7.7e-3 V, IT-0 trace)보다 3~9자릿수 작다. 물리적으로 판별할 수 없는 차이이다.
   - 이런 점을 거부하는 것은 **fail-closed와 일치한다**(좋은 점을 잃을 수는 있어도 나쁜 점을 받지 않는다).
3. **design은 'y 끝 봉인 보장'을 말하지 않는다.**
   - 41:633의 "경계는 tol을 포함한다"는 창 정의에 +tol_VDsat 판정 여유가 들어 있다는 뜻이다. 끝점 봉인을 보장한다는 문언은 없다(design 전체 grep: `y = 0`·`y 끝`·`모든 y` 0건).
   - test가 요구하는 "y = 0·1 포함 독립 여유 ≥ −1e-12"는 옛 A6 (5)(`_refine_ends`, 41:660)의 성질에 기댄 기대이다.
4. **옛 경로도 끝 봉인을 보장하지 않았다(실측).**
   - base(`_refine_ends` 있음)에서도 common_gate_amplifier y = 1은 6점 중 5점이 봉인 7로 거부된다(slack −7.95e-12).
   - 옛 '모든 y 봉인' 기대는 toy에서만 성립했다.

### 실측: 9회로 (`out/yends.jsonl`, eval_budget 40, head = 85847b49, base = 53d50aea)

| 회로 | 입력 뿌리 y | 탐색 중 y = 0/1 도달(head·base) | 탐색 봉인 7 실패 수(head = base) | 탐색점 기준 y 끝 강제 재평가(봉인 점 ≤ 6개): y = 0 head / base | y = 1 head / base |
|---|---|---|---|---|---|
| common_gate_amplifier | 있음 | 0 · 1(y = 1, 거부 아님) | 0 = 0 | **0/6 / 6/6**(slack −4.8e-13~−3.6e-12) | 1/6 / 1/6(같음, −7.95e-12) |
| current_reuse_telescopic_ota | 있음 | 0 · 0 | 40 = 40(끝 아님) | 봉인 점 없음(측정 불가) | 같음 |
| folded_cascode | 있음 | 0 · 0 | 0 = 0 | 6/6 / 6/6 | 6/6 / 6/6 |
| ngcc_3stage_ff | 있음 | 0 · 0 | 0 = 0 | 6/6 / 6/6 | 6/6 / 6/6 |
| nmcnr_amplifier | 있음 | 0 · 0 | 5 = 5(끝 아님) | 6/6 / 6/6 | 6/6 / 6/6 |
| pushpull_follower_buffer | 없음(입력 DC 선언) | -- | 0 = 0 | 해당 없음 | 해당 없음 |
| sf_pushpull_output_opamp | 없음(입력 DC 선언) | -- | 33 = 33(끝 아님) | 해당 없음 | 해당 없음 |
| two_stage_ota | 있음 | 0 · 0 | 0 = 0 | 6/6 / 6/6 | 6/6 / 6/6 |
| two_stage_ota_sf | 있음 | 0 · 0 | 0 = 0 | **0/6 / 6/6**(slack −6.55e-6) | 6/6 / 6/6 |

- **탐색 영향**: 이 예산(40)에서는 head의 탐색이 y 끝점에 한 번도 가지 않았다. 봉인 7 실패 수는 head와 base가 9회로 모두 같다. 거부율 변화는 0이다.
- **끝점을 강제로 재평가했을 때**: 2회로(common_gate y = 0, two_stage_ota_sf y = 0)에서 head만 거부한다. slack은 모두 분해능보다 훨씬 작다.
- SLSQP는 상자 [0, 1]의 경계에 닿을 수 있다(`search_domain.py:124`, `slsqp_outer.py:101-107` clip). 그래서 예산이 크거나 최적점이 경계에 있으면 이 거부가 탐색에서 나타날 수 있다. 이 경우의 발생률은 **미확인**이다.
- **부수 사실 -- card '무동작 판정 입력' 문언이 틀렸다.**
  - card는 "θ 프레임 W4 y 범위(`node.dc_window` 뿌리 lo·hi)와 `fd_jacobian` y 스텝 값은 9회로 비트 동일"이라고 적는다.
  - 실측: common_gate 같은 θ(src 4)의 vin 창 hi가 head 1.6957364591335347, base 1.6957364591379647로 다르다(다듬기 제거 때문). 비트 동일이 아니다.
  - 식('순서 창 ∩ override')은 같지만 override 값이 바뀐다. 이것도 4.7-8 변화표에 없는 동작 변경이다.

### 권고 (하나)
- **구현은 그대로 둔다(design대로).**
- design 4.7-8 변화표에 다음 한 항목을 더한다: "(8) 커널 W4 입력 뿌리 y 범위 끝이 다듬은 끝에서 선형 감도 끝으로 바뀐다. 끝점(y = 0·1)은 분해능 이하 오차로 봉인 7 거부가 날 수 있다(fail-closed, O-33 (3)의 결과)."
- card '무동작 판정 입력'에서 '뿌리 lo·hi 비트 동일'을 빼고 동작 변경 칸으로 옮긴다.
- test 작성 주체는 `test_off_mid_window_maps_y_and_ends_saturated`의 끝점 기대를 다음 둘 가운데 하나로 바꾼다. 어느 쪽이든 '봉인이면 독립 여유 ≥ −1e-12'는 유지한다.
  - (a) 내부 y(0 < y < 1)는 봉인과 여유 ≥ 0을 유지하고, 끝 y는 '봉인이거나 봉인 7 거부이며 그때 |slack| ≤ tol_V'로 바꾼다.
  - (b) 끝 y 단언을 IT-2d 다듬은 창 test로 옮긴다.
- 이 기대 변경은 **사용자에게 '원래 취지와 다름'(J-E '모든 y 봉인' → '끝은 분해능 안에서 거부될 수 있음')으로 보고하고 확인을 받는다.** 승인된 결정(O-33 (3))의 결과이므로 새 결정은 아니고, 결과를 알리는 확인이다.

### 원칙 점검
- 물리: 차이가 분해능 아래라서 물리적으로 구별할 수 없다. 끝을 안쪽으로 당기는 보정은 물리 근거가 없다(tol_VDsat가 이미 판정 여유이므로 이중 계산이 된다). → 채택하지 않는다.
- fail-closed: 봉인 7에 반올림 허용치를 더하는 것은 기준 약화이다. → 하지 않는다. 지금 동작이 fail-closed이다.
- 상수 발명: 끝을 ε만큼 안으로 당기거나 y 상자를 [ε, 1 − ε]로 두는 안은 새 상수이다. → 금지한다.
- graph 단일 정본: 커널에서 끝을 다시 풀면 다듬은 창(`dc_window_def_refined`, IT-2d)과 같은 값을 두 번째로 만드는 생산자가 된다. → 금지한다. 권고안은 새 필드·캐시가 없다.
- design 준수: 41:633·694를 그대로 따른다. 개정은 4.7-8 변화표와 card 문언(기록)뿐이다.

| 표시 | 값 |
|---|---|
| design 개정 | 필요(4.7-8 변화표 한 항목, 문언 -- 규칙 변경 아님) |
| card 개정 | 필요('무동작 판정 입력' 정정, test 작성 주체 몫에 끝점 기대 갱신 추가) |
| 계획 개정 | 불필요 |
| 사용자 결정 | 확인 필요(원래 취지와 다름 보고, 새 결정 아님) |
| 원래 취지와 다름 | **해당**(J-E 모든 y 봉인 약속) |

---

## 2. 구조 규칙 A 위반 (`_helpers_dc_solve.solve` 사용 파일 1개)

### 규칙 A의 정의·목적·예외
- 정의: `tests/structure/README.md:39` 규칙 A 보충 (3)은 "비공개 모듈(`_`로 시작하는 파일) = 공유 helper: 공개 함수마다 같은 하위 패키지의 **다른 파일 2개 이상**이 import해야 한다"고 적는다. 검사기 `structure_checks.py:344-359`(`HELPER_MIN_USERS = 2`)는 "하나면 그 파일로 옮김"이라는 메시지를 낸다. 공개 **함수**만 세고 클래스·상수는 세지 않는다(README:146-150).
- 목적: 사용자 규칙의 취지인 '한 파일에 너무 많은 함수'와 '공용 helper는 실제로 공유될 때만'이다. 한 곳만 쓰는 코드는 그 파일에 둔다.
- 예외: 규칙 A 예외는 `__init__.py`·`tests/`·레지스트리 데코레이터뿐이다. **중간 상태·기한부 예외는 없다.**
- design 41:760은 helper를 둘 근거를 "`Circuit`·`solve`는 `block_columns.py`·`window_refine.py` 둘이 쓴다"로 든다. 즉 **둘째 사용자가 있는 시점이 helper가 성립하는 조건**이다. IT-2b에는 둘째 사용자가 없다.
- 실측: head에서 `_helpers_dc_solve`를 import하는 엔진 파일은 `block_columns.py:50` 하나뿐이다. `_module_map`·CONTRACT·test는 사용자로 세지 않는다.

### 선택지 비교

| 안 | 내용 | 규칙 A | design 4.7-4와의 관계 | 필요한 개정 | 평가 |
|---|---|---|---|---|---|
| (가) | IT-2b는 `Circuit`·`FAILURES`만 옮기고 `solve`(+`_strict_recheck`)는 IT-2d까지 `block_columns`에 둔다 | 글자로는 통과한다(공개 함수 0). 그러나 `Circuit`도 IT-2b에서는 사용자가 하나뿐이다. 검사기가 클래스를 세지 않는 빈틈으로 통과하는 것이다 | 4.7-4 이동 범위(`Circuit`·`solve`·`FAILURES` 함께)와 다르다. 41:760 "옮기는 범위(`Circuit`·`solve`·`FAILURES`)"를 IT-2b에서 나누어 지킨다 | card 신규 시그니처 표 정정, test `test_it2b_d_helper_module_public_names_replace_block_columns_privates`(helper에 `solve`, block_columns에 `_solve` 없음 단언) 기대 변경 | 규칙 취지 위반(빈틈 이용). 권하지 않는다 |
| (나) | helper 이동 전체를 IT-2d(둘째 사용자 `window_refine`이 들어오는 변경)로 옮긴다. IT-2b는 `block_columns._Circuit`에 `region_rows`를 더하고 `_solve`·`_FAILURES`를 그대로 둔다 | 위반 0. 이동과 둘째 사용자가 같은 변경에 든다 | 4.7-4 문언과 맞는다(근거 '둘이 쓴다'가 처음 성립하는 시점). design 개정 불요 | card IT-2b 범위에서 '4.7-4 공유하는 것'과 시그니처 표의 `_helpers_dc_solve` 행을 빼서 IT-2d로 옮긴다(공통 문서 33·35행 표도 함께). test 작성 주체: `test__helpers_dc_solve.py`의 IT-2b 단언(D triode 행, S4-나 AST 검사는 대상 파일 경로 변경)을 `test_block_columns.py`로 옮기고, public-names test는 IT-2d로 옮긴다. 이 파일이 IT-2b에 남으면 규칙 H 고아가 된다. code: 이동을 되돌린다 | **권고** |
| (다) | 통합 브랜치 중간 상태로 허용한다(master 병합은 IT-2d 뒤 한 번, O-19 (2)) | IT-2b 판정에서 빨강이 남는다 | 무관 | 구조 test 예외 = 기준 약화이므로 사용자 승인이 필요하다 | 약화이고, IT-2d가 늦어지면 빨강이 남는다. 권하지 않는다 |
| (라-1) | IT-2d의 `window_refine.py` 골격을 당겨와 `solve`를 import한다 | 통과 | 범위 밖 card 일을 당겨온다(card 공통 멈춤 조건) | -- | 죽은 배선(만들면 배선 원칙 위반). 금지한다 |
| (라-2) | `solve`를 `Circuit.solve` 메서드로 바꿔 검사를 피한다 | 통과(빈틈) | 4.7-4 공개 이름 `solve`와 다르다 | design 개정 | 검사 회피. 금지한다 |

### 권고 (하나): (나)
- 규칙 A의 '하나면 그 파일로'와 design 41:760의 근거('둘이 쓴다')가 같은 결론을 낸다. helper는 둘째 사용자와 같은 변경에서 생긴다.
- design 개정은 필요 없고 card 경계만 옮긴다. O-69 (2)의 나눔 원칙("나눔은 판정 단위만 바꾸고 design·완료 조건은 그대로")에 맞는다.
- 대가: code 재작업(이동을 되돌림)과 test 파일 재배치. 둘 다 기계적이다.
- 덧붙임: 같은 논리로 `_refine_ends` 삭제 시점도 맞춘다(아래 부수 확인 2).

### 원칙 점검
- 만들면 배선: (나)는 helper가 생기는 순간 사용자가 둘이다. (가)·(라-1)은 사용자 하나인 공용 모듈을 만든다. → (나)만 맞는다.
- fail-closed·약화 금지: (다)는 약화이다. (나)는 test 기대를 낮추지 않고 위치만 옮긴다(단언 수 유지, public-names 단언은 IT-2d에서 같은 강도).
- graph 단일 정본: 해당 없음. 코드 배치 문제이고 새 필드·캐시가 없다.
- 상수 발명: 없음.

| 표시 | 값 |
|---|---|
| design 개정 | 불필요 |
| card 개정 | 필요(IT-2b·IT-2d 범위 경계, 공통 문서 33·35행, 신규 시그니처 표) |
| 계획 개정 | 불필요 |
| 사용자 결정 | 불필요(오케스트레이터 card 정정, 사용자에게 보고). 단 (다)를 고르면 승인 필요 |
| 원래 취지와 다름 | 해당 없음(design 4.7-4의 취지에 더 가깝다) |

---

## 3. 분류표 3건(cnr_ota VOP·VON, erfc_ota out)에 엔진 값이 없음

### 판정
**41:724가 말하는 '불일치'가 아니다.** 승인된 표와 O-66이 이 정지를 미리 예상했다. **사용자 재승인은 필요 없고 card(와 design 41:721) 문언 정정만 하면 된다.**

### 근거
1. **표 자체가 예상했다.**
   - `de1_output_structure_13.md` §0은 "cnr_ota·erfc_ota는 엔진 S0 쓰기 계획이 멈춘다. cnr_ota는 `dc_resistor_cycle`(x40 VCR–VDD_1V8), erfc_ota는 `mos_zero_current_structural`(M19·M20·M21). 그래서 이 두 회로는 topology JSON과 spec 원문으로 같은 정의를 따라 **손 스크립트로** 셌다. 옛 D3는 이 두 회로에서 **정의 불능**"이라고 적는다.
   - §2 표의 #11·#12·#13 '옛 D3' 칸은 '정의 불능', '새 대 옛' 칸은 '비교 불능'이다.
   - §4 Q5는 "분류 writer를 쓰기 계획 블록 안에 두면 이 두 회로는 분류 필드가 없다"고 명시한다.
2. **승인 원문이 이 결과를 받아들였다.**
   - `user_decisions.md:687` O-66 (1)은 "Q5 분류 writer = 쓰기 계획 블록 dc_writer_plan(G_vgs 둘째 생산자 방지, **정지 회로는 소비자 없음**) ... 따로: cnr_ota(dc_resistor_cycle)·erfc_ota(mos_zero_current_structural) 쓰기 계획 정지 = heldout 2회로 엔진 미실행, 백로그 확인"이라고 적는다.
   - 즉 사용자는 '이 3출력은 엔진 값이 없다'를 알고 승인했다.
   - 이 3출력의 '새 분류' 칸은 엔진이 내야 할 값이 아니다. 쓰기 계획 정지가 풀릴 때(백로그) 대조할 기준값이다.
3. **정지 사유가 표와 같다(head 실측, `out/stop/`).**
   - cnr_ota는 `{'nets': ('VCR', 'VDD_1V8'), 'reason': 'unsupported_rule_branch', 'rule_branch': 'dc_resistor_cycle'}`이다.
   - erfc_ota는 `{'reason': 'unsupported_rule_branch', 'rule_branch': 'mos_zero_current_structural'}`이다.
   - 표 §0과 같다. code 작성자 측정(`r1_os_heldout.txt`)은 `plan_stop: "None"`으로 사유를 담지 못했다(`getattr(e, "detail")`가 아니라 `e.record.detail`을 읽어야 한다). 이 측정이 보완한다.
4. **design 721 '정지 먼저'와 맞지만 문언이 좁다.**
   - 41:721은 "저항만으로 이어진 W3–레일 경로는 분류 전에 쓰기 계획의 기존 정지 `dc_resistor_cycle`에서 멈춘다(분류 값 없음, 기존 동작 그대로)"라고 W3–레일 경우만 적는다.
   - 실제 두 회로의 정지는 W3와 무관한 저항 루프(VCR–VDD_1V8)와 `mos_zero_current_structural`이다.
   - 같은 블록이 분류보다 먼저 정지하는 일반 규칙('쓰기 계획이 정지하면 분류 값 없음')은 적혀 있지 않다.
5. **card 문언이 지킬 수 없는 단언을 담고 있다.** card 'library 회로 적용 여부'는 "13회로 출력 15개마다 `node.dc_output_structure` 값이 승인된 표의 '새 분류'와 같음"을 요구한다. 엔진 값이 있는 것은 12출력뿐이다.
6. 나머지 12출력은 head 실측(`r1_os_library.txt`, `r1_os_heldout.txt`)에서 표와 모두 같다: KVL 5(#2·#3·#6·#7·#14), HZ 7(#1·#4·#5·#8·#9·#10·#15). r2r_opamp와 rfc_ota는 stage_a가 stopped/review_needed이지만 분류 값이 있다.

### 권고 (하나)
- card(와 공통 문서 해당 줄)의 대조 단언을 다음처럼 정정한다: "엔진 값이 있는 12출력은 '새 분류'와 같음; 쓰기 계획이 정지하는 회로의 출력(cnr_ota VOP·VON, erfc_ota out -- 표 §0·Q5, O-66 (1) '따로')은 **정지 사유가 표 §0과 같음**(`dc_resistor_cycle` nets VCR·VDD_1V8 / `mos_zero_current_structural`)을 적고 대조 대상에서 뺀다; 사유가 다르거나 다른 출력에서 정지가 새로 나면 41:724대로 멈춤."
- design 41:721의 '정지 먼저' 문장을 "쓰기 계획이 정지하는 회로(`dc_resistor_cycle` 일반·`mos_zero_current_structural` 등 기존 정지)는 분류 값이 없다"로 넓히는 문언 정정을 다음 design 판에 넣는다. 규칙 변경이 아니라 기존 동작을 적는 것이다.

### 원칙 점검
- graph 단일 정본: 분류 writer는 `dc_writer_plan` 하나로 유지한다(O-66 Q5). 정지 회로를 위해 별도 S0 블록에서 분류하는 안(Q5 대안)은 G_vgs 둘째 생산자가 되므로 배제한다.
- fail-closed: 정지 회로는 값을 지어내지 않고 필드 자체가 없다. 소비자 0(O-66).
- 상수 발명: 없음. 물리: 분류 규칙은 그대로이다.

| 표시 | 값 |
|---|---|
| design 개정 | 문언 정정 권장(41:721 '정지 먼저' 일반화, 동작 변경 아님) |
| card 개정 | 필요(대조 단언 15 → 12 + 정지 사유 3) |
| 계획 개정 | 불필요 |
| 사용자 결정 | 불필요(O-66 (1) '따로'·Q5가 이미 승인) |
| 원래 취지와 다름 | 해당 없음 |

---

## 부수 확인

### 1. code 작성자가 정한 이름·규칙이 design에 있는가

| 항목 | design에 있음? | 판정 |
|---|---|---|
| `INPUT_STATUS_*` 상수 이름(`s2_values.py:116-119` -- MEASURED·UNSETTLED·UNMEASURED·F_COMPONENT_UNDECLARED) | **값 어휘는 있다**(41:686 '값 형식' `input_status` ∈ {...}). **상수 이름은 없다**(design grep 0건, card 0건). `__init__` 공개 아님 | **as-built 결정(이름만)**. 동작에 영향이 없고, 같은 파일에 design이 이름을 정한 선례 `OUTPUT_HIGH_IMPEDANCE`·`OUTPUT_KVL_FIXED`(41:720)와 같은 꼴이다. design 문언 반영 권장(다음 판에 이름 인용). 멈출 사안은 아니다. 참고: O-98로 `op_mismatch`는 IT-2b 어휘에서 빠졌다(상수 없음, 맞음) |
| `_module_map` 새 층(`("_helpers_dc_solve.py",)`, LAYERS sizing 셋째 층) | 41:759는 `ModuleEntry` 행만 적고 **층 위치는 적지 않는다** | **as-built이지만 규칙에서 기계적으로 따라 나온다.** `_module_map.py` 머리는 "같은 층끼리 import 금지"이다. helper는 `input_window`·`fixed_point`·`scc_newton`·`_helpers_lut`(둘째 층)를 import하고 `block_columns`(넷째 층)가 helper를 import한다. 그래서 그 사이 새 층 하나만 가능하다. 판단의 여지가 없다. 권고 (나)를 택하면 이 층은 IT-2d로 옮겨진다 |
| F 성분 판정 규칙(`Circuit.writer_head` -- writer 사슬 끝이 F(`FIXED_RELATIONS`)인지, `free_window`인지; `block_columns._windows` 269-272) | 41:697은 개념("그 성분이 레일·W3에 닿아 포트가 W4 뿌리가 아니고 트리 경로로 DC가 정해지는 입력 포트")과 "분류 근거 = 쓰기 계획(writer relation이 `free_window`가 아니고 입력 DC 선언이 없음) -- 새 규칙·상수 없음"을 적는다. **사슬 끝 판정법은 적지 않는다** | **design 개념의 직역이고 새 규칙이 아니다.** 쓰기 계획 머리 4·5(`writer_plan.py:16-19`): 트리 writer는 F 또는 성분 뿌리에서 BFS로 쓰고, F 없는 성분의 뿌리는 입력 포트를 먼저 고른다. 그래서 사슬 끝이 F이면 F 성분, `free_window`이면 그 성분의 입력 뿌리(4.7-3 2)와 동치이다. design 697의 글자 기준('`free_window`가 아니고 선언 없음')만으로는 4.7-3 2의 뿌리 아닌 포트와 구별되지 않는다. 따라서 사슬 끝 판정은 **design 문언 보완 대상**이다(41:697에 'writer 사슬 끝 = F'를 명시). 결정 사항은 아니다 |

부수 관찰(미확인, 발동 0 추정): `_windows` 274-276은 `kernel.measured.slope.get(net, 0.0)`에서 기본값 0.0을 쓴다. 뿌리 성분의 고정 아닌 넷은 `unknown`에 들어 slope에 늘 있으므로 실제로 이 기본값을 쓰는 경로는 없어 보인다. 쓰기 계획 머리 5에 따르면 사슬 끝 `free_window`는 늘 입력 뿌리이다. 기본값이 쓰이면 '감도 0' 대체값이 되므로 fail-closed 관점에서 `slope[net]`(KeyError)이 더 맞다. code 정리 권장이고 결정 사항은 아니다.

### 2. `_refine_ends`가 IT-2d까지 죽은 코드로 남는 것
- 실측: head `block_columns.py:172`에 정의만 있고 호출 0이다(엔진·test grep: 정의, CONTRACT 설명, test docstring 1줄뿐). 판정 영향은 없다(완료 조건 (0) '커널 호출 0' 충족).
- design 41:761: "커널 쪽 `_refine_ends` 호출은 없어지므로 `block_columns.py`의 `_refine_ends`는 **같은 변경에서 지운다**." card IT-2b는 "`_refine_ends` 삭제는 IT-2d(대체 함수와 같은 변경)"라고 적어 **card가 design과 다르다**. design은 IT-2 한 card를 전제로 '같은 변경'이라 썼고, card 나눔이 시점을 IT-2d로 옮겼다.
- '만들면 배선' 원칙에서 보면, 새로 만든 것을 안 쓰는 경우가 아니라 옛 코드의 고아이므로 위반은 아니다. 다만 IT-2d의 끝 풀이는 "`window_refine.py` 안 비공개 함수로 **새로 쓴다**"(41:761)이므로 옛 함수를 남길 엔진상 이유가 없다. 참고용이면 git 이력이 있다. IT-2d의 R2 red는 새 모듈 `ImportError`로 잡으므로(41:804) base에 이 함수가 없어도 된다.
- **권고: IT-2b에서 지운다**(design 41:761을 그대로 따르고 card 한 줄 정정). 이렇게 하면 card 공통 문서 133행의 '없어지는 심볼' 목록과 시점이 맞는다. 사용자 결정은 필요 없다(오케스트레이터 card 정정).

---

## 미확인
- 탐색 예산이 40보다 크거나 최적점이 y 상자 경계에 있는 회로에서 y 끝 거부가 실제로 얼마나 나오는지(이번 9회로 실측은 도달 0).
- current_reuse_telescopic_ota는 탐색점 40개가 모두 봉인 7 실패라 끝점 재평가 대상이 없었다(head·base 같음, IT-2b와 무관한 기존 상태).
- heldout 4회로의 y 끝 동작(쓰기 계획 정지·stage A 상태 때문에 측정하지 않음).
- dispute 문서 1·3·4·5번(이번 판정 범위 밖).
