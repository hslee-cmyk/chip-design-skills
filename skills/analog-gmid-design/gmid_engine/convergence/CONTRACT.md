# gmid_engine.convergence 동작 계약 (test 작성용) -- MOD8 사이징↔레이아웃 수렴 (U14)

- 근거: 계획 N3.17 LY1·LY3·LY5·LY7·LY8, LR9, DEC-79·84·89·91·95, N3.6 `K_max`; 설계 `40-engine` §3.9 MOD8·§11 U14(+U12 인계 72ebe46)·R12; 체크리스트 D-M8.
- 단위: 길이·폭 m, 면적 m², 전압 V, 전류 A, 용량 F, 전력 W. **폭 키** = finger_w / 제조 격자(정수, LUT 슬라이스 폭 키).
- 호출 순서(U16 `run_gmid_design_pipeline` 이 부른다): `front = find_front(sctx, starts)` -> `converge(sctx, pdk_decl, front.front)` -> `ConvergedFront.front` 가 판정 축
  최종 front. `find_front` 의 `pending_front`(봉인 7 대기)는 재검증할 봉인 스냅샷이 없어 받지 않는다. `unmeasured_front`(spec ss 제약 일부 미측정)는 호출부가 골라 넘길 수 있다.
- test 배치(규칙 H): `gmid_engine/tests/convergence/test_<파일>.py`. 데이터 선언 모듈 `convergence_values.py` 는 H 대상이 아니다.

## 0. 파일·층·진입점

층 = `_module_map.LAYERS` convergence tuple 위치. 파일은 앞 층 파일만 import 한다(같은 층끼리 금지).

| 파일 | 층 | 진입점 | 내용 |
|---|---|---|---|
| `convergence_values.py` | 0 | (데이터) | `ConvergedPoint`·`ConvergedFront`·`Iteration`·`Relaxation`·`Placement`·`PlacedLayout`·`JunctionChange`·`DroppedPoint`, 상수 `STATUS_*`·`DROP_*`·`RELAX_*` |
| `layout_input.py` | 1 | `layout_input_of` | 봉인 스냅샷 -> `LayoutInput` (1절) |
| `effective_placement.py` | 1 | `effective_placement` | 레이아웃 필드(설계점 스냅샷) -> 소자별 실효 배치 (2절) |
| `kernel_keys.py` | 1 | `kernel_keys` | kind 별 평가 커널 폭 키와 충돌 (3절) |
| `key_exclusion.py` | 1 | `key_exclusion` | 거절된 기하의 폭 키 제외 (7절) |
| `layout_score.py` | 1 | `layout_score` | 레이아웃 후보 점수 (3절) |
| `realized_geometry.py` | 1 | `realized_geometry` | `search.RealizedGeometry` (4절) |
| `w_loop_bound.py` | 1 | `w_loop_bound` | W_request 루프 `K_max` (5절) |
| `junction_change.py` | 1 | `junction_change` | 접합 용량 전·후 (4절) |
| `relaxation.py` | 1 | `relaxation_decision` | LY5 완화 판정 (6절) |
| `relaxation_records.py` | 1 | `relaxation_records` | 완화 기록 (6절) |
| `refilter.py` | 1 | `refilter` | 판정 축 재필터 (8절) |
| `admission.py` | 1 | `admit_candidates` | 교대 재실행 후보 (9절) |
| `alternation_bound.py` | 1 | `alternation_bound` | 교대 상한 `K_alt` (9절) |
| `place_layout.py` | 2 | `place_layout` | 커널 없이 레이아웃 놓기 (7절) |
| `converge_point.py` | 3 | `converge_point` | front 점 하나의 수렴 루프 (7절) |
| `converge.py` | 4 | `converge` | MOD8 진입점 (9절) |

공개 API(`gmid_engine.convergence.__all__`): 위 진입점 16개 + 데이터 타입·상수. 모듈 수준 상태·캐시 없음(각 호출이 인자만 읽는다).

## 1. `layout_input_of(snapshot, pdk, passives, rejected=(), relaxed=()) -> (LayoutInput, undelivered)`

`snapshot` = 봉인 점의 S2 스냅샷(`EvalResult.evaluation.snapshot`: S1 필드·`dc_op`·`dc_coord`). MOS(`dc_op` 의 소자)마다 이름순으로 `LayoutDevice`:

| 필드 | 출처 |
|---|---|
| kind·L_m·ID_A·gm_id·vds_V·vsb_V·W_m | `dc_op` (`kind`·`L`·`current`·`gm_id`·`vds`·`vsb`·`W`), float 로 |
| drain·gate·source | S1 `pins` 의 `MOS_TERMINAL_NAMES` 단자 |
| body | S1 `bulk.net` |
| diode | S1 `is_diode` |
| W_adjustable | `dc_coord[소자].role == COORD_WRITER` -- `size_and_seal(w_request=)` 가 좌표를 ln(ID·L/W) 로 바꿀 수 있는 소자만. 종속 소자는 KCL 이 전류를 정해 W 를 따로 못 정한다 |

* 행 그룹 = (kind, body 넷) 마다 하나, rid = `kind|body`, 멤버 이름순. 행 그룹 순서 = (kind, body) 정렬.
* matching 그룹: S1 `matching_groups` 중 status `derived`·`ratified` 만(graph CONTRACT 4.5a 전달 정책). role: `diff_pair`·`mirror`·`branch_symmetric` -> layout 같은 낱말 상수.
  hub = diff_pair 의 `evidence.nets[0]`(공통 source), mirror 의 `evidence.nets[1]`(source), branch_symmetric 은 None. 허용 패턴 = `PATTERNS` 전부.
  S1 `matching_dispositions` 중 `bias_distribution`·`feedback_shared`(멤버 2 이상)는 제외 role 그룹(hub None, 허용 패턴 전부). gid = `evidence.rule` 또는 disposition kind + `"|"` +
  멤버 이름순을 `"+"` 로 이은 문자열(이름 치환을 따라간다).
* **완화**(`relaxed` = gid 집합): hub 가 있는 그 그룹의 role 을 `mirror`, 허용 패턴을 `(interdigitation,)` 로 바꿔 넘긴다. hub 없는 그룹은 바꾸지 않는다.
* 레이아웃 role(제외 role 이 아닌 것) 그룹의 멤버 (kind, body) 가 둘 이상이면 그 그룹은 넘기지 않고 `undelivered` 에 `(gid, "members_span_row_groups")` 로 돌려준다
  (이름순, 조용히 버리지 않는다). 제외 role 은 이 검사를 받지 않는다.
* `rejected` = W_request 를 거부한 소자 이름(`LayoutInput.rejected_requests`, 정렬), `passives` = `layout.passives_from_decl` 결과(호출부).
* 입력 `snapshot` 은 바꾸지 않는다. 같은 입력이면 같은 결과(결정론).

**레이아웃 결과 읽기(설계 40 v1.6 §2.4.7·§2.4.8, U17 ①)**: `LayoutResult` = (설계점 스냅샷, 계산 블록 목록)뿐이다. 이 패키지는 레이아웃 값을 그 스냅샷의
`ly_*` 필드(`layout.LAYOUT_KEY`·`F_*`)에서 읽는다 -- 그룹 `ly_groups`, 입력 그룹 `ly_groups_in`, 소자 이름 = `ly_point` 열 key, finger `ly_finger`, 면적 `ly_floorplan`, 확산 `ly_diffusion`.

## 2. `effective_placement(snapshot, grid_m) -> (placements, unplaced)`

`snapshot` = `LayoutResult.snapshot`, `grid_m` = 제조 격자. 소자(`ly_point` 열 key) 이름순 `Placement(name, key, finger_w_m, n_fingers, W_m, pending, tol_effective)`:
* 놓인 소자(`ly_finger` 값 있음, 그룹의 `pending` 멤버 아님): key = `round(finger_w_m / grid)`, `W_m = DeviceFinger.W_realized_m`, `pending=False`,
  `tol_effective = DeviceFinger.tol_effective`.
* **W_request 응답 대기 그룹**(`GroupLayout.pending`)의 멤버: 레이아웃은 잠정 배치만 했다(LY3 -- W 를 바꾸지 않는다). 그 소자는 마지막 시도(`attempts[-1]`)의
  `finger_w_m`(= 요청 W / 멤버 수)와 멤버 순서의 `n_fingers` 로 key = `round(finger_w_m / grid)`, `finger_w_m = key * grid`, `n_fingers = nf`, `W_m = nf * (key * grid)`
  (레이아웃이 후보 실현 W 를 만드는 식과 같아 다음 레이아웃의 실현 W 와 비트가 같다), `pending=True`.
* `unplaced` = `ly_finger` 값이 없는(사용 가능한 폭 슬라이스가 없는) 소자 이름, 이름순.

## 3. `kernel_keys(placements, kinds, current) -> (keys, conflicts)` · `layout_score(snapshot, unplaced) -> tuple`

* 평가 커널의 `LutAccess.w_keys` 는 kind 마다 슬라이스 하나다(sizing 계약). **[개정 예정 -- design 40 v1.15.1 §3.7-A 6·10, card WB-1]**: 이 전제는 폐기된다 -- 실현 기하 입력은 소자별 `RealizedGeometry.finger`(nf, finger_w)이고 슬라이스는 DC 블록이 `lut.slice_of_finger`로 정한다; `kernel_keys`·`place_layout` kind 키 좁히기는 삭제, `key_exclusion`은 레이아웃 행 그룹 단위로 재작성. `kinds` = {소자: kind}, `current` = ((kind, 키), ...).
  `keys` = `current` 의 kind 순 ((kind, 키), ...): 그 kind 의 배치가 쓰는 키(여럿이면 가장 작은 값 -- 충돌이라 의미 없음), 배치 소자가 없는 kind 는 `current` 값.
  `conflicts` = ((kind, (사용 키 오름차순)), ...) 둘 이상 쓰는 kind.
* `layout_score` = 작을수록 좋은 사전식 점수 `(놓지 못한 소자 수, 배치 못 한 common-centroid 요구 그룹 수(CC_REQUIRED_ROLES, pattern None, pending 아님),
  pending 그룹 수, ly_floorplan.outline_area_m2)` -- `snapshot` = `LayoutResult.snapshot`.

## 4. `realized_geometry(snapshot, placements, keys) -> search.RealizedGeometry` · `junction_change(before, after)`

* `w_request` = ((소자, `Placement.W_m`), ...) 이름순 -- 배치된 **모든** 소자(LY7: W_request 유무와 관계없이 실현 기하로 재평가).
* `w_keys` = `keys` 그대로. `diffusion` = ((소자, `metrics.DiffusionGeometry(finger_w_m, ad_m2, as_m2, pd_m, ps_m, float(n_fingers))`), ...) 이름순 -- `ly_diffusion` 필드
  (= `RealizedDevice.diffusion`, LY8) 중 **`pending` 이 아닌** 소자. pending 소자는 레이아웃의 잠정 기하가 요청한 (키, nf) 와 달라 LUT 생성 규칙 기하로 둔다.
* `junction_change(before, after)` = `ss_dev` 가 든 두 스냅샷의 소자(이름순, 둘에 모두 있는 것)마다 `JunctionChange(device, cdb_before, csb_before, cdb_after, csb_after)`.

## 5. `w_loop_bound(placements, sized_w) -> (k_max, max_dlnw, tol)`

`sized_w` = {소자: 사이징 W}. `max_dlnw = max |ln(W_m / sized_w)|`, `tol = min Placement.tol_effective`(둘 다 무차원 상대량). `k_max = 1` 이면(`max_dlnw <= tol`) 한 번 평가로 판정,
아니면 `sizing.k_max(max_dlnw, tol) = ceil(log2(max_dlnw / tol))`. 배치가 없으면 `(1, 0.0, 0.0)`. 새 상수 없음.

## 6. `relaxation_decision(snapshot, relaxed) -> (relax, not_relaxable)` · `relaxation_records(first_seen, final_layout, relaxed)`

* 대상 그룹 = `role in CC_REQUIRED_ROLES` ∧ `pattern is None` ∧ `not pending` ∧ gid ∉ `relaxed`(gid 순). 이 조건은 시도 (i) nf 조정 (ii) W_request 가 모두 소진됐음을 뜻한다(조정 불가·
  요청 거부·공통 폭 없음 -- 사유 문자열을 읽지 않는다). hub 넷이 있으면(`ly_groups_in` 필드의 `hub_net`) `relax`, 없으면 `not_relaxable`.
* `relaxation_records` = gid 순 `Relaxation(gid, role(완화 전), members, reason(완화 전 `GroupLayout.reason`), attempts(완화 전), outcome, pattern, dx, dy, ok)`:
  `relaxed` 에 든 gid 는 최종 레이아웃 같은 gid 그룹이 패턴을 가졌으면 `RELAX_PLACED`(pattern·dx·dy·ok), 아니면 `RELAX_NOT_PLACED`; 안 든 gid 는 `RELAX_NOT_AVAILABLE`.

## 7. `place_layout` · `converge_point`

`place_layout(memo, snapshot, pdk, passives, rejected, relaxed, first_seen, previous, kinds, current_keys, *, donors, counters) -> PlacedLayout` -- 평가 커널 호출 0.
[XRUN-F1 B] `donors`·`counters` = 필수 키워드(기본값 없음) -- `converge_point` 가 `sctx.dc.donors`·`.counters` 에서 꺼내 넘기고 `run_layout` 에 그대로 쓴다.
`run_layout` 의 **유일한 프로덕션 호출처**. 반복(상태는 `pdk`·`relaxed` 뿐이고 둘 다 단조: 폭 키 집합은 줄고 완화 집합은 는다):
1. `layout_input_of` -> `run_layout(layout_input, memo, snapshot, previous)`(레이아웃 필드는 설계점 `snapshot` 위, 재시도는 같은 설계점 lineage) -> `effective_placement`.
   `unplaced` 가 있으면 멈춘다. `PlacedLayout` 은 입력 사본(`layout_input`)을 두지 않는다(입력은 스냅샷의 `ly_*` 입력 필드).
2. `kernel_keys` 충돌이 있으면 충돌 kind 마다 사용된 키 각각으로 PDK 폭 키를 좁혀 다시 놓아 `layout_score` 가 가장 작은 키(동점은 작은 키)로 좁힌다. 1 로.
3. `relaxation_decision` 의 `relax` 가 있으면 `relaxed` 에 더하고 1 로. `not_relaxable`·`relax` 의 완화 전 `GroupLayout` 은 `first_seen` 에 gid 별로 처음 한 번만 남긴다.
`PlacedLayout.layout_calls` = 이 호출의 `run_layout` 횟수(좁히기 시험 포함), `narrowed` = ((kind, 키), ...).

`converge_point(sctx, pdk, point) -> ConvergedPoint` -- front 점 하나 (`point` = `search.FrontPoint`, `point.result` = 봉인된 `EvalResult`):
```
current = point.result ; previous_geometry = None
loop:
  placed = place_layout(current.evaluation.snapshot, ...)          # 커널 0
  unplaced 있음                          -> STATUS_UNPLACEABLE
  geometry = realized_geometry(placed...)
  geometry == previous_geometry          -> STATUS_CONVERGED      # 고정점: 마지막 재평가 점으로 놓은 레이아웃이 같은 기하를 낳는다
  K = w_loop_bound(첫 레이아웃에서 한 번)
  (w_request, w_keys) 가 같은 상태(PDK 후보·거부·완화)에서 직전보다 앞서 이미 평가한 것 -> STATUS_NONCONVERGENT (주기; detail cycle=True) -- 다음 레이아웃은 평가 점의 DC 상태만 읽는 결정론적 사상이라 K 까지 돌아도 벗어나지 못한다(확산 기하는 출력이라 키에 넣지 않는다; 직전과 DC 상태가 같고 확산만 다르면 주기가 아니라 확산 재평가)
  재평가 횟수(제외 재시도 제외) >= K     -> STATUS_NONCONVERGENT (FailureRecord NONCONVERGENT, margin = max_dlnw / tol)
  result = search.evaluate(sctx, θ, cells, parent=current, geometry=geometry)   # 커널 1회 + 봉인 1~8 + spec 제약 행 (LY7)
  accepted(status SEALED, 제약 행 c >= 0 전부, 출발 점이 재던 (metric, 연산) 을 잃지 않음) -> current = result ; previous_geometry = geometry ; previous_layout = None (새 설계점 -- 레이아웃은 그 스냅샷 위에 다시 쓴다)
  아니면 W_request 응답 대기 소자가 있고 아직 거부 안 했으면 -> rejected += 그 소자들 (같은 current 로 반복)
  아니면 key_exclusion(...) 이 뺄 폭 키를 주면          -> pdk 에서 그 (kind, 키) 를 뺀다 (Iteration.status "excluded", 같은 current 로 반복)
  아니면                                   -> STATUS_INFEASIBLE
```
* 평가 커널은 `evaluate(geometry=)` 한 곳에서만 불린다. `ConvergedPoint.kernel_calls` = 이 점이 새로 부른 커널 호출 수(`sctx.counters["kernel_calls"]` 차이, 캐시 적중 제외),
  `layout_calls` = `run_layout` 횟수 합. **레이아웃 안 재시도(좁히기·완화)는 커널을 부르지 않는다.**
* `ConvergedPoint.result` = 마지막으로 통과한 재검증 점(수렴이면 최종 freeze 점; 통과가 없었으면 None), `layout`·`geometry`·`layout_area_m2` = 마지막 레이아웃·기하(수렴이면
  `result` 의 기하와 같다), `search_area_m2` = 출발 점의 탐색 축 면적, `power_w`·`power_resolution_w` = `result.objectives`, `iterations` = 재평가마다 `Iteration`,
  `rejected` = 거부한 소자 이름순, `narrowed` = 좁힌 ((kind, 키), ...), `junction` = `junction_change(출발 스냅샷, result 스냅샷)`, `unmatched` = 패턴 없는 그룹 ((gid, role, reason), ...),
  `undelivered`, `relaxations` = `relaxation_records`.
* 출발 점에 전류 ≤ 0 인 MOS 가 있으면 레이아웃하지 않고 `STATUS_UNPLACEABLE`(notes `nonpositive_current`).
* W_request 처리: 그룹 요청(`cc_nf`)은 `Placement.pending` 소자의 (키, nf) 로 평가한다. `finger_quantization` 요청은 `W_new = W_realized` 라 재평가가 그대로 이행한다.
  거부 -> 다음 레이아웃에서 그 그룹은 조정 불가가 되어 pattern None -> 완화 판정으로 간다(LY5: nf 조정, W 조정이 모두 불가능할 때만 완화).

`key_exclusion(pdk, placements, kinds, sized_w, keys) -> ((kind, 키), narrower_pdk)`: 재검증이 거절한 기하에서 사이징 W 대비 실현 W 어긋남 `max |ln(W_m / sized_w)|` 가 가장 큰
kind(동률은 kind 이름순)의 지금 폭 키(`keys`)를 뺀 `LayoutPdk`. 그 kind 에 남는 키가 없으면 `narrower_pdk = None`(더 시도할 폭이 없다 -> `STATUS_INFEASIBLE`).
제외 재시도 수는 PDK 폭 키 수 이하(단조 감소)라서 `K_max` 로 세지 않는다(`Iteration.status != "excluded"` 인 반복만 `K_max` 에 센다).

## 8. `refilter(points) -> (kept, dominated, folded)`

`points` = `STATUS_CONVERGED` 인 `ConvergedPoint`. `search.nondominated` 를 쓴다: 축 (`power_w`, `layout_area_m2`) 최소화, slack = 재검증 점의 활성 제약 행 c 합, 동률 폭 =
(전력: 두 점 `power_resolution_w` 중 큰 값, 면적: `layout.area_tie_m2(floorplan_a, floorplan_b)` = 격자 x max(두 점 bbox 변 4개)). `kept` = 남은 id(남기는 순서),
`dominated`·`folded` = ((id, 지배·대표 id), ...) id 순.

## 9. `admit_candidates` · `alternation_bound` · `converge`

* `admit_candidates(survivors, candidates)`: 후보(`FrontPoint`, 탐색 축에서 지배당해 front 밖이던 봉인 점)를 (전력, **탐색 축 면적**)으로, 남은 점을 (전력, 레이아웃 면적)으로 놓아
  같은 비지배 필터를 돌려 살아남는 후보를 입력 순서로 낸다 -- 후보의 레이아웃 면적은 레이아웃 전에는 모르므로 탐색 축 면적이 대리값이다(추정; 뽑힌 점은 실제로 레이아웃한 뒤 진짜 값으로 다시 거른다).
  면적 동률 폭: 남은 점 쪽 floorplan `area_tie_m2`(후보 쪽은 비교 상대 점으로 갈음, 후보끼리는 남은 점 자기 쌍 폭의 최솟값). 남은 점이나 후보가 없으면 ().
* `alternation_bound(points)` = 수렴 점들의 `layout_area_m2` 범위 / 두 점 `area_tie_m2` 의 최솟값에 대한 `sizing.k_max`(범위가 폭 이하이거나 점이 하나뿐이면 1).
* `converge(sctx, pdk_decl, points, pool=(), slice_keys=None) -> ConvergedFront`:
  1. `LayoutPdk.from_decl(lut, pdk_decl)`(`slice_keys` = ((kind, 키 tuple), ...) 가 있으면 그 kind 의 폭 키 후보를 그것으로 줄인다). `points` 에 봉인 안 된 점·제약 행 c < 0 점이 있으면 `ValueError`.
  2. 점마다 `converge_point`. 3. 수렴한 점으로 `refilter`; 첫 재필터 뒤 `K_alt` 를 한 번 정한다. 4. `pool`(봉인·c ≥ 0 인 것만) 중 `admit_candidates` 가 뽑은 점이 있고 재실행이 `K_alt` 번 미만이면
  2 로 돌아가 그 점들을 수렴시킨다(`admitted`); 재실행이 `K_alt` 번에 닿고도 후보가 남으면 `notes` 에 `nonconvergent_alternation`.
  결과: `front` = 마지막 재필터 통과 점, `dropped` = `DroppedPoint(id, DROP_DOMINATED|DROP_FOLDED|DROP_NONCONVERGED, by)`(사유·id 순), `nonconverged` = 수렴 못 한 점(상태별 `STATUS_*`), `points` = 수렴을 시도한 모든 점(처리 순서),
  `rounds`, `k_alt`, `admitted`, `perf`(points·rounds·kernel_calls·layout_calls·wall_s), `notes`(판정 축 포함 항목 `judged_axis` -- DEC-79 '매 실행 명시',
  면적 모델 오차 선언 부재 `area_model_error_undeclared`).

## 10. 다른 패키지에 더한 인터페이스 (U14)

| 위치 | 변경 |
|---|---|
| `search.RealizedGeometry(w_request, w_keys, diffusion=())` | 새 데이터 타입(`search_values.py`, `search.__all__`) |
| `search.evaluate(sctx, theta, cells, parent=None, origin=(), geometry=None)` | `geometry` 가 있으면 `size_and_seal(w_request=geometry.w_request)`·`LutAccess(memo, geometry.w_keys)`·`ss_evaluate(diffusion=geometry.diffusion)` 로 평가하고 평가 키의 `w_fixed_fp = fp_of(geometry)`. 없으면 종전과 같다 |
| `metrics.ss_evaluate(..., diffusion=())` · `metrics.ss_dev(snapshot, lut, junction, diffusion)` | 있는 소자의 cdb·csb 를 실현 확산 기하로(`junction_model` = `JUNCTION_LAYOUT_DIFFUSION`), 없는 소자는 LUT 생성 규칙. 빈 `diffusion` 은 입력 버전이 종전과 같다 |
| `metrics.passive_values(snapshot, ctx, theta)` | `ss_evaluate._passive_values` 를 새 파일로 옮겨 공개(수동소자 값 정본 -- 판정 축 면적 입력과 공유) |
| `layout.__all__` | `area_tie_m2`·`passives_from_decl`·role·패턴 이름 상수 추가 |

## 11. 불변식 (test 대상)

1. 결정론: 같은 입력이면 `PYTHONHASHSEED` 와 무관하게 `ConvergedPoint`·`ConvergedFront`(perf 의 wall_s 제외)가 같다. 이름 전단사에 대해 면적·반복 수·상태가 같다.
2. 레이아웃 안 재시도(좁히기·완화)에서 평가 커널 호출 0 -- `place_layout` 전후 `sctx.counters["kernel_calls"]` 불변.
3. 재평가는 레이아웃 결과(사용한 것)마다 1회 -- `Iteration` 수 = 새 기하 평가 수, 같은 기하 재방문은 커널 0(캐시).
4. 고정점: `STATUS_CONVERGED` 이면 마지막 `place_layout` 의 기하 == 마지막 통과 재평가의 기하.
5. `K_max`: 제외 재시도를 뺀 `Iteration` 수 <= k_max, 닿고도 고정점이 아니거나 주기(직전 앞서 평가한 DC 상태로 돌아옴)면 `STATUS_NONCONVERGENT` + `failure.failure_class == "NONCONVERGENT"`(`detail` 의 `cycle`).
6. 완화는 배치가 없고 응답 대기도 아닌 common-centroid 요구 그룹에만 하고 `Relaxation` 기록이 항상 남는다(`RELAX_*`); 완화한 그룹은 최종 레이아웃에서 role 이 `mirror` 다.
7. 재필터: `refilter` 의 `kept` 는 판정 축 값으로 서로 지배하지 않는다(동률 폭 안은 접힘); ΔA_tie 는 `area_tie_m2` 하나.
8. 접합 용량: 수렴한 점의 `result` 의 `ss_dev` 는 `layout.diffusion` 이 있는 소자에서 `junction_model == JUNCTION_LAYOUT_DIFFUSION`.

## 12. 열린 항목·설계 gap (본문 §40 §3.9 에 기록)

- 평가 커널의 폭 슬라이스는 kind 당 하나라서(`LutAccess.w_keys`) MOD8 이 레이아웃의 PDK 폭 키를 kind 당 하나로 좁힌다(`place_layout`). 소자별 슬라이스를 받는 sizing 확장이 있으면 좁히기가 필요 없다.
- 종속 소자(미러 출력·차동쌍 입력 등)는 W 를 고정 입력으로 받을 수 없어 `W_adjustable=False`: 차동쌍이 `cc_same_W` 로 서지 못하면 곧바로 완화 판정으로 간다.
- LY1 소자별 W 허용오차는 소자 사이 전류비(미러 비)를 보장하지 않아, 재평가 봉인 3 이 KCL 로 거부할 수 있다. 그때 `key_exclusion` 이 폭 키를 하나씩 빼며 다시 시도하지만(탐욕 -- 어긋남이 가장 큰 kind 부터),
  다른 kind 의 키 조합까지 완전 탐색하지는 않는다.
- 판정 축 면적 모델 오차 선언값(DEC-80 (ii))이 없어 `review_needed` 승격은 기록(탐색 축 대 판정 축 차)만 한다.
