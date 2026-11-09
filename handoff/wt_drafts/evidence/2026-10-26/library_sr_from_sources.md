# library 9회로 원문의 슬루율(SR) 선언 조사 (2026-10-26)

역할: 원문 조사만 했다. 엔진·spec·topology·계획은 고치지 않았다. git은 읽기만 했다.

- 사용자 원문: "SR를 선언하자. library 원본문헌에서 SR을 선언한 부분을 검토해"
- 대상: library 9회로. heldout은 대상이 아니다.
- 원문 보관소: `chip-design-skills/skills/analog-gmid-design/assets/library/sources/` (아래 `S/`)
  - `pages/`·`images/`는 이미 있었다. `tools/pdf_to_md.py ensure`는 돌리지 않았다(새로 만든 파일 없음).
- spec 사본: master와 `wt/integ-it12`(`34585913`)의 `*.sizing_spec.json` 9개는 바이트가 같다(`cmp`).
- 작업 폴더: `wt/_scratch_srsurvey/`
  - `scripts/grid.py`·`scripts/slope.py`: Xie & Chen Fig. 17(b)·18(b) 비트맵 곡선 수치화
  - `scripts/ngcc_vec.py`·`scripts/ngcc_sr.py`: NGCC Fig. 5 벡터 곡선 추출
  - 원자료: `xie_up.txt`, `xie_dn.txt`, `ngcc_vec.txt`, `topo_dump.txt`
- 사용자 결정 O-129(2026-10-26, 조사 중 전달): nmcnr SR은 확정이다. 상승 ≥ 0.36 V/µs, 하강 ≥ 0.31 V/µs이고 사용자 지정 값이다. 아래 표에 '확정됨(사용자 지정)'으로 적고, 조건 차이는 사실로만 적는다.

---

## 0. 결론

1. **원문이 SR 숫자를 적은 library 회로는 nmcnr 하나다.**
   - Leung 1999 Table 1(p.602)의 측정값이다: SR⁺/SR⁻ = 0.36/0.31 V/µs.
   - 이 값은 O-129로 이미 확정됐다.
2. 원문에 SR 숫자는 없지만 계단 응답 **그림**이 있는 회로가 둘이다. 그림을 읽은 값은 원문이 선언한 값이 아니다.
   - ngcc_3stage_ff: Fig. 5. 상승만 있고, 20-80 % 판독값은 5.5~6.3 V/µs다.
   - current_reuse_telescopic_ota: Fig. 17·18. 차동 출력 기준 20-80 % 판독값은 약 43 V/µs이고 상승·하강이 같다.
3. 나머지 6회로의 원문에는 SR도 정착 시간도 없다: two_stage_ota, folded_cascode, two_stage_ota_sf, pushpull_follower_buffer, sf_pushpull_output_opamp, common_gate_amplifier.
   - Maloberti 2004는 layout 강의라 전기 사양이 하나도 없다.
   - Allen L20(CG)에는 속도 사양이 없다.
   - Allen L26의 SR 10 V/µs(Example 26-2)는 library에 없는 다른 회로의 값이다. class-A BJT 출력 buffered op amp이고 C_L = 100 pF다.
4. 지금 로더는 방향별 SR을 받을 수 없다.
   - O-128 Q5 자리는 `constraints[]`의 `.tran` metric(`slew_rise_v_per_s`·`slew_fall_v_per_s`)이다.
   - as-built registry에는 두 이름이 없다. 그래서 `constraints[]`에 넣으면 `metric_unknown`으로 거부된다.
   - 받는 자리는 `driving_spec.slew_rate_v_per_s` 단일 값뿐이다.
   - 상세는 §4.

---

## 1. 회로별 원문 조사

### 1.1 nmcnr_amplifier -- **확정됨(사용자 지정, O-129)**

- 원문: K. N. Leung, P. K. T. Mok, W.-H. Ki, "Right-Half-Plane Zero Removal Technique for Low-Voltage Low-Power Nested Miller Compensation CMOS Amplifier", ICECS 1999, pp.599-602
  - 웹: IEEE Xplore(유료). 링크는 찾지 못함(보관소 README).
  - 로컬: `S/nmcnr_amplifier__leung_1999/source.pdf`, 저널 p.602 = PDF p.4. 렌더 `pages/p04.png`
- 값: Table 1 'Measured results of the NMC and NMCNR amplifier with loading condition 100pF//25kΩ'
  - NMCNR 열: SR⁺/SR⁻ = **0.36/0.31 V/µs**, T_s⁺/T_s⁻ = 3.03/3.04 µs
  - NMC 열(비교 대상, library 회로가 아님): 0.23/0.23 V/µs, 4.25/4.36 µs
- 값의 종류: **칩 측정값**. 목표 사양이 아니다.
  - p.601 §5: "The transient responses were measured by LeCroy 9354A oscilloscope and are shown in Fig. 6."
- 조건(원문 인용):
  - Table 1 Note: "Slew rate and settling time were measured at unity-feedback configuration with 0.5V step input"
  - 부하: "a load of 100pF in parallel with 25kΩ"
  - 전원·공정: "supply voltage of +/-1V", "double-metal double-poly 0.8µm CMOS process from AMS"
  - 전력: 400 µW
  - Fig. 6(p.602): 오실로스코프 2 µs/div, 0.50 V/div. 계단의 위치(DC 기준 전압)는 그림으로 판독할 수 없다(O-119 정정 2와 같은 판단).
- SR 정의: 원문에 없다. 10-90 %, 20-80 %, 최대 기울기 가운데 무엇을 썼는지 적혀 있지 않다.
- 엔진 조건과의 차이(사실로만 기록):

| 축 | 원문 | 이 엔진 |
|---|---|---|
| 공정·전원 | AMS 0.8 µm, ±1 V | sky130, vdd 1.8 / vss 0 / agnd 0.9 V |
| 부하 | 100 pF ∥ 25 kΩ | spec `element_values` CL 100 pF + RL 25 kΩ(measurement_load). **같다** |
| 계단 | 0.5 V, 위치 미상 | O-119: follower 사용 범위 전 폭. 상승 lo→hi, 하강 hi→lo |
| 판정 양 | 정의 미기재 | O-121 B-2: 20-80 % 기울기 |
| 구성 | unity-feedback | O-119: β = 1 follower. 같다 |

- 앞선 oracle 실측(`2026-10-23/audit_slew_classab_nmcnrspec.md` §1.1, 층 0 시작 봉인점, sky130):
  - 상승: +0.10 V부터 follower 잠금을 잃는다. 출력이 레일로 가므로 슬루 측정이 아니다.
  - 하강: −1.70 V/µs(U-102 끝 −0.223 V 계단)
  - 이 점은 spec을 만족하는 설계점이 아니다. 크기 비교용으로만 본다.

### 1.2 ngcc_3stage_ff -- 원문에 SR 숫자 없음, 계단 응답 그림 있음

- 원문: J.-S. Lee et al., "A Design Guide of 3-stage CMOS Operational Amplifier with Nested Gm-C Frequency Compensation", JSTS 7(1):20-27, 2007
  - 웹: https://doi.org/10.5573/JSTS.2007.7.1.020
  - 로컬: `S/ngcc_3stage_ff__lee_2007/source.pdf`, 저널 p.24~25 = PDF p.5~6
- SR: **없다.** 'slew'라는 낱말이 원문에 0회 나온다.
- 속도 관련 값(시뮬레이션값):
  - p.24(PDF p.5): "The unity gain bandwidth, the phase margin, and the settling time of the designed NGCC 3-stage amplifier were 10MHz, 59˚, and 120nsec, respectively."
  - Table 5(C_L = 10 pF, p.25): 1 % settling time 165/120/102/100 ns(α = 0.1/0.3/0.5/1)
  - Table 6(C_L = 100 pF, p.25): 165/117/147/131 ns
  - 결론(p.25): "...111dB DC gain, 10MHz gain-bandwidth, 59˚ phase margin, and 120nsec settling time."
- Fig. 5 'Simulated step response (CL=10pF, CL=100pF and α=0.3)', p.25 = PDF p.6:
  - 입력 계단: 0.139 → 0.539 V(0.40 V). 상승만 있다.
  - 출력이 입력과 같은 값으로 정착한다. 그래서 β = 1 follower로 **추정**한다. 본문에 구성은 적혀 있지 않다.
  - 벡터 곡선 판독(`ngcc_sr.py`, 축 눈금 글자 위치로 보정, 20-80 % 기울기):
    - 진회색 곡선: 6.31 V/µs (t20 526 ns, t80 564 ns, 넘침 0.559 V)
    - 연회색 곡선: 5.47 V/µs (t20 526 ns, t80 570 ns)
    - 어느 곡선이 C_L = 10 pF인지는 범례 화살표로 확정하지 못했다(미확인). 두 설계는 C_L에 맞춰 전류를 10배 키운 별도 설계다(Table 6 전력 2490 µW 대 297 µW). 그래서 두 SR이 비슷하다.
- 조건: 0.18 µm CMOS, VDD 1.2 V, C_L 10 pF, α = 0.3, 시뮬레이션
- 엔진 조건과의 차이:

| 축 | 원문 | 이 엔진 |
|---|---|---|
| 공정·전원 | 0.18 µm, 1.2 V | sky130, 1.8 V(U-39에서 사용자가 1.8 V로 맞춤) |
| 부하 | 10 pF | spec CL 10 pF. **같다** |
| 계단 | 0.4 V(0.14→0.54), 상승만 | follower 사용 범위 전 폭, 상승과 하강 |
| 판정 양 | 원문은 SR을 정의하지 않음. 위 값은 이번 판독 | 20-80 % |

- 하강 방향은 원문에 근거가 없다.
  - 앞선 oracle 실측에서 ngcc 하강은 class-AB(M13·M14 σ)로 움직여 SR이 계단 크기에 비례했다. −0.04 V 계단에서 −2.74 V/µs, −0.444 V 계단에서 −81.5 V/µs였다(audit §1.1, O-119 정정 2 주의).
- 앞선 oracle 실측(층 0 시작점): 상승 0.31 V/µs(20-80), 최대 기울기 0.62 V/µs. 하강 −81.5 V/µs

### 1.3 current_reuse_telescopic_ota -- 원문에 SR 숫자 없음, 정착 spec과 계단 응답 그림 있음

- 원문: S. Xie, H. Chen, "A 126µW Current-Reuse Telescopic OTA with Class-AB Output Stage", UT Austin, 2019
  - 웹: 찾지 못함
  - 로컬: `S/current_reuse_telescopic_ota__xie_chen_2019/source.pdf`
- SR: **숫자 없음.**
  - p.2 §II.B: "Traditionally, for a common source output stage, the slew will be limited ... by using the designed Class-AB output stage, instantaneous current will can be provided and therefore, less current is need for slew requirement."
  - 'slew requirement'의 숫자는 적혀 있지 않다.
- 속도 관련 값:
  - Table I(p.1, Spec 열 / 결과 열): Settling time Up ≤ 40 ns / 37.885 ns, Down ≤ 40 ns / 37.885 ns
    - Static settling error ≤ 0.1 % / 0.033 %, Dynamic ≤ 0.1 % / 0.065 %
    - Output swing [−1.2 V, 1.2 V] / [−1.706, 1.706]
    - C1, C2, CL = 500 fF, 500 fF, 1 pF
  - p.3 §III.A(설계 배분, spec이 아님): "Assume ts = tslew + tlln ... we allocate tslew and tlln to 10ns and 30ns respectively"
  - p.4: loop gain UGF 28 MHz, PM 60.557°, β ≈ 0.48
- 그림: Fig. 17 'Settling (going up)'(p.16), Fig. 18 'Settling (going down)'(p.17). 신호는 `tran_Vod`(차동 출력)다.
  - 계단: Vod 0 → +1.1984 V(상승), 0 → −1.1984 V(하강). 계단 시각은 500 ns다.
  - 계단 직후 −0.22 V(상승)·+0.23 V(하강)의 피드스루 튐이 있다.
  - 비트맵 수치화(`images/p16_2.png`·`p17_2.png`, 격자 5 ns 간격으로 보정, 기준선·최종값으로 20-80 % 자기 보정):
    - 상승: t20 6.3 ns, t80 23.2 ns → 0.719 V / 16.9 ns ≈ **42.5 V/µs (차동)**
    - 하강: t20 6.4 ns, t80 23.1 ns → ≈ **42.9 V/µs (차동)**
    - 한쪽 출력으로 환산하면 약 21 V/µs다(대칭 가정, **추정**).
    - 판독 오차는 격자 보정과 선 두께 때문에 ±5~10 %로 본다(**추정**).
- 구성: 용량 되먹임 폐루프다. Cs = Cf = 500 fF, 이득 ≈ −1, β ≈ 0.48. **단위 이득 follower(β = 1)가 아니다.** 완전 차동이고 CMFB가 있다.
- 조건: 0.18 µm, 1.8 V, 27 °C, Cadence 시뮬레이션
- 엔진 조건과의 차이:

| 축 | 원문 | 이 엔진 |
|---|---|---|
| 공정 | 0.18 µm | sky130. 전원 1.8 V는 같다 |
| 부하 | CL 1 pF ×2, Cf·Cs 500 fF | spec CL1·CL2 1 pF, Cf·Cs 500 fF. **같다** |
| 구성 | 용량 되먹임 β ≈ 0.48, 차동 | O-119 follower β = 1. 계획 DV-9: '차동 출력 미선언 = 정의 불능' |
| 계단 | 차동 1.2 V(입력 쪽 크기는 이득 −1로 같다고 **추정**) | follower 사용 범위 전 폭 |
| 판정 양 | 원문은 SR을 정의하지 않음. 정착 시간만 spec | 20-80 % |

- 이미 spec에 있는 것: `compensation_targets.settling` total 40 ns / linear 30 ns(user_spec, 원문 III.A). 소비자 0(G2).
- 앞선 oracle 실측: 없다. B81 층 0이 실패해 실측 경로가 없다.

### 1.4 pushpull_follower_buffer · sf_pushpull_output_opamp · two_stage_ota_sf -- 원문에 SR 없음

- 원문: P. E. Allen, CMOS Analog Circuit Design, Lecture 26 'Buffered Op Amps'(6/25/14)
  - 웹: https://aicdesign.org/wp-content/uploads/2018/08/lecture26-140625.pdf
  - 로컬: `S/pushpull_follower_buffer+sf_pushpull_output_opamp+two_stage_ota_sf__allen_2014/source.pdf`
- 회로가 나오는 쪽: p.26-4(push-pull follower), p.26-5(two-stage + follower), p.26-6(Fig. 7.1-1 SF push-pull output)
  - 세 쪽 모두 SR·정착 값이 **없다.**
  - p.26-6에는 "Rout ≈ 1/(gm21+gm22) ≤ 1000Ω, Av(0)=65dB (IBias=50µA), and GB = 60MHz for CL = 1pF"만 있다.
- 강의 안 SR 언급 3곳. 모두 library 회로의 값이 아니다.
  - p.26-2(일반 요건): "Ability to sink and source sufficient current (CL·SR)". 숫자가 없다.
  - p.26-24 Example 26-2: "Slew rate ≥ 10V/µs", CL = 100 pF, RL = 500 Ω, VDD 2.5 V, 0.25 µm
    - 이 값은 folded cascode + class-A **BJT** 출력단(M12~Q15)의 설계 예제다.
    - library 세 회로의 회로도와 다르다. 그래서 **적용 대상이 아니다.**
  - p.26-25: "SR = 10V/µs and 100pF capacitor give I15 = 1mA." 같은 예제의 C_L·SR 전류 계산이다.
- 앞선 oracle 실측:
  - two_stage_ota_sf: 모든 점에서 follower 동작점이 없다. 그래서 슬루 정의 불능이다(audit §1.1, slew_estimate §0).
  - pushpull·sf_pushpull: 실측 없음. sf_pushpull은 B81 층 0 실패다.

### 1.5 two_stage_ota · folded_cascode -- 원문에 전기 사양 자체가 없음

- 원문: F. Maloberti, "Layout of Analog CMOS Integrated Circuit, Part 2"(강의, 2004)
  - 웹: 저자 게시처는 찾지 못함
  - 로컬: `S/two_stage_ota+folded_cascode__maloberti_2004/source.pdf`. p.28 Example 1, p.34 Example 2
- 'slew'·'settl'·'V/µs'·'pF'가 모두 0회 나온다. 소자 폭과 layout 지침만 있다.
- 앞선 oracle 실측(층 0 시작점, 20-80):
  - two_stage_ota: 상승 +5.86, 하강 −2.17 V/µs(최대 기울기 3.12)
  - folded_cascode: 상승 +0.15, 하강 −0.05 V/µs. 하강은 출력 범위가 잘려 슬루가 아니다.

### 1.6 common_gate_amplifier -- 원문에 SR 없음

- 원문: P. E. Allen, Lecture 20 'Low Input Resistance Amplifiers'(6/24/14)
  - 웹: https://aicdesign.org/wp-content/uploads/2018/08/lecture20-140624.pdf
  - 로컬: `S/common_gate_amplifier__allen_2014/source.pdf`. p.20-2 그림 060609-01
- 'slew'·'settl'이 모두 0회 나온다. 'CL = 1 pF'(paper.md 988행)는 다른 cascode 주파수 예제의 값이다.
- spec에 C_L 원소가 없다(SP-6(c) 대기).
- 이 회로에는 차동 입력이 없다. 그래서 O-119의 'β = 1 follower 사용 범위'가 이 회로에서 정의되는지 확인하지 않았다(미확인).

---

## 2. 회로별 표

| 회로 | 원문 SR 상승/하강 | 값 종류 | 조건 | 출처 | 엔진 조건과의 차이 | 선언 후보 |
|---|---|---|---|---|---|---|
| nmcnr_amplifier | **0.36 / 0.31 V/µs** | 측정 | unity-feedback, 0.5 V 계단, 100 pF ∥ 25 kΩ, ±1 V, AMS 0.8 µm, 정의 미기재 | Leung 1999 Table 1 p.602(PDF p.4) | 공정·전원, 계단(0.5 V 대 전 폭), 판정 정의. 부하·구성은 같다 | **확정됨(사용자 지정, O-129)** |
| ngcc_3stage_ff | 없음. Fig. 5 판독: 상승 5.5~6.3 / 하강 없음 | 시뮬레이션 그림(판독) | β = 1로 추정, 0.4 V 계단, 10 pF, 1.2 V, 0.18 µm. settling 1 % 120 ns | Lee 2007 Fig. 5·Table 5 p.25(PDF p.6) | 공정·전원(1.2 → 1.8), 계단, 하강 근거 없음(class-AB). 부하는 같다 | §3 N-1 |
| current_reuse_telescopic_ota | 없음. Fig. 17·18 판독: 차동 ≈ 42.5 / 42.9 | 시뮬레이션 그림(판독). spec은 정착 ≤ 40 ns | 용량 되먹임 β ≈ 0.48, 차동 1.2 V 계단, CL 1 pF, 1.8 V, 0.18 µm | Xie & Chen Table I p.1, §III.A p.3, Fig. 17 p.16, Fig. 18 p.17 | 구성(β = 1 아님, 차동 → DV-9 정의 불능), 공정. 부하·전원은 같다 | §3 N-2 |
| two_stage_ota | 없음 | -- | -- | Maloberti p.28 | -- | 선언 근거 없음 |
| folded_cascode | 없음 | -- | -- | Maloberti p.34 | -- | 선언 근거 없음 |
| two_stage_ota_sf | 없음 | -- | -- | Allen L26 p.26-5 | follower 동작점 없음(앞선 실측) | 선언 근거 없음 |
| pushpull_follower_buffer | 없음 | -- | p.26-2 일반 요건 'CL·SR'만 | Allen L26 p.26-4 | -- | 선언 근거 없음 |
| sf_pushpull_output_opamp | 없음 | -- | GB 60 MHz @ 1 pF만 | Allen L26 p.26-6 | -- | 선언 근거 없음 |
| common_gate_amplifier | 없음 | -- | -- | Allen L20 p.20-2 | C_L 원소 없음, follower 정의 미확인 | 선언 근거 없음 |

앞선 oracle SR(층 0 시작 봉인점, sky130, follower 전 폭, 20-80 %, `2026-10-23/audit_slew_classab_nmcnrspec.md` §1.1). 60점 원자료(`_scratch_audit_slew/out/pts_spice.jsonl`)는 폴더가 지워져 다시 집계하지 못했다.

| 회로 | 상승 | 하강 | 원문 값과 나란히 |
|---|---|---|---|
| nmcnr_amplifier | 잠금 상실(측정 아님) | −1.70 V/µs | 원문 0.36 / 0.31 |
| ngcc_3stage_ff | 0.31 (최대 0.62) | −81.5 (class-AB, 계단 크기에 비례) | 원문 그림 상승 5.5~6.3 |
| two_stage_ota | 5.86 | −2.17 | 원문 없음 |
| folded_cascode | 0.15 | −0.05 (절단) | 원문 없음 |
| two_stage_ota_sf | 정의 불능 | 정의 불능 | 원문 없음 |

---

## 3. 선언 후보 (모두 사용자 결정 대상, 확정하지 않음)

원칙: '논문 값 그대로 인용 금지 -- 사용자가 직접 지정한 값만 확정'. 아래 값은 결정 자료다.

### N-1. ngcc_3stage_ff

| 안 | 값 | 근거 | 걸리는 점 |
|---|---|---|---|
| (가) 선언 안 함 | -- | 원문이 SR을 선언하지 않았다 | 슬루 판정이 없다 |
| (나) 그림 판독값 그대로 | 상승 ≥ 5.5(또는 6.3) V/µs, 하강 미선언 | Fig. 5 20-80 판독 | ⚠ 원칙 경고: 논문 값 그대로 인용 금지·출처 발명 금지 — 원문이 적은 숫자가 아니라 이번에 그림에서 읽은 값이고, 두 곡선 중 C_L = 10 pF가 어느 것인지도 미확인이다 |
| (다) 공정·전원 차이를 반영해 환산 | 정의 불능 | SR = I/C에서 C_L은 원문과 같다(10 pF). 공정·전원 차이는 전류가 아니라 achievable 범위만 바꾼다. 그래서 환산식이 없다 | -- |
| (라) 사용자 직접 지정 | 사용자 값 | -- | -- |

- 하강: 원문 근거가 없다. 1.2절의 class-AB 계단 의존성 때문에 전 폭 계단 판정은 낙관 쪽이다(O-119 정정 2 주의).

### N-2. current_reuse_telescopic_ota

| 안 | 값 | 근거 | 걸리는 점 |
|---|---|---|---|
| (가) 선언 안 함, 정착 spec만 유지 | -- | 원문 spec은 정착(≤ 40 ns)이다 | 정착은 소비자 0(G2). 계단 크기 선언이 없다 |
| (나) 그림 판독값 | 차동 ≈ 43 V/µs(상승·하강) | Fig. 17·18 20-80 판독 | ⚠ 원칙 경고: 논문 값 그대로 인용 금지 — 원문 숫자가 아니라 판독값이다. 구성이 용량 되먹임(β ≈ 0.48)이라 O-119 follower(β = 1)와 다른 양이다 |
| (다) 설계 배분에서 유도 | 차동 ≥ 1.2 V / 10 ns = 120 V/µs | §III.A t_slew 10 ns + Fig. 17 계단 1.2 V | ⚠ 원칙 경고: 상수 발명 금지 — t_slew 10 ns는 저자의 설계 배분이지 spec이 아니다. 실제 판독(43 V/µs)은 이 값의 1/3이라 원문 회로도 못 맞춘다. 그래서 권하지 않는다 |
| (라) 정착을 `.tran` `settle_s`로 옮김(LDA D7 (가) 꼴) | 40 ns | Table I Spec 열(이미 user_spec) | 계단 크기 선언이 필요하다(원문 Fig. 17은 차동 1.2 V). 이것은 SR 선언이 아니라 정착 선언이다 |

- 판정 구성 문제: 이 회로는 완전 차동이고 용량 되먹임이다. 계획 DV-9 '차동 출력 미선언 = 정의 불능'과 O-119 follower 정의가 이 회로에서 어떻게 정해지는지가 먼저 정해져야 한다. 이것도 사용자 결정 대상이다.

### N-3. 원문 근거가 없는 6회로

- (가) 선언 안 함: 기본안. 원문·사용자 지정 출처가 없다.
- (나) 사용자 직접 지정
- 유도 경로가 될 수 있는 것을 검토한 결과는 다음과 같다. 모두 지금 쓸 수 없다.
  - full-power bandwidth SR ≥ 2π·f·Vp: f와 Vp 선언이 없다.
  - 정착에서 유도 SR ≥ ΔV/(t_s − t_lin): 정착 선언이 없다.
  - GBW 결합 SR/ω_GBW = 2/(gm/ID)₁(2단 Miller): GBW와 θ에서 SR이 **따라 나오는** 관계다. 요구값이 아니다(`2026-10-24/min_current_from_load.md` §1.5). 이것을 spec으로 쓰면 θ 가정이 들어가 상수 발명이 된다.
- C_L 비례 환산 SR' = SR·C_orig/C_new는 출력 노드가 슬루를 묶을 때만 성립한다. 내부 Cc 노드가 묶으면 C_L과 무관하다.
  - 원문 SR 값이 있는 nmcnr·ngcc·current_reuse는 spec C_L이 원문과 같다. 그래서 환산이 필요한 회로는 없다.

---

## 4. spec에 넣을 자리

- 정본 자리(O-128 Q5, LDA D7 (가), 계획 N3.8 626행): `human.constraints[]`의 `.tran` metric
  - 꼴(예):
    ```json
    {"metric": "slew_rise_v_per_s", "op": ">=", "value": 3.6e5,
     "source": {"kind": "user_spec", "record": "user_decisions.md O-129 ...", "decided": "2026-10-26"}}
    {"metric": "slew_fall_v_per_s", "op": ">=", "value": 3.1e5, "source": {...}}
    ```
  - 단위는 V/s다. 0.36 V/µs = 3.6e5 V/s, 0.31 V/µs = 3.1e5 V/s.
  - 계획 N3.8: 방향마다 따로 판정하고 집계하지 않는다. spec이 `slew_rate_v_per_s` 하나만 선언하면 두 방향에 적용한다.
- as-built 로더(`wt/integ-it12`, 읽기만 함)와의 차이:
  1. `gmid_engine/metrics/registry.py` `_ROWS`에 `slew_rise_v_per_s`·`slew_fall_v_per_s` 행이 없다.
     - `constraints[]`는 metric이 레지스트리 원소여야 한다(`authoring/spec_constraints.py` 머리 주석). 그래서 지금 넣으면 `metric_unknown`으로 거부된다.
     - test `tests/authoring/test_spec_constraints.py:150`이 `slew_ss_vps`의 `metric_unknown` 거부를 고정한다.
     - O-122는 '엔진 registry 행 없음'을 정했다. 그래서 metric 이름을 레지스트리 밖(oracle 전용 이름표)에서 받는 경로가 필요하다. 이것이 계획 VB-1(`verified_by`)과 Q5 형식 card의 몫이다.
  2. `.tran` 영역이 없다. `core/units.py:18` `DOMAINS = ("dc", "ss", "ls", "geom")`. 계획 표는 슬루를 `ls`로 둔다.
  3. 받는 자리는 지금 `human.driving_spec.slew_rate_v_per_s` 단일 값뿐이다(`authoring/spec_driving.py:17`). source kind는 `user_spec`만 받는다.
     - 방향별 두 값(0.36/0.31)을 담을 수 없다. 한 값으로 넣으면 두 방향에 같은 값이 적용된다.
     - LDA §4.2는 이 칸을 `constraints[]`로 옮기고 섹션을 지우는 안이다.
  4. `pending_constraints`로 대기 표기를 하는 것도 metric이 레지스트리 원소여야 해서 거부된다(test 157행).
- 결론: 방향별 SR은 Q5 형식 card(레지스트리 밖 `.tran` 이름 수용 + `driving_spec` 이관)가 들어가야 넣을 수 있다. O-129 기록('data 커밋은 spec 형식 card와 함께')과 같다.

---

## 5. 사용자 결정 목록

1. ngcc_3stage_ff SR: (가) 선언 안 함 / (나) Fig. 5 판독 상승값 / (라) 직접 지정 중 무엇으로 할지. 하강은 원문 근거가 없다.
2. current_reuse_telescopic_ota:
   - SR: (가) 선언 안 함(정착만) / (나) 판독값 / (라) 직접 지정 중 무엇으로 할지
   - 판정 구성: 완전 차동·용량 되먹임 회로를 O-119 follower로 잴지, 원문 구성(β ≈ 0.48)으로 잴지
3. current_reuse 정착 40 ns를 `.tran` `settle_s`로 옮길지와 그 계단 크기(LDA D7과 묶임)
4. 원문 근거가 없는 6회로: 선언하지 않을지(기본안), 직접 지정할지

---

## 6. 미확인

1. NGCC Fig. 5에서 진회색·연회색 곡선이 각각 어느 C_L인지. 범례 화살표 벡터(DRW 166·169)의 끝점을 곡선에 대응시키지 않았다.
2. NGCC Fig. 5의 측정 구성(β = 1)은 출력 정착값 = 입력값에서 추정했다. 본문에는 적혀 있지 않다.
3. Xie Fig. 17·18 판독의 입력 쪽 계단 크기. 이득 −1(Cs = Cf)로 추정했다.
4. nmcnr 원문의 SR 측정 정의(평균 기울기인지 최대 기울기인지)와 계단 위치
5. 60점 oracle 원자료가 지워져(`_scratch_audit_slew` 없음) 회로별 SR 분포를 다시 집계하지 못했다. 층 0 시작점 한 점의 값만 인용했다.
6. common_gate·pushpull_follower_buffer(차동 입력 없음 또는 개루프 buffer)에서 O-119 'β = 1 follower 사용 범위'가 정의되는지
7. Allen L26 p.26-7~26-23에 이 세 회로를 다시 다룬 쪽이 있는지는 'slew'·'V/µs'·'settl' grep으로만 확인했다(0회). 쪽 이미지는 보지 않았다.

---

## 7. 근거 링크

- Leung 1999: IEEE Xplore 링크는 찾지 못함. 로컬 `S/nmcnr_amplifier__leung_1999/source.pdf` p.4(저널 p.602) Table 1·Fig. 6. 본문 §4·§5는 p.3(저널 p.601)
- Lee 2007: https://doi.org/10.5573/JSTS.2007.7.1.020. 로컬 `S/ngcc_3stage_ff__lee_2007/source.pdf` p.5(저널 p.24) 본문, p.6(저널 p.25) Fig. 5·Table 5·6·결론
- Xie & Chen 2019: 웹은 찾지 못함. 로컬 `S/current_reuse_telescopic_ota__xie_chen_2019/source.pdf` p.1 Table I, p.2 §II.B, p.3 §III.A, p.4 §III.B·§IV, p.16 Fig. 17, p.17 Fig. 18
- Allen L26: https://aicdesign.org/wp-content/uploads/2018/08/lecture26-140625.pdf. 로컬 `S/pushpull_follower_buffer+sf_pushpull_output_opamp+two_stage_ota_sf__allen_2014/source.pdf` p.2, p.4, p.5, p.6, p.24~26
- Allen L20: https://aicdesign.org/wp-content/uploads/2018/08/lecture20-140624.pdf. 로컬 `S/common_gate_amplifier__allen_2014/source.pdf` p.2
- Maloberti 2004: 저자 게시처는 찾지 못함. 로컬 `S/two_stage_ota+folded_cascode__maloberti_2004/source.pdf` p.28, p.34


---

## §정밀 판독 (2026-10-26 추가, 사용자 O-130: ngcc·current_reuse 모두 (나) '원문 그림 판독값')

역할: 원문 판독과 정밀화만 했다. spec·엔진·계획은 고치지 않았다.

- 스크립트·원자료는 `wt/_scratch_srsurvey/`에 있다.
  - `scripts/ngcc_leg.py` → `ngcc_leg.txt`
  - `scripts/ngcc_sr2.py` → `ngcc_sr2.out`
  - `scripts/xie_sr2.py` → `xie_sr2.out`
- 판독 양: O-121 B-2와 같은 꼴이다. 출력 자신의 계단(정지 기준값 → 최종 정착값) 20 %와 80 % 교차 시각 사이의 평균 기울기다.
  - 교차 시각은 표본 사이를 선형 보간해 구했다.
- 가드 위반 기록: 스크래치 스크립트 `ngcc_sr2.py`에 bash heredoc append(`cat >>`)를 한 번 썼다.
  - 그 결과 파일 앞부분이 덮였다(기록된 사고와 같은 현상).
  - Write 도구로 전체를 다시 썼고, 수치는 다시 쓴 스크립트의 출력이다.
  - 증거 파일과 저장소 파일은 건드리지 않았다.

### P-1. ngcc_3stage_ff -- Lee 2007 Fig. 5 (저널 p.25 = PDF p.6)

**곡선 식별** (근거: 벡터 도형, `ngcc_leg.txt`)
- Fig. 5 곡선은 PDF 안의 벡터 폴리라인이다(비트맵 아님). 셋이 있다.
  - DRW 141: 검정, 입력
  - DRW 150: 회색 0.5
  - DRW 159: 연회색 0.754
- 범례 글자와 화살표
  - 글자 'CL=10pF, α=0.3' bbox y 307.5~317.3이다. 화살표 DRW 169의 머리(209.3, 312.2)가 이 글자를 가리킨다.
    - 꼬리 (163.7, 299.9)는 곡선 150 위의 점 (164.0, 299.3)에 있다(거리 0.6 pt).
    - 곡선 159는 같은 x에서 y 309.4라 9.5 pt 떨어져 있다.
  - 글자 'CL=100pF, α=0.3' bbox y 321.4~331.2이다. 화살표 DRW 166의 머리(207.8, 324.0)가 이 글자를 가리킨다.
    - 꼬리 (162.3, 311.8)는 곡선 159 위의 점 (162.2, 312.0)에 있다.
- 결론: **C_L = 10 pF = 곡선 150(회색 0.5)**, C_L = 100 pF = 곡선 159다.
  - 캡션 'Fig. 5. Simulated step response (CL=10pF, CL=100pF and α=0.3)'과 본문 p.24 "Fig. 5 shows the simulated step responses for the two cases of load capacitances (CL=10pF, CL=100pF) when α was set to 0.3"은 두 곡선의 존재만 말한다. 식별은 범례 화살표로 했다.

**계단** (입력 곡선 141)
- 0.1387 V → 0.5387 V. 크기는 **0.400 V**이고 50 % 시각은 500.5 ns다(사실상 이상 계단).
- 원문 글자로 적힌 값이 아니라 판독값이다. 축 눈금은 0.10~0.60 V, 0.05 V 간격이다.
- 상승 계단만 있다. 하강 계단은 그림에도 본문에도 없다.

**측정 구성**
- 원문 문장 근거: 'unity-gain'은 p.22(PDF p.3)의 PM 식 문맥 한 곳뿐이다.
  - "From (1), the phase margin in the unity-gain configuration can be written as"
  - 설계 사양 PM 63.4°가 단위 이득 구성의 PM이라는 뜻이다.
- Fig. 5 자체의 구성은 원문에 적혀 있지 않다.
- 그림 근거: 출력 최종값 0.5387 V가 입력 최종값 0.5387 V와 같다(판독 분해능 안에서 차이 0.0 mV).
  - 개루프 이득 111 dB 증폭기의 폐루프 이득이 1이라는 뜻이다. 그래서 β = 1 follower로 **판단**한다.
- 판정: β = 1은 **원문 문장으로 직접 확인되지 않음**. PM 정의 문맥과 그림 정착값에서 추론했다.

**20-80 % 기울기** (`ngcc_sr2.out`)

| 곡선 | 기준 → 최종 | 넘침 | t20 / t50 / t80 (ns) | SR 20-80 | 20-50 / 50-80 | 10-90 |
|---|---|---|---|---|---|---|
| **C_L 10 pF (150)** | 0.1387 → 0.5387 V | 5.2 % | 525.07 / 544.25 / 563.07 | **6.32 V/µs** | 6.26 / 6.38 | 6.10 |
| C_L 100 pF (159, 참고) | 0.1387 → 0.5399 V | 4.2 % | 525.96 / 547.13 / 569.22 | 5.56 V/µs | 5.69 / 5.45 | 5.40 |

- 20-50 구간과 50-80 구간 기울기가 2 % 안에서 같다. 그래서 20-80 구간이 직선 경사(슬루 제한)라고 본다.

**판독 오차**
- 시간 표본 간격: 원 파형 표본이 1.04 ns 간격이다. 창 양 끝에서 ±1 표본이면 6.15~6.50 V/µs(−2.7/+2.8 %)다.
  - 보간을 했으므로 실제 오차는 이보다 작다고 본다(**추정**).
- 축 보정: 눈금 글자 중심 간격의 균일도로 확인했다.
  - x: 43.5/43.35/43.5/43.35 pt per 50 ns
  - y: 13.7~13.8 pt per 0.05 V
  - 그래서 축척 오차는 0.5 % 아래다. 기울기 비에는 축척만 들어가고 원점 오프셋은 상쇄된다.
- 합계: ±3 % 안이다.

**단일 대표값: 상승 6.3 V/µs (±0.2, C_L 10 pF 곡선, 0.4 V 상승 계단, 20-80 %)**
- 근거
  - library spec C_L(10 pF)과 같은 부하의 곡선이다.
  - 판정 정의(20-80 %)와 같은 꼴이다.
  - 구간이 직선이라 정의 선택(10-90 6.10, 20-80 6.32)에 따른 차이가 4 % 안이다.
- 무엇을 재는가: 0.18 µm·1.2 V·α = 0.3 설계를 β = 1 follower(추론)로 놓고, 0.14 → 0.54 V(0.4 V) 상승 계단을 넣은 시뮬레이션의 출력 20-80 % 평균 기울기다.
- 하강: 원문 근거가 없다. 대표값을 낼 수 없다.

### P-2. current_reuse_telescopic_ota -- Xie & Chen Fig. 17·18 (p.16·p.17)

**재판독** (`xie_sr2.out`)
- 대상: 내장 비트맵 `images/p16_2.png`(Fig. 17(b)), `images/p17_2.png`(Fig. 18(b))
- 시간축은 격자선 픽셀로 보정했다. 500 ns 격자선 = 계단 열이다.
  - 상승 그림: 50.85 px / 5 ns
  - 하강 그림: 47.1 px / 5 ns
- 전압은 출력 자신의 정지값(0 V)과 최종값(±1.1984 V, 그림 표지 M15·M8)으로 자기 보정했다.
- 신호는 `tran_Vod`(차동 출력 v(Vop) − v(Vom))다.

| 방향 | 계단(Vod) | t10 / t20 / t50 / t80 / t90 (ns, 계단 뒤) | SR 20-80 | 20-50 / 50-80 | 10-90 |
|---|---|---|---|---|---|
| 상승 (Fig. 17) | 0 → +1.1984 V | 4.28 / 6.09 / 13.67 / 22.92 / 26.90 | **42.7 V/µs** | 47.5 / 38.9 | 42.4 |
| 하강 (Fig. 18) | 0 → −1.1984 V | 4.24 / 6.04 / 13.64 / 22.81 / 26.84 | **42.9 V/µs** | 47.3 / 39.2 | 42.4 |

- 20-50 구간과 50-80 구간 기울기가 18 % 다르다. 그래서 20-80 구간은 순수 슬루가 아니라 슬루와 선형 정착이 섞인 구간이다.
  - 원문 설계 배분도 t_slew 10 ns + t_lln 30 ns다(p.3 §III.A).
  - 그래도 판정 양(O-121 B-2)은 이 섞인 구간의 평균 기울기 그대로다.
- 계단 직후 피드스루 튐(−0.22 V / +0.23 V)은 20 % 교차(약 6 ns) 전에 끝난다. 그래서 20-80 값에 들어가지 않는다.

**판독 오차**
- 교차 시각 ±2 px(선 두께 중심)이면 42.2~43.4 V/µs(±1.2 %)다.
- 격자 간격 보정 ±0.5 px / 50 px는 ±1 %다.
- 전압 자기 보정 ±2 px / 352 px는 0.6 %다.
- 합계: **±3 %**. Cadence 화면 표시 보간은 평가할 수 없어 범위 밖이다.

**입력 계단 크기** (원문 확인 결과)
- 원문에는 입력 계단 크기를 적은 문장이 **없다.** 테스트벤치 그림도 없다(Fig. 1~5는 OTA·바이어스·CMFB뿐).
- 간접 근거
  1. Fig. 16 'OTA closed-loop frequency response'(p.15): dB20(Vod)가 대역 안에서 0 dB다. 표지 M16 "5.24807kHz −2.95369mdB"로 폐루프 |이득| = 0.9997이다.
  2. Table I(p.1): C1, C2 = 500 fF, 500 fF이고, p.4 식 (4)에서 Cf = Cs = 500 fF, β = Cf/(Cf + Cs + Cgg1) ≈ 0.48이다.
  3. 그래서 Cs/Cf = 1, 폐루프 이득 = 1이다.
- 결론: 입력 차동 계단 ≈ 출력 계단 = **차동 1.2 V로 추론**한다. 원문 문장은 없다.
  - 극성(반전 여부)과 입력 공통 모드 위치는 원문에서 알 수 없다.

**원문 측정 구성** (확인)
- 용량 되먹임 폐루프다. 원문 문장: p.4 식 (3)·(4), "assuming Cgg1 is negligible and Cf = Cs = 500fF, β is about 0.5. In reality, Cgg1 is not negligible. therefore, we assume that β is around 0.48."
- 부하: CL = 1 pF(Table I '1pF', 출력마다로 추정)
- 완전 차동 + CMFB(출력 CM 0.9 V, Abstract)
- 0.18 µm, 1.8 V, 27 °C(p.4 §IV)
- 엔진 spec과의 대응
  - `feedback.elements = [Cf1, Cf2]`
  - `element_values`: Cf1·Cf2·Cs1·Cs2 = 500 fF, CL1·CL2 = 1 pF(measurement_load)
  - 값은 원문과 같다.

**대표값: 차동 출력 43 V/µs (상승 42.7, 하강 42.9, ±3 %), 차동 1.2 V 계단, 용량 되먹임 Cs = Cf = 500 fF(β ≈ 0.48, 폐루프 이득 1), CL 1 pF/출력, 20-80 %**
- 한쪽 출력 값(약 21 V/µs)은 대칭 가정이다. 원문 그림은 차동만 있어 확인할 수 없다.

**엔진 판정 구성 후보별로 판독값을 그대로 쓸 수 있는가**

판정 근거 문서는 다음과 같다.
- oracle design §21.6 절차 1·1b(integ-it12 `docs/02-design/features/oracle-portability.design.md` 1939행~)
- 사용자 결정 O-50 G2, O-52, O-69 (1), O-78 (1)

| 후보 | 지금 oracle에서 정의되는가 | 판독값과 같은 양인가 | 판정 |
|---|---|---|---|
| (a) O-119 follower 구성(β = 1) | **정의 불능.** §21.6 1: "차동 출력 + `unity_follower` = `feedback_config_undeclared`(`why = differential_undeclared`, 정의 불능 유지)" (O-50 G2·O-52 '차동 출력 구성 미선언 = 정의 불능') | **아니다.** β 1 대 0.48, 되먹임·입력 망 Cf·Cs의 출력 부하(Cf 직렬 Cs ≈ 0.25 pF/쪽, 앞 증거 §1.5 손계산), 계단 위치(follower 사용 범위 전 폭 대 0 → ±1.2 V 차동)가 모두 다르다 | **그대로 쓸 수 없다.** 쓰려면 차동 출력 회로의 follower 정의를 새로 정해야 한다(계획 개정 대상). 정해도 다른 구성의 값이라 원문 판독값과 같은 양이 아니다 |
| (b) 원문 구성(선언 되먹임 Cf + 입력 Cs) | **지금은 정의 불능.** §21.6 1b: "용량만 선언된 차동 출력의 t = 0 시작 동작점 경로는 OP-10에서 만들지 않는다 -- gain-budget card AP-1(N6.22) 몫이고, 그때까지 그 슬루는 `feedback_config_undeclared`(`why = start_op_deferred`)". §21.6 2: 계단 자리 '입력 망 원소 갈래는 AP-1 몫' | **구성·부하는 같다**(spec 값 = 원문 값). 계단 정의는 다르다: oracle 계단 = 동작점 → 확정 ICMR 끝(§21.6 2, 계획 v6.21 문언) 또는 O-119 follower 사용 범위 전 폭. 원문 = 차동 0 → ±1.2 V | **AP-1 뒤에야 판정 가능.** 그때 계단 정의를 원문(차동 ±1.2 V = Table I 출력 스윙 사양의 반 폭)과 맞출지가 따로 정해져야 그대로 쓸 수 있다 |

- 덧붙이는 사실
  - §21.6 4는 아직 '최대 |dV/dt|'로 적혀 있다(design 13곳 정정 v1.14.2 대기). 판정 양 20-80 %(O-121 B-2)는 계획 기준이다.
  - 차동 출력에서 측정 노드(`slew.node`)가 차동(Vod)인지 단일 출력인지는 design에서 확인하지 못했다(미확인). 원문 판독값은 차동 Vod 기준이다.

### P-3. 사용자에게 물을 남은 선택

1. ngcc
   - 값: 상승 SR ≥ 6.3 V/µs(대표값)로 할지, 안전 쪽 판독 하한 6.1 V/µs로 할지
   - 하강: 원문 근거가 없다. (가) 미선언 / (나) 상승 값을 두 방향에 적용 / (다) 사용자 지정 중 하나를 정해야 한다.
     - (나)는 ⚠ 원칙 경고: 출처 발명 금지 — 하강은 원문에 근거가 없다.
   - 계단 차이: 원문 0.4 V 대 O-119 전 폭. 사실로 기록한다. ngcc 하강은 class-AB라 계단 크기에 비례한다(O-119 정정 2).
2. current_reuse
   - (i) 판정 구성: (a) follower는 같은 양이 아니고 정의도 불능이라 권하지 않는다. (b) 원문 구성이면 AP-1(용량만 선언된 차동 출력의 시작 동작점·입력 망 계단 자리) 뒤에야 판정할 수 있다. 그때까지는 'oracle 정의 불능(판정 대기)'으로 둘지 정해야 한다.
   - (ii) (b)를 고르면 계단 정의: 원문 차동 0 → ±1.2 V(출력 스윙 사양 반 폭)로 할지, oracle 규칙(동작점 → ICMR 끝 / O-119 전 폭)으로 할지. 원문과 같은 양이 되려면 앞의 것이 필요하다. 이는 계획 개정 대상이다.
   - (iii) 측정 노드: 차동 Vod 기준(원문과 같음)으로 할지, 한쪽 출력(약 21 V/µs, 대칭 가정)으로 할지
   - (iv) 값: 두 방향 모두 43 V/µs(±3 %)로 할지, 방향별 42.7 / 42.9로 할지
3. 공통: 그림 판독값이라 source.record에 '원문 그림 판독(이 증거 §정밀 판독), 원문 문장 값 아님'을 적을지

### P-4. 미확인 (정밀 판독 뒤 남은 것)

1. ngcc Fig. 5 구성(β = 1)의 원문 문장 근거. 추론만 했다.
2. Xie 입력 계단 크기·극성·공통 모드 위치의 원문 문장 근거. 0 dB 폐루프 이득에서 추론했다.
3. Xie 한쪽 출력 파형. 원문에 없다.
4. oracle 차동 출력 슬루의 측정 노드 정의(차동인지 단일인지)


---

## §정착 정의 (2026-10-26 추가, 사용자 O-132: current_reuse SR 폐기 → 정착 ≤ 40 ns spec, 측정 구성은 원문 그대로)

역할: 원문 확인만 했다. spec·엔진·계획은 고치지 않았다.

- 원문: Xie & Chen 2019. 웹은 찾지 못함. 로컬 `S/current_reuse_telescopic_ota__xie_chen_2019/source.pdf`
- 앞 절 §정밀 판독 P-2(current_reuse SR 대표값 43 V/µs)는 사용자 결정 O-132로 **폐기됐다.** 기록으로만 남긴다.

### T-1. 원문이 적은 것 (원문 문장 그대로)

| 자리 | 원문 |
|---|---|
| Table I p.1, Spec / Our Results 열 | Static settling error ≤0.1% / 0.033%; Dynamic settling error ≤0.1% / 0.065%; Settling time Up ≤40ns / 37.885ns, Down ≤40ns / 37.885ns; Loop gain at low-frequency (β·Adm) 69.36dB; Loop gain unity gain frequency 27.998MHz; Loop gain Phase margin ≥60° / 60.557° |
| Abstract p.1 | "Simulation results show that the design achieves outstanding performance of 0.033% static settling error, 0.065% dynamic settling error, 38ns settling time" |
| §III.A p.3, 식 (1) | "Consider the dynamic settling error and settling time requirement, we have ϵd ≤0.1%, ts ≤40ns, (1) where ϵd is the dynamic settling error and ts is the settling time." |
| §III.A p.3 | "Assume ts = tslew + tlln, where tslew is the slewing time and tlln is the linear settling time. The Class AB structure in the second stage can provide instantaneous current. Therefore, we allocate tslew and tlln to 10ns and 30ns respectively, to relax the bandwidth requirement and reduce the current consumption." |
| §III.A p.3, 식 (2) | "To achieve ϵd ≤0.1%, the equation tlln·ωc = 6.9 (2) should be satisfied [8], where ωc is the loop gain unity gain bandwith, which is also equal to the close-loop bandwidth." |
| p.4 | "Given tlln = 30ns, the value of ωc is then calculated to be 2.3×10⁸; thus, the loop gain unity gain frequency fc is 36.6MHz." |
| §IV.E p.4 | "Transient simulation gives the data of static settling error, dynamic settling error, and settling time. Figure 17 and Figure 18 show the results of going up and going down settling." |
| 참고문헌 [8] | N. Sun, "Step response," 2019. 저장소에 원문이 없고 웹도 찾지 못했다. UT Austin 강의 자료로 **추정**한다 |
| Fig. 17(a) p.16 | 표지 M15 "537.885ns 1.1984V", M14 "949.026ns 1.1996V"(상승, `tran_Vod`) |
| Fig. 18(a) p.17 | 표지 M8 "537.885ns −1.1984V", M7 "924.239ns −1.1996V"(하강) |

원문에 **없는** 것:
- 세 오차(static, dynamic, settling time)의 수식 정의
- 측정 시작점 문장
- 최종값 기준 문장
- ε를 해상도(비트 수)에서 유도한 문장

### T-2. 정착 정의 재구성 (원문 숫자의 산술 대조로 확정한 것과 추론한 것을 나눔)

원문 숫자들 사이의 산술 일치로 정의를 역추적했다.

| 항목 | 결과 | 근거(산술) | 확신 |
|---|---|---|---|
| **ε (정착 오차 띠)** | **0.1 %**, 실제 최종값 기준의 상대 띠 | 1.1996 V(M14, 실제 최종값) × (1 − 0.001) = 1.19840 V = M15 값 1.1984 V(4자리 일치). 하강도 같다: −1.1996 × 0.999 = −1.1984(M8) | 높음(4자리 일치, 상승·하강 둘 다) |
| **측정 시작점** | 계단 순간(t = 500 ns) | M15 537.885 ns − 500 ns = 37.885 ns = Table I settling time. Fig. 17(b)·18(b)에서 계단 열이 500.0 ns 격자선에 있다(§정밀 판독 P-2 픽셀 판독) | 높음 |
| **최종값 기준(정착 시간)** | **실제 최종값**(M14 1.1996 V, 이상값 1.2 V 아님) | 이상값 1.2 V 기준 0.1 % 띠는 1.1988 V다. 표지 값 1.1984와 다르다 | 높음 |
| **static settling error** | 이상 최종값(1.2 V) 대 실제 최종값(1.1996 V)의 상대 차 = 유한 루프 이득 오차 | (1.2 − 1.1996)/1.2 = 0.033 % = Table I 0.033 %. 그리고 1/(β·Adm) = 10^(−69.36/20) = 3.4×10⁻⁴ = 0.034 %. 두 값이 일치한다 | 높음(두 독립 경로 일치). 이상 최종값 1.2 V는 입력 차동 1.2 V × 폐루프 이득 1(Cs = Cf)에서 나온다 -- §정밀 판독 P-2의 추론을 이 일치가 뒷받침한다 |
| **dynamic settling error** | 정착 시간 사양 시점(계단 뒤 ts = 40 ns, 곧 540 ns)의 출력과 실제 최종값의 상대 차 | 식 (1)·(2)의 '선형 정착 끝 잔류 오차 e^(−tlln·ωc) = e^(−6.9) = 0.1 %' 정의, 그리고 0.065 % < 0.1 %(정착 시간 37.885 < 40 ns와 정합) | 중간(**추론** -- 540 ns 시점 값이 원문 그림 표지에 없어 산술 대조 불가. 비트맵 해상도 0.4 px/1.2 mV로는 0.065 %를 읽을 수 없다) |
| **상승·하강** | 같은 정의, 같은 값(37.885 ns 둘 다) | Fig. 17·18 표지 | 높음 |
| **'정착' 판정 방식** | 띠에 처음 들어간 시각인지, 마지막으로 들어간 뒤 머문 시각인지는 원문에 없다 | Fig. 17(a)·18(a)에서 띠 진입 뒤 넘침이 보이지 않는다(표지 사이 평탄). 두 정의가 같은 값을 줄 가능성이 크다(**추정**) | 미확인 |

- 식 (2)의 6.9 = ln(1000) = ln(1/0.001)이다. 단일 극점(1차) 선형 정착에서 오차가 0.1 %로 줄 때까지 걸리는 시정수의 수다.
  - 원문은 이 값을 [8]에서 인용만 했다. 1차 근사인지 PM 보정을 했는지는 적지 않았다.
  - 원문 PM은 60.557°이고, 실제 정착은 1차 모형과 다르다(**추정**).
- 판독 재확인: ε = 0.1 %는 1.2 mV다. 비트맵 축척 약 352 px/V에서는 0.4 px라 픽셀로 다시 판독할 수 없다. 그래서 원문 표지 값(M14·M15·M7·M8)을 쓴다.

### T-3. 원문 값의 성격

| 값 | 성격 | 근거 |
|---|---|---|
| settling time ≤ 40 ns (상승·하강) | **spec**(Table I Spec 열, 식 (1) "requirement") | p.1 Table I, p.3 식 (1) |
| dynamic settling error ≤ 0.1 % (= ε) | **spec** | 같은 자리 |
| static settling error ≤ 0.1 % | **spec**(루프 이득 요구와 같은 양 -- 1/(βA) ≤ 0.1 %이면 βA ≥ 60 dB) | Table I |
| tslew = 10 ns, tlln = 30 ns | **설계 배분**(spec 아님) -- "we allocate … to relax the bandwidth requirement" | p.3 §III.A |
| ωc = 2.3×10⁸ rad/s (fc 36.6 MHz) | 설계 배분 tlln에서 유도한 **설계 목표** | p.4 |
| 37.885 ns(상승·하강), 0.033 %, 0.065 % | **달성값, 시뮬레이션**(Cadence ADE, 0.18 µm, 27 °C, 1.8 V -- p.4 §IV "The simulations are conducted with 0.18µm CMOS manufacturing process in Cadence ADE environment") | Table I, Abstract, Fig. 17·18 |
| 실제 루프 fc 27.998 MHz | 달성값, 시뮬레이션. 설계 목표 36.6 MHz보다 낮은데도 정착 37.885 ns는 사양 안이다 | Table I, p.4 §IV.C |

- 지금 spec의 `compensation_targets.settling`은 total_s 4e-8, linear_s 3e-8, origin paper다. total 40 ns는 원문 spec이다. **linear 30 ns는 원문 설계 배분**이다(record 문구 "t_slew 10 ns / t_lln 30 ns"와 같다).

### T-4. ε와 해상도 요구의 관계

- 원문은 ε = 0.1 %를 **주어진 사양으로만** 적었다. 비트 수·ADC 해상도·LSB에서 유도한 문장은 없다.
  - 'LSB'·'bit'·'resolution'·'ADC'·'accura' grep 결과 0회
- 0.1 % ≈ 2^−10(0.098 %), 곧 10 bit 수준이다. 이 대응은 원문에 없는 해석이다. ⚠ 원칙 경고: 출처 발명 금지 — 해상도 근거로 기록하면 안 된다.

### T-5. 판정 방법론 점검 (원문 구성으로 이 정의를 재는 것)

- 원문 구성
  - 용량 되먹임 폐루프: Cs = Cf = 500 fF, β ≈ 0.48, 폐루프 이득 1, CL 1 pF/출력
  - 입력: 차동 계단(출력 Vod 0 → ±1.2 V, 입력 1.2 V로 추론. T-2 static 오차 일치가 뒷받침)
  - 측정: Vod 시간열에서 계단 순간부터 실제 최종값 ±0.1 % 띠 진입까지
- 문헌 대조
  - Leung 1999 p.601(저장소 원문, `S/nmcnr_amplifier__leung_1999/source.pdf` p.3)은 Kamath, Meyer, Gray 1974(JSSC 9, pp.347-352)를 인용해 "the settling time (Ts) is composed of the slewing and quasi-linear period"라고 적는다. Xie의 ts = tslew + tlln 분해와 같은 틀이다.
  - 정착 시간 = '계단 인가 시점부터 출력이 최종값의 지정 오차 띠 안에 들어가 머무를 때까지'가 일반 정의다. SC 증폭기에서 static 오차 1/(βA)와 dynamic 오차 e^(−t·βω_t)를 나눠 다루는 틀은 Johns & Martin 'Analog Integrated Circuit Design'(1997)의 SC 이득단·정착 논의와 같다.
    - **교과서 쪽 번호는 미확인**이다. 저장소와 G: 드라이브에 원문이 없다.
    - ADI MT-046 웹 확인은 시간 초과로 실패했다. 이 두 출처는 원문을 열어 확인하지 못한 인용이다.
- 판단
  1. **용량 되먹임(실제 사용 구성)에서 재는 것은 SC OTA 정착 측정의 표준 꼴과 맞는다.** 정착은 β·부하·되먹임 망에 의존하는 폐루프 양이라, 사용 구성 그대로 재야 같은 양이 된다. β = 1 follower에서 잰 정착은 β가 2배라 다른 양이다.
  2. 최종값 기준이 둘이다.
     - 정착 시간 = 실제 최종값 기준 띠(T-2)
     - static 오차 = 이상값 기준 → 이 둘은 다른 양이고 원문도 따로 사양화했다.
     - 정착 띠를 이상값 기준으로 잡으면 static 오차(0.033 %)가 띠의 1/3을 먹는다. 그러면 같은 회로의 정착 시간이 길어진다(1.1988 V까지).
  3. 계단 크기·위치가 정착을 좌우한다(슬루 몫). 원문은 차동 0 → ±1.2 V다. Table I 출력 스윙 사양 [−1.2, 1.2] V의 한쪽 끝까지에 해당한다.
     - 이 엔진의 slew 계단 규칙(O-119 follower 사용 범위 전 폭)은 follower 구성의 규칙이라 원문 구성에는 해당하지 않는다.
     - 원문 구성 정착의 계단은 따로 선언해야 한다. LDA §4.2 '`settle_s`(+ 계단 크기 선언 -- 없으면 하한 정의 불능)'가 이 경우다.
  4. 지금 oracle 상태
     - 용량만 선언된 차동 출력의 과도 시작 동작점(t = 0)은 AP-1 몫이다(oracle design §21.6 1b, O-78 (1)). 계단 자리(입력 망 원소)도 AP-1 몫이다.
     - `settle_s`는 oracle에서 '정의 미정'(§21.6 6, C25)이다.
     - 그래서 원문 구성 정착 판정은 **AP-1과 settle_s 정의(OP 쪽) 뒤에야 가능**하다.

### T-6. 사용자에게 물을 남은 선택

1. **ε**
   - (가) 원문 dynamic settling error 사양 0.1 %, 실제 최종값 기준(원문 산술로 확정한 정의) -- 기본안, 원문과 같은 양
   - (나) 이상 최종값 기준 0.1 % -- 원문과 다른 양. static 오차까지 섞인다
   - (다) 사용자 지정
2. **최종값 정의**: 실제 최종값을 어떻게 정할지
   - 원문은 계단 뒤 약 450 ns 시점 값(M14 949 ns)을 썼다.
   - oracle에서는 '긴 시간 뒤 값' 또는 '같은 구성 .op 해'가 후보다(계획·design에서 정할 몫, 상수 발명 주의).
3. **static settling error ≤ 0.1 %를 별도 spec으로 둘지**
   - 원문 Table I spec이다.
   - 루프 이득 βA ≥ 60 dB와 같은 양이다. β ≈ 0.48이면 Adm ≥ 약 66.4 dB(**계산**)다.
   - 지금 spec `gain_ss_db ≥ 54`(view MOD5 대기)와의 관계를 정해야 한다.
4. **linear_s(30 ns) 처리**
   - (가) 삭제: 원문 설계 배분이라 spec이 아니고, 소비자 0(G2)이다. total만 `settle_s`로 옮긴다 -- 기본안
   - (나) 엔진 설계 보조값으로 유지: 소비자를 새로 배선해야 한다. ⚠ 원칙 경고: 상수 발명·논문 값 그대로 인용 금지 — 저자의 배분을 spec 자리에 둔다
   - (다) 사용자 지정
5. **계단 선언**: 원문 차동 0 → ±1.2 V(출력 스윙 사양 끝)를 정착 계단으로 선언할지, 다른 규칙으로 할지
6. **판정 시점**: AP-1(용량 되먹임 차동 출력의 시작 동작점·입력 망 계단)과 oracle `settle_s` 정의가 들어갈 때까지 '판정 대기'로 둘지

### T-7. 미확인

1. 참고문헌 [8] N. Sun 'Step response'(2019)의 정의 원문. 식 (2) 6.9의 출처다.
2. dynamic settling error 0.065 %의 측정 시점(40 ns로 추론)
3. '띠에 처음 진입'과 '진입 뒤 머묾' 가운데 어느 정의인지
4. Johns & Martin, ADI MT-046의 쪽 번호와 문장. 원문을 열지 못했다.
5. Table I CL '1pF'가 출력마다인지 전체인지. spec은 출력마다 1 pF다.
