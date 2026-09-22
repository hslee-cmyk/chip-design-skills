# interface card: 20260922-ic3-completeness

생성: `tools/gates/interface_card.py`(05-role-separation §11.1). 본문 코드는 넣지 않는다(DEC-38).

## 관찰 가능한 계약

| 모듈 | 심볼 | 시그니처 |
|---|---|---|
| `stick_diagram` | `save_instance_json` | `def save_instance_json(path: str, topology_json_path: str, sizing_results: dict, pipeline_result: dict) -> None` |
| `stick_diagram` | `load_topology` | `def load_topology(json_path: str) -> tuple[list[Transistor], dict]` |
| `stick_diagram` | `check_stick_diagram_coverage` | `def check_stick_diagram_coverage(sized_device_names, stick_diagram_devices: dict) -> CoverageVerdict` |
| `stick_diagram` | `run_topology_pipeline` | `def run_topology_pipeline(topology_json_path: str, sizing_overrides: dict, floorplan_hints: dict \| None=None, cell_groups: dict \| None=None) -> dict` |

### `stick_diagram.save_instance_json`

> instance-output JSON 작성 — `pipeline_result`(`run_topology_pipeline()`의 반환값, 또는
> 독립된 물리 cell이 여러 개인 회로라면 §6.9 아래 문단처럼 직접 조립한 동일 스키마의 dict)를
> 손대지 않고 그대로 옮겨 쓴다(§1 표 5번 원칙: 함수 반환값 그대로, 손으로 축약/재구성 금지).
> `sizing_results`는 `{name: {"W":..., "L":..., "ID":..., "gm":..., "gm_id":...}}` 형태를
> 기대한다(sizing_recipe.py의 SizingResult 필드명 그대로).

### `stick_diagram.load_topology`

> topology library JSON(`library/*.topology.json`)을 읽어 (transistors, meta) 반환.

### `stick_diagram.check_stick_diagram_coverage`

> 리포트를 완료로 선언하기 **직전** 반드시 호출한다 — sizing이 끝난 소자 이름 전부가
> 실제로 어떤 stick-diagram 물리 행에든 배치돼 있는지, 단순 집합 차집합으로 확인한다.

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
| `stick_diagram` | `INSTANCE_TOP_FIELDS` | `INSTANCE_TOP_FIELDS: tuple[str, ...]` |
| `stick_diagram` | `INSTANCE_SIZING_FIELDS` | `INSTANCE_SIZING_FIELDS: tuple[str, ...]` |
| `stick_diagram` | `CompletenessVerdict` | `class CompletenessVerdict` |
| `stick_diagram` | `check_instance_completeness` | `def check_instance_completeness(instance: Mapping, device_names: Iterable[str]) -> CompletenessVerdict` |
| `stick_diagram` | `NameCollisionVerdict` | `class NameCollisionVerdict` |
| `stick_diagram` | `check_topology_name_uniqueness` | `def check_topology_name_uniqueness(device_names: Sequence[str], passive_names: Sequence[str]) -> NameCollisionVerdict` |
