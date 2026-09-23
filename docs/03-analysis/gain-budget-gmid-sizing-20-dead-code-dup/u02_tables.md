
### R-0 (7) -- 제안 삭제

| 함수 | 위치 | 줄수 | 참조(경로군별) | 레지스트리 이관 목적지 |
|---|---|---|---|---|
| `derived_spec` | :None | None | 0 | 〃 |
| `converge_with_parasitics` | sizing_recipe.py:126 | 31 | 0 | gmid_sizing_engine.py 또는 tests 데모 |
| `slew_rate` | sizing_recipe.py:179 | 3 | 0 | 삭제 후보 |
| `SemiEmpiricalGmIdLUT.fT` | sizing_recipe.py:674 | 8 | 0 | 삭제 후보(또는 준정적 검증에 배선) |
| `lut_conditions_from_npz` | sizing_recipe.py:5371 | 22 | 0 | circuit_state_graph S0(LUT 생성메타 해시) |
| `suggest_headroom_stack_groups` | stick_diagram.py:1538 | 148 | 0 | 삭제 후보 |
| `render_stick_diagram` | stick_diagram.py:6901 | 21 | 0 | test fixture/유틸 |

### R-1 (18) -- 제안 tests 이관

| 함수 | 위치 | 줄수 | 참조(경로군별) | 레지스트리 이관 목적지 |
|---|---|---|---|---|
| `build_toy_lut` | sizing_recipe.py:1414 | 39 | test 3 workspaces 1 | tests/ 픽스처(§8.8 test 분리 시 이관) |
| `run_regression_case` | sizing_recipe.py:1535 | 61 | test 1 | tests/(골든 회귀는 가치 있음 -- 이관) |
| `solve_diode_stack_current` | sizing_recipe.py:1671 | 50 | test 1 | 삭제 후보 |
| `estimate_area_budget` | sizing_recipe.py:2937 | 30 | test 2 | sizing_layout_convergence.py(배선 시) |
| `signal_path_nodes` | sizing_recipe.py:4059 | 35 | docs_py 1 probe 1 | (삭제 후보) |
| `node_pole_estimate` | sizing_recipe.py:4096 | 74 | probe 1 | (삭제 후보) |
| `validate_theta_declaration_order` | sizing_recipe.py:6885 | 93 | test 5 | topology_authoring |
| `load_derived_bounds` | sizing_recipe.py:8301 | 8 | test 1 | optimizer S3(흡수) 또는 삭제 |
| `find_interleaved_symmetric_splits` | stick_diagram.py:259 | 32 | test 1 | test util |
| `find_differential_and_mirror_forks` | stick_diagram.py:1321 | 74 | test 2 | 삭제 후보 |
| `check_multi_leaf_hub_parity` | stick_diagram.py:2990 | 39 | test 2 | test util |
| `find_diode_stacks` | stick_diagram.py:3107 | 29 | test 2 | circuit_state_graph(diode 정의 1개로 통합) |
| `audit_theta_root_direction` | stick_diagram.py:3525 | 79 | test 6 | topology_authoring(배선 여부 승인 필요) |
| `propose_theta_kcl_gap_fill` | stick_diagram.py:3626 | 346 | test 6 | topology_authoring(배선 승인 필요) |
| `apply_theta_kcl_gap_fill` | stick_diagram.py:3974 | 53 | test 1 | topology_authoring |
| `apply_device_roles_gap_fill` | stick_diagram.py:4737 | 63 | test 4 | topology_authoring |
| `audit_vertical_stack_id_euler_feasibility` | stick_diagram.py:5016 | 98 | test 3 | stick_diagram(배선 여부 승인 필요) |
| `find_euler_repair_options` | stick_diagram.py:5280 | 65 | test 3 | stick_diagram(배선 승인 필요) |

### R-2 (13) -- 제안 사슬 삭제

| 함수 | 위치 | 줄수 | 참조(경로군별) | 레지스트리 이관 목적지 |
|---|---|---|---|---|
| `GmIdLUT.junction_cap` | sizing_recipe.py:76 | 19 | engine 1 | gmid_sizing_engine.py(배선 시) 또는 삭제 |
| `_invq_newton` | sizing_recipe.py:1401 | 11 | engine 1 | tests/ 픽스처(삭제 아님) |
| `RegressionVerdict` | sizing_recipe.py:1495 | 5 | engine 7 | tests/(회귀 러너와 함께 이관, 삭제 아님) |
| `_cmfb_amp_gain_diode_load` | sizing_recipe.py:4935 | 49 | engine 2 test 2 workspaces 2 | (삭제 후보) |
| `_load_telescopic_topology_cached` | sizing_recipe.py:5061 | 14 | engine 1 | 삭제 후보 |
| `_telescopic_class_ab_open_loop_response` | sizing_recipe.py:5080 | 38 | engine 4 | 삭제 후보 |
| `_telescopic_open_loop_device_names` | sizing_recipe.py:5131 | 13 | engine 2 | 삭제 후보 |
| `_telescopic_class_ab_open_loop_gains` | sizing_recipe.py:5146 | 38 | engine 2 test 2 | 삭제 후보 |
| `MirrorSymmetryVerdict` | stick_diagram.py:234 | 2 | engine 2 | stick_diagram(삭제 후보) |
| `find_idiom_matches` | stick_diagram.py:1095 | 20 | engine 2 test 8 | topology_authoring |
| `MultiLeafHubParityVerdict` | stick_diagram.py:2984 | 4 | engine 4 | test util |
| `DiodeStackMember` | stick_diagram.py:3094 | 4 | engine 1 | - |
| `DiodeStack` | stick_diagram.py:3102 | 3 | engine 1 | - |

### R-3 (1) -- 제안 삭제(스크립트 확인)

| 함수 | 위치 | 줄수 | 참조(경로군별) | 레지스트리 이관 목적지 |
|---|---|---|---|---|
| `check_mirror_symmetry` | stick_diagram.py:238 | 19 | workspaces 1 | stick_diagram 유지 또는 test util |

### R-4 (9) -- 제안 유지·등급 정정

| 함수 | 위치 | 줄수 | 참조(경로군별) | 레지스트리 이관 목적지 |
|---|---|---|---|---|
| `render_report` | audit_current_forced.py:129 | 29 | engine 1 | §8.3 게이트 배선 후보 |
| `gm_from_fT` | sizing_recipe.py:101 | 3 | engine 2 | gmid_sizing_engine.py |
| `_run_optimize_multistage_case` | sizing_recipe.py:1502 | 24 | engine 1 | tests/ |
| `_cmrr_telescopic_class_ab` | sizing_recipe.py:4853 | 80 | engine 1 | (삭제 후보) |
| `_cmrr_telescopic_class_ab_cmfb` | sizing_recipe.py:5186 | 65 | engine 1 | 삭제 후보 |
| `_psrr_telescopic_class_ab` | sizing_recipe.py:5272 | 54 | engine 1 | 삭제 후보 |
| `_psrr_telescopic_class_ab_cmfb` | sizing_recipe.py:5328 | 34 | engine 1 | 삭제 후보 |
| `_optimize_theta_slsqp_block_coordinate` | sizing_recipe.py:11680 | 166 | engine 1 | 삭제 후보(또는 optimizer로 이관 후 실측) |
| `SharedFingerWCandidate` | stick_diagram.py:6381 | 5 | engine 1 | stick_diagram 유지 또는 삭제 |
