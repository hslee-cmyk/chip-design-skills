"""탐색 축 front -- 양 끝점 + ε 두 방향 스윕 + 비지배 필터 + L-b (설계 design_mod6_search_front 6.3, DEC-77·80, LR10).

진입점: `sweep_front(sctx, starts) -> dict`(키: solves, front, pending_front, failed_eps, resolution, lb_stops, *_removed, *_folded).

1. 양 끝점: 시작점(분지 = 시작점마다, L-c multi-start)마다 전력 최소·면적 최소를 ε 없이 푼다. 축별 최솟값 해가 E_P·E_A.
2. ε 격자: 면적 방향 = A(E_A) < ε_A < A(E_P) 를 b_A 간격으로 E_P 쪽부터(전력 최소화, 직전 해 warm start), 전력 방향 =
   P(E_P) < ε_P < P(E_A) 를 b_P 간격으로 E_A 쪽부터(면적 최소화). 격자의 b_P = max(b_P(E_P), b_P(E_A)). 두 방향을 모두 돈다.
3. 예산 게이트(DEC-80, **평가 수로 센다 -- 결정론**): ε 점 총수 > N_ε = ⌊(E_B − E_fixed)/e_ε⌋ 이면 간격을 2배씩 넓히고 배수를
   기록('해상도 굵음'). E_B = `sctx.eval_budget`, E_fixed = 끝점까지의 kernel_calls, e_ε = 끝점 풀이 하나의 kernel_calls 중앙값.
   판정 축 재필터 몫(T_refilter)은 MOD8 미구현이라 0(기록).
4. 비지배 필터(`nondominated`): 축 (power_dc_w, area_search_m2), 동률 폭 = (두 점 b_P 중 큰 값, b_A), slack = 활성 제약 c 합.
   **봉인된 점(`STATUS_SEALED`)만 최종 front** 로, 봉인 7 대기 점(`STATUS_PENDING_SEAL7`)은 따로 `pending_front` 로 거른다
   (`seal7_pending` 스위치 -- 대기 점은 최종 front 에 들어가지 못한다).
5. L-b(`polish_l_cells`)는 필터를 통과한 점에만 돌리고 새 점을 4 로 되돌린다(한 번). L-b 실행마다 `{"class", "l_from", "stop", "accepted"}` 를 실행 순서대로 `lb_stops`(tuple) 에 모은다.
"""
import math
import statistics

from .l_bin_search import polish_l_cells
from .pareto import nondominated
from .search_values import AXIS_AREA, AXIS_POWER, STATUS_PENDING_SEAL7, STATUS_SEALED, FrontPoint, StartPoint
from .slsqp_outer import solve_eps


def _value(result, axis):
    return result.objectives.power_w if axis == AXIS_POWER else result.objectives.area_m2


def _warm(solve, tag):
    best = solve.best
    return StartPoint(tag, best.theta, best.key.cells, "warm")


_CLASSES = (
    # (이름, 상태, ss 제약 모두 측정됨 요구) -- 최종 front = 봉인 + 모두 측정(미측정이 있으면 만족을 판정할 수 없다, S-1)
    ("front", STATUS_SEALED, True),
    ("unmeasured_front", STATUS_SEALED, False),
    ("pending_front", STATUS_PENDING_SEAL7, None),
)


def _filter(sctx, entries, status, measured):
    pool = [(pid, s) for pid, s in entries if s.best is not None and s.best.status == status
            and (measured is None or (not s.best.unmeasured) == measured)]
    points = tuple((pid, (s.best.objectives.power_w, s.best.objectives.area_m2),
                    sum(r.c for r in s.best.constraints if r.active)) for pid, s in pool)
    b_p = {pid: s.best.objectives.power_resolution_w for pid, s in pool}
    res = nondominated(points, (lambda p, q: max(b_p[p], b_p[q]), sctx.domain.area_resolution_m2))
    by = {i: points[k][0] for i, k in res.dominated}
    kept = tuple(FrontPoint(pool[i][0], pool[i][1].best, (("minimize", pool[i][1].minimize), ("eps", pool[i][1].eps)))
                 for i in res.kept)
    removed = tuple((pool[i][0], by[i]) for i in sorted(by))
    return kept, removed, tuple((pool[i][0], pool[k][0]) for i, k in res.folded)


def _grid(lo, hi, step):
    if not (math.isfinite(lo) and math.isfinite(hi)) or hi <= lo or step <= 0:
        return ()
    count = int(math.floor((hi - lo) / step))
    return tuple(hi - k * step for k in range(1, count + 1) if hi - k * step > lo)


def _count(span, factor):
    """격자 점 수 상계(만들지 않고 센다): 열린 구간 (lo, hi) 안 hi − k·step 점 수."""
    lo, hi, step = span
    if not (math.isfinite(lo) and math.isfinite(hi)) or hi <= lo:
        return 0
    return max(int(math.ceil((hi - lo) / (step * factor))) - 1, 0)


def sweep_front(sctx, starts):
    entries, failed, costs = [], [], []
    for start in starts:
        for axis in (AXIS_POWER, AXIS_AREA):
            k0 = sctx.counters["kernel_calls"]
            solve = solve_eps(sctx, start, axis, None, (("start", start.start_id), ("endpoint", axis)))
            costs.append(sctx.counters["kernel_calls"] - k0)
            entries.append(("E" + axis[0].upper() + ":" + start.start_id, solve))
            if solve.best is None:
                failed.append({"eps": None, "minimize": axis, "start": start.start_id, "stop": solve.stop,
                               "aborts": list(solve.aborts), "accepted": len(solve.history)})
    solved = [s for _p, s in entries if s.best is not None]
    resolution = {"b_A_m2": sctx.domain.area_resolution_m2, "b_P_rule": "sum_rails_abs_V_times_tol_I",
                  "estimated": True, "coarse_factor": 1, "E_refilter": 0, "refilter": "mod8_not_implemented",
                  "E_B": sctx.eval_budget}
    e_p = min((s for s in solved if s.minimize == AXIS_POWER), key=lambda s: (_value(s.best, AXIS_POWER), s.best.seq),
              default=None)
    e_a = min((s for s in solved if s.minimize == AXIS_AREA), key=lambda s: (_value(s.best, AXIS_AREA), s.best.seq),
              default=None)
    if e_p is not None and e_a is not None:
        e_eps = statistics.median(costs)
        e_fixed = sctx.counters["kernel_calls"]
        n_eps = int(math.floor((sctx.eval_budget - e_fixed) / e_eps)) if e_eps > 0 and sctx.eval_budget else 0
        resolution.update(E_B=sctx.eval_budget)
        b_p = max(e_p.best.objectives.power_resolution_w, e_a.best.objectives.power_resolution_w)
        span_a = (_value(e_a.best, AXIS_AREA), _value(e_p.best, AXIS_AREA), sctx.domain.area_resolution_m2)
        span_p = (_value(e_p.best, AXIS_POWER), _value(e_a.best, AXIS_POWER), b_p)
        factor = 1
        while _count(span_a, factor) + _count(span_p, factor) > max(n_eps, 0):
            factor *= 2
        grid_a = _grid(span_a[0], span_a[1], span_a[2] * factor)
        grid_p = _grid(span_p[0], span_p[1], span_p[2] * factor)
        resolution.update(N_eps=n_eps, e_eps=e_eps, E_fixed=e_fixed, coarse_factor=factor, b_P_grid_w=b_p)
        for axis, minimize, grid, anchor in ((AXIS_AREA, AXIS_POWER, grid_a, e_p), (AXIS_POWER, AXIS_AREA, grid_p, e_a)):
            previous = anchor
            for k, bound in enumerate(grid):
                tag = "eps:" + axis + ":" + str(k + 1)
                solve = solve_eps(sctx, _warm(previous, tag), minimize, (axis, bound), (("eps_point", tag),))
                entries.append((tag, solve))
                if solve.best is None:
                    failed.append({"eps": [axis, bound], "minimize": minimize, "stop": solve.stop,
                                   "aborts": list(solve.aborts), "accepted": len(solve.history)})
                else:
                    previous = solve
    out = {"failed_eps": tuple(failed), "resolution": tuple(sorted(resolution.items()))}
    lb_stops = []
    for name, status, measured in _CLASSES:
        kept, removed, folded = _filter(sctx, entries, status, measured)
        solves = dict(entries)
        extra = []
        for point in kept:
            accepted, stop = polish_l_cells(sctx, solves[point.point_id], (("l_from", point.point_id),))
            lb_stops.append({"class": name, "l_from": point.point_id, "stop": stop, "accepted": len(accepted)})     # [NFR-4] L-b 실행마다 정지 사유(실행 순서)
            for n, new in enumerate(accepted):
                extra.append(("L:" + point.point_id + ":" + str(n + 1), new))
        if extra:
            entries.extend(extra)
            kept, removed, folded = _filter(sctx, entries, status, measured)
    for name, status, measured in _CLASSES:          # L-b 새 점이 다른 묶음에 들 수 있어 마지막 entries 로 한 번 더 거른다
        kept, removed, folded = _filter(sctx, entries, status, measured)
        out[name] = kept
        out[name + "_removed"] = removed
        out[name + "_folded"] = folded
    out["solves"] = tuple(entries)
    out["lb_stops"] = tuple(lb_stops)
    return out
