---
id: 20261021-it2b-kernel-window
spec_card: docs/02-design/specs/20261021-it2b-kernel-window.spec.md
test_id: skills/analog-gmid-design/gmid_engine/tests/sizing/test_input_window.py::test_it2b_sw_several_roots_move_together
test_id: skills/analog-gmid-design/gmid_engine/tests/sizing/test_input_window.py::test_off_mid_window_maps_y_and_ends_saturated[0.0-above]
test_id: skills/analog-gmid-design/gmid_engine/tests/sizing/test_input_window.py::test_off_mid_window_maps_y_and_ends_saturated[0.0-below]
test_id: skills/analog-gmid-design/gmid_engine/tests/sizing/test_output_structure.py::test_it2b_os_g_declared_input_dc_reaches_output_through_gate_source
test_id: skills/analog-gmid-design/gmid_engine/tests/sizing/test__helpers_dc_solve.py::test_it2b_d_triode_row_zero_crossing_is_the_window_end
test_id: skills/analog-gmid-design/gmid_engine/tests/sizing/test__helpers_dc_solve.py::test_it2b_d_operating_point_mismatch_status_and_detail
test_id: skills/analog-gmid-design/gmid_engine/tests/sizing/test_s2_values.py::test_it2b_output_structure_vocabulary_and_window_status_defaults
test_id: skills/analog-gmid-design/gmid_engine/tests/sizing/test_s2_values.py::test_value_fields_as_contract
---
## 문제의 test

1. `test_it2b_sw_several_roots_move_together` 마지막 두 줄: `saturation_window(("a","b","w","x"), ("x",), vals, grad, rows)`에서 `w`가 `unknown`에 있으나 `roots`가 아니고 test의 `gradient`는 `a`, `b`만 안다(`KeyError: 'w'`). `unknown`의 비뿌리 넷은 `gradient`로 행을 세우는 것이 as-built 계약(`input_window.py` 머리)이라, 이 호출은 어떤 구현에서도 `gradient('w')`를 부른다. 고정 넷이면 `unknown`에 넣지 않는 것이 계약(설계 41 4.7-3 3 "다른 F 넷은 s = 0").
2. `test_off_mid_window_maps_y_and_ends_saturated[0.0-*]`: 창 끝 y = 0에서 봉인 7 pass와 독립 여유 ≥ −1e-12를 요구한다. 설계 41 4.7-3 1은 커널에서 `_refine_ends`를 부르지 않는다(선형 감도 끝). 측정: y = 0에서 slack_v = −1.79e-6(1차 외삽 오차)로 봉인 7이 거부한다(y = 0.125~1.0과 y = 1.0은 통과). 이 test는 끝 다듬기(옛 A6 (5))를 전제한다. `_refine_ends` 제거 전에는 통과, 제거 뒤 설계대로면 실패.
3. `test_it2b_os_g_...`: `build_ctx(tmp_path / "decl", ...)`가 존재하지 않는 하위 폴더에 토폴로지 파일을 써서 `FileNotFoundError`(엔진 밖 test 설정 오류; `mkdir` 없음).
4. `test__helpers_dc_solve.py::test_it2b_d_triode_row_zero_crossing...`: `run_blocks(upto="columns")`(conftest)는 `dc_columns`에 5번째 extras `linear_devices`를 넘기지 않아(`kernel_run.py:98`은 넘긴다) `triode` 선언이 블록에 닿지 않는다. 블록 입력이 없는 선언을 test가 기대한다.
5. `test_it2b_d_operating_point_mismatch...`·`test_s2_values.py`의 `status_detail` 칸 단언 둘: 사용자 결정 O-98(코디네이터 지시, 계획 v6.33 검증 중)로 `op_mismatch` 어휘와 `Window.status_detail` 칸이 IT-2b에서 빠졌다. test는 아직 옛 계약이다.

## 근거(oracle 또는 사용자 원문)

설계 41 v1.12.8 4.7-3 1(`_refine_ends` 커널 미호출), 4.7-3 3(F 넷 s = 0), 4.7-3a 3; spec card '관찰 가능한 계약'; 코디네이터 지시(O-98 "IT-2b는 triode 행 영 교차·부재 단언만"). 측정: 위 1~4는 `pytest` 실행 출력(`r1_sizing.txt`).

## 요청

test 작성 주체가 1~5를 고치거나 오케스트레이터가 계획 승인 뒤 정리하도록 넘긴다. code는 test를 바꾸지 않았다. 4번은 conftest `run_blocks`에 `linear_devices`를 받는 경로(또는 `dc_columns`가 선언 triode를 필드로 읽는 설계)가 필요하다.
