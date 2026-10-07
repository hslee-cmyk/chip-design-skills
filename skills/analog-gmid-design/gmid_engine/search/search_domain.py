"""탐색 정의역 -- θ 스키마 위 연속 변수·bounds·L 칸·축 분해능 (설계 design_mod6_search_front 4.1·4.2·5절, DEC-80·88).

진입점: `search_domain(dc_ctx, settings) -> SearchDomain`(S0 당 1회, 루프 밖).

* `ln_idu`(쓰기 소자 반전 좌표, DEC-88 (라)): bounds = kind 별 LUT 포락선. 상한 = 레이아웃 전 폭 슬라이스 전 격자점 ln IDu
  최댓값(설계 4.2 'VGS 축 끝 ln IDu 의 포락선'), 하한 = (L, VDS, VS) 곡선마다 gm/ID 정점의 ln IDu 중 최솟값 -- 그 아래 r 은
  어느 동작점에서도 정점 아래라 강반전 분지 근이 없다. 조회점별 실제 하한은 부등식 제약(constraints `inversion_floor`)이다.
* `y`: [0, 1](G7 3.4). `current`: ln 좌표, bounds = ln(`settings.current_bounds_a`)(GB4 상한표 미구현 -- 선언, S-3).
  `resistance`: ln 좌표, bounds = ln(`settings.resistance_bounds_ohm`)(θ 저항이 있는데 선언이 None 이면 `ValueError`).
* `L`: 연속 변수는 칸이 정해진 뒤(분지마다) 칸 [lo, hi] 로 만든다(lo == hi 칸은 고정). 여기서는 `l_cells` 표만 둔다.
* `area_resolution_m2` = b_A = 제조 격자 × kind 최소 finger 폭의 최솟값(DEC-80 (i), 설계 6.4 'Σ W·L 축 한 칸').
  면적 모델 오차가 미측정이라 (ii) = (i) 이고 '추정'이다(DEC-72·80).
"""
import math

import numpy as np

from gmid_engine.sizing import THETA_CURRENT, THETA_L, THETA_LN_IDU, THETA_RESISTANCE, THETA_Y

from .l_cells import l_cells
from .search_values import SearchDomain, SearchSettings, Variable


def _ln_idu_envelope(lut_access, kind):
    w_key = dict(lut_access.w_keys)[kind]
    sl = lut_access.memo.lut.slice_map[(kind, w_key)]
    ln_l = np.log(np.asarray(sl.grids[0], dtype=float))[:, None, None, None]
    ln_idu = np.asarray(sl.log_ID) + ln_l - math.log(sl.w_m)
    on = np.asarray(sl.on_mask, dtype=bool)
    hi = float(np.max(np.where(on, ln_idu, -np.inf)))
    gm_id = np.where(on, np.asarray(sl.log_GM) - np.asarray(sl.log_ID), -np.inf)
    peak = np.argmax(gm_id, axis=1)                                         # VGS 축(1) 위 정점 index
    at_peak = np.take_along_axis(ln_idu, peak[:, None, :, :], axis=1)[:, 0]
    valid = np.take_along_axis(on, peak[:, None, :, :], axis=1)[:, 0]
    lo = float(np.min(np.where(valid, at_peak, np.inf)))
    return lo, hi


def search_domain(dc_ctx, settings):
    if not isinstance(settings, SearchSettings):
        raise TypeError("search_domain: settings 는 SearchSettings 여야 한다(기본값 없음)")
    kinds = dict(dc_ctx.base.column("device", "kind"))
    envelopes = {}
    variables, mos = [], []
    for component in dc_ctx.schema.components:
        ckind, key = component
        if ckind == THETA_LN_IDU:
            if kinds[key] not in envelopes:
                envelopes[kinds[key]] = _ln_idu_envelope(dc_ctx.lut, kinds[key])
            lo, hi = envelopes[kinds[key]]
            variables.append(Variable(component, False, lo, hi))
        elif ckind == THETA_Y:
            variables.append(Variable(component, False, 0.0, 1.0))
        elif ckind == THETA_CURRENT:
            lo, hi = settings.current_bounds_a
            variables.append(Variable(component, True, math.log(lo), math.log(hi)))
        elif ckind == THETA_RESISTANCE:
            if settings.resistance_bounds_ohm is None:
                raise ValueError("search_domain: θ 저항 " + repr(key) + " 이 있는데 resistance_bounds_ohm 선언이 없다")
            lo, hi = settings.resistance_bounds_ohm
            variables.append(Variable(component, True, math.log(lo), math.log(hi)))
        elif ckind == THETA_L:
            mos.append(key)
    for var in variables:
        if not var.lo < var.hi:
            raise ValueError("search_domain: 빈 bounds " + repr(var))
    cells = {}
    table = tuple((m, cells.setdefault(kinds[m], l_cells(dc_ctx.lut, kinds[m]))) for m in sorted(mos))
    spec = dc_ctx.lut.memo.lut.spec
    b_area = spec.manufacturing_grid_m * min(w for _k, w in spec.min_finger_w_m)
    if not settings.power_resolution_w > 0:
        raise ValueError("search_domain: power_resolution_w 는 양수 선언이어야 한다")
    return SearchDomain(tuple(variables), table, float(b_area), float(settings.power_resolution_w))
