---
id: 20260922-v3-gmid-options
phase: 1
evidence_type: red-green
gate_change: yes
approval: 20260922-v3-gmid-options
---
## 의도

C6(`20260922-ts7-ic-xfail`)이 `tests/conftest.py`에 `--gmid-phase`(필수)를 넣은 뒤로, V3 도구 `tools/gates/mutate_changed.py`가
변이 전 기준 실행과 변이 실행의 pytest 명령에 그 옵션을 넘기지 않아 UsageError로 끝나고 모든 변이가 '살아남음'이 된다. 소스 def를
바꾸는 첫 red-green인 C8(IC3) 전에 도구를 승인된 conftest 계약(`00-common` §9.3)에 맞춘다. 막는 규칙을 넓히지 않는다 -- V3 판정식은 그대로다.
정본 명세는 design `10-test-separation` v1.2 §6.10·§9 C11 행(review2 N1 반영판). `mutate_changed.py`는 설치 사본이 없어(gate
`pre-receive`·`.claude/hooks`·`.githooks` 어느 것도 아님) 반영 뒤 §13.4 재설치는 필요 없다.

## 관찰 가능한 계약

1. `mutate_changed.py`가 `--gmid-phase=<값>`·`--gmid-strict=<값>` 인자를 받는다(auditor는 V1 명령과 같은 값을 준다).
2. 시험 대상 복사본의 `A/tests/conftest.py`가 `addoption("--gmid-phase", …)`을 가질 때(merge gate의 'CC-3 병합 전 판정식'과 같은 판정) 기준 실행과 변이 실행의 pytest 명령에 V1의 `--gmid-phase=`를 그대로 넘기고, `--gmid-strict=`에는 V1 엄격 집합 중 **인벤토리 test에 그 Phase의 `gmid_ic` 표식(IC·case)이 있는 키만** 넘긴다. 남는 키가 없으면 `--gmid-strict=`(빈 값, `00-common` §8.1 = 키 없음). 두 옵션 모두 `=` 한 토큰 형식.
3. conftest가 옵션을 모르는 저장소(C6 전 모양)에서는 옵션 없이 실행해 기존 판정과 같다(오거부 0).
4. conftest의 거부 규칙(모르는 키 거부 등)은 그대로다.

## 신규 시그니처

| 모듈 | 심볼 | 시그니처 |
|---|---|---|

## 판정 유형 근거

red-green: base 도구로는 conftest가 옵션을 요구하는 합성 저장소에서 변이가 '살아남음'으로 V3 FAIL, 병합본 도구로는 변이가 죽어 PASS(design §6.10).

## oracle 종류와 출처

(a) 구성으로 정답이 정해진 합성 저장소(redteam 케이스): `--gmid-phase`를 요구하는 conftest, 활성화 케이스 표식이 달린 test, 그 test가 죽이는 변이 하나를 가진 합성 소스. 합성 conftest는 커밋하지 않고 `rt.py` 선례대로 실행 중 임시 디렉터리에 만든다(`conftest.py`는 판정 환경 이름).

## 거부해야 할 입력

해당 없음(도구가 옵션을 전달하는 변경). conftest 거부 규칙 불변(계약 4).

## library 회로 적용 여부

해당 없음(게이트 도구).

## 무동작 판정 입력(무발동 값)

conftest가 옵션을 모르는 저장소 → 옵션 없이 실행, 기존 판정과 같음(계약 3).

## 재현할 수치

없음.

## 결정 필요 항목

없음(게이트 변경 승인 기록 `20260922-v3-gmid-options`).
