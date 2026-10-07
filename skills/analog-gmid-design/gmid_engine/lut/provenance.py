"""LUT 출처 읽기 -- manifest·슬라이스·기준 LUT 파일의 sha256 대조와 측정 조건 (설계 MOD1 2.5, I-A5).

진입점: `lut_provenance`.

* manifest(`manifest.json`, 슬라이스 생성기 산출)의 `slices[*]` 마다 파일 sha256 을 다시 재서 manifest 값과
  대조한다. 다르거나 파일이 없으면 `SchemaRejectedError`(로드 게이트 거부).
* 측정 조건은 옛 `lut_conditions_from_npz`(SR:4782) 본문 그대로 복사한 `_lut_conditions_from_npz` 로 읽는다
  (옛 엔진은 운영 경로에서 안 불렀다 -- 여기서 S0 지문 조립에 배선한다). 기록이 없으면 `recorded=False` 를
  그대로 싣는다(값을 지어내지 않는다).
* 경로는 인자로만 받는다(폴더 경로를 코드에 두지 않는다).
* 모델 파일(L bin 지도의 원천, lut/CONTRACT.md 4.0): 슬라이스 meta 의 `model_files_sha256`(상대 경로 -> sha256)
  파일을 meta `pdk_root` 아래에서 찾아 sha256 을 대조하고 `SliceSource.model_paths` 에 싣는다. 기록이 있는데
  `pdk_root` 가 없거나·파일이 없거나·sha256 이 다르면 거부(같은 파일은 한 호출에서 한 번만 잰다).
* [r6] `pdk_root` 인자: 주면 meta 의 절대 `pdk_root` 대신 그 폴더 아래에서 모델 파일을 찾는다(데이터·PDK 를 다른 기계·
  폴더로 옮겨도 sha256 대조는 그대로 -- 경로는 지문에 들어가지 않는다). 주지 않으면 meta 값(r5 그대로).
* [r6] `verify_midpoints` 인자: bin 검증 중점 파일(선택) -- 파일 sha256 과 meta `L_source` 를 출처에 싣는다(내용 검사는
  `load_lut_set`).
"""
import hashlib
import json
import os

import numpy as np

from gmid_engine.core import sorted_items

from ._helpers_fail import schema_rejected
from ._helpers_width import width_key
from .lut_types import LutProvenance, SliceSource


def _sha256_of(path):
    with open(path, "rb") as fh:
        return hashlib.file_digest(fh, "sha256").hexdigest()


def _lut_conditions_from_npz(npz_data) -> dict:
    """npz 의 측정 조건(corner·temp_c) dict, 기록이 없으면 recorded=False (복사본 -- 본문은 옛 4782행)."""
    files = set(getattr(npz_data, "files", []) or [])
    if "corner" in files or "temp_c" in files:
        out = {"recorded": True}
        if "corner" in files:
            out["corner"] = str(npz_data["corner"])
        if "temp_c" in files:
            out["temp_c"] = float(npz_data["temp_c"])
        return out
    return {"recorded": False,
            "note": "이 LUT 파일에 코너/온도가 기록돼 있지 않다 -- 사이징 결과가 어느 조건에서 "
                    "유효한지 추적할 수 없다. sky130_lut_sweep.py로 재생성하면 기록된다(A5)."}


def _conditions(npz):
    return sorted_items(_lut_conditions_from_npz(npz))


def _model_paths(meta, slice_path, digests, pdk_root):
    """meta 의 모델 파일 기록을 실제 경로로 풀고 sha256 대조. `digests` = 이 호출의 {경로: sha256} (같은 파일 1회).
    `pdk_root` 가 None 이 아니면 meta `pdk_root` 대신 쓴다."""
    recorded = sorted_items(meta.get("model_files_sha256") or {})
    if not recorded:
        return ()
    root = meta.get("pdk_root") if pdk_root is None else pdk_root
    if not root:
        raise schema_rejected("lut_model_root_missing", path=slice_path)
    out = []
    for rel, want in recorded:
        path = os.path.join(root, rel)
        if not os.path.isfile(path):
            raise schema_rejected("lut_model_file_missing", path=path, slice=slice_path)
        if path not in digests:
            digests[path] = _sha256_of(path)
        if digests[path] != want:
            raise schema_rejected("lut_model_file_sha256_mismatch", path=path, recorded=str(want),
                                  actual=digests[path], slice=slice_path)
        out.append((rel, path))
    return tuple(out)


def _midpoints(path):
    """중점 파일의 (절대 경로, sha256, meta L_source 쌍 tuple, 측정 조건). 파일 없음 -> `lut_midpoints_missing`."""
    if not os.path.isfile(path):
        raise schema_rejected("lut_midpoints_missing", path=str(path))
    with np.load(path) as npz:
        meta = json.loads(str(npz["meta_json"])) if "meta_json" in npz.files else {}
        conditions = _conditions(npz)
    return os.path.abspath(path), _sha256_of(path), sorted_items(meta.get("L_source") or {}), conditions


def lut_provenance(manifest_path, cap_npz_path, spec, *, pdk_root=None, verify_midpoints=None):
    """manifest 와 기준 LUT(`cap_npz_path`) 의 출처를 읽어 `LutProvenance` 로 돌려준다.

    슬라이스 소자 이름은 `spec.device_kinds` 로 kind 를 정한다(선언 밖 소자는 거부). 폭 키는
    `round(W / spec.manufacturing_grid_m)` 이고, 파일의 W(m) 와 키·격자 곱의 차가 float 반올림 3회(곱·격자·나눗셈)의
    상계 `2 * ulp(W / grid)` 를 넘으면 거부한다(폭이 제조 격자 위에 있지 않은 파일).
    `pdk_root`: 모델 파일을 찾을 PDK 루트(None = 슬라이스 meta 값). `verify_midpoints`: 검증 중점 파일 경로(None = 없음).
    """
    if not os.path.isfile(manifest_path):
        raise schema_rejected("lut_manifest_missing", path=str(manifest_path))
    with open(manifest_path, encoding="utf-8") as fh:
        manifest = json.load(fh)
    base = os.path.dirname(os.path.abspath(manifest_path))
    kinds = dict(spec.device_kinds)
    grid_m = spec.manufacturing_grid_m
    slices = []
    seen = set()
    digests = {}
    for row in manifest.get("slices") or ():
        device = row.get("device")
        if device not in kinds:
            raise schema_rejected("lut_device_undeclared", device=str(device))
        path = os.path.join(base, row["file"])
        if not os.path.isfile(path):
            raise schema_rejected("lut_slice_missing", path=path)
        digest = _sha256_of(path)
        if digest != row.get("sha256"):
            raise schema_rejected("lut_slice_sha256_mismatch", path=path, manifest=str(row.get("sha256")), actual=digest)
        with np.load(path) as npz:
            w_m = float(npz["W"])
            meta = json.loads(str(npz["meta_json"]))
            conditions = _conditions(npz)
        w_key, on_grid = width_key(w_m, grid_m)
        if not on_grid:
            raise schema_rejected("lut_width_off_grid", path=path, w_m=w_m, grid_m=grid_m)
        key = (kinds[device], w_key)
        if key in seen:
            raise schema_rejected("lut_slice_duplicate", kind=key[0], w_key=w_key)
        seen.add(key)
        slices.append(SliceSource(
            kinds[device], device, w_m, w_key, path, digest, conditions,
            sorted_items(meta.get("model_files_sha256") or {}),
            _model_paths(meta, path, digests, pdk_root),
        ))
    if not slices:
        raise schema_rejected("lut_manifest_empty", path=str(manifest_path))
    if not os.path.isfile(cap_npz_path):
        raise schema_rejected("lut_cap_missing", path=str(cap_npz_path))
    with np.load(cap_npz_path) as npz:
        cap_conditions = _conditions(npz)
    mid = (None, None, (), ()) if verify_midpoints is None else _midpoints(verify_midpoints)
    return LutProvenance(
        os.path.abspath(manifest_path), _sha256_of(manifest_path), str(manifest.get("generator_sha256")),
        tuple(sorted(slices, key=lambda s: (s.kind, s.w_key))),
        os.path.abspath(cap_npz_path), _sha256_of(cap_npz_path), cap_conditions, *mid,
    )
