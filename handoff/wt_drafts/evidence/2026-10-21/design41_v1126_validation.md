# design 40/41/42 v1.12.6 · IT-2c/IT-1 card 재동결 -- 독립 검증 + design↔계획 gap 분석

- 대상: `wt/design-it2c-o79`, 브랜치 `design/it2c-o79`, `git diff 2e60f9c7..be892734`(커밋 하나 `be892734`, 파일 8개, 48+/31-)
- base `2e60f9c7` = master `8c2357bc` 병합. 계획은 gb v6.27(`dae968ec`)이고 사용자 결정은 O-81~O-84입니다.
- 읽기만 했습니다(`git -C`·grep·Python 줄 추출). 엔진 코드는 사실 확인용으로만 열었습니다. 작성자의 보고는 증거로 쓰지 않았습니다.

## 0. 판정

**86/100입니다. design 필수 1건(MF-A), 계획 몫 멈춤 1건(S-FB1), 권고 8건입니다.**

- 41:734 경로 판정 설계는 계획 N3.8 '선언 되먹임의 DC 되먹임 판정 -- 정의 하나'와 맞습니다. toy를 손으로 확인한 결과도 모두 맞았습니다.
- S-FB1은 측정 꼴 수준에서는 실재하는 충돌입니다. 의미(보호 대상) 수준에서는 충돌이 아닙니다. 계획 (10)(a)의 측정 문언을 고치면 풀리고, 실현할 수 있습니다(§4).
- 승인 가능 시점: S-FB1 계획 정정이 승인되고 MF-A를 card에 한 줄 넣으면 승인할 수 있습니다.

## 1. v1.12.5 지적의 해소

| 지적 | v1.12.6 자리 | 판정 |
|---|---|---|
| MF-1 L10 (e) 용량 toy 충돌 | 41:812 (e) = R toy·Rf∥Cf toy, 계획 (10)(e) 정렬(O-81 (1)) | 해소 |
| N1 T-FB 네 행 | interface T-FB 대조표 네 행 | 해소. 다만 `()` 행 문언이 애매함 → 권고 R3 |
| N2 kind 출처 | S1 READS 다섯(`device.kind`·`pins`·`dc_nets`·`node.is_rail`·`port_direction`) | 해소 |
| N3 code 순서·나머지 칸 | 41:734: 판정이 구성 선택 전이라 code 하나, `inverting_port` = 절단 넷 포트, `tied_ports` = (), `transfer` 빈 값 | 해소 |
| N4 R2 toy | 41:811 (b3) 끝 R2 우선 toy | 해소 |
| N5 IT-2d | IT-2d spec 24행: 판 표시 갱신, L8 (b1)·(d) M7 항목 추가 | 해소 |
| N6 40/42 | 40·42 v1.12.6, 40:556·42 D-IT2 행 | 해소 |
| N7 경로 판정 | 계획 v6.27 N3.8(O-81 (2)·O-82), 41:734 | 해소 |
| N8 계획 (8)(b) 문언 | 계획 (8)(b1)~(b3) | 해소 |
| N9 unmeasured 단언 | 41:811 (b1) | 해소 |

## 2. 41:734 경로 판정 설계

### 2.1 계획 대조

| 계획 N3.8(587행) | design 41:734 | 판정 |
|---|---|---|
| 엣지: DC 전도 원소 양방향, MOS d↔s 양방향, g→d·g→s 한 방향 | `device.dc_nets`가 있는 원소 중 kind ≠ `current_source`는 양방향, MOS는 `device.pins`의 gate→drain·gate→source 한 방향 | 일치 |
| 용량·이상 전류원은 엣지 아님(`dc_edges_unpruned`와 다른 점) | 용량은 `dc_nets` None이라 빠짐. `current_source`는 kind로 뺌 | 일치 |
| 이상 전압원 = 지원 밖, 판정 정의 불능 | 지원 kind 밖 원소가 있으면 None → `icm_config_feedback_source_unsupported` | 일치. 범위는 넓어짐 → 권고 R1 |
| 끝점 = 선언 절단 넷(순수 함수) | (라) `feedback_cut_nets`가 낸 길이 1 튜플의 넷 | 일치 |
| 경유 금지 = 레일, 구동하는 다른 입력 포트 넷(끝점 예외) | `node.is_rail` 넷, 절단 넷 아닌 입력 포트 넷 | 일치 |
| 순서: 구조와 선언만 읽음, 구성 선택·T_p·시뮬레이터 호출 전 | '측정 구성 선택·T_p·어떤 풀이보다 먼저', 술어는 `config`·T_p를 읽지 않음. 단일 입력 → `as_is_single_input`이 먼저(O-80 R2, 계획 같은 문단) | 일치 |
| 계산 자리 하나 = `icm_config.py` 비공개 함수 하나 + 레지스트리 개념 행 | `_dc_feedback_reaches(view, cut_nets) -> bool \| None`, 레지스트리 행 둘(개념 행 + 순수 함수 행) | 일치 |
| 비용 O(N), 새 cache 없음 | (바) O(N) BFS, cache·memo 없음, graph reuse만 | 일치 |

### 2.2 `dc_nets`를 읽는 것이 정본인가

정본이 맞습니다. 이유는 다음과 같습니다.

- `device.dc_nets`는 S1 writer `s1_structure`가 `dc_edges_unpruned`로 채운 graph 필드입니다(`E/graph/s1_structure.py:80-82`). 엔진의 DC 전도 정의 하나(`dc_edges.py:11`·`:14-18`)가 그대로 담겨 있습니다.
  - MOS는 (d, s)입니다.
  - 수동소자는 `DC_CONDUCTING_PASSIVE_KINDS`(저항)만 들어갑니다.
  - 이상원은 전부 들어갑니다.
- kind 이름표를 icm_config에 다시 두면 같은 정의의 둘째 사본이 됩니다(규칙 3).
- 계획이 정한 차이(이상 전류원 제외)만 kind로 덧붙였습니다. 사본이 아니라 정의된 차이입니다.

### 2.3 손 검산

5T OTA 꼴의 DUT로 확인했습니다. M1·M2 차동쌍에서 in−는 M1 gate, 출력 = M2·M4 드레인입니다. M3·M4는 미러, M5는 꼬리입니다.

| toy | BFS(출력에서) | 기대 | 판정 |
|---|---|---|---|
| (b1) Cf 출력–in− | 출력 → M2 d↔s → 꼬리 → M1 d↔s → 미러 넷 → M3·M4 → VDD(금지). in−는 M1 gate뿐이라 들어오는 엣지가 없음 → False | no_dc | 일치 |
| (b2) R 출력–in− | 출력 → R → in− → True | `declared_feedback` | 일치 |
| (b3) Cf + Rb(in−–레일) | in−에 들어오는 엣지는 Rb뿐이고 그 반대 끝은 레일(경유 금지) → False | no_dc | 일치 |
| (b3) R(in−–레일)만 | 위와 같음 → False | no_dc | 일치 |
| (b3) T망: R1 출력–X, R2 X–in−(선언), R3 X–접지 | 출력 → R1 → X(레일 아님) → R2 → in− → True. R1·R3는 DUT 원소라 DUT DC 망 전체에 있음 | `declared_feedback` | 일치 |
| L10 (e) Rf∥Cf | Rf로 True | `declared_feedback` | 일치 |
| R2 toy: 입력 하나 + Cf | 판정 전에 `as_is_single_input` | `as_is_single_input` | 일치 |
| `()` | 판정 안 함(미선언 β=1) | follower 갈래 | 일치(계획 1512) |

## 3. 순수 함수 `feedback_cut_nets(terminals, input_nets) -> tuple`

- **반환 꼴**: 튜플(0/1/2)은 옛 `input_terminal_nets` 계약을 그대로 이어받습니다(`_feedback_cuts.py:4-6`). `spec_elements`에는 0(`feedback_element_not_on_input`)과 2(`feedback_cut_ambiguous`)의 구별이 필요하므로, 넷 하나나 None을 돌려주는 꼴로는 부족합니다. 계획의 '단자 넷 × 입력 포트 넷 집합 → 절단 넷'과도 어긋나지 않습니다. **원래 취지와 다르지 않습니다.**
- **옛 `_input_side`와의 동치**: 옛 함수의 `element.a != element.b` 검사(`noise_plan.py:31`)는 결과를 바꾸지 않습니다. a = b이고 그 넷이 입력이면 길이 2, 입력이 아니면 길이 0이어서, 어느 쪽이든 길이 1이 아닙니다. 새 함수의 '길이 1 아니면 `CODE_CUT_AMBIGUOUS`'와 같습니다.
- **호출 자리 넷·래퍼 없음**: `spec_elements.py:104`·`spec_views.py:101`·`noise_plan.py:48`의 현재 호출 줄이 실측과 일치합니다. 옛 두 def를 삭제하고 래퍼를 두지 않는 것은 O-83 R-M1과 같습니다.
  - 이름 조회(topology에서 소자 찾기)는 이제 두 호출부가 각자 합니다. 규칙의 사본은 아닙니다(조회일 뿐). → 권고 R6
- **동작 동일성 test 설계**: 옛 함수를 지우는 같은 변경에서 비교하려면 test에 옛 함수 사본이 필요합니다. 사본을 두지 않는 대안은 다음과 같고, 받아들일 수 있습니다.
  - (가) 공개 경로 test는 바꾸지 않고 base·head 둘 다 green(같은 입력 → 같은 출력)
  - (나) 순수 함수 0·1·2 직접 단언
- **단, 계획 IT-2c (iii)은 '옛 두 함수 … 0·1·2 갈래'를 요구합니다.** 현재 공개 경로 범위를 실측했습니다.
  - `input_terminal_nets`(로더): 0 ✓(`test_feedback_element_not_on_input`), 1 ✓, 2 ✓(`test_feedback_cut_ambiguous`)
  - `_input_side`(`test_noise_plan.py`): 1 ✓(`test_closed_frees…`), 0 ✓(CL, 41행), **2(두 입력 넷 사이 소자)는 없음**
  - `spec_views`의 0/2 갈래는 로더가 먼저 거부해서 공개 경로로는 닿지 않습니다(1만 있음).
  - → **MF-A**

## 4. S-FB1 분석(가장 중요)

### 4.1 (10)(a)의 원래 취지

- 출처는 O-58 S-3입니다. 선언 되먹임의 DC 망 = '선언 소자를 끊지 않은 봉인점 회로'(계획 587행)입니다.
- (10)(a)는 'spec 검사의 루프 절단(`spec_elements.py:19-22`, 7a L2)이 쓰기 계획·봉인점 DC 망에 적용되지 않음'을 잽니다. 보호 대상은 DC 망을 만드는 자리입니다.
- O-76 (2)가 측정 꼴을 정했습니다. '정적 검사는 호출 구문만(docstring 제외) + 동적 0회'입니다.
- IT-0 LC(`20261021-it0-baseline.spec.md:49`)는 다음 두 가지를 잽니다.
  - (i) `git grep "_feedback_cuts\|input_terminal_nets" -- E/sizing E/search E/metrics` = 0
  - (ii) `input_terminal_nets`를 관찰 래퍼로 감싼 뒤 `dc_writer_plan`·`run_kernel`·`seal_dc` 구간 호출 = 0
- 결과(history 1406행): 정적 1건(`noise_plan.py:6` docstring), 동적 0.

### 4.2 충돌은 실재하는가

- **측정 꼴 수준: 실재합니다.** (10)(f)는 `E/metrics`의 `icm_config`·`noise_plan`이 절단 넷 함수를 부르라고 요구합니다. (10)(a)가 그 함수(옛 이름의 후계)의 호출을 `E/metrics`에서 0으로 요구하면 둘은 함께 설 수 없습니다. 게다가 (10)(a) 문언의 대상 `input_terminal_nets`는 (10)(f)로 사라집니다.
- **의미 수준: 충돌이 아닙니다.**
  - `icm_config`는 절단 넷을 BFS 끝점과 반전 입력 이름으로만 씁니다. DC 망(`graph.ss_nodal` G)에는 선언 저항이 그대로 들어갑니다(41:738).
  - `noise_plan`은 잡음 계(ss 층)의 자유 노드를 정할 뿐이고 DC 망이 아닙니다. 그리고 **IT-0 때 이미 `E/metrics`에서 같은 규칙을 계산하고 있었습니다**(둘째 구현 `_input_side`). 그때 LC 정적 grep이 0이었던 이유는 이름이 달랐기 때문입니다. 옛 측정은 의미가 아니라 이름을 쟀습니다.
- **`icm_config`가 `run_kernel` 구간 안에서 도는가 -- 아닙니다(코드 배치로 실측).**
  - `run_kernel`(`E/sizing/kernel_run.py:65-101`) = `dc_currents`·`dc_lengths`·`dc_columns`·`dc_widths` → `seal_dc` 반환
  - `ss_evaluate`는 `E/search/kernel.py:136`에서 `size_and_seal`이 돌아온 **뒤** 봉인 점에서만 불립니다.
  - `icm_config`는 그 안(`ss_evaluate.py:101` 뒤, 41:730)에 있고, `noise_plan`은 `ss_metrics.py:412`에 있습니다. 둘 다 ss 층입니다.
  - `spec_elements`·`spec_views`는 로드 때 불립니다.
  - 따라서 동적 측정(구간 호출 0)은 바뀐 뒤에도 성립합니다.
- **관찰(미확인)**: IT-0 동적 측정은 모듈 속성 `_feedback_cuts.input_terminal_nets`를 감쌌습니다. 호출부는 `from ._feedback_cuts import input_terminal_nets`로 이름을 import 때 묶습니다(`spec_elements.py:28`·`spec_views.py:31`). 그래서 그 래퍼가 호출을 볼 수 없었을 가능성이 있습니다(측정이 공허함). 새 측정은 code object로 세야 합니다.

### 4.3 두 번째 선택지(grep에 걸리지 않는 모듈로 옮기기)는 정당한가

**측정 게이밍이므로 기각합니다.**

- 무엇을 하는지는 그대로 두고 측정 결과만 바꿉니다.
- 지금 design도 `gmid_engine.authoring` 공개 export를 둡니다. 그래서 `from gmid_engine.authoring import feedback_cut_nets`로 import하면 글자 그대로의 LC grep(`_feedback_cuts`)이 **우연히** 0이 됩니다. 계획 정정에서 '별칭·import 경로와 무관하게 호출 구문으로 센다'를 못 박아야 합니다.

### 4.4 권고 계획 문언(최소 변경, 취지 유지)

(10)(a) '판정:' 이하를 다음으로 바꿉니다.

> 판정: **DC 망을 만드는 자리에 루프 절단이 적용되지 않음**을 잰다 -- (i) 정적: 절단 넷 순수 함수(N3.8, 옛 `input_terminal_nets`·`_input_side`)의 호출 구문(별칭·import 경로와 무관, docstring·주석 제외 -- O-76 (2))은 (10)(f)의 넷 자리(`spec_elements`·`spec_views`·`icm_config`·`noise_plan`)에만 있고, `E/sizing` 전체와 봉인점 DC 망 조립 자리(`ss_nodal`·`E/metrics/_helpers_nodal.py`)에는 0 (ii) 동적: 그 함수의 호출 수(code object로 셈)가 `dc_writer_plan`·`run_kernel`·`seal_dc` 실행 구간에서 0 (iii) `icm_config`의 호출은 끝점 식별만 한다 -- 망이 절단되지 않았음은 (10)(e) 손계산 일치(선언 저항이 G에 있음)가 의미로 판정한다.

history에는 다음 한 줄을 남깁니다.

> IT-0 LC의 `E/metrics` 정적 0은 그때 `noise_plan`이 같은 규칙을 다른 이름(`_input_side`)으로 가지고 있어 통과한 것 -- 측정이 이름을 쟀다; O-83 R-M1이 구현을 하나로 모으면서 측정 꼴을 의미 기준으로 고침.

**실현 가능성**: 높습니다.

- (i) `git grep -n "feedback_cut_nets("`의 결과가 허용 파일 넷의 부분집합인지 봅니다. `E/sizing`·`ss_nodal.py`·`_helpers_nodal.py`는 0이어야 합니다.
- (ii) `sys.setprofile`(또는 `sys.monitoring`)로 `feedback_cut_nets.__code__` 호출을 셉니다. 이름 묶기와 무관하게 셀 수 있습니다.
- (iii) 이미 L10 (e)에 있습니다.
- 13회로에서 바뀌는 동작은 0입니다.

**원래 취지와 다른가**: 아닙니다. 보호 대상(DC 망이 절단되지 않음)은 그대로이고 대리 측정만 바뀝니다. 다만 사용자 결정 O-76 (2)의 측정 꼴을 바꾸는 것이므로 **사용자 승인이 필요**합니다.

## 5. 작성자 선택 중 원래 취지와 다를 수 있는 것

| 선택 | 판단 |
|---|---|
| code 이름 `icm_config_feedback_source_unsupported` | 계획은 '이상 전압원 → 정의 불능'만 말합니다. design은 '지원 kind 밖 원소 전부'(MOS·수동·이상원 kind)로 넓혔습니다. 이름의 'source'와 범위(인덕터 등 수동 kind 포함)가 맞지 않습니다. 운영 경로에서는 S1이 먼저 멈춰서 닿지 않습니다. **범위 확대(경미)로 보고합니다.** 이름을 `…_element_unsupported`로 바꾸거나 범위를 계획대로 줄이는 것을 권고합니다(R1) |
| 튜플 반환 | 취지와 같습니다(§3) |
| T-FB `()` 행을 (2)/(3)으로 일반화 | 계획 1512('`()` = 미선언 갈래')와 N3.8(KVL 고정도 follower 행 V_out = x)대로라면 두 구조 모두 `config == "follower_beta1"`입니다. 그런데 행 문언 '고임피던스 출력이면 follower_beta1'은 KVL 고정 쪽 값을 비워 둡니다. 취지와 다르지는 않지만 **애매합니다** → R3 |
| 동작 동일성 test 설계 | 사본 없이 base·head 공개 경로로 확인하는 방법은 받아들일 수 있습니다. 갈래 범위가 모자랍니다 → MF-A |
| 40이 v1.12.4에서 v1.12.6으로 건너뜀 | 40 머리에 '41 v1.12.5는 41만 바꿈'이라고 적혀 있습니다. 판 번호를 41에 맞춘 것이라 문제없습니다. 42는 건너뜀 설명이 없습니다 → R7(경미) |

## 6. card 재동결

| 항목 | 실측 | 판정 |
|---|---|---|
| 41 줄 | base·HEAD 모두 1992줄입니다. 734/738/744/811(L8)/812(L10)/672를 Python으로 추출해 확인했습니다 | '줄 추가 없음'이 맞습니다 |
| 코드 인용 | `s1_structure.py:56-57·64-65·74-75·82`(is_rail·port_direction / kind·pins / 수동·이상원 kind·pins / dc_nets), `s1_values.py:27-29`, `CONTRACT.md:394`, `noise_plan.py:28·48`, `spec_elements.py:104`, `spec_views.py:101`, `_feedback_cuts.py:11·4-6` | 전부 일치 |
| IT-2c interface·spec | 시그니처 행, T-FB 네 행, T-L8 (b1)~(b3)·R2, T-L10 (e)(i), 파일 범위, 거부 입력, S-FB1 멈춤 | O-81~O-83 범위 안 |
| it2-common | 재동결 기록 줄, L8/L10 행, code 목록, 시그니처 표, T-L8/T-L10 | 범위 안 |
| IT-2d 24행 | 판 표시, L8 (b1)·(d) M7 항목 | 범위 안(N5) |
| IT-1 spec 44-45행 | 소비자 열만 고침: `node.dc_writer`에서 `achievability` 삭제(41:672 `tie:` 등식 삭제), `device.dc_coord`의 `achievability`를 `theta_schema`로 바꿈. 실측: `theta_schema.py:62` READS에 `dc_coord`가 있음, `achievability.py:315`는 base에서 `dc_writer`를 읽고 IT-1에서 지워짐 | O-84 범위. 맞음 |
| 승인 밖 변경 | 없음 | 통과 |

## 7. graph 단일 정본(별도 항목)

| 검사 | 실측 | 판정 |
|---|---|---|
| 새 필드 | 0. 결과는 `IcmConfig.config`·`undefined`로만 남음 | 통과 |
| writer | `icm_config` 그대로 | 통과 |
| cache·memo·sctx 슬롯·EvalResult 칸·`IcmConfig` 값 칸 | 0 | 통과 |
| 투영 밖 읽기 | 0. S1 다섯 필드를 READS로 읽음(입력 버전에 듦), `ctx.base` 직접 읽기 0 | 통과 |
| DC 전도 정의 | `device.dc_nets`(정본 필드)를 읽음. kind 표 사본 없음 | 통과 |
| 절단 넷 규칙 | 구현 둘(`input_terminal_nets`·`_input_side`)이 하나(`feedback_cut_nets`)로 모임 | 통과(개선) |
| 지원 kind 판정 | (다)는 `s1_values` 상수 튜플로 '지원 밖'을 다시 판정함. 같은 값이 이미 S1 graph 필드 `device.unsupported`(writer `s1_structure`, `CONTRACT.md:154`)에 있음. **같은 양의 둘째 계산(경미)**입니다. 계획 READS 목록에 없어 design 단독으로는 못 바꿈 | 권고 R2(계획 한 줄) |
| 판정 재계산 | θ와 무관한 bool을 평가마다 O(N)으로 다시 계산함. 계획이 명시해 승인한 자리임('새 cache 없이 graph reuse') | 통과(승인 예외) |

## 8. gap 표(v6.27·O-81~O-84 → design·card)

| 계획 문장 | 자리 | 판정 |
|---|---|---|
| N3.8 DC 되먹임 정의(방향 의존 그래프, 출력 → 선언 절단 넷) | 41:734 (나)~(마) | 일치 |
| N3.8 절단 넷 = 순수 함수 하나, 래퍼 없음, 호출 넷 | 41:734 '절단 넷 순수 함수', spec 파일 범위 | 일치 |
| N3.8 엣지·제외(용량·이상 전류원) | 41:734 (나) | 일치 |
| N3.8 이상 전압원 = 판정 정의 불능 | 41:734 (다), 새 code | 일치. 범위 확대(R1) |
| N3.8 경유 금지 | 41:734 (마) | 일치 |
| N3.8 순서(구조·선언만, 구성 선택 전) | 41:734 | 일치 |
| N3.8 계산 자리 하나·레지스트리·S-OS2는 이 함수 호출 | 41:734 (S-OS2 '둘째 구현 금지'), L10 (i) | 일치 |
| N3.8 비용 O(N)·cache 0 | 41:734 (바) | 일치 |
| N3.8 단일 출력 + 없음 = 정의 불능, R2 먼저 | 41:734 갈래, 744 (2) | 일치 |
| N3.8 오라클 따로 구현·'정의 경계 불일치' | 범위 밖(oracle design) | 해당 없음 |
| (8)(b1) | 41:811 (b1) | 일치 |
| (8)(b2) R 출력–in− | 41:811 (b2) | 일치 |
| (8)(b3) 경로 판정 red 변형 셋 | 41:811 (b3) | 일치 |
| (10)(a) 측정 꼴 | 41:812 (a) 멈춤 S-FB1 | **계획 정정 대기**(§4) |
| (10)(e) R·Rf∥Cf toy | 41:812 (e) | 일치 |
| (10)(f) 술어 1곳·READS 다섯·새 필드 0·순수 함수 1곳·호출 넷·옛 def 0·레지스트리 | 41:812 (i) | 일치 |
| IT-2c (iii) code 이름·`config` 집합 그대로 | 41:734, 744 | 일치 |
| IT-2c (iii) L10 새 기호 (i) | 41:812 (i) | 일치 |
| IT-2c (iii)/O-83 R-N1 동작 동일성 test(0·1·2) | 41:812 (i), interface T-L10 | **부분**: `_input_side` 2 갈래가 빠짐(MF-A) |
| O-83 R-M1 래퍼 없음 | 41:734, (i) | 일치 |
| O-83 N4(공통 게이트 입력 DUT는 '있음') | design 언급 없음 | 정의대로라 따로 쓸 필요 없음(정보) |
| O-84 IT-1 소비자 표 정정 | IT-1 spec 44-45 | 일치 |
| O-84 design 40 §6-8 한 줄 | 40 diff `@@ -1610` | 일치 |

## 9. IT-1 영향

- IT-1 spec diff는 소비자 열 두 칸뿐입니다. 계약·test·기준·code 범위는 바뀌지 않았습니다.
- `role/audit/it1`(HEAD 근처 `bd468eaf`는 O-84 test 커밋들) 감사에 미치는 효과는 G6 '소비자 ≥ 1' 표 대조뿐입니다. 고친 표가 오히려 맞습니다(`achievability`는 IT-1 뒤 `dc_writer` 소비자가 아님).
- 감사가 옛 동결 card를 기준으로 쓰고 있다면 이 열만 새 판으로 읽으면 됩니다.
- 결론: 영향은 '소비자 표 정정'뿐입니다.

## 10. 필수

- **MF-A**(card 한 줄): 동작 동일성 test가 계획 IT-2c (iii) '옛 두 함수 … 0·1·2 갈래'를 채우도록 `tests/metrics/test_noise_plan.py`에 2 갈래 공개 경로 사례를 더합니다(두 입력 넷 사이 선언 소자 → `noise_feedback_cut_ambiguous`). **base에서 먼저 green**이어야 합니다(옛 `_input_side`로 통과하는지 확인). interface T-L10 (i)와 spec '기존 test 확장'에 적습니다.
- **S-FB1**(계획 몫, design은 올바르게 멈춤): §4.4 문언으로 (10)(a)를 정정하고 사용자 승인을 받습니다(O-76 (2) 측정 꼴 변경).

## 11. 권고

- R1: 새 code의 이름과 범위를 맞춥니다. `icm_config_feedback_element_unsupported`로 바꾸거나 범위를 이상 전압원으로 줄입니다. 그리고 이 갈래의 test 경로(운영 경로에서는 닿지 않으므로 합성 스냅샷으로 블록 호출)를 card에 적습니다.
- R2(계획 한 줄): (다)의 지원 판정은 S1 필드 `device.unsupported`를 READS로 읽게 합니다(같은 양의 둘째 계산 제거).
- R3: T-FB `()` 행을 '`config == "follower_beta1"`(고임피던스 (2)·KVL 고정 (3) 모두)'로 못 박습니다.
- R4: 동적 측정은 code object로 셉니다(§4.2 관찰). 이름 묶기 때문에 래퍼가 공허해지는 것을 피합니다.
- R5: `gmid_engine.authoring` export 때문에 글자 그대로의 grep이 우연히 0이 되는 일을 측정에 쓰지 않는다고 card에 한 줄 적습니다.
- R6: `spec_elements`·`spec_views`의 '이름 → 단자 넷' 조회가 두 자리에 생깁니다. 기존 조회 helper가 있으면 그것을 쓰고, 없으면 그대로 둬도 됩니다(규칙 사본은 아님).
- R7: 42 머리에 v1.12.5를 건너뛴 이유 한 줄을 적습니다.
- R8: interface T-L10 (i)에 '기대값 = 옛 docstring 규칙 + 손으로 읽은 단자'라고 이미 적혀 있습니다. 공개 경로 사례가 0/1/2 × (로더·`noise_plan`)를 덮는다는 대조표를 붙이면 감사가 쉬워집니다.

## 12. 미확인

- U1: IT-0 LC 동적 래퍼의 실제 구현(모듈 속성 패치인지)을 열지 않았습니다. 그래서 공허했을 가능성은 추정입니다.
- U2: 단일 입력 + 용량만 선언을 spec 검사가 받는지 실행하지 않았습니다(design도 미확인으로 표시함).
- U3: `spec_views` 0/2 갈래를 공개 경로로 닿게 하는 입력이 있는지(로더가 먼저 거부하는지) 실행으로 확인하지 않았습니다.
- U4: `role/audit/it1`이 기준으로 쓰는 card 판은 열지 않았습니다.
- U5: 동적 구간 호출 0은 코드 배치로 판단했고 실행하지 않았습니다.

## 13. 승인 준비

S-FB1 계획 정정(§4.4)이 승인되고 MF-A를 card에 반영하면 승인할 수 있습니다. R1·R3는 같은 재동결에 넣는 것을 권고합니다.
