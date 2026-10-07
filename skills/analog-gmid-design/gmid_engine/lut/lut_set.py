"""LUT 묶음 로드 -- DC 폭 슬라이스(manifest) + 기준 LUT 용량 열 -> 불변 `LutSet` (설계 MOD1 2.2·2.4·2.5).

진입점: `load_lut_set`.

* 슬라이스: 파일마다 소자 하나·폭 하나, 배열 `ID·GM·GDS·VTH` `[L, VGS, VDS, VS]`, 값은 그 폭에서의 절댓값.
  모든 슬라이스의 L·VGS·VDS·VS 축이 같아야 하고(정확히 같은 float), 측정 조건(corner·temp_c)이 같아야 한다.
* 기준 LUT(용량): kind 마다 `CGG<접미사>`·`CGD<접미사>` 열이 있어야 하고 `CGS<접미사>`·`CGB<접미사>` 는 있으면 쓴다.
  L·VGS·VDS 축은 슬라이스와 같아야 한다. VS 축은 기준 LUT 의 것(용량 조회의 축 범위).
* 용량 기준 폭 `w_ref_m`(CapTable): (1) 기준 npz 에 `w_ref_m` 기록이 있으면 그 값 (2) 없으면 기준 LUT `ID<접미사>` 와
  같은 kind 슬라이스 `ID` 의 겹치는 격자점(기준 VS 값이 슬라이스 VS 축에 정확히 있는 점, 기준 ID > 0)에서 최대 상대
  차가 가장 작은 슬라이스를 고른다. 채택 조건: 그 차가 '고른 슬라이스와 가장 가까운 다른 슬라이스 사이의 같은 차'의
  절반보다 작다(기준이 다른 어느 폭보다 그 폭에 가깝다는 것을 데이터가 보일 때만). 슬라이스가 하나뿐이거나 동률,
  조건 불충족이면 로드 거부. 하네스의 박힌 폭 값은 읽지 않는다.
"""
import types

import numpy as np

from ._helpers_fail import schema_rejected
from .fingerprint import lut_fingerprint
from .lut_types import CapTable, DcSlice, LutSet
from .provenance import lut_provenance


def _readonly(arr):
    out = np.asarray(arr, dtype=float)
    out.setflags(write=False)
    return out


def _log_with_floor(arr):
    positive = arr[arr > 0]
    if positive.size == 0:
        raise schema_rejected("lut_array_no_positive", size=int(arr.size))
    floor = float(positive.min())
    return _readonly(np.log(np.clip(arr, floor, None))), floor, int(arr.size - positive.size)


def _grids_of(npz):
    return tuple(tuple(float(x) for x in np.asarray(npz[axis], dtype=float)) for axis in ("L", "VGS", "VDS", "VS"))


def _build_slice(src, grids):
    with np.load(src.path) as npz:
        if _grids_of(npz) != grids:
            raise schema_rejected("lut_slice_axes_mismatch", path=src.path)
        raw_id = np.asarray(npz["ID"], dtype=float)
        raw_gm = np.asarray(npz["GM"], dtype=float)
        raw_gds = np.asarray(npz["GDS"], dtype=float)
        vth = npz["VTH"]
    shape = tuple(len(g) for g in grids)
    for name, arr in (("ID", raw_id), ("GM", raw_gm), ("GDS", raw_gds), ("VTH", vth)):
        if arr.shape != shape:
            raise schema_rejected("lut_slice_shape_mismatch", path=src.path, array=name)
    log_id, floor_id, np_id = _log_with_floor(raw_id)
    log_gm, floor_gm, np_gm = _log_with_floor(raw_gm)
    log_gds, floor_gds, np_gds = _log_with_floor(raw_gds)
    on_mask = (raw_id > 0) & (raw_gm > 0)
    on_mask.setflags(write=False)
    return DcSlice(
        src.kind, src.w_key, src.w_m, src.sha256, grids, grids, _readonly(grids[1]),
        _readonly(raw_id), _readonly(vth), on_mask, log_id, log_gm, log_gds,
        (("GDS", floor_gds), ("GM", floor_gm), ("ID", floor_id)),
        (("GDS", np_gds), ("GM", np_gm), ("ID", np_id)),
    )


def _max_rel_diff(a, b, mask):
    return float(np.max(np.abs(a[mask] - b[mask]) / np.abs(b[mask])))


def _cap_width_by_id_match(kind, ref_id, cap_vs, slices):
    if len(slices) == 1:
        raise schema_rejected("lut_cap_width_unresolved", kind=kind, why="single slice")
    vs = np.asarray(slices[0].grids[3])
    cols = []
    for v in cap_vs:
        hit = np.flatnonzero(vs == v)
        if hit.size != 1:
            raise schema_rejected("lut_cap_width_unresolved", kind=kind, why="cap VS not on slice VS axis", vs=v)
        cols.append(int(hit[0]))
    mask = ref_id > 0
    ids = [np.asarray(s.ID)[..., cols] for s in slices]
    dist = [_max_rel_diff(x, ref_id, mask) for x in ids]
    order = sorted(range(len(slices)), key=lambda k: dist[k])
    win = order[0]
    if dist[order[1]] == dist[win]:
        raise schema_rejected("lut_cap_width_unresolved", kind=kind, why="tie")
    win_mask = mask & (ids[win] > 0)
    separation = min(_max_rel_diff(ids[k], ids[win], win_mask) for k in range(len(slices)) if k != win)
    if not dist[win] < separation / 2:
        raise schema_rejected("lut_cap_width_unresolved", kind=kind, why="not separated",
                              best_rel_diff=dist[win], separation=separation)
    chosen = slices[win]
    basis = (("max_rel_diff", dist[win]), ("method", "slice_id_match"), ("nearest_other_rel_diff", separation),
             ("w_key", chosen.w_key))
    return chosen.w_m, basis


def _build_caps(spec, cap_path, cap_sha256, grids, slices_by_kind):
    suffix = dict(spec.cap_column_suffix)
    caps = {}
    with np.load(cap_path) as npz:
        cap_grids = _grids_of(npz)
        if cap_grids[:3] != grids[:3]:
            raise schema_rejected("lut_cap_axes_mismatch", path=cap_path)
        files = set(npz.files)
        recorded_w = float(npz["w_ref_m"]) if "w_ref_m" in files else None
        for kind in sorted(slices_by_kind):
            if kind not in suffix:
                raise schema_rejected("lut_cap_kind_undeclared", kind=kind)
            col = {name: name + suffix[kind] for name in ("CGG", "CGD", "CGS", "CGB", "ID")}
            for need in ("CGG", "CGD"):
                if col[need] not in files:
                    raise schema_rejected("lut_cap_column_missing", kind=kind, column=col[need])
            optional = {name: (_readonly(npz[col[name]]) if col[name] in files else None) for name in ("CGS", "CGB")}
            if recorded_w is not None:
                w_ref, basis = recorded_w, (("method", "recorded_w_ref_m"),)
            elif col["ID"] in files:
                w_ref, basis = _cap_width_by_id_match(
                    kind, np.asarray(npz[col["ID"]], dtype=float), cap_grids[3], slices_by_kind[kind])
            else:
                raise schema_rejected("lut_cap_width_unresolved", kind=kind, why="no w_ref_m and no ID column")
            caps[kind] = CapTable(kind, cap_sha256, cap_grids, cap_grids, _readonly(npz[col["CGG"]]),
                                  _readonly(npz[col["CGD"]]), optional["CGS"], optional["CGB"], w_ref, basis)
    return caps


def load_lut_set(manifest_path, cap_npz_path, spec):
    """manifest(슬라이스 목록)·기준 LUT 경로와 `LutSpec` 으로 불변 `LutSet` 을 만든다.

    실패(전부 `SchemaRejectedError`, detail.reason 은 CONTRACT.md 5절): manifest·파일 없음, sha256 불일치,
    선언 밖 소자, 폭이 제조 격자 밖, (kind, 폭 키) 중복, 축·형상 불일치, 측정 조건 불일치, 양수 원소 없는 배열,
    용량 열·kind 접미사 없음, 용량 기준 폭 미확정.
    """
    prov = lut_provenance(manifest_path, cap_npz_path, spec)
    conditions = {s.conditions for s in prov.slices}
    if len(conditions) != 1:
        raise schema_rejected("lut_conditions_mismatch", conditions=tuple(sorted(conditions)))
    slice_cond = dict(next(iter(conditions)))
    cap_cond = dict(prov.cap_conditions)
    if cap_cond.get("recorded"):
        for key in ("corner", "temp_c"):
            if key in cap_cond and cap_cond.get(key) != slice_cond.get(key):
                raise schema_rejected("lut_conditions_mismatch", key=key, cap=cap_cond.get(key),
                                      slices=slice_cond.get(key))
    with np.load(prov.slices[0].path) as npz:
        grids = _grids_of(npz)
    slices = [_build_slice(src, grids) for src in prov.slices]
    by_kind = {}
    for s in slices:
        by_kind.setdefault(s.kind, []).append(s)
    caps = _build_caps(spec,prov.cap_path, prov.cap_sha256, grids, by_kind)
    cap_basis = tuple((kind, caps[kind].w_ref_m, caps[kind].basis) for kind in sorted(caps))
    fp = lut_fingerprint(prov, cap_basis)
    return LutSet(
        spec, prov,
        types.MappingProxyType({(s.kind, s.w_key): s for s in slices}),
        types.MappingProxyType(caps),
        fp,
    )
