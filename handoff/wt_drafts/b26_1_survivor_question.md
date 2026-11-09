# B26-1(20260930-b26-rail-accessor-set) 사용자 결정 질문 초안 -- v4

> **대체됨(2026-10-01)**: 이 질문 초안은 통합 질문 `_drafts/b26_survivor_final_question.md`(Q1~Q3, U-BF는 Q1-BF -- 답해짐 "결함으로 고침 (Recommended)")로 대체됐다. AskUserQuestion에는 통합 질문을 쓴다. 이 파일은 근거 기록으로만 남긴다(삭제하지 않음).

작성 2026-10-01. 근거: `_drafts/draft_b26_1.spec.md` v4 'V3 계획' 2·3, `_drafts/b26_1_revision_log_v4.md`. 측정 scratch C:/g83(삭제), 스크립트 `_drafts/b26_scripts/`.
질문 3건(Q1 필수, Q2·Q3 승인 기록용). 오케스트레이터가 AskUserQuestion으로 물을 때 아래 문안을 그대로 쓴다.

---

## Q1. [U3] 계획된 계약으로도 죽지 않는 V3 대상 변이 24개를 어떻게 처리할까요?

**배경(질문 본문)**:
B26-1을 결정하신 V3 규칙(바뀐 문장 + 주변, 넓힌 T6)으로 재면 대상 변이가 301개입니다. 모의 사본에서 기존 test와 이 card에 더한 계약 test(근사)로 돌려 보니
277개는 죽고 24개가 남습니다. 24개는 B26-1이 `rails=rails`를 붙인 호출문의 **뒤쪽 기존 문장**들로, 레일 판정과는 무관한 기존 동작입니다.
- 20개는 test로 죽일 수 있는 **기존 test 공백**입니다: LUT 없는 repair 가지(4), euler-blocked 행 fixup(3), finger growth 루프·종료 경로(6), 바뀐 호출 결과를 쓰는 뒤 문장
  (`run_full_circuit_audit`의 미러·차동 그룹 루프 2, `resolve_stack_layout` 세로 스택 후보 반영 1, `propose_vertical_stack_id_gap_fill` 포트 경로 1, `case_collisions` 기록 1), 차동 후보 trace 루프 범위(2).
  이 중 7개는 지금 어떤 test도 그 줄을 실행하지 않습니다(base 실행 줄 기록 대조).
- 4개는 **등가 변이**(바꿔도 동작이 같음)라 test로 죽일 수 없습니다: `_propose_L_roles`의 서로 중복인 None 가드 2개, 길이 1이 보장된 목록의 `[0]`→`[-1]`, `range(i + 1, …)`→`range(i, …)`(늘어난 자기 짝은 건너뜀).

**선택지**:
1. **(Recommended) 앞선 test-only card로 기존 동작 test를 먼저 보강 + 등가 4개는 같은 def 안의 동작 불변 정리**
   - B26-1 앞에 test-only card(엔진 코드 변경 없음, 판정 기준 약화 없음) 1건을 두어 위 20개 경로의 **지금 동작**을 고정하는 test를 씁니다. 병합되면 B26-1의 V3에서 그 test가 인벤토리에 들어 20개가 죽습니다.
   - 등가 4개는 B26-1이 어차피 바꾸는 같은 def 안에서 동작을 바꾸지 않게 정리해 등가 변이 자리를 없앱니다: 중복 가드 `if candidates is None: return None` 삭제, `open_terminals[0]` → 튜플 풀기,
     `range(i + 1, …)` 이중 루프 → `itertools.combinations`(순서 같음). 정리 뒤 남는 가드는 이 card의 E4 계약이 죽입니다.
   - 원칙 근거: 판정 기준을 약화하지 않고, 만든 test가 실제 동작 경로를 판정합니다(만들면 배선). 비용은 아래 추정.
2. **def 해시에 묶은 decision 면제(약화)**
   - 24개를 변이 id@함수 원본 해시로 승인 기록 1건에 면제합니다(A1-a 규칙 -- 해시가 바뀌면 자동으로 무효).
   - 그 경로들의 test 공백은 남습니다(백로그 '돌려 보지 않은/생존 변이'로 기록). 판정 기준 적용 범위 축소라 약화 승인입니다.
3. 섞어서: 20개는 1번(test-only card), 등가 4개만 2번(면제).

**test-only card 크기 추정(1번)**:
| 묶음 | 필요한 test | 입력 |
|---|---|---|
| LUT 없는 repair 가지(`optimize_full_circuit_budget`·중첩 `_evaluate_row_split` 9411·9413) | 2 | repair가 필요한 행 분할을 만드는 합성 topology(또는 library 회로 사본)에서 `pr["repaired_rows"]`·`pr["repaired_audit"]` 기대값 |
| euler-blocked fixup(`_fixup_euler_blocked_rows` 11704~11708) | 1~2 | euler 경로가 막힌 행을 가진 합성 행 배치, 분할 결과(segments) 기대값 |
| finger growth(`run_matching_safety_with_finger_growth` 11809·11810·11886~11890) | 2~3 | growth가 한 번 이상 돌고, 끝까지 못 푸는 경우(종료 repair·`_finalize`·반환 dict 키) |
| 뒤 문장 관찰(`run_full_circuit_audit` 그룹 루프, `resolve_stack_layout`, `propose_vertical_stack_id_gap_fill` 포트 경로, `case_collisions`) | 4~5 | 작은 합성 넷리스트, 손으로 적은 기대값 |
| trace 루프 범위(`find_differential_pair_candidates`) | 1~2 | 같은 서명 branch 2개(const+)·3개 이상(arith, 순서) -- trace 진입 이름이 아직 `vdd`/`gnd`(B26-2)라 합성 입력은 그 이름을 쓴다 |
| 합계 | **약 10~14 test 함수, 300~500줄, 합성 픽스처 4~5종** | 엔진 소스 변경 0(V3 없음), V1·V4·V5·V8 판정. 일정: test-author 1회 + auditor 1회(인벤토리 시간 약 3~6분/실행) |

finger growth·euler fixup·LUT 없는 repair는 사이징 ctx가 필요해 픽스처가 가장 무겁습니다(기존 `tests/unit/_library_sized_contexts.py` 재사용 후보). 등가 정리 3줄은 B26-1 code-author 몫입니다(test-only card와 무관).

---

## Q2. [U4] A2 승인 기록에 B40(gate 없는 입력의 `unavailable_reason` 키 삭제)을 더해도 될까요?

**배경**: gate에 커밋된 A2 기록 `20260930-b26-before-phase3`의 범위 ③ B26-1 항목은 "B34에서 인계받은 도달 불가 부재 분기 삭제를 포함한다"만 적었습니다.
B40은 도달 불가 분기가 아니라 **도달 가능한 분기의 반환값 변경**입니다: analog-grammar가 있어도 gate 소자가 없는 입력이면 `propose_device_roles_gap_fill`이
`{…3키…, "unavailable_reason": "analog-grammar를 import할 수 없어…"}`(틀린 사유)를 돌려주는데, B26-1은 이 키만 지워 3키 dict를 돌려주게 합니다. 소비처는 0곳입니다(`git grep`).

**선택지**:
1. **(Recommended) 짧은 추가 승인 기록 1건으로 덮는다** -- id 후보 `20260930-b26-b40-reason-key`, `target_kind: decision`, `target: U4-B26-B40`.
2. B40을 B26-1에서 빼고 백로그(B39와 함께)로 둔다 -- 틀린 사유는 남습니다.

**추가 승인 기록 문안(1번)**:
```
---
id: 20260930-b26-b40-reason-key
date: <답한 날>
target_kind: decision
target: U4-B26-B40
scope: 결정 U4 -- A2(20260930-b26-before-phase3) 범위 ③ B26-1 보충: propose_device_roles_gap_fill이 gate 소자 없는 입력(refined is None, analog-grammar 있음)에서 돌려주는 dict의 unavailable_reason 키 삭제(백로그 B40, 관찰 가능한 반환값 변경)
---
(본문) 사용자 원문 / 질문 / 덮는 것: 위 키 하나 삭제(분기 자체와 나머지 세 키 matching_pairs_proposals·device_roles_proposals·review_needed는 그대로, spec card 계약 14) /
덮지 않는 것: propose_theta_kcl_gap_fill의 unavailable_reason(B39), V3·V7 면제 / 재검토: 소비처가 생기면 다시 묻는다.
```
(card 안 코드 블록의 `## ` 줄 문제를 피하려고 본문 절 머리는 생략했다 -- 실제 기록은 `_TEMPLATE.md` 절 구조로 쓴다.)

---

## Q3. [U5] P9 계약 test 2개의 시그니처 단언을 B26-1의 새 시그니처로 갱신해도 될까요?

**배경**: P9(`20260930-p9-kcl-edges`, 병합 `b7765b0`)의 영구 계약 test `test_kcl_series_union_signature_unchanged`·`test_kcl_and_matching_edges_signature_unchanged`는
매개변수 목록이 정확히 `[netlist, matching_pairs]`·`[transistors, matching_pairs]`이고 모든 매개변수 주석이 `list`인지 단언합니다. B26-1은 두 함수에 기본값 없는 키워드 전용 `rails: RailDeclaration`을 더하므로
병합본에서 두 test가 FAIL합니다. 기대값 변경은 test 작성자가 혼자 할 수 없습니다(작성자≠검증자, V5).

**선택지**:
1. **(Recommended) 갱신 승인** -- 새 기대 = `[…, "rails"]`, 앞 두 매개변수 단언 그대로(주석 `list`, 기본값 없음), `rails`는 키워드 전용·기본값 없음·주석 `RailDeclaration`, 반환 주석 그대로.
   P9의 '시그니처 유지' 계약을 B26-1 계약 4가 대체하며, 정확 일치 단언은 유지되므로 판정 기준 약화가 아닙니다. 승인 기록 `target_kind: diff`(id 후보 `20260930-b26-p9-signature-update`, test diff 위).
2. P9 시그니처를 유지하고 B26-1이 `kcl_series_union`·`_kcl_and_matching_edges`에 `rails`를 넘기지 않게 설계를 바꾼다 -- 두 함수의 레일 판정(계약 7(b))을 선언으로 바꿀 수 없어 B26-1 목표와 충돌(권하지 않음).
