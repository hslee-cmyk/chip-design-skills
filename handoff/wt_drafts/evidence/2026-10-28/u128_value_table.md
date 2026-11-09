# U-128 SP-2 값표 -- library 7회로 `input_dc`·`offset_sys_mv` 후보 (분석, 읽기 전용)

- 작성: 2026-10-28, 분석 agent (오케스트레이터 위임 O-167 (b)). 코드·spec은 고치지 않았다. 반영은 card SF-1 data 커밋에서 한다.
- 기준 트리: `wt/integ-it12` (d759838a = master 9d153f2f 병합본). 아래 `E/` = `wt/integ-it12/skills/analog-gmid-design/gmid_engine`, `L/` = `.../assets/library`, `S/` = `L/sources`.
- 회로 해석(입력 위치·입력쌍 종류)은 topology `netlist` 연결과 원문만으로 했다. `device_roles`·`sizing_roles`·`symmetry` 같은 태그는 근거로 쓰지 않았다.

## 0. 판단 전에 확인한 사실 (코드·기록 실측)

| # | 사실 | 출처 |
|---|---|---|
| F1 | `input_dc` 꼴은 정확히 넷 중 하나다: `pending`, `{"net": 레일}`(topology `supply_nets` 안이어야 함), `{"value_v": V}`(레일 전압 범위 안), `{"engine": true}`(W4 자유 변수, '요구 입력 공통모드'로 보고). `value_v`에는 참조 꼴이 없다. | `E/authoring/spec_input_dc.py:1-59` |
| F2 | `net`·`value` 꼴이면 `input_dc_v`가 숫자가 되고, **모든 입력 방향 포트 넷이 그 값으로 고정**된다(`fixed[net] = input_dc_v`). 그래서 두 입력이 같은 DC를 받는다. `engine`·`pending`이면 None이라 고정하지 않는다. | `E/sizing/dc_inputs.py:28-33`, `E/sizing/kernel_fields.py:50-54` |
| F3 | `pending`이나 `engine`일 때는 입력 포트 W4 뿌리가 하나뿐이다(y_icm). 다른 입력은 별도 writer가 쓰므로 두 입력이 묶이지 않는다. 계획은 J-E SP-2 (c)를 "두 입력을 한 값으로 묶지 않아 비대칭을 못 막음"으로 적는다. | `E/sizing/block_columns.py:727-745`, 계획 U-128 행(`docs/01-plan/features/gain-budget-gmid-sizing.plan.md:2465`) |
| F4 | as-built `offset_systematic`은 출력이 단일이면 spec `node_voltage_targets_v`에서 출력 기준을 찾는다. 없으면 `reference_undeclared`(fail-closed)를 낸다. 차동 출력이면 V(p) − V(n)을 쓴다. 7회로 모두 `node_voltage_targets_v = {"pending": "CI-15"}`이다. | `E/metrics/offset_systematic.py:32-41`, 각 `L/<회로>.sizing_spec.json` |
| F5 | 계획 DEC-23은 출력 기준 선언을 세 종류로 둔다: (값) `node_voltage_targets_v`, (넷), (입력 추종). 단일 출력에 선언이 없으면 정의 불능이고 엔진은 기준을 추론하지 않는다(O-53 B3). 상한 규칙은 '계통 ≤ 랜덤 예산'(`value_from_constraint: offset_in_sigma_mv`)이다. | 계획 :223 DEC-23 |
| F6 | `value_from_constraint`는 **같은 파일에 선언된 제약 값**만 가리킨다. 계산된 metric 값을 가리키는 꼴은 없다. | `E/authoring/spec_refs.py:1-6`, `E/authoring/spec_constraints.py:6-10` |
| F7 | `offset_in_sigma_mv`와 `offset_excess`는 같은 graph 결과 `OffsetAnalysis`의 두 칸(`sigma_in_mv`, `excess`)이다. 절대 σ 선언(`offset_in_sigma_mv`)은 current_reuse에만 있다. 나머지 다섯 회로(two_stage·two_stage_sf·folded·nmcnr·ngcc)는 비율 가드 `offset_excess ≤ √2`만 있고, common_gate에는 offset 제약이 하나도 없다. | `E/metrics/registry.py:56-58`, 각 spec constraints |
| F8 | **공급 구성 원칙(O-74, 사용자 2026-10-21)**: 원문이 dual이면 원래 접지를 agnd로 옮긴다. 원래 접지에 닿던 것(입력 DC·공통모드 기준 포함)도 agnd로 간다. **nmcnr = dual이고 "입력 DC 기준 = agnd -- SP-2 결정 때 원칙 적용"**이라고 적혀 있다. 원문이 single이면 중간 rail을 만들지 않고 "원문에 없는 rail·측정 조건을 관례로 덧붙이지 않"는다. single로 판정된 회로는 folded·two_stage_ota(Maloberti), current_reuse·ngcc·common_gate·two_stage_ota_sf다. | `wt/_drafts/user_decisions.md:695` (O-74) |
| F9 | 선례: pushpull·sf_pushpull은 `input_dc: {"net": "agnd"}`(U-25·U-39)를 쓰고, sf에는 `icm_margin_v ≥ 0`(J-E)이 함께 있다. 두 회로의 agnd는 수동소자(CL·Cc) 단자에 쓰이는 중간 rail이다. | `L/sf_pushpull_output_opamp.sizing_spec.json:22-28,146`, `L/*.topology.json` `_supply_nets_comment` |
| F10 | H 판정에서 엔진이 고른 입력은 두 입력 사이에 차이가 있었다. two_stage H0r: vin_n 1.393 V, vin_p 1.074 V(−324 mV). folded: +71/−118 mV. nmcnr: −141 mV. two_stage_sf: +27 mV. common_gate는 단일 입력이라 0이다. | `wt/_cmp_pilot/H/judge/res/raw_*.json` `.case`, `h_judgment.md:378` |

## 1. 회로별 값표

확신도: 상(연결과 원문, 또는 사용자 기록이 직접 뒷받침) / 중(물리 유도는 성립하지만 sizing에 따라 여유가 좁을 수 있음) / 하.

### 1-1. `input_dc`

| 회로 | 입력 (연결 근거) | 권고 꼴·값 | 유도 | 출처 | 확신도 |
|---|---|---|---|---|---|
| **nmcnr_amplifier** | `Vin_p`/`Vin_n` = PMOS M103/M102 게이트이고, 꼬리 M101은 vdd에서 온다. PMOS 입력쌍 | `{"net": "agnd"}` (= supplies_v agnd 0.9 V) | O-74: 원문이 dual(±1 V)이므로 원래 접지 0 V를 agnd로 옮기고 입력 DC 기준도 agnd로 둔다. 선례(pushpull·sf)와 같은 꼴이다. 물리 확인: PMOS 입력의 창 = [V(NodeF) − \|Vthp\|, vdd − Vsd(M101) − \|VGS102\|]. H 판정 SPICE 창 [0.15, 1.0] V가 0.9를 포함한다(여유 0.1 V). | O-74(`user_decisions.md:695`); topology supply_nets `[vdd, vss, agnd]`; spec supplies_v agnd 0.9; `h_judgment.md:253`; 원문 Leung 1999 Table 1(PDF p.4, `S/nmcnr_amplifier__leung_1999/source.pdf`, 웹 링크 찾지 못함)은 unity-gain 구성에서 측정했다(paper.md:254,374) -- 교차 확인만 | **상** |
| **current_reuse_telescopic_ota** | `Vip`/`Vim` = PMOS M1a/M1b 게이트(소스 Vx, vdd 쪽)와 NMOS M4a/M4b 게이트(소스 Vy, gnd 쪽)를 **함께** 구동한다. 상보 입력(current reuse) | `{"value_v": 0.9}` | 상보 쌍의 입력 창 = [V(Vy) + VGS(M4), V(Vx) − \|VGS(M1)\|]. 위·아래 꼬리 Vds와 n/p VGS가 대칭이면 창 중심이 (vdd + gnd)/2 = 0.9 V다. O-74 single 규칙 "기준은 원문대로"와도 맞다: 원문 DC 동작점에서 입력 DC = 0.2998 + 0.6002 = 1.8 − 0.2603 − 0.6397 = **0.900 V**(같은 1.8 V 공급의 VDD/2, 그림 숫자에서 다시 계산). 이미 있는 `icm_margin_v ≥ 0`(spec :255-262)이 이 선언으로 켜진다. | 원문 Xie & Chen 2019 Fig. 6(b) p.6(`S/current_reuse_telescopic_ota__xie_chen_2019/source.pdf`, 렌더 `images/p06_2.png` -- 이 worktree에는 없으므로 skill 폴더에서 `python tools/pdf_to_md.py ensure`. 웹 링크 찾지 못함). 원문 Table I p.1의 ICMR [576.5, 900.1] mV는 원문 sizing 결과라 값 근거로 쓰지 않았다. | **상~중** (값은 상. 원문 sizing에서는 0.9가 창 위 끝이었다. 엔진 sizing에서는 `icm_margin_v`가 판정한다) |
| **two_stage_ota** | `vin_p`/`vin_n` = NMOS M2/M1 게이트, 꼬리 M5는 gnd로 간다. NMOS 입력쌍 | **사용자 확인 U1** -- 기본안 (A) `{"value_v": 0.9}`, 대안 (B) 아래 | 원문(Maloberti 2004 layout 강의 p.28-33)에는 입력 DC가 없다. O-74 single 규칙상 관례값을 덧붙일 수 없다. 물리 유도: spec 되먹임 선언이 β = 1 루프이므로(feedback 선언 record) 사용 구성에서 V_in,DC = V_out,DC다. 단일 출력의 대칭 스윙을 최대로 하는 출력 DC ≈ (vdd + Vov,n − Vov,p)/2이고, 1차로 vdd/2다. 입력 창 [VGS1 + Vds5, vdd − \|VGS3\| + Vth1] ≈ [0.75, 1.5] V(손계산 추정) 안에 들어간다. CMP-1 armA가 0.9 V(AI 가정)로 SPICE를 통과한 적이 있다(교차 확인만). | `cmp1_pilot_judgment.md:30`; `S/two_stage_ota+folded_cascode__maloberti_2004/source.pdf` p.28(웹: 저자 게시처 찾지 못함) | 중 |
| **two_stage_ota_sf** | two_stage와 같은 NMOS 입력쌍(M1/M2). 출력 vout은 NMOS 소스 팔로워 M8의 소스다 | **사용자 확인 U1** -- two_stage와 같은 값. spec이 two_stage를 `value_from_file`로 상속하므로 정본 꼴을 맞춘다 | 유도는 two_stage와 같다. ⚠ β = 1로 쓰면 vout = vin이어야 한다. vout 상한 ≈ vdd − Vov6 − VGS8(몸체 효과 포함) ≈ 0.85~0.9 V(손계산 추정)라 0.9 V는 **팔로워 출력 범위 끝**이다. input_dc만 선언하면 출력이 묶이지 않아 엔진 풀이는 가능하다. 출력 기준을 (입력 추종)으로 두면 여유가 거의 없다. | Allen 2014 Lecture 26 p.26-5(`S/pushpull_follower_buffer+sf_pushpull_output_opamp+two_stage_ota_sf__allen_2014/source.pdf`, [aicdesign.org lecture26](https://aicdesign.org/wp-content/uploads/2018/08/lecture26-140625.pdf)) -- 입력 DC 없음 | 중~하 |
| **folded_cascode** | `vin_p`/`vin_n` = NMOS M2/M1 게이트, 꼬리 M11은 gnd로 가고, 드레인 X/Y는 PMOS M3/M4로 접힌다. NMOS 입력쌍 | **사용자 확인 U1** -- two_stage와 같은 기본안 | 원문에 입력 DC가 없다. 창 ≈ [VGS1 + Vds11, ~vdd](접힘이라 위쪽은 레일까지)이므로 0.9 V는 **창 아래 끝 쪽**이다(여유 ~0.1~0.15 V, 손계산 추정). armA는 1.0 V(AI 가정), H 엔진은 1.06~1.23 V를 골랐다. 성능 spec(SP-3/4/5)이 없어 sizing이 극소 전류로 가는 점은 별도 문제다. | `S/two_stage_ota+folded_cascode__maloberti_2004/source.pdf` p.34-38; `cmp1_pilot_judgment.md:30`; raw_folded_cascode.H0r.* | 중 |
| **ngcc_3stage_ff** | `Vinp`/`Vinn` = PMOS M2/M1 게이트, 꼬리 M0은 vdd에서 오고 부하는 NMOS 미러 M3/M4. PMOS 입력쌍 | **사용자 확인 U1** -- two_stage와 같은 기본안 | 원문 공급은 1.2 V single이고 입력 DC는 없다. 원문 Fig. 5 step은 unity-gain 구성이다(paper.md:1663-1666, β = 1과 맞음). PMOS 입력의 창 상한 = vdd − Vds0 − \|VGS1\|. 구조가 같은 nmcnr의 SPICE 창 상한 1.0 V로 보면 0.9 V는 **창 위 끝 쪽**이다(여유 ~0.1 V). 선언된 `icmr_v ≥ 0.6`(창 폭)과 함께 sizing이 맞춰야 한다. | Lee 2007 Fig. 3·5, Table 4(`S/ngcc_3stage_ff__lee_2007/source.pdf` PDF p.5-6, [doi:10.5573/JSTS.2007.7.1.020](https://doi.org/10.5573/JSTS.2007.7.1.020)); spec icmr_v ≥ 0.6 | 중 |
| **common_gate_amplifier** | 단일 입력 `vin` = CG 소자 M2의 소스 = 전류원 M1의 드레인. 게이트는 바이어스 VNBias2. 입력쌍 없음 | `{"engine": true}` | 전압 구동 CG의 입력 DC는 바이어스로 정해진다(V_in = VNBias2 − VGS2). 원문 Allen p.20-2도 VOUT(min) ≈ VON1 + VON2처럼 바이어스 식으로 적고 고정 입력 전압은 없다. 입력이 하나라 "두 입력을 묶지 못하는" J-E (c)의 결함이 생기지 않는다. 엔진이 고른 값을 '요구 입력 DC'로 보고하는 것이 원문 구성과 같다. 값을 박으면(예: 0.9) VNBias2 ≈ 1.5 V가 강제되고 출력 범위가 [~1.0, ~1.65] V로 좁아진다(물리적으로 불리, 근거 없는 상수). | Allen 2014 Lecture 20 p.20-2 그림 060609-01(`S/common_gate_amplifier__allen_2014/source.pdf`, [aicdesign.org lecture20](https://aicdesign.org/wp-content/uploads/2018/08/lecture20-140624.pdf)); `E/authoring/spec_input_dc.py:5` | 중~상 |

### 1-2. `offset_sys_mv`

| 회로 | 권고 | 꼴·유도 | 근거 | 확신도 |
|---|---|---|---|---|
| **current_reuse_telescopic_ota** | **유지(이미 선언)** | `{"metric": "offset_sys_mv", "op": "<=", "value_from_constraint": "offset_in_sigma_mv"}`(3.3 mV 선언 참조). 출력이 차동이라 기준 = V(p) − V(n) = 0(DEC-23 기본)이므로 정의된다. input_dc를 선언하면 성분 (1)(봉인점 입력 차)이 0이 되고, 판정은 성분 (2)·(3)이 맡는다. | spec :236-243, DEC-23 | 상 |
| **two_stage_ota, two_stage_ota_sf, folded_cascode, nmcnr_amplifier, ngcc_3stage_ff** | **기본안: 이번 SF-1에서는 걸지 않는다 → 사용자 확인 U2** | 정의에 필요한 두 선언이 모두 없다. (i) 단일 출력 기준: `node_voltage_targets_v` = CI-15 대기라 지금은 `reference_undeclared`다(F4·F5). (ii) 상한: 절대 σ 선언이 없어 `value_from_constraint: offset_in_sigma_mv`가 `ref_unresolved`가 된다(F6·F7). 상수를 새로 만들지 않고 걸 길이 지금은 없다. 그래도 input_dc만으로 H 비대칭은 막힌다(§2). | 계획 U-128 (나) "절대 σ 선언이 없는 offset_excess 회로는 상한 근거 선언이 따로 필요, 단일 출력은 출력 기준 선언이 있어야 정의됨" | 상(지금 걸 수 없다는 판단) |
| **common_gate_amplifier** | **걸지 않음** | 입력이 하나라 맞출 쌍이 없다. spec에 offset 제약이 하나도 없다. input_dc가 `engine`(입력 자유)이면 "출력을 기준으로 되돌리는 입력 이동량"은 엔진이 고른 입력값과 같은 자유도라 판정 의미가 없다. 단일 출력 기준도 없다. | 연결(M1·M2·M3), spec constraints | 상 |

## 2. 각 값이 H 판정의 비대칭 입력 문제를 막는가

| 회로 | 판정(한 줄) |
|---|---|
| nmcnr | 막는다. agnd 넷 선언으로 Vin_p = Vin_n = 0.9 V가 고정된다(F2). H의 −141 mV 입력 차를 쓸 자유도가 없어진다. |
| current_reuse | 막는다. 0.9 V로 두 입력이 고정되고, 이미 있는 `offset_sys_mv ≤ offset_in_sigma_mv`(3.3 mV)와 `icm_margin_v ≥ 0`이 켜진다. |
| two_stage_ota | (A)·(B) 어느 쪽이든 막는다. 두 입력이 같은 값이 된다(H0r −324 mV의 원인 제거). 남는 계통 offset의 위 경계: \|V_id*\| ≲ \|V_ref − V_out0\| / A_dc ≤ 0.9 V / 10^(57/20) ≈ **1.3 mV**(선언 gain ≥ 57 dB, 출력은 포화 조건으로 레일 안). |
| two_stage_ota_sf | 막는다(H +27 mV 제거). 위 경계 ≈ 1.3 mV(gain을 two_stage에서 상속). 단 β = 1 사용 구성의 출력 여유는 U1 ⚠ 참조. |
| folded_cascode | 입력 차는 막는다(H +71/−118 mV 제거). **gain 제약이 없어 A_dc 하한이 없으므로 남는 계통 offset의 경계도 없다.** SP-3/4/5(성능 spec)와 함께 풀어야 한다. |
| ngcc | 막는다. 위 경계 ≈ 0.9 V / 10^(111/20) ≈ 2.5 µV(선언 gain ≥ 111 dB). |
| common_gate | 해당 없음(단일 입력이라 비대칭 입력 문제가 없다). H의 '입력 DC가 30~104 mV 낮아야 같은 출력'은 nA 전류의 모델 오차이고 SP-2와 무관하다(`h_judgment.md:387`). |

위 경계는 손계산 추정이다. card SF-1 반영 뒤 독립 판정에서 two_stage H0r 같은 점의 SPICE trim이 이 경계 안인지 재는 것을 확인 항목으로 둔다.

## 3. 사용자 확인이 꼭 필요한 항목 (원칙만으로 정할 수 없는 것)

**U1. single 원문이고 원문에 입력 DC가 없는 4회로(two_stage_ota·two_stage_ota_sf·folded_cascode·ngcc_3stage_ff)의 `input_dc` 꼴**

| 안 | 내용 | 물리 정합 | 손계산 속도 | design 단순성 | 원칙 점검 |
|---|---|---|---|---|---|
| (A) 기본안 | `{"value_v": 0.9}` = (vdd + gnd)/2, 근거 = β = 1에서 V_in = V_out이고 대칭 스윙 최대 출력 DC가 1차로 vdd/2 | 4회로 모두 창 안이다(손계산). 다만 folded는 창 아래 끝, ngcc는 위 끝, two_stage_sf는 팔로워 출력 끝 쪽이다 | 변화 없음 | spec data만 바꾸면 되고 SF-1 범위 안이다 | ⚠ **O-74 "원문에 없는 측정 조건을 관례로 덧붙이지 않음"과 긴장**: 대칭 스윙 근거는 1차 근사이고 정확한 중심은 sizing에 따라 다르다. ⚠ 유도값 0.9를 숫자로 박는다(supplies가 바뀌어도 따라가지 않는다 -- 상수 원칙). `input_dc_out_of_rails` 검사만 이를 지킨다 |
| (B) | `{"engine": true}`로 두되, engine 꼴이 **모든 입력 포트를 W4 변수 하나(y_icm)로 묶게** 고친다. 이는 spec_input_dc 문서가 말하는 '요구 입력 **공통모드**'의 뜻과 같다 | 최적화가 창 안 공통 DC를 고르고, 비대칭은 막히며, 상수가 없다 | W4 변수 하나 그대로 | 엔진 변경(kernel_fields 입력 고정 갈래, writer 계획)이 필요하다. 계획 J-E (c)·IT-Q1 문언을 개정해야 한다(계획 먼저) | 원칙 위반 없음. **원래 취지와 다름**: 승인된 U-128 꼴은 '선언값'이었다. SF-1 단독으로 할 수 없고 card를 추가해야 한다 |
| (C) | 원문 창 중심값(ngcc VDD/3 등)을 인용 | 원문 공정·공급이 달라 맞지 않는다 | - | - | ✗ 논문 값 인용 금지 |

권고: 원칙만 보면 (B)가 맞다. SF-1 일정상 (A)로 먼저 반영하고 (B)를 후속 card로 두는 길도 있다. 어느 쪽인지는 사용자가 정한다. (A)를 고르면 `icm_margin_v ≥ 0`(sf·current_reuse 선례 J-E 꼴)을 같은 4회로에 함께 둘지도 정해야 한다. 승인된 U-128 꼴 밖의 제약 추가라 따로 묻는다.

**U2. 단일 출력 5회로의 `offset_sys_mv`**: 지금은 걸 수 없다(§1-2). 걸려면 두 가지가 필요하다.
- (i) **출력 기준 선언**: 후보는 DEC-23 '(입력 추종)'이고, U-127(sf_pushpull)과 같은 꼴이다. 근거는 spec 되먹임 선언 β = 1과 원문 unity-gain 측정(nmcnr·ngcc)이다. U-127 선례는 source에 사용자 확인 기록을 요구했다. 또 이 선언은 출력 DC를 0.9 V로 묶는 셈이어서 two_stage_sf의 출력 여유(U1 ⚠)에 영향을 준다.
- (ii) **상한 근거**: 후보 N1 = 같은 점에서 계산한 `offset_in_sigma_mv`(graph `OffsetAnalysis.sigma_in_mv` READS, 사본 없음) 이하. 이는 '계통 ≤ 랜덤'(DEC-23)을 같은 점에 적용한 것이다. 다만 spec 계약에 '계산값 참조' 꼴이 없어(F6) 계획·design 개정이 필요하다. 후보 N2 = 회로별 절대 σ 선언. 값은 사용자 spec이고 지금은 근거가 없다.

기본안(이번 SF-1): 걸지 않는다. §2의 경계(input_dc 고정 + 선언 gain)로 two_stage 계열 ≤ ~1.3 mV, nmcnr·ngcc ≤ µV급이다. **원래 취지와 다름**: 승인된 U-128 형태 '(가) input_dc + (나) offset_sys_mv' 가운데 (나)를 5회로에서 미룬다. folded는 gain 제약이 없어 경계가 없다는 점을 함께 보고한다.

**(위임 범위 안에서 정한 것 -- 확인 불요)**: nmcnr = agnd(O-74가 이미 지정), current_reuse = 0.9 V(상보 쌍 대칭과 원문 동작점 일치), common_gate = engine(단일 입력, 원문은 바이어스로 정한 입력), current_reuse offset_sys 유지, common_gate offset_sys 미적용.

## 4. 원칙 점검 (실측 / 자기보고 / 안 함)

| 항목 | 결과 | 구분 |
|---|---|---|
| graph 단일 정본 | input_dc는 사람 선언이고 writer는 spec 로더 하나다. 엔진 소비자(`dc_inputs` → `kernel_fields` fixed_values, `headroom_bound`, `ls_swing` icm_margin, `symmetry_marks`)는 READS만 한다(grep 확인). 새 cache·사본은 제안하지 않았다. U2 N1은 기존 `OffsetAnalysis` 필드 READS라 둘째 생산자가 아니다. | 실측(grep) |
| 상수 발명 | 새 숫자 없음. 0.9 = supplies_v (vdd + gnd)/2이고 nmcnr은 supplies_v agnd 참조다. ⚠ (A)는 유도값을 숫자로 박는다(U1에 경고). | 실측 |
| 논문 값 인용 | 하지 않았다. current_reuse 원문 0.900 V는 물리 유도와 일치하는지 교차 확인만 했다. 원문 ICMR 창·ngcc VDD/3은 값으로 쓰지 않았다. | 자기보고 |
| 회로 해석 근거 | netlist 연결(게이트-포트 넷, 꼬리 소자 레일)과 원문만 썼다. device_roles·sizing_roles는 읽지 않았다. | 실측(topology netlist 덤프) |
| DC/AC 분리 | input_dc·창·offset 경계는 모두 DC 양으로 다뤘다. A_dc는 DC 극한 전달이다. | 자기보고 |
| 손계산 창 추정 | Vth·Vov는 대략값(~0.45~0.6 V, 0.1~0.2 V)이고 LUT로 재지 않았다. nmcnr만 SPICE 창(H 판정)으로 확인했다. | **안 함(LUT 미측정)** -- SF-1 반영 뒤 독립 판정에서 확인 필요 |
