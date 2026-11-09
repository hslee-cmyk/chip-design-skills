# B26 최종 AskUserQuestion 입력 (질문 4개, 2026-10-01)

근거·문안·측정은 `_drafts/b26_survivor_final_question.md` Q1~Q4(독립 검토 `review_b26_final.md` F1~F3 반영판). 아래 문구를 그대로 쓴다. 각 질문 `multiSelect: false`, 선택지 첫 번째가 권고.
답을 받으면 원문을 `_drafts/user_decisions.md`에 적는다(Q1 답 기록 = B26-1 착수 조건 8).

---

## Q1

- header: `U3 등가`
- question:
  "[U3] B26-1 V3 대상 301개 중 지금 코드에 대응이 있는 264개를 지금 test로 돌리면 50개가 살아남습니다(새 문장 37개는 B26-1 계약 test 몫, 병합본에서 auditor가 잽니다). 26개는 B26-1 계약 test가, 18개는 앞선 test-only card b26pre(19 test, 엔진 변경 없음)가 죽이고, 2개는 이미 답하신 backfill 결함 수정으로 문장이 없어집니다. 남는 4개는 등가 변이(바꿔도 동작이 같음)라 어떤 test로도 죽지 않습니다: `_propose_L_roles`의 서로 중복인 None 가드 2개, `open_terminals[0]`→`[-1]`(원소가 정확히 1개), `range(i + 1, …)`→`range(i, …)`(늘어난 j == i 짝은 a == b로 건너뜀). 등가 4개를 어떻게 처리할까요?"
- options:
  1. label `정리 2줄 + 면제 1 (Recommended)` -- description: "B26-1에서 동작 불변 정리 2줄로 등가 3개를 없애고, 정리로 못 없애는 `range` 1개만 변이 id@def 해시로 면제합니다(약화 승인 1건, 기록은 구현 뒤 auditor가 잰 해시로 병합 전 커밋)."
  2. label `등가 4개 모두 면제` -- description: "엔진 정리 없이 등가 4개를 변이 id@def 해시로 면제합니다(약화 승인 1건에 4개)."
  3. label `4개 모두 정리(C3 포함)` -- description: "면제는 0이지만 `range` 이중 루프를 `itertools.combinations`로 바꾸면 루프 본문 7문장이 새로 대상이 되어 생존 7이 생깁니다(권하지 않음)."
  4. label `test 보강 없이 면제` -- description: "b26pre 없이 남는 24개를 면제합니다. 죽일 수 있는 18개와 결함 2개까지 덮는 기준 약화입니다(권하지 않음)."

## Q2

- header: `U4 B40`
- question:
  "[U4] A2 승인 기록 ③의 B26-1 항목은 'B34에서 인계받은 도달 불가 분기 삭제'만 덮습니다. B40은 도달 가능한 분기의 반환값 변경입니다: analog-grammar가 있어도 gate 소자 없는 입력이면 `propose_device_roles_gap_fill`이 틀린 사유의 `unavailable_reason` 키를 돌려주는데, B26-1이 이 키만 지워 3키 dict를 돌려줍니다(소비처 0곳, git grep). A2 승인에 B40을 더해도 될까요?"
- options:
  1. label `추가 승인 1건 (Recommended)` -- description: "짧은 decision 승인 기록 `20260930-b26-b40-reason-key`로 이 키 삭제만 덮습니다(분기와 나머지 세 키는 그대로)."
  2. label `B40 빼고 백로그` -- description: "B40을 B26-1에서 빼고 B39와 함께 백로그로 둡니다. 틀린 사유는 남습니다."

## Q3

- header: `U5 P9 시그`
- question:
  "[U5] P9 계약 test 2개(`test_kcl_series_union_signature_unchanged`·`test_kcl_and_matching_edges_signature_unchanged`)는 매개변수 목록이 정확히 `[netlist, matching_pairs]`·`[transistors, matching_pairs]`인지 단언합니다. B26-1은 두 함수에 기본값 없는 키워드 전용 `rails: RailDeclaration`을 더하므로 병합본에서 두 test가 FAIL합니다. 기대값 변경은 test 작성자가 혼자 할 수 없습니다(작성자≠검증자). 두 단언을 새 시그니처로 갱신해도 될까요?"
- options:
  1. label `갱신 승인 (Recommended)` -- description: "새 기대 = 원래 두 매개변수 + 키워드 전용·기본값 없음·주석 `RailDeclaration`인 `rails`. 정확 일치 단언은 유지되므로 약화가 아닙니다(승인 기록 diff 1건)."
  2. label `P9 시그니처 유지` -- description: "B26-1이 두 함수에 `rails`를 넘기지 않게 설계를 바꿉니다. 두 함수의 레일 판정을 선언으로 바꿀 수 없어 B26-1 목표와 충돌합니다(권하지 않음)."

## Q4

- header: `card phase`
- question:
  "[Q-B34-PHASE] B34·b26pre·backfill·B26-1 네 card는 Phase 2 DoD 뒤에 병합되는데, 머리는 `phase: 2`이고 A2 기록 ③은 'Phase 2 진행 중'이라 적었습니다. 게이트는 card phase를 현재 Phase와 대조하지 않고, phase 2·3에서 test 결과·strict 집합(둘 다 빈 집합)·N/A 허용이 같습니다. 달라지는 것은 판정 기록 V1의 `--gmid-phase=` 값, 어느 Phase DoD 목록이 card를 세는지, A2 ③ 문구뿐입니다. 어떻게 둘까요?"
- options:
  1. label `phase 3 + 정정 기록 (Recommended)` -- description: "네 card를 `phase: 3`으로, 'Phase 3 M card 전' 순서는 유지하고, ③ 문구를 바로잡는 decision 기록 1건을 남깁니다(design 30 승인·U-03을 기다리지 않는다고 명시)."
  2. label `Phase 2 DoD 앞으로` -- description: "네 card를 Phase 2 DoD 앞으로 당겨 `phase: 2`를 유지합니다. Phase 2 DoD가 늦어지고 DoD N6.3 집계 수치가 늘어납니다."
