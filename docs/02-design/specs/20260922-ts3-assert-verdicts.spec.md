---
id: 20260922-ts3-assert-verdicts
phase: 1
evidence_type: test-only
gate_change: no
approval: 20260922-10-test-separation-design
---

> **[상태 표지 2026-10-29] 실행·병합 완료 기록 -- 현행 규칙·절차 아님.** 판정 기록 `.ai/verification/20260922-ts3-assert-verdicts.json`(FAIL 0)이 있고 이 card의 커밋은 master에 병합됐다. 옛 계획 Phase 1 test 분리 card이고 Phase 1은 폐기됐다(계획 N6.1 '옛 Phase 처리' 1행; N3.11 'TS0~TS6 폐기'). 본문의 spec card·interface card·auditor 판정(V1~V10)·DEC-40 승인·R1 절차는 DEC-86으로 폐기했다(계획 N3.12·N4.2, DEC-40 행) -- 현행 완료 조건은 계획 N6.3이다. 본문의 `A`(`skills/analog-gmid-design/assets`) 아래 옛 엔진·test는 `skills/analog-gmid-design/legacy/`로 옮겨졌고(`60727b06`) 새 test 체계(`gmid_engine/tests/`)에서 돌지 않는다. card LT-1(DEC-99)이 `legacy/`를 지운 뒤에는 tag `legacy-final`에만 남는다. 본문은 기록이며 덧대지 않는다(O-169).

## 의도

TS3(계획 N3.11): 이관본 4개(`A/tests/legacy/selftest_{sizing_recipe,stick_diagram,design_report,topology_library}.py`)에서
print·logging 인자의 PASS/FAIL 판정을 `assert`로 바꾸거나 지우고, 판정 없는 데모 섹션 18개를 지운다(U-41 확정: 모두 삭제).
판정기를 contract test로 둔다. 정본 명세는 design `10-test-separation` v1.2 §6.3·§7(판정식 T)·§9 C4 행. A = `skills/analog-gmid-design/assets`.
문자열 상수·섹션 삭제는 V5 발견이라 DEC-40 승인이 필요하고, 05 §12 'V5 승인 운반'(R1)으로 2차 시도에 넣는다.

## 관찰 가능한 계약

1. design §6.3 표의 네 경우대로 변환한다: (i) 섹션 문장이 기대 쪽을 적은 조건식 토큰 → 기대 쪽 조건의 `assert`(메시지 = 원래 출력 문자열), print 삭제 (ii) 기대가 적히지 않은 데이터 표시 → print 삭제, assert 없음 (iii) 조건 없는 PASS/FAIL 문구 → print 삭제 (iv) 범주 C이고 뒤 섹션이 읽는 이름이 없는 섹션(데모 18개, design §6.3 표 -- 착수 시 C1 `sections`로 다시 뽑아 대조) → 섹션 삭제, 뒤 섹션이 읽는 이름을 만드는 C 섹션은 그 문장만 남김.
2. 변경 뒤 `A/tests/**/*.py`(`probes/**`·`tools/**` 제외)의 판정식 T(design §7) = 0. 새 contract test `A/tests/contracts/test_ts3_no_print_verdicts.py`가 이를 단언하고, 합성 소스 문자열(토큰 1개)에서 판정기가 실제로 T=1을 내는 것도 단언한다.
3. 변경 뒤 이관본 4개가 모두 exit 0(`tests/legacy/test_legacy_selftests.py` 4 PASS).
4. 이관본별 (새 `assert` 수) = (경우 (i)로 바꾼 print 수).
5. base 출력에서 기대와 반대인 판정 줄이 있으면 변환하지 말고 멈춘다(design §8 F4).

## 신규 시그니처

| 모듈 | 심볼 | 시그니처 |
|---|---|---|

## 판정 유형 근거

test-only(계획 N3.12.3 개정 P5): 대상 코드 불변.

## oracle 종류와 출처

(d) 섹션이 적은 기대(self-test 작성자가 적은 의도, design §6.3). 현재 출력에서 기대값을 가져오지 않는다(경우 (ii)는 assert를 만들지 않는다).

## 거부해야 할 입력

contract test의 합성 소스(토큰 1개) → 판정기가 T ≥ 1(거부). base 트리의 이관본 → T = 354(red 기록, V2 basis).

## library 회로 적용 여부

해당 없음(test 변환).

## 무동작 판정 입력(무발동 값)

해당 없음.

## 재현할 수치

없음.

## 결정 필요 항목

문자열·섹션 삭제의 DEC-40 승인(V5) -- 1차 시도에서 auditor가 발견 경로와 diff 해시를 내면 사용자에게 보여 받는다(R1). 삭제 목록은 U-41 확정.

## 변경 이력

- 2026-10-29 `cards/revise-1029`: 위 상태 표지만 더함 -- 본문 불변, 표지 전 원문 = `git show 052465ed:docs/02-design/specs/20260922-ts3-assert-verdicts.spec.md`.
