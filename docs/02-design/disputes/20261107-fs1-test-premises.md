---
id: 20261107-fs1-test-premises
spec_card: docs/02-design/specs/20261107-fs1.spec.md
test_id: skills/analog-gmid-design/gmid_engine/tests/search/test_start_intervals.py::test_without_s1v_start_is_none_and_layer0_uses_box_centre
test_id: skills/analog-gmid-design/gmid_engine/tests/search/test_start_intervals.py::test_sb2_second_start_intervals_computes_nothing
test_id: skills/analog-gmid-design/gmid_engine/tests/search/test_start_intervals.py::test_sb5_dependent_mirror_member_start_w_operational_path
test_id: skills/analog-gmid-design/gmid_engine/tests/search/test_off_judged.py::test_off_judged_path_passes_when_declared_metric_is_judged
test_id: skills/analog-gmid-design/gmid_engine/tests/search/test_layer0_center.py::test_halton_hit_and_run_probe_points
test_id: skills/analog-gmid-design/gmid_engine/tests/search/test_layer0_center.py::test_repair_bisection_count_and_points
test_id: skills/analog-gmid-design/gmid_engine/tests/search/test_layer0_center.py::test_no_repair_without_finite_window_ends
test_id: skills/analog-gmid-design/gmid_engine/tests/search/test_find_front.py::test_lb_stop_notes_empty_when_lb_never_runs
test_id: skills/analog-gmid-design/gmid_engine/tests/search/test_l_bin_search.py::test_n2_improving_wf_move_is_accepted
test_id: skills/analog-gmid-design/gmid_engine/tests/search/test_realize_front.py::test_realize_r6c_no_root_inside_rails_is_lost_fail_closed_and_lost_entry_has_small_m
test_id: skills/analog-gmid-design/gmid_engine/tests/metrics/test_block_param_tables.py::test_ub1_lookup_at_l_across_bins_is_nan
test_id: skills/analog-gmid-design/gmid_engine/tests/search/test_constraints_slices.py::test_constraints_inversion_floor_peak_reads_device_slice_key
test_id: skills/analog-gmid-design/gmid_engine/tests/search/test_constraints_slices.py::test_constraints_inversion_floor_differs_from_reference_key_peak_by_ln2
test_id: skills/analog-gmid-design/gmid_engine/tests/search/test_start_points.py::test_previous_run_front_points_are_not_start_candidates
test_id: skills/analog-gmid-design/gmid_engine/tests/search/test_front_entries.py::test_engine_written_runs_file_read_back_in_order
test_id: skills/analog-gmid-design/gmid_engine/tests/convergence/test_converge.py (3 case: two_stage_ota real path)
---
## 문제의 test

입력/전제가 FS-1 계약과 어긋나는 test(구현 오류가 아니라고 본 것; 개별 원인):

1. **S1v 뷰가 없는 sctx 의 출발 필드**(`test_without_s1v_start_is_none_and_layer0_uses_box_centre`, `test_off_judged_path_passes_when_declared_metric_is_judged`, convergence 실경로 `common_gate_amplifier` 계열):
   `wf_start` 는 모든 평가의 입력이다(spec 의도·interface §3.4 `initial_wf`). 그래서 `build_search_context` 는 `start_intervals` 를 **항상** 부른다(옛 `if S1v views` 조건 삭제 -- 뷰가 없으면 뷰 의존 경계만 비활성).
   (a) 첫 test 는 '뷰 없음 → `graph/start` 없음 + 층 0 상자 중심'을 단언한다 -- 이 조건이 서면 그 회로는 평가 입력이 없어 어떤 평가도 못 한다(`initial_wf` KeyError; library `common_gate_amplifier` 가 이 경우이고 base 에서는 통과하던 convergence 실경로 test 가 KeyError 로 깨진다).
   (b) 둘째 test 는 pmos 소자 + nmos 전용 toy LUT 로 sctx 만 만든다 -- `start_intervals`(기존 `headroom_bound`)가 `edges['pmos']` KeyError 를 낸다(LUT 가 모르는 kind; 출발 블록 기존 동작).
   **결정 필요(원래 취지와 다름)**: 뷰 없는 회로에도 출발 블록을 돌리는 것(내 구현)이 맞는지, 아니면 spec 에 '뷰 없는 회로는 wf 칸만 만드는 출발 경로'를 따로 정할지.
2. `test_sb2_second_start_intervals_computes_nothing`: `run_stage_b(...)` 결과 `b2.s1.snapshot` 에서 `wf_start` 를 읽는다 -- `run_stage_b` 는 `start_intervals` 를 부르지 않는다(`build_search_context` 가 부른다). spec/interface 어디에도 '단계 B 가 출발 블록을 부른다'가 없다.
3. `test_sb5_...`: `got[("MP1", "MP2")]` -- 칸 멤버 순서는 interface §3.2 '`position` 오름차순'(= `device.dc_colour`, 이름 무관)이고 이 toy 에서 MP2(colour 2) < MP1(colour 3)이라 칸 = `("MP2", "MP1")`. 이름 순을 기대하는 단언은 §3.2·S-3 과 모순.
4. 출발 불능 toy(`wf_start_undefined` / `no_member_density`): 손 회로 `circuit_window`(MA nmos (x, vdd, vdd), MB pmos (x, gnd, gnd) -- 게이트가 레일에 묶여 `fixed_vgs` 종속)는 쓰기 멤버 짝이 없어 계약(spec 범위 2·interface §3.3)대로 칸 출발 불능이다:
   `test_halton_hit_and_run_probe_points`, `test_repair_bisection_count_and_points`, `test_no_repair_without_finite_window_ends`(`layer0_start` ValueError -- 평가 입력 없음), `test_lb_stop_notes_empty_when_lb_never_runs`(진입 즉시 `start_undefined`, `l_search` 줄 없음).
   (실측 `wf_start` 칸: `MC` 키 100, `MA`·`MB` None, 기록 `wf_start_undefined` why `no_member_density` 둘.)
5. `test_n2_improving_wf_move_is_accepted`: 전제 단언(같은 θ 에서 키 100 → 200 이 면적을 분해능 한 칸 이상 줄인다)이 서지 않는다 -- 면적 `W` 는 쓰기 소자에서 `I·L/exp(θ ln IDu)`(슬라이스 무관)이고 이 회로(`circuit_c`)는 두 MOS 모두 쓰기 소자라 키가 W 를 바꾸지 않는다(실측: 두 평가의 `area_m2` 가 비트 같다).
6. `test_realize_r6c_...small_m`: 실현 재풀이가 `dc_solve` 안에서(`no_root_in_window`/Newton 비수렴) 실패하면 부분 스냅샷에는 `dc_solve` 출력(`dc_finger`)이 없다 → interface §6 '`dc_finger`가 없으면 None' 에 따라 `small_m` = None. test 는 `["M1"]` 을 요구한다.
7. `test_ub1_lookup_at_l_across_bins_is_nan`: 옛 `reachable_slices` 는 기준 폭 슬라이스의 bin 에 L 이 없으면 후보 전체를 `()` 로 비웠다. spec W5 는 `reachable_slices` → `widths` 로 바꾸고 'L 인자 없음'을 명시했다; 슬라이스마다 조회 정의 여부(`param_row` None)가 항을 가른다.
   toy 의 슬라이스 200(2 µm)은 L = 2.5 µm 가 자기 bin 안이라 값이 정의된다(실측: 슬라이스 100 은 `param_row` None, 슬라이스 200 은 값) → NaN 단언이 서지 않는다.
8. `test_constraints_slices.py` 2 case: 옛 선택 함수의 '곱 동률 → 큰 키(200)'를 전제한다(`ops["M1"].w_key == 200`) -- `search/conftest` 손 wf 는 '가장 좁은 후보 100' 이므로 키 100.
9. `test_previous_run_front_points_are_not_start_candidates`, `test_engine_written_runs_file_read_back_in_order`: 전제 `len(front) >= 1`. toy `circuit_c`·`lut_sealed`(W_MIN 5e-7, 슬라이스 1e-6)에서 탐색 front 점의 실현 정수화가 W < w_f → m = 1(W' = 2×W)이라 W' 고정 KCL 이 근을 못 찾아 점이 `realize.lost`(Newton `newton_line_search`)로 빠진다 --
   interface §1 R-6/R-8·계획 Q-FS1 의 '작은 m 한계'가 그대로 나타난 것이고 fail-closed 가 맞는 거동이다(실측 `LOST ... newton_line_search`).
10. `test_converge.py` 3 case: `search.conftest.evaluate` 래퍼가 쓰는 손 wf(가장 좁은 후보)가 층 0 이 푼 θ 의 출발 칸 키와 달라, 같은 θ 의 재평가가 제약 행 c < 0 이 된다 -- 입력 불일치. (손 wf 의 '가장 좁은 후보'는 test 가 정한 입력 선택이라고 `fs1_wf.py` 머리가 적었다.)

11. **θ 입력 키 `('L', 'M4')`**: `check_theta: θ 키가 스키마와 다르다 -- 남음 [('L', 'M4')]` -- `build_case`(A-188 정본 경로)가 단계 B 의 S1v L 동치류(`l_ties`)를 거친 스키마를 만들어 M4 의 L 이 주인 소자 L 에 묶이는데, `r2_theta` 류 손 θ 는 M4 의 L 을 따로 둔다:
    `convergence/test_realized_geometry.py`(r13a, l2 두 개), `search/test_realize_front.py`(r5, diff_pair 칸), `search/test_find_front.py`(r17 ×3, r18 ×2). FS-1 코드는 θ 스키마를 만들지 않는다(S0 입력).
12. **원인 규명 전**(분류 미완 -- 판정자가 본다): `search/test_kernel.py::test_u7_without_structure_no_block_residual_record`·`test_partial_snapshot_dc_block_failure`, `search/test_find_front.py::test_perf_blocks_rows_totals_and_index_bound`(block 행 37 대 색인 상한 26 행)·
    `test_g7_new_process_twice_bit_identical_wf_start_dc_finger_w_key`·`test_gate_entry_budget_perf_declared_and_block_index_bound`, `search/test_layer0_center.py::test_centre_point_box_centre_and_current_centre`(`1e-06 == 1.8e-06`)·`test_same_kind_single_term_cone_centre_is_box_centre`,
    `search/test_realize_front.py::test_realize_s3_6_target_net_is_unknown_in_resolve_and_its_row_is_judged`(손 oracle `hand` = −2.97 V 의 전제 단언 -- 엔진 호출 전 test 안 계산), `metrics/test_ss_evaluate.py` 의 7 failed(error 45 와 별개).

## 근거(oracle 또는 사용자 원문)

각 항목에 적은 interface/spec 조항과 실측 값. 구현이 계약대로 동작하고 test 입력이 계약을 벗어난 것으로 본다(1은 계약 자체의 빈 칸이라 결정 필요).

## 요청

항목별로 test 입력·전제를 고치거나(2, 3, 5, 7~10), 기대를 interface 와 맞춘다(4, 6), 1은 오케스트레이터가 정한다.
