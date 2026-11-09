---
id: 20261007-b26-v4-legacy-strengthen-v5
date: <YYYY-MM-DD -- 기록 작성일(운반 단계 2 (a))>
target_kind: diff
target: <TARGET_DIFF_HASH_64>
diff_base: <DIFF_BASE_40 = 1차 시도 base B1>
diff_head: <DIFF_HEAD_40 = 1차 시도 test 커밋 T1>
diff_path: skills/analog-gmid-design/assets/tests/unit/test_selftest_stick_diagram.py
scope: 결정 (다) + [V4 강화 V5] -- spec card 20261007-b26-v4-legacy-strengthen 1차 시도 test 커밋의 SD selftest 한 경로: test_s133_refine_differential_and_mirror_relations·test_s134__propose_vertical_stack_ids·test_s135_section·test_s159_apply_device_roles_gap_fill 네 test의 판정문을 손으로 유도한 리터럴 기대값으로 강화(s133 leg 8소자 분할, s134 장치 이름 동치 재서술, s135 Mamb 그룹 = {Mamb, Mout}, s159 입력 사본 구성 + 새 3쌍·파일 6쌍 리터럴) -- 약화 아님(B26-1 V4 규칙 (1) 기존 7줄 해소, 면제 (가′) 대체)
---

## 사용자 원문

> <답 -- A 양식이면 "사전 승인 (Recommended)">

(질문 <YYYY-MM-DD HH:MM KST>, 답 <YYYY-MM-DD HH:MM KST>(세션 jsonl `<세션 id>` AskUserQuestion `<toolu>`, 질문 <N>개 중 [V4 강화 V5]). 질문 원문(고치지 않고 그대로): "<_drafts/b26_v4_legacy_v5_question.md A의 question 전문>"
선택지: "사전 승인 (Recommended)" -- "<description 1>" / "1차 diff를 보고 승인" -- "<description 2>" / "(가′) 면제로 되돌림" -- "<description 3>".)

## 범위 설명

결정의 출처는 사용자 자유 답 "다로 하자."(2026-10-07 15:18 KST, 세션 jsonl `63c6146a-ab1d-4035-a169-bae810986922` 사용자 메시지 uuid `c42c4c06-8f48-4245-9917-06b8160f5340`)다.
이 답은 앞선 AskUserQuestion 답 [B26-1 V4] "(가′) 면제 + 재검토 줄 (Recommended)"(toolu `toolu_01MGv1L1nfGzLcPrjMTk5A44`)을 대체한다.
자유 문장이라 이 기록의 인용은 위 AskUserQuestion 하나다. 그 질문이 (다) 확인과 V5 승인을 함께 묻는다.

덮는 것: diff_path 한 줄(`weakening_diff.py` `diff_paths`), target 해시 하나가 이 경로의 base..T1 blob 변경 **전체**를 묶는다.
* 1차 T1의 이 파일 변경 중 위 네 test 함수 본문(docstring의 oracle 문장 포함)에서 `weakening_diff.py`가 낸 발견이다.
  종류는 'assert 삭제'(s133만 -- `==` 4줄을 분할 단언 1개로, assert 수 6 이상), '비교 완화'(Compare 연산자 변화), '리터럴 변경'(기대값·메시지·입력 구성 리터럴)이다.
* 시제품 실측(gate `6df4bd7`, 모래상자 `C:/g441`)의 발견은 9개였다. s133 셋, s134·s135·s159 각 둘. 판정은 강해진다.
  * 원 test가 놓친 변이 3종을 새 test가 잡는다(apply 무쓰기 → s159, b-leg stack 합침 → s133, Mamb 그룹 오염 → s135).
  * s134는 동치다.
  * 전체 1114 passed·15 xfailed로 base와 같다.

이 diff는 이 card **1차 시도** test 커밋 T1의 변경이다. 2차 시도는 같은 blob을 운반해 `cp`로 둔다(design 05 §12 'V5 승인 운반').

덮지 않는 것:
* 네 test 밖 단위의 발견, 다른 경로, 'assert 삭제'가 s133 밖에서 나는 변경, skip/xfail 추가, assert를 조건문·try 아래로 옮김. 그때는 이 기록을 쓰지 않고 멈춘다(B 양식 사후 질문).
* B26-1의 V5(`20261001-b26-p9-signature-update`, P9 test·B34 test 경로).
* 엔진·library 변경.

<!--
채우는 법(이 주석은 커밋 전에 지운다. 머리 자리표시도 모두 실제 값으로 바꾼다):
1. 시점: card '두 번 시도 절차' 1 뒤, 2 (a) -- 1차 auditor 순서 3이 V5 FAIL(`weakening_diff.py` 출력)을 `base_check.json`에 남긴 뒤, 1차 정리 전.
   작성·검사는 정리 전에 한다. 커밋·push는 정리(역할 브랜치 삭제) 뒤 -- EL1 `role_hooks._judge_push`가 `refs/heads/role/`에 브랜치가 남아 있으면 메인 push를 거부한다.
2. diff_base = B1(1차 `base_check.json`의 base, 40자리), diff_head = T1(40자리). 2차 base B2와 B1 사이 이 경로 blob이 같아야 한다(`git diff --quiet B1 B2 -- <경로>`).
3. target = `$PY tools/gates/weakening_diff.py --root <격리 복제본> --base B1 --head T1`의 `diff_hash`
   (= `$PY tools/gates/merge_gate.py diff-hash --repo <격리 복제본> --base B1 --head T1 skills/analog-gmid-design/assets/tests/unit/test_selftest_stick_diagram.py`).
   운반 스크립트가 셋을 대조한다. 1차 auditor 값, 오케스트레이터 재계산 값, 보관본 값이다.
   `diff_paths`가 정확히 이 경로 하나인지, 발견 단위가 네 test 안인지, 종류가 위 세 종류(assert 삭제는 s133만)인지 확인한다. 하나라도 아니면 멈춘다.
4. 인용 블록: 사전 승인(A)이면 `b26_1_quote_bind.py check 20261007-b26-v4-legacy-strengthen-v5 <이 파일> <세션 jsonl>`(PRE 핀을 질문 뒤 더함).
   사후 승인(B)이면 '## 사용자 원문' 절을 T0 블록 양식(머리 줄 → '> 질문' → '답:' → '> 답')으로 바꾸고 `t0_quote_check.check_record`(질문 재료 v5q·target·archive 시각)로 검사한다.
5. 검증: `merge_gate.py parse-approval .ai/approvals/20261007-b26-v4-legacy-strengthen-v5.md` exit 0. 기록은 2차 head 트리에 있어야 한다(`merge_gate` 9 `load_approvals(new_view)`).
   2차 판정 기록 `approvals[]`·`checks.V5.basis`에 이 id·해시와 "B1·B2 사이 이 파일 blob 같음"을 적는다. card 머리 `approval:` 줄은 이 기록과 같은 `Role: doc` 커밋의 card 개정으로 더한다.
선례 양식: `.ai/approvals/20260930-p9-e1-correction.md`, 초안 `_drafts/approval_20261001-b26-p9-signature-update.md`.
-->
