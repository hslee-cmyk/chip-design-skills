# erfc_ota M19~M21 `intended_region = triode` 검증 (2026-10-29)

질문(사용자): "erfc_ota의 topology 분석을 통해서 intended_region이 정말 triode가 되어야 하는지 검증해."
작성: 분석 agent(읽기·측정만, 저장소 수정 0). 회로 해석 근거 = netlist 연결과 원문만(topology 주석·태그 미사용).
스크립트·출력: `wt/_drafts/evidence/2026-10-29/erfc_region/`(`net_audit.py`→`net_audit.txt`, `run_ngspice.py`→`results.txt`·`*.cir`·`*.cir.log`, `corner_table.py`→`corner_table.txt`).
엔진 코드 줄 번호: 저장소 master 작업 트리 `skills/analog-gmid-design/gmid_engine` @ `07964dfe`.

원문: C. Wu 외, "Power-Efficient Recycling Folded Cascode OTA Based on Nested Local Feedback and Adaptive Biasing", Sensors 25(8):2523, 2025, https://pmc.ncbi.nlm.nih.gov/articles/PMC12031453/ ,
로컬 PDF `chip-design-skills/skills/analog-gmid-design/assets/heldout/sources/erfc_ota__wu_2025/source.pdf`(텍스트 `paper.md`).
- p.7 §3.1 Fig.5 본문(paper.md 338-339행): "In a static state, no current flows through the series RL CBAT, and VC is equal to VE" + 344-345·352-353행 "The RLCBAT is often designed as larger to achieve a lower low cut-off frequency… the RL also can be realized using a transistor."
- p.7 §3.2(paper.md 358-360행): "Transistors M19 to M21 are operated in the deep triode region, functioning as active resistors".
- p.8 Fig.6(회로도, `images/p08_1.png`), p.9 Table 1 "M19,20,21 3 µm/1 µm", p.11 식(paper.md 658-659행) "no current flows through resistor R1,2 … VX = VY = VZ = mVT ln{0.3IB/[(W/L)3A,4A I0]} + VTH".

## 결론

**판정: 조건부 맞음 (확신도: 중상).**

1. **연결상 구조적 0 전류는 맞다(확신도 높음).** n_m5g·n_m6g·n_m8g의 DC 전도 원소는 각각 M19·M20·M21 채널 하나뿐 -> KCL로 채널 전류 = 0. 소자 크기·바이어스와 무관하다(연결만으로 성립).
2. **"I_D = 0 -> VDS = 0"은 이상 MOS(누설 0)에서만 무조건이다.** 실제 소자에서는 드레인 접합 누설이 같은 노드의 둘째 DC 경로라서 VDS는 `I_leak · R_ch`다. 이 값은 **bulk 연결과 공정 Vth**에 달려 있다. bulk = source면 접합이 채널과 병렬이라 VDS = 0이 정확하다(실측 0.0000 V). topology의 bulk = vdd(가정)에 sky130을 쓰면 실측 VDS = **+0.21~0.25 V(M19/M20)**, **+0.026 V(M21)**이다. 이때 M19는 triode가 아니라 단자가 뒤바뀐 약반전 포화가 된다(표 C).
3. **영역 이름**: VDS = 0 < VDsat이므로 정의상 비포화(선형) 영역이다. 그래서 '`triode` = 선형'이라는 엔진 어휘로는 맞다. 다만 VSG < |Vth|이라 채널은 약반전이다. 원문의 'deep triode'(강반전 VDS ≪ VGS − Vth의 뜻)는 물리적으로 정확한 이름이 아니다. 정확한 이름은 **subthreshold(약반전) 선형 영역 = pseudo-resistor**다.
4. **엔진 관점: 선언은 지금도 DR-1 뒤에도 영역 정보로서는 중복이다.**
   - 봉인 7·9는 이미 `op.current > 0`인 소자만 판정해서 0 전류 MOS는 선언 없이 빠진다.
   - 정지는 `triode`를 읽지 않는다.
   - VDS = 0은 I = 0의 결과이지 영역 선언의 결과가 아니다.
   - 선언이 남기는 실익은 "이 0 전류는 의도된 것"이라는 **의도 확인 표지** 하나다. O-169(둘째 경로·호환 갈래 제거) 기준으로는 '영역 선언'이 아니라 '구조 규칙 + 물리 조건 점검'이 더 단순하다(아래 4절, ⚠ O-173 Q-4 재검토 권고).

## 1. 연결 확인 (net_audit.txt)

| 넷 | 닿는 원소(단자) | DC 전도 원소 | 결과 |
|---|---|---|---|
| n_m5g | M5.gate, **M19.drain**, CBAT1_L.t0(→X) | M19 채널 하나 | I_M19 = 0 |
| n_m6g | M6.gate, **M20.drain**, CBAT1_R.t0(→Y) | M20 채널 하나 | I_M20 = 0 |
| n_m8g | M7.gate, M8.gate, **M21.drain**, CBAT2.t1(→n_m7d) | M21 채널 하나 | I_M21 = 0 |
| Z | M19·M20·M3A·M4A gate, R1.t1, R2.t0 | R1, R2 | I_R1 = I_R2 -> V_Z = (V_X + V_Y)/2 (R1 = R2 = 52 kΩ) |
| vcn(레일) | M19·M20 source, M3C·M4C·M17B·M18B·M21 gate | -- | |
| vcp(레일) | M21 source | -- | |

- 오케스트레이터 1차 판독(M19 D = n_m5g, G = Z, S = vcn; M21 D = n_m8g, G = vcn, S = vcp)은 연결·Fig.6(p.8)과 일치한다.
- 비레일 넷 중 DC 전도 원소가 하나뿐인 넷은 이 셋뿐이다(스크립트 전수).
- 이 판정은 연결만 쓰므로 소자 크기·바이어스와 무관하다. 단 'DC 원소'에 MOS 접합(bulk)을 넣지 않은 이상화다. 2절 참고.

## 2. 영역의 물리

**식(약반전 채널, 소스·드레인 대칭):** I_D = I_0·e^{(V_SG − |V_th|)/(n·V_T)}·(1 − e^{−V_SD/V_T}).
- I_D = 0 ⇔ V_SD = 0이다. 채널 전도가 0이 아닌 한 어느 V_SG에서나 성립하고, 강반전에서도 같다.
- 그래서 **이상 소자에서는 VDS = 0이 영역 선언과 무관하게 KCL과 소자식에서 나온다.**
- VDS = 0 < VDsat(약반전 VDsat ≈ 3~4 V_T, 실측 vdsat 0.044 V)이므로 비포화(선형) 영역이다.
- V_SG < |V_th|이면 '차단'이 아니라 **약반전 선형**이다. 소신호 저항 R = 1/g_ds(VDS = 0) = n·V_T… 꼴로 지수적으로 크다. 이것이 pseudo-resistor다.

**V_Z 대표 동작점**
- 원문 p.11: V_Z = m·V_T·ln(0.3·I_B/((W/L)_3A·I_0)) + V_TH이고, M3A가 약반전이라 V_Z < V_THn이다.
  - 0.18 µm(V_THn ≈ 0.4~0.5 V) 추정: V_Z ≈ 0.35~0.45 V, **V_SG19 = 0.7 − V_Z ≈ 0.25~0.35 V**. (추정이고 실측 아님 -- 원문 공정 모델 없음.)
- sky130 전체 회로 .op 실측(`results.txt` B): V_Z = 0.496 V, V_SG19 = 0.204 V.
- M21: V_SG = V_CP − V_CN = 0.4 V로 고정(연결에서 바로 나옴).

**sky130 pfet_01v8 실측(W = 3 µm, VDS = 0, tt, `results.txt` A gmin = 1e-18; L = 1 µm = Table 1)**

| bulk | source | V_SG 0.20 | 0.30 | 0.40 | 0.45 | 0.50 | BSIM vth |
|---|---|---|---|---|---|---|---|
| vdd(topology 가정) | 0.7 V (M19/M20) | R = 3.6e17 Ω | 1.2e16 | 4.2e14 | 7.7e13 | 1.4e13 | 1.23 V |
| vdd | 1.1 V (M21) | 2.1e16 | 7.5e14 | 2.7e13 | 5.1e12 | 9.7e11 | 1.16 V |
| source | 0.7/1.1 V | 4.8e13 | 2.0e12 | 8.5e10 | 1.8e10 | 3.8e9 | 1.00 V |

- L = 0.5·2·4 µm 결과는 `results.txt` A에 있다(L↑ → R↑, 경향 같음).
- 모든 점에서 V_SG < |V_th|라 약반전이다. sky130에서 0.2~0.5 V는 전부 문턱 아래다.
- bulk = vdd에서 접합 기하 0, gmin = 1e-12인 '1 mV 직접 R'은 9.0e8 Ω이고 V_SG와 무관했다. 이는 **ngspice gmin × V_DB 인공 전류**(1e-12 S × 1.1 V = 1.1 pA)다. gmin = 1e-18이면 1.0e11 Ω로 바뀐다. 그래서 위 표는 모델 g_ds(채널만)로 적었다.

**부유 드레인 평형(표 C, 접합 기하 ad = as = 0.87 p, 드레인 = 채널·접합·1 pF만)**

| 소자 꼴 | gate | bulk | gmin 1e-12 | 1e-15 | 1e-18 |
|---|---|---|---|---|---|
| M19/M20 (S = 0.7) | 0.35 | vdd | +0.275 V | +0.136 | +0.126 |
| M19/M20 | 0.4957 (sky130 V_Z) | vdd | +0.392 | +0.255 | **+0.246** |
| M21 (S = 1.1) | 0.7 | vdd | +0.156 | +0.031 | **+0.026** |
| 모두 | -- | source | 0 | 0 | **0** |

- 전체 회로(gmin 1e-18)에서도 V(n_m5g) = 0.947 V(목표 0.7 V), V(n_m8g) = 1.126 V(목표 1.1 V)로 같다.
- 메커니즘: n-well(vdd) → p+ 드레인으로 흐르는 역바이어스 누설(실측 약 2 fA)이 같은 노드의 둘째 DC 경로다. 채널 R이 1e14~1e17 Ω이라 그 전류를 흘리려면 VSD가 수백 mV 필요하다. 그러면 높은 쪽 단자가 실효 소스가 되어 VSD > VDsat, 즉 **역방향 약반전 포화**가 된다.
- 판정 영향: '구조적 0 전류 → VDS = 0'의 물리 조건은 **I_leak · R_ch ≪ 엔진 전압 허용치**다.
  - bulk = source: 항상 성립(구조적).
  - bulk = vdd: 공정 V_th에 달림.
    - sky130에서는 깨진다(M5·M6 캐스코드 게이트 +0.25 V, M7·M8 게이트 +0.026 V).
    - 원문 0.18 µm(|V_thp| 약 0.45~0.6 V, body 효과 포함 추정)에서는 R_ch ~1e7~1e9 Ω × fA → µV라 성립할 것으로 추정한다(실측 아님).
- topology `_bulk_comment`가 이미 "M19~M21 bulk의 source 연결 여부 사용자 확인 필요"로 열어 두었다. 그림이 3단자 기호라 근거가 없다(Fig.6 p.8).

## 3. 회로 목적과의 정합

- **원문 의도는 VDS = 0이다.** p.7 Fig.5 본문 "static state, no current flows through the series RL CBAT, and VC is equal to VE"는 DC에서 cascode 게이트 = 바이어스 레일(VCN·VCP)이라는 뜻이다. 그리고 "RL also can be realized using a transistor"이므로 M19~M21 = R_L이다. 즉 **부유 전지(floating battery) + RC 고역 통과**: DC는 MOS 저항이 레일 전위로 잡고, 과도 신호는 CBAT로 X·Y(n_m7d)에서 cascode 게이트로 넘긴다(p.7 "VS travels through the RC highpass filter to the gate of the cascode transistor").
- **모서리 조건**: f_HP = 1/(2π·R_ds·C_BAT)이 신호·과도 대역(GBW 1.37 MHz, 1% 정착 0.473 µs; spec_source.md 2절, p.15 Table 2) 아래에 있어야 결합이 동작한다. 원문도 "lower low cut-off frequency"를 요구한다.
  - 실측 R(sky130, `corner_table.txt`): C_BAT 0.1~10 pF에서 f_HP = 4e-8 Hz~4e2 Hz, f_HP/GBW ≤ 3e-5. 모든 점에서 GBW보다 4자릿수 이상 아래다.
  - 원문 공정 추정 R(1e7~1e9 Ω) × 1 pF → 160 Hz~16 kHz. 역시 GBW보다 85배 이상 아래다(추정).
  - 이 조건이 쉽게 만족되는 이유가 약반전(큰 R)이다. 강반전 'deep triode'(R ~1e5~1e6 Ω)였다면 1 pF에서 f_HP가 0.16~1.6 MHz로 GBW와 겹친다. 그래서 **이 소자의 역할에 맞는 이름은 'deep triode'보다 'subthreshold 선형 pseudo-resistor'**다.
- 반대쪽 한계: R이 너무 크면 DC 전위를 누설이 정한다(2절). 그래서 설계 조건은 두 면이다. **f_HP ≪ 신호 대역**(R 크게)과 **I_leak · R ≪ 허용 바이어스 오차**(R 작게 또는 bulk = source).
- 관찰: CBAT 값은 spec에서 engine:true(B-5)인데, 엔진이 이 모서리 조건을 걸 자리(g_ds(VDS = 0) 조회·f_HP 판정)가 있는지는 이번 범위 밖이라 확인하지 않았다.

## 4. 엔진 관점

**as-built 사실**(코드 실측, 줄은 @ `07964dfe`)
- `gmid_engine/sizing/current_basis.py:129-133`: KCL 해에서 항이 빈 MOS(`dead`)는 `StructureUnresolvedError`(`mos_zero_current_structural`)를 낸다. **`linear_devices`·`triode`를 읽지 않는다.** 그래서 지금은 선언해도 erfc_ota는 같은 자리에서 멈춘다. 저항만 잎 가지치기되고(`graph/dc_conduction.py:12`) MOS는 가지치기되지 않는다.
- `sizing/seal_saturation.py:56`: `if op.current > 0 and m not in linear_devices`, `sizing/seal_conduction.py:41`: `if not op.current > 0: continue`. **0 전류 MOS는 봉인 7·9에서 선언 없이 이미 빠진다.** M19~M21에 대한 triode 선언의 봉인 7 효과는 0이다(중복).
- `sizing/block_columns.py:230`: 입력 창 포화 행에서 linear 소자를 뺀다. 대상은 `dc_coord`가 있는 소자이고, 0 전류 소자는 좌표가 정의되지 않는다.
- `sizing/symmetry_marks.py:23`: 선언은 대칭 블록의 처음 색에 `("linear", 0)` 표시로 들어간다. M19/M20 쌍은 같은 표시라 궤도가 바뀌지 않는다.
- 계획 N6.36 DR-1 범위(gain-budget plan 2341행): "erfc_ota '`triode` 선언·구조적 0 전류 MOS = VDS 0 연결(노드 묶음)' 규칙… 선언 없는 0 전류 MOS 정지는 유지"(O-173 Q-4).

**대안 비교**

| 안 | 내용 | 물리 정합 | 손계산·단순성(O-169) | fail-closed | 판정 |
|---|---|---|---|---|---|
| (가) 현 O-173 Q-4 | triode 선언이 있는 0 전류 MOS만 VDS = 0 묶음, 없으면 정지 | VDS = 0은 I = 0에서 나오는데 선언을 조건으로 건다. 영역은 출력 양인데 입력으로 받음. 누설 조건 점검 없음 | 같은 사실(0 전류) 아래 선언 유무로 두 갈래가 생김 | 의도 확인은 됨 | 조건부 |
| (나) 선언 없이 구조 규칙 | DC 원소가 그 채널 하나뿐인 넷 = 소스 쪽 고정 노드와 같은 전위(VDS = 0), 영역 = 결과 필드 '선형' | KCL + 소자식 그대로, 회로 이름·상수 0 | 한 규칙, 선언 0 | 연결 오류(끊긴 드레인)도 통과시킨다. 다만 connectivity는 사용자 확정(2026-10-14) 단계에서 걸러짐 | 권고 기본 |
| (다) (나) + bulk·누설 조건 | (나)에 'bulk = source 또는 같은 넷'이면 정확, 아니면 정지(또는 사용자 확인) | 2절 실측 조건을 구조로 반영(bulk 넷은 연결 사실) | 조건 하나 추가, 누설 모델 불필요 | sky130 bulk = vdd 같은 실패를 막음 | **권고** |

- ⚠ **원칙 경고(사용자 결정 재검토)**: O-173 Q-4의 '선언 있을 때만 VDS = 0' + '선언 없는 0 전류 MOS 정지 유지'는 두 가지와 충돌한다. (1) 영역(결과 양)을 입력 선언으로 받는다 -- DC 양은 풀이로(DEC-67 DC/AC 원칙 계열), 정본 하나. (2) 같은 구조 사실에 선언 유무 두 갈래를 둔다 -- O-169.
- 또 (가)·(나) 모두 **bulk = vdd에서 VDS ≠ 0이 되는 물리 조건**을 보지 않는다. 이 조건은 sky130 실측에서 0.25 V 오차를 만든다.
- 권고 (다)는 회로 이름 조건 0, 상수 0, 새 cache 0이다. 연결(bulk 넷 = source 넷)만 읽고, VDS = 0 노드 묶음의 writer는 DR-1 블록 하나로 둔다(graph 단일 정본 위반 없음).
- erfc_ota에 적용하려면 **M19~M21 bulk 결정(사용자 -- 회로 해석·topology connectivity 사안)**이 착수 조건이 된다. bulk = vcn/vcp(source)로 확정하면 VDS = 0은 정확하다. 그러면 `intended_region = triode` 선언은 필요 없다.
- 선언을 남길지 판단(O-169): 남길 근거가 '이미 승인됨'뿐이면 근거가 아니다. 남길 실익은 '의도 확인'인데, 그것은 영역 선언이 아니어도 된다. 예: 사용자 확정 connectivity와 bulk 결정이 그 역할을 이미 한다.

**9 물리 검증 요약**

| 항목 | 값 |
|---|---|
| 물리 결정자 | KCL(넷 DC 원소 = 채널 하나) + 채널식 I ∝ (1 − e^{−V_SD/V_T}) + 접합 누설 경로(bulk 연결) |
| 식/원문 | p.7 Fig.5 본문 "no current … VC = VE", p.7 §3.2 'deep triode … active resistors', p.11 V_Z 식, p.9 Table 1 3/1 µm |
| 실측 | sky130 tt ngspice-46. VDS = 0 g_ds 표(L 0.5~4 µm, V_SG 0.2~0.5 V, bulk 2가지), 부유 드레인 평형(gmin 3단계), 전체 회로 .op 2회 |
| 판정 | 구조적 0 전류: 맞음(높음). 영역 = 선형(약반전): 맞음(중상). 'deep triode' 이름: 부정확. VDS = 0: bulk = source면 맞음, bulk = vdd면 공정 조건부(sky130 틀림 0.25 V). 선언 필요성: 영역 정보로는 불필요(중복), 엔진 규칙은 구조 + bulk 조건으로 |

## 5. 한계

- 원문 0.18 µm 공정 모델이 없어 원문 공정의 R·V_Z는 추정이다(실측은 sky130 대용).
- 전체 회로 sky130 .op는 원문 바이어스(VCP 1.1·VCN 0.7 V는 원문 공정용)를 재현하지 못한다. M5·M7 가지가 붕괴했다(I_M7 ≈ 0.17 µA, n_m7d ≈ 6 mV). 그래서 B의 값은 M19~M21 국소 메커니즘(V_Z·누설 평형) 확인용으로만 썼다.
- 소신호 측면(M5 게이트가 CBAT로 X에 결합해 생기는 추가 gm 경로가 식 (10)에 빠져 있는지)은 이번 범위 밖이다.
