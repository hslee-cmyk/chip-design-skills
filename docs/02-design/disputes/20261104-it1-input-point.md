---
id: 20261104-it1-input-point
spec_card: docs/02-design/specs/20261104-it1-input-point.spec.md
test_id: gmid_engine/tests/sizing/test_writer_plan.py::test_renamed_diffpair_plan_follows_colour_correspondence
test_id: gmid_engine/tests/sizing/test_writer_plan.py::test_library_renaming_metamorphic
test_id: gmid_engine/tests/sizing/test_writer_plan.py::test_it2b_os_c_resistor_load_to_rail_is_kvl_fixed
test_id: gmid_engine/tests/sizing/test_writer_plan.py::test_it2b_os_k_no_same_dc_edge_between_input_ports
test_id: gmid_engine/tests/sizing/test_s2_values.py::test_block_reads_declared_as_contract[dc_writer_plan]
test_id: gmid_engine/tests/sizing/test_block_columns.py::test_it2b_pa_negative_sensitivity_port_window_is_min_max_of_the_two_end_voltages
test_id: gmid_engine/tests/sizing/test_block_columns.py::test_it1_t1h_input_point_ports_share_voltage_and_window_key
test_id: gmid_engine/tests/sizing/test_scc_order.py::test_library_order_valid
test_id: gmid_engine/tests/sizing/test_kernel_context.py::test_library_plan_invariants
test_id: gmid_engine/tests/sizing/test_current_basis.py::test_current_ties_and_variables_match_8e46548
test_id: gmid_engine/tests/graph/test_s1_symmetry.py::test_block_declaration
---
## 문제의 test

code 커밋 ①②③ 뒤에도 실패하는 test 열 묶음. 코드는 interface 계약(입력 점 규칙)대로 구현했고, 아래 test 의 기대가 그 계약과 맞지 않는다.

1. `test_renamed_diffpair_plan_follows_colour_correspondence`, `test_library_renaming_metamorphic[current_reuse_telescopic_ota-1]`: y 키를 dc_colour 대응 아래 비교한다. 계약은 y 키 = role `differential_input_p` 포트 넷(T-1g 가 role 이 정함을 단언). p·n 이 자기동형으로 맞바뀌는 회로에서 dc_colour 는 소자 이름순 정준 위치로 갈려서(1-WL 색은 port_role 을 읽지 않음), 이름 맞바꿈 뒤 p 포트의 색이 달라진다(a: y_key 색 8, b: 9). 두 단언은 동시에 성립할 수 없다.
2. `test_it2b_os_c_resistor_load_to_rail_is_kvl_fixed`, `test_it2b_os_k_no_same_dc_edge_between_input_ports`: 입력 DC 미선언 + role 이 차동쌍이 아닌 입력 포트 둘(`"x"`, `extra_input`)의 toy 라 계약 표 '그 밖' 행(`input_cm_undefined` 정지)에 든다. 입력 role 을 차동쌍으로 고치거나 입력 DC 를 선언해야 한다(os_k 의 '두 성분' 전제는 입력 점이 한 점으로 묶으므로 다시 유도).
3. `test_block_reads_declared_as_contract[dc_writer_plan]`: READS 집합 동등 단언. 기대 집합에 `node.port_role`·`graph.gvgs_summary` 가 없으나 T-1(`test_it1_writer_block_owns_plan_fields`)이 둘을 요구한다. 두 test 가 서로 모순.
4. `test_it2b_pa_negative_sensitivity...`: `_neg_doc` 의 두 입력 포트(x p, p n)가 이제 한 입력 점이라 x = `input_point`(뿌리), p = `input_point`(짝, 항목 없음). test 는 x `free_window`·p `vgs_gate`·p 창 항목을 단언해 계약('n 포트 항목 없다')과 충돌.
5. `test_it1_t1h_input_point_ports_share_voltage_and_window_key`: `abs(V["t"] - _dp_t(V["ina"])) <= 1e-5` 만 실패(실측 5.4e-5). 같은 oracle 이 입력 DC 선언 toy 에서 입력 1.0 V 일 때도 5.3e-5 차이(풀이기 tol_V 7.8e-3 안, LUT 보간 대 독립 이분법의 차)다. 입력 0.9 V 에서만 1.0e-6 으로 맞는다. 코드 문제가 아니라 허용오차 1e-5 가 입력 전압 1.0 V 근방에서 성립하지 않는다.
6. `test_scc_order.py::test_library_order_valid`(6), `test_kernel_context.py::test_library_plan_invariants`(6): 독립 oracle 이 relation 어휘에 `input_point` 가 없고(`unknown relation 'input_point'`), 순환수 oracle(`gvgs_counts`)이 입력 점을 한 점으로 묶지 않아 '종속 수 = 순환수' 가 5 대 4. 계약 불변식은 묶은 순환수.
7. `test_current_basis.py::test_current_ties_and_variables_match_8e46548`(6 회로): 회귀 기준선(BASELINE_8E46548) 변수 수가 입력 점으로 하나 줄어(예: folded_cascode 17 -> 16). interface '회귀 기준선 fixture' 규칙대로 판정자 재측정 대상(원인 칸 DEC-106).

## 근거(oracle 또는 사용자 원문)

interface card '입력 점 규칙(DEC-106 -- 손 판정 기준)': y 키 = role p 포트 넷, 두 포트 같은 점, n 포트 `dc_window` 항목 없음, 종속 수 = 묶은 G_vgs 순환수, 입력 DC 미선언 + 차동쌍 아님 = `input_cm_undefined`. 코디네이터 동결 판정(2026-11-04): achievability DOF 입력 점 변수 공유, T-1i 종속 2 -- 반영함.

## 요청

위 test 를 계약에 맞게 갱신(role·oracle 어휘·READS 기대·허용오차·기준선). 코드 주체는 test 를 고치지 않았다. 1·5 번은 기대값 선택이 필요하다(1: 색 대응 단언을 role 대응으로, 5: 허용오차 또는 입력 전압).

## 추가(fix/it1-canon): test_s1_symmetry.py::test_block_declaration

master 회귀 `search/test_canonical_order.py::test_renaming_keeps_kind_key_dim_sequence[1],[2]`(위 1번과 같은 원인: p 포트 dc_colour 가 p·n 자기동형으로 이름 전단사에서 뒤바뀜)를 정본 자리(`dc_colour` writer `s1_symmetry`)에서 고쳤다: role p 포트의 정준 위치를 자기 궤도의 최소 위치로 자기동형 h 로 다시 쓴다(cert 불변). 이를 위해 `s1_symmetry` 가 `("node", "port_role")` 을 READS 로 읽는다. 그 결과 canonical_order 12/12, tests/structure, sizing/test_writer_plan.py, tests/graph 2202건 통과, 단 `test_block_declaration`(test_s1_symmetry.py:134-135)이 reads 를 8개 집합으로 고정해 1건 실패한다. 요청: reads 기대값에 `("node", "port_role")` 추가. role 을 marks 로 우회하는 안은 같은 필드의 둘째 경로라 권하지 않는다.
