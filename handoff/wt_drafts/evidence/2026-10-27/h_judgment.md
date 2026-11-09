# CMP-1 혼합안 H(결정 O-163) 독립 SPICE 판정

판정자: 독립 SPICE 판정 agent(작성자≠검증자). 작성자 보고(`H/RESULTS.md`, jsonl 의 엔진 metric)는 **증거로 쓰지 않았다**. 아래 'SPICE' 열의 수치는 모두 판정자가 ngspice-46(`ngspice_con.exe -b`)으로 직접 잰 값이다. 엔진 예측·평가 수·벽시계는 jsonl 기록(작성자 실행 산출물)에서 읽은 **agent 인용** 값이고 그렇게 표시한다.

- 대상: `wt/_cmp_pilot/H/netlists/INDEX.txt` 18 netlist(C 2, H0box 2, H0 6, H0r 6(회로 4), H0rX 1, + common_gate H0r 2 포함). H1 미실행(작성자 보고대로, 엔진 불변 범위 밖).
- spec(저장소, 엔진이 읽은 사본): `wt/integ-it12/skills/analog-gmid-design/assets/library/<회로>.sizing_spec.json`. folded_cascode 는 추가로 O-140 사본 `wt/_cmp_pilot/verify/o140/folded_cascode.sizing_spec.json`(PM ≥ 70°, gain ≥ 70 dB, GBW ≥ 10 MHz). 온도 27 °C(DEC-96 (3)), tt.
- 판정 도구(판정 전용, 엔진·H 시제품에 배선하지 않음): `wt/_cmp_pilot/H/judge/`
  - `spice_judge_base.py` = `judge/spice_judge.py` 바이트 사본(sha256 973b718a…, 원본 미수정)
  - `hjudge.py`(입력 구동 일반화·trim 이분·rout·ICMR/swing·잡음 대체법), `run_h_judge.py`(케이스마다 `res/h_results.jsonl` append + `res/raw_<tag>.json`), `mk_tables.py`, `summ.py`, `val_noise_alt.py`, `probe_fail.py`(Q3), `specdump.py`
- 엔진 worktree `integ-it12` @ ebad06c1: 판정 전후 `git -C …/integ-it12 status --short` **빈 출력**(확인 2회: probe 뒤, 최종 실행 뒤). armA/armC/judge/verify/H(scripts·out·netlists) 미수정.

## 0. 측정 방법 (앞선 CMP 판정 `cmp1_pilot_judgment.md` §0 과 같은 정의, 바뀐 점만 표시)

| 항목 | 방법 | 앞선 판정과 차이 |
|---|---|---|
| 모델 | `C:/pdk/sky130_fd_pr` cells tt pm3 + mismatch.corner + lod, `ngbehavior=hsa`, 27 °C | 같음 |
| netlist | H `.sp`(eng2spice 변환, finger = round(W/5 µm)) 를 평탄화, bias 이상 전압원·Ibg 값은 `.case.json` 그대로, 측정 부하 CL 1개를 판정 deck 이 넣음 | 같음 |
| 입력 셀(판정자가 연결로 정함) | two_stage·two_stage_sf·folded: gate=vin_p/vin_n 인 M1·M2. nmcnr: gate=Vin_p/Vin_n 인 PMOS 쌍 M102·M103(꼬리 NodeTail 공유). common_gate: source=vin, gate=바이어스인 M2(M1 은 vin 의 전류원). pushpull: 정의 불요(spec = rout·면적). 엔진 기록의 input_cells 와 대조 → 모두 일치 | 신규 회로 |
| 입력 DC | input_dc 미정(SP-2) 회로: vin_n(또는 단일 vin) = 엔진 값, trim 을 첫 입력에 더해 V(out) = 엔진 출력 전압. pushpull: spec `input_dc = agnd` → vin = 0.9 V 고정, trim 없음 | **trim 을 DC 서보 대신 dc 스윕 구간 축소(이분)로 구함**: 고이득(80~105 dB) 회로에서 서보 OP 가 발산(trim 858 V)해 바꿈. 서보가 되던 케이스는 같은 값(two_stage H0r pt0: 서보 −319.05 mV, 이분 −319.05 mV) |
| AC | 차동 ±0.5(단일 입력 1.0) 구동, 이득 = 0.01 Hz, GBW = 0 dB 교차, PM = 180 + Δ위상, β = 1 | 같음 |
| offset_excess | 모든 MOS 게이트 직렬 AC 원(0.1 Hz) 전달 × 소자 bench σ_VGS(PDK slope_spectre 변수) | 같음(bench gm = 0 이면 σ=NaN 기록, 해당 없음) |
| noise_excess_th | `.noise` 1 Hz 소자별 열 성분(1overf 제외) + 저항 열잡음 / 입력 셀 열 성분 | **대체법 추가**: `.noise` 의 OP 재계산이 수렴 못 하는 2 점(folded H0r pt0, nmcnr H0rX pt0)은 'drain-source AC 전류 주입 전달 |Z_k|² × 소자 단독 bench 단락 전류 열잡음'. `.noise` 가 되는 6 점에서 두 방법 차 ≤ 3e-6(상대, `res/noise_alt_validation.jsonl`) |
| rout (two_stage_sf, pushpull) | 출력 노드 AC 1 A 주입, 입력 AC 0(포트 뷰), 0.01 Hz, |V(out)| | 신규(엔진 `rout.py` 정의: 입력 포트 고정, 출력 감지 노드 전류 주입) |
| ICMR·swing (nmcnr) | 출력 = 목표로 trim 을 점마다 다시 찾으며 vcm 스윕(ICMR), vcm 고정·출력 목표 스윕(swing), 50 mV 격자, 전 MOS VDS ≥ VDSAT 구간. swing = 2·min(hi−V_dc, V_dc−lo)(엔진 `ls_swing` 꼴) | 신규. 엔진 정의(경로 합 손계산)와 구현이 다르므로 '같은 양의 SPICE 측정'이지 같은 식은 아님. 판정자는 전 소자 포화로 잼(엔진은 입력 경로 소자) — 보수적 |
| 포화 | spec `vds_ge_vdsat`(여유 0) | 같음 |
| 면적 | ΣW·L·m + C(측정 부하 제외)/2e-3 F/m² + R(측정 부하 RL 제외)·2.2593e-15 + 2.178e-13 | 같음(수동소자 이름 일반화) |
| 전력 | −I(V_vdd)·1.8 V(이상 bias 원 제외; nmcnr agnd 원 전류 −1.4 nA 별도 기록) | 같음 |

## 1. 회로 × 변형 요약 (SPICE 통과 = spec 전 항목 PASS + 전 소자 포화, 사람 개입 없이 엔진 front 점 그대로)

'front/점'·'평가 수'·'벽시계'·'sealed/feasible' = **agent 인용**(jsonl). 교차 확인: 모든 jsonl 에서 `t_build+t_grid+t_screen+t_search = wall_total`(±1 s), `front.t − screen.t = t_search`(±1 s) 로 기록 내부가 일치. 5 프로세스 병렬 실행(`driver.py`)이라 벽시계는 서로 간섭된 값이다.

| 회로 | 변형 | front(인용) | SPICE 판정 점 | **SPICE 통과** | 평가 수(인용) | 벽시계 s(인용) | 통과점 최소 전력 | 통과점 최소 면적 |
|---|---|---|---|---|---|---|---|---|
| two_stage_ota | C | 0 | 0 | **0** | 107 | 71 | - | - |
| | H0box | 0 | 0 | **0** | 2928 | 514 | - | - |
| | H0 | 3 | 3 | **0** (pt0 GBW 1.04 MHz·PM 44°, pt1 PM 69.9°, pt2 GBW 1.56 MHz·PM 66°) | 3516 | 611 | - | - |
| | H0r | 1 | 1 | **1** | 3500 | 562 | 397 µW | 8030 µm² |
| two_stage_ota_sf | C / H0box / H0 | 0/0/0 | 0 | **0** | 398 / 3510 / 2867 | 233 / 764 / 739 | - | - |
| | H0r | 1 | 1 | **0** (PM 67.9° < 70) | 3517 | 668 | - | - |
| folded_cascode (저장소 spec: offset·noise·면적만) | C / H0box / H0 | 0/0(출발점 0)/0(출발점 0) | 0 | **0** | 744 / 274 / 0 | 219 / 141 / 85 | - | - |
| | H0r | 2 | 2 | **1** (pt0, noise 1.98 경계; pt1 noise 3.20·offset 1.55 FAIL) | 2294 | 587 | 2.68 µW | 1496 µm² |
| folded_cascode (O-140 사본) | C / H0box / H0 / H0r / H0rX | 0 전부 | 0 | **0** (참고: 저장소 spec H0r 점 2개도 O-140 으로 재면 둘 다 FAIL — pt0 GBW 0.091 MHz, pt1 이득 51.5 dB·GBW 6.7 MHz) | 628 / 274 / 950 / 2284 / 2569 | 192 / 123 / 263 / 478 / 647 | - | - |
| nmcnr_amplifier | C / H0box / H0 / H0r | 0/출발점 0/0/0 | 0 | **0** | 2000 / 212 / 2052 / 3266 | 630 / 158 / 570 / 831 | - | - |
| | H0rX(N 3000, k 12) | 1 | 1 | **0** (GBW 0.138 MHz, PM 26.7°, noise 2.67) | 4580 | 871 | - | - |
| pushpull_follower_buffer | C / H0box | 0 / 0 | 0 | **0** | 212 / 2705 | 47 / 174 | - | - |
| | H0 | 1 | 1 | **1** | 2052 | 135 | 56.5 µW | 576 µm² |
| | H0r | 1 | 1 | **1** | 3013 | 159 | 45.3 µW | 44.1 µm² |
| common_gate_amplifier (spec: noise·면적만) | C | 2 | 2 | **2** | 89 | 39 | 0.34 nW | 0.22 µm² |
| | H0box | 2 | 2 | **2** | 3505 | 302 | 0.67 µW | 2.02 µm² |
| | H0 | 2 | 2 | **1** (pt1 M1 포화 −27 mV) | 3509 | 364 | 68 pW | 1.47 µm² |
| | H0r | 2 | 2 | **2** | 3500 | 332 | 2.46 nW | 3.24 µm² |
| current_reuse_telescopic_ota | C / H0box / H0 / H0r / H0rX | 0 전부(H 는 출발점 0) | 0 | **0** | 1112 / 333 / 0 / 23 / 159 | 713 / 214 / 148 / 133 / 586 | - | - |
| sf_pushpull_output_opamp | C / H0box / H0 / H0r / H0rX | 0 전부(H 는 출발점 0) | 0 | **0** | 2000 / 1500 / 0 / 81 / 584 | 110 / 95 / 76 / 96 / 451 | - | - |
| ngcc_3stage_ff | 전 변형 | 단계 A review_needed 로 탐색 전 정지 | 0 | **0** | 0 | - | - | - |

회로 수로 세면(저장소 spec, SPICE 통과 점 ≥ 1 인 회로):

| 변형 | 통과 회로 | C 대비 새로 통과한 회로 |
|---|---|---|
| C | common_gate (1/9) | - |
| H0box(정의 그대로) | common_gate (1/9) | **0** |
| H0(폭 창+거름) | common_gate, pushpull (2/9) | pushpull |
| H0r(폭 수준 역산+거름) | common_gate, two_stage_ota, folded_cascode*, pushpull (4/9) | **two_stage_ota, folded_cascode*, pushpull = 3** |
| H0rX(확대, nmcnr·folded o140·current_reuse·sf_pushpull 만) | 없음 | 0 |

\* folded_cascode 저장소 spec 은 성능 제약이 없고(SP-3/4/5 pending) 통과 점은 GBW 91 kHz·noise 1.98(경계 1 %)이다. O-140 사본 기준으로는 어느 변형도 0.

## 2. 점별 판정 표

각 표: spec 항목별 한계·SPICE·판정·엔진 예측(agent 인용, jsonl `metrics_graph`)·차. 원자료 `H/judge/res/h_results.jsonl`, `res/raw_<tag>.json`.

#### common_gate_amplifier.C.pt0 (엔진 점 None)

| spec 항목 | 한계 | SPICE | 판정 | 엔진 예측 | 차(SPICE−엔진) |
|---|---|---|---|---|---|
| noise_exc | <= 2 | 1.22 | PASS | - | - |
| 면적 µm² | <= 5000 | 0.2382 | PASS | - | - |
| (참고) 이득 dB | spec 없음 | 24 | - | - | - |
| (참고) GBW MHz | spec 없음 | 3.87 | - | - | - |
| (참고) PM° | spec 없음 | 90.1 | - | - | - |
| 포화(VDS−VDSAT ≥ 0, 전 소자) | ≥ 0 | 최소 0.537 V (XM1) | PASS | - | - |
| 전력(vdd) | - | 0.0003435 µW | - | 0.0001231 µW | +179.1 % |
| 입력 trim(SPICE)/엔진 입력차 | - | -48.45 mV | - | 0 mV | - |
| V(out) DC / 엔진 | - | 1.214 V | - | 1.214 V | - |

판정: common_gate_amplifier → 전 spec 통과+전 소자 포화. 잡음 측정법: dotnoise. 최대 W = M2 0.4751 µm, 최대 m = M1 1. SPICE 실행 6 회.

#### common_gate_amplifier.C.pt1 (엔진 점 None)

| spec 항목 | 한계 | SPICE | 판정 | 엔진 예측 | 차(SPICE−엔진) |
|---|---|---|---|---|---|
| noise_exc | <= 2 | 1.16 | PASS | - | - |
| 면적 µm² | <= 5000 | 0.2171 | PASS | - | - |
| (참고) 이득 dB | spec 없음 | 19.4 | - | - | - |
| (참고) GBW MHz | spec 없음 | 10.1 | - | - | - |
| (참고) PM° | spec 없음 | 93.4 | - | - | - |
| 포화(VDS−VDSAT ≥ 0, 전 소자) | ≥ 0 | 최소 0.0711 V (XM3) | PASS | - | - |
| 전력(vdd) | - | 0.001113 µW | - | 0.0002417 µW | +360.3 % |
| 입력 trim(SPICE)/엔진 입력차 | - | -97.48 mV | - | 0 mV | - |
| V(out) DC / 엔진 | - | 1.686 V | - | 1.686 V | - |

판정: common_gate_amplifier → 전 spec 통과+전 소자 포화. 잡음 측정법: dotnoise. 최대 W = M3 0.5943 µm, 최대 m = M1 1. SPICE 실행 6 회.

#### common_gate_amplifier.H0.pt0 (엔진 점 eps:area_search_m2:7)

| spec 항목 | 한계 | SPICE | 판정 | 엔진 예측 | 차(SPICE−엔진) |
|---|---|---|---|---|---|
| noise_exc | <= 2 | 1.44 | PASS | 1.53 | -5.9 % |
| 면적 µm² | <= 5000 | 1.475 | PASS | 1.475 | -0.0 % |
| (참고) 이득 dB | spec 없음 | 36.3 | - | - | - |
| (참고) GBW MHz | spec 없음 | 1.07 | - | - | - |
| (참고) PM° | spec 없음 | 44.8 | - | - | - |
| 포화(VDS−VDSAT ≥ 0, 전 소자) | ≥ 0 | 최소 0.0403 V (XM1) | PASS | - | - |
| 전력(vdd) | - | 6.824e-05 µW | - | 9.262e-07 µW | +7267.8 % |
| 입력 trim(SPICE)/엔진 입력차 | - | -104.3 mV | - | 0 mV | - |
| V(out) DC / 엔진 | - | 0.3248 V | - | 0.3248 V | - |

판정: common_gate_amplifier → 전 spec 통과+전 소자 포화. 잡음 측정법: dotnoise. 최대 W = M2 0.4229 µm, 최대 m = M1 1. SPICE 실행 5 회.

#### common_gate_amplifier.H0.pt1 (엔진 점 EP:s3)

| spec 항목 | 한계 | SPICE | 판정 | 엔진 예측 | 차(SPICE−엔진) |
|---|---|---|---|---|---|
| noise_exc | <= 2 | 1.38 | PASS | 1.32 | +5.0 % |
| 면적 µm² | <= 5000 | 0.6229 | PASS | 0.6229 | -0.0 % |
| (참고) 이득 dB | spec 없음 | 28.5 | - | - | - |
| (참고) GBW MHz | spec 없음 | 3.9e+03 | - | - | - |
| (참고) PM° | spec 없음 | 48.1 | - | - | - |
| 포화(VDS−VDSAT ≥ 0, 전 소자) | ≥ 0 | 최소 -0.027 V (XM1) | FAIL {'XM1': -0.027} | - | - |
| 전력(vdd) | - | 0.7182 µW | - | 0.1427 µW | +403.2 % |
| 입력 trim(SPICE)/엔진 입력차 | - | -59.67 mV | - | 0 mV | - |
| V(out) DC / 엔진 | - | 0.2046 V | - | 0.2046 V | - |

판정: common_gate_amplifier → 불합격. 잡음 측정법: dotnoise. 최대 W = M2 1.131 µm, 최대 m = M1 1. SPICE 실행 6 회.

#### common_gate_amplifier.H0box.pt0 (엔진 점 EA:s6)

| spec 항목 | 한계 | SPICE | 판정 | 엔진 예측 | 차(SPICE−엔진) |
|---|---|---|---|---|---|
| noise_exc | <= 2 | 1.27 | PASS | 1.33 | -4.4 % |
| 면적 µm² | <= 5000 | 3.067 | PASS | 3.067 | +0.0 % |
| (참고) 이득 dB | spec 없음 | 31.8 | - | - | - |
| (참고) GBW MHz | spec 없음 | 901 | - | - | - |
| (참고) PM° | spec 없음 | 55.3 | - | - | - |
| 포화(VDS−VDSAT ≥ 0, 전 소자) | ≥ 0 | 최소 0.0528 V (XM3) | PASS | - | - |
| 전력(vdd) | - | 0.6741 µW | - | 0.2668 µW | +152.7 % |
| 입력 trim(SPICE)/엔진 입력차 | - | -30.7 mV | - | 0 mV | - |
| V(out) DC / 엔진 | - | 1.579 V | - | 1.579 V | - |

판정: common_gate_amplifier → 전 spec 통과+전 소자 포화. 잡음 측정법: dotnoise. 최대 W = M2 4.861 µm, 최대 m = M1 1. SPICE 실행 5 회.

#### common_gate_amplifier.H0box.pt1 (엔진 점 EA:s4)

| spec 항목 | 한계 | SPICE | 판정 | 엔진 예측 | 차(SPICE−엔진) |
|---|---|---|---|---|---|
| noise_exc | <= 2 | 1.13 | PASS | 1.12 | +0.2 % |
| 면적 µm² | <= 5000 | 2.019 | PASS | 2.019 | -0.0 % |
| (참고) 이득 dB | spec 없음 | 33.1 | - | - | - |
| (참고) GBW MHz | spec 없음 | - | - | - | - |
| (참고) PM° | spec 없음 | - | - | - | - |
| 포화(VDS−VDSAT ≥ 0, 전 소자) | ≥ 0 | 최소 0.0348 V (XM1) | PASS | - | - |
| 전력(vdd) | - | 7.036 µW | - | 4.744 µW | +48.3 % |
| 입력 trim(SPICE)/엔진 입력차 | - | -36.18 mV | - | 0 mV | - |
| V(out) DC / 엔진 | - | 0.6904 V | - | 0.6904 V | - |

판정: common_gate_amplifier → 전 spec 통과+전 소자 포화. 잡음 측정법: dotnoise. 최대 W = M2 0.98 µm, 최대 m = M1 1. SPICE 실행 6 회.

#### common_gate_amplifier.H0r.pt0 (엔진 점 eps:area_search_m2:5)

| spec 항목 | 한계 | SPICE | 판정 | 엔진 예측 | 차(SPICE−엔진) |
|---|---|---|---|---|---|
| noise_exc | <= 2 | 1.2 | PASS | 1.37 | -12.5 % |
| 면적 µm² | <= 5000 | 3.909 | PASS | 3.909 | +0.0 % |
| (참고) 이득 dB | spec 없음 | 31 | - | - | - |
| (참고) GBW MHz | spec 없음 | - | - | - | - |
| (참고) PM° | spec 없음 | - | - | - | - |
| 포화(VDS−VDSAT ≥ 0, 전 소자) | ≥ 0 | 최소 0.258 V (XM1) | PASS | - | - |
| 전력(vdd) | - | 0.002461 µW | - | 0.0004566 µW | +439.0 % |
| 입력 trim(SPICE)/엔진 입력차 | - | -51.78 mV | - | 0 mV | - |
| V(out) DC / 엔진 | - | 0.6617 V | - | 0.6618 V | - |

판정: common_gate_amplifier → 전 spec 통과+전 소자 포화. 잡음 측정법: dotnoise. 최대 W = M1 0.8216 µm, 최대 m = M1 1. SPICE 실행 6 회.

#### common_gate_amplifier.H0r.pt1 (엔진 점 EP:s4)

| spec 항목 | 한계 | SPICE | 판정 | 엔진 예측 | 차(SPICE−엔진) |
|---|---|---|---|---|---|
| noise_exc | <= 2 | 1.29 | PASS | 1.39 | -7.2 % |
| 면적 µm² | <= 5000 | 3.244 | PASS | 3.244 | +0.0 % |
| (참고) 이득 dB | spec 없음 | 31.6 | - | - | - |
| (참고) GBW MHz | spec 없음 | - | - | - | - |
| (참고) PM° | spec 없음 | - | - | - | - |
| 포화(VDS−VDSAT ≥ 0, 전 소자) | ≥ 0 | 최소 0.159 V (XM3) | PASS | - | - |
| 전력(vdd) | - | 3.366 µW | - | 1.218 µW | +176.3 % |
| 입력 trim(SPICE)/엔진 입력차 | - | -45.42 mV | - | 0 mV | - |
| V(out) DC / 엔진 | - | 1.454 V | - | 1.454 V | - |

판정: common_gate_amplifier → 전 spec 통과+전 소자 포화. 잡음 측정법: dotnoise. 최대 W = M2 2.06 µm, 최대 m = M1 1. SPICE 실행 6 회.

#### folded_cascode.H0r.pt0 (엔진 점 EP:s5)

| spec 항목 | 한계 | SPICE | 판정 | 엔진 예측 | 차(SPICE−엔진) |
|---|---|---|---|---|---|
| offset_exc | <= 1.414 | 1.04 | PASS | 1.04 | +0.6 % |
| noise_exc | <= 2 | 1.98 | PASS | 1.92 | +3.2 % |
| 면적 µm² | <= 1e+04 | 1496 | PASS | 1496 | +0.0 % |
| 이득 dB | >= 70 | 80.4 | PASS (O-140 사본 전용) | - | - |
| GBW MHz | >= 10 | 0.0909 | FAIL (O-140 사본 전용) | - | - |
| PM° | >= 70 | 78.4 | PASS (O-140 사본 전용) | - | - |
| 포화(VDS−VDSAT ≥ 0, 전 소자) | ≥ 0 | 최소 0.0393 V (XM3) | PASS | - | - |
| 전력(vdd) | - | 2.681 µW | - | 2.665 µW | +0.6 % |
| 입력 trim(SPICE)/엔진 입력차 | - | 96.23 mV | - | 70.59 mV | - |
| V(out) DC / 엔진 | - | 0.8575 V | - | 0.8575 V | - |

판정: folded_cascode → 전 spec 통과+전 소자 포화, folded_cascode.o140 → 불합격. 잡음 측정법: alt_injection_bench. 최대 W = MP 253.7 µm, 최대 m = MP 51. SPICE 실행 36 회.

#### folded_cascode.H0r.pt1 (엔진 점 EP:s3)

| spec 항목 | 한계 | SPICE | 판정 | 엔진 예측 | 차(SPICE−엔진) |
|---|---|---|---|---|---|
| offset_exc | <= 1.414 | 1.55 | FAIL | 1.21 | +28.6 % |
| noise_exc | <= 2 | 3.2 | FAIL | 2 | +60.0 % |
| 면적 µm² | <= 1e+04 | 34.83 | PASS | 34.83 | +0.0 % |
| 이득 dB | >= 70 | 51.5 | FAIL (O-140 사본 전용) | - | - |
| GBW MHz | >= 10 | 6.71 | FAIL (O-140 사본 전용) | - | - |
| PM° | >= 70 | 75.2 | PASS (O-140 사본 전용) | - | - |
| 포화(VDS−VDSAT ≥ 0, 전 소자) | ≥ 0 | 최소 0.044 V (XM5) | PASS | - | - |
| 전력(vdd) | - | 15.45 µW | - | 13.28 µW | +16.3 % |
| 입력 trim(SPICE)/엔진 입력차 | - | -94.63 mV | - | -118.3 mV | - |
| V(out) DC / 엔진 | - | 1.047 V | - | 1.047 V | - |

판정: folded_cascode → 불합격, folded_cascode.o140 → 불합격. 잡음 측정법: dotnoise. 최대 W = M10 16.51 µm, 최대 m = M10 3. SPICE 실행 20 회.

#### nmcnr_amplifier.H0rX.pt0 (엔진 점 EP:s3)

| spec 항목 | 한계 | SPICE | 판정 | 엔진 예측 | 차(SPICE−엔진) |
|---|---|---|---|---|---|
| 이득 dB | >= 100 | 105 | PASS | 108 | -3.08 |
| GBW MHz | >= 0.816 | 0.138 | FAIL | 0.82 | -83.2 % |
| PM° | >= 70 | 26.7 | FAIL | 70.8 | -44.16 |
| ICMR V | >= 0.5 | 0.85 | PASS | 0.703 | +20.9 % |
| swing V | >= 0.5 | 1 | PASS | 1.06 | -5.4 % |
| offset_exc | <= 1.414 | 1.3 | PASS | 1.12 | +16.4 % |
| noise_exc | <= 2 | 2.67 | FAIL | 2 | +33.3 % |
| 면적 µm² | <= 2.5e+04 | 5702 | PASS | 5702 | -0.0 % |
| 포화(VDS−VDSAT ≥ 0, 전 소자) | ≥ 0 | 최소 0.202 V (XM105) | PASS | - | - |
| 전력(vdd) | - | 167.6 µW | - | 165.3 µW | +1.4 % |
| 입력 trim(SPICE)/엔진 입력차 | - | -148.9 mV | - | -140.6 mV | - |
| V(out) DC / 엔진 | - | 0.9 V | - | 0.9 V | - |

판정: nmcnr_amplifier → 불합격. 잡음 측정법: alt_injection_bench. 최대 W = M109 1334 µm, 최대 m = M109 267. SPICE 실행 405 회.
ICMR 창 [0.15, 1.0], swing 창 [0.25, 1.4](전폭 1.15 V).

#### pushpull_follower_buffer.H0.pt0 (엔진 점 eps:area_search_m2:58)

| spec 항목 | 한계 | SPICE | 판정 | 엔진 예측 | 차(SPICE−엔진) |
|---|---|---|---|---|---|
| Rout Ω | <= 1000 | 687 | PASS | 999 | -31.3 % |
| 면적 µm² | <= 5000 | 576 | PASS | 576 | +0.0 % |
| (참고) 이득 dB | spec 없음 | -3.74 | - | - | - |
| (참고) GBW MHz | spec 없음 | - | - | - | - |
| (참고) PM° | spec 없음 | - | - | - | - |
| 포화(VDS−VDSAT ≥ 0, 전 소자) | ≥ 0 | 최소 0.0152 V (XM6) | PASS | - | - |
| 전력(vdd) | - | 56.55 µW | - | 39.76 µW | +42.2 % |
| 입력 trim(SPICE)/엔진 입력차 | - | - mV | - | 0 mV | - |
| V(out) DC / 엔진 | - | 1.101 V | - | 1.082 V | - |

판정: pushpull_follower_buffer → 전 spec 통과+전 소자 포화. 잡음 측정법: None. 최대 W = M1 3269 µm, 최대 m = M1 654. SPICE 실행 2 회.

#### pushpull_follower_buffer.H0r.pt0 (엔진 점 L:EA:s3:5)

| spec 항목 | 한계 | SPICE | 판정 | 엔진 예측 | 차(SPICE−엔진) |
|---|---|---|---|---|---|
| Rout Ω | <= 1000 | 832 | PASS | 991 | -16.0 % |
| 면적 µm² | <= 5000 | 44.1 | PASS | 44.1 | -0.0 % |
| (참고) 이득 dB | spec 없음 | -3.93 | - | - | - |
| (참고) GBW MHz | spec 없음 | - | - | - | - |
| (참고) PM° | spec 없음 | - | - | - | - |
| 포화(VDS−VDSAT ≥ 0, 전 소자) | ≥ 0 | 최소 0.0553 V (XM5) | PASS | - | - |
| 전력(vdd) | - | 45.29 µW | - | 38.23 µW | +18.5 % |
| 입력 trim(SPICE)/엔진 입력차 | - | - mV | - | 0 mV | - |
| V(out) DC / 엔진 | - | 1.005 V | - | 0.9931 V | - |

판정: pushpull_follower_buffer → 전 spec 통과+전 소자 포화. 잡음 측정법: None. 최대 W = M1 151.7 µm, 최대 m = M1 30. SPICE 실행 2 회.

#### two_stage_ota.H0.pt0 (엔진 점 EP:s1)

| spec 항목 | 한계 | SPICE | 판정 | 엔진 예측 | 차(SPICE−엔진) |
|---|---|---|---|---|---|
| 이득 dB | >= 57 | 69.2 | PASS | 69.8 | -0.56 |
| GBW MHz | >= 7 | 1.04 | FAIL | 7.13 | -85.4 % |
| offset_exc | <= 1.414 | 1.17 | PASS | 1.16 | +0.8 % |
| noise_exc | <= 2 | 1.14 | PASS | 1.14 | +0.8 % |
| 면적 µm² | <= 1.5e+04 | 4379 | PASS | 4379 | +0.0 % |
| PM° | >= 70 | 44.1 | FAIL | 70.5 | -26.35 |
| 포화(VDS−VDSAT ≥ 0, 전 소자) | ≥ 0 | 최소 0.0771 V (XM5) | PASS | - | - |
| 전력(vdd) | - | 22.32 µW | - | 26.06 µW | -14.3 % |
| 입력 trim(SPICE)/엔진 입력차 | - | 227.4 mV | - | 226.5 mV | - |
| V(out) DC / 엔진 | - | 1.147 V | - | 1.147 V | - |

판정: two_stage_ota → 불합격. 잡음 측정법: dotnoise. 최대 W = M1 1.006e+04 µm, 최대 m = M1 2011. SPICE 실행 14 회.

#### two_stage_ota.H0.pt1 (엔진 점 EA:s6)

| spec 항목 | 한계 | SPICE | 판정 | 엔진 예측 | 차(SPICE−엔진) |
|---|---|---|---|---|---|
| 이득 dB | >= 57 | 63.3 | PASS | 63 | +0.28 |
| GBW MHz | >= 7 | 8.58 | PASS | 9.19 | -6.7 % |
| offset_exc | <= 1.414 | 1.18 | PASS | 1.18 | +0.2 % |
| noise_exc | <= 2 | 1.4 | PASS | 1.41 | -0.2 % |
| 면적 µm² | <= 1.5e+04 | 4290 | PASS | 4290 | +0.0 % |
| PM° | >= 70 | 69.9 | FAIL | 71 | -1.15 |
| 포화(VDS−VDSAT ≥ 0, 전 소자) | ≥ 0 | 최소 0.238 V (XM5) | PASS | - | - |
| 전력(vdd) | - | 188.1 µW | - | 199.3 µW | -5.6 % |
| 입력 trim(SPICE)/엔진 입력차 | - | -56.04 mV | - | -58.23 mV | - |
| V(out) DC / 엔진 | - | 1.443 V | - | 1.443 V | - |

판정: two_stage_ota → 불합격. 잡음 측정법: dotnoise. 최대 W = M6 883.3 µm, 최대 m = M6 177. SPICE 실행 14 회.

#### two_stage_ota.H0.pt2 (엔진 점 EA:s1)

| spec 항목 | 한계 | SPICE | 판정 | 엔진 예측 | 차(SPICE−엔진) |
|---|---|---|---|---|---|
| 이득 dB | >= 57 | 72.3 | PASS | 72.5 | -0.24 |
| GBW MHz | >= 7 | 1.56 | FAIL | 18.9 | -91.8 % |
| offset_exc | <= 1.414 | 1.17 | PASS | 1.27 | -7.6 % |
| noise_exc | <= 2 | 1.11 | PASS | 1.11 | +0.1 % |
| 면적 µm² | <= 1.5e+04 | 3801 | PASS | 3801 | +0.0 % |
| PM° | >= 70 | 66.4 | FAIL | 121 | -54.25 |
| 포화(VDS−VDSAT ≥ 0, 전 소자) | ≥ 0 | 최소 0.0429 V (XM5) | PASS | - | - |
| 전력(vdd) | - | 4136 µW | - | 4136 µW | +0.0 % |
| 입력 trim(SPICE)/엔진 입력차 | - | 217.2 mV | - | 218.2 mV | - |
| V(out) DC / 엔진 | - | 1.179 V | - | 1.179 V | - |

판정: two_stage_ota → 불합격. 잡음 측정법: dotnoise. 최대 W = M1 4575 µm, 최대 m = M1 915. SPICE 실행 13 회.

#### two_stage_ota.H0r.pt0 (엔진 점 EA:s1)

| spec 항목 | 한계 | SPICE | 판정 | 엔진 예측 | 차(SPICE−엔진) |
|---|---|---|---|---|---|
| 이득 dB | >= 57 | 59.6 | PASS | 59.7 | -0.03 |
| GBW MHz | >= 7 | 8.35 | PASS | 8.69 | -3.9 % |
| offset_exc | <= 1.414 | 1.1 | PASS | 1.1 | -0.0 % |
| noise_exc | <= 2 | 1.81 | PASS | 1.82 | -0.4 % |
| 면적 µm² | <= 1.5e+04 | 8031 | PASS | 8031 | -0.0 % |
| PM° | >= 70 | 70.9 | PASS | 71.9 | -1.08 |
| 포화(VDS−VDSAT ≥ 0, 전 소자) | ≥ 0 | 최소 0.0163 V (XM5) | PASS | - | - |
| 전력(vdd) | - | 397 µW | - | 396.9 µW | +0.0 % |
| 입력 trim(SPICE)/엔진 입력차 | - | -319.1 mV | - | -324.1 mV | - |
| V(out) DC / 엔진 | - | 0.3998 V | - | 0.3998 V | - |

판정: two_stage_ota → 전 spec 통과+전 소자 포화. 잡음 측정법: dotnoise. 최대 W = M6 1126 µm, 최대 m = M6 225. SPICE 실행 13 회.

#### two_stage_ota_sf.H0r.pt0 (엔진 점 EA:s2)

| spec 항목 | 한계 | SPICE | 판정 | 엔진 예측 | 차(SPICE−엔진) |
|---|---|---|---|---|---|
| 이득 dB | >= 57 | 59.9 | PASS | 59.9 | +0.03 |
| Rout Ω | <= 1000 | 905 | PASS | 914 | -1.0 % |
| GBW MHz | >= 7 | 11 | PASS | 11.2 | -1.2 % |
| offset_exc | <= 1.414 | 1.1 | PASS | 1.12 | -2.5 % |
| noise_exc | <= 2 | 1.29 | PASS | 1.28 | +0.3 % |
| 면적 µm² | <= 1.5e+04 | 1444 | PASS | 1444 | +0.0 % |
| PM° | >= 70 | 67.9 | FAIL | 70.4 | -2.49 |
| 포화(VDS−VDSAT ≥ 0, 전 소자) | ≥ 0 | 최소 0.0679 V (XM6) | PASS | - | - |
| 전력(vdd) | - | 687.3 µW | - | 686.3 µW | +0.1 % |
| 입력 trim(SPICE)/엔진 입력차 | - | 28.59 mV | - | 27.07 mV | - |
| V(out) DC / 엔진 | - | 0.9729 V | - | 0.9729 V | - |

판정: two_stage_ota_sf → 불합격. 잡음 측정법: dotnoise. 최대 W = M6 859.9 µm, 최대 m = M6 172. SPICE 실행 17 회.


## 3. 물리 타당성 (spec 통과와 별도 표시)

| 점 | spec 판정 | 물리 표시 | 근거(SPICE·netlist) |
|---|---|---|---|
| two_stage_ota H0r pt0 | 통과 | ⚠ **입력쌍 극단 비대칭**: M1 W 7.3 µm×1, M2 W 88.7 µm(m 18), 같은 L 2.5 µm → 출력 목표를 잡는 입력 trim **−319 mV**(엔진 입력차 −324 mV). M6 W 1.13 mm(L 0.15 µm, m 225), M3 W 640 µm(m 128). 최소 포화 여유 16 mV(M5). 전력 397 µW(armA 해 136 µW 의 2.9 배) | 입력 DC 미정(SP-2)·계통 offset 제약 부재를 탐색이 이용(앞선 판정 4-4 (a) 와 같은 현상, 더 큼). 실사용(두 입력 같은 CM)에서는 이 점이 출력 레일로 감 |
| two_stage_ota H0 pt0 / pt2 | FAIL | ⚠ **M1 W 10.06 mm(m 2011)** / 4.58 mm(m 915), 입력 trim +227 / +217 mV. 엔진 GBW 7.13 / 18.9 MHz 대 SPICE 1.04 / 1.56 MHz(**−85 / −92 %**), PM 70.5 / 121° 대 44 / 66° | mm 급 소자의 기생(미러 노드 D3 에 M1 드레인)이 극을 만들어 엔진 예측이 크게 틀림 |
| two_stage_ota H0 pt1 | FAIL | M6 W 883 µm(m 177), M2 W 241 µm(m 48) vs M1 8.6 µm, 전력 188 µW | PM 69.9° 경계 |
| two_stage_ota_sf H0r pt0 | FAIL | M6 860 µm, M8 708 µm, 전력 687 µW | PM 67.9°(엔진 70.4°, −2.5°) |
| folded_cascode H0r pt0 | 통과(저장소 spec) | 전력 2.68 µW, GBW 91 kHz(CL 1 pF), MP 254 µm·M3 203 µm·M4 171 µm(L 0.49 µm) 대 입력쌍 M1 0.44 µm·M2 0.65 µm(L 1 µm 대 8 µm) **입력쌍 L 8 배 비대칭**, trim +96 mV(엔진 +71 mV) | 성능 spec 이 없어 의미 있는 증폭기라 보기 어려움 |
| folded_cascode H0r pt1 | FAIL | 엔진 noise 2.00(경계)·offset 1.21 대 SPICE 3.20·1.55 — **엔진이 이 점을 크게 낙관**(좁은 폭 0.5~0.7 µm 소자 다수: 앞선 판정 5-2·6-2 의 '5 µm 슬라이스 밖 좁은 폭' 오차와 같은 계열) | |
| nmcnr H0rX pt0 | FAIL | M101 W 1.31 mm(m 262), M109 1.33 mm(m 267), M102 532 µm, M104 W 0.42 µm·L 20 µm, Cm2 0.10 pF; 엔진 GBW 0.82 MHz·PM 70.8° 대 SPICE 0.138 MHz·26.7°(**−83 %, −44°**), noise 2.00 대 2.67. ICMR 0.85 V(엔진 0.70)·swing 1.0 V(엔진 1.06) 는 PASS | 보상 루프 예측 실패 — 앞 단 mm 급 소자 기생 |
| pushpull H0 pt0 | 통과 | ⚠ **M1 W 3.27 mm(m 654)**, L 0.15 µm; V(out) 1.101 V(엔진 1.082), rout 687 Ω(엔진 999 Ω) | 면적 576 µm²(예산 5000 µm² 의 12 %) — 면적 예산은 지키지만 단일 소자 mm 급 |
| pushpull H0r pt0 | 통과 | M1 152 µm, M4 W 0.43 µm·L 20 µm, M5 0.45 µm; rout 832 Ω(엔진 991 Ω) | 타당한 범위 |
| common_gate 전 점 | 대부분 통과 | ⚠ **동작 전류 pA~nA**: C pt0 0.19 nA, H0 pt0 0.038 nA, H0r pt0 1.37 nA. 엔진 전력 대비 SPICE **+180 % ~ +7270 %**(누설·약반전 모델 오차), 입력 DC 가 엔진보다 30~104 mV 낮아야 같은 출력. CL 미선언(SP-6)이라 GBW 수 GHz 값은 무의미 | spec 이 noise·면적뿐이라 전력 최소화가 누설 수준 전류로 감 — 'spec 통과'가 쓸 만한 증폭기를 뜻하지 않음 |

면적 예산 위반: 없음(모든 점 SPICE 면적 = 엔진 면적, 차 < 0.01 %, 예산 안). m 과대·mm 급 W 는 위 표.

## 4. 엔진 예측 대비 SPICE (사람 개입 없는 front 점, 이득·GBW·PM 이 있는 점)

| 점 | 이득 dB (SPICE−엔진) | GBW % | PM ° | 비고 |
|---|---|---|---|---|
| two_stage_ota H0r pt0 | −0.03 | −3.9 | −1.1 | 통과 |
| two_stage_ota H0 pt1 | +0.3 | −6.6 | −1.1 | PM 경계 FAIL |
| two_stage_ota H0 pt0 | −0.6 | **−85** | **−26** | M1 10 mm |
| two_stage_ota H0 pt2 | −0.2 | **−92** | **−55** | M1 4.6 mm |
| two_stage_ota_sf H0r pt0 | +0.03 | −1.4 | −2.5 | PM FAIL |
| nmcnr H0rX pt0 | −3.1 | **−83** | **−44** | mm 급 |

엔진이 제약 경계(GBW·PM ≈ 한계 + 0.4~2 %)에 붙여 낸 점이라, '정상 크기' 점(H0r two_stage, sf)에서도 수 % 모델 오차가 PM 2.5° 부족으로 판정을 뒤집는다(앞선 판정 5-3 과 같은 성격). 극단 W 점에서는 예측이 수십 % 틀린다.

## 5. 질문에 대한 답

### Q1. H 가 C 대비 SPICE 통과 front 를 늘렸는가?

- **H0box(정의 그대로): 늘리지 않았다. 0 회로.** C 와 같은 common_gate 하나만 통과(C 2 점, H0box 2 점). two_stage_ota·sf·pushpull 은 front 0, folded·nmcnr·current_reuse·sf_pushpull 은 출발점 0.
- **H0r(작성자가 브리핑 밖에서 더한 선언 읽기 변형): 3 회로에서 늘렸다** — two_stage_ota(1 점), pushpull_follower_buffer(1 점), folded_cascode(1 점, 단 성능 제약 없는 저장소 spec 에서만이고 GBW 91 kHz·noise 경계). 성능 제약이 실린 회로로 좁히면 **two_stage_ota 1 회로·1 점**, 그 점도 입력쌍 비대칭(trim −319 mV)이 있다.
- H0r 이 front 를 낸 two_stage_ota_sf(PM 67.9°)·nmcnr H0rX(GBW −83 %, PM 26.7°)·folded pt1 은 SPICE FAIL. 작성자 보고의 'front 5 회로'는 SPICE 기준 3 회로(성능 spec 기준 1 회로).
- H0(폭 창+거름): pushpull 1 회로. two_stage_ota H0 의 front 3 점은 전부 SPICE FAIL.
- 확신도: 높음(측정). 표본 9 회로 중 ngcc 는 양쪽 모두 탐색 전 정지.

### Q2. 비용 대비 이득 (평가 수·벽시계는 agent 인용, 기록 내부 일치 확인)

| 회로 | C 평가 / 벽시계 | H0r 평가 / 벽시계 | 배수(평가, 벽시계) | SPICE 통과 증가 |
|---|---|---|---|---|
| two_stage_ota | 107 / 71 s | 3500 / 562 s | 33×, 7.9× | 0 → 1 |
| two_stage_ota_sf | 398 / 233 s | 3517 / 668 s | 8.8×, 2.9× | 0 → 0 |
| folded_cascode | 744 / 219 s | 2294 / 587 s | 3.1×, 2.7× | 0 → 1(성능 spec 없음) |
| nmcnr (H0r / H0rX) | 2000 / 630 s | 3266 / 831 s ; 4580 / 871 s | 1.6×, 1.3× ; 2.3×, 1.4× | 0 → 0 |
| pushpull | 212 / 47 s | 3013 / 159 s | 14×, 3.4× | 0 → 1 |
| common_gate | 89 / 39 s | 3500 / 332 s | 39×, 8.5× | 2 → 2 |
| current_reuse / sf_pushpull | 1112 / 713 s ; 2000 / 110 s | 23 / 133 s ; 81 / 96 s(출발점 0, 격자 생성이 대부분) | - | 0 → 0 |

- H0r 9 회로 총 커널 평가 ≈ 19,200(C ≈ 6,660), SPICE 통과 회로 +3(성능 spec 기준 +1). 평가당 이득은 작다. 격자 스크리닝 1500 평가가 고정비로 붙고(작성자 상수), C 가 이미 되는 회로(common_gate)에서도 39 배를 쓴다.
- H0box 는 비용(2700~3500 평가)만 늘고 이득 0.
- 벽시계는 5 병렬 간섭값이라 배수는 대략치.

### Q3. 어느 변형도 못 푼 회로의 막힘 원인

판정자가 작성자 격자를 같은 seed 로 재생성(`hlib.make_grid` import, 수정 없음)해 엔진 `kernel.evaluate` 로 다시 평가하고 FailureRecord 를 센 결과(`res/probe_fail.jsonl`; 실측):

| 회로 | 출발 생성 | 평가 결과 사유(개수) | 문제 소자·노드 | C 기록(인용) | 분류(확신도) |
|---|---|---|---|---|---|
| current_reuse_telescopic_ota | H0r 거름 통과 23/300,000(전류 원뿔 양수 조건), H0box 300 중 241 outside_domain(원뿔 행 M3a~M4b 음수) | H0r 23: SEAL_VIOLATION `no_root_in_window` 21, `lut_query_failed` 2. H0box 나머지 59: `no_root_in_window` 54, `lut_query_failed` 5 | M37b·M24b·M40(노드 Ncmfb_tail), M23a·M20b·M4a | 층 0 'converged', 봉인 62·feasible 0 | **출발 앞단(독립 표본이 원뿔·DC 봉인 창을 못 맞춤) + DC 봉인 창**. C 는 봉인 점 62 개를 만드나 feasible 0 → C 쪽은 봉인 뒤 제약(커널·spec) 단계에서 막힘. H 는 봉인 자체를 못 함 → H 격자가 C 출발보다 나쁘다(중간) |
| sf_pushpull_output_opamp | H0r 81/300,000, H0box 1500 전부 failed | H0r 81: `lut_query_failed` 60, `no_root_in_window` 21. H0box 300: `lut_query_failed` 234, `no_root_in_window` 65 | **M10(212/381 건)·M9**(노드 N910, 창 [0.93, 1.8] V 에서 근 없음) | 2000 평가 봉인 0, 층 0 `start_lut_query_failed+probe_eval_budget` | **같은 두 소자에서 C·H 모두 봉인 실패 → 출발 앞단보다 DC 봉인 창/LUT 정의역 쪽**(M9·M10 의 DC 역할·노드 창). 출발법을 바꿔도 같은 곳에서 막힘(중간 — 원인 확정은 dc_role/봉인 창 감사 필요) |
| ngcc_3stage_ff | - | 단계 A `review_needed`: `dc_role_unresolved_group M14,M8` | M14·M8 | 같음 | **dc_role 사실 부재 — 탐색 전 정지, 출발 앞단 무관**(높음) |
| (참고) folded_cascode H0box | 300 중 248 outside_domain(원뿔 M1·M11 음수) | `no_root_in_window` 21, `lut_mismatch_no_block` 14, 그 밖 | M6·M5·M2 | - | 상자 문자 그대로의 격자는 원뿔 밖이 대부분 |
| (참고) two_stage_ota H0box | 300 중 sealed 9 | `lut_mismatch_no_block` 219(예: W 5.5e-14 m) | M7·M6 | - | 상자 격자의 암시 폭이 LUT 밖 — 작성자 설명(상자 27 decade)과 일치 |

C 의 front 0 원인(two_stage_ota·folded): 앞선 판정 `cmp1_pilot_judgment.md` 케이스 4-3 인용 — "GB4 이득 상한 인증 실패 → 이득 L 하한 비활성 → 최소 L 칸 출발 → 칸 고정 SLSQP status 4 → LR10 L 탐색 미기동"(출발 앞단 원인, 확신도 높음). 이번 H0r 이 two_stage_ota 에서 통과 점을 낸 것은 그 판정과 정합(출발 L 을 격자로 바꾸면 커널·SLSQP 는 해를 찾는다).

### Q4. "출발 앞단을 고친다(C′)" vs "격자 출발로 대체(H)" 판단에 주는 근거와 한계 (권고 아님)

근거:
1. 커널·SLSQP 를 그대로 두고 출발만 바꾸면 C 가 못 푼 two_stage_ota 가 SPICE 통과 점을 낸다(H0r) → 앞선 판정의 '출발 앞단 결함' 결론을 독립 경로로 다시 지지한다.
2. 그러나 정의 그대로의 격자(H0box)는 0 회로 개선. 효과는 전부 선언(w_min, area_budget, current_cone, l_ties)을 읽는 거름·역산(H0r)에서 나왔다 — 즉 '격자'가 아니라 '선언에서 유도한 물리적 출발 창'이 효과의 원천이다. 이것은 C′(LA-1·Q1-2 (ii)·Q6-1 (A))가 하려는 '출발 구간을 선언·물리로 바로잡기'와 같은 성분이다.
3. H0r 통과 점의 질: 입력쌍 비대칭(trim −319 mV), mm 급 W(H0 점들), 경계 붙음(PM·GBW 1~3 % 여유) — 출발법과 무관하게 SP-2(입력 DC)·계통 offset·폭 슬라이스(Q6-1) 문제가 남아 SPICE 판정을 뒤집는다(sf PM −2.5°, H0 GBW −85~−92 %).
4. 막힌 회로 중 sf_pushpull·ngcc 는 출발법을 바꿔도 같은 소자/단계에서 막힌다(DC 봉인 창·dc_role). current_reuse 는 C 가 H 보다 더 멀리 간다(봉인 62 대 0).
5. 비용: H0r 은 C 의 1.6~39 배 평가, 고정 스크리닝 1500.

한계:
- 표본 9 회로, 그중 front 를 비교할 수 있는 회로 6. 통과 증가 3 회로 중 2 개(folded, pushpull)는 성능 제약이 없거나(SP-3/4/5) 약한 spec.
- H1(W-bin 슬라이스) 미실행 — Q6-1 (A) 의 효과는 이 결과로 판단 불가. 폭 효과가 큰 점(folded pt1 noise +60 %)이 있어 H1/C′ 의 Q6-1 부분이 판정을 바꿀 수 있다.
- C′ 미구현 — 'C′ 가 같은 회로를 푸는가'는 이 실험의 범위 밖.
- 단일 seed·N 1500·Q 7·k 6 한 설정(H0rX 만 확대). seed·N 감도 미측정.
- 벽시계는 5 병렬 간섭값.
- 엔진 예측은 agent 인용(jsonl) — SPICE 와의 차는 판정자 측정.

## 6. 원칙 점검 (실험 코드이므로 '엔진 반영 시 문제가 될 지점'으로 기록)

| 점검 | 결과 | 근거(파일:줄, 읽기) |
|---|---|---|
| graph 단일 정본 — 둘째 생산자 | ⚠ `hlib._cone_currents`(176-188)·`_w_window_ok`(219-248) 이 θ 와 `theta_schema.current_cone` 로 **MOS 전류·암시 폭 W = I·L/IDu 를 엔진 DC 블록 밖에서 다시 계산**. 엔진에 넣으면 소자 전류·W 의 둘째 writer. `_repair_idu`(191-216)는 그 값으로 θ ln_idu 를 역산 | 실측 읽기 |
| 새 cache·값 사본 | ⚠ 스크리닝 결과 `results` 리스트·`tops`(EvalResult 참조) 를 Python 메모리에 두고 `dict(r.theta)` 사본을 `find_front` 에 시작점으로 넘김(337행) — 시작점이 graph 필드가 아니라 사본. `diagnose`(264-279)는 `sctx.cache` 읽기만. 엔진 반영 시 '출발 격자'는 writer 하나인 graph 필드(예: start 열)여야 함 | 실측 읽기 |
| 엔진 함수 우회 | `patch_layer0`(282-290)가 `find_front.layer0_start` 를 런타임 스텁으로 교체(파일 불변). `sctx.eval_budget` 을 스크립트가 덮어씀(335행). 엔진 반영 시 층 0 의 graph 필드(start 결과)와 예산 회계가 바뀌는 지점 | 실측 읽기 |
| 순위 규칙 | `score`(251-257) = (수락 여부, 위반 행 수, Σlog1p(위반)) — 엔진 제약 분류(constraint_classes)와 별개의 새 집계 규칙 | 실측 읽기 |
| 회로·소자 이름 | `make_grid`·`patch_layer0`·`_repair_idu`·`_w_window_ok` 에 회로·소자 이름 없음(grep). 회로 목록은 구동기 `driver.py` 에만 | grep 실측 |
| 매직넘버·새 상수 | N_start 1500·Q 7·k 6·pool_factor 200(X: 1500)·seed 20261027 — RESULTS.md 근거는 '벽시계 10 분 안팎'·'예산 2000 을 시작점에 나눔'(실행 예산 근거, 물리·선언 근거 아님). Q 7 은 근거 없음. **`_repair_idu` 210행 `w_min·1e3`(면적 예산 미선언 시 폭 상한) 근거 없음**. 폭 창 상한 `area_budget/(n_MOS·L)` 은 '면적을 MOS 수로 균등 분배' 가정(선언에서 직접 나온 양 아님) | 실측 읽기 |
| 원래 취지와 다름 | H0/H0r 은 브리핑(상자 Q 수준 + L 앵커) 밖에서 작성자가 더한 변형 — 작성자 스스로 RESULTS.md 에 표시. 본 판정은 H0box 와 H0r 을 분리해 결론(§5 Q1) | |
| 판정 도구 자체 | `hjudge.py` 등은 판정 전용, 엔진에 배선하지 않음(절대원칙 '만들면 배선'의 예외: 판정 근거 생성 목적). trim 이분·잡음 대체법은 측정 방법 변경이므로 §0 에 차이를 적고 대체법을 6 점에서 `.noise` 와 대조(차 ≤ 3e-6) | |

## 7. 실측 / agent 인용 / 안 함

- 실측(판정자): 18 점 SPICE(op·AC·offset·noise·rout·ICMR/swing), 잡음 대체법 검증 6 점, Q3 실패 사유 재평가 5 회로·모드 6 묶음(엔진 import, 수정 없음), jsonl 시간 기록 내부 일치, 원칙 점검(코드 읽기·grep), git status 빈 출력.
- agent 인용: front 수, 평가 수, 벽시계, sealed/feasible 수, 엔진 metric 예측값(jsonl).
- 안 함: 코너·온도 견고성(spec 미요구), H1, C′, seed 감도, 작성자 front 밖 점의 SPICE, folded O-140 실행의 feasible 5 점(front 아님, netlist 없음).

## 8. 재현 명령 (MSYS2 bash)

```bash
cd C:/Users/HSLEE/Documents/Todoc/fpga/wt/_cmp_pilot/H/judge
python specdump.py two_stage_ota two_stage_ota_sf folded_cascode nmcnr_amplifier pushpull_follower_buffer common_gate_amplifier \
  C:/Users/HSLEE/Documents/Todoc/fpga/wt/_cmp_pilot/verify/o140/folded_cascode.sizing_spec.json > res/specs.txt
rm -f res/h_results.jsonl && python run_h_judge.py            # 18 점, 약 5 분(nmcnr ICMR/swing 이 대부분)
python summ.py > res/summary_final.txt && python mk_tables.py   # res/tables.md
rm -f res/noise_alt_validation.jsonl && python val_noise_alt.py # 잡음 대체법 대조
export PYTHONDONTWRITEBYTECODE=1                                 # Q3 (엔진 import, 회로당 1~2 분)
python probe_fail.py current_reuse_telescopic_ota wrep+wfilter 600; python probe_fail.py current_reuse_telescopic_ota box 300
python probe_fail.py sf_pushpull_output_opamp wrep+wfilter 600;     python probe_fail.py sf_pushpull_output_opamp box 300
python probe_fail.py folded_cascode box 300; python probe_fail.py two_stage_ota box 300
git -C C:/Users/HSLEE/Documents/Todoc/fpga/wt/integ-it12 status --short   # 빈 출력이어야 함
```
