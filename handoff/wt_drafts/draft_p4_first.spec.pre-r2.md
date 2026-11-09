---
id: 20261002-d4-delete-unwired
phase: 4
evidence_type: equivalence
gate_change: no
approval: 20261002-40-defect-fixes-design
---
## 의도

Phase 4 design `40-defect-fixes`(초안 v0.9.9, 승인 전) §5.1 #2 `d4-delete-unwired`, §3.2·§3.3(`#2 ─> TS4(#5)`), 준비 자료 `_drafts/prep_deferred_rows.md` §3.2 D-1~D-4: 레지스트리 §7 `보류(Phase 4)` 행 중
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

1. **삭제**: 의도 표의 정의 6개(함수 5, `@dataclass` 클래스 1 -- `MultiLeafHubParityVerdict`는 바로 위 `@dataclass` 데코레이터 줄까지 지운다)가 card base의 정의 파일에서 없어진다. 다른 정의는 지우지 않는다 -- 특히 아래는 **남고 동작이 같다**: `_invert_gm_id_for_current`(운영 호출자 `revalidate_finger_override`),
   `SemiEmpiricalGmIdLUT.vgs_for_gm_id`(운영 호출 다수), `find_hub_merge_candidates`, `build_graph`, `check_euler_condition`, `assign_finger_geometry`(인자 `area_priors`는 예약 필드로 시그니처에 남긴다 -- 백로그),
   `select_layout_tool`(인자 `area_budget` 그대로), `achievable_metric_bound`, `resolve_constraint_references`, `solve_stacked_diode_pair`, `audit_vertical_stack_id_euler_feasibility`(D-5 함수는 #41 몫).
2. **G-1(선언 도달 경로 없음)**: 6개 이름 어느 것도 엔진의 문자열 키 딕셔너리(`_METRICS_REGISTRY`·`_CMRR_ESTIMATOR_REGISTRY`·`_PSRR_ESTIMATOR_REGISTRY`·`_COMPENSATION_REGISTRY`·`_THETA_FEED_REGISTRY` 포함 전수 -- 정의 파일이 바뀌어도 `A/*.py` 전체에서 찾는다)의 값으로 등록돼 있지 않다(base에서 판정 -- 지우기 전에 도달 경로가 없음을 보인다).
3. **GONE(AST)**: 6개 이름의 정의·`Name`·`Attribute`·`import` 참조가 `A/*.py`, `workspaces/run_harness.py`, `A/tests/**`(`A/tests/tools/**` 포함)에서 0이다. 새 GONE test는 이 이름들을 **문자열 상수로만** 든다(import·호출·딕셔너리 값 금지 -- 기존 전수 스캔 test `test_d_delete_dead.py`·`test_d_delete_telescopic.py`·`test_d_move_tests.py`·`test_ts3_no_print_verdicts.py`가 Name·Attribute·import·def를 세므로 걸리지 않게).
   V3 인벤토리(`reachability` 그래프)는 def 이름과 **같은 문자열 상수**도 간선으로 잡으므로 T만 있는 트리에서는 GONE test → 삭제 대상 def 간선이 생긴다 -- 병합본에서는 대상 def가 없으므로 간선이 생기지 않는다(무해).
4. **GONE(본문 언급)**: `A/*.py`와 `workspaces/run_harness.py`의 **원문 텍스트**(docstring·주석 포함)에서 6개 이름의 단어 일치(`\b<이름>\b`)가 0이다. 지금 언급하는 곳(card base에서 재측정 -- 심볼 기준, '작성 전 실측' 1):
   `SemiEmpiricalGmIdLUT.vgs_for_gm_id`·`_invert_gm_id_for_current`·`achievable_metric_bound`·`optimize_full_circuit_budget`의 docstring, `find_hub_merge_candidates`(2곳)·`assign_finger_geometry`·`search_shared_finger_w`·`select_layout_tool`의 docstring,
   그리고 `propagate_topology_forced_currents` 바로 위 절 머리 주석(`# 1.8) A/C 엔진 …`). 고칠 때 사실을 지어내지 않는다: 지운 함수를 가리키던 문장은 남는 정본(`build_graph()`+`check_euler_condition()`, `solve_stacked_diode_pair`, topology 제약 `_derived`)을 가리키거나 문장을 지운다.
   `achievable_metric_bound` docstring의 "프로세스를 넘는 재사용은 사이드카 파일이 한다"는 '선언의 `_derived`(운영 도구가 기록)'로 바꾼다(계약 5와 같은 사실).
5. **운영 도구 `A/tests/tools/derive_achievable_bounds.py`(code-author 경로)**: 사이드카 읽기(`load_derived_bounds`)와 쓰기(`derived_bounds_path` + 파일 쓰기 블록)를 없앤다. 유도 결과의 저장 위치는 topology 제약 `_derived` **하나**다(이미 하는 쓰기 그대로).
   도구는 한 실행 안에서만 결과를 모은다(`book`을 빈 dict로 시작). 도구 docstring·출력 문구의 '사이드카' 서술도 같은 사실로 고친다. library에 `value_from_achievable` 선언이 0이므로 library 실행은 무동작(대상 0 출력)이다.
   이 card의 도구 diff는 위 셋(사이드카 읽기 제거·쓰기 블록 제거·'사이드카' 서술 수정)뿐이다 -- 그 밖의 줄(경로 줄·계산·탐색 인자·선언 기록 블록)은 바꾸지 않는다(범위 계약, auditor가 K diff로 확인. 계약 8 (다)는 HEAD 도구를 읽지 않으므로 이 범위는 test가 아니라 이 문장과 diff 검토가 지킨다 -- D1).
   동작 차이(사실): 지금은 사이드카가 있을 때 한 실행에서 유도가 **실패한** metric도 같은 지문의 사이드카 옛 값이 `book`에 남아 topology `value`·`_derived`에 다시 쓰였다. 사이드카를 없애면 그 metric은 이번 실행에서 쓰지 않고 topology의 기존 `value`·`_derived`가 그대로 남는다.
   library 선언 0·추적 사이드카 0이라 지금 저장소에서는 무동작이다(동작 보존 주장은 이 범위 -- library 회로와 추적 파일).
6. **IC5 표(test, V5)**: `A/tests/contracts/test_ic5.py` `_DOMAIN_TABLE`에서 `check_multi_leaf_hub_parity` 행과 `audit_vertical_stack_id_euler_feasibility` 행을 지우고 `len(_DOMAIN_TABLE) == 21` → `19`, docstring·주석의 '21' 문구를 '19'로 고친다.
   표 밖 대상이 된 `audit_vertical_stack_id_euler_feasibility`는 여전히 §5.6 **형식** 판정을 받는다(test의 (2) -- 표 밖 대상은 형식만). oracle (d)인 design `10-test-separation` §5.6 영역 표의 두 행과 '현존 21개' 문구는 오케스트레이터 문서 커밋이 같은 card에서 고친다.
7. **기존 test 정리(test, V5)**: `A/tests/unit/test_selftest_sizing_recipe.py`의 `test_s007_solve_diode_stack_current`·`test_s028_estimate_area_budget`을 지우고 import 목록에서 `estimate_area_budget`·`solve_diode_stack_current`·`_invert_gm_id_for_current` 세 이름을 뺀다
   (`_invert_gm_id_for_current`를 `tests/unit`·`tests/contracts`에서 쓰는 곳은 `test_s007` 안 한 곳뿐이다 -- 36e170e 실측, card base에서 재확인. 엔진 함수 자체는 계약 1대로 남는다).
   같은 파일의 낡은 언급 두 곳도 같은 test 커밋에서 고친다(계약 4와 같은 원칙, V5 비용 0 -- `weakening_diff`는 함수 docstring과 주석을 보지 않는다): `test_s006_solve_id_for_target_gm` docstring의 `solve_diode_stack_current()/`를 지우고, `mismatch_sigma_mV` 제외 사유 주석의 "사이드카에 저장된다(`derived_bounds_path()`)"를 "topology 제약의 `_derived`에 기록된다"로 고친다.
   `A/tests/unit/test_selftest_stick_diagram.py`의 `test_s058_section`은 **지우지 않는다**. 기대값은 전부 **손 규칙**(홀수 finger leaf 수 m: 0 → `circuit`, 1·2 → `path`, ≥3 → `impossible` -- oracle (a), 지운 함수의 docstring 규칙을 test 쪽 구성으로 옮긴 것, 피검 함수 호출 없음)에서 온다:
   (i) `build_graph()`+`check_euler_condition()` 3-leaf 64조합 판정은 손 규칙 kind와 실제 그래프 kind가 전부 같은지 계속 판정한다(메시지의 '`check_multi_leaf_hub_parity()` 공식' 문구는 '손 규칙'으로).
   (ii) `find_hub_merge_candidates` 판정은 그대로 둔다.
   (iii) k=8·k=7 실제 그래프 판정 블록은 지금 지운 함수를 부른다(`formula = check_multi_leaf_hub_parity(...)`, `formula.ok`·`formula.kind`·`formula.m_odd_leaves`) -- 그 호출을 손 규칙으로 바꾼다: k=8 → 세 leaf 모두 짝수, m=0 → `circuit`(가능), k=7 → m=3 → `impossible`(불가).
   판정은 '실제 그래프의 가능 여부(`kind != 'impossible'`) == 손 규칙의 가능 여부'이고, 메시지에서 `m_odd_leaves` 부분(`(m=…)`)을 지운다.
   import 목록에서 `check_multi_leaf_hub_parity`를 뺀다. 손 규칙 helper(`_d4_` 접두)는 test 파일 안 함수이고 '거부해야 할 입력'의 합성 입력 판정 test를 하나 둔다.
   test id 집합은 base − {`test_s007_solve_diode_stack_current`, `test_s028_estimate_area_budget`} + {새 GONE·G-1 test, 손 규칙 helper 판정 test}와 같다.
8. **TS6 계약 test의 판정 대상을 이동 커밋 blob으로(test, V5 -- 결정 필요 항목 D1, 기본안 (다))**: `A/tests/contracts/test_ts6_probe_relocate.py::test_moved_tool_matches_base_except_path_lines`는 지금 **HEAD 도구**를 base `939f926` blob과 대조해 '경로 줄 외 동일'을 영구 판정한다 -- 계약 5 전체를 적용한 모의 병합본에서 **FAIL**(비경로 줄 변경 15줄, '작성 전 실측' 7(b)).
   바꾸는 것: 그 test의 판정 대상을 HEAD 도구가 아니라 **이동 커밋 `9d6800ef74017dd015f4628e840bdc9d965b42ce`의 blob**(`A/tests/tools/derive_achievable_bounds.py`)으로 바꾼다. 기준선(base `939f926` blob, 옛 자리 `A/tests/derive_achievable_bounds.py`)·경로 줄 정의·`non_path_line_changes`·`assert_only_path_lines_changed`는 그대로다.
   이동 커밋은 구조로 확인한다(oracle (a)): 그 커밋에 새 자리 blob이 있고(비어 있지 않음) 그 **부모 커밋에는 새 자리가 없다**. 이 sha는 TS6 card(`20260923-probe-relocate`)의 code 커밋이고 이 card가 interface card에 그대로 준다 -- code-author가 고르는 문자열은 판정에 들어가지 않는다.
   거부(같은 test 파일에서 실제 커밋으로 보인다): 부모에 이미 새 자리가 있는 커밋(예: `36e170eec5b9e893c03927e5bb45635071de7e69` -- 실측으로 부모에 새 자리 있음)을 이동 커밋으로 주면 거부, 새 자리가 없는 커밋(예: `a574f977dd45b1939dd530e94a20b29db550a3f3` = 이동 커밋의 부모)을 주면 거부. 비경로 줄 변경 거부는 기존 합성 쌍 test(`test_only_path_lines_judge_rejects_a_calculation_change`)가 이미 보인다.
   test 함수 이름·같은 파일의 다른 test(`test_moved_tool_is_in_tools_dir`·`test_moved_tool_paths_equal_pre_move_targets` -- HEAD 도구의 자리와 경로 줄)는 그대로 둔다. 이 test는 base·T·병합본 어디서나 green이다(red 대상 아님 -- V5 항목).
   F2 뒤 그 test가 이미 이 모양이면(Phase 3 F1이 같은 규칙을 채택 -- notes §3-2 요청) 계약 8은 무동작이고 D1은 V5 범위에서 빠진다. 다른 모양(예: 허용 쌍 목록에 import 줄 추가)이면 그 모양을 이 규칙으로 바꾼다('작성 전 실측' P3-5).
9. **레지스트리(code-author 경로, 같은 code 커밋)**: `docs/03-analysis/gain-budget-gmid-sizing.function-registry.md`에서 §7 행 5개(`solve_diode_stack_current`·`estimate_area_budget`·`load_derived_bounds`·`MultiLeafHubParityVerdict`·`check_multi_leaf_hub_parity`)와 §3 R0 행 1개(`derived_bounds_path`)를 지우고,
   §1 집계 표의 해당 파일 D·R0 값과 §3·§7 소절 제목 괄호 수를 행 수에 맞춘다(`A/tests/tools/reg_check.py` 규칙 `stale`·`count` -- 기존 계약 test `test_reg_check.py::test_main_on_this_repository_is_clean`이 병합본에서 발견 0을 요구한다. 실측: 코드만 지우고 레지스트리를 두면 `stale` 5건).
   §2 '스택 KVL 합' 행의 `solve_diode_stack_current`(운영 0) 언급을 지운다. 행 위치·파일 칸은 Phase 3 D0b가 다시 쓴 뒤의 표를 따른다.
10. **문서(오케스트레이터 문서 커밋, 같은 card)**: 계획 DF-09 행 → 닫힘(삭제로 해소, 경위는 history), N3.11 TS4 행의 "(DF-09 등)" → "V4 lint(`test_lint.py`) 산출 목록"(design §9-1·§9-9, UD-0 diff 승인 범위),
    design `10-test-separation` §5.6 두 행과 '현존 21개', 참조 문서(언급 줄 목록은 '작성 전 실측' 5 -- `design-report-spec.md`는 370·**400**(표 셀 안)·454·492행, `references/consistency-map.md`·`design-report-spec.md`·`function-selection-map.md`·`stick-diagram-euler-layout.md`·`analog-grammar-integration.md`)에서 지운 이름을 가리키는 문장을 정본(`build_graph()`+`check_euler_condition()` 등)으로 고친다.
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
V8: design v0.9.9 P-38(§10.1-0)에 따라 **'N/A -- 계측 미도입, 폴백 경로 불변'**이다(`fallback_events` 계측은 #13이 처음 단다. 이 card는 부록 C 사이트를 지우거나 바꾸지 않는다).

## oracle 종류와 출처

(c) 동작 보존: 기대값은 base 트리의 실행 결과다(E-LIB·E-INST·NEW-TOPO, 전체 suite). 새 기대값을 만들지 않는다.
(a) 구성: G-1 판정 입력은 저장소의 등록 딕셔너리, GONE 판정 입력은 삭제 이름 문자열, 계약 7 (i)의 기대값은 손 규칙(m = 홀수 finger leaf 수).
(d) 계획·원자료: IC5 표는 design `10-test-separation` §5.6 영역 표(이 card의 문서 커밋으로 19행).

## 거부해야 할 입력

* GONE 판정기가 **실제로 거부함**을 먼저 보인다: base 트리(정의가 남음)에서 계약 3·4 test가 FAIL(red), 정의를 하나만 남긴 합성 소스 문자열에서 판정 함수가 그 이름을 보고한다.
* G-1 판정기: 합성 소스(삭제 이름을 문자열 키 딕셔너리의 값으로 등록)에서 등록을 찾아 보고한다.
* 계약 7 (i)·(iii): 손 규칙 helper가 m=3 조합(예: {1,1,1})을 `impossible`로, m=0·2 조합을 가능으로 내는지 합성 입력으로 먼저 본다(기대값이 비어 공허해지지 않게).
* 계약 8: 이동 커밋 확인이 실제로 거부함 -- 부모에 이미 새 자리가 있는 커밋(`36e170e`)과 새 자리가 없는 커밋(`a574f97`)을 주면 각각 FAIL(계약 8 원문). 비경로 줄 거부는 기존 합성 쌍 test.

## library 회로 적용 여부

적용: E-LIB(로드 가능한 회로 전부, Phase 3 DoD 기록의 9회로를 재측정), E-INST(사이징 대상 회로). 합성 topology는 NEW-TOPO. 도구 계약 5는 library 무동작(`value_from_achievable` 선언 0).

## 무동작 판정 입력(무발동 값)

library 회로 전부와 지운 test 밖의 기존 test 전부 -- 판정이 base와 같다(삭제가 운영 경로를 건드리지 않는다). CC-8(`activations_out`·`noop_proof.py`, #9)은 아직 없다 -- 이 card는 '발동'을 다는 기능이 없으므로 E-LIB·E-INST 동일이 무동작 증거다.

## 재현할 수치

없음(해시 동일성은 계약 11~13의 동작 보존 증거).

## 결정 필요 항목

* **D1(사용자 -- 이 card의 V5 승인 기록 범위에 넣는다)**: 계약 8. **기본안 (다)** TS6 test의 판정 대상을 HEAD 도구에서 **이동 커밋 `9d6800e` blob**으로 바꾼다(TS6 계약 5의 원래 뜻 '이동이 경로 줄만 바꿨다'를 불변 이력으로 판정 -- HEAD 도구 내용을 영구 고정하지 않는다).
  대안 (가') HEAD 도구 대조를 두고 허용 차이를 '경로 줄 ∪ 아래 15개 (쪽, 원문) 쌍'으로 고정(그 밖 차이 0). 대안 (나) D-3을 이 card에서 빼고 `보류(Phase 4)` 유지(사이드카 두 저장 위치가 남음 -- DEC-68 위반 지속, 백로그).
  (다)를 고른 근거(실측 r1, gate `master` `36e170e`, 격리 복제본 `C:/g219` -- base → T(test 모의) → K(code 모의), '작성 전 실측' 15):
  (1) **test-first 실행 가능** -- (다) test는 HEAD 도구를 읽지 않으므로 T만 있는 트리·base·병합본에서 모두 green(병합본 `1 passed`), code-author의 docstring·출력 문구·`book` 줄 선택과 무관하다. 판정 입력은 card가 주는 sha 하나와 base blob이다.
  (2) **공격 변이를 거부** -- 이동 커밋 자리에 '부모 = `a574f97`, 새 자리 추가 + 비경로 줄 1개(`_first = [True]` → `[False]`)'인 가짜 이동 커밋을 고정하면 FAIL(`('base', 37, '_first = [True]'), ('new', 37, '_first = [False]')`), 부모에 새 자리가 있는 커밋(K)을 고정하면 FAIL('이동 커밋이 아니다'), 새 자리가 없는 커밋(`a574f97`)을 고정하면 FAIL.
  (3) **넓히는 범위(사용자가 볼 것)** -- HEAD 도구에 계약 5 밖의 비경로 줄 변경을 더한 변이(`emit("=" * 96)` → `95`)는 (다) test에서 **PASS**(옛 test는 FAIL). 즉 (다)는 'HEAD 도구가 이동 뒤 경로 줄 외 그대로'라는 영구 고정을 **푼다**. 이 card의 도구 변경 범위는 계약 5 범위 문장과 K diff 검토(auditor)가 지킨다. 원래 TS6 계약 5는 '이동' 커밋에 대한 문장이었다(test docstring '계약 5의 경로 계산 줄을 뺀 나머지가 원본과 같다'). 그 사실은 (다)도 계속 판정한다.
  (4) **유지 비용** -- (가')는 HEAD 도구를 고치는 card마다 쌍 목록이 늘어난다. Phase 3 F1이 도구 33행 `import sizing_recipe as sr`를 바꾸면 옛 test가 FAIL한다(실측 `[('base', 33, 'import sizing_recipe as sr'), ('new', 33, 'import theta_search as sr')]`). (다)는 F1·#2·이후 card 모두 이 test를 건드리지 않는다.
  (가')를 고르면 쓸 15쌍(base `939f926` blob 대 계약 5 전체 적용 모의 도구, `non_path_line_changes` 실측 -- 계약 5의 새 문장도 이 원문으로 고정해야 한다):
  base 쪽 10 -- 2 `"""제약 임계값을 **달성 가능 실측**에서 유도해 사이드카(`<topology>.derived.json`)에 남긴다.` / 10 `그걸 돌리면 self-test/프로브가 못 쓴다. 그래서 여기서 **한 번 계산해 파일에 남기고**,` / 11 `` `resolve_constraint_references()`는 이후 **읽기만** 한다. 파일에는 `spec_fingerprint()`가`` / 50 `emit("달성 가능 실측으로 제약 임계값 유도 (사이드카 갱신)")` / 69 `    book = sr.load_derived_bounds(topo)` / 70 `    book.setdefault(fp, {})` / 112 `    path = sr.derived_bounds_path(topo)` / 113 `    with open(path, "w", encoding="utf-8") as fh:` / 114 `        json.dump(book, fh, ensure_ascii=False, indent=2)` / 115 `    emit(f"  사이드카 저장: {path}  (지문 {fp})")`;
  new 쪽 5 -- 2 `"""제약 임계값을 **달성 가능 실측**에서 유도해 topology 제약의 `_derived`에 남긴다.` / 10 `그걸 돌리면 self-test/프로브가 못 쓴다. 그래서 여기서 **한 번 계산해 선언에 남기고**,` / 11 `` `resolve_constraint_references()`는 이후 **읽기만** 한다. `_derived`에는 `spec_fingerprint()`가`` / 50 `emit("달성 가능 실측으로 제약 임계값 유도 (topology `_derived` 갱신)")` / 69 `    book = {fp: {}}`.
  근거 요약: 원칙(저장 위치 하나, 지울 것은 지운다)은 (다)·(가') 모두 지키고, 실행 가능성·유지 비용은 (다)가 낫다. 어느 쪽이 '약화'인지는 사용자 판단 -- (3)을 V5 기록 범위 설명에 원문으로 적는다. 이 card는 어차피 V5 승인 한 건(계약 6·7)이 필요하므로 **새 질문을 늘리지 않는다**.
  design v0.9.9 §5.1 #2 (ii)·§7.4 #2 V5 줄·§7 'v0.9.9 대비'는 기본안 (가)로 적혀 있다 -- 개정 요청(notes §7).
* **V5 승인 기록(`target_kind: diff`, 사용자)**: 계약 6(IC5 두 행·19)·7(test 두 개 삭제, S058 기대값 출처를 손 규칙으로)·8(D1 답)을 한 기록으로. diff 해시는 T 커밋 뒤 오케스트레이터가 채운다(선례 `20261001-b26-p9-signature-update`).
  범위 설명에 원문으로 적을 것: (a) D-5 표 행을 함수보다 먼저 지우므로(P-18) **남는 함수 `audit_vertical_stack_id_euler_feasibility`의 영역 값 판정이 #41까지 꺼진다**(형식 판정만 남음). (b) D1 (3) -- (다)를 고르면 HEAD 도구의 '경로 줄 외 그대로' 영구 고정이 풀린다.
  모의 병합본의 V5 발견(r1 실측 8건)은 전부 계약 6·7·8 범위다: `test_ic5` `test_domain_table_uses_allowed_values`(21→19)·`<module>`(두 표 행 + 모듈 docstring '21행'), `test_ts6_probe_relocate` `test_moved_tool_matches_base_except_path_lines`(비교 완화 + 리터럴 변경), `test_s007`·`test_s028`(함수 삭제), `test_s058_section`(비교 완화 + 리터럴 변경). 계약 7의 docstring·주석 수정 두 곳과 새 test는 발견 0.
* **승인 줄(작성 전 실측 9)**: 머리 `approval`의 `20261002-40-defect-fixes-design`은 **후보 id**다(Phase 4 UD-0 기록 -- 날짜는 기록 커밋 때 확정). 그 기록의 범위 설명이 **이 card id와 'U-02 승인표의 D-1~D-4 처리 칸 `보류(Phase 4)` → 삭제'**를 원문으로 적어야 덮는다(U-02 기록 '재검토': "승인표를 바꾸는 것은 사용자 승인 사항").
  지금 Phase 4 승인 질문 문안(`phase4_approval_question.md` UD-0)은 "옛 함수 삭제·이관 #2~#4"만 적고 함수 이름·U-02 처리 칸 변경을 적지 않는다 -- 질문을 올리기 전에 Phase 3 D-10 선례처럼 원문으로 드러내야 한다(p4_first_card_notes.md §3).

## 작성 전 실측

(재측정 = gate `master` `dd60db6515b6fe80ab16349835c19aa75d4f292f`, 2026-10-02. 저장소 읽기 전용 -- 격리 복제본 `C:/g204/base`(`git clone` 뒤 그 커밋 checkout)와 모의 커밋용 복제본 `C:/g204/sim`(origin 제거, hooksPath 빈 값), gate 도구는 `git archive gate/master tools/gates`로 `C:/g204/gt`에.
스크립트·출력 사본은 `_drafts/p4kit_first/`. python `C:\Python314\python.exe -B`. **이 줄 번호는 Phase 3 이동 전 판이다 -- 아래 P3 절의 항목은 F2 병합본에서 다시 잰다.**
측정 중 gate `master`가 `36e170e`로 나아갔다(면제 묶기 card 병합 `5a602d4`·판정 기록, Phase 3 design v8.5 커밋 `6c8287f`, 승인 기록 `20260930-30-module-split-design`). `git diff --name-only dd60db6 36e170e`에 `skills/**`·`workspaces/**`·레지스트리 없음 -- 엔진·test·도구 사실은 그대로.
바뀐 것 중 닿는 것: `mutate_changed.py`(면제 묶기 -- `def_hash`는 여전히 `_strip_doc` 뒤 `ast.dump`, 87행), design 10 §5.6 머리 문장('파일' 열 = Phase 3 전 정의 위치 설명, 264·268행 그대로), 계획(561·599·618·623·640·919행 그대로).)

1. 사실 문장 재측정(`git grep -n -w <이름>`, AST 스캔 `p4kit_first/m_tests.py`, `refs.txt`):
   * 정의(dd60db6): SR `solve_diode_stack_current` 1499, `estimate_area_budget` 2765(식 2793~2794), `derived_bounds_path` 7700, `load_derived_bounds` 7712; SD `MultiLeafHubParityVerdict` 2800(`@dataclass` 2799), `check_multi_leaf_hub_parity` 2806.
   * 엔진·하네스 안 코드 참조: `load_derived_bounds` → `derived_bounds_path`(7715) 하나뿐(서로 부름). `solve_diode_stack_current`가 부르는 `_invert_gm_id_for_current`는 `revalidate_finger_override`(11333)도 불러 **남는다**. 엔진 밖 코드 참조: test 3개(아래)와 도구 `derive_achievable_bounds.py:69`(`sr.load_derived_bounds`)·`:112`(`sr.derived_bounds_path`). `workspaces/**` 0.
   * docstring·주석 언급(계약 4 대상, 모의 head에서 감싸는 def로 확인): SR `SemiEmpiricalGmIdLUT.vgs_for_gm_id`(627), `_invert_gm_id_for_current`(1475), `achievable_metric_bound`(7757), `optimize_full_circuit_budget`(9140); SD `find_hub_merge_candidates`(2657·2659), 절 머리 주석(2851), `assign_finger_geometry`(6063), `search_shared_finger_w`(6213), `select_layout_tool`(7004).
   * test 참조(AST): `test_selftest_sizing_recipe.py` import 24행(`estimate_area_budget`·`solve_diode_stack_current`), `test_s007_solve_diode_stack_current`(637~656), `test_s028_estimate_area_budget`(1785~1801); `test_selftest_stick_diagram.py` import 24행, `test_s058_section`(1420~1470, 1436·1466 호출); `contracts/test_ic5.py:58·62`(표 행), 251(`len == 21`). 1221행은 주석 언급, 617행은 `test_s006` docstring 언급(코드 아님 -- 계약 7이 같은 test 커밋에서 고친다). `_invert_gm_id_for_current`의 test 사용은 `test_selftest_sizing_recipe.py:651`(`test_s007` 안) 하나뿐(36e170e).
   * V4 lint(`tools/gates/test_lint.py --subject sizing_recipe:estimate_area_budget`): `test_s028` 1795행 (2) **FAIL**(확실한 복사 -- TS4의 유일한 명시 대상), 1801행 PASS(`v4_s028.json`).
   * `area_priors`: `SPECS`·library 0, 전달은 SR 9272 `assign_finger_geometry(area_priors=spec.get("area_priors"))` 하나. 사이드카 `*.derived.json` 추적 0, library `value_from_achievable` 0.
   * redteam 재생 `tools/gates/redteam/cases/e329283-area-alpha/v.json`은 `git e329283:` 원문만 읽는다 -- HEAD 삭제와 무관.
2. 이름 충돌: 새 test 파일 후보 `A/tests/contracts/test_d4_delete_unwired.py`(접두 `_d4_`) -- `ls A/tests/contracts/`에 같은 이름 없음. `grep -rn "glob(" A/tests/`(tools 제외) 패턴 = `*.py`·`probe_*.py`·`test_probe_*.py`·`*.topology.json`·`*.topology.md`·references `*.md` -- 겹치지 않음.
   `*.py` 전수 스캔 test(`test_d_delete_dead`·`test_d_delete_telescopic`·`test_d_move_tests`·`test_ts3_no_print_verdicts`·`test_ic_markers_match_plan`)는 Name·Attribute·import·def·IC 표식을 센다 -- 새 test는 이름을 문자열 상수로만 들고 IC 표식이 없다(계약 3).
3. 원칙의 계약화: 지울 코드를 고치지 않음 → 계약 1(DF-09 식 수정 없음). 저장 위치 하나(DEC-68) → 계약 5. 정본 하나 → 계약 7 (i)이 정본 판정만 남김. 조용한 공허 금지 → '거부해야 할 입력'. 무동작 → 계약 11~14. topology 무관 → 해당 없음(새 코드 없음, 지우는 정의에 회로 이름 리터럴 없음).
4. 쓰기 경로(계획 N3.12.2 표, dd60db6): 엔진 `A/*.py`·도구 `A/tests/tools/**`·레지스트리 = gmid-code-author(599·600·603행), test `A/tests/**`(tools 제외) = gmid-test-author(618행), 계획·design·references = 오케스트레이터(623·624·640행), 판정 기록 = auditor.
   EL3: code 커밋이 엔진과 `tests/tools/**`를 함께 바꾸는 것은 허용(`tests/**` 중 `tests/tools/**` 제외 규칙). 계약 8의 `test_ts6_probe_relocate.py`는 test-author.
5. 계획서 소비자(`git grep -n -w` docs/01-plan·docs/02-design/features·SKILL.md·references, history 제외): 계획 919행 DF-09(`estimate_area_budget`, 수정 Phase `4(TS4 red)`), 561행 TS4("DF-09 등", `4(첫 작업)`); design 05 318·456행(redteam 사례 설명 -- 원문 커밋 고정이라 그대로), design 10 264행(§5.6 표);
   references: `consistency-map.md:385`, `design-report-spec.md:370·400·454·492`(400은 표 셀 안 `check_multi_leaf_hub_parity()` -- r1에서 추가), `function-selection-map.md:69`, `stick-diagram-euler-layout.md:647·652·672·1068·1135·1188`, `analog-grammar-integration.md:384`. SKILL.md 0. 나머지 `docs/03-analysis/**`·`.ai/**`·spec card는 기록(소비자 아님).
   판정 표: DF 표(N5.2)·TS 표(N3.11)는 `plan_tables_hash` 입력(N4.1 담당 Phase·강제 test, N4.2 도입, N6.1 Phase, N3.12.2)이 아니다 -- 계획 698행 EL3 문장으로 확인.
6. 미배선: 새 def 0(V7 `new_defs` 0 예상). 되살리는 def 0.
7. 기존 계약 test(`A/tests/contracts/`): (a) `test_ic5.py` -- 표 행 함수가 대상에 없으면 FAIL(`missing`), 표 밖은 형식만, `len == 21`(계약 6). (b) `test_ts6_probe_relocate.py::test_moved_tool_matches_base_except_path_lines` -- 계약 5만 적용한 모의 head(`simA`)에서 `pytest --gmid-phase=2 -k moved_tool` → **1 failed, 2 passed**,
   비경로 줄 변경 `('base', 69, 'book = sr.load_derived_bounds(topo)')`·`('base', 112, 'path = sr.derived_bounds_path(topo)')`와 그 대체 2줄 -- **이 4건은 두 줄만 바꾼 `simA`의 수다**. 계약 5 전체(쓰기 블록 삭제·docstring·출력 문구·`book` 초기화)를 적용하면 **15줄**(base 쪽 10·new 쪽 5, D1에 원문, r1 실측 = 독립 검토 측정과 같음). (c) `test_reg_check.py::test_main_on_this_repository_is_clean` -- 코드만 지운 레지스트리로 `reg_check.py --registry … --root <모의>` → `stale` 5건(§7 SR 3·SD 2), 레지스트리를 계약 9대로 고친 모의 병합본 → 발견 0, base → 발견 0(계약 9).
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
15. **r1 재측정(독립 검토 `review_p4_first.md` 반영, gate `master` `36e170eec5b9…`, 2026-10-02)**: 격리 복제본 `C:/g219`(작업 저장소 clone 뒤 `36e170e` checkout, 모의 clone origin 제거·hooksPath 빈 값, TMP/TEMP도 그 안), gate 도구는 `git archive 36e170e tools/gates` → `C:/g219/gt`. 끝난 뒤 `C:/g219` 삭제, 작업 저장소 `git status` 변화 없음.
   모의 card(측정 전용 -- 역할 산출물 아님): base `36e170e` → T(계약 3·4 GONE test 4개·G-1, 계약 6, 계약 7 전부(손 규칙 (i)·(iii), import 세 이름, 617·1221 수정, 손 규칙 판정 test), 계약 8 (다)) → K(계약 1·4·5 전체·9).
   * 전체 suite(gate `pytest_gate.ini`, `--gmid-phase=2`, 각 트리 rootdir): base **1047 passed, 15 xfailed** / T만 **2 failed, 1048 passed, 15 xfailed**(실패 = GONE AST·본문 두 test, `AssertionError` -- 계약 8 (다) test는 T에서 green) / 병합본 **1050 passed, 15 xfailed, 실패 0**(= 1047 − 2 + GONE·G-1·거부 4 + 손 규칙 판정 1).
   * V3(`mutate_changed.py`, 36e170e 판, base..병합본): **PASS, targets SR·SD, mutants 0**. V7: **PASS, `new_defs` 0, unreached 0**. reg_check: base 발견 0 / 병합본 발견 0.
   * V5(`weakening_diff.py`): FAIL(승인 없음, 예상대로) 발견 **8건, 전부 계약 6·7·8 범위**(D1 V5 줄에 목록). 범위 밖 발견 0. 모의 diff 해시는 실제 기록에 쓰지 않는다.
   * 계약 8 (다) 공격 변이(test 하나만 실행): 병합본 PASS / 가짜 이동 커밋(비경로 줄 1개) FAIL / K 고정 FAIL / `a574f97` 고정 FAIL / HEAD 도구에 범위 밖 비경로 변경 → (다) PASS·옛 test FAIL / 병합본에 옛 test → FAIL(15줄). 이동 커밋 blob = 36e170e HEAD 도구(그 뒤 변경 0), `non_path_line_changes(939f926 blob, 이동 blob) = []`.
   * E-LIB·E-INST는 r1에서 다시 재지 않았다(독립 검토가 36e170e에서 E-LIB 해시 동일 `1d2e3bf6…`·9/9 회로를 쟀고, r1 변경은 test·card 문장뿐이라 엔진 diff가 같다).

### P3 -- Phase 3(`30-module-split`) 뒤 다시 잴 것 (F2 병합본 = card base에서)

* **P3-1 정의 파일**: SR·TL·DR은 F2에서 지워진다. 6개 정의의 파일을 R-DEF(Phase 3 design §7.1 -- `A/*.py` 최상위 바인딩이 정확히 하나)로 다시 정한다. D0b 착수 키트 시제품(`p3kit_d0b/out/plan_amend_ga.json`, 확정 아님):
  `estimate_area_budget` → `sizing_layout_convergence.py`, `derived_bounds_path`·`load_derived_bounds` → `theta_search.py`, `check_multi_leaf_hub_parity`·`MultiLeafHubParityVerdict` → `stick_diagram.py`(A-7 고립 단위), `solve_diode_stack_current` → 시제품 `unassigned`(A-6 규칙 뒤 D0b 이관표가 정함).
* **P3-2 IC5 표 키**: Phase 3 T0가 `test_ic5.py` `_DOMAIN_TABLE`(키 = (파일 이름, 함수))를 위치 가정 군 A로 고친다(Phase 3 §7.1). F2 뒤 키 모양·행 수(21인지)·두 행의 실제 키를 다시 읽고 계약 6을 그 모양에 적용한다. design 10 §5.6 표의 파일 칸도 Phase 3 문서 개정 뒤 판을 따른다.
* **P3-3 import 줄**: Phase 3 F1이 test 파일의 `from sizing_recipe import (…)`를 목적 모듈로 바꾼다 -- 계약 7의 import 정리 대상 줄을 다시 찾는다.
* **P3-4 docstring·주석 언급**: 계약 4 목록을 F2 병합본 `A/*.py` 전체 단어 일치로 다시 뽑는다(정의가 옮겨도 감싸는 def 이름은 같아야 한다 -- 다르면 목록을 고친다).
* **P3-5 도구와 TS6 test**: 도구는 지금 `import sizing_recipe as sr`(33행)로 `sr.load_derived_bounds`·`sr.derived_bounds_path`·`sr.spec_fingerprint`·`sr.achievable_metric_bound`를 읽는다 -- F2가 SR을 지우므로 Phase 3 F1이 이 도구를 고쳐야 하고, 그러면 `test_moved_tool_matches_base_except_path_lines`가 Phase 3에서 먼저 FAIL한다 -- **확정(측정)**: 33행만 `import theta_search as sr`로 바꾼 본에서 옛 test 판정 = `[('base', 33, 'import sizing_recipe as sr'), ('new', 33, 'import theta_search as sr')]` → FAIL(독립 검토 측정, r1 재측정 같음).
  Phase 3 §7.1 B군 목록에는 이 test 함수가 없다(`test_ts6_probe_relocate.py:528`만 있음) -- Phase 3 쪽 누락이고 Phase 3 F1/F2 담당에 보고한다(notes §3-2). 권고: F1이 계약 8 (다)와 같은 규칙으로 그 test를 고친다.
  F2 뒤 그 test의 모양을 읽는다: (다) 모양이면 계약 8 무동작·D1은 V5 범위에서 빠짐, 다른 모양이면 계약 8대로 (다)로 바꾼다.
* **P3-6 레지스트리**: D0b가 목적지 열과 §7 처리 칸을 다시 쓴다(D-10 9행 `보류(Phase 4)`). 계약 9의 행·§1 수·소절 괄호 수를 F2 판에서 다시 센다(`reg_check.py` 발견 0을 모의 병합본에서 확인).
* **P3-7 V3**: 그때 gate 규칙(면제 묶기·범위 정책 N2w·G1 이동 인식)으로 `v3sim.py`를 다시 돌린다(기대 changed defs 0).
* **P3-8 E-LIB·E-INST base**: Phase 3 DoD 판정 기록의 대상 커밋 산출물을 base로 재사용할 수 있는지(design §8.3 [미확인] -- 기록 형식) 확인한다.
* **P3-9 승인**: Phase 4 UD-0 기록 id(날짜)와 범위 설명 원문, V5 기록 diff 해시.
