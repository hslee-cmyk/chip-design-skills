# gmid_engine.metrics 동작 계약 (test 작성용) -- 1단계: 엔진 상태와 독립인 수치 핵심

- 대상: `gmid_engine.metrics.__all__`(이 단계 파일 23개, 아래 0절). test 는 `from gmid_engine.metrics import ...` 와
  `from gmid_engine.core import ...` 만 쓴다(`_` 이름 금지). test 배치(규칙 H): `gmid_engine/tests/metrics/test_<파일>.py`.
- 근거: `wt/_drafts/engine/design_mod1_lut_mod5_mna.md`(이하 DM) 3.1~3.4, 계획 N3.8(gain·PM U-48), DEC-25·53·66·67·68·
  78·79, DF-06·16·19·26·28·29·30·37, WP-03, 설계 `design_spec_format.md` 3.2(`metric_catalog`), coordinator 결정
  2026-10-07(용량 전용 노드 = 전하 보존 극한, 정의 불가 = 값으로 담기).
- 이번 범위 밖(다음 단계): `ss_linearize`(봉인 스냅샷 → 이 레코드), GB4 `achievability`, GB5 `compensation`, `ls_fields`,
  `@compute_block` 배선(S2 필드 `ss.mna`·`ss.freq`), `columns_current_check`, `area_layout_m2`. 이 단계 함수는 **입력
  레코드만 보는 순수 함수**이고 graph·S2·LUT 를 import 하지 않는다.

---

## 0. 파일·층·진입점

| 층 | 파일 | 진입점 | 내용 |
|---|---|---|---|
| 0 | `records.py` | (데이터) | 입력 레코드: `MosSmallSignal`, `Resistor`, `Capacitor`, `Excitation`, `Sense`, `SmallSignalCircuit`, `StampSet`, `RailBias`, `ChannelCurrent`, `CurrentSource`, `DcOperatingPoint`, `GateArea`, `PassiveArea` |
| 0 | `mna_types.py` | (데이터) | 결과 레코드: `Undefined`, `MnaSystem`, `Roots`, `DcLimit`, `SystemResponse`, `PointSolution`, `Factor`, `Crossing`, `LoopAnalysis`, `OutputResistance`, `ResponseRatio`, `SupplyCurrents`, `AreaSearch`, `MetricResult` |
| 0 | `_helpers_stamp.py` | (helper) | `admittance_pair` |
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
| 3 | `mna_solve.py` | `solve_responses` | 공유 격자 응답 |
| 3 | `_helpers_product.py` | (helper) | `product_at` |
| 4 | `crossing.py` | `find_crossing` | |T| = level 교차 |
| 4 | `phase_lag.py` | `phase_lag` | 누적 위상 지연 |
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
- 모든 값 필드는 생성 때 검사: 유한 실수, `MosSmallSignal` 의 gm·gmb·gds·용량 ≥ 0, `Resistor.ohm`·`Capacitor.farad` > 0
  (기본값 없음 -- `Resistor(a, b, None)` 은 `TypeError`, 0 은 `ValueError`).
- **MOS 소신호**: I(d→s) = gm(vg − vs) + gmb(vb − vs) + gds(vd − vs). NMOS·PMOS 같은 식(소신호 크기는 양수).
  용량 cgs(g–s), cgd(g–d), cgb(g–b), cdb(d–b), csb(s–b). bulk 는 `b` 인덱스(레일이면 교류접지 노드).
- **여기 열** `Excitation(name, voltages=((노드, V),…), currents=((노드, A),…))`: 전류는 노드로 들어가는 방향. 한 계의 모든 열에서
  전압 구동 노드는 고정 노드이고, 그 열에 없는 구동 노드는 0 V. 이름은 계 안에서 유일.
- **관측** `Sense(pos, neg=None)`: v(pos) − v(neg).
- **DC**: `ChannelCurrent(drain, source, amp)` = 소자 안 drain→source 전류(부호 있음). `CurrentSource(from_node, to_node, amp)` =
  from 에서 나와 to 로 들어가는 전류.

## 2. 예외 규약과 정의 불가 값

- **예외는 입력 계약 위반에만**: 형식 오류(`TypeError`), 값·뷰 정의 오류(`ValueError` -- 레코드 값, 여기 열 이름 중복,
  구동 노드가 교류접지와 겹침, 고정 노드에 전류 주입, 관측이 구동 안 된 고정 노드뿐, 격자 다른 인수 묶기, rout·ratio 열 조건,
  합산 레일 선언), 미등록 metric 이름(`KeyError`). 이것들은 값(사이징 점)과 무관한 배선·뷰 결함이다.
- **값에 따라 생기는 정의 불가는 예외가 아니라 값**: 결과 묶음의 해당 필드가 None 이고 `undefined` 에
  `Undefined(quantity, code, category, detail)` 가 있다. `metric_value(name, source)` 는 항상 `MetricResult(name, value, undefined)`
  를 돌려준다. MOD5 는 N3.14 분류를 하지 않는다 -- 판정 계층이 문맥으로 분류한다(아래 표는 권고 대응).

| code | category | 생기는 곳 | 판정 계층 권고 대응(탐색 전 구조 판정 / 탐색 중 평가) |
|---|---|---|---|
| `isolated_node` | structural | `build_mna`(`defects`) | STRUCTURE_UNRESOLVED / 후보 실패 `structure_inconsistent` |
| `singular_dc_limit` | structural | `solve_dc_limit` | 같음 |
| `dc_charge_injection` | definitional | `solve_dc_limit`(그 열만) | STRUCTURE_UNRESOLVED / 후보 실패 `structure_inconsistent` |
| `dc_not_above_level`, `no_crossing_above`, `dc_zero`, `den_zero`, `num_zero`, `operand_undefined` | definitional | 교차·비·이득 | STRUCTURE_UNRESOLVED / 제약 위반 후보 실패(margin null, N3.14 표의 해당 하위 클래스는 판정 계층이 확정) |
| `singular_mna`, `crossing_bracket_overflow`, `crossing_bound_violated`, `phase_jump_unresolved`, `zero_response_on_axis`, `response_not_finite`, `unrecorded_cause` | numeric | 풀이·이분·위상 | STRUCTURE_UNRESOLVED / NONCONVERGENT(후보 실패 클래스) |

## 3. 함수 계약

### 3.1 `mos_stamps(dev) -> StampSet`, `two_terminal_stamps(elem) -> StampSet`
- (행 노드, 열 노드, 값) tuple. KCL 행 = 노드에서 나가는 전류. MOS G 행: drain (d,d,gds)(d,g,gm)(d,b,gmb)(d,s,−(gm+gmb+gds)),
  source 는 부호 반대. 값 0 항목은 내지 않는다. 저항 = 1/R 의 2단자 4항목, 커패시터 = C 의 4항목. 다른 형식은 `TypeError`.

### 3.2 `build_mna(circuit, excitations, sense) -> MnaSystem`
- 소자마다 스탬프 함수를 **정확히 한 번** 부른다. 결과는 ω 와 무관한 실수 `G`·`C`(n×n), `BG`·`BC`(n×m), `sense_row`(n),
  `sense_direct`(m). 배열은 쓰기 금지. 미지수 = 소자·여기·관측에 나오는 노드 − 고정 노드(교류접지 ∪ 전압 구동), 오름차순.
- `defects`: 미지수 블록에서 G·C 의 그 행이 모두 0(KCL 식 없음) 또는 그 열이 모두 0 인 노드 → `isolated_node`(모든 ω 특이).
- `charge_nodes`: 전체 G 행(고정 노드 열 포함)이 0 인 미지수 노드의 미지수 번호 = 용량으로만 이어진 노드.

### 3.3 `solve_dc_limit(system) -> DcLimit` (ω → 0 극한, 전하 보존)
- (G + sC)x = BG + s·BC 에서 F = `charge_nodes` 행은 G_F = 0 이라 s(C_F x − BC_F) = BG_F. BG_F 는 그 노드 주입 전류뿐이다.
- BG_F = 0 인 열: F 행을 **C_F·x = BC_F**(전하 보존 -- 블록 C_cc x_c = −C_cr x_r 의 일반형, 구동 노드 결합은 BC_F 에 있다)로,
  나머지 행은 G_R·x = BG_R 로 쌓은 실수 행렬을 LU 1회로 모든 열에 대해 푼다. 이것은 극한 식 자체의 해다(상수·작은 ω 근사 없음).
- BG_F ≠ 0 인 열: 직류 전하 누적으로 극한 발산 → 그 열 NaN + `dc_charge_injection`. 쌓은 행렬이 특이면 모든 열 NaN +
  `singular_dc_limit`. `defects` 가 있으면 모든 열 NaN + 그 사유.
- **범위 한정**: 이 값은 소신호 전달의 ω → 0 극한이다. 용량 전용 노드의 **DC 동작점 전압**(바이어스)은 MOD5 몫이 아니다
  -- GB7 / spec 선언이 정한다. 여기서는 그 노드의 소신호 전하 보존만 쓴다.

### 3.4 `pencil_roots(system) -> Roots`
- `poles` = (G, −C) 유한 일반화 고유값, `zeros[j]` = 열 j 관측 전달함수의 유한 영점(증강 pencil). 무한 판정은 QZ 동차 좌표
  |β| ≤ 차원·eps·‖E‖_F(상수 없음). 정렬 (|s|, 실부, 허부). `defects` 가 있으면 빈 근. **격자 배치·상단 괄호 전용**.
- **원점 판정**(무한 판정과 같은 방식, 상수 없음): QZ 동차 좌표 (α, β) 에서 |α| ≤ 차원·eps·‖A‖_F 이면 그 고유값은 정확히
  0j 로 낸다(극점 pencil: A = G, 차원 n / 영점 pencil: 증강 A, 차원 n+1; eps = 배정밀도 기계 엡실론). 용량 전용 노드의 전하
  모드(원점 극점)가 반올림 잡음으로 작은 |s| 가 되어도 0 으로 판정된다. |s| = 0 은 격자 꺾임점·상단 괄호 상계에서 빠진다.

### 3.5 `omega_grid(roots_tuple) -> tuple`
- 0.0 + 양의 유한 |극점|·|영점| 꺾임점 + 인접 꺾임점 기하 중점, 오름차순·중복 없음. 꺾임점 없으면 `(0.0,)`.

### 3.6 `solve_responses(systems) -> tuple[SystemResponse]`
- 계마다 `pencil_roots` 1회, 모든 계 근의 합집합으로 **공유 격자** 1개. ω = 0 은 `solve_dc_limit`(LU 1회, 모든 열),
  ω > 0 은 (k,n,n) 묶음 풀이 1회(특이면 점마다 다시 풀어 특이 ω 만 NaN + `singular_mna`). 재스탬프 없음.
  `values[0]` = DC 극한, `dc` 속성 = `values[0].real`, `undefined` = 사유 모음.

### 3.7 `solve_point(system, omega) -> PointSolution`
- ω > 0: A = G + jωC 의 LU 1회로 모든 열 풀이 + 같은 분해로 반복 개선 1회, `errors[j]` = |sense_row·dx|. ω = 0: `solve_dc_limit`.
  영 피벗이면 NaN + `singular_mna`.

### 3.8 `find_crossing(factors, omegas, values, level, quantity) -> Crossing`
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
- **PM 정의(계획 N3.8, U-48)**: 선언된 되먹임 수동소자가 있으면 그 β 루프의 루프 이득 T = A·β → 인수 2개
  `(Factor(A 응답, 열), Factor(β 응답, 열))`, 없으면 β = 1 → 인수 1개. 기준이 T(0) 위상이라 관측 부호와 무관.
  루프 절단 위치(A·β 각 뷰의 정의)는 7a design 몫이다.

### 3.11 `output_resistance(response, column) -> OutputResistance`
- 열 조건(ValueError): 구동 진폭 전부 0, 전류는 관측 노드에만(단일: pos 에 I / 차동: pos +I, neg −I).
  `rout_ohm` = DC 극한 관측값 / I(부호 그대로). DC 극한이 정의 안 되면 None + 사유.

### 3.12 `response_ratio(response, num_column, den_column) -> ResponseRatio`
- `ratio_db` = 20·log10|H_num(0)/H_den(0)|, 같은 계의 두 열(같은 G·C·관측, 추가 분해 0). 분모·분자 0 은 `den_zero`·`num_zero`.

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
| `pm_ss_deg` | LoopAnalysis.phase_margin_deg(β 루프 인수) | deg | ss | loop | -- |
| `ratio_ss_db` | ResponseRatio.ratio_db | db | ss | ratio | -- |
| `rout_ss_ohm` | OutputResistance.rout_ohm | ohm | ss | output_port | -- |
| `supply_current_dc` | SupplyCurrents.supply_current_dc | amp | dc | -- | power |
| `power_dc_w` | SupplyCurrents.power_dc_w | w | dc | -- | -- |
| `area_search_m2` | AreaSearch.area_search_m2 | m2 | geom | -- | -- |

- `metric_catalog()` = {이름: MetricSignature} 읽기 전용(spec 로더 `metric_catalog` 인자).
- `metric_value`: 미등록 KeyError, 형식 다르면 TypeError, 그 외에는 `MetricResult`(값 None 이면 그 필드의 `Undefined` 들).

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

## 5. 손계산 예 (엔진과 독립인 폐형식으로 대조 가능)

모든 예는 노드 0 = 교류접지(소신호 접지). 진폭 1 V 구동. 아래 값은 2026-10-07 직접 실행에서 엔진과 손계산이 상대오차
≤ 6.3e-12 로 일치했다(최대는 Miller p1 의 고유값 반올림).

### 예 1 -- RC 저역통과
- `Resistor(1, 2, 1e3)`, `Capacitor(2, 0, 1e-9)`, `ac_ground=(0,)`, 여기 1 V at 1, `Sense(2)`. H = 1/(1 + sRC).
- 기대: `gain_ss_db` = 0, f_3dB = `gbw_ss_hz` = 1/(2πRC) = 159154.943 Hz. `ugf_ss_hz`·`pm_ss_deg` = 정의 안 됨
  (`dc_not_above_level`, |H(0)| = 1 은 1 을 넘지 않는다) -- `metric_value` 는 `MetricResult(value=None, undefined=…)`.

### 예 2 -- 단일 극 증폭기(CS) + β 되먹임
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

### 예 2c -- 순수 용량 분압 β (전하 보존 극한)
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

## 6. 열린 항목

| # | 항목 | 현재 처리 |
|---|---|---|
| M1 | PM 의 루프 절단 위치(A·β 각 뷰) | 7a design. 이 단계는 인수 곱 T 만 받는다. spec 쪽 loop·output_port 선언 view 는 그때까지 결정 대기 표지만 받는다(authoring SPEC_CONTRACT 7절 S1) |
| M3 | 정의 불가 사유 → N3.14 분류 | MOD5 는 값으로만 낸다(2절 표는 권고). 판정 계층이 확정 |
| M4 | `supply_current_dc` 단위 접미사(DEC-68: `_amp`) | 설계 문서·spec 설계 objective 표 이름 그대로 |
| M5 | `area_search_m2` 의 objective_axis | None(예산 대상은 판정 축 `area_layout_m2`) |
| M6 | `cap_model` 근사 표시(DF-28)·`verified_by` | MetricSignature 필드에 없음 -- ss_linearize 단계에서 결과 묶음에 싣는다 |
