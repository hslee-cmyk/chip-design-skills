# TD-3 / CI-15 — 단일 출력 6회로의 '출력 기준 DC' 선택지 (제안 초안)

* 작성 2026-10-15, 읽기 전용 조사. spec·topology·엔진 파일은 고치지 않았다. 값 확정은 사용자 몫이다(CI-15, offset-trim design §18.1 TD-3).
* 대상: folded_cascode, ngcc_3stage_ff, nmcnr_amplifier, sf_pushpull_output_opamp, two_stage_ota, two_stage_ota_sf
* 실측 증거(엔진 코드는 그대로, 실행 출력만 저장): `wt/_drafts/engine/td3_probe/`
  * `probe_w3.py`·`probe_w3.out`: 출력 넷에 W3 목표가 없을 때와 있을 때의 쓰기 계획 비교
  * `stage_b_probe.py`·`*.stage_b.json`: 단계 A→B 진단 실행에서 나온 헤드룸 창. 회로 하나씩 순차로 돌렸고 탐색(find_front)은 돌리지 않았다.

---

## 0. 결정 전에 알아야 할 엔진 사실 (이 조사에서 새로 확인)

### F-1. `node_voltage_targets_v`는 '측정 기준'에 그치지 않고 출력 노드를 사이징에서 고정한다

* 같은 필드를 두 곳이 쓴다.
  * (1) 쓰기 계획 W3: `sizing/writer_plan.py:8, :150-151`에서 고정 노드 F가 된다.
  * (2) `metrics/offset_systematic.py:39-41`의 단일 출력 기준.
* W3 넷의 DC 값은 선언값 그대로 들어간다(`sizing/block_columns.py:565` `values[net] = float(c.fixed[net])`).
  * 그래서 단일 출력 계통 offset의 오차 V_dc(out) − 기준은 **구성상 0**이다.
  * `offset_sys_mv` = 0(분해능만 남음)이고, trim 1단계의 |V_sys,s|도 0이다.
* 뜻: 이 엔진은 W를 쓰기 좌표에서 유도한다. 그래서 출력이 기준값에 있도록 사이징하는 것이 곧 '그 출력 DC에서 계통 offset 0'이다.
  * 기준값 선택은 offset 수치가 아니라 **어느 출력 DC에서 증폭기를 바이어스·사이징하는가**를 정한다. 그 출력 DC에서 출력단 소자의 VDS·포화 여유와 trim 끝 코드의 포화 검사가 정해진다.
  * 목표가 없으면 출력 넷은 W4 자유 변수(탐색 θ)다. 목표를 선언하면 W4 차원 하나가 빠진다(실측 아래 표).
* trim 균형 풀이(offset-trim design §10.5)는 W3을 고정하지 않는다. 대신 V(out) = 기준을 균형식 하나로 쓴다. 그래서 봉인 점에서 δ = 0 균형 V_in ≈ 0이다.
* **원래 취지와 다를 수 있음**: CI-15 질문은 원래 'W3(목표 전압) 노드 목록'이었다(PENDING_USER_DECISIONS CI-15, design_spec_format §node_voltage_targets_v).
  * TD-3은 이것을 'offset 측정 기준'으로 쓴다. 한 값이 사이징 고정점과 측정 기준을 겸한다는 점을 결정 때 알고 있어야 한다.

| 회로 | 목표 없음: 출력 writer | 출력 W3 선언 시 (값 무관, 구조 실측) |
|---|---|---|
| folded_cascode | `out` = W4 자유 | W3. W4 {Y, out, vin_p} → {Y, vin_p} |
| ngcc_3stage_ff | `Vout` = W4 자유 | W3. W4 {Vinp, Vout} → {Vinp} |
| nmcnr_amplifier | `Vout` = RL `resistor_drop`(agnd에서 I_RL·RL) | **정지: `StructureUnresolvedError` `dc_resistor_cycle`(RL, Vout–agnd)** |
| sf_pushpull_output_opamp | `vout` = M22 `vgs_source`(N17에서) | W3. W4 {N20} → {} (N20이 vout에서 쓰임) |
| two_stage_ota | `OUT` = W4 자유 | W3. W4 {OUT, vin_p} → {vin_p} |
| two_stage_ota_sf | `vout` = M8 `vgs_source`(OUT에서) | W3. W4 {OUT, vin_p} → {vin_p} (OUT이 vout에서 쓰임) |

### F-2. nmcnr은 지금 엔진으로는 출력 기준을 선언할 수 없다

* RL(25 kΩ, Vout–agnd)의 양 끝이 모두 고정 노드가 된다. 저항을 종속시키는 규칙이 없어서 값과 무관하게 `dc_resistor_cycle`로 정지한다(`writer_plan.py` 정지 규칙, 계약 §3 3).
* 선언하려면 엔진 변경이 필요하고, 공유 엔진 코드라 **사용자 승인 대상**이다. 후보는 둘이다.
  * (가) 두 고정 노드 사이 저항은 전류 = ΔV/R인 고정 KCL 항으로 취급한다.
  * (나) offset 기준을 W3과 분리한 별도 필드로 둔다.

### F-3. 입력 공통모드가 SP-2 (c)인 5회로에서는 '입력 CM과 같은 값'을 숫자로 적을 수 없다

* 입력 DC가 `pending: SP-2`인 회로는 입력 CM이 W4 자유 변수 y_icm이다(design 41 §4.6 J-E). 숫자가 아니라 해마다 달라진다.
* '창 중앙값을 숫자로 선언하지 않는다(EP-4)'는 원칙이 있다.
* 그래서 (a) 기준 = 입력 CM을 spec만으로 표현하는 방법은 SP-2에 숫자를 주고 CI-15에 같은 숫자를 두 번 적는 것뿐이다. 같은 사실이 두 곳에 있게 되어 단일 정본 위반이고, J-E 결정(입력 DC는 환경 몫, 자유 변수)을 되돌린다.
* 원칙에 맞는 구현은 엔진 변경이다(승인 필요). 예: 출력 넷을 입력 공통모드 묶음에 '같은 DC' 엣지로 잇는 W2 규칙(기존 `input_tie`와 같은 종류). 그러면 V(out) = y_icm으로 쓰이고, 단위 이득 동작점에서 사이징된다.
* sf_pushpull은 입력 DC가 선언되어 있다(`agnd` 0.9 V). 그래서 (a)를 숫자로 적을 수 있다.

### F-4. 기준 차이가 입력 환산에 미치는 크기 = Δref / A_dm (선형 근사)

* 실제 사용 동작점(예: 단위 이득에서 V_out = V_icm)과 선언 기준이 Δref만큼 다르면, 사이징 점에서 잰 계통 offset은 실사용 offset과 약 Δref/A_dm만큼 다르다.
* 아래 표는 spec 이득 하한에서 구한 상한이다(Δref 100 mV당).

| 회로 | 이득 하한 (spec) | 100 mV당 입력 환산 차 |
|---|---|---|
| two_stage_ota, two_stage_ota_sf | 57 dB (two_stage_ota `gain_ss_db`, sf는 `value_from_file` 참조) | ≤ 0.141 mV |
| sf_pushpull_output_opamp | 65 dB | ≤ 0.056 mV |
| nmcnr_amplifier | 100 dB | ≤ 1.0 µV |
| ngcc_3stage_ff | 111 dB | ≤ 0.28 µV |
| folded_cascode | 결정 대기(SP-4) | 미정 |

* 이득이 큰 ngcc·nmcnr에서는 기준 선택의 영향이 offset보다 **헤드룸(출력단 포화)** 쪽에 집중된다.
* 57 dB 회로는 수백 mV 차이면 σ_in(mV 급)과 비교할 만한 크기가 된다.

### F-5. 단계 B 헤드룸 창은 지금 선택지를 가르지 못한다

* 실측 결과 6회로의 출력·입력 창이 모두 레일 근처까지 열려 있다(아래 표).
* 엣지 비용의 |VGS| 최솟값이 0으로 나온다(derivation의 `vgs:0.0`). 그래서 창은 VDSAT 최솟값(약 0.04 V)만 뺀 사실상 레일 범위다.
* design 41 §4.6의 제안서 추정(pfet VSG 0.68~1.02 V로 창이 좁음)과 다르다. 원인 조사는 이 card 범위 밖이라 하지 않았다. 확인하지 못한 것에 적어 둔다.

| 회로 | 출력 창 [lo, hi] V | 입력 창 [lo, hi] V | 버퍼 창 |
|---|---|---|---|
| folded_cascode | out [0.076, 1.721] | [0.038, 1.8] | — |
| ngcc_3stage_ff | Vout [0.038, 1.76] | [0.0, 1.76] | — |
| nmcnr_amplifier | Vout [0.038, 1.76] | [0.0, 1.76] | — |
| sf_pushpull_output_opamp | vout [0.04, 1.76] | [0.038, 1.8] | Y [0.076, 1.721] |
| two_stage_ota | OUT [0.038, 1.76] | [0.038, 1.8] | — |
| two_stage_ota_sf | vout [0.038, 1.76] | [0.038, 1.8] | OUT [0.038, 1.76] |

---

## 1. 회로별 사실

| 회로 | 레일 (supplies_v) | 입력 DC (spec) | 출력 넷 / 부하 | 출력 관련 spec 제약 | 기존 노드 목표 |
|---|---|---|---|---|---|
| folded_cascode | vdd 1.8, gnd 0 | pending SP-2 → y_icm | `out` / CL 1 pF → gnd | 없음(gain·GBW·PM pending) | pending CI-15 |
| ngcc_3stage_ff | vdd 1.8, gnd 0 | pending SP-2 | `Vout` / CL 10 pF → gnd | `icmr_v ≥ 0.6`(입력 창 폭) | pending CI-15 |
| nmcnr_amplifier | vdd 1.8, vss 0, agnd 0.9 | pending SP-2 | `Vout` / CL 100 pF ∥ **RL 25 kΩ → agnd** | `swing_out_v ≥ 0.5`(폭), `icmr_v ≥ 0.5` | pending CI-15 |
| sf_pushpull_output_opamp | vdd 1.8, vss 0, agnd 0.9 | **`net: agnd` = 0.9 V**(U-25) | `vout` / CL 1 pF → agnd | `rout_ss_ohm ≤ 1000`, `icm_margin_v ≥ 0` | pending CI-15 |
| two_stage_ota | vdd 1.8, gnd 0 | pending SP-2 | `OUT` / CL 3 pF → gnd | 없음 | pending CI-15 |
| two_stage_ota_sf | vdd 1.8, gnd 0 | pending SP-2 | `vout`(NMOS 팔로워 M8 source) / CL 3 pF → gnd | `rout_ss_ohm ≤ 1000` | pending CI-15 |

* 출력 스윙 제약은 nmcnr의 `swing_out_v ≥ 0.5` 하나뿐이다. 이것은 창의 **폭**이고 위치(중심)는 선언되어 있지 않다.
* 입력쌍 극성(topology 판독):
  * NMOS 입력: folded M1/M2, sf_pushpull M1/M2, two_stage M1/M2, two_stage_sf M1/M2
  * PMOS 입력: ngcc M1/M2, nmcnr M102/M103

### 원문이 쓰는 측정 구성

| 회로 | 원문 | 측정 구성 / 출력 DC 명시 | 위치 |
|---|---|---|---|
| two_stage_ota, folded_cascode | Maloberti, Layout of Analog CMOS IC Part 2 (2004) — 웹: 저자 게시처 찾지 못함(제3자 재게시 slideshare layout02-1) | 소자 폭만 있음. 전원·DC·측정 구성 없음("Compensation network and bias are missing") | `assets/library/sources/two_stage_ota+folded_cascode__maloberti_2004/source.pdf` p.28(2단), p.34(folded) |
| ngcc_3stage_ff | Lee et al., JSTS 7(1):20-27, 2007 — https://doi.org/10.5573/JSTS.2007.7.1.020 | VDD 1.2 V(0.18 µm), PMOS 입력, ICMR ≥ VDD/3. Fig. 5 계단 응답에서 입력과 출력이 같은 준위로 정착해 단위 이득 구성으로 보인다(본문에 구성 명시 없음). **원문 값(그림 판독 근사)**: 입력 계단 약 0.14 → 0.54 V, 출력 약 0.54 V 정착 | `ngcc_3stage_ff__lee_2007/source.pdf` PDF p.6 = 저널 p.25 Fig. 5; ICMR 식(9) PDF p.5 = 저널 p.24 |
| nmcnr_amplifier | Leung, Mok, Ki, ICECS 1999 pp.599-602 — IEEE Xplore 링크 찾지 못함 | 전원 ±1 V, 부하 100 pF ∥ 25 kΩ(Fig. 3에서 CL은 접지 기호, 레일 중간). SR·Ts는 "unity-gain configuration with a 0.5V step input". **출력 DC 값은 명시 없음**. 부하가 접지 기준이라 단위 이득 출력 DC = 입력 DC = 접지(0 V, 레일 중간)로 읽히지만 추론이다 | `nmcnr_amplifier__leung_1999/source.pdf` PDF p.3 = 저널 p.601 §5 본문; PDF p.4 = p.602 Fig. 3·Table 1 주석 |
| sf_pushpull_output_opamp | Allen, Lecture 26 Buffered Op Amps (6/25/14) — https://aicdesign.org/wp-content/uploads/2018/08/lecture26-140625.pdf | VDD/VSS 분할 전원, Cc·CL이 접지 기호(레일 중간)에 연결. DC 값·측정 구성 없음. topology 결정 U-25: "Cc·CL·입력 공통모드 기준은 agnd" | `pushpull_follower_buffer+sf_pushpull_output_opamp+two_stage_ota_sf__allen_2014/source.pdf` p.6 (Page 26-6, Fig. 7.1-1) |
| two_stage_ota_sf | 같은 강의 | 단일 전원 VDD·접지, DC 값 없음 | 같은 PDF p.5 (Page 26-5, 060706-03) |

---

## 2. 선택지와 권고

공통 정의:
* (a) 입력 공통모드와 같은 값(단위 이득 피드백의 정상 동작점)
* (b) 레일 중간 (VDD + VSS)/2
* (c) 출력 스윙 spec 구간의 중심
* (d) 원문 측정 구성 값
* (e) 엔진 변경형(승인 필요)

영향 열의 두 줄:
* offset: 계통 offset = 출력 오차/A_dm의 뜻. W3 선언 시 수치는 0이고 남는 차이는 F-4의 실사용 괴리다.
* trim: 균형 V(out) = 기준과 끝 코드 포화 검사.

### 2.1 sf_pushpull_output_opamp

| 선택지 | 값 | 근거 | offset 영향 | trim 영향 |
|---|---|---|---|---|
| (a) = 입력 CM | 0.9 V | spec `input_dc = net agnd`(supplies 0.9) | 단위 이득 동작점과 일치. 괴리 0 | 균형이 실사용 동작점과 같다 |
| (b) 레일 중간 | 0.9 V | (1.8 + 0)/2 = agnd | (a)와 같음 | 같음 |
| (c) 스윙 중심 | 없음 | 스윙 제약 없음 | — | — |
| (d) 원문 | 레일 중간(접지), 값 표기 없음 | Allen p.26-6 CL·Cc → 접지 | (a)와 같음 | 같음 |

**권고: `vout` = 0.9 V (agnd).** 세 근거(선언 입력 DC, 레일 중간, 원문 접지 기준)가 모두 같은 점을 가리키고 F-3 제약도 없다.
* 남는 문제가 있다. 숫자 0.9는 `supplies_v.agnd`의 사본이라 레일이 바뀌면 따라가지 않는다(상수 원칙). node 목표 스키마는 `value_v`만 받는다. `{"net": "agnd"}` 형식 참조를 넣으려면 authoring 스키마 변경이 필요하고, 이것은 승인 대상이다.
* W3 선언 뒤 단계 B와 봉인 실현가능성은 돌려 보지 않았다(F-1 표의 구조 실측만 했다).

### 2.2 nmcnr_amplifier

| 선택지 | 값 | 근거 | offset 영향 | trim 영향 |
|---|---|---|---|---|
| (a) = 입력 CM | y_icm (숫자 아님) | SP-2 (c) | 단위 이득 정합. F-3 때문에 spec만으로는 불가 | 실사용 일치 |
| (b) 레일 중간 = agnd | 0.9 V | supplies `agnd` 0.9, RL이 agnd로 귀환 → 출력 DC 부하 전류 0 | 100 dB라 실사용 괴리 ≤ 1 µV/100 mV(무시 가능) | 출력단 포화는 0.9 V 기준으로 판정 |
| (c) 스윙 중심 | 없음 | `swing_out_v`는 폭만 선언. 중심은 엔진 산출값이라 숫자 선언 불가(EP-4) | — | — |
| (d) 원문 | 접지(레일 중간)로 읽힘, 명시 없음 | Leung p.601·602: ±1 V, 부하 접지, 단위 이득 측정 | (b)와 같음 | 같음 |

**권고: 값은 (b) 0.9 V(agnd)로 정한다. 다만 선언은 F-2 엔진 변경 승인 뒤에 한다.**
* 이유: RL이 agnd에 묶여 있으므로 출력 DC ≠ agnd이면 RL이 (V_out − 0.9)/25 kΩ의 DC 전류를 끌어간다. agnd만이 부하를 DC로 중립에 두는 점이다. 원문 측정 구성과도 같고, 이득이 커서 (a)와의 offset 차이는 무시할 수 있다.
* 지금 spec에 적으면 단계 A 쓰기 계획이 `dc_resistor_cycle`로 정지한다(실측). 그때까지 nmcnr의 trim은 후보표까지만 나온다.
* 확인 필요 1: design 41 §4.6의 옛 추정(L ≥ 0.5 µm에서 Vin,max가 agnd보다 0.26~0.48 V 낮음)이 맞다면 0.9 V는 PMOS 입력 창 밖이다. 이 경우 같은 칩을 단위 이득 버퍼로 쓰면 0.9 V가 될 수 없다.
* 확인 필요 2: 현재 단계 B 창 실측(F-5)은 이것을 판별하지 못한다.

### 2.3 two_stage_ota

| 선택지 | 값 | 근거 | offset 영향 | trim 영향 |
|---|---|---|---|---|
| (a) = 입력 CM | y_icm (숫자 아님) | SP-2 (c) | 단위 이득 정합. spec만으로는 SP-2·CI-15에 같은 숫자를 이중 기입해야 함(F-3) | 균형이 실사용 동작점 |
| (b) 레일 중간 | 0.9 V | (1.8 + 0)/2 | 57 dB라 실사용 V_icm과의 차 100 mV당 ≤ 0.14 mV(F-4) | M6(pmos)·M7(nmos) 출력단 VDS가 대칭이라 끝 코드 포화 여유가 양쪽으로 같다 |
| (c) 스윙 중심 | 없음 | 스윙 제약 없음 | — | — |
| (d) 원문 | 없음 | Maloberti p.28: DC 정보 없음 | — | — |
| (e) 엔진: out ↔ 입력 CM 같은 DC 엣지 | V(out) = y_icm | F-3 | 정의상 실사용 정합, 이중 기입 없음 | 실사용 일치 |

**권고: 원칙상 (e)이고, 엔진 변경 전 잠정안은 (b) 0.9 V.**
* 57 dB에서는 기준이 수백 mV 어긋나면 σ_in과 비교할 만한 차이가 생긴다. 그래서 단위 이득 정합을 구조로 보장하는 (e)가 offset 정의에 맞다.
* (e)는 공유 엔진 변경이라 승인이 필요하다.
* 잠정안 (b)는 출력단 대칭 헤드룸이라는 근거가 있고 숫자는 supplies에서 유도된다. 다만 사본이 생긴다(2.1과 같은 문제).

### 2.4 two_stage_ota_sf

| 선택지 | 값 | 근거 | offset 영향 | trim 영향 |
|---|---|---|---|---|
| (a) = 입력 CM | y_icm | SP-2 (c) | 2.3과 같음 | 같음 |
| (b) 레일 중간 | 0.9 V | (1.8 + 0)/2 | 2.3과 같음(57 dB) | **위험**: vout = 0.9 V이면 OUT = 0.9 + VGS8. M8은 NMOS 팔로워이고 bulk = gnd라 vsb = 0.9 V로 체효과가 있다. OUT ≤ VDD − VSDsat6이어야 하는데, VGS8(체효과 포함) + VSDsat6 > 0.9 V이면 M6이 포화를 벗어난다. 값은 확인하지 못했다 |
| (c) 스윙 중심 | 없음 | 제약 없음 | — | — |
| (d) 원문 | 없음 | Allen p.26-5: 값 없음 | — | — |
| (e) 엔진 | V(vout) = y_icm | F-3 | 정합 | 정합 |

**권고: 원칙상 (e).** 잠정 숫자를 쓰더라도 (b) 0.9 V는 위 헤드룸 확인 전에는 권하지 않는다.
* 팔로워 레벨시프트 때문에 vout의 실현 가능 상한은 VDD − VSDsat6 − VGS8(vsb = vout)이다.
* 숫자를 정해야 한다면 엔진의 출력 창 상한(현재 F-5 때문에 판별력 없음)을 고친 뒤 그 창 안에서 사용자가 고른다.

### 2.5 folded_cascode

| 선택지 | 값 | 근거 | offset 영향 | trim 영향 |
|---|---|---|---|---|
| (a) | y_icm | SP-2 (c) | 정합, spec 단독 불가 | 정합 |
| (b) | 0.9 V | (1.8 + 0)/2 | 이득 미정(SP-4)이라 괴리 크기 미정 | 출력 캐스코드 스택(M10·M8 / M6·M3) 위아래 VDS 합이 대칭 |
| (c) | 없음 | — | — | — |
| (d) | 없음 | Maloberti p.34: DC 정보 없음 | — | — |
| (e) | V(out) = y_icm | F-3 | 정합 | 정합 |

**권고: 원칙상 (e), 잠정안 (b) 0.9 V.**
* 캐스코드 출력은 위아래로 VDSAT 두 개씩을 쌓으므로 레일 중간이 양쪽 포화 여유를 같게 한다.
* 이득이 SP-4 대기라 F-4 괴리 크기를 말할 수 없다.

### 2.6 ngcc_3stage_ff

| 선택지 | 값 | 근거 | offset 영향 | trim 영향 |
|---|---|---|---|---|
| (a) | y_icm | SP-2 (c), PMOS 입력(창이 아래쪽) | 정합, spec 단독 불가 | 정합 |
| (b) | 0.9 V | (1.8 + 0)/2 | 111 dB라 괴리 ≤ 0.28 µV/100 mV(무시 가능) | class-A 출력단(M12 pmos / M13·M14·M7 nmos) VDS 대칭 |
| (c) | 없음 | `icmr_v`는 입력 창 폭이지 출력이 아님 | — | — |
| (d) 원문 값 | 약 0.54 V @ VDD 1.2 V (그림 판독) | Lee 2007 Fig. 5 (저널 p.25) | 1.8 V 재설계로 옮기는 환산 규칙이 원문에 없다. 그대로 쓰는지는 사용자만 정한다 | — |
| (e) | V(Vout) = y_icm | F-3 | 정합 | 정합 |

**권고: (b) 0.9 V.**
* 이득이 매우 커서 단위 이득 동작점과의 offset 차이는 µV 이하이고, 남는 쟁점은 출력단 헤드룸뿐이다. 이때는 레일 중간이 출력단 VDS를 대칭으로 둔다.
* (d) 0.54 V는 1.2 V 공정 값이고 PMOS 입력 창이 낮은 쪽이라는 정보에 가깝다. 출력 기준으로 그대로 옮길 근거는 없다.
* 이 회로는 단계 A가 `review_needed`라(기준선과 같음) 단계 B가 진단 모드로만 돈다.

---

## 3. 요약표

| 회로 | 레일 | 입력 CM | 선택지 (값) | 권고 |
|---|---|---|---|---|
| sf_pushpull_output_opamp | 1.8 / 0 / agnd 0.9 | 0.9 V(선언) | (a) = (b) = (d) 0.9 | **0.9 V** (spec만으로 가능) |
| nmcnr_amplifier | 1.8 / 0 / agnd 0.9 | SP-2 (c) | (a) y_icm, (b) 0.9 = agnd, (d) 접지 추론 | **0.9 V. 단 F-2 엔진 변경 승인 전에는 선언 불가** |
| ngcc_3stage_ff | 1.8 / 0 | SP-2 (c) | (a) y_icm, (b) 0.9, (d) 원문 약 0.54 V@1.2 V | **0.9 V** |
| two_stage_ota | 1.8 / 0 | SP-2 (c) | (a), (b) 0.9, (e) | **(e) 승인 필요, 잠정 0.9 V** |
| folded_cascode | 1.8 / 0 | SP-2 (c) | (a), (b) 0.9, (e) | **(e) 승인 필요, 잠정 0.9 V** |
| two_stage_ota_sf | 1.8 / 0 | SP-2 (c) | (a), (b) 0.9(헤드룸 위험), (e) | **(e) 승인 필요. 0.9 V는 헤드룸 확인 전 비권고** |

사용자 결정 항목:
1. 위 6개 값
2. F-1 이중 역할(사이징 고정 + 측정 기준)을 그대로 둘지
3. F-2 엔진 변경 (가)/(나)
4. F-3 (e) 엔진 규칙 추가 여부
5. 레일 참조형 node 목표(`{"net": "agnd"}`) 스키마 확장 여부

## 4. 확인하지 못한 것

* W3 선언 후 단계 B와 봉인 실현가능성(쓰기 계획 구조만 실측). 특히 sf_pushpull과 two_stage_ota_sf의 팔로워 체인.
* F-5: 엣지 비용의 |VGS| 최솟값이 0으로 나오는 원인. 그 때문에 단계 B 헤드룸 창이 설계 41 §4.6 추정보다 훨씬 넓다. 엔진 결함인지 정의대로인지 판정하지 않았다.
* nmcnr PMOS 입력 창이 0.9 V를 포함하는지(옛 제안서 추정은 미포함, 현 실측은 판별 불가).
* two_stage_ota_sf에서 vout = 0.9 V일 때 VGS8(vsb 0.9 V) + VSDsat6 값(LUT 미조회).
* ngcc Fig. 5 준위(0.14 / 0.54 V)는 그림 눈금 판독 근사다. 본문에 단위 이득 구성이라는 명시가 없다.
* nmcnr 원문의 출력 DC 값(명시 없음, 접지 기준은 추론).
* folded_cascode 이득(SP-4 대기)이라 F-4 크기를 정할 수 없다.
