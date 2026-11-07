---
id: 20261106-jc1
spec_card: docs/02-design/specs/20261106-jc1.spec.md
test_id: skills/analog-gmid-design/gmid_engine/tests/metrics/test_sensitivity.py::test_r2_miller_sensitivities_not_trivial
test_id: skills/analog-gmid-design/gmid_engine/tests/metrics/test_ss_evaluate.py::test_s12_junction_change_recomputes_ss_blocks_only
test_id: skills/analog-gmid-design/gmid_engine/tests/metrics/test_ss_linearize.py::test_vgs_min_g3_dc_finger_only_difference_reuses
test_id: skills/analog-gmid-design/gmid_engine/tests/metrics/test_ss_linearize.py::test_values_old_lut_secant_and_cap_fallback
test_id: skills/analog-gmid-design/gmid_engine/tests/metrics/test_ss_linearize.py::test_gmb_secant_differs_from_column
test_id: skills/analog-gmid-design/gmid_engine/tests/metrics/test_ss_linearize.py::test_lut_content_changes_input_version
---
## 문제의 test

code 커밋(card 범위 그대로 구현) 뒤 O-229 범위(metrics·core·lut/test_lut_set·structure·generality·convergence·search/test_canonical_order·sizing/test_s2_values)에서 남는 red는 아래 6개뿐이다(나머지는 통과). 6개 모두 엔진 결함이 아니라 test 기대가 card·정의와 어긋난 것으로 판단한다. 엔진은 고치지 않았다(card 계약과 다르게 맞추면 거짓 green).

1. `test_sensitivity.py::test_r2_miller_sensitivities_not_trivial` -- `assert n_live == 10`. `LUT_PARAMETERS`가 card 완료 (10)에 따라 8열(cdb·csb 추가)이 되면 이 Miller 변형에서 단위 스탬프가 살아있는 파라미터가 13개다(`kw` 사전은 이미 8열 이름을 쓰는데 합계 상수만 6열 시절 10으로 남음). 실측: `13 == 10` 실패.
2. `test_ss_evaluate.py::test_s12_junction_change_recomputes_ss_blocks_only` -- `temp_c`만 바꾼 묶음에서 블록 계수 `[ss_dev, metrics_ss, metrics_dc]`를 `[1, 1, 0]`으로 기대. 새 정의(DEC-91·DEC-107)에서 접합 값은 온도를 읽지 않으므로(같은 파일 `test_ss_linearize.py::test_s12_temp_change_recomputes_once_same_bundle_reuses`의 docstring도 '접합 값은 온도를 읽지 않아 값은 그대로') `ss_dev` 입력 버전만 바뀌고 출력 값은 같아 `metrics_ss` 입력 버전이 그대로다. 실측 `[1, 0, 0]`. BSIM4 온도 보정이 있던 시절의 기대다.
3. `test_ss_linearize.py::test_vgs_min_g3_dc_finger_only_difference_reuses` -- 서로 다른 두 스냅샷(`s_a`, `s_b` -- 따로 만든 스냅샷)에 같은 donors·counters로 `ss_dev`를 부르고 행 `(calls, reuses, grafts, replays, computes, recomputes_same_input) == (2, 1, 0, 0, 1, 0)`을 단언. 서로 다른 스냅샷이면 graph reuse(같은 객체 `is`)가 아니라 S3 graft가 정본 경로라 실측은 `(2, 0, 1, 0, 1, 0)`이다. card 계약은 '둘째 계산 0(재사용)'(computes 1, 둘째 계산 0)이며 그것은 성립한다. 같은 스냅샷 두 번을 부르는 G-4(`:281` 꼴)만 `reuses == 1`이다.
4. `test_ss_linearize.py` `lut_b` 사용 test 3개(`test_values_old_lut_secant_and_cap_fallback`, `test_gmb_secant_differs_from_column`, `test_lut_content_changes_input_version`) -- `lut_b = load_lut_v2(slice_gmbs=False, cap_cgb=False)`는 기준 폭 표에 CGS 열은 있고 CGB 열만 없다(docstring: '접합 항은 CGS·CDD·CSS 열이 있어 계산된다'). 이 표에서는 `lut.caps`가 `cap_model == "cgg_minus_cgd_at_gs"`로 `Caps.cgs = cgg − cgd`를 낸다(CGS 열을 읽지 않음, `lut/cap_query.py` -- card가 '변경 0, 갈래 유지'로 못박은 파일). interface §1 4의 `csb = (c.css − c.cgs)·r_s`를 그대로 구현하면 csb = (CSS − (CGG − CGD))·r_s이고 이 toy에서는 음수(−2.56e-16, M2 단자 s)라 수동성 관문 `junction_cap_negative`가 정지한다. test는 같은 표에서 `csb = (CSS − CGS 열)·r_s > 0`을 기대한다.

## 근거(oracle 또는 사용자 원문)

- 1: spec card 완료 10(a)·`LUT_PARAMETERS == (..., "cdb", "csb")`(interface §6). 숫자 10은 6열의 합이었다.
- 2: 같은 test 파일 `test_ss_linearize.py` S-12 docstring('접합 값은 온도를 읽지 않아 값은 그대로'), interface §2 `JunctionSource(lut_rule_decl, reference, temp_c)` -- temp_c는 `ss_dev` 입력 버전에만 든다(온도 보정 식 삭제, spec 의도·범위 3). 값이 같으면 하류 `metrics_ss` 입력 버전도 같다(graph reuse 정의).
- 3: 계획·CLAUDE.md '재사용 두 길' -- graph reuse(같은 입력 버전 = 같은 스냅샷에 이미 있음)와 S3 graft((블록, 분할, 입력 버전) 색인). 별개 스냅샷은 graft. card 완료 6 '`dc_finger`만 다른 스냅샷 `ss_dev` 재사용'의 관찰은 computes(둘째 0)이다.
- 4: interface §1 열 판별 2 '`CGS` 열 없음 → `lut_column_unavailable`{column "CGS"} (CGB 결손과 섞지 않음 -- CGS 대신 CGG − CGD를 쓰지 않는다)'와 4 'csb = (c.css − c.cgs)' 사이에 틈이 있다. `caps`는 CGS·CGB 둘 중 하나라도 없으면 `cgs = cgg − cgd` 대체값을 낸다. 즉 card 문언대로 구현하면 'CGB만 없는 표'에서 `c.cgs`가 CGG − CGD가 되어 'CGS 대신 CGG − CGD를 쓰지 않는다'를 어긴다. test는 반대로 CGS 열 값이 쓰인다고 가정했다. 둘 다 card 범위 안에서 정할 수 없다(`cap_query.py`는 card 범위 밖).

## 요청

- 1·2·3: test 기대를 고쳐 주세요 -- 1: 합계 13(또는 `n_live`를 열 목록에서 세는 식), 2: `[1, 0, 0]`(온도 불변 접합 값이므로 `ss_dev`만 재계산, 값이 같아 하류 재사용 -- 이 변화를 기록하는 단언으로), 3: `(2, 0, 1, 0, 1, 0)`(graft) 또는 같은 스냅샷 재사용 단언으로 교체.
- 4: 결정이 필요합니다(사람/오케스트레이터). 선택지: (a) card 정정 -- CGS 열이 있고 CGB만 없는 표를 허용하려면 접합이 읽는 CGS 열을 `caps`가 따로 내도록 `lut/cap_query.py`(`Caps`)를 card 범위에 넣는다(그러면 현 구현의 `c.cgs`를 그 칸으로 바꾸고 `lut_b` test는 그대로 통과). (b) 현 구현에 '`c.model`이 `lut_cgs_cgb`가 아니면 `lut_column_unavailable`{column CGS}'를 더하는 쪽으로 card를 정정하고 `lut_b` 3개 test는 이 toy에서 접합 정지를 기대하도록 고친다(물리·fail-closed 관점에서 대체값 CGG − CGD를 쓰지 않는다는 card 취지와 일치, 권고). 어느 쪽이든 현 코드는 card 문언 그대로이므로 정정 뒤 이 한 곳(`junction_at_vgs_min`)만 바뀐다.
