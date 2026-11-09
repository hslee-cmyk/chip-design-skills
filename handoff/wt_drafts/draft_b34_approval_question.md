> **폐기(2026-10-01)**: 사용자가 A2 기록 `20260930-b26-before-phase3`(B26-1·B34 Phase 3 전 착수 포함)를 승인해 이 별도 기록은 쓰지 않는다. card `approval`은 A2를 가리키고, `forks`를 범위에서 빼 등가 변이 면제도 필요 없다. 참고용으로만 남긴다.

# B34 앞당김 승인 질문 -- `20260930-b34-before-phase3`

B34 spec card(`draft_b34.spec.md`, id `20260930-b34-grammar-explicit`)의 머리 `approval` 줄이 가리키는 decision 승인 기록의 질문 원문과 범위다.
근거: review_b34 B1 -- design 20 승인(`20260923-20-dead-code-dup-design`)은 '동작이 바뀌는 수정'을 덮지 않는다. 앞당김은 '보고 때 알림'이 아니라 decision 승인 기록으로 받는다(U2·U-39 선례).
U2(`draft_b26_u2_approval_question.md`)와 같은 질문 회차에 묻는다. 기준 약화 면제는 없고, V3 등가 변이 1개만 이 기록의 target으로 면제한다(spec card 'V3 계획').

## 질문 원문(그대로 묻는다)

> **B34(analog-grammar 부재 시 조용한 폴백 제거)를 지금(Phase 2 진행 중) 착수하는 것을 승인해 주실지 여쭙니다.**
> analog-grammar skill이 없을 때 `stick_diagram`이 조용히 `None`을 돌려줘 사이징 입력(`device_roles` 자동 채움, matching 쌍)이 사라지는데도 계속 진행합니다. 설치본(`install.py`에 analog-grammar 없음)에서 실제로 일어납니다.
> B34는 이것을 `analog-grammar`와 경로를 적은 `ImportError`로 바꿉니다(동작 변경). 범위는 import 한 곳과 작은 함수 4개의 부재 분기 삭제이고, 운영 경로 큰 함수의 (이제 도달 불가인) 분기 삭제는 B26-1·B35로 넘깁니다. 기존 test 기준을 낮추는 면제는 없습니다.
> 앞당기는 이유: Phase 3 모듈 이동이 함수별 해시 동일 증명이라 최종형을 이동 전에 만드는 것이 쌉니다.
> 같은 승인으로 등가 변이 1개(`find_differential_and_mirror_forks` 안 `len(members) >= 2`를 `>= 1`로 -- 구성원 하나짜리 fork는 쌍을 못 만들어 결과가 같음)를 V3에서 면제합니다. 기존 test 기준 완화는 아닙니다.
> 따로 `install.py` `SKILLS`에 `"analog-grammar"`를 더하는 사용자 작업이 필요합니다(없으면 설치본은 이제 명시적으로 실패합니다).

선택지: **승인 (Recommended)** / **Phase 3 뒤 착수**(이동 뒤 새 모듈에서 같은 변경 -- card 편집 범위를 새 모듈 기준으로 다시 잰다) / **보류**.

## 승인 기록 초안(사용자 원문을 받은 뒤 오케스트레이터가 `.ai/approvals/20260930-b34-before-phase3.md`로 쓴다)

```
---
id: 20260930-b34-before-phase3
date: 2026-09-30
target_kind: decision
target: U3-B34-BEFORE-PHASE3, stick_diagram:find_differential_and_mirror_forks:const-:body[8].body[2].value.generators[0].ifs[0].comparators[0]
scope: B34 analog-grammar 부재 시 조용한 폴백 제거(부재 -> ImportError, 동작 변경)를 Phase 3 전에 착수 -- 범위 _import_analog_grammar + find_idiom_matches·find_stack_edges·find_differential_and_mirror_forks·audit_theta_root_direction, spec card 20260930-b34-grammar-explicit의 착수 조건
---

## 사용자 원문

> <원문>

(질문: 위 '질문 원문' 그대로 -- 선택지 '<고른 선택지>')

## 범위 설명

덮는 것:
* spec card `20260930-b34-grammar-explicit`의 동작 변경(부재 시 공개 진입점이 `ImportError`)과 그 card를 Phase 2 진행 중에 병합하는 것(card `phase: 2`).
* V3 등가 변이 면제 1개: `stick_diagram:find_differential_and_mirror_forks:const-:body[8].body[2].value.generators[0].ifs[0].comparators[0]`(내부 `_forks_of`의 `len(members) >= 2` → `>= 1`, 구성원 하나인 fork는 `_classify_forks`에서 쌍이 없어 반환 동일). 경로가 병합본과 다르면 이 원소를 정정하는 새 기록이 필요하다.
* 운영 경로 큰 def의 부재 분기를 도달 불가로 남기고 삭제를 B26-1·B35로 넘기는 순서, `propose_theta_kcl_gap_fill` 정리를 백로그로 보내는 것.
덮지 않는 것:
* 등가 변이 1개 외의 V3·V7 면제(변이 id·def id). 기존 test 강도 면제(기준 약화)는 없다.
* `install.py` 편집(사용자 작업), sys.path 주입 방식(R1), analog-grammar 이름 집합(B35)·쓰기 경로(B36).
* 판정 표(`plan_tables_hash` 입력) -- 바꾸지 않는다.

## 재검토

B34가 병합되지 않은 채 Phase 3 M 카드가 `stick_diagram`을 나누기 시작하면 이 앞당김은 효력을 잃고 card 범위를 새 모듈 기준으로 다시 잰다.
```

target 값 주의: V3·V7 도구는 head 트리의 모든 decision 기록 `target` 원소를 면제 id로 읽는다(`reachability._approved_ids`, 쉼표 구분). 첫 원소는 결정 이름(`U3-B34-BEFORE-PHASE3`, U2 기록과 같은 방식), 둘째 원소만 의도한 변이 id다.

