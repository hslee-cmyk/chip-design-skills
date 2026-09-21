---
id: 20260921-bootstrap-plan-tables
date: 2026-09-21
target_kind: plan_tables
target: cec77b63a203688f444fb96bc853d909011a6404597f9deac8b8e33a51179f96
scope: 부트스트랩 ③ 최초 판정 표 승인 -- 현재 계획서의 판정 표(N4.1 담당 Phase·강제 test, N4.2 도입, N6.1 Phase, N3.12.2 쓰기 경로표)
---

## 사용자 원문

> 네 가지 다 승인할게

## 범위 설명

덮는 것: 계획서(마지막 변경 커밋 835938b)를 `tools/gates/merge_gate.py plan-tables-hash`(05 §15.2, 00-common §8.2 `plan_tables`)로 파싱한 값의 해시. 이 값이 EL3·EL4가 이후 판정 표 변경을 대조하는 기준이다. F4 사용자 행(승인 기록 `20260921-f4-user-approval-row`)도 이 표에 포함된다.

덮지 않는 것: 판정 표가 아닌 계획서 문장. 이후 판정 표 변경은 각자 `plan_tables` 승인 기록이 필요하다.
