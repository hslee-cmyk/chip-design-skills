# interface card: 20260930-p3-gate-move-aware

생성: `tools/gates/interface_card.py`(05-role-separation §11.1). 본문 코드는 넣지 않는다(DEC-38).

## 관찰 가능한 계약

| 모듈 | 심볼 | 시그니처 |
|---|---|---|
| `stick_diagram` | `build_graph` | `def build_graph(transistors: list[Transistor]) -> StackGraph` |

### `stick_diagram.build_graph`

> §2.5.4 "최대한 섞는다"를 hierholzer()가 자동으로 따르게 만드는 지점이 바로 여기다.

## 신규 시그니처

| 모듈 | 심볼 | 시그니처 |
|---|---|---|
| `reachability` | `moved_defs` | `def moved_defs(base, head) -> dict` (`base`·`head` = `dict` 또는 `SourceIndex`) |
| `reachability` | `SourceIndex` | `class SourceIndex: def __init__(self, files: dict)` |
| `reachability` | `SourceIndex.units` | `def units(self, path: str) -> list` |
| `reachability` | `SourceIndex.global_names` | `def global_names(self, path: str) -> dict` |
| `reachability` | `SourceIndex.binding_origin` | `def binding_origin(self, path: str, name: str) -> tuple` |
| `reachability` | `def_hash` | `def def_hash(fn) -> str` |
