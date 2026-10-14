# cnr_ota (held-out D, 판독 이름 D_cnr) -- spec 원문 표 추출

> 저장소 등록 메모(2026-10-14): 사이징 spec 은 `cnr_ota.sizing_spec.json` 이다. 사용자 결정 user_decisions.md 2026-10-14 held-out D
> "U1~U9 모두 권고대로"(원문 = wt/_heldout/D_cnr/VERIFY.md 1절)에 따라 원문 값에서 아래만 옮겼다(값 조정 없음; 원문 PDK = 엔진 PDK = sky130).
>
> | spec 자리 | 값 | 원문 (GitHub `wulffern/cnr_ota_sky130nm` @ `8c839f7`) |
> |---|---|---|
> | 제약 `gain_ss_db >=` | 68.58 | `sim/CNR_OTA/README.md` 35행 lstb lf_gain Sch_typ (U8 beta=1 해석 -> 개방 이득) |
> | 제약 `gbw_ss_hz >=` | 8.15e6 | 같은 파일 43행 lstb ug Sch_typ (U8 beta=1 -> 단위이득 주파수 = GBW) |
> | 제약 `pm_ss_deg >=` | 54.92 | 같은 파일 39행 lstb pm_deg Sch_typ |
> | 결정 대기 `pending_constraints` `supply_current_dc` (U-75) | (92e-6 A, 판정 안 함) | `README.md` 75행 'Current from VDD 92 uA' (아래 2절) |
> | `supplies_v` | VDD_1V8 1.8, VSS 0 | `README.md` 71행 AVDD typ 1.8 V; `sim/CNR_OTA/lstb.spi` 26·27행 |
> | `element_values.CL1`·`CL2` (measurement_load) | 5e-12 F 각각 | `sim/CNR_OTA/load.spi` 10·11행 (U3 (a)) |
> | `element_values.IDC` | 2e-6 A, [VSS, IBPSR] | `sim/CNR_OTA/load.spi` 3행 (U2 (a)) |
> | `element_values.C1`·`C2` | 5.38e-14 F 각각 | PDK 파라미터로 계산 (U5 (a), 아래 4절) |
> | `element_values.x37`·`x38`·`x39`·`x40`·`x9`·`x3` | 결정 대기 U-75 | res_high_po PDK 셀 모델이 이 PC 에 없음 (U5 (a), 아래 4절) |
> | `input_dc` | 결정 대기 U-75 | 측정 TB 에 OTA 입력 CM 값 없음 (아래 3.2절) |
> | `feedback.elements` | [] (beta=1 루프) | U3 (a) 저항 귀환망 제외 + U8 beta=1 해석 (아래 3.1절) |
> | `driving_spec` | 없음 | 원문에 slew 없음 |
>
> 보고만(spec 에 넣지 않음): f3db, gain margin, CMFB 루프(lstbcmfb) 전 항목, 코너(Sch_etc)·Monte Carlo(Sch_std) 값 -- 아래 2·5절.

## 0. 출처와 로컬 사본

| 무엇 | 웹 | 로컬 사본 |
|---|---|---|
| 저장소 (커밋 `8c839f7`, 2024-03-01 "Updated readme") | https://github.com/wulffern/cnr_ota_sky130nm/tree/8c839f7 | -- |
| 회로도 `design/CNR_OTA_SKY130NM/CNR_OTA.sch` (마지막 수정 `31b9389`, 2024-02-03) | https://github.com/wulffern/cnr_ota_sky130nm/blob/8c839f7/design/CNR_OTA_SKY130NM/CNR_OTA.sch | `wt/_heldout/wulff/CNR_OTA.sch` (줄바꿈만 다름, 줄 번호 같음) |
| 회로도 그림 `documents/CNR_OTA_SKY130NM/CNR_OTA.svg` | https://github.com/wulffern/cnr_ota_sky130nm/blob/8c839f7/documents/CNR_OTA_SKY130NM/CNR_OTA.svg | `wt/_heldout/wulff/CNR_OTA.svg` |
| 저장소 README (Key parameters, Signal interface) | https://github.com/wulffern/cnr_ota_sky130nm/blob/8c839f7/README.md | `wt/_scratch_heldout_d/src/README_top.md` |
| 결과표 `sim/CNR_OTA/README.md` (cicsim, 2024-02-03) | https://github.com/wulffern/cnr_ota_sky130nm/blob/8c839f7/sim/CNR_OTA/README.md | `wt/_heldout/wulff/README.md` (같은 파일) |
| 결과표 메타 `sim/CNR_OTA/summary.yaml` | https://github.com/wulffern/cnr_ota_sky130nm/blob/8c839f7/sim/CNR_OTA/summary.yaml | `wt/_heldout/wulff/summary.yaml` |
| TB `sim/CNR_OTA/{load,lstb,tran,lstbcmfb,xdut}.spi`, `lstb.meas`, `lstb.yaml` | https://github.com/wulffern/cnr_ota_sky130nm/tree/8c839f7/sim/CNR_OTA | `wt/_scratch_heldout_d/src/` |
| 설계 서술 `design/CNR_OTA_SKY130NM/CNR_OTA.md` | https://github.com/wulffern/cnr_ota_sky130nm/blob/8c839f7/design/CNR_OTA_SKY130NM/CNR_OTA.md | `wt/_scratch_heldout_d/src/CNR_OTA.md` |
| 하위 셀 (MOS / 저항) | https://github.com/wulffern/cnr_atr_sky130nm , https://github.com/wulffern/sun_tr_sky130nm | 판독 기록 `wt/_heldout/D_cnr/D_cnr.flat_lib20240301.json`, `D_cnr.sizes.md` |
| sky130 PDK (엔진 LUT 생성에 쓴 것과 같은 checkout) | https://github.com/google/skywater-pdk-libs-sky130_fd_pr | `C:/pdk/sky130_fd_pr` (`assets/sky130_pdk_decl.json` `pdk_root`) |

## 1. 저장소 README.md "Key parameters" (설계자 요약, 67~76행)

| 항목 | Min | Typ | Max | 단위 | 행 |
|---|---|---|---|---|---|
| Technology | | Skywater 130 nm | | | 70 |
| AVDD | 1.7 | 1.8 | 1.9 | V | 71 |
| Temperature | -40 | 27 | 125 | C | 72 |
| Loop gain (fb=500k, in=100k) | 63 | 68 | 72 | dB | 73 |
| Bias current | | 2 | | uA | 74 (+ Signal interface 52행 `IBPSR ... Bias current (2 uA)`) |
| Current from VDD | | 92 | | uA | 75 |
| Load capacitance | 5 | | | pF | 76 |

Signal interface 표(42~53행): VIN Negative input(46), VIP Positive input(47), VOP Positive output(48), VON Negative output(49), LPCO Common mode loop output(50), LPCI 'Common mode loop input. Short to LCPO'(51), IBPSR(52), VSS(53).

## 2. sim/CNR_OTA/README.md -- 차동 루프 `lstb` (Tian/Middlebrook 루프 이득, 20~45행)

spec 열은 `sim/CNR_OTA/lstb.yaml` 의 min/typ/max 와 같다. 측정식 = `sim/CNR_OTA/lstb.meas` 10~20행.

| 항목 | 측정식 (`lstb.meas` 행) | spec min / typ / max | Sch_typ | Sch_etc (min / typ / max) | Sch_std (mean-σ / mean / mean+σ) | README 행 |
|---|---|---|---|---|---|---|
| idd (VDD 전류) | `-i(vdd)` @ op (10) | -80 / 100 / 120 uA | 90.682 uA | 86.596 / 90.487 / 93.600 | 89.108 / 90.730 / 92.351 | 22~25 |
| f3db | `when lg_phase=135` (18) | 0.1 / 3 / 15 kHz | 3.315 kHz | 1.887 / 3.417 / 6.370 | 3.022 / 3.279 / 3.536 | 26~29 |
| gain margin gm_db | `find lg_mag when lg_phase=0` (16) | -50 / -10 / -10 dB | -14.22 dB | -15.86 / -14.30 / -12.65 | -14.42 / -14.22 / -14.02 | 30~33 |
| DC gain lf_gain | `find lg_mag at=1` (20) | 60 / 75 / 80 dB | **68.58 dB** | 63.71 / 68.14 / 71.85 | 68.09 / 68.70 / 69.32 | 34~37 |
| phase margin pm_deg | `find lg_phase when lg_mag=0` (17) | 45 / 60 / 90 deg | **54.92 deg** | 49.25 / 55.24 / 60.54 | 54.25 / 54.91 / 55.57 | 38~41 |
| unity gain ug | `when lg_mag=0` (19) | 0.5 / 1 / 10 MHz | **8.15 MHz** | 6.68 / 7.90 / 9.42 | 7.99 / 8.15 / 8.32 | 42~45 |

코너: Sch_typ = `Gt Ktt Tt Vt`, Sch_etc = `Kss,Kff,Ksf,Kfs` x `Th,Tl` x `Vl,Vh`, Sch_std = `Kttmm` 10회 (`sim/CNR_OTA/Makefile`; summary.yaml 21~28행 결과 경로).
spec 제약은 Sch_typ 열(굵게)만 옮겼다. README Key parameters 의 "Loop gain 63/68/72 dB" 는 이 lf_gain 행(Sch_etc 63.71/68.14/71.85)을 반올림한 값으로 보인다(대응은 추정).

**VDD 전류(결정 대기 U-75)**: README 75행 'Current from VDD 92 uA'(정확히 92 인 결과 행은 없음 -- Sch_std mean+σ 92.351 이 가장 가깝다), 결과표 idd Sch_typ 90.682 uA. 측정식은 `-i(vdd)` = VDD_1V8 레일 전류만이고 IDC(2 uA, 노드 0 -> IBPSR)는 들어가지 않는다. 판정 제약에 넣지 않은 이유: 엔진 `supply_current_dc` 는 합산 레일 선언(counted_rails, DEC-78)이 있어야 정의되는데 spec 선언 칸이 아직 없다(설계 gap N12) -- held-out A·B·C 와 같은 처리. user_decisions.md 2026-10-14 U8 원문 줄에는 "IDD <= 92 uA" 로 적혀 있으나 등록 지시(오케스트레이터)에 따라 pending 으로 두었다.

## 3. beta 해석(U8)과 입력 DC

### 3.1 beta = 1 해석 근거 (사용자 U8 확정)

* 결과표 TB `sim/CNR_OTA/lstb.spi`: 전원 26·27행, LPCI-LPCO 단락 30행 `vlp1 lpci lpco dc 0`, DUT 35행 `.include ../xdut.spi`, 부하·귀환망 37행 `.include ../load.spi`, balun 41·42행 `xb1 LPO VCM VOP VON balun`, `xb2 LPI VCM LOP LON balun`, Tian 프로브 46행 `X999 LPI LPO loopgainprobe`.
* `load.spi` 5~8행: `R1 VSIP VIP 100k`, `R2 VSIN VIN 100k`, `R3 LOP VIN 500k`, `R4 LON VIP 500k`.
* `lstb.spi` 에는 VSIP·VSIN·VCM 을 정하는 소스가 **없다**(같은 폴더 `lstbcmfb.spi` 29~31행, `tran.spi` 37~39행에는 있다). 그러면 R1/R2 의 VSIP/VSIN 쪽 끝이 떠 있어 AC 에서 VIN = LOP, VIP = LON 이 되고 귀환 계수 beta = 1(입력 용량 무시)이다.
* 따라서 lf_gain 68.58 dB = 개방 루프 차동 이득, ug 8.15 MHz = beta=1 단위이득 주파수(= GBW), pm_deg 54.92 = beta=1 위상 여유로 읽는다. README 표 제목 "(fb=500k, in=100k)" 대로 beta = 100k/600k = 1/6 이라면 개방 이득은 약 84 dB 가 되지만, 사용자 U8 이 beta=1 해석을 확정했다.
* 엔진 쪽 대응: spec `feedback.elements = []`(선언된 되먹임 수동소자 없음 -> beta=1 루프, user_decisions.md 2026-10-07 9번 PM 정의). topology 에는 귀환망 R1~R4 를 넣지 않았다(U3 (a)).

### 3.2 입력 DC -- 결정 대기 U-75

* `lstb.spi`(결과표 TB)에는 OTA 입력 CM 을 정하는 소스가 없다 -- 입력 DC 는 500k 귀환(R3/R4)과 balun CM 을 거쳐 출력 CM(회로 안 CMFB 가 정함)을 따라간다.
* `tran.spi` 37행 `VCM VCM 0 dc {AVDD/2}`(= 0.9 V)와 `lstbcmfb.spi` 29행의 VCM 은 100k 입력 저항 바깥 **소스 쪽** CM 이다. OTA 입력 핀 DC 는 저항 분배(5:1)로 출력 CM 쪽에 끌린다.
* 설계 서술 `CNR_OTA.md` 17~18행 'The input common mode cannot be VDD/2. The threshold voltage of the input pair is too large for that', 30~33행 '출력 CM 을 일부러 높여 저항 귀환이 tail 전류원을 포화에 두는 입력 CM 을 주게 했다' -- 입력 CM 은 VDD/2 가 아니고 숫자는 적혀 있지 않다.
* 결론: 원문에 OTA 입력 핀 DC 값이 없어 `input_dc` 는 `{"pending": "U-75"}`(지시: 근거가 없으면 pending).

## 4. 소자 값 (U5 (a): PDK 모델로 계산, 값을 지어내지 않음)

### 4.1 MIM 커패시터 C1, C2 -- 계산함

* 소자: `CNR_OTA.sch` 632행 `C1 ... model=cap_mim_m3_1 W=5 L=5 MF=1`, 633행 `C2 ... W=5 L=5 MF=1` (단위 um).
* PDK 파라미터(로컬): `C:/pdk/sky130_fd_pr/models/r+c/res_typical__cap_typical__lin.spice` (sha256 dc4243210bb6bf59d31a1cdc935b6116cfcb1c6e4d6213d7bbc0c7ebaa5f0848 -- `assets/sky130_pdk_decl.json` 의 선언 sha256 와 같은 파일, sky130.lib.spice tt 절이 include)
  * 7행 `+ camimc=  2.00e-15  $ Units: farad/micrometer^2` (면적 용량)
  * 8행 `+ cpmimc = 0.19e-15 $ Units: farad/micrometer` (둘레 용량)
  * 웹: https://github.com/google/skywater-pdk-libs-sky130_fd_pr/blob/main/models/r%2Bc/res_typical__cap_typical__lin.spice
* 식: C = MF x (camimc x W x L + cpmimc x 2 x (W + L)) = 1 x (2.00e-15 x 25 + 0.19e-15 x 20) = 5.0e-14 + 3.8e-15 = **5.38e-14 F (53.8 fF)**.
* 식의 근거: cap_mim_m3_1 셀 모델 원본(`cells/cap_mim_m3/sky130_fd_pr__cap_mim_m3_1.model.spice`, `models/capacitors/sky130_fd_pr__model__cap_mim.model.spice` 16행이 include)은 로컬에 없다. 그래서 (1) 파라미터 단위(F/um², F/um)대로 면적 x 면적 용량 + 둘레 x 둘레 용량으로 묶고, (2) 같은 식이 xschem sky130 심볼 `cap_mim_m3_1.sym` 24행 표시식 `C=expr_eng(@MF * (@W * @L * 2e-15 + ( @W + @L ) * 0.38e-15) )`(0.38e-15 = 2 x cpmimc)와 같음을, (3) 원본 그림 `documents/CNR_OTA_SKY130NM/CNR_OTA.svg` 302·309행 글자 `C=5.38e-14`(xschem 이 C1·C2 에 대해 계산해 그린 값)와 값이 같음을 확인했다. 심볼 사본: `wt/_scratch_heldout_d/src/cap_mim_m3_1.sym`(이전 판독 세션이 받은 xschem sky130 심볼, 받은 저장소 커밋 기록 없음).
* 값은 spec `element_values.C1/C2.value_farad` 에만 둔다(F5 요소 값 정본 = spec). topology 값 칸은 판독본처럼 null -- topology 에 값을 채우면 connectivity_fp 가 바뀐다(2456805b... -> c59c8f57..., 실측).

### 4.2 저항 x37, x38, x39, x40, x9, x3 -- 계산 못 함 (결정 대기 U-75)

* 소자: `CNR_OTA.sch` 634행 x37, 635행 x38, 642행 x39, 643행 x40, 681행 x9 = `SUNTR_RPPO16`(res_high_po W=0.72 um 16개 직렬), 701행 x3 = `SUNTR_RPPO4`(4개 직렬). 세그먼트 L = 8.8 um (U6 (a) 2024-02 라이브러리; sun_tr `294c65b` 2024-10-04 뒤 HEAD 는 8.96 um). 판독 기록 `wt/_heldout/D_cnr/D_cnr.flat_lib20240301.json`.
* 필요한 PDK 모델: `sky130_fd_pr/cells/res_high_po/sky130_fd_pr__res_high_po.model.spice`(및 `_0p35`~`_5p73`) -- `C:/pdk/sky130_fd_pr/models/sky130_fd_pr__model__linear.model.spice` 30·37~41행이 include 하는 파일. **로컬 PDK 에 없다**(`C:/pdk/sky130_fd_pr/cells/` 에 nfet_01v8·pfet_01v8 만; `C:/Users/HSLEE`, `C:/ngspice`, `C:/oss-cad-suite`, `C:/pdk` 전체 검색 결과 0건). 엔진 core CONTRACT 9.7 도 같은 사실을 적어 두었다(res_high_po 시트 저항 읽을 수 없음).
* 로컬 `res_typical__cap_typical__lin.spice` 4·5행의 `sky130_fd_pr__res_high_po__var(_mult) = 0.0` 은 공정 변동 파라미터일 뿐 면저항·끝저항이 아니다.
* 참고 후보(PDK 모델 아님, spec 에 넣지 않음): xschem 심볼 `res_high_po.sym` 49행 표시식 `R=expr_eng( (378.3 + 317.17 * @L ) / @W / @mult )` 로 세그먼트(W=0.72, L=8.8)는 약 4.40 kΩ -> RPPO16 약 70.4 kΩ, RPPO4 약 17.6 kΩ. 이 식의 PDK 근거를 이 PC 에서 확인할 수 없어 쓰지 않았다 -- 사용자 결정 또는 PDK 모델 파일 확보 뒤 계산.
* spec: `element_values.<x37|x38|x39|x40|x9|x3> = {"pending": "U-75"}`. 로더 영향: `load_sizing_spec` 은 통과(pending 6건으로 모임), `build_s1` 통과, `run_stage_a` 는 아래 6절 결과.

## 5. sim/CNR_OTA/README.md -- 공통모드 루프 `lstbcmfb` (CMFB 루프 이득, 47~75행) -- 보고만

| 항목 | spec min / typ / max | Sch_typ | Sch_etc (min / typ / max) | Sch_std |
|---|---|---|---|---|
| f3db | 1 / 10 / 60 kHz | 55.725 kHz | 54.240 / 55.840 / 58.860 | 55.467 / 55.883 / 56.298 |
| gm_db | -50 / -10 / -10 dB | -41.46 dB | -42.97 / -41.18 / -40.58 | -41.75 / -41.49 / -41.23 |
| lf_gain | 10 / 20 / 30 dB | 17.02 dB | 14.58 / 17.01 / 18.80 | 16.57 / 16.98 / 17.39 |
| pm_deg | 45 / 60 / 105 deg | 96.34 deg | 94.66 / 96.23 / 99.27 | 95.95 / 96.38 / 96.82 |
| ug | 0.1 / 0.3 / 1 MHz | 0.39 MHz | 0.29 / 0.41 / 0.49 | 0.37 / 0.39 / 0.41 |

`lstbcmfb.spi`: 29행 `VCM VCM 0 dc {AVDD/2} ac 0`, 30·31행 VSIP/VSIN = VCM, 41·42행 `vlp1 LOP VOP`, `vlp2 LON VON`(출력 -> 귀환 저항 직결), 46행 `X999 LPCO LPCI loopgainprobe`(= CMFB 루프 절단점).

## 6. 엔진 로드 확인 (2026-10-14, 사이징 탐색 미실행)

* `load_topology`: 통과 -- MOS 72, 수동소자 10, 이상원 1, bias_inputs []. connectivity_fp `2456805b2986b5decfcc0e27e9005deab1607d3bd380a78b940110e021755c96` = 판독본 `wt/_heldout/D_cnr/D_cnr.topology.json` 과 같음.
* `load_sizing_spec(metric_catalog())`: 통과 -- pending 12건(element_values x3·x37·x38·x39·x40·x9, input_dc = U-75; intended_region CI-18, node_voltage_targets_v CI-15, objective.budgets PA-1, search.front_budget_s PA-2, spice_check.front_points_rule AC-3).
* `build_s1(VDD_1V8 1.8, VSS 0)`: 통과.
* `run_stage_a`(S1v): status `stopped`, exit 2. 정지 9건 = x47.M1·x48.M1 루프(VCBN2) 각각 `cs_output_low_impedance`, `loop_record_only`(global_feedback_or_cross_coupled, VOP 쪽·VON 쪽 CMFB 루프) 2건, `undeclared_loop_constraint` + `A4_coupling` STRUCTURE_UNRESOLVED(IDC, x24.M1 column_unassigned). 검토 8건 = 버스 펼침 쌍 x3[0:1]·x6[0:1]·x14[0:1]·x17[0:1] 의 `dc_role_unresolved_group`, `l_owner_name_order`. held-out 판정 자료로 기록만 한다(실행 스크립트·결과 `wt/_scratch_heldout_d/build_assets.py`, `results.jsonl`).

## 7. 없는 것 (명시)

* slew rate, settling, 출력 스윙, 잡음, 입력 공통모드 범위 수치 -- 없음(`tran.meas` 는 MEAS_START/END 만). 그래서 `driving_spec` 을 두지 않았다.
* OTA 입력 핀 DC 수치 -- 없음(3.2절).
* 출력 공통모드 목표 전압 수치 -- 없음(VCREF 는 저항 분압 x40/x39/x3 + SF x31 로 회로 안에서 만든다).
* 개방 루프 이득을 따로 잰 값 -- 없음(3.1절 beta=1 해석으로 lstb 값을 쓴다).

## 8. 설계자 서술 (`CNR_OTA.md`; `documents/schematic.md` 에도 같은 글)

* DIFF OTA(11~18행): "Fully differential current mirror OTA. The current mirrors have been designed to operate in moderate to weak inversion." / "The input common mode cannot be VDD/2."
* VCM OTA(20~26행): "I feed the output of the common mode into the cascode nodes on the DIFF OTA ... The dominant pole of the VCM OTA is also the output of the DIFF OTA".
* VCM(28~44행): 출력 CM 을 의도적으로 높임; 레벨시프터(source follower)는 2F(L=0.54) 사용; 저항이 CM 감지, 커패시터는 저항·VCM OTA 입력용량 극점을 상쇄하는 feedforward zero, 커패시터는 VCM OTA 입력용량보다 충분히 커야 함.
