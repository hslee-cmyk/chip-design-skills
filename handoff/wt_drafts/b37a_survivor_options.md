# B37a V3 생존 변이 처리 -- 선택지와 사용자 질문(v4s)

card: `_drafts/draft_b37a.spec.md`(v4s). 측정: card '작성 전 실측' 11(scratch `C:/g192`, gate `master` `dd60db6`).

## 1. 결론: 생존 5개는 모두 test 보강으로 죽는다 -- 사용자 질문이 필요한 생존 변이는 없다

| 변이(`load_topology` 연결 파일 루프, `stmt_delete`) | 죽이는 것 | 시제품 결과 |
|---|---|---|
| `body[13].body[4]` `all_matching_pairs.extend(…)` | 계약 10 (ii) | `AssertionError`(연결 파일 쌍이 meta에 없음) |
| `body[13].body[5]` `all_dispositions.extend(…)` | 계약 10 (iii) | `AssertionError` |
| `body[13].body[6]` `all_device_roles.update(…)` | 계약 10 (iv) | `AssertionError`(M3 `vertical_stack_id` `None` != `"SL"`) |
| `body[13].body[7]` `all_netlist_sections_structured.update(…)` | 계약 10 (v) | `AssertionError` |
| `body[13].body[8]` `all_ideal_sources.extend(…)` | 계약 6 수용 추가 + 계약 10 (vi) | 계약 6: `ports: netlist에 없는 넷 ['vsrc'](DEC-62)` 거부. 계약 10: `AssertionError` |

base(`dd60db6`)에서는 계약 10 PASS(보존), 계약 6 추가는 `KeyError: 'ports'`(허용 밖, red로 세지 않음 -- 다른 수용 항목과 같음). head(모의)에서는 둘 다 PASS.

계약 10은 **키가 겹치지 않는** 두 파일의 합만 단언한다. 문서화된 동작(`load_topology` docstring '자동으로 전부 합쳐서 반환')이고 의문 있는 의미를 고정하지 않는다. 그래서 (d)에 해당하는 변이는 0이다.

## 2. 일부러 고정하지 않은 것 -- 병합 충돌 의미(백로그 후보, 이 card 결정 아님)

모의 head에서 잰 사실(연결 파일 루프 문장은 base와 같다 -- B37a가 바꾸지 않는다):

| 경우 | 지금 동작(실측) |
|---|---|
| 두 파일의 `device_roles`가 같은 소자(M3)를 선언(진입 `{"L_role": "mirror"}`, 연결 `{"vertical_stack_id": "SL"}`) | 연결 파일 항목이 진입 파일 항목을 통째로 덮어쓴다: meta M3 `L_role` = `None`, `vertical_stack_id` = `"SL"`. 진입 파일 선언이 조용히 사라진다 |
| 두 파일의 `_netlist_sections_structured`가 같은 블록 키(`input`) | 연결 파일 블록이 덮어쓴다(진입 파일 블록 소실) |
| 같은 `matching_pairs` 쌍·`dispositions` 항목·`ideal_sources` 항목을 두 파일이 모두 선언 | 중복이 그대로 두 번 남는다(쌍 2·disposition 2·이상원 2) |

이 가운데 첫 두 줄은 IC3(조용한 소실·덮어쓰기) 축의 결함 후보다. test로 고정하면 결함을 '승인된 동작'으로 굳히게 되므로 계약 10은 이 입력을 쓰지 않는다.

**사용자 질문(백로그 이관 여부 -- B37a 착수 조건 아님)**

* Q-S1. 연결 파일 병합에서 같은 키 충돌(`device_roles` 같은 소자, `_netlist_sections_structured` 같은 블록 키)을 어떻게 다룰까?
  * (권장) A: B37a에서는 손대지 않고 백로그에 올린다. 별도 card에서 '충돌은 거부'(IC3의 소자 이름 겹침 거부와 같은 원칙 -- 조용한 덮어쓰기 금지, 어느 쪽을 고를지 추측하지 않음)로 고친다. library 9회로는 `linked_topology_files`가 모두 비어 있어 지금 영향 0이다.
  * B: B37a 범위에 넣는다 -- 동작 변경이라 승인 기록·계약이 늘고 B37a 목적(ports 선언 배선)과 무관하다. 권하지 않는다.
  * C: 지금 의미(덮어쓰기)를 test로 고정한다 -- 결함 후보를 굳히므로 권하지 않는다.
* 중복 유지(쌍·disposition·이상원)는 판정 영향이 확인되지 않았다(측정하지 않음). A의 백로그 card에서 함께 본다.
