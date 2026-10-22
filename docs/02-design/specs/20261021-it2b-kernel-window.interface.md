# interface card: 20261021-it2b-kernel-window

> **재동결 (design 41 v1.12.10, 계획 v6.33, base 2a4ab829)** -- 2026-10-22, 사용자 결정 O-98·O-100·O-101·O-103·O-104. 줄 인용 `41:n` = v1.12.10 줄(v1.12.8과 줄 같음). S4 갈래 = **(S4-나) 확정**(IT-2b~IT-2d 공통 -- spec card '의도'). 바뀐 것: `Window` 칸 다섯, `_helpers_dc_solve` 행 IT-2d로, `input_status` 어휘에서 `op_mismatch` 뺌, T-D 위치·내용, L12 (a)(e) test 기대, 판정 측정 I-5·분류표 대조.
>
> (옛 표시) **재동결 (design 41 v1.12.8, 계획 v6.31, base 0c048327)** -- 2026-10-22. 줄 인용 `41:n` = v1.12.8 줄(v1.12.3 대비 735행 이상 +1). 계약·test 목록 내용은 그대로이고 줄 번호와 test 위치 한 칸만 고쳤다.

card IT-2b -- 커널 창. test 작성 주체는 소스를 보지 않고 이 문서와 공통 문서 `docs/02-design/specs/20261021-it2-common.md`의 '창 규칙'·'정의 불능 code' 절만 쓴다(DEC-38 -- 본문 코드 없음). 정본 문장 = design 41 v1.12.10(`41:n`, base `2a4ab829`). `E/` = `skills/analog-gmid-design/gmid_engine/`. 쓰기 경로 = `E/tests/**`(agent 정의의 옛 `assets/tests/**`가 아니다).

## 관찰 가능한 계약

| 모듈 | 심볼 | 시그니처 |
|---|---|---|
| `gmid_engine.sizing.s2_values` | `Window` | Window(lo, hi, constraints, input_status=None, tol_v=None) -- 칸 다섯(`status_detail` 없음, 41:688) |
| `gmid_engine.sizing.s2_values` | `OUTPUT_HIGH_IMPEDANCE` | 상수 `"high_impedance"` |
| `gmid_engine.sizing.s2_values` | `OUTPUT_KVL_FIXED` | 상수 `"kvl_fixed"` |
| `gmid_engine.sizing.input_window` | `saturation_window` | def saturation_window(unknown, roots, values, gradient, rows, *, slope=None) -> tuple | None |

`gmid_engine.sizing._helpers_dc_solve`(`Circuit`·`solve`·`FAILURES`)는 IT-2d 몫이다(41:760 '이동 시점'). IT-2b에서 `region_rows`는 `block_columns` 안 비공개 이름이라 공개 진입점 `dc_columns`를 거쳐서만 본다.

### 필드(graph) -- writer 하나

| 필드 | 값 | writer |
|---|---|---|
| `node.dc_output_structure` | 출력 포트 넷마다 `"high_impedance"`\|`"kvl_fixed"` | `dc_writer_plan` |
| `node.dc_window` | `Window` -- 모든 입력 포트 + W4 뿌리; `input_status` ∈ {None, `"measured"`, `"unsettled"`, `"unmeasured"`(뿌리만), `"f_component_undeclared"`(`lo`·`hi` None)} -- 불일치 값 없음((S4-나), 41:688) | `dc_columns` |

### 단언 금지

`NodalSystem.factor` 내부 배열 값, `input_version` 문자열 값(같음·다름만), 분해능 수치 자체, `IcmConfig.transfer`의 resolution 수치, `IcmWindow.model_error_ref`(None만), S3 색인 내부, `RunCounters` 행 타입 이름.

## test 목록(위치 제안 -- 규칙 H 1:1, 이름 접두 `test_it2b_`)

| id | 위치 | 내용(정본) | oracle | base |
|---|---|---|---|---|
| T-OS | `tests/sizing/test_output_structure.py` | OS (a)~(k)(41:727) | (손)+(독립) | red((d)(e)(f)(k) 행동 red) |
| T-K1·K2 | `dc_columns` test 파일(`tests/sizing/test_block_columns.py`) | 41:800-801 | (손) | red |
| T-Pab-k | 같은 파일 | 감도 음수 포트 커널 창 lo ≤ hi = [min, max]; 선언 둘 포트 창 끝 차 = 선언 차(입력 DC는 스칼라 선언이라 선언 차 = 0) | (손) | red |
| T-D | `tests/sizing/test_block_columns.py`(IT-2b에서 `test__helpers_dc_solve.py`를 만들지 않는다 -- 규칙 H 고아 방지, 그 파일·공개 이름 test는 IT-2d) | 계획 (9) (a)~(d)(41:810): (a) `triode` 선언 소자가 동작점에서 triode(전제 단언)이고 훑기 중 포화로 가는 toy → 행 영 교차 = 커널 창 끝 (b) `region_rows` `kind` 집합 = {`"sat"`, `"triode"`} (c) 정적 AST(docstring·주석 제외) -- `region_rows`와 그것이 부르는 IT-2 모듈 함수에 VGS 상수 0 `op_point` 호출 0·`device.dc_off_current`·`device.dc_conduction_floor` 읽기 0·EO-1 모듈 import 0 (d) 정적 AST(비test 엔진 소스, docstring·주석 제외) -- 식별자·문자열 상수에 `"op_mismatch"`·`status_detail`·`input_window_operating_point_mismatch`·`INPUT_STATUS_OP_MISMATCH`·`CODE_INPUT_WINDOW_OPERATING_POINT_MISMATCH` 0. 동작점 불일치 단언(`op_mismatch` 상태·detail·같은 점 봉인 거부·metric code)은 이 card에 없고 card EO-1 test로 옮겨 간다 | (손)+(독립) | red((a)(b)), green 가능((c)(d) 부재 단언) |
| T-SW | `tests/sizing/test_input_window.py` | 새 서명: 이동량 창, `roots` 쌍 원소, `slope` 갈래, 5원소 행 | (식)+(손) | red |
| T-L12a-k | `dc_columns` test 파일 | `k_max` 소진·tol 미정 → 뿌리 `unsettled`, W4 y 범위 그대로(41:814 (a)). `k_max` 소진 toy = 주입 지점 `gmid_engine.sizing.block_columns.k_max`(상한 1)만, 전제 단언으로 소진 분기 도달(요청 y ≠ 1/2, y = 1/2 풀이 성공, 첫 회 창과 둘째 측정 창의 차 > tol -- 손계산). tol 미정 toy = 41:694 'A6 b 도달 조건'(슬라이스에 VDSAT 열 없음·기준 LUT VDSAT 셀 정의·슬라이스 id_equivalent 셀 미정·비순환 쓰기 계획), sizing conftest 새 픽스처, `run_blocks(…, upto="columns")`; 만들 수 없으면 멈추고 보고 | (손) | red |
| T-L12b-k | 같은 파일 | F 성분 미선언 포트 `node.dc_window` = `f_component_undeclared`, `lo`·`hi` None | (손) | red |
| T-L12e | `tests/sizing/test_input_window.py`(고침) | 41:814 (e)·4.7-8 (8): `test_off_mid_window_maps_y_and_ends_saturated`·`test_mid_window_ends_have_nonnegative_saturation_slack` -- 내부 y는 기존 단언(독립 여유 ≥ −1e-12) 그대로; 끝점 y = '봉인' 또는 '봉인 7 거부 + 엔진 `slack_v`와 독립 oracle 여유가 모두 \|·\| ≤ `node.dc_window.tol_v`'; `tol_v` None이면 그 사례 무효(통과로 세지 않음) | (독립)+(식) | 기대 갱신 |
| T-FD | `tests/search/test_fd_jacobian.py` | 입력 포트 항목이 늘어도 y 스텝 = W4 뿌리 창 폭만(값 자체는 4.7-8 (8)로 바뀜 -- 비트 동일 단언 아님) | (식) | green 유지(red 목록 제외) |

red 예상 목록 = 엔진 동작·엔진 트리 구조를 보는 test(green 유지 대상·하네스 자체 test 제외). 새 키워드 직접 호출 `TypeError`는 red로 세지 않는다. `-k` 식 충돌은 base·head `--collect-only` 수를 함께 보고(xrunf1b 3.3 상속). `assert_voltages` 키 단언은 둘로 나눈다. P (a) 감도 음수 포트 toy는 이미 있다(`fd7c636f`).

## 판정 측정(audit)

I-1, I-2 G1·G2·G3·G6(소비자 미배선 상태 기록)·G7, I-6, I-7 회로 이름 0. (I-n 정의 = 공통 문서 interface 측정표.) I-5(θ 프레임 W4 창·FD 스텝 9회로 비트 동일)는 이 card에 적용하지 않는다 -- 뿌리 `lo`·`hi`, θ y 사상, `fd_jacobian` y 스텝은 동작 변경 4.7-8 (8)(41:817)이라 변화표 원인 칸 (8)로 적는다.

- 출력 구조 분류표 대조(41:724, 감사 몫 -- test 작성 주체 몫 아님): 13회로 출력 15개 가운데 엔진 값이 있는 12출력은 `node.dc_output_structure`를 승인된 표(`C:/Users/HSLEE/Documents/Todoc/fpga/wt/_drafts/evidence/2026-10-21/de1_output_structure_13.md` §2 41-57행 '새 분류', 사용자 결정 O-66 (1) -- `wt/_drafts/user_decisions.md:687`)와 대조하고, 쓰기 계획이 정지하는 3출력(cnr_ota VOP·VON `dc_resistor_cycle`, erfc_ota out `mos_zero_current_structural`)은 정지 사유가 표 §0과 같은지 대조해 변화표에 출력별로 적는다. 불일치(값 다름·사유 다름·새 정지)면 구조 규칙을 고치기 전에 멈추고 보고, 병합 전에 W3 목표 선언(CI-15)·F 선언·코퍼스가 바뀌면 표를 다시 재고 승인받은 뒤 병합.
