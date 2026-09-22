# interface card: 20260922-ic3-completeness

생성: `tools/gates/interface_card.py`(05-role-separation §11.1). 본문 코드는 넣지 않는다(DEC-38).

## 관찰 가능한 계약

| 모듈 | 심볼 | 시그니처 |
|---|---|---|
| `stick_diagram` | `save_instance_json` | `def save_instance_json(path: str, topology_json_path: str, sizing_results: dict, pipeline_result: dict) -> None` |
| `stick_diagram` | `load_topology` | `def load_topology(json_path: str) -> tuple[list[Transistor], dict]` |

### `stick_diagram.save_instance_json`

> instance-output JSON 작성 — `pipeline_result`(`run_topology_pipeline()`의 반환값, 또는
> 독립된 물리 cell이 여러 개인 회로라면 §6.9 아래 문단처럼 직접 조립한 동일 스키마의 dict)를
> 손대지 않고 그대로 옮겨 쓴다(§1 표 5번 원칙: 함수 반환값 그대로, 손으로 축약/재구성 금지).
> `sizing_results`는 `{name: {"W":..., "L":..., "ID":..., "gm":..., "gm_id":...}}` 형태를
> 기대한다(sizing_recipe.py의 SizingResult 필드명 그대로).

### `stick_diagram.load_topology`

> topology library JSON(`library/*.topology.json`)을 읽어 (transistors, meta) 반환.

## 신규 시그니처

| 모듈 | 심볼 | 시그니처 |
|---|---|---|
| `stick_diagram` | `INSTANCE_TOP_FIELDS` | `INSTANCE_TOP_FIELDS: tuple[str, ...]` |
| `stick_diagram` | `INSTANCE_SIZING_FIELDS` | `INSTANCE_SIZING_FIELDS: tuple[str, ...]` |
| `stick_diagram` | `CompletenessVerdict` | `class CompletenessVerdict` |
| `stick_diagram` | `check_instance_completeness` | `def check_instance_completeness(instance: Mapping, device_names: Iterable[str]) -> CompletenessVerdict` |
| `stick_diagram` | `NameCollisionVerdict` | `class NameCollisionVerdict` |
| `stick_diagram` | `check_topology_name_uniqueness` | `def check_topology_name_uniqueness(device_names: Sequence[str], passive_names: Sequence[str]) -> NameCollisionVerdict` |
