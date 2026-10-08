# gmid_engine.metrics 동작 계약 (test 작성용) -- 1단계: 엔진 상태와 독립인 수치 핵심 + 2단계: ss_linearize 배선(7절)

- 대상: `gmid_engine.metrics.__all__`(이 단계 파일 27개 + 접합 용량 `junction_cap.py`(8절) + 분해능 `lut_parameters.py`·`sensitivity.py`·
  `resolution.py`·`_helpers_dc.py`(9절, 2026-10-08), 아래 0절). test 는 `from gmid_engine.metrics import ...` 와
  `from gmid_engine.core import ...` 만 쓴다(`_` 이름 금지). test 배치(규칙 H): `gmid_engine/tests/metrics/test_<파일>.py`.
- 근거: `wt/_drafts/engine/design_mod1_lut_mod5_mna.md`(이하 DM) 3.1~3.4, 계획 N3.8(gain·PM U-48), DEC-25·53·66·67·68·
  78·79, DF-06·16·19·26·28·29·30·37, WP-03, 설계 `design_spec_format.md` 3.2(`metric_catalog`), coordinator 결정
  2026-10-07(용량 전용 노드 = 전하 보존 극한, 정의 불가 = 값으로 담기), `wt/_drafts/engine/design_7a_loop_output_views.md`
  (이하 7a, 루프 뷰·출력 포트 뷰 -- 4.1 변경 목록), 오케스트레이터 결정 2026-10-07(7a Q3: 음의 rout = 정의 불가).
- 1단계(0~6절) 함수는 **입력 레코드만 보는 순수 함수**이고 graph·S2·LUT 를 import 하지 않는다. **2단계(7절, 2026-10-08)** =
  `ss_linearize` 배선: 봉인 스냅샷 → `ss_dev`·`metrics_ss`·`metrics_dc` 계산 블록 → S2 필드, 진입점 `ss_evaluate` (7a 4.5 단계 5
  배선 지점 -- spec `ViewDecl` → 계 레코드). 그 파일들만 graph·sizing·lut·authoring 을 import 한다(PACKAGE_ORDER 앞쪽).
- 아직 범위 밖: GB4 `achievability`, GB5 `compensation` 근사식(보상 수동소자 값 자체는 r5 부터 sizing θ 성분 -- 7.6),
  `ls_fields`, `columns_current_check`, `area_layout_m2`, `nqs_ratio`·`mismatch_sigma_v`, 레이아웃 기하(MOD7 `ly.diffusion`)로 하는
  접합 용량(지금은 LUT 생성 규칙 기하, 7.2·8절).

---

## 0. 파일·층·진입점

| 층 | 파일 | 진입점 | 내용 |
|---|---|---|---|
| 0 | `records.py` | (데이터) | 입력 레코드: `MosSmallSignal`, `Resistor`, `Capacitor`, `Excitation`, `Sense`, `SmallSignalCircuit`, `StampSet`, `LoopCut`, `RailBias`, `ChannelCurrent`, `CurrentSource`, `DcOperatingPoint`, `GateArea`, `PassiveArea` |
| 0 | `mna_types.py` | (데이터) | 결과 레코드: `Undefined`, `MnaSystem`, `Roots`, `DcLimit`, `SystemResponse`, `PointSolution`, `Factor`, `ProbeFactor`, `CutCircuit`, `Crossing`, `LoopAnalysis`, `OutputResistance`, `ResponseRatio`(+ `row`, 9절), `SupplyCurrents`, `AreaSearch`, [9절] `ParameterSet`·`ResponseSensitivity`·`Resolution`, `MetricResult`(+ `resolution`, 9절). **인수 공통 규약**(`Factor`·`ProbeFactor`): 속성 `response`(공유 격자), `samples`(격자 위 값), `poles`·`zeros`(상단 괄호용 근), `undefined`(격자 표본 사유); 격자 밖 한 점은 `PointSolution` → (복소값, 사후 오차, 사유)(`_helpers_product.product_at`) |
| 0 | `_helpers_stamp.py` | (helper) | `admittance_pair` |
| 0 | `_helpers_dc.py` | (helper) | `dc_limit_parts`(ω → 0 극한 식 행렬·우변·전하 주입 열 -- `dc_limit`·`sensitivity` 공용, 9.2) |
| 0 | `_helpers_pencil.py` | (helper) | `finite_eigs`(pencil 유한 고유값, `pencil_roots`·`probe_loop` 공용) |
| 0 | `junction_cap.py` | `junction_caps` | 접합 용량 cdb·csb(BSIM4, DEC-91) + 입력 레코드 `JunctionParams`·`DiffusionGeometry`, 결과 `JunctionCaps` (8절) |
| 1 | `_helpers_probe.py` | (helper) | `probe_value`(Middlebrook T 한 점 평가·사후 오차·[9절] ∂T/∂V -- 4-tuple, `probe_loop`·`_helpers_product`·`resolution` 공용) |
| 1 | `sensitivity.py` | `response_sensitivity` | 한 계·한 ω 의 관측값·사후 오차·∂V/∂p·∂V/∂ω(LU 1회 + 수반, 9.2) |
| 1 | `loop_cut.py` | `cut_circuit` | 루프 절단 회로(3.16) |
| 1 | `stamp_mos.py` | `mos_stamps` | MOS 소신호 스탬프 |
| 1 | `stamp_two_terminal.py` | `two_terminal_stamps` | R·C 스탬프 |
| 1 | `pencil_roots.py` | `pencil_roots` | 극점·영점 |
| 1 | `dc_limit.py` | `solve_dc_limit` | ω → 0 극한(전하 보존) |
| 1 | `omega_grid.py` | `omega_grid` | ω 격자 |
| 1 | `supply.py` | `supply_currents` | 레일 전류·전력 |
| 1 | `area.py` | `area_search` | 탐색 축 면적 |
| 1 | `rout.py` | `output_resistance` | 출력 저항 |
| 1 | `ratio.py` | `response_ratio` | 두 열 응답비 |
| 1 | `registry.py` | `metric_registry` | 이름 → `RegisteredMetric` |
| 2 | `mna_build.py` | `build_mna` | 조립 1회 |
| 2 | `point_solve.py` | `solve_point` | ω 한 점 풀이 + 사후 오차 |
| 2 | `catalog.py` | `metric_catalog` | {이름: MetricSignature} |
| 2 | `evaluate.py` | `metric_value` | 이름으로 값 읽기 → `MetricResult` |
| 2 | `lut_parameters.py` | `lut_parameters` | LUT 파라미터 Δp = ε·|p|·단위 스탬프(9.1) |
| 2 | `resolution.py` | `metric_resolutions` | metric 분해능 = max(LUT 1차 최악 전파, MNA 사후 오차 전파)(9.3) |
| 3 | `mna_solve.py` | `solve_responses` | 공유 격자 응답 |
| 3 | `_helpers_product.py` | (helper) | `check_factors`, `product_at` |
| 4 | `crossing.py` | `find_crossing` | |T| = level 교차 |
| 4 | `phase_lag.py` | `phase_lag` | 누적 위상 지연 |
| 4 | `probe_loop.py` | `probe_factor` | 절단 회로 계 → Middlebrook 루프 이득 인수(3.17) |
| 5 | `loop_analysis.py` | `analyze_loop` | gain·UGF·GBW·위상 여유 한 번 계산 |

core 추가: `core/units.py`(공개 정의 0, `METRIC_UNITS`(db, hz, deg, ohm, mv, amp, w, m2)·`DOMAINS`(dc, ss, ls, geom)·
`AMPLITUDE_DB_PER_DECADE`), `core/metric_signature.py`(데이터, `MetricSignature(unit, domain, view_kind=None, objective_axis=None)`
+ 어휘 `VIEW_KINDS`·`OBJECTIVE_AXES` -- `unit ∈ METRIC_UNITS`, `domain ∈ DOMAINS`, `view_kind` ∈ {None} ∪ `VIEW_KINDS`
(transfer, loop, output_port, ratio; None = 뷰 없음), `objective_axis` ∈ {None} ∪ `OBJECTIVE_AXES`(power, area) 아니면 ValueError).
뷰 종류 어휘의 정본은 `VIEW_KINDS` 한 곳이고 spec 로더(authoring SPEC_CONTRACT 4절)도 같은 어휘를 쓴다.

---

## 1. 입력 관례

- **노드 = 정수 인덱스**. 넷 이름 문자열을 노드로 주면 `TypeError`. 교류접지·레일은 이름이 아니라 선언된 인덱스 집합
  (`SmallSignalCircuit.ac_ground`, `DcOperatingPoint.rails`)으로 받는다. 인덱스만 바꿔 번호 매긴 같은 회로는 metric 이 같다(I-7).
- 모든 값 필드는 생성 때 검사: 유한 실수, `MosSmallSignal` 의 gm·gmb·gds ≥ 0, **`MosSmallSignal` 용량 5개(cgs·cgd·cgb·cdb·csb)는
  부호 있는 유한 실수**(NaN·inf 만 ValueError -- 오케스트레이터 결정 2026-10-08 Q7: BSIM4 단자 용량(예 cgb = −∂Qg/∂Vb)은 부호가
  있고 SPICE 오라클이 부호 그대로 스탬프하므로 같은 정의로 비교하려면 엔진도 부호 그대로 스탬프한다. 부호 규약의 원천 = LUT v2
  생성기 meta `sign_convention`(lut CONTRACT r6 1.2 -- 용량은 부호 보존, CGB·CGS·CSS·CGD(pfet) 에 음수 점), 엔진은 절댓값·클램프를
  쓰지 않는다), `Resistor.ohm`·`Capacitor.farad` > 0
  (기본값 없음 -- `Resistor(a, b, None)` 은 `TypeError`, 0 은 `ValueError`).
- **MOS 소신호**: I(d→s) = gm(vg − vs) + gmb(vb − vs) + gds(vd − vs). NMOS·PMOS 같은 식(소신호 크기는 양수).
  용량 cgs(g–s), cgd(g–d), cgb(g–b), cdb(d–b), csb(s–b). bulk 는 `b` 인덱스(레일이면 교류접지 노드).
- **여기 열** `Excitation(name, voltages=((노드, V),…), currents=((노드, A),…), charges=((노드, C),…))`: 전류·전하는 노드로
  들어가는 방향. 전하 주입 q 는 전류 s·q 라 열의 `BC` 에만 들어간다(`BG` 0 -- 용량 전용 노드의 ω → 0 극한이 전하 보존 식으로
  정의된다, 7a 2.4). 한 계의 모든 열에서 전압 구동 노드는 고정 노드이고, 그 열에 없는 구동 노드는 0 V. 이름은 계 안에서 유일.
  고정 노드에 전류·전하 주입은 ValueError.
- **관측** `Sense(pos, neg=None)`: v(pos) − v(neg). `build_mna(circuit, excitations, senses)` 의 `senses` 는 `Sense` tuple
  (1개 이상, 관측 하나면 1-tuple) -- 같은 계를 여러 노드에서 본다(루프 절단 계 2k 관측).
- **루프 절단** `LoopCut(kind ∈ {resistor, capacitor}, index, terminal ∈ {a, b})`: `SmallSignalCircuit` 의 그 원소 단자 하나를
  새 노드로 옮긴다(3.16).
- **DC**: `ChannelCurrent(drain, source, amp)` = 소자 안 drain→source 전류(부호 있음). `CurrentSource(from_node, to_node, amp)` =
  from 에서 나와 to 로 들어가는 전류.

## 2. 예외 규약과 정의 불가 값

- **예외는 입력 계약 위반에만**: 형식 오류(`TypeError`), 값·뷰 정의 오류(`ValueError` -- 레코드 값, 여기 열 이름 중복,
  구동 노드가 교류접지와 겹침, 고정 노드에 전류·전하 주입, 관측이 구동 안 된 고정 노드뿐, 격자 다른 인수 묶기, 인수 행·열 범위
  밖·순수 전하 열 인수, rout·ratio 열 조건, 합산 레일 선언, 절단 정의(원소 범위 밖·같은 원소 두 번·교류접지 절단),
  프로브 열·관측 없음·중복, 0·비유한 가중(`probe_factor`)), 미등록 metric 이름(`KeyError`). 이것들은 값(사이징 점)과 무관한
  배선·뷰 결함이다. **모양 위반은 TypeError 로 통일**: 비어 있으면 안 되는 tuple 이 비었음(excitations·senses·인수·
  `cut_circuit` 의 cuts·`probe_factor` 의 pairs), tuple·쌍 형식이 아님, `probe_factor` 의 weights 길이 ≠ pairs 길이.
- **값에 따라 생기는 정의 불가는 예외가 아니라 값**: 결과 묶음의 해당 필드가 None 이고 `undefined` 에
  `Undefined(quantity, code, category, detail)` 가 있다. `metric_value(name, source)` 는 항상 `MetricResult(name, value, undefined)`
  를 돌려준다. MOD5 는 N3.14 분류를 하지 않는다 -- 판정 계층이 문맥으로 분류한다(아래 표는 권고 대응).

| code | category | 생기는 곳 | 판정 계층 권고 대응(탐색 전 구조 판정 / 탐색 중 평가) |
|---|---|---|---|
| `isolated_node` | structural | `build_mna`(`defects`) | STRUCTURE_UNRESOLVED / 후보 실패 `structure_inconsistent` |
| `singular_dc_limit` | structural | `solve_dc_limit` | 같음 |
| `dc_charge_injection` | definitional | `solve_dc_limit`(그 열만) | STRUCTURE_UNRESOLVED / 후보 실패 `structure_inconsistent` |
| `dc_not_above_level`, `no_crossing_above`, `dc_zero`, `den_zero`, `num_zero`, `operand_undefined` | definitional | 교차·비·이득·Middlebrook 분모(`probe_factor`) | STRUCTURE_UNRESOLVED / 제약 위반 후보 실패(margin null, N3.14 표의 해당 하위 클래스는 판정 계층이 확정) |
| `loop_cut_mixed_charge` | definitional | `probe_factor` ω = 0(절단 노드 중 용량 전용과 전도 노드가 섞임 -- 열마다 1/s 차수가 달라 0차 동차성으로 극한을 못 낸다, 6절 M7) | STRUCTURE_UNRESOLVED / 후보 실패 `structure_inconsistent` |
| `negative_output_resistance` | definitional | `output_resistance`(DC 극한 관측 / I < 0 -- 양되먹임. 값을 내면 `<=` 제약이 통과하므로 정의 불가로 둔다, 7a Q3 오케스트레이터 결정 2026-10-07) | STRUCTURE_UNRESOLVED / 후보 실패(margin null) |
| `loop_open_rhp_poles` | definitional | `analyze_loop` 의 `phase_margin_deg` 만(→ `pm_ss_deg`·`parasitic_pm_ss_deg`). 루프 인수 `poles` 에 실부 > 0 인 근이 있음 -- Nyquist P > 0 이라 180° − 지연은 안정 여유가 아니다(3.10 전제). detail `rhp_poles`(근마다 `(실부, 허부)` float 쌍의 tuple -- complex 아님(블록 write 의 core `require_immutable`), 중복 없이 (|s|, 실부, 허부) 오름차순)·`rhp_pole_count`(int), 키 이름순 저장(3.10). 값을 내면 위상 앞섬으로 PM > 180° 가 `>=` 제약을 통과한다(ngcc 2026-10-08: PM 218°, SPICE 과도 0.73 Vpp 발진) | STRUCTURE_UNRESOLVED / 후보 실패(margin null) |
| `singular_mna`, `crossing_bracket_overflow`, `crossing_bound_violated`, `phase_jump_unresolved`, `zero_response_on_axis`, `response_not_finite`, `unrecorded_cause` | numeric | 풀이·이분·위상 | STRUCTURE_UNRESOLVED / NONCONVERGENT(후보 실패 클래스) |
| `loop_probe_singular` | numeric | `probe_factor`(그 ω 에서 프로브 직렬 임피던스 행렬 M = Pᵀ·Z·P 가 특이 -- 영 피벗) | STRUCTURE_UNRESOLVED / NONCONVERGENT |

## 3. 함수 계약

### 3.1 `mos_stamps(dev) -> StampSet`, `two_terminal_stamps(elem) -> StampSet`
- (행 노드, 열 노드, 값) tuple. KCL 행 = 노드에서 나가는 전류. MOS G 행: drain (d,d,gds)(d,g,gm)(d,b,gmb)(d,s,−(gm+gmb+gds)),
  source 는 부호 반대. 값 0 항목은 내지 않는다. 저항 = 1/R 의 2단자 4항목, 커패시터 = C 의 4항목. 다른 형식은 `TypeError`.

### 3.2 `build_mna(circuit, excitations, senses) -> MnaSystem`
- 소자마다 스탬프 함수를 **정확히 한 번** 부른다. 결과는 ω 와 무관한 실수 `G`·`C`(n×n), `BG`·`BC`(n×m, 전하 열 항은 `BC` 에),
  `sense_rows`(r×n), `sense_direct`(r×m), `senses`(행 순서 `Sense` tuple). 배열은 쓰기 금지. 미지수 = 소자·여기·관측에 나오는
  노드 − 고정 노드(교류접지 ∪ 전압 구동), 오름차순. 관측 하나라도 구동 안 된 고정 노드뿐이면 ValueError.
- `defects`: 미지수 블록에서 G·C 의 그 행이 모두 0(KCL 식 없음) 또는 그 열이 모두 0 인 노드 → `isolated_node`(모든 ω 특이).
- `charge_nodes`: 전체 G 행(고정 노드 열 포함)이 0 인 미지수 노드의 미지수 번호 = 용량으로만 이어진 노드.

### 3.3 `solve_dc_limit(system) -> DcLimit` (ω → 0 극한, 전하 보존)
- (G + sC)x = BG + s·BC 에서 F = `charge_nodes` 행은 G_F = 0 이라 s(C_F x − BC_F) = BG_F. BG_F 는 그 노드 주입 전류뿐이다.
- BG_F = 0 인 열: F 행을 **C_F·x = BC_F**(전하 보존 -- 블록 C_cc x_c = −C_cr x_r 의 일반형, 구동 노드 결합은 BC_F 에 있다)로,
  나머지 행은 G_R·x = BG_R 로 쌓은 실수 행렬을 LU 1회로 모든 열에 대해 푼다. 이것은 극한 식 자체의 해다(상수·작은 ω 근사 없음).
- BG_F ≠ 0 인 열: 직류 전하 누적으로 극한 발산 → 그 열 NaN + `dc_charge_injection`. 쌓은 행렬이 특이면 모든 열 NaN +
  `singular_dc_limit`. `defects` 가 있으면 모든 열 NaN + 그 사유. 결과 `values` 모양 (r, m).
- 전하 주입 열은 변경 없이 들어간다: BG_F = 0 이라 F 행이 C_F·x = BC_F(전하 보존)로 풀린다 -- 새 풀이 규칙이 없고
  `dc_charge_injection` 도 아니다(7a 2.4 'ω = 0').
- **범위 한정**: 이 값은 소신호 전달의 ω → 0 극한이다. 용량 전용 노드의 **DC 동작점 전압**(바이어스)은 MOD5 몫이 아니다
  -- GB7 / spec 선언이 정한다. 여기서는 그 노드의 소신호 전하 보존만 쓴다.

### 3.4 `pencil_roots(system) -> Roots`
- `poles` = (G, −C) 유한 일반화 고유값, `zeros[r][j]` = 관측 행 r · 열 j 전달함수의 유한 영점(증강 pencil). 순수 전하 열
  (전압·전류 없이 전하만)은 빈 tuple -- 영점 = 같은 노드 전류 열 영점 ∪ {0} 이고 원점은 격자에서 빠져 더할 꺾임점이 없다
  (그런 열은 `Factor` 로 쓰지 않는다, ValueError). QZ 전에 Ward 균형(행·열 2 의 거듭제곱 배율, log2 크기 최소제곱 한 번 --
  고유값 불변, 상수 없음)을 하고 아래 판정은 균형 뒤 행렬로 한다. |s| = |α/β| 가 분해능 한계 ‖A‖_F/(차원·eps·‖E‖_F) 를 넘는
  근도 무한대로 본다(β 의 상대 오차 1 초과 -- 예: 옛 구현의 −7e24 영점). 무한 판정은 QZ 동차 좌표
  |β| ≤ 차원·eps·‖E‖_F(상수 없음). 정렬 (|s|, 실부, 허부). `defects` 가 있으면 빈 근. **격자 배치·상단 괄호 전용**.
- **원점 판정**(무한 판정과 같은 방식, 상수 없음): QZ 동차 좌표 (α, β) 에서 |α| ≤ 차원·eps·‖A‖_F 이면 그 고유값은 정확히
  0j 로 낸다(극점 pencil: A = G, 차원 n / 영점 pencil: 증강 A, 차원 n+1; eps = 배정밀도 기계 엡실론). 용량 전용 노드의 전하
  모드(원점 극점)가 반올림 잡음으로 작은 |s| 가 되어도 0 으로 판정된다. |s| = 0 은 격자 꺾임점·상단 괄호 상계에서 빠진다.

### 3.5 `omega_grid(roots_tuple) -> tuple`
- 0.0 + 양의 유한 |극점|·|영점| 꺾임점 + 인접 꺾임점 기하 중점, 오름차순·중복 없음. 꺾임점 없으면 `(0.0,)`. 서로 1 ulp 안
  (다음 부동소수 이하)인 꺾임점은 하나(작은 쪽)로 친다. 격자 점 수 자체는 불변식 대상이 아니다(I-7 은 metric 불변).

### 3.6 `solve_responses(systems) -> tuple[SystemResponse]`
- 계마다 `pencil_roots` 1회, 모든 계 근의 합집합으로 **공유 격자** 1개. ω = 0 은 `solve_dc_limit`(LU 1회, 모든 열),
  ω > 0 은 (k,n,n) 묶음 풀이 1회(특이면 점마다 다시 풀어 특이 ω 만 NaN + `singular_mna`). 재스탬프 없음.
  `values` 모양 (k, r, m) = (ω, 관측 행, 열), `values[0]` = DC 극한, `dc` 속성 = `values[0].real`(r, m), `undefined` = 사유 모음.

### 3.7 `solve_point(system, omega) -> PointSolution`
- ω > 0: A = G + jωC 의 LU 1회로 모든 열 풀이 + 같은 분해로 반복 개선 1회, `errors[r, j]` = |sense_rows[r]·dx_j|. ω = 0:
  `solve_dc_limit`(오차 0). `values`·`errors` 모양 (r, m). 영 피벗이면 NaN + `singular_mna`.

### 3.8 `find_crossing(factors, omegas, values, level, quantity) -> Crossing`
- 인수 = `Factor`·`ProbeFactor`(0절 공통 규약, 섞어 묶을 수 있다). 근은 인수 속성 `poles`·`zeros`(`Factor`: 계 극점·그 행·열
  영점, `ProbeFactor`: T 자신의 극점·영점). `product_at` 은 같은 계를 한 번만 푼다.
- 격자 위 T(`values`)에 비유한 값이 있으면 교차를 찾지 않고 인수 `undefined` 의 첫 사유(없으면 `response_not_finite`)를
  quantity 로 바꿔 `Crossing.undefined` 로 낸다(단독 호출도 `analyze_loop` 와 같은 사유).
- T = Π 인수. |T(0)| ≤ level → `dc_not_above_level`. 격자에서 처음 |T| ≤ level 이 되는 칸을 괄호로. 격자 끝까지 > level 이면
  상계 |K|·Π(ω+|z|)/Π(ω−|p|)(ω > max|p|, 원점 근 제외)로 두 배씩 올려 상단 괄호를 유도하고 실제 풀이로 확인.
  극점 수 < 영점 수 또는 같고 |K| ≥ level → `no_crossing_above`. 이분: lo > 0 기하 중점, lo = 0 산술 중점. 정지 = 중점이 끝점과
  같은 부동소수 또는 | |T| − level | ≤ 사후 오차. 정의 불가는 `Crossing.undefined`(quantity = 인자).

### 3.9 `phase_lag(factors, omegas, values, omega_end, value_end, quantity) -> (lag | None, Undefined | None)`
- T(0) 대비 누적 지연(rad, 지연 양수). 칸마다 arg(T_k/T_{k−1}), |Δφ| ≥ π/2 면 중점을 실제로 풀어 세분.

### 3.10 `analyze_loop(factors) -> LoopAnalysis`
- 인수는 같은 `solve_responses` 결과여야 한다(격자 다르면 ValueError). 표본에 NaN 이 있으면 모든 양이 그 사유로 정의 불가.
- `gain_db` = 20·log10|T(0)|, `ugf_hz` = |T| = 1 교차 ω/2π, `gbw_hz` = |T(0)|·(|T| = |T(0)|/√2 교차)/2π,
  `gbw_ugf_gap_hz` = gbw − ugf, `phase_margin_deg` = 180° − `phase_lag`(UGF 까지).
- **PM 정의(계획 N3.8, U-48, 7a 2.1~2.7)**: `pm_ss_deg` 의 인수는 하나다. spec `feedback` 이 비어 있지 않으면 절단 회로
  (`cut_circuit`) 계의 `ProbeFactor` 1개(오라클 Middlebrook 이중 주입과 같은 식 T = (Tv·Ti − 1)/(Tv + Ti + 2), 3.17), 빈 list 면
  β = 1 -- 포트 전달 뷰 `Factor` 1개(T = A, `parasitic_pm_ss_deg` 의 기본 포트 뷰와 같은 MnaSystem, I-15). A·β 를 따로 푼 인수
  2개의 곱은 β 망이 증폭기 출력을 싣는 부하와 증폭기 입력이 β 망을 싣는 부하를 빼므로 `pm_ss_deg` 의 정의가 **아니다**(예 7
  대조: 무부하 곱 UGF 39756892.0418 Hz vs Middlebrook 22718224.0239 Hz, I-16). 인수 곱 기계 자체(예 2·2c)는 그대로 지원하고 test
  대상으로 남는다. 절단 위치·가중 = 7a 2.2·2.3(spec 쪽 유도는 authoring SPEC_CONTRACT 2절·3절). 기준이 T(0) 위상이라 관측 부호와 무관.
- **PM 전제 -- 개루프 T 에 우반면 극점 없음(Nyquist P = 0, 2026-10-08)**: `phase_margin_deg` = 180° − 지연이 안정 여유인 것은
  P = 0 일 때뿐이다(그때 Z = N 이고, −1 을 감지 않는 조건이 UGF 위상으로 읽힌다). 그래서 정의를
  **`phase_margin_deg` = 180° − `phase_lag`(UGF 까지), 단 인수 `poles` 의 모든 근이 Re ≤ 0 일 때**로 한다. 인수 `poles` 의
  합집합(`Factor`: 계 극점, `ProbeFactor`: T 의 극점 -- 둘 다 `finite_eigs` 근, 3.4·3.17)에 Re > 0 인 근이 하나라도 있으면
  `phase_margin_deg` = None + `Undefined("phase_margin_deg", "loop_open_rhp_poles", "definitional", (("rhp_poles", 근 쌍 tuple),
  ("rhp_pole_count", 개수)))` 이다. **detail 형식(정확히)**: `rhp_poles` = 근마다 `(실부, 허부)` Python float 쌍의 tuple
  (complex 객체가 아니다 -- `Undefined` 는 블록 `graph.metrics_ss` 에 그대로 쓰이고 core `require_immutable` 이 complex 를 받지
  않는다, 2절·7.4 '값 의존 정의 불가는 예외가 아님'), 중복 없이 (|s|, 실부, 허부) 오름차순(= `finite_eigs` 정렬). 켤레 복소쌍은
  두 원소(허부 + 와 −)로 들어간다. `rhp_pole_count` = int = `len(rhp_poles)`. `Undefined` 가 detail 을 키 이름순으로 정렬하므로
  저장 순서는 `(("rhp_pole_count", n), ("rhp_poles", ((re, im), …)))` 이다. 이 사유가 교차·위상 사유(`dc_not_above_level` 등)보다 먼저다(전제 위반). `phase_lag_rad`·
  `ugf_hz`·`gain_db`·`gbw_hz` 는 측정량이라 그대로 낸다. 우반면 근이 없으면 결과는 이 전제를 넣기 전과 비트 동일(I-17).
  - **문턱**: 새 상수 없이 근의 분해능 규약(3.4)을 그대로 쓴다 -- `finite_eigs` 가 원점으로 판정한 근은 정확히 0j 라 Re > 0 에
    들지 않고, 나머지 근의 실부 부호를 그대로 읽는다(Re > 0 엄격 비교).
  - **Nyquist 감김 수 대안을 쓰지 않는 이유**: (1) P 를 근 목록에서 세야 하는데 목록에는 상쇄 안 된 공통 근(분리 모드, 3.17 --
    지우려면 근 일치 문턱 상수가 필요해 지우지 않는다)이 남아 P 를 과대 계상한다(예 8b: 목록 P = 2, 실제 T 의 P = 1, 폐루프 우반면
    1 개 -- Z = N + P 가 2 로 틀린다). 근이 있는지 여부만 보는 판정은 그 근이 T 의 실제 극점이든 숨은 우반면 모드든 결론이 같다
    (둘 다 PM 이 안정 여유가 아님 -- 숨은 우반면 모드는 그 자체로 폐회로 불안정). (2) N 은 1 + T 의 위상을 jω 축 전체(ω → ∞
    포함)에서 언랩해야 해 격자 끝·−1 근처 세분 규칙이 새로 필요하다. (3) N 을 정확히 알아도 P > 0 이면 180° − 지연은 여유가
    아니다 -- 일반화 여유는 spec 에 정의가 없다. 그래서 근 존재 판정이 근 분해능 규약 아래에서 정확하고, 감김 수는 검증용으로만
    쓴다(예 8·8a·8b 에서 Z = N + P 가 폐회로 근 수와 맞음을 실측).
  - **폐루프 일관성(기록)**: `ProbeFactor` 의 폐루프 극점 = 1/(1 + T) = Q 의 극점 = 절단 전 회로(프로브 전압원 0 V 로 닫은
    회로)의 계 극점(`pencil_roots(build_mna(원래 회로, …)).poles`). MOD5 는 이 값을 metric 으로 내지 않는다(이 전제는 PM 의 정의
    조건이지 안정 판정이 아니다) -- 예 8a 처럼 개루프 우반면 극점이 있어도 폐루프가 안정일 수 있고, 그때도 PM 은 정의되지 않는다.

### 3.11 `output_resistance(response, column, row=0) -> OutputResistance`
- 계 = 포트 전달 뷰 계(입력 포트 고정 0 V, 레일·gate 전용 넷 교류접지 -- DEC-66 '모든 여기원 교류접지', 되먹임 소자가 있어도
  개루프). output_port 뷰는 감지 전용(sense_p, sense_n, sense_mode -- 여기 없음, authoring SPEC_CONTRACT 3절 mode `sense`):
  ss_linearize 가 이 계에 감지 노드 단위 전류 열 하나를 더하고 관측 행 `row` 를 감지로 둔다(감지 넷이 출력 포트와 다르면 관측
  행을 하나 더 -- 같은 계, 조립 1회).
- 열 조건(ValueError): 구동 진폭 전부 0, 전하 주입 없음, 전류는 관측 행 `row` 의 노드에만(단일: pos 에 I / 차동: pos +I,
  neg −I). 관측 행 범위 밖도 ValueError.
- `rout_ohm` = DC 극한 관측값 / I. DC 극한이 정의 안 되면 None + 그 사유. 값이 음수면 None + `negative_output_resistance`
  (definitional, detail `value_ohm` -- 음수를 값으로 넘기면 `rout_ss_ohm <= x` 가 늘 통과한다, 7a Q3 오케스트레이터 결정).

### 3.12 `response_ratio(response, num_column, den_column, row=0) -> ResponseRatio`
- `ratio_db` = 20·log10|H_num(0)/H_den(0)|, 같은 계의 두 열(같은 G·C·관측, 추가 분해 0). 분모·분자 0 은 `den_zero`·`num_zero`.
  결과 `ResponseRatio.row` = 인자 `row`(9절 분해능이 같은 관측 행을 읽는다, 기본 0).

### 3.13 `supply_currents(op, counted_rails) -> SupplyCurrents`
- I_k(레일 k → 회로) = 채널(drain=k: +i, source=k: −i) + 저항((V_k − V_other)/R) + 이상 전류원(from=k: +amp, to=k: −amp).
- `supply_current_dc` = Σ_{k∈counted_rails} I_k(DEC-78, 기본값 없음 -- 빈 선언·레일 밖·중복은 ValueError),
  `power_dc_w` = Σ_k V_k I_k, `kcl_residual_amp` = Σ_k I_k. 레일 이름 기본값 없음.

### 3.14 `area_search(gates, passives) -> AreaSearch`
- `area_search_m2` = Σ W·L + Σ(값 × 단위 면적, 선언된 것만). 미선언 수동소자 label → `passive_area_undeclared`(정렬).

### 3.15 `metric_registry()`, `metric_catalog()`, `metric_value(name, source)`
- 등록 10개(metric → 결과 형식.필드, 단위, 영역, view_kind):

| metric | 결과 형식.필드 | 단위 | 영역 | view_kind | objective_axis |
|---|---|---|---|---|---|
| `gain_ss_db` | LoopAnalysis.gain_db | db | ss | transfer | -- |
| `ugf_ss_hz` | LoopAnalysis.ugf_hz | hz | ss | transfer | -- |
| `gbw_ss_hz` | LoopAnalysis.gbw_hz | hz | ss | transfer | -- |
| `parasitic_pm_ss_deg` | LoopAnalysis.phase_margin_deg(전달 뷰 인수) | deg | ss | transfer | -- |
| `pm_ss_deg` | LoopAnalysis.phase_margin_deg(β 루프 `ProbeFactor` / β = 1 포트 `Factor`, 3.10) | deg | ss | loop | -- |
| `ratio_ss_db` | ResponseRatio.ratio_db | db | ss | ratio | -- |
| `rout_ss_ohm` | OutputResistance.rout_ohm | ohm | ss | output_port | -- |
| `supply_current_dc` | SupplyCurrents.supply_current_dc | amp | dc | -- | power |
| `power_dc_w` | SupplyCurrents.power_dc_w | w | dc | -- | -- |
| `area_search_m2` | AreaSearch.area_search_m2 | m2 | geom | -- | -- |

- `metric_catalog()` = {이름: MetricSignature} 읽기 전용(spec 로더 `metric_catalog` 인자).
- `metric_value`: 미등록 KeyError, 형식 다르면 TypeError, 그 외에는 `MetricResult`(값 None 이면 그 필드의 `Undefined` 들).
  `metric_value` 는 분해능을 계산하지 않는다(`resolution` None) -- 분해능은 `metrics_ss` 가 9절로 붙인다.
- 오라클 측정 이름(DEC-90 (3) `oracle_measure`, 레지스트리 필드로는 아직 없음 -- 넣을 때 이 대응): `pm_ss_deg` → `pm_deg`,
  `rout_ss_ohm` → `rout_ohm`(오라클 C26).

### 3.16 `cut_circuit(circuit, cuts) -> CutCircuit` (7a 2.2 L3, 2.4 '계 구성')
- 순수 함수. `LoopCut` 마다 그 원소 단자를 원래 노드 n 에서 새 노드 x 로 옮긴다. 같은 원래 노드에서 옮긴 단자는 같은 x(오라클
  `lbx_<넷>` 하나). x = 원래 회로 최대 노드 인덱스 뒤에 n 오름차순(재번호 불변). 교류접지는 그대로(고정 노드 = 레일 ∪ gate 전용
  미구동 넷 ∪ 절단 안 된 입력 포트는 회로 레코드를 만드는 쪽이 `ac_ground` 로 준다, 7a 2.2 L4).
- 결과: `circuit`(절단 회로), `cuts`, `pairs`((n_k, x_k) n 오름차순), `excitations`(단위 전류 I(n_1..n_k), I(x_1..x_k), 단위 전하
  Q(n_1..n_k), Q(x_1..x_k) -- 4k 열), `senses`(V(n_1..n_k), V(x_1..x_k) -- 2k 관측). `build_mna(cut.circuit, cut.excitations,
  cut.senses)` 로 조립 1회.
- TypeError: cuts 가 tuple 이 아니거나 비었음(2절 모양 위반 규약), 원소가 `LoopCut` 아님. ValueError: index 가 원소 수 밖,
  같은 원소를 두 번(두 단자 모두 -- 로더 `feedback_cut_ambiguous` 와 같은 조건), 절단 노드가 교류접지.

### 3.17 `probe_factor(response, pairs, weights) -> ProbeFactor` (7a 2.4)
- `response` = 절단 회로 계 하나의 `SystemResponse`. 열·관측은 구조로 찾는다(노드 v: `Sense(v)`, v 에만 전류를 넣는 열, v 에만
  전하를 넣는 열 -- 정확히 하나씩, 아니면 ValueError; 절단 노드가 미지수가 아니면 ValueError). `weights` = 쌍마다 0 아닌 유한
  실수(0·비유한 ValueError, tuple 아님·길이 ≠ pairs 길이 TypeError).
- Z(2k×2k, 행 = V(n), V(x), 열 = 같은 순서 단위 주입), P = [I; −I], M = Pᵀ·Z·P, s = [w; 0]:
  Tv = −wᵀV_x / wᵀV_n(V = Z·P·M⁻¹w), Ti = wᵀI / wᵀ(w − I)(I = M⁻¹·Pᵀ·Z·s), **T = (Tv·Ti − 1)/(Tv + Ti + 2)** -- 오라클
  `loop_gain` 과 같은 식·같은 부호 규약(`Vlb n x`, `Ilb 0 n`, `i(Vlb)` n → x). 오라클의 두 `.ac` 를 같은 계의 여기 열로 중첩
  (근사 없음).
- ω > 0: 전류 열. ω = 0: 전류 열 중 `dc_charge_injection` 이 없으면 전류 열 DC 해, 전부면 전하 열 DC 해(Tv·Ti 는 Z 의 0차
  동차식이라 열마다 같은 배율 s 는 값을 바꾸지 않는다), 섞이면 T(0) NaN + `loop_cut_mixed_charge`. M 특이 → 그 점 NaN +
  `loop_probe_singular`, Tv·Ti·T 분모 0 → `den_zero`.
- 결과 필드: 격자 위 T `samples`(1회 계산 보관), T 의 `poles`·`zeros`(항등식 1/(1 + T) = 1/(1 + Tv) + 1/(1 + Ti) = Q,
  Q·wᵀw = H + wᵀw, H = 프로브 전압원 k 개를 넣은 절단 회로 두 벌의 한 전달함수 → T = −H/(H + wᵀw): 영점 = H 영점, 극점 =
  H + wᵀw 영점, 증강 pencil), `undefined`(격자 표본 사유).
- 근의 정밀도 규약: `poles`·`zeros` 는 T 의 근이다 -- 근으로 재구성한 T(0)·Π(1 − s/z)/Π(1 − s/p) 가 T 와 같고(원점 근은 양쪽에
  같은 수, 상쇄), 노드 번호에 무관하다. 그러려고 (1) 용량 전용 노드 행(G 행 0)을 s 로 나눠(`solve_dc_limit` 의 전하 보존 식과
  같은 변환 -- 해 불변) 원점 결함 고유값을 없애고, 절단 노드가 용량 전용이면 프로브 전류 j = s·j'·2회 주입을 전하로 둔다(ω = 0
  열 선택과 같은 규칙, T 는 실험 배율에 무관), (2) `finite_eigs` 가 Ward 균형 뒤 유한·원점·무한 판정을 한다(3.4). 서로 지워지는
  극점·영점 쌍(분리 모드)은 남을 수 있다 -- 상계를 느슨하게 할 뿐 틀리게 하지 않고, 쌍을 지우려면 근 일치 문턱(상수)이 필요해
  지우지 않는다. 2026-10-07 실측(예 7·7b DM·CM, 재번호 포함): 지배 극점이 폐형식과 상대오차 ≤ 1.5e-15, 우반면 근 0, 나머지는
  같은 값 극점·영점 쌍. 사후 오차(격자 밖 점) = Z 원소 오차의 1차 전파 Σ|∂T/∂Z|·e,
  ∂T/∂Z = −(1 + T)²·∂Q/∂Z(해석 미분, 상수 없음).
- 격자: 루프 계와 포트 전달 계를 한 번의 `solve_responses` 로 함께 푼다(원래 회로 근이 격자에 들어간다, 7a 2.4 '격자' E2).

## 4. 불변식 (test 가 확인할 성질)

| # | 성질 |
|---|---|
| I-1 | 조립 1회: `solve_responses`·`analyze_loop`·`output_resistance`·`response_ratio` 동안 스탬프 함수 추가 호출 0 |
| I-2 | 같은 `SystemResponse` 를 여러 metric 이 공유: gain·UGF·GBW·PM 은 `analyze_loop` 1회의 필드, rout·ratio 는 같은 DC 해 |
| I-3 | 결정론: 같은 입력 두 번 → 격자·metric 비트 동일 |
| I-4 | gmb: source follower 이득 = gm/(gm+gmb+gds+GL). gmb = 0 으로 두면 값이 달라진다(옛 엔진 gmb 0건 결함 red) |
| I-5 | cgd(또는 Miller C) 스탬프가 극점을 분리시킨다(예 3의 p1·p2) |
| I-6 | 저항 값 없는 레코드는 생성 단계에서 거부(1e9 기본값 없음) |
| I-7 | 노드 재번호 불변(이름 리터럴 0) |
| I-8 | 레일 원점 이동: `power_dc_w` 변화 = Δ·잔차, `supply_current_dc` 불변 |
| I-9 | 엔진 소스에 숫자 리터럴·회로 이름 0(구조 test D·E) -- dB 계수는 `core/units.py` |
| I-10 | 값 의존 정의 불가에서 예외 0: `metric_value` 는 항상 `MetricResult` |
| I-11 | 용량 전용 노드: DC 극한 = 전하 보존 해(예 2c·2d), 그 노드에 DC 전류 주입한 열만 `dc_charge_injection` |
| I-12 | Middlebrook T = 단일 제어원 루프의 되돌림 비: 예 7 에서 `probe_factor` T 와 폐형식의 상대오차 ≤ 차원·eps 규모(실측 ≤ 3.3e-15) |
| I-13 | 가중 공통 배율 불변: 예 7b 에서 (½, −½) 와 (1, −1) 의 T 가 같다(모드는 부호·비가 고른다 -- DM 5, CM 25) |
| I-14 | 절단 계 조립 1회: 4k 열·2k 관측 한 계, `cut_circuit`·`probe_factor`·`analyze_loop` 동안 스탬프 함수 추가 호출 0(`build_mna` 1회 뒤) |
| I-15 | β = 1(feedback 빈 list)에서 `pm_ss_deg` = 기본 포트 뷰 `parasitic_pm_ss_deg` 비트 동일(같은 MnaSystem 의 같은 `Factor`) |
| I-16 | A·β 무부하 인수 곱 값(예 7 대조 UGF 39756892.0418 Hz)을 `pm_ss_deg` 경로가 내면 FAIL -- 옛 정의 red |
| I-17 | PM 전제(3.10): 인수 `poles` 에 Re > 0 근이 있으면 `phase_margin_deg` 는 None + `loop_open_rhp_poles`(예 8·8a·8b -- 옛 값 271.145°·274.443° 를 내면 FAIL). 없으면 `LoopAnalysis` 전 필드·`undefined` 가 전제 도입 전과 비트 동일(예 1~7c). `phase_lag_rad`·`ugf_hz` 는 우반면 근이 있어도 값 그대로 |

## 5. 손계산 예 (엔진과 독립인 폐형식으로 대조 가능)

모든 예는 노드 0 = 교류접지(소신호 접지). 진폭 1 V 구동. 아래 값은 2026-10-07 직접 실행에서 엔진과 손계산이 상대오차
≤ 6.3e-12 로 일치했다(최대는 Miller p1 의 고유값 반올림). 관측은 모두 1-tuple(`(Sense(…),)`).

### 예 1 -- RC 저역통과
- `Resistor(1, 2, 1e3)`, `Capacitor(2, 0, 1e-9)`, `ac_ground=(0,)`, 여기 1 V at 1, `Sense(2)`. H = 1/(1 + sRC).
- 기대: `gain_ss_db` = 0, f_3dB = `gbw_ss_hz` = 1/(2πRC) = 159154.943 Hz. `ugf_ss_hz`·`pm_ss_deg` = 정의 안 됨
  (`dc_not_above_level`, |H(0)| = 1 은 1 을 넘지 않는다) -- `metric_value` 는 `MetricResult(value=None, undefined=…)`.

### 예 2 -- 단일 극 증폭기(CS) + β 되먹임 (인수 곱 기계 test -- `pm_ss_deg` 정의 아님, 3.10·예 7)
- A 계: `MosSmallSignal(d=2, g=1, s=0, b=0, gm=1e-3, gmb=0, gds=1e-5)`, `Capacitor(2, 0, 1e-12)`, 열 `vin`(1 V at 1)·`iout`(1 A at 2),
  `Sense(2)`. β 계(저항): `Resistor(2, 3, 30e3)`, `Resistor(3, 0, 10e3)`, 열 `vfb`(1 V at 2), `Sense(3)`. 한 번의
  `solve_responses((A, β, …))` 로 푼다(공유 격자).
- 폐형식: A(s) = −gm·ro/(1 + s·ro·CL), ro = 100 kΩ, A0 = −100, ω_p = 1e7 rad/s. β = 0.25.
- β = 1(인수 1개): `gain_ss_db` = 40, UGF = ω_p√(A0² − 1)/2π = 159146985.146 Hz, GBW = 159154943.092 Hz,
  PM = 180° − atan√(A0² − 1) = 90.5729673449°. 같은 인수로 `parasitic_pm_ss_deg` 도 90.5729673449°(전달 뷰 = β 1 루프).
- β = 0.25(인수 2개): |T0| = 25 → 27.9588001734 dB, UGF = ω_p√624/2π = 39756892.0418 Hz, PM = 180° − atan√624 = 92.292442776°.
- `output_resistance(A 응답, 1)` → 100000 Ω.

### 예 2b -- gmb 가 들어간 source follower
- `MosSmallSignal(d=9, g=1, s=2, b=0, gm=1e-3, gmb=2e-4, gds=1e-5)`, `Resistor(2, 0, 1e4)`, `ac_ground=(0, 9)`, `Sense(2)`.
- A = gm/(gm + gmb + gds + 1/RL) = 0.763358779. gmb = 0 이면 0.900900901.

### 예 2c -- 순수 용량 분압 β (전하 보존 극한; 인수 곱 기계 test -- `pm_ss_deg` 정의 아님)
- β 계: `Capacitor(2, 3, Cf=1e-12)`, `Capacitor(3, 0, Cs=3e-12)`, `ac_ground=(0,)`, 열 1 V at 2, `Sense(3)`. 노드 3 은 컨덕턴스가 없다
  (`charge_nodes`). 전하 보존: Cf(v3 − v2) + Cs·v3 = 0 → β = Cf/(Cf + Cs) = 0.25(모든 ω 에서 같다).
- 기대: DC 극한 0.25, 격자 끝 |H| 0.25. 예 2 의 A 와 묶으면(인수 2개) 저항 β 와 같은 값: 27.9588001734 dB,
  UGF 39756892.0418 Hz, PM 92.292442776°.

### 예 2d -- 회로 안 SC 되먹임(gate 가 용량으로만 연결된 폐루프 CS)
- `MosSmallSignal(d=2, g=3, s=0, b=0, gm=1e-3, gds=1e-5)`, `Capacitor(2, 3, Cf=1e-12)`, `Capacitor(3, 1, Cs=3e-12)`, `Capacitor(2, 0, 1e-12)`,
  열 `vin`(1 V at 1)·`iinj`(1 A at 3), `Sense(2)`.
- 폐형식: 노드 3 전하 보존 Cf(v3 − v2) + Cs(v3 − v1) = 0, 노드 2 KCL gm·v3 + gds·v2 = 0 → v2/v1 = A0·Cs/((Cf + Cs) − A0·Cf)
  = −300/104 = −2.884615385(이상값 −Cs/Cf = −3 에 유한 이득 오차). `iinj` 열은 노드 3 에 DC 전류를 넣으므로
  `dc_charge_injection`(그 열만 NaN, 예외 없음).

### 예 3 -- 2극 Miller
- `M1(d=2, g=1, s=0, b=0, gm1=1e-4, gds=1e-6)`, `M2(d=3, g=2, s=0, b=0, gm2=1e-3, gds=1e-5)`, `Capacitor(2, 0, 0.1e-12)`,
  `Capacitor(3, 0, 1e-12)`, `Cc = Capacitor(2, 3, 0.5e-12)`, 여기 1 V at 1, `Sense(3)`.
- 폐형식(R1 = 1/g1, R2 = 1/g2): H(s) = gm1gm2R1R2(1 − sCc/gm2)/(1 + a1 s + a2 s²),
  a1 = R1(C1+Cc) + R2(CL+Cc) + gm2R1R2Cc = 5.075e-5, a2 = R1R2(C1CL + C1Cc + CLCc) = 6.5e-14.
- 기대: `gain_ss_db` = 80, |p1| = 19704.9308 rad/s, |p2| = 780749525.838 rad/s, 영점 +gm2/Cc = 2e9 rad/s(우반면),
  UGF = 30592376.7006 Hz, GBW = 31361371.396 Hz, PM = 70.6851677849°(폐형식 H 의 조밀 격자 언랩으로 독립 계산).
  근사식: UGF ≈ gm1/(2πCc) = 31.83 MHz, PM ≈ 90° − atan(ω_u/p2) − atan(ω_u/z) = 69.92°.

### 예 4 -- 레일 전류·전력
- 레일 10 = 1.8 V, 레일 0 = 0 V, `node_v=((6, 0.8),)`. 채널 (5→0, 10 µA), (5→10, −10 µA: PMOS 부하), (7→0, 5 µA),
  저항 10–6 100 kΩ, 6–0 80 kΩ, 이상원 10→7 5 µA, `counted_rails=(10,)`.
- 기대: I_10 = 25 µA, I_0 = −25 µA, `supply_current_dc` = 25 µA, `power_dc_w` = 45 µW, 잔차 0. 모든 전압 +1 V 뒤에도 45 µW.

### 예 5 -- 면적
- `GateArea(10e-6, 0.5e-6)`, `GateArea(4e-6, 1e-6)`, `PassiveArea("cc", 0.5e-12, 5e2)`, `PassiveArea("rz", 5e3, None)`.
- 기대: `area_search_m2` = 2.59e-10 m², `passive_area_undeclared` = ("rz",).

### 예 6 -- 응답비
- `Resistor(1, 2, 1e3)`, `Resistor(2, 3, 1e4)`, 열 `num`(1 V at 1)·`den`(1 V at 3), `Sense(2)`.
- H_num(0) = Rb/(Ra+Rb), H_den(0) = Ra/(Ra+Rb) → `ratio_ss_db` = 20·log10(Rb/Ra) = 20 dB.

### 예 7 -- CS + 용량 되먹임(β 루프, 단일 절단, 용량 전용 절단 노드) (7a 2.8)
- `MosSmallSignal(d=2, g=3, s=0, b=0, gm=1e-3, gmb=0, gds=1e-5)`, `Capacitor(2, 0, CL=1e-12)`, `Cf = Capacitor(2, 3, 1e-12)`
  (capacitors index 1), `Cs = Capacitor(3, 0, 3e-12)`, `ac_ground=(0,)`. 입력 포트 = 노드 3, F = {Cf} →
  `cut_circuit(c, (LoopCut("capacitor", 1, "b"),))`: pairs ((3, 4),). n = 3(gate + Cs), x = 4(Cf 만) 모두 용량 전용 → 전하 열 DC 극한.
  `build_mna(cut.circuit, cut.excitations, cut.senses)`, `probe_factor(응답, cut.pairs, (1.0,))`.
- 폐형식(되돌림 비): T(s) = gm·Cf/(Cf + Cs) / (gds + s(CL + Cf·Cs/(Cf + Cs))). T(0) = (gm/gds)·Cf/(Cf + Cs) = 25,
  ω_p = gds/(CL + 0.75 pF) = 5714285.71429 rad/s.
- 기대: Tv(0) = A0 + Cs/Cf = 103, Ti(0) = (A0 + 1)·Cf/Cs = 101/3(A0 = gm/gds = 100), T(0) = 25(정확). `gain_db` =
  27.9588001734 dB, UGF = ω_p·√624/2π = 22718224.0239 Hz, `pm_ss_deg` = 180° − atan√624 = 92.292442776°. ω = 1e3·1e6·1e7·1e8·1e9
  rad/s 에서 Middlebrook T 와 폐형식 상대오차 ≤ 3.3e-15. 2026-10-07 엔진 실측: T(0) = 24.999999999999993, UGF 상대오차
  3.3e-16, PM 상대오차 3.1e-16, 5 점 최대 상대오차 3.13e-15.
- 대조(I-16): 같은 소자로 A·β 무부하 인수 곱(예 2c 와 같은 계)이면 ω_p = gds/CL = 1e7 rad/s, UGF 39756892.0418 Hz -- 이 값을
  `pm_ss_deg` 경로가 내면 FAIL(옛 정의 red). 단일 극이라 PM 은 둘 다 92.29° 이고 UGF 가 1.75배 다르다.

### 예 7b -- 차동 절단 2개, 가중이 모드를 고른다
- 예 7 반회로 두 벌(a: 노드 2·3, b: 노드 12·13, 각 Cf 를 index 1·4 로), 출력 사이 `Resistor(2, 12, 5e4)`. 절단 2개(두 입력),
  가중 (+½, −½).
- 차동 반회로 폐형식: 출력 부하 gds + 2/Rx → T_DM(0) = gm/(gds + 2/Rx)·0.25 = 5. 가중 (+½, +½) 면 Rx 에 전류가 없어
  T_CM(0) = 25. 가중 (1, −1) 은 (½, −½) 와 같은 T(I-13).
- 기대(실측): DM 5.000000000000001, CM 25.00000000000007, 배율 바꿈 값 동일.

### 예 7c -- 섞인 절단(정의 불가 값)
- 예 7 에서 Cs 를 `Resistor(3, 0, 1e5)` 로 바꾸면 n = 3 은 전도 노드, x = 4 는 용량 전용 → `metric_value("pm_ss_deg",
  analyze_loop((pf,)))` = `MetricResult(value=None, undefined=(Undefined("phase_margin_deg", "loop_cut_mixed_charge",
  "definitional", …),))`, 예외 없음(I-10).

### 예 8 -- 우반면 극점 하나인 T (β = 1 `Factor`, PM 전제 위반, 3.10)
- `M1 = MosSmallSignal(d=2, g=1, s=0, b=0, gm=1e-3, gmb=0, gds=1e-5)`, 교차 결합 쌍 `M2(d=2, g=5, s=0, b=0, gm=gx, gds=1e-5)`·
  `M3(d=5, g=2, s=0, b=0, gm=gx, gds=1e-5)`, gx = √1.2e-9, `Capacitor(2, 0, 1e-12)`, `Capacitor(5, 0, 1e-12)`, `ac_ground=(0,)`,
  열 1 V at 1, `Sense(2)`, `Factor(응답, 0)`.
- 폐형식: 노드 2 (g2 + sC)v2 + gx·v5 = −gm·v1(g2 = 2e-5), 노드 5 gx·v2 + (g5 + sC)v5 = 0(g5 = 1e-5) →
  det = (g2 + sC)(g5 + sC) − gx² = C²(s − 2e7)(s + 5e7), **T(s) = 10·(1 + s/1e7)/((1 − s/2e7)(1 + s/5e7))** -- 극점 +2e7(우반면)·
  −5e7, 영점 −1e7, T(0) = 10.
- 기대: `gain_db` = 20, UGF = 158931912.449 Hz(|T| = 1, brentq), `phase_lag_rad` = −(atan(ω_u/1e7) + atan(ω_u/2e7) − atan(ω_u/5e7))
  = −1.59078562547(위상 앞섬), **`phase_margin_deg` = None + `loop_open_rhp_poles`(rhp_poles = ((2e7, 0.0),), 개수 1)**. 옛 정의
  값 180° − 지연 = 271.145302449° 는 `>=` 제약을 통과하지만 폐루프 특성식 1 + T = 0 의 근은 +9.812e8·−1.121e7 rad/s(불안정) --
  이 값을 `pm_ss_deg`·`parasitic_pm_ss_deg` 경로가 내면 FAIL(옛 정의 red). 2026-10-08 엔진 실측: 극점 19999999.999999996 + 0j,
  UGF 158931912.4494295 Hz(폐형식과 상대오차 ~5e-16), `phase_lag_rad` 폐형식과 비트 동일.

### 예 8a -- 개루프 우반면, 폐루프 안정(`ProbeFactor`) -- PM 은 그래도 정의 안 됨
- 예 7 회로 + 노드 2 에 교차 결합 쌍(예 8 의 M2·M3·노드 5 용량, gx = √1.2e-9), 절단·가중 예 7 과 같다.
- 노드 2 순 컨덕턴스 = 2e-5 − gx²/g5 = −1e-4(개루프 음수 → T 극점 하나 우반면), 되먹임이 더하는 gm·Cf/(Cf + Cs) = 2.5e-4 로
  폐루프는 안정. 실측(2026-10-08): T 극점 우반면 15481601.1727 rad/s 1 개, 폐루프 극점(절단 전 회로) 0·−5.3945e6·−1.5889e8 --
  Nyquist N = −1(반시계 1 회), Z = N + P = 0. 옛 값 274.443°, 새 값 None + `loop_open_rhp_poles`(개수 1).

### 예 8b -- 상쇄 안 된 공통 우반면 근(감김 수 대안이 틀리는 예)
- 예 8a 에서 gx = √5.2e-9(순 컨덕턴스 −5e-4). 실측: T 극점 +8278492.15·+43801205.4·−6.52e7·−1.726e8, 영점 +8278492.15·−1e7·
  −1.726e8 -- +8278492.15 는 극점·영점 양쪽에 있는 공통 근(분리 모드)이자 폐루프 극점이다. |T(0)| = 0.5 라 UGF 는
  `dc_not_above_level` 이고 `phase_margin_deg` 사유는 `loop_open_rhp_poles`(개수 2, 전제 위반이 먼저). 폐루프 우반면 극점 1 개 =
  N(0) + 실제 T 의 P(1). 근 목록으로 P 를 세면 2 라 Z = 2 로 틀린다(3.10 '대안을 쓰지 않는 이유' (1)).

## 6. 열린 항목

| # | 항목 | 현재 처리 |
|---|---|---|
| M1 | PM 의 루프 절단 위치(A·β 각 뷰) | **닫음**(2026-10-07) -- 7a design: β 루프 = 절단 회로 `ProbeFactor`(Middlebrook), β = 1 = 포트 `Factor`, 인수 2개 곱은 정의 아님(3.10·3.16·3.17). spec 쪽은 authoring SPEC_CONTRACT 2절·3절(S1 닫음) |
| M7 | 섞인 절단(전도 노드와 용량 전용 노드가 함께인 절단)의 ω → 0 극한 | 정의 불가 값 `loop_cut_mixed_charge`(로랑 전개 다음 차수가 필요). 9회로 선언에는 없다 -- 쓰는 회로가 생기면 확장 |
| M3 | 정의 불가 사유 → N3.14 분류 | MOD5 는 값으로만 낸다(2절 표는 권고). 판정 계층이 확정 |
| M4 | `supply_current_dc` 단위 접미사(DEC-68: `_amp`) | 설계 문서·spec 설계 objective 표 이름 그대로 |
| M5 | `area_search_m2` 의 objective_axis | None(예산 대상은 판정 축 `area_layout_m2`) |
| M6 | `cap_model` 근사 표시(DF-28)·`verified_by` | **근사 표시 닫음**(7절: `MetricBundle.approximations` 에 cap·gmb·junction 모형). `verified_by` 는 레지스트리 필드로 아직 없음 |


---

## 7. 2단계 -- ss_linearize 배선 (봉인 스냅샷 → 소신호 레코드 → spec 제약 metric, 2026-10-08)

근거: DM 3.2(`ss_linearize`)·3.3·3.5(커널 순서 봉인 → ss → mna → metric), 7a 2.2~2.5·3.2·4.5 단계 5(배선 지점), 설계
`design_mod6_search_front.md` 2.2(블록 표 ss·mna·freq·⑥), REQ '확정 사항' 1·5(필드 = 캐시, writer 하나, 같은 입력 재계산 0),
DEC-67(봉인 스냅샷만), DEC-78·79·91·92, sizing CONTRACT 2절(권한표 `S2_WRITERS`·`SealedSnapshot`), lut CONTRACT r6 4.1(`op_point`·
`caps`)·4.3(열 출처)·4.4(`gmb` = GMBS 열), 오케스트레이터 결정 2026-10-08(7.9 Q1~Q6).

### 7.0 파일·층·필드

| 층 | 파일 | 진입점 | 계산 블록(writer) | 쓰는 필드 |
|---|---|---|---|---|
| 0 | `ss_types.py` | (데이터) `SsDevice`·`SsCircuit`·`MetricRequest`·`MetricBundle`·`SsEvaluation` | -- | -- |
| 1 | `junction_source.py` | `JunctionSource` | -- | -- (접합 용량 입력 묶음, 7.2·7.6) |
| 1 | `ss_linearize.py` | `ss_dev` | `ss_dev` | `device.ss_dev`(MOS 마다 `SsDevice`) |
| 1 | `ss_circuit.py` | `ss_circuit` | -- | -- |
| 3 | `dc_metrics.py` | `metrics_dc` | `metrics_dc` | `graph.metrics_dc`(key `METRICS_KEY` = `"metrics"`) |
| 6 | `ss_metrics.py` | `metrics_ss` | `metrics_ss` | `graph.metrics_ss`(key `METRICS_KEY`) |
| 7 | `ss_evaluate.py` | `ss_evaluate` | -- | -- |

권한표: 세 필드는 sizing `S2_WRITERS` 에 `SS_WRITES` 로 선언돼 있다(sizing CONTRACT 2절 끝 표). writer 이름 상수 `SS_DEV_WRITER`·
`METRICS_SS_WRITER`·`METRICS_DC_WRITER`·`METRICS_KEY` 는 `gmid_engine.sizing` 공개 이름이다. 블록은 core `compute_block`(core 6절):
입력 버전 = fp_of((이름, 코드 해시, 투영 지문)), 같으면 재사용(스냅샷 `is` 반환), `stats()` 계수. 뷰 어휘는 authoring 공개 이름
(`INPUT_DIRECTION`, `BETA_DECLARED`, `SENSE_DIFFERENTIAL` -- 마지막은 이번에 authoring `__all__` 에 더함).

### 7.1 값 형식 (`ss_types`, frozen)
- `SsDevice(gm, gmb, gds, cgg, cgs, cgd, cgb, cdb, csb, cap_model, gmb_model, junction_model, lut_rel_tol=None)` -- S·F 절댓값(소자
  총 폭 W). [9절, 2026-10-08] `lut_rel_tol` = LUT 파라미터의 상대 불확실성 ε(무차원, 9.1), 미정이면 None -- 기본값 None 이라 12칸
  생성자 호출도 받는다(필드 순서 test 는 13칸으로 갱신 대상).
- `SsCircuit(nodes, circuit, resistors, capacitors, ground_nets, input_nets, missing=())`.
- `MetricRequest(metric, view=None)` -- `view` = authoring `ViewDecl`. 값·op 는 들지 않는다(임계를 바꿔도 블록 입력 버전 불변).
- `MetricBundle(entries, approximations=(), detail=())` -- `entries` = ((MetricRequest, MetricResult), ...) 요청 순서.
- `SsEvaluation(snapshot, ss, dc, lineage=None)` -- `lineage` = sizing `DcEvaluation(snapshot, report, SealedSnapshot(snapshot, report))`.

### 7.2 `ss_dev(snapshot, lut, junction)` -- reads `device.dc_op`, [9절] `device.dc_tol_v`, extras `(LutAccess, JunctionSource)`
- [9절, 2026-10-08] `ss_dev.reads == (("device", "dc_op"), ("device", "dc_tol_v"))`. `lut_rel_tol = dc_op.gm_id · dc_tol_v`(그 소자 열에
  dc_tol_v 가 없거나 None 이면 None). dc_tol_v 는 sizing `dc_tolerances` 가 쓴 tol_V(id_equivalent) 셀(sizing CONTRACT 6절 tol 행,
  봉인 2 와 같은 값) -- LUT 를 다시 조회하지 않는다. dc_tol_v 만 바뀌어도 블록 입력 버전이 바뀐다(재계산 1회).
- MOS(= `dc_op` 이 있는 소자)마다, `op = dc_op`, `w_m` = 슬라이스 `(op.kind, op.w_key)` 의 폭:
  `gm = op.gm_id · op.current`, `gds = op_point(memo, kind, w_key, L, vgs, vds, vsb).gds_per_w · op.W`,
  `gmb = lut.gmb(같은 인자) · op.W / w_m`, `(cgg, cgd, cgs, cgb, cap_model) = lut.caps(memo, kind, L, vgs, vds, vsb, op.W)`,
  **접합 용량(DEC-91, 2026-10-08 배선)** `(cdb, csb) = junction_caps(junction.params_of(op.kind),
  junction.pre_layout_geometry(w_m, op.W / w_m), op.vds + op.vsb, op.vsb, junction.temp_c)`(8절 -- 기하 = LUT 생성 규칙,
  finger_w = w_m, m = W / w_m), `junction_model = JUNCTION_LUT_RULE`(`"pdk_bsim4_lut_rule_diffusion"`). (L, vgs, vds, vsb) 는 `dc_op` 의 값
  그대로(크기, LUT 부호 규약). 옛 `JUNCTION_PENDING`(cdb = csb = 0) 경로와 이름은 삭제했다.
- `JunctionSource(params, lut_rule_decl, temp_c, pdk_decl_sha256)`(frozen): `params` = ((kind, `JunctionParams`), ...) kind 정렬,
  `lut_rule_decl` = LUT 규칙 core `PdkDecl`, `temp_c` = LUT 측정 온도, `pdk_decl_sha256` = PDK 선언 파일 sha256.
  `JunctionSource.from_decls(pdk_decl, lut_rule_decl, lut_set)`: kind = `lut_set.spec.device_kinds` 의 kind 집합(정렬), 온도 =
  `dict(lut_set.provenance.cap_conditions)["temp_c"]`(없으면 ValueError), params = `JunctionParams.from_pdk_decl(pdk_decl, kind)`.
  `params_of(kind)`(없는 kind -> KeyError), `pre_layout_geometry(finger_w, m)` = `DiffusionGeometry.from_lut_rule(lut_rule_decl, finger_w, m)`.
  블록 입력 버전에 이 묶음 전체가 지문으로 든다 -> 접합 파라미터·LUT 규칙 선언(원본 sha256 포함)·온도·PDK 선언 sha256 중 하나가
  바뀌면 `ss_dev` 재계산, 같으면 재사용.
- 접합 계산 예외(`junction_caps` 의 ValueError -- Weffcj ≤ 0, 보정 뒤 PB ≤ 0)는 그대로 전파한다(LUT 조회 실패처럼 감싸지 않는다 --
  선언 결함이지 후보 실패가 아니다).
- [lut r6] `gmb_model`: lut CONTRACT 4.3 열 출처 규칙과 같은 판정 -- 그 폭 슬라이스 `columns` 에 `"GMBS_PER_ID"` 가 있거나, 기준 LUT
  `CapTable.w_key == op.w_key` 이고 그 `columns` 에 있으면 `GMB_COLUMN`(`"lut_gmbs_column"`, 값 = lut `gmb` 의 열 정의 4.4), 아니면
  `GMB_VS_CELL_SECANT`(`"lut_vs_cell_secant"`, 옛 LUT 의 r5 VS 할선 -- 임시 근사). LUT v2 실데이터는 모든 폭이 슬라이스 열이라 `GMB_COLUMN`.
- [lut r6] 용량: LUT v2 는 CGS·CGB 열이 있어 `cap_model = "lut_cgs_cgb"`, 값은 **부호 보존**(lut 1.2 -- CGB·CGS 에 음수 점이 있다).
  `Caps.cdd`·`css` 는 읽지 않는다(DEC-91: 접합 용량 정본은 PDK 접합 파라미터, CDD·CSS 는 대조 test 전용 -- 7.9 Q3).
- 불변식(접합): `ss.cdb`·`ss.csb` == test 쪽이 같은 `dc_op`·`JunctionSource` 로 `junction_caps` 를 부른 값(비트). 작성자 실측(아래
  test_ss_evaluate CS 픽스처, toy LUT r6 + sky130 선언): M1 nmos W 2.3700841597752005e-05, w_m 1e-6, vds 0.9, vsb 0 ->
  cdb 1.6192271478167327e-14, csb 2.3226455532310698e-14(직접 호출과 같음), 같은 입력 재호출 computes 0, `temp_c` 만 +10 바꾼 묶음 ->
  `ss_dev` computes +1(cdb 1.6234719737286454e-14).
- LUT 조회 실패 -> `SealViolationError(devices=(소자,))`, detail = 원래 detail + reason `"lut_query_failed"`, `lut_reason` = 원래
  reason, `device_query` ∈ {"op_point", "gmb", "caps"}. (옛 12-L 세트의 용량 VS 0~0.8 V 축 밖 실패는 LUT v2 VS 0~1.8 V 로 해소 -- 7.9 Q6.)
- 불변식: 같은 `dc_op`·LUT -> 재사용(계산 0). `op_point` 는 `dc_widths` 가 같은 키로 이미 부른 값(LUT memo point 적중).

### 7.3 `ss_circuit(nodes, ground_nets, input_nets, devices, passive_values) -> SsCircuit`
- `nodes` 위치 = 노드 인덱스. `devices` = ((이름, element_class, kind, pins, bulk 넷|None, SsDevice|None), ...).
- MOS -> `MosSmallSignal(d, g, s, b, gm, gmb, gds, cgs, cgd, cgb, cdb, csb, label=이름)`(b = bulk 넷 인덱스). `MosSmallSignal` 은
  용량을 부호 있는 유한 실수로 받으므로(1절, Q7 결정) LUT v2 의 음의 용량은 그대로 스탬프된다. bulk None 또는 SsDevice
  None -> `StructureUnresolvedError`(reason `unsupported_rule_branch`, rule_branch `ss_element_kind`).
- 수동소자 kind ∈ `LOOP_CUT_KINDS`(resistor, capacitor): `passive_values` 에 값이 있으면 `Resistor(t0, t1, 값)`/`Capacitor(t0, t1, 값)`
  (pins 순서, label = 이름), 없으면 스탬프하지 않고 `missing` 에(이름순). `resistors`·`capacitors` = 회로 원소 순서의 이름 --
  **스탬프한(값 있는) 원소만** 든다(값 없는 원소는 `missing` 에만 있고 `circuit` 에도 이 두 tuple 에도 없다).
- 이상 전류원(element_class ideal_source, kind current_source): 스탬프 없음(소신호 개방). 그 밖 원소(이상 전압원, 다른 수동 kind)
  -> 위와 같은 `StructureUnresolvedError`(devices = 그 원소, detail element_class·kind).
- `circuit.ac_ground == ()`(뷰가 정한다), `ground_nets`·`input_nets` 정렬.

### 7.4 `metrics_ss(snapshot, requests, passive_values)` -- 뷰 -> 계 -> metric
reads `device.{ss_dev, element_class, kind, pins, bulk, dc_colour}`, `node.{ac_ground_class, port_direction, dc_colour}`. **[r12, 2026-10-08]** 노드·소자 순서 = (`dc_colour` -- 정점마다 유일, 이름은 색 없는 이름만)(이름 치환에 불변한 선형계 행·스탬프 순서; dc_colour 가 없는 이름은 -1). `requests` = `MetricRequest`
tuple(view_kind 가 None 이 아닌 등록 metric), `passive_values` = ((이름, 값), ...). 결과 `MetricBundle`.
- 노드 = `ac_ground_class` 열의 넷(모든 S1 노드, 이름순), ground_nets = 그 값이 None 아닌 넷(레일 ∪ gate 전용 미구동),
  input_nets = `port_direction == INPUT_DIRECTION`.
- 요청 처리: (1) view mode `pending` -> `MetricResult(metric, None, (Undefined(필드, "view_pending", "definitional",
  (("decision", ID),)),))`(필드 = 레지스트리 field). (2) `missing` 이 비어 있지 않으면 나머지 요청 전부
  `Undefined(필드, "passive_value_undeclared", "definitional", (("elements", missing),))` -- 계를 만들지 않는다(일부 소자를 빼고 푸는
  것은 다른 회로). (3) 계 조립.
- 계 규칙(F = 고정 넷, 같은 F 의 뷰는 한 계 -- G·C 같고 열만 다르다; 계의 교류접지 = F − 그 계 열들의 전압 구동 넷):

  | view mode | 계 | 열 | 관측 | 분석 |
  |---|---|---|---|---|
  | `port`, `loop`(beta ≠ declared), `transfer` | F = ground ∪ input ∪ 구동 넷 | 전압 구동(weights 또는 ac_excite) | sense_p − sense_n | `analyze_loop((Factor(응답, 열, 관측 행),))` |
  | `loop` beta declared | 절단 계: ac_ground = ground ∪ (input − 절단 넷), `cut_circuit`(되먹임 소자의 절단 넷 쪽 단자) | 프로브 4k | 2k | `analyze_loop((probe_factor(응답, pairs, 가중),))`, 가중 = view weights 를 pairs 의 n 순서로 |
  | `sense` | F = ground ∪ input | 전류 sense_p +1(차동이면 sense_n −1) | sense | `output_resistance(응답, 열, 행)` |
  | `ratio`(ViewDecl `num`·`den` = 각각 authoring `ExciteSense(ac_excite, sense_p, sense_n, sense_mode)` -- SPEC_CONTRACT 2·3절 ratio view `{num, den}`) | F = ground ∪ input ∪ num·den 구동 넷 | num 열, den 열 | num 관측(= den 관측이어야 함, 아니면 ValueError) | `response_ratio` |

  같은 (계, 열, 관측) 은 같은 분석 객체를 쓴다 -> β = 1 `pm_ss_deg` 와 같은 포트 뷰 `parasitic_pm_ss_deg` 는 **한 평가 안에서** 비트
  동일(I-15). 요청 집합이 다른 평가끼리는 공유 격자가 달라 마지막 자리가 다를 수 있다(실측: 포트 PM 60.49744894787342 대
  60.497448947873394 -- 격자 점 수는 불변식 대상이 아니다, 3.5).
- 모든 계는 `solve_responses` **한 번**(루프 계 + 포트 계 공유 격자). 값 = `metric_value(metric, 분석)`(값은 float 로 정규화).
- [9절, 2026-10-08] 분해능: 계 조립이 있는 호출에서 `parameters = lut_parameters(ss.circuit, (ss_dev[m.label].lut_rel_tol for m in
  ss.circuit.mos))` 1회, 분석 열쇠마다 `metric_resolutions(분석, 출처, parameters, memo)` 1회(memo = 이 호출 안의 dict -- 같은 계·같은 ω
  수반 풀이 공유). 값이 있는 `MetricResult.resolution` = 그 metric 의 레지스트리 필드 `Resolution.value`(float 또는 None), 값이 None 인
  결과·pending·passive 누락 결과는 None. 루프 출처 = 그 분석의 인수 tuple(`Factor` 1개 또는 β 루프 `ProbeFactor` 1개), rout·ratio 출처 =
  그 계 응답. 같은 열쇠의 두 요청(β = 1 `pm_ss_deg`·`parasitic_pm_ss_deg`)은 분해능도 같다(S-3 확장). `detail` 은 바뀌지 않는다.
- `approximations` = 모든 `ss_dev` 의 ("cap", cap_model), ("gmb", gmb_model), ("junction", junction_model) 집합 정렬.
  `detail` = `(("grid_points", 공유 격자 점 수), ("systems", 계 수))`, missing 이면 `(("missing_passives", 이름들),)`, 계산 요청 0 이면 ().
- 예외: 뷰 정의 결함(ratio 관측 불일치, `build_mna`·`cut_circuit` 의 ValueError -- 값과 무관), 미등록 metric KeyError.
  값에 따른 정의 불가는 예외가 아니다(2절).

### 7.5 `metrics_dc(snapshot, passive_values, counted_rails)` -- 전력·면적
reads `device.{dc_op, dc_current, element_class, pins, dc_colour}`, `node.{dc_v, dc_rail_v, dc_colour}`, `graph.dc_current_basis`. **[r12, 2026-10-08]** 노드 인덱스·채널·게이트·수동소자 합산 순서 = (`dc_colour` -- 정점마다 유일, 이름은 색 없는 이름만)(레일 전류·전력·면적의 부동소수 합이 이름 치환에 불변). 따라서 `per_rail_amp` 의 레일 나열 순서도 (`dc_colour`, 이름) 순이다(종래 이름순).
- 노드 인덱스 = (dc_rail_v ∪ dc_v 넷) 이름순. `DcOperatingPoint`: rails = `RailBias(레일, dc_rail_v)`; `basis.ends` 의 (원소, from, to)
  마다 MOS -> `ChannelCurrent(d, s, +dc_current if d == from else −dc_current)`, `basis.resistors` -> `Resistor(from, to,
  passive_values[원소])`, 그 밖 비수동 DC 원소(이상 전류원) -> `CurrentSource(from, to, dc_current)`; node_v = 그 저항 끝 중 dc_v 넷.
- **`power_dc_w` = 선언된 모든 공급 레일(spec `supplies_v` 의 레일 전부)의 Σ V_k·I_k**(오케스트레이터 결정 2026-10-08 Q4 -- 합산 선언과
  무관).
- `counted_rails` = 합산 레일의 **넷 이름** tuple(노드 인덱스가 아니다). 레일(`dc_rail_v` 넷) 밖 이름(회로에 없는 넷·레일 아닌 넷)이나
  중복 -> **ValueError**(합산 레일 선언 결함, 2절 표 -- KeyError 는 미등록 metric 이름 전용, 3.13 과 같은 규칙).
  `supply_currents(op, counted)`: counted = 그 이름들의 노드 인덱스, 비면 모든 레일을 넘기고 합만 버린다. entries 순서 `power_dc_w`,
  `supply_current_dc`, `area_search_m2`(view None). `counted_rails == ()` 이면 `supply_current_dc` = `MetricResult("supply_current_dc",
  None, (Undefined("supply_current_dc", "counted_rails_undeclared", "definitional"),))` -- 그 `Undefined.detail == ()`(빈 tuple).
- 면적: `area_search(GateArea(op.W, op.L) MOS 마다, PassiveArea(이름, 값) 값 있는 수동소자 -- 단위 면적 None)`.
- `detail` = counted_rails, kcl_residual_amp, passive_area_undeclared, passive_value_missing, per_rail_amp((레일 넷, A), ...) 키 정렬.
- [9절] 전력·면적 결과의 `resolution` 은 None(LUT 소신호 불확실성 전파 대상이 아니다 -- 전력 축 분해능 b_P 는 search 쪽 유도값).

### 7.6 `ss_evaluate(sealed, ctx, theta, constraints, counted_rails=(), *, junction) -> SsEvaluation`
- **[r5 2026-10-08, DEC-92 / 7.9 Q5 해결] 인자 `passive_theta` 삭제**: engine 보상 수동소자 값은 이제 sizing θ 스키마 성분
  (`capacitance`·`ss_resistance`, sizing CONTRACT 4.4 r5)이라 θ 에서 읽는다(값의 출처 하나). 6번째 위치 인자를 넘기던 호출은 TypeError.
- `sealed` 가 `SealedSnapshot` 아님 -> TypeError(DEC-67). `ctx` 가 `KernelContext` 아님 -> TypeError. `junction`(**필수 키워드**,
  2026-10-08 새 입력) 이 `JunctionSource` 아님 -> TypeError. θ = `check_theta(ctx.schema, ...)`.
- `junction` 이 새 입력인 이유: `KernelContext`(sizing)에 PDK 선언이 없다. 부르는 쪽이 S0 당 1회
  `JunctionSource.from_decls(read_pdk_decl(pdk 선언), read_pdk_decl(LUT 규칙 선언), ctx.lut.memo.lut)` 로 만든다(core 9.5·8.5).
  기본값을 두지 않는다(접합 용량 없는 평가 경로 = 옛 대기 경로를 남기지 않는다).
- passive_values = spec 값(`ctx.inputs.element_values` 중 S1 수동소자, 값 None 제외) ∪ θ `resistance` ∪ [r5] θ `capacitance`·
  `ss_resistance`(sizing `THETA_PASSIVE_KINDS`) ∪ [r5] **영점 상쇄 구조 규칙 값**: `ctx.schema.zero_cancel` 중 reason None 인 항목마다
  (resistor, 1/Σ_{c∈cells} gm_c), gm_c = 이 호출이 쓴 `ss_dev` 필드의 `SsDevice.gm`(7.2 -- gm 정의 하나). 이름이 S1 수동소자가
  아니거나 같은 소자 값이 두 출처면 ValueError(스키마가 S1·spec 에서 나오므로 정상 경로에서는 생기지 않는 계약 위반 표지). 정렬 tuple.
  어느 출처에도 없는 수동소자(spec mode pending 등)는 그대로 `missing` -> `passive_value_undeclared`(7.4 (2)).
- requests = constraints 의 (metric, view) 중 metric 이 None 아닌 것, 중복 제거·문서 순서. view_kind 가 있는 것만 `metrics_ss` 로.
- 순서 `ss_dev(sealed.snapshot, ctx.lut, junction)` -> (passive_values -- 구조 규칙이 gm 을 읽으므로 ss_dev 뒤) ->
  `metrics_ss(..., ss_requests, passive_values)` -> `metrics_dc(..., passive_values, tuple(counted_rails))`. `ss`·`dc` = 그 필드 값,
  `lineage` = 7.1.
- [r5] θ `capacitance`·`ss_resistance` 성분만 바꾼 θ' 로 `size_and_seal(ctx, θ', parent=res.lineage)` -> dc 블록 computes 0(sizing 7절
  r5), 이어 `ss_evaluate(그 결과 sealed, ctx, θ', ..., junction=같은 묶음)` -> `ss_dev` reuse(dc_op·junction 불변), `metrics_ss`·
  `metrics_dc` 각 computes 1(수동 값이 입력). 구조 규칙 값은 gm 의 함수라 dc_op 가 같으면 같다.
- 재사용: `ss_evaluate(res.lineage.sealed, 같은 인자)` -> 세 블록 computes 0·reuses 3, 결과 `snapshot is res.snapshot`.
  `size_and_seal(ctx, θ', parent=res.lineage)` 뒤 `ss_evaluate` -> dc_op 가 바뀌었으면 세 블록 재계산(바뀌지 않은 소자 LUT 조회는
  memo 적중), `recomputes_same_input` 0. 필드가 없는 lineage(예: `size_and_seal` 의 `ev.sealed`)에서 다시 부르면 다시 계산한다
  (core 6.2 -- 필드가 든 스냅샷에서만 재사용).

### 7.7 불변식 (test 가 확인할 성질)

| # | 성질 |
|---|---|
| S-1 | 손으로 만든 S2 스냅샷(권한표 `S2_WRITERS`, 각 열 writer = `writer_of`)에서 `metrics_ss` 의 β 루프 `pm_ss_deg` = 예 7 폐형식 92.292442776°(작성자 실측 92.29244277595588) |
| S-2 | 같은 소자의 포트 뷰 `gain_ss_db` = 20·log10(gm/gds) = 40 dB, sense 뷰 `rout_ss_ohm` = 1/gds = 1e5 Ω(실측 99999.99999999999) |
| S-3 | 한 요청 집합 안에서 β = 1 `pm_ss_deg` == 같은 포트 뷰 `parasitic_pm_ss_deg`(비트) |
| S-4 | 수동소자 값 하나를 빼면 모든 소신호 요청이 `passive_value_undeclared`(elements = 빠진 이름), 예외 0 |
| S-5 | pending 뷰 요청은 `view_pending`(decision = 뷰 decision), 다른 요청 값은 그대로 |
| S-6 | 재사용: 같은 입력 두 번 -> 두 번째 computes 0, 반환 스냅샷 `is` 같음 |
| S-7 | `ss_dev` 의 gm·gds·gmb·용량 = test 쪽이 `dc_op` 와 lut 공개 함수로 같은 식을 계산한 값 |
| S-8 | 넷 이름 전단사 뒤 metric 값 같음(I-7 확장 -- 노드 인덱스는 이름 정렬 위치뿐) |
| S-9 | `metrics_dc`: 2레일 회로 per_rail 합 = kcl_residual(≈ 0), `power_dc_w` = Σ V_k I_k |
| S-10 | `ss_evaluate` 에 `SealedSnapshot` 아닌 값(`DcEvaluation` 등) -> TypeError. [r5] `passive_theta` 인자 없음(6번째 위치 인자·`passive_theta` 키워드 -> TypeError) |
| S-11 | (DEC-91) `ss_dev` 의 cdb·csb = 같은 `dc_op`·`JunctionSource` 로 부른 `junction_caps`(8절) 값, `junction_model == JUNCTION_LUT_RULE`, `approximations` 에 `("junction", "pdk_bsim4_lut_rule_diffusion")` |
| S-12 | `JunctionSource` 의 한 필드(예 `temp_c`, 다른 PDK 선언의 params)만 바꾸면 `ss_dev` 재계산(computes +1), 같은 묶음이면 재사용(computes 0) -- `recomputes_same_input` 0 |
| S-13 | `ss_evaluate(..., junction=...)` 없이 부르면 TypeError(필수 키워드), `JunctionSource` 아닌 값 -> TypeError |
| S-14 | (9절) `ss_dev` 의 `lut_rel_tol` = 같은 소자 `dc_op.gm_id · dc_tol_v`(test 쪽이 S2 에 dc_tol_v 를 손으로 쓴 값), 열이 없거나 None 이면 None; `ss_dev.reads` 에 `("device", "dc_tol_v")` |
| S-15 | (9절) `metrics_ss` 의 값 있는 결과 `resolution` = test 쪽이 같은 회로·같은 ε 로 `lut_parameters`·`metric_resolutions` 를 부른 그 필드 value(비트); 한 MOS 라도 `lut_rel_tol` None 이면 모든 소신호 결과 `resolution` None, 값은 그대로 |
| S-16 | (9절) 손 S2 예 7(ε = 0.02 가 되도록 gm/ID·dc_tol_v 를 쓴 스냅샷)의 β 루프 `pm_ss_deg` 분해능 = 9.5 폐형식 0.0917466739° (상대 ≤ 1e-9), 같은 입력 두 번째 평가는 블록 재사용(분해능 재계산 0 -- S-6) |
| S-17 | [r5] (DEC-92, 옛 r5 번호 S-11, 병합 전 S-14) spec mode engine 커패시터는 θ `capacitance` 로 값이 들어가 소신호 요청이 값을 갖는다(같은 값을 spec 에 선언한 회로와 metric 값 같음) |
| S-18 | [r5] (DEC-92, 옛 r5 번호 S-12, 병합 전 S-15) 구조 규칙 저항(`zero_cancel` reason None) 값 = 1/Σ_{c∈cells} `ss_dev[c].gm` -- 같은 값을 spec 에 선언한 회로와 metric 값 같음 |
| S-19 | [r5] (DEC-92, 옛 r5 번호 S-13, 병합 전 S-16) θ `capacitance`·`ss_resistance` 만 바꾼 FD: dc 블록 computes 0, `ss_dev` reuse, `metrics_ss`·`metrics_dc` computes 1. `gain_ss_db`(용량 무관 DC 이득)는 **수치상** 불변(상대 차 ≤ 수 ulp -- 비트 동일 아님: `ss_resistance` 만 바꾼 경우 MNA 조립·풀이 순서 때문에 1 ulp 차가 실측됨) |

### 7.8 9회로 시연 (2026-10-08, master 798f29c 병합 뒤 LUT v2(`resolve_lut_location`), 작성자 측 실측 -- 정본 아님)

DC 점 = GB7 탐침(sizing CONTRACT 10절과 같은 θ 생성)에서 첫 '일관 DC 점'(봉인 7 만 undefined). 봉인 7 이 아직 master 에서
undefined 라 시연은 그 점을 **명시적으로** `SealedSnapshot(ev.snapshot, ev.report)` 로 감쌌다(엔진 규칙 변경 아님 -- DEC-67 게이트 유지, Q2).
master 그대로는 common_gate 만 일관 DC 점이 나온다(Q1 -- ng-seal7 에서 수정 중). 아래 값은 시연 전용 런타임 패치(VDS = 0 곡선 전체
미정 -> '목표 > 분지' +inf, 커밋 안 함)로 얻은 점이다. 보상 수동소자는 변형 A(값 없음) / B(시연 θ: engine 커패시터 1 pF, engine 저항
10 kΩ -- 탐침값, 설계값 아님).
- 근사 표시: 평가된 모든 회로 `(("cap", "lut_cgs_cgb"), ("gmb", "lut_gmbs_column"), ("junction", "pending_pdk_junction_params"))`
  (이 시연은 접합 배선 전 -- 배선 뒤 junction 항은 `"pdk_bsim4_lut_rule_diffusion"`, 9회로 재시연은 아직 안 함).
- 블록 계수: 평가된 7회로 모두 첫 평가 computes 1/1/1, 같은 θ(lineage) 두 번째 computes 0·reuses 3, FD(첫 current 성분 +1 %, parent =
  lineage) computes 1/1/1·`recomputes_same_input` 0.
- 변형 A: ngcc·two_stage·two_stage_sf 의 소신호 제약 `passive_value_undeclared`(Cm1·Cm2 / Cc·Rz / Cc), 전력·면적은 값.
- pushpull: LUT v2 VS 축으로 평가됨(옛 세트의 caps VS 실패 해소) -- `rout_ss_ohm` 2958.2 Ω(탐침 θ, `<= 1000` 판정 대상 값 아님).
- nmcnr: 탐침 점에 음의 `cgb`(−2.03e-16 F, LUT v2 부호 보존)가 있다 -- Q7 결정 (a) 뒤 부호 그대로 스탬프되어 평가됨(7회로 평가).
- current_reuse·sf_pushpull: 215 탐침 중 일관 DC 점 0(패치 유무 무관) -- ss 평가 못 함.

### 7.9 열린 항목·결정 (오케스트레이터 결정 2026-10-08)

| # | 항목 | 처리 |
|---|---|---|
| Q1 | lut r5/r6 + sizing r3: GB7 1변수 bisection 이 VDS = 0 끝점에서 `lut_curve_undefined` -- 8회로 탐침 통과 0 | **sizing 쪽 수정 중**(ng-seal7). 이 단계는 시연 런타임 패치로만 |
| Q2 | 봉인 7 대기 동안 `SealedSnapshot` 0 | **결정: DEC-67 타입 게이트 유지, 잠정 경로 없음**. 봉인 7 은 LUT r6 VDSAT 로 배선 중(ng-seal7) |
| Q3 | DEC-91 접합 용량 cdb·csb | **닫음(2026-10-08)**: core PDK 선언에 모델 카드 접합 파라미터(core 9.4), `junction_caps`(8절), `ss_dev` 배선(7.2, 레이아웃 전 LUT 생성 규칙 기하). 남은 것: 레이아웃 기하(MOD7 `ly.diffusion`)가 S2 에 생기면 그 기하로 바꾸는 경로 |
| Q4 | DEC-78 합산 레일 | **결정: `power_dc_w` = 선언된 모든 공급 레일 합(7.5), `supply_current_dc` 는 spec 선택 선언 `counted_rails` 가 생길 때까지 `counted_rails_undeclared`**. spec 형식 항목(authoring 몫)으로 기록 |
| Q5 | 보상 수동소자 θ(DEC-92) | **결정: sizing θ 스키마에 둔다**. [r5 해결 2026-10-08] sizing r5 가 θ `capacitance`·`ss_resistance` 와 `zero_cancel` 을 두어 `passive_theta` 인자를 지웠다(7.6). 4회로(ngcc·nmcnr·two_stage·two_stage_sf) 봉인 점에서 GBW·PM 측정됨 -- sizing CONTRACT 10.3. 어긋나게 된 기존 test: `tests/metrics/test_ss_evaluate.py::test_s10_passive_theta_conflicts_rejected[4]`·`::test_passive_theta_supplies_engine_value`(test 작성자가 S-10·S-14~S-16 으로 갱신 -- 병합 때 junction S-11~S-13·분해능 S-14~S-16 과 겹쳐 DEC-92 행을 S-17~S-19 로 옮김) |
| Q6 | 용량 LUT VS 축 밖 | **해소: LUT r6(VS 0~1.8 V)**. 축 밖이면 여전히 후보 실패(설계 2.4) |
| Q7 | LUT v2 용량은 부호 보존(음수 점 있음) -- 옛 1절 `MosSmallSignal` 용량 ≥ 0 과 충돌(nmcnr 실측 cgb −2.03e-16 F) | **결정 (a)**: 1절 용량을 '부호 있는 유한 실수'로(NaN·inf 만 거부), 부호 그대로 스탬프 -- SPICE 오라클과 같은 정의. 계약과 어긋나게 된 기존 test: `tests/metrics/test_records.py::test_mos_negative_value_error[cgs|cgd|cgb|cdb|csb]`(test 작성자가 계약에서 갱신, gm·gmb·gds 행은 그대로 유효) |

### 7.10 설계와 다르게 정한 점
1. **`ss.mna[view]`·`ss.freq[view]` 필드를 따로 두지 않았다**: `MnaSystem`·`SystemResponse` 는 numpy 배열이라 core 불변 값 규칙(core 2절)
   밖이고, mna·freq 의 입력이 전부 `ss_dev`·수동 값·뷰라 따로 두어도 재사용이 생기지 않는다(어느 `ss_dev` 가 바뀌어도 조립부터 다시 --
   설계 MOD6 2.2 '부분 스탬프 갱신은 근거 전 금지'와 같음). 조립·풀이·분석은 `metrics_ss` 블록 하나 안에서 계산 1회, 결과 metric 만 필드.
2. **`ss_dev` 는 소자별 필드 재사용이 아니라 블록 단위**(sizing 11절 2 와 같은 이유 -- core write 는 열 교체). 바뀌지 않은 소자의 LUT 조회는
   memo 적중이라 계산 0.
3. **전력·면적은 `metrics_dc` 별도 블록**: 소신호 값을 읽지 않으므로 ss 변경에 재계산되지 않게.
4. **S3 기록은 쓰지 않는다**: S3 는 search archive(MOD6 8절) 몫이고 아직 없다. 이 단계는 S2 필드까지.

---

## 8. 접합 용량 `junction_caps(params, geometry, v_db, v_sb, temp_c) -> JunctionCaps` (DEC-91 (2)(3), N3.16 'PDK 상수', 2026-10-08)

근거: DEC-91 (3) 값 정본 = PDK 모델 카드 접합 파라미터(core PDK 선언) + 봉인점 역바이어스 + 확산 기하. (2) 레이아웃 뒤 기하 = MOD7
`ly.diffusion[dev]`(Euler 행 공유 확산, finger 평균, `m = n_fingers`), 레이아웃 전 첫 사이징점 = LUT 생성 규칙. 오라클(spice_oracle
C22)이 같은 ad/as/pd/ps 를 넷리스트에 쓰고 ngspice 가 같은 식을 푼다 -- 엔진과 SPICE 가 같은 값을 내야 한다(아래 대조 표).
LUT `CDD`·`CSS` 열(− CGD·CGS)은 대조 test 전용(정본 아님). 이 파일은 입력 레코드만 보는 순수 함수다(graph·S2·LUT import 0).

### 8.1 입력 레코드 (frozen dataclass, 생성 때 검사 -- bool·비수 `TypeError`, 비유한 `ValueError`, 값은 float 로 정규화)
- `JunctionParams(cjs, cjd, cjsws, cjswd, cjswgs, cjswgd, mjs, mjd, mjsws, mjswd, mjswgs, mjswgd, pbs, pbd, pbsws, pbswd, pbswgs,
  pbswgd, tcj, tcjsw, tcjswg, tpb, tpbsw, tpbswg, tnom, permod, dwj)` -- 필드 이름 = BSIM4 모델 카드 이름(s = source 쪽, d = drain 쪽,
  sw = STI 측벽, swg = gate 측벽), SI(F/m²·F/m·V·1/K·V/K), `tnom` °C. 검사: `permod ∈ {0, 1}`(아니면 ValueError), cj*·mj* ≥ 0,
  pb* > 0(아니면 ValueError). `dwj` = 접합 유효 폭 축소량(Weffcj = finger_w − 2·dwj -- xw 포함, 부호 제한 없음).
  - `JunctionParams.from_pdk_decl(decl, kind)`: core `PdkDecl` 에서 `junction_<kind>_<필드>` 27개를 필드 순서로 `decl.values(...)`
    (없으면 core `SchemaRejectedError(pdk_quantity_undeclared)`). kind = 엔진 소자 kind(`"nmos"`·`"pmos"`) -- 이름 규약은 선언 파일 몫.
- `DiffusionGeometry(finger_w_m, ad_m2, as_m2, pd_m, ps_m, m)` -- finger 하나의 기하(m, m²) + finger 수 `m`(실수 허용, ngspice `m`).
  검사: `finger_w_m > 0`, `m > 0`, ad·as·pd·ps ≥ 0(아니면 ValueError).
  - `DiffusionGeometry.from_lut_rule(decl, finger_w_m, m)`: LUT 규칙 선언(`assets/sky130_lut_rule_decl.json`)의
    `lut_diffusion_ad_per_w_m`·`lut_diffusion_as_per_w_m`·`lut_diffusion_pd_extra_m`·`lut_diffusion_ps_extra_m` 으로
    `ad = ad_per_w·finger_w`, `as = as_per_w·finger_w`, `pd = finger_w + pd_extra`, `ps = finger_w + ps_extra`(C22 규칙과 같음).
- 결과 `JunctionCaps(cdb, csb)` -- 소자 전체(m 배) F.

### 8.2 식 (BSIM4 4.5 접합 용량 = ngspice BSIM4v5 와 같은 식, 실측 대조 8.4)
1. 형식: `params` 가 `JunctionParams` 아님·`geometry` 가 `DiffusionGeometry` 아님 -> TypeError. `v_db`·`v_sb`·`temp_c` 는 유한 실수
   (bool·비수 TypeError, 비유한 ValueError).
2. ΔT = temp_c − tnom. 영바이어스 단위 용량 온도 보정 `C(T) = C · max(0, 1 + tc·ΔT)`(바닥 tcj, STI 측벽 tcjsw, gate 측벽 tcjswg),
   내부 전위 `PB(T) = PB − tp·ΔT`(tpb, tpbsw, tpbswg). PB(T) ≤ 0 이면 ValueError(ngspice 는 0.01 V 로 자른다 -- 그 범위는 받지 않음).
3. Weffcj = finger_w − 2·dwj, ≤ 0 이면 ValueError.
4. 쪽마다(drain: ad·pd·cjd·…·v_db, source: as·ps·cjs·…·v_sb) 영바이어스 용량 세 항:
   바닥 `c0₁ = C_j(T)·A`, STI 측벽 `c0₂ = C_jsw(T)·P_eff`, gate 측벽 `c0₃ = C_jswg(T)·Weffcj`.
   `P_eff = P − Weffcj`(permod 1) 또는 `P`(permod 0). **P_eff 를 0 으로 자르지 않는다** -- P < Weffcj 면 c0₂ < 0(ngspice BSIM4v5 동작).
5. 항마다 바이어스 의존(v = 그 쪽 역바이어스, 양수 = 역방향):
   - v > 0: c0 > 0 이면 `c0·(1 + v/PB(T))^(−MJ)`, c0 ≤ 0 이면 0.
   - v ≤ 0(영·순바이어스): `c0·(1 − MJ·v/PB(T))`(선형 연장, 음수 c0 도 더함 -- v = 0 이면 c0).
6. `cdb = m · Σ drain 항`, `csb = m · Σ source 항`.
- 바이어스 부호: nmos v_db = V(d) − V(b), v_sb = V(s) − V(b); pmos 는 부호 반대(V(b) − V(d) 등). LUT 규약으로 `v_sb = VSB`,
  `v_db = VDS + VSB`(극성 정규화 크기).
- 알려진 불연속(ngspice 자체, 정정 2026-10-08 독립 test 실측 반영): P < Weffcj(STI 측벽 c0 < 0)이고 바이어스가 정확히 0 일 때
  ngspice 는 접합 전압의 수치 잡음 부호(실측 vbs = −2.2e-16 등)로 5의 어느 가지를 탈지 정해진다. **kind 와 무관**(nmos·pmos 모두
  생길 수 있다)하고 어느 가지가 될지는 넷리스트(전원 배치·노드 순서)·온도에 따라 달라진다 -- 작성자 실측은 pmos 한 경우(ngspice
  1.3830782127e-15 = 역방향 가지, 엔진 1.3001046135e-15 = v = 0 가지, 6.0 %)였고 nmos 같은 조건은 그 넷리스트에서 v = 0 가지로 일치했다.
  이 점에서 엔진(언제나 v = 0 가지)과 ngspice 의 차는 최대 |c0₂·m| 만큼이다. 레이아웃 기하가 permod 1 에서 `ps ≥ finger_w`(gate 변
  포함 둘레)를 지키면 생기지 않는다 -- MOD7 `ly.diffusion` 둘레 규약 확인 대상.
- 순바이어스·고온 편차(독립 test 실측): 85 °C 순바이어스에서 ngspice 와 상대 1.2e-8 차 -- sky130 모델의 `rbodymod` 바디 저항망 때문에
  내부 접합 노드 전압이 단자 전압과 아주 조금 달라서다(식 차이 아님). 역바이어스·27 °C 대조(8.4)에는 나타나지 않는다.

### 8.3 손계산 예 (test 작성용, 엔진과 독립인 폐형식)
- 공통 params: cj* = 1e-3, cjsw* = 1e-10, cjswg* = 2e-10, mj*·mjsw*·mjswg* = 0.5, pb* = 1, t* = 0, tnom = 27, permod = 1, dwj = 0;
  geometry(finger_w 1e-6, ad = as = 1e-12, pd = ps = 3e-6, m = 2), temp_c = 27.
  - v_db = 3: 영바이어스 합 = 1e-15 + 1e-10·2e-6 + 2e-10·1e-6 = 1.4e-15, 인수 (1 + 3)^(−0.5) = 0.5 -> cdb = 2·1.4e-15·0.5 = 1.4e-15.
  - v_sb = 0 -> csb = 2·1.4e-15 = 2.8e-15. v_sb = −0.5(순방향) -> 인수 1 + 0.5·0.5 = 1.25 -> csb = 3.5e-15.
  - permod = 0 이면 P_eff = 3e-6 -> finger 하나 영바이어스 합 1e-15 + 3e-16 + 2e-16 = 1.5e-15, v = 0 에서 cdb = csb = 3.0e-15.
  - tcj = 1e-3, tnom = 30, temp_c = 27 -> 바닥 항 1e-15·(1 − 3e-3), v = 0 에서 cdb = 2·(0.997e-15 + 4e-16) = 2.794e-15.
  - ps = 0.5e-6(< finger_w): c0₂ = 1e-10·(−0.5e-6) = −5e-17 -> v_sb = 3 이면 그 항 0(csb = 2·(1e-15 + 2e-16)·0.5 = 1.2e-15), v_sb = 0 이면
    csb = 2·(1e-15 − 5e-17 + 2e-16) = 2.3e-15.
- 값 위반: permod 0.5, pbs 0, finger_w 0, m 0, ad −1e-15, dwj = finger_w/2 -> ValueError. `JunctionParams(..., cjs=True)` -> TypeError.
- sky130 실데이터(PDK 선언 core 9.4): `JunctionParams.from_pdk_decl(decl, "nmos").cjs == 0.001339749237`, `.tnom == 30.0`,
  `.permod == 1.0`, `.dwj == 0.0`, `.cjd == .cjs`; `DiffusionGeometry.from_lut_rule(rule, 2e-6, 3)` -> ad = as = 1e-12(5e-7·2e-6),
  pd = ps = 4e-6(부동소수 2e-6 + 2.0000000000000003e-06).

### 8.4 ngspice 대조 (2026-10-08, 작성자 실측 -- ngspice-46 sky130 tt, TEMP 27 °C, 단일 소자 `X d g s b ... l w ad as pd ps m`,
`.op` 의 `@m.xdut.m<cell>[capbd]`/`[capbs]`, 출력 12자리)
- 대상 2 kind x 기하 3(LUT 규칙 finger 2 µm x 3, LUT 규칙 0.42 µm x 8, Euler 꼴 finger 1 µm·ad 0.29 pm²·as 0.145 pm²·pd 1.58 µm·
  ps 0.79 µm x 4) x L 3(0.15·0.5·4 µm -- 다른 모델 bin) x (v_db, v_sb) 5((0,0)·(0.3,0.1)·(0.9,0.4)·(1.8,1.0)·(−0.2,−0.1)) = 90점.
- 결과: 87점 상대 오차 ≤ 2.3e-11(출력 자릿수 한계), 나머지 3점 = 8.2 의 ngspice 불연속(pmos Euler 꼴 v_sb = 0, 6.0 %). L(bin)을
  바꿔도 ngspice 값 동일(접합 파라미터 bin 공통 확인). 독립 AC 대조(op 정보 아님): 같은 W·L·바이어스에서 drain 기하만 바꾼 두
  넷리스트의 `−Im(I(vd))/ω` 차 = 엔진 cdb 차, 상대 오차 ≤ 8.5e-11(nmos·pmos, v_db 0·0.5·1.2).
- 예(L 0.5 µm, LUT 규칙 finger 2 µm x 3): nmos (0.3, 0.1) cdb 4.8168933609e-15 / ngspice 4.8168933610e-15, csb 5.3305595669e-15;
  pmos (0.9, 0.4) cdb 3.0214419372e-15, csb 3.5374819305e-15(양쪽 같음).

### 8.5 소비자 호출 (배선 완료 2026-10-08 -- `ss_dev`, 7.2·7.6)
```python
from gmid_engine.core import BoundedLRU, read_pdk_decl
from gmid_engine.metrics import JunctionSource, ss_evaluate

memo = BoundedLRU(5)                                   # 두 선언 원본 5개(PDK 4 + LUT 규칙 1)
junction = JunctionSource.from_decls(
    read_pdk_decl(".../assets/sky130_pdk_decl.json", memo),
    read_pdk_decl(".../assets/sky130_lut_rule_decl.json", memo),
    ctx.lut.memo.lut)                                  # kind·온도는 LUT 에서 -- S0 당 1회
res = ss_evaluate(sealed, ctx, theta, constraints, counted_rails, junction=junction)
```
- `ss_dev` 안: `junction_caps(junction.params_of(op.kind), junction.pre_layout_geometry(w_m, op.W / w_m), op.vds + op.vsb, op.vsb,
  junction.temp_c)` -> `SsDevice.cdb·csb`, `junction_model = JUNCTION_LUT_RULE`. 옛 `JUNCTION_PENDING`(cdb = csb = 0) 경로·이름은 삭제.
- 레이아웃 뒤(아직 S2 에 없음): `ly.diffusion[dev]` 의 finger 평균 ad/as/pd/ps 와 n_fingers -> `DiffusionGeometry(fw, ad, as_, pd, ps, nf)`
  로 이 규칙 기하를 대체한다(그때 `junction_model` 새 값 -- MOD7/MOD8 배선 몫).
- 꺼진 소자·순바이어스: v_db·v_sb 가 음수(순방향)면 8.2-5 의 선형 연장 값이 나온다(봉인 6 이 tol_V 넘는 순바이어스를 이미 거부).

---

## 9. metric 분해능 `MetricResult.resolution` (계획 NFR-5 '격자 분해능', search S-19, 2026-10-08)

근거: 계획 NFR-5(최종 해 활성 제약의 여유 ≤ max(그 metric 의 격자 분해능, 측정된 모델 오차)), N3.13 3('격자 분해능 = spec 격자가 만드는
최소 metric 차, 계산'), DEC-72(모델 오차 = 별도 측정 선언값 -- 이 절 범위 밖), DEC-87·DEC-88, lut CONTRACT r6 5절(tol_V 정의·셀),
sizing CONTRACT 6절 tol 행(`dc_tol_v`), search CONTRACT(ng-mod6) 3.20·9절 S-19(소비자 -- 지금은 정규화 |목표|, 활성 판정 보류),
오케스트레이터 결정 2026-10-08(S-19 설계: LUT 조회 불확실성의 1차 민감도 전파와 MNA 수치 오차의 최댓값).

### 9.0 정의와 소비자
- metric q(값 있는 소신호 metric)의 **분해능 res(q) = max(lut(q), num(q))**, 단위 = q 의 단위(db·hz·deg·ohm). 정하지 못하면 None.
  - lut(q): q 를 계산하는 사슬(봉인 op → LUT 선형화 `ss_dev` → MNA → metric)에서 **격자가 만드는 값 불확실성은 LUT 보간뿐**이다(조립·풀이는
    결정적). 봉인점에서 LUT 보간 오차가 q 를 얼마나 흔들 수 있는가 = 이 점에서 q 로 구별할 수 있는 최소 차.
  - num(q): MNA 풀이의 사후 오차(반복 개선 1회 보정량 -- `solve_point`·`find_crossing` 과 같은 정의)를 같은 1차 식으로 q 에 옮긴 값.
- 소비자(search S-19): 소신호 제약 행 정규화 c = (값 − 목표)/res(>=) 또는 (목표 − 값)/res(<=), 활성 = c ≤ 1. NFR-5 의 max(res, 모델 오차)는
  모델 오차 선언값(DEC-72 `model_error_<metric>`)이 생기면 소비자가 합친다 -- metrics 는 res 만 낸다. **res = 0 도 값이다**(LUT 파라미터가
  없는 순수 수동 회로 + 정확한 DC 극한): 소비자는 모델 오차 바닥과 max 를 취하거나 0 을 '분해능 없음'으로 다룬다(0 으로 나누지 않는다).
- 전력·면적(`metrics_dc`)과 `metric_value` 단독 호출의 `resolution` 은 None(7.5·3.15).

### 9.1 소자 불확실성 ε 와 파라미터 Δp -- `lut_parameters(circuit, rel_tol) -> ParameterSet`
- **ε_d(`SsDevice.lut_rel_tol`) = (gm/ID)_d · tol_V,d**, tol_V,d = `device.dc_tol_v` = `tol_v_table(kind, w_key).at(L, vds, "id_equivalent")`
  (sizing 이 이미 쓴 셀, 봉인 2 와 같은 값), gm/ID = `dc_op.gm_id`. 유도: id_equivalent 셀 = |ln ID_LOO − ln ID|/(gm/ID)/2^p 의 최댓값(lut 5절)
  = 운영 보간이 ln ID 에 내는 오차를 VGS 로 환산한 값 -- 그 정의를 되돌리면 LUT 전류의 상대 불확실성 |ΔID/ID| = (gm/ID)·tol_V. 새 상수 0.
  - `gm_id_inverse` 지표는 쓰지 않는다: gm/ID 목표 → VGS 역산(층 0)의 오차라 봉인 op → ss 경로에 없다(DEC-88: 쓰기 소자 좌표 = ln IDu,
    봉인 2 가 id_equivalent 로 잰다).
- **LUT 파라미터** `LUT_PARAMETERS` = (gm, gmb, gds, cgs, cgd, cgb) -- `ss_dev` 가 LUT 조회로 만든 값(gm = ID·(gm/ID) 의 gm/ID, GDS·GMBS
  열, `caps` 의 CGS·CGD·CGB). **Δp = ε_d·|p|**(용량은 부호 있는 값이라 크기). 근거: 모든 LUT 열은 같은 격자·같은 보간 방법(DEC-87)에서
  나오고 W 로 정규화돼 있다; LOO 가 잰 것은 ln ID 열뿐이므로 다른 열의 오차를 따로 지어내지 않고 같은 상대 크기를 쓴다(일관 스케일).
  cdb·csb 는 PDK 접합 폐형식(8절, ngspice ≤ 2.3e-11)이라 LUT 불확실성이 없고, 수동소자 값은 선언·θ 그대로라 넣지 않는다.
- `ParameterSet` 필드: `params` = ((MOS 순번, 이름), ...) 값 ≠ 0 인 것만, (MOS 순번, `LUT_PARAMETERS` 순서) / `delta` (P,) /
  `rel_tol` = 정규화 tuple / 단위 스탬프 항목 `rows`·`cols`·`values`·`capacitive`·`owner`(파라미터 p 만 1 로 둔 `MosSmallSignal` 의
  `mos_stamps` 항목 -- 스탬프 식 정본 재사용) / `undetermined` = ε None 인 MOS 순번.
- 입력 규약: `circuit` 이 `SmallSignalCircuit` 아님·`rel_tol` 이 tuple 아님·길이 ≠ MOS 수·원소가 bool·비수 → TypeError, 원소 음수·비유한 →
  ValueError, None 허용(`undetermined`).

### 9.2 `response_sensitivity(system, parameters, omega) -> ResponseSensitivity`
- 행렬: ω > 0 은 A = G + jωC, b = BG + jω·BC. ω = 0 은 3.3 극한 식 그대로(용량 전용 노드 행 C_F·x = BC_F, `_helpers_dc.dc_limit_parts` --
  `solve_dc_limit` 과 같은 행렬). **LU 1회**로 x = A⁻¹b(모든 열), 반복 개선 1회 dx(`errors` = |S·dx|), 수반 y = A⁻ᵀSᵀ.
- ∂V/∂p = −yᵀ·(∂A_full/∂p)·x_full: 단위 스탬프 항목 중 행이 미지수 노드인 것만(고정 노드 행은 식이 아님), x_full = 미지수 해 + 고정 노드
  전압(그 열의 전압 구동 진폭, 교류접지 0 -- 구동 노드로 가는 스탬프의 우변 몫이 같은 식에 든다). 계수: ω > 0 은 G 항목 1, C 항목 jω;
  ω = 0 은 용량 전용 노드 행이면 C 항목만, 아니면 G 항목만(극한 식의 미분). 모든 항목을 한 번의 축약으로 더한다(파라미터마다 풀지 않는다).
- ∂V/∂ω(ω > 0) = yᵀ·j(BC − C·x); ω = 0 은 None.
- 결과 `values` (r, m) 복소, `errors` (r, m), `d_param` (P, r, m), `d_omega`. ω = 0 의 전하 주입 열은 값·민감도 NaN + `dc_charge_injection`
  (그 열만, 3.3 과 같음). 구조 결함 → `undefined` = `defects`(배열 None). 영 피벗 → 배열 None + `singular_mna`(numeric, ω > 0) /
  `singular_dc_limit`(structural, ω = 0).
- 입력: `MnaSystem`·`ParameterSet` 아님 → TypeError, ω 음수·비유한 → ValueError, 파라미터 항목 노드가 이 계의 미지수·고정 노드가 아님
  → ValueError(다른 회로의 ParameterSet -- 배선 결함). 절단 계(`cut_circuit`)는 MOS 단자가 그대로라 원래 회로의 ParameterSet 을 쓴다.
- 비용: 계·ω 하나에 LU 1회 + 삼각 풀이 (m + m + r) 열 + 항목 축약 1회. 재조립 0.

### 9.3 `metric_resolutions(analysis, source, parameters, memo=None) -> tuple[Resolution]`
- `analysis` = `LoopAnalysis`(source = 그 분석을 만든 인수 tuple) / `OutputResistance`·`ResponseRatio`(source = 그 `SystemResponse`). 다른
  형식·source 형식 불일치·`ParameterSet` 아님 → TypeError. `memo` = 부르는 쪽 dict((id(계), ω) → `ResponseSensitivity`), None 이면 호출 안.
- 결과: **값이 있는** 필드마다 `Resolution(quantity, value, lut, numeric)` -- LoopAnalysis 는 gain_db·ugf_hz·phase_margin_deg·gbw_hz 순서
  (값 None 인 필드는 빠진다), OutputResistance 는 rout_ohm, ResponseRatio 는 ratio_db(값 None 이면 빈 tuple).
- **결합 규칙(최악 선형)**: lut = Σ_p |∂q/∂p|·Δp -- 파라미터마다 오차 부호를 독립으로 둔다. 같은 소자의 열들이 같이 움직인다는 근거
  (상관)가 LOO 에 없으므로 상관을 가정하면 비 꼴 metric(gain ∝ gm/gds)에서 상쇄로 분해능을 과소평가한다. value = max(lut, numeric).
- 인수 곱 T = Π F_i: ∂T = Σ_i ∂F_i·Π_{k≠i}F_k, 사후 오차 e_T = Σ_i e_i·Π_{k≠i}|F_k|. `Factor` → V[행, 열]·그 민감도, `ProbeFactor` →
  `_helpers_probe.probe_value` 의 ∂T/∂V(Middlebrook 식 해석 미분, 3.17 '사후 오차'와 같은 ∂T/∂Z)로 ∂T = Σ ∂T/∂V ⊙ ∂V.
- 식(D = 20·log10(e) = 20/ln10 dB/neper -- `AMPLITUDE_DB_PER_DECADE` 에서, 새 상수 0):

  | 필드 | ∂q/∂p | numeric |
  |---|---|---|
  | gain_db | D·Re(∂T0/T0) (ω = 0) | D·e_T0/|T0| |
  | ugf_hz | ∂ω_u = −(∂|T|/∂p)/(∂|T|/∂ω) at ω_u = `ugf.omega`, /2π | δω_u/2π, δω_u = (\| \|T\| − level \| + e_T)/\|∂\|T\|/∂ω\| |
  | phase_margin_deg | Im(∂T/T) + Im((∂T/∂ω)/T)·∂ω_u (T(0) 실수 -- 위상 미분 0), 도 | 도(e_T/\|T\| + \|Im((∂T/∂ω)/T)\|·δω_u) |
  | gbw_hz | ρ = `f3db.level`/\|T0\|, ∂ω_3 = −(∂\|T3\| − ρ·∂\|T0\|)/(∂\|T3\|/∂ω), ∂gbw = (∂\|T0\|·ω_3 + \|T0\|·∂ω_3)/2π | (e_T0·ω_3 + \|T0\|·δω_3)/2π, δω_3 = (\| \|T3\| − level \| + e_T3 + ρ·e_T0)/\|∂\|T3\|/∂ω\| |
  | rout_ohm | rout·Re(∂V0)/V0 (ω = 0, 그 열·행) | rout·e/\|V0\| |
  | ratio_db | D·(Re(∂Vn/Vn) − Re(∂Vd/Vd)) | D·(e_n/\|Vn\| + e_d/\|Vd\|) |

  ∂|T|/∂p = Re(T̄·∂T)/|T|. 교차 양은 `find_crossing` 이 멈춘 ω(= `Crossing.omega`)에서 다시 푼다(같은 분해 방법 -- 같은 사후 오차).
- None 이 되는 경우(예외 아님): `parameters.undetermined` 가 비어 있지 않음(lut·value None, numeric 은 계산), 그 ω 풀이가 정의 안 됨·
  인수 값/민감도 비유한, ∂|T|/∂ω = 0(교차에서 기울기 없음), T(0) = 0 또는 V0·Vn·Vd = 0(로그·비 미분 불가) -- 그 필드 `Resolution(q, None)`.

### 9.4 배선과 캐시
- `ss_dev` 가 `lut_rel_tol` 을 쓰고(7.2), `metrics_ss` 가 호출마다 `lut_parameters` 1회·분석 열쇠마다 `metric_resolutions` 1회(memo 공유)로
  `MetricResult.resolution` 을 채운다(7.4). 블록 안 계산이라 **입력 버전이 같으면 블록 재사용으로 다시 계산하지 않는다**(S-6). LUT 를 다시
  조회하지 않는다(ε 는 S2 의 dc_tol_v·dc_op 에서).
- 정의 불가 결과(값 None)·pending·passive 누락 결과의 resolution 은 None.
- 공개 이름 추가: `LUT_PARAMETERS`, `ParameterSet`, `Resolution`, `ResponseSensitivity`, `lut_parameters`, `metric_resolutions`,
  `response_sensitivity`. `_helpers_probe.probe_value` 는 4-tuple(마지막 = ∂T/∂V 또는 None)로 바뀌었다(비공개, 호출부 2곳 갱신).
- 계약과 어긋나게 된 기존 test(작성자 몫, 수정 안 함): `tests/metrics/test_ss_types.py::test_field_names_and_order`(SsDevice 13칸),
  `tests/metrics/test_ss_linearize.py::test_block_declaration`(`ss_dev.reads` 에 dc_tol_v).

### 9.5 손계산 예 (엔진과 독립인 폐형식, test 작성용)
- **예 7 + ε = 0.02**(예: gm/ID = 10 S/A, tol_V = 2 mV): `lut_parameters(예 7 회로, (0.02,))` → `params` ((0, "gm"), (0, "gds"))(gmb·용량 0 은
  빠진다), `delta` (2e-5, 2e-7). β 루프 `probe_factor` → `analyze_loop` → `metric_resolutions(분석, (pf,), 그 ParameterSet)`.
  폐형식 T(s) = gm·β/(gds + s·Ceff), β = Cf/(Cf + Cs) = 0.25, Ceff = CL + Cf·Cs/(Cf + Cs) = 1.75 pF, T0 = gm·β/gds = 25,
  ω_u = √((gmβ)² − gds²)/Ceff:
  - gain_db: ∂/∂ln gm = D, ∂/∂ln gds = −D → lut = 2·D·ε = **0.3474355855 dB**.
  - ugf_hz: ω_u²·Ceff² = (gmβ)² − gds² → lut = ε·((gmβ)² + gds²)/(ω_u·Ceff²)/2π = UGF·ε·(T0² + 1)/(T0² − 1) = **455820.7769 Hz**.
  - phase_margin_deg(`pm_ss_deg`): PM = 180° − atan√(T0² − 1), ∂PM/∂ln T0 = −1/√(T0² − 1), |∂ln T0| ≤ 2ε → lut = 도(2ε/√(T0² − 1)) =
    **0.0917466739°**.
  - gbw_hz: 단일 극 → gbw = gm·β/(2π·Ceff)(gds 상쇄) → lut = ε·gbw = **454728.4088 Hz**.
  - numeric(작성자 실측): gain 1.2e-15 dB, ugf 2.1e-8 Hz, pm 2.9e-14°, gbw 1.5e-8 Hz -- 모두 value = lut.
- **예 2 rout + ε = 0.02**: `output_resistance(A 응답, 1)` = 1e5 Ω(노드 1 은 구동 고정 노드라 gm 무관) → lut = ε·rout = **2000 Ω**.
- **예 6 ratio**(MOS 없음): `params` = () → lut = 0.0, value = numeric(DC 사후 오차, 정확 해면 0.0).
- **미정**: `rel_tol` (None,) → `undetermined` (0,), 모든 필드 value·lut None, numeric 은 값.
- **수반 = 차분 대조**(작성자 실측 2026-10-08, 상대 h = 1e-6 중심 차분으로 파라미터마다 다시 조립·풀이): 예 7(gmb·cgs·cgd·음의 cgb 더한
  변형 포함), 예 3 Miller(두 MOS 에 cgs·cgd 추가)의 gain·ugf·gbw·pm 에서 Σ|Δq|·ε/h 와 lut 의 상대 차 ≤ 2.5e-9(차분 절단 오차 수준).

### 9.6 불변식 (test 가 확인할 성질)

| # | 성질 |
|---|---|
| R-1 | 예 7 + ε = 0.02 의 네 필드 lut = 9.5 폐형식(상대 ≤ 1e-9), value = lut(numeric ≪ lut) |
| R-2 | 수반 미분 = 중심 차분: 임의 파라미터 p 에 대해 test 쪽이 p 를 (1 ± h) 로 바꿔 `build_mna`·`solve_responses`·분석을 다시 부른 차분과 `response_sensitivity`·`metric_resolutions` 의 기울기가 같다(h 1e-6 에서 상대 ≤ 1e-6) |
| R-3 | lut 는 ε 에 선형(ε 두 배 → lut 두 배), 파라미터 부호와 무관(Σ|·|) -- MOS 하나만 ε 를 바꾸면 그 MOS 몫만 바뀐다 |
| R-4 | 한 MOS 라도 ε None → value·lut None, 예외 0 |
| R-5 | 값 None 인 필드는 결과에 없다(예 1: ugf·pm `dc_not_above_level` → gain·gbw 만) |
| R-6 | 노드 재번호(I-7) 뒤 분해능 같음(비트 아님 -- 같은 값 상대 ≤ 1e-12) |
| R-7 | `response_sensitivity` 의 ω = 0 값 = `solve_dc_limit` 값, ω > 0 값·오차 = `solve_point` 값·오차(같은 분해 방법) |
| R-8 | 다른 회로의 ParameterSet(계에 없는 노드) → ValueError, 형식 위반 TypeError |
| R-9 | 스탬프 함수 호출: `response_sensitivity`·`metric_resolutions` 동안 `mos_stamps`·`two_terminal_stamps`·`build_mna` 호출 0(조립 0 -- 단위 스탬프는 `lut_parameters` 에서 1회) |

### 9.7 실측 (2026-10-08, 작성자 측 시연 -- 정본 아님, LUT v2)
LUT v2(`resolve_lut_location`), sizing CONTRACT 10절 탐침 θ(seed 0, 회로당 215)에서 **첫 봉인 통과 점**(`DcEvaluation.sealed` 있음 -- 시연용
감싸기 없음), 관측 = 등록 소신호 metric 을 로더 기본 뷰(port·loop·sense)로 + spec 제약, engine 보상 수동소자는 시연 θ(1 pF / 10 kΩ, 7.8 과 같음 --
설계값 아님). 값은 탐침 θ 의 값이다(설계 판정 대상 아님 -- PM 음수 등). 9회로 중 7회로 평가(current_reuse·sf_pushpull 은 215 탐침 중 봉인 점 0).

| 회로 | 탐침 번째 | ε 범위 | gain dB ± res | UGF ± res(상대) | PM ° ± res | GBW res(상대) | rout ± res(상대) |
|---|---|---|---|---|---|---|---|
| common_gate_amplifier | 2 | 0.0068~0.0072 | 37.43 ± 0.120 | 3.671e9 ± 3.03e7 (0.82 %) | 90.77 ± 0.011 | 0.82 % | 78193 ± 548 (0.70 %) |
| folded_cascode | 8 | 0.0136~0.0157 | 76.10 ± 0.615 | 6.849e7 ± 1.62e6 (2.4 %) | 34.94 ± 1.54 | 2.9 % | 8.226e6 ± 3.74e5 (4.5 %) |
| ngcc_3stage_ff | 4 | 0.0099~0.0114 | 112.63 ± 0.799 | 5.345e7 ± 1.22e6 (2.3 %) | 218.34 ± 2.70 | 2.1 % | 79015 ± 846 (1.1 %) |
| nmcnr_amplifier | 23 | 0.0066~0.0224 | 115.31 ± 0.996 | 1.738e5 ± 8.57e3 (4.9 %) | −49.22 ± 2.03 | 3.5 % | 19477 ± 92 (0.47 %) |
| pushpull_follower_buffer | 50 | 0.0126~0.0304 | −3.65 ± 0.124 | 정의 불가(`dc_not_above_level`) -> None | 정의 불가 -> None | 5.0 % | 8728 ± 194 (2.2 %) |
| two_stage_ota | 6 | 0.0102~0.0109 | 58.84 ± 0.382 | 9.731e7 ± 1.91e6 (2.0 %) | 9.40 ± 1.02 | 2.5 % | 82266 ± 862 (1.0 %) |
| two_stage_ota_sf | 6 | 0.0104~0.0109 | 57.21 ± 0.413 | 7.742e7 ± 1.41e6 (1.8 %) | −15.42 ± 1.90 | 2.7 % | 685.2 ± 7.25 (1.06 %) |

- `pm_ss_deg`(loop 기본 뷰, 이 spec 들은 β = 1)와 `parasitic_pm_ss_deg` 는 값·분해능 모두 같다(같은 분석 열쇠).
- numeric/lut 비 최대 1.6e-12(folded gbw) -- 모든 점에서 분해능 = LUT 몫. ε 미정(dc_tol_v None) 소자 0.
- 시간(같은 점 새 lineage 5회 중앙값, 두 실행 -- 다른 agent 부하로 흔들림): `ss_evaluate` 첫 평가 17.6~61.0 ms / 30.2~82.3 ms 중 분해능
  (`lut_parameters` + `metric_resolutions`) 1.7~5.2 ms / 2.2~6.4 ms(6~10 %). 같은 lineage 두 번째 평가는 블록 재사용(`ss` 묶음 `is` 같음,
  분해능 재계산 0).

### 9.8 열린 항목
| # | 항목 | 처리 |
|---|---|---|
| R1 | 모델 오차(DEC-72)와의 max | 소비자(search S-19) 몫 -- 선언값이 생기면 max(res, model_error). metrics 는 res 만 |
| R2 | LUT 열별 LOO(gds·gmb·용량 열 자체의 보간 오차) | 없음 -- 지금은 ln ID 열 LOO 를 모든 LUT 열에 같은 상대 크기로 쓴다(9.1). 열별 LOO 표가 lut 에 생기면 Δp 만 바꾼다 |
| R3 | 파라미터 오차 상관 | 독립(최악 선형)으로 둔다. 상관 근거(같은 격자 점의 오차 부호 관계 측정)가 생기면 결합 규칙 재검토 |
| R4 | 레이아웃 기하 접합 용량 | 접합은 폐형식이라 이 절 대상 아님(8절) |

