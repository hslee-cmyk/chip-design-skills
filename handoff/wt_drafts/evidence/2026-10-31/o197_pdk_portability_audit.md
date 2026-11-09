# O-197 PDK 이식성 전수 감사 (원칙 19) -- 2026-10-31

감사자 = 읽기 전용(저장소·git 쓰기 0). 원칙: 루트 CLAUDE.md 원칙 11(O-197) -- PDK 양은 역할 이름으로만, 특정 PDK의 값·규칙 번호·파일 줄은 PDK 선언(pdk_decl) 한 곳에만. ★graph 단일 정본(선언 = 정본 자리 하나). as-built 엔진 인용은 재작성 범위 사실로만(원칙 8).

## 0. 대상 기준점(실측)

| 대상 | 경로 | 기준 커밋 |
|---|---|---|
| 계획 | `wt/plan-v6386/docs/01-plan/features/*.plan.md` | **f6d85ac0**(브리핑의 fa97df83 뒤에 여덟째 커밋이 들어옴 -- 일곱째 커밋 자리(DEC-79 C 면적 식·N3.16 MIM 배열 항목·O-195 행·Status)를 이미 역할 이름으로 고침. 아래 행 번호는 f6d85ac0 기준) |
| design | `wt/design-v115/docs/02-design/features/*.design.md` | e957ba44 |
| 엔진·test·도구·assets | `chip-design-skills` master | 325ee241 |

검색 패턴(grep/python, 스크립트 = scratchpad `ctx.py`·`ln.py`): `sky130*`, `capm.*`, `poly.N`, `difftap.N`, `licon.N`, `nwell.N`, `camimc`, `cpmimc`, `cap_mim*`, `C:/pdk*`, `*fet_01v8*`, `res_*_po`, `MANUFACTURINGGRID`, `tlef`, `1.8 V`, PDK 숫자(0.42 µm, 0.36 µm, 0.15 µm, 5e-9, 2.00e-15, 100 µm, 2.8e-7 등).
계획 hit: gain-budget 57행, offset-trim 8행, oracle-portability 43행, 나머지 9개 계획 0. design hit: 40-engine 17, 41 9, 42 2, 10-test 3, offset-trim 3, oracle-portability 34, 나머지 0.

분류: (a) PDK 선언 안(허용) (b) 선언을 역할 이름으로 READS·사례 표지(허용) (c) 계획·design 문언에 PDK 고유 이름·값 직접(정정 대상) (d) 엔진·test·도구 코드에 PDK 고유 리터럴(재작성 범위) (e) 경위·기록·결정 원문·실측 사실 행(그대로) (4) spec·topology 회로 데이터의 PDK 고유 값(별도 분류).

## 1. 분류별 건수

| 분류 | 건수 | 비고 |
|---|---|---|
| (a) 선언 안 | 파일 2 (+ LUT 데이터 선언 2) | `assets/sky130_pdk_decl.json`(sources 9, quantities 72, mismatch_models, resistor_types), `assets/sky130_lut_rule_decl.json`(lut_diffusion_* 4). LUT 데이터 선언 `assets/lut_v2_location.json`·`assets/sky130_lut_L_grid.json` |
| (b) 역할 이름 READS·사례 표지 | 엔진 소비자 전부 + 계획·design 약 30행 | 엔진: `area_decl.py:21` `CAP_DENSITY_QUANTITY`, `layout/contract_input.py:43,45` `PDK_RULE_QUANTITIES`·`GRID_QUANTITY`, `junction_<kind>_*`, `noise_ef_<kind>`, `mismatch_models`, `poly_res_*`(resistor_types가 `selected_as` 로 냄). 문서: offset-trim T-31·NFR-T7, oracle-portability '사례: sky130' 표지 |
| (c) 계획·design 정정 대상 | **계획 24행 + design 16행 = 40** | §2 목록 |
| (d) 엔진 코드(test 밖) | 코드 6 + 구조 3 + 주석 약 17 | §3.1 |
| (d-test) test 코드 | 7 묶음(파일 기준 30·18·15·11·5·1·약 12) | §3.2 |
| (d-tool) 도구 | 3 | §3.3 (oracle-portability F-11·F-14·D-2/OP-8이 이미 범위로 가짐) |
| (e) 기록 | 계획 약 75행(gain-budget 약 33, offset-trim 2, oracle-portability 약 40), design 약 35행 | 결정 행(O-·U-·Q- '결정됨' 원문), 실측 사실, as-built 인용, sha 대상 목록 |
| (4) spec·topology | 계획 7행 + library 13 파일(heldout 0) | §4 |

## 2. (c) 정정 대상 목록

열: 자리 / 지금 문언(요지) / 역할 이름 제안 / 선언에 있음? (없음 = 선언 항목 추가 필요 -- card 몫은 정하지 않음, ★표지)

### 2.1 계획 `gain-budget-gmid-sizing.plan.md` (f6d85ac0)

| # | 행 | 지금 문언 | 역할 이름 제안 | 선언 |
|---|---|---|---|---|
| P1 | 2248 (N6.28 SF-1 범위 9) | `C_min = camimc·w² + 4·cpmimc·w, w = capm.1`; `assets/sky130_pdk_decl.json` `poly_res_params` note; `C:/pdk/sky130_fd_pr/cells/res_high_po/`·PDK 커밋 `f62031a`; `res_high_po`; `cells/res_high_po/sky130_fd_pr__res_high_po_0p35.model.spice`; 'sky130 선언에서는 generic R_min = 0' | 'PDK 최소 MIM 용량(선언 양) = MIM 면적 밀도·MIM 둘레 밀도·MIM 최소 폭에서 선언 식으로'; '정밀 poly 저항 후보(선언 `resistor_types` 후보 하나: 시트 저항·최소 폭·머리 면적)'; 셀 파일 = 선언 `sources` 항목 | ★MIM 최소 폭 없음, ★MIM 둘레 밀도 없음, ★최소 MIM 용량 없음, ★정밀 저항 후보 없음(후보는 `poly_generic` 하나). MIM 면적 밀도 = 있음(`mim_cap_density_f_per_m2`) |
| P2 | 1026 (N3.16 PDK 상수 행) | 'sky130: `C:/pdk/sky130_fd_sc_hd/tech/sky130_fd_sc_hd.tlef`', '`min_finger_w` = difftap.2', 'MiM 최소 폭 capm.1(로컬 원본 = `C:/pdk/open_pdks_sky130_magic/sky130.tech` 5104행, open_pdks 커밋 `61a056e1` ... `periphery.csv:745`는 N/A)', 'capm.1 선언 항목(`assets/sky130_pdk_decl.json`)' -- 여덟째 커밋은 같은 행의 배열 간격·감싸기만 고침 | 제조 격자 `manufacturing_grid_m`, 최소 finger 폭 `min_finger_w_m`, MIM 최소 폭(역할), 'PDK 선언 파일' | grid·min_finger = 있음; ★MIM 최소 폭 없음 |
| P3 | 296 (DEC-96 (2)) | `sky130_fd_pr__{n,p}fet_01v8__mismatch.corner.spice`, A_VT = √2·`vth0_slope`, A_β = √2·`toxe_slope`, 'pfet L < 0.5 µm는 `vth0_slope1` = 7.356e-3', `.option scale=1.0u` | 'PDK 선언 mismatch 모델(kind별 모델 원본·slope 원본·변수 목록)', 'bin별 slope(선언이 블록마다 읽음)', 'mismatch 기하 단위 `mismatch_slope_geometry_unit_m`' | 있음(`mismatch_models`, `mismatch_slope_geometry_unit_m`) |
| P4 | 1036 (N3.16 PDK 추가 양) | `mim_cap_density_f_per_m2`(`camimc`), 잡음 `ef`, slope 이름 `vth0_slope`/`vth0_slope1`·`toxe_slope`/`toxe_slope1`·`voff_slope`·`nfactor_slope` | 역할 이름만(괄호의 모델 파라미터 이름 삭제 -- 선언 `expression`이 정본) | 있음 |
| P5 | 278 (DEC-79) | '`mim_cap_density_f_per_m2`(PDK `camimc`)' | 'MIM 면적 밀도 `mim_cap_density_f_per_m2`' | 있음 |
| P6 | 304 (DEC-105 (2)) | 슬라이스 폭 '0.42·0.55 µm; nfet 0.36·0.39 µm는 W_min 0.42 µm 아래', 읽는 열 원본 '`lut_data/sky130_lut_v2/*__W*um_dc.npz`'·생성기 `sky130_dc_width_slices.py`·`assets/sky130_lut_sweep.py`, '(PDK 선언 `manufacturing_grid_m`, `assets/sky130_pdk_decl.json`)', '공급 1.8 V' | 'LUT 위치 선언의 W 슬라이스 파일', '`min_finger_w_m` 아래 슬라이스', 'PDK 선언 `manufacturing_grid_m`', '공급 = spec `supplies_v`' (폭 숫자는 검증 실측 기록으로 history·evidence로) | 있음(LUT 위치 선언·grid·min_finger) |
| P7 | 733 (LR3) | 'bin 지도는 PDK 모델 파일(`sky130_fd_pr__{nfet,pfet}_01v8__<corner>.pm3.spice`의 `.model` 블록 `lmin`/`lmax`)' | 'PDK 선언 모델 카드 원본(kind별)의 bin 경계' | 부분: 모델 카드 원본은 `sources`에 있음(mismatch_models.model_source). ★'bin 지도 원본' 역할을 이름으로 따로 둔 항목은 없음(LUT 쪽은 슬라이스 meta 경로로 읽음) |
| P8 | 738 (LR8) | 'sky130 선언: 간격 규칙이 L과 무관하고 고정 poly pitch가 없어 행 안 L 혼재는 DRC 제약이 아니다', 'finger 폭 < sky130 최소폭' | 'PDK 선언에 L 의존 간격·고정 poly pitch 규칙이 없으면 행 안 L 혼재 허용'(조건으로), '`min_finger_w_m`' | ★없음: '고정 gate pitch / L 의존 간격' 역할(없음을 명시하는 항목 포함). 다른 PDK(고정 pitch FinFET 등)에서 규칙이 바뀌는 자리 |
| P9 | 1355 (T4-pre) | '`assets/sky130_lut_sweep.py` `DUT_LINE`(W = 5 µm 기준 ad = as = 2.5e-12 m² ... pd = ps = 7e-6 m)' | 'LUT 생성 규칙 선언의 확산 기하 `lut_diffusion_ad_per_w_m`·`_as_per_w_m`·`_pd_extra_m`·`_ps_extra_m`' | 있음(`sky130_lut_rule_decl.json`) |
| P10 | 1178 (N5.3 Q-2, 열림) | '`res_high_po` 머리 면적 기하 식 ratify(`assets/sky130_pdk_decl.json:5` note)' | '정밀 poly 저항 후보의 머리 면적 식' | ★없음(P1과 같음) |
| P11 | 2128 (D1 행) | 'MIM 2.00e-15 F/µm² `assets/sky130_pdk_decl.json`' | 'MIM 면적 밀도(선언)' -- 숫자는 evidence 인용으로 | 있음 |
| P12 | 2402 (DR-1 범위) | 소신호 스탬프 정의 원본 '`lut_data/sky130_lut_v2/*__W*um_dc.npz`, 생성기 `wt/_drafts/engine/lut_slices/sky130_dc_width_slices.py`', '`assets/sky130_lut_sweep.py:78`' (같은 행의 sky130 실측 수치는 (e)) | 'LUT 위치 선언의 W 슬라이스 DC 열', 'LUT 기준 폭 표' | 있음 |
| P13~P19 | 189 (NFR-5), 278 (DEC-79 ×2), 279 (DEC-80), 294 (DEC-95), 756 (층 0 표), 1052 (LY1), 1236 (단위 0), 1320 (완료 0) | 'PDK `MANUFACTURINGGRID`', 'tlef `MANUFACTURINGGRID`' | '제조 격자 `manufacturing_grid_m`(PDK 선언)' -- LEF 표준 키워드라 낮은 우선순위지만 규칙이 원본 형식(tlef)에 묶임 | 있음 |

### 2.2 계획 `offset-trim.plan.md`·`oracle-portability.plan.md`

| # | 행 | 지금 문언 | 역할 이름 제안 | 선언 |
|---|---|---|---|---|
| P20~P22 | offset-trim 492, 533, 549 | 선행 조건 'OP-6 능력 기록(sky130)', '그 계획의 능력 확인 card가 만든 sky130 능력 기록' | '현재 PDK 기술자의 능력 기록' (sky130은 사례 표지로) | 해당 없음(오라클 기술자 몫) |
| P23 | oracle-portability 551 (완료 8a) | '`E/`와 `A/sky130_pdk_decl.json`의 git diff 0' | '엔진 PDK 선언 파일' | 해당 없음 |
| P24 | oracle-portability 260 | 확산 규칙 입력 '`A/sky130_lut_rule_decl.json`' | 'LUT 생성 규칙 선언' | 있음 |

### 2.3 design

| # | 자리 | 지금 문언 | 역할 이름 제안 | 선언 |
|---|---|---|---|---|
| D1 | 40-engine:879 (§3.1-1 (a)) | 'C_min = camimc·w² + 4·cpmimc·w, w = capm.1' | P1과 같음 | ★없음(MIM 최소 폭·둘레 밀도·최소 MIM 용량) |
| D2 | 40-engine:1703 (§7.1) | 'capm.1 -- O-177; 로컬 원본 = `C:/pdk/open_pdks_sky130_magic/sky130.tech` 5104행, open_pdks 커밋 `61a056e1` ... `periphery.csv:745`는 N/A' | 'MIM 최소 폭(선언 항목, 출처 칸에 원본·줄)' | ★없음 |
| D3 | 42-gap:342 (D-TBX) | 'camimc·w² + 4·cpmimc·w, w = capm.1' | P1과 같음 | ★없음 |
| D4 | 40-engine:1699 | '원본은 `C:/pdk/sky130_fd_pr/models/r+c/res_typical__cap_typical__lin.spice`의 `camimc`' | 'MIM 면적 밀도 `mim_cap_density_f_per_m2`(선언 원본 칸)' | 있음 |
| D5 | 40-engine:1707 | 'R_□는 `C:/pdk/sky130_fd_pr/models/r+c/res_typical__cap_typical__lin.spice`의 poly 저항 시트 파라미터 ... periphery rules의 poly 저항 항목' -- 덧붙여 **사실 어긋남**: 선언 `poly_res_params` 원본은 `res_typical__cap_typical.spice`(lin 아님, `rp1`) | '선언 저항 후보의 `sheet_ohm_per_sq`·`min_w_m`·`head_area_m2`(→ `poly_res_*`)' | 있음 |
| D6 | 40-engine:1374 | 'dummy = `poly.1a + poly.7 + overhead/2`' | '`dummy_w_m`(선언 식)' | 있음 |
| D7 | 40-engine:1369 | '선언 파일은 `assets/sky130_pdk_decl.json`' | 'PDK 선언 파일(사례: sky130)' | 있음 |
| D8 | 40-engine:1169, 41:1432 | '제조 규칙 difftap.2 밖 손가락', 'nfet 0.36·0.39 µm 슬라이스는 읽지 않음' | '`min_finger_w_m` 밖 손가락' | 있음 |
| D9 | 40-engine:2095 | '접합 기하 = `assets/sky130_lut_sweep.py` `DUT_LINE`의 확산 기하 규칙' | '`lut_diffusion_*`(LUT 생성 규칙 선언)' | 있음 |
| D10 | 41:1621 (§6.4 slope 출처) | 'PDK `C:/pdk/sky130_fd_pr/cells/{nfet,pfet}_01v8/sky130_fd_pr__*_01v8__mismatch.corner.spice`를 파싱' | '선언 `mismatch_models.<kind>.slope_source`' | 있음 |
| D11 | 40-engine:1290 | '`MANUFACTURINGGRID × max(...)`' | '`manufacturing_grid_m` × ...' | 있음 |
| D12 | 40-engine:1608 | 'sky130 subckt 인자 sa/sb/sd, 모델의 `lod.spice`·`saref`/`sbref`' | '오라클 기술자의 LOD 인자 역할' | 해당 없음(★오라클 기술자 쪽 역할 -- 엔진 선언 밖) |
| D13 | offset-trim.design:129 | '꺼진 스위치 VGS는 음수인데 LUT VGS 축은 0~1.8 V' | 'LUT VGS 축 범위(LUT 데이터)' | 있음(LUT 축) |
| D14 | offset-trim.design:848 | 'OP-6이 만든 sky130 능력 기록' | P20과 같음 | 해당 없음 |
| D15 | oracle-portability.design:1447 | '`A/sky130_pdk_decl.json` diff 0' | '엔진 PDK 선언 파일' | 해당 없음 |
| D16 | 40-engine:1203 · 계획 2316 (as-built 인용) | '`E/metrics/device_sigma.py:17-31`(ceil(W/100 µm) 분할)' -- 코드는 100을 박지 않고 모델 블록 `wmax`에서 읽음(§3.1 확인) | '모델 bin 최대 폭(`wmax`)' -- 재작성 범위 인용이라 (e)에 가깝지만 숫자가 규칙처럼 읽힘 | 있음(mismatch_models 블록 wmax) |

(e)로 둔 대표 행: 계획 164·303·380·393·408·410·1185·1187·1188·1190(Q-CB 결정 전 문언 -- C_min 식·파일 7-8행 포함)·2493~2630 U 행(U-27·U-30·U-36 등 닫힌 결정 원문)·1674·1682(sha 대상 파일 목록)·1002·1025(옛 키 `sky130_supplies_v` -- 이관 대상 이름), design 40:1371(실측 sky130 값)·1488·1861, 41:580·598·1861, oracle-portability design §10.3(사례 값 -- 정본은 기술자 파일).

## 3. (d) 엔진·test·도구 -- 재작성 범위 사실

### 3.1 엔진 코드(test 밖, master 325ee241)

숫자 PDK 리터럴 grep(1.8, 0.42, 0.36, 0.15, 5e-9, 2e-3, 100e-6 등): **0건**. 규칙 번호를 값으로 쓰는 코드 0건(전부 선언 READS). 남는 것:

| # | 자리 | 내용 | 분류 |
|---|---|---|---|
| E1 | `gmid_engine/core/pdk_decl.py:47` | `_SLOPE_REF = re.compile(r"([A-Za-z_][A-Za-z0-9_]*_slope[0-9]*)\s*/\s*sqrt")` -- mismatch slope 참조를 sky130 모델 카드 꼴(`<이름>_slope[N] / sqrt(...)`)로만 찾음. oracle-portability 계획 G-16 (c)가 이미 지적 | (d) ★선언 역할 'mismatch slope 참조 꼴' 없음 |
| E2 | `gmid_engine/lut/mismatch_sigma.py:57` | `scale = math.sqrt(sens.w_m / W)` -- 면적 지수 −1/2(Pelgrom). 물리 법칙이라 조건부 허용이나 PDK 카드 꼴 전제(G-16 (a)) | (d) 조건부 |
| E3 | `gmid_engine/core/pdk_decl.py:46` | `_BOUND_KEYS = ("lmin","lmax","wmin","wmax")` -- BSIM bin 키워드(형식 키워드) | (d) 낮음 |
| E4 | `gmid_engine/lut/table_cache.py:48` | `_CONFIG_NAME = "lut_v2_location.json"` -- 엔진이 LUT 묶음 선언 파일 이름을 박음(PDK를 바꾸면 LUT 묶음도 바뀜) | (d) |
| E5 | `gmid_engine/lut/provenance.py:51` | 사용자 문구 'sky130_lut_sweep.py로 재생성하면 기록된다' | (d) 낮음 |
| E6 | `gmid_engine/search/search_domain.py:114` | 주석 '커패시터 상자는 PDK 선언에서 유도할 수 없다(capm.* 규칙값 N/A, cap_mim 셀 원본 없음)' -- O-177 뒤 사실과도 어긋남 | (d) 낮음(주석) |
| S1 | `gmid_engine/lut/lut_types.py:44-45,55` `LutSpec.manufacturing_grid_m`·`min_finger_w_m` 대 PDK 선언 `manufacturing_grid_m`·`min_finger_w_m` | **같은 이름 둘째 보유자**. grid는 `layout/contract_input.py:158-162`가 1 ulp 대조로 같게 강제(둘째 사본), `min_finger_w_m`은 **정의가 다름**: LutSpec = kind별 최소 슬라이스 폭(nfet 0.36 µm -- test 조립부가 manifest에서 계산), 선언 = difftap.2(0.42 µm). graph 단일 정본 규칙 3(같은 이름 = 같은 정의) 위반 후보 | (d) 구조 |
| S2 | 엔진에 PDK 선언 → LutSpec 조립 자리(실행 진입점)가 없음 | `grep "LutSpec("` test 밖 0건. 조립은 test 12곳 이상이 각자 함(§3.2) -- PDK 선택(선언 경로)·kind 지도·grid가 test마다 박힘 | (d) 구조 |
| S3 | `core/pdk_decl.py:458-486` `_quantity` + 형식 4종(`lef_statement`·`rule_table_csv`·`spice_model_card`·`spice_instance_line`) | 양 하나 = 원본 하나. (i) capm.1·2a·3 원본 `C:/pdk/open_pdks_sky130_magic/sky130.tech`(5104·5105·5113행 실측)은 magic DRC tech 형식이라 **읽을 형식이 없음** (ii) 최소 MIM 용량(면적 밀도·둘레 밀도는 r+c 파일, 최소 폭은 tech 파일)은 **원본 둘을 걸치는 식이라 선언 불가**. 선언 항목 추가 전에 로더 확장(형식 또는 양 사이 식)이 필요하다는 사실 | (d) 재작성 범위 |
| S4 | assets 선언 셋의 `pdk_root` | `sky130_pdk_decl.json` `"C:/pdk"`, `sky130_lut_rule_decl.json` `"C:/pdk/sky130_fd_pr"`, `lut_v2_location.json` `pdk_root.default "C:/pdk/sky130_fd_pr"` -- PDK 루트가 세 자리 | (a) 안이지만 선언 한 곳 원칙과 어긋남 |

주석 수준(재작성 때 함께, 우선순위 낮음, 약 17행): `core/pdk_decl.py:7-8`(예시), `lut/lut_types.py:44-45`, `layout/area_tie.py:5`, `layout/contract_input.py:15`, `layout/w_tolerance.py:7`, `search/constraints.py:6`, `search/search_domain.py:20`, `search/search_values.py:79`('difftap.2'), `search/search_context.py:4`, `search/area_decl.py:21`, `metrics/device_sigma.py:18`('sky130 은 W ≤ 100 µm' -- 값은 모델 블록에서 읽음), `lut/mismatch_set.py:6`, `lut/noise_set.py:6`, `lut/_helpers_bins.py:4`, `metrics/junction_cap.py:8`(대조 기록 -- (e)). 엔진 CONTRACT.md: core 9.4 'sky130 실값' 표·9.4b, layout 236-243·404-408, lut 241-982, metrics 379-1149, search 34·764, sizing 677·906 -- 사례 값·실측 기록((e)), 단 layout CONTRACT 404-408은 dummy 식 타당성을 sky130 값(0.28 ≥ 0.21 µm, lvt pfet 한계)으로 논증 -- 다른 PDK에서 다시 따질 자리.

### 3.2 test 코드(`gmid_engine/tests`)

| # | 내용 | 규모 | 비고 |
|---|---|---|---|
| T1 | 소자 kind 지도 `(("nfet_01v8","nmos"),("pfet_01v8","pmos"))` 박음 | 30 파일 | ★선언 역할 '소자 kind 지도' 없음 |
| T2 | PDK 선택 = `assets/sky130_pdk_decl.json` 경로 박음 | 18 파일 | 실행 설정 한 자리 없음(S2) |
| T3 | `LutSpec(float(man.get("manufacturing_grid_m", 5e-9)), ...)` -- sky130 격자 값 5e-9 대체값 + 격자를 LUT manifest에서 읽음(PDK 선언 아닌 둘째 생산자) | 15 파일 | 예: `integration/test_g10_no_recompute_9circuits.py:59`, `test_s0_layer_9circuits.py:96` |
| T4 | tlef 기본 경로 `C:/pdk/sky130_fd_sc_hd/tech/sky130_fd_sc_hd.tlef` + `MANUFACTURINGGRID` 정규식 재파싱(선언 로더 밖 둘째 생산자) | 5 파일 | `generality/pipeline.py:48,74-77`, `lut/conftest.py:41,1179`, `sizing/conftest.py:296,317`, `layout/test_run.py:522,606` |
| T5 | 손 기대값 `GRID, WMIN = 5e-9, 4.2e-7` ('손: PDK 격자·최소 폭') | 1 파일 | `integration/test_nfr4_compare.py:21,197-198` |
| T6 | 용량 열 접미사 `CAP_SUFFIX = (("nmos","_n"),("pmos","_p"))` | 11 파일 | LUT 데이터 형식(PDK 선언보다는 LUT 위치·meta 역할) |
| T7 | LutSpec `min_finger_w_m` = manifest 최소 슬라이스 폭(`generality/pipeline.py:80-86` 등) | 조립부 약 12 | S1의 다른 정의 |
| 허용 | `core/test_pdk_decl.py`(`needs_sky130` skip)·`search/test_area_decl.py:175`(camimc 원본 직접 파싱 -- 선언 독립 검증) | -- | sky130 사례 test로 표지돼 있음 -- (a)/(e). 토이 값 단위 test(`layout/test_area_tie.py` 등의 5e-9)는 토이 PDK라 허용 |

### 3.3 도구

| # | 자리 | 내용 |
|---|---|---|
| X1 | `tools/spice_oracle/legacy_adapter.py:27,48` | LUT 생성기 `assets/sky130_lut_sweep.py`의 공개 상수(PDK_ROOT·LOD_SPICE·NGSPICE_EXE)를 정규식으로 읽음 -- oracle-portability F-11 범위 |
| X2 | `assets/sky130_lut_sweep.py`(1205줄)·`assets/sky130_pair_mc.py` | sky130 경로·이름·코너 `tt` 고정 -- oracle-portability F-14, D-2(OP-8) 범위. `sky130_lut_rule_decl.json`이 sha256으로 묶음 |
| X3 | 나머지 oracle 모듈 | `oracle_simulate.py`·`oracle_offset_mc.py`·`oracle_compare.py` hit은 일반 `.include/.lib`·주석 실측 문구뿐 -- (e) |

## 4. (4) spec·topology 회로 데이터

* library 13 파일 중 sky130 언급 파일: sizing_spec 4(cnr_ota 23·r2r_opamp 5·erfc_ota 1·rfc_ota 1), topology 다수(`_cell` 주석 'sky130 nfet_01v8' 등 -- 주석). heldout 0.
* 공급 `supplies_v` 1.8 V(원문 인용) -- 회로 spec(계획 700·1330·2111~2122·2252 행 포함). PDK 값이 아니라 회로 선언.
* **표지**: `cnr_ota.sizing_spec.json` 저항 6개(`x3`·`x37`~`x40`·`x9`) `value_ohm`은 sky130 `res_high_po` 셀 모델 식(rsheet 317.3885·rhead 345.8312·tc 계수)으로 손계산한 값(`kind: user_spec`, 2026-10-14 D-R). 회로 원문 기하(W/L)에서 PDK로 유도한 값이라 PDK를 바꾸면 값의 근거가 사라진다 -- spec 값으로 남길지, 원문 기하 + PDK 저항 후보에서 유도할지는 회로 데이터 결정(사용자 몫).

## 5. 선언에 없는 역할 목록(★ -- 선언 항목 추가가 필요, card 몫은 정하지 않음)

| # | 역할 | 쓰는 자리 | 원본 사실(실측) | 막힘 |
|---|---|---|---|---|
| R1 | MIM 최소 폭 | 계획 N6.28 SF-1 범위 9·N3.16, design 40 §3.1-1 (a)·§7.1, 42 D-TBX | `C:/pdk/open_pdks_sky130_magic/sky130.tech:5104` `width *mimcap 1000 ... (capm.1)` | S3 (i) 형식 없음 |
| R2 | MIM 둘레(가장자리) 용량 밀도 | 같음, Q-CB3 둘레 항 | 선언 `mim_cap_params` 원본과 같은 r+c 파일(`cpmimc`) -- 지금 `line_pattern`이 `camimc` 줄만 | 형식은 있음(원본 항목 하나 더) |
| R3 | MIM 배열 간격 | 계획 DEC-79 C 면적 식·LY12 | `sky130.tech:5105` `spacing ... 840 ... (capm.2a)` | S3 (i) |
| R4 | MIM 감싸기 폭(아래 금속) | 같음 | `sky130.tech:5113` 'Metal3 must surround MiM cap ... (capm.3)' | S3 (i) |
| R5 | PDK 최소 MIM 용량 | 보상 C 하한 | R1·R2·면적 밀도의 식 | S3 (ii) 원본 걸침 식 불가 |
| R6 | 정밀 poly 저항 후보(시트·최소 폭·머리 면적) | 계획 SF-1 범위 9·Q-2 | `C:/pdk/sky130_fd_pr/cells/res_high_po/`(계획 기록) | 머리 기하 식 ratify(Q-2) |
| R7 | 소자 kind 지도(PDK 소자 셀 이름 ↔ 엔진 kind) | test 30 파일(T1), LUT manifest `device` | LUT manifest 키 `nfet_01v8`·`pfet_01v8` | 엔진 실행 진입점 없음(S2) |
| R8 | 고정 gate pitch·L 의존 간격 규칙 유무 | 계획 LR8 근거 | sky130은 없음(계획 738 문언) | 없음을 명시하는 항목 꼴 필요 |
| R9 | mismatch slope 참조 꼴 | 엔진 E1 | sky130 카드 `<변수>_slope[N] / sqrt(l*w*mult)` | 선언 키 추가 + 로더 |
| R10 | PDK 루트 한 자리 | S4 | 선언 셋에 세 값 | 선언 구조 결정 |
| (참고) | LOD 응력 인자 이름(sa/sb/sd) | design 40:1608 | 오라클 기술자 쪽 | 엔진 선언 밖 |

있는 역할(대조 완료): `manufacturing_grid_m`, `min_finger_w_m`, `mim_cap_density_f_per_m2`, `finger_pitch_overhead_m`, `row_gap_m`, `dummy_w_m`, `tap_w_m`, `well_spacing_m`, `junction_{nmos,pmos}_*` 28×2, `noise_ef_*`·`noise_fnoimod_*`·`noise_tnoimod_*`, `mismatch_slope_geometry_unit_m`, `mismatch_models`, `poly_generic_*` → `poly_res_*`(`resistor_types.selected_as`), `lut_diffusion_*` 4(LUT 생성 규칙 선언).

## 6. 우선순위

1. **최우선(다음 card가 바로 쓰는 자리)** -- SF-1 범위 9 계열: 계획 P1(2248)·P2(1026)·P10(1178), design D1(40:879)·D2(40:1703)·D3(42:342). 역할 R1~R6이 선언에 없고, 엔진 로더가 그 원본 형식(magic tech)과 원본 걸침 식을 못 읽는다(S3). 지금 문언대로 구현하면 card가 sky130 규칙 번호를 엔진·test에 옮길 위험이 크다. 계획 문언을 역할 이름으로 고치고, 선언 항목 + 로더 확장이 필요하다는 점을 계획에 표지해야 한다.
2. **엔진 구조(graph 단일 정본과 겹침)** -- S1(LutSpec `manufacturing_grid_m`·`min_finger_w_m` 둘째 보유자·다른 정의), T3·T4(격자 둘째 생산자 + 5e-9 리터럴), S2·T1·T2(PDK 선택·kind 지도가 test 30곳에 박힘 → R7).
3. **계획·design 규칙 문언의 모델 파라미터·파일 이름** -- P3(DEC-96 (2)), P7(LR3), P8(LR8 -- R8, PDK가 바뀌면 규칙 자체가 바뀌는 자리), P6(DEC-105), P4·P5·P9·P12, D4~D10. 역할은 R8을 빼고 이미 선언에 있으므로 문언만 고치면 된다.
4. **엔진 형식 전제** -- E1(R9)·E2·E4.
5. **낮음** -- `MANUFACTURINGGRID`·tlef 문언(P13~P19, D11), offset-trim·oracle 완료 조건 문언(P20~P24, D14·D15), 엔진 주석(E5·E6·§3.1 주석 목록), S4(R10).

## 7. 덧붙인 사실(감사 중 발견)

* 계획 HEAD가 감사 중 fa97df83 → f6d85ac0으로 바뀌었다(여덟째 커밋: O-197 일곱째 커밋 자리 적용). 위 목록은 f6d85ac0 기준이다. 여덟째 커밋은 DEC-79 C 면적 식·N3.16 MIM 배열 항목·O-195 행·Status만 고쳤고, 같은 N3.16 행의 capm.1·tlef 경로·difftap.2(P2)와 SF-1 범위 9(P1)는 그대로 남아 있다.
* design 40:1707은 poly 시트 저항 원본을 `res_typical__cap_typical__lin.spice`라고 적었으나, 선언 `poly_res_params`는 `res_typical__cap_typical.spice`(`rp1`)를 읽는다(문언 사실 어긋남).
* design 42-gap:242 D-RA '`rg "poly_res_sheet"` 0'은 낡았다. 엔진은 `resistor_types.selected_as = "poly_res"`로 `poly_res_sheet_ohm_per_sq` 등을 만들어 낸다(`core/pdk_decl.py:550-584`).
* oracle-portability 계획·design은 처음부터 '사례: sky130' 표지 규칙(T-31·NFR-T7)으로 써 있어서 (c)가 적다(4건, 모두 낮음).
