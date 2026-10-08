"""LUT 묶음 로드 -- DC 폭 슬라이스(manifest) + 기준 LUT 용량 열 -> 불변 `LutSet` (설계 MOD1 2.2·2.4·2.5).

진입점: `load_lut_set`.

* 슬라이스: 파일마다 소자 하나·폭 하나, 배열 `ID·GM·GDS·VTH` `[L, VGS, VDS, VS]`, 값은 그 폭에서의 절댓값.
  모든 슬라이스의 L·VGS·VDS·VS 축이 같아야 하고(정확히 같은 float), 측정 조건(corner·temp_c)이 같아야 한다.
* 기준 LUT(용량): kind 집합 = 슬라이스 kind ∪ `spec.cap_column_suffix` 선언 kind. 그 kind 마다 접미사 선언·슬라이스·
  `CGG<접미사>`·`CGD<접미사>` 열이 모두 있어야 하고(하나라도 없으면 거부 -- fail-closed) `CGS<접미사>`·`CGB<접미사>` 는 있으면 쓴다.
  L·VGS·VDS 축은 슬라이스와 같아야 한다. VS 축은 기준 LUT 의 것(용량 조회의 축 범위).
* 용량 기준 폭 `w_ref_m`(CapTable): (1) 기준 npz 에 `w_ref_m` 기록이 있으면 그 값 (2) 없으면 기준 LUT `ID<접미사>` 와
  같은 kind 슬라이스 `ID` 의 겹치는 격자점(기준 VS 값이 슬라이스 VS 축에 정확히 있는 점, 기준 ID > 0)에서 최대 상대
  차(분모 |기준 ID|)가 가장 작은 슬라이스를 고른다. 채택 조건: 그 차가 '고른 슬라이스와 가장 가까운 다른 슬라이스
  사이의 같은 차'(분모 |고른 슬라이스 ID|, 점 = 기준 ID > 0 이고 고른 슬라이스 ID > 0)의 절반보다 작다(기준이 다른 어느 폭보다 그 폭에 가깝다는 것을 데이터가 보일 때만). 슬라이스가 하나뿐이거나 동률,
  조건 불충족이면 로드 거부. 하네스의 박힌 폭 값은 읽지 않는다.
* L bin 지도(`LBinMap`, lut/CONTRACT.md 4.0): 슬라이스가 기록한 모델 파일(`SliceSource.model_paths`)의 `.model` 블록
  중 `lmin`·`lmax`·`wmin`·`wmax` 를 가진 것(bin 블록)을 읽어, 슬라이스 폭 W 를 품는 W bin 행(`_helpers_bins` 규칙 --
  경계 공유 시 아래 bin)의 L bin 들과 L 앵커마다의 소속 bin 을 만든다. 로드 1회 계산, 슬라이스·용량 표에 보관
  (같은 모델 파일은 한 로드에서 한 번만 읽는다). 모델 파일 기록이 없거나 bin 블록이 없으면 빈 지도(L 보간 불가).
  용량 표는 채택 폭과 같은 슬라이스의 지도를 쓴다.
* Hermite 단조 검사(DEC-87, 계획 N3.7, lut/CONTRACT.md 1.4): 슬라이스마다 VGS 축 칸(ln ID, 기울기 GM/ID)과 VDS 축 칸
  (ln ID, 기울기 GDS/ID)의 Fritsch–Carlson 단조 조건을 한 번 계산해 `DcSlice.fc_ok_vgs`·`fc_ok_vds` 에 두고 칸 수·위반 수를
  `hermite_fc` 에 기록한다(로드는 거부하지 않는다 -- 위반 칸은 조회에서 그 축 선형, 역산은 그 칸의 근을 내지 않는다, 4.2).
* [r7] VS 축 Hermite(DEC-87): GMBS 열이 있는 슬라이스는 VS 축 칸(ln ID, 기울기 −GMBS/ID)도 같은 단조 검사를 하고
  (`DcSlice.vs_slope_ok`·`fc_ok_vs`, `hermite_fc` 의 "VS" 항), 슬라이스마다 기울기 열 3개(GM/ID·GDS/ID·GMBS/ID)가 ln ID 격자 차분(현)과
  칸 안 기울기 범위로 맞는지(과반 칸이 모순이면, CONTRACT 1.4) 보고(`_check_units`) 어긋나면 `lut_unit_mismatch` 로 거부한다(41 §4.1 단위 불일치). 잡음 r1·mismatch 감도 r1 파일은
  `noise_set`·`mismatch_set` 이 읽는다.
* [r6] 선택 열(LUT v2): 기준 LUT 의 `CAP_TABLE_COLUMNS`(GMBS·VTH·VDSAT·CDD·CSS·SVG2_1HZ·SVG2_HF·ID·GM·GDS)와 슬라이스의
  `SLICE_OPTIONAL_COLUMNS` 는 있으면 읽고 없으면 비워 둔다(옛 12-L 세트도 그대로 로드 -- 그 열을 쓰는 조회가 구조화된
  `lut_column_unavailable` 로 실패한다, 조용히 대체하지 않는다). 기준 LUT meta 의 부호 규약 문장과 `L_source` 를 표에 싣는다
  (용량 열은 부호 보존 값 그대로 -- 로그·절댓값을 쓰지 않는다). 기준 LUT 폭 키(`CapTable.w_key`)는 슬라이스와 같은 폭 키
  규칙(`_helpers_width`)으로 정하고, bin 지도·열 출처 판정은 float 폭이 아니라 이 키로 같은 폭을 찾는다.
* [r6] 검증 중점 파일(`verify_midpoints`, 선택): 슬라이스와 같은 VGS·VDS·VS 축, 같은 측정 조건, meta `L_source` 에 sha256
  (승인 L 파일), 기준 LUT meta 에 `L_source` sha256 이 있으면 같은 값 -- 아니면 거부. kind 마다 `MidpointTable`.
"""
import json
import math
import re
import types

import numpy as np

from gmid_engine.core import sorted_items

from ._helpers_bins import bin_index
from ._helpers_fail import schema_rejected
from ._helpers_grids import npz_grids
from ._helpers_interp import HERMITE_DEGREE, VS_SLOPE_COLUMN
from ._helpers_width import width_key
from .fingerprint import lut_fingerprint
from .lut_types import (
    AXES,
    CAP_TABLE_COLUMNS,
    SLICE_OPTIONAL_COLUMNS,
    CapTable,
    DcSlice,
    LBin,
    LBinMap,
    LutSet,
    MidpointTable,
)
from .mismatch_set import load_mismatch_tables
from .noise_set import load_noise_tables
from .provenance import lut_provenance

BIN_KEYS = ("lmin", "lmax", "wmin", "wmax")
NO_BINS = LBinMap((), None, (), ())
_MODEL_BLOCK = re.compile(r"^\.model\s+(?P<name>\S+)(?P<body>.*?)(?=^\.model\b|\Z)", re.S | re.I | re.M)
_BIN_VALUE = tuple((k, re.compile(r"\b%s\s*=\s*(?P<value>[-+0-9.eE]+)" % k, re.I)) for k in BIN_KEYS)


def _bin_blocks(path):
    """모델 파일의 bin 블록 tuple: (이름, lmin, lmax, wmin, wmax) m. 키가 일부만 있는 블록은 거부."""
    with open(path, encoding="utf-8", errors="replace") as fh:
        text = fh.read()
    out = []
    for m in _MODEL_BLOCK.finditer(text):
        found = {k: rx.search(m.group("body")) for k, rx in _BIN_VALUE}
        have = tuple(k for k in BIN_KEYS if found[k] is not None)
        if not have:
            continue
        if len(have) != len(BIN_KEYS):
            raise schema_rejected("lut_model_bin_incomplete", path=path, model=m.group("name"), keys=have)
        out.append((m.group("name"),) + tuple(float(found[k].group("value")) for k in BIN_KEYS))
    return tuple(out)


def _l_bin_map(src, l_grid, parsed):
    """슬라이스 `src` 의 `LBinMap`. `parsed` = 이 로드의 {모델 경로: bin 블록} (같은 파일 1회 파싱)."""
    blocks = []
    for _, path in src.model_paths:
        if path not in parsed:
            parsed[path] = _bin_blocks(path)
        blocks.extend(parsed[path])
    if not blocks:
        return NO_BINS
    w_rows = sorted({(b[3], b[4]) for b in blocks})
    j = bin_index(w_rows, src.w_m)
    if j is None:
        raise schema_rejected("lut_model_bins_no_width", path=src.path, w_m=src.w_m)
    row = sorted((b[1], b[2], b[0]) for b in blocks if (b[3], b[4]) == w_rows[j])
    for (_, hi_a, name_a), (lo_b, _, name_b) in zip(row, row[1:]):
        if lo_b < hi_a and abs(hi_a - lo_b) > math.ulp(lo_b):
            raise schema_rejected("lut_model_bins_overlap", path=src.path, w_m=src.w_m, models=(name_a, name_b))
    intervals = tuple((lo, hi) for lo, hi, _ in row)
    anchor_bin = tuple(bin_index(intervals, L) for L in l_grid)
    if None in anchor_bin:
        raise schema_rejected("lut_l_anchor_outside_model_bins", path=src.path, w_m=src.w_m,
                              L=float(l_grid[anchor_bin.index(None)]))
    return LBinMap(tuple(rel for rel, _ in src.model_paths), w_rows[j],
                   tuple(LBin(name, lo, hi) for lo, hi, name in row), anchor_bin)


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


def _fc_monotone(dy, m0, m1, h):
    """2점 cubic-Hermite 칸의 Fritsch–Carlson 단조 조건(필요충분, 원소마다; dy = y1 − y0). 미분 p'(x)·h 의 Bernstein
    계수 b0 = m0·h, b1 = n·dy − (m0 + m1)·h, b2 = m1·h (n = Hermite 차수) 로 쓰면 비감소 ⇔ b0 ≥ 0, b2 ≥ 0,
    (b1 ≥ 0 또는 b1² ≤ b0·b2) 이고 -- Fritsch–Carlson(1980) 의 α = m0/δ, β = m1/δ 단조 영역과 같은 식 -- 비증가는 부호를
    뒤집은 같은 조건이다((−b1)² = b1², (−b0)(−b2) = b0·b2). 둘 중 하나면 단조."""
    b0 = m0 * h
    b2 = m1 * h
    b1 = HERMITE_DEGREE * dy - b0 - b2
    inner = b1 * b1 <= b0 * b2
    rising = (b0 >= 0) & (b2 >= 0) & ((b1 >= 0) | inner)
    falling = (b0 <= 0) & (b2 <= 0) & ((b1 <= 0) | inner)
    return rising | falling


def _fc_ok(log_id, slope, slope_ok, grid, axis):
    """축 `axis` 칸마다 단조 조건 배열(그 축 길이 n − 1), Hermite 칸 수, 위반 칸 수. 두 끝 기울기 자료가 다 있어야
    Hermite 칸이고 아니면 참(그 칸은 선형으로 보간)."""
    lower = tuple(slice(None, -1) if d == axis else slice(None) for d in range(log_id.ndim))
    upper = tuple(slice(1, None) if d == axis else slice(None) for d in range(log_id.ndim))
    both = slope_ok[lower] & slope_ok[upper]
    h = np.diff(np.asarray(grid, dtype=float)).reshape(tuple(-1 if d == axis else 1 for d in range(log_id.ndim)))
    with np.errstate(invalid="ignore", over="ignore"):
        bad = both & ~_fc_monotone(np.diff(log_id, axis=axis), slope[lower], slope[upper], h)
    ok = ~bad
    ok.setflags(write=False)
    return ok, int(both.sum()), int(bad.sum())


def _check_units(path, grids, log_id, pairs):
    """단위 불일치 검사(41 §4.1 '단위 불일치 -> 로드 거부'). 기울기 열(GM/ID·GDS/ID·GMBS/ID) 모두를 같은 규칙으로 검사한다.
    기준은 선택한 십진 수가 아니라 평균값 정리에서 나온다: 격자 칸 [x0, x1] 에서 ln ID 의 현(chord) 기울기 Δln ID/Δx 는 칸 안 어떤 점의 미분이고,
    칸 안에서 미분이 단조이면 두 끝 기울기 m0·m1(저장된 열, 부호 규약 적용) 사이에 든다. 단위·척도가 k 배 틀린 열은 k 가 1 에서 멀수록
    (k − 1 이 칸 안 기울기 변화비보다 크면) 현이 [min(m0,m1), max(m0,m1)] 밖으로 나간다. 그래서 '현이 두 끝 기울기 사이에 들지 않는 칸'
    (부동소수 허용분 eps·(|ln ID| 두 값)/Δx + eps·(|m0| + |m1|) 안은 든 것으로 본다)의 비율을 열마다 재고, **절반을 넘으면**(칸 비율의 중앙값 판정 --
    과반 칸이 모순이면 열 전체의 척도가 틀린 것이다) 거부한다. 검출 한계 = 그 열의 칸 안 기울기 변화(보간 해상도) 그 자체라 상수가 없다.
    정의 마스크가 두 끝에서 참인 칸만 센다. `pairs` = (축, 열 이름, GM/ID 류 양수 비, 정의 마스크, d ln ID/d 축 의 부호)."""
    eps = np.finfo(float).eps
    for axis, name, ratio, ok, sign in pairs:
        nd = log_id.ndim
        lower = tuple(slice(None, -1) if d == axis else slice(None) for d in range(nd))
        upper = tuple(slice(1, None) if d == axis else slice(None) for d in range(nd))
        h = np.diff(np.asarray(grids[axis], dtype=float)).reshape(tuple(-1 if d == axis else 1 for d in range(nd)))
        use = ok[lower] & ok[upper]
        n_use = int(use.sum())
        if n_use == 0:
            continue
        chord = np.diff(log_id, axis=axis) / h
        m0, m1 = sign * ratio[lower], sign * ratio[upper]
        slack = eps * (np.abs(log_id[lower]) + np.abs(log_id[upper])) / h + eps * (np.abs(m0) + np.abs(m1))
        outside = use & ((chord < np.minimum(m0, m1) - slack) | (chord > np.maximum(m0, m1) + slack))
        n_out = int(outside.sum())
        if 2 * n_out > n_use:
            raise schema_rejected("lut_unit_mismatch", path=path, column=name, cells_outside=n_out, cells=n_use)


def _build_slice(src, grids, parsed):
    with np.load(src.path) as npz:
        if npz_grids(npz) != grids:
            raise schema_rejected("lut_slice_axes_mismatch", path=src.path)
        raw_id = np.asarray(npz["ID"], dtype=float)
        raw_gm = np.asarray(npz["GM"], dtype=float)
        raw_gds = np.asarray(npz["GDS"], dtype=float)
        vth = npz["VTH"]
        extra = {name: _readonly(npz[name]) for name in SLICE_OPTIONAL_COLUMNS if name in npz.files}
    shape = tuple(len(g) for g in grids)
    for name, arr in (("ID", raw_id), ("GM", raw_gm), ("GDS", raw_gds), ("VTH", vth)) + tuple(sorted(extra.items())):
        if arr.shape != shape:
            raise schema_rejected("lut_slice_shape_mismatch", path=src.path, array=name)
    log_id, floor_id, np_id = _log_with_floor(raw_id)
    log_gm, floor_gm, np_gm = _log_with_floor(raw_gm)
    log_gds, floor_gds, np_gds = _log_with_floor(raw_gds)
    on_mask = (raw_id > 0) & (raw_gm > 0)
    on_mask.setflags(write=False)
    vds_slope_ok = (raw_id > 0) & (raw_gds > 0)
    vds_slope_ok.setflags(write=False)
    columns = _with_derived(extra, raw_id)
    gm_id, gds_id = np.exp(log_gm - log_id), np.exp(log_gds - log_id)
    ratio = columns.get(VS_SLOPE_COLUMN)                       # GMBS/ID (GMBS 열이 있을 때만)
    vs_slope_ok = np.zeros(shape, dtype=bool) if ratio is None else np.isfinite(ratio) & (ratio > 0)
    vs_slope_ok.setflags(write=False)
    vs_slope = np.zeros(shape) if ratio is None else -np.where(vs_slope_ok, ratio, 0.0)   # d ln ID / d VS = -GMBS/ID
    _check_units(src.path, grids, log_id, ((AXES.index("VGS"), "GM", gm_id, on_mask, 1),
                                           (AXES.index("VDS"), "GDS", gds_id, vds_slope_ok, 1),
                                           (AXES.index("VS"), "GMBS", np.zeros(shape) if ratio is None else np.where(vs_slope_ok, ratio, 0.0), vs_slope_ok, -1)))
    fc_vgs, n_vgs, bad_vgs = _fc_ok(log_id, gm_id, on_mask, grids[1], AXES.index("VGS"))
    fc_vds, n_vds, bad_vds = _fc_ok(log_id, gds_id, vds_slope_ok, grids[2], AXES.index("VDS"))
    fc_vs, n_vs, bad_vs = _fc_ok(log_id, vs_slope, vs_slope_ok, grids[3], AXES.index("VS"))
    return DcSlice(
        src.kind, src.w_key, src.w_m, src.sha256, grids, grids, _readonly(grids[1]),
        _readonly(raw_id), _readonly(vth), on_mask, log_id, log_gm, log_gds,
        (("GDS", floor_gds), ("GM", floor_gm), ("ID", floor_id)),
        (("GDS", np_gds), ("GM", np_gm), ("ID", np_id)),
        _l_bin_map(src, grids[0], parsed),
        vds_slope_ok, fc_vgs, fc_vds, (("VDS", n_vds, bad_vds), ("VGS", n_vgs, bad_vgs), ("VS", n_vs, bad_vs)),
        columns, vs_slope_ok, fc_vs,
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


def _meta_of(npz):
    return json.loads(str(npz["meta_json"])) if "meta_json" in npz.files else {}


def _with_derived(cols, raw_id):
    """선택 열 dict 에 파생 열(`DERIVED_COLUMNS`)을 더한 읽기 전용 매핑. GMBS_PER_ID = GMBS/ID(ID > 0, 아니면 NaN)."""
    if "GMBS" in cols:
        positive = raw_id > 0
        cols["GMBS_PER_ID"] = _readonly(np.where(positive, cols["GMBS"] / np.where(positive, raw_id, 1.0), np.nan))
    return types.MappingProxyType(cols)


def _cap_columns(npz, files, suffix, shape, cap_path):
    """기준 LUT 선택 열 {이름: 읽기 전용 배열}(있는 것만 + 파생 열)과 on_mask((ID > 0) & (GM > 0), 두 열이 없으면 None)."""
    cols = {}
    for name in CAP_TABLE_COLUMNS:
        if name + suffix in files:
            arr = _readonly(npz[name + suffix])
            if arr.shape != shape:
                raise schema_rejected("lut_cap_shape_mismatch", path=cap_path, column=name + suffix)
            cols[name] = arr
    on_mask = None
    if "ID" in cols and "GM" in cols:
        on_mask = (cols["ID"] > 0) & (cols["GM"] > 0)
        on_mask.setflags(write=False)
    return (_with_derived(cols, cols["ID"]) if "ID" in cols else types.MappingProxyType(cols)), on_mask


def _build_caps(spec, cap_path, cap_sha256, grids, slices_by_kind):
    suffix = dict(spec.cap_column_suffix)
    caps = {}
    with np.load(cap_path) as npz:
        cap_grids = npz_grids(npz)
        if cap_grids[:3] != grids[:3]:
            raise schema_rejected("lut_cap_axes_mismatch", path=cap_path)
        files = set(npz.files)
        recorded_w = float(npz["w_ref_m"]) if "w_ref_m" in files else None
        meta = _meta_of(npz)
        sign = meta.get("sign_convention")
        l_source = sorted_items(meta.get("L_source") or {})
        shape = tuple(len(g) for g in cap_grids)
        for kind in sorted(set(slices_by_kind) | set(suffix)):
            if kind not in suffix:
                raise schema_rejected("lut_cap_kind_undeclared", kind=kind)
            if kind not in slices_by_kind:
                raise schema_rejected("lut_cap_kind_without_slices", kind=kind)
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
            w_key, on_grid = width_key(w_ref, spec.manufacturing_grid_m)
            w_key = w_key if on_grid else None
            same_w = [s.l_bins for s in slices_by_kind[kind] if s.w_key == w_key]
            columns, on_mask = _cap_columns(npz, files, suffix[kind], shape, cap_path)
            caps[kind] = CapTable(kind, cap_sha256, cap_grids, cap_grids, _readonly(npz[col["CGG"]]),
                                  _readonly(npz[col["CGD"]]), optional["CGS"], optional["CGB"], w_ref, basis,
                                  same_w[0] if same_w else NO_BINS, w_key, columns, on_mask, sign, l_source)
    return caps


def _midpoint_tables(spec, prov, grids, slice_conditions, caps):
    """검증 중점 파일 -> {kind: MidpointTable}(lut/CONTRACT.md 1.7). 축·조건·L 출처·폭·열 검사(거부 = SchemaRejectedError)."""
    path = prov.midpoints_path
    l_source = dict(prov.midpoints_l_source)
    if not l_source.get("sha256"):
        raise schema_rejected("lut_midpoints_l_source_unrecorded", path=path, l_source=prov.midpoints_l_source)
    for kind, cap in sorted(caps.items()):
        cap_sha = dict(cap.l_source).get("sha256")
        if cap_sha and cap_sha != l_source["sha256"]:
            raise schema_rejected("lut_midpoints_l_source_mismatch", path=path, kind=kind, cap=cap_sha,
                                  midpoints=l_source["sha256"])
    mid_cond = dict(prov.midpoints_conditions)
    if mid_cond.get("recorded"):
        for key in ("corner", "temp_c"):
            if key in mid_cond and mid_cond.get(key) != slice_conditions.get(key):
                raise schema_rejected("lut_conditions_mismatch", key=key, midpoints=mid_cond.get(key),
                                      slices=slice_conditions.get(key))
    suffix = dict(spec.cap_column_suffix)
    out = {}
    with np.load(path) as npz:
        mid_grids = npz_grids(npz)
        if mid_grids[1:] != grids[1:]:
            raise schema_rejected("lut_midpoints_axes_mismatch", path=path)
        if "w_ref_m" not in npz.files:
            raise schema_rejected("lut_midpoints_width_missing", path=path)
        w_m = float(npz["w_ref_m"])
        w_key, on_grid = width_key(w_m, spec.manufacturing_grid_m)
        if not on_grid:
            raise schema_rejected("lut_width_off_grid", path=path, w_m=w_m, grid_m=spec.manufacturing_grid_m)
        shape = tuple(len(g) for g in mid_grids)
        for kind in sorted(caps):
            arrays = {}
            for name in ("ID", "GM", "VDSAT"):
                key = name + suffix[kind]
                if key not in npz.files:
                    if name == "VDSAT":
                        continue
                    raise schema_rejected("lut_midpoints_column_missing", path=path, kind=kind, column=key)
                arrays[name] = np.asarray(npz[key], dtype=float)
                if arrays[name].shape != shape:
                    raise schema_rejected("lut_midpoints_shape_mismatch", path=path, column=key)
            on = (arrays["ID"] > 0) & (arrays["GM"] > 0)
            on.setflags(write=False)
            positive = arrays["ID"] > 0
            safe_id = np.where(positive, arrays["ID"], 1.0)
            log_id = _readonly(np.where(positive, np.log(safe_id), np.nan))
            gm_id = _readonly(np.where(positive, arrays["GM"] / safe_id, np.nan))
            vdsat = _readonly(arrays["VDSAT"]) if "VDSAT" in arrays else None
            out[kind] = MidpointTable(kind, prov.midpoints_sha256, w_m, w_key, mid_grids[0], mid_grids[1:],
                                      log_id, gm_id, on, vdsat)
    return types.MappingProxyType(out)


def load_lut_set(manifest_path, cap_npz_path, spec, *, pdk_root=None, verify_midpoints=None, noise_npz=None,
                 mismatch_npz=None):
    """manifest(슬라이스 목록)·기준 LUT 경로와 `LutSpec` 으로 불변 `LutSet` 을 만든다.

    `pdk_root`: 모델 파일을 찾을 PDK 루트(None = 슬라이스 meta 의 절대 경로). `verify_midpoints`: bin 검증 중점 npz(선택 --
    주면 tol 표의 앵커 2개 bin 외부 값 원천, lut/CONTRACT.md 5.1). [r7] `noise_npz`·`mismatch_npz`: 잡음 r1·mismatch 감도 r1 npz(선택,
    기준 LUT 에 묶임 -- 9.1·10.1; `LutSet.noise`·`LutSet.mismatch`).
    실패(전부 `SchemaRejectedError`, detail.reason 은 CONTRACT.md 1.3·1.4·1.7): manifest·파일 없음, sha256 불일치,
    선언 밖 소자, 폭이 제조 격자 밖, (kind, 폭 키) 중복, 축·형상 불일치, 측정 조건 불일치, 양수 원소 없는 배열,
    용량 열·kind 접미사 없음, 용량 기준 폭 미확정, 모델 파일(bin 지도 원천) 없음·불일치·bin 블록 결함, 중점 파일 결함.
    """
    prov = lut_provenance(manifest_path, cap_npz_path, spec, pdk_root=pdk_root, verify_midpoints=verify_midpoints,
                          noise_npz=noise_npz, mismatch_npz=mismatch_npz)
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
        grids = npz_grids(npz)
    parsed = {}
    slices = [_build_slice(src, grids, parsed) for src in prov.slices]
    by_kind = {}
    for s in slices:
        by_kind.setdefault(s.kind, []).append(s)
    caps = _build_caps(spec, prov.cap_path, prov.cap_sha256, grids, by_kind)
    cap_basis = tuple((kind, caps[kind].w_ref_m, caps[kind].basis) for kind in sorted(caps))
    fp = lut_fingerprint(prov, cap_basis)
    midpoints = (types.MappingProxyType({}) if prov.midpoints_path is None
                 else _midpoint_tables(spec, prov, grids, slice_cond, caps))
    noise = types.MappingProxyType({}) if prov.noise_path is None else load_noise_tables(spec, prov, caps)
    mismatch = types.MappingProxyType({}) if prov.mismatch_path is None else load_mismatch_tables(spec, prov, caps)
    return LutSet(
        spec, prov,
        types.MappingProxyType({(s.kind, s.w_key): s for s in slices}),
        types.MappingProxyType(caps),
        fp,
        midpoints,
        noise,
        mismatch,
    )
