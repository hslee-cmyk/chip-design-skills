"""헤드룸 달성가능성 -- 출력·입력·버퍼 창 상한 (설계 41 §4.6, D-GB4f·D-J5; GB4 단계 A7 `headroom`).

진입점: `headroom_bound(local, rail_v, edges, windows, constraints, input_dc_v, differential_out) -> HeadroomResult`.

* `local` = `LocalInputs`(소자 핀·kind), `rail_v` = {레일 넷: 전위 V}, `edges` = {kind: `EdgeCost`}(`edge_costs`),
  `windows` = ((창 종류, 넷), ...) 창을 구할 넷(출력 포트 → output, 입력 포트 → input, 버퍼 블록 입력 → buffer),
  `constraints` = ((metric, op, 값), ...) 선언 제약, `input_dc_v` = 선언 입력 DC(V; SP-2 대기면 None), `differential_out` = 출력 포트가 차동 쌍이면 True.

**경로 그래프**(구조만 쓴다, 이름 없음): 위쪽으로 향하는 엣지 -- nmos: 소스→드레인(VDS 엣지, 비용 = VDSAT 최솟값 + tol_vdsat 최솟값), 소스→게이트(VGS 엣지, 비용 = 전도·포화를 지키는 |VGS| 최솟값);
pmos: 드레인→소스(VDS), 게이트→소스(VGS). 레일은 전위가 고정된 시작/끝. 엣지 비용은 그 kind 의 LUT 격자 전수 최솟값이라 서로 다른 소자를 독립으로 최소화한 값이다 --
실제 창 폭의 **상한**이다(41 §4.6 '상한 계산(인증)'). 저항·이상원은 엣지로 세지 않는다(전압 강하의 방향·크기를 모른다 -- 없는 제약은 창을 더 넓게 둘 뿐이라 상한은 안전하다).
넷 n 의 창 경계 = [max(레일 최저, L(n)), min(레일 최고, U(n))], L(n) = 레일에서 n 까지 위쪽 경로의 (레일 전위 + 비용 합) 최댓값(longest path), U(n) = n 에서 레일까지의
(레일 전위 − 비용 합) 최솟값. 폭 = U − L (비면 음수 = 부족량). 길이 최장 경로는 상태 (넷, VGS 엣지 지났는가) 위의 완화(Bellman–Ford 식, 라운드 상한 = 상태 수)로 구하고
라운드 상한 안에 끝나지 않으면(비용 양수 사이클) 그 창은 **미상**이다.
**대상 창**: 레일–레일 경로가 VGS 엣지를 하나 이상 지나는 넷만(41 §4.6 '대상'); 그 밖 넷은 `eligible` 아님 -- 계산해 보고하되 정지 근거로 쓰지 않는다.

**판정**(§4.3 과 같은 규칙, 정지는 인증된 대상 창에만):
* `swing_out_v >= S`: 출력 창 폭 상한 × (출력 포트가 차동 쌍이면 2 -- 차동 p-p, 40 §3.8-8) < S 이면 `headroom_unattainable`.
* `icmr_v >= w`: 입력 창 폭 상한(입력 포트 중 최솟값) < w.
* `icm_margin_v >= m`: 선언 입력 DC V 가 [L, U] 바깥 거리 < m(창 경계 바깥 한계 기준). 입력 DC 가 대기면(None) 보고만.
* 선언 제약이 없는 창(포화 전용 -- 버퍼 창 등)은 `verdict` = no_target 으로 보고(`buffer_window_report`).
**짧은 L bin 경고**: 입력 창 최장 경로의 VGS 엣지 kind 마다 L bin 별 폭 상한을 그 kind 의 엣지 비용만 그 bin 값으로 바꿔 구하고(다른 kind 는 전체 최솟값),
폭이 양인 bin 이 맨 아래(가장 짧은 L) bin 하나뿐이면 `icmr_window_short_l_bin{kind, bin, upper_bound_by_bin}`.
"""
import dataclasses

from .achievability_types import (
    REASON_HEADROOM,
    STATUS_CERTIFIED,
    STATUS_UNKNOWN,
    VERDICT_INFEASIBLE,
    VERDICT_NO_TARGET,
    VERDICT_NOT_EXCLUDED,
    VERDICT_UNDETERMINED,
    WARN_SHORT_L_BIN,
    WINDOW_INPUT,
    WINDOW_OUTPUT,
    HeadroomRow,
)

METRIC_SWING = "swing_out_v"
METRIC_ICMR = "icmr_v"
METRIC_MARGIN = "icm_margin_v"
EDGE_VGS = "vgs"
EDGE_VDS = "vds"
KIND_PMOS = "pmos"


@dataclasses.dataclass(frozen=True)
class HeadroomResult:
    """`rows` = 모든 창 `HeadroomRow`, `stops` = 정지 근거((코드, 상세 쌍들), ...), `warnings` = 경고((코드, 상세 쌍들), ...)."""

    rows: tuple
    stops: tuple
    warnings: tuple


def _edges(local, edges):
    """위쪽 엣지 목록 ((아랫 넷, 윗 넷, 비용, 소자, 엣지 종류, kind), ...)."""
    out = []
    for name, cls in sorted(local.cls.items()):
        if cls != "mos":
            continue
        pins, kind = local.pins[name], local.kind[name]
        cost = edges[kind]
        if kind == KIND_PMOS:
            out.append((pins["d"], pins["s"], cost.vds_min_v, name, EDGE_VDS, kind))
            out.append((pins["g"], pins["s"], cost.vgs_min_v, name, EDGE_VGS, kind))
        else:
            out.append((pins["s"], pins["d"], cost.vds_min_v, name, EDGE_VDS, kind))
            out.append((pins["s"], pins["g"], cost.vgs_min_v, name, EDGE_VGS, kind))
    return out


def _relax(nets, rails, rail_v, edge_list, upward):
    """(넷, VGS 지났는가) 상태 위의 최장(아래→위) 또는 최단(위→아래) 경로. -> ({상태: (값, 선행 엣지, 선행 상태)}, 순환 여부)."""
    best = {(r, False): (rail_v[r], None, None) for r in rails}
    for _ in range(2 * (len(nets) + 1)):
        changed = False
        for edge in edge_list:
            lo, hi, cost, _dev, etype, _kind = edge
            src, dst = (lo, hi) if upward else (hi, lo)
            for flag in (False, True):
                if (src, flag) not in best:
                    continue
                value = best[(src, flag)][0] + (cost if upward else -cost)
                state = (dst, flag or etype == EDGE_VGS)
                if state not in best or (value > best[state][0] if upward else value < best[state][0]):
                    best[state] = (value, edge, (src, flag))
                    changed = True
        if not changed:
            return best, False
    return best, True


def _walk(best, state):
    """상태에서 레일까지 선행 엣지 열(상태 쪽부터). 선행 사슬이 상태 수 안에 레일에 닿지 않으면(양수 사이클) 빈 열 -- 그 창은 어차피 미상."""
    chain = []
    while best[state][1] is not None:
        if len(chain) >= len(best):
            return []
        chain.append(best[state][1])
        state = best[state][2]
    return chain


def _values(best, net):
    return {flag: best[(net, flag)][0] for flag in (False, True) if (net, flag) in best}


def headroom_bound(local, rail_v, edges, windows, constraints, input_dc_v, differential_out):
    edge_list = _edges(local, edges)
    nets = sorted({n for e in edge_list for n in (e[0], e[1])} | set(rail_v))
    rails = sorted(rail_v)
    low, low_cycle = _relax(nets, rails, rail_v, edge_list, True)
    high, high_cycle = _relax(nets, rails, rail_v, edge_list, False)
    v_min, v_max = min(rail_v.values()), max(rail_v.values())
    rows, stops, warnings = [], [], []
    for kind, net in windows:
        lows, highs = _values(low, net), _values(high, net)
        lo_edge = max([v_min] + list(lows.values()))
        hi_edge = min([v_max] + list(highs.values()))
        eligible = (True in lows and bool(highs)) or (bool(lows) and True in highs)
        width = hi_edge - lo_edge
        path = ()
        if lows:
            path += tuple(reversed(_walk(low, (net, max(lows, key=lows.get)))))
        if highs:
            path += tuple(_walk(high, (net, min(highs, key=highs.get))))
        derivation = tuple((e[3], e[4], e[2], e[5]) for e in path)
        status = STATUS_UNKNOWN if low_cycle or high_cycle else STATUS_CERTIFIED
        best_row = next((edges[e[5]].best_row for e in path if e[4] == EDGE_VGS), ())
        verdict, constraint = _judge(kind, width, lo_edge, hi_edge, constraints, input_dc_v, differential_out, eligible, status)
        rows.append(HeadroomRow(kind, net, tuple((e[3], e[4], e[0], e[1], e[2]) for e in path), width, lo_edge, hi_edge,
                                tuple(sorted({e[3] for e in path})), best_row, status, verdict, constraint, derivation))
        if verdict == VERDICT_INFEASIBLE:
            stops.append((REASON_HEADROOM, (("metric", constraint[0]), ("window", kind), ("net", net), ("upper_bound", width),
                                            ("target", constraint[2]), ("derivation", derivation))))
        if kind == WINDOW_INPUT and status == STATUS_CERTIFIED and eligible:
            warn = _short_l_bin(edges, path, width)
            if warn is not None:
                warnings.append((WARN_SHORT_L_BIN, warn))
    return HeadroomResult(tuple(rows), tuple(stops), tuple(warnings))


def _short_l_bin(edges, path, width):
    kinds = sorted({e[5] for e in path if e[4] == EDGE_VGS})
    for kind in kinds:
        count = sum(1 for e in path if e[4] == EDGE_VGS and e[5] == kind)
        by_bin = []
        for b, cost in edges[kind].vgs_min_by_bin:
            by_bin.append((b, width + (edges[kind].vgs_min_v - cost) * count))
        positive = [b for b, w in by_bin if w > 0]
        if len(by_bin) > 1 and positive == [by_bin[0][0]]:
            return (("kind", kind), ("bin", by_bin[0][0]), ("upper_bound_by_bin", tuple(by_bin)))
    return None


def _judge(kind, width, lo_edge, hi_edge, constraints, input_dc_v, differential_out, eligible, status):
    if status != STATUS_CERTIFIED:
        return VERDICT_UNDETERMINED, None
    for metric, op, value in constraints:
        if op != ">=":
            continue
        if metric == METRIC_SWING and kind == WINDOW_OUTPUT:
            bound = width * (1 + int(bool(differential_out)))
        elif metric == METRIC_ICMR and kind == WINDOW_INPUT:
            bound = width
        elif metric == METRIC_MARGIN and kind == WINDOW_INPUT:
            if input_dc_v is None:
                return VERDICT_UNDETERMINED, (metric, op, value)
            bound = min(input_dc_v - lo_edge, hi_edge - input_dc_v)
        else:
            continue
        if not eligible:
            return VERDICT_NO_TARGET, (metric, op, value)
        return (VERDICT_INFEASIBLE if bound < value else VERDICT_NOT_EXCLUDED), (metric, op, value)
    return VERDICT_NO_TARGET, None
