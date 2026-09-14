# agent5 -- 작은 소스 모듈 / assets/tests / sizing_recipe 인라인 self-test 감사

기준: 저장소 읽기 전용, 2026-09-14. 계획서 `docs/01-plan/features/gain-budget-gmid-sizing.plan.md` v4.43 §8.2~§8.8(2336~2505행), §12.5~12.6(3844~3897행).
경로 약어: `A/` = `skills/analog-gmid-design/assets/`, `W/` = `workspaces/`.
등급: R0 그대로 재사용 / R1 국소 수정 / R2 재설계 / D 미사용 / DUP.

---

## 범위 A -- 작은 소스 모듈 전 함수

### A-1. `A/topology_library.py` (694줄, self-test `__main__` 528~694)

| 함수 (줄) | 책임 | 계획 § | 운영 호출자 (근거) | 등급 | 이관 목적지 |
|---|---|---|---|---|---|
| `miller_ota_topology` (33-52) | Miller 2단 보상식 -> `topology_fn(prev_cggs)->[gm1,gm2]` 팩토리 | §8.4 | `sizing_recipe.py:1464,1470` `_COMPENSATION_REGISTRY` -> `:8736` `_evaluate` | R0 | `gmid_sizing_engine.py`(보상식 레지스트리) |
| `  └ topology_fn` (42-50) | prev_cggs 고정점 반복용 gm | 〃 | `optimize_multistage` 반복 호출 | R0 | 〃 |
| `nmcnr_3stage_topology` (62-118) | NMCNR Eq6~11 + `topology_fn.dominant_pole_check` 부착 | §8.4 | `sizing_recipe.py:1471`, `:8736` | R1 -- 팩토리마다 4000점 스윕 진단 즉시 계산(`:117`), lru_cache(`:248`)로만 완화 | 〃 |
| `  └ topology_fn` (107-108) | 상수 gm 반환 | 〃 | 〃 | R0 | 〃 |
| `nmcnr_compensation_elements` (121-134) | Eq8/9 Cm1/Rm/Cm2 | §8.4/§8.5 | 모듈 내부 `:187`만(sizing_recipe import 목록 `:1464-1465`에 없음) | R0 | 〃 |
| `nmcnr_predict_ac_response` (137-245) | 4-노드 KCL 정확 전달함수 -> crossings/notch/dc_gain | §8.4 사후검증 metric | `sizing_recipe.py:3182`(`_metric_nmcnr_*`), self-test `:14808` | R0 | 〃 |
| `  └ _H` (213-217) | H(jw) | 〃 | 〃 | R0 | 〃 |
| `nmcnr_check_dominant_pole_approximation` (257-329) | Eq10/11 우세극 근사 성립 여부 | 진단 | `nmcnr_3stage_topology:117`만 | R1 -- valid 문턱(0.5~2.0배, 15도)을 docstring이 "임의값"이라 명시(`:306-308`) -- "상수 임의 금지" 원칙 위반 소지 | 〃 |
| `ngcc_3stage_topology` (339-363) | NGCC Eq8.a/8.b, `mu_ratio` 기본 3.9775(논문 역산 `:356`) | §8.4 | `sizing_recipe.py:1472`(레지스트리 등록만; `run_harness.SPECS` 4회로 중 사용 없음) | R1 -- 논문 역산 기본값 | 〃 |
| `  └ topology_fn` (360-361) | 상수 반환 | 〃 | 〃 | R0 | 〃 |
| `current_reuse_telescopic_topology` (373-520) | Xie&Chen Eq2-6, β/Cc 고정점, `exposed_params`/`stage_fT_targets` | §8.4 | `sizing_recipe.py:1475`, `:8736`, `:8740`(exposed_params -> ctx.derived) | R1 -- 클로저 속성 `exposed_params`를 호출마다 갱신(`:496`) = 숨은 가변 상태, §12.5.2 C-a(단일 writer·출처)와 충돌 | 〃 |
| `  └ topology_fn` (461-502) | [gmp,gmn,gmp2,gmn2] + Cc 유도(`:492`) | 〃 | 〃 | R1 | 〃 |
| `__main__` (528-694) | 5토폴로지 수치·sympy 재유도·불변성 assert | §8.8 | -- | 이관 | `tests/test_gmid_sizing_engine.py`(sympy 의존) |

DUP: 없음(정의는 이 파일에만). 참고: `run_harness._spec_current_reuse_telescopic_ota`의 `"Cc": 500e-15`(`run_harness.py:191`)는 topology.json `compensation.parameters`(`current_reuse_telescopic_ota.topology.json:189-195`: t_lln/PM_target_deg/Cf/Cs/C_Ltot)에 없어 보상식에 전달되지 않는다(`sizing_recipe.py:8723`). `spec["Cc"]`/`.get("Cc")` 직접 조회 grep 0건 -- 죽은 spec 값으로 보임(`value_from_spec` 간접 참조 가능성은 미확인).

### A-2. `A/design_report.py` (382줄, self-test 319~382)

| 함수 (줄) | 책임 | 계획 § | 운영 호출자 | 등급 | 이관 목적지 |
|---|---|---|---|---|---|
| `build_topology_device_table` (35-90) | topology.json -> matching_pairs union-find 소자 표 | §8.5 | `assemble_report_data:115` | R1 (인라인 union-find) | `instance_report_builder.py` |
| `  └ _find`/`_union` (54-62) | union-find | 〃 | 〃 | DUP 성격 -- union-find가 `sizing_recipe.py:3427`, `:10819`, `stick_diagram.py:3170`, `:5092`에도 각자 구현 | 공통 유틸 |
| `assemble_report_data` (93-137) | topology+instance.json+audit+narrative -> REPORT dict | §8.5 | `W/run_harness.py:500`; 비정본 `W/two-stage-ota-report/check_box_shape.py:113`, `check_box_shape_M5M7split.py:104`, `W/current-reuse-telescopic-ota-report/smoke_run_harness_session20.py:106` | R1 -- 경로로 instance.json 재로드, 지문(§12.5.2 C-d) 없음 | 〃 |
| `_kv_table` (177-195) | dict 리스트 -> HTML 표 | §8.5 | 내부 | R0 | 〃 |
| `render_html_report` (198-309) | REPORT -> self-contained HTML(순수) | **§8.5 `render_design_report_html()` 해당** | `save_html_report:316` | R1 -- 계획이 "신규"라 적은 함수가 이름만 다르게 이미 존재. §8.5가 요구한 헤드룸 검증/gain 배분 대조표/CMRR·PSRR·mismatch 요약 섹션은 없음(sizing은 instance.json 필드 덤프 `:228-232`) | `instance_report_builder.render_design_report_html`로 개명·확장 |
| `  └ _section` (213-216) | 섹션 번호 | 〃 | 〃 | R0 | 〃 |
| `save_html_report` (312-316) | 파일 쓰기 | §8.5 | `W/run_harness.py:501` 외 비정본 3곳 | R0 | 〃 |
| `__main__` (319-382) | Test1~4 assert 8개. Test3은 워크스페이스 instance.json 있을 때만 | §8.8 | -- | 이관 | `tests/test_instance_report_builder.py` |

§8.5 대응: `render_html_report` = `render_design_report_html` 후보(R1). docstring `:21-26`이 옛 SVG 렌더러 미이식 한계를 명시. `A/report_template.html`(git 추적)은 .py 로더 0건(grep `report_template` -> 주석뿐) -> D.

### A-3. `A/audit_current_forced.py` (180줄, CLI 153~180)

| 함수 (줄) | 책임 | 계획 § | 운영 호출자 | 등급 | 이관 목적지 |
|---|---|---|---|---|---|
| `_as_set` (46-52) | 문자열/리스트 -> set | §8.3 1단계 | `:69` | R0 | `topology_authoring.py` |
| `_theta_evidence_for_pair` (55-76) | 쌍이 theta feed A/A_signed root 또는 C target/reference로 강제되는지 | §8.3 1단계 | `audit_topology:104` | R1 -- A/A_signed/C만 인정. 엔진 feed는 B/settling_split/metric_stage_budget/`gm_id_match_vgs_of` 등 추가 존재(self-test `sizing_recipe.py:13902-13940`, `vgs_alias_map:1804`) -> 근거 누락 가능 | 〃 |
| `audit_topology` (79-119) | current_forced 양방향 대조 | §8.3 | `render_report:125` | R1 | 〃 |
| `render_report` (122-150) | 텍스트 리포트 + has_violation | §8.3 | CLI `__main__:171`만, 파이프라인 호출 0건 | D(파이프라인 미배선) | §8.3 게이트 배선 후보 |

DUP: `^def .*current_forced` 정의 0건. `stick_diagram.py:3727,8623,11119`는 current_forced 쌍을 소비할 뿐 theta 대조 아님.

### A-4. `A/sky130_lut_sweep.py` (337줄, 스크립트 313~337)

| 함수 (줄) | 책임 | 계획 § | 운영 호출자 | 등급 | 이관 목적지 |
|---|---|---|---|---|---|
| `_gen_netlist` (121-193) | ngspice .control 루프 넷리스트(op+Y11/Y12+noise) | LUT 도구(§8.2 밖) | `_run_combo:277` | R0 | LUT 생성 도구 유지 |
| `_parse_output` (196-225) | 'P' 마커 파싱 -> 6배열 | 〃 | `:284` | R0 | 〃 |
| `_ltag` (228-235) | L값 기반 체크포인트 태그 | 〃 | `:266` | R0 | 〃 |
| `_cleanup_temp` (238-261) | 임시파일 재시도 삭제 | 〃 | `:287-288` | R0 | 〃 |
| `_run_combo` (264-289) | 1조합 실행+체크포인트 | 〃 | `run_device:302` | R1 -- 미사용 인자 `iL`; 체크포인트 키가 파일명(L값·VS 인덱스)뿐, PDK/모델/격자(VGS·VDS 49점) 변경 시 스테일 재사용(§12.5.2 C-d 부재) | 〃 |
| `run_device` (292-310) | 4D 배열 조립 | 〃 | `__main__:318,321` | R0 | 〃 |

`NGSPICE_EXE`/`PDK_ROOT` 하드코딩(`:71-72`). 엔진은 npz `corner`/`temp_c`만 소비(`sizing_recipe.py:5362`). DUP 없음.

### A-5. `A/topology_to_markdown.py` (205줄, CLI 187~205)

| 함수 (줄) | 책임 | 계획 § | 운영 호출자 | 등급 | 이관 목적지 |
|---|---|---|---|---|---|
| `_flag_dangling_nets` (32-46) | S/D 단자 1개 net | §8.3 1단계 | `:88` | R0 | `topology_authoring.py` |
| `_flag_gate_only_nets` (49-62) | gate-only net | 〃 | `:89` | R0 | 〃 |
| `_net_table` (65-76) | net -> (device, terminal) 역색인 | 〃 | `:90` | R0 (§12.5.1 S1 구조층 도입 시 DUP 예정) | 〃 |
| `render_markdown` (79-184) | topology.md(사람 검토용 net 표) | §8.3, 메모리 "net 기준 표로 재검증" | CLI `__main__:201`만 | R0(도구) | 〃 |

DUP: `dangling|gate_only` 정의는 이 파일에만. `stick_diagram.run_full_circuit_audit_from_topology`(8868)는 소자 수/net-name/matching disposition 감사로 책임 다름.

### A-6. `W/run_harness.py` (531줄) -- 정본 spec 유일 진입점

| 함수 (줄) | 책임 | 계획 § | 운영 호출자 | 등급 | 이관 목적지 |
|---|---|---|---|---|---|
| 모듈 최상위 (35-68) | 절대경로 하드코딩 + **import 시 npz 로드·LUT 2개 생성** | §8.6 | `import run_harness as H` tests 25개 | R1 -- import 부작용 | spec 레지스트리와 실행부 분리 |
| `_spec_two_stage_ota` (71-128) | 정본 spec dict | §8.3 5단계 | `SPECS:307` | R1 -- 코드 dict. §8.3은 `sizing_spec.json`을 `library/`에 저장 요구 | `topology_authoring.py`(-> json) |
| `_spec_current_reuse_telescopic_ota` (131-208) | 〃 | 〃 | `SPECS:313` | R1 + 죽은 값 `Cc`(`:191`, A-1 참고) | 〃 |
| `_spec_folded_cascode` (211-245) | 〃 | 〃 | `SPECS:330` | R1 | 〃 |
| `_spec_nmcnr_amplifier` (248-299) | 〃 | 〃 | `SPECS:342` | R1 | 〃 |
| `SPECS` (304-351) | key -> topology/spec_fn/search 설정 | §8.6 | `canonical_spec:367`, `run:421`, tests 6개 직접 순회 | R1 | 〃 |
| `canonical_spec` (354-367) | 정본 spec | §8.6 | tests 19개 | R0 | `gmid_design_pipeline.py` |
| `derived_spec` (370-415) | override + `_spec_source` 기록, why 필수 | §8.6 | **호출 0건**(tests 20곳은 주석 안내문뿐) | D(만들고 미배선) | 〃 |
| `run` (417-524) | optimize_full_circuit_budget -> audit -> instance.json -> report.html | §8.6 `run_gmid_design_pipeline` 원형 | `__main__:531` | R2 -- 3단계 분리 없음, θ* print만(`:461`, §12.3 표 1행 지적), `except Exception`(`:507`)으로 실패도 exit 0 | `gmid_design_pipeline.run_gmid_design_pipeline` |

DUP: floorplan 판정식이 `run()` 안에서 두 번(`:453-454`, `:478-479`). `canonical_spec` <-> `sizing_recipe.require_declared_spec_source`(8172)는 생산자/게이트 짝(중복 아님).
정정: `import run_harness as H` tests는 23개, `canonical_spec` 호출 tests는 21개, `SPECS` 직접 사용 6개(derive_achievable_bounds, probe_lclass_warm_start, probe_mirror_common_L_wiring, probe_mirror_ratio_bound, probe_parasitic_pm_all_circuits, probe_role_L_derivation).

---

## 범위 B -- `A/tests/` 전 파일 (py 44개 + 데이터/기준선)

정적 스캔: AST(`scratchpad/inventory/agent5_scan.py` -> `agent5_tests_scan.json`). "실행 가능"은 import 심볼이 `sizing_recipe.py`/`run_harness.py` 최상위 정의에 존재하는지 + sys.path만 봄(실행 안 함). `.gitignore:29-33`이 `tests/*.result.txt`, `*.theta_star.json`, `*.unwired_theta.json`, `*.window_dump.txt`, `*.sizing_cache.json`을 무시 -> 결과 파일은 전부 **git 미추적**. py 44개는 전부 git 추적.

공통: assert가 있는 파일은 `apply_b19p_mirror_wiring`(5), `probe_b22_headroom_attribution`(1), `probe_mirror_gain_ranking`(1)뿐 -- 나머지 41개는 **print/emit만**. 9개는 워크스페이스 산출물 `W/current-reuse-telescopic-ota-report/current_reuse_telescopic_ota.instance.json`(git 추적, 최종 커밋 a1df744)을 직접 읽어 결과가 그 파일 상태에 종속(diode_vds_window, diode_min_vgs, stack_headroom_feasibility, diode_self_consistency, vs_semantics, physical_consistency, supply_current, mirror_ratio_error, metric_tiers).

| 파일 | 목적(한 줄) | 호출 엔진 공개/비공개 함수 | 엔진 로직 복제 | 분류 | 결과 파일 | 실행 가능성(정적) |
|---|---|---|---|---|---|---|
| apply_b19p_mirror_wiring.py | 미러 15소자에 `gm_id_match_vgs_of`를 library topology.json에 기록 | (엔진 import 없음, json 직접 편집 `:97-98`) | 넷리스트 기반 미러 그룹 판정(assert 5) | 운영 도구(일회성 마이그레이션) -- 이미 적용됨(`library/current_reuse_telescopic_ota.topology.json`에 `gm_id_match_vgs_of` 33회) -> 보관 or 삭제 | 없음 | 가능(재실행 시 정본 topology 덮어씀 -- 위험) |
| derive_achievable_bounds.py | 제약 임계값을 달성가능 실측으로 유도해 `<topology>.derived.json` + topology 갱신 | `achievable_metric_bound`, `derived_bounds_path`, `load_derived_bounds`, `spec_fingerprint`; H.`SPECS`,`canonical_spec` | 없음 | **운영 도구**(정본 데이터 갱신 `:108-114`) -> tests/ 밖(도구 폴더)로 이동 권장 | .result.txt 있음 | 가능 |
| probe_L_search_window.py | L 탐색을 knee 창으로 좁혀도 되는지 전수 스캔(§7.6 v4.7) | `_build_theta_evaluator`, `presolve_warm_start`; H.canonical_spec | 없음 | 일회성 진단 | 없음 | 가능 |
| probe_allocation_solvers.py | stage gm_id 배분: 전수/KKT탐욕/DP 비교(§7.9 v4.2) | `size_transistor`, `gm_gds_ratio` | `dp`(79-106)/`kkt_greedy` -- **엔진에 대응 DP 없음**(`^def .*(dp|allocat)` = `allocate_stack_headroom`뿐) = 계획 §7.9 "분리형 DP"의 프로토타입이 probe에만 존재 | 회귀 test 승격 가능(DP==전수 결정론 비교) -- 단 DP를 엔진에 배선할지 먼저 결정 필요 | 없음 | 가능 |
| probe_area_pareto.py | 면적 예산별 달성가능 경계(§7.9 v3.4) | `optimize_full_circuit_budget`(SLSQP), `is_diode_connected`, `load_topology` | 없음 | 일회성 진단(무거움) | 있음 | 가능 |
| probe_b22_headroom_attribution.py | B22 후 infeasible 원인 귀속 | `_build_theta_evaluator`, `diode_vds_window`, `optimize_full_circuit_budget` | `_window_no_mirror`(98) -- 미러 인식 이전 창 재현(비교용) | 일회성 진단(assert 1) | 있음 + unwired_theta.json + window_dump.txt | 가능(subprocess 사용) |
| probe_classab_battery_headroom.py | class-AB 배터리 헤드룸 미선언 -> M9b 예산 음수 원인 | `_build_theta_evaluator`, `InfeasibleSizingError`, `_DEFAULT_MIN_VDS_FALLBACK` | 없음 | 일회성 진단 | 있음 | 가능 |
| probe_diode_gmid_readiness.py | 헤드룸 시점에 diode gm_id/L 존재 여부(B1 5단계 전) | `_hr_resolve_vertical_group`(monkeypatch 추적), `optimize_full_circuit_budget` | `traced`(53) 래퍼만 | 일회성 진단(B1 해소됨) -> 삭제 후보 | 있음 | 가능 |
| probe_diode_min_vgs.py | diode 최소 자기일관 Vgs 스캔(§7.3 v4.13) | `solve_diode_connected_vds`, `DiodeSelfConsistencyError` | `min_vgs`(51) = 엔진 함수 격자 스캔(복제 아님) | 일회성 진단 -> 삭제 후보 | 없음 | 가능(instance.json 의존) |
| probe_diode_pass_skips.py | `apply_diode_self_consistent_gm_id` skip 분기 정당성 | 해당 함수 + `_AUTHORITATIVE_GM_ID_SOURCES`, `optimize_full_circuit_budget` | `traced` 래퍼 | 일회성 진단 | 있음 | 가능 |
| probe_diode_self_consistency.py | diode Vgs=Vds 자기일관해 vs 현재 배정 | `solve_diode_connected_vds` | 없음 | 일회성 진단 | 없음 | 가능(instance.json 의존) |
| probe_diode_vds_window.py | diode가 W 한계 안에서 허용하는 vds 구간(B16) | `gm_id_for_vgs`, `gm_id_to_id_density` | **`w_at`(71-76) = `diode_vds_window`(sizing_recipe.py:3570) 이전 수작업 판** | 일회성 진단 -> 삭제 후보(엔진 함수로 대체됨) | 없음 | 가능(instance.json 의존) |
| probe_diode_window_corner.py | diode 구간 하한/상한 선택의 면적·헤드룸 영향 | `allocate_stack_headroom`, `diode_vds_window`, `optimize_full_circuit_budget` | 없음 | 일회성 진단 | 있음 | 가능 |
| probe_full_research.py | B9/B20/B22/B25/B19' 후 파일럿 SLSQP 재탐색 | `optimize_full_circuit_budget`, `audit_vsb_consistency` | 없음 | 일회성 진단(θ*를 json.dump `:156`) | 있음 | 가능 |
| probe_gm_id_monotonicity.py | `_solve_vgs` 단조 전제 검사 + 수정 유지 감시(B20) | `_gm_id_curve`, `_solve_vgs`, `_query`, `_log_ID` 등 비공개 | `rightmost_root`(331-348) = `_solve_vgs`(522)의 **의도적 독립 참조구현**; `idu_at_vgs`(254) = `id_density_at_vgs`(609-622)와 동일식; `strong_branch_vgs`(243) | **회귀 test 승격 가능**(docstring "하나라도 어긋나면 회귀", 결정론 oracle 비교) -- `idu_at_vgs`는 엔진 메서드로 교체 | 있음 | 가능 |
| probe_gmid_gain_landscape.py | gm_id 축 gain/V_A/면적 거동(§10.2 A10/A11) | `size_transistor` | 없음 | 일회성 진단 | 없음 | 가능 |
| probe_interp_scheme_loo.py | L 보간 방식 leave-one-out 선택(B15①) | `_multilinear_interp`, `_grids_list`, `_log_ID` | `curves`(93) -- `_gm_id_curve`(499)의 대안 3종 재구현(연구 변형) | 일회성 진단(B15 결정 완료) | 있음 | 가능 |
| probe_l5c_stage2out_L.py | L5c 픽스처 `L_stage2out_p/n` 고정점 선택 | `_build_theta_evaluator` | 없음 | 일회성 진단(L5c 픽스처 근거 -> self-test 이관 시 참고) | 있음 | 가능 |
| probe_lclass_warm_start.py | l_class theta 웜스타트 제약/x0/자유변수 확인 | `_build_theta_evaluator`, `presolve_warm_start`, `_metric_device_footprint` | 없음 | 일회성 진단 | 있음 | 가능 |
| probe_lut_L_interpolation.py | L 보간이 gm/ID를 비물리값으로 만드는지(PHYS_MAX 40 `:129`) | `_multilinear_interp` | `curve_consistent`(119) -- `_gm_id_curve` 대안(로그 GM) | 회귀 test 승격 가능(비물리 판정 개수, 결정론) | 있음 | 가능 |
| probe_matching_pair_divergence.py | 매칭 쌍 사이징 동일성 전수 | `_optimize_theta_slsqp`(추적), `optimize_full_circuit_budget` | `traced` 래퍼 | 일회성 진단 | 있음 | 가능 |
| probe_metric_dashboard.py | 파일럿 6개 계기판 metric 일괄(§0.4) | `optimize_full_circuit_budget`, `is_diode_connected` | 없음 | 운영 도구(엔진 수정마다 재실행용 점검) | 있음 | 가능 |
| probe_metric_tiers.py | metric 3티어 실측 분류(§7.6 v4.4) | `compute_metric`, `SizingContext` | 없음(perf_counter 시간 측정 `:59-61` -> 비결정) | 일회성 진단 | 없음 | 가능(instance.json 의존) |
| probe_mirror_common_L.py | 미러 동치류 공통 L 결정 요인 | LUT 비공개 `_query`/`_log_ID`/`_w_ref_effective` | **`idu`(97-99) = `id_density_at_vgs`와 동일식**; 동작점 OP 상수 표 하드코딩(`:92-109` 부근) | 일회성 진단 | 있음 | 가능 |
| probe_mirror_common_L_wiring.py | 미러 동치류 L이 실제로 갈려 있는지 | `_build_theta_evaluator`, `vgs_alias_map`, `load_topology`, **`_L_ROLE_MULTIPLIERS`** | 없음 | 일회성 진단 | 있음 | **불가 -- `_L_ROLE_MULTIPLIERS` 삭제됨**(sizing_recipe 최상위 정의 없음, 존재하는 것은 `_L_ROLE_TARGETS:2766`; self-test `:13724` "옛 _L_ROLE_MULTIPLIERS는 삭제됐다") -> 삭제 후보 |
| probe_mirror_design_space.py | 깨진 미러 3그룹을 고칠 동작점 존재 여부(B19) | `optimize_full_circuit_budget`, `gm_id_for_vgs` | **`_mirror_groups_from_netlist`(160) 넷리스트 (gate,source,kind) 그룹핑**(아래 2개 probe와 3중 복제, 엔진 대응 함수 없음 -- 엔진 `vgs_alias_map:1804`는 선언 기반); **`_idu_at_vgs`(220) = `id_density_at_vgs`**; `widths_at`(236) = 미러 강제 사이징 수작업판 | 일회성 진단(B19' 배선 완료) | 있음 | 가능 |
| probe_mirror_gain_ranking.py | 미러 공유 VGS를 gain 기준으로 선택 | `_build_theta_evaluator`, `compute_metric`, `optimize_full_circuit_budget` | `_mirror_groups`(154) 3중 복제; **`forced`(181-210) = 미러 강제 사이징(W=L·ID/IDu, gds=gm/ratio, 포화 `vds<2/gm_id`) 재구현** -- 엔진 `gm_id_match_vgs_of` 경로(self-test `:14040` 섹션 검증)와 중복 | 일회성 진단(assert 1) | 있음 | 가능 |
| probe_mirror_infeasibility.py | B19' 배선 후 infeasible 소자 단위 원인 | LUT 비공개 | **`idu_at_vgs`(87) = `id_density_at_vgs`** | 일회성 진단 | 있음 | 가능 |
| probe_mirror_ratio_bound.py | `mirror_ratio_error` 상한을 선언에서 유도하기 위한 실측 | `_build_theta_evaluator`, `_matching_pairs_cached`, `estimate_mismatch_sigma`; `canonical_theta_star.json` 읽음(`:77`) | 없음 | 일회성 진단 | 있음 | 가능 |
| probe_mirror_ratio_error.py | 매칭 쌍 VDS 차이의 계통 전류오차(§10.2 A4) | `estimate_mismatch_sigma`, `_METRIC_UNITS` | **dVDS/V_A 인라인 계산(`:650-663`) = `_mirror_ratio_error_pairs`(4551)/`_metric_mirror_ratio_error`(4617)**; `names[0],names[1]`만 봄(`:651`) = 계획 §12.6 #5 결함과 같은 한계 | 일회성 진단(엔진 metric으로 대체됨) -> 삭제 후보 | 없음 | 가능(instance.json 의존) |
| probe_mirror_wiring_readiness.py | 미러 18소자 `gm_id_match_vgs_of` 강제 여부(배선 전) | `_build_theta_evaluator`, `_gm_id_already_authoritative`, `optimize_full_circuit_budget` | `mirror_groups`(92) 3중 복제 | 일회성 진단(배선 완료) -> 삭제 후보 | 있음 | 가능 |
| probe_node_voltage_audit.py | `propagate_node_voltages`/`audit_vsb_consistency`로 B9 상태 측정 | 두 함수 + `_build_theta_evaluator`, `optimize_full_circuit_budget` | 없음 | 일회성 진단(B9 해소) | 있음 + theta_star.json | **조건부 -- sys.path에 ASSETS만 넣고(`:34`) `import run_harness`(`:37`)** -> workspaces를 PYTHONPATH/cwd에 두지 않으면 ImportError |
| probe_parasitic_pm_all_circuits.py | `parasitic_pm_deg` 4회로 전수(§7.11) | `_build_theta_evaluator`, `_load_full_topology_cached`, `node_pole_estimate`, `signal_path_nodes`, `optimize_full_circuit_budget`; `canonical_theta_star.json` | 없음 | 회귀 test 승격 가능(4회로 일반성 = §12.7 DoD "필요 없는 회로에서 무동작") -- 단 perf_counter 출력은 제거 필요 | 있음 | 가능 |
| probe_physical_consistency.py | §7.5 검증기가 못 보는 것(B7/B8/B9) | `load_topology` | **`propagate`(48-68) 노드전압 전파 재구현 = `propagate_node_voltages`(3895)**(프로토타입 재현이 목적); 순회 순서 뒤집기 비교 = §12.5.2 C-a `test_order_shuffle_invariance`(미실행)의 원형 | 회귀 test 승격 가능 -- **엔진 `propagate_node_voltages`에 대해** 순서 불변성 assert로 재작성 | 없음 | 가능(instance.json 의존) |
| probe_prevention_wiring.py | §3.3 C1~C10 방지장치 배선 여부(B11) | `_feed_vds_fallback`, `load_topology`, `inspect.getdoc` | 없음 | 회귀 test 승격 가능(docstring `:25` "PASS로 바뀌면" -- 현재는 상태 기록형, assert 없음) | 없음 | 가능 |
| probe_ratio_pair_analysis.py | ratio 쌍이 실제 전류미러인지 connectivity 확인 | `optimize_full_circuit_budget`, `is_diode_connected` | 없음 | 일회성 진단 | 있음 | 가능 |
| probe_revalidation_scope.py | 레이아웃 재검증이 건너뛰는 metric 측정 | `_collect_device_refs`, `load_topology` | 없음 | 회귀 test 승격 가능(결정론 표) | 있음 | 가능 |
| probe_role_L_derivation.py | `L_role` 상수 -> 유도 대체 결과 4회로 전수 | `_L_ROLE_TARGETS`, `_diode_set_cached`, `feasible_L_window`, `knee_L_for_kind`, `_build_theta_evaluator`; `canonical_theta_star.json` | 없음 | 회귀 test 승격 가능(4회로 무동작 증명) | 있음 | 가능 |
| probe_runtime_budget.py | L_combo 전수 스캔 실행시간 예산(B4) | `_build_theta_evaluator`, `presolve_warm_start` | 없음 | 일회성 진단(시간 측정, 비결정) | 없음 | 가능(`sys.exit` 1곳) |
| probe_stack_headroom_feasibility.py | diode 자기일관 vds가 스택 KVL 예산에 드는가(§7.3) | `solve_diode_connected_vds` | 없음 | 일회성 진단(B1 해소) -> 삭제 후보 | 없음 | 가능(instance.json 의존) |
| probe_stacked_diode_options.py | 적층 diode(M11a/M11b/M12) 선택지 계산(B24) | LUT 비공개 | **`idu`(79) = `id_density_at_vgs`; `widths`(83-95) 적층 바디효과 W 계산 = `solve_stacked_diode_pair`(3659, B25)** | 일회성 진단(B25로 대체) -> 삭제 후보 | 있음 | 가능 |
| probe_supply_current.py | `sum_current`가 진짜 공급전류인지(A3) | `load_topology` | **레일 유입/유출 전류 인라인 계산(`:42-96`) = `_metric_supply_current`(4502)의 근거판**; 게인스테이지 소자명 하드코딩(`:47-48`) | 일회성 진단(엔진 metric으로 대체) -> 삭제 후보 | 없음 | 가능(instance.json 의존) |
| probe_vds_assignment_paths.py | vds가 어느 경로에서 정해지는지 monkeypatch 계측(§7.3 v4.3) | `resolve_feed_vds`, `_feed_vds_fallback`, `allocate_stack_headroom`, `_hr_resolve_vertical_group`, `_metric_stage_budget_vds_by_device`, `DEFAULT_POLICY` | `traced_*` 래퍼만 | 일회성 진단 | 없음 | 가능 |
| probe_vs_semantics.py | `vs` 정의를 LUT 정본에 맞춰 검산(B9) | `load_topology` | **노드전압 복원 인라인(`:30-45`) = `propagate_node_voltages`(3895)** | 삭제 후보 | 없음 | **실행은 되나 무의미 -- instance.json이 이제 `vsb` 51개/`vs` 0개인데 `if "vs" not in e: continue`(`:52`)로 전 소자 skip** |

데이터/기타:
| 파일 | 내용 | 비고 |
|---|---|---|
| `canonical_theta_star.json` (git 추적) | 지난 수렴 θ* | 생산자 py 없음(grep). 소비자 probe 4개(mirror_common_L_wiring `:70`, mirror_ratio_bound `:77`, parasitic_pm_all_circuits `:69`, role_L_derivation `:48`). 계획 `:3740`, `:3823`이 "엔진이 안 읽는다" 지적 -> §12.5.1 S3 아카이브 시드 후보 |
| `skipchk.result.txt` (무시됨) | "파일럿 metric 17개 -- 재검증이 영향 있음으로 볼까?" 표 | 생산 스크립트 없음(grep `skipchk` 0건). 내용상 probe_revalidation_scope 계열의 옛 산출물(그 probe의 OUT은 `probe_revalidation_scope.result.txt` `:55`) -> 고아, 삭제 |
| `baseline/README.md`, `baseline/sizing_recipe.selftest.baseline.log`(361줄), `baseline/stick_diagram.selftest.baseline.log`(1257줄) | self-test stdout 기준선 | 범위 C 참조 |

엔진 로직 복제 요약(B):
1. IDu(VGS 직접) `exp(_query(_log_ID))*L/_w_ref_effective(L)` 6곳: gm_id_monotonicity:254, mirror_design_space:220, mirror_infeasibility:87, mirror_common_L:97, stacked_diode_options:79, mirror_gain_ranking:298(인라인) <-> `SemiEmpiricalGmIdLUT.id_density_at_vgs`(sizing_recipe.py:609-622) 동일식.
2. 넷리스트 미러 그룹 (gate,source,kind): mirror_design_space:160, mirror_gain_ranking:154, mirror_wiring_readiness:92 -- probe 간 3중 복제, 엔진에 대응 공개함수 없음.
3. 노드전압 전파: physical_consistency:48, vs_semantics:30 <-> `propagate_node_voltages`(3895).
4. 미러 강제 사이징: mirror_gain_ranking.forced:181, mirror_design_space.widths_at:236 <-> 엔진 `gm_id_match_vgs_of` 경로.
5. diode vds 창: diode_vds_window.w_at:71 <-> `diode_vds_window`(3570).
6. 적층 diode W: stacked_diode_options.widths:83 <-> `solve_stacked_diode_pair`(3659).
7. 미러비 계통오차: mirror_ratio_error:650 <-> `_mirror_ratio_error_pairs`(4551).
8. 공급전류: supply_current:42 <-> `_metric_supply_current`(4502).
9. gm/ID 곡선 대안: interp_scheme_loo.curves:93, lut_L_interpolation.curve_consistent:119 <-> `_gm_id_curve`(499) (연구 변형, 의도적).
10. `_solve_vgs` oracle: gm_id_monotonicity.rightmost_root:331 (의도적 독립 참조 -- test oracle로 유지 가치).

---

## 범위 C -- `sizing_recipe.py` 인라인 self-test (`if __name__ == "__main__":` 12571 ~ 파일 끝 15269)

스캔: AST 최상위 문장 단위(`agent5_selftest_sections.json`). 경계는 `print("# ...")`(major, 연속 줄 병합)와 `print("  [...]")`(sub). A=assert 수, R=raise 수(주로 "에러가 안 났다" `raise AssertionError` 부정 케이스), 의존=앞 섹션에서 처음 대입된 `_`접두 전역을 읽음(한두 글자 루프변수 제외).

외부 파일(전 섹션): 임시 topology는 **전부 `tempfile.TemporaryDirectory()`**(`:12641, 12941, 13074, 13302, 13419, 13973, 14006, 14076, 14117, 14169, 14194, 14247, 14300, 14337, 14415, 14432, 14609, 14649`). 영구 파일 의존은 `A/sky130_regression_reference.json`(`:12669`), `A/sky130_nfet_pfet_lut_sample.npz`(`:13199`, L5c), `A/library/*.topology.json` 4종(`_lib_dir_recipe` `:13965`). 워크스페이스 instance.json 의존 0건. SLSQP(`search_method="slsqp"`) 호출 0건(grep: 유일한 `search_method="slsqp"`는 엔진 `achievable_metric_bound:8347`).

| 줄 범위 | 섹션 | 검증 대상 엔진 함수 | A | R | 판정 | 무거움 | 외부 파일 | 앞 섹션 의존 |
|---|---|---|---|---|---|---|---|---|
| 12572-12586 | 헬퍼 `_tst_grids` 정의 | -- | - | - | - | - | - | - |
| 12587-12600 | 공통 준비(stdout, 예시 스펙 상수) | -- | 0 | 0 | - | - | - | - |
| 12601-12613 | toy LUT 실행 예시 -- **전역 `lut` 생성** | `build_toy_lut`, `check_quasi_static`, `converge_with_parasitics` | 0 | 0 | **print-only** | 경 | - | - |
| 12614-12634 | `find_optimal_sizing()` 데모 | `find_optimal_sizing` | 0 | 0 | **print-only** | 중 | - | `lut` |
| 12635-12659 | `_COMPENSATION_REGISTRY` allowlist 거부 | `optimize_full_circuit_budget` | 1 | 1 | assert | 경 | tmp bad.topology.json | - |
| 12660-12681 | 배치 7-1 `run_regression_case` 골든 대조 | `run_regression_case`(->`optimize_multistage`) | 1 | 0 | assert(+ `[PASS]` print) | 중 | regression_reference.json | - |
| 12682-12686 | (B/C/F 엔진 헤더) | -- | 0 | 0 | - | - | - | - |
| 12687-12702 | B엔진 역산 | `solve_id_for_target_gm` | 2 | 0 | assert | 경 | - | `lut` |
| 12703-12721 | C엔진 diode 스택 전류 역산 | `solve_diode_stack_current`, `_invert_gm_id_for_current` | 1 | 0 | assert | 경 | - | `lut` |
| 12722-12742 | F엔진 metric 레지스트리 | `compute_metric`, `SizingContext` | 3 | 1 | assert | 경 | - | - |
| 12743-12809 | L4 finger 반올림 재검증 | `revalidate_finger_override`, `size_transistor` | 8 | 0 | assert | 경 | - | `lut` |
| 12810-12900 | L4b 쌍 finger 조정 | `apply_and_revalidate_pair_adjustment` (헬퍼 `_l4b_ctx_for`) | 9 | 0 | assert | 경 | - | `lut` |
| 12901-13031 | L4c M3a 11소자 finger fixup | `run_topology_pipeline_with_finger_fixup`, `_blocked_euler_rows` | 17 | 0 | assert | **중~중상**(stick_diagram 파이프라인) | tmp m3a_row | `lut` |
| 13032-13134 | L5 optimize_full_circuit_budget 실배선 | `optimize_full_circuit_budget`, `solve_diode_connected_vds` | 5 | 0 | assert | **중상** | tmp | **L4c `_l4c_L/_l4c_gds/_l4c_gm_id/_l4c_m3a_netlist/_l4c_matching_pairs_meta/_l4c_names/_l4c_r/_l4c_vds`** |
| 13135-13191 | L5b resolve_stack_layout | `resolve_stack_layout` | 4 | 0 | assert | 경 | library current_reuse | - |
| 13192-13447 | **L5c 헤드룸 singleton(파일럿 51소자, 실측 sky130 LUT)** | `optimize_full_circuit_budget`(grid 3, `stop_after_sizing=True` `:13370-13371`; 음수 케이스 grid 1 `:13424`), `diode_vds_window`, `SemiEmpiricalGmIdLUT` | 7 | 1 | assert + **특정 ValueError 메시지면 "참고(정직한 한계)" print로 흡수**(`:13372-13375`) | **최중**(실측 LUT 2개 로드, 전체회로 사이징 ×3+1) | npz, library current_reuse | - |
| 13448-13561 | L4d 매칭 finger growth | `suggest_matching_finger_growth`, `apply_and_revalidate_matching_finger_growth`, `run_matching_safety_with_finger_growth` | 11 | 0 | assert | 경~중 | library current_reuse | `lut` |
| 13562-13613 | L4e 매칭 안전 루프 | `run_matching_safety_with_finger_growth` | 7 | 0 | assert | 경 | - | **L4d `_l4d_ctx/_l4d_metrics/_l4d_r/_l4d_tight`** |
| 13614-13617 | (7-3b/e/f 헤더) | -- | 0 | 0 | - | - | - | - |
| 13618-13633 | 7-3b allocate_stack_headroom | `allocate_stack_headroom` | 2 | 0 | assert | 경 | - | - |
| 13634-13645 | gm_id 연동 헤드룸 | `allocate_stack_headroom` | 2 | 0 | assert | 경 | - | `_hr_stack`(13618) |
| 13646-13673 | HeadroomPolicy.thin_roles | `allocate_stack_headroom` | 3 | 0 | assert | 경 | - | - |
| 13674-13698 | 7-3e search_gm_id_for_role (헬퍼 `_feasible_w`) | `search_gm_id_for_role` | 3 | 0 | assert(oracle 비교) | 경 | - | `lut` |
| 13699-13712 | 'load' role (헬퍼 `_ro_direct`) | `search_gm_id_for_role` | 1 | 0 | assert | 경 | - | `_role_L/_role_vds/_role_id_target/_feasible_check`(13674) |
| 13713-13721 | W_bounds 불가 -> ValueError | `search_gm_id_for_role` | 0 | 1 | raise-기반 | 경 | - | `_role_*`(13674) |
| 13722-13797 | derive_role_L clamp 양방향 (헬퍼 `_drl_case`) | `derive_role_L`, `derive_class_L`, `feasible_L_window`, `knee_L_for_kind` | 7 | 1 | assert | 경~중(창 스캔) | - | `lut` |
| 13798-13821 | 계통 미러비 오차 단위 | `compute_metric` | 3 | 0 | assert | 경 | - | - |
| 13822-13845 | value_from_constraint | `resolve_constraint_references` | 1 | 1 | assert | 경 | - | - |
| 13846-13878 | 웜스타트 조인트 스캔 점수 | `_group_score_interior`, `_group_score_metric` | 3 | 2 | assert | 경 | - | - |
| 13879-13897 | estimate_area_budget | `estimate_area_budget` | 2 | 0 | assert | 경 | - | - |
| 13898-13901 | (7-3d 헤더) | -- | 0 | 0 | - | - | - | - |
| 13902-13940 | feed A/C/B/settling_split/metric_stage_budget (5개) | `apply_theta_feed`, `compute_metric` | 5 | 0 | assert | 경 | - | `lut` |
| 13941-13948 | 미등록 feed -> ValueError | `apply_theta_feed` | 0 | 1 | raise-기반 | 경 | - | - |
| 13949-13985 | roles 없는 회로 (`_lib_dir_recipe` 정의 `:13965`) | `optimize_full_circuit_budget` | 2 | 0 | assert | 중 | library folded_cascode | `lut` |
| 13986-14039 | 합성 sizing_roles 그리드서치 최적값 | `optimize_full_circuit_budget`(grid 5 `:14011`), `apply_theta_feed`, `_lerp` | 5 | 0 | assert | 중 | tmp | `lut` |
| 14040-14113 | gm_id_match_vgs_of | `_build_theta_evaluator`, `diode_vds_window` | 3 | 0 | assert | 중 | tmp | `lut` |
| 14114-14129 | gm_id_match_vgs_of 미존재 참조 | `_build_theta_evaluator` | 1 | 1 | assert | 경 | tmp | `_gmv_spec/_gmv_topo`(14040) |
| 14130-14190 | vds_match_vgs_of (`_tst_grids` 사용) | `_build_theta_evaluator` | 3 | 0 | assert | 중 | tmp | `lut` |
| 14191-14205 | vds_match_vgs_of 순환 | `_build_theta_evaluator` | 1 | 1 | assert | 경 | tmp | `_vmv_spec/_vmv_topo`(14130) |
| 14206-14277 | fixed-point worklist | `_build_theta_evaluator` | 4 | 0 | assert | 중 | tmp | `lut` |
| 14278-14316 | budget_reference 상호참조 | `_build_theta_evaluator` | 1 | 1 | assert | 경 | tmp | `_fpw_vdd`(14206), `lut` |
| 14317-14327 | diagnose_sizing_roles_gap 준비(`_diag_lut`) | `build_toy_lut` | 0 | 0 | 준비만 | 경 | - | - |
| 14328-14368 | gap 진단 정상 케이스 | `diagnose_sizing_roles_gap` | 5 | 0 | assert | 경 | tmp | `_diag_lut`(14317) |
| 14369-14394 | 실제 folded_cascode / nmcnr gap | `diagnose_sizing_roles_gap` | 2 | 0 | assert | 경~중 | library 2종 | `_lib_dir_recipe`(13949) |
| 14395-14419 | require_declared_spec_source 4건 | `require_declared_spec_source` | 1 | 1 | assert | 경 | tmp, library current_reuse | `_lib_dir_recipe` |
| 14420-14426 | has_theta 조기 반환 | `diagnose_sizing_roles_gap` | 1 | 0 | assert | 경 | library two_stage_ota | `_lib_dir_recipe` |
| 14427-14442 | 불가능 제약 -> ValueError | `optimize_full_circuit_budget`(grid 5 `:14437`) | 0 | 1 | raise-기반 | 중 | tmp | **`_ofc_spec/_ofc_topo`(13986)** |
| 14443-14582 | two_stage_ota 전체회로 | `optimize_full_circuit_budget` | 4 | 1 | assert | **중상** | library two_stage_ota | `_lib_dir_recipe`, `lut` |
| 14583-14635 | matching_pairs L 강제 일치(compensation vs L_role) | `optimize_full_circuit_budget`, `knee_L_for_kind` | 2 | 0 | assert | 중 | tmp | `lut` |
| 14636-14661 | L_role끼리 불일치 -> 에러 | `optimize_full_circuit_budget` | 0 | 1 | raise-기반 | 중 | tmp | `_lrec_topo`(14583) |
| 14662-14682 | 재현성(같은 spec 재호출 동일) | `optimize_full_circuit_budget` | 2 | 1 | assert | **중상**(2회 재실행) | - | **`_tso_path/_tso_spec/_tso_result/_tso_all_names`(14443)** |
| 14683-14686 | (7-3g/h/i 헤더) | -- | 0 | 0 | - | - | - | - |
| 14687-14693 | noise_1f SID_1F 없음 -> ValueError | `noise_1f_density` | 0 | 1 | raise-기반 | 경 | - | `lut` |
| 14694-14709 | SID_1F 합성 LUT 스케일링 | `SemiEmpiricalGmIdLUT` | 1 | 0 | assert | 경 | - | `lut` |
| 14710-14723 | flicker+thermal 합 | `compute_metric` | 1 | 0 | assert | 경 | - | `_lut_with_noise/_freq_test/_sid1f_expected/_w_target_test`(14694) |
| 14724-14738 | pelgrom mismatch | `estimate_mismatch_sigma`, `compute_metric` | 2 | 0 | assert | 경 | - | - |
| 14739-14750 | cmrr/psrr diff_pair_tail | `compute_metric` | 2 | 0 | assert | 경 | - | - |
| 14751-14759 | 미등록 family -> ValueError | `compute_metric` | 0 | 1 | raise-기반 | 경 | - | `_ctx_cmrr`(14739) |
| 14760-14782 | nmcnr metric 등록 확인 | (topology json 대조) | 7 | 0 | assert | 경 | library nmcnr | `_lib_dir_recipe` |
| 14783-14818 | nmcnr gain/pm 손계산 대조 | `_nmcnr_stage1_rout`, `compute_metric` (+`nmcnr_predict_ac_response` 직접 `:14808`) | 3 | 0 | assert | 경 | - | - |
| 14819-14830 | 0dB 교차 없음 -> 에러 | `compute_metric` | 0 | 1 | raise-기반 | 경 | - | `_nmcnr_sized/_nmcnr_spec`(14783) |
| 14831-14889 | telescopic_class_ab 역할 배정(connectivity assert) | (topology 대조, `_crt_by_name/_crt_transistors` 정의) | 16 | 0 | assert | 경 | library current_reuse | `_lib_dir_recipe` |
| 14890-14938 | telescopic_class_ab cmrr | `compute_metric` | 3 | 0 | assert | 경 | - | - |
| 14939-14991 | telescopic_class_ab_cmfb 유도 | (connectivity assert) | 12 | 0 | assert | 경 | - | `_crt_by_name/_crt_transistors`(14831) |
| 14992-15071 | cmfb cmrr/psrr 전면 | `_telescopic_class_ab_open_loop_gains`, `_cmfb_amp_gain_diode_load`, `compute_metric` | 6 | 1 | assert | 경 | - | `_cmfb_roles`(14939) |
| 15072-15092 | psrr Ann_open | `compute_metric` | 1 | 1 | assert | 경 | - | `_adm_o/_ann_o/_cmfb_ctx/_cmfb_spec`(14992) |
| 15093-15165 | smallsignal_ratio/gain 일반화 | `_full_circuit_response`, `compute_metric` | 7 | 0 | assert | 경~중(MNA) | library current_reuse | - |
| 15166-15213 | current_reuse_telescopic_topology 고정점(4-stage) | `optimize_multistage`, `_COMPENSATION_REGISTRY` | 9 | 0 | assert | 중 | - | `lut` |
| 15214-15269 | validate_theta_declaration_order 4건 | `validate_theta_declaration_order` | 5 | 0 | assert | 경 | library 4종 | - |

합계(스캔): assert 약 220개, raise 기반 부정 케이스 22곳. **판정이 print뿐인 섹션 2개**(12601-12613, 12614-12634 데모) + 준비 섹션 1개(14317). 부분적으로 판정을 print로 흡수하는 곳 1개(L5c `:13372-13375`).

### C-1. main guard 안 헬퍼 5개

| 헬퍼 (줄) | 하는 일 | 자유변수(클로저) | 호출처 | fixture화 |
|---|---|---|---|---|
| `_tst_grids(spec)` (12572-12586) | spec에 `L_candidates`/`VDS_candidates`/`gm_id_grid`를 LUT 격자로 setdefault(toy 픽스처를 정본 spec 모양으로) | 없음(순수, spec 인자만) | 6곳: `:14173, 14251, 14304, 14345, 14613, 14653` | **가능 -- conftest 헬퍼/fixture 1순위**(순수) |
| `_l4b_ctx_for(crit, crit_gds, harm, harm_gds)` (12842-12852) | Ma/Mb/Xa/Xb 4소자 `SizingContext` 조립 | `_l4b_L`, `_l4b_vds`(섹션 전역) | 2곳: `:12858, 12879` | 가능 -- L/vds를 인자로 올린 factory fixture |
| `_feasible_w(g)` (13685-13689) | gm_id별 W 계산(ValueError면 None) -- `search_gm_id_for_role` oracle | `lut`, `_role_id_target`, `_role_L`, `_role_vds` | `:13691` 리스트컴프 | 비권장 -- test 함수 내부 oracle로 유지(`lut` fixture만 주입) |
| `_ro_direct(g)` (13704-13705) | ro=1/gds oracle | 위와 동일 | `:13706-13709` | 비권장 -- 내부 oracle |
| `_drl_case(_ID, _wb, _want)` (13748-13761) | derive_role_L clamp 방향 케이스 | `_drl_spec`, `_drl_ctx`(**`_drl_ctx.sized["Mm"]`를 변경** `:13750`), `_drl_vds`, `_drl_knee`, `lut` | 2곳: `:13763-13764` | 가능 -- `pytest.mark.parametrize` 2케이스, 공유 ctx 변경은 케이스별 새 ctx로 |

### C-2. 기준선 / `.gitignore`

* `A/tests/baseline/README.md`: 대조 단위는 **stdout 전체 diff**, 재생성 `python stick_diagram.py > /tmp/sd.log`, `python sizing_recipe.py > /tmp/sr.log` 후 `diff`(0줄이면 회귀 없음). PYTHONHASHSEED 1~5 바이트 동일 확인 기록. 갱신 이력 9회(B20/B25+B9/B19'/2026-09-10 (1)~(6)) -- 대부분 L5c 완주 줄 수치 변경.
* 기준선 크기: `sizing_recipe.selftest.baseline.log` 361줄, `stick_diagram.selftest.baseline.log` 1257줄.
* `.gitignore:16` `*.log` + `:19` `!skills/analog-gmid-design/assets/tests/baseline/*.log` -> 기준선 2개만 추적(git ls-files 확인). `A/selftest_session6*.log` 6개, `A/sky130_lut_sweep_extend_L.log`는 `git check-ignore`로 `.gitignore:16`에 무시됨 확인 -> 재현 불가 옛 산출물(계획 §8.8 v4.0 정정과 일치).

### C-3. 이관 난점

1. **순서 의존(전역 공유)**: 전역 `lut`(12601 toy LUT)을 약 30개 섹션이 읽음; `_lib_dir_recipe`(13965)를 7개 섹션이 읽음; 강한 사슬 -- L4c->L5(`_l4c_*` 8개), L4d->L4e, 13674->13699->13713, 13986->14427, 14040->14114, 14130->14191, 14206->14278, 14443->14662(`_tso_result` 재사용), 14583->14636, 14694->14710, 14783->14819, 14831->14939->14992->15072(4단 사슬). pytest 분리 시 session fixture(`toy_lut`, `lib_dir`) + 사슬별 module fixture 필요.
2. **무거운 섹션**: L5c(13192-13447, 실측 npz + 전체회로 사이징 grid 3 + 음수 grid 1), L4c/L5(12901-13134), two_stage_ota 전체(14443-14582)와 재현성 재호출(14662-14682), 그리드 5점 2곳(14011, 14437), 레지스트리 골든(12665), 4-stage 고정점(15166). SLSQP는 없음. -> `@pytest.mark.slow` 분리 후보.
3. **print-only 판정**: 2개 섹션(데모) + L5c의 조건부 흡수 1곳. 이 데모들은 test가 아니라 예제 -- test 파일이 아니라 docs/예제로 옮기거나 assert 추가 필요.
4. **기준선 방식 불일치**: 현 회귀 기준은 stdout 바이트 diff인데 pytest는 stdout을 캡처·재배열 -> 이관 후 README의 `diff` 절차가 성립하지 않음. 이관 직후 1회는 "옛 `python sizing_recipe.py` stdout == 이관 test의 print 순서"로 대조하고, 이후는 assert 기반으로 전환해야 함(§8.8 "동일 PASS/FAIL 집합"과 표현 차이).
5. 부정 케이스 22곳이 `try: ...; raise AssertionError(...) except ValueError` 패턴 -> `pytest.raises` 기계 치환 가능(난점 낮음).

---

## 요약

**A -- R0(그대로 재사용)**: topology_library의 `miller_ota_topology`, `nmcnr_compensation_elements`, `nmcnr_predict_ac_response`(+`_H`), 각 상수 `topology_fn`; design_report `_kv_table`, `_section`, `save_html_report`; audit_current_forced `_as_set`; sky130_lut_sweep `_gen_netlist`, `_parse_output`, `_ltag`, `_cleanup_temp`, `run_device`; topology_to_markdown 4개 전부; run_harness `canonical_spec`.
**A -- R1 주요**: `render_html_report`(=§8.5 `render_design_report_html`, metric/헤드룸/gain 섹션 없음), `current_reuse_telescopic_topology`(클로저 속성 가변 상태), `nmcnr_check_dominant_pole_approximation`(임의 문턱), `ngcc_3stage_topology`(논문 역산 기본값), `_theta_evidence_for_pair`(feed 타입 3종만), `_run_combo`(지문 없음), spec 4함수(코드 dict, 죽은 `Cc`).
**A -- R2**: `run_harness.run`(3단계 미분리, θ* 미저장, 광범위 except). **D**: `derived_spec`(호출 0), `audit_current_forced.render_report`/`topology_to_markdown.render_markdown`(CLI만, 파이프라인 미배선), `report_template.html`.
**A -- DUP**: design_report union-find <-> 엔진 union-find 4곳; run() floorplan 판정 이중 계산.

**B -- 승격 후보**: probe_gm_id_monotonicity(oracle), probe_physical_consistency(엔진 함수 대상 순서 불변성으로 재작성 = C-a 강제 테스트), probe_parasitic_pm_all_circuits / probe_role_L_derivation(4회로 무동작), probe_lut_L_interpolation, probe_revalidation_scope, probe_prevention_wiring, probe_allocation_solvers(DP 엔진 배선 결정 선행).
**B -- 운영 도구**: derive_achievable_bounds, probe_metric_dashboard, (일회성 완료) apply_b19p_mirror_wiring.
**B -- 삭제 후보**: probe_mirror_common_L_wiring(**import 깨짐**), probe_vs_semantics(**전 소자 skip, 무의미**), probe_diode_vds_window, probe_mirror_ratio_error, probe_supply_current, probe_stacked_diode_options, probe_diode_gmid_readiness, probe_diode_min_vgs, probe_stack_headroom_feasibility, probe_mirror_wiring_readiness, 고아 `skipchk.result.txt`. 나머지는 결과 파일 보관형 일회성 진단.
**B -- 실행성 문제**: probe_node_voltage_audit(sys.path에 workspaces 없음). 결과 파일은 전부 git 미추적.

**C -- 난점**: 전역 `lut`/`_lib_dir_recipe` 공유 + 4단 사슬 포함 11개 순서 의존 사슬, 무거운 섹션 7곳(L5c 최중, SLSQP 없음), print-only 섹션 2개 + 조건부 흡수 1곳, stdout-diff 기준선이 pytest와 불일치.

