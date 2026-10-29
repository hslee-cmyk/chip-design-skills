# interface card: 20260929-probe-engine-dup

> **[상태 표지 2026-10-29] 실행·병합 완료 기록 -- 현행 규칙·절차 아님.** 판정 기록 `.ai/verification/20260929-probe-engine-dup.json`(FAIL 0)이 있고 이 card의 커밋은 master에 병합됐다. 옛 계획 Phase 2(죽은 코드·DUP 정리) card이고 Phase 2는 폐기됐다(계획 N6.1 '옛 Phase 처리' 2행 -- 새 엔진은 모듈 지도 N3.10으로 처음부터 개념당 정본 하나). 본문의 spec card·interface card·auditor 판정(V1~V10)·DEC-40 승인·R1 절차는 DEC-86으로 폐기했다(계획 N3.12·N4.2, DEC-40 행) -- 현행 완료 조건은 계획 N6.3이다. 본문의 `A`(`skills/analog-gmid-design/assets`) 아래 옛 엔진·test는 `skills/analog-gmid-design/legacy/`로 옮겨졌고(`60727b06`) 새 test 체계(`gmid_engine/tests/`)에서 돌지 않는다. card LT-1(DEC-99)이 `legacy/`를 지운 뒤에는 tag `legacy-final`에만 남는다. `engine_dup_scan.py`와 probe test는 지금 `legacy/tests/` 아래 있다. 본문은 기록이며 덧대지 않는다(O-169).

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
| `engine_dup_scan` | `*` | 신규 모듈 `A/tests/tools/engine_dup_scan.py` |
| `engine_dup_scan` | `scan_source` | `def scan_source(source: str, path: str) -> list` |
| `engine_dup_scan` | `main` | `def main(argv: list) -> int` |

## 변경 이력

- 2026-10-29 `cards/revise-1029`: 위 상태 표지만 더함 -- 본문 불변, 표지 전 원문 = `git show 052465ed:docs/02-design/specs/20260929-probe-engine-dup.interface.md`.
