---
id: 20261106-lm1e-out-of-list
spec_card: docs/02-design/specs/20261106-lm1e.spec.md
test_id: skills/analog-gmid-design/gmid_engine/tests/sizing/test_block_dc.py::test_cyclic_strict_recheck_below_floor_fails[0.7-False]
test_id: skills/analog-gmid-design/gmid_engine/tests/sizing/test_block_dc.py::test_cyclic_strict_recheck_below_floor_fails[0.75-False]
test_id: skills/analog-gmid-design/gmid_engine/tests/metrics/test_dc_metrics.py::test_u17_gate_area_and_power_resolution_fields
test_id: skills/analog-gmid-design/gmid_engine/tests/sizing/test_seal_tolerances.py::test_cell_combine_j_a_none_cell_cascades_to_seals_and_report
---
## 문제의 test

card의 '영향 test 목록' 밖에서 `table_at` 결합 규칙(None 하나면 None)의 결과 변화가 나온 4 함수다. 지시에 따라 기대값을 고치지 않고 멈춘다.

1. `test_cyclic_strict_recheck_below_floor_fails[0.7/0.75-False]`: 수렴 뒤 strict 재검증에서 기대 `reason == "lut_query_failed"` + `lut_reason == "lut_curve_undefined"`. 실제 `tol_v_undefined`. MA nmos의 VDS가 하한(0.25 V) 아래라 `tol_cell`의 칸 [0, 0.25) 셀이 None이고, 새 결합 규칙에서 tol = None이 되어 `block_dc._Circuit.tolerance`가 `tol_v_undefined`로 먼저 거부한다. 거부는 그대로이고 사유 이름만 다르다.
2. `test_u17_gate_area_and_power_resolution_fields`: `power_resolution_w` 기대 `1.8 * TOL_V["M2"] * gm["M2"]`(손: vdd 행만 정의, gnd 0 V는 기여 0, M3 tol 미정). 실제 `None`. 카드 3b(b_P: 레일에 닿는 소자 항에 None이 하나라도 있으면 None)에 따라 M3가 닿는 레일의 항이 None이라 b_P = None이 된다. 이 test는 M3가 닿는 레일이 |V| = 0 인 gnd일 때 그 항 기여 0이라 값이 나와야 한다고 본다(손 설명 `test_dc_metrics.py:229-230`).
3. `test_cell_combine_j_a_none_cell_cascades_to_seals_and_report`: card J-a는 봉인 1·3 행에 net `vout`이 undefined로 든다고 기대(`assert "vout" in items[n].nodes`). 실제 봉인 1 `nodes = ('pb', 'vdd')`(n_checked 7, n_undefined 2) -- `seal_node_conflict.py`의 행은 net별 `dc_path_values`의 MOS 경로 소자 tol에서 오고, 이 toy에서 net vout의 경로 소자에 M3가 없다(M3의 경로는 net pb·vdd에 있다). 엔진 변경으로 `vout` 행에 M3를 넣으려면 `dc_path_values`(graph 필드, 이 card 범위 밖)를 건드려야 한다.

## 근거(oracle 또는 사용자 원문)

- 지시: '목록 밖 `at` 결과 변화·`bin_missing_external` 거부가 나오면 기대값을 고치지 말고 멈춰 보고'.
- spec card '영향 test 합계' 문단: 목록 밖 변화는 실행 때 확인(미측정)이라 적혀 있다.
- (1)의 사유 변화는 fail-closed 유지이고 사유 이름만 바뀐다. (2)는 card 3b 문언('레일 항')과 test 손 설명(0 V 레일 기여 0)이 엇갈린다. (3)은 card J-a 전제(봉인 행의 net 구성)가 as-built `dc_path_values`와 다르다.

## 요청

(1) test 기대를 `tol_v_undefined`(또는 두 사유 중 하나)로 하거나 card가 이 사유 변화를 '알려진 fail-closed 손실'에 올리게 해 달라. (2) b_P가 |V| = 0 레일 항을 None 전염에서 뺄지 사람이 정해 달라(빼면 엔진 한 줄, 안 빼면 test 기대 None). (3) J-a 기대 net(`pb`·`vdd`)로 test를 고치거나 `dc_path_values` 범위 변경을 별도 card로 정해 달라.
