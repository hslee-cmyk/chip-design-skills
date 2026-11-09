# 접합 용량 C 열 대조 · 바이어스 넷 레일 소속 · 중점 적재 거부안 실측 (2026-11-06)

- 역할: 독립 측정·분석자. 엔진 수정·커밋 0, ngspice 0, 원 worktree 수정 0.
- 실행 사본: WB-1 worktree `wt/20261105-wb1-c` 머리 `29e907b9`(`git -C ... archive HEAD | tar -x`)를 `C:/Users/HSLEE/AppData/Local/Temp/la1s_jc27/src/`에 풀어 import했다. 측정이 끝난 뒤 풀어 둔 사본은 지웠다.
- 데이터: LUT v2 `C:/Users/HSLEE/Documents/Todoc/fpga/lut_data/sky130_lut_v2`(설정 `assets/lut_v2_location.json`, sha256 대조는 `resolve_lut_location`이 했다). 중점 파일은 `<root>/verify_midpoints_w/` 30개다.
- 원칙 8: 엔진 코드는 (1) 정의 함수를 부르는 데와 (2) 재작성 범위(어느 자리가 무엇을 읽는가)를 정적으로 읽는 데에만 썼다. 식은 다시 구현하지 않았다. 격자 점은 기준 LUT 축 마디이고, 상수는 새로 만들지 않았다.
- 스크립트(임시 경로, 파일로 실행): `C:/Users/HSLEE/AppData/Local/Temp/la1s_jc27/scripts/{jc_common.py, jc1_contrast.py, jc1_subsets.py, jc2_bias_nets.py, jc3_reject.py}`
- 출력: `C:/Users/HSLEE/AppData/Local/Temp/la1s_jc27/out/{jc1.jsonl, jc1_nmos_points.json, jc1_pmos_points.json, jc1_subsets.txt, jc2.jsonl, jc3.jsonl}`

## 결론 요약

| # | 질문 | 판정 | 요지 |
|---|---|---|---|
| 1a | 드레인: CDD − CGD 대 엔진 `cdb` | **조건부 맞음** | 접합 부분은 정의가 같다. 깊은 off(VGS = 0, VDS ≥ 0.3 V)에서 (CDD − CGD)/cdb = 1.000(n = 1008/kind, p05~p95 1.000, 최대 1.001). 채널이 켜지면 채널 전하 분배 항 Rd = CDD − CGD − cdb가 남는다. 엔진은 이 항을 빼고 있다. 크기는 sat p50 +0.8 %(nmos)·+1.4 %(pmos), p95 +5.0 %·+8.3 %이고 triode p05~p95는 −10 %~+17 %다(엔진 드레인 자기 용량 cgd + cdb 대비) |
| 1b | 소스: CSS − CGS 대 엔진 `csb` | **틀림(정의 다름)** | 깊은 off에서는 (CSS − CGS)/csb p50 = 0.998·0.999로 접합 정의가 같다. 채널이 켜지면 Rs = CSS − CGS − csb가 크게 음수다. sat p50 −26.2 %·−26.4 %, p05 −33.5 %·−35.6 %(엔진 소스 자기 용량 cgs + csb 대비)이고, Rs/CGG는 약 −0.27·−0.28이다. 엔진은 소스 마디 자기 용량을 CSS보다 1/4 남짓 크게 스탬프한다 |
| 2 | 바이어스 전압 넷이 레일 집합에 늘 드는가(m1-b) | 드는가 = **아니다**(0/20). O-244 결과 = **조건부 맞음** | 13회로 중 8회로가 `bias_inputs` 20넷을 선언한다. 레일에 든 넷 0/20, 입력 포트 0/20, gate 전용 20/20이다. gate 전용이라 전류 가지 끝점이 아니다. 그래서 봉인 3 행은 0/20이고 재풀이 미지수도 0/20이다(기준 점 값 고정). 원이 구동하는 넷을 봉인 3이 판정하는 일은 생기지 않는다. 다만 O-244 집합 문언 '레일 ∪ 입력 포트'에는 이 넷이 없다(정의 누락, 동작 영향 0). 이 성립은 authoring 게이트 `bias_input_not_gate_only`에 기댄다 |
| 3 | '앵커 2개 bin에 그 폭 중점이 없으면 적재 거부' | **조건부(거부 대상 = `widths()` 슬라이스일 때만 실현 가능)** | `widths()` 슬라이스 30/30이 앵커 2개 bin 4/4씩, 모두 120/120 덮인다. nmos 키 72·78(0.36·0.39 µm, W_min 0.42 µm 아래)도 앵커 2개 bin이 4개씩 있는데 중점 파일이 없다. 거부 대상을 `slice_map` 전체로 하면 이 두 슬라이스 때문에 `load_lut_set` 전체가 거부된다(LUT 전체 차단). 두 키는 `widths()`·`reachable_slices` 밖이다. tol 표 구성·소비 자리 중 이 키를 쓰는 곳은 정적으로 0이다. '거부 판정 대상 = `widths()` 슬라이스(= `build_slice_tables` 표 구성 대상)'로 정의가 선다 |

---

## 1. 접합 용량 정의 동일성 (DEC-91 (3) 대조 test, "왜 C열을 사용하지 않아?")

### 1.1 정의 확인 (문언 실측)

- LUT 열 정의: `lut/CONTRACT.md` 1.2(:125~:129)와 생성기 `assets/sky130_lut_sweep.py`:18~22·:312가 정한다. 용량은 부호를 보존한다. CGG = −Im(i(vgs))/ω(게이트 여기)이고 C_gx = +Im(i(vgs))/ω(x = d·s·b 여기)다. CDD = −Im(i(vds))/ω(드레인 여기, 나머지 단자는 AC 접지)이고 CSS = −Im(i(vsrc))/ω(소스 여기)다. 생성기 주석에 'CDD·CSS = 드레인·소스 자기 용량, 접합 포함'이라고 적혀 있다. 기준 LUT meta `sign_convention`(jc1.jsonl `loaded`)도 같은 글이다.
- 생성기 DUT 줄(:90)은 `w=5u ad=2.5p as=2.5p pd=7u ps=7u`이고 nf는 기본 1이다. 엔진 `JunctionSource.pre_layout_geometry(5e-6, 1)`은 `DiffusionGeometry(finger_w 5 µm, ad = as = 2.5 pm², pd = ps = 7 µm, m 1)`을 낸다(jc1.jsonl). 생성 기하와 같다.
- PDK 모델 카드(`C:/pdk/sky130_fd_pr/cells/{nfet,pfet}_01v8/*__tt.pm3.spice`, grep)는 `capmod = 2`, `xpart = 0.0`(40/60 전하 분배), `acnqsmod = 0`이다.
- 엔진 스탬프: `metrics/stamp_mos.py`:28~35는 상호적인 2단자 용량 5개(cgs g–s, cgd g–d, cgb g–b, cdb d–b, csb s–b)만 쓴다. 그래서 LUT 측정 구성과 같은 여기(한 단자 여기, 나머지 AC 접지)에서 엔진의 드레인 자기 용량은 cgd + cdb, 소스 자기 용량은 cgs + csb다. cds 항과 비상호 항은 없다. `metrics/ss_linearize.py`:79~85에 따르면 cgg·cgd·cgs·cgb는 LUT `caps`에서 오고, cdb·csb는 `junction_caps`에서 온다. CDD·CSS는 읽지 않는다.
- 따라서 Rd = CDD − CGD − cdb와 Rs = CSS − CGS − csb가 **엔진이 LUT 정의에서 빠뜨린 자기 용량 차**와 같다.

### 1.2 측정 구성

- 표: 기준 LUT(`cap_map[kind]`, w_ref = 5 µm, 축 L 18 × VGS 49 × VDS 49 × VS 10). 격자 = L 앵커 18개 전부 × VGS·VDS·VS 축 마디 3칸 간격. kind마다 20,808점이고 조회 실패는 0이다.
- 엔진 정의 함수만 불렀다. `lut.caps(memo, kind, L, vgs, vds, vsb, W = w_ref)`(비례 1, 마디 값)와 `junction_caps(junction.params_of(kind), junction.pre_layout_geometry(w_ref, 1), v_db = VDS + VSB, v_sb = VSB, junction.temp_c = 27 °C)`다. 차와 비 말고는 계산이 없다.
- 영역 표지는 보고용 묶음일 뿐이다(기준 LUT VTH·VDSAT 열 마디 값과 비교). off는 on_mask가 거짓이거나 VGS < VTH, sat는 VDS ≥ VDSAT, triode는 그 밖이다. 판정 규칙이 아니다(예: pmos L ≥ 0.5 µm, |VGS| = 0.9 V는 |VTH| 아래라 off로 묶인다).

### 1.3 결과 (jc1.jsonl, jc1_subsets.txt)

| kind | 묶음 | n | (CDD−CGD)/cdb p05 / p50 / p95 | Rd/(cgd+cdb) p05 / p50 / p95 [min, max] | (CSS−CGS)/csb p50 | Rs/(cgs+csb) p05 / p50 / p95 [min, max] | Rs/CGG p50 |
|---|---|---|---|---|---|---|---|
| nmos | 깊은 off, VGS = 0, VDS ≥ 0.3 | 1008 | 1.000 / 1.000 / 1.000 | ≈ 0 (p95 1.5e-4) | 0.998 | −0.041 / −0.001 / +0.016 | −0.001 |
| nmos | sat | 9196 | 1.000 / 1.013 / 1.096 | +0.0001 / +0.0084 / +0.0496 [−0.121, +0.134] | −0.34 | −0.335 / −0.262 / −0.126 [−0.348, −0.067] | −0.272 |
| nmos | triode | 1928 | −4.50 / 1.18 / 1.56 | −0.100 / +0.047 / +0.128 [−0.173, +0.144] | −1.20 | −0.319 / −0.252 / −0.107 | −0.169 |
| pmos | 깊은 off, VGS = 0, VDS ≥ 0.3 | 1008 | 1.000 / 1.000 / 1.000 | ≈ 0 (p95 1.1e-4) | 0.999 | −0.022 / −0.001 / −0.0003 | −0.0005 |
| pmos | sat | 6191 | 1.000 / 1.017 / 1.093 | +0.0001 / +0.0145 / +0.083 [−0.099, +0.151] | −0.35 | −0.356 / −0.264 / −0.120 [−0.368, −0.055] | −0.284 |
| pmos | triode | 1286 | −1.30 / 1.12 / 1.35 | −0.082 / +0.055 / +0.172 [−0.164, +0.222] | 0.03 | −0.333 / −0.224 / −0.092 | −0.187 |

대표점(W = 5 µm, VSB = 0, 단위 fF):

| kind | L µm | VGS | VDS | 묶음 | CDD | CGD | cdb | Rd | CSS | CGS | csb | Rs | CGG |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| nmos | 0.15 | 0.000 | 0.900 | off | 4.354 | 1.231 | 3.123 | +0.000 | 5.882 | 1.276 | 4.606 | +0.000 | 4.343 |
| nmos | 0.15 | 0.900 | 0.900 | sat | 4.365 | 1.228 | 3.123 | +0.014 | 8.002 | 4.185 | 4.606 | −0.789 | 6.382 |
| nmos | 0.50 | 0.900 | 0.900 | sat | 4.358 | 1.215 | 3.123 | +0.020 | 14.364 | 14.433 | 4.606 | −4.675 | 16.516 |
| nmos | 0.50 | 0.900 | 0.112 | triode | 12.472 | 6.941 | 4.301 | +1.230 | 12.970 | 11.786 | 4.606 | −3.422 | 19.145 |
| nmos | 20.0 | 0.900 | 0.900 | sat | 5.057 | 1.857 | 3.123 | +0.078 | 382.413 | 536.218 | 4.606 | −158.411 | 574.029 |
| pmos | 0.15 | 0.900 | 0.900 | sat | 2.489 | 0.081 | 2.284 | +0.123 | 6.484 | 3.792 | 3.232 | −0.540 | 5.415 |
| pmos | 20.0 | 0.900 | 0.900 | (|VGS|<VTH) | 2.674 | 0.388 | 2.284 | +0.002 | 142.393 | 190.545 | 3.232 | −51.383 | 285.728 |

### 1.4 판정

- **접합 항 정의 동일성: 맞음.** 채널이 없는 점(VGS = 0, VDS ≥ 0.3 V)에서 LUT의 CDD − CGD가 엔진 cdb와 n = 1008/kind 모두 0.1 % 안에서 같다(최대 비 1.001). 엔진 접합 식, 생성 규칙 기하, 역바이어스 v_db = VDS + VSB 규약이 LUT 열 정의와 같은 양을 낸다. 이로써 DEC-91 (3)이 정한 대조가 처음으로 실측되었다(소스 쪽 비는 p50 0.998, p05 0.926·0.975로 약간 넓다. 남은 차는 약반전 경계 점이다).
- **채널 전하 분배 항: 엔진이 빼고 있다(O-179 꼴).** 차가 채널 유무에 따라 생기므로 물리 결정자는 BSIM 진성 전하 분배(capmod 2, xpart 0 = 40/60)의 비상호 용량이다. 접합 문제가 아니다. 엔진 스탬프는 상호 2단자 5개뿐이라 이 항을 담을 칸이 없다.
  - 드레인 Rd: sat에서는 작다(p50 1 % 안팎, p95 5~8 %, 최대 13~15 %). triode에서는 p05~p95가 −10 %~+17 %다. 긴 L·triode 끝점에서는 Rd가 −64 fF(nmos L 20 µm) 크기까지 간다. 드레인 쪽 판정은 **조건부**다. sat 동작점이 대부분인 증폭 소자에서는 작고, triode·긴 L 점에서는 크다.
  - 소스 Rs: sat p50이 엔진 소스 자기 용량의 −26 %다. Rs/CGG가 영역 전반에서 −0.27 근처로 모인다(손계산 근거: 40/60 분배에서 sat 진성 ∂Qs/∂Vs ≈ 0.4·Cox·WL, Cgs ≈ (2/3)·Cox·WL, 차 ≈ −0.27·Cox·WL. 실측 Rs/CGG −0.27·−0.28과 맞는다). 엔진은 소스 마디(캐스코드 소스·접힌 마디·추종기 출력 등)의 자기 용량을 그만큼 크게 둔다. 소스 쪽은 **틀림(정의 다름)**이다.
- ⚠ 범위 한계:
  - (i) CDD·CSS는 기준 폭 5 µm 표에만 있다. 다른 폭 슬라이스의 Rd·Rs는 못 잰다. 기준 폭 환산은 접합 둘레 항이 W에 비례하지 않아 쓰지 않았다.
  - (ii) 상호 2단자 스탬프 집합으로는 게이트 행(CGS·CGD)과 소스·드레인 행(CSS·CDD)을 동시에 맞출 수 없다. 고치려면 비상호 스탬프(transcapacitance)가 필요하거나, 어느 행을 맞출지 정해야 한다. 그 선택(design·계획, DEC-91 (3)·O-179 문언)은 이 측정의 범위 밖이다.
  - (iii) cdb·csb와 ngspice `@m[capbd]`·`@m[capbs]`의 대조는 `junction_cap.py` 머리 문언의 기록(2026-10-08)이다. 여기서 재지 않았다(agent 인용). 위의 깊은 off 항등은 그와 독립인 LUT 대비 실측이다.

---

## 2. 원 넷 집합 m1-b -- 바이어스 전압 넷과 엔진 레일 집합

### 2.1 측정 (jc2.jsonl, 엔진 `load_topology`·`load_sizing_spec`)

- 레일 집합 원천: topology `supply_nets` → `TopologyDoc.rails` → `node.is_rail`이 원천이다. 값은 spec `supplies_v` → `node.dc_rail_v`(`sizing/w0_rails.py`)다.
- 13/13회로가 적재됐고 오류는 0이다.

| 회로 | 레일(supplies_v) | bias_inputs (모두 gate 전용) |
|---|---|---|
| cnr_ota | VDD_1V8 1.8, VSS 0 | 없음 |
| common_gate_amplifier | gnd 0, vdd 1.8 | VNBias1, VNBias2, VPBias1 |
| current_reuse_telescopic_ota | gnd, vdd | 없음 |
| erfc_ota | gnd 0, **vcn 0.7, vcp 1.1**, vdd 1.8 | 없음(바이어스 전압을 레일로 선언) |
| folded_cascode | gnd, vdd | bias3 |
| ngcc_3stage_ff | gnd, vdd | VBN, VBP |
| nmcnr_amplifier | agnd 0.9, vdd, vss | VB1~VB5 |
| pushpull_follower_buffer | agnd 0.9, vdd, vss | VNB1, VPB1 |
| r2r_opamp | VDD, VSS | vb1, vb3, vb4, vb5n, vb6n |
| rfc_ota | gnd, vdd | 없음 |
| sf_pushpull_output_opamp | agnd 0.9, vdd, vss | 없음 |
| two_stage_ota | gnd, vdd | bias |
| two_stage_ota_sf | gnd, vdd | bias |

- 바이어스 전압 넷의 선언 꼴은 둘이다.
  - (가) 레일로 선언: erfc vcn·vcp가 있다. 이 넷은 `dc_rail_v`에 든다.
  - (나) `bias_inputs`로 선언: 8회로 20넷이다. 레일 0/20, 입력 포트 0/20, gate 전용 20/20(비 gate 단자 0)이다.
  - agnd 0.9 V 레일 3회로는 '바이어스 전압'인지가 해석의 문제라 셈에 넣지 않았다(레일이므로 어느 쪽이든 `dc_rail_v`에 든다).
- 그래서 질문 "바이어스 전압 넷이 `supplies_v`·`dc_rail_v`에 늘 드는가"의 답은 **아니다(bias_inputs 20/20 넷이 레일 밖)**다.

### 2.2 봉인 3·재풀이가 그 넷을 판정·미지수로 삼는가 (정적 실측, 재작성 범위 인용)

- 봉인 3(`sizing/seal_kcl.py`:28~52): 행 = `graph.dc_current_basis.ends`의 끝점 넷 중 레일 밖인 것이다. ends는 MOS 채널 끝(d, s), 저항, 이상 전류원 단자다(`sizing/current_basis.py`:79~90). gate 전용 넷은 끝점이 될 수 없으므로 bias_inputs 20넷의 봉인 3 행은 **0/20**이다.
- 재풀이(`sizing/block_dc.py` `_kcl_solve`:773~795): 미지수 = flow_nets − 레일 − 입력 포트 − held다. bias 넷은 flow_nets 밖이라 미지수가 아니다. `_kcl_system`의 `fixed`(기준 스냅샷 `dc_v` 값)로 고정된다. 미지수 **0/20**이고, 바이어스 고정과 같다.
- SPICE 측정 구성에서 이 넷은 전압원으로 구동된다. 오라클 입력 `bias_voltages` 넷 집합 = topology `bias_inputs`(`authoring/CONTRACT.md`:271, agent 인용 아닌 문언 실측). 곧 '원이 구동하는 넷'은 레일 ∪ 입력 포트 ∪ bias_inputs이고, O-244 문언 '레일 ∪ 입력 포트'에는 셋째 원소가 빠져 있다.

### 2.3 판정

- 봉인 3이 원이 구동하는 넷을 판정하는가: **아니다(0/20)**. O-200 위반은 생기지 않는다. 조건은 authoring 게이트 `bias_input_not_gate_only`(`authoring/bias_inputs.py`)다. 이 게이트가 bias_inputs를 gate 전용으로 묶고, 채널에 닿는 바이어스 전압은 erfc처럼 레일로 선언하게 한다.
- O-244 집합 문언은 **정의가 하나 빠져 있다**(동작 영향은 0). 점검 기록 m1-a('봉인 9 다리 규칙이 레일·바이어스 전압·입력 포트를 따로 적음')의 '바이어스 전압'은 문언 중복이 아니라 O-244 집합에 없는 실제 셋째 원소다. 문언을 고친다면 '원 넷 = 레일 ∪ 입력 포트 ∪ bias_inputs(gate 전용이라 KCL 행 없음)'처럼 인용 하나로 맞추는 일이고, 사용자 결정 O-244 문언 변경에 해당한다. 판정: **조건부 맞음**.

---

## 3. 적재 거부안 실현 가능성 (점검 항목 4 사용자 결정 후보)

### 3.1 측정 (jc3.jsonl)

- 방법:
  - 엔진 `load_lut_set`으로 적재해 슬라이스별 bin 지도 `l_bins`(엔진 값)를 얻었다.
  - 앵커 2개 bin은 `anchor_bin`에서 같은 index를 가진 앵커가 2개인 bin이다.
  - `verify_midpoints_w/*.npz`(30개, 읽기만)는 npz `W`에서 폭 키를 얻었다.
  - 덮임은 중점 L이 엔진 `bin_index`로 그 bin에 들고 두 앵커 사이에 엄격히 있을 때로 셌다. `midpoint_l_bin_checks`와 같은 조건이다. LM-1e 적재 코드는 WB-1 머리에 없다(`verify_midpoints_w`를 읽는 엔진 코드 0, grep 결과는 provenance json뿐이다). 그래서 이 판정은 제안된 거부 규칙을 같은 조건으로 흉내 낸 것이다.
- 결과:
  - `slice_map`은 32슬라이스(nmos 20, pmos 12)이고 모든 슬라이스에 앵커 2개 bin이 4개씩 있다(bin 9개 중).
  - `widths()`는 nmos 18, pmos 12, 합 30슬라이스다(하한 `min_finger_w_m` = 0.42 µm, 격자 5 nm, 키 ≥ 84). 중점 파일 30개가 30/30 슬라이스에 대응하고, 각 4/4 bin을 덮어 **120/120**이다(provenance n = N = 120과 같다).
  - nmos 키 72(0.36 µm)·78(0.39 µm)은 앵커 2개 bin이 4개씩(model .179·.176·.175·.174, 앵커 쌍 (0.15, 0.18)·(0.7, 1.0)·(1.5, 2.0)·(2.5, 4.0) µm)이다. 중점 파일이 없어 **8칸 결측**이다.
  - 두 키는 `widths()` 밖이고, `reachable_slices` 합집합(기준 슬라이스 L 앵커 18개 전부) 밖이다. 참고로 키 1400(7 µm)은 `widths()` 안이지만 도달 밖이다. 중점은 있다.

### 3.2 키 72·78이 표 구성·소비 대상인가 (정적 실측, 재작성 범위 인용)

- tol 표 구성(`lut/slice_tables.py` `build_slice_tables`)은 `widths()` 키만 돈다.
- tol 표 소비 자리의 키 출처:
  - `sizing/seal_tolerances.py`:32와 `block_dc.py`:371은 `dc_op.w_key`를 쓴다. 이 키는 `finger_slice`·`slice_of_finger`에서 오며, 둘 다 W_min 하한이 있다.
  - `layout/slice_density.py`는 `layout/contract_input.py`:155의 `widths()`를 쓴다.
  - `search/cell_floor.py`:104와 `lut/derived_fns.py` edge_costs(`metrics/achievability.py`:280, `search/_helpers_curves.py`:84)는 `cap_map[kind].w_key`를 쓴다.
  - 결과: 키 72·78을 쓰는 자리는 0이다.
- `slice_map` 전체를 도는 소비자 셋(`metrics/area_lower_bound.py` `_kind_extrema`, `metrics/curve_checks.py`, `search/count_budget.py`)은 tol·중점을 읽지 않는다.

### 3.3 판정

- 거부 대상을 `slice_map` 전체로 하면 **틀림(현 데이터로 적재 불능)**이다. 키 72·78의 결측 8칸 때문에 `load_lut_set`이 거부된다. `load_lut_set`은 하나라도 결함이면 전체를 거부하는 구조라 LUT 전체가 막힌다.
- 거부 대상 = `widths()` 슬라이스(= `build_slice_tables` 표 구성 대상)로 하면 거부 0/30이고 정의가 선다. 그 바깥 슬라이스는 tol 표가 만들어지지 않으므로 정의 항(중점)이 필요 없다. 판정: **조건부 맞음**(조건 = 거부 판정 범위를 표 구성 범위와 같은 자리 `widths()`로 인용. graph 규칙 3, 판별 하나).
- 정적 관찰(질문 밖, 판정 안 함): `area_lower_bound._kind_extrema`는 W_min 아래 슬라이스(72·78)까지 L 최소·IDu 최대에 넣는다. 면적 하한 근거 집합이 `widths()`와 다른 셈이다. LA-1 재점검 입력 후보로만 적는다(O-229 3).

---

## 돌린 범위

- 실행:
  - `jc1_contrast.py`: LUT 적재 1회, kind당 20,808점, `caps` + `junction_caps`.
  - `jc1_subsets.py`: 점 파일 집계.
  - `jc2_bias_nets.py`: 13회로 `load_topology`·`load_sizing_spec`.
  - `jc3_reject.py`: LUT 적재 1회, 슬라이스 32개, 중점 npz 30개 읽기.
  - LUT 적재 전 여유 메모리는 5.30 GB·5.22 GB였다(기준 3.7 GB 이상).
- 안 돌린 것: pytest, ngspice, 비기준 폭 슬라이스의 C 열(데이터 없음), cdb·csb 대 ngspice capbd·capbs 재대조(머리 문언 기록 인용만), LM-1e 적재 코드(없음). 통과로 세지 않았다.
- 표 캐시 환경 변수 `GMID_LUT_TABLE_CACHE_DIR`는 임시 경로를 가리켰고, persistent 표는 부르지 않았다.
- 프로세스: 끝날 때 `python.exe` 0개를 확인했다.

## 정정 표지 (오케스트레이터, 2026-11-06)

- :65 부근 '손계산 −0.27·Cox·WL이 실측 Rs/CGG −0.27과 맞는다'는 두 정규화를 섞은 문장이다(권고 작성자 지적, `cap_and_set_questions_recommendation.md`). 이상값 Rs = −0.267·Cox·W·L(CGG,int 대비 −0.40), 대표점 실측 Rs/CGS = −0.14~−0.32. 부호·차수만 일치하고, 판정(소스 행 정의 다름)은 그대로다. 질문에 쓰인 양은 Rs/(cgs+csb) sat p50 −26 %.
