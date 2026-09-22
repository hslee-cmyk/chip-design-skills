---
id: 20260922-ts1-legacy-move
phase: 1
evidence_type: equivalence
gate_change: no
---
## 의도

TS1(계획 N3.11): 판정이 있는 인라인 self-test 블록 4개(`sizing_recipe`·`stick_diagram`·`design_report`·`topology_library`)를
C1 도구(`tools/migrate/extract_selftest.py`, 20260922-ts1-extract-tool)로 `tests/legacy/`에 본문 그대로 옮기고, 소스에서 블록과
바로 앞 연속 주석 배너를 지운다. 동작 보존 변경(equivalence). 정본 명세는 design `10-test-separation` v1.2 §6.1 C2·§7 E1·§9 C2 행.
이 뒤로 TS0(Test 16 fixture)과 TS3가 test 경로의 이관본을 test-author가 고칠 수 있게 된다.

## 관찰 가능한 계약

1. test 커밋(test-author): `A/tests/legacy/selftest_<m>.py` 4개(C1 도구 `extract --source A/<m>.py --module <m>` 출력 그대로, 손 편집 없음)와 `A/tests/legacy/test_legacy_selftests.py`(이관본마다 `[sys.executable, <이관본>, <A 절대 경로>]`를 `cwd=A`, `PYTHONHASHSEED=1`로 실행해 `returncode == 0`, parametrize 4). `A` = `skills/analog-gmid-design/assets`.
2. code 커밋(code-author): 4개 소스에서 `if __name__ == "__main__":` 블록과 그 바로 앞의 연속 `#` 주석 배너(블록 앞 빈 줄 전까지)만 지운다. 그 밖의 줄은 바꾸지 않는다.
3. 동등성(design §6.1 C2 증거 1~5, §7 E1): 같은 격리 복제본 한 곳에서 base 소스 직접 실행과 병합본 이관본 실행의 stdout이 모듈 4 × `PYTHONHASHSEED` 1..5 = 20쌍 모두 바이트 동일, 추출 재현(T에서 도구를 base 소스에 다시 돌린 출력 = 커밋된 이관본), 4개 소스의 모듈 AST(블록 제외) base = 병합본.

## 신규 시그니처

| 모듈 | 심볼 | 시그니처 |
|---|---|---|

## 판정 유형 근거

equivalence(계획 N3.12.3, N3.11 TS1): 동작 보존 이동이라 red가 없다. 증거는 design §6.1 C2의 20쌍 stdout 동일과 추출 재현·AST 동일.

## oracle 종류와 출처

(c) 이관 전 출력(동작 보존): base 소스의 self-test stdout이 기준이다. test 커밋의 `test_legacy_selftests.py`는 이관본이 끝까지 돈다(exit 0)만 판정하고, 출력 동등성은 auditor의 E1이 판정한다.

## 거부해야 할 입력

해당 없음(동작 보존). 동등성이 깨지면(20쌍 중 하나라도 다르면) auditor FAIL -- design §8 해당 실패 경로.

## library 회로 적용 여부

해당 없음(엔진 동작 불변, self-test 위치만 이동).

## 무동작 판정 입력(무발동 값)

해당 없음.

## 재현할 수치

없음.

## 결정 필요 항목

없음(V5 발견이 나오면 design §8 F5 -- R1 절차, 05 §12 'V5 승인 운반').
