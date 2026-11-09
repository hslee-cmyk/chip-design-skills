# O-73 선행 작업 -- 13회로 외부 응용 망 소자 목록 (DUT / 외부 분류, 공동분석 초안)

- 작성 2026-10-21, 분석 agent(읽기 전용, 저장소 무변경). base master `c237d96e`.
- 근거 결정: `_drafts/user_decisions.md` O-73(694행). 1단계 표현 = spec `element_values.<원소>.measurement_load: true`
  (`gmid_engine/authoring/spec_elements.py:9·37·70`) -- **면적(`area_search_m2`)·layout에서만 빠지고 모든 해석에는 남는다.**
- 13회로 = `evidence/2026-10-21/de1_output_structure_13.md`와 같다(library 9 + heldout 4).
- **근거로 쓴 것**: topology `passive_elements`·`ideal_sources`·`netlist` 연결(net마다 닿는 단자 전수 -- 스크립트 출력), sizing_spec `element_values`·`feedback`·출처 기록, `*.spec_source.md`, 원문(`assets/{library,heldout}/sources/` md). **안 쓴 것**: device_roles·symmetry·sizing_roles·compensation 태그, topology `_comment`(인용할 때는 '미검증 힌트'로 표시), 회로도 이미지.
- 스크립트·원자료: `C:/Users/HSLEE/AppData/Local/Temp/claude/C--Users-HSLEE-Documents-Todoc-fpga-chip-design-skills/63c6146a-ab1d-4035-a169-bae810986922/scratchpad/extnet/`(`dump2.py`, `ev.py`, `nets.py`).

## 0. 결론 요약

| 항목 | 값 |
|---|---|
| 수동소자 총수(13회로) | 54개 (C 34, R 20) -- 이 중 이미 `measurement_load` 16개(CL 14 + RL 2) |
| 이상 전류원(비 MOS 원천) | 13개 (`implementable: false`) -- 수동소자가 아니어서 면적 축 밖, `measurement_load` 표지 불가(spec_elements.py:70 거부) |
| **O-73으로 새로 외부 표시할 소자** | **4개: current_reuse_telescopic_ota `Cf1`·`Cf2`(되먹임 망), `Cs1`·`Cs2`(샘플링/입력 망)** -- 사용자 진술로 확정 |
| 이미 외부(`measurement_load`)로 맞게 표시된 것 | 모든 부하 CL(12회로, 14개)·RL(nmcnr·r2r 2개) -- 변경 없음 |
| DUT로 남는 수동소자 | 보상(Cc·Rz·Cm·Rm·CM·CBAT·C1/C2), CMFB 감지 저항(R1/R2, x37/x38, erfc R1/R2), 바이어스·기준 저항(x3/x39/x40/x9, RB, R1a~c) |
| 면적 축 변화 | current_reuse만: 고정 항 **-2 pF = -1.0e-9 m² (-1000 µm²)**, 나머지 12회로 0 |
| 공동분석 질문 | Q1 rfc CL 2.75 pF 안의 '안정용 추가 500 fF', Q2 이상 전류원 13개의 위치(DUT 바이어스 대역 vs 시험 원천), Q3 r2r RL 다른 끝(VSS), Q4 sf Cc(Y–agnd) 성격, Q5 cnr 바이어스 분압 저항 |

## 1. 분류 기준 (O-73 원문을 그대로 적용)

- **외부 응용 망** = 증폭기를 쓰는 쪽이 붙이는 소자: 부하 C·부하 R, 되먹임 망(출력→입력), 샘플링/입력 망, 시험 원천.
  사용자 진술(O-73): "Cf1/Cf2는 회로 외부에서 구성되는 feedback loop", "Cs1·Cs2 … 외부망이야. 회로의 load이지. load resistor들도 마찬가지".
- **DUT** = 증폭기 설계 자체가 정하는 소자: 보상 C·영점 저항, CMFB 감지 소자, 바이어스·기준 저항, 결합(battery) C.
- 판정 순서: (a) 연결 -- 소자 양 끝이 '포트(입력·출력) ↔ 레일/AC 접지/다른 포트'만 잇는가(외부 후보), 아니면 내부 node에 닿는가(DUT). (b) 원문이 그 소자를 측정 조건·응용 회로(시험대)로 적었는가, 설계 변수(표·식)로 적었는가.
- 결과 소비(O-73 1단계): 외부 표시 → `passive_area_decl`이 `excluded`로 빼고(`gmid_engine/search/area_decl.py:46-47`), layout도 만들지 않는다(`gmid_engine/layout/passives.py:20`, `contract_input.py:169`). `measurement_load`의 다른 소비자는 없다(grep: authoring·search·layout·pipeline만) -- **DC·AC·과도 해석에는 그대로 남는다**(O-73 요구와 일치).

## 2. 회로별 표

열: 이름 / kind / 연결(nets) / 현재 spec 상태(값·`measurement_load`·`feedback.elements`) / **분류** / 근거 / 확신도 / O-73 1단계 표시 결과.
면적 기여 = 지금 `area_search_m2`에 들어가는가(`measurement_load` 아님 + kind C/R, PDK 선언 있음).

### 2.1 common_gate_amplifier (MOS 3, 수동소자 0)

수동소자·이상원 없음. spec `element_values = {}`, `feedback.elements = []`. 부하 CL은 SP-6(c) 대기(spec `_element_values_comment`). **변경 대상 없음.** (CL이 들어오면 `measurement_load`로 넣는다 -- 규칙상 외부.)

### 2.2 current_reuse_telescopic_ota (MOS 51)

원문: Xie & Chen 2019, 로컬 `C:/Users/HSLEE/Documents/Todoc/fpga/chip-design-skills/skills/analog-gmid-design/assets/library/sources/current_reuse_telescopic_ota__xie_chen_2019/source.pdf`(paper.md), 웹 링크 찾지 못함(sources/README). Table I p.1(paper.md 76~77행 "Values for C1, C2, and CL: 500fF, 500fF, 1pF"), Eq.(3)(4) p.4(paper.md 403~418행 "β = Cf/(Cf+Cs+Cgg1)", "Cf = Cs = 500fF", "By setting Cc to 500fF"), CMFB 절 p.3(paper.md 337~347행 "R1 and R2 are used to averaging the differential signal (Vop and Vom) to common mode voltage (Voc)").

| 소자 | kind | 연결 | 현재 spec | 분류 | 근거 | 확신 | O-73 결과 |
|---|---|---|---|---|---|---|---|
| R1 | R | Vom–Voc | engine, 면적 기여 | **DUT**(CMFB 감지) | Voc는 R1·R2·M37a.g만(net 전수) → CMFB 증폭기 입력; 원문 p.3 CMFB 절 | 높음 | 변경 없음 |
| R2 | R | Voc–Vop | engine, 면적 기여 | **DUT**(CMFB 감지) | 같음 | 높음 | 변경 없음 |
| Cc1, Cc2 | C | Vom–N_cc_rz1 / Vop–N_cc_rz2 | engine, 면적 기여 | **DUT**(보상) | 내부 node 경유 Rz로 2단 gate(Vop1/Vom1)에 닿음; 원문 Eq.(3) "Cc is the value of the compensation capacitance" | 높음 | 변경 없음 |
| Rz1, Rz2 | R | N_cc_rz1–Vop1 / N_cc_rz2–Vom1 | engine(nulling, M16/M26 기준), 면적 기여 | **DUT**(영점 저항) | 내부 node만 잇는다 | 높음 | 변경 없음 |
| CL1, CL2 | C | Vop–gnd / Vom–gnd | 1 pF, **measurement_load** | 외부(부하 C) | Table I CL 1 pF; 출력 포트–레일 | 높음 | 이미 표시 |
| **Cf1** | C | Vom–Vip | 0.5 pF, `feedback.elements`, **면적 기여** | **외부(되먹임 망)** | 출력 포트↔입력 포트만 잇는다; Eq.(4) β의 Cf, Table I C1; **사용자 O-73 진술** | 높음(사용자 확정) | **새로 표시 → 면적·layout 제외, β·AC·과도 해석 유지** |
| **Cf2** | C | Vop–Vim | 0.5 pF, feedback, 면적 기여 | **외부(되먹임 망)** | 같음 | 높음 | **새로 표시** |
| **Cs1** | C | Vip–gnd | 0.5 pF, feedback 아님, 면적 기여 | **외부(샘플링/입력 망)** | 입력 포트–레일만; Eq.(4) β의 Cs, Table I C2; 사용자 O-73 진술 | 높음 | **새로 표시** |
| **Cs2** | C | Vim–gnd | 0.5 pF, 면적 기여 | **외부(샘플링/입력 망)** | 같음 | 높음 | **새로 표시** |
| Iref | 이상 I | Vbias1–gnd | 1.2 µA(spec), implementable false | 바이어스 기준 대역(Q2) | Vbias1 = M18_bg 다이오드 + 6개 gate(net 전수) → 바이어스 기준 전류 주입 | 중간 | 표시 불가(원천), 면적 0 |

O-73 표시 영향(이 회로): 면적 고정 항 4 x 0.5 pF = 2 pF → **-1.0e-9 m²**(MIM 밀도 camimc 2.00e-15 F/µm², `assets/sky130_pdk_decl.json` `mim_cap_density_f_per_m2`). 값이 고정이라 탐색 점 사이 순위·front 비지배 관계는 변하지 않고 보고 면적·GB4 면적 하한·layout 소자 수만 바뀐다. `feedback.elements = [Cf1, Cf2]`는 그대로 둔다(β 정의 유지 -- `measurement_load`와 `feedback`을 함께 막는 검사는 spec_elements.py에 없음, grep 0건). 주의: topology `_comment`(미검증 힌트)는 Cs가 개루프 AC에서 기여 0이라고 적는다 -- 해석 결과는 이번 표시와 무관.

### 2.3 folded_cascode (MOS 13)

원문 Maloberti 2004 p.34~38(로컬 `.../assets/library/sources/two_stage_ota+folded_cascode__maloberti_2004/source.pdf`, 웹 저자 게시처 찾지 못함). 원문 텍스트에 CL 값 없음 -- CL은 사용자 결정(TQ Q5, U-31).

| 소자 | kind | 연결 | 현재 spec | 분류 | 근거 | 확신 | O-73 결과 |
|---|---|---|---|---|---|---|---|
| CL | C | out–gnd | 1 pF, measurement_load | 외부(부하 C) | 출력 포트–레일; 사용자 "CL 1pF를 넣어줘" | 높음 | 이미 표시 |
| Ibg | 이상 I | vb1–vb2 | pending CI-17 | 바이어스 기준 대역(Q2) | vb1 = MP 다이오드+M3/M4 gate, vb2 = MN 다이오드+M11 gate | 중간 | 표시 불가, 면적 0 |

### 2.4 ngcc_3stage_ff (MOS 16)

원문 Lee 외 2007, 로컬 `.../assets/library/sources/ngcc_3stage_ff__lee_2007/source.pdf`, 웹 https://doi.org/10.5573/JSTS.2007.7.1.020 . Table 5 "CL=10pF"(paper.md 1312·1659행), 부하 조건 10 pF/100 pF(44행).

| 소자 | kind | 연결 | 현재 spec | 분류 | 근거 | 확신 | O-73 결과 |
|---|---|---|---|---|---|---|---|
| Cm1 | C | V1–Vout | engine, 면적 기여 | **DUT**(Miller 보상) | V1 = 1단 출력(M2.d·M4.d)·M8/M14 gate → 내부 node–출력 | 높음 | 변경 없음 |
| Cm2 | C | V2–Vout | engine, 면적 기여 | **DUT**(Miller 보상) | V2 = 2단 출력(M10.d·M11.d)·M13.g | 높음 | 변경 없음 |
| CL | C | Vout–gnd | 10 pF, measurement_load | 외부(부하 C) | Table 5 측정 조건 | 높음 | 이미 표시 |

### 2.5 nmcnr_amplifier (MOS 15)

원문 Leung·Mok·Ki 1999, 로컬 `.../assets/library/sources/nmcnr_amplifier__leung_1999/source.pdf`, 웹 IEEE Xplore 유료·링크 찾지 못함. p.2(paper.md 86~90행) "C_m1 and C_m2 are the compensation capacitors, and C_L is the loading capacitor"; p.2~3(141~151행) "A null resistor connected in series with the compensation capacitor"; p.4(239행) "a load of 100pF in parallel with 25kΩ", Table 1(361행) "loading condition 100pF//25kΩ".

| 소자 | kind | 연결 | 현재 spec | 분류 | 근거 | 확신 | O-73 결과 |
|---|---|---|---|---|---|---|---|
| Cm1 | C | NodeM2–NodeCM | engine, 면적 기여 | **DUT**(nested Miller 보상) | NodeM2 = 1단 출력(M107/M109.d, M201.g) | 높음 | 변경 없음 |
| Cm2 | C | NodeS2–NodeCM | engine, 면적 기여 | **DUT**(보상) | NodeS2 = 2단 출력(M202/M204.d, M301.g) | 높음 | 변경 없음 |
| **Rm** | R | NodeCM–Vout | engine, 면적 기여 | **DUT**(null 저항) | NodeCM은 Cm1·Cm2·Rm만 닿는 내부 node(net 전수) → Rm은 보상 C와 출력 사이 직렬; 원문 141~151행 null resistor = 보상 망. 출력 포트에 닿지만 다른 끝이 레일·입력이 아니라 보상 내부 node라 부하가 아니다 | 높음 | 변경 없음(공동분석 확인 항목, 의견 = DUT) |
| CL | C | Vout–agnd | 100 pF, measurement_load | 외부(부하 C) | 원문 측정 조건 | 높음 | 이미 표시 |
| RL | R | Vout–agnd | 25 kΩ, measurement_load | 외부(부하 R) | 원문 측정 조건 "100pF//25kΩ"; agnd는 supply_nets 선언 레일(CL·RL만 닿음) | 높음 | 이미 표시. O-66 유지: 출력 DC를 정함 → DC 해석에 남는다 |

### 2.6 pushpull_follower_buffer (MOS 6)

원문 Allen 2014 Lecture 26, 로컬 `.../assets/library/sources/pushpull_follower_buffer+sf_pushpull_output_opamp+two_stage_ota_sf__allen_2014/source.pdf`, 웹 https://aicdesign.org/wp-content/uploads/2018/08/lecture26-140625.pdf . p.6 "GB = 60MHz for CL = 1pF"(paper.md 283행).

| 소자 | kind | 연결 | 현재 spec | 분류 | 근거 | 확신 | O-73 결과 |
|---|---|---|---|---|---|---|---|
| CL | C | vout–agnd | 1 pF, measurement_load | 외부(부하 C) | 출력 포트–레일; 도면 CL=1pF | 높음 | 이미 표시 |

입력 DC(`input_dc` = net agnd)는 소자가 아니라 시험 원천 선언 -- 표시 대상 아님.

### 2.7 sf_pushpull_output_opamp (MOS 22)

원문 Allen 2014 p.6 Fig. 7.1-1(paper.md 269~323행: Cc 288행, R1 296~302행, IBias 310행, CL 323행).

| 소자 | kind | 연결 | 현재 spec | 분류 | 근거 | 확신 | O-73 결과 |
|---|---|---|---|---|---|---|---|
| R1a | R | N5–N1 | engine, 면적 기여 | **DUT**(바이어스/레벨시프트) | N5·N1 모두 MOS drain·gate 내부 node(M5.d, M1.d, M6/M9/M17/M5/M10 gate) | 높음 | 변경 없음 |
| R1b | R | N7–N2 | engine, 면적 기여 | **DUT** | 같은 구조(M7.d, M2.d …) | 높음 | 변경 없음 |
| R1c | R | N12–N13 | engine, 면적 기여 | **DUT** | M12.d–M13.d 사이 내부 node | 높음 | 변경 없음 |
| Cc | C | Y–agnd | engine, 면적 기여 | **DUT**(보상 -- Q4) | Y = 내부 이득단 node(M10.d·M15.d, M18/M19 gate); 원문 그림에 Cc로 그려짐; 출력 포트에 닿지 않음 | 중간~높음 | 변경 없음 |
| CL | C | vout–agnd | 1 pF, measurement_load | 외부(부하 C) | 도면 CL=1pF | 높음 | 이미 표시 |
| IBias | 이상 I | vdd–NB | 50 µA | 바이어스 기준 대역(Q2) | NB = M4 다이오드 + M3.g | 중간 | 표시 불가, 면적 0 |

### 2.8 two_stage_ota (MOS 7)

원문 Maloberti 2004 p.28~33(로컬 위 2.3과 같은 PDF). CL 3 pF = 사용자 결정(TQ Q4', U-31).

| 소자 | kind | 연결 | 현재 spec | 분류 | 근거 | 확신 | O-73 결과 |
|---|---|---|---|---|---|---|---|
| Rz | R | O1–N_cc_rz | engine, 면적 기여 | **DUT**(영점 저항) | O1 = 1단 출력(M2/M4.d, M6.g); 사용자 "cc와 Rz가 직렬로 O1-OUT사이" | 높음 | 변경 없음 |
| Cc | C | N_cc_rz–OUT | engine, 면적 기여 | **DUT**(Miller 보상) | 같음 | 높음 | 변경 없음 |
| CL | C | OUT–gnd | 3 pF, measurement_load | 외부(부하 C) | 사용자 "3pF으로 확정" | 높음 | 이미 표시 |

### 2.9 two_stage_ota_sf (MOS 9)

원문 Allen 2014 p.5(paper.md 204~256행, Cc 255행·CL 256행).

| 소자 | kind | 연결 | 현재 spec | 분류 | 근거 | 확신 | O-73 결과 |
|---|---|---|---|---|---|---|---|
| Cc | C | O1–OUT | engine, 면적 기여 | **DUT**(Miller 보상) | O1 = 1단 출력, OUT = 2단 출력(M6/M7.d, M8.g) -- 둘 다 내부 node(출력 포트는 vout) | 높음 | 변경 없음 |
| CL | C | vout–gnd | 3 pF, measurement_load | 외부(부하 C) | U-25 two_stage 정본 CL 3 pF | 높음 | 이미 표시 |

### 2.10 cnr_ota (heldout, MOS 72)

원문 = 논문 없음, 공개 xschem 저장소: 웹 https://github.com/wulffern/cnr_ota_sky130nm (@8c839f7), 로컬 `C:/Users/HSLEE/Documents/Todoc/fpga/chip-design-skills/skills/analog-gmid-design/assets/heldout/sources/cnr_ota__wulff_2024/source.md`·`CNR_OTA.design.md`. 설계 노트(CNR_OTA.design.md 39~41행): "The resistors senses the common mode, and the capacitors form a feedforward zero to cancel the pole of the resistor and input capacitance of the VCM OTA". 시험 부하 파일 `sim/CNR_OTA/load.spi`: "`IDC 0 IBPSR dc 2u`, CL1/CL2 5p, R1~R4"(source.md 20행) -- R1~R4 저항 귀환망은 U3 (a)로 topology에서 이미 제외(cnr_ota.spec_source.md 18·78행).

| 소자 | kind | 연결 | 현재 spec | 분류 | 근거 | 확신 | O-73 결과 |
|---|---|---|---|---|---|---|---|
| x37 | R | VCOP–LPCO | 70.13 kΩ, 면적 기여 | **DUT**(CMFB 감지) | LPCO = C1·C2·x37·x38 + x42.g만(net 전수) → CM 감지 node가 VCM OTA 입력; 설계 노트 39행 | 높음 | 변경 없음 |
| x38 | R | LPCO–VCON | 70.13 kΩ, 면적 기여 | **DUT**(CMFB 감지) | 같음 | 높음 | 변경 없음 |
| C1 | C | LPCO–VCOP | 53.8 fF, 면적 기여 | **DUT**(CMFB 앞먹임 영점) | x37과 병렬; 설계 노트 "capacitors form a feedforward zero" | 높음 | 변경 없음 |
| C2 | C | VCON–LPCO | 53.8 fF, 면적 기여 | **DUT** | 같음 | 높음 | 변경 없음 |
| x3 | R | VSS–net7 | 17.53 kΩ, 면적 기여 | **DUT**(CM 기준 분압 -- Q5) | net7은 x3·x39만; VDD_1V8–x40–VCR–x39–net7–x3–VSS 분압, VCR → x31.g | 중간~높음 | 변경 없음 |
| x39 | R | net7–VCR | 70.13 kΩ, 면적 기여 | **DUT**(분압) | 같음 | 중간~높음 | 변경 없음 |
| x40 | R | VCR–VDD_1V8 | 70.13 kΩ, 면적 기여 | **DUT**(분압) | 같음 | 중간~높음 | 변경 없음 |
| x9 | R | VCREF–VSS | 70.13 kΩ, 면적 기여 | **DUT**(기준 전압 저항) | VCREF = x31.s·x36 drain(IBPSR 미러 전류)·x43.g → 미러 전류 x 저항으로 기준 전압 생성 | 중간~높음 | 변경 없음 |
| CL1 | C | VOP–VSS | 5 pF, measurement_load | 외부(부하 C) | load.spi `CL1 VOP 0 5p` | 높음 | 이미 표시 |
| CL2 | C | VON–VSS | 5 pF, measurement_load | 외부(부하 C) | load.spi `CL2 VON 0 5p` | 높음 | 이미 표시 |
| IDC | 이상 I | VSS–IBPSR | 2 µA | **외부(시험 원천)** -- 원문이 시험 부하 파일(load.spi)에 둠 | load.spi 3행 `IDC 0 IBPSR dc 2u`; IBPSR = x24 다이오드 + 미러 gate 전수 | 높음 | 표시 불가(원천 kind), 면적 0 -- 2단계 응용 topology에서 다룰 항목 |

참고(O-73 밖): cnr 저항은 원 설계가 res_high_po(시트 수 kΩ/□)인데 PDK 선언 `resistor_types` 후보가 poly_generic(rp1 = 48.2 Ω/□) 하나뿐이라 면적 축이 크게 과대평가된다(§3 표). O-73 표시와 무관한 백로그 후보.

### 2.11 erfc_ota (heldout, MOS 29)

원문 Wu 외, Sensors 25(8):2523, 2025. 웹 https://pmc-oa-opendata.s3.amazonaws.com/PMC12031453.1/PMC12031453.1.pdf · https://www.mdpi.com/1424-8220/25/8/2523 , 로컬 `C:/Users/HSLEE/Documents/Todoc/fpga/chip-design-skills/skills/analog-gmid-design/assets/heldout/sources/erfc_ota__wu_2025/source.pdf`. p.6(paper.md 291·295행) "no current flows through the resistors R1,2 = RA, and VX = VY = VZ" / "half of the current … flows through the resistors R1,2"; p.9 Table 1(457~458행) "R1,2 52 kΩ"(치수표 = 설계 변수); p.4(184행) "coupling capacitors CBAT1 and CBAT2, along with the bias resistor RL"; p.6(338~348행) RL·CBAT 직렬 망; p.13 CL 70 pF.

| 소자 | kind | 연결 | 현재 spec | 분류 | 근거 | 확신 | O-73 결과 |
|---|---|---|---|---|---|---|---|
| R1 | R | X–Z | 52 kΩ, 면적 기여 | **DUT**(LCMFB 감지 저항) | Z = R1·R2 + M19/M20/M3A/M4A gate만 → 내부 CM 감지; X·Y = 내부 folding node; Table 1 치수표 | 높음 | 변경 없음 |
| R2 | R | Z–Y | 52 kΩ, 면적 기여 | **DUT** | 같음 | 높음 | 변경 없음 |
| CBAT1_L | C | n_m5g–X | engine, 면적 기여 | **DUT**(결합 C) | n_m5g = M5.g·M19.d; 원문 184행 coupling capacitor | 높음 | 변경 없음 |
| CBAT1_R | C | n_m6g–Y | engine, 면적 기여 | **DUT** | 대칭 | 높음 | 변경 없음 |
| CBAT2 | C | n_m7d–n_m8g | engine, 면적 기여 | **DUT** | 내부 node 둘 | 높음 | 변경 없음 |
| CL | C | out–gnd | 70 pF, measurement_load | 외부(부하 C) | p.13·Table 2 CL 70 pF | 높음 | 이미 표시 |
| IC_L, IC_R | 이상 I | vdd–n_m13g / vdd–n_m14g | 0.2 µA | 바이어스 기준 대역(Q2) | Fig.6 표 IC = 0.2 µA | 중간 | 표시 불가, 면적 0 |
| I05B_L, I05B_R | 이상 I | n_m11d–gnd / n_m12d–gnd | 1 µA | 바이어스 기준 대역(Q2) | Fig.6 표 0.5·IB | 중간 | 표시 불가, 면적 0 |

참고(미검증 힌트 아님, 원문 사실): 원문의 'bias resistor RL'(CBAT과 직렬)은 topology에 수동소자로 없다. DE-1 표가 적은 `mos_zero_current_structural`(M19·M20·M21)이 그 RL을 MOS로 구현한 자리로 보이나 이 문서 범위 밖 -- 연결 해석은 하지 않았다.

### 2.12 r2r_opamp (heldout, MOS 31)

원문 Hogervorst 외, IEEE JSSC 29(12) 1994. 웹 https://repository.tudelft.nl/file/File_0fc107fa-6796-4bae-9159-8537a431f171 , 로컬 `C:/Users/HSLEE/Documents/Todoc/fpga/chip-design-skills/skills/analog-gmid-design/assets/heldout/sources/r2r_opamp__hogervorst_1994/source.pdf`. Table I(paper.md 856~859행) "Vsupply = 3.3 V, Rload = 10 kΩ, Cload = 10 pF"; 본문 41·674행 "load of 10 pF"; Fig.13 CM1·CM2 2p(spec 출처 기록 PDF p.6).

| 소자 | kind | 연결 | 현재 spec | 분류 | 근거 | 확신 | O-73 결과 |
|---|---|---|---|---|---|---|---|
| CM1 | C | n_gp–Vo | 2 pF, 면적 기여 | **DUT**(Miller 보상) | n_gp = 출력단 gate(M25.g) 내부 node; Fig.13 | 높음 | 변경 없음 |
| CM2 | C | n_gn–Vo | 2 pF, 면적 기여 | **DUT** | n_gn = M26.g | 높음 | 변경 없음 |
| CL | C | Vo–VSS | 10 pF, measurement_load | 외부(부하 C) | Table I Cload | 높음 | 이미 표시 |
| RL | R | Vo–VSS | 10 kΩ, measurement_load | 외부(부하 R) | Table I Rload; **다른 끝 VSS는 원문 미기재**(spec 기록 C-1 (가)) -- Q3 | 높음(분류)/중간(연결) | 이미 표시. O-66 유지(출력 DC를 정함) |
| Ib1, Ib2, Ib4, Ib5, Ib6 | 이상 I | VDD–tail_p, VDD–n_abn, tail_n–VSS, n_abp–VSS, n_t29–VSS | 4/7/4/7/2 µA | 바이어스 기준 대역(Q2) | Fig.13 이상 전류원 기호(spec C-2) | 중간 | 표시 불가, 면적 0 |

### 2.13 rfc_ota (heldout, MOS 35)

원문 Matibag, UPC 석사논문 2024. 웹 https://upcommons.upc.edu/bitstreams/a99028f7-5d7f-447a-b086-c1f4effcdb1b/download , 로컬 `C:/Users/HSLEE/Documents/Todoc/fpga/chip-design-skills/skills/analog-gmid-design/assets/heldout/sources/rfc_ota__matibag_2024/source.pdf`. p.33(paper.md 1785~1790행) "the transconductance of Q3 in the biasing circuit is fixed by the resistor … The initial value for the resistor was 353Ω"; p.34 Fig.9 RB = 1412 Ω; p.35(1884~1890행) "**500fF were added for a total of 2.75pF, to make the Recycling structure stable**"; p.11 요구 부하 2.25 pF(spec 출처 기록).

| 소자 | kind | 연결 | 현재 spec | 분류 | 근거 | 확신 | O-73 결과 |
|---|---|---|---|---|---|---|---|
| RB | R | b_rb–gnd | 1412 Ω, 면적 기여 | **DUT**(constant-gm 바이어스 저항) | b_rb = Q2.s·RB만; 원문 p.33 "gm of Q3 … fixed by the resistor" | 높음 | 변경 없음 |
| CL | C | out–gnd | 2.75 pF, measurement_load | **외부(부하 C) -- 단 Q1** | 원문: 요구 부하 2.25 pF + 안정용 0.5 pF | 중간 | 이미 표시. Q1 결론에 따라 0.5 pF를 DUT로 나눌지 결정 |

## 3. 면적 축(`area_search_m2`) 기여 소자와 O-73 표시 효과

`passive_area_decl`(`gmid_engine/search/area_decl.py:38-55`): `element_class == passive`이고 `measurement_load`가 아니면 C는 1/camimc, R은 W_min²/R□ + 머리 면적으로 들어간다. 이상 전류원(`ELEMENT_SOURCE`, `gmid_engine/graph/s1_values.py:24`)은 들어가지 않는다.
환산(추정 표시): C 1 pF = 500 µm²(camimc 2.00e-15 F/µm²). R = 0.33² / 48.2 ≈ 2.26e-3 µm²/Ω + 머리 ≈ 0.22 µm²/개 -- poly.3 = 0.33 µm, licon.1 = 0.17 µm, licon.8a = 0.08 µm는 sky130 periphery 규칙 기억값으로 **이번에 PDK 파일에서 읽어 확인하지 않음**(추정).

| 회로 | 지금 면적 기여 소자(고정값) | 지금 면적 기여 소자(engine 변수) | 고정 항 추정 | O-73 표시로 빠지는 것 | Δ면적 |
|---|---|---|---|---|---|
| common_gate_amplifier | -- | -- | 0 | -- | 0 |
| current_reuse_telescopic_ota | **Cf1, Cf2, Cs1, Cs2** (0.5 pF x 4) | R1, R2, Cc1, Cc2, Rz1, Rz2 | 1000 µm² | **Cf1, Cf2, Cs1, Cs2** | **-1000 µm² = -1.0e-9 m²** |
| folded_cascode | -- | -- | 0 | -- | 0 |
| ngcc_3stage_ff | -- | Cm1, Cm2 | 0 | -- | 0 |
| nmcnr_amplifier | -- | Cm1, Cm2, Rm | 0 | -- (CL·RL 이미 제외) | 0 |
| pushpull_follower_buffer | -- | -- | 0 | -- | 0 |
| sf_pushpull_output_opamp | -- | R1a, R1b, R1c, Cc | 0 | -- | 0 |
| two_stage_ota | -- | Rz, Cc | 0 | -- | 0 |
| two_stage_ota_sf | -- | Cc | 0 | -- | 0 |
| cnr_ota | C1, C2 (53.8 fF x 2), x3·x37·x38·x39·x40·x9 (합 368.2 kΩ) | -- | C 53.8 µm² + R ≈ 833 µm²(추정, poly_generic 기준) | -- | 0 |
| erfc_ota | R1, R2 (52 kΩ x 2) | CBAT1_L, CBAT1_R, CBAT2 | R ≈ 236 µm²(추정) | -- | 0 |
| r2r_opamp | CM1, CM2 (2 pF x 2) | -- | 2000 µm² | -- (CL·RL 이미 제외) | 0 |
| rfc_ota | RB 1412 Ω | -- | ≈ 3.4 µm²(추정) | -- (Q1이 'DUT 0.5 pF 분리'로 결정되면 **+250 µm²**) | 0 (Q1 대기) |

결과: O-73 1단계 표시로 바뀌는 면적은 **current_reuse 한 회로, 고정 상수 -1.0e-9 m²**뿐이다. 값이 고정이라 탐색 순위·비지배 관계는 변하지 않고, 보고 면적·GB4 면적 하한·layout 산출물(Cf/Cs 4개 미생성)만 바뀐다.

## 4. 공동분석 질문 (의견·근거·확신도)

- **Q1 rfc_ota CL 2.75 pF의 '안정용 500 fF'** -- 원문 p.35가 "500fF were added for a total of 2.75pF, to make the Recycling structure stable"라고 적는다. 요구 부하는 2.25 pF(p.11). 의견: 2.25 pF = 외부 부하, 0.5 pF = 설계자가 안정을 위해 넣은 **출력 보상 C(DUT)**다. 지금처럼 2.75 pF 전체를 `measurement_load`로 두면 DUT 면적에서 0.5 pF(250 µm²)가 빠진다. 선택지: (가) 현 상태 유지(원문 testbench 값 그대로 측정 부하), (나) CL 2.25 pF(measurement_load) + 새 수동소자 out–gnd 0.5 pF(DUT, 값 원문) -- topology 연결 추가라 사용자 몫. 확신도: 분류 의견 중간(원문이 '부하에 더했다'고만 적어 설계 일부인지 시험 조건 조정인지 문장만으로는 갈림).
- **Q2 이상 전류원 13개의 위치** -- current_reuse Iref, folded Ibg, sf IBias, cnr IDC, erfc IC/I05B, r2r Ib1~6. 모두 `implementable: false`이고 면적 축 밖이며 `measurement_load` 표지를 받을 수 없다(spec_elements.py:70). 의견: cnr IDC는 원문이 시험 부하 파일(load.spi)에 두므로 **외부 시험 원천**(높음). 나머지는 원문 회로도 안의 바이어스 기준 전류(실제 칩에서는 DUT 바이어스 발생기)를 대신하는 이상 원천이라 'DUT 바이어스 대역'(중간). O-73 1단계에서는 할 일이 없다(면적 0, 해석 유지). 2단계 응용 topology card에서 IDC만 응용 회로로 옮길지 정하면 된다.
- **Q3 r2r RL의 다른 끝** -- 원문 Table I는 Rload = 10 kΩ만 적고 연결 끝은 적지 않는다. 지금 VSS(spec C-1 (가)). 3.3 V 단전원 rail-to-rail 측정이면 중간 전압(VDD/2)에 다는 것이 흔하지만 근거 문장이 없다. O-66(RL이 출력 DC를 정함)에 직접 영향 → 외부 표시와 별개로 연결 확인 필요. 확신도: 분류(외부) 높음, 끝 연결 낮음.
- **Q4 sf_pushpull Cc(Y–agnd)** -- 출력 포트에 닿지 않고 내부 이득 node Y와 AC 접지 사이 → 부하가 아니라 내부 pole을 정하는 보상 C. 의견 DUT, 확신도 중간~높음(원문 그림 이미지 판독 없이 연결과 원문 라벨 'Cc'로만 판단).
- **Q5 cnr 분압 저항 x3/x39/x40과 x9** -- 레일(VDD_1V8, VSS)에 닿지만 신호 포트에 닿지 않고 내부 기준 node(VCR, VCREF)를 만든다 → 바이어스·CM 기준 망(DUT). 원문 설계 노트는 CMFB 저항(x37/x38)만 설명하고 이 넷은 설명하지 않는다. 확신도 중간~높음. 원 시험대의 R1~R4(귀환망)는 이미 topology에서 빠져 있어 해당 없음.
- **(확인만) nmcnr Rm** -- 출력 포트에 닿지만 다른 끝 NodeCM이 Cm1·Cm2만 닿는 보상 내부 node라 부하가 아니다. 원문 null resistor. 의견 DUT, 확신도 높음.

## 5. graph 단일 정본 규칙 점검 (CLAUDE.md ★graph 단일 정본)

- 제안하는 표시는 기존 spec 필드 `measurement_load` 하나를 쓰고, 소비자는 기존 writer `passive_area_decl` 하나다(새 필드·cache·사본 없음).
- `feedback.elements`와 `measurement_load`는 정의 축이 다르다(β 루프 소속 대 면적·layout 소속) -- 같은 소자가 둘 다 가져도 같은 양의 두 번째 생산자가 아니다.
- Q1 (나)를 고르면 새 수동소자가 생기지만 topology connectivity 추가(사용자 몫)이지 계산값 복제가 아니다.
