"""CONTRACT 3.14 [r2] `polish_l_cells(sctx, solved, origin)` -- 설계 4.3 L-b.

손 근거: toy 회로 C 에서 면적 = Σ W·L, W = I·L/IDu 라 같은 동작점이면 면적 ∝ L². M2 를 칸 1(L 2 µm)에서 칸 0(1 µm)으로
내리면 면적이 크게 준다 -> 면적 최소화 L-b 가 그 이동을 받아들여야 한다(개선 ≥ 1 정규화 칸 = b_A). 아래 이동의 새 L = 새 칸 hi.
"""
import time

from gmid_engine.search import ACCEPTED_STATUSES, AXIS_AREA, SolveResult, polish_l_cells, solve_eps, start_points

from .conftest import GRID, W_MIN, build_case, circuit_c, theta_r4c


def _solved(tmp_path, lut, axis, eval_budget=400):
    case = build_case(tmp_path, circuit_c(), lut, eval_budget=eval_budget)
    s = case.sctx
    st, _ = start_points(s, [theta_r4c()])
    sr = solve_eps(s, st[0], axis, None, ("t",))
    assert sr.best is not None and tuple(sr.best.key.cells) == (0, 1)
    return case, s, sr


def test_area_moves_m2_down_one_cell(tmp_path, lut_sealed):
    case, s, sr = _solved(tmp_path, lut_sealed, AXIS_AREA)
    out = polish_l_cells(s, sr, ("L",))
    assert isinstance(out, tuple) and all(isinstance(r, SolveResult) for r in out)
    moved = [r for r in out if r.best is not None and tuple(r.best.key.cells) == (0, 0)]
    assert moved, [(r.stop, None if r.best is None else r.best.key.cells) for r in out]
    best = min(moved, key=lambda r: r.best.objectives.area_m2)
    assert dict(best.best.theta)[("L", "M2")] == 1e-6                  # 아래로 -> 새 칸 hi
    b_a = GRID * W_MIN
    assert (sr.best.objectives.area_m2 - best.best.objectives.area_m2) / b_a >= 1.0
    for r in out:
        if r.best is not None:
            assert r.best.status in ACCEPTED_STATUSES
            assert all(c.c >= 0 for c in r.best.constraints)


def test_stops_at_wall_budget(tmp_path, lut_sealed):
    case, s, sr = _solved(tmp_path, lut_sealed, AXIS_AREA)
    k0 = dict(s.counters)["kernel_calls"]
    s.deadline = time.perf_counter() - 1.0
    polish_l_cells(s, sr, ("L",))
    assert dict(s.counters)["kernel_calls"] - k0 <= len(s.domain.variables) + 1     # S-17


def test_stops_at_eval_budget(tmp_path, lut_sealed):
    case, s, sr = _solved(tmp_path, lut_sealed, AXIS_AREA)
    k0 = dict(s.counters)["kernel_calls"]
    s.eval_budget = k0
    polish_l_cells(s, sr, ("L",))
    assert dict(s.counters)["kernel_calls"] - k0 <= len(s.domain.variables) + 1     # S-17
