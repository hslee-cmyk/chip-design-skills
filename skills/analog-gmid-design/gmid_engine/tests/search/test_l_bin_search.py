"""CONTRACT 3.14 [r2] `polish_l_cells(sctx, solved, origin)` -- 설계 4.3 L-b.

손 근거: toy 회로 C 에서 면적 = Σ W·L, W = I·L/IDu 라 같은 동작점이면 면적 ∝ L². M2 를 칸 1(L 2 µm)에서 칸 0(1 µm)으로
내리면 면적이 크게 준다 -> 면적 최소화 L-b 가 그 이동을 받아들여야 한다(개선 ≥ 1 정규화 칸 = b_A). 아래 이동의 새 L = 새 칸 hi.

[NFR-4 card 2] interface card nfr4c2 C5: 반환 = (tuple[SolveResult], 정지 사유), 사유 ∈ {converged, eval_budget, wall_budget}.
사유 = 반환 직전 예산 확인 한 번: kernel_calls >= eval_budget(예산이 있을 때) 이면 eval_budget, 아니고 deadline 이 있고 지났으면 wall_budget,
둘 다 아니면 converged -- 끝난 길과 무관. 옛 test 셋(24·42·50행)은 반환 2-tuple 로 고쳤다(3.2 표). 새 test N-T15~N-T18 의 기대 사유는 위 식을
test 가 관찰한 계수·시각에 적용한 값이다(oracle (식)). 피검 함수 출력으로 기대값을 만들지 않는다.
"""
import time

from gmid_engine.search import ACCEPTED_STATUSES, AXIS_AREA, SolveResult, polish_l_cells, solve_eps, start_points

from .conftest import GRID, W_MIN, build_case, circuit_c, theta_r4c

LB_STOPS = ("converged", "eval_budget", "wall_budget")


def _solved(tmp_path, lut, axis, eval_budget=400):
    case = build_case(tmp_path, circuit_c(), lut, eval_budget=eval_budget)
    s = case.sctx
    st, _ = start_points(s, [theta_r4c()])
    sr = solve_eps(s, st[0], axis, None, ("t",))
    assert sr.best is not None and tuple(sr.best.key.cells) == (0, 1)
    return case, s, sr


def _kc(s):
    return dict(s.counters)["kernel_calls"]


def test_area_moves_m2_down_one_cell(tmp_path, lut_sealed):
    case, s, sr = _solved(tmp_path, lut_sealed, AXIS_AREA)
    out, why = polish_l_cells(s, sr, ("L",))                                 # [NFR-4 card 2] C5 반환 2-tuple
    assert why in LB_STOPS
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
    _out, _why = polish_l_cells(s, sr, ("L",))                               # [NFR-4 card 2] C5 반환 2-tuple
    assert dict(s.counters)["kernel_calls"] - k0 <= len(s.domain.variables) + 1     # S-17


def test_stops_at_eval_budget(tmp_path, lut_sealed):
    case, s, sr = _solved(tmp_path, lut_sealed, AXIS_AREA)
    k0 = dict(s.counters)["kernel_calls"]
    s.eval_budget = k0
    _out, _why = polish_l_cells(s, sr, ("L",))                               # [NFR-4 card 2] C5 반환 2-tuple
    assert dict(s.counters)["kernel_calls"] - k0 <= len(s.domain.variables) + 1     # S-17


# ---------------------------------------------------------------- [NFR-4 card 2] 정지 사유 (C5)

def test_lb_stop_converged(tmp_path, lut_sealed):
    """N-T15: E_B 넉넉(400), deadline 없음 -> 반환 2-tuple, 사유 converged. 전제: 반환 뒤 kernel_calls < E_B."""
    case, s, sr = _solved(tmp_path, lut_sealed, AXIS_AREA)
    s.deadline = None
    res = polish_l_cells(s, sr, ("L",))
    assert isinstance(res, tuple) and len(res) == 2
    out, why = res
    assert isinstance(out, tuple) and all(isinstance(r, SolveResult) for r in out)
    assert _kc(s) < s.eval_budget                                           # 전제(식의 첫 조건이 거짓)
    assert why == "converged"


def test_lb_stop_eval_budget(tmp_path, lut_sealed):
    """N-T16: (1) 들어올 때 이미 E_B 도달(eval_budget = 현재 kernel_calls) (2) L-b 중 E_B 도달(eval_budget = 현재 + 1, 전제: 반환 뒤
    kernel_calls >= E_B) -> 둘 다 eval_budget. deadline 없음."""
    for extra in (0, 1):
        case, s, sr = _solved(tmp_path / ("e%d" % extra), lut_sealed, AXIS_AREA)
        s.deadline = None
        s.eval_budget = _kc(s) + extra
        _out, why = polish_l_cells(s, sr, ("L",))
        assert _kc(s) >= s.eval_budget, (extra, _kc(s), s.eval_budget)       # 전제
        assert why == "eval_budget", extra


def test_lb_stop_both_budgets_prefers_eval_budget(tmp_path, lut_sealed):
    """N-T16: 두 예산이 함께 닿으면(E_B 도달 + 지난 deadline) eval_budget(우선순위: 평가 수가 먼저)."""
    case, s, sr = _solved(tmp_path, lut_sealed, AXIS_AREA)
    s.eval_budget = _kc(s)
    s.deadline = time.perf_counter() - 1.0
    _out, why = polish_l_cells(s, sr, ("L",))
    assert _kc(s) >= s.eval_budget and time.perf_counter() > s.deadline     # 전제: 둘 다 닿음
    assert why == "eval_budget"


def test_lb_stop_wall_budget(tmp_path, lut_sealed):
    """N-T17: deadline 을 지난 값, E_B 넉넉 -> wall_budget. 전제: 반환 뒤 kernel_calls < E_B."""
    case, s, sr = _solved(tmp_path, lut_sealed, AXIS_AREA)
    s.deadline = time.perf_counter() - 1.0
    _out, why = polish_l_cells(s, sr, ("L",))
    assert _kc(s) < s.eval_budget
    assert why == "wall_budget"


def test_lb_stop_checked_at_return_after_no_accept_round(tmp_path, lut_sealed):
    """N-T18 (L-b 쪽) 끝 확인: L-b 가 더 받아들일 이동이 없는 점(첫 L-b 의 최소 면적 결과)에서 다시 L-b 를 부른다.
    대조군: deadline 없음 -> converged(수락 없는 바퀴로 끝남). 본 단언: 같은 입력에 deadline = 지금 + 1 µs(반환 전에 반드시 지난다 -- 전제로 확인)
    -> 끝난 길(바퀴 안 확인 또는 수락 없는 바퀴 뒤 끝 확인)과 무관하게 wall_budget."""
    case, s, sr = _solved(tmp_path, lut_sealed, AXIS_AREA)
    s.deadline = None
    out, why = polish_l_cells(s, sr, ("L",))
    assert why == "converged"
    done = min((r for r in out if r.best is not None), key=lambda r: r.best.objectives.area_m2)
    again, why2 = polish_l_cells(s, done, ("L",))                          # 대조군: 이미 다듬어진 점
    assert why2 == "converged"
    b_a = GRID * W_MIN
    gains = [(done.best.objectives.area_m2 - r.best.objectives.area_m2) / b_a for r in again if r.best is not None]
    assert all(g < 1.0 for g in gains), gains                              # 전제: 수락할 개선(≥ 1 정규화 칸)이 없다
    s.deadline = time.perf_counter() + 1e-6
    _out3, why3 = polish_l_cells(s, done, ("L",))
    assert time.perf_counter() > s.deadline and _kc(s) < s.eval_budget     # 전제: 반환 전 마감이 지났고 E_B 는 남았다
    assert why3 == "wall_budget"
