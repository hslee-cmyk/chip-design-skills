# V. Srinivasan, G. J. Serrano, J. Gray, P. Hasler, 'A Precision CMOS Amplifier Using Floating-Gate Transistors for Offset Cancellation', IEEE JSSC 42(2):280-291, 2007

- 원본 PDF: 웹 다운로드(아래 웹 출처, 2026-10-15). 로컬 원문 보관처(G:/내 드라이브/work/Todoc/논문모음 등)에서 찾지 못함
- 사본: `source.pdf` (sha256 `99dcddacfe49221ff2b5a00dd5319d15f27eb0ebcfac47ec2aceac2405149caf`)
- 웹 출처: https://hasler.ece.gatech.edu/Courses/ECE4430/Proj3/CMOS_Amplifier_Offset_2007.pdf
- 쪽 수: 11
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

```text
280
IEEE JOURNAL OF SOLID-STATE CIRCUITS, VOL. 42, NO. 2, FEBRUARY 2007
A Precision CMOS Amplifier Using Floating-Gate
Transistors for Offset Cancellation
Venkatesh Srinivasan, Member, IEEE, Guillermo J. Serrano, Jordan Gray, and Paul Hasler, Senior Member, IEEE
Abstract—A long-term offset cancellation scheme that enables
continuous-time amplifier operation is described. Offset cancel-
lation is achieved by programming floating-gate transistors that
form an integral part of the amplifier’s architecture. The offset
voltage of a single-stage folded cascode amplifier has been pro-
grammed to a minimum of
25
V in a 0.5
m digital CMOS
process. The long-term offset voltage drift has been calculated to
be less than 0.5
V over a period of 10 years at 55 C from a
thermionic emission model for floating-gate charge loss. The offset
voltage varies by a maximum of 130
V over a temperature range
of 170 C, thereby making this a viable approach to offset cancel-
lation.
Index Terms—Charge retention, floating-gate drift, floating-gate
transistors, input offset voltage, offset cancellation.
I. OFFSET REMOVAL TECHNIQUES
M
ISMATCHES between MOS transistors pose a serious
challenge to analog circuit designers and most com-
monly manifest themselves as an offset voltage in operational
amplifiers. Techniques commonly used to reduce the offset
voltage include auto-zeroing, correlated double sampling and
chopper stabilization [1]. Auto-zeroing and correlated double
sampling are techniques applicable to sampled data systems
while chopper stabilization allows continuous-time operation
of the amplifier. Resistor trimming using laser trims is another
popular approach. This, however, is usually expensive. Another
technique includes using current-mode digital-to-analog con-
verters (DACs) to compensate for amplifier offsets by adjusting
amplifier load currents [2].
In this paper, a floating-gate based offset cancellation scheme
is presented that results in a continuous-time operation of the
amplifier with long-term offset cancellation that obviates the
need for any refresh circuitry. A prototype amplifier has been
fabricated with its offset voltage reduced to 25
V. The use of
floating-gate transistors for correcting mismatches in analog cir-
cuitry is particularly advantageous as it offers programmability,
long-term retention and can be fabricated in a standard digital
CMOS process. This approach involves no sampling and hence
avoids such issues as charge injection, clock feedthrough and
undersampled wideband noise that are serious limitations to au-
tozeroing and correlated double sampling [1], [3]. Also, unlike
Manuscript received December 8, 2005; revised October 12, 2006.
V. Srinivasan is with Texas Instruments Incorporated, Dallas, TX 75243 USA
(e-mail: v-srinivasan@ti.com).
G. Serrano, J. Gray, and P. Hasler are with the School of Electrical and Com-
puter Engineering, Georgia Institute of Technology, Atlanta, GA 30332-0250
USA (e-mail: gserrano@ece.gatech.edu; jgray@ece.gatech.edu; phasler@ece.
gatech.edu).
Digital Object Identifier 10.1109/JSSC.2006.889365
Fig. 1. Offset cancellation macromodel. The offset voltage of the amplifier
is cancelled by programming an offset current
in the opposite direction on
floating-gate transistors.
chopper stabilization [1], the proposed scheme is not limited
to low-bandwidth applications, while at the same time offering
continuous-time operation with comparable offset reduction.
The proposed scheme involves using floating-gate transistors
as both an integral part of the circuit of interest and as pro-
grammable elements. Fig. 1 shows a conceptual representation
of the proposed scheme applied towards offset cancellation in
an operational amplifier. Floating-gate transistors are used as
programmable current sources
that provide offset com-
pensation while being a part of the amplifier of interest during
normal operation. Such an approach results in a compact archi-
tecture with a simple design strategy that avoids the overhead of
using floating-gate transistors as separate trimming elements as
in [4] and [5] or current-mode DACs as trimming elements [2].
Also, the proposed offset cancellation scheme is independent of
other amplifier parameters, unlike other approaches [1], [6] and
the offset cancellation by itself dissipates no additional power.
Section II describes floating-gate transistors and the program-
ming scheme used to modify charge on the same. Sections III
and IV discuss two key aspects of a floating-gate device, namely,
the programming precision and charge retention. The use of
floating-gate transistors as part of a folded-cascode amplifier
is described in Section V along with a theoretical analysis of
the input referred offset voltage and its temperature dependence.
Section VI presents experimental results for the proposed am-
plifier fabricated in a 0.5
m standard digital CMOS process.
Finally, Section VII compares the proposed scheme with alter-
nate approaches and Section VIII concludes by summarizing the
results and the implications of the proposed approach.
II. FLOATING-GATE MOS TRANSISTOR
Floating-gate transistors are commonly used as nonvolatile
memory elements in EEPROMs [7], [8]. A floating-gate MOS
0018-9200/$25.00 © 2007 IEEE
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

![p.2 내장 이미지 17](images/p02_17.png)

![p.2 내장 이미지 18](images/p02_18.png)

![p.2 내장 이미지 19](images/p02_19.png)

![p.2 내장 이미지 20](images/p02_20.png)

![p.2 내장 이미지 21](images/p02_21.png)

![p.2 내장 이미지 22](images/p02_22.png)

![p.2 내장 이미지 23](images/p02_23.png)

![p.2 내장 이미지 24](images/p02_24.png)

![p.2 내장 이미지 25](images/p02_25.png)

![p.2 내장 이미지 26](images/p02_26.png)

![p.2 내장 이미지 27](images/p02_27.png)

![p.2 내장 이미지 28](images/p02_28.png)

![p.2 내장 이미지 29](images/p02_29.png)

![p.2 내장 이미지 30](images/p02_30.png)

```text
SRINIVASAN et al.: A PRECISION CMOS AMPLIFIER USING FLOATING-GATE TRANSISTORS FOR OFFSET CANCELLATION
281
Fig. 2. Circuit schematic and layout of a pFET floating-gate transistor. The
floating-gate node
is completely surrounded by SiO
and external inputs
are coupled onto the floating node through an input capacitor
. The capac-
itor
is used for Fowler–Nordheim tunneling. The input capacitor is im-
plemented using a poly–poly capacitor, while the tunneling capacitor is imple-
mented using a MOS capacitor.
transistor is a transistor whose polysilicon gate is completely
surrounded by SiO , a high-quality insulator. This creates a po-
tential barrier that prevents charge stored on the floating gate
from leaking from the floating node. Fig. 2 shows the circuit
schematic and layout of a single-poly floating-gate pMOS tran-
sistor. In order to maintain the nonvolatile charge storage of the
floating gate, external inputs are capacitively coupled through an
input capacitor
. It should be noted that the second polysil-
icon layer shown in Fig. 2 is used primarily to implement the
input capacitor. The tunneling capacitor
is implemented
using the gate oxide between the gate polysilicon and n-well.
A. Programming a Floating-Gate Transistor
Programming a floating-gate transistor involves adding or re-
moving charge from the floating gate, thereby modulating the
threshold voltage of the device. This is achieved through the
physical phenomena of hot-electron injection that adds elec-
trons to the floating gate and Fowler–Nordheim tunneling [9]
that is used to remove electrons. Using hot-electron injection
and tunneling, a floating-gate pFET transistor has been pro-
grammed to different threshold voltages with their magnitudes
ranging from 0.75–2.75 V as demonstrated in Fig. 3. It should
be noted that the absolute value of the threshold voltage of a
pFET device that is not a floating gate in the 0.5
m process
used is 0.9 V. Fig. 3 demonstrates the wide range in program-
ming capabilities of the floating-gate device.
The logarithmic nature of tunneling makes precision pro-
gramming time-consuming. Techniques have been proposed
to improve the speed and precision of tunneling-based pro-
gramming [10], [11]. However, in this work, tunneling is used
primarily as a global erase and precision programming is
achieved through hot-electron injection. Such a scheme has a
number of advantages over a tunneling-based programming
scheme as in [4] and [5]. These include avoiding special
processing steps such as ultrathin tunneling oxides and high
voltages of both positive and negative polarities.
Hot-electron injection occurs in pFETs when carriers are ac-
celerated to a high enough energy level to surmount the Si-SiO
Fig. 3. Programming a floating-gate pFET transistor. A floating-gate
pFET has been programmed using a combination of hot-electron injection
and Fowler–Nordheim tunneling. Hot-electron injection adds electrons to
the floating gate, thereby decreasing the threshold voltage of the device.
Fowler–Nordheim tunneling removes electrons from the floating gate and leads
to an increase in the threshold voltage.
barrier. At high drain currents, electrons are created at the drain
edge of the drain-to-channel depletion region via hot-hole im-
pact ionization. These electrons travel back into the channel
region, gain sufficient kinetic energy such that they cross the
Si-SiO barrier and are injected onto the floating gate [12]. Con-
ditions conducive for injection are created when the transistor
experiences a high source–drain potential and when there is
channel current flowing through the device.
Fig. 4(a) shows the use of floating-gate transistors as part
of analog circuitry. During normal operation, a digital Low is
applied to prog, thereby switching the floating-gate transistors
into the circuit of interest. The operating
is 3.3 V during
normal operation. Programming is achieved by first isolating
the floating-gate transistor from the rest of the circuitry such
that one can access the gate and drain terminals of the device.
This is achieved by applying a digital High to the prog terminal.
The drain of the floating-gate transistor of interest that needs
to be programmed is then switched to the external drain ter-
minal
using the digital selection circuitry shown. The drains
of the unselected devices are tied to
. It should be noted
that all floating-gate transistors share the same gate terminal
during program mode. The tunneling terminal is shared among
all floating-gate devices as well.
Fig. 4(b) shows a pictorial representation of the hot-elec-
tron injection process. To perform hot-electron injection on a
floating-gate transistor, the chip is ramped up such that
is
increased to 6.5 V with all other voltages increased with respect
to
as well. Next, the high fields necessary for injection are
created by pulsing down the drain voltage
for a certain
amount of time
such that a high source–drain voltage ap-
pears across the device. Typical
voltages used for hot-elec-
tron injection range from 4–6.5 V for a 0.5
m CMOS process.
After injection is completed, the chip is ramped down such that
all voltages are restored to their original values. The number of
electrons injected and hence the change in the drain current is a
```

---

## p.3

![p.3](pages/p03.png)

![p.3 내장 이미지 1](images/p03_1.png)

![p.3 내장 이미지 2](images/p03_2.png)

![p.3 내장 이미지 3](images/p03_3.png)

![p.3 내장 이미지 4](images/p03_4.png)

![p.3 내장 이미지 5](images/p03_5.png)

![p.3 내장 이미지 6](images/p03_6.png)

![p.3 내장 이미지 7](images/p03_7.png)

![p.3 내장 이미지 8](images/p03_8.png)

![p.3 내장 이미지 9](images/p03_9.png)

![p.3 내장 이미지 10](images/p03_10.png)

![p.3 내장 이미지 11](images/p03_11.png)

![p.3 내장 이미지 12](images/p03_12.png)

![p.3 내장 이미지 13](images/p03_13.png)

![p.3 내장 이미지 14](images/p03_14.png)

![p.3 내장 이미지 15](images/p03_15.png)

![p.3 내장 이미지 16](images/p03_16.png)

![p.3 내장 이미지 17](images/p03_17.png)

![p.3 내장 이미지 18](images/p03_18.png)

![p.3 내장 이미지 19](images/p03_19.png)

![p.3 내장 이미지 20](images/p03_20.png)

![p.3 내장 이미지 21](images/p03_21.png)

![p.3 내장 이미지 22](images/p03_22.png)

![p.3 내장 이미지 23](images/p03_23.png)

```text
282
IEEE JOURNAL OF SOLID-STATE CIRCUITS, VOL. 42, NO. 2, FEBRUARY 2007
Fig. 4. Floating-gate transistors in analog circuitry and hot-electron injection. (a) The use of multiple floating-gate transistors as part of analog circuitry is shown.
Applying a digital High to prog switches the floating-gate transistors into program mode. The floating-gate transistor of interest is then selected using the digital
selection circuitry. (b) Pictorial representation of the hot-electron injection process.
function of the source–drain potential
and the time interval
for which
is held high enough.
Automatic programming of floating-gate transistors is
achieved using a programming algorithm that calculates the
value of the source–drain potential and the number of pulses
required (with
held fixed) such that a target current is
reached without any overshoot. The value of
for a given
pulse interval is estimated from the relationship between the
initial drain current and the desired target current. This is
obtained from a first-principles model for hot-electron injection
and is described in detail in [12] and [13]. A single initial
calibration step that characterizes the hot-electron injection
rates for a given process is performed such that the algorithm
can predict an optimal value of
during injection. Program-
ming proceeds by first measuring the initial drain current of
the device. This is used by the programming algorithm along
with the target drain current to calculate the optimal value of
for a fixed pulse interval of about 100
s. The chip is then
ramped up and the calculated
is applied. The chip is then
ramped down and the drain current is measured again. If the
measured current is different from the target current, the algo-
rithm calculates a new
value and injection is performed
again. The above steps are repeated until the drain current of the
device reaches the target value within a pre-defined tolerance.
Since the injection rates vary between devices, programming
is performed asymptotically such that overshoot is avoided.
Typical convergence to target to within a 0.1% accuracy takes
about 7–12 pulses.
Fig. 5 [13] demonstrates the programming algorithm when
the drain current of the device is programmed to different target
currents (logarithmical spaced) from an initial current of 10 nA.
As can be observed, typically around 7 pulses are required to
Fig. 5. Programming algorithm [13]. The convergence of the programming al-
gorithm for different target currents from an initial starting current of 10 nA is
shown. The algorithm convergence to within 0.1% of the target current in all
cases with the pulsewidth being 100
s.
reach the target with the worst case of 11 pulses for a pro-
gramming change of two orders of magnitude. A pulsewidth of
100
s has been used in this case.
III. FLOATING-GATE PROGRAMMING PRECISION
The accuracy to which one can program floating-gate tran-
sistors to a target current depends on the smallest drain current
change that can be programmed onto a floating-gate device. In
order to estimate the design choices available to improve pro-
gramming precision, a figure of merit (FOM) is defined as
FOM
(1)
```

---

## p.4

![p.4](pages/p04.png)

![p.4 내장 이미지 1](images/p04_1.png)

![p.4 내장 이미지 2](images/p04_2.png)

![p.4 내장 이미지 3](images/p04_3.png)

![p.4 내장 이미지 4](images/p04_4.png)

![p.4 내장 이미지 5](images/p04_5.png)

![p.4 내장 이미지 6](images/p04_6.png)

![p.4 내장 이미지 7](images/p04_7.png)

![p.4 내장 이미지 8](images/p04_8.png)

![p.4 내장 이미지 9](images/p04_9.png)

![p.4 내장 이미지 10](images/p04_10.png)

![p.4 내장 이미지 11](images/p04_11.png)

![p.4 내장 이미지 12](images/p04_12.png)

![p.4 내장 이미지 13](images/p04_13.png)

![p.4 내장 이미지 14](images/p04_14.png)

![p.4 내장 이미지 15](images/p04_15.png)

![p.4 내장 이미지 16](images/p04_16.png)

![p.4 내장 이미지 17](images/p04_17.png)

![p.4 내장 이미지 18](images/p04_18.png)

![p.4 내장 이미지 19](images/p04_19.png)

![p.4 내장 이미지 20](images/p04_20.png)

![p.4 내장 이미지 21](images/p04_21.png)

![p.4 내장 이미지 22](images/p04_22.png)

![p.4 내장 이미지 23](images/p04_23.png)

![p.4 내장 이미지 24](images/p04_24.png)

![p.4 내장 이미지 25](images/p04_25.png)

![p.4 내장 이미지 26](images/p04_26.png)

![p.4 내장 이미지 27](images/p04_27.png)

![p.4 내장 이미지 28](images/p04_28.png)

![p.4 내장 이미지 29](images/p04_29.png)

![p.4 내장 이미지 30](images/p04_30.png)

![p.4 내장 이미지 31](images/p04_31.png)

![p.4 내장 이미지 32](images/p04_32.png)

![p.4 내장 이미지 33](images/p04_33.png)

![p.4 내장 이미지 34](images/p04_34.png)

![p.4 내장 이미지 35](images/p04_35.png)

![p.4 내장 이미지 36](images/p04_36.png)

![p.4 내장 이미지 37](images/p04_37.png)

![p.4 내장 이미지 38](images/p04_38.png)

![p.4 내장 이미지 39](images/p04_39.png)

![p.4 내장 이미지 40](images/p04_40.png)

![p.4 내장 이미지 41](images/p04_41.png)

![p.4 내장 이미지 42](images/p04_42.png)

```text
SRINIVASAN et al.: A PRECISION CMOS AMPLIFIER USING FLOATING-GATE TRANSISTORS FOR OFFSET CANCELLATION
283
Fig. 6. Programming precision. (a) The FOM is independent of the drain current in the weak inversion region of operation and increases as the transistor enters
the strong inversion regime. The experimental results are consistent with the theoretical prediction. (b) Programming a 20 nA sinusoid riding on a DC value of
1
A is shown along with the percentage error between the programmed current and the desired target. As can be observed, an error of
0.05% has been achieved.
where
is the minimum programmable change in drain cur-
rent that is necessary to meet a system level accuracy specifi-
cation and
is the bias current of the floating-gate transistor. It
should be noted that such a definition results in the FOM being
represented in the familiar binary system, as the number of bits
of accuracy achievable. In the discussion below, the FOM is re-
lated to floating-gate circuit parameters for operation in both the
weak and strong inversion regimes such that the floating-gate
transistor can be designed to achieve the required bits of preci-
sion.
Consider a floating-gate pFET operating in the weak inver-
sion regime. The source–drain current of the device, ignoring
Early effect, is given by [14]–[16]
(2)
where
is the pre-exponential constant,
is the thermal
voltage given by
,
,
and
are the floating-gate,
source, and bulk voltages referenced to ground, respectively,
and
is the threshold voltage of
the device referenced to the bulk terminal. Detailed analytical
expressions for the various terms in the above equation, such as
and
, can be found in [15] and [16].
Now, for a
change in the floating-gate voltage due to
programming, a
change in drain current results. Noting that
, the achievable change in drain current due
to programming relative to the initial drain current is given by
(3)
where
is the total capacitance at the floating gate and
is the programmed charge. It is clear from (3) that the achiev-
able precision is directly proportional to the charge that can be
reliably transferred onto the floating gate and inversely propor-
tional to the total floating-gate capacitance.
Similarly, for a floating-gate nFET operating in the strong
inversion regime, the change in the drain current relative to the
initial drain current is given by
(4)
where
, is the overdrive voltage. The
above equation is derived by assuming that the change in gate
voltage due to programming is much smaller than the overdrive
voltage of the device. As can be observed from (4), the achiev-
able precision is directly proportional to the charge that can be
transferred onto the floating-gate and inversely proportional to
the overdrive voltage of the device and the total floating-gate
capacitance.
In order to verify the theory presented above, a test chip was
fabricated in a 0.5
m standard CMOS process. Noting that for
a transistor operating in the strong inversion regime an alternate
expression for the overdrive voltage is
, it can
be inferred from (4) that the FOM is inversely proportional to
the square root of the drain current. Also, from (3), it is clear
that the FOM is independent of drain current in the weak inver-
sion regime. Therefore, one would expect that the plot of FOM
versus drain current would be constant in the weak inversion
regime and would increase in the strong inversion regime. This
was verified by injecting a constant charge onto a floating-gate
transistor and by measuring the I–V characteristic both before
and after injection. Calculating the difference in currents be-
tween the I–V sweeps and plotting against the initial set of cur-
rents results in the plot shown in Fig. 6(a). As can be observed,
the plot is constant in the weak inversion regime and increases
in the strong inversion regime, thereby verifying the theory.
Table I presents quantitative numbers for the FOM for both
the weak inversion and strong inversion regions based on the
theory developed above. The FOM has been calculated for dif-
ferent values of charge transfer and
for a
of 0.7,
of
26 mV, and an overdrive voltage of 250 mV. Fig. 6(b) presents
```

---

## p.5

![p.5](pages/p05.png)

![p.5 내장 이미지 1](images/p05_1.png)

![p.5 내장 이미지 2](images/p05_2.png)

![p.5 내장 이미지 3](images/p05_3.png)

![p.5 내장 이미지 4](images/p05_4.png)

![p.5 내장 이미지 5](images/p05_5.png)

![p.5 내장 이미지 6](images/p05_6.png)

![p.5 내장 이미지 7](images/p05_7.png)

![p.5 내장 이미지 8](images/p05_8.png)

![p.5 내장 이미지 9](images/p05_9.png)

![p.5 내장 이미지 10](images/p05_10.png)

![p.5 내장 이미지 11](images/p05_11.png)

![p.5 내장 이미지 12](images/p05_12.png)

![p.5 내장 이미지 13](images/p05_13.png)

![p.5 내장 이미지 14](images/p05_14.png)

![p.5 내장 이미지 15](images/p05_15.png)

![p.5 내장 이미지 16](images/p05_16.png)

![p.5 내장 이미지 17](images/p05_17.png)

![p.5 내장 이미지 18](images/p05_18.png)

![p.5 내장 이미지 19](images/p05_19.png)

![p.5 내장 이미지 20](images/p05_20.png)

![p.5 내장 이미지 21](images/p05_21.png)

![p.5 내장 이미지 22](images/p05_22.png)

![p.5 내장 이미지 23](images/p05_23.png)

![p.5 내장 이미지 24](images/p05_24.png)

![p.5 내장 이미지 25](images/p05_25.png)

![p.5 내장 이미지 26](images/p05_26.png)

![p.5 내장 이미지 27](images/p05_27.png)

![p.5 내장 이미지 28](images/p05_28.png)

![p.5 내장 이미지 29](images/p05_29.png)

![p.5 내장 이미지 30](images/p05_30.png)

![p.5 내장 이미지 31](images/p05_31.png)

![p.5 내장 이미지 32](images/p05_32.png)

![p.5 내장 이미지 33](images/p05_33.png)

![p.5 내장 이미지 34](images/p05_34.png)

![p.5 내장 이미지 35](images/p05_35.png)

![p.5 내장 이미지 36](images/p05_36.png)

![p.5 내장 이미지 37](images/p05_37.png)

![p.5 내장 이미지 38](images/p05_38.png)

```text
284
IEEE JOURNAL OF SOLID-STATE CIRCUITS, VOL. 42, NO. 2, FEBRUARY 2007
TABLE I
SUMMARY OF THE ACHIEVABLE BITS OF ACCURACY (FOM)
Fig. 7. Drain current of a floating-gate pFET. (a) The drain current of a floating-gate pFET measured over 16 days. The floating-gate transistor was programmed to
an initial value of 30
A. (b) The drain current distribution indicates a mean of 29.927
A with a standard deviation of 27.8 nA. The Gaussian nature of distribution
indicates the presence of thermal noise on the measured data.
experimental data from programming an array of floating-gate
transistors to result in a sinusoid with a DC offset of 1
A and
an amplitude of 20 nA. Also shown is the percentage error in
the programmed value of the sine wave to the ideal value. The
error is within
0.05%, indicating an FOM of approximately
11 bits. The total floating-gate capacitance for these transistors
is approximately 100 fF. With the devices operating in strong
inversion, it can be inferred from Table I that a little over 100
electrons worth of charge is responsible for the measured pre-
cision. Using the above developed theory and depending on the
region of operation of the floating-gate transistor, one can de-
sign a floating-gate transistor (
and
) such that a target
accuracy specification is met.
IV. FLOATING-GATE CHARGE RETENTION
Floating-gate transistors inherently have good charge reten-
tion capabilities on account of the gate being surrounded by a
high-quality insulator. Initial investigations of floating-gate re-
tention were carried out by observing the drain current of a
floating-gate device for long periods of time. Fig. 7(a) shows the
drain current of a floating-gate pFET measured over a period of
380 hours. The drain current was programmed from a current of
A to an initial value of 30
A and displayed a mean value
of 29.93
A with a standard deviation of 28 nA [see Fig. 7(b)].
The current exhibits a short-term drift in the beginning, beyond
which no significant drift can be observed. This short-term drift
is on account of the interface trap sites settling to a new equilib-
rium after programming [5]. Similar results have been observed
in a 1.5
m CMOS process [17]. Although this is a good indi-
cator of the charge retention capabilities of floating-gate tran-
sistors, accurate estimates of the long-term charge retention can
be made through accelerated lifetime tests.
Long-term charge loss in floating-gate transistors occurs due
to the phenomenon of thermionic emission [4], [5], [18], [19].
The amount of charge lost is a function of both temperature and
time and is given by
(5)
where
is the initial charge on the floating-gate,
is the
floating-gate charge at time ,
is the relaxation frequency of
electrons in polysilicon,
is the Si-SiO barrier potential in
electron-volts,
is Boltzmann’s constant, and
is the temper-
ature. As expected from (5), charge loss in floating-gates is a
slow process that is accelerated at high temperatures.
Floating-gate charge loss is measured indirectly by measuring
the change in the transistor’s threshold voltage. Programming
floating-gate transistors by adding/removing charge modifies
the threshold voltage of the device
as given by
(6)
where
is the floating-gate charge,
is the threshold voltage
of the transistor with zero floating-gate charge or that of a non-
floating-gate device, and
is the total capacitance at the gate
node. Using the above approximation for the threshold voltage
```

---

## p.6

![p.6](pages/p06.png)

![p.6 내장 이미지 1](images/p06_1.png)

![p.6 내장 이미지 2](images/p06_2.png)

![p.6 내장 이미지 3](images/p06_3.png)

![p.6 내장 이미지 4](images/p06_4.png)

![p.6 내장 이미지 5](images/p06_5.png)

![p.6 내장 이미지 6](images/p06_6.png)

![p.6 내장 이미지 7](images/p06_7.png)

![p.6 내장 이미지 8](images/p06_8.png)

![p.6 내장 이미지 9](images/p06_9.png)

![p.6 내장 이미지 10](images/p06_10.png)

![p.6 내장 이미지 11](images/p06_11.png)

![p.6 내장 이미지 12](images/p06_12.png)

![p.6 내장 이미지 13](images/p06_13.png)

![p.6 내장 이미지 14](images/p06_14.png)

![p.6 내장 이미지 15](images/p06_15.png)

![p.6 내장 이미지 16](images/p06_16.png)

![p.6 내장 이미지 17](images/p06_17.png)

![p.6 내장 이미지 18](images/p06_18.png)

![p.6 내장 이미지 19](images/p06_19.png)

![p.6 내장 이미지 20](images/p06_20.png)

![p.6 내장 이미지 21](images/p06_21.png)

![p.6 내장 이미지 22](images/p06_22.png)

![p.6 내장 이미지 23](images/p06_23.png)

![p.6 내장 이미지 24](images/p06_24.png)

![p.6 내장 이미지 25](images/p06_25.png)

![p.6 내장 이미지 26](images/p06_26.png)

![p.6 내장 이미지 27](images/p06_27.png)

![p.6 내장 이미지 28](images/p06_28.png)

![p.6 내장 이미지 29](images/p06_29.png)

![p.6 내장 이미지 30](images/p06_30.png)

![p.6 내장 이미지 31](images/p06_31.png)

![p.6 내장 이미지 32](images/p06_32.png)

![p.6 내장 이미지 33](images/p06_33.png)

![p.6 내장 이미지 34](images/p06_34.png)

![p.6 내장 이미지 35](images/p06_35.png)

![p.6 내장 이미지 36](images/p06_36.png)

![p.6 내장 이미지 37](images/p06_37.png)

![p.6 내장 이미지 38](images/p06_38.png)

![p.6 내장 이미지 39](images/p06_39.png)

![p.6 내장 이미지 40](images/p06_40.png)

![p.6 내장 이미지 41](images/p06_41.png)

![p.6 내장 이미지 42](images/p06_42.png)

![p.6 내장 이미지 43](images/p06_43.png)

![p.6 내장 이미지 44](images/p06_44.png)

![p.6 내장 이미지 45](images/p06_45.png)

![p.6 내장 이미지 46](images/p06_46.png)

![p.6 내장 이미지 47](images/p06_47.png)

![p.6 내장 이미지 48](images/p06_48.png)

![p.6 내장 이미지 49](images/p06_49.png)

![p.6 내장 이미지 50](images/p06_50.png)

![p.6 내장 이미지 51](images/p06_51.png)

![p.6 내장 이미지 52](images/p06_52.png)

```text
SRINIVASAN et al.: A PRECISION CMOS AMPLIFIER USING FLOATING-GATE TRANSISTORS FOR OFFSET CANCELLATION
285
TABLE II
SUMMARY OF FLOATING-GATE PARAMETER CHANGE IN 10 YEARS
of a floating-gate device, the charge loss in a floating gate can
be rewritten as
(7)
where
indicates the threshold voltage of the device after
time
and
represents the initial programmed threshold
voltage.
Estimating the amount of charge loss in floating-gate transis-
tors requires the estimation of the parameters
and
as these
parameters exhibit a wide spread in their values and therefore
need to be extracted for each process. For the 0.5
m process
used in the design, floating-gate pFETs were programmed to
a threshold voltage of
0.5 V and stored at high temperatures
for a predefined time period. The change in threshold voltage is
measured and using (7) the charge loss is estimated. Using (5),
(7), and the measured data points,
and
can be extracted
using
(8)
where
denotes the ratio of the floating-gate charge at time
to the initial floating-gate charge and the subscripts denote two
different data points. Using the above procedure, the values for
the barrier potential and the relaxation frequency were extracted
to be 0.9 eV and 60
for the 0.5
m CMOS process used in
the experiments.
Fig. 8 shows the measured floating-gate charge loss along
with a theoretical extrapolated fit using the estimated model pa-
rameters. The measured data agrees well with the theoretical
prediction and the trends observed in Fig. 8 have been observed
across many floating-gate devices.
Now, consider two identical floating-gate transistors that
have been programmed to a difference in current of
,
resulting in a differential floating-gate pair. Assuming weak
inversion operation and noting that the analysis is similar to
that in Section III, the difference in charge between the two
floating gates is given by
(9)
where all the variables have their usual meaning. Now, using (5)
and the extracted values of
and , the difference in charge at
time , namely
, can be estimated. From this, the differ-
ence in floating-gate voltage can be calculated, based on which
and using (9), the value of the programmed difference current
Fig. 8. Charge loss in floating-gate transistors. Charge loss measured at
different temperatures and time periods as estimated from threshold voltage
changes is plotted using
’s. Parameters for a thermionic emission model were
extracted using the measured data and the model is then used to calculate charge
loss at different temperatures and time periods. This extrapolated theoretical fit
is plotted using solid lines.
at time
can be estimated. Table II summarizes the
data retention numbers for two different cases of programmed
difference currents, namely, a 10% change and a 50% change
for a time period of 10 years for different temperatures. A total
floating-gate capacitance of 100 fF and a
of 0.7 has been as-
sumed for these calculations. As can be observed, floating-gate
transistors display excellent charge retention capabilities.
The nonvolatile charge retention. when combined with pro-
grammability, makes floating-gate transistors well suited for
use in precision analog circuits. Also, the analysis developed in
Section III can be used in designing the aspect ratio and
of
the floating-gate transistors such that a required programming
precision is met. The application of a floating-gate pair with a
difference current programmed between them to the design of
an operational amplifier is considered next.
V. AMPLIFIER ARCHITECTURE
A single-stage folded cascode amplifier, shown in Fig. 9,
demonstrates a practical implementation of the proposed ap-
proach shown in Fig. 1. The currents through the floating-gate
transistor pair
and
are programmed such that they
cancel the offset arising from mismatches in the input dif-
ferential pair
and the cascoded current mirrors
. During normal operation, the multiplexers
and
are set such that the floating-gate transistors are a part of the
operational amplifier. During programming, the floating-gate
transistors are isolated from the amplifier in order to program a
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

![p.7 내장 이미지 10](images/p07_10.png)

![p.7 내장 이미지 11](images/p07_11.png)

![p.7 내장 이미지 12](images/p07_12.png)

![p.7 내장 이미지 13](images/p07_13.png)

![p.7 내장 이미지 14](images/p07_14.png)

![p.7 내장 이미지 15](images/p07_15.png)

![p.7 내장 이미지 16](images/p07_16.png)

![p.7 내장 이미지 17](images/p07_17.png)

![p.7 내장 이미지 18](images/p07_18.png)

![p.7 내장 이미지 19](images/p07_19.png)

![p.7 내장 이미지 20](images/p07_20.png)

![p.7 내장 이미지 21](images/p07_21.png)

![p.7 내장 이미지 22](images/p07_22.png)

![p.7 내장 이미지 23](images/p07_23.png)

![p.7 내장 이미지 24](images/p07_24.png)

![p.7 내장 이미지 25](images/p07_25.png)

![p.7 내장 이미지 26](images/p07_26.png)

![p.7 내장 이미지 27](images/p07_27.png)

![p.7 내장 이미지 28](images/p07_28.png)

![p.7 내장 이미지 29](images/p07_29.png)

![p.7 내장 이미지 30](images/p07_30.png)

![p.7 내장 이미지 31](images/p07_31.png)

![p.7 내장 이미지 32](images/p07_32.png)

![p.7 내장 이미지 33](images/p07_33.png)

![p.7 내장 이미지 34](images/p07_34.png)

![p.7 내장 이미지 35](images/p07_35.png)

![p.7 내장 이미지 36](images/p07_36.png)

![p.7 내장 이미지 37](images/p07_37.png)

![p.7 내장 이미지 38](images/p07_38.png)

![p.7 내장 이미지 39](images/p07_39.png)

![p.7 내장 이미지 40](images/p07_40.png)

![p.7 내장 이미지 41](images/p07_41.png)

![p.7 내장 이미지 42](images/p07_42.png)

![p.7 내장 이미지 43](images/p07_43.png)

![p.7 내장 이미지 44](images/p07_44.png)

![p.7 내장 이미지 45](images/p07_45.png)

![p.7 내장 이미지 46](images/p07_46.png)

![p.7 내장 이미지 47](images/p07_47.png)

![p.7 내장 이미지 48](images/p07_48.png)

![p.7 내장 이미지 49](images/p07_49.png)

![p.7 내장 이미지 50](images/p07_50.png)

![p.7 내장 이미지 51](images/p07_51.png)

![p.7 내장 이미지 52](images/p07_52.png)

![p.7 내장 이미지 53](images/p07_53.png)

![p.7 내장 이미지 54](images/p07_54.png)

![p.7 내장 이미지 55](images/p07_55.png)

![p.7 내장 이미지 56](images/p07_56.png)

```text
286
IEEE JOURNAL OF SOLID-STATE CIRCUITS, VOL. 42, NO. 2, FEBRUARY 2007
Fig. 9. Operational amplifier circuit schematic. A single-stage folded cascode
amplifier that uses floating-gate transistors as trimming elements is shown.
During normal operation switches
and
are set such that floating-gate
transistors
and
are a part of the operational amplifier. Offset voltage
cancellation is achieved by programming a current difference between
and
. Using floating-gate transistors both as a part of the amplifier and as
trimming elements makes the architecture compact and easy to design.
difference current
such that the offset voltage is
nullified.
A key advantage of this architecture is that the programming
transistors are an integral part of the amplifier thereby simpli-
fying the design process. Initially, all transistors including
and
are made non-floating-gate transistors and are designed
to meet the amplifier’s specifications. Next, these transistors
and
are made floating-gate transistors and, based on
the offset requirement of the amplifier, an estimate can be made
of the programming precision required. In other words, an ap-
proximate value of the difference current
that needs to be
programmed can be estimated, from which the FOM is calcu-
lated. Next, depending on the region of operation of the tran-
sistors
and
, appropriate design equations developed in
Section III can be used to estimate the total floating-gate capac-
itance needed. With the aspect ratio of the transistors set during
the amplifier’s design stage, the input capacitance and the tun-
neling capacitance can be sized to either meet or exceed the
requirement. Appropriate switches are then added to isolate the
floating-gate transistors during programming. For this design,
the floating-gate current sources were set to be 10
A nom-
inally and the total floating-gate capacitance was designed to
be around 200 fF. From Table I it can be seen that a program-
ming precision greater than 10 bits can be achieved for a charge
transfer of around 100 electrons in strong inversion operation,
which is sufficient for the design.
A. Input-Referred Offset Voltage
The amplifier exhibits zero offset voltage when all currents
are balanced at its output. Assume that the amplifier has an
uncompensated offset voltage given by
. Let a current dif-
ference of
be programmed onto the pFET floating-gate
transistors such that this difference current creates a voltage at
the output equal to
, where
represents the effective
output impedance at the output of the amplifier. The input-re-
ferred offset voltage of the amplifier therefore becomes
(10)
where
is the transconductance of the input differential pair.
Therefore, based on (10), one would expect the input-referred
offset voltage of the amplifier to exhibit a linear dependence
with the programmed floating-gate difference current. Note that
the above expression has been derived without assuming any
specific region of device operation.
Now, performing a large-signal analysis by taking into ac-
count the mismatch between the various transistor pairs and
referring their contributions to the input, it can be shown that
for weak inversion operation, the input-referred offset voltage
is given by
(11)
and, similarly, for strong inversion operation, the offset voltage
becomes
(12)
In the above equations, the threshold voltage mismatch between
the input differential pair is accounted for with the threshold
voltage of
being different from that of
by
. In the
case of the transistor pair
, mismatch is represented
by the threshold voltage of
being different from that of
by
. And,
represents the voltage difference be-
tween the floating-gates of
and
on account of the pro-
grammed charge difference between them. Note that both (11)
and (12) simplify to (10) when the necessary small-signal ap-
proximations are made.
B. Temperature Sensitivity
Looking at (11) and (12), it is clear that the temperature sen-
sitivity of the offset voltage can be estimated based on the sen-
sitivities of the threshold voltage mismatch, ratios of transistor
currents and
’s. Note that
is temperature independent
as for a typical operating temperature range, the charge loss on
the floating-gate is negligible and therefore assumed constant,
and to a first order, the total floating-gate capacitance is inde-
pendent of temperature as well.
The temperature dependence of the threshold voltage is given
by [16]
(13)
where
is the temperature in Kelvin,
represents the
threshold voltage at a temperature
, and
represents the linear
temperature coefficient of the threshold voltage. Now, the tem-
perature dependence of the threshold mismatch between two de-
vices can be written as
(14)
```

---

## p.8

![p.8](pages/p08.png)

![p.8 내장 이미지 1](images/p08_1.png)

![p.8 내장 이미지 2](images/p08_2.png)

![p.8 내장 이미지 3](images/p08_3.png)

![p.8 내장 이미지 4](images/p08_4.png)

![p.8 내장 이미지 5](images/p08_5.png)

![p.8 내장 이미지 6](images/p08_6.png)

![p.8 내장 이미지 7](images/p08_7.png)

![p.8 내장 이미지 8](images/p08_8.png)

![p.8 내장 이미지 9](images/p08_9.png)

![p.8 내장 이미지 10](images/p08_10.png)

![p.8 내장 이미지 11](images/p08_11.png)

![p.8 내장 이미지 12](images/p08_12.png)

![p.8 내장 이미지 13](images/p08_13.png)

![p.8 내장 이미지 14](images/p08_14.png)

![p.8 내장 이미지 15](images/p08_15.png)

![p.8 내장 이미지 16](images/p08_16.png)

![p.8 내장 이미지 17](images/p08_17.png)

![p.8 내장 이미지 18](images/p08_18.png)

![p.8 내장 이미지 19](images/p08_19.png)

![p.8 내장 이미지 20](images/p08_20.png)

![p.8 내장 이미지 21](images/p08_21.png)

![p.8 내장 이미지 22](images/p08_22.png)

![p.8 내장 이미지 23](images/p08_23.png)

![p.8 내장 이미지 24](images/p08_24.png)

![p.8 내장 이미지 25](images/p08_25.png)

![p.8 내장 이미지 26](images/p08_26.png)

![p.8 내장 이미지 27](images/p08_27.png)

![p.8 내장 이미지 28](images/p08_28.png)

![p.8 내장 이미지 29](images/p08_29.png)

![p.8 내장 이미지 30](images/p08_30.png)

![p.8 내장 이미지 31](images/p08_31.png)

![p.8 내장 이미지 32](images/p08_32.png)

![p.8 내장 이미지 33](images/p08_33.png)

![p.8 내장 이미지 34](images/p08_34.png)

![p.8 내장 이미지 35](images/p08_35.png)

![p.8 내장 이미지 36](images/p08_36.png)

![p.8 내장 이미지 37](images/p08_37.png)

![p.8 내장 이미지 38](images/p08_38.png)

![p.8 내장 이미지 39](images/p08_39.png)

![p.8 내장 이미지 40](images/p08_40.png)

![p.8 내장 이미지 41](images/p08_41.png)

![p.8 내장 이미지 42](images/p08_42.png)

![p.8 내장 이미지 43](images/p08_43.png)

![p.8 내장 이미지 44](images/p08_44.png)

![p.8 내장 이미지 45](images/p08_45.png)

![p.8 내장 이미지 46](images/p08_46.png)

![p.8 내장 이미지 47](images/p08_47.png)

![p.8 내장 이미지 48](images/p08_48.png)

![p.8 내장 이미지 49](images/p08_49.png)

![p.8 내장 이미지 50](images/p08_50.png)

![p.8 내장 이미지 51](images/p08_51.png)

![p.8 내장 이미지 52](images/p08_52.png)

![p.8 내장 이미지 53](images/p08_53.png)

![p.8 내장 이미지 54](images/p08_54.png)

![p.8 내장 이미지 55](images/p08_55.png)

![p.8 내장 이미지 56](images/p08_56.png)

![p.8 내장 이미지 57](images/p08_57.png)

![p.8 내장 이미지 58](images/p08_58.png)

![p.8 내장 이미지 59](images/p08_59.png)

![p.8 내장 이미지 60](images/p08_60.png)

```text
SRINIVASAN et al.: A PRECISION CMOS AMPLIFIER USING FLOATING-GATE TRANSISTORS FOR OFFSET CANCELLATION
287
Fig. 10. Open loop DC transfer characteristics. The input offset voltage of the
amplifier was programmed to five different values in steps of 10 mV. The non-
inverting terminal of the amplifier was set at 1.65 V and the inverting terminal
was swept from 0–3.3 V. The DC transfer curves show the switching points
ranging from
20 to
20 mV with a 10 mV spacing as programmed.
where
represents the threshold mismatch at tempera-
ture
and
is the difference in their temperature coefficient.
The temperature dependence of
has been analyzed by incor-
porating the temperature dependence of the terms describing
and simulating using MATLAB. Assuming an n-channel tran-
sistor with a threshold voltage of 0.7 V with a temperature co-
efficient of
2 mV
C, a substrate doping of
cm
,
a
of 0.5 and a gate-bulk voltage of 1 V results in a
of
0.8049 at room temperature (300 K). The variation of
with
temperature over a range of
40 C to 140 C was found to be
27 ppm
C. Therefore, it was decided to assume
to be con-
stant with temperature to simplify the temperature analysis of
the amplifier offset voltage.
Next, consider the term
that appears in the expression
for the input offset voltage in the strong inversion region of op-
eration as given in (12). This term can be rewritten as
(15)
where all the terms are as defined earlier. Assuming fixed ter-
minal voltages, the only terms that have a temperature depen-
dence in the above equation are the threshold voltage and mo-
bility. With regards to mobility, for two transistors of the same
type, both the value and the temperature dependence can be as-
sumed constant, thereby making the ratio temperature indepen-
dent. For two transistors that are of dissimilar types, the electron
and hole mobilities have a slightly different temperature depen-
dence [20] and therefore result in a slight temperature depen-
dent mobility ratio. However, for ease of analysis, the electron
and hole mobilities will be treated as similar. With the above
observations, and (14), the third term in (12) can be written as
(16)
Fig. 11. Input offset voltage. (a) The input offset voltage of the amplifier was
measured by programming different current differences between the floating-
gate trimming transistors. The input offset voltage changes linearly with the
difference current as expected from theory. (b) A zoom into the region of very
low offset voltages. It is clear from the figure that offset voltages in the tens of
microvolts are achievable, with the lowest being 25
V.
where
. A similar expression can be arrived
at for the second term in (12). Denoting
as
,
as ,
as , and using (14) in (12)
results in
(17)
A similar analysis can be performed for weak inversion
operation as well. As can be observed from (17), the offset
voltage varies with the temperature and the variation can be
approximated to be quadratic in nature. Also, it is clear that
the offset voltage depends on threshold voltage mismatch
multiplied by a ratio of quantities (transconductance). Since the
threshold voltage mismatch by itself has a weak temperature
```

---

## p.9

![p.9](pages/p09.png)

![p.9 내장 이미지 1](images/p09_1.png)

![p.9 내장 이미지 2](images/p09_2.png)

![p.9 내장 이미지 3](images/p09_3.png)

![p.9 내장 이미지 4](images/p09_4.png)

![p.9 내장 이미지 5](images/p09_5.png)

![p.9 내장 이미지 6](images/p09_6.png)

![p.9 내장 이미지 7](images/p09_7.png)

![p.9 내장 이미지 8](images/p09_8.png)

![p.9 내장 이미지 9](images/p09_9.png)

![p.9 내장 이미지 10](images/p09_10.png)

![p.9 내장 이미지 11](images/p09_11.png)

![p.9 내장 이미지 12](images/p09_12.png)

![p.9 내장 이미지 13](images/p09_13.png)

![p.9 내장 이미지 14](images/p09_14.png)

![p.9 내장 이미지 15](images/p09_15.png)

![p.9 내장 이미지 16](images/p09_16.png)

![p.9 내장 이미지 17](images/p09_17.png)

![p.9 내장 이미지 18](images/p09_18.png)

```text
288
IEEE JOURNAL OF SOLID-STATE CIRCUITS, VOL. 42, NO. 2, FEBRUARY 2007
Fig. 12. Input offset voltage drift. (a) The input offset voltage of the amplifier was measured across a temperature range of
40 C to 130 C. The offset voltage
displayed a maximum change of 130
V across the entire temperature range. The
’s represent the measured data points while the solid line represents the theo-
retical fit based on (17). (b) The input offset voltage of the amplifier was measured for a period of 110 hours at 25 C. The offset was programmed from 1 mV to
a reduced value of around
50
V. It can be observed that after an initial short-term drift, the offset voltage drift is negligible.
dependence, designing the ratio of transconductances to be
fairly temperature independent can result in an overall offset
voltage that is temperature independent. This can be achieved
by either biasing the transistors to their zero-temperature
coefficient transconductances [21], [22] or by designing such
that their overdrive voltages are close to each other, making
the terms
, , and
equal such that temperature sensitivity is
minimized.
VI. AMPLIFIER EXPERIMENTAL RESULTS
Applying (10) and programming the drain currents of tran-
sistors
and
, the amplifier was programmed to five dif-
ferent offset voltages. The offsets were programmed in steps of
10 mV ranging from
20 to
20 mV. Fig. 10 shows the DC
transfer characteristics of the amplifier configured as a com-
parator with the non-inverting terminal held at 1.65 V. As can be
observed, the comparator trip points are evenly spaced 10 mV
apart as programmed. This clearly demonstrates the feasibility
of the approach and the range of programming that is possible.
Accurate measurements of the offset voltage are made by
using the amplifier under test along with a second amplifier
configured as a nulling amplifier forming a servo loop [23].
Fig. 11(a) and (b) shows the measured input-referred offset
voltage of the amplifier plotted against the various programmed
floating-gate transistor difference currents. The measured data
shows a linear dependence of the offset voltage with the pro-
grammed difference currents as expected from (10). As can be
observed in Fig. 11(b), which zooms into the region encircled
in Fig. 11(a), the offset voltage of the prototype amplifier can
be programmed to 25
V. Also, it can be seen that the amplifier
can be programmed to display different offset voltages with
both positive and negative polarities. This clearly demonstrates
the programmable nature of the approach, a feature that could
be exploited when designing, for instance, comparators. Ex-
perimentally, it is possible to program current increments as
low as 0.1 nA. Theoretically, this indicates that offset voltages
in the hundreds of nanovolts range are possible to achieve. At
present, however, the primary limitation has been the internal
noise of the amplifier itself.
Fig. 12(a) shows the sensitivity of the input offset voltage
with temperature. The offset voltage was measured for tem-
peratures ranging from
40 C to 130 C after programming
at 25 C. A maximum change of 130
V was observed over
the full temperature range of 170 C. Since the transistors in
the amplifier were biased in a region close to strong inversion,
the temperature dependence was modelled according to (17).
Shown in the figure is a theoretical fit of the data using (17).
Since the exact values of the threshold voltage mismatch of
the various transistor pairs are unknown, the fit was performed
using a reasonable set of parameter values. It should be noted
that the exact shape of the temperature characteristic depends
on the transistor operating regions, biasing conditions, and the
mismatch between threshold voltages.
In order to experimentally observe the offset drift with time,
the amplifier was programmed to an initial offset voltage of
around
50
V from an initial offset voltage of 1 mV and mea-
sured continuously over a period of 110 hours. Fig. 12(b) shows
the measurement of the offset voltage with time. As can be ob-
served, the offset voltage exhibits an initial short term drift of
about
10
V on account of the interface trap sites settling to a
new equilibrium. Beyond the initial short-term drift, the offset
voltage drift is negligible, as expected from earlier measure-
ments on floating-gate charge retention.
Table III summarizes the performance of the amplifier and
the chip micrograph is shown in Fig. 13. The total area of the
amplifier excluding the buffer is 115
m
45
m and the addi-
tional area occupied by the input capacitors and the switches on
account of using floating-gate transistors is 45
m
45
m. As
can be observed, using floating-gate transistors as a part of the
amplifier and also as a programming element leads to a compact
```

---

## p.10

![p.10](pages/p10.png)

![p.10 내장 이미지 1](images/p10_1.png)

![p.10 내장 이미지 2](images/p10_2.png)

![p.10 내장 이미지 3](images/p10_3.png)

![p.10 내장 이미지 4](images/p10_4.png)

![p.10 내장 이미지 5](images/p10_5.png)

![p.10 내장 이미지 6](images/p10_6.png)

![p.10 내장 이미지 7](images/p10_7.png)

![p.10 내장 이미지 8](images/p10_8.png)

![p.10 내장 이미지 9](images/p10_9.png)

![p.10 내장 이미지 10](images/p10_10.png)

![p.10 내장 이미지 11](images/p10_11.png)

![p.10 내장 이미지 12](images/p10_12.png)

![p.10 내장 이미지 13](images/p10_13.png)

![p.10 내장 이미지 14](images/p10_14.png)

![p.10 내장 이미지 15](images/p10_15.png)

![p.10 내장 이미지 16](images/p10_16.png)

![p.10 내장 이미지 17](images/p10_17.png)

![p.10 내장 이미지 18](images/p10_18.png)

```text
SRINIVASAN et al.: A PRECISION CMOS AMPLIFIER USING FLOATING-GATE TRANSISTORS FOR OFFSET CANCELLATION
289
TABLE III
OPERATIONAL AMPLIFIER SUMMARY OF PERFORMANCE
Fig. 13. Amplifier die micrograph. The chip micrograph of the prototype op-
erational amplifier excluding the output buffer is shown to occupy an area of
115
m
45
m. The additional area on account of using floating-gate transis-
tors is 45
m
45
m.
architecture. Also, the proposed cancellation scheme is indepen-
dent of other amplifier parameters.
Automatic programming of the floating-gate transistor makes
the approach attractive from a commercial standpoint. Unlike
wafer trimming, which is susceptible to offset drifts because of
packaging stress, the proposed scheme involves offset cancel-
lation at the package level. Extra pins (
,
,
) and
digital pins for the drain selection circuitry are needed for pro-
gramming multiple floating-gate transistors. The programming
infrastructure allows the gate, drain, and tunnel voltages to be
shared among different floating-gate transistors. This keeps the
number of extra pins required constant even when using mul-
tiple floating-gate transistors, a scenario that is typical while
using multiple amplifiers on the same chip. The pin count can
be reduced if the gate voltage is supplied by the biasing struc-
ture during programming as well and by using a serial digital
interface for the digital pins.
The reduction of the offset voltage involves three main
steps: 1) measurement of the offset voltage; 2) programming
of the floating-gate transistor; and 3) switching between the
measurement and the programming mode. Typical convergence
to minimum offset voltage takes about 10 programming pulses
of a 100
s each. A more detailed discussion can be found in
Section II. The programming time of minimum offset voltage is
determined by the measurement speed, as this is the slowest of
the steps by far. Typical programming times for the minimum
offset voltage is on the order of 10–20 s.
VII. COMPARISON TO PREVIOUS WORK
The use of floating-gate transistors to correct for mismatch
in analog circuitry has been investigated by other authors as
well [4], [5]. The approach in [4] results in an unidirectional
offset cancellation. This requires an intentional offset creation of
the correct polarity during the design phase of the amplifier for
proper operation. This intentional offset creation has been cited
as the reason for the degradation of the offset voltage tempera-
ture sensitivity [4]. The work in [5] introduces a trimming cir-
cuitry based on floating-gate transistors to produce a difference
current which is then used as a building block to compensate for
mismatch induced errors. The proposed approach in this paper
is conceptually similar to that in [5] in that it uses a differential
current to trim offsets. However, the difference current is created
using just two floating-gate transistors which then form an inte-
gral part of the amplifier of interest. This results in an advantage
in terms of both area and design overhead. Also, the proposed
approach uses hot-electron injection to program floating-gate
transistors while both [4] and [5] use Fowler–Nordheim tun-
neling as the primary programming mechanism. The advantages
of an injection based programming scheme over a tunneling
based programming has been highlighted earlier in Section II.
Correcting analog circuit mismatch using resistor trimming is
an alternate technique. Resistor trimming is usually performed
using laser annealing, laser trims, poly fuses and zener zapping.
Both laser annealing and laser trims are expensive and do not
provide the flexibility of in-package trims. Trimming using poly
fuses and zener zapping is discrete in nature and therefore ac-
curacy is limited to the smallest resistor step used. Also, using a
number of zener diodes and poly fuses involves an area penalty.
All of the above resistor trimming techniques are one-time pro-
grammable. The approach described in this paper is cost ef-
fective, field programmable and is a package level correction
scheme.
The proposed approach involves lesser design overhead when
compared to the technique of using current-mode digital-to-
analog converters controlled using an EEPROM and serial inter-
face [2], [22] to reduce amplifier offsets. Also, the proposed ap-
proach can provide a continuous range of offset voltages rather
than discrete values offered by the DAC-based scheme. This
makes the approach well suited for other applications as well,
such as, programming a chain of comparators to different trip
points for use in, say, Flash analog-to-digital converters.
Auto-zeroing is primarily useful for sampled data sys-
tems and is limited by issues such as charge injection, clock
feedthrough, and wideband noise folding into the baseband on
account of undersampling. For a continuous-time operation,
chopper stabilization or continuous-time auto-zeroing such
as a ping-pong amplifier [24] are the typical alternatives. The
chopper amplifier is, however, limited in use to low-band-
width applications [1]. The ping-pong approach involves the
```

---

## p.11

![p.11](pages/p11.png)

![p.11 내장 이미지 1](images/p11_1.png)

![p.11 내장 이미지 2](images/p11_2.png)

![p.11 내장 이미지 3](images/p11_3.png)

![p.11 내장 이미지 4](images/p11_4.png)

![p.11 내장 이미지 5](images/p11_5.png)

![p.11 내장 이미지 6](images/p11_6.png)

![p.11 내장 이미지 7](images/p11_7.png)

![p.11 내장 이미지 8](images/p11_8.png)

![p.11 내장 이미지 9](images/p11_9.png)

![p.11 내장 이미지 10](images/p11_10.png)

```text
290
IEEE JOURNAL OF SOLID-STATE CIRCUITS, VOL. 42, NO. 2, FEBRUARY 2007
TABLE IV
COMPARISON OF OFFSET CANCELLATION SCHEMES
use of multiple amplifiers and multi-phase clocks that add
additional overhead in terms of area and power. The proposed
floating-gate approach involves none of the above tradeoffs
and the offset cancellation by itself dissipates no additional
power. The approach places minimal overhead on the amplifier
design with nonvolatile storage of offset reduction information.
The primary limitation, however, is the lack of flicker noise
reduction. Finally, Table IV summarizes qualitatively the de-
sign tradeoffs of the proposed approach to the various offset
cancellation schemes on the different design parameters of
interest.
VIII. CONCLUSION
An amplifier topology has been presented that uses
floating-gate programmable elements as an integral part of
the amplifier. The approach places minimal overhead on the
amplifier design with nonvolatile storage of offset reduction
information. A prototype amplifier has been fabricated in a
0.5
m standard digital CMOS process and trimmed to an
offset voltage of 25
V. The offset voltage exhibits a tem-
perature sensitivity of 130
V over a temperature range of
170 C. Floating-gate transistors surrounded completely by
SiO , a high-quality insulator, exhibit excellent charge reten-
tion capabilities. A long-term offset voltage drift of less than
0.5
V when stored at a temperature of 55 C for 10 years
has been calculated based on a thermionic emission model
for floating-gate charge loss. Direct tunneling through the
gate oxide (gate leakage) is a limitation for charge retention
in floating-gate transistors for oxide thicknesses less than 5
nm which are typical for finer line processes
0.25
m .
However, the proposed approach is still scalable with process
technologies. Floating-gate transistors have not been used
in the signal path, therefore in smaller dimension processes,
floating-gate transistors can be implemented using the available
thick oxide transistors with no impact on the speed of operation
of the amplifier. Using thicker oxides preserve the charge
retention capability of floating-gate devices thereby providing
low long-term drifts in the amplifier offset voltage. Finally,
programmability coupled with a negligible long-term drift and
scalability makes this approach attractive for offset reduction
in operational amplifiers.
ACKNOWLEDGMENT
The authors would like to thank K. Sundaresan, Dr. F. Ayazi,
Dr. A. Doolittle, and Dr. P. Patel of Georgia Institute of Tech-
nology, Atlanta, GA, for help with the temperature measure-
ments. The authors would also like to thank Dr. Y. Tsividis for
his encouragement and many valuable discussions.
REFERENCES
[1] C. C. Enz and G. C. Temes, “Circuit techniques for reducing the effects
of op-amp imperfections: Autozeroing, correlated double sampling,
and chopper stabilization,” Proc. IEEE, vol. 84, no. 11, pp. 1584–1614,
Nov. 1996.
[2] W. J. Kim, S. Sompur, and Y. B. Kim, “A novel digial controlled tech-
nique for operational amplifier compensation,” in Proc. MidWest Symp.
Circuits and Systems, Aug. 2001, pp. 211–214.
[3] G. Erdi, “Never-mentioned op amp issues,” in Proc. Bipolar Circuits
and Technology Meeting, Minneapolis, MN, Sep. 1990, pp. 219–222.
[4] L. R. Carley, “Trimming analog circuits using floating-gate analog
MOS memory,” IEEE J. Solid-State Circuits, vol. 24, no. 6, pp.
1569–1575, Dec. 1989.
[5] E. Sackinger and W. Guggenbuhl, “An analog trimming circuit based
on a floating-gate device,” IEEE J. Solid-State Circuits, vol. 23, no. 6,
pp. 1437–1440, Dec. 1988.
[6] F. Adil, G. Serrano, and P. Hasler, “Offset removal using floating gate
circuits for mixed-signal systems,” in Proc. Southwest Symp. Mixed-
Signal Design, Feb. 2003, pp. 190–195.
[7] D. Kahng and S. M. Sze, “A floating-gate and its application to memory
devices,” Bell Syst. Tech. J., vol. 46, no. 4, pp. 1288–1295, 1967.
[8] S. Lai, “Flash memories: Where we were and where we are going,” in
IEDM Tech. Dig., San Francisco, CA, 1998, pp. 971–973.
[9] M. Lezlinger and E. Snow, “Fowler-Nordheim tunneling into thermally
grown SiO ,” J. Appl. Phys., vol. 40, no. 1, pp. 278–283, Jan. 1969.
[10] S. Kinoshita, T. Morie, M. Nagata, and A. Iwata, “A PWM analog
memory programming circuit for floating-gate MOSFETs with 75- s
programming time and 11-bit updating resolution,” IEEE J. Solid-State
Circuits, vol. 36, no. 5, pp. 1286–1290, May 2003.
[11] W. Gao and W. M. Snelgrove, “Floating gate charge-sharing: A novel
circuit for analog trimming,” in Proc. IEEE ISCAS’94, May 1994, pp.
315–318.
[12] C. Duffy and P. Hasler, “Modeling hot-electron injection in PFETs,” J.
Comput. Electron., vol. 2, no. 2-4, pp. 317–322, Dec. 2003.
[13] G. Serrano, P. Smith, H. Lo, R. Chawla, T. Hall, C. Twigg, and P.
Hasler, “Automatic rapid programming of large arrays of floating-gate
elements,” in Proc. IEEE ISCAS 2004, May 2004, pp. 373–376.
[14] C. Mead, Analog VLSI and Neural Systems.
Reading, MA: Addison-
Wesley, 1989.
[15] C. C. Enz, F. Krummenacher, and E. A. Vittoz, “An analytical MOS
transistor model valid in all regions of operation and dedicated to low-
voltage and low-current applications,” Analog Integr. Circuits Signal
Process., vol. 8, no. 1, pp. 83–114, Jul. 1995.
[16] Y. Tsividis, Operation and Modeling of the MOS Transistor.
New
York: McGraw-Hill, 1999.
[17] B. K. Ahuja, H. Vu, C. L. Aber, and W. Owen, “A 0.5
A precision
CMOS floating-gate analog reference,” in IEEE ISSCC Dig. Tech. Pa-
pers, Feb. 2005, pp. 286–287.
[18] C. Bleiker and H. Melchior, “A four-state EEPROM using floating-
gate memory cells,” IEEE J. Solid-State Circuits, vol. 22, no. 3, pp.
460–463, Jun. 1987.
[19] H. Nozama and S. Kokyama, “A thermionic electron emission model
for charge retention in SAMOS structures,” Jpn. J. Appl. Phys., vol. 21,
pp. L111–L112, Feb. 1992.
```
