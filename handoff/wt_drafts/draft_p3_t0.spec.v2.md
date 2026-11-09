---
id: 20260930-p3-tests-location-free
phase: 3
evidence_type: test-only
gate_change: no
approval: 20260930-30-module-split-design
approval: 20260930-p3-tests-location-free
---
## 의도

design `30-module-split`(초안 v2) §7.1 A군, card T0. Phase 3 이동 card(M1~M9)는 equivalence -- "test 커밋이 그대로이고 base와 병합본 모두 통과"(계획 N3.12.3 686행)다.
그런데 계약 test 셋이 **정의가 특정 파일에 있다고 가정**해, 그 정의를 옮기는 첫 M card에서 병합본이 FAIL하거나(equivalence 불성립) 판정이 **조용히 공허**해진다:

* `contracts/test_ic5.py:47-69` `_DOMAIN_TABLE` 키가 (파일 이름, 함수 이름) 21개 -- 함수를 옮기면 "design §5.6 영역 표의 함수가 대상에 없다" FAIL.
* `contracts/test_dup_w_calc.py:442` `size_transistor` 정의를 `sizing_recipe.py`에서만 찾는다 -- MOD4로 옮기면 FAIL.
* `contracts/test_ts6_dead_probes.py:219-222` `_L_ROLE_MULTIPLIERS` 바인딩 검사 범위가 `sizing_recipe.py` 한 파일 -- 옮긴 뒤 다른 파일에 그 이름이 다시 생겨도 통과(**공허**),
  `:259-263` `audit_vsb_consistency`의 운영 호출자를 `sizing_recipe.py`에서만 찾는다 -- 호출자 `_build_theta_evaluator`가 MOD6로 가면 FAIL.

이 셋을 **정의 위치에 무관한 판정**으로 바꾼다. 규칙 R-DEF(design v2 §7.1): 이름 n의 정의 파일 = `A/*.py`(하위 디렉터리 제외)와 `workspaces/run_harness.py` 중 최상위에서 n을
def·class·대입으로 바인딩하는 파일(AST; import로 받은 이름은 정의가 아니다). 정의 파일이 정확히 하나가 아니면 FAIL(0 = 공허, 2 이상 = 모호·사본). **판정 범위는 넓어지기만
한다**(한 파일 → 엔진 전체). A = `skills/analog-gmid-design/assets`.

모듈 이름으로 import하거나 파일 존재를 앵커로 쓰는 계약 test(B군 10파일 -- `test_d_delete_dead`·`test_d_delete_telescopic`·`test_d_move_tests`·`test_dup_w_calc:56·72-75`·
`test_df35_harness_paths:206`·`test_ts6_probe_relocate:528`·`test_ts6_dead_probes:229`·`test_restore_plan_functions`·`test_ic3`·`test_df36_instance_relpath`)는 shim이 살아
있는 동안 통과하므로 이 card의 범위가 아니다 -- F1(호출부 갱신)에서 고친다(최소 수정, 계획 534행 '호출부 갱신'). 엔진 소스는 바뀌지 않는다.

## 관찰 가능한 계약

1. **공용 도우미** `A/tests/contracts/_engine_defs.py`(test-author): `engine_source_files()` = `A/*.py`(하위 디렉터리 제외) + `workspaces/run_harness.py`, `defining_files(name)` =
   R-DEF의 정의 파일 목록(최상위 def·class·대입·주석 달린 대입, 메서드는 `Class.method`). 세 test 파일이 이것을 부른다(만들면 배선). 파일 이름이 `_`로 시작해 pytest가
   수집하지 않는다.
2. `test_ic5.py`: `_DOMAIN_TABLE` 키를 함수 이름으로 바꾼다 -- **값(영역 집합) 21개는 그대로**. 표의 이름마다 대상 함수(모든 깊이, 기존 `_collect_targets`)가 정확히 하나여야 하고
   (0 = "대상에 없다", 2 이상 = 모호), 그 하나의 docstring 영역 값 = 표 값. 형식 검사(2)와 합성 docstring test 5개는 그대로. 실패 메시지는 발견된 `파일:줄`을 그대로 보인다.
3. `test_dup_w_calc.py::test_size_transistor_calls_new_function`: `size_transistor`의 정의 파일(R-DEF, 정확히 하나)에서 본문이 `width_from_id_density`를 부르는지 본다.
4. `test_ts6_dead_probes.py::test_sizing_recipe_source_has_no_l_role_multipliers`: `engine_source_files()` 전부에서 `_L_ROLE_MULTIPLIERS` 바인딩 0(기존 `assert_source_binds_no_symbol`을
   파일마다). `::test_audit_vsb_consistency_has_operational_caller`: `engine_source_files()` 전부에서 운영 호출자(기존 `_NON_OPERATIONAL_PREFIXES` 규칙) 1개 이상.
   **test 함수 이름은 바꾸지 않는다**(수집 test id 불변 -- V2 test-only 매핑).
5. **범위 비약화**: 바뀐 test마다 판정 대상 집합이 base 판정 대상 집합의 상위집합이다(한 파일 → 엔진 전체), assert 수가 줄지 않는다, 표 값·기대 호출 이름은 그대로다.
6. **위치 독립(LOC-FREE)**: base 트리에서, 그리고 **정의를 다른 파일로 옮긴 합성 트리**(격리 복제본에서 `check_quasi_static`·`size_transistor`·`_build_theta_evaluator`의 def
   텍스트를 원래 파일에서 잘라 새 파일 `A/zz_loc_free_probe.py`에 붙이고 원래 파일 끝에 `from zz_loc_free_probe import <이름>`을 더한 트리 -- 바뀐 세 test는 소스를 AST로만
   읽는다)에서 바뀐 test 함수가 모두 PASS한다. 같은 합성 트리에서 base의 옛 test는 FAIL(ic5·dup_w_calc·ts6 caller)한다 -- 이 card가 필요한 이유의 증거.
7. **모호 거부**: 합성 트리에서 `size_transistor`를 새 파일에 **복사**(원래 것도 남김)하면 계약 3의 test가 FAIL(정의 파일 2개).
8. 엔진 소스·`A/tests/**`의 다른 파일은 바뀌지 않는다.

## 신규 시그니처

| 모듈 | 심볼 | 시그니처 |
|---|---|---|

## 판정 유형 근거

test-only: 엔진 소스가 바뀌지 않아 code 커밋이 없다(`00-common` §8.1 `code_commit: null`, 계획 N3.12.3 '순서 4·5 생략'). 판정 유형은 커밋 모양이 정한다(`20-dead-code-dup` §8 P2 정정,
`20260923-probe-promote-clean` 13행). red-green은 성립하지 않는다(피검 코드가 base와 같아 새 test가 base에서 FAIL할 수 없다). 계획 N3.12.3의 test-only 열거(TS0·TS2·TS3·TS5·TS7,
TS6 승격·삭제, redteam 데이터 게이트 변경)에 Phase 3 T0가 없다 -- design 30 승인(UD-0)이 열거에 더하는 개정을 덮는다.
증거(V2 test-only, `checks.V2.basis`): 매핑 = 바뀐 test id → 같은 test id(계약 4), base 트리에서 세 파일의 모든 test PASS + 계약 6·7 합성 트리 실행 결과.

## oracle 종류와 출처

(c) 동작 보존: 바뀐 test가 base 트리에서 base의 옛 test와 같은 판정(PASS)을 낸다. (a) 구성: 계약 6·7의 합성 이동 트리 -- 정의를 어디로 옮겼는지가 구성으로 정해져 기대(PASS·모호 FAIL)가
정해진다. `_DOMAIN_TABLE` 값은 기존 (d)(design `10-test-separation` §5.6 영역 표) 그대로.

## 거부해야 할 입력

정의 파일 0개(공허) 또는 2개 이상(복사·모호) → FAIL(계약 2·3·7). `_L_ROLE_MULTIPLIERS`를 엔진 어느 파일에서든 다시 바인딩 → FAIL(계약 4 -- base 판정보다 넓다).

## library 회로 적용 여부

해당 없음(소스 AST 판정).

## 무동작 판정 입력(무발동 값)

base 트리 전체 `PT`(`10-test-separation` §10): 수집 test id 집합과 판정이 base와 같다(바뀐 세 파일 포함). 도우미 파일 추가가 다른 test의 전수 스캔(`test_ts3_no_print_verdicts`의
print 판정 토큰, `test_d_delete_dead`·`test_d_move_tests`의 삭제·이관 이름 참조, `test_ic_markers_match_plan`의 `contracts/*.py` 표식 대조)에서 새 발견을 만들지 않는다.

## 재현할 수치

없음.

## 결정 필요 항목

V5 승인(design v2 §9.2 UD-6): `weakening_diff`가 문자열 상수 변경(`"sizing_recipe.py"` 등)을 '기대값·픽스처 리터럴 변경'으로 잡는다. test 커밋 뒤 그 diff 해시로 승인 기록
`20260930-p3-tests-location-free`(`target_kind: diff`)를 받는다 -- 근거: 판정 범위 확대 + 유일성 검사 추가, 기대값 불변(계약 5).

## 작성 전 실측

(기준 gate `master` `cd64170`)
1. 사실: `git grep -c -E "(sizing_recipe|stick_diagram|topology_library|design_report|audit_current_forced)\.py" -- skills/analog-gmid-design/assets/tests ':!skills/analog-gmid-design/assets/tests/probes'`
   → contracts 10파일 + unit 6 + tools 2. 파일별 `grep -n` 문맥으로 A군 3파일(위 의도의 줄)만 실제 트리의 정의 위치를 가정함을 확인(`test_reg_check.py` 13건·`test_probe_dup_scan.py`·
   `test_d_*`의 `import sizing_recipe` 문자열은 합성 입력, `unit/test_selftest_*`는 주석·문자열). R-DEF 유일성: `A/*.py`+`run_harness.py` 최상위 바인딩 중복 0, ic5 표 21개 이름은
   모든 깊이에서 각 1개, `size_transistor`·`width_from_id_density`·`audit_vsb_consistency`·`_build_theta_evaluator` 정의 파일 = `sizing_recipe.py` 1개, `_L_ROLE_MULTIPLIERS` 0개
   (`$PY -B -c` AST 스캔, design v2 부록 A M24).
2. 이름 충돌: 새 파일 `A/tests/contracts/_engine_defs.py` -- `git grep -n "glob(" -- skills/analog-gmid-design/assets/tests` → `contracts/*.py`를 읽는 것은
   `test_ic_markers_match_plan.py:91`(표식 대조 -- 도우미에 `gmid_ic` 표식 없음), `rglob("*.py")` 전수 스캔은 `test_ts3_no_print_verdicts:59`·`test_d_delete_dead:87`·
   `test_d_delete_telescopic:97`·`test_d_move_tests:87`(도우미가 print 판정 토큰·삭제·이관 이름을 쓰지 않으면 무발동 -- 무발동 절). `test_*` 수집 glob과 겹치지 않는다(`_` 접두).
3. 원칙: 범위 비약화 -- 계약 5, 위치 독립 -- 계약 6, 모호 거부 -- 계약 7, 만들면 배선 -- 계약 1(세 test가 부른다).
4. 쓰기 경로: 세 test·도우미 = test-author(`A/tests/**`), 엔진 소스 읽기는 test 실행 시 AST로만(test-author의 소스 열람 금지와 무관 -- 기존 test와 같은 방식), 합성 트리 실행 = auditor.
5. 계획서 소비자: 지우는 이름 없음(`_SIZING_RECIPE` 상수는 229행이 계속 쓰므로 남긴다). `grep -n "check_quasi_static" docs/02-design/features/*.md` → oracle (d)의 원천인
   design `10-test-separation` §5.6 영역 표(252~274행, 승인 `20260922-10-test-separation-design`)가 `| 파일 | 함수 | 영역 | 이유 |` 형식이다(254행 `audit_current_forced.py`,
   255행 `sizing_recipe.py`, 262행 `stick_diagram.py` …). 영역 값은 그대로 두고 '파일' 열이 판정 키가 아니라 설명임(위치는 R-DEF)을 적는 문서 개정이 필요하다 -- design 30 승인
   (UD-0)이 덮고 이 card의 문서 커밋(오케스트레이터)에서 반영한다.
6. 미배선: 새 엔진 def 없음. 도우미는 세 test가 부른다.
7. 기존 계약 test: 바뀌는 것이 계약 test 자체 -- V5 승인 경로(결정 필요 항목). B군 10파일은 F1.
