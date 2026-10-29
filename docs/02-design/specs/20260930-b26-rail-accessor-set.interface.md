# interface card: 20260930-b26-rail-accessor-set

> **[대체 표지 2026-10-29 -- 검증 10 병합 가능 판정, master `07964dfe`] 대체됨 -- 현행 계획 N6.1 단위 2(`rail_declaration` 이식), 옛 엔진 card라 재동결 없음(착수하지 않음).** 이 card는 옛 엔진(`assets/sizing_recipe.py`·`stick_diagram.py`) Phase 3 card이고 code·test 커밋(`e92e6b84`·`212f76a9` 등)은 master에 병합되지 않았다(판정 기록 없음). 계획 N6.1 '옛 Phase 처리'가 Phase 3 모듈 분할을 폐기하고(DEC-86, 2026-10-07) '옛 B26-1은 부품으로 이식'으로 정했으며, 새 엔진은 `gmid_engine/authoring/rails.py`에 레일 선언 접근자를 둔다. 옛 엔진 삭제는 card LT-1(DEC-99). 본문은 기록이다(O-169).


생성: `tools/gates/interface_card.py`(05-role-separation §11.1). 본문 코드는 넣지 않는다(DEC-38).

## 관찰 가능한 계약

| 모듈 | 심볼 | 시그니처 |
|---|---|---|
| `stick_diagram` | `load_topology` | `def load_topology(json_path: str) -> tuple[list[Transistor], dict]` |
| `sizing_recipe` | `_load_full_topology_cached` | `def _load_full_topology_cached(topology_path: str) -> tuple` |
| `sizing_recipe` | `_topology_meta_cached` | `def _topology_meta_cached(topology_path: str) -> dict` |
| `sizing_recipe` | `compute_metric` | `def compute_metric(metric_spec: dict, ctx: SizingContext) -> float` |
| `sizing_recipe` | `l_sharing_classes` | `def l_sharing_classes(by_name: dict, meta: dict, matching_pairs=()) -> dict` |
| `stick_diagram` | `find_matching_candidates` | `def find_matching_candidates(transistors: list, idiom_matches: list \| None=None) -> dict` |
| `stick_diagram` | `find_differential_pair_candidates` | `def find_differential_pair_candidates(transistors: list, inputs=(), outputs=(), feedbacks=(), biases=(), clocks=()) -> dict \| None` |
| `stick_diagram` | `_diff_pair_layer1_groups` | `def _diff_pair_layer1_groups(transistors: list) -> dict` |
| `stick_diagram` | `_propose_gm_id_roles` | `def _propose_gm_id_roles(transistors, base_inputs, outputs, feedbacks, biases, clocks)` |
| `stick_diagram` | `_propose_L_roles` | `def _propose_L_roles(transistors, relations, base_inputs, outputs, feedbacks, biases, clocks)` |
| `stick_diagram` | `kcl_series_union` | `def kcl_series_union(netlist: list, matching_pairs: list) -> dict` |
| `stick_diagram` | `_kcl_and_matching_edges` | `def _kcl_and_matching_edges(transistors: list, matching_pairs: list) -> list` |
| `stick_diagram` | `audit_vertical_stack_id_vs_kcl` | `def audit_vertical_stack_id_vs_kcl(transistors: list, matching_pairs: list, device_roles: dict) -> dict` |
| `stick_diagram` | `propose_device_roles_gap_fill` | `def propose_device_roles_gap_fill(transistors: list, device_roles: dict, matching_pairs_meta: list, compensation_stage_devices: list \| None=None, vds_theta_authoritative: set \| None=None, inputs=(), outputs=(), feedbacks=(), biases=(), clocks=()) -> dict` |
| `sizing_recipe` | `true_current_mirror_groups` | `def true_current_mirror_groups(by_name: dict) -> list` |
| `stick_diagram` | `check_symmetry_dispositions` | `def check_symmetry_dispositions(transistors: list, matching_pairs: list, dispositions: dict \| None=None) -> SymmetryDispositionsVerdict` |
| `stick_diagram` | `run_full_circuit_audit` | `def run_full_circuit_audit(devices: dict, expected_counts: dict, dispositions: dict, box_shape_checks: dict \| None=None, row_width_tol: float=1.5, accept_fail_blocks: set \| None=None) -> AuditResult` |
| `stick_diagram` | `refine_differential_and_mirror_relations` | `def refine_differential_and_mirror_relations(transistors: list, inputs=(), outputs=(), feedbacks=(), biases=(), clocks=(), max_iterations: int=5) -> dict \| None` |
| `stick_diagram` | `propose_vertical_stack_id_gap_fill` | `def propose_vertical_stack_id_gap_fill(transistors: list, matching_pairs: list, device_roles: dict, inputs=(), outputs=(), feedbacks=(), biases=(), clocks=()) -> dict` |
| `stick_diagram` | `_kcl_branch_map` | `def _kcl_branch_map(devices: list) -> dict` |
| `stick_diagram` | `_branch_composite_pair` | `def _branch_composite_pair(a: str, b: str, devices_by_name: dict, matching_pairs: list)` |
| `stick_diagram` | `_composite_collapse_for_crossover` | `def _composite_collapse_for_crossover(transistors: list, matching_pairs: list, pair_sensitivity: dict \| None=None) -> tuple` |
| `stick_diagram` | `find_min_crossover_layout_with_branch_composite` | `def find_min_crossover_layout_with_branch_composite(transistors: list, matching_pairs: list, pair_sensitivity: dict \| None=None) -> dict` |
| `stick_diagram` | `repair_matching_safety` | `def repair_matching_safety(rows: dict, matching_pairs: list, pair_sensitivity: dict \| None=None, max_iter: int=3, relaxed_pairs: set \| None=None) -> tuple` |
| `sizing_recipe` | `resolve_stack_layout` | `def resolve_stack_layout(transistors: list, matching_pairs: list, device_roles: dict, stack_groups_override: dict \| None=None) -> dict` |
| `stick_diagram` | `run_full_circuit_audit_from_topology` | `def run_full_circuit_audit_from_topology(topology_json_path: str, box_shape_checks: dict \| None=None, row_width_tol: float=1.5, accept_fail_blocks: set \| None=None) -> AuditResult` |
| `sizing_recipe` | `_build_theta_evaluator` | `def _build_theta_evaluator(topology_path: str, spec: dict) -> dict` |
| `sizing_recipe` | `l_class_owners` | `def l_class_owners(by_name: dict, meta: dict, matching_pairs=()) -> dict` |
| `sizing_recipe` | `audit_l_sharing_consistency` | `def audit_l_sharing_consistency(by_name: dict, meta: dict, sized: dict, matching_pairs=(), tol: float=1e-12, classes: dict \| None=None) -> list` |
| `sizing_recipe` | `synthesize_l_class_thetas` | `def synthesize_l_class_thetas(by_name: dict, meta: dict, spec: dict, declared_thetas: list, matching_pairs=()) -> list` |
| `sizing_recipe` | `_metric_kcl_residual` | `def _metric_kcl_residual(spec: dict, ctx: SizingContext) -> float` |
| `sizing_recipe` | `optimize_full_circuit_budget` | `def optimize_full_circuit_budget(topology_path: str, spec: dict, grid_points_per_theta: int=5, search_method: str='grid', slsqp_kwargs: dict \| None=None, stop_after_sizing: bool=False) -> dict` |
| `sizing_recipe` | `run_topology_pipeline_with_finger_fixup` | `def run_topology_pipeline_with_finger_fixup(topology_json_path: str, sizing_overrides: dict, ctx: SizingContext, lut_by_kind: dict, metrics_specs: dict, constraints: list, floorplan_hints: dict \| None=None, cell_groups: dict \| None=None, gm_id_bounds: tuple=(2.0, 30.0), max_fixup_rounds: int=5) -> dict` |
| `sizing_recipe` | `run_matching_safety_with_finger_growth` | `def run_matching_safety_with_finger_growth(rows: dict, matching_pairs: list, pair_sensitivity: dict, ctx: SizingContext, lut_by_kind: dict, metrics_specs: dict, constraints: list, gm_id_bounds: tuple=(2.0, 30.0), min_fingers: int=2, max_rounds: int=5, allow_layout_relaxation: bool=True) -> dict` |
| `sizing_recipe` | `_fixup_euler_blocked_rows` | `def _fixup_euler_blocked_rows(rows: dict, matching_pairs: list, pair_sensitivity: dict, ctx: SizingContext, lut_by_kind: dict, metrics_specs: dict, constraints: list, gm_id_bounds: tuple=(2.0, 30.0), max_rounds: int=5) -> tuple` |
| `stick_diagram` | `run_topology_pipeline` | `def run_topology_pipeline(topology_json_path: str, sizing_overrides: dict, floorplan_hints: dict \| None=None, cell_groups: dict \| None=None) -> dict` |
| `stick_diagram` | `trace_vdd_to_gnd_branches` | `def trace_vdd_to_gnd_branches(transistors: list) -> dict` |
| `stick_diagram` | `trace_gnd_to_vdd_branches` | `def trace_gnd_to_vdd_branches(transistors: list) -> dict` |
| `stick_diagram` | `propose_theta_kcl_gap_fill` | `def propose_theta_kcl_gap_fill(transistors: list, matching_pairs_meta: list, ideal_sources: list \| None=None, compensation_stage_devices: list \| None=None, inputs=(), outputs=(), feedbacks=(), biases=(), clocks=()) -> dict` |
| `sizing_recipe` | `propagate_node_voltages` | `def propagate_node_voltages(by_name: dict, sized: dict, vdd: float, rail_hi=_DEFAULT_RAIL_HI, rail_lo=_DEFAULT_RAIL_LO, tol: float=1e-06, max_passes: int=50) -> NodeVoltageReport` |
| `sizing_recipe` | `derive_vsb_from_nodes` | `def derive_vsb_from_nodes(kind: str, source_net: str, nodes: dict, vdd: float, rail_hi=_DEFAULT_RAIL_HI, rail_lo=_DEFAULT_RAIL_LO)` |
| `sizing_recipe` | `node_pole_estimate` | `def node_pole_estimate(by_name: dict, sized: dict, spec: dict, only: set=None) -> dict` |
| `sizing_recipe` | `_hr_resolve_vertical_group` | `def _hr_resolve_vertical_group(env, vsid)` |
| `stick_diagram` | `_import_analog_grammar` | `def _import_analog_grammar(*module_names)` |

### `stick_diagram.load_topology`

> topology library JSON(`library/*.topology.json`)을 읽어 (transistors, meta) 반환.

### `sizing_recipe._load_full_topology_cached`

> `topology_path`의 connectivity(소자+passive_elements)를 캐시해서 돌려준다(세션21
> 신설, topology-무관 일반화). 캐시 키가 경로 문자열이라 4개 회로(`current_reuse_
> telescopic_ota`/`folded_cascode`/`nmcnr_amplifier`/`two_stage_ota`)를 같은 프로세스
> 안에서 오가도 각자 캐시된다.

### `sizing_recipe._topology_meta_cached`

> `load_topology()`가 자동채움까지 끝낸 `meta`를 캐시에서 준다(2026-09-10).

### `sizing_recipe.compute_metric`

> 이미 사이징 완료된 `ctx`(모든 소자의 ID/gm/gds/W/L 확정)에서 `metric_spec`이 지정한
> 값 하나를 읽어 계산한다 — `theta_value` 인자가 없다(metric은 자유값을 받는 게 아니라
> 이미 정해진 상태를 관찰만 하는 순수 함수이기 때문, §7.3.3 Q2). 등록 안 된 `type`은
> `_COMPENSATION_REGISTRY`/`_THETA_FEED_REGISTRY`와 동일하게 즉시 `ValueError`.

### `sizing_recipe.l_sharing_classes`

> **같은 L을 써야 하는 소자들**의 동치류(층1, 2026-09-10). `{root: [members]}`.

### `stick_diagram.find_matching_candidates`

> 구조적 신호만으로 matching **후보**(확정 아님)를 찾는다 — AI/설계자가 소자쌍을
> 일일이 수동으로 훑지 않도록 후보를 미리 좁혀주는 게 이 함수의 존재 이유다(토큰 절약).
> 자동 탐지 가능한 두 유형:

### `stick_diagram.find_differential_pair_candidates`

> 구조적으로 매칭된 branch 쌍(`suggest_vertical_stack_composites()`의 composite
> 시퀀스가 완전히 같은 branch끼리 묶음, C-10과 동일 원리) 안에서, 서로 다른 위치의
> 소자쌍이 (1) 같은 kind, (2) 다른 gate(=mirror 아님), (3) **같은 non-rail source(진짜
> tail net)를 공유**하면 differential pair 후보로 판정한다.

### `stick_diagram._diff_pair_layer1_groups`

> `find_matching_candidates()`의 `diff_pair` net-only 판정(같은 kind + 같은
> non-rail source + 다른 gate, role/idiom 분류 불필요)만 떼어낸 헬퍼 -- `find_
> differential_pair_candidates()`의 층위1 폴백 전용(중복 구현 방지, `find_matching_
> candidates()`의 W-일치 필터는 topology 저작 단계엔 아직 W가 없어 항상 통과한다).

### `stick_diagram._propose_gm_id_roles`

> `refine_differential_and_mirror_relations()`가 쓰는 내부 헬퍼 -- `topology.json`
> `device_roles`의 `gm_id_role`(`matching`/`gain`/`balanced` 중 이 프로젝트가 실제로
> 쓰는 두 값) 후보를 제안한다.

### `stick_diagram._propose_L_roles`

> `refine_differential_and_mirror_relations()`가 쓰는 내부 헬퍼 -- `topology.json`
> `device_roles`의 `L_role`(`mirror`=2.5*L_min | `bias_replica`=1.2*L_min) 후보를
> 제안한다.

### `stick_diagram.kcl_series_union`

> L2 축A(2026-08-05, 세션10 L1/L2 구현) — `derive_stack_groups()`를 KCL용/geometry용
> 두 함수로 분리한 것 중 KCL(축A, `sizing_recipe.py`의 `stack_groups_kcl`) 쪽. 두 규칙으로
> union-find 병합한다:

### `stick_diagram._kcl_and_matching_edges`

> `kcl_series_union()`이 union할 때 실제로 쓰는 것과 똑같은 두 종류의 edge(내부
> 2단자 net + declared `current_forced` matching_pairs)를 `(a, b, kind, detail)`
> 리스트로 재구성한다 -- `audit_vertical_stack_id_vs_kcl()`과
> `propose_vertical_stack_id_gap_fill()` 둘 다 같은 edge 정의를 써야 서로 어긋나지
> 않으므로(2026-08-13 세션31, N-way 조인트 스캔 때 만든 `_shared_current_groups_
> from_compensation()`와 같은 이유로 단일 정의로 분리) 원래 `audit_vertical_stack_id_
> vs_kcl()` 안에 있던 로직을 그대로 추출.

### `stick_diagram.audit_vertical_stack_id_vs_kcl`

> L2 축A(`kcl_series_union()`)와 declared `vertical_stack_id`(topology.json
> `device_roles`)가 서로 다른 질문에 답한다는 걸 2026-08-10 세션 대화에서 실측으로
> 확인한 뒤 만든 감사(audit) 도구 -- **탐색 입력이 아니라 사후 대조표**로 쓴다(대화
> 결론: `vertical_stack_id`로 KCL 탐색 범위를 좁히면 오히려 `M11b`/`M12`처럼 진짜
> 2단자 직렬 관계를 vsid 경계가 가로막아 놓친다, 실측 확인됨 -- 그래서 탐색기가
> 아니라 검증 대상으로 쓴다).

### `stick_diagram.propose_device_roles_gap_fill`

> `symmetry.matching_pairs`/`device_roles`(`gm_id_role`/`L_role`/`headroom_role`)를 **netlist
> connectivity만으로** 제안한다(2026-08-14, `.ai/context.md` 세션32 I절 설계 + 다음 세션 실측
> 검증을 반영해 확정). `vertical_stack_id`는 제안하지 않는다 -- I-1의 `propose_vertical_stack_
> id_gap_fill()`이 이미 그 필드를 전담하고(같은 이유: mirror edge를 vsid 유니온에 안 쓰는 것과
> 동일 원칙), 이 함수와 역할이 겹치면 두 제안이 서로 다른 값을 낼 위험이 생긴다.

### `sizing_recipe.true_current_mirror_groups`

> **진짜 전류미러** 그룹 -- 같은 `(kind, gate net, source net)`을 공유하는 소자 집합.

### `stick_diagram.check_symmetry_dispositions`

> `find_matching_candidates()`/`find_hub_merge_candidates()`는 **후보**만 낸다 — "이
> 회로 기능상 진짜 matching/병합인가"는 항상 판단(설계자/AI)이 남아 있는데, 그 판단이
> 조용히 누락(후보를 발견하고도 topology JSON `symmetry.matching_pairs`에 채택도, 명시적
> 기각도 안 하고 그냥 빼먹는 것)되는 걸 이 함수가 구조적으로 차단한다. `run_full_circuit_
> audit()`의 3번 체크("every matching/hub-merge candidate has a recorded disposition")와
> 정확히 같은 원리를 topology-authoring 단계(사이징 이전, `devices`/`expected_counts` 같은
> 무거운 인자 없이)에 맞게 경량화한 것이다.

### `stick_diagram.run_full_circuit_audit`

> 리포트를 "완료"로 선언하기 전 **반드시 이 함수 하나로** 전체 회로를 감사한다 —
> sub-block마다 따로 짠 1회용 검증 스크립트를 다시 만들지 않는다(이게 바로 이 함수가 막으려는
> 사고 패턴이다: bias-gen만 확인 → CMFB만 확인 → net 이름은 확인 안 함 → 다른 sub-block과
> 합쳐야만 보이는 매칭을 놓침, 이 순서로 실제 4번 반복됐다).

### `stick_diagram.refine_differential_and_mirror_relations`

> `find_differential_pair_candidates()`(C-11)가 `inputs=` 선언 없이 순수
> connectivity로 찾아낸 differential pair 후보의 gate net을 **자동으로**
> `inputs=`에 승격해서 `find_verified_differential_and_mirror_relations()`를
> 재실행하는 오케스트레이션(`.ai/context.md` D절 item 0, 2026-08-07 사용자 지시로
> 세션24에 신설). 세션23까지는 이 승격을 사람이 손으로 한 번(`Voc`/`Voc_des`를
> 수동으로 `inputs=`에 넣어) 했을 뿐 코드화되어 있지 않았다.

### `stick_diagram.propose_vertical_stack_id_gap_fill`

> 선언 안 된 소자가 **결합(union) 그룹** 안에서 이미 선언된 `vertical_stack_id`를
> 물려받는 제안을 만든다(2026-08-13 세션31, 사용자 요청 -- `two_stage_ota.topology.
> json`의 M1/M2/M6 gap을 손으로 추론했던 걸 재사용 가능한 함수로 코드화).

### `stick_diagram._kcl_branch_map`

> `devices`에 `kcl_series_union()`의 순수 자동발견 규칙(2단자 net, `matching_pairs`
> 강제병합 없음)만 돌려 `{소자명: branch 전체 소자명 리스트}`로 펼쳐 반환한다 --
> `repair_matching_safety()`의 branch 복합 매칭(세션16)이 "이 소자가 다른 소자와 물리적으로
> 같은 직렬 컬럼(예: 캐스코드 스택)을 이루는가"를 판단하는 데 쓴다. 이미 있는 `kcl_series_
> union()`(세션10 L2, `stack_groups_kcl`용)을 그대로 재사용할 뿐 새 그래프 로직은 없다.

### `stick_diagram._branch_composite_pair`

> 실패한 매칭쌍 (a,b)가 서로 다른 hub(source)를 써서 `interdigitate_layout()`/
> `common_centroid_layout()`을 직접 적용할 수 없을 때(세션15 A-3/세션16에서 확인된 한계 --
> 예: branch_symmetric인 M2a/M2b), 각자 속한 `kcl_series_union()` 직렬 branch가 서로
> 완전히 대응되는 거울 branch인지 확인한다 -- 대응되면(길이 2, hub쪽 소자끼리도 leaf쪽
> 소자끼리도 둘 다 선언된 matching_pairs) 그 branch 전체를 감싸는 합성(composite)
> `Transistor` 한 쌍을 만들어 반환한다: 이러면 두 composite가 (진짜 공유 hub인)
> 같은 source를 갖게 되어 기존 도구를 그대로 적용할 수 있다 -- "M1a+M2a를 하나의 소자처럼
> 다룬다"는 아이디어(세션16 사용자 제안)를 이미 있는 `kcl_series_union()`으로 구현한 것,
> 새 그래프 탐색 로직은 없다.

### `stick_diagram._composite_collapse_for_crossover`

> **세션17 신설** -- `find_min_crossover_layout()`을 부르기 전에 이 그룹의 branch
> (예: M1a-M2a 캐스코드 컬럼)를 `_branch_composite_pair()`로 미리 합성 소자 하나로
> 뭉친다. `repair_matching_safety()`가 `interdigitate_layout()`/`common_centroid_
> layout()`을 부르기 전에 이미 이렇게 하고 있는 것과 정확히 같은 이유 -- branch는
> 물리적으로 한 덩어리로 움직여야 하는데, `find_min_crossover_layout()`은 raw 개별
> 소자만 보면 그 사실을 전혀 모른다(사용자 확인, 세션17). 이걸 안 하면 crossover
> 짝짓기가 같은 branch의 두 소자를 서로 다른 segment로 갈라놓을 수 있다 -- M6 그룹이
> 지금까지 우연히 안 갈라진 것뿐, 구조적 보장이 아니었다.

### `stick_diagram.find_min_crossover_layout_with_branch_composite`

> **세션17 신설** -- `find_min_crossover_layout()`을 branch-인지형으로 감싸는
> wrapper(`find_min_crossover_layout()` 자체는 안 건드림, 완전히 별도 함수). 호출
> 전에 `_composite_collapse_for_crossover()`로 branch를 합성 소자로 뭉쳐서 crossover
> 짝짓기가 branch를 갈라놓을 수 없게 만들고(구조적 보장 -- 합성 소자는 그래프에서
> 원자 단위 edge 하나라 애초에 쪼갤 방법이 없다), 결과 segment의
> `transistor_sequence`를 실제 소자 이름으로 다시 펼쳐서 반환한다(`_layout_result_
> to_rows()`가 쓰는 것과 동일한 펼치기 패턴).

### `stick_diagram.repair_matching_safety`

> 배치 7-4 — `audit_row_split()`이 FAIL한 matching pair에 대해 `select_layout_tool()`
> (배치 7-4b)이 고른 도구(`interdigitate_layout`/`common_centroid_layout`)로 그 pair가
> 속한 행을 재배치하고 재검증하는 걸 최대 `max_iter`회 반복한다.

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

### `stick_diagram.run_full_circuit_audit_from_topology`

> `run_full_circuit_audit()`(§1.6)의 자동 로더 -- topology.json 경로 하나만 주면
> `devices`/`expected_counts`/`dispositions`를 `load_topology()`가 이미 읽은 정보에서
> 전부 자동으로 구성해 호출한다. 호출자가 connectivity를 별도 dict로 다시 손타이핑하거나
> (사고9 net-이름 드리프트의 근본원인 재발) 이미 topology.json `symmetry.dispositions`에
> 적힌 판단을 다시 옮겨적을 필요가 없다(세션20, `.ai/context.md` 참고).

### `sizing_recipe._build_theta_evaluator`

> `optimize_full_circuit_budget()`의 세타-무관 setup + `_evaluate(theta_values)` 평가
> 클로저를 그대로 추출한 헬퍼(2026-08-11 세션29, 순수 리팩터 -- 동작 변화 없음. warm-start
> (`derive_theta_dependency_graph()`/`presolve_warm_start()`)가 grid search 전체를 돌리지
> 않고 임의의 theta_values 한 점만 평가해야 해서 신설). `optimize_full_circuit_budget()`은
> 이 함수를 호출해 아래 반환값을 그대로 재사용한다 -- 내부 로직은 옮기기 전과 완전히 동일.

### `sizing_recipe.l_class_owners`

> 각 L 동치류의 **주인**을 정한다(층2). `{root: {...}}`.

### `sizing_recipe.audit_l_sharing_consistency`

> L 동치류 안에서 **L이 갈린** 곳을 찾는다(층0 게이트, 2026-09-10).

### `sizing_recipe.synthesize_l_class_thetas`

> **L 동치류의 공통 L을 theta로 파생**시킨다(층3, 2026-09-10). `[theta_spec, ...]`.

### `sizing_recipe._metric_kcl_residual`

> F엔진(2026-09-08, B8) — **내부 노드의 KCL 잔차** `|Sum I_into_node|` 중 최댓값(A).

### `sizing_recipe.optimize_full_circuit_budget`

> 배치 7-3d/7-5 — spec(topology.json 경로 + design spec)만 받아 instance.json에 바로
> 옮길 수 있는 완성된 결과를 반환하는 **단일 진입점 harness**(2026-07-31 확장,
> do.md §10 "spec→instance.json 전체 workflow"를 실제로 실행 가능한 함수 하나로 묶음).

### `sizing_recipe.run_topology_pipeline_with_finger_fixup`

> `run_topology_pipeline()`(stick_diagram.py, L1~L3)이 euler-blocked row를 그냥 실패로만
> 보고하는 지점에 L3(`suggest_pair_finger_adjustments()`)+L4(`apply_and_revalidate_pair_
> adjustment()`) 자동 수정 루프를 감싸 붙인다 -- `.ai/context.md` 세션13 D절이 남긴 "다음
> 확장 지점", 세션14에서 실배선.

### `sizing_recipe.run_matching_safety_with_finger_growth`

> `repair_matching_safety()`(stick_diagram.py, L1~L3, branch 복합 매칭 포함)가
> 3c(common-centroid)를 못 푸는 지점에 "매칭 목적 핑거증가"(위) 자동 수정 루프를 감싸
> 붙인다 -- `run_topology_pipeline_with_finger_fixup()`(euler용)과 대칭되는 구조,
> `stick_diagram.py`<->`sizing_recipe.py` 단방향 import 제약 때문에 여기 위치(동일 이유).

### `sizing_recipe._fixup_euler_blocked_rows`

> `repair_matching_safety()`(3c 수리 -- 일부 소자를 `common_centroid_layout()`으로
> 새 행에 빼냄)가 원래 행에 **남은 나머지 소자들**의 euler 조건(짝수차수 -- 한붓그리기
> 가능 여부)까지 보존한다는 보장은 없다 -- 2026-08-13(세션31 이어) 실측 발견: `two_stage_
> ota` box-shape 진단 중 `save_instance_json()`이 repair *이전* 스냅샷을 저장하던 버그를
> 고치자(그 자체는 별개 수정), self-test(11소자 M3a 그룹, M4a/M4b+M10/M19를 3c 수리로
> 빼낸 뒤) 남은 행 `m3a_row`가 `status=blocked, odd_nodes=['Vbias3','gnd']`로 방치되는
> 게 처음으로 드러났다(지금까지는 이 저장 버그가 이 사실을 가려왔을 뿐, `repair_matching_
> safety()`가 새로 만든 버그가 아니다). `run_topology_pipeline_with_finger_fixup()`이
> euler-fixup에 쓰는 것과 **정확히 같은 전략**(1순위: `apply_and_revalidate_pair_
> adjustment()`로 매칭쌍 핑거증가, 안 되면 2순위: `find_min_crossover_layout_with_
> branch_composite()`로 그래프 이론상 항상 성공하는 그룹분할)을 그 함수와 달리
> `topology_path` 재로드 없이 `rows` 표현에 직접 적용한다 -- 두 저수준 함수
> (`apply_and_revalidate_pair_adjustment()`/`find_min_crossover_layout_with_branch_
> composite()`) 다 애초에 `row_transistors`를 직접 받는 API라 재사용 가능하다.

### `stick_diagram.run_topology_pipeline`

> `load_topology()` -> `sizing_overrides`로 소자별 layout 필드(n_fingers/finger_w/w/
> stack_id — **필수**, 사이징+finger 배분이 끝난 뒤에만 이 함수를 의미 있게 호출할 수 있다)
> 덮어쓰기 -> `check_finger_width_compatibility()`(§3.5, **세션18 배선** — W가 finger_w의
> 정수배가 아니면 물리적으로 존재할 수 없는 요구라 여기서 즉시 `ValueError`, 아래 euler
> 분석은 이 게이트를 통과해야만 의미가 있다) -> `split_into_stacks()`로 스택(=기본 물리
> 행 후보) 구성 -> §1.6/§1.7이 정한 순서 그대로: 행별 Euler 유효성 -> `check_box_shape()`
> -> `audit_row_split()`(matching-safety, `symmetry.matching_pairs`의 kind 사용) ->
> `pack_floorplan_grouped()` -> `check_stick_diagram_coverage()`.

### `stick_diagram.trace_vdd_to_gnd_branches`

> PMOS는 source(레일쪽)->drain(부하쪽), NMOS는 drain(부하쪽)->source(레일쪽) 순으로
> "전류가 실제로 흐르는 방향"을 kind로 고정해 소자를 잇는다 -- 이렇게 하면 같은 net을
> 공유하더라도 **같은 kind가 같은 타입 단자(둘 다 source 또는 둘 다 drain)를 공유하는
> 관계**(예: `M1a.source==M1b.source`, 병렬 형제)는 구조적으로 절대 다음 hop이 될 수
> 없고, **PMOS의 drain과 NMOS의 drain이 만나는 지점**(예: `M2a.drain==M3a.drain`,
> 캐스코드 출력 노드)만 정상적으로 다음 hop이 된다.

### `stick_diagram.trace_gnd_to_vdd_branches`

> `trace_vdd_to_gnd_branches()`의 반대 방향 -- GND에서 시작해 VDD 쪽으로 거슬러
> 올라간다. entry/exit 단자를 반대로 고정한다: PMOS는 `drain(부하쪽)->source(레일쪽)`,
> NMOS는 `source(레일쪽)->drain(부하쪽)` 순(하향 버전과 정확히 반대 -- "전류가 실제로
> 흐르는 방향"을 반대로 거슬러 올라가는 것뿐, 원리는 동일).

### `stick_diagram.propose_theta_kcl_gap_fill`

> `sizing_roles.theta`의 전류(ID) 구조(`"const"`/`"A"`/`"A_signed"` feed -- gm_id를
> 직접 다루는 `"B"`/`"C"`/`"metric_stage_budget"`류는 범위 밖)를 connectivity와
> analog-grammar idiom만으로 제안한다.

### `sizing_recipe.propagate_node_voltages`

> 레일에서 시작해 각 소자의 `vds`를 따라 **모든 내부 노드의 DC 절대 전압**을 복원한다.

### `sizing_recipe.derive_vsb_from_nodes`

> 소자 하나의 **소스-바디 전압 `vsb`**를 복원된 노드전압에서 유도한다(2026-09-08, B9).

### `sizing_recipe.node_pole_estimate`

> 내부 노드마다 **1차 pole** `w = G_node / C_node`를 넷리스트+LUT에서 추정한다
> (2026-09-10, §7.11).

### `sizing_recipe._hr_resolve_vertical_group`

(docstring 없음)

### `stick_diagram._import_analog_grammar`

> `skills/analog-grammar/assets`를 sys.path에 넣고(멱등) 주어진 모듈들을 임포트해
> 튜플로 반환한다. analog-grammar가 없으면 `ImportError`(skill 이름·탐색 경로, 원래
> 예외는 `__cause__`)를 던진다.

## 신규 시그니처

| 모듈 | 심볼 | 시그니처 |
|---|---|---|
| `stick_diagram` | `RailDeclaration` | `@dataclass(frozen=True) class RailDeclaration: nets: frozenset` |
| `stick_diagram` | `rail_declaration` | `def rail_declaration(topology: dict) -> RailDeclaration:` |

## 변경 이력

- 2026-10-29 `cards/simplify`(검증 대기): 위 대체 표지만 더함 -- 본문 불변, 표지 전 원문 = `git show 07181524:docs/02-design/specs/20260930-b26-rail-accessor-set.interface.md`.
- 2026-10-29 `cards/revise-1029`: 대체 표지의 '검증 대기'를 병합 표기로 바꿈(표지 내용 점검 결과 유지) -- 본문 불변, 고치기 전 원문 = `git show 052465ed:docs/02-design/specs/20260930-b26-rail-accessor-set.interface.md`.
