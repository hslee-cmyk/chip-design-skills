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
> | `element_values.x37`·`x38`·`x39`·`x40`·`x9` / `x3` | 70134.2 Ω 각각 / 17533.5 Ω | res_high_po PDK 셀 모델 식으로 계산, ngspice 대조 일치 (U5 (a), D-R 2026-10-14, 아래 4.2절) |
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

### 4.2 저항 x37, x38, x39, x40, x9, x3 -- 계산함 (D-R 2026-10-14)

* 결정: user_decisions.md 2026-10-14 D-R "D-R은 승인" -- 공개 저장소 `google/skywater-pdk-libs-sky130_fd_pr` 의 `cells/res_high_po` 셀 모델 파일을 받아 `C:/pdk/sky130_fd_pr/cells/res_high_po/` 에 두고 PDK 근거로 계산.
* 소자: `CNR_OTA.sch` 634행 x37, 635행 x38, 642행 x39, 643행 x40, 681행 x9 = `SUNTR_RPPO16`, 701행 x3 = `SUNTR_RPPO4`. 셀 구성(U6 (a) 2024-02 라이브러리, `wulffern/sun_tr_sky130nm` @`ccd959e` 2024-02-09): `SUNTR_RPPO16` -> `SUNTR_RES16` = `sky130_fd_pr__res_high_po W=0.72 L=8.8 mult=1` 16개 직렬, `SUNTR_RPPO4` -> `SUNTR_RES4` = 같은 세그먼트 4개 직렬 (sun_tr `294c65b` 2024-10-04 뒤 HEAD 는 L=8.96 um). 판독 기록 `wt/_heldout/D_cnr/D_cnr.flat_lib20240301.json` 에서 사슬 확인: 6개 셀 모두 세그먼트 수 16/4, 내부 노드 차수 2, (W, L, mult) = (0.72, 8.8, 1) 한 종류, 몸체 b = 셀 핀 B(= VSS, 2단자 모델이라 버림; 모델에서 b 는 기생 C 단자뿐이라 DC 값에 영향 없음). 확인 스크립트 `wt/_scratch_heldout_d_res/chk_chain.py` -> `chain.json`.

**받은 PDK 파일 (커밋 고정)**

* 커밋 선택: 로컬 `C:/pdk/sky130_fd_pr` 는 같은 저장소(`origin` = https://github.com/google/skywater-pdk-libs-sky130_fd_pr.git, blob:none 부분 복제 + sparse checkout)의 `f62031a1be9aefe902d6d54cddd6f59b57627436`(2020-11-10 "spice: Remove `.param TEMP=27`.") 이다(`git rev-parse HEAD`). 그래서 같은 커밋에서 받았고, 받은 파일마다 git blob sha1 이 로컬 커밋 tree 항목(`git ls-tree HEAD cells/res_high_po`)과 같음을 확인했다 -- 로컬 `models/` 파일과 짝이 맞는 판.
* 받은 파일 = `models/sky130_fd_pr__model__linear.model.spice`(sha256 715933557b35a83526337fcaf1e4cc7d147868926f58555420963c8655b5ea4e) 30·37~41행이 include 하는 res_high_po 파일 6개. 기존 PDK 파일은 고치지 않았다.

| 파일 (`C:/pdk/sky130_fd_pr/cells/res_high_po/`) | URL (커밋 고정) | sha256 | git blob (= tree 항목) |
|---|---|---|---|
| `sky130_fd_pr__res_high_po.model.spice` | https://raw.githubusercontent.com/google/skywater-pdk-libs-sky130_fd_pr/f62031a1be9aefe902d6d54cddd6f59b57627436/cells/res_high_po/sky130_fd_pr__res_high_po.model.spice | 5d5f46fc322ff3aa83222a588c712b758a3863b8aed3eea6ca637b120ddf411f | 600a0077 |
| `sky130_fd_pr__res_high_po_0p35.model.spice` | https://raw.githubusercontent.com/google/skywater-pdk-libs-sky130_fd_pr/f62031a1be9aefe902d6d54cddd6f59b57627436/cells/res_high_po/sky130_fd_pr__res_high_po_0p35.model.spice | b734c53d9317e2b9397c4322bfba943c15c8fad6450164dd8205b537344f0d2a | 7a245885 |
| `sky130_fd_pr__res_high_po_0p69.model.spice` | https://raw.githubusercontent.com/google/skywater-pdk-libs-sky130_fd_pr/f62031a1be9aefe902d6d54cddd6f59b57627436/cells/res_high_po/sky130_fd_pr__res_high_po_0p69.model.spice | cdc156f6d1f0009d7e7783fe692395a27568e29fbf3acc2f493233d0ee43a0d3 | 4da55bc9 |
| `sky130_fd_pr__res_high_po_1p41.model.spice` | https://raw.githubusercontent.com/google/skywater-pdk-libs-sky130_fd_pr/f62031a1be9aefe902d6d54cddd6f59b57627436/cells/res_high_po/sky130_fd_pr__res_high_po_1p41.model.spice | 10e284a92450c4e6f7cb0662d3580f156bf8f037aa99991a7f04ba24399aad1d | 41219cb1 |
| `sky130_fd_pr__res_high_po_2p85.model.spice` | https://raw.githubusercontent.com/google/skywater-pdk-libs-sky130_fd_pr/f62031a1be9aefe902d6d54cddd6f59b57627436/cells/res_high_po/sky130_fd_pr__res_high_po_2p85.model.spice | dc066401f00c16ae38ed9946163e9d1ba480dd6d88cb5edd45bffef55474cd4a | ba1a95fb |
| `sky130_fd_pr__res_high_po_5p73.model.spice` | https://raw.githubusercontent.com/google/skywater-pdk-libs-sky130_fd_pr/f62031a1be9aefe902d6d54cddd6f59b57627436/cells/res_high_po/sky130_fd_pr__res_high_po_5p73.model.spice | 7474ba669a8144316c2e4a79523a99643ea331bbc7e53b9efc3cb33a03fb254d | 97d0a86b |

* 쓰는 셀: 원본 넷리스트가 `sky130_fd_pr__res_high_po W=0.72 L=8.8`(xschem `res_high_po.sym` format 줄)을 부르므로 W·L 매개변수 일반 셀 `sky130_fd_pr__res_high_po`(위 표 1행)다. `_0p35`~`_5p73` 은 폭 고정 셀(W=0.69 등)이라 W=0.72 에는 쓰지 않는다(받은 것은 include 완전성 때문).

**모델 식 (`sky130_fd_pr__res_high_po.model.spice` 24~54행)**

* 26행 `rsheet = 317.3885`, 27행 `rbody_dw = -0.001`, 28행 `rhead_ps = 345.8312`(rhead_model rsh 43행과 같은 값)
* 36행 `weff = {w+rbody_dw-0.0672*max(0.69-w,0)}` -> W=0.72: 0.72 - 0.001 - 0 = **0.719 um**; 37행 `leff = {l+0.247}` -> **9.047 um**
* 39행 `rhead r0 rb rhead_model w = {weff+0.1558} l = 1.0`; 40행 `rbody rb r1 rbody_model w = {weff} l = {leff}` (둘 직렬; 41행 `xc0` 은 b 로 가는 기생 C 뿐)
* 43행 rhead rsh = `345.8312*(1+sky130_fd_pr__res_high_po__var)*(1+rend_match)`, 46행 `tc1 = -4.3e-4 tc2 = 12e-6 tnom = 30.0`
* 48행 rbody rsh = `rsheet*(1+sky130_fd_pr__res_high_po__var)*(1+res_match)`, 53행 `tc1 = {tc1rpolybody} tc2 = {tc2rpolybody} tnom = 30.0` -- `C:/pdk/sky130_fd_pr/models/sky130_fd_pr__model__r+c.model.spice`(sha256 54c67cfaa82cf4cd961b0780cb66392cd2f2031df6ae2773bd4f79d7587683f9) 62·63행 `tc1rpolybody= .514e-3`, `tc2rpolybody= .122e-5`
* 코너 tt: `models/r+c/res_typical__cap_typical__lin.spice`(sha256 dc4243210bb6bf59d31a1cdc935b6116cfcb1c6e4d6213d7bbc0c7ebaa5f0848) 4·5행 `sky130_fd_pr__res_high_po__var(_mult) = 0.0`; `sky130_fd_pr__model__linear.model.spice` 16·17행 `..._slope_spectre = 0.0`, `..._con_slope_spectre = 0.0` -> res_match = rend_match = 0 (mismatch 없음).
* 온도: 엔진 기준 온도 = LUT 측정 온도 `temp_c` = **27 °C** (`gmid_engine/metrics/junction_source.py` -- `JunctionSource.temp_c` 는 LUT `provenance.cap_conditions["temp_c"]`; `lut_v2_location.json` cap_npz `sky130_nfet_pfet_lut_v2_r2.npz` 의 `temp_c = 27.0`, `corner = tt` 실측). 모델 tnom = 30 °C(모델 카드 값) -> dT = -3 K, 보정 R(T) = R(tnom)·(1 + tc1·dT + tc2·dT²).
* 계산 (세그먼트 1개):
  * rbody = 317.3885 × 9.047 / 0.719 = 3993.621 Ω (30 °C) × (1 + 0.514e-3·(-3) + 0.122e-5·9 = 0.998469) = **3987.507 Ω**
  * rhead = 345.8312 × 1.0 / (0.719 + 0.1558) = 395.326 Ω (30 °C) × (1 + 4.3e-4·3 + 12e-6·9 = 1.001398) = **395.879 Ω**
  * 세그먼트 = **4383.386 Ω** (30 °C 값 4388.947 Ω)
* 결과(6유효자리, spec `element_values.<이름>.value_ohm`): `SUNTR_RPPO16`(x37·x38·x39·x40·x9) = 16 × 4383.386 = **70134.2 Ω**, `SUNTR_RPPO4`(x3) = 4 × 4383.386 = **17533.5 Ω**. 계산 스크립트(모델 파일에서 값을 읽어 계산) `wt/_scratch_heldout_d_res/apply.py`, 기록 `apply_log.jsonl`.
* 모델 해석 주의: `rhead_model`·`rbody_model` 의 `p2`·`q2`·`p3`·`q3`·`sw_et`·`isnoisy` 는 ngspice 저항 모델 파라미터가 아니다 -- ngspice-46 은 "unrecognized parameter ... - ignored" 로 버린다. 다른 시뮬레이터용 비선형(전압·형상 의존) 항으로 보이며 의미를 이 파일만으로 확정할 수 없다. 엔진 SPICE 기준(ngspice)과 같은 해석, 즉 R = rsh·l/w·(1+tc1·dT+tc2·dT²) 를 썼다. DC 1.8 V 까지 ngspice 값이 일정한 것(아래)도 이 해석의 결과다.

**ngspice 대조 (ngspice-46, `C:/ngspice/Spice64/bin/ngspice_con.exe -b`)**

* 넷리스트 `wt/_scratch_heldout_d_res/res_dc.cir`(sha256 5c73d6f325fc34e28a0f3690648320321a19a9fdd68637a5854769da942dc729): 위 셀 모델 + 기생 `models/parasitics/sky130_fd_pr__model__parasitic__res_po.model.spice` + `res_typical__cap_typical__lin.spice` 를 include, `slope_spectre`·`con_slope_spectre`·`tc1rpolybody`·`tc2rpolybody` 는 원본 줄 값 그대로 `.param`(`res_typical__cap_typical.spice` 는 로컬에 없는 res_generic 셀 파일을 include 해서 직접 못 쓰므로 기생 C 값 `crpf_precision`·`crpfsw_precision_1_1` 만 그 파일 40·41행 값으로 `.param` -- DC 무관), `.option temp=27`, 0.1 V 를 걸어 V/I.
* 결과(로그 `res_dc.log`): 세그먼트 1개 **4383.386 Ω**, 4개 직렬 **17533.54 Ω**, 16개 직렬 **70134.17 Ω** -- 손계산과 표시 자리수(7자리) 안에서 같다(차이 0). DC 0.1 / 0.95 / 1.8 V 에서 16개 직렬 값 같음(70134.17 Ω). 30 °C 판(`res_dc_t30.cir`): 4388.947 / 17555.79 / 70223.16 Ω = 손계산 30 °C 값과 같음 -- 모델 카드 tnom 30 이 쓰였다(로그의 "TNOM = 27" 은 시뮬레이터 기본값이고 모델 카드 tnom 이 우선).

**xschem 심볼 표시식과의 차이 (참고, 정본 아님)**

* `res_high_po.sym` 49행 `R=expr_eng( (378.3 + 317.17 * @L ) / @W / @mult )` -> 세그먼트 4401.94 Ω, RPPO16 70431.0 Ω, RPPO4 17607.8 Ω. 모델 계산(27 °C) 대비 **+0.42 %** (30 °C 모델 값 대비 +0.30 %). 표시식은 끝저항·폭 보정(weff, leff, rhead 의 w+0.1558)과 온도 보정을 단순화한 근사라 spec 에 쓰지 않는다.

* spec: `element_values.<x37|x38|x39|x40|x9> = {"value_ohm": 70134.2, source: user_spec, record = D-R, decided 2026-10-14, origin drawing, citation = 회로도 줄·sun_tr 셀·PDK 모델 URL·sha256}`, `x3 = 17533.5`. topology 값 칸은 C1/C2 와 같은 방식으로 null 유지(주석 `_value_note`·`_decisions.U5_values` 만 갱신) -- connectivity_fp 변경 전·후 `2456805b2986b5decfcc0e27e9005deab1607d3bd380a78b940110e021755c96` 같음(실측).

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
  * D-R 반영 뒤(2026-10-14) 재실행: pending **6건**(input_dc = U-75; intended_region CI-18, node_voltage_targets_v CI-15, objective.budgets PA-1, search.front_budget_s PA-2, spice_check.front_points_rule AC-3) -- 저항 6건 해소. spec_fp 8f053698... -> d2619d21...; connectivity_fp 그대로.
* `build_s1(VDD_1V8 1.8, VSS 0)`: 통과.
* `run_stage_a`(S1v): status `stopped`, exit 2. 정지 9건 = x47.M1·x48.M1 루프(VCBN2) 각각 `cs_output_low_impedance`, `loop_record_only`(global_feedback_or_cross_coupled, VOP 쪽·VON 쪽 CMFB 루프) 2건, `undeclared_loop_constraint` + `A4_coupling` STRUCTURE_UNRESOLVED(IDC, x24.M1 column_unassigned). 검토 8건 = 버스 펼침 쌍 x3[0:1]·x6[0:1]·x14[0:1]·x17[0:1] 의 `dc_role_unresolved_group`, `l_owner_name_order`. held-out 판정 자료로 기록만 한다(실행 스크립트·결과 `wt/_scratch_heldout_d/build_assets.py`, `results.jsonl`).
  * D-R 반영 뒤(2026-10-14) 재실행: status·exit·정지 9건·검토 8건 모두 그대로(문자열 같음). stage_a.json 차이는 `tables/key[0]/marks_fp` 하나(spec 지문 변경). 실행 `wt/_scratch_heldout_d_res/run_checks.py`, 결과 `results.jsonl`.

## 7. 없는 것 (명시)

* slew rate, settling, 출력 스윙, 잡음, 입력 공통모드 범위 수치 -- 없음(`tran.meas` 는 MEAS_START/END 만). 그래서 `driving_spec` 을 두지 않았다.
* OTA 입력 핀 DC 수치 -- 없음(3.2절).
* 출력 공통모드 목표 전압 수치 -- 없음(VCREF 는 저항 분압 x40/x39/x3 + SF x31 로 회로 안에서 만든다).
* 개방 루프 이득을 따로 잰 값 -- 없음(3.1절 beta=1 해석으로 lstb 값을 쓴다).

## 8. 설계자 서술 (`CNR_OTA.md`; `documents/schematic.md` 에도 같은 글)

* DIFF OTA(11~18행): "Fully differential current mirror OTA. The current mirrors have been designed to operate in moderate to weak inversion." / "The input common mode cannot be VDD/2."
* VCM OTA(20~26행): "I feed the output of the common mode into the cascode nodes on the DIFF OTA ... The dominant pole of the VCM OTA is also the output of the DIFF OTA".
* VCM(28~44행): 출력 CM 을 의도적으로 높임; 레벨시프터(source follower)는 2F(L=0.54) 사용; 저항이 CM 감지, 커패시터는 저항·VCM OTA 입력용량 극점을 상쇄하는 feedforward zero, 커패시터는 VCM OTA 입력용량보다 충분히 커야 함.
