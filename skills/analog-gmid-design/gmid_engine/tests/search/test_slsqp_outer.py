"""CONTRACT 3.13 [r2] `solve_eps(sctx, start, minimize, eps, origin) -> SolveResult`.

- 시작점이 받아들일 상태가 아니면 즉시 (None, ..., "start_<사유>", ()).
- best = 수락 반복 중 모든 c ≥ 0 이고 (목적, seq) 최소; ε 행 (ε − 값)/분해능 ≥ 0.
- 한도: maxiter = max(1, Σ max(⌈log2((hi−lo)/hᵢ)⌉, 1)), 재시작 상한 = max(1, ⌈log2(max 반경 / 최소 hᵢ)⌉) (hᵢ = 시작점 FD 스텝);
  새 x 평가 전 kernel_calls ≥ E_B -> stop eval_budget, perf_counter > deadline -> wall_budget.
- FD 열 양방향 실패 -> 열 고정(aborts "frozen:<kind>:<key>", frozen) (S-16).
"""
import math
import time

import pytest

from gmid_engine.search import (
    ACCEPTED_STATUSES,
    AXIS_AREA,
    AXIS_POWER,
    SolveResult,
    StartPoint,
    evaluate,
    solve_eps,
    start_points,
)

from .conftest import (
    CELLS_C,
    build_case,
    circuit_c,
    circuit_p,
    expected_fd_steps,
    theta_p,
    theta_r4c,
)


def _start(case, th):
    starts, _ = start_points(case.sctx, [th])
    assert len(starts) == 1
    return starts[0]


def _feasible(r):
    return all(c.c >= 0 for c in r.constraints) and all(c.c >= 0 for c in r.cone)


def test_start_not_accepted(tmp_path, lut_sealed):
    case = build_case(tmp_path, circuit_c(), lut_sealed)
    bad = StartPoint("sx", tuple(sorted(theta_r4c(y=0.1, v1=1.5).items())), CELLS_C, "given")
    r = solve_eps(case.sctx, bad, AXIS_POWER, None, ("t",))
    assert isinstance(r, SolveResult)
    assert r.best is None and r.iterations == 0 and r.restarts == 0 and tuple(r.history) == ()
    assert r.stop.startswith("start_") and r.minimize == AXIS_POWER and r.eps is None


@pytest.mark.parametrize("axis", [AXIS_POWER, AXIS_AREA])
def test_minimize_from_start_bounded_by_limits(tmp_path, lut_sealed, axis):
    case = build_case(tmp_path, circuit_c(), lut_sealed, eval_budget=400)
    s = case.sctx
    sp = _start(case, theta_r4c())
    start_res = evaluate(s, sp.theta, sp.cells)
    hs = expected_fd_steps(s, start_res)
    r = solve_eps(s, sp, axis, None, ("t",))
    assert r.best is not None and r.best.status in ACCEPTED_STATUSES and _feasible(r.best)
    key = "power_w" if axis == AXIS_POWER else "area_m2"
    assert getattr(r.best.objectives, key) <= getattr(start_res.objectives, key)
    vs = s.domain.variables
    used = [(v, h) for v, h in zip(vs, hs) if h]
    maxiter = max(1, sum(max(math.ceil(math.log2((v.hi - v.lo) / h)), 1) for v, h in used))
    cap = max(1, math.ceil(math.log2(max((v.hi - v.lo) / 2 for v, _ in used) / min(h for _, h in used))))
    assert r.iterations <= maxiter
    assert r.restarts <= cap
    assert dict(s.counters)["recompute_same_key"] == 0


def test_eps_constraint_respected(tmp_path, lut_sealed):
    case = build_case(tmp_path, circuit_c(), lut_sealed, eval_budget=400)
    s = case.sctx
    sp = _start(case, theta_r4c())
    a0 = evaluate(s, sp.theta, sp.cells).objectives.area_m2
    eps = (AXIS_AREA, 0.8 * a0)
    r = solve_eps(s, sp, AXIS_POWER, eps, ("t",))
    assert tuple(r.eps) == eps
    if r.best is not None:
        assert r.best.objectives.area_m2 <= eps[1]
        assert _feasible(r.best)


def test_eval_budget_stop(tmp_path, lut_sealed):
    case = build_case(tmp_path, circuit_c(), lut_sealed, eval_budget=3)
    s = case.sctx
    sp = _start(case, theta_r4c())
    r = solve_eps(s, sp, AXIS_POWER, None, ("t",))
    assert r.stop == "eval_budget"
    n = len(s.domain.variables)
    assert dict(s.counters)["kernel_calls"] <= 3 + n + 1         # S-17: FD 한 번만큼 넘을 수 있다


def test_wall_budget_stop(tmp_path, lut_sealed):
    case = build_case(tmp_path, circuit_c(), lut_sealed, eval_budget=400)
    s = case.sctx
    sp = _start(case, theta_r4c())
    s.deadline = time.perf_counter() - 1.0
    r = solve_eps(s, sp, AXIS_POWER, None, ("t",))
    # x0 = exp(ln θ) 가 시작 θ 와 1 ulp 달라 첫 평가도 '새 x' -> 'start_' 접두가 붙을 수 있다(계약 문장은 wall_budget, 모호점 보고).
    assert r.stop in ("wall_budget", "start_wall_budget")
    assert r.best is None


def test_fd_column_both_ways_out_freezes_variable(tmp_path, lut_sealed):
    rv = 9e4
    case = build_case(tmp_path, circuit_p(), lut_sealed, elements=(("R1", "resistor", None),),
                      rbounds=(rv * (1 - 1e-9), rv * (1 + 1e-9)), eval_budget=200)
    sp = _start(case, theta_p(case.dc, r=rv))
    r = solve_eps(case.sctx, sp, AXIS_POWER, None, ("t",))
    assert "frozen:resistance:R1" in tuple(r.aborts)
    assert any(getattr(f, "component", f) == ("resistance", "R1") for f in r.frozen)
    if r.best is not None:
        assert dict(r.best.theta)[("resistance", "R1")] == pytest.approx(rv, rel=2e-9)


def test_deterministic_rerun(tmp_path, lut_sealed):
    out = []
    for k in ("a", "b"):
        case = build_case(tmp_path / k, circuit_c(), lut_sealed, eval_budget=400)
        sp = _start(case, theta_r4c())
        r = solve_eps(case.sctx, sp, AXIS_POWER, None, ("t",))
        out.append((r.stop, r.iterations, r.restarts, None if r.best is None else r.best.theta,
                    dict(case.sctx.counters)["kernel_calls"]))
    assert out[0] == out[1]


# ---------------------------------------------------------------- [r5] 시작 θ 재사용 · stop 어휘 · [r6] x 복사

STOPS = {"start_candidate_failure", "start_constraint_set_changed", "start_eval_budget", "start_wall_budget", "converged",
         "eval_budget", "wall_budget", "restart_cap", "all_columns_frozen", "candidate_failure", "constraint_set_changed"}


def _stop_ok(stop):
    return stop in STOPS or (stop.startswith("slsqp_") and stop[len("slsqp_"):].lstrip("-").isdigit()) \
        or stop.startswith("start_")


def test_start_theta_reused_no_extra_kernel(tmp_path, lut_sealed):
    """r5 효율 수정: bounds 로 잘리지 않은 성분은 시작 θ 원값 -> 시작점 평가는 캐시 적중(같은 객체), 1 ulp 옆 키 재평가 0."""
    case = build_case(tmp_path, circuit_c(), lut_sealed, eval_budget=400)
    s = case.sctx
    sp = _start(case, theta_r4c())
    start_res = evaluate(s, sp.theta, sp.cells)
    r = solve_eps(s, sp, AXIS_POWER, None, ("t",))
    assert r.history and r.history[0] is start_res
    near = [h for h in r.history[1:] if h.key != start_res.key and all(
        abs(a - b) <= 4 * math.ulp(b) for (_, a), (_, b) in zip(h.theta, start_res.theta))]
    assert near == []


def test_history_points_key_matches_their_theta(tmp_path, lut_sealed):
    """r6 x 복사 불변식: 저장된 수락 점마다 키의 theta_hex = 그 점 θ 의 float.hex (저장 x 와 키 θ 불일치 0)."""
    from gmid_engine.search import eval_key
    case = build_case(tmp_path, circuit_c(), lut_sealed, eval_budget=400)
    s = case.sctx
    sp = _start(case, theta_r4c())
    r = solve_eps(s, sp, AXIS_AREA, None, ("t",))
    assert len(r.history) >= 2
    for h in r.history:
        assert h.key == eval_key(s.context_fp, s.schema_fp, h.theta, h.key.cells, h.key.w_fixed_fp)
    assert r.best.key == eval_key(s.context_fp, s.schema_fp, r.best.theta, r.best.key.cells, None)


def test_stop_vocabulary_complete(tmp_path, lut_sealed):
    """r5: stop 은 완전 목록 안 -- 끝점·ε·L-b 풀이 모두."""
    from gmid_engine.search import sweep_front
    case = build_case(tmp_path, circuit_c(), lut_sealed, eval_budget=60)
    starts, _ = start_points(case.sctx, [theta_r4c()])
    out = sweep_front(case.sctx, starts)
    stops = [r.stop for _, r in out["solves"]] + [dict(e)["stop"] for e in out["failed_eps"]]
    assert stops and all(_stop_ok(x) for x in stops), stops


# ---------------------------------------------------------------- [r11, 결정 11] SLSQP 입력 척도 (search CONTRACT 10.x)
# 계약: SLSQP 에 넘기는 행·목적에만 양의 상수 배를 곱한다 -- 가능 집합·best 판정(원 c ≥ 0)·SolveResult 값은 그대로.
# oracle (a): 면적 예산 행 c = (A − 면적)/b_A 를 이 test 가 결과 목적값과 b_A 로 다시 계산해 원 값과 대조(척도 배가 새면 어긋난다),
# best 는 같은 키의 평가 결과 객체 그 자체(캐시 적중 `is`) -- 값이 바뀌지 않았다는 직접 증거.

A_BIG = 5e-9            # 회로 C 시작점 면적 ≈ 6.7e-11 m², b_A = 5e-15 m² -> 시작점 예산 행 c ≈ 1e6 (크기 1e6 급 행, 구성 입력)


@pytest.mark.parametrize("axis", [AXIS_AREA, AXIS_POWER])
def test_large_area_row_best_judged_on_raw_c(tmp_path, lut_sealed, axis):
    case = build_case(tmp_path, circuit_c(), lut_sealed, eval_budget=400,
                      constraints=(("area_search_m2", "<=", A_BIG, None),))
    s = case.sctx
    b_a = s.domain.area_resolution_m2
    sp = _start(case, theta_r4c())
    start_res = evaluate(s, sp.theta, sp.cells)
    (row0,) = [c for c in start_res.constraints if c.name == "spec:area_search_m2<="]
    assert row0.c > 1e5                                         # 입력 확인: 크기 1e6 급 행
    r = solve_eps(s, sp, axis, None, ("t",))
    assert r.best is not None and r.best.status in ACCEPTED_STATUSES and _feasible(r.best)
    key = "power_w" if axis == AXIS_POWER else "area_m2"
    assert getattr(r.best.objectives, key) <= getattr(start_res.objectives, key)
    assert evaluate(s, r.best.theta, r.best.key.cells) is r.best              # 캐시 적중 = 같은 평가 결과(값 불변)
    for h in (r.best,) + tuple(r.history):
        (row,) = [c for c in h.constraints if c.name == "spec:area_search_m2<="]
        assert row.c == pytest.approx((A_BIG - h.objectives.area_m2) / b_a, rel=1e-9)
    # best = 수락 반복 중 모든 원 c ≥ 0 이고 목적 최소(3.13) -- 원 c 로 다시 고른 것과 같다
    feas = [h for h in r.history if _feasible(h)]
    assert feas                                                     # 시작점이 예산 안 -> 적어도 시작점
    assert getattr(r.best.objectives, key) <= min(getattr(h.objectives, key) for h in feas)
