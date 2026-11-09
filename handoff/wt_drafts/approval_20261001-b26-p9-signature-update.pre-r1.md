---
id: 20261001-b26-p9-signature-update
date: 2026-10-01
target_kind: diff
target: <TARGET_DIFF_HASH_64>
diff_base: <DIFF_BASE_40>
diff_head: <DIFF_HEAD_40>
diff_path: skills/analog-gmid-design/assets/tests/contracts/test_dup_kcl_edges.py
scope: 결정 U5 -- P9 계약 test test_kcl_series_union_signature_unchanged·test_kcl_and_matching_edges_signature_unchanged의 매개변수 목록 단언을 B26-1(spec card 20260930-b26-rail-accessor-set) 계약 4의 새 시그니처로 갱신(원래 두 매개변수 + 키워드 전용·기본값 없음·주석 RailDeclaration인 rails) -- 정확 일치 단언 유지, 약화 아님
---

## 사용자 원문

> 갱신 승인 (Recommended)

(질문 2026-10-01 21:10 KST, 답 2026-10-01 21:14 KST(세션 jsonl `63c6146a-ab1d-4035-a169-bae810986922` AskUserQuestion `toolu_01KTtsbRiK7S3cv1coUsAyPw`, 질문 4개 중 [U5 P9 시그]). 질문 원문(고치지 않고 그대로): "[U5] P9 계약 test 2개(test_kcl_series_union_signature_unchanged·test_kcl_and_matching_edges_signature_unchanged)는 매개변수 목록이 정확히 [netlist, matching_pairs]·[transistors, matching_pairs]인지 단언합니다. B26-1은 두 함수에 기본값 없는 키워드 전용 rails: RailDeclaration을 더하므로 병합본에서 두 test가 FAIL합니다. 기대값 변경은 test 작성자가 혼자 할 수 없습니다(작성자≠검증자). 두 단언을 새 시그니처로 갱신해도 될까요?"
선택지: "갱신 승인 (Recommended)" -- "새 기대 = 원래 두 매개변수 + 키워드 전용·기본값 없음·주석 RailDeclaration인 rails. 정확 일치 단언은 유지되므로 약화가 아닙니다(승인 기록 diff 1건)." / "P9 시그니처 유지" -- "B26-1이 두 함수에 rails를 넘기지 않게 설계를 바꿉니다. 두 함수의 레일 판정을 선언으로 바꿀 수 없어 B26-1 목표와 충돌합니다(권하지 않음).".)

## 범위 설명

덮는 것: `skills/analog-gmid-design/assets/tests/contracts/test_dup_kcl_edges.py`(P9 `20260930-p9-kcl-edges` 계약 test, 병합 `b7765b0`)의 두 test 기대값 변경 --
`list(sig.parameters)`를 `["netlist", "matching_pairs", "rails"]`·`["transistors", "matching_pairs", "rails"]`로, 앞 두 매개변수는 지금 단언 그대로(주석 `list`, 기본값 없음),
`rails`는 `KEYWORD_ONLY`·기본값 없음·주석 `RailDeclaration`(또는 `"RailDeclaration"`), 반환 주석 단언은 그대로. P9 card의 '시그니처 유지' 계약을 B26-1 계약 4가 대체한다.
test 이름의 `unchanged`는 바꾸지 않는다. 이 diff는 B26-1 test 커밋 T의 위 경로 변경이다.
덮지 않는 것: P9 계약 test의 다른 test·픽스처(넷리스트만 쓰는 직접 호출에 `rails=`를 더하는 것은 판정·기대값 불변이라 이 기록 밖 -- `weakening_diff.py`가 그 변경을 표시하면 따로 승인),
B26-1 card의 다른 test 파일·기존 픽스처의 `supply_nets`·`rails=` 추가(B26-1 승인 줄 배치 (6)), 엔진 변경.

<!--
채우는 법(B26-1 순서 -- 이 주석은 커밋 전에 지운다. 머리 자리 표시 3개도 커밋 전에 모두 실제 값으로 바꾼다):
1. 시점: B26-1 test-author의 test 커밋 T가 test worktree에 생긴 뒤, auditor가 V5를 재기 전. 사용자 승인(위 원문)은 이미 받았으므로 test-author는 이 기록 없이 갱신을 시작해도 된다.
2. diff_base = B26-1 착수 base(판정 기록 base_commit과 같은 커밋, `git -C <격리 복제본> rev-parse <base>`), diff_head = T(`git rev-parse <T>`). 40자리 소문자 16진.
3. target = 같은 사본에서 `$PY tools/gates/weakening_diff.py --root <격리 복제본> --base <diff_base> --head <diff_head>` 출력의 `diff_hash`
   (= `$PY tools/gates/merge_gate.py diff-hash --repo <격리 복제본> --base <diff_base> --head <diff_head> skills/analog-gmid-design/assets/tests/contracts/test_dup_kcl_edges.py`).
   출력 `diff_paths`가 이 한 경로가 **아니면** 이 기록으로 V5를 통과할 수 없다(해시가 경로 합집합) -- 다른 경로의 변경에 대한 사용자 승인을 따로 받아 두 원문을 함께 인용하는 기록 하나로 고친다(diff_path 줄을 경로마다 하나).
4. code-author는 test 파일을 바꾸지 않으므로 병합본(head)에서의 이 경로 blob은 T의 blob과 같다 -- auditor가 base..병합본으로 잰 `diff_hash`도 같은 값이어야 한다(다르면 기록을 쓰지 않고 멈춘다).
5. 검증: `$PY tools/gates/merge_gate.py parse-approval .ai/approvals/20261001-b26-p9-signature-update.md` exit 0. 기록은 auditor V5가 보는 head 트리(`weakening_diff.approved_hashes(root, head)`)에 들어 있어야 하고
   병합 규칙 9가 새 master 트리에서 같은 해시를 찾는다. 커밋한 뒤 B26-1 판정 기록 `approvals[]`·`checks.V5.basis`에 이 id·해시를 적고, card 머리 `approval:` 줄은 card 개정 커밋으로 더한다(선례 P10b `d6a9778` → `0f23786`).
선례 양식: `.ai/approvals/20260930-p9-e1-correction.md`(target_kind diff, diff_base/head = rev-parse, target = diff 해시).
-->
