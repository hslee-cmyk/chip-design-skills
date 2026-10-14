# J.-S. Lee et al., A Design Guide of 3-stage CMOS Operational Amplifier with Nested Gm-C Frequency Compensation (JSTS 7(1), 2007)

- 원본 PDF: `G:\내 드라이브\work\Todoc\기술문서\Gm_over_Id\A Design Guide of 3-stage CMOS Operational Amplifier with Nested Gm-C Frequency Compensation.pdf`
- 사본: `source.pdf` (sha256 `05f723d16bf50aae81e164ad9260d930480c0a062d6a9a868e75e8366fc3c2d7`)
- 웹 출처: https://doi.org/10.5573/JSTS.2007.7.1.020 (JSTS Vol.7 No.1 pp.20-27, March 2007). 서지 기록: https://oasis.postech.ac.kr/handle/2014.oak/39479
- 그림·표 위치: Fig. 3 'Circuit diagram of 3-stage NGCC amplifier' = 저널 p.24 = PDF p.5 (오른쪽 단 아래) -- 엔진 topology 근거 · Table 4 설계 요약 PDF p.5 · Table 5 'Summary of simulation results (CL=10pF)'(α=0.3 DC gain 111 dB) = 저널 p.25 = PDF p.6 · 보상식 Eq 8.a/8.b PDF p.4
- 엔진 연결: `assets/library/ngcc_3stage_ff.topology.json`, `ngcc_3stage_ff.sizing_spec.json`
- 쪽 수: 8
- 변환: PyMuPDF 텍스트 추출(쪽 단위). 수식·표·그림은 텍스트가 깨질 수 있으니 같은 쪽의 렌더 PNG(`pages/`)로 확인할 것.

---

## p.1

![p.1](pages/p01.png)

```text
20 
JAE-SEUNG LEE et al : A DESIGN GUIDE OF 3-STAGE CMOS OPERATIONAL AMPLIFIER WITH… 
Manuscript received Sep. 20, 2006; revised Feb. 16, 2007. 
Dept. Electrical and Computer Engineering Pohang University of 
Science and Technology 
San 31, Hyojadong, Pohang, Kyungbuk , 790-784, Korea 
TEL : +82-54-279-5025, FAX : +82-54-279-5026 
E-mail : hjpark@postech.ac.kr 
A Design Guide of 3-stage CMOS Operational Amplifier 
with Nested Gm-C Frequency Compensation 
 
Jae-Seung Lee, Jun Hyun Bae, Ho-Young Kim, Ji-Yong Um, 
Jae-Yoon Sim, and Hong June Park 
 
 
 
 
Abstract—An analytic design guide was formulated 
for the design of 3-stage CMOS OP amp with the 
nested Gm-C(NGCC) frequency compensation. The 
proposed design guide generates straight-forwardly 
the design parameters such as the W/L ratio and 
current of each transistor from the given design 
specifications, such as, gain-bandwidth, phase margin, 
the ratio of compensation capacitance to load 
capacitance. The applications of this design guide to 
the two cases of 10pF and 100pF load capacitances, 
shows that the designed OP amp work with a 
reasonable performance in both cases, for the range 
of compensation capacitance from 10% to 100% of 
load capacitance.  
 
Index Terms—Low voltage OP amp, design guide, 
frequency compensation, nested Gm-C 
I. INTRODUCTION 
As the minimum feature size of CMOS integrated 
circuits has been scaled down to nano-meter regime in 
recent years, the power supply voltage continues to scale 
down. However, the threshold voltage is not scaled down 
proportionally to the supply voltage due to the sub-
threshold leakage problem. Therefore, the design of 
analog circuits is becoming more difficult and 
challenging. The operational amplifier (OP amp), which 
is an important analog building block, is a good example 
to demonstrate the challenges in design of analog circuit 
with the nano-meter CMOS process [1]. Since, the 
conventional cascode structure of the high-gain OP amp 
requires multiple stacks of transistors between power 
supply and ground; it is difficult to design in low-voltage 
environment. As the solution to the design limits of 
cascode structure in low-voltage environment, the 
multistage amplifiers (cascade structure), which achieve 
the high gain by cascading multiple gain stages, have 
been researched. The multistage amplifier is more 
suitable to low-voltage applications, because the 
required number of stacks is less than cascode structure. 
However, since the multistage amplifier consists of 
multiple gain stages, it requires a complex frequency 
compensation scheme to ensure stability. 
There are two representative frequency compensation 
techniques: Nested Miller Compensation (NMC) and 
Nested Gm-C Compensation (NGCC) [2]. Most of the 
frequency compensation techniques are based on two 
major fundamental principles: pole-splitting and pole-
zero cancellation [3]. In the case of NMC, due to the 
stability problem caused by the positive real zero, a 
series resistance to the miller capacitance is used in 
general for CMOS OP amps[4]. The transfer function, 
stability, and phase margin conditions of multistage 
NMC amplifier are complicated to apply analytic design 
methodology. However, for multistage NGCC amplifier, 
a zero removal with feedforward path is applied, which 
makes the transfer function, stability, and phase margin 
conditions relatively simple to apply analytic design 
methodology.  
The design guide of multistage NGCC amplifier, 
proposed in previous paper [1], is not a completely 
systematic design guide. In this paper, a systematic 
design guide of 3-stage NGCC amplifier, which enables
```

---

## p.2

![p.2](pages/p02.png)

![p.2 내장 이미지 1](images/p02_1.png)

```text
JOURNAL OF SEMICONDUCTOR TECHNOLOGY AND SCIENCE, VOL.7, NO.1, MARCH, 2007 
21 
 
 
 
the systematic design of 3-stage NGCC amplifier with 
given design specifications, is proposed. The comparison 
between NMC with series resistance and NGCC will be 
presented in section II. The proposed systematic design 
guide of 3-stage NGCC amplifier will be described in 
section III. In section IV, the simulation results of 3-stage 
NGCC amplifier designed by the proposed design guide 
will be shown. 
II. FREQUENCY COMPENSATION TECHNIQUES 
In this section, two major frequency compensation 
techniques: NMC and NGCC will be briefly introduced, 
and also the comparison of characteristics for both 
techniques will be described. Fig.3 shows three 
frequency compensation techniques for 3-stage OP amps, 
where the dashed-line block represents the 2 stage OP 
amp version of each technique. The frequency 
compensation for 2-stage amplifier is performed by 
using a Miller capacitance. The feedforward current path 
through the Miller capacitance will generate the right-
half-plane (RHP) zero [3], which degrades the phase 
margin. The RHP zero is removed by using a series 
resistance(Rz2 = 1/gm3) to the compensation capacitance, 
as shown in Fig. 1. (b). Also, the GmC frequency 
compensation technique was developed to remove the 
RHP zero, as shown in Fig. 1. (c), by controlling the 
current through the feedforward transconductance 
stage(gmf2) to be the same as the current through the 
Miller capacitance (gmf2 = gm2) [3].  
Table.1 shows the transfer functions of both 2-stage 
and 3-stage amplifiers with the NMC with RZ (Fig.1(b)) 
and NGCC(Fig.1(c)). The stability conditions are listed 
in Table. 2. Table 3 shows the 63.4 o phase margin 
 
 
(a) 
gm2
gm3
Vin
Vout
CL
V2
gm1
Cm1
V1
-
Rz1
Cm2
Rz2
2-stage
 
(b) 
Cm2
gm2
gm3
Vin
Vout
CL
gmf2
V2
gm1
gmf1
Cm1
V1
-
-
-
2-stage
(c) 
Fig. 1. 3-stage frequency compensation topologies: (a) NMC  
(b) NMC with series resistor (c) NGCC. 
 
Table. 1. Transfer functions of 2-stage and 3-stage amplifiers 
with NMC and NGCC. 
 
Transfer Function 
NMC 
with RZ
(2-stage)
1
2
2
2
2
3
1
2
2
2
(1
)
( )
(
)
m
m
m
m
m
L
o
o
m
m
m
L
m
m
C
g g
s g
H s
C C
g g
sC g
s C
C
C
s
g
+
= −
+
+
+
+
 
Condition : 
2
1
Z
m
R
g
=
 
NMC 
with RZ
(3-stage)
1
2
3
1
1
3
2
1
2
2
3
1
2
3
1
2
3
1
2
2
3
1
2
(
)
( )
(
)
m
m
m
m
m
m
m
m
m
o
o
o
m
m
m
m
m
m
m
m
m
L
g g
g
s C g
g
C
g g
H s
g g g
sC g
g
s C C
g
g
s C C C
+
+
= −
+
+
+
+
 
Condition : 
1
2
1
z
m
R
g
=
, 
2
3
2
3
1
1
1
z
m
m
m
z
R
g
g
g
R
=
+
 
NGCC
(2-stage)
1
2
2
1
2
2
( )
m
m
o
o
m
m
L
m
g g
H s
g g
sC g
s C C
= −
+
+
 
Condition : 
1
mf
m
g
g
=
 
NGCC
(3-stage)
1
2
3
2
3
1
2
3
1
2
3
1
2
3
1
2
( )
m
m
m
o
o
o
m
m
m
m
m
m
L
m
m
g
g
g
H s
g g g
sC g
g
s C C
g
s C C C
= −
+
+
+
 
Condition : 
mf i
m i
g
g
=
(
2,1
=
i
) 
 
conditions. For the 3-stage NMC with RZ, it is difficult 
to satisfy the stability condition. However, the 3-stage 
NGCC amplifier has a relatively simple stability
```

---

## p.3

![p.3](pages/p03.png)

```text
22 
JAE-SEUNG LEE et al : A DESIGN GUIDE OF 3-STAGE CMOS OPERATIONAL AMPLIFIER WITH… 
Table. 2. Stability conditions of 2-stage and 3-stage amplifiers 
with NMC and NGCC (
3
m
L
C
C
=
). 
 
Stability Condition 
NMC with RZ 
(2-stage) 
always stable 
NMC with RZ 
(3-stage) 
1
2
2
1
2
3
2
3
2
3
1
1
1
1
1
1
k
k
k
ω
ω
ω
ω
ω
ω ω
⎛
⎞⎛
⎞
+
+
+
>
⎜
⎟⎜
⎟
⎜
⎟⎝
⎠
⎝
⎠
 
where 
m i
i
m i
g
C
ω =
 (
1,2,3
i =
), 
(
1)
m i
i
m i
C
k
C
+
=
 (
1,2,3
i =
) 
NGCC 
(2-stage) 
always stable 
NGCC 
(3-stage) 
3
1
ω
ω
>
 
where 
m i
i
m i
g
C
ω =
 (
1,3
i =
) 
 
Table. 3. Phase margin conditions (63.4
o ) of 2-stage and 3-
stage amplifiers with NMC and NGCC. 
 
Phase Margin Condition (to achieve 63.4 o ) 
NMC with RZ 
(2-stage) 
1
2
2
m
m
L
m
g
C
C
g
=
 
NMC with RZ 
(3-stage) 
too complex to calculate 
NGCC 
(2-stage) 
1
2
2
m
m
L
m
g
C
C
g
=
 
NGCC 
(3-stage) 
1
1
3
m
m
L
m
g
C
k
C
g
=
, 
2
2
2
3
1
2
m
m
L
m
g
k
C
C
k g
= +
, where 
1
k >
 
 
condition(
1
3
ω
ω >
), which can be satisfied rather easily. 
The feedforward transconductance of NGCC amplifier 
can be implemented by a single transistor, so the 
overhead due to the feedforward path is insignificant [1]. 
The 63.4 o phase margin condition is very complex in the 
NMC with RZ, while it is relatively simple in the NGCC. 
From these factors, we can see that the NGCC technique 
is easier to implement in 3-stage amplifiers than the 
NMC with RZ.  
III. DESIGN GUIDE OF 3-STAGE NGCC 
AMPLIFIER 
In this section, a systematic design guide is derived for 
the 3-stage OP amp using the NGCC frequency 
compensation technique. The design specifications 
include the gain-bandwidth product(GB), the ratio(k ) of 
the high frequency pole(
3
ω
) to GB, the phase 
margin(PM), the output loading(CL), and the input 
common-mode voltage range(ICMR).  
1. Stability and Phase Margin 
 
Assuming a dominant pole, the transfer function of 3-
stage NGCC OP amp in Table 1 can be written as  
 
0
2
0
1
2
2
3
( )
1
1
1
1
A
H s
A s
s
s
ω
ω
ω ω
−
= ⎛
⎞⎛
⎞
+
+
+
⎜
⎟⎜
⎟
⎜
⎟⎝
⎠
⎝
⎠
       (1) 
 
where 
0
A  is DC gain and 
i
ω  is equal to 
m i
m i
g
C  for i 
=1, 2, 3. Since 
1
0
/ A
ω
 in (1) represents the dominant 
pole, 
1
ω  is the gain-bandwidth product (GB), which is 
equivalent to product of the DC gain and the dominant 
pole. The dominant pole is generated by the 1st gain 
stage and 
1
m
C
. The stability condition of 3-stage 
NGCC OP amp, given in Table 2, indicates that the 
pole(
3
ω ), generated by the loading capacitance (
L
C ) 
and the 3rd gain stage, should be higher than 
1
ω . The 
frequency relation based on the stability condition can be 
written as 
 
3
1
k
ω
ω
=
               (2) 
 
where k  must be greater than 1 for stability. As 
indicated in (2), k  represents the ratio of the highest 
frequency pole to GB, and it is given as the design 
specification. 
From (1), the phase margin in the unity-gain 
configuration can be written as  
 
2
1
2
2
3
1
90
tan
1
1
GB
PM
GB
ω
ω ω
−
⎛
⎞
⋅
⎜
⎟
⎜
⎟
=
−
⎜
⎟
−
⋅
⎜
⎟
⎝
⎠
o
         (3) 
 
where GB  is the gain-bandwidth product which is 
equal to
1
ω . In order to satisfy the phase margin 
condition of 63.4°, the term given to 
1
tan− should be 
1/2. Therefore, the resulting expression of substituting 
(2) to (3) can be written as  
 
2
1
1
2k
k
ω
ω
+
=
             (4)
```

---

## p.4

![p.4](pages/p04.png)

![p.4 내장 이미지 1](images/p04_1.png)

```text
JOURNAL OF SEMICONDUCTOR TECHNOLOGY AND SCIENCE, VOL.7, NO.1, MARCH, 2007 
23 
 
 
 
(2) and (4) indicate that the poles 
2
ω
 and  
3
ω  
should be higher than 
1
ω  to achieve both stability and 
the 63.4° phase margin. In general, the inequality of 
3
2
1
ω
ω
ω
<
<
 holds. 
 
2. Transconductance of Each Stage 
 
In previous subsections, the values of 
1
ω , 
2
ω , 
3
ω , 
which determine the transfer function of 3-stage NGCC 
amplifier, were calculated using the design specification 
of GB, stability, and phase margin. In this subsection, the 
value of transconductance(
mi
g
) for each stage will be 
calculated from 
1
ω , 
2
ω
, 
3
ω
. Since the loading 
capacitance(
L
C ) is given as a specification, 
3
m
g
 can be 
calculated from 
3
ω  by using 
L
m
C
g
3
3 =
ω
. In order 
to determine the values of 
1
m
g
 and 
2
m
g
, the 
condition of minimizing the sum of products from W/L 
ratio and current of 1st and 2nd stage is used as a 
constraint, which can be written as  
 
2
2
1
2
1
2
1
2
2
2
m
m
D
D
p
ox
n
ox
g
g
W
W
H
I
I
L
L
C
C
μ
μ
⎛
⎞
⎛
⎞
=
+
=
+
⎜
⎟
⎜
⎟
⎝
⎠
⎝
⎠
    (5) 
 
Another constraint is required to calculate the proper 
values of 
1
m
g
 and 
2
m
g
. Since, the sum of 
compensation capacitors is maintained to be less than or 
equal to the loading capacitance(
L
C ) in general, the 
second constraint can be written as 
 
1
2
m
m
L
C
C
C
α
+
=
             (6) 
 
where α is less than or equal to 1. The value of α is 
given as a design specification. Using (2) and (4), (6) can 
be rewritten as  
 
1
2
3
1 2
m
m
m
k
g
g
g
k
k
α
+
=
+
          (7) 
 
Since the value of 
3
m
g
was already obtained, the values 
of 
1
m
g
 and 
2
m
g
can be determined from (5) and (7).  
 
Fig. 2. The graph of two constraints((5) and (7)) to determine 
1
m
g
 and 
2
m
g
. 
 
To get the optimum values of 
1
m
g
 and 
2
m
g
, which 
minimize the cost function of H in (5), (5) and (7) are 
plotted in Fig. 2, as an ellipse and a straight line, 
respectively 
In Fig. 2, when the straight line becomes the 
tangential line to the ellipse, the point of tangency 
marked as dotted line, is the optimum values of 
1
m
g
 
and 
2
m
g
 that minimize the cost function H , which 
can be written as  
 
2
1
3
2
2
(1
2 )
(1
2 )
m
m
n
p
k
g
g
k
k
k
α
μ
μ
+
=
⎛
⎞
+
+
⎜
⎟
⎜
⎟
⎝
⎠
       (8.a) 
2
3
2
2
(1
2 )
(1
2 )
m
m
p
n
k
g
g
k
k
α
μ
μ
+
=
+
+
        (8.b) 
 
3. Current and W/L Ratio of Each Stage 
 
In order to calculate the current and W/L ratio of each 
stage from the transconductance(
mi
g
) values acquired 
from previous subsection, the 
DSAT
V
 values of 
transistors are determined from the specification of the 
input common-mode voltage range(ICMR). The W/L 
ratios of input transistors in the 1st gain stage should be 
large enough to enhance the equivalent input noise 
voltage. Thus, 
DSAT
V
 values of the input transistors in 
the 1st gain stage were set to half of the 
DSAT
V
 values 
of the transistors, composing the active load of input
```

---

## p.5

![p.5](pages/p05.png)

![p.5 내장 이미지 1](images/p05_1.png)

```text
24 
JAE-SEUNG LEE et al : A DESIGN GUIDE OF 3-STAGE CMOS OPERATIONAL AMPLIFIER WITH… 
differential pair and current sources. Besides, the 
DSAT
V
 
values of all the gain-path transistors(
3,2,1
, =
i
gmi
) are 
set to be the same as 
DSAT
V
 of the input transistor of 1st 
gain stage. Then, the ICMR of PMOS differential pair 
with NMOS active load is given by 
 
5
DD
DSAT
TH
ICMR
V
V
V
=
−
−
          (9) 
 
where 
DSAT
V
 is the 
DSAT
V
 value of the input 
transistor in the 1st gain stage. The circuit schematic of 
OP amp is shown in Fig.5. To guarantee that the ICMR 
is greater than 1/3 of supply voltage, the following 
condition should be satisfied. 
 
1 2
5 3
DSAT
DD
TH
V
V
V
⎛
⎞
≤
−
⎜
⎟
⎝
⎠
          (10) 
 
The drain current and W/L of each transistor can be 
calculated from 
j
DSAT
j
m
j
D
V
g
I
.
.
.
5.0
=
 and 
2
)
/
(
. j
D
j
I
L
W
=
. 
)
(
2
. j
DSAT
ox V
C
⋅
μ
 
 
4. Compensation Capacitor 
 
Using (2) and (4), the compensation capacitances can 
be derived from 
 
1
1
3
m
m
L
m
g
C
k
C
g
=
            (11.a) 
2
2
2
3
1
2
m
m
L
m
g
k
C
C
k g
= +
           (11.b) 
 
5. Summary of the Proposed Design Guide 
 
In Table. 4, the proposed design guide is summarized 
and the calculated values of parameters with a given 
specification are presented as a design example. 
IV. SIMULATION RESULTS 
The NGCC 3-stage amplifier shown in Fig. 3 was 
designed using a 0.18μm CMOS process. Power supply 
voltage was set to 1.2V. The design specification was as 
follows ; k = 4, GB=10MHz, PM=63.4˚, ICMR= 0.4V,  
Table. 4. The summary of the proposed design guide. 
Example 
Step 
Equations 
GB = 10MHz, k=4, 
PM=63.4°, CL=10pF, 
ICMR≥VDD/3, α=0.3
Determine 
1
ω  
from GB. 
1
2
GB
ω
π
=
×
 
1
2
10
/sec
Mrad
ω
π
=
×
 
Calculate 
2
ω  
and 
3
ω . 
2
1
1 2k
k
ω
ω
+
=
 , 
3
1
k
ω
ω
=
 
2
2
22.5
/ sec
Mrad
ω
π
=
×
3
2
40
/ sec
Mrad
ω
π
=
×
Calculate 
3
m
g
.
3
3
m
L
g
C
ω
=
⋅
 
3
2.5
m
g
mS
=
 
Calculate 
1
m
g
 
and 
2
m
g
. 
2
1
3
2
2
(1 2 )
(1
2 )
m
m
n
p
k
g
g
k
k
k
α
μ
μ
+
=
⎛
⎞
+
+
⎜
⎟
⎜
⎟
⎝
⎠
 
2
3
2
2
(1
2 )
(1
2 )
m
m
p
n
k
g
g
k
k
α
μ
μ
+
=
+
+
 
1
0.105
m
g
mS
=
 
2
0.186
m
g
mS
=
 
Determine 
DSAT
V
.
1 2
5 3
DSAT
DD
TH
V
V
V
⎛
⎞
≤
−
⎜
⎟
⎝
⎠
 
80
DSAT
V
mV
=
 
Calculate 
D i
I
.
2
m i
DSAT
D i
g
V
I
⋅
=
 (
1,2,3
i =
) 
1
4.2
D
I
A
μ
=
 
2
7.4
D
I
A
μ
=
 
3
100
D
I
A
μ
=
 
Calculate 
i
W
L
⎛
⎞
⎜
⎟
⎝
⎠.
2
2
m i
i
ox
D i
g
W
L
C I
μ
⎛
⎞=
⎜
⎟
⎝
⎠
 
(
1,2,3
i =
) 
1
(
/ )
20
W L
=
 
2
(
/ )
8
W L
=
 
3
(
/
)
105
W
L
=
 
Calculate 
1
m
C
 
and 
2
m
C
. 
1
1
3
m
m
L
m
g
C
k
C
g
=
 
2
2
2
3
1 2
m
m
L
m
g
k
C
C
k g
= +
 
1
1.68
m
C
pF
=
 
2
1.32
m
C
pF
=
 
 
and CL=①10pF, ②100pF. The gate lengths of all 
MOSFETs were set to 0.5um, about 3 times the  
minimum feature size. Fig. 4 shows the simulated 
frequency response when the value of CL and α  were 
set to 10pF and 0.3, respectively. The unity gain 
bandwidth, the phase margin, and the settling time of the 
designed NGCC 3-stage amplifier were 10MHz, 59˚, and 
120nsec, respectively. Fig. 5 shows the simulated step 
responses for the two cases of load capacitances 
(CL=10pF, CL=100pF) when α  was set to 0.3. 
Table 5 shows the performance comparison of the 
designed OP amp for different values of α  with 10pF 
 
 
Fig. 3. Circuit diagram of 3-stage NGCC amplifier.
```

---

## p.6

![p.6](pages/p06.png)

```text
JOURNAL OF SEMICONDUCTOR TECHNOLOGY AND SCIENCE, VOL.7, NO.1, MARCH, 2007 
25 
 
 
 
1
10
100
1k
10k
100k
1M
10M
100M
-225
-180
-135
-90
-45
0
-20
0
20
40
60
80
100
120
 
Phase [Deg.]
Frequency [Hz]
PM=59ٛ
Magnitude [dB]
GBW=10MHz
 
Fig. 4. Simulated frequency response (CL=10pF and 
0.3
α =
). 
 
500.0n
550.0n
600.0n
650.0n
700.0n
0.10
0.15
0.20
0.25
0.30
0.35
0.40
0.45
0.50
0.55
0.60
120nsec.
CL=100pF, α=0.3
Voltage [V]
Time [sec.]
Input
CL=10pF, α=0.3
 
Fig. 5. Simulated step response (CL=10pF, CL=100pF and 
0.3
α =
). 
 
CL. Table. 6 shows the same comparison with 100pF CL. 
When the value of α  is much less than 1, the effect of 
parasitic capacitance becomes significant and it degrades 
the phase margin and increases the settling time. If the value 
of α  is large close to 1, the W/L value of MOSFET in 
each gain stage will be larger as the values of 
1
m
g
 and 
2
m
g
 increase. In addition, power consumption increases, 
as the amount of current required for each gain stage 
increases, and the chip area will be larger due to the 
larger compensation capacitors. Therefore, in the design 
process of the OP amp, α  should be determined 
carefully to optimize the design. 
V. CONCLUSIONS 
In this paper, an analytic design guide of 3-stage NGCC  
Table. 5. Summary of simulation results(CL=10pF). 
Specifications: CL=10pF, k=4, GBW=10MHz, PM=63.4˚, ICMR= 0.4V 
α 
0.1 
0.3 
0.5 
1 
DC gain [dB] 
113 
111 
109 
107 
Phase margin [Deg.] 
53 
59 
59 
60 
GBW [MHz] 
10.4 
10 
9.85 
9.8 
1% settling time [nsec]
165 
120 
102 
100 
Power [uW] 
242 
297 
368 
517 
gm1 [mS] (C/S)* 
0.035/0.031
0.105/0.1 
0.176/0.16
0.351/0.33
gm2 [mS] (C/S)* 
0.062/0.58 
0.187/0.175 
0.312/0.3 
0.624/0.59
gm3 [mS] (C/S)* 
2.5/2.3 
2.5/2.3 
2.5/2.3 
2.5/2.3 
Cm1 [pF] 
0.559 
1.676 
2.793 
5.586 
Cm2 [pF] 
0.441 
1.324 
2.207 
4.414 
sum(W x L) [um2] 
218 
255 
282 
376 
*C : calculation, S:simulation 
 
Table. 6. Summary of simulation results (CL=100pF). 
Specifications: CL=100pF, k=4, GBW=10MHz, PM=63.4˚, ICMR= 0.4V 
α 
0.1 
0.3 
0.5 
1 
DC gain [dB] 
111 
110 
106 
108 
Phase margin [Deg.] 
56 
60 
62 
60 
GBW [MHz] 
9.9 
9.27 
8.64 
9.8 
1% settling time [nsec] 
165 
117 
147 
131 
Power [uW] 
2024 
2490 
5380 
4800 
gm1 [mS] (C/S)* 
0.35/0.36 
1.1/0.9 
1.8/1.65 
3.5/3.2 
gm2 [mS] (C/S)* 
0.62/0.57 
1.8/1.6 
3.1/2.7 
6.2/6 
gm3 [mS] (C/S)* 
25.1/24 
25.1/24 
25.1/24 
25.1/24 
Cm1 [pF] 
5.586 
16.759 
27.931 
55.862 
Cm2 [pF] 
4.414 
13.241 
22.069 
44.138 
sum (W x L) [um2] 
1245 
1694 
1361 
3438 
*C : calculation, S:simulation 
 
OP amp for low-voltage application was proposed. The 
proposed design guide generates straight-forwardly the 
design parameters such as W/L ratio and current of each 
transistor, with the given OP amp design specification of 
gain-bandwidth(GB), the ratio of the highest frequency 
pole to GB, phase margin(PM), output loading(CL), and 
input common-mode range(ICMR), and the ratio of 
compensation capacitors(α ) to the load capacitor. A 3-
stage NGCC OP amp was designed by using the 
proposed design guide. A 0.18μm CMOS process with 
1.2V supply voltage was used in the design. The 
performance variation of the OP amps, depending on the 
ratio of compensation capacitors(α ) to the load capacitor, 
was observed. It was shown that the designed OP amp 
work with a reasonable performance for the range of α  
from 0.1 to 1.0. When the output loading is 10pF and α  
is 0.3, the designed OP amp gave 111dB DC gain, 
10MHz gain-bandwidth, 59˚ phase margin, and 120nsec 
settling time.
```

---

## p.7

![p.7](pages/p07.png)

![p.7 내장 이미지 1](images/p07_1.png)

![p.7 내장 이미지 2](images/p07_2.png)

![p.7 내장 이미지 3](images/p07_3.png)

![p.7 내장 이미지 4](images/p07_4.png)

![p.7 내장 이미지 5](images/p07_5.png)

![p.7 내장 이미지 6](images/p07_6.png)

![p.7 내장 이미지 7](images/p07_7.png)

![p.7 내장 이미지 8](images/p07_8.png)

![p.7 내장 이미지 9](images/p07_9.png)

```text
26 
JAE-SEUNG LEE et al : A DESIGN GUIDE OF 3-STAGE CMOS OPERATIONAL AMPLIFIER WITH… 
REFERENCES 
 [1] Fan You, Sherif H. K. Embabi, Edgar Sanchez-
Sinencio, “Multistage Amplifier Topologies with 
Nested Gm-C Compensation,” IEEE J. Solid-State 
Circuits, vol. 32, pp. 2000-2011, Dec. 1997. 
 [2] R. Eschauzier, and J. Huijsing, Frequency 
Compensation 
Techniques 
for 
Low-Power 
Operational Amplifiers, Boston, MA : Kluwer, 
1995. 
 [3] Ka Nang Leung and Philip K. T. Mok, “Analysis of 
Multistage Amplifier-Frequency Compensation,” 
IEEE Trans. Circuits Syst. I, vol. 48, pp. 1041-
1056, Sep. 2001. 
 [4] Gaetano Palumbo and Salvatore Pennisi, “Design 
Methodology and Advances in Nested-Miller 
Compensation,” IEEE Trans. Circuits Syst. I, vol. 
49, pp. 893-903, Jul. 2002. 
 
 
Jae-Seung Lee was born in Masan, 
Korea, on 1980. He received the B.S.  
degree in Electronic and Electrical 
Engineering from Pohang University 
of 
Science 
and 
Technology 
(POSTECH), Kyungbuk, Korea, in 
2005, where he is currently working 
toward the Ph.D degree in Electronic Engineering. His 
interests 
include 
high-speed 
CMOS 
chip-to-chip 
interface circuits, DLL/PLL circuits, and signal integrity. 
 
Jun Hyun Bae was born in Ui-Seong, 
Korea, on 1981. He received the B.S. 
degree in the Department of Electronic 
and Electrical Engineering from 
Kyung-Pook National University, 
Korea, in 2004 and M.S. degree in 
Electronic 
and 
Electrical 
Engineering from Pohang University of Science and 
Technology (POSTECH), Korea, in 2007, respectively. 
He is currently pursuing the Ph.D. degree in the 
Department of Electronic and Electrical Engineering 
from Pohang University of Science and Technology 
(POSTECH), 
Korea. 
His 
interests 
include 
data 
converters, high-speed interface circuits and ultra-low-
voltage analog circuits. 
Ho-Young Kim was born in Seoul, 
Korea, on 1981, He received the B.S. 
degree from the Department of 
Electrical Engineering and Computer 
Sciences, University of California, 
Berkeley, in 2005. He is currently 
pursuing the M.S. degree in the 
Department of Electronic and Electrical Engineering 
from Pohang University of Science and Technology 
(POSTECH), Korea. 
 
Ji-Yong Um was born in Incheon, 
Korea, on 1983, He received the B.S. 
degree from the Department of 
Electronic and Electrical Engineering 
from Pohang University of Science 
and Technology (POSTECH), Korea, 
in 2006. He is currently pursuing the 
M.S. degree in the Department of Electronic and 
Electrical Engineering from Pohang University of 
Science and Technology (POSTECH), Korea. 
 
Jae-Yoon Sim received the B.S., 
M.S., and Ph.D. degrees in Electronic 
and Electrical Engineering from 
Pohang University of Science and 
Technology, Korea, in 1993, 1995, 
and 1999, respectively. From 1999 
to 2005, he was a Senior Engineer 
at Samsung Electronics, Korea. From 2003, to 2005, he 
was a post-doctoral student with the University of 
Southern California, Los Angeles. In 2005, he joined the 
Faculty of Electronic and Electrical Engineering, Pohang 
University of Science and Technology, Korea, where he 
is currently an Assistant Professor. His research interests 
include PLL/DLL, high-speed links, memory circuits, 
and ultra low-power analog. 
 
Hong June Park received the B.S. 
degree from the Department of 
Electronic 
Engineering, 
Seoul 
National University, Seoul, Korea, 
in 1979, the M.S. degree from the 
Korea Advanced Institute of Science 
and Technology, Taejon, in 1981, and the Ph.D. degree 
from the Department of Electrical Engineering and
```

---

## p.8

![p.8](pages/p08.png)

```text
JOURNAL OF SEMICONDUCTOR TECHNOLOGY AND SCIENCE, VOL.7, NO.1, MARCH, 2007 
27 
 
 
 
Computer Sciences, University of California, Berkeley, 
in 1989. He was a CAD engineer with ETRI, Korea, 
from 1981 to 1984 and a Senior Engineer in the TCAD 
Department of Intel from 1989 to 1991. In 1991, he 
joined the Faculty of Electronic and Electrical 
Engineering, Pohang University of Science and 
Technology (POSTECH), Kyungbuk, Korea, where he is 
currently Professor. His research interests include high-
speed CMOS interface circuit design, signal integrity, 
device and interconnect modeling. Prof. Park is a 
member of IEEK, IEEE and IEICE.
```
