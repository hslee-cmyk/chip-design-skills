# A 126µW Current-Reuse Telescopic OTA with Class-AB Output Stage (Xie, Chen, UT Austin)

- 원본 PDF: `G:\내 드라이브\work\Todoc\논문모음\A 126uW Current-Reuse Telescopic OTA with Class-AB Output Stage.pdf`
- 사본: `source.pdf` (sha256 `dc173832a7a876cc02219c1db111da1678bb2f663df0cd9ffafc226e2a0e8316`)
- 웹 출처: 찾지 못함(2026-10-14 웹 검색 2회, arXiv 한정 포함). 저자: Shanshan Xie, Hao Chen (UT Austin), PDF 생성 2019-12-10
- 그림·표 위치: Table I 설계 spec·결과 요약 p.1 · Fig.1 전체 2단 OTA p.2 · Fig.2 current-reuse telescopic 1단 p.2 · Fig.3 Class-AB 2단 p.3 · Fig.4 바이어스 p.3 · Fig.5 CMFB p.3 · Fig.6~9 치수·DC 동작점(1단 p.6, 2단 p.7, 바이어스 p.8, CMFB p.9)
- 엔진 연결: `assets/library/current_reuse_telescopic_ota.*`
- 쪽 수: 18
- 변환: PyMuPDF 텍스트 추출(쪽 단위). 수식·표·그림은 텍스트가 깨질 수 있으니 같은 쪽의 렌더 PNG(`pages/`)로 확인할 것.

---

## p.1

![p.1](pages/p01.png)

```text
1
A 126µW Current-Reuse Telescopic OTA with
Class-AB Output Stage
Shanshan Xie, Hao Chen
Department of Electrical and Computer Engineering, The University of Texas at Austin
sxie@utexas.edu, haoc@utexas.edu
Abstract—In this paper, a low-power two-stage fully differen-
tial operational transconductance amplifier (OTA) is presented.
A current-reuse CMOS based cascode telescopic topology is
implemented as the input stage for high-gain and low power
consumption, while a Class AB amplifier is designed as the
output stage to improve slew performance and reduce the overall
power consumption. Furthermore, a common-mode feedback
(CMFB) circuit is used to stabilize the output common-mode
voltage level to 0.9V. Circuit parameters are optimized by a
gm/Id based design flow in a 0.18µm manufacturing process.
Simulation results show that the design achieves outstanding
performance of 0.033% static settling error, 0.065% dynamic
settling error, 38ns settling time, 272µV/
√
Hz noise, and 126µW
power consumption from a 1.8V power supply.
Index Terms—operational transconductance amplifier (OTA),
low power, current-reuse
I. INTRODUCTION
In modern analog and mixed-signal (AMS) integrated circuit
(IC) designs, metrics such as power consumption, noise, and
frequency bandwidth are considered. Among these design
factors, power consumption has gained higher and higher
attention due to the rapidly expanding market of the Internet of
Things (IoT) devices, wireless communication elements, and
consumer electronics. Thus, minimum power consumption is
paramount in analog IC design.
Operational transconductance amplifiers (OTA) often con-
sume the highest portion of total power usage in a low-
power analog circuit, and are also the bottleneck of circuit
power optimization. To design a low-power OTA, several
approaches have been proposed. A widely used method is
biasing the transistors in sub-threshold region. The advantages
of sub-threshold circuits are high intrinsic gain, large output
swing, and very low supply voltage...etc. While the main
disadvantage is that they have lower speed, which results
in smaller transient frequency. Other techniques for reducing
power consumption have also been proposed. Hogervorst
et. al [1] demonstrates a Class AB output stage to reduce the
quiescent current while preserving the signal. Song et. al [2]
shows a current-reuse scheme by letting the current flow
through two differential pair in order to reduce current while
maintaining the same gm/Id value.
In this work, we present a low-power two-stage OTA [3]
design. The first stage of the OTA contains a telescopic
amplifier [4] with current-reuse technique to reduce the current
consumption by half comparing with conventional cascode
telescopic OTA. The second stage consists of a Class AB
amplifier [5] and a miller compensation capacitor to improve
TABLE I: design specifications and result summary
Specs
Our Results
Values for C1, C2, and CL
500fF, 500fF, 1pF
Static settling error
≤0.1%
0.033%
Dynamic settling error
≤0.1%
0.065%
Output swing
[-1.2V, 1.2V]
[-1.706V, 1.706V]
Input common-mode range
[576.5mV, 900.1mV]
OTA open-loop DC small-signal gain (Adm)
75.6dB
Loop gain at low-frequency (β ⋅Adm)
69.36dB
Loop gain unity gain frequency
27.998MHz
Loop gain Phase margin
≥60○
60.557°
Settling time
Up
≤40ns
37.885ns
Down
≤40ns
37.885ns
CMRR at DC
≥60dB
94.4dB
PSRR at DC
≥60dB
82.28dB
Total output noise
≤300µV
272µV
Power consumption
126µW
the output swing and meet the frequency requirement. A
common-mode feedback (CMFB) circuit [6] is adopted to
stabilize the output common-mode voltage. Also, a power
efficient biasing circuit is implemented to make sure all
the transistors operate at desired region. Simulation results
demonstrate that the design satisfies all the requirements, as
shown in Table I.
The remaining sections are organized as follows. Section II
introduces the structure of our design. Section III gives the
derivation of design parameters. Section IV shows the simu-
lation results, and Section V concludes this paper.
II. CIRCUIT TOPOLOGY
To minimize power consumption, the selection of the OTA
topology is essential. In this section, we introduce the overall
structure of our OTA design, and detail each sub-module of the
circuit. Figure 1 shows the schematic design of the designed
OTA. We can observe that a current-reuse telescopic amplifier
is adopted as the input stage, and a Class AB amplifier is used
as the output stage.
A. First-Stage Current-Reuse Telescopic Amplifier
Achieving high gain and low power consumption simul-
taneously is challenging. The small-signal gain of the con-
ventional telescopic OTA design is 0.5 ⋅(gmro)2, where gm
is the transconductance of the input transistor and ro is the
output resistance. Current-reuse telescopic OTA, however, can
maintain the same magnitude of gain with smaller drain
current Id. Since the input port connects to both NMOS and
PMOS, the gain of the current-reuse telescopic OTA shows as
```

---

## p.2

![p.2](pages/p02.png)

```text
2
Vbias2
Vbias3
VDD
GND
Vcmfb
Vim
Vip
Vbias4
M1a
M1b
M2a
M2b
M3a
M3b
M4a
M4b
M5
M6
M7
Vbias1
Vbias1
M8
M9a
M9b
M10
M11a
M11b
M12
M14b
M14a
M13
Vom
M15
M16
Vbias1
M17
M18a
M18b
M19
M20a
M20b
M21
M24b
M23a
M22
Vop
M25
M26
Vbias1
Vom1
Vop1
Vx
Vy
Rz
Cc
Rz
Cc
Fig. 1: Overall schematic of two-stage OTA design.
((gmn4 + gmp1)ro)2, where gmn4 is the transconductance of
the NMOS M4a connected to the input port, and gmp1 is the
transconductance of PMOS M1a.
Consider the current-reuse telescopic OTA schematic design
in Figure 2 and assume that gmp1 = gmn4. Therefore, the value
of transconductance of each transistor becomes one-half the
original value. Keeping the same gm/Id value, the current
flowing through each transistor also be cut by half.
Despite the high gain and low power consumption, the
telescopic OTA design still carry some deficiencies, e.g. re-
stricted swings. Therefore, a second stage circuit is added to
our topology to resolve the shortcomings stated above.
Vbias2
Vbias3
VDD
GND
Vcmfb
Vbias1
Vim
Vip
Vbias4
Vom1
Vop1
M1a
M1b
M2a
M2b
M3a
M3b
M4a
M4b
M5
M6
M7
Vx
Vy
Fig. 2: Schematic of the current-reuse telescopic amplifier.
B. Second-Stage Class AB Amplifier
To satisfy the required output swings and further boost the
overall gain value while keeping the current usage low, a
Class AB amplifier is implemented as the second stage. The
detailed structure of the second stage amplifier is shown in
Figure 3.
When no differential input signal applied, both M15 and
M16 is biased at a barely-on state, meaning that minimum
current will be consumed while input signal is zero. In order
to do this, the gate voltage of M15 is pushed to about 1.3V
and the gate voltage of M16 is pushed to about 0.5V and the
two diode-connected (M11a and M11b) are pushed to sub-
threshold region. Because of such biasing, the Vov is low and
thus, the output swing is higher than conventional common
source output stage design. However, also because of such
bias, the output node of the first stage has lower biasing
point, around 0.5V, which put the pressure on lower side
NMOSs biasing because of the limited voltage swing. This
low common mode output will also lead to an unsymmetrical
input common mode range, because when the input common-
mode voltage is high, the bottom devices (M3, M4 and M5)
are pushed to linear region.
Traditionally, for a common source output stage, the slew
will be limited because the load transistors are not able to
provide the required current. However, by using the designed
Class-AB output stage, instantaneous current will can be pro-
vided and therefore, less current is need for slew requirement.
The limitation of reducing the current further more is the
stability requirement, since reducing the second stage current
will reduce gm2 and reduce the non-dominant pole location.
C. Biasing Circuit
Biasing circuit is a critical sub-module that largely affects
the overall performance of the OTA, and even determines
if a OTA functions properly. In our design, a magic battery
```

---

## p.3

![p.3](pages/p03.png)

```text
3
Vbias1
Vbias1
M8
M9a
M9b
M10
M11a
M11b
M12
M14b
M14a
M13
Vom
M15
M16
Rz
Cc
GND
VDD
Vbias4
Vop1
Fig. 3: Schematic of the Class AB amplifier.
approach [7] is chosen. The architecture of the biasing circuit
is shown in Figure 4, while the other side of Vx and Vy is
marked in Figure 3.
Vbias4
Vx
Vy
Vbias1
Vbias2
Vbias3
VDD
GND
M27
M28
M29
M30
M31
M32
M33
M34
M35
Ibias
Fig. 4: Schematic of the biasing circuit.
D. Common-mode Feedback
Stabilizing the output common-mode voltage to the desired
value ensures all the transistor work in desired region, such as
saturation region for the first-stage and second-stage. A CMFB
circuit compares the average voltage of two differential output
ports and a user-defined desired output common-mode voltage,
then feeds a signals (Vcmfb) back to control the tail current in
the first stage telescopic OTA. R1 and R2 are used to averaging
the differential signal (Vop and Vom) to common mode voltage
(Voc). Figure 5 shows the topology of the CMFB circuit. The
desired common-mode circuit Voc des is generated by two
transistors (M39 and M40) instead of two large resistors in
order to reduce the current flow. Because ensuring a stable
common mode is essential in this design, a larger channel
length is used to reduce process variation.
Vom
Vop
Vbias4
Voc_des
Voc
Vcmfb
GND
VDD
R1
R2
M36a
M37a
M37b
M36b
M38
M40
M39
Fig. 5: Schematic of the CMFB circuit.
III. CIRCUIT PARAMETERS DERIVATION
Given the circuit topology, the next step is to derive the
value of each design variable, e.g. width/length of each transis-
tor, capacitors and resistors value. Detailed steps of variables
derivation are described in this section. The exact value of
design variables used in our OTA can be found in Appendix.
A. First-Stage Variables
Consider the dynamic settling error and settling time re-
quirement, we have
ϵd ≤0.1%, ts ≤40ns,
(1)
where ϵd is the dynamic settling error and ts is the settling
time. Assume ts = tslew + tlln, where tslew is the slewing time
and tlln is the linear settling time. The Class AB structure in
the second stage can provide instantaneous current. Therefore,
we allocate tslew and tlln to 10ns and 30ns respectively,
to relax the bandwidth requirement and reduce the current
consumption.
To achieve ϵd ≤0.1%, the equation
tlln ⋅ωc = 6.9
(2)
should be satisfied [8], where ωc is the loop gain unity gain
bandwith, which is also equal to the close-loop bandwidth.
```

---

## p.4

![p.4](pages/p04.png)

```text
4
Given tlln = 30ns, the value of ωc is then calculated to be 2.3×
108; thus, the loop gain unity gain frequency fc is 36.6MHz.
To obtain the equivalent transconductance gm1 of the first
stage amplifier, we have
gm1 = ωc ⋅Cc
β
(3)
where Cc is the value of the compensation capacitance and β
is the feedback factor.
β =
Cf
Cf + Cs + Cgg1
(4)
assuming Cgg1 is negligible and Cf = Cs = 500fF, β is about
0.5. In reality, Cgg1 is not negligible. therefore, we assume
that β is around 0.48. By setting Cc to 500fF, we have
gm1 = gmn + gmp = 238µS.
(5)
Assuming gmn = gmp; therefore, gmn = gmp = 119µS. To
achieve low power consumption, value of gm/Id for each
transistor is set to 19µS/µA, so that the drain current of
each transistor should be 6µA. By current density chart, the
channel width Wn1 for NMOS transistors and the channel
width Wp1 for PMOS transistors turned out to be 2µm and
6µm, respectively.
B. Second-Stage Variables
Given phase margin PM = tan−1( ωp2
ωc ) [9]. Consider the
phase margin constraint PM ≥60○, the value of non-dominant
pole ωp2 should be manipulated. Let PM be 70○, we have
ωp2/ωc = 2.8. By equation
ωp2 ≈
gm2
CLtotCgg2
Cc
+ Cgg2 + CLtot
,
(6)
and the value of total load capacitance CLtot, parasitic capaci-
tance of second stage input transistors Cgg2, and compensation
capacitance Cc already defined, we have gm2 = 3mS. Assume
gm/Id = 17µS/µA for each transistor, the drain current is
decided to be 176µA. By current density chart with channel
length equals to 0.18nm, the channel width Wn2 and Wp2 of
second stage NMOS and PMOS transistors are set to 25µm
and 65µm respectively. However, because of the Class-AB
technique, second stage current is greatly reduce by biasing
the transistor at barely-on state. The final output stage current
is around 22µA while satisfying the stability requirement.
C. CMFB Circuit
The most important part of the CMFB loop is the size ratio
of the tail current source of the telescopic amplifier M6 and
the feedback transistor M7, as shown in Figure 1. If the size of
transistor M7 is too small, the feedback current would become
insignificant, thus unable to stabilize the feedback loop and
sustain the output common-mode voltage. By heuristic, the
size ratio of the two transistors (M6 and M7) are often decided
to be 0.7 ∶0.3.
IV. SIMULATION RESULTS
The simulations are conducted with 0.18µm CMOS manu-
facturing process in Cadence ADE environment. The execution
temperature is set to 27○C and the supply voltage is 1.8V. DC
sweep, DC analysis, stability analysis, AC analysis, transient
analysis, and noise analysis are included in our simulation
process. Figures of the simulation results are presented in
Appendix.
A. DC Sweep
This simulation derives the relation between differential-
mode gain and output swing, and the waveform of out-
put common-mode voltage versus differential-mode gain, as
shown in Figure 10 and Figure 11.
B. DC Analysis
To evaluate the power dissipation of our design, DC analysis
is performed. The total current usage and the power supply
voltage of our design are 70µA and 1.8V respectively. Hence
we have total power dissipation P = I ⋅V = 126µW. Figure 12
shows the power consumption result.
C. Stability Analysis
As for phase margin and unity gain frequency, we execute
stability analysis. Figure 14 presents the curve of loop gain
and phase margin of our design w.r.t frequency. Note that the
final phase margin is 60.557○and the unity gain frequency is
about 28MHz.
D. AC Analysis
By running AC simulation, we have the CMRR and PSRR
results, as shown in Figure 15(a) and Figure 15(b). The
frequency response of the OTA is shown in Figure 16.
E. Transient Analysis
Transient simulation gives the data of static settling error,
dynamic settling error, and settling time. Figure 17 and Fig-
ure 18 show the results of going up and going down settling.
F. Noise Analysis
Figure 19 shows the noise summary of our OTA, the final
noise turn out to be 272µV/
√
Hz.
V. CONCLUSION
This work presents a low-power fully differential two-stage
OTA design with a current-reuse telescopic first stage and
a Class AB second stage, which outperforms all the design
specifications. According to simulation results, the proposed
OTA achieves 0.033% static settling error, 0.065% dynamic
settling error, 38ns settling time, 272µV/
√
Hz noise, and
an excellent power consumption of 126µW for 1.8V power
supply,
```

---

## p.5

![p.5](pages/p05.png)

```text
5
ACKNOWLEDGEMENT
The authors thank Dr. Nan Sun, Abhishek Mukherjee for
giving valuable suggestions.
REFERENCES
[1] R. Hogervorst, J. P. Tero, R. G. H. Eschauzier, and J. H. Huijsing, “A
compact power-efficient 3 v cmos rail-to-rail input/output operational
amplifier for vlsi cell libraries,” IEEE Journal of Solid-State Circuits,
vol. 29, no. 12, pp. 1505–1513, 1994.
[2] S. Song, M. J. Rooijakkers, P. Harpe, C. Rabotti, M. Mischi, A. H. M. van
Roermund, and E. Cantatore, “A 430nw 64nv/vhz current-reuse telescopic
amplifier for neural recording applications,” in IEEE Biomedical Circuits
and Systems Conference (BioCAS), 2013, pp. 322–325.
[3] N. Sun, “Differential mode voltage range and two-stage ota,” 2019.
[4] N. Sun, “Feedback and port impedances, ota variants and cmfb imple-
mentation,” 2019.
[5] N. Sun, “Otas with single ended outputs and output stage examples,”
2019.
[6] N. Sun, “Stability analysis of feedback circuits,” 2019.
[7] N. Sun, “Current mirrors and mismatch,” 2019.
[8] N. Sun, “Step response,” 2019.
[9] N. Sun, “Ota design considerations,” 2019.
APPENDIX
```

---

## p.6

![p.6](pages/p06.png)

![p.6 내장 이미지 1](images/p06_1.png)

![p.6 내장 이미지 2](images/p06_2.png)

```text
6
(a)
(b)
Fig. 6: Schematic of first-stage amplifier with (a) size and (b) DC operating point.
```

---

## p.7

![p.7](pages/p07.png)

![p.7 내장 이미지 1](images/p07_1.png)

![p.7 내장 이미지 2](images/p07_2.png)

```text
7
(a)
(b)
Fig. 7: Schematic of second-stage amplifier with (a) size and (b) DC operating point.
```

---

## p.8

![p.8](pages/p08.png)

![p.8 내장 이미지 1](images/p08_1.png)

![p.8 내장 이미지 2](images/p08_2.png)

```text
8
(a)
(b)
Fig. 8: Schematic of biasing circuit with (a) size and (b) DC operating point.
```

---

## p.9

![p.9](pages/p09.png)

![p.9 내장 이미지 1](images/p09_1.png)

![p.9 내장 이미지 2](images/p09_2.png)

![p.9 내장 이미지 3](images/p09_3.png)

![p.9 내장 이미지 4](images/p09_4.png)

```text
9
(a)
(b)
(c)
(d)
Fig. 9: Schematic of CMFB circuit with size and DC operating point.
```

---

## p.10

![p.10](pages/p10.png)

![p.10 내장 이미지 1](images/p10_1.png)

```text
10
Fig. 10: DC gain versus output swing.
```

---

## p.11

![p.11](pages/p11.png)

![p.11 내장 이미지 1](images/p11_1.png)

![p.11 내장 이미지 2](images/p11_2.png)

```text
11
Fig. 11: DC gain versus output common-mode voltage.
Fig. 12: Power consumption of the OTA.
```

---

## p.12

![p.12](pages/p12.png)

![p.12 내장 이미지 1](images/p12_1.png)

```text
12
Fig. 13: Loop gain and phase margin.
```

---

## p.13

![p.13](pages/p13.png)

![p.13 내장 이미지 1](images/p13_1.png)

```text
13
Fig. 14: Open loop gain magnitude and in dB.
```

---

## p.14

![p.14](pages/p14.png)

![p.14 내장 이미지 1](images/p14_1.png)

![p.14 내장 이미지 2](images/p14_2.png)

```text
14
(a)
(b)
Fig. 15: (a) CMRR versus frequency; (b) PSRR versus frequency.
```

---

## p.15

![p.15](pages/p15.png)

![p.15 내장 이미지 1](images/p15_1.png)

```text
15
Fig. 16: OTA closed-loop frequency response.
```

---

## p.16

![p.16](pages/p16.png)

![p.16 내장 이미지 1](images/p16_1.png)

![p.16 내장 이미지 2](images/p16_2.png)

```text
16
(a)
(b)
Fig. 17: (a) Settling (going up); (b) Zoomed-in waveform of (a).
```

---

## p.17

![p.17](pages/p17.png)

![p.17 내장 이미지 1](images/p17_1.png)

![p.17 내장 이미지 2](images/p17_2.png)

```text
17
(a)
(b)
Fig. 18: (a) Settling (going down); (b) Zoomed-in waveform of (a).
```

---

## p.18

![p.18](pages/p18.png)

![p.18 내장 이미지 1](images/p18_1.png)

```text
18
Fig. 19: Stability and noise summary.
```
