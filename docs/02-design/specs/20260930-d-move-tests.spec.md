---
id: 20260930-d-move-tests
phase: 2
evidence_type: red-green
gate_change: no
approval: 20260923-u02-d-list
---

> **[상태 표지 2026-10-29] 실행·병합 완료 기록 -- 현행 규칙·절차 아님.** 판정 기록 `.ai/verification/20260930-d-move-tests.json`(FAIL 0)이 있고 이 card의 커밋은 master에 병합됐다. 옛 계획 Phase 2(죽은 코드·DUP 정리) card이고 Phase 2는 폐기됐다(계획 N6.1 '옛 Phase 처리' 2행 -- 새 엔진은 모듈 지도 N3.10으로 처음부터 개념당 정본 하나). 본문의 spec card·interface card·auditor 판정(V1~V10)·DEC-40 승인·R1 절차는 DEC-86으로 폐기했다(계획 N3.12·N4.2, DEC-40 행) -- 현행 완료 조건은 계획 N6.3이다. 본문의 `A`(`skills/analog-gmid-design/assets`) 아래 옛 엔진·test는 `skills/analog-gmid-design/legacy/`로 옮겨졌고(`60727b06`) 새 test 체계(`gmid_engine/tests/`)에서 돌지 않는다. card LT-1(DEC-99)이 `legacy/`를 지운 뒤에는 tag `legacy-final`에만 남는다. 옮긴 `regression_runner.py`·`interleave_splits.py`는 지금 `legacy/tests/tools/`에 있다. 본문은 기록이며 덧대지 않는다(O-169).

## 의도

design `20-dead-code-dup` v1.2 §2.1·§2.2-2(이관)·§7·§8 P6: 레지스트리 등급 D 중 **참조가 test뿐인 것**(R-1)과 그 동반 레코드를, 엔진
소스에서 test 도구 위치(`A/tests/tools/`, design §2.1이 허용하는 이관 위치 -- code-author 쓰기 경로라 원본을 읽어 바이트 그대로 옮길 수 있다)로 **바이트 그대로** 옮긴다(이름·본문·docstring 불변, import 경로만 바뀐다). 엔진에는 운영 경로가
쓰는 코드만 남는다. 옮기는 코드는 모두 회로 무관(공정·topology를 인자·레지스트리로 받는다)이고 엔진 식을 바꾸지 않는다.
A = `skills/analog-gmid-design/assets`.

대상(2026-09-30 참조 재측정, `git grep -w`):

| 묶음 | 정의(base `sizing_recipe.py`·`stick_diagram.py`) | 참조 | 새 위치 |
|---|---|---|---|
| 회귀 러너 | `RegressionVerdict`(클래스), `_run_optimize_multistage_case`, `_REGRESSION_ENGINES`(모듈 dict), `run_regression_case`, 그리고 그 위의 설명 주석 블록 | `unit/test_selftest_sizing_recipe.py::test_s004_optimize_multistage` 하나(엔진 안 참조는 묶음 내부뿐) | `A/tests/tools/regression_runner.py` |
| 대칭 분할 | `stick_diagram.find_interleaved_symmetric_splits` | `unit/test_selftest_stick_diagram.py` 하나 | `A/tests/tools/interleave_splits.py` |

이관하지 않는 R-1(보류, 사유): `build_toy_lut`·`_invq_newton` -- `workspaces/**` 진단 스크립트가 쓰고 엔진 docstring이 LUT 관례(`W*=L`)의
예로 인용한다(test 전용이 아님). `check_multi_leaf_hub_parity`·`MultiLeafHubParityVerdict` -- 엔진 docstring이 스크리닝 도구로 인용하고
IC5 게이트 목록(design 10 §5.6)에 든다. 나머지 R-1(topology_authoring·배선 승인 필요·삭제 후보)은 Phase 3·4 또는 P7 등급 정정 몫.

## 관찰 가능한 계약

1. **이관**: 위 표의 정의가 base 엔진 파일에서 없어지고 새 위치에 있다. 새 파일은 옮긴 코드가 쓰는 엔진 이름(`optimize_multistage`,
   `_COMPENSATION_REGISTRY` 등)을 `sizing_recipe`에서 import한다. `tools/`는 pytest가 수집하지 않는다(`pytest_gate.ini` norecursedirs).
   파일 이름은 기존 계약 test의 파일 패턴(`probe_*.py`, `test_probe_*.py`, `*.topology.json`)과 겹치지 않는다(2026-09-30 grep 확인).
2. **E-AST**: 옮긴 정의마다 docstring 포함 `ast.dump`가 base(엔진 파일)와 병합본(새 파일)에서 같다 -- 클래스·함수·모듈 dict 대입 모두.
3. **소비자**: `test_selftest_sizing_recipe.py`·`test_selftest_stick_diagram.py`는 옮긴 이름을 새 모듈에서 import한다(엔진 import 목록에서
   그 이름을 뺀다, `A/tests/tools`를 `sys.path`에 넣는 방식은 `contracts/test_probe_dup_scan.py` 선례). 두 파일의 test id와 판정은 base와 같다
   (바뀌는 것은 import 줄뿐).
4. **GONE(엔진)**: 옮긴 이름 5개(`RegressionVerdict`·`_run_optimize_multistage_case`·`_REGRESSION_ENGINES`·`run_regression_case`·
   `find_interleaved_symmetric_splits`)의 정의와 AST 참조가 `A/*.py`·`workspaces/run_harness.py`에서 0이다. `A/tests/**`의 참조는 새
   모듈을 가리킨다.
5. **레지스트리**: `docs/03-analysis/gain-budget-gmid-sizing.function-registry.md` §7 D 목록에서 이 5개 행을 같은 커밋에서 지우거나
   'tests 이관 완료(새 경로)'로 갱신한다(계획 N0.3).
6. **E-LIB·E-INST**: library 로드 가능 회로 전부와 파일럿·`folded_cascode` 결과가 base와 같다.
7. 전체 스위트는 base와 같은 결과(수집 id 동일, 실패 0).

## 신규 시그니처

| 모듈 | 심볼 | 시그니처 |
|---|---|---|
| `regression_runner` | `*` | 신규 모듈 `A/tests/tools/regression_runner.py`(엔진에서 이관, 시그니처는 관찰 가능한 계약의 기존 함수와 같다) |
| `interleave_splits` | `*` | 신규 모듈 `A/tests/tools/interleave_splits.py`(같음) |

## 판정 유형 근거

red-green: test 커밋이 소비자 import를 새 모듈로 바꾸고 GONE 계약 test를 더한다 -- T(엔진 = base)에서는 새 모듈이 없어 소비자 파일과
GONE test가 red(ImportError·원본 잔존)다. code 커밋이 새 모듈에 원본을 옮기고 엔진에서 지운다(병합본 green). 동작 보존 증거는 E-AST·E-LIB·E-INST
(코드가 옮겨질 뿐 동작은 같아야 한다). test-author는 엔진 소스를 읽지 않는다(DEC-38) -- 옮기는 일은 code-author 몫이다.

## oracle 종류와 출처

(c) 동작 보존: 기대값은 base 트리(엔진 파일의 원본 정의 AST, base 실행 결과)다. 새 기대값을 만들지 않는다.

## 거부해야 할 입력

해당 없음(이관). 대신 GONE 판정이 base에서 실제로 실패함(원본이 있음)을 test가 보인다.

## library 회로 적용 여부

적용: E-LIB·E-INST(엔진에서 지우는 것이 운영 경로를 건드리지 않음을 확인). `test_s004`는 `sky130_regression_reference.json` 골든 케이스를
새 위치의 러너로 그대로 돌린다.

## 무동작 판정 입력(무발동 값)

library 회로 전부와 두 소비자 파일 밖의 test 전부 -- 판정이 base와 같다.

## 재현할 수치

없음.

## 결정 필요 항목

없음(U-02 승인 `20260923-u02-d-list` 1항 'tests 이관(test·probe 전용과 동반 레코드)').

## 변경 이력

- 2026-10-29 `cards/revise-1029`: 위 상태 표지만 더함 -- 본문 불변, 표지 전 원문 = `git show 052465ed:docs/02-design/specs/20260930-d-move-tests.spec.md`.
