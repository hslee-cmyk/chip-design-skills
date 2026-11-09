# spec 후보 조사 -- folded_cascode · common_gate_amplifier (SP-3 PM, SP-4 gain, SP-5 GBW; CG 부하 SP-6 (c))

- 작성: spec 후보 조사 agent, 2026-10-26. 사용자 원문: "F도 스펙을 정하자".
- **값을 정하지 않는다.** 근거가 붙은 후보만 낸다. 근거 종류 표지: [원문] / [다른 원문] / [손계산](sky130 물리 한계) / [관례](library 다른 회로 spec) / [엔진 실측](as-built 실행, 판정 아님).
- 고친 파일 없음. spec·topology·엔진·계획·design 무변경. 실행 전후 `git -C wt/integ-it12 status --short` 모두 빈 출력(`_scratch_spec_fcg/git_status_before.txt` = `git_status_after.txt`).
- heldout 원문·회로 이름은 근거로 쓰지 않았다.
- 원자료: `C:/Users/HSLEE/Documents/Todoc/fpga/wt/_scratch_spec_fcg/`
  - `handcalc.py` → `out/handcalc.txt`·`out/handcalc.jsonl`(LUT 손계산), `area_check.py` → `out/area_check.txt`
  - `scripts/probe_spec.py`(spec **사본**에 후보 제약을 넣고 무수정 엔진으로 단계 A·B·출발 구간·층 0 실행) → `out/probe_<회로>.jsonl`, 요약 `out/probe_summary.md`; `scripts/rung0.py` → `out/rung0.jsonl`
  - spec 사본: `specs/<variant>/<회로>.sizing_spec.json`(로더가 파일 이름 = `<circuit>.sizing_spec.json`을 요구해 폴더로 나눴다. 원본 library 파일은 읽기만)
- 엔진: `wt/integ-it12` HEAD `f34b4090`. LUT: `lut_data/sky130_lut_v2/sky130_nfet_pfet_lut_v2_r2.npz`(tt, W_ref 5 µm, L 앵커 18개 0.15~20 µm).

---

## 0. 결론 요약

| 항목 | folded_cascode | common_gate_amplifier |
|---|---|---|
| 원문 전기 사양 | **없음**(Maloberti p.34 "Only Ws are shown", p.34~38 전부 레이아웃 내용) | **없음**(Allen L20 p.2~4는 식만; 숫자 예제 20-1은 다른 위상(캐스코드) p.17) |
| DC gain 물리 상한 [손계산] | L 0.5 µm ≈ 73~75 dB, 1 µm ≈ 83~87 dB, 4 µm ≈ 97~101 dB, 8 µm ≈ 102~106 dB (k = I3/I1 = 2~1.5) | L 0.3 µm ≈ 32 dB, 0.5 µm ≈ 37 dB, 1 µm ≈ 41 dB, 2 µm ≈ 43 dB, 8 µm ≈ 49 dB |
| GBW 물리 범위 [손계산] | CL 1 pF에서 GBW ∝ 전류(≈ 0.9 µA/MHz, 공급 M3+M4, A0 ≥ 60 dB, PM ≥ 60·70°)가 ~100 MHz까지 선형, 그 위에서 전류가 급증(무릎 100~200 MHz). PM ≥ 70°·A0 ≥ 60 dB 상한 ≈ 400 MHz | **CL 없으면 GBW는 전류와 무관한 기생 비(Cdd2+Cdd3)로 정해지고 fT와 같은 차수(0.5~11 GHz)** -- 준정적 LUT 모델 범위 밖. **CL과 함께 정해야 한다(SP-6 (c))** |
| PM | 단일단, 비주극점 = 접힘 노드·미러 노드. 손계산상 GBW ≲ 100 MHz에서 70° 확보가 쉽다(긴 L에서만 제약) | 미결 항목 아님(pending에 PM 없음) |
| 층 0 (계획 기준) | gain 선언 → gain 모드 활성(design 41 §5.1), GBW·PM 선언 → 매크로 전류 활성 | gain 선언 → gain 모드 활성; GBW 선언 → 매크로(단 CL 없이는 C_out = 기생뿐) |
| 층 0 (as-built 실측) | gain 모드 **미구현**(LA-1). gain L 하한 `u9_value_not_certified`로 비활성. GBW 선언 시 매크로 gm은 나오지만(62.9 µS @10 MHz) **θ 전류로 옮겨지지 않는다**(`current_from_macro: stage_current_unavailable`, θ 전류 M3·M4·M5·M6·MP 전부 `uncovered`) → 층 0 점 GBW 0.37 MHz. front 0(선언 전과 같음) | gain만 선언해도 front **2 → 0**(gain ≥ 30·35, 층 0 점 L 0.18 µm·gain 17.5 dB). 손계산 출발점(L 1 µm)을 주면 gain ≥ 35에서 front 1점(gain 42.8 dB) -- spec이 아니라 출발점 결함. CL 없이 GBW 선언 시 매크로 근 없음 |

---

## 1. 결정 기록 -- SP-3·SP-4·SP-5가 처음 나온 자리와 미룬 이유

| 자리 | 내용 |
|---|---|
| `wt/_drafts/engine/decision_package_specs.md` (2026-10-07) 표 행 13·14·15(folded), 33·34·35(CG) | 처음 나온 자리. 값은 비우고 근거 방식만: folded gain "7a SPICE 대조 달성값 − 마진(current_reuse 54 dB 선례) 또는 같은 단수 문헌 typical 참고", folded GBW "U-12 단일단 규칙 + 확정 CL 1 pF, 같은 전력 수준 GBW 스윕 무릎점(two_stage 7 MHz 선례 방식)", folded PM "#3과 같은 선례 일관", CG CL "같은 class 단일단 확정 CL(folded 1 pF)과 일관", CG gain "Av = gm2·(rds2∥rds3) 상한(LUT gm/gds) − 마진", CG GBW "U-12 + #33 CL, 스윕 무릎점" |
| `wt/_drafts/engine/PENDING_USER_DECISIONS.md` (2026-10-07) SP-3·SP-4·SP-5·SP-6 | 같은 내용을 질문으로 묶음. **필요 시점 = folded 5주, common_gate 6주**. 0절: "SP-3·SP-5·SP-6은 규칙(방식) 질문 … 다른 회로 칸의 값은 늦어도 5주·6주 시작 전" |
| `user_decisions.md` 131행 (2026-10-07 "5번 빼고, 1~7은 기본안대로 해.") | 파일럿(current_reuse)만 확정: PM 70°(항목 2), 정착 목표(항목 3), 부하(항목 4). **folded·CG 값은 그때 답하지 않음** -- 미룬 이유는 필요 시점이 파일럿보다 늦어서(위 PUD 필요 시점) |
| folded topology `sizing_roles._constraints_status` (2026-09-17 U-35) | 옛 제약 gain_db·pm_deg·cmrr_db·psrr_db는 **자기 실행 역산값**(Ibg 10 µA 임의 점에서 계산한 값)이라 삭제. "7a SPICE 대조에서 기준값을 다시 읽는다". **옛 값(gain 39.7 dB·PM 88.8° 등)은 근거로 쓰면 안 된다**(RC4, U-35) |
| design 41 §5.1 H2 (사용자 결정 2026-10-08 Q5b) | gain·rout 제약이 없는 회로 = '층 0 무동작' + '성능 판정 보류'. 해당 회로로 common_gate·folded가 명시돼 있다 |
| `user_decisions.md` O-135 (2026-10-26) | 두 회로 모두 SR 미선언(원문 근거 없음) -- 같은 원문 사정 |

## 2. 원문 확인

### 2.1 folded_cascode -- Maloberti, Layout of Analog CMOS IC Part 2 (2004)
- 로컬: `chip-design-skills/skills/analog-gmid-design/assets/library/sources/two_stage_ota+folded_cascode__maloberti_2004/source.pdf`(`paper.md`), 웹: 저자 게시처 찾지 못함(제3자 재게시 slideshare layout02-1, sources/README.md 표).
- p.34 "Example 2 (Folded Cascode)" -- 소자 이름과 W 숫자만, 문언 "**Only Ws are shown**". p.35 Split of Transistors, p.36 Stack Design, p.37 Interconnection Exercise, p.38 check-list -- 전부 레이아웃.
- `paper.md` 전체에서 gain·bandwidth·phase·margin·MHz·pF 문자열 0건(`dB`는 수식 깨짐 `C_DB` 4건뿐).
- 판정: **전기 사양(gain·GBW·PM·CL·전류) 없음**. 앞선 조사 결론과 같다. topology `sizing_roles.theta[0]._comment`("Maloberti 원본엔 절대 바이어스 전류값이 없다(W비율만)")와도 일치.
- 같은 위상을 다룬 다른 저장소 원문: library `sources/`에 folded cascode 단독 위상 원문은 없다. nmcnr(Leung 1999)의 1단이 PMOS 입력 folded cascode라는 회로 분석 기록(user_decisions 269행)은 있으나 3단 증폭기의 일부라 단독 사양이 아니다 → 근거로 쓰지 않음.

### 2.2 common_gate_amplifier -- Allen, Lecture 20 (6/24/14)
- 로컬: `.../sources/common_gate_amplifier__allen_2014/source.pdf`(`paper.md`), 웹: https://aicdesign.org/wp-content/uploads/2018/08/lecture20-140624.pdf
- p.2(Page 20-2, 그림 060609-01 오른쪽): 회로와 대신호 식만 -- "VOUT(max) ≈ VDD – VDS3(sat)", "VOUT(min) ≈ VDS1(sat) + VDS2(sat)".
- p.3(Page 20-3): 소신호 식만 -- "Av = vout/vin = + gm2rds2rds3/(rds2+rds3)", "Rin = rds1 || (rds2+rds3)/(1+gm2rds2)", "Rout ≈ rds2||rds3".
- p.4(Page 20-4): 부하별 Rin 식만.
- 숫자가 있는 예제는 p.17 "Example 20-1 - Comparison of the Cascode Amplifier Performance"("ID = 200 microamperes … CL = 1 pF", "Av = −37.1V/V", "p1 … 1.22 MHz") -- **위상이 다르다**(CS M1 + CG M2 캐스코드 증폭기, 0.5 µm급 Table 3.1-2 공정). 이 회로의 사양이 아니다. CL = 1 pF만 '같은 강의의 측정 부하 관례'로 참고 표시할 수 있다.
- p.11(Page 20-11) "Dominant pole (one with the largest resistance to ground)"·p.28 "The voltage driven common gate/common source amplifier has one dominant pole" -- 정성 문장(극점 위치 원리). 값 없음.
- 판정: **전기 사양 없음**.

## 3. sky130 물리 한계 손계산

공통 가정(근사 -- 모두 `handcalc.py` 머리 주석): LUT 기준 표(W_ref 5 µm)를 폭 비례로 씀(좁은 폭 효과 무시), 모든 소자 VDS = 0.375 V(접힘 스택 vdd→M3→M6→M8→M10→gnd 4단 합 1.5 V ≤ 1.8 V), 캐스코드 VS = 0.4 V, 후보 gm/ID ∈ [4, 26] 이고 VDSAT ≤ 0.30 V. gm/ID·L은 LUT 격자점(보간 없음). **'추정'** 표지: 이 표는 손계산 상한이고 엔진 판정(DEC-92 MNA)·SPICE가 아니다.

### 3.1 folded_cascode DC gain 상한
식(topology connectivity: 입력 M1/M2 nmos, 접힘 전류원 M3/M4 pmos, 캐스코드 M5/M6 pmos, 캐스코드 미러 M7~M10 nmos, 출력 out = M6.drain = M8.drain):
- A0 = gm1 · (R_up ∥ R_dn), R_up = (gm6+gmb6)·ro6·(ro1 ∥ ro3), R_dn = (gm8+gmb8)·ro8·ro10
- I3 = k·I1, I6 = (k−1)·I1(X 노드 KCL). VA = ID/gds 로 쓰면 A0 = g1 / [ (1/VA1 + k/VA3)/A6 + (k−1)/(A8·VA10) ] -- **절대 전류와 무관**, (gm/ID, L, k)만의 함수.
- 결과(`out/handcalc.txt` §1, 소자별 gm/ID 자유, 모든 소자 같은 L):

| L (µm) | k = 1.5 | k = 2 | k = 3 | 근거 값(예: L 1 µm) |
|---|---|---|---|---|
| 0.15 | 36.7 | 35.1 | 32.7 | |
| 0.3 | 62.3 | 60.2 | 57.0 | |
| 0.5 | 75.3 | 72.8 | 69.3 | |
| 1 | 86.5 | 83.4 | 79.3 | g1 25.7, VA1 4.3 V, VA3 15.1 V, (gm+gmb)/gds: M6 429, M8 148, VA10 7.7 V |
| 2 | 90.7 | 87.4 | 83.2 | |
| 4 | 100.9 | 97.1 | 92.3 | |
| 8 | 105.7 | 101.9 | 97.3 | |
| 20 | 106.6 | 102.7 | 98.0 | |

(단위 dB.) k(= M3 전류 / 입력 소자 전류)는 설계 선택이다 -- topology `r_mirror_M3_M4 1.5`는 analog-grammar 태그라 근거가 아니다(사용자 원칙). 표는 k를 세 값으로만 보였다.

### 3.2 folded_cascode GBW·PM 범위 (CL = 1 pF, 선언값)
- GBW 정의(엔진 `metrics/loop_analysis.py:11`): |T(0)|·f_3dB. 단일 주극점이면 GBW = gm1/(2π·C_out), C_out = CL + Cdd6 + Cdd8.
- 비주극점(전류 무관 -- 노드 gm과 노드 용량이 모두 W에 비례): 직접 경로(신호 절반) 접힘 노드 X = (gm6+gmb6)/(Css6+Cdd1+Cdd3); 미러 경로(신호 절반) Y·Vg7·Vg9·Vg10. H(s) = A0/(1+s/ωd)·[0.5/(1+s/ωX) + 0.5/((1+s/ωY)(1+s/ω7)(1+s/ω9)(1+s/ω10))], PM = 90° + ∠[…] at ω = 2π·GBW(손계산 근사).
- 격자: L ∈ {0.15, 0.5, 1, 2, 4, 8} µm를 네 무리(입력·접힘 전류원·pmos 캐스코드·nmos 미러)에 따로, gm/ID ∈ {8, 14, 20}을 다섯 무리에 따로, k ∈ {1.5, 2, 3} -- 944,784행.
- 결과(`out/handcalc.txt` §3·§4):

| GBW | PM ≥ 60°: 최대 A0 / 최소 공급전류(A0 ≥ 60 dB) | PM ≥ 70°: 최대 A0 / 최소 공급전류 |
|---|---|---|
| 1 MHz | 102.1 dB / 0.9 µA | 100.2 dB / 0.9 µA |
| 3 MHz | 98.2 dB / 2.7 µA | 97.0 dB / 2.7 µA |
| 10 MHz | 97.8 dB / 8.9 µA | 94.5 dB / 8.9 µA |
| 30 MHz | 91.2 dB / 26.8 µA | 88.0 dB / 27.1 µA |
| 60 MHz | 85.9 dB / 55.3 µA | 83.6 dB / 55.3 µA |
| 100 MHz | 83.6 dB / 92.3 µA | 79.9 dB / 93.0 µA |
| 200 MHz | 75.8 dB / 188.8 µA | 72.6 dB / 256.5 µA |

  - 공급전류 = M3 + M4(= 2k·I1), 바이어스 가지(MP–Ibg–MN)는 뺐다(Ibg는 CI-17 미결).
  - 최소 전류는 GBW에 ~0.9 µA/MHz로 비례하다가(gm1 = 2π·GBW·C_out, gm/ID 20) 100~200 MHz에서 PM 70° 쪽이 먼저 비례를 벗어난다(무릎).
  - PM·A0 하한별 GBW 상한(전류 무제한): PM ≥ 70°에서 A0 ≥ 60 dB → ≈ 400 MHz, A0 ≥ 70 dB → ≈ 220 MHz, A0 ≥ 80 dB → ≈ 90 MHz. PM ≥ 60°에서 각각 ≈ 630·400·140 MHz.
  - 긴 L의 상충(실측): GBW 1 MHz·PM ≥ 60°의 최대 A0 점(L 모두 8 µm)은 PM 66°에 걸린다 -- 접힘 노드 용량(Cdd1+Cdd3)이 커서 긴 L에서는 PM이 GBW를 묶는다.
- 면적 대조(`out/area_check.txt`, 대략 게이트 면적): GBW 10 MHz·PM 70° 최대 A0 점 ≈ 2,800 µm², 30 MHz ≈ 4,400 µm², 100 MHz ≈ 2,600 µm² -- 선언 면적 예산 `area_search_m2 ≤ 1e-8 m²`(10,000 µm²) 안.
- 전력: 선언 없음(PA-1 미결, `objective.budgets` pending). 그래서 GBW 값은 물리로 묶이지 않고(~수백 MHz까지 가능) **전력 대가로 정해진다** -- 이 점이 GBW 후보를 물리 한계에서 하나로 고를 수 없는 이유다.

### 3.3 common_gate_amplifier DC gain 상한
식(Allen p.3 소신호에 gmb 포함, vin = M2 source를 이상 전압원이 구동): Av = (gm2 + gmb2 + gds2)/(gds2 + gds3), I2 = I3 = I(M1은 vin 노드 전류만 세움 -- 이상원 구동이라 Av에 안 들어감). 전류 무관.
- 결과(`out/handcalc.txt` §5, M2 VS = 0.2 V; 0.4 V도 차이 ≤ 0.3 dB):

| L (µm) | 0.15 | 0.3 | 0.5 | 0.7 | 1 | 2 | 4 | 8 | 20 |
|---|---|---|---|---|---|---|---|---|---|
| Av 상한 (dB) | 20.9 | 32.0 | 37.2 | 40.0 | 40.7 | 42.7 | 47.3 | 49.4 | 49.8 |

### 3.4 common_gate_amplifier GBW -- CL이 필요한가 (판정)
- 이 회로는 단일 고임피던스 노드(vout) 하나에 주극점이 있다(Allen p.11·p.28 정성 문장). Rout = ro2∥ro3(p.3) → GBW = Av·f_3dB = (gm2+gmb2+gds2)/(2π·C_out), C_out = C_L + Cdd2 + Cdd3.
- **CL이 없으면**: gm과 Cdd가 모두 W에 비례하므로 GBW가 전류와 무관하고 (gm/ID, L)만의 값이다. 실측(`handcalc.py` 보조 계산): L 0.5 µm·gm/ID 15에서 GBW ≈ 1.69 GHz(fT2 ≈ 2.21 GHz), L 0.15 µm·gm/ID 10에서 11.5 GHz(fT2 33.5 GHz), L 1 µm·gm/ID 10에서 2.15 GHz(fT2 1.22 GHz -- fT보다 크다). pmos 부하 gm/ID 20(약반전, 큰 W)이면 Cdd3가 커져 10 MHz 이하로 떨어진다. 즉 무부하 GBW는 **(i) 전력·전류로 조절되지 않는 기생 비이고 (ii) fT와 같은 차수라 준정적 LUT 모델(CGG·CDD 단일 주파수 F_TEST 추출)이 성립하는 범위 밖**이다. 엔진 U-12 식 `gm_1 ≥ 2π·gbw_target_hz·C_out,total`(C_out,total = 봉인점 출력노드 용량 + 부하 요소)도 부하 요소가 0이면 전류 조건이 아니라 밀도 조건이 된다.
- **판정: GBW(SP-5)는 CL(SP-6 (c))과 함께 정해야 한다.** CL 없이 GBW만 선언하는 것은 물리적으로 의미가 약하고(위 (i)(ii)) 계획 U-12의 '부하 요소' 항이 비어 판정이 기생값에 매인다. 또 CL 추가는 topology connectivity 변경(사용자 몫, `_element_values_comment`·`_compensation_status_comment`)이다.
- CL 후보별 GBW(L 0.5 µm, gm/ID 15 대표점, `out/handcalc.txt` §6): CL 1 pF → 1 µA 2.9 MHz, 10 µA 28.6 MHz, 100 µA 248 MHz; CL 0.5 pF → 5.8 / 56 / 433 MHz; CL 0.1 pF → 29 / 248 / 1070 MHz. CL이 정해지면 GBW ∝ 전류(무릎은 C_par가 CL과 비슷해지는 전류).

## 4. library 관례 비교 [관례]

| 회로 | gain (dB) | GBW | PM | CL | 출처 성격 |
|---|---|---|---|---|---|
| current_reuse (파일럿) | ≥ 54 | (정착 40 ns로 대신) | ≥ 70 | 1 pF ×2 | gain = 실측 57.03 − 3 dB 마진(세션44 사용자 승인), PM 사용자 |
| two_stage_ota | ≥ 57 | ≥ 7 MHz | ≥ 70 | 3 pF | 문헌 typical 60 dB·20 MHz가 실측 불가 → 57·7 MHz 무릎점으로 하향(사용자) |
| two_stage_ota_sf | 상속(two_stage) | 상속 | ≥ 70 | 3 pF | |
| sf_pushpull | ≥ 65 | ≥ 60 MHz | ≥ 70 | 1 pF | Allen 도면 값 채택(U-25) |
| nmcnr | ≥ 100 | ≥ 816 kHz | ≥ 70 | 100 pF ∥ 25 kΩ | 논문(> 100 dB) 채택, PM은 논문 46° 기각 후 70 |
| ngcc | ≥ 111 | ≥ 10 MHz | ≥ 63.4 | 10 pF | 논문 채택 |

- 지시문 정정: 지시문의 "two_stage PM 60°"는 현행 spec과 다르다 -- two_stage_ota·two_stage_ota_sf·sf_pushpull 모두 PM ≥ 70(user_decisions 367행 2026-10-14 Q-S2 "Q-S2는 70도 이상"). PM 70은 library 6회로 중 5회로의 값이고 63.4는 ngcc 논문 값 하나다.
- gm 등가(GBW·2π·CL): two_stage 132 µS, sf_pushpull 377 µS, nmcnr 513 µS, ngcc 628 µS. folded CL 1 pF에 같은 gm을 주면 21~100 MHz가 된다 -- **관례 참고일 뿐 근거 아님**(회로 이름·다른 회로 값으로 정하는 꼴이 되므로).

## 5. 후보표

### 5.1 folded_cascode

| ID | metric | 후보 값 | 근거 [종류] | 달성 가능성 [손계산] | 층 0 활성(계획) | 위험 |
|---|---|---|---|---|---|---|
| F-PM-a | pm_ss_deg | ≥ 70 | library 5회로·파일럿 확정값과 일관 [관례] | GBW ≤ ~100 MHz에서 A0 80 dB 이상과 같이 성립(§3.2) | GBW와 함께 매크로·속도 경계(`iv_speed`: f_np = GBW·tan PM) 활성 | 낮음. 단일단이라 여유 큼 |
| F-PM-b | pm_ss_deg | ≥ 60 | 2단 Miller 구조 하한 관례(PUD SP-3 근거 방식) [관례] | 더 넓다 | 같음 | library 일관성 깨짐(5/6이 70) |
| F-G-a | gain_ss_db | ≥ 60 | 손계산 상한(L 0.3 µm에서도 60 dB, §3.1)에서 큰 여유 -- 출발·탐색이 쉬운 하한 [손계산] | 0.3 µm 이상 어느 L에서도 가능 | gain 모드 활성(§5.1) | 너무 낮으면 짧은 L로 내려가 '사이징 의미' 약함(접힘 캐스코드의 장점인 고이득을 시험하지 않음) |
| F-G-b | gain_ss_db | ≥ 70 | 손계산: L ≥ 0.5 µm 필요(k 1.5~2), GBW 10~100 MHz·PM 70°와 공존(§3.2 표: 100 MHz에서도 79.9 dB) [손계산] | 가능(여유 ≥ 10 dB at GBW ≤ 100 MHz) | 같음 | 중간 |
| F-G-c | gain_ss_db | ≥ 80 | 손계산: L ≥ ~1 µm, GBW ≤ ~90 MHz(PM 70°) [손계산] | GBW 10~30 MHz면 여유 8~14 dB | 같음 | 손계산 상한에 가까워 모델 오차(DEC-72 미측정)로 front가 빌 수 있음(fail-closed) |
| F-G-d | gain_ss_db | 7a SPICE 달성값 − 마진 | current_reuse 54 dB 선례 방식(사용자 승인 방식) [관례·방식] | 7a 대조 뒤에만 값이 생김 | 그때까지 무동작 | 지금 값이 없음(판정 보류 지속) |
| F-B-a | gbw_ss_hz | ≥ 10 MHz | 손계산 무릎(100~200 MHz) 훨씬 아래, 공급 ~9 µA(≈ 16 µW @1.8 V) -- 전력 대가 작음 [손계산] | A0 94.5 dB(PM 70)까지 | 매크로 전류 활성(계획) | as-built 실측: 층 0 점 GBW 0.37 MHz(§6) -- front 실현은 LA-1·매크로 전류 배선에 달림 |
| F-B-b | gbw_ss_hz | ≥ 30 MHz | 같은 방식, 공급 ~27 µA [손계산] | A0 88 dB(PM 70) | 같음 | 같음 |
| F-B-c | gbw_ss_hz | 전력 vs GBW 무릎점(≈ 100 MHz) | two_stage 7 MHz 선례 '스윕 무릎점' 방식(PUD SP-5) [손계산·방식] | A0 ≤ 80 dB와만 공존 | 같음 | ⚠ 아래 경고 |
| F-B-d | gbw_ss_hz | 미선언(보고만) | DF-1 | -- | 매크로 꺼짐 | 층 0 무동작 지속 |

- ⚠ 원칙 경고 (F-B-c): 「권고는 근본원칙과 일치 / 관례를 정의로 쓰지 말 것」 — 무릎점은 전력 축 선언(PA-1)이 없는 상태에서 손계산 근사(비주극점·PM 근사식)의 위치에 매인 값이라, 무릎을 '스펙'으로 박으면 근사 오차가 곧 스펙이 된다. 또 A0 80 dB 이상과는 공존하지 않는다(§3.2: PM 70°·A0 80 dB의 GBW 상한 ≈ 90 MHz). — 근거 `out/handcalc.txt` §3·§4.
- ⚠ 원칙 경고 (관례 gm 등가 21~100 MHz를 값으로 쓰는 경우): 「회로 이름을 근거로 쓰지 않음 · 논문 값 그대로 인용 금지」 — 다른 회로의 GBW·CL은 그 회로 사용자 결정·논문에서 온 값이라 folded에 옮기면 근거 없는 상수다. — 근거 §4.
- ⚠ 원칙 경고 (옛 folded 값 39.7 dB·PM 88.8°를 쓰는 경우): 「상수를 임의로 만들지 마라 / 자기 실행 역산값 금지(U-35·RC4)」 — 임의 Ibg 10 µA 점의 자기 실행 결과다. — 근거 topology `sizing_roles._constraints_status`.

### 5.2 common_gate_amplifier

| ID | metric | 후보 값 | 근거 [종류] | 달성 가능성 [손계산] | 층 0 활성(계획) | 위험 |
|---|---|---|---|---|---|---|
| C-G-a | gain_ss_db | ≥ 30 | 손계산 상한(L 0.3 µm 32 dB, 0.5 µm 37 dB)에서 여유 -- PUD 근거 방식 'Av 상한 − 마진' [손계산] | L ≥ 0.25 µm | gain 모드 활성 | 낮음 |
| C-G-b | gain_ss_db | ≥ 35 | 같은 방식, L ≥ ~0.45 µm 필요 [손계산] | L ≥ 0.5 µm에서 여유 2 dB, 1 µm에서 6 dB | 같음 | 중간 |
| C-G-c | gain_ss_db | ≥ 40 | L ≥ 0.7~1 µm에서만, 여유 ≤ 0.7 dB(1 µm), 3 dB(2 µm) [손계산] | 긴 L 필요 | 같음 | 상한에 붙어 front 빔 위험(fail-closed); 면적 예산 0.005 mm² 안인지는 미확인 |
| C-L-a | CL (SP-6 (c)) | 1 pF | 같은 class 단일단 확정 CL(folded 1 pF)과 일관 -- PUD SP-6 근거 방식 [관례]; 같은 강의 Example 20-1(다른 위상) CL 1 pF [다른 원문, 참고] | 1 µA ↔ 2.9 MHz, 10 µA ↔ 29 MHz | GBW 선언 시 매크로 전류 활성 | topology connectivity 추가(사용자) |
| C-L-b | CL | 미선언(GBW도 미선언) | 원문에 부하 없음(p.2 그림) [원문] | -- | gain만 → gain 모드 | GBW 판정 없음 |
| C-B-a | gbw_ss_hz | CL 1 pF에서 10 MHz | 전류 ~3.5 µA 수준(§3.4 비례) -- 손계산상 무릎 훨씬 아래 [손계산] | 가능 | 매크로 활성 | 값 자체는 전력 대가 선택 |
| C-B-b | gbw_ss_hz | CL 없이 선언 | -- | §3.4: 기생 비·fT 차수 | 매크로가 C_out = 기생만으로 돈다 | ⚠ 아래 경고 |
| C-B-c | gbw_ss_hz | 미선언(보고만) | DF-1 | -- | 매크로 꺼짐(as-built: 전류 = W_min 자리값 0.15 nA, B80) | 성능 판정 보류 |

- ⚠ 원칙 경고 (C-B-b): 「물리 정합 최우선 / gm/ID 손계산 물리 정합 필수」 — CL 없는 GBW는 전류로 조절되지 않는 기생 비이고 fT와 같은 차수라 준정적 모델이 성립하지 않는 영역의 값을 제약으로 삼게 된다. — 근거 §3.4 실측(L 1 µm·gm/ID 10에서 GBW 2.15 GHz > fT 1.22 GHz).
- ⚠ 원칙 경고 (C-L-a를 Allen Example 20-1 값으로 정당화하는 경우): 「논문 값 그대로 인용 금지」 — 다른 위상·다른 공정의 측정 조건이다. 'library 단일단 CL 일관'([관례])이 주 근거이고, CL은 사용자 규칙상 '동작 조건'(user_decisions 338행 2026-10-13)이라 사용자가 직접 지정하는 값이다.

## 6. 층 0 동작 확인

### 6.1 계획 조건으로 판정
- design 41 §5.1 활성 조건: (1) `gain_ss_db >= G` 있음 (2) 그 전달 뷰에 이득 블록 ≥ 1 (3) `review_needed` 없음. §5.12.4 실측: 두 회로 모두 단계 A·B ok, 이득 블록 1개 → **gain을 선언하면 계획상 gain 모드가 켜진다.** 지금은 gain·rout 둘 다 없어 H2 '층 0 무동작'(design 41 §5.1에 두 회로가 명시).
- GBW: `iv_context._target`이 `compensation_targets` 다음으로 판정 제약 `gbw_ss_hz >= v`를 읽는다 → 선언하면 매크로(`macro_poles`)가 돈다. PM도 선언돼야 속도 경계(`iv_speed`, `pm_target_missing`)가 켜진다 -- CG는 PM 미결 항목이 없으므로 GBW만 선언하면 속도 경계는 비활성으로 남는다.
- 단 design 41 §5.1 본문과 계획 DEC-71 상태 칸이 적은 대로 **as-built 층 0은 최소형(feasibility centering)이고 gain 모드는 card LA-1 미구현**이다(B80 §3 (a)).

### 6.2 as-built 실측 (spec 사본 + 무수정 엔진, 평가 예산 40 기본)
(표는 `out/probe_summary.md`. 층 0 점 = `layer0_start` 결과 점을 커널로 다시 평가한 값.)

| 회로 | 사본에 넣은 제약 | 출발 구간 비활성 사유(주요) | 매크로 | 층 0 (stop / 출발점 상태) | 층 0 점 metric 값 | 층 0 점 ss 행 c (≥ 0 이 만족) | front (예산 400) |
|---|---|---|---|---|---|---|---|
| folded | 없음(현행) | gain_l `constraint_not_declared`, speed `gbw_target_missing`, current_from_macro `stage_current_unavailable` | 꺼짐 | converged / sealed | noise_excess 3.74 | offset −2.4, noise −0.48 | (B80: 0) |
| folded | gain ≥ 60 | gain_l **`u9_value_not_certified`** | 꺼짐 | 같음 | gain **29.2 dB** | gain −3.4 | -- |
| folded | GBW ≥ 10 MHz, PM ≥ 70 | speed 활성, current_from_macro `stage_current_unavailable` | **켜짐** gm_out 62.9 µS(= 2π·10 MHz·1.0 pF), PM 92.6 | converged / sealed | GBW **0.37 MHz**, PM 109 | GBW −57, PM +2.1 | -- |
| folded | gain ≥ 60·70·80, GBW ≥ 10 MHz, PM ≥ 70 | gain_l `u9_value_not_certified` | 켜짐(같음) | 같음 | gain **9.7 dB**, GBW 0.37 MHz, PM 109 | gain −6.3 / −7.5 / −8.8, GBW −57 | **0**(60·10·70, slsqp_4 ×2, candidate_failure 14회) |
| folded | gain ≥ 60, GBW ≥ 30 MHz PM ≥ 60 / GBW ≥ 100 MHz PM ≥ 70 | 같음 | 켜짐 | 같음 | 같은 꼴 | 같은 꼴 | -- |
| CG | 없음(현행) | gain_l `constraint_not_declared`, speed `gbw_target_missing` | 꺼짐 | converged / sealed | noise_excess 1.35 | noise +1.6 | **2**(B80과 같음) |
| CG | gain ≥ 30 / 35 / 40 | gain_l **`u9_value_not_certified`** | 꺼짐 | 같음(L 0.18 µm, 전력 0.27 nW) | gain **17.5 dB** | gain −3.4 / −4.8 / −6.2 | **0** / **0** / --(slsqp_4 ×2) |
| CG | gain ≥ 30, GBW ≥ 10 MHz 또는 1 GHz (CL 없음) | speed `pm_target_missing` | 켜짐, **`macro_root_missing`(target_not_reached_at_upper_limit)**, gm 0.76 nS, UGF 8.6 kHz | converged / **failed**(출발 사다리 칸 봉인 9 위반 M3) → Halton 1점 | gain 19.3 dB, GBW 11.8 kHz, 전력 **3.07 mW** | GBW −2.6e3 / −2.6e5 | -- |

(folded GBW 선언 시 출발 사다리 칸 0: θ 전류 M3·M4·M5·M6·MP가 모두 `uncovered`이고 입력 소자 current_ref = 2.56 nA, L은 모든 소자 첫 앵커 0.15 µm -- `out/rung0.jsonl`.)

해석:
- **gain 선언**: 계획상 gain 모드 활성 조건은 채워지지만, as-built에서는 (i) 층 0이 최소형이라 gain을 보지 않고 (ii) 출발 구간 이득 L 하한(`iv_gain_l`, 41 §6.4-1)이 A_max 미인증(`u9_value_not_certified`, design 41 §5.12.4와 같은 사실)으로 꺼진다. 그래서 L이 첫 앵커(0.15~0.18 µm)에 남아 층 0 점 gain이 folded 29 dB·CG 17.5 dB로 손계산 상한(같은 L에서 folded 37 dB·CG 21~25 dB)보다도 낮고, **CG는 gain 30 dB만 선언해도 front가 2점 → 0점이 된다**(손계산상 L ≥ 0.25 µm면 달성 가능한 값). 원인은 spec이 아니라 B80 일반 결함('층 0이 ss 제약을 보지 않는 출발점 → 외층 SLSQP slsqp_4 → front 0')과 card LA-1 미구현이다(실측 + B80 대조).
- **GBW 선언(folded)**: 매크로는 목표 gm을 정확히 낸다(62.9 µS). 그러나 그 gm이 θ 전류로 옮겨지지 않아(`current_from_macro: stage_current_unavailable`, θ 전류 5개 uncovered) 층 0 점 GBW가 목표의 1/27이다. two_stage_ota는 같은 경로로 매크로 전류가 θ에 들어간다(B80 §2 표 '매크로(GBW → gm → I) 0.90 µA / 24.8 µA'). 원인 **추정**: folded의 KCL 기저에서 입력 소자 전류가 θ 전류의 차(I_M1 = θ_M3 − θ_M6 꼴)라 `iv_currents`의 '미지 항 하나인 방정식부터 전파' 규칙이 풀지 못한다. → **엔진 gap 후보**(새 결함 등록 여부는 오케스트레이터 판단).
- **GBW 선언(CG, CL 없음)**: 매크로가 근을 못 찾고(`macro_root_missing`) 출발 사다리 칸이 봉인 9에서 떨어져 Halton 점(전력 3 mW)으로 간다. §3.4의 'CL 없는 GBW는 정의가 약하다'는 판정과 맞는 실측이다.
- 결론: **이번에 값을 정해도 as-built에서 front가 생기는 회로는 없다**(CG는 오히려 2 → 0). spec 값이 맞는지의 판정은 LA-1(층 0 gain 모드)과 folded 매크로 전류 배선 뒤에야 의미가 있다. 이것은 spec 값을 낮춰서 풀 문제가 아니다(⚠ 원칙 경고: 「우회/skip 로직은 타당성 검토 후에만 · 결함 사례를 설계 판단 근거로 쓰지 말 것」 — front가 비는 것을 피하려고 gain을 낮추는 것은 엔진 결함을 spec으로 덮는 것이다 — 근거 위 표와 B80 §4).

### 6.3 'spec 실현 불가'와 '출발점 결함' 가르기 -- CG 손계산 출발점 (`scripts/probe_given.py`, `out/probe_given.jsonl`)
- 방법: 현행 CG front 점(FR_base `eps:area_search_m2:2`) θ에서 **L만** M1·M2·M3 = 1 µm(또는 0.5 µm)로 바꾼 점을 `given_starts`로 넣고 무수정 `find_front`(예산 400).
- gain ≥ 35 dB 사본, L 1 µm: 출발점 봉인, 그 점 gain **42.8 dB**(손계산 상한 40.7 dB와 2 dB 안 -- 손계산은 VDS 0.375 V 고정), front **1점**(gain 행 c = +1.10, noise +0.58). 즉 **gain 35 dB는 엔진이 실현한다. 층 0 출발점이 그 영역에 가지 않을 뿐이다.**
- L 0.5 µm(전류 68 pA·1 µA 두 경우): 출발점이 봉인 9(M1 전도 하한)에서 떨어져 front 0. 출발점을 만든 방식(ln IDu 그대로)의 문제이고 판정에는 쓰지 않는다.
- 같은 front 점의 전력은 **13 pW**, 면적 1.4e-12 m²(θ 전류 68 pA). GBW·CL이 없으면 전류를 아래로 묶는 제약이 없어 '사이징이 의미 없음' 쪽 위험이 실제로 나타난다(§5.2 C-B-c 위험 칸의 실측).
- 같은 출발점에 θ 전류 1 µA를 준 경우(ln IDu 그대로라 W가 커져 출발점이 면적 행을 어김): 외층이 s2에서 수렴해 front 1점(전력 18 nW, 면적 1.9e-10 m², L = 1·0.5·1 µm, gain 행 c = +23.5). gain ≥ 35 dB 실현이 두 번 재현된다.

## 7. 권고 (오케스트레이터 참고용 -- 값 확정은 사용자)

원칙 자기 점검: 사용자 지정값만 확정(값을 정하지 않음) · 논문 값 인용 없음(원문에 값 없음) · 회로 이름·heldout 근거 없음 · 자기 실행 역산값 없음(옛 39.7 dB 등 배제) · 물리 정합(손계산 상한 안, CL 없는 GBW 배제) · 관례는 '관례'로만 표지 · DC/AC 분리(전부 AC 소신호 양) · graph 정본 규칙: 이 조사는 spec 값 후보만 내고 계산 자리·cache를 새로 만들지 않는다.

| 회로 | 항목 | 기본안 | 근거 | 대안 비교 |
|---|---|---|---|---|
| folded | PM | ≥ 70° | [관례] library 5/6 회로·파일럿과 같은 값, [손계산] GBW ≤ 100 MHz에서 A0 ≥ 80 dB와 공존 | 60°: 손계산 여유는 더 크나 library 일관성 깨짐 |
| folded | gain | ≥ 70 dB | [손계산] L ≥ 0.5 µm에서 성립, GBW 10~100 MHz·PM 70°에서 여유 10~25 dB, 접힘 캐스코드 고이득 경로(캐스코드 출력 저항)를 실제로 쓰게 하는 값 | 60: 여유 크나 L 0.3 µm로 충분 → 캐스코드 시험 의미 약함 / 80: 여유 8~14 dB(10~30 MHz)이나 모델 오차 미측정이라 fail-closed 위험 |
| folded | GBW | ≥ 10 MHz (사용자 지정 권장) | [손계산] 무릎(100~200 MHz) 훨씬 아래, 공급 ≈ 9 µA로 전력 대가 작음, gain 70 dB·PM 70°와 여유 큼. **물리로 하나가 정해지는 값이 아니다**(전력 예산 PA-1 미선언) | 30 MHz: 공급 ≈ 27 µA, 여유 18 dB / 무릎점: ⚠(§5.1) |
| CG | CL | 1 pF (topology 추가, 사용자) | [관례] library 단일단 확정 CL과 같음. CL 없이는 GBW 정의가 약함(§3.4) | 미선언: GBW도 미선언이 되어 front 전력 13 pW 같은 무의미 점(§6.3) |
| CG | gain | ≥ 35 dB | [손계산] L ≥ 0.45 µm에서 성립, [엔진 실측] 손계산 출발점에서 front 1점(42.8 dB) | 30: 여유 큼 / 40: 상한에 붙음(L 1 µm 여유 0.7 dB) |
| CG | GBW | CL 1 pF에서 ≥ 10 MHz | [손계산] ≈ 3.5 µA, folded 기본안과 같은 대역(같은 CL·같은 측정 대역이라 비교 가능) | 미선언 |

**반영 시점 주의(원래 취지와 다름 가능)**: 이 값을 지금 spec에 넣으면 as-built에서 CG front가 2점 → 0점이 된다(§6.2). IT-0 기준선(M-I3 n_front common_gate 1)과 IT-2c 등 기준 비교가 바뀐다. 값은 맞고 원인은 LA-1 미구현(B80)이므로 값을 낮추지 말고, **반영 시점(지금 / LA-1 병합 뒤)** 을 따로 결정받아야 한다(D7).

## 8. 사용자 결정 목록 (값마다)

| # | 회로 | 결정 | 선택지(후보 ID) | 오케스트레이터 참고 |
|---|---|---|---|---|
| D1 | folded | PM 하한 (SP-3) | F-PM-a 70° / F-PM-b 60° / 미선언 | 관례상 70°가 library 다수값 |
| D2 | folded | gain 하한 (SP-4) | F-G-a 60 / F-G-b 70 / F-G-c 80 / F-G-d 7a − 마진 / 미선언 | 손계산 상한 대비 여유와 '고이득 위상' 시험 의미의 저울질 |
| D3 | folded | GBW 하한 (SP-5) | F-B-a 10 MHz / F-B-b 30 MHz / F-B-c 무릎점 / F-B-d 미선언 | 전력 예산(PA-1)이 없어 물리로 하나가 정해지지 않음 -- 전력 대가 선택 |
| D4 | CG | 부하 CL (SP-6 (c)) -- topology 추가 포함 | C-L-a 1 pF / 다른 값 / C-L-b 미선언 | GBW를 선언하려면 먼저 필요(§3.4) |
| D5 | CG | gain 하한 (SP-4) | C-G-a 30 / C-G-b 35 / C-G-c 40 / 미선언 | |
| D6 | CG | GBW 하한 (SP-5) | C-B-a (CL 정해진 뒤 값) / C-B-c 미선언 | C-B-b(CL 없이 선언)는 ⚠ |
| D7 | 둘 다 | spec 반영 시점 | 지금 / card LA-1(층 0 gain 모드) 병합 뒤 / folded 매크로 전류 gap 처리 뒤 | 지금 반영하면 CG front 2 → 0, 기준선 변화 예고 필요(작성자≠검증자 규칙상 기준 변경은 사용자 승인) |
| D8 | folded | 매크로 gm → θ 전류 미전파(§6.2)를 결함으로 등록할지 | 등록(backlog) / LA-1 범위에 포함 / 보류 | 원인은 '추정' -- 확인 실측이 먼저 필요 |

## 9. 미확인
- 손계산은 VDS 0.375 V 고정·폭 비례·격자 gm/ID 3점·근사 극점식이다. 엔진 MNA(DEC-92)·SPICE 대조값이 아니다(모델 오차 DEC-72 미측정).
- folded PM 근사에서 미러 경로 극점(Vg7·Vg9)의 용량 배정은 단순화(다이오드+거울 게이트 2배)했다. 정량 PM은 ±수 도 오차가 있을 수 있다(미검증).
- CG gain 40 dB 후보의 면적(0.005 mm² 예산) 안 실현 여부는 재지 않았다.
- 입력 DC(SP-2) 미결이라 엔진 실측은 W4 자유 노드전압(엔진 기본)으로 돌았다. CG M2 VS(= vin DC)를 0.2·0.4 V로만 손계산했다.
- folded의 매크로 gm이 θ 전류로 옮겨지지 않는 원인(§6.2)은 `iv_currents` 전파 규칙과 folded KCL 기저(θ 전류 = M3·M4·M5·M6·MP, 입력 소자 전류 = 차)의 조합으로 **추정**한다 -- 코드 경로를 끝까지 추적하지 않았다.
