# 폐기·교체 test -- card 20261106-jc1 (판정 기록 근거 `retired_tests`, 계약별 `covered_by`)

규칙: 정의가 바뀌어 전제가 깨진 test 는 고치지 않고 지운다(원칙 33, O-155 B1). 근거 = 계획 N6.42 JC-1, interface `20261106-jc1.interface.md` §1~§8.
접합 Cdb·Csb 의 출처가 PDK 모델 카드 BSIM4 접합 식에서 LUT 기기 폭 표 VGS 최소 조회 비례로 바뀌었다(DEC-91 (2)(3), O-247·O-248): BSIM4 식·접합 파라미터 운반(`params`·`pdk_decl_sha256`)·
`dc_finger` 의 접합 입력(`_finger_row`)과 그에 묶인 test 는 사라진다. **물리 단언은 그대로 옮긴다**: 이동·교체는 아래 표, 지운 것은 '폐기' 표(사유와 `covered_by` 포함).
**공통 ε_d**(= (gm/ID)·tol_V) 는 Q-N11 B 로 폐기된 정의라 어떤 새 기대값·toy 식에도 쓰지 않는다(카드 §6 (c)).

## 폐기

| test (옛 파일) | 사유 | covered_by |
|---|---|---|
| `tests/metrics/test_junction_cap.py` 의 BSIM4 식 test 전부: `test_reference_formula_matches_hand_example`, `test_hand_examples`(7 case), `test_temperature_factor_clamped_at_zero`, `test_built_in_potential_temperature_shift`, `test_negative_sidewall_term_only_dropped_in_reverse_bias`, `test_zero_c0_in_reverse_bias_contributes_zero`, `test_dwj_shrinks_gate_sidewall_and_perimeter`, `test_m_scales_linearly_and_may_be_fractional`, `test_asymmetric_random_against_reference`, `test_params_rejected`, `test_params_normalised_to_float_and_frozen`, `test_call_rejected`, `test_pb_just_above_zero_accepted`, `test_from_pdk_decl_sky130`, `test_from_pdk_decl_unknown_kind_and_wrong_decl`, `test_contract_84_examples`, `test_consumer_call_85_chain_and_memo`, `test_sky130_grid_against_reference_formula`, `test_against_ngspice_27c`, `test_against_ngspice_temperature_correction`, `test_documented_discontinuity_*`(3), `test_no_discontinuity_when_perimeter_includes_gate_edge`, `test_generality_toy_pdk_without_code_change` | `junction_caps`·`JunctionParams`·`JunctionCaps`·`from_pdk_decl` 삭제(BSIM4 식·perMod·온도 보정·바이어스 의존 전부 사라짐; 접합 값은 LUT 열 × 면적 비) | `tests/metrics/test_junction_cap.py::test_junction_c0_*`·`test_junction_j1_*`~`test_junction_j8_j10_*`·`test_vgs_min_j11_*`·`test_vgs_min_j12_*`(J-1~J-12, C-0) |
| 같은 파일 `test_geometry_rejected`·`test_geometry_normalised_zero_area_allowed_and_frozen`, `test_from_lut_rule_sky130`, 규칙 기하 부분(generality toy) | **폐기 아님 -- 유지**(분류 ③: `DiffusionGeometry`·`from_lut_rule` 는 r 의 기하·oracle 넷리스트 ad/as/pd/ps 출처). 같은 파일에 남는다 | -- |
| `tests/metrics/test_junction_source.py` 의 `test_fields_order`(params·pdk_decl_sha256 칸), `test_from_decls_kinds_params_temp_sha`, `test_kinds_follow_lut_not_decl`, `test_params_of`, `test_sky130_decls`, `test_frozen_immutable_fingerprint` 의 params·pdk_decl_sha256 변형 | `params`·`pdk_decl_sha256`·`params_of`·`from_decls(pdk_decl, …)` 삭제 | `tests/metrics/test_junction_source.py::test_junction_s1_*`·`test_junction_s2_s3_*`(S-1~S-3), `test_frozen_immutable_fingerprint`(새 칸), `test_junction_temperature_follows_lut_not_a_constant`, `test_missing_lut_temperature_rejected`, `test_junction_pre_layout_geometry_is_rule_geometry` |
| `tests/metrics/test_junction_field.py::test_field_holds_declared_junction_source`, `::test_same_input_reuses_and_changed_decl_recomputes` 의 `pdk_decl` 인자·params 지문 | `junction_field(snapshot, pdk_decl, lut_rule_decl, lut)` 에서 `pdk_decl` 인자 삭제 | `tests/metrics/test_junction_field.py::test_junction_field_holds_proportional_reference`, `::test_junction_s4_same_input_reuses_and_changed_decl_recomputes`(S-4) |
| `tests/metrics/test_ss_linearize.py` 의 BSIM4 접합 test: `_bit_junction`(계약 S-11 `junction_caps` 비트 동일), `test_junction_bias_and_side_mapping`(BSIM4 쪽·바이어스 매핑), `test_junction_value_error_propagates_unwrapped`(Weffcj ≤ 0·PB(T) ≤ 0 ValueError), `test_negative_check_junction_ok_params_do_not_raise`, `test_lut_temperature_is_junction_temperature`(온도 보정 값), `test_s12_each_bundle_field_changes_input_version` 의 `params_other_pdk_decl`·`pdk_decl_sha256` case, `test_s12_temp_change…` 의 온도 따른 값 변화 단언 | BSIM4 식·온도 보정·PDK 파라미터 사라짐; 접합 값은 온도·바이어스(VGS 최소 조회 열 외) 의존이 없다 | `tests/metrics/test_ss_linearize.py::test_vgs_min_da_*`·`test_vgs_min_da2_*`·`test_vgs_min_dc_*`·`test_vgs_min_de_*`·`test_vgs_min_df_dg_*`·`test_vgs_min_db_*`(D-a~D-g), `test_junction_lookup_point_and_kind_and_width_mapping`, `test_s12_*`(묶음 필드 변경 → 재계산 1회) |
| 같은 파일 `test_block_declaration` 의 READS `("device", "dc_finger")` 항목, 소자 접합 입력 `dc_finger` 경로 전부 | 접합 기하 = 그 평가가 쓴 W 하나(`dc_finger` 의 (m, w_f) 아님; graph 규칙 3) | `tests/metrics/test_ss_linearize.py::test_block_declaration`(G-1), `test_vgs_min_g3_*`(G-3) |
| `tests/metrics/test_ss_evaluate.py` 의 S-11 `junction_caps` 비트 대조(`test_s11_junction_caps_and_approximation` 의 `junction_caps` 줄)·`dc_finger` 규칙 test·sky130 BSIM4 실선언 test | 같은 사유 | `tests/metrics/test_ss_evaluate.py::test_s11_junction_lut_vgs_min_and_approximation`, `::test_jc1_df_dg_*`(D-f·D-g `ss_evaluate` 경유), `tests/metrics/test_ss_linearize.py` D-a~D-g |
| `tests/metrics/test_lut_parameters.py::test_lut_parameters_constant`(6열·"cdb not in") | LUT 열 목록이 8열(cdb·csb 포함)이 된다 -- 목록 소속만(Δp 꼴은 RS-1) | `tests/metrics/test_lut_parameters.py::test_lut_parameters_constant`(8열로 교체)·`test_jc1_ra_*`(R-a)·`test_jc1_rc_*`(R-c)·`test_jc1_rb_*`(R-b) |
| `tests/core/test_pdk_decl.py` 의 접합 54키 test: `test_drain_to_source_mapping_helper`, `test_sky130_declares_exactly_54_junction_quantities`, `test_sky130_junction_values_recomputed_independently`(2 case), `test_sky130_junction_rules_are_bin_common_with_first_block_line`(2 case) | PDK 선언에서 접합 파라미터 52키 삭제(tnom 두 키는 oracle 소비라 유지, JP-1 뒤 이동) | `tests/core/test_pdk_decl.py::test_jc1_n3_sky130_declares_only_the_two_tnom_junction_quantities`(N-3) |
| `tests/integration/test_s0_layer_9circuits.py::test_junction_source_content_unchanged_from_base` 의 옛 기준선(params 지문·PDK sha) (O-229 연기 파일 -- 판정자가 2회로 연기에서 실행) | `JunctionSource` 칸이 (`lut_rule_decl`, `reference`, `temp_c`) 로 바뀜 | 같은 test 가 새 칸(kind 별 reference 기하 = LUT 생성 규칙 선언 × 그 kind `w_ref_m`, temp_c)을 정의식으로 대조(기준선 fixture 교체 -- 아래 '교체') |

## 교체 (기대 근거가 바뀜 -- 단언 대상은 그대로, 근거만 새 자료로)

| test | 바뀐 것 | 근거 |
|---|---|---|
| `tests/metrics/test_resolution.py::_expected_lut`(`test_r2_*` 셋) | 옛: 6열 고정 tuple·`eps[k]·|p|` 로 Δp 계산. 새: 열 목록·Δp 모두 입력 `ParameterSet`(`ps.params`·`ps.delta`)에서 읽는다(Δ 꼴 독립 -- cdb·csb 에 ε·|p| 꼴 가정 0) | interface §8 `test_resolution.py` 행 (판정 M1) |
| `tests/metrics/test_resolution.py::test_r3_per_mos_share` | `P = 12` -> `P = 15` | LUT 열 목록이 6 -> 8열로 늘어난 것을 따르는 갱신(M1 8 + M2 7). 허용오차 식 `(P − 1)·eps` 는 그대로 -- 기준 약화 아님 |
| `tests/metrics/test_lut_parameters.py::test_all_six_parameters_and_negative_capacitance_magnitude` -> `test_all_eight_parameters_…` | 파라미터 목록 8열(길이 12 -> 15); 기존 6열 원소의 `delta == ε·|p|` 단언은 6열 원소로만 한정(as-built 회귀 -- RS-1 몫); cdb·csb 원소는 존재·유한·≥ 0 만 | interface §8 `test_lut_parameters.py` 행 (판정 M1) |
| `tests/metrics/conftest.py` `LUT_P` | 8열(계약 문자열의 test 쪽 사본). `LUT_P_OLD`(6열) 추가: R-b 항 없는 경로 | 같은 행 |
| `tests/metrics/conftest.py` `write_lut_v2`·`lut_cap_cols`·`lut_cap_closed` | 기준 LUT 에 CDD·CSS 열(합성 닫힌 식)을 더한다; `oracle_junction` = 정의 문장 손 식(옛 BSIM4 `ref_caps`·`TOY_JUNCTION` 삭제); `toy_junction(root, lut, rule_line=)` = `from_decls(규칙 선언, LUT)` | interface §8 `metrics/conftest.py` 행 |
| `tests/sizing/wb1_toy.py::write_r4_bins_lut(jc1_cols=)` | 기준 폭 표 CGS·CDD·CSS 열(상수)을 더하는 선택 인자(기본 False = 기존 호출 불변); `off_cases.py`·`test_ss_off_op_slices.py` 가 True 로 부른다 | 접합 입력 열 필요 |


## 삭제 (호출처 0 -- 죽은 사본 금지)

| 대상 | 사유 |
|---|---|
| `tests/convergence/conftest.py::bsim4_junction`(BSIM4 접합 용량 폐형식 helper) 와 `test_converge_point.py` 의 import | 호출처가 `test_real_junction_caps_from_realized_diffusion` 하나였고 그 test 가 정의 손 식(LUT npz 원 파일 numpy 직접 읽기)으로 바뀌어 호출처 0. 엔진이 BSIM4 접합 식을 쓰지 않는다 |

## toy LUT 생성기 보강 (ss_dev 가 기준 폭 표 CGS·CDD·CSS 열을 요구한다)

값은 손 식: CGS = CGG − CGD = 8e-16(CGB 열 없음 -> 용량 모형은 그대로 `cgg_minus_cgd_at_gs`), CSS − CGS = 5e-16(CSS = 1.3e-15), CDD − CGD = 3e-16(CDD = 5e-16). 기존 `cdd` 플래그 생성기의 CDD(2e-16 = CGD)는 E-18 닫힌 식이 그대로이도록 값을 유지한다(접합 항 cdb = 0 허용: 수동성 관문은 `>= 0`).

| 생성기 | 처리 | 남긴 플래그 |
|---|---|---|
| `sizing/conftest.py` 첫 생성기(r4 기본 toy) | CGS·CSS·CDD 추가 | 없음 |
| `sizing/conftest.py::write_r4_lut` | CGS·CSS 추가, `cdd` 기본값 False -> True | `cdd=False` 로 열 없는 표(E-18 거부 입력) |
| `metrics/gb4_hand.py` | CGS·CSS 추가, `cdd` 기본값 False -> True | `cdd=False` |
| `metrics/wb1_gb4.py`, `search/test_cell_floor.py`, `search/test_current_box.py`, `search/test_kernel.py`, `search/test_search_domain.py`, `sizing/test_block_dc.py` | CGS·CSS·CDD 추가 | 없음(E-18 거부 test 를 쓰는 생성기가 아님) |
| `search/u13_hand.py` | CGS·CSS 추가(cap_scale 비례); CDD 는 기존 `cdd=True` 기본 | `cdd=False` -- E-18 거부 test(`test_iv_currents`, `test_macro_poles`)가 그대로 쓴다 |
| `sizing/wb1_toy.py` | 앞 커밋: `jc1_cols`(기본 False; ss 경로 호출자 `off_cases`·`test_ss_off_op_slices`·`search/wb1_flow` 가 True) | `jc1_cols=False` |


## 폐기 (동결 판정 M1)

| test (옛 파일) | 사유 | covered_by |
|---|---|---|
| `tests/convergence/test_realized_geometry.py::test_layout_resolve_l2_waiting_device_row_erased_in_junction_input_is_realized_finger_missing` | `ss_evaluate` 입력에서 대기 소자 `dc_finger` 행을 지워 접합 경로(`ss_linearize._finger_row`)의 `realized_finger_missing` 정지를 기대했다. card 범위: `ss_dev` READS 에서 `dc_finger` 가 빠지고 접합이 `dc_finger` 를 읽지 않아 code 뒤에는 정지 자리가 없다 | 짝 test `test_layout_resolve_l2_device_without_input_finger_row_is_realized_finger_missing` 는 유지(정지 자리 = `block_dc` 실현 입력 손가락 관문). 접합 쪽은 `test_ss_linearize.py::test_vgs_min_da2_dc_finger_does_not_matter`(D-a2: `dc_finger` 행 값·열 유무와 무관, 정지 없음) |

## 교체 행에 덧붙임 (동결 판정 m1: 표에 이름이 빠진 지운 test 둘)

| 옛 이름 | 새 이름 |
|---|---|
| `tests/metrics/test_junction_source.py::test_temperature_comes_from_lut_cap_conditions` | `::test_junction_temperature_follows_lut_not_a_constant` |
| `tests/metrics/test_junction_source.py::test_pre_layout_geometry` | `::test_junction_pre_layout_geometry_is_rule_geometry` |

## 복원 (동결 판정 M2)

`tests/metrics/test_junction_cap.py::test_from_lut_rule_sky130` 의 sky130 규칙 절대값 단언(`ad/as ≈ 1e-12`, `pd/ps ≈ 4e-6`)은 이 card 가 `from_lut_rule` 을 바꾸지 않으므로 원래대로 복원했다.

## D-b 합성 LUT (동결 판정 M3)

`sizing/wb1_toy.write_r4_bins_lut(jc1_cols="node")`: 접합 입력 열을 점마다 다른 손 식(`jc1_node_cdd`, `jc1_node_css`, 인덱스 (l, g, d, s))으로 쓴다. D-b 는 이 LUT 의 마디 값을 `==` 로 비교한다.
