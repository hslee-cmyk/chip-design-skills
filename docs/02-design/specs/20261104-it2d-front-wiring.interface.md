# interface card: 20261104-it2d-front-wiring

card IT-2d 재동결(계획 v6.38.8 N6.6 범위 2·3, 'IT-2d -- B77', 완료 (1)(2)(4)(8)(g)(12)(c)(13)). 옛 `20261021-it2d-refine-front`(다듬은 창·front 전용 블록)을 대체한다. 그 옛 이름 `RefinedWindow`·`WindowEnd`·`refine_front_windows`·`icm_front`·`metrics_icm_front`·`window_end_*`는 만들지 않는다.

test 작성 주체는 엔진 소스를 보지 않고 이 문서와 기존 test 하네스(`E/tests/**`)만 쓴다. `E/` = `skills/analog-gmid-design/gmid_engine/`. base = 통합 브랜치 IT-2c 병합 head. `graph.icm_config`·`node.dc_window_cfg`·`graph.ss_nodal`·`graph.ss_circuit` 계약 = `20261104-it2c-icm-config.interface.md`.

## 관찰 가능한 계약

### 공개 이름

| 모듈 | 심볼 | 서명 |
|---|---|---|
| `gmid_engine.metrics.icm_window` | `icm_window_metrics` | `icm_window_metrics(config, ports, input_dc) -> IcmWindow`, 순수 함수 |
| `gmid_engine.metrics.aux_types` | `IcmPort` | frozen `IcmPort(net, v, lo, hi, tol_v, missing)` |
| `gmid_engine.metrics.aux_types` | `IcmWindow` | frozen `IcmWindow(icmr_v, icm_margin_v, required_input_cm_v, window, v_icm, input_dc, icmr_resolution, margin_resolution, undefined)`. 칸 `model_error_ref`·`sources`·`criterion`·`config` 없음 |
| `gmid_engine.metrics.ls_swing` | `ls_swing` | `ls_swing(devices, rails, node_v, outputs, diff_outputs=False) -> SwingIcmr`. 인자 `inputs`·`input_dc_v` 없음 |

서명 불변: `metrics_aux`(블록), `ss_evaluate`, `find_front`. `SwingIcmr` 형식·`swing_icmr` 보고 키·분해능 칸 이름 불변.

### 세 metric 정의(손 판정 기준)

입력 = `graph.icm_config`의 V_cm 칸.

- `icm_margin_v` = min(`vcm0` − `vcm_lo`, `vcm_hi` − `vcm0`)
- `icmr_v` = `vcm_hi` − `vcm_lo`
- `required_input_cm_v` = `input_dc == "pending"`이면 (`vcm0`, `vcm_lo`, `vcm_hi`), `"declared"`면 None
- `input_dc` = 입력 DC 미선언(spec `engine`·`pending`)이면 `"pending"`.
- `window` = (`vcm_lo`, `vcm_hi`), `v_icm` = `vcm0`
- 예: `vcm0` 0.90, `vcm_lo` 0.34, `vcm_hi` 1.19, `missing` 모두 () → margin 0.29, icmr 0.85, required (0.90, 0.34, 1.19)
- `margin_resolution` = 첫 포트 `tol_v`, `icmr_resolution` = 2·`tol_v`, `tol_v` None이면 None
- `ports` = 입력 포트 모두, 순서 = (`node.dc_colour`, 정준 위치). `lo`·`hi`는 **보고 열 전용**으로 metric 산술에 쓰지 않는다

**정의 불능**(세 metric 값 None, metric 이름마다 `Undefined` 한 원소): 어느 포트든 `missing`이 있으면 그 code(`input_window_unmeasured`, category `numeric`, detail에 `("port", net)`). 구성 None이면 `graph.icm_config.undefined`의 code를 그대로 옮긴다(category `definitional`).

**판정**(O-215 **임시 결정 -- 번복 가능**): `icmr_v`·`icm_margin_v` 선언 제약은 위 값으로 판정한다. 영역 행 창만, 기능 기준 칸을 읽지 않는다. 미선언 = 정의 불능 아님.

### 합치기

`metrics_aux`가 `ls_swing` 출력 `SwingIcmr`에 위 값을 넣어 한 `SwingIcmr`로 만든다. `undefined` = 스윙 사유 + ICMR 사유.

### 영역 칸 relabel(`metric_registry()[m].signature.domain`)

| metric | domain |
|---|---|
| `offset_in_sigma_mv`, `offset_excess`, `offset_sys_mv`, `mirror_ratio_sigma_pct`, `swing_out_v`, `icmr_v`, `icm_margin_v` | `dc` |
| `ff_gm_ratio` | `ss` |

VB-1이 먼저 병합되었으면 `offset_sys_mv`는 red 대상에서 뺀다(지금 미병합).

### B77 결측 판정(`metrics_aux`)

- 결측 유무 = `SsCircuit.missing` ≠ ∅.
- 영역 = `MetricSignature.domain`만 읽는다. metric 이름 목록·분기 0.
- 영역 `dc`: `graph.ss_nodal`이 `Undefined`일 때만 `passive_value_undeclared`. 그 밖에는 결측 없는 회로와 같은 계산.
- 영역 `ss`: 결측이 하나라도 있으면 `passive_value_undeclared`.
- 전달 뷰 보고(`block_residual`·`nqs_ratio`·`ls_fields`·FF): 결측이 하나라도 있으면 내지 않는다.
- metric별 보고(`offset_contrib`·`swing_icmr`·`mirror_ratio`): 그 metric이 정의되면 함께 낸다.
- 새 code 0. `metrics_ss` 결측 처리 불변.

### 단언 금지

`input_version` 값, 분해능 절대값 밖의 내부 표현, S3 색인 내부, front 정렬 지문, 13회로 값(유보), DE-1 뒤 필드(`node.dc_window_def`는 없음).

## test 목록(접두 `test_it2d_`)

| id | 위치 | 내용 | oracle | base |
|---|---|---|---|---|
| T-IW | `tests/metrics/test_icm_window.py` | 위 정의·예시·정의 불능 우선순위. 음수 감도 정렬 뒤에도 V_cm 칸에서 낸 값 | (식) | red(`ImportError`, 신규 함수) |
| T-LS | `tests/metrics/test_ls_swing.py` | 새 서명, 입력 칸 기본값(`icmr_v`·`icm_margin_v` None, `window` (), `v_icm`·`required_input_cm_v` None, `input_dc` ""), 입력 없는 회로 `swing_out_v` 값 있음 | (식) | red |
| T-M1 | `tests/metrics/test_metrics_aux.py` | 입력 DC 선언 toy: `icm_margin_v`가 `graph.icm_config` V_cm에서 나온 손 값, `required_input_cm_v` None. 미선언 toy(`pending`, `engine` 변형 둘 다): 튜플 | (손) | red |
| T-M2 | 같은 파일 | 구성 None toy(`view_required` 등): 세 metric 같은 code, `definitional`. 측정 실패 toy: `input_window_unmeasured`, `numeric`, 제약 판정 불능 | (손) | red |
| T-M3 | `tests/metrics/test_metrics_aux.py`(AST·READS) | `icm_window_metrics`·`_icm_ports` 소스에 `lo`·`hi`를 피연산자로 쓰는 산술 0(`BinOp`, `sum`·`min`·`max`·`mean` 인자). `metrics_aux` READS ∋ `graph.icm_config`·`node.dc_window_cfg`·`node.dc_colour`, ∌ `node.dc_window` | (독립) | red |
| T-G2 | `tests/metrics/test_ls_swing.py` 또는 `tests/structure`(AST) | `ls_swing` 소스에 입력 창 계산 0. 비test 엔진 소스에 `node.dc_window_def`·`dc_window_def_refined`·`dc_window_refine`·`metrics_icm_front`·`refine_front_windows`·`icm_front` 정의 0. `saturation_window` 호출 자리 = `Circuit` 경유 커널·`icm_config`뿐 | (독립) | red |
| T-F | `tests/search/test_find_front.py` 또는 `tests/metrics/test_ss_evaluate.py` | 커널 `icm_margin_v`와 front·보고 `icm_margin_v`가 같은 값(같은 칸). 모든 측정 구성 toy(servo·as-is) | (손) | red |
| T-O215 | `tests/metrics/test_ss_evaluate.py` | 입력쌍 한쪽 차단이 먼저인 꼴 toy: `icmr_v` 제약 = 영역 행 창 값으로 판정, 기능 칸 없음, 정의 불능 아님 | (손) | red |
| T-B77a | `tests/metrics/test_metrics_aux.py` | 용량만 결측 toy. 전제: `missing` ≠ ∅이고 전부 비전도, 결측 밖 정의 불능 사유 없음. `dc` metric 전부 정의, 대조 실행(같은 θ·봉인점, 그 커패시터 값만 선언)과 비트 동일. `ss`(`ff_gm_ratio`, `metrics_ss` 요청) `passive_value_undeclared`. 전달 뷰 보고 없음. metric별 보고 있음 | (손) | red |
| T-B77b | 같은 파일 | 저항 결측 toy: `dc`·`ss` 모두 `passive_value_undeclared` | (손) | red |
| T-B77c | 같은 파일(AST)·`tests/metrics/test_registry.py` | 결측 판정 함수와 부르는 함수에 metric 이름 비교 0. `is_dc_conducting_passive` `metrics_aux` 호출 0. registry 영역 칸 표(metric 이름으로) | (독립) | red |
| T-B77d | `tests/structure` 또는 같은 파일 | 새 결측 code 상수 0 | (독립) | green 후보(base에도 0이면 red 목록 제외) |

### green·기준선 공통 규칙(test 작성자 빈칸 답, 2026-11-04)

- **base green**: 표의 base 칸이 red여도 사례가 base에서 green이면, 그 사례가 옛 동작과 새 동작 모두에 성립하는 회귀 보호인지 확인하고 test는 유지한다. 그 사례는 red 예상 목록에서 빼고 판정자에게 나열한다. 사례 전체가 green이라 새 동작을 가르지 못하면 그 id에 red 사례가 하나는 남아야 한다.
- **회귀 기준선 fixture**(`tests/integration/fixtures/*`, NFR-4 덤프): test 작성자는 고치지 않는다. 판정자가 code 병합본에서 재측정하고 원인 칸을 적으며, 값 변화표는 O-225 보류 표지로 둔다(A-39). 재측정 전 그 test 실패는 판정 전 상태로 보고하고 통과로 세지 않는다.
- **폐기**: 정의가 바뀌어 전제가 깨진 test는 고치지 않고 지우며, 판정 기록 근거에 `retired_tests`(이름·사유)로 적는다. 판정자가 그 목록을 확인한다.

## 고칠 기존 test(test 주체 몫, 근거 O-109·O-112·U-106, 약화 아님)

줄 = integ/it12 `b9351eac` 실측.

| 파일 | 줄 | 일 |
|---|---|---|
| `tests/metrics/test_registry.py` | `:24` `TABLE`, `:49` 등 `"ls"` 3건 | 영역 칸 |
| `tests/authoring/conftest.py` | `:90-110` `u5_design_signatures` | 영역 칸 |
| `tests/metrics/test_pending_metrics.py` | `:72, :79, :86, :149, :157, :164` | 영역 단언 |
| `tests/metrics/test_catalog.py` | `:52-54` | `mirror_ratio_sigma_pct` 영역 |
| `tests/metrics/test_aux_types.py` | `:39-40` | `SwingIcmr` 입력 칸 |
| `tests/metrics/test_ls_swing.py` | 호출 17건 | 새 서명, 입력 창 단언 삭제 |
| `tests/sizing/test_input_window.py` | `:396` 부근 '선언 입력' | 기대 = 창 있음 |
| `tests/integration/test_spec_library_load.py` `U5_METRICS` | -- | 실행으로 확인(영역 단언 없으면 대상 밖) |

## 판정 측정(audit)

| # | 측정 | 합격 |
|---|---|---|
| A1 | test, red = base assertion(T-IW 제외) | PASS |
| A2 | 전체 suite | IT-1 D-1 기준 |
| A3 | G1~G7 최종, G-10·WP-10 | PASS + GL-1 병합 뒤 base에서 `ratchet.new` 0(새 키·수 증가 0). `block_columns.py` 쪽 줄어든 키는 판정자가 줄임. 행 추가로 통과시키면 `criteria_weakened`. 이 card는 rule 파일을 고치지 않는다(`structure.json` diff 0, A-34) |
| A4 | gap 분석 design 41 §4.7 대 구현 ≥ 90 %, 42 D-IT2 | 독립 gap-detector |
| A5 | 13회로 값 변화표(원인 칸 B77 대 `ls_swing` 삭제·cfg 배선 분리), 용량만 결측 봉인점 수, `ff_gm_ratio` 표기 | **미완료(보류 다리)** |
| A6 | 연기 시험(통합 병합) | 예외 없이 끝남, 세 metric 경로 지남 |
