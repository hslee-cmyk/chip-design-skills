# interface card: 20261021-it2b-kernel-window

> **[상태 표지 2026-10-29] 완료 이력** -- IT-2b 판정 PASS(`integ/it12:.ai/verification/20261021-it2b-kernel-window.json`, code `431d2e7b`), master 미병합. 이 master 사본은 판정 전 동결본이다(판정본 = `integ/it12`: `Window` 칸 다섯, helper 이동 없음, (S4-나) 확정, 동작점 불일치 단언은 card EO-1). 이 card 산출 가운데 `node.dc_output_structure`(와 그 writer)는 현행 IT-2c가 지우고(계획 v6.38.4 N6.6 범위 6·N6.35 E-09, O-109 D4), 입력 창 측정 되풀이 경로(`k_max`·`unmeasured`/`unsettled`)는 card WB-1 범위 3a가 KVL 순서 창으로 다시 쓴다(N6.35 E-13) -- 재작성 범위 기록이며 보존 근거가 아니다(원칙 8). 본문은 기록이며 덧대지 않는다(O-169).

card IT-2b -- 커널 창. test 작성 주체는 소스를 보지 않고 이 문서와 공통 문서 `docs/02-design/specs/20261021-it2-common.md`의 '창 규칙'·'정의 불능 code' 절만 쓴다(DEC-38 -- 본문 코드 없음). 정본 문장 = design 41 v1.12.3(`41:n`). `E/` = `skills/analog-gmid-design/gmid_engine/`. 쓰기 경로 = `E/tests/**`(agent 정의의 옛 `assets/tests/**`가 아니다).

## 관찰 가능한 계약

| 모듈 | 심볼 | 시그니처 |
|---|---|---|
| `gmid_engine.sizing.s2_values` | `Window` | Window(lo, hi, constraints, input_status=None, tol_v=None, status_detail=()) |
| `gmid_engine.sizing.s2_values` | `OUTPUT_HIGH_IMPEDANCE` | 상수 `"high_impedance"` |
| `gmid_engine.sizing.s2_values` | `OUTPUT_KVL_FIXED` | 상수 `"kvl_fixed"` |
| `gmid_engine.sizing._helpers_dc_solve` | `*` | 신규 모듈: `Circuit`(as-built `block_columns._Circuit`, `region_rows(values)` 추가)·`solve`·`FAILURES` |
| `gmid_engine.sizing.input_window` | `saturation_window` | def saturation_window(unknown, roots, values, gradient, rows, *, slope=None) -> tuple | None |

### 필드(graph) -- writer 하나

| 필드 | 값 | writer |
|---|---|---|
| `node.dc_output_structure` | 출력 포트 넷마다 `"high_impedance"`\|`"kvl_fixed"` | `dc_writer_plan` |
| `node.dc_window` | `Window` -- 모든 입력 포트 + W4 뿌리; `input_status` ∈ {None, `"measured"`, `"unsettled"`, `"unmeasured"`(뿌리만), `"op_mismatch"`(`lo`·`hi` None, `status_detail` = `(("devices", 정렬 tuple),)`), `"f_component_undeclared"`(`lo`·`hi` None)} | `dc_columns` |

### 단언 금지

`NodalSystem.factor` 내부 배열 값, `input_version` 문자열 값(같음·다름만), 분해능 수치 자체, `IcmConfig.transfer`의 resolution 수치, `IcmWindow.model_error_ref`(None만), S3 색인 내부, `RunCounters` 행 타입 이름.

## test 목록(위치 제안 -- 규칙 H 1:1, 이름 접두 `test_it2b_`)

| id | 위치 | 내용(정본) | oracle | base |
|---|---|---|---|---|
| T-OS | `tests/sizing/test_output_structure.py` | OS (a)~(k)(41:727) | (손)+(독립) | red((d)(e)(f)(k) 행동 red) |
| T-K1·K2 | `dc_columns` test 파일 | 41:799-800 | (손) | red |
| T-Pab-k | 같은 파일 | 감도 음수 포트 커널 창 lo ≤ hi = [min, max]; 선언 둘 포트 창 끝 차 = 선언 차 | (손) | red |
| T-D | `tests/sizing/test__helpers_dc_solve.py` | `triode` 행 영 교차 = 창 끝, (S4-나) `kind` 집합·공용 전도 함수 호출 0(`git grep`), `op_mismatch` 상태·detail·같은 점 봉인 거부(41:809) | (손)+(독립) | red |
| T-SW | `tests/sizing/test_input_window.py` | 새 서명: 이동량 창, `roots` 쌍 원소, `slope` 갈래, 5원소 행 | (식)+(손) | red |
| T-L12a-k | `dc_columns` test 파일 | `k_max` 소진·tol 미정 → 뿌리 `unsettled`, W4 y 범위 그대로 | (손) | red |
| T-L12b-k | 같은 파일 | F 성분 미선언 포트 `node.dc_window` = `f_component_undeclared`, `lo`·`hi` None | (손) | red |
| T-FD | `tests/search/test_fd_jacobian.py` | 입력 포트 항목이 늘어도 y 스텝 = W4 뿌리 창 폭만 | (식) | green 유지(red 목록 제외) |

red 예상 목록 = 엔진 동작·엔진 트리 구조를 보는 test(green 유지 대상·하네스 자체 test 제외). 새 키워드 직접 호출 `TypeError`는 red로 세지 않는다. `-k` 식 충돌은 base·head `--collect-only` 수를 함께 보고(xrunf1b 3.3 상속).

## 판정 측정(audit)

I-1, I-2 G1·G2·G3·G6(소비자 미배선 상태 기록)·G7, I-5 θ 프레임 W4 창·FD 스텝 9회로 비트 동일, I-6, I-7 회로 이름 0. (I-n 정의 = 공통 문서 interface 측정표.)

## 변경 이력

- 2026-10-29 `cards/revise-1029`: 위 상태 표지만 더함 -- 본문 불변, 표지 전 원문 = `git show 052465ed:docs/02-design/specs/20261021-it2b-kernel-window.interface.md`.
