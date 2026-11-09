# 'A(V/V)가 0과 구별되지 않음' 판정 -- δV_out 후보 실현 가능성 분석

- 작성 2026-10-21. 분석 agent가 읽기 전용으로 작업했고 저장소는 바꾸지 않았다. 코드 base는 master `468e6e73`, 검토한 계획은 `wt/gb-v624`(plan/gb-v624 head `449da113`)의 N3.8 '반전 입력 포트 식별 / 판정 분해능의 정의 자리'(plan.md 575행 안)와 DEC-23(223행)이다. 대상 결정은 `_drafts/user_decisions.md`의 O-67 (3)(688행), O-68 (1)(689행), O-70 (1)(691행)이다.
- 실측 스크립트는 엔진을 import만 하고 소스는 고치지 않았다. 스크립트는 `C:/Users/HSLEE/AppData/Local/Temp/claude/C--Users-HSLEE-Documents-Todoc-fpga-chip-design-skills/63c6146a-ab1d-4035-a169-bae810986922/scratchpad/dvout/meas.py`, 결과는 같은 폴더의 `out.jsonl`이다. 경로는 `run_stage_a` → `run_stage_b` → `build_kernel_context` → `build_search_context` → `layer0_start` → `size_and_seal` → `ss_evaluate`이고, 그 뒤 `metrics_aux._ss_of`로 봉인점 회로를 조립했다. 이것은 IT-2 설계의 `graph.ss_nodal`과 같은 계(`conductance_matrix` + `nodal_factor`, 고정 = ac 접지 ∪ 입력 넷)다.
- 대표점은 layer0 시작점 하나다(탐색 해가 아님). current_reuse_telescopic_ota는 `layer0_start`가 시작점을 내지 못해(`l0.start is None`) 측정하지 못했다. 그래서 이 회로는 §5 미검증 항목으로 남긴다.

## 0. 결론 요약

1. **현재 계획 문언(O-70 (1), 엔진 δV_out = `graph.dc_seal_1`의 출력 노드 항목)은 그대로 구현할 수 없다.** (a) `dc_seal_1`은 노드별 항목을 저장하지 않는다. `judge()`가 최악 행 하나만 `SealItem`에 남긴다(`sizing/_helpers_seal.py:19-38`, 30행 `worst = max(pool …)`). (b) 그 노드에 닿는 MOS의 `dc_tol_v` 최댓값이라는 문언도 사실과 다르다. 봉인 1이 세는 MOS 관계는 `PATH_MOS = "vgs"`(`sizing/s2_values.py:42`)뿐이라 drain에만 닿는 출력은 `n·eps·|V|`를 받는다(`sizing/seal_node_conflict.py:28-34`). 실측하면 two_stage_ota OUT은 **4.0e-16 V**(관계 `y` 하나), nmcnr Vout은 **1.1e-15 V**(관계 `resistor` RL·Rm)였다. IT-2c가 이 문언으로 착수하면 '정본 자리 없음'(CLAUDE.md graph 규칙 6)에 걸려 멈춰야 한다.
2. **LUT 허용오차 전파(S-19 꼴 s_A)는 쓸 수 없다.** 두 회로 모두 보통 증폭기인데 s_T/|T| = **0.98~2.2**가 나와, 반전 입력 식별이 전 회로에서 fail-closed로 막힌다. 물리적으로도 틀린 축이다. LUT 오차는 모델 오차(DEC-72, 오라클 대조)의 몫이고, 같은 셀을 쓰는 정합 소자끼리는 오차가 상관되어 있는데 abs-sum은 이를 독립으로 다룬다. 또 ε_d가 0.15~0.40이라 1차 전파가 유효한 범위 밖이다.
3. **권고: 후보 (iii) '선형해 수치 분해능'.** 엔진 δV_out을 '그 전달의 선형 풀이가 출력 노드 전압에 남긴 수치 오차(V)'로 둔다. 계산은 수반 z와 잔차 r의 곱이고 구동 = 레일 폭이다. 판정식으로 바꾸면 \|A\| ≤ δA_num = \|z_u\|ᵀ\|r\|(단위 구동)이다.
   - 필요한 값은 모두 기존 함수의 반환값이나 그 인수에서 나온다. `graph.ss_nodal`의 인수분해, `nodal_solve`, `nodal_adjoint`(`metrics/_helpers_nodal.py:52-82`)를 쓴다. 새 graph 필드, 새 상수, 새 생산자는 필요 없다.
   - 결과는 설계된 출력 전용 칸 `IcmConfig.transfer`의 (port, T_p, resolution)에 들어간다(design 41 v1.12.3 731행).
   - 실측값은 δA_num ≈ **1.4e-13~2.3e-12 V/V**이고 \|T\| = 41~188이다.
   - 이것은 **design 41 v1.12.3 734행 문언('`nodal_solve` 상대 잔차를 T_p에 전파한 폭')과 같은 뜻**이다. O-68 (1)이 버린 옛 O-67 (3)의 결함은 무차원 상대 잔차를 그대로 V로 쓴 것인데, 이 정의는 잔차를 z로 출력 노드 전압까지 전파하므로 그 결함이 없다.
   - 다만 계획 v6.24 N3.8의 엔진 δV_out 문언(O-70 (1))을 바꿔야 하므로 **사용자 결정이 한 건 필요하다**(§4.3 최소 결정).

## 1. 물리: 엔진이 DC 전달 A에 대해 '모르는 것'은 무엇인가

A = sᵀG⁻¹b는 봉인점 G(LUT의 gm·gmb·gds, 선언 1/R)의 결정적 함수이고, 엔진이 내는 A는 그 식의 값이다. 이 값을 흐리는 원천은 두 가지다.

| 원천 | 크기(실측) | 이 판정에서의 몫 |
|---|---|---|
| (N) 선형 풀이 수치 오차: LU 반올림. 1차식은 δA = zᵀr(z = 수반, r = G x̂ − b) | 1e-13~1e-12 V/V(§3), 상대 1e-15~1e-14 | **엔진 도구의 분해능.** DEC-23 원문 '분해능 이하의 A_dc로 나눈 값은 **수치적으로** 정해지지 않은 값', N3.8 원문 '출력 전압의 **수치 분해능**'이 가리키는 것이 이것이다. |
| (M) LUT 조회 불확실성: Δp = ε_d·\|p\|, ε_d = (gm/ID)·tol_V(`metrics/ss_linearize.py:74`, `metrics/lut_parameters.py:56`) | ε_d = 0.15~0.40(§3). abs-sum s_T ≥ \|T\| | **모델 오차**(DEC-72)의 몫이다. 계획 N3.8 감도 게이트 문언도 둘을 구분한다('ε은 선형해의 수치 분해능이고 모델 오차는 SPICE 대조값이다'). 오라클이 같은 양을 `.tf`로 독립 측정해 대조한다. |

상쇄로 생기는 작은 A(평형·차동 구조, 공칭 A ≈ 0)는 두 원천에서 다르게 다뤄진다.

- (N)은 상쇄를 정확히 다룬다. A = a − b를 LU로 풀면 오차는 eps·(\|a\|+\|b\|) 차수이고 zᵀr가 이를 잡는다. two_stage_ota에서 T(vin_p) + T(vin_n) = 41.808 − 41.353 = 0.455(공통모드 전달)인데, 그 수치 오차는 ~3e-12다.
- (M)의 abs-sum은 같은 LUT 셀에서 나온 정합 소자의 상관 오차를 독립으로 더한다. 엔진 모델 안에서 대칭 회로의 A = 0은 LUT 오차가 있어도 정확히 0을 유지한다(같은 조회에서 같은 값이 나오므로). abs-sum은 이 0 주위에 \|a\|+\|b\| 차수(~80 V/V)의 띠를 씌운다. 그래서 '실제 회로의 A가 0일 수 있는가'는 엔진 손계산이 답할 질문이 아니라 오라클·Monte-Carlo의 몫이다(O-31·O-32 손계산 원칙).
- '출력 전압 절대 바닥'(후보 ii)은 대신호 DC 동작점 허용오차(V)를 소신호 전달 판정에 섞는다. 이는 DC/AC 분리 원칙(O-23 계열)과 어긋나고, 아래 §3처럼 구조에 따라 값이 열세 자릿수 차이 난다.

**결론**: 판정이 물어야 할 것은 '엔진이 계산한 A의 부호·크기를 수치적으로 신뢰할 수 있는가'다. 그 척도는 (N)이고, (M)은 기존 모델 오차·오라클 경로가 맡는다.

## 2. 현재 있는 것(인벤토리, master 468e6e73)

| 항목 | 위치 | 내용 / 이 판정에 쓸 수 있는가 |
|---|---|---|
| S-19 `metric_resolutions` | `metrics/resolution.py`(머리말 1-23, `value = max(lut, numeric)` 100행) | LoopAnalysis·OutputResistance·ResponseRatio 필드만 다룬다. gain_db 분해능은 `db·Re(∂T0/T0)` 상대식(120행)이라 **T0 = 0이면 정의되지 않는다**(115-116행 `dc = None`). 단위는 dB다. A_dc나 포트별 T_p에 해당하는 레지스트리 metric은 없다(`metrics/metrics_aux.py:57-61` `RESOLUTION_FIELDS`에 A 항목 없음). numeric 몫 `e0`(MNA 사후 오차)이 바로 (N)이지만 MNA 계·뷰 단위이고 포트 단위가 아니다. |
| `lut_parameters` / `ParameterSet` | `metrics/lut_parameters.py:37-68`, `metrics/mna_types.py:310-330` | Δp = ε_d·\|p\|, 단위 스탬프. 후보 (i)의 재료이고 실측에 이것을 썼다. |
| `device.dc_tol_v`, `device.dc_gm` | writer `dc_tolerances`(`sizing/seal_tolerances.py:20-31`) | 소자별 V이고 노드 값이 아니다. |
| 노드별 전압 허용오차 graph 필드 | **없음** | `graph.dc_seal_1`은 `SealItem` 하나(최악 행)다(`sizing/_helpers_seal.py:30`, `sizing/s2_values.py:400`). 노드 허용오차 식은 `seal_node_conflict.py:28-34`에 블록 안 지역 값으로만 있다. |
| `_net_tolerance` | `metrics/metrics_aux.py:130-141`(private 함수, graph 필드 아님) | {넷: drain/source가 닿는 MOS tol_V 합}. 소비자는 `offset_systematic` 분해능 하나다(202행). 이 결과는 metric 단위(mV) 분해능으로만 graph에 들어간다(`offset_systematic.py:54`). |
| A_dc 계산 | `metrics/offset_analysis.py:74`, `metrics/offset_systematic.py:50` | 같은 `sense @ volt`가 **두 함수에서 따로** 계산된다(둘째 생산자 -- §4.4 위험). 정의 불능은 `not abs(a_dm) > 0`(정확히 0)일 때뿐이고 분해능 갈래는 아직 없다. `offset_analysis._resolution`(110행~)은 파라미터마다 a1을 1차 수반 갱신으로 이미 계산하지만 δA를 내보내지 않는다. |
| `graph.ss_nodal`, `graph.icm_config` | 코드에 없음(IT-2에서 새로 만듦). 설계는 design 41 v1.12.3 730-742행 | `IcmConfig.transfer` = (port, T_p, resolution), **출력 전용 칸**이다. 734행이 판정 분해능을 '`nodal_solve` 상대 잔차를 T_p에 전파한 폭'으로 적고 있다. |
| `nodal_solve` / `nodal_adjoint` | `metrics/_helpers_nodal.py:52-82` | (전압, 상대 잔차 ‖G_uu x − rhs‖/‖rhs‖)와 z를 낸다. rhs = −coupling·drive는 인수분해 튜플에서 다시 만들 수 있다. |

## 3. 대표 회로 실측(layer0 봉인점)

| 회로 / 출력 구조(de1 표) | 레일 폭 | 전달 | T(V/V) | (i) LUT s_T | s_T/\|T\| | (ii) 봉인1 tol → V/V | (ii′) `_net_tolerance` → V/V | (iii) δA_num(\|z\|ᵀ\|r\|) | (iii′) ‖z‖·resid·‖rhs‖ |
|---|---|---|---|---|---|---|---|---|---|
| two_stage_ota OUT(#9 HZ, drain-only M6·M7) | 1.8 | OUT←vin_n | −41.35 | 42.25 | 1.02 | 4.0e-16 V → 2.2e-16 | 26.6 mV → 1.48e-2 | 4.3e-13 | 5.0e-13 |
| 〃 | 〃 | OUT←vin_p | +41.81 | 41.18 | 0.98 | 〃 | 〃 | 2.3e-12 | 3.0e-12 |
| nmcnr_amplifier Vout(#6 KVL, RL·Rm) | 1.8(agnd 0.9 포함) | Vout←Vin_n | −131.7 | 289.3 | 2.20 | 1.1e-15 V → 6.2e-16 | 28.0 mV → 1.56e-2 | 1.4e-13 | 7.6e-13 |
| 〃 | 〃 | Vout←Vin_p | +187.6 | 410.0 | 2.19 | 〃 | 〃 | 3.9e-13 | 2.8e-12 |

- 1차식 확인: 가장 큰 기여 파라미터 하나를 +Δ만큼 바꿔 G를 다시 풀었다. 4개 전달 모두 선형 예측과 재풀이 차가 13자리까지 일치한다(`fd_check`). 가장 큰 기여는 two_stage의 M6 gm·gds, nmcnr의 M301 gm(ε_d = 0.40)이다.
- 봉인 1 관계: two_stage OUT은 `[('y','OUT')]`, nmcnr Vout은 `[('resistor','RL'), ('resistor','Rm')]`다. 둘 다 MOS(vgs) 관계가 없어서 eps 바닥이 된다. 출력에 vgs 관계가 있는 구조(#7 pushpull vout = M1.s·M2.s)는 같은 식으로 tol_V(~10 mV) → ~5e-3 V/V가 된다(코드 경로 추론, 이번 실측 대상은 아님). **같은 물리량인데 구조에 따라 바닥이 13자리 달라진다.**
- 오라클 쪽 참고: ngspice 기본값(vntol 1e-6, reltol 1e-3)이라면 two_stage OUT(.op 0.9 V) → 0.90 mV → 5.0e-4 V/V, nmcnr Vout(1.686 V) → 1.69 mV → 9.4e-4 V/V다. 실제 값은 `simulator.options`에 따르므로 미검증이다.
- 차동 출력 회로(current_reuse)는 layer0 시작점이 없어서 측정하지 못했다(§5).

## 4. 후보 비교

### 4.1 후보별 판정

| | (i) S-19 꼴 LUT 전파 s_A, \|A\| ≤ s_A | (ii) 봉인 1 노드 tol 승격(새 노드별 필드), O-70 (1) 문언 | (ii′) `_net_tolerance`를 graph 필드로 승격 | **(iii) 선형해 수치 분해능 δA_num = \|z_u\|ᵀ\|r\| / 구동** |
|---|---|---|---|---|
| 값의 존재 | 재료 있음(`lut_parameters`, ε_d). 포트별 계산은 새로 짜야 함 | **없음.** 노드별 값 미저장(`_helpers_seal.py:30`). 새 필드·새 writer 필요 | 함수는 있음(`metrics_aux.py:130`). graph 필드 아님 → 새 필드·writer 필요 | **있음.** `ss_nodal` 인수분해(IT-2 설계), `nodal_solve` 잔차·`nodal_adjoint` z(`_helpers_nodal.py:52-82`) |
| 단위 | V/V(절대). 상대형 gain_db는 A = 0에서 정의 불능 | V → /레일 폭 | V → /레일 폭 | V(구동 = 레일 폭) ≡ V/V |
| 포트별 | 가능 | 노드 단위(포트 무관) | 노드 단위 | 가능(T_p마다 정방향 1회, 출력마다 수반 1회) |
| 대표값 | s/\|T\| = 0.98~2.2 → **정상 증폭기 전부 '판정 불능'** | 2e-16~6e-16 V/V(drain·R 출력), vgs 출력 ~5e-3 | 1.5e-2 V/V | 1e-13~3e-12 V/V |
| 퇴화 | 1차 전파가 ε ≈ 0.2에서 무효. 정합 상관 무시 | 구조 의존(13자리). eps 바닥은 '노드 값의 부동소수 표현 한계'이지 전달 분해능이 아님 | 대신호 DC 허용오차를 소신호 판정에 섞음(DC/AC 분리 위배). 고임피던스 출력의 실제 DC 불확실성과도 무관 | A가 정확히 0이면(경로 없음·출력 floating) δ = 0이고 \|A\| ≤ δ가 참이라 판정 불능(fail-closed, 맞음). LU 특이는 기존 undefined 경로 |
| graph 규칙 | 계산은 `icm_config` 안에서 가능. 다만 모델 오차와 같은 정의의 양을 둘째로 만드는 셈(DEC-72) | 새 필드(규칙 6: 계획부터) | 새 필드 + 기존 private 계산 이전 | **새 필드 없음.** writer `icm_config`가 `IcmConfig.transfer.resolution`(설계된 칸)에 기록. 읽는 것은 `graph.ss_nodal`뿐. cache·사본 없음 |
| 오라클과 같은 축 | 아님(오라클 vntol은 수치 허용치) | 이름만 '전압 허용오차'로 같고 물리 의미는 다름 | 다름(LUT 허용오차와 시뮬레이터 수치 허용치) | **같음: '그 도구의 수치 분해능'**(엔진 = LU, 오라클 = Newton·.tf 허용치). 크기 차(1e-12 대 5e-4)는 DEC-23 '정의 경계 불일치' 기록으로 처리(기존 장치) |
| 동작 변화 | 반전 입력 식별이 거의 모든 회로에서 정의 불능 → ICMR follower 구성 소멸 | 사실상 'A == 0'일 때만 발동 | \|A\| ≤ 0.015에서 발동 | 사실상 수치적 0·상쇄 실패에서만 발동 |
| IT-2c가 새 결정 없이 구현 가능한가 | 불가(계획 문언과 다름 + 위 결함) | **불가**(정본 자리 없음) | 불가(새 필드) | 계획 문언(O-70 (1))과 다르므로 **결정 1건 필요**. 단 design 41 734행과는 일치 |

### 4.2 권고 (iii)의 실현성 점검표

| 점검 | 근거 | 결과 |
|---|---|---|
| 입력 존재 | `_helpers_nodal.py:52-70`(nodal_solve: 전압 + 상대 잔차, rhs = `inject[unknown] − coupling @ volt`), `:73-82`(nodal_adjoint) | 있음. ‖rhs‖는 인수분해 튜플의 `coupling`과 구동에서 같은 식으로 나온다. 잔차 벡터 r 자체가 필요하면 helper 반환을 늘리거나, Cauchy-Schwarz 상계 ‖z_u‖·resid·‖rhs‖를 쓴다(실측상 \|z\|ᵀ\|r\| 대비 1.2~7배 보수적) |
| 저장 단위 | design 41 731행 `IcmConfig.transfer` = (port, T_p, resolution) | 포트 × 출력 단위로 이미 설계된 칸이다. 출력 전용(소비자 없음 선언). 판정 결과는 `undefined` 코드 `icm_inverting_port_unresolved` |
| 단위·차원 | z[V/A]·r[A] = V(구동 1 V당) → V/V. 구동 = 레일 폭이면 δV_out[V] | 계획 '한 꼴' \|A\|·span ≤ δV_out과 바로 맞는다(δV_out = span·δA_num) |
| 차동 출력 | sense = e_p − e_n의 수반 하나 | 오라클 'δ_p + δ_n'과 같은 꼴(상계로 \|z_p\|+\|z_n\|를 써도 됨). 실측은 못 함(§5) |
| 경로 끝까지 | `ss_evaluate.py:101` ss_dev → (IT-2) `ss_nodal` → `icm_config`: T_p = nodal_solve(구동 p) → z = nodal_adjoint(e_out) → δ = \|z_u\|ᵀ\|r\| → \|T_p\| ≤ δ면 unresolved → `graph.icm_config`. 소비자는 `dc_window_refine`·`metrics_aux`·`metrics_icm_front`(구성 None 갈래, design 41 732행) | 끊긴 곳 없음 |
| graph 규칙 1~5 | writer 하나(`icm_config`), READS `graph.ss_nodal`, 새 cache·memo·sctx 슬롯·사본 없음 | 준수 |
| 새 상수 | 없음(eps도 쓰지 않음, 잔차 그대로) | 준수 |
| 성능 | 출력마다 수반 1회(LU 재사용), 포트마다 정방향은 T_p 계산에 이미 포함 | 무시할 수준(O(n²)) |
| DEC-23 A_dc 갈래 | 같은 식: `offset_analysis`는 z·factor·volt를 이미 가짐(`offset_analysis.py:74`, `_resolution` state) | 구현 가능. 단 §4.4 둘째 생산자 위험 |

### 4.3 필요한 최소 결정(한 건)

> **N3.8 '판정 분해능의 정의 자리'의 엔진 δV_out 정정**: 엔진 δV_out = 그 전달의 선형 풀이(`graph.ss_nodal` 인수분해, 구동 = 레일 폭)가 출력 노드 전압에 남긴 **수치 오차**, 곧 수반 z(출력 관측)와 풀이 잔차 r의 전파 \|z_u\|ᵀ\|r\|(V, 차동 출력이면 관측 e_p − e_n)이다. 기록 자리는 T_p면 `IcmConfig.transfer`의 resolution 칸, A_dc면 그 A_dc를 계산하는 자리 하나다. 새 필드·상수·생산자는 없다. O-70 (1)의 '`graph.dc_seal_1` 노드 항목' 문언을 대체한다. 근거는 노드별 항목이 없다는 점(`_helpers_seal.py:30`)과 drain·R 출력에서 eps 바닥이 된다는 점(`seal_node_conflict.py:34`, `s2_values.py:42`)이다. LUT 허용오차는 모델 오차(DEC-72)라 넣지 않는다. 오라클 쪽 문언(vntol + reltol·\|V\|)은 그대로 두며, 두 쪽 모두 '도구의 수치 분해능'이다.
>
> **원래 취지와의 관계**: O-68 (1)의 축('그 도구의 전압 분해능')은 유지하고 출처만 바꾼다. 옛 O-67 (3) 'nodal_solve 잔차'의 결함(무차원 값을 V로 사용)은 z 전파로 해소된다. design 41 v1.12.3 734행 문언과 같아지므로 design 개정은 인용 정리 정도면 된다.

### 4.4 함께 보고할 위험

- **A_dc 둘째 생산자**: `offset_analysis.py:74`와 `offset_systematic.py:50`이 같은 A_dm을 따로 계산한다. DEC-23 갈래('\|A_dc\| ≤ 판정 분해능이면 σ·V_id* 모두 정의 불능')를 두 함수에 따로 넣으면 판정이 두 곳에서 나온다(graph 규칙 1). DEC-23 갈래를 구현하는 card는 A_dc와 δA_dc의 정본 자리를 하나로 정해야 한다. 이는 IT-2c 범위 밖이다.
- **`_net_tolerance`**(`metrics_aux.py:130`)는 graph 밖 지역 계산이다(`offset_sys_mv` 분해능 전용). 이번 판정에 끌어 쓰면 둘째 사용처가 생기므로 권고하지 않는다. 이 함수의 존재 자체는 기존 상태다.
- **(M) 축 정보의 손실 없음**: LUT 전파 분해능은 S-19 `MetricResult.resolution`(gain_db·offset 등 metric 단위)과 DEC-72 모델 오차로 이미 보고된다. 이번 판정에서 빼도 어디서도 사라지지 않는다.

## 5. 미검증 항목

1. 차동 출력(current_reuse_telescopic_ota Vop·Vom)의 실측. 이 회로는 layer0 시작점이 없어 봉인점을 얻지 못했다. 차동 수반(e_p − e_n)의 값은 식으로만 확인했다.
2. 상쇄 구조(A ≈ 0)의 실측은 two_stage의 T_p + T_n = 0.455(수치 오차 ~3e-12)뿐이다. 진짜 A = 0 대칭 회로 사례는 재지 않았다.
3. 출력에 vgs 관계가 있는 구조(pushpull vout)의 봉인 1 tol 값(~10 mV)은 코드 경로로 추론했고 실측하지 않았다.
4. 오라클 vntol·reltol의 실제 선언값(`simulator.options`)은 확인하지 않았다(ngspice 기본값으로 계산).
5. 잔차 r을 `nodal_solve` 내부 부동소수로 계산하면 r 자체가 eps 수준에 묶인다. 더 보수적인 a priori 상계 n·eps·\|z_u\|ᵀ(\|G_uu\|\|x\| + \|rhs\|)를 쓸지는 design에서 정할 선택지다(계획 수준 결정은 아님).
6. 대표점은 layer0 시작점이다. 탐색 해·다른 θ에서 ε_d 분포(0.15~0.40)는 재지 않았다. 다만 결론 (i) 불가는 ε_d가 몇 배 작아져도 abs-sum이 \|T\|의 수십 %가 되므로 바뀌지 않을 것으로 본다(추론).
