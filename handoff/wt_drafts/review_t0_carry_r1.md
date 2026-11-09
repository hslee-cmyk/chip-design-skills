# review_t0_carry_r1 -- T0 운반 r1 재검토(2026-10-06)

검토자: 독립 agent(작성 안 함). 범위: `_drafts/t0_carry.sh`(`.pre-r1.bak` 대비), `t0_quote_check.py`·`t0_quote_check_test.py`(신규), `approval_20260930-p3-tests-location-free.md`(`.pre-r1.bak` 대비), `phase3_runbook.md` §8.4, `t0_briefs.md` 256행. 기준: `review_t0_carry.md`(S1·S2·m1~m5).
모래상자 `/c/g357`만 씀(TMP·TEMP 그 아래, 복제 `-c core.autocrlf=false --no-local`, origin 제거, gate = 모래상자 bare). 실제 저장소: 끝에 status 38줄·HEAD `6c724de`·role 브랜치 0·worktree 4줄로 그대로이고, 리허설 snap cmp도 같음. `_drafts/t0_carry_state*`·`t0_attempt1/`는 생기지 않았다. 끝에 `/c/g357` 삭제.

## 판정: **B 0 / S 1 / minor 3** -- 앞선 S1·S2·m1~m5는 모두 닫힘. 새 S1(V5 블록이 이 target·승인 선택지에 묶이지 않는다)을 고친 뒤 사용한다

## 1. 앞선 지적 반영 확인(실측)

| 항목 | 결과 |
|---|---|
| S1 답 묶기 | `check_quotes`: 블록마다 머리 줄의 jsonl 하나·toolu 하나, 질문 = `input.questions[].question` 하나와 전체 일치, 답 = `toolUseResult.answers[질문]` 전체 일치, tool_result 문자열의 `"Q"="A"`도 교차 확인. 앞선 거부 사례 4개는 모두 거부된다(리허설·selftest) |
| S2 | 양식 42·43행 삭제 확인(diff). bytes_ok에 `</[A-Za-z]` 추가. 끝에 덧붙인 태그는 canon 핀이 먼저 거부하고, 자리 값 안 태그는 bytes_ok가 거부한다 |
| m1 핀 | `canon-sha(현 초안)` = `T0_DRAFT_SHA256` `ca5385a6…`, `sha256(t0_quote_check.py)` = `T0_QCHK_SHA256` `95bc2c28…`로 둘 다 일치. `.pre-r1.bak` canon은 `d1a05d73…`라 다르다(태그 두 줄). 핀 두 값이 커밋 본문에 들어감을 확인 |
| m2 | t2-check가 `sums_ok`와 `$ADIR/t1_blobs.tsv` ↔ 상태 사본 cmp를 거친다. 변조 두 가지 모두 거부 |
| m3 | archive를 다시 실행하면 거부(ARCHIVED=1). 중단 흔적이 있으면 rm 2줄과 다시 실행 명령을 출력하고, 그대로 실행하면 SHA256SUMS가 첫 실행과 바이트까지 같다 |
| m4·m5 | after-push가 순서 8 → fetch → merge --ff-only → 정리 4 → purge → push를 옵션까지 붙여 출력한다. 리허설에서 출력된 명령을 그대로 실행해 PASS |
| 가드 명령 | `push`·`worktree add/remove`·`branch -D`·m3 `rm -rf`는 echo/say 안에만 있다(grep 251·252·373·376·455·477~489·546행). 실행되는 것은 fetch·add·commit·purge의 git rm과 읽기뿐이다 |
| `__pycache__` | `_drafts/__pycache__`에 t0_* pyc 없음. records는 `-B`로 돈다 |

## 2. 독립 사례(작성자 20사례와 따로 만듦)

단위(`check_quotes`·`canon` 직접 호출, 가짜 jsonl은 모래상자에 둠):

| 사례 | 결과 |
|---|---|
| 같은 질문 문장의 다른 toolu: 머리 A1(사용자 답 '거부'), 인용 = A2의 답 '승인' | 거부(맞음) |
| 답 끝 공백, 답 앞 공백 두 칸, 질문 줄 끝 공백 | 셋 다 거부 |
| NFD 답 ↔ NFC jsonl, NFC 인용 ↔ NFD jsonl | 둘 다 거부. 정규화하지 않음(fail-closed), NFD ↔ NFD는 수용 |
| 초안 전체 CRLF | 거부 |
| 다중 선택 `a.py, c.py` 전체 / 일부 / 순서 바꿈 | 수용 / 거부 / 거부 |
| 같은 toolu가 두 jsonl에 있을 때(사본) 머리 = 사본 | 수용(맞음) |
| 한 jsonl 안에 같은 toolu 줄이 두 번 | 거부(fail-closed) |
| 머리 줄에 toolu 둘, `답:` 두 번, `답:` 연속 | 모두 거부(canon과 parse_blocks 양쪽) |
| answers에는 있지만 tool_result 문자열에 `"Q"="A"`가 없음 | 거부 |
| **V5 자리에 W-1 세션의 무관한 실제 질문·답(D-11)** | **수용 -- S1 참조** |
| **V5 답 = 사용자가 실제로 고른 '거부 -- 운반하지 않음'** | **수용 -- S1 참조** |
| V5_ASKED_AT 자리에 산문 한 줄 | 수용 -- m1 |
| `date:` 줄에 산문 | canon은 통과하지만 parse-approval이 거부(`date 형식 위반`) |

리허설: 작성자 `t0_carry_rehearse_r1.sh`를 `/c/g357/e`로 옮기고, records 단계에 검증자 사례 10개(X1~X10)를 넣었다. 결과 **전 구간 PASS, 거부 23 = 작성자 16 + 검증자 7**: 답 끝 공백, `답:` 블록 중복, 머리 줄 toolu 둘, 같은 질문 다른 toolu 답, 정당한 질문 산문 안 `</b>`(bytes_ok), date 산문(parse-approval), 검사기 바이트 drift(키트 사본 → `T0_QCHK_SHA256 핀 불일치`). X1~X3(아래 S1·m1)은 실제 records에서도 **rc 0**이다.

실제 답 전수(읽기만, 프로젝트 폴더 jsonl 597개를 하위 폴더까지 재귀): AskUserQuestion 76개(toolu 74개, 둘은 두 파일에 있음), 답이 있는 질문 **87/87 수용**. load_ask 거부 8개는 모두 tool_result `is_error=True`(사용자가 도구 사용을 거절한 경우 7, JSON parse 실패 1)이므로 거부가 맞다. 다중 선택 1개, CR·`</`·자리표시 모양을 담은 실제 질문·답은 0개. 작성자 selftest를 모래상자 경로로 바꿔 돌린 결과 20/20, 전수 87/87이다(runbook의 85/85는 기록 시점 값이라 지금은 87).

## 3. S

* **S1 V5 인용 블록이 '이 target에 대한 승인'에 묶이지 않는다.** r1은 '인용 = 그 toolu의 실제 질문·고른 답'까지만 증명한다. 그 질문이 이 V5 발견에 대한 것인지, 그 답이 승인인지는 보지 않는다. 실측(실제 records, 모래상자):
  - X1: V5 머리 줄·질문·답을 W-1 세션의 `[D-11] 이동 도구…` 질문과 그 실제 답으로 바꿔도 **rc 0** → 승인 기록과 parse-approval까지 통과한다. 작성자 selftest 115행은 이 경우를 '정상' 수용으로 못박고 있다.
  - X2: 사용자가 '거부 -- 운반하지 않음'을 골랐고 기록이 그 답을 그대로 인용해도 **rc 0** → '거부'를 인용한 **승인** 기록이 만들어진다.

  briefs §4(253행)와 runbook 8.4는 'V5 질문 = `v5_question.txt`의 발견·해시 그대로'라고 하지만 records가 이를 재지 않는다. 기록의 권위는 사용자 답이므로(앞선 S1과 같은 이유) 사용 전에 고친다. 권고(최소):
  - (a) V5 블록(canon이 고른 첫 블록)의 질문이 `diff_hash(target) $DH` 줄을 담는다. 더 좋은 방법은 `sums_ok`를 통과한 `$ADIR/v5_question.txt` 본문 전체를 부분 문자열로 담는 것이다.
  - (b) V5 답이 그 tool_use 선택지 label 중 승인 쪽(예: `승인`으로 시작) 하나와 같다.
  - (c) 가능하면 V5 tool_use 줄의 timestamp가 ARCHIVED 뒤다.

  selftest 115행은 거부 사례로 바꾸고, X1·X2를 거부 사례로 넣는다.

## 4. minor

* **m1** canon 자리 중 `V5_ASKED_AT`는 산문 한 줄을 받아도 핀이 일치한다(X3 rc 0). jsonl tool_use의 `timestamp`(KST로 바꾼 값)와 대조하거나 `YYYY-MM-DD HH:MM KST` 형식으로 한정하면 닫힌다. `date:` 줄은 parse-approval이 형식을 재므로 문제없다.
* **m2** `t0_briefs.md` 256행 records 설명 '인용 줄 jsonl 원문 대조'는 r1 뒤 낡았다(틀린 말은 아니지만 너무 약함). 판단: 정본 명령 블록이므로 '인용 블록마다 자기 jsonl·toolu, 질문·고른 답 전체 일치 + 입력 핀 2개(T0_DRAFT_SHA256·T0_QCHK_SHA256)'로 고친다. S1을 고치면 '+ V5 질문에 target 해시·승인 선택지'도 함께 넣는다. 253행 '바이트 그대로'에도 '여러 줄이면 줄마다 `> `, 빈 줄은 `>`'를 덧붙이면 archive 출력과 같아진다.
* **m3** bytes_ok `</[A-Za-z]`는 정당한 질문 산문(예: `a </b>`)도 거부한다(X8). 실제 87개 질문에는 0건이고 fail-closed라 실해는 없다. 거부 메시지에 'V5 질문 문안에서 `</`를 피한다'는 안내 한 줄이면 충분하다.

## 5. 기타 확인

t0_carry.sh diff는 위 S1·S2·m1~m5 반영 범위 밖을 건드리지 않았다(옵션 `$SELF` 출력, archive 복구 분기, 핀, t2-check 기준). 양식 diff는 끝 두 줄 삭제뿐이다. runbook 8.4의 r1 문단은 실측과 맞는다(전수 수는 시점 값).
