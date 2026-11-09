verdict: Major 3

# JC-1 (card 20261106-jc1) test 순서 3 동결 판정

- 대상: test 브랜치 `role/test/20261106-jc1` 머리 `6d1d6fd57a5cbafd267e34c19b7dd8ee63ba17e8` (앞 `9c7db95010fe2770f29b6007d16713d181b61e6d`), base `da4f53665a839ab1bed6895279614140fdc4a9ed`(= master faf69218 + card 4b369d4d). base→T: 2 커밋, 33 파일 +1340 -1162, 전부 `gmid_engine/tests/` 아래(경로 밖 0). 트레일러 `Role: test`, `Change-Id: 20261106-jc1` 둘 다.
- audit worktree: `C:/Users/HSLEE/Documents/Todoc/fpga/wt/20261107-jc1-audit` (브랜치 `role/audit/20261106-jc1`). 모든 실행은 격리 복제본(`--no-hardlinks --no-local`, origin 제거) `C:/Users/HSLEE/AppData/Local/Temp/jc1_fz/iso`. pre-existing red 확인용 `.../base`(detach da4f5366).
- 환경: cwd = `gmid_engine/tests`, `-p no:cacheprovider`, OPENBLAS_NUM_THREADS=1, PYTHONIOENCODING=utf-8, U-87 전용 폴더. O-229 범위만(ngspice 0, 2회로 연기 안 돌림, `--run-slow` 없음).
- 작성자 보고는 증거로 쓰지 않았다. 모든 수치는 위 복제본에서 직접 쟀다.

## 결론

Major 3건 -> **동결 불가(수정 필요)**. 아래 M1~M3을 test 작성 주체가 고친 뒤 그 부분만 재판정한다. 나머지는 동결 가능 판단이고 기록 사항(m1~m6)은 LA-1 재점검 입력이다.

## Major

### M1 -- 낡은 접합 경로 test 미폐기 (test 결함, 범위 위반)
- 대상: `tests/convergence/test_realized_geometry.py::test_layout_resolve_l2_waiting_device_row_erased_in_junction_input_is_realized_finger_missing`(:225).
- 이 test 는 `kernel.ss_evaluate` 로 넘어가는 봉인 스냅샷에서 요청 대기 소자 M2 의 `dc_finger` 행을 지워 `realized_finger_missing` 이 나오기를 기대한다. 그 정지 자리는 옛 `ss_linearize._finger_row` 하나였다(기준 엔진 `metrics/ss_linearize.py:93`, :106 `fingers = ... "dc_finger"`).
- card(spec 범위 1·W5, interface §3)는 `ss_dev` READS 에서 `dc_finger` 를 빼고 `_finger_row` 를 삭제한다. 그러면 지운 행을 읽는 곳이 `ss_evaluate` 안에 없다: 엔진 비test 소스 중 `dc_finger` 를 읽는 곳은 `metrics/ss_linearize.py`(삭제 대상), `search/realize_front.py:53`(실현 뒤 후처리), `sizing/block_dc.py`(`dc_solve`, tamper 이전 단계)뿐이다. code 뒤 이 test 는 정지가 없어 `out.failure is not None` 에서 red 가 된다(정적 분석 -- 지금은 base 엔진이 같은 `pdk_quantity_undeclared` 로 먼저 깨져 가려진다).
- `tests/RETIRED_TESTS_jc1.md` 에도 없다(소자 접합 입력 `dc_finger` 경로 전부 폐기라 적었으나 이 파일의 이 test 는 목록에 없다). 동결 뒤 code 가 고치거나 지울 수 없는 test 라서 지금 처리해야 한다.
- 요구: 폐기(RETIRED 표에 사유·`covered_by` = D-a2/G-3 로 기록). 참고: 같은 파일 :210 `..._device_without_input_finger_row_is_realized_finger_missing` 은 아래 '판정 대기 2' 대로 유지.

### M2 -- 유지로 표기한 test 의 단언 삭제 (기준 약화)
- 대상: `tests/metrics/test_junction_cap.py::test_from_lut_rule_sky130`. RETIRED 표는 '폐기 아님 -- 유지'라 적었는데, 옛 판에 있던 sky130 규칙 절대값 단언 두 줄이 사라졌다.
  - 삭제: `assert rel_close(g.ad_m2, 1e-12, 1e-12) and rel_close(g.as_m2, 1e-12, 1e-12)`, `assert rel_close(g.pd_m, 4e-6, 1e-12) and rel_close(g.ps_m, 4e-6, 1e-12)`.
  - 남은 단언은 `g.ad_m2 == rule.value(...) * 2e-6` 꼴(선언에서 읽은 값과 같음)뿐이라 sky130 선언 파일이 바뀌어도 통과한다. 이 card 는 `DiffusionGeometry.from_lut_rule`·sky130 규칙 선언을 바꾸지 않는다(범위 밖 변경, 삭제 사유 없음).
- AST 도구(`scratchpad/weak.py`)로 기존 test 함수의 단언 수 감소를 훑어 5건이 나왔고, 4건은 카드/RETIRED 가 허용한 이유(`test_lut_parameters_constant` 교체 R-a, 접합 온도 값·`params` 변형 case 삭제, `test_missing_lut_temperature_rejected` 전제 줄)이며 이 1건만 근거가 없다.
- 요구: 두 줄 복원(값은 옛 판 그대로).

### M3 -- D-b 가 card 의 toy C 가 아니다 (card 문언 이탈, 변별력 약화)
- 대상: `tests/metrics/test_ss_linearize.py::test_vgs_min_db_declared_width_device_uses_declared_width_and_declared_point`.
- interface §3 D-b: `off` 선언 소자 M2(nmos, `w_m` = 2e-6, `l_m` = 2e-6, `off_op` vds = 1.0, vsb = 0.5), 기대 cdb = (CDD − CGD)**[1,0,1,1]**·((a·2e-6·1.0)/(a·1e-6·1.0)) -- toy C 격자 마디 값, 비트 동일.
- test 는 `sizing/wb1_toy.write_r4_bins_lut(jc1_cols=True)` 의 **모든 점 같은 상수 열**(JC1_CDD−JC1_CGD = 3e-16, JC1_CSS−JC1_CGS = 5e-16)을 쓰고 `rel_close(.., 1e-12)` 로 비교한다. docstring 에 '상수 열이라 점 무관'이라 적혀 있어 이름이 말하는 `declared_point`(off_op 의 vds·vsb, 선언 l_m)가 실제로는 단언되지 않는다: 엔진이 다른 점(dc_op·다른 L·vsb)을 조회해도 통과한다.
- card 는 '미측정 사실이 기대와 다르면 멈추고 보고'를 요구했다. 멈춤 보고가 없다.
- 요구: 점 의존 열(toy C 의 마디 값 또는 점에 따라 달라지는 합성 열)을 가진 LUT 로 `off` 소자를 만들어 마디 값을 비트로 단언하거나, 그게 불가능하면 불가능한 사실을 보고하고 완료 조건 (1)(b) 의 점 단언을 별도 test 로 둘 방법을 합의한다.

## 항목별 판정

### 1. 기준 약화 없음
| 점검 | 결과 |
|---|---|
| 지운 test 44개 대 RETIRED 표 | 44개 전부 표의 폐기 행·교체 행에 대응. 표에 이름이 없는 것 2개(`test_junction_source.py::test_temperature_comes_from_lut_cap_conditions`, `::test_pre_layout_geometry`)는 같은 파일의 `test_junction_temperature_follows_lut_not_a_constant`·`test_junction_pre_layout_geometry_is_rule_geometry` 로 교체되었고 covered_by 에는 새 이름이 적혀 있다 -> 기록만(m1). 지운 test 중 BSIM4 식·ngspice 대조·온도 보정·PDK 접합 54키 test 는 정의 교체로 전제가 깨진 것. |
| `test_r3_per_mos_share` P = 12 -> 15 | 입력 확인(`len(exp) == 15`: M1 8열 모두 ≠ 0 + M2 7열(csb = 0))이 `test_all_eight_parameters...` 에 단언으로 서 있고(base 에서 `tuple(ps.params) == exp` 가 red), 주석·RETIRED 에 근거 기록(요청 'P = 15 근거 기록' 충족). 허용오차 식 `(P − 1)·EPS·...` 은 그대로. 항 수가 늘면 허용이 커지는 구조라 숫자 느슨함은 수가 늘어난 만큼(11 -> 14 eps)이다 -> 약화 아님. |
| 6열 한정 `delta == eps·|p|` | `test_all_eight_parameters...` 에서 `old = [i for ... nm in LUT_P_OLD]` 원소만 `delta == eps[k]·|p|` 로 단언(카드 §8 의 '기존 6열 원소로만 한정'과 같다), cdb·csb 원소는 존재·유한·≥ 0 만. `test_epsilon_zero_and_none` 의 `delta == 0`/`> 0` 단언도 6열 한정(카드 허용 범위). 6열 delta 의 ε·|p| 는 이 파일이 여전히 단언하므로 `test_resolution.py::_expected_lut` 가 `ps.delta` 를 입력으로 읽어도(카드 §8 허용) 6열 정의 검증이 빠지지 않는다. |
| E-18 거부 test `cdd=False` | `search/test_iv_currents.py`·`search/test_macro_poles.py` 가 `toy_case(..., cdd=False)`(u13_hand)로 CDD 열 없는 표를 계속 쓴다. u13_hand 는 CGS·CSS 를 더하고 CDD 만 뺐으므로 거부 사유는 CDD 열 하나뿐(단언 `reason == "lut_column_unavailable"`, `column == "CDD"` 불변). `gb4_hand.write_lut`·`sizing/conftest.write_r4_lut` 의 `cdd` 기본값 False -> True 는 ss_dev 가 CDD 열을 요구하게 되는 데 따른 것이고, `cdd=False` 로 E-18 거부를 쓰는 호출자는 위 두 test 외에 없음(`cdd=` grep 전수). 감시 항목 w1: code 뒤 E-18 시작 경로 정지가 `ss_dev` 의 `lut_query_failed` 감쌈보다 앞에 오지 않으면 이 두 test 가 사유 문자열 때문에 red 가 된다(지금 못 잰다). |
| 생성기 보강 값 | CGS = CGG − CGD = 8e-16(기존 용량 모형 `cgg_minus_cgd_at_gs` 값 그대로), CSS − CGS = 5e-16, 기준 표 CDD: u13_hand·`write_r4_lut`·gb4_hand = CGD 와 같은 값이라 cdb = 0.0 정확히(수동성 관문 `>= 0` 경계, 통과), wb1 계열 = 5e-16 > CGD 2e-16. 기존 닫힌 식 기대값(매크로 극점 등)이 그대로 서도록 고른 값이고 기대값 리터럴 변경은 없다. cdb = 0 인 흐름에서는 접합 항 변별력이 없다 -> 기록(m2). |
| 피검 함수로 기대값 | 없음. `test_real_junction_caps_from_realized_diffusion` 의 `resolve_lut_location` 은 엔진 함수지만 값이 아니라 npz **파일 경로**만 얻는 용도이고(피검 대상은 `ss_dev`·접합), `interp4`·`axis_cell` 은 `tests/lut/conftest.py` 안 test helper(독립 다중선형 구현). `jc1_toy`·`oracle_junction` 은 `lut_cap_closed`(닫힌 식)·손 식만 사용. 접합 기대에서 `junction_at_vgs_min`·`from_decls`·`from_lut_rule`(기대 생산)·`lut_parameters`(기대 생산) 호출 없음. `from_lut_rule`·`lut_parameters` 는 피검 대상으로만 나온다. |
| 공통 ε_d 꼴 | 없음. 새 기대에 `(gm/ID)·tol_V` 꼴 0, cdb·csb Δ 를 ε·|p| 로 만드는 단언 0, 완료 (10)은 R-a(AST)·R-b(Resolution.lut B₈ > B₆, 전제 단언 뒤)·R-c(문서 grep) 구조 단언뿐. |

### 2. card toy id 전수 대응 (45 id)
| 묶음 | id | 파일::test | 판정 |
|---|---|---|---|
| T-J | C-0, J-1~J-12 | `metrics/test_junction_cap.py`: `test_junction_c0_..`, `j1_..`, `j2_..`, `j3_j5_..`(3 case), `j6_j7_..`(2), `j8_j10_..`(3), `test_vgs_min_j11_..`, `j12_..` | 전부 있음, 문언대로(비트 동일 `==`, spy 인자 VGS == 0.25 ≠ 0·W == reference.finger_w_m, d 먼저). 음성 대조 `test_junction_negative_check_clean_table_does_not_stop` 추가. |
| T-S | S-1~S-4 | `test_junction_source.py` s1·s2_s3(3 case)·`test_junction_field.py` s4 | 있음. S-2/S-3 전제(core 가 0 을 받아들임) 포함. S-1 은 kind 1개(nmos) toy 만 -> kind 정렬은 2회로 연기 파일이 덮는다(m3). |
| T-D | D-0, D-a, D-a2(2), D-b, D-c, D-d, D-e(3), D-f, D-g | `test_ss_linearize.py` d0·da·da2·db·dc·de·df_dg, `test_ss_evaluate.py::test_jc1_df_dg_...` | D-b 제외 문언대로(D-a: dc_finger (2, 1.7e-6)·m·w_f 값과 다름 단언, D-f: ss_dev 직접 + ss_evaluate 경유 + `ss_circuit_field` spy 미도달 + 양성 대조). D-d 는 card 가 D-a 갈음 허용. **D-b = M3**. |
| T-G | G-1~G-5 | `test_ss_linearize.py` `test_block_declaration`·g2·g3·g4·g5 | 있음 (G-2 는 LUT memo `point` 영역 miss 증분으로 단언, `stats()` 는 기존 공개 칸). |
| T-X | X-0, X-1~X-7 | `lut/test_lut_set.py` `test_axis_key_missing_vgs_is_classified_stop`(X-1~X-6 parametrize, X-0 는 같은 toy 의 키 안 뺀 `load` 선행) + `..._first_listed_axis_wins` + `..._x7_...` | 있음. rm2(X 블록 범위 표지) 충족: 블록 주석에 '원래 취지와 다름 위임 A-158 rm2 ... 판정자 확인 항목' 명시. |
| T-R | R-a, R-b, R-c | `test_lut_parameters.py` ra·rb·rc | 있음. rm1 충족: R-b 가 B₈ > B₆ 비교 앞에 독립 MNA 중심 차분으로 cdb·csb 의 ugf·gbw·PM 감도 ≠ 0 을 단언(내가 따로 재현: Miller 변형, cdb ±1e-6 상대 섭동에서 PM 70.81583969524 / 70.81583979139, csb 70.81583974436 / 70.81583974226 -- 모두 `!=` 성립, csb 쪽은 1e-9° 수준으로 약해 m4 로 기록). |
| T-N | N-1, N-2, N-3 | `structure/test_removed_names.py` n1·n2(+ 변별 9 case), `core/test_pdk_decl.py::test_jc1_n3_...` | 있음. N-1 정규식이 card 와 같다(`\|` 표 이스케이프 해제 후 동일). |
- 이름 규칙: 새 test 접두 `test_jc1_`·`test_junction_`·`test_axis_key_`·`test_vgs_min_` 준수, 금지어(`off` 시작·`test_ic`·`ic1/ic2/ic9/ic10/rule_g/rule_k_/g10`) 0.
- 영향 test: 목록 밖 기대 변경 없음(diff 33 파일이 전부 card §8 표 안). 단 §8 표에 없는 파일 `search/test_cell_floor.py`·`test_current_box.py`·`test_kernel.py`·`test_search_domain.py`·`sizing/test_block_dc.py`·`sizing/wb1_toy.py` 의 변경은 toy LUT 생성기에 CGS·CSS·CDD 열 추가뿐(기대 불변) -> 열 의존 때문에 필요한 서명 맞춤으로 판단.

### 3. base red 재현과 분류
base = 엔진 da4f5366 + test 6d1d6fd5, 엔진 diff 0. 돌린 범위: metrics / search / sizing / convergence / core / generality / structure / `lut/test_lut_set.py` 전체 + `integration/test_s0_layer_9circuits.py` 의 junction_source_content 1건(common_gate_amplifier). ngspice 0, slow 없음. 안 돌린 것(통과로 세지 않음): 2회로 연기 3파일, integration 나머지, layout/pipeline/authoring/graph 폴더, lut 의 test_lut_set 밖.

| 그룹 | 결과 |
|---|---|
| metrics | 148 failed, 1160 passed, 62 errors (수집 오류 1) |
| search + sizing | 391 failed, 1294 passed, 68 errors |
| convergence + core + generality + structure + lut_set | 37 failed, 2062 passed, 182 errors |
| integration junction_source_content (cga) | 1 failed |
| **red 합계** | **889** = 앞 세 그룹 888 (failed 576 + errors 312, 수집 오류 1 포함) + integration 1 |

| 사유 문자열(범주) -- 앞 세 그룹 888개 기준(integration 1건은 `AttributeError: 'JunctionSource' object has no attribute 'reference'`, 서명 범주) | 개수 | 분류 |
|---|---|---|
| `pdk_quantity_undeclared` (`junction_nmos_cjs`) -- 엔진이 지워진 PDK 접합 키를 읽음(toy 선언은 tnom 만 선언) | 490 | JC-1 이 고칠 재작성 범위(옛 PDK 접합 키 읽기) |
| `TypeError: JunctionSource.from_decls() missing 1 required positional argument: 'lut_set'` | 373 | 서명(§2) |
| 축 키 결손이 분류 안 된 `KeyError: 'VGS is not a file in the archive'`(6) / 사유는 맞으나 `axis` 칸 없음 `KeyError: 'axis'`(2) | 8 | §5 X |
| `LUT_PARAMETERS` 6열(`'cdb' in ...` 등), 폐형식 문언 줄 3 (R-a·R-b·R-c, 열 목록 상수, 8열 기대, 감도 test 둘) | 7 | §6 |
| `junction_model` `pdk_bsim4_*` != `lut_vgs_min_*`(2) + N-2 삭제 이름(1) | 3 | §3·§7 |
| `ValueError: not enough values to unpack (expected 3, got 2)` -- `junction_field` extras 개수 | 2 | §2 S-4 |
| `ImportError: cannot import name 'junction_at_vgs_min'` -- `test_junction_cap.py` 수집 오류 | 1 (파일의 C-0·J-1~J-12 test 는 수집 불가) | §1 |
| `ss_dev` READS 가 `dc_finger` 포함 (G-1) | 1 | §4 |
| N-1 정규식 엔진 잔존, N-3 PDK 접합 54키 | 2 | §7 |
| **JC-1 무관 (base 에서도 red)** `sizing/test_scc_newton::test_case_two_seal_violation_kept_with_newton_cause` (`tol_v_undefined != lut_query_failed`) -- base 복제본에서 같은 단언으로 실패 재현 | 1 | pre-existing, 이 card 무관 |

- red 사유가 test 쪽 결함(NameError·fixture 오류·잘못된 import 등)인 것은 0. 위 범주가 모두 '엔진 미구현'(옛 키 읽기·서명·이름 부재·열 목록·BSIM4 이름·dc_finger READS)이다. 단 M1 은 지금 red 사유가 가려져 있고 code 뒤 test 결함으로 드러날 것이다.
- 작성자 보고(384 failed / 53 errors)와 숫자가 다른 이유: 범위가 다르다(나는 metrics·search·sizing 전체 = failed 539 / errors 130). 사유별 범주는 같다.
- 새로 쓴 test 가 base 에서 green 인 것: 정규식 변별 test 9(양성/음성이 의도), 기타 이름이 겹친 기존 `test_junction_forward` 8. 실질 새 test 는 전부 red.
- 추가 base 사실(정보): base 복제본에서 `convergence/test_converge_point.py::test_real_junction_caps_from_realized_diffusion[two_stage_ota]` 가 `ValueError: converge: 봉인되고 모든 제약 행이 c >= 0 인 점만 받는다` 로 red(common_gate_amplifier 는 green). 실경로 2회로 전제 문제라 JC-1 무관으로 보이나, code 단계 판정 때 이 파라미터의 red 가 JC-1 탓이 아님을 구분해야 한다.
- 구조 `tests/structure`: 198 passed, 2 failed = `test_jc1_n1_no_bsim4_junction_names_in_engine_text`, `test_jc1_n2_removed_function_and_model_names_absent`(기대 red). 작성자 보고와 일치.

### 4. 판정 대기 항목
**(1) `test_real_junction_caps_from_realized_diffusion` L 보간 -- Major 아님(해소).**
- 실경로 소자 L 을 base 엔진으로 시작 점에서 직접 읽었다(탐침 test, 복제본 base 안): common_gate_amplifier M1·M2·M3 와 two_stage_ota M1~M7 **모두 L = 1.75e-6 m**. cap npz(`sky130_nfet_pfet_lut_v2_r2.npz`) L 격자 = [0.15, 0.18, 0.185, 0.2, 0.25, 0.255, 0.3, 0.35, 0.425, 0.5, 0.7, 1.0, 1.5, 2.0, 2.5, 4.0, 8.0, 20.0] µm -> 1.75 µm 는 격자점이 아니고 이웃 격자 1.5·2.0 µm 사이.
- sky130 nfet_01v8·pfet_01v8 모델 bin 의 L 범위는 [0.15,0.18], [0.18,0.25], [0.25,0.5], [0.5,1.0], [1.0,2.0], [2.0,4.0], [4.0,8.0], [8.0,20.0] µm(모델 카드 `lmin`/`lmax` grep). 1.75 µm 는 bin [1.0, 2.0] 안이고 이웃 격자 1.5·2.0 µm 도 같은 bin 의 닫힌 구간 안이다. 따라서 test 의 격자 L 선형 보간 = '같은 bin 안 선형 보간'이고 bin 경계를 넘지 않는다. 정의 불일치 아님.
- 남는 조건(m5): 이 일치는 L = 1.75 µm 한 값에서 잰 것이다. test 의 보간은 bin 을 아는 보간이 아니라서, 나중에 소자 L 이 bin 경계를 낀 두 격자(예: 1.0과 0.7·2.0과 2.5 사이)에 오면 의미가 갈린다. 지금은 그런 L 이 없다.

**(2) `test_layout_resolve_l2_device_without_input_finger_row_is_realized_finger_missing` -- 유지.**
- 이 test 는 사이징 점에는 M3 의 `dc_finger` 행이 있는데 입력 손가락 행이 없는 M3(배치도 요청도 아님)에서 `realized_finger_missing` 이 나오고 `counter.n == 0`(`block_dc.finger_slice` 호출 0)임을 단언한다. 정지 자리는 `sizing/block_dc.py:637-655`(실현 평가 입력 손가락 행 관문, `dc_solve`)이고 `ss_dev` 접합 경로가 아니다(`sizing/test_block_dc.py:142` D-5 후반과 같은 정지). card 범위(접합 값 출처 교체)가 이 관문을 바꾸지 않으므로 유지. 
- 같은 파일의 짝 test `..._waiting_device_row_erased_in_junction_input_...` 는 접합 경로(`ss_evaluate` 입력 스냅샷에서 행 삭제)라 폐기해야 한다 = M1.

### 5. `tests/structure`
198 passed, 2 failed(N-1, N-2 기대 red). 작성자 보고와 일치. 구조 test 가 낡은 이름으로 깨지는 것은 없다(`test_removed_names` 두 개 외 모두 통과).

## graph 정본·소비 확인(freeze 단계에서 볼 수 있는 부분)
- 이 단계는 test 만 본다: test 가 graph 밖 저장(cache·memo·dict·sctx 슬롯·값 사본)을 요구하는 단언을 만든 곳 0. G-2 는 LUT memo 의 승인된 point 영역 miss 계수를 읽을 뿐 새 칸을 요구하지 않는다. `junction_source` 의 writer 하나(`junction_field`), `ss_dev` READS 에서 `dc_finger` 삭제(G-1), 새 필드 0 이 test 로 고정된다. 엔진 소비자·정본 우회 재계산·KVL·KCL 관련 확인은 code 뒤 판정에서 한다(안 돌린 것을 통과로 세지 않음).

## 기록 사항(Major 아님, LA-1 재점검 입력)
- m1: RETIRED 표에 이름이 빠진 지운 test 2개(`test_temperature_comes_from_lut_cap_conditions`, `test_pre_layout_geometry`) -- covered_by 의 새 이름으로 교체된 것이라 표에 적을 것.
- m2: u13_hand·`write_r4_lut`·gb4_hand 계열 흐름은 cdb = 0 정확히(CDD = CGD) -- 수동성 경계는 통과하지만 접합 항 변별력은 0. 변별은 T-J/T-D/R-b 가 맡는다.
- m3: S-1 toy 가 kind 1개라 'kind 정렬·LUT kind 따름'은 toy 로는 안 가려진다(옛 `test_kinds_follow_lut_not_decl` 폐기). 실 LUT 2 kind 는 2회로 연기 파일(`test_junction_source_content_unchanged_from_base`)이 단언한다(그 파일은 base 에서 AttributeError 로 red 확인).
- m4: R-b 전제의 csb 감도는 ugf 약 1.4e-12·PM 약 3e-11 상대 차이로 아주 약하다(brentq 허용 4·EPS 보다 4~5 자릿수 위라 통과). `!=` 엄격 비교라 값이 더 약해지면 거짓 red 가 될 수 있다.
- m5: 위 판정 대기 (1)의 L 조건.
- w1: E-18 시작 경로 정지가 `ss_dev` 감쌈보다 앞서는지(`cdd=False` 두 test 의 사유 문자열) -- code 뒤 확인.
- 이 판정자의 절차 이탈: 탐침 파일을 격리 복제본(base) 안에서 `sed -i` 로 한 번 고쳤다(지시 금지 목록의 `sed -i`). 복제본 안 임시 탐침이라 산출물·저장소에 영향은 없고, 이후는 Write 로 바꿨다.
- 실제 저장소 `git status --short` 시작/끝 비교: 추가된 줄은 하네스가 만든 `?? .bkit/audit/2026-11-07.jsonl` 하나(내 작업 아님).
- 메모리: 첫 시도(한 프로세스, 6 GB 까지 불어남)에서 가용 메모리가 1 GB 아래(810 MB)로 내려가 그 pytest PID 만 종료했다(다른 측정 agent 프로세스는 건드리지 않음). 이후 그룹별 프로세스로 재측정. 각 그룹 동안 가용 메모리 ≥ 1.1 GB.

## 산출물
- `.ai/verification/20261106-jc1/base_check.json`, `.ai/verification/20261106-jc1/red_base.json`(audit 브랜치 커밋)
- 판정 기록 본체 `.ai/verification/20261106-jc1.json` 은 쓰지 않았다: evidence_type 이 red-green 이라 스키마가 `code_commit` sha1 을 요구하고 아직 code 커밋이 없다(lm1e 선례와 같다). code 커밋 뒤 순서 7 에서 쓴다.


## 재판정

대상: test 머리 `e51874f4`(앞 `6d1d6fd5`), 바뀐 6 파일(RETIRED_TESTS_jc1.md, convergence/test_realized_geometry.py, metrics/test_junction_cap.py, metrics/test_ss_linearize.py, metrics/test_ss_off_op_slices.py, sizing/wb1_toy.py) 전수 diff 읽음. 격리 복제본 `jc1_fz/iso2`(test 브랜치에서 `--no-hardlinks --no-local` 복제, origin 제거, 엔진 base 그대로). 범위: 바뀐 부분과 영향(O-229 3). 새 verdict: **Major 0, 동결 가능**.

### M1~M3 판정
| 항목 | 판정 | 근거 |
|---|---|---|
| M1 낡은 접합 경로 test 폐기 | 닫힘 | `..._waiting_device_row_erased_in_junction_input_...` 삭제(주석으로 폐기 사유 남김), RETIRED '폐기 (M1)' 행 추가, covered_by = D-a2·유지한 짝 test. 같은 파일의 짝 test(`..._device_without_input_finger_row_...`)는 그대로. 옮긴 D-a2(`test_vgs_min_da2_dc_finger_does_not_matter`)가 `dc_finger` 행 값·열 유무 무관을 단언한다. 삭제 외 변경 0. |
| M2 단언 복원 | 닫힘 | `test_from_lut_rule_sky130` 에 옛 두 줄이 같은 값(`1e-12`, `4e-6`, rtol `1e-12`)으로 돌아옴. 같은 파일의 `_rel_close(a, b, rtol)` 은 `abs(a-b) <= rtol*max(|a|,|b|)` 로 옛 conftest `rel_close` 와 같은 꼴이고 test 보다 앞에 정의됨. (이 파일은 base 에서 수집 불가라 실행 확인은 code 뒤.) |
| M3 D-b 를 점마다 다른 열로 | 닫힘(기록 1) | `write_r4_bins_lut(jc1_cols="node")` 이 CDD·CSS 를 격자 인덱스 손 식 `jc1_node_cdd = CGD + (7+l+g+d+s)e-16`, `jc1_node_css = CGS + (8+2l+g+d+s+s)e-16`(= 8+2l+g+d+2s) 로 쓴다(`"node"` 문자열은 truthy 라 기존 `True` 호출 경로와 분기가 겹치지 않고 `==` 순서로 먼저 걸림). D-b 는 `ss.cdb == (cdd(l,0,d,s) − CGD)·r_d`, `ss.csb == (css(l,0,d,s) − CGS)·r_s` 를 `==`(비트)로 단언, 연산 순서 `((a·w)/(a·w_ref))` 는 엔진 식(J-1)과 같다. 피검 함수 사용 0(손 식 + `R4_GRIDS.index`). |

M3 변별력(손 식으로 직접 계산, 스크립트 `scratchpad/jc1_node_probe.py`): 표적 마디는 L 격자 [1e-6, 2e-6]·VGS [0, 0.125, ...]·VDS 0.25 간격·VS 0.25 간격(−0.5 시작)에서 (l,g,d,s) = (1,0,4,4). 이웃 마디가 (cdd, css) 쌍을 바꾸는지: L−1, VGS+1(0.125), VDS±1, VSB±1 모두 값이 달라진다(L+1 은 축 끝이라 없음). 같은 쌍을 내는 다른 마디는 두 축을 동시에 틀리는 조합(예 (0,0,4,5), (1,1,3,4))뿐이라 단일 조회 오류(다른 L, 다른 vds, 다른 vsb, 0 아닌 VGS)는 잡힌다. 한계(기록 m6): 표적에서 vds 와 vsb 의 인덱스가 같아(4,4) **vds↔vsb 맞바꿈은 변별되지 않는다**. card 의 toy C 마디 [1,0,1,1] 도 d = s = 1 이라 card 자체가 가진 성질이다. 또 손 식의 VGS 계수가 toy C(CDD−CGD 의 2g)와 달리 1 이나 g = 0 마디에서는 toy C 정의 (7+l+d+s), (8+2l+d+2s) 와 같다. 기대 `ss.cdb ==` 는 엔진이 `W/w_ref = 1` 로 곱하고 같은 연산 순서를 쓰는 전제의 비트 비교라 code 뒤 부동소수 순서가 다르면 거짓 red 가 될 수 있다(code 몫으로 넘김).

### 이번 diff 의 새 기준 약화·범위 이탈
없음. 6 파일 변경 중 삭제된 단언은 M1 의 폐기 test 하나(접합 경로가 사라짐, RETIRED 기록·짝 유지). `test_ss_off_op_slices.build` 의 `jc1_cols=True` 기본값은 기존 호출 불변. `wb1_toy` 변경은 가산(기본 False 경로 불변). RETIRED 의 m1 행(옛 이름 두 개 → 새 이름)이 추가돼 m1 닫힘. 경로 밖 변경 0(전부 `gmid_engine/tests/`).

### 4건 red 분류 (`test_realized_geometry`)
- 앞 판정 base(da4f5366 test + 엔진)에서 이 파일은 **9 passed**(내가 직접 재현). 머리 test + base 엔진에서 4건 red: `r13a`, `r13b`, `l2_waiting_device_row_is_the_request_and_junction_follows_two_places`, `l2_device_without_input_finger_row_is_realized_finger_missing`.
- 4건 모두 같은 사유: `SchemaRejectedError pdk_quantity_undeclared quantity = junction_nmos_cjs`. 실패 지점은 case 구성 단계(`bins_case`/`_l2_start` → `build_search_context` → 엔진 `junction_field` 가 옛 PDK 접합 키를 읽음)로, test 의 toy PDK 선언이 이제 tnom 만 선언하기 때문이다 = JC-1 재작성 범위(범주 A). test 결함 아님.
- 유지한 짝 test 의 사유: base 엔진에서 case 를 만드는 fixture 단계가 `block_dc` 실현 입력 관문보다 앞에서 위 사유로 깨진다. 즉 이 red 는 정지 관문을 실행해서 나온 것이 아니라 그 앞 setup 에서 가려진 것이다. 관문 자체의 건전성은 base test(옛 PDK 선언을 쓰는 같은 단언)가 base 엔진에서 **통과**한다는 사실과, 정지 자리가 `sizing/block_dc.py` 실현 입력 손가락 행 관문이고 이 card 가 바꾸지 않는다는 앞 판정 근거로 갈음한다. 이 test 의 `realized_finger_missing` 단언은 code 뒤 setup 이 풀리면 처음 실행된다 -> code 단계 판정에서 첫 확인 항목(w2).
- 이 4건 외 `test_realized_geometry` 는 그대로 통과(`all_placed...`, `no_width_key...`, `equality...`, `device_class_helper...`).

### 실행 결과
- 범위: `convergence/test_realized_geometry.py`, `structure`, `metrics/test_ss_linearize.py`, `metrics/test_ss_off_op_slices.py`, `metrics/test_junction_cap.py`. 결과 **41 failed, 203 passed, 9 errors, 1 deselected**(수집 오류 1 = test_junction_cap). red 50 의 범주: `from_decls` 서명 41, 옛 PDK 접합 키 4, `junction_model` 식별자 2, `junction_at_vgs_min` ImportError 1, N-1 1, G-1(dc_finger READS) 1 -- 미분류·test 결함 0. D-b 의 base red 사유는 `from_decls` 서명(TypeError).
- `tests/structure`: **198 passed, 2 failed**(N-1, N-2 기대 red). 앞 판정과 같다.
- 작성자 측정(202 passed, 6 failed)은 같은 6 failed 구성(N-1·N-2 + 위 4건)과 맞는다.
- 안 돌린 것(통과로 세지 않음): 위 범위 밖 전부(앞 판정 목록 + 이번 diff 가 건드리지 않은 search/sizing 전체 재실행 등), 2회로 연기, ngspice.

### 기록 사항(Major 아님)
- m6: D-b 표적 마디가 d = s 라 vds↔vsb 맞바꿈 미변별(card 고유 성질, 위 참고).
- w2: 유지한 짝 test 의 `realized_finger_missing` 단언은 code 뒤에야 처음 실행된다.
- 절차: 이번 재판정에서 stdlib 모듈 이름 스크립트를 한 번 만들었다가(`dis.py` 가 `dis` 를 가려 import 오류) 바로 `jc1_node_probe.py` 로 바꿨다. `sed -i`·heredoc 은 쓰지 않았다.
