---
id: 20261104-it2c-icm-config
spec_card: docs/02-design/specs/20261104-it2c-icm-config.spec.md
test_id: skills/analog-gmid-design/gmid_engine/tests/metrics/test_icm_config.py::test_it2c_declared_view_same_key_merges_into_default
test_id: skills/analog-gmid-design/gmid_engine/tests/metrics/test_icm_config.py::test_it2c_declared_view_other_key_coexists_with_default
test_id: skills/analog-gmid-design/gmid_engine/tests/metrics/test_icm_config.py::test_it2c_servo_undeclared_input_dc_drives_both_ports_together
test_id: skills/analog-gmid-design/gmid_engine/tests/sizing/test_input_window.py::test_window_ends_are_saturated[0.0]
test_id: skills/analog-gmid-design/gmid_engine/tests/sizing/test_input_window.py::test_window_ends_are_saturated[1.0]
test_id: skills/analog-gmid-design/gmid_engine/tests/sizing/test_input_window.py::test_declared_input_dc_same_theta_seals
---
## 문제의 test

이 card 코드를 다 쓴 뒤에도 아래 여섯 test 는 코드로 green 이 될 수 없다. 나머지 새 test 와 `tests/structure` 는 통과한다(코드 작성자 자체 실행, 판정 증거 아님).

1. `test_it2c_declared_view_same_key_merges_into_default`, `test_it2c_declared_view_other_key_coexists_with_default` (T-S1V)
   -- `AttributeError: 'ViewS1v' object has no attribute 'source'`. 두 test 는 `graph.views` 의 `ViewS1v` 에서 `v.source == "spec_constraint_view"` 를 단언한다.
   `ViewS1v` 에는 `source` 칸이 없고(`ViewSeed.source` 만 있다; 갈래 합치기는 `ViewSeed` 단계에서 일어난다) interface '공개 이름과 서명' 이 `ViewSeed`·`ViewS1v` 에 더하는 칸은
   `default_port: bool` 하나뿐이다. 합친 뒤에도 선언 출처가 남는지는 `ViewSeed.source` 에서만 볼 수 있다.
2. `test_it2c_servo_undeclared_input_dc_drives_both_ports_together` (T-L12 2입력 변형)
   -- `ValueError: check_theta: θ 키가 스키마와 다르다 -- 빠짐 [], 남음 [('ln_idu', 'M2')]`. 이 test 의 `_two_stage(..., input_dc_v=None)` 는 입력 DC 미선언 차동 입력쌍에서
   `ln_idu` 를 M1 과 M2 둘 다 θ 로 준다. IT-1(DEC-106 입력 점)이 이미 병합된 base 에서 차동 입력쌍 두 포트는 한 점으로 묶여 같은 꼬리 입력쌍의 둘째 소자(M2)가 `parallel_vgs`
   종속이라 `ln_idu` 가 θ 성분이 아니다(`size_and_seal` 의 `check_theta` 가 거부 -- 측정 구성 코드에 닿기 전).
3. `test_window_ends_are_saturated[0.0]`·`[1.0]` (옛 test, 이 card 가 고칠 기존 test 표 `test_input_window.py` 의 'tol 3건'에 들어 있지 않음)
   -- `SealViolationError`(봉인 7, slack_v = −9.7e-4 V). 이 test 는 θ 정의역 끝 y = 0·1 이 커널 창 안이라 봉인 7 이 통과한다고 단언한다. IT-2b 의 창 끝 행은 `+tol_VDsat` 여유를 두어
   끝이 봉인 7 의 경계와 같았다. 이 card 는 창 행을 `VDS − VDSAT`(판정 여유 0)로 바꾸고(spec '재작성 범위' `region_rows` tol 항 삭제) 봉인 7 은 EO-1 까지 `+tol_VDsat` 로 둔다
   (spec '원래 취지와 다름' 넷째 줄, 봉인이 더 엄격). 그래서 정확한 창 끝 y = 0·1 의 점은 봉인 7 에서 거부된다. 같은 파일의
   `test_mid_window_ends_have_nonnegative_saturation_slack` 는 "봉인이거나 봉인 7 거부이면서 |slack_v|, |oracle| ≤ tol_v" 를 허용하도록 이미 쓰여 있다(IT-2b O-103).
4. `test_declared_input_dc_same_theta_seals` (옛 test, 'node.dc_window 포트 단언(:260, :355, :370, :410 부근)' 표의 마지막 줄)
   -- `KeyError: 'in'`. 입력 DC 선언 포트 `in` 의 `node.dc_window` 항목을 읽어 `input_status == "measured"` 를 단언한다. interface 'node.dc_window(바뀜)' 는 항목 = W4 뿌리 넷만(뿌리 아닌 입력 포트·선언 포트
   항목 없음)이라 이 항목은 없다. interface '고칠 기존 test'(빈칸 답 2 의 7번 표: 비뿌리·선언 포트 항목은 폐기 또는 cfg 로)에 해당하지만 :410 부근이 고쳐지지 않았다.

## 근거(oracle 또는 사용자 원문)

* 1: interface '공개 이름과 서명' 표 마지막 줄 `gmid_engine.graph | ViewSeed·ViewS1v | 칸 default_port: bool(기본 False) 추가`, 설계 41 §4.7-3b 'ICMR 전달 뷰 입력'(식별 = 새 칸 `ViewSeed.default_port`·`ViewS1v.default_port`;
   '`source` 는 `_constrained_keys` 가 DECLARED 출처로 gain·pm 키를 모으는 칸이라 다시 쓸 수 없다'). `ViewS1v.source` 를 만들면 소비자 0 인 칸(`fpga/CLAUDE.md` graph 규칙 '소비자 0 필드 금지')이고 interface 에 없는 결정이라
   코드 작성자가 정할 수 없다. 합쳐진 선언 씨앗의 출처는 `collect_views` 반환 `ViewSeed.source` 에서 확인할 수 있다(코드는 선언을 먼저 두고 같은 키는 `setdefault` 로 합친다 -- 위치: `graph/views.py`).
* 2: IT-1 판정 기록(작성자 ≠ 검증자)이 받은 DEC-106 입력 점 규칙과 base `tests/sizing/test_writer_plan.py` 의 입력 점 단언(입력쌍 둘째 소자 `parallel_vgs`, 폐기된 `test_it2b_os_k_no_same_dc_edge_between_input_ports` 사유 문구). θ 스키마가
   M2 의 `ln_idu` 를 성분으로 두지 않는다는 `check_theta` 메시지 자체가 oracle 이다.
* 3: spec '원래 취지와 다름' 넷째 줄 "봉인 7(+tol)과 창(여유 0)이 EO-1 병합 전까지 다른 경계를 쓴다. 봉인이 더 엄격해 fail-open 아님", sizing CONTRACT 14.6 (5) "y = 0·1 끝 점의 봉인 7 여유는 1차 외삽 오차만큼 음수일 수 있다",
   `test_mid_window_ends_have_nonnegative_saturation_slack` 의 O-103 허용 문구.
* 4: interface 'node.dc_window(바뀜)' 행, '필드 -- writer 하나' 표, 빈칸 답 2 의 7번 표 마지막 줄.

## 요청

1. T-S1V 두 test 의 `source` 단언을 `ViewSeed` 단계(`collect_views` 반환)로 옮기거나, interface 가 `ViewS1v.source` 칸과 그 소비자를 정하도록 결정해 달라(소비자 없이 칸을 만들 수 없다).
2. T-L12 2입력 변형의 θ 에서 M2 의 `ln_idu` 를 빼고 입력 점 규칙(`parallel_vgs`)에 맞춰 손 유도를 다시 해 달라(또는 입력 DC 선언 2입력 변형으로 바꿔 달라).
3. `test_window_ends_are_saturated` 를 `test_mid_window_ends_have_nonnegative_saturation_slack` 와 같은 허용 꼴(봉인이거나 봉인 7 거부이면서 slack 이 tol 안)로 바꾸거나 EO-1 까지 폐기해 달라.
4. `test_declared_input_dc_same_theta_seals` 의 `node.dc_window["in"]` 단언을 cfg(`node.dc_window_cfg`)로 옮기거나 지워 달라.

코드는 이 test 들을 통과시키려고 계약 밖 칸·우회를 만들지 않았다. 위 네 가지는 사람이 결정한다.
