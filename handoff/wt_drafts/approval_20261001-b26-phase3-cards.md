---
id: 20261001-b26-phase3-cards
date: 2026-10-01
target_kind: decision
target: Q-B34-PHASE-CARDS-PHASE3
scope: 결정 Q-B34-PHASE -- spec card 20260930-b34-grammar-explicit·20260930-b26-pre-test-strengthen·20261001-b26-backfill-interdig-final-audit·20260930-b26-rail-accessor-set 네 card의 phase를 3으로(Phase 2 DoD 뒤·Phase 3 M card 전 병합 순서는 그대로), 승인 기록 20260930-b26-before-phase3 ③의 병합 시점 문구('Phase 2 진행 중', card phase 2) 정정 -- 그 기록은 고치지 않는다, design 30 승인·U-03을 기다리지 않는다
---

## 사용자 원문

> phase 3 + 정정 기록 (Recommended)

(질문 2026-10-01 21:10 KST, 답 2026-10-01 21:14 KST(세션 jsonl `63c6146a-ab1d-4035-a169-bae810986922` AskUserQuestion `toolu_01KTtsbRiK7S3cv1coUsAyPw`, 질문 4개 중 [card phase]). 질문 원문(고치지 않고 그대로): "[Q-B34-PHASE] B34·b26pre·backfill·B26-1 네 card는 Phase 2 DoD 뒤에 병합되는데, 머리는 phase: 2이고 A2 기록 ③은 'Phase 2 진행 중'이라 적었습니다. 게이트는 card phase를 현재 Phase와 대조하지 않고, phase 2·3에서 test 결과·strict 집합(둘 다 빈 집합)·N/A 허용이 같습니다. 달라지는 것은 판정 기록 V1의 --gmid-phase= 값, 어느 Phase DoD 목록이 card를 세는지, A2 ③ 문구뿐입니다. 어떻게 둘까요?"
선택지: "phase 3 + 정정 기록 (Recommended)" -- "네 card를 phase: 3으로, 'Phase 3 M card 전' 순서는 유지하고, ③ 문구를 바로잡는 decision 기록 1건을 남깁니다(design 30 승인·U-03을 기다리지 않는다고 명시)." / "Phase 2 DoD 앞으로" -- "네 card를 Phase 2 DoD 앞으로 당겨 phase: 2를 유지합니다. Phase 2 DoD가 늦어지고 DoD N6.3 집계 수치가 늘어납니다.".)

## 범위 설명

덮는 것:
* 네 card의 spec card 머리 `phase: 3` -- B34 `20260930-b34-grammar-explicit`, b26pre `20260930-b26-pre-test-strengthen`, backfill `20261001-b26-backfill-interdig-final-audit`, B26-1 `20260930-b26-rail-accessor-set`.
  네 card의 머리 `approval:` 줄이 이 기록을 가리킨다. 판정 기록 V1 명령의 `--gmid-phase=`는 card `phase`를 따라 `3`이다(`merge_gate.v1_command_check(..., phase=card["phase"])`).
  게이트는 card `phase`를 진행 Phase와 대조하지 않고, phase 2·3에서 test 결과·strict 집합(둘 다 빈 집합)·N/A 허용이 같다(질문 원문의 사실).
* 병합 순서 유지: P10b → Phase 2 DoD → V3 면제 묶기 → V3 범위 정책 → B34 → b26pre → backfill → B26-1 → B33 → Phase 3 M card. 네 card는 **Phase 2 DoD 뒤·Phase 3 M card 전**에 병합한다.
  계획 1001행 "먼저 병합하는 card의 spec card `phase` 값은 병합 시점의 진행 Phase다"와 맞다(Phase 2 DoD PASS 뒤의 진행 Phase는 3). 네 card는 Phase 2 DoD의 N6.3 판정 기록 목록(`^phase: 2$` card)에 들지 않는다.
* 승인 기록 `20260930-b26-before-phase3`(gate `2d58fd8`)의 범위 설명 ③ 두 항목에 적힌 "Phase 2 진행 중에 병합하는 것(card `phase: 2`, DF-35·DF-36 선례)"을 "Phase 2 DoD 뒤·Phase 3 M card 전에 병합(card `phase: 3`)"으로 읽는다는 정정.
  그 기록 파일은 고치지 않는다(승인 기록은 고치지 않고 새 기록으로 바로잡는다). ③의 나머지(B26-1·B34를 Phase 3 모듈 분할보다 먼저 한다는 결정, 덮는 동작 변경, '재검토' 절)는 그대로 유효하다.
* 이 결정은 Phase 3 design(`30-module-split`) 승인과 U-03 답을 기다리지 않는다 -- 네 card는 그 승인 전에도 위 순서대로 착수·병합할 수 있다. Phase 3 승인 질문에서 A2-③ 항목은 이 답으로 닫힌다.

덮지 않는 것:
* 네 card의 계약·oracle·V3 대상·면제(각 card와 그 승인 기록 몫), B40(`20260930-b26-b40-reason-key`), P9 시그니처 test 갱신(`20261001-b26-p9-signature-update`), B26-1 등가 면제(`20261001-b26-v3-equiv-range`).
* Phase 3 card(T0·G1·D0a·D0b·M…)의 phase·순서·착수 조건(Phase 3 design과 그 승인 몫), Phase 2 DoD 판정 기준.
* 판정 표(`plan_tables_hash` 입력) -- 바꾸지 않는다.

## 재검토

네 card 중 하나라도 병합되지 않은 채 Phase 3 M card가 시작되면 `20260930-b26-before-phase3` '재검토' 절이 그대로 적용된다(그 card의 앞당김은 효력을 잃고 편집 범위를 새 모듈 기준으로 다시 잰다).
