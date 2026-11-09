# 독립 재검토 r1 -- Phase 4 첫 card `20261002-d4-delete-unwired` (#2)

검토 대상: `_drafts/draft_p4_first.spec.md`(r1), `_drafts/p4_first_card_notes.md`(r1). 대조: 이전 검토 `review_p4_first.md`, 반영 전 사본 `*.pre-r1.md`.
검토자는 작성자가 아니다. 저장소 쓰기 0 -- 격리 복제본 `C:/g223`(작업 저장소 `git clone --no-local` 뒤 `4a286f0` checkout, origin 제거, hooksPath 빈 값, TMP/TEMP도 그 안). 끝난 뒤 `C:/g223` 삭제, 작업 저장소 `git status`·reflog 변화 없음(아래 끝 절).
측정 판 = gate `master` = `4a286f0fad4f…`(작업 저장소 `master`와 같음). gate 도구 = `git archive 4a286f0 tools/gates`. python `C:\Python314\python.exe -B`.
작성자의 r1 모의(`C:/g219`)는 삭제돼 있어 **검토자가 모의 card를 따로 만들었다**(`C:/g223/mk.py`, 측정 전용 -- 역할 산출물 아님): base `4a286f0` → T `7355738`(계약 3·4 GONE·G-1·거부 test, 계약 6, 계약 7 전부, 계약 8 (다)) → K `b83e238`(계약 1·4·5 전체·9).

## 판정

**조건부 통과(수정 후 커밋)** -- B 0, S 1, minor 3.
이전 검토의 B1·S1~S3·minor 1~7은 모두 card 문장에서 해소됐다(아래 1절). (다)는 test-first로 실행 가능하고 병합본에서 green이며, 이동 커밋 sha 자리를 바꾸는 공격은 거부한다.
다만 (다)는 'HEAD 도구의 경로 줄 밖 내용 고정'을 **영구히** 푼다 -- 계산을 바꾸는 HEAD 도구 변이 4종이 전부 (다)에서 PASS(옛 test·(가')에서는 FAIL)다. 계약 5 범위 문장 + auditor K diff 검토는 **이 card 한 번, 사람 판정으로만** 그 자리를 메운다(기계 gate 없음, 다음 card부터는 아무것도 없음). 사용자 질문으로 올릴 문안은 4절.

## 1. 이전 검토 항목 해소 확인

| 항목 | 해소 여부 | 근거(r1 card 위치) |
|---|---|---|
| B1 허용 목록 test-first 불가 | 해소 -- 기본안 (다)로 바꿈, (가')는 15쌍 원문 고정 | 계약 8, D1. 검토자 모의 K 도구로 `non_path_line_changes(939f926 blob, K 도구)` 재측정 = **15건**, 쪽·줄 번호·원문이 D1 (가') 목록과 정확히 같음 |
| S1 Phase 3 F1이 같은 test를 먼저 깸 | 해소 -- '확정(측정)'으로, Phase 3 쪽 누락 보고 | notes §3-2, card P3-5 |
| S2 계약 7 (iii) 실행 불가 | 해소 -- (iii)도 손 규칙, `m_odd_leaves` 문구 삭제 | 계약 7 (iii). 모의에서 그대로 구현해 suite green |
| S3 design 판 v0.9.8·V8 | 해소 -- v0.9.9, V8 = 'N/A -- 계측 미도입, 폴백 경로 불변'(P-38) | 의도 1행, 판정 유형 근거 |
| minor 1 `_invert_gm_id_for_current` import | 해소(사실로) | 계약 7. 4a286f0에서도 `tests/` 사용은 `test_selftest_sizing_recipe.py:651` 하나 |
| minor 2 test 파일 낡은 언급 617·1221 | 해소 | 계약 7 |
| minor 3 `design-report-spec.md:400` | 해소 | 계약 10, 실측 5 |
| minor 4 V3 인벤토리 간선 문구 | 해소 | 계약 3 둘째 문단 |
| minor 5 동작 차이 한 줄 | 해소 | 계약 5 끝 |
| minor 6 D-5 표 행 먼저 삭제 | 해소 -- V5 범위 설명 (a) | 결정 필요 항목 V5 줄 |
| minor 7 `@dataclass` 데코레이터 | 해소 | 계약 1 |

## 2. 재측정(검토자 모의, 4a286f0)

| 항목 | 결과 | card 주장과 |
|---|---|---|
| 전체 suite(gate `pytest_gate.ini`, `--gmid-phase=2`, 각 트리 rootdir) | base **1047 passed, 15 xfailed** / T만 **2 failed(`test_d4_gone_ast`·`test_d4_gone_text`, AssertionError), 1050 passed, 15 xfailed** -- 계약 8 (다) test는 T에서 green / 병합본 **1052 passed, 15 xfailed, 실패 0** | 작성자 1050과 2 차이 = 검토자 모의가 계약 8 거부(`36e170e`·`a574f97`)를 **별도 parametrize test 2개**로 둔 몫 -- 아래 S1 |
| V3(`mutate_changed.py`, **4a286f0 판** -- changed-stmt 범위 규칙 반영 뒤) | **PASS, targets SR·SD, mutants 0** | 같음(36e170e 판과 결과 같음). 도구 `tests/tools/derive_achievable_bounds.py`는 V3 대상이 아니다(모듈 수준 스크립트, def 0) |
| V7(`reachability.py`, gate_config) | PASS, `new_defs` 0, unreached 0 | 같음 |
| reg_check | base 발견 0 / 병합본 발견 0 | 같음 |
| V5(`weakening_diff.py`) | FAIL(승인 없음, 예상대로) 발견 **8건**: `test_ic5` `test_domain_table_uses_allowed_values`(21→19)·`<module>`(두 표 행·docstring), `test_ts6_probe_relocate` `test_moved_tool_matches_base_except_path_lines` 2건, `test_s007`·`test_s028`(함수 삭제), `test_s058_section` 2건(비교 완화·리터럴 변경). 새 test·docstring·주석 수정은 발견 0 | **선언 범위(계약 6·7·8)와 단위가 정확히 같다.** 단 TS6 단위의 패턴은 검토자 모의에서 'assert 삭제 + 리터럴 변경'(card는 '비교 완화 + 리터럴 변경') -- 구현에 따라 달라진다(minor 2) |
| `parse_spec_card`(4a286f0 `role_paths.py`, `expect_id`) | 통과 -- id·phase `4`·`equivalence`·`gate_change: no`·approval 1, 절 11개 템플릿 순서 | 같음 |
| `interface_card.py --root <4a286f0 clone>` | 생성 성공, 기존 함수 22개 | 같음(이동 커밋 sha는 interface card에 없다 -- card 계약 문장으로 test-author에게 간다) |
| 이동 커밋 사실 | `9d6800e` 부모 1개 = `a574f97`. `9d6800e`는 새 자리 **추가만**(A), 옛 자리 삭제는 부모 `a574f97`(TS6 test 커밋). `9d6800e`는 HEAD의 조상이지만 **first-parent 사슬 위에는 없다**. `9d6800e:도구` blob = 4a286f0 HEAD 도구 blob(`a3e97b7`) | card 계약 8과 같음 |
| gate 판 이동 36e170e → 4a286f0 | 바뀐 경로 = 승인 기록 1·계획 1줄(839행)·design 05·spec/interface card 1쌍. `skills/**`·`workspaces/**`·레지스트리·card가 인용한 계획 줄 번호 변화 0 | card '작성 전 실측' 15는 36e170e 판으로 적혀 있음(minor 3) |

## 3. 계약 8 (다) 공격 변이(검토자 설계 -- 작성자 4개 밖)

판정기 구현은 검토자 모의(T 커밋의 `move_commit_blob_text` -- 부모 = `rev-list --parents` 정확히 1개, 부재 = `ls-tree` exit 0·빈 출력). 별도 worktree에서 test 함수를 직접 불러 판정.

| # | 변이 | (다) | 옛 test(HEAD 대조) | (가') 15쌍 |
|---|---|---|---|---|
| 1 | 병합본 그대로 | **PASS** | FAIL(15줄) | PASS |
| 2 | 거부 표본 `36e170e`(부모에 새 자리)·`a574f97`(새 자리 없음) | 각각 **거부** | -- | -- |
| 3a | HEAD 도구: `achievable_metric_bound(..., sense=sense)` → `sense="max"` | **PASS** | FAIL | FAIL |
| 3b | HEAD 도구: `c["value"] = …r["conservative"]` → `r["best"]`(보수값 대신 최댓값을 선언에 기록) | **PASS** | FAIL | FAIL |
| 3c | HEAD 도구: `c["_derived"] = {…}` 기록 제거 | **PASS** | FAIL | FAIL |
| 3d | HEAD 도구: `slsqp_kwargs=…` → `None`(선언 탐색 인자 무시) | **PASS** | FAIL | FAIL |
| 4a | sha 상수를 가짜 이동 커밋(부모 `a574f97`, 비경로 줄 1개 변경)으로 | 거부 | -- | -- |
| 4b | sha 상수를 내용 같은 가짜 이동 커밋(HEAD 조상 아님)으로 | PASS(조상 검사 없음 -- 내용이 같아 해 없음) | -- | -- |
| 4c | sha 상수를 부모에 새 자리가 있는 커밋으로 | 거부 | -- | -- |
| 5 | 얕은 복제 경계(`.git/shallow`에 `9d6800e` -- 부모 미상) | 검토자 구현(부모 수 검사) **FAIL(닫힘)** / 순진한 구현(`git show sha^:경로` 실패 = '부모에 없음') **PASS(열림)** | 옛 test는 `939f926` 없으면 닫힘 | -- |
| 6 | rename 탐지 | `diff -M 9d6800e^ 9d6800e` = `A`(rename 아님), `diff -M 939f926 9d6800e` = `R097`. card는 rename을 요구하지 않음 -- 맞다. test-author가 'rename 커밋'이나 '같은 커밋에서 옛 자리 삭제'를 요구하면 실제 sha가 red | -- | -- |
| 7 | replace 객체(`git replace`)로 `9d6800e`·`939f926`을 바꿔치기 | 속는다 | 속는다(기준선이 같은 `git show`) | 속는다 -- **(다)에 새로 생긴 위험 아님** |

결론: **(다)를 속여 이동 사실 판정을 통과시키는 길은 sha 상수 변경뿐**이고(test diff에 보이며 V5 '리터럴 변경'으로 잡힌다), 얕은 복제 경계에서의 구조 검사 열림은 구현 문구 문제다(minor 1 -- 핵심 blob 대조는 그대로라 해는 작다).
대신 (다)는 **HEAD 도구를 아예 보지 않는다** -- 3a~3d처럼 유도값 자체를 바꾸는 변경을 어떤 test도 잡지 못한다. 옛 test와 (가')는 모두 잡는다.

**잃는 보호와 대체 여부(정확히)**:
* 잃는 것: `A/tests/tools/derive_achievable_bounds.py`(topology 선언의 `value`·`_derived`를 **쓰는** 운영 도구)의 경로 줄 밖 내용 고정. (다) 뒤에 남는 HEAD 도구 test는 자리(`test_moved_tool_is_in_tools_dir`)와 경로 줄 값(`test_moved_tool_paths_equal_pre_move_targets`)뿐이다. 도구 동작을 보는 다른 test는 저장소에 없다(`git grep derive_achievable_bounds` -- TS6 test 하나). V3도 도구를 대상으로 잡지 않는다(실측 targets SR·SD).
* 계약 5 범위 문장 + auditor K diff 검토가 대체하는 범위: **이 card의 K diff에 한해, 사람(auditor)의 diff 판독으로만**. 기계 판정이 아니고(실패하는 test가 없다), 이 card가 병합된 뒤의 card(Phase 3 F1 포함)에는 적용되지 않는다. → **완전한 대체가 아니다.** 원래 TS6 계약 5 문장은 '이동 결과가 원본과 같다'(이동 card의 상태 문장)였고 옛 test가 그것을 영구 불변식으로 구현한 것이라, 영구 고정이 원래 의도였는지는 card 문장만으로 정해지지 않는다 -- 그래서 사용자 판단이다.

## S (커밋 전 고칠 것)

**S1. 계약 8이 요구하는 거부 test가 계약 7·14의 '수집 test id 집합'에 없다.**
* 계약 8: "거부(같은 test 파일에서 실제 커밋으로 보인다): `36e170e`… 거부, `a574f97`… 거부". 계약 7 끝: "test id 집합은 base − {s007, s028} + {새 GONE·G-1 test, 손 규칙 helper 판정 test}와 같다", 계약 14: "수집 id = 계약 7의 집합".
* 측정: 검토자 모의는 거부를 TS6 파일의 parametrize test 2개로 두었고 병합본 수집 = **1052**(작성자 모의 1050 = 거부를 별도 id로 두지 않은 모양). test-author가 자연스럽게 별도 test로 쓰면 auditor의 계약 14 대조가 FAIL → 재시도.
* 고칠 것(택1): 계약 7 집합에 '+ 계약 8 거부 test(`test_ts6_probe_relocate.py` 안)'를 넣는다, 또는 계약 8에 '거부는 기존 함수 `test_moved_tool_matches_base_except_path_lines` 안에서 보인다(새 test id 없음)'를 적는다.

## minor

1. **계약 8 구조 확인을 닫힌 쪽으로 적을 것**: "부모 커밋에는 새 자리가 없다"를 `git show <sha>^:<경로>` 실패로 구현하면 얕은 복제 경계(부모 객체 없음)에서 **통과**한다(실측 5 -- 순진한 구현 PASS, 부모 수 검사 구현 FAIL). 문구: "부모는 정확히 하나이고 읽을 수 있어야 하며(`git rev-list --parents -n 1`), 새 자리 부재는 그 부모 tree를 읽어 확인한다(`git ls-tree` 성공 + 빈 출력) -- 읽기 실패는 거부". 조상 검사를 넣는다면 `merge-base --is-ancestor`로(`9d6800e`는 first-parent 사슬 밖 -- first-parent로 쓰면 실제 sha가 red). 'rename'·'같은 커밋에서 옛 자리 삭제'는 요구하지 않는다고 한 줄(실측 6 -- 실제 이동은 `a574f97` 삭제 + `9d6800e` 추가로 나뉘어 있다).
2. **V5 범위를 패턴이 아니라 (파일, 단위)로**: D1·V5 줄의 'TS6 … (비교 완화 + 리터럴 변경)'은 구현마다 다르다(검토자 모의 = 'assert 삭제 + 리터럴 변경'). 승인 기록 범위 설명은 (파일, 단위) 8건 목록으로 적고 패턴은 '예'로만.
3. **측정 판 표기**: '작성 전 실측' 15는 gate `36e170e` 판이다. gate가 `4a286f0`로 나아갔다(V3 changed-stmt 범위 규칙 승인 -- `mutate_changed.py`는 그 card의 도구 변경 전이라 같은 판, 문서·승인 기록만 바뀜). 검토자 재측정(4a286f0): V3 PASS·mutants 0, V5 8건 범위 안, V7·reg_check 0, parse_spec_card·interface_card 통과 -- 한 줄로 판 갱신을 적을 것.

## 4. 사용자 질문 문안(AskUserQuestion용, 한국어)

**질문**: "#2 card(`d4-delete-unwired`)는 사이드카 함수를 지우면서 운영 도구 `tests/tools/derive_achievable_bounds.py`도 고칩니다. 그런데 TS6 계약 test 하나가 이 도구의 '경로 줄 밖 내용'을 이동 원본(`939f926`)과 영원히 같게 묶어 두고 있어, 도구를 고치려면 그 test를 바꿔야 합니다(V5 약화 승인 대상). 어느 쪽으로 바꿀까요?"

* **(다) 판정 대상을 '이동 커밋 9d6800e의 도구'로 바꾼다 (작성자 기본안)** -- "TS6 이동이 경로 줄만 바꿨다"는 사실은 계속 판정합니다(불변 이력). 대신 **현재 도구 내용은 더 이상 어떤 test도 보지 않습니다**: 실측으로 도구가 선언에 쓰는 값을 바꾸는 변경(보수값 대신 최댓값 기록, `_derived` 기록 제거, 탐색 인자 무시, sense 강제) 4종이 전부 통과합니다(옛 test는 전부 잡음). 이 card에서는 '도구 변경은 사이드카 읽기·쓰기 제거와 문구 수정뿐'이라는 card 문장을 auditor가 diff로 눈으로 확인하는 것으로 대신하지만, 기계 판정이 아니고 다음 card부터는 그것도 없습니다. 장점: test를 먼저 쓸 수 있고, Phase 3 F1(도구 import 줄 변경)과 이후 card가 이 test를 다시 건드리지 않습니다(V5 승인 반복 없음).
* **(가') 현재 도구 대조를 유지하고 이 card가 바꾸는 15줄만 원문으로 허용한다** -- 도구 내용 고정이 계속 남아 위 4종 변경을 모두 잡습니다. 대신 도구를 고치는 card마다 허용 줄 원문 목록을 card에 적고 V5 승인을 다시 받아야 합니다(가까운 예: Phase 3 F1의 import 줄 1쌍, 이 card의 15줄). code-author가 쓸 docstring·출력 문구도 card가 글자 그대로 정해야 합니다.
* **(기타) 다른 방식** -- 예: (다)에 더해 도구의 핵심 계산·기록 줄(`achievable_metric_bound` 호출 인자, `value`·`_derived` 기록 블록)만 현재 도구에서 계속 고정하는 좁은 test를 둔다(검토자 제안, 미측정), 또는 D-3을 이 card에서 빼고 사이드카를 남긴다(대안 (나) -- 저장 위치 두 개 유지).

(헤더 후보: "TS6 도구 test" / 선택지 라벨: "(다) 이동 커밋 판정", "(가') 15줄 허용 유지", "기타")

## 5. 측정 명령(재현)과 정리

* 모의: `C:/g223/mk.py`(T·K 생성), suite `run_suites.sh`(`python -B -m pytest -q -p no:cacheprovider -c <gate>/pytest_gate.ini --rootdir=<트리> --confcutdir=<트리> --gmid-phase=2 -rfE`, APPDATA 명시), gate `run_gates.sh`(`weakening_diff.py`·`reachability.py --config`·`reg_check.py`·`mutate_changed.py --gmid-phase 2`), 공격 `attack.py`(별도 worktree `wA`), 얕은 경계 = 별도 clone `C:/g223/sh`에 `.git/shallow` = `9d6800e`.
* 모의 V5 `diff_hash` `e16a2346…`는 모의 diff 해시 -- 실제 기록에 쓰지 말 것.
* 끝난 뒤 `C:/g223` 삭제. 작업 저장소: HEAD `4a286f0`, `git status --porcelain` 해시와 reflog 머리가 시작 때와 같음.
