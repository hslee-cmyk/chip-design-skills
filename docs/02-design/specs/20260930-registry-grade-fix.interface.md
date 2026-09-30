# interface card: 20260930-registry-grade-fix

생성: `tools/gates/interface_card.py`(05-role-separation §11.1). 본문 코드는 넣지 않는다(DEC-38).

## 관찰 가능한 계약

| 모듈 | 심볼 | 시그니처 |
|---|---|---|
| `audit_current_forced` | `render_report` | `def render_report(topology_path: str) -> tuple[str, bool]` |
| `sizing_recipe` | `gm_from_fT` | `def gm_from_fT(fT: float, C: float) -> float` |
| `sizing_recipe` | `_optimize_theta_slsqp_block_coordinate` | `def _optimize_theta_slsqp_block_coordinate(topology_path: str, spec: dict, ev: dict, n_rounds: int=4, slsqp_kwargs: dict \| None=None, fast_slsqp_kwargs: dict \| None=None, n_scan_full_circuit: int=21, fast_n_scan_full_circuit: int=9, progress: bool=True) -> tuple` |
| `sizing_recipe` | `build_toy_lut` | `def build_toy_lut(n: float=1.3, UT: float=0.026, VTo: float=0.4, ISuo: float=2e-07, L_grid=(1.8e-07, 3.5e-07, 5e-07, 1e-06), VGS_step: float=0.02, VGS_max: float=1.2, VDS_grid=(0.2, 0.4, 0.6, 0.8, 1.0), VS_grid=(0.0,)) -> SemiEmpiricalGmIdLUT` |
| `sizing_recipe` | `_invq_newton` | `def _invq_newton(x: float, iters: int=30) -> float` |
| `stick_diagram` | `check_multi_leaf_hub_parity` | `def check_multi_leaf_hub_parity(n_fingers_by_leaf: dict) -> MultiLeafHubParityVerdict` |
| `sizing_recipe` | `size_transistor` | `def size_transistor(gm: float, gm_id: float, L: float, lut: GmIdLUT, vds: float, vsb: float=0.0) -> SizingResult` |

### `audit_current_forced.render_report`

> (리포트 텍스트, has_violation) 반환 -- has_violation=True면 🔴(과소선언) 있음.

### `sizing_recipe.gm_from_fT`

> gm = 2*pi*fT*C  (방법론 식 1.6/1.7 — fT 스펙이 gm을 고정한다).

### `sizing_recipe._optimize_theta_slsqp_block_coordinate`

> `_optimize_theta_slsqp()`의 "설계 B" 확장(2026-08-20 세션40, 사용자 승인 -- A(L을
> 연속 SLSQP 자유변수로 승격)/B(블록 좌표 교대)/C(제약 자체 재정식화) 세 설계를 비교
> 제시한 뒤 B를 선택받음). `current_reuse_telescopic_ota`에 이 세션 앞부분에서 신설한
> Monticelli KVL 결합(M8/M9a/M9b/M10 등)이 실제로 만든 문제를 계기로 만들어졌다:
> `L_stage2out_p`/`L_stage2out_n`(`metric_stage_budget` theta) 같은 "복합"(둘 이상의
> metric type이 동시에 걸린) theta는 `presolve_warm_start()`가 SLSQP 진입 **전에** 한
> 번만 확정하고 그 뒤로 SLSQP 자유변수에서 제외되는데(`search_stage_budget_L_warm_
> start()`의 `stage_budget_L` 분류), 그 확정 시점엔 나머지 SLSQP 자유변수(`r_biasgen`
> 류)가 아직 bounds-midpoint(미튜닝)라 "이 L이 최선"이라는 판단 자체가 실제 최적점과
> 안 맞을 수 있다(실측: presolve가 고른 L에서 gain_db=57.24, 같은 L 근방을 이전에
> 튜닝된 값으로 손 스윕하면 72.1까지 나옴 -- "닭과 달걀" 문제).

### `sizing_recipe.build_toy_lut`

> E.K.V. 해석식으로 만든 합성(toy) 4D LUT — 실제 공정 데이터가 아니라 파이프라인 시연용.

### `sizing_recipe._invq_newton`

> VP/UT = 2(q-1)+ln(q) 를 q에 대해 뉴턴법으로 역산 (Jespers Annex 2 A2.2.2 invq() 참고).

### `stick_diagram.check_multi_leaf_hub_parity`

> hub 하나에 leaf가 N개(N≥2) 달린 구조(각 leaf = 서로 다른 소자 하나, 그 소자의
> finger 개수가 `n_fingers_by_leaf`)가 **finger 개수를 그대로 실현했을 때** 한붓그리기
> 가능한지를 그래프를 만들지 않고 공식으로 빠르게 판정한다(설계 공간 탐색 시 여러 k
> 후보를 빠르게 스크리닝하는 용도 — 최종 채택 전에는 반드시 `build_graph()`+
> `check_euler_condition()`으로 재확인할 것, 이 함수는 그 결과와 항상 일치함을 self-test로
> 직접 검증했다).

### `sizing_recipe.size_transistor`

> 방법론 식 1.17/1.18: ID = gm/(gm/ID),  W = L * ID / IDu.

## 신규 시그니처

| 모듈 | 심볼 | 시그니처 |
|---|---|---|
| `reg_check` | `*` | 신규 모듈 `A/tests/tools/reg_check.py` |
| `reg_check` | `check` | `def check(registry_text: str, engine_names: set) -> list` |
| `reg_check` | `main` | `def main(argv: list) -> int` |
