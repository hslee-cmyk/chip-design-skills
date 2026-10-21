---
id: 20261021-it2a-snapshot-derive
spec_card: docs/02-design/specs/20261021-it2a-snapshot-derive.spec.md
test_id: skills/analog-gmid-design/gmid_engine/tests/sizing/test_seal_versions.py::test_empty_calls_pass
---
## 문제의 test

`test_empty_calls_pass(ctx_c)`: `snap, _ = eval_calls(ctx, theta_c())`(커널 블록 넷을 부른 뒤 스냅샷) 다음 `seal_versions(snap, (), ctx.base)` 가 `status == "pass"` 이고 `n_checked == 0` 이어야 한다고 단언한다.
(커밋 03a385d4 가 옛 서명 호출에 `ctx_c[2].base` 인자만 더했다, 단언 불변, 승인 O-93.)

## 근거(oracle 또는 사용자 원문)

spec card '관찰 가능한 계약': 봉인 4 (3) coverage = 모든 필드 writer ∈ base writer ∪ calls. 이 test 의 스냅샷에는 `dc_currents`·`dc_lengths`·`dc_columns`·`dc_widths` 가 쓴 필드가 있고,
이 네 블록은 base writer 가 아니며(card (4) 서로소가 요구) calls 도 비어 있다. 따라서 (3) 에 따르면 foreign_writers = 그 네 블록이라 `fail` 이어야 하고,
이 test 의 `pass` 와 양립할 수 없다. 같은 파일의 `test_it2a_seal_4_rejects_field_of_writer_outside_base_and_calls` 는 호출 목록 밖 writer 필드를 `fail` 로 요구한다(같은 규칙).
구현은 card 문장 그대로(필드 writer 전수)이고 이 test 만 실패한다(관련 5개 파일 176개 중 1개).

## 요청

`test_empty_calls_pass` 를 card (3) 과 모순 없게 고친다(예: 빈 calls 의 스냅샷으로 `ctx.base` 자체를 쓰거나 기대를 `fail`/foreign_writers 로 바꿈) -- 결정은 사람. code 주체는 test 를 고치지 않았다.
