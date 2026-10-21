# interface card: 20261021-it2c-icm-config

card IT-2c -- 측정 구성. test 작성 주체는 소스를 보지 않고 이 문서와 공통 문서 `docs/02-design/specs/20261021-it2-common.md`의 '창 규칙'·'정의 불능 code' 절만 쓴다(DEC-38 -- 본문 코드 없음). 정본 문장 = design 41 v1.12.3(`41:n`). `E/` = `skills/analog-gmid-design/gmid_engine/`. 쓰기 경로 = `E/tests/**`(agent 정의의 옛 `assets/tests/**`가 아니다).

## 관찰 가능한 계약

| 모듈 | 심볼 | 시그니처 |
|---|---|---|
| `gmid_engine.metrics.ss_nodal` | `*` | 신규 모듈: 블록 `ss_nodal_system`, 상수 `SS_NODAL_WRITER` |
| `gmid_engine.metrics.icm_config` | `*` | 신규 모듈: 블록 `icm_config_window`, `def kvl_sensitivity(nodal, drive, closure)`, 상수 `ICM_CONFIG_WRITER` |
| `gmid_engine.metrics.aux_types` | `IcmConfig` | IcmConfig(config, inverting_port, tied_ports, transfer, undefined) |
| `gmid_engine.metrics.aux_types` | `NodalSystem` | NodalSystem(nodes, fixed, g, factor) |

### 필드(graph) -- writer 하나

| 필드 | 값 | writer |
|---|---|---|
| `graph.ss_nodal` | `NodalSystem`, `g`·`factor` 모든 ndarray `flags.writeable is False` | `ss_nodal` |
| `node.dc_window_cfg` | `Window`(입력 포트마다, 모든 측정 구성; 구성 None이면 항목 없음; 자기 측정 실패 `Window(None, None, 0, input_status="unmeasured")`; 커널 `unsettled` 이어받기(평가점 전체)·`f_component_undeclared` 이어받기, definitional 우선) | `icm_config` |
| `graph.icm_config` | `IcmConfig`; `config` ∈ {`"declared_feedback"`, `"follower_beta1"`, `"as_is_single_input"`, None}; `transfer` 출력 전용 | `icm_config` |

### 되먹임 선언 세 상태 대조(T-FB)

`ss_evaluate` 키워드 `noise_decl`의 `.feedback`: tuple(되먹임 소자 있음) / `()`(소자 없음 = β=1 선언) / `None`(결정 대기·거부·미전달). 기대 갈래는 design 41 4.7-3b (1)과 사용자 결정 O-68 (2)(DC 성분 없는 되먹임·미선언의 측정 구성)에서 손으로 읽어 정한다. `None`을 '선언 없음 = 정상'으로 다루는 결과가 나오면 red.

### 단언 금지

`NodalSystem.factor` 내부 배열 값, `input_version` 문자열 값(같음·다름만), 분해능 수치 자체, `IcmConfig.transfer`의 resolution 수치, `IcmWindow.model_error_ref`(None만), S3 색인 내부, `RunCounters` 행 타입 이름.

## test 목록(위치 제안 -- 규칙 H 1:1, 이름 접두 `test_it2c_`)

| id | 위치 | 내용(정본) | oracle | base |
|---|---|---|---|---|
| T-L8 | `tests/metrics/test_icm_config.py` | 41:811(v1.12.5) (a)~(e), S-OS1·S-OS2 fail-closed, (b) = (b1) 용량만 선언 단일 출력 toy → `config is None` + `icm_config_feedback_no_dc` 하나·`node.dc_window_cfg` 항목 없음, (b2) 저항 선언 단일 출력 toy → `config == "declared_feedback"`·선언 구성 창(손계산)(재동결 O-79/O-80)(M7 metric 쪽 단언은 IT-2d) | (손) | red |
| T-L10 | `tests/metrics/test_ss_nodal.py`·`test_icm_config.py` | 41:812(v1.12.5) (b)~(g)((a)는 감사 착수 실측 기록); (f) red 먼저 | (손)+(독립) | red |
| T-INH | `tests/metrics/test_icm_config.py` | 커널 `unsettled` → 평가점 모든 cfg 항목 `unsettled`; F 성분 미선언 → `f_component_undeclared`; 겹치면 definitional 우선 | (식) | red |
| T-RES | 같은 파일 | 반전 입력 후보 0·2·분해능 이하 → 세 code(분해능 수치 단언 금지, 충분히 작은/큰 전달 양 끝만), role 이름 맞바꿈 같은 `inverting_port` | (손) | red |
| T-FB | 같은 파일 | 되먹임 선언 세 상태(tuple·`()`·`None`)의 구성 갈래 = design 4.7-3b (1)·O-68 (2) 대조표(interface 아래) | (식) | red |

red 예상 목록 = 엔진 동작·엔진 트리 구조를 보는 test(green 유지 대상·하네스 자체 test 제외). 새 키워드 직접 호출 `TypeError`는 red로 세지 않는다. `-k` 식 충돌은 base·head `--collect-only` 수를 함께 보고(xrunf1b 3.3 상속).

## 판정 측정(audit)

I-1, I-2 G1·G2·G3·G6·G7, I-3 9회로 변화표(cfg 창 신설·offset 값 불변), I-4 G-10·WP-10, I-6, 착수 실측 C-1·C-2 기록(L10 (a)). (I-n 정의 = 공통 문서 interface 측정표.)
