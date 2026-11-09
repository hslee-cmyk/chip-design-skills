# design 40/41/42 v1.12.7 · IT-2c card 재동결 -- 독립 검증 + design↔계획 gap 분석(v1.12.5~v1.12.7 누적)

- 대상: `wt/design-it2c-o79`, `git diff ea605a02..54f22173`(커밋 `54f22173` 하나, 파일 7개, 47+/33-). base `ea605a02`는 master `e87092b3`(계획 gb v6.28) 병합입니다.
- 대조한 계획: gb v6.28 N3.8 589행(판정 문단·'차동 출력'·'지원 밖 원소'), N6.6 1515행 (8)(b1)~(b3)·(10)(a)(e)(f), 1519행 IT-2c (iii)(iv). 사용자 결정 O-79~O-86(`_drafts/user_decisions.md`).
- 대조한 오라클: design v0.3.10(`design-oracle-eo1` `72aad57c`) §7 481행, §18.1 1456행 (x)(xi), §19.2 1642·1643행, §19.6 F-15·F-16.
- 읽기만 했습니다(`git -C`·Python 줄 추출). 엔진 코드는 인용을 확인하는 데만 열었습니다.
- **재검증(둘째 커밋 `8258af89`, O-87 (1))은 맨 아래 §14입니다. 지금 판정은 §14가 정본입니다.**

## 0. 판정

**88/100입니다. 필수 2건(MF-1·MF-2), 권고 5건, 사용자 확인 3건입니다.**

- 직전 판(v1.12.6)에서 지적한 MF-A·S-FB1·R1~R5·R7·R8은 모두 해소됐습니다. R6은 선택 항목이라 그대로 남겼습니다.
- 41:812 L10 (a)는 계획 (10)(a) 새 문언과 항목마다 같습니다.
- 그러나 41:734의 차동 출력 결합에 결함이 둘 있습니다.
  - 판정 함수 서명에 출력 인자가 없습니다(MF-2).
  - `MOS_KINDS` 예외가 계획 (10)(f) '지원 kind 상수 참조 0'과 어긋납니다(MF-1).
- IT-2c가 차동 출력의 판정을 맡은 것은 계획이 S-OS2 card에 둔 일을 앞당긴 범위 확대입니다. 사용자 확인이 필요합니다.

## 1. v1.12.6 지적 해소

| 지적 | v1.12.7 자리 | 판정 |
|---|---|---|
| MF-A `noise_plan` 2 갈래 | interface '절단 넷 공개 경로 대조'의 2행, T-L10, spec '기존 test 확장', common 288행 ('base 먼저 green') | 해소 |
| S-FB1 | 41:812 (a)가 계획 (10)(a) 새 문언으로 바뀜. 멈춤 블록은 41·spec·interface·common에서 사라지고 '해소' 기록과 옛 재동결 줄에만 남음 | 해소 |
| R1 code 이름·test 경로 | `icm_config_feedback_element_unsupported`(계획이 정함, O-85 (3)), '합성 스냅샷으로 블록 호출' | 해소 |
| R2 `device.unsupported` READS | 41:731 READS·734 (다), (10)(f) 여섯 | 해소. 다만 `MOS_KINDS` 예외가 남음 → MF-1 |
| R3 `()` → `follower_beta1`(KVL 고정 포함) | interface T-FB `()` 행 | 해소. 작성자 근거가 맞습니다: 41:734 (3)이 '스칼라 하나로 닫는다(follower: u = V_out(v_x·x + v_u·u))'라고 적고, 계획 (8)(d)가 'follower 행 V_out = x', 744 (1)이 'β = 1 기본 표기는 `follower_beta1`에서'라고 적습니다. 고임피던스 (2)와 KVL 고정 (3)의 닫음은 모두 follower입니다 |
| R4 `__code__` 계수 | 41:812 (a)(ii) | 해소 |
| R5 export grep 0은 증거 아님 | 41:812 (a)(i), interface | 해소 |
| R6 이름 조회 두 자리 | 바뀐 것 없음 | 선택 항목이라 결함 아님 |
| R7 42 판 건너뜀 설명 | 42 머리 | 해소 |
| R8 공개 경로 대조표 | interface 새 표 | 해소 |

## 2. 41:734 핵심 검증

### 2.1 지원 밖 원소

- (다)는 S1 `device.unsupported`(writer `s1_structure`, `s1_structure.py:69·79` 실측 `put("device", "unsupported", …)`)가 있는 원소가 하나라도 있으면 None을 냅니다. kind 목록 대조는 지웠습니다. 계획 589행 '지원 밖 원소'와 같습니다.
- **남은 것(MF-1)**: (나)는 MOS를 'kind ∈ `MOS_KINDS`(`s1_values.py:27`)'로 고르고, L10 (i)는 '`icm_config.py`에 `MOS_KINDS` **외** 지원 kind 목록 대조 0'이라고 예외를 둡니다.
  - 계획 (10)(f)는 '`git grep`으로 `icm_config.py`의 **지원 kind 상수 참조 0**'이고 예외가 없습니다. `MOS_KINDS`는 `s1_values`의 지원 경계 상수입니다(CONTRACT 154: MOS kind ∉ {nmos, pmos} → unsupported).
  - 고칠 길: 지원 밖 원소는 (다)에서 이미 None으로 끝나므로, 남은 원소에서 MOS는 `device.pins`에 gate 단자가 있는 원소로 고를 수 있습니다(`s1_structure.py:65` `MOS_TERMINAL_NAMES` 꼴). kind 상수 없이 계획 문언을 그대로 지킵니다.
  - design에서 이렇게 고치는 것을 권합니다. 고치지 않으려면 계획 (10)(f)에 예외 한 구절이 필요합니다.

### 2.2 차동 출력의 결합(DV-21)

- 계획 589행: '두 출력의 판정이 같을 때만 그 판정을 쓴다. 갈리면 판정 정의 불능(이름은 design)'. design: 출력마다 한 번씩 부르고, 같으면 그 판정, 갈리면 `icm_config_feedback_outputs_split`. 정의는 같습니다.
- 갈래 순서 ① 지원 밖 → ② 갈림 → ③ 같음 → S-OS2 fail-closed. ①②는 판정 단계(계획 '순서': 측정 구성 선택 전)이므로 ③보다 앞서는 것이 맞습니다. `undefined`는 code 하나입니다.
- **MF-2**: 서명이 `_dc_feedback_reaches(view, cut_nets) -> bool | None`이고, (마)는 '출발 = 출력 넷(`node.port_direction == "output"`)에서 BFS'입니다.
  - 출력이 둘이면 이 문언대로는 두 출력에서 함께 출발합니다. 그러면 판정이 하나뿐이라 **갈림을 원리적으로 잡을 수 없습니다.**
  - '출력마다 이 함수를 한 번씩 부르고'와 맞추려면 서명에 출력 넷을 넣고(예: `_dc_feedback_reaches(view, output, cut_nets)`), (마)를 '출발 = 그 출력 넷 하나'로 고쳐야 합니다. card(spec 30행, interface)도 같이 고칩니다.
  - 오라클은 '출력별 BFS, 출력 넷마다 한 번'(F-15)으로 이미 분명합니다.

### 2.3 L8 (d) 새 toy 손 검산

- **`outputs_split` toy**: design·card에 연결이 적혀 있지 않습니다('두 출력 DC 되먹임 판정이 갈리는 선언 차동 출력 toy').
  - 손 검산상 **꼬리를 공유하는 보통 차동쌍에서는 갈림이 생기지 않습니다.**
  - 예: Rf1(Vop–in−) 선언 + Cf2(Von–in+) 선언, 꼬리 넷 t. Vop → Rf1 → in−로 '있음'. Von → M2 d↔s → t → M1 d↔s → Vop → Rf1 → in−로도 '있음'. t는 레일이 아니라 경유가 허용되므로 두 판정이 같아집니다.
  - 갈리는 toy는 출력이 MOS d↔s로 레일에만 닿아야 합니다. 오라클 (x)가 이 꼴입니다(`o_b`는 M1 → gnd·M3 → vdd뿐). 같은 연결을 card에 적어야 test 작성 주체가 성립하지 않는 toy를 만들지 않습니다(N-1).
  - 이 toy가 커널 봉인을 통과하는지(`icm_config`는 봉인 뒤에 돎)는 미확인입니다. 통과하지 못하면 합성 스냅샷으로 블록을 부르는 경로가 필요합니다.
- **`element_unsupported` toy**: `device.unsupported` 원소 하나를 넣은 합성 스냅샷 → (다)에서 None → code 하나. 기대값이 성립합니다.

### 2.4 IT-2c가 차동 출력 판정을 맡는 것 -- 계획 범위인가

- 계획 v6.28이 이 판정을 놓는 자리는 다음과 같습니다.
  - N3.8 589행: '아래 차동 출력 회로의 측정 구성(O-67 (1))과 슬루 행이 읽는 DC 되먹임 판정은 이 결합된 판정이다'
  - (10)(f): '뒤 S-OS2 card는 이 함수를 부른다'
  - O-67 (5): 'IT-2는 … S-OS2 + fail-closed code로 시작'
  - IT-2c (iii)(iv)는 단일 출력 no_dc 판정과 L10 (a)만 다룹니다.
  - 차동 출력의 결합을 쓰는 곳은 S-OS2 card입니다.
- design v1.12.7은 IT-2c에서 차동 출력 + 선언에도 판정을 돌리고, 새 code 둘이 S-OS2 code보다 앞서 나올 수 있게 했습니다.
- 13회로 영향은 0입니다. 비지 않은 선언은 `current_reuse` 하나이고 두 출력 모두 '없음'(오라클 F-15, n7 §5 인용)이라 ③ S-OS2 code는 그대로입니다. `cnr_ota`의 `()`는 판정하지 않습니다.
- **판정: 계획에 명시된 범위 밖이며 경미한 범위 확대입니다(원래 취지와 다름).**
  - 이점: 결합 구현이 처음부터 한 자리에 있고 S-OS2 card는 부르기만 하면 됩니다. 오라클은 OP-5에서 같은 결합을 지금 만듭니다.
  - 비용: IT-2c test 늘어남(갈림 toy 연결 문제, §2.3).
  - **사용자 확인 U-1**: (가) 받아들인다(권고), (나) 계획대로 IT-2c는 차동 + 선언 → S-OS2 code만 두고 결합·`outputs_split`는 S-OS2 card로 미룬다.

## 3. 41:812 L10 (a) 새 측정 = 계획 (10)(a)

| 계획 (10)(a) 항목 | design 41:812 (a) | 판정 |
|---|---|---|
| (i) 함수 객체 참조(load) -- 호출·값 넘김·별칭, import 경로 무관, docstring 제외 | 같음 | 일치 |
| `tests/` 제외(O-86 N1) | '엔진 소스(`tests/` 제외)' | 일치 |
| 허용 넷 자리 | `spec_elements`·`spec_views`·`icm_config`·`noise_plan` | 일치 |
| 0 구역: `E/sizing` 전체·`ss_nodal`·`_helpers_nodal.py` | 같음(`E/metrics/ss_nodal.py` 경로 명시) | 일치 |
| (ii) 원 함수 `__code__`로 셈 | 같음 | 일치 |
| 구간 기준 = 원 함수 `__code__`(O-86 N4): `dc_writer_plan.fn`(`compute_block.py:118·122`), `run_kernel`·`seal_dc`는 평함수 | 같음. 실측: `writer_plan.py:128-129` `@compute_block`·`def dc_writer_plan`, `compute_block.py:118` `class ComputeBlock`·`:122` `self.fn = fn`, `kernel_run.py:65`, `seal.py:34` | 일치 |
| 측정 입력 = 13회로 + (8)(b) toy, reuse 없는 실행 | '13회로 + L8 (b) 선언 되먹임 toy, graph reuse 없는 실행(새 입력 버전)' | 일치 |
| 양성 대조 (가) 구간 밖 ≥ 1, (나) 구간 안 red 변형 > 0, 둘 다 필수 | 같음 | 일치 |
| (iii) 의미 판정 = (e) 손계산 | '(iii) 의미 판정 = 아래 (e)' | 일치(인용 있음) |
| 다른 모듈로 옮기는 게이밍 기각 | 같음 | 일치 |
| IT-2c (iv): 41 L10 (a)와 card 측정 행을 새 문언으로 | 41:812, spec 80행대 C-1 측정 행('옛 IT-0 LC 꼴은 이 card 판정에 쓰지 않는다'), interface T-L10, common 75행 | 일치 |

## 4. 옛 이름 정책

`icm_config_feedback_source_unsupported`는 다음 자리에만 남습니다: 41:17(상태 사슬), 41:734·744('옛 이름' 표시), common 13·14행(옛 재동결 기록), common 86행('옛'), 40 1곳(머리 사슬). 규범 문장(갈래·code 목록·test 기대)은 모두 새 이름입니다. v1.12.6 이름은 코드에 한 번도 들어간 적이 없어 지울 대상 코드도 없습니다. **받아들일 수 있습니다.** 다만 '옛 이름'이라는 표시가 정의처럼 읽히지 않도록 744 (2) 목록 안의 괄호 주석은 history로 옮기는 것이 깔끔합니다(N-4, 경미).

## 5. card 재동결

| 항목 | 실측 | 판정 |
|---|---|---|
| 41 줄 수 | base·HEAD 모두 1992줄. 811 = L8, 812 = L10 | '줄 추가 없음'이 맞음 |
| 인용 다시 재기 | `s1_structure.py:56-57·64-65·69·74-75·79·82`, `compute_block.py:118·122`, `writer_plan.py:129`, `kernel_run.py:65`, `seal.py:34`, `test_noise_plan.py:22`, CONTRACT 154·394 | 전부 일치 |
| 바뀐 범위 | O-85 (1)(2)(3)·O-86 M1·N1~N4, v1.12.6 검증 MF-A·R1~R5·R7·R8만 | 승인 범위 안 |
| IT-2d 24행 | 판 표시 v1.12.7, '새 code 둘도 같은 M7 경로' | 맞음(M7은 code를 나열하지 않으므로 계약 변화 없음) |
| 오라클 대응 인용 | 41·card에서 오라클 이름을 쓰지 않음(엔진 이름만) | 문제없음 |

## 6. graph 단일 정본(별도 항목)

| 검사 | 실측 | 판정 |
|---|---|---|
| 새 field | 0. 결과는 `config` None + `undefined` code로만 남음 | 통과 |
| writer | `icm_config` 그대로 | 통과 |
| cache·memo·sctx 슬롯·EvalResult 칸·`IcmConfig` 값 칸 | 0. 출력별 판정 결과를 담는 칸 없음 | 통과 |
| 지원 밖 판정 | `device.unsupported` READS, kind 목록 대조 삭제 | 통과 |
| MOS 식별 | `MOS_KINDS` 상수 참조. 같은 경계의 둘째 사용이며 계획 (10)(f) 0 조건과 어긋남 | **MF-1** |
| 결합 규칙 | 결합은 `icm_config` 한 자리. S-OS2 card는 부르기만 함('둘째 구현 금지') | 통과 |
| 재계산 | 출력마다 O(N) BFS. 계획 승인 예외 | 통과 |
| 절단 넷 규칙 | 순수 함수 하나(v1.12.6 그대로) | 통과 |

## 7. gap 표(계획 O-79~O-86 → design·card, v1.12.5~v1.12.7 누적)

| 계획 문장(결정) | design·card 자리 | 판정 |
|---|---|---|
| N3.8 단일 출력 + DC 되먹임 없음 = 정의 불능, 이름 design, 0개, 계획부터(O-79) | 41:734 갈래, 744 (2) `icm_config_feedback_no_dc` | 일치 |
| N6.6 IT-2c (i)(ii) code 추가·L8 (b) 기대(O-80 R1) | 41:744 (2)·811 (b1)(b2) | 일치 |
| `config` 값 집합 그대로(O-80 R1) | 41:732·744 (1) | 일치 |
| 단일 입력이면 `as_is_single_input` 먼저(O-80 R2) | 41:734 | 일치 |
| card L8 인용 41:811(O-80 R3) | card 전부 41:811(v1.12.7) | 일치 |
| (8)(b1)·(10)(e) 정렬(O-81 (1)) | 41:811 (b1), 812 (e) R·Rf∥Cf | 일치 |
| 경로 판정 = 방향 의존 그래프(O-81 (2)·O-82) | 41:734 (나)~(바) | 일치(출력 인자는 MF-2) |
| 엣지·제외 | 41:734 (나) `dc_nets` − current_source, MOS g→d·g→s | 일치(MOS 식별은 MF-1) |
| 경유 금지·끝점 | 41:734 (라)(마) | 일치 |
| 순서(구성 선택 전, T_p 안 읽음) | 41:734 | 일치 |
| 계산 자리 하나·레지스트리·S-OS2는 부름(O-82) | 41:734, 812 (i) | 일치 |
| (8)(b2)(b3) | 41:811 | 일치 |
| 절단 넷 순수 함수 하나, 래퍼 없음, 호출 넷(O-83 R-M1) | 41:734, 812 (i), spec 파일 범위 | 일치 |
| IT-2c (iii) 순수 함수 분리·`_input_side` 대체·동작 동일성 0·1·2(O-83 R-N1) | 41:812 (i), interface 대조표, MF-A 2행 | 일치 |
| O-83 N4 공통 게이트 입력 = '있음' | 정의대로이고 design 문장 없음 | 정보(오라클은 toy (vii)) |
| O-84 IT-1 소비자 표·40 §6-8 | v1.12.6에서 반영 | 일치 |
| 차동 출력: 같을 때만, 갈리면 정의 불능, 이름 design, 0개(O-85 (1)·O-86 N3) | 41:734 '차동 출력의 결합' `icm_config_feedback_outputs_split` | 정의는 일치. **위치는 IT-2c(계획은 S-OS2 card)** → U-1. 서명 → MF-2 |
| (10)(a) 새 문언(O-85 (2)·O-86 M1·N1·N4) | 41:812 (a) | 일치(§3) |
| IT-2c (iv) S-FB1 → 새 문언(O-86 N2) | 41:812, spec, interface, common | 일치 |
| 지원 밖 원소 = `device.unsupported`, 이름 `icm_config_feedback_element_unsupported`, kind 상수 참조 0(O-85 (3)) | 41:731·734 (다)·744·812 (i) | 부분: `MOS_KINDS` 예외 → MF-1 |
| (10)(f) READS 여섯 | 41:731, 812 (i), spec | 일치 |

## 8. 오라클 대응

| 계획 정의 | 엔진(v1.12.7) | 오라클(v0.3.10) | 판정 |
|---|---|---|---|
| 차동 출력 갈림 = 판정 정의 불능(gb v6.28 N3.8 '차동 출력') | code `icm_config_feedback_outputs_split`(definitional), 출력마다 판정(서명은 MF-2) | `dc_feedback_judgment_undefined` `why = differential_split`, 출력별 BFS, `present`·`absent` | 같은 정의를 각자의 어휘로 표현함. 오라클 §19.2 1643행의 엔진 이름 칸이 '미확인·승인 대기'라 v1.12.7 이름으로 채워야 함(오라클 몫, N-5) |
| 지원 밖 원소 = 판정 정의 불능(gb v6.28 N3.8 '지원 밖 원소') | `device.unsupported` 원소 → `icm_config_feedback_element_unsupported` | `/sources` voltage → `why = element_unsupported`(나머지 kind는 스키마·`descriptor_kind_undeclared`가 먼저 막음) | 같은 경계. 1642행 '미확인'을 해소해야 함(N-5) |
| 갈래 순서 | ① 지원 밖 ② 갈림 ③ (IT-2c) S-OS2 | 판정 전 검사(지원 밖) → 결합 → 갈래 | 같은 순서 |
| 갈림 toy | 연결 미명시(N-1) | (x) o_b가 레일에만 닿음, (xi) CMFB 저항 대조 | 오라클이 더 구체적. 엔진 card가 같은 연결을 쓰기를 권함 |

**판정: 두 design은 같은 계획 정의를 표현합니다.** 엔진의 MF-2(출력 인자)를 고쳐야 그 동치가 구현 수준에서도 성립합니다.

## 9. 필수

- **MF-1**: 41:734 (나)의 MOS 식별을 kind 상수 없이 바꿉니다(`device.pins`의 gate 단자로). L10 (i)의 '`MOS_KINDS` 외' 예외를 지우고 계획 (10)(f) '지원 kind 상수 참조 0'과 맞춥니다. 고치지 않으려면 계획 예외 한 구절과 사용자 확인이 필요합니다.
- **MF-2**: 판정 함수 서명에 출력 넷을 넣고(예: `_dc_feedback_reaches(view, output, cut_nets)`), (마) '출발 = 그 출력 넷 하나'로 고칩니다. spec 30행대와 interface에도 반영합니다. 지금 문언대로면 두 출력에서 함께 출발해 갈림을 잡지 못합니다.

## 10. 권고

- N-1: L8 (d) `outputs_split` toy의 연결을 적습니다. 꼬리를 공유하는 차동쌍은 d↔s 경로로 두 출력이 이어져 갈리지 않습니다. 오라클 (x)와 같은 꼴(한 출력이 MOS d↔s로 레일에만 닿음)과 (xi) 대조를 씁니다. 봉인 통과가 어려우면 합성 스냅샷 경로를 명시합니다.
- N-2(계획 정보): '차동 출력 갈림'은 꼬리 공유 차동쌍에서는 정의상 거의 생기지 않습니다(d↔s 양방향). 계획이 말하는 '해당 0개'와 맞으며 결함은 아닙니다. 오라클 (xi)와 같은 맥락입니다.
- N-3: interface `()` 행에 'S-OS2(차동 출력 + `()`)는 판정하지 않고 O-68 (2) 갈래(IT-2c에서는 S-OS2 code)'를 한 구절 덧붙이면 대조표가 완결됩니다.
- N-4: 744 (2) 목록 안의 '옛 이름' 괄호 주석은 history로 옮깁니다(경미).
- N-5(오라클 몫): §19.2 1642·1643행의 엔진 이름 칸 '미확인·승인 대기'를 v1.12.7 이름으로 채웁니다.

## 11. 사용자 확인이 필요한 것(승인 때)

1. **U-1**: IT-2c가 차동 출력의 판정 결합과 `icm_config_feedback_outputs_split`(및 차동에서 `element_unsupported`가 먼저 나오는 것)을 맡는 범위 확대입니다. 계획은 이 일을 S-OS2 card에 둡니다. 원래 취지와 다르고 13회로 영향은 0입니다. (가) 받아들임(권고) / (나) S-OS2 card로 미룸.
2. **U-2**: MF-1을 design에서 고치지 않고 `MOS_KINDS` 예외를 두려면 계획 (10)(f)를 개정해야 합니다. design 정정을 권하며, 그러면 이 확인은 필요 없습니다.
3. **U-3**: design 40/41/42 v1.12.5~v1.12.7 누적판과 IT-2c·IT-2d·it2-common card 재동결의 승인(MF-1·MF-2 반영 뒤).
- 정보: 새 code 이름 `icm_config_feedback_outputs_split`는 계획이 design에 맡긴 것이라 확인 대상이 아닙니다.

## 12. 미확인

- V-1: 갈림 toy(오라클 (x) 꼴)가 엔진 커널 봉인과 S0 출력 구조 분류를 통과하는지 실행하지 않았습니다.
- V-2: `current_reuse` 두 출력 판정 '없음'은 오라클 F-15·n7 §5를 인용했고 다시 재지 않았습니다.
- V-3: 오라클 design v0.3.10 자체의 검증 상태('독립 검증 대기')는 이번 범위 밖입니다.

## 13. 승인 준비

**MF-1·MF-2를 고치고 U-1이 확인되면 승인할 수 있습니다.** 고칠 범위는 41:734·812 몇 구절과 card 두 곳 정도로 작습니다. L10 (a)(S-FB1 해소)는 그대로 승인할 수 있는 상태입니다.

## 14. 재검증 -- 둘째 커밋 `8258af89`(`git diff 54f22173..8258af89`, 파일 7개, 19+/19-)

기준은 사용자 결정 O-87 (1)입니다: '계획대로. IT-2c는 차동 출력 + 선언이면 S-OS2 code로 fail-closed. 두 출력 판정 결합과 `icm_config_feedback_outputs_split`은 S-OS2 일반형 card 몫. 단일 출력 경로 판정(MF-2 출력 인자 서명)은 IT-2c에 남김.'

### 14.1 판정

**95/100입니다. 남은 필수는 0건입니다.** 사용자 승인(U-3)을 받을 준비가 됐습니다. 권고 2건(R-a·R-b)은 승인 전이든 code 착수 때든 넣으면 됩니다.

### 14.2 점검 결과

| 항목 | 실측 | 판정 |
|---|---|---|
| (1) MF-1 MOS 식별 | 41:734 (나): `device.pins`에 gate 단자 이름 `MOS_GATE` = `"g"`(`s1_values.py:37-40` 실측 `MOS_DRAIN = "d"`·`MOS_GATE = "g"`·`MOS_SOURCE = "s"`·`MOS_TERMINAL_NAMES`, 쓰기 `s1_structure.py:65` 실측)가 있는 원소. 2단자는 `"t0"`·`"t1"`(`authoring/topology_model.py:20` 실측). L10 (i): '지원 kind 상수 참조 0(`MOS_KINDS`·`SUPPORTED_PASSIVE_KINDS`·`SUPPORTED_SOURCE_KINDS` 모두, 예외 없음)'. interface·spec도 같음 | **해소.** 단자 이름 상수는 '지원 kind 상수'가 아닙니다. 단자 어휘이고 지원 경계(CONTRACT 154)와 무관하므로 계획 (10)(f) 위반이 아닙니다. (다) 판정 뒤라 남은 원소는 지원 원소뿐이어서 gate 단자 유무로 MOS를 고르는 것이 정확합니다 |
| (1′) `MOS_GATE` 비공개 문제 | `gmid_engine.graph.__all__`에는 `MOS_TERMINAL_NAMES`만 있습니다(`graph/__init__.py:95·271`). 구조 규칙 C(3)(`tests/structure/README.md:41`)는 다른 하위 패키지 import를 `from gmid_engine.graph import <__all__ 이름>`만 허용합니다. 그래서 `icm_config.py`(metrics)가 `MOS_GATE`를 직접 import하면 규칙 C가 FAIL합니다. 이미 `metrics/dc_metrics.py:28`·`metrics/metrics_aux.py:22`는 `MOS_TERMINAL_NAMES`를 공개 import합니다 | **design 필수는 아닙니다.** gate 단자의 정체(`"g"`)는 바뀌지 않고, card 파일 범위 안에서 지킬 길(`MOS_TERMINAL_NAMES`에서 gate 원소를 얻음)이 있기 때문입니다. 다만 design 문언이 `MOS_GATE`라는 이름을 적고 있어, code 작성자가 '`graph/__init__.py` export 추가(파일 범위 밖)'와 '공개 튜플 사용' 사이에서 as-built 판단을 해야 합니다. 그래서 한 구절 권고 **R-a**로 둡니다 |
| (2) MF-2 서명 | 41:731·734 (마): `_dc_feedback_reaches(view, output, cut_nets) -> bool \| None`, '출발 = 인자 `output` 넷 하나'. spec·interface·L10 (i)('서명에 출력 넷 인자 하나')도 같음 | **해소.** 출력 하나에서만 출발합니다 |
| (3) U-1 철회 | `outputs_split`이 남은 자리를 실측했습니다: 41:17(상태 사슬), 41:734('차동 출력 결합은 S-OS2 일반형 card 몫 … 이름 예약, IT-2c는 쓰지 않음'), 40:12(머리)·40:556('S-OS2 일반형 card 몫 -- O-87 (1)'), 42:229(같은 뜻), common 14(옛 O-85/O-86 재동결 기록)·15(O-87 재동결 기록). IT-2c 갈래 순서·L8 (d) toy·744 (2) code 목록·common 86 code 목록·T-L8·spec '거부해야 할 입력'·IT-2d 24행에서는 모두 빠졌습니다 | **완료.** 남은 것은 상태·history·'S-OS2 card 몫' 표시뿐입니다 |
| (3′) IT-2c 갈래 순서 | 41:734 'IT-2c 갈래 순서': 차동 출력 + 비지 않은 선언 → **먼저** S-OS2 `icm_config_differential_output_structure`(판정을 부르지 않음). 단일 출력 + 비지 않은 선언 → ① 지원 밖 → `element_unsupported` ② 경로 판정 False → `no_dc` ③ True → 구성 선택. spec·interface T-FB 차동 줄도 같음 | **맞음.** 계획 (10)(f)·O-67 (5)와 같습니다. 차동 + 지원 밖 원소도 S-OS2 code가 먼저인데, 판정을 부르지 않으므로 정합합니다 |
| (4) N-3 | interface T-FB `()` 행: '차동 출력 + `()`도 판정하지 않음 -- O-68 (2) 갈래, IT-2c에서는 S-OS2 code' | 반영 |
| (4) N-4 | 744 (2)의 '옛 이름' 괄호를 지웠고, 41:17 둘째 커밋 기록으로 옮겼습니다 | 반영 |
| (4) N-1 | 갈림 toy는 S-OS2 card가 오라클 (x)(xi) 꼴로 쓴다고 41:734에 적혀 있습니다 | 반영(자리 이동) |
| (5) card 재동결 범위 | common 15행 재동결 기록. 바뀐 문장은 모두 O-87 (1)·MF-1·MF-2·N-1·N-3·N-4 몫입니다 | 승인 범위 안 |
| (5) 인용 다시 재기 | 41 HEAD 1992줄(줄 추가 없음), 811 = L8, 812 = L10. `s1_values.py:37-40`, `s1_structure.py:65`, `topology_model.py:20` 실측 일치 | 일치 |

### 14.3 graph 단일 정본(재검증)

| 검사 | 판정 |
|---|---|
| 새 field·cache·memo·sctx 슬롯·EvalResult 칸·`IcmConfig` 값 칸 | 0, 통과 |
| writer | `icm_config` 그대로, 통과 |
| 지원 밖 판정 | `device.unsupported` READS만, 통과 |
| MOS 식별 | `device.pins` 단자 이름(S1 필드 값의 어휘), kind 상수 0, 통과(MF-1 해소) |
| 차동 결합 | IT-2c에 구현 없음. S-OS2 card 하나가 맡음(둘째 구현 없음), 통과 |
| 재계산 | 단일 출력 O(N) BFS 한 번, 계획 승인 예외, 통과 |

### 14.4 누적 gap 판정(v1.12.5 → v1.12.7 둘째 커밋, 계획 v6.28·O-79~O-87)

§7 표의 행이 모두 '일치'가 됐습니다. 바뀐 행은 다음 셋입니다.

| 계획 문장(결정) | 자리 | 판정 |
|---|---|---|
| 차동 출력 결합(O-85 (1)·O-86 N3) + 위치(O-87 (1): S-OS2 card) | 41:734 'S-OS2 일반형 card 몫', IT-2c 차동 = S-OS2 code | 일치 |
| 지원 밖 원소·kind 상수 참조 0(O-85 (3)) | 41:734 (나)(다)·812 (i) | 일치(MF-1 해소) |
| 경로 판정 출발점(O-81 (2)·O-82 '출력 넷(차동이면 출력마다)') | 41:734 (마) `output` 인자 | 일치(MF-2 해소) |

- 초과 항목: 41:734가 S-OS2 card용으로 이름 `icm_config_feedback_outputs_split`을 '예약'해 둡니다. 계획이 이름을 design에 맡겼으므로 결함은 아닙니다. 확정은 S-OS2 card의 design에서 하면 됩니다(정보).
- 누락: 없습니다.

### 14.5 권고

- **R-a**: 41:734 (나)에 '단자 이름은 `gmid_engine.graph` 공개 `MOS_TERMINAL_NAMES`에서 얻는다(구조 규칙 C -- `MOS_GATE`는 `__all__` 밖)'를 한 구절 넣습니다. 그러면 code 작성자가 파일 범위 밖(`graph/__init__.py`) 변경과 공개 튜플 사용 사이에서 판단할 일이 없어집니다.
- **R-b**(오라클 몫, 옛 N-5 갱신): 오라클 §19.2 1643행의 엔진 이름 칸은 '`icm_config_feedback_outputs_split` -- S-OS2 일반형 card 몫(IT-2c는 S-OS2 code)'으로 채웁니다. 1642행은 `icm_config_feedback_element_unsupported`(IT-2c, 단일 출력)로 채웁니다.

### 14.6 오라클 대응(갱신)

- 정의 동치는 그대로입니다.
- 시점이 다릅니다. 오라클은 OP-5에서 차동 결합을 지금 구현합니다. 엔진은 S-OS2 card에서 구현합니다(O-87 (1)).
- 그 사이 차동 + 선언 회로에서 엔진은 S-OS2 code를 내고, 오라클은 결합 판정 뒤 (c) 등을 냅니다. 지금은 비교가 '정의 경계 불일치'가 아니라 '엔진 미구현 갈래'로 기록돼야 합니다.
- 해당 회로는 13회로 중 `current_reuse` 하나이고 두 출력 모두 '없음'입니다.

### 14.7 사용자 확인(갱신)

- U-1: O-87 (1)로 닫혔습니다.
- U-2: MF-1이 design에서 해소돼 필요 없습니다.
- **U-3만 남습니다**: design 40/41/42 v1.12.5~v1.12.7(둘째 커밋 포함) 누적판과 IT-2c·IT-2d·it2-common card 재동결의 승인입니다.

### 14.8 미확인

- 갈림 toy와 봉인 통과 문제는 S-OS2 card로 옮겨져 이 card 범위 밖이 됐습니다.
- `current_reuse` 판정은 여전히 인용값입니다(V-2).
