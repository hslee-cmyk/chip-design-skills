# gmid_engine.lut 동작 계약 (MOD1, test 작성용)

> **[U17 ①-b] LUT 파생 함수**(설계 40 §2.4.6 'memo 로 옮기는 것'·§2.4.8 (a) 행, v1.9.1 D10, 2026-10-13): `derived(memo, name, *args)` -- `DERIVED_FUNCTIONS` 의 `edge_costs`(kind, w_key)
> -> `EdgeCost`(옛 metrics `edge_cost_bounds`, 영역 derived -- `DERIVED_TABLES` 에 `edge_costs` 추가), `reference_vds`(kind, w_key, L), `vds_floor`(kind, w_key) -> float(영역 derived, `DERIVED_TABLES` 맨 뒤; 카드 HC-S -- 옛 `tol_vdsat_max` 는 삭제), `param_row`(kind, w_key, L, vds, vsb)
> -> ((VGS 마디), x, y, z) | None(영역 curve)를 `memo.lookup` 으로 담는다(같은 인자 재계산 0). `memo.call` 형식 전환은 U17 ③. `EdgeCost` 는 `lut_types.py` 값 형식이다.

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
  (9) [2026-10-08 오케스트레이터 결정 A] 외부 L 값(`l_bin_checks`·`MidpointRow`)은 **셀 단위 -- (bin, VDS 격자점)마다**(5절·5.1·5.2).
  (10) [결정 B] 폭 슬라이스 32개를 GMBS·VDSAT 포함으로 재생성(기존 열 비트 동일) -- 모든 폭에서 `vdsat`·`tol_vdsat_table`·GMBS 열 `gmb`
  (4.3·4.4), VS 축 Hermite 는 보류. (11) [결정 C] 앵커 2개 bin .23·.22·.21 은 외부 값 없이 `missing_external` 로 명시(8절).
- **개정 r7(2026-10-08, 구현 단위 U3 -- 설계 40 §11 U3, 41 §4.1·§6.4-2·§6.4-2b·§7.2, 계획 DEC-87·88·96)**: 바뀐 곳에 `[r7]` 표시. 요지 --
  (1) **VS 축 Hermite**(DEC-87, GMBS 열이 있는 슬라이스): ln ID 의 VS 축도 2점 cubic-Hermite, 기울기 = −GMBS/ID(4.2·5절 LOO·1.4 로드 검사). r6 의 '보류'를 푼다.
  (2) **FC 정책**: 선형 폴백에 사유를 남긴다 -- `OpPoint.fallbacks`·`Curve.cell_class`(4.1·4.2), 기울기 열이 ln ID 격자 차분과 십진 단위로 어긋나면 로드 거부
  `lut_unit_mismatch`(1.4). (3) `vgs_for_current_density`(3.1, DEC-88 -- sizing 의 `gm_id_for_target(current=)` 우회를 대체). (4) gm/ID 축 곡선 표
  `ft_curve`·`intrinsic_gain_curve`·`vdsat_curve`·`idu_curve`(4.5). (5) **잡음**: 새 버전 파일 `..._noise_r1.npz` 로드(`noise_set`), 분해 `noise_planes`,
  `noise_params`, `tol_noise_table`(9절). (6) **mismatch**: 새 버전 파일 `..._mismatch_r1.npz` 로드, `mismatch_dvgs`, `tol_mismatch_table`, 소자 σ
  `mismatch_sigma_vgs`(10절). (7) [XRUN-F1 A로 삭제: 첫 평가 상한 배선 -- 지금은 2.2 계수 상태 memo]·`require_lut_data`(9.5·10.5). (8) 데이터 위치 설정에 `noise`·`mismatch` 항목(1.8),
  `LutSpec.noise_ef`·`LutSet.noise`·`LutSet.mismatch`·`LutProvenance` 4필드·`lut_fingerprint` 항목(1.3·1.4·1.5), 0절 층 재배치(8개 파일 추가).
- 실패 객체는 core 의 `SchemaRejectedError`(로드 거부)·`SealViolationError`(조회 실패)다. `record.detail` 은
  `{"reason": <사유 키>, ...}` 의 키 정렬 쌍 tuple 이고 `record.devices == ()`, `record.margin is None`
  (LUT 는 소자 이름을 모른다 -- 소자를 아는 호출부가 덧붙인다, P-28·P-34).

---

## 0. 파일과 진입점 (구조 규칙 A~G, `_module_map.LAYERS["lut"]`)

| 층 | 파일 | 진입점 / 종류 |
|---|---|---|
| 0 | `_helpers_bins.py` [r4] | helper: `bin_index`(bin 소속 규칙, 4.0.1) |
| 0 | `_helpers_fail.py` | helper: `schema_rejected`, `seal_violation` |
| 0 | `_helpers_interp.py` [r5, r7] | helper: `cell`, `hermite`, `hermite_root`, `linear_point`, `node_values`(축별 보간 -- [r7] VS 축 Hermite·폴백 사유 4번째 반환, 4.2), 상수 `LINEAR_CONDITIONS`·`HERMITE_CONDITIONS`·`HERMITE_DEGREE`·[r7] `REASON_SLOPE`·`REASON_FC`·`VS_SLOPE_COLUMN` |
| 0 | `_helpers_width.py` [r6] | helper: `width_key(w_m, grid_m) -> (키, 격자 위 여부)`(1.3 규칙, provenance·lut_set 공용) |
| 0 | `fingerprint.py` | `lut_fingerprint` |
| 0 | `lut_types.py` | 데이터 선언 모듈(`LutSpec`·`SliceSource`·[r4] `LBin`·`LBinMap`·`LutProvenance`·`DcSlice`·`CapTable`·`LutSet`·`OpPoint`·`Curve`·`TargetSolution`·`Caps`·`TolVCell`·`CurveRow`·`CurveReport`, [r6] `MidpointTable`·`ColumnSource`·`TolVdsatCell`·`MidpointRow`·`MidpointChecks`·`LutLocation`, 상수 `AXES`·`TOL_V_METRICS`·[r6] `TOL_VDSAT_METRICS`·`CAP_TABLE_COLUMNS`·`SLICE_OPTIONAL_COLUMNS`·`DERIVED_COLUMNS`·`COLUMN_ORIGINS`) |
| 0 | `table_cache.py` [2026-10-08] | `TableCache`(2.1) |
| 0 | `widths.py` | `widths` |
| 1 | `_helpers_columns.py` [r6] | helper: `column_source(lut, kind, w_key, column, required=True)`(열 출처, 4.3) |
| 1 | `_helpers_grids.py` [r7] | helper: `npz_grids`(npz 축 읽기)·`npz_condition_mismatch`(측정 조건 대조) -- lut_set·noise_set·mismatch_set 공용 |
| 1 | `_helpers_root.py` [r5, r7] | helper: `peak_index`, `strong_inversion_root`(곡선 묶음, 칸 안 Hermite 근 -- `hermite_root` 를 쓴다), [r7] `monotone_end`(분지에서 엄격 증가 구간 끝) |
| 1 | `axis_bounds.py` [EO-1 범위 4] | `lut_axis_bounds(memo, kind, w_key) -> ((축, 첫 값, 끝 값), ...)`(`AXES` 순서, 슬라이스 격자 끝을 읽을 뿐 값 사본·memo 없음, 없는 슬라이스 `KeyError`) |
| 1 | `axis_guard.py` | `check_axes` |
| 1 | `curve_check.py` | `curve_report` |
| 1 | `data_location.py` [r6] | `resolve_lut_location`(1.8) |
| 1 | `lut_memo.py` [2026-10-08 층 0 -> 1] | `LutMemo` (+ 상수 `REGIONS`·`DERIVED_TABLES`; `lookup_persistent` 는 `table_cache` 를 쓴다) |
| 1 | `lut_requirements.py` [r7] | `require_lut_data`(9.5·10.5) |
| 1 | `provenance.py` | `lut_provenance` |
| 2 | `_helpers_anchor.py` [r4] | helper: `l_position`(옛 `l_anchor_index` 대체 -- 앵커 또는 같은 bin 보간 위치) |
| 2 | `mismatch_set.py` [r7] | `load_mismatch_tables`(10.1) |
| 2 | `noise_set.py` [r7] | `load_noise_tables`(9.1) |
| 3 | `lut_set.py` | `load_lut_set` |
| 4 | `_helpers_loo.py` [r6] | helper: `l_interior`·`external_by_model`·`l_loo_report`·`loo_estimate`·`cell_max`·`branch_targets`·`with_external`·`opt`·`table_at`·[r7] `linear_loo_cells`, 상수 `LINEAR_ORDER`·`HERMITE_ORDER`·`HERMITE_SLOPE_ORDER`(r5 `tolerance.py` 안 함수를 옮김 -- 동작 같음) |
| 4 | `cap_query.py` | `caps` |
| 4 | `gm_id_curve.py` | `gm_id_curve` |
| 4 | `point_query.py` | `op_point` |
| 4 | `vdsat_query.py` [r6] | `vdsat`(4.3) |
| 5 | `_helpers_gmid_axis.py` [r7] | helper: `axis_curve`(gm/ID 축 곡선 표 공용, 4.5) |
| 5 | `gmb.py` [r5, r6] | `gmb`(`op_point` 를 부른다, 4.4) |
| 5 | `id_inverse.py` | `gm_id_for_target` |
| 5 | `midpoint_checks.py` [r6] | `midpoint_l_bin_checks`(5.1) |
| 5 | `mismatch_query.py` [r7] | `mismatch_dvgs`(10.2) |
| 5 | `mismatch_tolerance.py` [r7] | `tol_mismatch_table`(10.3; `TolMismatchTable` 비진입 공개 이름) |
| 5 | `noise_planes.py` [r7] | `noise_planes`(9.2; 상수 `STATUS_KNOWN`·`STATUS_NO_POINT`·`STATUS_NONPOSITIVE`) |
| 5 | `vgs_current_density.py` [r7] | `vgs_for_current_density`(3.1) |
| 5 | `vgs_root.py` | `vgs_for_gm_id` |
| 6 | `ft_curve.py` [r7] | `ft_curve`(4.5) |
| 6 | `idu_curve.py` [r7] | `idu_curve`(4.5) |
| 6 | `intrinsic_gain_curve.py` [r7] | `intrinsic_gain_curve`(4.5) |
| 6 | `mismatch_sigma.py` [r7] | `mismatch_sigma_vgs`(10.4) |
| 6 | `noise_query.py` [r7] | `noise_params`(9.3) |
| 6 | `noise_tolerance.py` [r7] | `tol_noise_table`(9.4; `TolNoiseTable` 비진입 공개 이름) |
| 6 | `tolerance.py` [r6 층 3 → 5] | `tol_v_table` (`TolVTable` 은 비진입 공개 이름, 상수 `LOO_ORDERS`) |
| 6 | `sat_threshold.py` [HC-S] | `sat_threshold`(포화 기준 정본: `SatBound(vdsat_v, tol_v, reason)`, 사유 상수 `REASON_*`; vds < 0 = `reverse_vds` 조회 0, 열 없음 = `vdsat_column_unavailable`, 축·L 밖 = `lut_domain`, tol 은 기록 전용) |
| 6 | `sat_threshold_grid.py` [HC-S] | `sat_threshold_grid`(VDSAT 격자 입구, 축 (L, VGS, VDS, VS), 열 없음 None) |
| 6 | `vdsat_curve.py` [r7] | `vdsat_curve`(4.5) |
| 6 | `vdsat_tolerance.py` [r6] | `tol_vdsat_table` (`TolVdsatTable` 비진입 공개 이름, 상수 `LOO_ORDERS`, 5.2) |

graph 밖 상태는 `LutMemo` 하나뿐이다(모듈 수준 캐시 0). 조회 함수는 모두 첫 인자로 `LutMemo` 를 받는다.
[r7] 층 번호는 `_module_map.LAYERS["lut"]` 의 위치다: `lut_set` 이 `noise_set`·`mismatch_set`(층 2)을 부르므로 한 층 뒤(3)로, 그 아래 조회 파일은 한 층씩 밀렸다.

---

## 1. 입력 파일 형식과 로드

### 1.1 `LutSpec(manufacturing_grid_m, min_finger_w_m, device_kinds, cap_column_suffix, noise_ef=())` -- frozen dataclass
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
  없는 열은 그냥 없다(로드 거부 아님 -- 열이 없는 옛 세트는 ID·GM·GDS 만 있었다. 그 옛 sample LUT 파일은 O-180 으로 삭제했다). `meta_json`(선택)의
  `sign_convention`(문자열)·`L_source`(객체) 를 표에 싣는다. LUT v2 생성기 규약: ID·GM·GDS·GMBS·VTH·VDSAT 은 BSIM op 값의 크기,
  **용량은 부호 보존**(CGG = −Im(i(vgs))/ω 게이트 여기, C_gx = +Im(i(vgs))/ω x 여기, CDD = −Im(i(vds))/ω, CSS = −Im(i(vsrc))/ω --
  CGB·CGS·CSS·CGD(pfet) 에 음수 점이 있다), SVG2_* 는 게이트 환산 잡음 V²/Hz. 엔진은 용량에 로그·절댓값을 쓰지 않는다(4.1 caps).
- [r6] 슬라이스 선택 열: `SLICE_OPTIONAL_COLUMNS` = (`GMBS`, `VDSAT`)(접미사 없음, 모양 = 슬라이스 모양, 다르면
  `lut_slice_shape_mismatch` detail `array` = 그 이름). [r6, 2026-10-08 오케스트레이터 결정 B] 슬라이스 생성기가 GMBS·VDSAT 를
  같은 .dc 에서 저장하도록 바뀌어(기존 4열 비트 동일) 저장소 설정의 슬라이스 32개 모두 두 열을 가진다. 옛 슬라이스(열 없음)도 그대로 로드된다.
- [r6] 파생 열(로드 1회): 표에 GMBS·ID 가 다 있으면 `GMBS_PER_ID` = GMBS/ID(ID > 0 인 점, 아니면 NaN)를 그 표의 `columns` 에 더한다
  (`DERIVED_COLUMNS`). 기준 LUT 표는 ID·GM 이 다 있으면 `CapTable.on_mask` = (ID > 0) & (GM > 0).

### 1.3 `lut_provenance(manifest_path, cap_npz_path, spec, *, pdk_root=None, verify_midpoints=None, noise_npz=None, mismatch_npz=None) -> LutProvenance`
- [r6] `pdk_root`: None 이 아니면 모델 파일 경로 = `os.path.join(pdk_root, 상대 경로)`(meta `pdk_root` 대신, `lut_model_root_missing`
  판정도 이 값으로). sha256 대조는 그대로라 같은 모델 파일이면 어느 폴더든 같은 결과·같은 지문.
- [LM-1e] `verify_midpoints`: 경로 **sequence**(None·빈 sequence = 없음, 문자열 하나 → `TypeError`). 파일마다 짝 슬라이스 하나(1.7)를 찾고 관문 G0~G4c를 지나면
  `SliceSource(kind, device=<짝 manifest device>, w_m, w_key, path, sha256=<파일 raw 바이트>, conditions, model_files_sha256, model_paths=())` 를 만들어
  `LutProvenance.midpoint_sources`((kind, w_key) 오름차순 tuple)에 싣는다. `midpoints_sha256` = 그 sha256 의 정렬 tuple(property, 없으면 None).
  옛 칸 `midpoints_path`·`midpoints_l_source`·`midpoints_conditions` 는 없다.
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

### 1.4 `load_lut_set(manifest_path, cap_npz_path, spec, *, pdk_root=None, verify_midpoints=None, noise_npz=None, mismatch_npz=None) -> LutSet`
- `LutSet(spec, provenance, slice_map, cap_map, fp, midpoints)`: `slice_map` = 읽기 전용 매핑 {(kind, w_key): DcSlice}, `cap_map` = {kind: CapTable},
  [LM-1e] `midpoints` = {(kind, w_key): MidpointTable}(1.7, 중점 파일을 주지 않으면 빈 매핑). `pdk_root`·`verify_midpoints` 는 1.3 으로 넘긴다.
  **D7 적재 거부**: 구성(슬라이스·중점 표·기존 거부) 뒤 `widths(lut, kind)` 슬라이스마다 앵커 2개 bin 에 그 슬라이스 자기 중점 L 이 두 앵커 사이(`_helpers_bins.
  midpoint_bracket` 결과 `(그 bin, None)`)인 것이 하나 이상이어야 한다 -- 없으면 `bin_missing_external`(detail `kind, w_key, models` = 없는 bin `.model` 정렬
  tuple), (kind, w_key) 오름차순 첫 실패. `widths` 밖 폭은 대상 밖이고 표 구성은 바뀌지 않는다. 이 원인의 런타임 None 갈래는 없다.
- [r6] `CapTable` 추가 필드: `w_key`(= `width_key(w_ref_m, grid)` 의 키, 격자 밖이면 None), `columns`(1.2 선택 열 + 파생 열, 읽기 전용
  매핑), `on_mask`, `sign_convention`(meta 문자열 또는 None), `l_source`(meta `L_source` 키 정렬 쌍 또는 ()). `DcSlice.columns` 도 같은 뜻.
- [r6 결함 수정] **`CapTable.l_bins` = 그 kind 슬라이스 중 `w_key == CapTable.w_key` 인 것의 지도**(r4·r5 는 `w_m == w_ref_m` float 비교 --
  LUT v2 는 `w_ref_m` = 5e-06 이고 슬라이스 W = 4.9999999999999996e-06 이라 빈 지도가 되어 비앵커 L 의 `caps` 가 `lut_l_not_anchor` 로
  실패했다. 옛 세트는 w_ref 를 슬라이스 ID 대조로 고르므로 float 가 같아 영향 없었다).
- `DcSlice`: `grids` = 축별 float tuple 4개, 배열은 읽기 전용 numpy. 로그 배열 `log_ID·log_GM·log_GDS` = `ln(clip(배열, 그 배열의 최소 양수값))`
  (상수 바닥 없음), `floors`·`nonpositive` 에 바닥값·0 이하 원소 수 기록, `on_mask = (ID > 0) & (GM > 0)`.
- 불변식: 모든 슬라이스의 L·VGS·VDS·VS 가 float 단위로 같다. 측정 조건(`conditions`)이 모두 같다. 기준 LUT 조건이 기록돼
  있으면 corner·temp_c 가 슬라이스와 같다. 기준 LUT L·VGS·VDS 가 슬라이스와 같다(VS 는 달라도 됨).
- **[개정 예정 -- design 40 v1.15.1 §3.7-A 5·8, card WB-1(계획 v6.38.2 DEC-105 (2))]** `w_ref_m`의 쓰임이 둘로 갈린다: (i) 용량·잡음·mismatch 열 조회 = 기준 폭 표 키(`CapTable.w_key`)와 W/w_ref_m 환산 그대로(9.3·10.4) (ii) DC 열 조회는 더 이상 기준 폭 슬라이스 하나가 아니라 소자 W-bin 슬라이스(새 순수 함수 `finger_slice`·`slice_of_finger`·`reachable_slices` -- `E/lut/finger_slice.py`); `w_ref_m`은 손가락 규칙의 w_hi(그 L에서 기준 폭 슬라이스가 속한 W-bin 위 끝)와 종속 소자 출발 키를 정하는 선언으로 쓰인다. bin 소속 판정은 제조 격자 정수 비교 + bin 경계 선언(시뮬레이터 판·호환 모드·모델 sha256) 방향으로 바뀐다(4.0.1 `_helpers_bins.bin_index` 결함 D1 정정).
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
     격자 정수로 `round(lo_b/grid) < round(hi_a/grid)` 이면(겹침, WB-1 범위 0) `lut_model_bins_overlap`(detail `path, w_m, models`).
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
  - `DcSlice.hermite_fc = (("VDS", Hermite 칸 수, 위반 칸 수), ("VGS", Hermite 칸 수, 위반 칸 수))` [r7: + 세 번째 항 `("VS", Hermite 칸 수, 위반 칸 수)` -- GMBS 열이 없으면 `("VS", 0, 0)`]. 위반이 있어도 **로드는
    거부하지 않는다**(위반 칸의 조회 규칙은 4.2, 보고는 `curve_report` 의 `n_hermite_nonmonotone`).
  - [r5 실측 2026-10-07, 생성 슬라이스 32개] 모든 슬라이스 `hermite_fc = (("VDS", 276360, 0), ("VGS", 276480, 0))`(위반 0 --
    off 격자점은 VDS = 0 열 5880개뿐). 로드 3.0 s → 5.1 s(같은 기계·같은 시각 측정, FC 검사 ≈ 1.1 s 포함).
- [r7] **VS 축 Hermite 보조(DEC-87)**: `DcSlice.vs_slope_ok` = 파생 열 `GMBS_PER_ID` 가 있고 유한·양수인 격자점(VS 기울기 d ln ID/d VS = −GMBS/ID 정의 -- GMBS 열이 없으면
  전부 거짓), `fc_ok_vs` 모양 `[nL, nVGS, nVDS, nVS − 1]`(VGS·VDS 와 같은 단조 조건, Hermite 칸이 아니면 참), `hermite_fc` 에 세 번째 항 `("VS", Hermite 칸 수, 위반 칸 수)`.
  기울기 부호 근거: 실측 `−GMBS/ID` 는 ln ID 의 VS 격자 차분과 부호·크기가 맞는다(w_key 1000, 중앙 상대차 6e-4~8e-4, p99 3e-3~5e-3).
  [r7 실측 2026-10-08, 생성 슬라이스 32개] VS Hermite 칸 nmos 7,620,480개 중 단조 위반 353(슬라이스당 최대 243), pmos 4,572,288개 중 3,934(슬라이스당 최대 1,009); 같은 32개 슬라이스에서 VDS·VGS 위반은 0. (측정: `load_lut_set` 실데이터 로드 뒤 슬라이스마다 `DcSlice.hermite_fc` 의 "VS" 항을 kind 별로 합산.)
- [r7, 2026-10-09 2차 follow-up 개정] **기울기 열 단위 검사**(41 §4.1 '단위 불일치 -> 로드 거부'): 기울기 열 **전부**(GM/ID 대 VGS, GDS/ID 대 VDS, GMBS/ID 대 VS)를 같은 규칙으로 검사한다
  (1차 구현이 GMBS 를 뺐고 임계를 한 십진 단위로 올린 것은 철회 -- GMBS×1000 이 로드되고 ×ln10 류 척도 오류가 통과해 ID 가 약 8 % 틀렸다). 임계는 고른 수가 아니라 **그 열 자신의 보간 해상도**에서 유도한다:
  격자 칸 [x0, x1] 에서 ln ID 의 현 기울기 Δln ID/Δx 는 평균값 정리로 칸 안 어떤 점의 미분이고, 칸 안에서 미분이 단조이면 두 끝 기울기 m0·m1(저장된 열, 부호 규약 적용: GM/ID·GDS/ID 는 +,
  GMBS/ID 는 −) 사이에 든다. 현이 [min(m0,m1), max(m0,m1)] 밖(부동소수 허용분 eps·(|ln ID| 두 값)/Δx + eps·(|m0| + |m1|) 밖)인 칸의 비율을 열마다 재고, 정의 마스크가 두 끝에서 참인 칸의 **과반**(칸 비율의 중앙값 판정)이
  모순이면 `lut_unit_mismatch`(detail `path, column, cells_outside, cells`). 검출 한계는 그 열의 칸 안 기울기 변화비(보간 해상도)와 같다 -- 척도 오류가 그보다 작으면 그 열을 쓰는 보간 결과가 이미 해상도 안이다.
  실데이터(LUT v2, 슬라이스 32개) 실측: 모든 슬라이스 위반 칸 비율 GM 최대 0.0213·GDS 최대 1e-4·GMBS 0.0093~0.0246(과반의 1/20 이하), 같은 데이터의 GMBS 에 ×2·×1000·×2π·×ln10 을 곱하면 0.9978~1.0, GM ×2 는 1.0, GDS ×2 는 0.983~0.992 라
  모두 거부된다(`test_unit_mismatch_rejected_gmbs`). 과반이라는 판정선 하나만 쓰고(중앙값), 십진 수·배수 상수는 없다. 이 규칙을 만족하지 않는 toy 슬라이스(GM·GMBS 가 ln ID 와 무관한 임의 값인 것)는 로드가 거부된다 --
  그 toy 의 일관성은 test 쪽에서 고친다(검사를 풀지 않는다).
- [r7] `load_lut_set(..., noise_npz=None, mismatch_npz=None)`: 선택 두 파일(9.1·10.1)을 읽어 `LutSet.noise`·`LutSet.mismatch`(둘 다 {kind: 표}, 파일이 없으면 빈 매핑)에 둔다.
  `lut_provenance` 는 두 파일의 경로·sha256 을 `LutProvenance.noise_*`·`mismatch_*` 에 싣는다(파일 없음 -> `lut_noise_missing`·`lut_mismatch_missing`).
- `fp == lut_fingerprint(provenance, ((kind, w_ref_m, basis), ...))`.
- 실패(`SchemaRejectedError`, reason): 1.3 전부 + `lut_conditions_mismatch`, `lut_slice_axes_mismatch`, `lut_slice_shape_mismatch`,
  `lut_array_no_positive`, `lut_cap_axes_mismatch`, `lut_cap_kind_undeclared`, `lut_cap_kind_without_slices`, `lut_cap_column_missing`,
  `lut_cap_width_unresolved`
  (슬라이스 1개뿐·동률·분리 조건 불충족·VS 값이 슬라이스 축에 없음·`w_ref_m`·`ID` 열 둘 다 없음),
  [r4] `lut_model_bin_incomplete`, `lut_model_bins_no_width`, `lut_model_bins_overlap`, `lut_l_anchor_outside_model_bins`.
- [JC-1] **축 키 결손**: 적재가 읽는 npz(슬라이스·기준 폭 표·중점·mismatch r1·잡음 r1)에 축 키(`L`·`VGS`·`VDS`·`VS`, L 포함) 가운데 하나라도 없으면
  그 자리 기존 축 사유(슬라이스 = `lut_slice_axes_mismatch`, 기준 폭 표 = `lut_cap_axes_mismatch`, 중점 = `lut_midpoints_axes_mismatch`,
  mismatch = `lut_mismatch_axes_mismatch`, 잡음 = `lut_noise_axes_mismatch`) + detail `{path, axis}`(axis = 없는 키 가운데 `L`·`VGS`·`VDS`·`VS`
  순서 첫 것). 첫 슬라이스(기준 축 자체)의 축 키 결손도 `lut_slice_axes_mismatch`. 축 키 판정은 helper `npz_grids(npz, *, reason, path)` 하나다 --
  받아들이던 파일(축 키가 다 있는 파일)의 결과는 바뀌지 않는다.
- [실측 2026-10-07 -- 기록, 그때 쓴 옛 sample LUT 는 O-180 으로 삭제, 생성 완료 슬라이스 32개 + 옛 기준 LUT] 로드 1.5 s, nmos·pmos 모두 w_key 1000
  (5 µm) 채택, d_w ≈ 5.0e-7, 이웃 차 0.88(nmos)·1.25(pmos).

### 1.5 `lut_fingerprint(provenance, cap_basis) -> str`
- 64자 hex = `core.fp_of` of (manifest sha256, 생성기 sha256, 슬라이스별 (kind, w_key, 파일 sha256, 조건, 모델 파일 sha256),
  기준 LUT sha256·조건, cap_basis). 파일 경로는 들어가지 않는다(같은 파일을 다른 폴더로 옮겨도 같은 지문), 어느 sha256 이든
  바뀌면 다른 지문.
- [LM-1e] 항목 tuple 은 `manifest_sha256`, `generator_sha256`, `slices`, `cap_sha256`, `cap_conditions`, `cap_basis`, `bin_rule_sha256` 7항목 뒤에, `provenance.midpoint_sources`
  가 비어 있지 않으면 `("midpoints_sha256", tuple(sorted(각 파일 raw sha256)))` 를 더한다(중점 값이 tol 표 외부 값으로 들어가므로; 경로·sequence 순서 무관, 파일 하나라도
  다르면 다른 지문). 중점이 없으면 이 항목 자체가 없다(None·() 항목 0). 뒤이어 [r7] 항목이 온다.
- [r7] `noise_sha256`·`mismatch_sha256` 이 None 이 아니면 그 순서로 `("noise_sha256", 값)`·`("mismatch_sha256", 값)` 을 더한다(없으면 r6 와 같은 지문). 표 디스크 캐시의 자료 id
  (`TableCache.data_id`)는 바뀌지 않는다(manifest·cap_npz·중점 파일만) -- 잡음·mismatch 파생 표는 함수 이름(`noise_planes` 등)과 입력 내용 지문으로 구분된다.

### 1.6 `widths(lut, kind) -> tuple[int]`
- `kind` 슬라이스 폭 키 중 `w_key · grid ≥ min_finger_w_m[kind]` 인 것의 오름차순. 근접 폭 대체·보간 없음.
- 실패: `min_finger_w_m` 에 kind 없음 → `KeyError`. 그 kind 슬라이스가 없으면 `()`.

### 1.7 [LM-1e] 검증 중점 파일 (`load_lut_set(..., verify_midpoints=경로 sequence)`)
- 형식 = **그 슬라이스 DC 슬라이스 파일과 같은 꼴**(같은 생성기 산출 -- 계획 N3.6 '그 슬라이스 앵커와 같은 생성기'): 폭 `W`(스칼라, 필수), 중점 `L`(1개 이상, m),
  `VGS`·`VDS`·`VS` 축, 필수 열 `ID`·`GM`, 선택 `VDSAT`, `corner`·`temp_c`, `meta_json`(`device`, `generator_sha256`, `model_files_sha256`, `ngspice`).
  모양 `[len(L), VGS, VDS, VS]`. 옛 기준 폭 형식(열 접미사·`w_ref_m`·meta `L_source`)은 읽지 않는다(옛 형식 파일 → G1).
- **짝 슬라이스** = 중점 meta `device` = manifest 슬라이스 **파일** meta `device` 이고 폭 키(`round(W / grid)`)가 같은 슬라이스. kind = 짝 kind.
- 관문(파일마다 위에서 아래로 첫 맞는 행, detail 에 `path`; G0~G4c = `lut_provenance`, G5~G7b = `load_lut_set`): G0 파일 없음 `lut_midpoints_missing`; G1 `W` 없음
  `lut_midpoints_width_missing`; G1b `W` 제조 격자 밖 `lut_width_off_grid`(`w_m, grid_m`); G1c `L` 원소 하나라도 제조 격자 밖(폭 관문과 같은 판정)
  `lut_midpoints_l_off_grid`(`L_m, grid_m`); G2 meta `device` 없음·짝 슬라이스 없음 `lut_midpoints_slice_unmatched`(`device, w_key`); G3 같은 (kind, w_key) 둘 이상
  `lut_slice_duplicate`(`set` = "midpoints"); G4 meta `generator_sha256` ≠ manifest 값(manifest 에 없으면 언제나)·G4b `model_files_sha256` ≠ 짝 슬라이스·G4c `ngspice` ≠ 짝 슬라이스
  `lut_conditions_mismatch`(`key`); G5 corner·temp_c ≠ 짝 슬라이스 `lut_conditions_mismatch`(`key`); G6 축 ≠ 짝 슬라이스 축(float 그대로) `lut_midpoints_axes_mismatch`;
  G7 `ID`·`GM` 없음 `lut_midpoints_column_missing`(`kind, column`); G7b 열 모양 불일치 `lut_midpoints_shape_mismatch`(`column`).
  옛 `L_source` 대조(`lut_midpoints_l_source_*`)는 없다 -- 대체 = 생성기 sha256 직접 대조 + 모델·시뮬레이터·조건 짝 대조 + 위치 선언 raw sha256 + 중점 L 제조 격자 관문(G1c).
- `MidpointTable(kind, sha256, w_m, w_key, L_points, grids, log_ID, gm_id, on_mask, VDSAT)`: (kind, w_key)마다 하나(`LutSet.midpoints[(kind, w_key)]`), `sha256` = 그 파일 raw 바이트,
  `L_points` = 파일 L 축, `grids` = (VGS, VDS, VS), `log_ID` = ln ID(ID > 0, 아니면 NaN), `gm_id` = GM/ID(같은 점, 아니면 NaN), `on_mask` = (ID > 0) & (GM > 0),
  `VDSAT` = 열 또는 None.
- 실 데이터: LM-1d 산출 `verify_midpoints_w/` 30개 파일(출처 기록 `assets/lut_v2_midpoints_w.provenance.json` `files[]`), 위치 선언 배열이 그 30행을 고정한다.

### 1.8 [r6] 데이터 위치 `resolve_lut_location(config_path, env) -> LutLocation`
- 설정 JSON: `{"root": {"env": 이름, "default": 폴더}, "pdk_root": {"env", "default"}(선택), "files": {"manifest": {"path", "sha256"},
  "cap_npz": {...}, "verify_midpoints": [{"path", "sha256"}, ...](선택, [LM-1e] 폭별 중점 파일 배열 -- 옛 단일 객체·빈 배열·같은 `path` 둘·원소 형식 오류는
  `lut_location_config_invalid` item `verify_midpoints`; 파일 없음 `lut_location_file_missing`, raw sha256 불일치 `lut_location_sha256_mismatch`; 원소의 다른 키는 읽지 않음)}}`. 다른 키는 무시. `env` = 매핑(부르는 쪽이 `os.environ` 를 넘긴다 -- 모듈은 환경을
  직접 읽지 않는다).
- root·pdk_root = `env[이름]` 이 비어 있지 않으면 그 값(`sources` 에 `"env:<이름>"`), 아니면 `default`(`"config_default"`), 둘 다 없으면
  `lut_location_config_invalid`. 경로는 `os.path.abspath`.
- 파일: `path` 는 root 기준 상대(절대 경로·`..` 조각·빈 값·sha256 없음 → `lut_location_config_invalid` detail `item, why`), 파일 없음 →
  `lut_location_file_missing`(detail `item, path`), sha256 다름 → `lut_location_sha256_mismatch`(detail `item, path, recorded, actual`).
  manifest·cap_npz 항목이 없으면 `lut_location_config_invalid`. 설정 파일 없음 → `lut_location_config_missing`, root 폴더 없음 →
  `lut_location_root_missing`, `root`·`files` 가 객체가 아님 → `lut_location_config_invalid`. 슬라이스는 여기서 재지 않는다(manifest 가
  고정하고 `load_lut_set` 이 대조).
- `LutLocation(config_path, root, manifest_path, cap_npz_path, midpoints_paths, pdk_root, sources, noise_path, mismatch_path, bin_rule_path)`, `midpoints_paths` =
  절대 경로 tuple(`path` 오름차순, 없으면 `()`), `sources` = ((항목, 출처), ...) 항목 정렬.
- [r7] 선택 항목 `files.noise`·`files.mismatch`(같은 `path`·`sha256` 형식, root 기준 상대 경로): `LutLocation.noise_path`·`mismatch_path`(없으면 None). 호출:
  `load_lut_set(loc.manifest_path, loc.cap_npz_path, spec, pdk_root=loc.pdk_root, verify_midpoints=loc.midpoints_paths, noise_npz=loc.noise_path, mismatch_npz=loc.mismatch_path)`.
  새 파일은 공유 데이터 폴더의 **새 버전 파일**이다(기존 r2 파일은 고치지 않는다) -- 이 브랜치의 설정만 가리킨다.
- 저장소 설정: `skills/analog-gmid-design/assets/lut_v2_location.json` -- root 기본 `C:/Users/HSLEE/Documents/Todoc/fpga/lut_data/sky130_lut_v2`
  (git 밖, `GMID_LUT_V2_ROOT` 로 덮어씀), pdk_root 기본 `C:/pdk/sky130_fd_pr`(`GMID_PDK_ROOT`), 세 파일 sha256 고정. 쓰는 법:
  `loc = resolve_lut_location(<설정>, os.environ)` → `load_lut_set(loc.manifest_path, loc.cap_npz_path, spec, pdk_root=loc.pdk_root,
  verify_midpoints=loc.midpoints_paths)`.
- **test 기본 경로 전환(O-180 으로 완료)**: test 는 LUT 를 위 설정의 `resolve_lut_location` 결과로만 읽고 `load_lut_set` 에 `pdk_root`·
  `verify_midpoints` 를 넘긴다. LUT 를 가리키는 환경 덮어쓰기(`GMID_LUT_MANIFEST`·`GMID_LUT_CAP_NPZ` 등)는 없다 -- 허용 env 는
  설정 파일이 선언한 것(데이터 루트·캐시 폴더)뿐이고 루트 env 로 다른 폴더를 줘도 sha256 이 같은 파일만 받는다
  (`tests/lut/test_lut_single_source.py` 가 지킨다). 옛 세트 기대값(12 앵커 bin 상태, VS 상한 0.8 V, `cgg_minus_cgd_at_gs` 모델 등)을
  쓰는 test 는 v2 값(18 앵커, VS 0~1.8, `lut_cgs_cgb`)으로 다시 써야 한다.

---

## 2. memo `LutMemo(lut, *, point, curve, root)`

- 상한 인자: 1 이상 int(아니면 core `BoundedLRU` 의 `ValueError`). 예외: `LutMemo.counting` memo 를 고정할 때 창 안에서 한 번도 안 쓴 영역의 상한은 0 = 그 영역은 memo 하지 않는다(2.2). `derived` 영역 상한 = `len(lut.slice_map) * len(DERIVED_TABLES)`.
- `LutMemo.counting(lut, n_theta, *, table_cache=None)`: 계수 상태 memo(2.2). 영역 r ∈ {point, curve, root} 상한 = `(n_theta + 1) * U_r`(U_r = 창 안 서로 다른 키 수), 고정은 `fix_bound()`.
- `lookup(region, fn_name, key, compute)`: 키 = `(lut.fp, fn_name) + tuple(key)`. 적중이면 저장 값 그대로(`is`), 아니면 compute 1회.
  가변 원소가 든 키 → `TypeError`. 알 수 없는 region → `KeyError`.
- `stats()` → `(("curve", LruStats), ("derived", ...), ("point", ...), ("root", ...))`.
- 조회 함수별 영역: `op_point`·`gmb`·`caps`·[r6] `vdsat` = point, `gm_id_curve` = curve, `vgs_for_gm_id`·`gm_id_for_target` = root,
  `tol_v_table`·`curve_report`·[r6] `tol_vdsat_table`·`midpoint_l_bin_checks` = derived. [r6] `DERIVED_TABLES` =
  ("curve_report", "midpoint_l_bin_checks", "tol_v_table", "tol_vdsat_table") -- derived 상한 = 슬라이스 수 × 4(r5 는 × 2).
  [r7] `DERIVED_TABLES` = ("curve_report", "midpoint_l_bin_checks", "noise_planes", "tol_mismatch_table", "tol_noise_table", "tol_v_table", "tol_vdsat_table") --
  derived 상한 = 슬라이스 수 × 7. 영역: `noise_params`·`mismatch_dvgs`·`mismatch_sigma_vgs` = point, gm/ID 축 곡선 표 4개 = curve, `vgs_for_current_density` = root,
  `noise_planes`·`tol_noise_table`·`tol_mismatch_table` = derived(디스크 캐시 대상, `lookup_persistent`).
  `tol_v_table`·`tol_vdsat_table` 을 `l_bin_checks=None` 으로 부르면 LutSet 에 중점 표가 있을 때만 `midpoint_l_bin_checks` 를 먼저
  부른다(derived misses +1, 두 번째부터 hits) -- 중점 표가 없으면 그 조회를 하지 않는다(r5 와 같은 misses 수).
  [r6] `gmb` 의 compute 는 GMBS 열이 있으면 `op_point` 1회(조회점), 없으면 3회(r5). 같은 인자 두 번 → 두 번째는 compute 0(그 영역 hits +1). 실패한 조회는 저장되지 않는다.
  [r5] `gmb` 의 compute 는 같은 (L, vgs, vds) 의 `op_point` 3회(VS 칸 양끝·조회점, point 영역)를 부른다 -- 첫 `gmb` 호출은 point
  영역 misses 가 gmb 1 + op_point ≤ 3 늘어난다(이미 있던 op_point 키는 hits).
- 같은 내용의 LutSet 두 개(같은 파일, 다른 폴더)는 같은 `fp` 라 같은 키가 된다.

### 2.2 계수 상태 memo `LutMemo.counting(lut, n_theta, *, table_cache=None)`·`open_count()`·`fix_bound()`·`bound_state` (설계 40 §2.4.6 '첫 평가 버림 제거'; XRUN-F1 card A)
- `counting` 이 만든 memo 는 `bound_state == "counting"` 으로 시작한다: 영역 point·curve·root 는 상한 없이 값을 모은다(같은 키는 한 번만 계산, 마지막 접근 순서 유지). `derived` 영역은 처음부터 상한 LRU(계수 대상 아님).
  `table_cache=None` = `TableCache.default()`(생성자와 같은 뜻).
- U_r = `open_count()` 부터 `fix_bound()` 까지(그 실행의 **첫 커널 평가**) 조회한 서로 다른 키 수(영역 point·curve·root 마다). 창 열기 전 조회는 값을 모으되 U 에 세지 않는다. 창 안 조회가 창 전에 모은 키를
  다시 부르면(적중) 그 키도 U 에 든다. '서로 다름' = core `BoundedLRU` 와 같은 `canonical_key`(0.0 ≠ −0.0, 같은 내용 NaN 은 같은 키, 1·1.0·True 는 서로 다른 키). 창 안에서 `compute()` 가 예외로 끝난 조회는 U 에 넣지 않는다(`misses` 에는 센다).
- 상태 전이는 한 방향: `"counting"` --`open_count()`--> `"window_open"` --`fix_bound()`--> `"fixed"`. 그 밖의 호출(창 없이 `fix_bound`, 두 번째 `open_count`, `"fixed"` 에서 두 메서드)은 `ValueError`.
  `LutMemo(...)` 생성자 memo 는 처음부터 `"fixed"`(두 메서드 `ValueError`). `bound_state` 는 읽기 전용 속성.
- `fix_bound()`: 영역 r 상한 = `(n_theta + 1)·U_r`. 모은 항목을 오래된 것부터 `BoundedLRU.adopt`(원 key, hits·misses 불변)로 새 상한 LRU 에 옮긴다 -- 모은 항목이 상한보다 많으면 가장 오래 접근하지 않은 것부터 퇴출(`evictions` 에 든다).
  **U_r = 0 이면 그 영역 상한 0 = memo 하지 않음**(오류 아님): `lookup` 은 저장 없이 매번 `compute()` 를 부르고 `stats()` 의 그 영역은 `capacity 0, size 0, hits = 계수 상태 hits, misses = 계수 상태 misses + 이후 조회 수`.
  이 영역을 이후 평가가 쓰면 값은 맞고(같은 compute) 느릴 뿐이다(`_Unmemoized` 제거는 U17 ③). `LutMemo(...)` 직접 생성자의 0 은 여전히 `ValueError`.
- `stats()`: 계수 상태(`"counting"`·`"window_open"`)의 point·curve·root = `LruStats(capacity=None, size=모은 항목 수, hits, misses, evictions=0, recomputes_after_eviction=0)`. 고정 뒤 = `BoundedLRU` 계수(capacity·size·evictions·recomputes_after_eviction)에
  계수 상태 동안의 hits·misses 를 더한 값. 옮기기는 hits·misses 를 바꾸지 않는다(고정 직후 같은 원 key 조회는 hit).
- 값: memo 는 값을 바꾸지 않는다 -- 같은 인자의 조회 값은 계수 상태·고정 뒤·생성자 memo 에서 같다. 모든 조회는 `LutMemo.lookup` 을 거친다(고정의 항목 옮기기는 `LutMemo.lookup` 을 부르지 않는다).
- **소비처**: search `build_search_context`(`search_context.py::_wire_sweep_memo`)가 S0 당 1회 `counting` memo 를 설치한다(n_θ = `layer0_center.centre_start` 의 `variables` 수; 커널 평가 0, 임시 컨텍스트 없음).
  `kernel.evaluate` 가 그 컨텍스트의 첫 커널 평가에서 커널 호출 직전 `open_count()`, 결과를 만든 직후 `fix_bound()` 를 부른다. 결과 memo 가 `dc_ctx.lut`(`LutAccess`)의 memo 를 바꾼다 -- 호출자가 넘긴 memo 는 domain 등 S0 준비 조회에만 쓰이고
  그 상한 상수는 탐색에 영향이 없다. 첫 커널 평가가 없는 실행은 고정하지 않은 채 끝난다(`perf.lut_memo_bound == "unfixed_no_kernel_eval"`).

### 2.1 [2026-10-08, 사용자 승인 "tol_V표를 파일로 캐시해"] 파생 표 디스크 캐시 `TableCache` (`table_cache.py`, 층 0) + `LutMemo.lookup_persistent`

- 동기(실측): `tol_v_table` 첫 계산이 슬라이스당 CPU 11~19 s(`_inverse_cell` -> `strong_inversion_root` -> `hermite_root`), 프로세스마다
  다시 만들었다(검색 실행·pytest 프로세스·agent 측정). 같은 이유로 `curve_report`(전 슬라이스 7.7 s)·`tol_vdsat_table`(0.2~0.3 s)도 대상이다.
  `midpoint_l_bin_checks`·`op_point` 등은 비싸지 않아 대상이 아니다(실측 0.0 s).
- `LutMemo(lut, *, point, curve, root, table_cache=None)`: `table_cache=None` -> `TableCache.default()`(저장소 설정 + `os.environ`),
  끄려면 `TableCache(None)`. `memo.table_cache` 로 읽는다. 메모리 memo(`lookup`, 상한 BoundedLRU, 2절)는 그대로다.
- `LutMemo.lookup_persistent(region, fn_name, key, compute, inputs, settings=())`: `lookup` 과 같은 키·반환(메모리 적중이면 디스크를 안
  건드림). memo 에 없을 때 `compute` 대신 `table_cache.fetch(lut.fp, TableCache.data_id(lut.provenance), fn_name, key, inputs, settings, compute)` 를 부른다. 쓰는 곳:
  `tol_v_table`(inputs = 슬라이스 `DcSlice` 전체), `tol_vdsat_table`(inputs = `ColumnSource`), `curve_report`(inputs = 정렬된 전 슬라이스).
  결과는 디스크를 거치든 아니든 **비트 동일**하다(float 은 pickle 이 정확한 8바이트로 보존).
- 위치: `assets/lut_v2_location.json` 의 `"table_cache": {"env": "GMID_LUT_TABLE_CACHE_DIR", "default": <전용 폴더>}`(lut_data·저장소 밖).
  환경 변수가 비어 있지 않으면 그 값. 폴더가 없으면 만들고, 못 만들면 캐시를 끈다(RuntimeWarning + 이벤트 "disabled", 계산은 그대로).
  설정 파일·`table_cache` 항목이 없으면 꺼짐. `TableCache.from_config(config_path, env)` 는 `os.environ` 를 읽지 않는다(1.8 과 같은 규칙).
- 키 `key_digest` = sha256(코드 버전, 입력 지문, 설정 지문): 코드 버전 = lut·core 패키지 `.py` 소스 바이트 전부 + numpy·python 버전, 입력 지문
  = `inputs` 의 배열(dtype·shape·바이트)·dataclass 필드·tuple·Mapping 내용, 설정 지문 = `fp_of((lut.fp, fn_name, key, settings))`
  (`settings` = 결과에 영향을 주는 상수: tol_V `(LOO_ORDERS, TOL_V_METRICS, AXES)`, tol_VDsat `(LOO_ORDERS, TOL_VDSAT_METRICS, AXES)`).
  구성요소 하나라도 다르면 적중하지 않고 다시 계산해 **같은 칸**을 덮어쓴다. 칸 파일 이름 = `<fn_name>-<자료 id>-<fp_of((lut.fp, fn_name, key))>.tbl`
  (자료 id·지문은 64자 소문자 hex). **자료 id** = `fp_of((manifest sha256, cap_npz sha256, verify_midpoints raw sha256 의 정렬 tuple 또는 None))` -- 설정 파일
  `files` 가 고정하는 값이라 `TableCache.data_id(lut.provenance)` 와 설정 파일만으로 같은 값이 나온다(표를 열지 않음). `fetch(lut_fp, data_id, fn_name,
  key, inputs, settings, compute)`.
- **정리(cleanup, 2026-10-08 사용자 허용 "캐시 정리 삭제 코드 넣는 것을 허용해")**: `TableCache.from_config`(설정 경로를 아는 객체)만, 그 객체의 **첫 쓰기
  성공 직후 1회**(읽기·hit·두 번째 쓰기에선 안 함). 남기는 집합 = `git rev-parse --show-toplevel` 기준 설정 파일 상대 경로를 `git worktree list --porcelain`
  의 모든 worktree(본 작업 폴더 포함) 아래에서 읽은 자료 id + 이 객체의 설정이 가리키는 id (설정이 없거나 manifest·cap_npz 항목이 없는 worktree 는 id 없음).
  폴더 직하의 `<함수>-<64hex>-<64hex>.tbl` 파일 중 자료 id 가 집합에 **없는** 것만 `os.unlink`; 방금 쓴 파일·심볼릭 링크·일반 파일이 아닌 것·하위
  폴더·형식이 다른 이름·폴더 밖은 건드리지 않는다. 지우면 이벤트 `cleanup_removed`(함수 이름), 지울 수 없으면(OSError, 사용 중) `cleanup_skipped`.
  git 실행 실패·worktree 나열 실패·설정 JSON 읽기 실패(ValueError/OSError)·폴더 나열 실패면 아무것도 지우지 않고 `cleanup_failsafe`. 나이·개수 상한 없음.
  `TableCache(directory)`(설정 경로 없음)는 정리하지 않는다.
- 파일: `GMIDTBL1\n` + 키(64 hex) + `\n` + 본문 sha256(64 hex) + `\n` + pickle 본문. 읽기 검증: 머리 형식(MAGIC·구분자·길이, **키 칸이 64자 소문자 hex
  가 아니면 형식 위반**)·본문 해시 -> 깨짐(이벤트 "corrupt" + RuntimeWarning), 형식은 맞고 값만 다른 키 -> "stale_key"(경고 없음), 역직렬화 실패 -> "corrupt". 어느 경우도 예외를 내지 않고 `compute()` 로 만들어
  덮어쓴다. 키가 다른 표를 조용히 쓰는 경로는 없다.
- 쓰기: 같은 폴더 임시 파일(`tempfile.mkstemp`) -> write·flush·fsync -> `os.replace`. 읽는 쪽은 옛 완성 파일 또는 새 완성 파일만 본다(부분 파일
  없음). 동시 시작한 여러 프로세스가 같은 표를 각자 계산해 서로 덮어써도 된다(내용 같음). 교체 실패(잠김)·디스크 오류는 "write_error" 로 기록하고 계산
  결과를 그대로 돌려준다. 결과에 ndarray 가 들어 있으면 저장하지 않는다("unstorable").
- **Windows 경로 길이**: 칸 파일 이름이 ~150자(+ 임시 접미사)라 폴더 경로가 ~97자를 넘으면 MAX_PATH(260) 때문에 쓰기가 실패한다. 그래서 Windows(`sys.platform` 이 `win` 으로 시작)에서는
  캐시 폴더 안의 모든 파일 작업(폴더 만들기·나열·읽기·임시 파일 쓰기·교체·삭제)을 확장 길이 경로(절대 경로 앞에 `\\?\`, UNC 는 `\\?\UNC\`)로 한다.
  파일 이름은 바뀌지 않는다(정리가 이름을 읽는다). `path_of` 가 돌려주는 경로는 보통 표기다. 그래도 쓰기가 실패하면 RuntimeWarning 에 경로 길이와
  "MAX_PATH 한도 초과가 원인일 수 있다"를 적고 `write_error` 이벤트를 남긴다(계산 결과는 그대로).
- 관찰: `table_cache.stats()` = ((이벤트, 횟수), ...) 이름 정렬, `table_cache.events` = ((이벤트, 함수 이름), ...) 발생 순서.
  이벤트: hit·miss·stale_key·corrupt·read_error·write·write_error·unstorable·disabled·cleanup_removed·cleanup_skipped·cleanup_failsafe.
- test 작성자용 불변식(기대값은 test 가 정한다): (1) 구성요소별 적중/미스 -- 같은 키 두 번째 `fetch` 는 hit·compute 0회; LUT 자료 한 원소·
  `settings`·호출 인자 `key`·코드 버전(소스 바이트) 중 하나를 바꾸면 compute 1회 + 덮어쓰기. (2) 깨짐 -- 파일 중간 잘림·본문 바이트 변조·머리 변조·
  빈 파일·쓰레기 파일 모두 예외 없이 다시 계산 + 깨끗한 파일로 교체, corrupt 이벤트. (3) 원자성 -- 쓰는 도중에도 목적 경로엔 완성 파일 또는 이전
  파일만 있고, 쓰기 실패 뒤 임시 파일이 남지 않으며, 읽기 실패는 계산 결과를 바꾸지 않는다. (4) 비트 동일 -- 모든 (kind, w_key) 의
  `tol_v_table`·`tol_vdsat_table` 과 `curve_report` 가 캐시 끔/켬/적중에서 속성 전부 같고 float 바이트 같다. (5) 환경 변수 -- `from_config` 가
  `env` 매핑의 값을 설정 default 보다 우선하고, 빈 값이면 default, 폴더가 없으면 만든다, 만들 수 없으면 끄고 계산한다. (6) 격리 -- `TableCache(None)`
  이면 파일 입출력 0. (7) memo 불변 -- 같은 `LutMemo` 안에서 같은 인자는 디스크도 안 건드리고(memo hit) `lookup` 과 같은 상한·통계. (8) 정리 -- 임시
  git 저장소 + `git worktree add` 로 만든 worktree 들의 설정이 서로 다른 자료 id 를 가리킬 때: 가리켜진 id(본 저장소·각 worktree)의 파일은 남고 가리켜지지
  않은 id 의 형식 맞는 파일만 지워진다; 방금 쓴 파일은 id 가 어느 설정에도 없어도 남는다; 하위 폴더·형식 다른 이름·심볼릭 링크·폴더 밖 파일 불변; 첫
  쓰기에서만 실행(같은 객체 두 번째 쓰기·읽기 hit 에선 안 지움, 새 객체는 다시 실행); 삭제가 OSError 면 `cleanup_skipped` 이고 예외 없음; git 저장소 밖 설정·worktree
  설정 JSON 이 깨짐이면 `cleanup_failsafe` 이고 삭제 0; `TableCache(directory)` 는 삭제 0. 전부 `GMID_LUT_TABLE_CACHE_DIR` 같은 임시 폴더에서만 검증한다.

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

### 3.1 [r7] `vgs_for_current_density(memo, kind, w_key, ln_idu, L, vds, vsb) -> float V` (`vgs_current_density.py`; 계획 DEC-88, 설계 40 §2.3)
- 쓰기 소자의 독립 좌표 ln IDu(IDu = ID·L/w_m)에서 VGS 크기를 강반전 분지 위에서 역산한다. 곡선 = `gm_id_curve`(op_point 와 같은 곡면). 목표 ln ID = ln IDu + ln w_m − ln L(L = 앵커 값 또는
  같은 bin 보간 L). 정점 index p 부터 마디 ln ID 가 엄격히 증가하는 첫 구간 [p, e] 안이면(양끝은 exp·log 왕복 반올림 2 ulp 허용) 칸 j = p + max(searchsorted(왼쪽) − 1, 0) 을 고르고,
  j = e 면 VGS[e], 아니면 칸의 VGS Hermite(값 ln ID, 기울기 gm/ID)에서 `hermite_root` 로 `value − 목표 = 0` 을 푼다. 그래서 결과 VGS 의 `op_point(...).IDu` 는 입력과 부동소수 분해능 안에서 같다.
- 실패(`SealViolationError`, detail `kind, w_key, quantity = "ln_idu", target = 목표 ln ID, ln_idu, L, vds, vsb, branch_min, branch_max, monotone_lo, monotone_hi`): 곡선에 NaN 마디
  `lut_curve_undefined`, 목표가 분지 ln ID 범위 밖 `lut_target_out_of_range`, 범위 안이나 단조 구간 밖 `lut_target_non_monotonic`, 고른 칸 단조 위반 `lut_hermite_nonmonotone_cell`(+ `axis, cell_lo, cell_hi`).
- **대체**: sizing 이 같은 양을 `gm_id_for_target(W = w_m, current = IDu·w_m/L)` 로 푸는 임시 우회 두 곳(`block_columns._vgs_of_coordinate`·`_vgs_signed`)을 이 함수로 바꿨다(같은 커밋). 정점 마디 좌표처럼 분지 끝에 놓인
  입력에서 옛 우회는 반올림으로 `lut_target_out_of_range`(소비자는 −inf 로 취급)가 나던 곳을 이 함수는 끝 마디 VGS 로 돌려준다. 실측(실데이터 w_key 1000, 무작위 3000점×2 kind(seed 20261008, 좌표 = 곡선 IDu 마디 + 0~0.5 의 로그 오프셋): 둘 다 성공한 점에서 옛 우회와 VGS 차 최대 nmos 5.1e-15 V·pmos 3.1e-15 V, `op_point(결과).IDu` 왕복 |Δln IDu| 최대 2.1e-14; 옛 우회만 실패한 점 nmos 19·pmos 12(분지 끝 마디 반올림), 새 함수만 실패한 점 0).
- 소비자 호출 규약: `lut_target_out_of_range` 의 `target`·`branch_max` 는 같은 단위(ln ID)라 `target > branch_max` 가 '필요한 VGS 가 격자 위'다.

---

## 4. 조회 API

공통: 축 이름 `AXES = ("L", "VGS", "VDS", "VS")`, L 은 m, 전압은 V(VS = vsb 크기). 입력 숫자는 `float()` 로 바꿔 쓴다.

### 4.0 [r4 전면 교체] L = 앵커 또는 같은 모델 bin 안 보간 (사용자 결정 2026-10-07)
적용 경로: op_point·gm_id_curve·vgs_for_gm_id·gm_id_for_target·gmb·caps·TolVTable.at(모두 같은 판정 `l_position`). 판정 순서:
1. **앵커**(r2/r3 그대로): 조회 L 의 제조 격자 정수 `round(L/grid)` 가 L 축 앵커 a 의 `round(a/grid)` 와 같으면 그 앵커(WB-1 범위 0: `l_position(l_grid, l_bins, L, grid_m, rule, context)`, float 근접 허용폭 없음). 이 검사가 범위 검사보다 **먼저**다(대칭 --
   격자 양끝 앵커도 바깥쪽 같은 격자 정수까지 받는다). L 값으로 앵커 값 a 를 쓰고(`IDu = ID·a/w_m`,
   `id_a = IDu·W/a`), 결과는 r2 앵커 조회와 **비트 단위로 같다**(L 격자 = (a,) 한 장, L 가중치 (1, 0)).
2. 범위: 앵커의 격자 정수 밖으로 L 격자 밖(NaN 포함) → `lut_axis_out_of_range`(axis "L", 4.1).
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
- **현행(WB-1 범위 0, DEC-105 (2))**: 구간 끝과 x 를 제조 격자 정수 `round(값/grid_m)` 로 바꿔 정수끼리 닫힌 구간으로 비교한다(`bin_index(intervals, x, grid_m, rule)`, float 근접 허용폭 없음). 두 구간이 품으면 LUT 세트의 bin 선언(`LutSet.bin_rule`, 위치 설정 `bin_rule` 키 -> `LutLocation.bin_rule_path` -> `load_lut_set(..., bin_rule=)` 필수)의 `rule` 이 고른다: `"lower"` = 앞(lo 가 작은) 구간, `"upper"` = 뒤 구간. 세트(슬라이스·cap·noise·mismatch)의 모델 파일 sha256 묶음·시뮬레이터 판이 선언 밖이면 `bin_tie_undeclared`(detail `set`, `why`), `lut_fingerprint` 에 `bin_rule_sha256`(선언 LF 환산 sha256)이 들어간다. 아래 "아래 구간 우선" 문단은 선언 `rule = lower` 일 때의 규칙이고 실측은 그 선언의 출처 사례다.
- **예정(2026-10-16, oracle-portability 계획 D-4 승인)**: 경계 규칙의 정본은 card OP-7에서 'LUT 생성 실행에 묶은 bin 규칙 선언(모델 파일 sha256 묶음 + 생성 시뮬레이터 판)'으로 옮긴다(design oracle-portability §16). 그때까지 아래 규칙과 실측 문단이 현행이다. 아래 실측은 그 선언의 출처 사례로 남는다.
- 값 x 는 `lo ≤ x ≤ hi` 인 구간에 든다(**양끝 닫힘**). 경계를 공유한 두 구간이 다 품으면 **lo 가 작은(아래) 구간**이 이긴다.
  그래서 경계값 L = b 는 `lmax = b` 인 아래 bin 이다 -- 사실상 `lmin < L ≤ lmax`(맨 아래 bin 만 `lmin` 포함). W 도 같다(W = wmax 인 아래 W bin).
  경계 비교는 격자 정수 비교다(LUT L 은 `µm × 1e-6` 곱이라 경계와 1 ulp 어긋날 수 있으나 같은 정수다. 예: 슬라이스 W
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
| `op_point(memo, kind, w_key, L, vgs, vds, vsb)` | `OpPoint` | [r5] 4.0 의 L 장에서 4.2 의 축별 보간 1회: `IDu = exp(lnID)·L/w_m`, `gm_over_id` = lnID 의 VGS 미분(4.2), `gm_gds = gm_over_id · exp(lnID − lnGDS)`, `gds_per_w = exp(lnGDS)/w_m`(lnGDS 모든 축 선형), `vth`(모든 축 선형). 단조 위반 칸은 그 축 선형으로 보간하고 실패하지 않는다. [r7] **선형 폴백은 조용하지 않다**: Hermite 가 가능한 칸(VGS·VDS·VS 가 격자점 사이)인데 선형으로 간 축은 `OpPoint.fallbacks` = ((축, 사유), ...) 정렬 tuple 에 남는다(사유 `slope_undefined`·`fc_violation`, 없으면 ()) |
| `gm_id_curve(memo, kind, w_key, L, vds, vsb)` | `Curve` | [r7] `Curve.cell_class`[j] = 칸 분류(41 §4.1): `hermite`(단조 -- 역산 허용)·`fc_violation`(격자 전수만, 역산 거부 `lut_hermite_nonmonotone_cell`)·`slope_undefined`(끝 기울기 없음 -- 선형 칸). [r5] 4.0 의 L 장, VGS 격자 **마디마다** 4.2 의 마디 값: `log_id_vals` = V_a, `id_vals = exp(V_a)`(폭 w_m 의 A), `gm_id_vals` = S_a(정의 안 되면 NaN), `cell_ok`(길이 nVGS − 1) = 4.2 의 VGS 칸 단조 조건. `vgs_grid` 는 슬라이스 VGS 축. 배열 읽기 전용. 마디 사이 곡선은 그 칸의 VGS Hermite(op_point 와 같은 곡면). VGS 축 검사는 없다(격자 전체) |
| `vgs_for_gm_id(memo, kind, w_key, gm_id, L, vds, vsb)` | float V | [r5] 3절 규칙(칸 선택 + 칸 안 Hermite 미분 근). 실패(`SealViolationError`): 곡선에 NaN 마디 → `lut_curve_undefined`(detail `gm_id, L, vds, vsb, kind, w_key, n_undefined`), 해 없음 → `lut_no_strong_inversion_root`(detail `gm_id, L, vds, vsb, kind, w_key, branch_gm_id_min, branch_gm_id_max, peak_vgs`), 고른 칸 `cell_ok` 거짓 → `lut_hermite_nonmonotone_cell`(detail `gm_id, L, vds, vsb, kind, w_key, axis "VGS", cell_lo, cell_hi` -- 칸 양끝 VGS) |
| `gm_id_for_target(memo, kind, w_key, L, vds, vsb, *, W, gm=None, current=None)` | `TargetSolution(vgs, gm_id, id_a, gm_s)` | Q = `id_vals·W/w_m`(current) 또는 `id_vals·gm_id_vals·W/w_m`(gm) -- 마디 값. 분지 index p 부터 마디 Q 가 엄격히 증가하는 첫 구간 [p, e] 에서 칸 j = p + max(searchsorted(Q[p..e], 목표, left) − 1, 0). j = e 면 vgs = VGS[e], 아니면 [r5] 칸 [j, j+1] 의 VGS Hermite 로 ln Q(vgs) = ln 목표를 `hermite_root` 로 푼다(current: ln Q = p(v) + ln(W/w_m), gm: ln Q = p(v) + ln p'(v) + ln(W/w_m)). 그 vgs 의 `op_point` 로 `gm_id`, `id_a = IDu·W/L`, `gm_s = gm_id·id_a`. 목표가 Q[p]..Q[e] 밖이고 분지 Q 범위 밖 → reason `lut_target_out_of_range`, 범위 안이지만 단조 구간 밖에서만 닿음 → `lut_target_non_monotonic`(detail `quantity, target, W, L, vds, vsb, kind, w_key, branch_min, branch_max, monotone_lo, monotone_hi`). [r5] NaN 마디 → `lut_curve_undefined`(detail `quantity, target, W, L, vds, vsb, kind, w_key, n_undefined`), 칸 j(j < e) 의 `cell_ok` 거짓 → `lut_hermite_nonmonotone_cell`(앞 detail + `axis "VGS", cell_lo, cell_hi`). `gm`·`current` 둘 다/둘 다 없음, `W ≤ 0` → `ValueError` |
| `vdsat(memo, kind, w_key, L, vgs, vds, vsb)` [r6] | float V | 4.3 |
| [r7] `ft_curve`·`intrinsic_gain_curve`·`vdsat_curve`·`idu_curve` `(memo, kind, w_key, L, vds, vsb)` | `GmIdAxisCurve` | 4.5 |
| [r7] `vgs_for_current_density(memo, kind, w_key, ln_idu, L, vds, vsb)` | float V | 3.1 |
| [r7] `noise_params(memo, kind, w_key, L, vgs, vds, vsb)` | `NoiseParams` | 9.3 |
| [r7] `mismatch_dvgs(memo, kind, w_key, L, vgs, vds, vsb)` | `MismatchSens` | 10.2 |
| `tol_vdsat_table(memo, kind, w_key, l_bin_checks=None)` [r6] | `TolVdsatTable` | 5.2 |
| `midpoint_l_bin_checks(memo, kind, w_key)` [r6] | `MidpointChecks` | 5.1 |
| `gmb(memo, kind, w_key, L, vgs, vds, vsb)` | float A/V(폭 w_m) | [r6] GMBS 열이 있으면 4.4 의 열 정의(정본). 없으면 아래 r5 정의. [r5] VS 칸 k = `min(bisect_right(VS, vsb) − 1, len(VS) − 2)`(VS 는 선형 축이라 칸 안 ln ID 가 vsb 에 선형), `gmb = −ID(점) · (ln IDu(VS[k+1]) − ln IDu(VS[k])) / (VS[k+1] − VS[k])`, 세 값 모두 같은 (L, vgs, vds) 의 `op_point`(ID(점) = IDu·w_m/L). 소자 폭 W 값 = `× W / w_m`(부르는 쪽) |
| `caps(memo, kind, L, vgs, vds, vsb, W)` | `Caps(cgg, cgd, cgs, cgb, model)` F | [r4] 4.0 의 L 장(bin 지도 = `CapTable.l_bins`)에서 기준 LUT 열 (L, VGS, VDS, VS) 모든 축 선형 보간([r5] `linear_point`, 4.2 표) × `W / w_ref_m`. CGS·CGB 열이 있으면 `model = "lut_cgs_cgb"`, 없으면 `"cgg_minus_cgd_at_gs"`(cgs = cgg − cgd, cgb = 0.0). 축은 기준 LUT 축(옛 세트 VS 0~0.8 → vsb > 0.8 실패, LUT v2 는 0~1.8). kind 표 없음 → `KeyError`. [r6] `Caps.cdd`·`css` = CDD·CSS 열이 있으면 같은 보간 × W/w_ref_m, 없으면 None. [JC-1, A-169] `Caps.cgs_measured` = CGS 열이 있으면 같은 보간 × W/w_ref_m(CGB 열 유무와 무관 -- `model`·`cgs`·`cgb` 값과 갈래는 불변), 없으면 None; 소비자 = metrics `junction_at_vgs_min` 하나. 값은 저장 부호 그대로(음수 가능 -- 로그·절댓값 없음). bin 지도 = `CapTable.l_bins`(1.4 폭 키 수정) |
| `tol_v_table(memo, kind, w_key, l_bin_checks=None)` | `TolVTable` | 5절([r6] 기본값 None = 중점 파일 값) |
| `curve_report(memo)` | `CurveReport(lut_fp, rows)` | 슬라이스·L 앵커마다 `CurveRow`(lut_types 문서): 격자점 곡선만. [r2] `n_curves` = **검사한** 곡선 수(건너뛴 곡선 제외), `n_skipped` = ID·GM 에 0 이하 격자점이 있어 뺀 곡선 수,
`n_curves + n_skipped = len(VDS)·len(VS)`. [r5] `n_hermite_nonmonotone` = 그 L 앵커 i 의 `count(~fc_ok_vgs[i]) + count(~fc_ok_vds[i])` + [r7] `count(~fc_ok_vs[i])`. 행 순서 (kind, w_key) 정렬 후 L 오름차순 |

### 4.2 [r5] 축별 보간 방법 (DEC-87 -- `op_point`·`gm_id_curve`·역산·`gmb` 공통, `_helpers_interp`)

| 양 | L | VGS | VDS | VS |
|---|---|---|---|---|
| ln ID | 선형(4.0 의 L 장) | 2점 cubic-Hermite, 기울기 = 저장 GM/ID | 2점 cubic-Hermite, 기울기 = 저장 GDS/ID | [r7] 2점 cubic-Hermite, 기울기 = −GMBS/ID (GMBS 열이 있는 슬라이스, 아니면 선형) |
| gm/ID | (ln ID 의 VGS 미분으로 **정의**) | Hermite 미분 | 마디 기울기 S_a 는 선형 | 마디 기울기 S_a 는 선형 |
| ln GDS, VTH, 용량 | 선형 | 선형 | 선형 | 선형 |

- 칸 규칙: 축마다 `cell(grid, x)` = (i, t), i = `min(max(bisect_right(grid, x) − 1, 0), n − 2)`, t = (x − grid[i])/(grid[i+1] − grid[i])
  (마지막 격자점은 마지막 칸 t = 1). 선형 가중치가 0 인 마디(t = 0 이면 i+1, t = 1 이면 i)는 읽지 않는다.
- 2점 cubic-Hermite(x0, x1 = x0 + h, 끝 값 y0·y1, 끝 기울기 m0·m1, t = (x − x0)/h): `p = y0·h00 + h·m0·h10 + y1·h01 + h·m1·h11`
  (h00 = 2t³ − 3t² + 1, h10 = t³ − 2t² + t, h01 = −2t³ + 3t², h11 = t³ − t²), 미분 `p'(x) = dp/dt / h`. 코드는 같은 다항식을 Bernstein
  제어점 (y0, y0 + m0·h/3, y1 − m1·h/3, y1) 의 de Casteljau 로 계산한다(3 = 조건 수 4 − 1). p(x0) = y0, p'(x0) = m0, p(x1) = y1, p'(x1) = m1.
- **조회점 (L, vgs, vds, vsb) 의 계산**(텐서곱 순서):
  1. VGS 칸 [a, a+1] = `cell(VGS, vgs)`, VDS 칸 k = `cell(VDS, vds)`(t_d), [r7] VS 칸 s0 = `cell(VS, vsb)`(t_s), L 은 선형 가중(L 은 4.0 의 장 안).
  2. VGS 마디 a' ∈ {a, a+1} 마다 **마디 값** V_a' 와 **마디 기울기** S_a':
     - [r7] **VS 축**: VDS 마디 b ∈ {k, k+1}(VDS 가 격자점이면 그 하나)마다 L 선형 가중 후 VS 칸 [s0, s0+1] 의 Hermite(끝 값 ln ID, 끝 기울기 −GMBS/ID, 폭 h_s, t_s)로 y_b 를 만든다.
       조건: 가중치 0 이 아닌 L 모서리·VDS 마디 모두에서 두 VS 끝 `vs_slope_ok` 참이고 `fc_ok_vs` 참. 아니면 y_b = L·VS 선형 가중(사유 `slope_undefined`/`fc_violation` 기록).
       VS 가 격자점이면 VS 보간이 없다.
     - y_b = (위 VS 처리 결과 또는 Σ_{L, VS 모서리} w·lnID[·, a', b, ·]) (b = k, k+1), m_b = Σ w·(GDS/ID)[·, a', b, ·](L·VS 선형).
     - V_a' = VDS 가 격자점이면 그 y_b, 아니면 Hermite(y_k, y_k+1, m_k, m_k+1, h_d, t_d) -- 단, 가중치 0 이 아닌 (L, VS) 모서리의
       `vds_slope_ok` 가 (b = k, k+1) 모두 참이고 `fc_ok_vds[·, a', k, ·]` 가 모두 참일 때만, 아니면 VDS 선형 y_k + t_d·(y_k+1 − y_k).
     - S_a' = Σ_{L, VDS, VS 모서리(가중치 ≠ 0)} w·(GM/ID) -- 그 모서리 중 `on_mask` 거짓이 있으면 NaN.
  3. **VGS Hermite 칸** = S_a·S_a+1 이 둘 다 유한이고 `fc_ok_vgs[·, a, ·, ·]` 가 가중치 ≠ 0 인 (L, VDS, VS) 모서리에서 모두 참.
     **예외 [2026-10-09, 격자 마디 우선]**: 조회 VGS 가 격자점(t ∈ {0, 1})이면 그 마디의 S 만 유한하면 되고(이웃 칸의 FC 위반은 이 점과 무관) 마디 V·S 그대로 -- 이때 `fallbacks` 에 "VGS" 를 남기지 않는다("VGS" 폴백은 S 가 정의되지 않았을 때만). 4.1 [r7] 'Hermite 가 가능한 칸'은 칸 안쪽 점에만 해당한다.
     Hermite 칸이면 lnID = p(vgs), gm/ID = p'(vgs) (VGS 가 격자점 t ∈ {0, 1} 이면 그 마디의 V·S 그대로 -- 반올림 없음),
     아니면 lnID = V_a + t·(V_a+1 − V_a), gm/ID = (V_a+1 − V_a)/h (그 직선의 미분 -- 정의 유지).
- 결과: 격자점(네 축 모두 격자 위, L 앵커)에서 lnID·gm/ID·lnGDS·VTH 는 저장값 그대로(r4·옛 다선형과 같은 값, gm_gds 만 식이
  `gm/ID·exp(lnID − lnGDS)` 라 몇 ulp 차). 마디 사이에서 gm/ID 는 ln ID 의 VGS 미분과 **같다**(같은 곡면).
- [r7] VS 축 Hermite(GMBS 열 -- 기울기 −GMBS/ID): r6 에서 보류했던 변경을 U3 가 했다(운영 보간·tol_V LOO·FC 검사·로드 기록이 함께 바뀜). GMBS 열이 없는 슬라이스(옛 12-L 세트·toy)는 VS 선형 그대로다.
  gm/ID 의 마디 기울기 S_a 는 VS 방향도 선형(저장 GM/ID 의 L·VDS·VS 선형 가중, VDS 와 같은 규칙).
  [r7 실측 2026-10-08, 소자 W = 5 µm(w_key 1000)·L 0.35 µm 칸 중앙 점 -- 선형 대비] VS 칸 중앙(VS = 칸 두 격자점의 중점 9개) × VGS 격자 49 × VDS 격자 index 2·6·…·46(12개), ngspice-46 `.op` 직접 대조(소자 `DUT_LINE` 과 같은 W 5 µm, bulk = −VS, 표본 nmos·pmos 각 5,292점), 지표 |Δln ID|/(gm/ID) [V]: nmos Hermite p50 0.13 µV·p99 2.6 µV·max 6.5 µV 대 선형(두 VS 격자점 op_point ln IDu 평균) p50 0.176 mV·p99 0.775 mV·max 0.987 mV; pmos Hermite p50 0.30 µV·p99 5.1 µV·max 12.3 µV 대 선형 p50 0.190 mV·p99 0.950 mV·max 1.074 mV. (gm/ID ≤ 25 부분집합도 같은 자릿수: nmos Hermite p99 3.2 µV 대 선형 0.605 mV, pmos 5.6 µV 대 0.655 mV.)
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
**다른 폭의 열로 대신하지 않는다**(폭 무관 가정을 박지 않음). [r6 결정 B] 재생성 슬라이스(GMBS·VDSAT 포함)에서는 모든 폭이 origin
"slice" 다(w_key 1000 도 슬라이스 열이 우선 -- 기준 LUT 열과는 print 자릿수 차 ≤ 5e-7). 옛 슬라이스와 쓰면 w_key 1000 만 "cap_table".

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
  2.3 %/5.2 %/18.0 %/85.8 %, 칸 중앙 2.2 %/5.1 %/19.0 %/90.0 %. 열 경로 대 기준 LUT 저장 GMBS(격자점) 상대차 최대 4.9e-7(print 자릿수 차).
  재생성 슬라이스(열 출처 "slice")로 다시 재도 같은 값(할선 대 열 차는 소수 3자리까지 같음, 열 경로 대 기준 LUT GMBS 최대 4.9e-7).
- [r6 결정 B] 재생성 슬라이스 검증(`_drafts/engine/lut_v2_slices_vdsat/verification_slices_vdsat.json`): 32개 모두 ID·GM·GDS·VTH·축·W·조건이
  옛 v2 슬라이스와 비트 동일, 새 열 GMBS·VDSAT 유한값; W = 5 µm 슬라이스 대 기준 LUT 최대 상대차 GMBS 4.99e-7(n)·4.9e-6(p), VDSAT
  5.0e-7(n·p); 다른 폭 8점(seed 20261008) 새 독립 .op 대비 ID·VDSAT·GMBS 최대 상대차 3.2e-7. 생성기 sha256 8df35d2e…(옛 6ad080e9…),
  manifest sha256 a25b9036…, 576 조합 1230.6 s(jobs 9).

### 4.5 [r7] gm/ID 축 곡선 표 -- `ft_curve`·`intrinsic_gain_curve`·`vdsat_curve`·`idu_curve` `(memo, kind, w_key, L, vds, vsb) -> GmIdAxisCurve` (설계 40 §2.3, 41 §6.2~§6.4, §4.1)
- 곡선 = 고정 (L, VDS, VS)의 `gm_id_curve`. 표의 마디 = **강반전 분지**(VGS ≥ 곡선 정점 = gm/ID 최댓값 마디, `nanargmax`)의 VGS 격자 마디 -- 값은 그 마디에서 LUT 가 말하는 양이라 새 추정이 없고,
  마디 사이는 소비자가 `op_point` 등으로 읽는다. 분지 안에 gm/ID 가 정의 안 된 마디(NaN)가 있으면 `lut_curve_undefined`(역산 함수와 같은 규칙).
- `GmIdAxisCurve(quantity, kind, w_key, L, vds, vsb, gm_id, values, vgs, cell_ok, monotone)`: 배열은 VGS 오름차순(gm/ID 는 분지에서 내려간다)·읽기 전용, `cell_ok[j]` = 마디 j·j+1 사이가
  Hermite 칸(역산 허용), `monotone` = `gm_id` 가 분지에서 엄격히 감소(그러면 gm/ID 축으로 값을 역산할 수 있고, 아니면 소비자는 마디 전수로 쓴다 -- 41 §4.1 해법 매핑).
- 값(`quantity`): `ft_curve` "ft_hz" = gm/(2π·Cgg)(Hz; gm = (gm/ID)·ID(w_m), Cgg = `caps(W = w_m).cgg` 라 폭 무관, 2π = `math.tau`; Cgg ≤ 0 마디는 `lut_curve_undefined`),
  `intrinsic_gain_curve` "intrinsic_gain" = `op_point.gm_gds`(무차원), `vdsat_curve` "vdsat_v" = `vdsat(...)`(V; VDSAT 열 없으면 `lut_column_unavailable`), `idu_curve` "idu_a" = ID·L/w_m(A; `op_point.IDu` 와 같은 양).
- memo: 영역 curve, 키 `(kind, w_key, L, vds, vsb)`, 함수 이름 `<quantity>_curve`. 같은 인자 두 번째는 compute 0.
- **소비처**(설계 40 §2.3 'lut → 41 §6'): `ft_curve`·`idu_curve`·`vdsat_curve`·`intrinsic_gain_curve` = search 출발 구간(`iv_speed`·`iv_headroom`·`iv_gain_l`, U13)과 GB4 곡선 검사·블록 gain 상한(U9). 만들어진 곡선 API 와 겹치는
  기존 임시 구현은 없다(`rg "gm_gds|\.cgg|vdsat\(" gmid_engine -g '!tests' -g '!lut'` 은 sizing 의 `gm_gds`(미분 보조)뿐 -- 곡선 표가 아니다). `vgs_for_current_density` 만 sizing 임시 우회를 대체했다(3.1).
- 실측(실데이터 w_key 1000, 무작위 (L 앵커, VDS ≥ 2 칸, VS 격자) 300점/kind(seed 20261008): 표 생성 성공 nmos 300·pmos 300(VDS ≥ 2 칸이라 `lut_curve_undefined` 0), 분지(정점 = VGS 0 의 약반전 평탄 구간)에서 gm/ID 엄격 감소(`monotone`) nmos 300·pmos 74 -- pmos 는 중반전에서 gm/ID 가 한 번 올라가는 모델 특성(곡선 보고 `n_branch_nonmonotonic`)이라 `monotone` = False 인 곡선이 많고 소비자는 그 곡선을 마디 전수로 쓴다, 평균 마디 수 nmos 49.0·pmos 48.8, 표 하나(새 memo) 평균 ms: nmos ft 2.46·gain 4.71·vdsat 1.75·idu 0.77 / pmos ft 2.38·gain 4.65·vdsat 1.62·idu 0.72).

## 5. [r2 전면 교체, r4 L 방향 추가, r5 같은 방법 LOO + Richardson] tol_V 표 `tol_v_table(memo, kind, w_key, l_bin_checks=()) -> TolVTable` (계획 N3.6, 사용자 확정 2026-10-07)

- **보간 축 VGS·VDS·VS leave-one-out + [r4] 같은 모델 bin 안의 L 축 leave-one-out.** **모든 L 앵커가 셀을 가진다**(r1 의 '양끝 앵커 None' 폐기).
- 셀 = (kind, w_key, L 앵커 i, VDS 격자 k) -- `cells[i][k]` = `TolVCell`. **셀별 값만** 낸다(전역 최댓값으로 줄이지 않음).
- [r7] VS 축 id_equivalent LOO 도 같은 방법(Hermite, 기울기 −GMBS/ID, 두 이웃의 `vs_slope_ok` 가 다 있는 점)이다 -- 차수 p = 4(없는 점·GMBS 열 없는 슬라이스는 선형 p = 2). `loo_orders` 의
  (id_equivalent, VS) 행이 `("id_equivalent", "VS", "hermite", 4, 2^-4)`. gm_id_inverse 의 VS 축은 그대로(곡선 ln ID 는 두 이웃의 VS Hermite, gm/ID 는 선형). 이 변경으로 tol_V 값이 바뀐다(캐시 키의 코드
  버전이 달라 옛 표는 재사용되지 않는다). 실측(w_key 1000 두 슬라이스, 격자 셀 864개씩, `tol_v_table` 을 디스크 캐시 없이 계산, 'VS 선형' = 같은 코드에서 `vs_slope_ok` 를 전부 거짓으로 둔 엔진의 선형 경로): `id_equivalent_v` 는 nmos·pmos 모두 변하지 않았다(nmos 중앙값 2.41 mV·p99 39.5 mV·최대 44.6 mV, pmos 3.70·21.4·22.7 mV -- 셀 최댓값은 VGS·VDS 축이 정한다). `gm_id_inverse_v` 는 nmos 중앙값만 81.2 mV → 76.4 mV(p99 517.6 mV·최대 518.1 mV 불변), pmos 는 중앙값 118.5 mV·p99 640.3 mV·최대 648.2 mV 불변.
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
    [r6, 오케스트레이터 결정 A -- **셀 단위**] 값 칸은 **VDS 격자점마다의 수열**(길이 = `len(vds_grid)`, 원소 float 또는 None)이고 그 bin 두
    앵커 행의 셀 (i, k) 에는 k 번째 원소만 더한다(원소 None 이면 그 셀은 외부 몫 없음). 수 하나(r5 형식)는 모든 k 같은 값, None 은 모든 k
    None 으로 정규화한다(`_helpers_loo.per_vds`). 길이가 다르면 `ValueError`. 정규화 형식 = `(model, (k 별 tuple), (k 별 tuple))`.
  - 앵커 1개 bin: 그 bin 안 L 보간 자체가 없다(4.0 `lut_l_bin_unbracketed`) -- L 방향 값 불필요, 상태 "single_point".
  - `l_bin_checks` 오류 → `ValueError`: 같은 model 두 번, 앵커 2개 bin 이 아닌 model(지도에 없는 이름 포함), 빈 지도 슬라이스에 비어 있지 않은 값.
  - memo 키 = `(kind, w_key, l_bin_checks 정규화)`(model 문자열·VDS 별 float/None tuple, model 정렬) -- 다른 외부 값은 다른 표
    (수 하나와 그 수를 모든 VDS 에 둔 수열은 같은 키).
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
  그 행들 × 칸 (k, k+1) 결합 셀(최대 넷)의 그 지표 값이 **모두 정의되면 그 최댓값, 하나라도 None 이면 None**([LM-1e] 셀 결합 규칙 = `_helpers_loo.table_at` 한 곳:
  tol_V·tol_VDsat·잡음 tol·mismatch tol 표 조회가 모두 이 함수를 부른다 -- 정의 항이 빠진 값을 내지 않는다, 계획 N3.6 표 10행. None 원인 = 켜진 격자점이 없는 셀,
  실 LUT 에서는 VDS = 0 열). `table_at(table, value_of, L, vds, context)` 의 `value_of` = 셀 → 값 또는 None 함수(셀을 읽는 방법). `metric` 이 TOL_V_METRICS 밖 → `ValueError`,
  VDS·L 범위 밖 → `SealViolationError`(`lut_axis_out_of_range`, table "tol_v").
- `TolVTable` 속성: `kind, w_key, L_anchors, vds_grid, cells`, [r4] `l_bins, l_loo, l_loo_bins`.
- `TolVTable` [r5] 속성 `loo_orders`(위 환산 표 그대로). [r6] 속성 `l_bin_checks`(위).
- [r6] r5 의 `tolerance.py` 안 helper(`_l_interior`·`_l_loo_report`·`_external_by_model`·`_loo`·`_cell_max`·`_targets`·`_with_external`·
  `_opt`·`at` 본문)는 `_helpers_loo` 로 옮겨 `tol_vdsat_table`·`midpoint_l_bin_checks` 와 같이 쓴다 -- 식·순서·오류 문장 같음.
- [r6 실측 2026-10-08, LUT v2 w_key 1000, 기본 `l_bin_checks=None`(중점 파일)] 계산 nmos 19.6 s·pmos 19.7 s(중점 검증 포함; 재생성 슬라이스로 다시 잰 때 11.7~13.6 s -- 기계 부하 차, 값은 같음). bin 상태(nmos·pmos
  같음): .26 (앵커 0, 1 = 0.15·0.18) **external**, .25 (2, 3, 4) computed, .24 (5~9) computed, .23 (10, 11 = 0.7·1)·.22 (12, 13 = 1.5·2)·
  .21 (14, 15 = 2.5·4) **missing_external**(이 bin 들의 중점이 파일에 없다 -- 8절, 명시 상태로 둔다), .20 (16 = 8)·.19 (17 = 20) single_point.
  [셀 단위 외부 값, 2026-10-08] .26 행(앵커 0·1) 셀 값 p50/p90/max: nmos gm_id_inverse 505/518/518 mV, id_equivalent 10.7/17.2/18.9 mV;
  pmos 279/313/316 mV, 16.3/21.3/22.7 mV (스칼라 외부 값이던 때는 행 전부가 max). 표 전체: id_equivalent nmos 0.94/6.9/18.9 mV, pmos
  0.94/10.8/22.7 mV; gm_id_inverse nmos 52/428/518 mV, pmos 65/212/316 mV. gm_id_inverse 는 셀 단위로도 거의 줄지 않는다 -- 모든 VDS 에
  정점 근처 평탄 목표가 있다(5.1 분포).
- [r5] **환산 검증 test(ngspice 칸 중앙 표본, 계획 N3.6 -- test 작성자 구현, 실데이터 마커)**: 셀 표본(최소: nmos·pmos w_key 1000,
  L 앵커 0.15·0.35·1·4 µm, VS index 0·2, 모든 VDS 격자점)에서 ngspice 로 **VGS 칸 중앙**(VGS_j + h/2, VDS·VS 격자점)과
  **VDS 칸 중앙**(VDS_k + h/2, VGS·VS 격자점)의 ID·GM 을 새로 잰다. 넷리스트는 슬라이스 생성기(`lut_data/sky130_lut_v2/verification/slices_vdsat/
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
- `lut.midpoints` 에 `(kind, w_key)` 가 없으면 `MidpointChecks(kind, w_key, (), (), None)`(중점 표는 슬라이스마다 자기 폭 하나 -- 다른 폭 값을 옮겨 쓰지 않는다).
- 중점 m(L_m, `L_points` 순서)마다 **`_helpers_bins.midpoint_bracket(l_grid, l_bins, L_m, grid_m, rule) -> (bin index | None, 사유 | None)` 하나**가 아래 순서로 판정
  (D7 적재 거부도 같은 함수), 쓰지 않으면 `skipped` 에 `(L_m, 사유, model 또는 None)`:
  1. 슬라이스 bin 지도 없음 → `"bins_unavailable"`
  2. L 앵커와 같은 격자 정수 → `"is_anchor"` 3. `bin_index`(4.0.1)로 bin 없음 → `"outside_model_bins"` 4. 그 bin 의 앵커 수 < 2 → `"single_point"`(model 있음),
  > 2 → `"bin_has_interior_anchors"` 5. 두 앵커 a0 < L_m < a1 가 아님 → `"not_bracketed"`.
- 남은 중점: t = (L_m − a0)/(a1 − a0), 슬라이스 앵커 행 i0·i1. [r6 결정 A] **세 값은 VDS 격자점 k 마다의 tuple**(길이 = 슬라이스 VDS
  격자 수, 그 k 에 점·목표가 없으면 원소 None) -- 아래 max 는 그 VDS_k 의 (VGS, VS) 점·목표에 대해.
  - `id_equivalent_v[k]` = max over (VGS, VS) 격자점 [중점 on_mask ∧ 슬라이스 on_mask(i0) ∧ on_mask(i1)] (VDS = VDS_k) of
    |lnID(i0) + t·(lnID(i1) − lnID(i0)) − lnID_m| / gm_id_m (`DcSlice.log_ID`, 중점 `log_ID`·`gm_id`).
  - `gm_id_inverse_v[k]`: 곡선 = (VDS_k, VS_s), 곡선 on = 위 마스크가 VGS 전부 참. 중점 곡선 gm/ID g(off 점은 −∞)에서 5절 목표 규칙
    (`branch_targets` -- 정점 이후, 오른쪽 모든 점보다 큼)으로 (곡선, j). 보간 곡선 = (lnID, gm/ID) 를 L 선형(gm/ID 앵커 값 =
    exp(log_GM − log_ID)) -- 운영 `gm_id_curve` 의 마디 값과 같다. 값 = VDS_k 곡선 목표들의 max |strong_inversion_root(보간 곡선, g_j) − VGS_j|
    (해 있는 것). `n_targets` = 목표 수, `n_inverse_failed` = 해 없음 수(모든 VDS 합). 목표 없음 → 모두 None, 0, 0.
  - `vdsat_v[k]`: `column_source(..., "VDSAT", required=False)` 가 있고 중점 VDSAT 이 있고 출처 표 축(VGS, VDS, VS) = 중점 축일 때,
    max over (VGS, VS) [중점 on_mask ∧ (출처 on_mask(i0) ∧ on_mask(i1), 출처에 on_mask 가 없으면 생략)] of |V(i0) + t·(V(i1) − V(i0)) − VDSAT_m|,
    아니면 모두 None. 출처는 4.3 규칙(슬라이스 열이 있으면 슬라이스).
  - Richardson 환산 없음(운영 보간의 칸 안 오차 자체).
- 같은 bin 의 중점이 여럿이면 한 `MidpointRow` 로 합친다: `L_points` 오름차순(파일 순서), 세 값은 k 마다 최댓값(None 은 무시), 개수는 합.
  `rows` = model 이름 정렬.
- [실측 2026-10-08, LUT v2 + 중점 파일, w_key 1000] nmos: rows = (.26, (1.65e-7,), 23,520 목표, 실패 0) 하나, VDS 별 값 p50/p90/max:
  gm_id_inverse 505/518/518 mV, id_equivalent 10.7/17.1/18.9 mV, vdsat 2.04/2.40/2.49 mV(k = 0 은 ID = 0 이라 None).
  skipped = ((6e-6, "single_point", model.20), (1.4e-5, "single_point", model.19)). pmos: (.26, 19,671, 1,569), gm_id_inverse 279/313/316 mV,
  id_equivalent 16.3/21.2/22.7 mV, vdsat 19.6/29.8/32.5 mV, 같은 skipped. (옛 단일 기준 폭 중점 파일 시절 실측 -- LM-1e 이후 중점은 슬라이스마다 자기 폭 파일이다.)
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
  `()` = 없음. vdsat_v 는 5절과 같은 셀 단위(VDS 별 수열, 수 하나·None 허용, `per_vds` 정규화). 오류 규칙(중복·앵커 2개 bin 아님·빈 지도에 값 → `ValueError`)과 `l_loo`·`l_loo_bins` 상태 이름은 5절과 같다.
- `TolVdsatTable` 속성: `kind, w_key, origin, L_anchors, vds_grid, cells, l_bins, l_loo, l_loo_bins, loo_orders, l_bin_checks`.
  `loo_orders` = (("vdsat", "L", "linear", 2, 0.25), ("vdsat", "VDS", ...), ("vdsat", "VGS", ...), ("vdsat", "VS", ...))(축 이름순).
  `at(L, vds, metric="vdsat")` = 5절 `TolVTable.at` 와 같은 행·칸 규칙(`table_at`), context `kind, table "tol_vdsat", w_key`, metric 이
  `TOL_VDSAT_METRICS` 밖 → `ValueError`. memo derived 키 `(kind, w_key, l_bin_checks 정규화)`.
- 소비자(sizing O1): 봉인 7 `VDS − VDsat ≥ +tol_VDsat` 의 tol_VDsat = `tol_vdsat_table(memo, kind, w_key).at(L, vds)`.
- [실측 2026-10-08, 재생성 슬라이스(GMBS·VDSAT) + 중점 파일, w_key 1000, 기본 외부 값(셀 단위)] 출처 "slice", 계산 0.23 s. 셀 vdsat_v
  p50/p90/max nmos 0.93/1.88/2.49 mV, pmos 1.08/10.2/32.5 mV(max = .26 외부 값 -- pmos 0.165 µm 중점 VDSAT 보간 오차; .26 행 셀 p50 nmos
  2.04 mV·pmos 19.6 mV), 환산 전 nmos 3.3/4.4/8.5 mV, pmos 4.1/9.8/22.2 mV. bin 상태는 5절 실측과 같다. 예: `vdsat(nmos, 1000, 1 µm, 0.9, 0.9, 0)`
  = 0.2557 V, L 0.85 µm·vsb 0.3 = 0.2107 V, `tol_vdsat_table(nmos, 1000).at(1e-6, 0.9)` = 0.93 mV. 다른 폭: nmos w_key 72 origin "slice",
  `vdsat(1 µm, 0.9, 0.9, 0.3)` = 0.2576 V, 셀 p50/p90/max 0.97/1.31/1.39 mV; pmos w_key 84 0.0586 V, 0.89/1.36/8.18 mV -- 2-앵커 bin 은 모두
  missing_external(옛 단일 기준 폭 중점 파일 시절 -- LM-1e 이후 `widths` 슬라이스는 자기 중점이 없으면 적재 거부). 옛 슬라이스와 쓰면 w_key 1000 만 "cap_table"(값 차 ≤ 5e-7 상대).

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
| `lut.slice_map[("nmos", 100)].hermite_fc` | `(("VDS", 18, 0), ("VGS", 24, 0))` [r7: `+ (("VS", 0, 0),)` -- toy 슬라이스는 GMBS 열이 없다] |
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
| `slice_map[("nmos", 100)].hermite_fc` | `(("VDS", 18, 18), ("VGS", 24, 12))` [r7: `+ (("VS", 0, 0),)`]; `curve_report(m).rows[i].n_hermite_nonmonotone` = 10 (VGS 4 + VDS 6, 모든 행) |
| `op_point(m, "nmos", 100, 1e-6, 0.25, 0.75, 0.0)` | VGS·VDS 모두 선형 칸 → IDu = √(1e-7·1e-6) = 3.162278e-7, gm_over_id = ln10/0.5 = 4.605170(그 직선의 미분), gm_gds = 46.05170, gds_per_w 0.03162278, vth 0.4 -- 실패하지 않는다 |
| `vgs_for_gm_id(m, "nmos", 100, 15.0, 1e-6, 0.5, 0.0)` | 고른 칸 [0, 0.5] 위반 → `SealViolationError` `lut_hermite_nonmonotone_cell`, detail axis "VGS", cell_lo 0.0, cell_hi 0.5 |
| `vgs_for_gm_id(m, "nmos", 100, 7.0, 1e-6, 0.5, 0.0)` | 칸 [0.5, 1] (단조) 의 Hermite 미분 = 7 인 근 0.5834716 (2차식 근, 칸 안 t = 0.1669433) |
| `gm_id_for_target(m, "nmos", 100, 1e-6, 0.5, 0.0, W=2e-6, current=2e-6)` | 마디 Q = (2e-7, 2e-6, 2e-5) 에서 칸 j = 0 (searchsorted left − 1 → max 0) 이 위반 → `lut_hermite_nonmonotone_cell` |
| `tol_v_table(m, "nmos", 100).cells[0][0]` | id_equivalent_loo_v = |ln(1e-6) − Hermite(ln1e-7, ln1e-5, 20, 4, H = 1, t = ½)| / 10 = 0.2, id_equivalent_v = 0.2/16 = 0.0125 |

---

## 8. 범위 밖·보류

- ~~`vdsat` 대기~~ → [r6] 만들었다(4.3·5.2). `gm_id_for_vgs`: 소비처 미확정(DEC-76) → 만들지 않음.
- [r6 결정 B 완료] 슬라이스 생성기(`_drafts/engine/lut_slices/sky130_dc_width_slices.py`)가 VDSAT·GMBS 를 저장하고 576 조합을 다시
  돌렸다(`_drafts/engine/lut_v2_slices_vdsat/`, 검증 `verification_slices_vdsat.json`) -- 모든 폭에서 `vdsat`·`tol_vdsat_table`·GMBS 열 `gmb`.
  **VS 축 Hermite(GMBS 기울기)는 보류**(4.2 끝).
- [r6 -> 2026-10-08 사용자 결정으로 변경] 승인 L 파일의 `verification_midpoints_um` 을 (0.165, 6.0, 14.0) 에서 **(0.165, 0.85, 1.75, 3.25)** 로 바꿨다.
  옛 6.0·14.0 은 앵커 1개 bin(.20 = (4, 8] 앵커 8, .19 = (8, 20] 앵커 20)에 들어 쓰이지 않았고(조회 자체가 `lut_l_bin_unbracketed`),
  앵커 2개 bin .23(0.7·1 um)·.22(1.5·2 um)·.21(2.5·4 um)은 중점이 없어 missing_external 이었다. 원인: lut_regen_plan K2' 와 생성기 `candidates` 가 bin 소속을
  구간 끝점 포함([lmin, lmax])으로 셌고 4.0.1 실측 규칙(경계 L = 아래 bin)과 달랐다.
  유도 규칙(선언은 이 규칙의 결과): `candidates` 는 **showmod 가 후보 L 마다 고른 model 로 센 소속**이 정확히 2점인 bin 의 두 점의 중점(제조 격자로 반올림)을
  낸다 -- 하드코딩 없음. 구간 끝점이라도 다른 bin 에 속하는 점(경계 L)은 소속에서 뺀다(옛: 불연속 경계 근처만 뺐다).
  [실측 2026-10-08, w_key 1000, 새 중점 파일 sha256 `afda374c...0f99`, 4 중점 모두 사용(skipped = ())] bin 별 최대 오차(VDS 셀 최댓값, mV):

  | model | L (um) | kind | gm_id_inverse | id_equivalent | vdsat | n_targets / 실패 |
  |---|---|---|---|---|---|---|
  | .26 | 0.165 | nmos | 518 | 18.9 | 2.49 | 23,520 / 0 |
  | .26 | 0.165 | pmos | 316 | 22.7 | 32.5 | 19,671 / 1,569 |
  | .23 | 0.85 | nmos | 289 | 26.5 | 2.87 | 23,520 / 3,598 |
  | .23 | 0.85 | pmos | 635 | 12.8 | 1.33 | 22,992 / 0 |
  | .22 | 1.75 | nmos | 364 | 16.0 | 3.28 | 23,520 / 39 |
  | .22 | 1.75 | pmos | 252 | 8.43 | 0.79 | 22,207 / 6,341 |
  | .21 | 3.25 | nmos | 155 | 44.6 | 6.39 | 23,520 / 3,691 |
  | .21 | 3.25 | pmos | 648 | 21.4 | 0.77 | 21,850 / 0 |

  gm_id_inverse 의 큰 값은 5.1 과 같은 정점 근처 평탄 목표 효과다. 이 표는 `tol_v_table`·`tol_vdsat_table` 의 외부 bin 값 그대로이며 계약에 별도 수치 예산은
  선언돼 있지 않다(소비자 설계 몫).
  [데이터 = 버전 파일 r2] 공유 `lut_v2/` 의 기존 파일은 고치지 않는다. 새 파일: `sky130_nfet_pfet_lut_v2_verify_midpoints_r2.npz`(sha256 `afda374c...0f99`),
  `sky130_nfet_pfet_lut_v2_r2.npz`(sha256 `938e95b9...1efe2`; 기존 cap_npz 와 배열 비트 동일, meta `L_source.sha256` 만 새 L 파일 sha256
  `3312789263b2e3942fc58141088fa2e11b6d42010c28a90bd87a81872354074b` 로 -- cap_npz 의 `L_source` 는 승인 L 파일 전체의 sha256 이라 선언 파일을 바꾸면 중점 파일과의
  1.7 (2) 대조가 이 값을 요구한다). `assets/lut_v2_location.json` 이 두 r2 파일을 가리켜 브랜치 병합 때 전환된다. 옛 중점 파일 사본: `lut_v2/verification_r2/`.
- [r6] 외부 값은 셀(VDS) 단위로 바꿨다(오케스트레이터 결정 A). 그래도 gm_id_inverse 는 .26 행 p50 505 mV(nmos)로 크다 -- 모든 VDS 에
  정점 근처 평탄 목표(gm/ID ≈ 24.7)가 있어서다(5.1 분포: 점별 p50 10.5 mV, 목표 gm/ID ≤ 15 만이면 max 29 mV). 목표 gm/ID 범위 제한은 소비자
  tol 의미를 바꾸는 계약 변경 -- 결정 대상.
- [r6] **외부 값이 없는 앵커 2개 bin(명시 상태 `missing_external`)**: .23 (0.7·1 µm), .22 (1.5·2 µm), .21 (2.5·4 µm) -- nmos·pmos 모두, w_key 1000.
  (옛 단일 기준 폭 중점 파일 시절: 다른 폭은 모든 2-앵커 bin 이 missing_external. LM-1e 이후 `widths` 슬라이스는 자기 폭 중점이 없으면 `bin_missing_external` 적재 거부 -- `widths` 밖 슬라이스의 2-앵커 bin 만 상태 `missing_external` 로 남는다.)
- [r6] SVG2_1HZ·SVG2_HF·VTH(기준 LUT)·CDD·CSS 외 열: 로드만 하고(`CapTable.columns`) 조회 함수는 없다(잡음 소비처 미정).
- E3 디스크 캐시(tol_V 표·곡선 보고 지문 키): 이 단계 밖. 현재 derived memo(실행 내)만.
- toy LUT 픽스처(`tests/fixtures/toy_lut.py`, 옛 `_invq_newton`·`build_toy_lut` 복사)는 test 작성자 몫.
- 옛 `SemiEmpiricalGmIdLUT`(W_ref = 5 µm 슬라이스 배열) 대비 `op_point` 동치 test: [r5] **격자점에서만**(6절). 옛 로그 바닥(1e-18·1e-30)과
  갈리는 점(ID < 1e-18)은 비교에서 뺀다. `vgs_for_gm_id` 는 칸 선택(3절)만 옛과 비교할 수 있고 칸 안 근은 다르다. 옛 해가 정점 왼쪽인
  입력은 새 쪽이 실패해야 한다(3절).
- [r5 -> r7 해소] VS 축 Hermite(GMBS 열): 4.2·5절에서 했다. GMBS 열이 없는 슬라이스(옛 12-L 세트·toy)의 gmb 는 VS 칸 할선(이웃 칸 경계에서 계단) 그대로다.
- [r7] 잡음·mismatch 열: 기준 폭(5 µm)에서만 잰다(다른 폭으로 옮기지 않는다 -- 4.3 규칙). 폭 W 소자는 호출부가 환산한다(9.3·10.4).
- [r7] 특성화 깊이: 잡음 주파수 점은 고정 로그 이분 깊이(기본 3)이고, 설계 41 §7.2 의 '조건을 만족하는 점이 생길 때까지 반복(상한 K_max)'를 칸별 적응 반복이 아니라 전 칸 같은 깊이로 구현했다
  (칸별 tol 이 B 면에서 나와 순환이므로 flicker 면 tol 로 판정 -- 9.2). 미상 칸 수는 9.2 실측에 있다. 깊이를 늘려 다시 재는 것은 `--depth` 로 가능하다(새 버전 파일).

---

## 9. [r7] 잡음 -- 새 버전 파일 `..._noise_r1.npz`, 분해 S_vg = A/f^EF + B (설계 41 §7.2, 계획 DEC-96 (3), D-NZ2)

모델 사실(PDK 모델 카드, bin 전수 확인 `_drafts/engine/noise_spec_proposal.md` §0): `fnoimod = 1`(unified flicker, EF), `tnoimod = 1`(holistic thermal -- γ 는 모델 파라미터가 아니라 바이어스 함수).
그래서 γ·K 를 상수로 가정하지 않고 LUT 칸마다 읽는다. EF 는 PDK 선언 양(`noise_ef_nmos` 0.84, `noise_ef_pmos` 1.0 -- core CONTRACT 9.4b)이고 `LutSpec.noise_ef` 로 들어온다.

### 9.1 파일과 로드 `load_noise_tables(spec, prov, caps) -> {kind: NoiseTable}` (`noise_set.py`, `load_lut_set(noise_npz=)` 가 부른다)
- 생성기: `assets/sky130_lut_sweep.py noise --cap-npz <기준 LUT> --out <npz> --work <폴더> [--jobs N] [--depth K]`. 기준 LUT 와 **같은 (L, VGS, VDS, VS) 격자·같은 DUT 줄·같은 include·같은 측정 구조**
  (드레인 choke 개방 + 게이트 AC 여기, `inoise_spectrum`² = 게이트 환산 V²/Hz). 주파수 점 = 기준 LUT 두 점(meta `frequencies_hz`: `NOISE_F_PROBE` = 1 Hz, `F_TEST` = 100 MHz) 사이의 **로그 이분**
  (깊이 `--depth` 기본 3: 이웃 점 기하평균을 더하는 일을 깊이만큼 반복 -> 1, 10, 10², …, 10⁸ Hz). 점 위치는 상수가 아니라 두 끝과 깊이에서 나온다.
- 새 파일 키: `L·VGS·VDS·VS`, `w_ref_m`, `corner`, `temp_c`, `f_hz`(양끝 사이 이분 점 7개 [10.0, 100.0, 1000.0, 10000.0, 100000.0, 1000000.0, 10000000.0]), kind 마다 `SVG2_F<접미사>`[f, L, VGS, VDS, VS](V²/Hz, 기준 폭 5 µm), `meta_json`
  (`cap_npz_sha256` = 묶인 기준 LUT sha256, `base_frequencies_hz`, `bisect_depth`, `base_repro_rel_max` = 같은 생성기로 다시 잰 1 Hz·100 MHz 값과 기준 LUT 열의 최대 상대차, 모델 파일 sha256, ngspice 버전, 온도, 조합 기록).
  기존 r2 파일은 고치지 않는다. 기준 LUT 의 `SVG2_1HZ`·`SVG2_HF`(f_lo·f_hi)와 이 파일의 점을 합쳐 `NoiseTable.S` = [f_lo, 이분 점들, f_hi] 오름차순으로 노출한다.
- 거부(`SchemaRejectedError`): meta 키 없음/수 변환 불가 `lut_noise_meta_invalid`(detail `path, missing`), 묶인 기준 LUT 가 다름 `lut_noise_cap_mismatch`(`bound, cap`), 측정 조건(corner·temp_c)이 기준 LUT 와 다름
  `lut_conditions_mismatch`, 주파수 점이 오름차순·양끝 안쪽이 아님 `lut_noise_frequency_invalid`, 축·기준 폭 불일치 `lut_noise_axes_mismatch`, 기준 LUT 에 `SVG2_1HZ`·`SVG2_HF`·`GM` 열 없음
  `lut_noise_cap_column_missing`, `spec.noise_ef` 에 kind 없음 `lut_noise_ef_undeclared`, 열 없음/모양 다름 `lut_noise_column_missing`·`lut_noise_shape_mismatch`.
- [실측 2026-10-08] 생성기 `noise` 모드, 조합 360(nfet 180 + pfet 180 = L 18 × VS 10, 조합당 ngspice 프로세스 1개가 VGS×VDS 2401점 × 주파수 9개를 돈다), 병렬 8. 소요: 벽시계 약 104 분(20:01~21:45, 기계 부하 100 % -- 다른 단위의 테스트·특성화와 동시; 30 분 백그라운드 시간 제한에 한 번 중단돼 체크포인트(조합 단위, 생성기 sha256 같을 때만 재사용)로 이어 돌렸다), 단독 실행 조합 1개 17.5 s(2401점, 주파수 9개). 재현성: 같은 생성기로 다시 잰 1 Hz·100 MHz 값이 기준 LUT `SVG2_1HZ`·`SVG2_HF` 와 비트 동일(`base_repro_rel_max` = 0.0, 4개 열 모두). 파일 `sky130_nfet_pfet_lut_v2_noise_r1.npz` 48.6 MB sha256 `f5ecfdf1…32a1`, 생성기 sha256(작업 트리 CRLF 바이트) `0ea5ca36…cc69`(git blob LF `73522053…5987`), ngspice-46, TT 27 °C.

### 9.2 분해 `noise_planes(memo, kind) -> NoisePlanes` (`noise_planes.py`, 층 5; memo 영역 derived)
- 점마다 S_lo = S(f_lo), 이분 점 j 의 flicker 비 r_j = (f_j/f_lo)^−EF, **B_j = (S_j − S_lo·r_j)/(1 − r_j)**, A = (S_lo − B)·f_lo^EF (f_lo = 1 Hz 면 A = S_vg(1 Hz) − B).
- **B 를 읽는 점**: 점마다 아래 두 조건을 모두 만족하는 **가장 높은** 주파수 점 j.
  (1) **피드스루**(설계 41 §7.2): (2π·f_j·|Cgd|/gm)² ≤ 그 점의 허용오차 `tol_point`. Cgd = `CapTable.CGD`, gm = 기준 LUT `GM` 열 -- 같은 LUT 칸이라 새 상수가 없다.
      (게이트 환산 잡음의 피드스루: 드레인 열잡음 전류가 gm 대신 √(gm² + (ωCgd)²) 로 나뉘어 측정값이 B/(1 + (ωCgd/gm)²) 로 작아진다 -- 상대오차 (ωCgd/gm)².)
  (2) **평탄(plateau)** [r7 추가, 설계 밖]: j 가 가장 낮은 이분 점이 아니면 |B_j − B_{j−1}| ≤ `tol_point`·|B_{j−1}|. 근거(실측 2026-10-08): 긴 L·약반전에서는 입력 환산 잡음이 위 피드스루 식이
      예측하는 것보다 훨씬 낮은 주파수에서 1차 저역 통과로 떨어진다(L = 20 µm·VGS 0.6 V·VS 0.6 V, gm/ID 25: B_j 가 10 Hz~1e4 Hz 에서 6.82e-14 로 같다가 1e5 Hz 6.42e-14, 1e6 Hz 9.4e-15 -- 피드스루 식은
      1e6 Hz 에서 6e-4). 열잡음 평탄값은 주파수와 무관해야 하므로(모델이 정확하면 flicker 가 지배하는 낮은 주파수에서도 같은 B) 평탄이 깨지는 점은 쓰지 않는다. (1) 만 쓰면 이런 점의 B 를 86 % 낮게 읽는다.
      효과(같은 데이터로 재 본 |B_선택 − B(100 Hz)|/B 의 p50/p90/p99 -- 셀 허용오차+피드스루만: nmos 0.029/0.44/0.99(10 % 넘는 점 28 %), pmos 0.021/0.87/1.0(37 %); 점 허용오차+평탄: nmos 0.0023/0.105/0.42(10.5 %), pmos 0.00055/0.004/0.14(1.2 %). 대가: B known 비율 nmos 94.4 → 90.1 %·pmos 81.7 → 77.5 %).
  그런 점이 없으면 B 는 미상(`no_feedthrough_free_point`).
- **허용오차**: `tol_a`[L, VDS] = ln S_vg(f_lo) 면의 leave-one-out(선형, 네 축; L 은 같은 bin 안 내부 앵커) 오차 ÷ 2^2 의 셀 안 최댓값 -- 잡음 면 자체의 보간 해상도(`linear_loo_cells`). 정의 안 되면 NaN -> B 미상.
  `tol_point`[L, VGS, VDS, VS] = min(그 점의 같은 LOO 오차, 그 셀 `tol_a`); 점의 LOO 가 정의 안 되면(격자 가장자리) `tol_a`. **설계의 '그 칸의 tol' 보다 엄격하다**: 셀 최댓값은 몇 개 병적 점(VDS ≈ 0 열·VGS 끝)이 정해 셀 전체
  허용오차를 부풀린다(`tol_a` 중앙/최대 nmos 0.135/3.95·pmos 0.297/4.17 -- 상대오차가 1 을 넘는 셀이 있다). 점 허용오차 ≤ 셀 허용오차라 셀 허용오차 보증은 유지된다. B 의 주파수를 고르는 데 B 의 tol 을 쓸 수 없어(순환)
  flicker 면의 tol 을 쓴다.
- 상태 `NOISE_B_STATUS` = ("known", "no_feedthrough_free_point", "nonpositive"): 조건을 만족하는 점이 없으면 `no_feedthrough_free_point`, B ≤ 0 또는 A ≤ 0 이면 `nonpositive`. 미상인 점은
  A := S_lo·f_lo^EF(B 를 0 으로 둠), ln B = NaN. 설계 41 §7.2: 미상이면 그 칸을 쓰는 잡음 metric 의 resolution 을 무한대로 두고 판정을 보류한다(소비자 U8).
- 결과 `NoisePlanes(kind, ln_a, ln_b, status, tol_a, ln_b_filled, flag_no_point, flag_nonpositive, tol_point)`(배열은 읽기 전용; 뒤 4개는 조회·진단용 보조 면; 배열을 품어 디스크 캐시 `unstorable` -- 재계산 비용 1.3 s / 1.4 s(nmos/pmos, 한 번))). 잡음 r1 파일이 없으면 `KeyError`.
- [실측 2026-10-08] 격자점(기준 LUT on_mask 점) 중 B known 비율 nmos 90.1 %·pmos 77.5 % (상태 0/1/2 점 수 nmos {'0': 381515, '1': 41737, '2': 108}·pmos {'0': 328150, '1': 94975, '2': 235}). `tol_a` 정의된 셀 nmos 882/882·pmos 882/882, 중앙/최대 nmos 1.35e-01/3.95e+00·pmos 2.97e-01/4.17e+00. γ_eff = B·gm/(4kT)(T = 300.15 K, VDS 0.9 V, VS 0): nmos L 0.25 µm gm/ID 10.9 -> γ 1.95 K 1.72e-22 known; nmos L 0.25 µm gm/ID 15.7 -> γ 1.924 K 1.73e-22 known; nmos L 0.5 µm gm/ID 10.5 -> γ 1.977 K 2.71e-22 known; nmos L 0.5 µm gm/ID 17.3 -> γ 1.776 K 2.45e-22 known; nmos L 1 µm gm/ID 10.9 -> γ 2.108 K 3.08e-22 known; nmos L 1 µm gm/ID 15.4 -> γ 1.973 K 2.74e-22 known; pmos L 0.25 µm gm/ID 11.3 -> γ 1.016 K 7.31e-23 known; pmos L 0.25 µm gm/ID 15.2 -> γ 0.781 K 7.63e-23 known; pmos L 0.5 µm gm/ID 10.3 -> γ 1.013 K 1.24e-22 known; pmos L 0.5 µm gm/ID 15.3 -> γ 0.844 K 1.15e-22 known; pmos L 1 µm gm/ID 10.4 -> γ 1.056 K 1.87e-22 known; pmos L 1 µm gm/ID 15.2 -> γ 0.854 K 1.79e-22 known. 제안서 §0.2 값(nfet 1.9–2.1, pfet 1.0–1.05(gm/ID 10)·0.77–0.84(gm/ID 15), K = A·W·L nfet 1.7e-22–3.3e-22, pfet 0.5e-22–1.9e-22 V²·m²)과 일치.

### 9.3 조회 `noise_params(memo, kind, w_key, L, vgs, vds, vsb) -> NoiseParams(A, B, ef, b_status, w_m)` (`noise_query.py`, 층 6; memo 영역 point)
- S_vg(f) = A/f^EF + B (V²/Hz, 기준 폭 `w_m`). 폭 W 소자는 A·B 모두 `w_m`/W 배(같은 전류밀도에서 S_vg 는 폭에 반비례). 파생량은 읽는 쪽이 계산한다(열로 저장하지 않는다): **γ_eff = B·gm/(4kT)**, **K = A·W·L**
  (V²·m², §6.4-3 의 1/f L 하한).
- 보간: ln A·ln B 를 L(4.0 규칙)·VGS·VDS·VS 모든 축 선형(`linear_point`). 가중치 0 이 아닌 모서리 중 B 미상이 하나라도 있으면 그 점의 `B` = None, `b_status` = 그 사유(`nonpositive` 우선), `A` 는 면의 값 그대로.
- 폭 키가 기준 LUT 폭 키(`CapTable.w_key`)와 다르면 실패 -- 다른 폭 열로 대신하지 않는다(4.3 규칙).
- 실패(`SealViolationError`): 잡음 파일 없음 `lut_noise_unavailable`, 폭 키 불일치 `lut_column_unavailable`(`column` = "SVG2"), L·축 -> 4.0·4.1 사유(context `table` = "noise"). 옛 `SID_1F` 열은 읽지 않는다(단위가 잘못됨).
- 호출 비용 약 102 µs / 275 µs (nmos/pmos, memo 미적중 1회).

### 9.4 허용오차 `tol_noise_table(memo, kind) -> TolNoiseTable` (`noise_tolerance.py`; memo 영역 derived, 디스크 캐시 대상)
- 셀 (kind, L 앵커, VDS) × 지표 `TOL_NOISE_METRICS` = ("flicker", "thermal"): `flicker` = ln S_vg(f_lo) 면의 LOO 선형 상대오차 ÷ 2^2 의 셀 안 최댓값(= 위 `tol_a`), `thermal` = ln B 면(B known 인 점끼리)의 같은 값.
  값이 로그라 상대오차(무차원)다. `.at(L, vds, metric)` = `TolVTable.at` 와 같은 행·칸·셀 결합 규칙(`table_at`: 결합 셀에 None 이 하나라도 있으면 None). 앵커 2개 bin 의 외부 L 값(검증 중점)은 잡음에 없다 -- `l_loo` 상태에 남는다.
- [실측 2026-10-08] flicker 중앙/최대 nmos 1.35e-01/3.95e+00·pmos 2.97e-01/4.17e+00, thermal 중앙/최대 nmos 1.67e-01/1.03e+00·pmos 1.72e-01/1.29e+00 (상대). 계산 0.3 s/0.4 s. 셀 최댓값은 소수의 병적 점이 정한다 -- 점별(on 점) ln B LOO 오차 p50/p90/p99: nmos L 축 0.4/1.6/4.4 %·VGS 0.13/1.4/11.5 %·VDS 0.002/0.44/7.1 %·VS 0.13/0.94/12 %, pmos L 0.8/4.4/22 %·VGS 0.38/1.1/13 %·VDS 0.002/0.41/7.0 %·VS 0.17/0.75/14 %.

### 9.5 데이터 필수 검사 `require_lut_data(lut, kinds, *, noise=False, mismatch=False)` (`lut_requirements.py`)
- 잡음 제약(`noise_*` metric)이 선언됐는데 `lut.noise` 에 kind 가 없으면 `SchemaRejectedError` `noise_lut_missing`, offset 제약이 선언됐는데 `lut.mismatch` 에 없으면 `mismatch_lut_missing`
  (detail `kinds` = 없는 kind 정렬 tuple; 둘 다 없으면 잡음 쪽이 먼저). 호출부 = spec 의 제약 선언을 읽는 단위(authoring·search 시작, 설계 40 §11 U5·U9) -- 이 브랜치에는 그 제약 선언이 아직 없다.

### 9.6 손계산 toy (test 작성자가 그대로 만들 수 있는 입력)
- 잡음 r1·기준 LUT 를 같은 축으로 만들고 모든 점에서 S_vg(f) = A0/f^EF + B0 (A0 = 1e-12, B0 = 1e-16, EF = 1; f = f_lo = 1, 이분 점 10, 100, f_hi = 1e4 Hz -- 기준 LUT `SVG2_1HZ` = A0 + B0, `SVG2_HF` = f_hi 값)를 쓰고 `GM` = 1e-3 이다.
  - `CGD` = 0 이면 피드스루 0 이라 허용오차(≥ 0) 이하다. 모든 j 에서 B_j = B0(대수적으로 정확: S_j − S_lo·r_j = A0(f_j^−1 − f_j^−1) + B0(1 − r_j))이고 평탄 조건은 허용오차 0 이어도 반올림 허용분 안에서 통과한다 ->
    선택은 가장 높은 f(1e4), A = S_lo − B0 = A0 -> `noise_params` = (A0, B0, EF = 1, "known", w_m).
  - 면이 모든 점에서 같으면 LOO 오차 0 이라 허용오차 0: `CGD` > 0 이면 피드스루 > 0 이라 모든 점이 탈락 -> 모든 점 `no_feedthrough_free_point`, `B` = None, `A` = S_lo·f_lo^EF = A0 + B0.
  - 경계: 이분 점은 항상 f_lo 보다 크다(`lut_noise_frequency_invalid` 로 보장) -- B_j 식의 분모 1 − r_j 가 0 이 되지 않는다.
  - 한계(데이터): ngspice 가 `inoise_spectrum` 을 7자리로 찍어 S 가 상대 ~1e-6 해상도라, flicker 가 지배하는 낮은 주파수의 B_j 는 (S_lo·r_j/B)·1e-6 만큼 흔들린다(예: nfet L 0.5 µm, gm/ID 10: S_lo/B = 1.4e6 -> 10 Hz 점 B_j -4 %,
    100 Hz +1.8 %, 1e3 Hz 이상 0.5 % 안). 평탄 조건이 이 점들을 거부할 수 있다.

## 10. [r7] mismatch 감도 -- 새 버전 파일 `..._mismatch_r1.npz`, DVGS_k 와 A_eff (설계 41 §6.4-2·2b, 계획 DEC-96 (2), D-MM1·2, D-PG)

모델 카드는 변수 p ∈ {vth0, toxe, voff, (pfet) nfactor} 를 `p = p0 + p_slope_spectre·(p_slope/sqrt(l·w·mult))` 로 소자마다 독립 gauss(std 1) 로 흔든다(core CONTRACT 9.4b·9.6: l·w 는 µm 수치, slope 의 길이 단위 µm,
**bin 마다 쓰는 slope 이름이 다르다** -- pfet L < 0.5 µm 은 `vth0_slope1` 7.356e-3). 같은 ID 에서의 ΔVGS 가 β 경로(1/(gm/ID))와 Vth 경로를 한 열에 함께 담는다.

### 10.1 파일과 로드 `load_mismatch_tables(spec, prov, caps) -> {kind: MismatchTable}` (`mismatch_set.py`)
- 생성기: `assets/sky130_lut_sweep.py mismatch --cap-npz <기준 LUT> --out <npz> --work <폴더> [--jobs N]`. 기준 LUT 와 같은 격자·DUT 줄·include 로, 모델 카드 복사본에서 변수 k 의 `*_slope_spectre` 를 0 → **1σ**
  (= `.option scale` 에서 읽은 1e-6; DUT 가 l·w 를 m 로 주므로 sqrt(l·w) 가 µm 기준 값의 1e-6 배 -- core CONTRACT 9.4b 단위 확인)로 바꾼 섭동 곡선과 기준 곡선을 돌려, 기준 곡선 칸의 ID 에서 섭동 곡선의
  |VGS| 차를 **DVGS_k**(V) 로 둔다(역산 = 섭동 곡선의 VGS cubic-Hermite -- 값 ln ID, 기울기 gm/ID -- 의 bisection 70회, 기준 ID 가 섭동 곡선 범위 밖·ID ≤ 0·섭동 곡선이 단조 증가 아님이면 NaN). 변수 = 모델 카드 머리
  `*_slope_spectre` 전수(nfet toxe·vth0·voff, pfet toxe·vth0·voff·nfactor).
- 새 파일 키: `L·VGS·VDS·VS`, `w_ref_m`, `corner`, `temp_c`, kind 마다 변수별 `DVGS_<변수><접미사>`[L, VGS, VDS, VS], `meta_json`(`cap_npz_sha256`, `variables`{소자: [변수]}, `sigma_unit`,
  `sigma_unit_source`(all.spice 경로·sha256), `slope_ref`{소자: {L(µm 글자, 오름차순): {model, 변수: {slope 이름, value} 또는 None}}} = 앵커 L 마다 기준 폭 bin 이 쓴 slope, `ref_id_repro_rel_max` = 기준 곡선 ID 와 기준 LUT ID 열의
  최대 상대차(0 이어야 같은 넷리스트), 모델 파일 sha256, ngspice 버전, 온도, 조합 기록). 기존 r2 파일은 고치지 않는다. 한계: 기준 폭(5 µm)에서만 잰다.
- 거부(`SchemaRejectedError`): meta 키 없음 `lut_mismatch_meta_invalid`(앵커 수와 `slope_ref` 개수 불일치 포함), 기준 LUT 가 다름 `lut_mismatch_cap_mismatch`, 측정 조건 다름 `lut_conditions_mismatch`,
  축·기준 폭 다름 `lut_mismatch_axes_mismatch`, 열 없음/모양 다름 `lut_mismatch_column_missing`·`lut_mismatch_shape_mismatch`.
- [실측 2026-10-08] 생성기 `mismatch` 모드, 조합 360(nfet 180 + pfet 180), 조합당 ngspice 4~5회(기준 곡선 1 + 변수 nfet 3·pfet 4) × op 2401점, 병렬 6. 소요: 벽시계 약 79 분(20:01~21:20, 같은 부하 조건, 한 번 중단 후 체크포인트 재개). 기준 곡선 ID 가 기준 LUT ID 열과 비트 동일(`ref_id_repro_rel_max` = 0.0). NaN 칸 4.04 %(전 변수 공통: VDS = 0 열 + 섭동 곡선이 격자 끝 VGS = 1.8 V 를 넘는 최상단 행), voff 는 nfet 2.62 %·pfet 2.04 %, pfet voff 는 모델 카드가 쓰는 slope 가 0 이라 DVGS ≈ 1e-15 V. 파일 `sky130_nfet_pfet_lut_v2_mismatch_r1.npz` 24.4 MB sha256 `dfec7bbf…bf4e`, 같은 생성기 sha256, ngspice-46, TT 27 °C.

### 10.2 조회 `mismatch_dvgs(memo, kind, w_key, L, vgs, vds, vsb) -> MismatchSens(dvgs, slope_ref, w_m)` (`mismatch_query.py`; memo 영역 point)
- `dvgs`{변수: V}·`slope_ref`{변수: 기준 bin 의 slope 값(그 bin 이 변수를 안 쓰면 0.0)} 읽기 전용 매핑. 보간 = (L 4.0 규칙, VGS, VDS, VS) 모든 축 선형. `slope_ref` = 조회 L 아래 앵커의 기록(같은 bin 이라 같다).
- 실패(`SealViolationError`): mismatch 파일 없음 `lut_mismatch_unavailable`, 폭 키 불일치 `lut_column_unavailable`(`column` = "DVGS"), 가중치 0 이 아닌 모서리에 정의 안 된 칸(NaN) `lut_mismatch_undefined`(detail `parameters`),
  L·축 -> 4.0·4.1 사유(context `table` = "mismatch"). 호출 비용 약 102 µs / 275 µs (nmos/pmos, memo 미적중 1회).

### 10.3 허용오차 `tol_mismatch_table(memo, kind) -> TolMismatchTable` (`mismatch_tolerance.py`; memo 영역 derived, 디스크 캐시 대상)
- 셀 (kind, L 앵커, VDS) × 변수: DVGS_k 면의 LOO 선형 오차 ÷ 2^2 의 셀 안 최댓값(V). `.at(L, vds, param)` = `TolVTable.at` 규칙 -- 셀 결합은 `_helpers_loo.table_at` 하나를 부른다(둘째 구현 없음, `value_of` = 그 변수의 `params` 위치 값): 결합 셀이 모두 정의되면 그 최댓값, 하나라도 None 이면 None
  ([LM-1e] M-3; 소비자 `metrics/device_sigma.py` 는 None 이면 `extra = None` → 기존 fail-closed 갈래). 변수가 `params` 밖이면 `ValueError`.
- [실측 2026-10-08] 변수별 셀 최댓값 [V] nmos {'toxe': '3.00e-05', 'voff': '1.14e-04', 'vth0': '2.50e-05'}, pmos {'nfactor': '1.57e-04', 'toxe': '4.31e-05', 'voff': '2.22e-16', 'vth0': '4.82e-05'}. 계산 0.9 s/1.5 s.

### 10.4 소자 σ `mismatch_sigma_vgs(memo, model, kind, w_key, L, vgs, vds, vsb, W) -> MismatchSigma(sigma_v, parts, model)` (`mismatch_sigma.py`; memo 영역 point)

  σ_VGS(W, L, 점) = √(Σ_k (DVGS_k(L, 점) · slope_k(bin(W, L)) / slope_k(bin_ref))²) · √(W_ref / W)   [V, 단일 소자]

- `model` = `core.PdkMismatchModel`(kind 의 것, `decl.mismatch_model(kind)`). `slope_k(bin(W, L))` = 소자 폭 W(모델 카드에 넘기는 인스턴스 `w`, m)·길이 L 이 든 블록(`bin_index` 규칙으로 W bin 먼저, 그 안 L bin;
  블록이 변수를 안 쓰면 0). `slope_k(bin_ref)` = `MismatchSens.slope_ref`. 기하 √(W_ref·L)/√(W·L) = √(W_ref/W).
- 쌍: σ_ΔVGS,pair = √2·σ_VGS, **A_eff(L, gm/ID) = σ_쌍·√(W·L)**(mV·µm)이고 읽는 쪽이 계산한다(열로 저장하지 않는다). 변수별 기여 `parts`(V)는 offset 기여 표용.
- 손계산: 변수 3개 DVGS = (1, 2, 2) mV, 기준 bin slope = 소자 bin slope 이면 W = W_ref 에서 σ = √(1+4+4) = 3 mV, W = 4·W_ref 에서 1.5 mV(√(W_ref/W) = 1/2); 두 번째 변수의 소자 bin slope 가 기준의 2배면
  σ = √(1 + 16 + 4) = √21 mV (W = W_ref); 소자 bin 이 세 번째 변수를 안 쓰면(slope 0) σ = √(1+4) mV.
- 실패: `mismatch_dvgs` 사유, (W, L) 을 품는 블록 없음 `lut_mismatch_no_block`, 기준 bin 이 변수를 안 쓰는데(slope_ref 0) 소자 bin 은 쓰면 `lut_mismatch_slope_unscalable`. `W <= 0` -> `ValueError`.
- [대조 2026-10-08, W = 5 µm, 쌍 A_eff mV·µm, VDS 0.9 V·VS 0] nmos L 0.15: gm/ID 5/10/15/20 = 7.11/8.85/10.47/11.23 | nmos L 0.18: gm/ID 5/10/15/20 = 7.39/9.18/10.33/11.3 | nmos L 0.25: gm/ID 5/10/15/20 = 6.5/7.31/8.49/9.75 | nmos L 0.5: gm/ID 5/10/15/20 = 5.79/6.13/7.73/9.12 | nmos L 1: gm/ID 5/10/15/20 = 6.05/6.51/7.58/8.96 | nmos L 2: gm/ID 5/10/15/20 = 6.12/7.62/9.09/10.27 | nmos L 4: gm/ID 5/10/15/20 = 6.11/6.98/8.32/9.69 | pmos L 0.15: gm/ID 5/10/15/20 = 12.47/12.09/12.08/12.74 | pmos L 0.18: gm/ID 5/10/15/20 = 12.52/12.01/11.98/12.39 | pmos L 0.25: gm/ID 5/10/15/20 = 12.5/11.93/11.86/11.95 | pmos L 0.5: gm/ID 5/10/15/20 = 11.84/11.37/11.25/11.36 | pmos L 1: gm/ID 5/10/15/20 = 9.39/9.05/8.98/9.16 | pmos L 2: gm/ID 5/10/15/20 = 9.34/8.92/8.9/9.33 | pmos L 4: gm/ID 5/10/15/20 = 9.32/8.91/8.9/9.26 (제안서 §0.3 표: n 0.5 µm 5.8/6.0/7.1/8.6, p 0.5 µm 11.9/11.4/11.3/11.4 등과 일치)

### 10.5 필수 검사: `require_lut_data(..., mismatch=True)` -- 9.5.

### 10.6 PDK slope 와 Pelgrom 계수 유도 (참고, 대조용 -- 코드에 박지 않는다)
쌍 A_VT = √2·`vth0_slope`, A_β = √2·`toxe_slope`(%·µm, toxe 는 상대값): nfet 4.75 mV·µm / 0.487 %·µm; pfet L ≥ 0.5 µm 8.28 / 0.628; pfet L < 0.5 µm 10.40 / 0.911 (`vth0_slope1` 7.356e-3, `toxe_slope1` 6.443e-3).
ngspice 쌍 MC(`assets/sky130_pair_mc.py`) 확인: 표본 1000/사례(seed 20261008), nfet W5 L0.5: A_VT mc 4.75(기대 4.75, 비 1.001), native/meter 1.0000, A_eff mc 6.12, all/rss 1.025, A_β mc 0.452(기대 0.487); nfet W5 L1: A_VT mc 4.76(기대 4.75, 비 1.002), native/meter 1.0000, A_eff mc 6.49, all/rss 1.033, A_β mc 0.470(기대 0.487); nfet W5 L0.18: A_VT mc 4.56(기대 4.75, 비 0.961), native/meter 1.0000, A_eff mc 8.05, all/rss 0.962, A_β mc 0.370(기대 0.487); nfet W2 L1: A_VT mc 4.84(기대 4.75, 비 1.020), native/meter 1.0000, A_eff mc 5.94, all/rss 1.012, A_β mc 0.434(기대 0.487); pfet W5 L0.5: A_VT mc 10.14(기대 10.40, 비 0.974), native/meter 1.0000, A_eff mc 11.00, all/rss 0.975, A_β mc 0.843(기대 0.911); pfet W5 L1: A_VT mc 8.62(기대 8.28, 비 1.041), native/meter 1.0000, A_eff mc 9.31, all/rss 1.030, A_β mc 0.553(기대 0.628); pfet W5 L0.18: A_VT mc 9.16(기대 10.40, 비 0.881), native/meter 1.0000, A_eff mc 11.46, all/rss 1.000, A_β mc 0.892(기대 0.911); pfet W2 L1: A_VT mc 8.09(기대 8.28, 비 0.977), native/meter 1.0000, A_eff mc 8.64, all/rss 0.971, A_β mc 0.601(기대 0.628). A_β 는 toxe 만 흔든 σ(ΔVGS) = a + b/(gm/ID) 회귀(gm/ID 5·7·10·12)의 b·√(W·L)이라 근사다(제안서 §0.3 의 같은 회귀 결과 n 0.45–0.52·p 0.56–0.59(L ≥ 1)·0.88–1.16(L ≤ 0.5)과 같은 범위). LUT 감도 열로 합성한 A_eff 와 같은 점(다이오드 접속 VDS = VGS, 같은 전류밀도)의 쌍 MC 비교: nmos W5 L0.5: LUT 6.04 / MC 6.12 (비 1.014, 모델 블록 model.24); nmos W5 L1: LUT 6.33 / MC 6.49 (비 1.025, 모델 블록 model.23); nmos W5 L0.18: LUT 8.59 / MC 8.05 (비 0.938, 모델 블록 model.26); nmos W2 L1: LUT 6.35 / MC 5.94 (비 0.935, 모델 블록 model.41); pmos W5 L0.5: LUT 11.37 / MC 11.00 (비 0.967, 모델 블록 model.24); pmos W5 L1: LUT 9.06 / MC 9.31 (비 1.028, 모델 블록 model.23); pmos W5 L0.18: LUT 12.02 / MC 11.46 (비 0.953, 모델 블록 model.26); pmos W2 L1: LUT 9.05 / MC 8.64 (비 0.955, 모델 블록 model.41). 전체 표·재현 명령·sha256 = `docs/03-analysis/gain-budget-gmid-sizing.u3-lut-pdk-record.md`.
LUT 감도 열의 vth0 성분은 이 값과 같아야 한다(U3 test (c)): nmos W5 L0.5: 4.74; nmos W5 L1: 4.753; nmos W5 L0.18: 4.815; nmos W2 L1: 4.752; pmos W5 L0.5: 10.409; pmos W5 L1: 8.366; pmos W5 L0.18: 9.712; pmos W2 L1: 8.365 mV·µm (기대 = √2·vth0_slope: nfet 4.746, pfet L ≥ 0.5 µm 8.282, L < 0.5 µm 10.403 -- 짧은 채널(L 0.18 µm)에서는 같은 ID 의 ΔVGS 가 ΔVT 와 한 자릿수 % 다르다(pfet 9.71 대 10.40)). 같은 점의 쌍 MC 와 A_eff 비 MC/LUT = 1.014, 1.025, 0.938, 0.935, 0.967, 1.028, 0.953, 0.955

## 15. [WB-1 DC 블록] 소자 폭 슬라이스 선택 (설계 40 §3.7-A, interface card 20261104-wb1 §2)

- `finger_slice(lut, kind, L, w_of) -> FingerSlice(m, w_f_m, w_key)`: 도달 가능한 슬라이스(`reachable_slices`: 기준 폭 슬라이스의 W bin 위 끝 `w_bin[1]` 이하, W_min 이상, L 을 품는 bin 이 있을 때)마다 `w_of(키)` = 그 슬라이스에서의 총 폭을
  받아 x = W/(키·g), k = floor(x), k = 0 이면 m = 1 아니면 x − k ≤ k + 1 − x 일 때 m = k 아니면 k + 1, 잔차 |(m·키)·g/W − 1| 최소(동률은 큰 키)로 고른다. `w_of` 가 None·비유한·≤ 0 이면 그 키를 뺀다.
  후보 없음 `slice_missing`(`why` = `no_w_hi`·`no_candidate`, `excluded`). 저장 0, graph 읽지 않음.
- `slice_of_finger(lut, kind, L, w_f_m) -> 키`: 격자 정수 키가 `widths(lut, kind)` 에 있을 때만, 아니면 `slice_missing`(LUT 값 조회 0).
- `is_slice_gap(exc)`·`SLICE_GAP_REASONS`: 조회 불능 사유 다섯(`lut_axis_out_of_range`, `lut_l_not_anchor`, `lut_l_outside_model_bins`, `lut_l_bin_unbracketed`, `lut_l_cross_bin`).
- `build_slice_tables(memo) -> int`: `widths` 키마다 tol_V 표·(VDSAT 열이 있으면) tol_VDsat 표 구성.
- [M-TH1c] tol_V 지표는 `id_equivalent` 하나(`TOL_V_METRICS`): `TolVCell(id_equivalent_v, id_equivalent_loo_v)`, `MidpointRow(model, L_points, id_equivalent_v, vdsat_v)`.
  `strong_inversion_root` 정의는 `vgs_root.py`, `branch_targets` 삭제.
