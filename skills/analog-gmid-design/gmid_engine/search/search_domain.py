"""탐색 정의역 -- θ 스키마 위 연속 변수·bounds·L 칸·면적 축 분해능 (설계 design_mod6_search_front 4.1·4.2·5절, DEC-80·88).

진입점: `search_domain`(`@compute_block`, writer `search_domain`) -- `search_domain(snapshot, lut, resistance_bounds_ohm, capacitance_bounds_f, pdk_decl, spec_bounds,
area_budget_m2, untie)`. S0 수준 필드 `graph/kernel: search_domain`(설계 40 §2.4.7 'SearchContext 칸 배정'·§2.4.8) -- S0 당 1회, 입력이 같으면 재사용.
reads = S1 `element_class`·`kind`, graph 대칭 블록 `orbits`·`current_symmetry`·`dc_colour`, 쓰기 계획 `dc_current_basis`, θ 스키마 `graph/kernel: theta_schema`.
extras: `lut` = sizing `LutAccess`, `resistance_bounds_ohm`·`capacitance_bounds_f` = 실행 설정(`SearchSettings`)의 θ 수동소자 상자(run 단위 명시 재정의, None 이면 spec 상자) --
벽시계·평가 예산 같은 다른 실행 설정은 정의역을 바꾸지 않아 extras 에 넣지 않는다(실행 설정은 블록 입력이 아니다 -- 그 상자가 바뀌면 블록 입력 버전이 재계산을 보장한다, v1.9.1 D6),
`pdk_decl` = core `PdkDecl`, `spec_bounds` = spec `search.theta_bounds`(authoring ThetaBound tuple), `area_budget_m2` = 면적 예산 또는 None, `untie` = 묶음을 푼 원소 이름 tuple.

* `ln_idu`(쓰기 소자 반전 좌표, DEC-88 (라)): bounds = kind 별 LUT 포락선. 상한 = 레이아웃 전 폭 슬라이스 전 격자점 ln IDu
  최댓값(설계 4.2 'VGS 축 끝 ln IDu 의 포락선'), 하한 = (L, VDS, VS) 곡선마다 gm/ID 정점의 ln IDu 중 최솟값 -- 그 아래 r 은
  어느 동작점에서도 정점 아래라 강반전 분지 근이 없다. 조회점별 실제 하한은 부등식 제약(constraints `inversion_floor`)이다.
* `y`: [0, 1](G7 3.4).
* kind 상자(`current_box`)는 전류 기저의 MOS(`graph.dc_current_basis.mos`) 의 kind 마다 -- `off` 선언 소자는 기저에 없어 `off` 소자만 가진 kind 는 상자가 없다(EO-1 범위 4).
* `current`(ln 좌표): 기저 원소가 MOS 면 그 kind 의 `current_box`(I_off, I_max). MOS 가 아닌 기저 원소(값 미선언 이상 전류원 등)는
  그 원소를 항으로 갖는 MOS 행들의 kind 상자 합집합(최소 I_off, 최대 I_max) -- 그 전류는 그 MOS 들을 지나간다.
* `resistance`(ln 좌표): PDK 선언(`core.pdk_decl`)에 수동소자 범위가 없으므로 `settings.resistance_bounds_ohm` 이 정본이다. θ 저항이
  있는데 None 이면 `SchemaRejectedError`(detail gate `search_domain`, reason `theta_resistance_bounds_undeclared`, resistors) --
  기본값 없음.
* `L`: 연속 변수는 칸이 정해진 뒤(분지마다) 칸 [lo, hi] 로 만든다(lo == hi 칸은 고정). 여기서는 `l_cells` 표만 둔다.
* `area_resolution_m2` = b_A = PDK 선언 `manufacturing_grid_m` × `min_finger_w_m`(difftap.2)(DEC-80 (i), 설계 6.4 'Σ W·L 축
  한 칸') -- 같은 두 값을 W 하한 제약(S-18)이 `w_min_m`·`grid_m` 으로 읽는다.
  면적 모델 오차가 미측정이라 (ii) = (i) 이고 '추정'이다(DEC-72·80). 전력 분해능 b_P 는 점마다(`objectives`).
* 묶음 상자(CONTRACT 3.24-4, 40 §6-8 D-1): 같은 자기동형 궤도 안 구성원(부호 +1)의 상자가 대표와 다르면 `tied_orbit_bounds_differ` 로 거부한다. 궤도를 넘는(KCL 이 유도한 --
  graph `orbits` 에서 대표와 다른 궤도) θ 전류 구성원(부호 +1)은 대표 변수의 상자를 대표·구성원 상자의 **교집합**으로 줄이고, 교집합이 비면 `tied_current_box_empty`
  (SchemaRejectedError, gate `search_domain`)로 거부한다. 부호 −1 구성원은 상자 비교를 하지 않는다(값 = −대표).
"""
import math

import numpy as np

from gmid_engine.core import PdkDecl, SchemaRejectedError, compute_block
from gmid_engine.graph import ELEMENT_MOS, GRAPH_KEY
from gmid_engine.sizing import (DC_KEY, KERNEL_KEY, THETA_CAPACITANCE, THETA_CURRENT, THETA_L, THETA_LN_IDU, THETA_RESISTANCE,
                                THETA_SS_RESISTANCE, THETA_Y)

from .current_box import current_box
from .l_cells import l_cells
from .current_symmetry import current_symmetry
from .orbit_ties import orbit_ties
from .s0_fields import SEARCH_DOMAIN_WRITER, SEARCH_DOMAIN_WRITES
from .search_values import SearchDomain, Variable

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


def _current_bounds(schema, kinds, classes, boxes, key):
    if classes[key] == ELEMENT_MOS:
        return boxes[kinds[key]]
    users = [mos for mos, terms in schema.current_cone if any(t.source == key for t in terms)]
    if not users:
        raise ValueError("search_domain: θ 전류 " + repr(key) + " 를 지나는 MOS 행이 없다")
    return min(boxes[kinds[m]][0] for m in users), max(boxes[kinds[m]][1] for m in users)


def _passive_box(override, spec_bounds, key):
    """[r10] θ 수동소자 상자: run 단위 `SearchSettings` 값(명시 재정의)이 있으면 그것, 없으면 spec `search.theta_bounds` 의 그 원소,
    둘 다 없으면 None."""
    if override is not None:
        return tuple(override)
    return spec_bounds.get(key)


def _budget_i_max(lut_access, kind, l_lo_m, area_budget_m2):
    """면적 예산이 정하는 θ 전류 상한(S-3b 닫힘): 소자 하나의 W·L 은 총 면적 A 를 넘을 수 없으므로 W ≤ A / L, 전류는
    ID = IDu · W / L(IDu = 전류 밀도 좌표, 포락선 최댓값 `exp(hi)`)이라 ID ≤ IDu_max · A / L² -- L 은 kind 의 최소 L 앵커(가장 큰 값)."""
    _lo, hi = _ln_idu_envelope(lut_access, kind)
    return math.exp(hi) * area_budget_m2 / (l_lo_m * l_lo_m)


READS = (("device", "element_class"), ("device", "kind"), ("device", "dc_colour"), ("node", "dc_colour"), ("graph", "orbits"),
         ("graph", "current_symmetry"), ("graph", "dc_current_basis"), ("graph", "theta_schema"))


@compute_block(SEARCH_DOMAIN_WRITER, reads=READS, writes=SEARCH_DOMAIN_WRITES)
def search_domain(projection):
    lut, resistance_bounds_ohm, capacitance_bounds_f, pdk_decl, spec_bounds, area_budget_m2, untie = projection.extras
    if not isinstance(pdk_decl, PdkDecl):
        raise TypeError("search_domain: pdk_decl 은 core read_pdk_decl 결과여야 한다")
    base = projection
    schema = base.value("graph", KERNEL_KEY, "theta_schema")
    declared = {b.element: (b.lo, b.hi) for b in spec_bounds}          # authoring ThetaBound(kind 단위 Ω·F)
    kinds = dict(base.column("device", "kind"))
    classes = dict(base.column("device", "element_class"))
    mos_kinds = sorted({kinds[m] for m in base.value("graph", DC_KEY, "dc_current_basis").mos})      # 쓰기 계획이 연 MOS 의 kind -- `off` 소자만 가진 kind 는 상자가 없다
    boxes = {k: current_box(lut, k) for k in mos_kinds}
    if area_budget_m2 is not None:
        boxes = {k: (lo, _budget_i_max(lut, k, l_cells(lut, k)[0][0], area_budget_m2))
                 for k, (lo, _peak) in boxes.items()}
    envelopes = {}
    variables, mos = [], []
    resistors = [key for kind, key in schema.components if kind in (THETA_RESISTANCE, THETA_SS_RESISTANCE)]
    missing = tuple(r for r in resistors if _passive_box(resistance_bounds_ohm, declared, r) is None)
    if missing:
        raise SchemaRejectedError(detail={"gate": "search_domain", "reason": "theta_resistance_bounds_undeclared",
                                          "resistors": missing})
    capacitors = [key for kind, key in schema.components if kind == THETA_CAPACITANCE]
    missing = tuple(c for c in capacitors if _passive_box(capacitance_bounds_f, declared, c) is None)
    if missing:
        # 커패시터 상자는 PDK 선언에서 유도할 수 없다(capm.* 규칙값 N/A, cap_mim 셀 원본 없음 -- sizing CONTRACT O13)
        raise SchemaRejectedError(detail={"gate": "search_domain", "reason": "theta_capacitance_bounds_undeclared",
                                          "capacitors": missing})
    for component in schema.components:
        ckind, key = component
        if ckind == THETA_LN_IDU:
            if kinds[key] not in envelopes:
                envelopes[kinds[key]] = _ln_idu_envelope(lut, kinds[key])
            lo, hi = envelopes[kinds[key]]
            variables.append(Variable(component, False, lo, hi))
        elif ckind == THETA_Y:
            variables.append(Variable(component, False, 0.0, 1.0))
        elif ckind == THETA_CURRENT:
            lo, hi = _current_bounds(schema, kinds, classes, boxes, key)
            variables.append(Variable(component, True, math.log(lo), math.log(hi)))
        elif ckind in (THETA_RESISTANCE, THETA_SS_RESISTANCE):
            lo, hi = _passive_box(resistance_bounds_ohm, declared, key)
            variables.append(Variable(component, True, math.log(lo), math.log(hi)))
        elif ckind == THETA_CAPACITANCE:
            lo, hi = _passive_box(capacitance_bounds_f, declared, key)
            variables.append(Variable(component, True, math.log(lo), math.log(hi)))
        elif ckind == THETA_L:
            mos.append(key)
        else:
            raise ValueError("search_domain: 모르는 θ 종류 " + repr(component))   # 조용히 건너뛰지 않는다(sizing O16)
    for var in variables:
        if not var.lo < var.hi:
            raise ValueError("search_domain: 빈 bounds " + repr(var))
    # [r12] 같은 자기동형 궤도 원소의 같은 종류 θ 성분은 변수 하나로 묶는다(3.24) -- 묶인 구성원은 같은 bounds 여야 한다
    symmetry = current_symmetry(base, tuple(untie))
    reps, ties = orbit_ties(base, tuple(schema.components), tuple(untie), symmetry)
    by_component = {v.component: v for v in variables}
    negated = frozenset(symmetry.negated)
    orbit = dict(base.value("graph", GRAPH_KEY, "orbits").devices)
    for rep, members in ties:
        if rep not in by_component:
            continue
        head = by_component[rep]
        # 부호 −1 로 묶인 구성원은 대표와 상자가 같을 필요가 없다(값 = −대표)
        same = tuple(m for m in members if m not in negated and orbit.get(m[1]) == orbit.get(rep[1]))
        cross = tuple(m for m in members if m not in negated and orbit.get(m[1]) != orbit.get(rep[1]))
        odd = tuple(m for m in same if (by_component[m].log, by_component[m].lo, by_component[m].hi) != (head.log, head.lo, head.hi))
        if odd:
            raise SchemaRejectedError(detail={"gate": "search_domain", "reason": "tied_orbit_bounds_differ",
                                              "elements": (rep,) + odd})
        if cross:                                      # D-1: 궤도를 넘는 전류 묶음 = 구성원 상자의 교집합
            lo = max((head.lo,) + tuple(by_component[m].lo for m in cross))
            hi = min((head.hi,) + tuple(by_component[m].hi for m in cross))
            if not lo < hi:
                raise SchemaRejectedError(detail={"gate": "search_domain", "reason": "tied_current_box_empty",
                                                  "elements": (rep,) + cross, "box": (lo, hi)})
            variables[variables.index(head)] = Variable(head.component, head.log, lo, hi)
    tied = {m for _rep, members in ties for m in members} | set(symmetry.zeros)
    variables = [v for v in variables if v.component not in tied]
    mos = [m for m in mos if (THETA_L, m) not in tied]
    cells = {}
    table = tuple((m, cells.setdefault(kinds[m], l_cells(lut, kinds[m]))) for m in sorted(mos))
    grid, w_min = pdk_decl.values(_PDK_QUANTITIES)
    domain = SearchDomain(tuple(variables), table, float(grid * w_min), tuple(sorted(boxes.items())), float(w_min),
                          float(grid), area_budget_m2, ties, symmetry.negated, symmetry.zeros)
    return {("graph", "search_domain"): {KERNEL_KEY: domain}}
