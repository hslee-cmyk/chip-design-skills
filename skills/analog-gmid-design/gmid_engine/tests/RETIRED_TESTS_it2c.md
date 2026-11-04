# 폐기 test -- card 20261104-it2c-icm-config (판정 기록 근거 `retired_tests`)

interface '빈칸 답'의 폐기 규칙: 정의가 바뀌어 전제가 깨진 test는 고치지 않고 지운다. 사유 근거 = 계획 v6.38.8 N3.8·N6.6, design 41 v1.16.3 §4.7-W, 사용자 결정 O-109·O-205.

| test (옛 파일) | 사유 |
|---|---|
| `test_it2b_os_a_drain_only_output_is_high_impedance` (tests/sizing/test_writer_plan.py) | `node.dc_output_structure`·출력 구조 분류 삭제(O-205). 대체 = T-E9 `test_it2c_e9_output_structure_not_in_field_or_vocabulary` |
| `test_it2b_os_b_follower_output_without_fixed_end_is_high_impedance` | 위와 같음 |
| `test_it2b_os_c_resistor_load_to_rail_is_kvl_fixed` | 위와 같음 |
| `test_it2b_os_d_w3_output_without_fixed_end_is_high_impedance` | 위와 같음 |
| `test_it2b_os_e_w3_output_on_hard_path_is_kvl_fixed` (parametrize 2) | 위와 같음 |
| `test_it2b_os_f_other_w3_node_in_component_is_not_a_fixed_end` | 위와 같음 |
| `test_it2b_os_g_declared_input_dc_reaches_output_through_gate_source` | 위와 같음 |
| `test_it2b_os_h_swapped_names_give_same_values` (parametrize 2) | 위와 같음 |
| `test_it2b_os_i_value_is_theta_independent_and_not_recomputed` | 위와 같음 |
| `test_it2b_os_k_no_same_dc_edge_between_input_ports` | 위와 같음 |
| `test_it2b_os_j_single_writer_site_and_no_second_producer` | 위와 같음 (`dc_output_structure` 소스 자리 단언의 대상 소멸; T-L8f·T-E9 가 부재를 단언) |
| `test_it2b_output_structure_vocabulary_and_window_status_defaults` (tests/sizing/test_s2_values.py) | `OUTPUT_*` 어휘·`f_component_undeclared` 상태 삭제. 남은 `Window` 기본값 단언은 `test_it2b_window_status_defaults` 로 유지(이름만 바뀜) |
| `test_it2b_sw_several_roots_move_together` (tests/sizing/test_input_window.py) | `saturation_window` 의 `root` 는 넷 하나(묶음 없음). 대체 = `test_it2c_sw_root_is_a_single_net` |
| `test_it2b_sw_root_pair_replaces_row_equation_by_fixed_net` | 쌍 root 삭제. 대체 = `test_it2c_sw_pair_root_is_not_accepted` |
| `test_it2b_k1_declared_input_port_has_measured_window` (tests/sizing/test_block_columns.py) | 커널 `node.dc_window` 는 W4 뿌리 넷만(선언 입력 포트 항목 없음, interface 7번 표 폐기). 대체 = T-K(cfg), O-109 D1 (A-83) |
| `test_it2b_pb_declared_input_ports_share_one_shift_window` | 위와 같음. 대체 = T-P(cfg 일반·대칭 toy), O-49 P3 (A-83) |
| `test_it2b_d_triode_row_zero_crossing_is_the_window_end` | interface 7번 표 폐기. 대체 = `test_it2c_triode_declared_device_row_zero_crossing_is_the_window_end` (A-83) |
| `test_it2b_l12a_tol_undefined_root_window_is_unsettled_and_y_range_kept` 의 소사례 (d)만 (test 는 유지) | 창 행이 tol 을 읽지 않아 '슬라이스에 VDSAT 가 있으면 두 표가 함께 None -> unmeasured' 전제 소멸(실측 "unsettled"). (a)(c) 단언 유지 (A-83) |
| `test_declared_input_dc_same_theta_seals` 의 `node.dc_window["in"]` 단언 줄만 (test 는 유지) | 선언 포트 커널 창 항목 없음. cfg 는 `icm_config`(metrics) writer 라 `size_and_seal` 스냅샷에 없어 옮기지 않음. cfg 측 단언은 tests/metrics (A-83) |
| `test_it2b_l12b_f_component_port_without_declared_dc_has_undefined_window` (tests/sizing/test_block_columns.py) | 상태 `f_component_undeclared` 삭제: F 성분 미선언 포트도 구동에 든다. 대체 = `test_it2c_single_input_as_is_window_by_hand_kcl`·`test_it2c_servo_undeclared_input_dc_drives_both_ports_together` |

이동(폐기 아님): `test_it2b_d_region_rows_kinds_are_sat_and_triode_only`·`test_it2b_d_region_rows_has_no_zero_vgs_op_point_conduction_columns_or_eo1_import` 는 `tests/sizing/test__helpers_dc_solve.py` 로 옮겼다(대상 모듈 `Circuit.region_rows` 의 새 자리).
