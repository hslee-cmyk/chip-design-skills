# DE-1 착수 조건 (iii) -- 13회로 출력 구조 분류 표 (O-64 (1))

- 작성 2026-10-21, 분석 agent(읽기 전용, 저장소 무변경). base master `7675f71b`(gain-budget 계획 v6.23).
- 근거 규칙: 계획 N3.8 '출력 구조 분류 -- 규칙 하나'(plan.md 570행 안), N6.8 DE-1 순서·착수 조건 (iii)(1588행), N2 O-43 D3 행(310행)·O-64 행(318행); `_drafts/user_decisions.md` O-23(642행)·O-43 D3(663행)·O-64 (1)(685행).
- **판정 자료는 netlist 연결과 spec 선언뿐**이다. device_roles·symmetry·sizing_roles·compensation·topology 주석·회로 이름은 근거로 쓰지 않았다(회로 이름은 표의 행 이름으로만 씀).
- 13회로 = O-23 측정(`evidence/2026-10-19/dcswing/part_ab.py`, 결과 `out/ab.jsonl`)의 대상과 같다: library 9(`assets/library/*.topology.json`, `_TEMPLATE` 제외) + heldout 4(`assets/heldout/*`).

## 0. 계산 방법과 교차 확인

- 스크립트: `C:/Users/HSLEE/AppData/Local/Temp/claude/C--Users-HSLEE-Documents-Todoc-fpga-chip-design-skills/63c6146a-ab1d-4035-a169-bae810986922/scratchpad/de1_table/de1_classify.py`(엔진 import만 함, 소스는 고치지 않음). 결과: 같은 폴더 `out.jsonl`(11회로), `raw2.txt`(spec 원문 W3·입력 DC, cnr_ota·erfc_ota 손 계산).
- 엔진 경로: `run_stage_a` → `build_kernel_context` → `kctx.base`에서 pins·element_class·kind·is_rail·port_direction·`dc_writer`를 읽고, spec 선언은 `dc_inputs_from_spec`(`node_targets` = W3, `input_dc_v`)에서 읽었다.
- G_vgs는 `gmid_engine/sizing/writer_plan.py` 머리말 2의 정의대로 다시 만들었다. 포함하는 엣지는 MOS (gate, source), 저항 (t0, t1), 입력 DC가 선언되지 않았을 때 입력 포트끼리 잇는 '같은 DC' 엣지다. 용량과 이상 전류원은 넣지 않았다.
- F는 레일과, 입력 DC가 선언됐을 때의 입력 포트다. 규칙대로 W3는 F에서 뺐다. W3 노드는 성분 연결에는 그대로 남는다. 참고 칸 `new_if_cut`에서는 W3 노드를 그래프에서 잘라 내 다시 계산했다. 이 코퍼스에는 W3가 없어 두 계산의 결과가 같다.
- **cnr_ota·erfc_ota**는 엔진 S0 쓰기 계획이 멈춘다. cnr_ota는 `StructureUnresolvedError` `dc_resistor_cycle`(x40 VCR–VDD_1V8)에서, erfc_ota는 `mos_zero_current_structural`(M19·M20·M21)에서 멈춘다. 그래서 이 두 회로는 topology JSON의 `netlist`·`passive_elements`·`ports`·`supply_nets`와 spec `human` 원문으로 같은 정의를 따라 손 스크립트로 셌다(`raw2.txt`). 옛 D3(writer tier)는 이 두 회로에서 **정의 불능**이다.
- 직접 읽어 교차 확인한 것: 출력마다 닿는 단자 목록(`terms`)과 G_vgs 이웃(`gvgs_nbrs`)을 netlist 줄과 대조했다. cnr_ota는 F까지 가는 최단 경로를 따로 추적했다(§2). O-23 `ab.jsonl` 분류 라벨과는 15출력 전부를 대조했다.

## 1. spec 선언 (13회로 공통 사실)

| 회로 | W3(`node_voltage_targets_v`) | 입력 DC 선언(`input_dc`) |
|---|---|---|
| common_gate_amplifier | pending CI-15 → 없음 | pending SP-2 → 미선언 |
| current_reuse_telescopic_ota | pending CI-15 | pending SP-2 |
| folded_cascode | pending CI-15 | pending SP-2 |
| ngcc_3stage_ff | pending CI-15 | pending SP-2 |
| nmcnr_amplifier | pending CI-15 | pending SP-2 |
| pushpull_follower_buffer | pending CI-15 | **net agnd (0.9 V)** |
| sf_pushpull_output_opamp | pending CI-15 | **net agnd (0.9 V)** |
| two_stage_ota | pending CI-15 | pending SP-2 |
| two_stage_ota_sf | pending CI-15 | pending SP-2 |
| cnr_ota | pending CI-15 | pending U-75 |
| erfc_ota | pending CI-15 | **value 0.8 V** |
| r2r_opamp | pending CI-15 | pending U-75 |
| rfc_ota | pending CI-15 | **value 1.02 V** |

→ **13회로 모두 W3 목표가 선언되지 않았다**(CI-15 결정 대기). 그래서 O-64 (1)의 'W3 핀 빼기'는 지금 코퍼스에서 무동작이고 **경우 1은 0건**이다. CI-15가 결정되어 W3가 선언되면 이 표를 다시 재야 한다.

## 2. 표 -- 출력 15개(13회로)

열 설명: **G_vgs 이웃** = 출력에 직접 닿는 G_vgs 엣지. **F(W3 뺀 뒤)** = 출력 성분에 남은 레일·선언 입력 DC. **옛 D3** = O-43 D3 원문('출력 노드에 DC writer가 있으면 KVL 고정, W4면 고임피던스')을 엔진 `dc_writer` tier에 그대로 적용한 결과. **O-23** = `dcswing/out/ab.jsonl`의 `conn_class`.

| # | 회로 | 출력 | W3 | 입력 DC | 출력 단자(연결) | G_vgs 이웃 | 성분 크기 | F(W3 뺀 뒤) | **새 분류** | 옛 D3 (writer → 분류) | O-23 분류 | 경우 1 | gate-only 특례 | 새 대 옛 D3 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 1 | common_gate_amplifier | vout | 아님 | 미선언 | M2.d, M3.d | 없음(G_vgs 밖) | 1 | -- | **HZ** | W4 free_window → HZ | HZ(not in G_vgs) | 아님 | 아님 | 같음 |
| 2 | current_reuse_telescopic_ota | Vom | 아님 | 미선언 | M15.d, M16.d, R1.t0, CL2·Cc1·Cf1 | R1 → Voc | 25 | gnd, vdd | **KVL** | W2 resistor_drop(R1) → KVL | KVL(성분에 레일) | 아님 | 아님 | 같음 |
| 3 | current_reuse_telescopic_ota | Vop | 아님 | 미선언 | M25.d, M26.d, R2.t1, CL1·Cc2·Cf2 | R2 → Voc | 25 | gnd, vdd | **KVL** | W2 resistor_drop(R2) → KVL | KVL | 아님 | 아님 | 같음 |
| 4 | folded_cascode | out | 아님 | 미선언 | M6.d, M8.d, CL | 없음 | 1 | -- | **HZ** | W4 → HZ | HZ | 아님 | 아님 | 같음 |
| 5 | ngcc_3stage_ff | Vout | 아님 | 미선언 | M7·M12·M13·M14.d, CL, Cm1, Cm2 | 없음 | 1 | -- | **HZ** | W4 → HZ | HZ | 아님 | 아님 | 같음 |
| 6 | nmcnr_amplifier | Vout | 아님 | 미선언 | M301.d, M302.d, RL.t0, Rm.t1, CL | RL → agnd, Rm → NodeCM | 3 {Vout, NodeCM, agnd} | agnd | **KVL** | W2 resistor_drop(RL) → KVL | KVL | 아님 | 아님 | 같음 |
| 7 | pushpull_follower_buffer | vout | 아님 | **선언(agnd)** | M1.s, M2.s, CL | M1 g–s → A, M2 g–s → B | 4 {vout, A, B, vin} | **vin**(선언 입력 DC) | **KVL** | W2 vgs_source(M1) → A → M3 → vin(W2 input_dc) → KVL | 'floating (레일 없음) + 입력 포트 포함' | 아님 | 아님 | 같음 |
| 8 | sf_pushpull_output_opamp | vout | 아님 | 선언(agnd) | M21.s, M22.s, CL | M21 g–s → N20, M22 g–s → N17 | 4 {vout, N17, N20, Y} | 없음 | **HZ** | W2 vgs_source(M22) → KVL (사슬 뿌리 N20 = W4) | 'floating (레일 없음)' | 아님 | 아님 | **다름** |
| 9 | two_stage_ota | OUT | 아님 | 미선언 | M6.d, M7.d, CL, Cc | 없음 | 1 | -- | **HZ** | W4 → HZ | HZ | 아님 | 아님 | 같음 |
| 10 | two_stage_ota_sf | vout | 아님 | 미선언 | M8.s, M9.d, CL | M8 g–s → OUT | 2 {vout, OUT} | 없음 | **HZ** | W2 vgs_source(M8) → KVL (사슬 뿌리 OUT = W4) | 'floating (레일 없음)' | 아님 | 아님 | **다름** |
| 11 | cnr_ota | VOP | 아님 | 미선언 | x3[0,1].d, x6[0,1].d, **x33.g**, CL1 | x33 g–s → VCOP | 32 | VDD_1V8, VSS | **KVL** | 정의 불능(쓰기 계획 정지 `dc_resistor_cycle`) | KVL | 아님 | **변형**(§4) | 비교 불능 |
| 12 | cnr_ota | VON | 아님 | 미선언 | x14[0,1].d, x17[0,1].d, **x35.g**, CL2 | x35 g–s → VCON | 32 | VDD_1V8, VSS | **KVL** | 정의 불능 | KVL | 아님 | **변형** | 비교 불능 |
| 13 | erfc_ota | out | 아님 | 선언(0.8) | M6.d, M8.d, CL | 없음 | 1 | -- | **HZ** | 정의 불능(`mos_zero_current_structural`) | HZ | 아님 | 아님 | 비교 불능 |
| 14 | r2r_opamp | Vo | 아님 | 미선언 | M25.d, M26.d, RL.t0, CL, CM1, CM2 | RL → VSS | 7 | VSS | **KVL** | W2 resistor_drop(RL) → KVL | KVL | 아님 | 아님 | 같음 |
| 15 | rfc_ota | out | 아님 | 선언(1.02) | M6.d, M8.d, CL | 없음 | 1 | -- | **HZ** | W4 → HZ | HZ | 아님 | 아님 | 같음 |

집계:
- 출력 기준: KVL 고정 7개(#2, #3, #6, #7, #11, #12, #14), 고임피던스 8개(#1, #4, #5, #8, #9, #10, #13, #15).
- 회로 기준: KVL 고정 5회로(current_reuse_telescopic_ota, nmcnr_amplifier, pushpull_follower_buffer, cnr_ota, r2r_opamp), 고임피던스 8회로(common_gate_amplifier, folded_cascode, ngcc_3stage_ff, sf_pushpull_output_opamp, two_stage_ota, two_stage_ota_sf, erfc_ota, rfc_ota).
- 경우 1: 0건. 원인은 W3 선언이 하나도 없기 때문이다. 그러므로 W3 정정 자체는 이 코퍼스에서 무동작이다.
- 엄격한 gate-only 특례(출력이 '레일에 source가 붙은 소자'의 gate에만 닿음): 0건. 변형(출력이 G_vgs에 gate로만 닿고, 그 소자의 source는 레일이 아니며, 성분을 따라가면 F에 닿음)은 2건(cnr_ota VOP·VON).
- 새 규칙 대 O-23: 15출력 모두 일치한다. 단 #7은 O-23 F에 선언 입력 DC가 없어서 'floating + 입력 포트 포함'으로만 적혀 있었다. 선언 입력 DC(agnd)를 F로 넣으면 KVL이 된다.
- 새 규칙 대 옛 D3(원문 그대로 적용): 2건이 다르다(#8, #10). 2회로(#11·#12의 cnr_ota, #13의 erfc_ota)는 옛 D3를 정의할 수 없다.

## 3. 회로별 근거 (연결만)

**common_gate_amplifier vout**: M2·M3의 drain에만 닿고 G_vgs(g–s·R) 엣지가 없다. 그래서 G_vgs 밖이고 고임피던스다. drain끼리만 만나는 노드여서 KCL 전류 균형으로만 정해지고 KVL 사슬은 없다.

**current_reuse_telescopic_ota Vom/Vop**: R1이 Vom–Voc를, R2가 Voc–Vop를 잇는다(저항 평균). Voc는 M37a의 gate다. writer 사슬은 Voc ← M37a(vgs_gate) ← Ncmfb_tail ← M37b ← Voc_des ← M40 ← gnd다. 레일까지 가는 VGS·저항 사슬이 있으므로 KVL 고정이다. 구조로는 출력 공통모드를 저항으로 감지해 되먹이는 경로(CMFB)다. 공동분석 Q1을 본다.

**folded_cascode out, ngcc_3stage_ff Vout, two_stage_ota OUT, rfc_ota out, erfc_ota out**: 모두 drain과 용량에만 닿고 G_vgs 밖이다. 그래서 고임피던스다. rfc_ota·erfc_ota는 입력 DC가 선언됐지만 출력이 G_vgs 밖이어서 결과에 영향이 없다.

**nmcnr_amplifier Vout**: RL이 Vout–agnd를 잇는 레일 저항이다. 그래서 KVL 고정이다. 계획 N3.8의 예시와 같다. Rm(Vout–NodeCM)도 성분에 들어가지만 F 판정에는 영향이 없다.

**r2r_opamp Vo**: RL이 Vo–VSS를 잇는다. 그래서 KVL 고정이다. 성분 7개 {VSS, Vo, n_abn, n_gn, n_m24, n_m9, n_mn}이 RL·VSS를 거쳐 다른 VSS 기준 노드와 이어진다.

**pushpull_follower_buffer vout**: vout은 M1·M2의 source다. vout ← M1(g–s) ← A ← M3(g–s) ← vin으로 이어지고, vin은 선언 입력 DC(agnd 0.9 V)라 F다. 그래서 KVL 고정이다. 입력에서 VGS 사슬로 출력 DC가 정해지는 follower다.

**sf_pushpull_output_opamp vout**: vout은 M21·M22의 source다. 성분은 {vout, N20, N17, Y}로 닫혀 있고 레일도 입력 포트도 없다. 쓰기 계획 사슬은 vout ← M22 ← N17 ← M18 ← Y ← M19(vgs_gate) ← N20(W4 free_window)이다. 그래서 고임피던스다. 출력은 앞단 고임피던스 노드 N20을 VGS만큼 옮겨 따라간다.

**two_stage_ota_sf vout**: vout은 M8의 source이고 M9의 drain이다. 성분은 {vout, OUT}이고 OUT은 W4(free_window)다. F가 없으므로 고임피던스다. OUT을 VGS(M8)만큼 옮겨 따라가는 출력이다.

**cnr_ota VOP/VON**: VOP는 x3·x6의 drain이고 x33의 **gate**다. x33의 drain은 VDD_1V8, source는 VCOP이고 VCOP에는 x1 전류 싱크가 붙는다. VON도 같은 꼴이다(x14·x17의 drain, x35의 gate, source VCON). F까지 가는 최단 G_vgs 경로는 VOP → x33(g–s) → VCOP → x37(R) → LPCO → x42(g–s, pmos, source VSC) → VSC → x43(g–s) → VCREF → x9(R) → VSS다. VON은 x35 → VCON → x38(R) → LPCO로 같은 경로에 합류한다. 따라서 성분에 VDD_1V8·VSS가 있고 KVL 고정이다. 구조로는 source follower(x33/x35)로 레벨을 옮기고, 저항 평균(x37/x38 → LPCO)을 거쳐 차동쌍(x42/x43, 기준 VCREF)에 넣는 CMFB 감지 경로다. 엔진 쓰기 계획은 x40(VCR–VDD_1V8) 저항 루프에서 멈춘다.

## 4. 공동분석 질문 (사용자 승인 대상)

**Q1. CMFB로 감지되는 차동 출력의 KVL 고정**(current_reuse Vom/Vop, cnr_ota VOP/VON -- 출력 4개)
- 의견: 규칙대로 KVL 고정이 맞다.
- 근거:
  - (1) 출력 공통모드는 감지 경로(저항 평균 또는 SF+저항 평균)와 레일 기준 VGS·저항 사슬로 정해진다. 계획 570행도 'CMFB로 KVL이 정하는 출력'을 KVL 고정 쪽에 명시한다.
  - (2) KVL 고정의 계산은 봉인점 DC 방정식의 1차 감도(전회로 DC 야코비안)라서 차동 모드 이득 경로도 함께 담는다.
  - (3) 고임피던스 처리(θ 고정 연립에 V_out = x 행)를 하면 한쪽 출력을 x로 고정하는 순간 공통모드 사슬과 겹쳐 과결정이 될 수 있다.
- 주의: 차동 신호로 보면 각 출력은 높은 이득을 가진 고임피던스 노드다. 선형 감도로 낸 스윙 끝은 '추정'이고, 정확값은 oracle `.dc`가 낸다.
- 확신도: ~0.75.

**Q2. 엄격한 gate-only 특례**(출력이 '레일에 source가 붙은 소자'의 gate에만 닿음 -- 이 코퍼스에서는 0건이라 가정 질문)
- 의견: 규칙은 KVL 고정(V_out = 레일 ± VGS(θ))으로 분류한다. 계산 정합성은 문제없다. 야코비안이 그 소자의 gm을 담고, θ 고정 연립에 x 행을 더하면 오히려 VGS 고정과 충돌한다.
- 다만 물리적으로 이 노드는 증폭 경로의 고임피던스 노드다. DC가 'θ가 그 소자의 전류를 고정하기 때문에' 정해질 뿐이다. 실제 회로에서는 그 소자의 전류가 노드 전압으로 정해진다. 그래서 'KVL 고정'이라는 이름은 물리 해석과 어긋난다.
- 권고: 지금은 예외 규칙을 만들지 않는다. 0건이어서 만들면 쓰지 않는 코드가 된다. 나타나면 그때 공동분석한다.
- 변형인 cnr_ota(gate 소자의 source가 레일이 아니고, CMFB 경로로 F에 닿음)는 Q1로 처리한다.
- 확신도: ~0.6.

**Q3. source follower 출력의 고임피던스**(sf_pushpull_output_opamp vout, two_stage_ota_sf vout)
- 의견: 고임피던스가 맞다. 출력은 앞단 W4 고임피던스 노드(N20 또는 OUT)를 VGS만큼 옮긴 값이다. θ 고정 연립에 V_out = x를 두면 사슬을 따라 앞단 노드가 x + VGS로 정해져 모순이 없다.
- 확신도: ~0.85.
- **원래 취지와 다름(보고)**: 옛 O-43 D3 원문('출력 노드에 DC writer가 있으면 KVL 고정')을 그대로 적용하면 두 출력은 W2 vgs_source writer가 있어 KVL 고정이 된다. 그러면 계획 N3.8의 문장 'W3가 아닌 출력에서는 뺄 핀이 없어 결과가 옛 D3와 같다'는 이 2건에서 **사실이 아니다**. 옛 D3를 'writer 사슬의 뿌리가 F이면 KVL 고정'으로 읽으면 두 규칙이 같아진다.
- 그래서 결정할 것은 둘 중 하나다. (가) 계획 문언을 '옛 D3(사슬 뿌리 해석)와 같다'로 정정한다. (나) 이 2건을 옛 D3 대비 동작 변경으로 기록한다.
- 권고: (가). 근거는 O-23 측정도 두 출력을 'floating (레일 없음)'으로 적었다는 점이다. 다만 아직 구현된 분류가 없어 실제 동작 변경은 없다(DE-1 미구현).

**Q4. 선언 입력 DC를 F로 삼은 follower 버퍼**(pushpull_follower_buffer vout)
- 의견: KVL 고정이 맞다. 개루프 follower여서 출력 DC가 입력 DC에서 VGS 사슬로 정해진다. 스윙을 잴 때 입력을 훑는 구동도 야코비안이 담는다.
- O-23은 F에 선언 입력 DC를 넣지 않아 'floating + 입력 포트'로만 기록했다. 새 규칙(F = 레일 + 선언 입력 DC)으로 바꿔 읽으면 결과가 일치한다.
- 확신도: ~0.8.

**Q5. design 메모**(결정이 아니라 design이 다룰 것)
- 계획은 분류 graph 필드의 writer를 'S0 쓰기 계획 쪽'에 두라고 권고한다. 그런데 cnr_ota·erfc_ota는 쓰기 계획(`dc_writer_plan`)이 `StructureUnresolvedError`로 멈춘다. 분류 자체는 connectivity와 F 선언만으로 정해지므로 이 두 회로에서도 계산할 수 있다.
- 분류 writer를 쓰기 계획 블록 안에 두면 이 두 회로는 분류 필드가 없다. 쓰기 계획보다 앞선 별도 S0 블록에 두면 분류 필드가 생긴다. 어느 쪽인지 design이 정해야 한다(graph 규칙: writer 하나, 둘째 생산자 금지).

## 5. 출처 (원문 링크·로컬 경로)

로컬 경로 루트는 `C:/Users/HSLEE/Documents/Todoc/fpga/chip-design-skills/skills/analog-gmid-design/assets/`다.

| 회로 | 로컬 원문 | 웹 링크 |
|---|---|---|
| common_gate_amplifier | `library/sources/common_gate_amplifier__allen_2014/source.pdf`(+paper.md) | https://aicdesign.org/wp-content/uploads/2018/08/lecture20-140624.pdf |
| current_reuse_telescopic_ota | `library/sources/current_reuse_telescopic_ota__xie_chen_2019/source.pdf`. 보조: `__sooch_1985/source.pdf`, `__sanchez_sinencio_2000/source.pdf` | Xie & Chen 원문 링크는 찾지 못함(README 19행). 보조: https://patents.google.com/patent/US4550284A/en , https://people.engr.tamu.edu/s-sanchez/LV-Dallas-IEEE-Tutorial.PDF |
| folded_cascode, two_stage_ota | `library/sources/two_stage_ota+folded_cascode__maloberti_2004/source.pdf` | 저자 게시처 찾지 못함(README 25행) |
| ngcc_3stage_ff | `library/sources/ngcc_3stage_ff__lee_2007/source.pdf` | https://doi.org/10.5573/JSTS.2007.7.1.020 |
| nmcnr_amplifier | `library/sources/nmcnr_amplifier__leung_1999/source.pdf`(Fig.3·Table 1, 저널 p.602 = PDF p.4) | IEEE Xplore 링크 찾지 못함(README 27행) |
| pushpull_follower_buffer, sf_pushpull_output_opamp, two_stage_ota_sf | `library/sources/pushpull_follower_buffer+sf_pushpull_output_opamp+two_stage_ota_sf__allen_2014/source.pdf` | https://aicdesign.org/wp-content/uploads/2018/08/lecture26-140625.pdf |
| cnr_ota | `heldout/sources/cnr_ota__wulff_2024/`(CNR_OTA.sch, CNR_OTA.svg, CNR_OTA.design.md -- PDF가 아니라 xschem 회로도) | https://github.com/wulffern/cnr_ota_sky130nm/tree/8c839f7 |
| erfc_ota | `heldout/sources/erfc_ota__wu_2025/source.pdf`(Fig.6 p.8, Table 1 p.9, 입력 CM 800 mV p.13) | https://www.mdpi.com/1424-8220/25/8/2523 , https://pmc-oa-opendata.s3.amazonaws.com/PMC12031453.1/PMC12031453.1.pdf |
| r2r_opamp | `heldout/sources/r2r_opamp__hogervorst_1994/source.pdf` | https://repository.tudelft.nl/file/File_0fc107fa-6796-4bae-9159-8537a431f171 |
| rfc_ota | `heldout/sources/rfc_ota__matibag_2024/source.pdf` | https://upcommons.upc.edu/bitstreams/a99028f7-5d7f-447a-b086-c1f4effcdb1b/download |

이 표의 분류는 netlist 연결만으로 냈다. 원문 링크는 사용자가 회로를 확인할 때 쓰도록 붙였다.

## 6. graph 단일 정본 점검 (이 분석의 권고)

- 새 cache·사본·둘째 생산자를 권고하지 않는다.
- Q5는 분류 필드를 한 블록이 한 번 쓰고 다른 블록은 READS로 읽는다는 계획 규칙을 전제로, 그 writer의 위치만 묻는다.
- Q2는 0건 구조를 위한 예외 코드를 만들지 말라고 권고한다(만들면 배선하라는 원칙과 같은 방향).
