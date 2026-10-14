# P.E. Allen, CMOS Analog Circuit Design, Lecture 26 - Buffered Op Amps (6/25/14)

- 원본 PDF: 로컬 사본 없음 -- 2026-10-14 웹 출처에서 그대로 받음(aicdesign.org, 저자 P.E. Allen 공개 강의자료)
- 사본: `source.pdf` (sha256 `96bf1056a7bf7cda85223bfb04d2e10526a622a96fb316dde40169c42e6d3539`)
- 웹 출처: https://aicdesign.org/wp-content/uploads/2018/08/lecture26-140625.pdf (저자 공개 강의자료)
- 그림·표 위치: Page 26-4 = PDF p.4 'The Push-Pull Follower as a Buffer'(그림 060706-02) -> pushpull_follower_buffer · Page 26-5 = PDF p.5 'Two-Stage Op Amp with Follower'(그림 060706-03) -> two_stage_ota_sf · Page 26-6 = PDF p.6 'Source-Follower, Push-Pull Output Op Amp' Fig. 7.1-1(회색 Buffer 상자, 아래 Rout ≤ 1000Ω·Av(0)=65dB·IBias=50µA·GB=60MHz·CL=1pF) -> sf_pushpull_output_opamp, 그리고 pushpull_follower_buffer의 부하·레일·스펙
- 엔진 연결: `assets/library/pushpull_follower_buffer.*`, `assets/library/sf_pushpull_output_opamp.*`, `assets/library/two_stage_ota_sf.*` (원문 하나를 세 회로가 같이 쓴다)
- 쪽 수: 27
- 변환: PyMuPDF 텍스트 추출(쪽 단위). 수식·표·그림은 텍스트가 깨질 수 있으니 같은 쪽의 렌더 PNG(`pages/`)로 확인할 것.

---

## p.1

![p.1](pages/p01.png)

```text
Lecture 26 – Buffered Op Amps (6/25/14) 
Page 26-1   
CMOS Analog Circuit Design 
 
© P.E. Allen - 2016  
LECTURE 26 – BUFFERED OP AMPS 
LECTURE ORGANIZATION 
Outline 
• Introduction 
• Open Loop Buffered Op Amps 
• Closed Loop Buffered Op Amps 
• Use of the BJT in Buffered Op Amps 
• Summary 
CMOS Analog Circuit Design, 3rd Edition Reference 
Pages 354-370
```

---

## p.2

![p.2](pages/p02.png)

```text
Lecture 26 – Buffered Op Amps (6/25/14) 
Page 26-2   
CMOS Analog Circuit Design 
 
© P.E. Allen - 2016  
INTRODUCTION 
Buffered Op Amps 
What is a buffered op amp? 
 
Buffered op amps are op amps with the ability to drive a low output resistance and/or 
a large output capacitance.  This requires: 
 
- An output resistance typically in the range of 10  Ro  1000 
 
- Ability to sink and source sufficient current (CL·SR) 
 
Types of buffered op amps: 
 
- Open loop using output amplifiers 
 
- Closed loop using negative shunt feedback to reduce the output resistance of the op 
amp 
+
-
Op Amp
Buffer
Rout
Large
Rout
Small
vIN
vOUT
vOUT’
070430-01
```

---

## p.3

![p.3](pages/p03.png)

```text
Lecture 26 – Buffered Op Amps (6/25/14) 
Page 26-3   
CMOS Analog Circuit Design 
 
© P.E. Allen - 2016  
OPEN LOOP BUFFERED OP AMPS 
The Class A Source Follower as a Buffer 
• Simple 
• Small signal gain ≈ 
gm
gm + gmbs + GL < 1 
• Low efficiency 
• Rout = 
1
gm + gmbs ≈ 500 to 1000 
• Level shift from input to output 
• Maximum upper output voltage is limited 
• Broadbanded as the pole and zero due to the source follower are close so compensation 
is typically not a problem 
 
060118-10
VNBias1
VDD
M1
M2
vIN
vOUT
```

---

## p.4

![p.4](pages/p04.png)

```text
Lecture 26 – Buffered Op Amps (6/25/14) 
Page 26-4   
CMOS Analog Circuit Design 
 
© P.E. Allen - 2016  
The Push-Pull Follower as a Buffer 
• Voltage loss from 2 cascaded followers 
 
Av ≈ 






gm3
gm3 + gmbs3 





gm1
gm1 + gmbs1 + GL  < 1 
• Higher efficiency 
• Rout ≈ 
0.5
gm + gmbs ≈ 250 to 500 
• Current in M1 and M2 determined by: 
 
VGS4 + VSG3 = VGS1 + VSG2 
 
2I6
Kn'(W4/L4) + 
2I5
Kp'(W3/L3) 
 
= 
2I1
Kn'(W1/L1) + 
2I2
Kp'(W2/L2) 
 
Use the W/L ratios to define I1 and I2 from I5 and I6 
• Maximum positive and negative output voltages are limited 
 
 
060706-02
VNBias1
VDD
M1
M2
vIN
vOUT
VDD
VDD
M4
VDD
VPBias1
VDD
M5
M3
M6
+
-
VSG3
I5
I6
+
-
VSG2
+
-
VGS4
+
-
VGS1
I1
I2
```

---

## p.5

![p.5](pages/p05.png)

```text
Lecture 26 – Buffered Op Amps (6/25/14) 
Page 26-5   
CMOS Analog Circuit Design 
 
© P.E. Allen - 2016  
Two-Stage Op Amp with Follower 
 
Power dissipation now becomes (I5 + I7 + I9)VDD 
Gain becomes, 
 
Av = 






gm1
gds2+gds4  






gm6
gds6+gds7  






gm8
gm8+ gmbs8+gds8+gds9  
-
+
vin
M1
M2
M3
M4
M5
M6
M7
VNBias
Cc
CL
I5
I7
060706-03
VDD
M8
M9
vout
I9
```

---

## p.6

![p.6](pages/p06.png)

```text
Lecture 26 – Buffered Op Amps (6/25/14) 
Page 26-6   
CMOS Analog Circuit Design 
 
© P.E. Allen - 2016  
Source-Follower, Push-Pull Output Op Amp 
 
Rout ≈ 
1
gm21+gm22  1000, Av(0)=65dB (IBias=50µA), and GB = 60MHz for CL = 1pF 
Note the bias currents through M18 and M19 vary with the signal. 
vout
VDD
VDD
Cc
-
+
vin
M1
M2
M3
VSS
R1
M5
M6
R1
M7
M8
R1
M13
M14
VSS
VDD
VSS
M22
M21
IBias
M9
M10
M11
M12
M4
M17
M18
M15
M16
M19
M20
Fig. 7.1-1
CL
Buffer
-
+
VSG18
-
+
VSG21
-
+
VGS19
-
+
VGS22
I17
I20
```

---

## p.7

![p.7](pages/p07.png)

```text
Lecture 26 – Buffered Op Amps (6/25/14) 
Page 26-7   
CMOS Analog Circuit Design 
 
© P.E. Allen - 2016  
Compensation of Op Amps with Output Amplifiers 
Compensation of a three-stage amplifier:  
This op amp introduces a third pole, p’3  
(what about zeros?) 
With no compensation, 
  
Vout(s)
Vin(s)  = 
-Avo


s
p’1 - 1


s
p’2 - 1


s
p’3 - 1
 
Illustration of compensation choices:
```

---

## p.8

![p.8](pages/p08.png)

```text
Lecture 26 – Buffered Op Amps (6/25/14) 
Page 26-8   
CMOS Analog Circuit Design 
 
© P.E. Allen - 2016  
Crossover-Inverter, Buffer Stage Op Amp  
Principle:  If the buffer has high output resistance and voltage gain (common source), this 
is okay if when loaded by a small RL the gain of this stage is approximately unity. 
 
• This buffer trades gain for the ability to drive a low load resistance 
• The load resistance should be fixed in order to avoid changes in the buffer gain 
• The push-pull common source output will give good output voltage swing capability
```

---

## p.9

![p.9](pages/p09.png)

```text
Lecture 26 – Buffered Op Amps (6/25/14) 
Page 26-9   
CMOS Analog Circuit Design 
 
© P.E. Allen - 2016  
Crossover-Inverter, Buffer Stage Op Amp - Continued 
How does the output buffer work? 
The two inverters, M1-M3 and M2-M4 are designed to work over different regions of the 
buffer input voltage, vin’. 
Consider the idealized voltage transfer characteristic of the crossover inverters: 
 
Crossover voltage  VC = VB-VA  0 
VC is designed to be small and positive for worst case variations in processing. 
060706-05
VDD
VA
M6 Active
M6 Satur-
ated
M5 Active
M5 Saturated
VB
M1-M3
Inverter
M2-M4
Inverter
0
vin'
M1
M2
M3
M4
M7
vout
VDD
VSS
C2
C1
vin'
M6
M5
RL
vout
VDD
VSS
IBias
```

---

## p.10

![p.10](pages/p10.png)

```text
Lecture 26 – Buffered Op Amps (6/25/14) 
Page 26-10   
CMOS Analog Circuit Design 
 
© P.E. Allen - 2016  
Large Output Current Buffer 
In the case where the load consists of a large capacitor, the ability to sink and source a 
large current is much more important than reducing the output resistance.  Consequently, 
the common-source, push-pull is ideal if the quiescent current can be controlled. 
A possible implementation: 
 
 
 
 
 
If W4/L4 = W9/L9 and W3/L3 = 
W8/L8, then the quiescent 
currents in M1 and M2 can be 
determined by the following relationship: 
 
 
I1 = I2 = Ib 






W1/L1
W7/L7  = Ib 






W2/L2
W10/L10   
When vin is increased, M6 turns off M2 and turns on M1 to source current.  Similarly, 
when vin is decreased, M5 turns off M1 and turns on M2 to sink current. 
VDD
VSS
Ib
Ib
I=2Ib
M1
M2
M3 M4
M5
M6
M7
M8
M9
M10
vin
I=2Ib
vout
070430-07
vin
VDD
VSS
vout
```

---

## p.11

![p.11](pages/p11.png)

```text
Lecture 26 – Buffered Op Amps (6/25/14) 
Page 26-11   
CMOS Analog Circuit Design 
 
© P.E. Allen - 2016  
CLOSED LOOP BUFFERED OP AMPS 
Principle 
 
Use negative shunt feedback to reduce the output resistance of the buffer. 
 
 
• Output resistance 
 
 
ROUT = 
Ro
1 + Av 
• Watch out for when small RL causes Av to decrease. 
• The bandwidth will be limited by the feedback (i.e. at high frequencies, the gain of Av 
decreases causing the output resistance to increase. 
Av
+ -
vIN
vOUT
ROUT
Ro
070430-02
RL
```

---

## p.12

![p.12](pages/p12.png)

```text
Lecture 26 – Buffered Op Amps (6/25/14) 
Page 26-12   
CMOS Analog Circuit Design 
 
© P.E. Allen - 2016  
Two Stage Op Amp with a Gain Boosted, Source Follower Buffer 
 
 
Rout ≈ 
1
gm8K 
Power dissipation now becomes (I5 + I7 + I11)VDD 
Gain becomes, 
 
Av = 






gm1
gds2+gds4  






gm6
gds6+gds7  






gm8K
gm8K+ gmbs8K +GL  
-
+
vin
M1
M2
M3
M4
M5
M6
M7
VNBias
Cc
I5
I7
070430-03
VDD
M11
vout
I11
1:K
M8
M9
M10
Rout
```

---

## p.13

![p.13](pages/p13.png)

```text
Lecture 26 – Buffered Op Amps (6/25/14) 
Page 26-13   
CMOS Analog Circuit Design 
 
© P.E. Allen - 2016  
Gain Boosted, Source-Follower, Push-Pull Output Op Amp 
 
Rout ≈ 
1
K(gm21+gm22)  ≈ 1000
K
  ≈ 100  
Av(0)=65dB (IBias=50µA) 
Note the bias currents through M18 and M19 vary with the signal. 
VDD
Cc
-
+
vin
M1
M2
M3
VSS
M5
M6
M7
M8
R1
M13
M14
VSS
VDD
M21
IBias
M9
M10
M11
M12
M4
M17
M18
M15
M16
M19
M20
Gain Enhanced Buffer
-
+
VSG18
-
+
VSG21
-
+
VGS19
-
+
VGS22
I17
I20
M23
M24
+
VT+2VON
-
vout
1:K
M22
M23
M24
Rout
M25
M26
1:K
070430-04
```

---

## p.14

![p.14](pages/p14.png)

```text
Lecture 26 – Buffered Op Amps (6/25/14) 
Page 26-14   
CMOS Analog Circuit Design 
 
© P.E. Allen - 2016  
Common Source, Push Pull Buffer with Shunt Feedback 
To get low output resistance using MOSFETs, negative feedback must be used. 
Ideal implementation: 
 
Comments: 
•  The output resistance will be equal to rds1||rds2  divided by the loop gain 
•  If the error amplifiers are not perfectly matched, the bias current in M1 and M2 is not 
defined
```

---

## p.15

![p.15](pages/p15.png)

```text
Lecture 26 – Buffered Op Amps (6/25/14) 
Page 26-15   
CMOS Analog Circuit Design 
 
© P.E. Allen - 2016  
Low Output Resistance Op Amp - Continued 
Offset correction circuitry: 
 
 
The feedback circuitry of the two error amplifiers tries to insure that the voltages in 
the loop sum to zero. Without the M9-M12 feedback circuit, there is no way to adjust the 
output for any error in the loop. The circuit works as follows: 
When VOS is positive, M6  tries to turn off and so does M6A. IM9  reduces thus reducing 
IM12. A reduction in IM12 reduces IM8A thus decreasing VGS8A. VGS8A ideally decreases 
by an amount  equal to VOS. A similar result holds for negative offsets and offsets in EA2.
```

---

## p.16

![p.16](pages/p16.png)

```text
Lecture 26 – Buffered Op Amps (6/25/14) 
Page 26-16   
CMOS Analog Circuit Design 
 
© P.E. Allen - 2016  
Low Output Resistance Op Amp - Continued 
Error amplifiers: 
 
 
Basically a two-stage op amp with the output push-pull transistors as the second-stage of 
the op amp. 
 
vin
M1
M2
M3
M4
M5
M6
M6A
vout
VDD
VSS
VBias
+
-
Cc1
A1 amplifier
MR1
070430-05
A2 amplifier
vin
VBias
+
-
M2A
M1A
M5A
M4A
M3A
MR2
Cc2
```

---

## p.17

![p.17](pages/p17.png)

```text
Lecture 26 – Buffered Op Amps (6/25/14) 
Page 26-17   
CMOS Analog Circuit Design 
 
© P.E. Allen - 2016  
Low Output Resistance Op Amp - Complete Schematic 
Short circuit protection(max. output 60mA):  
 MP3-MN3-MN4-MP4-MP5  
 MN3A-MP3A-MP4A-MN4A-MN5A  
Rout  
rds6||rds6A
Loop Gain ≈ 50k
5000 = 10 
RC
R1
RL
CL
CC
C1
gm1
gm6
```

---

## p.18

![p.18](pages/p18.png)

```text
Lecture 26 – Buffered Op Amps (6/25/14) 
Page 26-18   
CMOS Analog Circuit Design 
 
© P.E. Allen - 2016  
Simpler Implementation of Negative Feedback to Achieve Low Output Resistance 
 
 
 
 
 
Output Resistance: 
 
 
Rout = 
Ro
1+LG   
 
where  
 
 
Ro = 
1
gds6+gds7  
 
 
and    
 
 
|LG| = 
gm2
2gm4 (gm6+gm7)Ro 
Therefore, the output resistance is: 
 
 
Rout = 
1
(gds6+gds7)






1 + 






gm2
2gm4 (gm6+gm7)Ro
  
-
+
vin
M1
M2
M3
M4
M5
M6
M7
vout
VDD
VSS
CL
M8
M10
M9
Fig. 7.1-9
1/1
10/1
200mA 10/1
10/1
10/1
1/1
1/1
1/1
10/1
10/1
```

---

## p.19

![p.19](pages/p19.png)

```text
Lecture 26 – Buffered Op Amps (6/25/14) 
Page 26-19   
CMOS Analog Circuit Design 
 
© P.E. Allen - 2016  
Example 26-1 - Low Output Resistance Using Shunt Negative Feedback Buffer 
Find the output resistance of above op amp using the model parameters of KN’ = 
120µA/V2, KP’ = 25µA/V2, N = 0.06V-1 and P = 0.08V-1. 
Solution 
The current flowing in the output transistors, M6 and M7, is 1mA which gives Ro of  
 
Ro = 
1
(N+P)1mA = 1000
0.14  = 7.143kΩ 
To calculate the loop gain, we find that 
 
 gm2 = 2KN’·10·100µA = 490µS 
 
 gm4 = 2KP’·1·100µA = 70.7µS 
and 
 
 gm6 = 2KP’·10·1000µA = 707µS 
Therefore, the loop gain is 
 
|LG| = 490
2·70.7  (0.707+0.071)7.143 = 19.26 
Solving for the output resistance, Rout, gives 
 
Rout = 7.143k
1 + 19.26 = 353 (Assumes that RL is large)
```

---

## p.20

![p.20](pages/p20.png)

```text
Lecture 26 – Buffered Op Amps (6/25/14) 
Page 26-20   
CMOS Analog Circuit Design 
 
© P.E. Allen - 2016  
USE OF THE BJT IN BUFFERED OP AMPS 
Substrate BJTs 
Illustration of an NPN substrate BJT available in a p-well CMOS technology: 
 
Comments: 
• gm of the BJT is larger than the FET so that the output resistance w/o feedback is lower 
• Collector current will be flowing in the substrate 
• Current is required to drive the BJT 
• Only an NPN or a PNP bipolar transistor is available 
n- substrate (Collector)
p- well (Base)
n+ (Emitter)
p+
n+
Emitter
Base
Collector
(VDD)
Collector(VDD)
Emitter
Base
Fig. 7.1-10
```

---

## p.21

![p.21](pages/p21.png)

```text
Lecture 26 – Buffered Op Amps (6/25/14) 
Page 26-21   
CMOS Analog Circuit Design 
 
© P.E. Allen - 2016  
A Lateral Bipolar Transistor 
n-well CMOS technology: 
• It is desirable to have the lateral 
collector current much larger than the 
vertical collector current. 
• Triple well technology allows the 
current of the vertical collector to avoid 
flowing in the substrate. 
• Lateral BJT generally has good 
matching. 
060221-01
p+
n-well
n+
Substrate
E
LC
B
VC
STI
STI
LC
STI
Lateral Collector
Emitter
Base
Vertical
Collector
p+
p+
```

---

## p.22

![p.22](pages/p22.png)

```text
Lecture 26 – Buffered Op Amps (6/25/14) 
Page 26-22   
CMOS Analog Circuit Design 
 
© P.E. Allen - 2016  
A Field-Aided Lateral BJT 
Use minimum channel length to 
enhance beta: 
ßF  50 to 100 depending on the 
process 
  
 
 
 
 
060221-02
p+
n-well
n+
Substrate
B
VC
STI
STI
LC
STI
Lateral Collector Emitter
Base
Vertical
Collector
p+
p+
p+
E
LC
Keeps carriers from
flowing at the surface
and reduces 1/f noise
```

---

## p.23

![p.23](pages/p23.png)

```text
Lecture 26 – Buffered Op Amps (6/25/14) 
Page 26-23   
CMOS Analog Circuit Design 
 
© P.E. Allen - 2016  
Two-Stage Op Amp with a Class-A BJT Output Buffer Stage 
Purpose of the M8-M9 source 
follower: 
1.) Reduce the output resistance 
(includes whatever is seen from the 
base to ground divided by 1+F) 
2.) Reduces the output load at the 
drains of M6 and M7 
 
Small-signal output resistance : Rout ≈ 
r10 + (1/gm9)
 1+ßF
 = 1
gm10 + 
1
gm9(1+ßF)   
  
= 51.6+6.7 = 58.3 where I10=500µA, I8=100µA, W9/L9=100 and ßF is 100 
vOUT(max) = VDD - VSD8(sat) - vBE10 = VDD - 
2KP’
I8(W8/L8)  - Vt ln





Ic10
Is10   
Voltage gain: 
 
vout
vin  ≈ 





gm1
gds2+gds4 





gm6
gds6+gds7 





gm9
gm9+gmbs9+gds8+g10 





gm10RL
1+gm10RL  
Compensation will be more complex because of the additional stages.
M1
M2
M3
M4
M5
M6
M7
vout
VDD
VSS
Cc
CL
IBias
Q10
M11
M12
M13
Fig. 7.1-11
M8
M9
Output Buffer
RL
vin
+
-
```

---

## p.24

![p.24](pages/p24.png)

```text
Lecture 26 – Buffered Op Amps (6/25/14) 
Page 26-24   
CMOS Analog Circuit Design 
 
© P.E. Allen - 2016  
Example 26-2 - Designing the Class-A, Buffered Op Amp 
 
Use an n-well, 0.25µm CMOS technology to design an op amp using a class-A, BJT 
output stage to give the following specifications.  Assume the channel length is to be 
0.5µm. The FETs have the model parameters of KN’ = 120µA/V2, KP’ = 25µA/V2, VTN 
= |VTP| = 0.5V, N = 0.06V-1 and P = 0.08V-1 along with the BJT parameters of Is = 
10-14A and ßF = 50.  
VDD = 2.5V 
VSS = 0V 
GB = 10MHz Avd(0)  2500V/V 
Slew rate  10V/µs 
RL = 500 
Rout  50 
CL = 100pF 
ICMR = +1V to 2V 
 
Solution 
 
A quick comparison shows that the 
specifications of this problem are similar to 
the folded cascode op amp that was designed 
in Ex. 24-4. Borrowing that design for this 
example results in the following op amp. 
 
Therefore, the goal of this example will 
be the design of M12 through Q15 to satisfy 
the slew rate and output resistance 
requirements. 
070430-06
VPB1
M4
M5
Rout
I6
VPB2
I4
I5
VDD
I7
M6
M7
VNB2
M8
M9
M10
M11
+
-
vIN
vOUT
VNB1
I1
I2
M1 M2
M3 I3
CL
VNB1
VPB1
M12
M13
M14
Q15
I12
I15
```

---

## p.25

![p.25](pages/p25.png)

```text
Lecture 26 – Buffered Op Amps (6/25/14) 
Page 26-25   
CMOS Analog Circuit Design 
 
© P.E. Allen - 2016  
Example 26-2 – Continued 
BJT follower (Q15): 
 
SR = 10V/µs  and 100pF capacitor give I15 = 1mA.   
  Assuming the gate of M14 is connected to the gate of M5, the W/L ratio of M14 
becomes 
 
W14/L14 = (1000µA/125µA)160 = 1280 
 W14 = 640µm 
 
I15 = 1mA    
1/gm15 =  0.0258V/1mA = 25.8  
MOS follower: 
To source 1mA, the BJT requires 20µA (ß =50) from the MOS follower (M12-M13).   
Therefore, select a bias current of 100µA for M13.   If the gates of M3 and M13 are 
connected together, then  
 
W13/L13 = (100µA/100µA)15 = 15  
   W13 = 7.5µm 
To get Rout = 50, if 1/gm15 is 25.8, then design gm12 as 
 
1
gm15 = 
1
gm12(1+ßF) 
 = 24.2 
gm12 = 
1
(24.2)(1+ßF) = 
1
24.2·51 = 810µS 
  gm12 and I12     W/L = 27.3 ≈ 30   W12 = 15µm
```

---

## p.26

![p.26](pages/p26.png)

```text
Lecture 26 – Buffered Op Amps (6/25/14) 
Page 26-26   
CMOS Analog Circuit Design 
 
© P.E. Allen - 2016  
Example 26-2 - Continued 
To calculate the voltage gain of the MOS follower we need to find gmbs9 (N = 0.4 V).  
  
gmbs12 = 
gm12N
2
2F + VBS12
 = 
810·0.4
2 0.5+0.55  = 158µS 
where we have assumed that the value of VSB12 is approximately 1.25V – 0.7V = 0.55V.   
  
AMOS = 
810µS
810µS+158µS+6µS+8µS = 0.825  
The voltage gain of the BJT follower is 
 
 
ABJT = 
500
25.8+500 = 0.951 V/V 
Thus, the gain of the op amp is  
 
Avd(0) = (4,680)(0.825)(0.951) = 3,672 V/V 
The power dissipation of this amplifier is,   
 
Pdiss. = 2.5V(125µA+125µA+100µA+1000µA) = 3.375mW 
The signal swing across the 500 load resistor will be restricted to ±0.5V due to the 
1000µA output current limit.
```

---

## p.27

![p.27](pages/p27.png)

```text
Lecture 26 – Buffered Op Amps (6/25/14) 
Page 26-27   
CMOS Analog Circuit Design 
 
© P.E. Allen - 2016  
SUMMARY 
•  A buffered op amp requires an output resistance between 10  Ro  1000 
•  Output resistance using MOSFETs only can be reduced by, 
- Source follower output (1/gm) 
- Negative shunt feedback (frequency is a problem in this approach) 
•  Use of substrate (or lateral) BJT’s can reduce the output resistance because gm is larger 
than the gm of a MOSFET 
•  Adding a buffer stage to lower the output resistance will most likely complicate the 
compensation of the op amp
```
