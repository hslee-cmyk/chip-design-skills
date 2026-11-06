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
* [LM-1e] `verify_midpoints` 인자: bin 검증 중점 파일들의 sequence(선택, 파일마다 DC 슬라이스 npz 꼴 -- 폭 `W`·중점 `L`·meta `device`) -- 파일마다
  짝 슬라이스(meta `device` 와 폭 키가 같은 manifest 슬라이스)를 찾고 관문 G0~G4c(`_midpoint_source`)를 지나면 `SliceSource`(sha256 = 파일 raw 바이트)로 출처에 싣는다
  (축·조건·열 검사 G5~G7b 는 `load_lut_set`).
* [r7] `noise_npz`·`mismatch_npz` 인자: 잡음 r1·mismatch 감도 r1 파일(선택) -- 경로와 sha256 을 출처에 싣는다(파일 없음 ->
  `lut_noise_missing`·`lut_mismatch_missing`, 내용 검사는 `load_lut_set`).
* [WB-1 범위 0] `bin_rule` 인자(필수): bin 규칙 선언 파일(스키마 `lut_bin_rule/1`, DEC-105 (2)). 엔진이 읽는 칸은 `rule`·
  `model_files_sha256`·`simulator` 뿐이다. 세트(슬라이스 파일마다·`cap`·`noise`·`mismatch`)마다 meta 의 모델 파일 sha256 묶음이 선언 안인지,
  meta `ngspice`(`<이름>-<판>`, 마지막 `-` 로 나눔)가 선언 `simulator` 와 같은지 대조하고 어긋나면 `bin_tie_undeclared`(detail `set`,
  `why`). 기록 sha256 이 선언 밖이어도 그 모델 파일의 raw 바이트 sha256 이 기록값이고 LF 환산 값이 선언 안이면 통과하고 (세트, 상대 경로)를
  `bin_rule_machine_dependent` 에 싣는다(줄바꿈이 다른 기계). 선언 파일의 LF sha256 은 지문 항목(`bin_rule_sha256`)이다.
"""
import hashlib
import json
import os

import numpy as np

from gmid_engine.core import file_sha256, sorted_items

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


def _midpoint_source(path, manifest_generator, grid_m, pairs, seen):
    """중점 파일 하나의 `SliceSource`(관문 G0~G4c, 위에서 아래로 첫 맞는 행에서 거부 -- detail 에 `path`).

    `pairs` = {(슬라이스 파일 meta `device`, 폭 키): (kind, manifest device, 슬라이스 meta)}, `seen` = 이미 짝이 된 (kind, 폭 키) 집합(호출자가 갱신).
    G0 파일 없음 `lut_midpoints_missing`, G1 `W` 없음 `lut_midpoints_width_missing`, G1b `W` 제조 격자 밖 `lut_width_off_grid`, G1c `L` 원소가
    제조 격자 밖(폭 관문과 같은 판정) `lut_midpoints_l_off_grid`, G2 meta `device` 없음·짝 슬라이스 없음 `lut_midpoints_slice_unmatched`, G3 같은
    (kind, 폭 키) 둘 이상 `lut_slice_duplicate`, G4 생성기 sha256 ≠ manifest 값(manifest 에 없으면 언제나)·G4b 모델 파일 sha256 ≠ 짝 슬라이스·G4c 시뮬레이터 판
    ≠ 짝 슬라이스 `lut_conditions_mismatch`(detail key). 옛 `L_source` 는 읽지 않는다.
    """
    if not os.path.isfile(path):
        raise schema_rejected("lut_midpoints_missing", path=str(path))
    with np.load(path) as npz:
        if "W" not in npz.files:
            raise schema_rejected("lut_midpoints_width_missing", path=str(path))
        w_m = float(npz["W"])
        w_key, on_grid = width_key(w_m, grid_m)
        if not on_grid:
            raise schema_rejected("lut_width_off_grid", path=str(path), w_m=w_m, grid_m=grid_m)
        for l_m in (float(x) for x in np.asarray(npz["L"], dtype=float)) if "L" in npz.files else ():
            if not width_key(l_m, grid_m)[1]:
                raise schema_rejected("lut_midpoints_l_off_grid", path=str(path), L_m=l_m, grid_m=grid_m)
        meta = json.loads(str(npz["meta_json"])) if "meta_json" in npz.files else {}
        conditions = _conditions(npz)
    device = meta.get("device")
    pair = pairs.get((device, w_key)) if device is not None else None
    if pair is None:
        raise schema_rejected("lut_midpoints_slice_unmatched", path=str(path), device=device, w_key=w_key)
    kind, manifest_device, pair_meta = pair
    if (kind, w_key) in seen:
        raise schema_rejected("lut_slice_duplicate", path=str(path), set="midpoints", kind=kind, w_key=w_key)
    seen.add((kind, w_key))
    recorded = sorted_items(meta.get("model_files_sha256") or {})
    for key, got, want in (("generator_sha256", meta.get("generator_sha256"), manifest_generator),
                           ("model_files_sha256", recorded, sorted_items(pair_meta.get("model_files_sha256") or {})),
                           ("ngspice", meta.get("ngspice"), pair_meta.get("ngspice"))):
        if want is None or got != want:
            raise schema_rejected("lut_conditions_mismatch", path=str(path), key=key, midpoints=got, slice=want)
    return SliceSource(kind, manifest_device, w_m, w_key, os.path.abspath(path), _sha256_of(path), conditions, recorded, ())


def _extra_file(path, reason):
    """선택 파일의 (절대 경로, sha256), 없으면 (None, None). 파일이 없으면 `reason` 으로 거부."""
    if path is None:
        return None, None
    if not os.path.isfile(path):
        raise schema_rejected(reason, path=str(path))
    return os.path.abspath(path), _sha256_of(path)


_BIN_RULE_SCHEMA = "lut_bin_rule/1"
_BIN_RULES = ("lower", "upper")


def _undeclared(set_name, why, **extra):
    return schema_rejected("bin_tie_undeclared", set=set_name, why=why, **extra)


def _read_bin_rule(path):
    """선언 파일 -> (rule, 모델 파일 LF sha256 frozenset, (시뮬레이터 이름, 판), 선언 LF sha256). 실패 `bin_tie_undeclared`
    (why `decl_missing`: 경로 None·파일 없음, `decl_invalid`: JSON 오류·스키마·`rule`·`model_files_sha256`·`simulator` 위반)."""
    if path is None or not os.path.isfile(path):
        raise _undeclared("decl", "decl_missing", path=str(path))
    try:
        with open(path, encoding="utf-8") as fh:
            decl = json.load(fh)
    except ValueError as exc:
        raise _undeclared("decl", "decl_invalid", path=str(path), error=str(exc)) from exc
    is_dict = isinstance(decl, dict)
    sim = decl.get("simulator") if is_dict else None
    shas = decl.get("model_files_sha256") if is_dict else None
    if (not is_dict or decl.get("schema") != _BIN_RULE_SCHEMA or decl.get("rule") not in _BIN_RULES
            or not isinstance(shas, list) or not shas or not all(isinstance(s, str) for s in shas)
            or not isinstance(sim, dict) or not all(isinstance(sim.get(k), str) and sim.get(k) for k in ("name", "version"))):
        raise _undeclared("decl", "decl_invalid", path=str(path))
    return decl["rule"], frozenset(shas), (sim["name"], sim["version"]), file_sha256(path)


def _meta_of_npz(path):
    with np.load(path) as npz:
        return json.loads(str(npz["meta_json"])) if "meta_json" in npz.files else {}


def _recorded_model_shas(meta):
    """meta `model_files_sha256` 의 ((상대 경로, sha256), ...) 정렬 중복 제거. 평탄 {경로: 값} 또는 kind 아래 중첩 {kind: {경로: 값}}."""
    out = set()
    for key, value in sorted_items(meta.get("model_files_sha256") or {}):
        if isinstance(value, dict):
            out.update((str(rel), str(sha)) for rel, sha in value.items())
        else:
            out.add((str(key), str(value)))
    return tuple(sorted(out))


def _file_digests(path, cache):
    """모델 파일의 (raw 바이트 sha256, LF 환산 sha256). 같은 파일은 한 호출에서 한 번만 읽는다."""
    if path not in cache:
        with open(path, "rb") as fh:
            data = fh.read()
        cache[path] = (hashlib.sha256(data).hexdigest(), hashlib.sha256(data.replace(b"\r\n", b"\n")).hexdigest())
    return cache[path]


def _check_set(name, meta, decl, pdk_root, cache):
    """세트 `name` 의 meta 기록이 선언 안인지 대조. 통과하면 이 세트의 기계 의존 ((세트, 상대 경로), ...)."""
    _rule, shas, simulator, _decl_sha = decl
    pairs = _recorded_model_shas(meta)
    if not pairs:
        raise _undeclared(name, "model_unrecorded")
    text = meta.get("ngspice")
    if not isinstance(text, str):
        raise _undeclared(name, "simulator_unrecorded")
    sim_name, sep, version = text.rpartition("-")
    if not sep or not sim_name or not version:
        raise _undeclared(name, "simulator_unparsed", recorded=text)
    if (sim_name, version) != simulator:
        raise _undeclared(name, "simulator_differs", recorded=text, declared="%s-%s" % simulator)
    root = meta.get("pdk_root") if pdk_root is None else pdk_root
    machine = []
    for rel, recorded in pairs:
        if recorded in shas:
            continue
        if not root:
            raise _undeclared(name, "model_root_missing", model=rel)
        path = os.path.join(root, rel)
        if not os.path.isfile(path):
            raise _undeclared(name, "model_file_missing", model=rel, path=path)
        raw, lf = _file_digests(path, cache)
        if raw == recorded and lf in shas:
            machine.append((name, rel))
            continue
        raise _undeclared(name, "model_undeclared", model=rel, recorded=recorded)
    return tuple(machine)


def lut_provenance(manifest_path, cap_npz_path, spec, *, bin_rule, pdk_root=None, verify_midpoints=None, noise_npz=None,
                   mismatch_npz=None):
    """manifest 와 기준 LUT(`cap_npz_path`) 의 출처를 읽어 `LutProvenance` 로 돌려준다.

    슬라이스 소자 이름은 `spec.device_kinds` 로 kind 를 정한다(선언 밖 소자는 거부). 폭 키는
    `round(W / spec.manufacturing_grid_m)` 이고, 파일의 W(m) 와 키·격자 곱의 차가 float 반올림 3회(곱·격자·나눗셈)의
    상계 `2 * ulp(W / grid)` 를 넘으면 거부한다(폭이 제조 격자 위에 있지 않은 파일).
    `bin_rule`(필수): bin 규칙 선언 파일 경로(모듈 docstring, 실패 `bin_tie_undeclared`).
    `pdk_root`: 모델 파일을 찾을 PDK 루트(None = 슬라이스 meta 값). `verify_midpoints`: 검증 중점 파일 경로 sequence(None·빈 sequence = 없음,
    문자열 하나 -> `TypeError`) -- 파일마다 짝 슬라이스 하나(`_midpoint_source`), 결과 `LutProvenance.midpoint_sources`.
    `noise_npz`·`mismatch_npz`: 잡음 r1·mismatch 감도 r1 파일 경로(None = 없음).
    """
    if isinstance(verify_midpoints, (str, bytes, os.PathLike)):
        raise TypeError("lut_provenance: verify_midpoints 는 경로 sequence(문자열 하나가 아님)")
    midpoint_paths = tuple(verify_midpoints or ())
    decl = _read_bin_rule(bin_rule)
    if not os.path.isfile(manifest_path):
        raise schema_rejected("lut_manifest_missing", path=str(manifest_path))
    with open(manifest_path, encoding="utf-8") as fh:
        manifest = json.load(fh)
    base = os.path.dirname(os.path.abspath(manifest_path))
    kinds = dict(spec.device_kinds)
    grid_m = spec.manufacturing_grid_m
    slices = []
    set_metas = []
    seen = set()
    pairs = {}
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
        pairs.setdefault((meta.get("device"), w_key), (key[0], device, meta))
        set_metas.append((os.path.basename(path), meta))
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
        set_metas.append(("cap", json.loads(str(npz["meta_json"])) if "meta_json" in npz.files else {}))
    paired = set()
    mid = tuple(sorted((_midpoint_source(p, manifest.get("generator_sha256"), grid_m, pairs, paired) for p in midpoint_paths),
                       key=lambda s: (s.kind, s.w_key)))
    noise = _extra_file(noise_npz, "lut_noise_missing")
    mismatch = _extra_file(mismatch_npz, "lut_mismatch_missing")
    for set_name, extra_path in (("noise", noise[0]), ("mismatch", mismatch[0])):
        if extra_path is not None:
            set_metas.append((set_name, _meta_of_npz(extra_path)))
    cache = {}
    machine = tuple(sorted(pair for name, meta in set_metas for pair in _check_set(name, meta, decl, pdk_root, cache)))
    return LutProvenance(
        os.path.abspath(manifest_path), _sha256_of(manifest_path), str(manifest.get("generator_sha256")),
        tuple(sorted(slices, key=lambda s: (s.kind, s.w_key))),
        os.path.abspath(cap_npz_path), _sha256_of(cap_npz_path), cap_conditions, mid,
        *noise, *mismatch,
        bin_rule=decl[0], bin_rule_sha256=decl[3], bin_rule_machine_dependent=machine,
    )
