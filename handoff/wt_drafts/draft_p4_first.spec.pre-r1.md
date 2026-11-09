---
id: 20261002-d4-delete-unwired
phase: 4
evidence_type: equivalence
gate_change: no
approval: 20261002-40-defect-fixes-design
---
## 의도

Phase 4 design `40-defect-fixes`(초안 v0.9.8, 승인 전) §5.1 #2 `d4-delete-unwired`, §3.2·§3.3(`#2 ─> TS4(#5)`), 준비 자료 `_drafts/prep_deferred_rows.md` §3.2 D-1~D-4: 레지스트리 §7 `보류(Phase 4)` 행 중
**선언으로도 코드로도 운영 경로가 없는** 정의 6개를 지운다. 지울 코드를 고치지 않는다(DF-09는 식을 고치지 않고 삭제로 닫는다 -- DF-29 선례). A = `skills/analog-gmid-design/assets`.
위치는 **심볼**로 적는다 -- 이 card는 Phase 3(`30-module-split`) DoD 뒤에 쓰이므로 정의 파일은 F2 뒤 R-DEF 규칙(Phase 3 design §7.1)으로 다시 정한다('작성 전 실측' P3 절).

| 묶음 | 지우는 정의 | 운영 경로가 없는 근거(원칙) |
|---|---|---|
| D-1 | `estimate_area_budget` | 계획 DEC-79가 면적을 두 단계(탐색 축 Σ(W·L)+선언 수동소자 / 판정 축 레이아웃 면적)로만 정의한다 -- 이 함수의 packing-density 블렌딩은 제3 모델이다. 반환형 float인데 소비처로 적힌 `select_layout_tool(area_budget=)`은 문자열 `"generous"`만 본다. 입력 `area_priors`는 어느 `SPECS`·library에도 없다. 식 자체가 DF-09 결함(`(1−α)A + α(A/α) = (2−α)A`) |
| D-2 | `solve_diode_stack_current` | 선언으로 도달 불가(G-1). 적층 diode의 운영 해법은 `solve_stacked_diode_pair`(B25). 자기 docstring이 호출 규약 미검증을 적고 단조성을 검사하지 않는다. 일반 KVL 해는 N3.6·DEC-71(6b) 몫 |
| D-3 | `load_derived_bounds`, `derived_bounds_path` | 같은 유도값의 두 번째 저장 위치(DEC-68 '개념 하나에 저장 위치 하나'). 엔진은 topology 제약의 `_derived`만 읽는다(`resolve_constraint_references`). 계획 N3.13-5도 결과를 '선언에 `value`와 `_derived`'로 기록한다. 사이드카 `*.derived.json` 추적 파일 0, `value_from_achievable` 선언 library 회로 0 |
| D-4 | `check_multi_leaf_hub_parity`, `MultiLeafHubParityVerdict` | 정본 판정 `build_graph()`+`check_euler_condition()`과 항상 같은 답(기존 test S058이 3-leaf 64조합으로 확인) -- 정보가 없는 사본(정본 하나). 속도용 사전 스크리닝이라는 근거는 측정이 없다 |

함께: `test_ic5` `_DOMAIN_TABLE`의 D-4 행과 **D-5(`audit_vertical_stack_id_euler_feasibility`) 행**을 지운다(design §5.1 #2, F18 -- 표 수정을 이 card 한 번으로 묶어 V5 승인을 한 번만 받는다. D-5 **함수**는 W-2 배선과 함께 #41이 지운다).
지울 이름을 아직 읽는 곳(test 3개, 운영 도구 1개, 레지스트리, 참조 문서, 계획 DF-09·TS4 행)을 같은 card에서 정리한다(메모리 '함수 만들기 전 재사용 레지스트리 확인': 대체·삭제하면 같은 커밋에서 레지스트리 갱신).
동작 보존 변경이라 판정은 equivalence(E-LIB·E-INST·NEW-TOPO) + GONE이다.

## 관찰 가능한 계약

(범위 계약은 모두 **이 card `Change-Id` 커밋들의 diff**로 한정한다 -- 기준 커밋과 판정 대상 사이에 다른 card 커밋이 끼면 그 diff는 이 계약의 대상이 아니다.)

1. **삭제**: 의도 표의 정의 6개(함수 5, `@dataclass` 클래스 1)가 card base의 정의 파일에서 없어진다. 다른 정의는 지우지 않는다 -- 특히 아래는 **남고 동작이 같다**: `_invert_gm_id_for_current`(운영 호출자 `revalidate_finger_override`),
   `SemiEmpiricalGmIdLUT.vgs_for_gm_id`(운영 호출 다수), `find_hub_merge_candidates`, `build_graph`, `check_euler_condition`, `assign_finger_geometry`(인자 `area_priors`는 예약 필드로 시그니처에 남긴다 -- 백로그),
   `select_layout_tool`(인자 `area_budget` 그대로), `achievable_metric_bound`, `resolve_constraint_references`, `solve_stacked_diode_pair`, `audit_vertical_stack_id_euler_feasibility`(D-5 함수는 #41 몫).
2. **G-1(선언 도달 경로 없음)**: 6개 이름 어느 것도 엔진의 문자열 키 딕셔너리(`_METRICS_REGISTRY`·`_CMRR_ESTIMATOR_REGISTRY`·`_PSRR_ESTIMATOR_REGISTRY`·`_COMPENSATION_REGISTRY`·`_THETA_FEED_REGISTRY` 포함 전수 -- 정의 파일이 바뀌어도 `A/*.py` 전체에서 찾는다)의 값으로 등록돼 있지 않다(base에서 판정 -- 지우기 전에 도달 경로가 없음을 보인다).
3. **GONE(AST)**: 6개 이름의 정의·`Name`·`Attribute`·`import` 참조가 `A/*.py`, `workspaces/run_harness.py`, `A/tests/**`(`A/tests/tools/**` 포함)에서 0이다. 새 GONE test는 이 이름들을 **문자열 상수로만** 든다(import·호출·딕셔너리 값 금지 -- 기존 전수 스캔 test `test_d_delete_dead.py`·`test_d_delete_telescopic.py`·`test_d_move_tests.py`·`test_ts3_no_print_verdicts.py`와 V3 인벤토리 간선에 걸리지 않게).
4. **GONE(본문 언급)**: `A/*.py`와 `workspaces/run_harness.py`의 **원문 텍스트**(docstring·주석 포함)에서 6개 이름의 단어 일치(`\b<이름>\b`)가 0이다. 지금 언급하는 곳(card base에서 재측정 -- 심볼 기준, '작성 전 실측' 1):
   `SemiEmpiricalGmIdLUT.vgs_for_gm_id`·`_invert_gm_id_for_current`·`achievable_metric_bound`·`optimize_full_circuit_budget`의 docstring, `find_hub_merge_candidates`(2곳)·`assign_finger_geometry`·`search_shared_finger_w`·`select_layout_tool`의 docstring,
   그리고 `propagate_topology_forced_currents` 바로 위 절 머리 주석(`# 1.8) A/C 엔진 …`). 고칠 때 사실을 지어내지 않는다: 지운 함수를 가리키던 문장은 남는 정본(`build_graph()`+`check_euler_condition()`, `solve_stacked_diode_pair`, topology 제약 `_derived`)을 가리키거나 문장을 지운다.
   `achievable_metric_bound` docstring의 "프로세스를 넘는 재사용은 사이드카 파일이 한다"는 '선언의 `_derived`(운영 도구가 기록)'로 바꾼다(계약 5와 같은 사실).
5. **운영 도구 `A/tests/tools/derive_achievable_bounds.py`(code-author 경로)**: 사이드카 읽기(`load_derived_bounds`)와 쓰기(`derived_bounds_path` + 파일 쓰기 블록)를 없앤다. 유도 결과의 저장 위치는 topology 제약 `_derived` **하나**다(이미 하는 쓰기 그대로).
   도구는 한 실행 안에서만 결과를 모은다(`book`을 빈 dict로 시작). 도구 docstring·출력 문구의 '사이드카' 서술도 같은 사실로 고친다. library에 `value_from_achievable` 선언이 0이므로 library 실행은 무동작(대상 0 출력)이다.
6. **IC5 표(test, V5)**: `A/tests/contracts/test_ic5.py` `_DOMAIN_TABLE`에서 `check_multi_leaf_hub_parity` 행과 `audit_vertical_stack_id_euler_feasibility` 행을 지우고 `len(_DOMAIN_TABLE) == 21` → `19`, docstring·주석의 '21' 문구를 '19'로 고친다.
   표 밖 대상이 된 `audit_vertical_stack_id_euler_feasibility`는 여전히 §5.6 **형식** 판정을 받는다(test의 (2) -- 표 밖 대상은 형식만). oracle (d)인 design `10-test-separation` §5.6 영역 표의 두 행과 '현존 21개' 문구는 오케스트레이터 문서 커밋이 같은 card에서 고친다.
7. **기존 test 정리(test, V5)**: `A/tests/unit/test_selftest_sizing_recipe.py`의 `test_s007_solve_diode_stack_current`·`test_s028_estimate_area_budget`을 지우고 import 목록에서 두 이름을 뺀다(`_invert_gm_id_for_current` import는 다른 test가 쓰면 남긴다 -- card base에서 재측정).
   `A/tests/unit/test_selftest_stick_diagram.py`의 `test_s058_section`은 **지우지 않는다**: (i) `build_graph()`+`check_euler_condition()` 3-leaf 64조합 판정은 기대값을 **손 규칙**(홀수 finger leaf 수 m: 0 → `circuit`, 1·2 → `path`, ≥3 → `impossible` -- oracle (a), 지운 함수의 docstring 규칙을 test 쪽 구성으로 옮긴 것, 피검 함수 호출 없음)으로 만들어 계속 판정하고
   (ii) `find_hub_merge_candidates` 판정과 (iii) k=8(가능)·k=7(불가) 실제 그래프 판정은 그대로 둔다. import 목록에서 `check_multi_leaf_hub_parity`를 뺀다. test id 집합은 base − {`test_s007_solve_diode_stack_current`, `test_s028_estimate_area_budget`} + {새 GONE test}와 같다.
8. **TS6 계약 test의 도구 내용 고정(test, V5 -- 결정 필요 항목 D1)**: `A/tests/contracts/test_ts6_probe_relocate.py::test_moved_tool_matches_base_except_path_lines`는 도구가 이동 기준 blob과 '경로 줄 외 동일'함을 영구 판정한다 -- 계약 5만 적용한 모의 head에서 **FAIL**한다(실측: 비경로 줄 변경 4건).
   기본안: test-author가 그 판정의 허용 차이를 '경로 줄 + 이 card 계약 5가 지운 사이드카 문장들(card 계약 5의 문장 목록을 interface card에 문자열로 고정)'로 좁혀 넓힌다(그 밖 줄은 여전히 동일 판정). F2 뒤 그 test가 이미 다른 모양이면(Phase 3 F1이 도구 import를 바꾸며 이 test를 고쳤을 수 있다 -- '작성 전 실측' P3-5) 그 모양에 맞춰 같은 원칙으로 적용한다.
9. **레지스트리(code-author 경로, 같은 code 커밋)**: `docs/03-analysis/gain-budget-gmid-sizing.function-registry.md`에서 §7 행 5개(`solve_diode_stack_current`·`estimate_area_budget`·`load_derived_bounds`·`MultiLeafHubParityVerdict`·`check_multi_leaf_hub_parity`)와 §3 R0 행 1개(`derived_bounds_path`)를 지우고,
   §1 집계 표의 해당 파일 D·R0 값과 §3·§7 소절 제목 괄호 수를 행 수에 맞춘다(`A/tests/tools/reg_check.py` 규칙 `stale`·`count` -- 기존 계약 test `test_reg_check.py::test_main_on_this_repository_is_clean`이 병합본에서 발견 0을 요구한다. 실측: 코드만 지우고 레지스트리를 두면 `stale` 5건).
   §2 '스택 KVL 합' 행의 `solve_diode_stack_current`(운영 0) 언급을 지운다. 행 위치·파일 칸은 Phase 3 D0b가 다시 쓴 뒤의 표를 따른다.
10. **문서(오케스트레이터 문서 커밋, 같은 card)**: 계획 DF-09 행 → 닫힘(삭제로 해소, 경위는 history), N3.11 TS4 행의 "(DF-09 등)" → "V4 lint(`test_lint.py`) 산출 목록"(design §9-1·§9-9, UD-0 diff 승인 범위),
    design `10-test-separation` §5.6 두 행과 '현존 21개', 참조 문서(`references/consistency-map.md`·`design-report-spec.md`·`function-selection-map.md`·`stick-diagram-euler-layout.md`·`analog-grammar-integration.md`)에서 지운 이름을 가리키는 문장을 정본(`build_graph()`+`check_euler_condition()` 등)으로 고친다.
    판정 표(`plan_tables_hash` 입력)는 바뀌지 않는다(DF 표·N3.11 표는 입력 밖 -- 작성 전 실측 5).
11. **E-LIB**: library의 로드 가능한 회로 전부에서 `load_topology` meta·`transistors`·`run_topology_pipeline` 반환이 base와 같다(키 정렬 sha256, 같은 경로에서 비교).
12. **E-INST**: 사이징 대상 회로(정본 실행이 `instance.json`을 쓰는 회로 -- card base에서 재측정, Phase 3 D-25 M10 진입점 test의 회로 포함)의 `instance.json` 정규화 sha256이 base와 같다.
13. **NEW-TOPO**: library에 없는 합성 topology(새 회로 이름·새 넷 이름·소자 수가 다른 넷리스트)에서 `load_topology`·`run_topology_pipeline` 결과가 base와 병합본에서 같다.
14. 전체 suite는 base와 같은 결과다(수집 id = 계약 7의 집합, 실패 0, xfail 집합 같음).

## 신규 시그니처

| 모듈 | 심볼 | 시그니처 |
|---|---|---|

## 판정 유형 근거

equivalence: 코드가 줄지만 운영 동작은 같아야 한다. 증거는 E-LIB·E-INST·NEW-TOPO(전후 동일)와 GONE(계약 3·4). test 커밋 T가 GONE test를 더하고(base에서 정의가 남아 있어 red), 지운 이름을 쓰던 test를 정리한다(계약 6·7·8 -- base에서도 green).
code 커밋 K가 정의·도구·레지스트리를 고친다(병합본 green). test-author는 엔진 소스를 읽지 않는다(DEC-38) -- 계약 7 (i)의 손 규칙은 이 card 계약 문장(지운 함수 docstring의 규칙을 옮긴 것)에서 온다.
V3: 이 card는 def를 지우고 docstring만 고치므로 변이 대상 def가 0이다(실측 -- '작성 전 실측' 8). 선례: 대상 def 0의 V3 PASS(`20260923-d-delete-dead` 판정 기록, 승인 `20260922-ts1-legacy-move`).

## oracle 종류와 출처

(c) 동작 보존: 기대값은 base 트리의 실행 결과다(E-LIB·E-INST·NEW-TOPO, 전체 suite). 새 기대값을 만들지 않는다.
(a) 구성: G-1 판정 입력은 저장소의 등록 딕셔너리, GONE 판정 입력은 삭제 이름 문자열, 계약 7 (i)의 기대값은 손 규칙(m = 홀수 finger leaf 수).
(d) 계획·원자료: IC5 표는 design `10-test-separation` §5.6 영역 표(이 card의 문서 커밋으로 19행).

## 거부해야 할 입력

* GONE 판정기가 **실제로 거부함**을 먼저 보인다: base 트리(정의가 남음)에서 계약 3·4 test가 FAIL(red), 정의를 하나만 남긴 합성 소스 문자열에서 판정 함수가 그 이름을 보고한다.
* G-1 판정기: 합성 소스(삭제 이름을 문자열 키 딕셔너리의 값으로 등록)에서 등록을 찾아 보고한다.
* 계약 7 (i): 손 규칙 helper가 m=3 조합(예: {1,1,1})을 `impossible`로, m=0·2 조합을 가능으로 내는지 합성 입력으로 먼저 본다(기대값이 비어 공허해지지 않게).

## library 회로 적용 여부

적용: E-LIB(로드 가능한 회로 전부, Phase 3 DoD 기록의 9회로를 재측정), E-INST(사이징 대상 회로). 합성 topology는 NEW-TOPO. 도구 계약 5는 library 무동작(`value_from_achievable` 선언 0).

## 무동작 판정 입력(무발동 값)

library 회로 전부와 지운 test 밖의 기존 test 전부 -- 판정이 base와 같다(삭제가 운영 경로를 건드리지 않는다). CC-8(`activations_out`·`noop_proof.py`, #9)은 아직 없다 -- 이 card는 '발동'을 다는 기능이 없으므로 E-LIB·E-INST 동일이 무동작 증거다.

## 재현할 수치

없음(해시 동일성은 계약 11~13의 동작 보존 증거).

## 결정 필요 항목

* **D1(사용자 -- 이 card의 V5 승인 기록 범위에 넣는다)**: 계약 8. 기본안 (가) TS6 도구 내용 고정 test의 허용 차이를 '경로 줄 + 계약 5의 사이드카 문장'으로 좁혀 넓힘(그 밖 줄 동일 판정 유지). 대안 (나) D-3을 이 card에서 빼고 `보류(Phase 4)` 유지(사이드카 두 저장 위치가 남음 -- DEC-68 위반 지속, 백로그).
  근거: 원칙(저장 위치 하나, 지울 것은 지운다)은 (가). 이 card는 어차피 V5 승인 한 건(계약 6·7)이 필요하므로 (가)는 **새 질문을 늘리지 않고** 같은 승인 기록의 범위 설명에 한 줄을 더한다.
* **V5 승인 기록(`target_kind: diff`, 사용자)**: 계약 6(IC5 두 행·19)·7(test 두 개 삭제, S058 기대값 출처를 손 규칙으로)·8(D1 답)을 한 기록으로. diff 해시는 T 커밋 뒤 오케스트레이터가 채운다(선례 `20261001-b26-p9-signature-update`).
* **승인 줄(작성 전 실측 9)**: 머리 `approval`의 `20261002-40-defect-fixes-design`은 **후보 id**다(Phase 4 UD-0 기록 -- 날짜는 기록 커밋 때 확정). 그 기록의 범위 설명이 **이 card id와 'U-02 승인표의 D-1~D-4 처리 칸 `보류(Phase 4)` → 삭제'**를 원문으로 적어야 덮는다(U-02 기록 '재검토': "승인표를 바꾸는 것은 사용자 승인 사항").
  지금 Phase 4 승인 질문 문안(`phase4_approval_question.md` UD-0)은 "옛 함수 삭제·이관 #2~#4"만 적고 함수 이름·U-02 처리 칸 변경을 적지 않는다 -- 질문을 올리기 전에 Phase 3 D-10 선례처럼 원문으로 드러내야 한다(p4_first_card_notes.md §3).
* **V8(auditor 판정 입력, 원칙 기본안)**: 계획 N4.2 V8 도입 = 4이지만 `fallback_events` 계측은 #13이 처음 단다. #13 전 Phase 4 card의 V8은 'N/A -- 계측 미도입, 이 card는 폴백 경로를 바꾸지 않음'으로 적는다(design에 이 문장이 없다 -- design 개정 요청, notes §4).

## 작성 전 실측

(재측정 = gate `master` `dd60db6515b6fe80ab16349835c19aa75d4f292f`, 2026-10-02. 저장소 읽기 전용 -- 격리 복제본 `C:/g204/base`(`git clone` 뒤 그 커밋 checkout)와 모의 커밋용 복제본 `C:/g204/sim`(origin 제거, hooksPath 빈 값), gate 도구는 `git archive gate/master tools/gates`로 `C:/g204/gt`에.
스크립트·출력 사본은 `_drafts/p4kit_first/`. python `C:\Python314\python.exe -B`. **이 줄 번호는 Phase 3 이동 전 판이다 -- 아래 P3 절의 항목은 F2 병합본에서 다시 잰다.**
측정 중 gate `master`가 `36e170e`로 나아갔다(면제 묶기 card 병합 `5a602d4`·판정 기록, Phase 3 design v8.5 커밋 `6c8287f`, 승인 기록 `20260930-30-module-split-design`). `git diff --name-only dd60db6 36e170e`에 `skills/**`·`workspaces/**`·레지스트리 없음 -- 엔진·test·도구 사실은 그대로.
바뀐 것 중 닿는 것: `mutate_changed.py`(면제 묶기 -- `def_hash`는 여전히 `_strip_doc` 뒤 `ast.dump`, 87행), design 10 §5.6 머리 문장('파일' 열 = Phase 3 전 정의 위치 설명, 264·268행 그대로), 계획(561·599·618·623·640·919행 그대로).)

1. 사실 문장 재측정(`git grep -n -w <이름>`, AST 스캔 `p4kit_first/m_tests.py`, `refs.txt`):
   * 정의(dd60db6): SR `solve_diode_stack_current` 1499, `estimate_area_budget` 2765(식 2793~2794), `derived_bounds_path` 7700, `load_derived_bounds` 7712; SD `MultiLeafHubParityVerdict` 2800(`@dataclass` 2799), `check_multi_leaf_hub_parity` 2806.
   * 엔진·하네스 안 코드 참조: `load_derived_bounds` → `derived_bounds_path`(7715) 하나뿐(서로 부름). `solve_diode_stack_current`가 부르는 `_invert_gm_id_for_current`는 `revalidate_finger_override`(11333)도 불러 **남는다**. 엔진 밖 코드 참조: test 3개(아래)와 도구 `derive_achievable_bounds.py:69`(`sr.load_derived_bounds`)·`:112`(`sr.derived_bounds_path`). `workspaces/**` 0.
   * docstring·주석 언급(계약 4 대상, 모의 head에서 감싸는 def로 확인): SR `SemiEmpiricalGmIdLUT.vgs_for_gm_id`(627), `_invert_gm_id_for_current`(1475), `achievable_metric_bound`(7757), `optimize_full_circuit_budget`(9140); SD `find_hub_merge_candidates`(2657·2659), 절 머리 주석(2851), `assign_finger_geometry`(6063), `search_shared_finger_w`(6213), `select_layout_tool`(7004).
   * test 참조(AST): `test_selftest_sizing_recipe.py` import 24행(`estimate_area_budget`·`solve_diode_stack_current`), `test_s007_solve_diode_stack_current`(637~656), `test_s028_estimate_area_budget`(1785~1801); `test_selftest_stick_diagram.py` import 24행, `test_s058_section`(1420~1470, 1436·1466 호출); `contracts/test_ic5.py:58·62`(표 행), 251(`len == 21`). 1221행은 주석 언급(코드 아님).
   * V4 lint(`tools/gates/test_lint.py --subject sizing_recipe:estimate_area_budget`): `test_s028` 1795행 (2) **FAIL**(확실한 복사 -- TS4의 유일한 명시 대상), 1801행 PASS(`v4_s028.json`).
   * `area_priors`: `SPECS`·library 0, 전달은 SR 9272 `assign_finger_geometry(area_priors=spec.get("area_priors"))` 하나. 사이드카 `*.derived.json` 추적 0, library `value_from_achievable` 0.
   * redteam 재생 `tools/gates/redteam/cases/e329283-area-alpha/v.json`은 `git e329283:` 원문만 읽는다 -- HEAD 삭제와 무관.
2. 이름 충돌: 새 test 파일 후보 `A/tests/contracts/test_d4_delete_unwired.py`(접두 `_d4_`) -- `ls A/tests/contracts/`에 같은 이름 없음. `grep -rn "glob(" A/tests/`(tools 제외) 패턴 = `*.py`·`probe_*.py`·`test_probe_*.py`·`*.topology.json`·`*.topology.md`·references `*.md` -- 겹치지 않음.
   `*.py` 전수 스캔 test(`test_d_delete_dead`·`test_d_delete_telescopic`·`test_d_move_tests`·`test_ts3_no_print_verdicts`·`test_ic_markers_match_plan`)는 Name·Attribute·import·def·IC 표식을 센다 -- 새 test는 이름을 문자열 상수로만 들고 IC 표식이 없다(계약 3).
3. 원칙의 계약화: 지울 코드를 고치지 않음 → 계약 1(DF-09 식 수정 없음). 저장 위치 하나(DEC-68) → 계약 5. 정본 하나 → 계약 7 (i)이 정본 판정만 남김. 조용한 공허 금지 → '거부해야 할 입력'. 무동작 → 계약 11~14. topology 무관 → 해당 없음(새 코드 없음, 지우는 정의에 회로 이름 리터럴 없음).
4. 쓰기 경로(계획 N3.12.2 표, dd60db6): 엔진 `A/*.py`·도구 `A/tests/tools/**`·레지스트리 = gmid-code-author(599·600·603행), test `A/tests/**`(tools 제외) = gmid-test-author(618행), 계획·design·references = 오케스트레이터(623·624·640행), 판정 기록 = auditor.
   EL3: code 커밋이 엔진과 `tests/tools/**`를 함께 바꾸는 것은 허용(`tests/**` 중 `tests/tools/**` 제외 규칙). 계약 8의 `test_ts6_probe_relocate.py`는 test-author.
5. 계획서 소비자(`git grep -n -w` docs/01-plan·docs/02-design/features·SKILL.md·references, history 제외): 계획 919행 DF-09(`estimate_area_budget`, 수정 Phase `4(TS4 red)`), 561행 TS4("DF-09 등", `4(첫 작업)`); design 05 318·456행(redteam 사례 설명 -- 원문 커밋 고정이라 그대로), design 10 264행(§5.6 표);
   references: `consistency-map.md:385`, `design-report-spec.md:370·454·492`, `function-selection-map.md:69`, `stick-diagram-euler-layout.md:647·652·672·1068·1135·1188`, `analog-grammar-integration.md:384`. SKILL.md 0. 나머지 `docs/03-analysis/**`·`.ai/**`·spec card는 기록(소비자 아님).
   판정 표: DF 표(N5.2)·TS 표(N3.11)는 `plan_tables_hash` 입력(N4.1 담당 Phase·강제 test, N4.2 도입, N6.1 Phase, N3.12.2)이 아니다 -- 계획 698행 EL3 문장으로 확인.
6. 미배선: 새 def 0(V7 `new_defs` 0 예상). 되살리는 def 0.
7. 기존 계약 test(`A/tests/contracts/`): (a) `test_ic5.py` -- 표 행 함수가 대상에 없으면 FAIL(`missing`), 표 밖은 형식만, `len == 21`(계약 6). (b) `test_ts6_probe_relocate.py::test_moved_tool_matches_base_except_path_lines` -- 계약 5만 적용한 모의 head(`simA`)에서 `pytest --gmid-phase=2 -k moved_tool` → **1 failed, 2 passed**,
   비경로 줄 변경 `('base', 69, 'book = sr.load_derived_bounds(topo)')`·`('base', 112, 'path = sr.derived_bounds_path(topo)')`와 그 대체 2줄(계약 8). (c) `test_reg_check.py::test_main_on_this_repository_is_clean` -- 코드만 지운 레지스트리로 `reg_check.py --registry … --root <모의>` → `stale` 5건(§7 SR 3·SD 2), 레지스트리를 계약 9대로 고친 모의 병합본 → 발견 0, base → 발견 0(계약 9).
   (d) `test_df23_inventory`·`df23_inventory.json` -- 6개 이름·DF-09 항목 0(무관). 조정이 필요한 것은 (a)·(b)이고 V5 승인 경로는 결정 필요 항목.
8. V3 규모(`p4kit_first/v3sim.py`, 도구 `mutate_changed.changed_defs`·`mutants` dd60db6 판 + 범위 정책 card 독립 프로토타입 `v3scope_kit/scope_proto.select`): 모의 head A(정의 6개 삭제 + 도구 2줄) → V3 대상 source 파일 SR·SD, **changed defs 0, 변이 0**(현 규칙·N2b·N2w 모두).
   모의 head B(A + docstring 언급 9곳 수정) → **역시 0**(`def_hash`가 docstring을 뺀 `ast.dump` -- `_strip_doc`). 그러므로 계약 4의 docstring 수정은 V3 비용이 없다. 바뀐 def를 늘리지 않는다(호출부 시그니처 변경 없음).
   (V3 면제 묶기 해시는 docstring을 포함하지만 이 card는 면제를 쓰지 않는다.)
9. 승인 줄: `ls .ai/approvals`(dd60db6) 49개(`_TEMPLATE.md` 포함)에 Phase 4 기록 0. U-02 기록 `20260923-u02-d-list` 1항은 D 항목을 '삭제/이관/보류(Phase 3 모듈 이동·Phase 4 배선)/유지'로 나눴고 이 6개는 레지스트리에서 `보류(Phase 4)`(491·492·496·507·508행; `derived_bounds_path`는 §3 R0 143행)다 -- 처리 칸 변경은 사용자 승인(U-02 '재검토').
   Phase 4 승인 질문 문안 UD-0에 함수 이름·처리 칸 변경 원문이 없다(`grep -n 'D-1\|estimate_area_budget\|U-02' phase4_approval_question.md` → 0줄) -- 결정 필요 항목.
10. 범위 계약: 계약 머리 문장('이 card `Change-Id` 커밋들의 diff')으로 한정.
11. test 이름·모양: 새 test·helper 접두 `_d4_`/`test_d4_`. 계약 7 (i) 손 규칙 helper는 test 파일 안 함수이고 피검 함수를 부르지 않는다. 지운 이름은 문자열 상수로만(계약 3).
12. 같음 판정: E-LIB·E-INST는 키 정렬 JSON의 sha256(선례 `e_lib.py`·Phase 3 D-28 `e_lib_p3.py` 모양), GONE은 (파일, 줄, 이름) 튜플 목록을 정렬해 비교. `set`을 `==`로 비교하는 계약 없음.
13. red 모양: base red는 계약 3·4 GONE test의 `AssertionError`(허용 예외)뿐이다. 새 키워드 인자 호출이 없다.
14. **모의 병합본 전체 suite**(측정 전용 `p4kit_first/simM.py` -- code·test 역할 산출물이 아니다): 모의 head M = A + 레지스트리(계약 9) + 모의 test 변경(계약 6·7, TS6 test는 고치지 않음). `run_suites.sh`로 base `wB`와 `wM`을 같은 설정(gate `pytest_gate.ini`, `--rootdir`·`--confcutdir` = 각 트리, `--gmid-phase=2`)으로 돌림(`p4kit_first/out/suite_*.txt`, 모의 커밋 `sim_revs.txt`):
   base **1047 passed, 15 xfailed**(Phase 2 DoD 수와 같음) / 모의 병합본 **1044 passed, 1 failed, 15 xfailed** -- 실패 1 = `test_ts6_probe_relocate.py::test_moved_tool_matches_base_except_path_lines`(계약 8, 모의에서 일부러 고치지 않음), passed 차이 3 = 지운 test 2 + 그 실패 1.
   그 밖에 깨지는 test 없음(GONE test는 모의에 넣지 않았다). Phase 4 판정 실행은 `--gmid-phase=4`라 F2 뒤 다시 돈다(P3-8과 함께).

### P3 -- Phase 3(`30-module-split`) 뒤 다시 잴 것 (F2 병합본 = card base에서)

* **P3-1 정의 파일**: SR·TL·DR은 F2에서 지워진다. 6개 정의의 파일을 R-DEF(Phase 3 design §7.1 -- `A/*.py` 최상위 바인딩이 정확히 하나)로 다시 정한다. D0b 착수 키트 시제품(`p3kit_d0b/out/plan_amend_ga.json`, 확정 아님):
  `estimate_area_budget` → `sizing_layout_convergence.py`, `derived_bounds_path`·`load_derived_bounds` → `theta_search.py`, `check_multi_leaf_hub_parity`·`MultiLeafHubParityVerdict` → `stick_diagram.py`(A-7 고립 단위), `solve_diode_stack_current` → 시제품 `unassigned`(A-6 규칙 뒤 D0b 이관표가 정함).
* **P3-2 IC5 표 키**: Phase 3 T0가 `test_ic5.py` `_DOMAIN_TABLE`(키 = (파일 이름, 함수))를 위치 가정 군 A로 고친다(Phase 3 §7.1). F2 뒤 키 모양·행 수(21인지)·두 행의 실제 키를 다시 읽고 계약 6을 그 모양에 적용한다. design 10 §5.6 표의 파일 칸도 Phase 3 문서 개정 뒤 판을 따른다.
* **P3-3 import 줄**: Phase 3 F1이 test 파일의 `from sizing_recipe import (…)`를 목적 모듈로 바꾼다 -- 계약 7의 import 정리 대상 줄을 다시 찾는다.
* **P3-4 docstring·주석 언급**: 계약 4 목록을 F2 병합본 `A/*.py` 전체 단어 일치로 다시 뽑는다(정의가 옮겨도 감싸는 def 이름은 같아야 한다 -- 다르면 목록을 고친다).
* **P3-5 도구와 TS6 test**: 도구는 지금 `import sizing_recipe as sr`(33행)로 `sr.load_derived_bounds`·`sr.derived_bounds_path`·`sr.spec_fingerprint`·`sr.achievable_metric_bound`를 읽는다 -- F2가 SR을 지우므로 Phase 3 F1이 이 도구를 고쳐야 하고, 그러면 `test_moved_tool_matches_base_except_path_lines`가 Phase 3에서 먼저 FAIL한다(Phase 3 §7.1 B군 목록에 이 test 함수는 없다 -- `test_ts6_probe_relocate.py:528`만 있음, **[미확인: Phase 3 F1 card 작성 전 실측에서 처리]**).
  F2 뒤 그 test의 모양을 읽고 계약 8을 그 모양에 맞춘다(Phase 3이 허용 차이를 이미 넓혔으면 D1이 '그 규칙에 이 card의 사이드카 문장 추가'로 줄어든다).
* **P3-6 레지스트리**: D0b가 목적지 열과 §7 처리 칸을 다시 쓴다(D-10 9행 `보류(Phase 4)`). 계약 9의 행·§1 수·소절 괄호 수를 F2 판에서 다시 센다(`reg_check.py` 발견 0을 모의 병합본에서 확인).
* **P3-7 V3**: 그때 gate 규칙(면제 묶기·범위 정책 N2w·G1 이동 인식)으로 `v3sim.py`를 다시 돌린다(기대 changed defs 0).
* **P3-8 E-LIB·E-INST base**: Phase 3 DoD 판정 기록의 대상 커밋 산출물을 base로 재사용할 수 있는지(design §8.3 [미확인] -- 기록 형식) 확인한다.
* **P3-9 승인**: Phase 4 UD-0 기록 id(날짜)와 범위 설명 원문, V5 기록 diff 해시.
