# review_t0_carry -- T0 두 번 시도 V5 운반 독립 검토(2026-10-06)

검토자: 독립 agent(작성 안 함). 범위: `_drafts/t0_carry.sh`(신규, 37752B 19:09판), `approval_20260930-p3-tests-location-free.md`(양식), `t0_launch.sh`·`t0_briefs.md`·`draft_p3_t0.spec.md`(`.pre-x1.bak` 대비 diff), `phase3_runbook.md` §8(.pre-x1.bak 대비), `f1_v5_carry_plan.md`.
근거: design 05 §12 'V5 승인 운반'·§9.2-4(gate master `6c724de`, `git -C show`), 선례 `b26_1_carry.sh`·`review_b26_1_carry_today.md`.
모래상자 `/c/g332`만 씀(TMP·TEMP도 그 아래, `clone --no-local -c core.autocrlf=false`, origin 제거, gate_config `gate_path` = 모래상자 bare gate). 끝에 `/c/g332` 삭제. 실제 저장소: status 38줄·refs 6·worktree 6·reflog `6c724de`·gate/master 시작과 끝 같음, `_drafts/t0_carry_state*`·`t0_attempt1/` 생성 없음.

## 판정: **B 0 / S 2 / minor 5** -- S1·S2를 고친 뒤 사용

## 1. 확인한 것(실측)

| 항목 | 결과 |
|---|---|
| `bash -n` | t0_carry.sh·t0_launch.sh OK |
| set -E·pipefail | 28~30행 `set -Eeuo pipefail` + `inherit_errexit` + ERR trap |
| 가드 명령 | 실행은 `fetch`·`add`·`commit`·`rm`(purge)·읽기뿐. `push`·`worktree remove --force`·`branch -D`·`worktree add`는 echo/say 안에서만(grep 365·368·446·468·473·476·530행). 모래상자에서 `cleanup` 뒤 worktree 2·role 브랜치 2 그대로, `final` 뒤 gate master = B1 그대로 |
| 저장소 가드 | `--repo` 별칭 3종(끝 `/`, `C:\…`, 실제 저장소 worktree 경로) rc 2, 단계 뒤 옵션 rc 2, 모래상자 모드 실제 `--state` rc 2, 상대 `--state` rc 2, `--draft` 누락 rc 2 |
| 순서 거부 | prep 전 records·cleaned·purge rc 1, archive 재실행 rc 1(덮어쓰지 않음), cleanup 전 cleaned·local rc 1(CLEANUP_PRINTED), cleanup 출력만 하고 실행 전 cleaned rc 1, worktree만 지우고 브랜치 남김 cleaned rc 1, push 전 after-push rc 1, 2차 test 중 purge rc 1(role 브랜치), **병합 전 purge rc 1**(lc_pred_ok '판정 기록 없음') |
| 운반 blob 변조 | records 뒤 `.blob`에 한 줄 덧붙임 → cleanup rc 1(360행 hash-object) |
| 전 구간 E2E | setup(비교 완화 1건 `==`→`>=` + 발견 밖 import 줄 변경, Role: test, audit base_check.json 키 V5 = 실제 weakening_diff 출력) → prep rc 0(3중 diff_hash 일치, blob 1 + paths.tsv, 보관 12파일) → records_good rc 0(parse-approval OK) → cleanup 4줄 → 모래상자에서 실행 → local rc 0(Role: doc 커밋 하나 = 기록 + blob + paths.tsv, 본문에 SHA256SUMS 발췌 -- review_b26_1 m1 반영) → push → after-push rc 0(B2 트리 V5 target 있음) → 2차: paths.tsv대로 cp + 발견 밖 경로 일부러 drift → **t2-check rc 1**(diff 출력) → 고침 커밋 → t2-check rc 0(PASS approved, 같은 해시, 2-커밋 Role: test 사슬 OK) → audit 커밋(V1~V10 PASS 흉내) → push·ff → 정리 → purge rc 0(운반 2파일 D, 승인 기록 유지) |
| T0-V4 순서 | t0_launch `pre` 322행이 gate master `_approved_ids`에 test_s009 id를 요구 → V4 면제 커밋이 1차 S 전이어야 진행(맞음). carry check는 B1 = launch S만 받으므로 따로 재확인하지 않아도 같다 |
| test-only 모양(2차) | t2-check가 B2..T2 첫 부모 사슬·전부 Role: test·Change-Id를 단정, after-push·브리프 3.2가 'audit 커밋 = T 바로 위, 병합 없음' + 순서 7 전 빈 브랜치 가드. design §9.2-4 test-only 행과 같음. (모래상자 gate에는 pre-receive가 없어 gate 판정 자체는 재지 않았다) |
| T1.patch 예외 | 정당. check가 B1..T1 바뀐 경로 ⊆ 계약 8 여덟(test 경로만, 실제 실행은 정확히 여덟)을 단정하므로 patch에 엔진 소스가 없고, 1차 test-author 자기 산출물이다 -- B26-1과 같다 |
| W-1 인용 | 실제 jsonl `toolu_01GVLKut4JY6FMvvZJEvhKS4`: 질문 원문·답 `(가) T0에서 test import 수정 (Recommended)` 바이트 같음, 시각 04:35:31Z/04:38:47Z = 13:35/13:38 KST 맞음 |
| 운반 경로 | `docs/03-analysis/gain-budget-gmid-sizing-30-module-split/v5-carry/<id>/<blob id>.blob` + paths.tsv = §12 (2) |

## 2. S

* **S1 jsonl 대조가 '사용자가 고른 답'을 묶지 않는다.** records 292~337행은 `## 사용자 원문` 절의 모든 `> ` 줄을, 절 안 모든 toolu id의 tool_use **입력**(질문 + 선택지 label 전부)과 tool_result 문자열을 합친 풀에서 **부분 문자열**로만 찾는다. 실측(모래상자, 가짜 V5 AskUserQuestion: 선택지 `승인 (Recommended)`·`거부 -- 운반하지 않음`, 답 = 승인):
  - V5 답 자리에 **고르지 않은 선택지** `거부 -- 운반하지 않음` → records **rc 0**
  - V5 답 `승인`(잘린 부분 문자열) → rc 0
  - W-1 답을 같은 tool_use의 다른 질문 답 `(가) 계획 표 MOD1에 추가 (Recommended)`로 → rc 0
  - W-1 답을 고르지 않은 `(나) shim에 기존 import 허용`으로 → rc 0
  - (정상 거부: 지어낸 답 rc 1, W-1 질문 한 글자 변조 rc 1, 자리표시 남음 rc 1)
  runbook §8.4의 '꾸민 답 거부'는 jsonl에 없는 문자열만 잰 것이다. 승인 기록의 권위가 사용자 답이므로 사용 전 고친다. 권고: 답 줄은 `toolUseResult.answers[<그 질문>]`(또는 tool_result의 `"Q"="A"`)와 **전체 일치**, 질문 줄은 그 tool_use `input.questions[].question`과 전체 일치, 인용 블록마다 자기 toolu에 묶기(V5 블록 ↔ `<V5_TOOLU>`, W-1 블록 ↔ W-1 id) -- b26_1의 fill_u3 check_jsonl 방식. self-test에 위 4사례를 거부 사례로 넣는다.
* **S2 승인 양식 끝에 도구 호출 찌꺼기 `</content>`·`</invoke>` 두 줄(42·43행).** bytes_ok는 대문자 자리표시·HTML 주석만 보므로 통과하고, 모래상자 local 커밋의 `.ai/approvals/20260930-p3-tests-location-free.md` 끝 바이트에 그대로 들어갔다(od 실측). 영구 승인 기록이므로 두 줄을 지우고, bytes_ok에 `</` 태그(또는 마지막 줄 = 범위 설명 문장) 검사를 더한다.

## 3. minor

* **m1** 양식 산문 핀 없음: '기대값 불변(계약 5)' → '기대값 변경 허용' 변조가 records rc 0. Role: doc 커밋 diff로 보이므로 minor(review_b26_1 m1과 같은 성격).
* **m2** t2-check는 `$STATE.t1_blobs.tsv`(상태 파일 옆, 해시 핀 없음)와 비교한다. `sums_ok` + `$ADIR/t1_blobs.tsv`와 cmp를 더하면 커밋 본문 SHA256SUMS 발췌까지 한 사슬이 된다.
* **m3** archive가 중간에 죽으면 `$R/$D`·`$ADIR`가 남아 재실행이 거부된다(fail-closed, 수동 삭제 필요) -- 머리 주석 '중단 뒤 이어 하기'와 다르다. 안내 한 줄 권고.
* **m4** after-push 476행 순서 8 안내에 push 뒤 `fetch`·`merge --ff-only`가 빠졌다(브리프 §4에는 있음, purge가 HEAD = gate/master로 막으므로 안전 쪽).
* **m5** after-push가 출력하는 `bash $0 t2-check`·`purge`에 옵션이 없다(실제 실행에는 맞음, 모래상자 리허설 때만 주의).

## 4. 문서 변경

t0_launch(echo 5줄·주석 3줄만), t0_briefs(3.1 1차 V5 기록·멈춤, 3.2 병합 없음·T 바로 위·2차에서만, 1절 '2차 시도' 문단, §4 명령 블록), spec card (X-1) 문단, runbook §8·§18 X-1/X-2 닫힘 -- design 05 §12·§9.2-4·§9.2-9와 어긋남 없음. f1_v5_carry_plan의 분석(1차 = 순서 0~3, 2차에 병합)도 §9.2-4 equivalence 모양과 맞다(F1 launch 전이라 미배선 -- 문서에 명시됨).
