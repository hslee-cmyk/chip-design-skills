# agent6 -- 계획서(gain-budget-gmid-sizing.plan.md v4.43) 대 구현 대조 감사

- 기준: 저장소 HEAD 5578aa3, 2026-09-14. 읽기 전용 감사.
- 추출: `agent6_extract.py`가 Version History 이전(1~3919줄)의 백틱 토큰 488개를 뽑음(func 158 / file 70 / field 38 / test 10 / ident 212) -> `agent6_candidates.tsv`. 호출부 계수는 `agent6_callers.py`로 했다(주석·문자열 제외, `if __name__` 이후는 self-test로 따로 셈).
- 경로 약어: SR=`skills/analog-gmid-design/assets/sizing_recipe.py`, SD=`.../stick_diagram.py`, RH=`workspaces/run_harness.py`, P=계획서 줄번호, CTX=`.ai/context.md`.

## 1. 약속 대 구현 표

| 약속(§) | 종류 | 상태 | 실제 위치/대체 | 근거 |
|---|---|---|---|---|
| `_solve_diode_connected_vgs_fixed_point()` (§2.1, §6.1다, §7.3, §8.4) | 함수 | 이름 바꿔 구현됨 + 계획 내 불일치 | SR:3297 `solve_diode_connected_vds()`(대입 반복 대신 bisection, A7) + SR:3516 `set_device_vds()` + SR:3743 `apply_diode_self_consistent_gm_id()` | P:1251/1307은 v4.17 새 이름, P:2399(§8.4)는 옛 이름 그대로 |
| `gm_id_for_gm_gds_ratio()` (§2.1, §6.1다, §7.2) | 함수 | 미구현 | def 0건, 문자열 0건 | P:329, P:832 |
| `resolve_stage_sizing()` (§2.1, §7.2, §7.6, §8.4) | 함수 | 미구현 | 없음. B3 시그니처 결함도 미해결 | P:331, P:1638, P:2580 |
| `_resolve_device_headroom()` (§2.1) | 함수 | 폐기(계획이 취소) | `resolve_feed_vds()` SR:2138 / `_hr_resolve_vertical_group()` SR:7644 유지 | P:333-336 취소선 |
| `solve_compensation_for_gbw_pm()` + topology_fn 방향 반전 (§2.1, §6.1가, §5) | 함수 | 부분 구현(다른 경로) | 함수는 없음. §10.8에서 Cc를 `sqrt(beta*tan(PM)*C_Ltot*Cgg2)`로 유도(topology_fn 내부)하는 것만 착지 | P:337, P:594, CTX:14293-14296 |
| ★`verify_node_voltage_consistency(ctx)` (§2.1, §3.1-6, §4.1, §7.5, §8.4-6) | 함수(게이트) | 부분 구현(이름 다름, 핵심 검사 빠짐) | SR:3895 `propagate_node_voltages()`, SR:3957 `derive_vsb_from_nodes()`, SR:4018 `audit_vsb_consistency()`(게이트 배선 SR:9441), SR:4430 `_metric_kcl_residual`. **다중도달 conflicts를 엔진이 읽지 않음**, 게이트-내부net VGS 불일치 검사 없음, `list[Violation]` 게이트 없음 | P:1568, P:3890(§12.6 #2) |
| `cross_check_with_spice()` + `build_transient_netlist.py` 편입 (§2.1, §4.1, §7.5, §8.4-7) | 함수+파일 | 미구현 | def 0건. `build_transient_netlist.py`가 저장소에 없음 | P:343, P:1581 |
| `L_candidates_product()` (§2.1, §6.1다, §7.6, §7.10) | 함수 | 미구현(방식 자체가 바뀜, 계획 미갱신) | L_combo 전수 스캔 대신 `synthesize_l_class_thetas()` SR:2612 + SLSQP L theta + `feasible_L_window()` SR:2694 | P:345, P:1639, P:3069 |
| `sweep_area_power_pareto() -> ParetoReport` (§2.1, §7.9, §8.4-0) | 함수 | 미구현 | 프로브만 있음: `tests/probe_area_pareto.py` | P:348, P:2078 |
| `make_cmrr_psrr_feasibility_check()` (§2.1, §6.1다) | 함수 | 삭제(v4.4) + 계획 내 모순 | `check_global_gates()`로 대체한다고 했으나 그것도 미구현. §6.1(다)에는 아직 남아 있음 | P:351(삭제), P:612(잔존), P:2579 |
| `make_stage_local_check()` (§2.1, §7.6) | 함수 | 미구현 | 기존 `make_matching_feasibility_check()` SR:7300, `make_replica_feasibility_check()` SR:7253만 있음 | P:355, P:1040 |
| `check_global_gates() -> GateReport` (§2.1, §7.6, §9-4) | 함수 | 미구현 | def 0건. T3 metric은 SLSQP 제약으로만 평가됨 | P:358, P:1043, P:2525 |
| `diagnose_sizing_dof() -> DofReport` (§2.1, §3.3 C6, §7.8, §8.3-7) | 함수 | 미구현 | def 0건. B5/B6(세는 축의 결함) 미해결 | P:361, P:1727, P:2582-2583 |
| `_hr_*` 6개 (§2.1, §8.4, 09-07 선행조치) | 함수 6 | 구현됨 | SR:7420 / 7428 / 7461 / 7515 / 7532 / 7644. 호출 SR:7661(재귀 어댑터), SR:9148(`_evaluate` 안 얇은 래퍼) | P:365 [x], 커밋 e5fbf92 |
| `compute_metric()` 경유 gain 제약 (§2.1, §7.9) | 배선 | 구현됨 | SR:5842, `_METRICS_REGISTRY` 경유 | P:368, CTX:14053 |
| `solve_allocation_dp() -> Allocation` (§2.1, §7.9, §9-5) | 함수 | 미구현 | 프로토타입만 있음: `tests/probe_allocation_solvers.py` | P:370, P:2035, P:2526 |
| `set_device_vds()` + 원시 대입 grep 테스트 (§2.1, C2/C9, §7.3) | 함수+테스트 | 함수는 구현 / 테스트는 미구현 | SR:3516. 원시 `entry["vds"] =`는 SR:3565 한 곳뿐. **grep 강제 테스트는 self-test와 tests/ 어디에도 없음** | P:375-378, CTX:14209 |
| `load_sizing_spec() -> SizingSpec` (§2.1, §7.1) | 함수 | 미구현 | def 0건 | P:379 |
| `resolve_headroom(topology_spec, ctx)` (§2.1, §8.4-2) | harness | 미구현 | def 0건. `_hr_*` 추출은 됐지만 묶는 harness가 없음 | P:383, P:2413 |
| `size_all_stages()` (§8.4-1) | harness | 미구현 | def 0건 | P:2411 |
| `headroom_fn(entry, ctx)` + gain 기여도 가중 배분 (§6.1가, §7.9) | 함수 | 대체됨(계획 미갱신) | `allocate_stack_headroom()` SR:2009가 `diode_vds_window()` SR:3570의 diode 구간 제약을 씀. 가중 배분은 없음 | P:591, P:2125, P:2593 |
| `search_gm_id_and_L_for_role()` (§6.1가, §7.10) | 함수 | 대체됨(계획 미갱신) | `derive_role_L()` SR:2772 / `derive_class_L()` SR:2865 / `feasible_L_window()` | P:592, P:2213, P:3241-3284 |
| `measure_L_knee()` (§6.1가/다, §7.10) | 함수 | 구현됨 | SR:2305, `knee_L_for_kind()` SR:2555(호출 SR:2598) | P:593, P:3013, CTX:14335 |
| `L_bounds_from_ft_and_matching()` (§6.1다, §7.10) | 함수 | 대체됨(새 함수 불필요로 결정) | 상한은 제약 `parasitic_pm_deg >= PM_target_deg`, 하한은 `mismatch_sigma_mV`, 창은 `feasible_L_window()` | P:611, P:2204, CTX:14321-14323 |
| `allocate_headroom_budget()` / `measure_stage_gain_ceiling()` / `redistribute_headroom_by_gain_gradient()` (§6.1다) | 함수 3 | 미구현 + 계획 내 모순(유령 함수) | def 0건. §10.5가 이미 "본문 정의 없음"이라 지적했지만 §6.1에 그대로 남아 있음 | P:609-610, P:2625 |
| `_L_ROLE_MULTIPLIERS` 제거 / `select_L_by_role()` 삭제 (§6.1가, §7.10, §10.11) | 삭제 | 폐기·대체됨(v4.39) | def 0건. 가드는 `derive_role_L()`로 옮김 | P:3291, CTX:14372 |
| `resolve_feed_vds()` 티어①(diode) (§6.1가, §7.3 v3.0) | 개선 | 폐기·대체됨(v4.3) | diode 경로가 0/51이라 `set_device_vds()` 단일 setter + pre-pass 방식으로 바꿈 | P:2578(B1) |
| `render_design_report_html()` 신규 (§8.5) | 함수 | 이름 바꿔 **계획보다 먼저** 구현돼 있었음(중복 약속) | `design_report.py:198 render_html_report()`(세션20, 커밋 e4042c5). 계획 v1.1은 "ad hoc build_report.py를 편입하는 신규"라고 적었지만 편입은 이미 끝난 상태였음 | design_report.py:1-20, P:2446 |
| `save_instance_json()` (§8.5-1) | 함수 | 구현됨(기존) | SD:8948, 호출 RH:487 | P:2444 |
| `<name>.sizing_spec.json` / `_TEMPLATE.sizing_spec.json` (§2.1, §4.1, §7.1) | 파일/스키마 | 미구현 | 저장소에 `*.sizing_spec.json` 0개 | P:317, P:534, P:631 |
| topology.json을 순수 connectivity로 (`device_roles`/`sizing_roles`/`compensation` 제거) (§2.1) | 스키마 | 미구현(오히려 늘어남) | `library/*.topology.json` 5개 모두 `sizing_roles`/`device_roles`/`compensation` 보유. v4.3x 이후 `sizing_roles.metrics`/`constraints`(`value_from_constraint`, `_derived`)가 계속 추가됨 | P:322, 최상위 키 덤프 |
| `stages[].gain_budget_db`(출력), `gain_budget_db_override`, `stages[].driving_spec`, `bias_devices[].gm_id_policy`, `compensation.gm_convention` (§2.1, §7.1) | 스키마 필드 | 미구현 | 코드와 JSON에서 0건 | P:317-321, P:781-809 |
| `structural_declarations` / `feedback_loops` (§7.1, §10.1 D3 "반영 완료") | 스키마 블록 | 미구현 + 계획 내 모순 | 코드/JSON 0건. 반영은 문서에만 됨 | P:2552, CTX:14057 |
| `review_needed` 상태값 (§3.3 C8) | 상태/게이트 | 미구현 | 코드 0건 | P:510 |
| C1~C10 강제 테스트 10개 (`test_diode_self_consistency` 외) (§3.3, §4.1 DoD) | 테스트 10 | 미구현 (C9는 setter 단일화까지만, 테스트 없음) | 저장소 전체에서 `def test_` 0건, `import pytest` 0건, `tests/test_*.py` 0개 | P:503-512, P:546-552 |
| §8 신규 소스 5개: `topology_authoring.py`/`gmid_sizing_engine.py`/`sizing_layout_convergence.py`/`instance_report_builder.py`/`gmid_design_pipeline.py` | 파일 5 | 미구현 | 저장소에 0개 | P:2351-2358 |
| harness `author_topology_spec()`/`run_sizing_layout_convergence()`/`build_instance_and_report()`/`run_gmid_design_pipeline()` | harness 4 | 미구현 | def 0건. 실제 진입점은 여전히 `optimize_full_circuit_budget()` SR:9624(RH:440) + `run_topology_pipeline_with_finger_fixup()` SR:12436 | P:2372, 2403, 2441, 2454 |
| `tests/test_<module>.py` 6개 + `test_stick_diagram.py` 이관 (§3.2, §8.2, §8.8) | 테스트 파일 | 미구현 | tests/ 78개 항목 중 test_*.py 0개. SD 인라인 self-test 8991~12936(3,946줄), SR 인라인 12571~15270(2,700줄) 그대로 | P:494, P:2355, P:2491 |
| `tests/baseline/*.baseline.log` + README (§8.8) | 파일 | 구현됨 | `sizing_recipe.selftest.baseline.log`, `stick_diagram.selftest.baseline.log`, README 갱신 이력 3회(B20 / B25+B9 / B19') | P:2498-2512, 커밋 e5fbf92/57abfdd/1285618/a412f40 |
| `_sorted_setmap()` 결정론화 (§8.8) | 함수 | 구현됨 | SD:943, 호출 SD:7031 | P:2509, e5fbf92 |
| 계기판 metric 4개 + `lut_conditions_from_npz()` (§0.1, §10.2-10.3) | metric/함수 | 구현됨 (`lut_conditions_from_npz`만 부분) | SR:4617 / 4502 / 4430 / 3392(레지스트리 경유). `lut_conditions_from_npz` SR:5355는 **프로덕션 호출 0** | P:60-61 |
| `ideal_sources.value_amp` 소비 배선 (B14, §0.5, §9-3) | 배선 | 부분 구현 | `_metric_kcl_residual` SR:4485에서만 소비. 사이징 `seed_currents` 경로에서는 소비하지 않음 | P:2591, SR:4474-4485 |
| 추적성 태그 `_vds_source`/`_gm_id_source` (B13) | 필드 | 부분 구현 | `_vds_source`, `_L_source`는 있음. `_gm_id_source` 규정은 없음 | P:2590 |
| §10.6 `require_declared_spec_source`/`spec_fingerprint`/`canonical_spec`/`derived_spec` | 함수 4 | 구현됨 | SR:8172(배선 SR:8492, RH:384) / SR:8151 / RH:354 / RH:370 | P:2670-2673 |
| §10.7 `stack_kvl_vgs_limit`/`lut_vdsat_headroom`/`repair_infeasible_baseline` | 함수 3 | 구현됨 | SR:1835(호출 2267, 6716) / SR:1758 / SR:10959(호출 11245, 11311) | P:2734-2768 |
| §10.8 L2 `full_circuit_response_at_omega`/`_mna_stamp_capacitance`/`_resolve_capacitor_farad`/`build_ac_network` | 함수 4 | 구현됨 (L1 `node_pole_estimate` SR:4080은 프로덕션 호출 0으로 남음) | SR:4267 / 4192 / 4157 / 4230 | P:2873, P:3135 |
| §10.9 `l_sharing_classes`/`true_current_mirror_groups`/`gain_stage_tails`/`l_class_owners`/`audit_l_sharing_consistency` | 함수 5 | 구현됨 (층0 게이트는 CTX:14337 "미배선" 기록 뒤에 배선됨) | SR:2385 / 2358 / 2434 / 2490 / 2518(호출 SR:9454) | P:2977-3059 |
| §10.10-10.12 `synthesize_l_class_thetas`/`feasible_gm_ids`/`feasible_L_window`/`derive_role_L`/`derive_class_L`/`_group_score_interior` | 함수 6 | 구현됨 | SR:2612(호출 8509) / 1745 / 2694 / 2772(호출 8943) / 2865(호출 8987) / 10595 | P:3069-3337 |
| §10.13 `_mirror_ratio_error_pairs`/`_mirror_ratio_aggregate`/`resolve_constraint_references`/`_metric_mirror_ratio_error_input_referred` | 함수 4 | 구현됨 (결함 §12.6 #5: SR:4576에서 `names[0], names[1]`만 봄) | SR:4551 / 4540 / 8370 / 4597 | P:3409-3412 |
| §10.14 `input_referred_offset_pairs`/`materialize_input_offset_pairs`/`achievable_metric_bound` | 함수 3 | 구현됨 / `achievable_metric_bound`는 오프라인 도구 | SR:4644 / 4696(호출 8517, 10145) / SR:8271은 **엔진 호출 0**(`tests/derive_achievable_bounds.py`만 씀. SR:8421은 오류 메시지 문자열) | P:3491-3585 |
| §10.15 임계값 bisection (`achievable_metric_bound(mode=...)`) | 설계 | 미구현 (계획대로 design 단계 뒤) | SR:8271 시그니처에 `mode` 없음 | P:3592-3663 |
| §11 CircuitGraph L1/L2/L3, `flow_dir` | 제안 | 미구현. 계획 위반 없음. §12가 일부 대체(v4.43) | 코드에 `CircuitGraph`/`flow_dir` 0건. §11.4의 `<topo>.derived.json`은 §10.14 `derived_bounds_path()`(SR ~8250)에 이미 있었음(선행 구현이라 위반 아님) | P:3665-3777, P:3834 |
| §12 CSG S0~S3 / 계약 C-a~C-d / §12.6 결함 8건 | 제안 | 미구현. 계획 위반 없음 (D1~D5 승인 대기) | 코드 0건. §12.6 #5는 SR:4576-4577에서 그대로 재확인 | P:3885-3918 |
| §8 재배치 시점: §8.7 vs §9 | 순서 | 계획서 안에서 서로 모순 | §8.7은 "파일럿 증명 안에서 함께 수행, 새 함수는 새 파일에 바로 작성"이라 적었고 §9-6은 "기능이 안정된 뒤가 안전하다"고 적음. 실제로는 v4.3 이후 새 함수 수십 개가 전부 SR에 추가됨 | P:2475-2477 vs P:2527 |
| 기타 계획 내부 모순 | 문서 | 계획서 안에서 서로 모순 | (a) §2.2 파일럿 1개 vs §4.1 C7 4개 전수 (b) §0 헤더 "2026-09-08/v4.14 기준" vs 문서 v4.43 (c) §8.8:2513 끊긴 문장 (d) 신규 함수 목록 3중 관리(§2.1/§6.1/§7) (e) §10.5 C 지적 대부분 미정리 | P:397 vs P:556, P:45/P:51, P:2513, P:2629 |

### 1.1 상태별 개수 (위 표 55행 기준, 여러 함수를 묶은 행은 1로 셈)

| 상태 | 행 수 |
|---|---|
| 구현됨 | 14 (그중 §10.6~§10.14에서 계획과 코드가 같이 자란 것이 7행) |
| 이름 바꿔 구현됨 | 2 (`solve_diode_connected_vds`, `render_html_report`) |
| 부분 구현 | 5 (verify_node_voltage_consistency, 보상 방향반전, set_device_vds grep 테스트, value_amp, 추적성 태그) |
| 미구현 | 25 = 실질 22 (§7 gain-budget-first 함수군, sizing_spec, §8 파일 5·harness 4·test 6, C 테스트 10) + 계획대로 아직 대상 아님 3 (§10.15, §11, §12) |
| 폐기·대체됨 | 7 (`_resolve_device_headroom`, `make_cmrr_psrr...`, `resolve_feed_vds` 티어①, `select_L_by_role`, `headroom_fn`, `search_gm_id_and_L_for_role`, `L_bounds_from_ft_and_matching`) |
| 계획서 안에서 서로 모순 | 독립 행 2개 + 다른 상태에 겹친 5건(유령 3함수, make_cmrr 잔존, 옛 diode 이름, D3 "반영 완료", 순서) |
| §11/§12 제안이 구현돼 계획을 위반한 경우 | 0 |

## 2. §8 파일 분리 / §8.8 self-test 분리 -- 진행 경위와 현재 상태

### 2.1 연표

| 날짜/버전 | 사건 | 근거 |
|---|---|---|
| 2026-09-04 v1.1 | §8 신설: 신규 파일 5개 + harness 4개 + `tests/test_<module>.py` 분리 방침 확정 | P Version History v1.1 |
| 2026-09-04 v1.2 | `stick_diagram.py` 인라인 self-test(당시 8980~12923)도 `tests/test_stick_diagram.py` 이관 범위에 포함(사용자 지시) | P v1.2, P:2481-2496 |
| 2026-09-07 v3.4 검토 | 4관점 독립 검토: "무변경 재사용" 서술이 코드와 달라 **§8 파일 분할 단계에서 먼저 막힌다**는 판정 | 커밋 e5fbf92 메시지 |
| 2026-09-07 선행조치 (e5fbf92) | (a) 헤드룸 2중 중첩 클로저 6개(401줄)를 모듈 레벨 `_hr_*`로 추출, 자유변수 13개를 `_HeadroomTopoEnv`/`_HeadroomEvalEnv`로 명시 **완료** (b) `tests/baseline/` 로그 2개 + README **완료**. 옛 `selftest_session*.log`는 git 미추적이었음 (c) `_sorted_setmap()`으로 SD 출력 7줄 결정론화 **완료**(PYTHONHASHSEED 1~5에서 바이트 동일) (d) MNA numpy 전환 | P:2415-2420, P:2501-2512, CTX:13965-13982, SR:7420-7644, SD:943 |
| 2026-09-07~08 v4.0~v4.14 | §9에서 §8 재배치를 **6순위**로 내림("위 기능이 안정된 뒤가 안전하다"). §0.1: "새 파이프라인은 아직 한 줄도 구현하지 않았다" | P:2527, P:53 |
| 2026-09-08~10 세션46~47 (v4.15~v4.42) | B1 배선과 재탐색이 B15~B25 결함 사슬로 번짐. §10.6~§10.15 함수 수십 개가 **전부 SR에 인라인으로 추가**됨. self-test 헬퍼 `_tst_grids()`(SR:12572)도 `__main__` 블록 안에 새로 생김 | P:2592-2604, CTX:14381 |
| 2026-09-14 v4.43 | §12 CSG 근본안 제시. 구조 재편을 다시 제안했고 D1~D5 승인 대기 | P:3898-3918, CTX:14519-14541 |
| git log (282커밋) | e5fbf92 이후 "분리/extract/test 분리" 계열 커밋 **0건** | `git log --oneline` + grep |

### 2.2 멈춘 이유 (근거가 있는 것만)

1. **우선순위를 명시적으로 뒤로 미룸**: §9-6 "§8 파일 구조 재배치 -- 이건 위 기능이 안정된 뒤가 안전하다"(P:2527). "위 기능"(B1 배선, vsb, value_amp, 3티어 게이트, DP)은 아직 안정되지 않았다.
2. **회귀 수단이 인라인 self-test stdout에 묶여 있음**: §0.4가 회귀 기준을 `python sizing_recipe.py`/`python stick_diagram.py` stdout과 `tests/baseline/*.baseline.log`의 바이트 동일로 정했다(P:199-201). 배선할 때마다 기준선을 의도적으로 갱신했다(README 이력 3회). 이관은 이 기준선을 다시 만드는 일이라, 기능 작업이 돌아가는 동안 끼워 넣지 못했다.
3. **Stage 1 harness의 선행 결정이 없음**: `author_topology_spec()`은 `sizing_spec.json` 스키마와 stage 분할 규칙이 있어야 성립한다. G6(stage 분할 규칙 부재)과 A2(Area 정의 부재)가 "새 파이프라인 전에 결정 필요"로 남아 있다(P:2530-2532, P:2618, CTX:14074-14076).
4. **계획 안의 모순**: §8.7은 "새 함수는 새 파일에 바로 작성하므로 이관 비용이 없다"(P:2475-2477)고 했지만 §9는 재배치를 미뤘다. 그 사이 새 함수가 SR에 쌓여 이관 비용이 실제로 커졌다.
5. (추론, 계획서에 직접 쓰인 문장 없음) v4.43 §12.7-2가 "소비자 단위로 이관하고 옛 경로는 같은 커밋에서 삭제"하는 방식이라, §8 파일 경계를 먼저 박으면 코드를 두 번 옮기게 된다.

### 2.3 현재 수치

| 항목 | 계획 시점(v1.2) | 현재 (HEAD 5578aa3) |
|---|---|---|
| `sizing_recipe.py` 전체 | (미기록) | **15,270줄** |
| SR 인라인 self-test | (미기록) | **2,700줄** (12571~15270) |
| `stick_diagram.py` 전체 | 12,923줄 | **12,936줄** |
| SD 인라인 self-test | 8980~12923 (약 3,900줄) | **3,946줄** (8991~12936) |
| 그 외 인라인 self-test | -- | design_report 65 / topology_library 168 / run_harness 6줄 |
| `assets/tests/` | 없음 | 항목 78개: `probe_*.py` 42, `*.result.txt` 29, `baseline/`(로그 2 + README), `apply_b19p_mirror_wiring.py`, `derive_achievable_bounds.py`, `canonical_theta_star.json`. **`test_*.py` 0개, pytest 0건** |
| §8 신규 파일 / harness | 5 / 4 약속 | **0 / 0** |
| 2026-09-07 선행조치 3건 | 약속 | **3/3 완료** |

결론: §8은 **분리를 가능하게 하는 준비만 끝났고 분리 자체는 0%**다. 그 뒤 SR에 새 함수가 전부 인라인으로 붙어 분리 대상은 오히려 커졌다. `tests/`는 pytest 테스트가 아니라 조사 스크립트 보관소로 쓰이고 있다.

## 3. 같은 개념이 두 번 이상 구현된 사례

판정 기준:
- **진짜 중복**: 같은 물리 사실을 서로 다른 규칙으로 따로 계산해 결과가 갈릴 수 있음.
- **역할이 다름**: 이름은 비슷하지만 목적이 다름.
- **사장**: 대체된 옛 구현이 프로덕션 호출 0인 채 남음.

호출 수는 `agent6_callers.py`로 셌다(prod = `__main__` 이전, st = self-test).

| # | 개념 | 후보 (위치, 호출) | 판정 | 근거 |
|---|---|---|---|---|
| D1 | **미러 그룹 정의** | ① `true_current_mirror_groups()` SR:2358, connectivity(kind/gate/source), prod 1 ② `_mirror_ratio_error_pairs()` SR:4551, 선언 `matching_pairs`의 ratio에서 **`names[0], names[1]`만** 봄, prod 2 ③ SD `find_verified_differential_and_mirror_relations` 1802(prod 3) / `refine_differential_and_mirror_relations` 2494 / `_diode_like_mirror` 2453 / `_mirror_node_map_from_pairs` 5517 ④ `find_differential_and_mirror_forks` SD:1314 (prod 0, st 3) | **진짜 중복**: 미러를 connectivity로 보는지 선언으로 보는지가 함수마다 다름. ④는 사장 | B19'에서 선언 기준 11소자, connectivity 기준 18소자로 결론이 뒤집힘(P:2597). §12.6 #5에서 7소자 그룹 중 1쌍만 검사(P:3893, SR:4576-4577) |
| D2 | **스택 KVL / 적층 diode** | ① `solve_diode_stack_current()` SR:1666, 미지수 Ib, **prod 0 / st 2** ② `solve_stacked_diode_pair()` SR:3659, 미지수 vds 쌍, prod 1(SR:7859) ③ `stack_kvl_vgs_limit()` SR:1835 prod 2 ④ `_metric_stack_headroom_slack` SR:3392 ⑤ `_hr_verify_group_kvl_sum` SR:7532 ⑥ `_stack_min_vds` SR:7792 | ①은 **사장(구 C엔진)**이고 ②가 대체. ③~⑥은 역할이 다르지만(유도/제약/metric/assert) 모두 "스택 합 = 예산"을 각자 다시 셈 | SR:1686-1690 docstring("호출 규약 재검증 필요"), P:2604(B25), CTX:14266 |
| D3 | **diode-connected 판정** | ① `is_diode_connected()` SR:3287 prod 2 ② `_diode_set_cached()` SR:5452(①의 캐시, 역할 다름) ③ `find_diode_stacks()` SD:3087 **prod 0 / st 6** ④ SD 인라인 `gate == drain` SD:3872, 4279, 4329 | ③은 **사장**. ④는 단일 출처를 쓰지 않는 인라인 복제(C9 계열). 식이 한 줄이라 결과는 같음 | SD:3088 docstring("구식 자기참조") |
| D4 | **노드전압 / rail에서 vds 누적** | ① `propagate_node_voltages()` SR:3895, 한 평가 안에서 SR:3999, 4026, 7849, 8004 **4곳이 따로 재계산** ② `_hr_sum_ref_vds` SR:7515(vss에서 vds 합) ③ `_hr_resolve_vertical_group`의 `setdefault("vsb", ref_vds)`(B9 원인, 지금은 reconcile이 덮어씀) ④ `signal_path_nodes()` SR:4043 **prod 0** | **진짜 중복**: ②③과 ①이 같은 노드전압을 다른 순회로 구함. conflicts는 ①만 계산하고 아무도 읽지 않음. ④는 사장 | P:2586(B9), P:3670-3686(§11.1 "열 번쯤 만들어졌다 버려진다"), P:3890 |
| D5 | **L 유도** | `measure_L_knee` SR:2305 → `knee_L_for_kind` 2555, `derive_role_L` 2772, `derive_class_L` 2865, `feasible_L_window` 2694, `layout_grid_L_candidates` 848, `search_stage_budget_L_warm_start` 10637, (삭제) `select_L_by_role` | 대체로 역할 분담. 다만 `derive_class_L`은 15개 류에서 호출되지만 소자별 유도와 **값이 같음(무동작)** | CTX:14393-14394. 불변식 보증용이라 적혀 있지만 같은 값을 두 번 계산함 |
| D6 | **topology 로딩/캐시** | ① `load_topology()` SD:8546 (prod 8 / st 38) ② `_load_full_topology_cached()` SR:5379(①을 감쌈, prod 14) ③ `_matching_pairs_cached()` SR:5472 ④ **캐시 우회**: `load_topology` 직접 호출 SR:4845, 5056, 8493 / `json.load` SR:8315(`achievable_metric_bound`) | 계층 구조로는 역할 분담이지만 **캐시를 우회하는 호출이 남아 있음** | 세션47에 `stack_kvl_vgs_limit`의 매 평가 `load_topology()`가 평가 시간의 99.3%를 쓴 사고와 같은 패턴(CTX:14352-14353) |
| D7 | **KCL / 전류** | ① `_metric_kcl_residual` SR:4430 ② `_metric_supply_current` SR:4502 ③ SD `kcl_series_union` 3167 / `_kcl_and_matching_edges` 3298 / `_kcl_branch_map` 7431 | **역할이 다름**(잔차·공급전류 metric vs 직렬 union 그룹핑). 넷 순회와 부호 규약은 각자 구현 | 각 docstring |
| D8 | **스택 구조 구성** | SD `split_into_stacks` 3122 / `find_stack_edges` 1110 / `suggest_vertical_stack_composites` 1390 / `suggest_headroom_stack_groups` 1531(**prod 0**) / `_propose_vertical_stack_ids` 1988 / `derive_horizontal_stack_groups` 5180 vs SR `reserved_vds_for_other_stack_members` 7163 / `_base_stack_id` 9500 | 대부분 역할이 다름(레이아웃 제안 vs 헤드룸). `suggest_headroom_stack_groups`는 사장 | callers 계수 |
| D9 | **pole / 위상여유** | L1 `node_pole_estimate()` SR:4080 (**prod 0**) + `signal_path_nodes()` vs L2 `full_circuit_response_at_omega()` SR:4267 | **사장**: L2가 대체했는데 L1이 남아 있음 | SR:4343-4356 docstring |
| D10 | **HTML 보고서** | `design_report.render_html_report()` 198(세션20) vs 계획 §8.5 `render_design_report_html()` "신규" | **계획이 이미 있는 것을 다시 약속함** | design_report.py:1-20, P:2446 |
| D11 | **vds 기입** | 7곳 → `set_device_vds()` SR:3516 하나(원시 대입은 SR:3565뿐) | **중복이 해소된 사례**. 강제 테스트는 없음 | P:2578, CTX:14209 |

### 3.1 "이미 있는 것을 다시 만들려 함" 기록과 패턴

| 출처 | 이미 있던 것 | 한 일 | 분류 |
|---|---|---|---|
| CTX:14239 세션47 | 계획 §7.10이 `measure_L_knee()`/`L_bounds_from_ft_and_matching()`를 이름까지 명세 | "제안"이라며 재설계 | 계획서를 안 읽음 |
| CTX:14240 세션47 | `search_stage_budget_L_warm_start()`가 `presolve_warm_start()`에 이미 배선됨 | grep 실수로 "미배선"이라 보고하고 주석까지 씀 | 호출부 확인 실패 |
| CTX:14241 세션47 | 보상망이 `passive_elements`에 전부 선언됨, MNA가 저항을 이미 씀 | "connectivity 없다"고 판단 | JSON 선언 확인 실패 |
| CTX:14242 세션47 | 미러 공통 L 사슬(M5→M38→M36a→M7)을 사용자와 이미 추적 | `(kind,gate,source)`로 재유도 | context.md 확인 실패 |
| CTX:14243 세션47 | `parasitic_pm_deg`가 L 상한 장치(§7.11 제목) | 용도를 잊고 더 약한 근사 시도 | 계획서 제목 확인 실패 |
| CTX:14444-14446 세션47 | `_L_ROLE_MULTIPLIERS`를 막 제거함 | 같은 세션에 `mirror_ratio_error_pct <= 8.0` 상수를 새로 박음 | 방금 없앤 반패턴 재발 |
| P:3834-3843, CTX:14532-14534 세션48 | §11이 "소비자"로 적은 함수 3개를 엔진은 호출하지 않음 (`signal_path_nodes`/`node_pole_estimate` prod 0이 이 계열로 보임) | 설계 문서를 코드 호출부로 검증하지 않음 | 호출부 확인 실패 |
| CTX:2077 | role 필터 | 중복 구현임을 확인하고 폐기, 기존 `find_idiom_matches()`/`find_diode_stacks()` 사용 | 발견 후 폐기 |
| CTX:1440 | `kcl_series_union()`(세션10) | 새로 만들려다 재발견 | 코드 grep 누락 |
| CTX:14337 → SR:9454 | `audit_l_sharing_consistency()` | 만들고 미배선(★절대원칙 위반 기록), 이후 배선 | 배선 누락 |
| P:2603 (B24) | `reconcile_vsb_from_nodes`/`audit_vsb_consistency`(세션46 작성) | 호출부 0으로 방치, B25에서 배선 | 배선 누락 |

**공통 패턴**
1. 확인할 곳 셋(계획서 §7/§10, context.md, `def` grep) 가운데 하나를 빼먹는다.
2. "있다"는 확인을 `def` 존재에서 멈추고 **호출부(배선)**는 보지 않는다. 그래서 "미배선"으로 오판하거나 사장 함수를 소비자로 적는다.
3. 대체한 뒤 옛 구현을 지우지 않는다(D1④, D2①, D3③, D8, D9). 다음 grep에서 후보가 둘 이상 나오고 오판 확률이 다시 올라간다.
