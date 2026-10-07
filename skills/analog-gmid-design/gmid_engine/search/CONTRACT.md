# gmid_engine.search 동작 계약 (MOD6 θ 탐색 -> (전력, 면적) 비지배 front, test 작성용)

- 대상: `gmid_engine/search/` 공개 API(`gmid_engine.search.__all__`). test 는 `from gmid_engine.search import ...` 와 그보다 앞
  패키지(`core`·`lut`·`authoring`·`graph`·`sizing`·`metrics`)의 공개 이름만 쓴다(`_` 이름·파일 모듈 직접 import 금지).
  배치는 규칙 H: `gmid_engine/tests/search/test_<파일>.py`(지금은 docstring 만 있는 자리표 21개 -- 동작 test 는 독립 test
  작성자 몫), 9회로 교차는 `tests/integration/`, 불변식은 `tests/contracts/`.
- 근거: `_drafts/engine/design_mod6_search_front.md`(이하 설계, Q3·Q7·Q10 개정본), `NEW_ENGINE_DESIGN_REQUIREMENTS.md` 끝
  '확정 사항' 3(S3)·7(L bin), 계획 DEC-34·54·72·77·78·79·80·85·88·95, LR3·LR5·LR10, U-47·U-49·U-51, sizing `CONTRACT.md` r2
  (12절 O1 봉인 7), metrics `CONTRACT.md` 3.13·3.14, authoring `SPEC_CONTRACT.md`, core `CONTRACT.md`.
- 기대값은 test 쪽이 손계산·toy 커널(설계 9절 T1~T14)로 만든다(피검 함수로 기대값을 만들지 않는다). 10절 숫자는 작성자 측
  실행값(교차 확인용)이고 정본이 아니다.
- 이 브랜치는 ng-gb7 r2(2db91e2) 위에 master(8d16dd7 병합: metrics·lut r4 L bin·core pdk_decl)를 합친 상태다.
- **r2(2026-10-08, 오케스트레이터 결정 반영)**: 바뀐 곳에 `[r2]`. 요지 -- b_P 를 점마다 tol_I × |V_rail| 로 유도(S-2), θ 전류 상자를
  LUT 에서 유도(`current_box`, S-3), θ 저항 상자는 선언 필수·없으면 구조화 거부(S-3), ss 제약은 점마다 '미측정' 기록 + 연결 자리
  `ss_constraints`(S-1), 한도는 평가 수(E_B)로 세어 결정론(S-7/8), FD 양방향 실패 열은 변수 고정(S-16), sizing `__all__` 에
  `dc_seal_vgs_match` 추가(S-9). 층 0(S-4)은 설계 입력 셋이 없어 막힘(9절).
- **r3(2026-10-08, 오케스트레이터 결정 2차)**: `[r3]`. b_P 의 gm 을 동작점 gm(ID·gm/ID)으로(S-2b), **설계 개정 S-18** W ≥ W_min 제약
  (W_min = PDK 선언 `min_finger_w_m` = difftap.2, core `sky130_pdk_decl.json` 에 quantity 추가), b_A 도 PDK 선언 두 값의 곱,
  `build_search_context`·`search_domain` 이 `pdk_decl` 을 받는다, I_max 잠정 표기(S-3b).

---

## 0. 파일·층·진입점 (`_module_map.LAYERS["search"]`)

| 층 | 파일 | 진입점 / 종류 |
|---|---|---|
| 0 | `search_values.py` | 데이터 선언 모듈(상태·단계·축·제약 접두 어휘, 2절 형식) |
| 1 | `archive.py` | `S3Archive` |
| 1 | `cone_rows.py` | `cone_rows` |
| 1 | `current_box.py` [r2] | `current_box` |
| 1 | `eval_key.py` | `eval_key` |
| 1 | `l_cells.py` | `l_cells` |
| 1 | `objectives.py` | `objective_values` |
| 1 | `pareto.py` | `nondominated` |
| 1 | `seal7_pending.py` | `seal_status` ★ 봉인 7 대기 스위치(4절) |
| 1 | `ss_constraints.py` [r2] | `ss_constraint_rows` ★ ss_linearize 연결 자리 |
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
pdk    = read_pdk_decl(<PDK 선언 json>, BoundedLRU(…))                                              # core, [r3]
sctx   = build_search_context(dc_ctx, spec, settings, archive_root, pdk)                             # S0 당 1회
front  = find_front(sctx, given_starts)                                                               # -> SearchFront
```

### 1.1 [r2] `SearchSettings(front_budget_s, eval_budget, resistance_bounds_ohm, sources)` -- frozen, 기본값 없음
| 필드 | 뜻 | 상태 |
|---|---|---|
| `front_budget_s` | front 벽시계 예산 B(s) -- 바깥 정지(`wall_budget`, 기록)와 E_B 유도에만 | spec `search.front_budget_s` = PA-2 결정 대기, U-47 보류 -> 부르는 쪽 선언 |
| `eval_budget` | 커널 평가 수 예산 E_B(int) 또는 None | None -> `evaluate` 가 커널 평가 수가 n + 1(n = 정의역 연속 변수 수, FD 한 번)을 넘는 순간 E_B = ⌊B / median(평가 시간)⌋ 를 한 번 정하고 기록(`eval_budget_source` = "derived_once:floor(B/median_t_eval)@n_evals=<수>") -- 첫 평가의 LUT 파생표(tol_V) 1회 비용이 중앙값을 끌지 않게 한 sweep 뒤에 잰다. 같은 E_B 를 넘기면 같은 결과 |
| `resistance_bounds_ohm` | θ 저항 상자 (lo, hi) Ω 또는 None | PDK 선언에 수동소자 범위 없음 -> θ 저항이 있는 회로는 필수. 없으면 `search_domain` 이 `SchemaRejectedError`(3.7) |
| `sources` | ((필드, 출처 문자열), ...) | S3 runs 에 그대로 기록 |

b_P(전력 분해능)와 θ 전류 상자는 선언이 아니라 유도다(3.6·3.7·3.19).

### 1.2 `given_starts`
θ Mapping({(kind, key): 값}, 스키마 전 성분) 의 iterable. 설계 6.1 시작점 출처 ① 층 0 은 [r2] 막힘(S-4 -- 설계가 시작점을
유도하는 세 입력이 엔진에 없다, 9절), ③ 선언 x0 은 spec 필드가 없어 부르는 쪽이 넘긴다.

## 2. 값 형식 (`search_values`, 모두 frozen dataclass)

- 상태: `STATUS_SEALED`("sealed"), `STATUS_PENDING_SEAL7`("pending_seal_7"), `STATUS_UNDEFINED`("seal_undefined"),
  `STATUS_FAILED`("failed"), `STATUS_OUTSIDE_DOMAIN`("outside_domain"); `ACCEPTED_STATUSES` = (sealed, pending_seal_7) =
  탐색 경로가 따라가는 상태.
- 단계: `STAGE_START`·`STAGE_SLSQP`·`STAGE_FD`·`STAGE_L_SEARCH`. 축: `AXIS_POWER` = "power_dc_w", `AXIS_AREA` =
  "area_search_m2", `AXES`. 제약 이름 접두: `CON_SEAL6`("seal6_bulk")·`CON_INVERSION`("inversion_floor")·`CON_CONE`
  ("current_cone")·`CON_EPS`("eps")·[r3] `CON_WMIN`("w_min") + ":" + 소자/축. 목적 축 spec 제약은 "spec:" + metric + op.
- `Variable(component, log, lo, hi)`, [r3] `SearchDomain(variables, l_cells, area_resolution_m2, current_box, w_min_m, grid_m)`,
  `EvalKey(context_fp, schema_fp, cells, w_fixed_fp, theta_hex)`, `Objectives(power_w, area_m2, per_rail, kcl_residual_a,
  gate_area_m2, passive_area_undeclared, passive_value_undetermined, power_resolution_w=None)`, `ConstraintRow(name, c, active)`,
  `EvalResult(key, theta, status, evaluation, objectives, constraints, cone, failure, seq, unmeasured=())`(eq=False),
  `StartPoint(start_id, theta, cells, source)`, `SolveResult(best, eps, minimize, iterations, restarts, stop, history,
  aborts=(), frozen=())`,
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
- [r3] `power_resolution_w` = b_P = Σ_{레일 k} |dc_rail_v_k| · tol_I,k, tol_I,k = 채널 끝(`dc_current_basis.ends` 의 from·to)이
  레일 넷 k 인 MOS 중 `dc_tol_v` 가 None 이 아닌 것의 `dc_tol_v · gm_op` 최댓값, gm_op = `dc_op.current · dc_op.gm_id`(그 점의
  동작점 gm). 행이 있는 레일이 없거나 합이 0 이면 None. **봉인 3 과 다른 점**: sizing 봉인 3 의 KCL 허용오차는 `dc_gm_bound`(곡선
  전체 최대 gm × W/w_m)를 쓰고 그대로 둔다(sizing 계약 -- 봉인은 어느 동작점에서나 안전한 상계가 필요). 탐색 축 해상도는 '이 점의
  전류가 tol_V 만큼 흔들릴 때 전력이 움직이는 양'이라 점 국소 gm 이 맞다 -- gm_bound 를 쓰면 W 큰 소자에서 수십~수천 배 과대였다
  (r2 실측: ngcc 120 배, two_stage_ota_sf 2000 배). power_dc_w 는 모든 레일 합이라 합산 레일 = 모든 레일(전압 0 레일은 0 기여).
  `supply_current_dc` 는 합산 레일 선언(`counted_rails`)이 spec 에 없어 계산하지 않는다(notes `supply_current_dc_needs_counted_rails_declaration`).

### 3.7 `search_domain(dc_ctx, settings) -> SearchDomain`
- [r3] 진입 `search_domain(dc_ctx, settings, pdk_decl)`. `settings` 가 SearchSettings 아님·`pdk_decl` 이 core `PdkDecl` 아님 ->
  `TypeError`. `pdk_decl` 에 `manufacturing_grid_m`·`min_finger_w_m` 이 없으면 core 의 `pdk_quantity_undeclared` 거부 그대로.
  변수(θ 스키마 성분 순, L 제외):
  `ln_idu` = (False, kind 포락선 lo, hi): hi = 레이아웃 전 슬라이스 on_mask 격자점의 ln(ID·L/w_m) 최댓값, lo = (L, VDS, VS)
  곡선마다 gm/ID(= exp(log_GM − log_ID)) 최대 VGS 격자점의 ln IDu 중 최솟값(정점 격자점이 on_mask 인 곡선만).
  `y` = (False, 0, 1). [r2] `current` = (True, ln I_off, ln I_max): 기저 원소가 MOS 면 그 kind 의 `current_box`, 아니면 그 원소를
  항으로 갖는 `current_cone` MOS 행들의 kind 상자 (최소 I_off, 최대 I_max)(그런 행이 없으면 `ValueError`).
  `resistance` = (True, ln lo, ln hi) -- [r2] θ 저항이 있는데 `resistance_bounds_ohm` 이 None 이면 변수를 만들기 전에
  `SchemaRejectedError`(detail {gate "search_domain", reason "theta_resistance_bounds_undeclared", resistors (θ 순)}).
  lo ≥ hi 인 변수 -> `ValueError`.
- `l_cells` = ((MOS, l_cells(kind)), ...) MOS 이름순. [r3] `grid_m` = PDK `manufacturing_grid_m`, `w_min_m` = PDK
  `min_finger_w_m`, `area_resolution_m2` = grid_m × w_min_m. `current_box` = ((kind, (I_off, I_max)), ...) MOS kind 이름순
  (I_max 잠정 -- S-3b).

### 3.19 [r2] `current_box(lut_access, kind) -> (I_off, I_max)`
- I_off = 레이아웃 전 폭 슬라이스(`w_keys[kind]`)의 VGS 격자 중 0(|v| ≤ ulp(격자 끝 크기)) 인 첫 index 면에서 on_mask 이고 ID > 0
  인 점의 ID 최솟값(SPICE 오라클 `off_current_A` 와 같은 열 -- LUT VGS=0 누설 ID).
- I_max = 그 kind 의 모든 슬라이스(`slice_map` 의 (kind, *))에서 on_mask 점 ID 최댓값(각 슬라이스 자기 폭의 ID -- finger 수 상한
  선언이 없어 다중 finger 합은 넣지 않는다, S-3b). **잠정값** -- 참 상한은 선언된 최대 nf 또는 면적 상한이 필요하다(notes
  verdict `provisional`).
- VGS 0 없음 -> `SchemaRejectedError`(reason `lut_vgs_zero_missing`), 유효 점 없음 -> (reason `lut_current_box_empty`).

### 3.20 [r2] `ss_constraint_rows(evaluation, declared) -> (rows, unmeasured)`
- `declared` = ((metric, op, value), ...). 비면 ((), ()). `evaluation.sealed is None` -> ((), 선언마다 (metric, op,
  "ss_requires_sealed_snapshot")). 봉인됨 -> ((), (metric, op, "ss_linearize_unavailable")). 행은 아직 만들지 않는다.
- **연결 자리**: metrics `ss_linearize` 가 `__all__` 에 들어오면 봉인된 경우 분기 하나를 '봉인 스냅샷 -> ss 레코드 -> metric_value
  -> 정규화 행'으로 바꾼다(호출부 `evaluate` 는 그대로). 봉인 7 대기 점은 그 뒤에도 '미측정'이다(DEC-67).

### 3.8 [r3] `constraint_rows(snapshot, lut_access, w_min_m, grid_m) -> (rows, undefined)`
- MOS 마다(`dc_op` 열 순서) 먼저 [r3] `w_min:<m>` c = (dc_op.W − w_min_m)/grid_m(**설계 개정 S-18**, tol 과 무관하게 늘 있음),
  그다음 tol = `dc_tol_v`; None 또는 ≤ 0 이면 `undefined` 에 이름(정렬) 하고 그 MOS 의 나머지 행 없음.
- `seal6_bulk:<m>` c = (min(vsb, vds + vsb) + tol)/tol. 쓰기 소자(`dc_coord.role == "writer"`)면 `inversion_floor:<m>`
  c = (ln_idu − r_peak)·gm_id/tol, r_peak = ln(curve.id_vals[argmax gm_id_vals]) + ln L − ln w_m(`gm_id_curve(memo, kind,
  w_key, L, vds, vsb)`). `active` = c ≤ 1.

### 3.9 [r3] `build_search_context(dc_ctx, spec, settings, archive_root, pdk_decl) -> SearchContext`
- 정의역 = `search_domain(dc_ctx, settings, pdk_decl)`.
- `context_fp` = fp_of((base.fp, plan_versions, lut, fixed_values, resistor_values, inputs)), `schema_fp` = fp_of(schema),
  `code_fp` = core·lut·graph·sizing·metrics·search `*.py` 바이트 sha256 묶음의 fp.
- [r2] `spec.judged_constraints` 를 문서 순서로: 값 None -> `constraint_notes`(verdict `judgment_pending`, reason
  `constraint_value_pending`, decision), metric ∈ AXES -> `judged_constraints` ((metric, op, value), ...), 그 밖 ->
  `ss_constraints`(같은 형식) + `constraint_notes`(verdict `unmeasured`).
- `eval_budget` = settings.eval_budget, `deadline` = None(find_front 가 정함).
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
6. 성공: 상태 = `seal_status`. 목적 = `objective_values`(저항 = dc resistor_values + θ resistance). [r2] b_P 가 None 이면
   상태 = `STATUS_UNDEFINED`. `STATUS_UNDEFINED` 가 아니면 제약 = `constraint_rows` 행 + 목적 축 spec 행(`spec:<m><op>`,
   c = (값 − 목표)/분해능(>=) 또는 (목표 − 값)/분해능(<=), 분해능 = 그 점의 b_P 또는 b_A) + `ss_constraint_rows` 행,
   `unmeasured` = ss_constraint_rows 의 미측정 목록.
7. 캐시 저장, archive 가 있으면 evals 한 줄(8절). [r2] `eval_budget` 이 None 이고 평가 시간 수 > n 이면 E_B 를 정한다(1.1).
- 같은 키를 커널로 두 번 계산하면 recompute_same_key +1(캐시가 막으므로 정상 0).

### 3.11 `fd_jacobian(sctx, variables, x, base, cells, to_theta, origin, skip=frozenset()) -> ((EvalResult | None, step), ...)`
- [r2] index ∈ `skip`(고정된 변수) -> (base, 0.0), 평가 없음.
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

### 3.13 [r2] `solve_eps(sctx, start, minimize, eps, origin) -> SolveResult`
- 변수 = domain.variables + 시작 칸이 구간인 MOS 의 L(칸 bounds). 칸이 한 점인 L 은 칸 lo 로 고정. x0 = 시작 θ(log 변수는 ln),
  bounds 로 자름. 축 분해능 = {power: 첫 받아들인 점(시작점)의 b_P, area: b_A} -- 풀이 하나 동안 고정. 목적 = 축 값/분해능,
  제약 = 커널 행 + 원뿔 행 (+ ε 행 (ε − 값)/분해능).
- 시작점이 받아들일 상태가 아니면 즉시 `SolveResult(None, eps, minimize, 0, 0, "start_<사유>", ())`.
- 같은 x(float.hex)는 한 번만 평가. x 평가 parent = 직전 수락 반복, FD parent = 그 x 평가.
- **한도(평가 수, 결정론)**: maxiter = max(1, Σᵢ max(⌈log2((hiᵢ − loᵢ)/hᵢ)⌉, 1))(hᵢ = 시작점 FD 실제 스텝 크기 > 0 인 변수만),
  재시작 상한 = max(1, ⌈log2(max 반경 / 최소 hᵢ)⌉). 새 x 를 평가하기 전 `kernel_calls ≥ eval_budget` -> stop `eval_budget`,
  `perf_counter > deadline` -> stop `wall_budget`(둘 다 재시작 없이 끝).
- 중단 사유: `candidate_failure`·`constraint_set_changed` -> 재시작(마지막 수락 x 중심, 반경 = (hi − lo)/2 / 2^k; 중심이 바뀌면 고정
  해제). `fd_column_failure`(열 i) -> 그 점이 마지막 수락 x 가 아니면 먼저 수락(고정 해제), 열 i 를 고정(bounds lo = hi = 중심 값)하고
  같은 중심에서 다시(재시작 수에 안 넣음); 모든 변수가 고정되면 stop `all_columns_frozen`. `aborts` = 순서대로 사유("frozen:<kind>:<key>"
  포함), `frozen` = 고정한 변수. 정상 끝: SLSQP(ftol 1) success 면 "converged", 아니면 "slsqp_<status>".
- `best` = 수락 반복 중 모든 c ≥ 0 이고 (목적, seq) 최소. 없으면 None.

### 3.14 [r2] `polish_l_cells(sctx, solved, origin) -> (SolveResult, ...)`
- 설계 4.3 L-b(본문 docstring). 새 칸의 L = 위로 이동이면 새 칸 lo, 아래로면 hi. 시험 조건: 받아들일 상태 ∧ (목적 감소 ∨ 음의
  제약 합 증가). 수락 = 재시작 해 목적 개선 ≥ 1(정규화 한 칸 -- 전력은 그 바퀴 기준점의 b_P). 한 바퀴 수락 없음 또는 평가 예산·
  벽시계 도달 -> 끝.

### 3.15 [r2] `sweep_front(sctx, starts) -> dict`
- 키: `solves`((id, SolveResult) -- 끝점 id "EP:<start>"/"EA:<start>", ε 점 "eps:<축>:<k>", L-b "L:<점>:<n>"), `failed_eps`
  (항목 {eps, minimize, stop, aborts, accepted, start?}), `resolution`(정렬 쌍: b_A_m2, b_P_rule, estimated True, coarse_factor,
  E_refilter 0, refilter "mod8_not_implemented", E_B; 끝점이 둘 다 있으면 N_eps·e_eps·E_fixed·b_P_grid_w),
  `front`·`pending_front`(FrontPoint), `*_removed`((id, 지배자 id)), `*_folded`.
- ε 격자 점 수 = 열린 구간 (lo, hi) 안 hi − k·간격 점 수. N_ε = ⌊(E_B − E_fixed)/e_ε⌋(e_ε = 끝점 풀이 kernel_calls 중앙값).
  총수 > max(N_ε, 0) 이면 간격 배수 ×2 반복. 전력 간격 = max(b_P(E_P), b_P(E_A)). 비지배 필터 전력 동률 폭 = max(b_P(p), b_P(q)).

### 3.16 [r2] `find_front(sctx, given_starts) -> SearchFront`
- deadline = 시작 시각 + B. E_B 는 선언 또는 `evaluate` 의 한 번 유도(1.1) -- perf `eval_budget_source` 에 기록. ε 게이트 때
  E_B 가 아직 None 이면 N_ε = 0.
- `front` = 봉인된 점만(지금은 항상 ()), `pending_front` = 봉인 7 대기 비지배 점. `notes` 에 판정 보류 사유: constraint_notes,
  DEC-79 review_needed, DEC-72 추정, MOD8 재필터 미실행, 층 0 막힘(`layer0_inputs_missing` + 빠진 입력 목록), supply_current_dc
  미계산, ss 미측정(`unmeasured` -- 제약 목록과 점 수), 봉인 7 대기.
  `perf` = counters + unique_keys, eval_time_median_s, wall_s, lut_memo_evictions, block_*(sizing 계산 블록 12개), n_starts, n_solves,
  eval_budget, eval_budget_source, frozen_columns, stops_eval_budget, stops_wall_budget.
- `run_id` = fp_of((context_fp, code_fp, settings, E_B, 시작 θ들)). archive 가 있으면 runs 한 줄 + front·대기 front 점 스냅샷 파일.

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
| I-8 | [r2] 결정론: 같은 입력·같은 `eval_budget`(선언 또는 기록된 유도값)이고 `stops_wall_budget == 0` 이면 `PYTHONHASHSEED` 무관 같은 front -- 평가 수 예산에 묶인 실행도 포함 |
| I-11 | [r2] θ 저항이 있고 `resistance_bounds_ohm` 이 None 이면 `build_search_context` 가 `SchemaRejectedError`(reason `theta_resistance_bounds_undeclared`) -- 커널 호출 0 |
| I-12 | [r2] 봉인 7 대기 점의 ss 제약은 모두 `unmeasured`(사유 `ss_requires_sealed_snapshot`), 행 0 -- 제약이 조용히 빠지지 않는다 |
| I-9 | `node_across_front` 커널 호출 0(counters 불변) |
| I-10 | 엔진 소스 숫자 리터럴·회로 이름 0(구조 test D·E) |

## 6. S3 기록 형식 (`<root>/<context_fp>/`, 줄마다 flush)

- `evals.jsonl`: {seq, schema_fp, cells, w_fixed_fp, theta_hex, theta, status, ok, origin, fail?, objectives?{power_dc_w,
  area_search_m2}, power_resolution_w?, constraints[{name, c, active}], unmeasured[[metric, op, 사유]], snapshot_fp?, code_fp}.
- `runs.jsonl`: {run_id, s0, schema_fp, settings, starts, resolution, front[], pending_front[], removed[], failed_eps,
  notes, perf, code_fp}; 점 = {point_id, status, seq, theta_hex[[키, hex]], cells, power_dc_w, area_search_m2, gate_area_m2,
  passives_in_area False, power_resolution_w, unmeasured, active, origin, snapshot_fp, snapshot_ref}.
- `snapshots/<snapshot_fp>.json.gz`: {fp, records[{kind, key, fields{이름: {value, writer, input_version}}}]}.
- Windows 경로 길이(260자) 때문에 `root` 는 짧아야 한다(지문 두 개가 64자).

## 7. 결정론
- 정렬: θ 키·MOS 이름·front 남기는 순서(3.1). 난수 없음. [r2] 탐색 안 한도(maxiter·재시작 상한·ε 수·평가 예산)는 모두 평가 수와
  LUT 해상도에서 나온다. 시간이 들어가는 곳은 두 곳뿐이고 둘 다 기록된다: E_B 를 유도할 때 한 번 잰 t_ref(`eval_budget` 으로
  다시 넘기면 재현), 바깥 벽시계 정지(`stops_wall_budget`). 그래서 I-8.

## 8. 설계와 다르게 정한 점

1. 파일: 설계의 `theta_schema.py`(sizing `dc_theta_schema` 가 이미 정본)·`kernel_context.py`(sizing `KernelContext` 정본 +
   `search_context.py`)·`eval_cache.py`(캐시 = SearchContext 필드)·`budget.py`(예산 게이트는 eps_sweep 안 식)·`layer0_columns.py`
   (막힘, S-4)·`budget_point.py`(예산 선언 PA-1 대기 -- 쓰는 곳이 없어 만들지 않음)는 없다. `cone_rows.py`·`current_box.py`·
   `l_cells.py`·`objectives.py`·`seal7_pending.py`·`search_domain.py`·`ss_constraints.py` 를 더했다.
2. L 은 소자마다(sizing 스키마 -- `l_class` proposed), "동치류 bin" = 소자별 L 칸.
3. 신뢰 상자: 전역 bounds 에서 시작해 실패 때 절반(S-7). 실패 점에 부분 목적값이 없어(size_and_seal 이 예외로 끝남) 봉인 6·7
   실패도 재시작한다(S-10, 오케스트레이터 승인 2026-10-08). FD 열 양방향 실패는 재시작 대신 변수 고정(S-16).
6. [r2] b_P 는 상수가 아니라 점마다 유도(3.6). 풀이 하나·ε 격자·동률 폭은 그 점들의 b_P 를 쓴다(3.13·3.15).
7. [r2] sizing `__all__` 에 `dc_seal_vgs_match` 를 더했다(이 브랜치 한 줄, sizing 쪽 누락 수정 -- 블록 계수 12개).
4. 목적 값은 graph 필드가 아니라 metrics 순수 함수를 search 가 부른다(S-6). 전력 축 = power_dc_w(S-5).
5. 평가 캐시는 모든 결과의 스냅샷을 든다(설계 7.2 는 front·parent 사슬만) -- 메모리 정책은 cProfile 뒤.

## 9. 열린 항목 ([r2] 오케스트레이터 결정 2026-10-08 반영 상태)

- **S-1 (처리)** ss 제약은 점마다 `unmeasured` 로 기록(빠뜨리지 않음), 연결 자리 `ss_constraint_rows`(3.20) -- ng-sslin 의
  `ss_linearize` 가 들어오면 한 분기만 바꾼다. 그 전에는 제약이 없어 전력 최소·면적 최소가 같은 방향으로 모인다(S-12).
- **S-2 (처리)** b_P = Σ|V_rail|·tol_I(3.6). r2 는 gm_bound 를 써서 b_P 가 점 전력과 같은 크기 이상이었다 -> r3 에서 동작점 gm.
- **S-3 (처리)** θ 전류 상자 = `current_box`(3.19), θ 저항 상자 = 선언 필수·없으면 구조화 거부(3.7). **S-3b** finger 수 상한
  선언이 PDK 선언에 없어 I_max 는 단일 finger 최대 폭 슬라이스 값이다(다중 finger 소자의 상한은 열린 항목). 시연에서 θ 저항이 있는
  sf_pushpull·current_reuse 는 선언이 없어 거부된다(10절).
- **S-4 (막힘 -- 추측 없이는 구현 불가)** 설계의 층 0 최소형(설계 6.1 '① 층 0 조립점: ℓ = LR5 knee 앵커, r = 역산 후보, y = 창
  중앙', DEC-71 (4))은 세 입력이 필요한데 엔진에 없다: (a) LR5 knee(`measure_L_knee` 는 gm/ID·VDS 를 입력으로 받는다 -- 그 값이
  (b) 에서 온다) (b) (4)(a) 필요 gm(블록 gain 예산 -- GB4 상한표·GB5·`ss_linearize`) (c) (4)(c) VDS 배분의 VDsat 하한(lut VDSAT
  접근자 -- 봉인 7 과 같은 대기). y = 창 중앙만 유도 가능하다. 층 0 은 (b)·(c) 가 들어온 뒤 구현하고, 그동안 시작점은 S3 이전
  front 점 + `given_starts` 이며 notes 에 `layer0_inputs_missing` 을 남긴다. spec `n_starts`·x0 필드는 설계가 시작점을 유도하므로
  만들지 않았다.
- **S-5 (처리)** 전력 축 = power_dc_w. supply_current_dc 는 합산 레일 선언이 필요하다(notes 기록).
- **S-6** metrics 계산 블록 배선(S2 metric 필드) 없음 -> search 가 순수 함수 호출.
- **S-7 (U-47 보류 유지)** 신뢰 상자 초기 반경 m.
- **S-8 (처리)** 반복 상한·ε 수·평가 예산을 평가 수로(3.13·3.15) -- 벽시계는 바깥 정지(기록).
- **S-9 (처리)** sizing `__all__` 에 `dc_seal_vgs_match` 추가.
- **S-10 (승인)** 부분 목적값이 없어 재시작(기록).
- **S-11** FD y 스텝의 'VDS 격자 간격'(비균등 격자) -> 최소 간격으로 읽었다.
- **S-13** 원뿔 제약 정규화(설계 5절 표에 없음) -> Σ항/Σ|항|.
- **S-14** T_refilter(판정 축 재필터 시간) = 0 -- MOD8 미구현.
- **S-15** L-b 의 'LR5 격자 안' -- LR5 knee 격자 미구현이라 LUT 의 모든 L 칸이 격자다.
- **S-16 (처리)** FD 양방향 실패 열 = 변수 고정(3.13), 모두 고정되면 끝.
- **S-17** 예산 초과: 예산 검사는 새 x 평가 때만 해서 FD 한 번·L-b 시험 한 번만큼(평가 수로 n + 1 이하) 넘을 수 있다.
- **S-18 (r3 처리 -- 설계 개정)** W ≥ W_min 제약 행 c = (W − W_min)/g 를 더했다(3.8). W_min = PDK 선언 `min_finger_w_m`
  (difftap.2 = 0.42 µm, core CONTRACT 9.4 에 추가), g = `manufacturing_grid_m`. 설계 5절 제약 표에 없던 행이라 계획 기록은
  오케스트레이터 몫. b_A 도 같은 두 PDK 값의 곱(LutSpec 의 슬라이스 최소 폭 대신 -- 한 출처).
- **S-2b (r3 처리)** b_P 의 gm = 동작점 gm(3.6).
- **S-3b (잠정 유지)** I_max = 단일 finger 최대 슬라이스 ID -- 참 상한은 선언된 최대 nf 또는 면적 상한이 필요(열린 항목, notes
  `provisional`).
- **S-4** 층 0 은 ng-sslin(`ss_linearize`)·ng-seal7(VDSAT) 병합 뒤 다시 다룬다(오케스트레이터).

## 10. 9회로 실측 -- 작성자 측 시연(정본 아님)

### 10.00 [r3] r3 실측 (2026-10-08, 이 커밋 코드 -- B = 120 s 만 선언, b_P 동작점 gm, W ≥ W_min)

| 회로 | 변수 | requests | kernel = 고유 키 | 블록 reuse | E_B(유도) | 풀이 | 고정 열 | 실패 ε | wall(s) | 대기 front 점: P(W), A(m²), b_P/P, w_min 활성 |
|---|---|---|---|---|---|---|---|---|---|---|
| common_gate_amplifier | 6 | 7924 | 188 | 0.17 | 6891 | 203 | 602 | 0 | 6.0 | 4.6e-14, 1.4e-12, 0.18, 0 |
| current_reuse_telescopic_ota | -- | -- | -- | -- | -- | -- | -- | -- | -- | 거부(θ 저항 상자 미선언) |
| folded_cascode | 16 | 940 | 209 | 0.16 | 309 | 6 | 18 | 3 | 93.3 | 9.2e-6, 3.7e-9, 0.055, 1 / 1.7e-5, 1.6e-10, 0.061, 0 |
| ngcc_3stage_ff | 19 | 3941 | 240 | 0.20 | 2370 | 42 | 22 | 38 | 19.0 | 2.5e-5, 1.0e-8, 0.022, 0 |
| nmcnr_amplifier | 21 | 13963 | 356 | 0.20 | 2810 | 47 | 402 | 0 | 26.0 | 1.35e-5, 4.4e-9, 0.16, 1 |
| pushpull_follower_buffer | 8 | 26278 | 3718 | 0.17 | 4014 | 252 | 1753 | 126 | 101.4 | 5.5e-14, 1.1e-7, 0.089, 2 / 1.3e-10, 3.5e-10, 0.094, 0 |
| sf_pushpull_output_opamp | -- | -- | -- | -- | -- | -- | -- | -- | -- | 거부(θ 저항 상자 미선언) |
| two_stage_ota | 9 | 4313 | 2569 | 0.15 | 4397 | 117 | 107 | 107 | 120.1(벽시계 정지 1) | 7.8e-13, 6.4e-10, 0.041, 0 / 3.9e-11, 2.7e-10, 0.036, 0 |
| two_stage_ota_sf | 11 | 1861 | 104 | 0.16 | 4593 | 40 | 8 | 37 | 5.9 | 6.5e-6, 2.5e-8, 0.31, 0 |

- 7회로 `kernel_calls == unique_keys`, `recompute_same_key == 0`, LUT memo 퇴출 0. 대기 점 소자 W 최솟값 ≥ 0.42 µm(W_min) 전부.
- **b_P/P = 0.02~0.31**(r2 의 1~2000 배에서 내려옴). 결정론: two_stage_ota E_B = 600 선언·B = 900 s, seed 1·2 -- kernel 505·505, 대기
  front 동일.
- 남은 비물리: W ≥ W_min 을 지켜도 전류가 꺼짐 전류 근처(pW)까지 내려간다(common_gate·pushpull·two_stage 대기 점 P ~ 1e-14~1e-10 W) --
  성능 제약(S-1)이 없어서다. 실패 ε 는 SLSQP status 4·8.

### 10.0 [r2] r2 실측 (2026-10-08, r2 코드)

조건: 아래 r1 과 같은 LUT·spec·시작점 탐침(시작점 생성은 시연 하네스 몫 -- 층 0 막힘). **선언 가정은 B = 120 s 하나**이고
b_P·θ 전류 상자·E_B 는 유도, θ 저항 상자는 미선언(그래서 θ 저항이 있는 두 회로는 거부). 최종 front 0/9(봉인 7 대기).

| 회로 | θ / 변수 | 시작점 | requests | kernel = 고유 키 | recompute_same_key | 블록 reuse 비 | E_B(유도) | 풀이 수 | 고정 열 | 실패 ε | wall(s) | 대기 front (P W, A m²) | b_P(격자) / P |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| common_gate_amplifier | 9 / 6 | 2 | 382 | 37 | 0 | 0.16 | 11000 | 19 | 0 | 15(slsqp_4) | 0.6 | 1.37e-12, 6.4e-18 | 8.4e-7 / 1.4e-12 |
| current_reuse_telescopic_ota | 105 | -- | -- | -- | -- | -- | -- | -- | -- | -- | -- | 거부: `theta_resistance_bounds_undeclared` (R1, R2) | -- |
| folded_cascode | 29 / 16 | 2 | 1037 | 140 | 0 | 0.17 | 406 | 12 | 11 | 8(slsqp_4) | 53.9 | 1.52e-5, 1.35e-10 | 7.0e-6 / 1.5e-5 |
| ngcc_3stage_ff | 35 / 19 | 2 | 23962 | 1560 | 0 | 0.25 | 1555 | 76 | 1070 | 0 | 112.4 | 3.79e-4, 2.68e-8 | 4.7e-2 / 3.8e-4 |
| nmcnr_amplifier | 36 / 21 | 2 | 8890 | 1524 | 0 | 0.20 | 1891 | 48 | 255 | 0 | 102.3 | 2.71e-4, 1.34e-10 | 1.8e-4 / 2.7e-4 |
| pushpull_follower_buffer | 14 / 8 | 2 | 824 | 434 | 0 | 0.16 | 1757 | 25 | 1 | 0 | 15.3 | 3.27e-5, 3.41e-12 | 1.2e-4 / 3.3e-5 |
| sf_pushpull_output_opamp | 47 | -- | -- | -- | -- | -- | -- | -- | -- | -- | -- | 거부: `theta_resistance_bounds_undeclared` (R1a, R1b, R1c) | -- |
| two_stage_ota | 16 / 9 | 2 | 271 | 70 | 0 | 0.16 | 1199 | 7 | 0 | 3(slsqp_4) | 11.8 | 4.01e-6, 6.67e-11 | 4.8e-6 / 4.0e-6 |
| two_stage_ota_sf | 20 / 11 | 2 | 16645 | 1663 | 0 | 0.18 | 4514 | 379 | 81 | 0 | 63.3 | 6.21e-6, 8.97e-13 | 1.3e-2 / 6.2e-6 |

- 7회로 모두 `kernel_calls == unique_keys`, `recompute_same_key == 0`, LUT memo 퇴출 0, `stops_wall_budget == 0`.
- 결정론(I-8, 평가 수 예산에 묶인 실행): nmcnr_amplifier 를 E_B = 300 선언, `PYTHONHASHSEED` 1·2 로 따로 -- kernel 323·323,
  대기 front 동일.
- **b_P(S-2b)**: 유도된 b_P 가 점의 전력과 같은 크기이거나 수십~수천 배 크다(ngcc 120 배, two_stage_ota_sf 2000 배) --
  tol_I = tol_V·gm_bound 의 gm_bound(곡선 전체 gm 최대 × W/w_m)가 W 큰 소자에서 크다. 전력 축 해상도가 사실상 한 칸이라 ε 전력
  방향 격자가 비거나 배수가 커진다(ngcc ε 배수 2097152).
- **W 하한 없음(S-18)**: θ 전류 하한이 LUT 꺼짐 전류(~pA)라 전력·면적 최소화가 전류를 꺼짐 수준까지 내린다(common_gate 대기 점
  P = 1.4 pW, A = 6.4e-18 m² -- W 가 최소 finger 폭보다 훨씬 작은 비물리 점). 설계 5절 제약 표에 W ≥ 최소 finger 폭(PDK)
  행이 없어 넣지 않았다(결정 필요).
- 고정 열(S-16): ngcc 1070, nmcnr 255 -- 대부분 L 열(칸 끝에서 양방향 실패). 실패 ε 는 모두 SLSQP status 4(부등식 양립 불가).
- ss 제약은 대기 점마다 `unmeasured`(사유 `ss_requires_sealed_snapshot`)로 S3 evals 에 기록, notes 에 제약 목록.
- cProfile(cumtime): folded_cascode 53.9 s 중 size_and_seal 52.8 s(98%), LUT `gm_id_for_target` 32.0 s, core `fp_of` 20.6 s;
  two_stage_ota 11.8 s 중 size_and_seal 11.3 s, `fp_of` 7.1 s(60%). search 자체는 1~4%.

### 10.1 r1 실측 (2026-10-07, 결정 전 -- 기록)

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
