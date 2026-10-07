# gmid_engine.lut 동작 계약 (MOD1, test 작성용)

- 대상: `gmid_engine/lut/` 공개 API(`gmid_engine.lut.__all__`). test 는 `from gmid_engine.lut import ...` 만 쓴다
  (파일 모듈 직접 import·`_` 이름 사용 금지). test 배치 규칙 D: `gmid_engine/tests/lut/test_<파일>.py`
  (helper 는 `test__helpers_interp.py` 처럼 글자 그대로).
- 근거: `_drafts/engine/design_mod1_lut_mod5_mna.md` 2절(MOD1), `_drafts/engine/NEW_ENGINE_DESIGN_REQUIREMENTS.md` 끝 '확정 사항',
  `_drafts/engine/tol_v_measurement.md`(분지 점프 결함·두 지표), core 계약 `gmid_engine/core/CONTRACT.md`.
- 실패 객체는 core 의 `SchemaRejectedError`(로드 거부)·`SealViolationError`(조회 실패)다. `record.detail` 은
  `{"reason": <사유 키>, ...}` 의 키 정렬 쌍 tuple 이고 `record.devices == ()`, `record.margin is None`
  (LUT 는 소자 이름을 모른다 -- 소자를 아는 호출부가 덧붙인다, P-28·P-34).

---

## 0. 파일과 진입점 (구조 규칙 A~G, `_module_map.LAYERS["lut"]`)

| 층 | 파일 | 진입점 / 종류 |
|---|---|---|
| 0 | `_helpers_fail.py` | helper: `schema_rejected`, `seal_violation` |
| 0 | `_helpers_interp.py` | helper: `multilinear_interp`, `multilinear_interp_point_multi`(옛 본문 복사) |
| 0 | `_helpers_root.py` | helper: `peak_index`, `strong_inversion_root` |
| 0 | `lut_types.py` | 데이터 선언 모듈(`LutSpec`·`SliceSource`·`LutProvenance`·`DcSlice`·`CapTable`·`LutSet`·`OpPoint`·`Curve`·`TargetSolution`·`Caps`·`TolVCell`·`CurveRow`·`CurveReport`, 상수 `AXES`·`TOL_V_METRICS`) |
| 0 | `fingerprint.py` | `lut_fingerprint` |
| 0 | `lut_memo.py` | `LutMemo` (+ 상수 `REGIONS`·`DERIVED_TABLES`) |
| 0 | `widths.py` | `widths` |
| 1 | `axis_guard.py` | `check_axes` |
| 1 | `curve_check.py` | `curve_report` |
| 1 | `provenance.py` | `lut_provenance` |
| 2 | `lut_set.py` | `load_lut_set` |
| 2 | `point_query.py` | `op_point` |
| 2 | `gm_id_curve.py` | `gm_id_curve` |
| 2 | `gmb.py` | `gmb` |
| 2 | `cap_query.py` | `caps` |
| 2 | `tolerance.py` | `tol_v_table` (`TolVTable` 은 비진입 공개 이름) |
| 3 | `vgs_root.py` | `vgs_for_gm_id` |
| 3 | `id_inverse.py` | `gm_id_for_target` |

graph 밖 상태는 `LutMemo` 하나뿐이다(모듈 수준 캐시 0). 조회 함수는 모두 첫 인자로 `LutMemo` 를 받는다.

---

## 1. 입력 파일 형식과 로드

### 1.1 `LutSpec(manufacturing_grid_m, min_finger_w_m, device_kinds, cap_column_suffix)` -- frozen dataclass
- `manufacturing_grid_m`: float(m). `min_finger_w_m`: `((kind, m), ...)`. `device_kinds`: `((manifest device, kind), ...)`.
  `cap_column_suffix`: `((kind, 접미사), ...)`. 값은 부르는 쪽이 PDK 선언에서 채운다(엔진 안 숫자 0).

### 1.2 manifest(`manifest.json`)와 슬라이스 npz
- manifest: `{"generator_sha256": str, "slices": [{"device": str, "file": <manifest 폴더 기준 상대 경로>, "sha256": hex}, ...]}`
  (다른 키는 무시). 경로는 인자로만 받는다.
- 슬라이스 npz 키: `W`(m, 스칼라), `L`(m)·`VGS`·`VDS`·`VS`(V, 오름차순 1차원), `ID`·`GM`·`GDS`·`VTH` 형상
  `[len(L), len(VGS), len(VDS), len(VS)]`(그 폭의 절댓값), `meta_json`(JSON 문자열, `model_files_sha256` 객체 선택),
  측정 조건 `corner`·`temp_c`(선택 -- 없으면 recorded=False).
- 기준 LUT(용량) npz 키: `L`·`VGS`·`VDS`·`VS`, kind 마다 `CGG<접미사>`·`CGD<접미사>`(필수), `CGS<접미사>`·`CGB<접미사>`(선택),
  `ID<접미사>`(폭 판정용, 선택), `w_ref_m`(선택), `corner`·`temp_c`(선택).

### 1.3 `lut_provenance(manifest_path, cap_npz_path, spec) -> LutProvenance`
- 슬라이스마다 파일 sha256 을 다시 재서 manifest 값과 대조. 폭 키 `w_key = round(W / grid)`(int).
- `slices` 는 (kind, w_key) 정렬 `SliceSource` tuple. `conditions`·`cap_conditions` 는 옛 `lut_conditions_from_npz` 결과의
  키 정렬 쌍 tuple: 기록 있음 → `(("corner", str), ("recorded", True), ("temp_c", float))`, 없음 → `(("note", str), ("recorded", False))`.
- 실패(`SchemaRejectedError`, reason): `lut_manifest_missing`, `lut_device_undeclared`(device_kinds 밖), `lut_slice_missing`,
  `lut_slice_sha256_mismatch`, `lut_width_off_grid`(|W/grid − w_key| > `2·ulp(W/grid)`), `lut_slice_duplicate`(같은 (kind, w_key)),
  `lut_manifest_empty`, `lut_cap_missing`.

### 1.4 `load_lut_set(manifest_path, cap_npz_path, spec) -> LutSet`
- `LutSet(spec, provenance, slice_map, cap_map, fp)`: `slice_map` = 읽기 전용 매핑 {(kind, w_key): DcSlice}, `cap_map` = {kind: CapTable}.
- `DcSlice`: `grids` = 축별 float tuple 4개, 배열은 읽기 전용 numpy. 로그 배열 `log_ID·log_GM·log_GDS` = `ln(clip(배열, 그 배열의 최소 양수값))`
  (상수 바닥 없음), `floors`·`nonpositive` 에 바닥값·0 이하 원소 수 기록, `on_mask = (ID > 0) & (GM > 0)`.
- 불변식: 모든 슬라이스의 L·VGS·VDS·VS 가 float 단위로 같다. 측정 조건(`conditions`)이 모두 같다. 기준 LUT 조건이 기록돼
  있으면 corner·temp_c 가 슬라이스와 같다. 기준 LUT L·VGS·VDS 가 슬라이스와 같다(VS 는 달라도 됨).
- **용량 기준 폭 `CapTable.w_ref_m`**: (1) 기준 npz 에 `w_ref_m` 이 있으면 그 값, `basis == (("method", "recorded_w_ref_m"),)`
  (2) 없으면 `ID<접미사>` 와 같은 kind 슬라이스 `ID` 를 기준 VS 값이 슬라이스 VS 축에 정확히 있는 열·기준 ID > 0 인 점에서 비교한다.
  d_s = max |ID_s − ID_ref| / |ID_ref|. 최소 d 인 슬라이스 w 를 고르되 **d_w < (w 와 가장 가까운 다른 슬라이스 사이의 같은 차) / 2**
  일 때만 채택. `basis` = `(("max_rel_diff", d_w), ("method", "slice_id_match"), ("nearest_other_rel_diff", 그 차), ("w_key", w))`.
- `fp == lut_fingerprint(provenance, ((kind, w_ref_m, basis), ...))`.
- 실패(`SchemaRejectedError`, reason): 1.3 전부 + `lut_conditions_mismatch`, `lut_slice_axes_mismatch`, `lut_slice_shape_mismatch`,
  `lut_array_no_positive`, `lut_cap_axes_mismatch`, `lut_cap_kind_undeclared`, `lut_cap_column_missing`, `lut_cap_width_unresolved`
  (슬라이스 1개뿐·동률·분리 조건 불충족·VS 값이 슬라이스 축에 없음·`w_ref_m`·`ID` 열 둘 다 없음).
- [실측 2026-10-07, 생성 완료 슬라이스 32개 + `assets/sky130_nfet_pfet_lut_sample.npz`] 로드 1.5 s, nmos·pmos 모두 w_key 1000
  (5 µm) 채택, d_w ≈ 5.0e-7, 이웃 차 0.88(nmos)·1.25(pmos).

### 1.5 `lut_fingerprint(provenance, cap_basis) -> str`
- 64자 hex = `core.fp_of` of (manifest sha256, 생성기 sha256, 슬라이스별 (kind, w_key, 파일 sha256, 조건, 모델 파일 sha256),
  기준 LUT sha256·조건, cap_basis). 파일 경로는 들어가지 않는다(같은 파일을 다른 폴더로 옮겨도 같은 지문), 어느 sha256 이든
  바뀌면 다른 지문.

### 1.6 `widths(lut, kind) -> tuple[int]`
- `kind` 슬라이스 폭 키 중 `w_key · grid ≥ min_finger_w_m[kind]` 인 것의 오름차순. 근접 폭 대체·보간 없음.
- 실패: `min_finger_w_m` 에 kind 없음 → `KeyError`. 그 kind 슬라이스가 없으면 `()`.

---

## 2. memo `LutMemo(lut, *, point, curve, root)`

- 상한 인자: 1 이상 int(아니면 core `BoundedLRU` 의 `ValueError`). `derived` 영역 상한 = `len(lut.slice_map) * len(DERIVED_TABLES)`.
- `LutMemo.from_sweep(lut, n_theta, unique_keys_per_eval)`: 영역 r ∈ {point, curve, root} 상한 = `(n_theta + 1) * unique_keys_per_eval[r]`
  (`unique_keys_per_eval` 은 Mapping 또는 (영역, int) 쌍).
- `lookup(region, fn_name, key, compute)`: 키 = `(lut.fp, fn_name) + tuple(key)`. 적중이면 저장 값 그대로(`is`), 아니면 compute 1회.
  가변 원소가 든 키 → `TypeError`. 알 수 없는 region → `KeyError`.
- `stats()` → `(("curve", LruStats), ("derived", ...), ("point", ...), ("root", ...))`.
- 조회 함수별 영역: `op_point`·`gmb`·`caps` = point, `gm_id_curve` = curve, `vgs_for_gm_id`·`gm_id_for_target` = root,
  `tol_v_table`·`curve_report` = derived. 같은 인자 두 번 → 두 번째는 compute 0(그 영역 hits +1). 실패한 조회는 저장되지 않는다.
- 같은 내용의 LutSet 두 개(같은 파일, 다른 폴더)는 같은 `fp` 라 같은 키가 된다.

---

## 3. 분지 규칙(정본) -- `vgs_for_gm_id`·`gm_id_for_target`·`tol_v_table`·`curve_report` 공통

- 곡선 = 고정 (L, VDS, VS) 의 VGS 격자 위 gm/ID. **정점 index p** = gm/ID 최댓값의 첫 index(`argmax`).
- **강반전 분지 = index p 이상(VGS ≥ VGS[p])**. 목표를 품는 구간(두 끝점 편차 곱 ≤ 0)은 분지 안의 구간 [i, i+1] (i ≥ p) 만 보고,
  그중 가장 오른쪽을 고른다. 분지 안에 그런 구간이 없으면 **해 없음 = 실패**(정점 왼쪽 해로 내려가지 않는다).
- 왜 새로 썼나: 옛 `_solve_vgs` 는 전 구간에서 가장 오른쪽 구간을 골라, 분지 안에 해가 없으면 정점 왼쪽 누설 분지(VGS≈0)의 교차를
  ValueError 없이 돌려줬다(tol_V 실측: 유효 목표 184,027 중 3,918(2.13%), 오차 최대 1.78 V). 그래서 구간 선택(분지 거르기·해 없음)은
  새로 쓰고, 고른 구간의 2점 역보간 문장만 본문 그대로 복사했다(6절 구간 A·B). 옛 결과가 분지 안의 해였던 입력에서는
  새 결과가 비트 단위로 같다(분지 거르기는 옛 후보 집합의 부분집합을 남기고, 가장 오른쪽 구간은 그대로다).

---

## 4. 조회 API

공통: 축 이름 `AXES = ("L", "VGS", "VDS", "VS")`, L 은 m, 전압은 V(VS = vsb 크기). 입력 숫자는 `float()` 로 바꿔 쓴다.
축 밖(격자 최소·최대 밖, NaN 포함) → `SealViolationError` reason `lut_axis_out_of_range`, detail `axis, value, lo, hi, kind, w_key`
(용량은 `w_key` 대신 `table: "cap"`, tol_V 는 `table: "tol_v"` 추가). 클램프·외삽 없음. 격자 끝점 자체는 축 안(정확값).
(kind, w_key) 슬라이스가 없으면 `KeyError`(계약 위반 -- 폭은 `widths()` 에서만 고른다).

| 함수 | 반환 | 정의 |
|---|---|---|
| `check_axes(grids, names, point, context=())` | None | 위 축 검사. `context` 쌍은 detail 에 더해진다 |
| `op_point(memo, kind, w_key, L, vgs, vds, vsb)` | `OpPoint` | 4축 다중선형 보간 1회: lnID·lnGM·lnGDS 로그공간, VTH 선형. `IDu = ID·L/w_m`, `gm_over_id = exp(lnGM−lnID)`, `gm_gds = exp(lnGM−lnGDS)`, `gds_per_w = GDS/w_m`, `vth` |
| `gm_id_curve(memo, kind, w_key, L, vds, vsb)` | `Curve` | VGS 격자 전체에서 lnID·lnGM 보간: `id_vals = exp(lnID)`(폭 w_m 의 A), `gm_id_vals = exp(lnGM−lnID)`. `vgs_grid` 는 슬라이스 VGS 축. 배열 읽기 전용. VGS 축 검사는 없다(격자 전체) |
| `vgs_for_gm_id(memo, kind, w_key, gm_id, L, vds, vsb)` | float V | 3절 규칙으로 `gm_id_curve` 의 gm/ID 격자 값에서 선형 역보간(곡선 격자 위 gm/ID 가 VGS 에 대해 선형인 근사 -- `op_point(vgs).gm_over_id` 와는 칸 안에서 다를 수 있다). 해 없음 → `SealViolationError` reason `lut_no_strong_inversion_root`, detail `gm_id, L, vds, vsb, kind, w_key, branch_gm_id_min, branch_gm_id_max, peak_vgs` |
| `gm_id_for_target(memo, kind, w_key, L, vds, vsb, *, W, gm=None, current=None)` | `TargetSolution(vgs, gm_id, id_a, gm_s)` | Q = `id_vals·W/w_m`(current) 또는 `id_vals·gm_id_vals·W/w_m`(gm). 분지 index p 부터 Q 가 엄격히 증가하는 첫 구간 [p, e] 에서 ln Q 를 VGS 에 대해 선형으로 풀어 vgs, 그 vgs 의 `op_point` 로 `gm_id`, `id_a = IDu·W/L`, `gm_s = gm_id·id_a`. 목표가 Q[p]..Q[e] 밖이고 분지 Q 범위 밖 → reason `lut_target_out_of_range`, 범위 안이지만 단조 구간 밖에서만 닿음 → `lut_target_non_monotonic`(detail `quantity, target, W, L, vds, vsb, kind, w_key, branch_min, branch_max, monotone_lo, monotone_hi`). `gm`·`current` 둘 다/둘 다 없음, `W ≤ 0` → `ValueError` |
| `gmb(memo, kind, w_key, L, vgs, vds, vsb)` | float A/V(폭 w_m) | VS 칸 k = `min(bisect_right(VS, vsb) − 1, len(VS) − 2)`, `gmb = −exp(lnID(점)) · (lnID(VS[k+1]) − lnID(VS[k])) / (VS[k+1] − VS[k])`(다른 축은 조회점 값으로 보간). 소자 폭 W 값 = `× W / w_m`(부르는 쪽) |
| `caps(memo, kind, L, vgs, vds, vsb, W)` | `Caps(cgg, cgd, cgs, cgb, model)` F | 기준 LUT 열 선형 보간 × `W / w_ref_m`. CGS·CGB 열이 있으면 `model = "lut_cgs_cgb"`, 없으면 `"cgg_minus_cgd_at_gs"`(cgs = cgg − cgd, cgb = 0.0). 축은 기준 LUT 축(현재 VS 0~0.8 → vsb > 0.8 실패). kind 표 없음 → `KeyError` |
| `tol_v_table(memo, kind, w_key)` | `TolVTable` | 5절 |
| `curve_report(memo)` | `CurveReport(lut_fp, rows)` | 슬라이스·L 앵커마다 `CurveRow`(lut_types 문서): 격자점 곡선만, ID·GM 에 0 이하 점이 있는 곡선은 `n_skipped`. 행 순서 (kind, w_key) 정렬 후 L 오름차순 |

---

## 5. tol_V 표 `tol_v_table(memo, kind, w_key) -> TolVTable` (계획 N3.6)

- **셀별 값만 낸다**(`cells[i_L][i_vds]` = `TolVCell`) -- 전역 최댓값으로 줄이지 않는다. **두 지표를 모두** 낸다
  (`TOL_V_METRICS = ("gm_id_inverse", "id_equivalent")`) -- 어느 지표를 어느 봉인·허용오차에 쓸지는 사용자 결정 대기라 고르지 않는다.
- 내부 앵커 i(양끝 제외)마다 (VDS k, VS s):
  - 곡선 i−1·i·i+1 의 그 (k, s) 에 `on_mask` 거짓 점이 하나라도 있으면 목표 없음.
  - LOO 곡선: L 격자 (L[i−1], L[i+1]) 2점 × VGS 격자로 `multilinear_interp`(운영 보간과 같은 함수, lnID·lnGM) 를 L[i] 에서.
  - 목표 j: 참 곡선(앵커 i 의 격자값) gm/ID g 의 정점 이후 index 중 오른쪽 모든 점보다 g_j 가 큰 점(= VGS_j 가 그 곡선의 분지 해).
  - `gm_id_inverse`: |strong_inversion_root(LOO g, VGS, g_j) − VGS_j|. 해 없으면 값에 넣지 않고 `n_inverse_failed` +1.
  - `id_equivalent`: |lnID_loo[j] − lnID[j]| / g_j.
  - 셀 값 = 그 (i, k) 의 모든 s·j 최댓값(없으면 None). `n_targets`·`n_inverse_failed` 는 합계. 양끝 앵커 셀 = `TolVCell(None, None, 0, 0)`.
- `TolVTable.at(L, vds, metric)`: L 칸 j = `min(bisect_right(L_anchors, L) − 1, n − 2)`, VDS 칸 k 같은 규칙, 네 셀 (j|j+1, k|k+1) 의
  그 지표 값 중 정의된 것의 최댓값(없으면 None -- 끝 앵커 칸은 이웃 내부 앵커 값만 남는다). `metric` 이 TOL_V_METRICS 밖 → `ValueError`,
  축 밖 → `SealViolationError`(`lut_axis_out_of_range`, table "tol_v").
- `TolVTable` 속성: `kind, w_key, L_anchors, vds_grid, cells`.
- [실측] 생성 슬라이스 pmos w_key 1000 한 장 계산 7.9 s. 참고: 측정 문서(`tol_v_measurement.md`)는 켜짐 판정에 `ID ≥ 1e-12 A` 상수를
  썼고 이 구현은 상수 대신 `on_mask`(ID·GM > 0) + 분지 목표 규칙을 쓴다 -- 정점 부근 평탄 구간 목표가 포함돼 gm_id_inverse 셀 값이
  측정 문서보다 클 수 있다(예: pmos L=0.7 µm, VDS 0.9 V 셀 670 mV -- 최댓값은 VGS=0 정점 목표에서, 정점 근접 조건수 효과).

---

## 6. 복사본 AST 해시 (설계 2.1 '복사'·'블록 복사')

판정: 대상 문장 목록(docstring 제외)의 `ast.dump(Module(body=문장들), include_attributes=False)` sha256 이 옛 것과 같다.
함수 이름 변경은 허용. 블록 복사는 (첫 문장, 끝 문장) 앵커로 구간을 자르고, 이름 바꿈 표를 옛 AST 에 적용한 뒤 비교한다.
옛 파일 `legacy/sizing_recipe.py`(이 브랜치) = 태그 `legacy-engine-v1`(`skills/analog-gmid-design/assets/sizing_recipe.py`)의 같은 정의(해시 같음).

| 새 위치 | 옛 위치 | 문장 수 | 이름 바꿈 | sha256 (옛 = 새) |
|---|---|---|---|---|
| `_helpers_interp.multilinear_interp` 본문 | `_multilinear_interp` SR:141 | 8 | (함수 이름만) | `d6bfc65c25e6e68f6b5f820c3a5a53ed6ed2429db00dc640ba15615dc7d69c54` |
| `_helpers_interp.multilinear_interp_point_multi` 본문 | `_multilinear_interp_point_multi` SR:206 | 7 | (함수 이름만) | `76e24d9d66e06b760dc79b9d69ac51143cec7238046f9ed3ffd27a4b624c7cba` |
| `provenance._lut_conditions_from_npz` 본문 | `lut_conditions_from_npz` SR:4782 | 3 | (함수 이름만) | `20513c618b94f19b50d8a4fcfc2fd0a17f934302259ed4e78d4b21163451235b` |
| `gm_id_curve._curve_arrays` `n = len(sl.VGS_grid)` ~ `result = (id_vals, gm_id_vals)` | `_gm_id_curve` SR:463~474 | 7 | `self`→`sl`, `_multilinear_interp`→`multilinear_interp`, `._grids_list`·`._log_ID`·`._log_GM` → 밑줄 없는 속성 | `a84728e5e100c2c99d70529188915128fcf02ed5b8fa660c7bcf85941718743f` |
| `_helpers_root.strong_inversion_root` 구간 A `d = g - gm_id` ~ `idx = np.flatnonzero(...)` | `_solve_vgs` SR:539~540 | 2 | 없음 | `0a86bafdeaddf5c9a83cfce762d1a47b01dd6051c285ded5e26b803a4d0fc729` |
| `_helpers_root.strong_inversion_root` 구간 B `i = int(idx[-1])` ~ `if x1 == x0: ...` | `_solve_vgs` SR:548~561 | 5 | 없음 | `29beb488b7222e495e3794d5685bd0d751289e08dc502368f9e7af3143c51680` |

구간 A 와 B 사이(분지 거르기·해 없음 처리)는 3절 사유로 새로 쓴 문장이라 대조 대상이 아니다. 옛 `_solve_vgs` 의
`_, g = self._gm_id_curve(...)`·`vgs_grid = self.VGS_grid`·캐시 줄, `_gm_id_curve` 의 캐시 줄은 옮기지 않았다.

---

## 7. 손계산 toy (test 작성자가 그대로 만들 수 있는 입력)

축: `L = (1e-6, 2e-6, 3e-6)`, `VGS = (0.0, 0.5, 1.0)`, `VDS = (0.5, 1.0)`, `VS = (0.0, 0.5)`.
폭 1e-6 m 슬라이스: `ID[iL, iG, k, s] = (1e-6 / L[iL]) · (1e-7, 1e-6, 1e-5)[iG] · (1.0, 0.5)[s]`(VDS 무관),
`GM = ID · (20, 10, 4)[iG]`, `GDS = ID / 10`, `VTH = 0.4`. 폭 2e-6 m 슬라이스 = 위 ID·GM·GDS × 2(같은 VTH).
두 파일 모두 `corner="tt"`, `temp_c=27.0`, `meta_json='{"model_files_sha256": {}}'`. manifest device `"toyn"`.
기준 LUT: 같은 축, `CGG_n = 1e-15`, `CGD_n = 2e-16`(상수 배열), `w_ref_m = 1e-6`, `corner`·`temp_c` 같음.
`LutSpec(1e-8, (("nmos", 1.5e-6),), (("toyn", "nmos"),), (("nmos", "_n"),))`. 폭 키 100·200.

| 호출 | 기대값 |
|---|---|
| `widths(lut, "nmos")` | `(200,)` |
| `op_point(m, "nmos", 100, 1e-6, 0.25, 0.5, 0.0)` | IDu = √(1e-7·1e-6) = 3.16228e-7, gm_over_id = √(20·10) = 14.1421, gm_gds = √(200·100) = 141.421, gds_per_w = 0.0316228, vth 0.4. w_key 200 도 같은 값(정규화 확인, 마지막 몇 ulp 차이 허용) |
| `vgs_for_gm_id(m, "nmos", 100, 15.0, 1e-6, 0.5, 0.0)` | 0.25 (정점 index 0, 구간 [0, 1] 선형) |
| `vgs_for_gm_id(..., 25.0, ...)` | `SealViolationError` reason `lut_no_strong_inversion_root`, peak_vgs 0.0 |
| `gmb(m, "nmos", 100, 1e-6, 0.5, 0.5, 0.25)` | −√(1e-6·5e-7) · ln(0.5) / 0.5 = 9.80258e-7 |
| `caps(m, "nmos", 1e-6, 0.5, 0.5, 0.0, 3e-6)` | cgg 3e-15, cgd 6e-16, cgs 2.4e-15, cgb 0.0, model `"cgg_minus_cgd_at_gs"` |
| `gm_id_for_target(m, "nmos", 100, 1e-6, 0.5, 0.0, W=2e-6, current=2e-6)` | vgs 0.5, gm_id 10, id_a 2e-6, gm_s 2e-5 |
| 같은 호출 `current=1e-4` | `SealViolationError` reason `lut_target_out_of_range` |
| `op_point(..., vsb=0.6)` | `SealViolationError` `lut_axis_out_of_range`, axis "VS", lo 0.0, hi 0.5 |
| `tol_v_table(m, "nmos", 100).cells[1][k]` | id_equivalent_v = ln(2/√3) / 4 = 0.0359603(LOO lnID 는 ln(1/1)·ln(1/3) 평균 → ID 비 2/√3, 최소 g = 4), gm_id_inverse_v ≈ 0(gm/ID 가 L 무관이라 LOO 곡선 = 참 곡선; 부동소수 수준), n_targets 6. 정점 목표(g = 20)는 LOO 곡선 끝값의 반올림에 따라 해 없음으로 셀 수 있다(현 구현 n_inverse_failed = 1) |
| `cells[0][k]`, `cells[2][k]` | `TolVCell(None, None, 0, 0)` |
| `at(1.5e-6, 0.75, "id_equivalent")` | 0.0359603(앵커 0 은 None, 앵커 1 값) |
| `curve_report(m).rows[0]` | kind nmos, w_key 100, L 1e-6, n_curves 4, n_skipped 0, n_branch_nonmonotonic 0, gm_id_max 20, gm_gds_max 200 |

---

## 8. 범위 밖·보류

- `vdsat`(설계 2.10): 규칙 미확정(DF-25, 6b)·소비자 없음 → 만들지 않음. `gm_id_for_vgs`: 소비처 미확정(DEC-76) → 만들지 않음.
- E3 디스크 캐시(tol_V 표·곡선 보고 지문 키): 이 단계 밖. 현재 derived memo(실행 내)만.
- toy LUT 픽스처(`tests/fixtures/toy_lut.py`, 옛 `_invq_newton`·`build_toy_lut` 복사)는 test 작성자 몫.
- 옛 `SemiEmpiricalGmIdLUT`(W_ref = 5 µm 슬라이스 배열) 대비 `op_point`·`vgs_for_gm_id` 동치 test: 옛 로그 바닥(1e-18·1e-30)과 갈리는
  점(ID < 1e-18)은 비교에서 뺀다. 옛 해가 정점 왼쪽인 입력은 새 쪽이 실패해야 한다(3절).
