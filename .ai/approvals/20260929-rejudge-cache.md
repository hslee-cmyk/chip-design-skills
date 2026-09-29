---
id: 20260929-rejudge-cache
date: 2026-09-29
target_kind: diff
target: 3e66546c733c7e7f77877783c0f3531231d579ad8e1b6992f24d9c53bc6f6d37
diff_base: f16a271ceb6ef72c906fef89ea2fecb5d08a6bde
diff_head: f8509d30a1efdfe9e4a446cf9d0fc9b72a88900e
diff_path: docs/02-design/features/gain-budget-gmid-sizing.05-role-separation.design.md
diff_path: docs/02-design/specs/20260929-rejudge-cache.spec.md
scope: 게이트 변경 spec card 20260929-rejudge-cache(행 3(나) 재판정 통과 캐시)와 design 05 §3.3 행 3(나)·§13.2 공격 22(f)·§13.5 N-06 재분류 개정 승인
---

## 사용자 원문

> 승인

(질문: f8509d3(설계 05 §3.3 행 3(나)·공격 22(f)·§13.5 개정 + spec card 20260929-rejudge-cache) 승인 -- 선택지 '승인'.
앞서 사용자: "N-06공격을 방어할 필요가 정말 있어?" → 위협 범위 N3.12.0 기준 분석 뒤 "응, 캐시로 진행해")

## 범위 설명

덮는 것: spec card `20260929-rejudge-cache` 전체, design 05 §3.3 행 3(나)의 '생략 캐시를 두지 않는다' 규정을 '재판정 통과 캐시(마지막 줄은
항상 재판정)'로 바꾸는 개정, §13.2 공격 22 (f) 기대를 알려진 한계(기록 케이스)로 바꾸는 개정, §13.5에 review31 N-06 재분류 행 추가 --
드러나게 하는 범위를 줄이는 기준 약화다. 반영 뒤 §13.4 재설치.
덮지 않는 것: 행 3(가) 사슬 대조·행 1·2·4·5·6, `merge_gate.py receive` 판정 자체, 공격 22 (a)~(e)의 기대.
