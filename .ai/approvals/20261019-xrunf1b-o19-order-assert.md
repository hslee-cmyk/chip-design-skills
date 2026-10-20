---
id: 20261019-xrunf1b-o19-order-assert
date: 2026-10-19
target_kind: decision
target: O-19-1-XRUNF1B-ORDER-ASSERT
scope: card xrunf1b(XRUN-F1 card B) -- test_id_change_recomputes_from_slices의 '쓴 순서' 단언 삭제(블록 순서는 코드 고정·layout CONTRACT §4가 정함), computed_blocks 삭제(O-17 (3))에 따라 test 5개를 RunCounters 판정으로 옮김; 기준 약화 승인(criteria_weakened)
---

## 사용자 원문

> 권고대로

(2026-10-19, 세션 jsonl `63c6146a-ab1d-4035-a169-bae810986922`. 결정 기록 `wt/_drafts/user_decisions.md` 638행 O-19 원문(고치지 않고 그대로): "(1) card B -- layout ly_slice_density를 정식 @compute_block으로(graph 필드 writer는 모두 RunCounters·G-10 계수 안, 근본원칙), computed_blocks 삭제(O-17 (3))에 따라 RunCounters로 못 옮기던 test 5개(test_output_shape·test_rejected_only_change_reuses_slices_and_candidates·test_id_change_recomputes_from_slices·test_reference_w_change_does_not_recompute_slices·test_lut_fingerprint_is_part_of_slice_key)는 RunCounters로 옮기고, test_id_change_recomputes_from_slices 405행 \"쓴 순서\" 단언은 삭제(블록 순서는 코드 고정·CONTRACT §4가 정함, 기준 약화 승인 -- criteria_weakened 기록)")

## 범위 설명

덮는 것: 위 test 하나의 '쓴 순서' 단언 삭제와 test 5개의 판정 수단을 `LayoutResult.computed_blocks`에서 `RunCounters` 증분으로 옮긴 것. 덮지 않는 것: 그 밖의 단언 삭제·약화, O-36 (3)·O-39(design 40 v1.11.2, O-42 승인)로 바뀐 재계산 집합 기대(예: passives만 바꾼 test의 `{ly_canonical_naming, ly_rows}`) -- 그것이 약화인지는 판정자가 따로 판단한다.
