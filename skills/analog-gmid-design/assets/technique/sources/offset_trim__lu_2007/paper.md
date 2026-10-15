# C.-W. Lu, 'An Offset Cancellation Technique for Two-Stage CMOS Operational Amplifiers', IEEE ICICDT 2007

- 원본 PDF: `G:\내 드라이브\work\Todoc\기술문서\ADC\(Ref) An Offset Cancellation Technique for Two-Stage CMOS OPamp.pdf`
- 사본: `source.pdf` (sha256 `2d80a2aa7f5c0bc27220c14ecd42e715f32915c5329d18a10e6aaca15b9485e7`)
- 웹 출처: 찾지 못함 (IEEE ICICDT 2007, 1-4244-0757-5/07; 2026-10-15 웹 검색에서 IEEE Xplore 기록을 찾지 못함)
- 그림·표 위치: PDF p.1 식(1)(2) 보조 Gm 주입 offset·주입 오차; p.2 Fig.2(보조 Gm,aux가 1단 출력(R1 노드)에 전류 주입), 식(6)-(8) 보정 뒤 잔여 offset = (±V_OS2 ± V_OS1)/(G_m1·R_1), 식(9) 주입 오차 ∝ G_m,aux/G_m1, Fig.3·식(10)(주입 소자를 더할 때 부하 전류 균형 W/L 관계); p.3 Table I·II. 클럭·저장 커패시터 동적 기법 자체는 trim 범위 밖
- 엔진 연결: 아직 없음 -- 계획 `docs/01-plan/features/offset-trim.plan.md` 근거표(R-행)에서 인용
- 쪽 수: 3
- 변환: PyMuPDF 텍스트 추출(쪽 단위). 수식·표·그림은 텍스트가 깨질 수 있으니 같은 쪽의 렌더 PNG(`pages/`)로 확인할 것.
- `pages/`·`images/` 는 git 에 없다. 없으면 skill 폴더에서 `python tools/pdf_to_md.py ensure` 로 만든다.

---

## p.1

![p.1](pages/p01.png)

![p.1 내장 이미지 1](images/p01_1.png)

![p.1 내장 이미지 2](images/p01_2.png)

![p.1 내장 이미지 3](images/p01_3.png)

![p.1 내장 이미지 4](images/p01_4.png)

![p.1 내장 이미지 5](images/p01_5.png)

![p.1 내장 이미지 6](images/p01_6.png)

![p.1 내장 이미지 7](images/p01_7.png)

![p.1 내장 이미지 8](images/p01_8.png)

![p.1 내장 이미지 9](images/p01_9.png)

![p.1 내장 이미지 10](images/p01_10.png)

![p.1 내장 이미지 11](images/p01_11.png)

![p.1 내장 이미지 12](images/p01_12.png)

![p.1 내장 이미지 13](images/p01_13.png)

![p.1 내장 이미지 14](images/p01_14.png)

![p.1 내장 이미지 15](images/p01_15.png)

![p.1 내장 이미지 16](images/p01_16.png)

```text
1
  
Abstract—An offset cancellation technique for two-stage 
CMOS operational amplifiers is proposed. The auxiliary 
amplifiers are employed to cancel the offset voltage. The error 
voltage is stored on a capacitor during the cancellation phase and 
is canceled during the normal operation. An experimental 
prototype amplifier implemented in a 0.35-µm CMOS technology 
demonstrates that the offset voltage is reduced to 1.898 mV under 
a clock frequency of 200 KHz. 
 
Index Terms—offset, offset voltage, offset cancellation, 
operational amplifier, op-amp. 
I. INTRODUCTION 
HE CMOS operational amplifier is the most important 
building block of linear CMOS and switched-capacitor 
circuits [1-3, 7]. However, mismatch of the devices causes an 
offset voltage, which limits the high-precision application [4-6]. 
Some methods were proposed to reduce the offset voltage. For 
example, “output offset storage” and “input offset storage” 
techniques measure the offset voltage and store the result on 
capacitors in series with the output/input [7]. The general 
drawback of these two techniques is that they introduce 
capacitors in the signal path, a particularly serious issue in 
op-amps and feedback system [7]. 
To resolve the above issues, an offset cancellation scheme, 
which can isolate the signal path from the offset storage 
capacitors through the use of an auxiliary amplifier, was 
proposed. Fig. 1 shows this conventional architecture of offset 
cancellation where each Gm stage is a differential pair and the R 
stage represents a transimpedance amplifier [7]. Gm1 and R may 
constitute a one-stage op-amp, which is the main amplifier. Gm2 
is an added auxiliary amplifier, which is used to store the offset 
voltage. VOS1 and VOS2 are the input-referred offset voltages for 
the main and auxiliary amplifiers, respectively. After the offset 
cancellation, these two offset voltages will be reduced. The 
total reduced offset voltage, VOS,tot, can be expressed as: 
R
G
V
R
G
V
V
m
OS
m
OS
tot
OS
1
2
2
1
 ,
+
=
.               (1) 
If Gm2 R and Gm1 R are large, then the total offset voltage is very 
small. Upon turning off, S3 and S4 may inject unequal charges 
onto C1 and C2, respectively, creating an error voltage that is 
not corrected. The input-referred offset voltage, which is due to 
the injection error, is expressed: 
 
The author is with the Department of Electrical Engineering, National Chi 
Nan University, Taiwan, R.O.C. (e-mail: cwlu@ ncnu.edu.tw).  
 
V
G
G
V
m
m
inj
OS
∆






=
1
2
 ,
               (2) 
where △V represents a differential injection-induced error 
voltage. To reduce the injection error, the value of Gm2 can not 
be chosen to large. However, VOS,tot will be larger for a smaller 
value of Gm2. Furthermore, the smaller devices of the 
differential pair of the auxiliary amplifier usually cause a larger 
value of the input referred offset voltage, i.e. VOS2. Hence, this 
is a trade off between the offset voltage and the injection error. 
In order to increase the gain for this one-stage amplifier, the 
transimpedance stage should be implemented by a cascode 
configuration. This limits the minimum value of the power 
supply. As the power supply voltage is continued to scale down, 
fewer cascode configuration is used for low voltage supply 
amplifier and more cascade circuits are employed in two-stage 
op-amps. In this work, an offset cancellation technique, which 
can be used in low-voltage two-stage CMOS op-amps, is 
proposed. 
 
 
 
Fig. 1 The conventional architecture of offset cancellation. 
 
II. PROPOSED OFFSET CANCELLATION TECHNIQUE 
A. Architecture 
Fig. 2 shows the proposed offset cancellation architecture 
with a feedback loop consisting of a transimpedance, R1, an 
amplifier, A2, and auxiliary amplifiers, Aaux and Gm,aux. Gm1, R1, 
and A2 form the main two-stage op-amp. Gm1 is a differential 
pair. R1 is the active load of Gm1. Offset voltages, VOS1 and VOS2 
are the input-referred offset voltages for the main and auxiliary 
amplifiers, respectively. During the offset cancellation, the 
switches, S1 and S2, are turned on. A negative feedback loop is 
formed. The input voltage is applied to the non-inverting 
terminals of Gm1 and Aaux. As depicted in Fig. 2, the relation 
between the input and output voltages can be expressed as: 
An Offset Cancellation Technique for Two-Stage 
CMOS Operational Amplifiers 
Chih-Wen Lu
T 
1-4244-0757-5/07/$20.00 ©2007 IEEE
1
ICICDT07
```

---

## p.2

![p.2](pages/p02.png)

![p.2 내장 이미지 1](images/p02_1.png)

![p.2 내장 이미지 2](images/p02_2.png)

![p.2 내장 이미지 3](images/p02_3.png)

![p.2 내장 이미지 4](images/p02_4.png)

![p.2 내장 이미지 5](images/p02_5.png)

![p.2 내장 이미지 6](images/p02_6.png)

![p.2 내장 이미지 7](images/p02_7.png)

![p.2 내장 이미지 8](images/p02_8.png)

![p.2 내장 이미지 9](images/p02_9.png)

![p.2 내장 이미지 10](images/p02_10.png)

![p.2 내장 이미지 11](images/p02_11.png)

![p.2 내장 이미지 12](images/p02_12.png)

![p.2 내장 이미지 13](images/p02_13.png)

![p.2 내장 이미지 14](images/p02_14.png)

![p.2 내장 이미지 15](images/p02_15.png)

![p.2 내장 이미지 16](images/p02_16.png)

```text
2
(
)
[
]
out
aux
m
aux
out
OS
in
m
OS
V
A
R
G
A
V
V
V
G
V
=
−
±
−
±
+
2
1
,
2
1
1
.     (3) 
Thus, 
(
)
aux
m
aux
m
OS
OS
in
aux
m
aux
m
OS
aux
m
auz
OS
in
out
G
A
G
V
V
V
A
R
G
A
A
R
G
V
A
R
G
A
V
V
V
,
1
1
2
2
1
,
2
1
1
1
2
1
,
2
1
±
+
±
≅
−
±
+
=
+
+
       (4) 
Then the output offset voltage is that 
aux
m
aux
m
OS
OS
in
out
G
A
G
V
V
V
V
,
1
1
2 ±
±
=
−
+
.            (5) 
A voltage of Aaux Vout is stored on the storage capacitor C after 
the switches are turned off. The offset voltage referred to the 
main amplifier is therefore given by 
.
,
1
1
1
1
1
1
2
1
1
,






±
±
=
−
=
+
aux
m
m
aux
m
OS
m
OS
m
in
out
tot
OS
G
G
A
R
G
V
R
G
V
R
G
V
V
V
 
        (6) 
If 
aux
m
m
aux
G
G
A
,
1
=
,                  (7) 
then 
(
)
1
2
1
1
,
1
OS
OS
m
tot
OS
V
V
R
G
V
±
±
=
.             (8) 
Gm1R1 is the first stage of the main amplifier. Its gain is usually 
on the order of 100. Hence, the offset voltage due to the device 
mismatch is very small. 
As the conventional offset cancellation, the switch S2 will 
introduce 
an 
injection-induced 
error. 
The 
resulting 
input-referred offset voltage can be expressed as: 
V
G
G
V
m
aux
m
inj
OS
∆






=
1
,
 ,
.                (9) 
To reduce this error, the value of Gm,aux can be chosen to much 
smaller than that of Gm1 without increasing VOS,tot. Form 
Equations (8) and (9), a design summary is made: The device 
sizes of differential pairs of Gm1 and Aaux can be chosen to be 
larger to obtain a better device match so that VOS1 and VOS2 will 
be smaller. Also, a larger value of Gm1 reduces the offset 
voltage due to both the device mismatch and clock 
injection-induced error. The value of Aaux is chosen to be on the 
order of (
)
aux
m
m G
G
,
1
. 
 
 
 
Fig. 2 The proposed offset cancellation architecture. 
 
B. Schematic 
The proposed schematic of the two-stage op-amp with 
cancellation technique is shown in Fig. 3, in which M1~M3, 
M4~M5, M6~M7, M8, and M9~M13 constitute of Gm1, R1, A2, 
Gm,aux, and Aaux, respectively. Gm1 and R1 form the first stage 
amplifier. Both the Gm1 and R1 are differential but Gm,aux is 
single ended. To balance the currents flowing in R1, the sizes of 
Gm,aux and R1 are arranged as: 
5
4
8






=






+






L
W
L
W
L
W
              (10) 
The aspect ratios of the active load are usually designed to be 
much smaller than those of the corresponding differential pair. 
Hence, the transconductance of Gm,aux is much smaller than that 
of Gm1. This results in a great reduction of the injection-induced 
error. Also, the gain of the first stage is easily deigned to be on 
the order of 100. This means that the offset voltages, which are 
due to the device mismatches of Gm1 and Aaux, are also greatly 
reduced. 
Vin
+
Vin
-
S1
S2
C
bias
CCS
RCS
M1
M2
M3
M4
M5
M6
M7
M8
bias
M9
M10
M11
M12
M13
Vout
Aaux
A2
Gm1
R1
Gm,aux
 
Fig. 3 The proposed schematic of the two-stage op-amp with 
cancellation technique. 
III. EXPERIMENTAL RESULTS 
The proposed two-stage op-amp with an offset cancellation 
technique was fabricated using 0.35-µm CMOS technology. 
The device sizes used in the amplifier are shown in Table I. The 
die photograph is shown in Fig. 4. The die area is 125 µm × 140 
µm. Fig. 5 shows the measured input and output waveforms for 
an input of 1 V under a power supply of 3.3 V. The clock 
frequency is 200 KHz. It can be seen that the offset voltage is 
1.898 mV. In this work, the storage capacitor is implemented 
by a small size of MOS transistor. The offset voltage can be 
further reduced by increasing the value of the storage capacitor. 
The performance summary is shown in Table II. 
 
1-4244-0757-5/07/$20.00 ©2007 IEEE
2
ICICDT07
```

---

## p.3

![p.3](pages/p03.png)

![p.3 내장 이미지 1](images/p03_1.png)

![p.3 내장 이미지 2](images/p03_2.png)

```text
3
Table I Device sizes ([µm/µm] for transistors). 
M1                30/2 
M2                60/2 
M3              240/2 
M4              240/2 
M5                5/2 
M6                10/2 
M7              120/2 
M8             40.8/2 
M9                60/2 
M10            120/2 
M11            120/2 
M12              10/2 
M13              10/2 
C                  1 pF 
Rcs             4 KΩ 
Ccs               5 pF 
 
 
Fig. 4 The die photograph of the proposed two-stage CMOS 
op-amp with offset cancellation technique. 
 
Fig. 5 The measured input and output waveforms for an input of 
1 V under a power supply of 3.3 V and 200 KHz clock 
frequency. 
 
Table II Performance summary. 
Process technology 
0.35 µm CMOS 
VDD 
3.3 V 
Capacitive load 
5 pF 
Unity-gain frequency 
10 MHz 
Phase margin 
62° 
Power dissipation 
0.6 mW 
Offset voltage 
1.898 mV 
 
IV. CONCLUSION 
An offset cancellation technique, which can be applied in 
two-stage CMOS op-amps, has been presented. The offset 
voltages and injection-induced error, which are due to the 
device mismatches of the circuit and the switch injection 
respectively, are greatly reduced. An experimental prototype 
two-stage op-amp implemented in 0.35-µm CMOS technology 
demonstrates that the offset voltage is only 1.898 mV under a 
clock frequency of 200 KHz. If the value of the storage 
capacitor is increased, the offset voltage will be further 
reduced. 
ACKNOWLEDGMENT 
The author would like to thank the Chip Implementation 
Center of National Science Council for their support in chip 
fabrication. 
REFERENCES 
[1] 
Fan You, S.H.K. Embabi and Edgar Sanchez-Sinencio, “Low-Voltage 
Class AB Output Amplifiers with Quiescent Current Control,” IEEE 
Journal of Solid-State and Circuits. Vol.33, No.6, pp. 915-920, June 
1998. 
[2] 
John A. Fisher, “A High-Performance CMOS Power Amplifier” IEEE 
Journal of Solid-State and Circuits. Vol. SC-20, No.6, pp. 1200-1205, 
December 1985. 
[3] 
 Joongsik Kih, Byungsoo Chang, Deog-Kyoon Jeong, and Wonchan Kim, 
“Class-AB Large-Swing CMOS Buffer Amplifier with Controlled Bias 
Current,” IEEE Journal of Solid-State and Circuits. Vol. 28, No.12, pp. 
1350-1353, December 1993. 
[4] 
Marcel J. M. Pelgrom, Aad C. Duinmaijer, and Anton P. G. Welbers, 
“Matching Properties of MOS Transistors,” IEEE Journal of Solid-State 
and Circuits. Vol.24, No.5, pp. 1433-1440,October 1989. 
[5] 
Remco J. Wiegerink, Evert Seevinck, and Wim De Jager, “Offset 
Canceling Circuit,” IEEE Journal of Solid-State and Circuits. Vol.24, 
No.3, pp. 651-658, June 1989. 
[6] 
Marcel J.M. Pelgrom, Hans P. Tuinhout and Maarten Vertregt, 
“Transistor Matching in Analog CMOS Applications,” in 1998 Technical 
Digest of International Electron Devices Meeting, pp. 915-918. 
[7] 
Behzad Razavi, Design of Analog CMOS Integrated Circuits, 
McGraw-Hill, 2001, pp. 471- 479. 
 
1-4244-0757-5/07/$20.00 ©2007 IEEE
3
ICICDT07
```
