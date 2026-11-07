"""스펙에서 gm/ID·L·전류 출발 구간 (설계 41 §6, 40 §11 U13 · §7.1 면적 예산 출발점, 단계 A8; D-SIa~g).

진입점: `start_intervals`(`@compute_block`, writer `start_intervals`) -- `start_intervals(snapshot, spec, inputs, pdk_decl, lut)`.

**쓰임**: 출발값과 보고에만 쓴다(EP-7 -- 판정은 외층 봉인·metric 이 한다). 층 0(`layer0_start`)이 상자 중심 대신 이 구간의 선택점(`graph/start: rungs` 칸 0)을 출발 θ 로 쓴다.
**입력**(설계 40 §2.4.7 `StartContext` 행 -- 블록이 선언한 S0 수준 필드를 투영으로 읽는다, `READS`): S1 소자·노드 열, 대칭 블록 `dc_colour`, 쓰기 계획 `dc_coord`·`dc_current_basis`,
`graph/kernel: theta_schema·l_ties·search_domain(L 칸·θ 상자)·passive_area_decl`, S1v `graph/s1v: views`(전달 뷰·블록·극점 노드), GB4 `graph/ach: gain_checks·local_inputs`(없으면 이득 L 하한 비활성).
extras: `spec`, `inputs`(sizing `DcInputs`), `pdk_decl`(core `PdkDecl`), `lut`(sizing `LutAccess` -- 곡선은 LUT memo, 기준 VDS·엣지 비용은 LUT 파생 `lut.derived`).
블록 안 읽기 묶음은 `iv_context.start_view`(`StartView`, 호출 안에서 만들고 버린다).
**출력**(S0 수준 필드, 설계 40 §2.4.8 v1.9.1 D3, 묶음 객체 없음): `device: start.row`(`StartRow`)·`start.point`((VDS, VSB) -- 곡선을 읽은 소자 동작점),
`graph/start`(key `START_KEY`): `conflicts`, `inactive`, `macro`, `rungs`(출발 사다리 `StartRung` tuple, 칸 0 = 선택점), `records`(매크로 모델 기록), `area_est_m2`, `area_fraction`(t),
`uncovered`(구간이 정하지 못해 상자 중심으로 남은 θ 성분), `wf_start`(FS-1: 출발 w_f 칸 `WfCell` tuple -- writer 는 이 블록 하나, 칸 폐포 계산 자리도 여기 하나).
면적 예산은 spec 선언이라 필드로 두지 않는다(소비자가 spec 을 읽는다).

**계산 순서**(41 §6.1, 순환 없음):
0. 주극점 노드(`dominant_node`, 구조 판정, 매크로 모델을 쓰지 않는다).
1. gm/ID 하한 -- 헤드룸 예산(`headroom_bounds`, §6.2). 소자 L 은 PDK/LUT 의 첫 정의된 L 앵커로 시작한다.
2. 이득 L 하한(`gain_l_bounds`, §6.4-1) -- A_max 가 모두 인증이고 gain 제약이 있을 때 블록 국소 모델이 목표 g_i 를 맞추는 최소 L(1회차 전류·gm/ID_lo 사용); 아니면 비활성 사유만 낸다.
3. 속도 L 상한(`speed_bounds`, §6.4-4; gm/ID_lo 사용).
4. matching·면적 L 경계(`matching_bounds`·`area_bounds`, §6.4-2·5) -- 이 경계에 필요한 전류는 **1회차 매크로 모델**(gm/ID = gm/ID_lo, `current_model` + `macro_solve`)에서 가져온다.
5. L 선택: L = max(L 하한들). L 동치류·자기동형 묶음은 구간의 교집합이고, LUT L 칸(bin) 안 값으로 맞춘다(LR3: 칸 하한이 L 보다 크면 그 칸의 하한, bin 사이 틈은 다음 칸).
5a. 출발 w_f 칸(FS-1, 계획 DEC-108 (2)(3), 설계 40 §3.7-B 3): 정합 묶음 폐포 칸(`wf_start_value`)마다 멤버 출발 W(`member_start_w` -- 쓰기 멤버 I·L/IDu, 종속 멤버 I_i·L/IDu_짝: I = 4의 1회차 전류,
   IDu = 1회차 gm/ID 의 기준 폭 슬라이스 곡선, L = 5의 L)의 최솟값 이하 가장 넓은 정의 후보 슬라이스를 `graph/start: wf_start` 로 한 번 쓴다(8의 전류는 돌아오지 않는다). 4의 L 경계는 w_f 칸을
   읽지 않는다(slope bin = 기준 폭 슬라이스, A-178 S-1). 6의 가드 slope bin 은 이 칸 키를 읽는다. 출발 불능 칸은 기록 `wf_start_undefined`(대체값 0).
   짝(`start_partner`: KVL 짝 ∪ 대칭 짝, 회로 MOS 전부)이 없는 비쓰기 단일 멤버 칸은 LUT 선언 기준 폭 슬라이스에서 출발한다(기록 `wf_start_reference`, 조건 = 후보 안 + L 위치 판정; 아니면 `reference_start_undefined`).
   이 블록은 전달 뷰 유무와 무관하게 늘 실행하고, 뷰 없을 때 비활성인 항목은 `graph/start: inactive` 에 사유 `transfer_view_absent` 로 남는다.
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
import dataclasses
import math
import sys

import numpy as np

from gmid_engine.core import SealViolationError, compute_block
from gmid_engine.graph import GRAPH_KEY
from gmid_engine.lut import is_slice_gap, op_point, slice_l_position, widths
from gmid_engine.sizing import COORD_WRITER, KERNEL_KEY, THETA_CAPACITANCE, THETA_CURRENT, THETA_L, THETA_LN_IDU, bracket_root

from ._helpers_area import area_estimate
from ._helpers_curves import QUANTITY_FT, QUANTITY_IDU, QUANTITY_VGS, curve_bundle, curve_bundle_of, curve_value, edge_cost, l_anchors, slice_of, snap_vds
from .dominant_node import RULE_NONE, DominantNode, dominant_node
from .iv_area import area_bounds
from .iv_context import start_view
from .iv_currents import current_model
from .iv_domain import domain_bounds
from .iv_gain_l import gain_l_bounds
from .iv_headroom import headroom_bounds
from .iv_matching_l import matching_bounds
from .iv_noise import noise_bounds
from .iv_speed import speed_bounds
from .macro_poles import macro_solve
from .s0_fields import START_INTERVALS_WRITER, START_KEY, START_WRITES
from .wf_member_w import member_start_w
from .wf_partner import start_partner
from .wf_start import wf_start_value
from .start_values import (
    EDGE_VDS,
    MACRO_INACTIVE,
    MACRO_NONCONVERGENT,
    MACRO_ROOT_MISSING,
    QUANTITY_AREA,
    QUANTITY_GM_ID,
    QUANTITY_L,
    SIDE_HI,
    SIDE_LO,
    SRC_FF_START_VIEW,
    SRC_L_CLASS,
    SRC_LUT_L,
    SRC_LUT_RANGE,
    SRC_OFFSET_L_VIEW,
    SRC_POLE0_VIEW,
    SRC_SPEED_VIEW,
    SRC_W_MIN,
    WHY_NO_CURRENT,
    WHY_NO_VIEW,
    Bound,
    StartConflict,
    StartRow,
    StartRung,
)


# 전달 뷰가 없을 때 이 블록이 새로 남기는 비활성 항목(설계 40 §3.7-B 3 (v1)(v3)(v4)(v6), A-205 이름). 기존 이름이 이미 비활성을 내는 (v2) `gain_l_6.4_1`(gain_l_bounds)·(v5) `noise_guard_7.5`(noise_bounds)는
# 그대로 두고, (v4) 는 기존 이름 `macro_inactive`. 5a 출발 w_f 칸은 뷰와 무관하게 돈다.
_VIEW_ONLY_ITEMS = (SRC_POLE0_VIEW, SRC_SPEED_VIEW, MACRO_INACTIVE, SRC_OFFSET_L_VIEW, SRC_FF_START_VIEW)
_REL = math.sqrt(sys.float_info.epsilon)      # 상대 비교·여유(부동소수 분해능 √ε): W = W_min 이 정확히 경계라 반올림이 아래로 떨어지지 않게 하는 여유, 같은 값끼리 비교의 허용


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
        bundle = curve_bundle_of(ctx, d.name, d.kind, lengths[d.name])
        if currents[d.name] is None and bundle is not None:
            refs[d.name] = max(scale, ctx.w_min_m * curve_value(bundle, QUANTITY_IDU, gm_id[d.name]) / lengths[d.name])
    merged = {n: currents[n] if currents[n] is not None else refs.get(n) for n in currents}
    area, passive, per_device = (None, None, None)
    if all(v is not None for v in merged.values()):
        area, per_device, passive = area_estimate(ctx, merged, gm_id, lengths, cap_values, res_values)
    return _State(model, macro, currents, elements, cap_values, res_values, area, passive, per_device, refs, failed)


def _width_floor_gm_id(ctx, d, length, current, g0):
    """전류 `current` 에서 폭 W(g) = I·L/IDu(g) (보고가 읽는 `curve_value` 와 같은 값) 가 W_min 이상이 되는 g0 이상의 최소 gm/ID. 이미 만족하면 g0, 곡선 끝까지 못 미치면 None.
    곡선은 약반전 쪽에서 gm/ID 가 비단조일 수 있어(포화 근처) 마디 교차 대신 g0 ~ 곡선 최댓값을 촘촘히 훑어 처음 만족하는 칸을 `bracket_root` 로 다듬는다."""
    bundle = curve_bundle_of(ctx, d.name, d.kind, length)
    target = ctx.w_min_m * (1 + _REL)

    def excess(x):
        return target - current * length / curve_value(bundle, QUANTITY_IDU, x)       # > 0 : 폭 부족

    if excess(g0) <= 0:
        return g0
    nodes = np.asarray(bundle[QUANTITY_IDU].gm_id, dtype=float)
    grid = np.unique(np.concatenate([[g0], nodes[nodes > g0]]))             # g0 이상의 곡선 마디(LUT 가 정한 해상도)
    for a, b in zip(grid[:-1], grid[1:]):
        if excess(float(b)) <= 0:
            root, _fa, _fb = bracket_root(excess, float(a), float(b), _REL * float(b))
            return float(b) if root is None or excess(float(root)) > 0 else float(root)
    return None


def _widen(ctx, state, g, lengths):
    """최소 폭 W ≥ W_min 을 **확정된 전류**에서 맞춘다 -- 전류가 정해진 소자의 폭 W = I·L/IDu(g) 는 g 에 대해 증가하므로 W < W_min 인 소자(같은 VGS 묶음은 함께)의 g 를 W = W_min 인 g 로 올린다.
    gm 고정 모델의 하한(`iv_area` 의 `w_min_gm_id`)은 입력 소자(전류 = gm/g)에는 맞지만 전류가 미러·KCL 로 입력 소자 전류를 따르는 소자에는 1회차 전류로 재서 어긋난다. 바뀌면 새 g 사전, 아니면 g 그대로."""
    need = {}
    for d in ctx.devices:
        current = state.currents.get(d.name)
        if current is None:
            continue
        found = _width_floor_gm_id(ctx, d, lengths[d.name], current, g[d.name])
        if found is not None:
            need[d.group] = max(need.get(d.group, 0.0), found)
    new = {n: max(v, need.get(ctx.by_name[n].group, 0.0)) for n, v in g.items()}
    return g if new == g else new


def _placed(ctx, gm_id, lengths, refine=True):
    """`_state` + 최소 폭 보정 -- (보정된 g 에서의 상태), `state.g` = 보정된 gm/ID. 보정은 전류를 다시 정하므로 고정점까지(상한 = 소자 수) 되풀이한다."""
    g = gm_id
    state = _state(ctx, g, lengths, refine)
    for _ in ctx.devices:                 # 고정점 반복: 한 번에 적어도 한 소자가 확정되는 단조 수렴(반복 상한 = 소자 수)
        wider = _widen(ctx, state, g, lengths)
        if wider is g:
            break
        g = wider
        state = _state(ctx, g, lengths, refine)
    state.g = g
    return state


def _first_defined(ctx, d, cells):
    """소자 d 의 L 칸에서 곡선이 정의된 첫 앵커(L 앵커 오름차순)."""
    lo, hi = cells[0][0], cells[-1][1]
    return next((L for L in l_anchors(ctx, d.kind) if lo <= L <= hi and curve_bundle(ctx, d.kind, L) is not None), None)


def _snap(ctx, d, L, cells):
    """L 이상인 LUT L 칸 안의 값으로 맞춘다(칸 하한보다 작으면 칸 하한, 칸 사이 틈이면 다음 칸 하한). 곡선이 정의되지 않으면 같은 칸의 다음 앵커. (L, 칸 index) 또는 (None, None)."""
    for j, (lo, hi) in enumerate(cells):
        if hi < L:
            continue
        pick = max(L, lo)
        if curve_bundle(ctx, d.kind, pick) is not None:
            return pick, j
        for anchor in l_anchors(ctx, d.kind):
            if pick <= anchor <= hi and curve_bundle(ctx, d.kind, anchor) is not None:
                return anchor, j
    return None, None


def _curve_range(bundle):
    """곡선 분지의 gm/ID 범위 (최솟값, 최댓값). 분지 맨 앞 마디가 gm/ID 정점이다."""
    g = np.asarray(bundle[QUANTITY_FT].gm_id, dtype=float)
    return float(g.min()), float(g.max())


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


READS = (
    ("device", "element_class"), ("device", "kind"), ("device", "pins"), ("device", "bulk"), ("device", "dc_colour"), ("device", "dc_coord"),
    ("node", "is_rail"), ("node", "dc_colour"), ("node", "port_direction"), ("node", "port_role"),
    ("graph", "dc_current_basis"), ("graph", "theta_schema"), ("graph", "l_ties"), ("graph", "search_domain"), ("graph", "passive_area_decl"),
    ("graph", "views"), ("graph", "gain_checks"), ("graph", "local_inputs"), ("graph", "matching_groups"),
)
_WHY_REFERENCE_UNDEFINED = "reference_slice_undefined"        # 기준 폭 슬라이스에서 출발점 조회가 정의되지 않음(wf_start_undefined 의 why)


def _wf_cells(ctx, groups, writers, gm_id, lengths, currents, bundles):
    """5a 출발 w_f 칸 -- (칸 tuple, 기록 tuple). 멤버 출발 W(`member_start_w`)를 낸 뒤 칸 폐포·선택(`wf_start_value`)을 한 번 부른다. 점 = 1회차 gm/ID `gm_id`(= g_lo0)·5의 L `lengths`·
    1회차 전류 `currents`(4단계 `matching_bounds` 에 넘긴 것과 같은 dict), IDu·조회는 기준 폭 슬라이스 곡선(`bundles`: 소자 동작점의 곡선 묶음). 비쓰기 멤버의 짝 = `start_partner`(회로 MOS 전부에서
    KVL 짝 ∪ 대칭 짝, 칸 무관). 짝 없는 단일 멤버 칸의 기준 폭 출발은 `wf_start_value` 가 `reference`·`l_defined`(L 위치 판정만)로 한다."""
    devices = ctx.devices
    names = tuple(d.name for d in devices)
    position = {d.name: d.colour for d in devices}
    kinds = {d.name: d.kind for d in devices}
    gate, source, bulk = {d.name: d.gate for d in devices}, {d.name: d.source for d in devices}, {d.name: d.bulk for d in devices}
    partner = {n: start_partner(n, names, position, gate, source, bulk, kinds, lengths, writers, groups) for n in names if n not in writers}
    ln_idu = {n: _WHY_REFERENCE_UNDEFINED if bundles[n] is None else math.log(curve_value(bundles[n], QUANTITY_IDU, gm_id[n])) for n in names if n in writers}
    start_w = member_start_w(names, writers, partner, currents, lengths, ln_idu)

    def defined(name, key):
        """그 멤버의 출발점(1회차 gm/ID 의 VGS, 곡선 동작점의 VDS·VSB, 5의 L)이 슬라이스 `key` 에서 조회 정의되는가 -- 축 밖·L bin 불가(`is_slice_gap`)만 정의 불능이고 그 밖 사유는 그대로 던진다."""
        bundle = bundles[name]
        if bundle is None:
            return False
        curve = bundle[QUANTITY_IDU]
        try:
            op_point(ctx.memo, kinds[name], key, lengths[name], curve_value(bundle, QUANTITY_VGS, gm_id[name]), curve.vds, curve.vsb)
        except SealViolationError as exc:
            if is_slice_gap(exc):
                return False
            raise
        return True

    def l_defined(name, key):
        """그 멤버의 5의 L 이 슬라이스 `key` 의 L 위치 판정(앵커 또는 같은 bin 안 두 앵커 사이)을 통과하는가 -- 전압을 읽지 않는다. 슬라이스 조회 불능만 False(lut 가 판정), 그 밖 사유는 던진다."""
        return slice_l_position(ctx.memo, kinds[name], key, lengths[name], strict=False) is not None

    candidates = {kind: widths(ctx.memo.lut, kind) for kind in sorted(set(kinds.values()))}
    reference = {kind: ctx.memo.lut.cap_map[kind].w_key for kind in candidates}
    return wf_start_value(groups, names, position, kinds, start_w, candidates, defined, reference, l_defined, grid_m=ctx.memo.lut.spec.manufacturing_grid_m)


def _wf_unstarted(ctx, groups):
    """출발 곡선을 읽을 수 없는 실행(`lut_curve_undefined_for_all_l`)의 칸: 구조는 그대로(같은 `wf_start_value`), 모든 칸 `w_key` None(`reference_slice_undefined`) -- 평가 입력을 만들 수 없는 실행임을 필드가 말한다."""
    names = tuple(d.name for d in ctx.devices)
    return wf_start_value(groups, names, {d.name: d.colour for d in ctx.devices}, {d.name: d.kind for d in ctx.devices},
                          {n: _WHY_REFERENCE_UNDEFINED for n in names}, {}, lambda name, key: False, {}, lambda name, key: False, grid_m=ctx.memo.lut.spec.manufacturing_grid_m)


def _fields(rows, points, conflicts, inactive, macro, rungs, records, area, t, uncovered, wf_start=()):
    """출력 필드 열 -- `START_WRITES` 와 같은 (kind, field)."""
    graph = {"conflicts": tuple(conflicts), "inactive": tuple(inactive), "macro": macro, "rungs": tuple(rungs), "records": tuple(records),
             "area_est_m2": area, "area_fraction": t, "uncovered": tuple(uncovered), "wf_start": tuple(wf_start)}
    out = {("device", "start.row"): {r.device: r for r in rows}, ("device", "start.point"): dict(points)}
    out.update({("graph", name): {START_KEY: value} for name, value in graph.items()})
    return out


@compute_block(START_INTERVALS_WRITER, reads=READS, writes=START_WRITES)
def start_intervals(projection):
    spec, inputs, pdk_decl, lut = projection.extras
    ctx = start_view(projection, spec, inputs, pdk_decl, lut)
    domain = projection.value("graph", KERNEL_KEY, "search_domain")
    schema = projection.value("graph", KERNEL_KEY, "theta_schema")
    devices = ctx.devices
    inactive, conflicts, records = [], [], []
    first_L, cells = {}, {}
    for d in devices:
        cells[d.name] = ctx.l_cells[d.owner]
        first_L[d.name] = _first_defined(ctx, d, cells[d.name])
    groups = tuple((g.kind, g.members, g.status) for g in projection.value("graph", GRAPH_KEY, "matching_groups"))
    if not devices or any(v is None for v in first_L.values()):
        unstarted, unstarted_records = _wf_unstarted(ctx, groups)
        return _fields((), {}, (), (("start_intervals", "lut_curve_undefined_for_all_l"),), None, (), tuple((c, tuple(d.items())) for c, d in unstarted_records),
                       None, None, (), unstarted)
    lut_range = {d.name: _curve_range(curve_bundle(ctx, d.kind, first_L[d.name])) for d in devices}

    if ctx.transfer is None:         # 전달 뷰 없음: 정의가 그 뷰를 읽는 항목만 비활성(값 0, 사유 기록) -- 매크로는 조건 없음으로 센다(근 없음·실패 아님)
        inactive.extend((item, WHY_NO_VIEW) for item in _VIEW_ONLY_ITEMS)

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
        low = edge_cost(ctx, d.kind).vds_min_v
        points[d.name] = (snap_vds(ctx, d.kind, low if budget is None else (low + budget) / 2), float(slice_of(ctx, d.kind).grids[3][0]))
    ctx = dataclasses.replace(ctx, points=points)

    # ---- 4: 1회차 매크로 전류
    first = _state(ctx, g_lo0, first_L)
    currents1 = {} if first is None else {n: (v if v is not None else first.refs.get(n)) for n, v in first.currents.items()}
    if first is not None:
        records.extend(first.macro.records)

    # ---- 2, 3, 4: L 경계
    l_items = {d.name: [] for d in devices}
    gain = gain_l_bounds(ctx, {} if first is None else first.elements, {} if first is None else first.res_values, g_lo0)
    inactive.extend(gain.inactive)
    speed = speed_bounds(ctx, dominant, first_L, g_lo0) if ctx.transfer is not None else None
    match = matching_bounds(ctx, currents1, first_L, g_lo0)
    area = area_bounds(ctx, currents1, first_L, g_lo0)
    for part in (speed, match, area, gain):
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

    # ---- 5a: 출발 w_f 칸(한 번 -- 8의 전류는 돌아오지 않는다). 6의 가드 slope bin 이 이 칸 키를 읽는다
    bundles = {d.name: curve_bundle_of(ctx, d.name, d.kind, chosen_L[d.name]) for d in devices}
    writers = frozenset(name for name, coord in projection.column("device", "dc_coord") if coord.role == COORD_WRITER)
    wf_cells, wf_records = _wf_cells(ctx, groups, writers, g_lo0, chosen_L, currents1, bundles)
    records.extend((code, tuple(detail.items())) for code, detail in wf_records)      # 필드 값은 불변이어야 한다 -- 기록 상세는 다른 출발 기록처럼 (키, 값) 쌍 tuple
    wf_keys = {name: cell.w_key for cell in wf_cells for name in cell.members}

    # ---- 6: 그 L 에서 gm/ID 경계
    head2 = headroom_bounds(ctx, chosen_L, head.budgets)
    conflicts.extend(head2.conflicts)
    dom2 = domain_bounds(ctx, chosen_L, vds_budget)
    conflicts.extend(dom2.conflicts)
    # 헤드룸 하한은 곡선 전체가 예산을 만족하면(하한 = 곡선 최솟값) 구간을 좁히지 않는다 -- 좁히는 것만 출처로 남긴다
    g_items = {d.name: [b for b in head2.bounds.get(d.name, ()) if b.value > float(min(bundles[d.name][QUANTITY_FT].gm_id)) * (1 + _REL)] + list(dom2.bounds.get(d.name, ()))
               for d in devices}
    g_lo = {d.name: max([float(min(bundles[d.name][QUANTITY_FT].gm_id))] + _side(head2.bounds.get(d.name, ()), QUANTITY_GM_ID, SIDE_LO)
                        + _side(g_items[d.name], QUANTITY_GM_ID, SIDE_LO)) for d in devices}
    speed2 = speed_bounds(ctx, dominant, chosen_L, g_lo) if ctx.transfer is not None else None
    area2 = area_bounds(ctx, currents1, chosen_L, g_lo)
    # 가드(offset·열잡음)의 입력 기여는 입력 소자가 가질 수 있는 최대 gm/ID 에서 잰다 -- 가드가 아닌 경계(LUT 곡선 끝·정의역·속도·면적)의 상한
    g_cap = {d.name: min([float(max(bundles[d.name][QUANTITY_FT].gm_id))] + _side(g_items[d.name], QUANTITY_GM_ID, SIDE_HI)
                         + [b.value for part in (speed2, area2) if part is not None for b in part.bounds.get(d.name, ())
                            if b.quantity == QUANTITY_GM_ID and b.side == SIDE_HI]) for d in devices}
    match2 = matching_bounds(ctx, currents1, chosen_L, g_lo, g_cap, wf_keys)
    noise2 = noise_bounds(ctx, currents1, chosen_L, g_lo, g_cap)
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
            # 하한을 정한 경계가 최소 폭이면 그 출처를 남긴다(W_min 은 경성 제약 -- 상한을 넘기는 최소 폭 보정은 조용한 위반이 아니라 충돌 기록, CONTRACT '최소 폭 보정')
            walls = {m.name: tuple((b.source, b.value) for b in g_items[m.name] if b.source == SRC_W_MIN and b.side == SIDE_LO and b.value > upper)
                     for m in devices if m.group == d.group}
            for m in sorted(walls):         # 같은 VGS 묶음은 한 gm/ID 를 공유한다 -- 최소 폭에 걸린 구성원마다 그 출처를 단 충돌을 남긴다
                if walls[m]:
                    conflicts.append(StartConflict(m, QUANTITY_GM_ID, (("lower", g_low[d.name]), ("upper", upper)) + walls[m], g_low[d.name] - upper))
            if not any(walls.values()):
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
        return _placed(ctx, pick(x), chosen_L, use_macro[0] and refine)

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
    rungs = [_rung(ctx, domain, schema, final, final.g, chosen_L, cell_index, bundles, t)]
    for k in range(1, (steps if t > 0 else 0) + 1):
        lower = t / 2 ** k
        state = solve(lower, refine=False)          # 사다리의 아래 칸은 대안 출발점 -- 전원 전류 최소화 없이 실행 가능한 출발점의 전류로 충분하다
        rungs.append(_rung(ctx, domain, schema, state, state.g, chosen_L, cell_index, bundles, lower))
    for d in devices:         # 최소 폭 보정이 상한을 넘겼다면 숨기지 않고 충돌로 남긴다(W_min 은 경성 제약이라 상한보다 우선)
        if final.g[d.name] > g_hi[d.name] * (1 + _REL) and d.name == d.group:
            conflicts.append(StartConflict(d.name, QUANTITY_GM_ID, (("w_min_at_fixed_current", final.g[d.name]), ("upper", g_hi[d.name])), final.g[d.name] - g_hi[d.name]))
    return _report(ctx, domain, final, final.g, chosen_L, cell_index, (g_low, g_hi, l_range, lut_range), (g_items, l_items), bundles,
                   (conflicts, inactive, records), t, tuple(rungs), wf_cells)


def _rung(ctx, domain, schema, state, g, L, cell_index, bundles, t):
    """한 사다리 칸의 출발 θ -- 구간이 값을 정한 성분(ln_idu·θ 전류·보상 커패시터·L 과 L 칸)만."""
    wanted = {v.component for v in domain.variables}
    theta = []
    for component in schema.components:
        kind, key = component
        if component not in wanted:
            continue
        if kind == THETA_LN_IDU and key in ctx.by_name:
            theta.append((component, math.log(curve_value(bundles[key], QUANTITY_IDU, g[key]))))
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


def _report(ctx, domain, state, g, L, cell_index, ranges, items, bundles, notes, t, rungs, wf_cells):
    g_lo, g_hi, l_range, lut_range = ranges
    g_items, l_items = items
    conflicts, inactive, records = notes
    rows = []
    for d in ctx.devices:
        current = state.currents.get(d.name)
        current = state.refs.get(d.name) if current is None else current
        idu = curve_value(bundles[d.name], QUANTITY_IDU, g[d.name])
        lut = (Bound(QUANTITY_GM_ID, SIDE_LO, SRC_LUT_RANGE, lut_range[d.name][0]), Bound(QUANTITY_GM_ID, SIDE_HI, SRC_LUT_RANGE, lut_range[d.name][1]),
               Bound(QUANTITY_L, SIDE_LO, SRC_LUT_L, ctx.l_cells[d.owner][0][0]), Bound(QUANTITY_L, SIDE_HI, SRC_LUT_L, ctx.l_cells[d.owner][-1][1]))
        mine = tuple(c for c in conflicts if c.device in (d.name, d.owner))
        rows.append(StartRow(d.name, d.kind, g_lo[d.name], g_hi[d.name], g[d.name], l_range[d.name][0], l_range[d.name][1], L[d.name], cell_index[d.name],
                             current, math.log(idu), None if current is None else current * L[d.name] / idu,
                             lut + tuple(g_items[d.name]) + tuple(l_items[d.name]), tuple(inactive), mine))
    wanted = {v.component for v in domain.variables}
    covered = {c for c, _v in rungs[0].theta}
    return _fields(rows, ctx.points, conflicts, inactive, state.macro, rungs, records, state.area, t, tuple(sorted(c for c in wanted if c not in covered)), wf_cells)
