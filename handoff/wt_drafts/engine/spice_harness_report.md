# SPICE 하네스 보고 (2026-10-07)

목표: 합격 시험의 SPICE 쪽 -- 엔진 출력 + topology.json -> ngspice 넷리스트(LUT 와 같은 모델/코너/온도) -> .op/.ac -> 엔진 예측 대 SPICE 비교표.
엔진 실행: `git clone --no-hardlinks gmid-light /c/g452/repo` (HEAD cb0ef86). 메인 저장소 2곳 무변경.

## 1단계: 있는 것 확인

- SPICE 관련 기존 코드
  - `skills/analog-gmid-design/assets/sky130_lut_sweep.py`: LUT 생성. 모델 = `C:\pdk\sky130_fd_pr\cells\{nfet,pfet}_01v8\..._tt.pm3.spice` + `__mismatch.corner.spice`, pfet 은 `models\parameters\lod.spice` 추가. W=5u nf=1 고정, ad=as=2.5p pd=ps=7u, `.temp` 없음(27C). npz 메타 corner="tt", temp_c=27.0. PDK 모델 파일은 디스크에 있음.
  - `workspaces/current-reuse-telescopic-ota-report/spice/*.py`: 단일 소자 .op 대조(gen_single_device.py, vgs_table.json 손입력)와 소신호(gm/gds 를 VCCS 로) MNA 교차검증뿐. **트랜지스터 수준 전체 회로 넷리스트 생성기는 없음.**
  - `references/spice-verification-workflow.md`: §1 폐루프 수렴 분해 절차, §2 LUT<->SPICE 교차검증(W=L*ID/IDu 로 만든 W 로 인스턴스화).
- 엔진 출력에 있는 것: `optimize_full_circuit_budget()` 반환 = theta_star, sizing(W/L/ID/gm/gds/gm_id/vds/vsb), metrics, pipeline_result(finger). **노드전압·VGS·보상 소자 derived 값(ctx.derived)은 반환에 없다** -- 노드전압은 엔진 함수 `propagate_node_voltages()`, VGS 는 `LUT.vgs_for_gm_id()` 로 하네스가 다시 불러 얻는다.
- 엔진 현황(engine_current_capability.md 와 같은 결과를 이번 복제본에서 재확인): current_reuse 완주(346s), folded_cascode 완주(36s, 제약 0건 자명해), two_stage_ota·nmcnr_amplifier 는 ValueError 로 W/L 출력 없음.

## 2단계: 만든 것

위치 `C:\Users\HSLEE\Documents\Todoc\fpga\wt\_drafts\engine\spice_harness\`

| 파일 | 역할 |
|---|---|
| `engine_dump.py <repo> <key> <out>` | 정본 spec(`run_harness.SPECS`/`canonical_spec`)으로 `optimize_full_circuit_budget()` 1회 실행 -> `<key>.engine.json`(theta_star·sizing·metrics·spec 스칼라·LUT 메타·엔진 예측 노드전압·소자별 VGS·게이트 넷 예측과 그 불일치 폭) + `<key>.instance.json`(`save_instance_json`) |
| `spice_harness.py <engine.json> <out> [옵션]` | 넷리스트 생성 -> ngspice `.op`(소자별 id/gm/gds/vth/vdsat/vgs/vds/vbs, 노드전압, I(vdd)) + `.ac`(wrdata) -> 비교 JSON(`*.compare.json`) + 표(`*.compare.md`). 단독 소자 대조(`*.iso.cir`)를 같이 돌린다 |
| `results/` | 이번 시험의 engine.json·instance.json·생성 넷리스트(.cir)·compare.json/.md |

넷리스트 규칙(전부 근거 파일에서 읽음, 하네스가 지어낸 상수 없음)
- 모델/코너/온도: LUT 스크립트 모듈을 import 해 `PDK_ROOT`·`LOD_SPICE` 를 그대로 쓰고, include 규칙도 LUT 스크립트와 같다. 코너·온도는 LUT npz 메타(corner=tt, temp_c=27) -> `.temp 27`. tt 가 아니면 멈춘다.
- 바디: NMOS=gnd, PMOS=vdd(엔진 `derive_vsb_from_nodes` 가정과 같음).
- 소자 기하 `--w-source layout|sizing`, `--finger-mode layout|lut_bin`: layout = instance.json finger 마다 w=finger_w·nf=1 인스턴스 병렬, lut_bin = sizing W 를 floor(W/5u) 개 nf=1 병렬(LUT 와 같은 모델 bin).
  - 실측 근거: ngspice 는 모델 bin 을 nf 로 나누지 않은 총 W 로 고른다. W=10u nf=2 가 5u 두 개보다 12% 작고, 총 W>100um 이면 "could not find a valid modelname" 으로 멈췄다. 그래서 nf 파라미터 대신 병렬 인스턴스.
- 전류원: topology `value_amp`, 없으면 theta_star 같은 이름. `--isrc engine` 이면 그 전류원이 먹이는 다이오드 소자의 엔진 ID.
- 수동소자: 저항 value_ohm / `nulling_reference_device` 면 1/gm(엔진 `_resolve_nulling_resistor_ohm` 규칙) / 없으면 1e9(엔진 `_DEFAULT_SENSE_RESISTOR_OHM`). 커패시터 value_farad / value_from_spec -> spec 값(엔진 ctx.derived 는 반환에 없어 spec 폴백, 주석으로 표시).
- 부하 C: `--cl` > spec `CL` > topology metrics 선언의 `CL`(엔진 PM 계산 가정). topology 가 출력-레일 C 를 갖고 있으면 그것만 쓴다.
- 구동 소자 없는 게이트 전용 넷(VB1~5, bias3 등): 엔진 예측 게이트 전압의 이상 전압원.
- 입력/되먹임(`--bias free`): 입력 DC 는 L=1e12 H, AC 는 C=1 F 로 넣는다. 단일 출력은 out -> input_n 을 (V_out_pred - V_in_pred) 만큼 내린 DC 되먹임, 차동 출력은 차동 성분 0.5*(Vom-Vop) 만 입력으로 되먹이고 입력 공통모드는 엔진 예측값에 고정(출력 공통모드는 회로 자신의 CMFB 몫). 출력 공통모드까지 되먹이면 출력이 레일에 붙는 해가 실측돼 이렇게 했다. `.nodeset` = 엔진 예측 노드전압(뉴턴 초기값일 뿐).
- `--bias forced`: 모든 내부 넷을 엔진 예측 전압에 L(1e12 H)로 묶는다. DC 동작점 = 엔진이 의도한 바이어스, 각 고정원 전류 = 그 넷의 KCL 잔차(엔진 바이어스가 실제 소자로 자기일관적인지의 척도), AC 에서는 L 이 열려 실제 모델(용량 포함) 선형화 개루프 응답. spice-verification-workflow.md §1(경계조건 고정 분해)의 회로 전체판.
- 측정: gain = |H(f_start=0.01Hz)|, UGF = |H|=1 교차(로그 보간), PM = 180 - (DC 위상 - UGF 위상), f-3dB, A0*f-3dB. 영역: |vds| >= |vdsat| + `--sat-margin`(기본 0) 이면 sat, id<1pA 면 off, vgs-vth 로 weak/moderate/strong.
- 허용오차: 하네스가 정하지 않는다. `--tol tol.json`(키 ID_rel, VGS_abs_V, gm_rel, gds_rel, node_abs_V, gain_db_abs, pm_deg_abs, ugf_rel, supply_rel) 을 주면 PASS/FAIL, 없으면 "N/A(tol 미설정)". 포화 여유도 매개변수.
- 비교 항목: 소자별 W(엔진 sizing / SPICE 실제), nf x 병렬과 bin, ID, VGS, VDS, VSB, gm, gds, gm/ID, VDSAT, VTH, 영역·반전 정도·포화 여유, 단독 소자 ID/gm/gds 오차. 넷별 엔진/SPICE 전압. 성능: 엔진 metrics 중 gain*/pm_deg 와 SPICE, spec GBW(있으면)·PM_target_deg, I(vdd) 대 엔진 supply_current_uA/power_uA, topology 선언 제약 중 SPICE 로 잴 수 있는 것(gain, pm) 판정.

## 3단계: 시험 결과

### 3.1 current_reuse_telescopic_ota (51 소자, 엔진 완주, 선언 제약 7/7 엔진 판정 만족)

같은 engine.json 으로 4가지 조건을 돌렸다(산출물 `results/current_reuse_telescopic_ota.<tag>.*`).

| 조건(tag) | gain dB (엔진 61.56 단합 / 67.08 MNA) | UGF Hz | PM deg (엔진 parasitic_pm 75.02) | I(vdd) uA (엔진 supply 82.02) | SPICE 포화 소자 |
|---|---|---|---|---|---|
| free, layout W, Iref=topology 1.2uA (`topo_iref`) | 동작 안 함(-206) | - | - | 244.3 | 30/51 |
| free, layout W, Iref=엔진 ID 0.199uA (`eng_iref`) | 동작 안 함(-177) | - | - | 41.6 | 32/51 |
| forced, layout W (`forced`) | 61.79 | 5.92e7 | 18.0 | 87.6 | 46/51 |
| **forced, 엔진 sizing W (`forced_sizingW`)** | **54.98** | **1.05e7** | **79.25** | **83.95** | 46/51 |

- free(회로가 스스로 DC 해를 찾음): 출력 Vop/Vom 이 1.8V 레일, 1단 출력 Vom1/Vop1 ~0.01V, 출력단 M15/M16 꺼짐. 엔진 예측 동작점이 자기일관적 DC 해로 실현되지 않는다(아래 4단계 원인).
- forced_sizingW(엔진이 의도한 노드전압·W 그대로): 선언 제약 gain_db>=54 -> 54.98 만족(엔진 61.56 보다 6.6dB 낮음, MNA 67.08 보다 12.1dB 낮음), parasitic_pm_deg>=70 -> 79.25 만족(엔진 75.02 보다 +4.2). spec 에 GBW 없음 -> UGF 10.45MHz 는 비교 대상 없음. f-3dB 18.8kHz.
- 포화 아님 5개(forced 두 조건 공통): M2a/M2b(엔진 VGS 1.157 인데 노드전압으로 정해지는 VGS 0.565 -> off), M3a/M3b(VGS 1.010 vs 엔진 0.784 -> triode), M5(VDS 0.027 vs 엔진 0.25 -> triode).
- KCL 잔차(forced 고정원 전류, sizing W): Vy 198uA, N64_63 -182uA, Vom1/Vop1 ~37uA, N3a4a/N3b4b ~34uA, Vbias3 -18uA -- 엔진 노드전압 집합이 실제 소자로는 전류가 맞지 않는다.
- layout W 로 바꾸면(forced) gain 은 61.8 로 오르나 PM 18도로 무너진다 -- instance.json 넷리스트 W 가 sizing W 와 29/51 소자에서 5% 넘게 다르다(M3a 3.49->36.02um, M58 1.69->36.02, M37a 5.0->36.02, M9b 1.05->36.02 등).
- 단독 소자 LUT 충실도(엔진 VGS/VDS/VSB 를 그대로 걸고 sizing W 를 LUT bin 병렬로): ID 오차 중앙값 3.3%, 10% 초과 19/51.
  - VSB > 0.8V(LUT VS 격자 상한 0.8 밖, 외삽): M9a/M18a -97.2%(vsb 0.825), M2a/M2b -35.0%(vsb 0.923).
  - 폭이 작아 LUT 기준폭 5um 와 다른 모델 bin: M58 +60%(1.69um), M9b/M18b -27%(1.05um), M12/M21/M66/M68 -19~-20%(1.2~1.3um), M14/M23/M24/M64 -11~-12%.
  - L=0.15um, W=9.1um(모델 bin [7,100]um): M16/M26 +32%.

### 3.2 folded_cascode (13 소자, 엔진 완주하나 constraints 0건 -> Ibg 하한 자명해)

| 조건 | gain dB (엔진 41.06) | PM (엔진 87.22) | I(vdd) uA (엔진 power 9.5) | 포화 |
|---|---|---|---|---|
| free, layout W (`folded_cascode`) | 동작 안 함(-173) | - | 0.54 | 5/13 |
| forced, sizing W (`forced_sizingW`) | -6.5 | - | 0.51 | 9/13 |

- 엔진 예측 노드전압 자체가 물리적으로 불가능: vin_p/vin_n -0.85V, Vg9 -0.65V, Vg7 -0.20V(레일 밖), propagate 충돌 X(1.6 vs 0.0V)·Y·Vg9·out 4건(최대 1.6V). forced 모드 KCL 잔차 X -4.3mA, out 3.8mA. 비교 수치는 하네스 동작 확인용일 뿐 성능 판정 의미 없음.
- 엔진 sizing W 와 instance W 가 크게 다름: M10 1.12->39.0um, M11 1.04->27.7um.
- 공통 노트: PM 은 개루프 A(β=1) 기준이다. current_reuse 의 Cf/Cs(입력측 커패시터)는 회로에 그대로 두고 입력을 이상 AC 원으로 구동하므로, 엔진 parasitic_pm_deg 가 β(Cf/Cs) 루프 이득 기준이라면 정의 차이가 남는다.

### 3.3 two_stage_ota, nmcnr_amplifier
엔진이 W/L 을 내지 않아 SPICE 대조 불가(4단계 목록).

## 4단계: 막힌 점(정확한 원인)

1. **two_stage_ota 엔진 실패** -- `ValueError: 'stage1_out' 그룹의 VDS 합(2.37965V)이 vdd(1.8V)와 불일치(diff=+0.579654V)` (sizing_recipe `_hr_verify_group_kvl_sum`). W/L 없음 -> SPICE 불가.
2. **nmcnr_amplifier 엔진 실패** -- `모든 theta 격자점이 infeasible ... 'stage2_diode_ref' 그룹(예산 1.5V, 미해결 ['M203']) ... M203∈[0.6375,0.975]`. W/L 없음.
3. **엔진 예측 동작점이 자기일관적이지 않음(free 모드 DC 해가 엔진 동작점으로 안 감)** -- 엔진은 소자마다 vds 를 따로 정하고 노드전압은 `propagate_node_voltages()` 로 사후 복원한다. 복원 충돌: current_reuse 4건 0.223V(M5/Vy, M64/Vbias3, M1a/N1a2a, M1b/N1b2b), folded_cascode 4건 최대 1.6V. 같은 게이트 넷을 공유하는 소자들이 요구하는 게이트 전압 차(엔진 VGS 기준): current_reuse Vbias2 0.89V, Vbias3 0.65V, Voc_des 0.55V, N14a14b 0.26V, N11b 0.15V, Vip/Vim 0.11V. 엔진 결과에 노드전압·VGS·KCL 잔차가 정본 출력으로 없다(하네스가 엔진 함수로 다시 계산).
4. **topology 전류원 값과 엔진 전류 불일치** -- current_reuse `ideal_sources.Iref.value_amp=1.2e-6` 인데 엔진은 M18_bg 에 ID 0.1993uA(theta `r_biasgen`=0.02 계열)를 쓴다. topology 값으로 SPICE 를 돌리면 bias 가지 전류가 5~6배(1.19~1.45uA). 하네스는 `--isrc engine` 으로 엔진 값을 쓸 수 있게 했고 차이를 경고로 남긴다. 어느 쪽이 정본인지는 사용자 결정.
5. **instance.json 넷리스트 W != 엔진 sizing W** -- finger 배정/매칭 수리 단계가 W 를 바꾸지만 그 W 로 gm/ID 를 다시 계산하지 않는다(current_reuse 29/51 소자 >5%, 최대 10배; folded M10 35배). layout W 로 SPICE 를 돌리면 PM 79->18도. "엔진 예측과 SPICE 비교"의 기준 W 를 어느 쪽으로 할지 정해야 한다(하네스 `--w-source`).
6. **LUT 범위/기하 밖 사용** -- (a) VSB 가 LUT VS 격자 상한 0.8V 를 넘는 소자(current_reuse M2a/M2b 0.923, M9a/M18a 0.825; folded M1/M2 1.6, M5 1.8, M7 -0.65)는 외삽이라 단독 ID 오차 -35~-98%. (b) 엔진은 W 를 5um 기준 LUT 에 선형 비례로 쓰는데 sky130 모델은 W bin 마다 다르다: 작은 W(1~2um) -11~-27%/+60%, W>7um 은 [7,100]um bin(L=0.15 에서 +32%). (c) ngspice 는 nf 로 bin 을 나누지 않아 finger 는 nf=1 병렬로 넣어야 한다(하네스 처리 완료, 확산 공유 효과는 빠짐).
7. **엔진 결과 dict 에 보상 소자 derived 값이 없음** -- Cc 등은 `ctx.derived` 에 있을 수 있으나 반환에 없어 spec 값(Cc=Cf=Cs=500fF, C_Ltot=1pF)으로 폴백했다. Rz 는 엔진 규칙(1/gm(M16)=2118.5Ω)으로 재계산해 metrics `rz1_ohm` 과 같다.
8. **비교 기준 정의가 비어 있음(사용자 결정)** -- 허용오차 값 전부, 포화 여유 `--sat-margin`, gain 을 엔진의 어느 metric(gain_db 단합 vs gain_full_circuit_db MNA)과 비교할지, PM 정의(개루프 A vs β 루프), GBW 예측(current_reuse·folded 는 spec 에 GBW 없음, two_stage/nmcnr 만 spec GBW). folded_cascode·nmcnr 는 topology constraints 가 비어 있어 SPICE 판정 기준 자체가 없다.

## 5단계: 정리
- 실행·임시 디렉터리 `/c/g452`(복제본·임시 넷리스트·로그) 삭제. 결과물은 `spice_harness/results/` 에 남김. 재실행 시 `engine_dump.py` 를 먼저 돌려 engine.json/instance.json 을 새로 만들 것(results 의 engine.json 안 경로는 삭제된 /c/g452 를 가리킨다).
- 메인 저장소 chip-design-skills, gmid-light: 쓰기·git 조작 없음.
