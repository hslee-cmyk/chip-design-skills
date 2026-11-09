# 9개 library 회로 정합(입력 offset·미러비)·스윙/ICMR 스펙 제안서 (검토용 초안)

작성 2026-10-08. 저장소는 읽기만 했다(이 파일만 새로 씀, 실측은 스크래치). 이 문서는 **제안**이다. sizing_spec에 반영된 것은 없다.
사용자 결정(2026-10-08): Q3(입력 offset·미러비 오차)·Q4(출력 스윙·ICMR)는 **값이 있는 곳만 활성**, 나머지는 구조 분석 기반 제안을
준비해 검토받는다. 같은 방법·문체: `noise_spec_proposal.md`(회로별 출처 사실은 그 문서와 같은 확인 범위).

현재 상태(실측):
- 선언된 값: 파일럿·two_stage_ota `mismatch_sigma_mv ≤ 5.0`(source `pending_spice`, U-17 "7a 재도출 대상"), two_stage_ota_sf는
  `value_from_file: two_stage_ota#mismatch_sigma_mv`, 파일럿 `mirror_ratio_error_mv ≤ value_from_constraint mismatch_sigma_mv`,
  ngcc `{metric: pending MOD5} ≥ 0.6`(옛 icmr_v, 논문 ICMR ≥ VDD/3을 1.8 V로 재계산). 나머지 회로 Q3·Q4 선언 없음.
- `mismatch_sigma_mv`·`mirror_ratio_error_mv`는 MOD5 레지스트리에 없다(`SPEC_CONTRACT.md:255` S2). 스윙·ICMR metric도 이름이 없다
  (ngcc 주석 "N3.8 스윙·입력 범위 ls metric, MOD5 design 이 이름을 정한다"). 그래서 아래 metric은 **구현 card가 먼저 필요**하다.
- 5.0 mV의 출처: 파일럿 topology `constraints[1]._comment` "여전히 도출 근거가 없다 ... 시스템 레벨 오프셋 요구에서 와야 하는 설계 입력",
  two_stage_ota는 그 값을 복제(`_target_spec_comment` (2)). 즉 두 값 모두 근거 없는 자리값이다.

---

## 0. 공통 근거

### 0.1 sky130 mismatch 모델 원문
파일 `C:/pdk/sky130_fd_pr/cells/{nfet_01v8,pfet_01v8}/sky130_fd_pr__*__mismatch.corner.spice`(`models/sky130.lib.spice:36-37`이 모든 corner에서
include). 모델 카드(`*__tt.pm3.spice`)에서 소자마다 독립 가우스(`statistics { mismatch { vary ..._slope_spectre dist=gauss std = 1.0 } }`)
변수 × slope / sqrt(l·w·mult)로 들어간다. 예: `vth0 = {0.5190093 + ..._vth0_slope_spectre*(..._vth0_slope/sqrt(l*w*mult))}`,
`toxe = {4.148e-09 + ..._toxe_slope_spectre*(4.148e-09*1.0*(..._toxe_slope/sqrt(l*w*mult)))}`.
`models/all.spice:2` `.option scale=1.0u` → l·w는 **µm²**. 따라서 slope의 단위는 vth0 = **V·µm**, toxe = **무차원·µm**(상대값).

| 파라미터 | nfet_01v8 | pfet_01v8 | 쓰는 bin(카드 180/108개 전수 집계) |
|---|---|---|---|
| vth0_slope | 3.356e-3 | 5.856e-3 | n: 176 bin / p: L ≥ 0.5 µm 72 bin |
| vth0_slope1 | 7.356e-3 | 7.356e-3 | n: L 4–8 µm·좁은 W(< 0.52 µm) 4 bin / p: **L < 0.5 µm** 36 bin |
| toxe_slope (/1) | 3.443e-3 | 4.443e-3 / 6.443e-3 | p: slope1 = L < 0.5 µm |
| voff_slope | 0.007 | 0 (slope2 0.007은 카드에서 안 씀) | |
| nfactor_slope (/1) | -- | 0.1 / 0.1 | |
| lint·wint slope | 0 | 0 | |

**발견 1(legacy 결함)**: `legacy/sizing_recipe.py:3073 estimate_mismatch_sigma`는 pfet에 5.856e-3 하나만 썼다 -- L < 0.5 µm pfet은
7.356e-3(+26 %)이다. 또 vth0 한 항만 본다(아래 0.3: toxe·voff 항이 같은 크기).

### 0.2 Pelgrom 계수 유도(원문 slope에서, 쌍 = 두 소자 독립 → √2)
σ(ΔVT) = A_VT/√(WL), A_VT = √2·vth0_slope. β ∝ Cox ∝ 1/toxe(1차) → σ(Δβ/β) = A_β/√(WL), A_β = √2·toxe_slope.

| | nfet_01v8 | pfet_01v8 L ≥ 0.5 µm | pfet_01v8 L < 0.5 µm |
|---|---|---|---|
| A_VT (vth0 항만) | **4.75 mV·µm** | **8.28 mV·µm** | **10.40 mV·µm** |
| A_β (toxe, 1차 Cox) | **0.487 %·µm** | **0.628 %·µm** | **0.911 %·µm** |

### 0.3 ngspice 감도 실측 -- toxe는 β보다 **Vth로** 더 크게 들어간다
방법(스크래치 `mm/mm.py`): pm3 카드 복사본에서 `<param>_slope_spectre`를 0 → 1e-6(인스턴스 l·w를 m로 주므로 1e-6 = 그 기하의 1σ)으로
바꾸고, W = 5 µm(LUT W_ref와 같음), |VDS| = 0.9 V, VS = 0, L 7점에서 VGS를 1 mV 간격 DC 스윕. 기준 곡선에서 gm/ID 목표점의 ID를
고정하고 섭동 곡선에서 같은 ID의 VGS 차 = 그 파라미터 1σ의 ΔVGS. 파라미터끼리 독립이므로 RSS, 쌍은 ×√2, A_eff = σ_pair·√(WL).

검증: vth0 항만 떼면 n 4.59–4.85(= 0.2의 4.75), p L ≥ 1 µm 8.42–8.53(= 8.28), p L = 0.5 µm 10.46(= slope1 10.40 -- W 5 µm에서
L = 0.5가 [0.25, 0.5] bin에 든다). toxe의 β 성분(ΔVGS_toxe = a + b/(gm/ID) 적합, gm/ID 5–12): n 0.45–0.52 %·µm(= 0.487),
p L ≥ 1 0.56–0.59(= 0.628), p L ≤ 0.5 0.88–1.16(= 0.911). **유도와 일치.** 그러나 절편 a(toxe → Vth, BSIM4 k1ox = k1·toxe/toxm 등)가
n 2.2–4.1, p 2.3–6.5 mV·µm로 vth0 항과 같은 크기다.

**유효 입력환산 계수 A_eff(쌍, mV·µm) = σ(ΔVGS at 같은 ID)·√(WL)** -- 엔진이 써야 하는 값:

| L (µm) | n gm/ID 5 | 10 | 15 | 20 | p gm/ID 5 | 10 | 15 | 20 |
|---|---|---|---|---|---|---|---|---|
| 0.15 | 7.0 | 8.6 | 10.1 | 11.1 | 12.5 | 12.1 | 12.1 | (12.8*) |
| 0.18 | 7.3 | 8.6 | 10.0 | 11.2 | 12.5 | 12.0 | 12.0 | (12.4*) |
| 0.25 | 6.5 | 7.1 | 8.3 | 9.7 | 12.6 | 12.0 | 11.9 | 12.0 |
| 0.5 | 5.8 | 6.0 | 7.1 | 8.6 | 11.9 | 11.4 | 11.3 | 11.4 |
| 1.0 | 6.1 | 6.3 | 7.5 | 8.9 | 9.5 | 9.1 | 9.0 | 9.2 |
| 2.0 | 6.1 | 7.0 | 8.5 | 9.8 | 9.4 | 9.0 | 8.9 | 9.4 |
| 4.0 | 6.1 | 6.7 | 8.1 | 9.4 | 9.4 | 9.0 | 8.9 | 9.3 |

(*) pfet L ≤ 0.18 µm의 gm/ID ≥ 18은 VSG 0.13–0.41 V의 누설 가지에서 잡힌 점이라 믿지 않는다(LUT도 같은 모양: pfet L 0.15 µm의
VGS ≥ 0.3 V 최대 gm/ID = 15.3).

강반전 분해(gm/ID 5–12): A_VT,eff = √(A_VT,vth0² + A_VT,tox²) = n **5.3–6.3**, p **11.1–11.5**(L ≤ 0.5) / **8.8–8.9**(L ≥ 1) mV·µm.
nfet은 약반전으로 갈수록 voff 항이 커진다(L 0.15 µm gm/ID 20: voff 7.6 mV vs vth0 3.8 mV, 단일 소자 W 5 µm).

**발견 2**: vth0만 쓰는 옛 식은 nfet을 **1.2–2.4배**, pfet을 **1.05–1.4배** 과소평가한다(약반전·짧은 L일수록 큼). 파일럿 논문 바이어스
(gm/ID 19, L 0.18 µm)에서 nfet A_eff 11 vs 옛 4.75.

**제안(엔진 쪽)**: 상수 표를 박지 않는다. LUT 생성기(`assets/sky130_lut_sweep.py`)가 이미 같은 include·DUT 줄로 점마다 돌므로, 같은
방식으로 **mismatch 감도 열** `DVGS_<param>`(param ∈ 카드의 *_slope_spectre 이름 전수, 1σ·W_ref·각 L 기준, 같은 ID에서의 ΔVGS)을
추가하고, 엔진은 σ_VGS,single(W, L, 점) = √(Σ_k (DVGS_k·slope_k(bin)/slope_k(bin_ref))²)·√(W_ref·L)/√(W·L)로 쓴다. slope는
mismatch.corner.spice에서 bin(LBinMap)별로 읽는다. 이것은 LUT·엔진 변경이라 승인 대상(§12-1).
한계: 이번 실측은 W 5 µm·VDS 0.9 V·VS 0 한 슬라이스다. W에 따른 bin 전환(nfet 좁은 W L 4–8 µm 등)은 slope 표로만 반영된다.

### 0.4 헤드룸 근거: LUT v2 r2의 |VGS|·VDSAT
출처 `lut_data/sky130_lut_v2/sky130_nfet_pfet_lut_v2_r2.npz`(BSIM `vdsat` 열 = 사용자 SPICE 포화 규칙 `vds_ge_vdsat`과 같은 양), W_ref 5 µm,
|VDS| = 0.9 V. 칸 = |VGS| / VDSAT (V).

| 소자, L | VS | gm/ID 8 | 10 | 15 | 20 |
|---|---|---|---|---|---|
| n 0.18 | 0 | 0.905/0.153 | 0.861/0.133 | 0.775/0.090 | 0.662/0.053 |
| n 0.5 | 0 | 0.851/0.192 | 0.800/0.160 | 0.710/0.104 | 0.626/0.065 |
| n 0.5 | 0.4 | 0.929/0.196 | 0.878/0.164 | 0.791/0.108 | 0.714/0.069 |
| n 1.0 | 0 | 0.821/0.201 | 0.770/0.166 | 0.682/0.107 | 0.603/0.066 |
| p 0.15 | 0 | 0.904/0.207 | 0.840/0.164 | 0.679/0.078 | -- |
| p 0.18 | 0 | 1.022/0.222 | 0.960/0.176 | 0.809/0.086 | -- |
| p 0.5 | 0 | 1.193/0.222 | 1.134/0.176 | 1.019/0.099 | 0.743/0.045 |
| p 0.5 | 0.4 | 1.287/0.229 | 1.230/0.183 | 1.121/0.106 | 0.841/0.046 |
| p 1.0 | 0 | 1.232/0.222 | 1.173/0.177 | 1.056/0.099 | 0.798/0.046 |

**발견 3(sky130 고유)**: pfet_01v8의 |VT|가 **bin에 따라 크게 뛴다** -- gm/ID 15에서 VSG = 0.68(L 0.15) / 0.81(L 0.18) / 1.02(L 0.5) V.
1.8 V 전원에서 PMOS 소자가 '게이트-소스로 쌓이는' 경로(PMOS 입력쌍, PMOS 팔로워, PMOS 미러 부하)는 L bin 선택이 곧 헤드룸 가능 여부다.
VS는 이 문서에서 bulk = 해당 레일로 가정했다(topology `b`는 모두 None -- §12-6).

### 0.5 입력 커패시턴스(파일럿 β 계산용)
LUT `CGG/(W·L)`(외인 포함): n L 0.5 µm gm/ID 15 = **6.04 fF/µm²**, p = **4.87 fF/µm²**(L 0.18: 7.75 / 5.85).

---

## 1. metric 정의 제안 -- 새 숫자 없이

| 이름(제안) | 정의 | 대체·관계 |
|---|---|---|
| `offset_in_sigma_mv` | **입력환산 랜덤 offset 1σ**. 모든 MOS i에 독립 게이트 전압원 σ_VGS,i(0.3 감도 열 × slope(bin)/√(W_iL_i))을 두고, MNA 저주파 전달로 출력(차동 출력이면 차동)으로 보낸 분산을 합해 차동 이득 A_dm으로 나눈다: σ²_in = Σ_i (H_i·gm_i·σ_VGS,i)² / A_dm², H_i = 소자 i의 드레인 전류 → 출력 전달 임피던스 | 옛 `mismatch_sigma_mv`(입력쌍만·vth0만·gm 가중) 계산을 대체. 이름표는 MOD5가 정함 |
| `offset_sys_mv` | **계통 offset**: 명목 동작점(MNA DC, 실제 VDS 반영)에서 입력 차 0일 때 출력 오차 / A_dm | 옛 `mirror_ratio_error_mv`(ratio 쌍 ΔVDS/V_A/(gm/ID))의 일반화. 상한 = `value_from_constraint: offset_in_sigma_mv`(기존 규칙 "계통 ≤ 랜덤 예산" 유지, 새 숫자 0) |
| `mirror_ratio_sigma_pct` | J-U4 mirror 그룹(tail_ratio·bias_distribution 포함)마다 랜덤 전류비 σ(ΔI/I) = (gm/ID)·σ_ΔVGS,pair | 보고 전용(전류 오차 → GBW·전력 산포) |
| `swing_out_v` | 출력 DC를 움직일 때 **모든 MOS가 VDS ≥ VDSAT + tol_vdsat**(사용자 포화 규칙 + LUT 허용오차 `tol_vdsat_table`)를 만족하는 출력 범위 [V_lo, V_hi]. 차동 출력이면 출력마다 | 대안 정의(§12-5): 소신호 이득 ≥ 그 회로의 gain 제약값인 범위(논문 Fig. 10 방식) |
| `icmr_v` | 입력 공통모드 창 [Vin,min, Vin,max] ∩ [하단 레일, 상단 레일]과 그 폭. 경계 = 입력 경로 소자 전부 VDS ≥ VDSAT + tol | ngcc 옛 icmr_v |
| `icm_margin_v` | 선언된 입력 DC(SP-2, 또는 `input_dc.net`)와 창 경계의 최소 거리 | 입력 DC가 선언된 회로의 실현가능성 |

MNA 방식은 회로 이름·그룹 규칙 없이 위상 무관하게 계산된다. J-U4 matching 그룹(CONTRACT 4.5a)은 계산 대상이 아니라 **해석·대조**에 쓴다:

| J-U4 그룹 종류 | offset에서의 역할(구조 분석) |
|---|---|
| diff_pair | σ_ΔVGS 그대로(가중 gm_pair/Σgm_in) |
| mirror(whole·consumer_symmetric)이 **차동쌍 drain 대응 넷 짝**에 붙은 것 | ΔI = gm_load·σ_ΔVGS,load를 입력쌍 gm으로 나눔 → (gm_load/gm_in)·σ_load |
| tail_ratio·bias_distribution·꼬리 | 공통모드 → 차동 offset 1차 0(CMRR로만 샘). 전류 산포는 `mirror_ratio_sigma_pct` |
| branch_symmetric(캐스코드) | ~1/(gm·ro) 배로 감쇠 → 무시 가능 |
| 뒷단(signal_cross_block 등) | 앞단 이득으로 나뉨 → 무시 가능 |
| CMFB 차동쌍 | 차동 offset 0, **출력 공통모드 offset**(→ 스윙 소모) |

---

## 2. current_reuse_telescopic_ota (파일럿) -- 값 있음(5 mV, 근거 없음)

### 2.1 출처 사실(Xie & Chen, 로컬 PDF `G:/내 드라이브/work/Todoc/논문모음/A 126uW ... .pdf`, pdftotext로 확인)
- Table I(Specs / Our Results): **Output swing 스펙 [-1.2 V, 1.2 V]**, 결과 [-1.706 V, 1.706 V](차동). **Input common-mode range:
  스펙 칸 비어 있음, 결과 [576.5 mV, 900.1 mV]**. **offset 항목 없음**. Static settling error 0.1 %(스펙) / 0.033 %(결과).
- 초록: CMFB가 출력 공통모드를 **0.9 V**로 안정화.
- II.B: M15 gate ≈ 1.3 V, M16 gate ≈ 0.5 V, 1단 출력 ≈ 0.5 V가 "lower side NMOS biasing"에 압박을 주고 "**unsymmetrical input common
  mode range** ... when the input common-mode voltage is high, the bottom devices (M3, M4 and M5) are pushed to linear region".
- III.A 식 4: β = Cf/(Cf+Cs+Cgg1), "we assume that β is around 0.48" (Cf = Cs = 500 fF → Cgg1 ≈ 41.7 fF 가정과 같다).
- 입력 소자: gm/ID 19, I = 6 µA, Wn 2 µm, Wp 6 µm(L 0.18 µm).

### 2.2 offset 구조 분석(netlist·J-U4 파일럿 행)
- 입력: diff_pair {M1a, M1b}(pmos, Vx) + {M4a, M4b}(nmos, Vy)가 같은 입력 → gm1 = gm_p + gm_n.
- **1단 출력 노드(Vop1/Vom1)에 전류를 넣는 대칭쌍** -- J-U4 consumer_symmetric {M10, M19}(drain Vop1/Vom1)와 {M8, M17}(drain Vg15/Vg25;
  Vg15 KCL: I_8 = I_9a + I_9b가 전부 M9a/M9b를 지나 Vop1로 간다). 둘 다 ΔI를 1단 출력에 직접 넣는다 → 입력환산 (gm_x/gm1)·σ_x.
  **옛 metric은 이 두 쌍을 안 셌다.**
- 캐스코드 {M2a, M2b}·{M3a, M3b}(branch_symmetric): 무시 가능. 꼬리 M5·M6·M7·M38 등(tail_ratio): 공통모드.
- CMFB {M37a, M37b}: 출력 공통모드 offset σ_CM ≈ σ_ΔVGS,37(루프가 Voc = Voc_des + offset으로 맞춤) → §2.4 스윙 소모.
- 2단(M15/M16, M25/M26): 1단 이득((gm·ro)² 규모)으로 나뉨 → 무시.

  σ²_os,in = [(gm_p σ_p)² + (gm_n σ_n)² + (gm_8 σ_8)² + (gm_10 σ_10)²] / (gm_p + gm_n)²,  σ_x = A_eff,x/√(W_xL_x)

예시(값 아님, 전류비 가정 표시): gm_p = gm_n(논문), 입력 gm/ID 15, M8 gm/ID 10·I_8 = I_1, M10 gm/ID 10·I_10 = I_1 + I_8, 모든 L 0.5–1 µm,
같은 WL → σ² = (31.7 + 12.7 + 9.1 + 17.9)/WL mV² → **뒤 두 쌍이 분산의 38 %**.

논문 크기(Wp 6/0.18, Wn 2/0.18, gm/ID ≈ 19)에서 입력쌍만: 옛 식(vth0, pfet slope 5.856) 5.6 mV / slope 정정(10.40) 6.4 mV /
**A_eff 약 11 mV**(n 10.9, p는 L 0.18 µm에서 gm/ID 19가 믿을 수 있는 점이 아니라 gm/ID 15 값 12.0 사용). -- 논문 크기 그대로면 5 mV를
2배 넘는다. (sky130 pfet은 L 0.18 µm에서 gm/ID 19에 정상 가지로 도달하지 못한다 -- 0.3 표 주석.)

### 2.3 5 mV를 대신할 값 -- 목적(정확도·β)에서 유도
(A) **정적 정확도 규칙**(잡음 문서 §2.4와 같은 해상도): 출력환산 offset ≤ ½ LSB, σ_in ≤ β·V_FS/2^(N+1), N = ⌈log2(1/ε_d)⌉ = 10,
V_FS = 2.4 V(Table I 스윙 스펙, 채택 대기) → 0.56 mV(β 0.48). 이를 만족하는 최소 입력 용량은 Cin = (Σ A_i√c_i)²/(4σ²)
(라그랑주 최적 배분, 0.5의 c_i) = **1.42 pF/측** → β = Cf/(Cf+Cs+Cin) = 0.21. β를 자기일관으로 풀면 s + 0.449/s = 0.586(s = σ, mV)이
**해가 없다** → 이 회로·이 Cf/Cs에서는 어떤 크기로도 불가능. 정적 정확도가 필요하면 offset 제거(CDS·자동영점) = 클럭·위상 변경이다.
(B) **스윙 소모 규칙**: offset은 이득 정확도(ε_d)에는 안 들어가고 출력 범위만 깎는다 → §2.4의 스윙 제약에 합친다.
   구조 추정: 달성 ±1.6–1.7 V(차동) vs 요구 ±1.2 V → 허용 출력 offset ~0.4–0.5 V → σ_in 수십 mV, **비구속**.
(C) **β 가정과 일관된 하한**: 입력 용량이 β 가정(0.5 → 0.48, Cgg1 = 41.7 fF)을 넘지 않는 최대 면적에서의 σ_os =
   (Σ A_i√c_i)/(2√Cin) = **3.3 mV**(gm/ID 15, L 0.5 µm; WL_p 5.0 µm², WL_n 2.9 µm²) / 4.4 mV(L 0.18 µm). 5 mV는 이 하한 근처라
   우연히 '그럴듯한' 값이었다. 단 β 0.48은 논문 가정이라 앵커이고, β 손실은 전력(gm1 = ω_c·Cc/β)과 교환되는 목적 함수 문제다.

### 2.4 스윙·ICMR 구조 분석
- **출력**: 출력마다 M15(pmos CS)/M16(nmos CS): Vo ∈ [VDSAT16, VDD − VSDsat15] → 차동 ±(VDD − VDSAT_n − VDSAT_p). class-AB 정지 전류가
  약반전(논문 "barely-on")이라 LUT VDSAT 0.04–0.07 V → **±1.66–1.72 V**(논문 결과 ±1.706 V와 같은 규모 → 식 검증). 요구 ±1.2 V(채택 대기)
  대비 여유 ~0.5 V. 출력별 소모 = 차동 출력 offset/2 + CMFB offset(σ_37) + tol_vdsat.
- **ICMR(발견 4, 중요)**: 입력 두 극성이 같은 gate. Vx = Vin + VSG1 ≤ VDD − VSDsat6, Vy = Vin − VGS4 ≥ VDSAT5 →
  **VDSAT5 + VGS4 ≤ Vin ≤ VDD − VSDsat6 − VSG1**, 창 폭 = VDD − VGS4 − VSG1 − VDSAT5 − VSDsat6. (위쪽은 추가로 nmos 스택
  Vin ≤ V_o1,CM + VGS4 − VDS4 − VDSAT3 -- 논문 II.B의 'M3·M4·M5 선형' 한계, VDS4는 M63/M64 추적 바이어스가 정함.)
  LUT(입력 VDS 0.4 V·VS 0.2 V, 꼬리 VDS 0.2 V): 창 폭 = **L 0.15 µm**(nfet gm/ID 20, pfet 15, 꼬리 gm/ID 15) **+0.14 V**, 같은 조건 L 0.18 µm
  −0.02 V, L 0.5 µm −0.15 V, 꼬리 gm/ID 10이면 전부 더 나쁨. → **sky130 1.8 V에서 이 입력단은 pfet 최단 bin(L 0.15, VSG 0.80)과
  nmos 약반전에서만 DC가 성립**하고 창 하한이 ~0.79 V다. (세션43 "M1a+M4a VDS 합만으로 VDD 초과" 기록과 같은 방향.)
  논문 0.18 µm 결과 창은 0.32 V.
- SC 응용에서 입력 공통모드는 기준 스위치로 정해지는 **한 점**(SP-2)이고 폐루프 가상접지라 신호 진폭은 작다 → 요구는 폭이 아니라
  **포함**: V_icm ∈ [Vin,min + tol, Vin,max − tol].

### 2.5 제안
- metric 교체: `mismatch_sigma_mv`(옛 정의) → `offset_in_sigma_mv`(§1, M8/M17·M10/M19 포함, A_eff).
- **값 기본안 = (B)**: 5 mV 제약 삭제, offset은 출력 스윙 제약 안에서 소모분으로만 판정(아래 스윙 제약식). 근거: 선언 목적(ε_d 이득 정확도,
  정착)이 offset을 요구하지 않고, (A)는 수학적으로 불가능. 대가: 면적 하한이 사라진다 → 입력 면적은 잡음 제안(§2.5 A, flicker)이 지킨다
  (잡음 스펙을 안 넣으면 입력쌍이 최소 크기로 갈 수 있다 -- §12-2).
- 대안 (C) σ ≤ 3.3 mV(식 = β 가정과 일관된 하한, 값은 엔진 계산) / (D) 5 mV 유지(사용자 시스템 값으로 명시 채택 시).
- `offset_sys_mv ≤ value_from_constraint: offset_in_sigma_mv` 유지(기본안 B에서는 참조 대상이 없어지므로 B 채택 시 계통 offset도
  스윙 소모식으로 옮긴다).
- **스윙**: 출력마다 [Voc − V_FS/4 − 3σ_out,dm/2 − 3σ_CM, Voc + V_FS/4 + ...] ⊂ [V_lo, V_hi](`swing_out_v`). V_FS = 2.4 V(논문 스펙,
  잡음 제안 §12-3과 같은 채택 대기), 3 = 양측 99.73 % 관례(사용자 확인). Voc = Voc_des(M39/M40이 정함).
- **ICMR**: `icm_margin_v ≥ 0`(SP-2 값이 창 안). SP-2 기본안(창 중앙)이 이 창을 쓰게 하면 된다. 창이 L 0.15 µm에서만 열린다는 것은 **엔진 탐색
  공간(L 하한·bin)에 대한 구조 경고**로 보고한다.
- 신뢰도: 구조식 높음, 수치(창 폭)는 W 5 µm 한 슬라이스·bulk = 레일 가정이라 중간 → SPICE DC 스윕 확인 필요.

---

## 3. two_stage_ota (Maloberti p.28-33) -- 값 있음(5 mV, 근거 없음)

1. 출처: Maloberti 레이아웃 강의 예제 -- offset·스윙·ICMR **미보고**(잡음 문서와 같은 판단, 원문 이번 미확보).
   선언: gain ≥ 57 dB, GBW 7 MHz(사용자 결정 2026-08-13), CL 3 pF.
2. offset: diff_pair {M1, M2}(nmos) + 차동쌍 drain(D3/O1)에 붙은 mirror {M3, M4}(pmos). 꼬리 {M5, M7}(외부 bias) 공통모드, M6/M7은 A1로 나뉨.
   σ²_in = σ²_12 + (gm3/gm1)²·σ²_34. 계통 offset = M3/M4 VDS 차(VDS4 = VSG6로 KVL 고정) → 옛 mirror_ratio_error가 본 바로 그것.
   예시(값 아님): 입력 gm/ID 15·L 0.5(A 7.1), 부하 gm/ID 10·L 1(A 9.1), gm3/gm1 = 0.67 → σ² = 50.6/WL1 + 36.5/WL3.
   σ ≤ 5 mV(같은 WL)면 **WL ≥ 3.5 µm²**. 옛 식(n vth0만)은 WL1 ≥ 0.91 µm²로 통과시키는데 그 크기의 실제 σ는 9.3 mV.
3. 스윙: OUT ∈ [VDSAT7, VDD − VSDsat6] → **1.45–1.60 V p-p**(gm/ID 10–15, L 0.5–1). ICMR: Vin,min = VGS1(VS) + VDSAT5 = 0.83–0.99,
   Vin,max = VDD − VSG3 + VGS1 − VDSAT1 = 1.20–1.50 → **폭 0.2–0.67 V**(부하 pmos의 큰 VSG가 위쪽을 깎는다).
4. 제안: metric 교체(`offset_in_sigma_mv`). 값은 **출처·응용이 없어 유도 불가** → 기본안 = 보고 + 구조 가드 `offset_excess ≤ √2`
   (부하 기여 분산 ≤ 입력쌍 분산 -- 잡음 제안 §12-4와 같은 등분 원칙; 부하 gm/ID를 낮추는 방향). 5 mV는 사용자가 시스템 값으로 채택할
   때만 유지(현재는 파일럿 자리값 복제). 스윙·ICMR 보고(입력 DC SP-2 정해지면 `icm_margin_v ≥ 0`). 신뢰도 중간.

## 4. two_stage_ota_sf (Allen L26 p.26-5) -- 값 있음(two_stage_ota 참조)

1. 출처(PDF 재확인, aicdesign lecture26): p.26-5는 회로·전력·이득식만, p.26-3 class A 팔로워 "**Maximum upper output voltage is limited**".
   offset·ICMR 수치 없음.
2. offset: two_stage_ota와 같음(팔로워 M8/M9는 A1·A2로 나뉨). `value_from_file` 상속 유지.
3. 스윙: vout = OUT − VGS8(VSB = vout) → vout,max = VDD − VSDsat6 − VGS8 ≈ 1.8 − (0.10–0.18) − (0.86–0.94) = **0.68–0.84 V**,
   vout,min = VDSAT9 = 0.10–0.17 → **0.5–0.75 V p-p**(강의의 '상한 제한'이 sky130에서 수치로). ICMR = two_stage_ota.
4. 제안: two_stage_ota 결정을 상속. 스윙 보고.

## 5. folded_cascode (Maloberti p.34-38) -- 값 없음

1. 출처: 미보고.
2. offset: diff_pair {M1, M2}(nmos) + 접힘 노드 X/Y의 consumer_symmetric {M3, M4}(pmos, 보통 입력보다 큰 전류) + mirror {M9, M10}(nmos).
   캐스코드 {M5, M6}·{M7, M8} 무시, 꼬리 M11(tail_ratio {M11, MN}) 공통모드.
   σ²_in = σ²_12 + (gm3/gm1)²σ²_34 + (gm9/gm1)²σ²_910. 예시(I3 = 2·I1, 부하 gm/ID 10, L 1): 50.6/WL1 + **146**/WL3 + 17.9/WL9 → **전류원이 지배**.
3. 스윙: out,max = VDD − VSDsat3 − VSDsat6, out,min = VGS9 + VDSAT8(단순 캐스코드 미러: M7 diode가 M9 diode 위) → **0.48–0.82 V p-p**
   (wide-swing 미러가 아니라 VT 하나를 잃는다). ICMR: Vin,min = VGS1 + VDSAT11 = 0.83–0.99, Vin,max는 VDD를 넘어 레일로 잘림 → [~0.9, 1.8].
4. 제안: 보고 + 선택 가드 `offset_excess ≤ √2`. 신뢰도 중간(전류비 미정).

## 6. ngcc_3stage_ff (Lee et al., JSTS 2007) -- 값 있음(ICMR ≥ 0.6 V)

1. 출처(이관 기록 `_paper_target_spec`): **ICMR ≥ VDD/3**(논문 1.2 V 기준 0.4 V → 사용자 확정 1.8 V 기준 0.6 V), Table 4 설계 예 VDSAT 0.08 V,
   gm1 105 µS·ID1 4.2 µA(gm/ID 25). offset·출력 스윙 수치 없음(원문 재확보 실패는 잡음 문서와 같음).
2. offset: diff_pair {M1, M2}(**pmos**, 꼬리 M0) + 부하 {M3, M4}(nmos, J-U4 그룹에는 M6B 포함 -- M6B는 피드포워드 탭이라 offset 기여는
   뒷단 이득으로 나뉨). σ²_in = σ²_12 + (gm3/gm1)²σ²_34. 예시(입력 gm/ID 15·L 0.5 A 11.3, 부하 gm/ID 10·L 1 A 6.3, 0.67) =
   126.6/WL1 + 17.9/WL3 → **입력 pmos가 지배**(sky130 pfet 정합이 nfet의 1.5–2배 나쁨). {M8, M14}(ratified, gm14 = gm8 조건) 오차는
   offset보다 NGCC 영점 상쇄 문제.
3. ICMR(값이 있는 회로 -- 구조로 **구속**): Vin,max = VDD − VSDsat0 − VSG1(VS ≈ 0.1–0.2); Vin,min = VGS3 + VSDsat1 − VSG1 < 0 → 하단 레일 0으로
   잘림 → 폭 = Vin,max. ≥ 0.6 V 조건 ⇔ **VSG1 + VSDsat0 ≤ 1.2 V**. LUT: 입력 gm/ID 15·L 0.5(VSG ≈ 1.07) + 꼬리 gm/ID 15(0.099) → 0.63 V
   (여유 0.03 V); 꼬리 gm/ID 10(0.176)이면 0.55 V 불합격; 입력 L 0.18(VSG ≈ 0.86)이면 0.84 V. → **ICMR 제약이 입력 L bin·꼬리 gm/ID를 실제로
   구속**한다(새 숫자 없이 선언값이 일한다). 출력: Vout ∈ [VDSAT13, VDD − VSDsat12] → 1.45–1.60 V p-p.
4. 제안: 기존 ICMR ≥ 0.6 V를 `icmr_v`(폭, 레일로 자름)로 이름 부여 -- 값 변경 없음. 정의 확인 필요(§12-4: 폭인가, 특정 중심 포함인가;
   레일 밖 입력 허용 여부). offset은 보고 + 선택 가드. 신뢰도: ICMR 식 높음, 수치 중간.

## 7. nmcnr_amplifier (Leung, Mok, Ki 1999) -- 값 없음(앵커 있음)

1. 출처(이관 기록): Table 1 측정 조건 "**measured at unity-feedback configuration with 0.5V step input**", SR±·Ts±, 전원 ±1 V(AMS 0.8 µm).
   offset·ICMR·스윙 수치 없음. 단위 이득 팔로워에서 0.5 V 계단을 정착시켰다 = **입력 공통모드와 출력이 같은 0.5 V 범위를 선형으로 지난다**는
   것이 원문이 보인 사용 조건(앵커).
2. offset: diff_pair {M102, M103}(pmos) + 접힘 노드 F1/F2의 mirror {M104, M105}(nmos, 외부 VB2, **I_104 = I_1 + I_fold > I_1**) + mirror
   {M108, M109}(pmos). 캐스코드 {M106, M107} 무시. 예시(I104 = 2·I1, 부하 gm/ID 10·L 1): 126.6/WL1 + 71.7/WL104 + 36.5/WL108.
3. 스윙·ICMR(±0.9 V): Vin,max = vdd − VSDsat101 − VSG102 = 0.9 − (0.10–0.18) − (1.06–1.20) = **−0.26 ~ −0.48 V**(L ≥ 0.5); L 0.18 입력이면
   ≈ −0.06 V. Vin,min은 vss 아래 → −0.9로 잘림. → 창 [−0.9, −0.26…−0.48], 폭 0.42–0.64 V. **입력 DC 0 V(agnd 관례)는 창 밖**(SP-2 대기,
   발견 5). 출력 Vout ∈ [vss + VDSAT301, vdd − VSDsat302] → 1.45–1.60 V p-p.
4. 제안: (i) `icmr_v ≥ 0.5 V`와 `swing_out_v ⊇ 같은 0.5 V 구간`(팔로워 동작 구간이 입력 창·출력 범위 양쪽 안) -- 원문 측정 조건 앵커, 값은
   원문 절대값 그대로(ngcc처럼 원문이 VDD 비율로 준 것이 아니라 변환 규칙을 새로 만들지 않음; 레일 폭 비율 0.45 V로 바꿀지는 §12-4).
   (ii) SP-2: 입력 DC는 이 창 안이어야 하고 0 V는 L ≥ 0.5 µm 입력에서 불가능. offset 보고. 신뢰도: 식 높음, 수치 중간.

## 8. sf_pushpull_output_opamp (Allen L26 p.26-6, Fig. 7.1-1) -- 값 없음(입력 DC 선언 있음)

1. 출처(PDF 재확인): 도면 스펙 Rout ≤ 1 kΩ, Av(0) 65 dB, GB 60 MHz(CL 1 pF), IBias 50 µA. offset·스윙·ICMR 수치 없음. p.26-6
   "the bias currents through M18 and M19 vary with the signal". 선언 입력 DC = agnd 0.9 V.
2. offset: diff_pair {M1, M2}(nmos, 꼬리 M3 tail_ratio) + 자기 바이어스 캐스코드 부하. 차동 대응 짝인 M6↔M8, M5↔M7은 J-U4에서 **서로 다른
   gate 묶음**(N5: {M6, M9, M17}, N7: {M8, M11})이라 대칭쌍 그룹이 없다(J-U4 판단 3 대기) → 레이아웃 정합 근거가 없는 상태. MNA offset은
   그룹과 무관하게 계산되지만, 정합 레이아웃 대상 확정이 필요.
3. ICMR: Vin,min = VGS1(VS ≈ 0.1–0.17) + VDSAT3 = 0.83–0.99 V → **선언 입력 DC 0.9 V가 하한에 걸린다**(입력 gm/ID ≥ ~15, 꼬리 VDSAT ≤ ~0.12
   일 때만 포함). **출력 버퍼(발견 6, 중요)**: Y → M18(p)/M19(n) 팔로워 → M22(n)/M21(p) 팔로워. 버퍼가 DC로 성립할 창
   Y ∈ [VGS19 + VDSAT20, VDD − VSDsat17 − VSG18], 폭 = VDD − VGS_n − VSG_p − VDSAT_n − VDSAT_p. LUT(팔로워 VDS 1.65 V·VS 0.2 V):
   L 0.15 gm/ID 15 **+0.11 V**, L 0.18 −0.12, L 0.5 −0.32 V(gm/ID 10이면 더 음). 출력 팔로워 vout 범위(최단 bin, gm/ID 15): bulk = 레일
   **−0.08 V**(dead zone), bulk = 소스 +0.22 V. → 1.8 V·sky130에서는 4-팔로워 출력단이 거의 스윙이 없다. 강의의 "limited"가 여기서는
   실현가능성 문제다.
4. 제안: 스펙 값은 넣지 않는다(출처 없음). 대신 **실현가능성 metric 2개를 보고**: `icm_margin_v`(0.9 V 포함 여부), 버퍼 창 폭(위). 사용자 판단
   필요: bulk 연결(pfet 소스 묶음 n-well 허용?), 소자 bin, 전원(§12-6). 신뢰도: 구조식 높음, 수치 중간(정지 전류·body 가정).

## 9. pushpull_follower_buffer (Allen L26 p.26-4) -- 값 없음(입력 DC 선언 있음)

1. 출처(PDF 재확인): p.26-4 "**Maximum positive and negative output voltages are limited**", Rout ≈ 0.5/(gm+gmbs) 250–500 Ω, KVL
   "VGS4 + VSG3 = VGS1 + VSG2"(전류 정의). 수치 스윙 없음. 선언 vin DC = agnd 0.9 V, Rout ≤ 1 kΩ.
2. offset: 차동쌍 없음. vout − vin(레벨 시프트 차)는 계통값이고, 랜덤 오차는 정지 전류(I1/I2) 산포로 주로 나타난다 → offset 스펙 무의미.
   정지 전류 산포는 `mirror_ratio_sigma_pct`와 같은 식(gm/ID·σ_ΔVGS)으로 보고 가능.
3. vin 창 = [VDSAT6 + VGS4, VDD − VSDsat5 − VSG3] -- §8의 버퍼와 **같은 식, 같은 수치**(L 0.15에서만 +0.11 V, 0.9 V 포함은 그 창 안에서만).
   출력 vout ∈ [VDSAT6 + VSG2, VDD − VSDsat5 − VGS1](M1·M2 각자 한쪽 방향 구동) → bulk = 레일이면 음수.
4. 제안: 스펙 없음. 실현가능성 보고(창 폭, `icm_margin_v`). Rout ≤ 1 kΩ(gm1 + gm2 ≥ 1 mS)는 전류를 키워 gm/ID를 낮추므로 창과 충돌한다 →
   두 선언(Rout, vin 0.9 V)을 동시에 만족하는 설계가 있는지가 첫 확인 대상.

## 10. common_gate_amplifier (Allen L20 p.20-2) -- 값 없음

1. 출처(PDF 재확인): "Large Signal Characteristics: **VOUT(max) ≈ VDD − VDS3(sat), VOUT(min) ≈ VDS1(sat) + VDS2(sat)**, Note VDS1(sat) = VON1"
   -- 식만, 수치 없음. offset 없음.
2. offset: 단일 입력·차동쌍 없음 → 무의미(J-U4 그룹 0).
3. 스윙: 출처 식 그대로 VDD − VDSAT3 − VDSAT1 − VDSAT2 = **1.26–1.50 V p-p**(gm/ID 10–15). 입력 vin = M1 drain ≥ VDSAT1, 위는 M2 포화
   (VNBias2 − VGS2) → 입력 DC는 SP-2 기본안(PENDING SP-2: M1 VDS(sat) 하한과 M2·M3 헤드룸에서 유도)과 같은 식.
4. 제안: 스펙 없음, 스윙 보고(출처 식이 `swing_out_v` 정의와 같음 → 엔진 결과를 이 식으로 대조 가능).

---

## 11. 요약표

| 회로 | metric | 제안 값 | 근거 | 신뢰도 |
|---|---|---|---|---|
| current_reuse (파일럿) | `offset_in_sigma_mv`(M8/M17·M10/M19 포함, A_eff) | **기본 B: 독립 상한 없음, 스윙식에서 소모분으로 판정** / C: ≤ 3.3 mV(β 가정 일관 하한, 엔진 계산) / D: 5 mV 유지 | ε_d는 offset 무관, ½ LSB(A)는 해 없음(증명), 논문 offset 미보고 | 구조 높음 |
| current_reuse | `swing_out_v` | 출력마다 Voc ± V_FS/4 + offset 소모 ⊂ [V_lo, V_hi], V_FS 2.4 V(채택 대기) | Table I 스펙 ±1.2 V, 달성 추정 ±1.66–1.72(논문 ±1.706) | 높음 |
| current_reuse | `icm_margin_v` | ≥ 0(SP-2 V_icm이 창 안) | 창 = VDD − VGS4 − VSG1 − VDSAT5 − VSDsat6, sky130 ≤ +0.14 V(L 0.15만) | 식 높음, 수치 중간 |
| two_stage_ota | `offset_in_sigma_mv` | 5 mV는 근거 없음 → 보고 + 선택 가드 offset_excess ≤ √2 / 사용자가 시스템 값 채택 시 유지 | 출처·응용 없음 | 중간 |
| two_stage_ota_sf | 상속 | two_stage_ota 결정 상속, 스윙 보고(0.5–0.75 V p-p) | 강의 '상한 제한' | 중간 |
| folded_cascode | 보고 | 제약 없음(+선택 가드) | 출처 없음, 전류원 지배 | 중간 |
| ngcc_3stage_ff | `icmr_v` | **≥ 0.6 V 유지(값 불변, 이름만)**; offset 보고 | 논문 VDD/3, 사용자 확정; 입력 L·꼬리 gm/ID를 구속 | 식 높음 |
| nmcnr_amplifier | `icmr_v`, `swing_out_v` | 후보: ≥ 0.5 V(원문 단위 이득 0.5 V 계단 앵커) | Table 1 측정 조건; 입력 DC 0 V는 창 밖 | 중간 |
| sf_pushpull_output_opamp | 실현가능성 보고 | 값 없음; `icm_margin_v`(0.9 V), 버퍼 창 폭 보고 | 0.9 V가 Vin,min에 걸림, 4-팔로워 창 ≈ 0 | 구조 높음 |
| pushpull_follower_buffer | 실현가능성 보고 | 값 없음 | 같은 창 식, Rout 선언과 충돌 가능 | 구조 높음 |
| common_gate_amplifier | 보고 | 값 없음 | 출처 식 = 스윙 정의 | 높음 |
| 전 회로 | `offset_sys_mv` | ≤ value_from_constraint `offset_in_sigma_mv`(그 제약이 있는 회로만) | 기존 "계통 ≤ 랜덤" 규칙 유지 | -- |
| 전 회로 | `mirror_ratio_sigma_pct` | 보고 | 전류 산포 | -- |

---

## 12. 사용자 판단이 필요한 항목

1. **mismatch 모델 범위(엔진·LUT 변경)**: vth0만(옛) vs PDK mismatch 블록 전 파라미터(toxe·voff·nfactor 포함, 0.3). 후자는 LUT 생성기에
   감도 열 추가 + 엔진 σ_VGS 계산 card가 필요하다. 옛 식은 1.2–2.4배 과소평가하고 pfet L < 0.5 µm slope도 틀렸다(발견 1·2).
2. **파일럿 offset 값: B(독립 상한 없음, 스윙 소모로만) / C(≤ 3.3 mV, β 가정 일관) / D(5 mV 유지)**. B를 고르면 입력 면적을 지키는 제약이
   잡음(flicker) 하나만 남는다 -- 잡음 스펙을 안 넣으면(DEC-96) 입력쌍이 최소 크기로 갈 수 있다. 정적 정확도(½ LSB)가 시스템에 필요하면
   offset 제거(CDS) = 클럭·위상 구조 결정이 먼저다(A는 이 Cf/Cs로 해 없음).
3. **two_stage_ota·two_stage_ota_sf 5 mV**: 근거 없는 복제값. 시스템 값으로 명시 채택 / 삭제하고 보고 + 가드(offset_excess ≤ √2) 중 선택.
   가드 기준 '부하 분산 ≤ 입력 분산'은 잡음 제안 §12-4와 같은 등분 원칙이며 함께 결정하면 일관된다.
4. **ICMR 정의**: (a) 폭인가, 선언 입력 DC 포함인가(SC 파일럿은 포함), (b) 레일 밖 입력 허용 여부(제안: 레일로 자름), (c) nmcnr 앵커
   0.5 V를 원문 절대값으로 쓸지 레일 폭 비율(1.8/2.0 → 0.45 V)로 바꿀지, (d) 3σ(양측 99.73 %) 관례 사용 여부.
5. **스윙 정의**: 모든 MOS VDS ≥ VDSAT + tol_vdsat(사용자 SPICE 포화 규칙 + LUT 허용오차, 새 숫자 0) vs 소신호 이득 ≥ 그 회로 gain 제약
   (논문 Fig. 10 방식, 역시 새 숫자 0). 파일럿 V_FS(±1.2 V 논문 스펙) 채택 -- 잡음 제안 §12-3과 같은 질문이다.
6. **헤드룸 실현가능성 경고(발견 4·5·6)**: (a) 파일럿 current-reuse 입력 창은 pfet L 0.15 µm bin에서만 열린다, (b) nmcnr 입력 DC 0 V 불가
   (L ≥ 0.5 µm), (c) sf_pushpull·pushpull 버퍼의 4-팔로워 스택은 1.8 V에서 거의 성립하지 않는다(bulk = 레일이면 dead zone). 모두 topology의
   bulk(`b` = None) 가정에 민감하다 → bulk 연결 선언(pfet 소스-묶음 n-well 허용 여부)과 SP-2(입력 DC)를 먼저 정해야 한다.
7. **J-U4 그룹과 offset**: sf_pushpull의 차동 대응 짝 M6↔M8·M5↔M7이 정합 그룹이 아니다(판단 3). 파일럿 {M8, M17}·{M10, M19}는 offset에
   38 % 규모로 기여하므로 consumer_symmetric 그룹(ratified)이 레이아웃 정합 대상이라는 점이 offset에서도 확인된다.
8. **검증 필요(가정 대신 실측)**: (a) 파일럿 ngspice Monte-Carlo(mismatch 블록 변수를 소자마다 gauss로) 입력 offset 분포 vs `offset_in_sigma_mv`
   MNA 값, (b) W 의존(이번 W 5 µm만), (c) 4-팔로워·current-reuse 창의 SPICE DC 스윕.

## 부록: 재현
- PDK slope·bin 집계: `mm/bins.py`(pm3 카드 `.model` 블록마다 lmin/lmax/wmin/wmax와 사용 slope 이름).
- 감도 실측: `mm/mm.py`(ngspice_con -b, `.save @m.xN.msky130_fd_pr__<dev>[id]`, dc vg 0→±1.8 V 1 mV, |VDS| 0.9 V, W 5 µm, L 0.15–4 µm),
  결과 `mm/mm_result.json`. 분해는 같은 json에서 gm/ID 5–12 선형 적합.
- LUT 값: `mm/lutv.py`(VGS·VDSAT), `mm/win.py`(파일럿 창), `mm/buf.py`(팔로워 출력), CGG는 같은 npz. 경로 모두 세션 스크래치
  `.../scratchpad/mm/`, 저장소 미변경.
- 출처 PDF: 파일럿 로컬 원본(pdftotext), Allen lecture20·26(aicdesign.org에서 스크래치로 내려받아 pdftotext).
