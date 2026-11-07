---
id: 20261107-fs1-d8-load-gate
spec_card: docs/02-design/specs/20261107-fs1.spec.md
test_id: skills/analog-gmid-design/gmid_engine/tests/sizing/test_block_dc.py::test_dc_solve_cell_member_lookup_failure_is_not_avoided
---
## 문제의 test

D-8 `test_dc_solve_cell_member_lookup_failure_is_not_avoided`. 슬라이스 `r4_nmos_w200.npz` 의 `L` 축만 `+3e-6` 으로 바꾼 뒤 `load_lut_set(...)` 으로 다시 적재하고(`# 적재 관문 통과가 전제(아니면 멈추고 보고)`), 그 LUT 로 `size_and_seal` 이 후보 실패로 끝나는지 본다.

## 근거(oracle 또는 사용자 원문)

* 적재가 test 자기 줄(`sizing/test_block_dc.py:196` `lut2 = load_lut_set(...)`)에서 `SchemaRejectedError` reason `lut_slice_axes_mismatch` 로 거부된다(`lut/lut_set.py` `load_lut_set` → `_build_slice`: 모든 슬라이스의 격자 축이 같아야 한다 -- FS-1 이전부터 있는 적재 관문, 이 card 가 바꾸지 않았다).
  test 가 스스로 적은 전제 '적재 관문 통과'가 서지 않는다(interface §4.4 D-8 도 '적재 관문을 통과하지 못하면 멈추고 보고').
* interface 가 말한 '그 슬라이스 하나만 다른 L 격자' LUT 는 슬라이스 간 축 일치 관문(`lut_slice_axes_mismatch`) 때문에 어떤 구현에서도 만들 수 없다. 따라서 D-8 의 입력(소자 L 이 슬라이스 키 200 의 L 축 밖)을 LUT 적재 경로로는 구성할 수 없다.
  (구현 쪽 사실: 같은 상황에서 필요한 동작 -- 칸 키 슬라이스에서 `lut_axis_out_of_range` 가 나면 다른 슬라이스로 피하지 않고 그 평가가 실패 -- 은 `dc_solve` 가 칸 키 슬라이스만 조회하므로 성립한다. 이 입력을 만들 수 없어 test 로는 보이지 못했다.)

## 요청

D-8 입력을 적재 관문을 통과하는 구성으로 바꾼다(예: 두 슬라이스의 축은 같게 두고, 소자 L 이 가장 짧은 L 앵커 밖/축 밖이 되게 θ 의 L 만 슬라이스 200 의 `lut_axis_out_of_range` 사유가 나는 값으로 정하거나, `LutMemo` 수준에서
슬라이스 200 의 점 조회만 `lut_axis_out_of_range` 가 나게 하는 정당한 방법). 또는 이 단언을 구조 단언(`dc_solve` 가 칸 키 외 슬라이스를 조회하지 않음 -- `op_point` 호출 인자의 `w_key` 집합 ⊆ 칸 키)으로 대체한다.
