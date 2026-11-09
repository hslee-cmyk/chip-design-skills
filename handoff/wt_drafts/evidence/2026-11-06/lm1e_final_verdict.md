verdict: Major 1

# LM-1e 병합본 판정 (순서 7, 판정자 1회)

- 판정 대상: code `04e53dfd` + test `cf1685d5` 를 격리 복제본에서 `--no-ff` 병합한 `955df83e`(복제본 안에서만 존재, 실제 저장소 불변). base `56d88fe7`.
- 판정 기록 커밋: audit worktree `role/audit/20261106-lm1e` = `36889a23` (`.ai/verification/20261106-lm1e.json`, 스키마 검증 통과).
- 측정 파일: `C:/Users/HSLEE/AppData/Local/Temp/la1s_lm1e_a7/` (v1_*.txt, mutants_results*.jsonl, dump_tso.json, v4_lint.txt). O-229 범위만, ngspice 0.

## Major (1)

**M-1. 필수 test 실패: `sizing/test_seal_tolerances.py::test_cell_combine_j_a_none_cell_cascades_to_seals_and_report`.**
- 메시지: `전제 실패(멈추고 보고): N3 ∩ 봉인 3 KCL 행 넷이 비어 있다 (N3=['pb', 'vdd'], KCL 넷=['vout'])`. 작성자가 'cf1685d5 가 고친다'고 한 2건 중 이 1건은 고쳐지지 않았다(J-b 쪽은 통과).
- 원인은 엔진이 아니라 test 의 N3 유도다. 같은 상태 probe(복사본에서만 실행): 봉인 1 undefined (M3; pb, vdd), 봉인 2 undefined (M3), **봉인 3 undefined (M2, M3; 넷 vout)**, `dc_current_basis.ends` = (M1 vin gnd)(M2 vout vin)(M3 vdd vout), `node.dc_path_values` 에서 M3 가 든 넷은 pb·vdd 뿐(vout 은 `('y','vout')`). 즉 봉인 3 은 기대대로 M3 의 None 이 vout KCL 행으로 번지는데, test 가 'M3 가 dc_path_values 경로에 든 넷 ∩ KCL 행 넷'으로 기대 집합을 만들어 공집합이 된다. card 문언 'N3 ∩ KCL 행 넷'(A-161·A-162) 자체가 이 회로에서 비는 정의다.
- 재현: 격리 복제본 `tests` 에서 `python -m pytest -p no:cacheprovider sizing/test_seal_tolerances.py -k j_a_none_cell`.
- 처리 제안(오케스트레이터 몫): test 작성자가 봉인 3 기대 넷을 '채널이 M3 에 닿는 KCL 행 넷(`dc_current_basis.ends` 에서 M3 의 끝 넷, 제외 넷 뺀 것) = {vout}'으로 유도하도록 card·test 를 고친다(엔진 불변). 고친 뒤 이 test 와 base red 였던 같은 id 를 재판정.

## 못 쟀다 (통과로 세지 않음)

- **2회로 연기(folded_cascode, ngcc_3stage_ff; stage_b·s0·g10)**: 단독 프로세스가 여유 메모리를 5.3 GB → 2.0 GB 아래로 먹어 2 GB 하한 규칙대로 두 번(stage_b·g10 의 folded_cascode) 멈췄다. 작성자 보고 '12 passed'는 확인하지 못했다. 메모리 여유가 큰 곳에서 한 번 더 돌려야 한다. G-10 블록 재계산 계수 불변, 연기 회로의 봉인 잔차, 폴백 발동 수도 같은 이유로 미측정.
- integration base red 196건(이름 맞춤 파일) 미실행(O-229 범위 밖). 완료 4(base 대 head tol 표 셀 비교)·완료 10(A-12 새 None 원인별 계수)·완료 8 (ii) 미실행.

## V1~V10

| V | 판정 | 요지 |
|---|---|---|
| V1 | FAIL | lut 1251·metrics 1433·search+layout 57·structure 189(1 deselected)·sizing 139 passed, sizing 1 failed(위 M-1). 2회로 연기 미실행 |
| V2 | FAIL | base red 비 integration 188 중 187 green, 1 red(J-a). integration 196 미측정 |
| V3 | PASS | 수동 뮤턴트 22 중 20 죽임. 생존 2 = 동치(bracket `<`→`<=`) 1, minor test 구멍 1(b_P 레일 항에서 None 소자만 빼기, P-1 은 vdd 에 소자가 M3 뿐이라 구분 못 함). 설정 배열 원소 거부 7개 모두 변별(빈 배열·중복·단일 객체·not_object·no_path·no_sha·absolute·dotdot) |
| V4 | PASS | test_lint 도구 FAIL 6건 = base 에 있던 test 5 + 새 test 1(assert 가 for/if 두 갈래, 비공허 -- minor). 확실한 복사 0, oracle 대조는 freeze 기록 |
| V5 | PASS | 사라진 assert 67 은 옛 형식·옛 결합 규칙 기대, 새 153. A-160 은 약화를 되돌림, A-162 spy 변경은 같은 힘. 기준 약화 0 |
| V6 | PASS | 새 광범위 except 0, 새 continue 1(0 V 레일 항, 물리 정의), 상수 발명 0(`_PAIR = len(LINEAR_CONDITIONS)`), 회로 이름 0, 옛 코드 grep 0 |
| V7 | PASS | 배선 확인(midpoint_bracket 2 호출자, table_at 4 호출자·둘째 구현 0, 이름 표 1). 새 스냅샷 필드 0, 새 cache/memo/sctx/결과 칸 0 |
| V8 | PASS | 런타임 폴백 0. 옛 꼴 읽기는 `table_cache._pinned_midpoints` dict 갈래(보존 집합 전용, 종료 조건 문서화). 연기 회로 발동 수는 미측정 |
| V9 | PASS | two_stage_ota b_P 독립 재계산 일치, J-a 상태에서 봉인 1·2·3 undefined 전염 정확. 연기 회로는 미측정 |
| V10 | PASS | two_stage_ota: 모든 MOS dc_tol_v 정의, M6 dc_tol_v 4.3747e-3 V(WB-1 뒤 4.25e-6 에서 회복), power_resolution_w 6.8909e-6 W(6.69e-9 에서 회복) = 1.8×(M6 tol×gm) 일치. 중점 30파일 L = 승인 목록(0.165·0.85·1.75·3.25 µm) |

## 원칙 점검

- graph 정본: tol 셀 writer `dc_tol_v` 하나 불변, 새 필드 0, 새 cache·memo·sctx 슬롯·결과 값 칸·값 사본 0(`LutProvenance.midpoints_sha256` 는 property). 셀 결합 `table_at` 한 곳(tol_V·tol_VDsat·잡음·mismatch 가 모두 호출, 둘째 구현 grep 0), bracket 판별 `midpoint_bracket` 한 곳(호출자 2). 필드 수 0 / 소비자 0 / 정본 우회 의심 0 / KVL·KCL 미적용 0 / graph 밖 저장 0.
- 물리 정합·fail-closed: 위반 0(셀 일부 None 이 봉인 행과 b_P·ICMR 로 정확히 전염, 값 대신 정의 항이 빠진 값 0). `_conduction_floor` 변경 0.
- dispute A-159~A-162 반영: 기준 약화 없음(V5). 단 A-162 (2)의 J-a 유도가 아직 틀렸다(M-1).

## minor (왕복 없이 LA-1 재점검 입력)

1. b_P 레일 항 부분 None 구분 test 부재(뮤턴트 m5b 생존) -- 한 레일에 정의 소자와 None 소자가 함께 닿는 toy 1개.
2. `test_lm1e_t1_both_keys_same_table`: assert 가 for/if 안(도구 규칙 3), 비공허.
3. `table_cache._pinned_midpoints` 옛 꼴(dict) 갈래: master 병합·옛 설정 worktree 0 이면 삭제.
4. `MidpointChecks.midpoints_sha256` 칸은 엔진 소비자 없음(base 부터 있던 칸, 값 의미만 슬라이스 파일 sha 로 바뀜).
5. 코드 서식 `t =(L_m ...)`(midpoint_checks), 이미 지적할 만한 기능 영향 없음.
6. 뮤턴트는 `-k 'not real'` 로 실데이터 test 를 제외했다(실데이터 test 는 V1 에서 통과).
7. gate 도구 `mutate_changed.py`·`source_lint.py`·`weakening_diff.py` 는 소스 분류가 `assets/` 뿐이라 gmid_engine 에 적용 못 해 수동 판독으로 대신했다(freeze 때와 같음).

## 사용자 결정 필요

없음. (2회로 연기 재실행 환경은 오케스트레이터가 정한다.)


## 재판정
re-verdict: Major 0 (측정한 범위 안; 2회로 연기 미실행 -- 아래)

- 대상: test 머리 `8c54bb2e` + code `04e53dfd` -> 격리 병합본 `8a2a0c7e`(복제본 안에서만).
- 앞 Major M-1 해소: `sizing/test_seal_tolerances.py` + `sizing/test_block_dc.py` + `sizing/test_s2_values.py` 140 passed(J-a 포함). J-a 의 K3 유도(M3 채널 끝 넷 ∖ (레일 ∪ 입력 포트), `dc_current_basis.ends` 에서 유도, 이름 박지 않음, 비면 전제 실패)는 interface A-163 과 같고, 단언 강도 불변 -> 기준 약화 0.
- 앞 판정의 나머지 V 결과 재사용(엔진·그 외 test 불변): lut 1251·metrics 1433·search+layout 57·structure 189 passed, V3~V10 그대로.
- **못 쟀다(통과로 세지 않음): 2회로 연기.** s0 folded_cascode 를 여유 5.2 GB 에서 단독 재시도했으나 프로세스가 약 3.3 GB 를 먹어 2 GB 하한 아래(1.75 GB)로 내려가 PID 지정으로 멈췄다(세 번째 중단). 작성자 '12 passed'는 여전히 미확인. G-10 계수 불변·연기 회로 봉인 잔차·폴백 발동 수도 미측정. 메모리 큰 환경(또는 다른 프로세스 정리 뒤)에서 회로별 순차 재실행이 필요하다 -- 오케스트레이터 결정.
- 판정 기록: `.ai/verification/20261106-lm1e.json` 갱신(code_commit `8a2a0c7e`, V1 N/A, V2 PASS), `Role: audit` 커밋.


### 재판정 2 -- 2회로 연기 (O-250 하한 1 GB)
re-verdict: Major 0 (LM-1e 귀속 실패 0; 미실행 1, 기존 실패 3은 사용자·오케스트레이터 결정 사항)

실행: 병합본 `8a2a0c7e`, 회로·파일 하나씩 순차, `run_in_background` + sleep 있는 감시 루프(여유 1 GB 미만이면 그 pytest PID 만 정지). 결과 파일 `smoke2_*.txt`, 로그 `smoke2_log2.txt`.

| 파일 | 회로 | 결과 | 최저 여유(MB) |
|---|---|---|---|
| s0_layer_9circuits | folded_cascode | 7 passed, **2 failed**, 74 deselected (582 s) | 1353 |
| g10_no_recompute_9circuits | folded_cascode | 1 passed (342 s) | 1319 |
| stage_b_library | folded_cascode | **미실행**: 두 번 모두 여유 936 MB·1004 MB 에서 1 GB 하한으로 멈춤 | 936 |
| stage_b_library | ngcc_3stage_ff | 5 passed (137 s) | 2593 |
| s0_layer_9circuits | ngcc_3stage_ff | 1 passed, **1 failed** (262 s) | 2826 |
| g10_no_recompute_9circuits | ngcc_3stage_ff | 1 passed (150 s) | 2566 |

- G-10 계수 불변: 두 회로 g10 test 통과(재계산 0 단언).
- 실패 3건: `test_stage_reports_unchanged_from_base[folded_cascode, ngcc_3stage_ff]`(보고서 키 `stage_b.achievability.curves`·`gain` 이 기준선과 다름), `test_s0_field_values_unchanged_from_base[folded_cascode]`(M3·M4·M7~M10·MP `start.row`, `rungs`, `area_est_m2`).
- **귀속: base `56d88fe7`(엔진·test 미변경) 에서 같은 test 를 돌리면 똑같이 실패한다**(`base_log.txt`; folded 2 failed 1 passed, ngcc 1 failed; E 줄 6개가 head 와 diff 0). LM-1e 가 만든 실패가 아니다. 낡은 기준선 fixture `fixtures/u17_1b_s0_baseline.json`(UB-1 achievability 키·start.row 변동을 아직 안 반영) 문제로 읽힌다 -- 판정 범위 밖이므로 고치지 않고 LA-1 재점검 입력 / 오케스트레이터 결정으로 넘긴다. ⚠ 단 O-229 3 의 'Major = 2번 test 실패'를 문언대로 적용할지는 오케스트레이터가 정한다(기존 실패라 이번 card 의 책임이 아님).
- 폴백 발동 수·연기 회로 봉인 잔차: 별도 지표로는 안 쟀다(통과 단언만). folded stage_b 미실행분은 통과로 세지 않는다.
- V1 확정: N/A(미실행 1 포함). Major 0, minor 추가: 기준선 fixture 낡음 3건, folded stage_b 는 메모리 5 GB 환경에서도 하한 근접(936·1004 MB) -- 더 큰 환경에서 1회 필요.


### 재판정 3 -- folded_cascode stage_b 를 test id 하나씩 (별도 pytest 프로세스)
re-verdict: Major 0 (변동 없음; V1 N/A 유지)

`--collect-only` 로 5 id(`test_count_budget_is_lut_grid_sum_of_used_kinds`, `test_block_grid_products_and_budget_gate`, `test_gain_target_and_verdict`, `test_area_lower_bound_from_declared_values`, `test_diagnostic_mode_keeps_stage_a_exit_code`, 모두 `[folded_cascode]`)를 얻어 하나씩 별도 프로세스로 순차 실행(`runsb3.sh`, 시작 전 여유 3.7 GB 이상 대기, 1 GB 미만이면 그 PID 만 정지).

| # | test | 결과 | 최저 여유(MB) |
|---|---|---|---|
| 1 | test_count_budget_is_lut_grid_sum_of_used_kinds | 정지(1 GB 하한) | 972 |
| 2 | test_block_grid_products_and_budget_gate | 정지 | 982 |
| 3 | test_gain_target_and_verdict | 정지 | 982 |
| 4 | test_area_lower_bound_from_declared_values | 정지 | 1021 |
| 5 | test_diagnostic_mode_keeps_stage_a_exit_code | 정지 | 969 |

- 5개 모두 시작 여유 약 4.9~5.0 GB 에서 단독으로 약 4 GB 를 써 하한에 닿았다 = 최고치는 프로세스 안 누적이 아니라 test 하나가(folded_cascode 세션 fixture·실 LUT 적재) 내는 값이다. 나눠도 낮아지지 않는다.
- 통과·실패 판정 없음(전부 정지). 통과로 세지 않으므로 V1 은 N/A 유지. 실패가 없어 base 귀속 실행은 하지 않았다.
- 필요: 여유 약 6 GB 이상의 환경에서 `integration/test_stage_b_library.py -k folded_cascode` 1회, 또는 사용자가 하한을 다시 정하는 결정(ngcc stage_b 5 passed 와 folded s0·g10 통과로 간접 증거는 있음).


### 재판정 4 -- folded_cascode stage_b 단일 프로세스 (여유 5.48 GB 시작)
re-verdict: Major 0

- `integration/test_stage_b_library.py --run-slow -k folded_cascode -p no:cacheprovider`, 병합본 `8a2a0c7e`, 시작 여유 5484 MB(5300 MB 이상 확인), 감시 루프 1 GB 하한.
- 결과: **5 passed**, 63 deselected, 297 s. 정지 없음. 최저 여유 **1577 MB**.
- 2회로 연기 전체: folded_cascode stage_b 5 passed·s0 7 passed 2 failed·g10 1 passed, ngcc_3stage_ff stage_b 5 passed·s0 1 passed 1 failed·g10 1 passed. 실패 3건은 base 에서도 동일(재판정 2), 오케스트레이터가 LA-1 재점검 입력으로 수용.
- **V1 확정: PASS**(LM-1e 귀속 실패 0; 실패 3건 기존·수용 명기). Major 0.
