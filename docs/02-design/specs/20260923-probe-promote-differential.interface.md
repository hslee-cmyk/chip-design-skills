# interface card: 20260923-probe-promote-differential

생성: `tools/gates/interface_card.py`(05-role-separation §11.1). 본문 코드는 넣지 않는다(DEC-38).

## 관찰 가능한 계약

| 모듈 | 심볼 | 시그니처 |
|---|---|---|
| `sizing_recipe` | `SemiEmpiricalGmIdLUT._solve_vgs` | `def _solve_vgs(self, gm_id: float, L: float, vds: float, vsb: float) -> float` |

### `sizing_recipe.SemiEmpiricalGmIdLUT._solve_vgs`

> 목표 gm/ID를 만족하는 **가장 큰 VGS 해**(rightmost root)를 격자 위에서 찾는다.

## 신규 시그니처

| 모듈 | 심볼 | 시그니처 |
|---|---|---|
