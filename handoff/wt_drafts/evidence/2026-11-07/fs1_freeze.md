verdict: Major 5

# FS-1 (20261107-fs1) 순서 3 동결 판정 -- 판정자 독립 측정

- 대상: audit worktree `C:/Users/HSLEE/Documents/Todoc/fpga/wt/20261107-fs1-audit` (브랜치 role/audit/20261107-fs1), T = `23c81fe13df6ba23aa15c5a03b84c26767a1b973` (tree `7358924e`), base = master `2cb26c92` + card `a7019b22` + interface 보정 `a0bf0903` + test 커밋 13개. base..T 17 커밋, 67 파일 +2548 −1262, tests 밖 경로 = docs/02-design 4파일뿐(엔진 코드 변경 0 -- 실측 `git diff --name-only`).
- 격리: `git -c core.longpaths=true clone --no-hardlinks --no-local <audit wt> C:/fzf1/iso` + `remote remove origin`. 모든 실행은 복제본 안 (cwd = `gmid_engine/tests`, `C:/Python314/python.exe -m pytest -p no:cacheprovider`, OPENBLAS_NUM_THREADS=1, PYTHONIOENCODING=utf-8, GMID_LUT_TABLE_CACHE_DIR=C:/fzf1/lutcache, 실행 스크립트 `C:/fzf1/run.sh`). 출력 = `C:/fzf1/out/*.txt|*.xml`, 분류 스크립트 `C:/fzf1/classify.py`·`junit_cls.py`.
- 작성자 보고는 증거로 쓰지 않았다. 아래 수치는 모두 이 복제본에서 잰 값이다.

## 돌린 범위와 결과 (base = 코드 없음 상태의 T)

| 묶음 | 결과 | 분류 |
|---|---|---|
| (a) `tests/structure` 전체 | 8 failed / 198 passed / 1 deselected (174 s) | 8건 전부 코드 없음: `test_fs1_source.py` G-1·G-2a·G-2b·G-2c·G-3·G-4·G-5, `test_wb1_source.py::test_wb1_slice_functions_defined_once`(옛 `finger_slice` 정의 있음) |
| (c) 전체 `--collect-only` | 11270/11299 수집(29 deselected), 수집 오류 3 | 3모듈 전부 코드 없음 ImportError: `search/test_l_bin_search.py`(polish_cells), `search/test_start_intervals.py`(initial_wf), `sizing/test_realize_fingers.py`(DeclaredRatio) |
| (b1) lut 4 + sizing 14 변경 파일 | 322 failed / 264 passed / 3 errors | **test 결함 289**(`'LutAccess' object has no attribute 'spec'` 286 + 같은 원인 subprocess 2 + 래퍼 `AttributeError: base` 1), 코드 없음 36 |
| (b2) search 변경 19 파일(test_iv_matching_l 제외) | 119 failed / 107 passed / 13 errors / 1 deselected (524 s) | 코드 없음 98, **test 결함 31**(LutAccess 22, 단계 A/B 불통과·CDD 열 7, S1 전제 모순 2), 원인 미확정 3 |
| (b3) metrics 5 + convergence 2 변경 파일 | 85 failed / 55 passed | **test 결함 35**(LutAccess), 코드 없음 50(FingerGeom 서명 34, WfCell 16) |
| (b4) integration/test_layer0_boundary_rows.py | 1 failed / 11 passed / 2 xfailed | 코드 없음 1(WfCell ImportError -- 단 코드 뒤에는 아래 M-1 경로로 다시 실패할 자리) |

**안 돌린 범위(통과로 세지 않음)**: `search/test_iv_matching_l.py`(M 묶음, 지시로 제외 -- M-1·M-2 실행 0), search 디렉터리 전체, generality 3파일(첫 실행 2회 모두 내 pytest 가 메모리 1 GB 아래로 내려가 PID 정지 -- 결과 없음), `integration/test_s0_layer_9circuits.py`(한 test 당 수 분, 진행 중 정지 -- 결과 없음), 2회로 연기(stage_b·s0·g10 `--run-slow -k`), `search/test_canonical_order.py`, slow 표지 test, 미측정 회로(`circuit_zl`·`circuit_cmfb_diff`·`tied_cs2` 등 build_case 호출 회로 전부 -- 통과 확인 없음). sizing/conftest `run_blocks` 를 쓰는 비변경 파일(`test_scc_newton`·`test_seal_tolerances`·`test_seal_versions`·`test_seal_writers` 등)도 안 돌렸다.

## Major

**M-1 (test 결함, 계통 -- 2번 범위 test 실패 원인이 test)**: 손 wf helper 가 커널 컨텍스트의 `LutAccess` 에 LUT 집합 함수를 부른다.
- `tests/fs1_wf.py:16` `widths(ctx.lut, ...)`, `tests/search/conftest.py` `hand_wf_of` `widths(sctx.dc.lut, ...)`, `search/test_start_intervals.py` S-B1·S-B5 `widths(case.kctx.lut, ...)`, `search/test_iv_matching_l.py` M-1 P4·M-2 `case.kctx.lut.spec.manufacturing_grid_m`·`widths(case.kctx.lut, ...)`.
- 사실: `build_kernel_context` 는 `lut` 가 `LutAccess` 가 아니면 TypeError(`sizing/kernel_context.py:59`), `LutAccess` 칸은 `memo` 하나뿐(`sizing/s2_values.py:237-244`), `widths` 는 `lut.spec`·`lut.slice_map` 을 읽는다(`lut/widths.py:15-18`). interface 는 `LutAccess` 에 칸을 더하지 않는다(spec W11 = 독스트링만, `widths` 변경 0).
- 결과: base 실측 test 결함 실패 289 + 22 + 35 = **346건**(위 표). 코드가 들어와도 그대로 실패한다. 또 `search/conftest.hand_wf_of` 는 `WfCell` import 가 `widths` 호출보다 앞이라 base 에서는 코드 없음(ImportError)으로 보이는 search 실패 약 72건 + integration 1건이 코드 뒤에 같은 결함으로 다시 실패한다(예측).
- 같은 묶음: `fs1_wf.size_and_seal` 래퍼가 엔진보다 먼저 `ctx.base` 를 읽어 `sizing/test_size_and_seal.py::test_type_error_ctx` 가 TypeError 대신 `AttributeError: base` 로 실패한다(코드와 무관, 기대 TypeError 단언이 래퍼 때문에 깨짐).
- 고칠 자리(test 쪽): `ctx.lut.memo.lut`(또는 toy `lut`) 로 부르고, 래퍼는 ctx 검사 전에 ctx 를 읽지 않게(또는 그 test 만 공개 `size_and_seal` 직접).
- 재현: `bash C:/fzf1/run.sh one -x -q --tb=short sizing/test_seal.py` (traceback `fs1_wf.py:16 -> lut/widths.py:15`).

**M-2 (test 결함 -- A-188 정본 경로 변경의 결과가 측정·기록되지 않음)**: `build_case`·`bins_case` 가 단계 A·B 를 거치게 바뀐 뒤 코드 없음으로 설명되지 않는 실패가 있다(RETIRED 기록 없음).
- 단계 A 정지 `stage_a_stopped` 3: `test_find_front.py::test_cm_unconstrained_warning_reaches_run_notes_i22`·`test_cm_constrained_circuit_has_no_warning_note`·`test_eval_result_warnings_equal_ss_evaluate_i22`.
- 단계 B 거부가 test 가 보려던 거부보다 앞에서 AssertionError 로 바뀜 2: `test_search_context.py::test_theta_resistance_without_bounds_rejected_before_kernel`(`theta_resistance_bounds_undeclared`), `..._capacitance_...`(`theta_capacitance_bounds_undeclared`).
- toy LUT 에 CDD 열이 없어 단계 B 실패(`lut_column_unavailable` CDD, `write_r4_bins_lut(jc1_cols=False)` 기본) 2: `test_kernel.py::test_e2_...`·`test_e3_...` (FS-1 새 test E-2·E-3). 같은 helper 를 쓰는 E-4 와 같은 LUT 꼴을 쓰는 N-1·N-2·N-4 는 수집 오류·ImportError 로 가려져 미측정(같은 실패 예상).
- S1 수준 전제가 정본 경로와 모순 2: `test_search_context.py::test_noise_decl_without_s1v`(기대 `input_cells=()`, 실측 `(('M1',),)`), `test_u7_context_inputs_default`(기대 `structure is None`, 실측 MetricStructure 있음).
- 원인 미확정(코드 없음으로 설명되는지 확인 못 함) 3: `test_find_front.py::test_passive_theta_circuit_front_measured`·`test_unmeasured_points_never_in_final_front`, `test_search_context.py::test_eval_results_identical_search_memo_vs_caller_memo` -- base 에서 front 가 빈 tuple.
- A-188 규칙(통과 못 하는 legacy = RETIRED + 기록, 절반 넘으면 멈춤)대로라면 위 test 는 RETIRED 기록이나 수정이 있어야 하는데 둘 다 없다. E-2·E-3 은 이 card 의 새 test 라 legacy 삭제 대상도 아니다.

**M-3 (interface §9 위반 -- 범위 위반)**: §9 '통과 spy 만, 동작 대체 금지, 그 밖 엔진 내부 이름 접근 0'.
- O-2 `test_find_front.py::test_o2_...`: `monkeypatch.setattr(find_front, "initial_wf", lambda snapshot: None)` -- 관찰 지점 목록 밖 이름을 동작 대체. 또 코드가 `find_front` 모듈 전역 이름 `initial_wf` 를 갖도록 강제한다(interface 밖 구조 요구; base 실측 `AttributeError: ... has no attribute 'initial_wf'`). interface O-2 는 'wf_start 에 None 칸이 있는 sctx' 입력이다.
- O-3 `test_realize_front.py::test_realize_o3_...`: `realize_front.evaluate` 를 강제 실패(`reason: fs1_test_forced_failure`)로 바꿔 lost 를 만든다 -- 관찰 지점 밖 동작 대체, interface O-3 은 '실현에서 잃는 점이 있는 기존 toy(r4 꼴)'.
- 고칠 길: None 칸 스냅샷(tamper helper 또는 S-B4 꼴)으로 만든 sctx, 실제로 잃는 toy. 또는 오케스트레이터가 §9 에 관찰 지점을 더하는 card 보정(dispute).

**M-4 (test·card 결함, 정적 판정 -- 미실행)**: `search/test_iv_matching_l.py::test_m2_evaluation_sigma_rows_use_the_evaluation_cell_key_not_reference_width` 는 평가 σ 행 호출을 `iv_matching_l.mismatch_sigma_vgs` spy 로 잡는다. 평가 σ 경로는 `metrics/metrics_aux.py:34 -> metrics/device_sigma.py:10·:20`(`from gmid_engine.lut import ... mismatch_sigma_vgs` 를 자기 모듈 이름으로 부름)이고 `iv_matching_l` 은 `search/start_intervals.py:52` 만 import 한다(실측 grep). 그래서 spy 호출 0 -> '관찰 지점 호출 0 -- 멈추고 보고' 단언으로 코드와 무관하게 실패한다. interface §9 가 M-2 후반에도 이 관찰 지점을 적은 것이 원인일 수 있다 -- 스냅샷 σ 행(또는 §9 에 `metrics.device_sigma.mismatch_sigma_vgs` 추가)으로 바꾸는 card 보정이 필요(dispute). M-1 의 `case.kctx.lut.spec` 결함도 같은 test 에 있다.

**M-5 (기준 약화 의심 -- 사용자 결정 필요, O-229 5 위임 밖)**: interface §4.3 은 실현 평가의 '재풀이·봉인·측정 구성·피벗 갈래·전력 축 = 기존 그대로', §4.4 는 레이아웃 뒤 평가를 유지한다. A-186 추가 삭제는 그 유지되는 성질을 단언하던 물리·fail-closed test 를 지웠다:
- `search/test_realize_front.py` R-2(입력 차 이동 닫힌 식), R-5, R-6(피벗 입력 유지), R-6 입력 고정 갈래 KCL 재풀이·재봉인 2 case, **R-6c(레일 안 근 없음 -> lost, fail-closed)**, R-15(실현 점 출력 넷 KCL 항등식), R-16 2 case(전력 = 실현 채널 전류의 레일 전류), S3-6 2개;
- `convergence/test_realized_geometry.py` R-13a·R-13b(레이아웃 뒤 고정점 닫힌 식), L-2 2개.
- 삭제 사유 '같은 입력을 만들 수 없음'은 옛 tamper 구성에만 맞다. 성질 자체는 새 경로에서 만들 수 있다: 실현 m 은 손 oracle(`realize_fingers` 정의, D-5 와 같은 방식)로 미리 정해지고, W < w_f 이면 m = 1 이라 큰 잔차(R-6c 의 r = 2 꼴)도 θ·칸 키 선택으로 만든다. 레이아웃 뒤는 요청 행 + 기준(실현) 스냅샷으로 D-7 꼴 입력이 있다.
- RETIRED 는 '덮이지 않게 된 것'을 LA-1 재점검 입력으로 기록했다(기록은 맞다). 그러나 바로 이 DC 블록을 다시 쓰는 card 에서 물리 정합·fail-closed 회귀망을 비우는 것은 O-229 1(완화 금지)·원칙 18(기준 약화 = 사용자 승인)에 걸린다. 선택지: (가) code 전에 손 oracle m 으로 위 성질 test 를 다시 쓴다(권고) (나) 사용자 승인으로 삭제 유지.
- R-8(탐색 dc_finger 행 없음 사유), R-12(C-3 이 덮음), R-10 tampered(O-1 대체), r3(D-5·D-6 대체)의 삭제는 대상 소멸로 타당하다.

## minor (LA-1 재점검 입력으로)

- m-1 `hand_wf(join=)`(D-2·D-5·D-7·D-8): interface toy D 문언은 '묶음 없으면 소자마다 칸'인데 `mirror_setup` 의 `matching_groups` 가 비어 있어 M1·M2 를 손으로 묶었다. M1(nb,nb,gnd)·M2(out,nb,gnd) 는 gate·source·bulk 가 같은 거울 쌍(`sizing/conftest.py:1019-1027`)이라 물리 정합은 맞고, 기대값은 손 식(D-5 = `hand_oracle`)이며 `WfInput` 은 평가 입력이다. 그러나 interface 전제('그 toy 에 정합 묶음이 있다')가 실측과 달라 '멈추고 보고' 대상이었다 -- 사실을 card 보정 메모로 남길 것.
- m-2 `fs1_wf` '가장 좁은 후보' 기본 키는 interface 가 정하지 않은 test 입력 선택이다. 다중 슬라이스 LUT 를 쓰는 옛 test 의 기대값이 코드 뒤 이 선택 때문에 달라질 수 있다(지금은 M-1 에 가려 측정 불가).
- m-3 G-2(a) `git show f42a13f8` 런타임 스캔: interface '적은 목록' 대신 같은 AST 규칙으로 base 를 훑는다. `check=True` 라 git·커밋이 없으면 실패(fail-closed). `f42a13f8..2cb26c92` 사이 엔진에 `matching_groups` READS 변화 0(실측 diff grep) -- 범위 안으로 본다.
- m-4 StartConflict `c.bounds` 출처 해석 = `((출처, 값), ...)`(`search/start_values.py:68` 독스트링·CONTRACT 형식) -- 맞다. 단 M-1 실행 A 는 충돌 device 집합 ⊇ 입력 소자 둘을 단언하는데 충돌 device 가 'L 동치류 주인'이면 둘째 소자가 빠질 수 있다(미측정 위험).
- m-5 D-5 spy 가 `realize_fingers` 호출 꼴을 위치 인자·키워드 0 으로 단언(`a[2] == ()`, `k == {}`) -- interface 보다 좁은 호출 꼴 요구.
- m-6 `structure/test_wb1_source.py` 주석이 없는 test 이름 `test_fs1_removed_names_absent_in_engine_sources` 를 가리킨다(실제 = `test_g3_removed_names_zero_in_engine_sources`).
- m-7 필드 부재 fail-closed: test 가 None 으로 넘기는 자리는 없다(확인). 그러나 'wf_start 없는 스냅샷 -> 조회 오류'를 직접 단언하는 test 는 없다(interface 요구 아님 -- 기록).
- m-8 N-1 전제 'L 이동 수락 0' 을 단언하지 않는다(수락되면 바퀴 순서 단언이 흔들릴 수 있음).
- m-9 S-B6 미작성(A-186): 운영 경로에서 `no_member_density` 기록이 남는 것은 덮이지 않는다. 시도 toy 목록은 작성자 측정(agent 인용, 판정자 재측정 안 함). 기록은 RETIRED 에 있다(조용한 skip 아님).
- m-10 `test_cell_floor.py` 7 항목 삭제(circuit_diode 단계 A 정지 `unsupported_rule_branch|cs_output_low_impedance`): 사유 'stage 미통과' 타당, 덮이지 않는 범위 기록 있음.

## 판정 항목별

1. **interface 만으로 썼는가**: 새 test 기대값 출처 = 손 식(`test_realize_fingers.hand_oracle` = §1 1~4 그대로, E1·E2 같은 꼴 `==`), toy 선언 닫힌 식(`r4_ln_idu`), LUT npz·PDK 원 파일(`search/fs1_hand_sigma.py` -- import = numpy·표준 라이브러리만, sha256 대조, bin 규칙 evidence 대조). 피검 함수로 만든 기대값 0. `widths` 는 입력 선택·interface 가 적은 전제(C-1′, S-B1 '∈ widths')에만 쓰였다. 엔진 소스 grep 열람의 흔적: 기대값에서 interface·CONTRACT 밖 값 0(`dc_coord.role/partner` = sizing CONTRACT :240, `StartConflict.bounds` = start_values 형식). 다만 O-2 의 `find_front.initial_wf` 이름 가정은 interface 밖(M-3).
2. **toy 82개 대응**: §1 18행 + R-E5·R-T(5)·R-V(3)·R-K(4)·R-E, §2 C-1·C-1′·C-2·C-3, §3 S-1~S-10·W-1~W-4·K-1~K-4·M-1·M-2·S-B1~S-B5, §4 D-0~D-8·E-1~E-5, §5 N-1~N-5, §6 O-1~O-4, §7 G-1~G-5·G-7 있음. 없음 = S-B6(A-186 결정, interface '서지 않으면 멈추고 보고' -- 보고·결정 경로를 거쳤다), G-6(기존 test 그대로 -- 새 test 불요). M-2 후반(A-186) = M-4 결함. G-7 = 새 프로세스 2회 PYTHONHASHSEED 1·2, float.hex 비교 -- interface 대로. M-1 (b) 전제 기록: two_stage_ota 입력 M1·M2 = nmos(gate vin_n·vin_p, topology 실측), mismatch npz `L` 축 18개에 4e-6·8e-6 있음·`w_ref_m` = 5e-6(실측 `C:/fzf1/out/m1_premise.txt`) -- RETIRED 의 '(b) 유지' 기록은 정적 사실로 맞다. 실행 시 앵커가 8 µm 에 닿는지는 test 가 단언(미실행).
3. **기준 약화**: M-5. 남긴 test 의 단언 diff: R-1 은 `residual == 0.0`·`w_key == round(w_f_m/GRID)` 를 지우고 `type(m) is int`·`W == m·w_key·GRID` 로 바꿨다(새 정의로 정당 -- O-1 이 residual 값을 본다). `test_converge_point` 레이아웃 입력 nf = `max(1, round(탐색 m))`(입력 선택, 기대값 아님). 그 밖 수정 파일의 지운 assert 줄은 이름·서명 맞춤뿐(실측 diff).
4. **새 래퍼**: `fs1_wf`·`hand_wf_of` 의 키 선택·`hand_wf(join=)` = 입력 선택으로 범위 안(m-1·m-2)이나 구현이 M-1 결함. StartConflict 해석 = 맞음(m-4). G-2(a) = 범위 안(m-3). `build_case`·`bins_case` = 단계 A -> 단계 B -> `build_kernel_context(b.s1, ...)` 하나, 끄는 인자 0, 단계 B·출발 레코드 부재면 AssertionError(정본 경로 맞음) -- 그 결과는 M-2.
5. **base red 분류**: 위 표. 코드 없음으로 설명되지 않는 것 = M-1(346 실측) + M-2(7 + 2 + 미확정 3).
6. **graph 정본·fail-closed 단언**: `wf_start` writer = `start_intervals` 하나(G-1, `test_s0_fields` START_FIELDS), `dc_finger` writer = `dc_solve` 하나(G-1 `S2_WRITERS.writer_of`), 폐포 구현 하나(G-2 a·b·c), 옛 이름 0(G-3·G-4), `realize_fingers` 순수(G-5), `dc_solve` wf 누락 TypeError(`test_dc_solve_wf_is_required_keyword`), `size_and_seal` wf 누락 TypeError(D-4), `WfInput` 길이·int 검사 ValueError, 칸 멤버 조회 불능 = 다른 슬라이스로 피하지 않음(D-8). 필드 부재 직접 단언 없음(m-7).

## code 착수 가능 여부

**불가.** M-1~M-4 는 test 쪽 수정(또는 M-3·M-4 는 card §9 보정 dispute) 뒤 재판정, M-5 는 다시 쓰기(권고) 또는 사용자 승인이 필요하다. 재판정 범위 = 고친 test 파일 + M-1 영향 파일 base 재실행.
