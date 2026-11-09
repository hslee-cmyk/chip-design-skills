---
id: 20261001-b26-p9-signature-update
date: 2026-10-01
target_kind: diff
target: <TARGET_DIFF_HASH_64>
diff_base: <DIFF_BASE_40>
diff_head: <DIFF_HEAD_40>
diff_path: skills/analog-gmid-design/assets/tests/contracts/test_b34_grammar_explicit.py
diff_path: skills/analog-gmid-design/assets/tests/contracts/test_dup_kcl_edges.py
scope: 결정 U5 + [B26-1 V5] -- B26-1(spec card 20260930-b26-rail-accessor-set) 1차 시도 test 커밋의 V5 발견 경로 합집합 두 파일: P9 계약 test test_kcl_series_union_signature_unchanged·test_kcl_and_matching_edges_signature_unchanged의 매개변수 목록 단언을 계약 4의 새 시그니처로 갱신(원래 두 매개변수 + 키워드 전용·기본값 없음·주석 RailDeclaration인 rails -- 정확 일치 단언 유지), B34 계약 test의 새 프로세스 스크립트 문자열 _B34_FRESH_SCRIPT 안 호출 4곳에 rails= 입력(과 그 값을 얻는 한 줄)만 더함(판정 기준 그대로) -- 약화 아님
---

## 사용자 원문

> 갱신 승인 (Recommended)

(질문 2026-10-01 21:10 KST, 답 2026-10-01 21:14 KST(세션 jsonl `63c6146a-ab1d-4035-a169-bae810986922` AskUserQuestion `toolu_01KTtsbRiK7S3cv1coUsAyPw`, 질문 4개 중 [U5 P9 시그]). 질문 원문(고치지 않고 그대로): "[U5] P9 계약 test 2개(test_kcl_series_union_signature_unchanged·test_kcl_and_matching_edges_signature_unchanged)는 매개변수 목록이 정확히 [netlist, matching_pairs]·[transistors, matching_pairs]인지 단언합니다. B26-1은 두 함수에 기본값 없는 키워드 전용 rails: RailDeclaration을 더하므로 병합본에서 두 test가 FAIL합니다. 기대값 변경은 test 작성자가 혼자 할 수 없습니다(작성자≠검증자). 두 단언을 새 시그니처로 갱신해도 될까요?"
선택지: "갱신 승인 (Recommended)" -- "새 기대 = 원래 두 매개변수 + 키워드 전용·기본값 없음·주석 RailDeclaration인 rails. 정확 일치 단언은 유지되므로 약화가 아닙니다(승인 기록 diff 1건)." / "P9 시그니처 유지" -- "B26-1이 두 함수에 rails를 넘기지 않게 설계를 바꿉니다. 두 함수의 레일 판정을 선언으로 바꿀 수 없어 B26-1 목표와 충돌합니다(권하지 않음).".)

> (가) 합친 V5 승인 (Recommended)

(질문 2026-10-07 14:59 KST, 답 2026-10-07 15:00 KST(세션 jsonl `63c6146a-ab1d-4035-a169-bae810986922` AskUserQuestion `toolu_01MGv1L1nfGzLcPrjMTk5A44`, 질문 2개 중 [B26-1 V5]). 질문 원문(고치지 않고 그대로): "[B26-1 V5 승인] test_b34_grammar_explicit.py의 새 프로세스 스크립트 문자열 `_B34_FRESH_SCRIPT` 안 호출 4곳에 rails= 입력만 더하는 수정(판정 기준은 그대로)을, 이미 받은 P9 시그니처 갱신 승인(U5)과 함께 덮는 V5 승인 기록(대상 경로 = P9 test + B34 test)으로 받을까요? card '승인 줄 배치' (6)이 정한 모양입니다."
선택지: "(가) 합친 V5 승인 (Recommended)" -- "P9 test + B34 test 두 경로를 덮는 V5 승인 기록으로 2차 시도를 진행한다." / "(나) card 계약 12 개정" -- "문자열 호출을 계약에 명시하고 1차 시도부터 다시 한다.".)

## 범위 설명

덮는 것(diff_path 두 줄 = `weakening_diff.py` `diff_paths` 정렬 순서, target 해시 하나가 두 경로의 base..T1 blob 변경 **전체**를 묶는다 -- 경로마다가 아니라 발견 경로 합집합에 해시 하나):
(1) `skills/analog-gmid-design/assets/tests/contracts/test_dup_kcl_edges.py`(P9 `20260930-p9-kcl-edges` 계약 test, 병합 `93b18db`)의 두 test 기대값 변경 -- 사용자 결정 U5(2026-10-01) --
`list(sig.parameters)`를 `["netlist", "matching_pairs", "rails"]`·`["transistors", "matching_pairs", "rails"]`로, 앞 두 매개변수는 지금 단언 그대로(주석 `list`, 기본값 없음),
`rails`는 `KEYWORD_ONLY`·기본값 없음·주석 `RailDeclaration`(또는 `"RailDeclaration"`), 반환 주석 단언은 그대로. P9 card의 '시그니처 유지' 계약을 B26-1 계약 4가 대체한다.
문자열 주석 `"RailDeclaration"`을 함께 허용하는 근거: 지금 단언이 앞 두 매개변수에 `list`(또는 `"list"`)를 허용하는 `p.annotation in (list, "list")` 모양이고(`stick_diagram.py` 32행 `from __future__ import annotations` 때문에 실행 시 주석은 문자열이다 -- gate `0f23786` 실측), 새 매개변수에도 같은 모양 `(RailDeclaration, "RailDeclaration")`을 적용할 뿐이다 -- 기대가 넓어지지 않는다.
test 이름의 `unchanged`는 바꾸지 않는다. 같은 파일 안의 넷리스트 직접 호출 `rails=` 추가와 helper도 이 해시에 함께 실린다 --
그 줄들은 V5 발견이 아니므로(실측: 순수 삽입·`Compare` 불변은 발견 아님, `_drafts/review_phase3_cards_set.md` (4)) 따로 승인할 대상이 없고, 이 기록은 그 줄들의 판정 불변을 승인하는 것이 아니라 같은 blob에 함께 실릴 뿐이다.
(2) `skills/analog-gmid-design/assets/tests/contracts/test_b34_grammar_explicit.py`(B34 `20260930-b34-grammar-explicit` 계약 test)의 모듈 최상위 문자열 `_B34_FRESH_SCRIPT`(새 프로세스에서 실행하는 스크립트 원문) 변경 -- 사용자 결정 [B26-1 V5](2026-10-07) --
그 스크립트 안 계약 4 함수 호출 4곳(`find_differential_pair_candidates`·`refine_differential_and_mirror_relations`·`propose_device_roles_gap_fill`·`propose_vertical_stack_id_gap_fill`)에 `rails=rails`를 더하고
그 값을 같은 topology 파일의 `stick_diagram.rail_declaration(…)`으로 얻는 한 줄을 더한다. 문자열 상수라 `weakening_diff.py`가 단위 `<module>`의 '리터럴 변경'으로 잡는다(1차 T1 모의 측정, 2026-10-07: 이 경로 발견은 그 하나).
스크립트가 출력하는 키·값과 그것을 비교하는 test 본문의 판정(`==`)은 그대로다 -- 계약 12의 기존 test 입력 갱신(`rails=` 추가)이 문자열 안에 있을 뿐이다. 같은 파일의 test 함수 안 호출 `rails=` 추가와 helper `_b26_topology_rails`도 이 해시에 함께 실린다((1)의 같은 파일 줄과 같은 처지).
이 diff는 B26-1 **1차 시도** test 커밋 T1의 위 두 경로 변경이다(2차 시도는 같은 blob 두 개를 운반해 쓴다 -- design 05 §12 'V5 승인 운반').
덮지 않는 것: `weakening_diff.py` 발견이 위 단위 밖(P9 파일의 두 시그니처 test 밖 단위, B34 파일의 `<module>` 밖 단위, 또는 세 번째 경로)에서 나는 변경 -- 그때는 이 기록을 쓰지 않고 멈춘다,
B26-1 card의 다른 test 파일·기존 픽스처의 `supply_nets`·`rails=` 추가(발견이 나면 B26-1 승인 줄 배치 (6)), V4 발견(기존 SD selftest 4개 -- 2차 시도 전 별도 test-only 강화 card가 다룬다), 엔진 변경.

<!--
채우는 법(B26-1 순서 -- 이 주석은 커밋 전에 지운다. 머리 자리 표시 3개도 커밋 전에 모두 실제 값으로 바꾼다):
1. 시점: B26-1 **1차 시도**(병합하지 않는 계획된 측정 시도 -- B26-1 card '두 번 시도 절차')에서 test 커밋 T1이 생기고 auditor 순서 3이 V5 FAIL(`weakening_diff.py` 출력)을 `base_check.json`에 남긴 뒤, 1차 정리 전.
   이 기록은 운반 blob 두 개·`20261001-b26-v3-equiv-range`·card 개정과 같은 `Role: doc` 커밋으로 2차 시도 착수 전에 gate에 넣는다(같은 시도 안에서는 head 트리에 넣을 수 없다 -- 병합 모양).
   작성·`parse-approval`은 1차 정리 전(B26-1 card '두 번 시도 절차' 2 (a)⑥), 커밋·push는 1차 시도 정리(역할 브랜치 삭제) 뒤 -- EL1 _judge_push(`tools/gates/role_hooks.py`)가 `refs/heads/role/`에 브랜치가 남아 있으면 메인 `git push gate master:master`를 거부한다(같은 절차 2 (b)→(c)→(d)). 사용자 승인(위 원문 두 블록)은 이미 받았다.
2. diff_base = 1차 시도 base B1(1차 `base_check.json`의 base, `git -C <격리 복제본> rev-parse <B1>`), diff_head = T1(`git rev-parse <T1>`). 40자리 소문자 16진.
   2차 시도 base B2와 B1 사이에 두 경로 blob이 모두 같아야 한다(`git diff --quiet B1 B2 -- <두 경로>`) -- 같으면 2차 판정의 base..병합본 해시 식 입력이 같다.
3. target = 같은 사본에서 `$PY tools/gates/weakening_diff.py --root <격리 복제본> --base <diff_base> --head <diff_head>` 출력의 `diff_hash`
   (= `$PY tools/gates/merge_gate.py diff-hash --repo <격리 복제본> --base <diff_base> --head <diff_head> <test_b34_grammar_explicit.py 경로> <test_dup_kcl_edges.py 경로>`).
   출력 `diff_paths`가 정확히 이 두 경로(정렬)가 **아니면** 이 기록으로 V5를 통과할 수 없다(해시가 경로 합집합) -- 세 번째 경로나 한 경로뿐이면 멈추고 사용자에게 다시 묻는다.
   발견 **단위**가 P9 파일은 정확히 두 시그니처 test(`test_kcl_series_union_signature_unchanged`·`test_kcl_and_matching_edges_signature_unchanged`), B34 파일은 `<module>`의 '리터럴 변경'뿐인지도 확인한다 -- 그 밖 단위에서 발견이 나면 이 기록을 쓰지 않고 멈춘다.
   운반: 같은 정리 전 시점에 두 경로 blob을 design 05 §12 (2)대로 `v5-carry/20260930-b26-rail-accessor-set/<blob id>.blob`(경로마다 하나) + `paths.tsv`(두 줄)로 둔다(추출·보관만 -- 미커밋).
   커밋·push는 1차 시도 정리(역할 브랜치 삭제) 뒤 -- EL1 _judge_push: 정리(`git worktree remove --force` 세 경로, `git branch -D role/{test,code,audit}/20260930-b26-rail-accessor-set`, `git for-each-ref refs/heads/role/` 0줄 확인) → 이 기록·운반 blob 두 개·`paths.tsv`·`20261001-b26-v3-equiv-range`·card 개정을 `Role: doc` 커밋 하나 → `git push gate master:master` 단독 실행·전체 출력 확인(B26-1 card '두 번 시도 절차' 2 (b)→(c)→(d)). target 해시의 출처(1차 `base_check.json`)는 정리 때 사라지므로 정리 전에 `_drafts/b26_1_attempt1/attempt1_base_check.json`으로 보관한다(같은 절차 2 (a)④).
4. 2차 시도에서 test-author는 운반 blob 두 개를 `cp`로 두고 code-author는 test 파일을 바꾸지 않으므로, 2차 병합본(head)에서의 두 경로 blob은 T1의 blob과 같다 -- auditor가 2차 base..병합본으로 잰 `diff_hash`도 이 target과 같아야 한다(다르면 V5를 통과시키지 않고 멈춘다).
5. 검증: `$PY tools/gates/merge_gate.py parse-approval .ai/approvals/20261001-b26-p9-signature-update.md` exit 0(diff_path 두 줄), `b26_1_quote_bind.py check`(두 인용 블록). 기록은 auditor V5가 보는 head 트리(`weakening_diff.approved_hashes(root, head)`)에 들어 있어야 하고
   병합 규칙 9가 새 master 트리에서 같은 해시를 찾는다. 2차 시도 B26-1 판정 기록 `approvals[]`·`checks.V5.basis`에 이 id·해시를 적고(basis에 "B1·B2 사이 두 경로 blob 같음"), card 머리 `approval:` 줄은 이 기록과 같은 `Role: doc` 커밋의 card 개정으로 더한다(선례 P5b `7a1e191`, P10b `d6a9778` → `0f23786`).
선례 양식: `.ai/approvals/20260930-p9-e1-correction.md`(target_kind diff, diff_base/head = rev-parse, target = diff 해시).
-->
