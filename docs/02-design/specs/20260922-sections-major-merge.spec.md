---
id: 20260922-sections-major-merge
phase: 1
evidence_type: red-green
gate_change: no
---

> **[상태 표지 2026-10-29] 실행·병합 완료 기록 -- 현행 규칙·절차 아님.** 판정 기록 `.ai/verification/20260922-sections-major-merge.json`(FAIL 0)이 있고 이 card의 커밋은 master에 병합됐다. 옛 계획 Phase 1 test 분리 card이고 Phase 1은 폐기됐다(계획 N6.1 '옛 Phase 처리' 1행; N3.11 'TS0~TS6 폐기'). 본문의 spec card·interface card·auditor 판정(V1~V10)·DEC-40 승인·R1 절차는 DEC-86으로 폐기했다(계획 N3.12·N4.2, DEC-40 행) -- 현행 완료 조건은 계획 N6.3이다. 본문의 `A`(`skills/analog-gmid-design/assets`) 아래 옛 엔진·test는 `skills/analog-gmid-design/legacy/`로 옮겨졌고(`60727b06`) 새 test 체계(`gmid_engine/tests/`)에서 돌지 않는다. card LT-1(DEC-99)이 `legacy/`를 지운 뒤에는 tag `legacy-final`에만 남는다. 본문은 기록이며 덧대지 않는다(O-169).

## 의도

백로그 B6(사용자 결정 "C9 전에 도구 수정", C12): C1 도구 `tools/migrate/extract_selftest.py`의 `sections`가 design `10-test-separation`
v1.2 §5.1 "연속한 대 표지 `print`는 하나로 합친다"를 어기고, 사이에 표지가 아닌 문장이 있는 대 표지까지 앞 대 표지 섹션에 합친다.
C9(TS2 섹션별 test 분리)의 매핑(M1·M2)이 `sections` 출력을 입력으로 쓰므로 C9 전에 §5.1대로 고친다. 바꾸는 것은 대 표지 병합 조건
하나뿐이다. B5(`extract` 머리글의 절대 경로)는 C9 뒤 추출 도구를 다시 쓰는 곳이 없어 이 card에 넣지 않는다(백로그 유지).

## 관찰 가능한 계약

1. `sections`: 대 표지 `print`가 **바로 앞 최상위 문장도 대 표지 `print`일 때만** 앞 섹션에 합쳐진다. 대 표지 앞 문장이 표지가 아닌 문장이거나 소 표지이면 새 섹션이 시작된다(design §5.1).
2. 그 밖의 `sections` 규칙(소 표지, 머리 P, 범주 P·D·A·B·C, 의존, 필드 목록)과 `extract`·`scan`의 동작·exit code는 바뀌지 않는다.
3. 실측(C2 병합 커밋 6abe0fc의 이관본, 오케스트레이터 사전 측정 -- 판정 증거 아님): 섹션 수가 sizing_recipe 72→77, stick_diagram 128→174, design_report 2→5, topology_library 11→16이 된다.

## 신규 시그니처

| 모듈 | 심볼 | 시그니처 |
|---|---|---|

## 판정 유형 근거

red-green: base 도구로는 '대 표지 → 표지 아닌 문장 → 대 표지' 합성 블록의 두 대 표지가 한 섹션이 되어 test가 AssertionError, 병합본에서 두 섹션이 되어 통과한다.

## oracle 종류와 출처

(a) 구성으로 정답이 정해진 합성 입력: test가 작은 합성 블록을 만들고, 섹션 경계·kind·category 기대값을 design §5.1 문장에서 직접 정한다. 피검 도구 출력으로 기대값을 만들지 않는다. 경우: (i) 연속한 대 표지 둘 → 한 섹션(기존 규칙 유지), (ii) 대 표지·일반 문장·대 표지 → 두 섹션, (iii) 대 표지·소 표지·대 표지 → 세 섹션. (ii)에서 앞 섹션에만 `assert`를 두면 두 섹션의 범주가 A와 D로 갈린다.

## 거부해야 할 입력

해당 없음(분할 규칙 수정). 기존 거부(exit 2·3·4)는 불변(계약 2).

## library 회로 적용 여부

해당 없음(도구).

## 무동작 판정 입력(무발동 값)

대 표지 사이에 다른 문장이 없는 블록 -- 섹션 목록이 base와 같다(계약 1 (i)).

## 재현할 수치

없음.

## 결정 필요 항목

없음(B6 사용자 결정으로 착수).

## 변경 이력

- 2026-10-29 `cards/revise-1029`: 위 상태 표지만 더함 -- 본문 불변, 표지 전 원문 = `git show 052465ed:docs/02-design/specs/20260922-sections-major-merge.spec.md`.
