# 13회로 공급 구성 감사 -- dual 원문 -> 중간 레일, single 원문 -> VSS 접지 (2026-10-21)

- 작성 2026-10-21, 분석 agent(읽기 전용, 저장소 무변경). base master `c237d96e`.
- 판정 원칙(사용자 2026-10-21): agnd 같은 중간 레일은 **dual supply(±V, 0 V 접지) 원문을 single supply(0..1.8 V)로 옮길 때만** 둔다. 원문의 접지는 선언된 중간 레일로 간다. single supply 원문은 VSS가 접지이고, 중간 레일을 새로 만들지 않는다.
- 대상: `de1_output_structure_13.md`와 같은 13회로(library 9 + heldout 4).
- 근거: 원문은 `assets/{library,heldout}/sources/*/paper.md`의 텍스트 추출본만 썼다(쪽 = `## p.N` 머리). 이식본은 `*.topology.json`의 `supply_nets`·`passive_elements`·`ideal_sources`·`netlist`와 `*.sizing_spec.json`의 `human.supplies_v`·`human.input_dc`·`element_values`를 봤다. **회로도 이미지는 읽지 않았다.** device_roles와 topology 주석은 근거로 쓰지 않았다. 주석은 '미확인 힌트'로만 적었다.
- 경로 약어: `L` = `chip-design-skills/skills/analog-gmid-design/assets/library`, `H` = `.../assets/heldout`.

## 1. 요약 표

| # | 회로 | 원문 공급(텍스트 근거) | 원문 구성 | 이식 supply_nets / supplies_v | 중간 레일 | 접지 쪽 소자의 대응 | 판정 | 확신도 |
|---|---|---|---|---|---|---|---|---|
| 1 | common_gate_amplifier | 값 없음. p.20-2 `VOUT(min) ≈ VDS1(sat)+VDS2(sat)`, p.20-7 "negative power supply (ground in this case)" | single | vdd/gnd; 1.8/0 (user 2026-10-07) | 없음 | M1.s->gnd | **일치** | 중상 |
| 2 | current_reuse_telescopic_ota | "1.8V power supply" p.1, p.4; 도면 텍스트 GND | single 1.8 V | vdd/gnd; 1.8/0 (user 2026-10-07) | 없음 | CL1·CL2·Cs1·Cs2·Iref·M40(Voc_des)->gnd | **일치** | 상 |
| 3 | folded_cascode | 값 없음. 같은 문서 p.30·p.33(two-stage 쪽)에 VDD·GND 라벨만. p.34~38(folded) 텍스트에는 레일 라벨 없음 | single로 추정 | vdd/gnd; 1.8/0 | 없음 | CL->gnd | 일치(추정) | 중하 |
| 4 | ngcc_3stage_ff | "Power supply voltage was set to 1.2V" p.5, "1.2V supply" p.6, "ICMR≥VDD/3" p.5 | single 1.2 V | vdd/gnd; 1.8/0 (user 2026-09-16) | 없음 | CL->gnd | **일치** | 상 |
| 5 | nmcnr_amplifier | "supply voltage of +/-1V and a load of 100pF in parallel with 25kΩ" p.4(저널 p.602), Table 1 "+/- 1 V" | **dual ±1 V** | vdd/vss/agnd; 1.8/0/0.9 (user 2026-10-12 Q8) | agnd 0.9 | CL·RL->agnd(대응 맞음), NMOS source->vss(-1 V 레일) | 레일·부하 **일치**. 입력 DC 미선언(SP-2) -- 대응상 agnd여야 함 | 상 |
| 6 | pushpull_follower_buffer | p.26-4 텍스트에 공급 값 없음, 레일 라벨은 VDD만(VSS 없음). "Maximum positive and **negative** output voltages are limited" | **불명**(텍스트 상충) | vdd/vss/agnd; 1.8/0/0.9 (U-39 2026-09-21) | agnd 0.9 | CL->agnd, input_dc=agnd, M2·M3.d·M6.s->vss | **공동 분석 필요** | 하 |
| 7 | sf_pushpull_output_opamp | p.26-6 Fig.7.1-1 텍스트: VDD·**VSS** 라벨 따로 있음, 공급 값 없음 | dual로 추정(VSS가 접지와 다른 이름) | vdd/vss/agnd; 1.8/0/0.9 (U-39) | agnd 0.9 | Cc·CL->agnd, input_dc=agnd, NMOS source->vss | 일치(추정) | 중하 |
| 8 | two_stage_ota | 값 없음. p.30·p.33 VDD·GND 라벨, "Vdd and GND crossing the cell" | single로 추정 | vdd/gnd; 1.8/0 | 없음 | CL->gnd | 일치(추정) | 중 |
| 9 | two_stage_ota_sf | p.26-5 "Power dissipation now becomes (I5+I7+I9)VDD", 레일 라벨 VDD만 | single | vdd/gnd; 1.8/0 (user 2026-10-07) | 없음 | CL->gnd, M9.s->gnd | **일치** | 중상 |
| 10 | cnr_ota | README "AVDD 1.7/1.8/1.9 V", 신호표 "VSS Input Ground"; sim `VSS VSS 0 dc 0` | single 1.8 V | VDD_1V8/VSS; 1.8/0 (user 2026-10-14) | 없음 | CL1·CL2->VSS(load.spi `CL1 VOP 0`), IDC VSS->IBPSR | **일치** | 상 |
| 11 | erfc_ota | "power supply of 1.8 V" p.1, p.12; 입력 CM "800 mV" p.12 | single 1.8 V | vdd/gnd/**vcp/vcn**; 1.8/0/1.1/0.7 (user 2026-10-13 B-2) | 없음(vcp·vcn은 바이어스 전압) | CL->gnd, I05B_L/R->gnd, input_dc 0.8 | **일치** | 상 |
| 12 | r2r_opamp | Table I "Vsupply = 3.3 V, Rload = 10 kΩ, Cload = 10 pF" p.8, "3 V supply" p.1; 레일 VDD·VSS. 부하 다른 끝·측정 접지 미기재 | **불명**(총 전압 하나만 기재) | VDD/VSS; 1.8/0 (user 2026-10-14 D-9) | 없음 | CL·RL->VSS(원문 미기재, 근거 주석이 낡음) | **공동 분석 필요** | 중하 |
| 13 | rfc_ota | "Supply voltage: 1.8V" p.11; 레이아웃 절 "Common connection to GND" | single 1.8 V | vdd/gnd; 1.8/0 (user 2026-10-13) | 없음 | CL·RB->gnd, input_dc 1.02 | **일치** | 상 |

집계: 원문이 확실히 dual인 회로 1개(nmcnr), dual로 추정 1개(sf_pushpull), 불명 2개(pushpull_follower_buffer, r2r_opamp), single 9개(그중 추정 3개: folded_cascode, two_stage_ota, common_gate는 중상).
- **dual 원문인데 중간 레일 없이 옮긴 것**: 확인된 것은 0건이다. r2r_opamp는 원문 구성이 불명이라 후보로 둔다.
- **single 원문인데 중간 레일을 둔 것**: 확인된 것은 0건이다. pushpull_follower_buffer가 후보다. 원 도면 텍스트에는 VSS 라벨이 없고, 레일 구성은 p.26-6에서 빌려왔다(§2.6).
- **접지 쪽 항목이 잘못된 넷에 있는 것**: nmcnr의 입력 DC가 미선언이다(대응상 agnd). r2r의 RL·CL 끝은 원문 구성이 정해질 때까지 미정이다.
- **중간 레일 값·출처 기록 누락**: 세 agnd 회로 모두 `supplies_v.source.record`는 있다. 하지만 `origin`/`citation`이 없다. nmcnr 기록에는 원문 ±1 V 인용이 없고, pushpull·sf 기록에는 dual이라는 원문 근거가 없다.

## 2. 회로별 메모

원문 링크 표기: 로컬 PDF 경로 + 웹 링크 + 쪽.

### 2.1 common_gate_amplifier -- single, 일치 (확신도 중상)
- 원문: Allen Lecture 20, 로컬 `L/sources/common_gate_amplifier__allen_2014/source.pdf`, 웹 https://aicdesign.org/wp-content/uploads/2018/08/lecture20-140624.pdf .
  - p.2(Page 20-2) `VOUT(max) ≈ VDD – VDS3(sat)`, `VOUT(min) ≈ VDS1(sat) + VDS2(sat)`. 최소 출력이 0 V 기준 포화전압 합이다. 음 레일 = 접지 = 0이다.
  - p.7(Page 20-7, 같은 강의의 cascode) "Referencing all potentials to the negative power supply (ground in this case)".
  - 공급 값은 없다.
- 이식: `supply_nets` [vdd, gnd]. `supplies_v` {vdd 1.8, gnd 0}(user_decisions 2026-10-07 항목 1). 중간 레일은 없다.
- 접지 항목: M1.source = gnd(바이어스 전류원). 부하 소자는 없다. input_dc는 pending SP-2.
- 판정: 일치. single 원문에 중간 레일이 없다.

### 2.2 current_reuse_telescopic_ota -- single 1.8 V, 일치 (상)
- 원문: Xie & Chen 2019, 로컬 `L/sources/current_reuse_telescopic_ota__xie_chen_2019/source.pdf`. 웹 출처는 찾지 못했다(paper.md 머리 기록).
  - p.1(paper.md 39행) "126µW power consumption from a 1.8V power supply".
  - p.4(464행) "the supply voltage is 1.8V".
  - 도면 텍스트 157·227·310·325행에 `GND` 라벨이 있다.
- 이식: vdd/gnd, 1.8/0(user 2026-10-07).
- 접지 항목: CL1(Vop-gnd), CL2(Vom-gnd), Cs1(Vip-gnd), Cs2(Vim-gnd), Iref(Vbias1->gnd)가 있다. M40은 pmos이고 source=Voc_des, gate=drain=gnd다. 원문 347행은 "desired common-mode circuit Voc des is generated by two ..."다. 모두 접지(=gnd=VSS)로 대응한다.
- 참고: 같은 폴더의 보조 원문 Sanchez-Sinencio 2000 paper.md 1756행 "Vdd=-Vss= 1.35V"는 dual이다. 하지만 이 회로의 topology 원문은 Xie & Chen이라 공급 근거가 아니다.

### 2.3 folded_cascode -- single로 추정 (중하)
- 원문: Maloberti, Layout of Analog CMOS IC Part 2, 로컬 `L/sources/two_stage_ota+folded_cascode__maloberti_2004/source.pdf`. 웹은 제3자 재게시만 있다(slideshare.net/slideshow/layout02-1/58842369).
  - folded cascode 쪽(p.34~38) 텍스트에는 공급 값도 레일 라벨도 없다.
  - 같은 문서 p.30(852행)·p.33(938행)에는 `VDD`/`GND` 라벨이 있다. p.33 문구는 "Vdd and GND crossing the cell"이다.
- 이식: vdd/gnd, 1.8/0(user 2026-10-07). CL(out-gnd, user 2026-10-07 Q5).
- 판정: 문서 전체가 VDD/GND 표기이므로 single로 추정하고, 그 가정에서는 일치한다. folded 쪽 자체에는 텍스트 근거가 없다.

### 2.4 ngcc_3stage_ff -- single 1.2 V, 일치 (상)
- 원문: Lee 외, JSTS 7(1) 2007, 로컬 `L/sources/ngcc_3stage_ff__lee_2007/source.pdf`, 웹 https://doi.org/10.5573/JSTS.2007.7.1.020 .
  - p.5(1304행) "Power supply voltage was set to 1.2V".
  - p.5 Table 4(1313행) "ICMR≥VDD/3".
  - p.6(1910행) "1.2V supply voltage".
  - p.1(66행) "between power supply and ground".
- 이식: vdd/gnd, 1.8/0(user 2026-09-16 "2는 1.8에 맞춰"). CL(Vout-gnd).
- 판정: 일치.

### 2.5 nmcnr_amplifier -- dual ±1 V, 레일·부하 일치, 입력 DC 미대응 (상)
- 원문: Leung·Mok·Ki, ICECS 1999. 로컬 `L/sources/nmcnr_amplifier__leung_1999/source.pdf`. 공개 웹본은 없다(IEEE Xplore 유료, ICECS'99 vol.2 pp.599-602).
  - PDF p.4(저널 p.602, paper.md 238~239행) "Both amplifiers have a supply voltage of +/-1V and a load of 100pF in parallel with 25kΩ".
  - Table 1(366~368행) "Power supply +/- 1 V".
  - 주석 "unity-feedback configuration with 0.5V step input"이 있다.
- 이식: vdd/vss/agnd, {1.8, 0, 0.9}. 기록은 user 2026-10-12 Q8 "nmcnr은 1.8, 0으로 고치고 agnd로 0.9로 하는 pushpull 형태로 고쳐"이고, 그 전 기록은 2026-09-15 "+-0.9".
- 접지 항목:
  - CL(Vout-agnd), RL(Vout-agnd)는 원문 접지를 agnd로 옮겼다. **맞다.**
  - NMOS M104·M105·M203·M204·M301 source는 vss(원 -1 V 레일)다. **맞다.**
  - 보상망 Cm1·Cm2·Rm은 접지에 닿지 않는다.
- 불일치·누락:
  1. `input_dc` = pending SP-2. dual 원문의 입력 공통모드는 접지(0 V)이므로 대응 규칙상 **net agnd**가 되어야 한다. pushpull·sf는 이미 agnd로 선언돼 있다. 결정은 사용자 몫이다.
  2. `supplies_v.source`에 `origin`/`citation`이 없다. 원문 ±1 V 인용(p.602, Table 1)을 기록에 붙여 dual 근거를 남길 것을 권고한다. 값 0.9 = (1.8+0)/2는 원문 0 V 접지를 대응한 값이다.
- bias_inputs VB1~VB5의 기준 레일은 원문 텍스트에서 확인하지 못했다.

### 2.6 pushpull_follower_buffer -- 원문 구성 불명, 공동 분석 필요 (하)
- 원문: Allen Lecture 26, 로컬 `L/sources/pushpull_follower_buffer+sf_pushpull_output_opamp+two_stage_ota_sf__allen_2014/source.pdf`, 웹 https://aicdesign.org/wp-content/uploads/2018/08/lecture26-140625.pdf , Page 26-4(PDF p.4, paper.md 116~200행).
  - 공급 값이 없다.
  - 도면 텍스트에 `VDD`는 6번 나오고 `VSS`는 한 번도 없다. 같은 강의 p.6에는 `VSS` 라벨이 텍스트로 뽑힌다.
  - 부하 소자 텍스트가 없다. CL은 식 안의 `GL`로만 나온다.
  - 본문 165행 "Maximum positive and **negative** output voltages are limited"가 있다. 출력이 음이 될 수 있다는 서술이라 dual을 시사한다.
  - 텍스트끼리 상충한다. VSS 라벨이 없다는 점은 single(접지 = 음 레일)을 시사하고, 'negative output'은 dual을 시사한다.
- 이식: vdd/vss/agnd {1.8, 0, 0.9}(U-39 2026-09-21). CL(vout-agnd). input_dc = net agnd. M2.d·M3.d·M6.s = vss.
- 미확인 힌트(topology `_note`, 근거 아님): 원 도면에서는 gnd였던 것을 2026-09-15 사용자 결정("변경해")으로 p.26-6 표기에 맞춰 vss로 바꿨다. CL vout-agnd도 이때 p.26-6에서 가져왔다. **이 회로의 dual 구성은 자기 원문이 아니라 p.26-6(sf_pushpull)에서 빌린 것**이다.
- 판정: p.26-4 원문이 single이면 '단일 원문에 중간 레일 발명'이 된다. 그 경우 CL·input_dc는 VSS 쪽으로 가야 한다. dual이면 일치한다. 도면 이미지 확인과 사용자 회로 해석이 필요하다.

### 2.7 sf_pushpull_output_opamp -- dual로 추정, 일치 (중하)
- 원문: Allen Lecture 26 Page 26-6 Fig. 7.1-1(PDF p.6, paper.md 269~340행).
  - 도면 텍스트에 `VDD`와 `VSS` 라벨이 따로 있다(295·305·307행).
  - Cc·CL의 다른 끝 라벨은 텍스트에 없다. topology 주석은 '접지 기호'라고 적었는데, 이는 미확인 힌트다.
  - 공급 값은 없다. 같은 강의에서 숫자 공급은 Example 26-2 p.24 "VDD = 2.5V, VSS = 0V" 하나뿐이고, 다른 회로(class-A BJT 버퍼)라 이 회로의 근거가 아니다.
  - p.1이 교재 "Pages 354-370"을 가리킨다. 교재 본문(Allen & Holberg 7.1절)은 저장소에 없다.
- 이식: vdd/vss/agnd {1.8, 0, 0.9}(U-39). Cc(Y-agnd), CL(vout-agnd), input_dc = net agnd. NMOS source = vss. M18·M21 drain = vss.
- 판정: VSS와 접지가 서로 다른 기호라면 dual이고 일치한다. 텍스트로는 접지 기호의 존재를 확인할 수 없다. `supplies_v.source`에 dual 근거 인용이 없다.

### 2.8 two_stage_ota -- single로 추정, 일치 (중)
- 원문: Maloberti p.28~33(로컬·웹은 2.3과 같음). 공급 값은 없고 p.30·p.33에 VDD/GND 라벨만 있다.
- 이식: vdd/gnd 1.8/0. CL(OUT-gnd, 3 pF user 2026-10-07). M5·M7 source = gnd.
- 판정: 일치.

### 2.9 two_stage_ota_sf -- single, 일치 (중상)
- 원문: Allen Lecture 26 Page 26-5(PDF p.5).
  - "Power dissipation now becomes (I5 + I7 + I9)VDD"(paper.md 216행). 총 공급이 VDD 하나라는 뜻이므로 VSS = 0이다.
  - 도면 텍스트 레일 라벨은 VDD뿐이다.
- 이식: vdd/gnd 1.8/0(user 2026-10-07). CL(vout-gnd). M9.s = gnd.
- 판정: 일치.

### 2.10 cnr_ota -- single 1.8 V, 일치 (상)
- 원문: wulffern/cnr_ota_sky130nm @8c839f7, 로컬 `H/sources/cnr_ota__wulff_2024/`(README.upstream.md, sim/*.spi), 웹 https://github.com/wulffern/cnr_ota_sky130nm/blob/8c839f7/README.md .
  - README 53행 "VSS | Input | Ground", 71행 "AVDD 1.7/1.8/1.9 V".
  - sim/lstb.spi 26~27행 `VSS VSS 0 dc 0`, `VDD VDD_1V8 0 dc {AVDD}`.
  - sim/load.spi 10~11행 `CL1 VOP 0 5p`, `CL2 VON 0 5p`. 3행 `IDC 0 IBPSR dc 2u`.
- 이식: VDD_1V8/VSS 1.8/0(user 2026-10-14). CL1(VOP-VSS), CL2(VON-VSS), IDC(VSS->IBPSR). 노드 0 = VSS로 대응했다.
- 참고: 원 testbench에는 `VCM VCM 0 dc {AVDD/2}`가 있다(lstbcmfb.spi 29행, tran.spi 37행). 이것은 원문이 직접 둔 시험용 중간 전압원이고(balun·입력 CM 기준) 발명이 아니다. CNR_OTA.design.md 17행 "The input common mode cannot be VDD/2"는 U-75(입력 DC) 결정 때 참고할 것. 이식본은 귀환망을 제외했으므로(U3 (a)) 지금은 VCM이 필요 없다.
- 판정: 일치.

### 2.11 erfc_ota -- single 1.8 V, 일치 (상)
- 원문: Wu 외, Sensors 25(8):2523, 2025, 로컬 `H/sources/erfc_ota__wu_2025/source.pdf`, 웹 https://pmc-oa-opendata.s3.amazonaws.com/PMC12031453.1/PMC12031453.1.pdf (출판사 https://www.mdpi.com/1424-8220/25/8/2523 ).
  - p.1(66행) "operating at a power supply of 1.8 V".
  - p.12(754행) "supply voltage of 1.8 V". 760행 "common-mode input voltage of 800 mV".
  - 입력 CM 0.8 V는 공급 중간값 0.9 V가 아니다. single 기준이라는 방증이다.
- 이식: vdd/gnd/vcp/vcn {1.8, 0, 1.1, 0.7}(user 2026-10-13 B-2, citation p.8 Fig.6 표). CL(out-gnd). I05B_L/R(->gnd). input_dc 0.8.
- vcp·vcn은 원문 Fig.6 표의 바이어스 전압을 레일로 선언한 것이다. 접지 대응용 중간 레일(agnd 유형)이 아니다. 기록에 origin=paper와 citation이 있으므로 '발명된 중간 레일'에 해당하지 않는다.
- 판정: 일치.

### 2.12 r2r_opamp -- 원문 구성 불명, 공동 분석 필요 (중하)
- 원문: Hogervorst 외, IEEE JSSC 29(12) 1994, 로컬 `H/sources/r2r_opamp__hogervorst_1994/source.pdf`, 웹 https://repository.tudelft.nl/file/File_0fc107fa-6796-4bae-9159-8537a431f171 .
  - p.8(JSSC p.1512) Table I(856~857행) "Vsupply = 3.3 V, Rload = 10 kΩ, Cload = 10 pF".
  - p.1(102행) "0.5 mW at a 3 V supply voltage".
  - 본문은 동작을 VSS·VDD 기준으로 적는다(221행 "between VSS + 1.3 V and VDD - 1.3 V").
  - 공급은 총 전압 한 값만 적혀 있다. ±1.65 V 분할 측정인지, RL·CL 다른 끝이 어디인지(VSS인지 중간인지)는 텍스트에 없다.
- 이식: VDD/VSS 1.8/0(user 2026-10-14 D-9). CL(Vo-VSS), RL(Vo-VSS)(user 2026-10-14 C-1 (가)).
- 주의: topology `RL._comment`의 근거 "엔진이 이상 전압원을 받지 않아 중간 전압 끝을 만들 수 없다"는 **낡았다**. 지금은 supply_nets 중간 레일(agnd 유형)로 중간 전압 끝을 만들 수 있다(nmcnr·pushpull·sf 선례). 주석도 "원 측정보다 DC 부하가 가혹할 수 있다"고 스스로 적고 있다.
- 판정: 원문이 single 측정(부하 -> VSS)이면 일치한다. 분할 공급(부하 -> 0 V = 중간)이면 dual 원문을 중간 레일 없이 옮긴 경우가 되고, RL·CL은 agnd로 가야 한다. 원문 텍스트만으로는 정할 수 없어 사용자 판단이 필요하다. 다음 결정인 input_dc U-75도 이 판단에 묶인다.

### 2.13 rfc_ota -- single 1.8 V, 일치 (상)
- 원문: Matibag, UPC 석사논문 2024, 로컬 `H/sources/rfc_ota__matibag_2024/source.pdf`, 웹 https://upcommons.upc.edu/bitstreams/a99028f7-5d7f-447a-b086-c1f4effcdb1b/download .
  - p.11(784행) "Supply voltage: 1.8V".
  - p.10 본문(700행) "bias voltage without the need of extra sources other than VDD".
  - 레이아웃 절(2871~2872행) "Common connection to GND".
  - p.37 Fig.11 testbench 텍스트에는 레일 라벨이 없다(이미지만 있음).
- 이식: vdd/gnd 1.8/0(user 2026-10-13). CL(out-gnd), RB(b_rb-gnd). input_dc 1.02 V는 ICMR 중앙값에서 유도했다(HA-1). 공급 중간값이 아니다.
- 판정: 일치.

## 3. 사용자 공동 분석이 필요한 항목

1. **pushpull_follower_buffer 원문 구성(§2.6).** Page 26-4 도면의 음 레일이 접지 기호(single)인지 별도 VSS(dual)인지 확인해야 한다. 텍스트 근거가 상충한다. VSS 라벨이 없다는 점은 single, "negative output voltages"는 dual을 가리킨다. single이면 agnd·CL(vout-agnd)·input_dc=agnd가 '발명된 중간 레일'이 되므로 고쳐야 한다(2026-09-15 p.26-6 표기 차용 결정 재검토). 도면 이미지 판독이 필요한데, 이 감사는 이미지를 읽지 않았다.
2. **sf_pushpull_output_opamp dual 근거(§2.7).** Fig. 7.1-1의 Cc·CL 끝이 VSS와 다른 접지 기호인지 확인해야 한다. 공급 값은 강의 텍스트에 없고, 교재 7.1절(pp.354-370)은 저장소에 없다. 확인되면 `supplies_v.source`에 origin/citation(dual 근거)을 붙인다.
3. **r2r_opamp 측정 공급 구성(§2.12).** Table I "Vsupply = 3.3 V"가 단일 공급(부하 -> VSS)인지 ±1.65 V 분할(부하 -> 0 V)인지 정해야 한다. 분할이면 agnd 레일을 추가하고 RL·CL을 agnd로 옮겨야 한다. RL 주석의 '중간 끝을 만들 수 없다'는 근거는 지금 사실이 아니다. U-75(input_dc)가 이 판단에 묶인다.
4. **nmcnr_amplifier input_dc(§2.5).** 원문이 dual ±1 V이므로 대응 규칙상 입력 공통모드 = agnd다. SP-2 결정에 이 대응을 기본안으로 올릴지 정해야 한다(사용자 spec 결정 사항). 함께 `supplies_v.source`에 원문 ±1 V 인용(p.602·Table 1)을 넣을지도 정한다.
5. **folded_cascode·two_stage_ota(Maloberti) 공급 값.** 원문에 값이 없다. VDD/GND 라벨로 single이라고 추정했다. 반대 근거는 없다. 확인만 하면 된다.

## 4. 이 감사에서 하지 않은 것

- 회로도 이미지를 판독하지 않았다(지시대로 텍스트만 봄). §3의 1~3은 이미지 확인이 있어야 닫힌다.
- 바이어스 입력(bias_inputs)의 원문 기준 레일 대응은 r2r(Vb1~Vb6, VDD/VSS 기준, topology `_ideal_voltage_sources_unloaded` 기록)을 빼고는 확인하지 않았다. 원문 텍스트에 기준이 나오지 않는다.
- 저장소는 바꾸지 않았다. `git -C` 읽기만 했다(HEAD `c237d96e`).
