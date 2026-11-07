---
id: 20261107-fs1-toy-spec-empty-widths
spec_card: docs/02-design/specs/20261107-fs1.spec.md
test_id: skills/analog-gmid-design/gmid_engine/tests/lut/test__helpers_gmid_axis.py::test_branch_starts_at_peak_node
test_id: skills/analog-gmid-design/gmid_engine/tests/lut/test__helpers_gmid_axis.py::test_monotone_false_when_branch_gm_id_rises
test_id: skills/analog-gmid-design/gmid_engine/tests/lut/test__helpers_gmid_axis.py::test_undefined_node_inside_branch
test_id: skills/analog-gmid-design/gmid_engine/tests/lut/test__helpers_gmid_axis.py::test_cell_ok_follows_fc
test_id: skills/analog-gmid-design/gmid_engine/tests/lut/test__helpers_root.py::test_rightmost_interval_inside_branch
test_id: skills/analog-gmid-design/gmid_engine/tests/lut/test__helpers_root.py::test_peak_is_first_argmax
test_id: skills/analog-gmid-design/gmid_engine/tests/lut/test__helpers_root.py::test_leak_branch_only_target_fails
test_id: skills/analog-gmid-design/gmid_engine/tests/lut/test__helpers_root.py::test_flat_interval_takes_upper_end_when_residual_zero
test_id: skills/analog-gmid-design/gmid_engine/tests/lut/test__helpers_root.py::test_flat_interval_inconsistent_cell_rejected
test_id: skills/analog-gmid-design/gmid_engine/tests/lut/test__helpers_root.py::test_endpoint_exact_match_is_inside
test_id: skills/analog-gmid-design/gmid_engine/tests/lut/test__helpers_root.py::test_cell_choice_matches_legacy_when_legacy_root_in_branch
test_id: skills/analog-gmid-design/gmid_engine/tests/lut/test_fingerprint.py::test_lm1e_f4_fp_item_tuple_contract
test_id: skills/analog-gmid-design/gmid_engine/tests/lut/test_gm_id_curve.py::test_undefined_node_is_nan
test_id: skills/analog-gmid-design/gmid_engine/tests/lut/test_gm_id_curve.py::test_cell_class_slope_undefined
test_id: skills/analog-gmid-design/gmid_engine/tests/lut/test_id_inverse.py::test_non_monotonic_vs_out_of_range
test_id: skills/analog-gmid-design/gmid_engine/tests/lut/test_id_inverse.py::test_curve_undefined
test_id: skills/analog-gmid-design/gmid_engine/tests/lut/test_lut_set.py::test_bin_missing_t7_toy_spec_passes_without_midpoints
test_id: skills/analog-gmid-design/gmid_engine/tests/lut/test_tolerance.py::test_no_inner_points_all_none
test_id: skills/analog-gmid-design/gmid_engine/tests/lut/test_tolerance.py::test_vds_linear_fallback_order
test_id: skills/analog-gmid-design/gmid_engine/tests/lut/test_vgs_current_density.py::test_non_monotonic_branch
test_id: skills/analog-gmid-design/gmid_engine/tests/lut/test_vgs_current_density.py::test_branch_starts_at_peak
test_id: skills/analog-gmid-design/gmid_engine/tests/lut/test_vgs_current_density.py::test_undefined_node
test_id: skills/analog-gmid-design/gmid_engine/tests/lut/test_vgs_root.py::test_curve_undefined
---
## 문제의 test

위 23개(전부 `tests/lut/`). 공통 입력: `tests/lut/conftest.py:84` `TOY_SPEC = LutSpec(1e-8, (("nmos", 1.5e-6),), ...)`(최소 finger 폭 1.5 µm)로, 폭 1e-6 이하 슬라이스만 가진 toy LUT 를 `load_lut_set` 으로 적재한다
(`curve_lut` 등 fixture). 이 test 들은 FS-1 에서 바뀌지 않은 파일이고 기대값도 바뀌지 않았다.

## 근거(oracle 또는 사용자 원문)

interface §2 / spec 계약 1: "`load_lut_set` 후보 0 거부: 슬라이스가 있는 kind마다 `widths(lut, kind)`가 비면 `SchemaRejectedError` detail `{reason: "wf_candidates_empty", kind}`". 위 fixture 의 nmos 슬라이스 폭은 모두 최소 finger 폭
1.5 µm 보다 좁아 `widths(lut, "nmos") == ()` 이므로 새 관문이 정확히 그대로 적재를 거부한다(실측: 23개 전부 `SchemaRejectedError` reason `wf_candidates_empty`, kind `nmos`; 다른 실패 사유 0).

특히 `test_bin_missing_t7_toy_spec_passes_without_midpoints` 는 이름 그대로 '`widths` 가 비는 toy spec 은 중점 없이 적재가 통과한다'(D7 `_require_midpoints` 는 `widths` 슬라이스만 훑는다)를 단언한다 -- 새 관문과 정면으로 부딪힌다.
interface §2 C-1/C-1′ 은 `write_r4_bins_lut` 꼴 toy 의 최소 폭만 다루고 이 `TOY_SPEC` fixture 군은 다루지 않았다. spec '분류 표'의 `lut/test_lut_set.py` 행은 "새 test 더함"으로만 적혀 있어 기존 fixture 의 `min_finger_w_m` 정정이 범위에 없다.
FS-1 코드는 계약대로 거부하므로, 이 23개는 코드 쪽에서 통과시킬 수 없다(통과시키려면 새 관문을 좁히거나 toy 에 예외를 두어야 하는데 둘 다 fail-closed·상수 발명 금지 위반).

## 요청

`TOY_SPEC` 계열 fixture 의 `min_finger_w_m` 를 toy 슬라이스 폭 이하로 맞추거나(후보가 하나 이상 되게) 이 23개 test 가 쓰는 toy LUT 에 후보를 만든다. `test_bin_missing_t7_toy_spec_passes_without_midpoints` 는 입력(후보가 없는
spec)이 새 계약에서 적재 불가이므로 의미를 다시 정해야 한다(D7 의 `widths` 밖 슬라이스는 보지 않는다는 성질은 후보가 있는 spec 에서 `widths` 밖 슬라이스(최소 폭 아래)를 따로 두는 toy 로 보일 수 있다).
