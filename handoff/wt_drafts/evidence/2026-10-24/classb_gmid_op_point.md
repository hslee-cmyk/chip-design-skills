# class-B 출력단 gm/ID 설계점 실측 (O-121 B-4 "실측 후 결정")

- 작성: 측정·분석 agent, 2026-10-24. 엔진·계획·design·spec은 고치지 않았다.
- 엔진: `wt/integ-it12/skills/analog-gmid-design/gmid_engine` (integ/it12 HEAD `3179cd78`). library 9개 회로만 썼다. heldout은 쓰지 않았다.
- 스크립트·원자료: `wt/_scratch_classb/scripts/`(probe.py, anchor.py, front.py, spice_pp.py, scale_pp.py, synth_classb.py, summ.py, eng_seal.py = 2026-10-23 eng_seal 사본에서 경로만 integ-it12로 바꿈), `wt/_scratch_classb/out/*.jsonl`(케이스마다 append), SPICE 넷리스트 `wt/_scratch_classb/spice/`.
- SPICE: ngspice-46 `ngspice_con.exe -b`, sky130 tt(pm3), `w = slice w_m`, `m = W / w_m`, 바이어스 넷은 엔진 봉인점 `dc_v`.

## 0. 결론 (먼저)

1. library에서 출력이 push_pull인 회로는 3개다: pushpull_follower_buffer, sf_pushpull_output_opamp, current_reuse_telescopic_ota. 원문은 셋 다 class-AB다. 정지전류는 rout ≤ 1 kΩ나 안정도 gm2 같은 **정지점 AC 요구**로 정해진다. class-B 원문 회로는 없다.
2. pushpull의 0.15 nA는 class-B 현상이 아니다. 원인은 셋이다.
   - layer0 시작점은 '봉인 여유 최대-최소 중심'이다(`meaning = feasibility_only`). rout 제약이 시작점 계산에 들어가지 않는다.
   - M1은 W 하한 `w_min = 0.42 µm`에 붙어 있다.
   - M1은 gm/ID가 LUT 정점의 0.997배인 깊은 약반전 점에 있다.
   SPICE도 정지전류 0.151 nA를 냈다(엔진 0.152 nA). 엔진 모델은 맞고, 이 점이 spec을 못 맞출 뿐이다. 이 점의 SPICE rout는 1.07e8 Ω다.
3. 같은 좌표(현행 (다))에서 θ 전류를 올리면 class-AB 점이 봉인된다. 측정값:
   - 정지 48 µA. 엔진과 SPICE가 모두 48 µA다.
   - SPICE rout 500 Ω로 spec을 통과한다.
   - 최대 출력 0.92 mA(source)·1.8 mA(sink)로, 정지전류의 19~38배다.
   따라서 정지점 gm/ID 사이징은 이 회로에서 의미가 있다.
4. 과제가 정한 (ii) 판정 기준(LUT 약반전 끝, 봉인 9 전도 하한)은 **W에 무관한 밀도 기준**이다. 절대 정지전류를 가르지 못한다. 그 영역은 봉인 9와 반전 하한이 이미 거부한다. 그래서 봉인된 점은 정의상 (ii)가 될 수 없다(§3 F1). **원래 취지와 다름**으로 따로 적는다.
5. 진짜 class-B 구조로 합성 시험을 했다. 두 팔로워의 gate를 vin 하나에 묶었다. 엔진은 0/300 봉인했고 layer0도 실패했다. 이미 fail-closed다. 다만 정지 사유는 일반 사유(LUT VGS 축 밖, `no_root_in_window`)이고 이름 붙은 분기가 아니다.
6. **권고: (다) 현행 유지**. 새 θ·필드·상수가 필요 없다. 0.15 nA는 시작점(layer0)과 탐색 문제로 따로 다룬다(§6 미확인).

## 1. 회로별 출력단 분류 (S1v `output_direction` + 원문)

| 회로 | 출력 노드: topology (충전 셀 / 방전 셀) | 원문 class | 정지전류 선언 | 원문 위치 |
|---|---|---|---|---|
| pushpull_follower_buffer | vout: **push_pull** (M1 σ / M2 σ) | class-AB push-pull follower | 수치 없음. "Current in M1 and M2 determined by VGS4 + VSG3 = VGS1 + VSG2 … Use the W/L ratios to define I1 and I2 from I5 and I6", Rout ≈ 0.5/(gm+gmbs) ≈ 250~500 Ω. spec: rout ≤ 1000 Ω(p.6 도면) | Allen Lecture 26, Page 26-4 = PDF p.4 (그림 060706-02), Page 26-6 = PDF p.6. [웹](https://aicdesign.org/wp-content/uploads/2018/08/lecture26-140625.pdf) · 로컬 `assets/library/sources/pushpull_follower_buffer+sf_pushpull_output_opamp+two_stage_ota_sf__allen_2014/source.pdf` |
| sf_pushpull_output_opamp | Y: **push_pull** (M10 σ / M15 σ); vout: **push_pull** (M22 σ / M21 σ) | class-AB(SF push-pull 출력) | IBias = 50 µA(고정값), "Rout ≈ 1/(gm21+gm22) ≤ 1000 Ω", "bias currents through M18 and M19 vary with the signal" | 같은 원문 Page 26-6 = PDF p.6, Fig. 7.1-1 |
| current_reuse_telescopic_ota | Vom: **push_pull** (M15 σ / M16 σ); Vop: **push_pull** (M25 σ / M26 σ); Vom1·Vop1: none | **Class-AB** 2단 | "both M15 and M16 is biased at a barely-on state". gm2 = 3 mS, gm/Id = 17로 176 µA, Wn2/Wp2 = 25/65 µm로 정한 뒤 "final output stage current is around 22µA while satisfying the stability requirement". 하한은 안정도(gm2)가 정한다 | Xie·Chen 2019, §II.B = PDF p.3 (paper.md 249~280행), 치수 절 = PDF p.4 (paper.md 436~451행). 웹 링크 찾지 못함. 로컬 `assets/library/sources/current_reuse_telescopic_ota__xie_chen_2019/source.pdf` |
| two_stage_ota_sf | vout: class_a (M8 σ / M9 β); OUT: class_a; O1: class_a | class-A follower | I9 (θ 전류) | Allen Page 26-5 = PDF p.5 |
| two_stage_ota | OUT: class_a (M6 σ / M7 β); O1: class_a | class-A | θ 전류 | Maloberti 2004 p.28 |
| folded_cascode | out: class_a (M6 β / M8 σ) | class-A | θ 전류 | Maloberti 2004 p.34 |
| ngcc_3stage_ff | Vout: class_a (M12 β / M13·M14 σ, M7 κ); V1: class_a; V2: none | 3단 출력은 σ가 한 방향(구조 판정 class_a) | θ 전류 | Lee 2007 Fig. 3, 저널 p.24 = PDF p.5 |
| nmcnr_amplifier | Vout: class_a (M302 β / M301 σ) | class-A 3단(M301-M302) | θ 전류. 원문은 "high quiescent current in the output stage"를 저전력에서 피할 조건으로 든다 | Leung 1999 저널 p.600 = PDF p.2 (paper.md 128행, 저널 p.602 = PDF p.4 기준 환산), Fig. 3 = PDF p.4 |
| common_gate_amplifier | vout: none (M3 β / M2 β) | 출력단 해당 없음 | -- | Allen Lecture 20 p.2 |

엔진은 push_pull σ 셀의 정지전류를 θ 전류 성분으로 둔다(`theta_schema.current_cone`).
- pushpull: M1·M2 = θ `current M2`
- sf_pushpull: vout = θ `current M21`, Y = θ `current M9`
- current_reuse: M15 = θ `current M15`, M16 = `M15 − R1`, M25 = `M25`, M26 = `M25 + R1`

원뿔 제약은 전류 > 0을 요구한다. 그래서 웹 조사가 걱정한 "ID = 0 → W = 0/0"은 엔진에서 생기지 않는다. W = ID·L/IDu이고 ID > 0인 θ다.

## 2. 봉인점 실측 (출력 σ 셀)

정의:
- LUT 약반전 끝: 그 소자 (L, VDS, VSB) 곡선(`gm_id_curve`)의 VGS 격자 첫 마디(VGS = 0)다. 측정한 모든 곡선에서 gm/ID 정점이 VGS = 0 마디였다. 따라서 엔진 `ln_idu` 하한(정점 IDu)과 이 끝은 같은 점이다.
- floor: `device.dc_conduction_floor`.
- W 출처: W = ID·L/IDu. ID는 cone의 θ 전류다. IDu는 `ln_idu`가 θ 성분이면 θ 값, 아니면 KCL로 풀린 VGS의 순방향 값이다.

### 2.1 push_pull 회로

| 회로·점 | 소자 | ID | gm/ID (정점 대비) | IDu = ID·L/W | W | ID/floor | IDu/IDu(VGS=0) | W 출처 |
|---|---|---|---|---|---|---|---|---|
| pushpull layer0 | M1 | 1.52e-10 A | 25.85 (0.997) | 5.42e-11 | **4.20e-7 = w_min** | 8.07e3 | 2.67e4 | θ I(M2) ÷ θ ln_idu(M1) |
| pushpull layer0 | M2 | 1.52e-10 A | 25.98 (0.834) | 1.25e-12 | 1.82e-5 | 147 | 376 | θ I(M2) ÷ KCL VSG2(ln_idu 파생) |
| pushpull 흔든 7점 | M1 | 6.4e-11 ~ 2.6e-10 | 25.9~29.1 (0.987~0.997) | -- | 1.9e-7 ~ 1.4e-6 | 8.1e3 ~ 2.1e5 | 2.7e4 ~ 4.7e6 | 같음 |
| pushpull 흔든 7점 | M2 | 6.4e-11 ~ 2.6e-10 | 20.4~31.9 (0.66~0.997) | -- | 1.4e-6 ~ **2.3e-3** | 147 ~ 1.3e6 | 376 ~ 1.3e7 | 같음 |
| pushpull θ 전류 ×10^5.5, ln_idu + 0.7·ln k (pp_grid try 10) | M1 / M2 | 4.80e-5 | 19.6 / 15.9 | -- | 1.88e-5 / 3.51e-3 | -- | -- | 같음 |
| sf_pushpull | -- | 봉인점 없음. layer0 실패(M10 VDS LUT 축 밖, `start_lut_query_failed`). 상자 균등 0/400, IBias(50 µA) 앵커 ±2 ln 0/1500(`lut_query_failed` 1142, N910 `no_root_in_window` 240 등) | | | | | | |
| current_reuse | -- | 봉인점 없음. layer0 실패(Ncmfb_tail `no_root_in_window`). Iref 앵커 0/600, 상자 0/300(N23a24b·Vbias4 `no_root_in_window` 등) | | | | | | |

### 2.2 class_a 회로 (비교 기준)

| 회로 | σ 셀 | layer0 ID | layer0 gm/ID (정점 대비) | ID/floor (전 8점) | IDu/IDu(0) (전 8점) |
|---|---|---|---|---|---|
| two_stage_ota | M6 (OUT) | 2.48e-5 | 14.8 (0.59) | 2.5e4 ~ 7.7e8 | 1.0e5 ~ 1.8e10 |
| two_stage_ota_sf | M8 (vout) | 2.71e-5 | 18.3 (0.75) | 1.3e6 ~ 8.3e6 | 1.2e7 ~ 1.3e8 |
| folded_cascode | M8 (out) | 1.13e-6 (W = w_min) | 19.0 (0.71) | 4.1e7 ~ 3.1e8 | 6.6e8 ~ 8.4e9 |
| ngcc_3stage_ff | M13 / M14 (Vout) | 2.82e-5 / 1.45e-5 | 20.2 / 21.3 (0.83 / 0.88) | 2.8e4 ~ 5.7e5 | 6.2e5 ~ 1.6e7 |
| nmcnr_amplifier | M301 (Vout) | 1.12e-3 | 22.5 (0.95) | 9.6e3 ~ 5.0e4 | 1.3e5 ~ 8.1e5 |

밀도 기준(ID/floor, IDu/IDu(0), gm/ID 정점 대비)으로는 pushpull layer0 M1이 nmcnr M301과 같은 무리에 든다. 두 소자는 모두 정점의 0.95~0.997이고 floor 대비 1e4 수준이다. 둘을 가르는 것은 절대 전류뿐이다(0.15 nA 대 1.1 mA).

## 3. 측정 사실

- **F1 전도 하한·LUT 끝은 W에 무관하다.** 봉인 9: floor = I_off/ε = [IDu(VGS=0)·W/L]/[(gm/ID)·tol_V]이고 ID = IDu·W/L이다. 그러면 ID/floor = IDu(VGS)·(gm/ID)·tol_V / IDu(0)이고 W가 지워진다(`sizing/seal_conduction.py` docstring, `search/cell_floor.py` [r9]도 같은 식을 "W/L이 지워져"라고 적는다). 정의역 상자 균등 표본으로 확인했다. pushpull box try 166은 ID = **3.4e-24 A**, M1 W = 1.2e-13 m에서 봉인 9를 통과했다(ID/floor 6.8). 이 점은 W ≥ w_min(S-18, 탐색 제약 `CON_WMIN`)을 어긴다. 그 제약은 봉인 항목이 아니다. 결론: 두 선언은 반전 수준을 묶을 뿐이다. 절대 정지전류에는 하한을 주지 않는다.
- **F2 절대 하한은 W 하한에서만 나온다.** W ≥ w_min과 IDu ≥ IDu(VGS=0)을 합치면 ID ≥ IDu(0)·w_min/L이다. pushpull layer0의 (L, VDS, VSB)에서 이 값은 M1 2.03e-15·0.42/0.15 = 5.7e-15 A, M2 9.3e-15 A다. layer0의 0.15 nA는 이 하한보다 2.7e4배 위다.
- **F3 0.15 nA의 출처.** layer0 기록은 `origin_point = centre`, `meaning = feasibility_only`, `meaning_reason = w_bounded_by_area_budget`이다. θ 전류 상자는 nmos (2.65e-19, 36.5) A, pmos (2.42e-26, 6.87) A다. 봉인 여유 최대-최소 중심이 M1을 W = w_min과 정점 근처 약반전에 두었고, 그 결과 ID = w_min/L × 약반전 IDu가 되었다. rout spec은 layer0에 들어가지 않는다.
- **F4 SPICE 대조 (layer0 + 흔든 7점).** 넷리스트 `wt/_scratch_classb/spice/pp_*`, 결과 `out/spice_pp.jsonl`.
  - 정지 ID: 엔진 대 SPICE 차 0.3~6 %. vout 차 ≤ 3 mV.
  - vout을 봉인점에 고정하고 vin을 0→1.8 V로 민 `.dc`(O-28 정의)의 최대 출력: source 0.20 µA ~ 26.6 µA, sink 1.4 µA ~ 59.6 µA. 최대/정지는 3e3 ~ 5e5다.
  - SPICE rout(vout ±2 mV): 6.8e7 ~ 2.2e8 Ω. spec 1e3 Ω를 크게 넘는다.
- **F5 현행 좌표에서 spec을 맞추는 class-AB 점 (scale_pp, pp_grid).**
  - θ 전류만 k배로 키우면(ln_idu 그대로) 모든 k(1 ~ 1e6)에서 봉인된다. gm만 쓴 rout = 1.27e8/k다.
  - θ 전류 ×10^5.5에 ln_idu + 0.7·ln k를 더한 점은 봉인되었다.
    - 엔진: ID 48.0 µA, gm/ID 19.6 / 15.9
    - SPICE: ID 48.0 µA, rout **500 Ω**, 최대 출력 0.92 mA(source) / 1.8 mA(sink)
  - ×10^5(ID 15.2 µA) 점은 SPICE rout 1505 Ω로 spec을 넘는다.
  - M2 W가 1.98 ~ 3.5 mm로 크다. M2의 ln_idu는 θ가 아니라 VGS4 + VSG3 = VGS1 + VSG2(KCL)로 정해지기 때문이다. 이 상태로 면적 예산 5e-9 m² 안에 든다.
- **F6 합성 class-B 시험 (`scripts/synth_classb.py`, scratch 전용 topology).**
  - 구조: M1 nmos (d vdd, g vin, s vout), M2 pmos (d vss, g vin, s vout). VGS1 = −VSG2다.
  - S1v는 vout을 push_pull(M1 σ / M2 σ)로 낸다. 이 구조와 class-AB는 구조로 가를 수 없다(`output_direction.py` docstring과 같다).
  - layer0 실패: `start_no_root_in_window`.
  - 상자 균등 300점 모두 봉인 안 됨. M2 VGS LUT 축 밖(`forward_point`, 264)과 vout `no_root_in_window`(나머지)다.
  - 정리: 이미 fail-closed다. 정지 사유는 일반 LUT·근 사유이고 이름 붙은 분기가 아니다.
- **F7 탐색(find_front) 결과.** pushpull에서 front·pending·unmeasured가 모두 0점이었다. eval_budget 40은 `eval_budget`에서, 2000은 두 방향 모두 `slsqp_4`에서 멈췄다. 탐색이 rout ≤ 1 kΩ 점을 찾지 못한 원인은 **미확인**이다. F5로 그런 점이 봉인 가능하다는 것은 확인했다.

## 4. 판정 (기준은 기존 선언만 썼다: LUT VGS = 0 끝 = ln_idu 하한, 봉인 9 floor, W 하한 S-18)

| 회로 | 판정 | 근거 |
|---|---|---|
| pushpull_follower_buffer | **(i)** | 모든 봉인점이 floor·LUT 끝 위에 있다(layer0 최소 ID/floor 147, IDu/IDu(0) 376). 원문은 class-AB이고 spec rout는 정지점 AC 양이다. SPICE가 정지 모델(≤ 6 %)과 spec 충족 class-AB 점(F5)을 확인했다. 0.15 nA는 layer0 중심 문제다(F3) |
| sf_pushpull_output_opamp | **(iii)** | 엔진 봉인점 0. 원문(class-AB, Rout ≤ 1000 Ω가 정지 gm으로 정해짐)만 보면 (i)로 예상된다 |
| current_reuse_telescopic_ota | **(iii)** | 엔진 봉인점 0. 원문(class-AB, 정지 22 µA, 하한 = 안정도 gm2)만 보면 (i)로 예상된다 |
| two_stage_ota, two_stage_ota_sf, folded_cascode, ngcc_3stage_ff, nmcnr_amplifier | (i) | class_a, σ 출력 ID 1.1 µA ~ 1.1 mA, floor 대비 ≥ 9.6e3 |
| common_gate_amplifier | 해당 없음 | 출력 topology none |

(ii) 판정 회로: 0개. F1 때문에 정의대로 쓴 (ii)는 봉인 9와 반전 하한이 이미 거부하는 영역이다. 봉인된 점에는 나타날 수 없다. **원래 취지와 다름:** 과제는 "정지전류가 LUT 밖·전도 하한 근처면 사실상 class-B"로 정의했다. 실측으로는 이 두 기준이 절대 전류를 보지 않는다. 기존 선언만으로 정지전류가 '작다'는 절대 판정을 만들 수 없다. 만들려면 새 문턱(상수)이나 spec 근거(rout, 부하 전류 등)가 필요하다.

SPICE 대조(과제 4)는 (ii) 회로가 없어서, 의심 회로인 pushpull에 대해 했다(F4·F5).

## 5. 세 안 비교

| 칸 | (가) 출력 소자를 최대 전류 설계점에서 gm/ID로 | (나) 지원 밖 fail-closed (`unsupported_rule_branch`) | (다) 현행 |
|---|---|---|---|
| 물리 정합 | class-B에는 맞는다. library 3개 회로는 class-AB이고 spec(rout, gm2 안정도)이 정지점 AC다. 정지 동작점을 W 고정 KCL로 다시 풀어야 해서 동작점이 둘이 된다 | 거부만 한다. 판정 대상(절대 정지전류)을 기존 선언으로 정의할 수 없다(F1) ⚠ | 정지점 SPICE 일치 0.3~6 %(F4), spec 충족 class-AB 점 존재(F5). 대신호 최대 전류는 W 고정으로 `ls_fields` σ = LUT ID(VGS_max)가 이미 낸다 |
| 손계산 속도 | 소자마다 동작점 두 번 + 정지점 KCL 재풀이로 느려진다 | 같다 | 같다 |
| graph 정본 | 새 θ 좌표(I_max 또는 최대 상태 밀도)와 새 필드(최대 상태 dc_op)·writer가 필요하다. 지금 ls_fields가 W 고정으로 내는 σ 상한과 같은 양을 다른 자리에서 다시 구하는 둘째 생산자 위험이 있다 ⚠ | 새 사유 이름만. 필드 0 | 새 θ·필드 0 |
| fail-closed | -- | 목적 그 자체. 진짜 class-B는 이미 일반 사유로 막힌다(F6). 새 분기는 사실상 사유 이름 바꾸기다 | 진짜 class-B는 봉인 실패(F6). 사유 이름이 일반적인 것은 약점이다 |
| 상수 0 | I_max의 출처가 spec에 없다. pushpull·sf_pushpull spec에는 SR·부하 전류 제약이 없고 rout와 면적뿐이다. 만들면 상수 발명이다 ⚠ | 절대 문턱이 필요한데 기존 선언에서 나오지 않는다(F1·F2) ⚠ | 0 |
| 일반성 | push_pull σ 셀 전체에 적용된다 | 구조로 AB와 B를 못 가른다. 값 기준은 상수 필요 ⚠ | topology 무관 |
| 원칙 충돌 | '설계점 = θ 고정, 섭동 = KCL' 틀을 뒤집는다(정지점이 KCL 파생). 계획 개정이 먼저다(S-7) ⚠ | -- | 없음 |
| 영향받는 회로 수 | 3 (push_pull 회로) | library 봉인점 0 | 0 |
| 구현 범위 | 큼: θ 스키마·sizing 커널·봉인·탐색 정의역·계획/design 개정 | 작음: 사유 이름·test. 판정식이 없어 착수 조건이 안 된다 | 없음 |

## 6. 권고 (하나)

**(다) 현행 유지.** 근거는 다음과 같다.
- library에 class-B 원문 회로가 없다.
- push_pull 3개 회로의 원문은 모두 정지점 AC 요구로 정지전류를 정하는 class-AB다.
- 현행 좌표가 정지 모델(SPICE ±6 %)과 spec 충족 class-AB 점(rout 500 Ω, 최대/정지 19~38)을 모두 표현한다.
- 진짜 class-B는 이미 봉인 실패로 fail-closed다.
- (가)·(나)는 새 θ·필드나 상수가 필요하다(⚠).

원칙 점검:
- graph 정본: 새 필드·cache 0.
- 상수: 0.
- DC/AC 분리: rout는 정지 DC 점의 AC 양이다.
- 계산 틀: 사이징은 θ 고정, 대신호 최대 전류는 W 고정(ls).
- 일반성: topology 무관.
- 원래 취지와 다름: §4 (ii) 정의 항목.

이 권고는 pushpull 0.15 nA를 "고칠 것 없음"으로 덮지 않는다. 0.15 nA는 class-B 문제가 아니라 layer0 시작점(feasibility 중심)과 탐색이 rout 점을 못 찾는 문제(F7)다. 그쪽은 별도 항목이다.

## 7. 미확인

- F7: find_front가 pushpull에서 `slsqp_4`로 멈춘 원인. F5의 봉인·spec 충족 점이 있는데도 탐색이 0점이다. 시작점, 상자 26자릿수, M2 W 상한 중 무엇 때문인지 재지 않았다.
- sf_pushpull·current_reuse의 봉인점 실측. 두 회로 모두 봉인점이 0이라 출력 σ 값을 재지 못했다. 원인은 LUT VDS 축 밖과 `no_root_in_window`로, class-B와 무관한 별도 결함으로 보인다(**추정**).
- pushpull M2 W(mm 단위)가 VGS4 + VSG3 = VGS1 + VSG2 KCL에서 나오는 구조적 결과인지, θ 선택 문제인지. 재지 않았다.
- F5의 grid 배수(10^4.5~10^5.5, 0.5~1.0)는 진단 표본 범위이고 판정 기준이 아니다.
- 합성 class-B 시험(F6)은 scratch topology 하나만 썼다. 다른 class-B 꼴(crossover inverter, Allen p.9)은 재지 않았다.
- `ss_evaluate`의 rout 값은 직접 읽지 않았다. 엔진 rout는 gm만 쓴 손계산(gmb 제외)이다. SPICE rout만 측정값이다.
