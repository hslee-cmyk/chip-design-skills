---
id: 20260923-probe-promote-clean
phase: 2
evidence_type: test-only
gate_change: no
approval: 20260923-20-dead-code-dup-design
---

> **[상태 표지 2026-10-29] 실행·병합 완료 기록 -- 현행 규칙·절차 아님.** 판정 기록 `.ai/verification/20260923-probe-promote-clean.json`(FAIL 0)이 있고 이 card의 커밋은 master에 병합됐다. 옛 계획 Phase 2(죽은 코드·DUP 정리) card이고 Phase 2는 폐기됐다(계획 N6.1 '옛 Phase 처리' 2행 -- 새 엔진은 모듈 지도 N3.10으로 처음부터 개념당 정본 하나). 본문의 spec card·interface card·auditor 판정(V1~V10)·DEC-40 승인·R1 절차는 DEC-86으로 폐기했다(계획 N3.12·N4.2, DEC-40 행) -- 현행 완료 조건은 계획 N6.3이다. 본문의 `A`(`skills/analog-gmid-design/assets`) 아래 옛 엔진·test는 `skills/analog-gmid-design/legacy/`로 옮겨졌고(`60727b06`) 새 test 체계(`gmid_engine/tests/`)에서 돌지 않는다. card LT-1(DEC-99)이 `legacy/`를 지운 뒤에는 tag `legacy-final`에만 남는다. 이 card가 만들거나 옮긴 파일 가운데 `legacy/tests/unit/test_probe_*` 승격본 4개·`legacy/tests/unit/_library_sized_contexts.py`·계약 test `legacy/tests/contracts/test_ts6_probe_relocate.py`는 O-180(LUT는 v2 r2 묶음만 남기고 sample LUT를 읽는 legacy test·probe도 지움)의 삭제 대상이다 -- LUT 정리(브랜치 `data/lut-v2-only`) 병합 전에는 `legacy/` 아래 있고, 병합 뒤에는 git 이력에만 있다(LT-1보다 먼저 지워짐). 본문은 기록이며 덧대지 않는다(O-169).

## 의도

TS6(계획 N3.11), design `20-dead-code-dup` v1.2 §5·§5.1·§8 P3: 승격 후보 7개 중 **엔진 식 재구현이 없는 4개**를 pytest test로 바꾼다.
나머지 3개는 재구현을 oracle로 다루는 판단이 필요해 다른 card로 나눈다(§5.1 표) -- 위험이 다른 것을 한 판정에 묶지 않는다.
대상: `probe_lut_L_interpolation`, `probe_parasitic_pm_all_circuits`, `probe_revalidation_scope`, `probe_role_L_derivation`.
A = `skills/analog-gmid-design/assets`. 엔진 소스는 바뀌지 않으므로 code 커밋이 없다(test-only -- P2에서 확인한 대로 판정 유형은 커밋 모양이 정한다).

## 관찰 가능한 계약

1. `A/tests/unit/test_probe_<주제>.py` 4개가 생기고, 대응하는 `A/tests/probe_*.py` 4개가 없어진다. 파일 이름의 `<주제>`는 원본 probe 이름에서 `probe_` 접두사를 뺀 것이다. 두 승격본이 같은 입력(회로 로드·theta 한 점 평가)을 쓰면 **판정을 담지 않는 입력 구성기**를 `A/tests/unit/_<이름>.py`로 따로 둘 수 있다 -- 그 파일에는 `assert`·`pytest.raises`·기대값이 하나도 없어야 하고, 이름이 `_`로 시작해 pytest가 수집하지 않아야 한다(이 계약은 존재 주장이지 '파일이 4개뿐'이라는 전수 주장이 아니다).
2. 각 probe가 **출력으로만 보고하던 사실**이 assert가 된다. 판정 문장은 test 본문에 보이고, 판정 보조 함수를 쓰면 이름이 `assert`로 시작한다(V4 규칙 (4)).
3. 기대값의 출처(oracle)를 test마다 docstring에 적는다. 원본 probe가 엔진 함수를 불러 **출력만 했다면**, 승격 test는 그 출력이 만족해야 할 성질(단조성·구간·일치 등)을 판정으로 적는다 -- 엔진 출력을 그대로 기대값으로 박지 않는다(V4 규칙 (2)).
4. 판정을 세울 수 없는 절(출력이 진단일 뿐 성질을 말할 수 없는 부분)은 **옮기지 않는다**. 옮기지 않은 절이 있으면 그 목록과 사유를 판정 기록에 남긴다(무동작 test 금지).
5. 승격한 test는 기본 실행에서 통과한다. 실패하면 그것은 엔진 결함이므로 test를 약화하지 말고 멈추고 보고한다(design §4 F4와 같은 처리).
6. `--gmid-phase=2 --gmid-strict=` 기본 순서와 `--shuffle-seed` 1~5에서 모두 통과한다(셔플 아래 공유 상태 없음).
7. 엔진 소스(`A/*.py`, `workspaces/run_harness.py`)는 바뀌지 않는다. probe도 이 card가 승격하는 4개 말고는 바뀌지 않는다.
7-a. **예외 -- 앞선 card가 굳혀 둔 파일 집합 사실**: P1·P2의 계약 test 두 개(`contracts/test_ts6_dead_probes.py`, `contracts/test_ts6_probe_relocate.py`)는 승격 전 probe 집합을 기대값으로 담고 있어 승격과 동시에 거짓이 된다. 이 card는 그 기대값을 **숫자·이름 목록이 아니라 규칙에서 유도**하도록 고친다(사용자 결정 2026-09-23 "규칙에서 유도하게"): 승격본 `unit/test_<probe 이름>.py`가 있으면 원본이 없어야 하고 그 반대도 성립해야 한다(양방향 배타). 판정을 약하게 하는 변경이 아니라 옮기다 만 상태를 새로 잡는 강화이고, V5 발견이므로 DEC-40 승인(`20260923-p3a-contract-tests`)을 받는다. 그 두 파일 말고 다른 test는 바뀌지 않는다.
8. 수집 집합은 base에서 사라진 id 0이고, 늘어난 것은 이 card의 새 test뿐이다.

## 신규 시그니처

| 모듈 | 심볼 | 시그니처 |
|---|---|---|

## 판정 유형 근거

test-only: 대상 코드 불변, code 커밋 없음, 병합 없음(`00-common` §8.1 `code_commit: null`). 증거는 새 test가 병합본에서 통과하는 것과 동작 보존(design §3 E-LIB·E-INST), 수집 불변(계약 8)이다.

## oracle 종류와 출처

(a) 구성으로 정답이 정해진 입력과 (d) 선언·문헌이 주다. 각 test의 기대값은 원본 probe가 **검사하려던 성질**에서 나오고, 그 성질은 probe의 주석·출력 문구와 계획서·design의 해당 규칙에서 읽는다. 엔진을 불러 나온 값을 기대값으로 삼지 않는다.

## 거부해야 할 입력

각 test가 판정하는 성질의 반례를 합성 입력으로 하나 이상 만들어, 판정이 실제로 거부하는 것을 보인다(게이트가 통과만 하는 것이 아님을 보이는 것 -- 계획 N4.2 V7 취지).

## library 회로 적용 여부

원본 probe가 library 회로를 읽으면 그대로 읽는다(예: `probe_parasitic_pm_all_circuits`는 회로 전부). 동작 보존은 E-LIB·E-INST로 확인한다.

## 무동작 판정 입력(무발동 값)

승격하지 않은 probe와 기존 test 전부 -- 판정이 base와 같다(계약 8).

## 재현할 수치

없음. 원본 probe가 출력하던 수치를 판정 기준으로 옮기는 경우에는 그 수치의 출처를 계약 3대로 docstring에 적고, 수치 자체를 기대값으로 박지 않는다.

## 결정 필요 항목

계약 7-a의 DEC-40 승인(`20260923-p3a-contract-tests`, diff 해시는 auditor 측정값). 그 밖에는 없다(U-02 승인 `20260923-u02-d-list`, design v1.2 §5.1). 계약 4·5에 걸리는 절이 나오면 멈추고 보고한다.

## 변경 이력

- 2026-10-29 `cards/revise-1029`: 위 상태 표지만 더함 -- 본문 불변, 표지 전 원문 = `git show 052465ed:docs/02-design/specs/20260923-probe-promote-clean.spec.md`.
