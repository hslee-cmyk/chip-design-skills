# interface card: 20260930-registry-grade-fix

> **[상태 표지 2026-10-29] 실행·병합 완료 기록 -- 현행 규칙·절차 아님.** 판정 기록 `.ai/verification/20260930-registry-grade-fix.json`(FAIL 0)이 있고 이 card의 커밋은 master에 병합됐다. 옛 계획 Phase 2(죽은 코드·DUP 정리) card이고 Phase 2는 폐기됐다(계획 N6.1 '옛 Phase 처리' 2행 -- 새 엔진은 모듈 지도 N3.10으로 처음부터 개념당 정본 하나). 본문의 spec card·interface card·auditor 판정(V1~V10)·DEC-40 승인·R1 절차는 DEC-86으로 폐기했다(계획 N3.12·N4.2, DEC-40 행) -- 현행 완료 조건은 계획 N6.3이다. 본문의 `A`(`skills/analog-gmid-design/assets`) 아래 옛 엔진·test는 `skills/analog-gmid-design/legacy/`로 옮겨졌고(`60727b06`) 새 test 체계(`gmid_engine/tests/`)에서 돌지 않는다. card LT-1(DEC-99)이 `legacy/`를 지운 뒤에는 tag `legacy-final`에만 남는다. 등급표가 있는 레지스트리(`docs/03-analysis/gain-budget-gmid-sizing.function-registry.md`)는 '옛 엔진 부품을 새 엔진으로 가져올 때 보는 표'로 남는다(계획 관련 문서 표). 본문의 도구 `A/tests/tools/reg_check.py`는 지금 `legacy/tests/tools/reg_check.py`에 있다. 본문은 기록이며 덧대지 않는다(O-169).

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
| `sizing_recipe` | `true_current_mirror_groups` | `def true_current_mirror_groups(by_name: dict) -> list` |
| `sizing_recipe` | `propagate_node_voltages` | `def propagate_node_voltages(by_name: dict, sized: dict, vdd: float, rail_hi=_DEFAULT_RAIL_HI, rail_lo=_DEFAULT_RAIL_LO, tol: float=1e-06, max_passes: int=50) -> NodeVoltageReport` |
| `sizing_recipe` | `build_ac_network` | `def build_ac_network(ctx: 'SizingContext', excite: dict, also_fix) -> dict` |
| `stick_diagram` | `find_diode_stacks` | `def find_diode_stacks(netlist: list) -> list` |

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

### `sizing_recipe.true_current_mirror_groups`

> **진짜 전류미러** 그룹 -- 같은 `(kind, gate net, source net)`을 공유하는 소자 집합.

### `sizing_recipe.propagate_node_voltages`

> 레일에서 시작해 각 소자의 `vds`를 따라 **모든 내부 노드의 DC 절대 전압**을 복원한다.

### `sizing_recipe.build_ac_network`

> L2 주파수응답의 **omega에 무관한 부분**을 한 번만 조립한다(2026-09-10, 중복계산 제거).

### `stick_diagram.find_diode_stacks`

> C엔진(§7.3.2) — `find_diode_loops()`(자기 자신의 gate==drain만 보는 구식 자기참조
> 체크)를 대체. **2026-07-30 정정 근거**: M57은 게이트가 자기 자신의 drain에 물려 self-diode로
> 잡히지만, M58은 게이트가 **M57의** drain에 물려 있어 자기참조 체크로는 놓친다 — 그래서
> "같은 물리적 스택(`stack_id`) 안에서, 각 소자의 gate가 그 스택 위 **어떤 소자의
> drain과든**(자기 것이든 이웃 것이든) 같은 net인지"를 보는 그래프 워크로 재정의했다.

## 신규 시그니처

| 모듈 | 심볼 | 시그니처 |
|---|---|---|
| `reg_check` | `*` | 신규 모듈 `A/tests/tools/reg_check.py` |
| `reg_check` | `check` | `def check(registry_text: str, engine_names: set) -> list` |
| `reg_check` | `main` | `def main(argv: list) -> int` |

## 변경 이력

- 2026-10-29 `cards/revise-1029`: 위 상태 표지만 더함 -- 본문 불변, 표지 전 원문 = `git show 052465ed:docs/02-design/specs/20260930-registry-grade-fix.interface.md`.
