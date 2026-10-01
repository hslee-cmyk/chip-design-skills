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

## 작성 전 실측

(오케스트레이터가 커밋 전에 채운다 -- 확인마다 실행한 명령과 결과 한 줄. 2026-09-30 재시도 5/9가 전부 이 확인 누락이었다.)

1. 사실 문장 재측정: 이 card의 줄 번호·개수·"X는 Y를 읽는다"·파일 내용 주장을 코드·파일로 다시 쟀다(설계서·레지스트리 문장을 옮기지 않았다).
2. 이름 충돌: 새 파일·모듈 이름이 기존 test의 glob 패턴(`grep -rn "glob(" A/tests/`)과 겹치지 않는다.
3. 원칙의 계약화: 의도 절에 적은 원칙(예: 정본 topology 무관)이 관찰 가능한 계약에 **전 범위로** 적혀 있다.
4. 쓰기 경로: 각 산출물을 누가 쓰는지(test-author는 엔진 소스를 읽지 못한다) N3.12.2 쓰기 경로표와 맞다.
5. 계획서 소비자: 지우거나 옮기는 이름을 `docs/01-plan`·`docs/02-design`에서 grep했다.
6. 미배선: 새로 만들거나 되살리는 def가 운영 경로에서 불리지 않으면 V7 면제 승인(`target_kind: decision`)을 이 card 전에 받았다.
7. 기존 계약 test: 바뀌는 이름·파일을 참조하는 기존 계약 test(`A/tests/contracts/`)를 grep했고, 조정이 필요하면 V5 승인 경로를 적었다.
8. V3 규모: 초안 단계에서 `tools/gates/mutate_changed.py`의 `changed_defs`·`mutants`·`inventory`를 시뮬레이션 head에 돌려 대상 def 수·변이 수·인벤토리 test 수를 적었다(그 시점 gate에서 유효한 V3 대상 규칙으로). 바뀌는 def는 작게 유지했다 -- 인자를 넘기려고 호출부 def를 고치면 그 def도 V3 대상이 된다.
9. 승인 줄: 동작을 바꾸거나 다른 Phase의 일을 당겨오는 card는 그것을 덮는 사용자 결정 승인 기록(`target_kind: decision`)이 `approval` 줄에 있다. design 승인은 '동작이 바뀌는 수정'을 범위에서 뺀 것이 있어 덮지 않는다 -- 기록의 범위 설명에 이 card id와 바뀌는 동작이 적혀 있는지 원문으로 확인했다.
10. 범위 계약: '바뀐 파일·변경 0' 같은 범위·diff 계약은 '이 card `Change-Id` 커밋들의 diff'로 한정해 적었다(기준 커밋과 판정 대상 사이에 다른 card 커밋이 끼면 그 diff까지 걸린다).
11. test 이름·모양: 새 test·보조 함수 이름은 card 접두(예: `_b26_`)로 기존 test와 겹치지 않고, 피검 함수는 test 본문에서 직접 부른다(`parametrize` 이름 문자열·모듈 상수 + `getattr`은 V3 인벤토리 간선으로 잡히지 않는다).
12. 같음 판정: `__eq__`가 없는 객체나 프로세스마다 순서가 다른 `set`을 `==`로 비교하는 계약이 없다 -- 비교할 필드와 정렬·튜플화 규칙(정규화)을 계약에 적었다.
13. red 모양: 각 계약의 base red가 허용 예외 타입(00-common §8.1)이다. `try/except Exception: pytest.fail`로 다른 예외를 `Failed`로 바꾸지 않고, 새 키워드 인자 직접 호출의 base `TypeError`는 red로 세지 않는다(red는 시그니처가 안 바뀌는 진입점이 맡는다).

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
