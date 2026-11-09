# Phase 2 DoD 사전 점검 (gate `master` cd64170, 2026-09-30)

측정: 읽기 전용. 격리 복제본 `C:/g19/r`(`--no-hardlinks --no-local`, origin 제거, cd64170 detach), 게이트 캐시 = `git archive cd64170 tools/gates` → `C:/g19/cache`.
Python `C:/Python314/python.exe -B`. 원출력은 `C:/g19/out/*.txt`(작업 끝에 C:/g19 삭제 -- 수치는 아래에 옮겨 둠). 메인 저장소는 바꾸지 않았다.
이 문서는 **사전 점검**이다. DoD 판정 수치는 auditor가 독립으로 다시 잰다(작성자≠검증자). 여기 수치를 DoD 보고 수치로 쓰면 안 된다.

---

## 1. 원문 인용

### design `docs/02-design/features/gain-budget-gmid-sizing.20-dead-code-dup.design.md` §10 (6398a28 정정 반영본, 211-222행)

213행: "auditor가 Phase 2 마지막 card 병합본의 격리 복제본 `<iso>`에서 실행한다. `PT`는 `10-test-separation` §10 정의를 그대로 쓴다."

| 행 | ID | N6.2 `2` 조건 | 명령 | 통과 기준 |
|---|---|---|---|---|
| 217 | E0 | 승인된 D 목록 처리 | `$PY <iso>/skills/analog-gmid-design/assets/tests/tools/reg_check.py --registry <iso>/docs/03-analysis/gain-budget-gmid-sizing.function-registry.md --root <iso>` (P7이 만든다) | exit 0: §7 모든 행이 엔진에 실재(삭제·이관 항목 0), `처리` 열이 '보류(Phase n)' 형식, §1 집계 = §7 행 수. (2026-09-30 정정: U-02 승인 기록에 '보류' 목록이 없어 '승인표 보류 집합과 같음'을 처리 열 형식 검사로 기계화, 도구는 게이트 변경을 피해 tests/tools에 둔다 -- spec card `20260930-registry-grade-fix`) |
| 218 | E1 | DUP 차등 test PASS 후 중복 정의 삭제 | `PT <iso>/…/tests/contracts -k "dup_w_calc or dup_kcl_edges"`(`-k "dup_"`는 P4의 `test_probe_dup_scan.py`까지 잡는다) 그리고 `.ai/verification/20260930-dup-w-calc.json`·`.ai/verification/20260930-p9-kcl-edges.json`의 `checks.V2` | 차등 test PASS(실패 0, 수집 1개 이상), 두 판정 기록의 V2 PASS(P8 = 식 함수 비트 동일·E-LIB·E-INST, P9 = DIFF-DUP·E-LIB·E-INST가 base = 병합본). (2026-09-30 정정 … 중복 정의 삭제의 기계 판정은 card별 계약이다: P8 = W 식 인라인 0(`20260930-dup-w-calc` 계약 2), P9 = `kcl_series_union` 본문의 `_RAIL_NETS` 참조·`.source`/`.drain` 접근 0과 정본 호출(`20260930-p9-kcl-edges` 계약 1)) |
| 219 | E2 | probe 엔진 식 재구현 0 | `$PY <iso>/skills/analog-gmid-design/assets/tests/tools/engine_dup_scan.py --root <iso>` | exit 0, 발견 0 |
| 220 | E3 | DF-23 전수 목록 | `git -C <iso> cat-file -e HEAD:docs/03-analysis/gain-budget-gmid-sizing-20-dead-code-dup/df23_inventory.json` 와 목록 항목 수 대조 | 목록이 있고 항목마다 담당 Phase가 적혀 있다 |
| 221 | E5 | 미래 topology 커버 | 합성 topology(라이브러리 밖 이름·넷)로 `PT <iso>/…/tests/unit -k new_topology` | PASS -- 로드·파이프라인 동일, 삭제한 선언 키는 `ValueError`, 일반 경로 선언은 값 산출 |
| 222 | E4 | 동작 보존 | `PT` 전체(실패 0)와 E-LIB·E-INST 재측정 | Phase 1 DoD와 같은 값(회로 9/9 로드, instance.json 해시 동일) |

(E1 행의 괄호 속 정정 사유 중간 문장은 길이 때문에 "…"로 줄였다. 원문은 218행.)

### 계획 `docs/01-plan/features/gain-budget-gmid-sizing.plan.md`

* N6.2 Phase 2 행(**1017행**): "| 2 | 승인된 D 목록 처리, DUP마다 옛 함수 대 정본 차등 test(실행 가능한 library 회로 입력 전수 출력 동일) PASS 후 옛 함수 삭제, 레지스트리 갱신, probe 엔진 식 재구현 0, DF-23 전수 목록(소자·넷·회로 이름 리터럴과 topology 파일 경로. DF-29~DF-34의 위치가 목록에 들어 있고 항목마다 담당 Phase가 적혀 있음) |"
* 참고 N6.1 Phase 2 행(999행): "| 2 | TS6, 레지스트리 등급 D 삭제(배선을 고른 항목은 Phase 4로), 레지스트리 §2에서 "행동 보존 통합 가능"인 DUP 통합, DF-23 전수 목록(…DF-29~DF-34 포함) | equivalence(TS6은 test-only, 운영 도구 이동은 code·test 두 커밋) | U-02 | `20-dead-code-dup` |"
* 참고 DF-23 행(933행) 담당 Phase 열: "2(전수 목록·레지스트리 기록), 4(일반 규칙으로 교체)".
* 참고 N6.3 공통(1028행~): "auditor 판정 기록 PASS(N4.2 도입 표 기준), merge gate(EL4) 통과, 동작 변경 spec card마다 거부해야 할 입력의 test 존재." / "동작 보존 Phase(1~3)는 실행 가능한 회로 전부에서 equivalence".

---

## 2. 지금(cd64170) 측정한 결과

| ID | 판정(지금) | 증거 | 언제 충족되는가 |
|---|---|---|---|
| E0 | **PASS** | `reg_check: 발견 0`, exit 0. 레지스트리 §7 = SR 9·SD 15·기타 1 = 25행, 전부 `보류(Phase 3/4/6a)`. §1 집계 D 9/15/1과 일치 | 이미 충족. P9가 레지스트리 §2·§6·§4·§5를 고쳐도 §7은 바뀌지 않는다(P9 계약 8(d)가 exit 0 재확인) |
| E1 | **아직 측정 불가**(절반 충족) | `PT tests/contracts -k "dup_w_calc or dup_kcl_edges"` → **106 passed, 707 deselected, exit 0**. 106건 전부 `test_dup_w_calc.py`이고 `dup_kcl_edges`는 0건 수집(파일 없음). `20260930-dup-w-calc.json` V2 = PASS. `20260930-p9-kcl-edges.json` **없음** | **P9 뒤**(test `test_dup_kcl_edges.py` + 판정 기록 V2) |
| E2 | **PASS**(범위 조건부 -- §2.1 관찰 A) | exit 0. 발견 1건 = `tests/probes/probe_mirror_gain_ranking.py:183` `lut-private`, `"exempt": true`(승인 `20260929-p4-scan-exempt`). 면제 아닌 발견 0 | 이미 충족. 단 관찰 A |
| E3 | **FAIL** | 파일 있음(cat-file exit 0). 590항목(메시지뿐 324·동작을 정함 266), 최상위 키 `scope·method·vocabulary·totals·items` -- **`phase` 필드를 가진 항목 0/590**, `measured_at` 없음(측정 1e2e243). `plan_mapping` 분포: `신규(계획 DF-29~…` 370, DF-29 62(+신규 위치 10), DF-31 57+7, DF-30 40+7+4, DF-34 20, DF-33 12, DF-32 1 | **P10 뒤**(재측정 목록 + 항목마다 `phase`) |
| E5 | **PASS**(명령 경로 결함 -- 관찰 B) | `PT tests/unit -k new_topology` → 9 passed, exit 0. 9건은 전부 **`tests/contracts/`** 소속: `test_d_delete_dead.py::test_unregistered_metric_type_is_rejected[new_topology_future_metric]` 1, `test_d_delete_telescopic.py::test_deleted_family_is_rejected_on_new_topology[…]` 6, `::test_general_path_yields_value_on_new_topology[cmrr_like/psrr_like]` 2 | 이미 충족. P9·P10은 삭제가 없어 NEW-TOPO를 더하지 않는다 |
| E4 | **부분 측정 -- 기준값 미정**(관찰 C) | `PT` 전체(`--gmid-phase=2 --gmid-strict=`): **798 passed, 15 xfailed, 실패·오류 0, exit 0**(234 s). `PT --gmid-dod`: 798 passed, 15 xfailed, exit 0(표식 Phase 2인 IC 케이스 없음 -- `grep 'phase="2"'` 0). E-LIB 로드: library 10파일 중 9 로드 OK, `_TEMPLATE` AttributeError(회로 아님) → 9/9. E-INST는 지금 재지 않았다(비교 기준값이 없음 -- 관찰 C) | P10 뒤 마지막 병합본에서 auditor. 기준값 해석이 먼저 필요(§4 결정 D1) |

N6.3 공통: Phase 2 card 판정 기록 13건 전부 V1~V10 PASS 또는 N/A(아래 §3). 엔진·하네스·library를 바꾼 da03c0e..cd64170의 비병합 커밋 25개는 전부 card의 `Role: code/test` 커밋이다(카드 밖 엔진 변경 0 -- 사슬 equivalence 논거가 성립).

### 2.1 관찰(판정에 걸리는 것)

**A. E2 범위 밖에 남은 probe 1개 -- `A/tests/probe_physical_consistency.py`(P3c 보류분)**
* P2는 32개를 `tests/probes/`로 옮겼고 P3a·P3b가 6개를 `unit/test_probe_*.py`로 승격했다. 남은 1개(P3c 보류, `.ai/context.md` 14938 백로그 B21)는 **tests 루트에 그대로** 있다 -- design §2.1(승격하지 않는 probe는 `tests/probes/`)과 §5.1("승격에서 빼고 진단으로 남긴다") 어느 쪽 상태도 아니다.
* `engine_dup_scan.py`는 `tests/probes/**`만 본다(PROBES_REL). 이 파일을 임시 루트의 `probes/`에 복사해 스캐너를 돌리면 **발견 1건, exit 1**: `probe_physical_consistency.py:40 rail-set`(레일 집합 재선언). 즉 E2 문구대로는 PASS지만 N6.2 "probe 엔진 식 재구현 0"은 이 1건이 남는다.
* 같은 자리의 `A/tests/apply_b19p_mirror_wiring.py`(probe가 아닌 B19' 적용 스크립트, probe 목록 42개에 없음)도 스캐너 기준 2건(`mirror-key`:41, `diode-inline`:48). TS6 범위 밖 -- 백로그 후보일 뿐 DoD 대상 아님.

**B. E5 명령 경로**: new_topology test는 `tests/contracts/`에 있다. `PT`가 이미 `assets/tests`를 인자로 가져 `tests/unit`를 덧붙여도 합집합이라 잡힌다(Phase 1 백로그 B13과 같은 현상). 판정 영향 없음. DoD 기록에 "9건 전부 contracts" 한 줄로 적으면 된다(design 문구 정정은 선택).

**C. E4 기준값 "Phase 1 DoD와 같은 값"은 그대로 잴 수 없다**
* `phase1-dod.md`(781f405)에는 E-LIB·E-INST 값이 **없다**(D1은 TS1 stdout 해시). 비교할 Phase 1 쪽 숫자가 기록에 없다.
* Phase 2 안에서 instance.json이 **의도적으로 바뀌었다**: DF-36(`20260930-df36-instance-relpath`, red-green)이 `topology_ref`를 저장소 상대 경로로 바꿨다. 판정 기록은 "topology_ref 뺀 해시 = base"로 판정했다. 그래서 raw 해시 동일은 원리상 성립하지 않는다.
* Phase 1 끝(da03c0e)의 `run_harness.py`는 메인 저장소 절대 경로 리터럴을 가진다(DF-35 이전). 그대로 돌리면 **메인 저장소 workspaces에 쓴다** -- DF-35 auditor가 쓴 base 모드(리터럴을 복제본 경로로 치환)가 필요하다.

**D. E1 "수집 1개 이상"은 합계 기준**: 지금도 106건이라 문구상 충족처럼 보인다. P9 뒤에는 **모듈별로** `test_dup_w_calc.py` ≥1·`test_dup_kcl_edges.py` ≥1을 따로 세야 E1의 뜻(두 DUP 각각 차등 PASS)이 된다. auditor 브리핑에 넣으면 된다(결정 아님).

**E. N6.2 1017행 "PASS 후 옛 함수 삭제" 문구**: P8은 인라인 식 18곳 제거(옛 함수 없음), P9는 `kcl_series_union` 유지 + 본문 중복 엣지 정의 제거다. 문구와 사실이 다르지만 승인 `20260930-p9-e1-correction`이 E1(측정식)을 정정했고 "덮지 않는 것: 계획 N6.2 문장"으로 명시했다. 계획 N6.2 머리글 "측정 명령은 design 문서에 고정"에 따라 E1이 측정식이므로 DoD 판정은 E1로 한다. 계획 문장 손질은 Phase 2 완료 기록 커밋에서 오케스트레이터 문서 정정으로 하거나 그대로 둔다(결정 아님 -- 기준 변경이 아니고 E1이 이미 승인됨).

**F. DF-23 '레지스트리 기록'(계획 933행 담당 2)은 E3가 재지 않는다**: P10 초안은 이것을 P10b(red-green, code-author)로 분리하고 design §8에 행을 더한다. N6.2 1017행과 E3는 레지스트리 기록을 요구하지 않지만 DF-23 행은 Phase 2 몫으로 적는다. 원칙 기본안: **P10b까지 Phase 2 안에서 끝낸 뒤 DoD**(계획 DF 행을 따른다). 그러면 마지막 card = P10b.

---

## 3. Phase 2 card와 판정 기록

| design §8 | card id | 유형 | 판정(V1~V10) | 판정 기록 커밋(audit) |
|---|---|---|---|---|
| P1 | 20260923-probe-dead-delete | test-only | PASS(V7 PASS, V8·V9 N/A) | 1cdebc9 |
| P2 | 20260923-probe-relocate | equivalence | PASS(V8·V9 N/A) | af3416a |
| P3(a) | 20260923-probe-promote-clean | test-only | PASS(V8·V9 N/A) | db25f7b |
| P3(b) | 20260923-probe-promote-differential | test-only | PASS(V8·V9 N/A) | 5e1ca79 |
| P3(c) | 20260923-probe-promote-consistency | test-only | **기록 없음 -- 보류**(2026-09-29 사용자 "보류, P5로 진행", 백로그 B21 Phase 4) | -- |
| P4 | 20260929-probe-engine-dup | red-green | PASS(V8·V9 N/A) | a53b8ac |
| P5 | 20260923-d-delete-dead | equivalence | PASS(V8·V9 N/A) | 1258efe |
| P5b | 20260923-d-delete-telescopic | equivalence | PASS(V8·V9 N/A) | d7bce7a |
| P6 | 20260930-d-move-tests | red-green | PASS(V8·V9 N/A) | 4e0f325 |
| P7 | 20260930-registry-grade-fix | red-green | PASS(V8·V9 N/A) | df77a5f |
| P8 | 20260930-dup-w-calc | red-green | PASS(V8·V9 N/A) | 54dec6a |
| P9 | 20260930-p9-kcl-edges | equivalence | **미착수**(초안 `draft_p9.spec.md`) | -- |
| P10 | 20260930-p10-df23-inventory | test-only | **미착수**(초안 `draft_p10_b22.spec.md`) | -- |
| (P10b 제안) | df23-registry-record | red-green | 초안이 제안, design §8 행 없음 | -- |
| §8 밖 | 20260930-restore-plan-functions | red-green | PASS(V8·V9 N/A) | 4967a82 |
| §8 밖 | 20260930-df35-harness-paths | red-green | PASS(V8·V9 N/A) | 34bc75e |
| §8 밖 | 20260930-df36-instance-relpath | red-green | PASS(V8·V9 N/A) | 148bd6d |

`phase: 2` spec card 중 판정 기록이 없는 것은 **P3c 하나뿐**이다(P9·P10은 spec card가 아직 gate에 없음). `20260930-v3-history-clone`(B28, spec d99919c)은 `phase: 0.5` 게이트 변경이라 Phase 2 목록 밖이지만 판정 기록이 없다 -- Phase 2 DoD 대상은 아니나, DoD 측정이 쓰는 V3 도구를 바꾸므로 순서상 DoD 전에 끝내는 편이 깔끔하다(20260929-rejudge-cache도 phase 0.5, V1·V10 PASS 나머지 N/A).

**P3c와 DoD**: E0~E5와 N6.2 1017행 어디에도 probe 승격 조건은 없다. design §8 P3 행이 "승격 7개(또는 `probe_physical_consistency` 제외 6개)"를 허용하므로 P3 몫은 6개로 충족이다. 걸리는 것은 관찰 A(남은 probe가 `tests/probes/`로 가지도 않고 스캐너 범위 밖에 1건 재구현을 가진 채 남음) 하나다 → §4 결정 D2.

---

## 4. P10(또는 P10b) 뒤 'Phase 2 완료 판정' 절차 제안

선례: Phase 1 DoD는 spec card·판정 기록(.json) 없이 **auditor 독립 측정 → 오케스트레이터가 `docs/03-analysis/gain-budget-gmid-sizing-10-test-separation/phase1-dod.md`로 옮겨 적어 커밋**(781f405, "auditor 보고를 그대로 옮긴 것, 다시 계산하지 않음")했다. 계획 N6.1 "이전 Phase DoD PASS"도 기록 파일 형식을 따로 정하지 않는다. 그래서 **별도 audit card는 필요 없다**(design 20 §10도 "auditor가 … 실행한다"만 적는다). 같은 방식을 따른다.

1. **착수 조건**: P9·P10(·P10b) 판정 기록이 gate `master`에 있다. 가능하면 B28 `20260930-v3-history-clone`도 끝나 있다.
2. **auditor(gmid-verification-auditor)** 가 마지막 card 판정 기록 커밋 `<H>`에서 격리 복제본(`--no-hardlinks --no-local`, origin 제거, `core.longpaths=true`, detach)을 떠서 잰다. 게이트 캐시 = `<H>`의 `tools/gates`. 브리핑 가드 4줄(격리 경로·`git -C`·`set -e`·끝나면 reflog/status) 필수.
   * E0: reg_check exit 0.
   * E1: `PT tests/contracts -k "dup_w_calc or dup_kcl_edges" -rA` -- 실패 0, **모듈별 수집 수**(dup_w_calc ≥1, dup_kcl_edges ≥1), 두 판정 기록 `checks.V2.verdict == PASS`.
   * E2: engine_dup_scan exit 0, 면제 아닌 발견 0, 면제 목록(현재 1건)과 근거 승인 id. 관찰 A 처리(D2 결정대로).
   * E3: cat-file exit 0 + `len(items) == totals.n_items`, 모든 항목 `phase`가 닫힌 집합 원소, DF-29~DF-34 항목 존재(plan_mapping별 개수), `measured_at` 커밋의 엔진 blob = `<H>`의 엔진 blob인지(아니면 P10 뒤 엔진이 바뀐 것 -- P10b는 레지스트리만 바꾸므로 같아야 함). P10b를 했다면 레지스트리 DF-23 기록의 총계 = 목록 총계.
   * E5: `PT … -k new_topology -rA` PASS, 수집 케이스 목록(현재 9, 전부 contracts).
   * E4: `PT` 전체 + `PT --gmid-dod`(실패 0, 수집·passed·xfailed 수), E-LIB 9/9 로드와 `run_topology_pipeline` 출력, E-INST 두 회로(파일럿·folded_cascode) -- 기준값은 D1 결정대로.
   * N6.3: Phase 2 판정 기록 전부 V1~V10 PASS/N/A, card마다 merge·audit 커밋이 gate 조상에 있음, 엔진·하네스·library를 바꾼 커밋이 전부 card 커밋인지(`git log da03c0e..<H> --no-merges -- A/*.py workspaces/run_harness.py A/library/*.json`).
   * 판별력 대조(Phase 1 D2·D5 선례): E3는 P10 문서 커밋 직전(현재 cd64170과 같은 상태 -- phase 0/590)에서 FAIL, E1은 P9 전 커밋에서 dup_kcl_edges 0 수집임을 함께 적는다.
3. **오케스트레이터**가 auditor 보고를 그대로 옮겨 `docs/03-analysis/gain-budget-gmid-sizing-20-dead-code-dup/phase2-dod.md`(Phase 1과 같은 머리: 대상 커밋·측정 주체·환경, E0~E5 표, N6.3 공통, 남긴 관찰)로 커밋하고, `.ai/context.md`에 Python 바이너리 append로 한 줄 기록(삭제 0줄 확인). 수치는 다시 계산하지 않는다.
4. 그 커밋이 Phase 3 design 착수 조건("Phase 2 DoD PASS", `draft_phase3_design.md` 297행)의 인용 대상이 된다.

### 사용자 결정이 필요한 것 (실제 결정만)

**D1. E4 기준값 "Phase 1 DoD와 같은 값(… instance.json 해시 동일)"의 해석** -- 판정 기준 문구라 오케스트레이터가 혼자 바꿀 수 없다(E1 정정과 같은 성격, 승인 기록 `target_kind: diff`).
* 사실: Phase 1 DoD 기록에 E-LIB·E-INST 값이 없고, DF-36이 `topology_ref`를 의도적으로 바꿨다(판정 기록 PASS).
* 기본안: 기준을 "Phase 1 마지막 병합본 da03c0e와 Phase 2 마지막 병합본을 **같은 경로**에서 비교 -- E-LIB 9/9 로드·`run_topology_pipeline` 출력 동일, E-INST(파일럿·folded_cascode)는 `topology_ref`를 뺀 해시가 같고 `topology_ref`는 DF-36 계약 1 기대값"으로 정정. da03c0e 쪽 하네스는 DF-35 판정 기록의 base 모드(경로 리터럴을 복제본 경로로 치환)로 돌린다. `topology_ref` 제외는 DF-36 승인된 red-green 변경이라는 근거를 적는다.
* 대안: card별 equivalence 사슬(각 판정 기록의 E-LIB·E-INST base = 병합본 + 카드 밖 엔진 변경 0)로 갈음 -- 새 측정이 없어 싸지만 E4가 따로 재는 의미가 없어진다.

**D2. P3c 보류분 `probe_physical_consistency.py`를 Phase 2 DoD에서 어떻게 세는가**(Phase 3 design 초안 297행이 "Phase 2 쪽 결정"으로 넘긴 항목).
* 기본안(a): DoD는 E2 문구(`tests/probes/**`)대로 판정하고, DoD 기록 '남긴 관찰'에 "P3c 보류(B21, Phase 4) -- 파일은 tests 루트에 남고 스캐너 범위 밖 재구현 1건(rail-set)" 을 적는다. 추가 card 없음. 사용자 "보류" 결정과 맞고, 이 파일을 옮기면 P1/P3a 계약 test의 `rglob('probe_*.py')` 계수와 P3c spec card 계약 1 경로가 같이 흔들린다(P4 2차의 34≠33 dispute와 같은 위험).
* 대안(b): design §5.1대로 "승격 못 하면 진단으로" -- `tests/probes/`로 옮기고 rail-set을 정본 호출로 바꾸는 작은 test-only card를 DoD 전에 한다(P3c spec card 경로 개정 동반).

그 밖(E5 경로 표기, E1 모듈별 계수, N6.2 문구, P10b를 Phase 2 안에서 할지)은 원칙 기본안으로 정해지므로 결정 항목이 아니다. P10b는 계획 DF-23 행(담당 2)을 따라 Phase 2 안에서 하는 것이 기본안이다 -- 만약 Phase 3로 넘기려면 그때는 계획 행과 어긋나므로 사용자 확인이 필요하다.
