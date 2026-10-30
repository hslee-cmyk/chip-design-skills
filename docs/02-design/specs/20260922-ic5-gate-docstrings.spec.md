---
id: 20260922-ic5-gate-docstrings
phase: 1
evidence_type: red-green
gate_change: no
activated_ic_case: IC5:
approval: 20260922-10-test-separation-design
---

> **[상태 표지 2026-10-29] 실행·병합 완료 기록 -- 현행 규칙·절차 아님.** 판정 기록 `.ai/verification/20260922-ic5-gate-docstrings.json`(FAIL 0)이 있고 이 card의 커밋은 master에 병합됐다. 옛 계획 Phase 1 test 분리 card이고 Phase 1은 폐기됐다(계획 N6.1 '옛 Phase 처리' 1행; N3.11 'TS0~TS6 폐기'). 본문의 spec card·interface card·auditor 판정(V1~V10)·DEC-40 승인·R1 절차는 DEC-86으로 폐기했다(계획 N3.12·N4.2, DEC-40 행) -- 현행 완료 조건은 계획 N6.3이다. 본문의 `A`(`skills/analog-gmid-design/assets`) 아래 옛 엔진·test는 `skills/analog-gmid-design/legacy/`로 옮겨졌고(`60727b06`) 새 test 체계(`gmid_engine/tests/`)에서 돌지 않는다. card LT-1(DEC-99)이 `legacy/`를 지운 뒤에는 tag `legacy-final`에만 남는다. 현행 계획 N4.1의 IC5 강제 test는 새 엔진 담당 패키지 test 폴더에 새 API로 다시 쓴다(N4.1 머리·N3.11 -- 옛 `contracts/` 폴더는 만들지 않는다). 이 card의 구현은 옛 엔진용이며 IC5 충족 근거가 아니다. 본문은 기록이며 덧대지 않는다(O-169).

## 의도

IC5(계획 N4.1 '게이트 사각'): 게이트 함수 docstring에 "검사하지 않는 것" 절과 `영역:` 한 줄(DEC-67, 값 규칙은 `00-common` §5 + 개정 C1
`없음(배치)`)을 필수로 한다. C6이 둔 뼈대 `contracts/test_ic5.py::test_gate_docstring_declares_blind_spots`를 실제 검사로 바꾸고, 현존
21개 게이트에 두 줄을 더한다. 정본 명세는 design `10-test-separation` v1.2 §5.6(대상·형식·영역 표)·§6.6·§9 C7 행. A = `skills/analog-gmid-design/assets`.

## 관찰 가능한 계약

1. 대상 = 소스 분류 파일(`A/*.py`, `workspaces/run_harness.py`)에서 이름이 `^(check_|verify_|validate_|audit_|reject_|require_)` 또는 `^load_.*_checked$`인 함수·메서드 전부(모든 깊이). 현존 21개(design §5.6 표): `audit_current_forced.audit_topology`, `sizing_recipe.check_quasi_static`·`audit_l_sharing_consistency`·`audit_vsb_consistency`·`validate_no_legacy_vs_key`·`validate_metric_units`·`validate_theta_declaration_order`·`require_declared_spec_source`, `stick_diagram.check_mirror_symmetry`·`check_symmetry_dispositions`·`check_multi_leaf_hub_parity`·`audit_vertical_stack_id_vs_kcl`·`audit_theta_root_direction`·`require_device_roles_reviewed`·`audit_vertical_stack_id_euler_feasibility`·`check_finger_width_compatibility`·`check_euler_condition`·`check_box_shape`·`check_walk_sequence`·`check_stick_diagram_coverage`·`audit_row_split`.
2. 모든 대상의 docstring(`inspect.cleandoc`)이 design §5.6 형식을 만족한다: `검사하지 않는 것:`으로 시작하는 줄 1개 이상(내용 있음), `영역:`으로 시작하는 줄 정확히 1개이고 §5.6 정규식(`없음(스키마)`·`없음(배치)`·`dc`·`ac_struct`·`ss`·`ls` 조합)에 맞는다.
3. 표의 21개는 영역 값이 design §5.6 표와 같다(값 집합, 쉼표 순서 무관).
4. 함수 본문은 바뀌지 않는다: 바뀐 함수마다 docstring을 뺀 `ast.dump`가 base와 같다.

## 신규 시그니처

| 모듈 | 심볼 | 시그니처 |
|---|---|---|

## 판정 유형 근거

red-green: base에서 21개가 형식 위반이라 활성화한 test가 AssertionError로 실패하고, 병합본에서 통과한다(design §6.6).

## oracle 종류와 출처

(d) 계획서 N4.1 IC5, `00-common` §5(+C1 개정), design §5.6 표(영역 값). 허용 영역 문자열은 `00-common` §4에서 옮긴다.

## 거부해야 할 입력

test가 판정기의 거부를 합성 docstring으로 보인다: 절 없음, `영역:` 두 줄, 허용 밖 값(`영역: dc_ac`).

## library 회로 적용 여부

해당 없음(docstring).

## 무동작 판정 입력(무발동 값)

해당 없음.

## 재현할 수치

없음.

## 결정 필요 항목

없음.

## 변경 이력

- 2026-10-29 `cards/revise-1029`: 위 상태 표지만 더함 -- 본문 불변, 표지 전 원문 = `git show 052465ed:docs/02-design/specs/20260922-ic5-gate-docstrings.spec.md`.
