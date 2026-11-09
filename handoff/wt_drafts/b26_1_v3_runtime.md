# B26-1 V3 실행 시간과 실행 방식 (조사, 2026-10-07)

읽기 전용 조사다. 게이트 도구는 바꾸지 않았다. 측정 scratch `C:/g427`(TMP·TEMP 그 아래, `core.autocrlf=false` 복제)는 측정 뒤 지웠다.
대상: gate master `6df4bd7fd9920e752da4b16bff9b0513caf78362` 판 `tools/gates/mutate_changed.py`, brief `_drafts/b26_1_briefs.md` §0.3·§2.2, `_drafts/b26_1_carry.sh` check(V3 블록 241~290행).

## 1. 도구가 지원하는 것 (6df4bd7 원문)

| 질문 | 답 | 근거(원문 위치) |
|---|---|---|
| 병렬 실행 | **없다.** 변이 루프는 `for path in targets` → `for q, fn in changed_defs(...)` → `for opname, ... in mutants(...)` 한 줄기다. 변이마다 같은 복제본 파일을 고쳐 쓰고(`fpath`) `run_tests`를 동기 호출한 뒤 되돌린다 -- 같은 복제본 위의 병렬은 구조상 불가능 | `main` 663~730행 |
| shard·대상 거르기 | **없다.** 인자는 `--root --base --head --pytest-ini --python --timeout --out --gmid-phase --gmid-strict` 뿐. 대상은 `git diff --name-only base head`가 정한다 | 599~610·618행 |
| resume | **없다.** `--out`은 레코드마다 `open(..., "a")`로 덧붙이기만 하고 읽지 않는다. 이미 있는 id를 건너뛰는 코드 없음. 다시 돌리면 같은 id가 다시 적힌다(carry check '`--out` id 중복' 단언에 걸린다) | 697~730행 |
| 판정 JSON | 끝까지 돈 **한 실행**만 stdout 한 줄로 낸다. 중간에 죽으면 판정 JSON이 없다(`finally`에서 임시 복제본 `gmid-v3-*`도 지운다) | 738~746행 |
| 변이별 기록 | `--out`에 `{"id","result":"not_targeted"}` / exempt 레코드 / `{"id","result":"killed","exit":코드 또는 "timeout"}` / `{"id","result":"survived","tests":[...]}` | 697~730행 |
| 고정 비용 | 인벤토리가 다른 def 묶음마다 **기준 실행 1회**(변이 없는 인벤토리 전체, `-x`가 있어도 전부 통과하므로 끝까지 돈다) | 678~684행 |
| 변이 상한 | `--timeout` 기본 600초. 넘으면 `"timeout"` = **killed로 센다** | 605·659~662·720~726행 |

결론 (1)·(2): 도구 자체로는 병렬·분할·이어 돌리기가 모두 불가능하다. 여러 번 나눠 돌리면 (a) 실행마다 전체 대상을 처음부터 다시 돌고, (b) 판정 JSON이 실행마다 따로 나오며 `mutants`·`killed`·`targets_by_def`가 그 실행 몫이 아니고, (c) `--out`에 id가 중복된다. carry check(`len(run) == v["mutants"]`, id 중복 금지, `targets_by_def` 합 = (`mutants`, `not_targeted`), 생존 = U3 1개)는 **끝까지 돈 단일 실행 출력만** 통과한다. 도구를 고치지 않고 '도구가 스스로 이어 받는' 분할은 없다.

## 2. 실측 (현재 트리 6df4bd7, B26-1 대상 def 30개)

방법: 도구 함수를 읽기 전용으로 import(`reachability.build_graph`·`mutate_changed.inventory`·`mutants`·`_replace_def`·`test_nodeid`)하고, pytest는 도구 `run_tests`와 같은 형태(`$PY -P -m pytest -c pytest_gate.ini --rootdir --confcutdir -x -q -p no:cacheprovider --gmid-phase=3 --gmid-strict= <인벤토리 node>`, `PYTHONPYCACHEPREFIX`·`PYTHONDONTWRITEBYTECODE=1`, timeout 600)로 실행했다. K1은 아직 없으므로 대상 def는 card 'V3 계획' 1의 def 목록(새 def `rail_declaration`·중첩 `classify` 제외 30개)을 6df4bd7 판으로 썼다. 기계 18 논리 코어, 측정 중 다른 agent 부하 있음(통제 안 함).

### 2.1 그래프·인벤토리
* `build_graph`(head 트리) 40.5초, test 노드 591. 30 def의 인벤토리 크기 64~172 test 함수, **서로 다른 인벤토리 21종**, 합집합 192 함수.
  (`_metric_kcl_residual`은 0 -- card 'V3 계획' 4의 이름 직접 호출 test가 K1에서 1 이상으로 만든다.)
* `make_clone` 상당(clone `--no-local --no-hardlinks` + checkout) 27초.

### 2.2 인벤토리 전체 실행 시간 (= 기준 실행 1회 = 생존 변이 1개의 비용)
합집합 192 함수(273 항목) 한 번 실행 216.9초(273 passed, 3 xfailed). `--durations=0`으로 인벤토리별 합을 내면 **21종 모두 187.7~199.5초**다 --
느린 test 다섯(`test_probe_parasitic_pm_all_circuits` 37.7초, `test_s157_M1_known_limitation` 32.2초, `test_b34_c8_restored_values_equal_fresh_process` 27.5초, `test_s157_M1` 20.1초, `test_ts6_probe_relocate::test_base_blob_reader_reads_the_base_tree` 11.9초)가 거의 모든 인벤토리에 들어 있기 때문이다.
**기준 실행 21종 합 = 3,855초(약 64분) + 프로세스 시작 몫.** 이것은 변이 수와 무관한 고정 비용이다.

### 2.3 변이 29개 실측 (5개 지정 + 24개 card def별 대상 수 가중 무작위, seed 20261007)

| 결과 | 수 | 초(개별) | 평균 |
|---|---|---|---|
| killed | 19 | 7.9, 9.1, 9.5, 9.7, 10.4, 10.8, 11.1, 11.2, 11.6, 13.0, 13.1, 13.7, 15.5, 16.0, 24.6, 83.3, 108.5, 112.5, 187.2 | **35.7**(중앙값 13.0) |
| survived | 9 | 155.1, 159.3, 162.8, 169.9, 178.9, 179.2, 188.3, 198.9, 263.0 | 184 |
| timeout(= killed로 셈) | 1 | 600.4 (`kcl_series_union` 중첩 `find`의 `while` 본문 `x = parent[x]` 삭제 → 무한 루프) | 600 |

주의: 무작위 24개는 **대상 밖 변이를 포함**한다(K1이 없어 대상 분류를 할 수 없다). 그래서 생존 비율(9/29)은 B26-1 대상 집합의 비율이 아니다 -- card 계획상 대상 299 중 생존 기대는 1(U3 `range` const−)이고 나머지는 killed다. 시간 추정에는 **killed 시간 분포**와 **생존·timeout 단가**만 쓴다.
대상 def 중 `while`이 있는 것: `l_sharing_classes`·`_build_theta_evaluator`·`_fixup_euler_blocked_rows`·`refine_differential_and_mirror_relations`·`kcl_series_union`·`audit_vertical_stack_id_vs_kcl`·`propose_vertical_stack_id_gap_fill` -- 이 본문의 삭제·비교 뒤집기가 대상이면 변이 하나에 600초가 든다.

### 2.4 attempt-1 V3(`--base B1 --head K1`) 소요 추정

T ≈ clone 0.5분 + 그래프 1분 + 기준 실행(D종 × 약 195초) + Σ 대상 변이(killed 시간) + 생존 1 × 약 200초 + timeout 수 × 600초

| 경우 | 기준 실행(D ≈ 23: 21 + `rail_declaration`·`classify`가 새 인벤토리를 만들 수 있음) | 대상 299 | 합 |
|---|---|---|---|
| 낙관(모든 대상이 앞쪽 test에서 죽음, 10초) | 약 75분 | 약 50분 | **약 2.1시간** |
| 중앙(실측 killed 평균 35.7초) | 약 75분 | 약 3.0시간 | **약 4.3시간** |
| 비관(무작위 killed 평균 45초 + timeout 3개) | 약 75분 | 약 3.7시간 + 30분 | **약 5.5시간** |
| 상한(모든 대상이 인벤토리 끝까지 -- card '상한 16.0 h'과 같은 뜻) | 약 75분 | 299 × 약 195초 | 약 17.5시간 |

**어느 경우든 2시간(Bash `run_in_background` 상한 7,200,000 ms; Monitor는 최대 30분)을 넘는다.** 낙관 경우조차 기준 실행 고정 비용 75분 때문에 넘는다.
2차 시도 V3(§3, `--base B2 --head M`)도 같은 대상·같은 인벤토리라 같은 규모다.

brief §0.3 정정: B34 선례 '12개에 1202초 = 변이당 약 100초'는 단가가 아니라 **기준 실행 몫이 큰 총합**이다(B34 대상 def 4개의 인벤토리 기준 실행 몇 종 × 약 190초 + killed 12개). 그래서 '300개 × 100초 = 8시간'은 근거가 다르지만, 결론(2시간 초과)은 이 실측으로도 같다.
brief §2.2 ①의 추정법('인벤토리 기준 실행 시간 × 대상 수')은 **상한**(약 17.5시간)을 내므로 멈춤 판단에는 쓸 수 있으나 실제 소요로 보고하면 안 된다 -- 이 문서의 식(고정 기준 실행 + killed 분포)을 쓰는 것이 맞다.

## 3. 설계 05·계획이 V3 실행 방식에 대해 정한 것

* design 05 §10 머리: "판정은 JSON 한 줄로 표준출력, exit 0/1/2. 모두 **격리 복제본**(§12-7)에서 돈다." §10 V3 행 ①~⑤: 대상·연산자·인벤토리·"변이마다 `--head` 커밋의 격리 복제본 … 그 test만"·생존 FAIL·면제. **실행 시간·병렬·분할·백그라운드 방식에 대한 규정은 없다.**
* 계획 N4.2 V3 행(841행): 같은 내용, 시간 규정 없음. design 05 26행: V3~V7 도구는 스크립트 형태(`$PY <경로>/mutate_changed.py`, `-P` 없음).
* spec card 'V3 계획' 2·'두 번 시도 절차' 예상 비용(464행): V3 '약 1시간 45분'은 **12개 병렬 복제 모의 측정값**이며 게이트 도구 실행 시간이 아니다(CPU 합 20.9 h).
* 판정 근거로 인정되는 것: carry check와 brief §0.3이 **도구 판정 JSON 그대로**를 요구한다. 병렬 복제(`v3_replica` 류) 결과는 대신할 수 없다.
* 실행 규율: 사용자 memory '장시간 실행은 run_in_background:true로 -- 수동 `&`·`nohup` 금지'(수동 백그라운드가 9~40분에 끊긴 사례), brief §0.3 '2시간 넘을 것으로 보이면 띄우기 전에 멈추고 보고(오케스트레이터가 실행 방식을 정한다)'.

즉 '도구 원출력 한 벌을 2시간 넘게 한 프로세스로 얻는 방법'은 문서 어디에도 정해져 있지 않다 -- **오케스트레이터 결정 + 사용자 승인(실행 규율 예외)** 사항이다.

## 4. 선택지

| # | 방식 | 증거(도구 원출력 그대로) | 약화 | 비용·위험 | 판단 |
|---|---|---|---|---|---|
| A | 도구를 **수정 없이 한 번**, harness 프로세스 트리 밖에서 띄운다(Windows 프로세스 생성: `Invoke-CimMethod Win32_Process Create` 또는 `schtasks /create /sc once` + `/run`). 래퍼 `.cmd`가 stdout → `attempt1_v3.json`, stderr → `out/attempt1_v3.stderr.txt`, 끝에 exit 코드 → `out/attempt1_v3.rc`. harness는 `run_in_background` 대기(각 < 2시간, 다시 걸기)로 rc 파일·PID 생존을 본다 | 그대로(단일 실행, `--out` 그대로) | 없음 | 사용자 승인 필요(memory 규율·brief '수동 백그라운드 금지'의 예외). 띄우는 방식이 이 환경에서 harness 종료·세션 종료를 견디는지 **미검증**(이번 조사에서 시스템 변경이 되는 시험은 하지 않았다) | **권고** |
| B | 게이트 도구 변경 card(`--jobs N` 복제본 N개 병렬, 또는 `--resume`: `--out` 기존 id를 읽어 건너뛰고 판정 JSON을 `--out` 전체에서 다시 계산) | 변경 뒤 도구 원출력 | 없음(설계에 따라) | gate card·red team·승인·병합이 B26-1 착수 base(B1)보다 먼저 와야 함 → 이미 있는 `role/test/20260930-b26-rail-accessor-set`(T1) 다시 하기. 18코어에서 `--jobs 6`이면 1시간 안팎으로 줄 것(추정) | 백로그(향후 V3 전반) |
| C | 대상 몫으로 여러 번 나눠 돌리기 | 실행마다 판정 JSON이 따로 나옴, `--out` id 중복 | -- | 6df4bd7 도구에 대상 거르기·resume가 없어 불가능, carry check 불통 | 기각 |
| D | `PYTEST_ADDOPTS`로 pytest 안 병렬(xdist) | 도구 출력이지만 test 실행 조건이 게이트 정의와 다름 | 판정 조건 변경 | `xdist` 미설치(`ModuleNotFoundError`), 설치는 패키지 정책·승인, `-x`·conftest 상태 공유 영향 미검증 | 기각 |
| E | `--timeout`을 낮춤 | -- | **약화**(timeout = killed로 셈 → 생존을 죽음으로 바꿀 수 있다) | -- | 기각 |
| F | 2시간 안에 끝나기를 바라고 그대로 run_in_background | 끊기면 판정 JSON 없음 | -- | 추정상 모든 경우 초과, 끊기면 `--out` 지우고 처음부터 | 기각 |

## 5. 권고 실행 계획 (A)

1. **승인 질문 1건**(오케스트레이터 → 사용자): "B26-1 V3(1차 `--head K1`, 2차 `--head M` 두 번, 각 추정 2~5.5시간, 중앙 약 4.3시간)를 게이트 도구 수정 없이 단일 실행으로 얻기 위해, harness 2시간 상한 밖에서 Windows 프로세스로 띄우고 harness는 대기 명령으로 추적하는 예외를 허용하는가." 기본안 = 허용(도구 원출력·판정 규칙 불변). 거부되면 B(게이트 card) 또는 대기.
2. **띄우기 전 확인**(auditor 2.2 ① 대체): K1 복제본에서 대상 수·인벤토리 종 수 D만 도구 함수로 세고(그래프 1분 이내), 위 식으로 소요를 적는다. 상한 17.5시간 같은 값은 '상한'이라고 표시.
3. **실행**: brief §2.2 ② 명령 그대로를 래퍼 `C:/g412/scripts/v3_run.cmd`에 리터럴로 적는다(`set TMP=C:\g412\tmp` 등 env 포함, `rm -f` 대응 `del` 먼저). 래퍼 마지막 줄이 `echo %ERRORLEVEL% > C:\g412\out\attempt1_v3.rc`. 시작 시각·PID를 `out/attempt1_v3.pid`에 적는다.
4. **추적**(harness가 직접): `run_in_background` + 상한 7,000,000 ms의 대기 명령 -- rc 파일이 생기면 끝, PID가 없는데 rc가 없으면 '비정상 종료'로 끝(침묵 ≠ 성공). 상한에 닿으면 같은 대기를 다시 건다. 중간 진행은 `--out` 줄 수로만 본다(판정 아님).
5. **끝난 뒤**: rc ∈ {0,1}, `attempt1_v3.json` 한 줄 JSON, carry check 단언을 미리 스스로 대조(`len(run) == mutants`, id 중복 0, `targets_by_def` 합). `--out`의 `"exit": "timeout"` killed 레코드는 id를 나열해 보고(아래 6).
6. **부하 주의(판정 무결성)**: timeout은 killed로 센다. 측정에서 생존 변이 하나가 155~263초였으므로, 동시에 다른 pytest 작업이 많으면 생존 변이가 600초를 넘어 **거짓 killed**가 될 수 있다. V3 실행 동안 같은 기계의 병렬 agent pytest 수를 줄이고, timeout 레코드가 있으면 그 변이를 따로 재현해 진짜 무한 루프인지 확인한 뒤 보고한다.
7. 중간에 끊기면 brief대로 `--out`을 지우고 처음부터(이어 붙이기 금지 -- id 중복).
8. 2차 시도 V3(§3 판정 기록 표 V3 행)에도 같은 방식이 필요하다 -- 승인 질문에 함께 넣는다.

## 6. 측정 원자료 요약 (scratch 삭제 전 옮김)

* 인벤토리 크기(6df4bd7): SR `true_current_mirror_groups`·`l_sharing_classes`·`_build_theta_evaluator`·`optimize_full_circuit_budget`·`_evaluate_row_split` 64, `resolve_stack_layout` 66, `run_topology_pipeline_with_finger_fixup` 65, `_fixup_euler_blocked_rows`·`run_matching_safety_with_finger_growth` 77, `_metric_kcl_residual` 0; SD `find_matching_candidates` 160, `find_differential_pair_candidates`·`_diff_pair_layer1_groups` 164, `_propose_gm_id_roles`·`_propose_L_roles`·`refine_differential_and_mirror_relations` 161, `check_symmetry_dispositions` 154, `kcl_series_union` 87, `_kcl_and_matching_edges` 172, `audit_vertical_stack_id_vs_kcl` 68, `propose_vertical_stack_id_gap_fill` 156, `propose_device_roles_gap_fill` 152, `run_full_circuit_audit` 72, `_kcl_branch_map`·`_branch_composite_pair` 85, `_composite_collapse_for_crossover` 80, `find_min_crossover_layout_with_branch_composite` 79, `repair_matching_safety` 84, `load_topology` 151, `run_full_circuit_audit_from_topology` 71.
* 변이 29개(def, 연산자, 인벤토리, exit, 초): 지정 5 -- `propose_device_roles_gap_fill` stmt_delete body[12] 152 1 10.4 / `find_differential_pair_candidates` cmp_flip(`_RAIL_NETS` 비교) 164 1 9.7 / `run_matching_safety_with_finger_growth` early_return 77 1 7.9 / `_build_theta_evaluator` stmt_delete body[25] 64 1 9.1 / `propose_device_roles_gap_fill` early_return 152 1 11.1. 무작위 24 -- 2.3 표.
* 측정 스크립트(`inv.py`·`dur.py`·`agg.py`·`mut.py`·`mut_rand.py`)는 scratch와 함께 지웠다(필요하면 이 문서 2절 방법으로 재현).
