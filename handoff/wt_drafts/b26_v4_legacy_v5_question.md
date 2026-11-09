# V4 강화 card -- V5 승인 질문 문안 (오케스트레이터가 AskUserQuestion으로 그대로 묻는다)

대상 card: `20261007-b26-v4-legacy-strengthen`(초안 `_drafts/draft_b26_v4_legacy_strengthen.spec.md`). 승인 기록 문안: `_drafts/approval_20261007-b26-v4-legacy-strengthen-v5.md`.

왜 다시 묻는가: 사용자 답 "다로 하자."(2026-10-07 15:18 KST, 세션 jsonl `63c6146a-ab1d-4035-a169-bae810986922` 사용자 메시지 uuid `c42c4c06-8f48-4245-9917-06b8160f5340`)는 **자유 문장**이다.
AskUserQuestion의 tool_use·tool_result가 없다. 그래서 운반 검사기 둘 다 이 답을 승인 기록 인용으로 묶을 수 없다.
* `t0_quote_check.check_record`: 인용 블록마다 toolu id·세션 jsonl 이름, 그 tool_use의 `input.questions[].question` 전체 일치, `toolUseResult.answers[질문]` 전체 일치, 답 = `V5_APPROVE_LABEL`, V5 tool_use 시각 > 1차 archive 끝 시각을 요구한다.
* `b26_1_quote_bind.check_all`: PRE 핀(세션·toolu·header·승인 label), 답 = 승인 label, tool_result가 정확히 하나이고 is_error가 아닐 것을 요구한다.
게다가 "다로 하자."의 직전 설명은 V5 승인을 '비용'으로 적었을 뿐, 승인을 묻지 않았다. 따라서 질문이 하나 필요하다. 아래 A(권장) 또는 B 중 하나만 쓴다.

---

## A. 사전 승인 (권장 -- B26-1 U5 양식, `b26_1_quote_bind` 핀)

시점: 지금(이 card 순서 0 전). AskUserQuestion 질문 1개, multiSelect 아님.

* header: `V4 강화 V5`
* question(고치지 않고 그대로):

[V4 강화 V5] "다로 하자."에 따라 test-only card 20261007-b26-v4-legacy-strengthen을 B26-1 1차 정리 뒤·2차 시도 전에 둡니다(B26-1 2차 base = 이 card 병합본). 이 card는 test_selftest_stick_diagram.py의 4개 test(s133·s134·s135·s159) 판정문만 고칩니다. s133은 같은 그룹 == 4줄을 leg 8소자 분할 리터럴 단언 1개로, s134는 같은 출력 두 필드 비교를 장치 이름 리터럴 동치 재서술로, s135는 Mamb 그룹 = 정확히 [Mamb, Mout]으로, s159는 입력 사본에서 3쌍·M9 역할을 지우고 새 3쌍·파일 6쌍을 리터럴로 바꿉니다(지금은 기대값이 빈 목록이라 apply가 아무것도 쓰지 않아도 통과합니다). 판정은 강해집니다(시제품이 원 test가 놓친 변이 3종을 모두 잡고, 전체 1114 passed는 그대로). 하지만 기존 test의 비교·리터럴 변경이라 V5(기준 약화 검출)에 걸려 승인 기록 1건이 필요합니다. diff 해시는 test 작성자가 1차 시도에서 커밋한 뒤에야 정해집니다. 지금 승인하시면, 1차 시도의 V5 발견이 이 파일·이 4 test·세 종류(assert 삭제는 s133만, 비교 변경, 리터럴 변경) 안일 때 그 해시로 기록을 써서 2차 시도로 운반합니다. 범위를 벗어나면 기록을 쓰지 않고 실제 해시와 발견 목록을 보여 드리며 다시 여쭙니다.

* options(순서 그대로):
  1. label `사전 승인 (Recommended)` -- description `위 범위 안이면 1차 시도 diff 해시로 V5 승인 기록을 쓰고 바로 운반합니다(1차 뒤 사용자 대기 없이 2차 시도까지 진행).`
  2. label `1차 diff를 보고 승인` -- description `1차 시도 뒤 실제 diff 해시와 발견 목록을 보여 드리고 그때 승인을 묻습니다(1차 뒤 대기 1회 추가, 아래 B 질문).`
  3. label `(가′) 면제로 되돌림` -- description `강화 card를 만들지 않고 4개 test의 V4 규칙 (1) 면제 기록을 씁니다. s159의 빈 판정은 남습니다(권하지 않음).`

답이 1이면 다음 순서를 따른다.
* `b26_1_quote_bind.py`의 PRE에 핀 한 줄을 더한다. `"20261007-b26-v4-legacy-strengthen-v5": [dict(session=<세션 id>, toolu=<이 질문 toolu>, header="V4 강화 V5", approve="사전 승인 (Recommended)")]`.
  PRE가 그 파일의 정본이고 핀은 질문 뒤에만 채운다. 기존 두 핀은 그대로 둔다.
* 기록 문안의 '## 사용자 원문' 블록을 그 양식으로 채운다.
* `_drafts/user_decisions.md`에 한 줄을 더한다.

답이 2이면 1차 시도 뒤 B를 묻는다. 답이 3이면 이 card를 접고, `approval_20261007-b26-v4-exempt.dropped.md`를 되살리는 질문으로 돌아간다.

---

## B. 사후 승인 (A의 답이 2이거나, 1차 발견이 A 범위를 벗어났을 때 -- T0 양식, `t0_quote_check` 재사용)

시점: 1차 시도 auditor 순서 3 산출물 보관(archive) **뒤**. 1차 정리 전이 좋다(브랜치가 남아 있어 다시 잴 수 있다). `check_record`가 "V5 tool_use timestamp > archive 끝 시각"을 요구한다.
질문 재료 `v5q`는 운반 스크립트가 보관본 `base_check.json`에서 만든다(T0 `t0_carry.sh archive`의 `v5_question.txt` 선례). 아래 자리표시를 그 값으로 채운다.

* header: `V4 강화 V5`
* question(채운 뒤 고치지 않고 그대로):

[V4 강화 V5 -- 1차 실측] card 20261007-b26-v4-legacy-strengthen 1차 시도 test 커밋 <T1 12자리>(base <B1 12자리>)의 V5 발견입니다. 경로 skills/analog-gmid-design/assets/tests/unit/test_selftest_stick_diagram.py 하나, 발견 <N>건:
<발견 줄마다 "test 이름 | 종류 | 요약">
diff_hash(target) <64자리 diff_hash>
판정은 강해집니다(1차 auditor 변이 측정: M-a·M-b·M-c를 새 test가 잡음, 전체 <passed>/<xfailed>). 이 target으로 V5 승인 기록을 써서 2차 시도로 운반할까요?

* options: `승인 -- 이 target으로 운반한다` -- `이 diff 해시로 V5 승인 기록을 쓰고 1차 test blob을 2차 시도로 운반합니다.` / `거부 -- 운반하지 않음` -- `기록을 쓰지 않습니다. card를 고치거나 접습니다.`
  (label 두 개는 `t0_quote_check.V5_APPROVE_LABEL`·`V5_REJECT_LABEL`과 글자까지 같다 -- 검사기가 같은 상수를 쓴다.)
