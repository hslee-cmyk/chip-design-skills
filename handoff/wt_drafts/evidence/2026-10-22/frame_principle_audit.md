# 틀 원칙 전수 감사 -- "계산 틀은 질문에 맞춘다"(사용자 지정 2026-10-22)

- 작성: 2026-10-22, 감사 agent(읽기 전용). 저장소 파일은 고치지 않았다. git은 `git -C`로 읽기만 했다.
- 대상
  - 계획: `chip-design-skills/docs/01-plan/features/gain-budget-gmid-sizing.plan.md` v6.33(master 작업 트리)
  - design: 같은 저장소 `docs/02-design/features/gain-budget-gmid-sizing.40-engine.design.md`, `...41-gain-budget.design.md` v1.12.11
  - 엔진: `wt/integ-it12/skills/analog-gmid-design/gmid_engine/`(head `6afe4758`)
  - 미병합 card: `wt/integ-it12/docs/02-design/specs/20261021-it2c-*`, `-it2d-*`(두 card 모두 code 브랜치 없음 -- `git -C … branch -a`에 `role/code/it2c`·`it2d` 없음)
- 근거 실측: `it2c_spice_frame.md`(이 폴더). 이번 감사 실측: `wt/_scratch_frame_audit/`(`swing_frame.py`, `out/*.swing.json`).
- 이미 결정된 것: O-108 -- HZ follower 감도는 KCL. 이 문서는 그 밖의 자리를 찾는다. O-108 자리는 딸린 자리를 찾기 위해 C0으로만 적는다.

## 0. 결론

1. **설계점 질문(θ 맞음)**: 커널 노드 풀이·봉인, 커널 창 A6 되풀이(y_icm 범위), `fd_jacobian` y 스텝, `kvl_window`, `headroom_bound`·`iv_headroom`, 층 0 조립·국소 봉인, 감도 게이트. 위반 없음.
   - y_icm 범위는 θ 변수의 범위 정의라 위반이 아니다(지시대로 구분).
2. **섭동 질문인데 KCL을 쓰는 자리(맞음)**: `icm_config`의 KVL 고정 (3)·`as_is_single_input` (5)·선언 되먹임 S-3·반전 입력 T_p, `offset_analysis`, `mirror_ratio`, DE-1 (c) 새 계통 offset 식, DE-1 (b) KVL 고정 스윙, AC metric 전부, 판정 분해능 δV_out.
3. **위반 6건(O-108 제외)**
   - C1 다듬은 창 `dc_window_refine`의 θ 고정 대신호 끝 풀이(IT-2d)
   - C2 DE-1 정의 창의 'θ 고정 끝점 손계산 블록'
   - C3 DE-1 고임피던스 출력 스윙의 θ 고정 끝과 다듬은 출력 창
   - C4 계획 N3.8 표·문장의 θ 고정 문언(609행 등)
   - C5 현 head의 `ls_swing`·`ls_fields` 경로 합 휴리스틱(이미 삭제 예정)
   - C6 현 head `offset_systematic` 분자(θ 프레임 구조적 0, 이미 DE-1 (c)가 고침)
4. **경계 6건**
   - D1 커널 `node.dc_window`의 뿌리 아닌 포트·선언 포트 항목: 섭동 성격의 값을 θ로 재는데 값 소비자가 없다.
   - D2 cfg 창이 커널 `unsettled`를 이어받음: 틀 사이 결합이다.
   - D3 F 성분 미선언 포트를 정의 불능으로 둠: 사유가 θ 틀에서 왔다.
   - D4 `node.dc_output_structure`: KCL로 바꾸면 엔진 소비자가 사라진다.
   - D5 `saturation_window`의 `roots` 쌍·묶음 꼴: 소비자가 사라진다.
   - D6 L8 (a) 기대값 문언.
5. **설계점 질문인데 θ가 아닌 무거운 계산**: 찾지 못했다(0건, 범위는 1절).
6. **실측 -- 고임피던스 출력 스윙(C3) θ 대 KCL, 봉인점 = layer0 시작점**
   - 끝 차: two_stage_ota 0.0 / 0.0 mV, ngcc_3stage_ff 0.0 / 0.0 mV, folded_cascode 아래 4.1 / 위 1.8 mV.
   - 내부 노드 감도 차: 최대 0.062 / 0.179 / 0.017 V/V.
   - 출력단 소자 행이 두 틀에서 기울기 ±1로 같아 끝이 거의 같다. 원칙 위반이지만 이 세 회로에서 수치 영향은 작다.
7. **권고 핵심**(O-108과 한 계획 개정으로 묶는다)
   - ICMR 측정 구성은 모두 KCL(`graph.ss_nodal` + 닫음)로 둔다.
   - 다듬은 창(대신호 θ 끝 풀이)은 모든 구성에서 없앤다. 정확값은 oracle `.dc`가 잰다.
   - DE-1의 이름·범위를 'θ 고정 끝점 손계산'에서 '봉인점 DC 야코비안(KCL) 선형 감도 끝 하나'로 바꾼다.
   - 이 바뀜이 낳는 소비자 소멸(D4·D5·`metrics_icm_front`)을 같은 개정에서 정리한다.
   - **원래 취지와 다른 항목이 있다**(5절 표 '취지' 칸). 사용자 결정이 필요하다.

## 1. 방법

- 문서: 계획 N3.8(584~622행, 596행은 문장 단위로 나눠 전부 읽음), N6.6(1499~1529행 grep), N6.8 DE-1(1592~1655행 전부), LA-1 표(1756~1792행). design 41 §4.6·§4.7(604~842행; 734~746행 전부). design 40은 grep(`θ 고정`·`follower`).
- 엔진: 후보 파일 머리말과 핵심 함수를 읽었다.
  - `sizing/input_window.py`(전부)
  - `sizing/block_columns.py`: `region_rows`·`input_windows`·`writer_grad` 240~470, `_solve_input_window`·`_windows` 727~800
  - `metrics/` 머리말: `ls_swing`·`ls_fields`·`offset_systematic`·`offset_analysis`·`sensitivity`·`sensitivity_gate`·`mirror_ratio`·`dc_limit`·`point_solve`·`headroom_bound`·`rout`·`supply`·`dc_metrics`
  - `search/` 머리말: `iv_headroom`·`fd_jacobian`·`residual_probe`
  - `node.dc_window` 소비자 grep
- '무거운 설계점 계산' 찾기 범위: 층 0(LA-1 표 전 단계), 커널(`kernel_run` steps), 출발 구간(`iv_*`), 탐색(`fd_jacobian`·`residual_probe`·`sensitivity_gate`). KCL 대신호 풀이(W 고정 순풀이)를 설계점에 쓰는 자리는 없었다. 엔진 전 파일 전수는 아니다(미확인 범위 = 위 밖 search 파일 머리말).
- 실측(2절 C3): `wt/_scratch_frame_audit/swing_frame.py`
  - `_scratch_it2c/src` 엔진을 import했고 APPDATA를 export했다. 순차 실행, SPICE는 쓰지 않았다.
  - 봉인점 = `it2c_spice_frame` `eng_seal.py`와 같은 layer0 시작점 봉인이다.
  - 끝 식 = 엔진 `saturation_window(slope=)`, 행 = 엔진 `region_rows`다.
  - θ 연립 = `_sensitivities`와 같은 식이다(writer 식 기울기). 출력 W4 뿌리 행 s = 1, 입력 넷 행 s = 0이다.
  - KCL = `conductance_matrix` + `nodal_factor`, 입력 넷 고정, 차동 구동 ±1/2, 출력 1 V 당으로 정규화했다.

## 2. 자리 목록

질문 성격: **설계점** = 어떤 θ(W·전류)로 설계할까 / θ 변수의 범위. **섭동** = 정해진 회로(W·바이어스 고정)를 흔들면.
줄 표기: `E/` = 엔진 head `6afe4758`, `P:` = 계획 v6.33 줄, `D41:` = design 41 v1.12.11 줄.

### 2.1 설계점 질문 -- θ 고정(맞음)

| # | 자리 | (a) 질문 | (b) 틀·근거 | (c) 판정 |
|---|---|---|---|---|
| A1 | 커널 노드 풀이 `dc_columns`·봉인 7·9 헤드룸 | 설계점(θ로 노드 전압·W) | θ 고정 writer plan -- `E/sizing/block_columns.py` 머리말 1~43, P:608 '헤드룸(봉인 7) θ 고정 노드 풀이 + 봉인' | 맞음 |
| A2 | 커널 창 A6 되풀이 = 입력 W4 뿌리 y_icm 범위 `node.dc_window`(뿌리 항목) | 설계점 -- θ 변수 y의 정의역(J-E 'y_icm 범위') | θ 고정 감도 `saturation_window(roots=(뿌리,))` -- `E/sizing/block_columns.py:727-777`, `:687`; D41:694, D41:633 | **맞음(θ 변수 범위 정의 -- 위반 아님)**. 매 평가 `k_max` 안 되풀이 비용은 미측정 |
| A3 | `fd_jacobian` y 스텝 | 설계점(θ 미분 스텝) | W4 뿌리 `dc_window` 폭 -- `E/search/fd_jacobian.py:41-68`; D41:680 | 맞음 |
| A4 | 순서 창 `kvl_window`(W4 y의 [lo, hi]) | 설계점 | writer 식 -- `E/sizing/block_columns.py` `update`·`writer_grad` W4 갈래(약 `:445-468`) | 맞음 |
| A5 | 헤드룸 달성가능성 `headroom_bound`(§4.6) | 설계 공간(어떤 θ로든 닿는가 -- LUT 격자 상한) | 구조 경로 + LUT 최솟값 -- `E/metrics/headroom_bound.py` 머리말; D41:604-645 | 맞음(DEC-67 예외 그대로) |
| A6 | 출발 구간 gm/ID 하한 `iv_headroom` | 설계 공간 | 같은 경로 그래프 -- `E/search/iv_headroom.py` 머리말 | 맞음 |
| A7 | 층 0 조립·국소 봉인·수리·외층 | 설계점 | θ 고정 쓰기 계획 W0~W4 -- P:1760, 1782~1790 표 | 맞음 |
| A8 | 감도 게이트(θ 섭동 재평가) | 설계점 집합 위 metric 정의의 성질 | θ 섭동 커널 재평가 -- `E/metrics/sensitivity_gate.py` 머리말, P:592 | 맞음(회로 반응이 아니라 두 metric 정의를 같은 설계점들에서 비교) |

### 2.2 섭동 질문 -- KCL(맞음)

| # | 자리 | (a) | (b) 틀·근거 | (c) |
|---|---|---|---|---|
| B1 | `icm_config` (3) KVL 고정 follower·(5) `as_is_single_input`·S-3 선언 되먹임·(1) 반전 입력 T_p | 섭동(ICMR, 정해진 회로) | `graph.ss_nodal` G + Schur 닫음 / `nodal_solve` -- D41:734 (1)(3)(5), D41:738; IT-2c spec '계산' | 맞음 |
| B2 | 판정 분해능 δV_out = \|z_u\|ᵀ\|r\| | 섭동 해의 수치 분해능 | 같은 KCL 인수분해 -- D41:735, P:596 문장 6~16 | 맞음 |
| B3 | `offset_in_sigma_mv`(σ) | 섭동(mismatch) | ω → 0 컨덕턴스 계 adjoint -- `E/metrics/offset_analysis.py` 머리말, P:612·618 | 맞음 |
| B4 | `mirror_ratio_sigma_pct` | 섭동 | 같은 VGS(바이어스 고정)에서 ΔI/I = (gm/ID)·ΔVGS -- `E/metrics/mirror_ratio.py` 머리말 | 맞음(국소 KCL 근사) |
| B5 | DE-1 (c) 새 계통 offset ΔV_out = −G⁻¹·ΔI, V_id* = −ΔV_out / A_dc | 섭동(ΔW) | 노드 전압 고정 ΔI + G⁻¹ -- P:1592~ DE-1 (c)(de1 범위 1 (c)), P:611 | 맞음 |
| B6 | DE-1 (b) KVL 고정 출력 스윙 | 섭동(차동 훑기) | 봉인점 DC 야코비안, `kvl_sensitivity` 재사용 -- P:610, DE-1 (b) | 맞음 |
| B7 | AC metric(`gain_ss_db`·PM·`rout_ss_ohm`·잡음·`sensitivity.py` adjoint) | 섭동(소신호) | 봉인점 MNA(고정 동작점 선형화) -- P:586~592·602~605 | 맞음 |
| B8 | 경계 행 `region_rows`(4.7-3a) | -- (행은 틀과 무관, 감도 생산자가 틀을 정함) | `E/sizing/block_columns.py:247-268`, D41:705 | 맞음. 단 (다) `off` 행(V_on − VGS)은 θ 틀에서는 θ 전류 소자의 VGS가 거의 안 움직여 사실상 죽은 행이다. KCL에서만 뜻이 있다(C2 참고) |
| B9 | DE-1 (d) 슬루 방향 최대 전류 = θ 전류 기저 합 | 섭동(입력을 끝까지 몬 정해진 회로) | 바이어스 고정 → 전류원 전류 = 봉인점 θ 값(이상 전류원 근사) -- P:613, DE-1 (d) | 맞음(근사 -- gds·VDS 변화 무시, '추정' 표기·SPICE 확정과 기초 가정에 맞음) |

### 2.3 섭동 질문인데 θ 또는 다른 틀 -- 위반

| # | 자리 | (a) | (b) 틀·근거 | (c) |
|---|---|---|---|---|
| C0 | (O-108, 결정됨) `icm_config` (2) HZ follower 감도 | 섭동 | θ 연립 + W4 뿌리 행 V_out = x -- D41:734 (2)(4), P:596 문장 55·65~66 | 위반(결정됨) -- 딸린 자리: W3 목표 HZ 출력 `roots=(출력,)`(D41:734 (4)), S-OS1(D41:725), `saturation_window` 쌍 꼴(D5) |
| C1 | 다듬은 창 `dc_window_refine` 끝 풀이 | 섭동(ICMR 끝의 정밀값) | **θ 고정 대신호** -- 뿌리 `override` = (x, x), HZ follower는 W4 y를 V_out = x로 정한 1변수 풀이, W3 HZ는 `fixed_values[출력]` = x, 선언 포트 묶음은 `fixed_values[p]` = 선언값 + Δ -- D41:764(4.7-4 2), D41:736 끝 두 문장, P:596 문장 55·66, N6.6 범위 1(다듬은 창 (a)(b)(c)), IT-2d spec '관찰 가능한 계약' | **위반** |
| C2 | DE-1 (a) 정의 창 `node.dc_window_def`·DE-1 완료 조건 1·2 (ii) | 섭동(ICMR 정의 끝) | 'θ 고정 끝점 손계산 블록 하나 -- `saturation_window` 선형 감도(θ 고정 노드 풀이의 야코비안) 일반화' -- DE-1 제목, 범위 1 머리, 완료 조건 1 '정본 하나: θ 고정 끝점 계산 자리', 2 (ii) 'θ 고정 선형 감도에서는 … 조향되어 꺼지는 경우는 표현할 수 없고' | **위반**(HZ 갈래. KVL 고정·단일 입력 갈래는 이미 KCL) |
| C3 | DE-1 (b) 고임피던스 출력 스윙(커널 선형 끝 + 다듬은 출력 창) | 섭동(차동 훑기) | θ 고정 선형 감도 끝, 끝 풀이 다듬기 -- DE-1 (b), P:609 표 행 | **위반**(실측 영향 작음 -- 3절) |
| C4 | 계획 N3.8 문언 | -- | P:609 표 '`icmr_v`·`icm_margin_v`·고임피던스 `swing_out_v` -- 평가 커널: θ 고정 선형 감도 끝 … 끝 풀이(Newton)'. P:596 문장 85 'θ 프레임 끝점 계산법(DC 끝점 풀이 하나)은 card DE-1'. 문장 55 'HZ 단일 출력은 θ 고정 연립과 다듬은 창 경로를 유지' | **위반**(문서) |
| C5 | 현 head `ls_swing`(스윙·ICMR·margin)·`ls_fields` σ 셀 VGS_max | 섭동 | 경로 합 차분 제약계 + 'source가 레일이 아니면 VGS 고정' 휴리스틱(θ도 KCL도 아님) -- `E/metrics/ls_swing.py` 머리말, `E/metrics/metrics_aux.py:16, :239`, `E/metrics/ls_fields.py` 머리말 | 위반. 삭제 예정(IT-2d = ICMR 입력 창, DE-1 = 스윙·`ls_fields`). 다만 DE-1의 HZ 스윙 대체가 C3(θ)라 그대로면 위반이 남는다 |
| C6 | 현 head `offset_systematic` 분자 '봉인 해의 입력 0 출력 오차' | 섭동 | θ 프레임 해(구조적 0) / KCL A_dm -- `E/metrics/offset_systematic.py:5-8, :28-52`, `metrics_aux.py:202` | 위반. DE-1 (c)가 B5 식으로 고치기로 이미 정함 -- 새 원칙과 같은 방향 |

### 2.4 경계

| # | 자리 | (a) | (b) | (c) |
|---|---|---|---|---|
| D1 | 커널 `node.dc_window`의 뿌리 아닌 입력 포트 항목(4.7-3 2)·입력 DC 선언 포트 묶음 항목(4.7-3 3) | 선언 포트 = 섭동('그 포트를 바깥에서 구동할 때 포화가 유지되는 범위', D41:696). 뿌리 아닌 포트 = y 범위의 포트 전압 사상 | θ 감도 -- `E/sizing/block_columns.py:783-800`(`_windows`, 선언 묶음 `:790-799`); 값 소비자 = `fd_jacobian`이 W4 뿌리만 읽음(`fd_jacobian.py:55`), 나머지 소비자 0(grep). 상태 칸만 D2 이어받기로 cfg에 들어간다 | 경계(값 소비자 없음 = 계산 낭비 + 섭동 성격 양을 θ로 잼). 선언 포트의 tol 미정 `unsettled`가 D2로 KCL cfg 창을 정의 불능으로 만든다 |
| D2 | cfg 창이 커널 `unsettled`를 이어받음(4.7-3b (가)) | -- | D41:737, N6.6 범위 1, O-61 P5; IT-2c spec T-INH | 경계(틀 사이 결합). 봉인점은 봉인을 통과한 유효 동작점이고, KCL 창은 y 범위 수렴과 무관하게 정의된다. y 범위(설계점 질문)의 미수렴이 섭동 질문 metric을 정의 불능으로 만든다 |
| D3 | F 성분 미선언 입력 포트 = 정의 불능(`f_component_undeclared`) | 섭동(ICMR) | D41:697, O-61 P4 (b). 근거 '그 포트 하나만 자기 x로 훑는 창은 …' -- θ 틀에서 그 포트 전압이 쓰기 사슬로 고정된다는 데서 나온 제약 | 경계. KCL에서는 입력 넷이 고정 노드(구동)라 같은 x로 함께 움직일 수 있어 정의가 가능해 보인다. library 발동 0(heldout r2r_opamp 꼴) |
| D4 | `node.dc_output_structure`(writer `dc_writer_plan`) | 구조 분류 | 소비자 = `icm_config` (2)/(3) 갈래 선택, `dc_window_refine` 2 (b), DE-1 (b) -- D41:722 | 경계. HZ가 KCL로 가면 (2)·(3)이 같은 식(G + follower 닫음, 근거 실측 `it2c_spice_frame.md` 1.5)이 된다. C1을 없애면 (b) 소비자도 없다. DE-1 (b)도 두 구조가 같은 KCL 차동 훑기다(P:596 문장 56 '전회로 야코비안이 두 꼴을 모두 담는다'). 엔진 소비자 0 → 삭제 또는 출력 전용 선언(graph 계산값 소비 규칙). S-OS1 code·계획 B3 대기도 함께 사라진다 |
| D5 | `saturation_window`의 `roots` 쌍 꼴 `(행 넷, 고정 넷)`·묶음 꼴 | -- | `E/sizing/input_window.py:33-40` | 경계. 쌍 꼴의 유일한 소비자 = HZ follower θ(C0). 묶음 꼴의 소비자 = D1 선언 포트 항목. 둘이 빠지면 죽은 코드 |
| D6 | design 41 L8 (a) 기대값 | -- | D41:811 '`node.dc_window_cfg`·`node.dc_window_def_refined` 끝 = follower 연립 끝(손계산 오라클)' | 경계(문서). 손계산 오라클이 θ 연립이면 C0과 충돌. 다듬은 창 단언도 C1에 걸림 |

## 3. 위반·경계의 물리적 영향

| # | 영향 추정 | 근거 |
|---|---|---|
| C0 | 감도 오차가 θ 쪽 최대 0.163 V/V(KCL 0.021). 창 끝에서 틀이 낳는 몫은 θ 21~61 mV, KCL 2~10 mV이고 tol_VDsat는 1.9~20 mV | `it2c_spice_frame.md` §0·§2.3(SPICE 대조) |
| C1 | θ 가정(바이어스 gate가 움직임, 종속 gds 빠짐, 배선 조건 깨짐)을 대신호로 그대로 지닌다. 크기는 **미확인**(IT-2d 미구현, 대신호 θ 끝 풀이 실행 안 함). 선형 몫(C0)보다 작을 근거는 없다. 출발 창(cfg = KCL)과 끝 풀이(θ)의 고정 변수가 달라 N6.6 범위 1 '같은 측정 구성·같은 기준'이 깨진다 | `it2c_spice_frame.md` §4.2 |
| C2 | C0과 같은 크기(HZ 정의 창). 더해 θ 틀에서는 전류 조향으로 꺼지는 전도 끝을 표현하지 못한다(DE-1 완료 조건 2 (ii) 원문이 인정함). KCL 선형 감도에서는 ID(x) 기울기가 있어 조향으로 꺼지는 끝을 1차로 낸다 | DE-1 완료 조건 2 (ii) |
| C3 | **실측(이번 감사)**: 아래 표. 출력단 행이 두 틀에서 기울기 ±1로 같아 끝 차가 작다. 내부 노드 감도는 크게 다르다 -- 내부 행이 끝을 정하는 회로에서는 C0 크기의 차가 날 수 있다(미확인) | `wt/_scratch_frame_audit/out/*.swing.json` |
| C4 | 문서가 구현을 θ로 이끈다(IT-2d·DE-1 착수 때 그대로 구현됨) | -- |
| C5 | 경로 합 ICMR과 DC 끝 풀이 차가 ICMR 폭 0.13~0.30 V였다(F-DE6, 옛 측정) | P:N6.8 F-DE6 |
| C6 | θ 프레임 봉인점에서 분자가 구조적 0이라 offset 위반을 거부하지 못한다(감사 P5) | P:611, DE-1 (c) |
| D1 | 값 영향 0(소비자 없음). 비용 = 선언 포트 회로에서 평가마다 감도 연립 1회. 상태가 D2로 KCL 창을 정의 불능으로 만들 수 있다(선언 포트에서 tol 미정일 때 -- 운영 sky130 v2에서 tol 미정 갈림 0, `a6b_reachability.md`) | `block_columns.py:790-799` |
| D2 | A6 b·c가 나면 KCL ICMR metric·선언 제약이 정의 불능 → 그 점은 front에서 빠진다. 발동 수는 미확인(A6 c 발동은 9회로 측정 기록에서 찾지 못함) | D41:737 |
| D3 | library 0, heldout r2r_opamp 1(F-IT9). 지금은 정의 불능으로 front 값이 없다 | D41:697 |
| D4·D5 | 값 영향 0. 죽은 필드·죽은 갈래 | -- |

### C3 실측 -- 고임피던스 출력 스윙, 출력 이동량 Δ(V) 끝

| 회로 | V_out(V) | θ [dlo, dhi] | KCL [dlo, dhi] | 끝 차(mV) | 끝을 정한 행 | 내부 감도 차 최대(V/V, 노드 θ / KCL) |
|---|---|---|---|---|---|---|
| two_stage_ota | 0.900 | [−0.8538, +0.7975] | [−0.8538, +0.7975] | 0.0 / 0.0 | OUT–gnd, OUT–vdd(기울기 ±1, 두 틀 같음) | 0.062(O1 −0.114 / −0.176) |
| ngcc_3stage_ff | 0.900 | [−0.8502, +0.8371] | [−0.8502, +0.8371] | 0.0 / 0.0 | Vout–gnd, Vout–vdd | 0.179(V2 −0.042 / −0.221) |
| folded_cascode | 1.132 | [−0.4265, +0.4465] | [−0.4223, +0.4448] | 4.1 / 1.8 | out–Vg10(θ 0.940 / KCL 0.949), out–X(−0.911 / −0.914) | 0.017(입력 ±0.017, Vg7 0 / −0.016) |

- 정의는 같다: 입력 공통모드 고정, 차동 훑기, 끝 = `region_rows` 여유 0. VDsat는 해 값으로 고정했다(두 틀 같음). SPICE 대조는 하지 않았다.
- folded의 4.1 mV는 tol_VDsat 범위(1.9~20 mV) 안이다.

## 4. 설계점 질문인데 θ가 아닌 자리(불필요하게 무거운 계산)

- 0건. 층 0·커널·출발 구간·탐색 모두 θ 고정 쓰기 계획을 쓴다. KCL 소신호는 결합 잔차 거르기(작은 MNA, AC)에만 있고 그것은 AC 양이다(P:1786 표).
- 참고: 커널 A6 되풀이(A2)는 매 평가 최대 `k_max`번 다시 푼다. 틀은 맞다. 비용은 미측정이다.

## 5. 수정 방향

'취지' 칸: **다름** = 원래 취지와 다름, 사용자 결정 필요. **같음** = 기존 결정의 적용.

| # | 고칠 곳 | 수정 방향 | 취지 | card |
|---|---|---|---|---|
| C0 | 계획 N3.8 문장 55·65~66, design 41 4.7-3b (2)(4), IT-2c spec·interface | O-108대로 HZ follower = `graph.ss_nodal` + follower Schur 1칸(`kvl_sensitivity`, (3)과 같은 함수). W3 목표 HZ 출력도 같은 식(목표값은 sizing 기준점이지 물리 전원이 아니라 KCL 계에 고정 노드로 들어가지 않는다). 그래서 S-OS1 갈래는 생기지 않는다 | 다름(O-108로 결정됨; W3·S-OS1 확장은 O-108 문언 범위 확인 필요) | IT-2c |
| C1 | 계획 N6.6 범위 1(다듬은 창)·N3.8 문장 55·66·'창 필드'(문장 107의 다듬은 정의 창), design 41 4.7-2 표 4행·4.7-4 전부·4.7-5 front·4.7-3b 736 끝, IT-2d spec, 계획 LA-1 범위 12 | **모든 측정 구성을 '선형 감도 끝만 정의되는 구성의 정본 칸'에 넣는다**(`it2c_spice_frame.md` §4.2 (i)). 다듬은 창 블록과 그 필드(`node.dc_window_def_refined`·`RefinedWindow`·`WindowEnd`·사유 상수 셋·`refine_front_windows`·perf `window_end_solves`)를 만들지 않는다. front·보고 값 = cfg(DE-1 뒤 def) 창, 정확값 = oracle `.dc`. KCL 대신호 끝 풀이(W 고정 순풀이)는 O-32가 금지한다 -- 대안 (ii)는 기각이 맞다. 이때 `metrics_icm_front`는 커널 `metrics_aux` ICM과 같은 입력·같은 정의가 되어 둘째 생산자다 → front는 커널 값을 읽고 블록을 만들지 않는다(graph 규칙 3) | **다름**(O-21·O-25 (3)·O-33 (3) '수락 반복·front는 끝 풀이로 다듬음', O-49 P4·P6, O-61 P6, O-64 (2)) | IT-2d(범위 대폭 축소), LA-1 범위 12 삭제 |
| C2 | 계획 N6.8 DE-1 제목·범위 1 머리·(a)·완료 조건 1·2 (ii)·X-DE4 | 'θ 고정 끝점 손계산 블록 하나' → '봉인점 DC 야코비안(KCL) 선형 감도 끝 하나'. 정의 창(tol 없음·전도 끝)은 `icm_config`가 같은 감도로 쓴다(이미 'writer 자리 = 측정 구성 블록'). 완료 조건 2 (ii) toy를 '전류 조향으로 꺼지는 끝을 1차로 낸다'로 바꾼다 -- KCL에서는 이 끝이 표현된다 | 다름(O-33 (2) 'θ 고정 손계산 기계 하나'의 '기계' 정의). 손계산·SPICE 확정 취지는 같음 | DE-1(미착수) -- 계획만 |
| C3 | 계획 P:609 표 행, DE-1 (b) | HZ 출력 스윙 = KVL 고정과 같은 KCL 차동 훑기(`kvl_sensitivity` 구동만 차동, 닫음 없음). 다듬은 출력 창 없음. 두 구조 구분 불요(D4) | 다름(작음 -- O-43 D1 (a)를 HZ로 넓힘) | DE-1 |
| C4 | 계획 P:609 표, P:596 문장 55·65~66·85, N6.8 제목 | C0~C3 결과대로 문언 정리. 'θ 고정 손계산 근거' 문단은 history로 옮긴다 | C0~C3에 따름 | 계획 개정(IT-2c 착수 전) |
| C5 | (없음 -- 삭제 예정 확인) | IT-2d가 ICMR 입력 창 계산을 지울 때 `ls_swing` 스윙 부분은 DE-1까지 남는다. DE-1 대체가 C3(KCL)이어야 위반이 끝난다 | 같음 | IT-2d·DE-1 |
| C6 | (없음) | DE-1 (c) 그대로 | 같음 | DE-1 |
| D1 | design 41 4.7-3 2·3, 4.7-2 표 1행 '쓰는 범위', 계획 N6.6 범위 1 (c), `E/sizing/block_columns.py:783-800`(IT-2b 병합 code) | 커널 `node.dc_window`는 W4 뿌리 항목만(θ 변수 범위)으로 줄이고, 뿌리 아닌 포트·선언 포트 묶음 항목을 지운다. 포트 창은 cfg(KCL) 하나. `port_window`·`declared_inputs` 묶음 경로도 소비자를 확인한 뒤 함께 지운다 | **다름**(O-16 (2) '노드 풀이 블록이 모든 입력 포트 창을 쓴다', IT-2b 범위) | IT-2c(같은 변경에서 θ 항목 삭제) 또는 작은 새 card |
| D2 | design 41 4.7-3b (가), 계획 N6.6 범위 1 '커널 창 되풀이 미수렴', IT-2c spec T-INH | cfg는 커널 `unsettled`를 이어받지 않는다. 봉인점이 유효하면 KCL 창은 정의된다. `icm_config` READS의 `node.dc_window`도 지운다. `f_component_undeclared` 이어받기는 D3 결정에 따른다 | **다름**(O-61 P5) | IT-2c |
| D3 | design 41 4.7-3 3, 계획 N6.6 범위 1 (c) | KCL cfg에서는 그 포트를 묶음에 넣어 같은 x로 움직이는 꼴이 정의 가능해 보인다. 회로 해석 공동분석 뒤 결정(발동 library 0) -- 지금은 그대로 두고 백로그 | 다름(O-61 P4 (b)) -- 보류 권고 | 백로그(후속) |
| D4 | design 41 4.7-1a, 계획 N3.8 문장 67~72·110, `E/sizing/writer_plan.py:25, :77, :143` | C0·C1·C3 뒤 엔진 소비자를 다시 센다. 0이면 삭제(또는 보고용 출력 전용 선언). S-OS1 code `icm_config_output_root_w3`·계획 B3 대기 삭제 | **다름**(O-64 (1)·O-66 (1)(3) 분류 기준선) | IT-2c(소비자 소멸 확인) + 삭제는 승인 |
| D5 | `E/sizing/input_window.py:33-40`, D41:695 서명 문언 | 쌍 꼴 삭제(C0), 묶음 꼴은 D1 결정에 따름. 서명 `saturation_window(unknown, roots, …)`의 `roots`를 커널 뿌리 하나로 줄일지는 IT-2c design 몫 | 같음(죽은 코드 금지) | IT-2c |
| D6 | D41:811 L8 (a), 4.7-7 관련 test interface | 손계산 오라클 = KCL follower(G + 닫음), 다듬은 창 단언 삭제(C1) | C0·C1에 따름 | IT-2c·IT-2d test 주체 |

- **y 같은 θ 변수의 범위 정의는 위반이 아니다**: A2·A3·A4는 고치지 않는다. 커널 창이 y 범위로 남는 것은 원칙에 맞다.
- **IT-2e**(4.7-3c 실패 평가 부분 스냅샷)는 틀과 무관하다. 영향 없다.

## 6. 요약표와 권고 순서

| 판정 | 수 | 자리 |
|---|---|---|
| 맞음(설계점, θ) | 8 | A1~A8 |
| 맞음(섭동, KCL) | 9 | B1~B9(B9는 근사) |
| 위반 | 6 + O-108 | C1~C6 (+ C0) |
| 경계 | 6 | D1~D6 |
| 설계점인데 무거운 KCL | 0 | -- |

**권고 순서**

1. **계획 개정 하나로 묶는다**(IT-2c 착수 전, S-7 '계획부터'). 내용:
   - O-108의 N3.8 개정
   - C1 다듬은 창 폐지(사용자 결정)
   - C2·C3 DE-1을 KCL로 바꿈
   - C4 문언 정리
   - D2 이어받기 폐지(사용자 결정)
   - D1 커널 창을 W4 뿌리로 축소(사용자 결정)
   - D4 소멸 예고

   한 번에 결정받아야 IT-2c·IT-2d design 재동결이 한 번으로 끝난다.
2. **design 41 개정**: 4.7-2·4.7-3 2·3·4.7-3b (2)(4)(가)·4.7-4·4.7-5 front·4.7-7 L8을 바꾸고, IT-2c·IT-2d card를 재동결한다.
3. **IT-2c 구현**: 다음을 한 변경에서 한다.
   - KCL follower
   - θ 쌍 꼴 삭제
   - 커널 θ 포트 항목 삭제(D1을 받아들일 때)
   - 이어받기 삭제
   - D4 소비자 재계수
4. **IT-2d 축소**: `icm_window_metrics`·`metrics_aux` 배선·`ls_swing` 입력 창 삭제만 남는다. 다듬은 창·front 블록은 만들지 않는다.
5. **DE-1(미착수)**: 계획 문언만 지금 고치고, 착수 때 KCL 정의 창·스윙을 만든다.
6. D3는 백로그(공동분석).

## 7. 원칙 자기 점검표

| 원칙 | 점검 |
|---|---|
| 기초 가정(손계산 근사 감수, 정확값 SPICE, 무거운 계산 회피) | 권고는 무거운 계산을 줄인다. 다듬은 창의 대신호 끝 풀이(평가마다 끝 2개 × `k_max` 되풀이)와 커널 θ 포트 감도 연립을 없앤다. KCL 선형 끝은 이미 있는 `ss_nodal` 인수분해 위의 `nodal_solve` 몇 번이다. 정확값은 oracle `.dc`(O-32·O-63 (4) 선례). 새 풀이기 0 |
| 물리 우선 | KCL은 SPICE `.dc` 접선과 0.021 V/V 안에서 맞고, θ는 바이어스 gate 이동·종속 gds 누락으로 틀린다(근거 실측). 스윙도 같은 틀로 맞춘다(이번 실측은 영향이 작음을 함께 보고) |
| DC/AC 분리 | KCL 계 = 봉인점 ω → 0 컨덕턴스(DC 야코비안)이고 DC 양(ICMR·스윙)에 DC 접선을 쓴다. AC 이득 나눗셈 없음. `ss_nodal`이 소신호 gm·gds로 조립되지만 그 값은 동작점 DC 미분이다(근거 실측에서 SPICE `.dc` 접선과 일치) |
| graph 단일 정본 | 감도 생산자가 `graph.ss_nodal` + `kvl_sensitivity` 하나로 모이고 θ 둘째 생산자(`writer_grad` 쌍 꼴)가 사라진다. 다듬은 창 필드·`metrics_icm_front`(커널 ICM과 같은 정의 = 둘째 생산자)를 만들지 않는다. 소비자가 사라지는 필드(D4)·갈래(D5)는 삭제 또는 출력 전용 선언으로 처리한다. 새 cache·memo·sctx 슬롯·값 사본 0. 커널 `node.dc_window`는 W4 뿌리(θ 변수 범위) 한 뜻만 남는다(규칙 3: 측정 구성 창과 다른 정의 = 다른 필드 유지) |
| 상수 발명·회로 이름 | 0건. 측정 스크립트는 회로 이름을 인자로만 받는다 |

## 8. 미확인

1. C1 대신호 θ 끝 풀이의 SPICE 대비 오차(IT-2d 미구현, 실행 안 함).
2. C3에서 내부 노드 행이 끝을 정하는 회로의 θ/KCL 끝 차(이번 3회로는 출력단 행이 지배). 나머지 6회로·heldout은 재지 않았다.
3. A2 커널 A6 되풀이의 평가당 비용과 D2 이어받기의 9회로 발동 수.
4. D3 KCL에서 F 성분 미선언 포트의 정의 가능성(회로 해석 -- 공동분석 몫).
5. W3 목표 HZ 출력·S-OS1 해소가 O-108 문언 범위 안인지(오케스트레이터 확인).
6. 엔진 search 패키지 전 파일 전수(머리말만 본 파일 밖은 미확인).
