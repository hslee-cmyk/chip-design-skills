# Phase 4 첫 card 메모 -- `d4-delete-unwired`(design #2)

측정 판: gate `master` `dd60db6515b6fe80ab16349835c19aa75d4f292f`(2026-10-02). 측정 중 gate가 `36e170e`로 나아갔으나 `skills/**`·`workspaces/**`·레지스트리 변경 0이고 인용한 계획·design 10 줄 번호도 같다(card '작성 전 실측' 머리). `parse_spec_card`는 두 판 도구 모두 통과. 저장소 쓰기 0 -- 격리 복제본 `C:/g204`(끝나면 삭제), 사본 스크립트·출력은 `p4kit_first/`.
입력: Phase 4 design 초안 v0.9.9(`draft_phase4_design.md`, 승인 전 -- r1에서 v0.9.8 → v0.9.9로 고침), DAG `p4_scripts/p4v091_dag.py`, 계획 N6.1 Phase 4 행, Phase 3 design v8.5(`draft_phase3_design_v8.md`, sha256 `a4350dc0…` -- 2026-10-02 UD-0 승인 판).
card 초안: `draft_p4_first.spec.md`(`parse_spec_card` 통과 -- §6).
**r1(2026-10-02)**: 독립 검토 `review_p4_first.md`(B1·S1~S3·minor 1~7) 반영. 재측정 판 gate `master` `36e170e`, 격리 복제본 `C:/g219`(끝나면 삭제). 반영 전 사본 `draft_p4_first.spec.pre-r1.md`·`p4_first_card_notes.pre-r1.md`. B1은 **(다)**(이동 커밋 blob 판정)를 골랐다 -- 근거·측정은 card D1·'작성 전 실측' 15.

## 1. 왜 이것이 첫 card인가(TS4가 아니라)

1. **아직 안 한 것 확인**: gate `master`의 `.ai/verification/`·`docs/02-design/specs/`에 `ts4`·`d4-delete`·`pole-oracle`·`toy-lut`·`cc4a` 이름 0. DF-35(`34bc75e`)·DF-36(`148bd6d`)은 gate `master` 조상이고 판정 기록(`20260930-df35-harness-paths.json`·`20260930-df36-instance-relpath.json`)이 있다 -- N6.1 순서의 'TS4 → DF-35 → DF-36'에서 뒤 둘은 끝났다.
2. **N6.1 문구('TS4 첫 작업') 대신 #2가 앞선다** -- design §1.5-1·§3.3·§9-9·P-35:
   * TS4의 명시 대상은 사실상 하나다: 판정 자기참조 test `test_s028_estimate_area_budget`. 실측(`tools/gates/test_lint.py --subject sizing_recipe:estimate_area_budget`): 1795행 V4 (2) **FAIL**(확실한 복사), 1801행 PASS.
   * 그 피검 함수 `estimate_area_budget`(DF-09)는 운영 경로가 없는 제3 면적 모델이라 design이 **삭제(D-1)**로 정했다. '지울 코드를 고치지 않는다'(N3.10 등급 D 처리 원칙) -- TS4가 먼저 오면 지울 함수의 test를 oracle로 고치는 일이 된다.
   * DAG(`p4v091_dag.py` 기본 그래프): `#5`(TS4)의 선행 = {P3DoD, `#2`, UD-0}, `#2`의 선행 = {P3DoD, UD-0}. Phase 4 card 중 선두 사슬 `#2 → #5 → #6 → #7/#9`의 뿌리다. `#3`(pole-oracle-to-tests)·`#4`(toy-lut-to-tests)도 같은 선행만 가진 뿌리라 **병렬 준비·병합 가능**하지만 선두 사슬 위에 있지 않다.
   * #2는 F2 뒤 단일 경로(P-35): 선행 UD-0이 Phase 4 착수 때 올리는 질문이라 D0b 전 앞당김은 순환(DAG 대조군 RC1).
3. #2가 TS4 범위를 바꾼다: D-1 삭제 뒤 TS4 대상 = V4 lint 산출 목록(계획 TS4 행 정정, design §9-1). design의 [미확인] '그 산출이 0이면 TS4는 계획 정정으로 닫는다'에 대한 예비 실측(아래 §5) -- **0이 아니다**.

## 2. 의존과 착수 조건

| 조건 | 상태(dd60db6) | 비고 |
|---|---|---|
| Phase 3 DoD PASS(F2 병합 = D-27 엔진 동결 끝) | 미충족 | Phase 3 card(T0·G1·D0a·D0b·M1~M10·F1·F2)와 그 앞 확정 순서(34 → 35 → B34 → B26pre → backfill → B26-1 → B33)가 남음 |
| Phase 4 design 승인(UD-0, 기록 `<날짜>-40-defect-fixes-design`, `target_kind: diff`) | 미요청 | 질문은 Phase 3 DoD 뒤(design §3.3 '승인 시점'). card 머리 `approval` 후보 id `20261002-40-defect-fixes-design` -- 날짜는 기록 커밋 때 확정 |
| UD-0 기록 범위 설명에 이 card id와 **U-02 처리 칸 변경**(D-1~D-4 `보류(Phase 4)` → 삭제)이 원문으로 있음 | **없음** | §3 -- 질문 문안 보강 필요 |
| V5 승인 기록(`target_kind: diff`): IC5 두 행·19, test 두 개 삭제, S058 기대값 출처, TS6 도구 test(D1) | 미요청 | T 커밋 뒤 해시. D1은 같은 기록의 범위 한 줄 |
| design·계획 정정 커밋(DF-09 닫힘, TS4 행, design 10 §5.6) | 미작성 | design §9-1·§9-9 -- UD-0 diff 범위 |
| F2 병합본에서 '작성 전 실측' P3-1~P3-9 재측정 | 미착수 | 정의 파일·IC5 표 키·import 줄·레지스트리 판이 Phase 3에서 바뀐다 |

착수 = Phase 3 DoD PASS + UD-0 승인 기록 커밋 + P3 재측정 반영 card 커밋. V5 기록은 T 커밋 뒤·병합 전.

## 3. 발견(이 card 작성 중 실측으로 드러난 것 -- 오케스트레이터 확인 필요)

1. **TS6 계약 test가 운영 도구 내용을 영구 고정한다**: `test_ts6_probe_relocate.py::test_moved_tool_matches_base_except_path_lines`는 `A/tests/tools/derive_achievable_bounds.py`가 이동 기준 blob과 '경로 줄 외 동일'함을 판정한다.
   D-3(사이드카 함수 삭제)이 도구의 69·112행을 바꾸게 하므로 모의 head에서 **1 failed**(실측). prep(`prep_deferred_rows.md` §3.2 D-3)의 "도구에서 사이드카 읽기·쓰기 제거(test-author 영역)"는 틀렸다 -- 도구는 code-author 경로(계획 600행)이고, 걸리는 것은 test-author 경로의 이 계약 test다.
   card 결정 항목 D1 -- ~~기본안 (가) 허용 차이를 '경로 줄 + 이 card의 사이드카 문장'으로 좁혀 넓힘~~ **(r1) 기본안 (다)**: 판정 대상을 HEAD 도구에서 이동 커밋 `9d6800e` blob으로(같은 V5 기록). (가)는 문자열 목록이 card에 없어 test-first로 쓸 수 없었다(독립 검토 B1 -- 계약 5 전체 적용 시 차이 15줄, '4건'은 두 줄만 바꾼 모의의 수). (가')(15쌍 원문 고정)는 D1에 대안으로 원문과 함께 남겼다.
2. **같은 test가 Phase 3에서 먼저 걸린다 -- 확정(측정)**: 도구는 `import sizing_recipe as sr`(33행)로 `sr.*` 네 이름을 읽는다. F2가 SR을 지우므로(design 30 85행) F1이 도구를 고쳐야 하고(§7.2 F1 대상에 `A/tests/tools` 2파일), 그러면 이 test가 Phase 3에서 FAIL한다.
   측정: 33행만 `import theta_search as sr`로 바꾼 본 → 옛 test 판정 `[('base', 33, 'import sizing_recipe as sr'), ('new', 33, 'import theta_search as sr')]` FAIL(독립 검토 측정, r1 `C:/g219` 재측정 같음).
   Phase 3 design §7.1 B군 목록에는 `test_ts6_probe_relocate.py:528`(파일 존재 앵커)만 있고 이 test 함수(672행)는 없다 -- **Phase 3 쪽 누락**. **Phase 3 F1/F2 담당(오케스트레이터)에 보고**: F1 card(또는 design 30 §7.1 B군)에 이 test와 V5 처리를 넣을 것. 권고 = #2 계약 8 (다)와 같은 규칙(판정 대상 = 이동 커밋 `9d6800e` blob) -- 그러면 F1·#2·이후 card 모두 이 test를 건드리지 않는다. F1이 (다)를 쓰면 #2 계약 8은 무동작이고 D1은 #2 V5 범위에서 빠진다(card P3-5).
3. **레지스트리 검사 계약 test**: `test_reg_check.py::test_main_on_this_repository_is_clean`이 레지스트리 §7 이름이 엔진에 있는지(`stale`)와 §1 D 수(`count`)를 판정한다. 코드만 지우면 `stale` 5건(실측) -- 레지스트리 정정이 **같은 code 커밋**이어야 한다(card 계약 9).
4. **UD-0 질문 문안이 U-02 처리 칸 변경을 드러내지 않는다**: `phase4_approval_question.md` UD-0은 "옛 함수 삭제·이관 #2~#4"만 적는다(함수 이름·`보류(Phase 4)` → 삭제 문장 0줄).
   U-02 기록 '재검토'는 "승인표를 바꾸는 것은 사용자 승인 사항"이고 템플릿 '작성 전 실측' 9는 기록 범위 설명에 card id와 바뀌는 것이 원문으로 있어야 한다고 한다. Phase 3 D-10 선례(처리 칸 9개 변경을 UD-0 문장에 원문 인용)처럼 보강 권고 -- 문안 예:
   "> 레지스트리 §7에서 `보류(Phase 4)`인 `estimate_area_budget`(DF-09 식 결함 포함)·`solve_diode_stack_current`·`load_derived_bounds`/`derived_bounds_path`·`check_multi_leaf_hub_parity`/`MultiLeafHubParityVerdict`를 지웁니다(#2 -- U-02 승인표의 처리 칸 변경). `node_pole_estimate`·`signal_path_nodes`는 test oracle로(#3), `build_toy_lut`·`_invq_newton`은 test 픽스처로(#4) 옮깁니다."
5. **docstring 수정은 V3 비용 0**: `mutate_changed.def_hash`가 docstring을 뺀 `ast.dump`라 docstring 9곳을 고친 모의 head도 changed defs 0(실측). 그래서 card는 지운 이름의 본문 언급까지 0으로(계약 4) -- 낡은 안내 문장을 남기지 않는다.
6. **V8 판정 공백 -- 해소(design v0.9.9)**: design v0.9.9가 P-38·§10.1-0("#2처럼 폴백 경로를 바꾸지 않는 card는 'N/A -- 계측 미도입, 폴백 경로 불변'")을 넣었다. card는 결정 필요 항목에서 빼고 '판정 유형 근거'에 V8 = 'N/A -- 계측 미도입, 폴백 경로 불변'(P-38 인용)으로 적었다(r1, 독립 검토 S3).
7. 관찰(범위 밖, 백로그 후보): SR 7871·7883의 실행 오류 메시지가 `python tests/derive_achievable_bounds.py`(TS6 이동 전 경로)를 안내한다 -- 지금 경로는 `tests/tools/`. 사용자에게 보이는 문자열이라 V3·E-INST와 무관, 다음에 그 함수를 고치는 card나 문서 card에서.

## 4. 다음 3 card(순서대로)

선두 사슬(design §5.2, DAG `#2 → #5 → #6 → {#7 → #8, #9}`):

1. **#5 `ts4-selfref-oracle`**(TS4, red-green, 선행 #2) -- V4 lint 산출 목록의 자기참조·복사 기대값을 oracle 4종으로 바꾼다(D-1 삭제로 `test_s028` 대상은 사라지고, 범위 = 계획 TS4 정정 문구 'V4 lint 산출 목록').
2. **#6 `cc4a-failure-classes`**(CC-4 앞부분, red-green, 선행 #5) -- N3.14 실패 클래스·`FailureRecord`·`exit_code_for`를 만들고 하네스 `run()`이 예외를 삼키고 exit 0 하던 것(F15 4회로)을 클래스별 exit code로 바꾼다(DF-18 exit 몫·DF-37 하네스 몫).
3. **#7 `cc7a-search-extract`**(CC-7a, equivalence, 선행 #6) -- θ 탐색부를 `optimize_full_circuit_budget`(Phase 3 뒤 MOD8)에서 MOD6 함수로 추출한다(E-INST·E-LIB 동일). 같은 시점 병렬: **#9 `cc8-noop-activations`**(선행 #6 -- `activations_out`·`noop_proof.py`), 그리고 언제든 병렬 뿌리 **#3**(D-6 → test oracle, DF-06·B26-4 앞)·**#4**(D-7 → test 픽스처).

## 5. TS4 대상 예비 실측(#5 card 작성 전 실측의 출발점 -- 판정 수치 아님)

`p4kit_first/v4scan.py`: `test_lint.py`에 엔진 5모듈 최상위 정의 363개 전부를 subject로 주고 `tests/unit`·`tests/contracts` 40파일에 돌림(dd60db6). 판정 문장 수: (2) NO-SUBJECT 718·UNJUDGED 582·PASS 37·**FAIL 14**, (1) **FAIL 18**.
FAIL 32문장 / test 24개(`out/v4scan.txt`). 그중 `test_s028`(1문장)은 #2가 지우고, `test_s052_compensation`·`test_s054_section`(2문장)은 V4 면제 `20260923-c9-v4-exempt`(규칙 (1))가 덮는다.
그래서 #2 뒤 TS4 후보는 0이 아니다(29문장 / 21 test -- (1) 규칙의 DESIGN-GAP 오거부(다른 입력 불변식) 여부는 #5 작성 전 실측에서 test마다 가린다). design §5.2 #5 '[미확인: 산출이 0이면 계획 정정으로 닫는다]'는 닫는 갈래가 아니다.

## 6. 산출물과 확인

* `draft_p4_first.spec.md` -- `parse_spec_card`(gate `master` 도구, `git archive gate/master tools/gates` → `C:/g204/gt`): id `20261002-d4-delete-unwired`, phase `4`, `equivalence`, `gate_change: no`, approval 1, 절 11개 전부(템플릿 순서). `interface_card.py` 생성 성공(기존 함수 22개 -- `p4kit_first/out/interface.generated.md`).
  **r1 재실행**(gate 도구 = `git archive 36e170e tools/gates` → `C:/g219/gt`): `parse_spec_card(expect_id=…)` 통과 -- id·phase `4`·`equivalence`·`gate_change: no`·approval 1, 절 11개 템플릿 순서. `interface_card.py --root <36e170e clone>` 생성 성공(기존 함수 22개, 표는 심볼·시그니처만 -- 계약 8의 이동 커밋 sha는 card 계약 문장으로 test-author에게 간다).
  r1 모의 card 수치(suite·V3·V5·V7·reg_check·계약 8 공격 변이)는 card '작성 전 실측' 15. 측정 스크립트는 `C:/g219`에서만 돌리고 삭제했다(측정 전용, 역할 산출물 아님).
* `p4kit_first/` -- `m_tests.py`(test 참조 AST), `v3sim.py`(V3 모의), `simM.py`(모의 병합본 -- 측정 전용, 역할 산출물 아님), `v4scan.py`, `run_suites.sh`, `out/`(refs·v3·v4·suite·reg_check 출력).

## 7. design 개정 요청(r1 -- design 파일 소유자에게. 이 메모 작성자는 `draft_phase4_design.md`를 고치지 않는다)

card D1 기본안이 (가) → **(다)**로 바뀌었으므로 design v0.9.9의 다음 문장을 맞춰 달라:
1. §5.1 #2 행 (ii): "TS6 계약 test … 허용 차이를 '경로 줄 + 이 card의 사이드카 문장'으로 좁혀 넓힘(card 결정 D1 기본안 (가) -- 그 밖 줄 동일 판정은 유지)" → "TS6 계약 test …의 판정 대상을 HEAD 도구에서 **이동 커밋 `9d6800e` blob**으로 바꿈(card 결정 D1 기본안 (다) -- '이동이 경로 줄만 바꿨다'는 계속 판정, HEAD 도구의 '경로 줄 외 그대로' 영구 고정은 풀림)". 같은 행의 "Phase 3 F1이 같은 test를 먼저 넓혔으면 … D1은 '그 규칙에 이 card의 사이드카 문장 추가'로 줄어든다" → "Phase 3 F1이 같은 (다) 규칙을 쓰면 #2 계약 8은 무동작이고 D1은 V5 범위에서 빠진다".
2. §7.4 #2 V5 줄: "TS6 도구 내용 고정 test 허용 차이 '경로 줄 + #2 사이드카 문장'(card D1 기본안 (가), …)" → "TS6 도구 test 판정 대상 = 이동 커밋 blob(card D1 기본안 (다), …)".
3. §7 'v0.9.9 대비' (1)과 머리 버전 줄(20행)의 "기본안 (가)" → "(다)".
4. (새 사실, Phase 3 쪽) design 30 §7.1 B군에 `test_ts6_probe_relocate.py::test_moved_tool_matches_base_except_path_lines`(672행)가 없다 -- F1이 도구 33행을 바꾸면 FAIL(확정, §3-2). Phase 4 design §9(Phase 3 의존) 또는 §8.1 준비 표에 'Phase 3 F1이 (다)로 처리하면 #2 계약 8 무동작'을 한 줄로 적는 것을 권고. 새 사용자 결정 0(D1은 #2 V5 기록 범위 한 줄 그대로).
