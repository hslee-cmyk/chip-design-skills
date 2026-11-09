# MOD1(LUT)·MOD5(metric·MNA) 짧은 design (E7)

- 작성 2026-10-07. 설계만(코드 없음). 저장소는 읽기만 했다.
- 기준: 메인 저장소 `chip-design-skills` HEAD `a21a24f`. 옛 엔진 SR = `skills/analog-gmid-design/legacy/sizing_recipe.py`(행 번호는 이 HEAD 기준, `legacy-engine-v1` = `6df4bd7`과 같은 내용). P = `docs/01-plan/features/gain-budget-gmid-sizing.plan.md`. REQ = `_drafts/engine/NEW_ENGINE_DESIGN_REQUIREMENTS.md`(특히 맨 끝 '확정 사항'). LCS = `_drafts/engine/lut_coverage_study.md`. SLG = `_drafts/engine/lut_slices/sky130_dc_width_slices.py`(폭 슬라이스 생성기, 생성 중).
- 상위 규칙(확정, 이 문서가 따르는 것): graph(S0~S3) 단일 정본·필드 = 캐시(writer 1개 + 입력 버전), 불변 스냅샷, **graph 밖은 LUT 조회 memo 하나뿐**(상한 LRU, 상한 = 한 평가 sweep 작업 집합), 파일 규칙 A~D(독립 진입점 1 / helper 국소 / 계산 블록 1 = 파일 1 / test 1:1), 상수 금지(WP-03), E5 finger_w 후보 = PDK 특성화 폭 슬라이스(보간 금지).
- 표기: **[제안]** = 원칙에서 유도한 기본안. **[추측]** = 실측 근거 없음. **[실측]** = 이 문서 작성 중 직접 확인.
- **[2026-10-07 개정 -- reference 검토 Q1~Q12 추천안 확정, 사용자 "B는 추천대로 해."]** 계획 worktree `plan-rev4` 커밋 `defdc24`의 DEC-87(축별 cubic-Hermite 보간·tol_V 2^p 환산), DEC-88(반전 좌표 ln IDu·봉인 7 VDSAT 열), DEC-91(접합 용량), DEC-92(GB5 = θ 연속 + 전회로 MNA), DEC-96(nqs·mismatch 보고), DEC-53(MetricSignature 어휘)을 이 문서에 반영했다(아래 [개정 Q*] 표시). 계약 문서 `gmid_engine/lut/CONTRACT.md`는 이 문서가 고치지 않는다(담당 작업이 개정).
- REQ 4.1 캐시 표 중 MNA·metric·`ss` 항목은 '확정 사항' 1·4에 따라 **memo가 아니라 S2 graph 필드**로 바뀐다(3.3절). LUT 계열만 memo로 남는다.

---

## 1. 경계: 무엇이 memo이고 무엇이 graph 필드인가

| 값 | 성격 | 자리 | 키 / 입력 버전 |
|---|---|---|---|
| LUT 점 조회·gm/ID 곡선·VGS 근·ID 역산·gmb | 공정 성질(입력값만으로 정해지는 불변 결과) | MOD1 LUT memo(graph 밖, LRU) | (LutSet 지문, kind, 폭 키, 축 값) |
| tol_V 표·곡선 검사 보고·폭 집합 | LUT 파생 표(공정 성질) | MOD1 LUT memo의 '파생 표' 영역(LRU 대상 아님, 개수 = 슬라이스 수) + E3 디스크 | LutSet 지문 + MOD1 코드 해시 |
| 소자 `ss`(gm·gmb·gds·용량), MNA 계, 주파수 응답, metric, GB4 상한표, GB5 보상 값 | 설계 상태 | S2(또는 S0 단위 구조 필드) graph 필드, writer = MOD5 파일 하나씩 | 입력 스냅샷 버전(봉인 `dc` 버전, passive 값 버전, 뷰) |

결과: MOD5에는 캐시 객체가 하나도 없다. "같은 값 재계산 금지"는 graph setter가 "입력 버전 같으면 쓰지 않음"으로 강제한다(확정 사항 5).

---

## 2. MOD1 -- LUT (`gmid_engine/lut/`)

### 2.1 이식 대상 표

처리 열: **복사** = 본문(docstring 제외 문장 목록) 그대로 + AST 해시 대조 test, **블록 복사** = 알고리즘 문장 구간만 그대로(캐시 줄 제거) + 구간 AST 해시 대조, **새로** = 새 데이터 모델에 맞춰 다시 씀(옛 함수는 기대값 비교 test의 참조로만), **안 함** = 이식하지 않음(사유).

| 옛 이름 | 옛 위치 | 처리 | 새 위치 | 알려진 결함(P DF·근거) |
|---|---|---|---|---|
| `_multilinear_interp` | SR:141 | **[개정 Q2] 새로**(옛 함수는 기대값 비교 참조로만, 동치 test는 격자점에서만) | `lut/_helpers_interp.py` | 운영 보간은 축별 방법 표(2.2a)로 바뀐다(DEC-87). 옛 함수: 축 밖 입력을 조용히 클램프(`x<=g[0] → f=0`) -- DF-27, 격자선 C0 꺾임·gm ≠ d(보간 ID)/dVGS |
| `_multilinear_interp_point_multi` | SR:206 | **[개정 Q2] 새로**(참조) | 같은 helper 파일 | 위와 같음 |
| `_QUERY_CACHE_MAX = 400_000` | SR:257 | 안 함 | -- | 상수(WP-03)이자 상한 도달 시 캐싱 중단(DF-07) |
| `GmIdLUT`(인터페이스) | SR:52 | 안 함 | -- | 구현 하나뿐인 추상 클래스. 새 모델은 불변 데이터 + 함수 |
| `SemiEmpiricalGmIdLUT.__init__` | SR:274 | 새로 | `lut/lut_set.py` | 로그 바닥 상수 `1e-18`(ID)·`1e-30`(GM·GDS)(WP-03). 인스턴스 dict 캐시 4개(`_gm_id_curve_cache`·`_solve_vgs_cache`·`_idu_scan_cache`·`_query_cache`) 상한 없음·`id(array)` 키 -- DF-13 |
| `_w_ref_effective` | SR:374 | 새로 | `lut/lut_set.py`(슬라이스 메타 `w_m`) | `W_ref=None`(단위 소자 관례) 분기와 하네스 `_W_REF = 5e-6` 박힌 값(`legacy/workspaces/run_harness.py:68`) -- 폭은 파일이 말해야 한다 |
| `_query` / `_query_multi` / `_sizing_bundle` | SR:378 / 394 / 401 | 새로 | `lut/point_query.py` | `id(array)` 키(DF-13), 상한 도달 시 저장 중단(DF-07) |
| `_gm_id_curve` | SR:455 | 블록 복사 | `lut/gm_id_curve.py` | 키 반올림 없음은 유지(같은 float), 캐시만 LUT memo로 |
| `_solve_vgs`(rightmost root, DEC-11) | SR:478 | 블록 복사(`d = g - gm_id`부터 `result` 계산까지) | `lut/vgs_root.py` | 없음(B20 수정본). 실패 `ValueError` → N3.14 `lut_axis_out_of_range`/곡선 범위 밖 실패 클래스로 |
| `gm_id_to_id_density`·`id_density_at_vgs`·`cgg_absolute`·`gm_gds_ratio`·`vgs_for_gm_id` | SR:580·565·606·616·625 | 새로 | `point_query.py`·`vgs_root.py`·`cap_query.py` | 정규화 `raw*L/W_ref`를 폭 슬라이스 `w_m`로 일반화. CGD 열이 npz에 있는데 엔진이 0회 읽음 **[실측: SR·stick_diagram `CGD`/`cgd` 0건]** |
| `gm_id_for_vgs` | SR:632 | 새로(소비처가 MOD4 design에서 확정될 때만, DEC-76) | `lut/gm_id_for_vgs.py` | 없음 |
| `noise_1f_density` | SR:653 | 안 함(잡음은 7b 이후 제약 metric, P 158) | -- | SID_1F 없는 LUT에서 거부는 유지 원칙 |
| `_idu_scan` | SR:428 | 안 함 | -- | 소비자(`search_gm_id_for_role`)가 새 엔진에 없음 |
| `solve_id_for_target_gm`·`_invert_gm_id_for_current` | SR:1433·1471 | 새로 | `lut/id_inverse.py` | 이분 역산이 단조성을 검사하지 않음 -- DF-10 |
| `diode_vds_cached`·`_KNEE_L_CACHE`·`_FEASIBLE_L_WINDOW_CACHE` | SR:3206·2391·2530 | 안 함(계산은 MOD4 블록, LUT 부분만 이 memo 사용) | -- | `id(lut)` 키·상한 없음(DF-13), `< 200_000`에서 저장 중단(DF-07) |
| `lut_conditions_from_npz` | SR:4782 | 복사(비공개 helper로) | `lut/provenance.py` | 운영 경로에서 안 불림(I-A5) → 새 엔진은 S0 지문 조립에 배선 |
| `_invq_newton`·`build_toy_lut` | SR:1343·1356 | 복사 | `gmid_engine/tests/fixtures/toy_lut.py` | toy LUT은 test 픽스처 전용 -- 엔진 소스에 두면 도달 test(`test_reachable_from_entry`) 위반. `W_ref=None` 대신 `w_m`를 명시 |
| LOO 방법 | `legacy/tests/probes/probe_interp_scheme_loo.py` | 새로(방법만 승격, N3.6) | `lut/tolerance.py` | 옛 probe는 L 축만(bin 구분 없음)·상대오차(%)라 보간 축(VGS·VDS·VS·bin 안 L)과 지표를 계획 N3.6 정의로 바꿔야 함(2.7절) |

AST 해시 대조 test(`tests/lut/test__helpers_interp.py` 등 규칙 D 파일): 대상 함수의 `body`에서 docstring 문장을 뺀 문장 목록의 `ast.dump(..., include_attributes=False)` sha256을 비교한다(함수 이름 변경은 허용). 블록 복사는 대상 문장 구간을 (첫 문장, 끝 문장) 소스 앵커로 지정한다. 옛 파일이 지워져도 test가 살도록 복사 시점의 해시·`legacy-engine-v1` 태그·`파일:행`을 test에 기록하고, 옛 파일이 있으면 재계산해 함께 대조한다.

### 2.2 데이터 모델 [제안]

- **두 원천**: (가) DC 폭 슬라이스(SLG 산출) -- 소자·폭마다 npz 하나, 배열 `ID·GM·GDS·VTH` `[L, VGS, VDS, VS]`, 값은 **그 폭 W에서의 절댓값(정규화 안 함)**, `W`(m), `corner`, `temp_c`, `meta_json`(모델 파일 sha256, bin 이름, 축, 생성기 sha256) + `manifest.json`(파일별 sha256). (나) 기준 LUT `assets/sky130_nfet_pfet_lut_sample.npz` -- 용량 `CGG·CGD`(·`SID_1F`)만 쓴다(DC 열은 슬라이스가 정본). [실측] 기준 LUT 축: L 12, VGS 49, VDS 49, VS 5(0~0.8 V), 메타는 `corner`·`temp_c`뿐(폭 없음).
- **폭 집합**(E5): PDK 모델 bin `wmin` 집합 = `bins.csv` W 집합(SLG가 교차 확인). [실측] nfet 20개(0.36~7.0 µm), pfet 12개(0.42~7.0 µm). finger_w 후보 = 슬라이스 폭 ∩ [`core.pdk_decl` 최소 finger 폭(difftap.2), ∞) -- 그래서 nfet 0.36·0.39는 빠진다. 최대 finger 폭 상수는 두지 않는다(슬라이스 최대 폭이 곧 상한).
- **폭 키(이산)**: `w_key = round(w_m / grid_m)`(정수, `grid_m` = `core.pdk_decl` tlef `MANUFACTURINGGRID`). 로드 때 `|w_m − w_key·grid_m|`가 float 표현 오차를 넘으면 거부. 조회는 정수 키 일치만 -- 근접 폭 대체·폭 사이 보간 없음(LCS 4절: bin 불연속 W 5/6/7/8 µm = 0/−14/−25/−11 %).
- `LutSet`(frozen): `{slices: ((kind, w_key) → DcSlice), cap: (kind → CapTable), fp, provenance}`. `DcSlice`는 생성 시 한 번 `log_ID·log_GM·log_GDS`(B15 로그공간 규칙 그대로)와 `grids_list`를 만든다. 로그 바닥은 상수 대신 **그 배열의 최소 양수값**(데이터를 자르지 않음, B15 주석의 의도)이고, 0 이하 원소 수를 provenance에 기록한다. 옛 바닥(1e-18)과 값이 갈리는 곳은 소자가 꺼진 영역뿐이므로 동치 test는 `ID ≥ 옛 바닥` 격자점에서만 비교한다.
- **정규화**: `IDu = ID_slice · L / w_m`(옛 `raw*L/W_ref`와 같은 식, W_ref 자리에 슬라이스 폭). 소자 총 W에 대한 값은 `× W / w_m`(nf 병렬, LCS 표 E: `w=finger_w m=nf`가 단일 폭과 같음).
- **용량**: `cap_query`가 기준 LUT 값을 `W / w_ref_cap`으로 비례(LCS 표 M ±9 %). `w_ref_cap`은 기준 npz에 폭 메타가 없어 [제안] 두 단계로 정한다: (1) 메타 `w_ref_m`(U-27 재생성 G4)이 있으면 그것 (2) 없으면 기준 LUT `ID`가 슬라이스 `ID`와 겹치는 격자점(VS ≤ 0.8)에서 **일치하는 슬라이스 폭**을 증거로 채택(LCS 6행: W=5 µm에서 비트 수준 일치)하고 채택 근거를 provenance에 남긴다. 일치 슬라이스가 0 또는 2개 이상이면 로드 거부. 하네스 `_W_REF` 값은 읽지 않는다.

### 2.2a 축별 보간 방법 [개정 Q2, 확정 DEC-87]

| 축 | 방법 | 값·기울기 |
|---|---|---|
| VGS | 2점 cubic-Hermite | y = ln ID, 기울기 = 저장 GM/ID. `op_point`의 gm/ID는 이 다항식의 미분으로 정의(ID·gm/ID·역산이 한 곡면) |
| VDS | 2점 cubic-Hermite | y = ln ID, 기울기 = GDS/ID |
| VS | 선형(GMBS 열이 생기면 기울기 −GMBS/ID의 Hermite) | |
| L | 같은 bin 안 선형(LR3) | 값 공간은 열별 규칙(ID는 ln) |
| ln GDS의 VGS 방향 | 선형 | |

- 역산(`vgs_for_gm_id`, `vgs_for_current_density`)은 같은 Hermite 칸 안 bisection, 반복 상한 `K_max`(N3.6).
- 로드 때 칸마다 Fritsch–Carlson 단조 조건 검사, 위반 칸은 `curve_report`에 실패로 기록(G1 실측: nmos 0/126,361, pmos 0/104,125).
- 근거(G1 실측): VGS 축 ln ID→VGS 환산 nmos p50 1.25 → 0.0026 mV, p99 3.83 → 0.042 mV, 칸 중앙 gm/ID p99 2.1 % → 0.021 %, VDS 축 p99 69.9 → 6.85 mV.

### 2.3 조회 API (`lut/__init__.__all__`) [제안]

| 함수 | 반환 | 비고 |
|---|---|---|
| `load_lut_set(manifest_path, cap_npz_path, pdk) -> LutSet` | 불변 LutSet | 모든 파일 sha256 대조(manifest), 축 일치 검사(슬라이스 간 L·VGS·VDS 같음) |
| `widths(lut, kind) -> tuple[int]` | 정렬된 폭 키 | MOD7 finger_w 후보 정본(E5) |
| `op_point(lut, kind, w_key, L, vgs, vds, vsb) -> OpPoint` | `IDu, gm_over_id, gm_gds, gds_per_w, vth` | `_query_multi` 1회로 묶음(F 설계 그대로) |
| `gm_id_curve(lut, kind, w_key, L, vds, vsb) -> Curve` | VGS 격자 위 (ID, gm/ID) | |
| `vgs_for_gm_id(lut, kind, w_key, gm_id, L, vds, vsb) -> float` | rightmost root | DEC-11 (층 0 gm/ID 역산 소비) |
| `vgs_for_current_density(lut, kind, w_key, ln_idu, L, vds, vsb) -> float` | 강반전 분지(VGS ≥ 정점) 위 단조 역산 | **[개정 Q3]** DEC-88 쓰기 소자 좌표의 정본 역산. 오차 = id_equivalent |
| `vdsat(lut, kind, w_key, L, vgs, vds, vsb) -> float` | V | **[개정 Q1·Q3]** VDSAT 열 보간(오라클 `@m[vdsat]`과 같은 양). 열 없는 LUT면 구조화 실패(이름 [제안] `vdsat_column_missing`, 봉인 7 '정의 미확정' 표시. 2/(gm/ID) 대체 금지) |
| `gm_id_for_target(lut, kind, w_key, L, vds, vsb, *, gm=None, current=None, W=None)` | gm_id | 단조 구간 확인 후 역산, 비단조면 구조화 실패(DF-10) |
| `gmb(lut, kind, w_key, L, vgs, vds, vsb) -> float` | A/V, 폭 w_m 기준 | 2.8절 |
| `caps(lut, kind, L, vgs, vds, vsb, W) -> Caps` | `cgg, cgd, cgs, cgb, model` | 2.8절 |
| `tol_v(lut, kind, w_key, L, vds) -> float` | V | 2.7절 |
| `curve_report(lut) -> CurveReport` | 단조성·범위 | N3.7 LUT 곡선 검사(GB4 입력) |
| `lut_fingerprint(lut) -> str` | S0 입력 | 2.5절 |

공통 규칙: 모든 조회는 먼저 `axis_guard`(축 밖 → `lut_axis_out_of_range{kind, w_key, 축, 값, 범위}`, LR3·DF-27; 클램프·외삽 없음, LUT L 점 범위 밖 포함). [2026-10-07 개정, LR3] L 조회는 L을 감싸는 두 LUT L 점이 **같은 PDK 모델 bin**(생성 메타의 시뮬레이터 실제 소속; 연속 경계의 경계값은 양쪽 bin 공통 끝점)일 때만 L 축 선형 보간(값 공간은 열별 규칙, ID는 ln)하고, 두 점이 다른 bin이면 구조화 실패 [제안, 이름은 MOD1 계약 개정 때 확정] `lut_l_cross_bin{kind, w_key, L, below, above}`(SEAL_VIOLATION)다. 호출자(외층·역산)는 bin을 고정해 L을 그 bin 안에서만 움직인다. 폭 키가 집합에 없으면 계약 위반(탐색 루프가 잡지 않는 비후보 예외 -- MOD7은 `widths()`에서만 고른다).

### 2.4 VS 축 확장 (U-27)

- DC: 슬라이스 VS 축 = 기준 LUT 간격(0.2 V)을 그대로 두고 상한만 소자 정격(기준 LUT VGS 상한 1.8 V)까지 늘린 10점(SLG `--vs-max`; 상수 아님, 기준 축에서 유도). 그래서 DC 조회는 vsb 0~1.8 V를 덮는다(LCS 5절: follower M9a·M18a 0.825 V, push-pull 출력 약 0.9 V).
- 용량·잡음: 기준 LUT VS 0~0.8 V 그대로라 `caps()`는 vsb > 0.8 V에서 `lut_axis_out_of_range`를 낸다(클램프 금지). 해소는 U-27 기준 LUT 재생성(VS 0~1.8, CGS·CGB, SID_1F)이고, 그 전까지 해당 점은 실패로 기록된다 -- 숨기지 않는다. [추측] 9회로 중 용량 축 밖이 실제 발동하는 회로는 push-pull 계열 둘 정도(실행으로 확인).
- 대조: 5 µm 슬라이스와 기준 LUT의 겹치는 격자점(VS 0~0.8) `ID·GM·GDS` 일치 test(U-27 (3) '옛 격자점 대조'의 동형). 어긋나면 red로 보고(기준선 변경은 사용자 승인).

### 2.5 메타·지문 (S0의 LUT 지문)

`lut_fingerprint = sha256(정규화 JSON{manifest sha256, 슬라이스별 (kind, w_key, 파일 sha256), 기준 npz sha256, conditions: 파일별 lut_conditions(corner, temp_c, recorded), 슬라이스 meta_json의 model_files_sha256 집합, w_ref_cap 채택 근거})`. 코드 해시는 넣지 않는다(S0의 별도 '유도 규칙 코드 해시' 항목이 맡는다, P N3.3). 조건 불일치(슬라이스 사이 corner·temp 다름)는 로드 거부. `recorded=False`(기준 npz처럼 기록 없음)면 S0에 그 사실을 그대로 싣고 결과 JSON에 표시(I-A5).

### 2.6 memo 키·상한 [제안]

- 영역 4개(한 `LutMemo`, `core` BoundedLRU 사용): `point`(OpPoint), `curve`(Curve), `root`(VGS 근·역산 gm_id), `derived`(tol_V 표·곡선 보고·gmb 셀 기울기 표). 키 = (`lut.fp`, 함수 이름, kind, w_key, 축 float 그대로). float은 반올림하지 않는다(반올림은 값을 바꾼다, 옛 `diode_vds_cached`의 `round(…, 9)` 폐기). `id()` 키 금지 -- 키에 객체가 들어가면 `TypeError`.
- **상한 = 한 평가 sweep의 고유 키 상계**. sweep = 같은 기준점을 공유하는 평가 묶음 중 가장 큰 것 = 외층 SLSQP 한 반복의 FD Jacobian(`n_θ + 1` 평가). 평가 1회의 키 상계는 구조에서 계산한다:
  `U_eval = Σ_dev (K_max,dev + 1) · q_dev`, `q_dev` = 그 소자가 고정점 반복 1회에 쓰는 조회 종류 수(point·curve·root, 블록 ②~⑤ 코드가 `@lut_reads` 선언으로 낸다), `K_max,dev` = N3.6 식(그 소자가 속한 순환 블록, 비순환이면 0).
  `B_region = (n_θ + 1) · U_eval,region`. `derived` 영역 상한 = 슬라이스 수 × 파생 표 종류 수(퇴출 없음).
- 계측: 첫 평가에서 영역별 실제 고유 키 수를 세어 `U_eval`보다 크면 상계 식 결함으로 FAIL(E2 (a)). 퇴출은 카운터로 남기고, `recompute_same_key`(퇴출되지 않은 키의 재계산)는 구조상 0, 퇴출 뒤 재계산은 별도 집계. 확정 사항 4의 '실행 내 같은 키 재계산 0' test는 sweep 범위 재계산 0 + 미퇴출 재계산 0으로 판정한다. 상계 × 키당 크기(Curve = VGS 점 수 × 2 float)로 메모리 상한을 결과 JSON `perf.lut_memo`에 함께 적는다.

### 2.7 tol_V (계획 N3.6 -- MOD1 함수로 승격)

- 정의(P N3.6, 사용자 확정 2026-10-07, 같은 날 'bin 안 L 보간' 결정으로 개정): 셀 = (kind, w_key, L 점, VDS)별 LUT leave-one-out 보간 오차의 최댓값. 보간 축은 **VGS·VDS·VS와 bin 안 L**이다(L 방향 LOO는 같은 bin 안 L 점만 쓴다. bin 경계를 넘지 않는다). L 점이 2개뿐인 bin([0.15, 0.18], (4, 8], (8, 20] -- 18점 격자 기준)은 LOO가 정의되지 않으므로 LUT 생성이 만든 bin 중점 검증 표본(별도 파일)과의 보간 오차를 그 bin의 L 방향 값으로 쓴다. 계산(`lut/tolerance.py`, 슬라이스마다 = (kind, w_key)마다):
  1. 보간 축(VGS·VDS·VS, bin 안 L)마다 내부 격자점 하나를 빼고 나머지 격자점으로 운영 보간과 같은 `_helpers_interp`로 뺀 점의 값을 만든다.
  2. 뺀 점의 실제 LUT 값과 비교해 두 지표로 환산한다: (i) gm/ID 역산 지표(목표 gm/ID에서 역산한 VGS 차, rightmost root 같은 규칙) (ii) ID 환산 지표(같은 VGS에서 `|Δln ID| / (gm/ID)`). 소비자 배정은 P N3.6.
  3. `tol_V[kind, w_key, L 점, VDS] = 셀 안 최댓값`(L 방향 값은 (kind, w_key, bin, VDS)로 따로 둔다)(전역 최댓값 하나로 줄이지 않는다). 결과 표는 `derived` memo + E3 디스크(키 = LutSet 지문 + MOD1 코드 해시).
- **[개정 Q2, DEC-87]** 1단계의 '운영 보간'은 2.2a의 축별 Hermite이고, 뺀 점을 보간하는 격자는 간격이 2배라 그 오차는 운영 오차보다 차수 p배로 크다. 셀 값 = LOO 값 / 2^p(p = 그 축 보간 차수: 선형 2, Hermite 4 -- Richardson). 환산은 셀 표본의 **칸 중앙을 ngspice로 직접 재는 검증 test**(`tests/lut/test_tolerance.py`의 slow 표본, 기대값 = SPICE)로 확인한다.
- **[개정 Q3, DEC-88]** 소비자 배정: ID 환산 지표 = 봉인 2·3, `tol_I`, W 허용오차 상한, forced 경고, 순환 블록 수렴. gm/ID 역산 지표 = 층 0 gm/ID 역산. 봉인 7은 VDSAT 열 자체의 LOO(`tol_vdsat`, 같은 방법·같은 환산)를 쓴다.
- 조회 `tol_v(L, VDS)`: L이 LUT L 점이면 그 셀, 같은 bin의 두 L 점 사이면 양옆 L 점 셀 값과 그 bin의 L 방향 값 중 최댓값(bin을 넘는 L은 `lut_l_cross_bin`). VDS는 격자점 값 중 양옆 최댓값. 양끝 격자점(LOO가 정의되지 않는 점) 처리는 P N3.6대로 MOD1·6b design이 정한다. 새 상수 없음.
- 소비자: 봉인 1·2·6·7·8(MOD4), tol_I = tol_V × gm 최대(MOD4), K_max(MOD4), SPICE forced 모드 소자 경고 허용오차(oracle, ID 환산 지표 -- 노드전압은 합격 비교 대상이 아님, 사용자 확정 2026-10-07 8번), **W 허용오차 상한 = tol_V × gm/ID**(MOD7, 사용자 결정; 하한 = 격자/(2·finger_w)).
- [정정 2026-10-07] 옛 열린 항목 O1(L 축 LOO만 tol_V에 쓰고 VDS·VS LOO는 보고 열)은 계획 N3.6 사용자 확정(보간 축 VGS·VDS·VS, L 축 제외)으로 대체됐다. [재정정 2026-10-07] 같은 날 사용자 결정 "나로 하자."로 L은 bin 안 연속이 되어 **bin 안 L 방향 LOO가 다시 들어간다**(bin 경계를 넘지 않는 점이 옛 L 축 LOO와 다르다). 근거·격자는 `lut_regen_plan.md` 0·1.2a·2절.

### 2.8 gmb와 용량(MOD1 쪽)

- **[개정 Q1, 계획 N3.8]** gmb 정본 = U-27 재생성 LUT의 `GMBS` 열 보간(× W/w_m). 아래 칸 기울기 방식은 열이 생기기 전 **임시**이고 결과에 '임시'로 표시한다(G1 실측: 이웃 칸 할선 상대차 p99 16.6 %(n)/20.6 %(p) -- 칸 경계 계단). 임시 기간에는 3점 2차식(VS 격자 세 점)으로 칸 경계 꺾임을 줄인다.
- (임시, 옛 기본안) gmb(P N3.8 "MOD1 수치미분"): 같은 다선형 보간식의 VS 방향 해석 미분 -- 조회점이 든 VS 칸 [vs_k, vs_k+1](보간과 같은 `bisect_right−1` 규칙)에서 `gmb = ID · (logID(vs_k+1) − logID(vs_k)) / Δvs`의 부호 반전(VGS·VDS 고정, 다른 축은 보간). 스텝 상수가 없고(격자 칸 = 스텝) 같은 보간면에서 나오므로 ID와 일관된다. 칸 기울기 표를 `derived` memo로 한 번 만든다. **[실측] 옛 엔진 gmb 0건**(SR·stick_diagram·topology_library 문자열 검색).
- 용량(DF-28): 기준 LUT에 CGS·CGB 열이 없으므로 `Caps.model`을 열 존재로 정한다 -- 열 있음 = `"lut_cgs_cgb"`, 없음 = `"cgg_minus_cgd_at_gs"`(cgs = CGG − CGD, cgb = 0, CGD는 그대로). 플래그 선언이 아니라 열 존재로 갈린다. **[개정 Q6, DEC-91]** 접합 용량(cdb·csb)은 MOD1이 아니라 MOD5 `junction_caps`가 PDK 접합 파라미터(CJ·CJSW·MJ·MJSW·PB, `core.pdk_decl`) + 봉인점 역바이어스 + 확산 기하(MOD7 `ly.diffusion`, 레이아웃 전은 LUT 생성 규칙)로 계산하고 `ss`에 스탬프한다(옛 '별도 열로 보고' 폐기). U-27 재생성 LUT의 `CDD`·`CSS` 열 − `CGD`·`CGS`는 `caps()`가 노출만 하고 대조 test(`tests/metrics/test_junction_caps.py`)에서만 쓴다(LUT 열은 생성 때 고정 확산 기하라 공유 확산을 반영하지 못한다).

### 2.9 DF-07·DF-13 회피 요약

DF-07(상한 도달 시 저장 중단) → `BoundedLRU`만 사용, 상한 도달 시 LRU 퇴출 + 카운터. DF-13(`id(lut)` 키·상한 없음) → 키는 `lut.fp` 내용 지문, 인스턴스·모듈 dict 캐시 금지(lint `test_no_unregistered_cache`), 모든 영역에 2.6 상계. 옛 `_query` 주석의 "내용 해시는 비싸다"는 LutSet 생성 시 지문을 한 번 계산해 해소된다.

### 2.10 파일 목록 (`gmid_engine/lut/`, 규칙 A~D)

| 파일(층) | 독립 진입점(A) | 비고 |
|---|---|---|
| `_helpers_interp.py`(0, kind=helper) | -- | 복사 2함수(B 예외 등록) |
| `provenance.py`(0) | `lut_provenance` | `lut_conditions_from_npz` 복사본 helper + manifest·meta 읽기 |
| `lut_set.py`(1) | `load_lut_set` | DcSlice·CapTable·w_ref_cap 채택·지문 |
| `fingerprint.py`(2) | `lut_fingerprint` | |
| `widths.py`(2) | `widths` | pdk_decl 최소 폭 필터 |
| `axis_guard.py`(2) | `check_axes` | 축 밖 실패 클래스 raise(core.failures) |
| `lut_memo.py`(2) | `LutMemo` | 영역·상계·카운터 |
| `point_query.py`(3) | `op_point` | |
| `gm_id_curve.py`(3) | `gm_id_curve` | |
| `vgs_root.py`(4) | `vgs_for_gm_id` | Hermite 칸 안 bisection(DEC-87) |
| `density_root.py`(4) | `vgs_for_current_density` | **[개정 Q3]** DEC-88, 파일 이름 [제안] |
| `id_inverse.py`(4) | `gm_id_for_target` | DF-10 |
| `gmb.py`(3) | `gmb` | |
| `cap_query.py`(3) | `caps` | |
| `tolerance.py`(5) | `tol_v_table`(+ `TolVTable.at`) | |
| `curve_check.py`(4) | `curve_report` | |
| `vdsat.py`(4) | `vdsat` | **[개정 Q1·Q3]** VDSAT 열 보간(DF-25 대체, DEC-88). 열 전에는 구조화 실패 |

test: `tests/lut/test_<파일>.py` 1:1 + `tests/fixtures/toy_lut.py`. 계층(core < lut) 밖 import 없음.

### 2.11 MOD1 test 요지

AST 해시(복사 4건·블록 복사 2건), 옛 `SemiEmpiricalGmIdLUT`(W_ref = 5 µm 슬라이스와 같은 배열로 구성) 대비 `op_point`·`vgs_for_gm_id` 값 동치(바닥 영역 제외), 축 밖 거부(VS·VGS·VDS·L, DF-27 red), 폭 키 밖 거부, 폭 사이 값 요청이 보간되지 않음, 5 µm 슬라이스↔기준 LUT 격자점 일치, `gmb` = 같은 보간 ID의 VS 방향 차분과 일치(독립 test 계산), tol_V 표가 손으로 만든 2앵커 합성 LUT에서 해석값과 일치, LUT memo 상계 초과 0·미퇴출 재계산 0, provenance `recorded=False` 전달.

---

## 3. MOD5 -- metric·MNA (`gmid_engine/metrics/`)

### 3.1 이식 대상 표

| 옛 이름 | 옛 위치 | 처리 | 새 위치 | 알려진 결함 |
|---|---|---|---|---|
| `build_ac_network` | SR:4067 | 새로(목적만 계승: ω 무관 조립 1회) | `mna_build.py` | 소자 리스트만 재사용하고 행렬은 ω마다 다시 스탬프(`full_circuit_response_at_omega` SR:4104), 고정 노드 `"gnd"` 이름 리터럴(DF-19·26), 경로 캐시로 topology 재로드(H 2985 계열) |
| `full_circuit_response_at_omega` | SR:4104 | 새로 | `mna_solve.py` | ω당 조립·풀이, 특이 행렬을 ValueError로 |
| `_mna_solve_smallsignal` | SR:4674 | 새로(고립 노드 진단 규칙만 계승) | `mna_build.py`(조립 시 검사) | 오류 문구가 파일럿 소자 이름(`battery_vop1_side`) -- DEC-62 |
| `_full_circuit_devices` | SR:4935 | 새로 | `mna_build.py` | 저항 기본값 `_DEFAULT_SENSE_RESISTOR_OHM = 1e9`(SR:4905, WP-03) |
| `_resolve_nulling_resistor_ohm` | SR:4908 | 새로(GB5 필드) | `compensation.py` | 캐시 키가 소자명뿐(DF-15) |
| `_mna_stamp_capacitance`·`_resolve_capacitor_farad` | SR:4029·3994 | 새로 | `ss_linearize.py`·`mna_build.py` | CGG 전부를 g–s에(CGD 무시), `except (KeyError, ValueError): continue`로 용량 조용히 누락(DF-06·DF-37), gmb 없음 |
| `_full_circuit_response`·`_metric_smallsignal_gain_db`·`_metric_smallsignal_ratio_db` | SR:4970·5042·5013 | 새로 | `gain.py`(`gain_ss_db`, `ratio_ss_db`) | `also_fix` 인자로 게이트 전용 노드 특이 회피(뷰 정의가 맡아야 함) |
| `_metric_parasitic_pm_deg` | SR:4166 | 새로(정의 계승: PM = 180° − DC 대비 누적 지연) | `gbw_pm.py` | ω_c를 spec·compensation 손값에서 읽음, 격자 25점·1e-4 상수(WP-03) |
| `_metric_supply_current` | SR:4339 | 새로 | `power.py` | 레일 이름 기본값 `("vdd","VDD")`(DF-19·26), 저항·이상전원 누락(자체 docstring C5 (1)(2)), 단일 레일(DEC-78 다레일) |
| `_metric_sum_current` | SR:2848 | 안 함 | -- | 직렬 기둥 중복 계상(DF-16) |
| `_metric_sum_area` | SR:2854 | 새로 | `area.py` | 수동소자 면적 없음(DEC-79 (a)) |
| `_METRICS_REGISTRY`·`compute_metric` | SR:5083·5280 | 새로 | `registry.py`·`evaluate.py` | 회로 이름 키 4개(DF-30), `circuit_family` 2단 레지스트리, 미등록 타입을 평가 시점에 거부 |
| `_METRIC_UNITS`·`_UNIT_SCALES`·`metric_unit_scale`·`validate_metric_units` | SR:5132·5158·5197·5245 | 개념 계승·새로 | `core/units.py` + 레지스트리 등록 단위 | 없음(A12 규칙 유지: 표에 없는 환산 거부) |
| `node_pole_estimate`·`signal_path_nodes` | SR:3917·3880 | 안 함 | -- | 광범위 except(DF-06), 응답 직접 풀이로 대체 |
| `_COMPENSATION_REGISTRY` + topology_library 회로별 함수 | SR:1416 | 안 함(규칙으로 대체) | `compensation.py` | 회로별 보상 함수 4개(DF-31) |
| `achievable_metric_bound` | SR:7721 | 안 함 | `achievability.py`(다른 정의) | SLSQP probe 방식 -- GB4는 S0당 1회 상한표 |
| 회로 전용 metric(`folded_cascode_*`·`nmcnr_*`·telescopic cmrr/psrr·`gain_stages_sum`) | SR:2893·2909·3019·3026·2860 등 | 안 함 | `gain_ss_db`·`ratio_ss_db` | DF-29·DF-30, P N3.8 이관표 |
| `_metric_kcl_residual` | SR:4267 | 안 함(MOD4 봉인 3) | -- | 레일 이름 기본 집합(DF-19·26) |

범위 밖(다른 MOD5 파일·뒤 단계): 스윙·`ls`(`ls_fields.py`), 오프셋(DF-05·DF-12), 잔차·감도 게이트, 출력 구동. 이 문서는 인터페이스만 맞춘다.

### 3.2 입력: 봉인 스냅샷 → S2 `ss` 필드 (`ss_linearize.py`, 계산 블록)

- 입력 = `SealedSnapshot`(타입으로 강제, DEC-67) + `LutSet` + 각 소자 `finger_w`(S2 레이아웃 필드, 없으면 2.2의 `w_ref_cap`과 같은 폭 키 -- 첫 사이징점) [제안: 이 기본 폭 규칙은 MOD4·MOD8 design과 같이 확정].
- 소자마다 `ss.dev[d] = {gm, gmb, gds, cgg, cgd, cgs, cgb, cdb, csb, cap_model, input_version}`(**[개정 Q6]** cdb·csb = `junction_caps` 블록 값, 입력 버전 = 봉인 `dc` 버전 + `ly.diffusion[d]` 버전 -- MOD8에서 nf가 바뀌면 그 소자만 무효): `gm = ID·gm_id`(dc 정의값), `gds = gds_per_w·W`, `gmb = gmb(…)·W/w_m`, 용량 = `caps(…, W)`. VGS·VDS·VSB는 `dc.node_v`에서 파생한 값(같은 vsb 버전을 W2 레벨 시프트와 gmb가 읽음, P N3.8 gmb 항목·SC-b).
- 노드 필드 `ss.node_c_farad`·`ss.node_g`(극점 노드용), 수동소자 값 `ss.passive`(writer: spec 선언 또는 GB5 보상 -- 노드·소자마다 writer 1개).
- **같은 값 반복 금지**: 소자 하나의 입력(op·finger_w)이 안 바뀌면 그 소자 필드는 재사용(구조 공유), 바뀐 소자만 새로 쓴다(FD 한 스텝 6.7/51 사례, REQ 4.3 #6).

### 3.3 MNA: 조립 1회, 주파수별 풀이만 [제안]

- **조립(`mna_build.py`, 계산 블록 → 필드 `ss.mna[view]`)**: 입력 = `ss`(dev·passive) 버전 + S1v 뷰(여기 노드·진폭, 교류접지 집합, sense). 출력 `MnaSystem {view_id, nodes(정렬 tuple), G(n×n 실수), C(n×n 실수), BG·BC(n×m, 여기원 m개 열), sense 행, 고립 노드 진단, input_version}`.
  - 소자 스탬프: `I(d→s) = gm(vg−vs) + gmb(vb−vs) + gds(vd−vs)`(bulk = S1 소자 `b`, 레일·교류접지면 고정 노드). 용량: cgd(g–d), cgs(g–s), cgb(g–b), **cdb(d–b), csb(s–b)**(**[개정 Q6]** DEC-91), 선언 커패시터(양 단자), 값 미선언 보상 수동소자는 θ 성분 값(**[개정 Q7]** DEC-92). 저항: 값은 `ss.passive`에서만(선언 없음 = 로드 거부, 1e9 기본값 폐기).
  - 고정 노드 = 뷰가 정한 교류접지(레일·바이어스 종속 넷, S1 `ac_ground_class`)와 여기 노드. 이름 리터럴 없음. 여기에 들지 않는 입력 포트를 0 V로 둘지는 뷰 정의(N3.2-2)가 정한다(옛 `also_fix` 인자 폐기).
  - 같은 뷰를 쓰는 metric(gain·UGF·GBW·PM·rout·ratio)은 **같은 MnaSystem 하나**를 읽는다. 여기 종류가 달라도 고정 노드 집합이 같으면 G·C는 같고 RHS 열만 다르다(CMRR의 num/den = 열 2개).
- **풀이(`mna_solve.py`, 계산 블록 → 필드 `ss.freq[view]`)**:
  - ω = 0: G를 LU 분해 1회(`scipy.linalg.lu_factor`), RHS 열 전부(여기원 m개 + rout용 출력 단위 전류)를 한 번에 푼다.
  - ω > 0: ω마다 `A(ω) = G + jωC`를 만들고 풀기만 한다(재스탬프 없음). 격자 전체를 `(k, n, n)` 묶음으로 `numpy.linalg.solve` 1회 호출. 결과 `H[view][excitation](ω)`를 필드에 저장, 모든 주파수 metric이 공유.
  - ω 격자(`omega_grid.py`): 상수 없이 계에서 유도 -- (G, −C) 일반화 고유값의 유한 크기 |s_k|와 sense 전달함수 영점(증강 pencil 고유값)의 크기를 꺾임점으로 두고, 인접 꺾임점 사이 기하 중점을 넣는다. 위상 언랩 시작점은 ω = 0의 실수 해(위상 0 또는 π)라 '충분히 낮은 시작 주파수' 상수가 필요 없다. 인접 격자점 위상 차가 π/2 이상이면 그 구간을 기하 2분할하고, 반복 상한은 N3.6 K_max 규칙(넘으면 NONCONVERGENT). 고유값은 **격자 배치에만** 쓰고 PM 계산에는 쓰지 않는다(옛 SR:4104 docstring의 거부 사유 -- 관측·제어 불가 bias 모드 -- 그대로 유효).
- 특이 계: 조립 때 0 행·열 노드 이름을 구조화 실패로(회로 이름 없는 문구). ω 풀이 특이는 그 ω와 함께 실패 기록.
- test(`test_mna_assembly_not_per_omega`): 주파수 응답 1회에서 조립 블록 쓰기 1, 풀이 블록 쓰기 1, 스탬프 함수 호출 1.

### 3.4 metric 정의 (레지스트리 변형군 = 파일 규칙 A의 한 개념)

| metric(정본 이름 후보, DEC-68) | 영역 | 정의 | 출처 |
|---|---|---|---|
| `gain_ss_db` | ss | 선언 전달 뷰의 `20·log10|H(0)|`(sense = 차동/단일 선언) | P N3.8 |
| `ratio_ss_db` | ss | 같은 MnaSystem 두 여기 열의 응답비 dB(옛 `smallsignal_ratio_db`, CMRR·PSRR 일반형) | DF-29·30 대체 |
| `ugf_ss_hz` | ss | `|H(ω)| = 1` 첫 교차: 격자에서 구간을 찾고 log ω 이분. 종료 = MNA 상대 잔차로 구별 불가한 폭(P N3.8 감도 게이트 ε 식) | [제안] |
| `gbw_ss_hz` | ss | `|H(0)| · f_3dB`, `f_3dB` = `|H| = |H(0)|/√2` 첫 교차(같은 이분 규칙). `gbw − ugf` 차를 함께 기록(단일 극점 가정의 진단) | [제안] |
| `parasitic_pm_ss_deg` | ss | `180° − (H(0) 대비 ugf까지 누적 위상 지연)`(옛 정의). 기준 주파수 = **같은 응답의 `ugf_ss_hz`**(옛: spec·compensation 손값 ω_c) | DEC-25, [제안 -- 열린 항목 O2] |
| `rout_ss_ohm` | ss | 여기원 전부 교류접지(고정값 0), 출력 포트에 1 A 주입 RHS -- ω = 0 같은 LU 재사용, 추가 분해 0 | DEC-66 |
| `supply_current_dc`(레일별 기록) | dc | 레일 k에서 회로로 들어오는 전류 `I_k` = 레일 노드에 닿는 MOS 채널 가지 전류(S2 `branch_i`, 단자 부호) + 저항 `(V_k − V_x)/R`(node_v) + 이상전원 선언값·θ 전류(`value_dc_amp`). 목적 축 = DEC-78 '선언 레일 기준 합' | DEC-78, DF-16 |
| `power_dc_w`(기록) | dc | `Σ_k V_k · I_k`. Σ I_k = KCL 잔차라 레일 원점 이동 불변(IC11)은 잔차 × 이동량 안에서 성립 -- test로 고정 | DEC-78 [제안: 목적 축을 이것으로 할지 O3] |
| `columns_current_check`(기록) | dc | '기둥마다 전류 한 번' 합과 `supply_current_dc` 차, `> tol_I`이면 `review_needed` | DEC-78 |
| `area_search_m2` | dc | `Σ_dev W·L` + 선언 수동소자 면적(값 × `core.pdk_decl` 단위 면적, U-36). 미선언이면 그 항 0 + `passive_area_undeclared` 매 실행 보고 | DEC-79 (a) |
| `area_layout_m2`·`area_axis_gap` | geom | MOD7가 쓴 S2 레이아웃 면적 필드를 읽고(import 아님, graph 필드 읽기) 탐색 축과의 차 기록, 선언 `max_error` 초과면 `review_needed`. 두 축이 수동소자 포함 여부를 매 실행 명시. **[개정 Q8]** 판정 축 면적에는 행 끝 dummy·tap·well 간격이 들어가고 '포함 항목'을 함께 낸다(LY10) | DEC-79 (b) |
| `nqs_ratio`(보고) | ss | **[개정 Q11]** `ugf_ss_hz` / min(신호 경로 소자 f_T), f_T = gm/(2π·cgg)(같은 `ss`, 추가 조회 0). 제약은 spec 임계 선언(출처 필수) 시만 | DEC-96 (1) |
| `mismatch_sigma_v`(보고) | dc→ss | **[개정 Q11]** matching 그룹마다 Pelgrom A_VT·A_β(PDK mismatch 파일 계수, `core.pdk_decl` 경로) × 봉인점 W·L·gm/ID, 입력 환산(DEC-23). 모든 front 점. 제약은 spec 선언 시만(U-17) | DEC-96 (2) |

공통: 모든 metric은 `SealedSnapshot`에서만(`ss`·`ls`), 레지스트리 항목 = {이름, 정규 단위, domain, 필요한 뷰 종류, 읽는 필드, `verified_by`, **`oracle_measure`**(**[개정 Q5]** 오라클이 재는 측정 이름 또는 없음 -- spec 로드 때 `spice_unverifiable[]` 사전 출력의 원천, DEC-90 (3))}. **[개정 MetricSignature, DEC-53]** 레지스트리가 내는 서명 = `MetricSignature(unit ∈ core/units.METRIC_UNITS(mv 포함), domain ∈ core/units.DOMAINS, view_kind ∈ {None, transfer, loop, output_port, ratio}, objective_axis ∈ OBJECTIVE_AXES)`. `pm_ss_deg` = loop, `rout_ss_ohm` = output_port, `ratio_ss_db` = ratio, `area_search_m2` domain = geom. loop·output_port 뷰 제약은 7a design의 뷰 정의(루프 끊는 점·출력 포트 주입) 전까지 pending 전용. 잡음·왜곡 metric은 레지스트리에 없다(9회로 스펙 없음, 선언되면 `metric_unknown`, DEC-96 (3)). 용량에 의존하는 metric(ugf·gbw·pm)은 `cap_model = "cgg_minus_cgd_at_gs"`인 동안 '근사(DF-28)'로 표시되고 `verified_by` 전까지 제약으로 쓰지 않는다(P N3.8). 미등록 type·회로 이름 키는 spec 로드에서 `SchemaRejectedError`(평가 시점 거부 폐기).

### 3.5 GB4·GB5를 MOD5에 둔다(확정, REQ C3 계층 위반 해소)

- 근거: GB4 상한은 블록 국소 소신호 모델(P N3.8, MOD5)로, GB5는 MNA 극점·영점(P 480)으로 계산되는데 P N3.1 표는 둘을 MOD4에 두었다 -- MOD4가 MOD5를 import하는 역방향(P 517 위반). 그래서 `metrics/achievability.py`(GB4)·`metrics/compensation.py`(GB5)로 옮긴다. MOD6(`search`)이 둘을 부르는 방향은 정방향이다.
- GB4(`achievability.py`, S0 단위 계산 블록 → 구조 필드 `structure.gain_bound[block]`): LUT 곡선 검사(`lut.curve_report`) + 블록 국소 모델의 완화 극값 상한: 격자 전 범위(LUT L 점과 bin 안 연속 L -- 구간 내부 극값이 L 점 값을 넘는지 확인, VDS, 레일 안 VS, 폭 슬라이스)에서 분자 소자는 최대 gm/ID, 분모 소자는 최소 gds/ID를 따로 골라 계산한다(소자별 gm/gds 최대 한 점을 넣는 것이 아니다). 상한이 LUT 범위 끝(격자 경계)에서 정해진 경우는 별도 분류로 표시한다(LUT 범위 한계이지 회로 한계가 아님). 봉인 불필요·INFEASIBLE 판정 전용. S0 지문당 1회, 7b 재계산은 이 표의 행 필터(P 461).
- GB5(`compensation.py`, 후보마다 계산 블록 → `ss.passive`·`ss.comp_constraints`) **[개정 Q7, DEC-92]**: S1v 극점 노드 목록에서 두 극점 노드 사이의 값 미선언 보상 수동소자를 찾아 **θ 연속 성분으로 MOD6 θ 스키마에 등록**하고(S0당 1회, 이 파일은 그 목록과 제약만 낸다), 후보마다 그 θ 값을 `ss.passive`에 쓴다. GBW·PM 판정은 같은 스냅샷 전회로 MNA의 `ugf_ss_hz`·`pm_ss_deg`(DEC-74). `gm_req`가 필요한 제약은 같은 MNA에서 '다른 θ 고정 시 제약을 만족하는 최소 gm_i'의 1-D 근 찾기. 영점 상쇄 저항: (a) 구조 규칙 R = 1/Σ_{c∈S} gm_c(S = 저항 끝 넷을 출력으로 갖고 루프 반대쪽에서 신호를 받는 CS 셀 집합, S1v에서 유도, 회로별 S는 J7 ratify) -- `ss.passive`에 쓰고 입력 버전 = S 소자 `ss` 버전(DF-15 소멸) (b) S가 정해지지 않으면 R도 θ 성분. 극점·영점 근사식은 층 0 시작점 생성에만 쓰고 근사 대 MNA 차 `comp_approx_gap`을 기록한다. 문헌 닫힌식은 test 오라클 전용(회로별 함수 금지 DF-31). 옛 '근사식으로 gm 요구량·수동소자 값 계산'은 폐기(TFD 3절: NMCNR 근사 GBW 2.5~21배 오차).
- 극점·영점(`poles_zeros.py`, **[개정 Q7]**): (G, C) 일반화 고유값(조립 지문 키, ω 무관). ω 격자 배치(3.3)와 같은 고유값 계산을 공유한다(같은 MnaSystem 필드에서 1회).
- 커널 순서(P N3.5 7b 순서와 같음): 봉인 → `ss_linearize` → `compensation`(passive 값) → `mna_build` → `mna_solve` → 제약 판정(①) → metric(⑥). 같은 스냅샷 값을 ①과 ⑥이 공유.

### 3.6 파일 목록 (`gmid_engine/metrics/`, 규칙 A~D)

| 파일(층) | 독립 진입점 / 계산 블록(C) |
|---|---|
| `junction_caps.py`(0) | `junction_caps` / 블록 `ss_junction` (**[개정 Q6]** DEC-91, 파일 이름 [제안]) |
| `ss_linearize.py`(0) | `linearize` / 블록 `ss_dev` |
| `ls_fields.py`(0) | `ls_fields` / 블록 `ls`(범위 밖, 인터페이스만) |
| `block_local.py`(1) | `block_local_model`(블록 국소 절점 방정식, GB4·잔차 공용) |
| `achievability.py`(2) | `gain_bound_table` / 블록 `gb4` |
| `compensation.py`(2) | `compensation_constraints` / 블록 `gb5` |
| `mna_build.py`(3) | `build_mna` / 블록 `mna` |
| `omega_grid.py`(3) | `omega_grid` |
| `poles_zeros.py`(3) | `poles_zeros` / 블록 `pz` (**[개정 Q7]** DEC-92) |
| `nqs.py`(5) | `nqs_ratio`(**[개정 Q11]** 보고) |
| `mismatch.py`(5) | `mismatch_sigma_v`(**[개정 Q11]** 보고) |
| `mna_solve.py`(4) | `solve_response` / 블록 `freq` |
| `gain.py`(5) | `gain_ss_db`·`ratio_ss_db`(레지스트리 변형군) |
| `gbw_pm.py`(5) | `ugf_ss_hz`·`gbw_ss_hz`·`parasitic_pm_ss_deg`(변형군) |
| `rout.py`(5) | `rout_ss_ohm` |
| `power.py`(5) | `supply_current_dc`·`power_dc_w`·`columns_current_check`(변형군) |
| `area.py`(5) | `area_search_m2`·`area_layout_m2`(변형군) |
| `registry.py`(6) | `metric_registry`(등록 데코레이터, 단위·domain·verified_by) |
| `evaluate.py`(7) | `evaluate_metrics` / 블록 `metrics`(봉인 스냅샷당 1회) |

test: `tests/metrics/test_<파일>.py` 1:1. 손계산 회로 oracle(CS 1단·차동쌍+미러·2단 Miller의 폐형식 gain·Rout·극점, **gmb 포함**)을 test 작성 주체가 독립으로 만든다.

### 3.7 MOD5 test 요지

조립 1회·ω 풀이만(계수), 같은 뷰 metric 공유(조립 쓰기 1), 소자 하나 섭동 시 그 소자 `ss` 필드만 새 버전, gmb 0으로 두면 손계산 값과 어긋나고 넣으면 일치(옛 결함 red), cgd 스탬프로 Miller 극점 이동 확인, 저항 미선언 로드 거부, 레일 이름을 바꾼 같은 회로에서 metric 값 동일(이름 리터럴 0), 레일 원점 이동 `power_dc_w`·`supply_current_dc` 불변(IC11 2·3레일), DEC-78 기둥 합과 차 ≤ tol_I, 수동소자 면적 미선언 보고, `cap_model` 근사 표시, GB4 S0당 1회 쓰기, GB5에 회로 이름 분기 0(`test_no_name_literals`).

---

## 4. 열린 항목·의존

| # | 항목 | 기본안 | 사용자 몫인가 |
|---|---|---|---|
| O1 | tol_V에 VDS·VS LOO 포함 | 해소: 계획 N3.6 사용자 확정(보간 축 VGS·VDS·VS + bin 안 L, 2026-10-07 'bin 안 L 보간' 결정으로 L 방향 재포함) | 해소(사용자 확정 2026-10-07) |
| O2 | PM 기준 주파수 = 같은 응답의 UGF(옛 손값 ω_c 폐기) | 채택 -- ω_c는 회로가 내는 값이고 손값은 WP-03 위반 | 아니오. 단 루프 뷰(되먹임 회로)에서 PM을 루프 이득 T로 잴지 전달 H로 잴지는 뷰 해석이라 **6a 루프 분류(J 항목)와 함께 사용자 확인** |
| O3 | 전력 목적 축 = `supply_current_dc`(DEC-78 문언) vs `power_dc_w`(다레일에서 전압 가중) | DEC-78 문언 유지, `power_dc_w` 기록 | 계획 DEC 변경이면 E1 개정 묶음으로 |
| O4 | 첫 사이징점의 finger_w 폭 키(레이아웃 전) | `w_ref_cap`과 같은 폭 키, MOD8 W_request 루프가 레이아웃 폭으로 갱신 | 아니오(MOD4·MOD8 design에서 확정) |
| D1 | U-27 기준 LUT 재생성(VS 0~1.8, CGS·CGB, **[개정 Q1]** VDSAT·GMBS·CDD·CSS, 잡음 `SVG2_1HZ`·`SVG2_HF`(옛 SID_1F 개명), L 상한 20 µm, 생성기 수정, 앵커 kind 공통. 전 폭 AC·잡음은 나중) | 그 전까지 용량 VS > 0.8 실패 기록, `cap_model` 근사, gmb 임시(2.8), 봉인 7 '정의 미확정' | 계획 확정 항목(일정만) |
| D3 | **[개정 Q2·Q3·Q6·Q7]** 계약 `gmid_engine/lut/CONTRACT.md`의 다선형 AST 고정(6절)·tol_V 정의·vdsat '소비자 없음'(8절)과 MOD5 쪽 GB5 근사식 문구 | 이 문서 2.2a·2.7·2.8·3.5로 대체 -- 계약 개정은 담당 작업 몫 | 아니오(사용자 확정 2026-10-07) |
| D2 | 폭 슬라이스 생성 완료(`_drafts/engine/lut_slices/`) | `load_lut_set`이 `manifest.json` 존재를 요구 -- 생성 중에는 MOD1 통합 test 보류 | 아니오 |

회로 해석 항목(사용자 승인 대상, E7)은 이 두 MOD에 O2의 루프 뷰 부분 하나뿐이다.
