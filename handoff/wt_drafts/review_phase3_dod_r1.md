# 독립 검토 r1 -- Phase 3 DoD 브리핑 v1 + kit r1 + design 30 정정 도구 (2026-10-02)

대상: `_drafts/draft_phase3_dod.md`(v1, 사본 `.pre-r1.bak`), `_drafts/phase3_dod_kit/*`(r1, 사본 `*.pre-r1.bak`), `_drafts/design30_dod_corrections.py`·`.md`. 앞 검토 `_drafts/review_phase3_dod.md`.
기준: gate `master` `4a286f0`. 검토자는 작성자가 아니다. 저장소는 읽기만(`git -C`). 모래상자 `C:/g255`(복제 `--no-hardlinks --no-local -c core.longpaths=true -c core.autocrlf=false`, origin 제거, TMP/TEMP/TMPDIR = `C:/g255/tmp`), 끝에 삭제.

## 판정: 경미(minor)만 -- B 0, S 0. 공식 실행 진행 가능

## 1. 앞 검토 S·경미 해소 대조

| 항목 | 해소 | 확인 방법 |
|---|---|---|
| S1 design `fresh()` | 해소(정정 도구 D1, kit `to_h`/`fresh_k`) | §4 모래상자 적용 + 합성 저장소에서 패치 판 `fresh()` 재현: 추적 파일을 더럽힌 A → `fresh B` rc 0·HEAD = B·파일 v2·status 0줄. 없는 판 → `E5 INVALID: 판 전환 실패 deadbeef` rc 1. `index.lock` → 같은 줄 rc 1. 옛 판은 같은 입력에서 rc 1·HEAD = A·파일 dirty(결함 재현) |
| S2-a E1 공허 | 해소 | 리허설 `E1 PENDING(E0 미충족 …)`. 합성: F2 base findings 3 → PASS, 0 → INVALID, 없음 → PENDING, F2 base ERROR → PENDING, H 위반 → FAIL, H exit 1·findings 0 → FAIL |
| S2-b E0 빈 표 | 해소 | MOD10 행을 뺀 계획 사본 → `E0 INVALID N3.10 표 9행`, 빈 layer.json → INVALID |
| S2-c N6.3-4 공허 | 해소 | 리허설 `4 PENDING(n=0 …)`. 덮음 대조는 §2 |
| S2-d test-only `{test}` | 해소 | 코드 `roles == {"test"}`. Phase 2 재현 test-only 5장 모두 `['test']` |
| S2-e equivalence 근거 | 해소 | basis 비면 `근거 문장 없음` ok=False, 인용 판정은 auditor 몫으로 표시 |
| S2-f E4 assignment | 해소 | 합성: `assignment` 없는 plan → `E4 INVALID` |
| S2-g E3 rc | 해소 | 모래상자에서 `blk_e3_ast.py`를 rc 3 가짜로 바꿔 `e3` 단독 실행: 두 판 모두 `E3 FAIL(도구 오류 rc=3 …)`만, `E3 PASS`·거부 확인 수 줄 없음 |
| 단계 HEAD 단정 | 해소 | `<iso>`를 P2D로 옮긴 뒤 `run_dod.sh … e6` → `need_h`가 H로 옮김(rc 0, HEAD 4a286f0). `index.lock`으로 옮기기 실패시 → `[HEAD] FAIL`, `e6 INVALID: 복제본 HEAD != H`, rc 1 |
| 경미 1(MPC blob) | 해소 | `inputs_p3` `missing`에 넣음(코드 확인) |
| 경미 2(V1 phase) | 해소 | `v1_phase != "3"` → `missing` |
| 경미 3(cards.txt 8줄) | 해소 | 합성: 3줄 → INVALID, 8줄·3칸 → INVALID, 0줄 → PENDING(공식이면 G5가 먼저 멈춤) |
| 경미 4·5·8(문구) | 해소 | 초안 §5 2행·§9-6·§8 watch 행 고침. 복제본 reflog `to 5f643a9` 3줄 |
| 경미 6(0.5 card 관찰) | 해소 | 리허설 `34 … audit=True merge=True`(판정 기준 밖) |
| 경미 7 | 조치 없음(확인 항목) | -- |
| 선택 D2~D4 | 채택 | §4 |

## 2. N6.3-4 덮음 대조를 좁힌 것 -- **기준 충실, 약화 아님**

기준 문구의 출처: 계획 N6.3(`4a286f0` 1028~1034행)에는 '4번'이 없다. 첫 bullet은 "auditor 판정 기록 PASS(N4.2 도입 표 기준), merge gate(EL4) 통과, 동작 변경 spec card마다 거부해야 할 입력의 test 존재"이다. N6.3-1~5 번호와 4번 '카드 밖 엔진 변경 0'은 Phase 2 브리핑이 만든 운용 정의다. `_drafts/phase2_dod_brief.md` 264행:
> 4. **카드 밖 엔진 변경 0**: `git -C "$ISO" log --no-merges --format=%H da03c0e.."$H" -- 'skills/analog-gmid-design/assets/*.py' workspaces/run_harness.py 'skills/analog-gmid-design/assets/library/*.json'` … 전부가 `Role: code` 또는 `Role: test` trailer와, 위 17건 중 하나인 `Change-Id`를 가진 커밋.

committed `phase2-dod.md` 97행도 같은 문구다. 기준은 "엔진 경로를 바꾼 범위 안 커밋 → 목록 card의 code/test 커밋"이라는 **한 방향**이다. 반대 방향("card 커밋 전부가 목록에 있다")은 기준에 없고 내 앞 검토 §4-c가 공허 방지로 **더한** 검사였다. 그 문구를 그대로 걸면 Phase 2 재현이 거짓 FAIL을 낸다. 실측: `cbddcb9`(`registry-grade-fix` code_commit, `Role: code`)는 `function-registry.md` 3줄만 바꾸고 엔진 경로를 건드리지 않아 목록에 들 수 없다. 그러니 앞 검토 문구가 틀렸다. 작성자가 좁힌 판("엔진 경로를 바꾼 card 커밋은 목록에 있어야 한다, 아니면 '경로 밖'으로 적기만")은 기준 본문(한 방향 검사, 0개면 PENDING)을 그대로 둔다. 고친 것은 검토가 더한 보조 검사뿐이다. → **충실, 사용자 승인 불필요.**

v1 검사기 Phase 2 재현(`n63_p3.py <iso> 5f643a9 da03c0e … 2`): `1 PASS(n=34) | 2 FAIL(18/17, 기록 없음 1) | 3 PASS | 4 PASS(n=31, 어긋남 0, 덮음 누락 0, 경로 밖 1) | 5 PASS`. card 커밋 29 = 목록 안 28 + 경로 밖 1(`cbddcb9`). test-only 5장 `{test}`. 초안 §6 수치와 같다.

합성 공격(`C:/g255/n63`, phase 3 모드, FU card 하나):

| 시나리오 | 4번 결과 | 기대와 같은가 |
|---|---|---|
| S0/T0 정직 | PASS | O |
| S1 trailer 없는 엔진 커밋을 master에 | **FAIL**(어긋남 1) | O |
| S6 엔진 커밋 Change-Id가 목록 밖 card | **FAIL** | O |
| S7 엔진 변경을 `Role: audit` 커밋에 섞음 | **FAIL** | O |
| S3 판정 기록 code_commit = 병합 안 된 곁가지 엔진 커밋 | **FAIL**(덮음 누락 1) | O(덮음 대조가 잡는다) |
| S4b 판정 기록 code_commit = P2D 이전 엔진 커밋 | **FAIL**(덮음 누락 1) | O |
| S5 card code 커밋이 문서만(cbddcb9 모양) | PASS, 경로 밖 1 | O(거짓 FAIL 없음) |
| S2 엔진 변경을 `merge <id>` 병합 커밋 안에만 넣음(evil merge) | **PASS** | 기준 그대로의 구멍(아래 경미 m2) |
| S8 경로 밖 파일(`assets/data.yaml`) | PASS | 기준 pathspec 정의대로 |
| S9 판정 기록 code_commit = 병합 커밋 | PASS, '경로 밖' 1 | 오분류(아래 경미 m3) |

'목록 밖에 숨긴 엔진 경로 커밋'은 범위 안 비병합 커밋이면 모두 잡힌다(S1·S6·S7). 범위 밖 커밋을 기록에 적으면 덮음 대조가 잡는다(S3·S4b). 좁힌 덮음 대조는 범위 안 커밋에 대해서는 정의상 항상 참이다. 판별력은 S3·S4b 모양에서만 나온다.

## 3. design 30 정정 = `Role: doc` 문서 커밋만 -- **확인함**

- 계획 N3.12.2 623행 `| 오케스트레이터 | docs/01-plan/** | -- | 없음 |`, 624행 `| 오케스트레이터 | docs/02-design/** | docs/02-design/disputes/** | 없음 |`(`4a286f0`, 그대로 인용).
- `merge_gate.py` 821행 `if "승인 기록" in pending or role == "user":` -- `pending`은 조건이 `승인 기록`인 경로에서만 생긴다(`role_paths.py` 36행 `CONTENT_CONDITIONS`). design·history는 해당 없음.
- 857행 `if PLAN_PATH in paths:` -- `PLAN_PATH` = `docs/01-plan/features/gain-budget-gmid-sizing.plan.md`(role_paths 21행). history.md는 대상 아님.
- 470~481행 `rule6_dates_approvals`: 승인 파일이 있는지 보고 `parse_approval_header`로 머리만 파싱한다. 720행~ `gate_change_ok`: spec card `approval:` 기록이 있고 파싱되는지만 본다.
- `git grep diff_base|diff_head 4a286f0 -- tools/gates hooks .githooks`(redteam 제외): `merge_gate.py` 178·247·262~268행(파서)뿐이다. `target_kind: diff`의 `target`을 대조하는 곳은 V5(`merge_gate.py` 1219~1224행, 판정 기록 V5 basis 해시)와 `weakening_diff.approved_hashes`(test 분류 diff 전용)뿐이다. UD-0 기록(`20260930-30-module-split-design`, `diff_base 3e835e0…`·`diff_head 6c8287f…`, design 30 포함 diff_path 6개)을 지금 트리로 다시 해시하는 게이트 코드는 없다. `30-module-split|a4350dc|design.md`를 tools/gates·hooks에서 찾으면 0줄, `02-design`은 spec/interface/disputes 경로뿐이다.
- 선례 `58024de`(Role: doc, design 20 1줄 + history 14줄, 승인 기록 없음)와 같은 모양이다. 정정은 §10 표 통과 기준 문구를 바꾸지 않는다(§4). 그래서 DEC-40(234행)·U-18(1093행)의 '기준 약화' 승인 대상이 아니다. 결론에 동의한다.

## 4. 정정 도구 모래상자 실행(`C:/g255/dp`, `4a286f0` 판 두 파일 사본)

- `--check`: pending 12, exit 1 → 적용: exit 0, 바뀐 줄 `[786, 788, 789, 793, 1034, 1036, 1037, 1038, 1040, 1044, 1099]`, history +1행 → `--check`: applied 12, exit 0 → 재적용: 바뀐 줄 0, sha256 불변(멱등).
- 앵커 중복 거부: 1034행을 끝에 한 번 더 넣은 사본 → exit 2, 두 파일 sha256 불변. history 앵커 2번 → `H ERROR: 앵커 2번` exit 2, 불변. `--only D2` → exit 2. CRLF 사본 → exit 2. D1만 먼저 적용하고 나중에 전체 적용 → 한 번에 적용한 결과와 바이트 같다.
- 합성 저장소에 패치 전후 design을 커밋하고 `extract_design_blocks.py`를 돌림: sha256 5개(`ec96033a…`·`b3803fca…`·`ae6422d6…`·`de554c33…`·`e00a4634…`)와 줄 범위가 전후 같다. `git diff --numstat` = `11 11`.
- 통과 기준 무변경: §10 표(1100~1119행, E0~E6 행 1106~1113)가 전후 바이트 같다. 바뀐 11줄은 모두 bash 블록 안이다(`|`로 시작하는 줄 없음). E5 행의 "`E5 INVALID` 줄이 없고"가 D1 출력을 그대로 FAIL로 만든다. D3의 `$H`는 같은 블록 1029행 `H=$(git -C "$ISO" rev-parse HEAD)`에서 정의된다.

## 5. 리허설 재실행(`run_dod.sh /c/g255 4a286f0 rehearse`, 전 단계, 2026-10-02 ~18:00~18:48)

v1 초안 §8.0과 **모두 같다**. E1 = `PENDING(E0 미충족 …) exit=0 findings=0`, N6.3 = `1 PASS(n=35) | 2 FAIL(0/20) | 3 FAIL | 4 PENDING(n=0 …) | 5 FAIL`. 그 밖: E0 FAIL 1/10. E2 PENDING(V3 `H^..H` exit 0, 키 5개 없음). E3 세 shim FAIL·거부 확인 stmt 69·call 9·파일 67(제외 1)·`제외 집합 밖 importer 66파일`. E3b `LIVE 0 0 1`+INVALID. E4·E6 PENDING. IMPORT-ANY 5/5/0. PT3·`--gmid-dod` 둘 다 1047 passed·15 xfailed. E-INST 두 회로 같음(raw `2fc426d9…`·`ef3cd996…`). E-LIB `1d2e3bf6…`. rails 계약 FAIL 9. W1·W2·W3 PASS. 블록 sha256 5개도 같다. 차이 하나: G2 역할 브랜치가 3개(`role/audit|code|test/20260930-v3-changed-stmt-scope`, 35 진행 상황)다. 리허설 INFO이고 공식이면 멈춘다.

## 6. 경미

- m1 `judge_p3.e01`: H 출력에 `findings` 키가 없으면(`present`만 있음) `f = []`로 읽어 `E1 PASS`가 된다(합성 확인). 실제 도구는 ERROR가 아니면 늘 `findings`를 낸다(import_layering 90행). 그래서 위험은 낮지만 E0의 `present` 단정과 맞추려면 `"findings" not in d` → INVALID로 할 것.
- m2 N6.3-4 `--no-merges`: 엔진 변경을 병합 커밋 안에만 넣으면(S2) 목록에 나오지 않는다. Phase 2 기준 문구도 같은 구멍이 있다. 다만 EL4가 막는다(`merge_gate.py` 1146행 "M 트리가 M^2(code 끝) 트리와 다르다", 역할 밖 병합은 1101~1110행 역할 경로 트리 동일). 기준을 바꿀 일은 아니다. 결과 '절차 메모'에 "병합 커밋 내용은 N6.3-3의 EL4 통과로 덮인다"를 한 줄 적으면 충분하다.
- m3 덮음 대조 `diff-tree`는 `-m`·`--root`가 없어서 병합 커밋이나 부모 없는 커밋을 '경로 밖'으로 분류한다(S9). EL4가 `code_commit == K`(비병합 `Role: code`, 1198행)를 강제하므로 받아들여진 기록에서는 생기지 않는다. 고친다면 `c`의 부모가 하나가 아닐 때 `MISSING_FROM_LIST` 대신 `UNCLASSIFIED`로 적을 것.
- m4 `e4` 출력 표지 `E4 PENDING/INVALID plan 출력 없음`은 두 상태를 한 줄에 적는다. 공식이면 G5가 먼저 멈추므로 판정에 영향은 없다. 표지만 하나로 정할 것.
- m5 초안 §8.0 G2 "역할 브랜치 2개"는 지금 3개다(진행 상황 -- 공식 실행 전 0이어야 함은 같다).

## 7. 정리

`C:/g255` 전체 삭제. `/tmp`·`.`에 쓰지 않았다. 메인 저장소: HEAD `4a286f0`, `status --porcelain --ignored`(175줄)·reflog(345줄)가 실행 전 스냅숏과 바이트 같다(kit W1·W2와 별도 대조). 이 검토가 쓴 저장소 밖 파일은 `_drafts/review_phase3_dod_r1.md` 하나다.
