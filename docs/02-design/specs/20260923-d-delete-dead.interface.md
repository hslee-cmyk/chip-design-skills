# interface card: 20260923-d-delete-dead

> **[상태 표지 2026-10-29] 실행·병합 완료 기록 -- 현행 규칙·절차 아님.** 판정 기록 `.ai/verification/20260923-d-delete-dead.json`(FAIL 0)이 있고 이 card의 커밋은 master에 병합됐다. 옛 계획 Phase 2(죽은 코드·DUP 정리) card이고 Phase 2는 폐기됐다(계획 N6.1 '옛 Phase 처리' 2행 -- 새 엔진은 모듈 지도 N3.10으로 처음부터 개념당 정본 하나). 본문의 spec card·interface card·auditor 판정(V1~V10)·DEC-40 승인·R1 절차는 DEC-86으로 폐기했다(계획 N3.12·N4.2, DEC-40 행) -- 현행 완료 조건은 계획 N6.3이다. 본문의 `A`(`skills/analog-gmid-design/assets`) 아래 옛 엔진·test는 `skills/analog-gmid-design/legacy/`로 옮겨졌고(`60727b06`) 새 test 체계(`gmid_engine/tests/`)에서 돌지 않는다. card LT-1(DEC-99)이 `legacy/`를 지운 뒤에는 tag `legacy-final`에만 남는다. 본문은 기록이며 덧대지 않는다(O-169).

생성: `tools/gates/interface_card.py`(05-role-separation §11.1). 본문 코드는 넣지 않는다(DEC-38).

## 관찰 가능한 계약

| 모듈 | 심볼 | 시그니처 |
|---|---|---|
| `sizing_recipe` | `converge_with_parasitics` | `def converge_with_parasitics(fT: float, C_external: float, gm_id: float, L: float, lut: GmIdLUT, vds: float, vsb: float=0.0, n_fingers: int=1, max_iter: int=10, tol: float=0.0001) -> SizingResult` |
| `sizing_recipe` | `slew_rate` | `def slew_rate(ID: float, C: float) -> float` |
| `sizing_recipe` | `SemiEmpiricalGmIdLUT.fT` | `def fT(self, gm_id: float, L: float, vds: float, vsb: float=0.0) -> float` |
| `sizing_recipe` | `lut_conditions_from_npz` | `def lut_conditions_from_npz(npz_data) -> dict` |
| `stick_diagram` | `suggest_headroom_stack_groups` | `def suggest_headroom_stack_groups(transistors: list, composites: list \| None=None, inputs=(), outputs=(), feedbacks=(), biases=(), clocks=()) -> dict \| None` |
| `stick_diagram` | `render_stick_diagram` | `def render_stick_diagram(result: StickResult) -> str` |
| `run_harness` | `derived_spec` | `def derived_spec(circuit_key: str, why: str, **overrides) -> dict` |
| `sizing_recipe` | `GmIdLUT.junction_cap` | `def junction_cap(self, L: float, W: float, n_fingers: int=1, V: float=0.0, CJ: float=1e-15, CJsw: float=1e-16, CJswg: float=3e-16) -> float` |
| `stick_diagram` | `load_topology` | `def load_topology(json_path: str) -> tuple[list[Transistor], dict]` |
| `stick_diagram` | `run_topology_pipeline` | `def run_topology_pipeline(topology_json_path: str, sizing_overrides: dict, floorplan_hints: dict \| None=None, cell_groups: dict \| None=None) -> dict` |

### `sizing_recipe.converge_with_parasitics`

> 방법론 §4.2 — 외부부하 C_external에 기생 CJD를 더해가며 수렴할 때까지 반복.

### `sizing_recipe.slew_rate`

> slew-rate = ID/C = omega_T/(gm/ID)  (방법론 식 6.10).

### `sizing_recipe.SemiEmpiricalGmIdLUT.fT`

> fT = gm/(2*pi*Cgg) — 방법론 §2.6, 준정적 검증에 사용.

### `sizing_recipe.lut_conditions_from_npz`

> LUT npz가 들고 있는 **측정 조건**(코너/온도)을 읽어 돌려준다(2026-09-08, A5).

### `stick_diagram.suggest_headroom_stack_groups`

> 2026-08-10(세션27) -- `suggest_vertical_stack_composites()`의 `composites`(idiom
> 경계)를 그대로 `device_roles.*.vertical_stack_id`로 옮기면 헤드룸(`allocate_stack_
> headroom()`) 배정이 깨질 수 있다는 걸 실측으로 발견하고 만든 후속 함수. 두 질문은
> 다르다 -- **composite**는 "이 소자들이 어떤 회로 idiom인가"(floating-battery,
> active-load 등, 문서화/`headroom_role` 힌트용으로 여전히 유효)에 답하고, 이 함수가
> 답하는 **헤드룸 그룹**은 "VDS 합이 vdd(또는 그 일부)가 돼야 하는 하나의 전기적
> 컬럼이 뭔가"에 답한다. 실제 사례(`current_reuse_telescopic_ota`): `M11a`/`M11b`
> (floating-battery composite)와 `M12`(active-load composite)는 같은 `chain`
> (`VDD-M11a-M11b-M12-GND`, 진짜 물리적 직렬)인데 서로 다른 composite라 서로 다른
> `vertical_stack_id`로 선언돼 있었다 -- `M11a`/`M11b`만으로 `allocate_stack_headroom()`
> 을 호출하면 cascode role만 있고 나머지를 배분할 'other' role이 없어 assert가 실패했다.

### `stick_diagram.render_stick_diagram`

> PDF 예제(예: `3 4 3 2 1 2 1 2 3 4 3` + 그 아래 M3/M2/M1/M2/M3 레이블 줄)와 같은 형식으로
> 출력한다.

### `run_harness.derived_spec`

> 정본에서 **명시한 항목만** 바꾼 spec(2026-09-10).

### `sizing_recipe.GmIdLUT.junction_cap`

> 드레인 접합 커패시턴스 CJD — Jespers Annex 2 jctCap() 공식 기반 근사(1차 견적).

### `stick_diagram.load_topology`

> topology library JSON(`library/*.topology.json`)을 읽어 (transistors, meta) 반환.

### `stick_diagram.run_topology_pipeline`

> `load_topology()` -> `sizing_overrides`로 소자별 layout 필드(n_fingers/finger_w/w/
> stack_id — **필수**, 사이징+finger 배분이 끝난 뒤에만 이 함수를 의미 있게 호출할 수 있다)
> 덮어쓰기 -> `check_finger_width_compatibility()`(§3.5, **세션18 배선** — W가 finger_w의
> 정수배가 아니면 물리적으로 존재할 수 없는 요구라 여기서 즉시 `ValueError`, 아래 euler
> 분석은 이 게이트를 통과해야만 의미가 있다) -> `split_into_stacks()`로 스택(=기본 물리
> 행 후보) 구성 -> §1.6/§1.7이 정한 순서 그대로: 행별 Euler 유효성 -> `check_box_shape()`
> -> `audit_row_split()`(matching-safety, `symmetry.matching_pairs`의 kind 사용) ->
> `pack_floorplan_grouped()` -> `check_stick_diagram_coverage()`.

## 신규 시그니처

| 모듈 | 심볼 | 시그니처 |
|---|---|---|

## 변경 이력

- 2026-10-29 `cards/revise-1029`: 위 상태 표지만 더함 -- 본문 불변, 표지 전 원문 = `git show 052465ed:docs/02-design/specs/20260923-d-delete-dead.interface.md`.
