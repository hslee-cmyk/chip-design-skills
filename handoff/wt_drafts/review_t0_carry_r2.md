# review_t0_carry_r2 -- T0 운반 r2 재검토(2026-10-06)

검토자: 독립 agent(작성하지 않음). 범위는 `_drafts/t0_quote_check.py`, `t0_quote_check_test.py`, `t0_carry.sh`, `t0_briefs.md` 253~260행, `phase3_runbook.md` §8.4이고, 각각 `*.pre-r2.bak`과 대조했다. 기준은 `review_t0_carry_r1.md`의 S1과 m1~m3이다.
모래상자는 `/c/g376`만 썼다. TMP·TEMP는 그 아래에 두었고 cd는 쓰지 않았다. 리허설 복제는 `-c core.autocrlf=false --no-local`로 떴고, origin을 지운 뒤 gate는 모래상자 bare로 두었다. 실제 저장소는 읽기만 했다. `_drafts/t0_carry_state*`·`t0_attempt1/`·`_drafts/__pycache__/t0_*`는 생기지 않았다. 끝에 `/c/g376`을 삭제했다.

## 판정: **B 0 / S 0 / minor 3(모두 정보성, 사용 전 수정 불필요)** -- r1의 S1과 m1~m3이 모두 닫혔다. 그대로 써도 된다

## 1. r1 지적 반영 확인(실측)

| 항목 | 결과 |
|---|---|
| S1 (a) target에 묶기 | `check_record`가 V5 블록(= `## 사용자 원문`의 첫 블록 = canon V5 머리 줄)에서 두 가지를 본다. 첫째, 질문 인용이 `sums_ok`를 통과한 `$ADIR/v5_question.txt` 전체(끝 줄바꿈 하나 제외)를 부분 문자열로 담아야 한다. 둘째, 그 재료 안에 `diff_hash(target) <상태 DIFF_HASH>` 줄이 줄 단위로 있어야 한다. r1의 X1(W-1 세션 D-11 질문·답)은 단위 시험과 리허설 records 양쪽에서 거부된다 |
| S1 (b) 승인 선택지 | 답이 `V5_APPROVE_LABEL`과 같아야 하고 그 질문의 options label 목록 안에 있어야 한다. label 정본은 검사기 상수 하나이며, archive가 `labels`로 꺼내 `v5_options.txt`에 쓴다(핀 확인 뒤). X2(사용자가 '거부'를 고름)는 거부된다 |
| S1 (c) 시각 | V5 tool_use 줄의 timestamp가 상태 `ARCHIVED_AT`보다 늦어야 한다. ARCHIVED_AT은 archive 끝에서 `date -u`로 적는다. SHA256SUMS 밖에 두므로 m3 재실행 때 sums 바이트가 같게 유지된다(리허설 cmp 통과) |
| m1 | `V5_ASKED_AT`은 `YYYY-MM-DD HH:MM KST` 형식(fullmatch)이어야 하고 tool_use timestamp의 KST 분과 같아야 한다 |
| m2 | briefs 253~260행이 'v5_question.txt 전체를 바이트 그대로', '`</` 쓰지 않음', 'label = v5_options.txt 두 줄 그대로('(Recommended)' 금지)', '여러 줄이면 줄마다 `> `, 빈 줄은 `>`', records 검사 3종과 핀 2개를 모두 적었다 |
| m3 | bytes_ok 태그 거부 메시지에 '`</`를 피해 다시 묻는다' 안내가 붙었다(리허설 출력으로 확인) |
| 핀 | `sha256(t0_quote_check.py)` = `03d07619…` = `T0_QCHK_SHA256`. `canon-sha(현 초안)` = `ca5385a6…` = `T0_DRAFT_SHA256`(초안은 바뀌지 않았다) |
| diff 범위 | t0_carry.sh 변경은 머리 주석, 핀, `qchk_pin_ok` 함수화, bytes_ok 안내, archive의 labels·ARCHIVED_AT, records의 `check_record` 호출뿐이다. 실행되는 git 명령은 늘지 않았다. runbook 대조에서 §8.4 밖의 차이(b26pre 2차 card·launch 문단)는 다른 작업의 변경이라 범위 밖이다. §8.4는 r2 문단 추가뿐이다 |
| 작성자 selftest | 모래상자 경로로 다시 돌린 결과 **30/30**, 실제 답 전수 **87/87**, timestamp→KST 68개. runbook 숫자와 같다 |

## 2. 독립 사례(작성자 30사례와 따로 만듦)

단위 시험(`check_record`를 직접 부르고 가짜 jsonl은 모래상자에 둠, 핀 일치 상태에서 33건):

| 사례 | 결과 |
|---|---|
| 승인 label에 ` (Recommended)`를 붙임(선택지·답 둘 다) | 거부("선택지에 승인 label이 없다") |
| 선택지에 원본과 Recommended판이 둘 다 있고 원본을 고름 | 수용(무해) |
| 질문에 v5_question.txt가 두 번 들어 있음 / 앞에 다른 문장 / 줄 경계 없이 접두·접미 | 셋 다 수용(부분 문자열, 같은 target) -- minor 3 |
| 선택지 순서 바꿈(거부, 승인 순) | 수용(맞음) |
| ASKED_AT `+09:00`, `T` 구분자, `UTC`, 초 포함, 소문자 `kst`, 끝 공백, 1분 차이 | 7건 모두 거부 |
| archive 전에 물은 질문 | 거부 |
| 상태 ARCHIVED_AT를 더 이르게 위조하고 archive 전 질문 사용 | **수용** -- minor 2 |
| ARCHIVED_AT를 늦게 위조 / 형식 깨짐 / 줄 삭제 | 늦게 위조·형식 깨짐 거부, 줄 삭제는 records가 `st_get`에서 멈춤 |
| ARCHIVED_AT와 질문이 같은 초(ts `.001`) | 수용(ARCHIVED_AT 초 단위 절사 -- 실제로 생길 수 없는 창, 정보성) |
| 보관 v5_question.txt를 한 바이트 고침(질문은 원본) | 거부 |
| v5_question.txt에 CRLF / 빈 파일 / 끝 줄바꿈 둘 | CRLF·빈 파일 거부, 끝 줄바꿈 둘은 수용(질문에 뒤 빈 줄이 있어 부분 문자열이 성립 -- 무해) |
| batch에서 V5가 2번째 질문 | 수용(맞음) |
| batch에서 1번 질문 답이 승인 label이고 V5 답은 거부인데, 그 승인 답을 V5 인용에 붙임 | 거부 |
| batch의 두 질문이 모두 v5q를 담고, 한쪽은 승인·한쪽은 거부 → 승인 쪽 인용 | 수용(오케스트레이터 문안 몫 -- minor 3) |
| v5q에 끝 공백 줄이 있고 질문·기록이 그대로 옮김 / 질문에서 공백이 빠짐 / 기록 인용에서 공백이 빠짐 | 수용 / 거부 / 거부. 공백 손실은 fail-closed로 다시 물어야 한다. 실제로는 weakening_diff `detail`이 항상 비어 있지 않고 records가 `" ".join(split())`로 정규화하므로 v5_question.txt에 끝 공백 줄은 생기지 않는다(weakening_diff.py 185~247행 확인) |
| multiSelect로 둘 다 고름 / 승인 label이 선택지에 없고 Other로 승인 label을 입력 | 둘 다 거부 |

리허설은 작성자 `t0_carry_rehearse_r2.sh`를 `/c/g376/rehearse_v.sh`로 복사하고(경로 가드만 `/c/g376/e`로 바꿈), records 단계에 검증자 사례 7개를 넣었다(아래 V1~V7). 결과는 다음과 같다.
- 0~6절 전 구간 통과: prep → m3 복구 cmp → records → cleanup 출력 명령 실행 → local → push → after-push → 2차 → t2-check → 순서 8 이후 출력 명령 → purge. 거부 **27 = 작성자 21 + 검증자 6**, 검증자 수용 1.
  - V1 `(Recommended)` label 거부, V2 ASKED_AT `+09:00` 표기 거부.
  - **V3 batch 2번째 질문 = V5 + 선택지 순서 거부·승인 → records 수용**.
  - V4 상태 ARCHIVED_AT 늦게 위조 거부, V5 상태 ARCHIVED_AT 줄 삭제 거부(st_get에서 멈춤).
  - V6 archive 뒤 v5_question.txt 변조 → `sums_ok` 거부.
  - V7 v5_question.txt와 SHA256SUMS를 함께 고침(질문은 원본) → check_record 거부.
- 7절 '실제 저장소 불변' cmp만 달랐다. 원인은 리허설 도중 오케스트레이터가 실제 저장소에 만든 커밋 `ae1b588`(22:31:10, b26pre spec card 개정 2차)과 b26pre role 브랜치·worktree 두 개다. 리허설 산출물은 모두 `/c/g376/e/r`·`gate.git`에만 있다. 실제 저장소 remote·worktree에는 g376 흔적이 0이다. T0 운반과 무관한 동시 작업이라 리허설 판정에는 영향이 없다.

실제 답 전수는 별도 스크립트로 읽기만 했다(프로젝트 폴더 jsonl을 하위 폴더까지 재귀). AskUserQuestion은 76개이고, answers 없는 8개는 거부가 맞다. 답이 있는 질문은 87개(batch 비첫 질문 19)이며 timestamp→KST 변환 87/87, 답이 선택지 label과 같은 경우 86(나머지 1은 multiSelect 결합 답)이다. 질문 텍스트가 result에서 바뀐 경우와 끝 공백 줄 질문은 0이다. **실제 답의 57/87이 ` (Recommended)`로 끝난다**(minor 1).

## 3. B·S

없음.

## 4. minor(정보성 -- 고치지 않아도 사용 가능)

* **m1 (Recommended) 습관.** 실제 답 87개 중 57개가 `(Recommended)`로 끝나므로 V5 질문에서도 붙일 가능성이 높다. 붙이면 fail-closed로 거부되고 사용자에게 다시 물어야 한다. 머리 주석과 briefs에는 금지가 적혀 있지만 archive 끝 `say` 문장에는 'label = v5_options.txt 두 줄 그대로'만 있고 `(Recommended)` 언급이 없다. 그 문장에 '(Recommended) 붙이지 않음'을 덧붙이면 다시 묻는 비용이 줄어든다(선택).
* **m2 ARCHIVED_AT는 상태 파일에만 있어 보호되지 않는다.** 더 이르게 고치면 archive 전 질문도 통과한다(단위 A6b). 다만 그 질문도 v5_question.txt 전체(B1·T1·DH)를 담아야 하므로 이 target에 대한 질문이라는 묶음은 유지된다. 실해 경로는 의도적 변조뿐이라 drift 탐지 범위(핀 설명 '무결성 증거 아님') 안이다. DIFF_HASH는 v5_question.txt(sums)와 교차되지만 ARCHIVED_AT는 교차 대상이 없다는 점만 기록해 둔다.
* **m3 질문 문안의 의미는 검사하지 않는다.** 앞뒤 문장이 자유이고 v5q가 두 번 들어가도 된다. 그래서 다른 target을 언급하는 오도 문장이나, 한 batch에서 v5q를 담은 두 질문(승인·거부 엇갈림)도 통과한다(A3·A3b·A8c). 기록되는 target은 상태 DH이고 v5q 안의 DH 줄과 같으므로 해시 묶음은 깨지지 않는다. 문안의 정직성은 오케스트레이터 몫이다(설계상 허용 '앞뒤 문장 추가 가능').

## 5. 기타

* `t0_quote_check_test.py`의 `expect`는 AssertionError만 '거부'로 센다. ValueError(예: timestamp 날짜 범위 밖)는 시험이 죽는 쪽으로 나타나지만 records에서는 어느 쪽이든 non-zero라 운반 안전성에는 영향이 없다.
* 이 검토는 `.ai/context.md`·저장소 파일을 쓰지 않았다. 쓴 파일은 이 파일 하나다.
