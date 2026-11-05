"""gm/ID 하한 -- 헤드룸 예산에서 (설계 41 §6.2, 사용자 결정 2026-10-08 Q4 스윙·ICMR·입력 DC 예산 분할; D-SIa).

진입점: `headroom_bounds(ctx, lengths, budgets=None) -> HeadroomBounds`.

**경로 그래프는 U9 `headroom_bound`(41 §4.6)를 그대로 부른다**(복제하지 않는다): 소자 VDS/VGS 엣지를 레일 사이 위쪽 엣지로 보고, 모든 MOS 단자 넷에 대해 창 (L(n), U(n)) =
(레일에서 n 까지 최장 경로, n 에서 레일까지 최단 경로)를 얻는다(엣지 비용 = 그 kind 의 LUT 격자 전수 최솟값). 소자 k 의 엣지 (아랫 넷 a, 윗 넷 b)에 대해

  예산_k = U(b) − L(a)        (다른 소자는 최솟값 비용, 즉 '나머지는 최소로 두고 k 가 가질 수 있는 최대 전압')

이다. 41 §6.2 식 `VDSAT_k(gm/ID) ≤ V_part − Σ_{j≠k}(VDSAT_j,min + tol_j)` 의 V_part − Σ 가 이 예산이다(기둥별 가용 폭 − 다른 소자 최소 비용).
* **VDS 엣지**: VDSAT_k(gm/ID, L) ≤ 예산(VDS) -> `hull` 의 최소 gm/ID 가 하한(`vdsat_curve`). VDSAT 는 gm/ID 가 낮을수록(강반전) 커지므로 하한이다.
* **VGS 엣지**: |VGS_k|(gm/ID, L) ≤ 예산(VGS) -> 같은 방식(VGS 도 강반전일수록 커진다). 다이오드 연결 소자는 VGS 예산이 지배한다.
* **스윙·ICMR·입력 DC 분할**(Q4): 선언 제약(`swing_out_v`·`icmr_v`·`icm_margin_v`)이 걸린 창에서, 창 경로 위 소자의 예산을 `min(기둥 예산, 최소 비용 + 창 여유)` 로 줄인다.
  창 여유 = 창 폭 − 요구 폭(`swing_out_v`: 차동 출력 포트면 폭 × 2 가 p-p 라 요구 폭 = 값/2, 단일은 값 그대로; `icmr_v`: 값). 출력 DC V_o 가 선언된 노드면 위·아래를 따로 나눈다 --
  위쪽 여유 = U(n) − (V_o + 요구/2), 아래쪽 여유 = (V_o − 요구/2) − L(n). 선언이 없으면 남는 여유(창 폭 − 요구)를 위·아래 부분 기둥의 남는 여유 중 최솟값이 가장 크도록 -- 두 부분 기둥이 같은 몫(여유/2) -- 나눈다
  (설계 41 §6.2; 위·아래가 한 여유를 모두 공유한다는 이전 CONTRACT 규칙은 위·아래 예산 합이 창 폭을 넘어 요구를 못 지킨다). `icm_margin_v >= m` + 입력 DC 선언이면 위쪽 여유 = U − V_icm − m,
  아래쪽 여유 = V_icm − L − m.
* 경계의 여유는 없다: 사용자 SPICE 포화 규칙 VDS ≥ VDSAT 그대로이고 LUT `tol_vdsat` 을 경계에서 빼지 않는다(O-204, 3σ 같은 통계 관례 없음). VDSAT 열이 없는 kind 의 소자는 이 경계가 비활성이다
  (`HeadroomBounds.inactive` 에 (`SRC_HEADROOM_VDSAT`, `vdsat_column_unavailable`), 대체값 없음).
* 요구 > 가용(예산 < 최소 비용)이면 그 경계는 자르지 않고 충돌 레코드로 남긴다(41 §6.6; 같은 사실의 정지 판정은 U9 의 몫). 경로에 양수 사이클이 있어 창이 미상이면 비활성.
출발값 전용(EP-7): 판정은 외층 봉인·metric 이 한다.
"""
import dataclasses
import types

from gmid_engine.authoring import INPUT_DIRECTION, OUTPUT_DIRECTION, ROLE_DIFFERENTIAL_OUTPUT_N, ROLE_DIFFERENTIAL_OUTPUT_P
from gmid_engine.lut import REASON_VDSAT_COLUMN_UNAVAILABLE
from gmid_engine.metrics import headroom_bound

from ._helpers_curves import QUANTITY_FT, QUANTITY_VDSAT, curve_bundle, edge_cost, hull
from .start_values import (
    EDGE_VDS,
    EDGE_VGS,
    QUANTITY_GM_ID,
    SIDE_LO,
    SRC_HEADROOM_VDSAT,
    SRC_HEADROOM_VGS,
    WHY_NO_RAILS,
    Bound,
    StartConflict,
)

# U9 어휘(metrics/achievability_types.py 의 WINDOW_*·STATUS_*·VERDICT_*) -- metrics 공개 API(`__all__`)가 이 상수를 내보내지 않아 같은 문자열을 둔다(설계 공백으로 보고).
WINDOW_BUFFER = "buffer"
WINDOW_INPUT = "input"
WINDOW_OUTPUT = "output"
STATUS_UNKNOWN = "unknown"
VERDICT_INFEASIBLE = "infeasible"
VERDICT_NOT_EXCLUDED = "not_excluded"
VERDICT_NO_TARGET = "no_target"
_METRIC_SWING = "swing_out_v"
_METRIC_ICMR = "icmr_v"
_METRIC_MARGIN = "icm_margin_v"
_HEADROOM_METRICS = (_METRIC_SWING, _METRIC_ICMR, _METRIC_MARGIN)
_KIND_PMOS = "pmos"


@dataclasses.dataclass(frozen=True)
class HeadroomBounds:
    """`bounds` = {소자: (Bound, ...)}(gm/ID 하한), `conflicts` = StartConflict tuple, `inactive` = ((경계 식, 사유), ...), `budgets` = {(소자, 엣지): V}(L 과 무관한 전압 예산, 재사용용)."""

    bounds: object
    conflicts: tuple
    inactive: tuple
    budgets: object


def _edge_nets(kind, drain, gate, source):
    """위쪽 엣지 (아랫 넷, 윗 넷) -- `headroom_bound` 의 방향 규칙(nmos: 소스→드레인·게이트, pmos: 드레인·게이트→소스)."""
    if kind == _KIND_PMOS:
        return {EDGE_VDS: (drain, source), EDGE_VGS: (gate, source)}
    return {EDGE_VDS: (source, drain), EDGE_VGS: (source, gate)}


def _chains(row):
    """창 경로를 (아래쪽 사슬, 위쪽 사슬) 로 가른다: 창 넷에 닿는 첫 엣지까지가 아래쪽."""
    for i, edge in enumerate(row.path):
        if edge[3] == row.net:
            return row.path[: i + 1], row.path[i + 1:]
    return (), row.path


def _slacks(row, ctx, differential):
    """창 요구에서 나온 (위쪽 여유, 아래쪽 여유) 또는 None(요구가 걸리지 않은 창)."""
    # 판정 어휘가 no_target 이어도 constraint 가 있으면 요구는 선언된 것이다 -- U9 는 레일–레일 경로가 VGS 엣지를 지나지 않는 창(캐스코드 게이트가 레일 바이어스인 기둥)을 정지 근거로
    # 쓰지 않을 뿐(`eligible`), 출발 구간은 같은 요구를 예산 분할에 쓴다.
    if row.constraint is None or row.verdict not in (VERDICT_INFEASIBLE, VERDICT_NOT_EXCLUDED, VERDICT_NO_TARGET) or not row.path:
        return None
    metric, _op, value = row.constraint
    need = value / (1 + int(bool(differential))) if metric == _METRIC_SWING else value
    if metric == _METRIC_MARGIN:
        if ctx.input_dc_v is None:
            return None
        return row.hi_edge_v - ctx.input_dc_v - value, ctx.input_dc_v - row.lo_edge_v - value
    declared = ctx.node_targets.get(row.net)
    if metric == _METRIC_SWING and declared is not None:
        return row.hi_edge_v - (declared + need / 2), (declared - need / 2) - row.lo_edge_v
    # 출력 DC 가 선언되지 않았다: 남는 여유(창 폭 − 요구)를 위·아래 부분 기둥의 남는 여유 중 최솟값이 가장 커지도록 나눈다(41 §6.2) -- 두 부분 기둥이 같은 몫을 가질 때다.
    # 한쪽 사슬이 비면(소자 없음) 그쪽은 몫이 의미가 없으므로 다른 쪽이 전부 가진다. 소자 k 의 예산은 '나머지는 최소로 두고 k 가 가질 수 있는 최대'라서 자기 사슬 몫 전체를 쓴다.
    lower, upper = _chains(row)
    rest = row.upper_bound_v - need
    sides = int(bool(lower)) + int(bool(upper))
    share = rest / sides if sides else 0.0
    return share if upper else 0.0, share if lower else 0.0


def _budgets(ctx, edges):
    local = types.SimpleNamespace(cls=ctx.cls, pins=ctx.pins, kind=ctx.kinds)
    nets = sorted({n for d in ctx.devices for n in (d.drain, d.gate, d.source)} | set(ctx.rail_v))
    windows = [(WINDOW_BUFFER, n) for n in nets]
    ports = sorted(ctx.port_direction)
    windows += [(WINDOW_INPUT, n) for n in ports if ctx.port_direction[n] == INPUT_DIRECTION]
    windows += [(WINDOW_OUTPUT, n) for n in ports if ctx.port_direction[n] == OUTPUT_DIRECTION]
    differential = {ROLE_DIFFERENTIAL_OUTPUT_P, ROLE_DIFFERENTIAL_OUTPUT_N} <= {
        ctx.port_role.get(n) for n in ports if ctx.port_direction[n] == OUTPUT_DIRECTION}
    constraints = tuple(c for c in ctx.constraints if c[0] in _HEADROOM_METRICS)
    result = headroom_bound(local, ctx.rail_v, edges, tuple(windows), constraints, ctx.input_dc_v, differential)
    rows = dict(zip(windows, result.rows))
    column = {}
    for d in ctx.devices:
        for edge, (lo, hi) in _edge_nets(d.kind, d.drain, d.gate, d.source).items():
            low, high = rows.get((WINDOW_BUFFER, lo)), rows.get((WINDOW_BUFFER, hi))
            if low is None or high is None or STATUS_UNKNOWN in (low.status, high.status):
                continue
            column[(d.name, edge)] = high.hi_edge_v - low.lo_edge_v
    window = {}
    for key, row in rows.items():
        if key[0] == WINDOW_BUFFER:
            continue
        slack = _slacks(row, ctx, differential)
        if slack is None:
            continue
        lower, upper = _chains(row)
        for chain, room in ((lower, slack[1]), (upper, slack[0])):
            for dev, edge, _lo, _hi, cost in chain:
                budget = cost + room
                window[(dev, edge)] = budget if (dev, edge) not in window else min(window[(dev, edge)], budget)
    return {key: min(value, window.get(key, value)) for key, value in column.items()}


def _lower_bound(bundle, edge, budget):
    """엣지 예산 -> (하한 gm/ID 또는 None, 출처 식 이름, 어긋남 V). 어긋남 = 곡선 전체에서 가장 가까운 값이 예산을 넘는 크기(하한이 없을 때만 양수)."""
    if edge == EDGE_VDS:
        curve = bundle[QUANTITY_VDSAT]
        level, values, source = budget, curve.values, SRC_HEADROOM_VDSAT
    else:
        curve = bundle[QUANTITY_FT]
        level, values, source = budget, curve.vgs, SRC_HEADROOM_VGS
    found = hull(curve.gm_id, values, level, below=True)
    return (None if found is None else found[0]), source, float(min(values) - level)


def headroom_bounds(ctx, lengths, budgets=None):
    if ctx.rail_v == {} or not ctx.devices:
        return HeadroomBounds({}, (), ((SRC_HEADROOM_VDSAT, WHY_NO_RAILS),), {})
    edges = {k: edge_cost(ctx, k) for k in sorted({d.kind for d in ctx.devices})}
    budgets = _budgets(ctx, edges) if budgets is None else budgets
    out, conflicts, inactive = {}, [], []
    for d in ctx.devices:
        bundle = curve_bundle(ctx, d.kind, lengths[d.name])
        if bundle is None:
            continue
        found = []
        for edge in (EDGE_VDS, EDGE_VGS):
            budget = budgets.get((d.name, edge))
            if budget is None:
                continue
            if edge == EDGE_VDS and QUANTITY_VDSAT not in bundle:               # VDSAT 열 없음: 이 경계는 비활성, 대체값 없음
                if (SRC_HEADROOM_VDSAT, REASON_VDSAT_COLUMN_UNAVAILABLE) not in inactive:
                    inactive.append((SRC_HEADROOM_VDSAT, REASON_VDSAT_COLUMN_UNAVAILABLE))
                continue
            value, source, gap = _lower_bound(bundle, edge, budget)
            if value is None:
                conflicts.append(StartConflict(d.name, QUANTITY_GM_ID, ((source, budget),), gap))
            else:
                found.append(Bound(QUANTITY_GM_ID, SIDE_LO, source, value))
        out[d.name] = tuple(found)
    return HeadroomBounds(out, tuple(conflicts), tuple(inactive), budgets)
