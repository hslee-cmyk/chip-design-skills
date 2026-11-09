# gm/ID 방법론 원본의 LUT 정의 판독 (2026-11-06)

역할: 원문 판독자. 판단은 원문 사실만 적고 권고는 하지 않는다. 원문을 직접 읽은 것만 사실로 적었다. 기억이나 외부 지식은 **[외부 지식]**으로 표지했고 근거로 쓰지 않는다.

## 0. 원본과 읽은 방법

| 약칭 | 로컬 경로 | 쪽 대응 |
|---|---|---|
| JM17-App2 | `chip-design-skills/skills/analog-gmid-design/references/gmid_sources/jespers_murmann_2017/extracted/lookup-table-generation-and-usage.pdf` | 책 쪽 = PDF 쪽 + 302 (책 303~314) |
| JM17-App3 | `.../extracted/layout-dependence.pdf` | 책 = PDF + 314 (책 315~321) |
| JM17-1 | `.../extracted/1 introduction.pdf` | 책 = PDF |
| JM17-2 | `.../extracted/2 basic-transistor-modeling.pdf` | 책 = PDF + 20 |
| JM17-3 | `.../extracted/3 basic-sizing-using-the-gmid-methodology.pdf` | 책 = PDF + 61 |
| JM17-4 | `.../extracted/4 noise-distortion-and-mismatch.pdf` | 책 = PDF + 113 |
| JM17-5 | `.../extracted/5 practical-circuit-examples-i.pdf` | 책 = PDF + 164 |
| JM17-6 | `.../extracted/6 practical-circuit-examples-ii.pdf` | 책 = PDF + 225 |
| JM17-sym | `.../extracted/symbols and acnonyms.pdf`, `index.pdf` | 책 xi~xiv |
| J10 | `chip-design-skills/skills/analog-gmid-design/references/gmid_sources/jespers_2010/gmid_methodology_jespers_2010.pdf` | 오프셋이 일정하지 않음. PDF 쪽마다 머리글로 직접 확인함(아래 표의 쪽은 모두 확인값) |

- 경로의 앞부분은 `C:/Users/HSLEE/Documents/Todoc/fpga/`이다.
- 텍스트는 `pdftotext -layout`으로 뽑았다. 출력은 `C:/Users/HSLEE/AppData/Local/Temp/la1s_book33/*.txt`에 있다.
- 핵심 쪽은 Read 도구로 PDF 쪽 그림을 열어 대조했다: JM17-App2 PDF 3~4(책 305~306, 대응 행렬), J10 PDF 113~114(책 101~102, 접합 용량 식).
- 책 쪽 번호는 각 PDF 쪽의 머리글로 확인했다.

---

## 1. LUT 생성: 무엇을 저장하고 어떻게 얻는가

### 1.1 저장하는 양 (JM17)
- 책 304쪽(PDF 2)에 Matlab 구조체 목록이 있다: `ID, VT, IGD, IGS, GM, GMB, GDS, CGG, CGS, CSG, CGD, CDG, CGB, CDD, CSS, STH, SFL`. 머리 정보는 `INFO: '65nm CMOS, PSP'`, `CORNER: 'NOM'`, `TEMP: 300`, `NFING: 5`, `W: 10`, 그리고 `L, VGS, VDS, VSB` 벡터다.
- 책 305쪽(PDF 3): `c.outvars = {'ID','VT','IGD','IGS','GM','GMB','GDS','CGG','CGS','CSG','CGD','CDG','CGB','CDD','CSS','STH','SFL'};`
- 책 305쪽(PDF 3): "The parameters STH and SFL are the thermal and flicker noise power spectral densities of the drain current."
  - STH: 책 115쪽(JM17-4 PDF 2) "STH is the variable name used in our lookup tables to represent the simulated thermal noise spectra density (constant across all frequencies)".
  - SFL: 책 125쪽(JM17-4 PDF 12) "the flicker noise drain current PSD (measured at f = 1 Hz) that is stored in our lookup tables".
- 원본 목록에 **VDSAT 열은 없다.** VDsat는 저장값이 아니라 2/(gm/ID)로 계산한다(3절).
- 원본 목록에 **CDB·CSB 열도 없다.** 접합 용량은 CDD·CSS 합에 들어간다(2절).
- 스윕: 책 303쪽(PDF 1) "the lookup tables used in this book are created through four-dimensional (L, VGS, VDS, and VSB) DC sweeps and noise analyses in a SPICE-like circuit simulator". 책 9쪽(JM17-1) "we perform DC sweeps (and noise simulations) in four dimensions (L, VGS, VDS and VSB) ... for a fixed device width W".
- W 비례 가정: 책 9쪽 "the parameters scale (approximately) linearly with W". 이 가정은 부록 3에서 검증한다.

### 1.2 어떻게 얻나: 시뮬레이터의 소자 op-point 출력 변수
- 책 305쪽(PDF 3): "**Most of these parameters are directly computed by Spectre, but some of them must be computed as sums of several Spectre output variables.**"
- 책 306쪽(PDF 4)의 대응 행렬 예(PDF 그림과 대조함). 열은 `{'ID','CGG','CGS','CDD'}`이다.

  | 행 | Spectre 변수 | ID | CGG | CGS | CDD |
  |---|---|---|---|---|---|
  | 1 | `mn.m1.m1:ids` | 1 | 0 | 0 | 0 |
  | 2~7 | `:vth`, `:igd`, `:igs`, `:gm`, `:gmb`, `:gds` | 0 | 0 | 0 | 0 (이 부분 예에서는 0) |
  | 8 | `:cgg` | 0 | 1 | 0 | 0 |
  | 9 | `:cgs` | 0 | 0 | 1 | 0 |
  | 10, 11 | `:cgd`, `:cgb` | 0 | 0 | 0 | 0 |
  | 12 | `:cdd` | 0 | 0 | 0 | 1 |
  | 13~15 | `:cdg`, `:css`, `:csg` | 0 | 0 | 0 | 0 |
  | 16 | `:cgsol` | 0 | 1 | 1 | 0 |
  | 17 | `:cgdol` | 0 | 1 | 0 | 1 |
  | 18 | `:cgbol` | 0 | 1 | 0 | 0 |
  | 19 | `mn.d1.d1:cj` | 0 | 0 | 0 | 1 |
  | 20 | `mn.d2.d1:cj` | 0 | 0 | 0 | 0 |

  - 책 306쪽: "considering only a subset of the variables for clarity (the actual table has additional columns)".
- 책 306쪽: "Consider the drain current ID. The single '1' in the column of this parameter means that it is simply computed taking the drain current from Spectre (mn.m1.m1:ids) and no other output variable must be added. Conversely, CGG will be computed by adding up four Spectre output variables ... The first one of these is the device's 'intrinsic' total gate capacitance, while the other three are fringe (or 'overlap') capacitances".
- 판독 1: GM·GDS·GMB·VT·C 값은 **모델이 내는 소자 op-point 변수**(`:gm`, `:gds`, `:vth`, `:cgg` …)를 읽은 것이다. 단자 전류를 수치 미분하거나 단자 AC 해석으로 잰 서술은 원문에 없다.
- 판독 2: 원문은 이 출력 변수들을 "Spectre output variables"라고 부른다. 그 변수들이 DC op-point 값이라는 것은 "DC sweeps" 서술에서 나온 해석이다.
- 소자 이름의 접두어: 책 306쪽 "the output variables have the prefix 'mn.m1.m1' since our model file places the transistors into a sub-circuit for RF modeling (i.e. it includes terminal resistances, etc.). This is not a requirement".

### 1.3 모델·시뮬레이터마다 다른 이름을 다루는 법: 설정 파일과 대응 행렬
- 책 305쪽(PDF 3): "The main Matlab script (techsweep_spectre.m) ... is kept general and does not contain any user- or process-specific parameters; all of this information is provided through a configuration file ... the file path to the simulator, the syntax template for the netlist, the sweep ranges and step sizes, as well as **the mapping from simulator output variables to Matlab variables**."
- 책 303~304쪽: "We used Cadence Spectre ... but the approach can be modified to work with other tools as well (the provided online material includes example files for both Spectre and HSPICE)."
- 책 307쪽(PDF 5): "The main step for generating lookup tables for a new technology or for additional device types ... is to create a new configuration file and re-run the main Matlab script". 설정 오류를 잡는 debug 스크립트 `techsweep_spectre_debug.m`도 있다.
- 부호 처리, 책 306쪽 각주 1: "pay special attention to the sign of the capacitances outputted by the simulator. Some of them may be negative, but may have to be counted as positive in the respective sum. In this case, the matrix entry can be set to '-1'."
- 판독: 원본은 모델 이름의 차이를 **공정마다 설정 파일의 변수 대응(부호 포함)**으로 흡수한다. 열 정의를 단자량으로 바꿔 모델과 무관하게 만드는 방식은 아니다.

### 1.4 ID는 채널 전류인가 단자 전류인가, 접합 누설·gmin
- ID는 `mn.m1.m1:ids` 하나만 읽는다(책 306쪽, 위 인용). 원문은 이것을 "the drain current from Spectre"라고만 부른다. "ids"가 채널 전류인지 단자 전류인지 원문에서 정의하는 문장은 **확인 못 함**. [외부 지식: Spectre·PSP의 `ids`는 보통 소자 내부의 drain-source 채널 전류 op 변수다. 근거로 쓰지 않음.]
- 게이트 누설은 따로 저장한다: `IGD`, `IGS` 열(책 304~305쪽). 대응 행렬에서 `:igd`·`:igs` 행은 ID 열에 0이다(책 306쪽). 곧 ID에 더하지 않는다.
- 접합 다이오드는 별도 소자(`mn.d1.d1`, `mn.d2.d1`)다. 행렬에는 그 `:cj`만 들어 있고 다이오드 전류 행은 없다(책 306쪽).
  - 판독: 접합 다이오드 전류는 ID 합에 들어가지 않는다. 이것은 행렬 구성에서 읽은 것이고, 원문이 문장으로 "누설을 뺀다"고 쓴 것은 아니다.
- 그림 2.15에 대한 서술, 책 44쪽(JM17-2 PDF 24): "One possible mechanism that could lead to the drop of gm/ID is junction leakage. **However, we have removed the junction leakage component from this plot.** What we see is in fact due to band-to-band tunneling (BT-BT) and gate-induced drain leakage (GIDL)". 이어서: "We will never bias a transistor in the region where BT-BT and GIDL play a role ... systematically disregard data to the left of the maximum every time we use the lookup function" (책 44쪽, 부록 A.2.4 책 310~312쪽).
- gmin: 원본 전체(JM17 장별 PDF 전부, J10)에서 "gmin"은 **원문에 없음**(텍스트 전수 grep 0건).

### 1.5 J10(Jespers 2010)의 표
- PDF 154 = 책 143 (Annex 1) "Semi-empirical Global Variables – Courtesy of IMEC"에 나오는 배열:
  - `IDRAINn/p`(Drain currents), `GMn/p`, `GMBn/p`, `GDSn/p`
  - "Intrinsic capacitances": `CGGn/p`, `CGSn/p`, `CGDn/p`, `CGBn/p`, `CSSn/p` (Css = "The source capacitance (com-gate)")
  - `LL` (gate lengths)
- J10 표에는 CDD·CDG·VT·잡음 열이 **없다**. VT는 표가 아니라 compact model 매개변수로 둔다: PDF 155 = 책 144, `VToN/P`, `nN/P`, `ISuoN/P`.
- 배열 크기, PDF 155 = 책 144: "a '9 by 49 by 49 by 9' 4D array ... lg ... vgs ... vds ... vs".
- 출처, PDF 23 = 책 8: "The currents stored in look-up tables are the result of measurements carried out on real transistors ... The drain currents may be derived also from advanced models such as BSIM or PSP". 각주 4는 BSIM과 PSP를 소개한다.
- 시뮬레이터 변수를 어떻게 대응시키는지는 J10에서 **확인 못 함**(IMEC 제공 데이터라 생성 절차 서술이 없다).

---

## 2. 용량

### 2.1 저장하는 용량 (JM17)
- 열: `CGG, CGS, CSG, CGD, CDG, CGB, CDD, CSS` (책 304~305쪽). 곧 **CGD와 CDG, CGS와 CSG를 따로 저장한다.**
- 정의 합: 책 56쪽(JM17-2 PDF 36) "Cgg = Cgs + Cgb + Cgd (2.46)".
- CGG·CGS·CDD에는 overlap·접합 성분을 더한다(1.2 행렬).
  - CGG = cgg + cgsol + cgdol + cgbol
  - CGS = cgs + cgsol
  - CDD = cdd + cgdol + d1:cj
  - 책 305쪽: "the total drain capacitance (CDD) consists of an intrinsic component (contributed by the MOSFET), a stray capacitance component, and a junction capacitance component."
- 예시 행렬에는 CGD·CDG·CGB·CSS·CSG 열이 없다(책 306쪽 "the actual table has additional columns"). 그래서 실제 표에서 CGD에 cgdol을 더하는지, CSS에 `mn.d2.d1:cj`를 더하는지는 **원문으로 확인 못 함**. [추정: d2는 소스 접합으로 CSS 열에 들어갈 것으로 보인다. 근거로 쓰지 않음.]

### 2.2 비상호(transcapacitance)
- 책 56쪽(JM17-2 PDF 36): "we consider only lumped capacitances in this book, in other words, we assume a quasi-static (QS) model and **don't deal with non-quasi-static (NQS) or transcapacitance effects**."
- 각주 13: "Transcapacitance effects are signified in modern devices by the fact that Cgd is not exactly equal to Cdg. Such effects are covered in the advanced modeling literature."
- 책 58쪽(PDF 38): 전류 이득 시뮬레이션 그림의 고주파 응답 일부를 "second-order effects (such as transcapacitance)"로 설명한다.
- 사용처: 3~6장 본문 code에서 `CDG`·`CSG`·`CGB` 조회는 0건이다. 쓰이는 조회는 `CGG, CGS, CGD, CDD, CSS`다.
  - 예: 책 92쪽 `CDD_W`, 책 112쪽 `CGS_W`·`CGD_W`·`CDD_W`, 책 257쪽(JM17-6 PDF 32) `GM_CSS`·`CDD_CSS`.
- 판독: 원본은 CDG를 **저장은 하지만 방법론에서는 쓰지 않고**, 회로 모델은 상호 집중 용량(QS, Cgd 하나)으로 둔다.

### 2.3 접합 용량 cdb·csb를 얻는 법
- **JM17은 LUT 안에서 얻는다.**
  - CDD 합에 접합 다이오드 `mn.d1.d1:cj`가 들어 있다(책 305~306쪽).
  - Cdb는 따로 저장하지 않고 차로 구한다. 책 112쪽(JM17-3 PDF 51) code: `Cgd = W.*lookup(nch,'CGD_W',...)`, `Cdd = W.*lookup(nch,'CDD_W',...)`, **`Cdb = Cdd-Cgd`**, `CLtot = CL+Cdb`.
  - 책 90쪽(PDF 29): "Extrinsic capacitances include the device's junction capacitances (Csb and Cdb), as well as the gate-to-drain fringe capacitance (Cgd) ... the total drain capacitance Cdd = Cdb + Cgd appears in parallel to the load. This is an approximation since Cgd contributes a feedforward current that is being neglected."
  - 책 113쪽(PDF 52): 용량 불일치는 "mainly due to assuming VDS = 0.6 V in the Matlab calculation, while the SPICE simulation indicates VDS = 0.66 V". 곧 접합을 포함한 CDD가 바이어스(VDS)에 의존하고, LUT 조회의 바이어스 가정이 오차 원인이라고 적는다.
  - 그림 2.26(책 56쪽): Cbsub(well-기판)는 "only present when the device sits in a well". 이 용량을 LUT에 넣는지는 **확인 못 함**.
- **J10은 기하 식으로 얻는다.**
  - PDF 113 = 책 101, (6.3): "C_J = A_J C_J + P_sw C_Jsw + P_swg C_Jswg".
  - 분할한 소자의 drain은 (6.4) A_JD = 0.5 N·w·w2, P_swD = N·w2, P_swgD = N·w.
  - PDF 114 = 책 102, source는 (6.5) A_JS = w(2w1 + (0.5N−1)w2), P_swS = 2(w+2w1) + (N−2)w2, P_swgS = N·w.
  - 분할하지 않으면 (6.6) A_J = W·w1, P_sw = W + 2w1, P_swg = W.
  - "Typical values for w1 and w2 are respectively 0.45 and 0.35 µm".
  - CJsw·CJswg 전형값(PDF 113 = 책 101): "of the order 10^-16 and 3×10^-16 F/µm".
  - J10의 LUT 용량은 "Intrinsic capacitances"로 표지되어 있다(PDF 154 = 책 143).

### 2.4 레이아웃·확산 기하 의존 (JM17 부록 3)
- 기준 배치를 하나 고정한다. 책 316쪽(App3 PDF 2): "The device has a total width of W = 10 µm and is partitioned into 5 fingers, each being 2 µm wide." 책 315쪽: "It is therefore practical to generate the lookup table data used in this book by assuming a fixed reference layout".
- LDE 처리, 책 315쪽: "LDE will shift the device parameters slightly after the exact finger partition and layout have been completed; however, these deviations should not require any sizing adjustments." 최종 추출은 "verification only".
- 폭 의존 실측: 책 318~320쪽.
  - W > 2 µm에서 오차는 "all errors are within about 1.5%"(책 318쪽, L = 100 nm, gm/ID = 15).
  - 여러 L과 반전 수준에서 gm/ID 최대 오차는 ~1%, gm/Cgg는 ~2%다. gm/gds는 "reaching up to 10–20% for long channels deep in weak inversion"(책 319쪽).
  - 최소 폭(0.2 µm)에서 gm/Cgg 오차는 최대 40%다. 원인은 "fringe and sidewall effects"다(책 318쪽).
  - finger 수 식 (C.3.1): nf = max(round(W/2 µm), 1) (책 317쪽).
- 접합 용량의 확산 기하(AD·AS·PD·PS)를 W마다 따로 계산하는 서술은 JM17에서 **원문에 없음**. 고정 기준 배치(nf = 5, 2 µm finger)에서 얻은 CDD를 W에 비례시켜 쓴다(CDD_W × W, 책 92·112쪽).
  - [판독: 접합 용량의 둘레 성분이 W에 정확히 비례하지 않는 문제는 부록 3의 Cgg·gds 비율 실측 범위 안에서만 다룬다. Cdd 비율의 폭 의존 실측은 원문에 없음.]

---

## 3. V*·VDsat와 포화 판단

### 3.1 정의
- JM17 책 45쪽(JM17-2 PDF 25): "Defining the drain saturation voltage of real transistors is less obvious than with the CSM model, since the drain current continues to increase with VDS in saturation. The expression of the drain saturation voltage below, which we advocate in this book, links VDsat to the reciprocal of the transconductance efficiency ... **VDsat = 2/(gm/ID) (2.34)**."
  - 약반전에서는 "boils down to 2nUT, typically near 50 mV". 강반전에서는 "VDsat is equal to the gate overdrive".
  - 각주 8: "An alternative approximation of VDsat is obtained by dividing (2.34) with the subthreshold factor n. The weak and strong inversion approximations are then equal to 2UT and (VG − VTo)/n".
- 책 46쪽(PDF 26): code `VDsat = 2./gm_ID;`. 각주 9: "there is no need to re-evaluate gm/ID for VDS = VDsat; the transconductance efficiency varies very little with the drain voltage." EKV 꼴 (2.35)는 VDsat = 2nUT(1 + qS)이다.
- 책 15쪽(JM17-1): "In the square-law framework, VDsat = VOV = VGS − VT. However, this expression does not hold in moderate and weak inversion ... VDSat is well approximated by 2/(gm/ID)".
- 기호 "V*"는 JM17 기호표(책 xi~xiii)와 색인에 **없다**. 같은 양은 'VDsat'로 쓴다(기호표 "VDsat Drain saturation voltage").
- SPICE 모델의 vdsat op 변수를 LUT에 저장하거나 쓰는 서술은 **원문에 없음**(outvars에 없음, 부록 2 전문에 vdsat 0건).
- CSM 설명, 책 26쪽(JM17-2 PDF 6): "When this happens [weak inversion], the drain saturation voltage is stuck around 60 to 100 mV ... **As soon as VD gets larger than approximately four times UT, the drain voltage loses control over the drain current.**"
- J10, PDF 34 = 책 20: "The drain current saturates as soon as the drain-to-source voltage attains 100 mV (nearly four times UT)". 약반전 식 (2.32)에 대한 서술이다. J10에서 'VDsat' 기호나 2/(gm/ID) 정의는 **확인 못 함**(텍스트 grep 0건).

### 3.2 포화 판단에 무엇을 쓰나
- **VDS ≥ VDsat + 여유**:
  - 책 174쪽(JM17-5 PDF 10): "With the chosen gm/ID (20 S/A), VDsat1 is equal to 100 mV. However, in practice, it is best to set the drain voltage of M1 somewhat larger than this value ... the output resistance of M3 varies rapidly around its VDsat. We therefore consider VDS1 equal to VDsat plus a small margin VX". code `VDS1 = 2./gmID1 + Vx;`
  - 책 177쪽(PDF 13): "When the margin VX is 50 mV or larger, the output current shows less than 0.2% variation ... **confirms the typical guideline that VDS1 should not be smaller than VDsat1 + 50 mV [3]**". [3]은 Gray, Hurst, Lewis, Meyer, *Analysis and Design of Analog Integrated Circuits*다. 이 여유는 SPICE 실측(그림 5.9)으로 확인한 경험칙이다.
- 포화 경계를 대략으로 쓰는 예:
  - 책 99쪽(JM17-3 PDF 38): "The horizontal lines in the plot mark the **(approximate)** output voltages for which the transistors leave saturation. The saturation voltages are found using (2.34) (VDsat = 2/(gm/ID))".
  - 책 172쪽: "below the drain saturation voltage VDsat1 (equal to 0.1 V per (2.34)) the current drops rapidly".
  - 책 215쪽: 공정 모서리에서 "VDsat varies significantly and this may push certain devices out of saturation".
- 헤드룸·스윙 예: 책 94쪽(VDsat2 ≈ 0.4 V는 "loss in headroom"), 책 71쪽("requiring VDsat = 150 mV, means gm/ID = 2/VDsat = 13.33 S/A").
- 약반전에서 몇 U_T를 쓰라는 판정 규칙: JM17은 CSM 설명(책 26쪽, "approximately four times UT")에만 쓰고 판정 규칙으로 정하지 않는다. 설계 판정에는 VDsat(2.34)와 +50 mV 여유를 쓴다.

---

## 4. VT(문턱)의 쓰임
- 저장한다: `VT` 열 = `mn.m1.m1:vth`(책 304~306쪽).
- 성격, 책 31쪽(JM17-2 PDF 11): "**the threshold voltage is not a quantity of physical significance.** It is merely a worthwhile notion ... This is possible using different definitions of VT, and there is no unique standard defined in the literature."
- 사이징의 독립 변수로 쓰지 않는다. 책 10쪽(JM17-1): "VOV is just a remnant of an obsolete model. Hence, a key concept advocated in this book is to eliminate VOV as a design variable altogether and instead link all design tradeoffs to the choice of gm/ID". 책 15쪽: "obviating once again the need to know VGS" (VDsat 문맥).
- 쓰이는 자리:
  - (a) EKV 매개변수(n, VT, IS) 추출. 책 36~41쪽: gm/ID 곡선에서 추출하며, LUT의 VT 열과는 다른 정의다. 예 2.3 결과 "VT = 0.5988 V".
  - (b) 비교용으로 SPICE VT를 쓴 예. 책 134쪽(JM17-4 PDF 21): "Equation (4.32) is plotted in Figure 4.19(b) using VT data from SPICE (0.5...0.38 V along the given sweep). We see that the square-law result does not fit".
  - (c) 부정합 모델 ΔVT(Pelgrom). 책 152쪽(PDF 39): "Even though VT is a somewhat ill-defined quantity in modern transistors, this is inconsequential for mismatch modeling. One can think of VT simply as a shift of the I-V transfer characteristic along the VGS axis."
- 책 134쪽: HD3에 대해 "The specific current IS and the threshold voltage VT play no role."
- J10: VT는 compact model 매개변수 VTo다(PDF 155 = 책 144). 추출은 PDF 83 = 책 70 각주(IdentN.m 등)에 있다.

---

## 5. 이 프로젝트 질문과의 관계 (원문 사실만, 권고 없음)

### (a) O-245 "DC 열도 SPICE 단자량으로 정의해서 모델 무관하게"와 원본 방식
- **다르다.**
  - 원본(JM17)은 DC 열(ID·GM·GMB·GDS·VT)을 포함한 모든 열을 **시뮬레이터가 내는 소자 op-point 출력 변수**(`mn.m1.m1:ids`, `:gm`, `:gds`, `:vth` …)에서 읽는다(책 305~306쪽).
  - 모델·시뮬레이터 차이는 **공정마다 쓰는 설정 파일의 변수 대응 행렬**(부호 −1 포함)로 흡수한다(책 305~307쪽).
  - 원본이 말하는 '모델 무관'(책 16쪽 "rely on lookup table data to maintain a model-agnostic approach")은 **설계 식이 I-V 해석 모형(템플릿)에 기대지 않는다**는 뜻이다. LUT 열을 단자량으로 정의한다는 뜻이 아니다.
  - 단자 전류나 단자 AC 어드미턴스로 열을 정의하는 서술은 **원문에 없음**.
- 원본도 ID에 게이트 누설(IGD·IGS)과 접합 다이오드 전류를 합치지 않는다. 이 둘은 따로 저장하거나 행렬에서 뺀다(책 304~306쪽). 원본의 ID는 단자 전류 합이 아니라 소자 출력 변수 `ids` 하나다.
- 용량 열 일부(CGG·CGS·CDD)는 intrinsic, overlap, 접합의 **합**으로 만든다. 그래서 '모델 내부 변수 그대로'도 아니고, 노드에서 본 총 용량에 가까운 합성값이다(책 305~306쪽).

### (b) 봉인 7 포화 판정(O-204, LUT VDSAT = SPICE `@m[vdsat]`)과 원본의 포화 판단
- **다르다.**
  - 원본은 SPICE vdsat op 변수를 저장하지도 쓰지도 않는다(outvars에 없음, 부록 2에 0건).
  - 원본의 VDsat는 **LUT의 gm/ID에서 2/(gm/ID)로 정의하는 양**이다(책 45쪽 (2.34)). 원본은 이것을 "we advocate in this book"이라고 적고, 실제 트랜지스터에서는 정의가 "less obvious"하다고 밝힌다.
  - 포화 경계는 "(approximate)"로 다룬다(책 99쪽).
  - 설계 여유는 경험칙 "VDS1 should not be smaller than VDsat1 + 50 mV [3]"을 SPICE 실측으로 확인해서 쓴다(책 177쪽).
- 원본에는 VDS = VDsat를 여유 없는 fail-closed 경계로 쓰는 규칙이 **없음**.
- 원본의 VDsat(2/(gm/ID))와 BSIM vdsat가 수치로 같은지 비교한 서술도 **없음**.

### (c) C 열 9원소(비상호) 사용과 원본
- 원본은 비상호 원소를 **저장한다**: CGD와 CDG, CGS와 CSG를 따로 저장한다(책 304~305쪽).
- 그러나 방법론은 **QS 집중 용량만 쓰고 transcapacitance는 다루지 않는다**(책 56쪽 본문과 각주 13 "Cgd is not exactly equal to Cdg").
- 3~6장 code에서 CDG·CSG·CGB 조회는 0건이다.
- 원본의 저장 열은 8개(CGG·CGS·CSG·CGD·CDG·CGB·CDD·CSS)다. CSB·CBD 같은 bulk 행 원소와, 9원소 행렬을 쓴다는 서술은 **원문에 없음**.
- 원본의 CDD·CGG에는 overlap(`cgdol` 등)과 접합(`d1:cj`)이 합쳐져 있다(책 306쪽). 그래서 원본 열 값은 모델 intrinsic 행렬 원소와 같지 않다(합성 정의).
- 원본은 Cdb를 저장하지 않고 **Cdb = Cdd − Cgd**로 구한다(책 112쪽).
- J10은 intrinsic 5종(Cgg·Cgs·Cgd·Cgb·Css)만 표에 두고, 접합은 기하 식 (6.3)~(6.6)으로 구한다(PDF 113~114 = 책 101~102).

---

## 6. 확인 못 한 것과 원문에 없는 것 (목록)
1. `ids`가 채널 전류인지 단자 전류인지 정의하는 문장: 확인 못 함.
2. gmin 처리: 원문에 없음.
3. 실제 대응 행렬의 CGD·CDG·CGB·CSS·CSG 열에 overlap이나 d2 접합을 더하는지: 확인 못 함. 예시는 부분 행렬이다.
4. GM·GDS·GMB를 op 변수로 읽는 것 말고 단자 AC나 수치 미분으로 재는 서술: 원문에 없음.
5. SPICE vdsat 사용, 그리고 V* 기호: 원문에 없음. 원본은 VDsat = 2/(gm/ID)로 정의한다.
6. 확산 기하(AD·AS·PD·PS)를 W마다 따로 계산하는 서술: JM17에는 없음. J10에는 기하 식이 있다.
7. J10 표의 생성 절차(시뮬레이터 변수 대응): 확인 못 함. IMEC 제공 데이터다.
8. Cbsub를 LUT에 넣는지: 확인 못 함.
