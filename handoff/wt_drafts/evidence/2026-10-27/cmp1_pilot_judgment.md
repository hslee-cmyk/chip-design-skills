# CMP-1 시범(O-161) 독립 판정 -- armA(zip gm/ID harness) 대 armC(as-built 엔진 find_front)

## 요약표 (판정자 실측 기준)

| 항목 | A (zip harness) | C (as-built 엔진) | 판정 | 근거 | 확신도 |
|---|---|---|---|---|---|
| spec 통과 two_stage | PASS (27/37 °C; GBW 7.09/7.31 MHz 여유 1.3~4.6 %, PM 73.5, 이득 83, offset_exc 1.11, noise_exc 1.34) | front 0 (최선점 이득 33 dB) | A | 케이스 1-1, 5-1 | 높음 |
| spec 통과 folded | **FAIL** noise_excess_th 2.016 (+0.8 %; armA 보고 1.92 는 자기 식) -- 엔진 평가도 2.015 로 같은 판정 | front 0 (최선점 offset_exc 53) | 둘 다 미달 | 1-2, 4-1 | 높음 |
| 전력 | 136 uW / 22.8 uW (이상 bias 원 제외; folded 값은 W 하한 수동 결정의 산물) | 해 없음 | 비교 불가 | 1, 3 | 높음 |
| 면적 | 2852 / 1139 um^2 | 해 없음 | 비교 불가 | 1 | 높음 |
| 견고성(참고) | two_stage: 기준 가지 구현 시 코너 PASS, 125 °C GBW -15 %; 이상 bias 전압 그대로면 ss/fs/-40 °C GBW FAIL. folded: fs 포화 여유 10 mV | 측정 대상 없음 | A 만 측정 | 2 | 높음 |
| 평가 정확도(같은 점) | harness 이득 -16 dB, folded 잡음식 오류 | armA 점에서 이득 0.4 dB·GBW 2.7 %·offset/noise 1 % 안 | **C** | 4-1 | 높음 |
| 벽시계 / SPICE | 24 분·58 분 / 261·553 회 | 9~150 s 탐색 / 0 회 | C 빠름(결과 없음) | 6 | 높음 |
| 사람/AI 개입 | two_stage 6 건, folded 10 건 + harness 코드 6 건(판정 기준 kcl_tol 완화 포함) | 0 | C | 3, 6 | 높음 |
| 바이어스 구현성 | 이상원(bias 구현 가능 확인, Ibg 수동소자 불가) | 이상원 노드 동일 | 동등 | 3, 5 | 높음 |
| 재현성 | 최종 intent 재실행 바이트 동일, 과정은 비결정 | 4 회 + 판정자 재실행 완전 결정론 | C | 6-1 | 높음 |
| 일반성 | 회로마다 intent 180~200 줄(회로 식) | 선언만 | C | 6 | 높음 |
| (C) front 0 원인 | -- | **엔진 탐색 결함**: GB4 이득 상한 인증 실패 -> 이득 L 하한 비활성 -> 전 소자 최소 L 칸 출발 -> 칸 고정 SLSQP status 4 -> LR10 L 탐색 미기동. armA θ 를 시작점으로 주면 front 1 점 | 엔진 결함(평가식 아님) | 4-2, 4-3 | 높음 |
| 엔진 front(A 시작점)의 SPICE | -- | two_stage 89 uW, GBW 6.28 MHz FAIL(-10 %); folded 2.2 uW PASS 이나 가지 전류 -67 % -- 좁은 폭(5 um 슬라이스 밖)·비대칭 입력쌍 | 모델 오차 미관리 | 5-3, 6-2 | 높음 |

판정자: 독립 판정 agent (작성자≠검증자). 작성자 보고(armA/RESULTS.md, armC/summary.json)는 증거로 쓰지 않고 수치는 전부 다시 쟀다.
판정 도구(판정 전용, 엔진·harness 에 배선하지 않음): `wt/_cmp_pilot/judge/spice_judge.py`, `run_cases.py`, `summarize.py`, 엔진 평가 스크립트는 아래 케이스에 적는다.
원자료: `wt/_cmp_pilot/judge/res/*.json`(케이스마다 1개).

## 0. 측정 방법 (판정자가 정함 -- 작성자 deck 재사용 안 함)

- netlist: armA `sized.sp` 를 읽어 평탄 netlist 로 옮김(W/L `u` 접미사 = 미터, m = 병렬 수 확인). subckt 안에 CL 없음 -> 측정 부하 CL 은 판정 deck 에 1개만(two_stage 3 pF, folded 1 pF, spec `measurement_load`). 이중 부하(F-1/B89 유형) 없음 확인.
- PDK: `C:/pdk/sky130_fd_pr` cells/*/<corner>.pm3 + mismatch.corner + lod (armA 와 같은 파일군, 엔진 LUT 생성 파일과 같은 sha 의 tt). ngspice-46 `ngspice_con.exe -b`, `ngbehavior=hsa`.
- 온도: spec 에 온도 선언 없음. 엔진 LUT = 27 °C(REGEN_REPORT), armA 설계 = 37 °C(intent temp 310.15 K). 공칭 판정은 **27 °C 와 37 °C 둘 다** 적는다.
- 입력 DC: spec `input_dc` 미정(SP-2). armA 가정(two_stage 입력 CM 0.9 V·출력 0.9 V, folded 입력 CM 1.0 V)을 그대로 쓰되, 입력 trim 은 판정 deck 의 DC 서보(L 1e12 H·C 1 F, DC 에서만 닫힘)가 푼다. 서보 목표: two_stage = V(OUT) 0.9 V, folded = V(out) = V(Vg7)(미러 균형점).
- AC: 차동 구동(vin_p +0.5, vin_n -0.5 = 엔진 view 가중), 개루프 이득 = 0.01 Hz 값, GBW = 0 dB 교차(로그 보간), PM = 180 + (위상(fu) - 위상(DC)) (unwrap, beta = 1).
- offset_excess (엔진 정의 `metrics/offset_analysis.py`: 모든 MOS 의 게이트 오차원 sigma_VGS,i 를 DC 전달로 출력까지 보내 합한 분산 / 입력 셀(M1, M2)만의 분산, 근): 모든 MOS 게이트에 직렬 AC 원을 넣어 0.1 Hz 에서 H_i = Vout/Vg_i 측정(서보 무력 주파수), A_dm 은 같은 주파수의 차동 이득. sigma_VGS,i = 소자 단독 bench(회로 OP 의 단자 전압, W·L·mult = m 물리 면적)에서 PDK mismatch `*_slope_spectre` 를 ±1e-6(미터 단위 1 sigma)씩 켜고 dID/gm 으로 변수별 dVGS 를 구해 제곱합 근 (nfet: toxe, voff, vth0; pfet: nfactor, toxe, voff, vth0).
- noise_excess_th (엔진 정의 `metrics/noise_analysis.py`: 열 성분 입력 환산 합 / 입력 셀 열 성분 합, f_lo = 1 Hz): ngspice `.noise` 1 Hz 소자별 기여(V/sqrt(Hz) 진폭 -> 제곱) 중 1overf 를 뺀 열 성분 합 비. 검산: 성분 제곱합 = onoise_spectrum^2 (0.0384267 대 0.0384267).
- 포화: spec `saturation_rule = vds_ge_vdsat`(여유 0) -> |VDS| - |VDSAT(BSIM4 OP)| >= 0. armA 는 자기 기준 50 mV 를 썼다.
- 면적: 엔진 `area_search_m2` 정의 = sum W*L(물리, m 포함) + Cc / camimc(2e-15 F/um^2, PDK 선언) + Rz poly 면적(엔진 PassiveAreaDecl 값 2.259e-15 m^2/ohm + 머리 2.178e-13 m^2). CL 제외.
- 전원 전류: I(V_vdd). 'vb' 모드 = armA 의 이상 bias 전압원 그대로(기준 가지 전류 미포함). 'ref' 모드(two_stage 만) = armA 의견대로 bias 를 M5 와 같은 L·finger 폭의 NMOS 다이오드 1 finger + 이상 기준전류 I5/5 = 1.391 uA 로 구현(기준 가지 전류 포함).

## 케이스 1. (A) 독립 재측정 -- 공칭 tt

원자료: `judge/res/ts_{vb,ref}_tt_{27,37}.json`, `judge/res/fc_vb_tt_{27,37}.json`. SPICE 실행 = 케이스당 op/ac/noise 1 + offset AC 1 + sigma bench 소자 수(7 또는 13).

### 1-1. two_stage_ota (armA r4)

| case | 이득 dB | GBW MHz | PM deg | offset_excess | noise_excess_th | sigma_in mV | 최소 포화 여유 V (소자) | I_vdd uA | P uW | 면적 um^2 | 입력 trim mV | 판정 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| ts_vb_tt_27 (이상 bias 0.6609 V) | 83.3 | 7.09 | 73.6 | 1.114 | 1.346 | 5.55 | 0.105 (M5) | 71.26 | 128.3 | 2852 | 0.12 | 전 spec PASS |
| ts_vb_tt_37 | 83.1 | 7.31 | 73.5 | 1.108 | 1.337 | 5.61 | 0.100 (M5) | 75.67 | 136.2 | 2852 | 0.12 | 전 spec PASS |
| ts_ref_tt_27 (다이오드 기준 가지, Iref 포함) | 83.2 | 7.28 | 73.9 | 1.113 | 1.342 | 5.52 | 0.101 (M5) | 75.45 | 135.8 | 2852 | 0.12 | 전 spec PASS |
| ts_ref_tt_37 | 83.1 | 7.13 | 73.8 | 1.109 | 1.339 | 5.62 | 0.103 (M5) | 75.45 | 135.8 | 2852 | 0.12 | 전 spec PASS |

spec 별 여유(가장 나쁜 공칭 칸 기준): gain 57 dB -> +26.1 dB, GBW 7 MHz -> **+1.3 %**(ts_vb_tt_27 7.09 MHz), PM 70 -> +3.5 deg, offset_excess 1.414 -> +0.30, noise_excess_th 2 -> +0.65, 면적 1.5e-8 m^2 -> 2.85e-9(19 %), 포화(여유 0) -> +0.100 V(M5).

- armA 보고와 비교: 이득 83.1 dB·GBW 7.32 MHz·PM 73.5 deg(37 °C)는 내 측정과 일치. **offset_excess 는 armA 1.295 대 판정 1.11, noise_excess_th 는 armA 1.517 대 판정 1.34** -- armA 는 자기 식(Pelgrom vth0 만, 잡음 gm 비 + 2단 항)을 썼고 엔진 정의(전 MOS, PDK mismatch 변수 4종, LUT/SPICE 열잡음)와 다르다. 두 값 모두 armA 쪽이 보수적이라 결론(PASS)은 같다.
- 면적 2852 um^2 = MOS 2115 + Cc 734 + Rz 3.5. armA 2849(Rz 미포함)와 일치.
- 전원: 이상 bias 전원 모드에서 71.3 uA(27 °C)/75.7 uA(37 °C) -- 같은 bias 전압에서 온도로 6 % 바뀐다. 기준 가지 구현 시 75.45 uA(Iref 1.39 uA 포함, 코어 74.1 uA)이고 온도 무관.
- GBW 여유가 1.3 % 뿐: 7.09 MHz(27 °C, 이상 bias). armA 는 37 °C 에서만 확인했다.
- 포화: 전 소자 PASS. 가장 빠듯한 M5(tail) |VDS| 0.233 V, VDSAT 0.131 V.

### 1-2. folded_cascode (armA r7)

| case | 이득 dB(참고) | GBW MHz(참고) | PM deg(참고) | offset_excess | noise_excess_th | sigma_in mV | 최소 포화 여유 V (소자) | I_vdd uA | P uW | 면적 um^2 | 판정 |
|---|---|---|---|---|---|---|---|---|---|---|---|
| fc_vb_tt_27 | 77.7 | 7.42 | 50.5 | 1.106 | **2.016** | 1.18 | 0.098 (M3/M4) | 12.66 | 22.8 | 1139 | **noise_excess_th FAIL (+0.8 %)** |
| fc_vb_tt_37 | 78.2 | 7.24 | 50.8 | 1.108 | **2.021** | 1.19 | 0.107 (M3/M4) | 12.65 | 22.8 | 1139 | **noise_excess_th FAIL (+1.1 %)** |

- **armA 의 'spec 전부 만족'은 SPICE 로 성립하지 않는다(경계 FAIL)**. 잡음 열 성분 분해(입력쌍 = 1): M3+M4 0.371, M9+M10 0.645, 캐스코드 M5/M6 0.0002, 나머지 0 -> 합 2.016. armA 식 `1 + gm3/gm1 + gm9/gm1` = 1 + 0.547 + 0.366 = 1.913 은 소자마다 같은 열잡음 계수(gamma)를 가정했다. 실제 BSIM4 열잡음은 M9(L 8 um, gm/ID 12.7) 가 M1(L 0.5 um, gm/ID 26, 약반전) 보다 gm 당 1.76 배 크다(0.645/0.366). 엔진 정의(LUT 열잡음 = 같은 SPICE 모델)로는 FAIL. 확신도: 높음(검산 일치, 두 온도에서 같은 방향). 여유가 1 % 라 의미 있는 결함이라기보다 'armA 의 식이 판정 정의와 달라 경계에서 뒤집혔다'는 사례다.
- offset_excess 1.106(armA 1.303) PASS, 면적 1139 um^2 PASS, 포화 PASS(가장 빠듯 M3/M4 0.098 V, armA 보고의 'M6 가장 빠듯'과 다름 -- 27 °C 에서 M3 이 0.098 V).
- 성능(이득·GBW·PM) spec 은 pending(SP-3/4/5)이라 참고만. PM 50.5 deg(CL 1 pF, beta = 1).
- 전력 22.8 uW 에 bias3 생성 가지는 없다(토폴로지 안에 생성 소자 없음). Ibg(이상 전류원 1.577 uA)는 vdd 전류에 포함(MP 가지).

## 케이스 2. (A) 견고성 -- spec 이 코너·온도를 요구하지 않으므로 전부 '참고'

원자료: `judge/res/ts_*.json`, `judge/res/fc_*.json`(코너 파일은 cells/*/<corner>.pm3, 이름은 PDK 파일 이름 그대로. 판정자 실측: `nfet__sf.pm3` 는 nfet 가 빠르고 pfet 가 느리다 -- 이름 순서와 반대이므로 아래 'sf'·'fs'는 파일 이름 표기다). 입력 CM ±50 mV·bias ±10 mV 는 37 °C(armA 설계 온도).

### 2-1. two_stage_ota

| case | 이득 dB | GBW MHz | PM deg | offset_exc | noise_exc | 최소 포화 V (소자) | I_vdd uA | 실패 |
|---|---|---|---|---|---|---|---|---|
| ref ss 27 | 83.0 | 7.08 | 73.2 | 1.108 | 1.322 | 0.078 (M5) | 75.34 | - |
| ref ff 27 | 83.2 | 7.46 | 74.4 | 1.116 | 1.352 | 0.125 (M5) | 75.56 | - |
| ref sf 27 | 81.5 | 7.41 | 72.9 | 1.100 | 1.327 | 0.133 (M5) | 75.59 | - |
| ref fs 27 | 84.7 | 7.10 | 74.9 | 1.126 | 1.350 | 0.070 (M5) | 75.30 | - |
| ref tt -40 | 83.3 | 8.35 | 75.0 | 1.167 | 1.382 | 0.090 (M5) | 75.44 | - |
| ref tt 125 | 82.6 | **5.96** | 73.6 | 1.092 | 1.332 | 0.112 (M5) | 75.45 | **GBW -15 %** |
| ref tt 37 CM -50 mV | 83.6 | 7.07 | 73.9 | - | - | 0.061 (M5) | 75.39 | - |
| ref tt 37 CM +50 mV | 82.6 | 7.16 | 73.7 | - | - | 0.144 (M5) | 75.48 | - |
| vb ss 27 (bias 0.6609 V 고정) | 83.6 | **5.24** | 73.3 | - | - | 0.110 (M5) | 52.05 | **GBW -25 %** |
| vb ff 27 | 82.7 | 9.35 | 74.2 | - | - | 0.100 (M5) | 95.57 | - (전력 +34 %) |
| vb sf 27 | 80.3 | 10.10 | 72.4 | - | - | 0.097 (M5) | 105.77 | - (전력 +48 %) |
| vb fs 27 | 85.1 | **4.70** | 74.7 | - | - | 0.112 (M5) | 46.06 | **GBW -33 %** |
| vb tt -40 | 84.0 | **4.82** | 75.1 | - | - | 0.134 (M5) | 39.70 | **GBW -31 %** |
| vb tt 125 | 81.5 | 8.42 | 73.0 | - | - | 0.060 (M5) | 109.64 | - (전력 +45 %) |
| vb tt 37 bias -10 mV | 83.3 | **6.51** | 73.6 | - | - | 0.113 (M5) | 66.33 | **GBW -7 %** |
| vb tt 37 bias +10 mV | 82.8 | 8.15 | 73.5 | - | - | 0.088 (M5) | 85.80 | - |

- 기준 가지(다이오드 + Iref)로 bias 를 만들면 코너 4종·-40 °C·CM ±50 mV 에서 전 spec 유지, 125 °C 에서만 GBW 5.96 MHz(-15 %). GBW 공칭 여유 1~4 % 라 온도로 gm/ID 가 내려가면 바로 깨진다.
- **armA 가 넘긴 형태(이상 bias 전압 0.6609 V)로는 ss·fs·-40 °C·bias -10 mV 에서 GBW 가 4.7~6.5 MHz 로 FAIL**, 전력은 40~110 uA 로 ±50 % 움직인다. 이 bias 전압 값은 37 °C tt 한 점에서만 맞다.
- 보정계수 k_clm(=0.61) 의 결과: M7/M5 전류비가 설계 9.545 대 실측 9.81~10.02(+3~5 %)로 코너 전부에서 같은 방향 잔차. 보정이 '한 점에서 맞춘 값'이지만 코너로 흔들어도 비율 오차는 5 % 안 -- 판정 기준(±5 %) 경계. spec 판정에는 영향 없음(이득·GBW·PM 은 위 표).
- offset_excess·noise_excess_th 는 코너·온도에 둔감(1.09~1.17, 1.32~1.38).

### 2-2. folded_cascode (bias3 0.3425 V, Ibg 1.577 uA 이상 전원 고정 -- 토폴로지 안에 생성 소자가 없어 기준 가지 모드 없음)

| case | 이득 dB(참고) | GBW MHz(참고) | PM deg(참고) | offset_exc | noise_exc | 최소 포화 V (소자) | Ic uA (설계 2.366) | 실패 |
|---|---|---|---|---|---|---|---|---|
| ss 27 | 72.7 | 7.15 | 49.5 | 1.104 | 2.009 | 0.067 (M3) | 2.351 | noise |
| ff 27 | 80.8 | 7.64 | 51.2 | 1.108 | 2.022 | 0.129 (M3) | 2.415 | noise |
| sf 27 | 79.4 | 7.46 | 48.5 | 1.099 | 1.987 | 0.057 (M3) | 2.321 | - |
| fs 27 | **60.5** | 7.19 | 52.7 | 1.112 | 2.049 | **0.010 (M5)** | 2.450 | noise (M5 포화 경계) |
| tt -40 | 71.8 | 8.69 | 46.7 | 1.096 | 2.031 | 0.037 (M3) | 2.464 | noise |
| tt 125 | 78.7 | 5.90 | 52.5 | 1.135 | 2.083 | 0.125 (M5) | 2.294 | noise |
| tt 37 CM -50 mV | 78.1 | 7.22 | 50.9 | - | - | 0.107 (M3) | 2.384 | - |
| tt 37 CM +50 mV | 78.2 | 7.27 | 50.8 | - | - | 0.107 (M3) | 2.365 | - |
| tt 37 bias3 -10 mV | 77.9 | 7.25 | 51.0 | - | - | 0.114 (M5) | 2.378 | - |
| tt 37 bias3 +10 mV | 78.3 | 7.23 | 50.6 | - | - | 0.099 (M3) | 2.371 | - |

- noise_excess_th 는 sf 코너 하나를 빼고 1.99~2.08 로 경계 FAIL(공칭부터 FAIL).
- 포화는 전 칸 유지(spec 여유 0 기준)지만 fs 코너에서 M5/M6(PMOS 캐스코드) 여유 10 mV, 이득 78 -> 60.5 dB. bias3 를 고정 전압으로 두었기 때문(X 노드가 코너로 움직임).
- 보정계수 c_mp(1.0286)·c_mn(0.9907)의 효과: 접힘 가지 전류 Ic 가 코너·온도로 2.29~2.46 uA(-3 % ~ +4 %). 보정 크기(약 3 %)가 코너 변동과 같은 크기라, '그 격자점에서만 맞춘 보정'이지만 결과를 깨지는 않는다. 다만 이 견고성은 Ibg·bias3 가 이상 전원이라 생긴 것이다(실제 기준 회로의 코너 변동은 포함되지 않음).
- CM ±50 mV·bias3 ±10 mV 에는 둔감.

## 케이스 3. (A) 판정 기준 변경·수동 결정의 영향

| 수동 결정 | 무엇을 바꿨나 | 결과에 미친 영향 | 판정자 평가 | 근거 |
|---|---|---|---|---|
| kcl_tol 1e-6 -> 1e-4 (two_stage r2 부터, folded 처음부터) | harness 의 'gate/bulk 전류' 검사 허용치 | r4 최종점의 max \|Ig\|,\|Ib\| = 1.47e-10 A -- 옛 허용치(4.5e-12 A)로는 **최종점도 FAIL** 이었다. 즉 r4 의 'DC PASS'는 이 완화에 기대고 있다 | 완화 자체는 물리적으로 타당: KCL 잔차는 4e-21 A 이고 걸린 것은 큰 W 소자 드레인-벌크 접합 누설(I5 의 2e-5). 검사기가 '정상 누설'과 'KCL 위반'을 한 칸에 섞은 결함. 다만 **작성자가 판정 기준을 직접 바꾼 사례**라 작성자≠검증자 원칙상 표시 대상 | `armA/harness/out/two_stage_r{1,4}/physics_check.md` |
| W 하한(folded: r1 0.42 um -> r2 2 um -> r6 5 um) | 소자 폭 탐색 하한 | 전력이 하한으로 정해짐: r1 0.45 uA 해 -> r7 12.62 uA(28 배). spec 에 성능 제약이 없어(SP-3/4/5 pending) 최소 전력점은 '하한 + 격자 상한 + 잡음 가드'가 정한다 | 결과 전력은 설계 판단이 아니라 **LUT 폭 기준(W_ref 5 um)에 맞춘 작성자 선택**의 산물. 두 방식의 전력 비교에 쓰면 안 된다 | `armA/RESULTS.md` 케이스 2 표, `fc_r1/sized.sp` |
| k_clm = 0.61 (two_stage) | 미러 CLM 오차 식 계수를 r1 SPICE 한 점에 맞춤 | M7/M5 비 잔차 +3.5 %(공칭) ~ +5 %(코너). spec 판정은 유지 | 한 점 보정이지만 효과는 작다. 일반 규칙 아님 | 케이스 2-1 |
| c_mp = 1.0286, c_mn = 0.9907 (folded) | MP·MN 크기를 r6 SPICE 실측 비로 보정 | Ic 오차 +7.9 %(r6) -> +0.4 %(r7). 코너 변동 ±4 % 와 같은 크기 | 같은 격자점 전용(작성자 명시). 다른 점·다른 회로로 옮길 수 없다 | 케이스 2-2, `armA/harness/intents/folded_cascode_armA.yaml:48-49` |
| 잡음·offset 식(intent YAML) | spec 정의 대신 작성자 식 | two_stage: 보수적(1.517 대 판정 1.34). folded: **낙관적(1.92 대 판정 2.02 -> 경계 FAIL)** | gamma 를 소자 공통으로 둔 단순식이 spec 정의(소자별 열잡음)와 다르다 | 케이스 1-2 |
| GBW 식 교체(two_stage r3 -> r4) | gm1/(2 pi Cc) -> p2 포함 0 dB 교차식 | 공칭 37 °C 에서 7.32 MHz(여유 4.6 %), 27 °C 7.09 MHz(1.3 %) | SPICE AC 를 보고 고친 식. 타당하나 37 °C 한 점 확인 | 케이스 1-1 |

### 이상 전원의 구현 가능성

| 전원 | 값 | 판정자 측정 | 평가 |
|---|---|---|---|
| bias (two_stage) | 0.6609 V | M5 단위 finger 다이오드 + Iref 1.391 uA 로 바꾸면(ts_ref) bias 0.6638 V(27 °C), 전 spec 유지, Iref 포함 전류 75.45 uA | **구현 가능(확인)**. 단 armA 가 넘긴 '이상 전압' 그대로는 코너·온도에서 GBW FAIL(케이스 2-1) -- 구현 형태(전류 기준)까지 결과물로 넘겨야 한다. Iref 의 출처(기준 회로)는 범위 밖 |
| bias3 (folded) | 0.3425 V | ±10 mV 에 둔감, fs 코너에서 M5 포화 여유 10 mV | 구현 가능하나 **토폴로지 밖 별도 가지와 그 전류**가 필요(전력 22.8 uW 에 미포함). 생성 회로를 넣으면 X 노드 추종형(예: 캐스코드 복제)이어야 코너 견고 |
| Ibg (folded, vb1 -> vb2) | 1.577 uA | V(vb1) 0.544 V < V(vb2) 0.595 V(27 °C): 양단 -51 mV | **수동소자로 불가**(armA 지적과 일치: 낮은 전위 -> 높은 전위로 전류). 별도 기준 2가지(PMOS·NMOS 미러) 필요. topology 도 implementable:false |
| 입력 trim | 0.12 mV (two_stage), 0 (folded) | 판정 서보 결과 같음 | 계통 offset 작음. 바이어스 아님 |

### W 하한 0.42 um 해(folded r1)가 SPICE 에서 깨진 물리

- r1 은 MP W 0.986 um, M3 W 0.539 um(같은 L 4 um)로 미러비 0.546 을 의도했다. SPICE: I3 186.7 nA(의도 117.7 nA, +58.6 %).
- 판정자 bench(`judge/t0/wbench.sp`, pfet L 4 um, 같은 VSG): |VTH| = 0.895 V(W 0.54 um), 0.956 V(W 0.99 um), 1.029 V(W 5 um). **역 좁은 폭 효과(inverse narrow-width effect, sky130 pfet bin 별 VTH)로 좁은 소자일수록 |VTH| 가 60~130 mV 낮다**. 같은 VSG 에서 단위폭 전류가 W 0.54 um 소자는 W 0.99 um 소자의 2.9 배(약반전이라 지수적으로 커짐).
- LUT 는 W_ref 5 um 한 폭이라 W/L 비례(단위폭 전류 일정)를 가정 -> 폭이 다른 미러는 비가 틀린다. 게다가 캐스코드 가지 전류 Ic = I3 - I1 이 차이 전류(설계 10 nA)라 I3 의 +58.6 % 가 Ic +714 % 로 증폭(fold 민감도 = I3/Ic ≈ 11.8).
- 결론(확신도 높음): r1 실패는 'LUT 폭 축 부재 + 차이 전류 증폭'의 결합. W 하한 5 um 은 이 결함을 피한 우회이지 해결이 아니다. 엔진은 LUT 폭 슬라이스 32개(0.36~7 um)를 갖고 있어 이 효과를 표에서 읽는 구조다(`lut_v2_location.json`).

## 케이스 4. (C) front 0 의 원인 판정 -- 엔진(integ-it12 @ 68b4e234)을 import 해 실행만 함, 수정 없음

판정 도구: `judge/engine_probe.py`(armC `run_engine.py` 와 같은 사슬로 sctx 를 만들고 `search.kernel.evaluate`·`find_front` 를 부름), `judge/engine_ycal.py`(θ 의 y 를 이분해 입력 DC 를 맞춤), `judge/engine_start.py`(graph/start 필드 읽기). 원자료 `judge/res/engine_*.json`. 실행 전후 `git -C integ-it12 status --short` 빈 출력(변경 없음).

### 4-1. (A) 의 해를 엔진 θ 로 옮겨 엔진 평가 함수로 평가

옮기는 법: θ 성분 = L(M1, M2, M3, M5, M6), Cc, current(M3 = I1, M4 = I2, M6 = I7), ln_idu = ln(I·L/W)(armA W·L, SPICE 27 °C 전류), y(OUT) = 0.5(0.9 V), y(vin_p) 는 입력 0.9 V 가 되게 이분(0.2207). 엔진 LUT 는 27 °C·폭 슬라이스 5 um(armA finger 폭과 같음).

| 항목 | 엔진 평가(armA 점) | 판정자 SPICE(ts_ref_tt_27) | 차 |
|---|---|---|---|
| 상태 | **sealed, 모든 제약 행 c > 0 (feasible), 최소 c = 0.888(GBW)** | 전 spec PASS | -- |
| gain_ss_db | 83.57 | 83.2 | +0.4 dB |
| gbw_ss_hz | 7.47 MHz | 7.28 MHz | +2.7 % |
| pm_ss_deg | 73.0 | 73.9 | -0.9 deg |
| offset_excess | 1.120 | 1.113 | +0.6 % |
| noise_excess_th | 1.359 | 1.342 | +1.3 % |
| 전력 | 133.3 uW(이상 bias 원 제외) | 133.3 uW(코어 74.06 uA × 1.8) | 일치 |
| M7 W(엔진 유도) | 230.8 um | armA 229.8 um | +0.4 % |
| bias 노드 | 0.6635 V | 0.6638 V | 0.3 mV |

folded_cascode 도 같은 방식(θ 26 성분, y 3개를 vin_p 1.0 V·Y 1.4992 V·out 1.2686 V 로 이분): 엔진 sealed, **noise_excess_th = 2.015 -> c = -0.042 (위반)**, offset_excess 1.188(판정 SPICE 1.106), 면적 1.157e-9. 즉 엔진도 armA folded 해를 잡음 가드 위반으로 판정한다 -- 케이스 1-2 의 SPICE 판정(2.016)과 일치(독립 두 경로의 일치, 확신도 높음). offset_excess 는 엔진이 7 % 비관적(M9/M10 sigma_VGS 엔진 1.11 mV 대 판정 bench 0.67 mV -- 원인 미확정, 결론에는 영향 없음).

**결론: 엔진 평가 함수(DC 정본·봉인·ss metric)는 (A) 의 해를 정확히(이득 0.4 dB, GBW 3 %, offset·noise 1 % 안) 재고 feasible 로 본다. front 0 은 평가식 문제가 아니다.** -> 후보 (c) gain_ss 손계산식 오차는 기각(armC 최선점에서도 엔진 33.0 dB 대 SPICE 33.4 dB, 케이스 5).

### 4-2. (A) 의 해를 시작점으로 주면 엔진은 front 를 낸다

`find_front(sctx, [armA θ])`(예산 2000, 벽시계 260 s): **front 1 점**. 층 0 시작점 s1 은 armC 와 똑같이 power·area 모두 `slsqp_4` 로 실패(같은 수락 5·4 회 -- 재현), 주어진 시작점 s2 에서 LR10 L 칸 탐색이 돌아 수락 3 회 후 평가 예산에서 멈춤. front 점: 전력 89.2 uW(armA 133 uW 의 67 %), 면적 6.56e-10 m^2(armA 의 23 %), GBW 7.003 MHz·PM 70.0 deg 가 활성 경계. (이 점의 SPICE 결과는 케이스 5.)

### 4-3. 원인 사슬 (실측)

armC 의 S3 기록(`%TEMP%/cmpC_two_stage_ota_b2000v4_*/s3/*/evals.jsonl`, 107 평가)과 graph/start 필드를 읽은 결과:

1. **출발 구간의 이득 L 하한이 꺼져 있다**: `graph/start: inactive` = `gain_l_6.4_1: u9_value_not_certified`. GB4 블록 이득 상한표(`graph/ach: gain_checks`)가 두 블록 모두 `status unknown, reason grid_product_over_budget`(격자 곱 1.7e22·1.9e9 가 인증 예산 초과) -- 인증 못 한 A_max 때문에 이득으로 L 을 올리는 규칙이 비활성.
2. 그래서 **모든 소자 L 이 LUT 최소 L 칸(0.15~0.18 um)에서 출발**: `start.row` 의 `l_chosen` = 1.5e-7(M1~M7 전부), 출발 사다리 칸 6개 모두 L 칸 0(folded 는 7개 모두 칸 0).
3. 그 칸 안에서 2단 이득은 33~35 dB 가 상한(층 0 출발점 gain c = -2.86, 107 평가 전부 L ≤ 0.18 um, 최선 33.0 dB). 57 dB 는 **그 칸 안에서 도달 불가**.
4. SLSQP 는 L 칸을 고정한 채 연속 변수만 움직인다 -> 선형화 제약이 양립 불가(`slsqp_4`), 큰 걸음이 LUT 정의역 밖(VDS 0, W 2.4e-10 m)으로 나가 `candidate_failure`(lut_query_failed 2, lut_mismatch_no_block 3).
5. 받아들일 점이 하나도 없으니 **L 칸을 바꾸는 LR10 L 탐색이 시작조차 안 한다**(`l_search stops: []`). -> front 0.
6. folded 도 같은 형태: `inactive` = gain_l(제약 미선언), speed(GBW 목표 없음), current_from_macro(단 전류 없음) -> L 0.15 um·W 0.42 um·전류 pA~nA 의 퇴화 출발점(`start.row`), SLSQP 21 수락 뒤 slsqp_4. 최선점은 M1 W 18,030 um·M11 W 24,380 um(L 0.15 um, VGS 0.29~0.39 V 약반전 극단), offset_excess 53(엔진)·40(SPICE).

### 4-4. 후보별 판정

| 후보 | 판정 | 근거 | 확신도 |
|---|---|---|---|
| (a) vin_p 독립 θ·vin_n = M1 VGS 인 입력 DC 미정(SP-2)이 만든 입력쌍 전류 비대칭 | **근본 원인 아님, 그러나 별도 결함(해의 질)** | 층 0 출발점은 대칭(I3 = I4 = 0.90 uA). 비대칭(0.33 대 11.1 uA)은 SLSQP 가 칸 0 안에서 움직이며 생겼다. 다만 armA 시작점에서 엔진이 찾은 **front 점도 비대칭**(I1 3.13 대 I2 1.55 uA, L1 0.174 대 L2 0.238 um, vin_p - vin_n = -8.4 mV): 입력 DC 두 개가 독립이고 계통 offset 제약이 없어 탐색기가 입력쌍 불균형을 전력 절감에 쓴다. SPICE 에서 이 점은 trim +46 mV 가 필요(케이스 5) | 높음 |
| (b) 미러 전류 미결속 | 근본 원인 아님 | M3/M4 전류가 별도 θ 이지만 W 로 비가 정해지는 유효한 비율 미러. armA 점(I3 = I4)도 같은 θ 공간 안의 점이고 엔진이 feasible 로 봤다 | 높음 |
| (c) gain_ss 손계산식 오차 | **기각** | armA 점 83.57 대 SPICE 83.2 dB, armC 최선점 33.0 대 33.4 dB | 높음 |
| (d) 탐색기(SLSQP status 4) | **직접 증상**(원인의 마지막 고리) | L 칸 고정 SLSQP 가 도달 불가 칸에서 실패, 실패 뒤 대안 출발점·칸 전환 없음 | 높음 |
| (e) 기타 = **출발 구간 L 선택(이득 L 하한 비활성) + L 칸 탐색이 feasible 점을 전제** | **근본 원인** | 4-3 의 1~5. 같은 엔진에 armA θ 하나만 주면 front 가 나온다(4-2) | 높음 |

정리: **(C) 의 front 0 은 엔진 결함이다(spec 은 성립 -- armA 해를 엔진이 feasible 로 평가).** 결함 위치는 평가가 아니라 탐색의 출발: GB4 이득 상한 인증 실패 -> 이득 L 하한 비활성 -> 최소 L 칸 출발 -> 칸 고정 SLSQP 실패 -> L 탐색 미기동. 

### 4-5. graph 단일 정본 규칙(프로젝트 CLAUDE.md) 점검 -- 원인 판정 범위 안

| 점검 | 결과 | 근거(실측/읽기) |
|---|---|---|
| 같은 값의 둘째 생산자 | 발견 못함 | `start.row`·`graph/start` writer = `start_intervals` 하나, 층 0 은 READS(`layer0_center.py` docstring·`_box_centre`) |
| 새 cache·사본 | 발견 못함 | 판정 범위(출발·층 0·kernel.evaluate)에서. kernel 의 `sctx.cache` 는 기존 승인 구조(평가 캐시) |
| 계산값 미소비 | **관찰**: `gain_checks.found_db`(블록별 실측 최대 이득 61.2·67.7 dB)는 계산되지만 인증 실패 시 출발 L 결정에 쓰이지 않는다. 규칙 위반은 아니나 '계산하고 버리는 값' | `engine_two_stage_ota_start.json` gain_checks |
| 확인 안 한 것 | slsqp_outer·LR10 내부의 필드 소유 | 범위 밖(자기보고 아님, 안 함) |

## 케이스 5. 엔진 점의 SPICE 재측정 (엔진 예측 대조)

판정 전용 변환 `judge/eng2spice.py`(엔진 -> oracle 어댑터가 없어 판정자가 만든 일회용 도구, **엔진에 배선하지 않음**): 엔진 스냅샷의 소자 W(총폭)·L·핀·벌크·수동소자 값 -> netlist, finger = round(W / 5 um)(엔진 레이아웃 전 폭 슬라이스 5 um), bias 게이트 노드 = 엔진 노드 전압 이상원, 입력 = vin_n 엔진 값 + vin_p 서보 trim(spec `free` 모드), 서보 목표 = 엔진 출력 노드 전압, CL = spec 측정 부하. 실행 `judge/run_engpts.py`, 원자료 `judge/res/eng_*.json`·`eng_*_cmp.json`, 변환 netlist `judge/conv/*.sp`.

### 5-1. armC two_stage 최선점(b2000v4, 최대-최소 c, front 아님)

| 항목 | 엔진 | SPICE | 비고 |
|---|---|---|---|
| gain_ss_db | 33.0 | 33.4 | 손계산식 정확 -> (c) 기각 근거 |
| gbw_ss_hz | 37.6 MHz | 31.4 MHz | -17 % |
| pm_ss_deg | 30.1 | 40.5 | |
| offset_excess | 1.645 | 1.669 | |
| noise_excess_th | 1.347 | 1.444 | |
| 전력 | 346 uW | 349 uW | |
| I(M1) | 0.334 uA | 0.679 uA (+103 %) | W 4.2 um, L 0.15 um 소자 -- 폭 5 um 슬라이스 밖 |
| 입력차 vin_p - vin_n | +30.0 mV(엔진 θ) | 서보 trim +0.78 mV(vin_n 기준) | 비대칭 쌍이 만든 계통 입력차 |

spec 판정: gain FAIL(-24 dB), PM FAIL. 엔진 판정과 같은 결론(최선점도 infeasible).

### 5-2. armC folded_cascode 최선점

| 항목 | 엔진 | SPICE | 비고 |
|---|---|---|---|
| offset_excess | 53.4 | 40.2 | 둘 다 FAIL(가드 1.414) |
| noise_excess_th | 2.567 | 측정 실패(.noise 의 OP 재계산 비수렴) | 엔진 FAIL |
| 접힘 가지 전류 I(M5)~I(M10) | 0.79·1.51 uA | 0.057·0.078 uA (**-93~-95 %**) | 차이 전류 붕괴 |
| I(M3)/I(M4) | 7.03/3.10 uA | 5.44/2.48 uA (-22 %/-20 %) | MP W 0.42 um 대 M3 W 21.9 um, L 0.15 um |
| 전력 | 18.8 uW | 14.8 uW | |

-> **armA r1 이 깨진 것과 같은 물리**(좁은 폭 미러 + 차이 전류 증폭)를 엔진 최선점도 갖는다. 엔진은 레이아웃 전 사이징을 폭 슬라이스 5 um 하나(`pre_layout_lut_access`)로 하고 W 하한 0.42 um 를 허용한다. 폭 효과는 MOD8(레이아웃 뒤 실현 폭) 재평가에서 잡도록 설계돼 있지만, 그 전에 탐색이 W 0.42 um 미러를 고를 수 있다.

### 5-3. 판정자가 armA 시작점으로 돌린 엔진 front 점(two_stage, 케이스 4-2)

| 항목 | 엔진 | SPICE (free, 27 °C, bias 0.859 V 이상원) | spec |
|---|---|---|---|
| gain_ss_db | 77.4 | 75.8 | PASS |
| gbw_ss_hz | 7.003 MHz | **6.28 MHz** | **FAIL (-10 %)** |
| pm_ss_deg | 70.0 | 71.0 | PASS |
| offset_excess | 1.017 | 1.034 | PASS |
| noise_excess_th | 1.352 | 1.416 | PASS |
| 전력 | 89.2 uW | 88.1 uW | -- |
| 면적 | 656 um^2 | 656 um^2 | PASS |
| I(M1)/I(M2) | 3.13/1.55 uA | 2.72/1.73 uA (-13 %/+12 %) | W 1.90/1.26 um(5 um 슬라이스 밖) |
| 입력 trim | vin_p - vin_n = -8.4 mV | **+46.2 mV** 필요 | 계통 offset |
| 최소 포화 여유 | -- | 0.077 V (M5) | PASS |

- 엔진이 GBW 7.003 MHz·PM 70.0 deg 경계에 붙인 점이라 모델 오차 몇 % 로 GBW 가 깨진다. 엔진 스스로도 `DEC-72 judgment_pending: model_error_unmeasured_front_estimated`(모델 오차 미측정 -> 판정 보류)로 표시한다 -- 즉 설계상 SPICE oracle 확인 전 front 는 확정이 아니다(엔진 자기 판정과 일치).
- 오차 원인(실측): 입력쌍 W 1.26~1.90 um 에서 전류 ±12~13 % 오차(5 um 슬라이스 밖) + 일부러 비대칭인 입력쌍(2:1 전류, 서로 다른 L)이 오차를 계통 offset 으로 증폭(-8.4 mV -> +46 mV).

## 케이스 6. 비교표

| 칸 | (A) zip harness (AI 의도 + 격자 전수 + SPICE 보정) | (C) as-built 엔진(find_front, 선언만) | 판정 | 근거 | 확신도 |
|---|---|---|---|---|---|
| spec 통과(SPICE, 판정자 측정) | two_stage **PASS**(27·37 °C, GBW 여유 1.3~4.6 %). folded **FAIL** noise_excess_th 2.016(가드 2, +0.8 %) | 두 회로 front 0 -> 낼 해 없음. 최선점은 엔진·SPICE 모두 FAIL | A 우세(two_stage), folded 는 둘 다 미달 | 케이스 1, 5 | 높음 |
| 전력 | two_stage 128~136 uW(이상 bias, 27/37 °C), 기준 가지 포함 135.8 uW. folded 22.8 uW(bias3 생성 가지 제외) | 해 없음. (판정자가 A 를 시작점으로 주면 엔진 front 89 uW -- SPICE GBW -10 % FAIL) | 비교 불가(C 해 없음). 엔진은 A 근처에서 전력 33 % 낮은 점을 찾지만 경계에 붙어 SPICE 미통과 | 케이스 1, 4-2, 5-3 | 중간 |
| 면적 | 2852 / 1139 um^2 (spec 19 % / 11 %) | 해 없음 (위 엔진 front 656 um^2) | 비교 불가 | 같음 | 중간 |
| 견고성(참고, spec 미요구) | two_stage: 기준 가지 구현 시 코너 4·-40 °C·CM ±50 mV PASS, 125 °C GBW -15 %. **이상 bias 전압 그대로면** ss·fs·-40 °C·bias -10 mV 에서 GBW FAIL. folded: 공칭부터 noise 경계 FAIL, fs 코너 M5 포화 여유 10 mV | 해 없음. 엔진에 코너·온도 축 없음(LUT tt 27 °C 하나) | A 만 측정 가능. 둘 다 코너를 설계 입력으로 쓰지 않음 | 케이스 2 | 높음 |
| 벽시계·SPICE 횟수 | two_stage 약 24 분(harness 782 s, 4 회), folded 약 58 분(2,782 s, 7 회 + 진단 2). SPICE 261 + 553 | 30~127 s/회(two_stage 9 s·folded 97~150 s 탐색), SPICE 0(oracle 미실행: front 없음) | C 가 수십 배 빠르나 결과 없음. A 시간의 대부분은 사람/AI 의 intent 수정 반복 | armA/RESULTS.md 표, armC/run_walls.txt, summary.json | 높음 |
| 사람/AI 판단 개입량 | two_stage: 판정 기준 변경 1(kcl_tol), 보정계수 1(k_clm), 제약 추가 1(mirror_err), 후보 격자 변경 1(M5 L), 식 교체 1(GBW), intent 식 작성(잡음·offset·헤드룸·Rz). folded: W 하한 3 회(0.42 -> 2 -> 5 um), fold_sens 제약 3 회(<=3, <=2, <=3), 바디효과 식 1, 재매개 1(Ic = kc·Itail/2), gm/ID·L 격자 변경 2, 보정계수 2(c_mp, c_mn), 헤드룸 식 m >= 0.1. harness 코드 수정 6 건 | 0(선언 spec·topology + 테스트 픽스처 설정값). 판정자가 시작점 1 개를 넣은 실험은 사람 개입 1 에 해당 | C 우세(개입 0) -- 단 결과 0 | RESULTS.md 반복 표, intent YAML 주석 | 높음 |
| 바이어스 구현성 | 이상 전압 bias(구현 가능 확인), bias3(별도 가지 필요), Ibg(-51 mV, 수동소자 불가) | 엔진도 bias·bias3 노드를 이상원 θ/유도값으로 둔다(armC 최선점 bias3 1.327 V). Ibg 는 MP 전류로 묶임 | 같은 한계(둘 다 바이어스 생성 회로를 설계하지 않음) | 케이스 3, 5 | 높음 |
| 재현성(같은 입력 -> 같은 결과) | harness 는 결정론(격자 전수) -- 판정자 재실행 결과: (아래 6-1). 그러나 **과정**(intent 수정·보정계수·W 하한)은 AI 판단이라 같은 출발에서 같은 경로가 보장되지 않음 | **결정론 확인**: armC b2000 v1~v4 4 회 모두 같은 평가 수(107 / 744)·같은 정지(slsqp_4); 판정자 재실행에서도 층 0 s1 이 같은 수락 횟수(5·4)로 같은 정지 | C 우세(완전 결정론) | armC/out/*.jsonl, judge/res/engine_two_stage_ota_frontA.json | 높음 |
| 일반성(회로마다 새로 쓰는 것) | 회로마다 intent YAML 180~203 줄: 이득·GBW·잡음·offset·헤드룸·fold_sens·바디효과 식, 소자 역할, 격자, 보정계수, netlist 템플릿, KVL 경로 -- **회로 전용 식과 회로 이름 의존** | topology.json + sizing_spec.json 선언만(회로 식 없음, MNA 로 metric) | C 우세(구조상) | intents/*.yaml, 엔진 metrics/* | 높음 |
| 평가 정확도(같은 점) | harness 근사: 이득 -84 %(67.3 대 83.1 dB), 잡음식 gamma 공통 가정 -> folded 판정 뒤집힘 | 엔진 평가: armA 점에서 이득 +0.4 dB, GBW +2.7 %, offset·noise ±1.3 % | **C 우세(평가식)** | 케이스 4-1 | 높음 |

### 6-1. (A) 재현성 재실행 (판정자 복사본 `judge/hA/`, armA 폴더 미수정)

- 최종 intent(two_stage r4, folded r7)를 판정자 복사본에서 다시 돌림: `sized.sp` **바이트 동일**, armA_counts(격자 점·feasible 수·후보 index) 동일, DC 물리검증 PASS 동일. -> 최종 intent 가 주어지면 harness 는 결정론. 재현 안 되는 것은 intent 를 만드는 과정(AI 판단 11~16 건).

### 6-2. 추가 실측: 엔진을 armA 시작점에서 돌린 folded front 점(케이스 4-2 의 folded 판)

`find_front(sctx, [armA folded θ])` 287 s: front 1 점(시작점 자체는 noise c = -0.042 위반, 엔진이 고쳐 냄). 엔진 예측 대 SPICE(`res/eng_fc_frontA_cmp.json`):

| 항목 | 엔진 | SPICE | spec |
|---|---|---|---|
| offset_excess | 1.105 | 1.028 | PASS |
| noise_excess_th | 1.998 (경계) | 1.549 | PASS |
| 면적 | 105 um^2 | 105 um^2 | PASS |
| 최소 포화 여유 | -- | 0.018 V (M6) | PASS(여유 0 기준, 빠듯) |
| 전력 | 2.88 uW | 2.22 uW | -- (armA 22.8 uW 의 1/10) |
| 접힘 가지 전류 M5~M10 | 0.32~0.34 uA | 0.107~0.112 uA (**-67 %**) | -- |
| I(M3)/I(M4) | 0.66/0.64 uA | 0.47/0.46 uA (-28 %) | MP W 0.97 um 대 M3 W 2.1 um, M9/M10 W 0.51 um |
| 참고 이득/GBW/PM | -- | 60.7 dB / 1.27 MHz / 70.4 deg | 성능 spec pending |

- spec 문언으로는 PASS(가드 3 개 + 포화)지만 **엔진이 의도한 동작점과 SPICE 동작점이 다르다**(가지 전류 1/3). 원인은 케이스 3·5 와 같은 좁은 폭 미러 + 차이 전류. folded 에 성능 spec 이 없어 '전력 최소'가 W 하한 근처 극소 전류로 가고, 그 영역에서 5 um 슬라이스 LUT 가 틀린다. armA 는 같은 함정을 W 하한 5 um 수동 결정으로 피했다.
- 입력쌍 비대칭(I1 0.324 대 I2 0.313 uA, L1 0.38 대 L2 0.35 um, vin_p - vin_n = +4.6 mV) 도 다시 나타남.

## 케이스 7. 결론 -- 무엇이 진짜 더 나은가

| 항목 | 판정 | 근거 | 확신도 |
|---|---|---|---|
| 지금 쓸 수 있는 해를 내는가 | **A**. two_stage 는 SPICE 로 전 spec 통과. folded 는 경계 FAIL(noise 2.016) -- armA 보고 'spec 전부 만족'은 틀림 | 케이스 1 | 높음 |
| 평가(같은 점을 얼마나 정확히 재나) | **C**. 엔진 평가는 armA 점에서 SPICE 와 이득 0.4 dB·GBW 3 %·offset/noise 1 % 안. harness 근사는 이득 -16 dB, 잡음식 gamma 공통 가정으로 folded 판정을 뒤집음 | 케이스 4-1, 1-2 | 높음 |
| 탐색(선언만으로 해를 찾나) | **C 실패(엔진 결함)**. 이득 L 하한 비활성 -> 최소 L 칸 출발 -> 칸 고정 SLSQP 실패 -> L 탐색 미기동. A 는 사람이 L·gm/ID 격자를 정해 우회 | 케이스 4-3 | 높음 |
| 시작점이 주어졌을 때의 국소 최적화 | C 가 A 보다 전력 33 %(two_stage)·87 %(folded) 낮은 점을 찾음. 단 경계에 붙고 폭 효과 오차로 two_stage 는 SPICE GBW -10 % FAIL, folded 는 가지 전류 -67 % | 케이스 4-2, 5-3, 6-2 | 높음 |
| 사람 개입·재현성·일반성 | **C**(개입 0, 완전 결정론, 선언만). A 는 회로마다 180~200 줄 intent 와 11~16 건의 수동 결정, 과정 재현 불가(최종 intent 재실행은 바이트 동일) | 케이스 3, 6 | 높음 |
| 견고성 | 둘 다 설계 입력에 코너·온도 없음. A two_stage 는 기준 가지로 구현하면 견고, 이상 bias 전압 그대로면 코너 FAIL | 케이스 2 | 높음 |
| 바이어스 구현성 | 동등(둘 다 이상원으로 남김, Ibg 는 수동소자 불가) | 케이스 3 | 높음 |

### C 가 A 에서 가져와야 할 것

1. **이득으로 L 을 정하는 출발**: A 는 '이득이 필요하면 L 을 길게'를 격자 선택으로 넣었다. 엔진은 같은 규칙(gain_l_bounds §6.4-1)을 갖고 있으나 GB4 인증 실패 시 꺼진다. 인증 실패여도 `gain_checks.found_db`(이미 계산된 실측 최대 이득)를 쓰거나, 꺼질 때 L 칸 여러 개에서 출발하는 것이 필요하다(설계 결정 사항, 아래 사용자 결정 1).
2. **feasible 점이 없을 때의 L 칸 이동**: A 의 격자 전수는 L 을 이산 후보로 전부 본다. 엔진 LR10 은 받아들인 점이 있어야 돈다 -> 출발 실패 시에도 L 칸을 바꾸는 경로.
3. **실제 폭으로의 확인을 탐색 안으로**: A 가 W 하한 5 um 로 피한 좁은 폭 효과를 엔진은 레이아웃 뒤 MOD8 에서만 본다. 엔진 front 두 점 모두 이 효과로 SPICE 와 어긋났다(-10 % GBW, -67 % 가지 전류). 엔진은 폭 슬라이스 32 개를 이미 갖고 있어 레이아웃 전에도 실제 W 슬라이스를 쓸 수 있다(사용자 결정 2).
4. **SPICE 확인 고리**: A 는 매 회 SPICE 물리검증 + AC 로 식을 고쳤다. 엔진은 DEC-72 oracle 이 front 에만 붙는다 -- front 가 없으면 아무것도 SPICE 로 안 본다. 최선점 진단용 oracle 1 회는 싸다(이 판정에서 1 점 2~5 s).

### A 가 못 하는 것 (C 의 고유 가치)

1. 회로 식 없이 MNA 로 metric 을 정의대로 잰다(spec 정의와 일치). A 는 회로마다 식을 써야 하고 식이 틀리면 판정이 뒤집힌다(folded noise).
2. 결정론·무개입. A 의 결과는 W 하한·보정계수 같은 작성자 선택에 따라 전력이 28 배 바뀐다.
3. 연속 θ 국소 최적화: 같은 출발에서 A 격자보다 낮은 전력점을 찾는다(단 모델 오차 관리가 전제).

### 사용자 결정이 필요한 항목

1. **엔진 결함 수정 방향(출발·L 탐색)** -- 후보: (가) GB4 인증 실패 시 `found_db` 로 이득 L 하한을 근사 활성, (나) 출발 사다리에 L 칸 여러 개를 넣음, (다) 출발 실패 시 LR10 을 feasible 전제 없이 기동. 판정자 권고: (가)+(다). 근거: (가)는 이미 계산된 graph 필드를 소비(새 cache 없음, graph 단일 정본 규칙 준수), (다)는 탐색 구조 문제를 직접 고침. ⚠ (가)는 '인증 안 된 값을 출발에 쓰는' 것이라 EP-7(출발값은 판정 아님) 범위 안에서만 허용돼야 한다. 계획 개정 필요(계획 먼저 원칙).
2. **레이아웃 전 폭 슬라이스 규칙** -- 5 um 하나 고정을 유지할지, 소자 W 에 맞는 슬라이스를 쓸지. 판정자 권고: 실제 W 슬라이스(물리 정합 우선). 원래 설계(MOD8 에서 실현 폭 재평가)와 다름 -> **원래 취지와 다름**으로 보고.
3. **SP-2 입력 DC 와 계통 offset** -- 엔진 front 점이 입력쌍을 일부러 비대칭으로 만든다(two_stage -8.4 mV, SPICE 에서 +46 mV). 선택지: (가) input_dc 를 두 입력 공통값으로 선언, (나) offset_sys_mv 제약 선언, (다) 그대로(비대칭 허용). 판정자 권고: (가)+(나). 태그 없이 물리 조건(같은 DC 입력)으로 막는 방식이라 analog-grammar 금지 원칙과 충돌하지 않는다.
4. **folded 성능 spec(SP-3/4/5)** -- 성능 제약이 없어 두 방식 모두 '전력 최소'가 W 하한·극소 전류로 간다(A 22.8 uW 는 작성자 W 하한의 산물, 엔진 2.2 uW 는 SPICE 와 가지 전류 1/3 차). 이 상태로는 folded 전력 비교가 의미 없다.
5. **온도·코너** -- spec 에 온도 선언이 없다(엔진 LUT 27 °C, armA 37 °C). two_stage GBW 여유가 27 °C 1.3 % 라 온도 선언이 판정을 바꿀 수 있다.
6. **armA folded 결과 처리** -- noise_excess_th 2.016(+0.8 %) 경계 FAIL 을 FAIL 로 기록할지(spec 문언 그대로면 FAIL).

### 판정자 자기 점검(실측/자기보고/안 함)

- graph 정본·G-10·블록 안 재계산: 엔진 코드를 고치지 않아 해당 없음. 원인 판정 범위의 필드 소유만 읽기로 확인(케이스 4-5, 실측 읽기).
- 회로 이름을 엔진 판정 근거로 쓰지 않음: 원인 사슬은 graph/start·S3 기록의 필드 값으로만(실측).
- 판정 도구(`judge/*.py`)는 판정 전용이며 엔진·harness 에 배선하지 않음(절대원칙 '만들면 배선' 의 예외로 판정 근거 생성만 목적 -- 엔진 → oracle 어댑터를 실제로 만들지는 사용자 결정 사항).
- heldout·논문 W/L 표 미사용. armA/armC 폴더·엔진 저장소 미수정(`git -C integ-it12 status` 빈 출력, armA 재실행은 judge/hA 복사본).
- 안 한 것: Monte Carlo offset(정의는 감도식이라 불필요), sf/fs 의미 확인 외 corner lib 체계(`sky130.lib.spice`) 사용, slsqp_outer·LR10 내부 정본 감사.
