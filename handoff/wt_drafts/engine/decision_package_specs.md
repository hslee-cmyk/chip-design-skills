# 사용자 결정 자료 -- 9회로 합격 시험 스펙 (2026-10-07)

목적: 범용 엔진 합격 시험(library 9회로 각각 엔진 사이징 -> ngspice에서 영역·스펙 만족)에 필요한 회로별 스펙 값을 사용자가 **한 번에** 정할 수 있게 현재 출처를 모으고, 비어 있거나 논문 값만 있는 칸을 표로 모은다.

원칙(이 문서가 지킨 것):
- 값을 정하지 않았다. 제안 칸에는 **근거 방식**만 적었다(값 없음).
- 논문·도면·강의 값은 **참고**로만 표시했다. 사용자가 그 값을 채택한다고 확정한 기록이 있으면 '확정(출처 논문)'으로 따로 표시했다.
- 읽기 전용: 메인 저장소 `chip-design-skills`(HEAD 6df4bd7)·clone `gmid-light`(HEAD cb0ef86) 둘 다 쓰기·git 조작 없음. `run_harness.py`는 두 곳 내용이 같다(줄바꿈 차이만).

출처 약어:
- **H** = `workspaces/run_harness.py` (`SPECS`/`canonical_spec`, 행 번호). SPECS에는 4회로만 있다(two_stage_ota, current_reuse_telescopic_ota, folded_cascode, nmcnr_amplifier). 나머지 5회로는 실행 spec이 없다.
- **T** = `skills/analog-gmid-design/assets/library/<회로>.topology.json` (행 번호). `T.decl` = `_declared_target_spec`, `T.paper` = `_paper_target_spec`, `T.cons` = `sizing_roles.constraints`.
- **P** = `docs/01-plan/features/gain-budget-gmid-sizing.plan.md` N7.2 (행 번호): U-13 1090, U-19 1096, U-25 1102, U-31 1108, U-34 1111, U-35 1112, U-36 1113. 함께 본 것: U-12 1089, U-17 1094, U-26 1103, U-29 1106.
- `sky130_supplies_v`: 현재 library에 이 키는 **0건**이다(MG0, 승인 `20260921-mg0-target-spec-split`이 `_declared_target_spec.supplies_v`로 옮김). P 1111(U-34) 본문은 아직 `_paper_target_spec.sky130_supplies_v`라고 적혀 있어 **계획서 문언이 파일과 어긋난다**(값은 같은 1.8 V).
- `_declared_target_spec`의 확정 근거: U-39 기본안 확정(2026-09-21, "기본안대로 확정") + MG0 회로별 분류표 사용자 선택. 5회로(ngcc, nmcnr, pushpull, sf_pushpull, two_stage_ota_sf)에 있다.

상태 기호: **확정** = 사용자 확정 기록 있음 / **확정·7a** = 처리 방식은 확정됐고 값은 7a SPICE 대조에서 다시 읽음 / **확인** = 실행 값은 있으나 사용자 확정 기록을 찾지 못함 / **논문** = 논문·도면 값만 있음 / **빈칸** = 값 없음 / **N/A** = 회로 성격상 해당 없음 / **선택** = 규칙상 미선언이면 보고만(U-29 출력 스윙) / **상속** = 다른 회로 정본을 참조.

---

## 1. 회로별 현재 스펙 출처 전부

### 1.1 two_stage_ota (Maloberti worked example, 2단 Miller OTA)
- H 72-130 `_spec_two_stage_ota`: `vdd` 1.8 (H 105), `GBW` 7e6·`CL` 3e-12·`Z` 10·`NDP` 4 (H 113), `stage_gain_min` 30 dB x2, `stage_objective` power.
  - GBW 7 MHz: 2026-08-13 세션31 사용자 결정(GBW 스윕 무릎점에서 타협). docstring H 73-92.
  - Z=10/NDP=4: "typical" 값(문헌 일반값), 확정 기록 아님 -- 스펙이라기보다 보상 설계 인자.
- T.cons (T 309): `gain_db >= 57` source `user_spec`; `mismatch_sigma_mV <= 5.0` source `pending_7a`(U-17, 판정에 안 씀).
- T `_target_spec_comment` (T 276): 원래 gain>=60·GBW 20 MHz(문헌 typical) -> 실측 불가 -> GBW 7 MHz·gain>=57로 하향(사용자 결정). **PM은 검증 함수가 없어 제약으로 넣지 않고 설계 의도(PM≈70°, Z/NDP)로만 남김.**
- objective: minimize power_uA. 면적 예산 없음. `supplies_v` 선언 없음(U-26 (a) 미결 -- 스칼라 vdd 1.8만).
- 계획: U-31(P 1108) CL 3 pF@OUT 닫힘(실행 spec `CL: 3e-12`), U-19 해당 없음(파일럿 전용).

### 1.2 current_reuse_telescopic_ota (파일럿, Xie & Chen 126 uW)
- H 132-209 `_spec_current_reuse_telescopic_ota`: `vdd` 1.8 (H 142), `t_lln` 30e-9 (H 190), `PM_target_deg` 70 (H 191), `Cc`/`Cf`/`Cs` 500e-15 (H 192-194), `C_Ltot` 1e-12 (H 195), `t_settle_total` 40e-9 (H 204), `omega_c` 6.9/30e-9(폴백).
  - `t_lln`·`t_settle_total`: 논문 III.A "t_slew=10 ns / t_lln=30 ns" 값(H 196-203 주석). **논문 값**.
  - `C_Ltot` 1 pF, `Cf`/`Cs` 500 fF: 논문 Table I `C1, C2, C_L = 500fF, 500fF, 1pF`(history 2744행). **논문 값**. Cc는 보상망이 유도(history 2773행, 500 fF는 폴백).
  - `PM_target_deg` 70: 출처 기록을 찾지 못함(nmcnr 쪽 H 270-275가 "current_reuse와 동일 값"이라고만 적음). **확인 필요**.
- T.cons (T 2035~): `gain_db >= 54` user_spec(세션44, SLSQP 실측 57.03 dB - 3 dB 마진, 사용자 승인. T 2031 `_gain_db_target_comment`), `mismatch_sigma_mV <= 5.0` pending_7a, `cmrr_estimate_db >= 60` user_spec, `psrr_estimate_db >= 60` user_spec, `mirror_ratio_error_mV <= (mismatch_sigma_mV 참조)` reference, `classab_centering_dev_v <= 0.15` user_spec(근사치라는 주석 있음), `parasitic_pm_deg >= PM_target_deg` reference.
- T 144 `ideal_sources.Iref.value_amp` 1.2e-6: 2026-09-08 사용자 확정(논문 값을 사용자가 원문 확인). ⚠️ 엔진은 아직 이 값을 소비하지 않음(B14) -- SPICE 하네스 보고 4단계 4번.
- 계획: U-19(P 1096) gain 기준을 7a SPICE 대조값으로 재도출 예정. U-13(P 1090) 면적 예산 선언 여부 = **7b 착수 조건, 미결**. U-35(P 1112) source 기입 완료.

### 1.3 folded_cascode (Maloberti p.34-38)
- H 212-246 `_spec_folded_cascode`: `vdd` 1.8 (H 234)뿐. GBW·CL·PM 없음.
- T.cons (T 441) = `[]`. `_constraints_status`(T 442): U-35 확정(gain/pm/cmrr/psrr 4건은 자기 실행 역산값이라 삭제), **7a 재도출 전까지 사이징 판정 보류**.
- T metrics `pm_deg.CL` 1e-12 (T 417): metric 안의 부하 가정. U-31(P 1108): **folded CL 1 pF 스펙 확정**, 실행 spec 반영은 7b.
- T 107 `ideal_sources.Ibg.value_amp` null: theta(const) 자유 탐색 -- 설계상 의도(값 선언 아님).
- objective: minimize power_uA.

### 1.4 nmcnr_amplifier (Leung·Mok·Ki 1999, 3단 NMCNR)
- H 249-301 `_spec_nmcnr_amplifier`: `vdd` 1.8(±0.9 V 원점 이동 동등, H 284-288), `GBW` 816000·`CL` 1e-10·`kg` 0.5 (H 289), `PM_target_deg` 70 (H 290).
- T.decl (T 30-51): `supplies_v` vdd 0.9 / vss -0.9 (2026-09-15 사용자 결정 "+-0.9로 고치고"), `CL_farad` 1e-10, `gbw_hz >= 816000`, `pm_deg >= 70`(세션37 확정, 논문 46°는 구조 전제 PM>60과 충돌해 기각). `kg`·논문 DC gain > 100 dB는 **declared에 넣지 않음**("7b에서 정한다").
- T.paper (T 52-~92): 부하 조건 **100 pF ∥ 25 kΩ**(T 54), DC gain > 100 dB, GBW 816 kHz, PM 46°, SR+ 0.36 / SR- 0.31 V/us, Ts 3.03/3.04 us, PSRR+ 92.61 dB@1k·75.62@10k, PSRR- 106.44@1k·84.62@10k, 전력 400 uW, 면적 0.18 mm²(공정 종속), 전원 ±1 V. 모두 AMS 0.8 um 값.
- T.cons (T 555) = `[]` (U-35 삭제, 판정 보류). T metrics `gain_db`/`pm_deg`에 `CL` 1e-10·`kg` 0.5 (T 514, 535).
- 계획: U-26 (a) nmcnr `supplies_v` 확정, U-31 실행 spec `CL: 1e-10`.

### 1.5 ngcc_3stage_ff (Lee et al. JSTS 2007, 3단 NGCC)
- H: **SPECS 항목 없음**.
- T.decl (T 182-209): `supplies_v` vdd 1.8 / gnd 0 (2026-09-16 사용자 결정 "2는 1.8에 맞춰"), `CL_farad` 1e-11, `gbw_hz >= 10 MHz`, `pm_deg >= 63.4`, `icmr_v >= 0.6`(VDD/3을 1.8 V로 재계산). 주석: "GB 10 MHz·PM·CL 10 pF는 topology 수준 목표라 그대로 쓴다"(사용자 결정).
- T.paper (T 211~): VDD 1.2 V, 0.18 um, Table 4 설계 예시(k=4, alpha=0.3, gm·ID·W/L·Cm1 1.68 pF·Cm2 1.32 pF) -- 참고값.
- gain: **선언 없음**. sizing_roles = null, compensation = null(`pending_topology_fn`).
- 계획: U-34(P 1111) 회로 추가 확정, "사이징 스펙은 미선언이라 구조 유도(6a)에만" -- 단 그 뒤 U-39/MG0에서 위 declared가 생김.

### 1.6 pushpull_follower_buffer (Allen L26 p.26-4, 버퍼 단독)
- H: SPECS 없음.
- T.decl (T 85-111): `supplies_v` vdd 1.8 / vss 0 / **agnd 0.9**, `CL_farad` 1e-12(vout–agnd), `rout_ohm <= 1000`, objective minimize power, `report_only: buffer_bandwidth_hz`(사용자 결정: GB 60 MHz를 버퍼 제약으로 옮기는 배수 근거 없음), `input_dc_net: agnd`.
- T.paper (T 112~): CL 1 pF, Rout ≤ 1 kΩ(도면).
- 계획: U-25(P 1102) 확정.

### 1.7 sf_pushpull_output_opamp (Allen L26 p.26-6 Fig. 7.1-1)
- H: SPECS 없음.
- T.decl (T 254-292): `supplies_v` vdd 1.8 / vss 0 / **agnd 0.9**, `input_dc_net: agnd`, `IBias_amp` 50e-6, `CL_farad` 1e-12, `dc_gain_db >= 65`, `gbw_hz >= 60 MHz`, `rout_ohm <= 1000`, R1·Cc는 유도(`derived_not_declared`).
- T.paper (T 293~): 도면 값 동일(IBias 50 uA, CL 1 pF, Av 65 dB, GB 60 MHz, Rout ≤ 1 kΩ).
- **PM 선언 없음**. compensation = null(`pending_topology_fn`, Cc가 Y–agnd 보상이라 기존 함수 없음).
- 계획: U-25(P 1102) 확정.

### 1.8 two_stage_ota_sf (Allen L26 p.26-5, 2단 + 팔로워)
- H: SPECS 없음.
- T.decl (T 120-140): `inherits` = H `_spec_two_stage_ota` + two_stage_ota T.cons·objective(값 복사 없이 참조). 추가 2건: `CL_farad` 3e-12 @vout, `rout_ohm <= 1000`(Allen L26 버퍼 기준). gain 감지 노드 = vout(팔로워 감쇠 포함).
- T.paper (T 141~): Rout ≤ 1000 Ω(강의 p.26-6/p.26-27).
- 상속 결과: 전원 1.8(스칼라), GBW 7 MHz, gain ≥ 57, mismatch 5.0 pending_7a. **입력 DC·PM·면적은 정본(two_stage_ota)에도 없으므로 상속해도 빈칸**.
- 계획: U-25(P 1102) 확정, 실행 SPECS 이관은 "사이징 착수 시".

### 1.9 common_gate_amplifier (Allen L20 p.20-2, 전압 구동 CG 3소자)
- H: SPECS 없음. T: `sizing_roles` = null, `_declared_target_spec`·`_paper_target_spec` **없음**.
- T `_compensation_status_comment`: 단일단, gm 출처는 U-12(7b), "부하 요소(CL)는 이 그림에 없다 -- 사이징 스펙을 선언할 때 함께 정한다".
- T `_reference_relations`(문서화 전용): Av = gm2·(rds2∥rds3), Rin ≈ 2/gm2(이 부하), Rout = rds2∥rds3, 스윙 vout_max = VDD − VDS3(sat), vout_min = VDS1(sat) + VDS2(sat).
- 계획: U-37(P 1114) "사이징 스펙 미선언, 검증 발동용". **스펙 전부 비어 있음**.

---

## 2. 회로 x 합격 시험 스펙 항목 (현재 값·출처·상태)

열: ①전원 `supplies_v`(3레일은 agnd) ②입력 DC ③부하 CL(U-31) ④gain ⑤GBW/UGF ⑥PM ⑦슬루/정착 ⑧출력 스윙 ⑨전력/면적 예산(U-13) ⑩회로별 기타.

| 회로 | ①전원 | ②입력 DC | ③CL | ④gain | ⑤GBW | ⑥PM | ⑦슬루 | ⑧스윙 | ⑨전력/면적 | ⑩기타 |
|---|---|---|---|---|---|---|---|---|---|---|
| two_stage_ota | **확인** H105 vdd 1.8 스칼라, supplies_v 미선언(U-26a) | **빈칸** | 확정 3 pF@OUT (H113, U-31) | 확정 ≥57 user_spec (T309) | 확정 7 MHz (H113, 세션31) | **빈칸** (T276: 의도 ≈70°, 제약 없음) | 선택 | 선택 | 전력=목적 최소 / 면적 **빈칸**(U-13) | mismatch 5.0 확정·7a(U-17); Z/NDP 10/4 typical |
| current_reuse_telescopic_ota | **확인** H142 vdd 1.8 스칼라 | **빈칸**(입력 공통모드) | **논문** C_Ltot 1 pF, Cf/Cs 500 fF (H192-195, Table I) | 확정·7a ≥54 user_spec (T2035, U-19 재도출 예정) | **논문** GBW 없음, t_lln 30 ns·t_settle 40 ns에서 omega_c 유도 (H190/204) | **확인** 70 (H191, 기록 미발견) | (⑤와 같은 근거 -- t_slew = f_slew·t_settle) | 선택 (classab_centering ≤0.15 확정) | 전력=목적 / 면적 **빈칸**(U-13, 7b 착수 조건) | CMRR ≥60·PSRR ≥60·classab 0.15 확정(user_spec); mismatch 확정·7a; Iref 1.2 uA 확정(엔진 미소비) |
| folded_cascode | **확인** H234 vdd 1.8 스칼라 | **빈칸** | 확정 1 pF (U-31, 실행 반영 7b; T417) | **빈칸** (U-35 삭제, 판정 보류) | **빈칸** | **빈칸** (U-35 삭제) | 선택 | 선택 | 전력=목적 / 면적 **빈칸** | CMRR/PSRR metric 있음·제약 **빈칸**(U-35 삭제); Ibg = theta 자유(의도) |
| nmcnr_amplifier | 확정 ±0.9 V (T32, U-26a) | **빈칸** | 확정 100 pF (T38) / 저항 부하 25 kΩ **논문**(T54) | **논문** >100 dB (T63, declared 미포함 "7b에서 정한다") | 확정 816 kHz (T41, 논문 값 채택) | 확정 70 (T45, 세션37) | **논문** SR 0.36/0.31 V/us, Ts 3.03 us (T70) | 선택 | **논문** 400 uW (T79) / 면적 0.18 mm² 참고만 | PSRR **논문** 92.61/106.44 dB@1k (T75); CMRR 없음; kg 0.5 임의(설계 자유도) |
| ngcc_3stage_ff | 확정 1.8/0 (T184) | **빈칸** (ICMR ≥0.6 V는 범위) | 확정 10 pF (T190, 논문 값 채택) | **빈칸** | 확정 10 MHz (T194) | 확정 63.4 (T199) | 선택 | 선택 | 면적 **빈칸** | ICMR ≥0.6 V 확정 (T204) |
| pushpull_follower_buffer | 확정 1.8/0/agnd 0.9 (T87) | 확정 agnd (T109) | 확정 1 pF vout–agnd (T94) | N/A (이득 <1) | 확정 보고만 (report_only) | N/A (버퍼 단독, 루프 없음) | 선택 | 선택 | 전력=목적 확정 / 면적 **빈칸** | Rout ≤1 kΩ 확정 (T98) |
| sf_pushpull_output_opamp | 확정 1.8/0/agnd 0.9 (T256) | 확정 agnd (T262) | 확정 1 pF (T268) | 확정 ≥65 dB (T272, 도면 값 채택) | 확정 60 MHz (T277) | **빈칸** | 선택 | 선택 | 면적 **빈칸** | Rout ≤1 kΩ·IBias 50 uA 확정; R1·Cc 유도 |
| two_stage_ota_sf | 상속 (two_stage_ota ①) | 상속 -- 정본도 빈칸 | 확정 3 pF@vout (T128) | 상속 ≥57 (감지 vout) | 상속 7 MHz | 상속 -- 정본도 빈칸 | 선택 | 선택 | 면적 **빈칸** | Rout ≤1 kΩ 확정 (T133) |
| common_gate_amplifier | **빈칸** | **빈칸** (vin DC가 M2 source 바이어스를 정함) | **빈칸** | **빈칸** | **빈칸** (U-12: 단일단 gm 출처에 gbw 목표 필요) | N/A (단일단, 보상 없음) | 선택 | 선택 (식은 T `_reference_relations`) | 면적 **빈칸** | Rin(≈2/gm2) 선택 |

메모:
- '상속' 칸은 two_stage_ota에서 정하면 자동으로 따라간다(복사하지 않는다 -- `require_declared_spec_source`). 그래서 아래 집계에서 따로 세지 않았다.
- 출력 스윙은 U-29(P 1106) 확정 규칙("선언된 경우만 제약, 아니면 보고만")이 있어 결정 필요로 세지 않았다. 슬루는 같은 규칙이 명문화돼 있지 않으나 엔진 `slew_rate()` 미배선이라 같은 취급으로 두었다 -- 단 **논문 값이 실제로 쓰이는 곳(current_reuse t_settle)과 논문 값만 있는 곳(nmcnr SR)은 셌다**.
- '확인' = 실행 spec에서 쓰이는데 사용자 확정 기록을 찾지 못한 값. 값을 바꾸자는 뜻이 아니라 확정 표시가 필요하다는 뜻이다.

---

## 3. 사용자 결정 필요 요약표 (회로 x 항목) -- 36칸

| # | 회로 | 항목 | 현재 | Claude 기본안의 **근거 방식**(값은 정하지 않음) |
|---|---|---|---|---|
| 1 | two_stage_ota | ①전원 | 확인(스칼라 1.8) | 같은 공정 정격(sky130 1.8 V core)·LUT VDS/VGS 특성화 범위(0~1.8 V)와, 이미 확정된 다른 library 회로(ngcc 1.8/0, nmcnr 폭 1.8)와 일관되게 `supplies_v{vdd, gnd}`로 표기만 확정 |
| 2 | two_stage_ota | ②입력 DC | 빈칸 | connectivity 헤드룸에서 입력 공통모드 범위(ICMR)를 유도(입력쌍 극성, tail 최소 VDS, 미러 부하 VGS)해 그 범위 중앙. 3레일 회로의 agnd(=전원 중간) 선례와 비교 표시 |
| 3 | two_stage_ota | ⑥PM | 빈칸 | 프로젝트 확정 선례(nmcnr·current_reuse 70°, ngcc 63.4°)와 일관 + 구조 하한(2단 Miller 60°)에 여유. T276의 설계 의도(Z/NDP가 인코딩한 PM)와 대조 |
| 4 | two_stage_ota | ⑨면적 | 빈칸 | U-13 기본안: 예산 미선언 시 (전력, 면적) 비지배 front를 내고 정지(DEC-77) -- 사용자가 '예산 선언' 또는 'front에서 점 선택' 중 고름. 예산을 선언한다면 front의 무릎점 근거 |
| 5 | current_reuse | ①전원 | 확인(스칼라 1.8) | #1과 같음 |
| 6 | current_reuse | ②입력 DC | 빈칸 | #2와 같은 ICMR 유도. current-reuse라 PMOS·NMOS 입력쌍 둘 다의 헤드룸 교집합에서 유도 |
| 7 | current_reuse | ③CL(C_Ltot, Cf/Cs) | 논문(Table I) | 부하·되먹임 용량은 공정 무관 topology 수준 값이라 논문 값을 **참고로 제시**하고 채택 여부만 사용자에게 묻기(ngcc·nmcnr에서 사용자가 논문 CL을 채택한 선례). 또는 같은 class 회로 확정 CL(1 pF/3 pF)과 일관 |
| 8 | current_reuse | ⑤GBW/정착(t_lln, t_settle_total) | 논문(III.A) | 정착 시간 배분식(t_s = t_slew + t_lln)이 엔진에 배선돼 있으므로 정착 목표를 시스템 요구로 받거나, 논문 값을 sky130 전원·부하로 스케일(SR ∝ I/C, 전원 폭 비)한 값을 참고로 제시 |
| 9 | current_reuse | ⑥PM | 확인(70, 기록 미발견) | nmcnr에서 사용자가 확정한 같은 값(구조 하한 60° + 10°)과 일관 -- 확정 표시만 받기 |
| 10 | current_reuse | ⑨면적 | 빈칸 | #4와 같음(U-13은 이 회로가 명시 대상, 7b 착수 조건) |
| 11 | folded_cascode | ①전원 | 확인(스칼라 1.8) | #1과 같음 |
| 12 | folded_cascode | ②입력 DC | 빈칸 | #2와 같은 ICMR 유도(SPICE 하네스 보고: 엔진 예측 vin −0.85 V로 레일 밖 -- 선언 필요성 근거) |
| 13 | folded_cascode | ④gain | 빈칸(U-35 삭제) | U-35대로 7a SPICE 대조에서 읽은 달성값에서 마진을 둔 값(current_reuse 54 dB 선례: 실측 달성점 − 안전 마진), 또는 같은 단수(단일단 캐스코드)의 문헌 typical을 참고 |
| 14 | folded_cascode | ⑤GBW | 빈칸 | U-12 단일단 규칙(gm1 ≥ 2π·GBW·C_out,total)과 확정 CL 1 pF에서, 같은 전력 수준의 GBW 스윕 무릎점(two_stage_ota 7 MHz 선례 방식) |
| 15 | folded_cascode | ⑥PM | 빈칸(U-35 삭제) | #3과 같은 선례 일관 |
| 16 | folded_cascode | ⑨면적 | 빈칸 | #4와 같음 |
| 17 | folded_cascode | ⑩CMRR/PSRR | 빈칸(U-35 삭제) | 선언할지 자체가 결정. 선언하면 current_reuse 확정값(60/60 dB)과 일관, 또는 7a 실측 − 마진 |
| 18 | nmcnr_amplifier | ②입력 DC | 빈칸 | 분할 레일 ±0.9 V라 중간(0 V) 기준 후보와 ICMR 유도를 함께 제시 |
| 19 | nmcnr_amplifier | ③저항 부하 25 kΩ | 논문(T54) | 논문 측정 조건 그대로 참고(GBW·PM·SR이 이 부하 기준) vs 다른 library 회로처럼 순수 용량 부하 -- 포함 여부만 결정 |
| 20 | nmcnr_amplifier | ④gain | 논문(>100 dB) | 논문 값은 참고. 엔진·7a 실측 달성 상한에서 마진(current_reuse 선례), 3단 구조의 이득 상한과 대조 |
| 21 | nmcnr_amplifier | ⑦슬루/정착 | 논문(SR 0.36/0.31 V/us) | 논문 SR을 sky130 전원 폭(2.0 -> 1.8 V)·CL 동일(100 pF)·전류 수준으로 스케일한 값을 참고로, 또는 U-29 유추로 '보고만' |
| 22 | nmcnr_amplifier | ⑨전력/면적 | 논문(400 uW, 0.18 mm²) | 전력은 목적 최소화라 예산 없이 둘 수 있음(논문 400 uW는 전원 비로 스케일한 참고). 면적은 공정 종속이라 논문 값 미채택이 이미 기록됨 -> #4 방식 |
| 23 | nmcnr_amplifier | ⑩PSRR | 논문(92.61/106.44 dB@1k) | 논문 값은 공정 다름 -> current_reuse 확정 PSRR(60 dB)과 일관, 또는 7a 실측 − 마진. 주파수점(1 kHz) 정의 포함 |
| 24 | ngcc_3stage_ff | ②입력 DC | 빈칸 | 확정 ICMR(≥ 0.6 V) 범위의 중앙을 ICMR 유도로 제시 |
| 25 | ngcc_3stage_ff | ④gain | 빈칸 | 3단 구조 이득 상한(엔진 실측) − 마진, nmcnr(3단) 결정과 일관 |
| 26 | ngcc_3stage_ff | ⑨면적 | 빈칸 | #4와 같음 |
| 27 | pushpull_follower_buffer | ⑨면적 | 빈칸 | #4와 같음 |
| 28 | sf_pushpull_output_opamp | ⑥PM | 빈칸 | #3과 같은 선례 일관(이 회로는 Cc–agnd 보상, GB5 규칙 뒤 측정 가능) |
| 29 | sf_pushpull_output_opamp | ⑨면적 | 빈칸 | #4와 같음 |
| 30 | two_stage_ota_sf | ⑨면적 | 빈칸 | #4와 같음(상속 대상 아님) |
| 31 | common_gate_amplifier | ①전원 | 빈칸 | #1과 같음(2레일 vdd/gnd) |
| 32 | common_gate_amplifier | ②입력 DC | 빈칸 | 전압 구동 CG라 vin DC = M2 source = M1 drain: M1 VDS(sat) 하한과 M2·M3 헤드룸(T `_reference_relations` 스윙 식)에서 유도 |
| 33 | common_gate_amplifier | ③CL | 빈칸 | 같은 class(단일단) 회로의 확정 CL(folded 1 pF)과 일관 |
| 34 | common_gate_amplifier | ④gain | 빈칸 | Av = gm2·(rds2∥rds3) 상한(LUT gm/gds 실측) − 마진 |
| 35 | common_gate_amplifier | ⑤GBW | 빈칸 | U-12 단일단 규칙 + #33 CL, 같은 전력 수준 스윕 무릎점 |
| 36 | common_gate_amplifier | ⑨면적 | 빈칸 | #4와 같음 |

회로별 개수: two_stage_ota 4 · current_reuse 6 · folded_cascode 7 · nmcnr 6 · ngcc 3 · pushpull 1 · sf_pushpull 2 · two_stage_ota_sf 1 · common_gate 6 = **36칸**.
항목별 개수: 면적 9(전 회로 -- U-13 방식 한 번 정하면 일괄), 입력 DC 6, PM 4, 전원 4, gain 4, GBW/정착 3, CL·부하 3, CMRR/PSRR 2, 슬루 1.

한 번에 정하기 쉬운 묶음(같은 근거 방식이면 한 결정으로 여러 칸):
- A. 면적 예산 방식(U-13) 1결정 -> 9칸.
- B. 기존 3회로 `supplies_v` 표기 확정(U-26 (a)) 1결정 -> 3칸(+ common_gate 1칸).
- C. 입력 DC를 ICMR 중앙으로 유도할지 1결정 -> 6칸(common_gate는 식이 달라 따로 확인).
- D. PM 하한 선례(70°/63.4°) 적용 1결정 -> 4칸(current_reuse는 확정 표시만).

## 3.1 (스펙 표 밖) 합격 판정 정의 결정 -- 참고

스펙 값이 다 정해져도 SPICE 합격 판정에 아래가 필요하다(출처: `spice_harness_report.md` 4단계 8번, `schedule_general_engine.md` 153-154행). 위 36칸에 넣지 않았다.
1. 예측-SPICE 허용오차 출처(ID·VGS·gm·gds·노드·gain·PM·UGF·공급전류), 포화 여유(`--sat-margin`).
2. 비교 기준 W: 엔진 sizing W vs instance(layout) W(current_reuse 29/51 소자 5% 넘게 다름).
3. current_reuse 바이어스 전류 정본: topology Iref 1.2 uA(사용자 확정) vs 엔진 사용값 -- 엔진이 확정값을 소비하게 고칠 대상인지 확인.
4. gain 비교 대상 metric(단합 `gain_db` vs 전체회로 MNA `gain_full_circuit_db`), PM 정의(개루프 A vs β 루프).
5. SPICE로 검증할 front 점(예산점 1점 vs front 전 점).
6. U-36(P 1113) 수동소자 단위 면적 PDK 출처 -- 미선언이면 보상·부하 수동소자 있는 회로 front가 `review_needed`.
7. U-26 (c) `wall_clock_budget_s`(파일럿 300 s를 전 회로 공통 적용할지).

---

## 4. 회로 해석 공동분석(J) 묶음 -- 9회로 해당분과 한 세션 순서

출처: P 1041-1070 (N7.1). **확정은 J1뿐**(2026-09-17). 나머지는 승인 기록 없음(`.ai/approvals`에 J 기록 0건).

### 4.1 J 항목 x 회로

| J | 내용(요약) | 걸린 회로 | 소비 Phase | 상태 |
|---|---|---|---|---|
| J1 | 바이어스 종속 넷 교류접지 예외 | 파일럿 2건, 나머지 7회로 무동작 | 6a | **확정** |
| J2 | diode gate->drain 같은 stage(미러) 여부 | nmcnr(M201->M203/M204) | 6a | 미결 |
| J5 | 5T 미러부하·NMCNR 폴딩 미러 기모드 축약 | two_stage_ota, nmcnr (two_stage_ota_sf·ngcc도 5T 미러 부하) | 6a | 미결 |
| J13 | 가지·기둥 유도와 기둥↔블록 매핑 | 9회로 전부(3레일 pushpull·sf_pushpull 포함) | 6a, 7b | 미결 |
| J11 | 루프 뷰(루프 목록·끊는 점) | 9회로 전부, 파일럿 CMFB·M58·M7 | 6a | 미결 |
| J3-ac | class-AB pass 묶음·stage1 출력노드·병렬 CS | current_reuse(M9a/M9b/M18a/M18b/M8/M17) | 6a (J3-dc는 7b) | 미결 |
| J4 | M7(gate Vcmfb) tail vs CMFB 구동 | current_reuse | 6a | 미결 |
| J10 | follower/pass 경로 독립 블록 vs 흡수 | two_stage_ota_sf(M8), pushpull, sf_pushpull, folded(M8) | 6a | 미결 |
| J12 | 신규 회로 대조표·symmetry | sf_pushpull, two_stage_ota_sf, pushpull, ngcc | 6a, 7b | 미결 |
| J12-a | 버퍼 블록 경계 3건 | pushpull, sf_pushpull, two_stage_ota_sf | 6a | 미결 |
| J12-b | A·B·N17·N20 구동 종류, 버퍼 load 귀속 | pushpull, sf_pushpull | 6a | 미결 |
| J12-c | G_vgs 사이클(push-pull KVL 루프) | pushpull, sf_pushpull, current_reuse | 6a | 미결 |
| J12-d | M17/M20 K8 측면 주입 vs 복합 블록 | sf_pushpull (결과에 따라 ngcc와 함께 DEC-81 발동) | 6a | 미결 |
| J12-e | 출력 방향 분류(class-A/push-pull) | two_stage_ota_sf, two_stage_ota, pushpull, sf_pushpull, current_reuse | 6a | 미결 |
| J12-f | 루프 종속 gm_id 소자·합류 KCL | pushpull/sf_pushpull(M1/M2, M21/M22) | 6a | 미결 |
| J12-g | Cc O1–OUT, follower가 Miller 루프 밖인지 | two_stage_ota_sf | 6a | 미결 |
| J12-h | M5/M6 복합 diode 루프 분류 | sf_pushpull(M7/M8·M13/M14 포함) | 6a | 미결 |
| J12-i | CG 대조표(전압 구동 CG stage 시작) | common_gate_amplifier | 6a | 미결 |
| J6 | 출력노드 부하 귀속 | current_reuse(M18a/M19/M18b), nmcnr(M104/M106) | 6a, 7a | 미결 |
| J7 | Cc–Rz 직렬 루프 극성 | current_reuse(Cc1–Rz), nmcnr(Cm1/Cm2–Rm) | 6a, 7b | 미결 |
| J8 | fold_group·shared_gm_id_groups·budget_reference_device 의도 | current_reuse(M61/M68/M38), two_stage_ota(M4), folded·nmcnr(fold_group) | 6b | 미결 |
| J9 | ports(완료, U-08 9/9) / passive 누락 | nmcnr·two_stage_ota passive(Cc·CL 등 미선언), folded CL | 7b(passive) | ports 완료, passive 미결 |

### 4.2 한 세션 진행 순서(계획 판정 순서 그대로: J1 -> J2·J5·J13 -> J11 -> J3-ac·J4·J10 -> J12-a~h -> J6·J7, 그 뒤 6b J8, 7b J9 passive)

0. (사전) 3절 스펙 결정 A~D 묶음 -- J와 독립이라 먼저 끝내도 된다. 회로 connectivity 표를 함께 띄운다.
1. J1 -- 확정됨, 회로별 대조표만 확인(파일럿 2건/나머지 무동작).
2. J2 (nmcnr) · J5 (two_stage_ota, nmcnr, 5T 미러 공통 회로) · J13 (9회로 가지·기둥, 3레일 2회로 레일 쌍 포함) -- 서로 독립, 같은 단계.
3. J11 -- 9회로 루프 뷰. 파일럿 CMFB·M58은 J1 결과를 입력으로.
4. J3-ac · J4 (current_reuse) · J10 (follower 4회로).
5. J12-a -> J12-b -> J12-c -> J12-d -> J12-e -> J12-f -> J12-g -> J12-h (신규 4회로; J12 본문 ngcc gmf1 가지·Vout 합류·Cm DC 고립·미러 후보 포함), J12-i (common_gate, 다른 J12와 독립).
6. J6 · J7 (current_reuse, nmcnr).
7. (6b) J8, (7b) J3-dc·J9 passive -- 같은 세션에서 다루면 미리 보기만, ratify는 해당 Phase.

회로 기준으로 보면: common_gate(J12-i, J13, J11) 가장 가볍고, current_reuse(J1·J3·J4·J6·J7·J8·J11·J12-c·J12-e·J13)가 가장 무겁다.

### 4.3 connectivity 표(topology_to_markdown.py 생성, 2026-10-07)

생성: `skills/analog-gmid-design/assets/topology_to_markdown.py <json> <out>`를 임시 경로에서 실행(저장소 쓰기 없음, `PYTHONDONTWRITEBYTECODE=1`), 9회로 전부 rc=0. 임시 경로 삭제 전에 아래로 복사했다. library에 이미 있는 `.topology.md` 6건과는 소스 경로 줄 1줄만 다르다(connectivity 같음).

- `C:/Users/HSLEE/Documents/Todoc/fpga/wt/_drafts/engine/decision_package_connectivity/common_gate_amplifier.connectivity.md` (32행)
- `C:/Users/HSLEE/Documents/Todoc/fpga/wt/_drafts/engine/decision_package_connectivity/current_reuse_telescopic_ota.connectivity.md` (136행)
- `C:/Users/HSLEE/Documents/Todoc/fpga/wt/_drafts/engine/decision_package_connectivity/folded_cascode.connectivity.md` (55행)
- `C:/Users/HSLEE/Documents/Todoc/fpga/wt/_drafts/engine/decision_package_connectivity/ngcc_3stage_ff.connectivity.md` (57행)
- `C:/Users/HSLEE/Documents/Todoc/fpga/wt/_drafts/engine/decision_package_connectivity/nmcnr_amplifier.connectivity.md` (52행)
- `C:/Users/HSLEE/Documents/Todoc/fpga/wt/_drafts/engine/decision_package_connectivity/pushpull_follower_buffer.connectivity.md` (43행)
- `C:/Users/HSLEE/Documents/Todoc/fpga/wt/_drafts/engine/decision_package_connectivity/sf_pushpull_output_opamp.connectivity.md` (83행)
- `C:/Users/HSLEE/Documents/Todoc/fpga/wt/_drafts/engine/decision_package_connectivity/two_stage_ota.connectivity.md` (36행)
- `C:/Users/HSLEE/Documents/Todoc/fpga/wt/_drafts/engine/decision_package_connectivity/two_stage_ota_sf.connectivity.md` (46행)
