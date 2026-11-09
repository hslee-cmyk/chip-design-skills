# Phase 4 card 후속 반영 대기열 (오케스트레이터가 해당 card 문서에 나중에 반영)

이 파일은 다른 agent가 소유한 초안(#2 `draft_p4_first.spec.md`·`p4_first_card_notes.md`)을 직접 고치지 않고, 반영할 문장만 모아 둔다.

## #2 `20261002-d4-delete-unwired` (`draft_p4_first.spec.md` 'P3 -- Phase 3 뒤 다시 잴 것' / `p4_first_card_notes.md`)

- (2026-10-02, 출처 B41 card 초안 `draft_b41_scope_note.spec.md`·`b41_briefs.md` §0.1-3, 독립 검토 `review_b41.md`) Phase 3 뒤 재측정 항목에 B41 test +37 passed: "B41 card(`20261002-b41-scope-note-test`, Phase 4 첫 card -- #2 앞) 병합 뒤 base 전체 suite가 `+37 passed`(`1 + 4 × len(LIB)`, LIB = library 9회로 기준 -- base에서 다시 센다)이고 #2의 V1·V2 기준 수치는 그 base에서 다시 잰다. B41 card가 #2보다 늦게 병합되면 이 줄은 지운다(B41 착수 조건 3)."
  - 참고: B41 test는 `save_instance_json`·`run_topology_pipeline`만 부르고 #2가 지우는 D-1~D-4를 부르지 않는다(검토 재측정 -- 상호 간섭 없음 예상, #2 재측정 때 확인).
