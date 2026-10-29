# interface card: 20260923-probe-relocate

> **[상태 표지 2026-10-29] 실행·병합 완료 기록 -- 현행 규칙·절차 아님.** 판정 기록 `.ai/verification/20260923-probe-relocate.json`(FAIL 0)이 있고 이 card의 커밋은 master에 병합됐다. 옛 계획 Phase 2(죽은 코드·DUP 정리) card이고 Phase 2는 폐기됐다(계획 N6.1 '옛 Phase 처리' 2행 -- 새 엔진은 모듈 지도 N3.10으로 처음부터 개념당 정본 하나). 본문의 spec card·interface card·auditor 판정(V1~V10)·DEC-40 승인·R1 절차는 DEC-86으로 폐기했다(계획 N3.12·N4.2, DEC-40 행) -- 현행 완료 조건은 계획 N6.3이다. 본문의 `A`(`skills/analog-gmid-design/assets`) 아래 옛 엔진·test는 `skills/analog-gmid-design/legacy/`로 옮겨졌고(`60727b06`) 새 test 체계(`gmid_engine/tests/`)에서 돌지 않는다. card LT-1(DEC-99)이 `legacy/`를 지운 뒤에는 tag `legacy-final`에만 남는다. 이 card가 만들거나 옮긴 파일 가운데 `legacy/tests/probes/`로 옮긴 probe 32개 중 30개·`legacy/tests/tools/derive_achievable_bounds.py`·계약 test `legacy/tests/contracts/test_ts6_probe_relocate.py`는 O-180(LUT는 v2 r2 묶음만 남기고 sample LUT를 읽는 legacy test·probe도 지움)의 삭제 대상이다 -- LUT 정리(브랜치 `data/lut-v2-only`) 병합 전에는 `legacy/` 아래 있고, 병합 뒤에는 git 이력에만 있다(LUT 정리와 LT-1 가운데 먼저 병합되는 쪽에서 작업 트리에서 지워진다). 본문은 기록이며 덧대지 않는다(O-169).

생성: `tools/gates/interface_card.py`(05-role-separation §11.1). 본문 코드는 넣지 않는다(DEC-38).

## 관찰 가능한 계약

| 모듈 | 심볼 | 시그니처 |
|---|---|---|

## 신규 시그니처

| 모듈 | 심볼 | 시그니처 |
|---|---|---|

## 변경 이력

- 2026-10-29 `cards/revise-1029`: 위 상태 표지만 더함 -- 본문 불변, 표지 전 원문 = `git show 052465ed:docs/02-design/specs/20260923-probe-relocate.interface.md`.
