"""mismatch 감도 r1 파일 로드 -- 새 버전 파일(`..._mismatch_r1.npz`)의 DVGS 열을 kind 마다 `MismatchTable` 로 (설계 41 §6.4-2b,
lut/CONTRACT.md 10.1).

진입점: `load_mismatch_tables`.

* 새 파일은 생성기 `sky130_lut_sweep.py mismatch` 산출이다: 축 `L·VGS·VDS·VS`(기준 LUT 와 float 단위로 같아야 함), 기준 폭 `w_ref_m`,
  kind 마다 변수별 `DVGS_<변수><접미사>`[L, VGS, VDS, VS](V; 변수의 `*_slope_spectre` 를 0 → 1σ 로 바꾼 섭동 곡선이 기준 곡선 ID 에서 내는
  |VGS| 차, 정의 안 되는 칸 NaN), meta(`cap_npz_sha256`, `variables`{소자: [변수]}, `sigma_unit`, `slope_ref`{소자: {L(µm 글자): {model,
  변수: {slope, value} 또는 None}}}).
* `slope_ref` 는 L 앵커마다의 기준 폭 bin 이 쓴 slope 이름·값(생성기가 모델 카드·mismatch 파일에서 읽어 기록)이고, 소자 폭이 다른 bin 이면
  PDK 선언의 bin 지도(`core.read_pdk_decl` 의 mismatch 모델)로 slope 를 다시 읽는다(`mismatch_sigma_vgs`).
* 거부(`SchemaRejectedError`): 파일 형식 `lut_mismatch_meta_invalid`, 기준 LUT 가 다름 `lut_mismatch_cap_mismatch`, 축·폭 다름
  `lut_mismatch_axes_mismatch`, 측정 조건 다름 `lut_conditions_mismatch`, 열 없음/모양 다름 `lut_mismatch_column_missing`·
  `lut_mismatch_shape_mismatch`.
"""
import json
import types

import numpy as np

from ._helpers_fail import schema_rejected
from ._helpers_grids import npz_condition_mismatch, npz_grids
from .lut_types import MismatchTable

_COLUMN = "DVGS_"


def _anchor_slopes(slope_ref, device, n_anchors, variables, path):
    """L 앵커마다 ((변수, slope 이름 또는 None, slope 값 또는 None), ...). 생성기가 앵커 L 오름차순으로 적은 `slope_ref[소자]` 의
    순서가 앵커 순서다(개수가 L 축과 다르면 거부)."""
    entries = list(slope_ref[device].values())
    if len(entries) != n_anchors:
        raise schema_rejected("lut_mismatch_meta_invalid", path=path, missing="slope_ref %s: %d != %d anchors"
                              % (device, len(entries), n_anchors))
    rows = []
    for entry in entries:
        cells = []
        for var in variables:
            found = entry.get(var)
            cells.append((var, None, None) if found is None else (var, str(found["slope"]), float(found["value"])))
        rows.append(tuple(cells))
    return tuple(rows)


def load_mismatch_tables(spec, prov, caps):
    """mismatch 감도 r1 파일(`prov.mismatch_path`)과 기준 LUT 표 `caps` 로 `{kind: MismatchTable}`(읽기 전용 매핑)."""
    path = prov.mismatch_path
    suffix = dict(spec.cap_column_suffix)
    devices = dict((kind, device) for device, kind in spec.device_kinds)
    out = {}
    with np.load(path) as npz:
        try:
            meta = json.loads(str(npz["meta_json"]))
            bound_cap = meta["cap_npz_sha256"]
            sigma_unit = float(meta["sigma_unit"])
            variables = meta["variables"]
            slope_ref = meta["slope_ref"]
            w_ref = float(npz["w_ref_m"])
        except (KeyError, ValueError) as exc:
            raise schema_rejected("lut_mismatch_meta_invalid", path=path, missing=str(exc)) from exc
        if bound_cap != prov.cap_sha256:
            raise schema_rejected("lut_mismatch_cap_mismatch", path=path, bound=str(bound_cap), cap=prov.cap_sha256)
        bad = npz_condition_mismatch(npz, prov.cap_conditions)
        if bad is not None:
            raise schema_rejected("lut_conditions_mismatch", key=bad[0], mismatch=bad[1], cap=bad[2])
        grids = npz_grids(npz, reason="lut_mismatch_axes_mismatch", path=path)
        shape = tuple(len(g) for g in grids)
        for kind in sorted(caps):
            cap = caps[kind]
            if grids != cap.grids or w_ref != cap.w_ref_m:
                raise schema_rejected("lut_mismatch_axes_mismatch", path=path, kind=kind)
            device = devices[kind]
            params = tuple(sorted(variables[device]))
            dvgs = {}
            for var in params:
                name = _COLUMN + var + suffix[kind]
                if name not in npz.files:
                    raise schema_rejected("lut_mismatch_column_missing", path=path, column=name)
                arr = np.asarray(npz[name], dtype=float)
                if arr.shape != shape:
                    raise schema_rejected("lut_mismatch_shape_mismatch", path=path, column=name)
                arr.setflags(write=False)
                dvgs[var] = arr
            out[kind] = MismatchTable(kind, prov.mismatch_sha256, prov.cap_sha256, cap.grids, params,
                                      types.MappingProxyType(dvgs),
                                      _anchor_slopes(slope_ref, device, len(cap.grids[0]), params, path), sigma_unit,
                                      cap.w_ref_m, cap.w_key, cap.l_bins)
    return types.MappingProxyType(out)
