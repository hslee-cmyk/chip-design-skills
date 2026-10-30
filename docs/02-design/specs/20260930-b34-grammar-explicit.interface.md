# interface card: 20260930-b34-grammar-explicit

> **[상태 표지 2026-10-29] 실행·병합 완료 기록 -- 현행 규칙·절차 아님.** 판정 기록 `.ai/verification/20260930-b34-grammar-explicit.json`(FAIL 0)이 있고 이 card의 커밋은 master에 병합됐다. 옛 계획 Phase 3(모듈 분할) card이고 Phase 3은 폐기됐다(계획 N6.1 '옛 Phase 처리' 3행 -- 새 엔진은 처음부터 패키지로 나뉘고 옛 B26-1은 부품으로 이식). 본문의 spec card·interface card·auditor 판정(V1~V10)·DEC-40 승인·R1 절차는 DEC-86으로 폐기했다(계획 N3.12·N4.2, DEC-40 행) -- 현행 완료 조건은 계획 N6.3이다. 본문의 `A`(`skills/analog-gmid-design/assets`) 아래 옛 엔진·test는 `skills/analog-gmid-design/legacy/`로 옮겨졌고(`60727b06`) 새 test 체계(`gmid_engine/tests/`)에서 돌지 않는다. card LT-1(DEC-99)이 `legacy/`를 지운 뒤에는 tag `legacy-final`에만 남는다. 이 card의 계약(analog-grammar를 못 찾으면 ImportError)은 analog-grammar를 사이징 입력의 원천으로 요구한다. 현행은 반대다: analog-grammar는 쓰지 않고 작업 트리에서 지우며(DEC-99), 회로 해석은 연결과 원문만으로 한다(CLAUDE.md 원칙 14). 본문은 기록이며 덧대지 않는다(O-169).

생성: `tools/gates/interface_card.py`(05-role-separation §11.1). 본문 코드는 넣지 않는다(DEC-38).

## 관찰 가능한 계약

| 모듈 | 심볼 | 시그니처 |
|---|---|---|
| `stick_diagram` | `load_topology` | `def load_topology(json_path: str) -> tuple[list[Transistor], dict]` |
| `stick_diagram` | `find_idiom_matches` | `def find_idiom_matches(transistors: list, inputs=(), outputs=(), feedbacks=(), biases=(), clocks=()) -> list \| None` |
| `stick_diagram` | `audit_theta_root_direction` | `def audit_theta_root_direction(transistors: list, sizing_roles: dict \| None, inputs=(), outputs=(), feedbacks=(), biases=(), clocks=()) -> list` |
| `stick_diagram` | `run_topology_pipeline` | `def run_topology_pipeline(topology_json_path: str, sizing_overrides: dict, floorplan_hints: dict \| None=None, cell_groups: dict \| None=None) -> dict` |
| `stick_diagram` | `find_stack_edges` | `def find_stack_edges(transistors: list) -> list \| None` |
| `stick_diagram` | `find_differential_and_mirror_forks` | `def find_differential_and_mirror_forks(transistors: list, inputs=(), outputs=(), feedbacks=(), biases=(), clocks=()) -> dict \| None` |
| `stick_diagram` | `suggest_vertical_stack_composites` | `def suggest_vertical_stack_composites(transistors: list, inputs=(), outputs=(), feedbacks=(), biases=(), clocks=(), direction: str='vdd_to_gnd') -> list \| None` |
| `stick_diagram` | `find_differential_pair_candidates` | `def find_differential_pair_candidates(transistors: list, inputs=(), outputs=(), feedbacks=(), biases=(), clocks=()) -> dict \| None` |
| `stick_diagram` | `find_verified_differential_and_mirror_relations` | `def find_verified_differential_and_mirror_relations(transistors: list, inputs=(), outputs=(), feedbacks=(), biases=(), clocks=()) -> dict \| None` |
| `stick_diagram` | `refine_differential_and_mirror_relations` | `def refine_differential_and_mirror_relations(transistors: list, inputs=(), outputs=(), feedbacks=(), biases=(), clocks=(), max_iterations: int=5) -> dict \| None` |
| `stick_diagram` | `propose_theta_kcl_gap_fill` | `def propose_theta_kcl_gap_fill(transistors: list, matching_pairs_meta: list, ideal_sources: list \| None=None, compensation_stage_devices: list \| None=None, inputs=(), outputs=(), feedbacks=(), biases=(), clocks=()) -> dict` |
| `stick_diagram` | `propose_device_roles_gap_fill` | `def propose_device_roles_gap_fill(transistors: list, device_roles: dict, matching_pairs_meta: list, compensation_stage_devices: list \| None=None, vds_theta_authoritative: set \| None=None, inputs=(), outputs=(), feedbacks=(), biases=(), clocks=()) -> dict` |
| `stick_diagram` | `geometry_colocation_union` | `def geometry_colocation_union(netlist: list, matching_pairs: list) -> dict` |
| `stick_diagram` | `propose_vertical_stack_id_gap_fill` | `def propose_vertical_stack_id_gap_fill(transistors: list, matching_pairs: list, device_roles: dict, inputs=(), outputs=(), feedbacks=(), biases=(), clocks=()) -> dict` |

### `stick_diagram.load_topology`

> topology library JSON(`library/*.topology.json`)을 읽어 (transistors, meta) 반환.

### `stick_diagram.find_idiom_matches`

> analog-grammar skill(Stage 1 net 분류 + Stage 2 role 배정 + Stage 3 idiom
> 매칭)을 한 번에 실행해 **겹침 해소 이전**의 원본 Match 리스트를 반환한다.
> resolve_overlaps()(Stage 4 계층 축약/보고용 요약)는 여기서 거치지 않는다 --
> 예를 들어 current-reuse-pair(priority 9)가 그 아래 differential-pair 2개를
> 흡수해도, 실제 W/L 매칭이 필요한 단위는 여전히 원래의 두 쌍이지 4소자 뭉치가
> 아니다. `inputs`/`outputs`/`feedbacks`/`biases`/`clocks`는 analog-grammar의
> Stage 1 net 분류에 그대로 전달된다 -- topology.json의 `ports` 필드를 그대로
> 승격해서 넘기면 이름 힌트 추정을 줄일 수 있다(references/analog-grammar-
> integration.md §5).

### `stick_diagram.audit_theta_root_direction`

> `sizing_roles.theta`의 `"A"`/`"A_signed"` feed가 `root`(이 theta가 전류를 **정의**하는
> 소자)의 값을, `analog-grammar`의 `idioms.m_cascode()`가 이미 찾아둔 캐스코드 관계에서
> **`root`가 lo(전류생성원 쪽)인데 정작 그 위에 얹힌 up(캐스코드)을 reference/terms로
> 참조**하는 경우를 찾는다 -- **방향이 거꾸로일 가능성이 높다는 신호**(캐스코드는 전류를
> 정의하지 않고 그 아래 소자가 이미 정한 전류를 그대로 물려받을 뿐이므로, lo가 자기 위의
> up을 참조해 자기 값을 정하는 건 인과관계가 뒤바뀐 것).

### `stick_diagram.run_topology_pipeline`

> `load_topology()` -> `sizing_overrides`로 소자별 layout 필드(n_fingers/finger_w/w/
> stack_id — **필수**, 사이징+finger 배분이 끝난 뒤에만 이 함수를 의미 있게 호출할 수 있다)
> 덮어쓰기 -> `check_finger_width_compatibility()`(§3.5, **세션18 배선** — W가 finger_w의
> 정수배가 아니면 물리적으로 존재할 수 없는 요구라 여기서 즉시 `ValueError`, 아래 euler
> 분석은 이 게이트를 통과해야만 의미가 있다) -> `split_into_stacks()`로 스택(=기본 물리
> 행 후보) 구성 -> §1.6/§1.7이 정한 순서 그대로: 행별 Euler 유효성 -> `check_box_shape()`
> -> `audit_row_split()`(matching-safety, `symmetry.matching_pairs`의 kind 사용) ->
> `pack_floorplan_grouped()` -> `check_stick_diagram_coverage()`.

### `stick_diagram.find_stack_edges`

> analog-grammar의 `netclass.stack_edges(devs)`를 그대로 재사용한다(role/net
> 분류 불필요, 순수 connectivity) -- "X.source==Y.drain이면 Y 위에 X가 얹혀
> 있다"는 관계를 [(lower_name, upper_name, node), ...]로 반환한다.
> `find_stacked_matching_candidates()`(§1.7c)에 그대로 넘긴다.

### `stick_diagram.find_differential_and_mirror_forks`

> `trace_vdd_to_gnd_branches()`(하향) + `trace_gnd_to_vdd_branches()`(상향) 양쪽
> branch tree에서 **첫 번째로 갈라지는 지점(fork)**을 전부 찾아, 그 fork의 소자쌍을
> analog-grammar gate 판정(같은 gate=mirror, 다른 gate+둘 다 `INPUT`=differential)으로
> 분류한다. `find_verified_differential_and_mirror_relations()`와 같은 gate 판정
> 규칙을 쓰지만, 그 함수는 (구조가 같은 branch끼리 묶은 뒤) **매칭된 쌍 안의 모든
> 위치**를 보는 반면, 이 함수는 branch tree 전체의 **모든** fork를 훑는다는 게 다르다.

### `stick_diagram.suggest_vertical_stack_composites`

> `trace_vdd_to_gnd_branches()`(물리 branch 골격) + analog-grammar idiom matching
> (diode-connected/floating-battery/cascode-stack/push-pull, branch **내부에서 연속된
> 부분열만** 병합)을 합쳐 `vertical_stack_id` 후보를 제안한다 -- 세션23 실측(5번째
> 시도)에서 `current_reuse_telescopic_ota`(51소자)에 돌려 63개 composite unit 중 62개가
> 사람이 선언한 `vertical_stack_id`와 정확히 일치, 나머지 1개(`M37a`+`M38`)도 진짜 충돌이
> 아니라 `M37a`의 declared 값이 애초에 비어있던 gap을 메우는 방향의 제안이었다(`.ai/
> context.md` 세션23 C절 4가지 실패 + 이 5번째 성공 전체 기록 참고). 앞선 4가지 시도
> (엄격한 2단자 KCL / 분기 허용 rail-to-rail 연결성분 / 소자 단위 분기별 경로 나열 /
> kind 기반 방향 고정 branch tracing 단독)는 전부 `vertical_stack_id`를 재현하지
> 못했다 -- branch 골격만으로는 "허브 소자"와 "branch 내부 상/하 분할"을 구별 못 했는데,
> analog-grammar의 idiom 판정(diode-connected 등 role은 connectivity에서 결정론적으로
> 도출됨)을 branch 위에 겹치면 바로 그 상/하 분할 경계가 자연스럽게 드러났다.

### `stick_diagram.find_differential_pair_candidates`

> 구조적으로 매칭된 branch 쌍(`suggest_vertical_stack_composites()`의 composite
> 시퀀스가 완전히 같은 branch끼리 묶음, C-10과 동일 원리) 안에서, 서로 다른 위치의
> 소자쌍이 (1) 같은 kind, (2) 다른 gate(=mirror 아님), (3) **같은 non-rail source(진짜
> tail net)를 공유**하면 differential pair 후보로 판정한다.

### `stick_diagram.find_verified_differential_and_mirror_relations`

> 진짜 **branch 단위** 비교 -- 세션23 C-7/C-8이 확립한 원리(composite 구조가
> 완전히 같은 branch끼리만 비교)를 상향까지 확장하고, 매칭된 branch
> 쌍 **안의 모든 위치**를 스캔한다(첫 divergence 하나만 보던 한계 해소).

### `stick_diagram.refine_differential_and_mirror_relations`

> `find_differential_pair_candidates()`(C-11)가 `inputs=` 선언 없이 순수
> connectivity로 찾아낸 differential pair 후보의 gate net을 **자동으로**
> `inputs=`에 승격해서 `find_verified_differential_and_mirror_relations()`를
> 재실행하는 오케스트레이션(`.ai/context.md` D절 item 0, 2026-08-07 사용자 지시로
> 세션24에 신설). 세션23까지는 이 승격을 사람이 손으로 한 번(`Voc`/`Voc_des`를
> 수동으로 `inputs=`에 넣어) 했을 뿐 코드화되어 있지 않았다.

### `stick_diagram.propose_theta_kcl_gap_fill`

> `sizing_roles.theta`의 전류(ID) 구조(`"const"`/`"A"`/`"A_signed"` feed -- gm_id를
> 직접 다루는 `"B"`/`"C"`/`"metric_stage_budget"`류는 범위 밖)를 connectivity와
> analog-grammar idiom만으로 제안한다.

### `stick_diagram.propose_device_roles_gap_fill`

> `symmetry.matching_pairs`/`device_roles`(`gm_id_role`/`L_role`/`headroom_role`)를 **netlist
> connectivity만으로** 제안한다(2026-08-14, `.ai/context.md` 세션32 I절 설계 + 다음 세션 실측
> 검증을 반영해 확정). `vertical_stack_id`는 제안하지 않는다 -- I-1의 `propose_vertical_stack_
> id_gap_fill()`이 이미 그 필드를 전담하고(같은 이유: mirror edge를 vsid 유니온에 안 쓰는 것과
> 동일 원칙), 이 함수와 역할이 겹치면 두 제안이 서로 다른 값을 낼 위험이 생긴다.

### `stick_diagram.geometry_colocation_union`

> L2 축B(세션22 전면 재설계) — `derive_stack_groups()`를 분리한 것 중 geometry(축B,
> `sizing_recipe.py`의 `stack_groups_geometry`, `assign_finger_geometry()`의 finger_w
> 공유 단위) 쪽. `kcl_series_union()`(현재 전류 propagation용, 이 함수와 목적이 다르므로
> 별개로 유지)과는 이제 union 규칙 자체가 다르다.

### `stick_diagram.propose_vertical_stack_id_gap_fill`

> 선언 안 된 소자가 **결합(union) 그룹** 안에서 이미 선언된 `vertical_stack_id`를
> 물려받는 제안을 만든다(2026-08-13 세션31, 사용자 요청 -- `two_stage_ota.topology.
> json`의 M1/M2/M6 gap을 손으로 추론했던 걸 재사용 가능한 함수로 코드화).

## 신규 시그니처

| 모듈 | 심볼 | 시그니처 |
|---|---|---|

(새 심볼 없음. 지우는 def 없음. 바뀌는 것은 def 4개의 본문.)

## 변경 이력

- 2026-10-29 `cards/revise-1029`: 위 상태 표지만 더함 -- 본문 불변, 표지 전 원문 = `git show 052465ed:docs/02-design/specs/20260930-b34-grammar-explicit.interface.md`.
