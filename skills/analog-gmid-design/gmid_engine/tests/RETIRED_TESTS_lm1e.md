# 폐기·교체 test -- card 20261106-lm1e (판정 기록 근거 `retired_tests`, 계약별 `covered_by`)

규칙: 정의가 바뀌어 전제가 깨진 test 는 고치지 않고 지운다(원칙 33, O-155 B1). 근거 = 계획 N6.40 LM-1e, interface `20261106-lm1e.interface.md` §2·§8.
옛 중점 파일 형식(`w_ref_m`·`<열>_<접미사>` 열·meta `L_source`)과 단일 파일 선언은 사라졌다: 중점은 폭마다 DC 슬라이스 npz 꼴 파일 한 장이다.
**물리 단언은 그대로 옮긴다**: 이동은 '이동' 표, 지운 것은 '폐기' 표(사유와 `covered_by` 포함).

## 폐기

| test (옛 파일) | 사유 | covered_by |
|---|---|---|
| `tests/lut/test_lut_set.py::test_reject_l_source_unrecorded`(3 case), `test_l_source_matching_cap_accepted_mismatch_rejected` | 중점 meta `L_source` 와 기준 LUT `L_source` 대조 폐기(interface §2: meta `L_source` 는 읽지 않는다, 옛 사유 `lut_midpoints_l_source_*` 삭제) | `tests/lut/test_provenance.py::test_lm1e_g4_conditions_mismatch`(G4·G4b·G4c: generator_sha256·model_files_sha256·ngspice 대조), `tests/lut/test_lut_set.py::test_lm1e_old_l_source_reasons_never_raised`(L_source 를 읽지 않는다), `test_lm1e_g1c_*`(L 격자 정합 G1c) |
| `tests/lut/test_midpoint_checks.py::test_width_differs_for_other_width`, `::test_real_other_width_width_differs` | 중점 표가 폭마다 있어 '중점 폭 다름' 사유가 없다(interface §3 `midpoint_bracket` 표 -- 사유 순서에서 `width_differs` 삭제) | `tests/lut/test_midpoint_checks.py::test_c2_other_width_has_no_midpoint_table`(C-2), `::test_lm1e_r1_real_load_midpoints_cover_widths`(R-1) |
| `tests/lut/test_lut_set.py::test_reject_width_missing_and_off_grid`, `::test_reject_column_missing`(ID_n·GM_n), `::test_reject_shape_mismatch`, `::test_reject_conditions_mismatch`(corner·temp_c), `::test_reject_axes_mismatch`, `::test_reject_order` | 접미사 열·`w_ref_m` 형식 폐기 -- 같은 사유를 새 형식 파일로 다시 쓴다(사유 이름은 interface §2 표) | `tests/lut/test_provenance.py::test_lm1e_g1_*`·`test_lm1e_g1b_*`·`test_lm1e_g_order_*`, `tests/lut/test_lut_set.py::test_lm1e_g5_*`·`test_lm1e_g6_*`·`test_lm1e_g7_*`·`test_lm1e_g7b_*`·`test_lm1e_gate_order` |
| `tests/lut/test_provenance.py::test_midpoints_recorded_in_provenance`, `::test_midpoints_missing` | `LutProvenance.midpoints_path`·`midpoints_l_source`·`midpoints_conditions` 칸 삭제, `midpoint_sources` tuple 로 | `tests/lut/test_provenance.py::test_lm1e_midpoint_sources_recorded`, `::test_lm1e_g0_midpoints_missing` |
| `tests/lut/test_fingerprint.py::test_midpoints_add_fp_item`, `::test_midpoints_content_changes_fp_path_does_not` | 같은 사유 | `tests/lut/test_fingerprint.py::test_lm1e_f1_*`·`f2`·`f3`·`f4` |
| `tests/lut/test_data_location.py` 의 `verify_midpoints` 항목 parametrize(`test_bad_file_entries`·`test_file_missing`·`test_sha256_mismatch` 의 `verify_midpoints` case) | 옛 단일 객체 선언 폐기 -- 배열 | `tests/lut/test_data_location.py::test_lm1e_midpoints_*` |

## 교체 (기대 근거가 바뀜 -- 단언 대상은 그대로, 근거만 새 자료로)

| test | 바뀐 것 | 근거 |
|---|---|---|
| `tests/lut/test_vdsat_tolerance.py::test_real_cells_match_independent`·`::test_real_contract_measured` 의 w_key 72(nmos)·84(pmos) case | 옛: 중점이 없는 폭이라 외부 값 없음, 계약 5.2 의 옛 실측 문자열(p50 0.97 등)과 대조. 새: 이 폭들도 `widths` 안이라 자기 중점 파일을 가진다(D7) -> 독립 구현(`midpoint_ref`)으로 외부 값을 넣은 기대와 대조, 옛 실측 문자열 대조는 없앤다(5.2 문장 갱신은 이 card 범위 밖 -- 보고) | interface §3 D7·§7 |
| `tests/lut/test_fingerprint.py::test_real_fp_midpoints_item` | 옛: 중점 없이 로드한 지문과 비교. 새: 실 LUT 는 중점 없이 적재되지 않으므로(D7) 중점 항목을 지운 provenance 의 지문과 비교; '항목 없음'은 toy F-4 | interface §4 F-4 |
