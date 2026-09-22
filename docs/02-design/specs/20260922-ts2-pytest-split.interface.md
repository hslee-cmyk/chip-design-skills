# interface card: 20260922-ts2-pytest-split

생성: `tools/gates/interface_card.py`(05-role-separation §11.1). 본문 코드는 넣지 않는다(DEC-38).

## 관찰 가능한 계약

| 모듈 | 심볼 | 시그니처 |
|---|---|---|
| `sizing_recipe` | `optimize_full_circuit_budget` | `def optimize_full_circuit_budget(topology_path: str, spec: dict, grid_points_per_theta: int=5, search_method: str='grid', slsqp_kwargs: dict \| None=None, stop_after_sizing: bool=False) -> dict` |

### `sizing_recipe.optimize_full_circuit_budget`

> 배치 7-3d/7-5 — spec(topology.json 경로 + design spec)만 받아 instance.json에 바로
> 옮길 수 있는 완성된 결과를 반환하는 **단일 진입점 harness**(2026-07-31 확장,
> do.md §10 "spec→instance.json 전체 workflow"를 실제로 실행 가능한 함수 하나로 묶음).

## 신규 시그니처

| 모듈 | 심볼 | 시그니처 |
|---|---|---|
