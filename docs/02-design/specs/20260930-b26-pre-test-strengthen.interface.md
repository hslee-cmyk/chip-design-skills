# interface card: 20260930-b26-pre-test-strengthen

> **[상태 표지 2026-10-29] 실행·병합 완료 기록 -- 현행 규칙·절차 아님.** 판정 기록 `.ai/verification/20260930-b26-pre-test-strengthen.json`(FAIL 0)이 있고 이 card의 커밋은 master에 병합됐다. 옛 계획 Phase 3(모듈 분할) card이고 Phase 3은 폐기됐다(계획 N6.1 '옛 Phase 처리' 3행 -- 새 엔진은 처음부터 패키지로 나뉘고 옛 B26-1은 부품으로 이식). 본문의 spec card·interface card·auditor 판정(V1~V10)·DEC-40 승인·R1 절차는 DEC-86으로 폐기했다(계획 N3.12·N4.2, DEC-40 행) -- 현행 완료 조건은 계획 N6.3이다. 본문의 `A`(`skills/analog-gmid-design/assets`) 아래 옛 엔진·test는 `skills/analog-gmid-design/legacy/`로 옮겨졌고(`60727b06`) 새 test 체계(`gmid_engine/tests/`)에서 돌지 않는다. card LT-1(DEC-99)이 `legacy/`를 지운 뒤에는 tag `legacy-final`에만 남는다. 본문의 `device_roles` 등 topology 태그 입력은 옛 엔진 태그 동작을 고정한 test 입력이다 -- topology 태그는 DEC-99로 저장소 데이터에서 지운다. 본문은 기록이며 덧대지 않는다(O-169).

생성: `tools/gates/interface_card.py`(05-role-separation §11.1). 본문 코드는 넣지 않는다(DEC-38).

## 관찰 가능한 계약

| 모듈 | 심볼 | 시그니처 |
|---|---|---|
| `sizing_recipe` | `size_transistor` | `def size_transistor(gm: float, gm_id: float, L: float, lut: GmIdLUT, vds: float, vsb: float=0.0) -> SizingResult` |
| `sizing_recipe` | `SemiEmpiricalGmIdLUT.gm_gds_ratio` | `def gm_gds_ratio(self, gm_id: float, L: float, vds: float, vsb: float=0.0) -> float` |
| `stick_diagram` | `build_stick_diagram` | `def build_stick_diagram(transistors: list[Transistor], matching_pairs: list \| None=None) -> dict` |
| `sizing_recipe` | `optimize_full_circuit_budget` | `def optimize_full_circuit_budget(topology_path: str, spec: dict, grid_points_per_theta: int=5, search_method: str='grid', slsqp_kwargs: dict \| None=None, stop_after_sizing: bool=False) -> dict` |
| `stick_diagram` | `repair_matching_safety` | `def repair_matching_safety(rows: dict, matching_pairs: list, pair_sensitivity: dict \| None=None, max_iter: int=3, relaxed_pairs: set \| None=None) -> tuple` |
| `stick_diagram` | `common_centroid_layout` | `def common_centroid_layout(transistors: list, n_rows: int \| None=None, max_candidates: int=24) -> dict` |
| `sizing_recipe` | `run_matching_safety_with_finger_growth` | `def run_matching_safety_with_finger_growth(rows: dict, matching_pairs: list, pair_sensitivity: dict, ctx: SizingContext, lut_by_kind: dict, metrics_specs: dict, constraints: list, gm_id_bounds: tuple=(2.0, 30.0), min_fingers: int=2, max_rounds: int=5, allow_layout_relaxation: bool=True) -> dict` |
| `sizing_recipe` | `apply_and_revalidate_pair_adjustment` | `def apply_and_revalidate_pair_adjustment(transistors: list, matching_pairs: list, ctx: SizingContext, lut_by_kind: dict, metrics_specs: dict, constraints: list, gm_id_bounds: tuple=(2.0, 30.0), max_candidates: int \| None=None) -> dict` |
| `stick_diagram` | `find_min_crossover_layout_with_branch_composite` | `def find_min_crossover_layout_with_branch_composite(transistors: list, matching_pairs: list, pair_sensitivity: dict \| None=None) -> dict` |
| `stick_diagram` | `run_full_circuit_audit_from_topology` | `def run_full_circuit_audit_from_topology(topology_json_path: str, box_shape_checks: dict \| None=None, row_width_tol: float=1.5, accept_fail_blocks: set \| None=None) -> AuditResult` |
| `sizing_recipe` | `resolve_stack_layout` | `def resolve_stack_layout(transistors: list, matching_pairs: list, device_roles: dict, stack_groups_override: dict \| None=None) -> dict` |
| `stick_diagram` | `refine_differential_and_mirror_relations` | `def refine_differential_and_mirror_relations(transistors: list, inputs=(), outputs=(), feedbacks=(), biases=(), clocks=(), max_iterations: int=5) -> dict \| None` |
| `stick_diagram` | `derive_horizontal_stack_groups` | `def derive_horizontal_stack_groups(transistors: list, vertical_groups: dict, matching_pairs: list) -> dict` |
| `stick_diagram` | `propose_vertical_stack_id_gap_fill` | `def propose_vertical_stack_id_gap_fill(transistors: list, matching_pairs: list, device_roles: dict, inputs=(), outputs=(), feedbacks=(), biases=(), clocks=()) -> dict` |
| `stick_diagram` | `load_topology` | `def load_topology(json_path: str) -> tuple[list[Transistor], dict]` |
| `stick_diagram` | `find_differential_pair_candidates` | `def find_differential_pair_candidates(transistors: list, inputs=(), outputs=(), feedbacks=(), biases=(), clocks=()) -> dict \| None` |
| `stick_diagram` | `propose_device_roles_gap_fill` | `def propose_device_roles_gap_fill(transistors: list, device_roles: dict, matching_pairs_meta: list, compensation_stage_devices: list \| None=None, vds_theta_authoritative: set \| None=None, inputs=(), outputs=(), feedbacks=(), biases=(), clocks=()) -> dict` |
| `stick_diagram` | `find_structural_symmetry_candidates` | `def find_structural_symmetry_candidates(transistors: list, seed_net_pairs: dict, transform: str='mirror') -> StructuralSymmetryVerdict` |
| `sizing_recipe` | `GmIdLUT.gm_gds_ratio` | `def gm_gds_ratio(self, gm_id: float, L: float, vds: float, vsb: float=0.0) -> float` |

### `sizing_recipe.size_transistor`

> 방법론 식 1.17/1.18: ID = gm/(gm/ID),  W = L * ID / IDu.

### `sizing_recipe.SemiEmpiricalGmIdLUT.gm_gds_ratio`

(docstring 없음)

### `stick_diagram.build_stick_diagram`

> 어떤 회로든(트랜지스터 리스트) 입력으로 받아 stack별 StickResult를 반환하는
> 최상위 엔트리 포인트. 이 함수 하나가 skill의 "결과물"인 stick diagram 출력이다.

### `sizing_recipe.optimize_full_circuit_budget`

> 배치 7-3d/7-5 — spec(topology.json 경로 + design spec)만 받아 instance.json에 바로
> 옮길 수 있는 완성된 결과를 반환하는 **단일 진입점 harness**(2026-07-31 확장,
> do.md §10 "spec→instance.json 전체 workflow"를 실제로 실행 가능한 함수 하나로 묶음).

### `stick_diagram.repair_matching_safety`

> 배치 7-4 — `audit_row_split()`이 FAIL한 matching pair에 대해 `select_layout_tool()`
> (배치 7-4b)이 고른 도구(`interdigitate_layout`/`common_centroid_layout`)로 그 pair가
> 속한 행을 재배치하고 재검증하는 걸 최대 `max_iter`회 반복한다.

### `stick_diagram.common_centroid_layout`

> N개(N>=2) 소자의 connectivity(`Transistor` 리스트 — 전부 같은 `source`를 hub로
> 공유하고 서로 다른 `drain`을 leaf로 가짐, `n_fingers`가 각 소자의 목표 개수)를 받아
> common-centroid 배치를 자동으로 찾는다.

### `sizing_recipe.run_matching_safety_with_finger_growth`

> `repair_matching_safety()`(stick_diagram.py, L1~L3, branch 복합 매칭 포함)가
> 3c(common-centroid)를 못 푸는 지점에 "매칭 목적 핑거증가"(위) 자동 수정 루프를 감싸
> 붙인다 -- `run_topology_pipeline_with_finger_fixup()`(euler용)과 대칭되는 구조,
> `stick_diagram.py`<->`sizing_recipe.py` 단방향 import 제약 때문에 여기 위치(동일 이유).

### `sizing_recipe.apply_and_revalidate_pair_adjustment`

> L3(`suggest_pair_finger_adjustments()`)의 제안을 L4(`revalidate_finger_override()`)로
> 자동 승인/거부하는 상위 오케스트레이션 -- 세션12/13이 각각 만든 두 엔진을 처음으로 잇는다
> (`.ai/context.md` 세션13 D절 "다음 확장 지점", 세션12 M3a 그룹 M9b/M18b 사례가 실제 동기).

### `stick_diagram.find_min_crossover_layout_with_branch_composite`

> **세션17 신설** -- `find_min_crossover_layout()`을 branch-인지형으로 감싸는
> wrapper(`find_min_crossover_layout()` 자체는 안 건드림, 완전히 별도 함수). 호출
> 전에 `_composite_collapse_for_crossover()`로 branch를 합성 소자로 뭉쳐서 crossover
> 짝짓기가 branch를 갈라놓을 수 없게 만들고(구조적 보장 -- 합성 소자는 그래프에서
> 원자 단위 edge 하나라 애초에 쪼갤 방법이 없다), 결과 segment의
> `transistor_sequence`를 실제 소자 이름으로 다시 펼쳐서 반환한다(`_layout_result_
> to_rows()`가 쓰는 것과 동일한 펼치기 패턴).

### `stick_diagram.run_full_circuit_audit_from_topology`

> `run_full_circuit_audit()`(§1.6)의 자동 로더 -- topology.json 경로 하나만 주면
> `devices`/`expected_counts`/`dispositions`를 `load_topology()`가 이미 읽은 정보에서
> 전부 자동으로 구성해 호출한다. 호출자가 connectivity를 별도 dict로 다시 손타이핑하거나
> (사고9 net-이름 드리프트의 근본원인 재발) 이미 topology.json `symmetry.dispositions`에
> 적힌 판단을 다시 옮겨적을 필요가 없다(세션20, `.ai/context.md` 참고).

### `sizing_recipe.resolve_stack_layout`

> B-5-3 설계(`.ai/context.md` 세션22~25) 중 실제로 비어있던 조각 하나만 채운다 --
> 2026-08-10 정밀조사(Explore 조사) 결과, B-5-3이 "새로 만들어야 한다"고 제안했던
> finger_w 탐색(`search_stack_finger_w()`)/오일러 재시도(`suggest_pair_finger_
> adjustments()`)/매칭 완화(`run_matching_safety_with_finger_growth()`)는 전부 이미
> 구현·배선돼 있었다(`assign_finger_geometry()`가 그룹별로 `search_stack_finger_w()`를
> 이미 호출하고, `run_topology_pipeline_with_finger_fixup()`/`run_matching_safety_
> with_finger_growth()`가 실패시 재시도까지 이미 오케스트레이션함) -- 진짜 빈 구멍은
> 이 함수들이 공통으로 입력받는 **1차 물리 그룹 분할 경계**(`stack_groups_geometry`,
> 지금까지 `geometry_colocation_union()`의 자동 추론 하나뿐이었다)를 사람이 선언한
> `vertical_stack_id`로 대체하는 부분뿐이었다.

### `stick_diagram.refine_differential_and_mirror_relations`

> `find_differential_pair_candidates()`(C-11)가 `inputs=` 선언 없이 순수
> connectivity로 찾아낸 differential pair 후보의 gate net을 **자동으로**
> `inputs=`에 승격해서 `find_verified_differential_and_mirror_relations()`를
> 재실행하는 오케스트레이션(`.ai/context.md` D절 item 0, 2026-08-07 사용자 지시로
> 세션24에 신설). 세션23까지는 이 승격을 사람이 손으로 한 번(`Voc`/`Voc_des`를
> 수동으로 `inputs=`에 넣어) 했을 뿐 코드화되어 있지 않았다.

### `stick_diagram.derive_horizontal_stack_groups`

> 2026-08-11(세션28 후반부) -- `vertical_stack_id`(전기적 VDD->GND 컬럼, 헤드룸/VDS
> 예산용)와 물리 레이아웃 행(같은 kind끼리 diffusion을 공유하는 오일러 trail 대상)이
> 애초에 서로 다른 두 개념이라는 사용자 통찰로 신설. 세션28 전반부는 `resolve_stack_
> layout()`이 `vertical_stack_id` 그룹을 그대로 `merge_layout_groups_by_matching_
> pairs()`에 넘겨 물리 레이아웃 그룹으로 썼는데, `vertical_stack_id`는 정의상 PMOS/NMOS
> 경계를 넘나든다(예: `output_stage_a`=class-AB 출력단, M15=pmos/M16=nmos가 한 전기적
> 컬럼) -- `build_graph()`의 kind 동질성 하드 게이트(같은 세션 신설)가 이걸 잡아냈다.

### `stick_diagram.propose_vertical_stack_id_gap_fill`

> 선언 안 된 소자가 **결합(union) 그룹** 안에서 이미 선언된 `vertical_stack_id`를
> 물려받는 제안을 만든다(2026-08-13 세션31, 사용자 요청 -- `two_stage_ota.topology.
> json`의 M1/M2/M6 gap을 손으로 추론했던 걸 재사용 가능한 함수로 코드화).

### `stick_diagram.load_topology`

> topology library JSON(`library/*.topology.json`)을 읽어 (transistors, meta) 반환.

### `stick_diagram.find_differential_pair_candidates`

> 구조적으로 매칭된 branch 쌍(`suggest_vertical_stack_composites()`의 composite
> 시퀀스가 완전히 같은 branch끼리 묶음, C-10과 동일 원리) 안에서, 서로 다른 위치의
> 소자쌍이 (1) 같은 kind, (2) 다른 gate(=mirror 아님), (3) **같은 non-rail source(진짜
> tail net)를 공유**하면 differential pair 후보로 판정한다.

### `stick_diagram.propose_device_roles_gap_fill`

> `symmetry.matching_pairs`/`device_roles`(`gm_id_role`/`L_role`/`headroom_role`)를 **netlist
> connectivity만으로** 제안한다(2026-08-14, `.ai/context.md` 세션32 I절 설계 + 다음 세션 실측
> 검증을 반영해 확정). `vertical_stack_id`는 제안하지 않는다 -- I-1의 `propose_vertical_stack_
> id_gap_fill()`이 이미 그 필드를 전담하고(같은 이유: mirror edge를 vsid 유니온에 안 쓰는 것과
> 동일 원칙), 이 함수와 역할이 겹치면 두 제안이 서로 다른 값을 낼 위험이 생긴다.

### `stick_diagram.find_structural_symmetry_candidates`

> 전역 구조 대칭 후보를 `seed_net_pairs`(이미 아는 net 대응 — 보통 differential I/O
> 포트나 vdd/gnd)에서 시작해 고정점까지 전파해 찾는다. `propagate_topology_forced_
> currents()`(A엔진, KCL 버전)와 정확히 같은 스타일의 반복 전파를 net/device 대응에
> 적용한 것 — 오늘 current_reuse_telescopic_ota에서 M8<->M17, M13<->M22, M11a-chain<->
> M20a-chain 같은 대응관계를 손으로 하나씩 재발견했던 작업을 이 함수 하나로 대체한다.

### `sizing_recipe.GmIdLUT.gm_gds_ratio`

> intrinsic gain gm/gds = (gm/ID)*VA. LUT의 GDS 열에서 유도(방법론 §2.5).

## 신규 시그니처

| 모듈 | 심볼 | 시그니처 |
|---|---|---|

## 변경 이력

- 2026-10-29 `cards/revise-1029`: 위 상태 표지만 더함 -- 본문 불변, 표지 전 원문 = `git show 052465ed:docs/02-design/specs/20260930-b26-pre-test-strengthen.interface.md`.
