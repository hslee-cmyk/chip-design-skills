# CMP-1 시범 판정 독립 재확인 + 엔진 수정 대안 분석 (2026-10-27)

재확인자: 독립 재확인 agent(판정자와 다른 agent). 판정 보고(`cmp1_pilot_judgment.md`)는 주장 목록으로만 쓰고, 수치는 `wt/_cmp_pilot/verify/` 의 내 스크립트로 다시 쟀다.
엔진 = `wt/integ-it12` @ 68b4e234 (import 실행만, 수정 없음). 원자료 = `wt/_cmp_pilot/verify/res/*`.
기록 방식: 케이스마다 Python 바이너리 append.


## 케이스 C. 판정자 주장 C1~C6 재확인 (내 실측)

공통: 엔진 = `wt/integ-it12` @ 68b4e234 import 실행만(빌드 사슬 = armC/tests 와 같은 run_stage_a -> run_stage_b -> kernel ctx -> search ctx, `verify/vbuild.py`). SPICE = ngspice-46 `ngspice_con.exe -b`, `ngbehavior=hsa`, sky130 tt pm3 + mismatch.corner + lod (LUT 생성 메타의 파일군과 같음), 27 °C(계획 DEC-96 (3) 합격 조건 = TT 27 °C).

### C1. armA two_stage 해 -> 엔진 θ -> 평가 feasible, 출발점으로 주면 front 1점 -- **재현**

- θ 를 판정자 파일을 쓰지 않고 다시 만들었다: armA `two_stage_r4/sized.sp` 기하(W 총폭 = w·m) + **내 SPICE OP**(`verify/sp/ts_op27.sp`, 27 °C, 이상 bias 0.6609 V, 단위 되먹임) 전류 I1 3.2712 µA·I2 3.2720 µA·I5 6.5432 µA·I6 64.717 µA(판정자는 기준 가지 모드 전류 3.40/67.26 µA를 썼다 -- 다른 출발). ln_idu = ln(I·L/W). y(OUT)·y(vin_p) 는 내 이분(`verify/v_c1.py`)으로 노드 DC 0.9 V 에 맞춤: y(vin_p) = 0.22534 (판정자 0.2207 -- 전류가 달라 다름).
- 엔진 평가(`res/c1_eval.json`): **sealed, 모든 제약 행 c > 0**(최소 활성 행 gbw c = 0.433, PM c = 1.08). 전력 128.27 µW = 1.8 V × 71.26 µA -- 내 SPICE I(Vdd) 71.26 µA 와 같음. 노드 DC: CS 0.2333 V(SPICE 0.2341), O1 0.6504(0.6502), D3 0.6542(0.6605), bias 0.6606(0.6609).
- `find_front(sctx, [θ])`(평가 예산 2000, 252 s, `res/c1_front.json`): **front 1점**. 층 0 시작점 s1 은 power·area 모두 `slsqp_4`(수락 5·4) -- 판정자 수치와 같은 정지. 주어진 시작점 s2 의 area 끝점에서 L-b 1회(`l_search stops = [{class front, l_from EA:s2, stop eval_budget, accepted 0}]`). front 점: 전력 92.6 µW·면적 7.22e-10 m²·gain 84.5 dB·GBW 7.002 MHz·PM 70.01°(GBW·PM 경계에 붙음). 판정자 front(89.2 µW, 6.56e-10 m²)와 수치는 조금 다르나(출발 전류가 다름) 결론 같음.
- 판정: **재현**. 근거 `verify/res/c1_eval.json`, `c1_front.json`.

### C2. 원인 사슬 -- **재현**(코드·실행 기록), 단 사슬 첫 고리에 **결정 미반영**이 겹쳐 있음(아래 ★)

| 고리 | 코드 file:line | 내 실측(`res/start_two_stage_ota.json`, `start_folded_cascode.json`) |
|---|---|---|
| ① GB4 상한 미상 | `metrics/block_gain_bound.py:227-234`(`over = model.pi > budget` -> `REASON_OVER_BUDGET`), 사유 상수 `metrics/achievability_types.py:21` | two_stage O1 블록 Π = 1.709e22(축: vgs 49⁴·L 18⁴·vds 49⁴·vsb 10²·current 49), OUT 블록 Π = 1.868e9(vgs 49²·L 18²·vds 49²), folded out 블록 Π = 6.19e52. found_db = 61.17·67.72 dB(two_stage), 119.3 dB(folded) |
| ② 예산 N_S 출처 | `search/count_budget.py:16-23`: N_S = Σ(쓰는 kind 의 LUT 폭 슬라이스) \|L\|·\|VGS\|·\|VDS\|·\|VS\| (설계 41 §0 D-NS, '상한 계산 한 번이 LUT 전체를 한 번 훑는 양'). spec 선언 `structure_count_budget` 이 있으면 그 값(`authoring/spec_count_budget.py`) | N_S = 32 슬라이스 × 18·49·49·10 = **13,829,760** (두 회로 같음, 선언 없음). Π/N_S = 1.2e15(O1)·135(OUT) -- 9 자릿수 이상 차이라 어떤 실용 블록도 인증 불가. 엔진 머리 주석 `metrics/achievability.py:25` 와 계획 F-LA5 가 이미 '9회로 거의 전부 미상'으로 적은 구조적 한계 |
| ③ 이득 L 하한 비활성 | `search/iv_context.py:49-51`: 블록 하나라도 `status != certified` 면 `(gain_l_6.4_1, u9_value_not_certified)` 반환, `search/iv_gain_l.py:99-101` 이 빈 경계로 끝 | two_stage `inactive` = gain_l_6.4_1 `u9_value_not_certified`. folded 는 gain 제약 미선언이라 `constraint_not_declared`(같은 고리가 아니라 spec 미반영 -- C6/D4) |
| ④ 최소 L 칸 출발 | 출발 구간 `start.row` | `l_chosen` = 1.5e-7 m, two_stage M1~M7 전부, folded 13 소자 전부 |
| ⑤ 그 칸 이득 상한 | (손계산 -- 독립 경로) LUT 5 µm 슬라이스 진성 이득 max gm/gds: nfet L 0.15 µm 24.2(27.7 dB), pfet 8.7(18.8 dB); L 0.18 µm nfet 42.8·pfet 22.7. 같은 전류 두 단 상한 ≈ Π_i A0n·A0p/(A0n+A0p) | **L 0.15 µm 약 32 dB, 칸 0 위 끝 L 0.18 µm 에서도 약 47 dB < 57 dB** -- 칸 0 안 도달 불가가 손계산으로도 성립(판정자 '33 dB 최대'와 일치) |
| ⑥ SLSQP 정지 | 외층 `search/eps_sweep.py:71-81`(끝점 두 개, best 없으면 failed) | 내 c1_front 실행에서 s1 power·area `slsqp_4` 수락 5·4(판정자·armC 와 같음) |
| ⑦ L-b 미기동 | `search/eps_sweep.py:116-124`: L-b(`polish_l_cells`)는 비지배 필터를 통과한 점(`kept`)에만 돈다; `search/l_bin_search.py:1-9` 'front 점에서 L 칸 한 칸 이동' | armC v4 기록 `l_search stops []`(두 회로). 내 c1_front 에서는 kept 점이 생기자 L-b 가 돎 -- 'feasible 점이 있어야 L 칸 이동이 시작된다'가 코드·실행 두 쪽에서 성립 |

★ **결정 미반영(판정자가 못 본 것)**: `wt/_drafts/user_decisions.md:313`(2026-10-13 사용자 "Q1-2는 (ii) 권고대로") -- "41 §6.4-1 이득 L 하한의 'A_max 미상 → 비활성'을 41 §5.3.2 L-2와 같은 found_db 비례 g_i로 대체(gain 선언 회로에서 활성)". 같은 파일 :371(2026-10-14 Q-R1)도 'Q1-2 (ii) 반영 뒤'를 전제한다. 그런데 계획(`grep Q1-2` 0건)·design 41 :1569("A_max가 미상이거나 gain 제약이 없으면 비활성이다(H3)")·코드(`iv_context.py:49-51`) 어디에도 반영되지 않았다. 즉 고리 ③은 '설계 결함'이 아니라 **승인된 결정이 계획·design·구현으로 전파되지 않은 결함**이다.

### C3. 엔진 평가 대 SPICE 1~3 % -- **재현(이득·GBW·PM·잡음), offset 은 미확인(엔진 쪽만 재현)**

같은 점(armA r4, 27 °C, 이상 bias 0.6609 V)에서 내 SPICE(`verify/sp/ts_ac27.sp`, 차동 ±0.5 구동, DC 서보 L 1e12/C 1, CL 3 pF) 대 내 엔진 평가(`res/c1_eval.json` metrics):

| metric | 엔진 | 내 SPICE | 차 |
|---|---|---|---|
| gain_ss_db | 83.66 | 83.26 | +0.40 dB |
| gbw_ss_hz | 7.227 MHz | 7.088 MHz | +2.0 % |
| pm_ss_deg | 73.18 | 73.64 | −0.46° |
| noise_excess_th(열 성분 전력비, f = 1 Hz, 1overf 제외) | 1.362 | 1.346 | +1.2 % |
| offset_excess | 1.121 | (안 잼 -- PDK mismatch 변수별 bench 필요) | 판정자 SPICE 1.113 인용만 |

판정: 주장 범위(1~3 %) 안 -- **재현**. offset_excess SPICE 값은 독립 측정하지 않았다(미확인).

### C4. 좁은 폭 효과 -- **재현**, 수치 조건 정정 1건, LUT·PDK 사실 보충

- **PDK W bin 존재**(내 파싱, `cells/pfet_01v8/..._tt.pm3.spice` `.model` 블록 wmin/wmax): pfet W bin 12개 경계 {0.42, 0.55, 0.64, 0.84, 1.0, 1.26, 1.65, 1.68, 2.0, 3.0, 5.0, 7.0, 100} µm, nfet 20개(0.36 ~ 100 µm). L bin 과 대칭인 **W 방향 bin 이 있다**.
- **LUT 폭 슬라이스 = W bin 경계 집합**: 슬라이스 메타 `width_source = "set of .model wmin in pm3 file == bins.csv W set"`, 32개(nfet 20·pfet 12, `manifest.json`), 각 슬라이스 = 단일 finger(nf 1, ad = W·0.5 µm, pd = W + 2 µm), 27 °C, 축 = 기준 LUT 축. 기준 LUT(용량·잡음·mismatch)는 W = 5 µm 하나(REGEN_REPORT 28행, `w_ref_m` 5e-6).
- **엔진 레이아웃 전 사이징은 5 µm 슬라이스 하나만 읽는다**: `sizing/pre_layout_widths.py:14-22`(kind 마다 `w_ref_m` 슬라이스, 근거 주석 'DEC-91 (2)·오케스트레이터 결정 2026-10-07'), 실현 폭 슬라이스는 'DEC-89 재평가 몫'(MOD8, 계획 DEC-89 '미구현').
- 내 bench(`verify/sp/wbench.sp`, pfet L 4 µm, |VGS| 0.6 V, |VDS| 0.9 V, **27 °C**): |VTH| = 0.904(W 0.42)·0.908(0.54/0.55)·0.971(0.99/1.0)·1.044 V(5 µm). 판정자 0.895/0.956/1.029 V 는 **37 °C** 값이다(판정 bench `judge/t0/wbench.sp` `.temp 37`) -- 같은 경향, 온도 조건만 정정. 단위폭 전류 J(0.55 µm)/J(5 µm) = **22.8 배**(약반전). LUT 슬라이스 값은 같은 조건 SPICE 와 VTH 소수 7자리까지 일치(0.42 슬라이스 0.9041356 = SPICE 0.9041356) -- 효과는 LUT 에 이미 들어 있고 엔진이 그 슬라이스를 안 읽을 뿐이다.
- **folded front 점 −67 %**: 판정자 변환 netlist(`judge/conv/fc_frontA.sp`, 읽기만)를 **내 서보**(B 원 고이득 DC 되먹임, `verify/sp/fc_frontA_op.sp`)로 다시 돌림: M5~M10 가지 0.1066~0.1116 µA(엔진 0.323~0.336 µA, **−67 %**), M3 0.4697 µA(엔진 0.6594, −29 %), 입력 trim +6.25 mV(엔진 vin_p − vin_n +4.60 mV). 판정자 수치와 4자리 일치.
- **원인 분리**(`verify/sp/wbench8.sp`, pfet L 8 µm, MP 점 |VGS| 1.2349 V): 단일 소자 SPICE 로 MP(0.967 µm 다이오드)→M3(2.106 µm, |VDS| 0.448) 거울비 = **1.537**(-> I3 0.470 µA, 회로 SPICE 0.4697 과 일치). 5 µm 슬라이스 가정 거울비 = **2.169**(-> 0.663 µA, 엔진 0.659 와 일치). 각 소자가 속한 W bin 의 위 끝 슬라이스(1.0·3.0 µm)를 쓰면 1.458(−5 %). -> **−29 % 거울 오차는 5 µm 슬라이스 고정으로 거의 전부 설명되고, W bin 슬라이스로 대부분 없어진다**. 접힘 가지 증폭(I3 − I1 차이 전류)으로 −29 % -> −67 %.
- 판정: **재현**(수치 온도 조건 정정: VTH 3값은 37 °C).

### C5. 입력쌍 비대칭 -- **부분 재현**(현상은 재현, 원인 귀속은 정정)

- 내 front 점(C1, 출발 전류가 판정자와 다름, `res/c5_front_dump.json`): θ 전류 M3 3.128 µA 대 M4 1.583 µA(2:1), W M1 5.33·M2 2.69·M3 3.23·M4 1.63 µm -- **비율 2:1 입력쌍 + 2:1 거울**. 엔진 vin_p − vin_n = **−0.1 mV**(판정자 front 는 −8.4 mV, L1 ≠ L2).
- 내 SPICE(`verify/sp/ts_front_mine.sp`, finger = round(W/5 µm), bias = 엔진 노드 이상원, 서보 trim): **trim +20.1 mV** 필요, I1 2.81(엔진 3.13, −10 %)·I2 1.71 µA(엔진 1.58, +8 %), gain 85.2 dB, **GBW 6.970 MHz(spec 7 MHz FAIL −0.4 %), PM 69.2°(spec 70 FAIL)**.
- 귀속 정정: 내 점에서는 엔진 자신의 입력차가 −0.1 mV 라 'vin_p 독립 θ(SP-2)'가 비대칭의 통로가 아니다. 비대칭의 통로는 **θ 전류 M3·M4 가 따로인 비율 쌍**(물리적으로 정당한 회로 -- 비율 쌍 + 비율 거울은 이상적으로 계통 offset 0)이고, SPICE trim 20 mV 는 **좁은 폭(M2·M4 < 5 µm) 슬라이스 오차가 비율 쌍에서 계통 offset 으로 나타난 것**(C4 와 같은 원인). 판정자 점의 −8.4 mV 는 엔진 자체 입력차라 계통 offset 제약이 있었다면 잡혔을 몫이고, 그 위 +46 mV 는 마찬가지로 폭 오차 몫이다.
- 계획 사실(판정자가 안 본 것): 계통 offset 정의 = DEC-23 일반형 (나′) V_id* = (V_id,seal − V_id,0) + [(V_ref − V_out0) − ΔV_out(ΔW)]/A_dc (O-118 1번), 판정 자리 = 커널 + front W 재판정(U-108, O-119, DEC-74), 구현 = card DE-1 범위 (c). as-built `metrics/offset_systematic.py:1-14` 는 출력 오차/A_dm 옛 꼴이라 성분 (V_id,seal − V_id,0) 이 없다. 그리고 two_stage·folded spec 에 `offset_sys_mv` 제약이 없고 `input_dc` 는 `pending SP-2` -- V_id,0 이 정의되지 않는다.
- 판정: 현상 **재현**, 원인 'vin_p 독립 θ(SP-2)'는 **부분 반박**(주 원인은 폭 슬라이스 오차 C4; SP-2·offset_sys 미선언은 엔진 자신이 만든 입력차를 못 막는 별도 결함).

### C6. armA folded noise_excess_th 2.016 FAIL -- **재현**

- 내 SPICE(`verify/sp/fc_noise27.sp`·`fc_noise37.sp`, armA `fc_r7/sized.sp`, bias3 0.3425 V·Ibg 1.577 µA 이상원, vin_n 1.0 V, 서보 V(out) = V(Vg7), CL 1 pF, `.noise` 1 Hz, 1overf 제외 성분 전력합 / M1+M2): **27 °C 2.0161, 37 °C 2.0214**. 성분(입력쌍 = 1): M9+M10 0.645, M3+M4 0.371, 나머지 < 1e-4. 엔진 정의 = `metrics/noise_analysis.py` 머리 'noise_excess_th = Q_th / Q_in,th'(전력비, 입력 셀만의 열 성분 합) -- 같은 정의. spec `folded_cascode.sizing_spec.json` `noise_excess_th <= 2`.
- 판정: spec 문언 그대로 **FAIL(+0.8 %)** -- 재현. 판정 온도는 계획 DEC-96 (3) 'TT 27 °C 한 조건'이 이미 정했다(armA 설계 37 °C 는 그 밖).


## 케이스 D. 결정 후보 대안 분석 (실측 + 원칙 점검)

### D0. 판정자가 못 본 기존 결정 3건 (대안 비교의 출발점)

| 결정 | 원문 위치 | 내용 | 계획·design·코드 반영 |
|---|---|---|---|
| Q1-2 (ii) (2026-10-13, 사용자 "Q1-2는 (ii) 권고대로") | `wt/_drafts/user_decisions.md:313`, 결정 꾸러미 `wt/_drafts/engine/STEP2_DESIGN_GAPS_DECISION_PACKAGE.md:14` '결정 완료' | 41 §6.4-1 이득 L 하한의 'A_max 미상 → 비활성'을 41 §5.3.2 L-2와 같은 found_db 비례 g_i 로 대체(gain 선언 회로에서 활성) | **없음**: 계획·history `grep Q1-2` 0, design 41:1569 옛 문언 그대로, 코드 `search/iv_context.py:49-51` 옛 동작 |
| Q6-1 (A) (2026-10-13, 사용자 "Q3, Q5, Q6는 모두 권고대로 해") | `user_decisions.md:310`, 결정 꾸러미 :24·:440-452 | DEC-91 (2) 개정: 레이아웃 전 사이징도 소자 W가 속한 모델 W-bin 의 LUT 슬라이스를 읽는다(bin 경계 넘는 보간 없음, LR3 와 같은 꼴, W→슬라이스→W 고정점 상한 = bin 수). 같은 꾸러미에서 B(W 하한)·C(소자 DC 모델 오차 여유)·D(현행 + 보고)는 기각 | **없음**: 계획 DEC-91 (2) 옛 문언, `git log -S"Q6-1" -- docs` 0, 코드 `sizing/pre_layout_widths.py:14-22` 5 µm 고정 |
| O-140 D1~D3 (2026-10-26) + O-143 | `user_decisions.md:967-976` | folded PM ≥ 70°, gain_ss_db ≥ 70, GBW ≥ 10 MHz. 반영 시점 = LA-1 범위 안(계획 N6.14 범위 14) | 계획 반영됨, library data 는 LA-1 커밋 대기(그래서 integ-it12 spec 은 아직 `pending SP-3/4/5`) |
| DEC-96 (3) | 계획 DEC-96 | 합격 = TT 27 °C 한 조건 | 계획 반영됨 -- 판정자 '온도 선언 없음'은 계획 차원에서 이미 답이 있음 |

### D1 실측: Q1-2 (ii) 모사(엔진 파일 무수정, 프로세스 메모리 안에서 `iv_context._gain_inputs` 교체 -- `verify/v_d1.py`, `v_d4.py`)

| 실행 | 출발 L | find_front 결과 | 근거 |
|---|---|---|---|
| two_stage, as-built | 0.15 µm 전 소자 | front 0, s1 slsqp_4 ×2 | armC v4, 내 c1_front s1 |
| two_stage, Q1-2 (ii) 모사 | **M1~M4 0.231 µm, M5~M7 0.255 µm**(목표 g = 57 × 61.2/128.9 = 27.1 dB, 57 × 67.7/128.9 = 29.9 dB) | **front 0**. 첫 평가 gain 53.0 dB(as-built 33 dB 대비 +20 dB). 435 평가 중 **전 제약 c ≥ 0 인 평가 5개**(전력 99.6~111 µW, 면적 3.23~3.70e-9 m²) -- 그러나 전부 SLSQP 의 FD 열 평가(`origin stage fd`)라 수락 iterate 가 아니어서 front 에 못 들어감. 끝점 정지 power `converged`(수락 13, best 없음)·area `slsqp_8` | `res/d1_two_stage_ota.json`, S3 `evals.jsonl` 집계 |
| folded(O-140 spec 사본 `verify/o140/`), as-built | 0.15 µm 전 소자, gain_l `u9_value_not_certified` | front 0, slsqp_4 ×2, L-b 미기동 | `res/d4_fc_p0.json` |
| folded(O-140), Q1-2 (ii) 모사 | **20 µm 전 소자**(퇴화) | front 0, 평가 예산 소진 | `res/d4_fc_p1.json` -- 출발 충돌 `gain_l_6.4_1 gap 70.0`: 어느 L 앵커에서도 블록 이득 행이 정의되지 않아(`current_from_macro: stage_current_unavailable` -- θ 전류가 없어 `iv_gain_l._row` 가 None) `iv_gain_l.py:126-128` 이 '가장 긴 앵커로 닫기'를 했다 |

결론(실측): Q1-2 (ii) 는 **필요하지만 충분하지 않다**. two_stage 에서는 출발을 feasible 영역 가장자리까지 옮기지만(feasible 평가 5개 존재) 외층이 그 점을 수락하지 못하고, folded 에서는 블록 하나·θ 전류 미정이라 L 을 20 µm 로 퇴화시킨다. 새 결함 1건: **'평가 가능한 앵커가 하나도 없음'을 '목표 미달'과 같은 길(가장 긴 앵커)로 닫는다** -- fail-closed 위반(P1), 비활성 + 사유가 맞다.

### D1. 출발 L / L 탐색 수정

| 대안 | 물리 정합 | 손계산 일치 | design 단순성 | 실측 근거 | 원칙 점검 |
|---|---|---|---|---|---|
| (i) 인증 실패 시 found_db 비례 g_i(= Q1-2 (ii), 이미 결정) | 중: found_db 는 하한 추정이라 배분 비만 씀; 블록 하나 L 을 전 소자에 거는 규칙(iv_gain_l 머리)은 캐스코드·거울까지 같은 L 로 묶음 | 중: 교과서 순서(이득 → L)와 같은 방향 | 높음(필드 소비 1곳) | two_stage L 0.15 → 0.23~0.255, 첫 평가 +20 dB, feasible 평가 5; folded 퇴화 20 µm | graph: 기존 필드 `gain_checks.found_db` READS(새 cache 0) ✓. EP-7: 출발값 용도 ✓. ⚠ P1: 앵커 전부 평가 불가 시 '가장 긴 앵커'로 닫는 현 동작은 fail-closed 위반 -- 함께 고쳐야 함 |
| (ii) LR10 L-b 를 feasible 점 없이 기동 | 중 | 낮음(이산 이동 탐색, 손계산 아님) | 낮음: L-b 정의(front 점 다듬기)를 바꿈 | 없음 | ⚠ 승인 계획 v6.38.1 재검증 5 G-1('외층 봉인 스냅샷의 표지는 기록만, 층 0 을 다시 열지 않는다(LR10)')과 충돌 -- O-162 승인 문언을 바꿔야 함. 권고 안 함 |
| (iii) 출발 사다리에 L 칸 여러 개 | 중 | 낮음 | 낮음: 어느 칸을 넣을지 규칙이 필요 -- 근거 없는 선택 규칙 = 상수·규칙 발명 위험 | 없음 | ⚠ P1(규칙 발명), LA-1 gain bin·DP 와 기능 중복(정의 둘) |
| (iv) GB4 인증 조건 자체를 고침 | 높음(인증된 상한) | -- | 매우 낮음 | Π/N_S = 1.2e15(O1), 135(OUT), folded 4.5e45 -- 격자 전수로는 불가. 격자 축소는 상한이 아님(`block_gain_bound.py:7`) | 계획 F-LA5 가 이미 '그래서 역산 우선'으로 정리. 권고 안 함 |
| (v) **LA-1(승인 범위) -- 층 0 역산 우선 L(DEC-71 (4)(b)), 탐색 개방(D-1 (A′)·R5′), 매크로 gm → θ 전류 전파(범위 13, B85), front ≥ 1 완료 조건 9 (a)** | 높음(스펙 → gm → gm/ID → ID → 목표 gm/gds → 같은 bin L, 블록마다·소자마다) | 높음(교과서 순서 그대로) | 중(이미 design 대상) | 이번 실측이 보여준 두 막힘 -- (가) L 최소 칸 고착, (나) folded θ 전류 미정(`stage_current_unavailable`) -- 이 범위 1·13 의 대상과 일치. 미구현이라 효과 미측정 | ✓ 승인 계획 그대로(계획 먼저 원칙 충족). |
| (vi) 외층이 이미 계산한 FD 열 feasible 평가를 비지배 필터 후보로 받기(새 대안) | 높음(실제 봉인·전 제약 통과 점) | -- | 중 | two_stage 모사 실행에서 feasible 평가 5개가 버려짐 | graph: 기존 평가 캐시(`sctx.cache`, 승인 구조)의 결과를 쓰는 것이라 새 cache 아님 -- 단 외층 알고리즘 변경이라 LA-1 범위 밖. ⚠ 계획 개정 필요, LA-1 뒤 재측정 후에만 판단 |

**권고**: (v) LA-1 을 주 경로로 그대로 진행 + (i) Q1-2 (ii) 를 계획·design 에 **전파**(새 결정 아님 -- 2026-10-13 승인분)하되 '평가 가능한 앵커 0 → 비활성·사유' fail-closed 를 같은 변경에 넣는다. 담당 card: §6.4-1 은 층 0 무동작 회로와 '층 0 조립 실패 경로'(LA-1 범위 6 LA-Q2 (b))의 출발에 남으므로 LA-1 범위에 넣는 것이 맞다(같은 파일 `start_intervals`·`iv_*` 를 범위 13 이 이미 고침). (vi) 는 LA-1 뒤 CMP 재실행에서 같은 현상(버려진 feasible 평가)이 남을 때만 올린다.
- **LA-1 범위 겹침**: (v) 그 자체. (i) 은 LA-1 범위에 문언이 없음(전파 필요). (ii) 는 LA-1·G-1 과 충돌.
- **계획 개정 필요**: 예 -- 작은 개정(v6.38.2): ① Q1-2 (ii) 를 DEC(§6.4-1 대응 행)와 LA-1 범위에 적기 ② fail-closed 보충. 원래 취지와 다름: 아니오(사용자 결정 그대로 전파).

### D2. 폭 효과

| 대안 | 물리 정합 | 손계산 일치 | design 단순성 | 실측 근거 | 원칙 점검 |
|---|---|---|---|---|---|
| (i)=(iv) **소자 W 가 속한 W-bin 슬라이스(= Q6-1 (A), 이미 결정)**, bin 경계 넘는 보간 없음, W→슬라이스→W 고정점 상한 = bin 수 | 높음 -- 슬라이스 = PDK W bin 경계(wmin 집합), SPICE 와 VTH 7자리 일치 | 높음(같은 LUT 읽기, 칸만 바뀜) | 중: 커널 W writer 안 고정점, LUT memo 키에 W bin | MP→M3 거울비: 5 µm 고정 2.169(+41 %) → bin 위 끝 슬라이스 1.458(−5 %), 참값 1.537. 남는 −5 % 는 bin 안 위치 차(bin 안 보간용 아래 끝 슬라이스가 대부분 bin 에 없음 -- 0.55 µm 슬라이스는 경계 규칙상 아래 bin 소속) | graph: writer 하나(dc_widths) 안 고정점 ✓, LUT memo 는 승인 예외(U-87) 키 확장 ✓. ⚠ 잡음·mismatch·용량 열은 5 µm 기준 LUT 에만 있다(u3-lut-pdk-record:126) -- DC 만 바뀌고 AC·잡음은 기준 폭 환산이 남음(기록 필요). LR3 와 대칭 -- bin 안 연속 보간을 하려면 'bin 아래 끝 + 격자 한 칸' 슬라이스 추가 생성 필요(LR3 의 불연속 경계 규칙과 같은 꼴, 새 상수 없음) |
| (ii) W 하한 = LUT 기준 폭(5 µm) 또는 슬라이스 간 ΔVGS ≤ tol_V 인 W_floor | 중: 모델 유효 영역으로 거르는 것이지 물리 제한 아님 | -- | 높음 | 결정 꾸러미 측정: nmos 3 µm 에서도 8~15 mV → 사실상 W ≥ 5 µm, 작은 전류 소자 전류 ~14 배. armA folded 가 이 길(W ≥ 5 µm 수동)로 22.8 µW, 엔진 front 2.2 µW | ⚠ '제한은 물리 근거 있을 때만'(규칙 물리 우선 원칙) 위반 소지, 2026-10-13 기각안(B) |
| (iii) MOD8 재평가에서만(현행) | 낮음(레이아웃 전 front 가 뒤집힘) | -- | 높음 | 이번: two_stage front GBW·PM 경계 FAIL, folded 가지 전류 −67 %. DEC-89 '미구현' | ⚠ P0 위반(물리적으로 안 되는 점을 front 로 냄), 2026-10-13 기각안(D) |
| (v) 소자 DC 모델 오차를 봉인 여유로 흡수 | 중 | -- | 중 | -- | ⚠ DEC-72 '측정 선언값' 문언과 형태 다름, 과설계(NFR-5) -- 2026-10-13 기각안(C) |

**권고**: (i)/(iv) = Q6-1 (A) 를 계획 DEC-91 (2) 개정으로 **전파**하고 독립 card 로 LA-0 기준선 **앞**에 둔다(커널 W 값이 바뀌므로 LA-1 변화표의 원인 귀속을 깨지 않으려면 기준선 전에 들어가야 함). 같은 card 에 'W-bin 아래 끝 슬라이스 추가 생성' 여부를 design 에서 재고 결정(LR3 대칭, 새 상수 없음).
- 원래 취지와 다름: **예** -- 현 계획 DEC-91 (2) 문언·as-built(오케스트레이터 결정 2026-10-07 'w_ref 슬라이스')와 다르다. 단 2026-10-13 사용자 결정(Q6-1 A)과는 같다 -- 표시는 '계획 문언과 다름, 사용자 결정 Q6-1 과 일치'.
- LA-1 범위 겹침: 없음(LA-1 은 'W = 커널 W 계산 블록과 같은 함수'를 READS 할 뿐 -- 이 card 가 그 함수를 바꾸면 LA-1 은 자동으로 따른다).
- 계획 개정 필요: 예(DEC-91 (2), N6 card 추가, LUT 체크리스트에 W-bin 끝 슬라이스).

### D3. SP-2 입력 DC 와 계통 offset

| 대안 | 물리 정합 | 손계산 일치 | design 단순성 | 실측 근거 | 원칙 점검 |
|---|---|---|---|---|---|
| (가) `input_dc` 두 입력 공통값 선언(SP-2 값 = 사용자) | 높음(차동 증폭기 동작점 정의) | 높음 | 높음(spec data) | V_id,0 이 정의돼야 DEC-23 (나′) 첫 성분이 계산됨 | 바이어스는 spec 에서 유도 ✓. ICMR(O-119 (1) icmr_v) 창 안 값이어야 함 -- 값은 사용자 |
| (나) `offset_sys_mv` 제약 선언(값 = 사용자) + DE-1 (c) 일반형 (나′) | 높음 | 높음 | 중(DE-1 이 이미 범위) | 판정자 front 의 엔진 자체 입력차 −8.4 mV 는 이것으로 잡힘. **내 front 는 엔진 입력차 −0.1 mV 인데 SPICE trim +20.1 mV** -- 이 몫은 (가)(나)로 못 잡고 D2 로만 잡힘 | Q3-3(2026-10-13): offset_sys 제약은 출력 기준 DC 선언 회로에만 -- two_stage·folded 둘 다 `node_voltage_targets_v` 있음 ✓. as-built `metrics/offset_systematic.py` 는 옛 꼴(성분 V_id,seal − V_id,0 없음) -- DE-1 전에는 선언해도 못 잡음 |
| (다) vin_p ≡ vin_n θ 묶음 | **낮음** -- 개루프 고이득 증폭기에서 출력 DC 를 정하는 자유도가 사라져 봉인 불가 | -- | -- | -- | ⚠ P0 위반. 기각 |
| (라) 대칭 태그로 입력쌍 묶기 | -- | -- | -- | -- | ⚠ analog-grammar·topology 태그 금지 원칙 위반. 기각 |
| (마) 그대로 두고 front oracle(DEC-98)에 맡김 | 중 | -- | 높음 | 탐색이 비율 쌍·입력차를 전력 절감에 씀(두 실행 모두) | 판정은 fail-closed 지만 탐색 낭비 |

**권고**: (가)+(나)(값은 사용자 spec, 계획 개정 없음 -- DE-1 범위 (c)·U-108·O-119 그대로) + D2 를 실제 SPICE 계통 offset 의 주 대책으로 함께. 비율 쌍(2:1 입력쌍 + 2:1 거울) 자체는 물리적으로 정당한 회로라 막을 근거가 없다(막으면 규칙 발명).
- LA-1 겹침: 없음(DE-1 소유). 계획 개정: 불필요. 원래 취지와 다름: 아니오.

### D4. folded spec·온도

- SP-3/4/5: **이미 결정**(O-140 D1~D3 -- PM ≥ 70°, gain ≥ 70 dB, GBW ≥ 10 MHz; 반영 = LA-1 범위 14, O-143). 판정자 '미정'은 integ-it12 data 기준이라 생긴 오해. 새 질문 불필요.
- 실측(O-140 spec 사본, `verify/o140/`): as-built 엔진 folded front 0(slsqp_4, L 0.15 µm 고착) -- O-140 D7 의 '지금 넣으면 as-built 층 0 결함으로 front 0' 근거와 일치. armA folded(내 SPICE 27 °C): gain 77.7 dB PASS, **GBW 7.37 MHz FAIL(< 10), PM 50.3° FAIL(< 70)**, noise_excess_th 2.016 FAIL -- 결정된 spec 기준으로 armA folded 는 세 항목 FAIL.
- 온도: **이미 결정**(DEC-96 (3) 합격 = TT 27 °C 한 조건; offset·trim 잔여만 T-29 온도 범위). armA 의 37 °C 설계는 이 조건 밖. 새 질문 불필요.
- 남는 질문(선택): CMP-1 folded 비교를 O-140 spec 으로 다시 할지(→ 의미 있는 시점은 LA-1 뒤).

### D5. 'front 없을 때 최선점 SPICE 진단'

| 대안 | 소비자 | 원칙 점검 |
|---|---|---|
| (가) 엔진에 새 기능 | 없음(DEC-98 판정 대상 = 시작점·front 점; LA-1 완료 조건 9 (a) '실현 불가 독립 근거'는 최선점 하나로 증명되지 않음) | ⚠ 만들면 배선 -- 소비자 없이 만들면 위반 |
| (나) EO-1 생산자(승인, 대상 '엔진 점(시작점·front 점)')의 대상에 '최선점' 추가 + LA-1 범위 9 보고(층 0 무동작·성능 판정 보류)에 진단 칸 | LA-1 범위 9 보고 경로(출력 전용 선언) | 계획 개정 필요(EO-1 대상, LA-1 범위 9 칸) |
| (다) **엔진 무변경 -- CMP-1 평가 card 도구에서만**(EO-1 병합 뒤 그 생산자를 불러 씀; 지금의 `judge/eng2spice.py` 는 일회용) | CMP-1 보고(평가 card 의 산출) | ✓ CMP-1 '엔진 코드 변경 0' 그대로, 생산자 둘(정본 둘) 방지는 EO-1 병합 뒤 그것을 쓰는 것으로 |

**권고**: (다). 근거: 이번 진단에서 값어치가 있었던 것은 '최선점 SPICE'(엔진·SPICE 모두 33 dB -- 평가가 아니라 탐색 문제임만 확인)보다 'armA 해를 엔진 θ 로 옮긴 평가'였고, 이것은 평가 card 일이다. (나)는 LA-1 뒤에도 front 0 회로가 남을 때 소비자(범위 9 보고)를 정해 다시 올린다.


## 요약표 (보고 맨 앞 표와 같음)

| 주장 | 판정 | 핵심 근거 |
|---|---|---|
| C1 armA two_stage → 엔진 feasible, 출발점이면 front 1 | **재현** | 내 SPICE 전류로 다시 만든 θ: sealed·전 제약 c > 0, 전력 128.27 µW = SPICE 71.26 µA × 1.8; find_front → front 1(92.6 µW, GBW 7.002 MHz·PM 70.01° 경계) |
| C2 원인 사슬 | **재현** + 정정 | 코드 7고리 file:line 확인, N_S = 13,829,760(`search/count_budget.py:16-23`, LUT 32 슬라이스 격자 합), Π = 1.7e22/1.9e9. ★ 고리 ③은 2026-10-13 사용자 결정 Q1-2 (ii)가 계획·design·코드에 전파되지 않은 결함 |
| C3 평가 1~3 % | **재현**(offset 미확인) | gain +0.40 dB, GBW +2.0 %, PM −0.46°, noise +1.2 % |
| C4 좁은 폭 | **재현**(온도 조건 정정) | VTH 3값은 37 °C 값(27 °C: 0.908/0.971/1.044 V). 슬라이스 = PDK W bin 경계. 거울비 5 µm 가정 2.169 대 참 1.537 대 W-bin 슬라이스 1.458 |
| C5 입력쌍 비대칭 | **부분 재현** | 현상(2:1 비율 쌍) 재현, 내 점은 엔진 입력차 −0.1 mV 인데 SPICE trim +20.1 mV → 주 원인은 폭 오차(C4), SP-2 는 부차 |
| C6 armA folded noise 2.016 FAIL | **재현** | 27 °C 2.0161, 37 °C 2.0214 |

| 결정 | 권고 | LA-1 겹침 | 계획 개정 | 원래 취지와 다름 |
|---|---|---|---|---|
| D1 | LA-1 그대로 + Q1-2 (ii) 전파 + '평가 가능 앵커 0 → 비활성' fail-closed | (v) 자체가 LA-1, (i) 문언 없음, (ii) G-1 과 충돌 | 예(소: 전파·보충) | 아니오 |
| D2 | Q6-1 (A) W-bin 슬라이스 전파, LA-0 앞 독립 card | 없음 | 예(DEC-91 (2), card) | 계획 문언과 다름(사용자 결정 Q6-1 과는 일치) |
| D3 | input_dc 공통값 + offset_sys_mv 선언(값 사용자), DE-1 (나′) | 없음(DE-1) | 아니오 | 아니오 |
| D4 | 새 질문 없음(O-140·DEC-96 (3) 이미 결정) | LA-1 범위 14 | 아니오 | 아니오 |
| D5 | 엔진 무변경, CMP-1 도구에서만(EO-1 뒤 그 생산자 사용) | 없음 | 아니오 | 아니오 |

## 재확인자 자기 점검 (실측 / 자기보고 / 안 함)

- 엔진·armA·armC·judge·계획·design·spec 무수정: `git -C wt/integ-it12 status --short` 빈 출력(실측). spec 실험은 `verify/o140/` 사본, Q1-2 모사는 프로세스 메모리 안 함수 교체(파일 무수정).
- graph 단일 정본 점검: 권고 대안마다 새 cache·사본·sctx 슬롯 없음을 표에 적음(자기보고 -- 구현이 아니라 대안 검토라 lint·G-10 계수는 안 함).
- 회로 이름을 규칙 근거로 쓰지 않음: 대안은 W-bin·found_db·KVL 등 구조·PDK 근거로만(자기보고).
- heldout·논문 값 미사용(실측: 입력은 armA 결과·library spec·PDK·LUT 뿐).
- 안 한 것: offset_excess SPICE 독립 측정, 판정자 two_stage front 점(−8.4 mV, +46 mV)의 SPICE 재측정(내 front 점으로 대신), 코너·온도 견고성 재측정(판정자 케이스 2), Q6-1 W-bin 슬라이스를 엔진에 모사한 front 재실행(LutAccess 교체가 커서 범위 밖).
- 기록 형식: 새 스크립트 파일 3개(`app.py`·`vbuild.py`·`noise_parse.py`)를 bash heredoc '새로 만들기'(`cat >`)로 만들었다 -- append 가 아니라 규칙 위반은 아니지만 이후는 Write 로 바꿨다. 증거 파일 추가는 전부 Python 바이너리 append.

