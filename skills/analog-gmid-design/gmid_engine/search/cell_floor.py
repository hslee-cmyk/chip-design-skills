"""L 칸 정점 하한 -- 쓰기 소자 반전 좌표 ln IDu 의 칸별 상자 하한 (계획 DEC-88·LR10, 오케스트레이터 결정 2026-10-08 S-4f).

진입점: `ln_idu_floors(sctx, variables, cells, one_var_only=False, start=None) -> {변수 index: 하한}`.

* 칸 정점 하한(kind, w_key, 칸) = 그 L 칸 [lo, hi] 안 LUT L 앵커 전부 × VDS·VS 전 격자의 곡선(정점 마디가 on_mask 인 곡선만,
  `search_domain` 하한과 같은 곡선 집합)에서 gm/ID 정점 마디의 ln IDu(= lnID + ln L − ln w_m) 최댓값 -- 좌표가 이 값 이상이면 그 칸의
  어느 격자 동작점에서도 강반전 분지 시작 위다. 칸 안 앵커 사이 L(선형 보간)의 정점은 따로 묶지 않는다(앵커 최댓값).
* `variables` 의 `ln_idu` 성분(= 쓰기 소자 m)마다 m 의 칸(`cells` = `domain.l_cells` 순 칸 index)으로 하한을 고르고, 원래 lo < 하한 <
  hi 일 때만 돌려준다. `one_var_only` 면 1변수 노드 writer(diode 의 gate 쓰기·소스 추종의 source 쓰기 = writer 소자의 d·s·bulk 가
  그 노드를 포함 -- sizing `dc_columns.self_referential` 과 같은 판정)만. 이 소자들은 정점 아래 좌표에서 노드 근이 늘 없다(분지 규칙).
* `start`(θ Mapping)가 있으면 하한 = min(칸 정점 하한, 시작 좌표) -- 받아들인 시작점 자체를 상자 밖으로 내몰지 않는다.
* 캐시: `sctx.cell_floors`(S0 수명, (kind, w_key, 칸) 마다 1회, 1변수 writer 집합 1회). LUT memo 의 derived 영역은 쓰지 않는다(상한이
  슬라이스 × 파생표 수라 tol_V 표를 밀어낼 수 있다).
"""
import math

import numpy as np

from gmid_engine.graph import MOS_TERMINAL_NAMES
from gmid_engine.sizing import REL_VGS_GATE, REL_VGS_SOURCE, THETA_LN_IDU

_ONE_VAR_KEY = ("one_var_writers",)
_SELF_RELATIONS = (REL_VGS_GATE, REL_VGS_SOURCE)


def _peak_floor(sctx, kind, w_key, cell):
    key = (kind, w_key, cell)
    if key not in sctx.cell_floors:
        sl = sctx.dc.lut.memo.lut.slice_map[(kind, w_key)]
        lo_l, hi_l = cell
        grid_l = np.asarray(sl.grids[0], dtype=float)
        pick = (grid_l >= lo_l - np.spacing(lo_l)) & (grid_l <= hi_l + np.spacing(hi_l))
        ln_l = np.log(grid_l[pick])[:, None, None, None]
        ln_idu = np.asarray(sl.log_ID)[pick] + ln_l - math.log(sl.w_m)
        on = np.asarray(sl.on_mask, dtype=bool)[pick]
        gm_id = np.where(on, np.asarray(sl.log_GM)[pick] - np.asarray(sl.log_ID)[pick], -np.inf)
        peak = np.argmax(gm_id, axis=1)
        at_peak = np.take_along_axis(ln_idu, peak[:, None, :, :], axis=1)[:, 0]
        valid = np.take_along_axis(on, peak[:, None, :, :], axis=1)[:, 0]
        sctx.cell_floors[key] = float(np.max(np.where(valid, at_peak, -np.inf)))
    return sctx.cell_floors[key]


def _one_var_writers(sctx):
    if _ONE_VAR_KEY not in sctx.cell_floors:
        pins = {n: dict(p) for n, p in sctx.dc.base.column("device", "pins")}
        bulk = {n: b.net for n, b in sctx.dc.base.column("device", "bulk")}
        out = set()
        for net, w in sctx.dc.base.column("node", "dc_writer"):
            if w.relation in _SELF_RELATIONS:
                d, _g, s = (pins[w.element][t] for t in MOS_TERMINAL_NAMES)
                if net in (d, s, bulk[w.element]):
                    out.add(w.element)
        sctx.cell_floors[_ONE_VAR_KEY] = frozenset(out)
    return sctx.cell_floors[_ONE_VAR_KEY]


def ln_idu_floors(sctx, variables, cells, one_var_only=False, start=None):
    kinds = dict(sctx.dc.base.column("device", "kind"))
    w_keys = dict(sctx.dc.lut.w_keys)
    cell_of = {mos: table[j] for (mos, table), j in zip(sctx.domain.l_cells, cells)}
    chosen = _one_var_writers(sctx) if one_var_only else None
    out = {}
    for i, var in enumerate(variables):
        ckind, m = var.component
        if ckind != THETA_LN_IDU or (chosen is not None and m not in chosen):
            continue
        floor = _peak_floor(sctx, kinds[m], w_keys[kinds[m]], cell_of[m])
        if start is not None:
            floor = min(floor, start[var.component])
        if var.lo < floor < var.hi:
            out[i] = floor
    return out
