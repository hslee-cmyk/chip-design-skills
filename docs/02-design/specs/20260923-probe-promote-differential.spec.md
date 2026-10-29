---
id: 20260923-probe-promote-differential
phase: 2
evidence_type: test-only
gate_change: no
approval: 20260923-20-dead-code-dup-design
---

> **[상태 표지 2026-10-29] 실행·병합 완료 기록 -- 현행 규칙·절차 아님.** 판정 기록 `.ai/verification/20260923-probe-promote-differential.json`(FAIL 0)이 있고 이 card의 커밋은 master에 병합됐다. 옛 계획 Phase 2(죽은 코드·DUP 정리) card이고 Phase 2는 폐기됐다(계획 N6.1 '옛 Phase 처리' 2행 -- 새 엔진은 모듈 지도 N3.10으로 처음부터 개념당 정본 하나). 본문의 spec card·interface card·auditor 판정(V1~V10)·DEC-40 승인·R1 절차는 DEC-86으로 폐기했다(계획 N3.12·N4.2, DEC-40 행) -- 현행 완료 조건은 계획 N6.3이다. 본문의 `A`(`skills/analog-gmid-design/assets`) 아래 옛 엔진·test는 `skills/analog-gmid-design/legacy/`로 옮겨졌고(`60727b06`) 새 test 체계(`gmid_engine/tests/`)에서 돌지 않는다. card LT-1(DEC-99)이 `legacy/`를 지운 뒤에는 tag `legacy-final`에만 남는다. 이 card가 만들거나 옮긴 파일 가운데 `legacy/tests/unit/test_probe_gm_id_monotonicity.py`·`legacy/tests/unit/test_probe_prevention_wiring.py`는 O-180(LUT는 v2 r2 묶음만 남기고 sample LUT를 읽는 legacy test·probe도 지움)의 삭제 대상이다 -- LUT 정리(브랜치 `data/lut-v2-only`) 병합 전에는 `legacy/` 아래 있고, 병합 뒤에는 git 이력에만 있다(LT-1보다 먼저 지워짐). 본문의 'C13이 연 `target_kind: decision` 면제'(V4)는 N4.2 폐기로 현행 절차가 아니다. 본문은 기록이며 덧대지 않는다(O-169).

## 의도

TS6(계획 N3.11), design `20-dead-code-dup` v1.2 §5.1: 승격 후보 중 **엔진과 독립 재구현을 나란히 비교하는 대조형** 2개를 pytest test로
바꾼다 -- `probe_gm_id_monotonicity`(엔진의 VGS 선택 `_solve_vgs`와 별개로 강반전 가지 해를 세워 비교), `probe_prevention_wiring`
(`gate == drain`이라는 물리 정의로 diode를 판정해, role 라벨로 갈리는 엔진 분기가 물리를 보는지 확인). 재구현은 **oracle이므로 정본 호출로
바꾸지 않는다**(design §5.1). A = `skills/analog-gmid-design/assets`. code 커밋이 없다(test-only).

## 관찰 가능한 계약

1. `A/tests/unit/test_probe_gm_id_monotonicity.py`와 `A/tests/unit/test_probe_prevention_wiring.py`가 생기고 원본 probe 2개가 없어진다.
   이름은 P3a(`20260923-probe-promote-clean` 계약 1)의 승격 규칙 `unit/test_<probe 파일 이름>`을 따른다 -- P1·P3a 계약 test
   (`contracts/test_ts6_dead_probes.py`, `contracts/test_ts6_probe_relocate.py`)가 이 규칙으로 승격본을 센다(2026-09-29 개정, 1차 시도에서
   `test_gm_id_monotonicity.py` 이름으로 두 계약 test가 실패).
2. **재구현을 그대로 옮긴다**: 엔진 함수를 부르는 쪽과 독립 방법으로 세운 쪽을 각각 계산해 비교하는 구조를 유지한다. 독립 쪽을 엔진 호출로 바꾸지 않는다.
3. 독립 쪽이 **엔진 코드를 옮겨 적은 것이 아님**을 test docstring에 근거와 함께 적는다(`probe_gm_id_monotonicity`: 엔진은 `_solve_vgs`가 고르는 해, test 쪽은 gm_id 곡선의 정점 오른쪽(강반전) 가지에서 역보간 -- 선택 규칙이 다르다. `probe_prevention_wiring`: `gate == drain`은 회로 물리의 diode 정의이고 엔진의 role 라벨 분기와 다른 근거다).
4. 판정은 두 쪽의 **차이가 뜻하는 성질**로 쓴다(예: 엔진 해가 강반전 가지에 있어야 한다, role 문자열이 바뀌어도 물리가 같으면 판정이 같아야 한다). 두 값이 같다는 것만 단언하고 끝내지 않는다.
5. 판정을 세울 수 없는 절은 옮기지 않고 사유를 남긴다(무동작 test 금지).
6. 승격한 test는 기본 순서와 `--shuffle-seed` 1~5에서 통과한다. 실패하면 test를 약화하지 말고 멈추고 보고한다(엔진 결함 가능성 -- design §4 F4).
7. 엔진 소스와 다른 test는 바뀌지 않는다. 수집 집합은 base에서 사라진 id 0.

## 신규 시그니처

| 모듈 | 심볼 | 시그니처 |
|---|---|---|

## 판정 유형 근거

test-only: 대상 코드 불변, code 커밋·병합 없음.

## oracle 종류와 출처

(b) 다른 방법의 폐형식·독립 계산: 두 test의 기대값은 엔진이 아니라 (i) gm_id 곡선의 강반전 가지라는 물리적 선택 규칙 (ii) `gate == drain`이라는 diode의 정의에서 온다. 엔진 출력을 기대값으로 쓰지 않는다.

## 거부해야 할 입력

각 성질의 반례를 합성 입력으로 만든다(약반전 가지 해를 준 경우, 물리적으로 diode가 아닌데 role만 diode인 경우) -- 판정이 실제로 거부해야 한다.

## library 회로 적용 여부

`probe_prevention_wiring`은 파일럿 topology를 읽는다(원본 그대로). 동작 보존은 E-LIB·E-INST로 확인한다.

## 무동작 판정 입력(무발동 값)

다른 test 전부 -- 판정이 base와 같다.

## 재현할 수치

없음.

## 결정 필요 항목

**V4 규칙 (1) 면제가 필요할 수 있다.** 두 test는 판정 양쪽에 같은 피검 호출(LUT 조회·topology 로드)이 남는 대조형이라, 1차 시도 auditor가 규칙 (1) 발견을 내면 C13(`20260923-v4-decision-exempt`)이 연 `target_kind: decision` 면제로 처리한다 -- 근거는 계약 3의 '독립 방법'이고, 사용자 승인을 받아 승인 기록에 test id를 적는다(C9 선례 `20260923-c9-v4-exempt`).

## 재시도 기록

1차 시도(2026-09-29, test 커밋 e19686f, dispute 없음): test-author가 새 test 10개(기본+seed 1~5 통과)를 썼으나 전체 스위트에서 P1·P3a 계약 test 2개가
실패 -- 이 spec card 계약 1의 파일 이름이 P3a 승격 규칙(`unit/test_probe_*`)과 달랐다(오케스트레이터 spec card 결함). 계약 test 기대는 고치지 않고
계약 1의 이름을 규칙에 맞춰 개정, 같은 id로 1부터 다시 한다. 1차 test의 본문은 2차 시도 입력으로 쓴다(이름만 바뀜).
개정 커밋 d0650b7은 bash heredoc 덧붙이기가 이 파일 앞 13줄(머리 블록·의도)을 덮어써 깨졌고, 다음 커밋이 d0650b7^ 판에서 다시 고쳤다.

## 변경 이력

- 2026-10-29 `cards/revise-1029`: 위 상태 표지만 더함 -- 본문 불변, 표지 전 원문 = `git show 052465ed:docs/02-design/specs/20260923-probe-promote-differential.spec.md`.
