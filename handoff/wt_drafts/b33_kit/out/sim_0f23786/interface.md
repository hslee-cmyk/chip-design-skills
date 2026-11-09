# interface card: 20260930-v7-registry-edges

생성: `tools/gates/interface_card.py`(05-role-separation §11.1). 본문 코드는 넣지 않는다(DEC-38).

## 관찰 가능한 계약

| 모듈 | 심볼 | 시그니처 |
|---|---|---|
| `sizing_recipe` | `SemiEmpiricalGmIdLUT.__init__` | `def __init__(self, L_grid, VGS_grid, VDS_grid, VS_grid, ID, GM, GDS, CGG, W_ref=None, SID_1F=None)` |
| `sizing_recipe` | `InfeasibleSizingError.__init__` | `def __init__(self, message: str, sized_snapshot: dict \| None=None)` |
| `stick_diagram` | `Transistor.__post_init__` | `def __post_init__(self)` |

### `sizing_recipe.SemiEmpiricalGmIdLUT.__init__`

> W_ref: ID/GM/GDS/CGG 배열이 실제로 어느 폭에서 측정/합성됐는지.

### `sizing_recipe.InfeasibleSizingError.__init__`

(docstring 없음)

### `stick_diagram.Transistor.__post_init__`

(docstring 없음)

## 신규 시그니처

| 모듈 | 심볼 | 시그니처 |
|---|---|---|

(엔진 신규 심볼 없음. `reachability.build_graph(files)`의 반환 모양 `(노드 집합, 간선 사전)`은 그대로이고 간선 사전에 `<파일>::=<이름>` 키가 더해진다. 게이트 안의 보조 함수
이름은 code-author가 정한다 -- `main`·`build_graph`가 부른다.)
