### S01 4e31a88b 41-gain-budget:1543
OLD: ·칸·t)은 `graph/start: placement`다(40 §2.4.8). `placement`는 U17 ②에서 U15 `placer`와 함께 만들고, as-built MOD8 `Placement`(`E/convergence/convergence_values.py:47`)와 다른 것이다(40 v1.9.1 D4, 근거: 소비자 위치). 층 0 `layer0_start`는 칸 0부터 차례로 커널에 확인해 처음 받아들일 상태인 칸을 기준점으로 쓴다(
NEW: ·칸·t)은 `graph/start: placement`다(40 §2.4.8). `placement`는 U17 ②에서 U15 `placer`와 함께 만들고, as-built MOD8 `Placement`(`E/convergence/convergence_values.py`)와 다른 것이다(40 v1.9.1 D4, 근거: 소비자 위치). 층 0 `layer0_start`는 칸 0부터 차례로 커널에 확인해 처음 받아들일 상태인 칸을 기준점으로 쓴다(

### S02 4e31a88b 41-gain-budget:699
OLD: values, ops, floors)`**(`region_rows`와 다른 함수 -- 아래 '(9)과의 관계'): `device.dc_conduction_floor`(writer `dc_seal_conduction`, `E/sizing/seal_conduction.py:12`)에 값이 있는 MOS마다 행 하나 = `(terms, I0 − I_floor, "conduction")` -- I0 = 봉인점 `device.dc_op`의 `current`(선
NEW: values, ops, floors)`**(`region_rows`와 다른 함수 -- 아래 '(9)과의 관계'): `device.dc_conduction_floor`(writer `dc_seal_conduction`, `E/sizing/seal_conduction.py`)에 값이 있는 MOS마다 행 하나 = `(terms, I0 − I_floor, "conduction")` -- I0 = 봉인점 `device.dc_op`의 `current`(선

### S03 4e31a88b 40-engine:619
OLD: tor` | `E/metrics/point_solve.py:40`(행렬 G + jωC), `E/metrics/sensitivity.py:76`(ω > 0이면 복소, ω = 0이면 실수 `dc_limit_parts`), `E/metrics/_helpers_probe.py:122`(복소 z) | 무관 실측(n = 1~11, 1,000회) |
NEW: lu_factor` | `E/metrics/point_solve.py`(행렬 G + jωC), `E/metrics/sensitivity.py`(ω > 0이면 복소, ω = 0이면 실수 `dc_limit_parts`), `E/metrics/_helpers_probe.py`(복소 z) | 무관 실측(n = 1~11, 1,000회) |

### S04 4e31a88b 40-engine:1103
OLD: dev`(as-built는 `op.gm_id * op.current`를 따로 계산, `E/metrics/ss_linearize.py:70`), 봉인 3(`E/sizing/seal_kcl.py:35`), 전력 분해능 b_P(`E/search/search_values.py:123`)가 모두 이 필드를 읽는다. parent에 의존하지 않으므로 같은 θ는 parent와 무관하게 같은 봉인 결과를 낸다. 순환 없음: `dc_gm`은 ⑤ W 블록 뒤의 `dc_o
NEW: . `ss_dev`(as-built는 `op.gm_id * op.current`를 따로 계산, `E/metrics/ss_linearize.py`), 봉인 3(`E/sizing/seal_kcl.py`), 전력 분해능 b_P(`E/search/search_values.py`)가 모두 이 필드를 읽는다. parent에 의존하지 않으므로 같은 θ는 parent와 무관하게 같은 봉인 결과를 낸다. 순환 없음: `dc_gm`은 ⑤ W 블록 뒤의 `dc_o

### S05 4e31a88b 41-gain-budget:714
OLD:   - **READS 지문**(계획 v6.21 재검증 Info): 블록 입력 버전 = `fp_of((name, code_hash, projection.fp))`(`E/core/compute_block.py:129-132`), projection 지문은 읽은 필드의 `FieldValue.value_fp`(= `fp_of(value)`, 쓰기 때 한 번 -- `E/core/field_value.py
NEW:   - **READS 지문**(계획 v6.21 재검증 Info): 블록 입력 버전 = `fp_of((name, code_hash, projection.fp))`(`E/core/compute_block.py`), projection 지문은 읽은 필드의 `FieldValue.value_fp`(= `fp_of(value)`, 쓰기 때 한 번 -- `E/core/field_value.py

### S06 4e31a88b 40-engine:684
OLD: | 노드 전압·소자 전류 | V·A | tol_V·tol_I | 계획 IC2(같은 출처), `E/sizing/seal_tolerances.py:5-11`. 노드 전압의 tol_V = 그 노드에 채널이 닿는 MOS의 `dc_tol_v` 최솟값(Q-N3 확정, 사용자 결정 2026-10-15 "기본안대로 진행해", U-79). 채널
NEW: | 노드 전압·소자 전류 | V·A | tol_V·tol_I | 계획 IC2(같은 출처), `E/sizing/seal_tolerances.py`. 노드 전압의 tol_V = 그 노드에 채널이 닿는 MOS의 `dc_tol_v` 최솟값(Q-N3 확정, 사용자 결정 2026-10-15 "기본안대로 진행해", U-79). 채널

### S07 4e31a88b 40-engine:571
OLD: - `cached_property`: `layout/_helpers_alias.py:28,32,36`
NEW: - `cached_property`: `layout/_helpers_alias.py`

### S08 4e31a88b 41-gain-budget:704
OLD: (ICM_CONFIG_WRITER, (("node", "dc_window_cfg"), ("graph", "icm_config")))`. θ 프레임 창 `node.dc_window`(writer `dc_columns`, 소비자 `E/search/fd_jacobian.py:54-55`)는 바꾸지 않는다(O-58 S-1).
NEW: (ICM_CONFIG_WRITER, (("node", "dc_window_cfg"), ("graph", "icm_config")))`. θ 프레임 창 `node.dc_window`(writer `dc_columns`, 소비자 `E/search/fd_jacobian.py`)는 바꾸지 않는다(O-58 S-1).

### S09 4e31a88b 41-gain-budget:640
OLD: | A3 | `saturation_rows` = 전도 MOS마다 (d, s, 부호, VDS − VDsat − tol_VDsat), 선형 선언 소자 제외, VDSAT 열·tol 미정이면 None | `E/sizing/block_columns.py:225-244` |
NEW: | A3 | `saturation_rows` = 전도 MOS마다 (d, s, 부호, VDS − VDsat − tol_VDsat), 선형 선언 소자 제외, VDSAT 열·tol 미정이면 None | `E/sizing/block_columns.py` |

### S10 4e31a88b 40-engine:397
OLD: | `LocalSeal` | `snapshot_fragment`, `gain_db`, `power_w`, `area_m2`(`E/sizing/size_and_seal_local.py:119-129`) | 국소 스냅샷(41 §5.3.9). 봉인 통과·실패 레코드는 봉인 필드, 국소 전력·면적·gain·Z_out은 블록 범위 metric 필드(§2.4.8) |
NEW: | `LocalSeal` | `snapshot_fragment`, `gain_db`, `power_w`, `area_m2`(`E/sizing/size_and_seal_local.py`) | 국소 스냅샷(41 §5.3.9). 봉인 통과·실패 레코드는 봉인 필드, 국소 전력·면적·gain·Z_out은 블록 범위 metric 필드(§2.4.8) |

### S11 4e31a88b 40-engine:677
OLD: 면적(`area_m2`·`gate_area_m2`·`area_est_m2`·출발 구간 상태 면적) | m² | b_A = `grid_m` × `w_min_m` | `E/search/search_domain.py:172`, `E/search/search_values.py:76·80` |
NEW: | 면적(`area_m2`·`gate_area_m2`·`area_est_m2`·출발 구간 상태 면적) | m² | b_A = `grid_m` × `w_min_m` | `E/search/search_domain.py`, `E/search/search_values.py` |

### S12 4e31a88b 40-engine:658
OLD: ish_l_cells`, `E/search/l_bin_search.py:32-34`)의 정지는 bool만 내고 `:41`·`:49`에서 조용히 끝나며, `best`가 없는 `solve_eps` 결과는 `:63-65`에서 버려져 `E/search/find_front.py:137`의 `stops_wall_budget`에 세지지 않는다. 그래서 지금은 (나)를 기록에서 확인할 수 없다. 이 card의 code 몫으로 L-b 종료 사유(`converged`·
NEW: b(`polish_l_cells`, `E/search/l_bin_search.py`)의 정지는 bool만 내고 `:41`·`:49`에서 조용히 끝나며, `best`가 없는 `solve_eps` 결과는 `:63-65`에서 버려져 `E/search/find_front.py`의 `stops_wall_budget`에 세지지 않는다. 그래서 지금은 (나)를 기록에서 확인할 수 없다. 이 card의 code 몫으로 L-b 종료 사유(`converged`·

### S13 4e31a88b 40-engine:484
OLD: `drain`·`gate`·`source`(`body`는 읽지 않는다 -- 같은 이유). 세 블록 모두 `W_m`을 읽지 않는다. `W_m`·`body`·`diode`·`ID_A`·`vds_V`·`vsb_V`를 읽던 것은 정준 표지(`canonical_naming.py:28-60`)뿐이다 | `ly_finger_candidates` READS device `ly_point`(`gm_id`)·`ly_slices`, graph `ly_pdk`. `ly_pat
NEW: `drain`·`gate`·`source`(`body`는 읽지 않는다 -- 같은 이유). 세 블록 모두 `W_m`을 읽지 않는다. `W_m`·`body`·`diode`·`ID_A`·`vds_V`·`vsb_V`를 읽던 것은 정준 표지(`canonical_naming.py`)뿐이다 | `ly_finger_candidates` READS device `ly_point`(`gm_id`)·`ly_slices`, graph `ly_pdk`. `ly_pat

### S14 4e31a88b 41-gain-budget:255
OLD:  MISS. 부분 대리물은 `E/authoring/_feedback_cuts.py:11`, `E/metrics/loop_cut.py:60`, `[ng-cmfb-pm] E/authoring/cm_partition.py`, `E/graph/matching_groups.py:202`다. SP1 본체는 `[u1-sp1]`(eae0292, 미병합)에 있다.
NEW: *상태**: MISS. 부분 대리물은 `E/authoring/_feedback_cuts.py`, `E/metrics/loop_cut.py`, `[ng-cmfb-pm] E/authoring/cm_partition.py`, `E/graph/matching_groups.py`다. SP1 본체는 `[u1-sp1]`(eae0292, 미병합)에 있다.

### S15 4e31a88b 40-engine:620
OLD: | 실수 `scipy.linalg.lu_factor`·`lu_solve` | `E/metrics/dc_limit.py:34·41`, `E/metrics/offset_analysis.py:123`, `E/metrics/_helpers_nodal.py:46·66·81`, `E/metrics/_helpers_probe.py:81·86`, `E/sizing/scc_newton.py:47·50` | 엔진 크기에서 무관 실측(n ≤ 39, 2,000
NEW: | 실수 `scipy.linalg.lu_factor`·`lu_solve` | `E/metrics/dc_limit.py`, `E/metrics/offset_analysis.py`, `E/metrics/_helpers_nodal.py`, `E/metrics/_helpers_probe.py`, `E/sizing/scc_newton.py` | 엔진 크기에서 무관 실측(n ≤ 39, 2,000회) |

### S16 4e31a88b 41-gain-budget:1459
OLD: 에서 import할 수 없다(규칙 B). 그래서 `layer0_center`는 정의식 `math.sqrt(sys.float_info.epsilon)`을 그 자리에서 쓴다 -- 같은 정의식을 그 자리에서 쓰는 선례가 이미 있다(`E/search/macro_poles.py:282`, `E/search/iv_matching_l.py:99`). 근거: 값의 출처는 정의(부동소수 기계 엡실론)이고 상수를 짓는 것이 아니다. `_REL`을 공개 이름으로 바꾸거나
NEW: 에서 import할 수 없다(규칙 B). 그래서 `layer0_center`는 정의식 `math.sqrt(sys.float_info.epsilon)`을 그 자리에서 쓴다 -- 같은 정의식을 그 자리에서 쓰는 선례가 이미 있다(`E/search/macro_poles.py`, `E/search/iv_matching_l.py`). 근거: 값의 출처는 정의(부동소수 기계 엡실론)이고 상수를 짓는 것이 아니다. `_REL`을 공개 이름으로 바꾸거나 co

### S17 e3dc6585 40-engine:1123
OLD: #### 3.7-A DC 블록 재작성 -- 레이아웃 전 W-bin 슬라이스 (v1.15.1, 계획 v6.38.2 DEC-105 (2)·card WB-1(N6.32), 사용자 결정 2026-10-13 Q6-1 (A)·O-164·O-165·O-166(U-130))
NEW: #### 3.7-A DC 블록 재작성 -- 레이아웃 전 W-bin 슬라이스 (계획 v6.38.2 DEC-105 (2)·card WB-1(N6.32), 사용자 결정 2026-10-13 Q6-1 (A)·O-164·O-165·O-166(U-130))

### S18 e3dc6585 41-gain-budget:708
OLD: .14.1; 행 꼴 = 일반 1차 행 `(terms, slack, kind)`) (ii) 구동 = **P3 묶음 = 모든 입력 포트**(v1.14.0 -- 계획 IT-2c 착수 조건 (vii); servo는 입력 포트를 출력에 묶지 않는다, O-53 A-2 갈래 소멸; v1.14.1 -- F 성분 미선언 포트 포함, 구동 = `graph.ss_nodal`의 입력 넷 그대로, O-118 3번) (iii) 감도 = `kvl_sensitivity(nodal, drive
NEW: .7-3a 6, v1.14.1; 행 꼴 = 일반 1차 행 `(terms, slack, kind)`) (ii) 구동 = **P3 묶음 = 모든 입력 포트**(계획 IT-2c 착수 조건 (vii); servo는 입력 포트를 출력에 묶지 않는다, O-53 A-2 갈래 소멸; F 성분 미선언 포트 포함, 구동 = `graph.ss_nodal`의 입력 넷 그대로, O-118 3번) (iii) 감도 = `kvl_sensitivity(nodal, drive

### S19 e3dc6585 41-gain-budget:793
OLD: (O-118 1번)·U-107(기준 도달 불가)·U-108(판정 자리)은 DE-1 (c) 몫이라 이 design은 인용만) -- 계통 offset(DE-1 (c))의 갈래 순서·판정 자리는 DE-1 design 몫이고 이 판은 설계하지 않는다 (7) **대상 없음**(v1.14.0 -- S-OS2 폐지, card RB-1 대상 없음(계획 N3.8 'IT-2 후속'); 차동 출력 스윙은 DE-1 (b)가 같은 연립·servo None으로 잰다) (8) **판정 분해
NEW: (O-118 1번)·U-107(기준 도달 불가)·U-108(판정 자리)은 DE-1 (c) 몫이라 이 design은 인용만) -- 계통 offset(DE-1 (c))의 갈래 순서·판정 자리는 DE-1 design 몫이고 이 판은 설계하지 않는다 (7) **대상 없음**(S-OS2 폐지, card RB-1 대상 없음(계획 N3.8 'IT-2 후속'); 차동 출력 스윙은 DE-1 (b)가 같은 연립·servo None으로 잰다) (8) **판정 분해

### S20 e3dc6585 40-engine:795
OLD: 용한다: `supply_nets` 필수 → 숨은 레일 (iii) → 넷 대소문자 유일 → `bias_inputs` 선언·gate 전용 → `source_manifest` 수 대조 → 태그 키 무시(U-50). spec은 출처 필수 제약, 정본 이름, θ 범위를 읽는다(v1.15.2 -- `optional_stages` 칸은 계획 SF-1 범위 11로 삭제, §3.1-1).
NEW: 용한다: `supply_nets` 필수 → 숨은 레일 (iii) → 넷 대소문자 유일 → `bias_inputs` 선언·gate 전용 → `source_manifest` 수 대조 → 태그 키 무시(U-50). spec은 출처 필수 제약, 정본 이름, θ 범위를 읽는다(`optional_stages` 칸은 계획 SF-1 범위 11로 삭제, §3.1-1).

### S21 e3dc6585 41-gain-budget:706
OLD: hi` = 아래·위 끝 상태의 값; 계산 = 아래 계산 (6); 소비자 = `metrics_aux`의 세 metric(4.7-5) -- 포트 창에서 V_cm을 다시 계산하는 둘째 생산자 금지); `undefined`: tuple[`Undefined`]). **삭제**(v1.14.0, 계획 완료 조건 (8)(f) -- 만들면 배선): 칸 `inverting_port`·`tied_ports`·`transfer`, `config` 값 `"declared_feedba
NEW: hi` = 아래·위 끝 상태의 값; 계산 = 아래 계산 (6); 소비자 = `metrics_aux`의 세 metric(4.7-5) -- 포트 창에서 V_cm을 다시 계산하는 둘째 생산자 금지); `undefined`: tuple[`Undefined`]). **삭제**(계획 완료 조건 (8)(f) -- 만들면 배선): 칸 `inverting_port`·`tied_ports`·`transfer`, `config` 값 `"declared_feedba

### S22 e3dc6585 40-engine:522
OLD: - **결과 JSON 형식**(v1.11, X-5 -- **형식 변경**): `perf.blocks` = 행 목록 `{block, part, calls, reuses, grafts, replays, computes, rec
NEW: - **결과 JSON 형식**(X-5 -- **형식 변경**): `perf.blocks` = 행 목록 `{block, part, calls, reuses, grafts, replays, computes, rec

### S23 e3dc6585 41-gain-budget:772
OLD: status_detail`·`input_window_operating_point_mismatch`·`INPUT_STATUS_OP_MISMATCH`·`CODE_INPUT_WINDOW_OPERATING_POINT_MISMATCH`(4.7-2 'S-4 갈래 몫의 꼴') 0(v1.12.10 셋째 커밋 -- 계획 (9)(d) '`git grep`'의 측정 꼴을 (c)와 하나로 정함; docstring에 '없다'는 설명은 셈하지 않음). **(S4-가)이면 D가 더 진다**(계획 (9)
NEW: status_detail`·`input_window_operating_point_mismatch`·`INPUT_STATUS_OP_MISMATCH`·`CODE_INPUT_WINDOW_OPERATING_POINT_MISMATCH`(4.7-2 'S-4 갈래 몫의 꼴') 0(계획 (9)(d) '`git grep`'의 측정 꼴을 (c)와 하나로 정함; docstring에 '없다'는 설명은 셈하지 않음). **(S4-가)이면 D가 더 진다**(계획 (9)

### S24 e3dc6585 41-gain-budget:742
OLD: *보고 열 전용**, metric 산술에 쓰지 않음 -- 계획 완료 조건 (8)(g) AST), `tol_v`: float 또는 None, `missing`: `()` 또는 `((code, detail),)`(code = `input_window_unmeasured`(v1.14.1 -- `input_window_f_component_undeclared` 삭제, O-118 3번); S-4 갈래 card가 두기로 하면 `input_window_operating_poi
NEW: *보고 열 전용**, metric 산술에 쓰지 않음 -- 계획 완료 조건 (8)(g) AST), `tol_v`: float 또는 None, `missing`: `()` 또는 `((code, detail),)`(code = `input_window_unmeasured`(`input_window_f_component_undeclared` 삭제, O-118 3번); S-4 갈래 card가 두기로 하면 `input_window_operating_poi

### S25 e3dc6585 40-engine:2180
OLD: EY`·`ls_swing` 입력 창 계산·`block_columns._refine_ends`, (v1.13.0) `node.dc_output_structure`·`OUTPUT_*`·`saturation_window` 쌍 roots·묶음 갈래·커널 뿌리 아닌 포트 항목, (v1.14.0) 설계만 있던 `IcmConfig` 칸 `inverting_port`·`tied_ports`·`transfer`·값 `declared_feedback`·`follower_beta1
NEW: UT_GROUP_KEY`·`ls_swing` 입력 창 계산·`block_columns._refine_ends`, `node.dc_output_structure`·`OUTPUT_*`·`saturation_window` 쌍 roots·묶음 갈래·커널 뿌리 아닌 포트 항목, 설계만 있던 `IcmConfig` 칸 `inverting_port`·`tied_ports`·`transfer`·값 `declared_feedback`·`follower_beta1

### S26 e3dc6585 41-gain-budget:1664
OLD:    - (옛 문언 -- 기록, v1.15.2 삭제) 모든 변수가 근 없이 끝나면 매크로 출발값을 버리고 상자 기하 중심을 쓴다. 이 값은 대체값이므로 **'추정'**으로 표기한다(v1.15.0, 계획 v6.38 후속 정정 표 '41 §6.5' -- 감사 `theta_basis_principle_audit.md` §2.5: gm·전류는 KVL 독립이라 θ 기저 위반은 아니고
NEW:    - (옛 문언 -- 기록, v1.15.2 삭제) 모든 변수가 근 없이 끝나면 매크로 출발값을 버리고 상자 기하 중심을 쓴다. 이 값은 대체값이므로 **'추정'**으로 표기한다(계획 v6.38 후속 정정 표 '41 §6.5' -- 감사 `theta_basis_principle_audit.md` §2.5: gm·전류는 KVL 독립이라 θ 기저 위반은 아니고

### S27 e3dc6585 41-gain-budget:1047
OLD: - **R-1′ 관계식 거르기**(v1.15.0, 계획 v6.38 LA-1 범위 11 → headroom-chain HC-1 범위로 이관, 사용자 결정 O-126·O-43 D2): 칸 대표 후보를 이 함수에 넣기 **전에** he
NEW: - **R-1′ 관계식 거르기**(계획 v6.38 LA-1 범위 11 → headroom-chain HC-1 범위로 이관, 사용자 결정 O-126·O-43 D2): 칸 대표 후보를 이 함수에 넣기 **전에** he

### S28 e3dc6585 40-engine:2181
OLD: `SsEvaluation.ss/dc`, `EvalResult`의 값 칸, `LocalSeal.snapshot_fragment`·`power_w`·`area_m2`, 오케스트레이터 초안 EvalCache, 이것들을 단언하던 test | **XRUN-F1 card B**(v1.11, 위 행), ①(①-b 완료: 병합 eadb729, 4차 판정 988eef4 -- 차단 0), U15 design(41 §5 v1.6) 승인, **실행 사이 재사용 제거 card**
NEW: `SsEvaluation.ss/dc`, `EvalResult`의 값 칸, `LocalSeal.snapshot_fragment`·`power_w`·`area_m2`, 오케스트레이터 초안 EvalCache, 이것들을 단언하던 test | **XRUN-F1 card B**(위 행), ①(①-b 완료: 병합 eadb729, 4차 판정 988eef4 -- 차단 0), U15 design(41 §5 v1.6) 승인, **실행 사이 재사용 제거 card**

### S29 e3dc6585 40-engine:2180
OLD: 던 `IcmConfig` 칸 `inverting_port`·`tied_ports`·`transfer`·값 `declared_feedback`·`follower_beta1`·반전 입력 식별·S-OS2·선언 되먹임 code(구현 전 삭제 -- 41 §4.7-3b 744), (v1.14.1) `block_columns` F 성분 항목 갈래·`writer_head`·`INPUT_STATUS_F_COMPONENT_UNDECLARED`, 이것들을 단언하던 test 기대값(
NEW: 던 `IcmConfig` 칸 `inverting_port`·`tied_ports`·`transfer`·값 `declared_feedback`·`follower_beta1`·반전 입력 식별·S-OS2·선언 되먹임 code(구현 전 삭제 -- 41 §4.7-3b 744), `block_columns` F 성분 항목 갈래·`writer_head`·`INPUT_STATUS_F_COMPONENT_UNDECLARED`, 이것들을 단언하던 test 기대값(

### S30 e3dc6585 42-gap-checklist:332
OLD: | D-WB2 | (v1.15.1, card WB-1 범위 0·1·2·2a) 선택 함수 `lut.finger_slice`·`slice_of_finger`·`reachable_slices`(손가락 규칙 m = ⌈W/w
NEW: | D-WB2 | (card WB-1 범위 0·1·2·2a) 선택 함수 `lut.finger_slice`·`slice_of_finger`·`reachable_slices`(손가락 규칙 m = ⌈W/w

### S31 e3dc6585 42-gap-checklist:323
OLD: | D-SF1b | (v1.15.0, card SF-1 범위 2·4·6 (c)) 삭제 키 거부: `human.driving_spec`·`load_peak_amp`·`load_dc_amp`·`compensation_ta
NEW: | D-SF1b | (card SF-1 범위 2·4·6 (c)) 삭제 키 거부: `human.driving_spec`·`load_peak_amp`·`load_dc_amp`·`compensation_ta

### S32 e3dc6585 40-engine:1012
OLD: - 영점 상쇄 저항 R은 θ 연속 성분이다(v1.15.2 -- 계획 DEC-92 (3) v6.38.3·DEC-105 (10) (b); 옛 'R = 1/Σgm(S)로 정한다(J7)'는 구조 규칙 고정값이라 대체). 구조 규칙 R = 1/Σ_{c
NEW: - 영점 상쇄 저항 R은 θ 연속 성분이다(계획 DEC-92 (3) v6.38.3·DEC-105 (10) (b); 옛 'R = 1/Σgm(S)로 정한다(J7)'는 구조 규칙 고정값이라 대체). 구조 규칙 R = 1/Σ_{c

### S33 ad63532e 40-engine:753
OLD: (정해지지 않았으면), 실행 끝 확인. **E_total 계산 자리를 한 곳으로 정하고 card B가 `find_front`에 둔 `perf.block_index_bound`용 E_total 식(§2.4.5 '상한' 행, card B J-6)을 같은 변경에서 지운다**(검증 N-4). `S3Index` 생성자에 상한 인자를 더하면 `open_run` 서명과 그 호출부 전부도 같은 변경에서 고친다(검증 N-3)). NFR-4 card 2 관찰 지점 계약 유지(
NEW: (정해지지 않았으면), 실행 끝 확인. **E_total 계산 자리를 한 곳으로 정하고 card B가 `find_front`에 둔 `perf.block_index_bound`용 E_total 식(§2.4.5 '상한' 행, card B J-6)을 같은 변경에서 지운다**. `S3Index` 생성자에 상한 인자를 더하면 `open_run` 서명과 그 호출부 전부도 같은 변경에서 고친다). NFR-4 card 2 관찰 지점 계약 유지(§2.4.13 

### S34 ad63532e 40-engine:1162
OLD: - **출발 단계 호출의 결과 자리와 실패 어휘**(검증 M-3 (a)): (m, w_f, 슬라이스 키)와 그 W는 그것을 부른 출발 블록(`start_intervals` -- mismatch slope bin·출발 경계)의 **블록 안 값**이다(정
NEW: - **출발 단계 호출의 결과 자리와 실패 어휘**: (m, w_f, 슬라이스 키)와 그 W는 그것을 부른 출발 블록(`start_intervals` -- mismatch slope bin·출발 경계)의 **블록 안 값**이다(정

### S35 ad63532e 40-engine:1935
OLD: ing.__all__ 공개(Circuit·saturation_window·INPUT_STATUS_MEASURED·INPUT_STATUS_UNMEASURED(INPUT_STATUS_F_COMPONENT_UNDECLARED 삭제, 일곱 이름) -- v1.13.0 둘째 커밋, 검증 S-4; SS_CIRCUIT_WRITER·SS_NODAL_WRITER·ICM_CONFIG_WRITER -- 여섯째 커밋, 재검증 3 S-A) -- 노드 풀이 부분은 block_colum
NEW: ing.__all__ 공개(Circuit·saturation_window·INPUT_STATUS_MEASURED·INPUT_STATUS_UNMEASURED(INPUT_STATUS_F_COMPONENT_UNDECLARED 삭제, 일곱 이름) -- v1.13.0 둘째 커밋; SS_CIRCUIT_WRITER·SS_NODAL_WRITER·ICM_CONFIG_WRITER -- 여섯째 커밋, 재검증 3 S-A) -- 노드 풀이 부분은 block_colum

### S36 ad63532e 42-gap-checklist:331
OLD: | D-WB1 | (card WB-1 범위 3; v1.15.2 정정 -- 검증 C-1·M-1·M-4) DC 블록 `dc_solve`(노드 풀이 + W·`dc_op` + `dc_finger` 쓰기, writer 하나), 쓰기 소자 무반복, 종속 소자 = **키 벡터 전체** 재방
NEW: | D-WB1 | (card WB-1 범위 3; v1.15.2 정정) DC 블록 `dc_solve`(노드 풀이 + W·`dc_op` + `dc_finger` 쓰기, writer 하나), 쓰기 소자 무반복, 종속 소자 = **키 벡터 전체** 재방

### S37 ad63532e 40-engine:1173
OLD: - **슬라이스별 tol 표**(검증 M-3 (b)): tol_V·tol_VDSAT 표(lut CONTRACT 5절)는 슬라이스 키마다 만든다. **만드는 때·주체** = LUT 적재(`load_lut_set`, 로드 1회)가 도달
NEW: - **슬라이스별 tol 표**: tol_V·tol_VDSAT 표(lut CONTRACT 5절)는 슬라이스 키마다 만든다. **만드는 때·주체** = LUT 적재(`load_lut_set`, 로드 1회)가 도달

### S38 ad63532e 41-gain-budget:775
OLD: `computes` 증분 0; `seal_versions(snapshot, calls, None)`·`seal_dc(…, base=None)`·`seal_dc`에서 `base` 생략 → `TypeError`(건너뛰어 pass면 red -- 계획 v6.31 (11)(d), 재검증 G-1) (e) (계획 v6.32 완료 조건 (11)(e), 사용자 결정 O-96 -- card IT-2e, 4.7-3c '실패 평가의 부분 스냅샷 파생') parent가 있는 평가에서
NEW: `computes` 증분 0; `seal_versions(snapshot, calls, None)`·`seal_dc(…, base=None)`·`seal_dc`에서 `base` 생략 → `TypeError`(건너뛰어 pass면 red -- 계획 v6.31 (11)(d)) (e) (계획 v6.32 완료 조건 (11)(e), 사용자 결정 O-96 -- card IT-2e, 4.7-3c '실패 평가의 부분 스냅샷 파생') parent가 있는 평가에서

### S39 ad63532e 41-gain-budget:726
OLD:  B-T16; `seal_versions`도 base None을 받으면 건너뛰지 않고 `TypeError`로 거부하며(SEAL_FAIL이 아니라 호출 오류 -- 필수 키워드 누락과 같은 형태, 재검증 G-1) `if base is not None` 건너뛰기 분기는 삭제 -- 검증 R-2, 계획 v6.31 N3.6 4행)) 끝에 (3) **coverage** '스냅샷의 모든 필드의 `FieldValue.writer` ∈ base writer ∪ {`calls`의 
NEW: s` 필수 키워드 B-T16; `seal_versions`도 base None을 받으면 건너뛰지 않고 `TypeError`로 거부하며(SEAL_FAIL이 아니라 호출 오류 -- 필수 키워드 누락과 같은 형태) `if base is not None` 건너뛰기 분기는 삭제, 계획 v6.31 N3.6 4행)) 끝에 (3) **coverage** '스냅샷의 모든 필드의 `FieldValue.writer` ∈ base writer ∪ {`calls`의 

### S40 ad63532e 40-engine:1222
OLD: | 슬라이스별 tol 표 구성(검증 M-3 (b)) | (가) LUT 적재 때 도달 가능 슬라이스 전부(7) | 블록 순수성 유지 | 적재 1회 | U-87 예외 안 | 첫 실행 ≈ 7~10 분(디스크 캐시 뒤 0) | **채택*
NEW: | 슬라이스별 tol 표 구성 | (가) LUT 적재 때 도달 가능 슬라이스 전부(7) | 블록 순수성 유지 | 적재 1회 | U-87 예외 안 | 첫 실행 ≈ 7~10 분(디스크 캐시 뒤 0) | **채택*

### S41 ad63532e 41-gain-budget:711
OLD: 형식'의 `"unmeasured"`(행 None·감도 특이·`saturation_window` None; 봉인점 tol_V 미정은 그 행이 undefined라서 봉인되지 않아(`sealed=None`) 이 블록이 돌지 않으므로 대상 없음, test 없음 -- 둘째 커밋, 검증 G-1). (마) **우선순위**: 상태가 `"measured"`·`"unmeasured"` 둘뿐이라 대상 없음. 모든 구성(`as_is_single_input` 포함)에서 같다.
NEW: 형식'의 `"unmeasured"`(행 None·감도 특이·`saturation_window` None; 봉인점 tol_V 미정은 그 행이 undefined라서 봉인되지 않아(`sealed=None`) 이 블록이 돌지 않으므로 대상 없음, test 없음 -- 둘째 커밋). (마) **우선순위**: 상태가 `"measured"`·`"unmeasured"` 둘뿐이라 대상 없음. 모든 구성(`as_is_single_input` 포함)에서 같다.

### S42 ad63532e 40-engine:764
OLD:  B J-6) | C | `E/search/find_front.py`에 E_total 계산(`2 *` 변수 수 항·`eval_budget_source` 분기)이 남지 않음 -- card C가 정한 E_total 한 자리만 | card C가 정한 E_total 계산 자리(검증 N-4) |
NEW:  B J-6) | C | `E/search/find_front.py`에 E_total 계산(`2 *` 변수 수 항·`eval_budget_source` 분기)이 남지 않음 -- card C가 정한 E_total 한 자리만 | card C가 정한 E_total 계산 자리 |

### S43 ad63532e 41-gain-budget:776
OLD: 은 tol_V 미정 행이 undefined라서 봉인되지 않아(`sealed=None` -- fail과 다른 상태) 측정 구성 블록이 돌지 않는다, 죽은 갈래라 cfg test 없음; 커널 상태 `"unsettled"`·`tol_v is None`만 단언 -- 둘째 커밋, 검증 G-1, 계획 v6.34.1 (12)(a)와 같은 문언)(`node.dc_window_cfg` 항목 `input_status == "measured"`, 세 metric 값 있음 -- 
NEW: 은 tol_V 미정 행이 undefined라서 봉인되지 않아(`sealed=None` -- fail과 다른 상태) 측정 구성 블록이 돌지 않는다, 죽은 갈래라 cfg test 없음; 커널 상태 `"unsettled"`·`tol_v is None`만 단언 -- 둘째 커밋, 계획 v6.34.1 (12)(a)와 같은 문언)(`node.dc_window_cfg` 항목 `input_status == "measured"`, 세 metric 값 있음 -- 

### S44 ad63532e 41-gain-budget:730
OLD: cuit`(하위 클래스, 같은 패키지)·metrics `icm_config`(`sizing.__all__` 경유, 패키지 밖). 규칙 문언('같은 하위 패키지 2파일')과 다른 점은 이 두 사용자 구성에서 온다. **확인 기록**(셋째 커밋, 오케스트레이터 판단 (가) -- 재검증 N-3): 검사기는 `sizing/__init__.py` 재수출도 사용 파일로 세지만 그것은 실사용이 아니다; 취지 충족 근거는 실사용자 둘(`block_columns`·`icm_con
NEW: cuit`(하위 클래스, 같은 패키지)·metrics `icm_config`(`sizing.__all__` 경유, 패키지 밖). 규칙 문언('같은 하위 패키지 2파일')과 다른 점은 이 두 사용자 구성에서 온다. **확인 기록**(셋째 커밋, 오케스트레이터 판단 (가)): 검사기는 `sizing/__init__.py` 재수출도 사용 파일로 세지만 그것은 실사용이 아니다; 취지 충족 근거는 실사용자 둘(`block_columns`·`icm_con

### S45 ad63532e 41-gain-budget:713
OLD: 기)로 함께 낸다; `len(g_ops) != len(g)`인 `StampSet`은 생성 때 거부한다(`StampSet.__post_init__` `ValueError` -- fail-closed; `g`가 빈 용량 스탬프는 `g_ops` 빈 값 그대로 -- 둘째 커밋, 검증 S-3). 스탬프 식이 바뀌면 개수도 바뀌어야 하므로 스탬프 식 변경을 잡는 test를 둔다(4.7-7 L10 (j)). 1차 상한이다(O(u²) 항 제외; Higham 인용 절·쪽 *
NEW: 기)로 함께 낸다; `len(g_ops) != len(g)`인 `StampSet`은 생성 때 거부한다(`StampSet.__post_init__` `ValueError` -- fail-closed; `g`가 빈 용량 스탬프는 `g_ops` 빈 값 그대로 -- 둘째 커밋). 스탬프 식이 바뀌면 개수도 바뀌어야 하므로 스탬프 식 변경을 잡는 test를 둔다(4.7-7 L10 (j)). 1차 상한이다(O(u²) 항 제외; Higham 인용 절·쪽 *

### S46 ad63532e 41-gain-budget:774
OLD: rix(…, bound=True)` 호출 자리 = `ss_nodal` 하나, E를 만드는 둘째 자리 0(다른 회로·뷰의 G를 조립하는 기존 `conductance_matrix` 소비자 `block_model`·`ff_gm_ratio`는 `bound` 없이 불러 대상 밖 -- 검증 N-4; `git grep`·AST); **봉인점 소신호 회로 필드 `graph.ss_circuit`**(계획 v6.34.1 완료 조건 (10)(c), 다섯째 커밋): writer 1곳
NEW: rix(…, bound=True)` 호출 자리 = `ss_nodal` 하나, E를 만드는 둘째 자리 0(다른 회로·뷰의 G를 조립하는 기존 `conductance_matrix` 소비자 `block_model`·`ff_gm_ratio`는 `bound` 없이 불러 대상 밖; `git grep`·AST); **봉인점 소신호 회로 필드 `graph.ss_circuit`**(계획 v6.34.1 완료 조건 (10)(c), 다섯째 커밋): writer 1곳

### S47 ad63532e 41-gain-budget:723
OLD: 는다), 반환 = base writer ∪ {블록 이름}의 `frozenset`. 'base writer ∪ 블록 이름' 합집합식과 coverage 차집합 꼴의 정의 자리는 이 함수 하나, 그 밖 재구현 0(L11 (e) AST 검사). **AST 검사가 세는 것**(검증 S-3, 계획 N3.3 측정 정의 안의 구현 세부 -- 정의를 넓히지 않는다): 세는 연산 = 합집합·차집합 -- 이항 `|`·`-`, 누적 대입 `|=`·`-=`, set 메서드 `.un
NEW: 는다), 반환 = base writer ∪ {블록 이름}의 `frozenset`. 'base writer ∪ 블록 이름' 합집합식과 coverage 차집합 꼴의 정의 자리는 이 함수 하나, 그 밖 재구현 0(L11 (e) AST 검사). **AST 검사가 세는 것**(계획 N3.3 측정 정의 안의 구현 세부 -- 정의를 넓히지 않는다): 세는 연산 = 합집합·차집합 -- 이항 `|`·`-`, 누적 대입 `|=`·`-=`, set 메서드 `.un

### S48 ad63532e 41-gain-budget:726
OLD:  4 우회 = 기준 약화; 선례 `donors`·`counters` 필수 키워드 B-T16; `seal_versions`도 base None을 받으면 건너뛰지 않고 `TypeError`로 거부하며(SEAL_FAIL이 아니라 호출 오류 -- 필수 키워드 누락과 같은 형태, 재검증 G-1) `if base is not None` 건너뛰기 분기는 삭제 -- 검증 R-2, 계획 v6.31 N3.6 4행)) 끝에 (3) **coverage** '스냅샷의 모든 필드의 `
NEW:  4 우회 = 기준 약화; 선례 `donors`·`counters` 필수 키워드 B-T16; `seal_versions`도 base None을 받으면 건너뛰지 않고 `TypeError`로 거부하며(SEAL_FAIL이 아니라 호출 오류 -- 필수 키워드 누락과 같은 형태) `if base is not None` 건너뛰기 분기는 삭제, 계획 v6.31 N3.6 4행)) 끝에 (3) **coverage** '스냅샷의 모든 필드의 `FieldValue

