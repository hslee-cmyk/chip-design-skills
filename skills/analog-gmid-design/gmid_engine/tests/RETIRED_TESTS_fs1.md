# FS-1 삭제·대체 test 대응표 (card 20261107-fs1, interface §8)

삭제 사유 = 대상(선택 함수 `finger_slice`/`reachable_slices`, Rʳ·`slice_cycle`·`slice_rounds`, 탐색 `dc_finger` (m, w_s) 실현 입력, `polish_l_cells`)이 소멸. 대체 id = interface §1~§7.

| 삭제 test | 사유 | 대체 |
|---|---|---|
| `tests/lut/test_finger_slice.py` 전체 (`reachable_slices`·`finger_slice` 손 stub 묶음) | 선택 함수 삭제, 후보 = `widths(lut, kind)` (L 무관) | `tests/lut/test_slice_of_finger.py` C-2·C-3, `tests/lut/test_widths.py`(기존), `tests/lut/test_lut_set.py` C-1·C-1′, `tests/sizing/test_realize_fingers.py` R·F·P |
| `tests/sizing/test_block_dc.py::test_dc_solve_mirror_hand_picks_finger_slice` (동률 큰 키·손 선택) | 소자별 선택 삭제, 슬라이스 = 칸 키 | 같은 파일 D-1 `test_dc_solve_search_eval_keeps_fractional_fingers_all_keys_100`, D-2 `test_dc_solve_cell_members_share_slice_and_w_is_closed_form` |
| 같은 파일 `CountFingerSlice` (관찰 지점 `block_dc.finger_slice`) | 대상 소멸 | `_realize_spy` (관찰 지점 `block_dc.realize_fingers`, D-6) |
| 같은 파일 `test_dc_solve_layout_reseal_writes_input_finger_rows_without_selection` | `RealizedFinger`·`FingerGeom.w_f_m` 삭제 | D-7 `test_dc_solve_layout_reseal_uses_request_rows_and_base_fingers` |
| 같은 파일 `test_dc_solve_layout_reseal_row_missing_is_classified` (`realized_finger_missing`) | 기준 스냅샷 행 없음 안전망(`REASON_REALIZED_FINGER_MISSING` 유지)을 만드는 입력이 새 `RealizeInput` 꼴로는 hand 구성이 없다 | **대체 없음 -- 보고(LA-1 재점검 입력)**: 안전망 사유 도달 test 는 code 작성 뒤 필요하면 새 card |
| 같은 파일 `test_dc_solve_dependent_all_candidates_missing` (D-4 옛: 모든 후보 gap -> `slice_missing` why `no_candidate`) | 후보 열거 삭제, 칸 키 한 슬라이스만 조회 | D-8 `test_dc_solve_cell_member_lookup_failure_is_not_avoided` |
| 같은 파일 Rʳ 묶음: `circuit_r_dep`·`r_dep_setup`·`Scripted`·`rdep`·`test_dc_solve_rdep_converges`·`test_dc_solve_rdep_cycle_rejected` (`slice_cycle`, `slice_rounds`) | Rʳ·`slice_cycle`·`slice_rounds` 삭제 | D-3 `test_dc_solve_no_slice_rounds_and_one_node_solve_per_eval` |
| `tests/search/test_realize_front.py::test_realize_r3_zero_residual_keeps_input_finger_without_reselecting` ('재선택 없음' r3) | 선택 함수 삭제 | D-5·D-6 (`test_dc_solve_realized_eval_uses_hand_oracle_m`) |
| 같은 파일 `test_realize_r10_json_finger_residual_and_selection_residual`·`..._is_the_tampered_search_value` (finger_residual = 탐색 residual) | `finger_residual` 출처 탐색 -> 실현 (원래 취지와 다름 3) | O-1·O-4 `test_realize_o1_json_finger_residual_is_the_realized_value_and_no_slice_rounds` |
| `tests/structure/test_wb1_source.py::test_wb1_reachable_slices_calls_have_three_args` | `reachable_slices` 삭제 | `tests/structure/test_fs1_source.py` G-3·G-4 |

서명 맞춤(삭제 아님, 기대값 변경 없음 또는 interface id 로 정당화): `lut/test_slice_of_finger.py`(L 인자 삭제, C-2·C-3), `lut/test_lut_memo_slices.py`(`finger_slice` 호출 -> `widths` 키 열거 `slice_lookup`, 단언 그대로),
`sizing/test_s2_values.py`·`test_dc_solve_values.py`(`FingerGeom(m, residual)`, `RealizeInput`, `WfCell`·`WfInput`, `SccLog.slice_rounds` 칸 삭제), `sizing/test_block_dc.py` 나머지(`size_and_seal(ctx, th, wf)`),
`search/test_eval_key.py`(`wf_fp`), `search/test_kernel.py`(`evaluate` 래퍼 + E-5 `wf_keys`), `search/test_l_bin_search.py`(`polish_cells`, `StartPoint(..., wf, ...)`), `search/test_find_front.py`(perf 키 23 -> 25),
`search/test_s0_fields.py`·`integration/test_s0_layer_9circuits.py`(필드 `wf_start`), `structure/test_wb1_source.py`(`finger_slice` 정의 0, `REWRITE_NEW` 에서 `lut/finger_slice.py` 제외).

## M-1 (b) 값 toy 전제 확인 (결정 A-182)

전제 P0(입력 소자 nmos), L 앵커 범위 ⊇ 8 µm: 아래 두 자료에서 확인 -- (b) 는 **유지**(빼지 않음).
- 입력 소자 kind: `assets/library/<회로>.topology.json` 입력 포트 게이트에 닿는 MOS -- two_stage_ota·two_stage_ota_sf·folded_cascode·sf_pushpull_output_opamp = nmos; cnr_ota = nmos(`x2.M1`·`x22.M1`); 나머지 회로(current_reuse_telescopic_ota 혼합, erfc_ota·ngcc_3stage_ff·nmcnr_amplifier·rfc_ota = pmos, r2r_opamp 혼합, pushpull_follower_buffer 혼합, common_gate_amplifier 입력 MOS 없음)는 (b) 대상 아님.
- L 앵커: LUT mismatch npz `L` 축 = 1.5e-7 ... 4e-6, 8e-6, 2e-5 (18개) -- 8 µm 앵커 있음. (회로별 탐색 L 상한이 8 µm 에 닿는지는 test 가 실행 A 의 spy 앵커 목록으로 단언한다.)

## S-B6 쓰지 않음 (결정 A-186, interface §3.4 S-B6 '전제 단언 -- 서지 않으면 멈추고 보고')

전제 = 정합 묶음 멤버 C 가 쓰기 멤버와 gate 만 공유하고 source 가 다른 mirror 묶음. 시도한 toy (모두 `search/u13_hand.toy_case` 로 단계 A·B 를 돌린 뒤 `graph.matching_groups`·`device.dc_coord` 를 읽음):
- 거울 부하(MN1 nmos 입력 + MP1 다이오드 pmos + MP2 pmos 거울 + MN2 싱크): mirror (MP1, MP2) derived, MP2 dependent·partner MP1 -- 같은 gate·source·bulk 라 **S-B5 에 사용**, gate 만 공유가 아님.
- 소스 퇴화 거울(MP2 소스에 저항): `matching_groups` 비어 있음 -- 묶음이 서지 않음.
- 캐스코드 거울(MP1·MP2 + MP3·MP4): mirror (MP1, MP2) 와 branch_symmetric (MP3, MP4) -- branch_symmetric 은 gate 만 공유(source 다름)하지만 둘 다 writer 라 '종속 멤버 + 짝 없음' 이 아님.
- 3출력/와이드스윙 꼴: mirror 는 source 가 같은 쌍으로만 섬.
결론: 정합 묶음이 gate 만 공유하는 종속 멤버로 서지 않는다 -> S-B6 test 없음 (skip 아님).
덮이는 범위: 짝 없음 -> `no_member_density` -> 칸 None -> 기록은 순수 함수 수준 `test_k2_gate_only_shared_has_no_partner`(K-2)·`test_w2_no_partner_is_no_member_density`(W-2)·`test_s7_s8_member_why_makes_cell_undefined`(S-7)·`test_s6_...`(S-6), `initial_wf` None 은 S-B4, 평가 0 진입은 O-2 가 덮는다. 운영 경로(출발 블록이 실제로 그 기록을 남기는 것)는 덮이지 않는다.

## A-186 추가 삭제 (이름·사유 -- 기준을 약하게 바꾼 단언은 0: 아래는 입력 경로 소멸로 대상이 사라진 test 의 삭제이며 남긴 test 의 단언은 그대로다)

`tests/search/test_realize_front.py` (옛 입력 = 탐색 스냅샷 `dc_finger` (m, w_s) 를 `with_fingers` 로 바꿔치기해 실현 입력으로 쓰는 구성 -- 실현 m 은 이제 실현 DC 블록이 `realize_fingers` 로 정한다, 같은 입력을 만들 수 없음):
`test_realize_r2_input_difference_shift_matches_closed_form`(R-2 입력 차 이동), `test_realize_r5_search_nondominated_point_dominated_by_realized_values`(R-5), `test_realize_r6_unresolved_servo_pivot_keeps_input_value`(R-6),
`test_realize_r6_input_fixed_branch_resolves_kcl_and_reseals`(R-6, 2 case)·`test_realize_r6c_no_root_inside_rails_is_lost_fail_closed`·`test_realize_r15_input_fixed_realized_point_satisfies_output_kcl`(R-6c·R-15 입력 고정 갈래),
`test_realize_s3_6_*`(S3-6 2개), `test_realize_r16_power_is_rail_current_of_realized_channel_current`(R-16, 2 case), `test_realize_r8_missing_search_finger_is_a_reason_not_keyerror`(R-8 -- 실현이 탐색 dc_finger 행을 읽지 않음),
`test_realize_r12_finger_not_a_slice_is_slice_missing`(R-12 -- `slice_of_finger` C-3 이 덮음), `test_realize_r10_json_finger_residual_is_the_tampered_search_value`(O-1 로 대체).
남긴 것: R-1(식 갱신), R-4, R-7, R-9, 새 O-1·O-3. **덮이지 않게 된 것(LA-1 재점검 입력)**: 실현 점의 입력 고정 갈래 KCL 재풀이·재봉인 값(R-6/R-15/R-16)과 입력 차 이동(R-2)의 닫힌 식 대조 -- 새 실현 경로에서 같은 구성을 만들 입력(실현 m 이 손 값으로 정해지는 키 선택)을 interface 가 정하지 않았다.
`tests/convergence/test_realized_geometry.py`: `test_layout_resolve_r13a_servo_branch_follows_the_vgs2_fixed_point`, `test_layout_resolve_r13b_input_fixed_branch_follows_the_output_fixed_point`, `test_layout_resolve_l2_waiting_device_row_is_the_request_and_junction_follows_two_places`,
`test_layout_resolve_l2_device_without_input_finger_row_is_realized_finger_missing` (+ helper `_fingers`·`_assert_input_rows`·`CountFingerSlice`·`_l2_start`·`_geometry`) -- 레이아웃 입력으로 탐색 `dc_finger` (m, w_f_m) 를 놓고 `finger_slice` 호출 0 을 세는 구성. 대체: D-7(요청 행 -> `slice_of_finger`, 없는 소자 = 기준 스냅샷). 덮이지 않는 것: 레이아웃 뒤 KCL 재풀이 값(R-13)의 닫힌 식 대조 -- LA-1 재점검 입력.

## A-188 (build_case 출발 단계 정본 경로) 삭제
`build_case`·`bins_case` 가 단계 A -> 단계 B 를 거친다. 통과하지 못한 toy = `circuit_diode` (종단 diode 부하): 단계 A 가 `unsupported_rule_branch|cs_output_low_impedance|transfer:0|out` 로 정지(exit 2). 이 회로를 쓰는 `tests/search/test_cell_floor.py` 6 함수(7 항목)를 삭제:
`test_one_var_only_selects_diode_writer`, `test_start_coordinate_caps_floor`, `test_cell_floor_cache_is_read`, `test_real_lut_v2_multi_anchor_cells`, `test_solve_eps_respects_one_var_floor`(2 case), `test_layer0_maxmin_respects_one_var_floor`. 삭제 수 7 항목 / `build_case`·`bins_case` 호출 test 약 189 곳 -- 절반 미만. 기준을 약하게 바꾼 단언 0 (남은 test 단언은 그대로).
**덮이지 않게 된 것(LA-1 재점검 입력)**: 1변수 writer(diode) 정점 하한 `one_var_only`·start 캡·캐시 읽기 단언 -- 단계 A 를 통과하는 diode 부하 회로가 생기면 되살린다.
통과 확인 회로(`lut_sealed`): circuit_c(3 LUT 변형)·circuit_p·circuit_z·circuit_n·R-2 회로(`bins_case`). 미측정: circuit_zl·circuit_cmfb_diff·tied_cs2 및 그 밖 호출 -- 전체 search 디렉터리 실행은 base 에서 코드 없이 끝까지 못 돌려(실행 중단) 호출별 통과율을 세지 못했다.

## A-190 (freeze 판정 Major 5 처리)
- **되살림 (M-5, 새 실현 경로로 다시 씀)**: R-6 피벗 유지, R-6 입력 고정 갈래(2 case), R-6c(fail-closed, + O-3 `small_m` 를 같은 시나리오에서 -- 동작 대체 stub 없음), R-15, R-16(2 case), S3-6 -- `search/test_realize_front.py` 아래 절. 입력 = 칸 키 200 에서 W < w_f 가 되게 θ 전류 스케일 (m = 1 은 손 oracle), 기대 = 옛 test 와 같은 `wb1_hand` 독립 해(r 은 스냅샷 실현 W / 탐색 W 에서 읽음). 옛 단언(허용오차·사유·핵심 식)은 약화하지 않았다.
- **A-191 결정 반영 (최종)**:
  - **R-2 (차동쌍 입력 차 이동 닫힌 식): 삭제 유지** -- 해법 S(DEC-108)에서 diff_pair 멤버는 한 칸에서 같은 w_f 로 정수화된다. 같은 전류·L·VGS 면 θ W 도 같아 m 이 같으므로 'M1 만 W' 가 달라지는 비대칭 실현'은 구조상 일어나지 않는다 (검사 대상 소멸, 기준 약화 아님). **대체 test**: `search/test_realize_front.py::test_realize_diff_pair_cell_members_get_same_m_and_realization_makes_no_input_shift` (칸 두 멤버의 실현 m 이 손 oracle 로 같고 실현이 입력 차 이동을 만들지 않는다).
  - **R-5: 다시 씀** -- `test_realize_r5_search_nondominated_point_dominated_by_realized_values` (3 슬라이스 LUT, 두 점 θ 를 test 가 골라 같은 칸 키에서 반올림이 달라지게 함, m 은 `hand_oracle`).
  - **R-13a·R-13b·L-2(2): 다시 씀** -- `convergence/test_realized_geometry.py` 의 같은 이름 4개. 입력 = 기준 실현 점(`realize_front`) + 레이아웃 요청 행/배치 (interface §4.4, D-7 꼴); 레이아웃 요청은 소자 하나만 W' 를 바꿀 수 있어 R-13a 의 비대칭 이동이 다시 만들어진다. L-2 두 번째 test 는 기준(실현) 스냅샷에서 dc_finger 행을 지운 입력으로 `realized_finger_missing` 안전망을 본다.
  - 이로써 A-186 의 M-5 대상 중 삭제로 남는 것은 R-2 하나(위 사유)다.
- **삭제 (M-2d, S1 수준 전제 legacy)**: `search/test_search_context.py::test_noise_decl_without_s1v`, `test_u7_context_inputs_default` (정본 경로 build_case 는 S1v 가 항상 있다: 실측 `input_cells=(('M1',),)`, structure 있음).
- **삭제 (M-2a)**: `search/test_find_front.py` `test_cm_unconstrained_warning_reaches_run_notes_i22`, `test_cm_constrained_circuit_has_no_warning_note`, `test_eval_result_warnings_equal_ss_evaluate_i22` (+ `circuit_cmfb_diff`·`_cm_case`). 단계 A 정지 `unsupported_rule_branch|loop_record_only|...|global_feedback_or_cross_coupled` (실측) -- 루프가 test 대상이라 toy 를 고칠 수 없다. 덮이지 않는 것: `cm_loop_unconstrained` 경고 표면(I-22) -- LA-1 재점검 입력.
- **고침 (M-2b)**: `test_theta_resistance/capacitance_without_bounds_rejected_before_kernel` -- 정본 경로에서 같은 사유(`theta_*_bounds_undeclared`)를 단계 B 가 먼저 거부함을 단언(거부는 유지, 자리만 바뀜).
- **미해결 (M-2e)**: `test_find_front.py::test_passive_theta_circuit_front_measured`·`test_unmeasured_points_never_in_final_front`, `test_search_context.py::test_eval_results_identical_search_memo_vs_caller_memo` -- 정본 경로 전환 뒤 front 가 빈 tuple. 실측 증상: 두 test 의 notes 에 `gain_ss_db ... passive_value_undeclared`(30점), `C-78 supply_current_dc_needs_counted_rails_declaration`(power_dc_w 축) 이 나온다. 원인(단계 B 를 거친 S0 스냅샷과 옛 S1 수준 스냅샷의 차이)은 엔진을 열지 않고는 특정할 수 없어 고치지 못했다 -- 오케스트레이터에 넘김.
  - **A-191 재측정**: `C-78 supply_current_dc_needs_counted_rails_declaration` 는 거부 사유가 아니라 notes 의 `not_computed` 정보 줄이다 (circuit_z 실행: front 0, pending 0, unmeasured 0, 평가 33회). 따라서 선언 추가로 고쳐지는 원인이 아니다. 같은 실행의 `DEC-79 passive_area_undeclared: [Cz, Rz]` 는 toy PDK 선언에 MIM 면적 밀도가 없기 때문이고, `write_decls_mim` 으로 `Cz` 는 선언되지만 `Rz` 는 남으며 front 는 그대로 0 이었다. 즉 수동소자 선언 부족만으로도 설명되지 않는다 -- 원인 미특정, 세 test 는 파일에 남아 있고 코드 뒤 결과로 판단.
  - **A-193 MR-1 최종 처리** (판정자 실측 원인 = test 입력 결함: 정본 경로 층 0 이 W = toy MINW 0.5 µm 로 가 실현 m = 1, circuit_c out 손 근 −1.19 V 레일 밖 -> 점을 잃음; MINW 3 µm 는 물리적으로 맞지 않는 선언이라 쓰지 않음):
    - `test_passive_theta_circuit_front_measured` -> **회로를 저항 부하 P + 수동소자 θ(Rz, Cz) 로 교체** (`circuit_pz`·`theta_pz`), base 에서 front 1 (측정). 전제 단언 `assert_realized_roots_inside_rails` (front 점마다 실현 잔차 r 로 `source_load_kcl_at_vdd` > 0 = 손 근이 레일 안) 추가.
    - `test_eval_results_identical_search_memo_vs_caller_memo` -> **회로를 저항 부하 P 로 교체** (`theta_p`, 예산 40), base 에서 통과 (측정).
    - `test_unmeasured_points_never_in_final_front` -> **삭제 (RETIRED)**: 저항 부하 P 에 미선언 CL 을 단 toy 를 (θ·rbounds 4 변형) 시도했으나 유일한 sealed front 점이 실현 item 3 실패로 사라져 unmeasured front 가 비었다(측정: sealed 38~40 / failed 1, realize.lost 1). 실현 조건이 맞는 toy 를 찾지 못했다. 덮이지 않는 것: '미측정(gain_ss_db 의 CL 미선언) 점은 최종 front 에 들지 않고 unmeasured_front 로 간다' 의 find_front 수준 단언 -- LA-1 재점검 입력. (skip·기대 약화 없음.)

## A-196·A-197 묶음 B (search·metrics·convergence, 판정 `evidence/2026-11-08/fs1_disputes_verdict.md`)
- **S2 귀결 -- 대상 소멸 (RETIRED)**: `start_intervals` 가 S1v 뷰 유무와 무관하게 늘 돈다(interface §3.4, 원래 취지와 다름: 층 0 출발점이 상자 중심에서 출발 사다리로 바뀜).
  - `search/test_start_intervals.py::test_without_s1v_start_is_none_and_layer0_uses_box_centre` -> **RETIRED**. 대체: `test_without_s1v_view_wf_start_still_exists_and_initial_wf_is_defined` (S1v 뷰 없는 회로에도 `wf_start` 가 있고 `initial_wf` != None, 층 0 출발 = 상자 중심 또는 출발 사다리).
  - `search/test_layer0_center.py::test_centre_point_box_centre_and_current_centre`(L 칸 = ln 중점 1.8 µm, ln_idu = 상자 중점, 전류 = 두 I_c 의 ln 중점)·`test_same_kind_single_term_cone_centre_is_box_centre`(θ 전류 = √(I_off·I_max)) -> **RETIRED**. 사다리 칸이 없는 `centre_start(sctx[, None])` 도 이제 상자 중심이 아니라 출발 구간 값(실측: L 1e-6, ln_idu −23.32)을 낸다 -- 상자 중심 기하는 어떤 호출로도 관찰되지 않는다. 대체: `test_first_point_is_ladder_rung_one_inputs_without_s1v_view`(첫 평가 점 = 사다리 첫 칸의 ln_idu·L·L 칸, y = 0.5, 원뿔 행 c > 0), `test_same_kind_single_term_cone_has_zero_centre_u_and_ladder_first_point`(u = 0). **덮이지 않는 것(LA-1 재점검 입력)**: 층 0 상자 중심의 L = ln 중점 칸·전류 기하 중심 닫힌 식(계약 3.21 1·2).
- **기대 변경(interface id 로 정당화)**:
  - `search/test_realize_front.py::test_realize_r6c_..._small_m`: `small_m` 기대 `["M1"]` -> `None` (interface §6 O-3: dc_solve 안 실패의 부분 스냅샷에는 `dc_finger` 가 없으면 None).
  - `metrics/test_block_param_tables.py::test_ub1_lookup_at_l_across_bins_is_nan` -> `test_ub1_lookup_at_l_across_bins_follows_each_slices_own_bin_map` (포락 후보 = `widths`, 슬라이스 100 None·슬라이스 200 정의 -> 포락 = 슬라이스 200 의 `param_row` 값, spec W5·interface §2).
  - `metrics/test_block_param_tables_slices.py::test_slice_block_value_e4_empty_bin_map_leaves_amax_undetermined` -> `..._empty_bin_map_no_longer_gates_candidates` (빈 bin 지도가 후보를 막지 못한다: 블록 인증, A_max = db(follower_amax(0.1, 4·s)) 손 값 -- 옛 기대의 원인 `reachable_slices` 소멸, spec W5·interface §2).
- **입력 정정 (기대값 불변)**: front 가 비던 test 3개의 회로를 저항 부하 P 로 교체(A-193 MR-1 선례, 전제 단언 `assert_realized_roots_inside_rails`) -- `test_start_points::test_previous_run_front_points_are_not_start_candidates`, `test_front_entries::test_engine_written_runs_file_read_back_in_order`, `search.conftest.fs1_determinism_probe`(G-7). 토이 LUT 후보 키 변경 대신 이 선례를 따랐다.
- **미해결 (red 유지, 오케스트레이터 보고)**: `test_l_bin_search::test_n2_improving_wf_move_is_accepted`(전제 불성립 -- 정합 칸 안 키는 면적을 바꾸지 못함, 위 본문 주석), `convergence/test_converge*.py` 실경로 two_stage_ota 7건(손 봉인 점이 gain/gbw 행 c < 0 -- θ 재조정 필요).
- **보류 (계획 v6.39.5 개정 -- 짝 없는 비쓰기 단일 멤버 칸 = 기준 폭 슬라이스 출발)**: `search/test_layer0_center.py` 3건(halton/repair/no_repair), `search/test_find_front.py::test_lb_stop_notes_empty_when_lb_never_runs`, `search/test_kernel.py::test_partial_snapshot_dc_block_failure`, `metrics/test_ss_evaluate.py::test_it2d_f_icm_margin_same_value_in_report_and_front_row_servo`. 손대지 않았다.
