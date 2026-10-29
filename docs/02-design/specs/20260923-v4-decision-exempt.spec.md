---
id: 20260923-v4-decision-exempt
phase: 1
evidence_type: red-green
gate_change: yes
approval: 20260923-v4-decision-exempt
---

> **[상태 표지 2026-10-29] 실행·병합 완료 기록 -- 현행 규칙·절차 아님.** 판정 기록 `.ai/verification/20260923-v4-decision-exempt.json`(FAIL 0)이 있고 이 card의 커밋은 master에 병합됐다. 옛 계획 Phase 1 card이고 다루는 대상은 auditor 판정 도구(N4.2 V1~V10)다. 역할 분리 gate·auditor는 DEC-86으로 꺼졌다(계획 N6.1 '옛 Phase 처리' 0.5·1행; N3.12·N4.2·N4.3은 폐기 절). 본문의 게이트 동작(EL1~EL4·V1~V10)·§13.4 재설치·승인(DEC-40·R1) 문장은 현행 절차가 아니다 -- 현행 완료 조건은 계획 N6.3(가벼운 절차)이다. `tools/gates/**`·`hooks/role_*`·`.githooks/`에 남은 파일은 꺼진 잔여물이다(DEC-86). 본문은 기록이며 덧대지 않는다(O-169).

## 의도

C9(TS2)에서 이관본 판정 두 개가 V4 규칙 (1)에 걸린다: sizing S052(한 번 부른 결과에서 Ma·Mb의 L이 같은지 보는 불변식)와
S054(같은 입력으로 두 번 부른 결과가 같은지 보는 재현성). 둘 다 이관본 판정을 그대로 옮긴 정당한 oracle인데, 규칙 (1)의
DESIGN-GAP 판정식("판정 양쪽에 같은 피검 호출이 지역 대입 인라인 뒤에도 남으면 FAIL", `test_lint.py` 머리)은 이것을 가른다.
V3(`mutate_changed.py`)에는 `target_kind: decision` 승인 기록으로 등가 변이를 면제하는 길이 있으나 V4에는 없다. 같은 방식을
V4 규칙 (1)에만 연다(사용자 결정 "V4 면제 게이트 변경"). **막는 규칙을 넓히지 않는다**: 판정식은 그대로이고, 면제는 승인 기록에
적힌 test id에만 적용된다. 정본 규칙 인용은 계획 N4.2 V4, `05-role-separation` §10 V4, V3 면제 선례는 `05` §9 V3 행.

## 관찰 가능한 계약

1. `tools/gates/test_lint.py`가 `--head <커밋>`을 받은 실행에서, 그 커밋 트리의 승인 기록(`.ai/approvals/**.md`, 이름이 `_`로 시작하지 않는 것) 중 `target_kind: decision`인 것의 `target` 목록을 읽는다(V3와 같은 읽기 -- `reachability._approved_ids`를 그대로 쓴다).
2. 규칙 (1) 발견의 test id(`<저장소 상대 경로, 슬래시>::<test 함수 이름>`)가 그 목록에 있으면 그 발견의 `output`이 `FAIL`이 아니라 `exempt`가 되고 판정(exit code)에 들어가지 않는다. 출력 JSON에는 남는다(auditor가 판정 기록에 적는다).
3. 규칙 (2)·(3)·(4)·(5)와 다른 발견은 면제되지 않는다. 승인 기록이 없거나(`--head` 없이 실행 포함) 목록에 그 test id가 없으면 판정은 지금과 같다(오거부·오통과 0).
4. redteam 공격 06(`v4-expected-from-subject`)은 그대로 적발된다(승인 기록이 없으므로 FAIL). 다른 test id를 적은 승인 기록이 있어도 적발된다.

## 신규 시그니처

| 모듈 | 심볼 | 시그니처 |
|---|---|---|

## 판정 유형 근거

red-green: base 도구에서는 승인 기록이 있어도 규칙 (1)이 FAIL이라 합성 케이스가 FAIL로 끝나고(red), 병합본에서는 그 test id만 `exempt`가 되어 PASS한다. 면제 없는 케이스는 양쪽 모두 FAIL이다.

## oracle 종류와 출처

(a) 구성으로 정답이 정해진 합성 저장소(redteam 케이스, `rt.py` 선례대로 실행 중 임시 디렉터리에 만든다): (1) 규칙 (1)에 걸리는 합성 test + 그 test id를 적은 `target_kind: decision` 승인 기록 → 병합본에서 PASS, `output: exempt` 1건 (2) 같은 합성 test + 승인 기록 없음 → FAIL (3) 같은 합성 test + 다른 test id를 적은 승인 기록 → FAIL (4) 규칙 (3)·(4)에 걸리는 합성 test + 그 test id를 적은 승인 기록 → 여전히 FAIL(면제는 (1)에만).

## 거부해야 할 입력

(2)(3)(4)의 합성 케이스. 공격 06 재생(계약 4).

## library 회로 적용 여부

해당 없음(게이트 도구).

## 무동작 판정 입력(무발동 값)

`target_kind: decision` 승인 기록이 하나도 없는 트리, `--head` 없는 실행 -- 판정이 base와 같다(계약 3).

## 재현할 수치

없음.

## 결정 필요 항목

없음(게이트 변경 승인 기록 `20260923-v4-decision-exempt`, 사용자 결정 원문은 그 기록에).

## 변경 이력

- 2026-10-29 `cards/revise-1029`: 위 상태 표지만 더함 -- 본문 불변, 표지 전 원문 = `git show 052465ed:docs/02-design/specs/20260923-v4-decision-exempt.spec.md`.
