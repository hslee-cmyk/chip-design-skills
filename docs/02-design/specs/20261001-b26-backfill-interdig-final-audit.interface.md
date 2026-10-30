# interface card: 20261001-b26-backfill-interdig-final-audit

> **[상태 표지 2026-10-29] 실행·병합 완료 기록 -- 현행 규칙·절차 아님.** 판정 기록 `.ai/verification/20261001-b26-backfill-interdig-final-audit.json`(FAIL 0)이 있고 이 card의 커밋은 master에 병합됐다. 옛 계획 Phase 3(모듈 분할) card이고 Phase 3은 폐기됐다(계획 N6.1 '옛 Phase 처리' 3행 -- 새 엔진은 처음부터 패키지로 나뉘고 옛 B26-1은 부품으로 이식). 본문의 spec card·interface card·auditor 판정(V1~V10)·DEC-40 승인·R1 절차는 DEC-86으로 폐기했다(계획 N3.12·N4.2, DEC-40 행) -- 현행 완료 조건은 계획 N6.3이다. 본문의 `A`(`skills/analog-gmid-design/assets`) 아래 옛 엔진·test는 `skills/analog-gmid-design/legacy/`로 옮겨졌고(`60727b06`) 새 test 체계(`gmid_engine/tests/`)에서 돌지 않는다. card LT-1(DEC-99)이 `legacy/`를 지운 뒤에는 tag `legacy-final`에만 남는다. 본문은 기록이며 덧대지 않는다(O-169).

생성: `tools/gates/interface_card.py`(05-role-separation §11.1). 본문 코드는 넣지 않는다(DEC-38).

## 관찰 가능한 계약

| 모듈 | 심볼 | 시그니처 |
|---|---|---|
| `sizing_recipe` | `run_matching_safety_with_finger_growth` | `def run_matching_safety_with_finger_growth(rows: dict, matching_pairs: list, pair_sensitivity: dict, ctx: SizingContext, lut_by_kind: dict, metrics_specs: dict, constraints: list, gm_id_bounds: tuple=(2.0, 30.0), min_fingers: int=2, max_rounds: int=5, allow_layout_relaxation: bool=True) -> dict` |
| `sizing_recipe` | `size_transistor` | `def size_transistor(gm: float, gm_id: float, L: float, lut: GmIdLUT, vds: float, vsb: float=0.0) -> SizingResult` |
| `sizing_recipe` | `GmIdLUT.gm_gds_ratio` | `def gm_gds_ratio(self, gm_id: float, L: float, vds: float, vsb: float=0.0) -> float` |
| `sizing_recipe` | `SemiEmpiricalGmIdLUT.gm_gds_ratio` | `def gm_gds_ratio(self, gm_id: float, L: float, vds: float, vsb: float=0.0) -> float` |

### `sizing_recipe.run_matching_safety_with_finger_growth`

> `repair_matching_safety()`(stick_diagram.py, L1~L3, branch 복합 매칭 포함)가
> 3c(common-centroid)를 못 푸는 지점에 "매칭 목적 핑거증가"(위) 자동 수정 루프를 감싸
> 붙인다 -- `run_topology_pipeline_with_finger_fixup()`(euler용)과 대칭되는 구조,
> `stick_diagram.py`<->`sizing_recipe.py` 단방향 import 제약 때문에 여기 위치(동일 이유).

### `sizing_recipe.size_transistor`

> 방법론 식 1.17/1.18: ID = gm/(gm/ID),  W = L * ID / IDu.

### `sizing_recipe.GmIdLUT.gm_gds_ratio`

> intrinsic gain gm/gds = (gm/ID)*VA. LUT의 GDS 열에서 유도(방법론 §2.5).

### `sizing_recipe.SemiEmpiricalGmIdLUT.gm_gds_ratio`

(docstring 없음)

## 신규 시그니처

| 모듈 | 심볼 | 시그니처 |
|---|---|---|

## 변경 이력

- 2026-10-29 `cards/revise-1029`: 위 상태 표지만 더함 -- 본문 불변, 표지 전 원문 = `git show 052465ed:docs/02-design/specs/20261001-b26-backfill-interdig-final-audit.interface.md`.
