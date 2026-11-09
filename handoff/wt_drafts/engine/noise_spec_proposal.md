# 9개 library 회로 잡음 스펙 제안서 (검토용 초안)

작성 2026-10-08. 저장소는 읽기만 했다(이 파일만 새로 씀). 이 문서는 **제안**이다. sizing_spec에 반영된 것은 없다.
현재 계획 상태: `NEW_ENGINE_DESIGN_REQUIREMENTS.md:484` "9회로 잡음·왜곡 스펙 없음"(DEC-96), `design_mod1_lut_mod5_mna.md:43`
"잡음은 7b 이후 제약 metric". 엔진 `gmid_engine/metrics/`에는 잡음 metric이 아직 없다(grep 확인). 그래서 잡음 스펙을
넣는 것은 **범위 변경**이고 사용자 결정이 필요하다(§12).

---

## 0. 공통 근거: sky130 잡음 파라미터(실측·인용)

### 0.1 모델 카드 원문(파라미터 이름·값)
파일: `C:/pdk/sky130_fd_pr/cells/nfet_01v8/sky130_fd_pr__nfet_01v8__tt.pm3.spice`(bin 180개),
`C:/pdk/sky130_fd_pr/cells/pfet_01v8/sky130_fd_pr__pfet_01v8__tt.pm3.spice`(bin 108개). BSIM4 level 54.
아래 값은 **모든 bin에서 같다**(이번에 bin 전수 집계, distinct = 1).

| 파라미터 | nfet_01v8 | pfet_01v8 | 의미 |
|---|---|---|---|
| `fnoimod` | 1 | 1 | flicker = unified 모델(NOIA/NOIB/NOIC, EF). **`KF`/`AF`는 쓰이지 않는다**(카드 값 kf=0, af=1) |
| `tnoimod` | 1 | 1 | thermal = holistic 모델(TNOIA/TNOIB, RNOIA/RNOIB). **γ는 모델 파라미터가 아니다** -- 바이어스 함수로 나온다 |
| `noia` | 2.5e42 | 1.5e42 | flicker 주계수 |
| `noib`, `noic` | 0, 0 | 0, 0 | |
| `ef` | **0.84** | 1.0 | 1/f^EF 지수 |
| `em` | 4.1e7 | 4.1e7 | |
| `tnoia` / `tnoib` | 1.5e7 / 9.9e6 | 2.5e7 / 0 | |
| `rnoia` / `rnoib` | 0.94 / 0.26 | 0.69 / 0.34 | |
| `ntnoi`, `lintnoi` | 1, -1e-7 | 1, -2e-7 | |
| `toxe`(공칭), `epsrox` | 4.148 nm, 3.9 | 4.23 nm, 3.9 | Cox = 3.9·ε0/toxe = **8.33 fF/µm²**(n), **8.16 fF/µm²**(p) |

결론: K_F·γ를 상수로 가정할 수 없다. 필요한 값은 **LUT v2의 잡음 열(이미 ngspice `.noise`로 특성화됨)** 에서 읽는다.

### 0.2 LUT v2에서 읽은 유효 γ와 flicker 계수
출처: `C:/Users/HSLEE/Documents/Todoc/fpga/lut_data/sky130_lut_v2/sky130_nfet_pfet_lut_v2_r2.npz`
(`assets/lut_v2_location.json`이 sha256 고정). 열 `SVG2_1HZ`·`SVG2_HF`(게이트 환산 V²/Hz, 1 Hz·100 MHz),
W_ref = 5 µm, TT 27 °C, 표본점 VS = 0, VDS = 0.9 V.

방법: S_vg(f) = A/f^EF + B 로 두고 A = SVG2_1HZ, B = SVG2_HF − A/(1e8)^EF (EF는 위 카드값).
γ_eff = B·gm/(4kT), K = A·W·L(V²·m², 1 Hz). 100 MHz 점은 fT ≥ ~1 GHz(10배)인 점만 믿는다(그보다 낮으면
Cgd 피드스루로 게이트 환산값이 작게 나온다 -- 긴 L·약반전에서 γ가 0 근처로 떨어지는 것이 그 증상).

| 소자 | 조건(fT ≥ 1 GHz) | γ_eff | K = S_vg(1 Hz)·W·L |
|---|---|---|---|
| nfet | L 0.25–1.0 µm, gm/ID 10–15 | **1.9–2.1** | 1.7e-22 – 3.3e-22 V²m² (L 0.15–0.2: 1.3–1.7e-22) |
| nfet | gm/ID ≈ 20, L ≤ 0.5 µm | 1.5–1.7 | 1.4–2.5e-22 |
| pfet | L 0.15–1.0 µm, gm/ID 10 | **1.0–1.05** | 0.5–1.9e-22 |
| pfet | L 0.25–0.5 µm, gm/ID 15 | 0.77–0.84 | 0.8–1.2e-22 |

ngspice 직접 확인(스크래치, 같은 include·같은 DUT 줄, 1 Hz–1 GHz 스펙트럼):
nfet L 0.5 µm gm/ID 14.8 → 100 MHz γ_equiv 2.16, 1 GHz 1.90 / nfet L 1 µm gm/ID 15.4 → 2.04(100 MHz) /
pfet L 0.5 µm gm/ID 15.3 → 0.84(100 MHz), 0.86(10 MHz) / pfet L 1 µm → 0.81–0.86. LUT 유도값과 일치.

이 문서의 추정에 쓴 대표값: **γ_n = 1.9, γ_p = 0.85**(gm/ID ~15 중반전), **K_n ≈ 2.7e-22, K_p ≈ 1.2e-22 V²m²**,
EF_n = 0.84, EF_p = 1.0. (K'=K·Cox 형식으로는 2.2e-24, 9.8e-25 V²·F.) 이것들은 **손 추정용**이고, 스펙 판정은
엔진이 소자별 LUT 값으로 해야 한다(상수 박기 금지 원칙).

### 0.3 sky130 고유의 구조적 함의(이번 측정에서 나온 것)
1. **γ_n ≈ 2.2·γ_p.** 교과서 2/3 가정(Allen 8kT/3gm)과 다르다. PMOS 입력 + NMOS 거울 부하 구조에서는 부하가
   열잡음을 지배하기 쉽다(ngcc, nmcnr).
2. **NMOS flicker EF = 0.84**: 1/f 성분이 MHz까지 남는다(nfet L 0.5 µm, W 5 µm에서 1 MHz 잡음이 열잡음의 ~7배).
   NMOS 입력 회로의 1/f corner는 WL = 10 µm²에서 ~100 kHz 규모. 적분 잡음의 하한 주파수 의존성은 약하지만
   (f^0.16) **상한 쪽(대역)에 민감**하다.

---

## 1. 측정 지표(metric) 정의 제안 -- 주파수 상수를 새로 만들지 않는 형태

| 이름(제안) | 정의 | 쓰는 곳 |
|---|---|---|
| `noise_th_in_v2hz` | 입력환산 **열잡음 평탄값**(V²/Hz): 소자별 LUT 열 성분 B_i로 MNA 전달함수 환산 합 | 일반 op amp 보고 |
| `noise_fc_in_hz` | 입력환산 **1/f corner**: 입력환산 flicker = 열잡음 평탄값이 되는 주파수 | 일반 op amp 보고 |
| `noise_excess_th` | `noise_th_in_v2hz` ÷ (입력 소자만의 열잡음 하한, 같은 LUT γ로) -- 무차원 | 선택적 가드 제약 |
| `noise_out_int_vrms` | **폐루프** 출력 적분 잡음(Vrms), 선언된 되먹임 β로 루프를 닫고 [f_lo, ∞) 적분 | 파일럿(SC) 제약 |

주파수를 숫자로 고르지 않아도 되도록 평탄값·corner로 정의했다. 적분 하한 f_lo만 필요한데, 제안은
**f_lo = 1 Hz = LUT가 실측한 가장 낮은 점(외삽 없음)**. EF_n = 0.84라 1 Hz→1 kHz로 바꿔도 NMOS flicker 적분은 ~13%만 변한다.

---

## 2. current_reuse_telescopic_ota (파일럿) -- **제약 대상**

### 2.1 출처가 보고한 잡음
Xie & Chen, "A 126uW Current-Reuse Telescopic OTA with Class-AB Output Stage"(로컬 원본
`G:/내 드라이브/work/Todoc/논문모음/A 126uW Current-Reuse Telescopic OTA with Class-AB Output Stage.pdf`).
- Table I: **"Total output noise ≤ 300µV"(스펙), 결과 272µV.**
- Fig. 19(p.18, Cadence 잡음 요약): "Integrated Noise Summary (in V^2) ... Total Summarized Noise = 7.40358e-08"
  → √ = **272 µVrms**. 즉 본문·초록의 "272µV/√Hz"는 단위 오기이고 **적분 출력 잡음(rms)** 이다.
  측정 회로는 loop probe가 있는 폐루프 SC 테스트벤치("telescopic_tb_v18_final"), "No input referred noise available".
  **적분 대역은 논문에 없다.**
- 상위 기여 소자(논문 인스턴스명): M3·M5 각 11.3 %, M7·M8 각 9.77 %, M87·M41 6.87 %, ... 상위 10개 합 69 %.
  논문 인스턴스 번호와 이 프로젝트 topology 이름의 대응은 확인되지 않았다 -- 해석하지 않는다.
- 조건: 0.18 µm, 27 °C, 1.8 V, C1 = C2 = 500 fF, CL = 1 pF, β ≈ 0.48(III.A 식 4), Cc = 500 fF, gm1 = gmn+gmp = 238 µS.

### 2.2 구조 분석(topology.json netlist 기준)
- 입력: 한쪽당 **M1a(pmos)+M4a(nmos)** 가 같은 게이트(Vip)를 공유(current-reuse) → 신호 gm1 = gm_M1 + gm_M4.
- 캐스코드 M2a/b, M3a/b: 소스 축퇴로 기여 무시 가능.
- 꼬리 M6·M7(vdd 쪽), M5(gnd 쪽): 잡음 전류가 양쪽 가지에 똑같이 나뉘어 **공통모드** → 차동 출력에 안 나온다
  (정합 오차만큼만 샌다). CMFB(M36–M40, R1·R2)·바이어스망(M57–M68)도 공통모드 경로.
- **1단은 거울 부하가 없다** → 열잡음은 사실상 입력 소자 4개뿐(이 구조의 장점).
- 2단(class-AB M15/M16, M25/M26 + 레벨시프트 M9·M18 계열): 1단 이득으로 나눠져 입력환산되지만 루프 교차
  주파수 근처에서는 무시 못 한다 → 아래 α로 둔다.

입력환산 차동 열잡음(입력 쌍만):
  S_in,diff = 2·4kT·(γ_n·gm_n + γ_p·gm_p)/(gm_n + gm_p)² = 8kT·γ_avg/gm1, γ_avg = (γ_n gm_n + γ_p gm_p)/gm1.

폐루프 출력 적분(단일 극 루프, 잡음 이득 1/β, ENBW = (π/2)·f_c, f_c = β·gm1/(2π·Cc)):
  **v²_out,OTA = 2·γ_avg·kT/(β·Cc) · (1+α)** -- gm1이 지워지고 Cc·β만 남는다.

flicker(입력 쌍): S_1f,in,diff = 2·[gm_n² K_n/(W_nL_n f^0.84) + gm_p² K_p/(W_pL_p f)]/gm1².

샘플링 kT/C(Cs가 매 샘플 갖는 잡음, Cs/Cf = 1로 출력 전달): v²_samp = 2kT/Cs.

### 2.3 수치(이 회로의 선언값만 사용)
- 선언값: Cs = Cf = 0.5 pF, CL = 1 pF each(sizing_spec), t_lln = 30 ns(sizing_spec settling.linear_s),
  ε_d ≤ 0.1 %의 정착 조건 t_lln·ω_c = 6.9(논문 식 2) → **ω_c = 2.3e8 rad/s, f_c = 36.6 MHz**.
- kT = 4.144e-21 J(27 °C). γ_avg = (1.9+0.85)/2 = 1.375(gm_n = gm_p 가정, 논문 III.A와 같은 분배).
- 입력 쌍만, Cc = 0.5 pF, β = 0.48: gm1 = ω_c·Cc/β = 240 µS, S_in = 1.9e-16 V²/Hz(13.8 nV/√Hz 차동),
  **v²_out = 4.75e-8 V² → 218 µVrms**(β = 0.5면 213 µV). 논문 0.18 µm 결과 272 µV(7.40e-8)와 같은 규모 → 식 검증.
- 샘플링 kT/C: 2kT/Cs = 1.66e-8 V² → **129 µVrms**.
- **flicker(sky130에서 새로 생기는 문제)**: 논문 크기(Wn 2 µm, Wp 6 µm, L 0.18 µm, K_n 1.5e-22, K_p 6e-23 @ L 0.18)로
  1 Hz–(π/2)f_c 적분하면 출력 9.5e-8 V² ≈ **308 µVrms -- flicker 하나가 300 µV를 넘는다.** sky130에서는 입력 소자
  면적(W·L)이 잡음 스펙의 실제 결정 변수가 된다(NMOS EF 0.84 때문). 0.18 µm 논문 크기를 그대로 못 쓴다.

### 2.4 잡음 예산(정확도와의 일관성)
- ε_d ≤ 0.1 % → N = log2(1/ε_d) = 9.97 ≈ **10 bit** 정확도.
- 같은 해상도의 양자화 잡음과 같은 크기까지 열잡음을 허용(총 잡음 ≤ V_FS/(2^N·√12))하는 통상 예산을 쓰면,
  V_FS(차동) = 2.4 V(논문 Table I 출력 스윙 스펙 ±1.2 V -- **사용자 채택 기록 없음**, §12-3)일 때 총 677 µVrms.
  샘플링 kT/C 129 µV를 빼면 **OTA 허용 = √(677² − 129²) = 664 µVrms**.
- 논문 스펙 300 µV는 이 상한보다 2.2배(진폭) 엄격하다.
- 필요한 최소 Cc(열잡음만, β 0.48): 300 µV이면 Cc ≥ 0.26 pF(α=0) / 0.38 pF(α=0.45, 논문 상위 10개 외 31 %를
  α 참고치로 쓴 경우); 664 µV이면 Cc ≥ 0.054–0.078 pF(θ 하한 0.1 pF보다 작다 = 사실상 비구속).

### 2.5 제안
- metric: `noise_out_int_vrms`(폐루프 차동 출력, 증폭 위상, β = 선언된 feedback {Cf1, Cf2}, OTA 소자 잡음만,
  [1 Hz, ∞) 적분, thermal + flicker 전부, LUT 소자별 값).
- **값 후보 A(유도, 기본 제안): ≤ √((V_FS/(2^N√12))² − 2kT/Cs)**, N = ⌈log2(1/ε_d)⌉ -- 식 자체를 선언하고 값은
  계산(ε_d·V_FS·Cs 선언을 참조, 숫자 박지 않음). V_FS = 2.4 V이면 664 µVrms. Cc만 보면 비구속이지만
  **flicker(입력 면적)는 구속**한다(§2.3: 논문 크기면 308 µV) → 의미 있는 제약.
- **값 후보 B(논문 앵커): ≤ 300 µVrms** -- 같은 회로·같은 커패시터·같은 정착 목표의 원 스펙. Cs/Cf/CL/정착처럼
  "논문 값 채택"으로 사용자가 확정할 때만. 이 경우 Cc ≥ 0.26–0.38 pF와 입력 면적 증가가 같이 걸린다.
- 신뢰도: 식·규모 **높음**(논문 272 µV와 독립 추정 218 µV 일치), α·flicker 크기 **중간**(ngspice 폐루프 `.noise` 필요).
- 기존 topology `sizing_roles.metrics.noise_v_rthz`(flicker_plus_thermal_sum, M1a·M4a, 단위 V/√Hz, 주파수 미정)는
  주파수가 없어 판정 불가 -- 위 metric으로 대체 제안(대체 시 옛 선언 삭제).

---

## 3. two_stage_ota (Maloberti p.28-33) -- 보고 전용 제안

1. 출처: Maloberti *Layout of Analog CMOS IC* worked example(레이아웃 강의) -- **잡음 미보고**(목적이 레이아웃).
2. 구조: 입력 M1/M2(nmos, 꼬리 M5), 거울 부하 M3/M4(pmos), 2단 M6(pmos CS)/M7(nmos 전류원). 꼬리 M5는 공통모드.
   2단 잡음은 A1²으로 나뉜다(저주파).
   S_th,in = (8kT·γ_n/gm1)·[1 + (γ_p/γ_n)·(gm3/gm1)].
   S_1f,in = 2K_n/(W1L1 f^0.84) + 2K_p·(gm3/gm1)²/(W3L3 f).
   GBW = gm1/(2π·Cc) → gm1 = 2π·7 MHz·Cc(gbw_target_hz 7 MHz 사용자 확정, CL 3 pF, Cc는 엔진).
3. 추정: Cc 0.66 pF(Allen의 PM 60° 기준 Cc ≥ 0.22·CL을 예시로 사용 -- PM은 SP-3 대기라 예시일 뿐) → gm1 = 29 µS,
   gm3/gm1 = 0.67–1 → **53–56 nV/√Hz**; Cc 1 pF → 43–46 nV/√Hz. NMOS 입력이라 1/f corner가 높다
   (W1L1 = 10 µm² 예에서 ~125 kHz).
4. 제안: 잡음 응용이 출처에 없으므로 **제약 없음, `noise_th_in_v2hz`·`noise_fc_in_hz` 보고**.
   가드가 필요하면 `noise_excess_th ≤ 2`(부하 잡음 ≤ 입력 잡음; §12-4). 신뢰도 중간(Cc·gm 비가 엔진 결과에 의존).

## 4. two_stage_ota_sf (Allen L26 p.26-5) -- 보고 전용(two_stage_ota 상속)

1. 출처: Allen Lecture 26 p.26-5 -- 잡음 언급 없음(강의 PDF 전문 검색: 'noise'는 p.26-22 lateral BJT의 "reduces 1/f noise"뿐).
2. 구조: two_stage_ota + NMOS 소스 팔로워 M8(전류원 M9). 팔로워 출력잡음 4kT(γ_n gm8 + γ_n gm9)/(gm8+gmbs8)²은
   입력환산 시 (A1·A2)²로 나뉘어 무시 가능 → **입력환산 잡음은 two_stage_ota와 같다**.
3. 추정: §3과 같음.
4. 제안: 기존 `inherits` 관례대로 two_stage_ota의 잡음 선언을 참조(`value_from_file`), 별도 값 없음.

## 5. folded_cascode (Maloberti p.34-38) -- 보고 전용

1. 출처: Maloberti 레이아웃 예제 -- **잡음 미보고**.
2. 구조: 입력 M1/M2(nmos, 꼬리 M11), 접힘 노드 X/Y의 pmos 전류원 M3/M4(**전부 기여**, 보통 입력보다 큰 전류),
   pmos 캐스코드 M5/M6(무시), nmos 하단 거울 M9/M10(기여, 캐스코드 M7/M8 무시).
   S_th,in = (8kT·γ_n/gm1)·[1 + (γ_p/γ_n)(gm3/gm1) + (gm9/gm1)], GBW = gm1/(2π·CL), CL = 1 pF.
3. 추정: GBW가 미정(SP-5)이라 S_th,in = 8kTγ_n·F/(2π·GBW·CL), F ≈ 1.95–3.9(gm3/gm1 1–2, gm9/gm1 0.5–1).
   예: GBW 10 MHz면 입력쌍만 31.7 nV/√Hz, 전체 44–63 nV/√Hz(예시, 값 아님).
4. 제안: 제약 없음, 보고. GBW(SP-5) 결정 뒤 같은 식으로 값이 정해진다. 신뢰도 중간.

## 6. ngcc_3stage_ff (Lee et al., JSTS 2007) -- 보고 전용(+ 구조 경고)

1. 출처: 논문 Table 4·본문(topology `_paper_target_spec`에 이관된 값: GB 10 MHz, PM 63.4°, CL 10 pF, ICMR, gm·ID·W/L·Cm)
   -- **잡음 항목 없음**. 원문 PDF는 이번에 다시 확보하지 못했다(DBpia 리다이렉트, POSTECH 저장소 파일 없음) --
   판단 근거는 기존 이관 기록.
2. 구조: 입력 M1/M2(**pmos**, 꼬리 M0), 거울 부하 M3/M4(**nmos**), 2·3단과 피드포워드(M14, M6B) 잡음은 단 이득으로 나뉨.
   S_th,in = (8kT·γ_p/gm1)·[1 + (γ_n/γ_p)(gm3/gm1)] -- **γ_n/γ_p ≈ 2.2라 부하 M3/M4가 지배하기 쉽다.**
   GBW = gm1/(2π·Cm1).
3. 추정: 논문 설계 예(gm1 105 µS, Cm1 1.68 pF)는 GB = 9.95 MHz와 맞는다. 같은 gm1이면 gm3/gm1 0.67–1에서
   **26–29 nV/√Hz**, 그중 부하 몫 60–70 %. PMOS 입력이라 1/f는 유리(EF 1.0, K_p < K_n).
4. 제안: 제약 없음, 보고. `noise_excess_th`를 보고하면 "부하 gm/ID를 낮게(강반전)" 쪽 설계 신호가 된다
   (offset·matching과 같은 방향). 신뢰도 중간.

## 7. nmcnr_amplifier (Leung, Mok, Ki 1999) -- 보고 전용(+ 구조 경고)

1. 출처: Table 1(100 pF ∥ 25 kΩ) -- topology `_paper_target_spec` 이관 항목은 GBW 816 kHz, PM 46°, SR±, Ts±, PSRR±(1k·10 kHz),
   전력 400 µW, 면적 0.18 mm², DC gain > 100 dB -- **잡음 항목 없음**. 원문 재확인은 못 했다(HKU 저장소 403).
2. 구조: 입력 M102/M103(pmos, 꼬리 M101), 접힘 노드 F1/F2의 **nmos 전류원 M104/M105(전부 기여, 입력보다 큰 전류)**,
   nmos 캐스코드 M106/M107(무시), pmos 거울 M108/M109(기여). 2·3단 무시.
   S_th,in = (8kT·γ_p/gm1)·[1 + (γ_n/γ_p)(gm104/gm1) + (gm108/gm1)], GBW = gm1/(2π·Cm1)(NMC).
3. 추정: Cm1은 엔진 값 → Cm1 = 1 pF당 gm1 = 5.1 µS, 입력쌍만 74 nV/√Hz, F 3.7–6.4로 **142–187 nV/√Hz × √(1 pF/Cm1)**.
   저전력·대용량 부하 회로라 잡음이 크다. 구조적으로 nmos 전류원이 지배.
4. 제안: 제약 없음, 보고. 신뢰도 중간-낮음(Cm1 미정).

## 8. sf_pushpull_output_opamp (Allen L26 p.26-6, Fig. 7.1-1) -- 보고 전용

1. 출처: 도면 스펙 Av(0) 65 dB, GB 60 MHz(CL 1 pF), Rout ≤ 1 kΩ, IBias 50 µA -- **잡음 없음**(강의 전문 검색).
2. 구조: 입력 M1/M2(nmos, 꼬리 M3 ← M4 거울), 자기 바이어스 캐스코드 부하 M5–M8(R1a/R1b), 출력 Y 노드 분기
   M9/M10·M15/M16(Cc는 Y–agnd), 버퍼(M17–M22). 입력환산 = 입력쌍 + 부하 하단 소자(M6, M8, M14·M16 경로) 기여,
   버퍼는 이득으로 나뉨.
3. 추정(가정 표시): 꼬리 전류 = IBias(거울비 1 가정, 도면에 W 없음) → 한쪽 25 µA, gm/ID 15 → gm1 375 µS,
   입력쌍만 13 nV/√Hz, 부하 포함(F≈2) ~18 nV/√Hz.
4. 제안: 제약 없음, 보고. 신뢰도 낮음(거울비·부하 gm 미정).

## 9. pushpull_follower_buffer (Allen L26 p.26-4/26-6) -- **잡음 스펙 무의미, 넣지 않음**

1. 출처: Rout ≤ 1 kΩ, CL 1 pF만 -- 잡음 없음.
2. 구조: 이득 ~1 팔로워 두 겹(M3/M4 레벨시프트 팔로워 + 전류원 M5/M6, 출력 팔로워 M1/M2). 모든 소자 잡음이
   이득 ~1로 출력에 나온다. 원 회로(Fig. 7.1-1)에서는 65 dB 이득 뒤에 있으므로 op amp 입력환산 기여는
   (1/10^(65/20))² ≈ 3e-7배 -- 무시.
3. 추정: 출력 팔로워만 4kT·γ_avg/(gm1+gm2), gm1+gm2 ≥ 1 mS(Rout 스펙)에서 ≤ 4.8 nV/√Hz; 실제로는 gm이 작은
   1단 팔로워 M3/M4·전류원 M5/M6이 지배.
4. 제안: 스펙 없음. 원하면 출력잡음 보고만.

## 10. common_gate_amplifier (Allen L20 p.20-2) -- 보고 전용

1. 출처: 강의 p.20-2 -- 잡음 없음(강의 전문 검색: 'noise'는 cascode 어원 각주의 논문 제목뿐).
2. 구조: 입력은 M2 소스(vin을 전압원이 직접 구동). M1(전류원)의 잡음 전류는 이상 전압원으로 빠져 **기여 0**
   (구동 임피던스가 0일 때; 실제 구동 저항 R_S가 있으면 M1 잡음·R_S가 들어온다). M3(pmos 부하) 기여.
   S_in = 4kT·[γ_n·gm2/(gm2+gmbs2)² + γ_p·gm3/(gm2+gmbs2)²](단일단).
3. 추정: CL·GBW·전류가 미정(SP-4/5, CL은 SP-6) → 값 없음.
4. 제안: 제약 없음, 보고. CG를 저잡음 용도로 쓸 계획이 없으면 의미 작다.

---

## 11. 요약표

| 회로 | metric | 제안 값 | 근거 | 신뢰도 |
|---|---|---|---|---|
| current_reuse_telescopic_ota | `noise_out_int_vrms`(폐루프 차동 출력, [1 Hz,∞), β = Cf 선언) | **A: ≤ √((V_FS/(2^N√12))² − 2kT/Cs)** = 664 µVrms(V_FS 2.4 V, N 10) / **B: ≤ 300 µVrms**(논문 Table I) | ε_d·Cs 선언 + 식 2kTγ_avg/(βCc); 독립 추정 218 µV vs 논문 272 µV | 식·규모 높음, flicker·α 중간 |
| two_stage_ota | `noise_th_in_v2hz`, `noise_fc_in_hz` 보고 (+선택 `noise_excess_th ≤ 2`) | 제약 없음(추정 43–56 nV/√Hz) | 출처 미보고, GBW 7 MHz·Cc 의존 | 중간 |
| two_stage_ota_sf | two_stage_ota 상속 | 제약 없음 | 팔로워 잡음 무시 가능 | 중간 |
| folded_cascode | 보고 | 제약 없음(8kTγ_nF/(2π·GBW·CL), F 2–3.9) | GBW 미정 | 중간 |
| ngcc_3stage_ff | 보고 (+선택 가드) | 제약 없음(추정 26–29 nV/√Hz, 부하 지배) | 논문 Table 4 gm1 | 중간 |
| nmcnr_amplifier | 보고 | 제약 없음(142–187 nV/√Hz·√(1pF/Cm1)) | Cm1 미정 | 중간-낮음 |
| sf_pushpull_output_opamp | 보고 | 제약 없음(~13–18 nV/√Hz) | 꼬리 = IBias 가정 | 낮음 |
| pushpull_follower_buffer | 없음 | 스펙 무의미 | 이득 뒤 출력단 | 높음(판단) |
| common_gate_amplifier | 보고 | 제약 없음(식만) | 전류·부하 미정 | 중간(식) |

---

## 12. 사용자 판단이 필요한 항목

1. **범위**: 현재 계획(DEC-96)은 "9회로 잡음 스펙 없음". 파일럿에 잡음 제약을 넣는 것 자체가 범위 변경이다.
   엔진에 잡음 metric(LUT `SVG2_1HZ`·`SVG2_HF` + MNA 잡음 전달)이 아직 없어 metric 구현 card가 먼저 필요하다.
2. **파일럿 값 A(정확도 유도, 664 µV) vs B(논문 300 µV)**. A는 Cc에는 비구속, 입력 면적(flicker)에는 구속.
   B는 Cc ≥ 0.26–0.38 pF와 입력 면적 증가를 같이 요구.
3. **V_FS**: A의 V_FS = 2.4 V는 논문 출력 스윙 스펙(±1.2 V)이며 sizing_spec에 채택 기록이 없다. 채택하거나 다른 근거
   (전원·헤드룸에서 유도)를 정해야 한다. 예산 규칙(총 잡음 ≤ 같은 해상도 양자화 잡음)도 승인 대상.
4. **8개 비-SC 회로**: 보고만 할지, `noise_excess_th ≤ 2` 가드를 걸지(기준 "부하 잡음 ≤ 입력 잡음"). 가드는
   ngcc·nmcnr(PMOS 입력+NMOS 부하)에서 부하 gm/ID를 낮추는 쪽으로 작동해 헤드룸과 부딪힐 수 있다.
5. **적분 하한 f_lo = 1 Hz**(LUT 실측 최저점, 외삽 없음) 채택 여부. 파일럿 상한은 폐루프 롤오프로 수렴(∞).
6. **잡음 계산 소자 범위**: 파일럿 적분에 CMFB·바이어스망·스위치를 넣을지(논문 Fig. 19는 OTA 인스턴스만 합산).
   제안은 OTA 전 소자, 스위치 제외(샘플링 kT/C는 예산식에서 따로 뺐다).
7. **검증 필요(가정 대신 실측)**: (a) 파일럿 폐루프 ngspice `.noise`로 α(2단·CMFB 몫)와 flicker 몫 측정,
   (b) γ·K의 VS·VDS 의존(이번 표본은 VS = 0, VDS = 0.9 V만), (c) 약반전 pfet(gm/ID ~19, 논문 입력 바이어스)은
   LUT 100 MHz 점이 fT 부족으로 신뢰 불가 -- 더 낮은 주파수 점(예: 1 MHz) LUT 열 추가 여부.

## 부록: 재현
- γ·K 표: LUT npz를 python으로 읽어 §0.2 방법으로 계산(VDS 인덱스 24 = 0.9 V, VS 인덱스 0).
- ngspice 스펙트럼: `assets/sky130_lut_sweep.py`의 `model_includes()`·`DUT_LINE`과 같은 include·DUT 줄,
  `vds dd 0` + `lchoke dd d 1e9` 구조, `noise v(d) vgs dec 1 1 1e9`. 스크래치에서 실행, 저장소 미변경.
