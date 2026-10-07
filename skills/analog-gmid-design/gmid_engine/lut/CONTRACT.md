# gmid_engine.lut 동작 계약 (MOD1, test 작성용)

- 대상: `gmid_engine/lut/` 공개 API(`gmid_engine.lut.__all__`). test 는 `from gmid_engine.lut import ...` 만 쓴다
  (파일 모듈 직접 import·`_` 이름 사용 금지). test 배치 규칙 D: `gmid_engine/tests/lut/test_<파일>.py`
  (helper 는 `test__helpers_interp.py` 처럼 글자 그대로).
- 근거: `_drafts/engine/design_mod1_lut_mod5_mna.md` 2절(MOD1), `_drafts/engine/NEW_ENGINE_DESIGN_REQUIREMENTS.md` 끝 '확정 사항',
  `_drafts/engine/tol_v_measurement.md`(분지 점프 결함·두 지표), core 계약 `gmid_engine/core/CONTRACT.md`.
- **개정 r2(2026-10-07, 사용자 확정 계획 N3.9 LR3·N3.6)**: 바뀐 곳에 `[r2]` 표시. 요지 -- L 은 LUT L 앵커 이산 키만(L 방향 보간 0,
  4.0절), tol_V 는 보간 축 VGS·VDS·VS leave-one-out(5절 전면 교체), 용량 kind 집합 fail-closed·`nearest_other_rel_diff` 분모(1.4),
  `CurveRow.n_curves` 정의(4절 표), 0절 파일 표(`_helpers_anchor.py`·층), 6절 gm_id_curve 블록 비고, 7절 toy 기대값.
- **개정 r4(2026-10-07, 사용자 결정 'L 은 같은 PDK 모델 bin 안 두 LUT 점 사이에서만 선형 보간')**: 바뀐 곳에 `[r4]` 표시.
  r2 의 'L 보간 0' 을 대체한다. 요지 -- 로드 때 슬라이스 meta 의 모델 파일에서 L bin 지도(`LBinMap`)를 한 번 만들고(1.2·1.3·1.4),
  조회 L 은 앵커(r2/r3 그대로) 또는 같은 bin 의 양옆 앵커 사이 보간, bin 경계를 건너면 거부(4.0 전면 교체·새 사유 키 3개),
  tol_V 에 같은 bin 안 L 방향 LOO 와 앵커 2개 bin 의 외부 오차 입력(5절), 0절 파일 표(`_helpers_bins.py`).
- **개정 r5(2026-10-07, 사용자 결정 reference 검토 Q2 (i) 예·(ii) (A) = 계획 DEC-87·N3.6·N3.7)**: 바뀐 곳에 `[r5]` 표시.
  r4 까지의 '3축 다중선형(로그공간)'을 대체한다. 요지 -- ln ID 는 **VGS 축 2점 cubic-Hermite(기울기 = 저장 GM/ID)·VDS 축 2점
  cubic-Hermite(기울기 = 저장 GDS/ID)**, VS·L 축 선형(L 은 r4 의 bin 안 선형 그대로), ln GDS·VTH·용량은 모든 축 선형.
  **gm/ID 는 그 다항식의 VGS 미분으로 정의**(op_point·gm_id_curve·역산이 한 곡면, 4.2). 역산은 같은 Hermite 칸 안 bisection(3절).
  로드 때 Hermite 칸마다 Fritsch–Carlson 단조 조건을 검사해 기록하고 위반 칸은 선형·역산 거부(1.4·4.2). tol_V 는 운영 보간과
  같은 방법의 LOO 를 Richardson 2^p 로 환산(5절). 옛 다선형 복사본은 패키지에서 빠지고 기대값 비교 참조(옛 파일 원본)로만 남는다(6절).
  7절 toy 를 기울기가 자료와 맞는 r5 toy 로 바꿨다(r4 toy 는 FC 위반 예시로 남김).
- **개정 r6(2026-10-08, LUT v2 배선 -- 재생성 데이터 `lut_v2/`, sizing 계약 12절 O1)**: 바뀐 곳에 `[r6]` 표시. 요지 --
  (1) 로더가 LUT v2 선택 열(GMBS·VTH·VDSAT·CDD·CSS·SVG2_1HZ·SVG2_HF·ID·GM·GDS)을 읽고, 열이 없는 옛 12-L 세트도 그대로 로드한다
  (그 열을 쓰는 조회만 구조화된 `lut_column_unavailable`, 1.2·4.3). 용량은 부호 보존 값 그대로(1.4·4.1 caps). (2) 열 출처 규칙 -- 열은
  저장한 표에서만, 폭을 건너 옮기지 않는다(4.3). (3) `vdsat` 접근자(모든 축 선형, 4.3)와 `tol_vdsat_table`(VDSAT 열 선형 LOO +
  Richardson 2^2, 5.2). (4) `gmb` 정본 = GMBS 열(있을 때), 없으면 r5 VS 할선(4.4). (5) 검증 중점 파일(`verify_midpoints`, 1.7)과
  `midpoint_l_bin_checks`(5.1) -- `tol_v_table`·`tol_vdsat_table` 의 `l_bin_checks` 기본값이 `()` 에서 **None(= 중점 파일 값)**으로
  바뀌었다(5절). (6) `pdk_root` 덮어쓰기 인자(1.3)와 설정 파일 기반 데이터 위치 `resolve_lut_location`(1.8). (7) 기준 LUT 폭 키
  `CapTable.w_key` -- r5 까지 bin 지도·폭 비교를 float `w_m == w_ref_m` 으로 해서 LUT v2(`w_ref_m` = 5e-06 기록, 슬라이스 W =
  4.9999999999999996e-06)에서 `CapTable.l_bins` 가 빈 지도가 되던 결함(비앵커 L 의 `caps` 가 `lut_l_not_anchor`)을 폭 키 비교로 고쳤다(1.4).
  (8) 0절 파일 표(새 파일 7개, 층 재배치), `DERIVED_TABLES` 4개(2절), 지문에 중점 파일 sha256(1.5).
- 실패 객체는 core 의 `SchemaRejectedError`(로드 거부)·`SealViolationError`(조회 실패)다. `record.detail` 은
  `{"reason": <사유 키>, ...}` 의 키 정렬 쌍 tuple 이고 `record.devices == ()`, `record.margin is None`
  (LUT 는 소자 이름을 모른다 -- 소자를 아는 호출부가 덧붙인다, P-28·P-34).

---

## 0. 파일과 진입점 (구조 규칙 A~G, `_module_map.LAYERS["lut"]`)

| 층 | 파일 | 진입점 / 종류 |
|---|---|---|
| 0 | `_helpers_bins.py` [r4] | helper: `bin_index`(bin 소속 규칙, 4.0.1) |
| 0 | `_helpers_fail.py` | helper: `schema_rejected`, `seal_violation` |
| 0 | `_helpers_interp.py` [r5] | helper: `cell`, `hermite`, `hermite_root`, `linear_point`, `node_values`(축별 보간, 4.2), 상수 `LINEAR_CONDITIONS`·`HERMITE_CONDITIONS`·`HERMITE_DEGREE` |
| 0 | `_helpers_width.py` [r6] | helper: `width_key(w_m, grid_m) -> (키, 격자 위 여부)`(1.3 규칙, provenance·lut_set 공용) |
| 1 | `_helpers_root.py` [r5] | helper: `peak_index`, `strong_inversion_root`(곡선 묶음, 칸 안 Hermite 근 -- `hermite_root` 를 쓴다) |
| 1 | `_helpers_columns.py` [r6] | helper: `column_source(lut, kind, w_key, column, required=True)`(열 출처, 4.3) |
| 0 | `lut_types.py` | 데이터 선언 모듈(`LutSpec`·`SliceSource`·[r4] `LBin`·`LBinMap`·`LutProvenance`·`DcSlice`·`CapTable`·`LutSet`·`OpPoint`·`Curve`·`TargetSolution`·`Caps`·`TolVCell`·`CurveRow`·`CurveReport`, [r6] `MidpointTable`·`ColumnSource`·`TolVdsatCell`·`MidpointRow`·`MidpointChecks`·`LutLocation`, 상수 `AXES`·`TOL_V_METRICS`·[r6] `TOL_VDSAT_METRICS`·`CAP_TABLE_COLUMNS`·`SLICE_OPTIONAL_COLUMNS`·`DERIVED_COLUMNS`·`COLUMN_ORIGINS`) |
| 0 | `fingerprint.py` | `lut_fingerprint` |
| 0 | `lut_memo.py` | `LutMemo` (+ 상수 `REGIONS`·`DERIVED_TABLES`) |
| 0 | `widths.py` | `widths` |
| 1 | `axis_guard.py` | `check_axes` |
| 1 | `curve_check.py` | `curve_report` |
| 1 | `provenance.py` | `lut_provenance` |
| 1 | `data_location.py` [r6] | `resolve_lut_location`(1.8) |
| 2 | `_helpers_anchor.py` [r4] | helper: `l_position`(옛 `l_anchor_index` 대체 -- 앵커 또는 같은 bin 보간 위치) |
| 2 | `lut_set.py` | `load_lut_set` |
| 3 | `_helpers_loo.py` [r6] | helper: `l_interior`·`external_by_model`·`l_loo_report`·`loo_estimate`·`cell_max`·`branch_targets`·`with_external`·`opt`·`table_at`, 상수 `LINEAR_ORDER`·`HERMITE_ORDER`·`HERMITE_SLOPE_ORDER`(r5 `tolerance.py` 안 함수를 옮김 -- 동작 같음) |
| 3 | `point_query.py` | `op_point` |
| 3 | `gm_id_curve.py` | `gm_id_curve` |
| 3 | `cap_query.py` | `caps` |
| 3 | `vdsat_query.py` [r6] | `vdsat`(4.3) |
| 4 | `gmb.py` [r5, r6] | `gmb`(`op_point` 를 부른다, 4.4) |
| 4 | `vgs_root.py` | `vgs_for_gm_id` |
| 4 | `id_inverse.py` | `gm_id_for_target` |
| 4 | `midpoint_checks.py` [r6] | `midpoint_l_bin_checks`(5.1) |
| 5 | `tolerance.py` [r6 층 3 → 5] | `tol_v_table` (`TolVTable` 은 비진입 공개 이름, 상수 `LOO_ORDERS`) |
| 5 | `vdsat_tolerance.py` [r6] | `tol_vdsat_table` (`TolVdsatTable` 비진입 공개 이름, 상수 `LOO_ORDERS`, 5.2) |

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
  `[len(L), len(VGS), len(VDS), len(VS)]`(그 폭의 절댓값), `meta_json`(JSON 문자열, `model_files_sha256` 객체 선택 --
  {PDK 루트 기준 상대 경로: sha256}; [r4] 비어 있지 않으면 `pdk_root`(문자열, 그 루트 폴더) 필수),
  측정 조건 `corner`·`temp_c`(선택 -- 없으면 recorded=False).
- 기준 LUT(용량) npz 키: `L`·`VGS`·`VDS`·`VS`, kind 마다 `CGG<접미사>`·`CGD<접미사>`(필수), `CGS<접미사>`·`CGB<접미사>`(선택),
  `ID<접미사>`(폭 판정용, 선택), `w_ref_m`(선택), `corner`·`temp_c`(선택).
- [r6] 기준 LUT 선택 열: kind 마다 `CAP_TABLE_COLUMNS` = (`CDD`, `CSS`, `GDS`, `GM`, `GMBS`, `ID`, `SVG2_1HZ`, `SVG2_HF`, `VDSAT`,
  `VTH`) 각 `<이름><접미사>` 가 있으면 읽는다(모양 = 기준 LUT 축 모양, 다르면 `lut_cap_shape_mismatch`, detail `path, column`).
  없는 열은 그냥 없다(로드 거부 아님 -- 옛 `assets/sky130_nfet_pfet_lut_sample.npz` 는 ID·GM·GDS 만 있다). `meta_json`(선택)의
  `sign_convention`(문자열)·`L_source`(객체) 를 표에 싣는다. LUT v2 생성기 규약: ID·GM·GDS·GMBS·VTH·VDSAT 은 BSIM op 값의 크기,
  **용량은 부호 보존**(CGG = −Im(i(vgs))/ω 게이트 여기, C_gx = +Im(i(vgs))/ω x 여기, CDD = −Im(i(vds))/ω, CSS = −Im(i(vsrc))/ω --
  CGB·CGS·CSS·CGD(pfet) 에 음수 점이 있다), SVG2_* 는 게이트 환산 잡음 V²/Hz. 엔진은 용량에 로그·절댓값을 쓰지 않는다(4.1 caps).
- [r6] 슬라이스 선택 열: `SLICE_OPTIONAL_COLUMNS` = (`GMBS`, `VDSAT`)(접미사 없음, 모양 = 슬라이스 모양, 다르면
  `lut_slice_shape_mismatch` detail `array` = 그 이름). 지금 슬라이스 생성기는 쓰지 않는다.
- [r6] 파생 열(로드 1회): 표에 GMBS·ID 가 다 있으면 `GMBS_PER_ID` = GMBS/ID(ID > 0 인 점, 아니면 NaN)를 그 표의 `columns` 에 더한다
  (`DERIVED_COLUMNS`). 기준 LUT 표는 ID·GM 이 다 있으면 `CapTable.on_mask` = (ID > 0) & (GM > 0).

### 1.3 `lut_provenance(manifest_path, cap_npz_path, spec, *, pdk_root=None, verify_midpoints=None) -> LutProvenance`
- [r6] `pdk_root`: None 이 아니면 모델 파일 경로 = `os.path.join(pdk_root, 상대 경로)`(meta `pdk_root` 대신, `lut_model_root_missing`
  판정도 이 값으로). sha256 대조는 그대로라 같은 모델 파일이면 어느 폴더든 같은 결과·같은 지문.
- [r6] `verify_midpoints`: None 이 아니면 그 파일 `(절대 경로, sha256, meta L_source 키 정렬 쌍, 측정 조건)` 을
  `LutProvenance.midpoints_path·midpoints_sha256·midpoints_l_source·midpoints_conditions` 에 싣는다(파일 없음 → `lut_midpoints_missing`
  detail `path`). 주지 않으면 None·None·()·().
- [r6] 폭 키 규칙은 `_helpers_width.width_key` 한 곳(아래 문장과 같은 규칙).
- 슬라이스마다 파일 sha256 을 다시 재서 manifest 값과 대조. 폭 키 `w_key = round(W / grid)`(int).
  [r3] 폭 키 허용도 대칭이다: |W/grid − w_key| ≤ `2·ulp(W/grid)` 이면 위·아래 어느 쪽으로 벗어나도 그 키(`abs` 판정). W 에는 격자 범위
  검사가 없으므로(폭 집합 = 슬라이스 집합) 경계 순서 문제가 없다. `widths()` 의 최소 finger 폭 필터는 정수 키 × grid 와 선언값의 비교라
  ulp 허용 대상이 아니다.
- `slices` 는 (kind, w_key) 정렬 `SliceSource` tuple. `conditions`·`cap_conditions` 는 옛 `lut_conditions_from_npz` 결과의
  키 정렬 쌍 tuple: 기록 있음 → `(("corner", str), ("recorded", True), ("temp_c", float))`, 없음 → `(("note", str), ("recorded", False))`.
- [r4] **모델 파일**: 슬라이스 meta `model_files_sha256` 의 파일마다 경로 = `os.path.join(meta["pdk_root"], 상대 경로)`, 파일 sha256 을
  다시 재서 기록값과 대조(같은 경로는 한 호출에서 1회). `SliceSource.model_paths` = ((상대 경로, 그 경로), ...) 상대 경로 정렬,
  기록이 없으면 `()`. 경로는 지문에 들어가지 않는다(모델 sha256 은 이미 `model_files_sha256` 로 지문에 있다).
- 실패(`SchemaRejectedError`, reason): `lut_manifest_missing`, `lut_device_undeclared`(device_kinds 밖), `lut_slice_missing`,
  `lut_slice_sha256_mismatch`, `lut_width_off_grid`(|W/grid − w_key| > `2·ulp(W/grid)`), `lut_slice_duplicate`(같은 (kind, w_key)),
  `lut_manifest_empty`, `lut_cap_missing`, [r4] `lut_model_root_missing`(모델 파일 기록이 있는데 `pdk_root` 없음, detail `path` = 슬라이스),
  `lut_model_file_missing`(detail `path, slice`), `lut_model_file_sha256_mismatch`(detail `path, recorded, actual, slice`).

### 1.4 `load_lut_set(manifest_path, cap_npz_path, spec, *, pdk_root=None, verify_midpoints=None) -> LutSet`
- `LutSet(spec, provenance, slice_map, cap_map, fp, midpoints)`: `slice_map` = 읽기 전용 매핑 {(kind, w_key): DcSlice}, `cap_map` = {kind: CapTable},
  [r6] `midpoints` = {kind: MidpointTable}(1.7, 중점 파일을 주지 않으면 빈 매핑). `pdk_root`·`verify_midpoints` 는 1.3 으로 넘긴다.
- [r6] `CapTable` 추가 필드: `w_key`(= `width_key(w_ref_m, grid)` 의 키, 격자 밖이면 None), `columns`(1.2 선택 열 + 파생 열, 읽기 전용
  매핑), `on_mask`, `sign_convention`(meta 문자열 또는 None), `l_source`(meta `L_source` 키 정렬 쌍 또는 ()). `DcSlice.columns` 도 같은 뜻.
- [r6 결함 수정] **`CapTable.l_bins` = 그 kind 슬라이스 중 `w_key == CapTable.w_key` 인 것의 지도**(r4·r5 는 `w_m == w_ref_m` float 비교 --
  LUT v2 는 `w_ref_m` = 5e-06 이고 슬라이스 W = 4.9999999999999996e-06 이라 빈 지도가 되어 비앵커 L 의 `caps` 가 `lut_l_not_anchor` 로
  실패했다. 옛 세트는 w_ref 를 슬라이스 ID 대조로 고르므로 float 가 같아 영향 없었다).
- `DcSlice`: `grids` = 축별 float tuple 4개, 배열은 읽기 전용 numpy. 로그 배열 `log_ID·log_GM·log_GDS` = `ln(clip(배열, 그 배열의 최소 양수값))`
  (상수 바닥 없음), `floors`·`nonpositive` 에 바닥값·0 이하 원소 수 기록, `on_mask = (ID > 0) & (GM > 0)`.
- 불변식: 모든 슬라이스의 L·VGS·VDS·VS 가 float 단위로 같다. 측정 조건(`conditions`)이 모두 같다. 기준 LUT 조건이 기록돼
  있으면 corner·temp_c 가 슬라이스와 같다. 기준 LUT L·VGS·VDS 가 슬라이스와 같다(VS 는 달라도 됨).
- **용량 기준 폭 `CapTable.w_ref_m`**: (1) 기준 npz 에 `w_ref_m` 이 있으면 그 값, `basis == (("method", "recorded_w_ref_m"),)`
  (2) 없으면 `ID<접미사>` 와 같은 kind 슬라이스 `ID` 를 기준 VS 값이 슬라이스 VS 축에 정확히 있는 열·기준 ID > 0 인 점에서 비교한다.
  d_s = max |ID_s − ID_ref| / |ID_ref|. 최소 d 인 슬라이스 w 를 고르되 **d_w < sep / 2** 일 때만 채택.
  [r2] sep = min over 다른 슬라이스 s ≠ w of max |ID_s − ID_w| / |ID_w| -- **분모는 고른 슬라이스 ID_w**, 비교 점 = 기준 ID > 0 이고
  ID_w > 0 인 같은 열의 점. `nearest_other_rel_diff` = sep. `basis` = `(("max_rel_diff", d_w), ("method", "slice_id_match"), ("nearest_other_rel_diff", 그 차), ("w_key", w))`.
- [r2] **용량 kind 집합(fail-closed)** = 슬라이스 kind ∪ `spec.cap_column_suffix` 선언 kind. 그 집합의 kind 마다 이 순서로 검사:
  접미사 선언 없음 → `lut_cap_kind_undeclared`, 슬라이스 없음 → `lut_cap_kind_without_slices`, `CGG<접미사>`·`CGD<접미사>` 열 없음 →
  `lut_cap_column_missing`. `cap_map` 의 키 = 이 집합.
- [r4] **L bin 지도 `DcSlice.l_bins` = `LBinMap(model_files, w_bin, bins, anchor_bin)`** -- 로드 때 슬라이스마다 1회 계산해 보관
  (조회마다 다시 만들지 않는다. 같은 모델 파일은 한 로드에서 한 번만 읽는다):
  1. bin 블록 = 슬라이스 `model_paths` 파일들의 `.model <이름> ...` 블록 중 `lmin`·`lmax`·`wmin`·`wmax`(대소문자 무시, `키 = 숫자`)를
     가진 것(값 m). 블록은 다음 `.model` 줄 또는 파일 끝까지. 넷 중 일부만 있는 블록 → `lut_model_bin_incomplete`(detail `path, model, keys`).
     넷 다 없는 블록(bin 아닌 모델)은 무시.
  2. bin 블록이 하나도 없으면(모델 파일 기록 없음 포함) **빈 지도** `LBinMap((), None, (), ())` -- 거부가 아니다. 빈 지도에서는 L 보간이 없다(4.0).
  3. W bin: 블록들의 서로 다른 `(wmin, wmax)` 쌍을 오름차순으로 놓고 4.0.1 규칙(`bin_index`)으로 슬라이스 W(`w_m`)의 쌍을 고른다
     → `w_bin`. 없으면 `lut_model_bins_no_width`(detail `path, w_m`).
  4. `bins` = 그 `w_bin` 과 같은 `(wmin, wmax)` 블록의 `LBin(model, lmin, lmax)`, (lmin, lmax, model) 오름차순. 이웃 두 bin 이
     `lo_b < hi_a` 이고 `|hi_a − lo_b| > ulp(lo_b)` 이면(겹침) `lut_model_bins_overlap`(detail `path, w_m, models`).
  5. `anchor_bin[i]` = L 축 앵커 i 의 `bins` index(4.0.1 규칙). 어느 앵커라도 bin 이 없으면 `lut_l_anchor_outside_model_bins`(detail `path, w_m, L`).
  `model_files` = 읽은 상대 경로 tuple. **`CapTable.l_bins`** = 그 kind 슬라이스 중 `w_m == w_ref_m` 인 것의 지도(없으면 빈 지도 --
  기준 LUT 는 모델 파일 기록이 없으므로 채택 폭 슬라이스의 지도를 빌린다).
- [r4 실측 2026-10-07, 생성 슬라이스 32개] 로드 1.75 s(r2 1.5 s). 모든 슬라이스의 `anchor_bin` = (0, 1, 1, 2, 2, 2, 2, 3, 3, 4, 5, 5)
  (L 앵커 0.15·0.2·0.25·0.3·0.35·0.425·0.5·0.7·1·1.5·2.5·4 µm, bin = [0.15,0.18]·(0.18,0.25]·(0.25,0.5]·(0.5,1]·(1,2]·(2,4]). w_key 1000
  (W = 4.9999999999999996e-06) 은 nmos·pmos 모두 `w_bin` (3e-6, 5e-6). pmos w_key 84·110 은 같은 `w_bin` (4.2e-7, 5.5e-7).
- [r5] **Hermite 보조 필드(슬라이스마다 로드 1회, DEC-87·N3.7)**:
  - `DcSlice.vds_slope_ok` = `(ID > 0) & (GDS > 0)`(원시 배열, VDS 기울기 GDS/ID 가 정의되는 격자점). VGS 기울기 GM/ID 의
    정의 격자점은 `on_mask` 다. 기울기 값 = `exp(log_GM − log_ID)`(VGS)·`exp(log_GDS − log_ID)`(VDS).
  - `DcSlice.fc_ok_vgs` 모양 `[nL, nVGS − 1, nVDS, nVS]`·`fc_ok_vds` 모양 `[nL, nVGS, nVDS − 1, nVS]`(읽기 전용 bool): 그 축 칸
    (두 이웃 격자점, 값 y = ln ID, 기울기 m)이 **Hermite 칸**(두 끝 기울기 정의)이면 Fritsch–Carlson 단조 조건의 참·거짓,
    Hermite 칸이 아니면 참. 단조 조건(필요충분, 원소마다, h = 칸 폭, n = Hermite 차수 = 3): `b0 = m0·h`, `b2 = m1·h`,
    `b1 = n·(y1 − y0) − b0 − b2`, `q = (b1² ≤ b0·b2)`; 비감소 = `b0 ≥ 0 ∧ b2 ≥ 0 ∧ (b1 ≥ 0 ∨ q)`, 비증가 = `b0 ≤ 0 ∧ b2 ≤ 0 ∧
    (b1 ≤ 0 ∨ q)`, 단조 = 둘 중 하나(p'(x)·h 의 Bernstein 계수가 [0, 1] 에서 한 부호 -- Fritsch–Carlson(1980) α = m0/δ,
    β = m1/δ 영역과 같은 식. 예: δ = 0 이고 기울기 ≠ 0 이면 위반).
  - `DcSlice.hermite_fc = (("VDS", Hermite 칸 수, 위반 칸 수), ("VGS", Hermite 칸 수, 위반 칸 수))`. 위반이 있어도 **로드는
    거부하지 않는다**(위반 칸의 조회 규칙은 4.2, 보고는 `curve_report` 의 `n_hermite_nonmonotone`).
  - [r5 실측 2026-10-07, 생성 슬라이스 32개] 모든 슬라이스 `hermite_fc = (("VDS", 276360, 0), ("VGS", 276480, 0))`(위반 0 --
    off 격자점은 VDS = 0 열 5880개뿐). 로드 3.0 s → 5.1 s(같은 기계·같은 시각 측정, FC 검사 ≈ 1.1 s 포함).
- `fp == lut_fingerprint(provenance, ((kind, w_ref_m, basis), ...))`.
- 실패(`SchemaRejectedError`, reason): 1.3 전부 + `lut_conditions_mismatch`, `lut_slice_axes_mismatch`, `lut_slice_shape_mismatch`,
  `lut_array_no_positive`, `lut_cap_axes_mismatch`, `lut_cap_kind_undeclared`, `lut_cap_kind_without_slices`, `lut_cap_column_missing`,
  `lut_cap_width_unresolved`
  (슬라이스 1개뿐·동률·분리 조건 불충족·VS 값이 슬라이스 축에 없음·`w_ref_m`·`ID` 열 둘 다 없음),
  [r4] `lut_model_bin_incomplete`, `lut_model_bins_no_width`, `lut_model_bins_overlap`, `lut_l_anchor_outside_model_bins`.
- [실측 2026-10-07, 생성 완료 슬라이스 32개 + `assets/sky130_nfet_pfet_lut_sample.npz`] 로드 1.5 s, nmos·pmos 모두 w_key 1000
  (5 µm) 채택, d_w ≈ 5.0e-7, 이웃 차 0.88(nmos)·1.25(pmos).

### 1.5 `lut_fingerprint(provenance, cap_basis) -> str`
- 64자 hex = `core.fp_of` of (manifest sha256, 생성기 sha256, 슬라이스별 (kind, w_key, 파일 sha256, 조건, 모델 파일 sha256),
  기준 LUT sha256·조건, cap_basis). 파일 경로는 들어가지 않는다(같은 파일을 다른 폴더로 옮겨도 같은 지문), 어느 sha256 이든
  바뀌면 다른 지문.
- [r6] `provenance.midpoints_sha256` 이 None 이 아니면 7번째 항목 `("midpoints_sha256", 값)` 을 더한다(중점 값이 tol 표 외부 값으로
  들어가므로). None 이면 r5 와 **같은 지문**(항목 6개 그대로).

### 1.6 `widths(lut, kind) -> tuple[int]`
- `kind` 슬라이스 폭 키 중 `w_key · grid ≥ min_finger_w_m[kind]` 인 것의 오름차순. 근접 폭 대체·보간 없음.
- 실패: `min_finger_w_m` 에 kind 없음 → `KeyError`. 그 kind 슬라이스가 없으면 `()`.

### 1.7 [r6] 검증 중점 파일 (`load_lut_set(..., verify_midpoints=경로)`)
- 형식 = 기준 LUT 생성기 산출 npz(`sky130_lut_sweep.py sweep --l-json <승인 L 파일> --l-json-key verification_midpoints_um`): `L`(LUT 축이
  아닌 중점, m)·`VGS`·`VDS`·`VS`, kind 마다 `ID<접미사>`·`GM<접미사>`(필수)·`VDSAT<접미사>`(선택), `w_ref_m`(필수), `corner`·`temp_c`,
  `meta_json` 의 `L_source`.
- 검사 순서와 거부(`SchemaRejectedError` reason): (1) meta `L_source` 에 `sha256` 없음 → `lut_midpoints_l_source_unrecorded`(detail `path,
  l_source`) -- `--l-um` 으로 만든 파일(`{"kind": "cli"}`)은 거부 (2) 어느 kind 의 `CapTable.l_source` 에 sha256 이 있고 중점 sha256 과
  다름 → `lut_midpoints_l_source_mismatch`(detail `path, kind, cap, midpoints`) (3) 중점 조건이 기록돼 있고 corner·temp_c 가 슬라이스와 다름 →
  `lut_conditions_mismatch`(detail `key, midpoints, slices`) (4) `VGS`·`VDS`·`VS` 가 슬라이스 축과 float 단위로 다름 → `lut_midpoints_axes_mismatch`
  (5) `w_ref_m` 없음 → `lut_midpoints_width_missing` (6) `w_ref_m` 이 제조 격자 밖 → `lut_width_off_grid` (7) kind(= `cap_map` 키) 마다 ID·GM
  열 없음 → `lut_midpoints_column_missing`(detail `path, kind, column`), 열 모양 ≠ 파일 축 모양 → `lut_midpoints_shape_mismatch`.
- `MidpointTable(kind, sha256, w_m, w_key, L_points, grids, log_ID, gm_id, on_mask, VDSAT)`: `L_points` = 파일 L 축, `grids` = (VGS, VDS, VS),
  `log_ID` = ln ID(ID > 0, 아니면 NaN), `gm_id` = GM/ID(같은 점, 아니면 NaN), `on_mask` = (ID > 0) & (GM > 0), `VDSAT` = 열 또는 None.
- [실측 2026-10-08] `lut_v2/sky130_nfet_pfet_lut_v2_verify_midpoints.npz` sha256 `d243f380…990f`(재생성 -- 배열은 옛 `--l-um` 파일과
  비트 동일, meta 만 `L_source = {kind json, sha256 0147c262…, key verification_midpoints_um}`·생성기 sha 바뀜), L = 0.165·6.0·14.0 µm,
  `w_ref_m` 5e-06 → 폭 키 1000.

### 1.8 [r6] 데이터 위치 `resolve_lut_location(config_path, env) -> LutLocation`
- 설정 JSON: `{"root": {"env": 이름, "default": 폴더}, "pdk_root": {"env", "default"}(선택), "files": {"manifest": {"path", "sha256"},
  "cap_npz": {...}, "verify_midpoints": {...}(선택)}}`. 다른 키는 무시. `env` = 매핑(부르는 쪽이 `os.environ` 를 넘긴다 -- 모듈은 환경을
  직접 읽지 않는다).
- root·pdk_root = `env[이름]` 이 비어 있지 않으면 그 값(`sources` 에 `"env:<이름>"`), 아니면 `default`(`"config_default"`), 둘 다 없으면
  `lut_location_config_invalid`. 경로는 `os.path.abspath`.
- 파일: `path` 는 root 기준 상대(절대 경로·`..` 조각·빈 값·sha256 없음 → `lut_location_config_invalid` detail `item, why`), 파일 없음 →
  `lut_location_file_missing`(detail `item, path`), sha256 다름 → `lut_location_sha256_mismatch`(detail `item, path, recorded, actual`).
  manifest·cap_npz 항목이 없으면 `lut_location_config_invalid`. 설정 파일 없음 → `lut_location_config_missing`, root 폴더 없음 →
  `lut_location_root_missing`, `root`·`files` 가 객체가 아님 → `lut_location_config_invalid`. 슬라이스는 여기서 재지 않는다(manifest 가
  고정하고 `load_lut_set` 이 대조).
- `LutLocation(config_path, root, manifest_path, cap_npz_path, midpoints_path, pdk_root, sources)`, `sources` = ((항목, 출처), ...) 항목 정렬.
- 저장소 설정: `skills/analog-gmid-design/assets/lut_v2_location.json` -- root 기본 `C:/Users/HSLEE/Documents/Todoc/fpga/lut_data/sky130_lut_v2`
  (git 밖, `GMID_LUT_V2_ROOT` 로 덮어씀), pdk_root 기본 `C:/pdk/sky130_fd_pr`(`GMID_PDK_ROOT`), 세 파일 sha256 고정. 쓰는 법:
  `loc = resolve_lut_location(<설정>, os.environ)` → `load_lut_set(loc.manifest_path, loc.cap_npz_path, spec, pdk_root=loc.pdk_root,
  verify_midpoints=loc.midpoints_path)`.
- **test 기본 경로 전환(아직 안 함 -- `tests/lut/conftest.py` 는 test 작성자 몫)**: conftest 의 `_DEFAULT_MANIFEST`·`_DEFAULT_CAP`(옛 12-L
  세트)를 위 설정의 `resolve_lut_location` 결과로 바꾸고 `load_lut_set` 에 `pdk_root`·`verify_midpoints` 를 넘긴다(`GMID_LUT_MANIFEST`·
  `GMID_LUT_CAP_NPZ` 환경 덮어쓰기는 유지 가능). 옛 세트 기대값(12 앵커 bin 상태, VS 상한 0.8 V, `cgg_minus_cgd_at_gs` 모델 등)을
  쓰는 test 는 v2 값(18 앵커, VS 0~1.8, `lut_cgs_cgb`)으로 다시 써야 한다.

---

## 2. memo `LutMemo(lut, *, point, curve, root)`

- 상한 인자: 1 이상 int(아니면 core `BoundedLRU` 의 `ValueError`). `derived` 영역 상한 = `len(lut.slice_map) * len(DERIVED_TABLES)`.
- `LutMemo.from_sweep(lut, n_theta, unique_keys_per_eval)`: 영역 r ∈ {point, curve, root} 상한 = `(n_theta + 1) * unique_keys_per_eval[r]`
  (`unique_keys_per_eval` 은 Mapping 또는 (영역, int) 쌍).
- `lookup(region, fn_name, key, compute)`: 키 = `(lut.fp, fn_name) + tuple(key)`. 적중이면 저장 값 그대로(`is`), 아니면 compute 1회.
  가변 원소가 든 키 → `TypeError`. 알 수 없는 region → `KeyError`.
- `stats()` → `(("curve", LruStats), ("derived", ...), ("point", ...), ("root", ...))`.
- 조회 함수별 영역: `op_point`·`gmb`·`caps`·[r6] `vdsat` = point, `gm_id_curve` = curve, `vgs_for_gm_id`·`gm_id_for_target` = root,
  `tol_v_table`·`curve_report`·[r6] `tol_vdsat_table`·`midpoint_l_bin_checks` = derived. [r6] `DERIVED_TABLES` =
  ("curve_report", "midpoint_l_bin_checks", "tol_v_table", "tol_vdsat_table") -- derived 상한 = 슬라이스 수 × 4(r5 는 × 2).
  `tol_v_table`·`tol_vdsat_table` 을 `l_bin_checks=None` 으로 부르면 LutSet 에 중점 표가 있을 때만 `midpoint_l_bin_checks` 를 먼저
  부른다(derived misses +1, 두 번째부터 hits) -- 중점 표가 없으면 그 조회를 하지 않는다(r5 와 같은 misses 수).
  [r6] `gmb` 의 compute 는 GMBS 열이 있으면 `op_point` 1회(조회점), 없으면 3회(r5). 같은 인자 두 번 → 두 번째는 compute 0(그 영역 hits +1). 실패한 조회는 저장되지 않는다.
  [r5] `gmb` 의 compute 는 같은 (L, vgs, vds) 의 `op_point` 3회(VS 칸 양끝·조회점, point 영역)를 부른다 -- 첫 `gmb` 호출은 point
  영역 misses 가 gmb 1 + op_point ≤ 3 늘어난다(이미 있던 op_point 키는 hits).
- 같은 내용의 LutSet 두 개(같은 파일, 다른 폴더)는 같은 `fp` 라 같은 키가 된다.

---

## 3. 분지 규칙(정본) -- `vgs_for_gm_id`·`gm_id_for_target`·`tol_v_table`·`curve_report` 공통

- 곡선 = 고정 (L, VDS, VS) 의 VGS 격자 **마디** gm/ID(`Curve.gm_id_vals`). **정점 index p** = 마디 gm/ID 최댓값의 첫 index(`argmax`).
- **강반전 분지 = index p 이상(VGS ≥ VGS[p])**. 목표를 품는 칸(두 끝 마디 편차 곱 ≤ 0)은 분지 안의 칸 [i, i+1] (i ≥ p) 만 보고,
  그중 가장 오른쪽을 고른다. 분지 안에 그런 칸이 없으면 **해 없음 = 실패**(정점 왼쪽 해로 내려가지 않는다).
- [r5] **칸 안의 근 = 그 칸 VGS Hermite 의 미분이 목표인 VGS**(값 = 마디 ln ID, 기울기 = 마디 gm/ID, 4.2 와 같은 다항식).
  두 끝 미분 = 두 끝 마디 gm/ID 라 고른 칸에는 근이 있다. 계산 = `hermite_root` bisection: 위 끝 residual 이 정확히 0 이면 위 끝
  VGS, 반올림으로 두 끝 residual 이 같은 부호면 |residual| 이 작은 끝, 그 밖은 불변식 'residual(lo) 가 위 끝 residual 과 같은
  부호 아님' 을 지키며 반복 K_max = ceil(log2(칸 폭 / ulp(max(|v0|, |v1|)))) 번(N3.6 K_max 규칙의 tol 자리에 부동소수 분해능 --
  tol_V 는 이 역산으로 재므로 쓸 수 없다), 결과 = 마지막 lo. 그래서 결과 VGS 의 `op_point(...).gm_over_id` 는 목표와 부동소수
  분해능 안에서 같다(r4 까지는 칸 안에서 다를 수 있었다). 칸이 단조 위반(`Curve.cell_ok` 거짓)이면 실패
  `lut_hermite_nonmonotone_cell`, 곡선에 gm/ID 가 정의 안 된 마디(NaN)가 있으면 실패 `lut_curve_undefined`(4.1 표).
- 왜 새로 썼나: 옛 `_solve_vgs` 는 전 구간에서 가장 오른쪽 구간을 골라, 분지 안에 해가 없으면 정점 왼쪽 누설 분지(VGS≈0)의 교차를
  ValueError 없이 돌려줬다(tol_V 실측: 유효 목표 184,027 중 3,918(2.13%), 오차 최대 1.78 V). r4 까지는 칸 선택만 새로 쓰고 칸 안
  2점 선형 역보간 문장을 복사했으나 [r5] 칸 안 근이 Hermite 로 바뀌어 복사 구간은 남지 않는다(6절). 칸 선택 규칙(분지 거르기·
  가장 오른쪽·해 없음)은 r4 와 같다.

---

## 4. 조회 API

공통: 축 이름 `AXES = ("L", "VGS", "VDS", "VS")`, L 은 m, 전압은 V(VS = vsb 크기). 입력 숫자는 `float()` 로 바꿔 쓴다.

### 4.0 [r4 전면 교체] L = 앵커 또는 같은 모델 bin 안 보간 (사용자 결정 2026-10-07)
적용 경로: op_point·gm_id_curve·vgs_for_gm_id·gm_id_for_target·gmb·caps·TolVTable.at(모두 같은 판정 `l_position`). 판정 순서:
1. **앵커**(r2/r3 그대로): 조회 L 이 L 축 앵커 a 와 `|L − a| ≤ math.ulp(a)` 이면 그 앵커. 이 검사가 범위 검사보다 **먼저**다(대칭 --
   격자 양끝 앵커도 바깥쪽 1 ulp 까지 받는다. 예 `L_max + ulp(L_max)` → 마지막 앵커). L 값으로 앵커 값 a 를 쓰고(`IDu = ID·a/w_m`,
   `id_a = IDu·W/a`), 결과는 r2 앵커 조회와 **비트 단위로 같다**(L 격자 = (a,) 한 장, L 가중치 (1, 0)).
2. 범위: 1 ulp 를 넘어 L 격자 밖(NaN 포함) → `lut_axis_out_of_range`(axis "L", 4.1).
3. 양옆 앵커 below = L[k−1] < L < above = L[k] (k = `bisect_right(L 격자, L)`). 표의 bin 지도(`DcSlice.l_bins`, 용량은 `CapTable.l_bins`,
   tol_V 는 `TolVTable.l_bins`)가
   - **빈 지도** → `lut_l_not_anchor`(r2 사유 키 유지, detail 에 `bins: "unavailable"` 추가).
   - `anchor_bin[k−1] == anchor_bin[k]`(같은 bin -- bin 은 구간이라 사이의 L 도 그 bin) → **보간**: L 격자 = (below, above) 두 장으로
     보간한다. L 축은 선형(L 가중치 `t = (L − below)/(above − below)`), [r5] 다른 축은 4.2 의 축별 방법(r4 의 '4축 다중선형' 대체).
     L 값은 조회 L 그대로(`IDu = ID·L/w_m`, `id_a = IDu·W/L`). bin 밖 장은 읽지 않는다.
   - 다르면 거부(bin 경계를 건너는 보간 금지). 조회 L 의 bin b = `bin_index(((lmin, lmax) of bins), L)`(4.0.1):
     - b 없음(모델 bin 사이 빈틈) → **`lut_l_outside_model_bins`**
     - b 의 LUT 앵커가 1개 이하 → **`lut_l_bin_unbracketed`**(그 bin 안에 감싸는 두 점이 없다)
     - b 의 앵커가 2개 이상(L 이 그 앵커들 바깥, 감싸는 쌍이 경계를 건넘) → **`lut_l_cross_bin`**
   - 세 거부의 detail: `value, below, above, below_bin, above_bin`(양옆 앵커의 bin `.model` 이름) + context; `lut_l_bin_unbracketed`·
     `lut_l_cross_bin` 은 `bin, bin_lmin, bin_lmax, bin_anchors`(b 의 이름·경계·그 bin 앵커 L tuple) 추가. context = kind·w_key / 용량 kind·table "cap" /
     tol_V kind·table "tol_v"·w_key.
- memo 키: op_point·gmb·gm_id_curve = `(kind, w_key, lo, hi, L 값) + 나머지`, caps = `(kind, lo, hi, L 값, ...)`(lo, hi = 쓴 L 장 index,
  앵커면 lo == hi 이고 L 값 = 앵커 값 → 1 ulp 이내 두 입력은 같은 키). vgs_for_gm_id·gm_id_for_target 은 입력 float 를 키로 쓴다.
- [r4 실측, 생성 슬라이스 nmos w_key 1000, VGS = VDS = 0.9, VS = 0] L 0.3·0.3125·0.4·0.45 µm 보간 성공(bin (0.25, 0.5]),
  0.6 µm → `lut_l_cross_bin`(bin (0.5, 1], 앵커 0.7·1.0), 0.17 µm → `lut_l_bin_unbracketed`(bin [0.15, 0.18], 앵커 0.15),
  1.2 µm → `lut_l_bin_unbracketed`(bin (1, 2], 앵커 1.5), 0.22 µm·0.85 µm·3 µm 보간 성공. 0.3875 µm 의 gm/ID 6.6575 는 0.35·0.425 µm 값
  6.7234·6.5923 사이.

#### 4.0.1 [r4] bin 소속 규칙 (`_helpers_bins.bin_index`, 로드 배정과 조회가 같은 함수)
- 값 x 는 `lo ≤ x ≤ hi` 인 구간에 든다(**양끝 닫힘**). 경계를 공유한 두 구간이 다 품으면 **lo 가 작은(아래) 구간**이 이긴다.
  그래서 경계값 L = b 는 `lmax = b` 인 아래 bin 이다 -- 사실상 `lmin < L ≤ lmax`(맨 아래 bin 만 `lmin` 포함). W 도 같다(W = wmax 인 아래 W bin).
  경계 비교는 그 경계값의 1 ulp 이내를 같은 값으로 본다(LUT L 은 `µm × 1e-6` 곱이라 경계와 1 ulp 어긋날 수 있다. 예: 슬라이스 W
  4.9999999999999996e-06 은 경계 5e-06 위로 보아 W bin (3e-6, 5e-6)).
- 근거(ngspice-46 실측, sky130 tt, `showmod` 의 lmin·lmax·wmin·wmax): (1) 생성 슬라이스 32개 × L 앵커 12개 = 384점 전부를 이 규칙의 예측과
  대조해 **384/384 일치**(code author 실측 2026-10-07, 스크립트 `scratchpad/bin_verify.py`·결과 `bin_verify.out`) (2) W = 5 µm 에서 L = 0.5 µm →
  bin [0.25, 0.5], 0.501 µm 까지 아래 bin, 0.5011 µm 부터 위 bin; L = 0.15 − 0.001 µm 도 맨 아래 bin, 0.1485 µm 은 "could not find a valid modelname"
  (3) 오케스트레이터 측 별도 실측: 0.1809 µm → 아래, 0.181 µm → 위, W = 5 µm → [3, 5] bin(`lut_regen_plan.md` 1.2a, raw `scratchpad/bincheck/`).
  **`lmin ≤ L < lmax` 가 아니다**(슬라이스 생성기 `bin_for` 와 meta `model_bin_per_L` 은 이 잘못된 규칙으로 적혀 있어 경계 앵커의 bin 이름이
  실제와 다르다 -- 엔진은 그 meta 를 읽지 않는다).
- ngspice 는 경계 바깥 약 1 nm 까지 아래 bin 을 쓰지만(위 (2)) 엔진은 그 허용폭을 쓰지 않는다(시뮬레이터 내부값 -- 박지 않음).
  영향: 조회 L ∈ (b, b + ~1 nm] 은 엔진에선 위 bin 이다. 위 bin 의 앵커는 모두 b 보다 크므로(앵커 b 는 아래 bin) 그 L 을 위 bin 의
  두 앵커가 감싸려면 (b, L) 안에 앵커가 있어야 하고, 제조 격자(0.005 µm) 위 앵커에서는 그런 점이 없다 -- 그 L 은 거부되며
  ngspice 와 다른 bin 의 값으로 보간되지 않는다(앵커가 제조 격자 위에 있다는 전제).

### 4.1 축 검사
축 밖(격자 최소·최대 밖, NaN 포함) → `SealViolationError` reason `lut_axis_out_of_range`, detail `axis, value, lo, hi, kind, w_key`
(용량은 `w_key` 대신 `table: "cap"`, tol_V 는 `table: "tol_v"` 추가). 클램프·외삽 없음. 격자 끝점 자체는 축 안(정확값).
(kind, w_key) 슬라이스가 없으면 `KeyError`(계약 위반 -- 폭은 `widths()` 에서만 고른다).

| 함수 | 반환 | 정의 |
|---|---|---|
| `check_axes(grids, names, point, context=())` | None | 위 축 검사. `context` 쌍은 detail 에 더해진다 |
| `op_point(memo, kind, w_key, L, vgs, vds, vsb)` | `OpPoint` | [r5] 4.0 의 L 장에서 4.2 의 축별 보간 1회: `IDu = exp(lnID)·L/w_m`, `gm_over_id` = lnID 의 VGS 미분(4.2), `gm_gds = gm_over_id · exp(lnID − lnGDS)`, `gds_per_w = exp(lnGDS)/w_m`(lnGDS 모든 축 선형), `vth`(모든 축 선형). 단조 위반 칸은 그 축 선형으로 보간하고 실패하지 않는다 |
| `gm_id_curve(memo, kind, w_key, L, vds, vsb)` | `Curve` | [r5] 4.0 의 L 장, VGS 격자 **마디마다** 4.2 의 마디 값: `log_id_vals` = V_a, `id_vals = exp(V_a)`(폭 w_m 의 A), `gm_id_vals` = S_a(정의 안 되면 NaN), `cell_ok`(길이 nVGS − 1) = 4.2 의 VGS 칸 단조 조건. `vgs_grid` 는 슬라이스 VGS 축. 배열 읽기 전용. 마디 사이 곡선은 그 칸의 VGS Hermite(op_point 와 같은 곡면). VGS 축 검사는 없다(격자 전체) |
| `vgs_for_gm_id(memo, kind, w_key, gm_id, L, vds, vsb)` | float V | [r5] 3절 규칙(칸 선택 + 칸 안 Hermite 미분 근). 실패(`SealViolationError`): 곡선에 NaN 마디 → `lut_curve_undefined`(detail `gm_id, L, vds, vsb, kind, w_key, n_undefined`), 해 없음 → `lut_no_strong_inversion_root`(detail `gm_id, L, vds, vsb, kind, w_key, branch_gm_id_min, branch_gm_id_max, peak_vgs`), 고른 칸 `cell_ok` 거짓 → `lut_hermite_nonmonotone_cell`(detail `gm_id, L, vds, vsb, kind, w_key, axis "VGS", cell_lo, cell_hi` -- 칸 양끝 VGS) |
| `gm_id_for_target(memo, kind, w_key, L, vds, vsb, *, W, gm=None, current=None)` | `TargetSolution(vgs, gm_id, id_a, gm_s)` | Q = `id_vals·W/w_m`(current) 또는 `id_vals·gm_id_vals·W/w_m`(gm) -- 마디 값. 분지 index p 부터 마디 Q 가 엄격히 증가하는 첫 구간 [p, e] 에서 칸 j = p + max(searchsorted(Q[p..e], 목표, left) − 1, 0). j = e 면 vgs = VGS[e], 아니면 [r5] 칸 [j, j+1] 의 VGS Hermite 로 ln Q(vgs) = ln 목표를 `hermite_root` 로 푼다(current: ln Q = p(v) + ln(W/w_m), gm: ln Q = p(v) + ln p'(v) + ln(W/w_m)). 그 vgs 의 `op_point` 로 `gm_id`, `id_a = IDu·W/L`, `gm_s = gm_id·id_a`. 목표가 Q[p]..Q[e] 밖이고 분지 Q 범위 밖 → reason `lut_target_out_of_range`, 범위 안이지만 단조 구간 밖에서만 닿음 → `lut_target_non_monotonic`(detail `quantity, target, W, L, vds, vsb, kind, w_key, branch_min, branch_max, monotone_lo, monotone_hi`). [r5] NaN 마디 → `lut_curve_undefined`(detail `quantity, target, W, L, vds, vsb, kind, w_key, n_undefined`), 칸 j(j < e) 의 `cell_ok` 거짓 → `lut_hermite_nonmonotone_cell`(앞 detail + `axis "VGS", cell_lo, cell_hi`). `gm`·`current` 둘 다/둘 다 없음, `W ≤ 0` → `ValueError` |
| `vdsat(memo, kind, w_key, L, vgs, vds, vsb)` [r6] | float V | 4.3 |
| `tol_vdsat_table(memo, kind, w_key, l_bin_checks=None)` [r6] | `TolVdsatTable` | 5.2 |
| `midpoint_l_bin_checks(memo, kind, w_key)` [r6] | `MidpointChecks` | 5.1 |
| `gmb(memo, kind, w_key, L, vgs, vds, vsb)` | float A/V(폭 w_m) | [r6] GMBS 열이 있으면 4.4 의 열 정의(정본). 없으면 아래 r5 정의. [r5] VS 칸 k = `min(bisect_right(VS, vsb) − 1, len(VS) − 2)`(VS 는 선형 축이라 칸 안 ln ID 가 vsb 에 선형), `gmb = −ID(점) · (ln IDu(VS[k+1]) − ln IDu(VS[k])) / (VS[k+1] − VS[k])`, 세 값 모두 같은 (L, vgs, vds) 의 `op_point`(ID(점) = IDu·w_m/L). 소자 폭 W 값 = `× W / w_m`(부르는 쪽) |
| `caps(memo, kind, L, vgs, vds, vsb, W)` | `Caps(cgg, cgd, cgs, cgb, model)` F | [r4] 4.0 의 L 장(bin 지도 = `CapTable.l_bins`)에서 기준 LUT 열 (L, VGS, VDS, VS) 모든 축 선형 보간([r5] `linear_point`, 4.2 표) × `W / w_ref_m`. CGS·CGB 열이 있으면 `model = "lut_cgs_cgb"`, 없으면 `"cgg_minus_cgd_at_gs"`(cgs = cgg − cgd, cgb = 0.0). 축은 기준 LUT 축(옛 세트 VS 0~0.8 → vsb > 0.8 실패, LUT v2 는 0~1.8). kind 표 없음 → `KeyError`. [r6] `Caps.cdd`·`css` = CDD·CSS 열이 있으면 같은 보간 × W/w_ref_m, 없으면 None. 값은 저장 부호 그대로(음수 가능 -- 로그·절댓값 없음). bin 지도 = `CapTable.l_bins`(1.4 폭 키 수정) |
| `tol_v_table(memo, kind, w_key, l_bin_checks=None)` | `TolVTable` | 5절([r6] 기본값 None = 중점 파일 값) |
| `curve_report(memo)` | `CurveReport(lut_fp, rows)` | 슬라이스·L 앵커마다 `CurveRow`(lut_types 문서): 격자점 곡선만. [r2] `n_curves` = **검사한** 곡선 수(건너뛴 곡선 제외), `n_skipped` = ID·GM 에 0 이하 격자점이 있어 뺀 곡선 수,
`n_curves + n_skipped = len(VDS)·len(VS)`. [r5] `n_hermite_nonmonotone` = 그 L 앵커 i 의 `count(~fc_ok_vgs[i]) + count(~fc_ok_vds[i])`. 행 순서 (kind, w_key) 정렬 후 L 오름차순 |

### 4.2 [r5] 축별 보간 방법 (DEC-87 -- `op_point`·`gm_id_curve`·역산·`gmb` 공통, `_helpers_interp`)

| 양 | L | VGS | VDS | VS |
|---|---|---|---|---|
| ln ID | 선형(4.0 의 L 장) | 2점 cubic-Hermite, 기울기 = 저장 GM/ID | 2점 cubic-Hermite, 기울기 = 저장 GDS/ID | 선형 |
| gm/ID | (ln ID 의 VGS 미분으로 **정의**) | Hermite 미분 | 마디 기울기 S_a 는 선형 | 마디 기울기 S_a 는 선형 |
| ln GDS, VTH, 용량 | 선형 | 선형 | 선형 | 선형 |

- 칸 규칙: 축마다 `cell(grid, x)` = (i, t), i = `min(max(bisect_right(grid, x) − 1, 0), n − 2)`, t = (x − grid[i])/(grid[i+1] − grid[i])
  (마지막 격자점은 마지막 칸 t = 1). 선형 가중치가 0 인 마디(t = 0 이면 i+1, t = 1 이면 i)는 읽지 않는다.
- 2점 cubic-Hermite(x0, x1 = x0 + h, 끝 값 y0·y1, 끝 기울기 m0·m1, t = (x − x0)/h): `p = y0·h00 + h·m0·h10 + y1·h01 + h·m1·h11`
  (h00 = 2t³ − 3t² + 1, h10 = t³ − 2t² + t, h01 = −2t³ + 3t², h11 = t³ − t²), 미분 `p'(x) = dp/dt / h`. 코드는 같은 다항식을 Bernstein
  제어점 (y0, y0 + m0·h/3, y1 − m1·h/3, y1) 의 de Casteljau 로 계산한다(3 = 조건 수 4 − 1). p(x0) = y0, p'(x0) = m0, p(x1) = y1, p'(x1) = m1.
- **조회점 (L, vgs, vds, vsb) 의 계산**(텐서곱 순서):
  1. VGS 칸 [a, a+1] = `cell(VGS, vgs)`, VDS 칸 k = `cell(VDS, vds)`(t_d), VS·L 은 선형 가중(L 은 4.0 의 장 안).
  2. VGS 마디 a' ∈ {a, a+1} 마다 **마디 값** V_a' 와 **마디 기울기** S_a':
     - y_b = Σ_{L, VS 모서리} w·lnID[·, a', b, ·] (b = k, k+1), m_b = Σ w·(GDS/ID)[·, a', b, ·].
     - V_a' = VDS 가 격자점이면 그 y_b, 아니면 Hermite(y_k, y_k+1, m_k, m_k+1, h_d, t_d) -- 단, 가중치 0 이 아닌 (L, VS) 모서리의
       `vds_slope_ok` 가 (b = k, k+1) 모두 참이고 `fc_ok_vds[·, a', k, ·]` 가 모두 참일 때만, 아니면 VDS 선형 y_k + t_d·(y_k+1 − y_k).
     - S_a' = Σ_{L, VDS, VS 모서리(가중치 ≠ 0)} w·(GM/ID) -- 그 모서리 중 `on_mask` 거짓이 있으면 NaN.
  3. **VGS Hermite 칸** = S_a·S_a+1 이 둘 다 유한이고 `fc_ok_vgs[·, a, ·, ·]` 가 가중치 ≠ 0 인 (L, VDS, VS) 모서리에서 모두 참.
     Hermite 칸이면 lnID = p(vgs), gm/ID = p'(vgs) (VGS 가 격자점 t ∈ {0, 1} 이면 그 마디의 V·S 그대로 -- 반올림 없음),
     아니면 lnID = V_a + t·(V_a+1 − V_a), gm/ID = (V_a+1 − V_a)/h (그 직선의 미분 -- 정의 유지).
- 결과: 격자점(네 축 모두 격자 위, L 앵커)에서 lnID·gm/ID·lnGDS·VTH 는 저장값 그대로(r4·옛 다선형과 같은 값, gm_gds 만 식이
  `gm/ID·exp(lnID − lnGDS)` 라 몇 ulp 차). 마디 사이에서 gm/ID 는 ln ID 의 VGS 미분과 **같다**(같은 곡면).
- 이 표에 없는 축 조합의 기울기 자료(GMBS 열 -- VS 축 Hermite 기울기 −GMBS/ID)는 열이 생기면 VS 를 Hermite 로 바꾼다(DEC-87, 계획 범위 밖).
  [r6] LUT v2 의 GMBS 는 **기준 LUT(W = w_ref) 에만** 있고 ln ID 곡면은 슬라이스에서 만든다 -- 슬라이스 32개 중 31개에는 기울기 자료가
  없어 폭마다 VS 방법이 갈리게 된다. 그래서 VS 축은 r6 에서도 선형으로 둔다(슬라이스 생성기가 GMBS 를 쓰면 바꾼다, 8절).
- [r5 실측 2026-10-07, ngspice-46 새 점 -- code author 측정, 소자 W = 5 µm(w_key 1000), L 0.15·0.35·1·4 µm, VS 0·0.4 V, 강반전 분지
  (VGS ≥ 그 곡선 정점) · VDS ≥ 2 격자칸] 칸 중앙 오차(엔진 op_point 대 ngspice, `|Δln ID|/(gm/ID)` V 단위 / gm/ID 상대):
  - VGS 칸 중앙(VDS 격자점) nmos: r4 p50 0.286 mV·p99 0.904 mV / gm/ID p99 0.53 % → r5 p50 0.13 µV·p99 2.5 µV / p99 0.0012 %
    (pmos r4 p50 0.297 mV·p99 0.773 mV / 0.49 % → r5 p50 0.26 µV·p99 2.2 µV / 0.0010 %), 18,048점씩.
  - VDS 칸 중앙(VGS 격자점) nmos: r4 p99 11.1 mV → r5 p99 0.149 mV(pmos 5.36 → 0.064 mV), gm/ID 상대 p99 0.22 % → 0.20 %
    (gm/ID 의 VDS 방향은 설계상 선형 -- 변화 없음이 맞다), 18,032점씩.
  - 격자점 대조(L 0.35 µm, 4,606점씩): ngspice 재실행 ID = LUT ID(차 0), gm/ID 상대 ≤ 6.4e-15(ngspice GM/ID 와 LUT 저장 GM/ID 의 계산 차).
    r5 op_point 의 격자점 값은 옛 다선형과 비트 단위로 같다(6절, 실데이터 1,168 격자점 대조 -- gm_gds 만 상대 ≤ 2.2e-16).
- [r5 실측] 시간(같은 기계, 다른 agent 부하 있음 -- 비율만 참고): op_point 2000점 새 memo 0.21 s → 0.38 s(점당 ~105 → ~190 µs, memo 키
  지문 비용 ~80 µs 포함), vgs_for_gm_id 300회(곡선 포함) 0.93 s → 0.43 s.

### 4.3 [r6] 선택 열 출처와 `vdsat`

**열 출처 `column_source(lut, kind, w_key, column, required=True)`**(`_helpers_columns`, 반환 `ColumnSource(origin, column, kind, w_key,
table_w_m, grids, array, l_bins, on_mask)`): (1) 슬라이스 (kind, w_key) 의 `columns` 에 열이 있으면 origin "slice"(그 슬라이스의 축·
bin 지도·on_mask) (2) 아니면 `cap_map[kind].w_key == w_key` 이고 기준 LUT `columns` 에 열이 있으면 origin "cap_table"(기준 LUT 축·
`CapTable.l_bins`·`CapTable.on_mask`, `table_w_m` = w_ref_m) (3) 아니면 `required` 면 `SealViolationError` **`lut_column_unavailable`**
(detail `column, kind, w_key, cap_w_key, slice_columns, cap_columns` -- 뒤 둘은 이름 정렬 tuple), 아니면 None. 슬라이스 없음 → `KeyError`.
**다른 폭의 열로 대신하지 않는다**(폭 무관 가정을 박지 않음). LUT v2 에서 VDSAT·GMBS 는 폭 키 1000(5 µm) 에서만 있다 -- sizing 의
레이아웃 전 폭 규칙(`pre_layout_lut_access`)이 nmos·pmos 모두 1000 을 쓰므로 그 경로는 열이 있다.

**`vdsat(memo, kind, w_key, L, vgs, vds, vsb) -> float`(V)**: 열 = `column_source(..., "VDSAT")`. L 위치 = `l_position(src.grids[0],
src.l_bins, L, context)`, 축 검사 = `check_axes(src.grids[1:], ...)`(context = `kind, table = src.origin, w_key`), 값 = 4.0 의 L 장에서
`linear_point`(**모든 축 선형, 값 공간**). memo point 키 `(kind, w_key, lo, hi, L 값, vgs, vds, vsb)`. 실패 = 열 없음(`lut_column_unavailable`,
memo 에 저장 안 됨)·4.0·4.1 사유.
- 왜 선형인가: VDSAT 의 도함수 열이 LUT 에 없다. 4.2 의 Hermite 는 저장 GM/ID·GDS/ID 가 ln ID 의 정확한 편미분이라서 썼다 -- 격자
  차분으로 기울기를 만들면 그 기울기 자체가 새 추정(3점 차분 = 다른 보간법)이고 운영 보간과 tol 의 '같은 방법'이 깨진다. 오차는 같은
  방법(선형) LOO 로 잰다(5.2). 격자점에서는 저장값 그대로.
- 정의 통일(DEC-88): 열 = 생성기 meta "VDSAT = ngspice @m[vdsat], same as tools/spice_oracle" -- 오라클 포화 판정과 같은 양.

### 4.4 [r6] `gmb` 정본 = GMBS 열
- GMBS 열이 있으면(`column_source(..., "GMBS_PER_ID", required=False)` 가 None 아님): `gmb = ID(점) × r`, ID(점) = `op_point(memo, kind,
  w_key, L, vgs, vds, vsb).IDu · w_m / L값`(같은 Hermite 곡면), r = 파생 열 GMBS_PER_ID 의 4.0 L 장 + 모든 축 선형 보간(축·bin 지도 =
  열 출처 표의 것, context table = origin). r 이 NaN(가중치 ≠ 0 인 모서리에 ID ≤ 0 -- LUT v2 는 VDS = 0 열뿐)이면 GMBS 열 값의 같은
  선형 보간. 격자점에서 r·ID(점) = 저장 GMBS × (슬라이스 ID / 기준 LUT ID).
- 열이 없으면 r5 정의(4.1 표 VS 할선) 그대로.
- 왜 열이 정본인가: 오라클 SPICE 의 `gmbs` 와 같은 양이고, 할선은 VS 칸(0.2 V) 평균 기울기라 점 미분이 아니다.
- [실측 2026-10-08, LUT v2 w_key 1000, 무작위 1500 (L 앵커, VGS index ≥ 8 격자점과 그 칸 중앙, VDS index ≥ 8, VS 격자) 점, seed 20261008]
  r5 할선 대 열 정의 상대차 p50/p90/p99/max: nmos 격자점 2.2 %/5.3 %/8.0 %/13.5 %, 칸 중앙 2.1 %/5.1 %/8.0 %/13.8 %; pmos 격자점
  2.3 %/5.2 %/18.0 %/85.8 %, 칸 중앙 2.2 %/5.1 %/19.0 %/90.0 %. 열 경로 대 저장 GMBS(격자점) 상대차 최대 4.9e-7(슬라이스 ID 와 기준 LUT ID 의
  print 자릿수 차, 3.4절 REGEN_REPORT 5e-7 과 같은 크기).

## 5. [r2 전면 교체, r4 L 방향 추가, r5 같은 방법 LOO + Richardson] tol_V 표 `tol_v_table(memo, kind, w_key, l_bin_checks=()) -> TolVTable` (계획 N3.6, 사용자 확정 2026-10-07)

- **보간 축 VGS·VDS·VS leave-one-out + [r4] 같은 모델 bin 안의 L 축 leave-one-out.** **모든 L 앵커가 셀을 가진다**(r1 의 '양끝 앵커 None' 폐기).
- 셀 = (kind, w_key, L 앵커 i, VDS 격자 k) -- `cells[i][k]` = `TolVCell`. **셀별 값만** 낸다(전역 최댓값으로 줄이지 않음).
- [r5] **LOO 추정 = 운영 보간과 같은 방법**(DEC-87, 4.2): 축 a, 내부 격자점 x_j(0 < j < n_a − 1), 이웃 x_{j−1}·x_{j+1},
  H = x_{j+1} − x_{j−1}, t = (x_j − x_{j−1})/H.
  - ln ID 추정: VGS 축 = Hermite(lnID_{j−1}, lnID_{j+1}, (GM/ID)_{j−1}, (GM/ID)_{j+1}, H, t), 두 이웃 `on_mask` 가 참일 때(아니면 선형);
    VDS 축 = Hermite(같은 식, 기울기 (GDS/ID)), 두 이웃 `vds_slope_ok` 일 때(아니면 선형); VS·L 축 = 선형 `lnID_{j−1} + t·(lnID_{j+1} − lnID_{j−1})`.
  - gm/ID 곡선의 LOO(gm_id_inverse 용, 아래): VGS 축 = 마디 j 를 **뺀** 곡선(칸 [j−1, j+1] 이 하나의 Hermite 칸이 된다);
    VDS 축 = 각 VGS 마디의 ln ID 를 위 VDS 식(Hermite/선형)으로, gm/ID 를 선형 `g_{k−1} + t·(g_{k+1} − g_{k−1})` 으로 만든 곡선;
    VS·L 축 = ln ID·gm/ID 모두 선형으로 만든 곡선. LOO 는 측정이라 FC 단조 검사로 거르지 않는다.
- [r5] **Richardson 환산**(Q2 (ii) (A)): LOO 는 간격 2배(H = 2h) 격자의 오차라 운영 칸(간격 h)의 칸 중앙 오차보다 2^p 배 크다.
  점마다(id_equivalent)·시도마다(gm_id_inverse) LOO 값을 **그 (지표, 축, 방법) 의 차수 p 로 2^p 나눈 값**을 셀 값의 후보로 쓴다.
  p 는 방법에서 유도(새 상수 0): 값 보간 차수 = 조건 수(선형 2, Hermite 4), Hermite 미분 = 4 − 1 = 3. 표(`tolerance.LOO_ORDERS`,
  `TolVTable.loo_orders` = ((지표, 축, 방법, p, 2^−p), ...)):

  | 지표 | L | VGS | VDS | VS |
  |---|---|---|---|---|
  | `id_equivalent` | linear p 2 | hermite p 4 | hermite p 4 | linear p 2 |
  | `gm_id_inverse` | linear p 2 | hermite_slope p 3 | linear_slope p 2 | linear p 2 |

  id_equivalent 의 VGS·VDS 점에서 위 'Hermite 조건'이 거짓이라 선형으로 추정한 점은 p = 2. gm_id_inverse 의 VDS 는 gm/ID 가 VDS 에
  선형(4.2)이라 p = 2. 비균일 격자(L 축)도 같은 2^p 를 쓴다(VGS·VDS·VS 격자는 균일).
  [code author 해석 -- 계획 문구는 'Hermite 4' 이고 gm/ID 의 VGS 축 3 은 미분 차수에서 유도한 것. 확인 대상]
- **두 지표**(`TOL_V_METRICS`; 소비자 배정은 계획 N3.6 -- `gm_id_inverse` = gm/ID 를 목표로 VGS 를 역산하는 단계(층 0),
  `id_equivalent` = 봉인 2(DEC-88)·KCL·W 허용오차 상한·소자 경고·순환 블록 수렴):
  - `id_equivalent`: 격자점 (i, g, k, s) 마다, 축 a 방향으로 그 점과 두 이웃이 모두 `on_mask` 이면 `|lnID_loo − lnID| / (gm/ID) / 2^p`
    (gm/ID = 그 점의 저장값 GM/ID). 셀 값 = 그 (i, k) 의 모든 g·s·a 최댓값.
  - `gm_id_inverse`: 곡선 (i, k, s) 의 `on_mask` 가 VGS 전부 참일 때만. 목표 j = 참 곡선 gm/ID g 의 정점 이후 index 중 오른쪽 모든 점보다
    g_j 가 큰 점(VGS_j = 그 곡선의 분지 해, 3절). 목표마다 LOO 곡선 최대 4개:
    VGS 축(j 가 VGS 양끝이면 없음), VDS 축(k 가 내부이고 곡선 (i, k±1, s) 의 on_mask 전부 참일 때),
    VS 축(s 내부, 곡선 (i, k, s±1) 같은 조건), [r4] L 축(i 가 bin 안 내부 앵커 -- 아래 'L 축 규칙', 곡선 (i±1, k, s) 같은 조건).
    시도마다 [r5] `|strong_inversion_root(LOO 곡선, g_j) − VGS_j| / 2^p`(3절의 운영 역산 -- 칸 선택 + 칸 안 Hermite 미분 근),
    해 없으면 값에 넣지 않고 실패로 센다. 셀 값 = 모든 s·j·축 최댓값.
- [r5] `TolVCell` 에 환산 전 값 `gm_id_inverse_loo_v`·`id_equivalent_loo_v`(같은 규칙의 환산 전 셀 최댓값, 정의 없으면 None)가 더해졌다
  (기본값 None -- 4칸 생성자 호출도 받는다). 외부 L 값(`l_bin_checks`, 아래)은 이미 운영 보간의 칸 중앙 오차라 **환산하지 않고**
  환산 후 셀 값과의 최댓값에만 들어간다(환산 전 필드에는 들어가지 않는다).
- **[r4] L 축 규칙(bin 안에서만)**: 앵커 i 의 L 방향 LOO 는 `anchor_bin[i−1] == anchor_bin[i] == anchor_bin[i+1]`(0 < i < n_L − 1, 1.4 의 지도)일
  때만 만든다 -- 운영 L 보간이 같은 bin 의 두 앵커만 쓰므로 경계를 건너는 추정은 만들지 않는다. 식은 위 LOO 식에서 x = L 격자(t 도 L 로).
  `id_equivalent` 의 L 방향 점 조건은 다른 축과 같다(그 점·두 이웃 on_mask). 빈 지도면 L 방향 LOO 없음(r2 값 그대로).
  - 앵커 3개 이상 bin: 첫·끝 앵커를 뺀 내부 앵커에만 L 방향 값이 있다(첫·끝 앵커 행은 L 방향 몫 없음 -- 그 bin 의 L 보간 오차는 내부 앵커 행이 잰다).
  - 앵커 2개 bin: LOO 정의 불가. 부르는 쪽이 **`l_bin_checks`** = `((model, gm_id_inverse_v, id_equivalent_v), ...)`(V, 값 None 허용 -- bin 중점
    검증 시뮬레이션에서 잰 그 bin 의 L 보간 오차, `lut_regen_plan.md` 2절 K2')를 주면 그 bin 두 앵커 행의 모든 셀에서 **정의된** 셀 값과의
    최댓값을 셀 값으로 한다(셀 값이 None 이면 None 그대로 -- 켜진 격자점이 없는 셀). `n_targets`·`n_inverse_failed` 는 바뀌지 않는다.
    주지 않으면 상태 "missing_external" 로 남는다(값에 L 방향 몫 없음을 명시).
    [r6] **기본값 `l_bin_checks=None`** = `midpoint_l_bin_checks(memo, kind, w_key).rows` 의 `(model, gm_id_inverse_v, id_equivalent_v)`
    (5.1 -- LutSet 에 중점 표가 없으면 그 조회 없이 `()`). `()` 을 명시하면 외부 값 없음(r5 기본 동작). 실제로 쓴 값은
    `TolVTable.l_bin_checks`(정규화 tuple, model 정렬).
  - 앵커 1개 bin: 그 bin 안 L 보간 자체가 없다(4.0 `lut_l_bin_unbracketed`) -- L 방향 값 불필요, 상태 "single_point".
  - `l_bin_checks` 오류 → `ValueError`: 같은 model 두 번, 앵커 2개 bin 이 아닌 model(지도에 없는 이름 포함), 빈 지도 슬라이스에 비어 있지 않은 값.
  - memo 키 = `(kind, w_key, l_bin_checks 정규화)`(model 문자열·float/None, model 정렬) -- 다른 외부 값은 다른 표.
- `TolVTable.l_loo`: 앵커마다 상태 -- `"in_bin_interior"`(L 방향 LOO 들어감), `"bin_edge"`(3개 이상 bin 의 첫·끝 앵커), `"bin_external"`,
  `"bin_missing_external"`(앵커 2개 bin, 외부 값 있음/없음), `"bin_single_point"`, `"bins_unavailable"`(빈 지도).
  `TolVTable.l_loo_bins`: 앵커가 하나 이상 든 bin 마다 `(model, 앵커 index tuple, 상태)`(bin index 오름차순), 상태 `"computed"`(3개 이상)·
  `"external"`·`"missing_external"`·`"single_point"`. 빈 지도면 `()`.
- **축 양끝 격자점 규칙**: 어떤 축의 양끝 격자점은 **그 축 방향** LOO 추정이 없고(이웃이 한쪽뿐 -- 외삽 추정은 만들지 않음), 다른 축 방향
  추정은 그대로 있다. 그래서 VDS 양끝 셀(k = 0, n_VDS − 1)은 VGS·VS 방향 값만으로, VGS 양끝 목표는 VDS·VS 방향 곡선으로만 정해진다.
  어떤 추정도 없는 셀의 그 지표 = None.
- `TolVCell(gm_id_inverse_v, id_equivalent_v, n_targets, n_inverse_failed)`: [r2] `n_targets` = 그 셀의 gm/ID 역산 **시도** 수((목표, 축) 쌍),
  `n_inverse_failed` = 그중 해 없음 수.
- `TolVTable.at(L, vds, metric)`: [r4] L 위치는 4.0 판정(`TolVTable.l_bins`) -- 앵커면 행 {i}, 같은 bin 보간이면 행 {below, above};
  거부 사유는 4.0 그대로(context kind·table "tol_v"·w_key). VDS 칸 k = `min(bisect_right(vds_grid, vds) − 1, n − 2)`,
  그 행들 × 칸 (k, k+1) 셀의 그 지표 값 중 정의된 것의 최댓값(없으면 None). `metric` 이 TOL_V_METRICS 밖 → `ValueError`,
  VDS·L 범위 밖 → `SealViolationError`(`lut_axis_out_of_range`, table "tol_v").
- `TolVTable` 속성: `kind, w_key, L_anchors, vds_grid, cells`, [r4] `l_bins, l_loo, l_loo_bins`.
- `TolVTable` [r5] 속성 `loo_orders`(위 환산 표 그대로). [r6] 속성 `l_bin_checks`(위).
- [r6] r5 의 `tolerance.py` 안 helper(`_l_interior`·`_l_loo_report`·`_external_by_model`·`_loo`·`_cell_max`·`_targets`·`_with_external`·
  `_opt`·`at` 본문)는 `_helpers_loo` 로 옮겨 `tol_vdsat_table`·`midpoint_l_bin_checks` 와 같이 쓴다 -- 식·순서·오류 문장 같음.
- [r6 실측 2026-10-08, LUT v2 w_key 1000, 기본 `l_bin_checks=None`(중점 파일)] 계산 nmos 19.6 s·pmos 19.7 s(중점 검증 포함). bin 상태(nmos·pmos
  같음): .26 (앵커 0, 1 = 0.15·0.18) **external**, .25 (2, 3, 4) computed, .24 (5~9) computed, .23 (10, 11 = 0.7·1)·.22 (12, 13 = 1.5·2)·
  .21 (14, 15 = 2.5·4) **missing_external**(이 bin 들의 중점이 파일에 없다 -- 8절), .20 (16 = 8)·.19 (17 = 20) single_point. 외부 값(.26):
  nmos gm_id_inverse 518 mV·id_equivalent 18.9 mV, pmos 316 mV·22.7 mV. 셀 값 p50/p90/max: id_equivalent nmos 0.94/18.9/18.9 mV,
  pmos 0.94/22.7/22.7 mV; gm_id_inverse nmos 52/518/518 mV, pmos 65/316/316 mV(p90 = 외부 값 -- 앵커 0·1 행 전부가 그 값).
- [r5] **환산 검증 test(ngspice 칸 중앙 표본, 계획 N3.6 -- test 작성자 구현, 실데이터 마커)**: 셀 표본(최소: nmos·pmos w_key 1000,
  L 앵커 0.15·0.35·1·4 µm, VS index 0·2, 모든 VDS 격자점)에서 ngspice 로 **VGS 칸 중앙**(VGS_j + h/2, VDS·VS 격자점)과
  **VDS 칸 중앙**(VDS_k + h/2, VGS·VS 격자점)의 ID·GM 을 새로 잰다. 넷리스트는 슬라이스 생성기(`_drafts/engine/lut_slices/
  sky130_dc_width_slices.py` `build_netlist`)와 같은 소자·기하·극성·바디 부호(dc 스윕 시작을 반 칸 옮김). 점마다
  e = |ln ID_op_point − ln ID_spice| / (GM/ID)_spice. 판정: (a) 강반전 분지(VGS ≥ 그 격자 곡선 정점)·VDS ≥ 2 격자칸 점에서 e ≤
  `tol_v_table(...).at(L, vds, "id_equivalent")` 가 **모든 점**에서 성립(셀 tol 은 상한이어야 한다) (b) VGS 칸 중앙 e 의 p50·p99 가
  VGS 축 id_equivalent LOO(환산 전, 같은 점들의 이웃 j)/2^4 의 p50·p99 와 같은 자릿수(비 0.5~2 -- Richardson 환산이 맞는지).
  (c) 같은 넷리스트를 격자점에서 돌리면 LUT 값과 같다(설정 동일성 확인). [실측 2026-10-07, code author] (a) e / 셀 tol 최대 0.0048
  (VGS 중앙)·0.29(VDS 중앙), 넘는 점 0/72,160 (b) nmos: 칸 중앙 e p50 0.13 µV·p99 2.5 µV 대 LOO/16 p50 0.15 µV·p99 2.6 µV, pmos:
  0.26·2.2 µV 대 0.30·2.5 µV(선형 r4 도 같은 방식으로 0.286·0.904 mV 대 LOO/4 0.289·0.961 mV) (c) ID 차 0.
- [r5 실측 2026-10-07, 생성 슬라이스 w_key 1000, l_bin_checks 없음 -- code author 측정, 같은 기계 r4 와 나란히] 계산 2표(nmos+pmos)
  48.9 s → 24.0 s. id_equivalent 셀 p50/p90/max: nmos 4.1/21.2/264 mV → **0.87/1.9/5.5 mV**, pmos 3.8/12.5/201 mV → **0.93/2.8/3.7 mV**
  (환산 전 nmos 3.5/7.6/41.8 mV, pmos 3.7/11.5/31.9 mV -- VS 축 선형 LOO 가 지배). gm_id_inverse 셀 p50/p90/max: nmos 229/293/402 mV
  → **49/73/114 mV**, pmos 254/449/492 mV → **61/113/124 mV**(환산 전 nmos 195/290/455, pmos 244/451/494 mV -- 정점·약반전 평탄
  목표의 조건수 효과). 역산 시도(실패) nmos 814,032 (56,517), pmos 779,455 (67,164) -- VGS 축 LOO 가 마디를 빼는 정의라 r4 와 실패 수가
  다르다. VGS 축만의 id_equivalent LOO(독립 numpy, 강반전 on 점): nmos 선형 p50 1.16 mV·p99 3.85 mV → Hermite p50 2.3 µV·p99 42 µV,
  pmos 0.95/3.37 mV → 4.8/39 µV.
- [r4 실측 2026-10-07, 생성 슬라이스 w_key 1000, l_bin_checks 없음 -- code author 측정] 계산 nmos 15.7 s·pmos 16.3 s. bin 상태(nmos·pmos 같음):
  model .26 (앵커 0) single_point, .25 (1, 2) missing_external, .24 (3, 4, 5, 6) computed, .23 (7, 8) missing_external, .22 (9) single_point,
  .21 (10, 11) missing_external → L 방향 LOO 가 있는 앵커는 0.35·0.425 µm 둘뿐. gm_id_inverse p50/p90/max = nmos 229/293/402 mV,
  pmos 254/449/492 mV; id_equivalent p50/p90/max = nmos 4.1/21.2/264 mV, pmos 3.8/12.5/201 mV; 역산 시도(실패) nmos 814,032 (53,720),
  pmos 779,455 (65,335). 앵커 행 최댓값 gm_id_inverse: nmos 0.35 µm 369 mV·0.425 µm 373 mV, pmos 492·454 mV.
- [r2 실측 -- L 방향 LOO 없던 정의, 참고] 계산 nmos 14.9 s·pmos 13.5 s. 정의된 셀 576개(12 앵커 × 48 VDS -- VDS = 0 열은 ID 0 이라 정의 없음).
  gm_id_inverse 셀 p50/p90/max = nmos 222/286/402 mV, pmos 224/371/445 mV(역산 실패 시도 nmos 44,003/766,992, pmos 56,389/733,056).
  id_equivalent p50/p90/max = nmos 3.7/21.1/264 mV, pmos 3.6/10.6/201 mV. gm_id_inverse 의 큰 값은 VGS 축 LOO(간격 37.5 mV)가 정점·약반전
  평탄 구간 목표에서 내는 조건수 효과다(값의 채택은 소비자 설계 몫).

### 5.1 [r6] 앵커 2개 bin 의 외부 값 `midpoint_l_bin_checks(memo, kind, w_key) -> MidpointChecks`
- memo derived, 키 `(kind, w_key)`. `MidpointChecks(kind, w_key, rows, skipped, midpoints_sha256)`.
- `lut.midpoints` 에 kind 가 없으면 `MidpointChecks(kind, w_key, (), (), None)`.
- 중점 m(L_m, `L_points` 순서)마다 아래 순서로 판정, 쓰지 않으면 `skipped` 에 `(L_m, 사유, model 또는 None)`:
  1. 중점 표 `w_key` ≠ 조회 w_key → `"width_differs"`(다른 폭으로 옮기지 않는다) 2. 슬라이스 bin 지도 없음 → `"bins_unavailable"`
  3. L 앵커와 1 ulp 이내 → `"is_anchor"` 4. `bin_index`(4.0.1)로 bin 없음 → `"outside_model_bins"` 5. 그 bin 의 앵커 수 < 2 → `"single_point"`(model 있음),
  > 2 → `"bin_has_interior_anchors"` 6. 두 앵커 a0 < L_m < a1 가 아님 → `"not_bracketed"`.
- 남은 중점: t = (L_m − a0)/(a1 − a0), 슬라이스 앵커 행 i0·i1.
  - `id_equivalent_v` = max over (VGS, VDS, VS) 격자점 [중점 on_mask ∧ 슬라이스 on_mask(i0) ∧ on_mask(i1)] of
    |lnID(i0) + t·(lnID(i1) − lnID(i0)) − lnID_m| / gm_id_m (`DcSlice.log_ID`, 중점 `log_ID`·`gm_id`). 점 없음 → None.
  - `gm_id_inverse_v`: 곡선 = (VDS_k, VS_s), 곡선 on = 위 마스크가 VGS 전부 참. 중점 곡선 gm/ID g(off 점은 −∞)에서 5절 목표 규칙
    (`branch_targets` -- 정점 이후, 오른쪽 모든 점보다 큼)으로 (곡선, j). 보간 곡선 = (lnID, gm/ID) 를 L 선형(gm/ID 앵커 값 =
    exp(log_GM − log_ID)) -- 운영 `gm_id_curve` 의 마디 값과 같다. 값 = max |strong_inversion_root(보간 곡선, g_j) − VGS_j|(해 있는 것),
    `n_targets` = 목표 수, `n_inverse_failed` = 해 없음 수. 목표 없음 → None, 0, 0.
  - `vdsat_v`: `column_source(..., "VDSAT", required=False)` 가 있고 중점 VDSAT 이 있고 출처 표 축(VGS, VDS, VS) = 중점 축일 때,
    max over [중점 on_mask ∧ (출처 on_mask(i0) ∧ on_mask(i1), 출처에 on_mask 가 없으면 생략)] of |V(i0) + t·(V(i1) − V(i0)) − VDSAT_m|, 아니면 None.
  - Richardson 환산 없음(운영 보간의 칸 안 오차 자체).
- 같은 bin 의 중점이 여럿이면 한 `MidpointRow` 로 합친다: `L_points` 오름차순(파일 순서), 세 값은 최댓값(None 은 무시), 개수는 합.
  `rows` = model 이름 정렬.
- [실측 2026-10-08, LUT v2 + 중점 파일, w_key 1000] nmos: rows = ((.26, (1.65e-7,), gm_id_inverse 0.5181 V, id_equivalent 0.01893 V,
  vdsat 0.00249 V, 23,520 목표, 실패 0)), skipped = ((6e-6, "single_point", model.20), (1.4e-5, "single_point", model.19)). pmos: (.26, 0.3159 V,
  0.02271 V, 0.03253 V, 19,671, 1,569), 같은 skipped. nmos w_key 84 → 세 중점 모두 "width_differs".
  중점 0.165 µm 점별 분포(독립 numpy 재계산): id_equivalent p50/p90/p99/max nmos 6.0/12.1/16.8/18.9 mV, pmos 6.6/14.1/20.4/22.7 mV;
  gm_id_inverse nmos 10.5/206/440/518 mV(최악 목표 gm/ID 24.7 -- 정점 근처 평탄 목표), 목표 gm/ID ≤ 15 만 보면 8.9/20/26/29 mV,
  pmos 6.4/100/286/316 mV(≤ 15: 3.9/8.8/57/111 mV).

### 5.2 [r6] VDsat 허용오차 `tol_vdsat_table(memo, kind, w_key, l_bin_checks=None) -> TolVdsatTable`
- 열 = `column_source(..., "VDSAT")`(없으면 `lut_column_unavailable`, 표를 만들지 않음). 축·bin 지도 = 열 출처 표의 것.
- 셀 (i_L, k_VDS) -- 5절과 같은 틀(`_helpers_loo`): 축 a ∈ AXES 마다 내부 격자점 x_j 를 빼고 두 이웃의 **선형** 추정(운영 `vdsat` 와 같은
  방법), 점 조건 = 그 점과 축 방향 두 이웃이 출처 `on_mask`(None 이면 모든 점), L 축은 `l_interior`(bin 안 내부 앵커)에서만.
  점 값 = |VDSAT_loo − VDSAT|(V). 셀 `TolVdsatCell(vdsat_v, vdsat_loo_v)`: `vdsat_loo_v` = 환산 전 셀 최댓값, `vdsat_v` = 점 값 / 2^2
  (선형 차수 p = 2, 네 축 모두)의 셀 최댓값과 외부 bin 값의 최댓값(셀 값이 None 이면 None).
- 외부 값 `l_bin_checks = ((model, vdsat_v), ...)`: None(기본) = `midpoint_l_bin_checks` rows 의 `(model, vdsat_v)`(중점 표 없으면 `()`),
  `()` = 없음. 오류 규칙(중복·앵커 2개 bin 아님·빈 지도에 값 → `ValueError`)과 `l_loo`·`l_loo_bins` 상태 이름은 5절과 같다.
- `TolVdsatTable` 속성: `kind, w_key, origin, L_anchors, vds_grid, cells, l_bins, l_loo, l_loo_bins, loo_orders, l_bin_checks`.
  `loo_orders` = (("vdsat", "L", "linear", 2, 0.25), ("vdsat", "VDS", ...), ("vdsat", "VGS", ...), ("vdsat", "VS", ...))(축 이름순).
  `at(L, vds, metric="vdsat")` = 5절 `TolVTable.at` 와 같은 행·칸 규칙(`table_at`), context `kind, table "tol_vdsat", w_key`, metric 이
  `TOL_VDSAT_METRICS` 밖 → `ValueError`. memo derived 키 `(kind, w_key, l_bin_checks 정규화)`.
- 소비자(sizing O1): 봉인 7 `VDS − VDsat ≥ +tol_VDsat` 의 tol_VDsat = `tol_vdsat_table(memo, kind, w_key).at(L, vds)`.
- [실측 2026-10-08, LUT v2 w_key 1000, 기본 외부 값] 출처 "cap_table", 계산 0.22 s. 셀 vdsat_v p50/p90/max nmos 0.93/2.49/2.49 mV,
  pmos 1.08/32.5/32.5 mV(p90·max = .26 외부 값 -- pmos 0.165 µm 중점 VDSAT 보간 오차 32.5 mV), 환산 전 nmos 3.3/4.4/8.5 mV, pmos
  4.1/9.8/22.2 mV. bin 상태는 5절 실측과 같다. 예: `vdsat(nmos, 1000, 1 µm, 0.9, 0.9, 0)` = 0.2557 V, L 0.85 µm·vsb 0.3 = 0.2107 V,
  `tol_vdsat_table(nmos, 1000).at(1e-6, 0.9)` = 0.93 mV. w_key 84 → `lut_column_unavailable`(cap_w_key 1000, slice_columns ()).

---

## 6. [r5 개정] 복사본 AST 해시 (설계 2.1 '복사'·'블록 복사')와 옛 다선형 참조

판정: 대상 문장 목록(docstring 제외)의 `ast.dump(Module(body=문장들), include_attributes=False)` sha256 이 옛 것과 같다.
함수 이름 변경은 허용. 블록 복사는 (첫 문장, 끝 문장) 앵커로 구간을 자르고, 이름 바꿈 표를 옛 AST 에 적용한 뒤 비교한다.
옛 파일 `legacy/sizing_recipe.py`(이 브랜치) = 태그 `legacy-engine-v1`(`skills/analog-gmid-design/assets/sizing_recipe.py`)의 같은 정의(해시 같음).

| 새 위치 | 옛 위치 | 문장 수 | 이름 바꿈 | sha256 (옛 = 새) |
|---|---|---|---|---|
| `provenance._lut_conditions_from_npz` 본문 | `lut_conditions_from_npz` SR:4782 | 3 | (함수 이름만) | `20513c618b94f19b50d8a4fcfc2fd0a17f934302259ed4e78d4b21163451235b` |

[r5] **복사 고정에서 빠진 것(DEC-87 '옛 다선형 보간 복사본은 기대값 비교 참조로만')**: r4 표의 `_helpers_interp.multilinear_interp`·
`multilinear_interp_point_multi`(옛 SR:141·206), `gm_id_curve._curve_arrays`(옛 `_gm_id_curve` SR:463~474), `_helpers_root.strong_inversion_root`
구간 A·B(옛 `_solve_vgs` SR:539~540·548~561)는 운영 경로가 Hermite 로 바뀌어 패키지에서 없어졌다(운영 경로에 쓰이지 않는 복사본을 패키지에
두면 구조 규칙 A 보충 (3) -- helper 공개 함수는 다른 파일 2개 이상이 import -- 도 어긴다). **기대값 비교 참조 = 옛 파일 원본**
(`legacy/sizing_recipe.py` = 태그 `legacy-engine-v1`) 의 아래 정의다. test 는 그 정의를 원본에서 읽어(AST 해시로 원본이 바뀌지 않았음을
확인한 뒤) 실행해 기대값을 만들 수 있다:

| 참조 정의(옛 파일) | 문장 수 | sha256(본문, docstring 제외) | 쓰임 |
|---|---|---|---|
| `_multilinear_interp` SR:141 | 8 | `d6bfc65c25e6e68f6b5f820c3a5a53ed6ed2429db00dc640ba15615dc7d69c54` | 격자점 동치 기대값 |
| `_multilinear_interp_point_multi` SR:206 | 7 | `76e24d9d66e06b760dc79b9d69ac51143cec7238046f9ed3ffd27a4b624c7cba` | 격자점 동치 기대값 |

**옛 함수와의 동치 test 는 격자점에서만**(DEC-87): L 앵커·VGS·VDS·VS 모두 격자점인 조회에서 `op_point` 의 IDu·gm_over_id·gds_per_w·vth 는
옛 다선형 결과(로그공간, 같은 바닥 규칙)와 **비트 단위로 같고**, gm_gds 는 식이 `gm/ID·exp(lnID − lnGDS)` 로 바뀌어 상대 차 ≤ 1e-14 다
(실측 최대 2.2e-16, 3 슬라이스 1,168 격자점 -- 마지막 격자점 포함).
`gm_id_curve` 는 VDS·VS 가 격자점이면 마디 값(`id_vals`, `gm_id_vals`)이 옛 곡선과 비트 단위로 같다. 격자 밖 조회의 기대값은 4.2 의
식(독립 구현)이나 7절 toy 의 닫힌 식에서 낸다. 옛 `_solve_vgs` 와의 비교는 3절 칸 선택 규칙만 같고(칸 index), 칸 안 근은 다르다.

---

## 7. 손계산 toy (test 작성자가 그대로 만들 수 있는 입력)

[r5] toy 를 **기울기 자료가 값 자료의 미분과 맞는** r5 toy 로 바꿨다(r4 toy 는 GM/ID 가 d lnID/dVGS 와 다르고 GDS/ID 가 d lnID/dVDS
와 달라 Hermite 칸이 단조 위반 -- 아래 7.2 의 FC 예시로 남긴다). r5 toy 는 ln ID 가 VGS 의 2차식·VDS 의 1차식이라 cubic-Hermite 가
**정확히** 재현하므로 격자 밖 기대값이 닫힌 식이다(같은 입력에서 옛 다선형은 다른 값을 낸다 -- 판별력).

### 7.1 [r5] r5 toy

축: `L = (1e-6, 2e-6, 3e-6)`, `VGS = (0.0, 0.5, 1.0)`, `VDS = (0.5, 1.0)`, `VS = (0.0, 0.5)`.
폭 1e-6 m 슬라이스: `ID[iL, iG, k, s] = (1e-6 / L[iL]) · 1e-7 · exp(20·VGS − 6·VGS²) · exp(0.1·VDS) · (1.0, 0.5)[s]`,
`GM = ID · (20 − 12·VGS)`, `GDS = ID · 0.1`, `VTH = 0.4`. 폭 2e-6 m 슬라이스 = 위 ID·GM·GDS × 2(같은 VTH).
닫힌 식(L = 1e-6 장): `lnID(v, d, s) = ln(1e-7) + 20v − 6v² + 0.1d + ln(0.5)·s/0.5`, `gm/ID = 20 − 12v`(4.2 정의 그대로 정확),
ln GDS 는 VGS 방향 **선형**(4.2) 이라 격자 밖 VGS 의 gds 는 닫힌 식 ln(0.1·ID) 가 아니라 이웃 마디 ln GDS 의 선형 보간이다.
두 파일 모두 `corner="tt"`, `temp_c=27.0`, `meta_json='{"model_files_sha256": {}}'`. manifest device `"toyn"`.
기준 LUT: 같은 축, `CGG_n = 1e-15`, `CGD_n = 2e-16`(상수 배열), `w_ref_m = 1e-6`, `corner`·`temp_c` 같음.
`LutSpec(1e-8, (("nmos", 1.5e-6),), (("toyn", "nmos"),), (("nmos", "_n"),))`. 폭 키 100·200.
[r4] 이 toy 는 모델 파일 기록이 없어 **빈 bin 지도**다 -- 아래 비앵커 L 행은 4.0 의 '빈 지도' 경로(`lut_l_not_anchor`, detail `bins: "unavailable"`),
tol_V 의 `l_loo` 전부 "bins_unavailable", `l_loo_bins == ()`. bin 보간·bin 거부·L 방향 LOO 를 toy 로 보려면 meta 에 `pdk_root` 와
`model_files_sha256`(그 파일의 sha256)을 적고, 그 루트 아래 `.model` 블록(`lmin`·`lmax`·`wmin`·`wmax`)을 가진 작은 모델 파일을 두면 된다(1.3·1.4).

| 호출 | 기대값(r5 toy) |
|---|---|
| `lut.slice_map[("nmos", 100)].hermite_fc` | `(("VDS", 18, 0), ("VGS", 24, 0))` |
| `widths(lut, "nmos")` | `(200,)` |
| [r2] `op_point(m, "nmos", 100, 1.5e-6, 0.5, 0.5, 0.0)` | `SealViolationError` `lut_l_not_anchor`, below 1e-6, above 2e-6. `1e-6 + 2·ulp(1e-6)` 도 같은 실패, `1e-6 + ulp(1e-6)` 은 앵커 1e-6 값 |
| [r2] `op_point(..., L=4e-6, ...)` | `lut_axis_out_of_range`, axis "L" |
| `op_point(m, "nmos", 100, 1e-6, 0.25, 0.5, 0.0)` | IDu = 1e-7·e^4.675 = 1.072326e-5, gm_over_id = 17, gds_per_w = exp(½(ln GDS(0) + ln GDS(0.5)))/1e-6 = 1e-8·e^4.3/1e-6 = 0.7369979, gm_gds = 17·exp(lnID − lnGDS) = 170·e^0.375 = 247.3485, vth 0.4. w_key 200 도 같은 값(마지막 몇 ulp 차이 허용) |
| `op_point(m, "nmos", 100, 2e-6, 0.7, 0.8, 0.3)` | IDu = ID·2e-6/1e-6 = 4.543835e-3(ID = 0.5·1e-7·e^(14 − 2.94 + 0.08)·0.5^0.6), gm_over_id = 11.6 (VDS·VS 격자 밖 -- VDS Hermite·VS 선형도 정확) |
| `vgs_for_gm_id(m, "nmos", 100, 15.0, 1e-6, 0.5, 0.0)` | 5/12 = 0.4166667 (칸 [0, 0.5], Hermite 미분 = 20 − 12v) |
| `vgs_for_gm_id(m, "nmos", 100, 11.0, 2e-6, 0.8, 0.3)` | 0.75 (칸 [0.5, 1]) |
| `vgs_for_gm_id(..., 25.0, ...)` | `SealViolationError` reason `lut_no_strong_inversion_root`, peak_vgs 0.0 |
| `gmb(m, "nmos", 100, 1e-6, 0.5, 0.5, 0.25)` | −ID·ln(0.5)/0.5, ID = 1e-7·e^8.55·√0.5 → 5.064753e-4 |
| `caps(m, "nmos", 1e-6, 0.5, 0.5, 0.0, 3e-6)` | cgg 3e-15, cgd 6e-16, cgs 2.4e-15, cgb 0.0, model `"cgg_minus_cgd_at_gs"` |
| `gm_id_for_target(m, "nmos", 100, 1e-6, 0.5, 0.0, W=2e-6, current=2·1e-7·e^4.675)` | vgs 0.25, gm_id 17, id_a = 2.144651e-5, gm_s = 17·id_a = 3.645907e-4 (`gm=3.645907e-4` 도 같은 vgs) |
| 같은 호출 `current=1.0` | `SealViolationError` reason `lut_target_out_of_range` (마디 Q 최대 = 2·1e-7·e^14.05 ≈ 0.253) |
| `op_point(..., vsb=0.6)` | `SealViolationError` `lut_axis_out_of_range`, axis "VS", lo 0.0, hi 0.5 |
| `gm_id_curve(m, "nmos", 100, 1e-6, 0.5, 0.0)` | `gm_id_vals` = (20, 14, 8), `log_id_vals − ln(1e-7)` = (0.05, 8.55, 14.05), `cell_ok` = (True, True) |
| [r5] `tol_v_table(m, "nmos", 100).cells[i][k]`(i = 0, 1, 2, k = 0, 1 모두) | id_equivalent_v = 0, gm_id_inverse_v = 0(둘 다 부동소수 수준 -- VGS 축 Hermite LOO 가 2차식을 정확히 재현, VDS·VS 축은 2점이라 내부점 없음), `*_loo_v` 도 0 수준. n_targets 2(VS 2점 × VGS 내부 목표 1개(j = 1) × VGS 축), n_inverse_failed 0. 판별: 옛 선형 LOO 였다면 id_equivalent 환산 전 = |ln ID(0.5) 의 선형 추정 − 참값|/14 = 1.5/14 = 0.107 V |
| [r5] `at(2e-6, 0.75, "id_equivalent")` / `"gm_id_inverse"` | 0 수준 / 0 수준. `at(1.5e-6, 0.75, ...)` → `lut_l_not_anchor` |
| [r5] `tol_v_table(...).loo_orders` | 5절 표의 8줄, 환산 배수 0.25·0.25·0.125·0.25·0.25·0.0625·0.0625·0.25 (지표·축 이름순) |
| `curve_report(m).rows[0]` | kind nmos, w_key 100, L 1e-6, n_curves 4, n_skipped 0, n_branch_nonmonotonic 0, gm_id_max 20, gm_gds_max 200, [r5] n_hermite_nonmonotone 0 |

[r6] 같은 r5 toy(선택 열·중점 파일 없음)의 r6 기대값:

| 호출 | 기대값(r6, r5 toy) |
|---|---|
| `lut.cap_map["nmos"].w_key` / `.columns` / `.on_mask` / `.sign_convention` / `.l_source` | 100 / 빈 매핑 / None / None / () |
| `lut.slice_map[("nmos", 100)].columns` | 빈 매핑 |
| `lut.midpoints`, `lut.provenance.midpoints_sha256` | 빈 매핑, None (지문은 r5 와 같은 6항목) |
| `vdsat(m, "nmos", 100, 1e-6, 0.5, 0.5, 0.0)` | `SealViolationError` `lut_column_unavailable`, detail column "VDSAT", kind "nmos", w_key 100, cap_w_key 100, slice_columns (), cap_columns () |
| `tol_vdsat_table(m, "nmos", 100)` | 같은 `lut_column_unavailable` |
| `midpoint_l_bin_checks(m, "nmos", 100)` | `MidpointChecks("nmos", 100, (), (), None)` |
| `caps(m, "nmos", 1e-6, 0.5, 0.5, 0.0, 3e-6)` | r5 값 + cdd None, css None |
| `gmb(...)`(7.1 행) | r5 값 그대로(GMBS 열 없음 → VS 할선) |
| `tol_v_table(m, "nmos", 100)`(l_bin_checks 생략) | r5 값 그대로, `.l_bin_checks == ()`(중점 표 없음 → midpoint 조회 없음) |
| toy 기준 LUT 에 `GMBS_n = 0.25·ID_n`, `ID_n` = 폭 1e-6 슬라이스 ID, `VDSAT_n = 0.1 + 0.2·VGS`(축 broadcast) 를 더한 경우 | `gmb(m, "nmos", 100, 1e-6, 0.25, 0.5, 0.0)` = 0.25 · ID(점), ID(점) = 1e-7·e^4.675·… 의 op_point 값(= IDu·w_m/L); `vdsat(m, "nmos", 100, 1.0e-6, 0.25, 0.75, 0.25)` = 0.15(선형 정확); `tol_vdsat_table(m, "nmos", 100).cells[i][k].vdsat_v` = 0 수준(선형 자료), origin "cap_table"; w_key 200 → `lut_column_unavailable` |

### 7.2 [r5] FC 위반 예시 = r4 toy

r4 toy: 위 7.1 과 같은 축·기준 LUT·LutSpec, 슬라이스만 `ID[iL, iG, k, s] = (1e-6 / L[iL]) · (1e-7, 1e-6, 1e-5)[iG] · (1.0, 0.5)[s]`(VDS 무관),
`GM = ID · (20, 10, 4)[iG]`, `GDS = ID / 10`(폭 2e-6 = × 2). VGS 칸 0(ln ID 차 ln10, 기울기 20·10, h 0.5)은 b1 = 3·ln10 − 15 = −8.09,
b1² = 65.5 > b0·b2 = 50 → 위반, VGS 칸 1(기울기 10·4)은 b1 = −0.092, b1² ≤ 10 → 단조. VDS 칸은 ln ID 차 0 인데 기울기 0.1 이라 위반.

| 호출 | 기대값(r4 toy) |
|---|---|
| `slice_map[("nmos", 100)].hermite_fc` | `(("VDS", 18, 18), ("VGS", 24, 12))`; `curve_report(m).rows[i].n_hermite_nonmonotone` = 10 (VGS 4 + VDS 6, 모든 행) |
| `op_point(m, "nmos", 100, 1e-6, 0.25, 0.75, 0.0)` | VGS·VDS 모두 선형 칸 → IDu = √(1e-7·1e-6) = 3.162278e-7, gm_over_id = ln10/0.5 = 4.605170(그 직선의 미분), gm_gds = 46.05170, gds_per_w 0.03162278, vth 0.4 -- 실패하지 않는다 |
| `vgs_for_gm_id(m, "nmos", 100, 15.0, 1e-6, 0.5, 0.0)` | 고른 칸 [0, 0.5] 위반 → `SealViolationError` `lut_hermite_nonmonotone_cell`, detail axis "VGS", cell_lo 0.0, cell_hi 0.5 |
| `vgs_for_gm_id(m, "nmos", 100, 7.0, 1e-6, 0.5, 0.0)` | 칸 [0.5, 1] (단조) 의 Hermite 미분 = 7 인 근 0.5834716 (2차식 근, 칸 안 t = 0.1669433) |
| `gm_id_for_target(m, "nmos", 100, 1e-6, 0.5, 0.0, W=2e-6, current=2e-6)` | 마디 Q = (2e-7, 2e-6, 2e-5) 에서 칸 j = 0 (searchsorted left − 1 → max 0) 이 위반 → `lut_hermite_nonmonotone_cell` |
| `tol_v_table(m, "nmos", 100).cells[0][0]` | id_equivalent_loo_v = |ln(1e-6) − Hermite(ln1e-7, ln1e-5, 20, 4, H = 1, t = ½)| / 10 = 0.2, id_equivalent_v = 0.2/16 = 0.0125 |

---

## 8. 범위 밖·보류

- ~~`vdsat` 대기~~ → [r6] 만들었다(4.3·5.2). `gm_id_for_vgs`: 소비처 미확정(DEC-76) → 만들지 않음.
- [r6] **VDSAT·GMBS 는 폭 키 1000(기준 LUT 폭)에서만** 있다 -- 다른 폭의 `vdsat`·`tol_vdsat_table` 은 `lut_column_unavailable`, `gmb` 는 r5
  할선. 모든 폭에서 쓰려면 슬라이스 생성기(`_drafts/engine/lut_slices/sky130_dc_width_slices.py`)가 VDSAT·GMBS 를 저장해야 한다
  (공유 생성기 변경 -- 승인 대상, 576 조합 재실행). 그러면 로더는 그대로 슬라이스 열을 쓴다(1.2). VS 축 Hermite(GMBS 기울기)도 그때.
- [r6] **앵커 2개 bin .23(0.7·1 µm)·.22(1.5·2 µm)·.21(2.5·4 µm) 은 중점이 없다**(5절 실측 missing_external). 승인 L 파일의
  `verification_midpoints_um` = (0.165, 6.0, 14.0) 중 6.0·14.0 은 앵커 1개 bin(.20 = (4, 8] 앵커 8, .19 = (8, 20] 앵커 20)에 들어
  쓰이지 않는다(그 L 은 조회 자체가 `lut_l_bin_unbracketed`). lut_regen_plan K2' 가 2점 bin 을 "[0.15, 0.18], (4, 8], (8, 20]" 으로 적은
  것은 경계값(4·8 µm)을 위 bin 으로 본 것으로 4.0.1 실측 규칙(경계 = 아래 bin)과 다르다. 바로잡으려면 중점 0.85·1.75·3.25 µm(제조 격자 위)를
  승인 L 파일에 더하고 1.7 의 생성 명령으로 다시 만든다(승인 파일 변경 -- 사용자 승인 대상, 약 6분).
- [r6] 외부 값은 bin 하나에 스칼라 하나(최댓값)라 .26 행 모든 셀의 gm_id_inverse 가 518 mV(nmos)로 덮인다(5.1 분포: p50 10.5 mV, 최댓값은
  정점 근처 평탄 목표). 셀(VDS)별 외부 값이나 목표 gm/ID 범위 제한은 계약 변경(소비자 tol 의미) -- 결정 대상.
- [r6] SVG2_1HZ·SVG2_HF·VTH(기준 LUT)·CDD·CSS 외 열: 로드만 하고(`CapTable.columns`) 조회 함수는 없다(잡음 소비처 미정).
- E3 디스크 캐시(tol_V 표·곡선 보고 지문 키): 이 단계 밖. 현재 derived memo(실행 내)만.
- toy LUT 픽스처(`tests/fixtures/toy_lut.py`, 옛 `_invq_newton`·`build_toy_lut` 복사)는 test 작성자 몫.
- 옛 `SemiEmpiricalGmIdLUT`(W_ref = 5 µm 슬라이스 배열) 대비 `op_point` 동치 test: [r5] **격자점에서만**(6절). 옛 로그 바닥(1e-18·1e-30)과
  갈리는 점(ID < 1e-18)은 비교에서 뺀다. `vgs_for_gm_id` 는 칸 선택(3절)만 옛과 비교할 수 있고 칸 안 근은 다르다. 옛 해가 정점 왼쪽인
  입력은 새 쪽이 실패해야 한다(3절).
- [r5] VS 축 Hermite(GMBS 열 -- 기울기 −GMBS/ID): GMBS 열이 LUT 재생성(Q1)에서 생기면 4.2 표의 VS 를 바꾼다. 그때까지 VS 는 선형이고
  gmb 는 VS 칸 할선(이웃 칸 경계에서 계단).
