# interface card: 20261001-b26-backfill-interdig-final-audit

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
