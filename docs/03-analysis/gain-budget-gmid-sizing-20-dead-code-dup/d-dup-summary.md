# Phase 2 실측 입력 -- D 48 / DUP 19 호출부 전수 (AST 기준)

- 생성: `scan.py`(참조 인덱스) + `scan2.py`(호출자 귀속·도달성) + `summarize.py`. 전부 스크래치패드. 저장소는 읽기만 했다.
- AST `ast.Name`/`ast.Attribute` 단일 패스 인덱스. 정의 헤더 줄과 **자기 본문 안 참조는 제외**.
- 스캔 대상 .py **202개** = engine 7 / test 21 / probe 42 / workspaces 40 / tools 20 / docs_py 45(`docs/03-analysis/*-function-audit` 감사 스크립트) / other 23(hooks, project-template, agent-kit, kb-global) / other_skills 4.
  `.claude/worktrees/**`(엔진 사본 2벌)는 **제외**했다 -- 포함하면 호출부가 중복 집계된다.
- `docs 언급`은 `docs/**.md|json` 텍스트 언급 수(코드 아님, 60에서 절단).
- `Class.method` 항목(`GmIdLUT.junction_cap`, `SemiEmpiricalGmIdLUT.fT`)은 **`ast.Attribute`만** 셌다(같은 이름의 지역변수 `fT`가 8건 오검출된 것을 제거).
- ⚠️ 아래 '이관 목적지'·'비고'에 보이는 `…`(U+2026)는 **레지스트리 원문에 이미 들어 있는 절단**이다(예: `.function-registry.md:448`에 U+2026이 실재). 이 문서의 추출이 자른 것이 아니다 -- 레지스트리 셀 자체가 잘려 있어 원 근거를 따라가려면 소스를 다시 봐야 한다.

### 이 실측에서 확인된 사실 (판단 아님, 관측)

1. **§7 D 48개 중 9개는 운영 경로에 살아 있는 참조가 있다**(묶음 `A_live_ops`). §7 제목 '운영 경로 호출 0'과 어긋난다.
2. **§2 W 계산 정본 `size_transistor`의 엔진 호출부는 1곳뿐이고, 그 1곳이 D 함수다**: `sizing_recipe.py:140` = `converge_with_parasitics`(이 문서 D 3번, 저장소 전체 참조 0). 즉 정본 쪽이 엔진에서 사실상 dead이고 인라인 사본이 살아 있다.
3. **§2가 적은 인라인 W 사본 위치(“`find_optimal_sizing:941`, `feasible_gm_ids:1756`, `search_gm_id_for_role:2234`, `feasible_L_window:2746`” 4곳)는 현 소스와 맞지 않는다.** 현재 `W = L*ID/IDu` 형태 대입은 `size_transistor` 밖에 **6곳**이다: `find_optimal_sizing:946`, `diode_vds_window:3645`, `solve_stacked_diode_pair:3723`, `solve_stacked_diode_pair:3746`, `apply_diode_self_consistent_gm_id:3873`, `make_matching_feasibility_check.check:7393`. `feasible_gm_ids`(1750-1761)·`feasible_L_window`(2705-2771)에는 그 식이 **docstring에만** 남아 있고, `search_gm_id_for_role`(2159-2305)도 본문에 인라인 대입이 없다(언급은 주석 2222행).
4. **DF-29가 '운영 metric 세 개'라 부른 `_cmrr_telescopic_class_ab_cmfb`·`_psrr_telescopic_class_ab`·`_psrr_telescopic_class_ab_cmfb`는 어떤 library 회로도 고르지 않는다.** `library/*.topology.json` 10개의 metrics를 재귀 파싱한 결과 데이터에 실재하는 `circuit_family` 값은 `diff_pair_tail` 4건뿐이다(`folded_cascode.topology.json` cmrr_db·psrr_db, `nmcnr_amplifier.topology.json` cmrr_db·psrr_db). `telescopic_class_ab`·`telescopic_class_ab_cmfb`는 **0건**이다(`current_reuse_telescopic_ota.topology.json`은 `_cmrr_psrr_estimate_db_comment`대로 `type=smallsignal_ratio_db`로 이미 교체됨). 이 4개 함수의 `engine_live` 참조는 전부 모듈 레벨 `_CMRR_ESTIMATOR_REGISTRY`(5253~5257)/`_PSRR_ESTIMATOR_REGISTRY`(5364~5368) **등록 항목**이지 호출이 아니다.
5. 데이터가 실제로 고르는 metric type census(library 10개 topology, 재귀): `sum_current` 4, `sum_area` 2, `input_referred_offset` 2, `smallsignal_ratio_db` 2, `smallsignal_gain_db` 2, `rail_referenced_voltage` 2, `nulling_resistor_ohm` 2, `cmrr_estimate` 2, `psrr_estimate` 2, 그리고 1건씩 `gain_stages_sum`·`flicker_plus_thermal_sum`·`battery_centering_deviation`·`mirror_ratio_error`·`supply_current`·`kcl_residual`·`stack_headroom_slack`·`parasitic_pm_deg`·`mirror_ratio_error_input_referred`·**`folded_cascode_gain_db`·`folded_cascode_pm_deg`·`nmcnr_gain_db`·`nmcnr_pm_deg`**. 즉 DUP 5·6번(`_metric_folded_cascode_gain_db`/`_pm_deg`)은 데이터가 실제로 고르는 metric이고, DUP 8번(`_cmrr_diff_pair_tail`)도 4건이 고른다 -- 삭제 전 대체가 필요한 쪽이다.
6. `render_report`(design report 텍스트 리포트)의 유일한 참조는 `audit_current_forced.py:178`의 `if __name__ == "__main__"` 블록이다 -- 즉 그 파일의 CLI 진입점이며 test/harness 경로에는 없다.
7. `search_shared_finger_w`(`SharedFingerWCandidate`의 유일한 생성자)는 `run_harness.py`에서 도달하지 않고 `workspaces/current-reuse-telescopic-ota-report/stick.py`에서만 쓰인다.
8. **`engine_live` 태그가 `<module>`인 항목은 AST만으로는 판정이 끝나지 않는다** -- 전부 레지스트리 dict 등록이라, 실제 발동 여부는 **library 데이터가 그 키를 고르는가**로 갈린다. 실측 결과 두 갈래로 나뉜다: (a) **데이터가 고름** -- `_metric_folded_cascode_gain_db`/`_metric_folded_cascode_pm_deg`(`folded_cascode.topology.json`), `_cmrr_diff_pair_tail`/`_psrr_diff_pair_tail`(4건). (b) **데이터가 안 고름** -- `_cmrr_telescopic_class_ab`, `_cmrr_telescopic_class_ab_cmfb`, `_psrr_telescopic_class_ab`, `_psrr_telescopic_class_ab_cmfb`(0건), `_run_optimize_multistage_case`(`_REGRESSION_ENGINES`의 유일 항목이고 그 소비자 `run_regression_case`의 참조는 test 1건뿐 -> test 전용 사슬).
9. `_telescopic_*` 체인 전체가 하나의 죽은 덩어리다: `_cmrr_telescopic_class_ab`/`_cmrr_telescopic_class_ab_cmfb`/`_psrr_telescopic_class_ab`/`_psrr_telescopic_class_ab_cmfb`(레지스트리 등록만) -> `_telescopic_class_ab_open_loop_gains` -> `_telescopic_class_ab_open_loop_response` -> `_telescopic_open_loop_device_names` -> `_load_telescopic_topology_cached`, 그리고 `_cmfb_amp_gain_diode_load`. 8개 함수 합계 약 380줄(정의 줄수 합)이 한 번에 죽는다. 바깥 소비자는 `workspaces/.../diagnose_cmrr_cmfb.py`(2건)와 test(4건)뿐이다.

### 묶음 정의

- **운영 경로** = engine + workspaces + tools. **비운영** = test + probe. **감사 스크립트** = docs_py/other.
- engine 참조는 다시 **호출자 귀속**으로 나눴다(`scan2.py`): 호출자가 (a) §7 D 목록 함수면 `engine_caller_is_D`, (b) §6 DUP 함수면 `engine_caller_is_DUP`, (c) self-test면 `engine_selftest`, (d) `__main__` 블록이면 `engine_cli_main`, 그 밖이면 `engine_live`. (a)(b)(c)는 운영 경로 참조로 세지 않는다 -- 부르는 쪽도 죽어 있기 때문이다.

## A. D 48개 -- 호출부 묶음 요약

| 묶음 | 개수 | 함수 |
|---|---|---|
| **호출부 0** -- 저장소 전체에서 참조 0 | 7 | `converge_with_parasitics`, `slew_rate`, `SemiEmpiricalGmIdLUT.fT`, `lut_conditions_from_npz`, `suggest_headroom_stack_groups`, `render_stick_diagram`, `derived_spec` |
| 감사 스크립트(docs/**/*.py)에만 있음 | 0 |  |
| **test/probe에만** 있음 | 17 | `run_regression_case`, `solve_diode_stack_current`, `estimate_area_budget`, `signal_path_nodes`, `node_pole_estimate`, `validate_theta_declaration_order`, `load_derived_bounds`, `find_interleaved_symmetric_splits`, `find_differential_and_mirror_forks`, `check_multi_leaf_hub_parity`, `find_diode_stacks`, `audit_theta_root_direction`, `propose_theta_kcl_gap_fill`, `apply_theta_kcl_gap_fill`, `apply_device_roles_gap_fill`, `audit_vertical_stack_id_euler_feasibility`, `find_euler_repair_options` |
| 엔진 참조가 있으나 **부르는 쪽도 D/self-test**(= 운영 경로 아님) | 12 | `GmIdLUT.junction_cap`, `_invq_newton`, `RegressionVerdict`, `_load_telescopic_topology_cached`, `_telescopic_class_ab_open_loop_response`, `_telescopic_open_loop_device_names`, `_telescopic_class_ab_open_loop_gains`, `MirrorSymmetryVerdict`, `find_idiom_matches`, `MultiLeafHubParityVerdict`, `DiodeStackMember`, `DiodeStack` |
| workspaces 진단 스크립트에만 있음(run_harness 아님) | 3 | `build_toy_lut`, `_cmfb_amp_gain_diode_load`, `check_mirror_symmetry` |
| **운영 경로에 살아 있는 참조**(살아 있는 engine 호출부 / run_harness / tools / CLI main) | 9 | `gm_from_fT`, `_run_optimize_multistage_case`, `_cmrr_telescopic_class_ab`, `_cmrr_telescopic_class_ab_cmfb`, `_psrr_telescopic_class_ab`, `_psrr_telescopic_class_ab_cmfb`, `_optimize_theta_slsqp_block_coordinate`, `SharedFingerWCandidate`, `render_report` |

합계 48. 레지스트리 §7은 이 48개 전부를 '운영 경로 호출 0'으로 등급했다 -- 마지막 두 묶음은 그 등급과 어긋나므로 design에서 재판정 대상이다.

## B. D 48개 -- 항목별

| # | 함수 | 파일:줄 | 줄수 | 묶음 | engine | test | probe | ws | tools | 기타 | docs 언급 | 참조 태그 | harness 도달 | DF | 이관 목적지(원문) |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 1 | `GmIdLUT.junction_cap` | sizing_recipe.py:76 | 19 | B2_dead_engine_caller_only | 1 | 0 | 0 | 0 | 0 | 0 | 3 | engine_caller_is_D:1 | n | - | gmid_sizing_engine.py(배선 시) 또는 삭제 |
| 2 | `gm_from_fT` | sizing_recipe.py:101 | 3 | A_live_ops | 2 | 0 | 0 | 0 | 0 | 0 | 3 | engine_caller_is_D:1 engine_live:1 | Y | - | gmid_sizing_engine.py |
| 3 | `converge_with_parasitics` | sizing_recipe.py:126 | 31 | D_zero | 0 | 0 | 0 | 0 | 0 | 0 | 13 | - | n | - | gmid_sizing_engine.py 또는 tests 데모 |
| 4 | `slew_rate` | sizing_recipe.py:179 | 3 | D_zero | 0 | 0 | 0 | 0 | 0 | 0 | 17 | - | n | - | 삭제 후보 |
| 5 | `SemiEmpiricalGmIdLUT.fT` | sizing_recipe.py:674 | 8 | D_zero | 0 | 0 | 0 | 0 | 0 | 0 | 61 | - | Y | - | 삭제 후보(또는 준정적 검증에 배선) |
| 6 | `_invq_newton` | sizing_recipe.py:1401 | 11 | B2_dead_engine_caller_only | 1 | 0 | 0 | 0 | 0 | 0 | 3 | engine_caller_is_D:1 | n | - | tests/ 픽스처(삭제 아님) |
| 7 | `build_toy_lut` | sizing_recipe.py:1414 | 39 | A2_ws_diag_script | 0 | 3 | 0 | 1 | 0 | 0 | 10 | test:3 workspaces_script:1 | n | - | tests/ 픽스처(§8.8 test 분리 시 이관) |
| 8 | `RegressionVerdict` | sizing_recipe.py:1495 | 5 | B2_dead_engine_caller_only | 7 | 0 | 0 | 0 | 0 | 0 | 4 | engine_caller_is_D:7 | n | - | tests/(회귀 러너와 함께 이관, 삭제 아님) |
| 9 | `_run_optimize_multistage_case` | sizing_recipe.py:1502 | 24 | A_live_ops | 1 | 0 | 0 | 0 | 0 | 0 | 4 | engine_live:1 | Y | - | tests/ |
| 10 | `run_regression_case` | sizing_recipe.py:1535 | 61 | B_test_probe_only | 0 | 1 | 0 | 0 | 0 | 0 | 11 | test:1 | n | - | tests/(골든 회귀는 가치 있음 -- 이관) |
| 11 | `solve_diode_stack_current` | sizing_recipe.py:1671 | 50 | B_test_probe_only | 0 | 1 | 0 | 0 | 0 | 0 | 23 | test:1 | n | - | 삭제 후보 |
| 12 | `estimate_area_budget` | sizing_recipe.py:2937 | 30 | B_test_probe_only | 0 | 2 | 0 | 0 | 0 | 0 | 31 | test:2 | n | DF-09 | sizing_layout_convergence.py(배선 시) |
| 13 | `signal_path_nodes` | sizing_recipe.py:4059 | 35 | B_test_probe_only | 0 | 0 | 1 | 0 | 0 | 1 | 27 | docs_py:1 probe:1 | n | - | (삭제 후보) |
| 14 | `node_pole_estimate` | sizing_recipe.py:4096 | 74 | B_test_probe_only | 0 | 0 | 1 | 0 | 0 | 0 | 29 | probe:1 | n | DF-06 | (삭제 후보) |
| 15 | `_cmrr_telescopic_class_ab` | sizing_recipe.py:4853 | 80 | A_live_ops | 1 | 0 | 0 | 0 | 0 | 0 | 20 | engine_live:1 | Y | DF-29 | (삭제 후보) |
| 16 | `_cmfb_amp_gain_diode_load` | sizing_recipe.py:4935 | 49 | A2_ws_diag_script | 2 | 2 | 0 | 2 | 0 | 0 | 6 | engine_caller_is_D:2 test:2 workspaces_script:2 | Y | - | (삭제 후보) |
| 17 | `_load_telescopic_topology_cached` | sizing_recipe.py:5061 | 14 | B2_dead_engine_caller_only | 1 | 0 | 0 | 0 | 0 | 0 | 9 | engine_caller_is_D:1 | Y | DF-29 | 삭제 후보 |
| 18 | `_telescopic_class_ab_open_loop_response` | sizing_recipe.py:5080 | 38 | B2_dead_engine_caller_only | 4 | 0 | 0 | 0 | 0 | 0 | 9 | engine_caller_is_D:4 | Y | DF-29 | 삭제 후보 |
| 19 | `_telescopic_open_loop_device_names` | sizing_recipe.py:5131 | 13 | B2_dead_engine_caller_only | 2 | 0 | 0 | 0 | 0 | 0 | 4 | engine_caller_is_D:2 | Y | - | 삭제 후보 |
| 20 | `_telescopic_class_ab_open_loop_gains` | sizing_recipe.py:5146 | 38 | B2_dead_engine_caller_only | 2 | 2 | 0 | 0 | 0 | 0 | 5 | engine_caller_is_D:2 test:2 | Y | - | 삭제 후보 |
| 21 | `_cmrr_telescopic_class_ab_cmfb` | sizing_recipe.py:5186 | 65 | A_live_ops | 1 | 0 | 0 | 0 | 0 | 0 | 12 | engine_live:1 | Y | DF-29 | 삭제 후보 |
| 22 | `_psrr_telescopic_class_ab` | sizing_recipe.py:5272 | 54 | A_live_ops | 1 | 0 | 0 | 0 | 0 | 0 | 13 | engine_live:1 | Y | DF-29 | 삭제 후보 |
| 23 | `_psrr_telescopic_class_ab_cmfb` | sizing_recipe.py:5328 | 34 | A_live_ops | 1 | 0 | 0 | 0 | 0 | 0 | 10 | engine_live:1 | Y | DF-29 | 삭제 후보 |
| 24 | `lut_conditions_from_npz` | sizing_recipe.py:5371 | 22 | D_zero | 0 | 0 | 0 | 0 | 0 | 0 | 19 | - | n | - | circuit_state_graph S0(LUT 생성메타 해시) |
| 25 | `validate_theta_declaration_order` | sizing_recipe.py:6885 | 93 | B_test_probe_only | 0 | 5 | 0 | 0 | 0 | 0 | 20 | test:5 | n | - | topology_authoring |
| 26 | `load_derived_bounds` | sizing_recipe.py:8301 | 8 | B_test_probe_only | 0 | 1 | 0 | 0 | 0 | 0 | 6 | test:1 | n | - | optimizer S3(흡수) 또는 삭제 |
| 27 | `_optimize_theta_slsqp_block_coordinate` | sizing_recipe.py:11680 | 166 | A_live_ops | 1 | 0 | 0 | 0 | 0 | 0 | 5 | engine_live:1 | Y | - | 삭제 후보(또는 optimizer로 이관 후 실측) |
| 28 | `MirrorSymmetryVerdict` | stick_diagram.py:234 | 2 | B2_dead_engine_caller_only | 2 | 0 | 0 | 0 | 0 | 0 | 5 | engine_caller_is_D:2 | n | - | stick_diagram(삭제 후보) |
| 29 | `check_mirror_symmetry` | stick_diagram.py:238 | 19 | A2_ws_diag_script | 0 | 0 | 0 | 1 | 0 | 0 | 15 | workspaces_script:1 | n | - | stick_diagram 유지 또는 test util |
| 30 | `find_interleaved_symmetric_splits` | stick_diagram.py:259 | 32 | B_test_probe_only | 0 | 1 | 0 | 0 | 0 | 0 | 5 | test:1 | n | - | test util |
| 31 | `find_idiom_matches` | stick_diagram.py:1095 | 20 | B2_dead_engine_caller_only | 2 | 8 | 0 | 0 | 0 | 0 | 9 | engine_caller_is_D:2 test:8 | n | - | topology_authoring |
| 32 | `find_differential_and_mirror_forks` | stick_diagram.py:1321 | 74 | B_test_probe_only | 0 | 2 | 0 | 0 | 0 | 0 | 7 | test:2 | n | - | 삭제 후보 |
| 33 | `suggest_headroom_stack_groups` | stick_diagram.py:1538 | 148 | D_zero | 0 | 0 | 0 | 0 | 0 | 0 | 5 | - | n | - | 삭제 후보 |
| 34 | `MultiLeafHubParityVerdict` | stick_diagram.py:2984 | 4 | B2_dead_engine_caller_only | 4 | 0 | 0 | 0 | 0 | 0 | 5 | engine_caller_is_D:4 | n | - | test util |
| 35 | `check_multi_leaf_hub_parity` | stick_diagram.py:2990 | 39 | B_test_probe_only | 0 | 2 | 0 | 0 | 0 | 0 | 12 | test:2 | n | - | test util |
| 36 | `DiodeStackMember` | stick_diagram.py:3094 | 4 | B2_dead_engine_caller_only | 1 | 0 | 0 | 0 | 0 | 0 | 3 | engine_caller_is_D:1 | n | - | - |
| 37 | `DiodeStack` | stick_diagram.py:3102 | 3 | B2_dead_engine_caller_only | 1 | 0 | 0 | 0 | 0 | 0 | 6 | engine_caller_is_D:1 | n | - | - |
| 38 | `find_diode_stacks` | stick_diagram.py:3107 | 29 | B_test_probe_only | 0 | 2 | 0 | 0 | 0 | 0 | 45 | test:2 | n | - | circuit_state_graph(diode 정의 1개로 통합) |
| 39 | `audit_theta_root_direction` | stick_diagram.py:3525 | 79 | B_test_probe_only | 0 | 6 | 0 | 0 | 0 | 0 | 16 | test:6 | n | - | topology_authoring(배선 여부 승인 필요) |
| 40 | `propose_theta_kcl_gap_fill` | stick_diagram.py:3626 | 346 | B_test_probe_only | 0 | 6 | 0 | 0 | 0 | 0 | 14 | test:6 | n | - | topology_authoring(배선 승인 필요) |
| 41 | `apply_theta_kcl_gap_fill` | stick_diagram.py:3974 | 53 | B_test_probe_only | 0 | 1 | 0 | 0 | 0 | 0 | 9 | test:1 | n | - | topology_authoring |
| 42 | `apply_device_roles_gap_fill` | stick_diagram.py:4737 | 63 | B_test_probe_only | 0 | 4 | 0 | 0 | 0 | 0 | 10 | test:4 | n | - | topology_authoring |
| 43 | `audit_vertical_stack_id_euler_feasibility` | stick_diagram.py:5016 | 98 | B_test_probe_only | 0 | 3 | 0 | 0 | 0 | 0 | 17 | test:3 | n | - | stick_diagram(배선 여부 승인 필요) |
| 44 | `find_euler_repair_options` | stick_diagram.py:5280 | 65 | B_test_probe_only | 0 | 3 | 0 | 0 | 0 | 0 | 16 | test:3 | n | - | stick_diagram(배선 승인 필요) |
| 45 | `SharedFingerWCandidate` | stick_diagram.py:6381 | 5 | A_live_ops | 1 | 0 | 0 | 0 | 0 | 0 | 3 | engine_live:1 | n | - | stick_diagram 유지 또는 삭제 |
| 46 | `render_stick_diagram` | stick_diagram.py:6901 | 21 | D_zero | 0 | 0 | 0 | 0 | 0 | 0 | 4 | - | n | - | test fixture/유틸 |
| 47 | `render_report` | audit_current_forced.py:129 | 29 | A_live_ops | 1 | 0 | 0 | 0 | 0 | 0 | 6 | engine_cli_main:1 | n | - | §8.3 게이트 배선 후보 |
| 48 | `derived_spec` | (정의 못 찾음) | 0 | D_zero | 0 | 0 | 0 | 0 | 0 | 0 | 11 | - | n | - | 〃 |

`harness 도달`은 **과대근사**다: 엔진 호출그래프에서 `run_harness.py`가 직접 쓰는 이름 9개(`SemiEmpiricalGmIdLUT`, `assemble_report_data`, `dense_candidates`, `diagnose_sizing_roles_gap`, `layout_grid_L_candidates`, `optimize_full_circuit_budget`, `run_full_circuit_audit_from_topology`, `save_html_report`, `save_instance_json`)와 **엔진 모듈 레벨 참조**(레지스트리 dict 등록 포함)에서 전파한 것이라, 레지스트리에 등록만 되고 실제로는 어떤 회로도 고르지 않는 함수도 Y가 된다. 따라서 `n`은 dead의 강한 증거, `Y`는 live의 약한 증거다.

### B-1. 운영 경로 참조 상세 -- 삭제 시 직접 영향 (묶음 A_live_ops / A2)

**`gm_from_fT`** (engine=2)
  - [engine / engine_caller_is_D] skills/analog-gmid-design/assets/sizing_recipe.py:139  안: `converge_with_parasitics`  --  `gm = gm_from_fT(fT, C)`
  - [engine / engine_live] skills/analog-gmid-design/assets/sizing_recipe.py:932  안: `find_optimal_sizing`  --  `gm = gm_from_fT(fT, C)`

**`_run_optimize_multistage_case`** (engine=1)
  - [engine / engine_live] skills/analog-gmid-design/assets/sizing_recipe.py:1529  안: `<module>`  --  `"optimize_multistage": _run_optimize_multistage_case,`

**`_cmrr_telescopic_class_ab`** (engine=1)
  - [engine / engine_live] skills/analog-gmid-design/assets/sizing_recipe.py:5255  안: `<module>`  --  `"telescopic_class_ab": _cmrr_telescopic_class_ab,`

**`_cmrr_telescopic_class_ab_cmfb`** (engine=1)
  - [engine / engine_live] skills/analog-gmid-design/assets/sizing_recipe.py:5256  안: `<module>`  --  `"telescopic_class_ab_cmfb": _cmrr_telescopic_class_ab_cmfb,   # 배치 7-5b(2026-08-03)`

**`_psrr_telescopic_class_ab`** (engine=1)
  - [engine / engine_live] skills/analog-gmid-design/assets/sizing_recipe.py:5366  안: `<module>`  --  `"telescopic_class_ab": _psrr_telescopic_class_ab,               # 세션20`

**`_psrr_telescopic_class_ab_cmfb`** (engine=1)
  - [engine / engine_live] skills/analog-gmid-design/assets/sizing_recipe.py:5367  안: `<module>`  --  `"telescopic_class_ab_cmfb": _psrr_telescopic_class_ab_cmfb,     # 세션20`

**`_optimize_theta_slsqp_block_coordinate`** (engine=1)
  - [engine / engine_live] skills/analog-gmid-design/assets/sizing_recipe.py:9758  안: `optimize_full_circuit_budget`  --  `theta_star, sizing, metrics_result = _optimize_theta_slsqp_block_coordinate(`

**`SharedFingerWCandidate`** (engine=1)
  - [engine / engine_live] skills/analog-gmid-design/assets/stick_diagram.py:6437  안: `search_shared_finger_w`  --  `results.append(SharedFingerWCandidate(`

**`render_report`** (engine=1)
  - [engine / engine_cli_main] skills/analog-gmid-design/assets/audit_current_forced.py:178  안: `<__main__ block>`  --  `report, has_violation = render_report(path)`

**`build_toy_lut`** (test=3 workspaces=1)
  - [workspaces / workspaces_script] workspaces/current-reuse-telescopic-ota-report/probe_group_split_wiring.py:9  안: `<module>`  --  `lut = build_toy_lut()`

**`_cmfb_amp_gain_diode_load`** (engine=2 test=2 workspaces=2)
  - [engine / engine_caller_is_D] skills/analog-gmid-design/assets/sizing_recipe.py:5241  안: `_cmrr_telescopic_class_ab_cmfb`  --  `A_c = _cmfb_amp_gain_diode_load(metric_spec, ctx)`
  - [engine / engine_caller_is_D] skills/analog-gmid-design/assets/sizing_recipe.py:5354  안: `_psrr_telescopic_class_ab_cmfb`  --  `A_c = _cmfb_amp_gain_diode_load(metric_spec, ctx)`
  - [workspaces / workspaces_script] workspaces/current-reuse-telescopic-ota-report/diagnose_cmrr_cmfb.py:122  안: `<module>`  --  `A_c = _cmfb_amp_gain_diode_load(mspec, ctx)`
  - [workspaces / workspaces_script] workspaces/current-reuse-telescopic-ota-report/diagnose_cmrr_cmfb.py:168  안: `<module>`  --  `ac = _cmfb_amp_gain_diode_load(mspec, ctx)`

**`check_mirror_symmetry`** (workspaces=1)
  - [workspaces / workspaces_script] workspaces/current-reuse-telescopic-ota-report/stick.py:165  안: `<module>`  --  `ok = check_mirror_symmetry(seq, pm).ok if seq else None`

### B-2. 삭제 시 같이 죽는 후보 -- 각 D 함수가 부르는 엔진 함수

| 함수 | 줄수 | 부르는 엔진 함수(이름:줄) |
|---|---|---|
| `GmIdLUT.junction_cap` | 19 | (없음) |
| `gm_from_fT` | 3 | (없음) |
| `converge_with_parasitics` | 31 | `gm_from_fT`:139, `gm_gds_ratio`:155, `junction_cap`:141, `size_transistor`:140 |
| `slew_rate` | 3 | (없음) |
| `SemiEmpiricalGmIdLUT.fT` | 8 | `_query`:679,680, `_solve_vgs`:676 |
| `_invq_newton` | 11 | (없음) |
| `build_toy_lut` | 39 | `SemiEmpiricalGmIdLUT`:1452, `_invq_newton`:1440 |
| `RegressionVerdict` | 5 | (없음) |
| `_run_optimize_multistage_case` | 24 | `optimize_multistage`:1515 |
| `run_regression_case` | 61 | `RegressionVerdict`:1549,1556,1580, `SemiEmpiricalGmIdLUT`:1565,1567 |
| `solve_diode_stack_current` | 50 | `_invert_gm_id_for_current`:1700, `_vgs_sum`:1705,1712, `vgs_for_gm_id`:1701 |
| `estimate_area_budget` | 30 | (없음) |
| `signal_path_nodes` | 35 | `_reach`:4093, `add`:4080,4081,4089 |
| `node_pole_estimate` | 74 | `cgg_absolute`:4152 |
| `_cmrr_telescopic_class_ab` | 80 | (없음) |
| `_cmfb_amp_gain_diode_load` | 49 | `g`:4971,4972,4973 |
| `_load_telescopic_topology_cached` | 14 | `load_topology`:5072 |
| `_telescopic_class_ab_open_loop_response` | 38 | `_load_telescopic_topology_cached`:5099, `_mna_solve_smallsignal`:5116, `_telescopic_open_loop_device_names`:5100, `add`:5112 |
| `_telescopic_open_loop_device_names` | 13 | (없음) |
| `_telescopic_class_ab_open_loop_gains` | 38 | `_hashable_key`:5168, `_telescopic_class_ab_open_loop_response`:5173,5175,5177, `_telescopic_open_loop_device_names`:5167 |
| `_cmrr_telescopic_class_ab_cmfb` | 65 | `_cmfb_amp_gain_diode_load`:5241, `_telescopic_class_ab_open_loop_gains`:5234 |
| `_psrr_telescopic_class_ab` | 54 | (없음) |
| `_psrr_telescopic_class_ab_cmfb` | 34 | `_cmfb_amp_gain_diode_load`:5354, `_telescopic_class_ab_open_loop_gains`:5347 |
| `lut_conditions_from_npz` | 22 | (없음) |
| `validate_theta_declaration_order` | 93 | `_build_shared_current_joint_plan`:6939, `_shared_current_groups_from_compensation`:6938, `add`:6976 |
| `load_derived_bounds` | 8 | `derived_bounds_path`:8304 |
| `_optimize_theta_slsqp_block_coordinate` | 166 | `_optimize_theta_slsqp`:11768,11782,11825 |
| `MirrorSymmetryVerdict` | 2 | (없음) |
| `check_mirror_symmetry` | 19 | `MirrorSymmetryVerdict`:256 |
| `find_interleaved_symmetric_splits` | 32 | (없음) |
| `find_idiom_matches` | 20 | `_import_analog_grammar`:1106, `_to_analog_grammar_devs`:1109 |
| `find_differential_and_mirror_forks` | 74 | `_classify_forks`:1393,1394, `_forks_of`:1371, `_import_analog_grammar`:1346, `_to_analog_grammar_devs`:1349, `add`:1366, `gate_class`:1380, `gate_of`:1360,1378, `trace_gnd_to_vdd_branches`:1390, `trace_vdd_to_gnd_branches`:1388 |
| `suggest_headroom_stack_groups` | 148 | `_explode_mixed`:1628, `_group_name`:1674,1675,1683, `_is_hub_composite`:1633,1642,1655, `add`:1660,1668, `suggest_vertical_stack_composites`:1580 |
| `MultiLeafHubParityVerdict` | 4 | (없음) |
| `check_multi_leaf_hub_parity` | 39 | `MultiLeafHubParityVerdict`:3025,3027,3028 |
| `DiodeStackMember` | 4 | (없음) |
| `DiodeStack` | 3 | (없음) |
| `find_diode_stacks` | 29 | `DiodeStack`:3134, `DiodeStackMember`:3132 |
| `audit_theta_root_direction` | 79 | `_import_analog_grammar`:3564, `_to_analog_grammar_devs`:3567, `find_idiom_matches`:3570 |
| `propose_theta_kcl_gap_fill` | 346 | `_import_analog_grammar`:3712, `_kcl_terminal_sign`:3873,3878, `_mark`:3792,3805,3829, `_run_rules_1_to_3`:3890,3934, `_to_analog_grammar_devs`:3716, `add`:3775, `find_idiom_matches`:3721 |
| `apply_theta_kcl_gap_fill` | 53 | (없음) |
| `apply_device_roles_gap_fill` | 63 | `add`:4762,4770 |
| `audit_vertical_stack_id_euler_feasibility` | 98 | `_verified_euler_fix`:5106, `build_graph`:5094, `check_euler_condition`:5094 |
| `find_euler_repair_options` | 65 | `_verified_euler_fix`:5323,5335 |
| `SharedFingerWCandidate` | 5 | (없음) |
| `render_stick_diagram` | 21 | (없음) |
| `render_report` | 29 | `audit_topology`:132 |
| `derived_spec` | - | (정의 없음) |

### B-3. 레지스트리 원문(이관 목적지 / 비고) -- 절단 없이

1. `GmIdLUT.junction_cap` [sizing_recipe.py (27)]
   - 책임: Jespers jctCap 1차 근사 CJD(원문 예시 unit-cap 기본값 CJ=1e-15 등)
   - 이관 목적지: gmid_sizing_engine.py(배선 시) 또는 삭제
   - 비고: 기본값이 원문 예시 상수(77, 80-81). 운영에 배선하려면 PDK 값에서 읽어야 함. 삭제/배선은 사용자 판단 필요
2. `gm_from_fT` [sizing_recipe.py (27)]
   - 책임: gm=2π·fT·C
   - 이관 목적지: gmid_sizing_engine.py
   - 비고: 1줄 순수함수, 데모·단일소자 경로용. 삭제 이득 없음
3. `converge_with_parasitics` [sizing_recipe.py (27)]
   - 책임: 기생 CJD 반복 수렴(발산하면 ValueError)
   - 이관 목적지: gmid_sizing_engine.py 또는 tests 데모
   - 비고: 발산 판정 `20*C_external`(143) 매직넘버. 운영 경로에서 기생 반영은 `optimize_multistage`의 cgg 반복이 대신 함. 배선 또는 삭제는 사용자 승인 필요
4. `slew_rate` [sizing_recipe.py (27)]
   - 책임: ID/C
   - 이관 목적지: 삭제 후보
   - 비고: 완전 dead. slew metric이 필요하면 `_METRICS_REGISTRY`에 metric으로 넣을 것
5. `SemiEmpiricalGmIdLUT.fT` [sizing_recipe.py (27)]
   - 책임: fT=gm/(2πCgg)
   - 이관 목적지: 삭제 후보(또는 준정적 검증에 배선)
   - 비고: `find_optimal_sizing`의 준정적 검증은 `check_quasi_static`+cgg로 따로 계산하므로 이 메서드는 안 쓰임
6. `_invq_newton` [sizing_recipe.py (27)]
   - 책임: EKV q 뉴턴 역산
   - 이관 목적지: tests/ 픽스처(삭제 아님)
   - 비고: toy 전용
7. `build_toy_lut` [sizing_recipe.py (27)]
   - 책임: EKV 합성 4D LUT
   - 이관 목적지: tests/ 픽스처(§8.8 test 분리 시 이관)
   - 비고: VA=5V/um, Cox 5e-15 등 toy 상수(1428,1432) -- 픽스처로만 쓸 것
8. `RegressionVerdict` [sizing_recipe.py (27)]
   - 책임: 회귀 판정 dataclass
   - 이관 목적지: tests/(회귀 러너와 함께 이관, 삭제 아님)
   - 비고: 
9. `_run_optimize_multistage_case` [sizing_recipe.py (27)]
   - 책임: reference JSON case로 optimize_multistage 실행 / engine 문자열 디스패치
   - 이관 목적지: tests/
   - 비고: 엔진 등록은 optimize_multistage 하나뿐(1524)
10. `run_regression_case` [sizing_recipe.py (27)]
   - 책임: 공정별 골든 JSON 로드 → 실행 → 상대오차 대조
   - 이관 목적지: tests/(골든 회귀는 가치 있음 -- 이관)
   - 비고: `W_ref=5e-6` 하드코딩(1561,1563) -- LUT npz 메타에서 읽어야 함(C-d/S0 지문 대상). `except (ValueError, KeyError)`를 실패 verdict로 바꾸는 건 테스트 러너라 허용
11. `solve_diode_stack_current` [sizing_recipe.py (27)]
   - 책임: 직렬 diode 스택 VGS합=target이 되는 전류 로그축 이분탐색
   - 이관 목적지: 삭제 후보
   - 비고: 적층 diode 문제의 운영 해법은 `solve_stacked_diode_pair`(3659, B25, 호출 7859)로 대체됨. 개념 중복 -- 삭제는 사용자 승인 필요
12. `estimate_area_budget` [sizing_recipe.py (27)]
   - 책임: n_fingers × pitch로 A_1D, packing_density 표본이 있으면 A_1D/density, 없으면 콜드스타트 블렌딩
   - 이관 목적지: sizing_layout_convergence.py(배선 시)
   - 비고: **공식 결함**: 콜드스타트 `(1-α)·A_1D + α·(A_1D/α)` = `(2-α)·A_1D`(2954-2955) -- α가 서로 상쇄돼 블렌딩이 아니다(α=0.65면 1.35·A_1D). self-test(13882-13884)가 **같은 식을 다시 써서** 비교하므로 잡지 못함(동어반복 테스…
   - DF: DF-09
13. `signal_path_nodes` [sizing_recipe.py (27)]
   - 책임: gate/source->drain 방향 그래프에서 excite∩sense 도달 내부노드
   - 이관 목적지: (삭제 후보)
   - 비고: 4354-4356 docstring이 L2에서 "원천적으로 필요 없어짐"이라 명시. §12.4가 소비자라 적은 것이 오류임을 재확인. 방향 규칙이 단일 DAG가 안 됨(§12.3-9) -> S1v 재활용 가치 낮음
14. `node_pole_estimate` [sizing_recipe.py (27)]
   - 책임: 노드별 G/C 1차 pole 추정
   - 이관 목적지: (삭제 후보)
   - 비고: 4343-4346: L1 값(34.2도) 무효라고 자인. **§12.6-6 광범위 except 4138 확인**: `except (KeyError, ValueError): pass`로 Cgg 누락을 조용히 버림 -- 운영 미호출이라 영향은 probe 한정
   - DF: DF-06
15. `_cmrr_telescopic_class_ab` [sizing_recipe.py (27)]
   - 책임: current-reuse 1단 open-loop CMRR 폐형식
   - 이관 목적지: (삭제 후보)
   - 비고: 파일럿이 `smallsignal_ratio_db`로 교체(JSON 1871,1873). 참조는 self-test와 `workspaces/.../spice/stage1_cmrr_*` 유도 스크립트뿐
   - DF: DF-29
16. `_cmfb_amp_gain_diode_load` [sizing_recipe.py (27)]
   - 책임: CMFB 에러앰프 A_c 정확 폐형식
   - 이관 목적지: (삭제 후보)
   - 비고: self-test + `diagnose_cmrr_cmfb.py`(workspaces)에서만 참조
17. `_load_telescopic_topology_cached` [sizing_recipe.py (27)]
   - 책임: current_reuse topology를 **하드코딩 경로**로 로드·캐시
   - 이관 목적지: 삭제 후보
   - 비고: 경로 하드코딩 `:5054-5055`(일반화 원칙 위반). 기능은 `_load_full_topology_cached`(5379)와 DUP. `__dict__` 캐시 무효화 없음 `:5051`
   - DF: DF-29
18. `_telescopic_class_ab_open_loop_response` [sizing_recipe.py (27)]
   - 책임: 31소자 부분망 소신호 MNA로 (Vop1,Vom1)
   - 이관 목적지: 삭제 후보
   - 비고: `_full_circuit_response`(5543)가 전체회로로 일반화·대체(`:5588-5591` docstring 스스로 "대체"라 명시). DUP
   - DF: DF-29
19. `_telescopic_open_loop_device_names` [sizing_recipe.py (27)]
   - 책임: 31소자망 소자명 열거
   - 이관 목적지: 삭제 후보
   - 비고: 위 체인 전용
20. `_telescopic_class_ab_open_loop_gains` [sizing_recipe.py (27)]
   - 책임: Adm/Acm/Ann/H 4여기 풀이 + ctx 캐시
   - 이관 목적지: 삭제 후보
   - 비고: 캐시 키에 gm/gds 스냅샷 포함(`:5152-5153`, 내용기반 — 설계는 모범). 그러나 소비자 없음
21. `_cmrr_telescopic_class_ab_cmfb` [sizing_recipe.py (27)]
   - 책임: telescopic CMFB CMRR(부분망+폐형식 G2/A_c)
   - 이관 목적지: 삭제 후보
   - 비고: 대체재 `_metric_smallsignal_ratio_db`(5586)가 current_reuse 정본. DUP
   - DF: DF-29
22. `_psrr_telescopic_class_ab` [sizing_recipe.py (27)]
   - 책임: telescopic 1단 open-loop PSRR 폐형식
   - 이관 목적지: 삭제 후보
   - 비고: `_cmrr_telescopic_class_ab`(4837)와 계산 복제를 docstring이 인정(`:5276-5278`). DUP
   - DF: DF-29
23. `_psrr_telescopic_class_ab_cmfb` [sizing_recipe.py (27)]
   - 책임: telescopic CMFB PSRR
   - 이관 목적지: 삭제 후보
   - 비고: G2/A_c/T 블록 `:5334-5343` = `:5221-5233` 복제(DUP `_cmrr_telescopic_class_ab_cmfb`)
   - DF: DF-29
24. `lut_conditions_from_npz` [sizing_recipe.py (27)]
   - 책임: LUT npz의 corner/temp 기록 여부 반환
   - 이관 목적지: circuit_state_graph S0(LUT 생성메타 해시)
   - 비고: D(배선 필요)
25. `validate_theta_declaration_order` [sizing_recipe.py (27)]
   - 책임: theta 선언순서=실행순서 계약 검사
   - 이관 목적지: topology_authoring
   - 비고: D(배선 필요)
26. `load_derived_bounds` [sizing_recipe.py (27)]
   - 책임: 사이드카 JSON 읽기
   - 이관 목적지: optimizer S3(흡수) 또는 삭제
   - 비고: 유도값 저장 경로가 사이드카 vs topology.json `_derived`(`resolve_constraint_references` `:8423`) 두 갈래 — 엔진은 후자만 읽음
27. `_optimize_theta_slsqp_block_coordinate` [sizing_recipe.py (27)]
   - 책임: L 격자 ↔ SLSQP 블록 좌표 교대
   - 이관 목적지: 삭제 후보(또는 optimizer로 이관 후 실측)
   - 비고: `window_around_reference` 경로의 유일한 사용자 → 함께 정리
28. `MirrorSymmetryVerdict` [stick_diagram.py (19)]
   - 책임: 대칭 판정 결과
   - 이관 목적지: stick_diagram(삭제 후보)
   - 비고: `check_mirror_symmetry` 전용
29. `check_mirror_symmetry` [stick_diagram.py (19)]
   - 책임: finger 순서 좌우 대칭 판정
   - 이관 목적지: stick_diagram 유지 또는 test util
   - 비고: 운영 호출 0
30. `find_interleaved_symmetric_splits` [stick_diagram.py (19)]
   - 책임: 홀수 finger 쌍 교차 대칭 분할 해
   - 이관 목적지: test util
   - 비고: SD 밖 grep 0건
31. `find_idiom_matches` [stick_diagram.py (19)]
   - 책임: analog-grammar Stage1~3 원본 Match
   - 이관 목적지: topology_authoring
   - 비고: 
32. `find_differential_and_mirror_forks` [stick_diagram.py (19)]
   - 책임: 양방향 fork 분류
   - 이관 목적지: 삭제 후보
   - 비고: `find_verified_...` docstring SD:1802-1815가 이 접근의 한계와 대체를 기술
33. `suggest_headroom_stack_groups` [stick_diagram.py (19)]
   - 책임: composite를 헤드룸 그룹으로 제안
   - 이관 목적지: 삭제 후보
   - 비고: AST 호출자 0, 저장소 grep 0
34. `MultiLeafHubParityVerdict` [stick_diagram.py (19)]
   - 책임: 결과 레코드
   - 이관 목적지: test util
   - 비고: 
35. `check_multi_leaf_hub_parity` [stick_diagram.py (19)]
   - 책임: hub-leaf 오일러 가능성 공식 스크리닝
   - 이관 목적지: test util
   - 비고: 
36. `DiodeStackMember` [stick_diagram.py (19)]
   - 책임: 결과 레코드
   - 이관 목적지: -
   - 비고: 
37. `DiodeStack` [stick_diagram.py (19)]
   - 책임: 결과 레코드
   - 이관 목적지: -
   - 비고: 
38. `find_diode_stacks` [stick_diagram.py (19)]
   - 책임: 스택 내 gate가 (자기/이웃) drain인 소자
   - 이관 목적지: circuit_state_graph(diode 정의 1개로 통합)
   - 비고: **DUP**: 계획 §12.3 표 5행 "diode 집합 16/1/20". 정의 4곳: 여기(이웃-diode, stack_id 필요 SD:3100-3112) / SR `is_diode_connected` SR:3294 / SR `_diode_set_cached` SR:5452 / SD 층위1 `t.ga…
39. `audit_theta_root_direction` [stick_diagram.py (19)]
   - 책임: theta A feed의 캐스코드 방향 역전 탐지
   - 이관 목적지: topology_authoring(배선 여부 승인 필요)
   - 비고: 
40. `propose_theta_kcl_gap_fill` [stick_diagram.py (19)]
   - 책임: theta 전류 구조 제안(고정점 규칙)
   - 이관 목적지: topology_authoring(배선 승인 필요)
   - 비고: 346줄, 운영 호출 0
41. `apply_theta_kcl_gap_fill` [stick_diagram.py (19)]
   - 책임: 위 제안을 topology.json에 기록
   - 이관 목적지: topology_authoring
   - 비고: 파일 쓰기 도구
42. `apply_device_roles_gap_fill` [stick_diagram.py (19)]
   - 책임: 제안을 topology.json에 영구 기록
   - 이관 목적지: topology_authoring
   - 비고: 
43. `audit_vertical_stack_id_euler_feasibility` [stick_diagram.py (19)]
   - 책임: 선언 vsid 그룹의 오일러 실현성
   - 이관 목적지: stick_diagram(배선 여부 승인 필요)
   - 비고: 
44. `find_euler_repair_options` [stick_diagram.py (19)]
   - 책임: unresolved_row 복구 선택지 진단
   - 이관 목적지: stick_diagram(배선 승인 필요)
   - 비고: 운영 0
45. `SharedFingerWCandidate` [stick_diagram.py (19)]
   - 책임: 공통 finger_w 탐색(Case B)
   - 이관 목적지: stick_diagram 유지 또는 삭제
   - 비고: 
46. `render_stick_diagram` [stick_diagram.py (19)]
   - 책임: PDF 형식 텍스트 출력
   - 이관 목적지: test fixture/유틸
   - 비고: 
47. `render_report` [기타 모듈 (2)]
   - 책임: 텍스트 리포트 + has_violation
   - 이관 목적지: §8.3 게이트 배선 후보
   - 비고: D(파이프라인 미배선)
48. `derived_spec` [기타 모듈 (2)]
   - 책임: override + `_spec_source` 기록, why 필수
   - 이관 목적지: 〃
   - 비고: D(만들고 미배선)

## C. DUP 19개 -- 중복 함수 vs 정본

| # | 중복 함수 | 파일:줄 | 줄수 | engine | test | probe | ws | tools | 기타 | 참조 태그 | §2 정본(원문 셀) |
|---|---|---|---|---|---|---|---|---|---|---|---|
| 1 | `size_transistor` | sizing_recipe.py:115 | 9 | 1 | 8 | 2 | 4 | 0 | 0 | engine_caller_is_D:1 probe:2 test:8 workspaces_script:4 | `size_transistor` / LUT `_sizing_bundle` |
| 2 | `_multilinear_interp_point_multi` | sizing_recipe.py:255 | 46 | 1 | 0 | 0 | 0 | 0 | 0 | engine_live:1 | `_multilinear_interp` |
| 3 | `true_current_mirror_groups` | sizing_recipe.py:2363 | 25 | 1 | 0 | 0 | 0 | 0 | 1 | docs_py:1 engine_live:1 | `true_current_mirror_groups`(connectivity, 키 kind·gate·source) |
| 4 | `_folded_cascode_rout` | sizing_recipe.py:3051 | 19 | 2 | 0 | 0 | 0 | 0 | 0 | engine_caller_is_DUP:2 | (§2 행 매칭 없음) |
| 5 | `_metric_folded_cascode_gain_db` | sizing_recipe.py:3072 | 14 | 1 | 0 | 0 | 0 | 0 | 0 | engine_live:1 | `_metric_smallsignal_gain_db` |
| 6 | `_metric_folded_cascode_pm_deg` | sizing_recipe.py:3088 | 29 | 1 | 0 | 0 | 0 | 0 | 0 | engine_live:1 | `_metric_parasitic_pm_deg` |
| 7 | `full_circuit_response_at_omega` | sizing_recipe.py:4283 | 61 | 1 | 0 | 0 | 0 | 0 | 0 | engine_live:1 | `build_ac_network` |
| 8 | `_cmrr_diff_pair_tail` | sizing_recipe.py:4844 | 7 | 1 | 0 | 0 | 0 | 0 | 0 | engine_live:1 | `_metric_smallsignal_ratio_db` |
| 9 | `_theta_device_map` | sizing_recipe.py:10973 | 24 | 1 | 0 | 0 | 0 | 0 | 0 | engine_live:1 | `_theta_feed_footprint` |
| 10 | `_collect_device_refs` | sizing_recipe.py:11866 | 20 | 1 | 0 | 2 | 0 | 0 | 0 | engine_live:1 probe:2 | `_theta_feed_footprint` |
| 11 | `_fixup_euler_blocked_rows` | sizing_recipe.py:12171 | 128 | 1 | 0 | 0 | 0 | 0 | 0 | engine_live:1 | `run_topology_pipeline_with_finger_fixup` |
| 12 | `find_matching_candidates` | stick_diagram.py:979 | 77 | 3 | 9 | 0 | 2 | 0 | 0 | engine_live:3 test:9 workspaces_script:2 | `true_current_mirror_groups`(connectivity, 키 kind·gate·source) |
| 13 | `find_differential_pair_candidates` | stick_diagram.py:1688 | 104 | 3 | 1 | 0 | 0 | 0 | 1 | docs_py:1 engine_live:3 test:1 | (미정) |
| 14 | `_diff_pair_layer1_groups` | stick_diagram.py:1794 | 13 | 1 | 0 | 0 | 0 | 0 | 0 | engine_caller_is_DUP:1 | (미정) |
| 15 | `kcl_series_union` | stick_diagram.py:3187 | 57 | 2 | 0 | 0 | 0 | 0 | 0 | engine_live:2 | `stick_diagram._kcl_and_matching_edges` |
| 16 | `_kcl_and_matching_edges` | stick_diagram.py:3318 | 22 | 2 | 0 | 0 | 0 | 0 | 0 | engine_live:2 | `stick_diagram._kcl_and_matching_edges` |
| 17 | `_kcl_terminal_sign` | stick_diagram.py:3614 | 10 | 2 | 0 | 0 | 0 | 0 | 0 | engine_caller_is_D:2 | (§2 행 매칭 없음) |
| 18 | `_quantize_to_grid` | stick_diagram.py:6114 | 12 | 2 | 0 | 0 | 0 | 0 | 0 | engine_live:2 | `quantize_L` |
| 19 | `_find` | design_report.py:54 | 4 | 3 | 0 | 0 | 0 | 0 | 0 | engine_live:3 | (§2 행 매칭 없음) |

### C-1. 정본 함수들의 호출부 (§2 '정본(제안)' 열에서 뽑은 이름)

| 정본 후보 | 파일:줄 | 줄수 | engine | test | probe | ws | tools | 기타 | 참조 태그 |
|---|---|---|---|---|---|---|---|---|---|
| `_kcl_and_matching_edges` | stick_diagram.py:3318 | 22 | 2 | 0 | 0 | 0 | 0 | 0 | engine_live:2 |
| `_metric_parasitic_pm_deg` | sizing_recipe.py:4345 | 98 | 1 | 0 | 0 | 0 | 0 | 0 | engine_live:1 |
| `_metric_smallsignal_gain_db` | sizing_recipe.py:5631 | 15 | 1 | 0 | 0 | 0 | 0 | 0 | engine_live:1 |
| `_metric_smallsignal_ratio_db` | sizing_recipe.py:5602 | 27 | 1 | 0 | 0 | 0 | 0 | 0 | engine_live:1 |
| `_multilinear_interp` | sizing_recipe.py:190 | 63 | 3 | 0 | 8 | 0 | 0 | 0 | engine_live:3 probe:8 |
| `_sizing_bundle` | sizing_recipe.py:450 | 26 | 1 | 0 | 0 | 0 | 0 | 0 | engine_live:1 |
| `_theta_feed_footprint` | sizing_recipe.py:10214 | 37 | 1 | 0 | 0 | 0 | 0 | 0 | engine_live:1 |
| `build_ac_network` | sizing_recipe.py:4246 | 36 | 2 | 0 | 0 | 0 | 0 | 0 | engine_caller_is_DUP:1 engine_live:1 |
| `quantize_L` | sizing_recipe.py:804 | 17 | 7 | 0 | 0 | 0 | 0 | 0 | engine_live:7 |
| `run_topology_pipeline_with_finger_fixup` | sizing_recipe.py:12476 | 129 | 1 | 3 | 0 | 2 | 0 | 0 | engine_live:1 test:3 workspaces_script:2 |
| `size_transistor` | sizing_recipe.py:115 | 9 | 1 | 8 | 2 | 4 | 0 | 0 | engine_caller_is_D:1 probe:2 test:8 workspaces_script:4 |
| `true_current_mirror_groups` | sizing_recipe.py:2363 | 25 | 1 | 0 | 0 | 0 | 0 | 1 | docs_py:1 engine_live:1 |

### C-2. 시그니처·반환형 차이 (판단 없이 나열)

#### 1. `size_transistor`
- 중복: `size_transistor(gm: float, gm_id: float, L: float, lut: GmIdLUT, vds: float, vsb: float=0.0) -> SizingResult` @ skills/analog-gmid-design/assets/sizing_recipe.py:115 (9줄, func)
  - docstring: 방법론 식 1.17/1.18: ID = gm/(gm/ID),  W = L * ID / IDu.
  - return 123: SizingResult(gm=gm, gm_id=gm_id, ID=ID, W=W)
- §2 개념 `W 계산 `W=L*ID/IDu`` / 정본 셀: `size_transistor` / LUT `_sizing_bundle` / 중복 셀: `find_optimal_sizing`, `feasible_gm_ids`, `search_gm_id_for_role`, `feasible_L_window`에 인라인 4곳 / 상태: 식 동일 -- 행동 보존 통합 가능
  - 정본: `size_transistor(gm: float, gm_id: float, L: float, lut: GmIdLUT, vds: float, vsb: float=0.0) -> SizingResult` @ skills/analog-gmid-design/assets/sizing_recipe.py:115 (9줄)
    - return 123: SizingResult(gm=gm, gm_id=gm_id, ID=ID, W=W)
  - 정본: `_sizing_bundle(self, gm_id: float, L: float, vds: float, vsb: float=0.0, need_cgg: bool=False)` @ skills/analog-gmid-design/assets/sizing_recipe.py:450 (26줄)
    - return 475: (IDu, gm_gds, cgg_raw)
- 이관 목적지(원문): gmid_sizing_engine.py
- 비고(원문): 같은 식 `W=L·ID/IDu`를 엔진이 인라인으로 다시 씀: `find_optimal_sizing:941`, `feasible_gm_ids:1756`, `search_gm_id_for_role:2234`, `feasible_L_window:2746`. 계획은 "재사용"이라 했지만 엔진은 이 함수를 안 …

#### 2. `_multilinear_interp_point_multi`
- 중복: `_multilinear_interp_point_multi(grids, arrays, point)` @ skills/analog-gmid-design/assets/sizing_recipe.py:255 (46줄, func)
  - docstring: `_multilinear_interp()`와 동일한 다중선형보간을, **단일 좌표**에서 **여러 배열을 / 한 번에** 계산한다(F 설계, 세션31 -- `find_optimal_sizing()`의 L×VDS×gm_id 핫루프에서 / `gm_id_to_id_density()`/`gm_gds_ratio()`/`cgg_absolute()`가 같은 (L,vgs,vds,vs) 지점에서 / 각자 `_query()`를 불러 bisect 탐색(4축)을 3~4번 반복하던 것을 남은 최대 레버로 지목한 / 성능감사 후속). 축별 `idx_lo`/`frac`(bisect 탐색, 원래 비용의 핵심)을 **한 번만** 계산해 / `arra
  - return 300: totals
- §2 개념 `다선형 보간` / 정본 셀: `_multilinear_interp` / 중복 셀: `_multilinear_interp_point_multi` 복붙 / 상태: 
  - 정본: `_multilinear_interp(grids, values, points)` @ skills/analog-gmid-design/assets/sizing_recipe.py:190 (63줄)
    - return 252: np.asarray(result)
- 이관 목적지(원문): gmid_sizing_engine.py
- 비고(원문): 축별 bisect/frac/corner-weight 코드가 `_multilinear_interp`(217-246)와 복붙. 공통 `(idx_lo, frac)` 헬퍼 하나로 합칠 것

#### 3. `true_current_mirror_groups`
- 중복: `true_current_mirror_groups(by_name: dict) -> list` @ skills/analog-gmid-design/assets/sizing_recipe.py:2363 (25줄, func)
  - docstring: **진짜 전류미러** 그룹 -- 같은 `(kind, gate net, source net)`을 공유하는 소자 집합. /  / 순수 connectivity 사실이다(role 라벨을 안 본다). 물리 근거는 미러비 식 자체다: /  /     ID2/ID1 = (W2/L2) / (W1/L1) /  / 이 **순수한 W 비**(=레이아웃 비, PVT에 강함)로 축약되려면 `L1 == L2`여야 한다. L이 / 다르면 비가 이동도/Vth/채널길이변조의 L 의존성을 타고 공정·전압·온도에 흔들린다 / (사용자 지적: "tail이 bias generation하는 mirror와 L이 다르면 전류비가 실제 실리콘에서는 / PVT때문에
  - return 2387: [sorted(v) for v in groups.values() if len(v) > 1]
- §2 개념 `전류미러 그룹` / 정본 셀: `true_current_mirror_groups`(connectivity, 키 kind·gate·source) / 중복 셀: `stick_diagram.find_matching_candidates`(키 kind·gate 또는 kind·bias·rail), `_mirror_ratio_error_pairs`(선언 기반, 첫 쌍만), probe 3곳 복제 / 상태: ★ B19'에서 11 vs 18소자로 결론이 뒤집힌 원인
  - 정본: `true_current_mirror_groups(by_name: dict) -> list` @ skills/analog-gmid-design/assets/sizing_recipe.py:2363 (25줄)
    - return 2387: [sorted(v) for v in groups.values() if len(v) > 1]
- 이관 목적지(원문): circuit_state_graph.py(S1 "개념당 정의 하나"의 미…
- 비고(원문): 같은 개념이 다른 정의로 또 있다: `stick_diagram.find_matching_candidates`(972, 1005-1006 `(kind, gate, source)` current_mirror 그룹핑), `_mirror_ratio_error_pairs`(4551, connectivity가 아니…

#### 4. `_folded_cascode_rout`
- 중복: `_folded_cascode_rout(spec: dict, ctx: SizingContext) -> tuple` @ skills/analog-gmid-design/assets/sizing_recipe.py:3051 (19줄, func)
  - docstring: `folded_cascode` 계열 단일 스테이지의 출력저항(표준 캐스코드 폐형식, 2026-08-15 / 세션35 신설) -- `_metric_folded_cascode_gain_db`/`_metric_folded_cascode_pm_deg`가 / 공유하는 헬퍼(중복 방지). Rout_p(PMOS 캐스코드 branch) = gm(cascode_p)·ro(cascode_p)· / (ro(fold_leg_a)‖ro(fold_leg_b)) -- 폴딩 노드(예: X)에 diffpair 다리와 PMOS 전류원이 / 같이 물려 그 둘의 ro가 병렬로 캐스코드 소스단 임피던스를 이룬다. Rout_n(NMOS 캐스코드 / branc
  - return 3069: (rout_p, rout_n, rout)
  - return 3064: 1.0 / ctx.sized[name]['gds']
- 이관 목적지(원문): gmid_sizing_engine.py
- 비고(원문): 소비자 둘이 DUP라 종속. ro_fold 계산(3054)이 `_nmcnr_stage1_rout`(3126)와 같은 식 복제
- DF: DF-30

#### 5. `_metric_folded_cascode_gain_db`
- 중복: `_metric_folded_cascode_gain_db(spec: dict, ctx: SizingContext) -> float` @ skills/analog-gmid-design/assets/sizing_recipe.py:3072 (14줄, func)
  - docstring: F엔진(2026-08-15 세션35 신설) -- 단일 스테이지 folded-cascode의 DC 이득 표준 폐형식 / (문헌 표준: Razavi *Design of Analog CMOS Integrated Circuits* 등이 공통으로 주는 / `Adm = gm1·(Rout_p‖Rout_n)` 형태 -- diffpair 한쪽 다리의 gm과 병렬 출력저항의 곱). / 이 프로젝트의 다른 CMRR/PSRR 폐형식(예: `_cmrr_telescopic_class_ab`)과 달리 sympy / 전수 유도·ngspice 교차검증은 아직 안 했다(2026-08-15 세션35, 사용자 승인 범위 -- / "gain은 잘 알려진 표
  - return 3085: 20 * math.log10(abs(gm1 * rout))
- §2 개념 `gain metric` / 정본 셀: `_metric_smallsignal_gain_db` / 중복 셀: `_metric_folded_cascode_gain_db` / 상태: folded_cascode가 사용 중 -- 4회로 재측정 후
  - 정본: `_metric_smallsignal_gain_db(metric_spec: dict, ctx: SizingContext) -> float` @ skills/analog-gmid-design/assets/sizing_recipe.py:5631 (15줄)
    - return 5645: 20 * math.log10(abs(val))
- 이관 목적지(원문): gmid_sizing_engine.py
- 비고(원문): 같은 개념을 회로무관 MNA `_metric_smallsignal_gain_db`(5615)가 계산(파일럿·two_stage는 이미 그쪽). docstring 3066-3068: sympy/SPICE 검증 안 됨. 운영 중이므로 삭제 전 JSON 타입 이전+4회로 측정 필요
- DF: DF-30

#### 6. `_metric_folded_cascode_pm_deg`
- 중복: `_metric_folded_cascode_pm_deg(spec: dict, ctx: SizingContext) -> float` @ skills/analog-gmid-design/assets/sizing_recipe.py:3088 (29줄, func)
  - docstring: F엔진(2026-08-15 세션35 신설) -- 단일 스테이지 folded-cascode의 위상여유, 2-pole / 근사(`PM = 90도 - atan(GBW/p2)`, 표준 형태). 지배극은 출력(`p1 = 1/(2π·Rout·CL)`), / GBW = gm1/(2π·CL) = Adm·p1. 2차극은 폴딩 노드(예: X)의 국소 임피던스(≈1/gm(cascode_p), / 캐스코드 소스단이 낮은 임피던스를 만드는 표준 근사)와 그 노드의 기생 커패시턴스로 / 추정: `p2 = gm(cascode_p) / (2π·C_fold)`. /  / ⚠️ **정직한 한계**(`_psrr_telescopic_class_ab`류와 
  - return 3116: 90.0 - math.degrees(math.atan(gbw_hz / p2_hz))
- §2 개념 `PM metric` / 정본 셀: `_metric_parasitic_pm_deg` / 중복 셀: `_metric_folded_cascode_pm_deg` / 상태: 〃
  - 정본: `_metric_parasitic_pm_deg(spec_metric: dict, ctx: SizingContext) -> float` @ skills/analog-gmid-design/assets/sizing_recipe.py:4345 (98줄)
    - return 4442: 180.0 - lag_deg
    - return 4417: v
- 이관 목적지(원문): gmid_sizing_engine.py
- 비고(원문): `_metric_parasitic_pm_deg`(4329, L2 실제 주파수응답)와 같은 개념. 접합용량·Y-branch 극 무시(3084-3091)
- DF: DF-30

#### 7. `full_circuit_response_at_omega`
- 중복: `full_circuit_response_at_omega(ctx: 'SizingContext', excite: dict, also_fix, omega: float, network: dict | None=None)` @ skills/analog-gmid-design/assets/sizing_recipe.py:4283 (61줄, func)
  - docstring: `(G + j*omega*C) v = b`를 풀어 **복소** 노드전압을 돌려준다(2026-09-10, §7.11 L2). /  / `_full_circuit_response()`(DC/mid-band, 실수)의 주파수 확장이다 -- 같은 `devices` / 스탬프(`_full_circuit_devices()`, 저항 포함)를 쓰고 거기에 용량 항만 더한다. /  / ## 왜 pole을 고유값으로 뽑지 않는가 /  / §7.11이 L2를 "MNA에서 실제 pole 추출(고유값)"으로 적어뒀는데, 구현하며 **그대로는 틀린다**는 / 것이 드러났다: `det(G + sC)=0`의 근에는 bias 노드가 만드는 모드까지 
  - return 4342: {**{k: complex(v) for k, v in fixed.items()}, **{nodes[i]: complex(sol[i]) for i in range(n)}}
  - return 4307: dict(fixed)
- §2 개념 `MNA 소자 스탬프` / 정본 셀: `build_ac_network` / 중복 셀: `full_circuit_response_at_omega`, `_mna_solve_smallsignal` / 상태: 
  - 정본: `build_ac_network(ctx: 'SizingContext', excite: dict, also_fix) -> dict` @ skills/analog-gmid-design/assets/sizing_recipe.py:4246 (36줄)
    - return 4281: {'devices': devs, 'caps': caps, 'nodes': nodes, 'fixed': fixed}
- 이관 목적지(원문): gmid_sizing_engine.py
- 비고(원문): 트랜지스터 스탬프 6줄(4305-4311)이 `_mna_solve_smallsignal`(4970) 5016-5022와 **동일**. ω=0이면 DC 해와 같음 -> 복소 solver 하나로 합칠 것. 이쪽엔 고립노드 진단(5029-5034)이 없음

#### 8. `_cmrr_diff_pair_tail`
- 중복: `_cmrr_diff_pair_tail(metric_spec: dict, ctx: SizingContext) -> float` @ skills/analog-gmid-design/assets/sizing_recipe.py:4844 (7줄, func)
  - docstring: `circuit_family="diff_pair_tail"` — CMRR ≈ [(ro_tail/2) + (1/gm_tail)]·gm_tail / (문헌 표준 1차 근사, do.md 배치 7-3i). `tail_device`의 이미 사이징된 gm/gds만 쓴다.
  - return 4850: 20 * math.log10(cmrr_linear)
- §2 개념 `CMRR` / 정본 셀: `_metric_smallsignal_ratio_db` / 중복 셀: `_cmrr_diff_pair_tail` / 상태: 〃
  - 정본: `_metric_smallsignal_ratio_db(metric_spec: dict, ctx: SizingContext) -> float` @ skills/analog-gmid-design/assets/sizing_recipe.py:5602 (27줄)
    - return 5628: 20 * math.log10(abs(num / den))
    - return 5621: p - n if mode == 'diff' else (p + n) / 2.0
- 이관 목적지(원문): gmid_sizing_engine.py
- 비고(원문): 같은 개념을 회로무관 전체회로 MNA `_metric_smallsignal_ratio_db`(5586)가 계산(파일럿은 이미 전환, JSON 주석 1873). 운영 중이라 삭제 전 JSON 이전+측정 필요

#### 9. `_theta_device_map`
- 중복: `_theta_device_map(thetas: list) -> dict` @ skills/analog-gmid-design/assets/sizing_recipe.py:10973 (24줄, func)
  - docstring: `{theta_name: {이 theta가 값을 정하는 소자 이름들}}` -- feed 선언에서 긁어모은다. /  / feed 타입마다 소자를 담는 키가 다르므로(`devices`/`root`/`roots`/`target`/`reference`/ / `ref_device`/`stage_devices` ...) 값이 문자열이거나 문자열 리스트면 전부 후보로 본다. / 소자 이름인지 아닌지는 호출자가 실제 소자 집합과 교집합을 취해 거른다 -- 여기서는 / 회로를 모르는 채 선언만 훑는다.
  - return 10996: out
- §2 개념 `theta가 건드리는 소자` / 정본 셀: `_theta_feed_footprint` / 중복 셀: `_theta_device_map`, `_collect_device_refs` / 상태: 
  - 정본: `_theta_feed_footprint(theta: dict) -> dict` @ skills/analog-gmid-design/assets/sizing_recipe.py:10214 (37줄)
    - return 10227: {'roots': frozenset(), 'derived_writes': frozenset(writes), 'reads': frozenset()}
    - return 10232: {'roots': frozenset(roots), 'derived_writes': frozenset(), 'reads': frozenset(reads)}
    - return 10235: {'roots': frozenset(roots), 'derived_writes': frozenset(), 'reads': frozenset()}
    - return 10237: {'roots': frozenset({feed['target']}), 'derived_writes': frozenset(), 'reads': frozenset({feed['omega_key']})}
    - return 10240: {'roots': frozenset({feed['target']}), 'derived_writes': frozenset(), 'reads': frozenset({feed['reference']})}
    - return 10243: {'roots': frozenset(feed['devices']), 'derived_writes': frozenset(), 'reads': frozenset()}
- 이관 목적지(원문): (정본 `_theta_feed_footprint` 10174 / walk…
- 비고(원문): 소자명 아닌 문자열(type, metric 이름)도 수집 후 교집합으로 거름. 두 함수와 개념 중복

#### 10. `_collect_device_refs`
- 중복: `_collect_device_refs(spec, known_names: set) -> set` @ skills/analog-gmid-design/assets/sizing_recipe.py:11866 (20줄, func)
  - docstring: `spec`(metric_spec처럼 임의로 중첩된 dict/list) 안의 문자열 leaf 중 `known_names`에 / 속하는 것만 재귀로 모은다 -- metric마다 소자를 가리키는 키 이름이 제각각이라 / (`devices`/`stages`/`device`/`tail_device`/`high_device`/... , _METRICS_REGISTRY 9종 / 확인) 특정 키에 의존하지 않고 구조 전체를 훑는다.
  - return 11885: found
- §2 개념 `theta가 건드리는 소자` / 정본 셀: `_theta_feed_footprint` / 중복 셀: `_theta_device_map`, `_collect_device_refs` / 상태: 
  - 정본: `_theta_feed_footprint(theta: dict) -> dict` @ skills/analog-gmid-design/assets/sizing_recipe.py:10214 (37줄)
    - return 10227: {'roots': frozenset(), 'derived_writes': frozenset(writes), 'reads': frozenset()}
    - return 10232: {'roots': frozenset(roots), 'derived_writes': frozenset(), 'reads': frozenset(reads)}
    - return 10235: {'roots': frozenset(roots), 'derived_writes': frozenset(), 'reads': frozenset()}
    - return 10237: {'roots': frozenset({feed['target']}), 'derived_writes': frozenset(), 'reads': frozenset({feed['omega_key']})}
    - return 10240: {'roots': frozenset({feed['target']}), 'derived_writes': frozenset(), 'reads': frozenset({feed['reference']})}
    - return 10243: {'roots': frozenset(feed['devices']), 'derived_writes': frozenset(), 'reads': frozenset()}
- 이관 목적지(원문): (`_theta_device_map` 10933)
- 비고(원문): 판정 로직에선 더 이상 안 씀(`:11894-11921` 사유) — 진단 필드 전용

#### 11. `_fixup_euler_blocked_rows`
- 중복: `_fixup_euler_blocked_rows(rows: dict, matching_pairs: list, pair_sensitivity: dict, ctx: SizingContext, lut_by_kind: dict, metrics_specs: dict, constraints: list, gm_id_bounds: tuple=(2.0, 30.0), max_rounds: int=5) -> tuple` @ skills/analog-gmid-design/assets/sizing_recipe.py:12171 (128줄, func)
  - docstring: `repair_matching_safety()`(3c 수리 -- 일부 소자를 `common_centroid_layout()`으로 / 새 행에 빼냄)가 원래 행에 **남은 나머지 소자들**의 euler 조건(짝수차수 -- 한붓그리기 / 가능 여부)까지 보존한다는 보장은 없다 -- 2026-08-13(세션31 이어) 실측 발견: `two_stage_ / ota` box-shape 진단 중 `save_instance_json()`이 repair *이전* 스냅샷을 저장하던 버그를 / 고치자(그 자체는 별개 수정), self-test(11소자 M3a 그룹, M4a/M4b+M10/M19를 3c 수리로 / 빼낸 뒤) 남은 행 `m3
  - return 12298: (current_rows, cur_ctx)
  - return 12225: components
  - return 12237: (current_rows, cur_ctx)
- §2 개념 `euler 행 수정 전략` / 정본 셀: `run_topology_pipeline_with_finger_fixup` / 중복 셀: `_fixup_euler_blocked_rows`(docstring이 "정확히 같은 전략") / 상태: 
  - 정본: `run_topology_pipeline_with_finger_fixup(topology_json_path: str, sizing_overrides: dict, ctx: SizingContext, lut_by_kind: dict, metrics_specs: dict, constraints: list, floorplan_hints: dict | None=None, cell_groups: dict | None=None, gm_id_bounds: tuple=(2.0, 30.0), max_fixup_rounds: int=5) -> dict` @ skills/analog-gmid-design/assets/sizing_recipe.py:12476 (129줄)
    - return 12601: {**result, 'fixup_rounds': fixup_rounds, 'group_splits': group_splits, 'sizing_overrides': overrides, 'ctx': cur_ctx, 'unresolved_row': blocked[0] if 
    - return 12555: {**result, 'fixup_rounds': fixup_rounds, 'group_splits': group_splits, 'sizing_overrides': overrides, 'ctx': cur_ctx, 'unresolved_row': None, 'unresol
- 이관 목적지(원문): (`run_topology_pipeline_with_finger_fixu…
- 비고(원문): docstring 스스로 "정확히 같은 전략"(`:12143-12146`). rows 표현용·topology_path용 두 벌

#### 12. `find_matching_candidates`
- 중복: `find_matching_candidates(transistors: list, idiom_matches: list | None=None) -> dict` @ skills/analog-gmid-design/assets/stick_diagram.py:979 (77줄, func)
  - docstring: 구조적 신호만으로 matching **후보**(확정 아님)를 찾는다 — AI/설계자가 소자쌍을 / 일일이 수동으로 훑지 않도록 후보를 미리 좁혀주는 게 이 함수의 존재 이유다(토큰 절약). / 자동 탐지 가능한 두 유형: /  / - `current_mirror`: 같은 극성(kind) + 같은 gate net을 공유하는 2개 이상의 소자. /   (`gate`를 지정하지 않은 소자는 대상에서 제외된다.) / - `diff_pair`: 같은 극성 + 같은 source net을 공유하지만 서로 다른 gate net을 가진 /   정확히 2개의 소자(차동 입력쌍의 구조적 정의 그 자체 — W는 요구하지 않는다). /   *
  - return 1055: {'current_mirror': current_mirror, 'diff_pair': diff_pair}
  - return 1029: {'current_mirror': current_mirror, 'diff_pair': diff_pair}
- §2 개념 `전류미러 그룹` / 정본 셀: `true_current_mirror_groups`(connectivity, 키 kind·gate·source) / 중복 셀: `stick_diagram.find_matching_candidates`(키 kind·gate 또는 kind·bias·rail), `_mirror_ratio_error_pairs`(선언 기반, 첫 쌍만), probe 3곳 복제 / 상태: ★ B19'에서 11 vs 18소자로 결론이 뒤집힌 원인
  - 정본: `true_current_mirror_groups(by_name: dict) -> list` @ skills/analog-gmid-design/assets/sizing_recipe.py:2363 (25줄)
    - return 2387: [sorted(v) for v in groups.values() if len(v) > 1]
- 이관 목적지(원문): circuit_state_graph(S1 matching 엣지 정의 1개…
- 비고(원문): mirror 정의 3개: net-only (kind,gate) SD:1024-1031 / idiom (kind,bias,rail) SD:1041 / SR `true_current_mirror_groups` (kind,gate,source)+레일게이트 제외 SR:2358-2382. diff_pair는 `_…

#### 13. `find_differential_pair_candidates`
- 중복: `find_differential_pair_candidates(transistors: list, inputs=(), outputs=(), feedbacks=(), biases=(), clocks=()) -> dict | None` @ skills/analog-gmid-design/assets/stick_diagram.py:1688 (104줄, func)
  - docstring: 구조적으로 매칭된 branch 쌍(`suggest_vertical_stack_composites()`의 composite / 시퀀스가 완전히 같은 branch끼리 묶음, C-10과 동일 원리) 안에서, 서로 다른 위치의 / 소자쌍이 (1) 같은 kind, (2) 다른 gate(=mirror 아님), (3) **같은 non-rail source(진짜 / tail net)를 공유**하면 differential pair 후보로 판정한다. /  / ⚠️ **왜 이게 중요한가(사용자 통찰, 2026-08-07)**: "differential pair를 먼저 찾고 / 나서 mirror 관계를 분석해야 정확해진다" -- `Voc`를
  - return 1791: {'candidates': out}
  - return 1728: None
  - return 1735: tuple(((len(c['members']), c['idiom'], tuple((by_name[m].kind for m in c['members']))) for c in b['composites']))
- §2 개념 `diffpair / tail` / 정본 셀: (미정) / 중복 셀: `find_differential_pair_candidates`, `_diff_pair_layer1_groups`, `_propose_gm_id_roles`(SD, connectivity) vs `gain_stage_tails`, `input_referred_offset_pairs`(SR, 선언) / 상태: ★ S1 유도 정본을 정해야 함
- 이관 목적지(원문): circuit_state_graph
- 비고(원문): diffpair/tail 정의 다중: 여기 / `find_matching_candidates` diff_pair SD:1033-1046 / SR `gain_stage_tails`(stage source net을 drain으로 갖는 tail) SR:2434-2470 / SR `input_referred_o…

#### 14. `_diff_pair_layer1_groups`
- 중복: `_diff_pair_layer1_groups(transistors: list) -> dict` @ skills/analog-gmid-design/assets/stick_diagram.py:1794 (13줄, func)
  - docstring: `find_matching_candidates()`의 `diff_pair` net-only 판정(같은 kind + 같은 / non-rail source + 다른 gate, role/idiom 분류 불필요)만 떼어낸 헬퍼 -- `find_ / differential_pair_candidates()`의 층위1 폴백 전용(중복 구현 방지, `find_matching_ / candidates()`의 W-일치 필터는 topology 저작 단계엔 아직 W가 없어 항상 통과한다).
  - return 1804: {k: v for k, v in by_source.items() if len(v) == 2 and v[0].gate is not None and (v[1].gate is not None) and (v[0].gate != v[1].gate)}
- §2 개념 `diffpair / tail` / 정본 셀: (미정) / 중복 셀: `find_differential_pair_candidates`, `_diff_pair_layer1_groups`, `_propose_gm_id_roles`(SD, connectivity) vs `gain_stage_tails`, `input_referred_offset_pairs`(SR, 선언) / 상태: ★ S1 유도 정본을 정해야 함
- 이관 목적지(원문): circuit_state_graph
- 비고(원문): docstring SD:1787-1789가 `find_matching_candidates` diff_pair와 같은 판정이라 명시

#### 15. `kcl_series_union`
- 중복: `kcl_series_union(netlist: list, matching_pairs: list) -> dict` @ skills/analog-gmid-design/assets/stick_diagram.py:3187 (57줄, func)
  - docstring: L2 축A(2026-08-05, 세션10 L1/L2 구현) — `derive_stack_groups()`를 KCL용/geometry용 / 두 함수로 분리한 것 중 KCL(축A, `sizing_recipe.py`의 `stack_groups_kcl`) 쪽. 두 규칙으로 / union-find 병합한다: /  / 1. **내부 노드(2단자 net, 레일 제외)**: 어떤 net이 **레일(vdd/gnd/vss)이 아니고** /    정확히 2개의 소자 단자에만 연결되면, 전하보존으로 그 두 소자 전류가 반드시 같다 — /    극성과 무관한 물리 법칙(예: `folded_cascode`의 `M106`(nmos)/`M108`(
  - return 3243: result
  - return 3218: x
- §2 개념 `KCL 엣지` / 정본 셀: `stick_diagram._kcl_and_matching_edges` / 중복 셀: `kcl_series_union`이 같은 엣지를 따로 구현, `_metric_kcl_residual` / 상태: 행동 보존 통합 가능
  - 정본: `_kcl_and_matching_edges(transistors: list, matching_pairs: list) -> list` @ skills/analog-gmid-design/assets/stick_diagram.py:3318 (22줄)
    - return 3339: edges
- 이관 목적지(원문): circuit_state_graph
- 비고(원문): 같은 edge를 `_kcl_and_matching_edges`(SD:3298, docstring "단일 정의로 분리")가 재구성하지만 이 함수 본문 SD:3188-3212는 그것을 쓰지 않고 독자 구현

#### 16. `_kcl_and_matching_edges`
- 중복: `_kcl_and_matching_edges(transistors: list, matching_pairs: list) -> list` @ skills/analog-gmid-design/assets/stick_diagram.py:3318 (22줄, func)
  - docstring: `kcl_series_union()`이 union할 때 실제로 쓰는 것과 똑같은 두 종류의 edge(내부 / 2단자 net + declared `current_forced` matching_pairs)를 `(a, b, kind, detail)` / 리스트로 재구성한다 -- `audit_vertical_stack_id_vs_kcl()`과 / `propose_vertical_stack_id_gap_fill()` 둘 다 같은 edge 정의를 써야 서로 어긋나지 / 않으므로(2026-08-13 세션31, N-way 조인트 스캔 때 만든 `_shared_current_groups_ / from_compensation()`와 같은
  - return 3339: edges
- §2 개념 `KCL 엣지` / 정본 셀: `stick_diagram._kcl_and_matching_edges` / 중복 셀: `kcl_series_union`이 같은 엣지를 따로 구현, `_metric_kcl_residual` / 상태: 행동 보존 통합 가능
  - 정본: `_kcl_and_matching_edges(transistors: list, matching_pairs: list) -> list` @ skills/analog-gmid-design/assets/stick_diagram.py:3318 (22줄)
    - return 3339: edges
- 이관 목적지(원문): circuit_state_graph
- 비고(원문): 상대: `kcl_series_union`

#### 17. `_kcl_terminal_sign`
- 중복: `_kcl_terminal_sign(kind: str, terminal: str) -> int` @ skills/analog-gmid-design/assets/stick_diagram.py:3614 (10줄, func)
  - docstring: PMOS/NMOS의 관례적 전류 방향(2026-08-18 세션, 사용자 지적 "PMOS/NMOS 경계는 항상 / drain-drain" 이후 sympy로 재확인한 부호 규칙)을 net 기준 부호로 변환한다 -- PMOS는 / source->drain(그 net에 전류를 **공급**하는 쪽이 drain, +1 / **흡수**하는 쪽이 source, / -1), NMOS는 drain->source(그 반대, drain=-1/source=+1)다. 어떤 net에 모인 모든 / 소자의 이 부호*ID 합은 KCL로 항상 0이다(nmcnr_amplifier의 NodeF1/NodeM1/NodeM2를 / 이 부호로 sympy 재유도해
  - return 3623: -1 if terminal == 'drain' else 1
  - return 3622: 1 if terminal == 'drain' else -1
- 이관 목적지(원문): circuit_state_graph
- 비고(원문): 운영 0(D). SR `_metric_kcl_residual` SR:4469-4472이 같은 규약 독자 구현

#### 18. `_quantize_to_grid`
- 중복: `_quantize_to_grid(x: float, grid_step: float, mode: str='nearest') -> float` @ skills/analog-gmid-design/assets/stick_diagram.py:6114 (12줄, func)
  - docstring: `sizing_recipe.quantize_L()`과 정확히 같은 공식(길이 치수를 `grid_step`의 배수로 / 스냅)의 로컬 사본 — `sizing_recipe.py`가 이 파일(`stick_diagram.py`)을 import하므로 / 반대 방향 import는 순환참조가 된다(2026-08-13 세션31 이어, box-shape finger_w에도 / 공정 manufacturing grid를 적용하기 위해 신설 — `.ai/context.md` 세션31 CD 참고). / 구현이 3줄짜리 순수 함수라 사본 유지 비용이 낮다.
  - return 6125: fn(x / grid_step) * grid_step
- §2 개념 `L grid 스냅` / 정본 셀: `quantize_L` / 중복 셀: SD `_quantize_to_grid`(의도적 사본) / 상태: 모듈 경계 결정 후
  - 정본: `quantize_L(L: float, grid_step: float, mode: str='nearest') -> float` @ skills/analog-gmid-design/assets/sizing_recipe.py:804 (17줄)
    - return 820: fn(L / grid_step) * grid_step
- 이관 목적지(원문): stick_diagram(공용 유틸로 추출 가능)
- 비고(원문): SR `quantize_L` SR:799-815와 동일 공식; docstring SD:6059-6063이 순환 import 회피용 의도적 사본이라 명시

#### 19. `_find`
- 중복: `_find(x)` @ skills/analog-gmid-design/assets/design_report.py:54 (4줄, func)
  - return 57: x
- 이관 목적지(원문): 공통 유틸
- 비고(원문): DUP 성격 -- union-find가 `sizing_recipe.py:3427`, `:10819`, `stick_diagram.py:3170`, `:5092`에도 각자 구현
