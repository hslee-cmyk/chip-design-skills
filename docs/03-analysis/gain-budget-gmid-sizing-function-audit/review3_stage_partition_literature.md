# stage 분할 기준: 문헌 조사와 계획서 v5.5 대조

조사일: 2026-09-15. 대상: `docs/01-plan/features/gain-budget-gmid-sizing.plan.md` v5.5의 N3.2(SP1), 용어집 L84-90, DEC-04/57/58, J10, N3.8, 원자료 probe 3건.
표기: [확인] = 원문 텍스트를 직접 추출해 읽음(PDF는 PyMuPDF로 추출해 scratchpad `review3/*.txt`에 보관). [요약만] = 검색 결과 요약이나 초록만 읽음. **확인 못 함** = 원문에 접근하지 못함.

---

## 1. 교과서·강의자료의 gain stage 정의

| 출처 | 확인 수준 | (a) 캐스코드 | (b) CG 증폭기 | (c) follower/출력 버퍼 | (e) 경계 기준 |
|---|---|---|---|---|---|
| Razavi, UCLA EE215A 강의노트 HO#2 "One-Stage Op Amps"(2014 가을) http://www.seas.ucla.edu/brweb/teaching/215A_F2014/opamps.pdf | [확인] | telescopic cascode(p.2-3), folded cascode(p.4-5)를 **"One-Stage Op Amps"** 절에 둔다. p.8: 헤드룸이 부족하고 gm·ro가 낮아 one-stage op amp로는 gain이 낮으니 two-stage를 가장 많이 쓴다 | - | - | 5T OTA와 telescopic 단일출력의 **mirror pole**을 단점으로 적음(p.2-3). folded cascode는 "Poles at X & Y"(접는 노드)를 telescopic과 비교(p.5). 즉 캐스코드 내부 노드는 같은 stage 안의 비지배 극점으로 다룬다 |
| Razavi, 같은 강의 HO "Single-Stage Amplifiers" http://www.seas.ucla.edu/brweb/teaching/215A_F2014/SingAmps.pdf | [확인] | "Cascode Stage"(p.8), "Folded Cascode"를 single-stage amplifier 장에 둠 | **"CS and CG stages, source followers, and cascades"**(p.1): 소자 구성 수준에서는 CG도 하나의 "stage" | source follower도 single-stage 장에 들어가지만 buffer로 평가("How good a buffer is a source follower?"), 잡음을 더하고 헤드룸을 먹어 가끔만 쓴다(p.6) | - |
| Razavi 교과서 *Design of Analog CMOS ICs* 3장 "Single-Stage Amplifiers"(3.4 Source Follower, 3.5 Common-Gate Stage, 3.6 Cascode Stage) | [요약만] 목차 수준(UBC·LIP6 강의자료 검색 결과) | 소자 구성 수준 용어로 "stage" | 같음 | 같음 | 본문 확인 못 함 |
| NTU(臺大) "Design of Analog ICs" 9장 Op Amps 슬라이드 http://cc.ee.ntu.edu.tw/~ecl/Courses/107AIC/lock/Analog_Chapter_06_OP_Amps.pdf (Razavi 9장 구성) | [확인] | "9.2 One-Stage Op Amps" 아래 telescopic·folded cascode(p.5-13), "9.3 Two-Stage Op Amps"·"Two-Stage Op Amps with cascode devices"(p.14-15) | - | - | p.16의 "Folded-cascode inserts one more stage"는 gain boosting 보조증폭기 문맥이라 stage 수 규칙으로 쓰지 않음 |
| Iowa State EE435 Lecture 8 "High-Gain Single-Stage Op Amps"(2023) http://class.ece.iastate.edu/ee435/lectures/EE%20435%20Lect%208%20Spring%202023.pdf | [확인] 제목·목차 | telescopic cascode, regulated(gain-boosted) cascode를 "Single-Stage High Gain Op Amps"로 분류 | - | - | - |
| ADI University Program Wiki, "Chapter 10: Multi stage amplifier configurations" §10.3 https://wiki.analog.com/university/courses/electronics/text/chapter-10 | [요약만] WebFetch | **cascode를 "two-stage amplifier"(transconductance amp + current follower)라 부른다** → 용어 반례. 이것은 소자 구성 단위의 stage이지 op amp gain stage 수가 아님 | - | follower는 단 사이 레벨 시프트 요소로 설명 | - |
| Silva-Martinez / Palermo, TAMU ECEN474 Lecture 19 "Output Stages" https://people.engr.tamu.edu/spalermo/ecen474/lecture19_ee474_output_stages.pdf | [확인] | - | - | p.4 **"Three-Stage OpAmp" = 차동 입력단(Av>1) + 2nd gain stage(Av>>1, Miller 보상에 씀) + output stage(전류 이득 크고 전압 이득 ≈1, 출력 임피던스 작음)**. p.5 "Buffered OTA = OPAMP", "2nd Stage & Buffer". 이후 source follower(class A), push-pull(class B), class AB 출력단 | 이득 기준이 아니라 **기능(입력/이득/출력)**으로 stage를 셈 |
| P. E. Allen, Georgia Tech ECE6412 Lecture 300 "Buffered Op Amps"(2002) https://pallen.ece.gatech.edu/Academic/ECE_6412/Spring_2003/L300-BufferedOpAmps-2UP.pdf | [확인] | - | - | "buffered op amp = 출력저항이 낮은 op amp". p.300-7 "Compensation of a three-stage amplifier": 출력단(Output stage)이 **세 번째 극점 p3'**을 만들고, Miller를 2단만 감쌀지 2·3단을 함께 감쌀지 선택. **"Crossover-Inverter, Buffer Stage Op Amp"**: 버퍼를 출력저항이 높고 전압이득이 있는 **CS**로 만들되 작은 RL로 부하하면 그 단 gain ≈1 | 극점·보상 관점에서는 버퍼도 stage 수에 들어감 |
| Leung & Mok, "Analysis of multistage amplifier-frequency compensation", IEEE TCAS-I 48(9), 2001, Sec. II https://nthuee.org/archive/AIC/106%E8%AC%9D%E5%BF%97%E6%88%90/HW/Final%20project/reference/reference/01CAS-leung.pdf | [확인] 표기 절 | - | - | 출력단도 transconductance g_mL을 가진 한 단으로 모델링 | **i번째 gain stage = (g_mi, 출력저항 r_oi, 출력 노드의 lumped 기생용량 C_pi)**. 즉 stage마다 출력 노드 하나에 극점 하나를 둠(pole-splitting 해석의 전제). 가정 목록 세부는 추출본에서 수식이 깨져 확인 못 함 |
| Johns & Martin / Carusone *Analog IC Design* 2판(5장 two-stage, 6장 folded cascode) | **확인 못 함**(본문 접근 실패). 목차 요약에서 3장 "cascode gain stages", 6장 "folded-cascode opamp"만 확인 | | | | |
| Gray-Hurst-Lewis-Meyer *Analysis and Design of Analog ICs* | **확인 못 함**. "Output Stages" 장이 op amp 장과 따로 있다는 것만 목차 요약으로 확인 | | | | |
| Allen & Holberg *CMOS Analog Circuit Design*(교과서) | **확인 못 함**(위 Allen 강의노트 L300으로 대체) | | | | |
| Sansen *Analog Design Essentials* | **확인 못 함** | | | | |
| Jespers & Murmann *Systematic Design of Analog CMOS Circuits*(2017) | **확인 못 함**(목차 PDF 접속 실패). Murmann IEEE Toronto SSCS 강연(2016) https://www.ieeetoronto.ca/wp-content/uploads/2020/06/20160226toronto_sscs.pdf [확인]: 예제를 "Noise-limited gain stages"(CS voltage amp, charge amp, basic OTA, **folded-cascode OTA**)와 "Distortion-limited gain stages"로 묶음(p.30-31) → folded-cascode OTA 전체를 **하나의 gain stage 예제**로 취급. 단 분할 규칙이나 캐스코드 gm/ID 결정 방식에 대한 명시 규칙은 확인 못 함 | | | | |
| (d) class-AB 출력단·floating current source | TAMU L19와 Allen L300에 class AB 출력단 절은 있음. floating battery를 어느 stage 출력노드로 볼지 규칙은 **확인 못 함** | | | | |

요지
- **op amp gain stage 수**(Razavi 강의노트, NTU, Iowa, Murmann 강연): 캐스코드(telescopic/folded, gain-boosted 포함)는 **한 stage**다.
- **소자 구성 수준**(Razavi single-stage 장, ADI wiki): CS·CG·SF·cascode를 각각 "stage"라 부르고, ADI는 cascode를 "two-stage"라 부른다. 용어가 두 뜻으로 쓰인다.
- **follower/출력단**: 이득 배분에서는 이득 ≈1인 단으로 표시하지만(TAMU), **극점·보상에서는 stage 수에 넣는다**(TAMU "three-stage", Allen p3', Leung-Mok g_mL).

## 2. 자동화 도구·연구의 구조 인식 기준

| 도구/연구 | 확인 수준 | stage/블록 정의 | CS/CG/CD 처리 | 전압/전류 구동 구분 |
|---|---|---|---|---|
| Massier, Graeb 외, "The Sizing Rules Method for CMOS and Bipolar Analog IC Synthesis", IEEE TCAD 2008 https://dl.acm.org/doi/10.1109/TCAD.2008.2006143 | [요약만] 초록 | 트랜지스터 쌍 그룹(차동쌍, 전류미러, level shifter, cascode pair …)의 계층 라이브러리와 자동 인식. gain stage 개념은 초록에 없음 | 확인 못 함 | 확인 못 함 |
| M. Eick, *Structure and Signal Path Analysis for Analog and Digital Circuits*, TUM 박사논문 2013(심사 Graeb) https://d-nb.info/1036974812/34 | [확인] 2.1, 3장, 4.1 | 블록 인식 뒤 **ESFG**(Enhanced Structural Signal Flow Graph, Def. 4.2): 넷이 노드, 블록마다 라이브러리에 저장한 전형적 신호흐름이 엣지(Table 4.1: nta g/d/s, scm i→o, dp i1,i2→o1,o2, ls …, §4.1.2). 신호 경로·아날로그/디지털/바이어스 분할과 대칭 계산에 사용 | 라이브러리 수준 블록(level shifter, cascode pair, folded cascode pair). **gain stage 번호 매기기는 없음** | 없음(엣지는 블록 종류·핀 속성) |
| Abel, Neuner, Graeb, "A Functional Block Decomposition Method for Automatic Op-Amp Design", arXiv 2012.09051 / Integration 2022 https://arxiv.org/abs/2012.09051 | [확인] 5-6절, 식 (20)-(36), Alg. 2-3, 10절 | **amplification stage = transconductance + load + stage bias**(HL3/HL4). **transconductance는 게이트에 걸린 전압을 (증폭된) 전류로 바꾸고**(5.1), **load는 전류를 전압으로 바꾼다**(5.2). 비반전 stage(1단·CMFB stage)는 차동쌍 transconductance, 반전 stage(n≥2)는 source가 레일에 붙은 트랜지스터 스택이며 **맨 아래 게이트가 다른 transconductance나 load 출력에 붙는다**(식 23, 34). CMFB stage도 amplification stage로 인식. 3단 op amp도 인식(Fig. 18) | **캐스코드 = load part 안의 gate-connected couple이고 source가 transconductance 출력에 붙는다**(5.2, 식 30) → 같은 stage. 전압 구동 source를 받는 CG 증폭기 stage, follower, 출력 버퍼, class-AB 출력단 정의는 **본문에서 찾지 못함**(향후 과제로는 다단 보상 회로만 언급, 10절) | **사실상 있음**: 게이트에 전압을 받는 소자가 stage를 시작하고(transconductance), 전류를 받아 전압을 만드는 쪽(load, 캐스코드 포함)은 같은 stage |
| Abel, Graeb, "A Hierarchical Performance Equation Library for Basic Op-Amp Design"(HPEL), arXiv 2012.09088 / IEEE TCAD 2021 https://arxiv.org/pdf/2012.09088 | [확인] HL3 식 (19)-(23) | stage transconductance = **stage 입력 신호에 게이트가 붙은 트랜지스터의 gm**(식 19. 반전 stage는 앞 stage 출력에 게이트가 붙은 소자). 상보 차동쌍은 gm 합(식 20). stage 출력저항·open-loop gain·비지배 극점과 영점은 HL4에서 계산 | 2-스택 출력 컨덕턴스 g_out = g_d·g_d/g_m(식 21), 캐스코드/folded-cascode 차동쌍 load는 입력쌍 g_d까지 포함(식 22) → **캐스코드는 같은 stage의 출력 컨덕턴스에 흡수** | 암묵적(게이트 입력 기준) |
| Abel, Graeb, "FUBOCO: Structure Synthesis of Basic Op-Amps by FUnctional BlOck COmposition", ACM TODAES 2022, arXiv 2101.07517 | [확인] 2절, 8절 | 위와 같은 계층(HL3 load/transconductance/stage bias, HL4 amplification stage). 1단(telescopic·folded cascode·symmetrical·complementary)과 2단 합성. 3단은 **Outlook(8절)**이고 위상여유 모델이 없어 향후 과제 | 캐스코드 load part를 1단의 일부로 합성 | 위와 같음 |
| Neuner, Abel, Graeb, "Library-free Structure Recognition for Analog Circuits", DATE 2021 https://past.date-conference.com/proceedings-archive/2021/pdf/1540.pdf | [확인] 초록 수준 | 소자 쌍을 연결 특성으로 묶어 블록 인식 규칙을 자동 생성. stage 규칙은 따로 없음 | - | - |
| Kunal 외(Sapatnekar 그룹), "GNN-based Hierarchical Annotation for Analog Circuits"(GANA), IEEE TCAD 2023 http://people.ece.umn.edu/~sachin/jnl/tcad23kk.pdf / ALIGN arXiv 2008.10682 | [확인] 1·4절 | 계층 = element → primitive(21종 ALIGN 라이브러리, 서브그래프 동형) → sub-block(GNN 분류) → block. Fig. 1: telescopic OTA를 "STAGE 1" sub-block(CM-P, DP-P, 캐스코드 전류미러 CM-N)으로 표시 | **CS-Amp-N**이 primitive로 존재(바이어스 회로 안). 목적이 레이아웃 제약(대칭)이라 **gain stage 번호·신호흐름 기반 stage 경계는 없음** | 없음 |
| Shi, "Automatic Stage-form Circuit Reduction for Multistage Opamp Design Equation Generation", ACM TODAES 25(1), 2019 https://dl.acm.org/doi/abs/10.1145/3363499 | [요약만] 초록 | 다단 op amp를 기호적으로 stage-form macromodel로 축약하고 보상 소자를 추출. **stage 정의 방법은 확인 못 함** | 확인 못 함 | 확인 못 함 |
| "Sizing of multi-stage Op Amps by combining design equations with the gm/ID method", 2021 https://www.researchgate.net/publication/350523435 | [요약만] 검색 요약 | stage별 초기 사이징, 자동 회로 인식으로 gain stage와 신호 경로를 뽑는다는 요약. 저자·인식 기준은 **확인 못 함**(ScienceDirect 403) | | |

## 3. stage 단위 gain 배분 방법론

- Leung-Mok 2001(Sec. II): 단별 (g_m, r_o, C_p) 매크로모델로 DC gain = Π g_mi·r_oi, 극점은 단 출력노드마다. **stage 경계 = 고임피던스 출력노드**라는 전제. [확인: 표기 절]
- HPEL(식 19-23): stage gain을 입력 소자 gm과 load·transconductance·stage bias 출력 컨덕턴스 합으로 조립. 캐스코드는 컨덕턴스 식 안에 들어간다. [확인]
- Murmann 강연: 잡음 또는 왜곡이 정하는 "gain stage" 단위로 gm/ID를 고른다. [확인: 목차 슬라이드]
- 단별 gain을 할당하는 별도 "gain budgeting" 절차 문헌(stage를 어떻게 정의하는지 포함)은 **확인 못 함**.

---

## 4. 우리 규칙별 판정

| # | 우리 규칙(계획서 위치) | 판정 | 근거 |
|---|---|---|---|
| R1 | 전류 구동 CG(캐스코드) = 같은 stage (N3.2-5 둘째 항목, DEC-57) | **일치** | Razavi HO#2·NTU·Iowa: telescopic/folded cascode = one-stage. Abel-Graeb FBD 5.2: 캐스코드는 load part. HPEL 식 21-22: 캐스코드는 같은 stage 출력 컨덕턴스. 용어 반례는 ADI wiki("cascode = two-stage amplifier")뿐이고, 이는 소자 구성 수준 용어다 |
| R2 | source가 전압 구동인 CG = 새 gain stage (N3.2-5 첫째 항목) | **부분 일치 / 도구 문헌 없음** | Razavi는 CG를 소자 구성 수준 "stage"로 다룬다(SingAmps p.1, 7). FBD·HPEL·GANA 라이브러리에는 CG 입력 gain stage 정의가 없다. 4개 회로에도 사례가 없다(probe_cg_cascode_stage: CG 8개 모두 전류 구동) → 규칙은 문헌과 모순되지 않지만 검증되지 않았다 |
| R3 | CD·pass = 버퍼 구간, gain stage 번호를 올리지 않음 (N3.2-5 셋째 항목) | **부분 일치** | 이득 기준으로는 일치(TAMU: output stage Av≈1). 그러나 TAMU "Three-Stage OpAmp", Allen L300 "three-stage amplifier"(출력단이 p3'를 만든다), Leung-Mok(g_mL)은 모두 **출력 버퍼를 stage 수에 넣는다**. 우리 안의 "번호를 올리지 않음"은 gain 배분 번호로는 맞지만, 극점·보상 stage 수와 다른 번호 체계가 된다 |
| R4 | stage 경계 = 셀 입력 노드 구동 종류(전압/전류) (N3.2-5, 용어집 L84) | **부분 일치(개념 동등, 형식 다름)** | FBD: "게이트에 전압 → 전류(transconductance)", "전류 → 전압(load)", 반전 stage 게이트는 앞 transconductance/load 출력에 붙음(식 23). HPEL 식 19도 같다. 교과서 보상 관점(Leung-Mok)은 **고임피던스 출력노드**를 경계로 본다. 고전 op amp에서는 결과가 같지만, 우리 규칙은 임피던스 등급을 경계 판정에 쓰지 않고 기록만 한다(N3.2-6) |
| R5 | DM 뷰 + gate→drain 비용 1, source→drain·gate→source 비용 0, 0-1 BFS (N3.2-3·4) | **문헌 없음** | Eick ESFG는 블록 라이브러리 기반 신호흐름 그래프이고 대칭 계산을 하지만 stage 번호용 가중치나 BFS는 없다. 4개 회로 실측 일치(probe_stage_partition R3)가 유일한 근거 |
| R6 | diode 노드 게이트의 gate→drain 비용 0(미러는 같은 stage) (N3.2-4) | **일치(극점 주의)** | FBD: 전류미러 load는 stage의 load. Razavi HO#2 p.2-3: 단일출력 미러 극점을 단점으로 적음 → 같은 stage로 묶되 **미러 노드 극점은 따로 남겨야** 한다 |
| R7 | 이득 블록 / 버퍼 블록 구분 (DEC-58, 용어집 L89) | **부분 일치** | TAMU의 Av>1 / Av>>1 / Av=1 구분, Allen의 "buffered op amp"와 맞다. 반례: Allen L300 "Crossover-Inverter, Buffer Stage"는 **CS로 만든 버퍼**(부하가 걸리면 gain ≈1)이므로, 셀 종류(CS)만으로 이득 블록이라 정하면 틀린다 |
| R8 | follower 독립 블록 여부 미정 (J10) | **문헌 경향 = 독립 stage** | TAMU·Allen·Leung-Mok 모두 출력단을 별도 단으로 두고 극점·보상 계산에 넣는다. FBD·HPEL은 follower를 다루지 않는다(문헌 없음) |
| R9 | 입력·캐스코드 gm_id·L 독립 결정변수 (DEC-04) | **부분 일치** | HPEL은 입력 gm(식 19)과 캐스코드 g_m·g_d(식 21-22)를 서로 다른 소자 변수로 둔다(성능식 수준). gm/ID 설계서가 둘을 함께 정하라고 규정하는지는 확인 못 함(Jespers-Murmann 본문 미접근) |

## 5. 우리 안이 놓친 기준·반례

1. **전류 입력 포트를 받는 CG(transimpedance/current-mode 입력단)**: CG 입력단 TIA와 current-mode 광 전치증폭기는 입력이 전류다(검색 요약: Springer AICSP "On the design of low-noise current-mode optical preamplifiers", ResearchGate "common gate TIA input stage with common source active feedback"). N3.2-5는 입력 포트를 전압 구동으로 가정한다(용어집 L84 "입력 포트"). 그래서 이 CG는 "전류 구동 CG = 캐스코드 = 같은 stage"로 떨어지고, **앞 stage가 없는데 캐스코드로 분류되는** 모순이 생긴다.
2. **CS로 만든 버퍼**(Allen L300 crossover-inverter buffer), **diode 부하 CS**(Razavi SingAmps의 diode-connected load, gain ≈ gm1/gm2): 셀이 CS라 이득 블록이 되지만 실제 gain은 ≈1 이하다. 이득 할당 대상으로 들어가면 DP의 gain bin이 낭비된다.
3. **게이트가 전류 구동 노드에 붙은 CS**: gain-boosting 보조증폭기(Razavi HO#2 p.6-7, 캐스코드 source 노드가 보조 CS 게이트를 구동), regulated cascode, flipped voltage follower 계열. N3.2-5는 "전압 구동 입력을 받는 CS"만 정의하므로 이 셀은 **분류가 정의되지 않는다**. gain boosting이 범위 밖이더라도 `review_needed`로 떨어진다는 문장이 없다. FVF는 문헌을 확인하지 않은 추론이다.
4. **캐스코드 내부 노드 극점**: folded cascode 접는 노드 X·Y(Razavi HO#2 p.5), 5T/telescopic 단일출력 미러 극점(p.2-3). 같은 stage로 묶는 것은 맞지만 블록 속성(N3.8 L428)에 비지배 극점 후보 노드가 없다.
5. **symmetrical OTA의 두 second stage**(FBD 식 36, ainvv: stage bias가 voltage bias이고 다른 second stage와 gate-gate로 연결): 한쪽 second stage가 다른 쪽의 미러 부하 역할을 한다. DM 뷰 대응과 diode 비용 0 규칙이 이 구조에서 어떻게 동작하는지는 4개 회로에 사례가 없다.
6. **CMFB stage**: FBD는 CMFB를 non-inverting amplification stage로 인식한다. SP1은 모드 선언이 없으면 DM 뷰만 만든다(N3.2-2). CMFB 루프 gain·PM을 stage 단위로 배분하려면 CM 뷰 분할이 필요하지만 기본 경로가 없다.
7. **stage 번호 두 뜻**: gain 배분 번호(버퍼 제외)와 극점·보상 번호(버퍼 포함, Allen·TAMU·Leung-Mok)가 다르다. N3.2-5 근거 문단은 `compensation.stage_devices`와의 정합을 이유로 드는데, nmcnr처럼 3단 보상에서 출력 버퍼가 끼면 두 번호가 어긋난다.
8. **gain-boosted cascode**: Iowa EE435 L8은 single-stage로 분류한다. 범위 밖이라도 R1과 같은 결론(같은 stage)이라는 것은 문헌과 일치한다.

## 6. 개선 제안(계획서 절·문장 수준)

- **P1 (N3.2-5, 용어집 L84)**: "입력 포트의 구동 종류는 `ports` 선언의 `drive: voltage|current`에서 읽는다(기본 voltage). 전류 구동 입력 포트를 source로 받는 CG는 캐스코드가 아니라 **transimpedance gain stage의 시작**이다(번호 +1)."를 추가한다.
- **P2 (N3.2-5 셋째 항목, J10, DEC-58)**: stage 번호를 두 필드로 나눈다. `gain_stage_index`(SP1 결과, 버퍼는 올리지 않음)와 `pole_stage_index`(버퍼 블록도 +1, 출력노드마다 극점 하나 -- Leung-Mok Sec. II, Allen L300 p.300-7). `compensation.stage_devices` 대조는 `pole_stage_index`로 한다. J10의 기본안은 "follower·pass 구간은 **독립 버퍼 블록**(gain 할당 대상 아님, 극점·출력 임피던스·최대 출력 전류를 가짐)"으로 두고, 앞 stage 흡수는 공동분석으로 예외만 둔다.
- **P3 (N3.8 블록 속성 L428)**: 블록 국소 모델로 계산한 |gain|이 1 이하이거나 출력노드 임피던스 등급이 '낮음'인 CS 시작 블록은 `review_needed`("이득 블록인가 버퍼인가")로 올린다. 반례 근거는 Allen crossover-inverter buffer와 diode 부하 CS다. 임계 1은 이득/버퍼 정의 자체에서 나오는 값이라 새 상수가 아니다.
- **P4 (N3.2-9 "graph로 정하지 않는 것")**: "게이트가 전류 구동 노드에 붙은 CS(gain boosting 보조증폭기, regulated cascode, flipped voltage follower 등 국소 궤환 셀)는 SP1 셀 분류 밖이며 `review_needed`로 보고한다"를 추가해, 분류가 정의되지 않은 채 조용히 지나가는 경로를 막는다.
- **P5 (N3.2-6 stage 구성)**: 블록 노드 집합 중 출력노드가 아닌 내부 노드(캐스코드 source 노드, folded 접는 노드, 미러 diode 노드)를 `internal_pole_nodes`로 기록하고, 블록 속성에 저주파 극점 추정을 넣어 GB5 보상 규칙이 쓰게 한다(Razavi HO#2 p.2-5).
- **P6 (N3.2-5 근거 문단)**: 외부 정합 근거를 한 줄 넣는다. "캐스코드를 같은 stage에 두는 것은 Abel-Graeb functional block 분해(transconductance/load/stage bias, 캐스코드는 load part)와 HPEL 출력 컨덕턴스 식(21)-(22)와 같다." 용어 대응(input↔transconductance, cascode+load↔load, tail↔stage bias)도 용어집에 둔다.
- **P7 (N3.2-8 검증 기준, U-22)**: 4개 회로에 없는 경우를 일반성 측정 대상으로 명시한다. (a) 출력 source follower가 있는 3단 op amp (b) symmetrical OTA(second stage 2개) (c) CG 입력 TIA(전류 포트) (d) CS 버퍼. 각 회로에서 SP1이 무동작이거나 `review_needed`를 내는지 측정한다.
- **P8 (N3.2-2 여기 모드)**: CMFB 루프 metric(CM gain·CM PM)이 선언되면 CM 뷰에서도 SP1을 돌린다는 조건을 명시한다(FBD의 CMFB amplification stage 인식이 근거).

## 7. 확인 못 한 항목
Johns & Martin/Carusone, Gray-Hurst-Lewis-Meyer, Allen-Holberg 교과서 본문, Sansen, Jespers-Murmann 본문, Shi(2019) stage 정의, "multi-stage gm/ID sizing"(2021) 저자와 인식 기준, Massier-Graeb 2008 본문, class-AB floating current source의 stage 출력노드 규칙.
