# G. Bertotti et al., 'An 8 bit current steering DAC for offset compensation purposes in sensor arrays', Adv. Radio Sci. 10:201-206, 2012

- 원본 PDF: `G:\내 드라이브\work\Todoc\기술문서\ADC\An 8 bit current steering DAC for offset compensation purposes in sensor arrays_ars-10-201-2012.pdf`
- 사본: `source.pdf` (sha256 `96117af5b3c5eab9ed2be5183db37d273f15a08023e090a862ce1920300e9a67`)
- 웹 출처: https://doi.org/10.5194/ars-10-201-2012
- 그림·표 위치: PDF p.2 §2(BW·UW·segmented), §3 식(2) 최악 INL 분산, 식(3) 분할 m비트 최악 DNL 분산; p.3 §4.2 식(4) 강반전 σ_I,Rel(A_β, A_VTH, WL, V_GS−V_TH), 식(5) 약반전; p.4 Fig.3(차동 출력 Iout+/Iout− steering 단위 셀 + cascode), Fig.4; p.5 Fig.5-6 공통중심 배치, Fig.7-8 MC DNL·INL; p.6 Table 1(출력 잡음 항목)
- 엔진 연결: 아직 없음 -- 계획 `docs/01-plan/features/offset-trim.plan.md` 근거표(R-행)에서 인용
- 쪽 수: 6
- 변환: PyMuPDF 텍스트 추출(쪽 단위). 수식·표·그림은 텍스트가 깨질 수 있으니 같은 쪽의 렌더 PNG(`pages/`)로 확인할 것.
- `pages/`·`images/` 는 git 에 없다. 없으면 skill 폴더에서 `python tools/pdf_to_md.py ensure` 로 만든다.

---

## p.1

![p.1](pages/p01.png)

![p.1 내장 이미지 1](images/p01_1.png)

```text
Adv. Radio Sci., 10, 201–206, 2012
www.adv-radio-sci.net/10/201/2012/
doi:10.5194/ars-10-201-2012
© Author(s) 2012. CC Attribution 3.0 License.
Advances in
Radio Science
An 8 bit current steering DAC for offset compensation purposes
in sensor arrays
G. Bertotti1,2, A. Laifi1, E. Di Gioia1, M. Masoumi1, N. Dodel1, E. F. Scarselli2, and R. Thewes1
1Chair of Sensor and Actuator Systems, TU Berlin, Berlin, Germany
2ARCES, University of Bologna, Bologna, Italy
Correspondence to: G. Bertotti (gabriel.bertotti@tu-berlin.de)
Abstract. An 8 bit segmented current steering DAC is pre-
sented for the compensation of mismatch of sensors with cur-
rent output arranged in a large arrays. The DAC is imple-
mented in a 1.8 V supply voltage 180 nm standard CMOS
technology.
Post layout simulations reveal that the de-
sign target concerning a sampling frequency of 2.6 MHz
is exceeded, worst-case settling time equals 60.6 ns. The
output current range is 0–10 µA, which translates into an
LSB of 40 nA. Good linearity is achieved, INL < 0.5 LSB
and DNL < 0.4 LSB, respectively. Static power consump-
tion with the outputs operated at a voltage of 0.9 V is ap-
proximately 10 µW. Dynamic power, mainly consumed by
switching activity of the digital circuit parts, amounts to
100 µW at 2.6 MHz operation frequency.
Total area is
38.6 × 2933.0 µm2.
1
Introduction
Sensor arrays implemented on CMOS chips with thousands
up to millions of sensor sites repeated in a regular manner
have found many applications in today’s world: Whereas the
most prominent example may be the imaging chip in CMOS
cameras from consumer to professional applications (http://
isscc.org/doc/2011/2011 Trends.pdf), other applications are
found in space industry (Lin et al., 2009), security (Perenzoni
et al., 2011), biomedical research (Eversmann et al., 2003;
Frey et al., 2010), and further fields. There, the output signal
of the sensor sites can be given in the voltage domain – which
usually applies to the pixels of CMOS imaging chips – or
in the current domain. Frequently, the output date received
from the respective sensor sites are prone to biasing offsets
and random parameter variations.
In this work, we consider sensor sites with current output,
i.e. the sensors can be modeled as current sources, whose
output currents consist of a bias value (IBIAS), which is
prone to variations (1IBIAS), and a signal dependent por-
tion (ISIGNAL). Under worst-case conditions, the following
relation holds:
IBIAS ≫1IBIAS ≫ISIGNAL
(1)
In such cases, it can be advantageous to implement compen-
sation mechanisms for the deviation 1IBIAS. In this work,
a digital-to-analog converter (DAC) is presented, operated at
the sensor array border and used for the compensation of the
bias current deviations. The required data patterns used for
compensation are derived in an initial calibration phase.
For our purposes – aiming for an application in the
biomedical domain, the following design specifications have
been identified:
full-scale current range = 10 µA, resolu-
tion = 8 bit, operating frequency should at least amount to
2.6 MHz and, moreover, the layout must not measure more
than 40 µm in one direction.
Many different solutions implementing current steering
DACs are available in the literature, e.g. Bastos et al. (1996),
Bastos et al. (1998), Miki et al. (1986), Chen and Gielen
(2007), Lei Luo (2008) and many more. However, these so-
lutions are designed for full scale output current ranges of
order 10 mA and cannot simply be adjusted to our design tar-
gets with 10 µA full scale range. Moreover, all state of the art
DACs achieve their performances thank to the application of
symmetrical layouts, which cannot be adapted to our aspect
ratio of order 100.
The paper is organized as follows: in Sect. 2 the funda-
mental concepts of current steering DACs are introduced.
Section 3 presents mismatch considerations whose under-
standing is necessary for the design. Section 4 briefly com-
ments on the transistor-level implementation, and Sect. 5 fo-
cuses on layout issues. In Sect. 6, post-layout simulation
results are presented, and finally, in Sect. 7, the paper is
concluded.
Published by Copernicus Publications on behalf of the URSI Landesausschuss in der Bundesrepublik Deutschland e.V.
```

---

## p.2

![p.2](pages/p02.png)

```text
202
G. Bertotti et al.: A 2.6 MS/s, 10 µA full-scale 8-bit current steering DAC
2
Current steering DAC topologies
Current steering digital-to-analog converters are based on
the principle of providing a digitally controlled sum of cur-
rents.
Depending on the manner how respective current
sources are tailored and summed, Binary Weighted (BW) and
Unary Weighted (UW) topologies are distinguished (Baker
et al., 1998). In the latter case, all current sources provide a
unity current value (associated with the Least Significant Bit,
LSB). The number of current sources equals the number of
quantization levels, and their connection to the DAC’s output
is controlled by a thermometer code signal derived from the
input word. The Binary Weighted architecture uses only N
current sources with N being the resolution in bits. Conse-
quently, they are binary weighted and directly controlled by
the N input signals.
Both architectures have advantages and drawbacks: for
instance, the simplicity of the BW approach allows to save
area and power but leads to worse accuracy, in the worst-
case even to non-monotonic behavior. On the other hand,
for high resolutions UW converters require huge binary-to-
thermometer decoders, which increase latency, limit the op-
erating frequency, and lead to very expensive solutions in
terms of area. However, monotonic behavior is always guar-
anteed and a linear dependence between output glitch and
transition value is obtained (Lin and Bult, 1998).
A mixture of UW and BW topologies leads to the so-called
segmented current steering topology, where the advantages
of both approaches are merged by concurrently converting
the more significant bits through a UW DAC and the less sig-
nificant bits by means of a BW converter (Maloberti, 2008).
3
Mismatch considerations
As shown in Cong and Geiger (2002), Differential Non Lin-
earity (DNL) and Integral Non Linearity (INL) errors of
unary weighted current steering DACs can be analytically re-
lated to the matching properties of the unity current sources.
Moreover, since binary scaled current sources consist of en-
sembles of unity current sources, it can be shown that the
worst INL error occurs at midcode. This applies to UW, BW,
and segmented current steering topologies, and it amounts to:
E[INL2
WORST] ≃
σ 2
I,Rel
4

2N −1−
1
2N −1

(2)
There, E[INL2
WORST] is the variance of the INL error at mid-
code, N is the resolution in bits, i.e. (2N −1) is the total
number of unity current sources. The parameter σI,Rel is the
standard deviation of the relative error of the unity current
sources’ output current. This mismatch is mainly dependent
on the dimensions of the transistor responsible for the current
generation and on its operating point (Pelgrom et al., 1989;
Sansen, 2008; Bastos et al., 1996).
On the basis of similar considerations it can be shown that,
if the DAC is segmented or binary weighted, the worst-case
DNL code is given by the code which shares the smallest
number of current sources with its previous one: in a BW-
DAC that is the midcode, while in a segmented architecture
it is every code, that makes the BW part convert a zero. If
m is the number of bits with binary weighted conversion, we
achieve:
E[DNL2
WORST] =

2m+1 −1−
1
2N −1

σ 2
I,Rel
(3)
From Eqs. (2) and (3) the optimum percentage of segmen-
tation and the required precision of the unity current source
can be evaluated, once maximum INL and DNL are defined.
For this work, aiming for an 8 bit input signal and a mono-
tonic behavior with high probability (99.9 %), a maximum
σI,Rel of 1.904 % and an m-value of ≤5 are calculated, re-
spectively. Consequently, in the next paragraphs the related
blocks of a current steering DAC with a segmentation of
50 % and unity current sources with a target current of 40
nA and an absolute standard deviation of less than 760 pA
are presented.
4
Transistor level design
As shown in Fig. 1, the binary weighted part of the con-
verter consists of four scaled current sources which gener-
ate 1×LSB, 2×LSB, 4×LSB, and 8×LSB currents, respec-
tively. They are controlled by the four inputs for the less
significant bits. The 4 more significant bits are fed into a
binary-to-thermometer decoder. Its fifteen outputs control
the 16×LSB current sources which are used in the DAC’s
unary weighted part.
4.1
Binary-to-thermometer decoder
Figure 2 shows the small decoder that translates the four in-
put signals into the 15 thermometer outputs. The clear hierar-
chical structure with its exponential dependence on the num-
ber of bits to be converted is the issue to be faced when de-
signing high-precision high-bit unary weighted DACs. Some
sophisticated solutions have been developed to bypass this
challenge taking advantage of the unary weighted topology
(Miki et al., 1986; Bastos et al., 1998): There, use of a row-
column selection architecture reduces the area demand on the
cost of additional digital gates in every current source unit.
Another solution has been reported by Jeong et al. (2010),
where sub-arrays are used. However, since in this work we
are aiming to interface the DAC with a small-pitch sensor ar-
ray, harvesting of any opportunity to save area is mandatory.
Thus, we have chosen not to implement any sophisticated
strategy but to accept a slight linearity degradation due to the
segmented topology.
Adv. Radio Sci., 10, 201–206, 2012
www.adv-radio-sci.net/10/201/2012/
```

---

## p.3

![p.3](pages/p03.png)

![p.3 내장 이미지 1](images/p03_1.png)

![p.3 내장 이미지 2](images/p03_2.png)

```text
G. Bertotti et al.: A 2.6 MS/s, 10 µA full-scale 8-bit current steering DAC
203
4.2
LSB current cell
If the LSB current source is operated in strong inversion the
following equation applies (Pelgrom et al., 1989):
σ 2
I,Rel =
A2
β
WL +
4A2
VTH
WL(VGS −VTH)2
(4)
On this basis the following considerations can be drawn:
1. Given the mismatch related parameters Aβ and AVTH
with Aβ being the transistor constant related matching
constant in [ % µm] and AVTH being the threshold volt-
age related matching constant in [mV µm], the required
standard deviation σI,Rel can be achieved by choosing
an adequate channel area WL and/or by choosing an ap-
propriate effective gate voltage VG,EFF = (VGS −VTH).
2. Consequently, for a given standard deviation, the appli-
cation of a higher effective gate voltage always trans-
lates into the option to decrease the active transistor
area.
3. However, given a defined current to be generated by the
MOSFET, the only way to increase VG,EFF is to make
the ratio W/L smaller.
A comparison with the mismatch behavior for devices oper-
ated in the subthreshold region yields:
σ 2
I,Rel =
 q
nkT
2 A2
VTH
WL
(5)
There, q is the elementary electronic charge, k the Boltz-
mann constant, T the absolute temperature, and n the so-
called non-ideality factor. For a chosen standard deviation
and a fixed current, transistors operated in strong inversion at
sufficiently high effective gate voltage are smaller than tran-
sistors operated in subthreshold region.
Given the boundary conditions in this work, this, however,
would translate into an extremely high L/W ratio as the re-
quired current is small. This is not convenient from the lay-
out related point of view. As a consequence, the LSB current
cell in this work is based on an NMOS transistor operated in
subthreshold region, with more reasonable values for W and
L at an active transistor area of roughly 60 µm2.
The entire schematic of the LSB current source is shown
in Fig. 3. Two output nodes are used to ensure an optimum
transient response by never switching off the current sources
(Baker et al., 1998; Sansen, 2008). A cascode transistor is
added in order to minimize the parasitic capacitance at the
source of the switch transistors, and thus to optimize the
settling-time of the circuit. For the same reason the switches
have minimum dimensions and dummy switches are avoided
as the use of dummies would imply doubling the amount of
switch transistors and related parasitics.
As shown in Fig. 4, the effect of using a cascode transis-
tor on current source mismatch is negligible. Associated to
Fig. 1. Block diagram.
Fig. 2. Binary-to-thermometer decoder.
the switchable current source is also a small driver (Fig. 3).
By means of that circuit the control signals SW and SWn
are generated: their voltage swing is limited to the window
from 0.7 V to 1.2 V in order to reduce the clock feedthrough
(CFT) to the output while still maintaining proper switching
functionality. Moreover, a slower transient drive capability
caused by the minimum dimensions of the output stage of
the driver is advantageous in the sense that CFT is further
reduced. Thus, the voltage error induced on node Vs of the
current source is minimized, which is also advantageous for
the overall settling time.
www.adv-radio-sci.net/10/201/2012/
Adv. Radio Sci., 10, 201–206, 2012
```

---

## p.4

![p.4](pages/p04.png)

![p.4 내장 이미지 1](images/p04_1.png)

![p.4 내장 이미지 2](images/p04_2.png)

![p.4 내장 이미지 3](images/p04_3.png)

```text
204
G. Bertotti et al.: A 2.6 MS/s, 10 µA full-scale 8-bit current steering DAC
Fig. 3. LSB current source with related driver. Bias transistors
connected to input “Iref-IN” are shared by the entire array.
Fig. 4. Relative output current standard deviation of a single tran-
sistor based and of a cascode current source.
4.3
Scaled current cells
The current sources required for the unary weighted part of
the DAC and for the other bits of the binary weighted part
can be directly derived from the circuit presented in Sect. 4.2.
The generic weighted cells are implemented as replica cells
of the LSB current cell (i.e. LSB current source with related
Fig. 5. Schematic plot of the realized layout.
driver) since the small driver in Fig. 3 is optimized only for
one LSB current source.
Although the area consumption
consequently slightly increases, the layout regularity due to
the replication of the entire cell has a positive impact on the
linearity and suppresses the sensitivity to on-chip parameter
gradients.
5
Layout
As e.g. emphasized by Bastos et al. (1998), the performance
of digital-to-analog converters is strictly related to their lay-
out implementation. As the array of current sources can de-
mand a huge area depending on the number of bits, precision,
Adv. Radio Sci., 10, 201–206, 2012
www.adv-radio-sci.net/10/201/2012/
```

---

## p.5

![p.5](pages/p05.png)

![p.5 내장 이미지 1](images/p05_1.png)

![p.5 내장 이미지 2](images/p05_2.png)

![p.5 내장 이미지 3](images/p05_3.png)

```text
G. Bertotti et al.: A 2.6 MS/s, 10 µA full-scale 8-bit current steering DAC
205
Fig. 6. Example for the impact of a systematic error applied to
the array of current sources for a Common-Centroid and a Non-
Common-Centroid layout. Details concerning the assumed error
function see Eq. (6).
and full-scale current, CMOS process parameter gradients on
the chip cannot be neglected. A systematic error of the cur-
rent sources’ parameters would indeed determine a distortion
of the static characteristics and might have a severe negative
impact on DNL and INL. For that reason a Common Cen-
troid layout is used. Some further techniques may addition-
ally give rise to even better results (Van der Plas et al., 1999;
Nakamura et al., 1991), however, as they also require to in-
vest a huge amount of extra area, layout constraints do not
allow for their implementation in this work.
In Fig. 5, details are depicted of the Common Centroid
layout used here. The current sources of the binary weighted
part are placed in the center of the array in a symmetrical
manner supported by the use of dummy LSB cells. The cur-
rent cells of the unary weighted part form the rest of the array.
The 15 UW cells, each one consisting of 16 LSB cells con-
nected together, are not arranged side by side in space but
symmetrically distributed with respect to the binary weighted
part within the entire array. The effects of such a local distri-
bution are exemplarily shown in Fig. 6, where for instance a
parabolic error as a function of the current source location is
considered following the relation
1I(x,y) = ILSB
h
KX(x −x0)2 +KY (y −y0)2i
(6)
with KX = 5 × 10−8 µm−2, KY = 1 × 10−7 µm−2, x0 =
−500 µm,
y0 = 100 µm,
x ∈[−1311;1311] µm,
y ∈
[−2.3;2.3] µm.
6
Results
Figures 7 and 8 provide post-layout simulation results of
DNL and INL, respectively. For these simulations, a low-
ohmic 0.9 V (=VDD/2) voltage source is connected as a load
to the DAC’s output. The shown results are based on 5000
Monte-Carlo runs: the data are generated by means of a Mat-
lab script, which computes the transfer characteristics on the
Fig. 7. DNL error vs. input code for 5000 Monte-Carlo simulations.
Fig. 8. INL error vs. input code for 5000 Monte-Carlo simulations.
basis of DC simulations of 255 equal independent LSB cells.
With the DNL being always smaller than half of an LSB,
the Integral Non Linearity error is ≤0.5 LSB with a prob-
ability of 99.82 %. The slight deviation from the targeted
99.9 % may originate from the limitations of the model used
in Eq. (5), from the impact of the cascode transistor, but also
from the finite number of Monte-Carlo runs. Anyway, the
result is considered to be acceptable.
Using transient simulations and the same output configura-
tion as above, the overall correct functionality, settling time,
glitch values, and the dynamic power consumption are con-
sidered. The results are summarized in Table 1. Since the
settling time at 5 % of LSB level in a full scale transition is
much smaller than required for the specified 2.6 MHz oper-
ating frequency, a maximum operating frequency calculated
as reciprocal of the 3-sigma worst-case Monte-Carlo settling
time appears to be 10.2 MHz. At 1.8 V supply voltage a dy-
namic power of 100 µW is dissipated at the operating fre-
quency of 2.6 MHz, and a DC power of 10 µW is absorbed
mainly by the low-ohmic load.
7
Conclusions
An 8 bit, 2.6 MHz, 10 µA full scale CMOS current steer-
ing DAC with high linearity, low noise, and small area has
been presented. Using a standard 180 nm CMOS technology,
www.adv-radio-sci.net/10/201/2012/
Adv. Radio Sci., 10, 201–206, 2012
```

---

## p.6

![p.6](pages/p06.png)

```text
206
G. Bertotti et al.: A 2.6 MS/s, 10 µA full-scale 8-bit current steering DAC
Table 1. Summary of simulation results.
Parameter
Value
LSB Current
40 nA
DNL
< 0.5 LSB
INL
< 0.5 LSB
Settling Time (nominal, 5 %-LSB)
60.6 ns
Settling Time (Monte-Carlo, 5 %-LSB)
µ = 68.2 ns
σ = 9.98 ns
Output Noise [20 Hz; 2.6 MHz]
2.75 nA
Average Glitch Current
14 pA
(1 LSB transition)
DC Power Consumption
10 µW
Dynamic Power Consumption
100 µW
(2.6 MHz Full Scale Transition)
Maximum Operating Frequency
10.2 MHz
it dissipates 100 µW from a single power supply voltage of
1.8 V at 2.6 MHz operating frequency. Monte-Carlo simula-
tions reveal DNL and INL of ≤0.4 LSBs and ≤0.5 LSB, re-
spectively. Maximum operating frequency is 10.2 MHz. Fol-
lowing the target application, a layout with total dimensions
38.6 × 2933 (µm)2 = 0.113 mm2 is provided. Common Cen-
troid layout techniques are applied to the crucial blocks in
order to minimize the impact of possible on-chip gradients.
Acknowledgements. This work was supported by the “Bun-
desministerium f¨ur Bildung und Forschung” (BMBF), reference
0315636B.
References
Baker, R. J.: CMOS Circuit Design, Layout, and Simulation, 800–
802, IEEE Press, 1st edn., 1998.
Bastos, J., Steyaert, M. and Sansen, W.: A High Yield 12-bit 250-
MS/s CMOS D/A Converter, IEEE Cust. Integr. Cir., 431–434,
1996.
Bastos, J., Marques, A. M., Steyaert, M. S. J. and Sansen W.: A 12-
Bit Intrinsic Accuracy High-Speed CMOS DAC, IEEE J. Solid.-
St. Circ., 33, 1959–1969, 1998.
Chen, T. and Gielen, G. G. E.: A 14-bit 200-MHz current-steering
DAC with switching-sequence post-adjustment calibration, IEEE
J. Solid.-St. Circ., 42, 2386–2394, 2007.
Cong, Y. and Geiger, R. L.: Formulation of INL and DNL yield es-
timation in current-steering D/A converters, Proc. Iscas., 3, 149–
152, 2002.
Eversmann, B., Jenkner, M., Hofmann, F., Paulus, C., Brederlow,
R., Holzapfl, B., Fromherz, P., Merz, M., Brenner, M., Matthias,
S., Gabl, R., Plehnert, K., Steinhauser, M., Eckstein, G., Schmitt-
Landsiedel, D. and Thewes, R.: A 128 × 128 CMOS Biosensor
Array for Extracellular Recording of Neural Activity, IEEE J.
Solid.-St. Circ., 38, 2306–2317, 2003.
Frey, U., Sedivy, J., Heer, F., Pedron, R., Ballini, M., Mueller, J.,
Bakkum, D., Hafizovic, S., Faraci, F. D., Greve, F., Kirstein, K.
and Hierlemann, A.: Switch-Matrix-Based High-Density Micro-
electrode Array in CMOS Technology, IEEE J. Solid.-St. Circ.,
45, 467–482, 2010.
Jeong, S., Kim, K., Jung, K., Park, K., Cho, S.: A Novel Current
Steering Cell Matrix DAC Architecture with Reduced Decoder
Area, Ele. Com. Eng.-CISST, 10, 167–170, 2010.
Lei Luo, J. Y. R.: An 8-bit 700 Mss current-steering DAC, Solid-
State and Integrated-Circuit Technology, Int. Conf. on, 1925–
1928, Beijing, 20-23 Oct. 2008.
Lin, C.-H. and Bult, K.: A 10-b, 500-MSample/s CMOS DAC in
0.6 mm2, IEEE J. Solid.-St. Circ., 33, 1948–1958, 1998.
Lin, J.-F., Chang, S.-J, Chiu, C.-F., Tsai, H.-H and Wang, J.-J.:
Low-Power and Wide-Bandwidth Cyclic ADC with Capacitor
and Opamp Reuse Techniques for CMOS Image Sensor Appli-
cation, IEEE Sens. J., 9, 2044–2054, 2009.
Maloberti, F.: Data Converters, Springer, Dordrecht, The Nether-
lands, 1st edn., 124–129, 2008.
Miki, T., Nakamura, Y., Nakaya, M., Asai, S., Akasaka, Y. and
Horiba, Y.: An 80-MHz 8-bit CMOS D/A Converter, IEEE J.
Solid.-St. Circ., 21, 983–988, 1986.
Nakamura, Y., Miki, T., Maeda, A., Kondoh, H. and Yazawa, N.:
A 10-b 70-MS/s CMOS D/A Converter, IEEE J. Solid.-St. Circ.,
26, 637–642, 1991.
Pelgrom, M. J. M., Duinmaijer, A. C. J. and Welbers, A. P. G.
: Matching Properties of MOS Transistors, IEEE J. Solid.-St.
Circ., 24, 1433–1440, 1989.
Perenzoni, M., Massari, N., Stoppa, D., Pancheri, L., Malfatti, M.
and Gonzo, L. : A 160 × 120-Pixels Range Camera With In-
Pixel Correlated Double Sampling and Fixed-Pattern Noise Cor-
rection, IEEE J. Solid.-St. Circ., 46, 1672–1681, 2011.
Sansen, W.: Analog Design Essential, 614–615, Springer, Dor-
drecht, The Netherlands, 1st edn., 2008.
Van der Plas, G. A. M., Vandenbussche, J., Sansen, W., Steyaert,
M. S. J., Gielen, G. G. E.: A 14-bit Intrinsic Accuracy Q2 Ran-
dom Walk CMOS DAC, IEEE J. Solid.-St. Circ., 34, 1708–1718,
1999.
Adv. Radio Sci., 10, 201–206, 2012
www.adv-radio-sci.net/10/201/2012/
```
