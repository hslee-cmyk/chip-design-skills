---
id: 20261107-fs1-signature-misses-search
spec_card: docs/02-design/specs/20261107-fs1.spec.md
test_id: skills/analog-gmid-design/gmid_engine/tests/search/test_layer0_center.py::test_single_current_first_probe_direction_zero
test_id: skills/analog-gmid-design/gmid_engine/tests/search/test_layer0_center.py::test_maxmin_t_rows_hard_and_monotone
test_id: skills/analog-gmid-design/gmid_engine/tests/search/test_layer0_center.py::test_layer0_lift_independent_of_solver_noise
test_id: skills/analog-gmid-design/gmid_engine/tests/search/test_layer0_center.py::test_layer0_start_fd_theta_bits_equal_start_theta
test_id: skills/analog-gmid-design/gmid_engine/tests/search/test_layer0_center.py::test_theta_coords_used_by_layer0
test_id: skills/analog-gmid-design/gmid_engine/tests/search/test_search_values.py::test_frozen (StartPoint-args2)
test_id: skills/analog-gmid-design/gmid_engine/tests/search/test_search_values.py::test_eval_result_identity_equality
test_id: skills/analog-gmid-design/gmid_engine/tests/search/test_slsqp_outer.py (11 case: test_start_not_accepted, test_minimize_from_start_bounded_by_limits x2, test_eps_constraint_respected, test_start_theta_reused_no_extra_kernel, test_history_points_key_matches_their_theta, test_large_area_row_best_judged_on_raw_c x2, test_outer_start_outside_box_component_is_exp_of_clipped, test_outer_first_step_shortfall_zero_iterations_best_is_start, test_outer_mid_iteration_budget_stop_keeps_kernel_calls_within_budget)
test_id: skills/analog-gmid-design/gmid_engine/tests/search/test_seal7_pending.py::test_real_evaluations
test_id: skills/analog-gmid-design/gmid_engine/tests/search/test_kernel.py::test_pending_point_passive_values_reused_on_mos_theta_only_change
test_id: skills/analog-gmid-design/gmid_engine/tests/search/test_residual_probe.py (4 case)
test_id: skills/analog-gmid-design/gmid_engine/tests/metrics/test_metrics_aux.py (8 error: size_and_seal 호출)
test_id: skills/analog-gmid-design/gmid_engine/tests/metrics/test_ss_evaluate.py (49 error: size_and_seal 호출)
test_id: skills/analog-gmid-design/gmid_engine/tests/metrics/test_block_param_tables_slices.py::test_slice_block_value_e4_empty_bin_map_leaves_amax_undetermined
test_id: skills/analog-gmid-design/gmid_engine/tests/convergence/test_converge_point.py (17 case)
---
## 문제의 test

새 서명에 맞추지 않은 호출. 실패 메시지(코드 변경 없이 호출 모양 때문에 나는 것):

* `test_layer0_center.py:185` 모듈 `wrapped`(spy)가 `real(sctx, theta, cells, parent=..., origin=..., geometry=...)` 로 `evaluate` 를 부른다 -- `wf` 인자 없음 → `TypeError: evaluate() missing 1 required positional argument: 'wf'`(5 case).
* `test_search_values.py`: `StartPoint(...)`(`wf` 칸 빠짐: `StartPoint.__init__() missing 1 required positional argument: 'source'`), `EvalKey(...)`(`wf_fp` 칸 빠짐: `missing ... 'theta_hex'`).
* `test_slsqp_outer.py`: `evaluate(...)` `wf` 없음 8, `StartPoint(...)` 3 칸, `eval_key(...)`(`wf_fp` 없음) 1.
* `test_seal7_pending.py::test_real_evaluations`, `metrics/test_metrics_aux.py` 8 error·`metrics/test_ss_evaluate.py` 49 error: `size_and_seal(ctx, th)` 에 `wf` 없음.
* `test_kernel.py::test_pending_point_...`: 시험 코드의 `lambda ... parent=` 가 `evaluate(sctx, theta, cells, wf, parent=...)` 의 4번째 위치 인자와 `parent` 키워드를 함께 받아 `got multiple values for argument 'parent'`.
* `test_residual_probe.py` 4 case: 가짜 sctx(`types.SimpleNamespace`)에 `dc` 가 없는데 FS-1 의 `residual_probe` 는 `initial_wf(sctx.dc.base)` 로 평가 입력을 만든다(spec W19 `residual_probe.py:87` 평가 입력 조립 자리) → `AttributeError: ... no attribute 'dc'`.
* `test_converge_point.py` 17 case: 가짜 평가 루프 `evaluate(self, sctx, theta, cells, parent=None, origin=(), geometry=None)`(`test_converge_point.py:93`)에 `wf` 인자가 없고, 손 스냅샷 `FakeSnapshot`(convergence/conftest.py)에 `graph/start: wf_start`·`dc_op` 가 없어 `point_wf(start.evaluation.snapshot)` 이 `KeyError: ('graph', 'wf_start')`.
  (`converge_point` 는 spec W19 가 정한 대로 레이아웃 뒤 평가 입력 칸을 기준 점 스냅샷에서 읽는다 -- `EvalResult`/`EvalKey` 에 `WfInput` 사본 칸이 없다.)
* `test_block_param_tables_slices.py:193` 가 삭제된 `reachable_slices` 를 import(`ImportError`).

## 근거(oracle 또는 사용자 원문)

interface §4.1·§4.5(`evaluate(sctx, theta, cells, wf, ...)`, `eval_key(..., cells, wf_fp, w_fixed_fp)`, `EvalKey.wf_fp`, `StartPoint(start_id, theta, cells, wf, source)`, `size_and_seal(ctx, theta, wf, ...)`), spec 재작성 범위 W17~W19·삭제 이름(`reachable_slices`), spec '분류 표'(해당 파일은
"서명 맞춤" 대상으로 적혀 있거나(`search/test_slsqp_outer`·`test_search_values` 는 `StartPoint` 서명), 적혀 있지 않다). 코드가 선택 인자·옛 서명을 되살리면 D-4/E 시리즈(필수 인자) 단언이 깨진다.

## 요청

위 호출을 새 서명으로 맞춘다(`search/conftest.evaluate`·`fs1_wf.size_and_seal` 래퍼, `StartPoint(..., wf, ...)`, `EvalKey(..., wf_fp, ...)`). 가짜 sctx/스냅샷 test 는 가짜에 `dc.base` + `wf_start` 칸을 더하거나(또는 가짜 평가 `evaluate` 에 `wf` 를 더하고 `FakeSnapshot` 에 `graph/start wf_start`·`device dc_op` 행을 준다).
