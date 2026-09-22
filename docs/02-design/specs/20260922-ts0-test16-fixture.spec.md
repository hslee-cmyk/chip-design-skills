---
id: 20260922-ts0-test16-fixture
phase: 1
evidence_type: test-only
gate_change: no
approval: 20260921-u01-test16-intent
---
## 의도

TS0(계획 N3.11, U-01 확정 `20260921-u01-test16-intent`): stick_diagram Test 16 (b)의 FAIL은 test fixture 누락이다. 이관본
`A/tests/legacy/selftest_stick_diagram.py` Test 16 (b)의 `dispositions`에 M4/M5 차동쌍 후보 키 판정을 한 항목 더해 (b)를 PASS로
만들고, 기준선 `A/tests/baseline/stick_diagram.selftest.baseline.log`의 (b) 줄을 갱신한다. 대상 코드는 바꾸지 않는다.
정본 명세는 design `10-test-separation` v1.2 §6.2·§9 C3 행. 기준선 `.log` 변경은 V5 대상이라 DEC-40 승인이 필요하고, 그 승인은
05 §12 'V5 승인 운반'(R1) 절차로 2차 시도의 head 트리에 넣는다. A = `skills/analog-gmid-design/assets`. 완료 시 DF-17 해소.

## 관찰 가능한 계약

1. 이관본 stick Test 16 (b)의 `dispositions`에 `("diff_pair", "pmos", "tail"): ("real_match", <사유 문자열>)` 한 항목만 더한다. (a)와 그 밖의 줄은 그대로.
2. 변경 뒤 이관본 stick 실행에서 Test 16 (b) 블록의 판정 줄이 모두 `[PASS]`이고 `FAIL(예상과 다름` 줄이 0이다(base에서는 1).
3. 기준선 `.log`는 Test 16 (b)가 내는 줄(`(b) ...` 머리 다음 줄부터 `전체 결과` 줄까지)만 변경 뒤 실행의 같은 줄로 바뀐다. 나머지 줄(경로 줄, `sizing_recipe` 기준선 포함)은 그대로.
4. `A/tests/legacy/test_legacy_selftests.py` 4케이스가 base와 변경 뒤 모두 PASS.

## 신규 시그니처

| 모듈 | 심볼 | 시그니처 |
|---|---|---|

## 판정 유형 근거

test-only(계획 N3.12.3 개정 P5, N3.11 TS0 개정 P2): 대상 코드가 바뀌지 않아 code 커밋이 없다.

## oracle 종류와 출처

(d) 사용자 승인(U-01 확정): M4/M5가 소스 공유·게이트 상이의 차동쌍이라 후보 탐색기의 `diff_pair` 후보는 설계대로이고, test가 그 판정을 빠뜨렸다.

## 거부해야 할 입력

해당 없음(판정 추가). (a)는 계속 `OK(의도대로 FAIL)`이어야 한다 -- 대소문자 불일치·미판정 후보를 계속 잡는다.

## library 회로 적용 여부

해당 없음(합성 회로 test).

## 무동작 판정 입력(무발동 값)

해당 없음.

## 재현할 수치

없음.

## 결정 필요 항목

기준선 `.log` 변경의 DEC-40 승인(V5) -- 1차 시도에서 auditor가 발견 경로와 diff 해시를 내면 사용자에게 diff를 보여 받는다(R1).
