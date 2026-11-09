# review_b26_1_qbind -- B26-1 carry 인용 묶기(qbind) 독립 검증

검증자: 독립 verifier(작성자 아님), 2026-10-07. 대상: `_drafts/b26_1_quote_bind.py`(신규), `b26_1_quote_bind_test.py`(신규),
`b26_1_kit_selftest/fill_u3.py`·`b26_1_carry.sh`·`b26_1_kit_selftest/records_u3_test.sh`·`b26_1_kit_selftest/out_check_test.sh`(각 `*.pre-qbind.bak` 대비).

## 판정: B 0 / S 0 / minor 4 (+ 절차 메모 1)

통과로 본다. 요구 항목은 모두 코드와 실측으로 확인했다. minor는 위협 범위 밖 강화 제안이거나 test 문구 정밀도 문제다.

## 1. 요구 항목 대조(코드 + 실측)

| 요구 | 결과 | 근거 |
|---|---|---|
| 기록 4·5 인용 = 자기 jsonl·자기 toolu `toolu_01KTtsbRiK7S3cv1coUsAyPw` | OK | `PRE` 핀(session·toolu), `basename(jsonl)== <sid>.jsonl`, `_check_blocks`가 `jdir/<sid>.jsonl`의 그 toolu만 읽음 |
| 질문 전체 일치 | OK | `qs.count(q)==1`(t0 `_check_blocks`), 공백 하나·한 글자 변조 STOP |
| 답 자리 == `toolUseResult.answers[질문]` == 핀 승인 label | OK | 답은 절 정규식의 답 자리에서만 뽑음, 본문 다른 곳/부록 인용은 무시됨(elsewhere 사례 STOP) |
| header / N / options 일치 | OK | header 3중(jsonl·인용·핀), N = 질문 수, 선택지 줄 = label·description·순서 전체, multiSelect 거부 |
| tool_result 정확히 하나, is_error 아님 | OK(minor m1) | t0 `_read_ask` 1개 단정 + `_result_meta` is_error |
| KST 분 시각 | OK | 실제 12:10:47Z→21:10, 12:14:58Z→21:14. 경계 12:15:00Z는 STOP, 12:14:00Z는 PASS |
| P9 초안 바이트 핀 | OK | `P9_DRAFT_SHA256=22da78b7…` = 실측 sha256. QBIND `050a27cd…`, QCHK `03d07619…`, U3 초안 `3d2333b7…`, fill_u3 `fb8a1948…`도 모두 실측과 같음 |
| 기록 4: state 옆 임시 파일에 쓰고, check 뒤에만 이동 | OK | `$STATE.a4.md` → `QBIND check` → `mv`. set -Eeuo pipefail이라 check가 실패하면 mv 없음. records_u3 rec4_* STOP 사례가 "기록 4가 쓰였다" 없음을 단정 |
| 기록 5 | OK | fill_u3 `check_jsonl`이 같은 `check_record` 호출, 실패하면 쓰기 전 exit 1 |
| t0_quote_check.py sha256 | OK | `03d07619cca7c93888a900f1314e2a5a86892cbe962ab4491385ac7fa8974421`(= carry QCHK_SHA256 = t0_carry.sh T0_QCHK_SHA256) |

## 2. 자기 시험 4종(모래상자 사본, 피검 바이트 동일 확인 후)

- `b26_1_quote_bind_test.py`: **27 / 불일치 0**(사례마다 기대 이유 문구가 실제 거부 메시지와 일치함을 TSV로 확인)
- `t0_quote_check_test.py`(변경 없음): **30/30 OK**, 실제 답 전수 87/87 수용
- `records_u3_test.sh`: **24 / 불일치 0**(1회차는 사례 24개 전부 ok였지만, 같은 시각 오케스트레이터 커밋 863a037(12:32:59) 때문에 마지막 실제 저장소 reflog 앞뒤 비교가 멈춤. 재실행에서 reflog·HEAD 863a037 앞뒤 같음)
- `out_check_test.sh`: **62 / 불일치 0**

## 3. 독립 적대 사례(직접 작성, 49개: 기대와 다른 결과 2개는 정보용)

모두 기대대로였다: 답 = 거부 선택지 / 다른 비승인 선택지, 실제 승인 label을 범위 설명·부록에 두고 답 자리만 변조, 같은 toolu와 같은 내용을 가진 다른 세션 이름의 파일,
jsonl에서 사용자가 실제로 거부(기록이 승인을 인용 → 답 불일치, 기록이 거부를 인용 → 승인 label 아님),
answers는 승인인데 tool_result 문자열은 거부(교차 확인으로 STOP), 기록 쪽 선택지 순서 바꿈 / jsonl 쪽 선택지 순서 바꿈 / 선택지 하나 누락,
'(Recommended)'를 답·선택지·둘 다에서 제거, jsonl 전체에서 일관되게 제거(핀 label 없음으로 STOP), 끝 공백 / 이중 공백 / NBSP / 탭 / 빈 줄 추가 / CRLF / BOM,
is_error true / false(PASS) / 현실형(`toolUseResult`가 "Error: …" 문자열), tool_result 두 줄 / 한 줄에 둘 / 두 번째 결과가 에러, tool_use 중복, 결과 없음,
jsonl header 변경, multiSelect, timestamp 없음, 9시간 어긋난 시각(UTC를 KST로 착각), 절 두 개, 머리 id 중복, 기록 5 본문을 기록 4 id로 검사,
U4 질문·선택지·header·U4 승인 답으로 통째 바꿈(핀 header로 STOP), 핀 없는 id.

정보용 2개: `is_error: "true"`(문자열)·`is_error: 1`이 PASS → m1.

## 4. 작성자가 기대값을 바꾼 곳 -- 원칙 판정

| 변경 | 판정 | 이유 |
|---|---|---|
| records_u3 `tamper_quote` 이유 "질문 원문 불일치" → "질문 인용이 그 tool_use의 질문 하나와 전체 일치하지 않는다" | 정당 | 검사기를 옛 check_jsonl에서 t0 `_check_blocks`로 바꿨기 때문. 기대(STOP, 기록 없음, RECORDS=1 없음)는 그대로이고, 새 문구는 의도한 층(질문 대조)의 메시지와 정확히 같다(실측 TSV 확인) |
| `tamper_answer` 이유 "답 원문 인용 불일치" → "답 인용 != 사용자가 고른 답" | 정당 | 같은 이유. 실제 거부도 답 대조 층에서 났다 |
| records_u3 0단계 범위 잠금 `ins_vars` 허용 이름 +4(P9_DRAFT_SHA256·QBIND·QBIND_SHA256·QCHK_SHA256) | 정당 | 같은 자리(DRAFT4 다음)에 넣은 상수 줄만, 이름 단위로 허용. 값은 따로 묶임(PIN_4 단정 신설, QBIND·QCHK 핀은 carry가 실행할 때 대조하고 qbind_pin 사례로 확인). stage_records 본문 변경은 원래 허용 구간 안. 이름만 보고 오른쪽 값은 보지 않는 약점은 원래부터 있던 것 |
| out_check 필터 +4 이름 | 정당 | 피검 heredoc 밖의 상수 줄을 비교에서 빼는 것일 뿐이다 |
| mkkit 일반화(DRAFT4/P9_DRAFT_SHA256/QBIND 덮어쓰기) | 정당 | 다른 줄 바이트가 같다는 단정이 유지되고, 허용 접두는 세 개만 늘었다 |

약화된 기대값은 없다. 새 사례(rec4_* 5, qbind_pin)는 추가만 했다.

## 5. `t0_quote_check._read_ask`가 is_error를 보지 않는 문제 -- 사실 확인과 T0 영향

- 확인: `_read_ask`는 tool_result를 (블록, toolUseResult)로만 모으고 `is_error`를 읽지 않는다(작성자 관찰이 맞다).
- 실제 코퍼스 전수(읽기만, 프로젝트 jsonl 전체): AskUserQuestion tool_result 76개 중 is_error true가 8개이고, **8개 모두 toolUseResult가 문자열**이다("Error: The user doesn't want to proceed…", "User rejected tool use", "InputValidationError…"). 그래서 answers dict가 없다. is_error 값은 bool이거나 키 자체가 없다(문자열·정수 0건).
- 영향: T0에서 에러난 질문은 `_read_ask`의 "toolUseResult.answers가 없다" 단정에서 이미 거부된다(이유 문구는 다름). 통과하려면 is_error true이면서 answers dict와 '"질문"="답"' 문자열을 모두 갖춘 **손으로 만든 jsonl**이 필요하다. jsonl은 harness가 쓰고, T0는 archive 뒤 시각·target 해시 묶기를 더 하므로 위협 범위 밖이다. **T0 수정은 지금 필요 없다**(백로그 권장). 고치면 sha 03d07619 핀 두 곳(carry QCHK_SHA256, t0_carry T0_QCHK_SHA256)을 같이 고쳐야 한다.

## 6. minor

- **m1** `_result_meta` 판정이 `rm[0][0] is not True`라서 참으로 읽히는 bool 아닌 값("true", 1)을 통과시킨다. harness는 bool만 쓰고 코퍼스에도 0건이라 실해는 없다. `in (None, False)`로 좁히기를 권장(QBIND 핀 갱신 동반).
- **m2** `_result_meta`의 `len(rm)==1` 단정은 도달 불가다. t0 `_read_ask`가 같은 조건을 먼저 단정한다. 그래서 quote_bind_test result_id/result_dup의 기대 문구 "tool_result가 정확히 하나가 아니다"는 t0 메시지("jsonl에 그 tool_result가 정확히 하나가 아니다")와 맞아 통과한 것이고, qbind 자기 검사를 증명하지는 않는다. 해는 없지만 docstring의 'tool_result 정확히 하나' 출처를 t0로 밝혀 두면 좋다.
- **m3** CLI `check`는 jsonl의 **파일 이름**만 핀과 대조하고 디렉터리는 보지 않는다. 다른 폴더에 같은 이름의 위조 jsonl을 두면 PASS한다(정보 사례 forged_samename_otherdir). carry는 고정 경로 `JSONL5`(`$HOME/.claude/projects/…`)만 넘기므로 위협 범위 밖이다. 원하면 dirname도 핀으로 대조할 수 있다.
- **m4** quote_bind_test의 `header`·`question_other` 사례는 기대 이유 문구가 "header"인데, 이 부분 문자열은 절 양식 오류 메시지("…·N·[header])…")에도 들어 있다. 그래서 다른 층에서 거부돼도 통과하는 약한 잠금이다(실제 이유는 맞게 "질문 header != 인용 [header] != 핀"이었다). "질문 header != 인용"으로 좁히기를 권장.

## 7. 절차 메모(검증자 측)

- 이 실행 환경에서는 `VAR=x bash …` 접두 방식이든 `export` 방식이든 자식 bash로 환경변수가 전달되지 않았다(실측: `env FOO=1 /usr/bin/bash`만 전달됨). 그래서 `OUT_CHECK_SCR`·`RECORDS_U3_SCR`이 무시되고 기본 모래상자 `/c/g241`(없던 것, 시험이 만들고 지움)·`/c/g252/rt`가 쓰였다. `/c/g252`는 2026-10-02부터 있던 빈 폴더(다른 agent 것)이고, 그 아래 `rt`만 시험이 만들고 지웠다. `/c/g252`는 건드리지 않고 그대로(빈 상태) 두었다. 결과 TSV는 KIT/DR을 모래상자 사본으로 바꾼 사본 test가 `/c/g387` 아래에 썼다. 실제 `_drafts`에는 이 리뷰 파일만 썼다.
- 후속 agent 브리핑에는 "모래상자 변수는 `env NAME=… bash script`로 넘긴다"를 넣을 것을 권장한다.
