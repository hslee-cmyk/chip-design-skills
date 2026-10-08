"""헤드룸 경로 엣지 비용의 LUT 격자 최솟값 (설계 41 §4.6 '|VGS|_min·VDSAT_min 은 그 소자 kind 의 LUT 격자 전수에서의 최솟값'; D-GB4f).

진입점: `edge_costs(memo, kind, w_key) -> EdgeCost`  (`memo` = `lut.LutMemo`).

* **VGS 엣지 비용** = 봉인 9(전도 여유) 를 지킬 수 있는 격자 행(= 강반전 분지 마디, 곡선의 gm/ID 정점 이상의 VGS 마디)의 |VGS| 최솟값. 전도 판정은 sizing 봉인 9 와 같은 식이다:
  `I_off ≤ ε·ID`, ε = (gm/ID)·tol_V, I_off = VGS = 0 누설 => `gm·tol_V ≥ I_off` (tol_V = `tol_v_table` 의 `id_equivalent_v`, (L 앵커, VDS) 칸; None 이면 그 행은 봉인할 수 없다).
  VGS = 0 마디는 gm/ID 정점이라 분지에 들지만 꺼진 소자(전도 봉인 위반)이므로 이 조건이 빼는 것이다(조건 없이 최솟값을 잡으면 0 V 라 상한이 의미가 없다).
  (L 앵커, VDS, VS) 곡선마다 조건을 만족하는 첫 마디 VGS 의 최솟값을 L bin(`DcSlice.l_bins.anchor_bin`, 지도가 없으면 bin 하나)별로 모은다 -- 서로 다른 소자를 독립으로 최소화하므로
  경로 폭의 **상한**이다. VS(=VSB) 범위는 bulk 기본 규칙이 소스 전위를 모르므로 격자 전체(보수). `best_row` = 전체 최솟값을 낸 행(L, VDS, VS, gm/ID).
* **VDS 엣지 비용** = (분지·전도 마디의 VDSAT 열 최솟값, VDSAT 열이 없으면 0) + (`tol_vdsat_table` 의 정의된 칸 중 `vdsat_v` 최솟값, 표를 만들 수 없으면 0). 두 최솟값을 따로 잡으므로
  실제 (VDSAT + tol_vdsat) 최솟값의 하한이다(상한 계산이 틀리지 않는 쪽).
격자 배열 통계이고 보간 조회가 아니다(`cell_floor`·`search_domain` 의 격자 통계와 같은 방식). 결정론.
"""
import math

import numpy as np

from gmid_engine.core import SchemaRejectedError, SealViolationError
from gmid_engine.lut import tol_v_table, tol_vdsat_table

from .achievability_types import EdgeCost


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


def _tol_vdsat_grid(memo, kind, w_key, shape):
    """(L, VDS) 별 tol_vdsat (정의 안 되면 0 -- 하한을 낮추는 쪽), 표를 만들 수 없으면 전부 0."""
    out = np.zeros(shape)
    try:
        cells = tol_vdsat_table(memo, kind, w_key).cells
    except (SchemaRejectedError, SealViolationError):
        return out
    for i, row in enumerate(cells):
        for k, cell in enumerate(row):
            if cell.vdsat_v is not None:
                out[i, k] = float(cell.vdsat_v)
    return out


def edge_costs(memo, kind, w_key):
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
    vdsat = sl.columns.get("VDSAT")
    tol_sat = _tol_vdsat_grid(memo, kind, w_key, (n_l, n_d))
    if vdsat is not None:                           # 포화 행만(봉인 7: VDS ≥ VDSAT + tol_vdsat) -- 모든 MOS 는 기본 포화 의도
        vds = np.asarray(sl.grids[2], dtype=float)[None, None, :, None]
        ok = ok & (vds >= np.asarray(vdsat) + tol_sat[:, None, :, None])
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
    vdsat_min = 0.0 if vdsat is None else float(np.min(np.where(branch_on, np.asarray(vdsat), np.inf)))
    positive = tol_sat[tol_sat > 0]
    tol_min = float(positive.min()) if positive.size and (tol_sat > 0).all() else 0.0
    return EdgeCost(kind, w_key, float(first_vgs.min()), by_bin, vdsat_min + tol_min, best)
