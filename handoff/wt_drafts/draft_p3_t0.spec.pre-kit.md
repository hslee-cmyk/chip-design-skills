---
id: 20260930-p3-tests-location-free
phase: 3
evidence_type: test-only
gate_change: no
approval: 20260930-30-module-split-design
approval: 20260930-p3-tests-location-free
---
## 의도

design `30-module-split`(초안 v8) §7.1 A군, card T0. Phase 3 이동 card(M1~M9)는 equivalence -- "test 커밋이 그대로이고 base와 병합본 모두 통과"(계획 N3.12.3 686행)다.
그런데 계약 test 셋이 **정의가 특정 파일에 있다고 가정**해, 그 정의를 옮기는 첫 M card에서 병합본이 FAIL하거나(equivalence 불성립) 판정이 **조용히 공허**해진다:

* `contracts/test_ic5.py:47-69` `_DOMAIN_TABLE` 키가 (파일 이름, 함수 이름) 21개 -- 함수를 옮기면 "design §5.6 영역 표의 함수가 대상에 없다" FAIL.
* `contracts/test_dup_w_calc.py:442` `size_transistor` 정의를 `sizing_recipe.py`에서만 찾는다 -- MOD4로 옮기면 FAIL.
* `contracts/test_ts6_dead_probes.py:219-222` `_L_ROLE_MULTIPLIERS` 바인딩 검사 범위가 `sizing_recipe.py` 한 파일 -- 옮긴 뒤 다른 파일에 그 이름이 다시 생겨도 통과(**공허**),
  `:259-263` `audit_vsb_consistency`의 운영 호출자를 `sizing_recipe.py`에서만 찾는다 -- 호출자 `_build_theta_evaluator`가 MOD6로 가면 FAIL.
* **(v5, B26-1 병합 뒤 생김)** `contracts/test_b26_rail_accessor.py`의 계수 test(B26-1 계약 3): `stick_diagram.rail_declaration` **모듈 속성**을 계수 래퍼로 바꿔 호출 수를 센다. 호출자
  `load_topology`는 자기 모듈 전역에서 그 이름을 읽으므로, `load_topology`가 M3에서 MOD3(`circuit_state_graph.py`)로 가면(`rail_declaration`은 design 30 D-19 결정에 따라 M2에서 MOD2 또는 M3에서 MOD3 -- 어느 쪽이든) shim의 속성을 바꿔도
  호출을 가로채지 못해 계수가 0 → FAIL(equivalence 불성립). HEAD `7535799`에는 엔진 모듈 속성을 바꾸는 test가 없다(`git grep -n setattr -- '*.py'` 0건; v7: `a796468`에서도 `tools/` 밖 0건 -- 4차 검토 m1) -- 이 test가 처음이다.
  사용자 결정 A2(승인 기록 `20260930-b26-before-phase3`)로 B26-1이 Phase 3 전에 병합되므로 이 card의 범위에 넣는다. **이 card는 B26-1 병합 뒤 base에서 시작한다.**
  병합은 **Phase 2 DoD PASS 뒤**다(`phase: 3` card -- 계획 991행 "이전 Phase DoD PASS", design 30 D-23, v6). 그 전에는 spec card 초안·작성 전 실측만 한다.
  **v7(확정 순서, design 30 §8.1)**: P10b → Phase 2 DoD → 면제 묶기(34) → 범위 정책(35) → B34 → B26-1(앞선 test 보강 card 포함) → B33(33) → Phase 3. 이 card의 base는 B33 병합 뒤 master다.

이 셋을 **정의 위치에 무관한 판정**으로 바꾼다. 규칙 R-DEF(design 30 §7.1): 이름 n의 정의 파일 = `A/*.py`(하위 디렉터리 제외)와 `workspaces/run_harness.py` 중 최상위에서 n을
def·class·대입으로 바인딩하는 파일(AST; import로 받은 이름은 정의가 아니다). 정의 파일이 정확히 하나가 아니면 FAIL(0 = 공허, 2 이상 = 모호·사본). **판정 범위는 넓어지기만
한다**(한 파일 → 엔진 전체). A = `skills/analog-gmid-design/assets`.

모듈 이름으로 import하거나 파일 존재를 앵커로 쓰는 계약 test(B군 11파일 -- `test_d_delete_dead`·`test_d_delete_telescopic`·`test_d_move_tests`·`test_dup_w_calc:56·72-75`·
`test_df35_harness_paths:206`·`test_ts6_probe_relocate:528`·`test_ts6_dead_probes:229`·`test_restore_plan_functions`·`test_ic3`·`test_df36_instance_relpath`, v7: P9가 더한 `test_dup_kcl_edges:35`(`importlib.import_module("stick_diagram")`)
-- design 30 §7.1, 4차 검토 m3)는 shim이 살아
있는 동안 통과하므로 이 card의 범위가 아니다 -- F1(호출부 갱신)에서 고친다(최소 수정, 계획 534행 '호출부 갱신'). 엔진 소스는 바뀌지 않는다.

## 관찰 가능한 계약

1. **공용 도우미** `A/tests/contracts/_engine_defs.py`(test-author): `engine_source_files()` = `A/*.py`(하위 디렉터리 제외) + `workspaces/run_harness.py`, `defining_files(name)` =
   R-DEF의 정의 파일 목록(최상위 def·class·대입·주석 달린 대입, 메서드는 `Class.method`), **`binding_files(name)`**(v5) = 엔진 소스 파일 중 최상위에서 n을 **정의하거나 import로 바인딩하는**
   파일 목록(`from M import n`·`from M import x as n` -- AST). 네 test 파일(v4의 셋 + v5 계약 10)이 이것을 부른다(만들면 배선). 파일 이름이 `_`로 시작해 pytest가
   수집하지 않는다.
2. `test_ic5.py`: `_DOMAIN_TABLE` 키를 함수 이름으로 바꾼다 -- **값(영역 집합) 21개는 그대로**. 표의 이름마다 대상 함수(모든 깊이, 기존 `_collect_targets`)가 정확히 하나여야 하고
   (0 = "대상에 없다", 2 이상 = 모호), 그 하나의 docstring 영역 값 = 표 값. 형식 검사(2)와 합성 docstring test 5개는 그대로. 실패 메시지는 발견된 `파일:줄`을 그대로 보인다.
3. `test_dup_w_calc.py::test_size_transistor_calls_new_function`: `size_transistor`의 정의 파일(R-DEF, 정확히 하나)에서 본문이 `width_from_id_density`를 부르는지 본다.
4. `test_ts6_dead_probes.py::test_sizing_recipe_source_has_no_l_role_multipliers`: `engine_source_files()` 전부에서 `_L_ROLE_MULTIPLIERS` 바인딩 0(기존 `assert_source_binds_no_symbol`을
   파일마다). `::test_audit_vsb_consistency_has_operational_caller`: `engine_source_files()` 전부에서 운영 호출자(기존 `_NON_OPERATIONAL_PREFIXES` 규칙) 1개 이상.
   **test 함수 이름은 바꾸지 않는다**(수집 test id 불변 -- V2 test-only 매핑). 모듈 상수 `_SIZING_RECIPE`(60행)는 이 두 test(221·222·261·262행)만 쓰므로 바꾼 뒤 소비자가 0이 되어
   **지운다**(죽은 이름을 남기지 않는다 -- 저장소 전체 `git grep -n _SIZING_RECIPE` 결과가 이 파일의 그 다섯 줄뿐, 계획서·design 소비자 0).
5. **범위 비약화**: 바뀐 test마다 판정 대상 집합이 base 판정 대상 집합의 상위집합이다(한 파일 → 엔진 전체), assert 수가 줄지 않는다, 표 값·기대 호출 이름은 그대로다.
6. **위치 독립(LOC-FREE)**: base 트리에서, 그리고 **정의를 다른 파일로 옮긴 합성 트리**(격리 복제본에서 `check_quasi_static`·`size_transistor`·`_build_theta_evaluator`의 def
   텍스트를 원래 파일에서 잘라 새 파일 `A/zz_loc_free_probe.py`에 붙이고 원래 파일 끝에 `from zz_loc_free_probe import <이름>`을 더한 트리 -- 바뀐 세 test는 소스를 AST로만
   읽는다)에서 바뀐 test 함수가 모두 PASS한다. 같은 합성 트리에서 base의 옛 test는 FAIL(ic5·dup_w_calc·ts6 caller)한다 -- 이 card가 필요한 이유의 증거.
7. **모호 거부**: 합성 트리에서 `size_transistor`를 새 파일에 **복사**(원래 것도 남김)하면 계약 3의 test가 FAIL(정의 파일 2개).
8. 엔진 소스·`A/tests/**`의 다른 파일은 바뀌지 않는다(바뀌는 파일 = 세 test 파일 + 새 도우미 + v5 계약 10의 `test_b26_rail_accessor.py`).
9. **전수 스캔 test와 충돌하지 않는 이름**: 도우미와 바뀐 세 파일의 **새 줄**은 다음 토큰을 식별자·문자열로 쓰지 않는다(쓰면 전수 스캔 test가 새 발견을 낸다):
   * `test_d_delete_dead.py` `_DELETED_FUNCTIONS`·`_DELETED_METHODS`: `converge_with_parasitics`, `render_stick_diagram`, `slew_rate`, `suggest_headroom_stack_groups`, `fT`, `junction_cap`.
   * `test_d_delete_telescopic.py` `_DELETED_NAMES`·`_DELETED_CONSTANTS`·`_DELETED_FIELDS`: `_cmfb_amp_gain_diode_load`, `_cmrr_telescopic_class_ab`, `_cmrr_telescopic_class_ab_cmfb`,
     `_load_telescopic_topology_cached`, `_psrr_telescopic_class_ab`, `_psrr_telescopic_class_ab_cmfb`, `_telescopic_class_ab_open_loop_gains`, `_telescopic_class_ab_open_loop_response`,
     `_telescopic_open_loop_device_names`, `_TELESCOPIC_FIXED_BASE`, `_open_loop_gains_cache`.
   * `test_d_move_tests.py` `_MOVES`: `RegressionVerdict`, `_REGRESSION_ENGINES`, `_run_optimize_multistage_case`, `find_interleaved_symmetric_splits`, `run_regression_case`
     (모듈 이름 `regression_runner`·`interleave_splits`를 import하지 않는다).
   * `test_ts3_no_print_verdicts.py`: `print(...)`·`logging`/`logger`/`log` 호출 인자 안의 `PASS`·`FAIL` 문자열 토큰.
   목록은 `wt/_drafts/p3v3_facts.py` `m6_scan_names`(cd64170)에서 뽑았다. auditor: 바뀐 줄(`git diff -U0 <base> <test_commit> -- <바뀐 다섯 파일>`의 `+` 줄)에 위 토큰 0.
   (v5) B26-1·B34 병합본에서 목록을 다시 뽑는다 -- 두 card가 전수 스캔 test의 목록을 바꾸지 않을 것으로 보지만(두 card 모두 삭제·이관 이름 없음) 확인한다.
10. **(v5) B26-1 계수 test의 위치 독립**: `test_b26_rail_accessor.py`의 계수 래퍼는 `stick_diagram` 한 모듈이 아니라 **`binding_files("rail_declaration")`의 모든 엔진 모듈**(정의 파일 + import로
    바인딩한 파일 -- 재수출 shim 포함)의 그 속성을 같은 래퍼로 바꾼다(`monkeypatch.setattr`, 모듈은 파일 줄기로 import). 정의 파일은 R-DEF로 정확히 하나여야 한다(0·2 이상이면 FAIL). B26-1 계약 3의
    불변식(호출 수 = `load_topology` 호출 수 + 선언을 가진 연결 파일 수, 반복 평가에서 늘지 않음)과 입력·기대값은 **그대로**다(계약 5 -- 판정 대상이 넓어지기만 한다: 한 모듈의 속성 → 그 이름을
    바인딩한 모든 모듈). test 함수 이름은 바꾸지 않는다. 이 test 파일의 다른 test(`sizing_recipe._metric_kcl_residual` 이름 호출 -- design §7.1 B군)는 F1 몫이라 바꾸지 않는다.
    위치 독립 증거(계약 6에 더함): 합성 트리에서 `load_topology` 정의를 새 파일로 옮기고(새 파일은 원래 파일에서 필요한 이름을 import, 원래 파일 끝에 재수출) `rail_declaration`은 다른 새 파일로
    옮긴 뒤(원래 파일 재수출) 바뀐 계수 test가 PASS, base의 옛 계수 test는 FAIL(계수 0). 합성 트리 구성 세부는 B26-1 병합본의 실제 test 모양을 보고 test-author가 정한다(구성이 기대를 정한다 --
    oracle (a)).

## 신규 시그니처

| 모듈 | 심볼 | 시그니처 |
|---|---|---|

## 판정 유형 근거

test-only: 엔진 소스가 바뀌지 않아 code 커밋이 없다(`00-common` §8.1 `code_commit: null`, 계획 N3.12.3 '순서 4·5 생략'). 판정 유형은 커밋 모양이 정한다(`20-dead-code-dup` §8 P2 정정,
`20260923-probe-promote-clean` 13행). red-green은 성립하지 않는다(피검 코드가 base와 같아 새 test가 base에서 FAIL할 수 없다). 계획 N3.12.3의 test-only 열거(TS0·TS2·TS3·TS5·TS7,
TS6 승격·삭제, redteam 데이터 게이트 변경)에 Phase 3 T0가 없다 -- design 30 승인(UD-0)이 열거에 더하는 개정을 덮는다(문안 `_drafts/p3_doc_amendments.md` §3, design 커밋에서 반영).
증거(V2 test-only, `checks.V2.basis`): 매핑 = 바뀐 test id → 같은 test id(계약 4), base 트리에서 세 파일의 모든 test PASS + 계약 6·7 합성 트리 실행 결과. 스키마상 test-only는
`red`·`equivalence` 필드를 갖지 않으므로(`_schema.json` allOf) 합성 트리 결과는 `basis` 문장으로만 남는다(선례 `20260923-probe-promote-clean`).

## oracle 종류와 출처

(c) 동작 보존: 바뀐 test가 base 트리에서 base의 옛 test와 같은 판정(PASS)을 낸다. (a) 구성: 계약 6·7의 합성 이동 트리 -- 정의를 어디로 옮겼는지가 구성으로 정해져 기대(PASS·모호 FAIL)가
정해진다. `_DOMAIN_TABLE` 값은 기존 (d)(design `10-test-separation` §5.6 영역 표) 그대로.

## 거부해야 할 입력

정의 파일 0개(공허) 또는 2개 이상(복사·모호) → FAIL(계약 2·3·7). `_L_ROLE_MULTIPLIERS`를 엔진 어느 파일에서든 다시 바인딩 → FAIL(계약 4 -- base 판정보다 넓다).

## library 회로 적용 여부

해당 없음(소스 AST 판정).

## 무동작 판정 입력(무발동 값)

base 트리 전체 `PT3`(design 30 §10 -- `10-test-separation` §10 `PT`에서 `--gmid-phase=1`만 `--gmid-phase=3`, card V1과 같은 Phase 값; v8 -- 5차 검토 B1: v7의 `PT`는 `--gmid-phase=1`이라 phase 2·3 표식 케이스의 실패가 xfail로 지나갔다): 수집 test id 집합과 판정이 base와 같다(바뀐 세 파일 포함). 도우미 파일 추가가 다른 test의 전수 스캔(`test_ts3_no_print_verdicts`의
print 판정 토큰, `test_d_delete_dead`·`test_d_delete_telescopic`·`test_d_move_tests`의 삭제·이관 이름 참조, `test_ic_markers_match_plan`의 `contracts/*.py` 표식 대조)에서 새 발견을
만들지 않는다(계약 9의 토큰 목록).

## 재현할 수치

없음.

## 결정 필요 항목

V5 승인(design 30 §9.2 '뒤에 올 승인' -- 착수 전 사용자 결정이 아니다. 초안 v3의 UD-6을 2차 검토 §5 권고대로 T1·F1의 V5 승인과 같은 목록으로 옮겼다): `weakening_diff`가 문자열 상수 변경(`"sizing_recipe.py"` 등)을 '기대값·픽스처 리터럴 변경'으로 잡는다. test 커밋 뒤 그 diff 해시로 승인 기록
`20260930-p3-tests-location-free`(`target_kind: diff`)를 받는다 -- 근거: 판정 범위 확대 + 유일성 검사 추가, 기대값 불변(계약 5), 죽은 상수 삭제(계약 4), (v5) 계수 래퍼 대상 확대(계약 10 --
B26-1 계약 test의 판정 기준 소유자는 B26-1 승인이므로 승인 범위 설명에 'B26-1 계약 3의 불변식·기대값 불변, 래퍼 설치 모듈만 넓힘'을 적는다).

## 작성 전 실측

(기준 gate `master` `cd64170`; `7535799`(B28 병합 뒤)에서 `git diff --stat cd64170 HEAD -- skills/analog-gmid-design/assets` 0 -- 아래 줄 번호 불변.
**v7(4차 검토 m1) `a796468`에서 다시 확인**: `git diff --stat 7535799 a796468 -- skills/analog-gmid-design/assets` = `stick_diagram.py`(P9, −11줄 순)와 새 계약 test 셋(`test_df23_inventory.py`·
`test_dup_kcl_edges.py`·`test_phase2_stale_refs.py`)뿐 -- A군 3파일·아래 1·2·5·8의 인용 줄은 그대로다. 새 셋 중 정의 위치를 가정하는 것(A군)은 0: `test_df23_inventory.py`는 엔진 소스를 읽지 않고
기록 JSON(`measured_at` 고정)만 보며, `test_phase2_stale_refs.py`는 `references/*.md`를 읽고, `test_dup_kcl_edges.py`는 모듈 이름 import(B군 -- F1)다. **v8(5차 검토 m6)**: gate `master`가 `0f23786`으로 나아갔다 -- `git diff --name-only a796468 0f23786` = `.ai/approvals/20261001-p10b-v3-equiv.md`·`docs/02-design/specs/20260930-df23-registry-record.spec.md` 2파일뿐(엔진·`tools/`·계획서·레지스트리 무변경)이라 위 확인이 그대로 성립한다.
**v5: 이 card의 base는 P9·B34·B26-1 병합 뒤 master다**(design 30 §8.1; v7 확정 순서로는 B33 병합 뒤 master -- P10b·면제 묶기·범위 정책·B34·B26-1·B33 포함). B26-1의 test 입력 갱신 규칙(그 card 계약 12)이 `A/tests/**`의 호출에 `rails=`를 더하고 B34·B26-1이 계약 test 두 파일을
더하므로, 착수 때 1·2·5와 계약 9 목록, 계약 10 대상 test의 실제 줄·모양을 그 병합본에서 다시 잰다. 아래 1의 '정의 파일 = `sizing_recipe.py`'와 A군 정의 위치는 B26-1이 정의를 옮기지 않으므로
그대로일 것으로 보지만 줄은 밀릴 수 있다)
1. 사실: `git grep -c -E "(sizing_recipe|stick_diagram|topology_library|design_report|audit_current_forced)\.py" -- skills/analog-gmid-design/assets/tests ':!skills/analog-gmid-design/assets/tests/probes'`
   → contracts 10파일 + unit 6 + tools 2. 파일별 `grep -n` 문맥으로 A군 3파일(위 의도의 줄)만 실제 트리의 정의 위치를 가정함을 확인(`test_reg_check.py` 13건·`test_probe_dup_scan.py`·
   `test_d_*`의 `import sizing_recipe` 문자열은 합성 입력, `unit/test_selftest_*`는 주석·문자열). R-DEF 유일성: `A/*.py`+`run_harness.py` 최상위 바인딩 중복 0, ic5 표 21개 이름은
   모든 깊이에서 각 1개, `size_transistor`·`width_from_id_density`·`audit_vsb_consistency`·`_build_theta_evaluator` 정의 파일 = `sizing_recipe.py` 1개, `_L_ROLE_MULTIPLIERS` 0개
   (`$PY -B -c` AST 스캔, design 30 부록 A M24; 독립 검토 재측정 일치).
2. 이름 충돌: 새 파일 `A/tests/contracts/_engine_defs.py` -- `git grep -n "glob(" -- skills/analog-gmid-design/assets/tests` → `contracts/*.py`를 읽는 것은
   `test_ic_markers_match_plan.py:91`(표식 대조 -- 도우미에 `gmid_ic` 표식 없음), `rglob("*.py")` 전수 스캔은 `test_ts3_no_print_verdicts:59`·`test_d_delete_dead:87`·
   `test_d_delete_telescopic:97`·`test_d_move_tests:87` -- 피할 토큰은 계약 9(`p3v3_facts.py` `m6_scan_names`). `test_*` 수집 glob과 겹치지 않는다(`_` 접두).
3. 원칙: 범위 비약화 -- 계약 5, 위치 독립 -- 계약 6, 모호 거부 -- 계약 7, 만들면 배선 -- 계약 1(세 test가 부른다), 죽은 이름 없음 -- 계약 4(`_SIZING_RECIPE` 삭제).
4. 쓰기 경로: 세 test·도우미 = test-author(`A/tests/**`), 엔진 소스 읽기는 test 실행 시 AST로만(test-author의 소스 열람 금지와 무관 -- 기존 test와 같은 방식), 합성 트리 실행 = auditor.
5. 계획서 소비자: `git grep -n "_SIZING_RECIPE" -- .` → `test_ts6_dead_probes.py` 60(정의)·221·222·261·262뿐(초안 v2의 "229행이 계속 쓴다"는 틀렸다 -- 229행은
   `importlib.import_module("sizing_recipe")`), docs·`.ai` 0건 → 지운다. 바뀌는 test id 둘은 `.ai/verification/20260930-df36-instance-relpath/order7/collect_m.txt`(기록된 수집 목록,
   불변 기록)에만 나온다 -- id를 바꾸지 않으므로 무관. `grep -n "check_quasi_static" docs/02-design/features/*.md` → oracle (d)의 원천인 design `10-test-separation` §5.6 영역 표
   (252~274행, 승인 `20260922-10-test-separation-design`)가 `| 파일 | 함수 | 영역 | 이유 |` 형식이다(254행 `audit_current_forced.py`, 255행 `sizing_recipe.py`, 262행 `stick_diagram.py` …).
   영역 값은 그대로 두고 '파일' 열이 판정 키가 아니라 설명임(위치는 R-DEF)을 적는 문서 개정이 필요하다 -- design 30 승인(UD-0)이 덮는다. 문안은 `_drafts/p3_doc_amendments.md` §5이고
   design 30 커밋에서 반영된다(v6: UD-0 승인 diff에 들어가므로 이 card의 문서 커밋이 따로 하지 않는다 -- 3차 검토 B4).
6. 미배선: 새 엔진 def 없음. 도우미는 세 test가 부른다.
7. 기존 계약 test: 바뀌는 것이 계약 test 자체 -- V5 승인 경로(결정 필요 항목). B군 11파일은 F1(v5: + `test_b34_grammar_explicit.py`, `test_b26_rail_accessor.py`의 이름 호출 test).
8. (v5) 엔진 모듈 속성 교체: `git grep -n setattr HEAD -- '*.py'` → 0건, `git grep -n "monkeypatch\." HEAD -- skills/analog-gmid-design/assets/tests` → `test_df36_instance_relpath.py`의 `chdir` 4건뿐
   (`7535799`, design 30 부록 A E3; v7: `a796468`에서도 `tools/` 밖 `setattr` 0건). 계약 10의 대상은 B26-1 초안 계약 3("계수 래퍼는 test가 `stick_diagram.rail_declaration`을 바꿔 센다")에서 온 추정이다 -- B26-1 병합본의 실제 test로 확인한다.
   실제 test가 모듈 속성 교체가 아닌 방식(예: 호출자 모듈을 R-DEF로 찾아 교체)이면 계약 10은 필요 없고 지운다(빈 계약 금지).
