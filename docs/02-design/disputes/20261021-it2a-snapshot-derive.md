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

## 문제의 test 2 (기존 test -- 계수 기대, 목록 밖)

`skills/analog-gmid-design/gmid_engine/tests/sizing/test_size_and_seal.py` 4개(기대 `sum(reuses for EVAL13) == 13`, 실제 4):
`test_same_theta_with_parent_zero_compute`, `test_passive_theta_only_change_zero_dc_compute[key0-1.1e-12]`, `[key1-11000.0]`, `[both-None]`.

## 근거 2

design 41 4.7-3c: keep = base writer ∪ 커널 호출 블록(`steps`·`later` 네 블록). 봉인 항목 블록 8개와 `dc_seal_report`(`seal_dc` 가 부르는 아홉 블록)는 keep 에 없으므로
child 에서 필드가 지워지고, 같은 입력 버전이라 S3 색인 graft 로 돌아온다(`computes` 0 은 그대로 통과, outcome 이 `reuse` -> `graft`). 그래서 EVAL13 의 `reuses` 는 13 이 아니라 4(커널 블록)다.
design 41:756 (i)은 이 outcome 변화를 'ss 블록'에 대해서만 적었고 봉인 블록 아홉은 빠져 있다(같은 규칙의 결과). 봉인 블록을 keep 에 넣으면 `dc_seal_report` 가 봉인 4 coverage 에서
foreign_writers 가 되고(그 블록은 item4 뒤에 불림) 12 + 1 이라 어차피 13 이 안 된다 -- design 규칙대로 구현하는 한 이 기대는 맞출 수 없다.

## 요청

위 4개의 기대를 `reuses == 4`(실측, computes 0 은 통과; 나머지 아홉이 graft 인지는 test 작성 주체가 계수로 확인) 꼴로 바꾸고 변화표에 적는다(약화 아님, ss reuse -> graft 와 같은 종류). 결정은 사람/test 작성 주체.

## 요청(문제의 test 1)

`test_empty_calls_pass` 를 card (3) 과 모순 없게 고친다(예: 빈 calls 의 스냅샷으로 `ctx.base` 자체를 쓰거나 기대를 `fail`/foreign_writers 로 바꿈) -- 결정은 사람. code 주체는 test 를 고치지 않았다.

## 결정과 해소 (사용자 O-94·O-95)

- O-94: (1) test_empty_calls_pass는 test 쪽에서 수정(완료) (2) reuses==4로 낮추기 기각, design 정오로 keep에 봉인 항목 블록 여덟 포함 (3) seal_dc(base=None) 기본값 기각. 해소: code 수정 -- seal.py SEAL_ITEM_BLOCKS 상수·seal_dc base 필수, seal_versions base None TypeError, run_kernel keep 확장. dispute 종결.
