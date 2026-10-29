# interface card: 20261021-it2d-refine-front

> **[대체 표지 2026-10-29 -- 검증 대기] 대체됨 -- 현행 계획 card IT-2d(계획 v6.38.3 N6.6 범위 2·3, 'IT-2d -- B77'), 재동결 필요.** 이 판의 범위(다듬은 창 `dc_window_refine`·끝 풀이·`refine_front_windows`·`metrics_icm_front`·`IcmPort`의 `tied_ports` 제외)는 계획 v6.34 사용자 결정 O-109 C1('측정 구성 창 = 선형 감도 끝 하나', 다듬은 창·front 전용 블록 없음)과 v6.35 O-115(`tied_ports` 삭제)로 대상이 없어졌다. 현행 IT-2d 범위 = front·보고가 `node.dc_window_cfg`를 읽는 배선, `ls_swing` 입력 창 계산 삭제·`metrics_aux` 배선(V_cm 칸 READS), B77 결측 판정 영역 분리·metric 영역 칸 relabel(v6.34.2 O-111·O-112)뿐이다. 아래 본문은 기록이며 현행 계획에 맞춰 덧대지 않는다(O-169). 구현 상태: 미구현.


card IT-2d -- 다듬은 창·front. test 작성 주체는 소스를 보지 않고 이 문서와 공통 문서 `docs/02-design/specs/20261021-it2-common.md`의 '창 규칙'·'정의 불능 code' 절만 쓴다(DEC-38 -- 본문 코드 없음). 정본 문장 = design 41 v1.12.3(`41:n`). `E/` = `skills/analog-gmid-design/gmid_engine/`. 쓰기 경로 = `E/tests/**`(agent 정의의 옛 `assets/tests/**`가 아니다).

## 관찰 가능한 계약

| 모듈 | 심볼 | 시그니처 |
|---|---|---|
| `gmid_engine.sizing.s2_values` | `RefinedWindow` | RefinedWindow(lo, hi, lo_end, hi_end, tol_v, criterion) |
| `gmid_engine.sizing.s2_values` | `WindowEnd` | WindowEnd(x, v, reason) |
| `gmid_engine.sizing.s2_values` | `DC_WINDOW_REFINE_WRITER` | 상수 `"dc_window_refine"` |
| `gmid_engine.sizing.s2_values` | `CRITERION_TOL_JUDGEMENT` | 상수 `"tol_judgement"` |
| `gmid_engine.sizing.s2_values` | `CRITERION_DEFINITION` | 상수 `"definition"` |
| `gmid_engine.sizing.s2_values` | `REASON_WINDOW_END_SOLVE_FAILED` | 상수 `"window_end_solve_failed"` |
| `gmid_engine.sizing.s2_values` | `REASON_WINDOW_END_K_MAX` | 상수 `"window_end_k_max_exhausted"` |
| `gmid_engine.sizing.s2_values` | `REASON_WINDOW_END_UNCONFIRMED` | 상수 `"window_end_saturation_unconfirmed"` |
| `gmid_engine.sizing.window_refine` | `*` | 신규 모듈: 블록 `refine_input_windows` |
| `gmid_engine.search.front_windows` | `*` | 신규 모듈: `def refine_front_windows(sctx, result) -> EvalResult` |
| `gmid_engine.metrics.icm_window` | `*` | 신규 모듈: `def icm_window_metrics(ports, input_dc, config_undefined=()) -> IcmWindow` |
| `gmid_engine.metrics.icm_front` | `*` | 신규 모듈: 블록 `icm_front`, 상수 `METRICS_ICM_FRONT_WRITER` |
| `gmid_engine.metrics.aux_types` | `IcmPort` | IcmPort(net, v, lo, hi, tol_v, missing) |
| `gmid_engine.metrics.aux_types` | `IcmWindow` | IcmWindow(icmr_v, icm_margin_v, required_input_cm_v, window, v_icm, input_dc, icmr_resolution, margin_resolution, undefined, model_error_ref, sources) |
| `gmid_engine.metrics.ls_swing` | `ls_swing` | def ls_swing(devices, rails, node_v, outputs, diff_outputs=False) -> SwingIcmr |
| `find_front 결과` | `perf `window_end_solves`` | 결과 칸 |

### 필드(graph) -- writer 하나

| 필드 | 값 | writer |
|---|---|---|
| `node.dc_window_def_refined` | `RefinedWindow`(`criterion == "tol_judgement"`); 쓰지 않는 포트 = F 성분 미선언·`kvl_fixed` 출력 또는 `as_is_single_input` 평가의 입력 포트 전부·출발 창 없음·출발 창 `unsettled`; 한 끝이라도 결측이면 `lo` = `hi` = None | `dc_window_refine` |
| `graph.metrics_icm_front` | {METRICS_KEY: `IcmWindow`} -- 출력 전용(EO-1 전) | `metrics_icm_front` |
| perf `window_end_solves` | 끝 풀이 수(실행 합) -- 출력 전용 | -- |

### 포트 집합 규칙(design 41 v1.12.4 gap G4 -- 780·789·794·811행)

세 metric(`icm_margin_v`·`required_input_cm_v`·`icmr_v`)은 커널(`metrics_aux`)과 front(`metrics_icm_front`) 모두 **측정 구성이 묶지 않은 입력 포트**만으로 낸다: `graph.icm_config.tied_ports`의 포트는 빼고, 묶인 포트가 없으면 입력 포트 전부. 단언: 되먹임 미선언 차동 입력·단일 출력 toy(follower 구성)에서 세 metric = 비반전 입력 창 하나로 낸 손계산 값(반전 입력을 포함하면 red).

### 단언 금지

`NodalSystem.factor` 내부 배열 값, `input_version` 문자열 값(같음·다름만), 분해능 수치 자체, `IcmConfig.transfer`의 resolution 수치, `IcmWindow.model_error_ref`(None만), S3 색인 내부, `RunCounters` 행 타입 이름.

## test 목록(위치 제안 -- 규칙 H 1:1, 이름 접두 `test_it2d_`)

| id | 위치 | 내용(정본) | oracle | base |
|---|---|---|---|---|
| T-K3 | `tests/search/test_front_windows.py` | 41:801 (a)~(d) | (독립) | red |
| T-R1·R2 | `tests/sizing/test_window_refine.py` | 41:802-803(주입 지점 둘만) | (손)+(식) | red(ImportError) |
| T-Pcde | 같은 파일 | 41:808 (c)(d)(e); P (a)(b) 다듬은 창 쪽 | (손)+(독립) | red |
| T-M1·W1 | `tests/metrics/test_icm_front.py`·`tests/search/test_front_windows.py` | 41:804-805 | (비교)+(손) | red |
| T-IW | `tests/metrics/test_icm_window.py` | 규칙·예시(0.28 / 0.83 / (0.90, 0.33, 1.18))·정의 불능 우선순위·M7 quantity(L10 (h)) | (식) | red(ImportError) |
| T-LS | `ls_swing` test | 새 서명, 입력 칸 기본값, 입력 포트 없는 회로 `swing_out_v` 값 있음·입력 두 metric만 `no_input_port` | (식) | red |
| T-D-m | `tests/metrics/test_icm_window.py` | `op_mismatch` `Window` → `input_window_operating_point_mismatch`(definitional) | (식) | red |
| T-L12 | `test_window_refine.py`·`test_icm_front.py`·`test_front_windows.py` | 41:813 (a) front 쪽·(b) metric·(c)·(d) | (손)+(독립) | red |
| T-G | `tests/structure`(또는 integration) | G1·G2·G6 최종 `git grep` 표(writer 자리·`front_cache` 0·사본 칸 부재·필드별 소비자 또는 출력 전용) | (독립) | red |

red 예상 목록 = 엔진 동작·엔진 트리 구조를 보는 test(green 유지 대상·하네스 자체 test 제외). 새 키워드 직접 호출 `TypeError`는 red로 세지 않는다. `-k` 식 충돌은 base·head `--collect-only` 수를 함께 보고(xrunf1b 3.3 상속).

## 판정 측정(audit)

I-1, I-2 G1~G7 최종, I-3 9회로 변화표(41:816 (1)~(7) 원인), I-4 G-10·WP-10·`kernel_calls` 불변, I-6, I-7, I-8 gap-detector(design 41 §4.7 ↔ 구현) ≥ 90 %·42 D-IT2·D-ICM. 이 판정 PASS 뒤 IT-1·IT-2 통합 병합본 전체 판정. (I-n 정의 = 공통 문서 interface 측정표.)

## 변경 이력

- 2026-10-29 `cards/simplify`(검증 대기): 위 대체 표지만 더함 -- 본문 불변, 표지 전 원문 = `git show 07181524:docs/02-design/specs/20261021-it2d-refine-front.interface.md`.
