"""잡음 r1 파일 로드 -- 기준 LUT 의 `SVG2_1HZ`·`SVG2_HF` 와 새 버전 파일(`..._noise_r1.npz`)의 로그 이분 주파수 점을 합쳐 kind 마다
`NoiseTable` 로 (설계 41 §7.2, lut/CONTRACT.md 9.1).

진입점: `load_noise_tables`.

* 새 파일은 생성기 `sky130_lut_sweep.py noise` 산출이다: 축 `L·VGS·VDS·VS`(기준 LUT 와 float 단위로 같아야 함), 기준 폭 `w_ref_m`(기준
  LUT 와 같음), 주파수 점 `f_hz`(양끝 사이 이분 점), kind 마다 `SVG2_F<접미사>`[f, L, VGS, VDS, VS], meta(`cap_npz_sha256` = 묶인
  기준 LUT sha256, `base_frequencies_hz` = 기준 LUT 두 점의 주파수). 이 파일은 기준 LUT 를 고치지 않는다.
* 합친 `NoiseTable.S` = [기준 LUT `SVG2_1HZ` (f_lo), r1 점들, 기준 LUT `SVG2_HF` (f_hi)] -- 주파수 오름차순.
* 거부(`SchemaRejectedError`): 파일 형식 `lut_noise_meta_invalid`, 기준 LUT 가 다름 `lut_noise_cap_mismatch`, 축·폭이 다름
  `lut_noise_axes_mismatch`, 측정 조건이 다름 `lut_conditions_mismatch`, 주파수 점이 오름차순·양끝 안쪽이 아님 `lut_noise_frequency_invalid`,
  열 없음/모양 다름 `lut_noise_column_missing`·`lut_noise_shape_mismatch`, 기준 LUT 에 필요한 선택 열(`SVG2_1HZ`·`SVG2_HF`·`GM`) 없음
  `lut_noise_cap_column_missing`, PDK EF 선언 없음 `lut_noise_ef_undeclared`.
"""
import json
import types

import numpy as np

from ._helpers_fail import schema_rejected
from ._helpers_grids import npz_condition_mismatch, npz_grids
from .lut_types import NoiseTable

_CAP_COLUMNS = ("SVG2_1HZ", "SVG2_HF", "GM")                 # 기준 LUT 선택 열(CGD 는 CapTable 필수 열)
_SLICE_COLUMN = "SVG2_F"


def _ascending_inside(extra, f_lo, f_hi):
    pts = (f_lo,) + tuple(extra) + (f_hi,)
    return all(a < b for a, b in zip(pts, pts[1:]))


def load_noise_tables(spec, prov, caps):
    """잡음 r1 파일(`prov.noise_path`)과 기준 LUT 표 `caps`({kind: CapTable})로 `{kind: NoiseTable}`(읽기 전용 매핑).

    `spec.noise_ef` = ((kind, EF), ...) 가 파일에 쓰이는 kind 를 다 덮어야 한다."""
    path = prov.noise_path
    ef = dict(spec.noise_ef)
    suffix = dict(spec.cap_column_suffix)
    out = {}
    with np.load(path) as npz:
        try:
            meta = json.loads(str(npz["meta_json"]))
            base = meta["base_frequencies_hz"]
            f_lo, f_hi = float(base["NOISE_F_PROBE"]), float(base["F_TEST"])
            bound_cap = meta["cap_npz_sha256"]
            extra = tuple(float(x) for x in np.asarray(npz["f_hz"], dtype=float))
            w_ref = float(npz["w_ref_m"])
        except (KeyError, ValueError) as exc:
            raise schema_rejected("lut_noise_meta_invalid", path=path, missing=str(exc)) from exc
        if bound_cap != prov.cap_sha256:
            raise schema_rejected("lut_noise_cap_mismatch", path=path, bound=str(bound_cap), cap=prov.cap_sha256)
        bad = npz_condition_mismatch(npz, prov.cap_conditions)
        if bad is not None:
            raise schema_rejected("lut_conditions_mismatch", key=bad[0], noise=bad[1], cap=bad[2])
        if not _ascending_inside(extra, f_lo, f_hi):
            raise schema_rejected("lut_noise_frequency_invalid", path=path, f_lo=f_lo, f_hi=f_hi, extra=extra)
        grids = npz_grids(npz, reason="lut_noise_axes_mismatch", path=path)
        shape = tuple(len(g) for g in grids)
        for kind in sorted(caps):
            cap = caps[kind]
            if grids != cap.grids or w_ref != cap.w_ref_m:
                raise schema_rejected("lut_noise_axes_mismatch", path=path, kind=kind)
            missing = [c for c in _CAP_COLUMNS if c not in cap.columns]
            if missing:
                raise schema_rejected("lut_noise_cap_column_missing", kind=kind, columns=tuple(missing))
            if kind not in ef:
                raise schema_rejected("lut_noise_ef_undeclared", kind=kind)
            name = _SLICE_COLUMN + suffix[kind]
            if name not in npz.files:
                raise schema_rejected("lut_noise_column_missing", path=path, column=name)
            extra_s = np.asarray(npz[name], dtype=float)
            if extra_s.shape != (len(extra),) + shape:
                raise schema_rejected("lut_noise_shape_mismatch", path=path, column=name)
            s = np.concatenate([cap.columns["SVG2_1HZ"][None], extra_s, cap.columns["SVG2_HF"][None]], axis=0)
            s.setflags(write=False)
            out[kind] = NoiseTable(kind, prov.noise_sha256, prov.cap_sha256, cap.grids, (f_lo,) + extra + (f_hi,), s,
                                   float(ef[kind]), cap.w_ref_m, cap.w_key, cap.l_bins)
    return types.MappingProxyType(out)
