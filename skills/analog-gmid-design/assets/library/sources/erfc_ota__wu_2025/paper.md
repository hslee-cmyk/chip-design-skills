# C. Wu et al., Power-Efficient Recycling Folded Cascode OTA Based on Nested Local Feedback and Adaptive Biasing (Sensors 25(8):2523, 2025)

- 원본 PDF: `C:\Users\HSLEE\Documents\Todoc\fpga\wt\_heldout\erfc_sensors2025.pdf` (논문모음·Gm_over_Id 두 폴더에 같은 원문 없음, 2026-10-14 확인)
- 사본: `source.pdf` (sha256 `ea13f0d354fdbc13edd5dbcbf1a5c4b35b4ba8f9dba5dcc949f28c843fbd8722`)
- 웹 출처: https://pmc-oa-opendata.s3.amazonaws.com/PMC12031453.1/PMC12031453.1.pdf (PMC12031453 오픈액세스) · 출판사 https://www.mdpi.com/1424-8220/25/8/2523
- 그림·표 위치: p.5 Figure 3(b) adaptive biasing · p.6 Figure 4(a) NLF · p.8 Figure 6 'Transistor-level implementation of proposed ERFC OTA'(+오른쪽 위 VDD·VCP·VCN·IB·IC 표) -- 엔진 topology 근거 · p.9 Table 1(치수) · p.13 본문 CL · p.14 Table 2
- 엔진 연결: `assets/library/erfc_ota.topology.json`, `erfc_ota.sizing_spec.json`, `erfc_ota.spec_source.md`, `erfc_ota.topology.md`
- 쪽 수: 18
- 변환: PyMuPDF 텍스트 추출(쪽 단위). 수식·표·그림은 텍스트가 깨질 수 있으니 같은 쪽의 렌더 PNG(`pages/`)로 확인할 것.

---

## p.1

![p.1](pages/p01.png)

```text
Academic Editor: Cristoforo
Marzocca
Received: 28 February 2025
Revised: 15 April 2025
Accepted: 15 April 2025
Published: 17 April 2025
Citation: Wu, C.; Cai, P.; Li, J.; Xie, J.;
Luo, Z. Power-Efficient Recycling
Folded Cascode Operational
Transconductance Amplifier Based on
Nested Local Feedback and Adaptive
Biasing. Sensors 2025, 25, 2523.
https://doi.org/10.3390/s25082523
Copyright: © 2025 by the authors.
Licensee MDPI, Basel, Switzerland.
This article is an open access article
distributed under the terms and
conditions of the Creative Commons
Attribution (CC BY) license
(https://creativecommons.org/
licenses/by/4.0/).
Article
Power-Efficient Recycling Folded Cascode Operational
Transconductance Amplifier Based on Nested Local Feedback
and Adaptive Biasing
Chunkai Wu 1,†, Peng Cai 2,†, Jinghu Li 1,*
, Jin Xie 3
and Zhicong Luo 3
1
School of Computer and Information Technology, Fujian Agriculture and Forestry University,
Fuzhou 350002, China; chunkaiwu1105@163.com
2
Department of Information and Electromechanical Engineering, Jinshan College, Fujian Agriculture and
Forestry University, Fuzhou 350002, China; 0236798063@stu.fafu.edu.cn
3
School of Mechanical and Electrical Engineering, Fujian Agriculture and Forestry University,
Fuzhou 350002, China; jinxie1216@126.com (J.X.); zcl@fafu.edu.cn (Z.L.)
*
Correspondence: jhlee@eochip.com
†
These authors contributed equally to this work.
Abstract: In this paper, we present a novel enhanced recycling folded cascode (ERFC)
operational transconductance amplifier (OTA), which exhibits high efficiency and a fast
transient response under weak inversion. Our innovative combination of adaptive biasing
with nested local feedback (ABNLF) effectively enhances the input transconductance and
slew rate (SR), thus improving the transient response. By incorporating coupling capacitors
at the output stage, we achieve a stable operating region with large signal responses. Both
the traditional RFC OTA and the proposed ERFC OTA were designed in a 0.18 µm CMOS
process, operating at a power supply of 1.8 V, with quiescent currents of 8 µA and 10.4 µA,
respectively. Post-layout simulations reveal a remarkable enhancement in the proposed
ERFC OTA over the traditional RFC OTA, with the SR and gain–bandwidth (GBW) surging
by 120- and 5.95-fold, respectively. This advancement boosts the efficiency of the traditional
RFC OTA and provides an impressive figure of merit (FoM) of 130.04 (V/µs)·pF/µA.
Keywords: enhanced recycling folded cascode (ERFC); high efficiency; transient response;
adaptive biasing; nested local feedback technique
1. Introduction
In analog and mixed-signal circuits, low-power operational transconductance ampli-
fiers (OTAs) play a crucial role and are commonly used in a range of applications, such
as in portable devices, Internet of Things sensors, and medical electronic devices [1–4].
The folded cascode (FC) OTA, known for its balanced gain and signal swing, is a popular
choice among different OTA architectures. Designers typically favor the PMOS-input
FC OTA, as it features a higher non-dominant pole, lower flicker noise, and a reduced
common-mode level compared to the NMOS variant [5–11]. However, traditional FC OTAs
may be inefficient since they rely on current sources in the folded stage, which limits their
performance at lower current levels. To resolve this matter, the recycling folded cascode
(RFC) OTA is introduced to enhance FC OTA performance. By substituting the folded-stage
current source with active current mirrors, the RFC OTA achieves a higher gain–bandwidth
(GBW) and slew rate (SR) with no change in its power consumption [12–14]. Nevertheless,
the performance in terms of GBW, SR, and noise is influenced by the current mirror ratio,
which may have a destabilizing effect by shifting non-dominant poles to lower frequencies
Sensors 2025, 25, 2523
https://doi.org/10.3390/s25082523
```

---

## p.2

![p.2](pages/p02.png)

```text
Sensors 2025, 25, 2523
2 of 18
and affecting power consumption. Moreover, the fixed tail current source restricts the
slew rate.
Numerous techniques have been proposed to tackle the challenges associated with the
traditional RFC OTA. These techniques include current shunt methods, double recycling FC
OTAs, positive-feedback techniques, and multi-path recycling methods. An improved RFC
OTA, as discussed in [15,16], effectively increases the ratio of the dynamic current source
without requiring additional power consumption. In a study outlined in [17], a positive
feedback mechanism implemented through cross-coupling achieves effects similar to those
described in [18]. Additionally, strategies such as double RFC (DRFC) [19] and multi-
path RFC (MRFC) [20] have been harnessed to enhance RFC performance. However,
the intricate nature of these circuit structures introduces additional low-frequency zero-
pole pairs, potentially constraining performance in high-frequency applications. One
common limitation of these methodologies is the Class A operation of the amplifier. In the
context of the RFC OTA, a technique known as local common-mode feedback (LCMFB) has
been applied (as discussed in [21]). Nevertheless, the slew rate (SR) enhancement remains
restricted due to the Class A operation of the input stage and the finite resistance associated
with LCMFB. A recent development in this field is the introduction of a super Class AB
RFC OTA, as proposed in [12,22], which significantly enhances both the gain–bandwidth
(GBW) and SR. However, achieving high transconductance at low static current requires a
large resistor, resulting in a substantial spatial footprint. Furthermore, the SR is limited due
to the constant bias of the cascode transistors, as indicated in [23,24].
To address the above limitations, this work proposes an improved RFC OTA with
low power consumption. A novel adaptive biasing and nested local feedback topology is
introduced in the proposed ABNLF technique, enhancing the input equivalent transcon-
ductance without consuming extra power. This method resolves the trade-off between
power efficiency and GBW. Additionally, a floating bias network is used for the output-
stage cascode transistors, ensuring stable operating conditions for the OTA under large
signal conditions. The designed ERFC OTA demonstrates good performance in terms of
gain–bandwidth, power consumption, and noise.
The article is structured as follows. Section 2 provides a brief analysis of the conven-
tional RFC OTA and introduces the principle behind the proposed ERFC OTA. Section 3
presents the circuit implementation along with a detailed analysis of low- and large-signal
performance. Post-layout simulation results are discussed in Section 4, followed by the
conclusion in Section 5.
2. Methodology of ERFC OTA
2.1. Limitations of Conventional RFC OTAs
The conventional RFC OTA is shown in Figure 1, assuming that ( W
L )1B = ( W
L )1A,
( W
L )3B:( W
L )3A = K and K is a constant. Its equivalent transconductance and gain–bandwidth
(GBW) can be expressed as follows:
gm,RFC = (1 + K)gm1A
(1)
GBWRFC = (1 + K)gm1A
2πCL
(2)
where gm1A is the transconductance of M1A, gm1A = gm1B, CL is the load capacitance of
the OTA, and factor K is usually set to 3 to ensure that the RFC OTA has the same power
consumption as the FC OTA.
```

---

## p.3

![p.3](pages/p03.png)

![p.3 내장 이미지 1](images/p03_1.png)

```text
Sensors 2025, 25, 2523
3 of 18
Figure 1. Conventional RFC OTA [13,14].
When a large-signal Vid is introduced to the input pair, the largest output current is
limited to 2KIB. Therefore, the slew rate (SR) of the RFC OTA can be expressed as follows:
SRRFC = 2KIB
CL
(3)
Increasing K has a dual positive impact on the performance of both the GBW and
the slew rate (SR). However, it will lead to higher power consumption and causes non-
dominant poles to shift to lower frequencies, which may have a destabilizing effect. More-
over, the fixed bias current at the tail restricts the SR. These combined factors constrain the
power efficiency of the RFC OTA circuit.
2.2. Concept of ERFC OTA
The proposed ERFC OTA structure is shown in Figure 2. M3B, M4B, M9, and M10 form
a current mirror, which resembles the traditional current mirror OTA. This design includes
several key modifications compared to the conventional structure depicted in Figure 1. It
retains the cross-coupling structure to enhance dynamic characteristics and introduces a
wide-swing, low-power adaptive tail current source for the input differential pairs M1A,
M2A, M1B, and M2B. A nested local feedback circuit serves as the load for the first-stage
amplifier. This network improves the transient response through its internal feedback loop.
Furthermore, coupling capacitors CBAT1 and CBAT2, along with the bias resistor RL, provide
floating bias voltages for the gates of M5–M8. This addresses the potential operating point
shift in traditional ERFC OTAs during the transient response.
```

---

## p.4

![p.4](pages/p04.png)

![p.4 내장 이미지 1](images/p04_1.png)

```text
Sensors 2025, 25, 2523
4 of 18
Figure 2. Concept of the proposed ERFC OTA.
MOSFETs biased in the weak inversion region achieve higher transconductance,
reduced noise, and improved current efficiency at the cost of larger mismatch or area.
The MOSFET current in the weak inversion region can be expressed as follows:
ID = (W
L )I0 exp(VGS −VTH
mVT
)[1 −exp(−VDS
VT
)]
(4)
where W/L is the aspect ratio, I0 = µCoxV2
T is a process-dependent constant, µ is the carrier
mobility, Cox is the capacitance per unit area of the gate oxide, VT = kT/q is the thermal
voltage, VGS is the gate-source voltage, T is the absolute temperature, k is Boltzmann’s
constant, q is the electronic charge, VTH is the threshold voltage, m is the subthreshold slope
factor, and VDS is the transistor drain-source voltage. When VDS is greater than 100 mV,
Equation (4) can be simplified as follows:
ID ≈(W
L )I0 exp(VGS −VTH
mVT
)
(5)
Therefore, the transconductance of the transistor under subthreshold bias is expressed
as follows:
gm = ∂ID
∂VGS
=
ID
mVT
(6)
As shown in Equations (5) and (6), MOSFETs operating under weak inversion exhibit
a larger transconductance efficiency ( gm
Id ) compared to those operating in the saturation
region. In this design, the circuit operates in the subthreshold region to enhance the OTA’s
transient response while maintaining low power consumption. Circuit matching must be
closely monitored to prevent mismatches from affecting the OTA’s static operating point
and dynamic response.
```

---

## p.5

![p.5](pages/p05.png)

![p.5 내장 이미지 1](images/p05_1.png)

```text
Sensors 2025, 25, 2523
5 of 18
3. Circuit Implementation
3.1. The ABNLF Technique
The proposed ABNLF technique consists of three parts: an adaptive wide-swing
current source, a nested local feedback network, and an output stage floating bias circuit.
The goal is to achieve a good transient response while maintaining low power consump-
tion. Figure 3a illustrates the principle of adaptive biasing with input expansion. It uses
two floating voltage sources, VB, to bias the input differential pair. Figure 3b shows the
transistor-level implementation of the floating voltage source bias circuit. M1A, M2A, M1B,
and M2B serve as the differential inputs for the designed OTA circuit. M11 and M12 act as
the floating voltage sources, VB, to provide a bias voltage to the differential pair. In the
ideal case of a perfectly matched differential pair, the source stages of the differential
pairs M1A, M2A, M1B, and M2B match the source stages of the floating voltage sources
M11 and M12, and the current of the input differential pair is 0.5IB. Moreover, M15 and
M16 are independently biased by the current source, IC. Together with M11, M13, M12,
and M14, they form a flipped voltage follower (FVF) structure. M15 and M16 are used as
a level-shifter to increase the FVF input swing. Thus, when a large step signal is input
to the differential pair, the adaptive biasing current source can provide a large dynamic
current that is not limited by IB. This current is positively correlated with the square of the
input differential signal. Additionally, the transconductance of the input pair is effectively
doubled by the cross-coupling of the two flipped voltage followers (FVFs), ensuring that
the input transistors receive the fully differential signal.
Figure 3. Adaptive bias with input expansion.
```

---

## p.6

![p.6](pages/p06.png)

![p.6 내장 이미지 1](images/p06_1.png)

```text
Sensors 2025, 25, 2523
6 of 18
The proposed nested-local feedback (NLF) is shown in Figure 4a. It is achieved by
embedding the local positive feedback formed by the cross-coupling of M17A and M18A in
the conventional LCMFB [15], where the transistor aspect ratio of M3B:M3A:M17A is 15:3:2.
Additionally, the introduction of M3C,4C,17B,18B improves the replication accuracy of the
current in static conditions. In the quiescent state, assuming the devices perfectly match,
no current flows through the resistors R1,2 = RA, and the voltage VX = VY = VZ. At this
time, the static behavior of the NLF is similar to that described in [18].
Figure 4. Proposed nested local feedback (a) circuit with (b) as mall-signal model.
In small-signal operation, when a fully differential current iind is applied to the NLF,
half of the current iind/2 flows through the resistors R1,2 = RA, generating complementary
voltages vX = −vY at nodes X and Y. Consequently, node Z can be treated as a virtual
ground. The simplified small-signal model of the NLF is depicted in Figure 4b, where gmi
and roi represent the transconductance and output impedance of Mi, respectively. Thus,
the impedance of nodes X and Y can be formulated as follows:
RX,Y =
RA//roeq,X,Y
1 −gm17A,18A(RA//roeq,X,Y)
(7)
It is important to feasibly design gm17A,18A and RA to ensure that RX,Y > 0, which
guarantees the stability of the NLF. Additionally, the negative resistance −1/gm17A,18A in-
troduced via the local positive feedback increases the resistance RX,Y at nodes X and
Y, reducing the passive resistance area.
The NLF current gain can be expressed as
```

---

## p.7

![p.7](pages/p07.png)

![p.7 내장 이미지 1](images/p07_1.png)

```text
Sensors 2025, 25, 2523
7 of 18
Ai = gm3B,4BRX,Y, which is independent of the current mirror ratio and is not affected by
the parasitic capacitance at node Z.
Considering large-signal operation, if a large-signal current Iind is applied to the NLF,
the voltages at nodes X and Y may become unbalanced due to the voltage drop across
the LCMFB resistor RA, and this instability is significantly reinforced by the local positive
feedback loop. As a result, the voltage at node X will be very high while the voltage at
node Y is close to 0. As a result, M3B enters saturation and the strong inversion region,
while M4B and M17A enter the cutoff region, and M18A enters the deep linear region. Thus,
the differential output current of the NLF is Iout = Io+ −Io−, and it can be expressed by the
square law.
Taking an NMOS cascode transistor as an example, a conventional constant gate bias
cascode transistor is shown in Figure 5a. When a large-signal current flows through the
transistor, the voltage at its source decreases significantly, potentially shifting the circuit’s
DC operating point. For example, in Figure 4a, M5 is the cascode transistor with M3B
as its source-connected current source, and M3B may enter the linear region under large-
signal conditions, limiting the output current. The proposed floating-gate bias cascode
transistor depicted in Figure 5b is implemented using a RL and CBAT. In a static state,
no current flows through the series RLCBAT, and VC is equal to VE without additional
power consumption. If a large step is applied, an induced voltage is generated via an
induction circuit and connected to VS. VS travels through the RC highpass filter to the gate
of the cascode transistor, preventing the transistor connected to its source from entering the
linear region and increasing the permissible high current output. Furthermore, the induced
voltage can be generated via the NLF without the need for additional circuits. The RLCBAT
is often designed as larger to achieve a lower low cut-off frequency. The CBAT does not
need to be excessively large, as the local positive feedback loop significantly enhances the
large-signal response at VX,Y. This is primarily due to the amplified signal amplitude at VS
introduced via the feedback mechanism, which reduces the dependency on a large CBAT to
achieve the desired signal swing and response speed. Consequently, this design approach
enables a more area-efficient implementation while maintaining robust performance under
large-signal conditions. Moreover, the RL also can be realized using a transistor. This
facilitates a reduction in the area.
Figure 5. The bias cascode transistor in (a) constant and (b) floating.
3.2. Transistor-Level Implementation
Based on the proposed ABNLF technique, the final transistor-level circuit implementa-
tion of the ERFC OTA is depicted in Figure 6. In the proposed circuit, transistors M15 and
M16 are biased in the saturation region to achieve a higher source-to-gate voltage (VSG),
which facilitates an extended input range under the given bias current, IC. Transistors M19
to M21 are operated in the deep triode region, functioning as active resistors to provide the
desired impedance characteristics. All remaining transistors are biased in the subthreshold
```

---

## p.8

![p.8](pages/p08.png)

![p.8 내장 이미지 1](images/p08_1.png)

```text
Sensors 2025, 25, 2523
8 of 18
region to maximize the intrinsic gain and transconductance (gm) for a given bias current,
thereby enhancing the overall performance of the circuit. This strategic biasing approach
ensures optimal trade-offs between input range, gain, and power efficiency.
Figure 6. Transistor-level implementation of proposed ERFC OTA.
Table 1 shows the design dimensions of the proposed ERFC OTA and traditional
RFC OTA. In the design and optimization of the ERFC OTA, the selection of transistor
dimensions is a critical design decision, directly impacting the circuit’s performance, power
consumption, and stability. For the differential pair and cascode transistors, a large width-
to-length ratio and a short channel length are employed to enhance the gain bandwidth
(GBW) and input transconductance. For the current mirror, a longer channel length is
preferred to increase the output impedance. Additionally, the area of the differential pair is
carefully balanced to further optimize input noise performance. In the ERFC OTA design,
the transistor dimensions must be carefully traded off among gain, power consumption,
noise, stability, robustness, and area. By optimizing the width and length of the transistors,
a high-performance, low-power, and robust OTA can be achieved, meeting the demands of
complex analog circuit design.
Compared with the traditional RFC OTA, the proposed ERFC OTA needs to consider
the proper operation of the FVF (folded-voltage-follower) structure, which sacrifices some
voltage margin. The proposed ERFC OTA utilizes the FVF structure with input extension to
replace the adaptive biasing of the input-pair transistor M0. For proper operation, the FVF
transistors (M11/M12, M13/M14) must remain in the saturation region to maintain the
appropriate operating point. Under small input conditions, transistors M11 and M12 enter
the linear region, defining the lower limit of the input signal. Conversely, under large
input conditions, transistors M13 and M14 enter the linear region, causing a significant
decrease in the gate-to-source voltages of M15 and M16. This drives the current source, IB,
```

---

## p.9

![p.9](pages/p09.png)

![p.9 내장 이미지 1](images/p09_1.png)

```text
Sensors 2025, 25, 2523
9 of 18
into the linear region, disrupting the operating point and defining the upper limit of the
input signal. Therefore, the input voltage range of the proposed traditional ERFC OTA is
expressed as follows:
VDD −VSG11 −VSG13 −VSD11,sat −VSG15 ≤Vin ≤VDD −VSG11 −VSD13,sat
(8)
Since the output branches of the traditional RFC OTA and the proposed ERFC OTA
are almost the same, and the floating-gate bias does not affect its output signal range,
the output signal ranges are identical and can be expressed as follows:
VDS4B,sat + VDS6,sat ≤Vout ≤VDD −VSD10,sat −VSD8,sat
(9)
Table 1. OTA device dimensions under PVT variations.
ERFC OTA
RFC OTA
M1A,1B,2A,2B,11,12
24 µm/0.6 µm
M9,10
48 µm/0.3 µm
M1A,1B,2A,2B
24 µm/0.6 µm
M3A,4A
18 µm/0.3 µm
M13,14
24 µm/0.3 µm
M3A,4A
18 µm/0.3 µm
M17A,18A
12 µm/0.3 µm
M3C,4C,17B,18B
30 µm/0.3 µm
M3B,4B
90 µm/0.3 µm
M3B,4B
90 µm/0.3 µm
M15,16
1 µm/20 µm
M7,8
24 µm/0.3 µm
M5,6
60 µm/0.3 µm
M19,20,21
3 µm/1 µm
M5,6
60 µm/0.3 µm
M7,8
24 µm/0.3 µm
R1,2
52 kΩ
M9,10
48 µm/0.3 µm
3.3. Small-Signal Analysis
The small-signal half-circuit of the ERFC OTA is illustrated in Figure 7. The transcon-
ductance and GBW of the proposed ERFC OTA are expressed as follows:
gm,ERFC = 2(gm1Bgm4BRY + gm2A)
(10)
GBWERFC = 2(gm1Bgm4BRY + gm2A)
2πCL
(11)
where RY ≈R1,2/(1 −gm17A,18AR1,2) and RC ≈1/gm5,6, respectively.
Figure 7. The small-signal half-circuit of ERFC OTA.
Factor 2 in Equation (11) is attributed to the transconductance provided via the
adaptive bias circuits of the differential pair, and factor gm4BRY is attributed to the
NLF configuration.
```

---

## p.10

![p.10](pages/p10.png)

```text
Sensors 2025, 25, 2523
10 of 18
The RFC and ERFC OTA have identical output branches in terms of quiescent current
and transistor aspect ratios. Consequently, the output impedance is also the same and is
expressed as follows:
Rout ≈(ro2A//ro4B)gm6ro6//ro10gm8ro8
(12)
Stability is a fundamental requirement for the proper operation of an OTA. It is pri-
marily governed by the phase margin of the amplifier, which is directly influenced by
the positions of the poles and zeros in the transfer function. For the same load capac-
itance, CL, since the output impedances of both the ERFC OTA and the conventional
RFC OTA are identical and very large, they share the same dominant pole, which can be
expressed as wp1 = −1/RoutCout ≈−1/RoutCL. The non-dominant poles of the ERFC
OTA are wp2 = −1/RX,YCx,Y and wp3 = −1/RCCC, where CX,Y ≈Cgs3B,4B + Cgs18A,17A
and CC represents the parasitic capacitance at the source node of M5 or M6. Given
that RX,Y · CX,Y ≫RC · CC, the first non-dominant pole wp2 of the proposed ERFC
OTA must be at least 2.2 times larger than the unity-gain–bandwidth (GBW) to ensure
a sufficient phase margin. Typically, the amplifier phase margin can be expressed as
follows: PM = 180 −tan−1(GBW/wp1) −tan−1(GBW/wp2) −tan−1(GBW/wp3). Since
wp1 ≪GBW, it follows that tan−1(GBW/wp1) ≈90◦. Additionally, since wp3 ≫wp2,
and tan−1(1/2.2) ≈tan−1(0.4545) ≈24.4◦. Therefore, the PM of the proposed ERFC OTA
is given as follows:
PM ≈90◦−tan−1
 GBW
fX,Y

≈90◦−tan−1
2[gm,1Agm,3BRX,Y + gm,1A]RX,YCX,Y
CL

(13)
Therefore, the required load capacitance can be described as follows:
CL,min ≥2(gm,1Agm,3BRX,Y + gm,1A)RX,YCX,Y
0.45
(14)
In this design, a 70 pF capacitor will be used as the compensation capacitor CL,
sacrificing the gain in bandwidth to ensure loop stability.
3.4. Noise Analysis
Flicker noise and thermal noise are the primary noise sources in CMOS analog circuits.
The input-referred mean-square noise voltage spectral density in a CMOS device is defined
as follows:
V2n ( f ) = 4kTγ
gm
+
KP/N
CoxWL f
(15)
where k is the Boltzmann’s constant, T is the absolute temperature, and the factor γ varies
from 1/2 to 2/3, e.g., from weak to strong inversion, for long-channel devices. KP/N
represent the flicker noise coefficient, which is dependent on the CMOS process and device
characteristics. The first and second terms of Equation (15) represent the thermal and
flicker noise spectral density, respectively. Similarly, the thermal noise spectral density for
a resistor of resistance R is given as follows:
V2
nR = 4kTR
(16)
```

---

## p.11

![p.11](pages/p11.png)

```text
Sensors 2025, 25, 2523
11 of 18
Under the assumption that all noise sources are uncorrelated and, for simplicity, that
we have the same γ factor for all MOSFETs, the input-referred mean-square thermal noise
spectral density of the RFC OTA in a bandwidth ∆f can be expressed as follows:
V2
T,inRFC =
8kTγ
h
(1 + K2) + (1 + K) gm3A
gm1A + gm9
gm1A
i
gm1A(1 + K)2
(17)
The thermal noise expression for the proposed ERFC OTA can be expressed as
Equation (18).
V2
T,inERFC =
2kTγ
gm1A(1 + gm3BRX,Y)2

(1 + g2
m3BR2
X,Y) + g2
m3BR2
X,Y(1 + α +
1
γgm3AR1,2
) gm3A
gm1A
+ β gm3A
gm1A
+ gm9
gm1A

(18)
where α and β are the ratios of M17A and M3A, as well as M3B and M3A, which are 2/3 and
15/3, respectively.
For the flicker noise, it is again assumed that all noise sources are uncorrelated and
equal for the same type (NMOS or PMOS) of transistor KP/N. The input-referred mean-
square flicker noise of the RFC OTA in a bandwidth ∆f is shown as Equation (19). The ex-
pression of flicker noise for the proposed ERFC OTA is Equation (20).
Determining which configuration has lower noise directly based on Equations (17)–(20)
is difficult. However, by optimizing the transconductance and size of the input MOSFETs
for the proposed ERFC OTA, we can minimize the input-referred noise. This optimization
enables the ERFC OTA to achieve lower noise than traditional designs, primarily due to its
larger equivalent input transconductance, which reduces input-referred noise.
V2
F,in( f ) =
2
h
KP
Cox(WL)1A f g2
m1A +
KP
Cox(WL)1A f g2
m1AK2 +
KN
Cox(WL)3A f g2
m3AK2 +
KN
Cox(WL)3B f g2
m3B +
KP
Cox(WL)9 f g2
m9
i
(1 + K)2g2
m1A
(19)
V2
F,inERFC( f ) =
2
n
KP
Cox(WL)1A f g2
m1A
h
1 + g2
m3BR2
X,Y
i
+ g2
m3BR2
X,Y
h
KN
Cox(WL)3A f g2
m3A +
KN
Cox(WL)17A f g2
m17A
i
+
KN
Cox(WL)3B f g2
m3B +
KP
Cox(WL)9 f g2
m9
o
4g2
m1A(1 + gm3BRX,Y)2
(20)
3.5. Large-Signal Response
The slew rate (SR) is an important factor in the settling time of the proposed ERFC OTA.
Under static conditions, the currents of M1A,1B and M2A,2B are all equal to 0.5IB. The cur-
rents flowing into nodes X and Y are Iin+ and Iin−, provided via I2B and I1B, respectively.
They are also equal to 0.5IB and distributed via transistors M17A : M3A in a 2:3 ratio. There-
fore, the current of M3A is 0.3IB, and no current flows through resistor R1,2. The voltages of
nodes of X, Y, and Z are VX = VY = VZ = mVT ln{0.3IB/[(W/L)3A,4AIo]} + VTH.
We assume that the large-signal Vid = (Vin+ −Vin−) > 0 is applied to the input
pair. The operating region of M2B shifts from weak inversion at static to strong inversion,
while the operating region of M1B shifts from weak inversion at static to the cut-off region.
Therefore, M2B, M1B yields a differential current, Iind = Iin+ −Iin−≈I2B, which can be
expressed as follows:
I2B =1
2 β2B(mVT ln[
0.5IB
I0(W/L )] + Vid)
2
≈1
2 β2BV2
id
(21)
The NLF generates a significant voltage swing at nodes X and Y, resulting in a current
of Iind/2 through both resistors. This local positive feedback accelerates the voltage imbal-
ance at these nodes. The current through M3A and M4A is the common-mode component,
```

---

## p.12

![p.12](pages/p12.png)

![p.12 내장 이미지 1](images/p12_1.png)

```text
Sensors 2025, 25, 2523
12 of 18
Icm ≈(Iin+ + Iin−)/2 −(I17A + I18A)/2 ≈I2B/2 >> 0.3IB. Hence, the voltage of X, Y,
and Z can be given as follows:

















VZ =
s
2Icm
β3A,4A
+ VTH
VX = VZ + R1Iind
2
VY = VZ −R2Iind
2
(22)
The ERFC output current Iout is represented as shown below:
Iout ≈Io+ = I3B = 1
2 β3B(
s
2Icm
β3A
+ R1Iind
2
)
2
≈1
2 β3B(
s
β2B
2β3A
V2
id + R1β2B
4
V2
id)
2
(23)
From Equation (23), Iout is proportional to V4
id. A similar result occurs during negative
slewing. Therefore, the slew rate (SR) of the proposed ERFC OTA can be expressed as
follows:
SRERFC = Iout
CL
(24)
By integrating the Class-AB input stage with the nonlinear feedback (NLF) mechanism,
the proposed enhanced recycling folded cascode (ERFC) OTA achieves a maximum output
current proportional to V4
id, significantly enhancing the slew rate (SR) compared to the
conventional recycling folded cascode (RFC) OTA.
4. Post-Layout Simulations and Comparisons
The proposed ERFC OTA uses an 0.18 µm CMOS process with a supply voltage of 1.8 V
and a quiescent current of 10.4 µA. The bias current IB is 2 µA, and the load capacitance CL
is 70 pF. The layout of the proposed ERFC OTA is presented in Figure 8, with an active area
of 107 × 83 µm2.
Figure 8. The layout of ERFC OTA.
The open-loop frequency response of two OTAs is shown in Figure 9. The post-
layout simulation uses a typical corner and a common-mode input voltage of 800 mV.
```

---

## p.13

![p.13](pages/p13.png)

![p.13 내장 이미지 1](images/p13_1.png)

![p.13 내장 이미지 2](images/p13_2.png)

```text
Sensors 2025, 25, 2523
13 of 18
The proposed ERFC OTA achieves a GBW of 1.37 MHz, six times higher than the RFC OTA.
The DC gain of the ERFC OTA is 84.18 dB, which is significantly greater than that of the
RFC OTA. The phase margin (PM) for the ERFC OTA is 67.05◦, and the PM for the RFC
OTA is 89.15◦. The ERFC OTA’s PM decreases by 22.1◦due to increased transconductance.
However, it remains well above the 60◦threshold, ensuring stable operation.
Figure 9. Open-loop frequency response of ERFC OTA.
Figure 10 illustrates the noise performance of the two amplifiers. At 1 MHz, the input-
referred noise, primarily dominated by thermal noise, is 31.86 nV/
√
Hz for the proposed
ERFC OTA and 37.77 nV/
√
Hz for the RFC OTA. At 0.1 Hz, where flicker noise is the
dominant factor, the input-referred noise is 26.61 µV/
√
Hz for the proposed ERFC OTA
and 40.10 µV/
√
Hz for the RFC OTA. The proposed amplifier demonstrates low noise
performance due to its enhanced transconductance.
Figure 10. Equivalent input noise of ERFC OTA.
Two OTAs are configured as unity-gain-inverting amplifiers to simulate low- and
large-signal transient responses. A 100 kHz, a 10 mV peak-to-peak periodic square wave
with a 50% duty cycle and an 800 mV DC level is applied. The output transience is
```

---

## p.14

![p.14](pages/p14.png)

![p.14 내장 이미지 1](images/p14_1.png)

![p.14 내장 이미지 2](images/p14_2.png)

```text
Sensors 2025, 25, 2523
14 of 18
illustrated in Figure 11. The ERFC OTA achieves a 1% settling time of 0.473 µs, which
is significantly faster than the RFC OTA’s 2.945 µs. This improvement is attributed to
increased transconductance.
Figure 11. Small-signal transient response of ERFC OTA.
The proposed ERFC OTA demonstrates significantly improved large-signal transient
performance compared to the RFC OTA, as shown in Figure 12. When a 600 mV peak-
to-peak periodic square wave is applied, the ERFC OTA achieves an average slew rate of
19.32 V/µs, which is better than the RFC OTA’s 0.16 V/µs. Additionally, the ERFC OTA’s
step response shows no ringing, indicating a minimal impact on PM. Although there is an
overshoot of approximately 100 mV, it is smaller than that reported in prior work [24].
Figure 12. Large-signal transient response of ERFC OTA.
Table 2 compares the performance parameters of the designed ERFC OTA with conven-
tional RFC OTAs. Table 3 shows the simulation results across process, power supply voltage,
and temperature (PVT) variations. The results indicate that the ERFC OTA has an excellent
GBW and transient response while using nearly the same static power consumption.
```

---

## p.15

![p.15](pages/p15.png)

![p.15 내장 이미지 1](images/p15_1.png)

![p.15 내장 이미지 2](images/p15_2.png)

```text
Sensors 2025, 25, 2523
15 of 18
Table 2. The performance comparison of two OTAs.
Parameter
Traditional RFC OTA
Proposed ERFC OTA
Supply current (µA)
8
10.4
CL (pF)
70
70
GBW (MHz)
0.23
1.37
DC gain (dB)
68.37
84.18
Phase margin (◦)
89.15
67.05
Average slew rate (V/µs)
0.16
19.32
1% setting time (µs)
2.945
0.473
Input noise (nV/
√
Hz)
37.77
31.86
FoMS (MHz pF/µA)
2.01
9.22
FoML (V/µs) pF/µA)
1.40
130.04
Table 3. Performance of the OTA under PVT variations.
Parameter
Corner
VDD
Temp
FF
SS
SF
FS
TT
−10%
+10%
−40°
+125°
GBW (MHz)
1.71
1.10
1.41
1.33
1.37
1.14
1.63
1.22
1.47
PM (◦)
63.29
69.03
65.95
67.45
66.86
72.32
60.95
70.42
57.87
Gain (dB)
83.87
84.02
84.87
83.55
84.18
82.56
85.7
84.45
82.48
SRav (V/µs)
18.74
18.015
17.81
19.79
19.175
18.42
19.435
15.68
18.005
STav (ns)
391.3
539.3
468.25
479.5
471.95
359.65
429.2
388.15
626.85
To evaluate the effects of process variations and mismatches on the proposed ERFC
OTA, 200-point Monte Carlo simulations were performed, and the simulation results are
shown in Figure 13. The GBW, DC gain, phase margin, and offset voltage under 200-point
Monte Carlo simulation are shown in Figure 13a, b, c and d, respectively. The mean
values of GBW, DC gain, phase margin, and offset are 1.376 MHz, 84.15 dB, 66.77◦, and
0.036 mV, respectively. The standard deviations are 0.18 MHz, 1.133 dB, 4.203◦, and
1.094 mV, respectively. The proposed ERFC OTA maintains stable performance even in
subthreshold regions.
(a) GBW
(b) DC gain
Figure 13. Cont.
```

---

## p.16

![p.16](pages/p16.png)

![p.16 내장 이미지 1](images/p16_1.png)

![p.16 내장 이미지 2](images/p16_2.png)

```text
Sensors 2025, 25, 2523
16 of 18
(c) Phase margin
(d) Offset
Figure 13. Two hundred-point Monte Carlo simulation.
The well-known figures of merit (FoMS and FoML) are used to quantitatively compare
OTA performance and evaluate the power efficiency of low and large signals, respectively.
They can be expressed as follows [23]:
FoMS = GBW · CL
Isupply
(25)
FoML = SR · CL
Isupply
(26)
The comparison with prior works is shown in Table 4. The proposed ERFC OTA
achieves a GBW of 1.37 MHz, surpassing the 1.12 MHz reported in [24] while consuming
less power. While its GBW is lower than [7,8], it consumes significantly less supply current.
The proposed OTA also demonstrates a slew rate of 19.32 V/µs at a current consumption
of 10.4 µA, outperforming [11,24]. Furthermore, the proposed ERFC OTA achieves FoMS
and FoML values of 9.22 and 130.04, respectively, which are substantially higher than those
of other works listed in Table 4, highlighting its superior power efficiency. It is particularly
suitable for applications that require less power while achieving a high performance, such
as portable devices and IoT systems.
Table 4. Comparison with prior arts.
Parameter
[7]
[8]
[11]
[12]
[24]
This Work
Supply voltage (V)
1.8
1.8
1
2
0.8
1.8
Technology (nm)
180
180
180
500
180
180
Supply current (µA)
344
800
50
50
45
10.4
Load (pF)
10
5.6
20
70
130
70
DC gain (dB)
72.7
60.9
92.3
72.7
102.7
84.18
GBW (MHz)
173.3
134.2
6.51
3.4
1.12
1.37
Phase margin (◦)
55
70.6
75.81
75.1
67.85
67.05
Slew rate (V/µs)
139.4
94.1
15.19
19.25
1.033
19.32
1% Settling time (ns)
9.2
10.2
79.5
110
555
473
Offset voltage (mV)
7.3
7.6
N/A
N/A
3.72
3.3
Noise 1 MHz (nV/
√
Hz)
48
N/A
N/A
23
68.8
31.9
FoMS (MHz·pF/µA)
5.03
0.94
2.604
4.76
3.326
9.22
FoML ((V/µs)·pF/µA)
4.07
0.66
6.07
26.95
2.98
130.04
Measured/simulated
Meas.
Sim.
Sim.
Meas.
Meas.
Sim.
```

---

## p.17

![p.17](pages/p17.png)

```text
Sensors 2025, 25, 2523
17 of 18
5. Conclusions
This work has presented innovative enhancements to the traditional RFC OTA, intro-
ducing the ABNLF technique, which effectively addresses the power consumption-versus-
transient response trade-off in amplifiers through nested local feedback and adaptive
biasing. Compared to conventional RFC OTA, it incurs only a 30% increase in power
consumption while boosting the SR and GBW by 120- and 5.95-fold, respectively. It is
poised to be an effective solution in low-power amplifier applications.
Author Contributions: The work presented in this paper was a collaboration betwene both authors.
Writing—original draft, validation, methodology, investigation and formal analysis, C.W. and P.C.;
formal analysis, writing—review and editing, and resources, J.L., J.X. and Z.L. All authors have read
and agreed to the published version of the manuscript.
Funding: This work was partially supported by the project “MultiSource Information Sensing
and AI Recognition Collaborative Innovation Platform for Intelligent Manufacturing Equipment
in the Fuzhou-Xiamen-Quanzhou National Independent Innovation Demonstration Zone”, Project
No. 2023FX0002.
Data Availability Statement: Data will be made available upon request.
Conflicts of Interest: The authors declare no conflicts of interest.
References
1.
Liu, J.; Li, S.; Guo, W.; Wen, G.; Sun, N. A 0.029-mm2 17-fJ/Conversion-Step Third-Order CT ∆Σ ADC with a Single OTA and
Second-Order Noise-Shaping SAR Quantizer. IEEE J. Solid-State Circuits 2019, 54, 428–440. [CrossRef]
2.
Kulej, T.; Khateb, F.; Kumngern, M. 0.5 V Multiple-Input Fully Differential Operational Transconductance Amplifier and Its
Application to a Fifth-Order Chebyshev Low-Pass Filter for Bio-Signal Processing. Sensors 2024, 24, 3013. [CrossRef] [PubMed]
3.
R˘aducan, C.; Gr˘ajdeanu, A.-T.; Plesa, C.-S.; Neag, M.; Negoi¸t˘a, A.; ¸Topa, M.D. LDO with Improved Common Gate Class-AB OTA
Handles any Load Capacitors and Provides Fast Response to Load Transients. IEEE Trans. Circuits Syst. I Regul. Pap. 2020, 67,
3740–3752. [CrossRef]
4.
Chen, J.; Sanchez-Sinencio, E.; Silva-Martinez, J. Frequency-dependent harmonic-distortion analysis of a linearized cross-coupled
CMOS OTA and its application to OTA-C filters. IEEE Trans. Circuits Syst. I Regul. Pap. 2006, 53, 499–510. [CrossRef]
5.
Zhang, X.; El-Masry, E.I. A Novel CMOS OTA Based on Body-Driven MOSFETs and its Applications in OTA-C Filters. IEEE Trans.
Circuits Syst. I Regul. Pap. 2007, 54, 1204–1212. [CrossRef]
6.
Chen, X.; Wang, K.; Liao, H.; Ma, S.; Ma, K. A Power-Efficient Linearized Open-Loop OTA Utilizing Reconfigurable Tail-Resistor
Pair. IEEE Trans. Circuits Syst. I Regul. Pap. 2023, 70, 2824–2828. [CrossRef]
7.
Akbari, M.; Hussein, S.M.; Hashim, Y.; Khateb, F.; Kulej, T.; Tang, K.-T. Implementation of a Multipath Fully Differential OTA in
0.18-µm CMOS Process. IEEE Trans. Very Large Scale Integr. (VLSI) Syst. 2023, 31, 147–151. [CrossRef]
8.
Anisheh, S.M.; Abbasizadeh, H.; Shamsi, H.; Dadkhah, C.; Lee, K.-Y. 98-dB Gain Class-AB OTA with 100 pF Load Capacitor in
180-nm Digital CMOS Process. IEEE Access 2019, 7, 17772–17779. [CrossRef]
9.
Li, X.; Hou, B.; Ju, C.; Wei, Q.; Zhou, B.; Zhang, R. A Complementary Recycling Operational Transconductance Amplifier with
Data-Driven Enhancement of Transconductance. Electronics 2019, 8, 1457. [CrossRef]
10.
Kim, J.; Song, S.; Roh, J. A High Slew-Rate Enhancement Class-AB Operational Transconductance Amplifier (OTA) for Switched-
Capacitor (SC) Applications. IEEE Access 2020, 8, 226167–226175. [CrossRef]
11.
Lv, X.; Zhao, X.; Wang, Y.; Wen, B. An improved non-linear current recycling folded cascode OTA with cascode self-biasing.
AEU—Int. J. Electron. Commun. 2019, 101, 182–191. [CrossRef]
12.
Garde, M.P.; Lopez-Martin, A.; Carvajal, R.G.; Ramírez-Angulo, J. Super Class-AB Recycling Folded Cascode OTA. IEEE J.
Solid-State Circuits 2018, 53, 2614–2623. [CrossRef]
13.
Assaad, R.S.; Silva-Martinez, J. The Recycling Folded Cascode: A General Enhancement of the Folded Cascode Amplifier. IEEE J.
Solid-State Circuits 2009, 44, 2535–2542. [CrossRef]
14.
Assaad, R.; Silva-Martinez, J. Enhancing general performance of folded cascode amplifier by recycling current. Electron. Lett 2007,
43, 1243–1244. [CrossRef]
15.
Li, Y.L.; Han, K.F.; Tan, X.; Yan, N.; Min, H. Transconductance enhancement method for operational transconductance amplifiers.
Electron. Lett 2010, 46, 1321–1323. [CrossRef]
```

---

## p.18

![p.18](pages/p18.png)

```text
Sensors 2025, 25, 2523
18 of 18
16.
Ahmed, M.; Shah, I.; Tang, F.; Bermak, A. An improved recycling folded cascode amplifier with gain boosting and phase margin
enhancement. In Proceedings of the 2015 IEEE International Symposium on Circuits and Systems (ISCAS), Lisbon, Portugal,
24–27 May 2015; pp. 2473–2476.
17.
Zhao, X.; Fang, H.; Xu, J. A transconductance enhanced recycling structure for folded cascode amplifier. Analog Integr. Circuits
Signal Process 2012, 72, 259–263. [CrossRef]
18.
Dabas, A.; Kumari, S.; Gupta, M.; Yadav, R. Design and Analysis of Class AB RFC OTA with Improved Performance. In
Proceedings of the 2022 8th International Conference on Signal Processing and Communication (ICSC), Noida, India, 1–3
December 2022; pp. 582–586.
19.
Yan, Z.; Mak, P.-I.; Martins, R.P. Double recycling technique for folded-cascode OTA. Analog Integr. Circuits Signal Process 2012, 71,
137–141. [CrossRef]
20.
Yavari, M.; Moosazadeh, T. A single-stage operational amplifier with enhanced transconductance and slew rate for switched-
capacitor circuits. Analog Integr. Circuits Signal Process 2014, 79, 589–598. [CrossRef]
21.
Ramirez-Angulo, J.; Holmes, M. Simple technique using local CMFB to enhance slew rate and bandwidth of one-stage CMOS
op-amps. Electron. Lett 2002, 38, 1409–1411. [CrossRef]
22.
Zhao, X.; Wang, Y.; Dong, L. Super current recycling folded cascode amplifier with ultra-high current efficiency. Integration 2018,
62, 322–328. [CrossRef]
23.
Algueta-Miguel, J.M.; Lopez-Martin, A.; Garde, M.P.; De La Cruz, C.A.; Ramirez-Angulo, J. ±0.5 V 15 µW Recycling Folded
Cascode Amplifier with 34767 MHz·pF/mA FOM. IEEE Solid-State Circuits Lett. 2018, 1, 170–1731. [CrossRef]
24.
Wang, Y.; Zhang, Q.; Yu, S.S.; Zhao, X.; Trinh, H.; Shi, P. A Robust Local Positive Feedback Based Performance Enhancement
Strategy for Non-Recycling Folded Cascode OTA. IEEE Trans. Circuits Syst. I Regul. Pap 2020, 67, 2897–2908. [CrossRef]
Disclaimer/Publisher’s Note: The statements, opinions and data contained in all publications are solely those of the individual
author(s) and contributor(s) and not of MDPI and/or the editor(s). MDPI and/or the editor(s) disclaim responsibility for any injury to
people or property resulting from any ideas, methods, instructions or products referred to in the content.
```
