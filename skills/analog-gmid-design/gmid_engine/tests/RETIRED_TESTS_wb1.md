# 폐기·이동 test -- card 20261104-wb1 (판정 기록 근거 `retired_tests`, 계약별 `covered_by`)

규칙: 정의가 바뀌어 전제가 깨진 test 는 고치지 않고 지운다(원칙 33, O-155 B1). 근거 = 계획 N6.32, design 40 §3.7-A·§2.4.8, interface `20261104-wb1.interface.md` §3·§8.
**물리 단언은 그대로 옮긴다**: 이동은 아래 '이동' 표, 지운 것은 '폐기' 표(사유와 `covered_by` 포함).

## 이동 (단언 불변, 파일·이름·서명만 바뀜)

| 옛 | 새 | 바뀐 것 |
|---|---|---|
| `tests/sizing/test_block_columns.py` 전부(폐기 4개 제외) | `tests/sizing/test_block_dc.py` 뒤쪽 '노드 풀이' 절 | `dc_columns(...)` -> `dc_solve(...)`(인자 순서 같음), `LutAccess(memo, W_KEYS)` -> `LutAccess(memo)`, `dc_widths(snap, lut)` 후속 호출 -> 같은 스냅샷의 `dc_op` 열 읽기(한 블록) |
| `tests/sizing/test_block_widths.py` 전부 | `tests/sizing/test_block_dc.py` 중간 '소자 동작점' 절 | writer 이름 `dc_widths` -> `dc_solve`, `DeviceOp.w_key` = 그 소자 손가락 슬라이스(toy LUT 는 슬라이스 하나라 100), 블록 계수 시험은 `dc_solve` 직접 호출 |
| 모든 `dc_columns`·`dc_widths` writer 이름 | `dc_solve` | 권한표 writer(`tamper(..., "dc_solve", ...)`), 블록 객체 이름 |
| `device.dc_drop_current` 단언 | `device.dc_current` 저항·가지치기 행 | 필드 삭제(D40 §3.7-A 10·11) |
| `pre_layout_lut_access(memo)` | `LutAccess(memo)` | 인자 이름 |
| `acc.w_keys[kind]` 로 기준 슬라이스를 읽던 oracle | `lut.cap_map[kind].w_key` | 같은 값(기준 폭 키) |
| `ParamTables(memo, w_keys, grids)` | `ParamTables(memo, grids, side=, z_side=)` | 슬라이스 하나짜리 합성 LUT 는 네 표가 같아 `upper/max` |
| `EVAL12` 12 블록 | `EVAL11` 11 블록 | 평가 커널 4 -> 3 블록(dc_solve 하나) |

## 폐기

| test (옛 파일) | 사유 | covered_by |
|---|---|---|
| `tests/sizing/test_pre_layout_widths.py` 의 `test_toy_w_ref_gives_w_key_100`, `test_w_ref_picks_matching_slice_among_two`, `test_missing_slice_value_error` | `pre_layout_lut_access`·`LutAccess.w_keys`·`w_key_of` 삭제(kind 당 슬라이스 하나라는 계약 폐기, 설계 40 §3.7-A 7, 계획 DEC-105 (2)) | `tests/sizing/test_dc_solve_values.py::test_dc_solve_value_types_fields_and_frozen`(`LutAccess` 칸 = memo 뿐), `tests/lut/test_finger_slice.py`·`test_slice_of_finger.py`(소자별 슬라이스 선택) |
| 같은 파일 `test_fp_follows_lut_and_w_keys`, `test_usable_for_kernel_context` | 지문에 `w_keys` 가 들던 계약 소멸. `__canonical__ = memo.lut.fp` | `tests/sizing/test_kernel_context.py::test_lut_access_fingerprint_independent_of_memo_state`(memo 상태 무관 지문), `tests/sizing/test_dc_solve_values.py`(LUT 지문이 다르면 `LutAccess` 지문이 다르다) |
| `tests/sizing/test_kernel_context.py::test_w_keys_missing_kind`, `test_w_key_not_in_slice_map` | `build_kernel_context` 의 `w_keys` 검사 삭제(§3.7-A 7) | 슬라이스 부재는 소자별 `slice_missing`(`tests/lut/test_finger_slice.py`, `tests/sizing/test_block_dc.py::test_dc_solve_dependent_all_candidates_missing`) |
| `tests/sizing/test__helpers_lut.py::test_w_keys_choose_slice` | 위와 같음 | 위와 같음 |
| `tests/sizing/test_block_columns.py::test_it2b_k1_unmeasurable_root_is_unmeasured_with_order_window` | E-13: 커널이 `Window.input_status`·`tol_v` 를 더 쓰지 않는다(`INPUT_STATUS_UNSETTLED`·`_interior_solution`·상태 쓰기 삭제, 창은 순서 창 하나). 창 내용(레일 범위, 채널 소자 없음)은 T-W 가 덮음 | `tests/sizing/test_block_dc.py::test_window_w4_gate_only_root_is_rail_range_without_constraints`, `test_window_w1..w3` |
| `test_it2b_l12a_k_max_exhausted_root_window_is_unsettled_and_y_range_kept` | E-13: 되풀이 소진 `unsettled` 상태·`block_columns.k_max` 삭제(상태 쓰기·되풀이 없음) | T-W1~4 (순서 창은 닫힌 정의, 되풀이 없음) |
| `test_it2b_l12a_tol_undefined_root_window_is_unsettled_and_y_range_kept` | 같은 사유(`tol` 미정 `unsettled` 상태) | 같음 |
| `test_it2b_l12a_window_tol_v_is_the_tolerance_of_the_last_measured_solution` | `Window.tol_v` 를 커널이 쓰지 않는다(§3.11-1 'VDSAT·tol 읽기 0') | 같음 |
| `tests/sizing/test_size_and_seal.py::test_current_perturbation_skips_columns` 의 `dc_columns` 계산 0 단언만 | 노드 풀이와 W 가 한 블록(`dc_solve`)이라 '노드 풀이만 건너뛰기'가 없다. test 는 `test_current_perturbation_recomputes_dc_solve_not_lengths` 로 남김 | 같은 test |
| `tests/convergence/test_kernel_keys.py` 전부 | `kernel_keys` 삭제(kind 당 폭 키 운반 폐기, 설계 40 §3.9 LY7) | `tests/convergence/test_key_exclusion.py`(행 그룹 단위 키 제외), `test_realized_geometry.py` |
| `tests/convergence/test_place_layout.py::test_conflict_narrows_kind_to_best_scoring_key`, `test_score_tie_picks_smaller_key` | kind 키 충돌 좁히기(`narrowed`)·`PlacedLayout.keys` 삭제 | `test_place_layout.py::test_excluded_row_group_keys_reach_layout_input_unchanged_and_pdk_is_not_narrowed`, `test_key_exclusion.py` |
| `tests/convergence/test_convergence_values.py` 의 `kernel_keys` 진입점 항목, `PlacedLayout.narrowed·keys` 칸 단언 | 위와 같음 | 같은 파일 15 진입점·`PlacedLayout` 칸 등식 |
| `tests/convergence/test_layout_score.py` 전부(`test_score_counts_each_component`, `test_score_orders_lexicographically`), `test_convergence_values.py` `ENTRY_POINTS` 의 `layout_score` 항목(15 -> 14, 함수명 `..._has_14_entry_points_...`) | `layout_score` 삭제: 호출처 0(`gmid_engine` 안 `.py` grep 0, CONTRACT 3절 '(삭제)'). 좁히기 후보 비교가 없어져 소비자 없음 | 대체 계약 없음. 미배치(`unplaced`) 판정은 `test_place_layout.py`·`test_converge_point.py` |
| `tests/sizing/test_input_window.py` 의 `test_interior_y_maps_into_saturation_window[5]`, `test_window_ends_are_saturated[2]`, `test_window_found_when_rail_midpoint_is_outside`, `test_off_mid_window_maps_y_and_ends_saturated[14]`, `test_mid_window_ends_have_nonnegative_saturation_slack[2]` (24건) | E-13: 커널 `node.dc_window` 는 KVL 순서 창(V_DS ≥ 0)이고 포화 여유(VDSAT·tol)를 읽지 않는다. 옛 전제 '기록된 창 = 정확한 포화 창(±tol_V), 창 안 y 는 모두 봉인, 창 끝 y = 0·1 도 포화 여유 ≥ 0'이 사라졌다. 이 toy 의 뿌리 `in` 은 게이트만 닿아 창 = 레일 범위(실측 [0, 1.8])이고 y 는 레일 범위로 사상된다. 기대를 낮추지 않고 단언을 물리 결론으로 옮겼다(아래 covered_by) | `test_input_window.py::test_y_mapped_inside_exact_saturation_window_seals[mid·below·above × t 0.3·0.5·0.7]`(정확한 포화 창 안 -> 봉인 7 pass + 독립 여유 ≥ 0 + V(in) 사상), `test_y_mapped_outside_exact_saturation_window_is_never_sealed[12]`·`test_rail_end_y_is_never_sealed[6]`(창 밖·레일 끝 -> 봉인 안 됨), `test_seal7_slack_v_is_not_better_than_independent_slack`(봉인 7 slack_v ≤ 독립 여유), `test_recorded_window_is_order_window_wider_than_exact_saturation_window`(순서 창 ⊋ 포화 창). 옮길 곳 없는 단언: '기록된 창 끝 = 정확한 포화 창 끝 ±tol_V'는 정의가 바뀌어 폐기(순서 창 끝은 `tests/sizing/test_block_dc.py` T-W1~4 가 덮음) |
| `tests/sizing/test_input_window.py::test_empty_window_rejected` (이름 `test_empty_exact_saturation_window_rejects_every_y` 로 바꿈) 의 `reason == "empty_window"`·`node == "in"` 단언 | 사유 `empty_window` 소멸(커널이 포화 창을 좁히지 않음). `SealViolationError` 거부(어떤 y 도 봉인 안 됨)는 유지 | 같은 test(물리 결론), 사유는 봉인 7 또는 VDS < 0 LUT 정의역 밖 `lut_query_failed` |
| `tests/sizing/test_size_and_seal_local.py::test_whole_circuit_candidate_failure` 의 `reason == "empty_window"`·'어느 기둥을 골라도 ok = False' | 같은 사유 + 전 회로 공통 거부 소멸: 포화 위반은 위반 소자가 든 기둥의 봉인 7 로만 나온다(실측: 기둥 0 은 slack_v = −0.103 로 실패, 기둥 1 은 통과). 기대를 '실패한 기둥은 모두 봉인 7, slack_v ≤ 독립 MB 여유, 실패 기둥 ≥ 1'로 바꿈(독립 oracle `Follower` MA +0.049 / MB −0.103) | 같은 test |
| `tests/lut/test_tolerance.py`: `gm_id_inverse` 지표 단언 전부(`LOO_ORDERS_EXPECTED` 의 `gm_id_inverse` 4줄, `FIELDS` 의 `gm_id_inverse_v`·`gm_id_inverse_loo_v`, `n_targets`·`n_inverse_failed` 합계·셀별 등식, `test_r4_toy_cells` 의 `gm_id_inverse_v == loo / 8`, `test_real_scaled_values...` 의 `/8` 범위, 외부 L 값의 inv 몫, `TolVCell(None, None, 0, 0)` 4칸 형식) | M-TH1c: 지표 `gm_id_inverse` 삭제, `TolVCell` = (`id_equivalent_v`, `id_equivalent_loo_v`) 두 칸, `TOL_V_METRICS = ("id_equivalent",)`, `l_bin_checks` = `(model, id_equivalent_v)`. 삭제된 칸의 단언은 옮길 곳 없음 | 남은 지표 `id_equivalent` 의 값·환산·L 방향·외부 값 단언은 같은 파일에서 그대로 유지(독립 구현 `tol_cell_ref` 의 `eq`·`eq_loo`), 지표 삭제 자체는 `test_tolerance_metrics.py`(M-2)·`test_lut_types.py::test_constants`·`test_tolvcell_fields`. 판별 단언 하나는 값으로 바꿈: `test_real_l_rows_cells_match_independent` 의 '그 행 시도 수 > L 방향 없는 계산'(n_targets) -> '환산 전 값 ≥ L 방향 없는 독립 값 − 상한' |
| `tests/lut/test_midpoint_checks.py`: `MidpointRow.gm_id_inverse_v`·`n_targets`·`n_inverse_failed` 단언, `CONTRACT_8_TABLE` 의 (목표 수, 실패)·inv 열 | 같은 사유(`MidpointRow` = model, L_points, id_equivalent_v, vdsat_v) | `id_equivalent_v`·`vdsat_v` 독립 대조(`midpoint_ref`)·CONTRACT 8절 eq·vdsat mV 값은 유지 |
| `tests/lut/test__helpers_loo.py`, `test__helpers_anchor.py`, `test_lut_types.py`: `gm_id_inverse` 외부 값 몫·`TolVCell` 6칸 형식 | 같은 사유 | 남은 id_equivalent 몫으로 같은 구조(셀 단위 외부 값, 정규화 키, 길이 불일치 `ValueError`, 앵커 끝 ulp 조회) |

## 기대 횟수가 바뀐 test (블록 합침의 직접 결과, 폐기 아님)

| test | 옛 → 새 | 근거 |
|---|---|---|
| `tests/search/test_fd_jacobian.py::test_current_column_recomputes_dc_solve_once` (옛 `..._reuses_columns_block`) | 노드 풀이 블록 computes 증분 0 → dc_solve 1 | 노드 풀이·W 블록 합침. dc_solve 가 `dc_current` 를 읽는다(D40 §3.7-A 1 READS). dc_currents 1 은 그대로 |
| `tests/search/test_kernel.py::test_parent_reuses_lineage` | 같음 | 같음 |
| `tests/sizing/test_size_and_seal.py::test_current_perturbation_*` | 위 폐기 표 | 위 폐기 표 |

## 대체 서명으로 바꾼 test (단언 의미 유지)

* `test_realized_geometry.py`: `realized_geometry(snapshot, placements, keys)` -> `(snapshot, placements)`, 반환 `RealizedGeometry(layout_ref, w_request)`(`w_keys`·`diffusion` 칸 없음).
* `test_key_exclusion.py`: `key_exclusion(pdk, placements, kinds, sized_w, keys)` -> `(pdk, row_groups, placements, sized_w, excluded, colour)`, 반환 `((rid, 키), new_excluded | None)`.
* `test_converge_point.py`: 가짜 `place_layout(..., kinds, excluded=(), ...)`, 가짜 `PlacedLayout` 8칸, 행 그룹 `ly_row_groups`·구조 색 `dc_colour` 가짜 열.
* `tests/metrics`: `hand_write(dc_op)` 가 같은 블록의 `dc_finger` 행을 함께 쓴다(손가락 폭 = 슬라이스 폭, 정수 손가락 수). 접합 기대값의 m 은 `dc_finger.m`(옛 `W / w_m` 비정수 폐기, C-2).
