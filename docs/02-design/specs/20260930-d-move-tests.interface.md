# interface card: 20260930-d-move-tests

> **[상태 표지 2026-10-29] 실행·병합 완료 기록 -- 현행 규칙·절차 아님.** 판정 기록 `.ai/verification/20260930-d-move-tests.json`(FAIL 0)이 있고 이 card의 커밋은 master에 병합됐다. 옛 계획 Phase 2(죽은 코드·DUP 정리) card이고 Phase 2는 폐기됐다(계획 N6.1 '옛 Phase 처리' 2행 -- 새 엔진은 모듈 지도 N3.10으로 처음부터 개념당 정본 하나). 본문의 spec card·interface card·auditor 판정(V1~V10)·DEC-40 승인·R1 절차는 DEC-86으로 폐기했다(계획 N3.12·N4.2, DEC-40 행) -- 현행 완료 조건은 계획 N6.3이다. 본문의 `A`(`skills/analog-gmid-design/assets`) 아래 옛 엔진·test는 `skills/analog-gmid-design/legacy/`로 옮겨졌고(`60727b06`) 새 test 체계(`gmid_engine/tests/`)에서 돌지 않는다. card LT-1(DEC-99)이 `legacy/`를 지운 뒤에는 tag `legacy-final`에만 남는다. 옮긴 `regression_runner.py`·`interleave_splits.py`는 지금 `legacy/tests/tools/`에 있다. 본문은 기록이며 덧대지 않는다(O-169).

생성: `tools/gates/interface_card.py`(05-role-separation §11.1). 본문 코드는 넣지 않는다(DEC-38).

## 관찰 가능한 계약

| 모듈 | 심볼 | 시그니처 |
|---|---|---|
| `sizing_recipe` | `optimize_multistage` | `def optimize_multistage(topology_fn, luts, L_candidates, VDS_candidates, gm_id_grid, objective: str='power', gain_min=None, w_max=None, max_iter: int=10, tol: float=0.001, shared_gm_id_groups: list \| None=None, stage_extra_feasible: list \| None=None, vds_kvl_groups: list \| None=None, vdd: float \| None=None, power_tolerance: float \| None=None)` |
| `sizing_recipe` | `_run_optimize_multistage_case` | `def _run_optimize_multistage_case(case: dict, luts_by_kind: dict) -> dict` |
| `sizing_recipe` | `run_regression_case` | `def run_regression_case(reference_json_path: str, case_key: str, rel_tol: float=0.01) -> RegressionVerdict` |
| `stick_diagram` | `find_interleaved_symmetric_splits` | `def find_interleaved_symmetric_splits(count_a: int, count_b: int) -> list` |

### `sizing_recipe.optimize_multistage`

> 제네릭 다단 회로 최적화 엔진 — **토폴로지가 바뀌어도 이 함수는 그대로 재사용**한다.

### `sizing_recipe._run_optimize_multistage_case`

> `"engine": "optimize_multistage"` case를 실제로 실행해 gms/stages를 반환한다.
> `case`는 reference JSON의 한 case 항목 그대로(`topology_fn`/`topology_fn_kwargs`/
> `lut_kinds`/`search`/`constraints`).

### `sizing_recipe.run_regression_case`

> `reference_json_path`(공정별 1개 JSON, 예: `sky130_regression_reference.json`)에서
> `case_key`로 지정된 검증 케이스를 로드해 실제로 실행하고 `expected`와 대조한다.

### `stick_diagram.find_interleaved_symmetric_splits`

> A, B가 서로 swap 파트너(예: pair_map={"A":"B","B":"A"})이고 **개별 finger 총합이
> 홀수**라 각자 단독으로는 좌우 절반씩 나눌 수 없을 때, 두 소자를 섞어 배치하면 전체 대칭을
> 살릴 수 있다 — folded cascode bottom row의 실제 사례(M9=3, M10=3, 둘 다 홀수)가 정확히
> 이 경우다: 원본 시퀀스 `...9xxoo99nno...`에서 M9는 좌1/우2, M10은 좌2/우1로 **불균등하게**
> 나뉘어 있지만, 두 소자가 서로의 불균형을 정확히 상쇄해 전체는 대칭이 된다.

## 신규 시그니처

| 모듈 | 심볼 | 시그니처 |
|---|---|---|
| `regression_runner` | `*` | 신규 모듈 `A/tests/tools/regression_runner.py`(엔진에서 이관, 시그니처는 관찰 가능한 계약의 기존 함수와 같다) |
| `interleave_splits` | `*` | 신규 모듈 `A/tests/tools/interleave_splits.py`(같음) |

## 변경 이력

- 2026-10-29 `cards/revise-1029`: 위 상태 표지만 더함 -- 본문 불변, 표지 전 원문 = `git show 052465ed:docs/02-design/specs/20260930-d-move-tests.interface.md`.
