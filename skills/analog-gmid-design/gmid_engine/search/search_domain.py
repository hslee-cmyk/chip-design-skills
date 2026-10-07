"""탐색 정의역 -- θ 스키마 위 연속 변수·bounds·L 칸·면적 축 분해능 (설계 design_mod6_search_front 4.1·4.2·5절, DEC-80·88).

진입점: `search_domain(dc_ctx, settings) -> SearchDomain`(S0 당 1회, 루프 밖).

* `ln_idu`(쓰기 소자 반전 좌표, DEC-88 (라)): bounds = kind 별 LUT 포락선. 상한 = 레이아웃 전 폭 슬라이스 전 격자점 ln IDu
  최댓값(설계 4.2 'VGS 축 끝 ln IDu 의 포락선'), 하한 = (L, VDS, VS) 곡선마다 gm/ID 정점의 ln IDu 중 최솟값 -- 그 아래 r 은
  어느 동작점에서도 정점 아래라 강반전 분지 근이 없다. 조회점별 실제 하한은 부등식 제약(constraints `inversion_floor`)이다.
* `y`: [0, 1](G7 3.4).
* `current`(ln 좌표): 기저 원소가 MOS 면 그 kind 의 `current_box`(I_off, I_max). MOS 가 아닌 기저 원소(값 미선언 이상 전류원 등)는
  그 원소를 항으로 갖는 MOS 행들의 kind 상자 합집합(최소 I_off, 최대 I_max) -- 그 전류는 그 MOS 들을 지나간다.
* `resistance`(ln 좌표): PDK 선언(`core.pdk_decl`)에 수동소자 범위가 없으므로 `settings.resistance_bounds_ohm` 이 정본이다. θ 저항이
  있는데 None 이면 `SchemaRejectedError`(detail gate `search_domain`, reason `theta_resistance_bounds_undeclared`, resistors) --
  기본값 없음.
* `L`: 연속 변수는 칸이 정해진 뒤(분지마다) 칸 [lo, hi] 로 만든다(lo == hi 칸은 고정). 여기서는 `l_cells` 표만 둔다.
* `area_resolution_m2` = b_A = PDK 선언 `manufacturing_grid_m` × `min_finger_w_m`(difftap.2)(DEC-80 (i), 설계 6.4 'Σ W·L 축
  한 칸') -- 같은 두 값을 W 하한 제약(S-18)이 `w_min_m`·`grid_m` 으로 읽는다. 진입점은 `search_domain(dc_ctx, settings, pdk_decl)`.
  면적 모델 오차가 미측정이라 (ii) = (i) 이고 '추정'이다(DEC-72·80). 전력 분해능 b_P 는 점마다(`objectives`).
"""
import math

import numpy as np

from gmid_engine.core import PdkDecl, SchemaRejectedError
from gmid_engine.graph import ELEMENT_MOS
from gmid_engine.sizing import THETA_CURRENT, THETA_L, THETA_LN_IDU, THETA_RESISTANCE, THETA_Y

from .current_box import current_box
from .l_cells import l_cells
from .search_values import SearchDomain, SearchSettings, Variable

_PDK_QUANTITIES = ("manufacturing_grid_m", "min_finger_w_m")   # PDK 선언 이름(core CONTRACT 9.4) -- 값은 선언 파일이 계산


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


def _current_bounds(dc_ctx, kinds, classes, boxes, key):
    if classes[key] == ELEMENT_MOS:
        return boxes[kinds[key]]
    users = [mos for mos, terms in dc_ctx.schema.current_cone if any(t.source == key for t in terms)]
    if not users:
        raise ValueError("search_domain: θ 전류 " + repr(key) + " 를 지나는 MOS 행이 없다")
    return min(boxes[kinds[m]][0] for m in users), max(boxes[kinds[m]][1] for m in users)


def search_domain(dc_ctx, settings, pdk_decl):
    if not isinstance(settings, SearchSettings):
        raise TypeError("search_domain: settings 는 SearchSettings 여야 한다(기본값 없음)")
    if not isinstance(pdk_decl, PdkDecl):
        raise TypeError("search_domain: pdk_decl 은 core read_pdk_decl 결과여야 한다")
    kinds = dict(dc_ctx.base.column("device", "kind"))
    classes = dict(dc_ctx.base.column("device", "element_class"))
    mos_kinds = sorted({kinds[m] for m, c in classes.items() if c == ELEMENT_MOS})
    boxes = {k: current_box(dc_ctx.lut, k) for k in mos_kinds}
    envelopes = {}
    variables, mos = [], []
    resistors = [key for kind, key in dc_ctx.schema.components if kind == THETA_RESISTANCE]
    if resistors and settings.resistance_bounds_ohm is None:
        raise SchemaRejectedError(detail={"gate": "search_domain", "reason": "theta_resistance_bounds_undeclared",
                                          "resistors": tuple(resistors)})
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
            lo, hi = _current_bounds(dc_ctx, kinds, classes, boxes, key)
            variables.append(Variable(component, True, math.log(lo), math.log(hi)))
        elif ckind == THETA_RESISTANCE:
            lo, hi = settings.resistance_bounds_ohm
            variables.append(Variable(component, True, math.log(lo), math.log(hi)))
        elif ckind == THETA_L:
            mos.append(key)
    for var in variables:
        if not var.lo < var.hi:
            raise ValueError("search_domain: 빈 bounds " + repr(var))
    cells = {}
    table = tuple((m, cells.setdefault(kinds[m], l_cells(dc_ctx.lut, kinds[m]))) for m in sorted(mos))
    grid, w_min = pdk_decl.values(_PDK_QUANTITIES)
    return SearchDomain(tuple(variables), table, float(grid * w_min), tuple(sorted(boxes.items())), float(w_min),
                        float(grid))
