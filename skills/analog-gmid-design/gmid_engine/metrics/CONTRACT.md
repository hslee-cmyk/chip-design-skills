# gmid_engine.metrics 동작 계약 (test 작성용) -- 1단계: 엔진 상태와 독립인 수치 핵심

- 대상: `gmid_engine.metrics.__all__`(이 단계 파일 27개 + 접합 용량 `junction_cap.py`(8절), 아래 0절). test 는 `from gmid_engine.metrics import ...` 와
  `from gmid_engine.core import ...` 만 쓴다(`_` 이름 금지). test 배치(규칙 H): `gmid_engine/tests/metrics/test_<파일>.py`.
- 근거: `wt/_drafts/engine/design_mod1_lut_mod5_mna.md`(이하 DM) 3.1~3.4, 계획 N3.8(gain·PM U-48), DEC-25·53·66·67·68·
  78·79, DF-06·16·19·26·28·29·30·37, WP-03, 설계 `design_spec_format.md` 3.2(`metric_catalog`), coordinator 결정
  2026-10-07(용량 전용 노드 = 전하 보존 극한, 정의 불가 = 값으로 담기), `wt/_drafts/engine/design_7a_loop_output_views.md`
  (이하 7a, 루프 뷰·출력 포트 뷰 -- 4.1 변경 목록), 오케스트레이터 결정 2026-10-07(7a Q3: 음의 rout = 정의 불가).
- 이번 범위 밖(다음 단계): `ss_linearize`(봉인 스냅샷 → 이 레코드 -- 7a 배선 지점: spec `ViewDecl`(mode port·loop·sense)을
  계 레코드로 사상한다. 소자 이름 → 원소 인덱스·`LoopCut`, 넷 → 노드 인덱스, 고정 노드 = 레일 ∪ gate 전용 미구동 넷 ∪
  절단 안 된 입력 포트(7a 2.2 L4), 루프 계와 포트 전달 계를 한 번의 `solve_responses` 로), GB4 `achievability`, GB5 `compensation`, `ls_fields`,
  `@compute_block` 배선(S2 필드 `ss.mna`·`ss.freq`), `columns_current_check`, `area_layout_m2`. 이 단계 함수는 **입력
  레코드만 보는 순수 함수**이고 graph·S2·LUT 를 import 하지 않는다.

---

## 0. 파일·층·진입점

| 층 | 파일 | 진입점 | 내용 |
|---|---|---|---|
| 0 | `records.py` | (데이터) | 입력 레코드: `MosSmallSignal`, `Resistor`, `Capacitor`, `Excitation`, `Sense`, `SmallSignalCircuit`, `StampSet`, `LoopCut`, `RailBias`, `ChannelCurrent`, `CurrentSource`, `DcOperatingPoint`, `GateArea`, `PassiveArea` |
| 0 | `mna_types.py` | (데이터) | 결과 레코드: `Undefined`, `MnaSystem`, `Roots`, `DcLimit`, `SystemResponse`, `PointSolution`, `Factor`, `ProbeFactor`, `CutCircuit`, `Crossing`, `LoopAnalysis`, `OutputResistance`, `ResponseRatio`, `SupplyCurrents`, `AreaSearch`, `MetricResult`. **인수 공통 규약**(`Factor`·`ProbeFactor`): 속성 `response`(공유 격자), `samples`(격자 위 값), `poles`·`zeros`(상단 괄호용 근), `undefined`(격자 표본 사유); 격자 밖 한 점은 `PointSolution` → (복소값, 사후 오차, 사유)(`_helpers_product.product_at`) |
| 0 | `_helpers_stamp.py` | (helper) | `admittance_pair` |
| 0 | `_helpers_pencil.py` | (helper) | `finite_eigs`(pencil 유한 고유값, `pencil_roots`·`probe_loop` 공용) |
| 0 | `junction_cap.py` | `junction_caps` | 접합 용량 cdb·csb(BSIM4, DEC-91) + 입력 레코드 `JunctionParams`·`DiffusionGeometry`, 결과 `JunctionCaps` (8절) |
| 1 | `_helpers_probe.py` | (helper) | `probe_value`(Middlebrook T 한 점 평가·사후 오차, `probe_loop`·`_helpers_product` 공용) |
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
- 모든 값 필드는 생성 때 검사: 유한 실수, `MosSmallSignal` 의 gm·gmb·gds·용량 ≥ 0, `Resistor.ohm`·`Capacitor.farad` > 0
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

## 6. 열린 항목

| # | 항목 | 현재 처리 |
|---|---|---|
| M1 | PM 의 루프 절단 위치(A·β 각 뷰) | **닫음**(2026-10-07) -- 7a design: β 루프 = 절단 회로 `ProbeFactor`(Middlebrook), β = 1 = 포트 `Factor`, 인수 2개 곱은 정의 아님(3.10·3.16·3.17). spec 쪽은 authoring SPEC_CONTRACT 2절·3절(S1 닫음) |
| M7 | 섞인 절단(전도 노드와 용량 전용 노드가 함께인 절단)의 ω → 0 극한 | 정의 불가 값 `loop_cut_mixed_charge`(로랑 전개 다음 차수가 필요). 9회로 선언에는 없다 -- 쓰는 회로가 생기면 확장 |
| M3 | 정의 불가 사유 → N3.14 분류 | MOD5 는 값으로만 낸다(2절 표는 권고). 판정 계층이 확정 |
| M4 | `supply_current_dc` 단위 접미사(DEC-68: `_amp`) | 설계 문서·spec 설계 objective 표 이름 그대로 |
| M5 | `area_search_m2` 의 objective_axis | None(예산 대상은 판정 축 `area_layout_m2`) |
| M6 | `cap_model` 근사 표시(DF-28)·`verified_by` | MetricSignature 필드에 없음 -- ss_linearize 단계에서 결과 묶음에 싣는다 |

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
- 알려진 불연속(ngspice 자체): P < Weffcj 이고 바이어스가 정확히 0 일 때 ngspice 는 수치 잡음(실측 vbs = −2.2e-16)으로 5의 어느
  가지를 탈지 정해진다(pmos 실측: ngspice 1.3830782127e-15 = 역방향 가지, 엔진 1.3001046135e-15 = v = 0 가지, 6.0 %). 레이아웃
  기하가 permod 1 에서 `ps ≥ finger_w`(gate 변 포함 둘레)를 지키면 생기지 않는다 -- MOD7 `ly.diffusion` 둘레 규약 확인 대상.

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

### 8.5 소비자 호출 (ss_linearize `ss_dev` 배선 -- ng-sslin 담당, 이 브랜치는 배선하지 않는다)
```python
from gmid_engine.core import BoundedLRU, read_pdk_decl
from gmid_engine.metrics import DiffusionGeometry, JunctionParams, junction_caps

pdk = read_pdk_decl(pdk_decl_path, memo)          # assets/sky130_pdk_decl.json -- 부르는 쪽 BoundedLRU(원본 수 이상)
lut_rule = read_pdk_decl(lut_rule_decl_path, memo)  # assets/sky130_lut_rule_decl.json
params = JunctionParams.from_pdk_decl(pdk, op.kind)  # kind 마다 1회(블록 밖 또는 ctx 에 캐시)
temp_c = dict(lut.provenance.cap_conditions)["temp_c"]   # LUT 측정 온도 = SPICE 온도
# 레이아웃 전(첫 사이징점): finger_w = 슬라이스 폭 w_m(op.w_key), m = op.W / w_m
geometry = DiffusionGeometry.from_lut_rule(lut_rule, w_m, op.W / w_m)
# 레이아웃 뒤: ly.diffusion[dev] 의 finger 평균 ad/as/pd/ps 와 n_fingers -> DiffusionGeometry(fw, ad, as_, pd, ps, nf)
jc = junction_caps(params, geometry, op.vds + op.vsb, op.vsb, temp_c)
SsDevice(..., cdb=jc.cdb, csb=jc.csb, junction_model=<"pdk_bsim4_lut_rule" 또는 "pdk_bsim4_layout">)
```
- `JUNCTION_PENDING` 은 이 호출로 대체한다(만들면 배선 -- cdb = csb = 0 경로 삭제). 블록 입력 버전에 PDK 선언 sha256·LUT 규칙 sha256
  (`PdkDecl.decl_sha256`·`sources`)이 들어가야 같은 입력 재계산 0·선언이 바뀌면 재계산이 된다(extras 로 `params`·`geometry` 를 넘기면
  frozen dataclass 라 `fp_of` 가 값으로 지문한다).
- 꺼진 소자·순바이어스: v_db·v_sb 가 음수(순방향)면 8.2-5 의 선형 연장 값이 나온다(봉인 6 이 tol_V 넘는 순바이어스를 이미 거부).
