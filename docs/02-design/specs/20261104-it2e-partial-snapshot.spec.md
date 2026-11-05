---
id: 20261104-it2e-partial-snapshot
phase: 해당 없음 (DEC-86 -- merge_gate 미사용, N6.3 절차)
evidence_type: red-green
gate_change: no
---
## 의도

후보 실패로 붙는 부분 스냅샷에서 parent의 낡은 필드를 지워 지문이 (평가 키, 실패 지점)만으로 정해지게 한다. 원칙: '없음'이 '낡은 값'보다 안전(N3.3), graph 규칙 3(집합식 정의 자리 하나). 결정 덮개: O-96·O-97, O-225·O-226.

## 관찰 가능한 계약

interface card `20261104-it2e-partial-snapshot.interface.md` 전체.

## 재작성 범위(엔진 인용 = 지울·바꿀 자리, integ/it12 `b9351eac`, IT-2d head에서 다시 잰다)

| 자리 | 일 |
|---|---|
| `E/sizing/seal_versions.py:16-40` 인라인 `base_writers`·`called`·`used − …` | 함수로 |
| `E/sizing/kernel_run.py:85-87` keep 합집합식, `:56-62` `_call_block` 부착 | 함수 호출, `before` 인자 |
| `E/sizing/seal.py:66-78, :87` 부착 | 줄인 스냅샷 부착 |
| `E/sizing/CONTRACT.md`, `E/_module_map.py` 항목 | 문언 |

## 신규 시그니처

| 모듈 | 심볼 | 시그니처 |
|---|---|---|
| `gmid_engine.sizing.seal_versions` | `writers_in_scope` | `def writers_in_scope(base, blocks) -> frozenset` |

## graph 단일 정본

(원칙 7, `fpga/CLAUDE.md` '★graph 단일 정본', 계획 N3.3 G0~G7·N6.3 '같은 입력 재계산 0')

* 새 필드·cache·값 사본·블록 호출 0. 함수는 순수 집합 함수.
* 파생은 기존 `derive_child`. 셋째 사본 금지(AST).
* 정본 자리가 없으면 만들지 않고 멈추고 보고한다.

## 소비자

| 새·바뀐 필드·def | 엔진 소비자 |
|---|---|
| `writers_in_scope` | `kernel_run`(keep·부착), `seal`(부착), `seal_versions`(coverage) |

## 판정 유형 근거

지문(실패 줄 `snapshot_fp`) = 동작 변경, 지문 밖 결과 = 순수 리팩터링(O-34). SPICE 다리는 N6.3 '대상 없음' (ii) -- 소비자 0 증거를 판정 기록에.

## oracle 종류와 출처

(a) 변성 관계: 축소가 no-op인 parent 없는 경로가 기대값을 낸다. `writers_in_scope` 값은 손 집합.

## 거부해야 할 입력

`writers_in_scope(None, …)` = `TypeError`. 봉인 4 coverage 위반 픽스처 FAIL 유지.

## library 회로 적용 여부

회로 무관 기계 규칙. 13회로 실패 줄 변화 수는 **유보**(O-225).

## 무동작 판정 입력(무발동 값)

parent 없는 평가: 스냅샷 writer가 이미 집합 안이라 지문 불변. ss 단계 실패 불변. 계수 변화 0.

## 재현할 수치

없음.

## 결정 필요 항목

| 항목 | 물리 결정자 | 식·원문 | 실측 | 판정 |
|---|---|---|---|---|
| 없음 | -- | -- | -- | -- |

## 원래 취지와 다름

없음(U-93 취지 회복, 계획 표지). 13회로 실패 줄 수 유보만 A-7.

## 절차

(계획 DEC-86이 남긴 넷 그대로, 정본 = 계획 N6.3)

1. 코드 작성 주체와 test·기대값 작성 주체 분리(WP-13).
2. 깨진 test·기준 약화는 숨기지 않고 보고.
3. 변경당 커밋 1.
4. 매 변경 뒤 새 test 체계(`gmid_engine/tests/`) 전체 실행.

* **판정 기록**: `.ai/verification/20261104-it2e-partial-snapshot.json`.
* **test 이의**: `docs/02-design/disputes/20261104-it2e-partial-snapshot.md`.

## 작성 전 실측

(2026-11-04)

1. 사실 재측정: `seal_versions.py`(`git cat-file` 전문), `kernel_run.py:85-87`, `seal.py:48-72`. 줄은 IT-2d head에서 다시 잰다(계획 범위 5 규칙).
2. 엔진 인용 용도: 재작성 범위뿐.
3. 이름 충돌: `writers_in_scope`·`test_it2e_` 0 파일(`scope_grep.txt`). 새 파일 없음.
4. 원칙 계약화: T-E6.
5. 쓰기 경로: 코드 ≠ test ≠ 판정.
6. 계획서 소비자: 지우는 이름 없음.
7. 미배선: 호출 자리 셋.
8. 기존 test: 없음 예상, `tests/search/test_kernel.py` `partial` 35건 실행 확인.
9. 승인 줄: 의도 절.
10. 범위 계약: diff 계약 없음.
11. test 이름: 접두 `test_it2e_`.
12. 같음 판정: `frozenset`·fp 문자열 비교.
13. red 모양: T-E5만 `ImportError`, 나머지 assertion.
14. 상수·회로 이름: 0.
