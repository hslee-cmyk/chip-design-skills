# IT-2 선행 조건과 C-3(되먹임 선언 자리) 분석 -- 읽기 전용 (master 468e6e73, 2026-10-21)

`E` = `chip-design-skills/skills/analog-gmid-design/gmid_engine`, `P` = `docs/01-plan/features/gain-budget-gmid-sizing.plan.md`,
`D41` = `docs/02-design/features/gain-budget-gmid-sizing.41-gain-budget.design.md`, `D40` = 같은 폴더 `.40-engine.design.md`.
IT-2 card = `wt/spec-it2/docs/02-design/specs/20261021-it2-window-writers.spec.md` (브랜치 `spec/it2` 04d68f0f, master 미병합).

---

## Q1. C-3 -- `icm_config` 가 spec 되먹임 선언을 받는 자리

### 1. 실측 사실

| # | 사실 | 근거 |
|---|---|---|
| F1 | spec 로드: `human.feedback` -> `element_value_declaration` -> `_feedback`. 결과는 이름순 tuple(빈 tuple = 되먹임 수동소자 없음, β=1), `PendingMark`, 또는 거부 None | `E/authoring/spec_elements.py:1-24, :118-173`, `E/authoring/spec_load.py:104-106, :148` |
| F2 | `Spec` 칸 `feedback`과 지문 `feedback_fp` | `E/authoring/spec_model.py:265, :310` |
| F3 | **graph 필드가 이미 있다**: `graph/s1v: noise_input_cells`. writer는 `noise_decl` 하나(`@compute_block`)이고 값은 `NoiseDecl(feedback, sampling_caps, input_cells)`. `feedback`은 spec feedback tuple이고, PendingMark나 거부이면 None | `E/search/noise_decl.py:33-43`, `E/search/s0_fields.py:6, :23, :30, :37`, `E/metrics/noise_types.py:23-28`, D40 543행(S0 행, v1.9.1 D7) |
| F4 | 이 블록을 부르는 곳은 하나다. `_s0_blocks`가 `spec.feedback`을 tuple일 때만 넘기고, 아니면 None을 넘긴다. spec feedback이 엔진에 들어오는 유일한 길이다 | `E/search/search_context.py:184` |
| F5 | `build_search_context`는 S0 블록을 돈 base로 `dc = dataclasses.replace(dc_ctx, base=base)`를 만든다. 그래서 **탐색 중의 `KernelContext.base`는 `noise_input_cells`를 담은 S0 base다**. `run_kernel`은 parent가 없으면 `ctx.base`에서 출발한다 | `E/search/search_context.py:204-205`, `E/sizing/kernel_run.py:68-75` |
| F6 | `ss_evaluate`는 이미 키워드 `noise_decl`(`NoiseDecl`)을 받는다. 유일한 운영 호출자는 `kernel.py:136`이고, 그 값은 `sctx.noise_decl`, 곧 `self.dc.base.value("graph", S1V_KEY, "noise_input_cells")`다. 필드를 읽어 참조로 넘기는 것이고 다시 계산하지 않는다 | `E/metrics/ss_evaluate.py:81, :89-90, :103`, `E/search/kernel.py:136-138`, `E/search/search_context.py:76-77, :101-102` |
| F7 | `E/sizing/`·`E/pipeline/`에는 `feedback` 칸이 0개다. card의 사전 실측과 같다. `DcInputs`·`KernelContext`에도 없다. 커널 계획 블록은 spec 선언을 **extras로 투영**해 받는다. 예: `dc_writer_plan(base, target_nets, input_dc_declared, …)`에서 `input_dc_declared = inputs.input_dc_v is not None` | `E/sizing/kernel_context.py:85-86`, `E/sizing/writer_plan.py:130-152` |
| F8 | S0 필드 값을 ss 층 블록에 extras로 넘기는 선례가 있다. `area_decl`(`graph/kernel: passive_area_decl`) -> `metrics_dc` extras, `structure`(`graph/s1v: metric_structure`) -> `metrics_aux` 인자, `noise_decl` -> `noise_devices`. D41 4.7-3b도 `fixed_values`·`resistor_values`(S0 필드)를 extras로 둔다 | `E/metrics/ss_evaluate.py:103-111`, D41 731행 |
| F9 | 루프 절단 `input_terminal_nets`는 authoring 안(`spec_elements`·`spec_views`)에서만 쓰인다. 쓰기 계획·봉인점 망(`E/sizing`)에는 import가 0개다. S-3 착수 실측의 사전 근거이고, 판정은 검증자가 다시 잰다 | grep `_feedback_cuts\|input_terminal_nets` |

### 2. design이 이미 허용한 것

- D41 731행(4.7-3b READS 문단): "extras = `dc_window_refine`과 같은 넷 … + **spec 되먹임 선언(`human.feedback.elements` 로드 결과, `E/authoring/spec_elements.py:118`)** -- 커널 컨텍스트에 그 값이 있는 자리는 착수 때 확인, 없으면 멈추고 보고". 전달 방식은 **extras**로 이미 정해져 있다. 열려 있는 것은 출처 자리뿐이다.
- D41 833행(4.7-9): 멈춤 조건 '커널 컨텍스트에 되먹임 선언 자리 없음'.
- IT-2 card C-7(162행): `icm_config` READS에 design 밖 필드가 필요해 보이면 멈춘다(계획부터).
- D40 543행: `noise_input_cells` = S0 필드이고 writer는 `noise_decl` 하나다. 소비자로는 잡음 경로만 적혀 있다.

### 3. 세 선택지 판정 (graph 단일 정본 규칙 1~6)

| 안 | 내용 | 규칙 점검 | 계획·design 변경 |
|---|---|---|---|
| **(b′) 권고** | `ss_evaluate`가 이미 받는 `noise_decl`(F6)의 `.feedback`을 `icm_config` extras로 넘긴다. 출처는 graph 필드 `graph/s1v: noise_input_cells`(writer `noise_decl` 하나)다. `kernel.py:136`이 그 필드를 읽어 넘기는 값이고, 새로 만드는 것이 없다 | 규칙 1: 둘째 생산자가 없다. spec feedback을 엔진에 싣는 곳은 여전히 `search_context.py:184` 하나다. 규칙 2: 새 cache·sctx 슬롯·EvalResult 칸이 없다. 규칙 3: 같은 정의(spec 되먹임 소자 이름)의 필드는 여전히 하나다. 규칙 4: 필드 값을 그대로 넘긴다(F8 선례와 같은 꼴). 값은 extras 지문으로 블록 입력 버전에 들어가므로 재사용 키가 맞다 | **없음**. D41 731행의 "extras = spec 되먹임 선언 로드 결과"를 그대로 따르고, "자리는 착수 때 확인"을 사실(F3~F6)로 채울 뿐이다. card의 C-3 줄을 '해소: 자리 = `ss_evaluate(noise_decl=…)` = `graph/s1v: noise_input_cells`'로 고치면 된다(오케스트레이터) |
| (a) | `icm_config` READS에 `("graph", "noise_input_cells")`를 더하고 `NoiseDecl.feedback`을 읽는다 | 규칙 1의 'READS로 읽는다' 문언에 가장 가깝다. 다만 필드에 `input_cells`·`sampling_caps`가 함께 있어 입력 버전이 관계없는 칸에도 묶인다(S0 상수라 실제 재계산은 0). child 스냅샷이 이 필드를 가지려면 4.7-3c `derive_child`의 keep(= base writer)이 같은 card 안에서 먼저 서야 한다 | **design 변경 필요**: D41 4.7-3b READS 목록, D40 543행 소비자 열. 그다음 design-validator와 사용자 승인을 거친다. card C-7에 따라 그 전까지 멈춤 |
| (c) | 새 S0/S1 필드(예: `graph.feedback_decl`, writer 하나) | 같은 정의의 양이 `NoiseDecl.feedback`에 이미 있어 **규칙 3 위반**이다. 피하려면 `noise_decl`이 새 필드를 READS하도록 다시 써야 하는데, IT-2 범위 밖 리팩터다 | 계획 N3.3 S0 표와 D40 §2.4.8 개정 -> 사용자 승인. 권고하지 않음 |

### 4. 권고: (b′)

- 권고 근거: design이 정한 전달 방식(extras)과 출처 정본(기존 graph 필드)이 둘 다 이미 있다. 사본·새 슬롯·새 필드가 없다. 계획·design·사용자 결정이 필요 없다.
- 구현 주의(code 주체 브리핑과 test interface에 넣을 것. **판단이 아니라 design 문언의 적용 확인**):
  1. 세 상태를 구분한다. `NoiseDecl.feedback`은 tuple(소자 있음), `()`(소자 없음 = β=1 선언), `None`(결정 대기·거부·`noise_decl` 미전달) 셋이다. D41 4.7-3b "(1) 선언이 있으면 선언이 정한다"의 '선언'에 `()`가 드는지는 O-67 (1) "DC 성분이 없거나 선언이 없으면 follower"로 읽으면 결과가 같다(follower). 갈래 code나 사유가 달라지는지는 **design 문언을 대조해야 하는 항목**이다. 다르면 멈추고 보고한다.
  2. `ss_evaluate(noise_decl=None)` 기본값 경로는 test에서만 쓰인다. 운영 경로에서 이 경로는 결정 대기와 같은 None 갈래로 간다. 조용히 '선언 없음 = 정상'으로 바꾸지 않는다(fail-closed는 design 갈래를 따른다).
  3. `ss_evaluate` 안에서 `ctx.base.value("graph", S1V_KEY, "noise_input_cells")`를 직접 읽지 않는다. 투영 밖에서 읽는 것이라 입력 버전에서 빠진다. 반드시 extras로 넘긴다.
- 원래 취지와 다른 점: 없음. 731행이 정한 extras 방식이고, 출처만 확정한다.

---

## Q2. IT-2 선행 조건 현황

### (i) IT-1

| 항목 | 상태 | 근거 |
|---|---|---|
| 계획 card | N6.5(v6.16 승인 O-14 (2), 병합 f2852c36) | P 1350- |
| design | D41 **4.7-1**(쓰기 계획 개정, 범위 1~5, 다중 입력 뿌리 정지)이 v1.12.3에 있다. **사용자 승인 O-67 (5)**("design 40/41/42 v1.12.3 승인, IT-2 구현 착수")로 함께 승인됐다. N6.5 순서 1의 design 정정 항목(F-IT4 test 위치, IT-Q1 (나) rule_branch 이름, IT-Q2 반영)이 4.7-1에 모두 반영됐는지는 **재대조가 필요하다**(IT-Q2 칸은 4.7-8a에서 '미측정') | D41 666-675행, `_drafts/user_decisions.md` 688행 |
| spec card | **없음**. `wt/*/docs/02-design/specs/`에 it1/it0 card 파일이 0개다. IT-2 card(`spec/it2`)는 IT-2a~d 분할만 있고 IT-1 몫은 없다 | ls |
| branch | `design/it1-41`은 f2852c36(계획 병합 시점)에 머물러 있고 master에 병합된 상태다. 구현 branch(`role/*/it1`, `integ/it*`)는 0개 | `git branch -a` |
| 코드 | 미구현. `writer_plan.py`에 `_TIE`·`input_tie`·`INPUT_GROUP_KEY`가 남아 있다(:76-77, :105, :213-214, :234) | grep |

### (ii) card 0 IT-0

- **계획이 요구하는 것**:
  - N6.5 순서 0: 검증자가 엔진 무변경 상태로 측정한다. base는 IT-1의 실제 base(card B 병합 master)다. 결과를 바꾸는 card가 먼저 병합되면 다시 잰다. 측정 항목은 library 9회로 as-built 대 §6.7-1a 모사의 M-I1~M-I7이다.
  - N6.6 완료 조건 (6): 커널 창 미수렴 발동률(되풀이 미수렴·tol 미정 평가 수 / 평가 수)과 **front가 빈 회로 수**를 **IT-2 착수 전에** 재고 기록해야 한다. 이 기록이 있어야 완료다.
  - N6.6 완료 조건 (10) (a): 루프 절단이 적용되지 않음을 착수 실측(순서 0)으로 잰다.
  - D41 4.7-8a 결과 칸 6개(M-I4 IT-Q2 판정, s_p 부호, 커널 창 상태 발동, 다중 뿌리·고립·F 성분 미선언 포트, front가 빈 회로 수, 출력 구조 분류 발동 9+4회로 및 S-OS1·S-OS2 발동 수)는 모두 **'미측정'**이다.
- **있는 것**: 없음. `.ai/verification/`에 IT-0 판정 기록이 0개이고 IT-0 card 파일도 없다.
- 주의: 미수렴 발동률, front 빈 회로, 출력 구조 분류 같은 칸은 IT-2 필드(`input_status`, `node.dc_output_structure`)가 아직 없는 as-built에서 재야 한다. **as-built에서 어떻게 잴지(모사 스크립트 정의)를 card 0 card가 정해야 한다**. design 4.7-8a는 칸만 정하고 측정 방법은 적지 않았다.

### (iii) 순서 정본

- N6.1 card 표 141행: `IT-1 + IT-2(같은 통합 병합) | N6.5·N6.6 | 선행 XRUN-F1 card B; SPICE 다리 선행 EO-1 | 착수 조건 card 0 IT-0`.
  - card B는 **병합됨**(138a6db3, d6bd02b1 판정 PASS).
  - EO-1은 design만 있다(`design/oracle-eo1` 3e4ee765, **master 미병합**). EO-1은 IT-1·IT-2의 **완료 판정(SPICE 다리) 선행**이고 착수·병합 선행이 아니다(N6.1 EO-1 행 "병합 선행이 아니다").
- N6.6 '순서'(P 1488): **IT-1과 같은 통합 병합**(O-19 (2)). IT-1 쓰기 계획 개정 위에 IT-2 test·code 커밋을 쌓고, 통합 병합 하나로 들어간다. 그 뒤가 HC-S다.
- 따라서 IT-2 구현 착수(O-67 (5) 승인)는 **IT-0 기록**과 **IT-1 커밋을 밑에 둔 통합 branch**를 전제로 한다. IT-2 card를 IT-1 없이 master 위에서 따로 구현하면 O-19 (2)와 다르다.

### 최소 다음 단계 (순서대로)

| # | 일 | 주체 | 사용자 승인 |
|---|---|---|---|
| 1 | IT-2 card C-3을 Q1 (b′)로 해소 표기(출처 = `ss_evaluate(noise_decl=…)` = `graph/s1v: noise_input_cells`, F3~F6 줄 인용)하고, 세 상태 대조 항목을 interface card에 넣는다 | 오케스트레이터 | 불요(design 731행 적용) |
| 2 | D41 4.7-1 대 계획 N6.5 순서 1(design 정정 항목) gap 대조. 빠진 것이 있으면 design 정정 -> design-validator | 오케스트레이터(+ gap 분석 agent) | 빠짐이 있을 때만 design 정정 승인 |
| 3 | **card 0 IT-0 spec card 작성**. base = 현재 master(card B 병합 뒤). 범위는 N6.5 M-I1~M-I7, N6.6 완료 조건 (6) 발동률·front 빈 회로, (10) (a) 루프 절단 미적용, D41 4.7-8a 6칸, D41 4.7-3b 착수 실측(구동 쌍 넷 ⊆ ac 접지 ∪ 입력 넷, 9회로+toy). as-built 측정 방법을 card에 정의한다 | 오케스트레이터 | 불요(계획 정의 범위). 방법 정의가 원래 취지와 다르면 보고 |
| 4 | IT-0 측정 실행과 판정 기록 `.ai/verification/<IT-0 id>/`. 4.7-8a 칸 채움 | 검증자(auditor) | 불요. 단 결과에 따라 아래 분기가 생긴다: M-I4 -> IT-Q2 (나)/(다)는 O-13이 이미 정한 규칙이라 기계적이다. S-OS1·S-OS2·다중 뿌리 발동이 0이 아니면 멈춤 갈래 발동이므로 **사용자에게 보고** |
| 5 | **IT-1 spec card + interface card 작성**(N6.5 순서 2~4, D41 4.7-1). IT-2 card(IT-2a~d)와 같은 통합 branch 계획(브랜치 이름, 커밋 순서 IT-1 test -> IT-1 code -> IT-2a… )을 적는다 | 오케스트레이터 | card 승인(통상 절차) |
| 6 | IT-1 red test(interface만 보고, 손계산 오라클 toy (a)(b)(c), 다중 뿌리 정지 red) | test | -- |
| 7 | IT-1 구현(범위 1~5, 소비자 표, CONTRACT) | code | -- |
| 8 | IT-2a~d test -> code를 같은 통합 branch 위에 차례로 쌓는다(C-3 해소본, S-OS1·S-OS2는 fail-closed로 시작) | test, code | 착수는 O-67 (5)로 승인됨. C-5(분해능 정의 함수 = 계획 v6.24 `plan/gb-v624`)는 **사용자 승인·병합 전**이라 그 부분은 막혀 있다 |
| 9 | 통합 병합본 판정: red->green, 9회로 변화표(IT-0 대비, IT-Q3 (가) 기준선 갱신 근거), 결정성, graph 정본 점검(G-8·G-10·소비자) | 검증자 | 기준선 갱신은 IT-Q3 (가)로 이미 결정됨. 변화표 보고 |
| 10 | 병합 | 오케스트레이터 | 사용자 병합 승인 |
| 11 | SPICE 다리 완료 판정은 EO-1 병합 뒤 | 검증자 | EO-1 card 쪽 승인 |

**막힘 요약**: IT-2 착수 전에 반드시 있어야 하는 것은 IT-0 기록(완료 조건 (6))과 IT-1 커밋을 밑에 둔 통합 branch(O-19 (2))다. C-3은 계획·design 변경 없이 풀린다. C-5(분해능 정의 함수)는 계획 v6.24 승인 대기라 IT-2c의 반전 입력 식별 일부를 막는다.
