# interface card: 20261002-d4-delete-unwired

생성: `tools/gates/interface_card.py`(05-role-separation §11.1). 본문 코드는 넣지 않는다(DEC-38).

## 관찰 가능한 계약

| 모듈 | 심볼 | 시그니처 |
|---|---|---|
| `sizing_recipe` | `_invert_gm_id_for_current` | `def _invert_gm_id_for_current(lut: 'GmIdLUT', current: float, L: float, vds: float, vsb: float, W: float, gm_id_bounds: tuple=(2.0, 30.0), tol: float=1e-09, max_iter: int=60) -> float` |
| `sizing_recipe` | `revalidate_finger_override` | `def revalidate_finger_override(ctx: SizingContext, lut_by_kind: dict, overrides: dict, metrics_specs: dict, constraints: list, gm_id_bounds: tuple=(2.0, 30.0)) -> dict` |
| `sizing_recipe` | `SemiEmpiricalGmIdLUT.vgs_for_gm_id` | `def vgs_for_gm_id(self, gm_id: float, L: float, vds: float, vsb: float=0.0) -> float` |
| `stick_diagram` | `find_hub_merge_candidates` | `def find_hub_merge_candidates(transistors: list) -> dict` |
| `stick_diagram` | `build_graph` | `def build_graph(transistors: list[Transistor]) -> StackGraph` |
| `stick_diagram` | `check_euler_condition` | `def check_euler_condition(g: StackGraph) -> EulerVerdict` |
| `stick_diagram` | `assign_finger_geometry` | `def assign_finger_geometry(sizing_results: dict, stack_groups: dict, area_priors: dict \| None=None, min_finger_w: float=1.0, max_finger_w: float=40.0) -> dict` |
| `stick_diagram` | `select_layout_tool` | `def select_layout_tool(matching_sensitivity: str, shares_node: bool, area_budget: str \| None=None) -> str` |
| `sizing_recipe` | `achievable_metric_bound` | `def achievable_metric_bound(topology_path: str, spec: dict, metric_name: str, sense: str='min', n_probes: int=3, slsqp_kwargs: dict \| None=None) -> dict` |
| `sizing_recipe` | `resolve_constraint_references` | `def resolve_constraint_references(constraints: list, spec: dict, topology_path: str='') -> list` |
| `sizing_recipe` | `solve_stacked_diode_pair` | `def solve_stacked_diode_pair(lut_up, L_up: float, ID_up: float, vsb_up: float, lut_lo, L_lo: float, ID_lo: float, W_bounds: tuple, vds_grid, constrain_up: bool=True, v_up_min: float=0.0) -> list` |
| `stick_diagram` | `audit_vertical_stack_id_euler_feasibility` | `def audit_vertical_stack_id_euler_feasibility(transistors: list, device_roles: dict, matching_pairs: list) -> dict` |
| `sizing_recipe` | `optimize_full_circuit_budget` | `def optimize_full_circuit_budget(topology_path: str, spec: dict, grid_points_per_theta: int=5, search_method: str='grid', slsqp_kwargs: dict \| None=None, stop_after_sizing: bool=False) -> dict` |
| `stick_diagram` | `search_shared_finger_w` | `def search_shared_finger_w(devices: dict, min_finger_w: float=0.4, max_finger_w: float=45.0, min_fingers: int=1, max_n: int=200, grid_step: float \| None=None) -> list` |
| `stick_diagram` | `propagate_topology_forced_currents` | `def propagate_topology_forced_currents(netlist: list, seed_currents: dict, mirror_ratios: dict) -> dict` |
| `sizing_recipe` | `load_derived_bounds` | `def load_derived_bounds(topology_path: str) -> dict` |
| `sizing_recipe` | `derived_bounds_path` | `def derived_bounds_path(topology_path: str) -> str` |
| `stick_diagram` | `check_multi_leaf_hub_parity` | `def check_multi_leaf_hub_parity(n_fingers_by_leaf: dict) -> MultiLeafHubParityVerdict` |
| `sizing_recipe` | `solve_diode_stack_current` | `def solve_diode_stack_current(lut: 'GmIdLUT', known_stack: list, target_voltage: float, i_bounds: tuple=(1e-09, 0.01), gm_id_bounds: tuple=(2.0, 30.0), tol: float=1e-09, max_iter: int=80) -> float` |
| `sizing_recipe` | `estimate_area_budget` | `def estimate_area_budget(kind: str, role_tag: str, area_priors: dict, n_fingers: int, finger_pitch_area: float=1.0, cold_start_alpha: float=0.65) -> float` |
| `stick_diagram` | `load_topology` | `def load_topology(json_path: str) -> tuple[list[Transistor], dict]` |
| `stick_diagram` | `run_topology_pipeline` | `def run_topology_pipeline(topology_json_path: str, sizing_overrides: dict, floorplan_hints: dict \| None=None, cell_groups: dict \| None=None) -> dict` |

### `sizing_recipe._invert_gm_id_for_current`

> 주어진 전류를 만드는 gm_id를 이분탐색으로 역산한다 — ID(gm_id) = IDu(gm_id)*(W/L)가
> gm_id에 단조감소(약반전=높은 gm_id=낮은 전류)이므로 성립. `solve_diode_stack_current()`의
> 내부 헬퍼(diode-stack 각 소자의 VGS를 구하려면 먼저 그 소자의 gm_id를 알아야 한다).

### `sizing_recipe.revalidate_finger_override`

> `overrides`(`{device_name: new_W}`, finger 반올림으로 실제 강제된 W)가 gm/ID
> 스펙을 깨지 않는지 재검증한다 -- L3(레이아웃)가 L4(사이징)에 피드백하는 지점.

### `sizing_recipe.SemiEmpiricalGmIdLUT.vgs_for_gm_id`

> 목표 gm/ID를 만족하는 VGS 자체가 필요한 호출자를 위한 공개 래퍼(`_solve_vgs()`와
> 동일 계산) — diode-stack KVL 역산(C엔진, `solve_diode_stack_current()`, §7.3.2,
> 배치 7-3/2026-07-31)처럼 VGS 절대값이 직접 필요한 새 호출자가 생겨 공개 인터페이스로
> 추가했다(이전엔 클래스 내부 전용이었다).

### `stick_diagram.find_hub_merge_candidates`

> `stack_id`/stage 배정을 무시하고, 극성 + 공유 단자(source 또는 drain) 하나만으로
> "이 소자들을 한 물리 행으로 합칠 수 있을까"의 **후보**를 전체 회로에서 찾는다.

### `stick_diagram.build_graph`

> §2.5.4 "최대한 섞는다"를 hierholzer()가 자동으로 따르게 만드는 지점이 바로 여기다.

### `stick_diagram.check_euler_condition`

> PDF/pptx가 명시한 3가지 오일러 조건을 그대로 판정한다:
> 0개 홀수차수 → circuit(닫힌 한붓그리기), 2개 → path(열린 한붓그리기), 4개 이상 → impossible.
> 연결성도 함께 확인한다(차수 조건을 만족해도 그래프가 끊겨 있으면 한 줄 diffusion으로 불가능).

### `stick_diagram.assign_finger_geometry`

> 배치 7-6(2026-07-31) — `size_transistor()`가 만든 raw `W`(사이징 결과)와
> `derive_stack_groups()`가 만든 stack 후보를 이어 `run_topology_pipeline()`이 요구하는
> `sizing_overrides`(`{name: {"n_fingers","finger_w","w","stack_id","l"}}`)를 자동 구성한다
> — bootstrapping 문제(`search_stack_finger_w()`/`search_unit_cell_sizing()` 둘 다 "맞출
> 참조값"이 이미 있어야 동작하는데, 맨 처음 stack엔 맞출 대상이 없음)를 seed 선택으로
> 해결한다.

### `stick_diagram.select_layout_tool`

> 배치 7-4b(2026-07-30/31), **2026-08-05(세션10) L1 하드컷** — `audit_row_split()`의
> kind→게이트 매핑(§2.6/§2.7 실측 기준)을 구성(construction) 단계에서도 쓸 수 있도록 뽑은
> 함수. 세션10에서 `kind`(`current_mirror`/`current_matched`/`diff_pair`/`branch_symmetric`)
> 문자열 하나 대신 L1이 분해한 두 독립 축을 직접 받도록 시그니처를 바꿨다(하위호환 shim
> 없음, kind 문자열은 더 이상 받지 않는다):
> - `matching_sensitivity`(축C, 선언값): `"offset"`이면 offset/CMRR 민감도 때문에
>   `common_centroid_layout`이 무조건 필수(구 `diff_pair`).
> - `shares_node`(축B, `shares_diffusion_node()`로 계산): `matching_sensitivity=="ratio"`인
>   쌍 중 source/drain을 공유하면(구 `current_mirror`/`current_matched`) 미러비 오차
>   전파만 관심사라 `interdigitate_layout`으로 충분(§2.7) — 공유 안 하면(구
>   `branch_symmetric`) interdigitation 자체가 그래프상 불가능해 `common_centroid_layout`이
>   필수.

### `sizing_recipe.achievable_metric_bound`

> `metric_name`이 **나머지 선언된 제약을 전부 만족하면서** 실제로 도달하는 값을 잰다.

### `sizing_recipe.resolve_constraint_references`

> constraint의 **임계값 참조**를 실제 값으로 치환한다. 소비자는 기존대로 `c["value"]`만
> 읽으면 된다(`_build_theta_evaluator()`가 부르는 유일한 치환 지점).

### `sizing_recipe.solve_stacked_diode_pair`

> **적층 diode 두 개의 vds를 함께 푼다**(2026-09-09, B25, 사용자 승인).

### `stick_diagram.audit_vertical_stack_id_euler_feasibility`

> 2026-08-10 세션26 후속(2) K-3에서 발견된 `cmfb_tail`류 문제를 정면으로 잡는
> audit -- `audit_vertical_stack_id_vs_kcl()`(전기적 정합성)과는 다른 질문에 답한다:
> **declared `vertical_stack_id` 그룹 하나가 그 자체로 오일러 실현 가능한가**.

### `sizing_recipe.optimize_full_circuit_budget`

> 배치 7-3d/7-5 — spec(topology.json 경로 + design spec)만 받아 instance.json에 바로
> 옮길 수 있는 완성된 결과를 반환하는 **단일 진입점 harness**(2026-07-31 확장,
> do.md §10 "spec→instance.json 전체 workflow"를 실제로 실행 가능한 함수 하나로 묶음).

### `stick_diagram.search_shared_finger_w`

> §4.2/Case B — 여러 stage에 걸친 소자들이 **하나의 공통 finger_w**를 쓰도록(=행 높이를
> 통일해 좌우로 나란히 배치할 수 있도록) finger_w 후보를 찾는다. `search_stack_finger_w()`
> (Case A)의 정반대 방향 자매 함수: 거기서는 n_fingers를 고정하고 finger_w를 stack마다
> 다르게 찾았는데, 여기서는 finger_w 하나를 고정하고 n_fingers가 stage마다 자유도다.

### `stick_diagram.propagate_topology_forced_currents`

> A엔진(§7.3.2) — 위상(그래프 구조)만으로 100% 결정되는 전류를 두 가지 전파 규칙으로
> 고정점(fixed-point)까지 반복 전파한다:

### `sizing_recipe.load_derived_bounds`

> 사이드카를 읽는다. 없으면 `{}`(호출자가 '없음'을 판단한다).

### `sizing_recipe.derived_bounds_path`

> 유도된 임계값 사이드카 파일 경로 -- `<topology>.derived.json`.

### `stick_diagram.check_multi_leaf_hub_parity`

> hub 하나에 leaf가 N개(N≥2) 달린 구조(각 leaf = 서로 다른 소자 하나, 그 소자의
> finger 개수가 `n_fingers_by_leaf`)가 **finger 개수를 그대로 실현했을 때** 한붓그리기
> 가능한지를 그래프를 만들지 않고 공식으로 빠르게 판정한다(설계 공간 탐색 시 여러 k
> 후보를 빠르게 스크리닝하는 용도 — 최종 채택 전에는 반드시 `build_graph()`+
> `check_euler_condition()`으로 재확인할 것, 이 함수는 그 결과와 항상 일치함을 self-test로
> 직접 검증했다).

### `sizing_recipe.solve_diode_stack_current`

> C엔진(§7.3.2) — 직렬 diode-connected 스택(`find_diode_stacks()`가 찾아낸 경로, 예:
> M8->M11a->M11b)이 공통 branch 전류 Ib(A엔진의 직렬-스택 원칙에 따라 스택 내 전부 동일
> 전류)로 흐를 때, 각 소자 VGS의 합이 `target_voltage`(예: 이미 B엔진으로 확정된 참조
> 소자의 Vgs)와 같아지는 Ib를 이분탐색으로 역산한다("배치 7-3c Level5: Ib = Vg15 KVL
> 루프 해").

### `sizing_recipe.estimate_area_budget`

> 배치 7-4b 확장(2026-07-31) — `select_layout_tool()`의 `area_budget` 인자를 "맨손으로
> 찍는" 대신 근거 있게 계산하는 harness. 디지털의 `gate_count = 면적/NAND2 면적` 개념을
> 아날로그에 맞게 각색(문헌: 1D/2D 배치 모델의 가중평균 `A ≈ (1-α)·A_1D + α·A_2D`) —
> `n_fingers`(이미 사이징 결과)만으로 정해지는 `A_1D = n_fingers * finger_pitch_area`
> (컴팩션 없는 1D 배치, 상한)와, `pack_floorplan_grouped()`가 실제 instance마다 내놓는
> `packing_density`를 역할별로 누적한 실측 평균으로 정해지는 `A_2D = A_1D / packing_density`
> (2D 컴팩션 반영 추정) 사이를 잇는다.

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
