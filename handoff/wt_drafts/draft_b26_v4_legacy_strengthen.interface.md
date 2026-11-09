# interface card: 20261007-b26-v4-legacy-strengthen

생성: `tools/gates/interface_card.py`(05-role-separation §11.1). 본문 코드는 넣지 않는다(DEC-38).

## 관찰 가능한 계약

| 모듈 | 심볼 | 시그니처 |
|---|---|---|
| `stick_diagram` | `refine_differential_and_mirror_relations` | `def refine_differential_and_mirror_relations(transistors: list, inputs=(), outputs=(), feedbacks=(), biases=(), clocks=(), max_iterations: int=5) -> dict \| None` |
| `stick_diagram` | `propose_device_roles_gap_fill` | `def propose_device_roles_gap_fill(transistors: list, device_roles: dict, matching_pairs_meta: list, compensation_stage_devices: list \| None=None, vds_theta_authoritative: set \| None=None, inputs=(), outputs=(), feedbacks=(), biases=(), clocks=()) -> dict` |
| `stick_diagram` | `apply_device_roles_gap_fill` | `def apply_device_roles_gap_fill(topology_json_path: str, result: dict) -> dict` |
| `stick_diagram` | `load_topology` | `def load_topology(json_path: str) -> tuple[list[Transistor], dict]` |

### `stick_diagram.refine_differential_and_mirror_relations`

> `find_differential_pair_candidates()`(C-11)가 `inputs=` 선언 없이 순수
> connectivity로 찾아낸 differential pair 후보의 gate net을 **자동으로**
> `inputs=`에 승격해서 `find_verified_differential_and_mirror_relations()`를
> 재실행하는 오케스트레이션(`.ai/context.md` D절 item 0, 2026-08-07 사용자 지시로
> 세션24에 신설). 세션23까지는 이 승격을 사람이 손으로 한 번(`Voc`/`Voc_des`를
> 수동으로 `inputs=`에 넣어) 했을 뿐 코드화되어 있지 않았다.

### `stick_diagram.propose_device_roles_gap_fill`

> `symmetry.matching_pairs`/`device_roles`(`gm_id_role`/`L_role`/`headroom_role`)를 **netlist
> connectivity만으로** 제안한다(2026-08-14, `.ai/context.md` 세션32 I절 설계 + 다음 세션 실측
> 검증을 반영해 확정). `vertical_stack_id`는 제안하지 않는다 -- I-1의 `propose_vertical_stack_
> id_gap_fill()`이 이미 그 필드를 전담하고(같은 이유: mirror edge를 vsid 유니온에 안 쓰는 것과
> 동일 원칙), 이 함수와 역할이 겹치면 두 제안이 서로 다른 값을 낼 위험이 생긴다.

### `stick_diagram.apply_device_roles_gap_fill`

> `propose_device_roles_gap_fill()`의 순수 결과를 받아 **실제로 topology.json 파일을 읽고
> 병합하고 다시 쓴다**(`symmetry.matching_pairs`/`device_roles` 갱신) -- I-3 정정 2(세션32)
> 그대로: `vertical_stack_id`(층위4, `propose_vertical_stack_id_gap_fill()`)와 달리 이 필드들은
> 사이징 결과에 직접 영향을 주므로 `load_topology()`의 메모리상 자동채움이 아니라 파일 자체를
> 영구히 갱신하는 쪽을 사용자가 확정했다.

### `stick_diagram.load_topology`

> topology library JSON(`library/*.topology.json`)을 읽어 (transistors, meta) 반환.

## 신규 시그니처

| 모듈 | 심볼 | 시그니처 |
|---|---|---|
