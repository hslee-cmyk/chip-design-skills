# O-174 재검토: erfc_ota M19·M20 bulk = vcn, M21 bulk = vcp (2026-10-31)

질문(사용자, O-198): "bulk를 바꾼 결정이 합리적이고 물리정합이 되는지 다시 확인해."
작성: 회로·물리 분석 agent(읽기·측정만; 저장소·topology·spec·git 쓰기 0). 결정 기록(O-174)은 근거로 쓰지 않음(원칙 20).
측정: `o174_recheck/recheck.py` -> `o174_recheck/results.txt`(D·E·F), deck·log 같은 폴더. sky130 tt, ngspice-46, gmin 1e-18.
원문: C. Wu 외, Sensors 25(8):2523, 2025, https://pmc.ncbi.nlm.nih.gov/articles/PMC12031453/ ,
로컬 PDF `chip-design-skills/skills/analog-gmid-design/assets/library/sources/erfc_ota__wu_2025/source.pdf`(텍스트 `paper.md`, 그림 `images/`).

## 결론

**판정: 조건부 맞음 -- (가) bulk = source 유지 권고 (확신도: 중상).**

- DC: bulk = source면 드레인 VDS = 0이 온도·접합 기하와 무관하게 정확하다(실측 48점 모두 0.0000 V). 원문이 명시한 정적 의도 "VC is equal to VE"(p.7)를 그대로 만족한다. bulk = vdd면 sky130에서 M19·M20 +0.05~+0.45 V, M21 +0.0001~+0.22 V로 **온도·레이아웃 기하에 따라 흔들리는** 오프셋이 생긴다. 엔진(LUT, 누설 모델 없음)이 예측할 수 없는 값이다.
- PDK: M19~M21은 **세 개 모두 pmos**다(원문 Fig.6 화살표, topology kind). 그래서 deep n-well은 필요 없다. 별도 n-well 섬 2개(vcn 1개는 M19·M20 공유, vcp 1개)로 표준 sky130에서 실현된다. 대가는 well 간격만큼의 면적과, well–기판 용량이 vcn·vcp(바이어스 레일)에 붙는 것이다.
- **새로 찾은 대가(O-174 근거에 없던 항목)**: bulk = source면 드레인이 source보다 올라가는 대신호 방향에서 두 효과가 함께 생긴다. (1) p+ 드레인/n-well 접합이 순바이어스된다. (2) 실효 source(드레인 쪽)에 순방향 body 바이어스가 걸려 채널이 더 많이 전도한다. 둘 다 CBAT 승압을 빨리 새게 한다. M19·M20에서 이 방향(X↑ → M5 게이트↑)은 원문 기법이 쓰는 방향이다.
  - 실측(F, CBAT 1 pF, dX +0.8 V, 0.5 µs 뒤): bulk = vdd에서 0.763 V가 남고 bulk = source에서 0.525 V가 남는다.
  - dX ≤ 0.4 V(CBAT ≥ 1 pF)에서는 두 경우 차가 ≤ 0.004 V다.
  - M21의 유용 방향(아래로)에서는 차이가 없다(−0.791 대 −0.791).
- 그래서 "맞음"이 아니라 "조건부"다. 조건은 **이 대신호 손실이 slew/정착 spec을 깨지 않음**이고, 아직 전체 회로 과도(오라클)로 재지 않았다(아래 '더 잴 것').

## 1. 원문 (직접 읽음)

| 항목 | 내용 | 쪽 |
|---|---|---|
| M19~M21 기능 | "Transistors M19 to M21 are operated in the deep triode region, functioning as active resistors" | p.7 §3.2 (paper.md 358-360) |
| R_L 역할 | Fig.5(b) 부유 게이트 바이어스: "In a static state, no current flows through the series RL CBAT, and VC is equal to VE" / "VS travels through the RC highpass filter to the gate of the cascode transistor, preventing the transistor connected to its source from entering the linear region" / "the RL also can be realized using a transistor" | p.7 (paper.md 338-353), 그림 `images/p07_1.png` |
| 기호·kind | Fig.6: M19·M20 = pmos(source = VCN, gate = Z, drain = M5·M6 gate), M21 = pmos(source = VCP, gate = VCN, drain = M7·M8 gate). **3단자 기호**라 bulk가 그려져 있지 않다. Fig.5도 3단자다. 본문에 body·bulk·well 서술은 0건이다(grep "bulk\|body\|substrate\|well" -- 무관한 문장만 나옴) | p.8 `images/p08_1.png` |
| 치수·공정 | M19,20,21 = 3 µm/1 µm(Table 1 p.9). "0.18 µm CMOS process", 1.8 V(p.13). 바이어스 VCP 1.1 V, VCN 0.7 V(Fig.6 표) | p.9, p.13 |
| 레이아웃 | Fig.8(`images/p12_1.png`): 가드링 섬이 여러 개 보이지만 층 범례가 없어 M19~M21 well 연결은 판독할 수 없다 | p.12 |

- 원문 관례: 논문 전체가 3단자 기호다. 원문은 bulk를 정하지 않았다. 원문에서 bulk를 정하는 데 쓸 수 있는 유일한 문장은 **정적 의도 VC = VE**(= 드레인 DC = 레일)다.

## 2. 연결 (master 작업 트리, `assets/library/erfc_ota.topology.json`)

- M19: pmos d = n_m5g, g = Z, s = vcn, b = vcn. M20: d = n_m6g, g = Z, s = vcn, b = vcn. M21: pmos d = n_m8g, g = vcn, s = vcp, b = vcp. 나머지 26개 MOS는 bulk를 kind별 레일(vdd/gnd)로 **명시**했다.
- `supply_nets` = [vdd, gnd, vcp, vcn]이다. vcn·vcp는 원문 Fig.6의 이상 전압 단자를 레일로 둔 것이다(`_supply_nets_comment`). 신호 넷이 아니라 DC 고정 레일이고, AC 접지다.
- DEC-61(계획 260행)·O-188: bulk는 선택 필드다. 미선언 = nmos 최저·pmos 최고 전위 레일이고, 기본과 다른 연결(source 연결 등)만 선언한다. → O-174의 bulk = source는 O-188이 말한 "명시적으로 source쪽에 붙일 때"에 해당한다. **규칙과 충돌하지 않는다.**
- 재작성 범위 사실(원칙 8 용도 (2)): `graph/bulk_default.py`는 한 소자라도 기본 규칙을 쓰면 회로 전체의 채널 레일을 검사한다. erfc는 vcn·vcp에 채널이 닿아 `bulk_multi_domain`으로 정지한다. 그래서 erfc에서 '(나) 되돌림'은 '미선언'이 아니라 **명시적 bulk = vdd**를 뜻한다(옛 상태).
- spec(`erfc_ota.sizing_spec.json`)에는 bulk·vsb·M19~M21을 언급하는 항목이 0건이다(grep). 지문 불일치(o181_test_impact.md 94행)는 해시만의 문제다.

## 3. 물리·PDK 실현성

- **pmos bulk = source(레일 아닌 전위 0.7·1.1 V)**: p-기판 n-well 공정에서는 pmos마다 n-well을 따로 둘 수 있다. sky130 표준 구성이고 deep n-well이 필요 없다. 브리핑의 "nmos는 deep n-well 필요" 우려는 **해당 소자가 없어 적용되지 않는다**.
- 대가:
  - n-well 섬 2개(vcn·vcp)와 vdd well 사이 간격 규칙만큼 면적이 든다. 소자 3 µm × 1 µm에 비해 well 경계 여유가 더 크다. 수치는 PDK 선언에서 읽을 양이라 여기 박지 않는다(원칙 11).
  - n-well–p기판 용량·누설이 vcn·vcp에 붙는다. topology에서 vcn·vcp는 이상 레일이라 회로 동작에는 영향이 없다. 실제 칩에서는 바이어스 생성기 부하다(topology 밖).
  - 드레인–bulk 용량의 반대편이 vdd에서 vcn·vcp로 바뀐다. 둘 다 AC 접지라 소신호 효과는 같다.
- **엔진 VSB**: DEC-61 vsb = |V(s) − V(b)|를 노드전압에서 유도한다(`sizing/block_columns.py`, 봉인 6 `seal_bulk_reverse.py`).
  - bulk = source → VSB = 0. LUT 축의 원점이라 조회가 가장 정확하다.
  - bulk = vdd → M19 VSB = 1.1 V, M21 0.7 V. 다만 0 전류 소자라 dc_op 조회 대상이 아닐 수 있다. f_HP 조건용 g_ds 조회 자리는 2026-10-29 범위 밖이었다.
  - 봉인 6: bulk = source에서 VDS = 0이면 순바이어스 0이다. 통과한다.

## 4. 'bulk = vdd면 드레인 접합 누설로 VDS 이동' 주장의 물리 (재측정)

- 접합 방향: pmos p+ 드레인(≈0.7 V)과 n-well(vdd 1.8 V)은 **역바이어스 1.1 V**다(M21: 1.1 대 1.8 → 0.7 V 역). 역방향 누설은 n-well → p+ 드레인으로 흘러 드레인 노드에 전류를 주입한다(E: ibd ≈ −2.0 fA, 드레인 전위와 거의 무관).
- 그 노드의 다른 DC 경로는 채널 하나뿐이고 약반전이라 R이 1e14~1e17 Ω이다. 그래서 fA를 흘리려면 VSD가 수백 mV 필요하다. 주장의 메커니즘은 맞다.

**D. 부유 드레인 평형 V(d) − V(s) [V]** (results.txt D, 기하 1x = 2026-10-29와 같은 ad = 0.87p)

| 꼴 | bulk | 기하 | −40 °C | 27 °C | 85 °C | 125 °C |
|---|---|---|---|---|---|---|
| M19/M20 | vdd | 0 | +0.449 | +0.286 | +0.147 | +0.055 |
| M19/M20 | vdd | 1x | +0.268 | **+0.247** | +0.281 | +0.307 |
| M19/M20 | vdd | 2x | +0.270 | +0.272 | +0.312 | +0.342 |
| M21 | vdd | 0 | +0.219 | +0.058 | +0.002 | +0.000 |
| M21 | vdd | 1x | +0.038 | **+0.027** | +0.054 | +0.078 |
| M21 | vdd | 2x | +0.040 | +0.046 | +0.082 | +0.111 |
| 모두 | source | 0/1x/2x | 0.0000 | 0.0000 | 0.0000 | 0.0000 |

- 2026-10-29 값(+0.246, +0.026)을 독립 재현했다(27 °C, 1x).
- 새 사실: bulk = vdd 오프셋은 **온도와 접합 기하(레이아웃)에 따라 0~0.45 V로 바뀐다.** 기하가 0이어도 남는 것은 모델의 기하 무관 성분 때문이다(gmin 1e-18).
- 크기 판단: M5·M6은 cascode 게이트다. +0.25 V는 VCN 0.7 V의 36%이고, M3B·M4B VDS 헤드룸을 그만큼 바꾼다. 회로 동작점을 바꿀 만한 크기다. M21(+0.03 V, 최대 0.22 V)은 M7·M8 VSG를 그만큼 줄인다.
- 원문 0.18 µm(|Vthp| 더 작음)에서는 R_ch가 작아 오프셋이 µV급일 것으로 **추정**한다(모델 없음, 실측 아님). 원문 저자는 bulk = vdd로도 문제가 없었을 수 있다. 그러나 **엔진이 쓰는 PDK에서 VC = VE를 지키는 것은 bulk = source뿐**이다.

## 5. 대신호(새 측정) -- bulk = source의 대가

**E. M19 꼴 드레인 강제 DC**(S = 0.7, G = V_Z 0.4957, 27 °C): 드레인이 source 위로 올라갈 때 전체 전류 / 그중 접합 전류

| V(d) − V(s) | bulk = vdd I_d | bulk = source I_d | bulk = source 접합 ibd |
|---|---|---|---|
| +0.3 | −4.6e−16 A | 1.4e−10 A | 9.9e−12 A |
| +0.5 | 4.5e−11 | 4.7e−8 | 2.9e−9 |
| +0.7 | 1.3e−8 | 3.7e−6 | 8.4e−7 |
| +0.9 | 9.6e−7 | 2.2e−4 | 2.0e−4 |

- bulk = source는 드레인↑ 방향에서 전류가 약 1000배 크다. 주된 성분은 실효 source(드레인) 쪽에 걸린 순방향 body 바이어스 때문에 커진 채널 전류다. +0.9 V 이상에서는 순방향 접합(p+/n-well, 기판 쪽 기생 PNP 주입)이 지배한다.

**F. CBAT 승압 유지**(드레인 = 채널 + CBAT, 반대편 계단 dX, 27 °C). 0.5 µs 뒤 V(d) − V(s). 원문 1% 정착 0.473 µs(spec_source, p.15 Table 2) 근방이다.

| 꼴 | CBAT | dX | bulk = vdd | bulk = source |
|---|---|---|---|---|
| M19 | 0.1 pF | +0.4 | +0.436 | +0.395 |
| M19 | 0.1 pF | +0.8 | +0.683 | +0.432 |
| M19 | 1 pF | +0.4 | +0.404 | +0.400 |
| M19 | 1 pF | +0.6 | +0.603 | +0.517 |
| M19 | 1 pF | +0.8 | +0.763 | +0.525 |
| M19 | 10 pF | +0.8 | +0.795 | +0.631 |
| M21 | 1 pF | −0.8(유용 방향) | −0.791 | −0.791 |
| M21 | 1 pF | +0.8 | +0.556 | +0.393 |

- CBAT 값은 원문에 없다(topology value_farad null). 그래서 0.1/1/10 pF와 dX 0.2~0.8 V를 **스캔**했다. 설계값이 아니다.
- 유용 방향의 판독(연결 + 원문 p.7):
  - M19·M20: X↑ → M3B 전류↑ → n_m5s↓ → M3B가 선형 영역으로 갈 위험 → CBAT1이 M5 게이트를 올려 막는다. **드레인↑ 방향**이다.
  - M21: n_m7d↓ → M10 전류↑ → n_m10d↓ → CBAT2가 M7·M8 게이트를 내린다. **드레인↓ 방향**이다.
- 결과:
  - M21은 유용 방향에서 bulk 영향이 0이다.
  - M19·M20은 승압이 ≥ 0.5 V이고 CBAT가 작을 때 bulk = source가 승압을 0.15~0.4 V 깎는다.
  - 원문은 "the voltage at node X will be very high"(p.7, 대신호 시 X)와 "CBAT does not need to be excessively large"를 말한다. 그래서 이 영역은 원문 동작 범위 안일 수 있다(불확실 -- X 진폭 수치가 원문에 없다).

## 6. 대안 비교

| 안 | 물리 정합(DC) | 대신호(원문 기법) | 원문 정합 | PDK 실현성·대가 | O-188 관계 | 엔진(DR-1) | spec·test |
|---|---|---|---|---|---|---|---|
| **(가) 유지: M19·M20 b = vcn, M21 b = vcp** | VDS = 0 정확(온도·기하 무관, D) | M19·M20 승압 ≥ 0.5 V에서 감쇠(F). M21 유용 방향 무영향 | 정적 의도 "VC = VE"(p.7) 정확. 그림은 무기재 | n-well 섬 2개(deep n-well 불필요), well 간격 면적 | "명시적으로 source쪽" 예외 그대로 | DR-1 'bulk = source면 VDS = 0 묶음' 적용, 정지 없음 | 지문만 갱신(spec 항목 bulk 무관) |
| (나) 되돌림: 모두 b = vdd(명시) | VDS 오프셋 M19 +0.05~0.45 V, M21 ~0~0.22 V, 온도·레이아웃 의존(D). LUT로 예측 불가 | 승압 유지 가장 좋음(역 body 바이어스) | sky130에서 VC ≠ VE(의도 위반). 0.18 µm에서는 아마 무해(추정) | well 추가 없음 | 기본 규칙과 같은 값(erfc는 레일 4개라 미선언은 정지 → 명시 필요) | DR-1 정지(bulk ≠ source) → erfc 단계 A 정지(fail-closed) | 지문 원복 |
| (다) 소자별 혼합(M19·M20 = vdd, M21 = vcp 또는 그 반대) | 혼합 | M19·M20 승압 유지 + M21 정확 / 또는 반대 | 일부 위반 | well 1개 | 예외 일부 | 한쪽 정지 | -- |
| (라) kind별 | M19~M21이 모두 pmos라 **구분이 성립하지 않음** | -- | -- | -- | -- | -- | -- |

- ⚠ (나)는 원칙 6(물리 정합)·원칙 1(물리적으로 말이 안 되는 동작점 무의미)과 부딪힌다. 엔진이 정할 수 없는 누설이 동작점을 정하기 때문이다.
- ⚠ (가)의 대신호 손실은 엔진(DC/AC 손계산)이 보지 않는 양이다(원칙 3). 그래서 최종 판정은 오라클 과도로 해야 한다(원칙 2 E-1: front 점 합격은 oracle).
- (다)는 한쪽이 (나)의 결함을 그대로 갖고 DR-1 정지도 남아 이점이 없다.

## 7. 권고와 O-171

**권고: (가) O-174 유지.** 근거: DC 동작점 정확성(원문 명시 의도 + PDK·온도·레이아웃 무관), PDK 실현 가능(pmos 별도 n-well), O-188 예외 형식과 일치.

단 다음 두 가지를 붙인다.
1. 대신호 대가를 사용자에게 알린다(원래 취지와 다름 표지: O-174 근거에 대신호 손실이 없었다).
2. erfc 과도(slew/정착) 오라클 검증 때 bulk 두 경우를 비교하는 항목으로 남긴다.

spec 지문 갱신은 (가)에서 문제가 없다. spec 항목에 bulk 의존이 없다.

| O-171 칸 | 내용 |
|---|---|
| 물리 결정자 | 드레인 노드 KCL: 채널(약반전, I ∝ e^{(VSG−|Vth|)/nVT}(1 − e^{−VSD/VT})) + 드레인–bulk 접합(역방향 누설 또는 순방향 diode) + CBAT 변위전류. bulk = source면 접합이 채널과 병렬(0 V)이라 VDS = 0이 구조적이다. bulk = vdd면 누설 × R_ch가 VDS를 정한다. 대신호에서는 body 바이어스 부호가 채널 전도를 정한다 |
| 식·원문 | p.7 Fig.5 본문 "VC is equal to VE", "RL also can be realized using a transistor", "RC highpass filter to the gate of the cascode"; p.7 §3.2 "deep triode … active resistors"; p.8 Fig.6(3단자, pmos); p.9 Table 1 3/1 µm; p.13 0.18 µm. 로컬 PDF `chip-design-skills/skills/analog-gmid-design/assets/library/sources/erfc_ota__wu_2025/source.pdf` |
| SPICE 실측 | `o174_recheck/results.txt`: D(48점, bulk × 기하 × 온도), E(드레인 DC 쓸기), F(48점 과도, CBAT·dX 스캔). sky130 tt, ngspice-46 |
| 판정 | DC: (가) 맞음(높음). PDK 실현성: 맞음(높음, pmos). 대신호 영향: 불확실(전체 회로 X 진폭·CBAT 값 미정). 종합: **조건부 맞음** |

**더 잴 것 (불확실 칸 해소)**
- erfc 전체 회로 과도(대신호 계단, CL 70 pF)에서 bulk 두 경우의 SR·1% 정착 비교. 원문 바이어스가 sky130에서 M5·M7 가지를 붕괴시키는 문제(2026-10-29 한계 5절)가 있어 **spec 바이어스로 엔진이 낸 사이징 점**에서 재야 한다. 그래서 엔진 erfc 단계 A가 지나간 뒤에 할 수 있다.
- X·Y 노드 대신호 진폭 실측(이 값이 0.5 V 아래면 (가)의 대가는 사실상 0이다, F).

## 8. 관찰 (범위 밖, 수정 안 함)

- topology `_bulk_comment`에 옛 문장("0.18 um … PMOS bulk=vdd를 명시했다", "M19~M21 … 사용자 확인 필요")과 O-174 문장이 섞여 있다. 주석은 connectivity가 아니지만 topology 파일이라 사용자 대기열 판단 사항이다.

## 9. 사용자 질문 초안

> erfc_ota M19·M20 bulk = vcn, M21 bulk = vcp(O-174)를 다시 쟀습니다. 세 소자는 모두 pmos라 별도 n-well로 실현됩니다(deep n-well 불필요). bulk = source는 DC에서 VDS = 0을 정확히 지키고 원문 "VC = VE"(p.7)와 맞습니다. bulk = vdd는 sky130에서 M5·M6 cascode 게이트를 +0.05~0.45 V 옮기고, 그 크기는 온도·레이아웃에 달려 엔진이 예측할 수 없습니다. 다만 새로 잰 대가가 있습니다. bulk = source면 M19·M20의 CBAT 승압이 0.5 V를 넘을 때 0.5 µs 안에 0.15~0.4 V 샙니다(순방향 body·접합). M21은 유용 방향에서 영향이 없습니다.
> - (가) O-174 유지 + erfc 과도 오라클 검증 때 bulk 두 경우 SR·정착 비교 항목을 추가, spec 지문 갱신 진행 (Recommended)
> - (나) bulk = vdd로 되돌림 -- DC 오프셋 감수, DR-1에서 erfc 정지(fail-closed)
> - (다) 결정 보류, 전체 회로 과도 실측 뒤 결정(spec 지문 갱신도 보류)
