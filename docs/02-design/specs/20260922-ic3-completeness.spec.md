---
id: 20260922-ic3-completeness
phase: 1
evidence_type: red-green
gate_change: no
activated_ic_case: IC3:
approval: 20260922-10-test-separation-design
---
## 의도

IC3(계획 N4.1 '조용한 소실·덮어쓰기'): 이름 전역 유일, 저장 필드 목록 단일 정의, 커버리지 재검증. `stick_diagram.py`에 저장 필드 상수
두 개와 검사 함수 두 개를 두고, `save_instance_json`(저장 전 완전성)과 `load_topology`(이름 충돌)에 배선한다(★만들면 반드시 배선).
C6 뼈대 `contracts/test_ic3.py::test_coverage_and_field_completeness`를 실제 검사로 바꾸고, 새 계약과 충돌하는 이관본 stick Test 26을
고친다. 정본 명세는 design `10-test-separation` v1.2 §5.5·§6.7·§9 C8 행. A = `skills/analog-gmid-design/assets`.
test 변경(뼈대 교체·이관본 Test 26)은 V5 발견이라 DEC-40 승인이 필요하고 R1(05 §12 'V5 승인 운반')로 2차 시도에 넣는다.

## 관찰 가능한 계약

1. `INSTANCE_TOP_FIELDS`(`save_instance_json`이 지금 쓰는 키 전부, 선택 키 `scope_note` 제외)와 `INSTANCE_SIZING_FIELDS`(`"W","L","ID","gm","gm_id"`)가 한 곳에만 정의되고 `save_instance_json`은 `INSTANCE_TOP_FIELDS` 순서로 `data`를 만든다.
2. `check_instance_completeness(instance, device_names)`가 `CompletenessVerdict`(`ok`, `missing_top`, `missing_sizing`, `missing_fields`, `missing_netlist`, `coverage_missing`)를 돌려준다 -- design §5.5 필드 정의 그대로.
3. `check_topology_name_uniqueness(device_names, passive_names)`가 `NameCollisionVerdict`(`ok`, `duplicate_devices`, `device_passive_overlap`, `case_only_collisions`)를 돌려준다.
4. 배선: `save_instance_json`은 파일을 열기 전에 (2)를 `load_topology(topology_json_path)`의 소자 이름으로 부르고 `ok`가 거짓이면 모든 누락을 담은 `ValueError`를 내며 파일을 쓰지 않는다. `load_topology`는 연결 파일까지 합친 netlist 소자 이름과 `passive_elements` 이름으로 (3)을 부르고 `ok`가 거짓이면 `ValueError`.
5. 오거부 0: 변형하지 않은 library 9회로 전부 `load_topology` 통과, 사이징 스펙이 선언되고 지금 실행되는 회로(파일럿·`folded_cascode`)의 하네스 `instance.json` 키 정렬 직렬화 sha256이 base와 같다.
6. 새 두 함수의 docstring은 IC5 형식(`검사하지 않는 것:`, `영역: 없음(스키마)`)이고, 레지스트리에 등록된다.

## 신규 시그니처

| 모듈 | 심볼 | 시그니처 |
|---|---|---|
| `stick_diagram` | `INSTANCE_TOP_FIELDS` | `INSTANCE_TOP_FIELDS: tuple[str, ...]` |
| `stick_diagram` | `INSTANCE_SIZING_FIELDS` | `INSTANCE_SIZING_FIELDS: tuple[str, ...]` |
| `stick_diagram` | `CompletenessVerdict` | `class CompletenessVerdict` |
| `stick_diagram` | `check_instance_completeness` | `def check_instance_completeness(instance: Mapping, device_names: Iterable[str]) -> CompletenessVerdict` |
| `stick_diagram` | `NameCollisionVerdict` | `class NameCollisionVerdict` |
| `stick_diagram` | `check_topology_name_uniqueness` | `def check_topology_name_uniqueness(device_names: Sequence[str], passive_names: Sequence[str]) -> NameCollisionVerdict` |

## 판정 유형 근거

red-green: base에 새 심볼이 없어 import가 실패하고(신규 심볼 red), 배선 단언이 AssertionError. 병합본에서 통과(design §6.7).

## oracle 종류와 출처

(a) 구성으로 정답이 정해진 입력: 손으로 만든 instance dict, library topology를 로드·변형한 임시 파일(WP-07), 연결 파일 픽스처(library 회로 하나의 netlist를 두 파일로 나눔). 이관본 Test 26의 합성 sizing도 구성 입력.

## 거부해야 할 입력

design §6.7 1~5: 최상위 키 누락·소자 sizing 누락·필드 누락·netlist 누락·`coverage.missing` 비지 않음(완전성), 소자 이름 중복·소자-수동소자 겹침·대소문자만 다른 겹침(이름), 나뉜 연결 파일 두 곳의 같은 소자 이름, sizing에서 소자 하나를 뺀 `save_instance_json`(`ValueError`, 파일 없음).

## library 회로 적용 여부

적용: library 9회로 `load_topology` 무변형 통과(오거부 0)와 변형 거부.

## 무동작 판정 입력(무발동 값)

변형하지 않은 library 9회로와 정상 instance -- 게이트 통과, 산출물 불변(계약 5).

## 재현할 수치

없음(해시 동일성은 계약 5의 동작 보존 증거).

## 결정 필요 항목

test 변경의 DEC-40 승인(V5, R1). 남는 등가 변이는 `target_kind: decision` 승인으로만 면제(N4.2 V3).
