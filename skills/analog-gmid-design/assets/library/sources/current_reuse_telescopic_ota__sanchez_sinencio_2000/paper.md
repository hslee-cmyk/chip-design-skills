# Low Voltage Analog Circuit Design Techniques: A Tutorial (E. Sánchez-Sinencio, TAMU AMSC, IEEE Dallas CAS Workshop 2000)

- 원본 PDF: 로컬(G:/내 드라이브/work/Todoc/논문모음/·기술문서/Gm_over_Id/) 없음 → 저자 게시본 다운로드 `https://people.engr.tamu.edu/s-sanchez/LV-Dallas-IEEE-Tutorial.PDF` (2026-10-16)
- 사본: `source.pdf` (sha256 `cb7418228dea1784d57497fd442cc303fd6397554d1d76f6a26518e072ca2178`)
- 웹 출처: https://people.engr.tamu.edu/s-sanchez/LV-Dallas-IEEE-Tutorial.PDF
- 서지(p.1에서 확인): Edgar Sánchez-Sinencio, "Low Voltage Analog Circuit Design Techniques: A Tutorial", Texas A&M University Analog and Mixed-Signal Center, IEEE Dallas CAS Workshop 2000, 2000-03-27
- 핵심 위치(self-cascode):
  - p.19 "What is a Self-Cascode Composite Transistor?" -- 그림(M1 아래 W/L, M2 위 mW/L, gate 공유), "The lower transistor M1 is equivalent to a resistor"
  - p.20 등가 β 유도 -- "M2 should in saturation and M1 is in linear region"
  - p.21 "Comments on VDSAT" -- "transistor M1 always operates in linear region"
  - p.22 참고문헌 1: C. Galup-Montoro et al., "Series-Parallel Association of FET's for High Gain and High Frequency Applications", IEEE JSSC, Sept. 1994 (원본 미보관)
- 엔진 연결: `assets/library/current_reuse_telescopic_ota.topology.json` 최상위 `_design_intent`(`_pattern`, M63·M64·M57·M58)
- 쪽 수: 78
- 변환: PyMuPDF 텍스트 추출(쪽 단위). 수식·표·그림은 텍스트가 깨질 수 있으니 같은 쪽의 렌더 PNG(`pages/`)로 확인할 것.
- `pages/`·`images/` 는 git 에 없다. 없으면 skill 폴더에서 `python tools/pdf_to_md.py ensure` 로 만든다.

---

## p.1

![p.1](pages/p01.png)

![p.1 내장 이미지 1](images/p01_1.png)

![p.1 내장 이미지 2](images/p01_2.png)

```text
Low Voltage Analog Circuit Design Techniques:
A Tutorial
Edgar Sánchez-Sinencio
http://amsc.tamu.edu/
Texas A&M University
Analog and Mixed-Signal Center
IEEE Dallas CAS Workshop 2000                           March 27, 2000
```

---

## p.2

![p.2](pages/p02.png)

![p.2 내장 이미지 1](images/p02_1.png)

```text
Low voltage (LV) power supply circuit design 
techniques are addressed in this tutorial.
In 
particular:
(i) Introduction; 
(ii) Transistor models capable to provide performance 
and power consumption tradeoffs; 
(iii) Low voltage implementation techniques, such as 
floating gates and bulk driven;
(iv) Basic building blocks not involving cascode 
structures, and
(v) LV circuit implementations examples.
Low Voltage Analog Circuit 
Design Techniques: Roadmap
Analog and Mixed-Signal Center, TAMU
```

---

## p.3

![p.3](pages/p03.png)

```text
Motivation
• What are the challenges in designing low voltage circuits ?
- To operate with power supplies smaller than 3.3 volts
- To design circuits with the same performance or better 
than circuits designed for larger power supplies
- To perform with technologies smaller than 0.5 micron
-To come with new design alternatives, 
The need for analog circuits in modern mixed-signal VLSI 
chips for multimedia, perception, control, instrumentation  
medical electronics and telecommunication is very high.
Analog and Mixed-Signal Center, TAMU
```

---

## p.4

![p.4](pages/p04.png)

```text
- Designers can not use conventional cascode structures, and 
other conventional design methodologies.
- Circuits should have the same performance or better than 
circuits designed for larger power supplies
- Circuit performance with technologies smaller than 0.5um   
must be better than circuits for larger technologies. 
-Third-generation communication applications require circuits   
( and systems)  with improved dynamic range over a much 
wider bandwidth.
- New building blocks and system must be designed to satisfy 
the needs of portable, lighter and faster equipment
( continues)
Analog and Mixed-Signal Center, TAMU
• Why are we concerned in designing low voltage circuits ?
```

---

## p.5

![p.5](pages/p05.png)

```text
Issues about low power supply voltage
Mister   5 volts  IC
Mister 0.8 volts IC
VTH
VTH
Scaling down size technology and
supply voltage does not scale linearly 
the “ VTH hat ”
```

---

## p.6

![p.6](pages/p06.png)

```text
• Threshold and VDSAT do not scale down linearly with power 
supply nor with smaller size technologies.
• Let us consider an illustrative example of a cascode and a 
simple inverting amplifiers, assume transistors MC and MS carry 
the same current IL, VT= 0.75V and VDS(SAT)=0.2V
• Keeping the same output voltage swing for both circuits 
involve the tradeoffs shown in the plot of transistor sizes and 
GBW vs. Power Supply Voltage
```

---

## p.7

![p.7](pages/p07.png)

![p.7 내장 이미지 1](images/p07_1.png)

---

## p.8

![p.8](pages/p08.png)

```text
• How to determine how much bias current is needed for 
certain application ?
• When a designer operates transistors in saturation, 
what does it mean VDS > VDS(SAT)  ?
• Can a circuit have their transistors operating in the transition
region ?  What transistor model equation can be employed ?
```

---

## p.9

![p.9](pages/p09.png)

```text
One Equation-All Regions  Transistor Model
•
Features of ACM model:
– physics-based model,
– universal and continuous expression for any inversion,
– independent of technology, temperature, geometry and gate voltage,
– same model for analysis, characterization and design.
•
Main design equations: (design parameters: I, gm, if)
2
1
1
f
m
t
i
n
g
I
+
+
=
φ
(
)1
1
2
2
2
−
+
=
f
t
T
i
L
f
π
µφ
1
1
1
−
+
=
f
t
ox
m
i
C
g
L
W
φ
µ
(
)
4
1
1
+
−
+
≅
f
t
DSAT
i
V
φ






−
=
1
2
n
g
I
C
g
L
W
m
t
t
ox
m
φ
φ
µ
I
drain current in transistor
gm transconductance in saturation
n
slope factor
φt 
thermal voltage
if
inversion level of the transistor defined as    
,  where               
is the normalization current.
if << 1  weak inversion,
if >> 1  strong inversion.
s
f
I
I
i
=
L
W
nC
I
t
ox
s
2
2
φ
µ
=
```

---

## p.10

![p.10](pages/p10.png)

![p.10 내장 이미지 1](images/p10_1.png)

---

## p.11

![p.11](pages/p11.png)

```text
L
W
C
n
I
I
I
i
t
ox
S
S
D
f
2
2
φ
µ
′
=
=
 
ID: saturation current 
IS: normalization current 
n: slope factor 
 
 
φ t
m
D
d
ng
I
i
=
+
+
2
1
1
 
10-2
10-1
100
101
102
103
10
-2
10
-1
0
4
10
(                  ) theory (n=1.35)
(                 ) simulation
(o o o o o o) experiment
φ t
m
D
g
I
i
10
 
 
 
WI 
      MI 
        SI 
 
 
Normalized Current
Transconductance-to-Current Ratio
Analog and Mixed-Signal Center, TAMU
```

---

## p.12

![p.12](pages/p12.png)

```text
The intrinsic cutoff frequency 
 
(
)
2
2
1
1
2
L
f
i
f
f
t
o
f
o
T
π
µφ
=
−
+
≅
 
 
10
-2
10
-1
10
0
10
1
10
2
10
3
10
4
10
-2
10
-1
10
0
10
1
10
2
10
3
id
f
f
T
o
 
 Drain-to-source saturation voltage 
 
(
) 4
1
1
+
−
+
≅
f
t
DSsat
i
V
φ
 
 
10
-2
10
-1
10
0
10
1
10
2
10
3
10
4
10
0
10
1
10
2
10
3
id  
 
 
 
 
 
 
 
 
 
 
 
 
WI 
      MI 
    SI 
 
 
 
WI 
       MI 
    SI 
 
 
VDSsat
t
φ
Analog and Mixed-Signal Center, TAMU
```

---

## p.13

![p.13](pages/p13.png)

```text
Correlation Between Junction Capacitance (CJ) and Frequency Response
  Parasitic capacitance α GBW/fT
                  CJ
CJ
W LDIF
=
′ ⋅
⋅
T
DIF
ox
f
GBW
L
L
C
J
C
2
CL
CJ
′
′
≅
LDIF
W
CJ
WL
CL
C
GBW
f
ox
T
≅
′
2
Correlation Between Area and Frequency Response 
Analog and Mixed-Signal Center, TAMU
```

---

## p.14

![p.14](pages/p14.png)

```text
+
VO
-
CL
IBIAS=IC
+
VI
-
CL
+
VO
-
IBIAS=ID
+
VI
-
t
C
m
1
I
g
φ
=
(
)





+
+
φ
=
d
t
D
m
i
1
1
n
2
1
I
g
t
vo
VA
A
φ
−
=
(
)





+
+
φ
−
=
d
t
vo
i
1
1
n
2
VA
A
t
C
I
CL
2
1
GBW
φ
π
=
(
)





+
+
φ
π
=
d
t
D
i
1
1
n
2
I
CL
2
1
GBW
πτ
≅2
1
fT
(
)1
i
1
2
2
1
f
d
T
−
+
πτ
≅
≅
φ t
CEsat
V
6 to 8
(
)
4
1
i
1
V
d
t
DSsat
+
−
+
=
φ
BIPOLAR
MOS
Transconductance
-to-current-ratio
(gm/ID)
DC Gain
(Avo)
Gain-Bandwidth
Product (GBW)
Intrinsic Cutoff
Frequency (fT)
Minimum Output
Voltage (VO)
DC Circuit
```

---

## p.15

![p.15](pages/p15.png)

![p.15 내장 이미지 1](images/p15_1.png)

```text
Low voltage (LV) power supply circuit design techniques are addressed in 
this  tutorial.  In particular:
(i) Introduction; 
(ii) Transistor models capable to provide performance and power 
consumption tradeoffs; 
(iii) Low voltage implementation techniques, such as 
floating gates, self-cascode, low voltage 
current-mirrors and bulk driven;
(iv) Basic building blocks not involving cascode structures, and
(v) LV circuit implementations examples.
Low Voltage Analog Circuit 
Design Techniques: Roadmap
Analog and Mixed-Signal Center, TAMU
```

---

## p.16

![p.16](pages/p16.png)

```text
(a) Layout
(b) Schematic Symbol
(c) Equivalent Circuit
Poly I
Poly II
N Diffusion
Metal
VG1
VG2
VG3
S
D
VG1
VG2
VGn
CG1
CG2
CGn
CFGB
CFGS
CFGD
VG1
VG2
VGn
Floating Gate Transistors
The floating gate voltage VF ,assuming that the initial charge QF in the floating gate is zero,,is 
described by:
VF = w0V0 + w1V1+ w2V2 + ….. + wnVn
Where                           wi = Ci/CTOT
CTOT = C0 + C1 + C2 +….+  Cn
```

---

## p.17

![p.17](pages/p17.png)

![p.17 내장 이미지 1](images/p17_1.png)

![p.17 내장 이미지 2](images/p17_2.png)

```text
Floating Gate MOS Transistors
CG (control Gate)
Poly - I
Poly - II
D
S
CO = Cgs + Cgb + Cgd
Assuming Cg >> Cgd,Cgb,  an approximate IDS can be obtained:
IDS=Koeff [( VCGS-VT,eff)VDS-CT VDS2/2Cg]  
ohmic
IDS =Kseff ( VCGS-VT,eff)2
saturation
Cg
Where: 
VT,eff =VTCO - QFG/Cg
Koeff = Kp(Cg/CT)(W/L),
Kseff =Kp(Cg/CT)2(W/L),
CT= CO + Cg
```

---

## p.18

![p.18](pages/p18.png)

![p.18 내장 이미지 1](images/p18_1.png)

```text
What is the effect of the FG on the transconductance and the 
output conductance, in the saturation region ?
gm = ( 2K2eff IDS)2 =  Cg gcm/CT
go = gco + Cgd gm/Cg
Where gcm and gco are the conventional transconductance 
and the output conductance of the conventional MOS transistor.
Thus, the FGT has a smaller transconductance 
and a larger output conductance than conventional
MOS transistor
Analog and Mixed-Signal Center, TAMU
```

---

## p.19

![p.19](pages/p19.png)

```text
What is a Self-Cascode Composite Transistor?
M2
M1
W/L
m W/L
G
D
S
X
(a) Self-Cascode Composite NMOS Transistor
(b) Equivalent Simple Transistor
In practical cases, for optimal operation the W/L ratio of M2 should be larger 
than that of M1, i.e. m>1. 
The 2-transistor structure can be treated as a composite transistor, which has
a much larger effective channel length (thus lower output conductance). 
D
G
S
The lower transistor M1 is equivalent to a resistor, but this resistor is input dependent..
The effective transconductance of the composite transistor is approximately
equal to the transconctance of M1: gm-eff =gm2/m=gm1
```

---

## p.20

![p.20](pages/p20.png)

```text
Equivalent Transistor Parameter
(
)
2
2
1
2
T
X
GS
V
V
V
i
−
−
= β
X
X
T
GS
V
V
V
V
i






−
−
=
2
1
1
1
β
For the composite transistor work in saturation region, we know M2 should
in saturation and M1 is in linear region. Thus, we can write equations for these 
two transistors as:
Solving      we can obtain:
1i
(
)
2
1
2
1
2
2
2
1
T
GS
V
V
i
−
+
=
β
β
β
β
From (3), we have
1
2
1
2
β
β
β
β
β
+
=
eq
If
1
2
β
β
⋅
= m
2
1
1
1
1
β
β
β
+
=
+
=
m
m
m
eq
1
β
β
=
∞
>
−
m
eq
```

---

## p.21

![p.21](pages/p21.png)

```text
Comments on VDSAT
Because transistor M1 always operates in linear region while the top
transistor operates in saturation or linear region. Voltage between the source
and  drain  terminal  of M1 is  so  small that  there  is  no  discernable VDSAT
difference in both the composite and simple transistors. Thus,self-cascode
structure can be used in low voltage applications.
The operating voltage of a regular cascode circuit is much higher than that of 
a single transistor. This characteristic makes regular cascode circuit not suitable
for low voltage applications. 
1
2
2
1
2
M
D
M
DSAT
M
DS
M
DSAT
eq
DSAT
R
I
V
V
V
V
+
=
+
=
−
−
−
−
(
) L
W
V
V
C
R
T
GS
OX
M
−
=
µ
1
1
where
```

---

## p.22

![p.22](pages/p22.png)

```text
References
1. C. Galup-Montoro, etc., “Series-Parallel Association of FET’s for 
High Gain and High Frequency Applications”, IEEE JSSC, Sept. 1994
2. D. Ceuster, etc., “Improvement of SOI MOS current-mirror 
performances using serial-parallel association of transistors”, Electronics 
Letters, Feb. 1996
3. P. Furth, H. Om’mani, “A 500-nW Floating-Gate Amplifier with 
Programmable Gain”, IEEE 1999
4. I. Fujimori, T. Sugimoto, “A 1.5V, 4.1mW Dual-Channel Audio 
Delta-Sigma D/A Converter”, IEEE JSSC, Dec. 1998
5. Personal note from Dr. Ugur Cilingiroglu
6. Yunchu Li, examples and SPICE tables
7. A.I.A. Cunha, M.C. Schneider, and C. Galup-Montoro, “An MOS transistor model 
for analog circuit design”, IEEE J. Solid-State Circuits, vol. 33, No. 10, pp 1510-
1519, Oct. 1998
```

---

## p.23

![p.23](pages/p23.png)

```text
Iin
Mm
M1
Mc
Iout
Vcas
M2
Iout
Vref
Aact
Iin
M1 M2
Iout
Iin Vref
M1
Mm
Mc
Potential LV Current-Mirrors
Goals: To reduce the input impedance and to increase the output 
Goals: To reduce the input impedance and to increase the output impedance,
impedance,
while keeping the voltage operation
while keeping the voltage operation
Iout
Vref
Iin
Mc
Mm
M1
M2
Vmirror
```

---

## p.24

![p.24](pages/p24.png)

```text
Iout
Iin
M1
M3
M2
M4
X
Iout
M1
M3
IB
IB
M2
Vcas
Iin
Iout
Iin
M1
M3
IB
IB
M2
M4
M5
Vshift
Iout
Iin
M1
M2
Iout
Iin
M1
M2
Vdd
IB1
M3
M4
IB2
Iout
M1
M2
Iin
ROB
AFB
```

---

## p.25

![p.25](pages/p25.png)

![p.25 내장 이미지 1](images/p25_1.png)

```text
LV CURRENT-SOURCE
A conceptual Schematic of the low voltage current source.  (a) Current source representation
(b) Architecture
dd
V
X
Y
Z
A
−
+
1
M
2
M
I
B
I
S
0
R
B
0
R
(a)
I
S
0
R
x
V
(b)
Analog and Mixed-Signal Center (AMSC) TAMU
How can we obtain a large impedance and low head room 
for the tail current used in a differential pair ?
```

---

## p.26

![p.26](pages/p26.png)

```text
)
g
/
g
A
)
g
g
/(
g
A
1(
2
o
)
oB
1
o
o
1
m
os
2
o
2
m
o
oB
1
o
1
m
o
g
g
g
/(
A
g
1
R
−
+
+
+
+
=
where
(
)
2
m
g
1
m
g
(
)
2
o
1
o g
g
,
are the transconductance and output conductance of 
(
)
2
1 M
M
,
respectively.
o
A
is the DC gain of the error amplifier  “A”  and
(
)
oB
oB R
g
is the output
conductance (resistance) of the reference current source
B
I
.  Assuming that
1
m
g
2
m
g
=
and
1
o
g
2
o
g
=
, equation (1) can be simplified as:
oB
os
R
R
−
≈
Note that the resistance is negative and is equal to the resistance of the reference source         .
B
I
4
o
3
o
4
m
os
g
g
g
R
−
≈
(1)
(2)
(3)
Analog and Mixed-Signal Center (AMSC) TAMU
```

---

## p.27

![p.27](pages/p27.png)

```text
dd
V
X
Y
Z
1
M
2
M
o
I
S
0
R
4
M
3
M
b
V
B
I
D
I
V
Current Ref.
Error Amplifier A
ss
V
Full implementation of the LV current source.
Analog and Mixed-Signal Center (AMSC) TAMU
dd
V
X
Y
Z
A
−
+
1
M
2
M
I
B
I
S
0
R
B
0
R
(a)
```

---

## p.28

![p.28](pages/p28.png)

![p.28 내장 이미지 1](images/p28_1.png)

```text
Measured output current of the simple (curve A) and LV (Curve B) current source.
Analog and Mixed-Signal Center (AMSC) TAMU
```

---

## p.29

![p.29](pages/p29.png)

```text
Bulk-Driven MOS Transistor 
Characteristics
•
ID vs. VBS or VGS of bulk-driven and conventional gate-driven MOS 
transistors
Drain Current
Gate-Source or Bulk-Source Voltage
-3V
-1.5V
0V
1.5V
3V
0mA
2mA
4mA
6mA
8mA
Bulk-Source 
Driven
Gate-Source 
Driven
ID
1.5V
VGS
VBS
```

---

## p.30

![p.30](pages/p30.png)

```text
Overhead of Bulk-Driven MOS Transistors
The bulk-driven amplifier is more suitable for low voltage operation. Please 
notice that the maximum allowable voltage at Vx is VDIODE. 
M1
Ib1
Vin
Vout
M1
Ib1
Vin
M2
Ib2
M2
Ib2
Vin
Vout
Vb
Vb
Vx
Vy
Vdd
Vdd
-Vss
-Vss
SRVX, 
Swing range 
of Vx
Swing range 
of Vy
Vdsat,M1
Vdsat,Ib1
Vdsat,Ib1
VGS,M2
SRVX=Vsup-Vdsat,Ib1-Vdsat,M1
SRVY=Vsup-Vdsat,Ib1-VGS,M2
= Vsup-Vdsat,Ib1-Vdsat,M2-VT
(a)
(b)
```

---

## p.31

![p.31](pages/p31.png)

```text
Advantages of Bulk-Driven MOS 
Transistors
•
The depletion characteristic allows zero, negative, and even small 
positive values of bias voltage to achieve the desired dc current. This 
can lead to larger input common mode voltage range and voltage 
swing that could not otherwise be achieved at low power supply 
voltages. ( Please refer the following example in this section and bulk-
driven differential pair discussed in following sections )
•
We can use the conventional gate to modulate the bulk-driven MOS 
transistor.
•
Example
Assume for the low voltage amplifiers, power supply voltage is
Vsup = Vdd+|Vss|<VDIODE+Vdsat   ,
where VDIODE is the forward Si diode cut-in voltage.
The voltage swing of Vx ( Figure a,  the amplifier with bulk-driven MOS 
FETs ) has only 2Vdsat’s decrease over Vsup. In such a low voltage, the 
conventional gate-driven amplifier ( Figure b ) fails to operate or may be 
greatly limited in voltage swing.
```

---

## p.32

![p.32](pages/p32.png)

```text
Disadvantages of Bulk-Driven MOS 
Transistors
•
The transconductance of a bulk-driven MOS FET is substantially 
smaller than a conventional gate-driven MOS transistor. This may 
result in lower GBW and worse frequency response, but better 
linearity and smaller power supply requirements.
•
For a conventional gate-driven MOSFET, the frequency response 
capacity is described by its transitional frequency, fT,
•
For the bulk-driven MOSFET, fT is given by
where     is the ratio of gmb to gm and typically has a value in the range 
of 0.2 to 0.4.
gs
m
driven
gate
T
C
g
f
π
2
,
=
−
)
(
2
)
(
2
,
bsub
bs
m
bsub
bs
mb
driven
bulk
T
C
C
g
C
C
g
f
+
=
+
=
−
π
η
π
η
```

---

## p.33

![p.33](pages/p33.png)

```text
Disadvantages of Bulk-Driven MOS Transistors 
( cont’d )
•
For typical saturated strong inversion MOSFET operation, the 
following approximation stands,
•
Another disadvantage of bulk-driven MOSFETs is that the polarity of 
the bulk-driven MOSFETs is process related. For an P well CMOS 
process, we only have N channel bulk-driven MOSFETs available, and 
for N well CMOS process, only P channel  MOSFETs. This limits its 
application. We can not use bulk-driven MOS transistors in some 
circuit structures which requires both N and P MOSFETs.
driven
gate
T
driven
bulk
T
f
f
−
−
≈
,
,
8.3
η
```

---

## p.34

![p.34](pages/p34.png)

```text
Disadvantages of Bulk-Driven MOS Transistors 
( cont’d )
•
MOS transistors can be laid out in the same well, thus their 
characteristics  will match better. Bulk driven transistors are in 
differential wells, it is inconvenient to design some circuits which 
require tight matching between transistors. For bulk-driven MOSFETs, 
it is not easy to utilize some layout techniques such as interdigitized 
and common centroid layout to make good matching.
•
Potentials to turn on the parasitic BJT transistors which may result in 
latch-up problem
•
The equivalent noise of  a bulk-driven MOS amplifier is larger than a 
conventional gate-driven MOS amplifier.
```

---

## p.35

![p.35](pages/p35.png)

```text
Example of OTAs using different approaches:
Example of OTAs using different approaches:
Conventional, 
Conventional, Current Divider
Current Divider-Source Degeneration
Source Degeneration
(CD
CD-SD
SD), 
), Floating Gate
Floating Gate, and 
, and Bulk Driven
Bulk Driven
Vi+
Vi-
Vout
M1
M2
M3
M4
M5
M6
VSS
M7
M8
VDD
ISS
M9
M10
VSS
DESIGN
ESIGN A 
A - REFERENCE
EFERENCE OTA
OTA
VOUT
OUT = G
= GMROUT
OUTVIN
IN
ROUT 
OUT = 
= 8.3 Mohms
8.3 Mohms
VIN
IN
RBIAS
BIAS
VBIAS
BIAS
VOFFSET
OFFSET
IOUT
OUT
IBIAS
BIAS
GM
1.2 AMI Technology
Vdd=-Vss= 1.35V
EXPERIMENTAL TEST SETUP
EXPERIMENTAL TEST SETUP
```

---

## p.36

![p.36](pages/p36.png)

![p.36 내장 이미지 1](images/p36_1.png)

![p.36 내장 이미지 2](images/p36_2.png)

```text
DESIGN
ESIGN A 
A - REFERENCE
EFERENCE OTA
OTA
Input Ch1 160mVpp @ 1 Hz
Input Ch1 160mVpp @ 1 Hz
Output Ch2 18mVpp
Output Ch2 18mVpp
THD ~ 
THD ~ -28dBm ~ 3.9% @160mVpp, 1Hz
28dBm ~ 3.9% @160mVpp, 1Hz
```

---

## p.37

![p.37](pages/p37.png)

```text
DESIGN B - CURRENT DIVISION OTA and 
Source Degeneration
ISS
Vi+
Vi-
ISS
Vout
VDD
VSS
M1
MM1
M2
MM2
M3
M14
M15
M16
M17
M18
M5
M7
M6
M8
M4
M9
M10
M11
M12
VSS
VDD
```

---

## p.38

![p.38](pages/p38.png)

![p.38 내장 이미지 1](images/p38_1.png)

![p.38 내장 이미지 2](images/p38_2.png)

```text
DESIGN
ESIGN B 
B - CURRENT
URRENT DIVISION and 
IVISION and SD OTA
SD OTA
Input Ch1 214mVpp @ 1 Hz
Input Ch1 214mVpp @ 1 Hz
Output Ch2 16mVpp
Output Ch2 16mVpp
THD ~ 
THD ~ -30dBm ~ 3.2% @214mVpp, 1Hz
30dBm ~ 3.2% @214mVpp, 1Hz
```

---

## p.39

![p.39](pages/p39.png)

```text
DESIGN C - FLOATING GATE OTA, plus SD and CD
Vi-
Vi+
ISS
Vb
VDD
VSS
VSS
M1
M2
MM1
MM2
M3
M4
M5
M6
M7
M8
M9
M10
Vout
```

---

## p.40

![p.40](pages/p40.png)

![p.40 내장 이미지 1](images/p40_1.png)

![p.40 내장 이미지 2](images/p40_2.png)

```text
DESIGN
ESIGN C 
C - FLOATING
LOATING GATE
ATE OTA
OTA
Input Ch1 214mVpp @ 1 Hz
Input Ch1 214mVpp @ 1 Hz
Output Ch2 15.2mVpp
Output Ch2 15.2mVpp
THD ~ 
THD ~ -34dBm ~ 2% @214mVpp, 1Hz
34dBm ~ 2% @214mVpp, 1Hz
```

---

## p.41

![p.41](pages/p41.png)

```text
DESIGN D - BULK DRIVEN OTA, PLUS CD AND SD
Vi-
Vi+
ISS
VG
VDD
VSS
VSS
M1
M2
MM1
MM2
M3 M4
M5
M6
M7
M8
M9
M10
Vout
```

---

## p.42

![p.42](pages/p42.png)

![p.42 내장 이미지 1](images/p42_1.png)

![p.42 내장 이미지 2](images/p42_2.png)

```text
DESIGN
ESIGN D 
D - BULK 
ULK DRIVEN
RIVEN OTA
OTA
Input Ch1 214mVpp @ 1 Hz
Input Ch1 214mVpp @ 1 Hz
Output Ch2 15.2mVpp
Output Ch2 15.2mVpp
THD ~ 
THD ~ -39dBm ~ 1.1% @214mVpp, 1Hz
39dBm ~ 1.1% @214mVpp, 1Hz
```

---

## p.43

![p.43](pages/p43.png)

```text
SIMULATION VS EXPERIMENTAL RESULTS
SIMULATED RESULTS
EXPERIMENTAL RESULTS
PAR \ DES
A
B
C
D
A
B
C
D
GM(nA/V)
11.6
11.55
11.51
11.24
10.5
9.3
8.7
8.8
∆ϕ @ 1Hz
(°)
0.1
0.098
0.047
0.025
<1
<1
<1
<1
Offset (mV) 0.07
0.027
-0.086
0.045
-1.8
-1.9
-1.5
0.647
THD (%)
1@162
mVpp
1@240
mVpp
1@330
mVpp
1@900
mVpp
3.9@160
mVpp
5.6@242
mVpp
3.2@330
mVpp
5.9@900
mVpp
THD (%) @
214mVpp
-
-
-
-
3.9
3.2
2
1.1
IBIAS(nA)
2
100
200
500
4
120
230
560
VDD = |VSS|
(V)
1.35
1.35
1.35
1.35
1.35
1.35
1.35
1.35
BIAS (V)
N/A
N/A
-1.35
-1.35
N/A
N/A
-1.35
-1.35
1.2 micron CMOS Technology
```

---

## p.44

![p.44](pages/p44.png)

```text
Rail-to-Rail Op Amps
•
There are two basic configurations for Op Amp applications:
(a) inverting configuration, and,
(b) non-inverting configuration.
R2
R1
Vin
Vout
(a) Inverting Configuration
Vout
Vin
R1
R2
Vout
Vin
(b) Non-Inverting 
Configuration
(c) Voltage Follower
( a special case of non-
inverting configuration )
Analog and Mixed-Signal Center,TAMU
```

---

## p.45

![p.45](pages/p45.png)

```text
Why Rail-to-Rail Differential Input Stage?
• The input and output swings of inverting and non-inverting 
configurations
Configuration
Input common mode
voltage swing
Output voltage swing
Inverting
≈0
Rail-to-rail
Non-inverting
R1/(R1+R2) * Vsup
Rail-to-rail
Voltage follower
Rail-to-rail
Rail-to-rail
•
From the table, we see that for inverting configuration, rail-to-rail input 
common mode range is not needed. But for non-inverting configuration, 
some input common mode voltage swing is required, especially for a 
voltage follower which usually works as an output buffer, we need a rail-
to-rail input common mode voltage range! To make an Op Amp work 
under any circumstance, a differential input with rail-to-rail common 
mode range is needed.
Analog and Mixed-Signal Center,TAMU
```

---

## p.46

![p.46](pages/p46.png)

```text
How to Obtain a Rail-to-Rail Input 
Common Mode Range?
•
We know that usually the input stage of an op amp consists of a 
differential pair. There are two types of differential pairs.
Ib1
To the next 
stage
To the next 
stage
Vi+
Vi+
Vi-
Vi-
(a) P-type differential input 
stage
(b) N-type differential input 
stage
```

---

## p.47

![p.47](pages/p47.png)

```text
•
First, let us observe how a differential pair works with different input 
common mode voltage
– P-type input differential pair 
To the next 
stage
Vi+
Vi-
Input Common 
Mode Voltage
-Vss
Vdd
Itail
gm
Vdsat,Ib
VGS,M1,2
VCMR
Vdd
-Vss
Ib
Vicm
M1 M2
Input common 
mode voltage range
Vdsat
VGS
VCMR ( Common Mode Range )
Where VGS=Vdsat+VT
```

---

## p.48

![p.48](pages/p48.png)

```text
– N-type differential input stage
Input Common 
Mode Voltage
-Vss
Vdd
Itail
gm
Ib
To the next 
stage
Vi+
Vi-
Vdsat
VGS
VCMR
Vdd
-Vss
Input common 
mode voltage range
Vdsat
VGS
VCMR ( Common Mode Range )
```

---

## p.49

![p.49](pages/p49.png)

```text
•
Why not connect these two pairs in parallel and try to get a full rail-to-
rail range? 
Again, how to Obtain a Rail-to-Rail Input 
Common Mode Range?
Simple N-P complementary input stage
Almost all of the rail-to-rail input stages are doing 
in this way by some variations! But how well 
does it work? 
Vi+
Vi-
M1
M3
M4
M2
Mb1
Mb2
IN
IP
Ib
Mb3
Mb4
Current 
Summation and 
subsequent stages
There should be an 
overlap between 
VCMR,P and VCMR,N , 
so the minimum 
power supply 
voltage requirement 
is
( 4Vdsat+VTN+VTP )
VCMR,P
Vdd
-Vss
Vdsat
VGS
VCMR
VCMR,N
P Pair
N Pair
VSUP ≥4Vdsat+VTN+VTP
```

---

## p.50

![p.50](pages/p50.png)

```text
• If 
and
IN=IP=ITAIL
then gmN=gmP=gm=                .
Region I.
When Vicm is close to the negative rail, only P-
channel pair operates.The N channel pair is off because 
its VGS is less than VT. The total transconductance of the 
differential pair is given by gmT= gmP=gm.
Region II. When Vicm is in the middle range, both of the P 
and N pairs operate. The total transconductance is given 
by gmT = gmN+gmP=2gm.
Region III.When Vicm is close to the positive rail, only N-
channel pair operates. The total transconductance is 
given by gmT = gmN=gm.
Common Mode Voltage
-Vss
Vdd
gm
Gm, the sum of 
gmN and gmP
gmN
gmP
P
P
N
N
L
W
KP
L
W
KP
K
)
(
2
1
)
(
2
1
=
=
The total transconductance of the input 
stage varies from gm to 2gm, the 
variation is 100% !
Region I
Region II
Region III
•
Transconductance vs. Vicm
TAIL
KI
2
Observations on transconductance performance 
for the entire region.-
```

---

## p.51

![p.51](pages/p51.png)

```text
CMRR(dB)
Vio(mV)
0
2
4
VI,CM(V)
0
0.5
1.0
-1.0
-0.5
60
70
80
90
6
CMRR
Vio
How does the CMRR varies with the input common-mode signal ?
```

---

## p.52

![p.52](pages/p52.png)

```text
Rail-to-Rail Techniques: Summary and Comparison
Case
Principle
∆gm
Slew Rate
CMRR
Advantage
Limitations
N/A for weak
inversion
1
const
I
I
P
N
=
+
[1][2][6
]
40% if in strong
inversion
Constant
56dB@10Hz,
52dB@100KHz,
measured in [2]
Small gm
variation ( 6% ) in
weak inversion
operation
Only work well in weak inversion, can
not used in high speed application
2
const
I
I
P
N
=
+
[3]
[16]
-12% +6%  (
simulated in this
presentation )
2 times
variation
80 dB / 53 dB
( measured in [3] )
Depends on quadratic characteristics of
MOSFETs, which is not exactly
followed for short channel transistors in
sub-micron processes
3
4 times IN or IP when
only one pair operates
[3][4][6]
+15% systematic gm
variation
2 times variation
70dB / 43 dB
( measured in [4] )
Somewhat simple
1) Same with case 2, but we can
change 4 to other numbers to have
smaller gm variation for short
channel transistors
2) Systematic gm deviation of 15%
even for ideal MOSFETs with
quadratic characteristics
4
Current switch, backup
pairs [5]
+20% systematic gm
variation
Constant
N/A
Constant slew rate
Systematic gm deviation of 20% even
for ideal MOSFETs with quadratic
characteristics
5
6-pair structure, back
pairs [7]
+20% systematic gm
variation ( analytical
),
±10% ( measured in
[7] )
Constant
N/A
Constant slew rate
Same with Case 4
6
Max/min selection [8][9]
7% ( simulated [9] )
5% ( strong
inversion, measured
[8] )
20% ( weak
inversion, measured
[8] )
Constant
N/A
Somewhat complex
7
Electronic zener [10]
8% ( measured )
80 dB / 43 dB
( measured in [10] )
Same with Case 2
8
Level shift [11]
±4% after tuning
13% before tuning
( measured )
≥80 dB ( DC )
( measured in [11] )
Simple
Gm variation sensitive to VT variation
and power supply voltage change
```

---

## p.53

![p.53](pages/p53.png)

```text
VB
Vi+
Vi-
IB
Io+
Io-
(a)
M1 M2
IB
VB
Vi+
Vi-
ViFG+
ViFG-
Io+
Io-
C1
C2
C2'
C1'
(b)
M1
M2
IB
Io+
Io-
Vi-
Vi+
VB
(c) Bulk Driven DP
Another Potential Solutions for Rail-to-Rail Amplifiers
Floating Gate DP
```

---

## p.54

![p.54](pages/p54.png)

```text
M2
M1
M4
M3
vI+
vI-
V1
V2
V4
V3
vSHIFT
vSHIFT
vSHIFT
vSHIFT
By using dynamic level shift, the rail-to-rail 
Amplifier can be obtained.
One more Rail-to-Rail Op Amp Technique
```

---

## p.55

![p.55](pages/p55.png)

```text
R10
R11
R8
R9
Q8
Q9
Q11
Q10
Q2
Q1
Q4
Q3
vI+
vI-
To next stage
VB2
RL1
RL3
RL2
RL4
IL1
IL2
IL3
IL4
V1
V2
V4
V3
N-P complementary input stage
with  dynamic level shift
Current summation
```

---

## p.56

![p.56](pages/p56.png)

```text
0.2
0.4
0.6
0.8
1.0
VI,CM (V)
VI,CM
V1 and V3
V2 and V4
V1~V4 and
VSHIFT (V)
0.4
0.2
0.6
0.8
1.0
VSHIFT
Q8
Q10
Q2
Q1
Q4
Q3
vI+
vI-
RL1
RL3
RL2
RL4
IL1
IL2
IL3
IL4
V1
V2
V4
V3
```

---

## p.57

![p.57](pages/p57.png)

```text
M2
M1
M4
M3
vI+
vI-
RL1
RL3
RL2
RL4
N-P complementary input stage
with  dynamic level shift
Current summation
vI+
vI-
Level-Shift Current
Generator
To next stage
IL
Vdd
-Vss
M10
M12
M11
M9
M5
M7
M8
M6
ML1
ML2
ML3
ML4
ML6
ML7
ML8
ML5
```

---

## p.58

![p.58](pages/p58.png)

```text
References
[1]
 J. H. Huijsing, and D. Linebarger, “Low voltage operational amplifier with rail-to-
rail input and output stages,” IEEE Journal of Solid-State Circuits, vol. SC-20, no.
6, pp. 1144-1150, December 1985
[2]
W.-C. S. Wu, W. J. Helms, J. A. Kuhn, and B. E. Byrkett, “Digital-compatible
high-performance operational amplifier with rail-to-rail input and output ranges,”
IEEE Journal of Solid-State Circuits, vol. 29 , no. 1, pp. 63-66, January 1994
[3]
R. Hogervorst, R. J. Wiegerink, P. A. L. de Jong, J. Fonderie, R. F. Wassenaar, and
J. H. Huijsing, “CMOS low-voltage operational amplifiers with constant-gm rail-
IEEE Proc. ISCAS 1992, pp. 2876-2879
[4]
R. Hogervost, J. P. Tero, R. G. H. Eschauzier and J. H. Huijsing, “A compact
power-efficient 3-V CMOS rail-to-rail input/output operational amplifier for VLSI
cell libraries,” IEEE Journal of Solid-State Circuits, vol. 29, no. 12, pp. 1505-
1513, December 1994
[5]
R. Hogervorst, S. M. Safai, and J. H. Huijsing, “A programmable 3-V CMOS rail-
to-rail opamp with gain boosting for driving heavy loads,” IEEE Proc. ISCAS
1995, pp. 1544-1547
[6]
J. H. Huijsing, R. Hogervorst, and K.-J. de Langen, “Low-power low-voltage
VLSI operational amplifier cells,” IEEE Trans. Circuits and Systems-I, vol. 42. no.
11, pp. 841-852, November 1995
```

---

## p.59

![p.59](pages/p59.png)

```text
References ( cont’d )
[7]
W. Redman-White, “A high bandwidth constant gm, and slew-rate rail-to-rail
CMOS input circuit and its application to analog cell for low voltage VLSI
systems,” IEEE Journal of Solid-State Circuits, vol. 32, no. 5, pp. 701-712, May
1997
[8]
C. Hwang, A. Motamed, and M. Ismail, “LV opamp with programmable rail-to-
rail constant-gm,” IEEE Proc. ISCAS 1997, pp. 1988-1959
[9]
C. Hwang, A. Motamed, and M. Ismail, “Universal constant-gm input-stage
architecture for low-voltage op amps,” IEEE Trans. Circuits and Systems-I, vol.
42. no. 11, pp. 886-895, November 1995
[10]
R. Hogervost, J. P. Tero, and J. H. Huijsing, “Compact CMOS constant-gm rail-to-
rail input stage with gm-control by an electronic zener diode,” IEEE Journal of
Solid-State Circuits, vol. 31, no. 7, pp. 1035-1040, July 1996
[11]
M. Wang, T. L. Mayhugh, Jr., S. H. K. Embabi, and E. Sánchez-Sinencio,
“Constant-gm rail-to-rail CMOS op-amp input stage with overlapped transition
IEEE Journal of Solid-State Circuits, vol. 34, no. 2, pp. 148-156,
February 1999
[12]
G. Ferri and W. Sansen, “A rail-to-rail constant-gm low-voltage CMOS
operational transconductance amplifier,” IEEE Journal of Solid-State Circuits, vol.
32, no. 10, pp. 1563-1567, October 1997
```

---

## p.60

![p.60](pages/p60.png)

```text
References ( cont’d )
[13] S. Sakurai and M. Ismail, “Robust design of rail-to-rail CMOS operational amplifiers for a
IEEE Journal of Solid-State Circuits, vol. 31, no. 2, pp. 146-
156, February 1996
[14] J. H. Botma, R. F. Wassenaar, and R. J. Wiegerink, “Simple rail-to-rail low-voltage constant
transconductance CMOS input stage in weak inversion,” Electronics Letters, vol. 29, no. 12,
pp. 1145-1147, June 1993
[15] V. I. Prodanov and M. M. Green, “Simple rail-to-rail constant transconductance input stage
operating in strong inversion,” IEEE 39th Midwest Symposium on Circuits and Systems, vol
2, pp. 957-960, August 1996
[16] J. H. Botma, R. F. Wassenaar, and R. J. Wiegerink, “A low voltage CMOS op amp with a
rail-to-rail constant-gm input stage and a class AB rail-to-rail output stage,” IEEE Proc.
ISCAS 1993, vol. 2, pp. 1314-1317, May 1993
[17] J. F. Duque-Carrillo, J. M. Valverde, and R. Perez-Aloe, “Constant-gm rail-to-rail common-
IEEE Journal of Solid-State
Circuits, vol. 28, no. 6, pp. 661-666, June 1993
[18] A. L. Coban and P. E. Allen, “A low-voltage CMOS op amp with rail-to-rail constant-gm
input stage and high-gain output stage,” IEEE Proc. ISCAS 1995, vol. 2, pp. 1548-1551,
April-May 1995
[19] J.F.Duque-Carrillo et al, “ 1-V Rail-to-Rail Operational Amplifiers in Standard CMOS
 IEEE Journal of Solid-State Circuits, vol. 35, no. 1, pp. 33-44, January 2000
```

---

## p.61

![p.61](pages/p61.png)

```text
Voltage Multistage Transconductance Amplifier Topologies
For LV Power Supply.
•  Good voltage gain can be obtained using cascode stages.  But these stages
are not amenable for LV power supply.
•  Under LV conditions, high voltage can be obtained using cascade amplifiers.
That is growing horizontally, rather than vertically.
•  Direct Cascade of simple (inverting) stages gives the required voltage gain
without control of poles and zeroes.
•  Dynamic behavior for optimal performance requires feedback (and 
feedforward) circuits.
Analog & Mixed-Signal Center (AMSC)
```

---

## p.62

![p.62](pages/p62.png)

```text
First Approach:  Direct Cascade
0
V
2
m
g
1
m
g
CL
in
V
Symbolic Representation
P
C
i
V
0
V
1
M
2
M
x
V
1
b
I
2
bI
(a)
i
V
1
M
1
b
I
2
b
I
P
C
2
M
x
V
(b)
Two Possible Implementations
02
01
2
m
1
m
L
02
p
p
01
p
2
02
01
L
p
01
p
02
L
L
p
2
m
1
m
in
0
g
g
g
g
)
o
(
H
C
g
  ,  
C
g
at
 
located
 
are
 
poles
 
The
s
g
g
C
C
g
C
g
C
s
1
C
C
/
g
g
)s(
V
)s(
V
)s(
H
2
1
=
=
ω
=
ω
+






+
+
+
≅
=
P
C
Analog & Mixed-Signal Center (AMSC)
```

---

## p.63

![p.63](pages/p63.png)

```text
How do you bring one pole close to the origin?
-Use feedback
0
V
2
m
g
1
m
g
L
C
in
V
p
C
1
m
C
Neglect Cp (i.e., Cp<<Cm1)
(
)
(
)
1
m
L
02
01
L
02
L
2
m
p
L
1
m
L
01
2
1
m
L
1
m
2
m
1
m
in
0
C
C
/
g
g
C
/
g
C
/
g
C
C
/
C
C
g
s
s
C
C
/)
sC
g
(
g
)s(
V
)s(
V
)s(
H
+
+
+
+
+
−
=
=
1
m
2
m
z
02
01
2
m
m1
p
p
V
1
m
01
2
m
02
1
m
01
p
L
02
2
m
p
C
g
RHP
 
at the
 
zero
 a 
is
 
news
 
bad
 
The
gain
 
 voltage
DC
 
Large
     
g
g
/
g
g
H(o)
stability
for 
 
Good
      
          
          
:
 that
is
 
news
 
good
 
The
A
1
C
g
g
g
C
g
  
and
  
C
/)
g
g
(
:
at
 
located
ely 
approximat
 
are
 
poles
 
The
1
2
1
02
1
2
=
ω
=
ω
<<
ω






=






≅
ω
+
≅
ω
Analog & Mixed-Signal Center (AMSC)
```

---

## p.64

![p.64](pages/p64.png)

```text
Now we will use a feedforward circuit to cancel the zero at the RHP.
This will impact the complexity and performance of the design.
1
m
g
mf
g
)s(
H
=
02
01
2
m
1
m
L
1
m
2
2
m
1
m
g
g
g
sC
C
C
s
g
g
+
+
−
=
This can be extended to higher-order systems, let us consider first a
third-order system.
Analog & Mixed-Signal Center (AMSC)
0
V
1
m
C
1
m
g
2
m
g
mf
g
in
V
L
C
No zero
(
)
(
)
1
m
L
02
01
L
02
L
2
m
p
L
1
m
L
01
2
1
m
L
1
m
2
m
1
m
in
0
C
C
/
g
g
C
/
g
C
/
g
C
C
/
C
C
g
s
s
C
C
/)
sC
g
(
g
)s(
V
)s(
V
)s(
H
+
+
+
+
+
−
=
=
Now the corresponding H(s) becomes:
Recall that before applying the feedforward we had:
```

---

## p.65

![p.65](pages/p65.png)

```text
1
mf
g
1
m
g
1
m
C
i
V
0
V
2
m
C
2
m
g
3
m
g
2
mf
g
CL
Three-stage amplifier topology with NGCC
(
)
(
)
(
)
2
m
1
m
L
3
2
m
1
m
2
m
2
mf
3
m
2
1
m
3
m
2
m
03
02
01
2
m
1
m
1
m
1
mf
2
m
2
m
2
mf
1
m
3
m
2
m
1
m
i
0
C
C
C
s
C
C
g
g
g
s
C
g
sg
g
g
g
C
C
g
g
C
g
g
sg
g
g
g
)s(
V
)s(
V
)s(
H
+
−
+
+
+
−
+
−
+
=
=
2
m
1
m
L
3
2
m
1
m
3
m
2
1
m
3
m
2
m
03
02
01
3
m
2
m
1
m
i
0
2
m
mf2
1
m
mf1
C
C
C
s
C
C
g
s
C
g
sg
g
g
g
g
g
g
)s(
V
)s(
V
)s(
H
,
g
g 
and
 
g
g 
making
By 
+
+
+
−
=
=
=
=
Analog & Mixed-Signal Center (AMSC)
Nested Gm-C Compensation Amplifier.
```

---

## p.66

![p.66](pages/p66.png)

```text
3
0
V
V0
1
m
01
1
m
3
m
2
m
03
02
01
03
02
01
3
m
2
m
1
m
1
m
1
m
0
1
1
mi
mi
i
L
2
m
3
m
2
m
3
2
2
m
2
m
2
1
m
1
m
1
02
03
01
2
m
3
m
1
m
0
3
2
2
2
1
0
0
A
A
1
 
C
g
C
g
g
g
g
g
g
g
g
g
g
g
C
g
A
f
P
at
 
located
 
is
 
pole
dominant 
 
 that the
Note
C
g
f
  ;  
C
C
g
g
f
f
  ,  
C
g
f
C
g
GB
f
  
and
  
g
g
g
g
g
g
A
f
f
s
f
s
1
 
f
A
s
1
A
-
H(s)
as
 written 
be
can 
 
H(s)
 
This
2






=
=
=
=
=
=
=
=
=
=








+
+






+
=
Analog & Mixed-Signal Center (AMSC)
```

---

## p.67

![p.67](pages/p67.png)

```text
1
2
3
1
2
3
1
m
C
2
m
C
3
m
C
1
m
g
2
m
g
3
m
g
mf
g
4
m
g
−
i
V
0
V
1
m
C
2
m
C
3
m
C
0
V
i
V
1
m
g
2
m
g
3
m
g
mf
g
4
m
g
−
i
V
0
V
1
m
g
2
m
g
mf
g
1
m
C
(a)  Multipath nested miller compensation topology.
FF
(b) An abstract model for the amplifier proposed by
Castello, et.al.
(c ) The amplifier with multipath miller zero
cancellation.
Multipath Nested Miller Compensation Technology
Potential Feedforward Schemes: An Amplifier Topologies Re-Visit.
Analog & Mixed-Signal Center (AMSC)
```

---

## p.68

![p.68](pages/p68.png)

```text
i
V
0
V
1
m
g
2
m
g
3
mf
g
1
m
C
3
m
g
4
m
g
2
mf
g
1
mf
g
2
m
C
3
m
C
CL
Four stage amplifier topology with NGCC         (Fan You et al)
Let Us Now Compare Several Four-Order Topologies
(
)
mi
mi
i
3
m
2
m
3
m
2
m
3
2
4
3
2
3
3
2
2
2
1
0
1
3
3
2
2
1
1
0
g
C
f
1
  ,  
g
g
C
C
f
f
1
 
          
f
f
f
1
a
  ,  
f
f
1
a , 
f
1
a
  
          
A
GB
P
  
          
s
a
s
a
s
a
1
 
P
s
1
A
)s(
H
=
=
=
=
=
=
+
+
+






+
−
=
(
)
ly.
respective
 
factors,
ion 
normalizat
frequency 
 
and
current 
 
are
 
f 
and
 
I
         
C
g
f
  ,  
C
C
  ,  
f
f
1
I
V
V
P
         
n
Comsumptio
Power 
    
f/
f
1
f
f
GB
f
   
,
   
f
f
f
f
n
n
L
mi
i
i
L
mi
i
1
n
1
i
n
i
i
n
ss
DD
3
2
2
4
1
4
3
2
1
=
α
=
α






∑
α
+
−
=
•
−
>
=
≤
<
<
−
=
```

---

## p.69

![p.69](pages/p69.png)

```text
Comparison of Several Topologies.
0
0
1
1
4
3
2
1
0
mi
mi
i
oi
mi
i
3
3
2
2
1
1
3
3
2
2
1
0
i
0
A
GB
A
f
P
  , 
k
k
k
k
A
Where
C
g
f
   
and
   
1,3
i , 
g
g
k
   
          
,  
)
s
a
s
a
s
a
)(1
P
/
s
1(
s
b
s
b
s
b
1
A
)s(
V
)s(
V
=
=
=
=
=
=
+
+
+
+
−
−
−
−
=
Comparison of Polynomial Coefficients for Four Stage NMC and NGCC Amplifier.
Ph(s)
NMC
NGCC
NMC
NGCC
Z(s)
a1
a2
a3
b1
b2
b3
(
)
4
m
2
m
3
m
2
m
2
m
4
m
g
g
C
g
C
g
−
(
)
4
m
3
m
2
m
3
m
2
m
3
m
2
m
4
m
g
g
g
C
C
g
g
g
−
−
2
m
2
m
g
C
3
m
2
m
3
m
2
m
g
g
C
C
4
m
3
m
2
m
L
3
m
2
m
g
g
g
C
C
C
4
m
3
m
2
m
L
3
m
2
m
g
g
g
C
C
C
4
m
3
m
g
C
0
0
0
4
m
3
m
3
m
2
m
g
g
C
C
4
m
3
m
2
m
3
m
2
m
1
m
g
g
g
C
C
C
Design
Complex
Simple 
Analog & Mixed-Signal Center (AMSC)
```

---

## p.70

![p.70](pages/p70.png)

```text
i
V
0
V
1
m
g
2
m
g
mfn
g
1
m
C
mn
g
1
gmn +
n 
Level
2 
Level
2
mf
g
1
mf
g
1 
Level
2
m
C
mn
C
1
mf
g
1
m
g
)s(
A
1
m
C
i
V
0
V
Conceptual multistage amplifier topology with NGCC.
Abstract model.
Nested Gm-C Compensation (NGCC) Nth-Order
Analog & Mixed-Signal Center (AMSC)
```

---

## p.71

![p.71](pages/p71.png)

```text
i
V
0
V
1
m
G
2
m
G
1
mf
G
1
m
C
i
V
out
V
dd
V
ss
V
1
m
g
1
b
V
2
b
V
2
m
g
12
M
22
M
21
M
1
Mf
1
mf
g
13
M
14
M
11
M
(a)  Representation
(b)  Transistor Level
How to Implement a Positive Gm?
M22.
 
 to
parallel
in 
    
          
          
          
r
 transisto
PMOS
 a 
add
 
and
 
M21
 
Remove
  , 
G
G
 
If
   
current.
 
additional
 
provide
 
 to
M21
    
          
          
          
 
add
 then 
,
current 
 
Mf1
current
 
M22
  , 
G
G
 
If
   
1
Mf
G
    
g
g
  , 
22
M
21
M
G
    
g
g
  , 
14
M
11
M
G
    
1
mf
m2
1
mf
m2
1
mf
2
m
mM22
2
m
1
m
mM11
1
m
>
•
>
>
•
⇒
=
−
⇒
=
−
⇒
Analog & Mixed-Signal Center (AMSC)
```

---

## p.72

![p.72](pages/p72.png)

```text
dd
V
ss
V
1
m
g
2
m
g
3
m
g
3
M
5
M
4
M
−
V
+
V
1
m
C
2
m
C
3
m
C
out
V
4
m
g
2
mf
g
3
mf
g
3
b
V
2
b
V
1
b
V
1
mf
g
Four stage operational amplifier with NGCC topology
Design Example of a Four-Stage Amplifier
Analog & Mixed-Signal Center (AMSC)
```

---

## p.73

![p.73](pages/p73.png)

```text
Measured Performance of the 4-Stage NGCC Op Amp.
2
2
o
o
0.22mm
          
0.22mm
       
          
          
          
Area
//20pF
10k
    
20
//
10k
        
          
Condition 
 
Load
1.0V
    
          
1.0V
        
          
Supply    
Power 
5.0V
 
          
S
2.5V/
         
          
          
Rate
 
Slew
5.2mV
   
          
5.2mV
  
          
          
Offset    
Input 
58
        
          
60
         
          
Margin    
 
Phase
1.0MHz
 
          
610kHz
        
          
Bandwidth 
Gain 
100dB
          
100dB
     
          
          
Gain      
 
DC
1.40mW
      
0.68mW    
  
n         
Consumptio
Power 
Ω
Ω
±
±
≈
≈
pF
µ
Analog & Mixed-Signal Center (AMSC)
```

---

## p.74

![p.74](pages/p74.png)

```text
0
1
2
3
4
5
6
7
8
1
2
3
4
5
6
7
8
0
20
40
60
80
Phase Margin
Ts*GB
f4/GB
___
-----
phase
Ts
The phase margin and normalized settling time (TsGB) of an
NGCC amplifier vs. f4/GB.
Analog & Mixed-Signal Center (AMSC)
What is the effect of f4 /GB?
How far should one push f4?
•  Trade-off between phase margin versus setting time.
```

---

## p.75

![p.75](pages/p75.png)

```text
*
*
*
*
*
*
*
*
*
*
*
+
+
+
+
+
+
+
+
+
0.5
1
1.5
2
2.5
3
3
3.5
4
4.5
5
5.5
6
6.5
7
7.5
8
NMC
NGCC
Ts*GB
Normalized Power
The normalized power consumption of the NGCC and the NMC amplifiers as
a function of the normalized settling time.
Analog & Mixed-Signal Center (AMSC)
How do the Two Topologies Compare for Power Consumption?
```

---

## p.76

![p.76](pages/p76.png)

![p.76 내장 이미지 1](images/p76_1.png)

```text
Analog & Mixed-Signal Center (AMSC)
More Experimental Results.
```

---

## p.77

![p.77](pages/p77.png)

```text
References
S. Pernici, “A CMOS Low-Distortion Fully Differential Power Amplifier with Double Nested
Miller Compensation,” IEEE J. Solid-State Circuits, Vol. 28, No. 7, pp. 758-763, July 1993.
F. You, S.H.K. Embabi and E. Sánchez-Sinencio, “Multistage Amplifier Topologies with 
Nested Gm-C  Compensation,” IEEE J. of Solid-State Circuits, Vol. 32, No. 12, pp. 2000-2011,
December 1997.
K.N. Leung, P.K. T. Mok, W.-H. Ki, and J. K. O. Sin, “ Three-Stage Large Capacitive Load 
Amplifier with Damping Factor-Control Frequency Compensation, “IEEE J. of Solid-State 
Circuits, Vol. 35, No. 2, pp. 221-230, February 2000
Analog & Mixed-Signal Center (AMSC)
S. Yan and E. Sánchez-Sinencio, Low Voltage Analog Circuit Design Techniques: A 
Tutorial, IEICE Trans. Fundamentals, Vol. E83-A, No. 2 February 2000
E. Sánchez-Sinencio and Andreas G. Andreou, Eds. “ Low-Voltage/Low-Power Integrated 
Circuits and Systems “, IEEE Press, Piscataway, NJ 1999
A. Rodriguez-Vazquez and E. Sánchez-Sinencio, Eds., Special Issue on Low-Voltage and 
Low-Power Analog and Mixed-Signal Circuits and Systems, IEEE Trans. on Circuits and 
Systems I, vol. 42, No. 11, November 1995
```

---

## p.78

![p.78](pages/p78.png)

![p.78 내장 이미지 1](images/p78_1.png)

![p.78 내장 이미지 2](images/p78_2.png)

```text
Conclusions
•
Low power supply and smaller 
size  
technologies require 
new analog circuit techniques
•
Power Consumption and area 
are critical specifications in 
portable equipment, clever 
design methodologies are 
needed. 
Analog and Mixed-Signal Center, TAMU
Joe         Edgar
```
