"""스펙에서 gm/ID·L·전류 출발 구간 (설계 41 §6, 40 §11 U13 · §7.1 면적 예산 출발점, 단계 A8; D-SIa~g).

진입점: `start_intervals(s1v, ach, kctx, spec, pdk_decl, domain) -> StartIntervals`.

**쓰임**: 출발값과 보고에만 쓴다(EP-7 -- 판정은 외층 봉인·metric 이 한다). 층 0(`layer0_start`)이 상자 중심 대신 이 구간의 선택점을 출발 θ 로 쓴다(`build_search_context(s1v=, ach=)`).
입력: `s1v`(단계 A -- 전달 뷰·블록·극점 노드·L 동치류), `ach`(U9 `Achievability` 또는 None), `kctx`(쓰기 계획·전류 기저·θ 스키마), `spec`, `pdk_decl`, `domain`(`search_domain` -- L 칸·θ 상자).

**계산 순서**(41 §6.1, 순환 없음):
0. 주극점 노드(`dominant_node`, 구조 판정, 매크로 모델을 쓰지 않는다).
1. gm/ID 하한 -- 헤드룸 예산(`headroom_bounds`, §6.2). 소자 L 은 PDK/LUT 의 첫 정의된 L 앵커로 시작한다.
2. 이득 L 하한(`gain_l_status`, §6.4-1) -- A_max 미인증이면 비활성 사유만 낸다.
3. 속도 L 상한(`speed_bounds`, §6.4-4; gm/ID_lo 사용).
4. matching·면적 L 경계(`matching_bounds`·`area_bounds`, §6.4-2·5) -- 이 경계에 필요한 전류는 **1회차 매크로 모델**(gm/ID = gm/ID_lo, `current_model` + `macro_solve`)에서 가져온다.
5. L 선택: L = max(L 하한들). L 동치류·자기동형 묶음은 구간의 교집합이고, LUT L 칸(bin) 안 값으로 맞춘다(LR3: 칸 하한이 L 보다 크면 그 칸의 하한, bin 사이 틈은 다음 칸).
6. 그 L 에서 gm/ID 하한(헤드룸 §6.2, **LUT 역산 정의역** `domain_bounds`, 최소 폭 W ≥ W_min)·상한(속도 §6.3, offset·열잡음 가드 §6.4-2a·§7.5, 면적 §6.4-5, LUT 역산 정의역)을 다시 낸다.
   같은 VGS 묶음(`parallel_vgs`)은 gm/ID 구간의 교집합 하나를 공유한다. 소자 동작점(곡선을 읽는 VDS·VSB)은 포화 경계와 헤드룸 예산의 중점 VDS, 첫 VS 격자점이다.
7. gm/ID 선택: 구간의 **최댓값**(t = 1; 약반전일수록 VDSAT 가 작아 포화·헤드룸에 가장 여유가 있다), 단 그 점이 실행 가능하지 않으면 구간 안 위치 t(0 = 하한, 1 = 상한)를 줄여
   **실행 가능한 최대 t**(`bracket_root`)를 쓴다. 실행 가능 = (면적 예산이 있으면) 면적 추정 A_est ≤ 예산 **그리고** 매크로 모델이 GBW·PM 을 상자 범위 안에서 풀었다(근 없음 기록 없음:
   약반전 소자의 큰 게이트 용량은 gm/ID 를 낮출수록 줄어 속도가 풀린다). 선택은 항상 소자별 구간 안이라 다른 경계를 깨지 않는다(U11 임시 `fit_to_area_budget` 이 모든 ln IDu 를 같은 Δ만큼
   옮기던 방식을 대체한다, 40 §7.1). 가장 느슨한 끝(t = 0)에서도 매크로가 풀리지 않으면 목표가 이 구간에서 달성 불가라는 충돌 레코드를 남기고 면적만으로 고른다.
8. 전류 확정: 선택점에서 `current_model` + `macro_solve` 2회차. 매크로·미러 전파가 정하지 못한 소자의 전류는 자리값 = 그 점에서 W = W_min 인 전류(`current_ref`)이고 층 0 의 Chebyshev 중심이
   기준 전류로 쓴다. 매크로가 풀리지 않으면 풀이의 출발점 gm(단일 극점 근사 2π·GBW·C_ref)을 쓰되 그 t 는 실행 불가로 센다.
9. 출발 사다리: t 와 그 절반들(구간 폭을 gm/ID 하한까지 반으로 가르는 횟수 + 1 칸). 층 0 이 칸 순서로 커널 봉인 여부를 확인해 처음 받아들일 상태인 칸에서 출발한다.

**충돌**(41 §6.6): 하한 > 상한이면 자르지 않고 `StartConflict` 를 남긴다 -- 선택은 헤드룸 하한 쪽(포화 유지 = 봉인 7)으로 간다.
**불변식**: 같은 입력이면 같은 표. 소자 순회·합산은 구조 색 순이고 이름은 행 이름에만 쓰인다(이름 전단사).
"""
import math
import sys

import numpy as np

from gmid_engine.sizing import THETA_CAPACITANCE, THETA_CURRENT, THETA_L, THETA_LN_IDU, bracket_root

from ._helpers_area import area_estimate
from .dominant_node import RULE_NONE, DominantNode, dominant_node
from .iv_area import area_bounds
from .iv_context import build_start_context
from .iv_currents import current_model
from .iv_curves import QUANTITY_FT, QUANTITY_IDU
from .iv_domain import domain_bounds
from .iv_gain_l import gain_l_status
from .iv_headroom import headroom_bounds
from .iv_matching_l import matching_bounds
from .iv_noise import noise_bounds
from .iv_speed import speed_bounds
from .macro_poles import macro_solve
from .start_values import (
    EDGE_VDS,
    MACRO_NONCONVERGENT,
    MACRO_ROOT_MISSING,
    QUANTITY_AREA,
    QUANTITY_GM_ID,
    QUANTITY_L,
    SIDE_HI,
    SIDE_LO,
    SRC_L_CLASS,
    SRC_LUT_L,
    SRC_LUT_RANGE,
    WHY_NO_CURRENT,
    Bound,
    StartConflict,
    StartIntervals,
    StartRow,
    StartRung,
)


class _State:
    """한 선택점 (gm/ID, L)의 전류·면적 상태. `currents` = {MOS: A 또는 None(정해지지 않음)}, `elements` = {θ 전류 원소: A}(양수만), `macro` = MacroResult, `area`·`passive` = A_est·수동소자 몫
    (정해지지 않은 소자는 `refs` 의 자리값으로 센다), `refs` = {전류가 정해지지 않은 MOS: 자리값 A}."""

    def __init__(self, model, macro, currents, elements, cap_values, res_values, area, passive, per_device, refs, macro_failed):
        self.model, self.macro, self.currents, self.elements = model, macro, currents, elements
        self.macro_failed = macro_failed
        self.cap_values, self.res_values = cap_values, res_values
        self.area, self.passive, self.per_device, self.refs = area, passive, per_device, refs


def _value(vec, gm):
    """아핀 전류 벡터의 값. gm 이 없으면(매크로 비활성) gm 계수가 모두 0 인 벡터만 값이 있다."""
    if gm is None:
        return None if vec[:-1].any() else float(vec[-1])
    return float(vec[:-1] @ gm + vec[-1])


def _mos_currents(ctx, elements):
    rows = {name: tuple((t.source, t.num / t.den) for t in terms) for name, terms in ctx.basis.rows}
    out = {}
    for d in ctx.devices:
        terms = rows.get(d.name, ())
        out[d.name] = sum(c * elements[s] for s, c in terms) if terms and all(s in elements for s, _c in terms) else None
    return out


def _state(ctx, gm_id, lengths, refine=True):
    model = current_model(ctx, gm_id, lengths)
    macro = macro_solve(ctx, model, gm_id, lengths, refine)
    # 풀리지 않은 매크로(근 없음·반복 한도)의 gm 은 풀이의 출발점 -- 단일 극점 근사 gm = 2π·GBW·C_ref(41 §6.5 '특수 경우') 그대로이거나 실행 가능한 점이다. 그 값으로 전류를 잡되
    # 이 선택 점은 실행 불가로 센다(`macro_failed`).
    failed = any(code in (MACRO_ROOT_MISSING, MACRO_NONCONVERGENT) for code, _detail in macro.records)
    gm = np.asarray([v for _k, v in macro.gm], dtype=float) if macro.gm else None
    elements = {e: v for e, vec in model.affine.items() for v in [_value(vec, gm)] if v is not None}
    free = set(ctx.basis.free)
    elements = {e: v for e, v in elements.items() if e not in free or v > 0}      # θ 전류는 양수 -- 아닌 값은 정해지지 않은 것으로 센다
    cap_values, res_values = dict(macro.cap_values), dict(macro.resistor_values)
    currents = {n: (v if v is not None and v > 0 else None) for n, v in _mos_currents(ctx, elements).items()}
    # 전류를 정하지 못한 소자의 자리값(층 0 의 Chebyshev 중심이 기준 전류로 쓴다): 폭이 PDK 최소 finger 폭 W_min 일 때의 전류 I_Wmin = W_min·IDu/L (가장 작은 실현 가능 소자 = front 의 최소
    # 전력·면적 쪽 끝점)과, 정해진 전류가 있으면 그 기하 평균(선언된 이상 전류원·매크로가 정한 전류 눈금 -- 눈금이 다른 가지를 섞으면 미러·적층의 DC 가 무너진다) 중 큰 쪽.
    known = [v for v in currents.values() if v is not None]
    scale = math.exp(sum(math.log(v) for v in known) / len(known)) if known else 0.0
    refs = {}
    for d in ctx.devices:
        bundle = ctx.curves.bundle_of(d.name, d.kind, lengths[d.name])
        if currents[d.name] is None and bundle is not None:
            refs[d.name] = max(scale, ctx.w_min_m * ctx.curves.value(bundle, QUANTITY_IDU, gm_id[d.name]) / lengths[d.name])
    merged = {n: currents[n] if currents[n] is not None else refs.get(n) for n in currents}
    area, passive, per_device = (None, None, None)
    if all(v is not None for v in merged.values()):
        area, per_device, passive = area_estimate(ctx, merged, gm_id, lengths, cap_values, res_values)
    return _State(model, macro, currents, elements, cap_values, res_values, area, passive, per_device, refs, failed)


def _first_defined(ctx, d, cells):
    """소자 d 의 L 칸에서 곡선이 정의된 첫 앵커(L 앵커 오름차순)."""
    lo, hi = cells[0][0], cells[-1][1]
    return next((L for L in ctx.curves.l_anchors(d.kind) if lo <= L <= hi and ctx.curves.bundle(d.kind, L) is not None), None)


def _snap(ctx, d, L, cells):
    """L 이상인 LUT L 칸 안의 값으로 맞춘다(칸 하한보다 작으면 칸 하한, 칸 사이 틈이면 다음 칸 하한). 곡선이 정의되지 않으면 같은 칸의 다음 앵커. (L, 칸 index) 또는 (None, None)."""
    for j, (lo, hi) in enumerate(cells):
        if hi < L:
            continue
        pick = max(L, lo)
        if ctx.curves.bundle(d.kind, pick) is not None:
            return pick, j
        for anchor in ctx.curves.l_anchors(d.kind):
            if pick <= anchor <= hi and ctx.curves.bundle(d.kind, anchor) is not None:
                return anchor, j
    return None, None


def _side(items, quantity, side):
    return [b.value for b in items if b.quantity == quantity and b.side == side]


def _vgs_groups(ctx, lows, highs):
    """같은 VGS 묶음(`DeviceInfo.group`)은 gm/ID 를 공유한다 -- 구간의 교집합. (하한 사전, 상한 사전 또는 None). 교집합이 비면 하한 쪽으로 닫고(포화 유지) 충돌은 호출부가 센다."""
    groups = {}
    for d in ctx.devices:
        groups.setdefault(d.group, []).append(d.name)
    low = {n: max(lows[m] for m in names) for names in groups.values() for n in names}
    if highs is None:
        return low, None
    high = {n: max(min(highs[m] for m in names), low[n]) for names in groups.values() for n in names}
    return low, high


def _owner_groups(ctx):
    groups = {}
    for d in ctx.devices:
        groups.setdefault(d.owner, []).append(d.name)
    return groups


def start_intervals(s1v, ach, kctx, spec, pdk_decl, domain):
    ctx = build_start_context(s1v, ach, kctx, spec, pdk_decl, domain)
    devices = ctx.devices
    inactive, conflicts, records = [], [], []
    first_L, cells = {}, {}
    for d in devices:
        cells[d.name] = ctx.l_cells[d.owner]
        first_L[d.name] = _first_defined(ctx, d, cells[d.name])
    if not devices or any(v is None for v in first_L.values()):
        return StartIntervals((), (), (("start_intervals", "lut_curve_undefined_for_all_l"),), None, (), (), None, ctx.area_budget_m2, None, ())
    lut_range = {d.name: ctx.curves.gm_id_range(ctx.curves.bundle(d.kind, first_L[d.name])) for d in devices}

    # ---- 0, 1: 주극점 노드 · gm/ID 하한
    dominant = dominant_node(ctx.transfer) if ctx.transfer is not None else DominantNode((), RULE_NONE)
    head = headroom_bounds(ctx, first_L)
    inactive.extend(head.inactive)
    conflicts.extend(head.conflicts)
    vds_budget = {d.name: head.budgets.get((d.name, EDGE_VDS)) for d in devices}
    dom0 = domain_bounds(ctx, first_L, vds_budget)
    g_lo0 = _vgs_groups(ctx, {d.name: max([lut_range[d.name][0]] + _side(head.bounds.get(d.name, ()), QUANTITY_GM_ID, SIDE_LO)
                                          + _side(dom0.bounds.get(d.name, ()), QUANTITY_GM_ID, SIDE_LO)) for d in devices}, None)[0]
    # 소자 동작점(곡선 읽기용): VDS = 포화 경계와 헤드룸 예산의 중점의 LUT 격자점, VSB = 첫 VS 격자점. 경계 VDS 는 triode 가장자리라 gds 가 커서 진성 이득이 터무니없이 낮다.
    points = {}
    for d in devices:
        budget = head.budgets.get((d.name, EDGE_VDS))
        low = ctx.curves.edge(d.kind).vds_min_v
        points[d.name] = (ctx.curves.snap_vds(d.kind, low if budget is None else (low + budget) / 2), ctx.curves.vsb_ref(d.kind))
    ctx.curves.assign(points)

    # ---- 4: 1회차 매크로 전류
    first = _state(ctx, g_lo0, first_L)
    currents1 = {} if first is None else {n: (v if v is not None else first.refs.get(n)) for n, v in first.currents.items()}
    if first is not None:
        records.extend(first.macro.records)

    # ---- 2, 3, 4: L 경계
    l_items = {d.name: [] for d in devices}
    inactive.extend(gain_l_status(ctx))
    speed = speed_bounds(ctx, dominant, first_L, g_lo0) if ctx.transfer is not None else None
    match = matching_bounds(ctx, currents1, first_L, g_lo0)
    area = area_bounds(ctx, currents1, first_L, g_lo0)
    for part in (speed, match, area):
        if part is None:
            continue
        for name, items in part.bounds.items():
            l_items[name].extend(b for b in items if b.quantity == QUANTITY_L)
        conflicts.extend(c for c in part.conflicts if c.quantity == QUANTITY_L or c.quantity == QUANTITY_AREA)
    chosen_L, cell_index, l_range = {}, {}, {}
    for owner, names in _owner_groups(ctx).items():
        lows = [cells[names[0]][0][0]] + [v for n in names for v in _side(l_items[n], QUANTITY_L, SIDE_LO)]
        highs = [cells[names[0]][-1][1]] + [v for n in names for v in _side(l_items[n], QUANTITY_L, SIDE_HI)]
        lo, hi = max(lows), min(highs)
        if lo > hi:
            conflicts.append(StartConflict(owner, QUANTITY_L, ((SRC_L_CLASS, lo), (SRC_L_CLASS, hi)), lo - hi))
        pick, j = _snap(ctx, ctx.by_name[names[0]], lo, cells[names[0]])
        pick, j = (first_L[names[0]], 0) if pick is None else (pick, j)
        for n in names:
            chosen_L[n], cell_index[n], l_range[n] = pick, j, (lo, hi)

    # ---- 6: 그 L 에서 gm/ID 경계
    bundles = {d.name: ctx.curves.bundle_of(d.name, d.kind, chosen_L[d.name]) for d in devices}
    head2 = headroom_bounds(ctx, chosen_L, head.budgets)
    conflicts.extend(head2.conflicts)
    dom2 = domain_bounds(ctx, chosen_L, vds_budget)
    conflicts.extend(dom2.conflicts)
    g_items = {d.name: list(dom2.bounds.get(d.name, ())) for d in devices}
    g_lo = {d.name: max([float(min(bundles[d.name][QUANTITY_FT].gm_id))] + _side(head2.bounds.get(d.name, ()), QUANTITY_GM_ID, SIDE_LO)
                        + _side(g_items[d.name], QUANTITY_GM_ID, SIDE_LO)) for d in devices}
    speed2 = speed_bounds(ctx, dominant, chosen_L, g_lo) if ctx.transfer is not None else None
    match2 = matching_bounds(ctx, currents1, chosen_L, g_lo)
    noise2 = noise_bounds(ctx, currents1, chosen_L, g_lo)
    area2 = area_bounds(ctx, currents1, chosen_L, g_lo)
    for part in (speed2, match2, noise2, area2):
        if part is None:
            continue
        for name, items in part.bounds.items():
            g_items[name].extend(b for b in items if b.quantity == QUANTITY_GM_ID)
        conflicts.extend(c for c in part.conflicts if c.quantity == QUANTITY_GM_ID)
        inactive.extend(part.inactive)
    raw_hi = {d.name: min([float(max(bundles[d.name][QUANTITY_FT].gm_id))] + _side(g_items[d.name], QUANTITY_GM_ID, SIDE_HI)) for d in devices}
    raw_lo = {d.name: max([g_lo[d.name]] + _side(g_items[d.name], QUANTITY_GM_ID, SIDE_LO)) for d in devices}       # 헤드룸 하한 + 최소 폭 하한
    g_low, g_hi = _vgs_groups(ctx, raw_lo, raw_hi)
    for d in devices:
        upper = min(raw_hi[m.name] for m in devices if m.group == d.group)
        if d.name == d.group and g_low[d.name] > upper:
            conflicts.append(StartConflict(d.name, QUANTITY_GM_ID, (("lower", g_low[d.name]), ("upper", upper)), g_low[d.name] - upper))

    # ---- 7, 8: 선택(면적 예산 안 최대 t)과 전류 확정
    def pick(t):
        return {n: g_low[n] + t * (g_hi[n] - g_low[n]) for n in g_low}

    budget = ctx.area_budget_m2

    use_macro = [True]      # 매크로 목표를 실행 가능 판정에 쓰는가 -- 가장 느슨한 끝에서도 풀리지 않으면 끄고, 그 뒤에는 SLSQP 정제도 건너뛴다(`refine`)

    def feasible(state):
        """면적 예산 안이고(예산이 있으면) 매크로 모델이 목표(GBW·PM)를 상자 범위 안에서 풀었다. 매크로가 모든 t 에서 풀리지 않는 회로(`use_macro` 해제)는 면적만 본다."""
        within = budget is None or (state.area is not None and state.area <= budget)
        return within and not (use_macro[0] and state.macro_failed)

    def solve(x, refine=True):
        return _state(ctx, pick(x), chosen_L, use_macro[0] and refine)

    # 사다리 길이 = 구간 폭을 LUT gm/ID 최솟값 단위까지 반으로 가르는 횟수 -- t 탐색의 분해능도 같은 칸 폭(2^-steps)이면 충분하다(더 가는 t 는 사다리의 칸 사이에 든다)
    span = max(g_hi[n] - g_low[n] for n in g_low)
    floor = min(lo for lo, _hi in lut_range.values())          # LUT 곡선의 gm/ID 최솟값
    steps = max(0, math.ceil(math.log2(span / floor))) if span > 0 else 0

    top = solve(1.0)
    t, final = 1.0, top
    if not feasible(top):
        bottom = solve(0.0)
        if bottom.macro_failed:
            use_macro[0] = False            # 가장 느슨한 끝(gm/ID 하한 = 가장 작은 게이트 용량)에서도 목표를 못 맞춘다 -- 목표가 이 구간에서 달성 불가: 기록하고 면적만으로 고른다
            conflicts.append(StartConflict("circuit", QUANTITY_GM_ID, (("macro_target_unattainable_at_gm_id_lo", ctx.gbw_hz),), math.nan))
        t, final = 0.0, bottom
        if feasible(top):
            t, final = 1.0, top
        elif not feasible(bottom):
            conflicts.append(StartConflict("circuit", QUANTITY_AREA, (("estimate_at_gm_id_lo", bottom.area), ("budget", budget)),
                                           math.nan if bottom.area is None or budget is None else bottom.area - budget))
        else:
            tol = 1 / 2 ** steps if steps else math.sqrt(math.sqrt(sys.float_info.epsilon))
            x, _a, _b = bracket_root(lambda v: 1.0 if not feasible(solve(v)) else -1.0, 0.0, 1.0, tol)
            candidate = max(0.0, (0.0 if x is None else x) - tol)
            state = solve(candidate)
            if feasible(state):
                t, final = candidate, state
    records.extend(final.macro.records)
    if final.refs:
        inactive.append(("current_from_macro", WHY_NO_CURRENT))
    # 출발 사다리: 실행 가능한 최대 t 에서 시작해 t 를 절반씩 줄인 점들(층 0 이 커널로 봉인 여부를 확인한다)
    rungs = [_rung(ctx, domain, kctx, final, pick(t), chosen_L, cell_index, bundles, t)]
    for k in range(1, (steps if t > 0 else 0) + 1):
        lower = t / 2 ** k
        state = solve(lower, refine=False)          # 사다리의 아래 칸은 대안 출발점 -- 전원 전류 최소화 없이 실행 가능한 출발점의 전류로 충분하다
        rungs.append(_rung(ctx, domain, kctx, state, pick(lower), chosen_L, cell_index, bundles, lower))
    return _report(ctx, domain, final, pick(t), chosen_L, cell_index, (g_low, g_hi, l_range, lut_range), (g_items, l_items), bundles,
                   (conflicts, inactive, records), t, tuple(rungs))


def _rung(ctx, domain, kctx, state, g, L, cell_index, bundles, t):
    """한 사다리 칸의 출발 θ -- 구간이 값을 정한 성분(ln_idu·θ 전류·보상 커패시터·L 과 L 칸)만."""
    wanted = {v.component for v in domain.variables}
    theta = []
    for component in kctx.schema.components:
        kind, key = component
        if component not in wanted:
            continue
        if kind == THETA_LN_IDU and key in ctx.by_name:
            theta.append((component, math.log(ctx.curves.value(bundles[key], QUANTITY_IDU, g[key]))))
        elif kind == THETA_CURRENT and key in state.elements:
            theta.append((component, state.elements[key]))
        elif kind == THETA_CAPACITANCE and key in state.cap_values:
            theta.append((component, state.cap_values[key]))
    represent = {d.owner: d.name for d in reversed(ctx.devices)}
    cells_out = []
    for mos, _cells in domain.l_cells:
        if mos in represent:
            theta.append(((THETA_L, mos), L[represent[mos]]))
            cells_out.append((mos, cell_index[represent[mos]]))
    refs = tuple(sorted(state.refs.items(), key=lambda kv: ctx.by_name[kv[0]].colour))
    return StartRung(t, tuple(theta), tuple(cells_out), refs)


def _report(ctx, domain, state, g, L, cell_index, ranges, items, bundles, notes, t, rungs):
    g_lo, g_hi, l_range, lut_range = ranges
    g_items, l_items = items
    conflicts, inactive, records = notes
    rows = []
    for d in ctx.devices:
        current = state.currents.get(d.name)
        current = state.refs.get(d.name) if current is None else current
        idu = ctx.curves.value(bundles[d.name], QUANTITY_IDU, g[d.name])
        lut = (Bound(QUANTITY_GM_ID, SIDE_LO, SRC_LUT_RANGE, lut_range[d.name][0]), Bound(QUANTITY_GM_ID, SIDE_HI, SRC_LUT_RANGE, lut_range[d.name][1]),
               Bound(QUANTITY_L, SIDE_LO, SRC_LUT_L, ctx.l_cells[d.owner][0][0]), Bound(QUANTITY_L, SIDE_HI, SRC_LUT_L, ctx.l_cells[d.owner][-1][1]))
        mine = tuple(c for c in conflicts if c.device in (d.name, d.owner))
        rows.append(StartRow(d.name, d.kind, g_lo[d.name], g_hi[d.name], g[d.name], l_range[d.name][0], l_range[d.name][1], L[d.name], cell_index[d.name],
                             current, math.log(idu), None if current is None else current * L[d.name] / idu,
                             lut + tuple(g_items[d.name]) + tuple(l_items[d.name]), tuple(inactive), mine))
    wanted = {v.component for v in domain.variables}
    covered = {c for c, _v in rungs[0].theta}
    return StartIntervals(tuple(rows), tuple(conflicts), tuple(inactive), state.macro, rungs[0].theta, rungs[0].cells, state.area, ctx.area_budget_m2, t,
                          tuple(sorted(c for c in wanted if c not in covered)), tuple(records), rungs[0].current_ref, rungs)
