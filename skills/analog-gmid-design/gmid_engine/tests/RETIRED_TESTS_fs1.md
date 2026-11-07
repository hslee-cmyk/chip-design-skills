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
