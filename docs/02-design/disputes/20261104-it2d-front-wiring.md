---
id: 20261104-it2d-front-wiring
spec_card: docs/02-design/specs/20261104-it2d-front-wiring.spec.md
test_id: skills/analog-gmid-design/gmid_engine/tests/metrics/test_ls_swing.py::test_undefined_codes_swing_only
test_id: skills/analog-gmid-design/gmid_engine/tests/metrics/test_metrics_aux.py::test_it2d_m2_config_none_same_definitional_code_for_metrics
test_id: skills/analog-gmid-design/gmid_engine/tests/metrics/test_ss_evaluate.py::test_it2d_f_icm_margin_same_value_in_report_and_front_row_as_is
test_id: skills/analog-gmid-design/gmid_engine/tests/metrics/test_ss_evaluate.py::test_it2d_f_icm_margin_same_value_in_report_and_front_row_servo
---
## 문제의 test

세 건 모두 구현을 맞춰도 통과할 수 없다(나머지 card test는 green).

**D1. `test_undefined_codes_swing_only` 셋째 사례 (test_ls_swing.py:171-179)**
`ls_swing(CS, RAILS, (("out", 1.0),), ("out",))` 가 `node_v_missing`(`swing_out_v is None`)을 내야 한다고 단언한다. 같은 파일 `test_it2d_ls_swing_circuit_without_inputs_has_swing_value`(:233-238)는
바로 그 호출 `ls_swing(CS, RAILS, (("out", 1.0),), ("out",))` 이 `undefined == ()`·`swing_out_v == 1.0` 이라고 단언한다. 두 단언은 같은 입력에 서로 반대다. 옛 test 셋째 사례는 입력 인자 `("in",)` 가 있어
`in` 의 node_v 가 없어서 `node_v_missing` 이었고, 입력 인자를 지우며 그 전제가 사라졌다.

**D2. `test_it2d_m2_config_none_same_definitional_code_for_metrics` (test_metrics_aux.py)**
입력 포트 셋 toy를 `input_dc_v` 없이(`load_case(..., constraints)`, 입력 DC = engine) 만들고 `size_and_seal` 을 부른다. 입력 DC 미선언 + 단일 입력 셋 이상이면 사이징 층이 DEC-106 으로
`StructureUnresolvedError(unsupported_rule_branch, rule_branch=input_cm_undefined, ports=(in, in2, in3))` 를 던진다(`sizing/writer_plan.py:309` `_input_point`, 탐색 전 정지). `ss_evaluate`·`icm_config`
갈래 2(`icm_inputs_unsupported`)에 도달하지 못한다. IT-2d code가 고칠 범위가 아니다(DEC-106 은 사이징 계약, test_writer_plan.py:612 가 그 정지를 요구한다).

**D3. `test_it2d_f_icm_margin_same_value_in_report_and_front_row_{as_is,servo}` (test_ss_evaluate.py:841-842)**
`T2.field(rep, "icm_margin_v")`(rep = `swing_icmr` 보고)를 읽는다. 보고는 `(이름, 값)` 쌍 tuple 이라 키 `icm_margin_v` 가 있어야 한다. 그러나 interface card 는 "`swing_icmr` 보고 키 ... 불변"(관찰 가능한
계약, '서명 불변' 절)이라고 하고, 현 보고 키는 `out_ranges`·`window`·`v_icm`·`input_dc`·`required_input_cm_v` 다. 키를 더하면 interface 의 불변 조항과 충돌하고, 값 사본(같은 칸 `icm_margin_v` 를 보고에 한 번 더 둠)이
된다 -- 원칙(값 사본 금지)과도 어긋난다.

## 근거(oracle 또는 사용자 원문)

* D1: test 파일 안의 두 단언(위 줄)이 동일 호출에 서로 다른 기대. oracle (a) 위 CS 산수(out ∈ [0.15, 1.5], V_o 1.0 -> swing 1.0)는 `test_it2d_ls_swing_circuit_without_inputs_has_swing_value`
  docstring 이 적었고 interface T-LS "입력 없는 회로 `swing_out_v` 값 있음"이 뒷받침한다. 따라서 셋째 사례가 틀리다.
* D2: `sizing/writer_plan.py:_input_point` 와 `tests/sizing/test_writer_plan.py:612`(DEC-106 정지 요구), `s2_values.py:95`. interface T-M2 "구성 None toy(`view_required` 등)"는 정지에 걸리지 않는 toy(입력 DC 선언
  또는 정지하지 않는 갈래)를 요구하는 것이지 정지를 우회하라는 요구가 아니다.
* D3: interface 서명 불변 문장("`SwingIcmr` 형식·`swing_icmr` 보고 키·분해능 칸 이름 불변")과 test 의 보고 키 읽기가 모순. 이 모순은 interface 문장을 고치거나(키 추가 허용) test 를 같은 칸 비교(`window`·`v_icm` 로부터
  손 margin 계산 또는 `SsEvaluation.ss` 항목)로 바꾸는 쪽에서만 풀린다.

## 요청

* D1: 셋째 사례를 지우거나 `node_v` 에 출력 넷을 뺀 입력(예: `node_v=()`)으로 바꾼다.
* D2: toy 에 입력 DC 를 선언하거나(`input_dc_v=0.6`, θ 스키마에서 `ln_idu` 제외) 사이징 정지에 걸리지 않는 구성 None 갈래(예: 입력 포트 0 이 아닌 `view_required`)로 바꾼다.
* D3: (a) test 를 `window`·`v_icm`·`ss.entries` 의 같은 칸 비교로 바꾸거나, (b) 사용자가 `swing_icmr` 보고에 `icm_margin_v` 키를 두는 것을 승인(interface 개정, 값 사본 예외)한다.
  code 는 결정이 나오기 전에는 보고 키를 바꾸지 않았다.
