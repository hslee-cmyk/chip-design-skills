# common_gate_amplifier 출력 범위 spec 후보 (독립 해석, 2026-10-26)

- 역할: 독립 회로 해석자, 읽기 전용. 앞선 조사(output_range_candidates.md)는 근거로 쓰지 않았다.
- 근거 자료
  - connectivity: `assets/library/common_gate_amplifier.topology.json` `netlist`(M1~M3 단자·넷)와 `ports`만 썼다. 태그·주석·`_reference_relations`는 쓰지 않았다.
  - spec: `assets/library/common_gate_amplifier.sizing_spec.json` (레일 vdd 1.8 V, gnd 0 V, `input_dc` = pending SP-2, 부하 CL = SP-6(c) 대기, constraints는 noise_excess_th·area_search_m2 둘뿐, swing_out_v·icmr_v 없음)
  - 원문: P.E. Allen, *CMOS Analog Circuit Design* Lecture 20, Page 20-2(PDF p.2, 그림 060609-01 오른쪽, 060609-02 대신호 특성). 웹 https://aicdesign.org/wp-content/uploads/2018/08/lecture20-140624.pdf , 로컬 `assets/library/sources/common_gate_amplifier__allen_2014/source.pdf`(p.2), 렌더 `pages/p02.png`
  - LUT: `C:/Users/HSLEE/Documents/Todoc/fpga/lut_data/sky130_lut_v2/sky130_nfet_pfet_lut_v2_r2.npz` (`lut_v2_location.json`의 cap_npz, sha256 938e95b9...), tt 27 °C, W_ref 5 µm, 축 [L, VGS, VDS, VS], VS = |VSB|. VDSAT = ngspice `@m[vdsat]`(BSIM). 계산 스크립트·원표: `C:/Users/HSLEE/Documents/Todoc/fpga/wt/_scratch_swing_common_gate/vdsat.py`, `vdsat_table.txt`
  - 결정: user_decisions.md O-154(특히 Q4), O-128 Q5, O-23/O-26(DC/AC 분리)

## 1. topology 해석 (connectivity만)

| 소자 | 종류 | D | G | S | 
|---|---|---|---|---|
| M1 | nmos | vin | VNBias1 | gnd |
| M2 | nmos | vout | VNBias2 | vin |
| M3 | pmos | vout | VPBias1 | vdd |

- 출력 노드: `vout`(ports.vout = single_ended_output). vout에 붙은 단자 = M2.D, M3.D 둘뿐이다. 수동소자 0, 부하 미선언.
- 입력 노드: `vin`(ports.vin = 입력, 전압원이 직접 구동). vin에 붙은 단자 = M1.D, M2.S.
- 게이트 넷 VNBias1·VNBias2·VPBias1은 게이트에만 붙고 구동 소자가 없다 -> DC 고정 바이어스(교류접지).

### 위쪽 경로 (vout -> vdd)
- vout -[M3 D-S]- vdd. MOS 1개. M3는 S = vdd, G = 고정 바이어스 -> 레일 source 전류원. 포화 조건: V_SD3 >= VDsat3 -> **vout <= VDD - VDsat3**. 적층 = VDsat 1개.

### 아래쪽 경로 (vout -> gnd)
- vout -[M2 D-S]- vin -[M1 D-S]- gnd. MOS 2개 직렬.
- 단 중간 노드 vin은 입력 전압원이 정하는 노드다. 그래서 두 항의 성격이 다르다.
  - M2 포화: V_DS2 >= VDsat2 -> **vout >= vin + VDsat2** (출력 쪽 조건)
  - M1 포화: V_DS1 = vin >= VDsat1 -> **vin >= VDsat1** (입력 DC 쪽 조건, 출력과 직접 무관)
- 따라서 출력 하한은 V_lo = vin_DC + VDsat2이고, 입력 DC를 M1 포화 한계까지 낮췄을 때만 V_lo = VDsat1 + VDsat2(VDsat 2개 적층)가 된다. Allen p.2 그림 060609-02도 vIN 축에서 VON1을 지난 뒤 vOUT 바닥이 VON1+VON2인 것으로 같은 구조를 보인다.

### 출력단 종류 판정
- M2: 게이트 = 고정 바이어스, 신호 입력 = source(vin), 출력 = drain(vout) -> **공통 게이트(CG)**. follower 아님(출력이 source가 아님), 공통 소스 아님(신호가 게이트로 들어가지 않음).
- vout은 두 drain만 만나는 **고임피던스 노드**(전류원 부하 M3 대 CG M2). 출력 DC는 I_D2(VNBias2 - vin) = I_D3 균형으로만 정해진다.
- 단일 출력(출력 포트 1개, 대칭 쌍 없음). 되먹임 경로 없음(vout에서 어느 게이트·source로도 돌아가는 연결 없음), CM 제어 없음.
- 확신도: 높음(연결이 단순하고 원문 p.2 회로·대신호 그림과 일치).

## 2. 이론 스윙 식 (DC 양)

- V_hi = VDD - VDsat3
- V_lo = vin_DC + VDsat2(VSB2 = vin_DC),  vin_DC >= VDsat1
- 최소(능력) V_lo = VDsat1 + VDsat2  (원문 p.2 "VOUT(min) ≈ VDS1(sat) + VDS2(sat)", "VOUT(max) ≈ VDD - VDS3(sat)"와 같은 꼴 -- 식 꼴만 대조, 값은 아래에서 sky130으로 유도)
- VGS 항 없음(follower가 아니므로). 다만 VNBias2 = vin_DC + VGS2 <= VDD 는 바이어스 쪽 필요조건(출력 범위와는 무관, 1.8 V에서 여유 큼).
- M2는 VSB = vin_DC > 0 (벌크 = gnd, DEC-61 기본 규칙)이라 VDsat2는 VSB를 반영해 읽었다(영향 +0.005~0.01 V 수준).

## 3. 수치 (sky130 LUT, gm/ID 가정별)

조회 조건: L = 1.0 µm(대표 가정), M1·M3 VSB = 0, M2 VSB = 0.2 V(vin_DC 근방), VDS = 0.3 V. L 0.5~2 µm, VDS 0.3~0.9 V로 바꿔도 VDsat 변화는 ±0.02~0.03 V 이내(vdsat_table.txt).
gm/ID는 **설계 선택(가정)**이다. 세 소자 같은 gm/ID로 둔 대표점.

### 3a. VDsat 값

| gm/ID 가정 [S/A] | 영역 | nmos VDsat (BSIM, VSB0) | nmos M2 VDsat (VSB 0.2) | pmos VDsat (BSIM) | 손계산 2/(gm/ID) |
|---|---|---|---|---|---|
| 5 | 강반전 | 0.278 | 0.282 | 0.314 | 0.400 |
| 8 | 강~중간 | 0.200 | 0.204 | 0.218 | 0.250 |
| 10 | 중간 | 0.166 | 0.170 | 0.175 | 0.200 |
| 15 | 중간~약 | 0.109 | 0.112 | 0.099 | 0.133 |
| 20 | 약반전 쪽 | 0.069 | 0.072 | 0.046 (주의) | 0.100 |

주의: pmos는 gm/ID 15->18 사이에서 BSIM `vdsat`가 0.10 -> 0.047 V로 꺾인다(같은 구간 VGS도 1.02 -> 0.81 V로 뛴다). 약반전에서 BSIM vdsat는 물리적 포화 경계(수 kT/q)보다 작게 나오므로 gm/ID >= 18의 pmos 값은 낙관값이다.

### 3b. 출력 범위 (vin_DC = VDsat1, 즉 입력 DC를 M1 포화 한계에 둔 최대 폭)

| gm/ID 가정 | V_lo BSIM (VDsat1+VDsat2) | V_hi BSIM (1.8 - VDsat3) | 폭 BSIM | V_lo 손계산 (4/(gm/ID)) | V_hi 손계산 (1.8 - 2/(gm/ID)) | 폭 손계산 |
|---|---|---|---|---|---|---|
| 5 | 0.560 | 1.486 | 0.93 | 0.800 | 1.400 | 0.60 |
| 8 | 0.404 | 1.582 | 1.18 | 0.500 | 1.550 | 1.05 |
| 10 | 0.336 | 1.625 | 1.29 | 0.400 | 1.600 | 1.20 |
| 15 | 0.221 | 1.701 | 1.48 | 0.267 | 1.667 | 1.40 |
| 20 | 0.141 | 1.754 (낙관) | 1.61 | 0.200 | 1.700 | 1.50 |

vin_DC를 VDsat1보다 높게 두면 V_lo는 그만큼(vin_DC - VDsat1) 올라간다. V_hi는 vin_DC와 무관.

## 4. 순환 위험과 '의미 있는 요구'

- 능력 식 V_lo = VDsat1 + VDsat2, V_hi = VDD - VDsat3를 **후보 자신의 sizing으로 평가**해 요구로 쓰면, R8 범위 끝 고리는 정의상 항상 성립해 아무것도 거르지 않는다(순환).
- 요구가 의미를 가지려면 범위가 **sizing과 독립인 숫자**여야 한다. 숫자 [V_lo, V_hi]를 고정하면 R8은 (i) M3: VDsat3 <= VDD - V_hi, (ii) M2: VDsat2 <= V_lo - vin_DC, (iii) 입력 DC: vin_DC >= VDsat1 를 강제한다. 즉 범위 선언 = '각 소자의 gm/ID 하한(VDsat 상한)' 요구가 된다. 이것이 설계 의미다.
- 이 회로에서 범위의 원천은 응용 요구여야 하는데, 원문(Allen p.2~p.4)에는 구동 대상·출력 진폭·부하 요구가 없다. p.2는 능력 식(근사)만, p.3은 소신호 Av = gm2·(rds2||rds3), Rin, Rout, p.4는 부하에 따른 Rin 변화만 준다. 따라서 범위 숫자는 **원문 응용에서 유도되지 않고 gm/ID 설계 의도 가정에서만** 나온다 -- 이 가정은 사용자 몫이다.
- 고임피던스 출력 + 되먹임 없음: 출력 DC 위치는 I_D2 = I_D3 균형으로만 정해지고 이득이 커서(gm2·ro/2 꼴) 출력 범위 전체가 입력으로는 Δvin = Δvout/Av(수 mV) 안에 몰린다. 범위 끝 판정은 DC 전달특성(.dc vin 훑기, 원문 그림 060609-02와 같은 꼴)으로 한다(DC/AC 분리 -- 범위는 DC 양, 이득은 AC 양으로 따로).

## 5. 기존 spec과의 정합

- 레일: [V_lo, V_hi]는 [0, 1.8] 안에 있어야 한다 -- 모든 후보 만족.
- icmr_v: 이 회로 spec에 없다. 대신 이 회로의 입력 DC(input_dc, **pending SP-2**)가 출력 하한과 묶인다: VDsat1 <= vin_DC <= V_lo - VDsat2. 범위를 선언하면 SP-2 값 선택이 이 부등식의 제약을 받는다(SP-2를 먼저 정하면 V_lo의 하한이 vin_DC + VDsat2로 정해진다). follower와 달리 ICMR-출력 범위의 VGS 연결은 없다.
- 부하: CL 미선언(SP-6(c)), 정상상태 부하 전류 0 -> 출력 KCL은 I_D2 = I_D3. 범위 끝에서 공급 전류 요구(R10 (i))는 SR·CL이 없어 비어 있다.
- 기존 swing_out_v: 이 spec에 없다 -> O-154 Q3 삭제 대상 없음.
- **기존 결정과의 관계(중요)**: O-154 Q4는 common_gate를 **미선언**으로 확정했다(미선언 = 범위 끝 요구 행 없음, 능력은 '정의 불능' 표시, O-154 Q1). 아래 권고 범위를 채택하려면 O-154 Q4의 common_gate 항목을 다시 여는 사용자 결정이 필요하다 -- 원래 결정과 다름.

## 6. 권고와 대안

### 권고 (선언한다면): 출력 절대 범위 [0.40, 1.60] V, 단일 출력
- 근거: 세 소자 gm/ID = 10 S/A(중간 반전, 이득·속도·헤드룸 절충점이라는 설계 의도 '가정')에서 손계산 VDsat = 2/(gm/ID) = 0.2 V를 적층 수(아래 2, 위 1)에 곱한 값. V_lo = 2 x 0.2, V_hi = 1.8 - 0.2.
- BSIM 포화 판정(spec saturation_rule vds_ge_vdsat)으로 보면 이 범위는 대략 nmos gm/ID >= ~8, pmos gm/ID >= ~8.8 을 요구한다(3a 표 보간). gm/ID 10 설계는 BSIM 기준으로 V_lo 쪽 0.06 V, V_hi 쪽 0.025 V 여유를 남긴다.
- 조건: 입력 DC는 VDsat1 <= vin_DC <= 0.40 - VDsat2 이어야 한다(gm/ID 10이면 BSIM으로 약 0.17~0.23 V). SP-2 값이 이보다 높으면 V_lo를 vin_DC + VDsat2로 올려야 한다.
- 단, **원칙상 가장 무리 없는 선택은 O-154 Q4대로 미선언 유지**다(대안 D). 원문에 응용 근거가 없어 숫자가 전적으로 gm/ID 가정에서 나오기 때문이다. 권고 [0.40, 1.60] V는 '이 회로로 R8 범위 끝 고리를 검증 발동시키고 싶다'는 목적이 있을 때의 후보다.

### 대안 비교

| 항목 | A. [0.40, 1.60] gm/ID 10 손계산 (권고) | B. [0.80, 1.40] gm/ID 5 강반전 | C. [0.27, 1.67] gm/ID 15 | D. 미선언 유지 (O-154 Q4) |
|---|---|---|---|---|
| 물리 정합 | 중간 반전, VDsat 손계산이 BSIM보다 0.03 V 보수 -- 정합 | 정합, 그러나 1.8 V에서 폭 0.6 V로 헤드룸 낭비 | pmos가 BSIM vdsat 꺾임 구간 근처 -- 판정이 낙관 쪽으로 흔들릴 위험 | 해당 없음 |
| 손계산 일치 | 2/(gm/ID) 그대로, 원문 p.2 식 꼴과 일치 | 일치 | 일치하나 약반전 쪽은 2/(gm/ID) 근사 자체가 거칠다 | -- |
| 기존 spec 정합 | SP-2 vin_DC 창 0.17~0.23 V 생김(좁지만 존재) | vin_DC 창 넓음(0.28~0.52 V) | vin_DC 창 0.11~0.16 V로 좁다 | 충돌 없음 |
| 기존 결정 | O-154 Q4 재개방 필요 | 재개방 필요 | 재개방 필요 | O-154 Q4와 일치 |
| 순환 위험 | 없음(숫자 고정, gm/ID >= ~8 강제) | 없음(대부분 설계가 쉽게 통과 -> 걸러내는 힘 약함) | 없음(엄격, gm/ID >= ~12 강제 -> 탐색 공간 크게 좁힘) | 없음(요구 행 자체가 없음) |
| 원칙(상수 발명·논문 값) | gm/ID 10은 가정 -- 사용자 확정 필요 | 가정 | 가정 | 가장 깨끗(가정 없음) |

## 7. 확신도

- 출력 노드·적층(위 1, 아래 2 단 M1 항은 입력 DC 경유)·CG 판정·단일 출력·되먹임 없음: **높음**
- 스윙 식: **높음** (연결 유도와 원문 p.2 식 꼴이 일치)
- 수치: LUT 조회는 **높음**(재현 스크립트 있음), 단 gm/ID·L·vin_DC가 가정이므로 권고 숫자 자체는 **중간**
- 권고 채택 여부: O-154 Q4 미선언 결정과 충돌하므로 **사용자 결정 사항**

## 8. 사용자 확인 포인트

1. O-154 Q4의 common_gate '미선언'을 유지할지, 다시 열어 범위를 선언할지(원래 결정과 다름).
2. 선언한다면 설계 의도 gm/ID(권고 10 S/A, 손계산 기준) -- 이것이 범위 숫자를 정한다.
3. SP-2 input_dc: 범위 선언 시 VDsat1 <= vin_DC <= V_lo - VDsat2 창 안에 두어야 한다(권고 A면 약 0.17~0.23 V). SP-2를 먼저 다른 값으로 정하면 V_lo는 vin_DC + VDsat2로 따라 올라가야 한다 -- 순서(SP-2 먼저 vs 범위 먼저) 결정 필요.
4. 범위 끝 판정의 VDsat 정의: spec saturation_rule은 BSIM `vdsat`(vds_ge_vdsat)인데 약반전 pmos에서 BSIM vdsat가 물리 경계보다 작다(3a 주의). gm/ID >= 15 쪽 후보를 고르면 이 점을 함께 정해야 한다.
