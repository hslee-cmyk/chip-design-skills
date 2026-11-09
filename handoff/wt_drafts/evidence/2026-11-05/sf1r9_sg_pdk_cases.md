# SF-1 범위 9 PDK 사례 값 (sky130) -- 2026-11-05, 위임 A-94, 단순화 A-96·A-97

계획·design·card는 역할 이름만 쓴다(O-197, O-233). sky130 값·규칙 번호는 PDK 선언, 그 기록 파일, 이 사례 기록에만 있다. 실행 측정 0(원본 읽기와 손 산술). 엔진은 아래 이름 가운데 `cap_unit_f`·`cap_array_pitch_m`·`cap_unit_side_m`·`resistor_*`만 읽는다.

## 1. 커패시터 배열 (card c1)

기록 파일 `assets/pdk_records/sky130_cap_array_rules.spice`(선언 `sources` 항목, `base` = 선언 폴더, 기존 형식 `spice_instance_line`, `line_pattern` = `^\.param\s+(.*)$`, `units_m` = {"": 1e-6}). 내용:

```text
* sky130 MIM 배열 규칙 기록. 원본 = C:/pdk/open_pdks_sky130_magic/sky130.tech
* 원본 sha256 = 5f96a22bd00169807b2228742e17a27e3624e5fb010c523447bbc4fee30a4f97
* capm.1 = 줄 5104, capm.2a = 줄 5105, capm.3 = 줄 5112~5113(이어짐 줄). 값 단위 µm. 원본이 바뀌면 손으로 옮긴다(자동 감지 없음, O-233)
.param capm_1 = 1.0
.param capm_2a = 0.84
.param capm_3 = 0.14
```

| 양(선언 안 이름) | 출처 | 값 |
|---|---|---|
| `mim_min_w_m` w | 기록 파일 `capm_1` | 1 µm |
| `mim_array_spacing_m` s | 기록 파일 `capm_2a` | 0.84 µm |
| `mim_enclosure_m` e | 기록 파일 `capm_3` | 0.14 µm |
| `mim_perimeter_cap_f_per_m` ρ_P | cpmimc, `sky130_fd_pr/models/r+c/res_typical__cap_typical__lin.spice:8`(기존 형식, 새 source 항목) | 0.19e-15 F/µm |
| `mim_cap_density_f_per_m2` ρ_A(기존) | camimc, 같은 파일 `:7` | 2.00e-15 F/µm² |

`derived_quantities`(식은 여기와 선언에만):

| 엔진 이름 | 식 | 값 |
|---|---|---|
| `cap_unit_f` C_u | `mim_cap_density_f_per_m2 * mim_min_w_m * mim_min_w_m + 4 * mim_perimeter_cap_f_per_m * mim_min_w_m` | 2.76 fF |
| `cap_array_pitch_m` p | `mim_min_w_m + mim_array_spacing_m` | 1.84 µm |
| `cap_unit_side_m` a | `mim_min_w_m + 2 * mim_enclosure_m` | 1.28 µm |

**옛 식과 대조(손 산술)**: A_C = (√N·(w + s) − s + 2e)² = ((√N − 1)·p + a)², C_max = C_u·((√A − 2e + s)/(w + s))² = C_u·(1 + (√A − a)/p)²이다(p = w + s = 1.84 µm, a = w + 2e = 1.28 µm). 값 일치: C = C_u → 1.6384 µm²(= a²), 1 pF → (18.0347 × 1.84 + 1.28)² = 1187.75 µm², 10 pF → 12142.9 µm². 세 수 모두 양수.

C_max(A) (√A는 µm 기준):

| area_search_m2 | C_max | 옛 공통 상한 대비 |
|---|---|---|
| 1.5e-8 m² | 12.3 pF | 1.2배 |
| 2e-8 m² | 16.4 pF | 1.6배 |
| 2.5e-8 m² | 20.5 pF | 2.1배 |
| 4e-8 m² | 32.8 pF | 3.3배 |

**상계 조건 η(u) ≥ η(w)**: η(u) = (ρ_A·u² + 4·ρ_P·u)/(u + s)². 2ρ_A·s = 3.36, 4ρ_P = 0.76(fF 단위) → 2ρ_A·s ≥ 4ρ_P라 η는 u에 단조 증가, 그러므로 u ≥ w에서 조건 성립(손 산술 η(1) 0.815, η(2) 1.18, η(5) 1.58, η(30) 1.92 fF/µm²). capm.12(최대 면적)는 값 없음(`wt/_drafts/evidence/2026-10-29/q2_cbox.md` §1).

대가: 큰 배열 효율 대비 과대. u = 1 µm 효율 0.295 대 u = 30 µm 0.946(`wt/_drafts/evidence/2026-10-31/k13_cprime/eff_out.txt`). 1 pF 사례: 이 식 1187 µm², 한 개의 MIM 505 µm²(2.35배).

## 2. 저항 후보 (card c1·c5)

| 양 | poly_generic(c1, Ω당 면적·κ 추가) | 정밀 poly(c5, `sky130_fd_pr/cells/res_high_po/sky130_fd_pr__res_high_po_0p35.model.spice`) |
|---|---|---|
| 시트 저항 | rp1(기존) 48.2 Ω/□ | rsheet × w = 1112.41 × 0.35 |
| 폭 | poly.3(기존) 0.33 µm | w = 0.350 µm |
| 기생 면적 계수 c_A | cp1f 1.06e-04 F/m² (`models/parameters/typical.spice:2876`) | crpf_precision 1.06e-04 F/m² (`models/r+c/res_typical__cap_typical.spice:40`) |
| 기생 둘레 계수 c_P | cp1fsw 8.64e-11 F/m (같은 줄) | crpfsw_precision_1_1 5.04e-11 F/m (같은 파일 `:41`) |
| 머리 면적(수 하나) | 기존 식 | 2·(licon.1b + 2·licon.8a)·(licon.1c + licon.8a) = 1.456 µm² |
| `area_per_ohm_m2` 식 | w·w/R□ = 2.259e-15 m²/Ω | 같은 식 = 3.146e-16 m²/Ω |
| κ `c_par_per_ohm` 식 | (w/R□)·(c_A·w + 2·c_P) = 1.4226e-18 F/Ω | 같은 식 = 1.2397e-19 F/Ω |

머리 식 대조(periphery.csv:625·626·639): licon.1b + 2·licon.8a = 0.19 + 0.16 = 0.35 = 셀 폭. licon.1c + licon.8a = 2.00 + 0.08 = 2.08 = 셀 C 식의 머리 길이. poly_generic의 cp1f·cp1fsw는 작성자 판독이다(`.model mcp1f` poly-field 용량, `sky130_fd_pr__model__r+c.model.spice:87`). 독립 판정 대상.

선언 셀 파일과 κ의 출처: 시트 저항·폭 = 셀 파일, c_A·c_P = 그 셀이 읽는 `res_typical__cap_typical.spice`. 레이아웃 뒤 SPICE 소자 = 셀 파일 하나.

Ω당 면적: 정밀 3.15e-4 µm²/Ω 대 generic 2.26e-3 µm²/Ω(`wt/_drafts/evidence/2026-10-29/p4r_cm_sense.md` §3.3). 선언 시점 선택 = 정밀 poly.

C_par = κ·R(정밀) 대 셀 역산 값 `res_handcalc.out.txt` C_cell. 옛 안(둘레 끝 항 2·c_P·w = 0.035 fF 포함)과의 차는 그 상수뿐이다:

| R | κ·R | 옛 안 | C_cell | κ·R / C_cell |
|---|---|---|---|---|
| 2 kΩ | 0.248 fF | 0.283 | 0.726 | 0.34 |
| 10 kΩ | 1.240 fF | 1.275 | 1.757 | 0.71 |
| 70.1 kΩ | 8.690 fF | 8.72 | 9.219 | 0.94 |
| 1 MΩ | 124.0 fF | 124.0 | 124.5 | 0.996 |

같은 표의 ωRC(30 MHz) 곱은 10 kΩ에서 3.3×10⁻³이라 비가 작은 쪽은 C가 중요하지 않은 구간이다. 정밀화는 oracle 몫.

## 3. R_min -- 철회(O-233, A-96)

R_min(정밀 후보) = 1701 Ω(옛 기록 `wt/_drafts/evidence/2026-10-29/handcalc_principle_audit/res_handcalc.out.txt` 끝 줄, sha256 499b7d70…)은 선언·엔진에 넣지 않는다. 실현은 레이아웃 뒤 SPICE 몫이다. 그 아래 값 R도 선언 시점 종류의 면적·κ로 평가한다. 크기: 100 Ω이면 정밀 면적 0.03 + 1.456 µm², generic 면적 0.23 + 머리, 차는 µm² 규모이고 κ·R 차는 0.13 fF 규모다(손 산술). 합격은 oracle.
