---
id: 20261107-fs1-signature-misses
spec_card: docs/02-design/specs/20261107-fs1.spec.md
test_id: skills/analog-gmid-design/gmid_engine/tests/sizing/test_dc_solve_values.py::test_dc_solve_writer_constant_and_dc_sat_v_writer
test_id: skills/analog-gmid-design/gmid_engine/tests/sizing/test_dc_solve_values.py::test_dc_solve_sealed_point_passes_all_nine_items
test_id: skills/analog-gmid-design/gmid_engine/tests/sizing/test_scc_newton.py::test_slow_contraction_switches_to_newton (2 case)
test_id: skills/analog-gmid-design/gmid_engine/tests/sizing/test_scc_newton.py::test_contracting_gauss_seidel_does_not_run_newton (2 case)
test_id: skills/analog-gmid-design/gmid_engine/tests/sizing/test_scc_newton.py::test_methods_direct_and_bisection
test_id: skills/analog-gmid-design/gmid_engine/tests/sizing/test_scc_newton.py::test_gauss_seidel_not_contracting_newton_converges (2 case)
test_id: skills/analog-gmid-design/gmid_engine/tests/sizing/test_scc_newton.py::test_q_ill_conditioned_point_no_longer_rejected_by_seal_9
test_id: skills/analog-gmid-design/gmid_engine/tests/sizing/test_scc_newton.py::test_newton_failure_in_case_one_is_raised
test_id: skills/analog-gmid-design/gmid_engine/tests/sizing/test_scc_newton.py::test_r7_q_close_to_one_projection_not_accepted
test_id: skills/analog-gmid-design/gmid_engine/tests/sizing/test_scc_newton.py::test_case_two_seal_violation_kept_with_newton_cause
test_id: skills/analog-gmid-design/gmid_engine/tests/sizing/test_scc_newton.py::test_newton_converged_then_strict_recheck_failure_raised
test_id: skills/analog-gmid-design/gmid_engine/tests/sizing/test_scc_newton.py::test_newton_path_deterministic (2 case)
---
## 문제의 test

위 16개 case. `size_and_seal(ctx, th)`(또는 `size_and_seal(ctx_s, th)`)를 `wf` 없이 부른다 -- 새 서명 `size_and_seal(ctx, theta, wf, ...)` 에서 `wf` 는 필수 위치 인자라 `TypeError: size_and_seal() missing 1 required positional argument: 'wf'`.

## 근거(oracle 또는 사용자 원문)

interface §4.1: "`size_and_seal(ctx, theta, wf, parent=None, ...)` -- `wf: WfInput` **필수 위치 인자**(기본값 없음)", D-4 `test_dc_solve_wf_required_positional`(wf 없이 부르면 `TypeError`)이 이 계약을 직접 단언한다.
spec '분류 표' 는 `sizing/test_dc_solve_values.py` 를 "서명·칸 맞춤" 대상으로 적었고 `RETIRED_TESTS_fs1.md` 의 서명 맞춤 목록에도 `test_dc_solve_values.py` 가 있으나, 이 두 함수는 고쳐지지 않았다. `sizing/test_scc_newton.py` 는 분류 표·서명 맞춤 목록에 없다
(`ctx_s`·`ctx_q` 회로에서 `size_and_seal` 을 직접 부른다). 코드 쪽에서 `wf` 를 선택 인자로 되돌리면 D-4 가 깨진다 -- 모순.

## 요청

위 16개 case 의 `size_and_seal(ctx, th)` 를 `fs1_wf.size_and_seal`(손 wf 래퍼)로 바꾸거나 `wf=hand_wf(ctx)` 를 더한다. 기대값은 바꾸지 않는다(wf 키는 그 ctx 의 유일한 슬라이스 - 기존 단일 슬라이스 LUT 에서는 선택 불변).
