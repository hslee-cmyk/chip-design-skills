---
id: 20260918-u38-jsonschema
date: 2026-09-18
target_kind: decision
target: U-38
scope: merge gate(판정 기록 로더)와 로드 게이트의 JSON Schema 검증에 jsonschema 패키지를 쓴다(의존성 추가, WP-20)
---

## 사용자 원문

> U-38은 기본안대로 해

## 범위 설명

덮는 것: `jsonschema` 패키지를 프로젝트 의존성으로 쓰는 것(Phase 0.5 merge gate 로더, 이후 로드 게이트의 스키마 검증).
기본안 원문(계획 N7.2 U-38): 스키마를 손으로 옮긴 검증기를 따로 두면 스키마와 검증기가 두 정본이 된다. `format: date-time`은
형식 검사기가 없으면 강제되지 않으므로 로더가 따로 검사한다.
덮지 않는 것: 패키지 최소 릴리스 나이 정책 변경(WP-20: 낮추지 않는다), 다른 패키지 추가.
