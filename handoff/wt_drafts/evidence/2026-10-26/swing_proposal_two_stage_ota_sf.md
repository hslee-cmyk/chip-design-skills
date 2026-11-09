# two_stage_ota_sf 출력 범위(출력 절대 범위) spec 후보 -- 독립 이론 유도

- 작성: 2026-10-26, 독립 회로 해석자(읽기 전용). output_range_candidates.md는 근거로 쓰지 않았다.
- 근거: topology connectivity(netlist·passive_elements·ports·supply_nets)만 사용. device_roles·symmetry·sizing_roles·compensation·주석은 쓰지 않았다.
- 원문: P.E. Allen, Lecture 26 Buffered Op Amps (6/25/14), https://aicdesign.org/wp-content/uploads/2018/08/lecture26-140625.pdf
  로컬 `chip-design-skills/skills/analog-gmid-design/assets/library/sources/pushpull_follower_buffer+sf_pushpull_output_opamp+two_stage_ota_sf__allen_2014/source.pdf`
  - PDF p.5 (Page 26-5) 'Two-Stage Op Amp with Follower', 그림 060706-03: 회로도와 이득식만 있고, 스윙·전원·ICMR 수치는 없다.
  - PDF p.3 (Page 26-3) 'The Class A Source Follower as a Buffer', 그림 060118-10: "Level shift from input to output", "Maximum upper output voltage is limited". 정성적인 서술뿐이고 수치는 없다.
- LUT: `lut_data/sky130_lut_v2/sky130_nfet_pfet_lut_v2_r2.npz`(lut_v2_location.json cap_npz, tt, 27 °C, W_ref 5 µm, 축 [L, VGS, VDS, VS], VS = |V_SB|), 열 VDSAT_n/_p(ngspice @m[vdsat]), VTH, ID, GM.
- 계산 스크립트: `wt/_scratch_swing_two_stage_ota_sf/swing.py`, `icmr.py`. 결과 원본은 같은 폴더의 `swing_results.txt/json`, `icmr_results.txt`.
- 결정 맥락: **O-154 Q4가 이미 two_stage_ota_sf를 '미선언'으로 정했다.** 이 문서의 권고를 채택하면 그 결정을 뒤집는 것이므로 사용자 결정이 필요하다.

## 1. topology 해석 (연결만 사용)

| 소자 | 종류 | D / G / S | 연결로 판정한 기능 |
|---|---|---|---|
| M1, M2 | nmos | D3·O1 / vin_n·vin_p / CS | 공통 source CS를 공유하는 차동쌍 |
| M3, M4 | pmos | D3·O1 / D3 / vdd | M3 diode(G=D=D3), M4가 같은 gate를 쓰는 전류 거울 부하 |
| M5 | nmos | CS / bias / gnd | 꼬리 전류원(gate = 바이어스 입력) |
| M6 | pmos | OUT / O1 / vdd | 2단 공통 source(gate = 1단 출력 O1, source = 레일) |
| M7 | nmos | OUT / bias / gnd | 2단 전류원 부하 |
| M8 | nmos | vdd / OUT / vout | **source follower**(drain = vdd, gate = OUT, source = 출력 포트) |
| M9 | nmos | vout / bias / gnd | follower 전류원 |
| Cc | C | O1–OUT | 1·2단 사이 용량(DC 경로 아님) |
| CL | C | vout–gnd | 부하(DC 전류 0) |

- 출력 노드: `ports.vout`(direction output, single_ended_output) = M8 source = M9 drain. 확신도 높음.
- 단일 출력이다. 출력 포트는 하나이고 CM 제어 소자가 없다. 차동 출력이 아니므로 Vod·CM 선언은 해당하지 않는다. 확신도 높음.
- 되먹임: netlist 안에 출력에서 입력으로 가는 DC 경로가 없다. 회로는 개루프이고, 사용 상태의 β=1 루프는 spec `feedback.elements = []` 결정(2026-10-07 '9번 PM 정의')에서 온 외부 조건이다.
- 출력단 판정: **공통 source(M6/M7) + nmos source follower(M8/M9)**. 근거는 M8의 drain이 레일(vdd)이고 gate가 앞단 노드, source가 출력이라는 점이다. 원문 p.5 그림과 같다. 확신도 높음.
- DC 가지:
  - vout 가지: vdd → M8(D→S) → vout → M9(D→S) → gnd. CL은 DC 전류가 0이고 저항 부하 선언이 없다. 따라서 I8 = I9이고, 이 값은 bias가 고정한다.
  - OUT 가지: vdd → M6 → OUT → M7 → gnd. M8 gate로는 DC 전류가 흐르지 않는다.

### 적층 해석

- **위로 끌어올리는 쪽(vout 상한).** vout = OUT − VGS8 이고, OUT의 상한은 M6 포화 경계 VDD − VDsat6 이다.
  → 쌓이는 항은 **VDsat 1개(M6) + VGS 1개(M8, body effect 포함)** 이다.
  - M8 bulk는 gnd이므로(벌크 기본 규칙, nmos = 가장 낮은 레일) V_SB8 = vout 이다. 상한 근처에서 VTH8이 오른다.
  - M8 자신의 포화: VDS8 = VDD − vout = VDsat6 + VGS8 ≫ VDsat8 이므로 범위 전체에서 항상 성립한다.
  - M7: 상한에서 VDS7 = VDD − VDsat6 으로 커서 묶이지 않는다.
- **아래로 끌어내리는 쪽(vout 하한).** M9 포화 경계 vout ≥ VDsat9.
  → 쌓이는 항은 **VDsat 1개(M9)** 이다.
  - 이때 OUT = V_lo + VGS8(V_SB = V_lo) ≈ 0.68~1.3 V 로 VDsat7보다 훨씬 크다(표 2 OUT_at_Vlo). 따라서 M7은 묶이지 않고 M9가 먼저 경계에 닿는다.
- 1단(M1~M5) 포화 행은 출력 전압에 의존하지 않는다. DC에서 I6 = I7이 고정이면 VSG6, 즉 O1도 고정이다. 그래서 출력 범위 끝 고리(R8)에 들지 않는다. 단, β=1 사용 상태에서는 ICMR과 엮인다(§5).

## 2. 이론 스윙 식 (DC 양)

```
V_hi = VDD − VDsat6 − VGS8(I9, V_SB = V_hi)      (V_hi에 대한 고정점 방정식, body effect)
V_lo = VSS + VDsat9
```

R8 범위 끝 헤드룸 행(범위 끝 V에서 의도 영역 = 포화):

- 상한 행 (M6): VSD6 = VDD − (V_hi + VGS8(V_SB = V_hi)) − VDsat6 ≥ 0
- 하한 행 (M9): VDS9 = V_lo − VSS − VDsat9 ≥ 0
- M7·M8 행은 범위 전체에서 큰 여유를 가지므로 묶는 행이 아니다.

## 3. gm/ID 가정별 수치 (sky130 LUT v2, tt)

**가정:** M6·M8·M9가 같은 gm/ID, 같은 L을 쓴다. gm/ID와 L은 설계 선택이며 여기서는 가정으로 놓는다. VDS는 0.6 V 격자점을 쓰고, M8은 실제 VDS를 따라간다.
- VDSAT의 VDS 감도: L = 1 µm, gm/ID = 10에서 VDS 0.3~0.9 V 범위의 변화는 M6 1.8 mV, M9 0.7 mV 이하다.
- L은 LUT 격자점(0.5·1·2 µm)만 쓰고 bin을 넘는 보간은 하지 않았다. VS는 격자 사이를 선형 보간했다.

### 표 1 -- 출력 범위 (V)

| gm/ID (S/A) | L 0.5 µm [V_lo, V_hi] | L 1 µm [V_lo, V_hi] | L 2 µm [V_lo, V_hi] | 손계산 2/(gm/ID) |
|---|---|---|---|---|
| 5 (강반전) | [0.269, 0.402] | [0.294, 0.417] | [0.318, 0.446] | 0.400 |
| 8 | [0.192, 0.614] | [0.202, 0.632] | [0.220, 0.657] | 0.250 |
| 10 | [0.160, 0.696] | [0.167, 0.713] | [0.181, 0.735] | 0.200 |
| 12 (중간 반전) | [0.135, 0.759] | [0.140, 0.775] | [0.153, 0.793] | 0.167 |
| 15 | [0.105, 0.836] | [0.108, 0.850] | [0.119, 0.864] | 0.133 |
| 18 | [0.080, 0.918] | [0.082, 0.929] | [0.092, 0.941] | 0.111 |
| 20 (약반전 쪽) | [0.065, 0.947] | [0.068, 0.956] | [0.075, 0.964] | 0.100 |

LUT gm/ID 최대값(VDS 0.6 V, V_SB 0): nfet 26.8~27.4, pfet 29.9~31.3.

### 표 2 -- 구성 항 (L = 1 µm)

| gm/ID | VDsat6 | VGS8 @V_hi | VTH8 @V_hi | VDsat9 | OUT @V_lo |
|---|---|---|---|---|---|
| 5 | 0.340 | 1.043 | 0.685 | 0.294 | 1.312 |
| 10 | 0.176 | 0.911 | 0.742 | 0.167 | 0.971 |
| 12 | 0.141 | 0.884 | 0.753 | 0.140 | 0.898 |
| 15 | 0.099 | 0.851 | 0.766 | 0.108 | 0.810 |
| 18 | 0.049 | 0.822 | 0.779 | 0.082 | 0.732 |
| 20 | 0.046 | 0.798 | 0.784 | 0.068 | 0.678 |

관찰:
- (a) 상한 손실은 **VDsat6 + VGS8(body 포함) ≈ 0.85~1.4 V** 로 하한 손실(VDsat9 ≈ 0.07~0.3 V)보다 훨씬 크다. 그래서 범위는 레일 중앙(0.9 V)에 대해 비대칭이고 아래로 치우친다. 원문 p.3의 "Maximum upper output voltage is limited", "Level shift"와 같은 방향이다.
- (b) **V_hi ≥ 0.9 V는 gm/ID ≳ 17 (M6·M8) 에서만 성립한다.** 레일 중앙 0.9 V는 gm/ID ≤ 15에서 출력 범위 밖이다.
- (c) gm/ID 15 → 18 사이에서 pfet VDSAT가 0.099 → 0.049로 불연속처럼 떨어진다. 이것은 BSIM vdsat가 약반전에서 보이는 거동이다. gm/ID ≥ 18 구간의 V_hi는 LUT VDSAT 기준(spec saturation_rule vds_ge_vdsat과 같은 정의)이며, 실제 출력저항 저하는 반영하지 않는다.

## 4. 순환 위험과 '의미 있는 요구'의 논리

- 능력 식(어떤 sizing에서든 맞는 범위)은 대략 [~0.065, ~0.96] V 다. LUT gm/ID 상한 근처를 넣은 값이다.
  - 이 값을 요구로 두면 어느 설계도 통과한다(순환).
  - 반대로 이보다 넓게 두면 실현할 수 없다.
- 의미 있는 요구의 조건은 두 가지다.
  - (1) 능력 상한보다 엄격하다. 즉 일부 gm/ID 영역을 실제로 거부한다.
  - (2) 거부 기준이 이 회로의 쓰임에서 나온다.
- 원문 단서:
  - p.5는 "Two-Stage Op Amp with Follower", 즉 buffered op amp다. spec에 rout_ss_ohm ≤ 1000(p.26-6 인용)이 있어 저임피던스 구동 버퍼로 쓰인다.
  - spec `feedback.elements = []`이므로 사용 상태는 β=1이다. 이때 **vin = vout** 이므로 사용 가능한 DC 점은 [출력 범위] ∩ [ICMR] 이다.
  - 이것이 연결과 spec에서 나오는 물리 결합이다. 관례 상수가 아니다.

## 5. 기존 spec과의 정합

- 레일: vdd 1.8 V, gnd 0 V(single supply, O-74). 위 식과 같다.
- 부하: CL 3 pF만 있다. DC 전류가 0이라 I8 = I9이고 출력 범위에 영향이 없다. 저항 부하 선언이 없다.
- 기존 constraints: gain_ss·gbw_ss·pm_ss·rout_ss(AC), offset·noise·area. 출력 범위와 충돌하지 않는다(DC/AC 분리). swing_out_v 제약은 이 회로 spec에 없어 삭제할 대상이 없다(O-154 Q3).
- icmr_v: 이 회로 spec에는 없다. input_dc = pending SP-2.

같은 LUT·같은 가정으로 nmos 입력쌍 ICMR을 계산했다(icmr.py).
- ICMR_lo = VDsat5 + VGS1(V_SB = VDsat5)
- ICMR_hi = (VDD − VSG3) − VDsat1 + VGS1, body effect 고정점

| gm/ID (L 1 µm, 전 소자 같음) | 출력 범위 | ICMR | β=1 DC 창 = 교집합 |
|---|---|---|---|
| 10 | [0.167, 0.713] | [0.974, 1.315] | **공집합** |
| 12 | [0.140, 0.775] | [0.903, 1.366] | **공집합** |
| 15 | [0.108, 0.850] | [0.816, 1.437] | [0.816, 0.850] (34 mV) |
| 18 | [0.082, 0.929] | [0.741, 1.652] | [0.741, 0.929] |
| 20 | [0.068, 0.956] | [0.690, 1.715] | [0.690, 0.956] |

- L 0.5 µm, gm/ID 15에서는 V_hi 0.836 < ICMR_lo 0.838 로 창이 공집합이다. L 2 µm에서는 [0.817, 0.864].
- **결론:** nmos 입력 + nmos follower 조합에서는 follower의 상한(VDD − VDsat6 − VGS8)과 입력쌍의 하한(VDsat5 + VGS1)이 둘 다 VGS 하나만큼 레일에서 떨어진다. 그래서 β=1 버퍼로 쓰려면 출력 쪽과 입력 쪽 모두 중간~약반전(gm/ID ≳ 15)이 필요하다.
- 1단과 출력단 gm/ID가 서로 다르면 수치가 달라진다. 결합식 V_hi(M6, M8) ≥ ICMR_lo(M1, M5)는 그대로다.

## 6. 권고

**권고 (A): vout ∈ [0.11, 0.85] V** (단일 출력, CM·Vod 해당 없음). 오차 10 mV 단위로 바깥으로 반올림했다(바깥 = 더 엄격).

- 유도: M6·M8·M9가 gm/ID = 15, L = 1 µm일 때의 능력 [0.108, 0.850]이다.
- gm/ID = 15를 고른 근거: L = 1 µm에서 β=1 DC 창(출력 범위 ∩ ICMR)이 공집합이 아니게 되는, 표에 있는 가장 낮은 gm/ID다. 가장 강반전 쪽이라 VDsat 여유가 가장 크다. §5에 따라 이 근거는 관례가 아니라 회로의 쓰임에서 나온다.
- 요구로서의 의미:
  - V_hi ≥ 0.85 V는 M6·M8 gm/ID ≲ 14 (L 1 µm)를 거부한다.
  - V_lo ≤ 0.11 V는 M9 gm/ID ≲ 14.5를 거부한다.
  - 능력 상한(~0.96 V)보다 좁으므로 늘 통과하는 요구가 아니다.
- 남는 약점:
  - (i) gm/ID 15·L 1 µm는 결합 경계에서 고른 값이다. L이 바뀌면 경계가 ±0.015 V 움직인다.
  - (ii) 이 범위만으로는 β=1 창(입력 쪽)이 보장되지 않는다. ICMR이나 입력 DC 선언이 함께 있어야 결합이 닫힌다.

### 대안 비교

| 안 | 값 | 물리 정합 | 손계산 일치 | 기존 spec 정합 | 순환 위험 | 원칙 |
|---|---|---|---|---|---|---|
| **A (권고)** | [0.11, 0.85] V, gm/ID 15·L 1 µm 능력 | 상한 VDsat6 + VGS8(body), 하한 VDsat9 고리 그대로 | 2/(gm/ID) = 0.133 대 LUT 0.099~0.108. VGS8은 body effect를 넣어야 맞는다 | 레일·부하 무관. β=1 창 [0.816, 0.850]과 겹친다 | 낮음. gm/ID ≲ 14를 거부한다 | gm/ID 근거가 회로 쓰임(β=1)에서 나온다. 단 ⚠ O-154 Q4 '미선언'을 뒤집는다 |
| B | [0.17, 0.71] V, gm/ID 10·L 1 µm(중간 반전 하단) | 고리 식은 같다 | 2/(gm/ID) = 0.2 대 LUT 0.167~0.176 | **⚠ β=1 창이 공집합**(ICMR_lo 0.974 > V_hi 0.713). 버퍼로 쓰는 DC 점이 없다 | 낮음 | ⚠ gm/ID 10은 관례(영역 이름)이며 회로 근거가 없다 |
| C | 미선언(O-154 Q4 현행) | 범위 끝 행이 없다 | -- | 현행 결정과 같다 | 없음(요구 자체가 없다) | 원칙 위반은 없다. 그러나 follower 상한 제한과 β=1 공집합을 엔진이 잡지 못한다 |
| D | [V_lo, ≥ 0.90] V, 레일 중앙 포함(gm/ID ≳ 17) | 고리 식은 같다 | -- | 형제 회로의 입력 DC 0.9 V와 맞는다 | 낮음 | ⚠ 레일 중앙·형제 회로 값은 이 회로의 근거가 아니다(SP-2 미결). 관례를 정의로 쓰는 셈이다 |
| E | 수치 대신 결합 제약 V_hi(출력) ≥ ICMR_lo(입력) 또는 '입력 DC ∈ 출력 범위' | 가장 정확하다. 결합 자체를 요구로 둔다 | -- | SP-2와 바로 연결된다 | 없음 | ⚠ 새 제약 형식(spec 형식 변경)이 필요하다. '새 집계 규칙'에 가까워 계획 개정부터 해야 한다 |

## 7. 확신도

| 항목 | 확신도 | 근거 |
|---|---|---|
| 적층 해석 | 높음 | 연결이 명확하고 원문 그림과 같다 |
| 스윙 식 | 높음 | 각 소자의 포화 행을 전수 검토했다 |
| LUT 수치 | 중상 | VDS 격자 0.6 V 근사(감도 ≤ 2 mV). gm/ID ≥ 18에서 pfet VDSAT가 불연속이다 |
| β=1 결합 결론(gm/ID ≲ 12 공집합) | 중상 | 같은 gm/ID 가정에서 나온 결론이다. 수치 검증은 SPICE .dc 확인이 필요하다 |
| 권고 A의 '값' | 중 | gm/ID·L 선택이 설계 의도라 결정은 사용자 몫이다 |

## 8. 사용자 확인 포인트

1. **O-154 Q4에서 two_stage_ota_sf는 '미선언'으로 확정됐다.** 권고 A를 채택하면 그 결정을 뒤집는다.
   - 유지(안 C)할지, A·E 중 하나로 바꿀지 정해야 한다.
2. 이 회로를 β=1 버퍼(vin = vout)로 쓰는 것이 의도인가?
   - spec의 β=1 루프는 PM 정의(AC)에서 왔다. DC 사용 상태도 β=1이라면 §5의 결합이 실제 요구가 되고, 중간 반전(gm/ID ≤ 12)은 DC 점이 없다.
3. SP-2(입력 DC) 값을 정할 때 출력 범위 안에 들도록 할 것인가?
   - 예: 0.9 V로 두면 출력 쪽 gm/ID ≳ 17이 강제된다.
4. 1단(M1~M5)과 출력단(M6·M8·M9)의 gm/ID를 따로 둘 것인가?
   - 결합 경계 gm/ID가 바뀌어 권고 A의 수치가 움직인다.
5. 권고값은 LUT VDSAT(ngspice @m[vdsat]) 기준이다. 정확값은 oracle .dc로 확인해야 한다(O-154 Q3 원천 하나 원칙).
