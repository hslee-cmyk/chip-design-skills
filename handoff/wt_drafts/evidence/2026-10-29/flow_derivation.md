# erfc_ota 부유 전지 f_HP의 이론적 결정자 -- f_low 없이 정해지는가 (2026-10-29)

질문(사용자): "f_low를 이론적으로 결정할 수 있는 방법은 정말 없나? … 잘못된 f_low를 잡으면 큰 영향을 미치기 때문에 기본적으로 결정방법이 있는지 검토하고 싶어."
작성: 분석 agent(읽기·측정만, 저장소 수정 0). 스크립트·출력: `wt/_drafts/evidence/2026-10-29/flow_derivation/`
(`erfc_net.py` 생성기, `s1_bias_scan`·`s2_op_ac`·`s3_tran`·`s4_doublet_model`·`s5_corpus`·`s6_pump` 각 `.py`→`.txt`; 큰 파형 `.dat`는 지움 -- 스크립트로 재생성).
원문: Wu 외, Sensors 25(8):2523, 2025, https://pmc.ncbi.nlm.nih.gov/articles/PMC12031453/ , 로컬 PDF `chip-design-skills/skills/analog-gmid-design/assets/heldout/sources/erfc_ota__wu_2025/source.pdf`(텍스트 `paper.md`).
Kamath·Meyer·Gray, "Relationship between frequency response and settling time of operational amplifiers", IEEE JSSC SC-9(6), 1974 -- **로컬 PDF 없음**(저장소·Todoc 아래 검색 0). 이 문서의 doublet 꼬리 식은 그 논문을 인용하지 않고 2절에서 직접 유도하고 S4로 검증했다.

## 결론

1. **f_low(응용 신호 대역 하한)는 회로에서 유도되지 않는다 -- 그러나 f_HP의 물리 결정자도 아니다.** 계획 v6.38.5 Q-ZG1의 전제 "f_HP는 신호 대역 하한 아래에 있어야 한다"는 이 회로에서 **틀림**(확신도 중상).
   - f_HP 아래 주파수에서는 결합 경로만 끊긴다. OTA는 Fig.5a 고정 바이어스 cascode로 그대로 증폭한다. 실측: DC 이득은 모든 f_HP에서 73.059 dB로 같다. 결합 경로가 더하는 이득은 kα ≈ 1.6 %(+0.14 dB)뿐이다(S2).
   - 원문의 "lower low cut-off frequency"(p.7)는 **RC 고역 통과 자신의 차단 주파수**를 말한다. 증폭기 신호 대역이 아니다. 원문 어디에도 신호 대역 하한은 없다. 저주파 서술은 p.13 "0.1 Hz 입력 잡음" 하나뿐이다.
   - 전지 경로의 기능은 **대신호 과도(슬루) boost**다(p.3 2.2절, p.7 3.1절). 실측: 결합을 끊은 고정 게이트에서 SR = 0.65/0.53 V/µs, 결합 시 47/19 V/µs다(S3). 원문의 RFC 0.16 대 ERFC 19.32 V/µs와 같은 꼴이다.
2. **f_HP의 상한은 이미 있는 양에서 상수 발명 없이 나온다**(확신도 중). 네 가지다.
   - (i) 대신호: τ = R_ds·(C_BAT + C_g) ≫ t_slew = ΔV/SR. 처짐 1 − e^{−t_slew/τ}가 SR을 깎는다. 실측: τ 169 ns, t_slew/τ 0.08~0.18에서 SR −5~−8 %, t_slew/τ 0.018에서 변화 없음.
   - (ii) 소신호 정착 doublet: 느린 꼬리 진폭 A_s = k·f_HP/((1+k)·β·f_u), 시상수 (1+k)/(2π f_HP). 식은 정확해·ngspice와 일치한다(S4).
   - (iii) PM: f_HP ≥ 0.3·f_u에서 PM 84 → 70°가 된다.
   - (iv) 부하: R_ds ≫ R_X,Y. R_ds가 X·Y 노드를 짐으로 잡아 NLF 이득을 깎는다. 같은 f_HP 100 kHz라도 C 10 pF·R 159 kΩ이면 f_u −36 %이고, C 0.1 pF·R 15.9 MΩ이면 −2 %다.
   - (iii)·(iv)는 R_ds·C_BAT를 AC MNA에 스탬프하면 선언 제약 GBW·PM이 직접 본다. (i)은 SR 제약 항목(계단 크기 포함)이 있으면 손계산 행 하나로 쓴다.
3. **f_HP의 하한은 spec 지표에서 나오지 않는다.** 소신호 지표는 f_HP → 0에서 모두 좋아지거나 같다(꼬리 진폭 ∝ f_HP).
   - 하한을 거는 물리는 둘이다. 둘 다 spec 밖 응용 시간 양이거나 f_HP와 다른 축이다.
   - (a) 시동·사건 후 회복 시간. MOS pseudo-R에서는 회복 전류가 포화된다. t ≈ C·ΔV/I_F이고, 실측 I_F ≈ 5.8e-16 A로 0.16 V 회복에 약 290 s다. erfc spec에 시동 시간은 없다.
   - (b) **MOS pseudo-R 정류(pumping)**. 반복 대신호에서 게이트가 VCN 위로 크게 오르면 M19가 역방향 지수 전도로 전하를 뺀다. 그래서 전지 DC가 아래로 표류한다.
     - 실측(C 1 pF, 600 mV p-p 100 kHz): g5가 0.700 → 0.540 V(60주기, 600 µs) 표류했고 여전히 진행 중이었다. n_m5s는 0.178 → 0.055 V로 M3B 포화 경계에 접근했다.
     - 선형 R(f_HP 1 kHz)은 ±12 mV 안에서 안정했다.
     - 표류 평형은 f_HP가 아니라 **게이트 상승 진폭 α·ΔV_X**가 정한다(C 0.1 pF는 상승 +0.29 V에서 표류 0, C 10 pF는 −5 mV/주기). 속도만 1/C에 비례한다.
     - 이것은 O-174 'VDS = 0 묶음'이 **소신호·정지 상태에서만 정확**하다는 뜻이다(별건 위험, 4절).
4. 그래서 기본 결정법은 **(나) 시간 영역 spec + AC 제약에서 상한을 유도하고, 하한이 없으니 면적 최소 기하(상한에 붙음)를 고르는 것**이다.
   - f_low 선언(가)은 필요 없다. 선언하면 오히려 근거 없는 큰 R·C(면적)를 강제한다.
   - 다만 erfc spec에서 SR은 `driving_spec`(DEC-58 v6.38: `.tran` 제약 -- card SF-1로 이전 예정)이고 정착은 보고만이다. 계단 크기 ΔV(원문 600 mV p-p)는 spec 칸이 아니라 출처 문장에만 있다. (나)의 착수 조건은 SF-1의 `.tran` SR 항목(자극 크기 포함)이다.
   - **원래 취지와 다름**: v6.38.5 Q-ZG1(결정자 = f_low)과 다르다. 계획 개정이 먼저다.
5. 13회로 전수(S5): 'AC 결합 게이트 + 고저항 DC 바이어스' 꼴은 erfc_ota 셋(CBAT1_L·CBAT1_R·CBAT2)뿐이다.
   - 다른 hit 3회로(current_reuse_telescopic Cc–Rz, nmcnr Cm–Rm, two_stage Cc–Rz)는 게이트가 없는 직렬 RC 보상 내부 넷이다. R이 작고 고주파 영점용이라 다른 범주다.
   - 규칙 식은 topology 무관(SR·계단·β·f_u·R_X 일반 양)이지만, 현재 소비자는 erfc 하나다.

## 1. 원문 근거 (쪽 = PDF 쪽, 로컬 `source.pdf`)

| 쪽 | 내용 (paper.md 행) | 의미 |
|---|---|---|
| p.3 2.2절 (184-186) | "coupling capacitors CBAT1 and CBAT2, along with the bias resistor RL, provide floating bias voltages for the gates of M5–M8. This addresses the potential operating point shift … during the transient response." | 목적 = 과도 응답 중 동작점 이동 방지(대신호) |
| p.7 3.1절 Fig.5 (333-352) | "M3B may enter the linear region under large-signal conditions, limiting the output current … In a static state, no current flows through the series RLCBAT, and VC is equal to VE … If a large step is applied, an induced voltage … VS travels through the RC highpass filter to the gate of the cascode transistor, preventing the transistor connected to its source from entering the linear region and increasing the permissible high current output … The RLCBAT is often designed as larger to achieve a lower low cut-off frequency. The CBAT does not need to be excessively large, as the local positive feedback loop significantly enhances the large-signal response at VX,Y … RL also can be realized using a transistor." | 경로 = 계단 때 boost. 'low cut-off' = RC HPF 차단. CBAT 크기 근거 = X·Y 스윙 증폭(정성, 수치 없음) |
| p.7-8 3.2절 (358-360) | M19~M21 "deep triode … active resistors" | R_L = MOS |
| p.9 Table 1 | M19,20,21 3 µm/1 µm. **CBAT 값 없음** | τ·f_HP 수치 원문 없음 |
| p.10 (499-519) | PM 식 (13): 비주극 wp2 = 1/(R_X C_X), wp3. **CBAT·R_L은 극·영점 목록에 없음** | 원문 소신호 분석은 결합 경로를 무시(doublet 무시) |
| p.11-12 3.5절 (654-751) | SR = I_out/CL, I_out ∝ V_id⁴ (식 21~24) | SR 손계산에 전지 처짐 항 없음(τ ≫ t_slew 가정이 암묵) |
| p.13-14 (796-825) | 단위이득 **반전** 구성. 소신호 = 10 mV p-p 100 kHz 50 % 구형파(DC 800 mV), 1 % 정착 0.473 µs. 대신호 = 600 mV p-p 구형파, 평균 SR 19.32 V/µs, overshoot 약 100 mV | 정착 ε = 1 %, β = 1/2, 계단 ΔV = 0.6 V, t_slew = 0.6/19.32 µs = 31 ns |
| p.13 (783-786) | 입력 잡음 @0.1 Hz 26.61 µV/√Hz | 유일한 저주파 서술(잡음 표시 점이지 신호 대역 선언 아님) |
| p.1-2 (76) | 응용: "portable devices, Internet of Things sensors, and medical electronic devices" | 응용 범주만, 대역 수치 없음 |

## 2. 연결로 본 경로 역할과 식

**연결**(topology.json, S5·erfc_region net_audit):
- CBAT1_L: X ↔ n_m5g(M5 게이트). M5 = NMOS cascode, 소스 n_m5s = M3B 드레인 = M1A 드레인(접힘 노드). M3B 게이트 = X.
- CBAT1_R: Y ↔ n_m6g(M6 게이트, 같은 꼴).
- CBAT2: n_m7d(M9·M10 게이트 = 미러 입력) ↔ n_m8g(M7·M8 게이트).
- M19/M20/M21: n_m5g/n_m6g/n_m8g를 VCN/VCN/VCP에 DC로 묶는다(0 전류, VDS = 0).

**DC·저주파(f ≪ f_HP)**: 게이트 = 레일(Fig.5a 고정 바이어스 cascode). DC 이득·출력 저항은 모두 이 망이 정한다(원문 식 (10)·(12)와 같음).

**f ≫ f_HP**: v_g5 = α·v_X, α = C_BAT/(C_BAT + C_g) (C_g = n_m5g 기생, 실측 M5 cgg 62 fF + M19 7 fF).
- cascode 소스가 게이트를 따라가 v_s5 ≈ α v_X다. 접힘 노드 KCL은 i_5 = g_m3B·v_X + (g_o3B + g_o1A)·v_s5다.
- 그래서 boost 비율은 **k_branch = α·(g_o3B + g_o1A)/g_m3B**이다. 실측 op(S2): (2.04 + 0.10)/63.0 µS × 0.94 = 3.2 %(M5·M6 가지 상한 추정).
- 출력 전류 전체로는 측정치 **k ≈ 1.6 %**다(고정 게이트 f_u 463.1 kHz 대 결합 470.3 kHz, S2). M8 쪽 CBAT2 경로는 n_m7d 스윙이 1/g_m9 노드라 작다.
- **결론: 소신호에서 전지 경로는 cascode 게이트 bootstrapping으로 이득을 1~3 % 올리는 부경로다. DC 이득을 주는 경로는 고정 바이어스 망이다.** 대신호에서는 X 스윙(수백 mV~1 V)이 그대로 게이트로 넘어가 M3B를 포화에 붙잡는다. 이것이 주경로다(SR 30~70배).

**doublet**: A(s) = A_lo·(1 + sτ(1+k))/(1 + sτ), τ = R_ds(C_BAT + C_g).
- 영점은 ω_z = 1/(τ(1+k)), 극은 ω_p = 1/τ다. 영점이 극 바로 아래에 있다(고역 이득 +k).
- 폐루프(되먹임 β, 고역 단위이득 각주파수 ω_u = 2π·β·f_u)의 계단 오차는 e(s) = (s + ω_p)/(s² + s(ω_p + ω_u) + ω_u ω_z)다.
  - 느린 극 ≈ ω_z.
  - 유수 **A_s ≈ (ω_p − ω_z)/ω_u = k·f_HP/((1+k)·β·f_u)**, 시상수 **τ_s ≈ (1+k)/(2π f_HP)**.
- S4 행동 모형(k = 0.074 스트레스 값, β 1/2, f_u 470 kHz): f_HP 10 Hz~30 kHz에서 식·정확해·ngspice가 맞는다(1e3 Hz: 2.932e-4 / 2.954e-4 / 2.954e-4). f_HP → β f_u이면 식이 깨진다(1e5 Hz 식 2.9e-2 대 정확 7.1e-2 -- 그 영역은 doublet이 아니라 PM 문제).
- **정착 조건**: A_s ≤ ε이면 꼬리가 처음부터 오차 띠 안에 있다. 그래서 **f_HP ≤ ε(1+k)·β·f_u/k**이면 무해하다. 넘으면 t_s ≥ τ_s·ln(A_s/ε)가 필요하다.
  - S4 실측: A_s 1.1 % > ε 1 %가 되는 30 kHz에서 1 % 정착 3109 → 3669 ns.

**대신호 처짐**: X 계단 ΔV_X에 대해 v_g5(t) = α·ΔV_X·e^{−t/τ}다. 슬루 동안 처짐 비율은 1 − e^{−t_slew/τ} ≈ t_slew/τ, t_slew = ΔV_out/SR다.
- 선형 R이면 이 식이 그대로다.
- MOS pseudo-R은 게이트가 VCN보다 올라가는 쪽에서 드레인·소스가 바뀌어 V_SG′ = V_g − V_Z로 지수 전도한다. 그래서 올라가는 쪽 실효 τ가 짧고 내려가는 쪽은 포화 전류 I_F로 제한된다(비대칭 → 6절 정류).

## 3. sky130 실측 (bench 조건과 결과)

**bench**(S1):
- 원문 바이어스(VCP 1.1·VCN 0.7·VCM 0.8 V)는 sky130에서 붕괴한다(erfc_region.md 5절).
- 그래서 VDD 1.8·**VCP 0.7·VCN 0.7·VCM 0.6 V** 격자점을 골랐다. M19~M21 밖 전 MOS가 포화(최소 여유 +0.13 V, M4B)이고, 정지 전류 9.18 µA(원문 10.4)다.
- Table 1 치수, CL 70 pF, M19~M21 bulk = source(O-174 반영 topology), tt.
- 개루프: DC 이득 73.06 dB, f_u 470 kHz, PM 82.6°(원문 84.18 dB·1.37 MHz·67°와 다름 -- 공정 대용이라 경향만 쓴다).
- f_HP 변경: M19~M21 자리에 선형 R_ps(`mode=res`, f_HP = 1/(2π R C_BAT))를 넣거나 Table 1 MOS(`mode=mos`)를 썼다.
- 기준: 고정 게이트 = R 1 Ω로 VCN에 묶음(Fig.5a). R 1 GΩ·C→0은 게이트 자기 Cgs bootstrapping이 섞여 기준이 아니다(S2 `selfboot` 행).

**(a) 개루프 AC (S2 `s2_op_ac.txt`)**

| 경우 | R_ps | C_BAT | f_HP | DC 이득 dB | f_u kHz | PM ° |
|---|---|---|---|---|---|---|
| 고정 게이트 | 1 Ω | → 0 | -- | 73.059 | 463.1 | 84.31 |
| res | 159 GΩ | 1 p | 1 Hz | 73.059 | 470.3 | 82.56 |
| res | 1.59 GΩ | 1 p | 100 Hz | 73.059 | 470.3 | 82.55 |
| res | 15.9 MΩ | 1 p | 10 kHz | 73.059 | 467.9 | 82.64 |
| res | 1.59 MΩ | 1 p | 100 kHz | 73.059 | 447.2 | 82.84 |
| res | 531 kΩ | 1 p | 300 kHz | 73.059 | 419.3 | 80.64 |
| res | 159 kΩ | 1 p | 1 MHz | 73.059 | 414.8 | 74.34 |
| res | 15.9 kΩ | 1 p | 10 MHz | 73.059 | 435.1 | 70.21 |
| MOS(Table 1) | ~5e13 Ω | 1 p | ~3 mHz | 73.059 | 470.2 | 82.78 |
| res | 15.9 MΩ | 0.1 p | 100 kHz | 73.059 | 460.8 | 82.93 |
| res | 159 kΩ | 10 p | 100 kHz | 73.059 | **302.3** | 80.58 |

- DC 이득은 f_HP와 무관하다. f_HP ≪ f_u이면 f_u는 +1.6 %, PM은 −1.7°다(doublet 무해).
- f_HP ≥ 0.3 f_u이면 PM이 −4~−14° 빠진다.
- 같은 f_HP(100 kHz)에서 R이 작으면(10 pF·159 kΩ) f_u −36 %다. **R_ds가 X 노드를 짐으로 잡는 것**(R_X,Y와 비교, 원문 식 (7))이 f_HP와 별개의 조건이다.

**(b) 폐루프 소신호 계단 (S3, 반전 β 1/2, 10 mV p-p 100 kHz)**: 1 % 정착 시간

| 고정 | f_HP 10 Hz | 1 kHz | 10 kHz | 100 kHz | 1 MHz | MOS |
|---|---|---|---|---|---|---|
| 2995 ns | 2903 | 2903 | 2918 | 2893 | 2453 | 2903 |

- k = 1.6 %, ε 1 %, β f_u = 235 kHz이면 무해 조건은 f_HP ≤ ε(1+k)βf_u/k ≈ 149 kHz이고, 실측은 100 kHz까지 변화가 없다.
- 1 MHz는 τ_s(0.16 µs)가 폐루프 τ(0.68 µs)보다 빨라 꼬리가 아니라 빠른 동역학에 섞인다. 그래서 정착이 오히려 빠르다(대신 PM 74°).
- 원문 수치(β f_u = 685 kHz, k 미상 -- sky130 k = 1.6 %를 쓰면): 상한은 ≈ 0.43 MHz다.

**(c) 폐루프 대신호 계단 (S3, 600 mV p-p 100 kHz)**

| 경우 | SR 하강/상승 V/µs | 1 % 정착 ns | g5 최대·최소 V | n_m5s 최소 V |
|---|---|---|---|---|
| 고정 게이트 | 0.65 / 0.53 | 2189 / 2389 | 0.700 / 0.700 | **0.001**(M3B 선형) |
| f_HP 10 Hz~10 kHz | 47.1 / 19.0 | 1947~2005 | 1.445 / 0.264 | 0.027 |
| f_HP 100 kHz | 47.1 / 19.6 | 2012 / 2103 | 1.439 / 0.271 | 0.027 |
| f_HP 1 MHz (τ = 169 ns) | **44.6 / 17.5** | 1834 / 1782 | 1.393 / 0.286 | 0.025 |
| MOS(Table 1) | 47.7 / 19.8 | 1966 / 2044 | 1.418 / 0.242 | 0.027 |

- t_slew(10-90 % 기준 전체 0.6 V)는 하강 13 ns, 상승 31 ns다.
- f_HP 1 MHz에서 t_slew/τ = 0.08/0.18(처짐 8 %/17 %)이고, SR은 −5 %/−8 %다(감도 약 0.5 × 처짐).
- f_HP 100 kHz(t_slew/τ ≤ 0.018)에서는 SR 변화가 측정 잡음 안이다.
- 고정 게이트는 n_m5s → 1 mV(M3B 선형)로 SR이 30~70배 낮다. 원문 Fig.5 메커니즘을 재현한다.

## 4. 반복 대신호 정류 (S6, `s6_pump.txt`) -- MOS pseudo-R 고유

| 경우 | 게이트 상승 최대 | g5 주기 0 → 끝 | n_m5s 0 → 끝 | 반주기 끝 오차 |
|---|---|---|---|---|
| MOS, C 1 pF, 60주기 | 1.430 V | 0.700 → **0.540** (계속 표류) | 0.178 → 0.055 | +0.08 → −0.72 % |
| MOS, C 10 pF, 20주기 | 1.484 V | 0.700 → 0.621 | 0.178 → 0.115 | +0.05 → −0.20 % |
| MOS, C 0.1 pF, 20주기 | 0.990 V | 0.700 → 0.700 | 불변 | +0.26 %(SR 27.6/8.2 -- α 낮음) |
| 선형 R f_HP 1 kHz, C 1 pF, 30주기 | -- | 0.700 → 0.702 (g8 0.688, 수렴) | 불변 | +0.06 % |

**물리**:
- M19의 순방향(게이트 < VCN) 복원 전류는 V_SG = VCN − V_Z(0.20 V)에서 포화된 I_F ≈ g_ds0·V_T = 2.23e-14 × 0.0259 = 5.8e-16 A다.
- 역방향(게이트 > VCN)은 V_SG′ = V_g − V_Z로 지수 증가한다. 그래서 한 주기 순전하는 상승 진폭이 순방향 대비 몇 nV_T 이상이면 음수다.
- 표류 평형은 진폭(α·ΔV_X)과 V_Z가 정하고, R·C 크기(f_HP)는 속도만 정한다(C 10배 → 표류 속도 약 1/2.4, α도 함께 올라감).
- 원문 0.18 µm에서도 같은 비대칭(같은 소자의 정·역 지수식)이라 정성은 같다고 추정한다(실측 아님).

**의미**: (1) 하한 쪽 '정답 f_HP'가 있는 문제가 아니라 **pseudo-R 소자 종류와 결합비 α의 대신호 조건**이다. (2) DR-1/O-174 'VDS = 0 묶음'은 정지·소신호 정의로는 맞지만, 반복 대신호 동작에서 전지 DC는 VCN이 아니다(별건 위험 -- 이번 질문 범위 밖이라 권고만).

## 5. 엔진 손계산 꼴 (권고안 (나)의 구체형 -- 이름·자리 design 몫)

| 조건 | 식 | 입력(정본 자리) | 출처 상태(erfc) |
|---|---|---|---|
| U1 대신호 boost 유지 | τ ≥ t_slew/ln(1/(1−e_m)), τ = R_ds(C_c + C_g), t_slew = ΔV_step/SR_spec | SR·ΔV_step = SF-1 `.tran` SR 항목(자극 크기 포함), e_m = ME-1 손계산 오차 범위(O-173 E-0·E-1), R_ds = DR-1 갈래 LUT gds(VDS 0), C_c = θ(DEC-105) | SR 19.32 V/µs = `driving_spec`(SF-1 이전 예정), ΔV 0.6 V = 출처 문장뿐(칸 없음) |
| U2 소신호 정착 doublet | k·f_HP/((1+k)β f_u) ≤ ε (또는 τ_s ln(A_s/ε) ≤ t_s) | k = AC MNA 고·저역 이득비(스탬프 시 자동), β = 측정 구성, ε·t_s = 정착 제약 | 정착은 **보고만** -- 선언 없으면 행 없음 |
| U3 PM·GBW | MNA가 직접 본다 | R_ds·C_c 소신호 스탬프(Q-ZG1 계획 완료 조건 (9)에 이미 있음) | GBW·PM = **제약** |
| U4 X 노드 부하 | R_ds ≫ R_X,Y | MNA가 GBW로 직접 본다(U3에 포함) | 제약 경유 |
| 하한 | 없음(spec 지표 기준) | -- | 시동·회복 시간은 spec 없음 → 기록만 |

- 기하 선택: 하한이 없으니 면적 최소 = U1(과 U3)을 만족하는 R·C 가운데 최소 면적이다.
  - sky130 LUT 실측(`plan_v6385_v3/zg1_alt.txt`): W_min·L_min에서 M19 R = 1.8e8 Ω, M21 8.5e6 Ω, C 1 pF → f_HP 0.9 kHz·18.7 kHz다.
  - 원문 수치 U1 상한(e_m 5 % 예시만: τ ≥ 31 ns/0.051 = 0.61 µs → f_HP ≤ 260 kHz)보다 한참 아래다. 그래서 erfc는 **최소 기하가 이미 U1을 만족**한다(e_m 값은 ME-1 몫, 예시는 결정 아님).
- graph 정본 점검:
  - f_HP·τ 칸 writer는 DR-1 블록 하나다.
  - U1 행은 SR 항목·e_m·τ를 READS로 읽는다.
  - 새 cache·memo·사본은 0이고, 상수 0(e_m·ε·β·ΔV 모두 기존 정본 또는 spec 항목)이다.

## 6. 대안 비교

| 안 | 물리 결정자 | 판정 | 확신도 | 비고 |
|---|---|---|---|---|
| (가) f_low spec 선언(현 Q-ZG1) | 응용 대역 -- 그러나 f_HP 아래서도 OTA는 정상 증폭(DC 이득 불변, 이득 차 1.6 %) | **틀림**(결정자로서) | 중상 | 사용자 값이 틀리면 R·C를 근거 없이 키움(f_low 10 Hz → R 1.6e11 Ω, M21 L 7 µm -- zg1_L). 원문에 값 없음. 이득 평탄도 spec이 따로 있으면 그때 ±k 조건으로 쓰는 것이 맞다 |
| (나) 시간 영역 spec(SR·계단·정착) + AC 제약에서 상한 유도, 하한 없음 → 면적 최소 | SR 동안 boost 유지(τ ≫ t_slew), doublet 꼬리, PM·R_X 부하 | **조건부 맞음** | 중 | 조건: SF-1 `.tran` SR 항목(계단 크기 포함) + R_ds·C_c MNA 스탬프. erfc 정착은 보고만이라 U2 행 없음. MOS 정류는 범위 밖 위험 |
| (다) 미선언, 기록만(W_min·L_min) | 없음(기록) | 조건부 맞음 | 중 | erfc sky130에서는 결과가 (나)와 같음(최소 기하가 상한 아래). 보장이 없음 -- 짧은 L·큰 V_SG·큰 C에서 f_HP가 상한을 넘어도 막지 못함(zg1: L 0.15 µm·V_SG 0.6 V에서 f_HP/GBW 1.8) |

**권고: (나)**(기본 결정자 = SR 항목 + AC 제약, f_low 칸 만들지 않음). SF-1 이전 전에는 (다)(기록)에 U1 계산값을 기록하는 데까지만 한다.

⚠ 원칙 경고:
- (가)는 'f_HP ≪ 신호 대역'이라는 관례를 정의로 쓴 것이다(관례를 정의로 쓰지 말 것 -- 2026-10-23 원칙). 그리고 사용자 값을 결정자로 둬서 잘못된 값의 영향이 그대로 들어온다(사용자 우려와 같음).
- **원래 취지와 다름**: 계획 v6.38.5 Q-ZG1·card DR-1 완료 조건 (9)(f_low 선언 갈래, SF-1 선행 사유 'f_low 선언 자리')을 바꾸는 권고다 → 계획 개정 먼저(S-7).

## 7. 오케스트레이터 가설 판정

| 가설 | 판정 | 근거 |
|---|---|---|
| f_low는 응용 양이라 회로에서 안 나온다 | 맞음 | 원문·연결 어디에도 없음 |
| f_HP 허용 범위는 회로 기능에서 유도된다 | 맞음(상한), 하한은 spec 지표에서 안 나옴 | 2·3절 |
| (1) doublet: PM 영향 작고 정착 꼬리 | 맞음 | PM −1.7°, 꼬리 식 S4 검증. 다만 erfc k ≈ 1.6 %라 무해 창이 넓어(≤ 0.6 β f_u) 사실상 PM·R_X 부하가 먼저 묶음 |
| (2) τ ≫ t_slew → f_HP ≪ SR/(2πΔV) | 맞음(꼴), 상수 '≪'는 e_m으로 | 실측 감도 SR 변화 ≈ 0.5 × 처짐. 원문 수치 SR/(2πΔV) = 5.1 MHz |
| (3) 하한 = 시동 후 DC 평형 시간 | 맞음(물리) / spec 양 아님 | MOS pseudo-R은 포화 전류 회복(약 290 s/0.16 V) -- 시동 spec 없음. 추가 발견: 반복 대신호 정류는 f_HP가 아니라 α·ΔV_X 축 |
| 가설에 빠진 것 | -- | R_ds ≫ R_X,Y 부하 조건(같은 f_HP에서 GBW −36 % 가능), 결합비 α = C_c/(C_c + C_g)(SR 47 → 28 V/µs at 0.1 pF) |

## 8. ⑨ 물리 검증 요약

| 항목 | 값 |
|---|---|
| 물리 결정자 | 상한: 슬루 동안 RC 처짐(t_slew = ΔV/SR), doublet 유수 k f_HP/(β f_u), R_ds 대 R_X 부하, PM. 하한: spec 지표 없음(시동·회복 = 응용 시간) |
| 식/원문 | p.3 2.2절, p.7 3.1절 Fig.5(목적 = 대신호), p.10 식 (13)(원문 소신호 분석은 결합 경로 무시), p.11-12 식 (24), p.13-14 측정 조건. doublet 식 = 2절 유도(Kamath 1974 꼴, 로컬 PDF 없음) |
| 실측 | sky130 tt ngspice-46 전회로(바이어스 재조정 VCP·VCN 0.7, VCM 0.6 V): AC 14경우, 폐루프 tran 소·대신호 각 7경우, 정류 4경우(최장 60주기), 행동 모형 6경우, 13회로 연결 전수 |
| 판정 | f_low 결정자: 틀림(중상). 시간 영역 + AC 상한 유도: 조건부 맞음(중). 하한: spec 지표로는 없음(중상). MOS pseudo-R 정류: 실측 확인(sky130), 원문 공정은 추정 |

## 9. 한계

- sky130은 원문 0.18 µm의 대용이다. f_u·PM·k 수치는 원문과 다르다(k는 g_o/g_m 비라 공정 의존). 원문 공정의 k·R_ds는 미측정이다.
- bench 바이어스는 sky130에서 포화를 맞추려고 VCP·VCN·VCM을 바꿨다(VCP = VCN이라 M21 V_SG = 0).
- 반전 구성은 이상 VCVS 분압(β 1/2, 부하 0)이다. 원문 저항값은 미기재다.
- SR 감도 'SR 변화 ≈ 0.5 × 처짐'은 이 bench 실측이다. 손계산 행은 e_m으로 보수 처리했다.
- 정류 평형점은 60주기 안에 도달하지 못했다(표류 진행 중). 평형 위치는 추정이다.
