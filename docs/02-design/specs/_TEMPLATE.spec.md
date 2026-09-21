---
id: YYYYMMDD-<slug>
phase: <계획서 N6.1에서 읽은 Phase 순서의 원소>
evidence_type: red-green
gate_change: no
activated_ic_case: <IC:case>
activated_ic_case_rename: <옛 IC:case> -> <새 IC:case>
noop_activation_id: <ID>
approval: <승인 기록 id>
---
## 의도

## 관찰 가능한 계약

## 신규 시그니처

| 모듈 | 심볼 | 시그니처 |
|---|---|---|
| `<모듈 점 표기>` | `<심볼 또는 * (신규 모듈 전체)>` | `<def 줄>` |

## 판정 유형 근거

## oracle 종류와 출처

## 거부해야 할 입력

## library 회로 적용 여부

## 무동작 판정 입력(무발동 값)

## 재현할 수치

## 결정 필요 항목

<!--
양식의 정본은 docs/02-design/features/gain-budget-gmid-sizing.05-role-separation.design.md §11.2이고 필드 목록의 정본은
계획서 N3.12.3이다. 머리 블록 규칙(게이트가 읽는다, tools/gates/role_paths.py parse_spec_card):
  * 한 줄에 `key: value` 하나. 모르는 키는 거부한다. 빈 줄·주석 금지.
  * 한 번: id, phase, evidence_type(red-green | equivalence | test-only), gate_change(yes | no).
  * 반복 가능(0개 이상): activated_ic_case, activated_ic_case_rename(`<옛> -> <새>`), noop_activation_id, approval.
    쓰지 않는 반복 키는 줄을 지운다.
본문 '신규 시그니처'의 (모듈, 심볼) 표는 interface card로 옮겨지고 red 수집 플러그인의 신규 심볼 판정 입력이다
(00-common §8.1). 표 머리는 그대로 둔다.
dispute가 있었을 때만 마지막에 `## dispute 기록` 절(원문 인용 + blob id, §12 재시도)을 더한다.
이 파일은 이름이 `_`로 시작해 게이트 파서 대상에서 빠진다.
-->
