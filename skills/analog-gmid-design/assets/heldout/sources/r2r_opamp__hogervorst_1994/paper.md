# R. Hogervorst, J. P. Tero, R. G. H. Eschauzier, J. H. Huijsing, A Compact Power-Efficient 3 V CMOS Rail-to-Rail Input/Output Operational Amplifier for VLSI Cell Libraries (IEEE JSSC 29(12), 1994)

- 원본 PDF: `G:\내 드라이브\work\Todoc\논문모음\A Compact Power-Efficient 3 V CMOS Rail-to-Rail Input_Output Operational Amplifier for VLSI Cell Libraries.pdf` (판독 때 쓴 `wt/_heldout/tudelft_0fc1.pdf`와 sha256 같음)
- 사본: `source.pdf` (sha256 `b7dfbdbb4c1ffe9d4bfa0f743a2a61b2137d87e319316c7d3db225168b944e39`)
- 웹 출처: https://repository.tudelft.nl/file/File_0fc107fa-6796-4bae-9159-8537a431f171 (TU Delft repository 공개본; IEEE JSSC 29(12) pp.1505-1513, Dec. 1994)
- 그림·표 위치: PDF p.6 = 저널 p.1510 왼쪽 위 Fig. 13 'Overall design of the compact rail-to-rail operational amplifier with Miller compensation' -- 엔진 topology 근거 (바로 아래 Fig. 14 cascoded-Miller 판은 쓰지 않음) · PDF p.8 = 저널 p.1512 Table I 머리(CL·RL)
- 엔진 연결: `assets/heldout/r2r_opamp.topology.json`, `r2r_opamp.sizing_spec.json`, `r2r_opamp.spec_source.md`, `r2r_opamp.topology.md`
- 쪽 수: 9
- 변환: PyMuPDF 텍스트 추출(쪽 단위). 수식·표·그림은 텍스트가 깨질 수 있으니 같은 쪽의 렌더 PNG(`pages/`)로 확인할 것.

---

## p.1

![p.1](pages/p01.png)

![p.1 내장 이미지 1](images/p01_1.png)

```text
IEEE JOURNAL OF SOLID-STATE CIRCUITS. VOL. 29. NO 
I?. DECEMBER 1994 
1 SO5 
A Compact Power-Efficient 3 V CMOS 
Rail-to-Rail Input/Output Operational 
Amplifier for VLSI Cell Libraries 
Ron Hogervorst, John P. Tero, Ruud G. H. Eschauzier, and Johan H. Huijsing 
Abstruct- This paper presents a two-stage, compact, power- 
efficient 3 V CMOS operational amplifier with rail-to-rail input 
and output ranges. Because of its small die area of 0.04 mm', it is 
very suitable as a VLSI library cell. The floating class-AB control 
is shifted into the summing circuit, which results in a noise and 
offset of the amplifier which are comparable to that of a three 
stage amplifier. A floating current source biases the combined 
summing circuit and the class-AB control. This current source 
has the same structure as the class-AB control which provides a 
power-supply-independent quiescent current. Using the compact 
architecture, a 2.6 MHz amplifier with Miller compensation and 
a 6.4 MHz amplifier with cascoded-Miller compensation has been 
realized. The opamps have, respectively, a bandwidth-to-supply- 
power ratio of 4 MHdmW and 11 MHdmW for a capacitive 
load of 10 pF. 
I. INTRODUCTION 
HE design of low-cost mixed/mode VLSI systems re- 
T 
quires compact, power-efficient library cells. Digital li- 
brary cells fully benefit from the continuing down-scaling 
of CMOS processes as well as from the ongoing reduction 
of the supply voltage. The down-scaling of processes results 
in smaller digital cells, because these cells can be designed 
using minimum-length components. The power consumption 
of digital cells is reduced by using a lower supply voltage [I]. 
In contrast to digital cells, analog library cells, such as the op- 
erational amplifier, cannot be designed using minimum-length 
components, for reasons of gain, offset etc. Furthermore, 
a lower supply voltage does not necessarily decrease the 
dissipation of the cell because it often leads to more complex 
designs, resulting in a larger quiescent current. To obtain 
compact, low-voltage, power-efficient analog cells, simple 
library cells with good performance need to be developed. 
A two-stage opamp is very suitable to obtain a compact de- 
sign. Published two-stage rail-to-rail opamps, however, contain 
complex class-AB output stages, which use large die area [2], 
[3]. Moreover, the class-AB control contributes significantly 
to the noise and offset of the amplifier. Very recently, an 
operational amplifier which overcomes the aforementioned 
problems has been described in [4]. This amplifier, however, 
uses a complex floating current source to bias the summing 
Manuscript received June 6. 1994; revised August 22, 1994. 
R. Hogervorst, R. G. H. Eschauzier, and J. H. Huijsing are with Delft 
University of Technology, Faculty of Electrical Engineering, Laboratory for 
Electronic Instrumentation, 2628 CD Delft, The Netherlands. 
J. P. Tero is with Philips Semiconductors, USA Application Specific 
Business Group, Sunnyvale, CA 94088 USA. 
IEEE Log Number 9406269. 
circuit and the class-AB control. The transconductance of 
the input stage varies strongly with the common-mode input 
voltage, which impedes an optimal frequency compensation. 
Moreover, the quiescent current in the output transistors de- 
pends on supply voltage variations. 
In this paper a compact, two-stage, 3 V CMOS opamp with 
rail-to-rail input and output ranges will be presented. Because 
of its small die area, it is very suitable as a VLSI library cell. 
The opamp contains a constant-g,, rail-to-rail input stage and a 
simple class-AB output stage. To save die area, the class-AB 
driver circuit has been incorporated in the folded-cascoded 
summing circuit of the rail-to-rail input stage. The floating 
architecture of the class-AB driver prevents that it contributes 
to the noise and offset of the amplifier. This makes the input 
offset and noise of the amplifier comparable to those of a three- 
stage amplifier. The combined summing circuit and class-AB 
control is biased by a simple floating current source which 
has the same structure as the class-AB control, resulting in a 
quiescent current which is independent of the supply voltage. 
Using the compact opamp, two designs with different types 
of frequency compensation have been realized. The first opamp 
is compensated using the well-known Miller splitting tech- 
nique [5], resulting in a unity-gain frequency of 2.6 MHz. The 
second opamp is compensated by inserting the folded-cascode 
of the summing circuit in the Miller loop, which increases the 
unity-gain frequency up to 6.4 MHz. The compact design of 
the opamps provides a low-power consumption of 0.5 mW at 
a 3 V supply voltage. Both opamps occupy 0.04 mm2. 
The constant-g, rail-to-rail input stage and class-AB driver 
circuit are described in Section I1 and Section 111, respectively. 
Section IV describes the topology of the compact opamp. The 
overall design and the frequency compensation are described 
in Section V. The realizations and measurement results are 
discussed in Section VI. Finally, some conclusions are drawn 
in Section VII. 
11. CONSTANT-GM 
RAIL-TO-RAIL INPUT STAGE 
In order to obtain a reasonable signal-to-noise ratio in low- 
voltage design, the input stage should be able to deal with 
common-mode input voltages from rail-to-rail. This can be 
achieved by placing an N-channel and a P-channel differential 
input pair in parallel, as is shown in Fig. 1 [5]. The N-channel 
input pair, MI - M2, is able to reach the positive supply rail 
while the P-channel input pair, M3 - M4, is able to reach 
00 18-9200/94$04.00 0 1994 IEEE
```

---

## p.2

![p.2](pages/p02.png)

![p.2 내장 이미지 1](images/p02_1.png)

```text
1506 
IEEE JOURNAL OF SOLID-STATE CIRCUITS, VOL. 29, NO. 12, DECEMBER 1994 
VDD 
vss 
Fig. 1. 
voltage is larger than tibp + Si,,, + 21 is,, . 
Common-mode input range of the rail-to-rail input stage. The supply 
M D  
vss 
Fig. 2. 
voltage is smaller than \is&, 
+ lisn + 21i1.,,t. 
the negative supply rail. This input stage requires a supply 
voltage of at least: 
Common-mode input range of the rail-to-rail input stage. The supply 
where V,, 
and Vgsp are the gate-source voltage of an N -  
channel and the gate-source voltage of a P-channel transistor, 
respectively. Vdsat 
is the voltage across a current source which 
is necessary to ensure that it operates as a current source. If 
the supply voltage is below Kup,mi,, the input stage ceases to 
operate in the middle of the common-mode input range, as is 
shown in Fig. 2. 
A drawback of the rail-to-rail input stage is that its y,, 
varies by a factor of two over the common-mode input range, 
as shown in Fig. 3. This large variation of the g, 
impedes 
an optimal frequency compensation [5]. An optimal frequency 
compensation requires a constant yln of the input stage. In 
order to obtain a constant y, 
over the common-mode input 
range, the gm at the lower and upper part of the common- 
mode input range has to be increased by a factor of two. Since 
the g, 
of a MOS transistor operating in strong inversion is 
proportional to the square-root of its drain current, the tail- 
current of the actual active input pair could be increased by 
a factor of four. 
This principle is realized in the circuit as shown in Fig. 4 
[6]. The gm-control is implemented by means of two current 
switches, M5 and Mg, and two current mirrors, MG - M7 and 
Mg - MIO, each with a gain of three. The principles of the yTn- 
control can be best understood by dividing the common-mode 
input range into three parts. 
If low common-mode input voltages are applied, i.e., volt- 
ages between VSS and VSS + 1 V, only the P-channel input 
pair operates. The N-channel current switch conducts while 
the P-channel one is off. The N-channel current switch takes 
away the current Irefl and directs it to the current mirror, 
MG - M7, where it is multiplied by a factor three and added 
to  ire^. Since Irefl and Ire= are equal, the tail-current of the 
P-channel input equals 41r,f. 
2.4 
2.2 
2 
1.8 
1.6 
1.4 
1.2 
1 
0.8 
0 
0 5  
1 
1.5 
2 
2.5 
3 
Vcommon 
Fig 3 
..... Rail-to-rail input stage, 
- 
Normalized g1,2 versu? the common-mode inputvoltage for 
Rail-to-rail input stage with three-times current mirrors 
M6 
M7 
M11 
M12 
30/3 
90/3 
90/2 
San 
30/3 
900 
20w 
2ow 
Fig. 4. Rail-to-rail input stage with g?,, -control by three-times current 
mirrors. 
If intermediate common-mode input voltages are applied, 
i.e., voltages between VSS + 1.3 V and VDD - 1.3 V, the 
P-channel as well as the N-channel input pair operate. Now, 
both current switches are off. The result is that the tail currents 
of the N-channel input pair and that of the P-channel input 
pair are equal to Iref. 
If high common-mode input voltages are applied, i.e., 
voltages between VDD - 1  V and VDD, only the N-channel 
input pair operates. The P-channel current switch conducts 
while the N-channel current switch is off. The P-channel 
current switch takes away the current Ires and feeds it into the 
current mirror, MS - MIO, where it is multiplied by a factor 3 
and added to the current Irefl. 
The result is that the tail-current 
of the N-channel input pair equals 41,,f. 
It can be calculated that for each part of the common-mode 
input range the g, 
is given by: 
where p is the mobility of the charge carriers, CO, is the 
normalized oxide capacitance, W and L are the width and 
the length of a transistor, respectively. The subscripts N 
and P refer to an N-channel or P-channel input transistor, 
respecti vel y .
```

---

## p.3

![p.3](pages/p03.png)

![p.3 내장 이미지 1](images/p03_1.png)

```text
HOGERVORST PI d.. A COMPACT POWER-EFFICIENT AMPLIFIER FOR VLSl LIBRARIES 
1507 
From (2) it can be observed that for a constant gm the W’ 
over L ratios of the P-channel and the N-channel input pair 
have to obey the following relation: 
If the ratio ~
~
$
7
 
over p p  differs from its nominal value because 
of process variations, the Q~~ will have an additional variation. 
For example if p , ~  
over ~ i p  
changes about 1S%, the additional 
variation will be approximately 7.5%. 
It can be concluded that the gm is approximately constant 
over the common-mode input range except for two take-over 
ranges, i.e., common-mode input voltages between VSS + 1 
V and L’s~ + 1.3 V and common-mode input voltages 
between VDD - 1.3 V and VDD - 1 V, where the gm varies 
only IS%, as is shown in Fig. 3. In the take-over ranges 
the current through one of the current switches changes 
from 0 to Iref. or vice versa. 
The offset of the rail-to-rail input stage changes over the 
common-mode input range because the N-channel input pair 
and the P-channel input pair have, in general, a different 
offset. This change in offset limits the CMRR of the input 
stage, since it is defined as the change of offset relative to 
the change in common-mode input voltage. To maximize the 
CMRR the change of offset should be spread out over a large 
part of the common-mode input range. In this circuit, the 
change of offset is spread out over the two take-over ranges 
of the current-switches. This allows a relatively large CMMR 
for these types of input stages. 
At supply voltages below 2.9 V both current switches might 
conduct at the same common-mode input voltage. To prevent 
the positive feedback loop, A45 - Mlo, from becoming active. 
Mzg-hl31 are added to the circuit. Each side of the differential 
pair, -4429 - hf30, is connected via a voltage source, vb5 or 
vb6, to either one of the supply-rails. The differential pair, 
M29 - M 3 0  measures the supply voltage. If the supply voltage 
is larger than 2.9 V the gate-voltage of the current switch, M , .  
is biased by M31. At supply voltages lower than 2.9 V, the 
differential pair gradually tums off M8. Thus, the gate-voltage 
of the N-channel current switch moves towards the positive 
supply rail. This means that the current switch is always off at 
supply voltages below 2.9 V. In this way the positive feedback 
loop can never become active. 
The current mirror, A411 - M14, together with the folded 
cascodes, iWlj - M16, form a summing circuit. This summing 
circuit adds the signals coming from the complementary rail- 
to-rail input stage. 
111. RAIL-TO-RAIL 
CLASS-AB OUTPUT STAGE 
To make efficient use of the supply voltage and supply- 
current, an opamp requires class-AB biased output transistors 
connected in a common-source configuration. Moreover, the 
class-AB control should be compact to efficiently use die area. 
The compact class-AB output stage is shown in Fig. S [7]. It 
consists of two common-source connected output transistors, 
M25 and Adz,, 
which are directly driven by two in-phase signal 
currents, Ilnl and Iln2. The floating class-AB control is formed 
by M l g  and Mzo. The stacked diode-connected transistors, 
Fig. 5. Rail-to-rail output stage with floating class-AB control 
1 
IbZ 
I
I
 
. 
Vss 
lb3 
IM 
V M  
lb6 
lb5 
Fig. 6. Two-stage cascaded operational amplifier. 
M23 - M 2 4  and M21 - M22, bias the gates of the class- 
AB transistors M 1 9  and M20, respectively. As was shown in 
the previous section the minimum required supply voltage is 
limited by the demand for a fully rail-to-rail common-mode 
input range. Therefore, two stacked gate-source voltages are 
allowed in the class-AB output stage. 
The floating class-AB control transistors, the stacked diode- 
connected transistors and the output transistors set up two 
translinear loops M20. M21, MZ2, 
and h l l g ,  M23, M24, 
M26, which determine the quiescent current in the output 
transistors. The class-AB action is performed by keeping the 
voltage between the gates of the output transistors constant. 
Suppose the in-phase signal current sources, I i n l  and Iin2, are 
pushed into the class-AB output stage. As a result, the current 
of the P-channel class-AB transistor, M20, increases while the 
current in the N-channel class-AB transistors, M 1 9 ,  decreases 
by the same amount. Consequently, the gate-voltages of both 
the output transistors move up. Thus the output stage pulls 
a current from the output node. This action continues until 
the current through the P-channel class-AB transistor is equal 
to 1t,7. Now, the current of the P-channel output transistor 
is kept at a minimum value, which can be set by W over L 
ratios of the class-AB control transistors. Note that the current 
through the N-channel output transistor is still able to increase. 
A similar discussion can be held when input signals are pulled 
from the class-AB output stage.
```

---

## p.4

![p.4](pages/p04.png)

![p.4 내장 이미지 1](images/p04_1.png)

```text
1508 
IEEE JOURNAL OF SOLID-STATE CIRCUITS, VOL. 29, NO. 12, DECEMBER 1994 
Fig. 7. Three-stage cascaded operational amplifier 
MI2 Vbl 
M21 
1x3 
VDD 
V- 
MI7 
M18 
Vb4 
lb5 
M24 
Fig. 9. 
mirrors which are biased by two separate current sources. 
Compact two-stage opamp. The summing circuit contains two current 
M12 Vbl 
M21 
Ib8 
Both drawbacks can be overcome by adding an intermediate 
circuit to the two stage cascaded opamp, as is shown in Fig. 
gain between the input transistors, MI - M a ,  and the bias 
currents of the class-AB control, Ib6 and I b 7 ,  so the noise 
and offset contribution of Ib6 and Ib7 can be neglected. The 
result is that the noise and offset of the operational amplifier 
lb3 
lM 
V M  
lb5 
is only determined by the input transistors, A 4 1  - M 4 ,  and 
by 
and by Ib3 - IbbJ. The price to pay is more 
die area and a lower unity-gain frequency. In general, more 
stages result in a lower unity-gain frequency of the opamp. If 
nested Miller compensation is used, the unity-gain frequency 
decreases by a factor Of two [5]. The die area is increased 
not only because an additional stage is needed, but also 
because additional capacitors, Cnr3 and C,zfi7 are needed to 
compensate the oPamP. These capacitors, which are normall!, 
of the order of several PFs, OCCUPY considerable die area. 
An alternative way to reduce the noise and offset contribu- 
tion of the class-AB control, without the cost of die area and 
a loss of unity-gain frequency, is to shift the floating class-AB 
V- 
7. The intermediate stage, M 3 1  and M 3 2 ,  increases the current 
- 
Fig. 8. Compact two-stage opamp. The floating class-AB control is biased 
by the cascodes of the summing circuit. 
A drawback of the Class-AB control is that the quiescent 
current of the output transistors depends on supply voltage 
variations. The supply voltage variations are directly put. by 
the gate-source voltages of the output transistors, across the 
finite output impedances of the floating class-AB transistors. 
The result is a power-supply dependent variation of the qui- 
escent current. 
Iv. TOPOLOGY 
OF THE OPAMP 
In the previous sections the rail-to-rail input stage and the 
rail-to-rail class-AB output stage have been described. In this 
section the overall topology of the operational amplifier will 
be described. 
The conventional way to design a two-stage opamp is to 
place the input stage, M1 - &I, and A411 - M l c ,  and the 
class-AB output stage. M l g  - '4426, in cascade, as is shown in 
Fig. 6. The capacitors Cnll and c1,112 can be used to frequency 
compensate the opamp. For reasons of clarity, the g,-control 
of the input stage has been omitted. Although a compact design 
is obtained, this approach has important drawbacks. Firstly, the 
gain of the amplifier decreases because the bias current sources 
of the class-AB control, I,, and Ib:, are in parallel with the 
cascodes, Idla and A116, of the summing circuit. Secondly, 
apart from the input transistors, 
- h14, and A 4 1 1  - A112 
and Ib3 - Ib4 of the summing circuit , also the bias current 
sources of the class-AB control, 
and Ib7, contribute to the 
noise and offset of the amplifier. These bias sources contribute 
significantly to the input offset and noise, because the current 
gain between the bias sources of the class-AB control and the 
drain currents of the input transistors is equal to one. 
control, M l g  and M ~ o ,  
into the summing circuit, AI11 - M 1 6 ,  
as is shown in Fig. 8. The floating class-AB control is biased 
by the cascodes of the summing circuit. Now, the noise and 
offset of the amplifier are mainly determined by the input 
transistors and the summing circuit. This is also the case in 
the three stage amplifier as is shown in Fig. 7. The opamp is 
even smaller than the two-stage cascaded operational amplifier, 
as is shown in Fig. 6, because the bias sources of the claw 
AB control have been eliminated. Note that for reasons of 
simplicity, the C,lrl and C,bl2 have been omitted. 
A drawback of shifting the class-AB control into the sum- 
ming circuit is that the quiescent current of the output transis- 
tors depends on the common-mode input voltage. When the 
common-mode input voltage varies, the tail currents of the 
input pairs, and therefore the currents through the cascodes, 
change. The result is that the bias current of the class-AB 
control, and consequently the quiescent current of the output 
transistors, depends on the common-mode input voltage. This 
problem can be overcome by using a summing circuit with 
two current mirrors, M 1 1  - I d 1 4  and M 1 5  - M 1 8 ,  which are 
biased by two separate current sources, Ib3 and Ib4. as is shown 
in Fig. 9. Both sides of each current mirror are loaded by 
equal common-mode currents, coming from the input stage,
```

---

## p.5

![p.5](pages/p05.png)

![p.5 내장 이미지 1](images/p05_1.png)

```text
HOGERVORST er a/. A COMPACT POWER-EFFICLENT AMPLIFIER FOR VLSI LIBRARIES 
1509 
z 
VDD 
M12 Vbl 
M21 
Ib8 
# 
I 
I 
I
I
 I 
M18 
Vb4 
lb5 
Fig. IO. 
Compact two-stage opamp. The summing circuit contains two 
current mirrors which are biased by one floating current source. 
M1 - M 4 .  Since I,, and I,, have the same value, the output 
current of both current mirrors is equal to Ib3. 
A drawback of the separate biased current mirrors is that 
the bias current sources of the current mirrors contribute to 
the noise of the amplifier because the current gain between the 
current sources and the drain currents of the input transistors 
is equal to one. Mismatch in the bias current sources will also 
contribute to the offset of the amplifier. To overcome these 
problems the current mirrors are biased by a floating current 
source, I63, as is shown in Fig. 10. Because of the floating 
architecture of the current source, it does not contribute to the 
noise and offset of the amplifier [8], [9]. 
As described in Section 111, the class-AB control, and 
therefore the quiescent current in the output transistors, suffers 
from supply voltage variations. To make the quiescent current 
of the output transistors insensitive to supply voltage varia- 
tions, the floating current source should have the same supply 
voltage dependency as the class-AB control. Fig. 11 shows 
the amplifier with a practical realization of such a floating 
current source, 
- ~1428. 
The floating current source has 
the same structure as the floating class-AB control. The value 
of the current source is set by two translinear loops, M11, 
MZ1, M 2 2 ,  1142~ and ~2117, 1Vf23, 11,124, hl27. The mirrors, 
~W11 - M14 and M15 - ,5118, are loaded by the drain currents 
of the input pairs M1 - 
and AI, - M a ,  respectively. These 
drain currents, and consequently the gate-source voltages of 
Mll and kl17, change with the common-mode input voltage. 
If, for example, the common-mode input voltage approaches 
the positive supply rail, the SI,-control circuit increases the 
current of 
and decreases the current of I b 2 .  As a result, the 
gate-source voltage of MI 1 decreases while the gate-source 
voltage of hf17 increases. However, this hardly effects the 
value of the floating current source, Ad27 - M ~ s ,  
because an 
increase of the gate-source voltage of one mirror compensates 
for a decrease in the other mirror. The result is that the current 
of the floating-current source vanes only 5%# over the full 
common-mode input range, as is shown in Fig. 12. 
- M28, has the same 
structure as the class-AB driver circuit, hflg - .bf20, the supply 
voltage dependency of the current mirror compensates for the 
supply voltage dependency of the class-AB driver. The result 
is a quiescent current which is insensitive to supply voltage 
variations. 
Since the floating current source, 
MI2 Vbl 
M21 
lb8 
V 
MI8 
Vb4 
lb5 
Fig 11 
Compact two-stage opamp The floating current source I \  imple- 
mented by means of -1127 and 1Izq 
Floating current source 
o 
O
o
g
:
:
 
08 
a5 
0 
05 
i 
1 5  
2 
25 
3 
Vcommon 
Simulation result of the normalized kalue of the flodting current 
Fig. 12 
source vcrws the common-mode input voltage 
The resulting two-stage topology is compact which makes 
it very suitable as a VLSI library cell. It has an offset and 
noiye which are comparable to those of a three gtage amplifier. 
Moreover, the quiescent current of the operational amplifier is 
insensitive to supply voltage variations. 
v. OVERALL DESIGN AND FREQUENCY 
COMPENSATION 
Using the topology as described in the previous section, a 
compact opamp with Miller compensation has been designed, 
and is shown Fig. 13. The opamp consists of the rail-to-rail 
input stage, M-M4,gm-control, h.l;-n/!10 and M2,-Af31, a 
summing circuit, M 1 1  - M 1 8 ,  and a rail-to-rail class-AB output 
stage, MlY - M26. The floating current source, M 2 7  - M 2 8 ,  
biases the summing circuit and the floating class-AB control. 
The opamp is compensated using the conventional Miller 
technique. The capacitors Cjlrl and C,,I~ around the output 
transistors, M25 and hf26, split apart the poles ensuring a 20 
dB per decade roll off of the amplitude characteristic. The 
conventional Miller splitting shifts the output pole up to a 
frequency of approximately 
Smo 
Wout = - 
CL 
(4) 
where gTRO 
is the transconductance of the output transistors and 
Cr. is the load capacitor. In Fig. 14, a second design of the
```

---

## p.6

![p.6](pages/p06.png)

![p.6 내장 이미지 1](images/p06_1.png)

```text
1510 
IEEE JOURNAL OF SOLID-ST.4TE CIRCUITS, VOL. 29, NO 12. DECEMBER 1994 
Fig. 13. 
Miller compensation. 
Overall design of the compact rail-to-rail operational amplifier with 
Fig. 14. 
cascoded-Miller compensation. 
compact rail-to-rail opamp is shown. This opamp is basically 
the same as the opamp shown in Fig. 13, except for the 
frequency compensation scheme. This opamp is compensated 
by including the cascode stages,  MI^ and M 1 6 ,  in the Miller 
loops. This compensation technique shifts the output pole to 
a frequency of approximately 
Overall design of- the compact rail-to-rail operational amplifier with 
( 5 )  
C,\I 
gmo 
J,,t 
= ~ 
- 
CGS.out CL 
where C,tf and C G S . , ~ ~  
are the total Miller capacitor and 
the total gate-source capacitance of the output transistor, 
respectively. 
The output pole in (3, and therefore the unity-gain fre- 
quency of the cascoded Miller compensation, is a factor 
C , ~ ~ / C G S , , ~ ~  
larger than the output pole in (4). In the opamp as 
shown in Fig. 14, this ratio is chosen to be about 2.5, resulting 
in a unity-gain frequency of the compact opamp with cascoded 
Miller compensation which is about 2.5 times higher compared 
to the opamp with conventional Miller compensation. 
VI. REALIZATIONS 
AND MEASUREMENT RESULTS 
The opamps have been realized in a 1 pm BiCMOS process. 
The N-channel transistors and the P-channel transistors have 
threshold voltages of 0.64 V and -0.75 V, respectively. The 
micrograph of the compact opamp with Miller compensation 
and the micrograph of the opamp with cascoded-Miller com- 
pensation are shown in Fig. 15. A Bode plot of the compact 
opamp with Miller compensation is shown in Fig. 16. The 
opamp has a unity-gain frequency of 2.6 MHz, with a load 
capacitor of 10 pF. The unity-gain phase margin is 66'. Fig. 
(b ) 
Fig. 15. 
Miller compensation. (b) cascoded-Miller compensation. 
Micrograph of the compactrail-to-rail operational amplifier with (a) 
16 shows the Bode plot of the compact opamp with cascoded 
Miller compensation. The opamp has a unity-gain frequency of 
6.4 MHz and a phase margin of 530, with the same capacitive 
load of 10 pF. To compare the amplifiers, the following figure 
of merit is used: 
F=-1 psup 
CL=lOpF 
(6) 
where B is the unity-gain frequency of the opamp, Psup is 
the quiescent dissipation and CL is the load capacitor [lo]. 
The figure of Merits of the opamp with Miller compensation 
and that of the opamp with cascoded-Miller compensation are 
4 and 11 MHz/mW, respectively, for a capacitive load of 10 
pF. It can be concluded that the opamp with cascoded-Miller 
compensation uses the power about 2.5 times more efficiently, 
with respect to bandwidth than the Miller compensated opamp. 
Fig. 17 shows the small signal step response of the opamp 
with Miller and cascoded-Miller compensation, respectively. 
The opamp with Miller compensation responds to small- 
signals within 1% of the final value in 220 ns, for a load 
of 10 pF and a step of 100 mV. The opamp with cascoded 
Miller compensation has a small signal-settling time 180 ns, 
for the same accurracy of 1%, capacitive load and step. The 
large signal step response of the opamps is shown in Fig. 18. 
B
```

---

## p.7

![p.7](pages/p07.png)

![p.7 내장 이미지 1](images/p07_1.png)

```text
HOCERVORST er al.: A COMPACT POWER-EFFICIENT AMPLIFIER FOR VLSl LIBRARIES 
1511 
a 
NETWORK 
A: REF 
8: REF 
0 MKR 
2 600 9 5 8 . 6 4 7  Hz 
60.00 
250.0 
T/R 
- 2 4 8 . 1 9 8 m  
d 8  
[ 
dE 
1 
deg 
1 
8 
- 1 1 4 . 2 9 1  
deg 
I 
I 
I
l
l
 
I 
I 
I l l  
I 
.a, 
r 
U 
6 
a
1
 
D I V  
OIV 
START 
l o o  ooo.ooo nz 
D I V  
D I V  
START 
100 000.000 HZ 
10.00 
50.00 
STOP 
20 000 000.000 HZ 
10.00 
50 00 
STOP 
20 000 000.000 Hz 
RBW: 
100 H Z  ST: 4 3 . 1  sec RANGE: R--10. 
T--1OdEm 
RBW: 
300 HZ ST: 1 4 . 3  sec RANGE: R--10. 
T- 
O d E m  
(a) 
(b) 
Fig. 16. Bode plot of the compact rail-to-rail operational amplifier with (a) Miller compensation, and (bj caacoded-Miller compensation 
100 
ns/dlv 
(a) 
(b) 
Fig. 17. 
Miller compensation. (y-axis scale = 10 mVldiv). 
Small-signal step response (lLtv,, = 100 mV) of the compact rail-to-rail operational amplifier with (a) Miller compensation and (b) cascoded 
The 1% large-signal settling time for the compact opamp with 
Miller compensation is 440 ns, for a capacative load of 10 
pF and a step of 1 V. The 1% large-signal settling time for 
the compact opamp with cascoded Miller compensation is 275 
ns, for the same capacitive load and step. It can be concluded 
that the compact opamp with cascoded Miller compensation 
is faster than that with the Miller compensation. 
From Fig. 18 it can be observed that the slew-rate of the 
opamps change by a factor of two. As was explained in Section 
11, in the intermediate common-mode, input voltage range in 
both input pairs are active. At the upper and lower part of the 
common-mode input range, the tail current of the actual active 
input pair is increased by a factor of four. Thus, in the outer 
parts of the common-mode input range, there is two times as 
much current to charge the compensation capacitor as there 
is in the intermediate part of the common-mode input range. 
Therefore, slew-rate changes by a factor of two. The slew-rate 
of the compact opamp with Miller compensation is 2 V/ps, 
when the common-voltage is in the range of VSS + 1.3 V and 
VDD - 1.3 V. It is 4 V/ps when the common-voltage is in 
the range of VSS and VSS + 1 V or in the range of VDD - 1 
V and VDD. The slew-rate of the compact opamp with Miller 
compensation is 4 V/ps. when the common-voltage is in the 
range of VSS + 1.3 V and VDD - 1.3 V. It is 8 V/pm when 
the common-voltage is in the range of VS, and Ifss + 1 V or 
in the range of VDD - 1 V and VDD. 
At high output currents, the cascoded-Miller compensation 
could give rise to peaking [ 111. However, at the maximum 
output current of this opamp, which has a value of 3 mA, 
the peaking is negligible. If the operational amplifier has to 
drive output currents much larger than 3 mA, the amplifier 
with Miller compensation should be used. 
A list of specifications is given in Table I. The minimum 
supply voltage is 2.5 V. At this voltage both opamps dissipate 
only 0.45 mW. At supply voltages between 2.5 and 2.9 V 
the opamp is able to deal with common-mode voltages in the 
range from L& 
- 0.4 V to VDD - 1.4 V. At supply voltages 
above 2.9 V, the opamps are able to deal with common-mode 
input voltages from rail-to-rail, or even beyond the rails. The 
common-mode input range is from VSS - 0.4 V to ID, + 0.5 
V. The maximum supply voltage is 6 V and is determined 
by the process. The gain of both opamps is approximately 
85 dB. The gain can be increased by applying gain boosting 
techniques to the cascodes M14 and MI6 of the amplifiers as 
shown in Figs. 13 and 14 [12]. The offset of both opamps 
is about 5 mV, which is comparable to that of three-stage 
operational amplifiers. The offset can be reduced, to values 
of about 2 a 3 mV, by increasing the area of the input 
transistors and by using common-centroid layout structures. 
The CMRR of the opamps is determined by the change of 
offset relative to the change in common-mode input voltage. 
The offset changes gradually during the take-over ranges, i.e.,
```

---

## p.8

![p.8](pages/p08.png)

![p.8 내장 이미지 1](images/p08_1.png)

```text
1512 
IEEE JOURNAL OF SOLID-STATE CIRCUITS, VOL. 29, NO. 12, DECEMBER 1994 
840.000 ns 
200 
nS/dlv 
(a) 
(b) 
Fig. 18. 
compensation (y-axis scale = 200 mV/div). 
Large-signal step response of 
= 1 V) the compact rail-to-rail operational amplifier with (a) Miller compensation; (b) cascoded-Miller 
TABLE I 
MEASUREMENT 
RESULTS 
Vsupply = 3.3 V, Rload = IO kl2, 
Cload = IO pf, TA = 27’C. UNLESS OTHERWISE 
STATED 
lsble I: Measurement rrsults Vsupply=JdV, Rload=lOkQ Cload=lO pF, TA=27’C, 
unless otherwise stated 
Parameft1 
II O W P l  
I OpamP2 
I 
Dk mea 
II 0.04 
10.04 
I mm2 
Supply voltage range 
ll2.5-6 
I2.5.6 
I V  
Quiesant ~
m
~
t
 
11 180 
I180 
IPA 
Offset voltage 
Input mise volage0 IO kHz 
CMRR 
Vc- 
h m  Vs,y 4V IO V s e l V  
andfrom V&l3VmVDD-I3V 
anb from VDD-lV U, VD& 5 
V<-: 
fmm V*l 
V IO Vsfll.3V 
43 
43 
andhmVDD-l 3Vr0VDD-lV 
Ooen-lcm eam 
11 85 
I87 
I dB 
The simple design of the opamp results in a very small die 
area of 0.04 mm2. In spite of its simplicity it shows a very good 
performance. The offset and noise of the compact opamp are 
comparable to that of a three stage amplifier, because the float- 
ing class-AB control is shifted into the summing circuit. The 
summing circuit is biased by a floating current source which 
has the same structure as the class-AB control, resulting in a 
quiescent current which is independent of the supply voltage. 
Using the compact amplifier, two designs have been real- 
ized. The key difference in the designs is in the frequency 
compensation scheme. The first design is compensated using 
Miller compensation. This results in a bandwidth-to-supply 
power ratio of 4 MHz/mW. The second amplifier is compen- 
sated using the cascoded Miller compensation, resulting in a 
bandwidth-to-supply-power ratio of 1 1 MHz/mW. 
REFERENCES 
Unity-gam frequency 
1126 
1 6 4  
I MHr 
Unity-gam phase-margin 
66 
53 
II 
I 
I VIlm 
1 4  
I -  I 
@amp I refers to the compact opamp with Miller compensation 
@amp 2 refers to the compact opamp with casccded Miller compensation 
common-mode voltages between VSS + 1 V and VSS + 1.3 V 
and common-voltages between VDD - 1.3 V and VDD - 1 V, 
of the current switches. Moreover, the change offset is spread 
out over two take-over ranges. In each take-over range the 
offset changes about 2 mV. The result is CMRR of 43 dB in 
the take-over ranges of the current switches. It increases up to 
70 dB, in the other parts of the common-mode input voltage. 
VII. CONCLUSION 
A two stage compact operational amplifier with rail-to- 
rail input and output ranges has been presented. The opamp 
contains a rail-to-rail input stage with a g,-control with three- 
times current mirrors and simple class-AB control. The g, of 
the input stage varies only 15% over the common-mode input 
[l] C. Mead and L. Conway, fnrroduction to VLSI System. Reading, MA: 
Addison-Wesley, 1980. 
121 J. H. Botma er al., “A low-voltage CMOS operational amplifier with 
a rail-to-rail constant-gm input stage and a class AB rail-to-rail output 
stage,” in Proc. ISCAS 93, pp. 1314-1317. 
131 J. N. Babanezhad, “A rail-to-rail CMOS Op amp.” IEEE J. Solid-Slate 
Circ., vol. 23, pp. 1414-1417, 1988. 
141 W.-C. S. Wu, “Digital-compatible high-performance operational ampli- 
fier with rail-to-rail input and output ranges,” IEEE J. Solid-State Circ., 
vol. 29, no. I ,  Jan. 1994. 
IS] J. H. Huijsing and D. Linebarger, “Low-voltage operational amplifier 
with rail-to-rail input and output ranges,” IEEE J. Solid-Sfare Circ., vol. 
SC-20, pp. 1144-1 150, Dec. 1985. 
[6] R. Hogervorst et al.. “CMOS low-voltage operational amplifiers with 
constant-gm rail-to-rail input stage,” Analog Integrated Circ. Signal 
Proc., vol. 5, no. 2, pp. 135-146, Mar. 1994. 
[7] D. M. Montecelli, “A quad CMOS single-supply op amp with rail-to-rail 
output swing,” IEEE J. Solid-Stare Cite., vol. SC-21, pp. 1026-1034, 
Dec. 1986. 
[8] R. Hogervorst, J. P. Tero, R. G. H. Eschauzier, and J. H. Huijsing, “A 
compact power-efficient 3V CMOS rail-to-rail input/output operational 
amplifier for VLSI cell libraries,” in Dig. ISSCC ‘94, Feb. 1994, San 
Francisco, CA, pp. 244-245. 
[9] J. H. Huijsing and J. P. Tero, “Combination driver-summing circuit for 
rail-to-rail differential amplifier,” US Pat. Appl. Ser. No. 36774, filed 
Mar. 25, 1993. 
[IO] M. J. Fonderie and J. H. Huijsing, Design of lowvoltage bipolar 
operational amplifiers. 
[ 1 I ]  R. G. H. Eschauzier and J. H. Huijsing, “An operational amplifier with 
multipath Miller zero cancellation for RHP zero removal,” in Proc. 
ESSCIRC , (Seville, Spain), Sept. 1993, pp. 122-125. 
[ 121 K. Bult and G. J. G. M Geelen, “A fast-settling CMOS op amp for SC 
circuits with 90-dB DC Gain,” IEEE J. Solid-Stare Circ., vol. 25, pp. 
Norwell, MA: Kluwer, 1993, p 171. 
range. 
1379-1383, Dec. 1990.
```

---

## p.9

![p.9](pages/p09.png)

![p.9 내장 이미지 1](images/p09_1.png)

```text
HOGERVORST Cf al.: A COMPACT POWER-EFFICIENT AMPLIFIER FOR VLSl LIBRARIES 
1513 
Ron Hogervorst, for a photograph and biography, see this issue, p. 1504 
Ruud G. H. Eschauzier, for a photograph and biography, see this issue, p. 
1504. 
John Tero was born in Northampton, England in 
1944 and received the B.Sc. degree in physics from 
the University of Leicester in 1966, and the M.Sc. 
degree in electronic devices from the University of 
London in 1970. 
He joined Hawker Siddeley Dynamics in 1966 
and worked on satellite attitude control and propul- 
sion systems. He joined Plesset Research in 1972 
and designed high frequency integrated circuits for 
mobile radio and radar applications in both sil- 
icon and gallium arsenide technologies. In 1979 
Johan H. Huijsing, for a photograph and biography, see this issue, p. 1504. 
he moved to Ferranti Semiconductors to lead a group manufacturing and 
developing RF bipolar power transistors, and qince 1984, he has been with 
Philips Semiconductors in Sunnyvale CA, where he is currently Design 
Engineering Manager for LAN products. As such, he is involved in the 
development of wired and wireless LAN circuits in bipolar. CMOS, BiCMOS 
technologies and his current areas of interests are in analog signal processing, 
high speed data recovery and generation and low voltage circuit technique\.
```
