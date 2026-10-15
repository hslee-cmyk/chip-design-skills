# A. R. Mohamed, M. F. Ibrahim, F. Farag, 'Input Offset Cancellation Trimming Technique for Operational Amplifiers', SIECPC 2013

- 원본 PDF: `G:\내 드라이브\work\Todoc\논문모음\input offset cancellation trimming technique for operational amplifier_mohamed2013.pdf`
- 사본: `source.pdf` (sha256 `bc22971249661f6693b0b1ba2cf183bef64e71d87ad4e449eab047c4e947c09b`)
- 웹 출처: https://pure.kfupm.edu.sa/en/publications/input-offset-cancellation-trimming-technique-for-operational-ampl/
- 그림·표 위치: PDF p.2 Fig.2(주입 전류 I_Trim로 한 입력 단자에 DC 전압 더하기), 식(1)(2) 단별 입력 환산 offset; p.3 Fig.4(M9/M11 두 단 level shifter = 신호 경로 안 버퍼), 식(3)(4) ΔV_GS(I_Trim), 식(7) 버퍼 이득, Fig.6 전체 회로; p.4 Fig.9 I_Trim 대 I_n, Fig.11 V_ic 대 I_optimum; p.5 Table II
- 엔진 연결: 아직 없음 -- 계획 `docs/01-plan/features/offset-trim.plan.md` 근거표(R-행)에서 인용
- 쪽 수: 5
- 변환: PyMuPDF 텍스트 추출(쪽 단위). 수식·표·그림은 텍스트가 깨질 수 있으니 같은 쪽의 렌더 PNG(`pages/`)로 확인할 것.
- `pages/`·`images/` 는 git 에 없다. 없으면 skill 폴더에서 `python tools/pdf_to_md.py ensure` 로 만든다.

---

## p.1

![p.1](pages/p01.png)

![p.1 내장 이미지 1](images/p01_1.png)

![p.1 내장 이미지 2](images/p01_2.png)

```text
Input Offset Cancellation Trimming Technique  
for Operational Amplifiers   
 
Ahmed Reda Mohamed, Mohamed F Ibrahim, and Fathi Farag  
Electronics and Communication. Dept., Faculty of Engineering,   
 Zagazig University, Egypt. 
ffarag@zu.edu.eg   
 
  
Abstract— This paper presents a novel input offset cancellation 
technique dedicated for analog building blocks. This technique 
provides an injected current to the analog input signal that is a 
function of the offset. The proposed technique provides a suitable 
method to the post-package offset cancellation. Unlike, other 
convention techniques, the proposed technique avoids the 
potentially stability issue, consumes a low silicon area, low power 
consumption, and  temperature independent. The input offset 
cancellation circuit is attached to the  input stage of the 
differential input single output (DISO) amplifier to revoke 
undesired DC, offset voltage (Vos, out), based on trimming current 
(ITrim). DISO amplifier with input offset cancellation circuit is 
simulated and comprehend a DC gain of 78 dB, a unity-gain 
frequency (GBW) of 58 MHz associated with a phase margin of 
૟ૠ࢕. Moreover, the total consumption power is 0.72 mW. The 
statistical analysis with practical different coefficients provided 
from foundry demonstrates offset voltage less than 200 ࣆ࢜. The 
circuit is simulated in IBM 0.13µm CMOS technology with a 
single power supply  1.5-V. 
Keywords- Analog circuit; Offset cancellation; Post-packging;  
Trimming current; DISO. 
I. 
 INTRODUCTION  
 Steady advances in design of MOS integrated circuit 
increases the direction for realization analog and digital 
circuits on a single chip. Frequently, the quality of the analog 
portion of such chips is limited by the offset voltage (Vos, out) 
exhibited by integrated differential amplifiers. Differential 
amplifier is used in many vital applications whether that was 
analog or digital applications such as, an analog circuit of an 
orthogonal frequency divisions multiplexing (OFDM) wireless 
communication system [1], optical communication system, 
and audio/video processing system [2,3]. So, it is mandatory 
to identify the dominant reasons of  Vos, out to find a qualified 
settlement to revoke. 
The offset voltage is generated from transistor mismatches 
due to technology scaling trend and  reduction in the feature 
size. Furthermore, the mechanical stress [4] is an additional 
factor to cause a DC error or Vos, out. Usually, the offset voltage 
is specified by assuming a single source of error at the input 
terminals as shown in Fig. 1(a). The value of this imaginary 
voltage source represents the input referred offset voltage        
(Vos, in) of the amplifier [5].  
The harmful effects of DC error lies in the limitation of the 
amplifier ability to resolve a small DC input voltage smaller 
than the Vos, in. This leads to  reduce the output swing and 
drives the latter stages into nonlinear operation [6]. Therefore, 
DC offset cancellation is imperative way to reduce the 
inherent offset as shown in Fig. 1(b). 
(a) 
 
 
 
 
 
 
 
 
 
 
 
(b) 
Fig. 1. (a) The input referred offset voltage (Vos, in) of the DISO amplifier 
representation. (b) DC characteristic curve of the DISO amplifier. 
 
Many techniques have been reported [7, 8, 9] and used in 
the past to cancel out the offset voltage. Based on the 
trimming during the production process, all trimming 
techniques can be classified into two categories: pre-package 
trim and post-package trim. The pre-package trim includes all 
trim techniques that take place before the silicon die is 
packaged into its final package. On the other hand, post-
package trim is done after packaging the part. The pre-
package trim is a critical one, since the packaging process can 
lead to significant offset shifts of the part. Especially, the 
majority of all parts are shipped by plastic packages which  
inflict high mechanical stresses to silicon die [4]. These 
mentioned mechanical stresses are converted into offset 
voltage due to the piezoelectric prosperities of silicon. These 
offset voltage changes randomly after packaging. 
978-1-4673-6195-8/13/$31.00 ©2013 IEEE
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

```text
The most common method for pre-pack
of the aforementioned offset error is t
differential input voltage offset error. Then
such voltage offset error from one of the 
terminals. For example, Ac coupling techniq
capacitor is used in the signal’s path at inp
penalty of this method is signal loss and 
larger capacitor. Another method is the
cancellation [10, 11] technique which ten
amplified offset from the output and feedba
eliminate any potential DC offset. This me
loop delay, loop gain, and potential stabili
feedforward offset cancellation technique 
high consumed area and high power consum
strenuous efforts to remove offset voltage 
but it will most likely show a non-zero 
assembled [4]. Therefore, pre-package trim
guarantee very high accuracies of the trimme
So, post-package trim technique is a m
because it takes into account offset shift 
Therefore, very high trim accuracies can be
former arts of post-package trim techniques
changes to an IC in order to store the off
voltage. For example, include trimming resi
blowing links with a laser, shorting out zene
reverse voltage, lowing metal fuses with
modifying the resistivity of a poly-silicon re
current, and storing digital bits onto a non
(e.g. flash) [7]. In this work, a novel input o
technique for DISO amplifier is discussed
above mentioned issues. The proposed ci
injected current to the analog input sig
additional DC voltage is generated to revoke
This article is organized as following: Th
is described in section II. In section III, sim
presented. Finally, conclusion is presented in
II. 
THE PROPOSED CIRCU
 The block diagram shown in Fig. 2 
embodiment to the proposed settlement for 
error. The proposed solution suggests an o
circuit controlled by injected current which
one of amplifier’s  terminals. The offset c
can recover the Vos, in by adding a DC volta
serves as a starting point for the following
block will be discussed in detail f
implementation. 
Fig. 2. The block diagram of the proposed
kage compensation 
to determine the 
n, add or subtract 
differential input 
que [5] in which a 
put or output. The 
large area due to 
e feedback offset 
nds to extract the 
ack to the input to 
ethod suffers from 
ty issues. Finally, 
[12] which uses 
mption. Despite the 
before packaging, 
offset after being 
m is not able to 
ed offset voltage. 
mandatory method 
due to package. 
e achieved. In the 
s make permanent 
ffset compensation 
istors with a laser, 
er diodes by a high 
h a high current, 
esistor with a high 
n-volatile memory 
offset cancellation 
d to overcome the 
rcuit is based on 
nal in which an 
e the offset. 
he proposed circuit 
mulation results are 
n section IV. 
UIT  
is an exemplary 
canceling the DC 
offset cancellation 
h  is connected to 
ancellation circuit 
age. This diagram 
g discussion. Each 
for the specific 
d solution. 
A. Design a CMOS Differentia
CMOS differential amplifi
PMOS-differential pair M1 an
NMOS active load M3 and M4 
PMOS-differential pair is fo
common source amplifier. T
NMOS transistor M5 with PM
stage are biased by transferri
through M8. Dimension of M
according to available Iref. Sta
using compensation network 
capacitor (ܥ௖) and nulling re
CMOS differential amplifier
shown in Fig. 3(a, b), is analyz
solution. 
 
 
(a)                      
Fig. 3. (a) Schematic of CMOS tw
symbol.(c) Input referred offset vo
There are several methodolo
to design a CMOS two stage d
most recent one is gm/ID me
These methodology   has a lot o
the performances of analog cir
of two stage differential ampli
to evaluate the dimensions of a
V୭ୱ,୧୬ =V୭ୱଵ,୧୬ +
V౥౩మ,౟౤
A౬భ  
V୭ୱ,୧୬=ቊට
ଶIDయ
ஒ౤య ቈ
∆ቀW
L ቁ
ଶቀW
L ቁ቉
ଷ 
      ට
ଶIDభ 
ஒ౦భ ቈ
∆ቀW
L ቁ
ଶቀW
L ቁ቉
ଵ 
Where; 
V୭ୱ,୧୬      : is the input referred offset vo
V୭ୱଵ,୧୬    : is the input referred offset vo
V୭ୱଶ,୧୬    : is the input referred offset vo
A୴ଵ        : is the voltage gain of 1st stag
IDଵሺଷሻ     : is the DC current of M1(3). 
β୮ଵ         : is the gain process factor of P
β୬ଷ         : is the gain process factor of N
W
L           : is the width to length ratio of
∆VTH୬    : is the difference between thr
∆VTH୮    : is the difference between thr
g୫ଵሺଷሻ    : is the trans-conductance of M
al Amplifier 
ier shown in Fig. 3 consists of 
nd M2, as the first stage, with 
biased by PMOS transistor M7. 
ollowed by the second stage, 
The second stage consists of 
MOS active load M6. Both two 
ing the reference current (Iref) 
M13, diode connection, is set 
ability issues can be handled by 
composed from compensation  
esistor (ܴ௭) [6]. The two-stage 
r with compensation network  
zed to be a part of the proposed 
 
          
(c) 
 
 
 
 
 
                             (b) 
o-stage differential amplifier. (b) Its 
oltage for each stage representation. 
 
ogies mentioned in [5, 6, 13, 14] 
differential amplifier. One of the 
ethodology, described in [14]. 
of benefits as strongly related to 
rcuits. The methodology design 
ifier described in [6, 14] is used 
all transistors. 
 
 (1) 
+ ∆VTH୬ቋ
୥ౣయ 
୥ౣభ  +      
                     
+ ∆VTH୮             +  
V౥౩మ,౟౤
A౬భ       (2) 
oltage of DISO amplifier. 
oltage of 1st  stage of DISO amplifier. 
oltage of 2nd stage of DISO amplifier. 
e. 
PMOS, M1. 
NMOS, M3. 
f MOST. 
reshold of M3 and M4. 
reshold of M1 and M2. 
M1(3).
```

---

## p.3

![p.3](pages/p03.png)

![p.3 내장 이미지 1](images/p03_1.png)

![p.3 내장 이미지 2](images/p03_2.png)

![p.3 내장 이미지 3](images/p03_3.png)

![p.3 내장 이미지 4](images/p03_4.png)

![p.3 내장 이미지 5](images/p03_5.png)

```text
In addition to used methodology [6 ,14], it is necessary to 
keep in mind  the design and layout considerations to reduce 
any systematic and DC error [16]. Moreover, the first stage 
has superior priority and has a dominant effect on the offset 
voltage during the design with respect to design the second 
stage. So, Vos1, in represented in Fig. 3(c) should be reduced 
according to (1). 
B. Design the Offset Cancellation Circuit 
Based on the prior art in [17], the offset cancellation 
technique circuit is mainly a two cascaded DC level shifters, 
common drain amplifiers. The schematic circuit and its 
symbol are presented in Fig. 4(a, b). The first DC level shift 
composes of  PMOS M9 with PMOS active load M10. And, the 
other consists of  NMOS M11 with NMOS active load M12. 
M10 is fed from PMOS diode connection M14, forced in 
saturation mode. ITrim is transferred from M14 to M10 by the 
same factor for equal dimensions. ITrim is varied according to 
value of the potentiometer (POT) as shown in Fig. 4(c). Both 
M10 and M14 perform a current mirror. Also, M12 is bias from 
NMOS M13, diode connection, shown in Fig. 3 (a). 
 
 
 
 
 
 
 
      (a)                            (b)                             (c) 
Fig. 4. (a) Schematic of the offset cancellation circuit. (b) its symbol. 
(c) Bias circuit with POT.  
 
The proposed cell has a main function is to generate an 
additional offset voltage, ∆ܸீௌ which is the difference between 
VGS of M9 and M11 , to cancel out the original offset generated 
from mismatches and mechanical stresses. This cell is 
connected to one of the differential pairs of DISO amplifier to 
compensate any DC error at the output. Using the proposed 
cell, an analog signal control line is provided to DISO 
amplifier. 
 VOS, in   = VOS,୧୬ หୢ୳ୣ ୲୭ ୫୧ୱ୫ୟ୲ୡ୦ୣୱ ,
୫ୣୡ୦ୟ୬୧ୡୟ୪ ୱ୲୰ୣୱୱୣୱ
+ ∆VGS 
            (3) 
∆VGS    =ට
ଶIT౨౟ౣ
ஒ౦వ -ට
ଶIf౟౮
ஒ౤భభ  + ∆VTH 
                         (4) 
IDଵସ     = 
ஒ౦భర
ଶሺVSGଵସെVTHଵସሻଶ  
                         (5) 
IT୰୧୫    = 
VDDିVSGభర
R
  
                                       (6) 
Where; 
β୮ଽሺଵସሻ  : is the gain process factor of PMOS , M9(14). 
β୬ଵଵ      : is the gain process factor of NMOS, M11. 
If୧୶        : is the DC current of M12. 
∆VTH    : is the difference between the threshold of M9 and M11. 
VSGଵସ    : is the DC voltage between the source and the gate of M14. 
VTHଵସ   : is the threshold of the PMOS, M14. 
 R         : is the value of potentiometer resistor, POT. 
VDD      : is the positive power supply. 
 
The relation between VOS, in  and ITrim is expressed by (3) 
and (4). These relations indicate that, the designer is free to 
control the offset voltage after packaging the silicon die. It is 
clear form (4), that ∆ܸீௌ is independent on temperature if 
threshold of NMOS and PMOS are equal. ∆ܸீௌ is mainly 
function of ITrim so, external analog control line is provided. 
Using (5) and (6), potentiometer enables the customer to 
control on  ITrim  and therefore control the offset voltage. 
V౥
V౟ൌ
୥ౣవ.Rభబ
ଵା୥ౣవ.Rభబ .  
୥ౣభభ.Rభమ
ଵା୥ౣభభ.Rభమ  
                         (7) 
Where; 
g୫ଽሺଵଵሻ  : is the trans-conductance of  M9(11). 
ܴଵ଴ሺଵଶሻ   : is the output resistor of M10(12). 
 
The proposed cell should be designed well to perform as an 
ideal buffer with high wide band range. The voltage gain of 
such cell is equal to unity. To verify that, it is necessary to 
select proper length of the transistor of M9, M10, M11, and M12. 
Equation (7) is derived from the ac model circuit shown in 
Fig. 5 with the output resistors of M9 and M11 are ignored as 
they are very large.  
 
 
 
 
 
 
 
 
 
 
Fig. 5. Ac circuit model for the proposed cell. 
III. 
SIMULATION RESULTS 
The complete schematic of the proposed input offset 
cancellation circuit with DISO amplifier is shown in Fig. 6 
being embodiment of the presented block in Fig. 2. 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
Fig. 6. Schematic of the input offset cancellation with DISO amplifier.
```

---

## p.4

![p.4](pages/p04.png)

![p.4 내장 이미지 1](images/p04_1.png)

![p.4 내장 이미지 2](images/p04_2.png)

![p.4 내장 이미지 3](images/p04_3.png)

![p.4 내장 이미지 4](images/p04_4.png)

![p.4 내장 이미지 5](images/p04_5.png)

```text
The proposed DISO amplifier having  a DC gain of 78 dB, 
GBW  of 58 MHz associated with a phase margin of 67௢ is 
designed with the input offset cancellation circuit using the 
methodology design reported in [6,14]. Table I indicates the 
dimensions of every transistor and values of Cc and Rz. 
The proposed circuit is simulated using spectre to ensure if 
DISO with input offset cancellation circuit is stable or not. AC 
response analysis is used to plot the open loop gain to measure 
the phase margin as shown in Fig. 7. It is worth to mention 
that the total power consumption of the proposed circuit is less 
than 0.72mW with Iref  equals to 20μA. 
 
Fig. 7.  Loop gain and phase versus frequency. 
Figure 8 shows a novel  view to sense Vos, out as a function 
of current using a Unit Under Test (UUT), normalized resistor 
( Rn=1Ω). 
 
 
 
 
 
 
 
 
 
 
Fig. 8. Sensing circuit for Vos, out  with Rn. 
 
V୭=Vୡ୫+I୬. R୬                        
                       (8) 
 
The normalized current (In) is generated from the 
difference between currents of M5 and M6 and it finds its path 
through Rn. According to (8), In should be equal to zero to 
revoke any DC error at the output. The injected current, 
trimming current, is swept to null In as shown in Fig. 9. The 
value of injected current at zero In is the optimum current       
(Ioptimum) to revoke the offset. 
Fig. 9.  ITrim  versus In. 
 
 The effect of ITrim on the offset voltage is measured by 
using a unity feedback test as shown in Fig. 10. Vi is adjusted 
to be equal 0.75v (mid the range of power supply) and observe 
the output voltage to be  0.75v. The adjusted value is selected 
to achieve high dynamic range for input and output. The 
proposed circuit  provides a solution to revoke the offset 
voltage at Ioptimum as show in characteristic curve of DISO 
amplifier in Fig. 10. The relation between Ioptimum  and input 
DC common voltage (Vic) shown in Fig. 11 is used to set         
the injected current to be equal Ioptimum  at any desired Vic. 
Fig. 10. The DC characteristic curve of DISO with input offset cancellation. 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
Fig. 11. Common input voltage versus I optimum. 
 
Intensive simulation using Monte Carlo tool with models 
provided by foundry is performed to anticipate any DC error 
due to mismatches. Monte Carlo tool runs with practical 
TABLE I 
SUMMARY OF THE TRANSISTOR’S DIMENSION FOR L=1 µm 
  Transistor 
 
W(µm) 
  M1, M2 
  M3,M4 
  M5 
  M6 
  M7  
  M8 
  M9, M10, M13,M14 
  M11, M12 
 
90 
23 
92 
600 
300 
40 
10 
23 
Cc=2pf,  
 
Rz=1.5kΩ
```

---

## p.5

![p.5](pages/p05.png)

![p.5 내장 이미지 1](images/p05_1.png)

```text
different correlation coefficients to produce the variation at the 
output based on statistical analysis. The histogram of the 
offset is shown in Fig. 12 at Vic equals 0.75v and Ioptimum =5.41 
μA, which confirms the functionality of the proposed circuit 
solution including significant reduction of the mean offset 
(Mu) as well as its spread (Sd). Also, Table II indicates 
statistical result at trimming current equal to Ioptimum and       
Inon-optimum. The performance of the proposed technique 
compared to previous work is shown in table III. 
 
 
Fig. 12. Histogram simulation of the offset voltage. 
 
 
 
IV. 
CONCLUSION 
The novel input offset cancellation technique has been 
presented to provide an analog control line for operational 
amplifier. This control line produces an injected, trimming, 
current varied by potentiometer to cancel out DC error. The 
designed input offset cancellation technique is considered as 
post-package trim technique in which random and systematic 
offset have been cancelled out. The proposed input offset 
cancelation circuit has been used with DISO amplifier, and 
yields a DC gain of 78 dB, a unity-gain frequency (GBW) of 
58 MHz associated with a phase margin of 67୭. Moreover, the 
designed circuit has been simulated and analyzed using 
statistical and Monte Carlo tool provided from foundry that 
yields a mean offset 200µv with spread 3.13mv which is a 
good results according to mentioned former works. Also, the 
total power consumption is 0.72mW. IBM 0.13µm CMOS 
technology parameter has been used for circuit simulation 
with single power supply 1.5v 
ACKNOWLEDGMENT 
The  authors  would  like  to  thank  the  MOSIS  Company  
and IBM  foundry  for  providing  us  with  the  model’s  
parameters used in this work.  
REFERENCES 
[1] Y. Lee, Y. Park, and E. Hong,“Apparatus for Cancellation DC Offset 
and Method Thereof,” U.S. Patent 8 170 147, May 1,2012. 
[2] J. Chen, G.w. Sheets, J. Anidjar, R.J. Kapuschinsky, and L.A.Smith, 
“Analog Amplifier Having DC Offset Cancellation Circuit and Method 
of Offset Cancellation for Analog Amplifier,” U.S. Patent 7 775 421, Jul 
13, 2010. 
[3] S.B. Mashhadi, S.H. Nasrollaholosseini, H. Sepehrian, and R.  Lotfi, 
“An Offset Cancellation Technique for Comparators Using Body-
Voltage Trimming,” IEEE International Conference of  New Circuits 
and Systems, pp. 273 – 276, Jun. 2011. 
[4] R.G.H.  Eschauzier, “ Amplifiers with Input Offset Trim and Methods,” 
U.S. Patent 8 102 204, Jan.  24, 2012. 
[5] Behzad Razavi, Design of Analog CMOS Integrated Circuits, McGraw-
Hill, 2001. 
[6] P. R. Gray and R. G. Meyer, Analysis and Design of Analog Integrated 
Circuits, John Wiley & Sons, 1993. 
[7] J.H. Atherton and H.T. Simmonds, “An Offset Reduction Technique for 
Use with CMOS Integrated Comparators and Amplifiers,” IEEE Journal 
Of Solid-State Circuits, Vol.27, pp. 1168 – 1175, Aug. 1992. 
[8] Y. Hsieh, “Operational Amplifier Having DC Offset Cancellation 
Capability,” U.S. Patent 7 999 612, Aug. 16, 2011. 
[9] T. Yang, J. Shyu, and R. Olah, “Fully Differential Amplifier with 
Continous-Time Offset Reduction,” U.S. Patent 7 683 717, Mar. 23, 
2010. 
[10] T. Iida, T. Asai, E. Sano, and Y. Amemiya, “Offset Cancellation with 
Subthreshold-Operated 
Feedback 
Circuit 
for 
Fully 
Differential 
Amplifiers,” IEEE International Conference on Electronics, Circuits, 
and Systems, pp. 140 – 143, Dec. 2009.   
[11] C. Lu, “An Offset Cancellation Technique for Two-Stage CMOS 
Operational Amplifiers,” IEEE International Conference on Integrated 
Circuit Design and Technology, pp. 1–3, May 2007. 
[12] D. Pham, J. Brinkhoff, K. Kang,C. Ang, and F. Lin, “Feedforward 
Technique 
for 
Offset 
Cancellation 
in 
Broadband 
Differential 
Amplifiers,” IEEE International Symposium on Integrated Circuits, pp. 
429 – 432, Dec. 2009. 
[13] A. Girardi, F. P. Cortes, and S. Bampi, “A Tool for Automatic Design of  
Analog Circuits Based on gm/ID Methodology,” IEEE International  
Symposium on Circuits and Systems, pp. 4643-4646, May 2006. 
[14]  P. Jespers,  The gm/ID Methodology, A Sizing Tool for Low-voltage 
Analog CMOS Circuits, Springer ,2010. 
[15] M. Bhaskaran, S. Sriram, A. Stojcevski, and A. Zayegh, “Design & 
Simulation of a High Performance Rail-to-Rail CMOS Op-Amp at ± 3V 
Supply,” IEEE International Workshop on Electromic Design, Test,and 
Application, Jan. 2006. 
[16] C. saint and J. saint,  Ic Mask Design Essential Layout Techniques,         
McGraw Hill,2002.                            
[17] A.R. Mohamed, M.F. Ibrahim, and F. Farag , “Automated Design 
Technique for Constant-gm  Rail-to-Rail for OTA Input Stage,” IEEE 
International Conference of Microelectronics, pp. 1-4,  Dec. 2012. 
[18] M. Tateno, H. Date, and K. Ohhata, “Low-Power , Low-Offset Stached            
Anlog Latch using an Offset Cancellation Technique,” IEEE 
International Symposium on Integrated Circuits, pp. 140–143,Dec. 2011 
[19]   http://www.ti.com/product/lm741                                                                                 
TABLE III 
  THE PERFORMANCE OF THE PROPOSED CIRCUIT  AT VIC=0.75V 
  Item 
This work 
Ref[18] 
Ref[11] 
Ref[7] 
Ref[19] 
Operation 
Technology 
 
Sd 
Mu 
Power 
supply 
Power 
dissipation 
Analog 
0.13μm 
CMOS 
3.13mv 
200 μv 
1.5 v 
 
0.72mw 
 
    Digital 
    0.18 μm 
    CMOS 
    15:3.3mv 
        - 
    1.8v 
     
    10mw 
   Digital       Analog      Analog 
   0.35 μm     CMOS      BJT 
   CMOS 
      -                 -               - 
   1.898mv     5m            0.8mv 
   3.3v            5v             10v 
    
  0.6mw         3.25mw    500mw 
TABLE II 
 STATISTICAL RESULT AT VIC=0.75V 
  State 
    Count 
Mu 
Sd 
 
ITrim=Ioptimum 
=5.41 μA 
500 
    199.9μv             3.136mv 
 
ITrim=Inon-optimum 
= 8μA 
    500 
    -33.86mv           3.16mv
```
