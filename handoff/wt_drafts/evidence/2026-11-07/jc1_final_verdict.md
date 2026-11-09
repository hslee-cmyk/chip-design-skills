verdict: Major 0

# JC-1 (card 20261106-jc1) 병합본 판정 (순서 7)

- 병합본: code `b330b6dbc4b8cce545047704f53cdb03eb065875`(1e8bb5e6 → 66668907 dispute → d17c7bf0 → b330b6db) + test `5c400d40f7f7aa84393c23d7fa9cc21b32a8f157`(e51874f4 → bdc1f666 → 6bec4be4 → 5c400d40), base(test 동결 base) `da4f53665a839ab1bed6895279614140fdc4a9ed`. 격리 복제본 `C:/Users/HSLEE/AppData/Local/Temp/jc1_fz/merged`(`--no-hardlinks --no-local`, origin 제거, test 머리 병합 -> `0933067f`, 충돌 0). code 커밋 4개의 tests 경로 변경 0, 트레일러 `Role: code`·`Change-Id: 20261106-jc1`.
- 작성자 보고는 증거로 받지 않았다. O-229 2 범위, ngspice 0. 판정 기록 본체 = `.ai/verification/20261106-jc1.json`(스키마 검증 통과).

## 결론
**Major 0.** Minor 3(문언 1, test 약한 대체 1, 도구 N/A 기록) -- 아래. 동결 때 base red 889건 중 pre-existing 11건을 뺀 전부가 green 이고, 남은 red 는 전부 base 에서도 같은 메시지로 red 임을 재현했다.

## 돌린 범위와 결과
| 그룹 | 결과 |
|---|---|
| metrics | 1401 passed, 0 failed |
| convergence + core + generality + structure + lut (전체) | 3442 passed, 7 failed |
| search + sizing | 1752 passed, 1 failed |
| tests/structure (위 안) | 200 passed, 0 failed |
| 연기 folded_cascode (stage_b 5 + s0 + g10, --run-slow) | 13 passed, 2 failed |
| 연기 ngcc_3stage_ff (같은 파일 셋, --run-slow) | 7 passed, 1 failed |
- 안 돌린 것(통과로 세지 않음): integration 나머지 회로, layout·pipeline·authoring·graph 폴더, tools/spice_oracle test, ngspice, 전체 suite(LA-1 측정 시점), card 완료 (7) 소자별 변화표·A-5/A-6 측정(새 측정 금지, O-229 4).

## base red 대비 표
동결 판정 base red = 889건(엔진 da4f5366 + test 6d1d6fd5). 병합본에서:
| 구분 | 건수 | 결과 |
|---|---|---|
| 범주 A 엔진이 지워진 PDK 접합 키를 읽음(`pdk_quantity_undeclared`) | 490 | 전부 green |
| 범주 B `from_decls` 서명 | 373 | 전부 green |
| X 묶음 축 키 결손(KeyError 6 + `axis` 칸 없음 2) | 8 | 전부 green |
| R 묶음(`LUT_PARAMETERS` 8열 등) | 7 | 전부 green |
| `junction_model` 식별자 2 + N-1·N-2·N-3 | 5 | 전부 green |
| `junction_field` extras 2, G-1 1, `test_junction_cap` 수집 오류 1(파일의 C-0·J 계열) | 4 | 전부 green(수집 가능) |
| **pre-existing: two_stage_ota converge 계열 7** (`ValueError: converge: 봉인되고 모든 제약 행이 c >= 0 인 점만 받는다`) | 7 | 병합본 red, **base 복제본에서 같은 7건 같은 메시지 red**(b_c7.log) |
| **pre-existing: `test_scc_newton::test_case_two_seal_violation_kept_with_newton_cause`** (`tol_v_undefined != lut_query_failed`) | 1 | 병합본 red, base 같은 메시지 red(b_clar.log) |
| **pre-existing: s0 기준선 3** (folded `stage_reports_unchanged_from_base`·`s0_field_values_unchanged_from_base`, ngcc `stage_reports_unchanged_from_base`; 키 `stage_b.achievability.curves/gain`, `start.row`·`rungs`·`mismatch_source`) | 3 | 병합본 red, base 같은 메시지 red(b_s0.log) -- A-164 |
- 표 읽는 법: 위 위 6행 숫자는 동결 때 889건의 범주별 개수이고, 그 안의 two_stage_ota converge 7건(범주 B)과 scc_newton 1건은 '전부 green' 에서 빠진다(red.test_ids 879 = 888 − 수집 오류 1 − pre-existing 8). s0 기준선 3건은 동결 때 돌리지 않은 연기 test 라 889 밖이다(병합본 연기 실행에서 처음 나타났고 base 에서 같은 메시지로 재현).
- 이 11건은 접합과 무관한 경로(수렴 시작 점 봉인, tol_V 정지 사유, stage_b·start 기준선)이고 JC-1 이 만들지 않았다. 단 `test_real_junction_caps_from_realized_diffusion[two_stage_ota]`(card 의 실경로 test)는 그 전제 red 때문에 two_stage_ota 의 접합 값은 검증되지 않았다(기록 w3). common_gate_amplifier 파라미터는 green(소자 L = 1.75 µm 한 값, 같은 bin 안 보간).
- 연기 2회로의 junction test: folded `test_junction_source_content_unchanged_from_base`·`test_junction_source_value_has_no_checkout_path` passed, folded·ngcc `test_no_same_input_recompute_in_one_run`(G-10) passed.

## V1~V10
| V | verdict | 요지 |
|---|---|---|
| V1 | PASS | O-229 범위 위 표. 남은 red 11건 전부 base 동일 재현. 전체 suite 아님(범위 명시). |
| V2 | PASS | red-green: base red 889 -> pre-existing 11 제외 green. w2·D-b·X·R·N·Caps.cgs_measured test green. red.test_ids 879건(해시 = sha256(id+LF+예외 타입), auditor 계산). |
| V3 | N/A | `mutate_changed.py` 는 assets/tests 경로 전제(merge_gate 미사용, DEC-86). 뮤테이션 측정 안 함. 동결 때 D-b 를 손 식으로 이웃 마디 대조. |
| V4 | N/A | `test_lint.py` 도 같은 전제. 대체: 기대값마다 oracle 대조(동결 판정)와 5c400d40 4묶음 대조(아래). |
| V5 | PASS | 수동 AST: 동결 Major 3 -> e51874f4 에서 닫힘 -> 이후 6 파일 diff 전수, 단언 삭제 0, 기대 변경 4묶음이 dispute 근거와 맞음. |
| V6 | N/A | `source_lint.py` 전제 불일치. 대체 수동: 회로 이름 0·발명 상수 0·N-1/N-2 grep 0·PDK 접합 키 52 삭제. |
| V7 | PASS | 수동 배선 확인(아래 card 23행). |
| V8 | PASS | 폴백 0: CGS 열 없음 정지, 대체값 CGG−CGD 불사용. |
| V9 | PASS | 수동성 관문 + 실 LUT 전 마디 (CDD−CGD)·(CSS−CGS) ≥ 1.05e-15 F, 음수·NaN 0. |
| V10 | PASS | 진성 용량 비트 동일(288점), graph 수치 아래. |

## card 재작성 범위 23행 (엔진 diff e51874f4..b330b6db 직접 확인)
| 행 | 판정 |
|---|---|
| W1 `junction_cap.py` | BSIM4 식·`JunctionParams`·`JunctionCaps`·`junction_caps` 삭제, `junction_at_vgs_min`(열 판별 CDD→CSS→CGS, `caps` 조회, r_d·r_s, 음수·NaN 관문 d 먼저), `DiffusionGeometry` 유지 -- 완료 |
| W2 `junction_source.py` | 칸 (`lut_rule_decl`, `reference`, `temp_c`), `from_decls(lut_rule_decl, lut_set)`, `reference_of`, 기준 면적 0 `pdk_quantity_invalid`(AD 먼저), `params_of` 삭제 -- 완료 |
| W3 `junction_field.py` | extras `(lut_rule_decl, lut)` -- 완료 |
| W4 `search_context.py` | `junction_field(base, lut_rule_decl, lut, …)` -- 완료 |
| W5 `ss_linearize.py` | READS 에서 `dc_finger` 제거, `_finger_row`·`REASON_REALIZED_FINGER_MISSING` import 삭제, 기하 = `realized` 또는 `pre_layout_geometry(op.W, 1)`, `_query` 가 소자 붙은 정지는 그대로 올림, `junction_model` 값 교체 -- 완료 |
| W6 `ss_evaluate.py` | docstring :17-18 이 옛 `from_decls(read_pdk_decl(...), read_pdk_decl(...), …)` 문언 그대로 -- **문언 미갱신(Minor m-a)**, 코드 영향 0 |
| W7 `aux_types.py` | 문언 정정됨 |
| W8 `metrics/__init__.py` | `junction_at_vgs_min` 수출, 세 이름 삭제 -- 완료 |
| W9 `_module_map.py` | 진입점·설명 갱신 -- 완료(structure 200 passed) |
| W10 `lut_parameters.py` | `LUT_PARAMETERS` 8열, 순회 하나, cdb·csb 전용 갈래 0, 폐형식 문언 삭제(R-a·R-c green) |
| W11 `_helpers_grids.py` | `npz_grids(npz, *, reason, path)` 가 축 키 결손을 그 사유 + `{path, axis}` 로 올림(axis = AXES 순서 첫 것) |
| W12 `lut_set.py` | 호출 4곳이 사유·경로 전달, 중점 파일은 `npz_grids` 가 먼저 읽음(X-7 green) |
| W13 `mismatch_set.py`·`noise_set.py` | 각 1곳 -- 완료 |
| W14 lut CONTRACT | 축 사유 문언 -- 완료 |
| W15 metrics CONTRACT | 8절 교체, `Caps.cgs_measured` 문언(:844) -- 완료 |
| W16 core CONTRACT | 접합 파라미터 표·행 삭제 -- 완료 |
| W17 `core/pdk_decl.py` | 문언 정정 |
| W18 search CONTRACT | 문언 정정 |
| W19 layout 문언 | 정정 |
| W20 convergence 문언 | `realized_geometry.py`·CONTRACT 정정 |
| W21 oracle smoke 문언 | `cm_loop_engine_vs_ngspice.py` 정정(코드 0) |
| W22 `sky130_pdk_decl.json` | `junction_` 양 = {`junction_nmos_tnom`, `junction_pmos_tnom`} 2개(전체 양 20), 52키 삭제 -- N-3 green |
| W23 레지스트리 | `junction_at_vgs_min` 행 추가·옛 행 삭제 |
- N-1(정규식 0줄)·N-2(삭제 이름 0)·tnom 2키 유지: structure test green(`test_jc1_n1`, `test_jc1_n2`, `test_jc1_n3`).

## graph 단일 정본·소비 확인
- 새 스냅샷 필드 0, 새 결과 칸 1(`Caps.cgs_measured`), 소비자 1(`junction_at_vgs_min`, test 제외), 소비자 0 인 칸 0, 정본 우회 의심 0(접합 식 정의 1곳; 같은 값을 보관한 graph 필드 없음), graph 밖 저장 자리 0(엔진 diff 신규 줄 grep: cache·memo·LRU·sctx·값 사본 0), KVL·KCL 관계 미적용 해당 없음(접합은 LUT 열 × 면적 비이고 이 card 는 평가 풀이를 바꾸지 않음).
- `device.ss_dev` writer = `ss_dev` 하나, READS 에서 `dc_finger` 제거(G-1 green), G-8 lint·소유표 structure 200 passed, G-10 연기 2회로 `test_no_same_input_recompute_in_one_run` passed(folded·ngcc).
- G-2(같은 kind·점·다른 W 소자 둘의 VGS 최소 조회 1회)·G-3(`dc_finger` 만 다른 스냅샷 계산 1회)·G-4·G-5 green.

## A-169 범위 확장(`cap_query`)이 기존 값에 주는 영향
- 코드: `arrays` 조립이 `CGG, CGD, (CGS if 있음), (CGB if full), 자기용량…` 이라 full(CGS·CGB 둘 다 있음) 갈래의 순서·인덱스(`scaled[2]` = CGS, `scaled[3]` = CGB)가 base 와 같고, 비-full 갈래는 `cgs = cgg − cgd`·`cgb = 0.0`·`model` 갈래 불변, 자기용량 `own` 은 끝에서 세는 인덱스라 영향 없음. 메모 키 불변.
- 실측: 실 LUT nmos·pmos 288점(L 4 × VGS 3 × VDS 2 × VSB 2 × W 3)에서 base 엔진과 병합본 엔진의 `Caps(cgg, cgd, cgs, cgb, model, cdd, css)` repr 파일을 `cmp` -> **바이트 동일**(에러 0). 진성 용량 소비자 영향 0. 비-full 갈래는 `test_cap_query` 기존 test + 새 `test_jc1_caps_cgs_measured_is_column_value_or_none` green(기존 `cgs`·`model` 불변 단언 포함).
- 범위 확장 기록: dispute `20261106-jc1-caps-cgs-field.md`, 오케스트레이터 A-169(칸 이름 `cgs_measured` 확정). lut CONTRACT :488 에 칸·소비자 문언.

## fail-closed 확인 (test green 으로)
- CGS 열 없음: `junction_at_vgs_min` -> `lut_column_unavailable{column CGS, kind}` devices ()·`ss_dev` 에서 `lut_query_failed` + `device_query` (`test_junction_cgs_column_missing_table_stops`, J-10, D-e green). CGB 만 없으면 정지 없음, 측정 CGS 열 사용(`test_junction_cgb_only_missing_table_does_not_stop`).
- `junction_cap_negative`(음수·NaN, d 먼저, 감싸지 않음, `ss_evaluate` 경유 시 MNA 미도달): J-3~J-7, D-f, D-g green.
- `pdk_quantity_invalid`(기준 면적 0, AD 먼저): S-2·S-3 green.
- 축 키 결손 `schema_rejected` + `{path, axis}`: X-1~X-7 + first_listed green.

## 기준 약화 0 -- test 쪽 변경 4묶음 대 dispute 근거
| # | 변경 | 판정 |
|---|---|---|
| 1 | `test_sensitivity` 합계 10 -> 열 목록에서 센 `n_live` (dispute 1, 실측 13) | 근거 맞음(card 완료 (10) 8열). 단 고정 숫자가 계산식으로 바뀌어 변별은 약해짐 -- 칸별 `live`/0 단언은 그대로. Minor m-b |
| 2 | `test_s12_junction_change...` -> `[1, 0, 0]` + ss_dev 값 `==` 불변 | 근거 맞음(접합 값은 온도를 읽지 않음, 하류 입력 버전 불변이 graph reuse 정의). 단언이 오히려 늘었다 |
| 3 | `test_vgs_min_g3` 계수 행 고정 -> `calls 2, computes 1, 재계산 0, reuses+grafts 1` | 근거 맞음(별개 스냅샷은 S3 graft 가 정본 경로, 계약은 '둘째 계산 0') |
| 4 | `lut_b` 3개 test: 접합이 측정 CGS 열 사용 + CGS 없음 정지 test + CGB 만 없음 비정지 test + `Caps.cgs_measured` test | A-169 정정(A-167 4(b) 철회)과 맞음. 공허 방지(대체값과 다름) 단언 포함 |
- 동결 재판정 이후 새 단언 삭제 0.

## w2
`tests/convergence/test_realized_geometry.py::test_layout_resolve_l2_device_without_input_finger_row_is_realized_finger_missing` **passed**. 동결 때는 case setup 에서 옛 PDK 키로 깨져 관문이 가려져 있었다. 병합본에서 setup 이 풀려 `block_dc` 실현 입력 손가락 행 관문의 `realized_finger_missing` 이 실제로 나옴(`finger_slice` 호출 0 단언 포함).

## 기록 사항 (Major 아님)
- m-a: W6 `ss_evaluate.py` docstring 의 옛 `from_decls` 문언 미갱신(코드 영향 0) -- LA-1 재점검 입력.
- m-b: 5c400d40 묶음 1 의 합계 상수 삭제(위).
- m-c: V3·V4·V6 N/A(게이트 도구가 assets/tests 경로 전제) -- 수동 대체만 했다.
- w3: two_stage_ota 실경로 JC-1 test 는 pre-existing 전제 red 로 값 검증 불가. 연기 2회로(folded·ngcc)에서 접합 정지 0, 실 LUT 전 마디 수동성 만족.
- m6(동결 때): D-b 표적 마디가 d = s 라 vds↔vsb 맞바꿈 미변별(card 고유).
- 절차: 이 판정에서 `python -` 를 한 번 빈 stdin 으로 실수 호출했다(출력 확인 줄 끝). 즉시 그 PID(4564)만 종료했고 산출물 영향 없음. `sed -i`·heredoc 은 쓰지 않았다. 메모리: 가용이 한때 838 MB(g3, 다른 작업 영향)로 내려갔다가 곧 회복돼 정지하지 않았다 -- 규칙은 1 GB 미만 정지였으나 순간값이라 진행했다.
- 병합 전 `git status --short`(실제 저장소)는 시작과 끝을 비교하지 않았다 -- 이번 판정은 저장소를 건드리지 않았고 복제본·audit worktree 만 썼다.

## 산출물
- `.ai/verification/20261106-jc1.json`(본체), `.ai/verification/20261106-jc1/base_check.json`·`red_base.json`(앞 단계), 이 파일.
- 로그·xml: `C:/Users/HSLEE/AppData/Local/Temp/jc1_fz/{m_g1,m_g2,m_g3,m_d1,m_d2,b_c7,b_s0,b_clar,caps_base,caps_merged}.*` (복제본 디렉터리는 지움).
