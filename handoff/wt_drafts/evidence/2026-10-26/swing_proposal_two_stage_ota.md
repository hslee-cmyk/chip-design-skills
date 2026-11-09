# two_stage_ota 출력 범위(DK5) spec 후보 -- 독립 이론 유도

- 작성: 독립 회로 해석자, 2026-10-26. 읽기 전용, 앞선 조사(output_range_candidates.md)·다른 해석자 결과·heldout은 근거로 쓰지 않았다.
- 근거로 쓴 것: `assets/library/two_stage_ota.topology.json`의 `netlist`·`passive_elements`·`ports`·`supply_nets`·`bias_inputs`(connectivity만 썼고 device_roles·symmetry·sizing_roles·compensation 태그와 주석은 쓰지 않음), `assets/library/two_stage_ota.sizing_spec.json`, 원문 `assets/library/sources/two_stage_ota+folded_cascode__maloberti_2004/source.pdf`, sky130 LUT v2 `C:/Users/HSLEE/Documents/Todoc/fpga/lut_data/sky130_lut_v2/sky130_nfet_pfet_lut_v2_r2.npz`(`assets/lut_v2_location.json`의 cap_npz, sha256 938e95b9…), `wt/_drafts/user_decisions.md` O-154·O-128 Q5·O-151, 계획 DEC-65·DEC-100.
- 계산 스크립트와 원자료: `C:/Users/HSLEE/Documents/Todoc/fpga/wt/_scratch_swing_two_stage_ota/` (`calc.py` -> `results.txt`, `calc_Lsweep.py` -> `results_Lsweep.txt`, `calc_ft.py` -> `results_ft.txt`).

> ⚠ 현재 결정과의 관계: O-154 Q4는 two_stage_ota를 **'미선언'**으로 확정했다. 이 문서는 그 결정을 바꾸자는 것이 아니라, 선언한다면 어떤 값이 이론적으로 타당한지를 제시한다. 선언 여부는 사용자 결정이다(아래 대안 A0).

## 1. 원문

- Maloberti, *Layout of Analog CMOS IC Part 2*, p.28 'Example 1 (2 stages OTA)' 그림(로컬 `source.pdf` p.28, 렌더 `pages/p28.png`; 웹 재게시 slideshare.net/slideshow/layout02-1/58842369). 폭만 있고(M1·M2 60, M3·M4 30, M5 40, M6 108, M7 72) "Compensation network and bias are missing (!)"라고 적혀 있다. p.29~33도 레이아웃(stack·stick) 내용뿐이다.
- 원문에는 **전원, 공정, 출력 스윙, 구동 대상, 이득, ICMR 같은 응용 단서가 없다**. 그래서 출력 범위 값은 원문에서 가져올 수 없고, 선언한다면 설계 의도(gm/ID 가정)에서 유도한 user_spec이 된다.

## 2. topology 해석 (connectivity만)

| 소자 | 종류 | D | G | S |
|---|---|---|---|---|
| M3 | pmos | D3 | D3 | vdd |
| M4 | pmos | O1 | D3 | vdd |
| M6 | pmos | OUT | O1 | vdd |
| M1 | nmos | D3 | vin_n | CS |
| M2 | nmos | O1 | vin_p | CS |
| M5 | nmos | CS | bias | gnd |
| M7 | nmos | OUT | bias | gnd |

수동소자: Rz(O1–N_cc_rz), Cc(N_cc_rz–OUT), CL 3 pF(OUT–gnd). 포트: 입력 vin_p·vin_n, 출력 OUT 하나.

1. **출력 노드 = OUT** (ports에 출력 포트가 OUT 하나뿐이고, M6.D = M7.D = OUT). 확신도 높음.
2. **단일 출력**: 출력 포트가 하나이고 OUT에 짝 노드가 없다. CMFB 소자나 CM 감지 넷이 없다 → CM 제어 없음. 확신도 높음.
3. **OUT에서 레일까지의 DC 경로**: OUT에 닿는 DC 경로 소자는 M6(D)와 M7(D)뿐이다. Cc는 DC에서 열려 있어(DEC-100 (2)) O1–OUT 사이 DC 경로가 없다. CL도 DC에서 열려 있다.
   - 위쪽(끌어올림): vdd –M6(S→D)– OUT. **소자 1개 = VDsat 1개.**
   - 아래쪽(끌어내림): OUT –M7(D→S)– gnd. **소자 1개 = VDsat 1개.**
4. **출력단 종류 = 공통 소스 + 전류원 부하**(class-A). 근거: M6는 source가 vdd(AC 접지)이고 gate가 내부 노드 O1, drain이 OUT → 공통 소스. M7은 gate가 바이어스 입력 넷 `bias`(외부 고정 DC), source가 gnd → 고정 VGS 전류원. 출력이 source 단자에 붙은 소자가 없으므로 follower가 아니고, OUT과 레일 사이에 직렬 소자가 둘 이상인 경로가 없으므로 cascode도 아니다. 확신도 높음(0.95).
5. **나머지 구조(참고)**: M1·M2는 source를 CS에서 공유하고 gate가 두 입력 → 차동쌍. M3는 gate=drain(diode), M4는 M3와 gate·source 공유 → 전류 거울 부하. M5·M7은 gate(bias)와 source(gnd)를 둘 다 공유 → **VGS가 같다**(KVL 고정, DEC-64 v0 equal_vgs). O1 = M2·M4 drain = M6 gate → 첫 단 출력이 둘째 단 입력. Rz–Cc 직렬이 O1–OUT 사이 → 밀러 보상. 확신도 높음.
6. **되먹임**: 저장소 spec `human.feedback.elements = []`(선언 되먹임 소자 없음). 회로 안에서 OUT이 입력으로 돌아가는 DC 경로는 없다. PM 측정용 β = 1 루프는 측정 구성(합성, O-68·O-69)일 뿐 응용 회로 선언이 아니다.

## 3. 스윙 식 (DC)

출력단만의 범위(입력 CM이 출력과 독립인 구성, 예: DEC-65처럼 출력을 범위 끝 V에 고정하고 입력을 차동으로 모는 경우):

- V_hi = VDD − VDsat(M6) (M6 포화: V_SD6 = VDD − V_OUT ≥ VDsat6)
- V_lo = VSS + VDsat(M7) = VDsat(M7) (M7 포화: V_DS7 = V_OUT ≥ VDsat7)
- follower 항(VGS)은 없다(출력이 어떤 소자의 source에도 붙지 않음).
- 범위 끝에서 첫 단은 거의 안 움직인다: O1은 ΔV_OUT/A2만큼만 변하므로(둘째 단 이득 A2 ≫ 1) M1~M5의 포화 여부는 출력 범위 끝에서 바뀌지 않는다. 그래서 R8 범위 끝 헤드룸 고리에서 출력 범위에 직접 묶이는 행은 M6·M7 두 개다.
- 부하는 CL(용량)뿐이라 DC 부하 전류가 0이다. 범위 끝에서도 DC로는 I6 = I7이고, M7은 VGS가 고정이며 M6의 VSG도 동작점 그대로 유지된다(W·바이어스 고정 섭동 틀). 그래서 범위 끝 VDsat ≈ 동작점 VDsat로 놓을 수 있다(LUT로 확인: VDS를 0.9 V에서 VDsat까지 바꿔도 VDSAT 차이는 ≤ 2 mV, `results.txt`).

β = 1 follower 구성(입력 CM = OUT, 응용이 follower인 경우)에서는 입력 CM 창이 함께 걸린다.

- VCM_min = VGS1(V_SB = V_CS) + VDsat5
- VCM_max = VDD − VSG3 − VDsat1 + VGS1 (M1 포화: V_D3 − V_CS ≥ VDsat1, V_D3 = VDD − VSG3)
- follower 범위 = [max(V_lo, VCM_min), min(V_hi, VCM_max)]

## 4. 수치 (sky130 LUT v2, tt, 27 °C)

LUT 읽는 법: 배열 [L, VGS, VDS, VS]. gm/ID = GM/ID는 |VDS| = 0.9 V(=VDD/2, 설계 동작점 가정)에서 정의했다. VDsat = LUT `VDSAT` 열(ngspice BSIM `@m[vdsat]`, spec `saturation_rule: vds_ge_vdsat`와 같은 양)이고, VDS = VDsat가 되는 자기일관 끝점에서 읽었다. M6·M7은 source가 레일이므로 VS 축 0(V_SB = 0). pfet은 크기값(LUT sign_convention). **gm/ID와 L은 설계 가정**이다(상수가 아니다).

### 4.1 소자별 VDsat (L = 1 µm 대표)

| gm/ID [S/A] (가정) | nfet VGS / Vov | nfet VDsat | pfet VSG / Vov | pfet VDsat | 2/(gm/ID) 참고 |
|---|---|---|---|---|---|
| 5 (강반전) | 0.958 / +0.369 | 0.294 | 1.382 / +0.360 | 0.342 | 0.400 |
| 8 | 0.821 / +0.231 | 0.201 | 1.232 / +0.210 | 0.222 | 0.250 |
| 10 (중간 반전 하단) | 0.770 / +0.180 | 0.166 | 1.173 / +0.151 | 0.177 | 0.200 |
| 12 | 0.730 / +0.141 | 0.139 | 1.125 / +0.103 | 0.141 | 0.167 |
| 15 (중간 반전) | 0.682 / +0.092 | 0.107 | 1.056 / +0.034 | 0.099 | 0.133 |
| 18 (약반전 쪽) | 0.637 / +0.047 | 0.081 | 0.862 / −0.160 | 0.048 | 0.111 |
| 20 | 0.603 / +0.014 | 0.066 | 0.798 / −0.224 | 0.046 | 0.100 |

- 손계산 근사 2/(gm/ID)는 LUT VDsat보다 0.03~0.06 V 크다(보수적). 범위 계산에는 LUT 값을 쓴다.
- pfet gm/ID ≥ 18은 VSG < VTH(약반전)이고, BSIM VDSAT가 약 0.045 V에서 바닥을 친다. 물리적인 포화 여유(3~4 U_T ≈ 0.08~0.10 V)보다 작아서, 이 영역의 범위 값은 `vds_ge_vdsat` 규칙에서는 낙관적이다.

### 4.2 출력단 범위 (A): gm/ID 가정별 V_lo, V_hi (M6·M7 같은 gm/ID)

| gm/ID (가정) | L = 0.5 µm [V_lo, V_hi] | L = 1 µm | L = 2 µm | 전 L 격자(18점) 최악: V_lo = max VDsat_n, V_hi = 1.8 − max VDsat_p |
|---|---|---|---|---|
| 5 | [0.269, 1.459] | [0.294, 1.458] | [0.318, 1.466] | -- |
| 8 | [0.191, 1.580] | [0.201, 1.578] | [0.219, 1.587] | [0.219, 1.577] |
| 10 | [0.159, 1.626] | [0.166, 1.623] | [0.181, 1.631] | [0.181, 1.623] |
| 12 | [0.133, 1.661] | [0.139, 1.659] | [0.152, 1.664] | [0.152, 1.658] |
| 15 | [0.103, 1.702] | [0.107, 1.701] | [0.118, 1.703] | [0.118, 1.701] |
| 20 | [0.064, 1.755] | [0.066, 1.754] | [0.074, 1.759] | -- (pfet 약반전) |

(출처: `results.txt`, `results_Lsweep.txt`.) 범위 중심은 어느 가정이든 약 0.89~0.91 V(= VDD/2 근처)다. n·p VDsat가 비슷하기 때문이다.

### 4.3 follower 구성 범위 (B): 모든 소자 같은 gm/ID·L 가정

| gm/ID | L = 0.5 µm | L = 1 µm | L = 2 µm |
|---|---|---|---|
| 5 | 공집합 (VCM_min 1.30 > VCM_max 1.21) | 공집합 | 공집합 |
| 8 | [1.08, 1.34] | [1.07, 1.26] | [1.07, 1.19] |
| 10 | [0.99, 1.40] | [0.97, 1.32] | [0.97, 1.26] |
| 12 | [0.92, 1.45] | [0.90, 1.37] | [0.90, 1.32] |
| 15 | [0.84, 1.51] | [0.81, 1.44] | [0.81, 1.39] |

NMOS 입력쌍(body = gnd라 V_SB = V_CS로 body effect가 있음)과 pfet |VTH|(약 1.0 V, LUT)가 커서, follower로 쓰면 출력 범위가 입력 CM 창에 크게 잘린다.

### 4.4 실현 가능성 점검 (AC 쪽은 DC 범위 값에 쓰지 않고, 충돌 여부만 봄)

출력 범위를 넓히라는 요구는 M6·M7 gm/ID를 올리라는 요구다. gm/ID를 올리면 W6가 커지고, 그러면 O1의 Cgs6가 커져 둘째 극점이 내려간다. LUT fT = GM/(2π·CGG), pfet(`results_ft.txt`):

| pfet L | gm/ID 8 | 10 | 12 | 15 |
|---|---|---|---|---|
| 0.5 µm | 1695 MHz | 1300 | 966 | 526 |
| 1 µm | 467 | 358 | 265 | 142 |
| 2 µm | 115 | 88 | 67 | 38 |

GBW ≥ 7 MHz·PM ≥ 70°에 필요한 둘째 극점은 GBW의 몇 배 수준(수십 MHz)이다. gm/ID 15에 L 2 µm이면 fT6가 38 MHz까지 내려가 PM 제약과 부딪힌다. 이득 57 dB 때문에 L을 길게 가져가야 하는 상황과도 겹친다. gm/ID 10이면 L 2 µm에서도 fT6가 88 MHz다. 그래서 gm/ID 15 수준의 범위는 다른 spec과 실제로 겨루는 엄격한 요구다. gm/ID 10 수준은 L 선택을 크게 막지 않는다. 이 판단은 정성적이다(Cc·Rz·C1 실값이 엔진 계산 대상이라 정량화하지 않았다).

## 5. 순환 위험

- 능력 식 V_hi = VDD − VDsat6, V_lo = VDsat7을 **엔진이 고른 동작점의 VDsat로 다시 계산해 요구로 쓰면** R8 행은 늘 정확히 0 여유로 통과한다. 그러면 요구가 의미 없다(순환). 그러니 요구는 엔진 밖에서 정한 **고정 숫자**여야 한다.
- 고정 숫자 [V_lo, V_hi]는 탐색에서 **VDsat7 ≤ V_lo, VDsat6 ≤ VDD − V_hi**, 곧 M6·M7 gm/ID 하한(L에 따라 다름)으로 작동한다. 그래서 순환이 아니다. 이 요구가 의미 있으려면 다음 둘이 필요하다.
  1. 탐색 상자 안에서 이 요구를 어기는 점이 실제로 있다(그렇지 않으면 무동작). 강반전 쪽 gm/ID 5~8 점은 [0.19, 1.62]를 어긴다(4.2) → 거부가 실제로 일어난다.
  2. 다른 spec과 함께 달성할 수 있다(4.4).
- 동반 효과(연결에서 나옴): M5·M7은 VGS가 같다. L이 같으면 gm/ID도 같으므로 V_lo 요구는 꼬리 M5의 gm/ID 하한도 함께 건다. M6의 VSG는 계통 offset 0 조건(O1 = D3, 곧 VSG6 = VSG4)에서 M3·M4와 같은 전류 밀도가 되므로 V_hi 요구가 첫 단 부하로 번진다. 단 이것은 설계 조건이지 연결 사실은 아니다.
- 의미 있는 값을 정하는 논리: 원문에 응용 단서가 없으므로 기준은 '설계 의도 gm/ID'다. 그 gm/ID는 모든 L에서 만족되도록 **L 격자 최악값**으로 환산한다. 그래야 요구가 L 선택을 몰래 묶지 않고 gm/ID 하한만 건다.

## 6. 기존 spec과의 정합

- 레일: vdd 1.8, gnd 0 → 모든 후보가 레일 안이다.
- ICMR: spec에 `icmr_v` 제약이 **없다**. `input_dc`는 `pending: SP-2`다. 출력단 범위(A)는 입력 CM과 독립이라 충돌하지 않는다. follower 구성(B)을 응용으로 선언하면 ICMR 선언과 input_dc가 함께 정해져야 한다(입력 DC = 출력 DC).
- 부하: CL 3 pF뿐이다(measurement_load). DC 부하 전류가 0이라 범위 끝 공급 능력(DEC-65 I_cap)은 포화만 지키면 된다. 정상상태 전류 요구는 0이다.
- swing_out_v: 이 spec에는 없다(삭제할 대상 없음, O-154 Q3 해당 없음).
- 다른 제약(gain 57 dB, GBW 7 MHz, PM 70°, offset_excess, noise_excess_th, area 0.015 mm²): 범위 값은 DC라 직접 섞지 않는다(DEC-67). 4.4의 실현 가능성 점검만 했다. 면적 예산은 W 증가를 넉넉히 받는다.

## 7. 권고와 대안

**권고 (A1): 출력 절대 범위 [V_lo, V_hi] = [0.19, 1.62] V** (단일 출력이라 Vod·CM 없음).
- 유도: M6·M7 설계 의도 gm/ID ≥ 10 S/A(중간 반전 하단, 가정)를 LUT 18개 L 격자 최악 VDsat로 환산하면 [0.181, 1.623] V다. 10 mV 단위로 반올림하되, gm/ID 10에서 모든 L이 통과하도록 느슨한 쪽(V_lo 올림, V_hi 내림)으로 맞췄다. 폭 1.43 V, 중심 0.905 V.
- 측정 구성: 입력 CM과 독립인 구성(DEC-65 출력 고정 `.dc`).

| 안 | 범위 [V] | 설계 의도 | 물리 정합 | 손계산 일치 | 기존 spec 정합 | 순환 위험 | 원칙 |
|---|---|---|---|---|---|---|---|
| **A1 (권고)** | [0.19, 1.62] | M6·M7 gm/ID ≥ 10 | 포화 행 2개, 강·중간 반전 경계라 BSIM VDsat가 물리 포화와 맞음 | 2/(gm/ID) 근사 [0.20, 1.60]과 0.02 V 안 | ICMR·부하·레일 충돌 없음, fT6 ≥ 88 MHz(L ≤ 2 µm)라 PM 충돌 작음 | 낮음: gm/ID 5~8 점 거부 | gm/ID는 가정으로 명시, 원문 값 인용 없음, 이름·태그 미사용 |
| A2 | [0.22, 1.57] | gm/ID ≥ 8 | 강반전, 물리 정합 좋음 | 근사 [0.25, 1.55] | 충돌 없음 | 중간: 거부되는 점이 gm/ID 5 근처뿐이라 요구가 약함 | 같음 |
| A3 | [0.12, 1.70] | gm/ID ≥ 15 | pfet Vov ≈ +0.03~0.05 V, 약반전 경계라 BSIM VDsat의 물리 여유가 가장 작음 | 근사 [0.13, 1.67]과 0.03 V 차 | L 2 µm에서 fT6 38 MHz, PM·이득(L)과 겨룸 | 낮음(엄격함) | 같음, 단 약반전 근처라 판정 낙관 위험 |
| A4 | [0.97, 1.32] (L 1 µm, 전 소자 gm/ID 10) | follower 응용 | ICMR 포함 전 소자 포화 | 식 단순 | ICMR·input_dc 선언이 같이 필요(지금 미정 SP-2), L 의존이 큼 | 중간: 첫 단 gm/ID까지 묶음 | ⚠ 응용 망(follower)이 원문·사용자 선언에 없음 → DEC-100 (6) '선언된 조건만'에 어긋남 |
| A0 | 미선언(현 O-154 Q4) | -- | -- | -- | 현 결정 그대로 | 순환 없음, 단 R8·R10 (i) 행 없음, 범위 양 '정의 불능' | 원문 근거 없는 값을 만들지 않는다는 원칙에 가장 충실 |
| (기각) 능력 식 그대로 | 엔진 동작점 VDsat | -- | -- | -- | -- | ⚠ 높음: 늘 통과(순환) | 요구 = spec 양(R1) 위반 |

## 8. 확신도

- 출력 노드·적층(위 1 VDsat, 아래 1 VDsat)·CS 출력단·단일 출력·CM 제어 없음: **높음(0.95)**. 연결만으로 결정된다.
- LUT 수치: **높음**. LUT 직접 조회이고 L 격자 전수다. VDS 자기일관 끝점과 0.9 V 점의 차는 ≤ 2 mV다. tt·27 °C 한 코너만 봤다(코너·온도 변동은 안 봄).
- 권고 값 자체: **중간**. 원문 근거가 없어서 값은 전적으로 gm/ID 설계 의도 가정에 달려 있다.

## 9. 사용자 확인 포인트

1. **선언 여부**: O-154 Q4는 '미선언'이다. 원문에 출력 spec이 없는 회로에 설계 의도 범위를 user_spec으로 새로 둘지(A1~A3), 미선언을 유지할지(A0) 정해야 한다.
2. **응용 구성**: 출력 범위를 입력 CM과 독립인 구성(A, 권고)으로 정의할지, follower(β = 1) 응용으로 정의할지(A4). A4를 고르면 input_dc(SP-2)·ICMR 선언이 함께 필요하고 응용 망 선언(AP-1)이 먼저 있어야 한다.
3. **설계 의도 gm/ID 수준**: 10(A1) / 8(A2) / 15(A3).
4. **반올림 방향**: 권고는 '그 gm/ID에서 모든 L이 통과하는 쪽'(느슨한 쪽)이다. LUT 원값 [0.181, 1.623]을 그대로 쓸지도 정해야 한다.
5. 약반전(pfet gm/ID ≥ 15) 영역에서는 `vds_ge_vdsat`(BSIM VDSAT ≈ 0.045 V 바닥)가 물리 포화 여유보다 낙관적이다. A3을 고르면 이 점을 함께 알아야 한다.
