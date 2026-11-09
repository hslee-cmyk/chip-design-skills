# library 9회로 출력 절대 범위 후보 (DK5 조사, 2026-10-26)

- 역할: spec 후보 조사자(읽기 전용). 값 확정은 사용자 몫(O-151 DK5 "후보 조사 후 사용자 확정"). 이 문서는 후보·근거·논리만 낸다.
- 정의(계획 gain-budget v6.38): 출력 범위 = 출력 포트(차동이면 Vod -- O-131, O-151 A3) 전압의 spec 절대 범위 [V_lo, V_hi]. SF-1 범위 3(계획 2140행), DEC-65(264행) 범위 끝 V에서 I_cap,d, DEC-104 R1 (b)·R2 (b)·R8·R10(303행)이 R_ss,d를 정의하는 데 쓴다. DC 양이다. 미선언이면 범위 끝 양은 정의 불능이다(fail-closed, O-128 Q5).
- 근거로 쓴 것: 원문 PDF(아래 표), 각 `*.sizing_spec.json` human 선언, `*.topology.json`의 netlist·passive_elements connectivity, `wt/_drafts/user_decisions.md` 결정. topology 태그(device_roles 등)와 heldout은 쓰지 않았다. `_paper_target_spec` 주석은 원문과 대조하는 데만 보고, 값은 원문 쪽에서 다시 읽었다.
- 작업 파일: `C:/Users/HSLEE/Documents/Todoc/fpga/wt/_scratch_outrange/`(spec·topology 덤프, Leung Fig. 6·Lee p.5·p.6 고해상도 렌더).

## 0. 원문 출처

| 회로 | 원문 | 웹 | 로컬 PDF(skill 폴더 `assets/library/sources/`) |
|---|---|---|---|
| current_reuse_telescopic_ota | Xie·Chen, "A 126µW Current-Reuse Telescopic OTA with Class-AB Output Stage" (UT Austin, 2019) | 찾지 못함 | `current_reuse_telescopic_ota__xie_chen_2019/source.pdf` |
| nmcnr_amplifier | Leung·Mok·Ki, ICECS 1999 pp.599-602 | IEEE Xplore(유료) 링크 찾지 못함 | `nmcnr_amplifier__leung_1999/source.pdf` |
| ngcc_3stage_ff | Lee et al., JSTS 7(1):20-27, 2007 | https://doi.org/10.5573/JSTS.2007.7.1.020 | `ngcc_3stage_ff__lee_2007/source.pdf` |
| pushpull_follower_buffer, sf_pushpull_output_opamp, two_stage_ota_sf | Allen, Lecture 26 "Buffered Op Amps" (6/25/14) | https://aicdesign.org/wp-content/uploads/2018/08/lecture26-140625.pdf | `pushpull_follower_buffer+sf_pushpull_output_opamp+two_stage_ota_sf__allen_2014/source.pdf` |
| common_gate_amplifier | Allen, Lecture 20 "Low Input Resistance Amplifiers" (6/24/14) | https://aicdesign.org/wp-content/uploads/2018/08/lecture20-140624.pdf | `common_gate_amplifier__allen_2014/source.pdf` |
| two_stage_ota, folded_cascode | Maloberti, "Layout of Analog CMOS IC, Part 2" (2004) | 저자 게시처 찾지 못함 | `two_stage_ota+folded_cascode__maloberti_2004/source.pdf` |

## 1. 회로별 권고 요약

| 회로 | 출력 포트(connectivity) | 권고 범위 | 근거 출처 | 유도 논리(한 줄) | 확신도 | 사용자 확인 포인트 |
|---|---|---|---|---|---|---|
| current_reuse_telescopic_ota | 차동 Vop/Vom(M25/M26·M15/M16, 두 방향 모두 신호 구동 셀) | **Vod ∈ [−1.2, +1.2] V**, 노드별 Vop·Vom ∈ [0.3, 1.5] V(출력 CM 0.9 V) | Xie·Chen Table I p.1 'Output swing spec [−1.2V, 1.2V]'(차동 Vod -- Fig. 10 p.10 가로축 Vod), 초록 p.1 'output common-mode voltage level to 0.9V', 기존 `swing_out_v ≥ 2.4`(Q4 (5)), O-131·O-134 A3 노드 사상 | 원문 spec 값이고 공급(1.8 V)이 같다. 사용자가 이미 같은 값(폭 2.4)과 같은 노드 사상(0.9 → 1.5/0.3 V)을 승인했다 | 높음(Vod) / 중간(노드 CM 0.9 V의 선언 자리) | (1) Vod로 선언 + CM 0.9 V를 spec으로 둘지, 노드 범위를 직접 선언할지 (2) 원문 swing은 '3 dB 이득 저하' 정의, `swing_out_v`는 '포화 기준' -- 정의 축 차이 |
| nmcnr_amplifier | 단일 Vout(M302 PMOS 바이어스 구동 레일 source = 공급, M301 NMOS 신호 구동 = 흡수), 부하 RL 25 kΩ ∥ CL 100 pF → agnd 0.9 V | **[0.65, 1.15] V**(후보 A) | Leung Table 1 주 p.602 'unity-feedback configuration with 0.5V step input', Fig. 6 p.602(0.50 V/div, 계단 1칸), 공급 ±1 V p.601; 기존 `swing_out_v ≥ 0.5`·`icmr_v ≥ 0.5`(Q4 (4)); agnd 0.9 V·RL→agnd(Q8) | 원문은 폭(0.5 V)만 있고 절대 위치가 없다. 원문 부하 기준(접지 = ±1 V의 중간)을 사용자가 agnd 0.9 V로 옮긴 사상(Q8)대로 부하 기준을 범위 중심에 둔다 | 낮음~중간(위치는 원문에 없음) | (1) 위치: 중심(A) / agnd에서 위로(B [0.9, 1.4]) / 아래로(C [0.4, 0.9]) -- R_ss와 M302 전류 하한이 갈린다(§2.2) (2) settle 계단(O-145, 0.5 V)의 절대 위치도 같이 정해야 한다 |
| ngcc_3stage_ff | 단일 Vout(M12 PMOS 바이어스 구동 = 공급, M13·M14·M7 NMOS 신호 구동 = 흡수), CL 10 pF → gnd | **[0.14, 0.54] V**(후보 B) | Lee Fig. 5 p.25(PDF p.6) 단위 이득 계단 0.14 → 0.54 V(VDD 1.2 V), O-145·O-130 계단 = 원문 0.14 → 0.54 V(절대값 유지 승인) | 원문에 출력 범위 spec은 없다. 이미 승인된 settle·SR 계단(절대값)을 범위로 쓰면 계단 ⊆ 범위 정합이 정확히 맞는다 | 중간 | (1) 비례 환산 [0.21, 0.81] V(ICMR VDD/3 환산 선례)는 O-145 계단 0.14 V를 담지 못한다 -- 둘 중 하나 (2) 범위 아래 끝 0.14 V는 M13·M14·M7 VDS = 0.14 V 포화를 요구한다(gm/ID 압력) |
| two_stage_ota | 단일 OUT(M6 신호 구동 PMOS, M7 바이어스 구동 NMOS), CL 3 pF | **미선언 유지** | 원문 전기 사양 없음(Maloberti p.28 'Width only are shown; Compensation network and bias are missing') | 수치 근거 0, swing_out_v도 미선언 | -- | 사용자 직접 지정 원하면 값 |
| two_stage_ota_sf | 단일 vout(M8 NMOS follower 신호 구동 = 공급, M9 바이어스 구동 NMOS = 흡수), CL 3 pF | **미선언 유지** | Allen L26 p.26-3 'Maximum upper output voltage is limited'(정성), p.26-5 도면 값 없음 | 수치 근거 0 | -- | 같음 |
| folded_cascode | 단일 out(M6 PMOS·M8 NMOS 캐스코드, 레일 source 셀 아님), CL 1 pF | **미선언 유지** | Maloberti p.34 'Only Ws are shown' | 수치 근거 0 | -- | 같음 |
| common_gate_amplifier | 단일 vout(M3 PMOS 바이어스 구동 = 공급, M2 NMOS CG = 흡수) | **미선언 유지** | Allen L20 p.20-2: VOUT(max) ≈ VDD − VDS3(sat), VOUT(min) ≈ VDS1(sat) + VDS2(sat) -- 식만, 수치 없음 | 식은 회로 능력(포화 한계)이지 요구가 아니다(요구를 능력으로 정의하면 순환 -- load_drive_principle_audit D2 (라)) | -- | 같음 |
| pushpull_follower_buffer | 단일 vout(M1 NMOS·M2 PMOS follower, 두 방향 신호 구동), CL 1 pF → agnd | **미선언 유지** | Allen L26 p.26-4 'Maximum positive and negative output voltages are limited'(정성) | 수치 근거 0 | -- | sf_pushpull과 같은 값을 쓸지(값 하나를 참조로) |
| sf_pushpull_output_opamp | 단일 vout(M22 NMOS·M21 PMOS follower, 신호 구동), CL 1 pF → agnd | **미선언 유지** | Allen L26 p.26-6 Fig. 7.1-1: Rout ≤ 1000 Ω, Av(0) 65 dB, GB 60 MHz만 | 수치 근거 0 | -- | 같음 |

## 2. 회로별 상세

### 2.1 current_reuse_telescopic_ota

**원문**
- Table I(p.1, 'design specifications and result summary'): 'Output swing | Specs [-1.2V, 1.2V] | Our Results [-1.706V, 1.706V]'. 공급 1.8 V(초록 p.1, IV절 p.4: 'the supply voltage is 1.8V'), 공정 0.18 µm.
- 이 값은 **차동 Vod**다: Fig. 10 p.10 'DC gain versus output swing' 가로축 'Vod (V)' -1.8~1.8, 표지 M2·M3 = ±1.70626 V에서 72.672 dB = 중앙 75.672 dB − 3 dB. 즉 원문 결과값의 정의 = '차동 이득 3 dB 저하점'.
- 출력 CM: 초록 p.1 'a common-mode feedback (CMFB) circuit is used to stabilize the output common-mode voltage level to 0.9V'.
- 단일 전원 정합: Vod ±1.2 V를 CM 0.9 V에 두면 Vop·Vom 각각 0.9 ± 0.6 = [0.3, 1.5] V로 레일 [0, 1.8] 안이다. 원문 결과 ±1.706 V도 노드로는 0.9 ± 0.853 = [0.047, 1.753] V로 레일 안이다. 'current_reuse ±1.2 V가 단일 전원에서 불가능'은 Vod를 노드 전압으로 읽은 오독이다(O-131 표기 규칙).

**기존 선언과 관계**
- `swing_out_v ≥ 2.4`(user_decisions 2026-10-08 Q4 (5), citation 'Xie & Chen 원문 Table I 출력 스윙 +-1.2 V', '포화 기준 swing_out_v'). 범위 폭 2.4 = swing_out_v 2.4로 여유 없이 같다.
- O-131·O-134 A3 계단 'Vod 0 → ±1.2 V (Vop·Vom 각각 0.9 V → 1.5 V / 0.3 V)'를 이미 승인했다. 계단 ⊆ 범위가 정확히 맞는다.

**후보**

| 칸 | (A) Vod [−1.2, 1.2] V + CM 0.9 V(노드 [0.3, 1.5] V) | (B) 원문 결과 Vod [−1.706, 1.706] V | (C) Vod만 선언, 노드는 CMFB DC 해의 CM에서 |
|---|---|---|---|
| 물리 정합 | ○ 레일 안, 포화 여유 0.3 V(노드마다) | ○ 레일 안이나 레일에서 47 mV(0.18 µm 3 dB 점, sky130에서 포화 불가 가능성 큼) | △ 노드 값이 설계점에 기댐 |
| 원문 일치 | ○ spec 열 | 결과 열(spec 아님) | ○ |
| 기존 spec 정합 | ○ swing_out_v 2.4·O-131·O-134 계단과 같음 | × swing_out_v보다 넓다(요구 상향) | ○ |
| 일반성 | ○ 차동 회로 공통 꼴(Vod 범위 + CM) | -- | ⚠ 원칙 경고: DEC-103 -- 요구(spec 양)가 설계점(CMFB DC 해)에 기댐(load_drive_principle_audit D2 (다)와 같은 결함) |

**권고 (A)**, 확신도 높음(Vod) / 중간(CM 0.9 V를 spec 칸으로 둘지). 논문 값 그대로 인용 금지와의 관계: 이 값은 이미 사용자가 Q4 (5)에서 spec으로 채택했고 공급(1.8 V)이 같아 환산이 필요 없다. 공정이 달라 생기는 차이(포화 여유)는 요구가 아니라 엔진이 판정할 능력 쪽이다.

**사용자 확인 포인트**
1. 노드 범위의 CM 0.9 V를 spec으로 선언할지(원문 초록 p.1, O-131 표기에서 이미 사용). topology에서 `Voc_des`는 M39/M40이 만드는 내부 넷이라 CM은 지금 선언이 아니라 회로 결과다(`node_voltage_targets_v`는 pending CI-15).
2. 정의 축 차이: 원문 swing = 3 dB 이득 저하점(Fig. 10), 이 저장소 `swing_out_v` = 포화 기준. 같은 이름의 범위로 묶을 때 '측정 구성·판정 기준이 다르다'를 기록해야 한다(graph 규칙 3).
3. R_ss: 응용 망(원문 구성 Cs·Cf·CL)은 DC에서 모두 용량이라 R_ss = 0이다. CMFB 감지 저항 R1·R2(Vop–Voc–Vom)는 DUT 소자라 능력 쪽 KCL에 들어간다(Vod ≠ 0이면 Vod/(R1+R2) 전류가 흐름) -- R_ss로 세면 안 된다.

### 2.2 nmcnr_amplifier

**원문**
- Leung p.601(PDF p.3) 5절: 'Both amplifiers have a supply voltage of +/-1V and a load of 100pF in parallel with 25kΩ'.
- Table 1 주(p.602, PDF p.4): 'Slew rate and settling time were measured at unity-feedback configuration with 0.5V step input'. Fig. 6 p.602: 세 채널 모두 2 µs·0.50 V/div, 입력·출력 계단 높이 1칸(= 0.5 V). 고해상도 렌더(`_scratch_outrange/leung_fig6.png`)에서도 채널 접지 표지로 계단의 **절대 위치는 읽을 수 없다**.
- 출력 스윙·출력 범위 문장 없음(전문 grep 'swing'·'output voltage' -- 'settle the output voltage' 한 곳뿐, 범위 아님).

**기존 선언과 관계**
- `swing_out_v ≥ 0.5`(Q4 (4), '원문 단위 이득 0.5 V 계단 측정 조건'), `icmr_v ≥ 0.5`(같은 근거, U-104 사용자 지정 최소 요구). 범위 폭은 0.5 V 이상이어야 한다.
- 레일 vdd 1.8·vss 0·agnd 0.9, RL·CL → agnd(2026-10-12 Q8 '원문 ±1 V를 1.8/0 + agnd 0.9 pushpull 형태로').
- O-145 settle 계단 '원문 0.5 V'도 절대 위치가 아직 없다. 범위 위치를 정하면 계단 위치도 그 안에서 정해야 한다.

**R_ss 계산(DEC-104 R1 (b), 응용 망 = RL ∥ CL → agnd, DC는 RL만)**: R_ss(V) = (V − 0.9 V)/25 kΩ(양 = 출력이 내보냄).

| 칸 | (A) [0.65, 1.15] V(agnd 중심) | (B) [0.9, 1.4] V(agnd에서 위로 0.5 V) | (C) [0.4, 0.9] V(agnd에서 아래로 0.5 V) |
|---|---|---|---|
| 범위 끝 R_ss | 위 끝 +10 µA(공급, M302), 아래 끝 −10 µA(흡수, M301) | 위 끝 +20 µA, 아래 끝 0 | 위 끝 0, 아래 끝 −20 µA |
| R10 정확한 하한 대상 | 공급 방향 셀 M302 = 바이어스 구동 레일 source → (i) I_M302(1.15 V) ≥ 10 µA | (i) I_M302(1.4 V) ≥ 20 µA(VSD 0.4 V) | 공급 방향 R_ss 0. 흡수 M301은 신호 구동 → 추정 목표만 |
| 물리 정합 | ○ | ○ | ○ |
| 원문 일치 | 폭만 일치(위치는 원문에 없음) | 같음 | 같음 |
| 기존 spec 정합 | 폭 = swing_out_v 0.5 | 같음 | 같음 |
| 일반성 | 부하 기준 중심 = 위치 규칙이 아니라 이 회로의 사용자 지정 값으로만 써야 한다 | 같음 | 같음 |
| 원칙 | ⚠ 원칙 경고: 상수 발명 금지 -- '부하 기준 중심'을 엔진 규칙으로 쓰면 관례를 정의로 쓰는 것(load_drive_principle_audit D2 (나)). 사용자 지정 값이면 정합 | 같은 경고(시작점 = agnd 가정) | 같은 경고 |

**권고 (A) [0.65, 1.15] V**, 확신도 낮음~중간. 근거: 원문 ±1 V의 부하 기준(접지)은 공급 중간이고, 사용자가 그 기준을 agnd 0.9 V로 옮겼다(Q8). 계단 위치가 원문에 없으므로 양 방향 R_ss를 같게 두는 꼴이 가장 적게 가정한다. 원문 공급 폭 2 V → 1.8 V 축소에도 폭 0.5 V는 사용자가 절대값으로 정했다(Q4 (4)).

**사용자 확인 포인트**
1. 위치 A/B/C -- 공급 셀 M302 전류 하한이 10 µA / 20 µA / 0으로 갈린다(SB-1 R8·R10 (i)).
2. 실현 가능성 참고(spec 근거 아님): 한 설계점 SPICE servo ICMR 폭 0.409 V, 위 끝을 묶은 소자 M302(evidence/2026-10-23 decision_audit_O61_O117.md 232행, nmcnr_linear_end_cause.md). 즉 이 회로의 위 끝은 RL로 전류를 대는 M302가 먼저 묶는다 -- 위 끝을 높게 둘수록(B) M302 전류 압력이 커진다.
3. follower 계단(settle·SR)을 범위 안에 두려면 PMOS 입력쌍(M102·M103) ICMR도 그 위치를 덮어야 한다(단위 이득에서 입력 = 출력). DEC-65 범위 정의 자체는 입력을 따로 몰기 때문에 ICMR에 묶이지 않는다 -- 두 양을 섞지 말 것.

### 2.3 ngcc_3stage_ff

**원문**
- Lee p.24(PDF p.5) IV절: 'Power supply voltage was set to 1.2V', spec 'k = 4, GB=10MHz, PM=63.4˚, ICMR= 0.4V'. 식 (9) ICMR = V_DD − 5V_DSAT − V_TH, 식 (10) V_DSAT 조건, Table 4 V_DSAT = 80 mV.
- Fig. 5 p.25(PDF p.6) 'Simulated step response (CL=10pF, CL=100pF and α = 0.3)': 입력 0.14 V → 0.54 V(세로축 0.10~0.60 V), 출력이 같은 범위를 따라감(단위 이득, beta = 1은 추론 -- O-130 기록).
- 출력 스윙·출력 범위 문장·표 항목 없음(Table 5·6 항목: DC gain, PM, GBW, 1% settling, Power, gm, Cm, 면적).

**기존 선언과 관계**
- `icmr_v ≥ 0.6`(VDD/3를 1.8 V로 환산, U-39·U-34 사용자 확정). swing_out_v 미선언.
- O-130 확정: 상승 SR ≥ 6.3 V/µs(Fig. 5, 0.4 V 계단). O-145: settle_s ≤ 120 ns, ε 1 %, **계단 = 원문 0.14 → 0.54 V**(절대값 그대로, 1.8 V로 환산하지 않음), 상승만.

| 칸 | (A) 비례 환산 [0.21, 0.81] V(×1.8/1.2) | (B) 원문 절대 계단 [0.14, 0.54] V | (C) [0.14, 0.74] V(계단 시작 + ICMR 폭 0.6) |
|---|---|---|---|
| 물리 정합 | ○ | ○ 아래 끝 0.14 V에서 흡수 셀(M13·M14·M7) VDS = 0.14 V 포화 필요(원문 V_DSAT 80 mV 설계는 만족; sky130에서는 gm/ID 압력) | ○ |
| 원문 일치 | △ 환산값 | ○ 그림 값 그대로 | × 원문에 없는 조합 |
| 기존 spec 정합 | × O-145 계단 0.14 V를 담지 못함(계단 ⊄ 범위) | ○ O-130·O-145 계단 = 범위 | ○ 계단 ⊆ 범위 |
| 일반성 | ICMR VDD/3 환산 선례와 같은 규칙 | 다른 원문 구성 회로(O-131 '원문 계단 꼴')와 같은 규칙 | ⚠ 원칙 경고: 상수 발명 금지 -- 두 출처를 이어 붙인 값 |

**권고 (B) [0.14, 0.54] V**, 확신도 중간. 근거: 이미 승인된 settle·SR 계단(원문 절대값)과 범위가 정확히 같아 계단 ⊆ 범위 정합이 자동이고 새 값이 없다.

**사용자 확인 포인트**
1. (A)를 고르면 O-145 계단도 [0.21, 0.81] V로 바꿔야 정합한다(원래 취지와 다름 -- O-145 '원문 값 사용' 변경).
2. 부하가 CL만이라 R_ss = 0이다. 범위의 효과는 범위 끝 헤드룸 고리(R8 '범위 끝 헤드룸 고리')와 I_cap ≥ 0뿐이다.

### 2.4 원문에 수치 근거가 없는 6회로

| 회로 | 원문 확인 내용(쪽) | 대안 | 권고 |
|---|---|---|---|
| two_stage_ota | Maloberti p.28 'Width only are shown; Compensation network and bias are missing (!)', p.28~33 레이아웃만 | (가) 미선언 유지 (나) 사용자 직접 지정 | (가) |
| folded_cascode | Maloberti p.34 'Only Ws are shown', p.34~38 레이아웃만 | 같음 | (가) |
| common_gate_amplifier | Allen L20 p.20-2 'Large Signal Characteristics: VOUT(max) ≈ VDD – VDS3(sat), VOUT(min) ≈ VDS1(sat) + VDS2(sat)' -- 식만 | 같음. 식을 범위로 쓰는 안은 기각(요구를 능력으로 정의 = 순환, 판정이 늘 통과 -- D2 (라)) | (가) |
| two_stage_ota_sf | Allen L26 p.26-3 'Maximum upper output voltage is limited'(class-A SF, 정성), p.26-5 도면 값 없음 | 같음 | (가) |
| pushpull_follower_buffer | Allen L26 p.26-4 'Maximum positive and negative output voltages are limited'(정성) | 같음, 또는 sf_pushpull 값을 참조(값 하나 -- 사본 금지) | (가) |
| sf_pushpull_output_opamp | Allen L26 p.26-6 Fig. 7.1-1: 'Rout ≈ 1/(gm21+gm22) ≤ 1000Ω, Av(0)=65dB (IBias=50µA), and GB = 60MHz for CL = 1pF'만. p.26-27 요약도 Ro 범위만 | 같음 | (가) |

(가) 미선언 유지의 근거:
- P1 상수 발명 금지·O-135 선례(원문 근거 없는 SR은 미선언, 사용자가 나중에 지정 가능)와 같은 처리다.
- 이 6회로는 SR 미선언(O-135)이고 부하가 용량뿐(CL; DC 부하 원소 없음)이라 R_ss = 0이다. 범위를 선언해도 추가되는 요구는 '범위 끝 포화(헤드룸) 고리'뿐이고, 지금도 swing_out_v가 없어 출력 스윙 요구가 없다. 미선언은 현 spec 내용을 바꾸지 않는다.
- 미선언이면 DE-1의 I_cap·class-AB 보고가 이 회로에서 정의 불능으로 남는다(보고 손실, 판정 손실 없음).
- 실현 가능성 참고(spec 근거 아님): 한 설계점에서 two_stage_ota_sf 출력 위 끝 1.012 V, folded_cascode 하강이 0.915 V에서 멈춤(evidence/2026-10-23/audit_slew_classab_nmcnrspec.md 34·39행). 사용자가 직접 지정한다면 이 값보다 넓은 범위는 엔진이 다른 설계점을 찾아야 한다는 뜻이다.

## 3. 원문에 근거가 전혀 없는 회로

- 수치 근거 0: two_stage_ota, folded_cascode(Maloberti -- 전기 사양 자체가 없음), two_stage_ota_sf, pushpull_follower_buffer, sf_pushpull_output_opamp(Allen L26 -- 정성 문장만), common_gate_amplifier(Allen L20 -- 능력 식만).
- 위치 근거 0, 폭 근거만: nmcnr_amplifier(0.5 V 계단 폭).
- 원문 spec 값 있음: current_reuse_telescopic_ota(Vod ±1.2 V). ngcc_3stage_ff는 spec 문장은 없고 그림 계단(0.14~0.54 V)만 있다.

## 4. 정의상 문제(따로 결정 필요)

1. **차동 출력의 노드 범위**(current_reuse): DEC-65·O-151 A3는 측정 노드 = Vod다. 그런데 R9 계산법은 소자 LUT를 V_DS = 출력 범위 끝으로 조회하므로 노드 전압(Vop·Vom 각각)이 필요하다. Vod만 선언하면 노드 값 = CM ± Vod/2이고 CM이 필요하다. CM을 CMFB DC 해에서 읽으면 요구가 설계점에 기댄다(⚠ 원칙 경고: DEC-103). 선택: (i) Vod 범위 + CM(0.9 V) spec 선언 (ii) 노드 범위 직접 선언. 또 Vod 범위 끝은 두 노드가 반대 끝(1.5 V·0.3 V)에 동시에 있는 상태라 방향별 I_cap,d 정의(공급/흡수)를 노드마다 따로 읽어야 한다 -- design에서 정의 필요.
2. **swing_out_v와 출력 범위의 둘째 원천**: 절대 범위가 선언되면 폭 요구(V_hi − V_lo)가 그 안에 들어 있다. `swing_out_v ≥ 값`(nmcnr 0.5, current_reuse 2.4)을 따로 두면 같은 요구가 두 자리에 선언된다(⚠ 원칙 경고: graph 규칙 1·3 -- 같은 정의 양은 필드 하나). 다만 `swing_out_v`는 능력(포화 기준 DC 동작 범위 폭) 측정값의 문턱이고 범위는 위치를 가진 요구라, 정의 축이 다르다고 볼 수도 있다. 처리안: (a) 범위 선언 회로는 swing_out_v 문턱을 범위 폭 참조로(value_from) (b) swing_out_v 판정을 '범위 ⊆ 능력 창' 판정으로 대체. **원래 취지와 다름** 가능성(Q4 (4)(5) 선언 형태 변경)이라 사용자 결정.
3. **계단 ⊆ 범위 정합**: settle·SR 계단(current_reuse Vod 0→±1.2 V, ngcc 0.14→0.54 V, nmcnr 0.5 V 위치 미정)은 선언 출력 범위 안이어야 한다. 이 정합 검사 자리(spec 로더 SF-1 검사인지)를 정해야 한다. nmcnr는 계단 위치도 함께 정해야 한다.
4. **용량 부하 회로에서 범위의 쓰임**: library 9회로 중 DC 부하 원소가 있는 회로는 nmcnr(RL)뿐이다. 나머지는 R_ss = 0이라 범위는 R8 '범위 끝 헤드룸 고리'로만 작동한다. 또 O-151 N-1로 R10 (ii) 동적 항의 창은 '레일 전 범위'라 선언 범위를 읽지 않는다 -- 그렇다면 SR을 선언한 ngcc에서도 R10 (ii)는 범위 없이 정의되고, 범위가 필요한 것은 (i)·R8뿐이다. design_v115_plan_defects.md DK5 문장('SR을 선언한 nmcnr·ngcc도 R10 하한이 동작하지 않는다')은 N-1 반영 뒤 기준으로 다시 확인할 것(이 조사에서는 design 원문을 대조하지 않았다 -- 미확인).
5. **원문 swing 정의와 판정 정의**: current_reuse 원문 결과값은 '3 dB 이득 저하'로 잰 폭이다. 이 저장소의 범위 판정(포화 기준, DC 해)과 정의가 다르므로 원문 결과값 ±1.706 V를 능력 기대값으로 비교하면 안 된다.

## 5. 원칙 자기 점검

| 항목 | 결과 |
|---|---|
| 상수 발명 | 없음. 값은 원문(Table I·Fig. 5)·기존 선언(swing_out_v·agnd·계단)에서만. nmcnr 중심 위치는 '사용자 지정 값' 후보로만 제시(엔진 규칙 아님, ⚠ 표기) |
| 논문 값 그대로 인용 | current_reuse: 공급 같음 + 사용자 이미 채택(Q4 (5)). ngcc: 사용자가 O-145에서 절대 계단 사용을 이미 승인 -- 범위는 그 계단과 같게. 비례 환산 대안 병기 |
| graph 단일 정본 | 범위 = spec 필드 하나(writer = spec 해석 블록, R1). swing_out_v 중복 위험을 §4-2로 올림. 노드 범위를 CMFB DC 해에서 다시 계산하는 둘째 생산자 안은 ⚠ 표기 |
| DC/AC 분리 | 범위·R_ss·I_cap 모두 DC 양. 원문 3 dB 이득 저하 정의(AC 소신호 기준)와 구분(§4-5) |
| topology 태그·heldout | 쓰지 않음(netlist connectivity와 원문만) |
| 확인 안 한 것 | design 41/42의 R10 창·차동 I_cap 정의 원문 대조(§4-4), sky130 LUT로 범위 끝 포화 실현성 계산(한 설계점 as-built 관찰값만 참고로 인용) |
