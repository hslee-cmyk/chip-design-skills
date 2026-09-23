# interface card: 20260923-probe-promote-consistency

생성: `tools/gates/interface_card.py`(05-role-separation §11.1). 본문 코드는 넣지 않는다(DEC-38).

## 관찰 가능한 계약

| 모듈 | 심볼 | 시그니처 |
|---|---|---|
| `sizing_recipe` | `_metric_kcl_residual` | `def _metric_kcl_residual(spec: dict, ctx: SizingContext) -> float` |

### `sizing_recipe._metric_kcl_residual`

> F엔진(2026-09-08, B8) — **내부 노드의 KCL 잔차** `|Sum I_into_node|` 중 최댓값(A).

## 신규 시그니처

| 모듈 | 심볼 | 시그니처 |
|---|---|---|
