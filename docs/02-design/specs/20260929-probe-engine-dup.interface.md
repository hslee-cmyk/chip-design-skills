# interface card: 20260929-probe-engine-dup

생성: `tools/gates/interface_card.py`(05-role-separation §11.1). 본문 코드는 넣지 않는다(DEC-38).

## 관찰 가능한 계약

| 모듈 | 심볼 | 시그니처 |
|---|---|---|
| `sizing_recipe` | `size_transistor` | `def size_transistor(gm: float, gm_id: float, L: float, lut: GmIdLUT, vds: float, vsb: float=0.0) -> SizingResult` |
| `sizing_recipe` | `SemiEmpiricalGmIdLUT.id_density_at_vgs` | `def id_density_at_vgs(self, vgs: float, L: float, vds: float, vsb: float=0.0) -> float` |
| `sizing_recipe` | `true_current_mirror_groups` | `def true_current_mirror_groups(by_name: dict) -> list` |
| `sizing_recipe` | `is_diode_connected` | `def is_diode_connected(transistor) -> bool` |
| `sizing_recipe` | `_metric_supply_current` | `def _metric_supply_current(spec: dict, ctx: SizingContext) -> float` |

### `sizing_recipe.size_transistor`

> 방법론 식 1.17/1.18: ID = gm/(gm/ID),  W = L * ID / IDu.

### `sizing_recipe.SemiEmpiricalGmIdLUT.id_density_at_vgs`

> `gm_id_to_id_density()`와 같은 IDu(W/L=1 기준 전류)를 **VGS에서 직접** 읽는다
> (2026-09-09, B22 신설).

### `sizing_recipe.true_current_mirror_groups`

> **진짜 전류미러** 그룹 -- 같은 `(kind, gate net, source net)`을 공유하는 소자 집합.

### `sizing_recipe.is_diode_connected`

> `gate == drain`이면 diode-connected다 -- **connectivity만 본다**(2026-09-08, B1).

### `sizing_recipe._metric_supply_current`

> F엔진(2026-09-08, A3) — **VDD 레일에서 실제로 빠져나가는 전류**의 합(A). 회로의 진짜
> 공급전류이자 전력 예산의 분모다.

## 신규 시그니처

| 모듈 | 심볼 | 시그니처 |
|---|---|---|
| `probe_dup_scan` | `*` | 신규 모듈 `A/tests/tools/probe_dup_scan.py` |
| `probe_dup_scan` | `scan_source` | `def scan_source(source: str, path: str) -> list` |
| `probe_dup_scan` | `main` | `def main(argv: list) -> int` |
