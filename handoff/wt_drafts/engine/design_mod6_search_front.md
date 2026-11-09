# MOD6 탐색·front 설계 (`gmid_engine/search/`) + 판정 축 재필터 배치

- 작성 2026-10-07. 설계 문서만 썼다(코드 없음, 저장소는 읽기만 함).
- 기준 문서와 약칭: P = `chip-design-skills/docs/01-plan/features/gain-budget-gmid-sizing.plan.md`(master 94569a3; N3.3 S3, N3.5~N3.7, N3.9 LR3·LR5·LR9, N3.13, N3.14, DEC-34·54·70~80·83, NFR-2·NFR-5). H = 같은 폴더 `.history.md`(12.3 #2 SLSQP 811회 중 784회 중복, #6 FD 한 스텝에 6.7/51 소자만 바뀌는데 전부 재계산). REQ = `_drafts/engine/NEW_ENGINE_DESIGN_REQUIREMENTS.md`(맨 끝 '확정 사항' 우선). G7 = `design_gb7_dc_canonical.md`, M15 = `design_mod1_lut_mod5_mna.md`, M7 = `design_mod7_layout.md`, R = `ROADMAP.md`, PA = `power_area_min_study.md`, PUD = `PENDING_USER_DECISIONS.md`. LC = 브랜치 `ng-lut`의 `gmid_engine/lut/CONTRACT.md` r2/r3, TV = `tol_v_measurement.md`.
- 사용자 확정 입력(이 문서는 바꾸지 않는다): S3는 설계점 단위로 기록하고 front 점·채택 해는 S2 스냅샷을 참조하며 `node_across_front`로 조회한다. 판정 축 재필터는 범위 안이다(12번 (나): floorplan 외곽 면적, 동률은 격자 한 칸). ~~L은 앵커 이산값이고 외층도 L을 연속 변수로 다루지 않는다(LR3).~~ **[정정 2026-10-07]** L은 같은 bin 안 선형 보간이다(LR3 개정, "나로 하자.") -- 외층은 bin을 고정하고 bin 안 L을 연속으로 다룬다(4.1·4.3, 계획 LR10). graph가 단일 정본이고 필드가 곧 캐시이며 graph 밖 캐시는 LUT memo 하나다. 파일 규칙 A~D를 따른다.
- 표기: **[제안]** 원칙에서 유도한 기본안, **[결정]** 사용자 몫(10절), **[추측]** 실측 근거 없음.
- **[2026-10-07 개정 -- reference 검토 Q3·Q7·Q10 추천안 확정, 사용자 "B는 추천대로 해."]** 계획 worktree `plan-rev4` 커밋 `defdc24`(DEC-88·92·95, LR10). D-1·D-2·D-4 결정됨, D-3 보류 확정, D-8·D-9 신설(10절). 아래 [개정 Q*]·[결정됨] 표시.

---

## 0. 요지

1. MOD6이 맡는 것: 평가 커널 조립 `evaluate(ctx, θ, parent)`, θ 스키마, 정규화 제약 벡터·FD Jacobian, 층 0 시작점, 외층 SLSQP(ε-제약), 탐색 축 front, 예산점의 탐색 축 풀이, S3 기록, 실패 캐시.
2. **판정 축 재필터와 MOD8 재실행의 교대는 MOD6에 둘 수 없다.** import는 작은 번호 쪽으로만 허용되므로(N3.10) MOD6은 MOD8을 부를 수 없다. 그래서 교대 루프는 `convergence/front_refilter.py`(MOD8)에 두고 비지배 필터 `search.pareto`를 재사용한다. 판정 축 예산점 확인도 같은 이유로 MOD8에 둔다(6.5절). MOD10은 MOD6 `find_front` → MOD8 `refilter_front` → MOD8 `budget_point_on_layout` → MOD9 순서로 부른다.
3. θ는 세 블록이다. 연속 θ_c(반전 좌표·θ 전류 기저·W4 y·DC 경로 미선언 저항), 이산 ℓ(L 동치류 앵커 index), MOD8이 넘기는 고정 W 집합. SLSQP는 θ_c만 움직이고, ℓ은 시작점에서 정해져 이산 국소 탐색(4.3)으로만 바뀐다(LR3).
4. **정점 근처 tol 문제의 대안**(4.2): gm/ID 역산 지표는 LC 5절 실측에서 셀 p50 222 mV, 최대 445 mV다. 기본안은 쓰기 소자의 독립 좌표를 gm_id에서 **ln(ID/W)**(전류밀도)로 바꾸는 것이다. VGS가 순방향·단조 역산으로 정해져 오차가 id_equivalent 지표(p50 3.7 mV)로 내려간다. DEC-04·DEC-70 문언 변경이라 [결정] D-1이다.
5. 중복 평가 0은 구조로 강제한다. 평가 키 = (S0 지문, 스키마 지문, ℓ, 고정 W 지문, θ_c `float.hex`)이고 ε은 키에 넣지 않는다. 그래서 같은 θ에 대한 fun·jac·constraints 호출과 ε 점 사이의 재방문이 커널 1회로 모인다.

---

## 1. 파일 목록 (`gmid_engine/search/`, 규칙 A~D)

A = 파일당 독립 진입점 1, B = helper는 그 파일에서만, C = 계산 블록 1개 = 파일 1개, D = test는 `tests/search/test_<파일>.py` 1:1.

| 층 | 파일 | 독립 진입점(A) | 계획 ID / 비고 |
|---|---|---|---|
| 0 | `theta_schema.py` | `build_theta_schema(dc_plan, s1, spec, lut_memo) -> ThetaSchema` | DEC-70 θ, G7 3.1-5 DOF 표. 성분 종류·스케일·FD 스텝·bounds·ℓ 격자(LR5) |
| 0 | `eval_key.py` | `eval_key(ctx, theta) -> EvalKey` | N3.5 실패 캐시 키 정의 한 곳 |
| 0 | `budget.py` | `eval_budget(spec, timings) -> EvalBudget` | DEC-34 식 N = ⌊(B − T_fixed)/t⌋, DEC-80 bin 2배 확대 게이트 |
| 1 | `kernel_context.py` | `KernelContext.build(s0, s1, structure, spec, lut_memo, pdk)` | S0당 1회(WP-23 (3)), 2.1절 |
| 1 | `pareto.py` | `nondominated(points, ties) -> ParetoResult` | DEC-77. 축별 동률 폭을 인자로 받고 MOD8도 쓴다 |
| 2 | `kernel.py` | `evaluate(ctx, theta, parent=None) -> EvalResult` | N3.5 커널 조립(2.2절). 계산 블록이 아니라 조립자(블록은 MOD4·MOD5 파일) |
| 2 | `eval_cache.py` | `EvalCache`(lookup·store·load_failures) | 성공·실패 캐시. 디스크 실패 캐시는 S3 evals에서 재구성(7.3절) |
| 2 | `archive.py` | `S3Archive`(append_eval·append_run·write_snapshot) | N3.3 S3, append-only, 케이스마다 flush(WP-11) |
| 3 | `constraints.py` | `constraint_vector(ctx, result, eps) -> ConstraintVector` | N3.14 정규화 margin, NFR-5 여유 바닥(5절) |
| 3 | `fd_jacobian.py` | `fd_jacobian(ctx, theta, base) -> Jacobian` | parent = base, 영향 집합만 재계산(3절) |
| 3 | `start_points.py` | `start_points(ctx, layer0, archive) -> tuple[StartPoint]` | N3.5 시작점 순서 |
| 3 | `layer0_columns.py` | `layer0_start(ctx) -> tuple[StartPoint]` | DEC-71 최소형(R D18·PUD DF-10): 기둥 KVL 조립 시작점. gain bin front 확장은 U-49 뒤 `layer0_local.py`·`layer0_assemble.py`로 추가 |
| 4 | `slsqp_outer.py` | `solve_eps(ctx, start, eps) -> SolveResult` | DEC-54, 신뢰 상자 재시작(6.2절) |
| 5 | `l_anchor_search.py` | `polish_l_anchors(ctx, solved, eps) -> SolveResult` | LR3·LR5 이산 국소 탐색(4.3절) |
| 6 | `eps_sweep.py` | `sweep_front(ctx, starts, budget) -> SearchFront` | N3.7 외층 ε 두 방향(6.3절) |
| 6 | `budget_point.py` | `solve_at_budget(ctx, front, budget) -> SolveResult` | DEC-77 예산점, 탐색 축 풀이만 |
| 6 | `front_query.py` | `node_across_front(front, node) -> tuple[NodeRow]` | 사용자 확정 S3 조회 |
| 7 | `find_front.py` | `find_front(ctx, search) -> SearchFront` | 공개 API(REQ 3.2). 위 파일들을 묶는다 |

MOD8 쪽 추가(`gmid_engine/convergence/`):

| 파일 | 진입점 | 비고 |
|---|---|---|
| `front_refilter.py` | `refilter_front(ctx, front) -> JudgedFront` | 판정 축 재필터 ↔ MOD8 재실행 교대, K_max 상한(6.4절) |
| `budget_on_layout.py` | `budget_point_on_layout(ctx, front, budget) -> JudgedPoint` | 판정 축 예산 확인(6.5절) |

`search/__init__.__all__` = `KernelContext`, `evaluate`, `find_front`, `solve_at_budget`, `solve_eps`, `nondominated`, `node_across_front`, `S3Archive`, `ThetaSchema`와 결과 타입. `solve_eps`는 MOD8이 W 고정 재풀이(M7 5절 "θ 재탐색 포함")에 쓰므로 공개한다.

---

## 2. 평가 커널

### 2.1 `KernelContext`(S0당 1회, 루프 불변식)

- 담는 것: S0, S1, S1v·`Structure`, `dc_plan`(MOD4 `compile_writer_plan`, 고정 W 집합마다 1회), `ThetaSchema`, GB4 상한표, `LutMemo`, tol_V 표(LUT derived memo), 제약 목록과 정규화 분모(5절), metric 레지스트리 항목, 목적 축 metric 이름, 예산 선언, PDK 격자.
- `LutMemo` 상한은 `LutMemo.from_sweep(lut, n_θc, U_eval)`(LC 2절)로 정한다. sweep 단위는 SLSQP 한 반복의 FD Jacobian(n_θc + 1 평가)이다(M15 2.6). 생성 계수 = S0당 1이고 `test_kernel_context_built_once_per_s0`로 확인한다.
- 고정 W 집합이 바뀌면 `dc_plan`과 스키마가 바뀐다(G7 3.2-4: 고정 W 소자의 반전 좌표가 종속이 됨). 컨텍스트를 새로 만들지 않고, 컨텍스트 안의 `(고정 W 지문 → dc_plan, schema)` 필드가 늘어난다. 같은 지문이면 재사용한다.

### 2.2 계산 블록 순서와 블록별 입력 필드(N3.5, M15 3.5)

| 순 | 블록(파일) | 읽는 입력 필드 | 쓰는 필드 | 이 블록을 무효화하는 θ 성분 |
|---|---|---|---|---|
| ② | `sizing/block_currents` | θ 전류 기저, `matching_ratio`, `value_dc_amp`, S1 KCL | `branch_i`, `device_id` | 전류 성분 |
| ③ | `sizing/block_lengths` | ℓ(앵커 index), LR 입력 | `l_class` | ℓ(이산, FD 대상 아님) |
| ④ₖ | `sizing/block_columns`(SCC k마다 필드 1) | `rail_v`, 앞 SCC 노드, SCC 안 쓰기 소자의 반전 좌표, `l_class`, 저항 강하용 `device_id`, SCC 안 y | `scc[k]`, `path_values`, `column_window` | SCC k가 읽는 반전·y·저항 성분, 상류 SCC version |
| ⑤ₘ | `sizing/block_widths`(소자마다) | `device_id[m]`, 반전 좌표 또는 종속 gm_id, `l_class`, VDS·VSB(node_v 파생), 고정 W | `w[m]` | 소자 m의 다섯 입력 |
| 봉인 i | `sizing/seal/item{i}` | G7 3.6 표 | `seal[i]` | 표의 읽기 필드 |
| ss | `metrics/ss_linearize`(소자마다) | 봉인 op, `w[m]`, finger_w 폭 키 | `ss.dev[m]` | 소자 m의 op·W |
| ls | `metrics/ls_fields` | `ss`, node_v, 부하 선언 | `ls.*` | 해당 노드 경로 소자 |
| GB5 | `metrics/compensation` | 기준 소자 `ss.dev`, S1v 극점 노드, spec 목표 | `ss.passive`, `ss.comp_constraints` | 기준 소자 `ss` version |
| mna | `metrics/mna_build`(뷰마다) | `ss.dev` 전체, `ss.passive`, 뷰 | `ss.mna[v]` | 어느 `ss.dev`든 |
| freq | `metrics/mna_solve`(뷰마다) | `ss.mna[v]` | `ss.freq[v]` | 조립 version |
| ① | 제약 판정(`search/constraints`가 읽음) | `ss.comp_constraints`, `ls`, `ss.freq`(PM) | 제약 벡터 | -- |
| ⑥ | `metrics/evaluate` | 레지스트리 항목별 reads | `metrics` | 읽는 필드 |
| 목적 | `metrics/power`·`metrics/area`(⑥ 변형군) | 전력: `branch_i`, node_v(저항), 이상원 / 면적: `w`, `l_class`, 선언 수동소자 | `metrics.power`, `metrics.area_search` | 위 필드 |

- **재사용 규칙**(G7 6절 `reuse_or_compute`): parent 스냅샷의 같은 필드가 같은 `input_fp`를 가지면 객체를 공유하고 계산하지 않는다. 값이 같으면 version을 유지해 하류 재계산을 끊는다. MOD6이 넘기는 parent는 FD 열 = base, SLSQP 다음 반복 = 직전 수락 반복, ε 다음 점 = 직전 ε 해, L 이웃 = 이전 해, MOD8 재풀이 = 그 front 점이다.
- **gm/ID 매개화의 구조적 이득**: VGS가 ID를 포함하지 않으므로(DEC-70) 전류 성분의 FD는 ④를 건드리지 않는다. 그 가지 소자의 `device_id` → ⑤ W → `ss.dev` → mna·freq·metric만 다시 계산한다. 예외는 가지에 DC 저항이 있을 때로, 그 저항 강하를 읽는 SCC만 다시 돈다.
- MNA 조립은 `ss.dev` 하나만 바뀌어도 다시 한다. 파일럿 135.6 µs = 평가의 0.17%다(DEC-74 실측). 부분 스탬프 갱신은 cProfile(U-49) 근거가 생기기 전에는 만들지 않는다(DEC-76).

### 2.3 `EvalResult`

- 담는 것: `key`, `ok`, 성공 시 `SealedSnapshot`·`ss`·`ls`·`metrics`, 실패 시 `FailureRecord{class, devices, margin, detail}`, 부분 목적값, 봉인 항목별 잔차·여유, 블록 카운터 델타.
- 부분 목적값: 전력은 ②만으로 계산되므로(노드전압 의존은 DC 저항 항뿐) ④·봉인 실패에도 있다. 저항 항이 있는 회로에서 ④가 실패하면 `None`이다. 면적은 ⑤까지 끝나야 있다. SLSQP의 실패 처리는 6.2절이다.

---

## 3. FD Jacobian (`fd_jacobian.py`)

- **전진 차분**, 열마다 `evaluate(ctx, θ + hᵢeᵢ, parent=base)` 1회라 영향 집합만 다시 계산된다. 기대값은 G7 3.1-6 영향 표(θ 성분 → 전이적으로 읽는 필드)다. test `test_fd_step_recomputes_only_impact_set`가 열마다 재계산 필드 집합 = 영향 표를 확인한다.
- **스텝 hᵢ**(상수 없이, 그 좌표의 LUT 해상도에서; 계획 N3.7 DOF "FD 스텝 = 해당 변수의 LUT 격자 간격"과 같은 규칙):
  - 반전 좌표 ln(ID/W): 조회점의 VGS 격자 간격 × gm/ID(d ln ID = (gm/ID)·dVGS). gm_id 좌표를 유지하는 D-1 (가)에서는 이웃 격자점의 gm/ID 차.
  - y: VDS 격자 간격 / 그 노드 창 폭. 전류: 상대 스텝 = 가지 소자 `tol_V(id_equivalent) × gm/ID`의 최솟값(M7 L1 W 허용 상대오차와 같은 식). 저항: I·R 강하가 tol_V가 되는 ΔR.
  - 다선형 보간은 칸 안에서 선형이므로, 격자 간격 스텝은 칸 경계의 꺾임을 가로지르는 할선이 되어 국소 잡음에 강하다.
- **열 점 실패**: 후진 스텝(−hᵢ)으로 다시 계산한다. 둘 다 실패하면 그 열은 봉인 6·7 margin만 채우고, 목적·metric 행은 `None`으로 두고 6.2절 재시작 규칙으로 넘긴다.
- **커널 연속성 요구(MOD4 계약)**: SCC 풀이가 |Δ| ≤ tol_V에서 멈추면 출력이 θ에 대해 최대 tol_V 크기의 계단 함수가 되어 FD 열이 0 또는 큰 값이 된다(gm/ID 역산 tol_V는 수백 mV라 치명적). 요구 [제안]은 둘이다. (i) 1변수 bisection의 마지막 구간에서 할선 한 스텝으로 끝내 출력이 θ에 연속이 되게 한다. (ii) SCC 수렴 판정·K_max는 **id_equivalent 셀 tol**을 쓰고 봉인 판정 tol과 분리한다. G7 3.4 개정이 필요하므로 [결정] D-5다.

---

## 4. 외층 결정변수 θ

### 4.1 스키마(`ThetaSchema`, S0와 고정 W 집합마다 1개)

| 성분 | 정의(출처) | 범위·스케일 | SLSQP |
|---|---|---|---|
| 반전 좌표 r_m | G7 3.1 쓰기 계획의 **트리 엣지 소자(쓰기 소자)**마다 1. 비트리 소자(equal_vgs 둘째, 차동쌍 둘째, kvl_branch 종속 멤버)는 VGS 정합으로 종속(G7 3.3) | 4.2절 | 연속 |
| θ 전류 기저 I_b | KCL·전류 강제로 정해지지 않는 가지 전류의 독립 기저(결합변수 y의 전류 분할 포함, 이름 정렬, DEC-70) | (0, GB4 표 행 최대 ID], ln 좌표 | 연속 |
| y_n | W4 노드 창 위치 ∈ [0, 1](G7 3.4) | 고정 bounds | 연속 |
| R_k | DC 경로 미선언 저항(DEC-70 잎 가지치기 후) | ln 좌표 | 연속 |
| b_c | **[개정 Q10 (i), 계획 LR10]** L 동치류마다 PDK 모델 **bin index**(LR3 bin 지도) | LR5 격자가 닿는 bin | **이산, SLSQP 밖**(4.3절) |
| ℓ_c | L 동치류마다 **bin 안 연속 L**(LR3, 사용자 2026-10-07 bin 안 선형 보간) | [그 bin의 양끝 LUT L 점] | 연속 |
| C_k, R_k(보상) | **[개정 Q7, 계획 DEC-92]** 값 미선언 보상 수동소자(극점 노드 사이)와 구조 규칙(R = 1/Σgm)으로 정해지지 않는 영점 상쇄 저항 | ln 좌표, bounds = PDK 수동소자 범위 선언 [제안] | 연속 |

스키마 지문 = 성분 목록·종류·좌표 정의·고정 W 집합의 지문이다. 지문이 다르면 θ 값이 같아도 다른 평가이므로 평가 키에 들어간다. `dof_rank_sample_count` 수치 rank(N3.7 DOF)는 이 스키마 위에서 재고, DEC-76에 따라 발동 시 구현한다.

### 4.2 반전 좌표 선택 -- 정점 근처 tol 문제(TV, LC 5절) [결정 D-1]

**문제(실측)**: gm/ID 역산 지표 tol_V는 셀 p50/p90/max = nmos 222/286/402 mV, pmos 224/371/445 mV다(LC 5절, 보간 축 LOO). 정점 근접(r = g/g_peak > 0.95)에서 커진다(TV 2절: nmos 최대 288 mV가 r ≥ 0.95에 몰림). 같은 셀의 id_equivalent 지표는 p50 3.7 mV로, 차이는 조건수 1/(d(gm/ID)/dVGS)가 정점에서 발산하기 때문이다. gm_id를 독립 변수로 두면 세 문제가 생긴다. (a) 봉인 2 허용이 수백 mV라 무력하다. (b) 정점 근처 FD에서 VGS가 크게 튀어 Jacobian이 나빠진다. (c) 정점 위 목표는 `lut_no_strong_inversion_root`라는 불연속 실패이고, 정점이 (L, VDS, VSB)마다 달라 bounds가 상태에 의존한다.

| 안 | 쓰기 소자 독립 좌표 | VGS 결정 | 봉인 2 지표 | 장점 | 단점 |
|---|---|---|---|---|---|
| (가) 현행 | gm_id | `vgs_for_gm_id` 역산(분지 규칙) | gm_id_inverse | 계획 문언 그대로, 방법론 언어 | 위 (a)(b)(c) |
| (나) 혼합 | 정점 근접 소자만 VGS, 나머지 gm_id | 영역별 | 영역별 | 강반전 쪽은 현행 유지 | 영역 경계가 θ에 따라 바뀌면 스키마가 바뀌어 SLSQP 중 불가. 실행마다 시작점 영역으로 고정해야 하고 경계 판정 식이 새로 필요 |
| (다) VGS | VGS | 그대로(역산 없음) | 순방향만 | 역산 오차 0 | 같은 반전 수준이라도 VSB(체효과)에 따라 VGS가 움직여 y·source 노드와 결합이 늘어남. 범위 [VGS_peak, VGS_max]가 상태 의존 |
| **(라) ln(ID/W)** | 전류밀도 `ln IDu`(LC `op_point.IDu` = ID·L/w_m) | ID가 VGS에 엄격 단조라 강반전 분지(VGS ≥ VGS_peak) 위에서 유일 역산. 오차 = Δln ID/(gm/ID) = id_equivalent | id_equivalent | 정점에서도 조건수 유한(약반전에서 오히려 작음). 반전 수준이 VSB에 1차로 무관. **W = I·L/IDu로 역산 없이** 나옴. ℓ이 바뀌어도 같은 r로 시작하면 반전 수준이 유지돼 warm start가 좋다 | DEC-04·DEC-70 "셀별 gm_id" 문언 변경. MOD1 진입점 `vgs_for_current_density` 추가. 방법론 보고는 gm_id(파생값)로 |

**[결정됨 (2026-10-07)] (라)** -- 사용자 "B는 추천대로 해."(reference 검토 Q3 (i)), 계획 DEC-88(DEC-04·DEC-70 문언 개정, 봉인 2 = ID 환산 지표). 같은 결정으로 봉인 7 = `VDS − VDsat ≥ +tol_VDsat`(VDSAT 열, Q3 (ii) (C)).

**기본안 (라)** [확정]
- 반전 수준 하한(조회점의 정점 ln IDu)은 상태 의존이므로 bounds가 아니라 부등식 제약으로 둔다. margin = (r − r_peak)·(gm/ID)/tol_V(id_eq)이고 연속이다. 상한은 LUT VGS 축 끝 ln IDu의 포락선(전 VDS·VS 격자 최댓값)을 bounds로 쓴다.
- 종속 소자 gm_id는 노드 VGS에서 `op_point`로 순방향으로 구한다(역산 아님).
- MOD1 추가 `vgs_for_current_density(memo, kind, w_key, ln_idu, L, vds, vsb)`: LC 3절 분지 규칙과 같은 구간 선택(정점 이상) 위에서 `gm_id_curve.id_vals`에 ln 선형 역보간한다. `gm_id_for_target(current=…, W=L)`로도 같은 값을 낼 수 있지만 W = L 우회는 읽는 사람을 속이므로 진입점을 따로 둔다. 소비자가 MOD6이므로 DEC-76에 맞는다.
- 층 0 역산(DEC-71 (4)(a) `gm_id = gm/ID`)은 그대로 두고, 결과 gm_id를 같은 곡선에서 ln IDu로 한 번 바꿔 시작점 r로 넘긴다(루프 밖 1회). 결과 JSON·front 표에는 gm_id를 파생값으로 함께 낸다.

### 4.3 L 이산 처리(LR3) [결정 D-2]

**[결정됨 (2026-10-07)]** 기본안(L-a + L-c + front 점에만 L-b) 채택 -- 사용자 "B는 추천대로 해."(Q10 (i)), 계획 **LR10**. 단 같은 날 L 결정 "나로 하자."(bin 안 선형 보간)로 이산 대상이 'L 앵커'가 아니라 **bin 벡터 b**로 바뀌었다: SLSQP는 b를 고정하고 bin 안 ℓ을 연속으로 움직이며, L-a = 시작점 b 고정, L-c = b가 다른 시작점끼리 분지, L-b = front 점에서 동치류마다 인접 bin(LR5 격자 안)으로 한 칸 이동 시험. 아래 표의 'ℓ_c ± 1 앵커'는 'b_c ± 1 bin'으로 읽는다(T3 test도 같다).

| 방식 | 내용 | 평가 수 | 비고 |
|---|---|---|---|
| L-a 시작점 고정 | ε 풀이마다 시작점의 ℓ을 그대로 둔다(LR3 "시작점의 L 앵커를 그대로 쓴다") | 추가 0 | 계획 문언 그대로. 시작점 ℓ이 나쁘면 front가 좁아진다 |
| L-b 이산 국소 탐색 | SLSQP 수렴점(θ_c*, ℓ)에서 동치류 c를 이름 순으로 돌며 ℓ_c ± 1 앵커(LR5 격자 안)를 시험한다: ① 같은 r·I·y로 커널 1회 ② 봉인 통과이고 활성 제약 위반이 줄거나 목적이 개선된 후보만 SLSQP 재시작 ③ 현 ε에서 목적 개선이 그 축 분해능 max(격자 분해능, 모델 오차) 이상이면 수락. 한 바퀴에 개선이 없으면 끝 | 바퀴당 ≤ 2·n_c 평가 + 통과 후보 SLSQP | LR5 확장 규칙과 같다. 상한 = Σ_c 동치류 격자 크기. 유한 격자·비증가라 종료 보장(N3.7 중층 상한과 같은 논리) |
| L-c ℓ 분지 multi-start | 층 0 시작점·S3 feasible 점 중 ℓ 벡터가 다른 것을 서로 다른 분지로 보고 각자 SLSQP(N3.5 '분지') | 시작점 수 × SLSQP | 정밀 경로 없이 ℓ 다양성 확보 |

**기본안** [제안]: L-a + L-c로 양 끝과 ε 점을 풀고, **비지배 필터를 통과한 front 점에만** L-b를 한 번 돌린다. 새 점은 같은 필터에 다시 넣는다. ε 점마다 L-b를 돌리면 평가가 ε 수 × 2·n_c배로 늘어 PA-2 시간 예산을 넘는다(파일럿 n_c ≈ 10 [추측]). L-b 수락 분해능은 NFR-5 바닥이고, 모델 오차가 측정되기 전에는 격자 분해능만으로 판정하되 그 수락을 '추정'으로 표기한다(DEC-72).

---

## 5. 제약 함수와 margin 정규화(N3.14)

SLSQP 부등식은 cⱼ(θ_c) ≥ 0이고 **전부 무차원**이다. 분모는 그 양의 판정 분해능이고 상수는 두지 않는다.

| 제약 | cⱼ | 분모 sⱼ |
|---|---|---|
| metric 선언 `metric op value`(외층 판정, DEC-74) | `>=` (m − v)/s, `<=` (v − m)/s. dB·deg metric은 그 단위로 | NFR-5 바닥 = max(격자 분해능, `value_from_model_error`). 모델 오차 미측정이면 격자 분해능을 쓰고 '여유 판정 보류'로 표시 |
| GB5 보상 gm_i ≥ gm_req(DEC-70) | (gm_i − gm_req)/s | gm_req·(gm/ID)_i·tol_V(id_eq)_i(ln ID 오차가 (gm/ID)·tol_V라서 gm 상대 분해능이 된다) |
| 슬루 I_max,k ≥ SR·C_k | (I − SR·C)/s | SR·C·(gm/ID)·tol_V(id_eq)(공급 셀 기준) |
| 기생 PM(LR6) | (PM − PM_t)/s | `pm_ss_deg`의 NFR-5 바닥 |
| 봉인 7 포화 여유 | **[개정 Q3 (ii)]** (VDS − VDsat − tol_VDsat)/tol_VDsat(소자마다, VDsat = VDSAT 열) | 그 소자 셀 tol_VDsat(VDSAT 열 LOO, 계획 DEC-88) |
| 봉인 6 벌크 | (역바이어스 + tol_V)/tol_V | 같음 |
| 반전 하한(D-1 (라)) | (r − r_peak)·(gm/ID)/tol_V(id_eq) | 위 식 |
| ε 제약 면적 방향 | (ε_A − A_search)/b_A | b_A = 면적 축 bin 폭(DEC-80 (ii)) |
| ε 제약 전력 방향 | (ε_P − P)/b_P | b_P = max(전력 격자 분해능, 전력 모델 오차)(DEC-72·78) |

- **봉인 1·2·3·4·5·8**(일관성 게이트)은 최적화 제약으로 두지 않는다. 위반은 커널 결함이나 풀이 실패이므로 그 점은 실패 레코드다(6.2절). 6·7은 물리 여유라 연속 제약으로 노출해 SLSQP가 경계로 미는 정보로 쓴다.
- 목적도 전력/b_P, 면적/b_A로 정규화한다. SLSQP가 스케일에 민감하고, 분모는 위와 같은 분해능이다.
- 활성 판정(NFR-5 보고): 해에서 cⱼ ≤ 1(여유가 분해능 한 칸 이하)이면 활성이다. 활성 제약 여유가 바닥을 넘으면 '스펙 오버'로 보고한다. DEC-80 '해상도 굵음'이 켜진 실행은 굵어진 bin 기준임을 함께 적는다.
- 실패 레코드 margin은 클래스 안에서만 비교한다. 시작점 선택(N3.5)에서 클래스가 다른 margin을 섞어 '거의 feasible'로 쓰지 않는다.

---

## 6. 탐색 절차

### 6.1 시작점(N3.5)

순서는 ① 층 0 조립점(DEC-71 최소형: ℓ = LR5 knee 앵커, r = 역산 후보, y = 창 중앙 [제안]) ② 같은 S0·스키마 지문의 S3 feasible 점 상위 `n_starts`(선언값; 정렬은 비지배 순위 → 활성 여유 합 → 이름순) ③ 선언 x0이다. 같은 ℓ 벡터끼리는 θ_c 거리가 가장 먼 순서로 고른다. 모든 시작점은 평가 1회로 봉인 통과를 확인한다(R K8 완료 조건).

### 6.2 `solve_eps`(외층 SLSQP, DEC-54)

- `scipy.optimize.minimize(method="SLSQP")`의 `fun`·`jac`·`constraints[].fun/jac`는 모두 같은 `evaluate` 결과를 읽는다. 같은 x로 다섯 번 불려도 커널은 1회이므로 H 12.3 #2의 784/811 중복은 구조적으로 0이다. 반복 간 parent는 직전 수락 반복이다.
- **신뢰 상자**: 초기 bounds = 시작점 근방 격자 반경(N3.7 인계 "격자 반경")이다. 성분마다 반경 = FD 스텝 hᵢ × 2^m이고 m은 DEC-34 예산 식에서 정한다. feasible이 없으면 2배씩 넓혀 전역 bounds까지 간다.
- **실패 점 처리**: 부분 목적값이 있고 실패 클래스가 봉인 6·7(물리 여유)이면 목적 = 부분값, 제약 = margin을 돌려주고 계속한다. 그 밖(④ 실패로 목적 없음, 일관성 게이트 위반, NONCONVERGENT)이면 `CANDIDATE_FAILURE_CLASSES`만 이름으로 잡아 그 실행을 끊고, 마지막 수락 반복에서 상자 반경을 절반으로 줄여 재시작한다. 재시작 상한은 ⌈log2(초기 반경/hᵢ)⌉(K_max와 같은 bisection 논리)이고, 닿으면 그 ε을 '실패 ε'로 기록한다. 상수 페널티는 쓰지 않는다(N3.5).
- 종료: SLSQP 수렴(`ftol` = 정규화 목적 한 칸 = 1) 또는 반복 상한(= DEC-34 식의 ε당 몫 / (n_θc + 1)).

### 6.3 탐색 축 front `sweep_front`(N3.7 외층, DEC-77·80)

1. **양 끝점**: E_P = 전력 최소(ε 없음), E_A = 탐색 축 면적 최소(ε 없음). 6.1절의 모든 분지에서 풀어 축별 최솟값을 끝점으로 한다.
2. **ε 격자**: 면적 방향은 A(E_A) < ε_A < A(E_P)를 b_A 간격으로 E_P 쪽부터 풀고, 직전 해를 다음 점의 시작점으로 쓴다(warm start). 전력 방향은 P(E_P) < ε_P < P(E_A)를 b_P 간격으로 푼다. 두 방향을 모두 돌아야 양 끝이 덮인다.
3. **예산 게이트**(DEC-80): ε 점 총수가 N_ε = ⌊(B − T_fixed − T_refilter_est)/t_ε⌋를 넘으면 간격을 2배씩 넓히고 확대 배수 n과 사유를 기록해 '해상도 굵음(n)'을 표기한다. t_ε = 끝점 풀이 실측 중앙값, B = `wall_clock_budget_s`다(**[결정] D-3 -- 보류(사용자 2026-10-07 Q10 (ii)), 새 커널 cProfile(U-49) 뒤 재질의, 계획 U-47**, PUD PA-2).
4. **비지배 필터**(`pareto.nondominated`): 축 (전력, 탐색 축 면적), 동률 폭은 면적 b_A·전력 b_P다. 두 축이 모두 동률이면 같은 점으로 접고, 남기는 순서는 전력 작은 쪽 → 활성 여유 합 큰 쪽 → 점 id 이름순(NFR-4)이다. 지배당한 ε 해는 버리고 `dominated_by`를 기록한다(PA 2.4 국소해 실례).
5. **L-b**는 front 점에만 돌리고 새 점은 4로 되돌린다(4.3절).
6. 산출 `SearchFront` = 점마다 {point_id, ℓ, θ_c, 스냅샷, P, A_search, 활성 제약, gain 예산(층 0이 있으면), 출처 ε} + 실패 ε 목록 + 해상도 표기.

전력·면적 축의 `verified_by`나 모델 오차가 없는 동안 front는 '추정'이고 판정·보고 값으로 쓰지 않는다(DEC-72·77). 수동소자 회로에 면적 선언이 없으면 `review_needed`다(DEC-79).

### 6.4 판정 축 재필터 ↔ MOD8 교대(`convergence/front_refilter.py`, DEC-79·LR9, 12번 (나))

1. front 점마다 `converge(ctx, p)`(MOD8 W_request 루프, M7 5절)로 수렴 스냅샷 p′를 얻는다(W 고정 재풀이로 θ가 바뀔 수 있다). p′에서 floorplan 외곽 면적 A_L = bbox_w·bbox_h, P, A_search를 다시 재고, 탐색 축 대 판정 축 차를 기록한다.
2. **판정 축 비지배 필터** (P, A_L): 면적 동률 폭 = **격자 한 칸** ΔA_tie(p, q) = g·max(w_p, h_p, w_q, h_q) [**확정** D-4 -- 사용자 2026-10-07 Q10 (iii), 계획 DEC-79·DEC-95 (2)]. A_L에는 행 끝 dummy·tap·well 간격이 들어간다(계획 LY10). g = `core.pdk_decl` `MANUFACTURINGGRID`이고, 짧은 변이 한 격자 움직일 때 면적 변화가 g·긴 변이라는 근거다. DEC-80 (i)의 Σ W·L 축 한 칸(g × 최소 finger 폭)과는 다른 축이다. 전력 동률 폭은 b_P다. 제거 점은 `removed{reason: dominated_on_layout_axis, by}`로 남긴다.
3. **순위 뒤집힘**(두 축에서 지배 관계가 다른 쌍의 점 p): ε_A ← A_search(p) − (A_L(p) − A_search(p))로 보정해 `search.solve_eps`로 다시 풀고 1을 다시 돈다(MOD8 재실행).
4. **수렴·상한**: front 점 집합과 각 A_L이 직전 교대와 같은 지문이면 끝이다. 상한 K_front = ⌈log2((max A_L − min A_L)/min ΔA_tie)⌉(N3.6 K_max 규칙 그대로, q 조기 판정도 같음)이다. 닿으면 NONCONVERGENT 레코드를 남기고 마지막 front를 '판정 미수렴'으로 표기해 낸다.
5. front 표에는 탐색 축 값·판정 축 값·차·수동소자 포함 여부(MOD7이 수동소자를 배치하지 않는 동안 "트랜지스터만")를 병기한다(DEC-79). 실측 차가 면적 축 모델 오차 선언값을 넘으면 `review_needed`, 선언이 없으면 '판정 보류'다.

### 6.5 예산점

- 선언 `human.objective_budget{<목적 metric 정본 이름>: {value, source}}` [제안 이름, D-7]. 목적 metric은 `supply_current_dc_a` 또는 `area_layout_m2`다. 미선언이면 front를 내고 정지한다(DEC-77, PUD PA-1 기본 (a)).
- 탐색 축 풀이(MOD6 `solve_at_budget`): 전력 예산이면 ε_P = 예산으로 두고 면적을 최소화하고, 면적 예산이면 ε_A = 예산으로 두고 전력을 최소화한다. 시작점은 예산에 가장 가까운 front 점이다.
- 판정 축 확인(MOD8 `budget_point_on_layout`): 면적 예산의 정본 축은 판정 축이다(DEC-79). MOD8 수렴 뒤 A_L ≤ 예산이면 채택하고, 넘으면 ε_A ← ε_A − (A_L − 예산)으로 다시 푼다(교대 상한 K_front). 해가 없으면 그 예산을 INFEASIBLE로 보고하고 front는 그대로 낸다.

---

## 7. 실패 캐시와 중복 평가 0

- **7.1 평가 키** `EvalKey = (S0.fp, schema.fp, ℓ tuple, w_fixed.fp, tuple(float.hex(θ_c,i)))`. ε·시작점·호출 출처는 평가 결과와 무관하므로 넣지 않는다. 그래서 ε 점 사이 재방문, 양 끝점과 ε 경계의 같은 θ, L-b가 원래 ℓ로 돌아오는 경우가 모두 적중한다.
- **7.2 메모리 캐시** `EvalCache`: 값 = `EvalResult`(실패 포함)다. 스냅샷 객체는 front 점·채택 해·현재 parent 체인만 들고, 나머지는 요약만 둔다(N3.5 "버린 후보 스냅샷은 S3 요약만"). 적중 시 요약을 바로 돌려주고, 스냅샷이 필요하면 결정론적으로 재생성해 `snapshot_fp`로 대조한다(불일치 = NFR-4 위반 → `review_needed`). 상한은 평가 수 상한(DEC-34 식)이고 실행 수명이다. 요약 크기가 θ 길이에 비례하는 작은 값이라 퇴출 정책이 필요 없다.
- **7.3 디스크 실패 캐시**: 별도 파일을 두지 않고 **S3 evals의 실패 레코드에서 재구성**한다(같은 값을 두 곳에 두지 않는다). 재사용 조건은 S0 지문과 레코드의 `code_fp`(MOD4·MOD5·MOD6 패키지 소스 해시)가 현재와 같은 것이다(REQ E3 "코드가 바뀌면 자동 무효"). 성공 요약도 같은 방식으로 시작점과 중복 회피에 쓴다.
- **7.4 계측** 결과 JSON `perf.search`: `requests`(fun·jac·cons 호출 합), `kernel_calls`, `hits`, `fail_hits`, `disk_hits`, `recompute_same_key`, FD 열마다 재계산 필드 수 대 영향 표 크기, 평가 시간 중앙값, `KernelContext` 생성 수. 합격 기준(NFR-2)은 `kernel_calls == 고유 키 수`, `recompute_same_key == 0`, LUT memo 퇴출 0이다.

---

## 8. S3 기록 형식(`library/<name>.search_archive/<S0 지문>/`, append-only, 케이스마다 flush)

`evals.jsonl`(평가 1회 = 1줄. 캐시 적중은 줄을 쓰지 않고 perf에만 센다):
```jsonc
{"seq": 812, "code_fp": "…", "schema_fp": "…", "l_anchor": [3, 5, 2], "w_fixed_fp": "∅|…",
 "theta_hex": ["0x1.8p-3", "…"], "theta": [0.1875, …],            // hex = 키, 10진 = 읽기용
 "ok": false, "fail": {"class": "SEAL_VIOLATION", "devices": ["…"], "margin": 2.31, "detail": {"item": 7}},
 "objectives": {"supply_current_dc_a": 8.2e-5, "area_search_m2": null},   // 부분값 규칙 2.3절
 "metrics": {…}, "constraints": [{"name": "gain_ss_db>=", "c": 0.4, "active": true}, …],
 "branch": "b2", "origin": {"stage": "slsqp|fd|layer0|l_search|mod8|budget", "eps": {"area_search_m2": 1.0e-9}, "start": "s1"},
 "snapshot_fp": "…"}   // 성공 시, 재생성 대조용
```

`runs.jsonl`(실행 1회 = 1줄, 단계별 중간 기록 포함):
```jsonc
{"run_id": "…", "s0": "…", "code_fp": "…", "search": {…}, "budget": {"wall_clock_budget_s": 300, "N_eps": 6, "coarse_factor": 2},
 "resolution": {"b_A_m2": …, "b_P_a": …, "dA_tie_rule": "grid*max_side", "estimated": true},
 "starts": [{"id": "s1", "source": "layer0|s3|x0", "seal_ok": true}],
 "front": [{"point_id": "f3", "theta_hex": […], "l_anchor": […], "w_fixed": {"M5": "0x…"},
            "power": …, "area_search": …, "area_layout": …, "gap": …, "passives_in_layout": false,
            "gain_budget_db": {…}, "active": [{"name": …, "c": …}], "selected": false,
            "snapshot_ref": {"snapshot_fp": "…", "file": "snapshots/<fp>.json.gz"},
            "status": "kept|removed", "removed": {"reason": "dominated_on_layout_axis", "by": "f5"}}],
 "failed_eps": [{"eps": {…}, "last_fail": {…}}],
 "refilter": [{"iter": 1, "removed": ["f2"], "rank_flips": ["f4"], "mod8_reruns": ["f4"], "fp": "…"}],
 "budget_point": {"point_id": …, "verdict": "ok|infeasible|nonconvergent"}, "perf": {…}}
```

- **스냅샷 참조의 디스크 표현** [제안]: front 점과 채택 해만 S2 전체(`dc`·`ss`·`ls`·layout 필드 값과 version)를 `snapshots/<snapshot_fp>.json.gz`로 쓴다(개수는 front 크기 이하). 나머지는 θ로 재생성하고, 메모리에서는 구조 공유 객체를 그대로 든다.
- `node_across_front(front, node)`는 front 점마다 (point_id, 노드전압, writer 티어, 그 노드에 닿는 소자 op)를 낸다. 실행 안에서는 메모리 스냅샷, 다른 실행의 front는 `snapshots/`를 읽고 재계산은 0이다(test로 고정). 폴더는 `.gitignore`에 등록하고, 지문이 다른 디렉터리는 읽지 않는다.

---

## 9. test 계획(`tests/search/test_<파일>.py` 1:1 + `tests/integration`·`perf`)

기대값은 피검 함수를 부르지 않고 손계산으로 만든다(작성자 ≠ 검증자). 허용치는 SLSQP `ftol`(정규화 목적 1칸)과 부동소수 한계에서 유도한다. T1~T6·T10~T14의 toy는 커널 프로토콜을 만족하는 픽스처 커널이다.

| id | 대상 | toy | 손계산 기대 |
|---|---|---|---|
| T1 볼록 front | `eps_sweep`, `slsqp_outer`, `pareto` | θ = (x₁, x₂) ∈ [0.1, 10]², P = x₁ + x₂, A = 1/x₁ + 4/x₂ | 내부 해 x₂ = 2x₁, x₁ = 3/ε_A, **P·A = 9**(ε_A ∈ [0.6, 30]). E_P = (0.2, 50), E_A = (20, 0.5). 모든 점이 P·A = 9 또는 bound 활성, 서로 지배하는 점 0 |
| T2 비볼록 front | `eps_sweep` | t ∈ [0, 1], P = t, A = 1 − t² | ε_A = 0.75 → t = 0.5, P = 0.5(가중합으로는 끝점만 나오는 구간). 두 방향 스윕이 같은 집합 |
| T3 L 이산 | `l_anchor_search` | 앵커 {1, 2, 3}, 제약 L·x ≥ 3, P = x, A = L(1 + x) | 앵커별 (P, A) = (3, 4), (1.5, 5), (1, 6) 모두 비지배. ℓ = 1에서 시작한 L-b가 ε_A = 5.5에서 ℓ = 2로 이동, ε_A = 4.5에서는 이동 없음. L 연속값 요청 0(LR3) |
| T4 실패 캐시 | `eval_cache`, `slsqp_outer` | T1 + x₁ < 0.5에서 `SealViolationError(item=7, margin=(0.5 − x₁)/0.05)` | 실패 θ 재요청 시 커널 호출 증가 0, margin 손계산값. 봉인 6·7은 계속, 다른 클래스는 상자 절반 재시작(재시작 수 ≤ ⌈log2(반경/h)⌉) |
| T5 중복 평가 0 | `kernel`, `eval_cache` | T1 sweep 전체 | `kernel_calls == 고유 EvalKey 수`, `recompute_same_key == 0`, ε 경계의 같은 θ 적중. 옛 784/811과 대조 기록 |
| T6 넓은 except 금지 | `slsqp_outer` | toy 커널이 `ValueError`·`InfeasibleSizingError`를 직접 raise | 전파(삼키지 않음, N3.14) |
| T7 FD 영향 집합 | `fd_jacobian` + 실제 커널 | G7 F9 축소 two_stage(이름 없는 toy) | 열마다 재계산 필드 = 손도식 영향 표. 전류 성분 열에서 ④ 재계산 0 |
| T8 FD 스텝 | `theta_schema` | toy LUT(LC 7절) | hᵢ = 격자 간격 × gm/ID 손계산값, 상수 리터럴 0(`test_numeric_literals_derived`) |
| T9 반전 좌표 | `theta_schema` + MOD1 | LC 7절 toy의 ln IDu ↔ VGS | 정점 인근 목표의 VGS 오차 ≤ id_equivalent 셀 값, gm_id 좌표 대비 감소 기록. 정점 아래 r은 제약 margin < 0 |
| T10 비지배·동률 | `pareto` | 손으로 고른 점 5개(한 쌍은 면적 차 < b_A) | 남는 집합, 접힘, 타이 브레이크 순서 |
| T11 판정 축 재필터 | `front_refilter` + MOD8 스텁 | 탐색 축 front 3점, 스텁이 A_L을 돌려줌(한 점 순위 뒤집힘), g = 0.005 µm | 제거 점·사유, ΔA_tie = g·max 변 손계산, 재실행 1회 뒤 지문 수렴. 2-주기 스텁은 K_front에서 NONCONVERGENT |
| T12 예산점 | `budget_point`, `budget_on_layout` | T1, 면적 예산 2.0, 스텁 gap +0.1 | ε = 2.0 → A_L 2.1 > 2.0 → ε = 1.9 재풀이 → 채택. 미선언이면 front 정지 |
| T13 S3 | `archive`, `front_query` | T1 실행 | evals 줄 수 = kernel_calls, 강제 종료 뒤에도 마지막 줄까지 남음. 같은 code_fp면 디스크 실패 재사용, 다르면 무효. `node_across_front` 재계산 0 |
| T14 결정론 | `find_front` | T1 + 입력 순서 섞기 × `PYTHONHASHSEED` 1~5 | front JSON 정규화 해시 동일(IC2) |
| T15 파일럿 E2E(slow) | 전체 | 파일럿 | 서로 지배하는 점 0, 시작점 봉인 통과, `perf.search` 합격 기준, cProfile 기록(U-49) |

---

## 10. 결정 항목

| # | 항목 | 기본안 [제안] | 사용자 몫인가 |
|---|---|---|---|
| D-1 | 쓰기 소자 독립 좌표: (가) gm_id 유지 (나) 혼합 (다) VGS (라) ln(ID/W) | (라). DEC-04·DEC-70 "셀별 gm_id" → "셀별 반전 좌표(ln ID/W, gm_id는 파생 보고)", N3.6 봉인 2 지표 → id_equivalent로 개정. MOD1 `vgs_for_current_density` 추가 | **결정됨 (2026-10-07)** (라) -- 계획 DEC-88 |
| D-2 | 외층 L 이산 처리 | L-a(시작점 고정) + L-c(ℓ 분지 multi-start) + front 점에만 L-b 1회 | **결정됨 (2026-10-07)** 기본안, bin 벡터로 읽음 -- 계획 LR10·DEC-95 (1) |
| D-3 | 시간 예산(PUD PA-2): 300 s를 front 전체에 쓸지 | ε 점 수는 그 예산에서 식으로 유도. 옛 파일럿 실측(1회 ≈146 s)으로는 끝점 2개뿐이라 새 커널 cProfile(U-49) 뒤 재질의 | **보류 확정 (2026-10-07)** -- cProfile 뒤 재질의, 계획 U-47·DEC-95 (4) |
| D-4 | '격자 한 칸' 동률 식 | ΔA_tie = MANUFACTURINGGRID × max(두 점 bbox 변) | **결정됨 (2026-10-07)** -- 계획 DEC-79·DEC-95 (2) |
| D-8 | **[개정 Q10 (v)]** 종속 gm_id 소자 선택(G7 U1·U4) | ratified → diode → GB5가 gm을 요구하는 소자·뒤 stage 소자 독립 유지 → 대칭 궤도 대표 → 이름. '이름 전단사 후 front 정규화 해시(이름 사상 적용) 동일' metamorphic test(T14 확장) | **결정됨 (2026-10-07)** -- 계획 DEC-64·DEC-95 (3) |
| D-9 | **[개정 Q7]** 보상 수동소자 θ 성분(4.1 C_k·R_k)과 층 0 시작점(근사식, `comp_approx_gap` 기록) | 채택 | **결정됨 (2026-10-07)** -- 계획 DEC-92 |
| D-5 | MOD4 커널 연속성(SCC 마지막 할선 스텝, 풀이 tol = id_equivalent 셀) | 채택하고 G7 3.4 개정 | 아니오(엔진 내부). MOD4 design 수정 필요 |
| D-6 | 계획 문언 충돌: NFR-5 "1차 합격 범위에서는 판정 축 재필터를 보류"와 N3.8 면적 항목 "판정 축 재필터는 보류, DEC-79"가 DEC-79·LR9의 12번 (나) "범위 안"과 어긋남 | NFR-5·N3.8을 DEC-79에 맞춰 정정 | 계획 정정(E1 방식) |
| D-7 | 예산 필드 이름 `human.objective_budget{metric: {value, source}}`, 면적 예산은 판정 축 기준 | 채택 | 아니오(N3.15가 MOD6 design에 위임) |
| 대기 | PUD PA-1(예산 선언 여부), AC-3(SPICE를 돌릴 front 점) | 각각 (a) | 예(이미 PUD에 있음) |

범위 밖(DEC-76): 정밀 경로(내층 DP·중층 좌표강하), 층 0 gain bin front 전체판(U-49 뒤), 전역 샘플 예산 채우기, 임계값 bisection. 선언으로 켜는 것은 DEC-75 화이트리스트로만 하고, 입력이 미구현 분기를 요구하면 `unsupported_rule_branch`로 정지한다.
