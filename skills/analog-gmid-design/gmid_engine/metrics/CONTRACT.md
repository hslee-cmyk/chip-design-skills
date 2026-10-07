# gmid_engine.metrics 동작 계약 (test 작성용) -- 1단계: 엔진 상태와 독립인 수치 핵심

- 대상: `gmid_engine.metrics.__all__`(이 단계 파일 21개, 아래 0절). test 는 `from gmid_engine.metrics import ...` 와
  `from gmid_engine.core import ...` 만 쓴다(`_` 이름 금지). test 배치(규칙 H): `gmid_engine/tests/metrics/test_<파일>.py`.
- 근거: `wt/_drafts/engine/design_mod1_lut_mod5_mna.md`(이하 DM) 3.1~3.4, 계획 N3.8(gain·PM U-48), DEC-25·53·66·67·68·
  78·79, DF-06·16·19·26·28·30·37, WP-03, 설계 `design_spec_format.md` 3.2(`metric_catalog`).
- 이번 범위 밖(다음 단계): `ss_linearize`(봉인 스냅샷 → 이 레코드), GB4 `achievability`, GB5 `compensation`, `ls_fields`,
  `@compute_block` 배선(S2 필드 `ss.mna`·`ss.freq`), `ratio_ss_db`, `parasitic_pm_ss_deg`, `columns_current_check`,
  `area_layout_m2`. 이 단계 함수는 **입력 레코드만 보는 순수 함수**이고 graph·S2·LUT 를 import 하지 않는다.

---

## 0. 파일·층·진입점

| 층 | 파일 | 진입점 | 내용 |
|---|---|---|---|
| 0 | `records.py` | (데이터) | 입력 레코드: `MosSmallSignal`, `Resistor`, `Capacitor`, `Excitation`, `Sense`, `SmallSignalCircuit`, `StampSet`, `RailBias`, `ChannelCurrent`, `CurrentSource`, `DcOperatingPoint`, `GateArea`, `PassiveArea` |
| 0 | `mna_types.py` | (데이터) | 결과 레코드: `MnaSystem`, `Roots`, `SystemResponse`, `PointSolution`, `Factor`, `Crossing`, `LoopAnalysis`, `OutputResistance`, `SupplyCurrents`, `AreaSearch` |
| 0 | `_helpers_stamp.py` | (helper) | `admittance_pair` |
| 1 | `stamp_mos.py` | `mos_stamps` | MOS 소신호 스탬프 |
| 1 | `stamp_two_terminal.py` | `two_terminal_stamps` | R·C 스탬프 |
| 1 | `pencil_roots.py` | `pencil_roots` | 극점·영점 |
| 1 | `point_solve.py` | `solve_point` | ω 한 점 풀이 + 사후 오차 |
| 1 | `omega_grid.py` | `omega_grid` | ω 격자 |
| 1 | `supply.py` | `supply_currents` | 레일 전류·전력 |
| 1 | `area.py` | `area_search` | 탐색 축 면적 |
| 1 | `rout.py` | `output_resistance` | 출력 저항 |
| 1 | `registry.py` | `metric_registry` | 이름 → `RegisteredMetric` |
| 2 | `mna_build.py` | `build_mna` | 조립 1회 |
| 2 | `mna_solve.py` | `solve_responses` | 공유 격자 응답 |
| 2 | `_helpers_product.py` | (helper) | `product_at` |
| 2 | `catalog.py` | `metric_catalog` | {이름: MetricSignature} |
| 2 | `evaluate.py` | `metric_value` | 이름으로 값 읽기 |
| 3 | `crossing.py` | `find_crossing` | |T| = level 교차 |
| 3 | `phase_lag.py` | `phase_lag` | 누적 위상 지연 |
| 4 | `loop_analysis.py` | `analyze_loop` | gain·UGF·GBW·PM 한 번 계산 |

core 추가: `core/units.py`(데이터, `METRIC_UNITS`·`DOMAINS`·`AMPLITUDE_DB_PER_DECADE`), `core/metric_signature.py`(데이터,
`MetricSignature(unit, domain, view_kind=None, objective_axis=None)` -- `unit ∈ METRIC_UNITS`, `domain ∈ DOMAINS` 아니면 ValueError).

---

## 1. 입력 관례

- **노드 = 정수 인덱스**. 넷 이름 문자열을 노드로 주면 `TypeError`. 교류접지·레일은 이름이 아니라 선언된 인덱스 집합
  (`SmallSignalCircuit.ac_ground`, `DcOperatingPoint.rails`)으로 받는다. 같은 회로를 인덱스만 바꿔 번호 매겨도 metric 은
  같다(불변식 I-7).
- 모든 값 필드는 생성 때 검사: 유한 실수, `MosSmallSignal` 의 gm·gmb·gds·용량 ≥ 0, `Resistor.ohm`·`Capacitor.farad` > 0
  (기본값 없음 -- `Resistor(a, b, None)` 은 `TypeError`, 0 은 `ValueError`).
- **MOS 소신호**: I(d→s) = gm(vg − vs) + gmb(vb − vs) + gds(vd − vs). NMOS·PMOS 같은 식(소신호 크기는 양수).
  용량 cgs(g–s), cgd(g–d), cgb(g–b), cdb(d–b), csb(s–b). bulk 는 `b` 인덱스(레일이면 교류접지 노드).
- **여기 열** `Excitation(name, voltages=((노드, V),…), currents=((노드, A),…))`: 전류는 노드로 들어가는 방향. 한 계의 모든 열에서
  전압 구동 노드는 고정 노드이고, 그 열에 없는 구동 노드는 0 V. 이름은 계 안에서 유일.
- **관측** `Sense(pos, neg=None)`: v(pos) − v(neg).
- **DC**: `ChannelCurrent(drain, source, amp)` = 소자 안 drain→source 전류(부호 있음). `CurrentSource(from_node, to_node, amp)` =
  from 에서 나와 to 로 들어가는 전류.

## 2. 함수 계약

### 2.1 `mos_stamps(dev) -> StampSet`, `two_terminal_stamps(elem) -> StampSet`
- (행 노드, 열 노드, 값) tuple. KCL 행 = 노드에서 나가는 전류. MOS G 행: drain (d,d,gds)(d,g,gm)(d,b,gmb)(d,s,−(gm+gmb+gds)),
  source 는 부호 반대. 값 0 항목은 내지 않는다. 저항 = 1/R 의 2단자 4항목, 커패시터 = C 의 4항목.
- 다른 형식 입력은 `TypeError`(조용한 누락 없음).

### 2.2 `build_mna(circuit, excitations, sense) -> MnaSystem`
- 소자마다 스탬프 함수를 **정확히 한 번** 부른다. 결과는 ω 와 무관한 실수 `G`·`C`(n×n), `BG`·`BC`(n×m), `sense_row`(n),
  `sense_direct`(m). 배열은 쓰기 금지.
- 미지수 = 소자·여기·관측에 나오는 노드 − 고정 노드(교류접지 ∪ 전압 구동), 오름차순.
- 거부(`StructureUnresolvedError`, `record.detail["reason"]`): `excitation_name_duplicate`, `driven_node_is_ac_ground`,
  `current_injection_into_fixed_node`, `isolated_node`(미지수 블록의 G·C 행이 모두 0 또는 열이 모두 0), `sense_on_undriven_fixed_node`.
- `dc_floating`: 미지수 블록 G 행 또는 열이 0 인 노드(용량으로만 연결). 조립은 통과, DC 풀이가 거부.

### 2.3 `pencil_roots(system) -> Roots`
- `poles` = (G, −C) 유한 일반화 고유값, `zeros[j]` = 열 j 관측 전달함수의 유한 영점(증강 pencil). 무한 판정은 QZ 동차 좌표
  |β| ≤ 차원·eps·‖E‖_F(상수 없음). 정렬 (|s|, 실부, 허부). **격자 배치·상단 괄호 전용** -- metric 값은 실제 풀이로 잰다.

### 2.4 `omega_grid(roots_tuple) -> tuple`
- 0.0 + 양의 유한 |극점|·|영점| 꺾임점 + 인접 꺾임점 기하 중점, 오름차순·중복 없음. 꺾임점 없으면 `(0.0,)`.

### 2.5 `solve_responses(systems) -> tuple[SystemResponse]`
- 계마다 `pencil_roots` 1회, 모든 계 근의 합집합으로 **공유 격자** 1개. ω = 0 은 G 의 LU 1회로 모든 열, ω > 0 은 (k,n,n) 묶음
  풀이 1회. 재스탬프 없음. `values[0]` = DC(실수), `dc` 속성 = `values[0].real`.
- 거부: `dc_floating_node`(DC 경로 없는 노드), `singular_mna`(영 피벗, detail 에 ω).

### 2.6 `solve_point(system, omega) -> PointSolution`
- A = G + jωC 의 LU 1회로 모든 열 풀이 + 같은 분해로 반복 개선 1회, `errors[j]` = |sense_row·dx|(사후 오차).

### 2.7 `find_crossing(factors, omegas, values, level) -> Crossing`
- T = Π 인수. |T(0)| ≤ level 이면 `omega=None, reason="dc_not_above_level"`.
- 격자에서 처음 |T| ≤ level 이 되는 칸을 괄호로. 격자 끝까지 > level 이면 상계 |K|·Π(ω+|z|)/Π(ω−|p|)(ω > max|p|)로 두 배씩
  올려 상단 괄호를 유도하고 실제 풀이로 확인(어긋나면 `NonconvergentError`, 부동소수 넘침도). 극점 수 < 영점 수 또는 같고
  |K| ≥ level 이면 `reason="no_crossing_above"`.
- 이분: lo > 0 기하 중점, lo = 0 산술 중점. 정지 = 중점이 끝점과 같은 부동소수 또는 | |T| − level | ≤ 사후 오차.

### 2.8 `phase_lag(factors, omegas, values, omega_end, value_end) -> float`
- T(0) 대비 누적 지연(rad, 지연 양수). 칸마다 arg(T_k/T_{k−1}), |Δφ| ≥ π/2 면 중점을 실제로 풀어 세분. 세분 불가(끝점 인접)·T = 0
  표본은 `NonconvergentError`.

### 2.9 `analyze_loop(factors) -> LoopAnalysis`
- 인수는 같은 `solve_responses` 결과여야 한다(격자 다르면 ValueError).
- `gain_ss_db` = 20·log10|T(0)|, `ugf_ss_hz` = |T| = 1 교차 ω/2π, `gbw_ss_hz` = |T(0)|·(|T| = |T(0)|/√2 교차)/2π,
  `gbw_ugf_gap_hz` = gbw − ugf, `pm_ss_deg` = 180° − `phase_lag`(UGF 까지).
- **PM 정의(계획 N3.8, U-48)**: 선언된 되먹임 수동소자가 있으면 그 β 루프의 루프 이득 T = A·β → 인수 2개
  `(Factor(A 응답, 열), Factor(β 응답, 열))`, 없으면 β = 1 → 인수 1개. 기준이 T(0) 위상이라 반전/비반전 관측 부호와 무관.
  루프를 어디서 끊는가(A·β 각 뷰의 정의)는 7a design 몫이다 -- 이 함수는 인수 곱만 받는다.
- 값이 정의되지 않으면 None, `undefined` 에 (metric, 사유).

### 2.10 `output_resistance(response, column) -> OutputResistance`
- 열 조건: 구동 진폭 전부 0, 전류는 관측 노드에만(단일: pos 에 I / 차동: pos +I, neg −I). `rout_ss_ohm` = DC 관측값 / I(부호 그대로).
  어기면 ValueError. 추가 분해 없음(`solve_responses` 의 DC 해).

### 2.11 `supply_currents(op, counted_rails) -> SupplyCurrents`
- I_k(레일 k → 회로) = 채널(drain=k: +i, source=k: −i) + 저항((V_k − V_other)/R) + 이상 전류원(from=k: +amp, to=k: −amp).
- `supply_current_dc` = Σ_{k∈counted_rails} I_k(DEC-78 '선언된 레일 기준 합', 기본값 없음 -- 빈 선언·레일 밖·중복은 ValueError),
  `power_dc_w` = Σ_k V_k I_k, `kcl_residual_amp` = Σ_k I_k. 레일 이름 기본값 없음.
- 불변식(IC11): 모든 레일·노드 전압을 Δ 옮기면 `power_dc_w` 변화 = Δ·`kcl_residual_amp`, `supply_current_dc` 불변.

### 2.12 `area_search(gates, passives) -> AreaSearch`
- `area_search_m2` = Σ W·L + Σ(값 × 단위 면적, 선언된 것만). 미선언 수동소자 label → `passive_area_undeclared`(정렬).

### 2.13 `metric_registry()`, `metric_catalog()`, `metric_value(name, source)`
- 등록 8개(이름 정렬): `area_search_m2`(m2, dc), `gain_ss_db`(db, ss, transfer), `gbw_ss_hz`(hz, ss, transfer),
  `pm_ss_deg`(deg, ss, loop), `power_dc_w`(w, dc), `rout_ss_ohm`(ohm, ss, output_port), `supply_current_dc`(amp, dc, 목적 축 power),
  `ugf_ss_hz`(hz, ss, transfer). 항목 = `RegisteredMetric(signature, source_type, field)` -- metric 은 결과 묶음의 필드다.
- `metric_catalog()` = {이름: MetricSignature} 읽기 전용(spec 로더 `metric_catalog` 인자로 그대로 넘긴다).
- `metric_value`: 미등록 이름 KeyError, 묶음 형식 다르면 TypeError, 값 None 이면 `StructureUnresolvedError`
  (detail `reason="metric_undefined"`, `metric`, `cause`).

## 3. 불변식 (test 가 확인할 성질)

| # | 성질 |
|---|---|
| I-1 | 조립 1회: `solve_responses`·`analyze_loop`·`output_resistance` 동안 스탬프 함수 추가 호출 0(소자 수 = 호출 수) |
| I-2 | 같은 `SystemResponse` 를 여러 metric 이 공유: gain·UGF·GBW·PM 은 `analyze_loop` 1회의 필드, rout 는 같은 DC 해 |
| I-3 | 결정론: 같은 입력 두 번 → 격자·metric 비트 동일 |
| I-4 | gmb: source follower 이득 = gm/(gm+gmb+gds+GL). gmb = 0 으로 두면 값이 달라진다(옛 엔진 gmb 0건 결함 red) |
| I-5 | cgd(또는 Miller C) 스탬프가 극점을 분리시킨다(아래 예 3의 p1·p2) |
| I-6 | 저항 값 없는 레코드는 생성 단계에서 거부(1e9 기본값 없음) |
| I-7 | 노드 재번호 불변: 인덱스만 바꾼 같은 회로에서 metric 동일(이름 리터럴 0) |
| I-8 | 레일 원점 이동 불변(2.11) |
| I-9 | 엔진 소스에 숫자 리터럴·회로 이름 0(구조 test D·E) -- dB 계수는 `core/units.py` |

## 4. 손계산 예 (엔진과 독립인 폐형식으로 대조 가능)

모든 예는 노드 0 = 교류접지(소신호 접지). 진폭 1 V 구동.

### 예 1 -- RC 저역통과
- 회로: `Resistor(1, 2, 1e3)`, `Capacitor(2, 0, 1e-9)`, `ac_ground=(0,)`, 여기 `voltages=((1, 1.0),)`, `Sense(2)`.
- 폐형식: H = 1/(1 + sRC), ω_p = 1/RC = 1e6 rad/s.
- 기대: `gain_ss_db` = 0, 극점 = −1e6, 격자 = (0, 1e6), f_3dB = 1/(2πRC) = 159154.943 Hz, `gbw_ss_hz` = 159154.943 Hz,
  `ugf_ss_hz`·`pm_ss_deg` = 정의 안 됨(`dc_not_above_level` -- |H(0)| = 1 은 1 을 넘지 않는다), `metric_value("ugf_ss_hz", …)` 는
  `StructureUnresolvedError`.

### 예 2 -- 단일 극 증폭기(CS) + β 되먹임
- A 계: `MosSmallSignal(d=2, g=1, s=0, b=0, gm=1e-3, gmb=0, gds=1e-5)`, `Capacitor(2, 0, 1e-12)`, 열 `vin`(1 V at 1) 과
  `iout`(1 A 주입 at 2), `Sense(2)`. β 계: `Resistor(2, 3, 30e3)`, `Resistor(3, 0, 10e3)`, 열 `vfb`(1 V at 2), `Sense(3)`.
  둘을 **한 번의** `solve_responses((A, β))` 로 푼다(공유 격자).
- 폐형식: A(s) = −gm·ro/(1 + s·ro·CL), ro = 1/gds = 100 kΩ, A0 = −100, ω_p = 1e7 rad/s. β = Rs/(Rf+Rs) = 0.25.
- β = 1(인수 1개): `gain_ss_db` = 40, UGF = ω_p·√(A0² − 1)/2π = 159146985.146 Hz, GBW = |A0|·ω_p/2π = 159154943.092 Hz,
  PM = 180° − atan(√(A0² − 1)) = 90.5729673449°.
- β = 0.25(인수 2개): |T0| = 25 → `gain_ss_db` = 27.9588001734, UGF = ω_p·√(624)/2π = 39756892.0418 Hz,
  PM = 180° − atan(√624) = 92.292442776°, GBW = 25·ω_p/2π = 39788735.773 Hz.
- `output_resistance(A 응답, 1)` → `rout_ss_ohm` = ro = 100000 Ω.

### 예 2b -- gmb 가 들어간 source follower
- `MosSmallSignal(d=9, g=1, s=2, b=0, gm=1e-3, gmb=2e-4, gds=1e-5)`, `Resistor(2, 0, 1e4)`, `ac_ground=(0, 9)`, `Sense(2)`.
- 폐형식: A = gm/(gm + gmb + gds + 1/RL) = 1e-3/1.31e-3 = 0.763358779. gmb = 0 이면 0.900900901.

### 예 3 -- 2극 Miller
- `M1(d=2, g=1, s=0, b=0, gm1=1e-4, gds=1e-6)`, `M2(d=3, g=2, s=0, b=0, gm2=1e-3, gds=1e-5)`, `C1 = Capacitor(2, 0, 0.1e-12)`,
  `CL = Capacitor(3, 0, 1e-12)`, `Cc = Capacitor(2, 3, 0.5e-12)`, 여기 1 V at 1, `Sense(3)`.
- 폐형식(R1 = 1/g1, R2 = 1/g2): H(s) = gm1gm2R1R2(1 − sCc/gm2)/(1 + a1 s + a2 s²),
  a1 = R1(C1+Cc) + R2(CL+Cc) + gm2R1R2Cc = 5.075e-5, a2 = R1R2(C1CL + C1Cc + CLCc) = 6.5e-14.
- 기대: `gain_ss_db` = 80, 극점 |p1| = 19704.9308 rad/s, |p2| = 780749525.838 rad/s, 영점 = +gm2/Cc = 2e9 rad/s(우반면),
  UGF = 30592376.7006 Hz, GBW = 31361371.396 Hz, PM = 70.6851677849°(폐형식 H 를 조밀 격자 언랩으로 독립 계산한 값).
  근사식 대조: UGF ≈ gm1/(2πCc) = 31.83 MHz, PM ≈ 90° − atan(ω_u/p2) − atan(ω_u/z) = 69.92°.

### 예 4 -- 레일 전류·전력
- 레일 10 = 1.8 V, 레일 0 = 0 V, `node_v=((6, 0.8),)`. 채널 (5→0, 10 µA), (5→10, −10 µA: PMOS 부하), (7→0, 5 µA),
  저항 10–6 100 kΩ, 6–0 80 kΩ, 이상원 10→7 5 µA, `counted_rails=(10,)`.
- 기대: I_10 = 10 + 10 + 5 = 25 µA, I_0 = −25 µA, `supply_current_dc` = 25 µA, `power_dc_w` = 45 µW, 잔차 0.
  모든 전압 +1 V 이동 후에도 `power_dc_w` = 45 µW.

### 예 5 -- 면적
- `GateArea(10e-6, 0.5e-6)`, `GateArea(4e-6, 1e-6)`, `PassiveArea("cc", 0.5e-12, 5e2)`(2 fF/µm² 에 해당하는 m²/F),
  `PassiveArea("rz", 5e3, None)`.
- 기대: `area_search_m2` = 5e-12 + 4e-12 + 2.5e-10 = 2.59e-10 m², `passive_area_undeclared` = ("rz",).

## 5. 열린 항목 (이 단계가 정하지 않은 것)

| # | 항목 | 현재 처리 |
|---|---|---|
| M1 | PM 의 루프 절단 위치(A·β 각 뷰) | 7a design. 이 단계는 인수 곱 T 만 받는다 |
| M2 | 용량만으로 이어진 노드(스위치드 커패시터 β 망, 파일럿 Cf·Cs)의 DC 값 | `dc_floating_node` 로 거부(lim ω→0 처리 미정) -- β = Cf/(Cf+Cs) 같은 용량 분압 루프는 지금 풀 수 없다 |
| M3 | 교차가 없을 때 실패 클래스 | metric 읽기에서 `StructureUnresolvedError(metric_undefined)`. 탐색 중이면 후보 실패여야 할 수 있음(N3.14 분류 확정 필요) |
| M4 | `supply_current_dc` 단위 접미사(DEC-68: `_amp`) | 설계 문서·spec 설계 objective 표 이름 그대로. 바꾸면 두 설계와 함께 |
| M5 | `area_search_m2` 의 objective_axis | None(예산 대상은 판정 축 `area_layout_m2`, spec 설계 1.x `objective`) |
| M6 | `cap_model` 근사 표시(DF-28)·`verified_by` | MetricSignature 필드에 없음 -- ss_linearize 단계에서 결과 묶음에 싣는다 |
