# O-245 LUT DC 열의 단자량 정의 -- 권고안 (2026-11-06)

- 역할: 권고안 작성자(문서·분석). 엔진·생성기 수정 0, 커밋 0, ngspice·pytest 0.
- 실행한 것: grep·sed, 읽기 전용 Python 스크립트 1개(LUT npz 읽기). 임시 경로 `C:/Users/HSLEE/AppData/Local/Temp/la1s_o245_31/`
  - 스크립트 `vdsat_cmp.py`, 결과 `vdsat_cmp.out.txt`
- 사용자 결정 O-245 원문: "DC열도 SPICE 단자량으로 정의해서 모델 무관하게 바꿔". 앞선 지시는 "C열과 4열은 PDK와 무관해야 …"이다(O-197 확장).
- 범위 추가(오케스트레이터 전달, 사용자 "그래"):
  - 비교안 B(Murmann techsweep 꼴 대응표)와 섞는 안 C
  - V* = 2/(gm/ID) 실측
  - 원문 확인
- 원칙 8: 아래 as-built 인용은 외부 사실(PDK·ngspice·LUT 값)과 재작성 범위에만 쓴다.

---

## 0. 결론 요약

| 열 | 권고 | 근거 한 줄 |
|---|---|---|
| ID·GM·GDS·GMBS | **안 A(단자량)**, 네 열을 한 정의로 묶는다. ⚠ 조건 2개 | 노드 KCL과 SPICE AC가 보는 양이 단자량이다(물리 정합). ln ID Hermite 일관성 때문에 네 열은 같은 정의여야 한다 |
| C 6열 + 4열 | 이미 단자량이다(변경 없음) | v2 §1 |
| VTH | **열 삭제**(대안 (b)) | 엔진 소비자 0(실측 grep). 단자량 정의는 상수나 관례가 필요하다 |
| VDSAT | **권고 없음** | 모델 무관하면서 상수 없고 물리 경계와 같은 단자 정의가 없다. V*는 실측상 물리 경계와 다르다. 사용자 질문으로 올린다 |
| 잡음·mismatch | O-245 'DC열' 문언 범위 밖. 같은 원칙(O-197)의 후속 후보(v2 QC5) | §5 |

---

## 1. 열별 단자량 정의 표 (안 A)

생성기 원문 자리:
- 기준 LUT: `wt/20261105-wb1-c/skills/analog-gmid-design/assets/sky130_lut_sweep.py`
  - :92 `OP_PARAMS = ("id","gm","gds","gmbs","vth","vdsat")`
  - :238-239 `@m.xdut.msky130_fd_pr__<cell>[p]`
  - :240-243 AC print, :264-270 점 루프, :307-312 열 계산, :319 `COLUMNS`
- DC 폭 슬라이스: `lut_data/sky130_lut_v2/verification/slices_vdsat/sky130_dc_width_slices.py`
  - :61 `QUANTS`, :179 `.save … @m[...]`, :184-185 `.dc` 2D 스윕
- manifest의 `generator_sha256 8df35d2e…`가 위 슬라이스 생성기와 일치한다.

manifest 열 전수(실측 `keys.py`):
- 기준 npz: kind마다 `ID GM GDS GMBS VTH VDSAT CGG CGD CGS CGB CDD CSS SVG2_1HZ SVG2_HF`
- 슬라이스 npz: `ID GM GDS VTH GMBS VDSAT`
- 별도 파일: noise_r1 `SVG2_F`, mismatch_r1 `DVGS_<변수>`

| 열 | 단자량 정의(안 A) | 지금 정의 | 정의 차(물리) | 크기·의미 있는 영역 | 생성기 변경 자리 |
|---|---|---|---|---|---|
| **ID** | DC 단자 전류. 선언 드레인으로 들어가는 전류 × 극성(NMOS +, PMOS −) = `i(vds)`(기준: `vds dd 0`, 드레인 직렬 원). 슬라이스: `.dc`에 `.save i(vds)` | `@m[id]` = BSIM 채널 전류 크기. 역방향이어도 양수(oracle README:64-71) | 단자 = 채널 + 드레인–벌크 접합 전류(역바이어스 포화전류 + **ngspice `gmin`·V_db**) + 게이트 누설(sky130 `igcmod = igbmod = 0`이라 0) + GIDL(`agidl = 0`이라 0). 근거: 모델 카드 `cells/nfet_01v8/…__tt.pm3.spice` model.0 | 접합 Is ≈ jss·AS + jsws·PS = 2.75e-3·2.5e-12 + 6e-10·7e-6 ≈ 1.1e-14 A(W = 5 µm). gmin 항 ≈ 1e-12 S × V_db = 0.9~2.7e-12 A(⚠ gmin 기본값은 외부 지식). 실측 정합: oracle README:70 "꺼진 NMOS 감지원 2.08e-12 대 @id 2.64e-13" → 차 1.8e-12 ≈ gmin × 1.8 V. **LUT 실측**: VGS = 0·VDS = 0.9 V의 `@m` ID 중앙값 nfet 1.1e-15 A, pfet 2.6e-20 A다. gmin 항이 VGS 환산 > 1 mV 옮기는 on 칸 비율은 W_ref nfet 21.3 %·pfet 36.1 %, 최소 폭 nfet 0.36 µm 26.0 %·pfet 0.42 µm 34.0 %(`vdsat_cmp.out.txt`). 모두 깊은 약반전 칸이다(ID ≲ 1e-10 A). 의미 있는 영역은 꺼짐 판정, ln ID 보간의 깊은 약반전 끝, VDS = 0 열이다 | 기준: `_fields`(:239-244)에 op 뒤 `i(vds)` print, `_parse_output`(:307-312) ID = 극성 × i(vds). 슬라이스: `build_netlist` :179 `.save`, `run_combo` :236 |
| **GM** | Re(Y_dg) 저주파: 게이트 AC 여기, 드레인 단자 AC 전류 실수부. `real(i(vds))` at f_lo | `@m[gm]` | 게이트 누설 0(위)이라 정의 차 ≈ 0 | 무시 가능 | 기준: 저주파 `ac`(아래 ⚠1) 게이트 여기 때 `real(i(vds))` print. 슬라이스: `.dc` 대신 점마다 op + ac(비용 §4) |
| **GDS** | Re(Y_dd) 저주파: 드레인 여기, 드레인 전류 실수부 | `@m[gds]` | 단자 = gds + g_bd(접합 컨덕턴스 ≈ gmin + Is/(n·U_T)·e^{−V/U_T}) | ≈ 1e-12 S. 강반전 gds 1e-6~1e-4 S 대비 1e-6 이하, 깊은 약반전·꺼짐 gds(≲ 1e-11 S)와 같은 자릿수다 | 드레인 여기 블록(:268)에 `real(i(vds))` print(저주파) |
| **GMBS** | Re(Y_db) 저주파: 바디 여기, 드레인 전류 실수부(부호 = 단자 규약 그대로) | `@m[gmbs]` 절댓값 | 단자 = gmbs − g_bd | 위와 같은 1e-12 S 자릿수. 강·중반전에서 무시 가능 | 바디 여기 블록(:269)에 `real(i(vds))` print |
| **VTH** | 단자 정의 없음(§2) | `@m[vth]` | -- | -- | 삭제 시: :92, :319, 슬라이스 :61, `_dc_run`·`boundary_probe` 마스크(:545·:551) |
| **VDSAT** | 단자 정의 없음(§2) | `@m[vdsat]` | -- | -- | §2 결정에 따름 |
| C 6열·4열 | 이미 단자 AC Im(Y)/ω | 같음 | -- | -- | QC1·QC2 v2 |
| SVG2 | `inoise_spectrum`²(게이트 환산 출력잡음 = 해석 결과) | 같음 | 모델 무관(정의는 단자) | -- | 없음 |

**⚠1 측정 주파수(물리 정합)**
- 기준 AC는 F_TEST = 100 MHz다. sky130 카드는 `rbodymod = 1`(rbdb = rbsb = rbpb = 50 Ω)이다.
- 100 MHz의 Re(Y)에는 접합 C가 바디 저항을 거쳐 생기는 (ωC_j)²·R_b 항이 들어간다. 추정값은 C_j ≈ 3.6 fF(W = 5 µm, cjs·AS + cjsws·PS)일 때 ≈ (2π·1e8·3.6e-15)²·50 ≈ 2.6e-10 S다(물리 추정, 미측정).
- 이 크기는 약반전 gds와 같은 자릿수라 **GDS·GMBS 단자 정의는 저주파 AC여야 한다.**
- 저주파 점은 새 상수를 만들지 않고, 생성기에 이미 선언된 `NOISE_F_PROBE = 1 Hz`(:80)를 쓸 수 있다.

**⚠2 gmin(시뮬레이터 옵션)이 값에 들어간다**
- 단자량은 '모델 무관'이 되지만 값에 ngspice 수치 옵션 `gmin`(물리 아님)이 섞인다. 깊은 약반전에서는 단자 ID가 ~1e-12 A 바닥으로 평평해진다.
- 그러면 gm/ID = GM/ID → 0이 되어, gm/ID 대 VGS 곡선이 약반전 끝에서 내려간다.
- 영향:
  - lut CONTRACT §3 분지 규칙(gm/ID → VGS 역산)이 한 gm/ID에 VGS 둘을 낼 수 있다(미측정).
  - Hermite 일관성(GM/ID·GDS/ID = ln ID 편미분)은 유지된다. gmin 항이 VGS에 무관하기 때문이다.
- 처리 조건:
  - (i) `gmin`을 LUT 측정 조건(provenance)에 싣고 oracle도 같은 값으로 돈다(정의 동일성).
  - (ii) 바닥 칸의 정의역 처리는 design에서 정한다. 새 문턱 상수는 금지다.

**같은 정의로 묶어야 하는 열(안 C 설계 제약)**
- lut CONTRACT 4.2: "저장 GM/ID·GDS/ID가 ln ID의 정확한 편미분이라 Hermite"(`lut/CONTRACT.md:537`).
- ID를 채널 op로, GDS를 단자로 섞으면 깊은 약반전에서 d ln ID/dVDS ≠ GDS/ID가 되어 이 전제가 깨진다.
- 그래서 **ID·GM·GDS·GMBS는 한 정의(모두 단자 또는 모두 대응표)**여야 한다.

---

## 2. 단자량이 아닌 양: VTH·VDSAT

### 2.1 VTH -- 소비자와 원 결정

- **엔진 소비자**(실측 grep, `gmid_engine` tests 제외):
  - `lut_set.py:188-215`(적재), `point_query.py:54-61`(`OpPoint.vth` 생산), `lut_types.py:294`
  - `OpPoint.vth`를 **읽는 엔진 자리 0**이다(`\.vth\b` grep: lut 밖 0). `_module_map.py:329`는 문언이다.
- **oracle**: `core/compare.py:248·271` `VTH_spice`·`vov_spice`는 기록 칸이다(판정 0).
- **생성기**: `boundary_probe` 마스크 `vg >= vth`(:545)와 `switch_excess_dVTH_V` 통계(:551)가 있다. bin 경계 탐침의 기록용이다.
- **계획 문언**:
  - :305 DEC-105 '읽는 열 … ID·GM·GDS·VTH·GMBS·VDSAT'(열 목록)
  - :586 B3 `OpPoint`(IDu·gm/ID·gds_per_w·VTH)
  - :2581·:2834는 물리 설명 서술이다(엔진 소비 아님).
- 원 결정: VTH는 옛 4열(ID·GM·GDS·VTH)부터 있던 열이고, U-27·E5에서 계속 실렸다. 판정 근거로 정한 결정은 찾지 못했다(계획 grep).

| 대안 | 정의 | 물리 정합 | oracle 정의 동일성 | 상수 발명 | 판정 |
|---|---|---|---|---|---|
| (a1) ELR(최대 gm 선형 외삽) | 낮은 VDS 선형 영역 ID–VGS 접선 절편 | 강반전 문턱 관례 | oracle도 재생 필요 | 'VDS 낮음' 선택이 상수 | 관례 |
| (a2) d²ID/dVGS² 최대점 | 단자 ID 2차 미분 극값 | 상수 없음. 격자 37.5 mV 분해능 | 같은 식으로 가능 | 0 | 가능하지만 **소비자 0** → 원칙 9 위반 |
| (a3) 정전류법 | ID = I_c·W/L의 VGS | 관례 | -- | I_c 발명 | ✗ |
| **(b) 열 삭제** + 문언 정정(:305·:586, CONTRACT 1.2·4.2, oracle VTH 기록 칸·`vov_spice`, 생성기 마스크를 on_mask ∧ 포화 정의로) | -- | -- | 기록 칸 소멸 | 0 | **권고** |

### 2.2 VDSAT -- 소비자와 원 결정(O-238 대조)

- **엔진 소비자**(실측 grep, 46파일): `lut/vdsat_query.py`·`vdsat_curve.py`·`vdsat_tolerance.py`·`sat_threshold*.py`, `sizing/seal_region.py`·`region_judge.py`·`block_dc.py`·`seal.py`, `search/iv_headroom.py`·`start_intervals.py`·`seal7_pending.py`, `metrics/icm_config.py`·`headroom_bound.py`·`ls_swing.py`·`ss_off_gate.py` 등이다.
- **원 결정 근거**:
  - **O-204**(계획 :416, :679 N3.6 (2)): 포화 = VDS ≥ VDSAT, 여유 없음. 근거는 "LUT VDSAT = SPICE `@m[vdsat]` 정의 동일"과 "분해능을 판정에 쓰지 않음"이다.
  - 근거의 핵심은 엔진과 oracle이 같은 정의를 쓰는 것이다. `@m[vdsat]` 자체의 물리 정합은 근거가 아니다(:679 "경계 양 VDSAT 자체의 약반전 정합(U-122·B88·O-156)은 별도 열린 결정").
  - **U-27 (c)**(:2734): VDSAT 열을 '봉인 7, DEC-88' 용도로 추가했다.
  - **U-122/B88**(:2828): "약반전 pfet BSIM vdsat 바닥 -- 포화 판정이 약반전에서 낙관일 수 있음", 미결이다. O-156 sf_pushpull 해석이 이 결과에 달려 있다.
  - **LA-0 (5)**(:2098): s_eng = VDS − VDsat(LUT), s_sp = VDS_sp − `@m[vdsat]`의 대조표 기록이다(판정 아님).

**실측: BSIM VDSAT 대 V* = 2/(gm/ID)** (`vdsat_cmp.out.txt`)
- 조건: 기준 npz W = 5 µm, VDS = 0.9 V, T = 27 °C, U_T = 25.87 mV.
- `@m` 열을 단자량 대용으로 썼다. 강·중반전에서는 차 ≤ 1e-6이고, 깊은 약반전은 §1 ⚠2 참조.

| 소자 L, VS | 영역(gm/ID) | VDSAT(BSIM) | V* | V*/VDSAT |
|---|---|---|---|---|
| nfet 0.15, 0 | 24.3(약) | 43.0 mV = 1.66 U_T | 82.4 mV | 1.91 |
| nfet 0.15, 0 | 2.67(강) | 240.6 mV | 749.9 mV | 3.12 |
| nfet 0.15, 0 | 0.99(VGS 1.8) | 351.9 mV | 2021 mV(> VDD) | 5.74 |
| nfet 0.5, 0 | 12.5(중) | 128.2 mV | 159.6 mV | 1.25 |
| nfet 1.0, 0 | 27.0(약) | 39.1 mV = 1.51 U_T | 74.1 mV | 1.90 |
| nfet 4.0, 0 | 9.2 | 189.4 mV | 217.7 mV | 1.15 |
| pfet 0.15, 0 | 14.8(약, DIBL) | 43.4 mV | 135.2 mV | 3.12 |
| pfet 0.5, 0 | 30.5(약) | 43.8 mV = 1.69 U_T | 65.7 mV | 1.50 |
| pfet 1.0, 0 | 9.0 | 197.0 mV | 222.2 mV | 1.13 |

- **전역(on 칸, VDS ≥ 0.3 V)**: V*/VDSAT
  - nfet: p1 1.07, p50 1.58, p99 4.76, min 1.01, max 7.58
  - pfet: p1 1.01, p50 1.34, p99 2.58, min 0.93, max 3.47
- **약반전(gm/ID > 20) BSIM VDSAT/U_T**:
  - nfet: p1 1.51, p50 1.75, p99 2.80
  - pfet: p1 1.54, p50 1.81, p99 2.21
- ID–VDS 꺾임점(−dGDS/dVDS 최대)은 격자(37.5 mV)가 거칠어 거의 모든 점에서 첫 칸 56 mV가 나왔다. **정보 없음**이라 근거에 쓰지 않는다.

**물리 해석(원칙 21)**
- 약반전 채널 전류는 I ∝ 1 − e^{−VDS/U_T}다.
  - 확산 성분만 보면 gds/ID = e^{−x}/((1 − e^{−x})·U_T)(x = VDS/U_T)다.
  - BSIM VDSAT(x ≈ 1.75)에서 이 값은 0.21/U_T다. 확산 성분만으로 진성 이득 (gm/ID)/(gds/ID) ≈ 1/(0.21·n) ≈ 3~4다(n ≈ 1.3, 추정).
  - V*(x ≈ 2.5~3.2)에서는 0.04~0.09/U_T라 10~20이다.
  - 약반전 '포화'는 점근이라 경계가 관례이고(교과서 3~4 U_T), BSIM의 2·vt항(BSIM4 Vdsat 식의 Vgsteff + 2vt, 외부 지식)도 관례다. → **B88 우려(BSIM 바닥 낙관)가 데이터로 뒷받침된다**: p50 1.75 U_T < 3 U_T.
- 강반전 짧은 채널에서는 속도 포화로 VDSAT ≪ V_ov다. V*는 오히려 2·V_ov까지 커진다(gm/ID → 1/V_ov).
  - nfet L 0.15 µm에서 V*/VDSAT가 3~5.7이고, V*가 2.0 V로 VDD를 넘는다.
  - 즉 V*는 이 영역에서 포화 경계가 아니다.
  - 2는 제곱 법칙의 계수다. 이 값을 경계로 쓰면 모형 가정을 정의로 쓰는 것이다(원칙 1 '관례를 정의로 쓰지 말 것'·원칙 11 긴장).
- §1 ⚠2 때문에 단자 ID를 쓰면 깊은 약반전에서 GM → 0, ID → gmin 바닥이 된다. 그러면 V* = 2ID/GM이 발산해 그 칸을 모두 비포화로 만든다(수치 옵션 산물).

**봉인 7 판정 변화(V*로 바꿀 때)**
- 방향: V* ≥ VDSAT가 거의 전 칸이다(nfet min 1.01, pfet p1 1.01). 그래서 **모두 더 엄해지는 쪽**이다. VDSAT ≤ VDS < V*인 점이 새로 E-0 거부된다.
- 크기: 같은 소자의 포화 하한이 다음만큼 오른다.
  - 중반전 L ≥ 0.5 µm: +25~40 mV
  - 약반전: +25~40 mV(nfet), 짧은 L pfet: +90 mV
  - 강반전 짧은 L: +0.5~1.7 V
- 캐스코드가 쌓인 1.8 V 회로의 헤드룸에 직접 들어간다. library 회로별 실현 가능성 변화는 **미측정**이다(재려면 엔진 실행 필요, 이 역할 밖).

| 대안 | 정의 | 물리 정합(포화 물리 정의) | oracle 정의 동일성(DEC 관문) | 상수 | O-245 | 판정 |
|---|---|---|---|---|---|---|
| (a) V* = 2/(gm/ID) | 단자 ID·GM만 | 약반전: BSIM보다 보수(2.5~3.2 U_T). **강반전 짧은 L: 경계 아님**(3~5.7배, VDD 초과). ⚠ gmin 바닥에서 발산 | oracle이 소자별 단자 gm을 재야 함 → 소자 재생 넷리스트(§3) | '2' = 제곱 법칙 계수(⚠ 관례를 정의로) | 충족 | ⚠ 물리 위반 영역 있음 |
| (a′) ID–VDS 꺾임(곡률 극값·접선 교점) | 단자 ID(VDS) | 강반전은 가능. **약반전은 극값 없음**(곡률 최대 = VDS 0). 접선 교점은 V_ov/2·U_T로 물리 VDSAT와 다름 | 같은 식 재생 가능 | 약반전에 관례 상수 필요 | 충족 | ✗ |
| (b) 열 삭제 + 포화 술어 재정의(예: gds/ID ≤ 문턱, 이득 몫) | 단자 GDS·ID | 술어 자체는 물리적이다. 다만 문턱이 필요하다 | 같은 식 | **문턱 발명** 또는 spec 선언 필요 | 충족 | DEC-90 '전 MOS 포화'·O-204·O-53 선언 영역의 근본 재정의 → 사용자 원칙 결정 |
| (c) 대응표: 논리 이름 VDSAT ↔ 그 모델의 포화 전압 op 변수(BSIM4 `vdsat`, PSP `vdss` 등), PDK·LUT 규칙 선언 한 곳 | 모델 op | 공정 안에서는 현행과 같다(B88 우려 그대로) | 엔진·oracle이 같은 대응을 읽어 동일 | 0 | **위반**(모델 종속 정의, 모델마다 식이 다름) | ⚠ O-245 문언 위반 |

**권고: 없음.**
- 모순 1: O-245(모델 무관)와 원칙 1(물리 경계)을 동시에 만족하는 상수 없는 단자 정의가 없다.
  - (a)는 물리 위반 영역이 있다.
  - (a′)는 약반전 정의가 없다.
  - (b)는 문턱이 필요하다.
  - (c)는 O-245와 충돌한다.
- 모순 2: U-122/B88이 미결이다. 지금 정의를 바꾸면 U-122 판정 자리(card CL-1 뒤 E-1 판정, :2098·:2828)를 앞당겨 정하게 된다.
- 질문(§6 Q3)으로 사용자 원칙 결정을 받는다. 오케스트레이터 참고로 실현성 순위만 적는다.
  - (c): O-245 범위를 'VDSAT 제외'로 좁히는 원래 취지와 다름 표지가 필요하다. LA-1 차단 0이다.
  - (b): 문턱을 spec 선언으로 받는 원칙 결정이 필요하다.
  - (a): 비권고(물리).

---

## 3. oracle 정의 동일성 -- 바뀌는 자리와 물리 영향

| 자리 | 지금 | 안 A(ID 단자) | 물리 영향 |
|---|---|---|---|
| 꺼짐 판정 O-205 (2)·O-210 RR-2(계획 :290 DEC-90 (1), :683 N3.6 (6)) | 선언 방향 `@m[id]`·sign(@vds) ≤ 0 = FAIL(`adapters/ngspice/read.py:35-39` `signed_id`) | 선언 드레인 직렬 0 V 감지원 전류 × 극성 ≤ 0 = FAIL. 부호가 감지원에서 바로 나와 `signed_id` 꾀가 필요 없다 | 정방향(V_d > V_s, nmos): 채널·접합 모두 드레인 유입(+)이라 판정 같음. **역방향 미세 전류**(\|I_ch\| < gmin·V_db ~1e-12 A)는 단자가 양수 → '전도'로 바뀐다. 다만 선언 없는 MOS는 그다음 포화 대조 VDS < 0 < VDSAT에서 FAIL이라 최종 판정은 같다. `triode` 선언 MOS는 '역방향 미세 전류 = 전도'로 받아들여진다(차이 1건, 크기 ≲ 1e-12 A). KCL 항등 0 소자(VDS = 0)는 단자 ID = 접합 몫 ≠ 0이다. 그래도 연결 기반 제외 규칙(표 9행)이라 영향 0 |
| RR-2 근거(O-238) | "oracle 꺼짐 = 엔진 P5와 같은 식"(user_decisions O-210 행), README:70 "LUT ID 열과 같은 양끼리 비교" | 근거가 'LUT와 같은 양'이다. LUT가 단자로 바뀌면 근거가 단자 쪽으로 같이 옮겨 간다 | 근거 유지, 문언 '채널 op ID, 단자 전류 아님'만 번복(**원래 취지와 다름**) |
| 엔진 P5(봉인 9) | LUT `@m` ID > 0 | LUT 단자 ID > 0 | VDS > 0 칸은 둘 다 > 0이라 같다. VDS = 0 열: `@m` = 0, 단자 = gmin·VS + Is > 0. 그래도 on_mask = ID > 0 ∧ GM > 0에서 GM(VDS = 0) ≈ 0으로 막힌다(GM이 수치 잡음으로 > 0이 될 수 있다 -- 미측정) |
| 봉인 7 oracle 대조(O-204, DEC-90 SPICE 대조 (ii)) | VDS ≥ `@m[vdsat]` | VDSAT 결정(§2.2)에 따름. (c)면 그대로, (a)면 oracle이 소자마다 그 바이어스로 **단독 소자 재생**(같은 DUT 줄·include, 저주파 AC)을 돌려 단자 gm을 잰다 | (a) 비용: 소자 수 × 점 수만큼 ngspice 소실행이 추가된다(미측정) |
| oracle 기록 칸(DEC-72): gm·gds·VTH·VDSAT `@m` | `compare.py:248-271` | gm·gds를 단자로 같은 정의로 쓰려면 재생이 필요하다. 기록 전용이라 우선순위 낮다. VTH·`vov_spice`는 삭제(§2.1) | 판정 영향 0 |
| LA-0 (5) 대조표(:2098) | s_sp = VDS_sp − `@m[vdsat]` | VDSAT 결정에 따름 | -- |
| 생성기·oracle `gmin` | 기본값(선언 없음) | LUT provenance에 싣고 oracle 같은 값(정의 동일성 조건) | §1 ⚠2 |

---

## 4. 데이터 비용 (실측 인용 + 추정)

| 대상 | 기록 | 안 A 변경 | 비용 |
|---|---|---|---|
| 기준 LUT 360조합 | `REGEN_REPORT.md` §1: 벽시계 3997 s(동시 13개), ngspice 합 nfet 12,909 s·pfet 10,175 s, 단독 조합 ~53 s(op + AC 4 + noise 2, 2401점) | ID: op 뒤 print만(0). GM·GDS·GMBS: 저주파 AC 3회/점 추가 | 추정 +30~40 %(미측정). AC 1회가 noise보다 가벼우면 더 적다 |
| DC 슬라이스 576조합 | `generation_progress.log`: `.dc` 2D, 조합 ~17 s, 전체 1230.6 s(2026-10-08) | ID: `.save i(vds)` 추가(0). GM·GDS·GMBS 단자: `.dc`로는 불가 → 점마다 op + AC 3회 루프(기준 생성기 꼴) | 추정 조합 ~30~40 s 단독 → ~2만 CPU-s, jobs 5~6에서 ~1 h(미측정) |
| QC2 (S1) 슬라이스별 C | v2 :479 "약 35만 CPU-s, 7~8 h"(agent 인용 -- v2 권고 작성자 추정) | 같은 op + AC 루프 | **같은 실행에 묶으면 DC 단자 열의 추가 비용 ≈ print + 저주파 AC 3회**. 한 생성으로 묶을 수 있다(같은 DUT 줄·격자·점 루프) |
| mismatch 360조합 | lut CONTRACT 10.1: 79분, 조합당 op 2401 × 4~5 곡선 | 매칭 전류 `@m[id]` → `i(vds)`, 역산 기울기 `@m[gm]` → 단자 gm 또는 단자 ID 미분 | 재생성 필요(같은 시간대, ~80분 추정) |
| noise | 변경 없음 | -- | 0 |

- **LA-1 지연**: DC 열 정의를 바꾸면 기존 LUT 묶음(`lut_v2_location.json` sha256 고정)의 기준·슬라이스·mismatch를 재생성해야 한다.
  - QC2 (S1)과 한 번에 하면 추가 벽시계는 QC2 실행 안에 흡수된다.
  - 따로 하면 슬라이스 ~1 h + 기준 ~1.3 h + mismatch ~1.3 h가 든다(추정).
  - 엔진 쪽 재작성 범위: `lut_set` 적재 열, `OpPoint.vth` 삭제, `signed_id` 대체, oracle 감지원 넷리스트. card 1개 규모로 본다(추정).
- O-229 2: 데이터 card는 오라클 card가 아니다. ngspice 기준선 대조 1회 규칙의 적용 여부는 오케스트레이터가 정한다.

---

## 5. 잡음·mismatch -- 범위 판정만

| 양 | 지금 정의 | 단자량인가 | O-245 'DC열' 범위 | 같은 원칙(O-197) |
|---|---|---|---|---|
| `SVG2_*`(기준·noise_r1) | `inoise_spectrum`² = 출력 잡음 v(d)를 게이트 AC 이득으로 나눈 해석 결과(생성기 :271-273, :798) | **예**(정의가 단자 측정이다. 잡음원 모형은 시뮬레이터 안) | 밖(AC 잡음 열) | 이미 충족 |
| `noise_ef_{nmos,pmos}`(PDK 선언, `LutSpec.noise_ef`) | BSIM4 `ef`로 분해 S_vg = A/f^EF + B(CONTRACT 9) | 아님(모형 꼴) | 밖(DC 열 아님, 선언 양) | 위반 후보. v2 QC5 그대로(주파수 7점 데이터 보간이면 EF 불요) |
| `DVGS_k`(mismatch_r1) | 같은 `@m[id]`에서의 VGS 차, 섭동 = 카드 `*_slope_spectre` 0 → 1σ(:995-1020) | 측정량(ΔVGS at equal ID)은 DC 단자량으로 바꿀 수 있다(매칭 전류 `i(vds)`) | **매칭 전류 부분만 범위 안**(DC 양). 섭동 변수의 꼴(카드 mismatch 표현 파싱, DEC-96 (2)·2026-10-08 Q2·`core/pdk_decl.py`)은 범위 밖 | 꼴 의존 위반 후보. v2 QC5(모델 무관 대안 = 쌍 MC 단자 σ(ΔVGS), `assets/sky130_pair_mc.py` 꼴, 생성기 비용 큼) |
| U-36(수동소자 면적) | PDK 선언 단위 면적 | 해당 없음(LUT 열 아님) | 밖 | 관련 없음 |

---

## 6. 비교안 B(gm/ID 방법론 표준 도구 방식)·섞는 안 C

### 6.1 원문 확인

- **저장소**: https://github.com/bmurmann/Book-on-gm-ID-design(WebFetch, 2026-11-06). 로컬 PDF는 없다(`find`·`references/` grep 0).
- (a) **모델 대응을 설정 파일 한 곳에 두는가: 예.**
  - `starter_files_closed_source_tools/techsweep_config_{bsim3_180_hspice, bsim4_28_spectre, bsim4_45_hspice, bsimcmg_16_spectre, psp_65_spectre}.m`가 모델·시뮬레이터마다 하나씩 있다.
  - `c.outvars = {'ID','VT','IGD','IGS','GM','GMB','GDS','CGG','CGS','CSG','CGD','CDG','CGB','CDD','CSS'}`가 논리 열이다.
  - `c.n{k} = {'<op 표현식>','<단위>',[선택 벡터]}`가 대응이다.
  - URL: https://raw.githubusercontent.com/bmurmann/Book-on-gm-ID-design/main/starter_files_closed_source_tools/techsweep_config_psp_65_spectre.m
- (b) **쓰는 변수는 모두 소자 op 변수다.**
  - PSP 65: `'mn.m1.m1:ids'`(ID), `':vth'`(VT), `':gm'`, `':gmb'`, `':gds'`, `':cgg'`…, 접합 `'mn.d1.d1:cj'`
  - BSIM4 28: `'mn:ids'` …. PMOS 부호는 선택 벡터의 −1이다(bsim4_28). PSP 판은 바이어스 원 부호로 처리한다.
  - 오픈 소스 sky130: `starter_files_open_source_tools/sky130/simulation/techsweep_nfet_01v8.spice`가 `.save @m.xm1.msky130_fd_pr__nfet_01v8[id]·[vth]·[gm]·[gmbs]·[gds]·[cgg]…`, 잡음 `onoise.m….id`·`.1overf`를 쓴다.
  - **단자 전류 `i(v…)`는 ID에 쓰지 않는다. `vdsat`은 어느 설정에도 없다.**
  - 용량도 op 변수다. 이 프로젝트가 피한 방식으로, 생성기 docstring은 "ngspice BSIM4 `@device[cgd]` op-info … Cgd 36배" 실측이라고 적는다.
- (c) **V* 정의 쪽·줄: 확인 못 함.**
  - 책(Jespers & Murmann, *Systematic Design of Analog CMOS Circuits*, CUP 2017, doi 10.1017/9781108125840)의 로컬 PDF가 없고, 저장소 README에도 V* 정의가 없다.
  - 'V* ≡ 2/(gm/ID)'는 외부 지식이고 근거로 쓰지 않는다.
  - 로컬 근거 `references/gm-id-methodology.md:567`은 Walker 강의 "VDsat ≈ 2/(gm/ID)"이고, :169는 "1차 견적"이다(경계 정의가 아니라 견적).

### 6.2 열별 A·B·C 비교

| 열 | 안 A 단자량 | 안 B 대응표(Murmann 꼴) | 안 C(혼합) |
|---|---|---|---|
| ID | `i(V_d)`. 공정 바꿀 때 **무엇도 안 바꿈**(DUT 줄·include만). 정의 = 접합·gmin 포함. oracle 감지원 | 논리 ID ↔ 모델 `id`/`ids`. 공정 바꿀 때 **대응표 1곳**. 정의 = 채널(모델마다 미세 차) | A |
| GM·GDS·GMBS | 저주파 Re(Y). 안 바꿈. 정의 = 접합 컨덕턴스 포함 | ↔ `gm`·`gds`·`gmbs`/`gmb`. 1곳 | A(ID와 한 정의 -- §1 Hermite 제약) |
| C 10열 | 이미 A | Murmann은 op `cgg`… → ⚠ ngspice BSIM4 op-info 오류 실측(Cgd 36배) | A |
| VTH | 정의 없음 → 삭제 | ↔ `vth`(모델마다 정의 다름) | 삭제 |
| VDSAT | 정의 없음(§2) | ↔ `vdsat`(BSIM4)·`vdss`(PSP, 외부 지식). 모델마다 식이 다름 | **대응표**(사용자 결정 대기 -- §2.2 (c)) |

| 축 | A | B | C |
|---|---|---|---|
| 이식성(공정 바꿀 때) | DUT 줄·include만 | 대응표 1곳 + 부호 규약 | DUT 줄 + VDSAT 대응 1항목 |
| 물리 정의 | 노드 KCL·SPICE AC가 보는 양과 같다(KCL 자기 정합 E-0과 정합). gmin 섞임 ⚠ | 채널 양. 노드 KCL과 접합 몫(~1e-12 A)만큼 다르다. 엔진 MNA가 접합 컨덕턴스를 따로 넣지 않으면 꺼짐·깊은 약반전 노드에서 SPICE와 정의 차가 생긴다 | A와 같다 + VDSAT 모델 정의 |
| 정의 동일성(oracle) | oracle 감지원 + (VDSAT (a)면) 재생 | 엔진·oracle 같은 대응표 → 자명 | ID: 감지원, VDSAT: 같은 대응 |
| 공정 사이 정의 동일 | 예 | **아니오**(모델마다 vth·vdsat 식이 다름 → 봉인 7 의미가 공정마다 바뀜) | VDSAT만 아니오 |
| 비용 | §4 | 0(현행 그대로 + 선언 이동) | §4 |
| 원칙 1(SPICE 복제 금지) | 생성기에만 SPICE, 엔진 0 | 같음 | 같음 |
| 원칙 11·O-197 | 선언 0 | 대응표 = PDK 선언 한 곳(O-197 문언 충족) | VDSAT 1항목 |
| O-233(모형 식 재구현 금지 -- v2 인용) | 충족 | 충족(식 재구현 없음) | 충족 |
| O-245 문언 | **충족**(VDSAT·VTH 제외) | **위반**(DC 열 = 모델 변수) | VDSAT만 위반 |

**권고: 안 C = {ID·GM·GDS·GMBS·C: 단자량, VTH: 삭제, VDSAT: §2.2 사용자 결정}.**
- 안 B는 O-245 문언과 정면으로 충돌하고, C 열에서 실측 오류가 있는 op 변수를 쓰므로 권고하지 않는다.
- VDSAT 칸을 (c) 대응표로 정하면 안 C가 확정된다. 그때 표지는 'O-245 범위 축소 -- 원래 취지와 다름'이다.

---

## 7. 질문 문언 초안 (머리 ≤ 12자)

- **Q1 머리 "ID 단자 전환"**
  - 질문: "LUT의 ID·GM·GDS·GMBS를 SPICE 단자량(드레인 단자 전류, 저주파 단자 어드미턴스 실수부)으로 다시 정의할까요? 그러면 oracle 꺼짐 판정(O-205 (2)·O-210 RR-2)의 '채널 op ID, 단자 전류 아님' 문언도 '선언 드레인 단자 전류'로 바뀝니다. 근거인 '엔진 P5와 같은 식'은 그대로입니다."
  - (가) 전환 (Recommended)
    - 노드 KCL이 보는 양이다. 공정을 바꿔도 정의가 그대로다.
    - ⚠ ngspice gmin(~1e-12 S)이 깊은 약반전 칸에 섞인다. LUT 측정 조건에 gmin을 싣고 oracle도 같은 값으로 돈다.
  - (나) 현행 유지(대응표만 PDK 선언으로 이동, 안 B)
    - ⚠ O-245 문언 위반
- **Q2 머리 "VTH 열 삭제"**
  - 질문: "VTH는 단자량 정의가 없고 엔진 소비자가 0입니다(oracle은 기록 칸뿐). 열과 OpPoint.vth, 계획 :305·:586 문언, oracle VTH·vov 기록 칸을 지울까요?"
  - (가) 삭제 (Recommended)
  - (나) d²ID/dVGS² 극값으로 정의해 유지
    - ⚠ 소비자 0이라 원칙 9 위반
- **Q3 머리 "VDSAT 정의"**
  - 질문: "포화 경계 VDSAT는 모델과 무관하면서 상수 없이 물리 경계와 같은 단자 정의가 없습니다. 실측(sky130 LUT): V* = 2/(gm/ID)는 BSIM vdsat의 1.0~7.6배(p50 1.6/1.3)입니다. 약반전에서는 BSIM(1.75 U_T)보다 보수적인 2.5~3.2 U_T이지만, 짧은 L 강반전에서는 VDD를 넘습니다. 어느 정의로 할까요? 이 결정은 U-122(B88) 판정을 앞당깁니다."
  - 권고 없음.
  - (가) 모델 포화 전압 op 변수를 PDK 선언 대응표로(현행 값 그대로)
    - ⚠ O-245 범위 축소, 원래 취지와 다름
  - (나) V* = 2/(gm/ID)
    - ⚠ 강반전 짧은 L 물리 위반, 봉인 7이 모두 엄해짐, gmin 바닥에서 발산
  - (다) VDSAT 삭제 + 포화 술어를 단자 gds/ID 문턱(spec 선언)으로 재정의
    - ⚠ DEC-90·O-204·O-53 재정의, 문턱 출처 필요
  - (라) U-122 판정(card CL-1 뒤)까지 현행 유지, 그 뒤 결정
- **Q4 머리 "oracle 꺼짐식"**: Q1 (가)에 딸린 문언 확인이다. 따로 묻지 않고 Q1에 넣어도 된다.
  - 질문: "oracle은 각 MOS 선언 드레인에 0 V 감지원을 넣고, 그 전류 × 극성 ≤ 0을 꺼짐 FAIL로 판정합니다(`signed_id` 삭제). `triode` 선언 MOS의 역방향 미세 전류(≲ 1e-12 A)가 '전도'로 바뀌는 차이 1건을 받아들일까요?"

---

## 8. 남은 불확실

1. ngspice gmin 기본값 1e-12 S와 접합에 더해지는 방식은 외부 지식이다. oracle README 실측 차 1.8e-12 A와 정합하지만 직접 재지 않았다(ngspice 금지).
2. 단자 ID 바닥이 gm/ID 역산 분지 규칙(CONTRACT §3)에 주는 영향은 미측정이다.
3. 100 MHz Re(Y)의 바디 저항 항 크기 2.6e-10 S는 추정이다.
4. 생성 비용 증가(+30~40 %, 슬라이스 ~1 h)는 추정이다.
5. library 회로별 V* 봉인 7 영향은 미측정이다.
6. PSP `vdss` 등 다른 모델 변수 이름은 외부 지식이다.
7. Jespers & Murmann 2017 V* 정의 쪽·줄은 확인하지 못했다.
8. VDS = 0 열 GM 수치 잡음(on_mask 변화 여부)은 미측정이다.

---

## 9. 보고 5묶음 (원칙 26)

### 9.1 bkit 단계표

| 계획 | design | 검증 | 승인 | test | code | 구현 gap | 감사 |
|---|---|---|---|---|---|---|---|
| 안 함(권고 단계 -- 계획 개정은 결정 뒤) | 안 함 | 안 함(독립 판정 대기) | 안 함 | 해당 없음(코드 0) | 해당 없음 | 해당 없음 | 안 함 |

### 9.2 단계별 점검표 (권고안 기준)

| 항목 | 판정 |
|---|---|
| graph 단일 정본 | 해당 없음(코드 0). 권고는 새 필드 0, 열 정의만 바꾼다. VTH 삭제는 필드 순감, `signed_id` 대체는 정의 자리 하나 유지 |
| G-10·블록 안 재계산 | 해당 없음(코드 0) |
| 새 필드 소비자 | 새 필드 0. VTH 삭제는 소비자 0 실측(grep) |
| 구조·회로 이름 0·상수 발명 0 | 권고 안에 새 상수 0. 저주파는 기존 `NOISE_F_PROBE`를 쓴다. V*의 '2'는 ⚠로 표지 |
| fail-closed | 바닥 칸 정의역 처리는 design 몫(문턱 금지) |
| DC·AC 분리 | ID = DC 해석, GM·GDS·GMBS = 동작점 소신호(AC) -- 정합 |
| 계획 먼저 | 결정 뒤 계획 문언(:290·:305·:416·:586·:679·:683·:2098·U-27 (c))부터 고친다 |
| 작성자 ≠ 검증자 | 이 문서는 작성자 몫이다. 독립 판정 필요 |
| 일반성 n/N | 해당 없음(회로 실행 0). LUT 전 격자 통계는 실측 |
| 만들면 배선 | 스크립트는 측정용(임시 경로). 엔진 산출물 0 |

### 9.3 원래 취지와 다름

1. O-205 (2)·O-210 RR-2 문언 '채널 op ID, 단자 전류 아님' → 단자 전류(Q1 (가)일 때). 근거 '엔진 P5와 같은 식'은 유지된다.
2. U-27 (c) op 열 VDSAT·GMBS → GMBS 단자 정의, VDSAT는 Q3에 따름.
3. VTH 열 삭제(옛 4열 구성 번복).
4. Q3 (가)이면 O-245 범위 축소, (나)·(다)이면 O-204 경계 양 정의 번복과 U-122 선판정.
5. mismatch 매칭 전류 정의 변경(DEC-96 (2) 계산 꼴은 유지).

### 9.4 권고 실측 출처

- **직접 잼**:
  - 생성기 원문 :92·:239-244·:264-273·:307-319·:491-560·:995-1020
  - 슬라이스 생성기 :61·:179·:184-236
  - PDK 카드 model.0 플래그(`rbodymod 1`, `igcmod 0`, `igbmod 0`, `agidl 0`, jss·jsws·rb*·gbmin)
  - 엔진 VTH·VDSAT grep, oracle `compare.py:210-277`·`read.py:35-39`·README:55-90, 계획 행(:290·:297·:305·:416·:586·:679·:683·:2098·:2734·:2828), user_decisions O-205·O-210·O-245 행
  - `vdsat_cmp.out.txt`(LUT 통계), `REGEN_REPORT.md` §1, `generation_progress.log`(1230.6 s), lut CONTRACT 9.1·10.1
  - Murmann 저장소 파일 목록·설정 3개(WebFetch)
- **agent 인용**: v2 권고 :479 "35만 CPU-s, 7~8 h"(추정), v2 §1·§2 표, 모순 점검 V2-4·V2-5.

### 9.5 권고 확인표 10항목 (Q1·Q2, Q3 권고 없음)

| # | Q1 ID 단자 | Q2 VTH 삭제 |
|---|---|---|
| ① 지적 사실 재확인 | 실측(생성기 :239, README:64-71) | 실측(grep 소비자 0) |
| ② 계획 grep | 실측(:290·:683·:2098) | 실측(:305·:586·:2581·:2834) |
| ③ 원칙 전수 | 1·7·8·9·11·O-197 실측 대조(§6.2) | 9·11 |
| ④ 대안표 + ⚠ | §6.2 | §2.1 |
| ⑤ 실현 가능성 | 생성기 print 자리·감지원 실측. 비용은 추정 | grep |
| ⑥ 열린 결정·design | QC2 (S1) 묶음, U-122 | -- |
| ⑦ 원래 취지 | §9.3 | §9.3 |
| ⑧ 원문 쪽 + PDF | 해당 없음(회로 원문 무관). Murmann 저장소 링크 | 해당 없음 |
| ⑨ 물리·회로이론 | §1 접합·gmin·rbody 추정, §3 | 해당 없음(소비자 0) |
| ⑩ 결정 간 모순 점검 | **미실시** -- 점검자 ≠ 작성자 필요(O-204·O-205·O-210·U-27·U-122·DEC-90·DEC-96 (2)·O-197·O-233 대조) | **미실시**(같음) |

## 돌린 범위

- 읽기·grep, 읽기 전용 스크립트 2개(`keys.py`, `vdsat_cmp.py`), WebFetch 6회.
- ngspice·pytest·엔진 적재·커밋 0.
