# P. J. I. Matibag, Design and test of a CMOS folded cascode OTA with current recycling (UPC Master Thesis, 2024)

- 원본 PDF: `C:\Users\HSLEE\Documents\Todoc\fpga\wt\_heldout\upc_rfc.pdf` (논문모음·Gm_over_Id 두 폴더에 같은 원문 없음, 2026-10-14 확인)
- 사본: `source.pdf` (sha256 `8fe378cebc9a7482c1f1d93d9707073c9e242e04351e5533d9387ea699d92b7b`)
- 웹 출처: https://upcommons.upc.edu/bitstreams/a99028f7-5d7f-447a-b086-c1f4effcdb1b/download (UPC upcommons 석사논문 공개본, 지도 J. Cosp Vilella)
- 그림·표 위치: 쪽 번호 = PDF 쪽 = 인쇄 쪽 · p.22 Figure 5(코어 구조, 접점 점·hop 표기) · p.27 Table 2(치수) · p.28 Figure 6(치수 부기 코어 17 MOS) · p.32 Figure 8(wide-swing constant-gm 바이어스, 원 출처 Johns&Martin) · p.34 Figure 9(치수 부기 바이어스 18 MOS + RB) · p.37 Figure 11(부하 CL)
- 엔진 연결: `assets/heldout/rfc_ota.topology.json`, `rfc_ota.sizing_spec.json`, `rfc_ota.spec_source.md`, `rfc_ota.topology.md`
- 쪽 수: 85
- 변환: PyMuPDF 텍스트 추출(쪽 단위). 수식·표·그림은 텍스트가 깨질 수 있으니 같은 쪽의 렌더 PNG(`pages/`)로 확인할 것.

---

## p.1

![p.1](pages/p01.png)

![p.1 내장 이미지 1](images/p01_1.png)

![p.1 내장 이미지 2](images/p01_2.png)

```text
Design and test of a CMOS folded cascode
OTA with current recycling
Master Thesis
submitted to the Faculty of the
Escola T`ecnica d’Enginyeria de Telecomunicaci´o de Barcelona
Universitat Polit`ecnica de Catalunya
by
Prince Jay Ilagan Matibag
In partial fulfillment
of the requirements for the master in
ELECTRONIC ENGINEERING
Advisor: Jordi Cosp Vilella
Barcelona, 2024
```

---

## p.2

![p.2](pages/p02.png)

![p.2 내장 이미지 1](images/p02_1.png)

![p.2 내장 이미지 2](images/p02_2.png)

```text
Contents
List of Figures
4
List of Tables
5
Acronyms
7
Abstract
9
1
Introduction
10
1.1
Methodology and procedures . . . . . . . . . . . . . . . . . . . . . . . . . .
10
1.2
Scope of work . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . .
11
1.3
Work requirements and specifications . . . . . . . . . . . . . . . . . . . . .
11
1.3.1
Requirements . . . . . . . . . . . . . . . . . . . . . . . . . . . . . .
11
1.3.2
Specifications . . . . . . . . . . . . . . . . . . . . . . . . . . . . . .
11
1.4
Gantt Diagram . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . .
11
2
Conventional Folded Cascode
14
2.1
Structure
. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . .
14
2.2
Characteristics
. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . .
15
2.3
Sizing
. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . .
16
3
Current Recycling Folded Cascode
22
3.1
Structure
. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . .
22
3.2
Characteristics
. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . .
23
3.3
Comparison against Conventional Folded Cascode . . . . . . . . . . . . . .
24
3.4
Sizing
. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . .
25
4
Biasing
30
4.1
Circuit . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . .
30
4.2
Sizing
. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . .
33
5
Pre Layout Simulations
35
5.1
Open Loop Gain
. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . .
36
5.2
Bandwidth . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . .
38
5.3
Phase Margin . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . .
39
5.4
DC Offset Voltage . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . .
41
5.5
Common Mode Rejection Ratio (CMRR) . . . . . . . . . . . . . . . . . . .
41
5.6
Power Supply Rejection Ratio (PSRR) . . . . . . . . . . . . . . . . . . . .
43
5.7
Input Common Mode Range (ICMR) . . . . . . . . . . . . . . . . . . . . .
46
5.8
Slew Rate . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . .
47
5.9
Settling time
. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . .
49
5.10 Linearity . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . .
51
5.11 Noise . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . .
53
5.12 Comparison and simulation conclusion
. . . . . . . . . . . . . . . . . . . .
54
2
```

---

## p.3

![p.3](pages/p03.png)

![p.3 내장 이미지 1](images/p03_1.png)

![p.3 내장 이미지 2](images/p03_2.png)

```text
6
Layout
57
6.1
Layout criteria
. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . .
57
6.2
Amplifier . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . .
58
6.3
Biasing circuit . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . .
64
6.4
Design Rules Check (DRC)
. . . . . . . . . . . . . . . . . . . . . . . . . .
67
6.5
Layout vs Schematic (LVS)
. . . . . . . . . . . . . . . . . . . . . . . . . .
67
6.6
Parasitic Extraction (PEX)
. . . . . . . . . . . . . . . . . . . . . . . . . .
67
7
Post Layout Simulations
70
7.1
Open Loop Gain
. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . .
70
7.2
Bandwidth . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . .
70
7.3
Phase Margin . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . .
71
7.4
DC Offset Voltage . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . .
72
7.5
Common Mode Rejection Ratio (CMRR) . . . . . . . . . . . . . . . . . . .
73
7.6
Power Supply Rejection Ratio (PSRR) . . . . . . . . . . . . . . . . . . . .
74
7.7
Input Common Mode Range (ICMR) . . . . . . . . . . . . . . . . . . . . .
75
7.8
Slew Rate . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . .
75
7.9
Settling Time . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . .
77
7.10 Linearity . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . .
78
7.11 Noise . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . .
79
7.12 Discrepances against Pre Layout Simulations . . . . . . . . . . . . . . . . .
80
8
Economic Study
82
9
Conclusions and future development
83
3
```

---

## p.4

![p.4](pages/p04.png)

![p.4 내장 이미지 1](images/p04_1.png)

![p.4 내장 이미지 2](images/p04_2.png)

```text
List of Figures
1
Initial Gantt diagram of the project . . . . . . . . . . . . . . . . . . . . . .
12
2
Final Gantt diagram of the project . . . . . . . . . . . . . . . . . . . . . .
12
3
Conventional Folded Cascode Structure . . . . . . . . . . . . . . . . . . . .
14
4
Conventional Folded Cascode Schematic with computed dimensions . . . .
21
5
Recycling Folded Cascode Structure . . . . . . . . . . . . . . . . . . . . . .
22
6
Recycling Folded Cascode Schematic with computed dimensions . . . . . .
28
7
Stable transconductance biasing circuit . . . . . . . . . . . . . . . . . . . .
31
8
Wide-Swing Constant-Transconductance Bias Circuit . . . . . . . . . . . .
32
9
Biasing circuit schematic
. . . . . . . . . . . . . . . . . . . . . . . . . . .
34
10
Circuit for Open-Loop Frequency Response . . . . . . . . . . . . . . . . . .
36
11
AC Response simulation circuit . . . . . . . . . . . . . . . . . . . . . . . .
37
12
AC Response simulation results . . . . . . . . . . . . . . . . . . . . . . . .
37
13
Complete AC Response for Margin calculations
. . . . . . . . . . . . . . .
40
14
Schematic for measuring the DC Offset Voltage
. . . . . . . . . . . . . . .
41
15
Circuit for Common-Mode Rejection Ratio . . . . . . . . . . . . . . . . . .
42
16
Schematic for CMRR simulation . . . . . . . . . . . . . . . . . . . . . . . .
43
17
Result for CMRR simulation . . . . . . . . . . . . . . . . . . . . . . . . . .
43
18
Circuit for Power Supply Rejection Ratio . . . . . . . . . . . . . . . . . . .
44
19
Schematic for Power Supply Rejection Ratio simulation . . . . . . . . . . .
44
20
Result of PSRR+ simulation . . . . . . . . . . . . . . . . . . . . . . . . . .
45
21
Result of PSRR- simulation
. . . . . . . . . . . . . . . . . . . . . . . . . .
45
22
Circuit for Input Common Mode Range . . . . . . . . . . . . . . . . . . . .
46
23
Schematic for Input Common Mode Range . . . . . . . . . . . . . . . . . .
47
24
Results for the pre layout Input Common Mode Range . . . . . . . . . . .
47
25
Circuit for transient simulations . . . . . . . . . . . . . . . . . . . . . . . .
48
26
Transient response
. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . .
48
27
Slew Rate visual check . . . . . . . . . . . . . . . . . . . . . . . . . . . . .
49
28
Settling time markers . . . . . . . . . . . . . . . . . . . . . . . . . . . . . .
50
29
Close look at the overshoot . . . . . . . . . . . . . . . . . . . . . . . . . . .
51
30
Schematic for linearity simulations
. . . . . . . . . . . . . . . . . . . . . .
52
31
DFT result for Conventional Structure . . . . . . . . . . . . . . . . . . . .
53
32
DFT result for Recycling Structure . . . . . . . . . . . . . . . . . . . . . .
53
33
Output Referred noise curve for Conventional Structure . . . . . . . . . . .
54
34
Interdigitated MOS transistors example . . . . . . . . . . . . . . . . . . . .
58
35
Layout of input transistors . . . . . . . . . . . . . . . . . . . . . . . . . . .
59
36
Layout of current mirror . . . . . . . . . . . . . . . . . . . . . . . . . . . .
60
37
Layout of transistors M11 and M12 . . . . . . . . . . . . . . . . . . . . . .
61
38
Layout of transistors M5 and M6
. . . . . . . . . . . . . . . . . . . . . . .
62
39
Layout of transistors M7 and M8
. . . . . . . . . . . . . . . . . . . . . . .
62
40
Layout of transistors M9 and M10 . . . . . . . . . . . . . . . . . . . . . . .
63
41
Layout of transistors M0 . . . . . . . . . . . . . . . . . . . . . . . . . . . .
64
42
Layout of transistors Q7, Q9 and Q11 . . . . . . . . . . . . . . . . . . . . .
65
43
Layout of transistors Q5 and Q12 . . . . . . . . . . . . . . . . . . . . . . .
65
44
Layout of transistors Q15 and Q16
. . . . . . . . . . . . . . . . . . . . . .
66
4
```

---

## p.5

![p.5](pages/p05.png)

![p.5 내장 이미지 1](images/p05_1.png)

![p.5 내장 이미지 2](images/p05_2.png)

```text
45
Complete Layout . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . .
66
46
DRC Results
. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . .
67
47
LVS Results . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . .
67
48
Parasitics
. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . .
68
49
Calibre File with amplified view of the resistor fix . . . . . . . . . . . . . .
69
50
Post Layout Gain Simulation
. . . . . . . . . . . . . . . . . . . . . . . . .
70
51
Post Layout complete frequency response . . . . . . . . . . . . . . . . . . .
72
52
Post Layout CMRR Simulation . . . . . . . . . . . . . . . . . . . . . . . .
73
53
Post Layout PSRR+ . . . . . . . . . . . . . . . . . . . . . . . . . . . . . .
74
54
Post Layout PSRR- . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . .
74
55
Post layout ICMR
. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . .
75
56
Post layout transient response . . . . . . . . . . . . . . . . . . . . . . . . .
76
57
Post layout Slew Rate visual check
. . . . . . . . . . . . . . . . . . . . . .
76
58
Post Layout settling time markers . . . . . . . . . . . . . . . . . . . . . . .
77
59
Post Layout close look at the overshoot . . . . . . . . . . . . . . . . . . . .
78
60
DFT Results for Post Layout Recycling Folded Cascode . . . . . . . . . . .
79
61
Post Layout Input Referred Noise curve . . . . . . . . . . . . . . . . . . . .
79
List of Tables
1
Sizing of the transistors in the Conventional Folded Cascode . . . . . . . .
20
2
Sizing of the transistors in the Recycling Folded Cascode . . . . . . . . . .
27
3
Sizing comparison . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . .
29
4
First iteration of simulations . . . . . . . . . . . . . . . . . . . . . . . . . .
35
5
Open Loop Gain values for the pre layout simulations . . . . . . . . . . . .
37
6
Bandwidth values for the pre layout simulations . . . . . . . . . . . . . . .
38
7
GBW values for the pre layout simulations . . . . . . . . . . . . . . . . . .
39
8
Phase Margin for the pre layout simulations . . . . . . . . . . . . . . . . .
40
9
DC Offset Voltage for the pre layout simulations . . . . . . . . . . . . . . .
41
10
CMRR for the pre layout simulations . . . . . . . . . . . . . . . . . . . . .
42
11
PSRR for the pre layout simulations
. . . . . . . . . . . . . . . . . . . . .
46
12
ICMR for the pre layout simulations
. . . . . . . . . . . . . . . . . . . . .
47
13
Slew Rate for the pre layout simulations
. . . . . . . . . . . . . . . . . . .
49
14
Settling time and overshoot for the pre layout simulations
. . . . . . . . .
50
15
HD2 and HD3 results for the pre layout simulations . . . . . . . . . . . . .
52
16
Noise for the pre layout simulations . . . . . . . . . . . . . . . . . . . . . .
54
17
Characterization comparison between Conventional and Recycling structures 56
18
Open Loop Gain values for the post layout simulations . . . . . . . . . . .
70
19
Bandwidth values for the post layout simulations
. . . . . . . . . . . . . .
71
20
GBW values for the post layout simulations
. . . . . . . . . . . . . . . . .
71
21
Phase Margin for the post layout simulations . . . . . . . . . . . . . . . . .
71
22
DC Offset Voltage for the post layout simulations . . . . . . . . . . . . . .
73
23
CMRR for the post layout simulations
. . . . . . . . . . . . . . . . . . . .
73
24
PSRR for the post layout simulations . . . . . . . . . . . . . . . . . . . . .
75
25
ICMR for the post layout simulations . . . . . . . . . . . . . . . . . . . . .
75
5
```

---

## p.6

![p.6](pages/p06.png)

![p.6 내장 이미지 1](images/p06_1.png)

![p.6 내장 이미지 2](images/p06_2.png)

```text
26
Slew Rate for the post layout simulations . . . . . . . . . . . . . . . . . . .
77
27
Settling time and overshoot for the post layout simulations . . . . . . . . .
77
28
HD2 and HD3 results for the post layout simulations
. . . . . . . . . . . .
78
29
Noise for the post layout simulations
. . . . . . . . . . . . . . . . . . . . .
80
30
Pre Layout and Post Layout Characterization comparison
. . . . . . . . .
81
31
Economic Study . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . .
82
6
```

---

## p.7

![p.7](pages/p07.png)

![p.7 내장 이미지 1](images/p07_1.png)

![p.7 내장 이미지 2](images/p07_2.png)

```text
Acronyms
AC Alternating Current
CMOS Complementary Metal-Oxide-Semiconductor
CMRR Common-Mode Rejection Ratio
DC Direct Current
DFT Discrete Fourier Transform
DRC Design Rules Check
GBW Gain Bandwidth Product
HD Harmonic Distortion
ICMR Input Common Mode Range
LVS Layout vs Schematic
MOS Metal-Oxide-Semiconductor
NMOS N-Channel Metal-Oxide-Semiconductor
OTA Operational Transconductance Amplifier
PDK Process Design Kit
PEX Parasitic Extraction
PMOS P-Channel Metal-Oxide-Semiconductor
PN P-Type and N-Type
PSRR Power Supply Rejection Ratio
RMS Root-Mean-Square
RVE Results Viewing Environment
VAT Value-Added Tax
VPN Virtual Private Network
7
```

---

## p.8

![p.8](pages/p08.png)

![p.8 내장 이미지 1](images/p08_1.png)

![p.8 내장 이미지 2](images/p08_2.png)

```text
Revision history and approval record
Revision
Date
Purpose
0
06/12/2023
Document creation
1
07/01/2024
First document revision
2
12/01/2024
Second document revision
3
26/01/2024
Third document revision
4
29/01/2024
Final document
DOCUMENT DISTRIBUTION LIST
Name
e-mail
Prince Jay Ilagan Matibag
Jordi Cosp Vilella
Written by:
Reviewed and approved by:
Date
28/01/2024
Date
29/01/2024
Name
Prince Jay Ilagan Matibag
Name
Jordi Cosp Vilella
Position
Project Author
Position
Project Supervisor
8
```

---

## p.9

![p.9](pages/p09.png)

![p.9 내장 이미지 1](images/p09_1.png)

![p.9 내장 이미지 2](images/p09_2.png)

```text
Abstract
This thesis covers the design of a Complementary Metal-Oxide-Semiconductor (CMOS)
folded Cascode Operational Transconductance Amplifier (OTA) in UMC 180nm technol-
ogy. The broad use of operational transconductance amplifiers in the industry requires
them to be highly efficient to improve the operation of the circuits they are included in.
A technique called current recycling is known to improve the power efficiency of
the amplifier with a minimal complication of the circuit. This thesis covers the standard
implementation of the folded cascode amplifier and the current recycling folded cascode
and simulations to compare them in terms of performance, checking both pros and cons
of both implementations. Layout and Post Layout simulations of the current recycling
folded cascode amplifier will also be carried out.
Furthermore, a biasing circuit has also been included in both designs, which will pro-
vide the bias voltage without the need of extra sources other than VDD. The implemented
design of the biasing circuit is a design that it is insensitive to power source fluctuations
based on a stable transconductance matched to the conductance of a resistor.
9
```

---

## p.10

![p.10](pages/p10.png)

![p.10 내장 이미지 1](images/p10_1.png)

![p.10 내장 이미지 2](images/p10_2.png)

```text
1
Introduction
Operational Transconductance Amplifiers (OTA) is a common and widely used amplifying
device used in voltage or current mode devices. One of the most popular structures for
the OTA is a folded cascode structure, that is widely chosen because of the high output
impedace, low noise characteristic and wide output swing.
The continuous integration of complex analog and digital building blocks on a single
chip make silicon area and power consumption two very valued aspects when designing
integrated circuits. Even having all those previous pros and despite being one of the most
important blocks in Analog Design and vital in many applications, in the mobile and
portable industry the OTA is still the largest component and also the block that usually
has the largest power consumption, which limits the usage of this device in this field [1].
Different approaches have been attempted to reduce both size and power consump-
tion, but in this thesis, the one presented is Current Recycling [3]. Previous work tried
multi-path schemes [11] to enhance output impedance and slew rate, nonetheless, the
main drawback of that approach is that it made the OTA not suitable for high speed
applications due to the low frequency pole-zero pairs[3].
Current recycling theoretical study shows that with similar area and same power
budget it can boost the gain and slew-rate without adversely affecting the input referred
noise and the input offset [3] . This thesis goes through different checks to verify the
performance boost and improvements and the adverse effects of using this structure is
minimal and it is a structure worth to consider when designing an OTA.
1.1
Methodology and procedures
For the development of this thesis, both Conventional and Recycling current structure
are compared. Both amplifiers are designed in schematics level in Cadence Virtuoso and
then, the physical design verification is done through Calibre.
Theoretical simulations are performed for both structures and then compared to see
which structure has better performance and also to verify and check any limitations on
the proposed Recycling structure. Other parameters are also checked to verify that no
other performance metric is affected adversely.
Layout is performed on the Current Recycling structure. Post Layout simulations
are also performed to check and get a closer performance simulation of the physical block
of the design.
10
```

---

## p.11

![p.11](pages/p11.png)

![p.11 내장 이미지 1](images/p11_1.png)

![p.11 내장 이미지 2](images/p11_2.png)

```text
1.2
Scope of work
Due to time limitation constrains, this work does not include the tape-out of the chip and
the experimental verification of the design.
This work focuses on the implementation and the layout and the simulations from
Cadence Virtuoso.
1.3
Work requirements and specifications
The following requirements and specifications are considered for the development of this
thesis:
1.3.1
Requirements
1. Recycling Folded Cascode Gain Bandwidth Product (GBW): 150MHz.
2. Capacitive load (CL): 2.25pF
3. For a fair comparison in the performance, both amplifiers must have similar cur-
rent consumption to demonstrate that, with the same current consumption, the
performance of the Recycling structure is better than the Conventional structure.
1.3.2
Specifications
1. Supply voltage: 1.8V
2. Use same test bench for comparison
3. Use the same biasing circuit to generate the bias voltage of both circuits
1.4
Gantt Diagram
The timing of this thesis is divided in two big blocks: schematic and layout. Besides these
two blocks, an initial part of the project was to get familiar with the setup, specially
with the physical validation in Calibre. The initial project timing was projected to be as
follows:
11
```

---

## p.12

![p.12](pages/p12.png)

![p.12 내장 이미지 1](images/p12_1.png)

![p.12 내장 이미지 2](images/p12_2.png)

```text
Phases of the Project
2023
2024
SW Introduction
0% complete
Inverter schematic
0% complete
Inverter Layout
Schematic
0% complete
Conventional
0% complete
Recycling
0% complete
Simulations
Layout
0% complete
Layout
0% complete
Simulations
Figure 1: Initial Gantt diagram of the project
The final timing of the project is as follows:
Phases of the Project
2023
2024
SW Introduction
100% complete
Inverter schematic
100% complete
Inverter Layout
Schematic
100% complete
Conventional
100% complete
Recycling
100% complete
Biasing
100% complete
Simulations
Layout
100% complete
Layout
100% complete
Simulations
Figure 2: Final Gantt diagram of the project
The differences in the Gantt diagrams are briefly explained:
1. Longer time in schematic design:
1.1 Delay due to biasing circuit. The initial design of the amplifiers did not include
a biasing circuit, the biasing of the amplifiers was implemented using other
12
```

---

## p.13

![p.13](pages/p13.png)

![p.13 내장 이미지 1](images/p13_1.png)

![p.13 내장 이미지 2](images/p13_2.png)

```text
methodologies that required external current sources. During the development
of the thesis, it was decided that a biasing circuit should be included to avoid
the usage of extra external sources other than VDD in case of implementing
on a chip. Furthermore, a biasing circuit that is insensitive to power source
fluctuations and has a constant transconductance is selected, for a more stable
system against external variations.
1.2 Delay in the sizing of the amplifiers. From initial simulations, the Recycling
Folded Cascode did not reach enough Phase Margin to consider the system
stable, which lead to iterations in the sizing and the capacitance value. More
detailed explanation in section 5.
2. Delay in layout
2.1 There was a delay in the layout due to Parasitic Extraction (PEX) not working
correctly. This lead to multiple tests and debugging to try to find the error and
also reinstallation of Cadence configuration.
2.2 Layout iteration. Initial proposed layout for the input transistors used a common-
centroid scheme in a 4x4 shape. This made the common-centroid to be in the
middle and all the transistors had the same distance to the center. Nonetheless,
the main drawback of that design is in terms of sizing. The input transistors
are the wider, and having them in a 4x4 shape, made the layout larger because
of the space that the rows in the 4x4 structure needed in between to allow
interconnection. By changing to a 16x1 structure and applying interdigitation
a more compact solution is achieved. Furthermore, given that interdigitation is
applied, this does not affect negatively the matching between transistors, since
the common-centroid structure is mantained.
13
```

---

## p.14

![p.14](pages/p14.png)

![p.14 내장 이미지 1](images/p14_1.png)

![p.14 내장 이미지 2](images/p14_2.png)

![p.14 내장 이미지 3](images/p14_3.png)

```text
2
Conventional Folded Cascode
2.1
Structure
The structure of the conventional Folded Cascode OTA is depicted in Figure 3. This
amplifier is widely used because of its high gain and large signal swing. The most common
structure is composed by P-Channel Metal-Oxide-Semiconductor (PMOS) input, given
that it provides a higher non-dominant pole, lower flicker noise and input common mode
level[16].
Figure 3: Conventional Folded Cascode Structure [3]
Despite the previous presented advantages and being one of the most used blocks
in analog design, one of the drawbacks of this design is the inefficiency in transistors M3
and M4. Circuit analysis shows that these two transistors are the transistors that conduct
the highest current in the circuit, thus, in the majority of designs are the transistors
with highest transconductance. This is highly inefficient if the role of these transistors is
considered: both transistors are only used to provide a folding node for the small signal
current generated by the input transistors.
The amplifier is a single stage with differential input and single ended-output. The
input transistors are formed by M1 and M2. To the drain of transistors M3 and M4 there
are also connected the cascode transistors M5 and M6 and, to do the differential-to-
single-ended conversion, transistors M7 to M10 are implementing a wide-swing current
mirror [9].
14
```

---

## p.15

![p.15](pages/p15.png)

![p.15 내장 이미지 1](images/p15_1.png)

![p.15 내장 이미지 2](images/p15_2.png)

```text
What makes this structure one of the most widely used is that with the size and
the simplicity of a single-stage amplifier it can reach the performance of a multi-stage
amplifier because of the usage of cascode structures in the output stage, which make the
output impedance high.
The biasing circuit specified in section 4 generates the biasing voltages in figure 3.
2.2
Characteristics
All the transistors shown in the circuit and in all the following sections are working in
saturation region and the simplified square-law drain current model is used to compute
an initial approximation and to develop and show the characteristics of the amplifier.
ID = 1
2 · µ · Cox · W
L · (VGS −VT)2
(1)
The main characteristics that are looked into this section for further comparison
are the transconductance, the gain and the slew rate, since these parameters are easily
obtained and give a good overview of the amplifier performance.
Regarding the transconductance of the amplifier (GmFC) it is fixed by the transcon-
ductance of the input transistor (gm1), thus:
GmFC = gm1
(2)
For the gain (AvF C), the expression is:
AvF C = GmFC · RoutF C
(3)
Where GmFC is the transconductance of the amplifier and RoutF C is the output
impedance of the amplifier.
By analysing the circuit, the output impedance considering the parasitic resistors of
the active load is expressed as:
RoutF C = gm6 · rds6 · (rds2||rds4)||gm8 · rds8 · rds10
(4)
15
```

---

## p.16

![p.16](pages/p16.png)

![p.16 내장 이미지 1](images/p16_1.png)

![p.16 내장 이미지 2](images/p16_2.png)

```text
Where gmi is the transconductance of transistor i and rdsi is the drain-source resistor
of transistor i.
Therefore, by substituting in the gain expression, the resulting formula for the gain
is:
Av = gm1 · gm6 · rds6 · (rds2||rds4)||gm8 · rds8 · rds10
(5)
The expression for the slew rate (SR) is given by:
SR = 2 · Ib
CL
(6)
In that expression two factors take into account: the maximum current that flows
through the loads (2 · Ib, where Ib is the current defined in figure 3) and the capacitive
load (CL).
2.3
Sizing
For the sizing of this amplifier, a first approximation is performed to obtain the first
Width and Length ratios. The followed steps to obtain this initial approximation are:
1. Obtain the transconductance for the input transistors
The transconductance of the input transistors (gm1) are obtained with the Gain-
Bandwidth product (GBW) and the load capacitance (CL). From the specifications
of the thesis, the Recycling Folded Cascode GBW has to be 150MHz. From [3], the
GBW of the Recycling structure is twice as large as the conventional. Thus, for the
sizing of the conventional a GBW of 100MHz is used, to have some margin due to
the usage of the square-law drain current model and further approximations in the
sizing. The CL value is also fixed from the specifications and it is 2.25pF.
This value is an approximation of what ideally the transistor should have if all the
components are ideal. The expression used is:
gm1 = 2 · π · CL · GBW
(7)
16
```

---

## p.17

![p.17](pages/p17.png)

![p.17 내장 이미지 1](images/p17_1.png)

![p.17 내장 이미지 2](images/p17_2.png)

```text
2. Obtain the W
L ratio for the input transistors
With the previously obtained transconductance, calculate the sizing ratio required
for the input transistors:
gm1 = KP · W
L · (VGS −VT)
(8)
W
L =
gm
KP · (VGS −VT)
(9)
Where KP is KP = µp · Cox and (VGS −VT) is the overdrive voltage, that is defined
by the gate-source voltage minus the threshold voltage.
3. Fix an overdrive voltage
As seen in the expression there is a parameter that is unknown and it is a degree
of freedom in the design, which is the overdrive voltage (VGS −VT). For the initial
approximation a value of 150mV is selected for all transistors. This value is the
mean value from two different methodologies to fix the overdrive voltage. The first
methodology is to fix an overdrive voltage of 200mV [13], and the other methodology
is to use the 20% of VDD[4].
For the value of KP, a first approximation was done by simulations. The value used
for the calculations is 63 µA/V 2.
4. Fix the length of the input transistors
To reduce the channel modulation effects, the length of most of the transistors is
3·MinimumLength. In this case, the selected value of length for the input transistors
is 540nm, given that the minimum length for this technology is 180nm.
5. Compute the Width of the input transistors
With the aspect ratio and the length that is fixed in the previous step, the width of
the input transistors are obtained.
17
```

---

## p.18

![p.18](pages/p18.png)

![p.18 내장 이미지 1](images/p18_1.png)

![p.18 내장 이미지 2](images/p18_2.png)

```text
6. Calculate the current through input transistors
With the width and length values fixed and using the simplified square-law drain
current model:
ID = 1
2 · KP · W
L · (VGS −VT)2
(10)
7. Calculate the current passing through all the other transistors
When the current passing through the input transistor is known, from the schematic
in figure 3, all the currents flowing through the different transistors in the circuit
are calculated.
8. Calculate the W
L for the rest of transistors
For the calculation of the size ratios of the transistors the simplified square-law
drain current model is used. The expressions that are given are for PMOS, for
NMOS transistors, instead of the previously obtained KP, an approximation of KN
is used. It was found using the same procedure and the value obtained was 280
µA/V 2 :
ID = 1
2 · KP · W
L · (VGS −VT)2
(11)
W
L =
2 · ID
KP · (VGS −VT)2
(12)
Analogous expression used for NMOS:
W
L =
2 · ID
KN · (VGS −VT)2
(13)
From previously given expression, the size ratio is obtained with the overdrive volt-
age specified and the approximation of KP and KN also given in previous steps.
18
```

---

## p.19

![p.19](pages/p19.png)

![p.19 내장 이미지 1](images/p19_1.png)

![p.19 내장 이미지 2](images/p19_2.png)

```text
9. Fix the Lengths of the transistors and obtain the Width
For all the transistors, the same criteria as the input transistors is followed: 3 ·
MinimumLength. The only exception in the design are transistors M9 and M10.
Both of these transistors, since are part of the active load and the source is connected
to VDD, the channel length modulation effect is reduced, so a smaller length is used
for these transistors, in this case only a length of 2 · MinimumLength is selected
for both transistors.
19
```

---

## p.20

![p.20](pages/p20.png)

![p.20 내장 이미지 1](images/p20_1.png)

![p.20 내장 이미지 2](images/p20_2.png)

```text
By following these steps, the resulting table summarizes the values obtained with
the approximations done:
Recycling Folded Cascode Sizing [µm]
M0
W
161.57
L
0.54
W/L
299.20
M1and M2
W
80.78
L
0.54
W/L
149.59
M3 and M4
W
36.36
L
0.54
W/L
67.32
M5 and M6
W
18.17
L
0.54
W/L
33.66
M7 and M8
W
80.78
L
0.54
W/L
149.59
M9 and M10
W
53.85
L
0.36
W/L
149.59
Table 1: Sizing of the transistors in the Conventional Folded Cascode
20
```

---

## p.21

![p.21](pages/p21.png)

![p.21 내장 이미지 1](images/p21_1.png)

![p.21 내장 이미지 2](images/p21_2.png)

![p.21 내장 이미지 3](images/p21_3.png)

```text
The resulting schematic is:
Figure 4: Conventional Folded Cascode Schematic with computed dimensions
21
```

---

## p.22

![p.22](pages/p22.png)

![p.22 내장 이미지 1](images/p22_1.png)

![p.22 내장 이미지 2](images/p22_2.png)

![p.22 내장 이미지 3](images/p22_3.png)

```text
3
Current Recycling Folded Cascode
3.1
Structure
The main structure of this amplifier is really similar to the structure of the Conventional
Folded Cascode, but with some modifications to address the main drawback that the
conventional structure has: the inefficiency of transistors M3 and M4.
The modifications performed are to make M3 and M4driving transistors. To do so,
the input transistors M1 and M2 are divided in half. With the circuit structure depicted
in figure 5, each of the half transistors drive half of the current that M1 and M2 were
driving in the Conventional structure.
Figure 5: Recycling Folded Cascode Structure [3]
Another modification done is to the transistors that are intended to be modified:
M3 and M4. These transistors are split into current mirrors with a ratio of K:1. When
the selected K is 3 (K = 3), as seen in the annotations in the circuits figure, the current
consumption is the same as in the Conventional Folded Cascode, so, for a fair comparison,
that value of K is selected. For another value of K, the load section must be resized to
maintain the power consumption[3].
Two additional transistors are added in the structure, which are connected in be-
tween the input transistors and the smaller size branch of the current mirrors. These
transistors are added to ensure that the small signal current added in the sources of M5
and M6 are in phase.
22
```

---

## p.23

![p.23](pages/p23.png)

![p.23 내장 이미지 1](images/p23_1.png)

![p.23 내장 이미지 2](images/p23_2.png)

```text
As observed, the circuit and structure modifications are relatively easy to perform
and as shown in next section, from theoretical analysis, are supposed to deliver a higher
performance.
3.2
Characteristics
The same characteristics as the Conventional Folded Cascode are analyzed: transconduc-
tace, gain and slew rate.
When it comes to the transconductace of the amplifier (GmRFC), the expression
obtained for this amplifier is:
GmRFC = gm1A · (1 + K)
(14)
Where gm1A is the transconductance of the input amplifier and the K is the design
parameter previously selected as K = 3.
Regarding the gain, the expression keeps being the same, the amplifier transcon-
ductance (GmRFC )multiplied with the output resistance (RoutRF C), however, due to the
changes mentioned, there are changes in the output resistance:
Av = GmRFC · RoutRF C
(15)
RoutRF C = gm6 · rds6 · (rds2a||rds4a)||gm8 · rds8 · rds10
(16)
Av = gm1A · (1 + K) · gm6 · rds6 · (rds2a||rds4a)||gm8 · rds8 · rds10
(17)
As in previous sections, gmi is the transconductance of transistor i and rdsi is the
drain-source resistor of transistor i.
As observed, the modifications in this expression is that instead of considering the
drain-source resistance of the input transistor (M2) and transistor M4, since both of
them have been split in half, only the resistance of half transistor is considered. In the
next section the effect of this slight change is discussed.
23
```

---

## p.24

![p.24](pages/p24.png)

![p.24 내장 이미지 1](images/p24_1.png)

![p.24 내장 이미지 2](images/p24_2.png)

```text
The slew rate in this case it is observed that in this structure, the current is higher
because it is multiplied by K, which leads to a higher Slew Rate:
SR = 2 · K · Ib
CL
(18)
3.3
Comparison against Conventional Folded Cascode
From previous sections, a comparison of the characteristics between the Conventional
Folded Cascode and the Recycling Folded Cascode is done.
For the transconductance of the amplifier, for the conventional structure the expres-
sion was:
GmFC = gm1
(19)
And for the Recycling Folded Cascode:
GmRFC = gm1a · (1 + K)
(20)
In the Conventional Folded Cascode, the input transistors are not split, thus, the
size is doubled. Since the rest of the parameters remain equal, the current that the input
transistors drive in the Conventional Folded Cascode is twice as large as in the Recycling,
which leads also to twice the transconductance in the input transistors: gm1 = 2 · gm1a
For the Recycling Folded Cascode, by substituting K, the expressions for the transcon-
ductance simplifies to:
GmRFC = gm1a · (1 + K) = 4 · gm1a
(21)
Then, the transconductance of the Conventional Folded Cascode expressed in terms
of gm1a :
GmFC = 2 · gm1a
(22)
24
```

---

## p.25

![p.25](pages/p25.png)

![p.25 내장 이미지 1](images/p25_1.png)

![p.25 내장 이미지 2](images/p25_2.png)

```text
From above expressions, it is seen that the transconductance of the Recycling struc-
ture is the double, which means with the same power consumption, the GBW of the
Recycling is twice as large as the Conventional (considering that CL is not changed):
GBW = 2 · π · CL · Gm
(23)
Another improvement that appears by changing to a Recycling structure is in the
gain. From the increased transconductance (2 times larger), there is already a 6dB im-
provement in the Gain. Nonetheless, in the output resistance there was a change, given
that another resistances need to be considered.
In the Recycling structure, half transistors are used to get the output resistance.
Since these half transistors are driving less current, the value of those parasitic resistors
increases, thus, increasing the overall output resistance.
From previous analysis, it was already observed that with the Recycling structure,
the Slew Rate was higher, because the maximum current flowing through the load is
higher.
Nonetheless, not all the parameters improve. With the changes in the structure, pole-
zero pairs are added, affecting the Phase Margin. Both structures share the dominant pole
in the output node, and also share the non-dominant pole due to the non-parasitics of the
source of M5 and M6.
In the Recycling structure, splitting M3 and M4 in current mirrors, generates a new
pole-zero pair. Because the devices that generate the pole-zero pair are NMOS, the pair is
located at high-frequency, but it is expected to worsen the Phase Margin in the Recycling
compared to the Conventional.
3.4
Sizing
Since a fair comparison must be done between both amplifiers, the sizing of the Recycling
structure is based on the sizing previously done for the Conventional Structure. The
modifications presented in the Structure section are applied to the sizing obtained in the
Conventional structure to obtain the sizing of the Recycling structure. The following list
of changes shows the difference compared to the Conventional Folded Cascoded:
1. Input transistors split in half
2. M3 and M4 split into a 3:1 current mirror structure
25
```

---

## p.26

![p.26](pages/p26.png)

![p.26 내장 이미지 1](images/p26_1.png)

![p.26 내장 이미지 2](images/p26_2.png)

```text
To size the current mirror transistors, for the branch that drives the smaller current,
the width is 1
4 of the width of transistors M3 and M4 in the Conventional Structure.
For the branch that drives more current, the ratio of K = 3 is used, thus, the width
is 3
4 of the width of transistors M3 and M4 in the Conventional Structure.
3. Newly added transistors M11 and M12
For the sizing of both of these transistors, the simplified square-law drain current
model is used. An alternative to calculate the sizing of these transistors is to use the
sizing of transistors M5 and M6. Given that the current flowing in M11 and M12 is
the half of the current that flows through M5 and M6, to have the same overdrive
voltage, the size must be the half.
26
```

---

## p.27

![p.27](pages/p27.png)

![p.27 내장 이미지 1](images/p27_1.png)

![p.27 내장 이미지 2](images/p27_2.png)

```text
The table summarizing the sizes of this amplifier is:
Recycling Folded Cascode Sizing [µm]
M0
W
161.57
L
0.54
W/L
299.20
M1a and M1b
W
40.39
L
0.54
W/L
74.80
M2a and M2b
W
40.39
L
0.54
W/L
74.80
M3a and M4a
W
27.24
L
0.54
W/L
50.4
M3b and M4b
W
9.09
L
0.54
W/L
16.83
M5 and M6
W
18.17
L
0.54
W/L
33.66
M7 and M8
W
80.78
L
0.54
W/L
149.59
M9 and M10
W
53.85
L
0.36
W/L
149.59
M11 and M12
W
9.09
L
0.54
W/L
16.83
Table 2: Sizing of the transistors in the Recycling Folded Cascode
27
```

---

## p.28

![p.28](pages/p28.png)

![p.28 내장 이미지 1](images/p28_1.png)

![p.28 내장 이미지 2](images/p28_2.png)

![p.28 내장 이미지 3](images/p28_3.png)

```text
The resulting schematic is:
Figure 6: Recycling Folded Cascode Schematic with computed dimensions
28
```

---

## p.29

![p.29](pages/p29.png)

![p.29 내장 이미지 1](images/p29_1.png)

![p.29 내장 이미지 2](images/p29_2.png)

```text
The comparison table between both designs is table 3. The gate area slightly in-
creases due to the addition of two transistors (M11 and M12) and the total area increases
too, because the transistors are split, nonetheless, the current consumption does not in-
crease. If the area is not a limitation, from theoretical comparison of both options, the
Recycling structure outperforms the Conventional structure.
Transistor
Conventional Structure [µm]
Recycling Structure [µm]
M0
W
161.57
161.57
L
0.54
0.54
W/L
299.20
299.20
M1 and M2
W
80.78
-
L
0.54
-
W/L
149.59
-
M1a and M1b
W
-
40.39
L
-
0.54
W/L
-
74.80
M2a and M2b
W
-
40.39
L
-
0.54
W/L
-
74.80
M3 and M4
W
36.36
-
L
0.54
-
W/L
67.32
-
M3a and M4a
W
-
27.24
L
-
0.54
W/L
-
50.4
M3b and M4b
W
-
9.09
L
-
0.54
W/L
-
16.83
M5 and M6
W
18.17
18.17
L
0.54
0.54
W/L
33.66
33.66
M7 and M8
W
80.78
80.78
L
0.54
0.54
W/L
149.59
149.59
M9 and M10
W
53.85
53.85
L
0.36
0.36
W/L
149.59
149.59
M11 and M12
W
-
9.09
L
-
0.54
W/L
-
16.83
Table 3: Sizing comparison
29
```

---

## p.30

![p.30](pages/p30.png)

![p.30 내장 이미지 1](images/p30_1.png)

![p.30 내장 이미지 2](images/p30_2.png)

```text
4
Biasing
4.1
Circuit
For the very initial phase of the project different biasing methods were used to bias
the transistors. The first methodology used was to use the ideal voltage source to set the
Direct Current (DC) Gate voltage. It is known that the real-life variations and fluctuations
in real sources make this option not ideal. Another tested implementation was to bias
the transistors in the circuit using current mirrors, but one of the disadvantages of this
implementation is that it requires multiple current sources, that can also have variations
and fluctuations. In the way it was implemented in the test bench it required multiple
current sources with different current output to properly generate the bias required for
the circuit, furthermore, in OTA circuits, the transconductance is really important since it
impacts the gain, bandwidth and other parameters[5], as also shown in previous sections.
With the objective to not have any other power source other than the VDD in the
circuit, the decision of implementing a biasing circuit in order to bias all the transistors
was taken.
As seen through the years and different projects and studies, one of the biggest
difficulties is to have a stable reference current. One of the techniques that is used to have
a stable current is to stabilize the transconductance by matching this parameter to the
conductance of a resistor. By doing this, not even the variations and fluctuations in VDD
can affect the transconductance of the biasing circuit, which is the main reason why this
biasing circuit is selected. This concept was firstly introduced by Steininger[14] and also
explained by Johns and Martin[9].
The result of this process is to have a transconductance that does not depend on
the power supply voltage or temperature fluctuations, making the transconductance pa-
rameter more robust against this type of changes and variations that are common in any
design or component.
Analyzing the circuit on figure 7, the following expression is obtained for the transcon-
ductance of transistor Q13:
30
```

---

## p.31

![p.31](pages/p31.png)

![p.31 내장 이미지 1](images/p31_1.png)

![p.31 내장 이미지 2](images/p31_2.png)

![p.31 내장 이미지 3](images/p31_3.png)

```text
Figure 7: Stable transconductance biasing circuit [9]
gm13 =
2 · [1 −
s
(W/L)13
(W/L)15
]
RB
As observed in the equation above, the transconductance only depends on the ratio
of size ratios of the two NMOS and the resistor, thus, for the particular case where the
ratio of sizes is (W/L)15 = 4 · (W/L)13, then the transconductance is:
gm13 =
1
RB
One of the main advantages of this structure is that not only one transistor is sta-
bilized, but all transistors in the biasing circuit. This is because the currents of all the
transistors are obtained from the same biasing network, so the currents and transconduc-
tances only depend on the geometry ratios. For the NMOS:
gmNMOS =
s
(W/L)NMOS · INMOS
(W/L)13 · I13
· gm13
And for the PMOS:
gmP MOS =
s
µp
µn
· (W/L)PMOS · IPMOS
(W/L)13 · I13
· gm13
31
```

---

## p.32

![p.32](pages/p32.png)

![p.32 내장 이미지 1](images/p32_1.png)

![p.32 내장 이미지 2](images/p32_2.png)

![p.32 내장 이미지 3](images/p32_3.png)

```text
The circuit shown in [9], the Wide-Swing Constant-Transconductance Bias Circuit,
is the biasing circuit used in this thesis. The circuit is based on the circuit from figure 7,
which ensures the stability of the transconductance. A start-up circuit and a cascode bias
are also added.
Figure 8: Wide-Swing Constant-Transconductance Bias Circuit [9]
One of the improvements of the circuit in figure 8 is the use of wide-swing current
mirrors. This improvement increases the output impedance of transistors, which was not
considered previously and affects negatively in the performance of the circuit in figure 7.
The cascode bias provides the gate voltage for the cascodes in the bias loop. This
circuit is composed by transistors Q10-Q13 and the diode-connected transistors Q5 and
Q14.
Another modification from the initial design is the addition of a start-up circuit.
There is not a unique stable state for this circuit. One of them is when the transcon-
ductance is stable and all currents and transconductances in the circuit are stable and
different from 0. But that is not the only possible stable state for this circuit. The other
stable state is when all currents in the biasing circuit are zero. In that case, the biasing
circuit does not generate any voltage, thus, the amplifier does not work either. This is
solved with the implementation of a start-up circuit.
The start-up circuit implemented in this design only takes effect when there is no
32
```

---

## p.33

![p.33](pages/p33.png)

![p.33 내장 이미지 1](images/p33_1.png)

![p.33 내장 이미지 2](images/p33_2.png)

```text
current flowing in the biasing loop. This is because the lower transistor (Q17) is off, so
the gates from the two transistors, Q15 and Q16 are turned ON and inject current into
the bias loop. By injecting this current, the stable state where the circuit was is broken
and the circuit switches to the other state, where the transconductance is stable. After
that current is injected, transistors Q14 and Q9 that were initially OFF, are turned ON
and transistors Q15 and Q16 turn OFF, so this circuit does not have any effect when the
design operates in the other stable state[9].
4.2
Sizing
From previous section, it is known that the transconductance of Q3 in the biasing circuit is
fixed by the resistor, so, since the Gate-Source voltage of this transistor biases transistors
M3 and M4 from the Conventional structure, the obtained transconductance in the sizing
section of the Conventional Cascode is used to define the resistor. The initial value for the
resistor was 353Ωsince the transconductance obtained for transistors M3 and M4 was
2.83mS.
With that resistor value, the transconductance is fixed, thus is the current. In order
to get the desired overdrive voltage for the transistors M3 and M4 in the amplifier, through
transistor Q3 in the biasing circuit it must drive the same current, so it must be sized
exactly the same as transistors M3 and M4 in the Conventional Structure. The size of Q2
in the biasing circuit is fixed to be 4 times larger, to ensure a constant transconductance
in Q3. For Q1 and Q4 a larger length is selected to get a larger drain-source voltage,
which helps to reduce a second-order effect due to body effect and to have slightly more
margin between the triode and active region [9].
For the sizing of transistors Q9 and Q7 in the biasing circuit, since they provide the
gate-source voltage of transistor M0 in the amplifier, they must drive the same current,
so the same size is applied to both of these transistors. For Q8 and Q6, the same criteria
as previously applied for transistors Q1 and Q4 is used.
This given design was functional, nonetheless, the current consumption was large
because it was using a ratio 1:1 with the circuit, so to reduce the current consumption,
the size of the transistors was decreased by 4, to the ratio now 1:4, reducing the current
consumption of the biasing circuit. But since the size of the transistors has changed, the
value of the resistor also needs to be changed to keep the proper biasing. In this case, since
the sizes of all transistors are divided by 4, the value of the resistor must be multiplied
by 4 to keep the ratio constant and keep the correct biasing into the circuit.
For the sizing of the Cascode Bias section in figure 8, the same sizes as the transistors
in the Bias loop are used, except for the diode-connected transistors Q5 and Q14, which
are set to be 4 times smaller.
33
```

---

## p.34

![p.34](pages/p34.png)

![p.34 내장 이미지 1](images/p34_1.png)

![p.34 내장 이미지 2](images/p34_2.png)

![p.34 내장 이미지 3](images/p34_3.png)

```text
For the sizing of the Start-up circuitry, the same size as Q3 is used for all transistors
except for Q18. For that transistor, a smaller size ratio is selected, as specified in figure 8.
The schematic of the biasing circuit is depicted in figure 9.
Figure 9: Biasing circuit schematic
34
```

---

## p.35

![p.35](pages/p35.png)

![p.35 내장 이미지 1](images/p35_1.png)

![p.35 내장 이미지 2](images/p35_2.png)

```text
5
Pre Layout Simulations
For the Pre Layout Simulations, both designs, the Conventional and the Recycling Folded
Cascodes are checked with the same conditions and same testbench and are compared to
see which one is better.
In the following subsections the circuit, the different constraints and conditions
applied for the simulations are presented.
The given results correspond to the final values in the simulations. For the initial
sizing, the aim was to obtain a GBW of 150MHz with a capacitance of 2.25pF for the
Recycling Structure. The sizing of the Conventional structure was done with a GBW of
100MHz and the same capacitive load, nonetheless, during the first iteration of simula-
tions, the following values were obtained:
Parameter
Conventional Structure
Recycling Structure
Bias Current (µA)
457.4
457.2
DC Gain (dB)
48.46
57.91
Bandwidth (kHz)
281.3
207.4
GBW (MHz)
74.82
154.1
Phase Margin (º)
80.88
57.33
Table 4: First iteration of simulations
It is observed that the GBW was reasonable, slightly above to the desired GBW
for the Recycling structure (150MHz). The GBW for the Conventional structure was not
reached (below 100MHz) because the value of KP was an approximation and not the
exact value. The value used for the sizing was slightly higher than the actual value, since
the overdrive voltages were checked and all of them were close to 150mV. Nonetheless,
the main issue observed is the Phase Margin obtained for the Recycling Structure, which
is below 60°, threshold selected to define the stability.
Two approaches were attempted to increase the phase margin: change the sizing of
the non-dominant pole to move it further or get the dominant pole closer to 0. By adjusting
the non-dominant pole, a stable solution was achieved, nonetheless, the overdrive voltage
was lower than the initial 150mV, so the other approach was preferred. The initial sizing
was maintained, but 500fF were added for a total of 2.75pF, to make the Recycling
structure stable. This limits the GBW and the 150MHz target is not achievable with the
increase in the capacitance, but makes the design stable.
35
```

---

## p.36

![p.36](pages/p36.png)

![p.36 내장 이미지 1](images/p36_1.png)

![p.36 내장 이미지 2](images/p36_2.png)

![p.36 내장 이미지 3](images/p36_3.png)

```text
5.1
Open Loop Gain
To compute the Open Loop Gain, the circuit depicted in figure 10 is used. The open-loop
frequency response is checked only with a capacitive load.
Figure 10: Circuit for Open-Loop Frequency Response[2]
The values of C and R have been set high enough thus they do not have any effect
on the simulations, just to obtain a more accurate result of the Alternating Current (AC)
simulation. In this case, the selected value for the capacitor was 10mF and for the feedback
resistor was 1GΩ.
The simulation is set to be an AC simulation between 1Hz to 100MHz.
The schematic with the values of the components is despicted in figure 11 and the
results for this simulation in figure 12, where the gain in decibels is depicted for both
amplifiers.
36
```

---

## p.37

![p.37](pages/p37.png)

![p.37 내장 이미지 1](images/p37_1.png)

![p.37 내장 이미지 2](images/p37_2.png)

![p.37 내장 이미지 3](images/p37_3.png)

![p.37 내장 이미지 4](images/p37_4.png)

```text
Figure 11: AC Response simulation circuit
Figure 12: AC Response simulation results
Open Loop Gain
Conventional Structure
48.46dB
Current Recycling Structure
57.91dB
Table 5: Open Loop Gain values for the pre layout simulations
37
```

---

## p.38

![p.38](pages/p38.png)

![p.38 내장 이미지 1](images/p38_1.png)

![p.38 내장 이미지 2](images/p38_2.png)

```text
Looking at the simulation results, it is concluded that the gain of the Recycling
Structure is 57.91dB and the Conventional Structure is measured at 48.46dB. As men-
tioned in previous sections and in the specifications of the thesis, for a fair comparison,
both amplifiers have a similar current consumption, as shown in table 17, so in this param-
eter it can be clearly stated that the Recycling outperforms the Conventional Structure.
The increase in the gain is, as mentioned also in the comparison between both structures,
higher than 6dB due to the increase in the transconductance. As mentioned, because of
the increase in the output resistance, a slightly higher gain increase is expected.
5.2
Bandwidth
To measure the Bandwidth of the amplifiers, the same circuit for the Open Loop Gain is
used and the same response is analyzed. To get the Bandwidth of the amplifiers the point
where the −3dB point is reached is used.
For a better precision in the bandwidth calculation, the calculator is used to get the
value using the bandwidth function. The expression used is the following:
bandwidth((VF(”output”) / VF(”input”)) 3 ”low”)
As seen in table 6, the bandwidth of the Conventional structure is higher than the
Current Recycling.
Bandwidth
Conventional Structure
233.9 kHz
Current Recycling Structure
173.2 kHz
Table 6: Bandwidth values for the pre layout simulations
Nonetheless, the parameter that actually shows the performance of the amplifier is
the GBW, which is calculated from the gain and the bandwidth obtained. In this case,
for a better accuracy, the calculator is used with the following expression:
unityGainFreq(VF(”output”) / VF(”input”))
The results obtained are shown in table 7. It is observed that with the same current
consumption, the current recycling is clearly outperforming the conventional structure by
having more than the double of GBW. Nonetheless, due to the increase of the capacitance
load, the specification of reaching 150MHz is not satisfied, but the stability of the design
is prioritized and the obtained GBW reduction is tolerable.
38
```

---

## p.39

![p.39](pages/p39.png)

![p.39 내장 이미지 1](images/p39_1.png)

![p.39 내장 이미지 2](images/p39_2.png)

```text
Gain-Bandwidth Product (GBW)
Conventional Structure
63.66 MHz
Current Recycling Structure
133.2 MHz
Table 7: GBW values for the pre layout simulations
5.3
Phase Margin
From the initial simulations, it was proved that the added transistors in the Recycling
Folded Cascode degrade the Phase Margin, making the system unstable. By adding a
capacitor, the system was brought to stability, but it is an important factor to consider
when switching to the Recycling Structure. Also, the stability of this structure has a
dependency on the load, which does not happen in the Conventional Structure, because
the Phase Margin is large enough that the changes in the load do not highly affect the
stability.
For this measurement, as previously done, for a more precise value, the calculator
is used to obtain the values. The expression is:
• Phase Margin: phaseMargin((VF(”output”) / VF(”input”)))
The Complete AC response where the Phase Margin is obtained for both amplifiers
is depicted in figure 13.
The Phase Margin obtained with the expression is shown in table 8 and both am-
plifiers are stable, nonetheless, there is a clear degradation in the Phase Margin, which
must be considered if using the Recycling structure.
39
```

---

## p.40

![p.40](pages/p40.png)

![p.40 내장 이미지 1](images/p40_1.png)

![p.40 내장 이미지 2](images/p40_2.png)

![p.40 내장 이미지 3](images/p40_3.png)

```text
Figure 13: Complete AC Response for Margin calculations
Phase Margin
Conventional Structure
82.49°
Current Recycling Structure
62.77°
Table 8: Phase Margin for the pre layout simulations
40
```

---

## p.41

![p.41](pages/p41.png)

![p.41 내장 이미지 1](images/p41_1.png)

![p.41 내장 이미지 2](images/p41_2.png)

![p.41 내장 이미지 3](images/p41_3.png)

```text
5.4
DC Offset Voltage
The DC offset voltage is obtained with the circuit in figure 14
Figure 14: Schematic for measuring the DC Offset Voltage
This parameter is important to get a more accurate Common Mode Rejection Ratio
(CMRR) result and to check which is the level of DC Offset that the amplifier has for a
better characterization of the performance.
To get this value, a DC simulation is done and the voltage between VCM and the
output is measured to obtain the DC Offset voltage.
Refer to table 9 for the obtained DC Offset voltage for both amplifiers. The Recycling
Structure has a smaller offset magnitude than the Conventional.
DC Offset Voltage
Conventional Structure
-942.3µV
Current Recycling Structure
-319µV
Table 9: DC Offset Voltage for the pre layout simulations
5.5
Common Mode Rejection Ratio (CMRR)
Because both designed amplifiers are differential, the CMRR is an important characteristic
to check the ability to reject common-mode signals for both amplifiers. To do so, the
circuit in figure 15 is used. The offset voltage obtained in previous subsection is used to
compensate this voltage and get a more accurate CMRR value.
By definition, the CMRR is calculated as:
41
```

---

## p.42

![p.42](pages/p42.png)

![p.42 내장 이미지 1](images/p42_1.png)

![p.42 내장 이미지 2](images/p42_2.png)

![p.42 내장 이미지 3](images/p42_3.png)

```text
CMRR =
Av
ACM
= Vout
VCM
(24)
Where Vout is the output of the differential amplifier, that is obtained from the open-
loop gain simulation and VCM is the output of the Common Mode that is obtained from
the circuit in figure 15.
Figure 15: Circuit for Common-Mode Rejection Ratio [2]
The CMRR is checked at 10Hz and at 100MHz.
An AC simulation is performed to obtain the AC behavior in Common Mode. The
schematic used is given in figure 16. The value of the DC source in the input is changed
accordingly to the DC Offset Voltage obtained in the previous section. The result is
shown in figure 17, where it is observed that the CMRR of the Recycling structure is
higher, except for a small range where the conventional is slightly better. That behavior
is expected because the gain of the Recycling structure is higher, thus, when dividing by
the Common Mode Gain, which is expected to be small, the structure with higher gain
is also expected to have higher CMRR.
CMRR @ 10Hz
CMRR @ 100MHz
Conventional Structure
63.29dB
34.53dB
Current Recycling Structure
69.72dB
37.06dB
Table 10: CMRR for the pre layout simulations
42
```

---

## p.43

![p.43](pages/p43.png)

![p.43 내장 이미지 1](images/p43_1.png)

![p.43 내장 이미지 2](images/p43_2.png)

![p.43 내장 이미지 3](images/p43_3.png)

![p.43 내장 이미지 4](images/p43_4.png)

```text
Figure 16: Schematic for CMRR simulation
Figure 17: Result for CMRR simulation
5.6
Power Supply Rejection Ratio (PSRR)
Given that it is possible that the power supply of the amplifier has some variations, it
is important to check the PSRR to check the ability of both amplifiers to suppress any
variation in the power supply that can affect the output signal. To do that, the circuit
used is depicted in figure 18 and the following expressions are used:
PSRR+ = Vdd
Vout
(25)
43
```

---

## p.44

![p.44](pages/p44.png)

![p.44 내장 이미지 1](images/p44_1.png)

![p.44 내장 이미지 2](images/p44_2.png)

![p.44 내장 이미지 3](images/p44_3.png)

![p.44 내장 이미지 4](images/p44_4.png)

```text
PSRR−= Vss
Vout
(26)
Where Vout is the output, and Vdd and Vss is the ripple in the inputs.
Figure 18: Circuit for Power Supply Rejection Ratio [2]
The Schematic used and the results for both amplifiers is shown in figure 19. It is
observed that the PSRR is higher for the Recycling structure, which is expected. This
is because the definition of the PSRR is the relation between the input gain and the
supply noise gain. Even both amplifiers have a similar noise gain, since the loop gain of
the Recycling structure is higher, it also leads to higher PSRR.
Figure 19: Schematic for Power Supply Rejection Ratio simulation
The results are shown in figures 20 and 21.
44
```

---

## p.45

![p.45](pages/p45.png)

![p.45 내장 이미지 1](images/p45_1.png)

![p.45 내장 이미지 2](images/p45_2.png)

![p.45 내장 이미지 3](images/p45_3.png)

![p.45 내장 이미지 4](images/p45_4.png)

```text
Figure 20: Result of PSRR+ simulation
Figure 21: Result of PSRR- simulation
45
```

---

## p.46

![p.46](pages/p46.png)

![p.46 내장 이미지 1](images/p46_1.png)

![p.46 내장 이미지 2](images/p46_2.png)

![p.46 내장 이미지 3](images/p46_3.png)

```text
PSRR+ @ 10Hz
PSRR- @ 10Hz
Conventional Structure
51.40dB
68.34dB
Current Recycling Structure
56.79dB
76.65dB
Table 11: PSRR for the pre layout simulations
5.7
Input Common Mode Range (ICMR)
The range of input that the amplifier is working in the intended region (saturation) is
defined by the ICMR. To measure this parameter, the circuit from figure 22 is used.
Figure 22: Circuit for Input Common Mode Range [2]
The valid range is given for the range of voltages where the output has slope 1. As
a reference, the DC voltage is also plotted, because it has slope 1. The result is plotted
in figure 24 and the schematic used in figure 23. A DC simulation is done with a sweep
in the DC value of the input voltage. The voltage is swept from -0.5V to 2V and when
the input value deviates a 2% from the input, it is considered that the amplifier is not
working in the intended region anymore.
The results show that the input range where the amplifier works in the saturation
region is larger in the Recycling structure compared to the Conventional.
46
```

---

## p.47

![p.47](pages/p47.png)

![p.47 내장 이미지 1](images/p47_1.png)

![p.47 내장 이미지 2](images/p47_2.png)

![p.47 내장 이미지 3](images/p47_3.png)

![p.47 내장 이미지 4](images/p47_4.png)

```text
Figure 23: Schematic for Input Common Mode Range
Figure 24: Results for the pre layout Input Common Mode Range
ICMR [V]
Conventional Structure
[0.3; 1.27]
Current Recycling Structure
[0.3; 1.74]
Table 12: ICMR for the pre layout simulations
5.8
Slew Rate
For the measurement of the Slew Rate, the same circuit than for the Open-Loop simu-
47
```

---

## p.48

![p.48](pages/p48.png)

![p.48 내장 이미지 1](images/p48_1.png)

![p.48 내장 이미지 2](images/p48_2.png)

![p.48 내장 이미지 3](images/p48_3.png)

![p.48 내장 이미지 4](images/p48_4.png)

```text
lations is used, but instead of using the sinusoidal voltage source, a pulse source is used.
A transient simulation is performed in order to assess the slew rate of the amplifier. The
circuit used is given in figure 25.
Figure 25: Circuit for transient simulations
The transient response of the amplifiers is shown in figure 26.
Figure 26: Transient response
48
```

---

## p.49

![p.49](pages/p49.png)

![p.49 내장 이미지 1](images/p49_1.png)

![p.49 내장 이미지 2](images/p49_2.png)

![p.49 내장 이미지 3](images/p49_3.png)

```text
Besides the visual check of the Slew Rate measurement, a calculator expression is
used to check the value of the Slew Rate for a more precise calculation. From the visual
check shown in figure 27, the Slew Rate of the Recycling is slightly higher than the
Conventional, but not as much as the theory expects.
Figure 27: Slew Rate visual check
The calculator expression used are and the output results is given in table 13:
Positive Slew Rate: slewRate(VT(”output”) 0 nil 1 nil 10 90 nil ”time”)
Negative Slew Rate: slewRate(VT(”output”) 1 nil 0 nil 10 90 nil ”time”)
Slew Rate +
Slew Rate -
Conventional Structure
17.69 V/µ s
-18.4 V/µ s
Current Recycling Structure
19.16 V/µ s
-18.95 V/µ s
Table 13: Slew Rate for the pre layout simulations
5.9
Settling time
For both amplifiers, two settling times are computed. The first one is the 10% −90% and
the other one is the measure of the overshoot. The same circuit and simulation as the
49
```

---

## p.50

![p.50](pages/p50.png)

![p.50 내장 이미지 1](images/p50_1.png)

![p.50 내장 이미지 2](images/p50_2.png)

![p.50 내장 이미지 3](images/p50_3.png)

```text
Slew Rate simulation is used, but other part of the transient is checked and measured.
For both measurements, markers are used at 0.1V and 0.9V, given that the voltage pulse
used is 1V. For the overshoot, an amplified view of the transition is taken to measure it.
Regarding the overshoot, it is observed that the Conventional Structure does not
have any overshoot, it always keeps below the expected voltage, whereas the Recycling
structure has a slight overshoot of 0.12% as shown in figure 29. Since the overshoot is
not high enough to need time to stabilize around 1%, the overshoot magnitude is used to
compare against the post layout.
The results of the settling time and the overshoot are:
Settling time (90% Final Value)
Overshoot
Conventional Structure
44.67ns
0%
Current Recycling Structure
41.95ns
0.12%
Table 14: Settling time and overshoot for the pre layout simulations
Figure 28: Settling time markers
50
```

---

## p.51

![p.51](pages/p51.png)

![p.51 내장 이미지 1](images/p51_1.png)

![p.51 내장 이미지 2](images/p51_2.png)

![p.51 내장 이미지 3](images/p51_3.png)

```text
Figure 29: Close look at the overshoot
5.10
Linearity
For the linearity measurement the second and third Harmonic Distortion (HD) (HD2 and
HD3) are measured. The procedure followed is to calculate the Discrete Fourier Transform
(DFT) and from that, calculate the magnitude of the DFT in decibels.
Since the frequency of the source is known, in this case set to 1MHz as shown in figure
30 the second and third harmonics are 2MHz and 3MHz respectively. The magnitude of
these harmonics is subtracted to the fundamental and the HD2 and HD3 are calculated.
51
```

---

## p.52

![p.52](pages/p52.png)

![p.52 내장 이미지 1](images/p52_1.png)

![p.52 내장 이미지 2](images/p52_2.png)

![p.52 내장 이미지 3](images/p52_3.png)

```text
Figure 30: Schematic for linearity simulations
The obtained values are:
HD2
HD3
Conventional Structure
56.07dB
61.05dB
Current Recycling Structure
55.04dB
59.85dB
Table 15: HD2 and HD3 results for the pre layout simulations
The figures showing the DFT for both systems are figure 31 and 32 for the Con-
ventional and the Recycling structure respectively. Conventional structure has a slight
advantage in terms of linearity against the Recycling structure.
52
```

---

## p.53

![p.53](pages/p53.png)

![p.53 내장 이미지 1](images/p53_1.png)

![p.53 내장 이미지 2](images/p53_2.png)

![p.53 내장 이미지 3](images/p53_3.png)

![p.53 내장 이미지 4](images/p53_4.png)

```text
Figure 31: DFT result for Conventional Structure
Figure 32: DFT result for Recycling Structure
5.11
Noise
For the noise measurements of both amplifiers, the schematic depicted in figure 30 is used.
Since Virtuoso has the noise performance simulation, it is used to characterize the noise of
both amplifiers. Given that the simulation outputs the value of the output referred noise,
but not for the input, the calculator is used for that measurement.
53
```

---

## p.54

![p.54](pages/p54.png)

![p.54 내장 이미지 1](images/p54_1.png)

![p.54 내장 이미지 2](images/p54_2.png)

![p.54 내장 이미지 3](images/p54_3.png)

```text
• Input referred noise: sqrt(integ((getData(”in” ?result ”noise”)**2) 1 100000000))
Two different simulations have been done, given that in the simulation the output
and input nodes must be specified.
The results for the Root-Mean-Square (RMS) input referred noise between 1Hz and
100MHz are shown in table 16 and the input referred noise curve in figure 33. The input
referred noise shows that the Conventional structure is a noisier structure. That is also
appreciated in the noise curves, where the values for the Conventional structure are larger.
Figure 33: Output Referred noise curve for Conventional Structure
Input Referred Noise (Vrms)
Conventional Structure
107µV
Current Recycling Structure
87.45µV
Table 16: Noise for the pre layout simulations
5.12
Comparison and simulation conclusion
Table 17 summarizes the simulations and checks performed in this section. The values
that are better for each parameter are highlighted. The Bias Current does not have a
subsection, but it was checked with the operating point and only the amplifier current is
considered.
54
```

---

## p.55

![p.55](pages/p55.png)

![p.55 내장 이미지 1](images/p55_1.png)

![p.55 내장 이미지 2](images/p55_2.png)

```text
The Recycling Folded Cascode with similar current consumption is clearly outper-
forming the Conventional Folded Cascode in terms of DC Gain, where the approximated
8-9dB increased is shown. Given that increase in the gain, the GBW it is slightly over the
double despite a decrease in the bandwidth.
The Slew Rate performance of the Recycling Structure is better than the Conven-
tional, nonetheless, the theoretical improvement was that the Recycling should be three
times larger than the Conventional, however, the actual improvement obtained from sim-
ulation shows a smaller improvement.
Another parameter that has improved from the conventional to the recycling is
the PSRR. The increase in the PSRR is expected, given that the gain in the Recycling
structure is higher. Also because of the increase in the GBW the improvement in the
PSRR extends to higher frequencies.
The input referred noise is also lower for the Recycling structure in comparison with
the Conventional structure.
CMRR is higher in the Recycling Structure and the input where the amplifier is
working in saturation has also slightly increased, covering a higher input range.
Nonetheless, besides the expected worse Phase Margin, which clearly shows up with
a decrease of roughly 20°, which must be considered when designing given that could lead
to really low Phase Margin and bring the system to a non-stable behavior, as in the initial
simulations.
Furthermore, another parameter where the Conventional Structure shows a slight
performance improvement against the Recycling is the linearity, where the distortion of
the harmonics is higher for the Conventional.
Despite the above mentioned decrease in performance, the improvements are more,
so after the pre layout simulations, it is concluded that the Recycling structure is a
structure that is worth switching to, since the performance improvement justifies the pa-
rameters performance decrease and the modifications to switch from the conventional to
the recycling are not extremely difficult to perform, which have a similar power consump-
tion and a slight increase in the area, given the two extra added transistors and the split
transistors. Nonetheless, the stability of the design must be monitored to avoid non-stable
behavior.
55
```

---

## p.56

![p.56](pages/p56.png)

![p.56 내장 이미지 1](images/p56_1.png)

![p.56 내장 이미지 2](images/p56_2.png)

```text
Parameter
Conventional Structure
Recycling Structure
Bias Current (µA)
457.4
457.2
DC Gain (dB)
48.46
57.91
Bandwidth (kHz)
233.9
173.2
GBW (MHz)
63.66
133.2
Phase Margin (º)
82.49
62.77
Slew Rate + (V/µs)
17.69
19.16
Slew Rate - (V/µs)
-18.4
-18.95
Offset Voltage (µV )
-942.3
-319
PSRR+ @ 10Hz (dB)
51.40
56.79
PSRR- @ 10Hz (dB)
68.34
76.65
CMRR @ 10Hz (dB)
63.29
69.72
CMRR @100MHz (dB)
34.53
37.06
ICMR [V]
[0.3; 1.27]
[0.3; 1.74]
Settling time (90% Final Value) (ns)
44.67
41.95
Overshoot
0%
0.12%
Input referred noise [µVrms]
1Hz - 100MHz
107
87.45
HD2 (dB)
56.07
55.04
HD3 (dB)
61.05
59.85
Table 17: Characterization comparison between Conventional and Recycling structures
56
```

---

## p.57

![p.57](pages/p57.png)

![p.57 내장 이미지 1](images/p57_1.png)

![p.57 내장 이미지 2](images/p57_2.png)

```text
6
Layout
Given that the amplifier has a differential pair and current mirrors, the matching between
transistors is an important factor to be considered during the layout of the device. The
criteria for the layout focuses on this idea of matching transistors in the layout.
This section specifies the criteria followed in order to proceed with the layout and
the resulting layout and the righteousness of the decisions taken for each block of the
layout.
6.1
Layout criteria
The main criteria followed for the layout are:
1. Although chip area is not an issue, whenever is possible, try to compact as much as
possible the layout.
2. No restriction in the usage of available metal layers, but avoid higher layers to keep
the P-type and N-Type (PN) junctions hidden from exposition to light to avoid PN
junctions variations. The reason of that is because one of the potential usages of this
amplifier is in combination with optical sensors and this amplifier must be covered
with higher metals to prevent to be exposed to light. The top metal is not used in
the layout.
3. Larger transistors are divided into smaller ones to avoid excessively large transistors
layout.
4. For improved matching, the maximum simmetry is kept among transistors, by keep-
ing rectangular shapes and the same orientation: the transconductance of Metal-
Oxide-Semiconductor (MOS) transistors depend on carrier mobilities, which show
orientation-dependent sensitivities. Having MOS transitors oriented in different di-
rections leads to different intrinsic transconductances for each of those transistors
making the matching difficult due to mismatches in the current[7].
5. Another aspect to be considered is the gradient-induced mismatches. Mismatch
caused by gradient is dependant on the separation between the effective centers,
or centroids, of matched devices. Mismatch due to gradient depends on the mag-
nitude of the gradient and also the distance between the centroids of the matched
devices. To minimize this effect, the common-centroid layout is applied. Apply-
ing common-centroid layout cancels the effects of long-range variations as long as
these are linear functions of distance, or even if the variations have non-linearities,
a linear approximation is considered over short distances[10].
57
```

---

## p.58

![p.58](pages/p58.png)

![p.58 내장 이미지 1](images/p58_1.png)

![p.58 내장 이미지 2](images/p58_2.png)

![p.58 내장 이미지 3](images/p58_3.png)

```text
6. As general norm, transistors should be placed thus the current follows the same
direction[7].
7. An exception of previous criteria is when transistors can be interdigitated, when
transistors can share a source or drain diffusion. Interdigitation ensures exact align-
ment of the centroids. By applying interdigitation, previous criteria for layout is not
fulfilled, since in a pattern of 2 interdigitated transistors in the form DASBDBSAD,
as shown in the example in figure 34, it is observed that the current through the
transistors of the same segment have the current flowing in opposite directions,
nonetheless, if in an interdigitated block a transistor is composed by the same num-
ber of left-oriented and right-oriented segments, the orientation effects that lead
to mismatch are canceled. The before-mentioned orientation effects can take place
because of diagonal shifts when ion implantation is performed at an angle. Tilted im-
plants do not have a big impact in matched transistors operating in the linear area,
nonetheless, in saturated devices it can lead to some transconductance mismatch.[7]
Figure 34: Interdigitated MOS transistors example[7]
8. Matched transistors are placed in close proximity.
9. Only paired transistors are designed to match.
6.2
Amplifier
For the layout of the transistor groups listed below, a matching technique is used:
1. Input transistors
58
```

---

## p.59

![p.59](pages/p59.png)

![p.59 내장 이미지 1](images/p59_1.png)

![p.59 내장 이미지 2](images/p59_2.png)

![p.59 내장 이미지 3](images/p59_3.png)

```text
Input transistors are split in 4 transistors each, for a total of 16 input transistors.
For the common-centroid and interdigitation pattern to ensure a good matching in
the transistors the following structure is followed:
SWDWSXDXSZDZSYDYSYDYSZDZSXDXSWDWS
The legend of the transistors is:
• Transistor M1A: W
• Transistor M1B: X
• Transistor M2A: Y
• Transistor M2B: Z
Refer to figure 35 for the implemented layout.
Figure 35: Layout of input transistors
2. Current mirror in M3 and M4
For this structure, the transistors are split. All the transistors have the same width
and length, but since one of the branches must be 3 times larger, one of the branches
59
```

---

## p.60

![p.60](pages/p60.png)

![p.60 내장 이미지 1](images/p60_1.png)

![p.60 내장 이미지 2](images/p60_2.png)

![p.60 내장 이미지 3](images/p60_3.png)

```text
has the triple amount of transistors than the other. In this case one branch has 4
transistors, whereas the other has 12.
For a more compact solution a 32x1 structure is implemented. A 2-D Common
Centroid Layout was also considered [10] but the space that was required between
rows to do the connections was more space consuming than making a 32x1. Refer
to figure 36 for a closer look at the layout.
SXDXSZDZSWDWSWDWSWDWSYDYSYDYSYDYSYDYSYDYSYDYSWDWSWDWSWDWSZDZSXDXS
The legend of the transistors is:
• Transistor M3A: W
• Transistor M3B: X
• Transistor M4A: Y
• Transistor M4B: Z
Figure 36: Layout of current mirror
3. Transistors M11 and M12
These transistors only are placed in a common-centroid structure, given that inter-
digitation is not possible. Transistors are placed as follows:
Y ZZY
60
```

---

## p.61

![p.61](pages/p61.png)

![p.61 내장 이미지 1](images/p61_1.png)

![p.61 내장 이미지 2](images/p61_2.png)

![p.61 내장 이미지 3](images/p61_3.png)

```text
• Transistor M11: Y
• Transistor M12: Z
The layout is depicted in figure 37.
Figure 37: Layout of transistors M11 and M12
4. Transistors M5 and M6
Same case and structure as transistors M11 and M12, but in this case split in 8
transistors in the structure Y Y ZZZZY Y . The size of transistors is the same, but
in this case there is double of each. Layout is given in figure 38.
• Transistor M5: Y
• Transistor M6: Z
61
```

---

## p.62

![p.62](pages/p62.png)

![p.62 내장 이미지 1](images/p62_1.png)

![p.62 내장 이미지 2](images/p62_2.png)

![p.62 내장 이미지 3](images/p62_3.png)

![p.62 내장 이미지 4](images/p62_4.png)

```text
Figure 38: Layout of transistors M5 and M6
5. Transistors M7 and M8
Same case and structure as transistors M11 and M12 , but in this case split in 8
transistors in the structure Y Y ZZZZY Y . Layout shown in figure 39.
• Transistor M7: Y
• Transistor M8: Z
Figure 39: Layout of transistors M7 and M8
62
```

---

## p.63

![p.63](pages/p63.png)

![p.63 내장 이미지 1](images/p63_1.png)

![p.63 내장 이미지 2](images/p63_2.png)

![p.63 내장 이미지 3](images/p63_3.png)

```text
6. Transistors M9 and M10
For the layout of this pair of transistors, besides the common-centroid structure,
interdigitation is also used because they share a common connection to VDD:
(SYDYSZDZSZDZSYDYS)
The legend of the transistors is:
• Transistor M9: Y
• Transistor M10: Z
The layout implementation is given in figure 40.
Figure 40: Layout of transistors M9 and M10
Transistor M0 does not require any matching technique, but to reduce the size of
it, it is divided in 16 transistors and interdigitation is applied as shown in figure 41. The
structure for this transistor is:
(DYSYDYSYDYSYDYSYDYSYDYSYDYSYDYSYD)
63
```

---

## p.64

![p.64](pages/p64.png)

![p.64 내장 이미지 1](images/p64_1.png)

![p.64 내장 이미지 2](images/p64_2.png)

![p.64 내장 이미지 3](images/p64_3.png)

```text
Figure 41: Layout of transistors M0
6.3
Biasing circuit
The transistors in the biasing circuit do not require any common-centroid structure, be-
cause it is not a hard-requirement that the transistors are matched, thus, for the transistors
in this side of the circuit, only interdigitation is applied in the transistors that allow to
apply it to reduce the size of the biasing circuit when doing the layout.
Moreover, another modification made is that all transistors are split thus the size in
the layout is reduced.
Below the list of transistors that are grouped by applying interdigitation:
1. Transistors Q7, Q9 and Q11: Common connection to VDD. Layout in figure 42.
2. Transistors Q5 and Q12: Common connection to GND. Layout in figure 43.
3. Transistors Q15 and Q16: Common connection to GND. Layout in figure 44.
64
```

---

## p.65

![p.65](pages/p65.png)

![p.65 내장 이미지 1](images/p65_1.png)

![p.65 내장 이미지 2](images/p65_2.png)

![p.65 내장 이미지 3](images/p65_3.png)

![p.65 내장 이미지 4](images/p65_4.png)

```text
Figure 42: Layout of transistors Q7, Q9 and Q11
Figure 43: Layout of transistors Q5 and Q12
65
```

---

## p.66

![p.66](pages/p66.png)

![p.66 내장 이미지 1](images/p66_1.png)

![p.66 내장 이미지 2](images/p66_2.png)

![p.66 내장 이미지 3](images/p66_3.png)

![p.66 내장 이미지 4](images/p66_4.png)

```text
Figure 44: Layout of transistors Q15 and Q16
For the rest of transistors, self-interdigitation is applied, in a similar way that is
performed with transistor M0.
The final layout is shown in figure 45.
Figure 45: Complete Layout
66
```

---

## p.67

![p.67](pages/p67.png)

![p.67 내장 이미지 1](images/p67_1.png)

![p.67 내장 이미지 2](images/p67_2.png)

![p.67 내장 이미지 3](images/p67_3.png)

![p.67 내장 이미지 4](images/p67_4.png)

```text
6.4
Design Rules Check (DRC)
The design showed in figure 45 did not show any Design Rules error, thus, the design
was correct from the foundry Process Design Kit (PDK) as shown in figure 46, where no
errors appear in the DRC.
Figure 46: DRC Results
6.5
Layout vs Schematic (LVS)
When it comes to the LVS check, where it is checked that all the components in the
schematic are present in the layout, no errors appeared. Results of this check are shown
in figure 47.
Figure 47: LVS Results
6.6
Parasitic Extraction (PEX)
After the correct LVS check, the next step for the layout validation is the Parasitic Ex-
67
```

---

## p.68

![p.68](pages/p68.png)

![p.68 내장 이미지 1](images/p68_1.png)

![p.68 내장 이미지 2](images/p68_2.png)

![p.68 내장 이미지 3](images/p68_3.png)

```text
traction (PEX), which extracts the capacitors, coupled capacitors and parasitic resistors
of the design. The output of this check is the closest simulation to the reality.
As mentioned in the introduction, one of the points that lead to delays and dis-
crepancies from the initial Gantt diagram was found at this point. The issues and the
solutions found for the different points are presented in this point.
The first issue that was encountered was that the PEX simulation was not outputting
the parasitic elements of the circuit. Even after checking the runset that was provided
by the Thesis Advisor and all the configuration parameters, it was observed that there
was something wrong in the configuration, given that, with the exact same runset and
configuration, the PEX on one side was outputting all the parasitics, whereas on the
other side it was not. This issue was solved by doing a reinstallation of the complete
configuration. After doing this, the issue was solved and the output of the PEX was the
expected and all the parasitics were included. The parasitics values are shown in figure
48.
Figure 48: Parasitics
68
```

---

## p.69

![p.69](pages/p69.png)

![p.69 내장 이미지 1](images/p69_1.png)

![p.69 내장 이미지 2](images/p69_2.png)

![p.69 내장 이미지 3](images/p69_3.png)

```text
After that, a first Post Layout simulation was done. In this case, only the Open
Loop and Bandwidth simulations. The results were not expected, given that the GBW
was 10 times lower. By looking in the Parasitics section in the Results Viewing Envi-
ronment (RVE), it was observed that the parasitic elements were not that high to have
such reduction in the GBW. By looking closer into the Calibre output of the PEX, it
was observed that the resistor from the design was not connected. The resistor was in
the Calibre, but there were 3 additional pins besides all the parasitic elements. Those 3
additional pins correspond to the pins of the resistor and those were floating.
The first step to debug this issue was to change the resistor and the layout. This
was done to check if the issue was caused by a single resistor. The resistor was changed
in the schematic and then the layout was quickly changed to pass DRC and LVS and
then, PEX. The layout for this tests was not optimized, it was only done for testing
purposes. The conclusion obtained for all those tests was that all the resistors had the
same behavior, thus the decision was to keep the first given that it was the layout that
was better optimized in terms of size.
The solution found for this issue was to manually connect the resistor. To do so,
after running the PEX, when the Calibre View Setup opens, instead of opening in Read
Mode, open it in Edit Mode. Then manually do the connection of the resistor to where it
corresponds. In this case, the resistor was connected between the source of the transistor
of the biasing circuit and ground. The final calibre file output view is shown in figure 49
with the implemented solution in the resistor.
Figure 49: Calibre File with amplified view of the resistor fix
After this connection was done, the Post Layout simulations were done.
69
```

---

## p.70

![p.70](pages/p70.png)

![p.70 내장 이미지 1](images/p70_1.png)

![p.70 내장 이미지 2](images/p70_2.png)

![p.70 내장 이미지 3](images/p70_3.png)

```text
7
Post Layout Simulations
In this section, the same circuits and simulation conditions as in the Pre Layout Simu-
lations are performed, thus in the following subsections, only the results comparing Pre
Layout Simulations and Post Layout Simulations are shown.
7.1
Open Loop Gain
After running the same circuit and conditions as in the Pre Layout simulations, the
obtained results for the amplifier after the layout is given in figure 50. The Open Loop Gain
for the Post Layout Recycling structure has a similar value of Gain as the ideal Recycling
structure, but it is slightly higher at 58.78dB compared to the previously obtained of
57.91dB for the ideal Recycling structure.
Figure 50: Post Layout Gain Simulation
Open Loop Gain
Conventional Structure
48.46dB
Current Recycling Structure
57.91dB
Post Layout Current Recycling Structure
58.78dB
Table 18: Open Loop Gain values for the post layout simulations
7.2
Bandwidth
For the bandwidth, the results are shown in table 19. The results for the bandwidth show
70
```

---

## p.71

![p.71](pages/p71.png)

![p.71 내장 이미지 1](images/p71_1.png)

![p.71 내장 이미지 2](images/p71_2.png)

```text
that the bandwidth value for the Post Layout is slightly lower than the theoretical value,
also, if comparing the GBW from table 20 it is observed that the GBW it is lower. This is
explained because there is an increase in the current consumption, which makes increase
slightly the gain, as shown before. This increase in current also leads to a decrease in the
output resistance, that should lead to an increase in the bandwidth. But due to the effects
of the parasitics it makes both bandwidth and GBW decrease.
Bandwidth
Conventional Structure
233.9 kHz
Current Recycling Structure
173.2 kHz
Post Layout Current Recycling Structure
155.1 kHz
Table 19: Bandwidth values for the post layout simulations
Gain-Bandwidth Product (GBW)
Conventional Structure
63.66 MHz
Current Recycling Structure
133.2 MHz
Post Layout Current Recycling Structure
132.6 MHz
Table 20: GBW values for the post layout simulations
7.3
Phase Margin
For the stability check, the Recycling structure it is still stable after the layout, as observed
in table 21 and the complete AC response in figure 51. Even it is still stable, the reduction
in the phase margin must be considered when designing, given the decrease in the margin
is roughly 20°.
Phase Margin
Conventional Structure
82.49°
Current Recycling Structure
62.77°
Post Layout Current Recycling Structure
62.59°
Table 21: Phase Margin for the post layout simulations
71
```

---

## p.72

![p.72](pages/p72.png)

![p.72 내장 이미지 1](images/p72_1.png)

![p.72 내장 이미지 2](images/p72_2.png)

![p.72 내장 이미지 3](images/p72_3.png)

```text
Figure 51: Post Layout complete frequency response
7.4
DC Offset Voltage
The DC Offset Voltage of the three amplifiers is shown in table 22. An observation from
this point is that the post layout Recycling structure is the structure that has less DC
Offset voltage.
72
```

---

## p.73

![p.73](pages/p73.png)

![p.73 내장 이미지 1](images/p73_1.png)

![p.73 내장 이미지 2](images/p73_2.png)

![p.73 내장 이미지 3](images/p73_3.png)

```text
DC Offset Voltage
Conventional Structure
-942.3µV
Current Recycling Structure
-319µV
Post Layout Current Recycling Structure
-114.3µV
Table 22: DC Offset Voltage for the post layout simulations
7.5
Common Mode Rejection Ratio (CMRR)
With previous obtained offset voltage, the schematic for this simulation and the voltage
were changed accordingly and the resulting simulation is in figure 52. It is observed that
the CMRR of the Recycling in the Post Layout is higher. This follows the same explanation
as explained in the Pre Layout Simulations. Given that the gain of the Post Layout was
slightly higher, when dividing by the Common Mode Gain, the expected result is to still
be higher than the Pre Layout.
Figure 52: Post Layout CMRR Simulation
CMRR @ 10Hz
CMRR @ 100MHz
Conventional Structure
63.29dB
34.53dB
Current Recycling Structure
69.72dB
37.06dB
Post Layout Current Recycling Structure
87.89dB
40.16dB
Table 23: CMRR for the post layout simulations
73
```

---

## p.74

![p.74](pages/p74.png)

![p.74 내장 이미지 1](images/p74_1.png)

![p.74 내장 이미지 2](images/p74_2.png)

![p.74 내장 이미지 3](images/p74_3.png)

![p.74 내장 이미지 4](images/p74_4.png)

```text
7.6
Power Supply Rejection Ratio (PSRR)
Regarding the PSRR the simulation results is shown in figures 53 and 54 . It is observed
that the PSRR is higher due to higher gain in the Post Layout structure because of the
previously mentioned increase in the current consumption, that leads to a performance
improvement in the PSRR.
Figure 53: Post Layout PSRR+
Figure 54: Post Layout PSRR-
74
```

---

## p.75

![p.75](pages/p75.png)

![p.75 내장 이미지 1](images/p75_1.png)

![p.75 내장 이미지 2](images/p75_2.png)

![p.75 내장 이미지 3](images/p75_3.png)

```text
PSRR+ @ 10Hz
PSRR- @ 10Hz
Conventional Structure
51.40dB
68.34dB
Current Recycling Structure
56.79dB
76.65dB
Post Layout Current Recycling Structure
59.54dB
77.42dB
Table 24: PSRR for the post layout simulations
7.7
Input Common Mode Range (ICMR)
No considerable changes in the ICMR after layout. Results in figure 55.
Figure 55: Post layout ICMR
ICMR [V]
Conventional Structure
[0.3; 1.27]
Current Recycling Structure
[0.3; 1.74]
Post Layout Current Recycling Structure
[0.3; 1.74]
Table 25: ICMR for the post layout simulations
7.8
Slew Rate
As similarly done to previous sections, the transient response, the slew rate visual check
75
```

---

## p.76

![p.76](pages/p76.png)

![p.76 내장 이미지 1](images/p76_1.png)

![p.76 내장 이미지 2](images/p76_2.png)

![p.76 내장 이미지 3](images/p76_3.png)

![p.76 내장 이미지 4](images/p76_4.png)

```text
and the values are given in figure 56, 57 and table 26 respectively. From the figures it is
observed that no large variations in the Slew Rate after the layout.
Figure 56: Post layout transient response
Figure 57: Post layout Slew Rate visual check
76
```

---

## p.77

![p.77](pages/p77.png)

![p.77 내장 이미지 1](images/p77_1.png)

![p.77 내장 이미지 2](images/p77_2.png)

![p.77 내장 이미지 3](images/p77_3.png)

```text
Slew Rate +
Slew Rate -
Conventional Structure
17.69 V/µ s
-18.4 V/µ s
Current Recycling Structure
19.16 V/µ s
-18.95 V/µ s
Post Layout Current Recycling Structure
19.16 V/µ s
-18.94 V/µ s
Table 26: Slew Rate for the post layout simulations
7.9
Settling Time
With the same methodology used, the settling time and overshoot figures are 58 and 59.
The obtained values for the settling time and the overshoot do not differ considerably
from the theoretical:
Settling time (90% Final Value)
Overshoot
Conventional Structure
44.67ns
0%
Current Recycling Structure
41.95ns
0.12%
Post Layout Current Recycling Structure
41.98ns
0.10%
Table 27: Settling time and overshoot for the post layout simulations
Figure 58: Post Layout settling time markers
77
```

---

## p.78

![p.78](pages/p78.png)

![p.78 내장 이미지 1](images/p78_1.png)

![p.78 내장 이미지 2](images/p78_2.png)

![p.78 내장 이미지 3](images/p78_3.png)

```text
Figure 59: Post Layout close look at the overshoot
7.10
Linearity
The linearity harmonic distortion values are:
HD2
HD3
Conventional Structure
56.07dB
61.05dB
Current Recycling Structure
55.04dB
59.85dB
Post Layout Current Recycling Structure
55.03dB
59.84dB
Table 28: HD2 and HD3 results for the post layout simulations
The DFT graph is shown in figure 60. In this case, as the values also show, there is
no large variation in the results of linearity after the layout.
78
```

---

## p.79

![p.79](pages/p79.png)

![p.79 내장 이미지 1](images/p79_1.png)

![p.79 내장 이미지 2](images/p79_2.png)

![p.79 내장 이미지 3](images/p79_3.png)

![p.79 내장 이미지 4](images/p79_4.png)

```text
Figure 60: DFT Results for Post Layout Recycling Folded Cascode
7.11
Noise
Noise results are shown in figures 61 and table 29. Results match the theoretical values,
where the Recycling structure performs better than the Conventional.
Figure 61: Post Layout Input Referred Noise curve
79
```

---

## p.80

![p.80](pages/p80.png)

![p.80 내장 이미지 1](images/p80_1.png)

![p.80 내장 이미지 2](images/p80_2.png)

```text
Input Referred Noise (Vrms)
Conventional Structure
107µV
Current Recycling Structure
87.45µV
Post Layout Recycling Structure
87.45µV
Table 29: Noise for the post layout simulations
7.12
Discrepances against Pre Layout Simulations
From the previous sections, both Pre Layout Simulations for the Conventional Folded
Cascode and the Recycling Folded Cascode are shared, nonetheless, in the table 30 only
the Recycling Folded Cascode is compared (pre and post layout).
This simulations only confirm the performance increase shown in previous simula-
tions, given that the performance is similar to what was previously obtained. But there
are some parameters that clearly have an unexpected improvement.
Among these results are the Gain, CMRR and PSRR. It is observed that these
parameters have an increase of performance, given that the bias current is also increasing,
which is not expected at all, because the design has not been modified, so the current
consumption of the amplifier should be the same.
The reason of that was checked. Due to the appearance of parasitics, not only in
the amplifier, but also in the biasing circuit, the effect on one of the branches of the
biasing circuit is affecting the current consumption of the circuit, thus affecting some of
the performance. In this case, it leads to an improvement in the performance, mainly due
to an increase in the current consumption. As shown in table 30 there is an increase in
the bias current of roughly 6µA after the layout, due to the affectation of the parasitics
to the bias circuit.
The other parameters show the expected behavior. Some of them are expected to
be slightly lower, given that the effect of the parasitics is usually negative, which is what
is observed in general terms in table 30.
80
```

---

## p.81

![p.81](pages/p81.png)

![p.81 내장 이미지 1](images/p81_1.png)

![p.81 내장 이미지 2](images/p81_2.png)

```text
Parameter
Pre Layout
Post Layout
Bias Current (µA)
457.2
463.7
DC Gain (dB)
57.91
58.78
Bandwidth (kHz)
173.2
155.1
GBW (MHz)
133.2
132.6
Phase Margin (º)
62.77
62.59
Slew Rate + (V/µs)
19.16
19.16
Slew Rate - (V/µs)
-18.95
-18.94
Offset Voltage (µV )
-319
-114.3
PSRR+ @ 10Hz (dB)
56.79
59.54
PSRR- @ 10Hz (dB)
76.65
77.42
CMRR @ 10Hz (dB)
69.72
87.89
CMRR @100MHz (dB)
37.06
40.16
ICMR [V]
[0.3; 1.74]
[0.3; 1.74]
Settling time (90% Final Value) (ns)
41.95
41.98
Overshoot
0.12%
0.10%
Input referred noise [µV rms]
1Hz - 100Mhz
87.45
87.45
HD2 (dB)
55.04
55.03
HD3 (dB)
59.85
59.84
Table 30: Pre Layout and Post Layout Characterization comparison
81
```

---

## p.82

![p.82](pages/p82.png)

![p.82 내장 이미지 1](images/p82_1.png)

![p.82 내장 이미지 2](images/p82_2.png)

```text
8
Economic Study
Since this thesis does not include the tape-out of the design, the cost related to this
process is not included in the Economic Study.
The considered wage for the Economic Study is the salary of a Junior Electronic
Engineer working full-time during 5 months, since that is the duration of this project.
The Social Security contribution is computed separately.
The cost associated for the computer and peripherals is the value that the asset has
depreciated during the development of this project.
For the Value-Added Tax (VAT), a 21% of the price is considered for the computer,
mouse, keyboard and monitor. For the Cadence license, VPN (Virtual Private Network)
and internet the 21% of the associated cost is used and for the electricity a 10% of the
associated cost is used.
Resource
Price
Use time
Associated Cost
Junior Engineer Salary
32000€/year
5 months
13333.33€
Social Security contribution
30% of the gross salary
5 months
4000€
Computer
2000€
5 months
500€
Mouse and keyboard
150€
5 months
30€
Monitor
400€
5 months
80€
Cadence license
(approximated, not disclosed)
12000€/year
5 months
5000€
VPN
(approximated, not disclosed)
10€/month
5 months
50€
Electricity
50€/month
5 months
250€
Internet
40€/month
5 months
200€
Total VAT
1663€
Total
25106.33€
Table 31: Economic Study
82
```

---

## p.83

![p.83](pages/p83.png)

![p.83 내장 이미지 1](images/p83_1.png)

![p.83 내장 이미지 2](images/p83_2.png)

```text
9
Conclusions and future development
From previous sections and study presented in this thesis, it is concluded that the recycling
structure clearly outperforms the conventional folded cascode operational amplifier. The
slight modification with minimal circuit modifications and minimal transistor increase in
the circuit that should not complicate excessively the integration, simulation results show
that it is a structure worth to switch to if the performance of the conventional structure
does not fulfill the expectations.
This circuit should also be preferred when working with tight current budgets, given
that provides twice the performance with the same current consumption. Regarding the
area, the only difference in terms of size is the addition of two extra transistors and the
increase due to the transistor split, that should not increase the area massively.
Nonetheless, as seen during the development of this thesis, as also mentioned in
[3], the phase margin decreases in the recycling structure, so that is a point to consider,
when switching from a Conventional to a Recycling structure by applying the mentioned
changes does not ensure that the system will be stable, mainly because of the decrease in
the phase margin due to the addition of a new zero-pole pair.
The stability of the Recycling Structure is sensitive to changes in the load capacitor
CL. As seen in the Pre-Layout Simulations, due to the tight phase margin in the Recycling
Structure, slight changes in the load can affect the stability of the design, thus, great care
should be taken with this parameter. In the case of the Conventional Structure, since the
Phase Margin is larger, the stability of the design does not depend on the load.
The linearity of the Conventional Structure is also slightly better than the Recycling
structure.
Some other works show that the increase in the recycling structure keeps improv-
ing the performance, which should be interesting to check in future thesis. It has been
demonstrated that by recycling the current the performance improves, and from refer-
ences, with a double recycling technique [15] [6] [12] it is still improving, nonetheless, the
performance improvement is not infinite. That study will of course depend on the appli-
cation, but should be interesting to find the limits until where the recycling structure is
really improving and up to what point can this outperform the previous step.
One of the outcomes of this thesis and one of the main gained knowledge is to
get familiar with this technology and the provided PDK. Some issues, such as the one
presented in the layout section were found. This design does not have a large number of
transistors and components, but when the parasitics are added, this number increases.
When the circuit complexity increases, the number of impedance that can bring that
83
```

---

## p.84

![p.84](pages/p84.png)

![p.84 내장 이미지 1](images/p84_1.png)

![p.84 내장 이미지 2](images/p84_2.png)

```text
issue also increases, thus some internal study must be done to try to find what causes the
issue, since in this thesis it was possible to manually fix it because only one resistance
was included in the design.
Regarding this thesis, the future steps are the tape-out of the chip and the experi-
mental and on-chip characterization of the design. Many factors must be considered when
checking against all the simulations presented in this thesis, such as the value of the load,
temperature and testing conditions[3].
Another thesis that could be developed to be compared against this one is to compare
two different sizing methodologies and compare which one can lead to a better performance
or the advantages and disadvantages that each of the methodologies bring to the design.
A methodology that could be used for the sizing is the gm
ID
[8].
84
```

---

## p.85

![p.85](pages/p85.png)

![p.85 내장 이미지 1](images/p85_1.png)

![p.85 내장 이미지 2](images/p85_2.png)

```text
References
[1]
Meysam Akbari et al. “High performance folded cascode OTA using positive feed-
back and recycling structure”. In: Analog Integrated Circuits and Signal Processing
82 (2015), pp. 217–227.
[2]
P.E. Allen. Measurement and Simulation of OPAMPS. Presentation. June 2014.
[3]
Rida S. Assaad and Jose Silva-Martinez. “The Recycling Folded Cascode: A General
Enhancement of the Folded Cascode Amplifier”. In: IEEE JOURNAL OF SOLID-
STATE CIRCUITS 44.9 (Sept. 2009), pp. 2535–2542.
[4]
R. Jacob Baker. CMOS Circuit Design, Layout and Simulation. 4th. John Wiley
and Sons, 2019.
[5]
Jiwei Chen and Bingxue Shi. “Novel constant transconductance references and the
comparisons with the traditional approach”. In: Southwest Symposium on Mixed-
Signal Design (2003).
[6]
Annu Dabas et al. “Design and Analysis of High-Performance Double Recycling
Folded Cascode Operational Transconductance Amplifier”. In: Iranian Journal of
Science and Technology, Transactions of Electrical Engineering 47 (2003), pp. 825–
843.
[7]
Alan Hastings. The Art of Analog Layout. Prentice-Hall, 2001.
[8]
Pankaj Kumar Jha, Pravanjan Patra, and Ashudeb Dutta. “gm/ID sizing and anal-
ysis of a recycling folded-cascode OTA for ECG signal conditioning in 0.18um
CMOS technology”. In: Analog Integrated Circuits and Signal Processing 115 (2023),
pp. 263–278.
[9]
David Johns and Ken Martin. Analog Integrated Circuit Design. Wiley, 1997.
[10]
Di Long, Xianlong Hong, and Sheqin Dong. “Optimal Two-Dimension Common
Centroid Layout Generation for MOS Transistors Unit-Circuit”. In: ed. by IEEE
Xplore. 2005.
[11]
K. Nakamura and L.R. Carley. “An enhanced fully differential folded-cascode op
amp”. In: IEEE JOURNAL OF SOLID-STATE CIRCUITS 27 (1992), pp. 563–
568.
[12]
Mohammad Rashtian. “Adaptive double recycling folded cascode amplifier”. In:
Analog Integrated Circuits and Signal Processing 110 (2022), pp. 165–174.
[13]
Willy M. Sansen. Analog Design Essentials. Springer Sciencce and Business Media,
2007.
[14]
J.M. Steininger. “Understanding wide-band MOS transistors”. In: IEEE Circuits
and Devices Magazine 6.3 (May 1990), pp. 26–31.
[15]
Zushu Yan, Pui-In Mak, and R.P Martins. “Double recycling technique for folded-
cascode OTA”. In: Analog Integrated Circuits and Signal Processing (2012).
[16]
M. Yavari. “Single-stage class AB operational amplifier for SC circuits”. In: Elec-
tronics Letters 46.14 (July 2010), pp. 977–979.
85
```
