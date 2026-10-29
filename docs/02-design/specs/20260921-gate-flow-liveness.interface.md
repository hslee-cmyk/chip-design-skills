# interface card: 20260921-gate-flow-liveness

> **[상태 표지 2026-10-29] 실행·병합 완료 기록 -- 현행 규칙·절차 아님.** 판정 기록 `.ai/verification/20260921-gate-flow-liveness.json`(FAIL 0)이 있고 이 card의 커밋은 master에 병합됐다. 옛 계획 Phase 0.5(역할 분리 인프라) card다. 역할 분리 gate·auditor는 DEC-86으로 꺼졌다(계획 N6.1 '옛 Phase 처리' 0.5행; N3.12 역할 분리·N4.2 auditor V1~V10·N4.3 게이트 거부 증명은 폐기 절). 본문의 게이트 동작(EL1~EL4·V1~V10)·§13.4 재설치·승인(DEC-40·R1) 문장은 현행 절차가 아니다 -- 현행 완료 조건은 계획 N6.3(가벼운 절차)이다. `tools/gates/**`·`hooks/role_*`·`.githooks/`에 남은 파일은 꺼진 잔여물이다(DEC-86). 본문의 `A`(`skills/analog-gmid-design/assets`) 아래 옛 엔진·test는 `skills/analog-gmid-design/legacy/`로 옮겨졌고(`60727b06`) 새 test 체계(`gmid_engine/tests/`)에서 돌지 않는다. card LT-1(DEC-99)이 `legacy/`를 지운 뒤에는 tag `legacy-final`에만 남는다. 본문은 기록이며 덧대지 않는다(O-169).

생성: `tools/gates/interface_card.py`(05-role-separation §11.1). 본문 코드는 넣지 않는다(DEC-38).

## 관찰 가능한 계약

| 모듈 | 심볼 | 시그니처 |
|---|---|---|

## 신규 시그니처

| 모듈 | 심볼 | 시그니처 |
|---|---|---|

## 변경 이력

- 2026-10-29 `cards/revise-1029`: 위 상태 표지만 더함 -- 본문 불변, 표지 전 원문 = `git show 052465ed:docs/02-design/specs/20260921-gate-flow-liveness.interface.md`.
