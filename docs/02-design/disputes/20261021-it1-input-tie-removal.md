---
id: 20261021-it1-input-tie-removal
spec_card: docs/02-design/specs/20261021-it1-input-tie-removal.spec.md
test_id: skills/analog-gmid-design/gmid_engine/tests/sizing/test_s2_values.py::test_block_reads_declared_as_contract[dc_columns]
test_id: skills/analog-gmid-design/gmid_engine/tests/sizing/test_current_basis.py::test_current_ties_and_variables_match_8e46548
test_id: skills/analog-gmid-design/gmid_engine/tests/search/test_orbit_ties.py::test_ds_flip_symmetry_bit_identical[names0]
---
## 문제의 test

code 구현(범위 1~5) 뒤 IT-1 규칙 test는 모두 green이고, 아래 기존 test 8개만 남아 red다. 세 건 모두 card 규칙의 결과인데 test 쪽 기대가 안 바뀌었다(code 주체는 test를 고치지 않는다).

1. `test_s2_values.py::test_block_reads_declared_as_contract[dc_columns]` -- `READS["dc_columns"]`(test_s2_values.py:~150)가 `dc_columns.reads`와 **정확히 같음**을 단언하는데, 같은 변경의 `test_writer_plan.py:522`(`("node","port_direction") in set(dc_columns.reads)`)와 interface card·41:672는 `node.port_direction` 추가를 요구한다. 두 단언은 동시에 성립하지 않는다. K-3 갱신 목록에 test_s2_values가 있으나 이 READS 집합에는 `port_direction`이 빠져 있다.
2. `test_current_basis.py::test_current_ties_and_variables_match_8e46548`의 6개 파라미터(current_reuse_telescopic_ota ties 29->30, folded_cascode variables 16->17, ngcc_3stage_ff 21->22, nmcnr_amplifier 23->24, two_stage_ota 10->11, two_stage_ota_sf 12->13) -- 기준 `BASELINE_8E46548`.
3. `test_orbit_ties.py::test_ds_flip_symmetry_bit_identical[names0]` -- 이름 `("M1",)` drain/source 뒤집기 toy에서 두 입력 포트(inp, inn)가 서로 다른 G_vgs 성분이 되어 `StructureUnresolvedError(input_port_multiple_roots, nets=('inn','inp'))`.

## 근거(oracle 또는 사용자 원문)

1. 계약 (a)와 interface card 필드 절·41:672: `dc_columns` READS에 `node.port_direction` 추가(W4 입력 뿌리 판정 `input_roots`가 읽음). 두 test가 모순.
2. 계약 (b)·41:668-672: 같은 DC 엣지가 없어져 G_vgs 순환이 줄어 종속(`cycle_vgs`) 소자가 하나 줄고, 그 소자가 쓰기 소자가 되어 θ 변수가 +1(차동 입력 회로 5개). current_reuse는 전류 기저 열이 바뀌어 tie 수가 바뀜. 모두 K-3·O-13 (1)이 승인한 동작 변경(`.ai/approvals/20261021-it1-o13-scope.md`, '쓰기 계획·θ y·결과'). 이 baseline은 spec card의 test 작성 주체 몫 목록에 없다 -- 소비자 표 밖(S-2)이므로 보고한다.
3. 계약 (d)·41:672: 입력 포트인 W4 뿌리가 둘 이상이면 정지. 이 toy는 drain/source 뒤집기로 두 입력이 서로 다른 성분에 놓이는 구조라 새 규칙에서 정지가 올바른 결과다(S-3 해당 여부는 test 주체가 정함).

## 요청

test 작성 주체가 (1) `READS["dc_columns"]`에 `("node","port_direction")` 추가, (2) `BASELINE_8E46548`을 위 새 값으로 갱신(감사 변화표 근거, 'K-3, 약화 아님'), (3) `test_ds_flip_symmetry_bit_identical[names0]`를 새 규칙에 맞게 정리(toy 변경 또는 정지 단언)할지 정한다. code는 이 셋을 맞추려고 규칙·READS를 바꾸지 않는다.
