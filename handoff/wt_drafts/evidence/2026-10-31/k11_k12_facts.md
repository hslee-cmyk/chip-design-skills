# K11·K12 실측 사실·대안·권고 (분석자, 읽기만)

- 작성 2026-10-31. 기준: master `325ee241`(엔진), 계획 v6.38.6 worktree `wt/plan-v6386` HEAD `b1d23b09`(아홉째 커밋).
- 엔진 인용 용도: 원칙 8의 (1) 엔진 밖 사실(PDK·LUT 값)과 (2) 재작성 범위(지울·바꿀 코드, 소비자 목록)로만 쓴다. as-built 구조는 근거로 쓰지 않는다.
- 저장소·git 쓰기 0. 이 파일만 썼다.

---

## K11. `min_finger_w_m` 두 정의

### 1. 사실(실측)

**1.1 보유자 둘**

| 보유자 | 정의 | 값(sky130) | writer | 근거 |
|---|---|---|---|---|
| PDK 선언 `assets/sky130_pdk_decl.json:98-102` | 제조 규칙 difftap.2 '최소 채널 폭'(areaid.sc 밖 FET) | 0.420 µm(n·p 공통 스칼라) | core `read_pdk_decl`(선언 → 규칙표 파싱) | 원본 `C:/pdk/skywater-pdk/docs/rules/periphery/periphery.csv:321`(difftap.2 0.420), `:323`(difftap.2b, areaid.sc 안 0.360) |
| `LutSpec.min_finger_w_m` `gmid_engine/lut/lut_types.py:45,53` | 칸 docstring은 "`widths()`의 하한(PDK difftap 규칙)", lut CONTRACT 1.1은 "부르는 쪽이 PDK 선언에서 채운다" | test 조립부가 넣는 값 = **kind별 LUT 최소 슬라이스 폭**(nmos 0.36 µm, pmos 0.42 µm) | 엔진 안 writer 없음. `LutSpec(` 생성 자리는 test 밖 0건(S2). test 39곳이 조립한다: 실제 LUT 19 파일(`sorted(mins.items())` -- manifest 슬라이스 W 최솟값), toy 20곳(1e-6·1.5e-6 등) | `gmid_engine/tests/generality/pipeline.py:85-100` 등. 이 관례는 `lut_data/sky130_lut_v2/REGEN_REPORT.md:78`에 처음 기록됐다("kind별 최소 슬라이스 폭(nmos 0.36 µm, pmos 0.42 µm) ... 엔진 test conftest와 같은 구성") |

- 엔진 문언(docstring·CONTRACT)은 두 칸을 모두 "PDK difftap 규칙"이라고 적는다. 정의가 갈라진 곳은 test 조립부뿐이다. 다만 엔진에 조립 진입점이 없어서(S2) 실제로 돌아가는 값은 언제나 test가 넣은 값이다.

**1.2 두 값이 다른 물리 이유**
- LUT 폭 슬라이스 집합은 PDK 모델 bin의 `wmin` 집합이다. 슬라이스 생성기 `lut_data/sky130_lut_v2/verification/slices_vdsat/sky130_dc_width_slices.py:11-14,100-109`가 이를 만들고 `bins.csv`의 W 집합과 대조한다.
- nfet bin에는 0.36·0.39 µm가 있다(`C:/pdk/sky130_fd_pr/cells/nfet_01v8/sky130_fd_pr__nfet_01v8.bins.csv` W 열). 이 폭은 표준셀 안 FET(difftap.2b 0.36 µm)용 특성화 폭이다. pfet의 최소 bin은 0.42 µm다.
- 즉 '슬라이스 최솟값'은 모델이 유효한 범위다. 제조 가능한 폭이 아니다.
- 계획 U-30(닫힘, 계획 2487행)이 이미 이렇게 판정했다: "로컬 bins.csv(nfet W ≥ 0.36, pfet W ≥ 0.42)는 모델 유효 범위이지 DRC가 아니다".

**1.3 소비자 전수(재작성 범위)**

| 소비자 | 읽는 칸 | 하는 일 | 물리적으로 필요한 정의 |
|---|---|---|---|
| `lut/widths.py:14` `widths(lut, kind)` | `LutSpec.min_finger_w_m` | finger_w 후보 슬라이스를 `w_key·grid ≥ w_min`으로 거른다 | **제조 규칙**. 슬라이스 범위로 거르면 항등 필터가 된다(모든 슬라이스가 통과하므로 정의역 정보가 0) |
| ↳ `layout/contract_input.py:151` `LayoutPdk.from_lut` → `slice_width_keys` | widths 결과 | 레이아웃 finger_w 후보 | 제조 규칙(손가락 하나하나가 DRC를 받는다) |
| ↳ `convergence/converge.py:53` `LayoutPdk.from_decl(lut, pdk_decl)` | 위와 같음 | **엔진 실행 경로(MOD8)**. `from_decl`은 선언을 손에 쥐고도 W 하한을 선언에서 읽지 않는다. 격자만 대조한다(`:158-162`) | 제조 규칙 |
| ↳ `layout/run.py:85`, `convergence/{converge,key_exclusion,place_layout,kernel_keys}.py` | `slice_width_keys` | 후보를 좁히고 실현 슬라이스를 고른다 | 제조 규칙 |
| `search/search_domain.py:43` `_PDK_QUANTITIES`, `search/constraints.py:5`(S-18 W ≥ W_min), `search/iv_area.py:9`, `search/search_values.py:38,79`, b_A(`search_domain.py:20`, `metrics/area_lower_bound.py:14`) | **PDK 선언** `min_finger_w_m` | 소자 총 W 하한, 면적 분해능 | 제조 규칙(지금도 선언을 읽는다) |
| 계획 DEC-105 (2)(계획 304행, v6.38.6) "`min_finger_w_m` 아래 슬라이스는 도달하지 않음", 계획 1834행 범위 (5) layout W_min 출처 = `ly_pdk`(`LayoutPdk.from_decl`, "sizing `min_finger_w_m`과 같은 PDK 선언"), design `offset-trim.design.md:210` | PDK 선언 | 손가락 선택·layout W_min 검사(계획만 있고 아직 구현 안 됨) | 제조 규칙 |
| `authoring/_spec_fields.py:54` `min_finger_w` | -- | 옛 spec 키를 거부하는 목록 | 해당 없음 |

**1.4 물리 결함(실측, 위 표에서 나옴)**
- 실제 LUT로 조립한 모든 경로(test 19 파일)에서 엔진 MOD8 경로의 finger_w 후보에 **nfet 0.36·0.39 µm 슬라이스가 들어간다**. 이 폭은 difftap.2(0.42 µm) 위반이다.
- layout·convergence에 손가락 단위 W_min 검사는 따로 없다(`git grep -i "w_min|min_finger" -- layout convergence` 0건).
- search의 W ≥ W_min은 소자 총 W 하한이다. 손가락 폭을 막지 못한다.
- 그래서 지금은 E-0(실현 가능) 관문에 구멍이 있다. 레이아웃이 0.36·0.39 µm 손가락을 고를 수 있다.
- 실제로 고른 점이 있는지는 **미측정**이다(evidence 폴더 grep 0건, 실행하지 않음).
- pfet은 최소 슬라이스가 0.42 µm라 영향이 없다.

**1.5 계획·design 문언**
- 계획 v6.38.6 N3.16 '선언 추가 필요 역할' 행(1039행)의 재작성 범위 표지: "S1 `LutSpec`의 제조 격자·최소 finger 폭이 PDK 선언과 같은 이름의 둘째 보유자이고 최소 finger 폭은 정의가 다름(graph 규칙 3 후보 -- 정의 선택은 결정 후보)".
- 계획 1022행(PDK 상수 한 곳 선언, `min_finger_w` = difftap.2), DEC-80 (i)(최소 finger 폭 = PDK 선언), DEC-105 (2), 1834행 (5)는 모두 PDK 선언 정의를 쓴다.
- 계획·design에 LUT 최소 슬라이스 폭을 쓰는 문언은 0건이다(`LutSpec` 언급은 1039행 표지 하나).
- 엔진 CONTRACT: lut 1.1·1.6, layout 234·266·522(toy `LutSpec`), core 534.

### 2. 대안(graph 규칙 3 기준)

| 안 | 장점 | 대가 | 원칙 |
|---|---|---|---|
| (가) 정본 = PDK 선언. `LutSpec.min_finger_w_m` 칸을 지운다. `widths()`(또는 `LayoutPdk.from_decl`)가 선언값을 READS한다 | 정의 하나·이름 하나. 모든 소비자가 원래 제조 규칙 뜻이다(1.3 표 7/7). E-0 구멍(1.4)이 같은 변경에서 닫힌다. LUT 정의역은 `slice_map` 자체가 이미 정본이라 따로 담을 칸이 필요 없다(슬라이스 밖 폭 → `KeyError`/fail-closed가 이미 있다) | test 조립 39곳과 CONTRACT 5곳을 고친다. **동작 변경**: nfet 레이아웃 후보 20 → 18 슬라이스(0.36·0.39 제외). 13회로 front 변화표가 필요하다. `widths` 인자 또는 `from_lut` 인자가 바뀐다 | 규칙 1·3·4 맞음, 원칙 9 맞음(지우기만 함), O-197 맞음, E-0 맞음 |
| (나) 이름을 둘로 나눈다: PDK `min_finger_w_m` + LUT `lut_min_slice_w_m`(축 = 제조 규칙 대 모델 bin 유효 하한) | 두 양을 모두 남긴다 | LUT 쪽 양의 소비자 = 0(1.3 표 -- 필터로 쓰면 항등이고, 정의역은 `slice_map`이 이미 담는다). 만들고 안 쓰는 칸이다. 그리고 widths 필터를 그 이름으로 옮기면 E-0 구멍이 그대로 남는다 | ⚠ 원칙 9(소비자 없는 필드), 규칙 1(`slice_map`에서 파생되는 둘째 생산자) |
| (다) 현행 유지 | 변경 0 | 같은 이름에 두 정의. 엔진 실행 경로의 손가락 하한이 test 조립 값에 따라 달라진다(1.4 E-0 구멍) | ⚠ 규칙 3, ⚠ E-0, ⚠ 원칙 11(값이 선언 밖 test에서 정해진다) |

### 3. 권고·물리 검증
- **권고 (가)**. 판정: **맞음**(소비자 7/7이 제조 규칙 뜻이라는 것은 실측, 슬라이스 범위 뜻 소비자 0).
- 물리 결정자: 손가락 하나의 최소 채널 폭 = DRC 규칙 difftap.2(E-0 실현 가능)다. LUT 슬라이스 하한은 모델 특성화 범위(표준셀 FET 포함)이고 실현 가능성의 결정자가 아니다.
- 식: `widths = {w_key : w_key·grid ≥ W_min(PDK 선언)} ∩ slice_map`.
- 원문: periphery.csv:321·323, bins.csv, 계획 U-30.
- 실측: 소비자 grep(위 표). nfet 슬라이스 0.36·0.39 존재(manifest 32 슬라이스).
- 같이 볼 것(같은 S1, K11 밖):
  - `LutSpec.manufacturing_grid_m`은 같은 정의의 둘째 보유자다. 지금은 1 ulp 대조로 같게 강제한다(`contract_input.py:158-162`). 규칙 1·4로는 이것도 선언을 READS로 받는 것이 맞다. test T3(manifest 기본값 5e-9)·T4(tlef 재파싱)도 같은 묶음이다.
  - (가)를 실행하는 card가 격자도 함께 맡을지는 card 배정 때 정한다.
- 일반화 메모(원칙 6):
  - PDK 선언은 n·p 공통 스칼라다(sky130 difftap.2가 FET 공통이라 맞다).
  - 소자 종류마다 최소 폭이 다른 PDK가 있으면 선언 쪽을 kind별 이름(`noise_ef_<kind>` 꼴)으로 넓히면 된다.
  - LutSpec의 kind별 tuple이 그 근거가 되지는 않는다.
- 남은 실측(card 완료 조건 후보):
  - (i) 지금 13회로 레이아웃·수렴 결과 가운데 nfet 0.36·0.39 µm 손가락을 고른 점의 수.
  - (ii) (가) 뒤 front 변화표.

---

## K12. cnr_ota 저항 6개

### 1. 사실(실측)

**1.1 원문이 정한 것: 값이 아니라 PDK 셀 기하**
- 원문은 PDF가 아니다. xschem 회로도다.
  - `assets/library/sources/cnr_ota__wulff_2024/CNR_OTA.sch`(sha256 `e989d7de…`, 웹 https://github.com/wulffern/cnr_ota_sky130nm/blob/8c839f7/design/CNR_OTA_SKY130NM/CNR_OTA.sch).
  - 출처 기록 `sources/cnr_ota__wulff_2024/source.md`.
- 저항 인스턴스는 모두 sky130 저항 셀 기호다. Ω 값은 없다.
  - `CNR_OTA.sch:634` x37, `:635` x38, `:642` x39, `:643` x40, `:681` x9 = `SUNTR_SKY130NM/SUNTR_RPPO16.sym`.
  - `:701` x3 = `SUNTR_RPPO4.sym`.
- 셀의 속은 저장소 밖 `wulffern/sun_tr_sky130nm` @`ccd959e`(2024-02-09)에 있다: `sky130_fd_pr__res_high_po W=0.72 L=8.8` 16개 또는 4개 직렬(`cnr_ota.spec_source.md` 4.2절 103행, 판독 기록 `wt/_heldout/D_cnr/D_cnr.flat_lib20240301.json`). sun_tr HEAD는 그 뒤 L=8.96 µm로 바뀌었다.
- 설계자 서술 `CNR_OTA.design.md`:
  - VCM 절은 "The resistors senses the common mode, and the capacitors form a feedforward zero to cancel the pole of the resistor and input capacitance of the VCM OTA"라고 적는다. 즉 기능은 저항**값**(R·C 영점, CM 감지 부하)에 달려 있다.
  - BIAS 절은 "standard bias source"라고만 적는다.
- 같은 원문에서 시험대 부하는 값으로 주어진다: `sim/load.spi:5-8` R1·R2 100k, R3·R4 500k. 이것은 DUT 저항이 아니다.

**1.2 spec `value_ohm` 6개의 현재 출처**(`assets/library/cnr_ota.sizing_spec.json` `human.element_values`)
- x37·x38·x39·x40·x9 = 70134.2 Ω, x3 = 17533.5 Ω.
- 출처 칸: `kind: user_spec`, `origin: drawing`, `decided: 2026-10-14`, record = `user_decisions.md` 372행 D-R "D-R은 승인"(U5 (a) PDK 모델로 계산, U6 (a) 2024-02 세그먼트 L=8.8). citation은 위 .sch 줄과 sun_tr 셀이다.
- 계산 식: res_high_po 셀 모델(`C:/pdk/sky130_fd_pr/cells/res_high_po/sky130_fd_pr__res_high_po.model.spice` 24~54행). rsheet 317.3885, rhead 345.8312, tc1·tc2, dT = 27 − 30 ℃(LUT 측정 온도 27 ℃, 모델 tnom 30), tt 코너.
- 재계산(이 분석): 세그먼트 = 3987.507 + 395.879 = 4383.386 Ω, ×16 = 70134.17, ×4 = 17533.54. **기록값과 일치한다.**
- 값은 **PDK 셀 식과 LUT 측정 온도와 코너**에 묶여 있다. PDK·온도·코너가 바뀌면 근거가 바뀐다.

**1.3 topology 정의**(`cnr_ota.topology.json` `passive_elements[2..7]`)
- `kind: resistor`, `value_ohm: null`, 단자 둘이다. `_cell`은 "SUNTR_RPPO16 = 16 x sky130 res_high_po W=0.72um L=8.8um 직렬", `_value_note`는 "값 정본 = spec element_values(F5)"다.
- topology는 연결만 담는다. 값은 spec이 정본이다.

**1.4 같은 부류인데 감사(§4)가 빠뜨린 것**
- spec C1·C2 `value_farad` 5.38e-14도 같은 방식이다. 원문 `CNR_OTA.sch:632-633`의 `cap_mim_m3_1 W=5 L=5 MF=1`을 sky130 camimc·cpmimc로 계산했다(같은 spec `element_values.C1/C2` record).
- K12의 범위는 저항 6 + 용량 2 = **8개 값**이 맞다.

**1.5 엔진이 이 값을 쓰는 방향**
- 엔진은 Ω을 회로 입력으로 받는다(`authoring/spec_elements.py`, `metrics/achievability.py:9`).
- 면적은 Ω에서 **PDK 선언으로** 기하를 유도한다: `search/area_decl.py:10-22` 본체 W_min²/R□ + 머리 면적. 선언 `resistor_types.selected_as = poly_res` ← 후보 `poly_generic`(`sky130_pdk_decl.json:466-475`).
- 즉 엔진의 정본 방향은 '회로 = Ω, 기하 = PDK에서 유도'다.
- 다른 library 회로의 저항은 모두 원문이 준 Ω이다: erfc_ota R1·R2 52 kΩ, rfc_ota RB 1412 Ω, nmcnr RL 25 kΩ, r2r RL 10 kΩ. 모두 `origin: paper`다.

**1.6 O-197의 문언 범위**
- 원칙 11·O-197(`user_decisions.md` 1178행)의 대상은 "계획·design·엔진·test"다. 회로 spec 값은 명시 대상이 아니다.
- 원칙 13(확정 값 = 사용자 지정분)으로는 D-R이 사용자 승인 값이다.

### 2. 대안

| 안 | 장점 | 대가 | 원칙 |
|---|---|---|---|
| (가) Ω 유지(사용자 선언 회로 값) | 회로 기능의 결정자(R·C 영점, CM 감지, 바이어스 전류 = 저항값)를 그대로 선언한다. 엔진 정본 방향(Ω → PDK 기하, 1.5)과 다른 회로들의 관례와 같다. PDK를 바꿔도 회로 의도(Ω)는 유지되고, 면적은 새 PDK 선언에서 다시 나온다 | 출처가 sky130 셀 식이라 다른 PDK로 옮길 때 '같은 Ω를 쓸지'는 사람이 다시 판단해야 한다. 그 표지가 record 글에만 있고 기계가 읽을 표지는 없다 | 원칙 13 맞음(D-R). O-197 문언 범위 밖. 원칙 14 맞음(원문 기하 → PDK 모델 → Ω 경위 기록) |
| (나) spec에 원문 기하(셀 종류·W·L·직렬 수)를 선언하고, Ω는 PDK 선언의 저항 셀 식으로 엔진이 유도 | 원문이 실제로 정한 양(기하)을 그대로 쓴다. sky130 안에서는 PDK 판(L=8.8 → 8.96 등)이 바뀌면 값이 따라간다 | ⚠ 선언하는 기하(`res_high_po`, W=0.72, L=8.8)가 **sky130 고유**다. PDK를 바꾸면 그 셀이 없어 유도가 안 되거나 Ω가 달라져 회로 기능(영점·바이어스)이 바뀐다. 이식성이 (가)보다 나쁘다. 엔진에 '기하 → Ω' 생산 블록이 새로 든다(지금 정본 방향 'Ω → 기하'의 역). 저항 셀 모델 식 선언 항목(R6 확장)과 온도·코너 입력이 필요하다. spec 형식이 바뀐다(회로 데이터 = 사용자 몫) | ⚠ O-197 취지(PDK가 바뀌어도 동작), ⚠ 원칙 9(cnr_ota 하나만 쓰는 블록), 원칙 12(일반성 1/13) |
| (다) (가) + 기계가 읽는 'PDK 고유 유도' 표지(예: 출처에 유도에 쓴 PDK 선언 지문). 실행 PDK 선언 지문과 다르면 spec 로더가 `review_needed`/거부(fail-closed) | 이식 때 다시 볼 자리가 자동으로 드러난다(조용한 재사용 방지). C1·C2와 다른 '원문 기하 → PDK 식' 값에도 한 규칙으로 쓴다 | 새 출처 칸과 그 소비자(로더 대조)가 필요하다. 출처 스키마(`authoring/spec_sources.py:28-31` ORIGINS)를 바꾸고 card가 하나 든다. 지금 PDK가 하나뿐이라 당장 발동하지 않는다 | 원칙 9 맞음(소비자 = 로더 대조를 같이 만들 때만). 원칙 10 맞음 |
| (그 밖) '문제 없음'으로 닫음 | -- | 원문이 값을 정했다면 성립하지만, 사실 1.1은 원문이 값이 아니라 기하를 정했음을 보인다. 그대로 닫을 수는 없다 | -- |

### 3. 권고·물리 검증
- **권고 (가)**. 판정: **조건부 맞음**. 조건은 회로의 물리 결정자가 Ω라는 해석이고, 이것은 사용자가 확인해야 한다.
- (다)는 PDK가 둘 이상이 될 때(이식 card) 함께 만드는 것이 원칙 9에 맞다. 지금 만들면 발동하지 않는 칸이 된다.
- 물리 결정자:
  - 회로 동작(CM 감지 부하, R·C feedforward 영점 f_z = 1/(2π R C), 바이어스 분압 VCR과 x9의 I·R)은 **저항값 Ω**가 정한다.
  - 기하(W·L·직렬 수)는 sky130에서 그 Ω를 만드는 구현이다.
  - 다만 x40 : x39 : x3 = 16 : 16 : 4의 분압비는 같은 세그먼트 직렬 수 비율이라 PDK와 무관하다. 지금 Ω 선언(70134.2 : 70134.2 : 17533.5 = 4 : 4 : 1.00000)도 그 비를 보존한다.
- 식·원문: 위 1.1(.sch 줄, design.md VCM 절), 1.2(res_high_po model 24~54행).
- 실측: Ω 재계산이 일치했다(1.2).
- 판정 '조건부'인 이유: 설계자가 의도한 양이 Ω인지 기하(면적·정합·온도 계수까지 포함한 셀 선택)인지는 원문 서술만으로 확정되지 않는다. VCM 절은 값 뜻이고 BIAS 절은 말이 없다.
- 표지: 감사 §4가 C1·C2를 빠뜨렸다(1.4). 어느 안을 고르든 같은 규칙으로 8개 값에 적용한다.
- 참고(결함 아님, 면적 모형 사실): 면적 선언이 고르는 저항 종류(`poly_generic`)와 cnr_ota 값의 출처 셀(`res_high_po`)이 다르다. 그래서 cnr_ota 저항 면적은 원문 셀 면적과 다르게 나온다. 면적 모형의 범위 문제이고 K12와는 따로다.
- 사용자 결정 필요: **예**. spec 값과 그 출처 규칙은 회로 데이터라 사용자 몫이다(원칙 13·15). (가)이면 spec 변경 0이고 출처 문언만 기록한다.

---

## 질문 초안

**K11.** 최소 finger 폭은 정의 하나만 남기는 것을 권고합니다.
- 정본은 PDK 선언 `min_finger_w_m`(제조 규칙 difftap.2, sky130 0.42 µm)입니다. `LutSpec.min_finger_w_m` 칸은 지웁니다((가)).
- 근거 1: 엔진 소비자 7곳이 모두 제조 규칙 뜻입니다. LUT 최소 슬라이스 폭 뜻의 소비자는 0입니다. 정의역은 슬라이스 집합이 이미 담고 있습니다.
- 근거 2: 지금 test가 조립하는 값(nfet 0.36 µm, 모델 bin 하한)이 엔진 수렴 경로의 손가락 후보에 nfet 0.36·0.39 µm(difftap.2 위반)을 들여보냅니다(E-0 구멍).
- 동작이 바뀝니다: nfet 후보 20 → 18. 13회로 변화표가 card 완료 조건에 들어갑니다.
- 같은 card에서 `LutSpec.manufacturing_grid_m`(같은 정의의 둘째 보유자)도 선언 READS로 바꿀지 함께 정해 주세요.
- ① (가) 승인 ② (나) 이름 둘(⚠ LUT 칸 소비자 0 -- 원칙 9) ③ 유지(⚠ graph 규칙 3·E-0)

**K12.** cnr_ota 원문(xschem `CNR_OTA.sch:634·635·642·643·681·701`)은 저항을 Ω가 아니라 sky130 셀(`res_high_po` W=0.72 L=8.8 µm 16·4개 직렬)로 정했습니다. spec의 Ω 6개는 D-R(2026-10-14) 승인으로 그 셀 모델 식에서 계산한 값입니다(재계산 일치). 같은 방식으로 정한 C1·C2(MIM W=L=5 µm)도 있어서 대상은 8개입니다.
- 권고 (가) Ω 유지: 회로 기능(CM 감지·R·C 영점·바이어스)의 결정자가 Ω이고, 엔진은 Ω에서 PDK 선언으로 면적을 유도합니다.
- (나) 원문 기하 선언 + PDK 유도는 선언 기하가 sky130 고유라 오히려 PDK 이식성이 나빠집니다(⚠ O-197 취지).
- (다) 'PDK 고유 유도' 기계 표지 + 로더 대조는 PDK가 둘이 되는 이식 card에서 함께 만드는 것을 권고합니다(지금 만들면 소비자가 발동하지 않음).
- ① (가) ② (가) + 지금 (다) ③ (나)
- 확인 요청: 원 설계 의도를 '저항값'으로 보는 해석이 맞습니까?
