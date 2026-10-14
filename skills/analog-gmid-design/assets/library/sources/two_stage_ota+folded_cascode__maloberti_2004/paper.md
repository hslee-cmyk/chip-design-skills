# F. Maloberti, Layout of Analog CMOS Integrated Circuit - Part 2: Transistors and Basic Cells Layout

- 원본 PDF: `G:\내 드라이브\work\Todoc\논문모음\analog layout\(Bible - Euler Path) Layout of Analog CMOS Integrated Circuit Part2.pdf` (references/stick-diagram-euler-layout.md가 인용하는 `vendor/analog/Layout02.pdf`와 같은 원문 -- vendor 폴더는 저장소에 없음). PDF 생성 2004-03-15, 열기 암호 없는 소유자 제한(RC4)만 걸림
- 사본: `source.pdf` (sha256 `67225fc639670bfe980d2e3ee9df53650fd6134cf14a0c15c2387c002eec18c6`)
- 웹 출처: 저자 공식 게시처 찾지 못함(2026-10-14 웹 검색). 제3자 재게시만 확인: slideshare.net/slideshow/layout02-1/58842369, pdfcoffee.com/layout-02-pdf-free.html
- 그림·표 위치: p.28 'Example 1 (2 stages OTA)' M1~M7 폭 -> two_stage_ota · p.29 'Layout Oriented Design' · p.30 Stack Design and Interconnections · p.31 Use of one Metal Layer · p.32 Stick Layout: Exercise · p.33 From Stick to Layout · p.34 'Example 2 (Folded Cascode)' M1~M11·MP·MN 폭(Only Ws are shown) -> folded_cascode · p.35 'Split of Transistors' · p.36 Stack Design · p.37 Interconnection: Exercise · p.38 Basic Cell Design: check-list. 쪽 번호는 슬라이드 아래 번호 = PDF 쪽
- 엔진 연결: `assets/library/two_stage_ota.*` (p.28~33), `assets/library/folded_cascode.*` (p.34~38); 레이아웃 패턴 표(`gmid_engine/layout/patterns_*.py`)도 같은 원문 p.15·p.19 인용
- 쪽 수: 38
- 변환: PyMuPDF 텍스트 추출(쪽 단위). 수식·표·그림은 텍스트가 깨질 수 있으니 같은 쪽의 렌더 PNG(`pages/`)로 확인할 것.

---

## p.1

![p.1](pages/p01.png)

```text
F. Maloberti - Layout of Analog CMOS IC
1
F. Maloberti
Layout of Analog
 CMOS
Integrated Circuit
Part 2
Transistors and Basic Cells Layout
```

---

## p.2

![p.2](pages/p02.png)

```text
F. Maloberti - Layout of Analog CMOS IC
2
Outline
Introduction
Process and Overview Topics
Transistors and Basic Cells Layout
Passive components: Resistors, Capacitors
System level Mixed-signal Layout
```

---

## p.3

![p.3](pages/p03.png)

```text
F. Maloberti - Layout of Analog CMOS IC
3
Part II: Transistor and Basic Cell Layout
Transistors  and Matched Transistors
Layout of a single transistor
Use of multiple fingers
Interdigitated devices
Common Centroid
Dummy devices on ends
Matched interconnect (metal, vias, contacts)
Surrounded by guard ring
Design for Layout
Stacked layout of analog cells
Stick diagram of analog cells
Example 1: two stages op-amp
Example 2: folded cascode
```

---

## p.4

![p.4](pages/p04.png)

```text
F. Maloberti - Layout of Analog CMOS IC
4
Single Transistor Layout
A CMOS transistor is the crossing of two rectangles,
polysilicon and active area
but, … we need the drain and source connections and we
need to bias the substrate or the well
diffusion
Polysilicon gate
```

---

## p.5

![p.5](pages/p05.png)

```text
F. Maloberti - Layout of Analog CMOS IC
5
Source and Drain Connections
Ensure good connections
Multiple contacts or one big contact?
```

---

## p.6

![p.6](pages/p06.png)

```text
F. Maloberti - Layout of Analog CMOS IC
6
Multiple or single contacts?
Curvature in the metal layer can lead to micro-fractures
Not important for large areas
Reliability problems, possible electro-migration
```

---

## p.7

![p.7](pages/p07.png)

```text
F. Maloberti - Layout of Analog CMOS IC
7
Multiple contacts: Exercise
Consider the following design rules:
minimum contact 0.5 µ
spacing contact-contact 0.4 µ
minimum grid strep 0.1 µ
spacing contact diffusion 0.6 µ
Estimate the number of contacts and their spacing for
W=50 µ
W=52 µ
W=60 µ
```

---

## p.8

![p.8](pages/p08.png)

```text
F. Maloberti - Layout of Analog CMOS IC
8
Matching single Transistors
Regular (rectangular shape)
the W and L matter!!
Parallel elements
silicon is unisotropic
Possibly, the current flowing
in the same direction
```

---

## p.9

![p.9](pages/p09.png)

```text
F. Maloberti - Layout of Analog CMOS IC
9
Asymmetry due to Fabrication
Shadowed region
7°
An MOS transistor is not a symmetrical device. To avoid channeling of
implanted ions the wafer is tilted by about  7 °. 
Source and drain are not equivalent
```

---

## p.10

![p.10](pages/p10.png)

```text
F. Maloberti - Layout of Analog CMOS IC
10
Parasitics in Transistors
)
2
)(
2
(
diff
D
diff
DB
SB
l
L
l
W
C
C
+
+
=
=
Analog transistors often have a large W/L ratio
Capacitance diffusion substrate
W
LD
Resistance of the poly gate
poly
sq
gate
gate
R
L
R
,
=
```

---

## p.11

![p.11](pages/p11.png)

```text
F. Maloberti - Layout of Analog CMOS IC
11
Use of multiple fingers
W
S
S
S
S
D
D
D
D
D
W/2
W/3
'
;
2
1
DB
DB
DB
SB
C
C
C
C
=
=
SB
SB
C
C
'
3
2
=
DB
DB
C
C
'
3
2
=
DB
SB C
C
'
' ;
```

---

## p.12

![p.12](pages/p12.png)

```text
F. Maloberti - Layout of Analog CMOS IC
12
Parasitic in Transistors: Exercise
Calculate the parasitic capacitance diffusion-
substrate for a 40 micron width transistor
one finger
5 finger
8 finger
Use the design rules available and minimum diffusion length
```

---

## p.13

![p.13](pages/p13.png)

```text
F. Maloberti - Layout of Analog CMOS IC
13
Interdigitated Devices
Two matched transistors with one node in common
spilt them in an equal part of fingers (for example 4)
interdigitate the 8 elements: AABBAABB or ABBAABBA
B
2
A
3
1
A
A
B
B
A
A
B
B
2
1
3
A
B
B
A
A
B
B
A
2
1
3
```

---

## p.14

![p.14](pages/p14.png)

```text
F. Maloberti - Layout of Analog CMOS IC
14
Axis of Symmetries
A
B
B
A
A
B
A
B
A
B
A
(A)
(B)
(C)
Common axis
of symmetry
Axis of symmetry
of device A
Axis of symmetry
of device B
Common axis of
symmetry
```

---

## p.15

![p.15](pages/p15.png)

```text
F. Maloberti - Layout of Analog CMOS IC
15
Interdigitiation Patterns
A
AA
AAA
AAAA
AB*
ABBA
ABBAAB*
ABABBABA
ABC*
ABCCBA
ABCBACBCA*
ABCABCCBACBA
ABCD*
ABCDDCBA
ABCBCADBCDA*
ABCDDCBAABCDDCBA
ABA
ABAABA
ABAABAABA
ABAABAABAABA
ABABA
ABABAABABA
ABABAABABAABABA ABABAABABAABABAABABA
AABA*
AABAABAA
AABAAABAAABA*
AABAABAAAABAABAA
AABAA
AABAAAABAA
AABAAAABAAAABAA AABAAAABAAAABAAAABAA
Note: not all the patterns permit a stacked layout
```

---

## p.16

![p.16](pages/p16.png)

```text
F. Maloberti - Layout of Analog CMOS IC
16
Interdigitated Transistors: Exercises
Sketch the layout of two interdigitated transistors
having W1=3W2 and split W2 into 4 fingers. M1 and M2
have their source in common.
Sketch the layout of three interdigitized transistors
having the same width. Use the optimum number of
fingers. The three transistors have the source in
common.
```

---

## p.17

![p.17](pages/p17.png)

```text
F. Maloberti - Layout of Analog CMOS IC
17
Common Centroid
DB
DA
DA
DB
DB
DA
DA
DB
Gradients in features are compensated for (at first
approximation)
metal and poly interconnections are more complex
```

---

## p.18

![p.18](pages/p18.png)

```text
F. Maloberti - Layout of Analog CMOS IC
18
Common Centroid Arrays
A
B
B
A
B
B
A
A
A
B
B
A
Cross coupling
Tiling (more sensitive to 
high-order gradients)
```

---

## p.19

![p.19](pages/p19.png)

```text
F. Maloberti - Layout of Analog CMOS IC
19
Common Centroid Patterns
ABBA
ABBAABBA
ABBAABBA
ABBAABBA
BAAB
BAABBAAB
BAABBAAB
BAABBAAB
ABBAABBA
BAABBAAB
ABBAABBA
ABA
ABAABA
ABAABA
ABAABAABA
BAB
BABBAB
BABBAB
BABBABBAB
ABAABA
BABBABBAB
ABAABAABA
ABCCBA
ABCCBAABC
ABCCBAABC
ABCCBAABC
CBAABC
CBAABCCBA
CBAABCCBA
CBAABCCBA
ABCCBAABC
CBAABCCBA
ABCCBAABC
AAB
AABBAA
AABBAA
AABBAA
BAA
BAAAAB
BAAAAB
BAAAAB
AABBAA
BAAAAB
AABBAA
```

---

## p.20

![p.20](pages/p20.png)

```text
F. Maloberti - Layout of Analog CMOS IC
20
Dummy Devices on Ends
Ending elements have different boundary conditions
than the inner elements -> use dummy
Dummies are shorted transistors
Remember their parasitic contribution!
s
b
d
```

---

## p.21

![p.21](pages/p21.png)

```text
F. Maloberti - Layout of Analog CMOS IC
21
Matched interconnections
Specific resistance of metal lines
Specific resistance of poly
Resistance of metal-contact
Resistance of via
I
Z
V
int
=
Δ
Minimize the interconnection impedance
Achieve the same impedance in differential paths
Keep short the width of fingers for high speed applications
```

---

## p.22

![p.22](pages/p22.png)

```text
F. Maloberti - Layout of Analog CMOS IC
22
Matched Metal Connection
```

---

## p.23

![p.23](pages/p23.png)

```text
F. Maloberti - Layout of Analog CMOS IC
23
Waffle Transistor
S
D
Minimum capacitance
drain-substrate and
source-substrate
W not accurate
L not well defined
To be used in wide transistors
whose aspect ratio is not
relevant
```

---

## p.24

![p.24](pages/p24.png)

```text
F. Maloberti - Layout of Analog CMOS IC
24
Part II: Transistor and Basic Cell Layout
Transistors  and Matched Transistors
Layout of a single transistor
Use of multiple fingers
Interdigitated devices
Common Centroid
Dummy devices on ends
Matched interconnect (metal, vias, contacts)
Surrounded by guard ring
Design for Layout
Stacked layout of analog cells
Stick diagram of analog cells
Example 1: two stages op-amp
Example 2: folded cascode
```

---

## p.25

![p.25](pages/p25.png)

```text
F. Maloberti - Layout of Analog CMOS IC
25
Stacked Layout
Systematic use of stack or transistors (multi-finger
arrangement)
Same width of the fingers in the same stack, possibly
different length
Design procedure
Examine the size of transistors in the cell
Split transistors size in a number of layout oriented fingers
Identify the transistors that can be placed on the same stack
Possibly change the size of non-critical transistors
Use (almost) the same number of finger per stack
place stacks and interconnect
```

---

## p.26

![p.26](pages/p26.png)

```text
F. Maloberti - Layout of Analog CMOS IC
26
Stick Representation (one transistor)
s d
s
d
s
s d
s
d
d
s d
s
d
s d
s
d
Ending drain
Ending source
D/S ending
S/D ending
s
d
EVEN
ODD
```

---

## p.27

![p.27](pages/p27.png)

```text
F. Maloberti - Layout of Analog CMOS IC
27
Multi-transistor Stick Diagram
1
2
3
1 2 3
4
4
1 2 3 4
2
Same width
M1
M2
M3
M1 double
1 2 1 2 3 2 3 4 3 4
M1
M2
M3
3 4 3 2 1 2 3 4 3
M3 M2 M1 M2 M3
3 4 3
2
2 3 4 3
M3 M2
M1
M2 M3
2
1
1
3
2
4
1
```

---

## p.28

![p.28](pages/p28.png)

```text
F. Maloberti - Layout of Analog CMOS IC
28
Example 1 (2 stages OTA)
M1
M2
M3
M4
M5
M6
M7
60
60
40
30
30
72
108
Assume to layout a two stages OTA
Width only are shown; 
Compensation network and bias are missing (!)
```

---

## p.29

![p.29](pages/p29.png)

```text
F. Maloberti - Layout of Analog CMOS IC
29
Layout Oriented Design
M1
M2
M3
M4
M5
M6
M7
60
60
40
30
30
72
108
Possible stacks:
1 p-channel, 2 n-channel
change the size of M6 and M7 
to 80 and 120 respectively
Width of each finger?
We want the same number of 
fingers per stack (k).
Wp1 = 180/k
Wn1=120/k
Wn2=120/k
for M3 and M4 use 2 fingers
M3, M4, M6
M1, M2
M5, M7
Only width matters
```

---

## p.30

![p.30](pages/p30.png)

```text
F. Maloberti - Layout of Analog CMOS IC
30
Stack Design and Interconnections
M1
M2
M3
M4
M5
M6
M7
6
6
4
2
2
8
8
M6
M6
M3
M4
M7
M7
M5
First attempt of
interconnections
(not completed)
GND
OUT
CS
O1
VDD
D3
M1
M2
D3
O1
```

---

## p.31

![p.31](pages/p31.png)

```text
F. Maloberti - Layout of Analog CMOS IC
31
Use of one Metal Layer
M1
M2
M3
M4
M5
M6
M7
GND
OUT
CS
O1
VDD
D3
GND
VDD
M1
CS
O1
OUT
M2
M4
M3
Use metal for carrying 
current!
Poly connections are
not a problem (usually)
M5
M5
```

---

## p.32

![p.32](pages/p32.png)

```text
F. Maloberti - Layout of Analog CMOS IC
32
Stick Layout: Exercise
Draw the stick diagram of the two stages OTA in 
the following three cases:
• fingers of M6 and M7 all together
• M6 =90 M7=60
• M1 and M2 in a common centroid arrangement
```

---

## p.33

![p.33](pages/p33.png)

```text
F. Maloberti - Layout of Analog CMOS IC
33
From Stick to Layout
Input-Output
Well and its bias
Substrate bias
Compensation
Bias voltage
Bias current
VDD
GND
Rectangular shape
System oriented cell layout
Related cells with same height
Vdd and GND crossing the cell
In and Out properly placed
```

---

## p.34

![p.34](pages/p34.png)

```text
F. Maloberti - Layout of Analog CMOS IC
34
Example 2 (Folded Cascode)
M1
M2
M3
M4
M11
M5
M7
M9
M6
M8
M10
30
30
80
80
MN
60
60
16
16
38
38
25
25
Only Ws are shown
20
MP
```

---

## p.35

![p.35](pages/p35.png)

```text
F. Maloberti - Layout of Analog CMOS IC
35
Split of Transistors
M1
M2
M3
M4
M11
M5
M7
M9
M6
M8
M10
30
30
80
80
MN
60
60
16
16
40
40
24
24
20
2
3
3
6
6
25
38
5
2
5
3
3
2
MP
```

---

## p.36

![p.36](pages/p36.png)

```text
F. Maloberti - Layout of Analog CMOS IC
36
Stack Design
M1
M2
M3
M4
M11
M5
M7
M9
M6
M8
M10
MN
2
3
3
6
6
5
2
5
3
3
2
MP
10x2
555555344PP334666666
11221122112211221122
22112211221122112211
777779xxoo99nno88888
X=11; o=10
```

---

## p.37

![p.37](pages/p37.png)

```text
F. Maloberti - Layout of Analog CMOS IC
37
Interconnection: Exercise
Sketch the source-drain interconnections of the folded-cascode
```

---

## p.38

![p.38](pages/p38.png)

```text
F. Maloberti - Layout of Analog CMOS IC
38
Basic Cell Design: check-list
Draw a well readable transistor
diagram
Identify critical elements and
nodes
Absolute and relative accuracy
Minimum parasitic capacitance
Minimum interference
Mark transistors that must
match
Mark symmetry axes
Analyze transistor sizing (W’s)
Possibly, change transistor size
for a layout oriented strategy
Group transistors in stacks
Define the expected height
(or width) of the cell
Sketch the stick diagram
transistors of the same type in
the same region
Foresee room for substrate
and well biasing
substrate bias around the cell
well-bias surrounding the well
Define the connection layer
for input-output (horizontal,
vertical connections)
Begin the layout now!!
```
