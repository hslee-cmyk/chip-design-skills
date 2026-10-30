---
template: design
version: 1.2
plan_version: 5.19
---

# gain-budget-gmid-sizing -- 10-test-separation Design Document

> **[폐기 표지 2026-10-29] 폐기된 설계 -- 현행 절차 아님.** 이 문서는 옛 Phase 1 test 분리(인라인 self-test 이관·TS0~TS6·IC 계약 xfail) 설계다. 계획 N6.1 '옛 Phase 처리' 1행이 '폐기 -- 옛 test는 `legacy/tests/`에 동결했고 LT-1에서 삭제(tag `legacy-final`, DEC-99)'이고, N3.11은 TS0~TS6을 폐기로 적는다. 현행 test 체계는 N3.11(새 엔진 `gmid_engine/tests/`; IC1~IC11 강제 test는 담당 패키지 test 폴더에 새 API로 -- N4.1, TS7 = 담당 단위까지 xfail)이다. 이 문서가 기대는 spec card·auditor·DEC-40 승인 절차도 DEC-86으로 폐기했다. 현행 절차는 계획 N6.3(가벼운 절차, DEC-86: 코드 작성 주체 ≠ test·기대값 작성 주체(WP-13), 깨진 test·기준 약화는 숨기지 않고 보고, 변경당 커밋 1, 매 변경 뒤 새 test 체계 `gmid_engine/tests/` 전체 실행)이다. 본문의 `A`(`skills/analog-gmid-design/assets`) 아래 옛 엔진·test 경로는 `skills/analog-gmid-design/legacy/`로 옮겨졌고(`60727b06`), card LT-1(DEC-99)이 `legacy/`를 지운 뒤에는 tag `legacy-final`에만 남는다. 본문은 기록이며 고치지 않는다(DEC-86 '지우지 않고 폐기 표시'; 표지 전 원문 = `git show 052465ed:docs/02-design/features/gain-budget-gmid-sizing.10-test-separation.design.md`).

> **Summary**: Phase 1 설계. 소스 안의 인라인 self-test 블록을 `tests/`의 pytest로 옮기고(DEC-46), print·stdout 기준선 판정을 assert로 바꾸고, IC1~IC11 계약 test를 xfail로 선언한 뒤 IC3·IC5를 활성화한다. 추출 도구 `tools/migrate/extract_selftest.py`(TS1), Test 16 fixture 정정(TS0, U-01), print 판정 제거(TS3), 기준선 퇴역(TS5), xfail 생성과 표식 대조(TS7, `00-common` CC-3), 섹션→test 분리와 셔플(TS2), IC5 docstring 검사, IC3 필드 완전성·이름 충돌 검사, 사례 caa970b 재생.
>
> **Project**: chip-design-skills (analog-gmid-design skill) · **Author**: Claude Code (오케스트레이터 -- 작성 agent)
> **Date**: 2026-09-21 · **Status**: v1.2 -- review2 N1·S3 참고(§6.10·§9 C11) 반영. v1.1 -- 독립 검증 review1(`docs/03-analysis/gain-budget-gmid-sizing-10-test-separation/review1.md`) S1·S2 반영, 사용자 승인 대기(DEC-51)
> **Planning Doc**: [gain-budget-gmid-sizing.plan.md](../../01-plan/features/gain-budget-gmid-sizing.plan.md) v5.19 · N6.1 `1` 행 · N9.1 `10-test-separation` 행 · **공통 정의**: [00-common](gain-budget-gmid-sizing.00-common.design.md) v1.8 · **흐름·게이트**: [05-role-separation](gain-budget-gmid-sizing.05-role-separation.design.md) v3.6

Context Anchor: 계획서에 `## Context Anchor` 절이 없어 옮기지 않는다.

---

## 0. 이 문서를 읽는 법

* 정의는 계획서·`00-common`·`05`가 정본이다. 이 문서는 **Phase 1 변경을 무엇으로 어떻게 판정하는가**만 더한다(N9.4). 흐름(순서 0~8·재시도·worktree 명령)은 `05` §12, spec card 양식은 `05` §11.2, 판정 기록·승인 기록 형식은 `00-common` §8, xfail 옵션의 의미는 `00-common` §9.3을 그대로 인용한다.
* **실측 기준**: 저장소 HEAD `89d257c`. 수치는 모두 부록 A의 명령으로 셌고 원자료는 `docs/03-analysis/gain-budget-gmid-sizing-10-test-separation/`에 있다. 섹션 번호 `S<i>`는 그 커밋 기준이며, 착수 시점의 번호는 추출 도구(§5.2)가 다시 낸다(§6.8).
* **영역 표기**(`00-common` §5): 이 문서의 규칙·판정식은 전부 test·도구의 구조 판정이라 전기 영역이 없다 -- 모두 `영역: 없음(스키마)`다. §5.6 표의 영역 값은 **검사 대상 게이트의** 영역이다.
* 명령의 `$PY`는 `C:\Python314\python.exe`, `<iso>`는 auditor 격리 복제본 루트(`05` §12-7), `<cache>`는 게이트 코드 캐시(`05` §4.4), `A`는 `skills/analog-gmid-design/assets`다.

---

## 1. 범위 (N9.2-1)

| 이 문서 절 | 구현하는 계획서 절·ID |
|---|---|
| §4 순서 | N6.1 `1` 행, N3.11 TS 표, N3.12.3 '한 건의 단위' |
| §5.1·§5.2 섹션 규칙·추출 도구 | N3.11 TS1(추출 스크립트·선행 변경 `<id>-extract-tool`), N3.12.3 '섹션->test 매핑표' |
| §6.1 TS1 | N3.11 TS1, DEC-46 |
| §6.2 TS0 | N3.11 TS0, U-01(확정), DF-17, DEC-40 |
| §6.3 TS3 | N3.11 TS3 |
| §6.4 TS5 | N3.11 TS5 |
| §5.4·§6.5 TS7 | N3.11 TS7, N4.1, `00-common` §9.3·CC-3 |
| §5.6·§6.6 IC5 | N4.1 IC5, DEC-67, `00-common` §5 |
| §5.5·§6.7 IC3 | N4.1 IC3 |
| §5.4·§6.8 TS2 | N3.11 TS2·conftest(`--shuffle-seed`), DEC-36 |
| §6.9 사례 caa970b | N4.3 과거 사례 표(재생 Phase 1), N6.2 `1` |
| §6.10 V3 도구 옵션 | N4.2 V3(도입 1), `00-common` §9.3 |

범위 밖: TS4(Phase 4, `40-defect-fixes`), TS6(Phase 2, `20-dead-code-dup`), 모듈 분할 뒤 test 파일 재배치(`30-module-split`), IC3·IC5 외 IC의 본문(각 담당 Phase design).

---

## 2. 구현 주체 분류 (`00-common` §3.2)

| 항목 | 결과물 | 부류 | 판정 근거(§3.1 순서 번호와 이유) | 고정 수단 | 구현 소유 | 판정 기준 소유 | 산출 spec card 또는 승인 기록 |
|---|---|---|---|---|---|---|---|
| 이 문서 | design 문서 | `AI 직접` | 3 -- 작성 | 독립 검증 → 사용자 승인 | `오케스트레이터` | `독립 검증 agent` | 이 문서의 승인 기록(§11) |
| 섹션 경계·범주 규칙과 추출·계수 | `tools/migrate/extract_selftest.py` | `코드` | 2 -- TS1 산출물과 TS2·TS3 매핑표(V2 test-only 증거)의 입력 | red-green | `gmid-code-author` | `gmid-test-author` | C1 |
| 이관본 | `A/tests/legacy/selftest_*.py`, `A/tests/legacy/test_legacy_selftests.py` | `코드` | 2 -- 판정 입력 | equivalence(stdout 동일) | `gmid-test-author`(도구 실행) | `gmid-verification-auditor`(동등성 측정) | C2 |
| 소스 블록 삭제 | `A/{sizing_recipe,stick_diagram,design_report,topology_library}.py` | `코드` | 2 -- 운영 코드 | equivalence | `gmid-code-author` | `gmid-test-author` | C2 |
| Test 16 fixture 정정 | 이관본 한 줄 + 기준선 두 줄 | `코드` | 2 -- 판정 기준 | test-only + DEC-40 승인 | `gmid-test-author` | `사용자`(U-01 확정, DEC-40 승인) | C3 |
| print 판정 → assert | 이관본 4개, `A/tests/contracts/test_ts3_no_print_verdicts.py` | `코드` | 2 -- 판정 기준 | test-only + DEC-40 승인 | `gmid-test-author` | `사용자`(삭제 목록 승인, U-41) | C4 |
| 기준선 퇴역 | `A/tests/baseline/` 삭제, `A/tests/README.md` | `코드` | 2 -- 판정 기준 | test-only + DEC-40 승인 | `gmid-test-author` | `사용자` | C5 |
| xfail 생성·표식 대조 | `A/tests/conftest.py`의 `--gmid-*`, `A/tests/contracts/test_ic*.py` 11개, 대조 test | `코드` | 2 -- xfail 만료 판정 | 계획서 N4.1 직접 대조(`00-common` §9.3) | `gmid-test-author` | `사용자`(계획서 N4.1 승인) | C6 |
| IC5 docstring 절 | 게이트 함수 21개 docstring | `코드` | 2 -- IC5 판정 입력 | red-green | `gmid-code-author` | `gmid-test-author` | C7 |
| IC5 게이트별 영역 값 | §5.6 표 | `코드` | 2 -- IC5 test 기대값(oracle (d) = 승인된 이 표) | 이 문서 승인 + red-green | `오케스트레이터`(표 작성) | `사용자` | 이 문서의 승인 기록 |
| IC3 필드 완전성·이름 충돌 | `stick_diagram.py` 새 게이트 2개와 배선 | `코드` | 2 -- 거부 판정 | red-green | `gmid-code-author` | `gmid-test-author` | C8 |
| IC3 필수 필드 목록 | §5.5 `INSTANCE_*_FIELDS` 값 | `코드` | 2 -- 판정 입력 | 이 문서 승인 + red-green | `오케스트레이터`(목록 작성) | `사용자` | 이 문서의 승인 기록 |
| 섹션→test 분리, 셔플 | `A/tests/unit/test_selftest_*.py`, conftest `--shuffle-seed`·세션 fixture | `코드` | 2 -- 판정 기준 | test-only + DEC-40 승인 | `gmid-test-author` | `gmid-verification-auditor`(매핑·판정 수 대조) | C9 |
| V3 도구 옵션 전달 | `tools/gates/mutate_changed.py` | `코드` | 2 -- V3 판정 실행 | red-green(redteam 케이스) | `gmid-code-author` | `gmid-test-author` | C11 |
| 사례 caa970b 재생 | `tools/gates/redteam/cases/caa970b-*/`, `redteam/lib/rt.py` 동작 하나 | `코드` | 2 -- 게이트 거부 증명 | 재생 로그 | `gmid-test-author` | `사용자`(재생 로그 확인) | C10 |
| 참고 문서 갱신 | `skills/analog-gmid-design/references/*.md` 두 곳 | `AI 직접` | 3 -- 문서 | 독립 검증 | `오케스트레이터` | `독립 검증 agent` | C5와 같은 Phase |

---

## 3. 설계 입력 실측 (HEAD `89d257c`)

| 항목 | 값 | 출처(부록 A) |
|---|---|---|
| `A/*.py`의 `if __name__ == "__main__":` 블록 | 7개 파일 | A-1 |
| 그중 판정이 있는 블록(§5.1 범주 A·B 섹션 ≥ 1) = **인라인 self-test** | 4개: `sizing_recipe.py` 12571–15269(2,699줄) · `stick_diagram.py` 8992–12936(3,945줄) · `design_report.py` 319–382(64줄) · `topology_library.py` 528–694(167줄) | A-1 |
| 판정이 없는 블록(CLI·생성 스크립트, 범위 밖) | 3개: `audit_current_forced.py`(`sys.argv`), `sky130_lut_sweep.py`(LUT 생성), `topology_to_markdown.py`(`sys.argv`) | A-1 |
| 섹션 수(머리 P 포함) | sizing 77 · stick 174 · design_report 5 · topology_library 16 = **272** | A-1 |
| 범주 P / D / A / B / C | sizing 1/5/68/1/2 · stick 1/10/114/21/28 · design_report 1/0/4/0/0 · topology_library 1/0/10/0/5 | A-1 |
| 범주 C 중 뒤 섹션이 이름을 읽는 것 | sizing 2 · stick 13 · topology_library 2(나머지 C = 뒤 섹션이 안 읽는 데모 **18개**, §6.3 표) | A-1 |
| `assert` / `raise AssertionError` / 거부 try(`try` 안 `raise AssertionError` + `except`) | 596 / 30 / 29 (파일별은 부록 A-1 표) | A-1 |
| print·logging 인자 안 PASS/FAIL 토큰 | sizing 113 · stick 232 · design_report 5 · topology_library 4 = **354**(§7 T, f-string 상수 조각은 한 번) | A-1 |
| 전역 `lut`(sizing S1)을 읽는 섹션 | 27 | A-1 |
| 앞 섹션 이름을 읽는 섹션(의존 후보) | sizing 52 · stick 120 · design_report 3 · topology_library 7 | A-1 |
| 블록 안 `def` | sizing 5(`_tst_grids`, `_l4b_ctx_for`, `_feasible_w`, `_ro_direct`, `_drl_case`) · stick 6 · 나머지 0 | A-1 |
| 블록이 읽는 모듈 이름(명시 import 후보) | 56 · 92 · 4 · 8, 미해결 0 | A-1 |
| `__file__` 사용 | 8 · 8 · 2 · 0, **전부** `<os 별칭>.path.dirname(<os 별칭>.path.abspath(__file__))` 꼴 | A-1 |
| `globals()`·`locals()`·`eval`·`exec`·`__import__` | 0 | A-1 |
| 실행 시간(격리 복제본, 직접 실행) | sizing 11.2–12.8 s · stick 23.3–24.9 s · design_report 0.3 s · topology_library 1.1–2.9 s, 모두 exit 0 | A-2 |
| 결정론 | `PYTHONHASHSEED` 1~5(stick 1·2) 모두 stdout 해시 1개 | A-2 |
| 모듈 한 벌 실행(모듈 import 뒤 블록 본문만 그 전역 사본에서 exec -- 이관본 흉내)과 직접 실행 | 4개 모두 stdout 바이트 동일(stick은 모듈이 서로 import해 두 벌이 생기는 구조지만 출력 차 0) | A-2 |
| 실행 뒤 작업 트리 | 변경 0(`git status --porcelain`) | A-2 |
| stdout 안 절대 경로 | stick 1줄(Test 31 (3), `library/folded_cascode.topology.json`의 절대 경로) -- **실행 위치가 다르면 바이트가 다르다** | A-3 |
| 커밋된 기준선 대 HEAD 출력 | stick: 경로 줄 1개만 다름(위치), Test 16 (b) `FAIL(예상과 다름)` 그대로. **sizing: 45줄 다름(기준선 361줄, HEAD 388줄)** -- 기준선이 마지막 갱신(README '2026-09-10 (6)') 뒤 출력 변화를 따라오지 않았다 | A-3 |
| IC5 대상 게이트 함수(§5.6 규칙) | **21개**(sizing 7 · stick 13 · audit_current_forced 1 · run_harness 0), `검사하지 않는 것:`·`영역:` 줄 0 | A-4 |
| library 9회로 이름 충돌(소자 중복·소자∩수동소자·대소문자만 다름) | 0 | A-4 |
| 추적 `instance.json` 필드 완전성(§5.5) | library를 참조하는 4건 누락 0, 나머지 2건은 임시 topology 참조라 대상 아님 | A-4 |
| `A/tests/` 추적 파일 | 48(`.py` 44, `test_*.py` 0, `baseline/` 3) | A-5 |
| `A/tests/*.py`(probe 등)의 print PASS/FAIL 토큰 | 0 | A-5 |

---

## 4. Phase 1 변경 순서

N6.1 `1` 행은 단계의 집합이고 순서를 정하지 않는다. 아래 순서는 원칙에서 정한 기본안이다(한 번에 변경 하나, `05` §12).

| 순서 | spec card(§9) | 단계 | 판정 유형 | 이 순서인 이유 |
|---|---|---|---|---|
| 1 | C1 `ts1-extract-tool` | TS1 선행 | red-green | N3.11 TS1: 추출 스크립트는 먼저 병합하고 TS1의 base가 그 병합 커밋 |
| 2 | C2 `ts1-legacy-move` | TS1 | equivalence | TS0의 수정 대상(Test 16 fixture)이 test 경로로 와야 test-author가 고친다 -- 이관 전에는 그 fixture가 소스 파일(code-author 경로) 안에 있어 code-author가 판정 기준을 쓰게 된다(N3.12.1 위반) |
| 3 | C3 `ts0-test16-fixture` | TS0 | test-only | TS3가 print를 assert로 바꾸면 고치지 않은 Test 16 (b)가 FAIL로 TS3를 막는다 |
| 4 | C4 `ts3-assert-verdicts` | TS3 | test-only | **TS2보다 먼저**: V4 (4)(5)(N4.2, 도입 1)는 새·바뀐 test 함수에 적용되므로, print로만 판정하는 섹션(범주 B 22개)·판정 없는 섹션(C)을 그대로 test 함수로 만들면 TS2가 V4 FAIL이다. 이관본(모듈 수준 스크립트, test 함수 없음)에서 먼저 assert로 바꾼다 |
| 5 | C5 `ts5-baseline-retire` | TS5 | test-only | N3.11 'TS3 직후' -- TS3가 stdout을 바꾸므로 기준선은 그 뒤 쓸모가 없다 |
| 6 | C6 `ts7-ic-xfail` | TS7(CC-3) | test-only | IC5·IC3 활성화 card의 엄격 집합(`00-common` §9.3)이 이 conftest에 기댄다 |
| 7 | C7 `ic5-gate-docstrings` | IC5 | red-green | IC3이 더하는 게이트도 IC5 규칙을 처음부터 따르게 먼저 |
| 7a | C11 `v3-gmid-options` | 게이트 변경 | red-green | C6 conftest 뒤로 V3 도구(`mutate_changed.py`)의 pytest 실행이 `--gmid-phase` 없이 UsageError로 끝나 변이 전 기준 실행이 실패하고 모든 변이가 '살아남음'이 된다. C6 뒤 소스 def를 바꾸는 첫 red-green이 C8이므로 그 앞(§6.10) |
| 8 | C8 `ic3-completeness` | IC3 | red-green | 엔진 동작 변경(거부 경로) -- 이 시점에는 이관본 판정이 모두 assert라 회귀가 exit code로 드러난다. 이관본 stick Test 26이 빈 sizing으로 `save_instance_json`을 불러 새 계약과 충돌하므로 이 card의 test 커밋이 그 섹션을 고친다(§6.7) |
| 9 | C9 `ts2-pytest-split` | TS2 | test-only | 이관본을 섹션별 test로 나누고 이관본을 지운다(N3.11 'legacy는 TS2 완료 시 삭제') |
| 10 | C10 `caa970b-replay` | N4.3 사례 | test-only(게이트 변경) | 다른 card와 독립. Phase 1 DoD 항목 |

순서 2~5 사이에는 엔진 동작 변경이 없다(C2·C3·C4·C5는 test만 바꾸거나 동작 보존) -- 그래서 그 구간에서 print 판정 섹션의 회귀를 볼 stdout 기준선 비교 test를 따로 두지 않는다(§6.1).

---

## 5. 인터페이스 (N9.2-2)

### 5.1 섹션 경계와 범주 규칙

블록 = 모듈 최상위 `If` 중 조건의 `ast.unparse`(작은따옴표를 큰따옴표로)가 `__name__ == "__main__"`인 것.

* **표지**: 블록 최상위 문장이 `print(<첫 인자>)`이고 첫 인자의 정적 텍스트(문자열 상수, 또는 f-string의 상수 조각을 이은 것)가
  * `"# "` 또는 `"=== "`로 시작하면 **대 표지**(연속한 대 표지 `print`는 하나로 합친다),
  * `"  ["`로 시작하고 정규식 `^  \[\s*(PASS|FAIL|OK|SKIP|불가)`에 맞지 않으면 **소 표지**.
* **섹션** = 표지(대·소)부터 다음 표지 앞까지의 최상위 문장. 첫 표지 앞은 **머리(P)**다. 번호 `S<i>`는 블록 안 순서(0 = 머리).
* **범주**(위에서부터 처음 맞는 것):

| 범주 | 조건 |
|---|---|
| P | 머리 |
| D | 섹션 문장이 모두 인자가 정적 문자열뿐인 `print`(표지만) |
| A | `Assert` 1개 이상 또는 `raise AssertionError(...)` 1개 이상 |
| B | print·logging 인자 안 PASS/FAIL 토큰(§7 판정식 T) 1개 이상 |
| C | 그 밖(판정 없음) |

* **의존**: 섹션 안의 이름 읽기(`Load`)마다 블록 안에서 그 줄 앞의 마지막 저장(대입·`def`·`class`·`import` 별칭·인자·`except ... as`)이 앞 섹션에 있으면 그 섹션에 의존한다. 이 계수는 **후보**다(중첩 함수가 나중에 불리는 경우 등 과대 계수가 있다) -- TS2 test-author가 섹션마다 확정한다.
* **인라인 self-test** = 범주 A 또는 B 섹션이 1개 이상인 블록.

### 5.2 추출 도구 `tools/migrate/extract_selftest.py` (C1, code-author)

```
$PY tools/migrate/extract_selftest.py extract  --source <A/모듈.py> --module <import 이름> --out <A/tests/legacy/selftest_<모듈>.py>
$PY tools/migrate/extract_selftest.py sections --source <.py> --out <json 경로>
$PY tools/migrate/extract_selftest.py scan     --root <디렉터리> [--out <json 경로>]
```

**`extract`** -- 출력 파일 = 머리글 + 블록 원문:

1. 블록이 정확히 하나가 아니면 exit 2.
2. 블록 안 `__file__`이 든 식이 모두 `<X>.path.dirname(<X>.path.abspath(__file__))` 꼴(`<X>`는 이름 하나)이 아니면 exit 4. 블록 안에 `globals`·`locals`·`eval`·`exec`·`__import__` 호출이 있으면 exit 4(이름 해석을 보장할 수 없다).
3. **이름 해석**: 블록 안에서 읽히고(`Load`, 중첩 함수 안 포함) 블록 안에서 한 번도 저장되지 않은 이름 중 내장 이름이 아닌 것 = 필요 이름. 그중 원본 모듈 최상위에서 묶이는 이름(`def`·`class`·대입·`import`·`try`/`if` 안 포함)은 `from <module> import (<정렬된 이름>)` **한 줄**로 가져온다(모듈 속성 그대로 -- 같은 객체). 블록 안에서 저장도 되는 이름 중 원본 모듈 최상위에도 있고 블록에서 첫 저장 전에 읽히는 것도 같이 가져온다. 어디서도 묶이지 않는 이름이 있으면 목록을 출력하고 exit 3.
4. **본문**: `if __name__ == "__main__":` 줄부터 블록 끝 줄까지 원문 텍스트를 줄 단위로 그대로 옮긴다(주석·빈 줄·들여쓰기 포함). 유일한 치환: 2의 식 각각의 원문 조각(`ast.get_source_segment`)을 `_ASSETS_DIR`로 바꾼다.
5. **머리글**(고정 텍스트): 생성 도구·원본 경로·원본 blob id를 적은 주석, `import os`, `import sys`, `_ASSETS_DIR = os.path.abspath(sys.argv[1]) if len(sys.argv) > 1 else os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".."))`, `sys.path.insert(0, _ASSETS_DIR)`, 3의 import 줄. 원본 블록이 `_ASSETS_DIR`을 이미 쓰면 exit 4.
6. 출력은 UTF-8(BOM 없음), 줄 끝 LF. 같은 입력이면 바이트가 같다(결정론). exit 0.

**`sections`** -- §5.1 규칙으로 섹션 목록 JSON을 쓴다: 섹션마다 `{index, kind(prelude|major|sub), category(P|D|A|B|C), start, end, title, asserts, raise_assertion, reject_try, verdict_tokens, deps:[{name, section}], provides_to:[index], defs:[name]}`. 원본 소스와 이관본 모두에 쓴다(이관본의 블록도 같은 `if __name__` 블록이다).

**`scan`** -- `<디렉터리>/*.py`(하위 디렉터리 제외)마다 블록과 인라인 self-test 여부를 JSON으로 쓰고, 인라인 self-test가 하나라도 있으면 exit 1, 없으면 0. Phase 1 DoD '소스에 인라인 self-test 0'의 측정 도구다.

exit code: 0 성공 / 1 `scan`이 인라인 self-test 발견 / 2 입력 오류(파일 없음·블록 0개 또는 2개 이상·파싱 실패) / 3 미해결 이름 / 4 지원하지 않는 구성.

* 레지스트리: 도구는 엔진 밖(`tools/`)이라 함수 레지스트리 대상이 아니다.
* **실행 주체**: TS1에서 test-author가 자기 test worktree에서 Bash로 실행해 출력을 커밋한다(N3.11 TS1).

### 5.3 test 배치

| 경로 | 내용 | 쓰는 card | 사라지는 card |
|---|---|---|---|
| `A/tests/tooling/test_extract_selftest.py` | 추출 도구의 test(도구 test는 test-author, N3.11 `tools/` 줄) | C1 | -- |
| `A/tests/legacy/selftest_<모듈>.py` ×4 | TS1 이관본(pytest가 수집하지 않는 이름) | C2 | C9 |
| `A/tests/legacy/test_legacy_selftests.py` | 이관본 4개를 하위 프로세스로 실행해 exit 0 단언 | C2 | C9 |
| `A/tests/contracts/test_ts3_no_print_verdicts.py` | TS3 AST 검사(§7 T) | C4 | -- |
| `A/tests/README.md` | pytest 실행법(§6.4) | C5 | -- |
| `A/tests/conftest.py` | `--gmid-phase`·`--gmid-strict`·`--gmid-dod`, `gmid_ic` 표식, xfail 생성(C6) / `--shuffle-seed`, 세션 fixture, 보고 머리(C9) | C6, C9 | -- |
| `A/tests/contracts/test_ic<N>.py` ×11 | IC 계약 test(뼈대 → 담당 Phase에서 본문) | C6 | -- |
| `A/tests/contracts/test_ic_markers_match_plan.py` | 표식-계획서 대조 test(`00-common` §9.3) | C6 | -- |
| `A/tests/unit/test_selftest_<모듈>.py` ×4 | TS2 섹션별 test | C9 | `30-module-split`에서 `unit/test_mod*.py`로 재배치 |

`tooling/`은 N3.11 트리에 없는 줄이다 -- 계획서 개정 요청 P4(§12).

### 5.4 conftest (`A/tests/conftest.py`, test-author, 바꿀 때마다 V5 승인 -- `05` §10 V5)

**C6에서 만드는 것**(`00-common` §9.3이 의미의 정본):

* `pytest_addoption`: `--gmid-phase=<Phase>`(기본값 없음), `--gmid-strict=<IC:case,...>`, `--gmid-dod`(플래그). 모두 `=` 한 토큰 형식(`00-common` §8.1).
* `pytest_configure`: 표식 `gmid_ic(ic, *, phase, case)` 등록. `--gmid-phase`가 없거나 계획서 `phase_order`(아래 대조 test와 같은 `read_plan_tables`로 읽는다) 밖이면 `pytest.UsageError`(수집 오류).
* `pytest_collection_modifyitems`(C9에서 셔플을 같은 함수 끝에 더한다): 각 item의 `gmid_ic` 표식(함수 데코레이터와 `pytest.param(..., marks=...)` 모두 -- `item.iter_markers("gmid_ic")`)에서 (IC, phase, case)를 읽어, xfail 조건·reason·엄격 대상(`--gmid-dod`, `--gmid-strict`)·모르는 케이스 키 거부는 `00-common` §9.3 그대로 구현한다(`item.add_marker(pytest.mark.xfail(reason=..., strict=False))`, 거부는 `pytest.UsageError`). **빈 엄격 집합**: `00-common` §8.1이 정한 `--gmid-strict=`(값 없음)는 키가 없는 것이다 -- 빈 문자열을 `split(",")`해 키 `""`를 만들지 않는다(그러면 모르는 키로 거부된다).
* 케이스 키 = `"<IC>:<case>"`, 케이스가 하나인 IC는 `case=""`이라 키가 `"IC3:"`처럼 콜론으로 끝난다.
* `read_plan_tables`는 게이트 코드(`tools/gates/merge_gate.py`)를 import해 쓴다(표 읽기 규칙의 정본이 하나 -- WP-14). conftest는 `<저장소 루트>/tools/gates`를 `sys.path` **끝**에 더한다 -- V1은 `<cache>`를 `PYTHONPATH` 맨 앞에 두므로 base 판 게이트 코드가 먼저 잡힌다(`05` §12-7).

**C9에서 더하는 것**:

* `--shuffle-seed=<int>`(기본 없음). `pytest_collection_modifyitems` 끝에서(xfail 표시 뒤) 값이 있으면 `random.Random(seed).shuffle(items)`. 플러그인을 더하지 않는다(DEC-36).
* `pytest_report_header`: `shuffle-seed: <값 또는 none>`, `real_lut: <npz 상대 경로> sha256=<파일 바이트 해시>`(N3.11 '지문 기록'). 헤더는 판정 문자열이 아니다(PASS/FAIL 토큰 없음).
* 세션 fixture: `assets_dir`(= `A`, conftest 위치에서 계산), `library_dir`(= `assets_dir/library`), `toy_lut`(= `build_toy_lut()`, 이관본의 전역 `lut`), `real_lut`(`A/sky130_nfet_pfet_lut_sample.npz` 고정 경로). N3.11의 `topology 팩토리`·`grids`는 소비자가 둘 이상 파일에 생길 때 만든다(지금 소비자 1파일 -- WP-01).

### 5.5 IC3 새 코드 (C8, code-author, `stick_diagram.py` -- `save_instance_json`·`load_topology`가 있는 곳)

```python
INSTANCE_TOP_FIELDS: tuple[str, ...] = ("schema_version", "topology_ref", "sizing", "netlist",
                                        "floorplan", "box_shape", "audit_row_split", "coverage")
INSTANCE_SIZING_FIELDS: tuple[str, ...] = ("W", "L", "ID", "gm", "gm_id")

@dataclass(frozen=True)
class CompletenessVerdict:
    ok: bool
    missing_top: tuple[str, ...]            # INSTANCE_TOP_FIELDS 중 없는 키
    missing_sizing: tuple[str, ...]         # topology 소자 중 sizing에 없는 이름
    missing_fields: Mapping[str, tuple[str, ...]]   # 소자 -> INSTANCE_SIZING_FIELDS 중 없는 키
    missing_netlist: tuple[str, ...]        # topology 소자 중 netlist 원소 이름에 한 번도 없는 것
    coverage_missing: tuple[str, ...]       # instance["coverage"]["missing"]

def check_instance_completeness(instance: Mapping, device_names: Iterable[str]) -> CompletenessVerdict: ...

@dataclass(frozen=True)
class NameCollisionVerdict:
    ok: bool
    duplicate_devices: tuple[str, ...]
    device_passive_overlap: tuple[str, ...]
    case_only_collisions: tuple[tuple[str, ...], ...]   # 소자·수동소자 이름 중 casefold가 같은 서로 다른 이름 묶음

def check_topology_name_uniqueness(device_names: Sequence[str], passive_names: Sequence[str]) -> NameCollisionVerdict: ...
```

* **필드 목록의 근거**: `INSTANCE_TOP_FIELDS`는 `save_instance_json`이 지금 쓰는 키 전부(선택 키 `scope_note` 제외), `INSTANCE_SIZING_FIELDS`는 그 docstring이 적은 입력 계약(`{"W","L","ID","gm","gm_id"}`, `SizingResult` 필드명)이다. 목록은 이 두 상수 한 곳에만 있고(IC3 '저장 필드 목록 단일 정의') `save_instance_json`은 `INSTANCE_TOP_FIELDS` 순서로 `data`를 만든다.
* **배선**(★만들면 반드시 배선): (1) `save_instance_json`은 파일을 열기 **전에** `check_instance_completeness(data, <load_topology(topology_json_path)의 소자 이름>)`을 부르고, `ok`가 거짓이면 모든 누락을 담은 `ValueError`를 내고 파일을 쓰지 않는다(운영 경로: `workspaces/run_harness.py`가 부른다). (2) `load_topology`는 연결 파일까지 합친 netlist 소자 이름과 `passive_elements` 이름으로 `check_topology_name_uniqueness`를 부르고, `ok`가 거짓이면 `ValueError`.
* 예외 클래스: Phase 1에는 N3.14 클래스가 없어 `ValueError`다. `SchemaRejectedError` 등으로의 재분류는 `40-defect-fixes`(CC-4·CC-5)가 한다(§8).
* docstring은 §5.6 형식(`검사하지 않는 것:`, `영역: 없음(스키마)`).
* 레지스트리 `docs/03-analysis/gain-budget-gmid-sizing.function-registry.md`에 두 함수를 같은 code 커밋에서 등록한다(목적지 모듈은 레지스트리 규칙).

### 5.6 IC5 docstring 형식과 영역 표 (C7)

**대상** = 소스 분류 파일(`A/*.py`, `workspaces/run_harness.py` -- N3.12.4 EL3 경로 분류)에서 이름이 `^(check_|verify_|validate_|audit_|reject_|require_)` 또는 `^load_.*_checked$`인 함수·메서드 전부(모든 깊이). test가 실행 때 AST로 센다(목록을 박지 않는다).

**형식**(`inspect.cleandoc`한 docstring의 줄 단위):

* 앞뒤 공백을 뗀 줄이 `검사하지 않는 것:`으로 시작하는 줄이 1개 이상이고, 그 줄의 콜론 뒤나 다음 비지 않은 줄에 공백 아닌 문자가 있다.
* 앞뒤 공백을 뗀 줄이 `영역:`으로 시작하는 줄이 **정확히 1개**이고 정규식 `^영역:\s*(없음\((스키마|배치)\)|(dc|ac_struct|ss|ls)(\s*,\s*(dc|ac_struct|ss|ls))*)\s*(\.|$)`에 맞는다. `없음(배치)`는 `00-common` §5 개정 요청 C1이다(레이아웃 게이트는 전기 영역도 스키마도 아니다).

**영역 표**(현존 21개, test가 이 값과 같음을 단언 -- oracle (d) = 이 문서 승인). '파일' 열은 이 표를 쓸 때(Phase 3 전)의 정의 위치를 적은 **설명**이고 판정 키가 아니다 -- test는 함수 이름으로 대조하고, 정의 위치는 엔진 소스(`skills/analog-gmid-design/assets/*.py`, `workspaces/run_harness.py`)에서 그 이름을 최상위로 정의하는 파일이 정확히 하나인지로 찾는다(Phase 3 T0, design 30 §7.1 R-DEF). 판정 기준은 '영역' 값이다:

| 파일(설명, Phase 3 전 위치) | 함수 | 영역 | 이유(N0.4 '영역') |
|---|---|---|---|
| `audit_current_forced.py` | `audit_topology` | 없음(스키마) | `matching_pairs` 선언과 `sizing_roles.theta` 선언의 대조 |
| `sizing_recipe.py` | `check_quasi_static` | ss | gm·Cgg(선형화 값) |
| 〃 | `audit_l_sharing_consistency` | dc | L(N0.4: L·VDS는 DC) |
| 〃 | `audit_vsb_consistency` | dc | 노드전압·VSB |
| 〃 | `validate_no_legacy_vs_key` | 없음(스키마) | 옛 키 |
| 〃 | `validate_metric_units` | 없음(스키마) | 선언 단위 |
| 〃 | `validate_theta_declaration_order` | 없음(스키마) | 선언 순서 |
| 〃 | `require_declared_spec_source` | 없음(스키마) | 출처 선언 |
| `stick_diagram.py` | `check_mirror_symmetry` | 없음(배치) | finger 순서 대칭 |
| 〃 | `check_symmetry_dispositions` | 없음(배치) | 레이아웃 매칭 후보의 판정 기록 |
| 〃 | `check_multi_leaf_hub_parity` | 없음(배치) | 오일러 차수 |
| 〃 | `audit_vertical_stack_id_vs_kcl` | dc | KCL |
| 〃 | `audit_theta_root_direction` | dc, ac_struct | 전류 정의 root(DC)와 connectivity로 찾은 캐스코드 관계(AC구조) |
| 〃 | `require_device_roles_reviewed` | 없음(스키마) | review 상태 선언 |
| 〃 | `audit_vertical_stack_id_euler_feasibility` | 없음(배치) | 오일러 실현 |
| 〃 | `check_finger_width_compatibility` | 없음(배치) | finger 폭 |
| 〃 | `check_euler_condition` | 없음(배치) | 오일러 조건 |
| 〃 | `check_box_shape` | 없음(배치) | 셀 모양 |
| 〃 | `check_walk_sequence` | 없음(배치) | diffusion 순서 |
| 〃 | `check_stick_diagram_coverage` | 없음(배치) | 행 배치 포함 |
| 〃 | `audit_row_split` | 없음(배치) | 행 분할 |

C8이 더하는 두 게이트는 `없음(스키마)`다(표 밖 게이트는 형식만 검사한다).

---

## 6. 단계별 설계

### 6.1 TS1 -- 이관 (C1, C2)

**C1 `ts1-extract-tool`** (red-green): §5.2 도구. test(`tests/tooling/test_extract_selftest.py`, oracle (a) 구성으로 정답이 정해진 합성 입력): 임시 디렉터리에 합성 모듈(함수·클래스·모듈 상수·`import json`·`os` 별칭 경로식·주석·빈 줄이 있는 블록)을 쓰고 (1) `extract` 출력의 본문 줄이 원본 블록 줄과 같고(치환 한 가지만 다름) import 줄이 손으로 적은 기대 이름 목록과 같다, (2) 원본 실행과 이관본 실행의 stdout 바이트가 같다, (3) 거부: 블록 없음·둘 → 2, 미해결 이름 → 3, 다른 꼴의 `__file__`·`eval` → 4, (4) `sections`: 섹션 수·범주·의존이 손으로 적은 기대와 같다(대·소 표지, `[PASS]`는 표지 아님, 연속 대 표지 병합, P/D/A/B/C 각 1개 이상), (5) `scan`: 판정 있는 블록이 있는 디렉터리 → 1, CLI 블록만 → 0. red = base에 도구가 없어 하위 프로세스 exit가 기대와 달라 AssertionError.

**C2 `ts1-legacy-move`** (equivalence, N3.12.3):

* test 커밋: test-author가 C1 도구로 4개 이관본을 만들고(`--module`은 `sizing_recipe`·`stick_diagram`·`design_report`·`topology_library`), `test_legacy_selftests.py`(이관본마다 `[sys.executable, <이관본>, <A 절대 경로>]`를 `cwd=A`, `PYTHONHASHSEED=1`로 실행해 `returncode == 0` 단언, parametrize 4)를 더한다.
* code 커밋: code-author가 4개 소스에서 블록과 **바로 앞의 연속 주석 배너**(블록 앞 빈 줄 전까지의 `#` 줄, 예: `stick_diagram.py`의 `# 7) Self-test — python stick_diagram.py로 바로 확인 가능`)를 지운다. 그 밖의 줄은 바꾸지 않는다.
* **동등성 증거**(auditor, 격리 복제본 `<iso>` **한 곳**에서 -- stdout에 절대 경로가 나오므로 같은 경로에서 돌려야 한다, §3):
  1. `git -C <iso> checkout --detach <base>` 뒤 모듈 m ∈ (sizing_recipe, stick_diagram, design_report, topology_library) 순, 시드 s = 1..5 순으로 `PYTHONHASHSEED=s $PY <iso>/A/<m>.py`(cwd `<iso>/A`)의 stdout을 모은다.
  2. `git -C <iso> checkout --detach <병합본>` 뒤 같은 순서로 `PYTHONHASHSEED=s $PY <iso>/A/tests/legacy/selftest_<m>.py <iso>/A`(cwd `<iso>/A`).
  3. 20쌍 각각 바이트 동일(§7 E1). 판정 기록 `equivalence.commands` = 2의 20개 명령, `outputs_hash` = 2의 stdout을 순서대로 이은 바이트의 sha256(`00-common` §8.1), `checks.V2.basis`에 1의 해시가 같음을 적는다.
  4. 추출 재현: T(test 커밋)에서 C1 도구 `extract`를 base 소스에 다시 돌린 출력이 커밋된 이관본과 바이트 동일(손 편집 없음 -- '본문 그대로'의 기계 증거). 단 머리글 둘째 줄 `# 원본 경로:` 주석은 도구가 받은 `--source` 절대 경로를 그대로 적어 실행 위치마다 다르므로, 그 한 줄은 빼고 비교하고 그 줄의 끝 파일 이름(`<m>.py`)이 같음만 본다(2026-09-22 사용자 승인 `20260922-c2-extract-repro-path-line`, 도구 쪽 수정은 백로그 B5). 실행 동등성(1~3)은 그대로 바이트 동일.
  5. 소스 동작 보존: 4개 소스 각각 base와 병합본의 모듈 AST(`ast.dump`, 블록 제외)가 같다.
* V5: base→병합본 diff에서 소스의 `__main__` 단위는 통째로 사라지고 test 함수 단위가 아니다 -- `weakening_diff.py` 판정식상 발견이 없다(구현 판독). 발견이 나오면 §8 F5.

### 6.2 TS0 -- Test 16 (C3)

**원인 대조**: U-01 확정(승인 기록 `20260921-u01-test16-intent`) -- Test 16 (b)는 신설 판 e329283부터 HEAD까지 여덟 판 모두 `UNDISPOSED: ('diff_pair','pmos','tail') M4/M5`로 FAIL이고, 원인은 (b) `dispositions`가 그 키를 빠뜨린 test fixture 누락이다(대상 코드는 설계대로). HEAD `89d257c` 격리 실행에서도 같은 줄(`FAIL(예상과 다름 ...)`)이 나온다(부록 A-3).

**조치**(test-only, test-author):

* `A/tests/legacy/selftest_stick_diagram.py` Test 16 (b)의 `dispositions` dict에 `("diff_pair", "pmos", "tail"): ("real_match", <사유 문자열>)` 한 항목을 더한다. 대상 코드와 (a)는 그대로(U-01 '덮는 것').
* **기준선 재생성**(N3.11 TS0 완료 판정): `A/tests/baseline/stick_diagram.selftest.baseline.log`에서 Test 16 (b)가 내는 줄(`(b) ...` 머리 다음 줄부터 `전체 결과` 줄까지)만 수정 후 실행의 같은 줄로 바꾼다. 나머지 줄(경로 줄 포함)은 건드리지 않는다. `sizing_recipe` 기준선의 45줄 드리프트(§3)는 U-01 범위 밖이라 TS0에서 고치지 않고 TS5가 기준선을 지울 때 승인 diff에 함께 보인다(§6.4).
* **증거**(V2 test-only): base와 변경 뒤 각각 격리 복제본에서 이관본 stick을 실행 -- base의 Test 16 (b) 블록에 `FAIL(예상과 다름` 1줄, 변경 뒤 0줄이고 (b) 판정 줄이 전부 `[PASS]`, `test_legacy_selftests.py` 4케이스가 양쪽 PASS. 기준선 diff가 위 (b) 블록 줄로만 이뤄졌음을 `checks.V2.basis`에 적는다.
* 승인: 기준선 `.log` 변경은 V5 '비-`.py`' 규칙 대상 -- DEC-40 승인 기록(`target_kind: diff`, 경로 = `weakening_diff.py`가 낸 `diff_paths`). 승인을 head 트리에 넣는 절차는 R1(§12).
* 완료 시 DF-17 해소.

### 6.3 TS3 -- print 판정 → assert (C4)

이관본 4개에서(테스트 함수가 없는 모듈 수준 스크립트라 V4 대상이 아니다) print·logging 호출마다:

| 경우 | 조치 |
|---|---|
| 인자에 PASS/FAIL 토큰이 조건식(`'PASS' if c else 'FAIL'` 등)으로 들어 있고, 그 섹션 문장이 기대 쪽을 적어 둔 경우(예: "(a) ... FAIL 기대", "대조군 -- ... FAIL해야 한다", "(b) ... PASS 기대") | 기대 쪽 조건을 `assert`로 바꾸고(메시지 = 원래 출력 문자열) print를 지운다. 기대 쪽 = 섹션 문장이 적은 쪽(oracle (d)의 한 형태 -- self-test 작성자가 적은 의도). base 출력이 기대와 반대면 멈춘다(§8 F4, TS0과 같은 판정 필요) -- HEAD 실측에서 그런 줄은 Test 16 (b) 하나뿐이고 C3이 고친다(부록 A-3) |
| 기대 쪽이 적혀 있지 않은 데이터 표시(예: sizing S1의 gm/ID 후보별 `quasi-static=OK/FAIL`) | print를 지운다. assert를 만들지 않는다(기대값을 현재 출력에서 가져오게 된다 -- N3.12.3 금지) |
| 조건 없는 PASS/FAIL 문구(`print("PASS: ...")`) | print를 지운다(판정은 앞의 assert가 이미 한다. assert가 없는 주장은 원래 판정이 아니었다) |
| 범주 C이고 뒤 섹션이 읽는 이름이 없는 섹션(데모 18개, 아래 표) | 섹션을 지운다(N3.11 TS3 '판정 없는 데모는 삭제'). 뒤 섹션이 읽는 이름을 만드는 C 섹션(17개)은 그 이름을 만드는 문장만 남긴다 |

**삭제 후보 18개**(HEAD 기준. 착수 시 C1 `sections`로 다시 뽑는다 -- U-41):

| 파일 | 섹션 |
|---|---|
| stick_diagram | S1 Test 1a · S2 Test 1b · S3 Test 2 · S4 Test 3 · S5 Test 4 · S6 Test 5 · S9 Test 5.5 사례2 · S10 Test 5.5 사례3 · S12 Test 5.6-1 · S15 Test 5.6-4 · S18 Test 8 · S19 Test 9 · S20 Test 10 · S59 Test 15 · S82 Test 24 보조 |
| topology_library | S1 Miller 2단 · S3 nmcnr 스모크 · S9 NGCC 3단 |

* 새 contract test `tests/contracts/test_ts3_no_print_verdicts.py`: §7 판정식 T = 0 단언(대상 = `A/tests/**/*.py`에서 `A/tests/probes/**`·`A/tests/tools/**` 제외). 판정기가 실제로 거부함을 같은 파일에서 합성 소스 문자열(토큰 1개)로 보인다(WP-02).
* 증거(V2 test-only): base에서 이관본 4개 exit 0(판정 줄에 기대 반대가 없음 -- C3 뒤), 변경 뒤 exit 0이고 새 contract test PASS(base에서는 T = 354라 FAIL -- 기록). 변환 수 대조: 이관본별 (새 assert 수) = (조건식 토큰으로 바꾼 print 수)임을 `checks.V2.basis`에 적는다.
* 승인: 문자열 상수 삭제·섹션 삭제는 V5 발견 -- DEC-40 승인(삭제 목록은 U-41), 절차 R1.
* stdout이 바뀌므로 이 card부터 커밋된 기준선은 쓸모가 없다 → C5.

### 6.4 TS5 -- 기준선 퇴역 (C5)

* test-author: `A/tests/baseline/`(README.md, 두 `.log`) 삭제, `A/tests/README.md` 작성 -- 실행법 `$PY -P -m pytest -c tools/gates/pytest_gate.ini --rootdir=. --confcutdir=. skills/analog-gmid-design/assets/tests --gmid-phase=<Phase>`(C6 전에는 `--gmid-phase` 없이), 판정 규칙(assert만, print 판정 금지, xfail은 conftest가 계획서 N4.1로 만든다), 디렉터리 표(N3.11). README 내용에 PASS/FAIL 토큰 줄이 있어도 §7 T의 대상(`.py`)이 아니다.
* **사용자**(세션 밖, `Role: user` 커밋 + `staged_diff` 승인 기록 -- N3.12.2 `.gitignore` 행, `05` §8.2-5): `.gitignore`의 기준선 예외 3줄(`# 예외: self-test 회귀 기준선은 ...` 두 줄과 `!skills/analog-gmid-design/assets/tests/baseline/*.log`) 삭제.
* 오케스트레이터: `skills/analog-gmid-design/references/sky130-worked-example.md`(`python topology_library.py` 스모크 안내), `references/stick-diagram-euler-layout.md`(`python stick_diagram.py` self-test 안내)의 실행 안내를 `tests/README.md` 인용으로 바꾼다. 과거 기록 서술(`consistency-map.md` 등의 "self-test exit 0 재확인")은 이력이라 두지 않고 고치지도 않는다(N0.1 -- 이력은 history).
* 승인: 비-`.py` test 파일 삭제·추가는 V5 발견 -- DEC-40 승인. 이 승인의 diff에 sizing 기준선의 45줄 드리프트(§3)가 삭제분으로 들어 있음을 승인 요청에 명시한다.
* 증거: §10 D5 명령 출력 0줄.

### 6.5 TS7 -- xfail 선언 (C6, `00-common` CC-3)

**선언 목록**(N4.1에서 생성 -- 표식 Phase = `read_plan_tables(...).ic_parts[IC]`의 phase 집합, 함수 이름 = `ic_test[IC]`, 부록 A-6에서 게이트 파서로 확인):

| IC | 파일 | test 함수 | 표식 `(phase, case)` | xfail reason(Phase 1) |
|---|---|---|---|---|
| IC1 | `contracts/test_ic1.py` | `test_vgs_consistency_all_devices` | (6b, "") | `IC1 -- 담당 Phase 6b -- 만료: 6b DoD` |
| IC2 | `contracts/test_ic2.py` | `test_order_shuffle_invariance` | (6b, "") | 같은 형식 |
| IC3 | `contracts/test_ic3.py` | `test_coverage_and_field_completeness` | (1, "") | 엄격 대상 전까지 xfail, C8부터 PASS |
| IC4 | `contracts/test_ic4.py` | `test_role_label_removal_invariance` | (6c, "") | |
| IC5 | `contracts/test_ic5.py` | `test_gate_docstring_declares_blind_spots` | (1, "") | 엄격 대상 전까지 xfail, C7부터 PASS |
| IC6 | `contracts/test_ic6.py` | `test_dof_catches_incident19_fixture` | (6c, "") | |
| IC7 | `contracts/test_ic7.py` | `test_all_library_topologies_run` | (6a, "run"), (6c, "stop") | 케이스별 |
| IC8 | `contracts/test_ic8.py` | `test_unevidenced_derivation_stops_before_search` | (6c, "") | |
| IC9 | `contracts/test_ic9.py` | `test_no_raw_duplicated_writes` | (6b, "") | |
| IC10 | `contracts/test_ic10.py` | `test_cache_key_covers_mutable_state` | (6b, "") | |
| IC11 | `contracts/test_ic11.py` | `test_rail_origin_shift_invariance` | (4, "rail2"), (6a, "rail3"), (6a, "reject") | 케이스별(`00-common` §9.3) |

* 케이스가 둘 이상인 IC는 `pytest.mark.parametrize`의 `pytest.param(..., marks=pytest.mark.gmid_ic(...))`로 케이스마다 표식을 단다.
* **뼈대 본문**: 담당 Phase가 1이 아닌 9개와 C7·C8 전의 IC3·IC5는 본문이 `pytest.fail()` 한 줄이다(인자 없음). 이유: V4 (4)는 `pytest.fail` 호출을 판정으로 센다(`test_lint.py` `_other_judgements`) -- `assert False, "<문구>"`로 쓰면 활성화 card가 문자열 상수를 지워 V5 '리터럴 변경'이 매번 승인을 요구한다. 활성화 card의 base에서 이 뼈대는 `Failed`(허용 red 타입, `00-common` §8.1)로 red가 된다.
* **대조 test** `contracts/test_ic_markers_match_plan.py`(oracle (d) 계획서 N4.1): 계획서를 `read_plan_tables`로 읽고, `A/tests/contracts/*.py`를 AST로 읽어 함수 `ic_test[IC]`에 달린 `gmid_ic` 표식(데코레이터와 `pytest.param` marks)의 phase 집합이 `{p.phase for p in ic_parts[IC]}`와 같음을 IC 11개 모두 단언. 판정기가 실제로 거부함을 합성 소스(계획서에 없는 Phase를 단 함수 하나, 계획서 Phase에 표식이 없는 함수 하나)로 같은 파일에서 보인다(CC-3 'red는 표식이 계획서와 다른 합성 test 파일에서 FAIL').
* 이 card는 `activated_ic_case`가 없다. V1 명령의 `--gmid-phase`: **C6의 병합본 실행부터** `--gmid-phase=1`을 붙이고(병합본 conftest가 그 옵션을 요구한다), C6의 base 쪽 실행(C6 전 conftest)에는 붙이지 않는다. merge gate는 C6 때 old conftest에 옵션이 없어 대조하지 않는다(`00-common` §9.3 'CC-3 병합 전 판정식').
* 승인: `tests/conftest.py` 신설은 V5 무조건 승인 대상(`05` §10) -- DEC-40 승인, 절차 R1.

### 6.6 IC5 (C7)

* test(`contracts/test_ic5.py::test_gate_docstring_declares_blind_spots`, 뼈대 교체): 대상 함수를 실행 때 AST로 모아 (1) 개수 ≥ 1(공허한 통과 방지), (2) 전부 §5.6 형식, (3) §5.6 표의 21개는 영역 값이 표와 같음(값 집합 비교, 쉼표 순서 무관). 판정기가 거부함을 합성 docstring(절 없음, `영역:` 두 줄, 허용 밖 값 `영역: dc_ac`)으로 보인다. oracle (d): 계획서 N4.1 IC5, `00-common` §5(+C1 개정), 이 문서 §5.6 표.
* code: 21개 docstring에 두 줄(절)을 더한다. 코드 본문은 바꾸지 않는다 -- 동작 보존 증거는 바뀐 함수마다 docstring을 뺀 `ast.dump`가 base와 같음(auditor 기록).
* 허용 영역 문자열은 test-author가 `00-common` §4에서 옮긴다(`DOMAINS`는 6a CC-6이 만들고 그때 두 곳의 일치 test를 더한다 -- `00-common` §5).
* `activated_ic_case: IC5:`. red = base에서 21개가 형식 위반 → AssertionError.

### 6.7 IC3 (C8)

* test(`contracts/test_ic3.py::test_coverage_and_field_completeness`, 뼈대 교체, oracle (a) 구성으로 정답이 정해진 입력):
  1. `check_stick_diagram_coverage`: 사이징 이름 {A,B,C} 대 행 {r:[A,B]} → `missing == {C}`, 전부 덮으면 `ok`.
  2. `check_instance_completeness`: 손으로 만든 instance dict에서 최상위 키 하나 뺌 / 소자 하나 sizing에서 뺌 / 필드 하나 뺌 / netlist에서 뺌 / `coverage.missing` 비지 않음 -- 각각 해당 필드에만 그 이름이 나온다. 전부 있으면 `ok`.
  3. 배선(저장): library topology 하나로 `run_topology_pipeline`을 돌린 결과를 `save_instance_json`에 넘기되 sizing에서 소자 하나를 빼면 `ValueError`이고 파일이 생기지 않는다. 빼지 않으면 파일이 생기고 다시 읽어 2가 `ok`.
  4. 배선(로드, WP-07 library 로드·변형): library topology를 읽어 임시 파일로 (i) 소자 이름 하나를 다른 소자 이름으로 바꿈 (ii) 소자 이름을 수동소자 이름으로 바꿈 (iii) 소자 이름의 대소문자만 바꿔 다른 소자와 겹치게 함 → `load_topology`가 `ValueError`. **오거부 0**: 변형하지 않은 library 9회로 전부 로드 통과(HEAD 충돌 0, §3).
* code: §5.5.
* 동작 보존 범위(N6.3 '동작 보존 Phase는 실행 가능한 회로 전부에서 equivalence'): 새 게이트는 통과하면 산출물을 바꾸지 않는다. auditor는 (1) library 9회로 `load_topology` 통과, (2) 사이징 스펙이 선언되고 지금 실행되는 회로(I-C11 해소 전: 파일럿·`folded_cascode`)의 하네스 실행을 base·병합본에서 각각 돌려 `instance.json`의 키 정렬 직렬화 sha256이 같음을 기록한다(`00-common` §11 도구는 Phase 4 CC-8이라 이 수동 절차를 쓴다, `topology_ref`는 같은 격리 경로라 같다).
* **이관본 Test 26 정정**(C8 test 커밋, test-author): 이관본 stick의 Test 26 `save_instance_json(...)` 섹션은 sizing으로 빈 dict `{}`를 넘겨(HEAD `stick_diagram.py:10744-10750`) 배선 (1) 뒤 `ValueError`로 이관본이 exit 1이 된다. 새 계약에 맞게 (가) 빈 sizing이면 `ValueError`임을 단언하고(try 안 `raise AssertionError` + `except ValueError` 거부 형태 -- C9에서 `pytest.raises`), (나) 정상 저장은 `_fc_result`의 소자마다 `INSTANCE_SIZING_FIELDS` 다섯 키를 가진 합성 sizing(값은 판정 대상이 아닌 구성 입력, oracle (a) -- 이 섹션의 판정은 'pipeline_result를 그대로 옮기는가')으로 보인다. 이 변경은 리터럴·판정 변경이라 **V5 발견 -- DEC-40 승인 기록 필요**(절차 R1). base에서 이 섹션은 (가)의 AssertionError로 이관본 exit 1 → `test_legacy_selftests` red.
* **V3 대상과 죽일 입력**(`mutate_changed.py` 인벤토리 = 정적 호출 그래프로 도달하는 test -- 이관본은 하위 프로세스라 들지 않는다, 그래서 `contracts/test_ic3.py`가 전부 죽여야 한다): 대상 def = `load_topology`(HEAD 변이 55), `save_instance_json`(8), 새 `check_instance_completeness`·`check_topology_name_uniqueness`. library 9회로는 모두 `"linked_topology_files": []`라 연결 파일 루프 본문 변이가 1~4의 입력으로 죽지 않는다 -- test-author는 (5) **연결 파일 픽스처**(WP-07 로드·변형: library 회로 하나의 netlist를 두 파일로 나눠 한쪽이 `linked_topology_files`로 다른 쪽을 가리키게 한 임시 topology)로 `load_topology`가 합친 소자 수·이름이 원본과 같음과 반환 `meta`의 필드(원본 로드와 같은 값)를 단언하고, 나뉜 두 파일에 같은 소자 이름이 있으면 `ValueError`임을 단언한다. 그래도 남는 등가 변이는 `target_kind: decision` 승인 기록으로만 면제한다(N4.2 V3. 원소 형식은 design 05 §10 V3 ⑤ -- 2026-10-01부터 `<변이 id>@<묶기 해시>`).
* `activated_ic_case: IC3:`. red = 새 심볼 import(interface card 신규 시그니처 표에 둘) + 배선 단언의 AssertionError.

### 6.8 TS2 -- 섹션 → test (C9)

**매핑 규칙**(N3.12.3 '섹션->test 매핑표'의 정본):

1. 매핑의 섹션 번호는 **C2 병합 커밋의 이관본**에 C1 `sections`를 돌린 JSON이다(오케스트레이터가 C4·C9 spec card에 첨부). C4가 지운 섹션도 번호를 유지한다(빈 번호).
2. 섹션 → 대상:

| 범주(C4 뒤) | 대상 |
|---|---|
| P | test 파일 머리(import, 모듈 상수). `sys.stdout.reconfigure`는 버린다(판정 무관) |
| D | test 없음. 표지 문구는 다음 섹션 test의 docstring 첫 줄 |
| A(C4 뒤의 B 포함) | `A/tests/unit/test_selftest_<모듈>.py::test_s<NNN>_<slug>` 하나. `NNN` = 3자리 섹션 번호, `slug` = 표지에서 처음 나오는 `식별자(`의 식별자(없으면 `section`) |
| C 중 뒤 섹션이 이름을 읽는 것 | test 없음. 그 이름을 만드는 fixture(아래) |
| C4에서 지운 C | test 없음(승인 U-41) |

3. **fixture**: 섹션 사이 의존(§5.1)마다 -- (가) 블록 안 `import` 별칭 → test 파일 머리 import (나) 블록 안 `def` → test 파일 모듈 수준 함수(자유 변수가 블록 데이터를 가리키면 인자로 올린다) (다) 데이터 → 그 이름을 만드는 문장을 담은 **함수 범위 fixture**(셔플 아래에서 공유 상태가 없게. 예외는 불변 자원인 세션 fixture `toy_lut`·`real_lut`·`library_dir`·`assets_dir`, §5.4). 섹션 사슬은 fixture가 fixture를 받는 명시 사슬이 된다.
4. 전역 `lut` → `toy_lut`, `__file__` 경로(`_ASSETS_DIR`) → `assets_dir`·`library_dir`, 거부 케이스(try 안 `raise AssertionError` + `except X`) → `pytest.raises(X)`(메시지 단언은 `match=` 또는 `excinfo` 단언으로 옮긴다), `_drl_case`(sizing, 호출 2곳) → `pytest.mark.parametrize` 2케이스(케이스마다 새 ctx -- 원본은 공유 ctx의 `sized["Mm"]`를 바꾼다).
5. 판정은 바꾸지 않는다: 섹션마다 (test의 `assert` + `pytest.raises` 수) ≥ (섹션의 `assert` + 거부 try 수)(§7 M2).
6. **assert가 모두 `if`·`try` 아래에 있는 섹션**(거부 try로 4에서 `pytest.raises`가 되는 것 제외 -- 그대로 옮기면 V4 (3) FAIL, `test_lint.py`): 그 조건을 먼저 `assert`한다 -- `if C:` 아래면 `assert C`, 정상 경로가 `try` 본문이면 `except` 분기를 지워 예외가 test 실패가 되게 한다 -- 그 뒤 원래 assert를 조건 밖에서 그대로 실행하고, `else`·`except` 분기의 print·skip 문구는 지운다. 판정이 하나 늘 뿐이라 M2(≥)에 맞는다. 조건이 참이어야 하는 근거(oracle)는 C9 spec card에 섹션마다 적는다(예: design_report S3의 `os.path.exists(<파일럿 instance.json>)` -- 추적되는 파일). 조건이 참이라는 근거를 댈 수 없으면 test-author가 멈추고 보고한다(§8 F4와 같은 처리). HEAD 기준 해당 섹션 5개: sizing S14·S51·S54, stick S157, design_report S3(review1 S2-5 실측. 착수 시 C1 `sections` 출력의 assert 조상으로 다시 뽑는다).

**HEAD 기준 규모**(부록 A-1): test 함수 후보 = A+B = sizing 69 · stick 135 · design_report 4 · topology_library 10 = **218**. 데이터 의존을 주는 섹션(fixture 후보 상한) sizing 30 · stick 97 · design_report 2 · topology_library 5. 블록 안 헬퍼 sizing 5 · stick 6. `pytest.raises` 후보 29. 섹션별 표는 `docs/03-analysis/gain-budget-gmid-sizing-10-test-separation/selftest_sections.md`.

* 이관본 4개와 `test_legacy_selftests.py`를 같은 변경에서 지운다.
* conftest: §5.4 C9 부분.
* **증거**(V2 test-only, `N3.12.3`): base에서 `test_legacy_selftests.py` 4케이스 PASS(= 모든 섹션 통과 -- 이관본은 첫 실패에서 멈춘다), 변경 뒤 매핑표의 모든 test가 기본 순서와 `--shuffle-seed` 1~5에서 PASS(§10 D3), M1·M2가 성립. `--durations=0` 표를 판정 기록 부속 산출물로 첨부한다.
* `slow` 표식: 기본 실행 예산이 선언돼 있지 않아(WP-03 -- 숫자를 지어내지 않는다) Phase 1은 붙이지 않는다. 실측 합계는 §3의 블록 실행 시간 합 약 40 s이고 `--durations` 표로 판정 기록에 남는다.
* 셔플이 실제로 순서를 바꾸는지: §10 D3b.
* 승인: conftest 변경, `test_legacy_selftests` 삭제는 V5 발견 -- DEC-40 승인, 절차 R1.
* 매핑의 test id는 `30-module-split`이 `unit/test_mod*.py`로 옮길 때 그 design이 새 매핑을 낸다.

### 6.9 사례 caa970b 재생 (C10)

사례(N4.3, `agent7_self_concealment.md` #11): caa970b의 L4 self-test가 `unaffected_metrics_skipped == ["other_current"]`로 결함 동작(전역 metric 재검증 건너뛰기)을 기대값으로 박제했다(d32811b가 고침). 새 흐름에서 이 기대값은 **red-green 변경의 red가 되지 못한다** -- 결함이 있는 base에서 통과하므로 V2 'red 부재'로 걸린다.

* 재생 데이터(test-author, `tools/gates/redteam/cases/caa970b-stale-expected-value/`, 기존 `expect.json`의 `phase: "1"` 유지·`skip_reason` 제거, `setup.sh`·`run.sh` 추가, `lib/rt.py`에 동작 하나):
  * base 트리 = `caa970b`의 `A/sizing_recipe.py`와 그것이 import하는 같은 커밋의 `A/*.py`(blob 읽기).
  * attack: `05` §13.3 변환 규칙으로 caa970b의 L4 섹션(표지 `[L4 revalidate_finger_override()`)을 test 함수로 만들고, 그 섹션이 읽는 앞 섹션 이름(`lut` 등)은 C1 `sections`의 의존으로 찾아 머리에 넣는다. 격리 명령(`05` §12-7, red 수집 플러그인 `-p merge_gate`, `GMID_RED_CAPTURE`)으로 base에서 실행 → test PASS·red 수집 0건 = 기대 'V2 red 부재'.
  * control(오거부 0): 같은 base에 d32811b의 단언(`== []`)으로 바꾼 test → red 1건(`builtins.AssertionError`).
* 판정 유형: test-only(code 커밋 없음 -- redteam 데이터와 실행기만). `gate_change: yes`(쓰기 경로 조건 '게이트 변경'), 승인 기록 필요. 설치 사본을 바꾸지 않으므로 `05` §13.4 재설치는 없다.

### 6.10 V3 도구의 conftest 옵션 전달 (C11, 게이트 변경)

* 문제: C6 conftest는 `--gmid-phase`가 없으면 `pytest.UsageError`다(`00-common` §9.3, §5.4). `tools/gates/mutate_changed.py`의 test 실행 명령에는 `--gmid-*`가 없어, C6 뒤 V3의 변이 전 기준 실행이 exit 4로 끝나고 모든 변이가 '살아남음'으로 기록된다. `--gmid-phase`만 넘기면 활성화 케이스(`test_ic3`)가 엄격 대상이 아니라 non-strict xfail이 되어, 변이가 test를 깨도 exit 0이라 변이가 살아남는다.
* 계약(code-author): `mutate_changed.py`가 `--gmid-phase=<값>`·`--gmid-strict=<값>` 인자를 받는다(auditor는 V1 명령과 같은 값을 준다). 시험 대상 복사본의 `A/tests/conftest.py`가 `addoption("--gmid-phase", …)`을 가질 때(merge gate의 'CC-3 병합 전 판정식'과 같은 판정) 기준 실행과 변이 실행의 pytest 명령에 V1의 `--gmid-phase=`를 그대로 넘기고, `--gmid-strict=`에는 V1 엄격 집합 중 **인벤토리 test에 그 Phase의 `gmid_ic` 표식(IC·case)이 있는 키만** 넘긴다. 남는 키가 없으면 `--gmid-strict=`(빈 값 -- `00-common` §8.1, 키 없음)다. 두 옵션 모두 `=` 한 토큰 형식. conftest가 옵션을 가지지 않으면 넘기지 않는다(C6 전 동작 불변). 인벤토리만 실행하는 V3에 V1 엄격 집합을 통째로 넘기면 인벤토리 밖 키가 conftest의 모르는 케이스 키 거부(`00-common` §9.3)에 걸려 기준 실행이 수집 오류로 끝나기 때문이다. conftest의 거부 규칙은 그대로다(막는 규칙 불변).
* **막는 규칙을 넓히지 않는다**: 이미 승인된 conftest 계약(`00-common` §9.3)에 도구를 맞추는 수정이고, V3의 판정식(N4.2 V3·`05` §10)은 그대로다.
* test(test-author, `tools/gates/redteam/**`, oracle (a) 구성으로 정답이 정해진 합성 저장소): `--gmid-phase`를 요구하는 conftest와 활성화 케이스 표식이 달린 test, 그 test가 죽이는 변이 하나를 가진 합성 소스로 (1) 두 옵션을 주면 변이가 죽고 V3 PASS, (2) conftest가 옵션을 모르는 저장소(C6 전 모양)에서는 옵션 없이 실행되어 기존 판정과 같음(오거부 0), (3) 인벤토리 밖 키가 섞인 엄격 집합(예: `IC3:,IC5:`를 주고 인벤토리에는 IC3 표식 test만)에서 V3 기준 실행이 정상이고 변이가 죽음(오거부 0). red = base 도구에서 (1)이 '살아남음'으로 V3 FAIL.
* 합성 conftest는 커밋하지 않고 기존 redteam 선례(`rt.py`가 실행 중 임시 디렉터리에 만든다)대로 만든다 -- `conftest.py`는 판정 환경 이름이라 test-author가 커밋할 수 없다.
* 설치 사본을 바꾸지 않으므로(`mutate_changed.py`는 게이트 코드 캐시에서 실행된다) `05` §13.4 재설치는 없다.

---

## 7. 판정식 모음 (N9.2-3)

모두 `영역: 없음(스키마)`.

| ID | 판정 | 식 | 입력 |
|---|---|---|---|
| S | 섹션 경계·범주 | §5.1 | 블록 AST |
| T | print 판정 토큰 수 | Σ(호출 c) Σ(c의 위치·키워드 인자 안 문자열 `ast.Constant` 노드마다 한 번 -- f-string은 그 안의 `Constant` 조각만 세고 `JoinedStr`를 따로 세지 않는다) `len(re.findall(r"(?<![A-Za-z])(PASS\|FAIL)(?![A-Za-z])", s))`, c = `print(...)` 또는 `<logging\|logger\|log\|LOGGER\|LOG>.<debug\|info\|warning\|warn\|error\|critical\|exception\|log>(...)`(V4 (5)와 같은 호출 집합) | `A/tests/**/*.py` − `A/tests/probes/**` − `A/tests/tools/**` |
| E1 | TS1 stdout 동등 | ∀ m, s∈{1..5}: `stdout(base, <m>.py, s) == stdout(병합본, selftest_<m>.py, s)`(바이트), 같은 절대 경로에서 | §6.1 |
| E2 | 추출 재현 | `extract(base 소스) == 커밋된 이관본`(바이트) | §6.1 |
| E3 | 소스 동작 보존 | `ast.dump(모듈 − 블록)` base = 병합본(C2), 바뀐 함수의 docstring 제외 `ast.dump` base = 병합본(C7) | |
| X | xfail 여부 | `phase_idx(표식) > phase_idx(현재)` ∨ (`=` ∧ 키 ∉ 엄격 대상) | `00-common` §9.3 |
| K | 표식 대조 | ∀ IC: `{표식 phase} == {p.phase for p in ic_parts[IC]}` | 계획서 N4.1 |
| D | IC5 형식 | §5.6 두 줄 규칙 ∧ (표 안 함수면 영역 값 집합 = 표) | docstring |
| R | IC3 완전성 | `missing_* == ()` 전부 ∧ `coverage_missing == ()` | instance, topology 소자 |
| N | IC3 이름 충돌 | 소자 중복 = ∅ ∧ 소자∩수동소자 = ∅ ∧ casefold 충돌 묶음 = ∅ | topology |
| M1 | 매핑 완전 | 매핑표의 A·B 섹션 수 = 매핑된 test id 수, 모두 수집됨 | C1 `sections`, `--collect-only` |
| M2 | 판정 수 보존 | 섹션마다 `asserts_test + raises_test ≥ asserts_sec + reject_try_sec` | C1 `sections`, `weakening_diff.features` |
| Q | 셔플 | ∀ k∈{1..5}: 순서(k) ≠ 순서(기본) ∧ 순서(k) 두 번 같음 | `--collect-only -q` |
| G | 기준선 참조 | §10 D5 출력 줄 수 = 0 | |

수치 임계값은 없다(WP-03).

---

## 8. 실패 경로 (N9.2-4)

Phase 1은 N3.14 실패 클래스가 생기기 전이다(Phase 4). 이 Phase의 코드 실패는 다음으로 끝난다.

| ID | 경우 | 결과 | 처리 |
|---|---|---|---|
| F1 | 추출 도구 입력 오류·미해결 이름·지원 밖 구성 | exit 2·3·4, 출력 파일 없음 | test-author가 멈추고 오케스트레이터에 보고(규칙을 손으로 우회하지 않는다) |
| F2 | IC3 게이트 거부 | `ValueError`(모든 누락·충돌 나열), `instance.json` 미작성 | Phase 4 `40-defect-fixes`가 N3.14 분류(CC-4·CC-5, DF-37: 지금 하네스 `run()`은 예외를 삼키고 0으로 끝난다)로 옮긴다 |
| F3 | TS1 stdout 불일치(E1) | auditor V2 FAIL | 차이 줄을 판정 기록 부속 산출물로 남기고 `05` §12 재시도. 원인이 이관 방식(모듈 한 벌 대 두 벌 등)이면 오케스트레이터가 사용자에게 보고(HEAD 실측은 차이 0, §3) |
| F4 | TS3에서 base 출력이 섹션의 기대와 반대 | test-author가 dispute 없이 멈추고 보고(test가 틀렸는지 대상이 틀렸는지는 U-01과 같은 사용자 판정) | 새 U 항목, 해소 전 C4 보류 |
| F5 | V5 발견이 예상 밖(C2 등) | auditor V5 FAIL | R1 절차로 승인 후 재시도 |
| F6 | 셔플에서만 FAIL | auditor V1/V2 FAIL | 숨은 순서 의존 -- test-author가 fixture를 고쳐 재시도. 엔진 상태 공유가 원인이면 DF로 등록(IC2·NFR-4 소관) |
| F7 | 대조 test FAIL(표식 ≠ 계획서) | V1 FAIL | 표식을 계획서에 맞춘다. 계획서 N4.1이 틀렸다고 보면 계획 개정 + `plan_tables` 승인(EL3·EL4) |
| F8 | code-author가 test가 틀렸다고 봄 | dispute(`05` §12-5) | 사용자 결정 후 1부터 |

도구 exit code: 추출 도구 §5.2. pytest는 표준(0 통과 / 1 실패 / 2 중단 / 4 사용 오류 / 5 수집 0).

---

## 9. 역할별 산출물 -- spec card 목록 (N9.2-5)

한 건 = red 하나로 판정되는 계약 하나, test 전용 변경은 TS 단계 하나(N3.12.3). id의 날짜는 발행일이다.

| card | id 꼴 | Phase | 판정 유형 | gate_change | oracle(N3.12.3 선택 기준) | test-author 산출물 | code-author 산출물 | auditor 산출물 | 활성화 IC 케이스 | 승인 기록 |
|---|---|---|---|---|---|---|---|---|---|---|
| C1 | `YYYYMMDD-ts1-extract-tool` | 1 | red-green | no | (a) 합성 입력 | `tests/tooling/test_extract_selftest.py` | `tools/migrate/extract_selftest.py` | 판정 기록(V1~V6, V7 N/A 도입 2) | -- | -- |
| C2 | `YYYYMMDD-ts1-legacy-move` | 1 | equivalence | no | (c) 이관 전 출력(동작 보존) | 이관본 4 + `tests/legacy/test_legacy_selftests.py` | 소스 4개 블록·배너 삭제 | 판정 기록 + E1·E2·E3 출력 | -- | -- (F5면 R1) |
| C3 | `YYYYMMDD-ts0-test16-fixture` | 1 | test-only | no | (d) U-01 승인 | 이관본 stick 1항목, 기준선 (b) 줄 | -- | 판정 기록(V2 basis: base·변경 뒤 (b) 줄) | -- | DEC-40 diff(기준선·이관본), R1 |
| C4 | `YYYYMMDD-ts3-assert-verdicts` | 1 | test-only | no | (d) 섹션이 적은 기대(§6.3) | 이관본 4개, `contracts/test_ts3_no_print_verdicts.py` | -- | 판정 기록(T=354→0, 변환 수) | -- | DEC-40 diff, 삭제 목록 U-41, R1 |
| C5 | `YYYYMMDD-ts5-baseline-retire` | 1 | test-only | no | -- (삭제·문서) | `tests/baseline/` 삭제, `tests/README.md` | -- | 판정 기록(D5 0줄) | -- | DEC-40 diff, R1. 사용자 `.gitignore` 커밋의 `staged_diff` |
| C6 | `YYYYMMDD-ts7-ic-xfail` | 1 | test-only | no | (d) 계획서 N4.1(승인 판 커밋 해시) | `tests/conftest.py`(`--gmid-*`), `contracts/test_ic1..11.py` 뼈대, `contracts/test_ic_markers_match_plan.py` | -- | 판정 기록 | -- | DEC-40 diff(conftest), R1 |
| C7 | `YYYYMMDD-ic5-gate-docstrings` | 1 | red-green | no | (d) N4.1 IC5·`00-common` §5·이 문서 §5.6 | `contracts/test_ic5.py` 본문 | 21개 docstring | 판정 기록 + E3 | `IC5:` | -- |
| C11 | `YYYYMMDD-v3-gmid-options` | 1 | red-green | yes | (a) 구성 입력(redteam 합성 저장소, conftest는 실행 중 생성) | `tools/gates/redteam/**` 케이스 3종(§6.10: 옵션 전달, C6 전 모양, 인벤토리 밖 키 섞인 엄격 집합) | `tools/gates/mutate_changed.py`(`--gmid-phase=` 전달, `--gmid-strict=`는 인벤토리 표식 키만) | 판정 기록 | -- | 게이트 변경 승인 기록 |
| C8 | `YYYYMMDD-ic3-completeness` | 1 | red-green | no | (a) 구성 입력 + library 무변형 로드·연결 파일 픽스처 | `contracts/test_ic3.py` 본문, 이관본 stick Test 26 정정(§6.7) | §5.5 코드·배선, 레지스트리 | 판정 기록 + 하네스 instance 해시 대조(§6.7) | `IC3:` | DEC-40 diff(이관본 Test 26), R1 |
| C9 | `YYYYMMDD-ts2-pytest-split` | 1 | test-only | no | (c) 이관본 판정(동작 보존) | `unit/test_selftest_*.py` 4, conftest(셔플·fixture·머리), 이관본·wrapper 삭제 | -- | 판정 기록(M1·M2·Q, `--durations=0` 표) | -- | DEC-40 diff(conftest·wrapper 삭제), R1 |
| C10 | `YYYYMMDD-caa970b-replay` | 1 | test-only | yes | (a) 구성 입력(사례 blob) | `redteam/cases/caa970b-*/`, `redteam/lib/rt.py` 동작 | -- | 판정 기록 + `run_all.py --cases 1` 로그 | -- | 게이트 변경 승인 기록 |

**쓰기 경로 대조**(N3.12.2, 부트스트랩 뒤라 `부트스트랩` 조건 행은 없는 것으로 본다):

| card | 경로 | 쓰는 주체 | 맞는 행(경로 glob / 제외 / 조건) | 판정 환경·판정 트리 행 | 결과 |
|---|---|---|---|---|---|
| C1 | `tools/migrate/extract_selftest.py` | code-author | `tools/migrate/**` / -- / 없음 | 해당 없음 | 쓸 수 있음 |
| C1 | `A/tests/tooling/test_extract_selftest.py` | test-author | `A/tests/**` / `A/tests/tools/**`(`tooling`은 `tools` 조각이 아니다) / 없음 | 판정 트리 안이지만 다른 행에 맞음 | 쓸 수 있음 |
| C2 | `A/tests/legacy/*.py` | test-author(도구 실행) | `A/tests/**` | 같음 | 쓸 수 있음 |
| C2 | `A/{sizing_recipe,stick_diagram,design_report,topology_library}.py` | code-author | `A/*.py` / -- / 없음 | 같음 | 쓸 수 있음 |
| C3·C4·C5·C9 | `A/tests/legacy/**`, `A/tests/baseline/**`, `A/tests/README.md`, `A/tests/contracts/**`, `A/tests/unit/**` | test-author | `A/tests/**` | 같음 | 쓸 수 있음 |
| C6·C9 | `A/tests/conftest.py` | test-author | `A/tests/**` | 사용자 `**/conftest.py` 행의 **제외 glob**이 이 경로라 판정 환경 행에 맞지 않음 | 쓸 수 있음(V5 승인 필요) |
| C7·C8 | `A/stick_diagram.py`, `A/sizing_recipe.py`, `A/audit_current_forced.py` | code-author | `A/*.py` | 같음 | 쓸 수 있음 |
| C8 | `docs/03-analysis/gain-budget-gmid-sizing.function-registry.md` | code-author | 그 파일 행 / 없음 | -- | 쓸 수 있음 |
| C10 | `tools/gates/redteam/**` | test-author | `tools/gates/redteam/**` / -- / 게이트 변경 | -- | spec card `gate_change: yes` + 승인 기록일 때 쓸 수 있음 |
| C5 | `.gitignore` | 사용자 | `.gitignore` / 없음 | -- | 사용자만(세션 밖, `Role: user` + `staged_diff`) |
| C5 | `skills/analog-gmid-design/references/*.md` | 오케스트레이터 | `skills/analog-gmid-design/references/**` / 없음 | -- | 쓸 수 있음 |
| 모든 card | `.ai/verification/<id>.json`, `<id>/**` | auditor | 그 행 / 자기 변경 id | -- | 쓸 수 있음 |
| 모든 card | `docs/02-design/specs/<id>.spec.md`·`.interface.md`, `.ai/approvals/<id>.md` | 오케스트레이터 | `docs/02-design/**`, `.ai/approvals/**` | -- | 쓸 수 있음 |
| C11 | `tools/gates/mutate_changed.py` | code-author | `tools/gates/*.py` / -- / 게이트 변경 | -- | spec card `gate_change: yes` + 승인 기록일 때 쓸 수 있음 |
| C11 | `tools/gates/redteam/**` | test-author | `tools/gates/redteam/**` / -- / 게이트 변경 | -- | 같음 |
| R1 | `docs/03-analysis/gain-budget-gmid-sizing-10-test-separation/v5-carry/<id>/<blob id>.blob`, `.../v5-carry/<id>/paths.tsv` | 오케스트레이터 | `docs/03-analysis/**` | 판정 환경 이름(`conftest.py` 등, N3.12.2)이 아니다 -- 원래 경로 이름으로 두면 `conftest.py`가 사용자 `**/conftest.py` 행에 걸려 아무도 못 쓴다 | 쓸 수 있음 |

쓸 수 없는 경로는 없다. 사용자 경로 하나(`.gitignore`)는 사용자 몫이다(§13 U-43).

---

## 10. DoD 측정 명령 (N9.2-6, N6.2 `1`)

auditor가 Phase 1 마지막 card 병합본의 격리 복제본 `<iso>`에서 실행한다. `PT` = `PYTHONPATH=<cache> PYTHONPYCACHEPREFIX=<빈 임시 디렉터리> $PY -P -m pytest -c <cache>/pytest_gate.ini --rootdir=<iso> --confcutdir=<iso> <iso>/skills/analog-gmid-design/assets/tests --gmid-phase=1`.

| ID | N6.2 `1` 조건 | 명령 | 통과 기준 |
|---|---|---|---|
| D0 | TS0 판정 기록 | `git -C <iso> cat-file -e HEAD:.ai/verification/<C3 id>.json` | 있음(gate `master`에 있다 = EL4 통과) |
| D1 | TS1 seed 1~5 stdout 전후 동일 | C2 판정 기록 `equivalence`와 `checks.V2.basis`(§6.1 절차) | E1 20쌍 동일이 기록돼 있음 |
| D2 | 소스에 인라인 self-test 0 | `$PY <iso>/tools/migrate/extract_selftest.py scan --root <iso>/skills/analog-gmid-design/assets` | exit 0 |
| D3 | TS2 기본·셔플 순서 PASS | `PT --gmid-dod` 그리고 k=1..5마다 `PT --gmid-dod --shuffle-seed=k` | 여섯 번 모두 실패 0 |
| D3b | 셔플이 순서를 바꿈(Q) | `PT --collect-only -q`와 k마다 `PT --collect-only -q --shuffle-seed=k` 두 번 | k마다 기본과 다르고 두 번 같음 |
| D4 | TS3 판정 문자열 0 | `PT <iso>/…/tests/contracts/test_ts3_no_print_verdicts.py` | PASS(판정식 T = 0) |
| D5 | TS5 기준선 참조 0 | `git -C <iso> grep -n -I -e "tests/baseline" -e "selftest.baseline" -- skills workspaces tools .gitignore ":(exclude)tools/gates/redteam"` | 출력 0줄(HEAD 실측 4줄: `.gitignore` 1, 기준선 README 3). `tests/README.md`에 이 두 문자열을 쓰지 않는다. redteam 제외 이유: 사례 e5fbf92 재생이 과거 커밋 blob을 경로로 읽는다(`05` §13.3) |
| D6 | IC3·IC5 PASS, 나머지 IC xfail 선언(담당 Phase 명시) | `PT --gmid-dod -rA <iso>/…/tests/contracts` | IC3·IC5 PASS, 대조 test PASS, 나머지 12개 케이스 XFAIL이고 reason이 `<IC> -- 담당 Phase <p> -- 만료: <p> DoD` |
| D7 | 사례 caa970b 적발 | `$PY <iso>/tools/gates/redteam/run_all.py --cases 1 --mode direct` | caa970b 케이스 PASS(attack red 0건, control red 1건) |

D3의 `--gmid-dod`는 Phase 1 표식 케이스(IC3·IC5)를 엄격 대상으로 만든다(`00-common` §9.3).

---

## 11. 착수 조건 확인 (N9.2-7)

* 공통(N6.1): 이 문서의 사용자 승인(DEC-51) -- 승인 시 `.ai/approvals/<승인일>-10-test-separation-design.md`(`target_kind: diff`, `diff_path` = 이 문서와 이 승인이 덮는 개정 파일, `00-common` §8.2). 이전 Phase(0.5) 완료: 부트스트랩 ⑤ 완료 기록(커밋 `e9fde7f`), MG0 완료(`1bcddbb`·`fe45ac3`, 승인 기록 `20260921-mg0-target-spec-split`·`20260921-u39-paper-target-spec`), 부트스트랩 승인 기록 `20260921-bootstrap-*`.
* Phase 1 추가 조건: **U-01 확정**(승인 기록 `20260921-u01-test16-intent`).
* J: 없음.
* card별 착수 조건: C4는 U-41(§13), C5의 `.gitignore`는 U-43, R1이 필요한 card(C3·C4·C5·C6·C8·C9)는 R1 승인(§12, U-42).

---

## 12. 계획서·`00-common`·`05` 개정 요청

이 문서의 승인이 함께 덮는다(`05`가 `00-common` v1.8을 덮은 방식). 판정 표 파싱 값(N4.1 `담당 Phase`·`강제 test`, N4.2 `도입`, N6.1 `Phase` 열, N3.12.2)은 **바꾸지 않는다** -- `plan_tables` 승인이 필요 없다.

| ID | 대상 | 개정 | 근거 |
|---|---|---|---|
| P1 | 계획 N3.11 TS1 | "두 `if __name__` 블록" → "판정이 있는 인라인 self-test 블록 전부(`10-test-separation` §5.1 규칙, 현재 4개)" | N6.2 `1` '소스에 인라인 self-test 0'과 DEC-46. `design_report.py`·`topology_library.py`에도 assert가 있는 self-test가 있다(§3) |
| P2 | 계획 N3.11 TS0 행, N6.1 `1` 행 '판정 유형' | TS0 red-green → test-only. N6.1 `1`: "C1·IC3·IC5 red-green, TS1 equivalence, TS0·TS2·TS3·TS5·TS7 test-only" | U-01 확정으로 대상 코드 불변 -- code 커밋이 없어 EL4 red-green 모양(`05` §9.2-4, code 커밋 1개 이상)이 될 수 없다 |
| P3 | 계획 N3.11 | 순서 주: "TS3는 이관본에서 TS2보다 먼저, TS5는 TS3 직후" | V4 (4)(5) 도입 1(§4) |
| P4 | 계획 N3.11 트리 | `tooling/  code-author 도구(tests/tools/, tools/migrate/)의 test(test-author)` 줄 추가 | 도구 test의 자리가 트리에 없다 |
| P5 | 계획 N3.12.3 test 전용 변경 목록 | "(TS2·TS3·TS5, TS6의 …)" → "(TS0·TS2·TS3·TS5·TS7, TS6의 …, redteam 데이터만 바꾸는 게이트 변경)" | P2, C6, C10 |
| C1 | `00-common` §5 게이트 행 | 영역 값에 `없음(배치)` 추가: "영역 판정이 없는 스키마·경로 게이트는 `없음(스키마)`, 레이아웃(배치) 게이트는 `없음(배치)`" | 현존 게이트 21개 중 10개가 레이아웃 판정이다(§5.6) |
| C2 | `00-common` §14 CC-3 행 '판정 유형' | "test-only가 아니라 TS7 선언의 일부" → "test-only(TS7 card)" | code 커밋이 없어 EL4 모양이 test-only다 |
| R1 | `05` §12 '재시도' 행 뒤 | **V5 승인 운반 절차**(아래) | V5 승인 기록은 병합 판정 때 head 트리에서 찾는데(`merge_gate.py` §9.2-9, `weakening_diff.py`도 head 트리) 진행 중에는 문서 push가 거부되고(`05` §6.2) 오케스트레이터는 역할 worktree에 쓰지 못한다(`05` §5.1) -- 지금 흐름에는 test 내용이 정해진 뒤의 승인을 head 트리에 넣는 길이 없다. Phase 1 card 여섯(C3·C4·C5·C6·C8·C9)이 기댄다 |
| R2 | `05` §18 | "⑤ 뒤 게이트 변경은 spec card로 한다(red-green, oracle (a))" → "… (red-green, oracle (a). 판정 기준 데이터만 바꾸는 게이트 변경 -- `tools/gates/redteam/**`만 바꾸고 code 커밋이 없는 것 -- 은 test-only)" | C10은 code 커밋이 없어 EL4 모양이 test-only다. EL4 `gate_change_ok`는 판정 유형을 보지 않아 실행은 되지만 05 §18 문언과 어긋난다(review1 S2-6). P5(계획 N3.12.3)와 같은 내용 |

**R1 절차(기본안)**: diff 해시는 blob id로 만들어 같은 내용이면 같다(`00-common` §8.2) -- 이를 써서 승인을 1차 시도에서 2차 시도로 옮긴다.

1. 1차 시도: 순서 1~3(test-only면 audit까지). auditor가 `weakening_diff.py` 출력(`findings`, `diff_paths`, `diff_hash`)을 `base_check.json`에 남기고 V5 FAIL로 멈춘다.
2. 오케스트레이터: 정리 **전에** 발견 경로마다 T의 blob을 bash에서 `git -C <W>/<id>-test cat-file blob <T>:<path> > docs/03-analysis/gain-budget-gmid-sizing-10-test-separation/v5-carry/<id>/<blob id>.blob`으로 옮기고(파일 이름은 blob id -- 원래 경로 이름을 쓰지 않는다, 판정 환경 이름 회피), 한 줄에 `<path>	<blob id>`인 대응표 `v5-carry/<id>/paths.tsv`를 쓴다(삭제 경로는 옮길 것이 없다), 사용자에게 diff를 보여 승인을 받아 승인 기록(`target_kind: diff`, `diff_base` = base, `diff_head` = T, `diff_path` = `diff_paths`, `target` = `diff_hash`)을 쓴다. 정리(`05` §12) 뒤 둘을 `Role: doc`로 커밋하고 gate에 push한다.
3. 2차 시도(같은 id, 새 base): test-author가 `paths.tsv`대로 `<blob id>.blob`을 `cp`로 원래 경로에 두어(이름을 되돌린다) 같은 blob을 만들고 나머지를 다시 쓴다. 발견 경로의 base blob은 문서 커밋으로 바뀌지 않으므로 해시가 같고, 승인이 base(= head 트리)에 있다.
4. 운반 디렉터리는 그 card 병합 뒤 지운다(`Role: doc`).

---

## 13. 열린 질문 (N9.2-8)

사용자 몫(삭제 승인, 승인된 design의 흐름 변경)만 남았다. 계획서 N7.2에 아래 U 항목 추가를 요청하고, 해당 card는 확정 전에 착수하지 않는다.

| 제안 ID | 질문 | 기본안 | 막는 card |
|---|---|---|---|
| U-41 | TS3에서 판정 없는 데모 섹션 18개(§6.3 표)를 지울지, 일부를 독립 oracle로 판정을 새로 붙여 남길지 | 모두 삭제(N3.11 TS3 문언). 남길 섹션은 새 assert의 oracle을 사용자가 지정 | C4(와 C9 매핑) |
| U-42 | R1 V5 승인 운반 절차(`05` 흐름 변경)를 채택할지 | 채택 | C3·C4·C5·C6·C8·C9 |
| U-43 | `.gitignore`의 기준선 예외 3줄을 사용자가 세션 밖에서 지울지 | C5 병합 뒤 삭제(`Role: user`) | D5 통과 |

그 밖에 이 문서가 새로 알린 사실(판정 대상 아님): `sizing_recipe` 기준선이 HEAD 출력과 45줄 다르다(§3) -- 기준선 갱신 이력 마지막 판 뒤의 출력 변화가 기록되지 않았다. 기본 처리는 C5 삭제 승인 때 함께 보이는 것이다. DF로 올릴지는 사용자 판단이다.

---

## 부록 A. 계수 명령

원자료 디렉터리 `D = docs/03-analysis/gain-budget-gmid-sizing-10-test-separation/`(오케스트레이터 분석 부산물, 판정 도구 아님).

| ID | 명령 | 출력 |
|---|---|---|
| A-1 | `$PY D/count_selftest_sections.py .` | `D/selftest_sections.json`, `D/selftest_sections.md`(파일별 요약과 섹션 272행 표 -- §5.1 규칙과 같은 구현) |
| A-2 | `git clone --no-hardlinks --no-local <저장소> <scratch>/iso` 뒤 `$PY D/measure_selftest.py <scratch>/iso <out> <모듈들> <시드들>`(직접 실행과 모듈 한 벌 실행, cwd = `A`), 실행 뒤 `git -C <scratch>/iso status --porcelain` | `D/selftest_run_measure.jsonl`(38회: tl·dr 시드 1~5 ×2방식, sizing 1~5 ×2, stick 1·2 ×2) |
| A-3 | 기준선 대 A-2 시드 1 stdout을 CR 제거 뒤 `diff` | `D/baseline_vs_head.diff.txt`(sizing 45줄, stick 경로 1줄) |
| A-4 | `$PY D/measure_ic_inputs.py .` | `D/ic_inputs.json`(IC5 게이트 21, 절·영역 줄 0 / library 이름 충돌 0 / 추적 instance 완전성) |
| A-5 | `git ls-files skills/analog-gmid-design/assets/tests`와 A-1의 `verdict_print_count`를 `A/tests/*.py`에 적용 | 48파일, 토큰 0 |
| A-6 | `$PY -c "import sys; sys.path.insert(0,'tools/gates'); import merge_gate as m; t=m.read_plan_tables('docs/01-plan/features/gain-budget-gmid-sizing.plan.md'); print(t.ic_parts, t.ic_test)"` | §6.5 표의 표식 Phase와 함수 이름 |

파일별 A-1 요약(assert / raise AssertionError / 거부 try / 토큰): sizing 220/20/20/113 · stick 346/10/9/232 · design_report 13/0/0/5 · topology_library 17/0/0/4.
