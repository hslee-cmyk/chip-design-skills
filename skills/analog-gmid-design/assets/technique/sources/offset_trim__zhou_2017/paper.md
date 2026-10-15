# Y. Zhou, A. Kay, 'Offset Correction Methods: Laser Trim, e-Trim, and Chopper', TI SBOT037A, Jun 2017 (rev. Jul 2017)

- 원본 PDF: `G:\내 드라이브\work\Todoc\논문모음\(Reference - trim) Offset Correction Methods_Laser Trim, e-Trim , and Chopper.pdf`
- 사본: `source.pdf` (sha256 `dbcfad180d8c7eb2dbdeeffc960de422a52d2538b050149fc07eb77983743fc3`)
- 웹 출처: https://www.ti.com/lit/SBOT037
- 그림·표 위치: PDF p.1 laser trim(패키지 뒤 offset 이동), e-Trim(내부 보정 전류원을 패키지 최종 시험에서 조정); p.2 Fig.2(입력쌍 소스 쪽 trim 저항·Trim Control), Fig.3 chopper, Table 1(방법 비교: chopper만 drift·1/f 제거)
- 엔진 연결: 아직 없음 -- 계획 `docs/01-plan/features/offset-trim.plan.md` 근거표(R-행)에서 인용
- 쪽 수: 3
- 변환: PyMuPDF 텍스트 추출(쪽 단위). 수식·표·그림은 텍스트가 깨질 수 있으니 같은 쪽의 렌더 PNG(`pages/`)로 확인할 것.
- `pages/`·`images/` 는 git 에 없다. 없으면 skill 폴더에서 `python tools/pdf_to_md.py ensure` 로 만든다.

---

## p.1

![p.1](pages/p01.png)

![p.1 내장 이미지 1](images/p01_1.png)

![p.1 내장 이미지 2](images/p01_2.png)

```text
Laser Trimmed
1
SBOT037A–June 2017–Revised July 2017
Submit Documentation Feedback
Copyright © 2017, Texas Instruments Incorporated
Offset Correction Methods: Laser Trim, e-Trim™, and Chopper Ying Zhou, Art Kay
____________________________________________________
Offset Correction Methods: Laser Trim, e-Trim™, and
Chopper
Ying Zhou, Art Kay
Introduction
Amplifier input offset voltage is often the key
parameter for design accuracy, and there are different
circuit techniques used to minimize it. Knowing the
various trimming and offset correction methods may
be productive when selecting an amplifier for a
particular application.
Laser trim: wafer-level trim
Each amplifier is composed of tens to thousands of
transistors, resistors, and capacitors. The device input
offset error is caused by the mismatch (or variations)
of the input transistors in each amplifier. Figure 1
shows a photo of an op amp die. The highlighted
areas show the thin film resistors. During the wafer-
level test process, a laser burns away sections of
resistive material, thus adjusting its value by
increasing the total resistance of the die.
Figure 1. Laser Trimming on Thin-Film Resistors
This trimming can actually be done while the device is
in operation under the laser; that is, we can monitor
the offset voltage and then trim the resistor until the
offset is nulled to zero. Wafer-level trimming may
produce very accurate results. However, after the
wafer is sawn into individual dies and packaged, any
physical stress to a given die can produce some shifts
in the offset voltage.
Laser trim is a practical way to trim ICs fabricated on a
bipolar wafer process. It is used widely not only for op
amps, but also in difference and instrumentation
amplifiers to improve the resistor matching that is
critical in minimizing gain error while optimizing
common-mode rejection ratio (CMRR) performance.
The INA826S is an instrumentation amplifier that uses
laser trim to achieve high DC accuracies and low
quiescent current: 150-µV offset, 2-µV/°C drift, and
250-µA quiescent current. With the additional
shutdown function and small (3-mm × 3-mm) DFN
package, this amplifier is suitable for power-sensitive
applications such as circuit breakers, portable medical
instrumentation, and test equipment.
e-Trim™: package-level trim
Another method used to achieve low offset voltage
and drift is e-Trim, which is TI’s patented trimming
architecture implemented after device packaging.
Correction current sources internal to the devices are
adjusted during the final package-level manufacturing
test. Once the trimming is completed, the gateway to
trim circuitry is closed, so the trim control circuit is
disabled and the adjustments become permanent.
Figure 2 illustrates the e-Trim method.
This polysilicon, fuse-blowing technique does not
require extra pins or test pads and provides substantial
improved performance over wafer-level trim. This
approach also avoids the parameter shifts that
typically occur as a result of package stress, producing
the excellent precision only possible with zero-drift
amplifiers and allowing miniature package sizes.
```

---

## p.2

![p.2](pages/p02.png)

```text
VIN
+VOS-
VOUT
gm
-a
Band
Stop
High-
Frequency
Path
CC
S
Transconductance
Transimpedance
Copyright © 2017, Texas Instruments Incorporated
Copyright © 2017, Texas Instruments Incorporated
VCC
VIN1
VIN2
GND
IS1
Trim
Control
Trim signals
applied to 
output
K
Output 
Stage
VOUT
www.ti.com
2
SBOT037A–June 2017–Revised July 2017
Submit Documentation Feedback
Copyright © 2017, Texas Instruments Incorporated
Offset Correction Methods: Laser Trim, e-Trim™, and Chopper Ying Zhou, Art Kay
Figure 2. Package-Level e-Trim
The OPA2191 is the newest addition to the e-Trim
amplifier family, featuring 25-µV (max) offset voltage,
0.8-µV/°C (max) drift, and low quiescent current of
200 µA per amplifier.
Chopper: dynamic correction
Although it is not a trim method as such, a third
method to correct offset and drift is with a zero-drift
amplifier. The chopper is a common type of zero-drift
amplifier that uses an internal dynamic calibration
method to minimize the offset voltage. Figure 3 shows
the diagram of a typical chopper architecture. The
input and output of the first trans-conductance stage
has a set of switches that swaps the polarity of the
input signal once every calibration cycle. The drift over
time and temperature is averaged to zero. This
characteristic also eliminates the 1/f noise that occurs
in conventional amplifiers at very low frequencies.
These features make chopper amplifiers very useful in
DC (or low-frequency) signal conditioning applications
such as weigh scales, strain gauges, and temperature
measurement. The OPA2187 is an example of a
chopper with 10-µV (max) offset voltage, 0.05-µV/°C
(max) drift, and 0.4-µVPP low-frequency noise (0.1 Hz
to 10 Hz), all with only 145-µA (max) quiescent current
per amplifier.
Figure 3. Typical Diagram of Chopper Amplifier
Chopper amplifiers, however, may insert an additional
noise component caused by charge injection because
of the switch closing and opening; these operations
induce spikes in the input bias current that may be
converted into voltage spikes in high source
impedance applications or during use of high-value
resistors to gain up the signal. For this reason, in
applications with a narrow temperature range such as
medical instrumentation, the near-zero drift may not be
as important as the ultra-low input bias current of the
amplifier coupled with high source impedance. In such
cases, the OPA2191 with 20-pA (max) bias current is
likely a better option than the OPA2187 with much
lower offset drift but 350-pA (max) bias current.
Summary
Table 1 compares the three offset correction methods.
This technical brief may serve as a guide to help you
select an amplifier that best meets your low-offset,
low-drift circuit needs.
Table 1. Laser Trim, e-Trim, and Chopper
Comparison
Devices
Correction
Method
Advantages
Disadvantages
INA826S
OPA145
OPA2325
Laser trim
Simplified
manufacturing flow
over temperature
Parameter shifts
after packaging
OPA2191
OPA2192
OPA2376
e-Trim
No parameter
shifts because of
packaging
Complex
manufacturing flow
over temperature
INA188
OPA189
OPA2187
OPA388
Chopper
Lowest possible
drift; no 1/f noise
Bias current
spikes can cause
problems with high
source
impedances
Table 2. Related Blog Posts and Resources
Video
Op Amp Technology Overview
Precision Hub Blog
How does package level trim compare to
other offset correction methods?
Precision Hub Blog
Trimmed or chopped: How do you like your
op amp?
EDN Analog Design
Post
Pushing the precision envelope –
Understanding the precision challenge in
operational amplifiers
```

---

## p.3

![p.3](pages/p03.png)

```text
IMPORTANT NOTICE FOR TI DESIGN INFORMATION AND RESOURCES
Texas Instruments Incorporated (‘TI”) technical, application or other design advice, services or information, including, but not limited to,
reference designs and materials relating to evaluation modules, (collectively, “TI Resources”) are intended to assist designers who are
developing applications that incorporate TI products; by downloading, accessing or using any particular TI Resource in any way, you
(individually or, if you are acting on behalf of a company, your company) agree to use it solely for this purpose and subject to the terms of
this Notice.
TI’s provision of TI Resources does not expand or otherwise alter TI’s applicable published warranties or warranty disclaimers for TI
products, and no additional obligations or liabilities arise from TI providing such TI Resources. TI reserves the right to make corrections,
enhancements, improvements and other changes to its TI Resources.
You understand and agree that you remain responsible for using your independent analysis, evaluation and judgment in designing your
applications and that you have full and exclusive responsibility to assure the safety of your applications and compliance of your applications
(and of all TI products used in or for your applications) with all applicable regulations, laws and other applicable requirements. You
represent that, with respect to your applications, you have all the necessary expertise to create and implement safeguards that (1)
anticipate dangerous consequences of failures, (2) monitor failures and their consequences, and (3) lessen the likelihood of failures that
might cause harm and take appropriate actions. You agree that prior to using or distributing any applications that include TI products, you
will thoroughly test such applications and the functionality of such TI products as used in such applications. TI has not conducted any
testing other than that specifically described in the published documentation for a particular TI Resource.
You are authorized to use, copy and modify any individual TI Resource only in connection with the development of applications that include
the TI product(s) identified in such TI Resource. NO OTHER LICENSE, EXPRESS OR IMPLIED, BY ESTOPPEL OR OTHERWISE TO
ANY OTHER TI INTELLECTUAL PROPERTY RIGHT, AND NO LICENSE TO ANY TECHNOLOGY OR INTELLECTUAL PROPERTY
RIGHT OF TI OR ANY THIRD PARTY IS GRANTED HEREIN, including but not limited to any patent right, copyright, mask work right, or
other intellectual property right relating to any combination, machine, or process in which TI products or services are used. Information
regarding or referencing third-party products or services does not constitute a license to use such products or services, or a warranty or
endorsement thereof. Use of TI Resources may require a license from a third party under the patents or other intellectual property of the
third party, or a license from TI under the patents or other intellectual property of TI.
TI RESOURCES ARE PROVIDED “AS IS” AND WITH ALL FAULTS. TI DISCLAIMS ALL OTHER WARRANTIES OR
REPRESENTATIONS, EXPRESS OR IMPLIED, REGARDING TI RESOURCES OR USE THEREOF, INCLUDING BUT NOT LIMITED TO
ACCURACY OR COMPLETENESS, TITLE, ANY EPIDEMIC FAILURE WARRANTY AND ANY IMPLIED WARRANTIES OF
MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE, AND NON-INFRINGEMENT OF ANY THIRD PARTY INTELLECTUAL
PROPERTY RIGHTS.
TI SHALL NOT BE LIABLE FOR AND SHALL NOT DEFEND OR INDEMNIFY YOU AGAINST ANY CLAIM, INCLUDING BUT NOT
LIMITED TO ANY INFRINGEMENT CLAIM THAT RELATES TO OR IS BASED ON ANY COMBINATION OF PRODUCTS EVEN IF
DESCRIBED IN TI RESOURCES OR OTHERWISE. IN NO EVENT SHALL TI BE LIABLE FOR ANY ACTUAL, DIRECT, SPECIAL,
COLLATERAL, INDIRECT, PUNITIVE, INCIDENTAL, CONSEQUENTIAL OR EXEMPLARY DAMAGES IN CONNECTION WITH OR
ARISING OUT OF TI RESOURCES OR USE THEREOF, AND REGARDLESS OF WHETHER TI HAS BEEN ADVISED OF THE
POSSIBILITY OF SUCH DAMAGES.
You agree to fully indemnify TI and its representatives against any damages, costs, losses, and/or liabilities arising out of your non-
compliance with the terms and provisions of this Notice.
This Notice applies to TI Resources. Additional terms apply to the use and purchase of certain types of materials, TI products and services.
These include; without limitation, TI’s standard terms for semiconductor products http://www.ti.com/sc/docs/stdterms.htm), evaluation
modules, and samples (http://www.ti.com/sc/docs/sampterms.htm).
Mailing Address: Texas Instruments, Post Office Box 655303, Dallas, Texas 75265
Copyright © 2017, Texas Instruments Incorporated
```
