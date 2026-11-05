"""LUT 파생 함수 -- LUT 와 숫자 인자만의 함수를 LUT memo 에 담는다 (설계 40 §2.4.6 'memo 로 옮기는 것', §2.4.8 (a) 행, v1.9.1 D10).

진입점: `derived(memo, name, *args)` -- `name` ∈ `DERIVED_FUNCTIONS`(`edge_costs`·`reference_vds`·`param_row`·`vds_floor`)의 값을 `memo.lookup` 으로 읽는다
(처음이면 계산해 담는다). 호출 형식은 as-built `LutMemo.lookup(region, fn_name, key, compute)` 이고 `memo.call(fn, *args)` 형식 전환은 U17 ③이다.

옮겨 온 것(graph 필드를 읽지 않는 LUT 파생 -- 소자 이름을 키로 하지 않는다):
* `edge_costs`(kind, w_key) -> `EdgeCost` -- 헤드룸 경로 엣지 비용의 LUT 격자 최솟값(설계 41 §4.6, D-GB4f; 옛 `metrics/edge_cost_bounds.py`, 영역 derived).
  * VGS 엣지 비용 = 봉인 9(전도 여유)를 지킬 수 있는 격자 행(강반전 분지 마디)의 |VGS| 최솟값: `I_off ≤ ε·ID`, ε = (gm/ID)·tol_V => `gm·tol_V ≥ I_off`
    (tol_V = `tol_v_table` 의 `id_equivalent_v`, (L 앵커, VDS) 칸; None 이면 그 행은 봉인할 수 없다). VGS = 0 마디는 꺼진 소자라 이 조건이 뺀다.
    (L 앵커, VDS, VS) 곡선마다 조건을 만족하는 첫 마디의 한 칸 아래 VGS 를 L bin 별로 모은다 -- 경로 폭의 **상한**이다. `best_row` = 전체 최솟값 행.
  * VDS 엣지 비용 = 포화 가능 격자점(분지·전도 마디이고 그 격자 VDS ≥ 같은 점 VDSAT -- `sat_threshold_grid`)의 VDSAT 최솟값. tol 합 없음(O-204). 열이 없으면 0.0 이고
    포화 거르기도 없다(DEC-67 상위집합 예외 -- 포화 술어는 VDS ≥ VDSAT).
* `reference_vds`(kind, w_key, L) -> VDS | None -- 출발 구간 곡선의 기준 VDS: VDS 격자 중 엣지 비용 VDS 이상이고 그 (L, VDS, 첫 VS 격자점)에서 vdsat 곡선이
  정의되는 첫 점(옛 `CurveBook.ref_vds`, 영역 curve). VDSAT 열이 없으면 vdsat 곡선 대신 IDu 곡선이 정의되는 첫 점(그 경계만 비활성, 대체값 없음).
* `vds_floor`(kind, w_key) -> float -- 슬라이스의 VDS 정의역 하한: `on_mask` 가 그 VDS 격자 열부터 끝 열까지 모든 (L, VGS, VS) 점에서 참인 첫 VDS 격자값, 없으면 VDS 격자 최소
  (그보다 작은 VDS 는 꺼진 열과 보간되어 gm/ID 곡선 마디가 정의되지 않는다 -- 데이터 사실, 상수 없음; 옛 sizing 안 함수, 영역 derived 슬라이스당 1값).
* `param_row`(kind, w_key, L, vds, vsb) -> ((VGS 마디, ...), x, y, z) | None -- 블록 국소 모델의 소자 파라미터 행: 그 (L, VDS, VS) 의 강반전 분지 VGS 마디에서
  x = gm/ID, y = gds/ID, z = gmb/ID(1/V, 전류 규모와 무관). 곡선을 만들 수 없으면 None(옛 `ParamTables._load`, 영역 curve).
"""
import math

import numpy as np

from gmid_engine.core import SchemaRejectedError, SealViolationError

from .gmb import gmb
from .idu_curve import idu_curve
from .intrinsic_gain_curve import intrinsic_gain_curve
from .lut_types import AXES, EdgeCost
from .point_query import op_point
from .sat_threshold_grid import sat_threshold_grid
from .tolerance import tol_v_table
from .vdsat_curve import vdsat_curve

_UNDEFINED = (SealViolationError, SchemaRejectedError, KeyError, ValueError)
_VDS_AXIS = AXES.index("VDS")


def _conduction_ok(sl, tol):
    """(L, VGS, VDS, VS) 마스크: 분지 마디(VGS ≥ gm/ID 정점) ∧ on ∧ gm·tol_V ≥ I_off (tol 이 정의된 칸만)."""
    on = np.asarray(sl.on_mask, dtype=bool)
    gm_id = np.where(on, np.asarray(sl.log_GM) - np.asarray(sl.log_ID), -np.inf)
    peak = np.argmax(gm_id, axis=1)
    branch = np.arange(on.shape[1])[None, :, None, None] >= peak[:, None, :, :]
    off = np.exp(np.asarray(sl.log_ID))[:, :1]                                # VGS 격자 첫 마디(0 V) 의 ID = I_off
    zero_first = abs(float(sl.grids[1][0])) <= math.ulp(float(np.max(np.abs(sl.grids[1]))))
    gm = np.exp(np.asarray(sl.log_GM))
    ok = branch & on & (gm * tol[:, None, :, None] >= off) if zero_first else branch & on & (gm * tol[:, None, :, None] > 0)
    return ok, branch & on


def _edge_costs(memo, kind, w_key):
    lut = memo.lut
    sl = lut.slice_map[(kind, w_key)]
    table = tol_v_table(memo, kind, w_key)
    n_l, _n_v, n_d, _n_s = (len(g) for g in sl.grids)
    tol = np.full((n_l, n_d), np.nan)
    for i in range(n_l):
        for k in range(n_d):
            v = table.cells[i][k].id_equivalent_v
            if v is not None:
                tol[i, k] = float(v)
    ok, branch_on = _conduction_ok(sl, tol)
    ok &= np.isfinite(tol)[:, None, :, None]
    vgs = np.asarray(sl.grids[1], dtype=float)
    vdsat = sat_threshold_grid(memo, kind, w_key)
    if vdsat is not None:                           # 포화 행만(봉인 7: VDS ≥ VDSAT, 판정 여유 0) -- 모든 MOS 는 기본 포화 의도. 열 없음 = 거르기 없음
        vds = np.asarray(sl.grids[2], dtype=float)[None, None, :, None]
        saturable = vds >= np.asarray(vdsat)
        ok = ok & saturable
    first = np.argmax(ok, axis=1)                                             # 처음 유효 마디 (L, VDS, VS)
    any_ok = ok.any(axis=1)
    below = vgs[np.maximum(first - 1, 0)]                                     # 격자 한 칸 아래(마디 사이 보간 해상도 -- 하한을 낮추는 쪽)
    first_vgs = np.where(any_ok, below, np.inf)
    if not np.isfinite(first_vgs).any():
        raise SchemaRejectedError(detail={"reason": "edge_cost_no_conducting_row", "kind": kind, "w_key": str(w_key)})
    per_l = first_vgs.reshape(n_l, -1).min(axis=1)
    bin_of = tuple(sl.l_bins.anchor_bin) if sl.l_bins.anchor_bin else (0,) * n_l
    by_bin = tuple((int(b), float(per_l[[i for i in range(n_l) if bin_of[i] == b]].min())) for b in sorted(set(bin_of)))
    flat = int(np.argmin(first_vgs))
    i_l, i_d, i_s = np.unravel_index(flat, first_vgs.shape)
    i_v = int(first[i_l, i_d, i_s])
    log_gm, log_id = np.asarray(sl.log_GM), np.asarray(sl.log_ID)
    best = (("L", float(sl.grids[0][i_l])), ("VDS", float(sl.grids[2][i_d])), ("VS", float(sl.grids[3][i_s])),
            ("gm_id", float(np.exp(log_gm[i_l, i_v, i_d, i_s] - log_id[i_l, i_v, i_d, i_s]))))
    vdsat_min = 0.0 if vdsat is None else float(np.min(np.where(branch_on & saturable, np.asarray(vdsat), np.inf)))
    return EdgeCost(kind, w_key, float(first_vgs.min()), by_bin, vdsat_min, best)


def _reference_vds(memo, kind, w_key, L):
    sl = memo.lut.slice_map[(kind, w_key)]
    vsb = float(sl.grids[3][0])
    floor = _lookup(memo, "edge_costs", kind, w_key).vds_min_v
    probe = vdsat_curve if sat_threshold_grid(memo, kind, w_key) is not None else idu_curve      # 열 없음: VDSAT 곡선 대신 같은 (L, VDS, VS) 에서 IDu 곡선이 정의되는 첫 점
    for v in (float(a) for a in sl.grids[2]):
        if v < floor:
            continue
        try:
            return probe(memo, kind, w_key, float(L), v, vsb).vds
        except _UNDEFINED:
            continue
    return None


def _vds_domain_floor(memo, kind, w_key):
    sl = memo.lut.slice_map[(kind, w_key)]
    on = np.asarray(sl.on_mask, dtype=bool)
    full = on.all(axis=tuple(a for a in range(on.ndim) if a != _VDS_AXIS))
    grid = sl.grids[_VDS_AXIS]
    for j in range(len(grid)):
        if bool(full[j:].all()):
            return float(grid[j])
    return float(grid[0])


def _param_row(memo, kind, w_key, L, vds, vsb):
    w_m = memo.lut.slice_map[(kind, w_key)].w_m
    try:
        curve = intrinsic_gain_curve(memo, kind, w_key, L, vds, vsb)
        ids = [op_point(memo, kind, w_key, L, float(v), vds, vsb).IDu * w_m / L for v in curve.vgs]
        body = [gmb(memo, kind, w_key, L, float(v), vds, vsb) for v in curve.vgs]
    except SealViolationError:
        return None
    x = np.asarray(curve.gm_id, dtype=float)
    y = x / np.asarray(curve.values, dtype=float)
    z = np.asarray(body, dtype=float) / np.asarray(ids, dtype=float)
    return (tuple(float(v) for v in curve.vgs), tuple(float(v) for v in x), tuple(float(v) for v in y), tuple(float(v) for v in z))


# (이름, memo 영역, 계산 함수) -- 영역은 LutMemo REGIONS 의 하나: 슬라이스당 하나인 표는 derived(`DERIVED_TABLES` 에 이름이 있다), 축 값 키는 curve
DERIVED_FUNCTIONS = (
    ("edge_costs", "derived", _edge_costs),
    ("reference_vds", "curve", _reference_vds),
    ("param_row", "curve", _param_row),
    ("vds_floor", "derived", _vds_domain_floor),
)


def _lookup(memo, name, *args):
    for known, region, fn in DERIVED_FUNCTIONS:
        if known == name:
            return memo.lookup(region, name, args, lambda: fn(memo, *args))
    raise KeyError("lut.derived: 모르는 파생 함수 " + repr(name))


def derived(memo, name, *args):
    """`DERIVED_FUNCTIONS` 의 `name` 값(키 = 숫자·문자열 인자 그대로). 처음이면 계산해 memo 에 담는다. 모르는 이름은 `KeyError`."""
    return _lookup(memo, name, *args)
