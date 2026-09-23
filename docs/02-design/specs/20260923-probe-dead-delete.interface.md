# interface card: 20260923-probe-dead-delete

생성: `tools/gates/interface_card.py`(05-role-separation §11.1). 본문 코드는 넣지 않는다(DEC-38).

## 관찰 가능한 계약

| 모듈 | 심볼 | 시그니처 |
|---|---|---|
| `sizing_recipe` | `audit_vsb_consistency` | `def audit_vsb_consistency(by_name: dict, sized: dict, vdd: float, tol: float=1e-06, **kw) -> list` |

### `sizing_recipe.audit_vsb_consistency`

> 선언된 `vsb`가 복원된 노드전압과 맞는지 소자 전수 대조해 어긋난 것만 돌려준다.

## 신규 시그니처

| 모듈 | 심볼 | 시그니처 |
|---|---|---|
