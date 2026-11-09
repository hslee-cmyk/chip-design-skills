# ngcc_3stage_ff -- 동작 조건·정지 원인·ICMR 기능 기준 권고 (독립 회로 분석, 2026-11-01)

- 대상: `skills/analog-gmid-design/assets/library/ngcc_3stage_ff.{topology,sizing_spec}.json`, 원문 `assets/library/sources/ngcc_3stage_ff__lee_2007/source.pdf`
- 원문: J.-S. Lee 외, "A Design Guide of 3-stage CMOS Operational Amplifier with Nested Gm-C Frequency Compensation", JSTS 7(1) pp.20-27, 2007, https://doi.org/10.5573/JSTS.2007.7.1.020 (로컬 `.../sources/ngcc_3stage_ff__lee_2007/source.pdf`, 아래 쪽 = 저널 쪽 / PDF 쪽)
- 엔진: master `08048939`, code_fp `2c7cbca4…99db1`. 실행만(소스 수정 0), library 경로 그대로, LUT = `lut_v2_location.json` → `C:\…\lut_data\sky130_lut_v2\manifest.json`(load_lut_set verify_midpoints r2 대조 통과)
- 저장소·계획·topology·spec·git 쓰기 0. what-if structure.json·SPICE 작업 파일은 TEMP와 이 폴더의 `ngcc_3stage_ff_files/`에만.
- 스크립트·로그(`ngcc_3stage_ff_files/`): `topology_connectivity.md`(net 표), `fig3_zoom.png`(원문 Fig. 3 확대), `run_stage_ab.py`→`engine_run.log`, `run_whatif_chain*.py`→`whatif_chain*.log`, `char_gmid.py`·`char_table.py`→`char_gmid.log`, `icmr_servo_spice.py`→`icmr_servo.log`·`icmr_<case>.csv`.

## 0. 요약

| 항목 | 결과 | 판정 |
|---|---|---|
| 토폴로지 | PMOS 입력 차동쌍(M1·M2)+NMOS 미러 부하(M3·M4) → NMOS CS(M8)+PMOS 미러(M9·M10)+NMOS 전류원(M11) → NMOS CS(M13)+PMOS 전류원 부하(M12) 3단, NGCC feedforward 2개(FF1 = M5·M6B·M6A·M7, ND→Vout; FF2 = M14, V1→Vout), 보상 Cm1(V1–Vout)·Cm2(V2–Vout) | 맞음(확신 높음) -- connectivity 16/16 소자·3/3 수동소자 원문 Fig. 3과 일치 |
| 단계 A 정지 | `review_needed|dc_role_unresolved_group||M14,M8|…dc_role 사실이 필요하다` (engine_run.log) | 사용자 선언(structure.json `dc_role` 사실) -- topology 결함 아님 |
| 사실을 넣으면(what-if) | 단계 A·B ok, 탐색 159 평가(봉인 133) **front 0** -- `gain_ss_db` 행 133/133 실패(c_max −4.17), L 전 소자 150 nm 고정, `slsqp_4` 중단 | 엔진 재작성 범위(L 탐색이 front 점에서만 열림) -- spec 결함 아님(SPICE L = 1 µm 손 사이징에서 117~120 dB) |
| ICMR | SPICE servo(원칙 3 DC, N3.8 측정 구성): 창 = [0 V(레일 자름), 0.674~0.693 V(M0 VDS = VDSAT)], 폭 0.674~0.693 V ≥ 0.6 V | 영역 행이 끝을 정함. 점별 증분 DC 이득 기준은 두 시험점 모두 **창 끝을 정하지 못함**(⚠ §3.4) |
| ICMR 기능 기준 권고 | 기준점 = 봉인점 servo 동작점, 허용 저하 = 그 점 이득 − spec `gain_ss_db` 하한(value_from_constraint) ⇒ 창 안 모든 점 A(x) ≥ 111 dB | 조건부 맞음(§3) |

## 1. 토폴로지 직접 분석 (원칙 14 -- netlist 연결 + 원문만)

### 1.1 net 기준 연결 (`ngcc_3stage_ff_files/topology_connectivity.md`, `tools`=`assets/topology_to_markdown.py`)

| Net | 단자 | 해석 |
|---|---|---|
| TAIL | M0.d, M1.s, M2.s | PMOS 차동쌍 공통 source, M0(gate VBP) = tail 전류원 |
| ND | M1.d, M3.d=g, M4.g, M6B.g | 입력쌍 한쪽 drain = diode M3 → 미러 기준 + FF1 탭 |
| V1 | M2.d, M4.d, M8.g, M14.g, Cm1 | 1단 출력(고임피던스 이득 노드) |
| NP | M8.d, M9.d=g, M10.g | 2단 PMOS 미러 기준(diode M9) |
| V2 | M10.d, M11.d, M13.g, Cm2 | 2단 출력(고임피던스), M11(gate VBN) = 전류원 |
| NX | M5.d, M6A.d=g, M6B.d, M7.g | FF1 내부: M5(VBP) 전류 − M6B(ND 복사) 전류 = diode M6A 전류 → M7 구동 |
| Vout | M7.d, M12.d, M13.d, M14.d, Cm1, Cm2, CL | 출력: M12(VBP) 전류원 부하, 세 갈래(M7·M13·M14) 합류 |

원문 Fig. 3(저널 p.24 / PDF p.5 오른쪽 아래, `ngcc_3stage_ff_files/fig3_zoom.png`)과 소자별로 대조: 일치(16/16, 수동 3/3). **대기열 후보 0.**

### 1.2 신호 경로·극성 (연결에서 유도, 확신 높음)
- 주경로: Vinp↑ → I(M2)↓·I(M1)↑ → M3/M4 미러로 V1↓ (1단 반전) → I(M8)↓ → M9/M10 미러 I(M10)↓ → V2↓ (2단 비반전) → I(M13)↓ → Vout↑ (3단 반전). 전체 Vinp → Vout 비반전, Vinn 반전. 단위 이득 되먹임 = Vout → Vinn.
- FF2(M14, gmf2): V1 → Vout 반전 = 주경로 V1 → V2 → Vout(비반전·반전 = 반전)과 같은 부호. 원문 NGCC 조건 gmf2 = gm2 (Table 1 '(3-stage) Condition: gmf,i = gm,i', 저널 p.21 / PDF p.2).
- FF1(M5·M6B·M6A·M7, gmf1): 작은 신호 i(M6B) = (gm6B/gm3)·i1, v(NX) = −i(M6B)/gm6A, i7 = −(gm7/gm6A)·i(M6B). 원문 비율 M3:M6B = 1:1, M6A:M7 = 1:2(Fig. 3 표지) → |i7| = 2·i1 = gm1·v_id, 즉 gmf1 = gm1이 **미러 비율로 자동 성립**(i1 = gm1·v_id/2). 부호: Vinp↑ → i1(M1)↑ → ND↑ → NX↓ → I(M7)↓ → Vout↑ = 주경로와 같은 부호.
- 엔진 단계 A 유도 결과도 같다(whatif_chain.log: FF `ND->Vout` cells M6B·M7, load M6A, bias M5, sign +1 / `V1->Vout` M14 sign −1(V1 기준), loop `loop:M8:V1` compensation_internal).

### 1.3 DC 동작 조건 (물리 결정자)
- **M6A 전도 조건**: I(M6A) = I(M5) − I(M6B) > 0 (O-205 P5: 전도 = ID > 0). I(M6B) ≈ I(M1)·(W6B/W3) 이므로 I(M5) > I(M1)·(W6B/W3)가 물리 조건이다. 깨지면 NX가 바닥으로 내려가 M7 꺼짐 → FF1 소멸(영점 상쇄 깨짐 → PM 붕괴). 엔진은 ID > 0 행으로 잡는다(별도 선언 불필요).
- **출력 KCL**: I(M12) = I(M7) + I(M13) + I(M14). V1은 I(M8)(= I(M11)·W9/W10)이 정하고 그 V1이 I(M14)도 정하므로, I(M13) = I(M12) − I(M7) − I(M14) > 0이어야 V2가 정의된다.
- **바이어스**: `bias_inputs` VBP(M0·M5·M12 공통 gate), VBN(M11). 세 PMOS 전류원이 같은 VSG라 전류비 = W/L비(+VDS 변조).

### 1.4 입력 공통모드가 움직일 때 무엇이 먼저 무너지나 (ICMR 물리)
servo 구성(출력 고정, 계획 N3.8 'ICMR 측정 구성', P:729)에서는 V1·V2·ND가 거의 고정되고 TAIL = Vcm + VSG(M1)만 움직인다.
- **위쪽 끝**: Vcm↑ → TAIL↑ → VSD(M0)↓ → **M0(tail)가 먼저 triode**(VSD0 = VDSAT0). 식: Vcm_max = VDD − VDSAT(M0) − VSG(M1). 그다음 tail 전류가 줄고(실측 Vcm 0.6 → 1.2 V에서 I(M0) 6.65 µA → 3.7 nA, L = 0.5 µm) gm1 ∝ I(약반전) → GBW(ω1 = gm1/Cm1)가 무너진다.
- **아래쪽 끝**: Vcm↓ → M1·M2 VSD = TAIL − ND(또는 V1)↓ → **M1/M2가 triode**. 식: Vcm_min = VGS(M3) + VDSAT(M1) − VSG(M1) ≈ VTN + 2·VDSAT − |VTP|. sky130 |VTP| ≈ 0.92 V > VTN ≈ 0.64 V라 이 값이 0 V 아래(실측 외삽 ≈ −0.37 V) → **레일 자름(DEC-96 (2), N3.8 '레일 자름' P:729)이 아래 끝 = 0 V**.
- 원문 식 (9) ICMR = VDD − 5·VDSAT − VTH (저널 p.24 / PDF p.5, 'ICMR of PMOS differential pair with NMOS active load') = 위 두 끝의 차(입력 VDSAT = V, 부하·전류원 VDSAT = 2V, VTH = NMOS 부하 VTN)와 같은 정의 -- **원문 ICMR은 입력단 전 소자 포화 범위(폭)** 이고 이득 저하 정의는 원문에 없다. 식 (10) 'ICMR ≥ VDD/3 보장 조건'(p.24) → spec `icmr_v ≥ 0.6`(1.8 V 기준, spec :98-109).
- sky130 1.8 V 귀결: 아래 끝이 레일에 잘리므로 실제 폭 = 위쪽 끝 = 1.8 − VDSAT0 − VSG1. VSG1 ≈ 0.95~1.0 V(pfet |VTP| 큼)라 폭 ≈ 0.67~0.70 V → 0.6 V 요구 대비 여유 0.07~0.09 V뿐. **입력쌍 gm/ID를 키워 VSG1을 낮추고 M0 VDSAT를 작게 하는 것이 ICMR의 물리 결정자**(원문 '입력 VDSAT = 부하의 절반' 규칙과 같은 방향, p.23-24).

## 2. 엔진 정지·front 공백 진단 (실측)

### 2.1 master 그대로 (engine_run.log)
```
stage A status=review_needed exit=2
review_needed = ["review_needed|dc_role_unresolved_group||M14,M8|같은 gate·source 묶음에 diode 기준이 없고 gate 가 신호 넷이라 DC 역할을 구조로 못 가른다 -- dc_role 사실이 필요하다"]
declared_comparison = "not_performed: ngcc_3stage_ff.structure.json absent"
stage B status=review_needed exit=2 (diagnostic: verdict ok, gain blocks unknown -- grid_product_over_budget)
```
- 원인: M8·M14가 같은 (gate V1, source gnd) 묶음이고 묶음에 diode 기준이 없으며 gate가 교류접지가 아님 → graph CONTRACT 4.4 (2) 마지막 행 'signal, review_needed (J-U3-c)'(`gmid_engine/graph/CONTRACT.md:213-229`). 엔진 test가 이 회로를 예로 고정(`gmid_engine/tests/graph/test_s1v_build.py:251-260` -- 사실 M8·M14 = signal이면 사라짐).
- 물리 판정(연결만): V1 = M2·M4 drain = 1단 고임피던스 출력, 그 전압은 v_id에 따라 움직인다 → M8(gm2)·M14(gmf2) 모두 **신호 전달 소자(signal)**. 바이어스 미러가 아님(기준 diode 없음, gate가 바이어스망이 아님). 확신 높음.
- **분류: 사용자 선언(structure.json ratified 사실)**. topology 연결 문제 아님(대기열 후보 아님), 엔진 결함도 아님(설계상 확인 요청). 선택적 재작성 후보(⚠ 원칙 12 일반성 관점): 'gate 넷이 신호 블록 키(이 회로 V1 = stage 1 블록 키)인 diode 없는 묶음 = signal derived'로 유도하면 사실 없이 풀린다 -- 다만 그 규칙의 library 전수 n/N은 재지 않았다(미측정, 권고 아님·기록만).

### 2.2 사실을 넣은 what-if (TEMP structure.json, 승인 표지 `WHATIF-icmr4-not-user-approved`; whatif_chain.log·v4.log)
- 단계 A ok(applied_facts dc_role M8·M14), 단계 B ok(verdict ok), ff_ratio_candidates 2건(`r_ff = G_ff / gm_in(B_b) = 1` -- 값은 spec 선언 때만 제약).
- find_front: 평가 159(봉인 133·정의역 밖 26), 18.7 s, **front = ()**, 층 0 = `feasibility_only`(`w_bounded_by_area_budget`), sweep `stop: slsqp_4`·`candidate_failure` 다수, `l_search LR10 stops []`.
- 봉인 평가 133개 행별 통과 수(whatif_chain_v4.log 47-54행):

| 행 | 통과 | c 최대 | 뜻 |
|---|---|---|---|
| ss:0 gain_ss_db ≥ 111 | **0/133** | −4.17 | 이득 미달(어느 점도 근처에 못 감) |
| ss:1 gbw_ss_hz ≥ 10 MHz | 0/133 | −0.13 | 미달 |
| ss:2 pm_ss_deg ≥ 63.4 | 0/133 | −0.40 | 미달 |
| ss:5 noise_excess_th ≤ 2 | 0/133 | −0.51 | 미달 |
| spec area ≤ 0.025 mm² | 2/133 | — | 층 0 출발점 c = −1.28e7(M5 ln IDu −23.5 → W 수십 mm, PMOS 전류원 깊은 약반전) |
| ss:3 icmr_v ≥ 0.6 | 133/133 | 11~13 | as-built 옛 정의로 통과 -- O-206 기준 미선언이면 '정의 불능'이어야 함 |
| ss:4 offset_excess | 133/133 | — | 통과 |

- **L 고정**: 모든 평가 θ의 L = 1.5e-7 m(9개 L 동치류 모두, cells (0,…,0)). L-b는 front 점에서만 칸을 옮긴다(`gmid_engine/search/l_bin_search.py:1-12` docstring '`solved` = front 에 남은 SolveResult') → front 0이면 L이 최소 칸을 벗어나지 못함 → 111 dB 이득에 도달 불가 → front 0의 닫힌 고리.
- spec 실현 가능성(SPICE, §3.2 손 사이징 시험점): L = 0.5 µm → 106~108 dB(미달), **L = 1 µm → 117~120 dB(통과)**. 원문도 L = 0.5 µm(0.18 µm 공정 최소의 약 3배, 저널 p.24)로 111 dB(Table 5 p.25) -- sky130에서 같은 '최소 L 배수' 꼴은 이득이 모자라고 L ≈ 1 µm면 충분. ⇒ **spec(111 dB) 문제 아님, 엔진 탐색 구조 문제.**
- **분류: 엔진 재작성 범위** (원칙 8 -- as-built 동작은 근거 아님, 범위 기록만):
  1. L 탐색이 front 존재에 묶임 → 이득 요구가 긴 L을 요구하는 회로에서 front 0 고정(계획의 이득 → L 역산 규칙과의 대조는 이 분석에서 원문 행을 끝까지 확인하지 않음 -- 'agent 인용' 수준, 재작성 card에서 확인 필요).
  2. 층 0 출발점이 PMOS 전류원 깊은 약반전(ln IDu −23.5)·면적 1.3e7배 위반 점 -- `feasibility_only`.
  3. as-built `inversion_floor` 행이 아직 있음(P-7 철회 O-207 → 삭제 대상).
  4. as-built `icmr_v` 행이 기능 기준 없이 값을 냄(O-206: 미선언 = 정의 불능 → 재작성 범위, SF-1 로더 칸·DE-1 (e) 함수 착수 조건 -- 계획 P:1329·P:1333).
  5. power 축 `not_computed: supply_current_dc_needs_counted_rails_declaration`(DEC-78) -- 전력 축이 필요하면 사용자 선언(§4).

### 2.3 '동작'시키는 데 필요한 조치 (순서)
1. **사용자**: structure.json `dc_role` 사실 2건 승인(M8 = signal, M14 = signal; 근거 §2.1) → 단계 A·B ok(what-if로 확인).
2. **사용자**: ICMR 기능 기준 spec 칸 선언(§3 권고) -- 없으면 O-206에 따라 `icmr_v` 정의 불능(재작성 뒤 엔진 기준).
3. **엔진(card, 재작성 범위)**: L 탐색을 front 존재와 분리(이득 요구 → L 칸 개방) · 층 0 출발점 · `inversion_floor` 삭제 · O-206/O-211 ICMR 기능 기준(SF-1 칸 로더, DE-1 (e) 함수, `graph.ss_nodal` writer 선행).
4. **oracle**: front 점마다 servo `.dc` + 점별 `.tf`(§3.2 스크립트와 같은 구성)로 ICMR 확정, `.ac` 로 gain·GBW·PM.
5. 선택 선언(§4): input_dc(SP-2), 전력 축 레일, front 점 규칙(AC-3) 등.

## 3. ICMR 기능 기준 선언 권고 (O-206·O-211)

### 3.1 무엇을 정해야 하나
계획 N3.8 'ICMR 기능 기준'(P:729, O-206·O-211): 창 안 각 DC 점의 증분 DC 이득 ∂Vout/∂Vid가 **기준점 대비 선언 허용 저하 이내**, ICMR 끝 = 영역 행 끝 ∧ 기능 기준 끝, 미선언 = 정의 불능. 사용자가 정할 칸 = (기준점, 허용 저하).

### 3.2 SPICE 실측 (servo, 손 사이징 시험점 -- spec 값 아님)
- 측정 구성 = N3.8 servo: Vinp = Vcm + e/2, Vinn = Vcm − e/2, e = (Vref − Vout)(A_s = 1, 음되먹임), 입력 두 포트를 Vcm으로 훑음. 점별 이득 = 같은 DC 해에서 `.tf v(e) Vref` → A = 1/(de/dVref) − 1 (DC 소신호, 원칙 3). 영역 = |VDS| − |VDSAT|(ngspice `@m[vds]`·`[vdsat]`, O-204 경계 VDS = VDSAT).
- 손 사이징(원문 설계 절차 Table 4 p.24를 sky130에 옮긴 시험점): GB 10 MHz·CL 10 pF(spec)·k = 4·α = 0.3(원문 예시, 시험 선택) → gm3 = 2π·40 MHz·10 pF = 2.5 mS, gm1 = 0.105 mS, gm2 = 0.186 mS, Cm1 = 1.68 pF, Cm2 = 1.32 pF; 전류밀도는 `char_gmid.log`(sky130 tt, L = 0.5 µm, |VDS| 0.6 V) -- pfet gm/ID 15·10, nfet 10·12. W(µm, L = 0.5 µm 기준; L = 1 µm 때는 W/L 유지): M0 6.9, M1·M2 15.1, M3·M4·M6A·M6B 0.86, M5 6.9, M7 1.72, M8·M14 2.93, M9·M10 7.6, M11 1.9, M12 116.6, M13 39.4; VBP 0.725 V, VBN 0.815 V.

| 경우 | Vref | 영역 행 창(Vcm) | 영역 끝 소자 | 창 안 A(x) | 창 밖(위) A(x) |
|---|---|---|---|---|---|
| L 0.5 µm | 0.9 | [0(레일), **0.674**] (−0.2 V에서도 M2 여유 +0.11 V) | 위 M0(0.66 V +0.011 / 0.68 V −0.004) | 106.2~107.8 dB | 1.2 V까지 106.2~108.2 dB(tail 전류 3.7 nA인데도) |
| L 1 µm | 0.9 | [0(레일), **0.693**] | 위 M0(0.675 V +0.013 / 0.700 V −0.005) | 118.0~120.0 dB | 0.9 V까지 118.0~120.0 dB |
| L 1 µm | 0.5 | [—, **0.693**] (위 끝 Vref 무관) | 위 M0 | 118.7~118.9 dB | 0.8 V까지 118.2 dB |

(icmr_servo.log, icmr_hs_vref0p9.csv, icmr_hs_L1u_vref0p9.csv, icmr_hs_L1u_vref0p5.csv)

- 원문 대조: 식 (9) 꼴 그대로(입력단 포화 폭). 측정 폭 0.674~0.693 V ≥ 0.6 V. 위 끝 = M0 포화 경계 = §1.4 유도와 일치, 아래 끝 = 레일(원문 식의 아래 끝은 sky130에서 음수).

### 3.3 대안 비교 (기준점·허용 저하)

공통 기준점 = **봉인점 servo 동작점**(N3.8 근 찾기 구간 [봉인점, 영역 행 창 끝]과 같은 점; spec `input_dc`가 SP-2 대기라 입력 CM은 엔진 θ `y:input_common_mode` -- 숫자 선언 없이 '봉인점'으로 칸을 채움, 상수 0).

| 안 | 허용 저하 | 물리 정합 | 원문 맥락 | 엔진 계산 꼴 | 상수 | 판정 |
|---|---|---|---|---|---|---|
| **(가) spec 이득 하한 유도** | Δ = A(기준점) − `gain_ss_db` 하한 (value_from_constraint `gain_ss_db`) ⇔ 창 안 모든 점 A(x) ≥ 111 dB | 증폭기가 선언 ICMR 안 모든 CM에서 자기 이득 spec을 지킨다 -- 응용 의미 그대로 | 원문은 이득 저하로 ICMR을 정의하지 않음(식 (9) 포화 폭); 111 dB는 원문 Table 5 결과를 사용자가 spec으로 채택(spec :62-73) | DE-1 (e) 같은 함수, 판정값 = 기존 spec 칸 READS(graph 규칙 3 -- gain_ss_db와 같은 정의, 상태 축 = ICMR servo 점) | 0 | **권고(조건부 맞음)** |
| (나) 상대 저하 사용자 상수(예: 3 dB) | 사용자 숫자 | 3 dB는 current_reuse 원문 Fig. 10 정의(N3.8 '출력 범위 판정 꼴' (b))이지 ngcc 원문 근거 없음 | ngcc 원문에 없음 | 같은 함수 | 1(사용자 선언) | ⚠ 원칙 11·13 -- 근거 없는 상수, 사용자가 원하면 선언 |
| (다) 허용 저하 0 | 0 dB | 실측 창 안 A가 이미 ±1~2 dB 변함 → 창이 기준점 한 점으로 줄어듦 | 없음 | 같은 함수 | 0 | 틀림(물리적으로 무의미) |
| (라) 기능 기준 미선언 | — | — | — | O-206: `icmr_v` 정의 불능 → 판정 정지 | — | 현 상태(동작 안 함) |

(가)의 조건·대가:
- 봉인점 이득이 111 dB에 겨우 닿는 front 점이면 창 안 이득 변화(실측 2 dB)만큼 창이 좁아질 수 있다 -- 이득 spec과 ICMR이 결합. 물리적으로는 맞는 결합(그 CM에서 실제로 spec 미달).
- 기준점에서 (가)의 판정은 `gain_ss_db` 행과 같은 값 -- 같은 정의 한 필드(규칙 3), 둘째 생산자 아님(O-211 (4) 상태 축 = servo 점).

### 3.4 ⚠ 실측 관찰 -- 증분 DC 이득은 ngcc 위쪽 끝을 가르지 못함
- 두 시험점 모두 영역 행 밖(위)에서도 A(x)가 기준점 대비 ≤ 1.6 dB(L 0.5 µm: tail 전류가 1/1800로 줄어도 106~108 dB).
- 물리 이유: 1단 이득 = gm1·(ro2 ∥ ro4). 약반전에서 gm ∝ I, ro ∝ 1/I라 **gm·ro가 전류와 무관** → tail 전류 고갈을 DC 이득이 보지 못한다. 기능 손실은 AC 쪽(GBW ∝ gm1 ∝ I_tail, 위 끝 넘어 약 4.6배 감소 = ID 비 6.65 → 1.44 µA로 추정 -- AC 미측정)에서 난다.
- 귀결: 이 회로의 ICMR 창은 **영역 행(M0 포화)** 이 정한다. O-205 (3)(R0 창 끝 = 포화·triode 영역 행)·N3.8 'ICMR 끝 = 영역 행 끝 ∧ 기능 기준 끝'이 유지되는 한 결과는 원문 식 (9)와 같다. 만약 나중에 영역 행을 빼고 기능 기준만으로 ICMR을 정의하자는 안이 나오면 ngcc가 반례다(위 끝이 1.2 V 이상으로 부풀음). 판정: O-211 기준은 ngcc에서 '조건부 맞음'(영역 행과 함께일 때만). 결정 변경 제안 아님 -- 기록.

## 4. 사용자 선언 필요 목록 (O-202~O-213 귀결 포함)

| # | 칸 | 현재 | 필요/권고 | 근거 |
|---|---|---|---|---|
| U1 | structure.json `dc_role` M8·M14 = signal | 파일 없음 | **필수**(단계 A 통과) | §2.1, what-if 실측 |
| U2 | `icmr_v` 기능 기준(기준점·허용 저하) | 없음 | **필수**(O-206), 권고 (가) | §3 |
| U3 | `intended_region` (CI-18) | pending | 기본(전 MOS 포화, ID > 0)로 충분 -- diode M3·M6A·M9 자동 포화, `off` 소자 0 → `judged_by`(O-202 (4)) 불필요. 명시 선언하면 '전부 saturation' | O-202·O-205·O-210 RR-6 |
| U4 | `input_dc` (SP-2) | pending | 선언 안 해도 엔진 θ(y)로 정함 -- ICMR 기준점은 '봉인점'으로 충분. 응용 CM이 정해져 있으면 그 값 선언(값은 사용자 몫, 원문 근거 없음) | §3.3 |
| U5 | `pending_constraints` 의 `gain_ss_db`(SP-4) | 남아 있음 | constraints에 111 dB가 이미 선언(2026-10-13) -- 낡은 대기 항목 여부 확인(SF-1 정리 후보) | spec :62-73 vs :141-146 |
| U6 | 전력 축 레일 선언(DEC-78) | 없음 | front 축에 전력이 필요하면 선언(`supply_current_dc_needs_counted_rails_declaration`) | whatif notes |
| U7 | `objective.budgets` (PA-1), `front_points_rule` (AC-3), `front_budget_s` (PA-2), `node_voltage_targets_v` (CI-15) | pending | 기본안 유지 가능(정지 원인 아님) | spec :161-171, :186-188, :254-257 |
| U8 | FF 비율 제약(`ff_ratio_candidates` r_ff = 1) | 미선언 | 선언 안 함 권고 -- PM을 MNA로 직접 판정하므로 영점 상쇄 비율은 수단이지 spec 아님(선언하면 탐색 축소). 원하면 원문 Table 1 조건(p.21)으로 선언 | 단계 A 보고 |

## 5. topology 정정 대기열 후보
없음 -- connectivity 16/16·3/3 원문 Fig. 3과 일치(§1.1). 비율(1:1, 1:2)은 사이징이지 연결이 아니다.

## 6. 보고 5묶음 (원칙 26)

1. bkit 단계표: 계획·design·검증·승인·test·code·구현 gap·감사 = 해당 없음(분석·실측만, 코드·문서 변경 0).
2. 단계별 점검표: graph 단일 정본 -- 권고 (가)는 기존 spec 칸 READS·DE-1 (e) 함수 재사용, 새 필드·cache 0(실측 아님, 계획 문언 대조); G-10·블록 안 재계산·소비자·구조 분할 = 해당 없음(코드 변경 0); 회로 이름 0 -- 권고 규칙에 회로 이름 없음; fail-closed -- (라) 미선언 정의 불능 유지; 상수 발명 0 -- (가)는 spec 값 유도, 손 사이징 값은 시험점(판정·spec에 안 씀); DC·AC 분리 -- ICMR·이득 모두 DC 해석(.dc/.tf); 계획 먼저 -- 계획 변경 제안 없음; 작성자 ≠ 검증자 -- 이 문서는 분석자 작성, 판정은 별도 검증 필요; 일반성 n/N -- ngcc 1/1만(다른 3회로는 다른 agent); 만들면 배선 -- 만든 것 없음(측정 스크립트만).
3. 원래 취지와 다름: 없음(결정 변경 제안 없음). §3.4는 O-211 기준이 ngcc에서 영역 행 없이 쓰이면 틀린다는 관찰 기록.
4. 권고 실측 출처: 직접 실측 = engine_run.log, whatif_chain*.log, icmr_servo.log·csv, char_gmid.log, fig3_zoom.png. agent 인용 = 없음. 문서 인용 = 계획 P:729·P:1329·P:1333, user_decisions.md O-202~O-213(1183-1194행), graph CONTRACT 4.4.
5. 권고 확인표 (권고 U1·U2(가)):
   ① 지적 사실 재확인: U1 = 엔진 실행 정지 문자열·CONTRACT 4.4·test_s1v_build.py:251 직접 확인 / U2 = spec :98-109 기능 기준 칸 없음 직접 확인. ② 계획 grep: 'ICMR 기능 기준' P:661·P:729·P:1329·P:1333. ③ 원칙 전수: 1(물리 -- SPICE 영역·이득 실측, SPICE 복제 아님: 엔진 계산은 DE-1 (e) 닫힌 식), 3(DC), 11·13(상수 0, 111 dB는 사용자 채택 spec), 14(연결·원문만), 15(대기열 0), 16(library). ④ 대안표 §3.3 + ⚠(나). ⑤ 실현 가능성: SPICE 두 시험점에서 (가) 적용 시 창 = 영역 행 창(L 1 µm: [0, 0.693] 안 A ≥ 118 dB > 111). ⑥ 열린 결정 상호작용: SP-2(input_dc) 미정이어도 기준점 = 봉인점이라 무관; SF-1(칸 로더)·DE-1 (e) 착수 조건. ⑦ 원래 취지: 같음. ⑧ 원문 쪽: 식 (9)(10) 저널 p.24/PDF p.5, Table 1 p.21/PDF p.2, Table 5 p.25/PDF p.6, 로컬 PDF 위 경로. ⑨ 물리·회로이론: §1.3·§1.4 유도 + §3.2 실측, 판정 = U1 맞음, U2 (가) 조건부 맞음(§3.4). ⑩ 결정 간 모순 점검: 작성자 자체 대조만(O-205 (3)·O-206·O-211과 충돌 없음으로 봄) -- **권고 작성자 아닌 점검자의 전수 대조 기록 없음 → 원칙 26 ⑩ 미충족, 질문 전 별도 점검 필요**.
