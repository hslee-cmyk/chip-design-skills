# agent4 -- `stick_diagram.py` 1~8990줄 함수 전수 감사

기준: `skills/analog-gmid-design/assets/` (SD=`stick_diagram.py`, SR=`sizing_recipe.py`, RH=`workspaces/run_harness.py`). 계획서 = `docs/01-plan/features/gain-budget-gmid-sizing.plan.md` v4.43.

## 도달성 판정 방법 (근거)
- AST로 SD 최상위 158개 심볼의 내부 참조 그래프를 만들고(`scratchpad/inventory/sd_reach.py`, 결과 `sd_reach.json`) 운영 루트에서 전이 폐포를 계산했다.
- 운영 루트: SR이 SR:5864-5877에서 import한 심볼 중 **SR 코드(SR:12571 `__main__` 이전, 주석/문자열 제외)에서 실제 호출되는 것**, RH:39(`save_instance_json` RH:487, `run_full_circuit_audit_from_topology` RH:467). RH가 `optimize_full_circuit_budget`을 RH:440에서 호출하므로 SR 운영경로 = RH 운영경로. 보조: `design_report.py:32,324`, `audit_current_forced.py:43`, `topology_to_markdown.py:29`(모두 `load_topology`).
- 표기: **SR**=사이징 엔진 경로(직접/전이), **PIPE**=`run_topology_pipeline`(SD:8723) 전이, **LOAD**=`load_topology`(SD:8546) 자동채움 전이(SR을 거쳐 운영에 닿음), **RH**=run_harness(직접/전이), **WS**=workspaces 일회성 스크립트만.
- SR 실제 호출부(문자열 제외): `load_topology` SR:5056,5386,8493,12502 / `propagate_topology_forced_currents` SR:8889,8905 / `kcl_series_union` SR:8604 / `geometry_colocation_union` SR:7134 / `assign_finger_geometry` SR:9820 / `run_topology_pipeline` SR:9857,12510,12558 / `repair_matching_safety` SR:9953,12347,12426 / `split_into_stacks` SR:9882,9901,9999 / `suggest_pair_finger_adjustments` SR:11986 / `_branch_composite_pair` SR:12389 / `find_min_crossover_layout_with_branch_composite` SR:12245,12536 / `refine_differential_and_mirror_relations` SR:7127 / `audit_vertical_stack_id_vs_kcl` SR:7106 / `derive_horizontal_stack_groups` SR:7125,7132 / `build_stick_diagram` SR:12192,12226 / `audit_row_split` SR:9893,12340 / `apply_explicit_row_split` SR:9883 / `rebuild_floorplan` SR:10000 / `check_stick_diagram_coverage` SR:9980 / `require_device_roles_reviewed` SR:8501.
- **import만 하고 SR 호출 0**: `_failing_required_pairs`(SR:12272,12356은 docstring/주석), `merge_layout_groups_by_matching_pairs`(SR:7080 docstring), `check_box_shape`(SR:9890,9963 주석). `Transistor`/`PairAdjustmentSuggestion`은 SR:11980-11983, 12096에서 사용.
- self-test 열: SD:8991~ 블록에서 이름이 나오는 섹션(`Test N`). "간접"은 공개 함수 경유로만 실행됨.

## 함수 표

| 함수(줄) | 책임 | 계획 대응 | 운영호출자 | 등급 | 이관 목적지 | self-test | 근거/비고 |
|---|---|---|---|---|---|---|---|
| `Transistor`(47-77, dataclass, `__post_init__`) | connectivity+finger 필드를 담는 소자 레코드 | §8.4 레이아웃 입력 / §12 S1 엣지 후보 | SR(SR:11981,12096), 모듈 전반 | R1(레이아웃 필드 stack_id/n_fingers가 connectivity와 한 레코드) | stick_diagram 유지(S1은 별도 엣지 타입) | Test 1a 이후 전반(234회) | `load_topology` docstring SD:8570-8576: connectivity만 채워진다고 명시 |
| `_try_interdigitation_table_match`(129-160) | 문헌 interdigitation 표 경로 | §8.4 레이아웃 | SR 전이(`repair_matching_safety`→`interdigitate_layout`) | R0 | stick_diagram | 간접(Test 12.6/12.11) | 순수 |
| `interdigitate_layout`(163-206) | hub-leaf 1행 interdigitation 배치 | §8.4 | SR 전이(`repair_matching_safety` SD:7660, SR:9953) | R0 | stick_diagram | Test 12.6, 12.11, 28 | 결정론 |
| `build_mirror_symmetric_pattern`(209-229) | 좌반부로 대칭 finger 패턴 생성 | §8.4 | PIPE(`mirror_symmetric_trail`) | R0 | stick_diagram | Test 5 | |
| `MirrorSymmetryVerdict`(233-234) | 대칭 판정 결과 | 계획 외 | 없음 | D | stick_diagram(삭제 후보) | - | `check_mirror_symmetry` 전용 |
| `check_mirror_symmetry`(237-249) | finger 순서 좌우 대칭 판정 | 계획 외 | 없음(WS `current-reuse-telescopic-ota-report/stick.py:9-11`만) | D | stick_diagram 유지 또는 test util | Test 5, 5.5, 9 | 운영 호출 0 |
| `find_interleaved_symmetric_splits`(252-283) | 홀수 finger 쌍 교차 대칭 분할 해 | 계획 외 | 없음 | D | test util | Test 9, 12 | SD 밖 grep 0건 |
| `_hubleaf_sequence_node_path`(292-317) | finger 순서의 hub-leaf 경로 산출 | §8.4 | SR 전이 | R0 | stick_diagram | Test 12.7~12.12 | |
| `_common_centroid_from_pattern_table`(320-369) | 표 기반 2D common-centroid | §8.4 | SR 전이 | R0 | stick_diagram | Test 11, 12.5 | |
| `_try_pattern_table_match`(372-403) | N=2 표 경로 분기 | §8.4 | SR 전이 | R0 | stick_diagram | 간접 | |
| `common_centroid_layout`(406-537) | N소자 common-centroid 배치(표/회전/탐색) | §8.4 | SR 전이(`repair_matching_safety`) | R0 | stick_diagram | Test 11~12.11, 28 | |
| `_fix_block_parity`(540-563) | 블록 크기 홀짝 보정 | §8.4 | SR 전이 | R0 | stick_diagram | Test 12.9 | |
| `_common_centroid_nway_exact`(566-664, 중첩 `_rotate_segments`) | 회전대칭 최적 경로 | §8.4 | SR 전이 | R0 | stick_diagram | Test 12 | |
| `_proportional_round_robin`(667-685) | 비율 유지 섞기 | §8.4 | SR 전이 | R0 | stick_diagram | 간접 | |
| `_slice_into_rows`(688-700) | 순환 시퀀스 행 분할 | §8.4 | SR 전이 | R0 | stick_diagram | 간접 | |
| `_row_feasible`(703-710) | 행 오일러 실현성 | §8.4 | SR 전이 | R0 | stick_diagram | 간접 | |
| `_repair_row_parity`(713-744) | 행 배분 오일러 보정 | §8.4 | SR 전이 | R0 | stick_diagram | 간접 | |
| `_build_rows_from_shares`(747-769) | 배분을 실제 finger 행으로(hierholzer) | §8.4 | SR 전이 | R0 | stick_diagram | 간접 | |
| `_build_rows_from_shares_with_crossover`(772-811) | crossover 허용판 | §8.4 | SR 전이 | R0 | stick_diagram | 간접 | |
| `_common_centroid_residual`(814-841) | 행 안 centroid 잔차 | §8.4 | SR 전이 | R0 | stick_diagram | Test 12.10 | |
| `_count_isolated_pairs`(844-863) | 같은 행에 없는 소자쌍 수 | §8.4 | SR 전이 | R0 | stick_diagram | 간접 | |
| `_common_centroid_nway_search`(866-931) | 휴리스틱 탐색 경로 | §8.4 | SR 전이 | R0 | stick_diagram | 간접 | |
| `_sorted_setmap`(943-951) | set 맵 결정론적 렌더링 | §8.8(기준선 결정론화) 계획대로 | RH 전이(`run_full_circuit_audit`) | R0 | stick_diagram | Test 21.5 | baseline README "결정론 전제" |
| `_scan_case_collisions`(954-961) | net 이름 대소문자 충돌 | 계획 외 | RH/LOAD 전이 | R0 | topology_authoring(검증) | 간접 | |
| `find_matching_candidates`(972-1048) | mirror/diff_pair 후보 탐지(net-only 또는 idiom 경로) | §8.3 step2 계획대로(재사용 명시) / §12 S1 "개념당 정의 하나" 위반 | LOAD/RH 전이(`propose_device_roles_gap_fill` 층위1, `run_full_circuit_audit`) | DUP | circuit_state_graph(S1 matching 엣지 정의 1개) | Test 6, 21.5, 30 | mirror 정의 3개: net-only (kind,gate) SD:1024-1031 / idiom (kind,bias,rail) SD:1041 / SR `true_current_mirror_groups` (kind,gate,source)+레일게이트 제외 SR:2358-2382. diff_pair는 `_diff_pair_layer1_groups`, `find_differential_pair_candidates`와 중복 |
| `_to_analog_grammar_devs`(1062-1069) | Transistor를 analog-grammar dict로 변환 | 계획 외 | LOAD/SR 전이(11개 호출자) | R0 | topology_authoring | Test 30 | |
| `_import_analog_grammar`(1072-1085) | analog-grammar sys.path 주입+import | 계획 외 | LOAD/SR 전이 | R1(sys.path 부작용을 패키지 import로) | topology_authoring | 간접 | |
| `find_idiom_matches`(1088-1107) | analog-grammar Stage1~3 원본 Match | §8.3 step2 | 없음(호출자 `audit_theta_root_direction`, `propose_theta_kcl_gap_fill` 둘 다 운영 0) | D | topology_authoring | Test 30, 33 | |
| `find_stack_edges`(1110-1121) | `netclass.stack_edges` 래퍼 | 계획 외 | SR 전이(`geometry_colocation_union` = `resolve_stack_layout` 4순위 폴백 SR:7134) | R0 | topology_authoring | Test 30 | |
| `find_stacked_matching_candidates`(1135-1180, 중첩 `_upper_same_kind`) | 매칭쌍 위 적층쌍 재귀 상속 | 계획 외 | SR 전이(폴백 경로만) | R1(S1 stacked 관계로 흡수) | circuit_state_graph | Test 30 | |
| `trace_vdd_to_gnd_branches`(1214-1263, 중첩 entry_net/exit_net/_trace) | kind별 전류방향 고정 branch 골격(하향) | §12 S1v 성격(명시 없음) | LOAD/SR 전이 | R2 | circuit_state_graph(S1 방향 엣지/뷰) | Test 32, 35 | 전류방향 규약 3곳: SD:1216-1224, `_kcl_terminal_sign` SD:3580, SR `_metric_kcl_residual` SR:4469-4472 |
| `trace_gnd_to_vdd_branches`(1266-1311) | 상향 branch 골격 | 동상 | LOAD/SR 전이 | R2 | circuit_state_graph | Test 35 | 위와 쌍 |
| `find_differential_and_mirror_forks`(1314-1387, 중첩 4개) | 양방향 fork 분류 | 계획 외 | 없음 | D | 삭제 후보 | Test 35, 36 | `find_verified_...` docstring SD:1802-1815가 이 접근의 한계와 대체를 기술 |
| `suggest_vertical_stack_composites`(1390-1528, 중첩 `_composite`) | branch+idiom으로 vsid composite 제안 | §8.3 step2 계열 | LOAD/SR 전이 | R2 | topology_authoring | Test 33, 44 | |
| `suggest_headroom_stack_groups`(1531-1678, 중첩 3개) | composite를 헤드룸 그룹으로 제안 | 계획 외 | 없음(self-test에도 없음) | D | 삭제 후보 | 없음 | AST 호출자 0, 저장소 grep 0 |
| `find_differential_pair_candidates`(1681-1784, 중첩 `signature`) | inputs 선언 없이 diffpair 후보(shared_source) | §12 S1 | LOAD/SR 전이 | DUP | circuit_state_graph | Test 37 | diffpair/tail 정의 다중: 여기 / `find_matching_candidates` diff_pair SD:1033-1046 / SR `gain_stage_tails`(stage source net을 drain으로 갖는 tail) SR:2434-2470 / SR `input_referred_offset_pairs`(선언 기반) SR:4644-4693 |
| `_diff_pair_layer1_groups`(1787-1799) | net-only diff_pair 판정 재사용 | 계획 외 | LOAD/SR 전이 | DUP | circuit_state_graph | 간접 | docstring SD:1787-1789가 `find_matching_candidates` diff_pair와 같은 판정이라 명시 |
| `find_verified_differential_and_mirror_relations`(1802-1985, 중첩 3개) | branch 구조 일치쌍 안의 diff/mirror 관계 | §12 S1 | LOAD/SR 전이 | R2 | topology_authoring | Test 36, 38, 39, 46 | |
| `_propose_vertical_stack_ids`(1988-2225, 중첩 `assign`) | vsid 후보 이름 생성 | §8.3 | LOAD/SR 전이 | R2 | topology_authoring | Test 41 | |
| `_propose_gm_id_roles`(2228-2288) | gm_id_role(balanced/matching) 제안 | §8.3 | LOAD/SR 전이 | R2 | topology_authoring | 간접(Test 53) | tail 판정(shared_source를 drain으로, SD:2238-2242)이 SR `gain_stage_tails`와 개념 중복 |
| `_propose_L_roles`(2291-2371) | L_role(mirror/bias_replica) 제안 | §8.3 / 계획과 다름(v4.39) | LOAD/SR 전이 | R1(docstring/라벨 의미 갱신) | topology_authoring | 간접 | docstring SD:2293 "`mirror`=2.5*L_min"; SR:2780이 `_L_ROLE_MULTIPLIERS` 제거를 기록 -> 설명 stale |
| `_propose_headroom_roles`(2374-2491, 중첩 `_diode_like_mirror`) | headroom_role 제안(37/37 규칙) | §8.3 | LOAD/SR 전이 | R2 | topology_authoring | 간접(Test 45) | diode 판단이 netclass role 기반(SD:2484) -> SR `is_diode_connected`(gate==drain, SR:3294)와 다른 정의 |
| `refine_differential_and_mirror_relations`(2494-2713, 중첩 `classify`) | diffpair gate net 자동 승격 고정점 반복 | §8.3 step2 | SR 직접(SR:7127, `resolve_stack_layout` 3순위) + LOAD | R2 | topology_authoring | Test 38, 40~43, 45 | `load_topology` 호출마다 재실행(아래 `propose_device_roles_gap_fill` 비고) |
| `SymmetryDispositionsVerdict`(2717-2720) | 결과 레코드 | 계획 외 | LOAD 전이 | R0 | topology_authoring | - | |
| `check_symmetry_dispositions`(2723-2800) | 후보 대비 disposition 누락 게이트 | §8.3 step2 | LOAD 전이 | R1 | topology_authoring | Test 21.5, 54 | |
| `find_hub_merge_candidates`(2811-2834) | 같은 hub 공유 행 병합 후보 | §8.4 | RH/LOAD 전이 | R0 | stick_diagram | Test 14 | |
| `StructuralSymmetryVerdict`(2846-2851) | 결과 레코드 | 계획 외 | LOAD 전이 | R0 | topology_authoring | - | |
| `find_structural_symmetry_candidates`(2856-2966, 중첩 `expected_kind`) | seed net 대응 고정점 전파(automorphism) | §12 S1 | LOAD 전이 | R1 | circuit_state_graph(대칭 관계 유도) | 간접(Test 53) | docstring SD:2858-2860: `propagate_topology_forced_currents`와 같은 전파 스타일 |
| `MultiLeafHubParityVerdict`(2970-2973) | 결과 레코드 | 계획 외 | 없음 | D | test util | - | |
| `check_multi_leaf_hub_parity`(2976-3008) | hub-leaf 오일러 가능성 공식 스크리닝 | 계획 외 | 없음 | D | test util | Test 14 | |
| `propagate_topology_forced_currents`(3019-3070) | stack_id+미러비 전류 고정점 전파(A엔진) | §11.1 표 / §12 S1(동일전류 엣지) | SR 직접(SR:8889,8905 `_build_theta_evaluator`) | R2 | circuit_state_graph(엣지) + 엔진(값) | Test 27 | 전류 동일 관계를 레이아웃 필드 `stack_id`에서 읽음 SD:3044-3048(본문 시작부) |
| `DiodeStackMember`(3074-3077) | 결과 레코드 | 계획 외 | 없음 | D | - | - | |
| `DiodeStack`(3082-3084) | 결과 레코드 | 계획 외 | 없음 | D | - | - | |
| `find_diode_stacks`(3087-3115) | 스택 내 gate가 (자기/이웃) drain인 소자 | §11.1 표 소비자 기재 / §12.3 "엔진 호출부 0" | 없음(SR:1595,1669는 주석/docstring) | D | circuit_state_graph(diode 정의 1개로 통합) | Test 27 | **DUP**: 계획 §12.3 표 5행 "diode 집합 16/1/20". 정의 4곳: 여기(이웃-diode, stack_id 필요 SD:3100-3112) / SR `is_diode_connected` SR:3294 / SR `_diode_set_cached` SR:5452 / SD 층위1 `t.gate == t.drain` SD:4279, SD:3872 |
| `split_into_stacks`(3122-3144) | stack_id 또는 (kind,finger_w)로 행 후보 분할 | §8.4 | SR 직접(SR:9882,9901,9999) + PIPE | R0 | stick_diagram | Test 3, 26.5 | |
| `shares_diffusion_node`(3150-3164) | S/D 공유(게이트 제외) 판정 | §8.4 | PIPE/SR 전이 | R0 | stick_diagram | 간접 | |
| `kcl_series_union`(3167-3223, 중첩 find/union) | 2단자 내부넷+matching_pairs union-find KCL 그룹 | §11.1 / §12 S1 | SR 직접(SR:8604) | DUP | circuit_state_graph | Test 29, 47 | 같은 edge를 `_kcl_and_matching_edges`(SD:3298, docstring "단일 정의로 분리")가 재구성하지만 이 함수 본문 SD:3188-3212는 그것을 쓰지 않고 독자 구현 |
| `geometry_colocation_union`(3226-3295, 중첩 find/union) | matching base+적층 상속 geometry 그룹 | §8.4 | SR 직접(SR:7134, 4순위 레거시 폴백) | R1 | stick_diagram | Test 5.6, 12.13, 29, 48 | |
| `_kcl_and_matching_edges`(3298-3319) | KCL/matching edge 목록(원인 보존) | §12 S1 | SR 전이(`audit_vertical_stack_id_vs_kcl`) + LOAD | DUP | circuit_state_graph | 간접 | 상대: `kcl_series_union` |
| `audit_vertical_stack_id_vs_kcl`(3322-3415, 중첩 find/union) | 선언 vsid vs KCL 그룹 대조표 | §12 S1 status(선언/유도 대조) | SR 직접(SR:7106, 불일치 시 ValueError SR:7100-7110) | R1 | topology_authoring(→S1 검증) | Test 47, 52 | |
| `propose_vertical_stack_id_gap_fill`(3418-3495, 중첩 find/union) | union 그룹 내 vsid 상속 제안 | §8.3 | LOAD(SD:8624) | R2 | topology_authoring | Test 52 | |
| `audit_theta_root_direction`(3498-3569) | theta A feed의 캐스코드 방향 역전 탐지 | 계획 외 | 없음 | D | topology_authoring(배선 여부 승인 필요) | Test 60 | |
| `_kcl_terminal_sign`(3580-3589) | PMOS/NMOS 단자 KCL 부호 | 계획 외 | 없음 | DUP | circuit_state_graph | 간접(Test 61) | 운영 0(D). SR `_metric_kcl_residual` SR:4469-4472이 같은 규약 독자 구현 |
| `propose_theta_kcl_gap_fill`(3592-3937, 중첩 `_mark`,`_run_rules_1_to_3`) | theta 전류 구조 제안(고정점 규칙) | §8.3 성격 | 없음 | D | topology_authoring(배선 승인 필요) | Test 61, 62 | 346줄, 운영 호출 0 |
| `apply_theta_kcl_gap_fill`(3940-3992) | 위 제안을 topology.json에 기록 | §8.3 step6 성격 | 없음 | D | topology_authoring | Test 62 | 파일 쓰기 도구 |
| `propose_device_roles_gap_fill`(3995-4700, 중첩 `_propose_pair`,`_points_at`) | matching_pairs/device_roles 3단 소스 제안 | §8.3 step2~3 | LOAD(SD:8649) -> SR/RH/design_report | R2 | topology_authoring | Test 29, 52~56 | 706줄. `load_topology`마다 analog-grammar 전체 재실행. SR 캐시(SR:5386,5414)가 있으나 `run_topology_pipeline` SD:8781, `_build_theta_evaluator` SR:8493, fixup SR:12502는 캐시 없이 재호출(C10 재계산) |
| `apply_device_roles_gap_fill`(4703-4765) | 제안을 topology.json에 영구 기록 | §8.3 step6 | 없음(수동 저작 도구; SR:13954는 SR self-test 주석) | D | topology_authoring | Test 55~58 | |
| `find_authoritative_sizing_devices`(4768-4808) | role 없이도 안전한 소자 집합 | 계획 외 | LOAD/SR 전이 | R1(정의 이중화 해소) | topology_authoring | Test 57 | docstring SD:4770-4775: SR `_AUTHORITATIVE_*`와 "반드시 같은 정의"여야 한다 -> 두 곳 정의 |
| `find_unreviewed_device_roles`(4811-4846) | 자동채움 중 review 필요 필드 | §12 C-a(`proposed` 차단) 선행 | SR 전이 | R1 | circuit_state_graph(status) | Test 57 | |
| `find_unreviewed_matching_pairs`(4849-4879) | review 필요 매칭쌍 | §12 C-a 선행 | SR 전이 | R1 | circuit_state_graph(status) | Test 58 | |
| `require_device_roles_reviewed`(4882-4931) | 미검토 자동채움이면 사이징 거부 | §12 C-a 선행 | SR 직접(SR:8501) | R1 | circuit_state_graph(status 게이트) | Test 57, 58 | |
| `_verified_euler_fix`(4934-4973) | 그룹 오일러 검사+finger 조정 재검증 | §8.4 | SR 전이(`merge_layout_groups_by_matching_pairs`) | R0 | stick_diagram | 간접 | |
| `audit_vertical_stack_id_euler_feasibility`(4976-5067) | 선언 vsid 그룹의 오일러 실현성 | §8.4 | 없음 | D | stick_diagram(배선 여부 승인 필요) | Test 49 | |
| `merge_layout_groups_by_matching_pairs`(5070-5177, 중첩 find/euler_feasible) | 매칭쌍으로 레이아웃 그룹 재병합 | §8.4 | SR 전이(`derive_horizontal_stack_groups`); SR import는 호출 0 | R0 | stick_diagram | Test 48 | SR:5873 import 정리 대상 |
| `derive_horizontal_stack_groups`(5180-5231) | vsid 그룹을 kind 분할+매칭 재병합 | §8.4 | SR 직접(SR:7125,7132) | R0 | stick_diagram | Test 51 | |
| `find_euler_repair_options`(5234-5298) | unresolved_row 복구 선택지 진단 | §8.4 | 없음 | D | stick_diagram(배선 승인 필요) | Test 50 | 운영 0 |
| `FingerWidthIssue`(5306-5311) / `FingerWidthVerdict`(5315-5317) | 결과 레코드 | §8.4 | PIPE | R0 | stick_diagram | - | |
| `check_finger_width_compatibility`(5320-5345) | W가 finger_w 정수배인지 | §8.4 | PIPE | R0 | stick_diagram | Test 26.55 | |
| `StackGraph`(5353-5358) | stack multigraph | §11.1 "레이아웃 전용" 계획대로 | PIPE/SR 전이 | R0 | stick_diagram | - | 계획 §11.1 표 마지막 행 |
| `build_graph`(5361-5417) | Transistor 리스트를 finger multigraph로 | §8.4 | PIPE/SR 전이(12개 호출자) | R0 | stick_diagram | Test 5.6, 12, 12.13, 14, 49 | |
| `_degrees`(5420-5421) / `_is_connected_ignoring_isolated`(5424-5436) | 차수/연결성 | §8.4 | PIPE | R0 | stick_diagram | - | |
| `EulerVerdict`(5440-5445) / `check_euler_condition`(5448-5470) | 오일러 3조건 판정 | §8.4 step4 계획대로 | PIPE/SR 전이 | R0 | stick_diagram | Test 5.6, 12.13, 14 | |
| `hierholzer`(5477-5505) | 오일러 경로 순회 | §8.4 | PIPE/SR 전이 | R0 | stick_diagram | Test 12, 12.13 | |
| `_mirror_node_map_from_pairs`(5517-5556, 중첩 `_add`) | 매칭쌍에서 net 거울 대응 | §8.4 | SR 전이 | R0 | stick_diagram | Test 12.13 | |
| `_pair_odd_nodes_by_mirror`(5559-5600) | 홀수차수 노드 거울 우선 짝짓기 | §8.4 | SR 전이 | R0 | stick_diagram | Test 12.13 | |
| `_build_crossover_segments`(5603-5649) | 가상 edge로 segment 분할 | §8.4 | SR 전이 | R0 | stick_diagram | Test 12.13 | |
| `_count_matching_pair_splits`(5652-5699, 중첩 `_sensitivity_of`) | segment 간 매칭쌍 분리 수 | §8.4 | SR 전이 | R0 | stick_diagram | Test 12.13 | |
| `_is_perfect_crossover_score`(5702-5706) | 점수 0 판정 | §8.4 | SR 전이 | R0 | stick_diagram | Test 12.13 | |
| `_enumerate_perfect_matchings`(5713-5723) | 완전짝짓기 열거 | §8.4 | SR 전이 | R0 | stick_diagram | 간접 | (2m-1)!! 폭발 상한 확인 필요 |
| `_select_crossover_pairing`(5726-5771) | 최적 crossover 짝 선택 | §8.4 | SR 전이 | R0 | stick_diagram | Test 12.13 | |
| `find_min_crossover_layout`(5774-5868) | 최소 crossover hub-leaf 배치 | §8.4 | SR 전이 | R0 | stick_diagram | Test 12.9, 12.12, 12.13, 28 | |
| `AdjustmentSuggestion`(5876-5880) / `suggest_finger_adjustments`(5883-5923) | 단일 소자 finger ±1 제안 | §8.4 | PIPE(`build_stick_diagram`) | R0 | stick_diagram | 간접 | |
| `PairAdjustmentSuggestion`(5927-5931) / `suggest_pair_finger_adjustments`(5934-6012) | 쌍 finger 조정 제안 | §8.4 step5 | SR 직접(SR:11986) | R0 | stick_diagram | Test 5.6, 49 | |
| `UnitCellCandidate`(6025-6029) / `search_unit_cell_sizing`(6032-6051) | nominal W 근방 unit cell 후보 | §8.4 | SR 전이(`assign_finger_geometry`) | R0 | stick_diagram | Test 7 | |
| `_quantize_to_grid`(6058-6069) | 길이 grid 스냅 | 계획 외 | SR 전이 | DUP | stick_diagram(공용 유틸로 추출 가능) | 간접 | SR `quantize_L` SR:799-815와 동일 공식; docstring SD:6059-6063이 순환 import 회피용 의도적 사본이라 명시 |
| `BoxLayoutCandidate`(6073-6078) / `search_stack_finger_w`(6081-6167) | stack별 finger_w 탐색(Case A) | §8.4 | SR 전이 | R0 | stick_diagram | Test 10, 15, 29 | |
| `assign_finger_geometry`(6170-6265, 중첩 `_w_of`,`_l_of`) | 사이징 W를 finger/width로 배분 | §8.4 step3 계획대로 | SR 직접(SR:9820) | R0 | stick_diagram | Test 29 | |
| `apply_explicit_row_split`(6268-6310) | 명시 row_split 균등 분할 | §8.4 | SR 직접(SR:9883) | R0 | stick_diagram | 없음(직접 테스트 없음) | self-test 등장 0회 |
| `SharedFingerWCandidate`(6325-6329) / `search_shared_finger_w`(6332-6386) | 공통 finger_w 탐색(Case B) | §8.4 | 없음(WS `stick.py:9`만) | D | stick_diagram 유지 또는 삭제 | Test 15 | |
| `pitch`(6411-6420) | finger 1개 폭 근사 | §8.4 | PIPE/RH | R0 | stick_diagram | Test 13 | |
| `RowGeometry`(6424-6429) / `compute_row_geometry`(6432-6468) | 행 폭/높이 계산 | §8.4 | PIPE/RH | R0 | stick_diagram | 간접 | |
| `BoxShapeVerdict`(6472-6483) / `check_box_shape`(6486-6579) | box-shape 게이트 | §8.4 | PIPE/RH 전이; SR import 호출 0 | R0 | stick_diagram | Test 13 | SR:5875 import 정리 대상 |
| `StickResult`(6587-6595) | stack 결과 | §8.4 | PIPE | R0 | stick_diagram | - | |
| `WalkVerdict`(6599-6604) / `check_walk_sequence`(6607-6695) | 제안 순서 연속성 독립 검산 | §8.4 | PIPE | R0 | stick_diagram | Test 5.5, 5.6, 24 | |
| `mirror_symmetric_trail`(6701-6791) | 매칭 인지 대칭 trail 선택 | §8.4 | PIPE | R0 | stick_diagram | Test 5.5, 5.6 | |
| `build_stick_diagram`(6794-6832) | stack별 오일러 결과 생성 진입점 | §8.4 | SR 직접(SR:12192,12226) + PIPE | R0 | stick_diagram | Test 1a~4 등 | |
| `render_stick_diagram`(6835-6855) | PDF 형식 텍스트 출력 | 계획 외 | 없음 | D | test fixture/유틸 | Test 1a~4 | |
| `folded_cascode_example`(6862-6900) | Maloberti FC 넷리스트 | 계획 외 | 없음 | fixture | tests/fixtures | Test 4, 5.5, 6, 22, 26, 27... (19회) | Test 26 SD:10703-10704가 library json과 대조 -> 이중 정본 |
| `two_stage_ota_example`(6903-6933) | Maloberti 2-stage 넷리스트 | 계획 외 | 없음 | fixture | tests/fixtures | Test 8, 22, 26 | |
| `AuditCheck`(6947-6950) / `AuditResult`(6954-6970, 메서드 `add`) | 감사 결과 레코드 | §8.5 산출물 입력 | SR/RH/PIPE | R0 | stick_diagram(직렬화는 instance_report_builder) | - | `design_report.py:32`가 `_audit_result_json` 사용 |
| `run_full_circuit_audit`(6973-7062) | devices dict 기반 전체회로 4단계 감사 | 계획 외 | RH 전이(`run_full_circuit_audit_from_topology`) | R1(입력 `devices` 튜플 dict가 topology와 별도 정본 -> S1에서 읽게) | stick_diagram 또는 instance_report_builder | Test 16, 21.5 | docstring SD:6992-6993이 정본 1벌을 요구 |
| `CoverageVerdict`(7079-7081) / `check_stick_diagram_coverage`(7084-7114) | 사이징 소자 전부 행에 배치됐는지 | §8.4 | SR 직접(SR:9980) + PIPE | R0 | stick_diagram | Test 25 | |
| `select_layout_tool`(7132-7160) | 민감도/공유노드로 도구 선택 | §8.4 | PIPE/SR 전이 | R0 | stick_diagram | Test 28 | |
| `audit_row_split`(7163-7368, 중첩 `_sensitivity_of`,`_centroid`) | 행 분할 후 euler/box/matching 고정 순서 감사 | §8.4 | SR 직접(SR:9893,12340) + PIPE | R0 | stick_diagram | Test 22, 23, 26, 26.6, 28 | |
| `_failing_required_pairs`(7378-7393) | AuditCheck name 문자열에서 실패 쌍 파싱 | §8.4 | SR 전이(`repair_matching_safety`); SR import 호출 0 | R1(구조화 필드 부재로 정규식 파싱) | stick_diagram | 간접 | SR:12356-12359이 같은 파싱 패턴 복제 언급 |
| `_layout_result_to_rows`(7396-7428) | 도구 반환값을 rows로 | §8.4 | SR 전이 | R0 | stick_diagram | 간접 | |
| `_kcl_branch_map`(7431-7442) | kcl_series_union을 소자별 branch로 펼침 | §8.4 | SR 전이 | R1(S1 KCL 관계 사용으로) | stick_diagram | 간접 | `kcl_series_union` DUP 사슬 |
| `_two_device_branch_outer`(7445-7459) | 2소자 branch 바깥 단자 | §8.4 | SR 전이 | R0 | stick_diagram | 간접 | |
| `_branch_composite_pair`(7462-7549) | 거울 branch를 합성 소자쌍으로 | §8.4 | SR 직접(SR:12389) | R0 | stick_diagram | Test 28 | |
| `_composite_collapse_for_crossover`(7552-7626, 중첩 `_sensitivity_of`) | crossover 전 branch 합성 | §8.4 | SR 전이 | R0 | stick_diagram | Test 28 | `_sensitivity_of` 중첩이 `audit_row_split`, `_count_matching_pair_splits`에도 각각 있음(본문 동일성 미확인) |
| `find_min_crossover_layout_with_branch_composite`(7629-7657) | branch 인지형 최소 crossover 래퍼 | §8.4 | SR 직접(SR:12245,12536) | R0 | stick_diagram | Test 28 | |
| `repair_matching_safety`(7660-7839, 중첩 `_sensitivity_of_pair`) | 매칭 실패 행 재배치 반복 | §8.4 | SR 직접(SR:9953,12347,12426) | R0 | stick_diagram | Test 28, 29 | 같은 역할 이름의 중첩 헬퍼 4곳 중 하나(본문 동일성은 미확인) |
| `FloorplanBlock`(7857-7863) / `PlacedBlock`(7867-7872) / `FloorplanResult`(7876-7884) | floorplan 레코드 | §8.4 | PIPE | R0 | stick_diagram | Test 18 | |
| `_block_center`(7887-7888) / `_total_wire_cost`(7891-7918) | 배선 비용 | §8.4 | PIPE | R0 | stick_diagram | 간접 | |
| `skyline_pack`(7921-8003, 중첩 3개) | bottom-left skyline packing | §8.4 | PIPE | R0 | stick_diagram | 간접 | |
| `_sweep_widths`(8006-8026) / `skyline_pack_best_width`(8029-8053) / `pack_to_height`(8056-8091) | 폭 스윕/정사각 폭/높이 맞춤 | §8.4 | PIPE | R0 | stick_diagram | Test 18 | |
| `find_diffusion_safe_split_points`(8094-8115) / `evaluate_row_split_candidates`(8118-8166) | 행 분할 후보 평가 | §8.4 | PIPE | R0 | stick_diagram | Test 18 | |
| `pack_floorplan`(8169-8278) | spine+mirror pair packing | §8.4 | PIPE | R0 | stick_diagram | Test 17, 19 | |
| `block_from_rows`(8281-8293) | rows를 블록으로 | §8.4 | PIPE | R0 | stick_diagram | Test 17 | |
| `rebuild_floorplan`(8296-8374) | rows만으로 floorplan 재조립 | §8.4 | SR 직접(SR:10000) + PIPE | R0 | stick_diagram | 없음(직접 테스트 없음) | |
| `_pack_by_subkind`(8377-8413) / `pack_group_as_unit`(8416-8484) / `pack_floorplan_grouped`(8487-8537) | 기능 그룹 단위 packing | §8.4 | PIPE | R0 | stick_diagram | Test 19~21 | |
| `load_topology`(8546-8720, 중첩 `_read_one`) | JSON+linked 파일 병합 로드 **+ vsid/device_roles/matching 자동채움** | §8.3 step1 계획대로(로더) / 자동채움은 §12 C-a와 충돌(`proposed`를 meta에 섞음) | SR 직접(SR:5056,5386,8493,12502), RH/design_report/audit_current_forced/topology_to_markdown, probe 23개 | R2(파싱 R0 + 구조 유도 분리) | 파싱: circuit_state_graph S0/S1 로더 / 자동채움: topology_authoring | Test 26 외 34회 | SD:8624, 8649-8652가 매 호출 구조 유도; SR:5416이 "매번 다시 돌린다"고 기록 |
| `run_topology_pipeline`(8723-8865) | load->override->finger 검사->stack->euler->box->audit->floorplan->coverage | §8.4 계획대로(패턴 증명) | SR 직접(SR:9857,12510,12558) | R1(`load_topology` 재호출 SD:8781 -> 로드 결과 주입) | stick_diagram | Test 26, 26.5, 26.55, 26.6 | |
| `run_full_circuit_audit_from_topology`(8868-8921) | topology.json만으로 full audit 자동 구성 | 계획 외(§8.5 인접) | RH 직접(RH:467), design_report.py:324 | R0 | instance_report_builder | Test 31 | |
| `_box_shape_json`(8924-8936) | BoxShapeVerdict 직렬화 | §8.5 | RH 전이 | R0 | instance_report_builder | 간접 | |
| `_audit_result_json`(8939-8945) | AuditResult 직렬화 | §8.5 | RH 전이, design_report.py:130 | R0 | instance_report_builder | 간접 | |
| `save_instance_json`(8948-8984) | instance.json 작성 | §8.5 step1 계획대로 | RH 직접(RH:487) | R0 | instance_report_builder | Test 26 | |

## self-test 블록(SD:8991~12935) 구조 조사

### 실측 (2026-09-14, 이 감사에서 1회 실행)
- 실행: `scratchpad/inventory/run_timed.py`가 `python stick_diagram.py` stdout을 줄마다 타임스탬프. 종료코드 0, **총 30.06s**, 섹션 77개.
- `tests/baseline/stick_diagram.selftest.baseline.log`(1257줄)와 **바이트 동일**(`sd_section_times.txt` 마지막 줄 `identical_to_baseline=True`). 저장소 git 상태 변화 없음(쓰기는 전부 tempfile).
- 무거운 섹션: **Test 53 = 23.41s**(SD:12402 `from sizing_recipe import optimize_full_circuit_budget` 후 SD:12418, 12440, 12451 세 곳에서 사이징 호출), Test 12.10 = 3.21s(n_rows != N 전수 스윕), 나머지 전부 0.6s 미만.
- `tests/baseline/` 내용: `README.md`, `sizing_recipe.selftest.baseline.log`(361줄), `stick_diagram.selftest.baseline.log`(1257줄). README 재생성 절차: `cd skills/analog-gmid-design/assets; python stick_diagram.py > /tmp/sd.log 2>&1; diff tests/baseline/stick_diagram.selftest.baseline.log /tmp/sd.log` -- 0줄이어야 회귀 없음. 결정론 전제는 `_sorted_setmap()`(SD:943), PYTHONHASHSEED 1~5 확인(README "결정론 전제").

### 섹션표
판정: A=assert 기반(실패 시 중단), P=print PASS/FAIL 문자열만(실패해도 계속), V=print만(판정 없음, 눈으로 확인). 외부: L=`library/*.topology.json`(fc=folded_cascode, crt=current_reuse_telescopic_ota, tso=two_stage_ota, nm=nmcnr_amplifier), G=analog-grammar skill, S=`sizing_recipe` import, T=tempfile 쓰기.

| 섹션 | 줄 | 검증 대상(주) | 판정 | 외부 | 앞 섹션 변수 의존 | 시간 |
|---|---|---|---|---|---|---|
| (prelude) | 8991-8995 | stdout utf-8 재설정 | - | - | - | - |
| Test 1a/1b | 8996-9017 | build_graph/check_euler_condition/build_stick_diagram/render | V | - | - | <0.1s |
| Test 2 | 9018-9032 | suggest_finger_adjustments(홀수차수 4) | V | - | - | <0.1s |
| Test 3 | 9033-9045 | split_into_stacks 극성 분리 | V | - | - | <0.1s |
| Test 4 | 9046-9059 | folded_cascode_example stick | V | - | - | <0.1s |
| Test 5 | 9060-9070 | build_mirror_symmetric_pattern/check_mirror_symmetry | V | - | - | <0.1s |
| Test 5.5 | 9071-9110 | mirror_symmetric_trail/check_walk_sequence | V | - | - | <0.1s |
| Test 5.6 | 9111-9159 | suggest_pair_finger_adjustments+trail | V | - | `top` 정의(이후 12.7/17/21/22/26.6/27/45에서 같은 이름) | <0.1s |
| Test 6 | 9160-9175 | find_matching_candidates | V | - | - | <0.1s |
| Test 7 | 9176-9182 | search_unit_cell_sizing | V | - | - | <0.1s |
| Test 8 | 9183-9189 | two_stage_ota_example stick | V(SD:9187 "예상과 다름" 문자열만) | - | - | <0.1s |
| Test 9 | 9190-9201 | find_interleaved_symmetric_splits | V | - | - | <0.1s |
| Test 10 | 9202-9214 | search_stack_finger_w | V | - | - | <0.1s |
| Test 11 | 9215-9251 | 표 기반 common-centroid | P | - | - | <0.1s |
| Test 12 | 9252-9272 | common_centroid_layout 회전 | A(1) | - | - | <0.1s |
| Test 12.5~12.9b | 9273-9654 | common_centroid/interdigitate 경로·스윕 | A(2~9)+P | - | `row0/row1`(12.6)이 17/22/24/28에서 재사용 | 각 <0.1s |
| Test 12.10 | 9655-9744 | n_rows != N 전수 스윕 | A(5) | - | - | **3.21s** |
| Test 12.11 | 9745-9778 | INTERDIGITATION_PATTERNS 표 전체 | A(2) | - | - | <0.1s |
| Test 12.12 | 9779-9839 | find_min_crossover_layout | A(7) | - | - | <0.1s |
| Test 12.13 | 9840-9994 | crossover matching_pairs 확장/가중치 | A(22) | L(crt) | - | 0.09s |
| Test 13 | 9995-10053 | check_box_shape | P | - | - | <0.1s |
| Test 14 | 10054-10105 | find_hub_merge_candidates/check_multi_leaf_hub_parity | P | - | `candidates` 정의 SD:10084 | <0.1s |
| Test 15 | 10106-10133 | search_shared_finger_w | V | - | - | <0.1s |
| Test 16 | 10134-10167 | run_full_circuit_audit | **P -- 기준선에 "FAIL(예상과 다름)" 박제** | - | `expected` SD:10143, `dispositions` SD:10155 정의 | <0.1s |
| Test 17 | 10168-10230 | pack_floorplan(51소자 블록) | P | - | `spine` SD:10182, `mirror_pairs` SD:10194 정의 | 0.31s |
| Test 18 | 10231-10266 | find_diffusion_safe_split_points/evaluate_row_split | P | - | `spine`(17) | <0.1s |
| Test 19 | 10267-10298 | pack_floorplan_grouped | P | - | `spine`,`mirror_pairs`(17); `spine_groups` SD:10271 정의 | 0.16s |
| Test 20 | 10299-10329 | net_weights | P | - | `mirror_pairs`(17),`spine_groups`(19); `net_weights` SD:10304 | 0.32s |
| Test 21 | 10330-10361 | sub_kind packing | P | - | 17/19/20 변수 | 0.53s |
| Test 21.5 | 10362-10455 | check_symmetry_dispositions | A(6)+P | L(crt), T | - | 0.13s |
| Test 22 | 10456-10551 | audit_row_split 회귀 | P | - | `row0/row1`(12.6) | <0.1s |
| Test 23 | 10552-10631 | branch_symmetric kind | P | - | - | <0.1s |
| Test 24 | 10632-10652 | check_walk_sequence | V | - | `dist_top_row0`(23), `row0`(12.6) | <0.1s |
| Test 25 | 10653-10684 | check_stick_diagram_coverage | P | - | - | <0.1s |
| Test 26 | 10685-10762 | load_topology/run_topology_pipeline/save_instance_json | A(2)+P | L(fc,tso), T | `_lib_dir` SD:10694, `_fc_original/_fc_loaded/_fc_meta/_fc_overrides/_fc_result` SD:10703-10716 정의 | 0.10s |
| Test 26.5/26.55/26.6 | 10763-10844 | run_topology_pipeline 오류/게이트/cell_groups | A+raise 기대 | L(fc) | `_lib_dir`,`_fc_*`(26) | <0.1s |
| Test 27 | 10845-10906 | propagate_topology_forced_currents/find_diode_stacks | A(8) | L(crt) | `_fc_original`(26) | 0.11s |
| Test 28 | 10907-11108 | select_layout_tool/repair_matching_safety/branch composite | A(27) | L(crt,fc), S | `_fc_loaded/_fc_meta`(26); `_fc_pairs_meta` SD:10945 정의 | 0.10s |
| Test 29 | 11109-11200 | kcl/geometry union, assign_finger_geometry | A(12) | L(fc) | `_fc_loaded`(26), `_fc_pairs_meta`(28) | <0.1s |
| Test 30 | 11201-11302 | analog-grammar Tier1(find_idiom_matches 등) | A(16) | G | - | <0.1s |
| Test 31 | 11303-11387 | run_full_circuit_audit_from_topology | A(8)+raise 기대 | L(crt,fc), T(**NamedTemporaryFile delete=False** SD:11370) | - | 0.18s |
| Test 32 | 11388-11432 | trace_vdd_to_gnd_branches | A(6) | - | - | <0.1s |
| Test 33 | 11433-11464 | suggest_vertical_stack_composites | A(8) | G | - | <0.1s |
| Test 35 | 11465-11514 | trace_gnd_to_vdd/forks | A(6) | G | `_t35_fixture` SD:11470 정의 | <0.1s |
| Test 36~46 | 11515-11882 | find_verified.../find_differential_pair_candidates/refine.../_propose_vertical_stack_ids | A(2~11) | G | `_t35_fixture`(35)를 36,37,39~46이 재사용 | 각 <0.1s |
| Test 47 | 11883-11935 | audit_vertical_stack_id_vs_kcl | A(6) | L(crt) | - | 0.07s |
| Test 48 | 11936-12020 | merge_layout_groups_by_matching_pairs | A(9) | L(fc), G | - | <0.1s |
| Test 49 | 12021-12113 | audit_vertical_stack_id_euler_feasibility | A(12) | L(crt) | `_t49_os/_t49_lib/_t49_trs/_t49_meta/_t49_forced/_t49_device_roles` SD:12030-12035 정의 | 0.07s |
| Test 50 | 12114-12162 | find_euler_repair_options | A(5) | - | `_t49_*`(49) | <0.1s |
| Test 51 | 12163-12219 | derive_horizontal_stack_groups | A(7) | - | `_t49_*`(49) | <0.1s |
| Test 52 | 12220-12325 | propose_vertical_stack_id_gap_fill | A(12) | L(tso), S | `_t49_lib`(49) | <0.1s |
| Test 53 | 12326-12466 | propose_device_roles_gap_fill + 채움 후 사이징 불변 | A(11) | L(crt,tso), S, T | `_t49_lib`(49) | **23.41s** |
| Test 54 | 12467-12497 | 층위1 폴백 | A(3) | L(fc) | `_t49_lib`(49) | <0.1s |
| Test 55 | 12498-12546 | apply_device_roles_gap_fill 왕복 | A(5) | L(fc), T | `_t49_lib`,`_t49_os`(49); `_t55_tempfile` 정의 | 0.06s |
| Test 56 | 12547-12605 | 충돌 필드 비덮어쓰기 | A(6) | T | `_t55_tempfile`(55) SD:12584 | <0.1s |
| Test 57 | 12606-12676 | find_unreviewed_device_roles/require_... | A(8) | L(crt), T | `_t49_lib`, `_t55_tempfile` SD:12645 | 0.34s |
| Test 58 | 12677-12735 | find_unreviewed_matching_pairs | A(5) | L(fc), S, T(**mkdtemp** SD:12692) | `_t49_lib`(49) | <0.1s |
| Test 60 | 12736-12803 | audit_theta_root_direction | A(6) | L(4회로 전부), G | `_t49_lib` | 0.15s |
| Test 61 | 12804-12887 | propose_theta_kcl_gap_fill | A(14) | L(fc,nm), G | `_t49_lib`; `_t61c_result` SD:12833 정의 | <0.1s |
| Test 62 | 12888-12935 | apply_theta_kcl_gap_fill | A(5) | L(nm), T | `_t49_lib`, `_t61c_result`(61) | 0.12s |

(Test 34, 59는 번호 결번.) 변수 의존은 정규식 교차 스캔 후 정의 줄을 grep으로 확인한 것만 기재 -- `row`,`name`,`stack_id` 같은 루프/키워드 인자 동명은 제외.

### 이관 난점
1. **경로 기준이 `__file__`**: `_lib_dir`(SD:10694), `_t49_lib`(SD:12030)가 `os.path.dirname(__file__)/library`. `tests/test_stick_diagram.py`로 옮기면 `tests/library`를 가리켜 깨진다 -- 바이트 동일 기준선을 유지하려면 경로만 부모 디렉터리로 바꿔야 하고 출력 문자열에 경로가 찍히는지 추가 확인 필요.
2. **`from stick_diagram import *`로는 부족**(계획 §8.8 문구): self-test가 쓰는 `_` 접두 심볼 최소 16개(`_hubleaf_sequence_node_path`, `_common_centroid_from_pattern_table`, `_fix_block_parity`, `_common_centroid_nway_exact`, `_common_centroid_residual`, `_sorted_setmap`, `_to_analog_grammar_devs`, `_propose_vertical_stack_ids`, `_mirror_node_map_from_pairs`, `_pair_odd_nodes_by_mirror`, `_build_crossover_segments`, `_count_matching_pair_splits`, `_is_perfect_crossover_score`, `_branch_composite_pair`, `_composite_collapse_for_crossover`, `_pack_by_subkind`)는 `import *`에 안 딸려온다 -> 명시 import 필요.
3. **순서/전역 의존 사슬**: Test 17→18~21, Test 16→(dispositions/expected), Test 26→26.5~29, Test 28→29, Test 35→36~46, Test 49→50~62, Test 55→56·57, Test 61→62. pytest 함수 단위로 쪼개면 fixture로 끌어올려야 하고, 한 파일 스크립트로 옮기면 순서를 그대로 유지해야 한다.
4. **판정 없는 섹션**: Test 1a~10, 15, 24는 V(판정 없음), Test 11, 13, 14, 16~23, 25는 P(문자열만). 기준선 diff만이 판정 수단이다. 특히 **Test 16이 SD:10164-10165에서 `FAIL(예상과 다름 — dispositions 키를 재확인할 것)`을 출력하고 이것이 기준선 로그 453줄에 그대로 들어 있다**(452줄: UNDISPOSED `('diff_pair','pmos','tail') ['M4','M5']`). 즉 "바이트 동일 = 통과" 기준은 이 알려지지 않은 실패를 정상으로 고정한다.
5. **역방향 의존**: Test 28, 52, 53, 58이 `sizing_recipe`를 import하고, Test 53은 실제 사이징을 여러 번(SD:12418, 12440, 12451) 돌려 전체 시간의 78%(23.4/30.1s)를 쓴다. SR:12446-12449가 "SD는 SR을 모르고 단방향 import"라고 적었지만 SD self-test는 SR에 의존한다 -- test 파일 분리 시 소요시간/의존 경계 결정 필요.
6. **analog-grammar 의존**: Test 30, 33, 35~46, 48, 60, 61은 `_import_analog_grammar`(SD:1072)의 sys.path 주입에 기대 -- 실행 위치 변화에 민감.
7. **임시 파일 잔재 가능성**: SD:11370 `NamedTemporaryFile(delete=False)`, SD:12692 `mkdtemp()` -- 정리 코드 여부는 확인하지 않았다(미확인).
8. **계획 문구 드리프트**: §8.8/§8.2는 `stick_diagram.py:8980~12923`이라 하지만 실제 `if __name__` 은 SD:8991, 끝은 12935.

## 요약

### 등급별 개수(최상위 심볼 158개 기준, 표는 dataclass 묶음 행 포함)
| 등급 | 개수 |
|---|---|
| R0 그대로 재사용 | 101 |
| R1 재사용+국소 수정 | 16 |
| R2 재설계 대상 | 12 |
| DUP 중복 | 7 (+ D로 분류했지만 중복인 `find_diode_stacks`) |
| D 미사용(운영) | 20 |
| test fixture | 2 |

### R0 (새로 만들면 중복)
레이아웃 계층 거의 전부: common-centroid/interdigitation 20개(SD:129-931), `_sorted_setmap`, `_scan_case_collisions`, `_to_analog_grammar_devs`, `find_stack_edges`, `find_hub_merge_candidates`, 결과 레코드 3종, `split_into_stacks`, `shares_diffusion_node`, `_verified_euler_fix`, `merge_layout_groups_by_matching_pairs`, `derive_horizontal_stack_groups`, finger-width 검사, `StackGraph`/`build_graph`/`check_euler_condition`/`hierholzer`, crossover 8개(SD:5517-5868), finger 조정/unit cell/`search_stack_finger_w`/`assign_finger_geometry`/`apply_explicit_row_split`, box-shape/row geometry, `check_walk_sequence`/`mirror_symmetric_trail`/`build_stick_diagram`, `AuditCheck`/`AuditResult`, `check_stick_diagram_coverage`, `select_layout_tool`/`audit_row_split`, branch composite 4개, `repair_matching_safety`, floorplan packing 13개(SD:7857-8537), `run_full_circuit_audit_from_topology`, `_box_shape_json`/`_audit_result_json`/`save_instance_json`.

### sizing_recipe.py와의 교차 DUP 쌍
| 개념 | SD 쪽 | SR 쪽 | 차이(근거) |
|---|---|---|---|
| diode | `find_diode_stacks` SD:3087(이웃-diode 포함, stack_id 필요); 층위1 `t.gate == t.drain` SD:4279, SD:3872; `_propose_headroom_roles` netclass role SD:2484 | `is_diode_connected` SR:3294, `_diode_set_cached` SR:5452 | 계획 §12.3: 16/1/20 |
| 전류미러 그룹 | `find_matching_candidates` net-only (kind,gate) SD:1024-1031 / idiom (kind,bias,rail) SD:1041 | `true_current_mirror_groups` (kind,gate,source), 레일 게이트 제외 SR:2358-2382 | 키가 서로 다르다 |
| diffpair / tail | `find_differential_pair_candidates` SD:1681, `_diff_pair_layer1_groups` SD:1787, `find_matching_candidates` diff_pair SD:1033, `_propose_gm_id_roles`의 balanced tail SD:2228 | `gain_stage_tails` SR:2434, `input_referred_offset_pairs` SR:4644 | SD는 connectivity 유도, SR은 선언(headroom_role/ports/matching_sensitivity) 기반 |
| KCL 동일전류 그룹 | `kcl_series_union` SD:3167, `_kcl_and_matching_edges` SD:3298, `propagate_topology_forced_currents` SD:3019(stack_id 기반) | `_metric_kcl_residual` SR:4430 노드 KCL, `_hr_vfind` SR:7420 | SD 내부에서도 edge 정의 2벌 |
| 전류 방향/KCL 부호 | `_kcl_terminal_sign` SD:3580, `trace_*_branches` SD:1214/1266 | `_metric_kcl_residual` SR:4469-4472 | 같은 규약 독자 구현 |
| 레일 넷 집합 | `_RAIL_NETS = {"vdd","gnd","vss"}` SD:3147 | `_DEFAULT_RAIL_HI/LO`(대소문자 변형 포함) SR:3882-3883, `_metric_kcl_residual` 기본값 SR:4456 | **대소문자 처리 불일치** |
| grid 스냅 | `_quantize_to_grid` SD:6058 | `quantize_L` SR:799 | 의도적 사본(SD:6059-6063) |
| authoritative 소자 | `find_authoritative_sizing_devices` SD:4768 | SR `_AUTHORITATIVE_*`(docstring SD:4770-4775이 동일 정의 요구) | 두 곳 유지 |

### D 목록(운영 도달 0)
`MirrorSymmetryVerdict`, `check_mirror_symmetry`(WS만), `find_interleaved_symmetric_splits`, `find_idiom_matches`, `find_differential_and_mirror_forks`, `suggest_headroom_stack_groups`(self-test에도 없음), `MultiLeafHubParityVerdict`, `check_multi_leaf_hub_parity`, `DiodeStackMember`, `DiodeStack`, `find_diode_stacks`, `audit_theta_root_direction`, `_kcl_terminal_sign`(DUP 표기), `propose_theta_kcl_gap_fill`, `apply_theta_kcl_gap_fill`, `apply_device_roles_gap_fill`(수동 저작 도구), `audit_vertical_stack_id_euler_feasibility`, `find_euler_repair_options`, `SharedFingerWCandidate`/`search_shared_finger_w`(WS만), `render_stick_diagram`. -- 절대원칙상 배선하거나 삭제할지 **사용자 승인 필요**.

### 추가 발견
- `load_topology`(SD:8546)가 파싱과 함께 `propose_vertical_stack_id_gap_fill`(SD:8624)·`propose_device_roles_gap_fill`(SD:8649, 706줄, analog-grammar 전체)을 매번 실행한다. SR은 SR:5386/5414에서 캐시하지만 `run_topology_pipeline` SD:8781, `_build_theta_evaluator` SR:8493, fixup SR:12502는 캐시 없이 다시 부른다(§12 C-d, C10 재계산).
- SR import 목록(SR:5864-5877) 중 `_failing_required_pairs`, `merge_layout_groups_by_matching_pairs`, `check_box_shape`는 SR에서 호출 0(주석/docstring만).
- `_propose_L_roles` docstring(SD:2293)의 "`mirror`=2.5*L_min"은 v4.39의 `_L_ROLE_MULTIPLIERS` 제거(SR:2780) 이후 stale.
