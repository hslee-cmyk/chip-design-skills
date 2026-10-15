# H. M. von Staudt, 'Trim DAC Design with Minimum DNL for Self-Trim with Self-Test Schemes', IEEE IMS3TW 2011, pp.19-24

- 원본 PDF: `G:\내 드라이브\work\Todoc\논문모음\(Bible - self trim) Trim DAC Design with Minimum DNL for Self-Trim with Self-Test Schemes__staudt2011.pdf`
- 사본: `source.pdf` (sha256 `f72b03b492731ba0f05e30d9ed68c493b0db31797e54237f0f1228e300530dcd`)
- 웹 출처: https://doi.org/10.1109/IMS3TW.2011.34
- 그림·표 위치: PDF p.1-2 §II.A(trim 범위 R = 2^n·LSB가 미보정 분포를 덮어야 함, 꼬리 무시 조건), 식(1)-(5); p.3 §II.C·Table I(이진 가중 주 전이 DNL = σ_U·√(2^n−1), thermometer = σ_U), Fig.4; p.3-4 §III Table II·III(의도적 음의 DNL, 범위 손실); p.4-5 §IV Fig.5-7, §V silicon
- 엔진 연결: 아직 없음 -- 계획 `docs/01-plan/features/offset-trim.plan.md` 근거표(R-행)에서 인용
- 쪽 수: 6
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

```text
Trim DAC Design with Minimum DNL for  
Self-Trim with Self-Test Schemes
Hans Martin von Staudt 
Dialog Semiconductor 
Swindon, United Kingdom 
HansMartin.vonStaudt@diasemi.com 
 
 
Abstract—High precision mixed-signal design strongly depends 
on trimming techniques to overcome manufacturing induced 
variability, of which the digital trimming is the most popular 
approach. The central element of a digitally driven trim circuit is 
the trim DAC. Whilst it needs to be simple and cheap its 
electrical performance in the digital to analogue conversion 
process will affect the trim result. In this paper we analyse the 
trimmed distribution as a function of the DNL performance of 
the trim DAC. Of particular concern is the shaping of the 
distribution by comparator based self-calibration schemes. A 
minimum DNL trim DAC design is proposed that overcomes 
unwanted distribution tails. Eliminating distribution tails is a 
design goal for any type of trimming but it is crucially important 
if an on-chip self-test scheme shall be added to the self-trimming. 
A simulation model for the trimmed distribution is compared to 
actual silicon results of standard and minimum-DNL trim DACs. 
Keywords—self-trim 
by 
reference, 
self-calibration, 
self-
trimming, self-test, self-tuning, trim DAC 
I. 
 INTRODUCTION 
The fundamental trend in microelectronics to use smaller 
and smaller devices increases inevitably variability. In 
principle this effect is well known already in analogue circuit 
design. As the absolute electrical variation of semiconductor 
devices is huge (~30%) most precision circuits are based on 
matching performance i.e. the ability to process two devices 
that match each other even though both undergo the same 
absolute variation. It is determined by the geometric variability 
of the process which manifests itself at the fringes of each 
shape. By increasing the size of corresponding shapes the 
matching performance increases as the fringes compared to the 
total area become negligible. 
This constitutes however a conflict with the commercial 
requirement for small chip size. A long standing practice 
therefore is trimming. The shapes are designed significantly 
smaller than ideal but are equipped with a small adjustable 
element as depicted in Figure 1. 
The performance of the circuit is measured during the 
mandatory manufacturing step of testing and the adjustable 
element is trimmed (by switching on or off small sub-elements) 
until the desired value is reached. The same type of digitally 
driven trimming is used for reference circuits [1]. 
In theory the trend to smaller geometries should help the 
geometric variability. However, electrical variability (threshold 
voltage Vth, saturation current IDsat) becomes dominating. 
The requirement for trimming becomes ubiquitous and shifts 
the focus from static external trimming to a dynamic on-chip 
process. Self-calibration for matching [2], against an external 
reference [3, 4], or against an indirect specification [5, 6] has 
been shown to be an attractive approach to tackle variability0F1. 
On-chip self-calibration raises the requirement for self-test. 
In [7] a window test was proposed that checks against a simple 
fault model for the comparator based self-trim. The test scheme 
checks the trimmed distribution not to be much wider than the 
rectangle 1 LSB wide. However, as shown in [7] the 
imperfections of the comparator and in particular of the trim 
DAC potentially result in long distribution tails, which can 
easily fail the window test. Hence it is important to have a 
mathematical way to describe it. 
II. 
TRIMMED DISTRIBUTION 
A. Ideal Trimming Process 
The ideal trimming process divides the natural distribution 
of the value, characterised by its standard deviation σV, in a 
series of usually 2n slices, each 1 LSB wide. As depicted in 
Figure 2 the trimming process piles the slices on top of each 
other. 
 
Fig. 2. Natural distribution cut in slices, forming a trimmed rectangle 
For the remainder of this paper we assume that the trim 
range R = 2n · LSB is designed wide enough to cover the 
                                                                          
1 The terms calibration and trimming are used interchangeably. There is no 
particular convention in this paper to distinguish between the two terms. 
+1 LSB
0 
reference  
reference   
(a)                              (b) 
→ 
Fig. 1. Large matching structures vs. small structures with trim elements 
2011 International Mixed-Signals, Sensors and Systems Test Workshop
Unrecognized Copyright Information
DOI 10.1109/IMS3TW.2011.34
19
2011 International Mixed-Signals, Sensors and Systems Test Workshop
978-0-7695-4479-3/11 $26.00 © 2011 IEEE
DOI 10.1109/IMS3TW.2011.34
19
2011 IEEE 17th International Mixed-Signals, Sensors and Systems Test Workshop
978-0-7695-4479-3/11 $26.00 © 2011 IEEE
DOI 10.1109/IMS3TW.2011.34
19
```

---

## p.2

![p.2](pages/p02.png)

![p.2 내장 이미지 1](images/p02_1.png)

![p.2 내장 이미지 2](images/p02_2.png)

![p.2 내장 이미지 3](images/p02_3.png)

```text
natural distribution of the value to be trimmed, usually ±5σV, 
so the tails beyond R can be neglected. As a further convention 
we further assume that the centre of the untrimmed distribution 
µ = 0, as well as the target value of the (self-) trim operation. 
The trim codes may be designed in a 2’s complement form 
with i ∈ [–2n-1, 2n-1–1]. Each slice can then be described as 
follows. 
(
)
⎪
⎪
⎩
⎪⎪
⎨
⎧
+
<
≤
⋅
=
⎟⎠
⎞
⎜⎝
⎛−
−
otherwise
    
0
2
1
2
for  
 
2
1
 
2
2
2
2
/
2
n
n
V
n
iR
x
V
R
i
x
R
i
slice(x,i)
e
σ
πσ
 
It can be shown that the sum of all slices form the ideal 
rectangular trimmed distribution as depicted in Figure 2b. The 
second line expresses the rectangular distribution with the step 
function (Heaviside function [8]) H(x). 
LSB
LSB
x
LSB
H
x
H
x
V
LSB
x
i
x
slice
x
V
)
(
)
(
)
(
0
0
)
,
(
)
(
otherwise
:
for
1
−
−
=
⎪⎩
⎪⎨
⎧
>
≥
=
= ∑
 
We assume here the comparator-based self-trim, which 
stops once the value to be trimmed is beyond the reference. 
This affects the rectangle such that it is not centred on the 
reference but single-sided attached to it (see Figure 2.). 
B. Trimming Process With Noise 
The measurement process required for trim decisions is a 
second independent random process, this time in the time 
domain. In the example of the comparator-based self-trim it is 
the uncertainty if the difference between the reference and the 
value under trim is close to zero. Under this condition any kind 
of noise will determine the outcome of the comparison. Other 
terms for the same effect are repeatability and random 
measurement inaccuracy. This random process can be 
described with the probability density function (PDF) N(µ=0, 
σN). As depicted in Figure 3 each transition is affected by 
random noise. 
It shapes the form of each of the slices. The mathematical 
operation expressing this is a convolution [9], indicated by the 
asterisk. As the convolution is a linear operation of its 
application to all slices is equivalent to applying it to the ideal 
sum of all slices, which is the rectangle 
(
)
LSB
x
LSB
H
x
H
i
x
slice
i
x
slice
x
V
Ν
Ν
Ν
)
(
)
(
)
(0,
)
,
(
)
(0,
)
,
(
)
(0,
)
(
N
N
N
−
−
∗
∗
∗
=
=
=
∑
∑
σ
σ
σ
 
The result of convoluting a step function with a PDF is 
equal to the cumulative distribution function (CDF). For a 
normal distribution the CDF is expressed with the error 
function erf(x) [10]. 
 
Fig. 3. Trim DAC transfer function, modified by noise 
LSB
LSB
x
erf
x
erf
x
V
N
N
2
2
2
)
(
2
2
⎟
⎟
⎠
⎞
⎜
⎜
⎝
⎛
−
−
⎟
⎟
⎠
⎞
⎜
⎜
⎝
⎛
=
σ
σ
 
C. Trimming Process With Differential Non-Linearity 
The effect of manufacturing variations on the elements of a 
DAC have been widely examined in [11, 12] with regards to 
DNL and INL performance and yield. A trim DAC, however, 
has only one purpose: to find a (i.e. any) correction of the 
untrimmed value. Hence INL is of no particular interest as it is 
overshadowed by the width of the untrimmed distribution. 
In contrast DNL refers to the width of the trimmed 
distribution as it describes the ability of a DAC to target a 
given output value. For trim DACs this effect is expected to 
become visible in the trimmed distribution. 
The definition of the slices in (1) needs to be changed in 
order to take the variation of their widths into account. As 
discussed above the INL contribution in (6) can be neglected as 
it will be eliminated as part of the trimming process. 
(
)
(
)
⎪
⎪
⎪
⎪
⎩
⎪⎪
⎪
⎪
⎨
⎧
⋅
+
+
+
+
>
+
≤
=
−
−
otherwise
for    
     
for    
2
2
2
2
2
1
)1
(
)
(
2
1
0
       
)
(
2
    
0
V
i
x
V
n
n
e
i
DNL
i
INL
R
i
x
i
INL
R
i
x
slice(x,i)
σ
πσ
 
The width of each step is determined by the corresponding 
DNL(i+1), which again can be described with a normally 
distributed probability density function, similar to what was 
depicted in Figure 3. A convolution between the two PDFs 
would be required. 
There are two major differences to the convolution with the 
comparator noise. Firstly the self-trim algorithm eliminates the 
left hand tail of the distribution, because it carries on stepping 
to the next slice until the trimmed value is beyond the 
reference. The tail which is cut off on the left hand side will be 
Trim code 
3 
2 
1 
0 
-1 
-2 
-3 
-4 
Required trim (correction) value 
Probability 
density 
Target 
(6) 
(2) 
(3) 
(4) 
(5) 
(1) 
20
20
20
```

---

## p.3

![p.3](pages/p03.png)

![p.3 내장 이미지 1](images/p03_1.png)

![p.3 내장 이미지 2](images/p03_2.png)

![p.3 내장 이미지 3](images/p03_3.png)

```text
shifted with the next trim step by 1 LSB and will then be 
subjected to a convolution operation before its contribution 
would be added. For the sake of simplicity we neglect this 
small contribution to the target rectangle and rather focus on 
the tail which is produced by the last self-trimming step. 
As a second simplification we set the PDF of the 
untrimmed distribution to be constant for the width of the slice. 
Then each of the slices can be described as the convolution of a 
step function with the normal distribution of the respective 
DNL(i). 
⎪⎪
⎪
⎩
⎪⎪
⎪
⎨
⎧
≥
⎟
⎟
⎠
⎞
⎜
⎜
⎝
⎛
⎟
⎟
⎠
⎞
⎜
⎜
⎝
⎛
−
−
⋅
⋅
<
=
⎟⎠
⎞
⎜⎝
⎛
−
0
2
1
2
1
2
1
0
0
for 
for 
DNL(i)
 
of
 
CDF
n
 transitio
of
y 
Probabilit
2
2
2
2
2
/
2
x
LSB
x
erf
x
slice(x,i)
i
V
n
iR
V
e
4
4
4
3
4
4
4
2
1
4
4
4
3
4
4
4
2
1
σ
πσ
σ
  
The total trim distribution of the values is again the sum of 
all slices. V(x) = ∑slice(x,i). 
The second major difference to the trimming process with 
noise is that each slice is characterised by a different σi. Hence 
the terms can’t be simplified but remain a sum of terms. 
σi depends on the number of simultaneously switching trim 
elements. It is well known that especially for binary weighted 
DACs the major transition gives the highest DNL contribution. 
Table I compares the DNL values of the transitions of a 3-bit 
DAC (in brackets: 4-bit DAC) for binary weighted and 
thermometer encoded DACs. It is assumed that both DACs are 
made of unit elements, each with a standard deviation of σU. 
TABLE I.  
DNL OF 3(4)-BIT TRIM DAC TRANSITIONS 
Transition: 
1 
(15) 
2 
(14) 
3 
(13) 
4 
(12) 
5 
(11) 
6 
(10) 
7 
(9) 
(8) 
Elements 
switching 
1 
3 
1 
7 
1 
3 
1 
15 
DNL(i) 
Binary weights 
σU 
σU ·√3 
σU 
σU ·√7 
σU 
σU ·√3 
σU 
σU ·√15
DNL(i) 
Themometer 
σU 
σU 
σU 
σU 
σU 
σU 
σU 
σU 
 
It is no surprise that the binary weighted DAC shows strong 
DNL peaks at the major transitions. However, a binary DAC 
usually delivers the easiest and most area efficient 
implementation. 
Depicted in Figure 4 are the PDFs of the slices associated 
to the major transition (4), its two neighbours (3, 5), and the 
trimmed distribution V(x) as the sum of all slices. At first sight 
V(x) looks like a normal CDF but the steepness of the slope at 
+1 LSB is followed by an unusually long tail. The explanation 
for this long tail is down to the rather high standard deviation 
of the major transition σU·√(2n-1). In fact, for a properly 
centred untrimmed distribution (see assumptions above) hitting 
the major transition is the most likely outcome of the self-trim 
process. The steepness of the slope is down to all the minor 
transitions with DNL(i) = σU. 
III. 
DESIGN OF A MINIMUM-DNL TRIM DAC 
As explained in II the left hand side tail is eliminated by the 
trim algorithm. Only the tail on the right hand side of the 
distribution is of concern. It is caused by the positive DNL of 
any transition i.e. the probability that the required trim step for 
reaching beyond the reference is too wide, hence ending up in 
the tail. 
This observation is the basis for the suggestion to build a 
skewed trim DAC with a strong negative DNL. Under normal 
circumstances an intentionally “bad” design of a DAC would 
be avoided, but linearity is not a design goal for a trim DAC; 
actually it is only the first of the two goals below. The second 
is derived from our observation. 
1. Ability to find one (or more) correction 
values inside the target distribution. 
2. Minimise positive DNL to ensure a tail-
free trim distribution 
A. Continuous Under-Dimensioning of Trim Elements 
One way to achieve both goals is to under-dimension every 
more significant trim element. Instead of a factor of 2.0 
between trim elements a small fraction e.g. 5% is subtracted 
each time. Assume 5% is also the standard deviation σU of the 
unit element and σn = σU·√(2n-1) is the standard deviation of 
the major transitions. 
TABLE II.  
KEY FIGURES OF 5% UNDER-DIMENSIONED TRIM DAC  
 
MSB 
 
 
 
 
LSB 
Nominal(n) 
320 
160 
8 
4 
2 
1 
Skewed 
24.76 
13.03 
6.86 
3.61 
1.90 
1.00 
DNL/LSB 
-2.64 
-1.34 
-0.65 
-0.29 
-0.10 
 
DNL/σU 
-52.8 
-26.7 
-13.0 
-5.8 
-2.0 
 
DNL/σn 
-6.7 
-4.8 
-3.4 
-2.2 
-1.2 
 
Range Loss 
-19% 
-15% 
-11% 
-7% 
-3% 
 
 
Table II illustrates the increasingly strong negative DNL of 
the transitions which suppresses the associated positive DNL 
tails for trim DACs up to 6 bits. In fact, as the major transitions 
are defused, the unsuppressed positive DNL of the minor 
transitions become the strongest contributor. 
An obvious drawback of the skewed trim DAC design is 
the reduction in trim range. According to Table II it is 
moderate but noticeable. If that endangers the proper covering 
of the untrimmed distribution the trim range must be widened, 
either by increasing the LSB (for the price of a broader target 
distribution, here 19%), or by adding another trim bit i.e. 
(7) 
0
1
0,0
1,0
2,0
Reference
V(x)
major transition  4
minor transitions 3 and 5
Fig. 4. DNL tail of major transistion dominates tail of trimmed distribution 
trim value
probability density
21
21
21
```

---

## p.4

![p.4](pages/p04.png)

![p.4 내장 이미지 1](images/p04_1.png)

![p.4 내장 이미지 2](images/p04_2.png)

![p.4 내장 이미지 3](images/p04_3.png)

```text
doubling the trim range. Of course this increases the required 
area but it does not come with the usual penalty of poorer 
positive DNL performance. 
B. Discrete Under-Dimensioning of Trim Elements 
In practical design the use of unit elements is prevalent. 
Hence a continuous under-dimensioning is not always easy to 
achieve (e.g. more difficult for current sources than for 
resistors). A variation of the continuous scheme according to 
Table II would be to focus only on the major transitions and to 
“discount” 1 element for each more significant bit. If the 
discounting would start already with the second trim element 
the trim DAC would degenerate and become thermometer 
encoded as all trim elements are equal. 
TABLE III.  
KEY FIGURES OF “-1” UNDER-DIMENSIONED TRIM DAC  
 
MSB 
 
 
 
 
LSB 
Nominal(n) 
32 
16 
8 
4 
2 
1 
Skewed 
25 
13 
7 
4 
2 
1 
DNL/LSB 
-3 
-2 
-1 
0 
0 
 
DNL/σU 
-60 
-40 
-20 
0 
0 
 
DNL/σn 
-8.3 
-7.7 
-5.3 
0.0 
0.0 
 
Range Loss 
-17% 
-13% 
-7% 
0% 
0% 
 
 
In the example of Table III (again with σU = 5%) the 
suppression of the positive DNL is even stronger than for the 
three major transitions. The range loss is comparable but the 
price to pay for the discrete under-dimensioning are the 
untouched minor transitions which will push the trimmed 
distribution tail uncompensated. 
IV. 
SIMULATION 
A Monte-Carlo simulation of the statistical effects of noise 
and DNL distribution together with the original untrimmed 
distribution is the safest way to verify the design of any trim 
DAC in the presence of the aforementioned random processes. 
It can also be used to verify the analytical models derived in II. 
As a particular concern the simulator evaluates the 
simulated tails and calculates possible yield loss against the 
self-test elements as introduced in [7]. It should be noted that in 
contrast to the figures in the previous sections the simulated 
system was designed to produce a left sided distribution 
(searching from above). 
Figure 5 contains histograms of 2 simulations with 6-bit 
trim DACs against a natural untrimmed distribution with a 
standard deviation of 4 LSB and a target value of 200 LSB: 
The trimmed distribution is shaped by the comparator noise (a), 
and by the DNL distribution (b). The black curve is the 
analytical model according to II.B and II.C. It shows a very 
good fit and verifies the two methods against each other. 
Figure 6 shows two further histograms for which no 
analytical model was derived. Figure 6a shows the trimmed 
distribution with both effects. Intuitively it looks like the 
convolution of the two graphs of Figure 5a and 5b. The 
simulated yield loss at the overlap of the 1.5 LSB test element 
and the tail represents already a fairly high yield loss of 
300ppm. 
This 
might 
sound 
low 
but 
for 
practical 
implementations with a high number of such elements (see 
section V.) this value is critical. It is highlighted with the green 
ellipse in Figure 6a. 
Figure 6b shows the design with the same random variables 
but with a “discounted” trim DAC for the 3 most significant 
0
500
1000
1500
2000
2500
3000
3500
4000
198,4
198,7
198,9
199,2
199,4
199,7
200,0
200,2
200,5
Distribution
Limits
Test Element
Model
Trim Value
Count
     
0
500
1000
1500
2000
2500
3000
3500
4000
198,4
198,7
198,9
199,2
199,4
199,7
200,0
200,2
200,5
Distribution
Limits
Test Element
Model
Trim Value
Count
 
 
Fig. 5a. Simulation of comparator noise, σN = 0.05 LSB 
Fig. 5b. Simulation of DNL variation σu = 0.05 LSB, σu = 4 LSB 
  
0
500
1000
1500
2000
2500
3000
3500
4000
198,4
199,0
199,5
200,1
Distribution
Limits
Test Element
Trim Value
Count
   
0
5000
10000
15000
20000
25000
30000
35000
40000
198,4
199,0
199,5
200,1
Distribution
Limits
Test Element
Trim Value
Count
 
Fig. 6a. Simulation of comparator noise and DNL 
Fig. 6b. Simulation of “discounted” trim DAC with comparator noise and DNL
22
22
22
```

---

## p.5

![p.5](pages/p05.png)

![p.5 내장 이미지 1](images/p05_1.png)

![p.5 내장 이미지 2](images/p05_2.png)

![p.5 내장 이미지 3](images/p05_3.png)

```text
bits, as suggested in Table III. The suppression of the DNL tail 
is sufficient to push the yield loss to 0, even with a high 
number of identical self-calibrated and self-tested systems per 
chip. 
It should be noted that the trim code distribution is no 
longer a direct representation of the untrimmed distribution. 
The negative DNL “discounts” create gaps in DAC’s transfer 
function which in turn show up in the distribution of the trim 
codes (see Figure 7). 
For all simulations no difference was ever encountered 
between binary and linear search. Linear search is referenced a 
couple of times throughout this paper as it is easier to grasp the 
effects of the linear search, for the critical moment the 
algorithm makes a decision to stop or to carry on searching the 
trip point. 
0
50000
100000
150000
200000
250000
300000
350000
400000
0
3
6
9
12
15
18
21
24
27
30
33
36
39
42
45
48
51
54
57
60
63
trim codes
count
 
Fig. 7. Discontinuous trim code distribution of “discounted” trim DAC 
V. 
SILICON RESULTS 
The techniques described above were applied to a passive 
matrix OLED driver chip with a display resolution of 
240 x 320 RGB. To the display panel it features 720 precision 
current sources which need to be matched against each other 
within a ±0.25% range. For this design the self-trim and self-
test algorithm was implemented but the first silicon showed 
huge tails which eventually failed most chips in the self-test 
phase of the self-trim.  
The plots in Figure 8 compare the self-trim performance of 
the first and the second silicon iteration. On the second silicon 
only the MSB was discounted. This proved sufficient to 
suppress the DNL tail on the left hand side of the trimmed 
distribution. The remaining tails in Figure 8b are balanced 
which proves they are caused by a random noise process: either 
by the comparator noise or by the measurement noise.  
Measurement noise was considerable when acquiring the 
values for Figure 8. It can be measured as repeatability yet 
despite heavy filtering it was not possible to eliminate it from 
the data. In fact, it constitutes a further convolution washing 
out the trimmed distribution (see Figure 6) further.  
A contributor to the unsatisfying results on the first silicon 
iteration was the trim range being significantly wider than the 
untrimmed distribution. Consequently the positive DNL of the 
overly big major transition pushed the tail of the trimmed 
distribution. Nevertheless the overly large trim range design 
was exploited on the second silicon revision as only the MSB 
was discounted i.e. only the major transition was defused. 
Centring the trim range and the untrimmed distribution also 
eliminated the 2nd major transition as the untrimmed 
distribution was narrow enough not to touch these transitions. 
Only the 3rd major transition was touched at the fringes of the 
untrimmed distribution. The remaining minor transitions were 
anyhow unavailable for the “discounting” technique without 
dramatically limiting the trim range. Furthermore their 
contributions disappear behind the comparator noise which 
dominates Figure 8b. 
VI. 
CONCLUSION 
The design of an intentionally “bad” DAC, strongly skewed 
towards a negative differential non-linearity, makes it the best 
possible trim DAC. It proves to be a very simple yet effective 
way to suppress the distribution tail which results from the 
positive DNL of a trim DAC. The design scheme allows the 
unchanged use of trim algorithms for the comparator based 
self-trim and ensures the success of a window self-test scheme.  
The disadvantage of a reduced trim range can be overcome 
by adding a trim bit without the risk normally associated with 
introducing a further more significant transition of a binary 
trim DAC. 
The remaining risk of the positive DNL tail can be 
calculated with the developed formulas, if the untrimmed 
distribution is known. Hence a design-yield trade-off can be 
made to find an acceptable yield with the smallest overhead in 
terms of trim DAC modifications. 
0 
5 
10 
15 
20 
25 
30 
count (sources) 
trim value (current)
reference 
Fig. 8a. Trim distribution result of original trim DAC 
0
10
20
30
40
50
60
70
80
90
100
reference 
Fig. 8b.  Trim distribution result of “discounted” trim DAC 
count (sources)
trim value (current)
23
23
23
```

---

## p.6

![p.6](pages/p06.png)

![p.6 내장 이미지 1](images/p06_1.png)

![p.6 내장 이미지 2](images/p06_2.png)

![p.6 내장 이미지 3](images/p06_3.png)

```text
The discounting of unit elements instead of continuously 
under-designed 
trim 
elements 
will 
be 
the 
practical 
implementation for most trim DACs. 
Still a Monte-Carlo simulation is required to model the 
simultaneous effects of comparator noise, DNL tails and 
discounted trim elements. All effects analysed separately show 
a perfect match between the analytical solution and the 
simulation. An acceptable match to silicon performance can be 
achieved after extracting the standard distribution parameters. 
ACKNOWLEDGMENT 
The author wants to express his thanks to the design and 
test engineering colleagues of the Rosberg project for their 
support and patience with the author during implementation 
and evaluation. 
REFERENCES 
[1] 
Meijer, Gerard; , “Concepts for Bandgap References and Voltage 
Measurement Systems”, Analog Circuit Design 1996, p.256, Kluwer 
Academic Publishers 
[2] 
Lehmann et al. "Self Trimming Voltage Generator"; US Patent 
6,909,642 B2, Jun 21, 2005 
[3] 
Beer et al. "Semiconductor Chip With Trimmable Oscillator"; US Patent 
6,671,221, B2, Dec 30, 2003 
[4] 
Chandra et al. "Resistor Self-Trim Circuit for Increased Performance", 
US Patent 7642852 B2, Jan 5, 2010 
[5] 
Donghoon Han; Akbay, S.S.; Bhattacharya, S.; Chatterjee, A.; 
Eisenstadt, W.R.; , "On-chip self-calibration of RF circuits using 
specification-driven built-in self test (S-BIST)," On-Line Testing 
Symposium, 2005. IOLTS 2005. 11th IEEE International , vol., no., pp. 
106- 111, 6-8 July 2005 
[6] 
Das, T.; Gopalan, A.; Washburn, C.; Mukund, P.R.; , "Self-calibration of 
input-match in RF front-end circuitry," Circuits and Systems II: Express 
Briefs, IEEE Transactions on , vol.52, no.12, pp. 821- 825, Dec. 2005. 
[7] 
von Staudt, H.M.; , "Comparator based self-trim and self-test scheme for 
arbitrary analogue on-chip values," Mixed-Signals, Sensors and Systems 
Test Workshop (IMS3TW), 2010 IEEE 16th International , vol., no., 
pp.1-6, 7-9 June 2010 
[8] 
http://mathworld.wolfram.com/HeavisideStepFunction.html 
[9] 
http://mathworld.wolfram.com/Convolution.html 
[10] http://mathworld.wolfram.com/NormalDistribution.html 
[11] Yonghua Cong; Geiger, R.L.; , "Formulation of INL and DNL yield 
estimation in current-steering D/A converters," Circuits and Systems, 
2002. ISCAS 2002. IEEE International Symposium on , vol.3, no., pp. 
III-149- III-152 vol.3, 2002 
[12] Lakshmikumar, 
K.R.; 
Hadaway, 
R.A.; 
Copeland, 
M.A.; 
, 
"Characterisation and modeling of mismatch in MOS transistors for 
precision analog design," Solid-State Circuits, IEEE Journal of , vol.21, 
no.6, pp. 1057- 1066, Dec 1986 
 
 
 
24
24
24
```
