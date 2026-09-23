---
id: 20260923-probe-promote-clean
phase: 2
evidence_type: test-only
gate_change: no
approval: 20260923-20-dead-code-dup-design
---
## 의도

TS6(계획 N3.11), design `20-dead-code-dup` v1.2 §5·§5.1·§8 P3: 승격 후보 7개 중 **엔진 식 재구현이 없는 4개**를 pytest test로 바꾼다.
나머지 3개는 재구현을 oracle로 다루는 판단이 필요해 다른 card로 나눈다(§5.1 표) -- 위험이 다른 것을 한 판정에 묶지 않는다.
대상: `probe_lut_L_interpolation`, `probe_parasitic_pm_all_circuits`, `probe_revalidation_scope`, `probe_role_L_derivation`.
A = `skills/analog-gmid-design/assets`. 엔진 소스는 바뀌지 않으므로 code 커밋이 없다(test-only -- P2에서 확인한 대로 판정 유형은 커밋 모양이 정한다).

## 관찰 가능한 계약

1. `A/tests/unit/test_probe_<주제>.py` 4개가 생기고, 대응하는 `A/tests/probe_*.py` 4개가 없어진다. 파일 이름의 `<주제>`는 원본 probe 이름에서 `probe_` 접두사를 뺀 것이다.
2. 각 probe가 **출력으로만 보고하던 사실**이 assert가 된다. 판정 문장은 test 본문에 보이고, 판정 보조 함수를 쓰면 이름이 `assert`로 시작한다(V4 규칙 (4)).
3. 기대값의 출처(oracle)를 test마다 docstring에 적는다. 원본 probe가 엔진 함수를 불러 **출력만 했다면**, 승격 test는 그 출력이 만족해야 할 성질(단조성·구간·일치 등)을 판정으로 적는다 -- 엔진 출력을 그대로 기대값으로 박지 않는다(V4 규칙 (2)).
4. 판정을 세울 수 없는 절(출력이 진단일 뿐 성질을 말할 수 없는 부분)은 **옮기지 않는다**. 옮기지 않은 절이 있으면 그 목록과 사유를 판정 기록에 남긴다(무동작 test 금지).
5. 승격한 test는 기본 실행에서 통과한다. 실패하면 그것은 엔진 결함이므로 test를 약화하지 말고 멈추고 보고한다(design §4 F4와 같은 처리).
6. `--gmid-phase=2 --gmid-strict=` 기본 순서와 `--shuffle-seed` 1~5에서 모두 통과한다(셔플 아래 공유 상태 없음).
7. 엔진 소스(`A/*.py`, `workspaces/run_harness.py`)는 바뀌지 않는다. 다른 probe·test도 바뀌지 않는다.
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

없음(U-02 승인 `20260923-u02-d-list`, design v1.2 §5.1). 계약 4·5에 걸리는 절이 나오면 멈추고 보고한다.
