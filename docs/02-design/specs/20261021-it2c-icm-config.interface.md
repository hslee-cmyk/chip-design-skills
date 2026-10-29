# interface card: 20261021-it2c-icm-config

> **[대체 표지 2026-10-29 -- 검증 10 병합 가능 판정, master `07964dfe`] 대체됨 -- 현행 계획 card IT-2c(계획 v6.38.4 N6.6 범위 1·6), 재동결 필요.** 이 판은 계획 v6.23~v6.28·design 41 v1.12.3~v1.12.7 동결본이다. 그 뒤 계획이 범위를 바꿨다: 측정 구성 = servo(v6.35 O-115 -- 반전 입력 식별 T_p·`inverting_port`·`tied_ports`·선언 되먹임 DC 판정·S-OS2 멈춤 갈래 삭제), 전도 행 R0·F 성분 함께 구동(v6.36 O-118), `graph.ss_circuit` writer 하나(v6.34.1), 커널 상태 이어받기 삭제(v6.34 O-109 D2), 출력 구조 분류 필드 `node.dc_output_structure` 삭제(v6.38.3 N6.35 E-09)·전도 행 건너뜀 문턱 = 행 단위 분해능(E-22). (θ 프레임 창 = KVL 순서 창(N6.35 E-13)은 IT-2c가 아니라 card WB-1 범위 3a-0·3a 몫이다 -- 2026-10-29 정정.) 재동결본 `card/it2c` `d95c8ff8`(계획 v6.37·design v1.14.1)도 v6.38.3 E-09·E-22 반영 전이다. 계획 v6.38.4: 착수 실측 = (a) servo 피벗 a_e·δA_num (b) 진짜 A = 0 대칭 사례 하나; 옛 (c) 오라클 vntol·reltol은 엔진 착수 조건에서 뺐다(`67e7b182`, 승인 O-173 S-1). 재동결 착수 = design v1.15.x 승인 뒤(master design 40·41 = v1.14.2, v1.15.x는 미승인). 재동결 때 지킬 것(O-178: `IcmWindow.model_error_ref`·ME-1 인용 등 e_m 칸 옮기지 않음, O-181: library 13·held-out 0 동안 A' 판정 정지)은 IT-2 공통 문서 표지와 같다. 아래 본문은 기록이며 현행 계획에 맞춰 덧대지 않는다(O-169). 구현 상태: 미구현.


card IT-2c -- 측정 구성. test 작성 주체는 소스를 보지 않고 이 문서와 공통 문서 `docs/02-design/specs/20261021-it2-common.md`의 '창 규칙'·'정의 불능 code' 절만 쓴다(DEC-38 -- 본문 코드 없음). 정본 문장 = design 41 v1.12.3(`41:n`). `E/` = `skills/analog-gmid-design/gmid_engine/`. 쓰기 경로 = `E/tests/**`(agent 정의의 옛 `assets/tests/**`가 아니다).

## 관찰 가능한 계약

| 모듈 | 심볼 | 시그니처 |
|---|---|---|
| `gmid_engine.metrics.ss_nodal` | `*` | 신규 모듈: 블록 `ss_nodal_system`, 상수 `SS_NODAL_WRITER` |
| `gmid_engine.metrics.icm_config` | `*` | 신규 모듈: 블록 `icm_config_window`, `def kvl_sensitivity(nodal, drive, closure)`, 상수 `ICM_CONFIG_WRITER` |
| `gmid_engine.metrics.aux_types` | `IcmConfig` | IcmConfig(config, inverting_port, tied_ports, transfer, undefined) |
| `gmid_engine.metrics.aux_types` | `NodalSystem` | NodalSystem(nodes, fixed, g, factor) |
| `gmid_engine.authoring` | `feedback_cut_nets` | `feedback_cut_nets(terminals, input_nets) -> tuple[str, ...]`(입력 포트 넷에 물린 단자 넷, 단자 순서·중복 유지; 길이 1 = 절단 넷 -- 41:734 (1) v1.12.6; `input_terminal_nets`·`_input_side`는 없음 -- 재동결 O-81~O-83) |

### 필드(graph) -- writer 하나

| 필드 | 값 | writer |
|---|---|---|
| `graph.ss_nodal` | `NodalSystem`, `g`·`factor` 모든 ndarray `flags.writeable is False` | `ss_nodal` |
| `node.dc_window_cfg` | `Window`(입력 포트마다, 모든 측정 구성; 구성 None이면 항목 없음; 자기 측정 실패 `Window(None, None, 0, input_status="unmeasured")`; 커널 `unsettled` 이어받기(평가점 전체)·`f_component_undeclared` 이어받기, definitional 우선) | `icm_config` |
| `graph.icm_config` | `IcmConfig`; `config` ∈ {`"declared_feedback"`, `"follower_beta1"`, `"as_is_single_input"`, None}; `transfer` 출력 전용 | `icm_config` |

### 되먹임 선언 세 상태 대조(T-FB)

`ss_evaluate` 키워드 `noise_decl`의 `.feedback`: tuple(되먹임 소자 있음) / `()`(소자 없음 = β=1 선언) / `None`(결정 대기·거부·미전달). 기대 갈래는 design 41 4.7-3b (1)과 사용자 결정 O-68 (2)(DC 성분 없는 되먹임·미선언의 측정 구성)에서 손으로 읽어 정한다. `None`을 '선언 없음 = 정상'으로 다루는 결과가 나오면 red.

대조표(재동결 O-81~O-83, 검증 N1 -- 41:734 (1) v1.12.6; 단일 출력·입력 둘):

| `.feedback` | 기대 갈래 |
|---|---|
| tuple, 출력→절단 넷 DC 되먹임 경로 있음(예 R 출력–in−) | `config == "declared_feedback"` |
| tuple, 경로 없음(예 용량만, Cf + Rb(in−–레일)) | `config is None`, `undefined` = `icm_config_feedback_no_dc` 하나 |
| `()` | `config == "follower_beta1"`(고임피던스 41:734 (2)·KVL 고정 (3) 모두 -- (3)의 닫음도 follower u = V_out; 재동결 O-85/O-86, 검증 R3), DC 되먹임 판정 안 함(`icm_config_feedback_no_dc`가 나오면 red); 차동 출력 + `()`도 판정하지 않음 -- O-68 (2) 갈래, IT-2c에서는 S-OS2 code(재동결 O-87, 검증 N-3) |
| `None` | 결정 대기 갈래(fail-closed; '선언 없음 = 정상'이면 red) |

차동 출력 + 비지 않은 선언(재동결 O-87, 41:734 (1) v1.12.7 둘째 커밋 'IT-2c 갈래 순서'): 판정을 부르지 않고 `icm_config_differential_output_structure`(S-OS2) 하나. 차동 출력 결합과 그 code는 S-OS2 일반형 card 몫이라 이 card에 toy·기대 없음(O-87 (1)).

### 절단 넷 공개 경로 대조(T-L10 (i), 재동결 O-85/O-86, 검증 R8·MF-A)

| 입력 넷 단자 수 | 로더(`spec_elements`·`default_views`) | `noise_plan` |
|---|---|---|
| 0 | `feedback_element_not_on_input` | `noise_feedback_cut_ambiguous` |
| 1 | 통과, `cuts` = (소자, 그 넷) | `NoisePlan("closed")`, `free_nets` ∋ 그 넷(`test_noise_plan.py:22`) |
| 2(두 입력 넷 사이 소자) | `feedback_cut_ambiguous` | `noise_feedback_cut_ambiguous`(MF-A -- 새 공개 경로 사례, base(옛 `_input_side`)에서 먼저 green) |

기대값은 옛 docstring 규칙과 손으로 읽은 단자에서 만든다. 동적 계수는 함수 `__code__`로 세고(이름 묶기 무관 -- 검증 R4), `gmid_engine.authoring` export 때문에 이름 문자열 grep이 0이 되는 것은 증거로 쓰지 않는다(검증 R5).

### 단언 금지

`NodalSystem.factor` 내부 배열 값, `input_version` 문자열 값(같음·다름만), 분해능 수치 자체, `IcmConfig.transfer`의 resolution 수치, `IcmWindow.model_error_ref`(None만), S3 색인 내부, `RunCounters` 행 타입 이름.

## test 목록(위치 제안 -- 규칙 H 1:1, 이름 접두 `test_it2c_`)

| id | 위치 | 내용(정본) | oracle | base |
|---|---|---|---|---|
| T-L8 | `tests/metrics/test_icm_config.py` | 41:811(v1.12.7) (a)~(e), (d) 끝 v1.12.7 -- `device.unsupported` 합성 스냅샷 → `icm_config_feedback_element_unsupported`(재동결 O-85/O-86; 차동 갈림 toy 삭제 -- 재동결 O-87), S-OS1·S-OS2 fail-closed, (b) = (b1) 용량만 선언 단일 출력 toy → `config is None` + `icm_config_feedback_no_dc` 하나·`inverting_port` = in−·`tied_ports` = ()·`node.dc_window_cfg` 항목 없음, (b2) R 출력–in− → `config == "declared_feedback"`·선언 구성 창(손계산), (b3) 경로 판정 red 변형 -- Cf + Rb(in−–레일)·R(in−–레일)만 → no_dc, T망(R2만 선언) → `declared_feedback`; R2 우선 toy(입력 하나 + 용량만) → `as_is_single_input`(재동결 O-79~O-83)(M7 metric 쪽·unmeasured 단언은 IT-2d) | (손) | red |
| T-L10 | `tests/metrics/test_ss_nodal.py`·`test_icm_config.py`·`tests/authoring/test__feedback_cuts.py`(기존 파일) | 41:812(v1.12.7) (b)~(g)·(i)((a)는 감사 착수 실측 기록 -- 41:812 (a) v1.12.7: (i) 함수 객체 참조(load) 정적 계수, `tests/` 제외, 네 자리만·`E/sizing`·`ss_nodal`·`_helpers_nodal.py` 0 (ii) `dc_writer_plan.fn.__code__`·`run_kernel`·`seal_dc` 구간의 `feedback_cut_nets.__code__` 호출 0, 13회로 + L8 (b) toy·reuse 없는 실행, 양성 대조 (가) 구간 밖 ≥ 1 (나) 구간 안 red 변형 > 0 (iii) (e) -- 재동결 O-85/O-86); (e) 저항 toy·Rf∥Cf toy 창 = 손계산; (f) red 먼저; (i) 술어 정의 1곳(서명에 출력 넷 인자 하나 -- 재동결 O-87, MF-2)·READS 일곱(`device.unsupported`·`device.element_class` 포함 -- 재동결 O-88)·`icm_config.py`의 지원 kind 상수 참조 0(`MOS_KINDS` 포함, 예외 없음 -- 재동결 O-87, MF-1; `ELEMENT_MOS`는 원소 분류 어휘라 해당 없음, `MOS_GATE` 직접 import 0 -- 재동결 O-88)·`feedback_cut_nets` 정의 1곳·호출 넷·옛 두 def 0(`git grep`), 동작 동일성 = 기존 공개 경로 test(`test__feedback_cuts.py`·`tests/metrics/test_noise_plan.py`) 그대로 green + `test_noise_plan.py`에 2 갈래 공개 경로 사례(두 입력 넷 사이 선언 소자 → `noise_feedback_cut_ambiguous`, base에서 먼저 green -- MF-A) + `feedback_cut_nets` 0·1·2 갈래 직접 단언(기대값 = 손으로 읽은 단자; 위 공개 경로 대조표)(재동결 O-81~O-86) | (손)+(독립) | red |
| T-INH | `tests/metrics/test_icm_config.py` | 커널 `unsettled` → 평가점 모든 cfg 항목 `unsettled`; F 성분 미선언 → `f_component_undeclared`; 겹치면 definitional 우선 | (식) | red |
| T-RES | 같은 파일 | 반전 입력 후보 0·2·분해능 이하 → 세 code(분해능 수치 단언 금지, 충분히 작은/큰 전달 양 끝만), role 이름 맞바꿈 같은 `inverting_port` | (손) | red |
| T-FB | 같은 파일 | 되먹임 선언 세 상태(tuple·`()`·`None`)의 구성 갈래 = design 4.7-3b (1)·O-68 (2) 대조표(위 네 행 + 차동 출력 줄 -- 재동결 O-81~O-86) | (식) | red |

red 예상 목록 = 엔진 동작·엔진 트리 구조를 보는 test(green 유지 대상·하네스 자체 test 제외). 새 키워드 직접 호출 `TypeError`는 red로 세지 않는다. `-k` 식 충돌은 base·head `--collect-only` 수를 함께 보고(xrunf1b 3.3 상속).

## 판정 측정(audit)

I-1, I-2 G1·G2·G3·G6·G7, I-3 9회로 변화표(cfg 창 신설·offset 값 불변), I-4 G-10·WP-10, I-6, 착수 실측 C-1·C-2 기록(L10 (a)). (I-n 정의 = 공통 문서 interface 측정표.)

## 변경 이력

- 2026-10-29 `cards/simplify`(검증 대기): 위 대체 표지만 더함 -- 본문 불변, 표지 전 원문 = `git show 07181524:docs/02-design/specs/20261021-it2c-icm-config.interface.md`.
- 2026-10-29 `cards/revise-1029`: 대체 표지 내용 개정(E-13 귀속 정정 = WB-1 범위 3a, v6.38.4 착수 실측 (c) 삭제 반영, 재동결 착수 조건·지킬 것, '검증 대기' → 병합 표기) -- 본문 불변, 고치기 전 원문 = `git show 052465ed:docs/02-design/specs/20261021-it2c-icm-config.interface.md`.
