# 출력 범위 spec 후보 -- sf_pushpull_output_opamp (독립 회로 해석, 2026-10-26)

- 역할: 독립 회로 해석자. 읽기 전용. output_range_candidates.md는 근거로 쓰지 않았다.
- 근거로 쓴 것: topology.json의 `netlist`·`passive_elements`·`ideal_sources`·`ports`(연결만), sizing_spec.json(레일·포트·constraints), 원문 PDF, sky130 LUT v2 r2, user_decisions.md O-128 Q5·O-154, bulk 기본 규칙 `gmid_engine/graph/bulk_default.py`(DEC-61).
- 쓰지 않은 것: device_roles·symmetry·sizing_roles·compensation 태그, `_comment`, heldout, 논문 수치.
- 계산 스크립트·원 출력: `C:/Users/HSLEE/Documents/Todoc/fpga/wt/_scratch_swing_sf_pushpull/` (`swing.py`→`swing_results.txt`, `swing2.py`→`swing_results2.txt`, `swing3.py`→`swing_results3.txt`).
- 원문: P.E. Allen, Lecture 26 Buffered Op Amps, https://aicdesign.org/wp-content/uploads/2018/08/lecture26-140625.pdf , 로컬 `assets/library/sources/pushpull_follower_buffer+sf_pushpull_output_opamp+two_stage_ota_sf__allen_2014/source.pdf` (`paper.md`, `pages/p0N.png`).

## 0. 결론 먼저

**기본 bulk 규칙(nmos→vss, pmos→vdd)과 VDD 1.8 V에서는 의미 있는 출력 범위가 거의 없다.** 출력 push-pull follower의 두 VGS(M22, M21)가 body effect로 커져서, 실용 gm/ID(≤ 20 S/A) 전 영역에서 V_lo > V_hi가 된다. 즉 '모든 소자 포화 + 두 follower 도통'을 만족하는 출력 전압이 없다. 정지점 0.9 V(agnd)조차 L ≥ 0.5 µm에서는 gm/ID ≈ 25 S/A(깊은 약반전)가 되어야 겨우 성립한다(§3.4).

권고: **출력 범위는 미선언으로 유지한다(O-154 Q4 현행과 같음, fail-closed, 양은 '정의 불능').** 다만 이 물리적 불성립은 출력 범위와는 별개로 spec·topology 문제이므로 따로 보고한다(§7 확인 포인트 1·2).

## 1. topology 해석 (연결만 사용)

### 1.1 출력 노드
- `ports.vout`(direction output, 단일 출력). 입력은 `vin_p`·`vin_n` 차동 입력, 출력은 단일 출력이다. 차동 출력이 아니므로 Vod나 출력 CM 선언 대상이 아니다.
- vout에 닿는 소자: M22(nmos, d=vdd, g=N17, s=vout), M21(pmos, d=vss, g=N20, s=vout), CL(vout–agnd).

### 1.2 단 구성 판정

| 단 | 소자(연결) | 판정 | 근거 | 확신도 |
|---|---|---|---|---|
| 1단 | M1/M2 nmos, s=TAIL, g=vin_p/vin_n; M3 tail(g=NB), M4 diode(NB, IBias) | nmos 차동쌍 + 꼬리 전류 거울 | 같은 TAIL source, 게이트가 두 입력 | 높음 |
| 1단 부하 | M6(s=vdd,d=N56,g=N5)–M5(s=N56,d=N5,g=N1), R1a(N5–N1); 대칭 M8/M7/R1b | 저항 self-bias cascode 다이오드 부하 | M5 drain N5 = M6 gate, M5 gate N1 = M1 drain, 두 노드가 R로만 이어짐. 게이트는 DC 전류가 없으므로 I_M1 = I_R1a = I_M5 | 높음 |
| 2단 | M9/M10(g=N5/N1, d=Y) 위쪽, M15/M16(g=N12/N13, d=Y) 아래쪽; M11/M12 → M13/M14 + R1c 전달 | 거울 출력 cascode 2단, 고임피던스 노드 Y | M9/M10이 M6/M5와 게이트 공유, M15/M16이 M13/M14와 게이트 공유 | 높음 |
| Y 보상 | Cc(Y–agnd) | 접지 분로 C (Miller 아님) | 단자 연결 | 높음 |
| 레벨 시프트 | M17(pmos 전류원, s=vdd, g=N5, d=N17) + M18(pmos, s=N17, g=Y, d=vss); M19(nmos, d=vdd, g=Y, s=N20) + M20(nmos 전류원, s=vss, g=N13, d=N20) | Y에서 위아래로 VGS만큼 옮기는 source follower 두 개 | 게이트 Y, source가 전류원 노드 | 높음 |
| 출력단 | M22 nmos follower(d=vdd, s=vout, g=N17), M21 pmos follower(d=vss, s=vout, g=N20) | class-AB push-pull source follower | 두 소자 source가 모두 vout, drain이 각 레일 | 높음 |

- 되먹임: 수동 되먹임 소자 없음(spec `feedback.elements` = [], 결정 2026-10-07 9번: β=1 루프로 PM 정의). CM 제어 없음(단일 출력).
- bulk: netlist에 bulk 키가 없다 → DEC-61 기본 규칙(nmos→최저 전위 vss, pmos→최고 전위 vdd). 그래서 follower M18·M19·M21·M22에는 body effect가 있다(VSB ≠ 0).
- 원문 대조: Fig. 7.1-1(p.6, PDF p.6)의 회색 'Buffer' 상자가 M17~M22이고, 그림에 VSG18·VGS19·VSG21·VGS22, I17·I20 표기가 있다. 위 연결 해석과 같다.

### 1.3 출력에서 레일까지의 DC 적층 (범위 끝에서 포화 요구)
출력 DC 부하는 CL뿐이다(DC 전류 0). 그래서 vout KCL은 I22 = I21이다. 범위 끝에서도 두 follower가 함께 도통해야 한다. 한쪽이 꺼지면 다른 쪽도 0이 되어 출력이 떠 버린다.

- 위쪽(끌어올림): vdd –[M17 VSD]– N17 –[M22 VGS]– vout
  - N17 = vout + VGS22(VSB = vout)
  - M17 포화: VDD − N17 ≥ VDsat17
- 아래쪽(끌어내림): vss –[M20 VDS]– N20 –[M21 VSG]– vout
  - N20 = vout − VSG21(VBS_p = VDD − vout)
  - M20 포화: N20 ≥ VDsat20
- 나머지 행(모두 덜 엄격, §3.3에서 실측):
  - M22: VDD − vout ≥ VDsat22. VGS22 > VDsat이라 자동으로 만족한다.
  - M21: vout ≥ VDsat21
  - M18·M19: VDS가 크다.
  - Y 경로 2단 cascode: Y ∈ [VDsat15+VDsat16, VDD−VDsat9−VDsat10]. 이 식은 R1a·R1c를 최적으로 골랐을 때의 값이다. vout = Y + VSG18 − VGS22 = Y − VGS19 + VSG21.

위쪽에는 VDsat 1개와 VGS 1개, 아래쪽에도 VDsat 1개와 VSG 1개가 쌓인다. follower 출력이므로 VGS 항이 들어가고, 이 VGS에는 body effect로 커진 Vth가 들어 있다.

## 2. 이론 스윙 식 (DC 양)

```
V_hi = VDD − VDsat17 − VGS22(VSB = V_hi)
V_lo = VSS + VDsat20 + VSG21(VBS = VDD − V_lo)
성립 조건: V_hi ≥ V_lo  ⇔  VDD − VSS ≥ VDsat17 + VDsat20 + VGS22 + VSG21
```
Y 경로 행은 다음과 같다.
```
V_hi,Y = VDD − VDsat9 − VDsat10 + VSG18 − VGS22
V_lo,Y = VDsat15 + VDsat16 − VGS19 + VSG21
```
VSG18 > 2·VDsat이므로 위쪽은 M17 행이 지배하고, 아래쪽은 M20 행이 지배한다(§3.3 실측).

원문 단서: p.3(PDF p.3) "Maximum upper output voltage is limited", p.4(PDF p.4) push-pull follower "Maximum positive and negative output voltages are limited", "Voltage loss from 2 cascaded followers". 이 회로의 스윙 수치는 원문 p.6에 없다(Rout ≤ 1000 Ω, Av(0) = 65 dB, GB = 60 MHz, CL = 1 pF, IBias = 50 µA만 있음).

## 3. 수치 (sky130 LUT v2 r2, tt, 27 °C)

LUT 출처: `C:/Users/HSLEE/Documents/Todoc/fpga/lut_data/sky130_lut_v2/sky130_nfet_pfet_lut_v2_r2.npz` (lut_v2_location.json sha256 938e95b9…). 축은 [L, VGS, VDS, VS]이고 VS = VSB(source 0 V, body = −VS)이다. VDSAT = ngspice BSIM `@m[vdsat]`. 조회 방법: L은 격자점에서만 읽었다(bin 넘는 보간 없음). VDS·VS는 선형 보간했다. VGS는 GM/ID = 가정값이 되는 점을 peak 위 강반전 쪽 가지에서 선형으로 풀었다.

가정(설계 선택, 상수 발명 아님 -- 표의 축):
- gm/ID: 5(강반전), 10, 15(중간), 20(약반전 쪽)
- 모든 소자 같은 L
- 전류원(M17·M20) VDS = 0.3 V에서 VDsat 평가. 0.15~0.45 V로 바꿔도 V_hi·V_lo 변화는 14 mV 이하(results.txt 민감도 절).
- follower VDS·VSB는 범위 끝 전압에서 자기 일치 반복으로 정했다.

### 3.1 L = 0.5 µm (발췌, gm/ID_cs = 전류원, gm/ID_f = follower)

| gm/ID_cs | gm/ID_f | VDsat17 | VGS22 (Vth22) | **V_hi** | VDsat20 | VSG21 (Vth21) | **V_lo** | 폭 |
|---|---|---|---|---|---|---|---|---|
| 5 | 5 | 0.315 | 1.062 (0.716) | 0.423 | 0.259 | 1.379 (1.019) | 1.638 | −1.215 |
| 10 | 10 | 0.175 | 0.927 (0.766) | 0.699 | 0.159 | 1.230 (1.076) | 1.388 | −0.690 |
| 15 | 15 | 0.099 | 0.864 (0.790) | 0.837 | 0.105 | 1.145 (1.105) | 1.250 | −0.413 |
| 20 | 20 | 0.045 | 0.804 (0.808) | 0.951 | 0.066 | 0.924 (1.157) | 0.990 | −0.039 |
| 20 | 10 | 0.045 | 0.947 | 0.808 | 0.066 | 1.244 | 1.310 | −0.501 |
| 10 | 20 | 0.175 | 0.788 | 0.837 | 0.159 | 0.904 | 1.063 | −0.225 |

L = 0.15·1.0·2.0 µm 전체 4×4 표는 `swing_results.txt`에 있다. 경향은 같다. L = 1.0, 20/20일 때 폭 −0.080, L = 2.0, 20/20일 때 폭 −0.064이다. L = 0.15 µm에서만 gm/ID_f = 20일 때 폭이 양수(+0.23~+0.56)로 나온다. 그러나 이 pfet 점은 VSG21 = 0.35 V, Vth 0.90 V, ID/W = 8e-11 A/µm인 누설 지배 깊은 subthreshold 점이다(results2 '의심점'). L = 0.15 pfet은 gm/ID peak가 VGS = 0에 있다. 이 점은 신뢰하지 않는다.

### 3.2 폭 ≥ 0이 되는 최소 follower gm/ID (기본 bulk, swing_results3.txt)

| L (µm) | gm/ID_cs | 최소 gm/ID_f | [V_lo, V_hi] | Rout ≤ 1 kΩ(gm21+gm22 ≥ 1 mS, 0.5 mS씩 가정) 필요 W21 | 게이트 면적 W·L (M21+M22) |
|---|---|---|---|---|---|
| 0.5 | 15 | 23.5 | [0.965, 0.966] | 21,022 µm | 1.06e-8 m² |
| 0.5 | 20 | 21.5 | [0.961, 0.973] | 10,456 µm | 5.3e-9 m² |
| 1.0 | 20 | 23.0 | [0.995, 1.001] | 23,706 µm | 2.4e-8 m² (spec area 2e-8 초과) |
| 0.15 | 20 | 15.5 | [0.897, 0.907] | 26 µm | 4e-12 m² |

창 폭은 1~12 mV뿐이고, pmos follower 면적이 매우 크다. L = 0.15 줄은 §3.1의 pfet 의심 가지 근처라서 확신도가 낮다.

### 3.3 Y 경로 행과 비교 (L = 0.5, gm/ID 공통)
| g | V_hi,Y | V_hi (M17) | V_lo,Y | V_lo (M20) |
|---|---|---|---|---|
| 10 | 1.698 | 0.699 | 0.721 | 1.388 |
| 15 | 1.768 | 0.837 | 0.632 | 1.250 |
| 20 | 1.650 | 0.951 | 0.430 | 0.990 |

M17·M20 행이 지배한다. 이로써 §2의 식이 확인된다.

### 3.4 정지점 vout = agnd 0.9 V에서 바이어스가 성립하는가 (기본 bulk, 모든 소자 같은 gm/ID)
| L | g | M17 여유 = VDD − VDsat17 − 0.9 − VGS22 | M20 여유 = 0.9 − VSG21 − VDsat20 |
|---|---|---|---|
| 0.5 | 15 | −0.072 | −0.422 |
| 0.5 | 20 | +0.060 | −0.102 |
| 0.5 | 25 | +0.175 | +0.014 |
| 1.0 | 25 | +0.177 | −0.044 |

→ input_dc = agnd 0.9 V로 선언된 동작점 자체가 아래쪽 pmos follower 적층 때문에 깊은 약반전이 아니면 포화를 지키지 못한다.

### 3.5 bulk 시나리오 (topology 변경이 필요하므로 사용자 영역, 참고만)
| L, g | 레일 bulk (기본) | M21 bulk=source | M21·M22 bulk=source |
|---|---|---|---|
| 0.5, 15 | [1.250, 0.837] 폭 −0.413 | 폭 −0.285 | [1.122, 0.990] 폭 −0.132 |
| 0.5, 20 | [0.990, 0.951] 폭 −0.039 | [0.809, 0.951] +0.142 | [0.809, 1.127] +0.318 |
| 1.0, 20 | 폭 −0.080 | [0.867, 0.960] +0.093 | [0.867, 1.149] +0.282 |

bulk를 source에 묶어도 gm/ID 20에서 폭이 0.1~0.3 V 정도다. M22를 source에 묶으려면 sky130에서 deep nwell 분리 p-well이 필요하다(공정 선택).

### 3.6 입력 ICMR (follower 사용 시 출력 = 입력)
β = 1 루프(결정 9번)에서는 vout = vin이므로 출력 범위가 ICMR 안에 들어야 한다.
- 하한 = VDsat3 + VGS1(VSB = V_TAIL)
- 상한 = VDD − VSG5 − VDsat6 − VDsat1 + VGS1. R1a를 M6 VSD = VDsat가 되도록 최적으로 골랐을 때의 값이다.

| L, g | ICMR |
|---|---|
| 0.5, 10 | [0.989, 1.150] |
| 0.5, 15 | [0.833, 1.384] |
| 0.5, 20 | [0.705, 1.746] |

icm_margin_v ≥ 0(입력 DC 0.9 V)은 gm/ID 약 13 이상에서 성립한다. ICMR 상한 식은 근사다(M1 VSB 반복 단순화).

## 4. 순환 위험과 '의미 있는 요구'

- 회로 능력 식(§2)을 그대로 요구로 쓰면 θ마다 같은 식을 다시 평가하는 셈이라, 판정이 늘 통과해 아무것도 걸러내지 못한다(순환).
- 의미 있는 요구는 응용에서 와야 한다. 예: 구동 대상이 요구하는 출력 진폭, follower 사용 시 신호 진폭, slew 계단 폭.
- 원문 p.2(PDF p.2)의 응용 단서는 "drive a low output resistance and/or a large output capacitance, 10 ≤ Ro ≤ 1000 Ω, sink/source CL·SR"이다. 진폭 수치는 없다. p.6에도 스윙 수치가 없다. 이 회로에 선언된 SR 요구도 없다(O-128 Q5 `.tran` 항목 0건).
- 그러므로 응용에 근거한 진폭 값은 원문과 spec 어디에도 없다. 값을 정하면 상수 발명이 된다.
- '특정 gm/ID 설계 의도에서의 범위'(예: gm/ID 15에서의 V_hi/V_lo)를 요구로 쓰는 방법도 검토했다. 이 회로에서는 그 값이 모든 실용 gm/ID에서 빈 집합(V_lo > V_hi)이라, 요구로 쓸 수 없다.

## 5. 기존 spec과의 정합

| 항목 | 관계 | 판정 |
|---|---|---|
| 레일 vdd 1.8 / vss 0 | 성립 조건 VDD ≥ VDsat17+VDsat20+VGS22+VSG21 ≈ 0.11~0.57 + 1.73~2.44 V (gm/ID 20~5, L 0.5) | **충돌**: 실용 gm/ID에서 불성립 |
| input_dc = agnd 0.9 V | β = 1에서 정지 출력 0.9 V가 범위 안이어야 함 | §3.4: L ≥ 0.5에서 gm/ID ≈ 25 필요 |
| icm_margin_v ≥ 0 | ICMR 하한 0.70~0.99 V(gm/ID 20~10) | gm/ID ≳ 13에서 성립. 출력 범위를 선언하면 범위 ⊂ ICMR이 추가로 필요(follower 사용 시) |
| rout_ss_ohm ≤ 1000 | gm21+gm22 ≥ 1 mS. follower gm/ID가 높을수록 W가 폭증 | §3.2: 폭 ≥ 0 점은 pmos W ~1e4 µm |
| area_search_m2 ≤ 2e-8 | §3.2 면적 | L = 1.0에서 초과, L = 0.5에서 절반 소모 |
| CL 1 pF (DC 전류 0) | 범위 끝에서 I21 = I22 (두 follower 도통) | §1.3 근거 |
| swing_out_v | 이 회로 spec에 없음 | O-154 Q3 삭제 대상 아님 |

## 6. 권고와 대안

**권고 (A): 출력 범위 미선언 유지(fail-closed, 범위 끝 능력·보고 양 = '정의 불능').** O-154 Q4 현행과 같다. 이 판단은 앞선 조사를 근거로 쓰지 않고 독립적으로 도달한 결론이다. 이와 함께 §3의 물리적 불성립(정지점조차 깊은 약반전에서만 포화)을 spec·topology 문제로 사용자에게 따로 올린다.

| 안 | 내용 | 물리 정합 | 손계산 일치 | 기존 spec 정합 | 순환 위험 | 원칙 |
|---|---|---|---|---|---|---|
| **A (권고)** | 미선언 유지 | 정합: 빈 범위를 요구로 만들지 않음 | 해당 없음 | O-154 Q4·Q1과 같음 | 없음 | 상수 발명 없음, 대체값 금지(O-128 Q5) 준수 |
| B | 정지점 한 점 [0.9, 0.9] 선언 | 정합: 정지점 포화 요구 | §3.4로 판정 가능 | input_dc와 같음 | 낮음. 단 SPICE 합격 규칙 '전 MOS 포화'와 중복이라 새 정보가 없음 | 폭 0 '범위'는 출력 범위 정의(O-154)의 취지와 맞지 않음 |
| C | 특정 gm/ID 의도 범위 (예: L 0.5·gm/ID 20의 [0.990, 0.951]) | ⚠ 빈 집합 | 일치(§3.1)하지만 V_lo > V_hi | 레일과 충돌 | 능력 식을 요구로 씀(순환) | ⚠ 상수 발명·원칙 위반 |
| D | bulk=source 선언을 전제로 agnd 중심 대칭 범위 (예: L 0.5·gm/ID 20, M21·M22 bulk=source에서 [0.81, 0.99]) | 조건부 정합 | §3.5 | topology 변경(사용자 영역)·deep nwell 필요 | 중간: 폭 값의 근거가 능력 식뿐 | ⚠ 원래 취지와 다름(topology 변경 필요), 진폭 근거 없음 |
| E | 레일 기반 대체값 (예: [VSS+x, VDD−x]) | ⚠ 불성립 | 불일치 | 충돌 | 높음 | ⚠ O-154 Q1·O-128 Q5 대체 금지 위반 |

확신도:
- topology 해석: 높음(연결이 명시적이고 원문 Fig. 7.1-1과 일치)
- 스윙 식: 높음
- 수치: 중상(LUT 선형 보간, 전류원 VDS 가정 민감도 14 mV 이하, 같은 L 가정, VDSAT은 BSIM 정의)
- 'V_lo > V_hi' 결론: 높음. 여유 −0.04~−1.2 V이고, body effect를 뺀 최선 경우에도 gm/ID 15에서 폭이 −0.13이다.
- L = 0.15 pfet 점: 낮음

## 7. 사용자 확인 포인트

1. **bulk 연결**: topology에 bulk 선언이 없어 DEC-61 기본 규칙(레일)이 적용된다. 원문 의도나 실제 구현에서 follower bulk를 source에 묶을지(pmos M18·M21은 자기 n-well, nmos M19·M22는 deep nwell)는 connectivity 결정이라 사용자 영역이다. 묶어도 폭은 gm/ID 20에서 0.1~0.3 V 수준이다(§3.5).
2. **전원 1.8 V와 회로의 정합**: 정지점 0.9 V 자체가 L ≥ 0.5에서 gm/ID ≈ 25가 아니면 아래 follower가 포화를 지키지 못한다. U-39 확정 spec(vdd 1.8)을 유지할지, 이 회로를 1.8 V 단일 전원 sky130에서 '정의 불능 회로'로 표시할지 결정이 필요하다. ⚠ 원래 취지와 다를 수 있음: 원문은 split supply(VDD/VSS 표기, p.6)이고 값이 적혀 있지 않다.
3. **범위를 꼭 선언한다면** 진폭 근거(구동 대상 진폭, SR 계단 폭 등)를 사용자가 지정해야 한다. 원문과 spec에는 그 근거가 없다.
4. β = 1(follower) 판정을 쓰므로, 범위를 선언하는 경우 '범위 ⊂ ICMR' 조건을 R8 행에 넣을지 design에서 확인해야 한다.
