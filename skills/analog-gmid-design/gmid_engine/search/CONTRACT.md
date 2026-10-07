# gmid_engine.search 동작 계약 (MOD6 θ 탐색 -> (전력, 면적) 비지배 front, test 작성용)

- 대상: `gmid_engine/search/` 공개 API(`gmid_engine.search.__all__`). test 는 `from gmid_engine.search import ...` 와 그보다 앞
  패키지(`core`·`lut`·`authoring`·`graph`·`sizing`·`metrics`)의 공개 이름만 쓴다(`_` 이름·파일 모듈 직접 import 금지).
  배치는 규칙 H: `gmid_engine/tests/search/test_<파일>.py`(지금은 docstring 만 있는 자리표 19개 -- 동작 test 는 독립 test
  작성자 몫), 9회로 교차는 `tests/integration/`, 불변식은 `tests/contracts/`.
- 근거: `_drafts/engine/design_mod6_search_front.md`(이하 설계, Q3·Q7·Q10 개정본), `NEW_ENGINE_DESIGN_REQUIREMENTS.md` 끝
  '확정 사항' 3(S3)·7(L bin), 계획 DEC-34·54·72·77·78·79·80·85·88·95, LR3·LR5·LR10, U-47·U-49·U-51, sizing `CONTRACT.md` r2
  (12절 O1 봉인 7), metrics `CONTRACT.md` 3.13·3.14, authoring `SPEC_CONTRACT.md`, core `CONTRACT.md`.
- 기대값은 test 쪽이 손계산·toy 커널(설계 9절 T1~T14)로 만든다(피검 함수로 기대값을 만들지 않는다). 10절 숫자는 작성자 측
  실행값(교차 확인용)이고 정본이 아니다.
- 이 브랜치는 ng-gb7 r2(2db91e2) 위에 master(8d16dd7 병합: metrics·lut r4 L bin·core pdk_decl)를 합친 상태다.

---

## 0. 파일·층·진입점 (`_module_map.LAYERS["search"]`)

| 층 | 파일 | 진입점 / 종류 |
|---|---|---|
| 0 | `search_values.py` | 데이터 선언 모듈(상태·단계·축·제약 접두 어휘, 2절 형식) |
| 1 | `archive.py` | `S3Archive` |
| 1 | `cone_rows.py` | `cone_rows` |
| 1 | `eval_key.py` | `eval_key` |
| 1 | `l_cells.py` | `l_cells` |
| 1 | `objectives.py` | `objective_values` |
| 1 | `pareto.py` | `nondominated` |
| 1 | `seal7_pending.py` | `seal_status` ★ 봉인 7 대기 스위치(4절) |
| 2 | `constraints.py` | `constraint_rows` |
| 2 | `search_domain.py` | `search_domain` |
| 3 | `search_context.py` | `build_search_context`(+ 비진입 공개 클래스 `SearchContext`) |
| 4 | `kernel.py` | `evaluate` |
| 5 | `fd_jacobian.py` | `fd_jacobian` |
| 5 | `front_query.py` | `node_across_front` |
| 5 | `start_points.py` | `start_points` |
| 6 | `slsqp_outer.py` | `solve_eps` |
| 7 | `l_bin_search.py` | `polish_l_cells` |
| 8 | `eps_sweep.py` | `sweep_front` |
| 9 | `find_front.py` | `find_front` |

계산 블록(`@compute_block`)은 없다 -- MOD6 은 조립자이고 graph 필드는 sizing 블록이 쓴다(설계 2.2). 모듈 수준 가변 캐시 없음:
평가 캐시는 `SearchContext` 객체가 소유한다.

## 1. 공개 흐름과 입력

```
dc_ctx = build_kernel_context(build_s1(...), dc_inputs_from_spec(spec), pre_layout_lut_access(memo))   # sizing, S0 당 1회
sctx   = build_search_context(dc_ctx, spec, settings, archive_root)                                  # S0 당 1회
front  = find_front(sctx, given_starts)                                                               # -> SearchFront
```

### 1.1 `SearchSettings(front_budget_s, power_resolution_w, current_bounds_a, resistance_bounds_ohm, sources)` -- frozen, 기본값 없음
| 필드 | 뜻 | 상태 |
|---|---|---|
| `front_budget_s` | front 전체 벽시계 예산 B(s) | spec `search.front_budget_s` = PA-2 결정 대기, U-47 보류 -> 부르는 쪽 선언 |
| `power_resolution_w` | 전력 축 분해능 b_P(W) | 설계 5절 '전력 격자 분해능' 정의 없음(열린 항목 S-2) -> 선언 |
| `current_bounds_a` | θ 전류 기저 상자 (lo, hi) A | GB4 상한표 미구현(S-3) -> 선언 |
| `resistance_bounds_ohm` | θ 저항 상자 (lo, hi) Ω 또는 None | 설계에 DC 경로 θ 저항 범위 출처 없음(S-3) -> 선언 |
| `sources` | ((필드, 출처 문자열), ...) | S3 runs 에 그대로 기록 |

### 1.2 `given_starts`
θ Mapping({(kind, key): 값}, 스키마 전 성분) 의 iterable. 설계 6.1 시작점 출처 ① 층 0 은 미구현(S-4), ③ 선언 x0 은 spec 필드가 없어
부르는 쪽이 넘긴다.

## 2. 값 형식 (`search_values`, 모두 frozen dataclass)

- 상태: `STATUS_SEALED`("sealed"), `STATUS_PENDING_SEAL7`("pending_seal_7"), `STATUS_UNDEFINED`("seal_undefined"),
  `STATUS_FAILED`("failed"), `STATUS_OUTSIDE_DOMAIN`("outside_domain"); `ACCEPTED_STATUSES` = (sealed, pending_seal_7) =
  탐색 경로가 따라가는 상태.
- 단계: `STAGE_START`·`STAGE_SLSQP`·`STAGE_FD`·`STAGE_L_SEARCH`. 축: `AXIS_POWER` = "power_dc_w", `AXIS_AREA` =
  "area_search_m2", `AXES`. 제약 이름 접두: `CON_SEAL6`("seal6_bulk")·`CON_INVERSION`("inversion_floor")·`CON_CONE`
  ("current_cone")·`CON_EPS`("eps") + ":" + 소자/축. 목적 축 spec 제약은 "spec:" + metric + op.
- `Variable(component, log, lo, hi)`, `SearchDomain(variables, l_cells, area_resolution_m2, power_resolution_w)`,
  `EvalKey(context_fp, schema_fp, cells, w_fixed_fp, theta_hex)`, `Objectives(power_w, area_m2, per_rail, kcl_residual_a,
  gate_area_m2, passive_area_undeclared, passive_value_undetermined)`, `ConstraintRow(name, c, active)`,
  `EvalResult(key, theta, status, evaluation, objectives, constraints, cone, failure, seq)`(eq=False),
  `StartPoint(start_id, theta, cells, source)`, `SolveResult(best, eps, minimize, iterations, restarts, stop, history, aborts=())`,
  `FrontPoint(point_id, result, origin, dominated_by=None)`, `ParetoResult(kept, folded, dominated)`,
  `SearchFront(run_id, front, pending_front, failed_eps, resolution, perf, notes)`, `NodeRow(point_id, status, voltage,
  tier, devices)`.

## 3. 함수 계약

### 3.1 `nondominated(points, ties) -> ParetoResult`
- `points` = ((id, (축 값, ...), slack), ...), 축은 모두 최소화. `ties` = 축마다 음 아닌 수 또는 `width(id_p, id_q)` 호출 가능.
  점의 축 수 ≠ ties 수 -> `ValueError`.
- 축 비교: |a − b| ≤ 폭 -> 동률, a < b − 폭 -> 나음. p 가 q 를 지배 = 나쁜 축 0, 나은 축 ≥ 1. 모든 축 동률 -> 접힘.
- 처리 순서 = (첫 축 값 오름, slack 내림, id 이름순). 그 순서로 넣으며: 이미 남은 점 k 와 모든 축 동률이면 `folded` 에 (i, k),
  k 가 지배하면 `dominated` 에 (i, k); 아니면 새 점이 지배하는 남은 점을 `dominated` 에 (k, i) 로 빼고 남긴다.
- `kept` = 남은 index 를 같은 순서로 정렬. `folded`·`dominated` 는 정렬 tuple. 결정론: 입력 순서와 무관하게 같은 결과(id 유일 시).

### 3.2 `eval_key(context_fp, schema_fp, theta, cells, w_fixed_fp) -> EvalKey`
- `theta` 가 키 정렬 쌍이 아니면 `ValueError`. `theta_hex` = 값마다 `float.hex`(1 ulp 다르면 다른 키). ε·출처는 키 밖.

### 3.3 `seal_status(evaluation) -> str` -- 4절.

### 3.4 `l_cells(lut_access, kind) -> ((lo, hi), ...)`
- 레이아웃 전 폭 슬라이스(`lut_access.w_keys[kind]`)의 L 앵커(`grids[0]`)와 `l_bins`. bin 지도가 비면 앵커마다 (a, a).
  있으면 같은 `anchor_bin` 앵커들 -> (최소, 최대); `anchor_bin` 이 None 인 앵커는 자기 칸 (a, a). lo 오름차순.

### 3.5 `cone_rows(schema, theta) -> (ConstraintRow, ...)`
- `schema.current_cone` MOS 순서대로 c = Σ항 / Σ|항|(유리수, `schema.fixed` 포함; 항 합 0 이면 c = 0). `active` 는 항상 False.
  양의 유리수가 float 0 이 되면 `ArithmeticError`. c ≤ 0 ⇔ `check_theta` 가 정의역 밖으로 거부하는 θ.

### 3.6 `objective_values(snapshot, resistances, element_values) -> Objectives`
- 노드 = `node.is_rail` 열의 key 정렬 index. 레일 = `dc_rail_v`, 노드 전압 = `dc_v`. 채널·이상 전류원 = `dc_current_basis.ends`
  (from, to) + `dc_current`(값 없는 원소 생략), DC 저항 = `basis.resistors` 중 `resistances` 에 값이 있는 것.
- `power_w` = metrics `supply_currents(...).power_dc_w`(모든 레일), `per_rail` = (레일 넷, I_k), `kcl_residual_a`.
- `area_m2` = metrics `area_search(GateArea(dc_op.W, dc_op.L) 전 MOS, PassiveArea(값 있는 수동소자, 단위 면적 None))`.
  수동소자 값이 `element_values`·`resistances` 어디에도 없으면 `passive_value_undetermined`(이름순), 값은 있는데 단위 면적
  선언이 없으면 `passive_area_undeclared`(U-36).

### 3.7 `search_domain(dc_ctx, settings) -> SearchDomain`
- `settings` 가 SearchSettings 아님 -> `TypeError`. 변수(θ 스키마 성분 순, L 제외):
  `ln_idu` = (False, kind 포락선 lo, hi): hi = 레이아웃 전 슬라이스 on_mask 격자점의 ln(ID·L/w_m) 최댓값, lo = (L, VDS, VS)
  곡선마다 gm/ID(= exp(log_GM − log_ID)) 최대 VGS 격자점의 ln IDu 중 최솟값(정점 격자점이 on_mask 인 곡선만).
  `y` = (False, 0, 1). `current` = (True, ln lo, ln hi). `resistance` = (True, ln lo, ln hi) -- 선언 None 이면 `ValueError`.
  lo ≥ hi 인 변수 -> `ValueError`.
- `l_cells` = ((MOS, l_cells(kind)), ...) MOS 이름순. `area_resolution_m2` = `lut.spec.manufacturing_grid_m` ×
  min(`lut.spec.min_finger_w_m` 값). `power_resolution_w` ≤ 0 -> `ValueError`.

### 3.8 `constraint_rows(snapshot, lut_access) -> (rows, undefined)`
- MOS 마다(`dc_op` 열 순서) tol = `dc_tol_v`; None 또는 ≤ 0 이면 `undefined` 에 이름(정렬) 하고 그 MOS 행 없음.
- `seal6_bulk:<m>` c = (min(vsb, vds + vsb) + tol)/tol. 쓰기 소자(`dc_coord.role == "writer"`)면 `inversion_floor:<m>`
  c = (ln_idu − r_peak)·gm_id/tol, r_peak = ln(curve.id_vals[argmax gm_id_vals]) + ln L − ln w_m(`gm_id_curve(memo, kind,
  w_key, L, vds, vsb)`). `active` = c ≤ 1.

### 3.9 `build_search_context(dc_ctx, spec, settings, archive_root) -> SearchContext`
- `context_fp` = fp_of((base.fp, plan_versions, lut, fixed_values, resistor_values, inputs)), `schema_fp` = fp_of(schema),
  `code_fp` = core·lut·graph·sizing·metrics·search `*.py` 바이트 sha256 묶음의 fp.
- `spec.judged_constraints` 중 metric ∈ AXES 이고 값이 있는 것 -> `judged_constraints` ((metric, op, value), ...), 나머지 ->
  `constraint_notes`(verdict `judgment_pending`, reason `metric_not_evaluable_without_ss_linearize`).
- `archive_root` 가 None 이면 S3 없음. 아니면 `S3Archive(root, context_fp, code_fp)` 이고 `disk_failures` = evals 의 ok 아닌 줄
  (같은 schema_fp·code_fp) -> {EvalKey: FailureRecord}.
- `counters` 키: requests, kernel_calls, hits, fail_hits, disk_hits, outside_domain, recompute_same_key(모두 0 시작).

### 3.10 `evaluate(sctx, theta, cells, parent=None, origin=()) -> EvalResult`
순서와 계수(정확히 이 순서):
1. requests +1. 키 = `eval_key(..., 키 정렬 θ, cells, None)`.
2. 메모리 캐시 적중 -> hits +1(실패면 fail_hits 도 +1), 같은 객체(`is`) 반환. 커널 0.
3. 디스크 실패 적중 -> disk_hits +1, `STATUS_FAILED`(failure = 디스크 레코드, seq −1), 캐시 저장. 커널 0.
4. `cone_rows` 에 c ≤ 0 -> outside_domain +1, `STATUS_OUTSIDE_DOMAIN`(seq −1), 캐시 저장. 커널 0, S3 줄 없음.
5. kernel_calls +1, seq +1, `size_and_seal(dc, θ, parent=parent.evaluation)`. `NonconvergentError`·`SealViolationError` 만
   잡아 `STATUS_FAILED` + `exc.record`. 그 밖 예외는 전파(캐시·계수는 kernel_calls 까지 증가한 채).
6. 성공: 상태 = `seal_status`. 목적 = `objective_values`(저항 = dc resistor_values + θ resistance). `STATUS_UNDEFINED` 가
   아니면 제약 = `constraint_rows` 행 + 목적 축 spec 행(`spec:<m><op>`, c = (값 − 목표)/분해능(>=) 또는 (목표 − 값)/분해능(<=),
   분해능 = b_P 또는 b_A).
7. 캐시 저장, archive 가 있으면 evals 한 줄(8절).
- 같은 키를 커널로 두 번 계산하면 recompute_same_key +1(캐시가 막으므로 정상 0).

### 3.11 `fd_jacobian(sctx, variables, x, base, cells, to_theta, origin) -> ((EvalResult | None, step), ...)`
- 스텝(base 스냅샷에서): `ln_idu` = (dc_op.vgs 를 품는 VGS 격자 칸 폭) × gm_id; `y` = 첫 w_key 슬라이스 VDS 격자 최소 간격 /
  (그 y 키를 쓰는 노드 `dc_window` 의 hi − lo)(창 없음·폭 0 -> None); `current` = 그 기저를 항으로 갖는 MOS 의 tol·gm_id 최솟값
  (없으면 전 MOS 최솟값, 그것도 없으면 None); `resistance` = (전 MOS tol 최솟값) / (|dc_drop_current|·R)(강하 0 -> 0);
  `L` = 그 변수 칸 [lo, hi] 안 L 앵커들(1 ulp 포함)만으로 dc_op.L 을 품는 앵커 간격(L == hi 면 마지막 간격) -- 이웃 bin 간격을
  쓰지 않는다.
- 스텝 0 -> (base, 0.0)(평가 없음). None -> (None, 0.0). x + h > hi 면 h = −h. h, −h 순으로: 값 = x + 스텝, bound 와 1 ulp
  이내면 bound 로 맞추고 스텝 = 값 − x; bounds 밖이거나 값 == x 면 건너뜀; 아니면 `evaluate(..., parent=base)`. 처음 받아들일
  상태인 것을 (결과, 실제 스텝)으로. 둘 다 아니면 (None, h).

### 3.12 `start_points(sctx, given) -> (starts, log)`
- 후보 = S3 runs(같은 schema_fp·code_fp)의 front·pending_front 점 θ(`theta_hex` 복원) 다음 `given`. 칸 = L 마다 [lo − ulp, hi + ulp]
  가 품는 첫 칸(없으면 `ValueError`). 후보마다 `evaluate`(id "s<n>", 1부터) 1회 -> log 항목 {id, source, status, seq, fail?}.
  받아들일 상태이고 처음 보는 키면 `StartPoint`.

### 3.13 `solve_eps(sctx, start, minimize, eps, deadline, origin) -> SolveResult`
- 변수 = domain.variables + 시작 칸이 구간인 MOS 의 L(칸 bounds). 칸이 한 점인 L 은 칸 lo 로 고정. x0 = 시작 θ(log 변수는 ln),
  bounds 로 자름. 목적 = 축 값/분해능, 제약 = 커널 행 + 원뿔 행 (+ ε 행 (ε − 값)/분해능).
- 시작점이 받아들일 상태가 아니면 즉시 `SolveResult(None, eps, minimize, 0, 0, "start_<사유>", ())`.
- 같은 x(float.hex)는 한 번만 평가. x 평가 parent = 직전 수락 반복, FD parent = 그 x 평가.
- 중단 사유: `candidate_failure`·`fd_column_failure`·`constraint_set_changed`(제약 이름 tuple 이 시작점과 다름) -> 재시작(마지막 수락
  x 중심, 반경 = (hi − lo)/2 / 2^k), `budget`(deadline 지남) -> 끝. 재시작 상한 = max(1, ⌈log2(max 반경 / 최소 FD 스텝)⌉),
  넘으면 stop `restart_cap`. `fd_column_failure` 가 마지막 수락 x 자신에서 났으면 같은 중심의 같은 열이 또 실패할 뿐이므로 stop
  `fd_column_failure_at_centre`(S-16). `aborts` = 중단 사유 목록(FD 열 실패는 "fd_column_failure:<kind>:<key>"). 정상 끝: SLSQP(ftol 1, maxiter = max(1, ⌊남은 시간 / ((n + 1)·평가 시간 중앙값)⌋)) 결과
  success 면 "converged", 아니면 "slsqp_<status>".
- `best` = 수락 반복 중 모든 c ≥ 0 이고 (목적, seq) 최소. 없으면 None.

### 3.14 `polish_l_cells(sctx, solved, deadline, origin) -> (SolveResult, ...)`
- 설계 4.3 L-b(본문 docstring). 새 칸의 L = 위로 이동이면 새 칸 lo, 아래로면 hi. 시험 조건: 받아들일 상태 ∧ (목적 감소 ∨ 음의
  제약 합 증가). 수락 = 재시작 해 목적 개선 ≥ 1(정규화 한 칸). 수락하면 그 해에서 다음 바퀴, 한 바퀴 수락 없음 또는 deadline -> 끝.

### 3.15 `sweep_front(sctx, starts, t_start) -> dict`
- 키: `solves`((id, SolveResult) -- 끝점 id "EP:<start>"/"EA:<start>", ε 점 "eps:<축>:<k>", L-b "L:<점>:<n>"), `failed_eps`,
  `resolution`(정렬 쌍: b_A_m2, b_P_w, estimated True, coarse_factor, T_refilter_s 0.0, refilter "mod8_not_implemented",
  끝점이 둘 다 있으면 N_eps·t_eps_s·T_fixed_s), `front`·`pending_front`(FrontPoint), `*_removed`((id, 지배자 id)),
  `*_folded`.
- ε 격자 점 수 = 열린 구간 (lo, hi) 안 hi − k·간격 점 수. N_ε = ⌊(B − T_fixed)/t_ε⌋. 총수 > max(N_ε, 0) 이면 간격 배수 ×2 반복.

### 3.16 `find_front(sctx, given_starts) -> SearchFront`
- `front` = 봉인된 점만(지금은 항상 ()), `pending_front` = 봉인 7 대기 비지배 점. `notes` 에 판정 보류 사유(1.1·9절).
  `perf` = counters + unique_keys, eval_time_median_s, wall_s, lut_memo_evictions, block_calls/reuses/computes/
  recomputes_same_input(sizing 계산 블록 11개 -- `dc_seal_vgs_match` 제외, S-9), n_starts, n_solves.
- `run_id` = fp_of((context_fp, code_fp, settings, 시작 θ들)). archive 가 있으면 runs 한 줄 + front·대기 front 점 스냅샷 파일.

### 3.17 `node_across_front(front, node, archive=None) -> (NodeRow, ...)`
- 원소가 `FrontPoint` 면 메모리 스냅샷, dict(runs front 항목)면 `archive.read_snapshot(entry["snapshot_ref"])`(archive 없으면
  `ValueError`). 노드 없음 -> `KeyError`. 전압 = dc_rail_v 또는 dc_v, tier = dc_writer.tier, devices = pins 에 그 넷이 있는 MOS
  ((소자, 단자들, ((vgs, vds, vsb, current, gm_id, W, L) 쌍))). 커널 호출 0.

### 3.18 `S3Archive(root, context_fp, code_fp)` -- 8절.

## 4. ★ 봉인 7 대기 스위치 (`seal7_pending.seal_status`, sizing O1)

| 입력 DcEvaluation | 결과 |
|---|---|
| report.status sealed 이고 `sealed` 있음 | `STATUS_SEALED` |
| report.status undefined, 미정 항목이 정확히 봉인 7 하나, 그 detail reason == `REASON_VDSAT_MISSING` | `STATUS_PENDING_SEAL7` |
| report.status undefined, 그 밖 | `STATUS_UNDEFINED` |
| report.status violated | `ValueError`(size_and_seal 이 예외로 내므로 도달 불가) |
| DcEvaluation 아님 | `TypeError` |

- 대기 점은 탐색이 따라가지만(목적·제약이 정의됨) **최종 `front` 에 들어갈 수 없다** -- `pending_front` 로만 나온다(봉인 7 을 통과로
  치거나 2/(gm/ID) 로 대신하지 않는다). 봉인 7 행은 제약에 없다(VDSAT 없음).
- VDSAT 접근자가 생겨 `dc_seal_saturation` 이 pass/fail 을 내면 `REASON_VDSAT_MISSING` 이 사라져 이 표의 둘째 줄이 발동 0 이 되고
  `front` 가 채워진다(코드 변경 없음). 그때 `seal7_pending.py` 는 무동작이다.

## 5. 불변식 (test 가 확인할 성질)

| # | 성질 |
|---|---|
| I-1 | 중복 평가 0: 한 실행에서 `kernel_calls == unique_keys`, `recompute_same_key == 0`(같은 θ 의 fun·jac·cons·ε 재방문은 hits) |
| I-2 | 캐시 적중은 커널·S3 줄 0, 같은 객체 반환. evals 줄 수 = kernel_calls(archive 있을 때) |
| I-3 | 같은 code_fp·S0 면 디스크 실패 적중(커널 0), code_fp 가 다르면 무효 |
| I-4 | FD 열 parent = base: 전류 성분 열에서 sizing `dc_columns` computes 0(DC 저항 전류가 같을 때) |
| I-5 | 넓은 except 없음: 커널이 낸 ValueError·TypeError 는 evaluate 밖으로 전파 |
| I-6 | 봉인 7 대기 점은 `SearchFront.front` 에 0개(4절) |
| I-7 | `nondominated` 결과는 입력 순서 섞기에 불변, kept 안 두 점은 서로 지배하지 않고 모든 축 동률도 아니다 |
| I-8 | 결정론: 예산이 묶이지 않은 실행(stop 에 "budget" 없음, SLSQP 가 maxiter 전에 끝남)은 `PYTHONHASHSEED` 무관 같은 front |
| I-9 | `node_across_front` 커널 호출 0(counters 불변) |
| I-10 | 엔진 소스 숫자 리터럴·회로 이름 0(구조 test D·E) |

## 6. S3 기록 형식 (`<root>/<context_fp>/`, 줄마다 flush)

- `evals.jsonl`: {seq, schema_fp, cells, w_fixed_fp, theta_hex, theta, status, ok, origin, fail?, objectives?{power_dc_w,
  area_search_m2}, constraints[{name, c, active}], snapshot_fp?, code_fp}.
- `runs.jsonl`: {run_id, s0, schema_fp, settings, starts, resolution, front[], pending_front[], removed[], failed_eps,
  notes, perf, code_fp}; 점 = {point_id, status, seq, theta_hex[[키, hex]], cells, power_dc_w, area_search_m2, gate_area_m2,
  passives_in_area False, active, origin, snapshot_fp, snapshot_ref}.
- `snapshots/<snapshot_fp>.json.gz`: {fp, records[{kind, key, fields{이름: {value, writer, input_version}}}]}.
- Windows 경로 길이(260자) 때문에 `root` 는 짧아야 한다(지문 두 개가 64자).

## 7. 결정론
- 정렬: θ 키·MOS 이름·front 남기는 순서(3.1). 난수 없음. 시간 의존은 deadline 과 maxiter(평가 시간 중앙값)뿐 -- I-8 조건.

## 8. 설계와 다르게 정한 점

1. 파일: 설계의 `theta_schema.py`(sizing `dc_theta_schema` 가 이미 정본)·`kernel_context.py`(sizing `KernelContext` 정본 +
   `search_context.py`)·`eval_cache.py`(캐시 = SearchContext 필드)·`budget.py`(예산 게이트는 eps_sweep 안 식)·`layer0_columns.py`
   (미구현)·`budget_point.py`(예산 선언 PA-1 대기 -- 쓰는 곳이 없어 만들지 않음)는 없다. `cone_rows.py`·`l_cells.py`·
   `objectives.py`·`seal7_pending.py`·`search_domain.py` 를 더했다.
2. L 은 소자마다(sizing 스키마 -- `l_class` proposed), "동치류 bin" = 소자별 L 칸.
3. 신뢰 상자: 전역 bounds 에서 시작해 실패 때 절반(S-7). 실패 점에 부분 목적값이 없어(size_and_seal 이 예외로 끝남) 봉인 6·7
   실패도 재시작한다(S-10).
4. 목적 값은 graph 필드가 아니라 metrics 순수 함수를 search 가 부른다(S-6). 전력 축 = power_dc_w(S-5).
5. 평가 캐시는 모든 결과의 스냅샷을 든다(설계 7.2 는 front·parent 사슬만) -- 메모리 정책은 cProfile 뒤.

## 9. 열린 항목 (결정 필요 -- 추측으로 채우지 않고 선언 입력으로 받았다)

- **S-1** spec 성능 제약(gain·GBW·PM 등 ss 영역)은 MOD5 `ss_linearize` 가 없어 잴 수 없다 -> `judgment_pending` 기록. 그 결과
  제약이 없어 전력 최소·면적 최소가 같은 점(전류 하한)으로 모여 front 가 한 점으로 줄어든다(S-12).
- **S-2** b_P '전력 격자 분해능'의 정의가 설계·계획에 없다 -> `power_resolution_w` 선언.
- **S-3** θ 전류 상자(GB4 상한표 미구현)·θ 저항 상자 -> 선언.
- **S-4** 시작점 ① 층 0(DEC-71, U-49) 미구현, `n_starts`·x0 spec 필드 없음 -> `given_starts`.
- **S-5** 전력 축: DEC-78 은 레일 공급 전류 합(`supply_current_dc`, 이름표 objective_axis power)인데 합산 레일 선언(`counted_rails`)
  이 spec 에 없다 -> 지시대로 `power_dc_w` 를 축으로 쓴다(2레일·gnd 0 이면 순서 같음, 3레일이면 다를 수 있다).
- **S-6** metrics 계산 블록 배선(S2 metric 필드) 없음 -> search 가 순수 함수 호출.
- **S-7** 신뢰 상자 초기 반경 m(DEC-34 식) -- U-47 보류라 정할 수 없음.
- **S-8** SLSQP 반복 상한 'ε 당 몫' -- U-47 보류 -> 남은 예산/((n+1)·t_eval)(시간 의존, I-8 조건).
- **S-9** sizing `__all__` 에 `dc_seal_vgs_match` 가 빠져 있다(sizing 쪽 누락) -> 블록 계수에서 제외.
- **S-10** 부분 목적값(설계 2.3)을 얻을 길이 없다(size_and_seal 실패 = 예외, 중간 스냅샷 없음).
- **S-11** FD y 스텝의 'VDS 격자 간격'(비균등 격자) -> 최소 간격으로 읽었다.
- **S-13** 원뿔 제약 정규화(설계 5절 표에 없음) -> Σ항/Σ|항|.
- **S-14** T_refilter(판정 축 재필터 시간) = 0 -- MOD8 미구현.
- **S-15** L-b 의 'LR5 격자 안' -- LR5 knee 격자 미구현이라 LUT 의 모든 L 칸이 격자다.
- **S-16** 수락된 점에서 FD 열이 양방향 모두 실패하면 설계 3절·6.2 는 '재시작'만 말한다 -- 같은 중심에서는 진전이 없다. 지금은
  그 ε 풀이를 끝내고(`fd_column_failure_at_centre`) 실패 ε 로 기록한다. 열을 고정하거나 한쪽 차분 0 으로 둘지는 결정 필요.
- **S-17** 벽시계 예산 초과: deadline 검사는 새 x 평가 때만 해서 FD 한 번·L-b 시험 한 번만큼 넘을 수 있다(실측 ≤ 10 s / 120 s).

## 10. 9회로 실측 -- 작성자 측 시연(정본 아님)

조건: LUT = `_drafts/engine/lut_slices/manifest.json` + `assets/sky130_nfet_pfet_lut_sample.npz`(옛 LUT, VDSAT 열 없음),
`pre_layout_lut_access`, spec = library(metric 이름표 = `metric_catalog()` + integration 픽스처의 mismatch_sigma_mv·
mirror_ratio_error_mv·area_layout_m2). **시연 가정(결정 대기 값, 엔진 밖)**: B = 120 s, b_P = 1e-7 W, θ 전류 [1, 100] µA,
θ 저항 [100 Ω, 100 kΩ](GB7 §10 탐침 범위), 시작점 = GB7 §10 탐침식(L = 1 µm, writer gm/ID U[6, 26] -> ln IDu, y U[0.05, 0.95],
전류 log-U, seed 1) 중 받아들인 2개(최대 200 탐침). 결과는 모두 봉인 7 대기 -> **최종 front 0점(9/9)**.

| 회로 | θ / 연속 변수 | 탐침 -> 시작점 | requests | kernel = 고유 키 | hits | recompute_same_key | 블록 reuse 비 | 평가 중앙값 | wall(s) | 풀이 수 | ε 배수 | 실패 ε | 대기 front |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| common_gate_amplifier | 9 / 6 | 2 -> 2 | 5097 | 64 | 5033 | 0 | 0.17 | 19 ms | 2.0 | 292 | 1024 | 287(FD 열 L 양방향 실패) | 1 |
| current_reuse_telescopic_ota | 105 / 54 | 200 -> 0 | 192 | 192 | 0 | 0 | -- | 163 ms | -- | 0 | -- | -- | 0(시작점 없음: no_root_in_window 191) |
| folded_cascode | 29 / 16 | 6 -> 2 | 714 | 120 | 593 | 0 | 0.19 | 282 ms | 48.6 | 11 | 64 | 7(slsqp_4) | 1 |
| ngcc_3stage_ff | 35 / 19 | 5 -> 2 | 7341 | 360 | 6922 | 0 | 0.22 | 46 ms | 20.9 | 84 | 262144 | 0 | 1 |
| nmcnr_amplifier | 36 / 21 | 8 -> 2 | 3623 | 184 | 3434 | 0 | 0.20 | 62 ms | 14.1 | 48 | 32 | 44(slsqp_4) | 1 |
| pushpull_follower_buffer | 14 / 8 | 30 -> 2 | 3927 | 133 | 3794 | 0 | 0.17 | 31 ms | 4.3 | 180 | 16384 | 175(FD 열 L) | 1 |
| sf_pushpull_output_opamp | 47 / 25 | 200 -> 1 | 1143 | 334 | 809 | 0 | 0.18 | 134 ms | 37.0 | 9 | 128 | 7(slsqp_4) | 1 |
| two_stage_ota | 16 / 9 | 7 -> 2 | 1344 | 87 | 1257 | 0 | 0.17 | 145 ms | 14.4 | 39 | 4 | 35(slsqp_4) | 1 |
| two_stage_ota_sf | 20 / 11 | 9 -> 2 | 4458 | 109 | 4349 | 0 | 0.18 | 42 ms | 6.6 | 107 | 16 | 103(slsqp_4) | 1 |

- kernel 은 탐침 선별 평가 포함. 9회로 모두 `kernel_calls == unique_keys`, `recompute_same_key == 0`, LUT memo 퇴출 0(I-1).
  requests/kernel = 5~80 배 -- 같은 x 의 fun·jac·cons·ε 재방문이 커널 0 으로 모였다(옛 SLSQP 811 중 784 중복 대조).
- 블록 reuse 비 = sizing 계산 블록(11개) reuses/calls. `block_recomputes_same_input` 1~492 -- FD 형제 lineage 사이 같은
  입력(sizing O8, graph 가 곧 캐시라 다른 lineage 값을 못 본다).
- FD 열 재사용(two_stage_ota, 열마다 sizing 블록 computes): current 열 = dc_currents 1·dc_columns **0**·dc_widths 1,
  ln_idu·y 열 = dc_columns 1·dc_widths 1·dc_currents 0, 같은 x 의 FD 반복 = 커널 0(I-4).
- 결정론: two_stage_ota 를 `PYTHONHASHSEED` 1·2 로 따로 돌려 대기 front 동일(I-8, 예산 미구속).
- front 가 한 점으로 줄어든다: 성능 제약을 잴 수 없어(S-1) 전력·면적이 같은 방향(전류 하한)으로 움직인다. ε 점은 대부분 그 한 점에
  지배당하거나 warm start 에서 ε 제약을 못 맞춰 SLSQP status 4(부등식 양립 불가)로 끝난다 -- 엔진 동작 확인용이고 front 로 의미가 없다.
- cProfile(cumtime): folded_cascode 48.6 s 중 size_and_seal 47.3 s(97%), LUT `gm_id_for_target` 27.5 s, core `fp_of` 19.5 s
  (40%), `Projection.from_snapshot` 10.6 s; two_stage_ota 14.4 s 중 size_and_seal 13.4 s, `fp_of` 8.5 s(59%). search 자체
  (키·캐시·원뿔·목적·제약·SLSQP 조립)는 2~7% -- 핫스팟은 sizing O9(투영 지문)·LUT 역산이다.
