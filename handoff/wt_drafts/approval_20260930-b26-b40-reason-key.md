---
id: 20260930-b26-b40-reason-key
date: 2026-10-01
target_kind: decision
target: U4-B40-UNAVAILABLE-REASON-KEY
scope: 결정 U4 -- spec card 20260930-b26-rail-accessor-set(B26-1)이 propose_device_roles_gap_fill의 refined is None 분기 반환 dict에서 unavailable_reason 키만 지우는 것(도달 가능한 분기의 관찰 가능한 반환값 변경, 백로그 B40) -- 승인 기록 20260930-b26-before-phase3 ③ B26-1 항목의 보충, 분기와 나머지 세 키는 그대로
---

## 사용자 원문

> 추가 승인 1건 (Recommended)

(질문 2026-10-01 21:10 KST, 답 2026-10-01 21:14 KST(세션 jsonl `63c6146a-ab1d-4035-a169-bae810986922` AskUserQuestion `toolu_01KTtsbRiK7S3cv1coUsAyPw`, 질문 4개 중 [U4 B40]). 질문 원문(고치지 않고 그대로): "[U4] A2 승인 기록 ③의 B26-1 항목은 'B34에서 인계받은 도달 불가 분기 삭제'만 덮습니다. B40은 도달 가능한 분기의 반환값 변경입니다: analog-grammar가 있어도 gate 소자 없는 입력이면 propose_device_roles_gap_fill이 틀린 사유의 unavailable_reason 키를 돌려주는데, B26-1이 이 키만 지워 3키 dict를 돌려줍니다(소비처 0곳, git grep). A2 승인에 B40을 더해도 될까요?"
선택지: "추가 승인 1건 (Recommended)" -- "짧은 decision 승인 기록 20260930-b26-b40-reason-key로 이 키 삭제만 덮습니다(분기와 나머지 세 키는 그대로)." / "B40 빼고 백로그" -- "B40을 B26-1에서 빼고 B39와 함께 백로그로 둡니다. 틀린 사유는 남습니다.".)

## 범위 설명

덮는 것: B26-1 card 계약 14 -- analog-grammar가 있어도 gate 소자 없는 입력이면 `refine_differential_and_mirror_relations`가 `None`을 돌려주고, 그때 `propose_device_roles_gap_fill`이
`refined is None` 분기에서 돌려주는 dict에서 `unavailable_reason` 키("analog-grammar를 import할 수 없어…" -- 이 입력에서는 틀린 사유)를 지운다. 반환은 키가 정확히 셋인 dict
`{"matching_pairs_proposals": [], "device_roles_proposals": {}, "review_needed": []}`가 된다. 소비처 0곳(git grep -- B26-1 card B40 행). B26-1 card의 머리 `approval:` 줄이 이 기록을 가리킨다.
덮지 않는 것: `refined is None` 분기 자체(남긴다), 나머지 세 키의 값, `refine_differential_and_mirror_relations`의 `None` 반환(B34 계약 5 그대로), 백로그 B39(사유 문구 일반),
B34에서 인계받은 도달 불가 분기 삭제(이미 `20260930-b26-before-phase3` ③이 덮음), V3·V7 면제 일체. 이 기록의 `target`은 결정 이름이며 def id·변이 id가 아니다.
