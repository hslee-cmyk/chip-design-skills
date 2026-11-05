---
id: 20261022-it2a-seal-signature-ext
date: 2026-10-22
target_kind: decision
target: O-93-IT2A-SEAL-SIG-EXT
scope: card IT-2a(20261021-it2a-snapshot-derive) -- 승인 기록 20261021-it2-o67-scope 확장(약화 아님): tests/sizing/test_seal_versions.py 옛 서명 seal_versions(snapshot, calls) 호출 4곳에 base 셋째 인자 추가
---

## 사용자 원문

> 승인 범위 확장 (권고)

(2026-10-22, AskUserQuestion, 세션 jsonl `63c6146a-ab1d-4035-a169-bae810986922`. 결정 기록 `wt/_drafts/user_decisions.md` O-93 행.)

## 범위 설명

덮는 것: card IT-2a가 `seal_versions(snapshot, calls)` -> `seal_versions(snapshot, calls, base)`로 서명을 바꾸므로(spec 23·35행, interface 10행), 기존 `E/tests/sizing/test_seal_versions.py`의 옛 서명 호출 4곳 -- `test_pass_and_independent_version_formula`, `test_input_changed_after_compute_is_violation`, `test_output_written_with_other_version_is_violation`, `test_empty_calls_pass` -- 에 base 셋째 인자(그 test의 `ctx.base`)를 넘기는 기계적 수정. 기존 (1)(2) 단언·기대값은 그대로.

덮지 않는 것: base 기본값 도입(봉인 4 검사 우회 = 기준 약화, card 서명과 다름 -- 기각), 단언 삭제·완화, 그 밖 기준 약화.
