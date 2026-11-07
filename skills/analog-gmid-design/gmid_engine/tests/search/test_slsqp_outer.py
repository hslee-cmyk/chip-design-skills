"""CONTRACT 3.13 [r2] `solve_eps(sctx, start, minimize, eps, origin) -> SolveResult`.

- 시작점이 받아들일 상태가 아니면 즉시 (None, ..., "start_<사유>", ()).
- best = 수락 반복 중 모든 c ≥ 0 이고 (목적, seq) 최소; ε 행 (ε − 값)/분해능 ≥ 0.
- 한도: maxiter = max(1, Σ max(⌈log2((hi−lo)/hᵢ)⌉, 1)), 재시작 상한 = max(1, ⌈log2(max 반경 / 최소 hᵢ)⌉) (hᵢ = 시작점 FD 스텝);
  새 x 평가 전 kernel_calls ≥ E_B -> stop eval_budget, perf_counter > deadline -> wall_budget.
- FD 열 양방향 실패 -> 열 고정(aborts "frozen:<kind>:<key>", frozen) (S-16).
"""
import importlib
import math
import time

import pytest

from gmid_engine.core import fp_of
from gmid_engine.search import (
    ACCEPTED_STATUSES,
    AXIS_AREA,
    AXIS_POWER,
    SolveResult,
    StartPoint,
    evaluate,
    initial_wf,
    solve_eps,
    start_points,
)

from .conftest import (
    CELLS_C,
    CELLS_P,
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
    bad = StartPoint("sx", tuple(sorted(theta_r4c(y=0.1, v1=1.5).items())), CELLS_C, initial_wf(case.sctx.dc.base), "given")   # [FS-1 A-196] StartPoint(start_id, theta, cells, wf, source) -- wf = 출발 블록 값(입력 구성)
    r = solve_eps(case.sctx, bad, AXIS_POWER, None, ("t",))
    assert isinstance(r, SolveResult)
    assert r.best is None and r.iterations == 0 and r.restarts == 0 and tuple(r.history) == ()
    assert r.stop.startswith("start_") and r.minimize == AXIS_POWER and r.eps is None


@pytest.mark.parametrize("axis", [AXIS_POWER, AXIS_AREA])
def test_minimize_from_start_bounded_by_limits(tmp_path, lut_sealed, axis):
    case = build_case(tmp_path, circuit_c(), lut_sealed, eval_budget=400)
    s = case.sctx
    sp = _start(case, theta_r4c())
    start_res = evaluate(s, sp.theta, sp.cells, sp.wf)
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
    a0 = evaluate(s, sp.theta, sp.cells, sp.wf).objectives.area_m2
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
    # 이 test 는 solve_eps 전에 시작점을 평가하지 않아 시작점이 평가 캐시에 없다 -> 시작점 평가가 첫 '새 평가'라 deadline 이 지났으면
    # "start_wall_budget"(CONTRACT 3.13: 시작점이 캐시에 없을 때만 start_ 접두). 시작점이 캐시에 있으면 그 점을 받아들이고 첫 새 평가(FD 열)에서
    # "wall_budget". 시작 좌표 -> θ 는 원값 보존(interface card xrunf1a C2)이라 1 ulp 옆 점이 생기지 않는다(아래 test_start_theta_reused_no_extra_kernel).
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
    start_res = evaluate(s, sp.theta, sp.cells, sp.wf)
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
        assert h.key == eval_key(s.context_fp, s.schema_fp, h.theta, h.key.cells, fp_of(sp.wf), h.key.w_fixed_fp)     # [FS-1 §4.1] wf_fp = 그 점이 쓴 wf 의 지문(시작 wf 그대로 -- 이 풀이는 w_f 를 옮기지 않는다)
    assert r.best.key == eval_key(s.context_fp, s.schema_fp, r.best.theta, r.best.key.cells, fp_of(sp.wf), None)


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
    start_res = evaluate(s, sp.theta, sp.cells, sp.wf)
    (row0,) = [c for c in start_res.constraints if c.name == "spec:area_search_m2<="]
    assert row0.c > 1e5                                         # 입력 확인: 크기 1e6 급 행
    r = solve_eps(s, sp, axis, None, ("t",))
    assert r.best is not None and r.best.status in ACCEPTED_STATUSES and _feasible(r.best)
    key = "power_w" if axis == AXIS_POWER else "area_m2"
    assert getattr(r.best.objectives, key) <= getattr(start_res.objectives, key)
    assert evaluate(s, r.best.theta, r.best.key.cells, sp.wf) is r.best             # 캐시 적중 = 같은 평가 결과(값 불변)
    for h in (r.best,) + tuple(r.history):
        (row,) = [c for c in h.constraints if c.name == "spec:area_search_m2<="]
        assert row.c == pytest.approx((A_BIG - h.objectives.area_m2) / b_a, rel=1e-9)
    # best = 수락 반복 중 모든 원 c ≥ 0 이고 목적 최소(3.13) -- 원 c 로 다시 고른 것과 같다
    feas = [h for h in r.history if _feasible(h)]
    assert feas                                                     # 시작점이 예산 안 -> 적어도 시작점
    assert getattr(r.best.objectives, key) <= min(getattr(h.objectives, key) for h in feas)


# ---------------------------------------------------------------- [XRUN-F1 card A] 외층 시작 좌표 원값 보존 (interface card xrunf1a C2)
# 외층 행: 풀이·FD 에 들어가는 시작 좌표 = clip(x0ᵢ; loᵢ, hiᵢ), 좌표 -> θ = clip 뒤 ThetaCoords.to_theta. 결과: 시작 좌표가 상자 안인 성분은
# 시작 θ 원값(비트), 상자 밖 log 성분은 math.exp(clip 좌표)(원값 아님). 관찰 지점(J-3) = 모듈 속성 `slsqp_outer.fd_jacobian`(첫 호출 =
# 시작점 FD, x = 시작 좌표). base 실패 요구 없음(as-built 외층이 이미 원값 보존 -- card A-T7).
# oracle: (Py) 기대값 = 시작 θ 원값 또는 math.exp(min(max(math.log θ, lo), hi)) -- lo·hi 는 FD 호출에 넘어온 변수의 bounds(ln 좌표).
# θ 는 math.exp(math.log(θ)) != θ 인 성분이 있게 골랐고(회로 C 전류 1e-5, 회로 P 저항 9e4) 그 전제를 test 가 먼저 단언한다.

_SO = importlib.import_module("gmid_engine.search.slsqp_outer")


def _record_outer_fd(monkeypatch, store, coords_log=None):
    real = _SO.fd_jacobian

    def rec(sctx, variables, x, base, cells, to_theta, origin, skip=frozenset(), **kw):  # [XRUN-F1 card C] ceiling 키워드 통과
        store.append((tuple(variables), [float(v) for v in x], to_theta, coords_log[-1] if coords_log else None))
        return real(sctx, variables, x, base, cells, to_theta, origin, skip, **kw)
    monkeypatch.setattr(_SO, "fd_jacobian", rec)


def _hexes(d, comps):
    return {c: float(d[c]).hex() for c in comps}


def test_outer_start_inside_box_theta_bits_preserved(tmp_path, lut_sealed, monkeypatch):
    """A-T7 (상자 안): 첫 fd_jacobian 호출의 to_theta(x) 변수 성분 = 시작 θ 원값(비트)."""
    case = build_case(tmp_path, circuit_c(), lut_sealed, eval_budget=400)
    sp = _start(case, theta_r4c())
    th0 = dict(sp.theta)
    calls = []
    _record_outer_fd(monkeypatch, calls)
    solve_eps(case.sctx, sp, AXIS_POWER, None, ("t",))
    assert calls
    variables, x, to_theta, _ = calls[0]
    comps = [v.component for v in variables]
    # 전제: 모든 시작 좌표가 상자 안, 왕복이 원값을 잃는 log 성분이 있다(공허 방지)
    assert all(v.lo <= (math.log(th0[v.component]) if v.log else th0[v.component]) <= v.hi for v in variables)
    assert any(v.log and math.exp(math.log(th0[v.component])) != th0[v.component] for v in variables)
    assert _hexes(to_theta(x), comps) == _hexes(th0, comps)


def test_outer_start_outside_box_component_is_exp_of_clipped(tmp_path, lut_sealed, monkeypatch):
    """A-T7 (상자 밖): 회로 P, θ 저항 상자 (1e3, 3e4) Ω 에 시작 저항 9e4 Ω(상자 밖, 구성 입력). 첫 FD 의 to_theta(x) 저항 성분 =
    math.exp(min(max(math.log 9e4, lo), hi))(원값 아님), 상자 안 성분은 시작 θ 원값(비트)."""
    rv = 9e4
    case = build_case(tmp_path, circuit_p(), lut_sealed, elements=(("R1", "resistor", None),), rbounds=(1e3, 3e4), eval_budget=200)
    th0 = theta_p(case.dc, r=rv)
    sp = StartPoint("sx", tuple(sorted(th0.items())), CELLS_P, initial_wf(case.sctx.dc.base), "given")   # [FS-1 A-196] wf = 출발 블록 값(입력 구성)
    calls = []
    _record_outer_fd(monkeypatch, calls)
    solve_eps(case.sctx, sp, AXIS_POWER, None, ("t",))
    assert calls, "시작점이 받아들여지지 않았다(전제)"
    variables, x, to_theta, _ = calls[0]
    got = to_theta(x)
    (rvar,) = [v for v in variables if v.component == ("resistance", "R1")]
    assert rvar.log and not (rvar.lo <= math.log(rv) <= rvar.hi)                    # 전제: log 변수, 시작 좌표가 상자 밖
    want = math.exp(min(max(math.log(rv), rvar.lo), rvar.hi))                       # (Py)
    assert want != rv
    assert float(got[rvar.component]).hex() == float(want).hex()
    inside = [v.component for v in variables
              if v.component != rvar.component and v.lo <= (math.log(th0[v.component]) if v.log else th0[v.component]) <= v.hi]
    assert inside                                                                    # 비교할 상자 안 성분이 있다
    assert _hexes(got, inside) == _hexes(th0, inside)


def test_theta_coords_used_by_outer(tmp_path, lut_sealed, monkeypatch):
    """A-T8(외층 경로): ThetaCoords.start 를 클래스 수준에서 감싸(원래 것을 부름) solve_eps 가 한 번 이상 부르고, 첫 FD 에 넘긴 변환 출력
    (시작 좌표 x, 상자 안 -- 자르기 = 항등)이 그 직전에 만든 객체의 to_theta(x) 출력과 비트 같다. oracle (비교)."""
    from gmid_engine.search import ThetaCoords
    case = build_case(tmp_path, circuit_c(), lut_sealed, eval_budget=400)
    sp = _start(case, theta_r4c())
    made = []
    orig = ThetaCoords.start

    def start(cls, variables, theta):
        c = orig(variables, theta)
        made.append(c)
        return c
    monkeypatch.setattr(ThetaCoords, "start", classmethod(start))
    calls = []
    _record_outer_fd(monkeypatch, calls, made)
    solve_eps(case.sctx, sp, AXIS_POWER, None, ("t",))
    assert made and calls
    variables, x, to_theta, coords = calls[0]
    assert coords is not None
    assert all(v.lo <= xi <= v.hi for v, xi in zip(variables, x))
    a, b = to_theta(x), coords.to_theta(x)
    assert {k: float(v).hex() for k, v in a.items()} == {k: float(v).hex() for k, v in b.items()}


# =====================================================================================================================
# [XRUN-F1 card C] interface card xrunf1c C5 (C-T6) 외층 행 -- 첫 스텝 FdBudgetShortfall: 반복 0, 재시작 0, 정지 사유 eval_budget,
# aborts == ("eval_budget",), best = c ≥ 0이면 시작점 아니면 None. 반복 중 shortfall: 정지 사유 eval_budget. 호출 전후 kernel_calls <= 탐색 예산.
# oracle: (손) 구성 -- 선언 예산을 시작점 평가(캐시 적중) 뒤 kernel_calls + m 으로 맞춘다. 유한차분 한 묶음의 상계 = 2 n_θ (C4 정의).
#   m = 1 < 2 n_θ(n_θ ≥ 1): 첫 묶음이 못 시작 -> 첫 스텝 shortfall.
#   m = 2 n_θ + 1: 첫 묶음은 시작하고 곧 예산이 닿는다 -> 정지 사유 eval_budget (SLSQP 가 이 예산 안에서 수렴하지 않음은 구성 전제로 단언).
# =====================================================================================================================

def _cut_case(tmp_path, lut_sealed, m):
    case = build_case(tmp_path, circuit_c(), lut_sealed, eval_budget=400)
    s = case.sctx
    sp = _start(case, theta_r4c())
    start_res = evaluate(s, sp.theta, sp.cells, sp.wf)
    s.eval_budget = dict(s.counters)["kernel_calls"] + m
    return s, sp, start_res


def test_outer_first_step_shortfall_zero_iterations_best_is_start(tmp_path, lut_sealed):
    s, sp, start_res = _cut_case(tmp_path, lut_sealed, 1)
    assert 1 < 2 * len(s.domain.variables)                                  # 전제: 한 묶음 상계(2 n_θ)보다 작은 남은 한도
    r = solve_eps(s, sp, AXIS_POWER, None, ("t",))
    assert r.iterations == 0 and r.restarts == 0
    assert r.stop == "eval_budget"
    assert tuple(r.aborts) == ("eval_budget",)
    if _feasible(start_res):
        assert r.best is start_res                                          # c ≥ 0 이면 시작점
    else:
        assert r.best is None
    assert dict(s.counters)["kernel_calls"] <= s.eval_budget


def test_outer_mid_iteration_budget_stop_keeps_kernel_calls_within_budget(tmp_path, lut_sealed):
    s, sp, start_res = _cut_case(tmp_path, lut_sealed, 2 * 4 + 1)
    assert len(s.domain.variables) == 4                                     # 전제: 이 회로 n_θ = 4 -> m = 2 n_θ + 1
    r = solve_eps(s, sp, AXIS_POWER, None, ("t",))
    assert r.stop == "eval_budget"
    assert dict(s.counters)["kernel_calls"] <= s.eval_budget
    if r.best is not None:
        assert r.best.status in ACCEPTED_STATUSES and _feasible(r.best)
