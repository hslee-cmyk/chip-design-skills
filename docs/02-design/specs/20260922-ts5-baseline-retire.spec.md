---
id: 20260922-ts5-baseline-retire
phase: 1
evidence_type: test-only
gate_change: no
approval: 20260922-10-test-separation-design
---

> **[상태 표지 2026-10-29] 실행·병합 완료 기록 -- 현행 규칙·절차 아님.** 판정 기록 `.ai/verification/20260922-ts5-baseline-retire.json`(FAIL 0)이 있고 이 card의 커밋은 master에 병합됐다. 옛 계획 Phase 1 test 분리 card이고 Phase 1은 폐기됐다(계획 N6.1 '옛 Phase 처리' 1행; N3.11 'TS0~TS6 폐기'). 본문의 spec card·interface card·auditor 판정(V1~V10)·DEC-40 승인·R1 절차는 DEC-86으로 폐기했다(계획 N3.12·N4.2, DEC-40 행) -- 현행 완료 조건은 계획 N6.3이다. 본문의 `A`(`skills/analog-gmid-design/assets`) 아래 옛 엔진·test는 `skills/analog-gmid-design/legacy/`로 옮겨졌고(`60727b06`) 새 test 체계(`gmid_engine/tests/`)에서 돌지 않는다. card LT-1(DEC-99)이 `legacy/`를 지운 뒤에는 tag `legacy-final`에만 남는다. 본문은 기록이며 덧대지 않는다(O-169).

## 의도

TS5(계획 N3.11): C4(TS3)로 self-test stdout이 바뀌어 커밋된 stdout 기준선은 더 이상 대조 대상이 아니다. `A/tests/baseline/`(README.md,
`sizing_recipe.selftest.baseline.log`, `stick_diagram.selftest.baseline.log`)을 지우고 `A/tests/README.md`를 pytest 실행법으로 쓴다.
정본 명세는 design `10-test-separation` v1.2 §6.4·§10 D5·§9 C5 행. A = `skills/analog-gmid-design/assets`. 비-`.py` test 파일 삭제·추가는
V5 발견이라 DEC-40 승인이 필요하고 R1(05 §12 'V5 승인 운반')로 2차 시도에 넣는다. 이 삭제에는 sizing 기준선의 45줄 드리프트(design §3)가 함께 들어간다.
병합 뒤 사용자가 `.gitignore`의 기준선 예외 3줄을 지우고(U-43, `Role: user` + `staged_diff`), 오케스트레이터가 references의 실행 안내 두 곳을 `tests/README.md` 인용으로 바꾼다.

## 관찰 가능한 계약

1. `A/tests/baseline/` 디렉터리의 세 파일이 없다.
2. `A/tests/README.md`가 있고 design §6.4의 세 내용을 담는다: 실행법(`$PY -P -m pytest -c tools/gates/pytest_gate.ini --rootdir=. --confcutdir=. skills/analog-gmid-design/assets/tests`, C6 뒤 `--gmid-phase=<Phase>`), 판정 규칙(assert만, print 판정 금지, xfail은 conftest가 계획서 N4.1로 만든다), 디렉터리 표(계획 N3.11 트리).
3. design §10 D5 명령의 출력이 0줄(기준선 참조 0).
4. 전체 test가 base와 변경 뒤 모두 PASS(기준선 파일은 어떤 test도 읽지 않는다).

## 신규 시그니처

| 모듈 | 심볼 | 시그니처 |
|---|---|---|

## 판정 유형 근거

test-only(계획 N3.12.3 개정 P5): 대상 코드 불변, 삭제·문서.

## oracle 종류와 출처

해당 없음(삭제·문서 -- design §9 C5 행 '-- (삭제·문서)').

## 거부해야 할 입력

해당 없음.

## library 회로 적용 여부

해당 없음.

## 무동작 판정 입력(무발동 값)

해당 없음.

## 재현할 수치

없음.

## 결정 필요 항목

기준선 삭제·README 추가의 DEC-40 승인(V5, R1). 승인 요청에 sizing 기준선 45줄 드리프트가 삭제분에 포함됨을 명시한다.

## 변경 이력

- 2026-10-29 `cards/revise-1029`: 위 상태 표지만 더함 -- 본문 불변, 표지 전 원문 = `git show 052465ed:docs/02-design/specs/20260922-ts5-baseline-retire.spec.md`.
