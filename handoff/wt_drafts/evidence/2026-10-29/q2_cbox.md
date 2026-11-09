# 묶음 Ⅱ 권고 전 실측 -- θ 커패시터 상자 '10번'·Q-CB1·Q-CB2·DEC-79 (a)

작성: 실측 agent(읽기·측정만, 문서·데이터·git 쓰기 0). 2026-10-29. 저장소 기준 chip-design-skills `dea19cb7`, 계획 `wt/plan-v6385` `45a31ff1`.
스크립트·출력: `wt/_drafts/evidence/2026-10-29/q2_cbox/`
- `m1_spec_census.py`→`.txt`: 13 spec 수동소자·면적 제약·θ 상자 전수
- `m2_pdk_mim.py`→`.txt`: PDK 파일에서 camimc·cpmimc 파싱, 최소 MIM 용량, 면적 예산 C 상한
- `m3_comp_toy.py`→`.txt`: 보상 C 하한 결정자, 합성 2단 Miller toy(소신호 MNA 정확해)
- `m4_coupling_toy.py`→`.txt`: 결합 C 결정자 α, 합성 sky130 toy(ngspice `.tran`). deck·log는 `m4_runs/`
- `m5_coupling_handcalc.py`→`.txt`: m4 경계를 정지 곡선(LUT 꼴)만으로 손계산해 대조

엔진 코드 인용은 두 용도뿐이다. 엔진 밖 사실을 대거나, 재작성 범위를 적는 데만 쓴다. 자리·writer·판정의 근거로 쓰지 않았다.

## 판정 요약

| # | 질문 | 판정 | 확신도 |
|---|---|---|---|
| 1 | 최소 MIM 용량을 PDK 선언에서 유도할 수 있나 | **조건부**. 단위 용량은 로컬에 있다(camimc·cpmimc). 최소 폭(capm.1)은 **로컬 원본이 N/A**다. 원격 open_pdks magic tech에는 capm.1 = 1.000 µm가 있다. 그 값을 쓰면 C_min = 2.76 fF(tt)이고, 모서리별로 1.90~3.63 fF다. 로컬 PDK 원본을 더해야 원칙 11을 충족한다 | 상 |
| 2 | 보상 C 하한의 물리 결정자 | **PM 목표다**(+ gm 비 + 선언 CL). 최소 MIM은 PM 목표가 있으면 묶이지 않는다(toy에서 Cc_min/C_min_MIM = 115~1214배). 하한이 결정을 바꾸는 경우는 PM 행이 비활성일 때뿐이다. 그때 실현 가능한 최솟값 = 최소 MIM이 물리 하한이다(E-0 실현 가능). 마디 기생은 하한이 아니다. 하한 근처에서 MNA 모델 오차(E-1)를 키우는 양이다 | 상(toy)·중(13회로 적용) |
| 3 | 13 spec 면적 선언·제약 | 수동소자는 모두 값이 있다(선언값 또는 θ). 값 미정은 **0/13**이다. PDK 단위 면적(C·R)은 이미 선언돼 있다. 면적 제약 `area_search_m2`가 있는 회로는 **9/13**이다(library 9, heldout 0). STEP2 N7의 'PM 없는 3회로'는 **낡았다**(2026-10-13 측정, 2026-10-14에 세 회로 모두 PM ≥ 70 선언) | 상 |
| 4 | 결합 C 하한 결정자 α·SR | α = C/(C+C_g,eff)와 출력 전류 요구가 결정자다. **합성 toy로 보일 수 있다**(held-out 불필요). 단일 결합 toy에서는 손계산(정지 Id·전하 평균 cgg)이 실측 경계 안 또는 바로 옆에 든다(3건 중 2건 안, 1건 −2 %). erfc 같은 사슬 결합에서는 손계산이 성립하지 않는다(cbox c2·c4). 원문 p.7 §3.1은 둘째 결정자로 R_L·C_BAT 저역 차단을 든다 | 중상 |
| 5 | DEC-79 (a) '면적 미선언 = 0' | 계획 278행 DEC-79 (a)와 679행에 있다. 같은 278행 안에서 U-36 '확정'(C 면적 = 값/camimc)과 모순된다. "(현재 library 회로에는 선언이 없다 -- 실측)"은 낡은 문언이다. E-12(2317행)는 '정의 불능, 0으로 메우지 않음'이라 충돌한다. N5.4 1171행도 같은 문언 계열이다 | 상 |

## 1. sky130 MIM 선언값과 최소 MIM 용량

| 양 | 값 | 출처(경로:행) | 로컬 여부 |
|---|---|---|---|
| camimc (tt) | 2.00e-15 F/µm² | `C:/pdk/sky130_fd_pr/models/r+c/res_typical__cap_typical__lin.spice:7` | 로컬 |
| cpmimc (tt) | 0.19e-15 F/µm | 같은 파일 `:8` | 로컬 |
| camimc / cpmimc (cap_high) | 2.231e-15 / 0.35e-15 | `res_high__cap_high__lin.spice:7-8`(`res_low__cap_high` 같음) | 로컬 |
| camimc / cpmimc (cap_low) | 1.778e-15 / 0.03e-15 | `res_high__cap_low__lin.spice:7-8` | 로컬 |
| 엔진 PDK 선언 | `mim_cap_density_f_per_m2` = camimc | `skills/analog-gmid-design/assets/sky130_pdk_decl.json:46-54, 93-97` | 저장소 |
| capm.1 최소 폭 | **N/A** | `C:/pdk/skywater-pdk/docs/rules/periphery/periphery.csv:745`(capm.1~12 모두 N/A, 742-756). 원격 upstream `periphery-rules.rst`도 N/A(WebFetch 확인) | 로컬 = 값 없음 |
| capm.1 최소 폭 (원격) | `width *mimcap 1000 "MiM cap width < %d (capm.1)"` = 1.000 µm. 같은 줄 무리에 capm.2a 0.84·capm.3 0.14·capm.11 1.34 µm가 있다 | https://github.com/RTimothyEdwards/open_pdks/blob/master/sky130/magic/sky130.tech (DRC 절, magic 단위 nm) | **로컬 없음** |
| 용량 식 | `carea = camimc*wc*lc`, `cperim = cpmimc*(wc+lc)*2` | 원격 `skywater-pdk-libs-sky130_fd_pr/cells/cap_mim_m3/sky130_fd_pr__cap_mim_m3_1.model.spice`. 로컬 `models/capacitors/sky130_fd_pr__model__cap_mim.model.spice:16`이 include하지만 셀 파일은 로컬에 없다 | 로컬 없음 |
| capm.12 최대 면적 | 값 없음(로컬·원격 rst N/A, magic tech에 행 없음) | -- | -- |

**유도식**: C_min = camimc·w_min² + cpmimc·4·w_min (정사각 1개, MF = 1). 숫자는 규칙에 박지 않고 위 두 선언에서 계산한다. 결과는 m2이며 아래 표와 같다.

| 모서리 | C_min | 둘레 항 몫 |
|---|---|---|
| tt | **2.760 fF** | 28 % |
| cap_low | 1.898 fF | 6 % |
| cap_high | 3.631 fF | 39 % |

- '10번' 하한 0.1 pF는 C_min(tt)의 **36배**다. 0.1 pF는 정사각 6.88 µm, 47.4 µm²다.
- 실제 sky130 설계 cnr_ota C1·C2가 53.8 fF(5×5 µm)다. 0.1 pF가 PDK 최소가 아니라는 점은 두 출처에서 일치한다.
- **정의 차이 ⚠**: 엔진 면적 모델(U-36, DEC-79)은 면적 = C/camimc로 둘레 항을 뺀다.
  - 최소 MIM에서 그 면적은 1.38 µm²이고, 실제 1.00 µm²보다 +38 % 크다.
  - 0.1 pF에서는 +5.5 %다.
  - 하한을 PDK 최소 MIM으로 내리면 면적 축 정의(둘레 항 포함 여부)도 같은 변경에서 한 정의로 맞춰야 한다(같은 양 = 필드 하나).
- **엔진 재작성 범위**(근거 아님):
  - `gmid_engine/search/search_domain.py:114` 주석과 `gmid_engine/sizing/CONTRACT.md:903-910` O13은 "capm.* N/A → PDK에서 유도 불가"라고 적고 있다.
  - 로컬 원본 기준으로는 지금도 사실이다. 원격 원본을 로컬 PDK 보관소에 들이면 낡은 문언이 된다.

**착수 조건(원칙 11)**: open_pdks `sky130.tech`(또는 같은 값을 담은 KLayout DRC deck)와 `cap_mim_m3_1.model.spice`를 `C:/pdk/` 아래에 PROVENANCE(커밋·sha256)와 함께 두어야 한다. 그다음 `sky130_pdk_decl.json`에 `capm.1` 출처 항목을 더한다. 이것은 사용자 승인이 필요한 data·PDK 선언 변경이다. 그 전까지는 "PDK 최소 MIM" 하한이 **원격 사실**일 뿐 로컬 선언이 아니다.

## 2. 보상 C 하한의 물리 결정자 (m3 합성 toy, held-out 미사용)

2단 Miller toy를 썼다: 이상 gm, R1·C1(마디 기생)·R2·CL, Cc(+ Rz = 0 또는 1/gm2). PM 목표는 70°다.

| 경우 | Cc_min(PM ≥ 70) | 손 tan(PM)·gm1/gm2·CL | Cc = C_min_MIM일 때 PM | Cc = 0.1 pF일 때 PM | Cc_min / C_min_MIM | Cc_min / C1 |
|---|---|---|---|---|---|---|
| A (CL 1 pF) | 0.447 pF (Rz = 1/gm2: 0.316) | 0.275 pF | 3.2° | 40~43° | 162 (115) | 8.9 |
| B (CL 3 pF) | 1.26 pF (0.891) | 0.824 pF | 2.1° | 22~23° | 456 (323) | 12.6 |
| C (CL 20 pF) | 3.35 pF (2.82) | 2.75 pF | 1.9° | 11° | 1214 (1021) | 16.7 |

- PM은 Cc에 단조다(세 경우 모두 확인). **Cc 하한을 정하는 것은 PM 목표·gm 비·CL**이다. PM 행이 살아 있으면 상자 하한(0.1 pF이든 2.76 fF이든)은 결정에 닿지 않는다.
- 상자 하한이 설계값이 되는 경우는 두 가지다.
  - (i) PM 목표가 없을 때. 이때는 spec 빈칸의 문제다.
  - (ii) PM을 만족하면서 면적·전력 목적이 Cc를 상자 하한 아래로 밀 때. ngcc Cm2 0.1 pF(STEP2 N7, 2026-10-13 측정)가 이 경우다.
  - (ii)에서 0.1 pF는 **관례값으로 실현 가능한 해를 잘라낸다**. 물리 하한은 실현 가능한 최솟값 = 최소 MIM이다(E-0 '실현 가능' 관문).
- **마디 기생을 하한으로 쓰는 안 ⚠**: 탐색 상자를 탐색 결과(θ 의존 MNA 양)로 정하는 순환이다. 그리고 같은 기생을 MNA와 상자 writer가 따로 내는 둘째 생산자다.
  - 물리적으로도 하한이 아니다. Cc < C_par여도 MNA가 PM을 판정한다.
  - 역할: Cc가 마디 기생과 같은 자릿수(fF)로 내려가면 MNA 기생 모델(Cgd·배선)의 오차가 판정을 좌우한다. 그러면 E-1에 따라 oracle이 판정한다. 하한 결정자가 아니라 **e_m 관리 대상**이다.
- 비교 참고(근거 아님): cbox c4의 erfc 게이트 C_g,eff는 0.06~0.23 pF다. toy C1은 50~200 fF로 구성했다.

## 3. 13 spec 수동소자 면적 선언·제약 (m1)

| 회로 | area_search_m2 | θ C 상자 | 비고 |
|---|---|---|---|
| common_gate | 5e-9 | -- | 수동소자 없음 |
| current_reuse | 4e-8 | Cc1·Cc2 [0.1, 10] pF | Cf·Cs 선언 0.5 pF |
| folded_cascode | 1e-8 | -- | CL 측정 부하만 |
| ngcc | 2.5e-8 | Cm1·Cm2 [0.1, 10] | PM 63.4 |
| nmcnr | 2.5e-8 | Cm1·Cm2 [0.1, 10] | PM 70 |
| pushpull | 5e-9 | -- | -- |
| sf_pushpull | 2e-8 | Cc [0.1, 10] | PM 70(2026-10-14) |
| two_stage | 1.5e-8 | Cc [0.1, 10] | PM 70(2026-10-14) |
| two_stage_sf | 1.5e-8 | Cc [0.1, 10] | PM 70(2026-10-14) |
| cnr_ota (heldout) | **없음** | -- | C1·C2 53.8 fF 선언 |
| erfc_ota (heldout) | **없음** | CBAT1_L·CBAT1_R·CBAT2 **상자 미선언** | 지금 `search_domain`이 `theta_capacitance_bounds_undeclared`로 거부한다(fail-closed) |
| r2r (heldout) | **없음** | -- | CM1·CM2 2 pF 선언 |
| rfc (heldout) | **없음** | -- | -- |

- 값 미정 수동소자는 **0/13**이다. 측정 부하는 제외했다.
- PDK 단위 면적은 C(camimc)와 R(rp1·poly.3·머리 면적)에 이미 선언돼 있다(`sky130_pdk_decl.json` quantities).
- 그래서 지금 13회로에는 DEC-79 (a)의 '수동소자 면적 미선언' 갈래가 **발동하지 않는다(0/13)**.
- 면적 제약은 9/13이다. heldout 4/13은 면적 예산이 없어서 면적에서 C 상한을 유도할 수 없다.
- **면적 예산이 주는 C 상한**(m2, 면적 전부를 C에 줄 때의 느슨한 경계 = area × camimc): 10~80 pF다. θ C가 있는 6회로는 30~80 pF로, '10번' 상한 10 pF보다 3~8배 넓다.
  - 그러니 10 pF는 면적 제약보다 먼저 자르는 관례 상한이다.
  - 상한 결정자는 면적 제약(spec 선언, 9/13)이고, 그 판정은 이미 제약 행이 한다.
- **STEP2 N7 인용 확인**(`wt/_drafts/engine/STEP2_DESIGN_GAPS_DECISION_PACKAGE.md:94, 545-552, 642`):
  - 측정 기준은 master `3151392`(2026-10-13 19:10)이다.
  - 그 뒤 2026-10-14 Q-S2로 sf·two_stage·two_stage_sf에 `pm_ss_deg >= 70`이 선언됐다(spec `decided: 2026-10-14`).
  - → 계획 1167행 Q-CB2의 "PM 목표 없는 3회로 Cc"는 **낡은 사실**이다. 지금 하한 고착을 보인 기록은 ngcc Cm2 하나다(그것도 2026-10-13 엔진).
  - 둘 다 재측정이 필요하다(Q-CB2 상정 조건 'LA-1·ME-1 변화표'와 같은 자리).

## 4. 결합 C 하한 결정자 -- 손계산 식, 원문, toy로 보일 수 있나

**식**(원칙 4 θ 고정, 대신호 끝점 DC 양):
- α = ΔV_g/ΔV_x = C/(C + C_g,eff)
- 요구 출력 전류 ΔI_req = CL·SR_spec → V_GS,req = I_D^{-1}(I_0 + ΔI_req)(LUT) → α_req = (V_GS,req − V_B)/ΔV_x
- C_g,eff ≈ C̄_g = (1/ΔV_g)∫cgg dV_GS (V_B → V_GS,req, LUT 전하 평균)
- **C_min = α_req/(1 − α_req)·C̄_g**
- 둘째 결정자(원문): 고역 통과 R_L·C_BAT의 저역 차단이다. 계단 지속 시간 동안 게이트 전하가 유지돼야 한다. cbox c3에서 첫 edge 처짐은 2 % 미만이었고, 반복 계단 정류 표류는 cbox 2.5에 있다.

**원문**: Wu 외 2025, Sensors 25(8):2523, https://pmc.ncbi.nlm.nih.gov/articles/PMC12031453/
로컬 PDF: `chip-design-skills/skills/analog-gmid-design/assets/heldout/sources/erfc_ota__wu_2025/source.pdf`(텍스트 `paper.md`).
- p.3 §2.2(paper.md 184-186행): "coupling capacitors CBAT1 and CBAT2, along with the bias resistor RL, provide floating bias voltages for the gates of M5–M8" -- 목적 = 과도 응답 중 동작점 유지.
- p.7 §3.1 Fig.5(paper.md 338-352행): "The RLCBAT is often designed as larger to achieve a lower low cut-off frequency. The CBAT does not need to be excessively large, as the local positive feedback loop significantly enhances the large-signal response at VX,Y" -- 크기는 정성 기술뿐이고 p.9 Table 1에 값이 없다.

**toy로 보일 수 있나(m4·m5)**: library 9회로에는 결합 C가 없다(0/9, cbox c0). 그래서 library로는 보일 수 없고, **합성 toy로는 보일 수 있다**.
- toy 구성(spec 근거 아님): sky130 nfet W/L 20/0.3 µm, 게이트 V_B 0.55 V(R_b 1e12), 드레인 고정 0.9 V, 계단 ΔV_x 0.6 V.
- 실측 α는 C에 단조다. 0.01 → 100 pF에서 α 0.21 → 0.9996이고, ΔI_pk는 48 → 1947 µA다.
- C_g,eff(역산)는 37~42 fF로 거의 일정하다. 정지 cgg(V_B)는 24.6 fF로 **1.7배 과소**다.

| 요구(구성) | 실측 경계 | 손계산(정지 cgg(V_B)) | 손계산(전하 평균 C̄_g, LUT 꼴) |
|---|---|---|---|
| ΔI = 0.5·ΔI_max | (50, 100] fF | 52.5 fF (안) | 66.0 fF (안) |
| 0.8 | (200, 500] fF | 175 fF (FAIL 쪽) | 225 fF (안) |
| 0.9 | (500, 1000] fF | 378 fF (FAIL 쪽) | 489 fF (−2 %, 경계 바로 아래 -- 낙관) |

- 단일 결합에서 C_min을 정하는 것은 α와 I_D(V_GS)다. 손계산(LUT 정지 곡선, θ 고정)은 실측 경계 안에 들거나, 격자 분해능 안에서 경계 바로 옆이다.
- 정지 cgg 하나만 쓰면 낙관 쪽으로 틀린다(cbox의 erfc 1.45~2.9배 결과와 같은 방향).
- **erfc에 옮길 수 없는 이유**(cbox c2·c4): 사슬 결합(CBAT2가 n_m7d 스윙에 의존), Cgd Miller(움직이는 드레인), SR = edge 시간 평균, SR_∞ 여유 5~9 %. 그래서 엔진 손계산 행은 O-122와 충돌한다(cbox 2.4 (iii)).
- 결정자가 일반적이라는 것은 toy로 보일 수 있다. erfc 하한 **값**은 그 회로의 oracle 측정이 필요하다. held-out을 spec 조정에 쓰는 것은 원칙 16 ⚠이고 묶음 Ⅰ 답에 따른다.

## 5. DEC-79 (a)·E-12 문언 자리 (`wt/plan-v6385/docs/01-plan/features/gain-budget-gmid-sizing.plan.md`)

| 행 | 문언 | 상태 |
|---|---|---|
| 278 (DEC-79 (a)) | "수동소자 면적 선언이 없으면 그 항을 0으로 두고 '수동소자 면적 미선언'을 매 실행 보고한다(현재 library 회로에는 선언이 없다 -- 실측)" / "수동소자 면적 선언이 없으면 그 회로의 front는 … `review_needed`" / 같은 행 뒤쪽: "수동소자 면적 모델 … U-36이고 확정(2026-10-08): 커패시터 = 값 / `mim_cap_density_f_per_m2`" | **행 안 모순**: 앞은 '미선언 → 0', 뒤는 '확정'이다. "선언이 없다 -- 실측"은 2026-10-08 전 사실이다(m1: 미선언 0/13) |
| 679 (N5 면적 bullet) | "탐색 축 = `sum_area`(+ 선언 수동소자 면적, 미선언이면 0으로 두고 보고)" | 같은 문언 계열 |
| 1171 (N5.4) | "수동소자 면적이 선언되지 않았으면 그 사실을 명시한다(DEC-79)" | 보고 규칙. 0 채움은 아니다 |
| 2317 (N6.35 E-12) | "값 미정 소자가 있으면 그 점의 면적은 **정의 불능**(… 0으로 메우지 않음), head 면적 미선언도 같음" | DEC-79 (a)의 '0'과 **충돌** |
| 2439 (U-36) | "확정(2026-10-08) … 선언 전까지 … `review_needed`" | 확정 뒤 '선언 전까지' 갈래가 비어 있다 |
| 1166-1167 (Q-CB1·Q-CB2) | Q-CB2 "PM 목표 없는 3회로 Cc" | 낡은 사실(3절) |

## 6. 권고 점검 (원칙·graph)

- **graph 단일 정본**:
  - 보상 C 하한을 PDK에서 유도하면 writer는 PDK 선언 로더(core `pdk_decl` 양 하나, 예: capm.1 → 최소 MIM 용량)다. 상자 writer(S0 `search_domain` 블록 하나)가 그 양을 READS한다. 새 cache·사본은 0이다.
  - ⚠ spec `theta_bounds.min`(지금 9개 원소에 0.1 pF)과 PDK 유도 하한이 같은 원소의 하한을 둘이 내면 **둘째 생산자**다. 역할별 출처를 하나로 정해야 한다. 보상 C는 PDK 유도만 쓰고 spec 선언을 지우며, 결합 C는 spec 선언만 쓴다.
  - 상한을 area_search_m2 × camimc로 두면 이미 있는 면적 제약 행과 같은 입력이다. 상자 상한은 정의역일 뿐이고 판정은 제약 행 하나가 한다.
  - ⚠ 면적 제약이 없는 heldout 4/13은 상한이 정의되지 않는다. fail-closed 정지 또는 선언이 필요하다.
- **원칙 11**: capm.1 로컬 원본이 생기기 전에는 '최소 MIM'도 원격 사실이다. 로컬 PDK 보관소 추가(PROVENANCE)가 착수 조건이다.
- **원칙 16**: 결합 C 결정자는 합성 toy로 보일 수 있다(m4·m5). 그래서 '결정자·규칙'의 증거에는 held-out이 필요 없다. erfc '값'만 묶음 Ⅰ에 따른다.
- **원칙 2(E-0·E-1)**: 최소 MIM = E-0 '실현 가능' 관문이다. fF대 Cc의 PM 판정 정확도는 E-1(oracle 판정)이다.
- **DEC-79 (a)**: '면적 미선언 → 0'은 지금 13회로에서 발동 0이다. 문언만 E-12와 충돌한다. 정리안은 이렇다.
  - (a) 값 있는 수동소자 = PDK 선언 식으로 계산
  - (b) 값 미정 또는 PDK 밀도 미선언 소자 = 그 점 면적 정의 불능(E-12 한 규칙)
  - (c) "library 선언 없음 -- 실측" 문장 삭제. 이것은 계획 개정 몫이다.

## 7. 물리 검증 요약 (⑨)

| 항목 | 내용 |
|---|---|
| 물리 결정자 | 보상 C: PM(+ gm 비·CL). 하한 고착 시 물리 하한 = 최소 MIM(제조 실현 가능). 결합 C: α = C/(C + C̄_g)와 I_D(V_GS)·SR, 그리고 R_L·C 저역 차단 |
| 식/원문 | C_min,MIM = camimc·w² + 4·cpmimc·w. Cc_min ≈ tan(PM)·gm1/gm2·CL(toy 실측 비 1.2~1.6). C_min,coupling = α_req/(1 − α_req)·C̄_g. erfc 원문 p.3 §2.2, p.7 §3.1 |
| 실측 | PDK 파일 파싱(m2). 소신호 toy(m3). sky130 ngspice toy 11점 + 정지 곡선 121점(m4·m5) |
| 판정 | 보상 C 하한 '0.1 pF' = 관례(틀림, 물리 하한은 PDK 최소 MIM 2.76 fF -- 조건부: 로컬 원본 필요). 상한 10 pF = 관례(면적 제약이 결정자, 9/13). 결합 C 결정자 = 맞음(toy 일반성 확인, erfc 값은 oracle). DEC-79 (a) '0' = 틀림(E-12와 충돌, 발동 0/13) |
| 불확실 | capm.1이 원격 출처다. 둘레 항을 빼는 면적 정의 차이(+38 % at w_min). N7 하한 고착 사례는 2026-10-13 엔진 기준이라 재측정이 필요하다 |
