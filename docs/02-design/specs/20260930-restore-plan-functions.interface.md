# interface card: 20260930-restore-plan-functions

생성: `tools/gates/interface_card.py`(05-role-separation §11.1). 본문 코드는 넣지 않는다(DEC-38).

## 관찰 가능한 계약

| 모듈 | 심볼 | 시그니처 |
|---|---|---|
| `run_harness` | `canonical_spec` | `def canonical_spec(circuit_key: str) -> dict` |
| `sizing_recipe` | `require_declared_spec_source` | `def require_declared_spec_source(topology_path: str, spec: dict) -> None` |

### `run_harness.canonical_spec`

> 이 회로의 **정본 spec**을 준다 -- 조사 스크립트가 써야 할 기본 진입점(2026-09-10).

### `sizing_recipe.require_declared_spec_source`

> 라이브러리 회로를 사이징할 때 spec의 **출처 선언**을 강제한다(2026-09-10).

## 신규 시그니처

| 모듈 | 심볼 | 시그니처 |
|---|---|---|
| `sizing_recipe` | `lut_conditions_from_npz` | `def lut_conditions_from_npz(npz_data) -> dict` |
| `run_harness` | `derived_spec` | `def derived_spec(circuit_key: str, why: str, **overrides) -> dict` |
