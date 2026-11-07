"""CONTRACT 3.14 [r2] `polish_cells(sctx, solved, origin)` -- 설계 4.3 L-b + [FS-1 §5] w_f 칸 이웃 시험 (`polish_l_cells` 대체).

손 근거: toy 회로 C 에서 면적 = Σ W·L, W = I·L/IDu 라 같은 동작점이면 면적 ∝ L². M2 를 칸 1(L 2 µm)에서 칸 0(1 µm)으로
내리면 면적이 크게 준다 -> 면적 최소화 L-b 가 그 이동을 받아들여야 한다(개선 ≥ 1 정규화 칸 = b_A). 아래 이동의 새 L = 새 칸 hi.

[NFR-4 card 2] interface card nfr4c2 C5: 반환 = (tuple[SolveResult], 정지 사유), 사유 ∈ {converged, eval_budget, wall_budget}.
사유 = 반환 직전 예산 확인 한 번: kernel_calls >= eval_budget(예산이 있을 때) 이면 eval_budget, 아니고 deadline 이 있고 지났으면 wall_budget,
둘 다 아니면 converged -- 끝난 길과 무관. 옛 test 셋(24·42·50행)은 반환 2-tuple 로 고쳤다(3.2 표). 새 test N-T15~N-T18 의 기대 사유는 위 식을
test 가 관찰한 계수·시각에 적용한 값이다(oracle (식)). 피검 함수 출력으로 기대값을 만들지 않는다.

[FS-1 §5] 서명 맞춤: `polish_l_cells` -> `polish_cells`, 시작점 `StartPoint(start_id, theta, cells, wf, source)` (손 wf: conftest `hand_wf_of`).
N-1~N-4: oracle (식) interface card 20261107-fs1 §5 -- 한 바퀴 순서 = L 칸(MOS마다 −1, +1) 다음 w_f 칸(칸 순서, 칸마다 후보 목록에서 바로 아래, 바로 위; 목록 끝 쪽 건너뜀),
수락·정지 = 기존 L-b 하나. 후보 목록 = 합성 LUT 슬라이스 폭 (손 구성).
"""
import sys
import time

from gmid_engine.core import fp_of
from gmid_engine.search import ACCEPTED_STATUSES, AXIS_AREA, SolveResult, StartPoint, polish_cells, solve_eps

from .conftest import GRID, W_MIN, build_case, circuit_c, hand_wf_of, theta_r4c

LB_STOPS = ("converged", "eval_budget", "wall_budget")


def _start(s, theta, cells, keys=None):
    return StartPoint("t", tuple(sorted(theta.items())), cells, hand_wf_of(s, keys), "given")


def _solved(tmp_path, lut, axis, eval_budget=400, theta=None, cells=(0, 1), keys=None):
    case = build_case(tmp_path, circuit_c(), lut, eval_budget=eval_budget)
    s = case.sctx
    sr = solve_eps(s, _start(s, theta or theta_r4c(), cells, keys), axis, None, ("t",))
    assert sr.best is not None and tuple(sr.best.key.cells) == cells
    return case, s, sr


def _kc(s):
    return dict(s.counters)["kernel_calls"]


def test_area_moves_m2_down_one_cell(tmp_path, lut_sealed):
    case, s, sr = _solved(tmp_path, lut_sealed, AXIS_AREA)
    out, why = polish_cells(s, sr, ("L",))                                   # [NFR-4 card 2] C5 반환 2-tuple
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
    _out, _why = polish_cells(s, sr, ("L",))                                 # [NFR-4 card 2] C5 반환 2-tuple
    assert dict(s.counters)["kernel_calls"] - k0 <= len(s.domain.variables) + 1     # S-17


def test_stops_at_eval_budget(tmp_path, lut_sealed):
    case, s, sr = _solved(tmp_path, lut_sealed, AXIS_AREA)
    k0 = dict(s.counters)["kernel_calls"]
    s.eval_budget = k0
    _out, _why = polish_cells(s, sr, ("L",))                                 # [NFR-4 card 2] C5 반환 2-tuple
    assert dict(s.counters)["kernel_calls"] - k0 <= len(s.domain.variables) + 1     # S-17


# ---------------------------------------------------------------- [NFR-4 card 2] 정지 사유 (C5)

def test_lb_stop_converged(tmp_path, lut_sealed):
    """N-T15: E_B 넉넉(400), deadline 없음 -> 반환 2-tuple, 사유 converged. 전제: 반환 뒤 kernel_calls < E_B."""
    case, s, sr = _solved(tmp_path, lut_sealed, AXIS_AREA)
    s.deadline = None
    res = polish_cells(s, sr, ("L",))
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
        _out, why = polish_cells(s, sr, ("L",))
        assert _kc(s) >= s.eval_budget, (extra, _kc(s), s.eval_budget)       # 전제
        assert why == "eval_budget", extra


def test_lb_stop_both_budgets_prefers_eval_budget(tmp_path, lut_sealed):
    """N-T16: 두 예산이 함께 닿으면(E_B 도달 + 지난 deadline) eval_budget(우선순위: 평가 수가 먼저)."""
    case, s, sr = _solved(tmp_path, lut_sealed, AXIS_AREA)
    s.eval_budget = _kc(s)
    s.deadline = time.perf_counter() - 1.0
    _out, why = polish_cells(s, sr, ("L",))
    assert _kc(s) >= s.eval_budget and time.perf_counter() > s.deadline     # 전제: 둘 다 닿음
    assert why == "eval_budget"


def test_lb_stop_wall_budget(tmp_path, lut_sealed):
    """N-T17: deadline 을 지난 값, E_B 넉넉 -> wall_budget. 전제: 반환 뒤 kernel_calls < E_B."""
    case, s, sr = _solved(tmp_path, lut_sealed, AXIS_AREA)
    s.deadline = time.perf_counter() - 1.0
    _out, why = polish_cells(s, sr, ("L",))
    assert _kc(s) < s.eval_budget
    assert why == "wall_budget"


def test_lb_stop_checked_at_return_after_no_accept_round(tmp_path, lut_sealed):
    """N-T18 (L-b 쪽) 끝 확인: L-b 가 더 받아들일 이동이 없는 점(첫 L-b 의 최소 면적 결과)에서 다시 L-b 를 부른다.
    대조군: deadline 없음 -> converged(수락 없는 바퀴로 끝남). 본 단언: 같은 입력에 deadline = 지금 + 1 µs(반환 전에 반드시 지난다 -- 전제로 확인)
    -> 끝난 길(바퀴 안 확인 또는 수락 없는 바퀴 뒤 끝 확인)과 무관하게 wall_budget."""
    case, s, sr = _solved(tmp_path, lut_sealed, AXIS_AREA)
    s.deadline = None
    out, why = polish_cells(s, sr, ("L",))
    assert why == "converged"
    done = min((r for r in out if r.best is not None), key=lambda r: r.best.objectives.area_m2)
    again, why2 = polish_cells(s, done, ("L",))                            # 대조군: 이미 다듬어진 점
    assert why2 == "converged"
    b_a = GRID * W_MIN
    gains = [(done.best.objectives.area_m2 - r.best.objectives.area_m2) / b_a for r in again if r.best is not None]
    assert all(g < 1.0 for g in gains), gains                              # 전제: 수락할 개선(≥ 1 정규화 칸)이 없다
    s.deadline = time.perf_counter() + 1e-6
    _out3, why3 = polish_cells(s, done, ("L",))
    assert time.perf_counter() > s.deadline and _kc(s) < s.eval_budget     # 전제: 반환 전 마감이 지났고 E_B 는 남았다
    assert why3 == "wall_budget"


# =====================================================================================================================
# [XRUN-F1 card C] interface card xrunf1c C6 (C-T8) -- polish_cells 의 정지는 탐색 예산 기준.
# oracle: (손) 구성 -- 유도 실행(전이 뒤) 상태를 만든다: sctx.eval_budget = D, eval_budget_source = "derived_once:…" 이면 탐색 예산 = D − R,
# R = 2 n_θ (정의 1절). D = kernel_calls + R 로 정하면 탐색 예산 = kernel_calls -> 들어올 때 이미 도달: 평가 0, 사유 eval_budget.
# 대조: 같은 D 를 선언 실행(source "declared")으로 읽으면 탐색 예산 = D = kernel_calls + R 이라 도달하지 않는다 -- 그래서 사유가 갈린다.
# =====================================================================================================================

def _derived_state(s, search_budget):
    r = 2 * len(s.domain.variables)
    s.eval_budget = search_budget + r
    s.eval_budget_source = "derived_once:floor(B/median_t_eval)@n_evals=%d" % (len(s.domain.variables) + 1)
    return r


def test_lb_stop_derived_budget_is_d_minus_reserve_no_evaluation(tmp_path, lut_sealed):
    case, s, sr = _solved(tmp_path, lut_sealed, AXIS_AREA)
    s.deadline = None
    k0 = _kc(s)
    _derived_state(s, k0)                                                   # 탐색 예산 = 지금 kernel_calls
    _out, why = polish_cells(s, sr, ("L",))
    assert why == "eval_budget"
    assert _kc(s) == k0                                                     # 도달 -> 평가 안 함


def test_lb_stop_declared_same_d_does_not_stop_at_d_minus_reserve(tmp_path, lut_sealed):
    case, s, sr = _solved(tmp_path, lut_sealed, AXIS_AREA)
    s.deadline = None
    k0 = _kc(s)
    s.eval_budget = k0 + 2 * len(s.domain.variables)                        # 선언 실행: 탐색 예산 = E_B = k0 + R (> k0)
    assert s.eval_budget_source == "declared"
    _out, why = polish_cells(s, sr, ("L",))
    assert _kc(s) > k0                                                      # 평가가 돌았다
    assert why in ("converged", "eval_budget")


# =====================================================================================================================
# [FS-1 §5 N-1~N-4] w_f 칸 이웃 시험. 합성 LUT 슬라이스 폭 3개 (1e-6, 2e-6, 3e-6 -> 키 100·200·300).
# 시작점 = 면적 최소 L 칸 (0, 0) 에 키 (200, 200): L 이동은 −1 없음·+1 은 면적 증가라 수락 0 -> 첫 바퀴가 곧 전부. 면적은 슬라이스 IDu 비(idu_factor)에만 갈린다.
# =====================================================================================================================
def _wf_spy(monkeypatch):
    """관찰 지점 `l_bin_search.evaluate`(§9 통과 spy -- 동작 대체 0): 호출마다 wf.keys 를 기록한다."""
    mod = sys.modules["gmid_engine.search.l_bin_search"]
    orig, calls = mod.evaluate, []

    def spy(sctx, theta, cells, wf, *a, **k):
        calls.append(tuple(wf.keys))
        return orig(sctx, theta, cells, wf, *a, **k)
    monkeypatch.setattr(mod, "evaluate", spy)
    return calls


def _three_slice(tmp_path, idu_factor=None):
    from sizing.wb1_toy import write_r4_bins_lut
    lut, _, _ = write_r4_bins_lut(tmp_path / "lut3", widths=(1e-6, 2e-6, 3e-6), idu_factor=idu_factor, jc1_cols=True)      # CDD 열 있는 toy (단계 B 요구, A-190 M-2c)
    return lut


def _lowest_l_start(tmp_path, lut, keys):
    theta = theta_r4c(l1=1e-6, l2=1e-6)
    return _solved(tmp_path, lut, AXIS_AREA, theta=theta, cells=(0, 0), keys=keys)


def test_n1_trial_order_l_moves_then_wf_moves(tmp_path, monkeypatch):
    """N-1: 첫 바퀴 시험 순서 = L 이동 전부 -> w_f 이동(칸 순서, 아래 -> 위). 키 (200, 200) 에서 w_f 이동 손 순서:
    칸 0 아래 (100, 200), 칸 0 위 (300, 200), 칸 1 아래 (200, 100), 칸 1 위 (200, 300)."""
    lut = _three_slice(tmp_path)
    case, s, sr = _lowest_l_start(tmp_path, lut, {"M1": 200, "M2": 200})
    base_keys = (200, 200)
    assert tuple(hand_wf_of(s, {"M1": 200, "M2": 200}).keys) == base_keys              # 전제: 칸 순서 = (M1, M2)
    calls = _wf_spy(monkeypatch)
    out, why = polish_cells(s, sr, ("L",))
    assert why in LB_STOPS and len(calls) >= 1
    seq = list(calls)
    first_wf = next(i for i, k in enumerate(seq) if k != base_keys)
    assert all(k == base_keys for k in seq[:first_wf]) and first_wf >= 1               # L 이동 시험이 먼저 (>= 1)
    assert seq[first_wf:first_wf + 4] == [(100, 200), (300, 200), (200, 100), (200, 300)]
    # 전제 (판정 minor 8): 첫 바퀴에서 L 이동은 하나도 수락되지 않았다 (최소 L 칸에서 +1 은 면적 증가) -- 수락되면 바퀴 순서 단언이 흔들린다
    assert all(tuple(r.best.key.cells) == (0, 0) for r in out if r.best is not None)


def test_n2_improving_wf_move_is_accepted(tmp_path):
    """N-2: 슬라이스 200 의 IDu 가 2 배(idu_factor)라 W 가 절반 -> 키 100 -> 200 이동이 면적을 줄인다 (전제: 같은 θ 두 키의 면적 차를 먼저 잰다).
    수락 1 이상, 수락 결과 best.key.wf_fp = 이동한 keys 의 지문."""
    # [FS-1 A-196 판정 #8-5 -- 미해결, 오케스트레이터 보고] 판정 방향(종속 소자 회로 + idu_factor)을 R-2 회로로 측정했다(search/N2 측정 2026-11-08, 격리 복제본):
    # 모든 칸 키 100 대 거울 칸 (M3,M4) 키 200 면적 5.8394e-12 / 5.8445e-12 (차 −5.1e-15 < 분해능 한 칸 5e-15 의 ±1배), 차동쌍 칸 키 200 은 5.8372e-12.
    # 원인(손): 거울 칸의 쓰기 소자 M3 는 W = I·L/exp(θ ln IDu) 로 슬라이스 무관이고, 같은 칸 종속 M4 는 같은 VGS 에서 같은 슬라이스를 읽어 IDu 배율이 약분된다
    # (W4/W3 = I4/I3). 정합 칸 안에서는 키가 면적을 바꾸지 못하므로(DEC-108 설계), 이 N-2 전제는 이 toy 계열로 만들 수 없다 -- 아래는 기존 본문 그대로(red).
    from gmid_engine.sizing import WfCell, WfInput
    from .conftest import evaluate
    lut = _three_slice(tmp_path, idu_factor={2e-6: 2.0})
    case, s, sr = _lowest_l_start(tmp_path, lut, {"M1": 100, "M2": 100})
    theta = tuple(sorted(theta_r4c(l1=1e-6, l2=1e-6).items()))
    lo = evaluate(s, theta, (0, 0), wf=hand_wf_of(s, {"M1": 100, "M2": 100}))
    hi = evaluate(s, theta, (0, 0), wf=hand_wf_of(s, {"M1": 200, "M2": 100}))
    assert (lo.objectives.area_m2 - hi.objectives.area_m2) / (GRID * W_MIN) >= 1.0       # 전제: 분해능 한 칸 이상 개선
    out, why = polish_cells(s, sr, ("L",))
    base = hand_wf_of(s, {"M1": 100, "M2": 100})
    moved = {fp_of(WfInput(base.cells_ref, ks)) for ks in ((200, 100), (100, 200), (200, 200))}
    acc = [r for r in out if r.best is not None and r.best.key.wf_fp in moved]
    assert acc and all(r.best.objectives.area_m2 < sr.best.objectives.area_m2 for r in acc)


def test_n3_single_candidate_kind_has_no_wf_trials(tmp_path, lut_sealed, monkeypatch):
    """N-3: 후보 하나뿐인 LUT(widths 1개) -> w_f 시험 평가 0, 수락 0, 정지 converged."""
    case, s, sr = _lowest_l_start(tmp_path, lut_sealed, None)
    base = tuple(hand_wf_of(s).keys)
    calls = _wf_spy(monkeypatch)
    out, why = polish_cells(s, sr, ("L",))
    assert len(calls) >= 1                                                               # 양성 대조: L 이동 시험은 돌았다
    assert all(k == base for k in calls)                                                 # w_f 이동 시험 0
    assert why == "converged"


def test_n4_deterministic_two_runs(tmp_path):
    lut = _three_slice(tmp_path, idu_factor={2e-6: 2.0})
    runs = []
    for i in range(2):
        case, s, sr = _lowest_l_start(tmp_path / ("r%d" % i), lut, {"M1": 100, "M2": 100})
        out, why = polish_cells(s, sr, ("L",))
        runs.append((why, tuple((r.best.key.cells, r.best.key.wf_fp) for r in out if r.best is not None)))
    assert runs[0] == runs[1] and runs[0][0] in LB_STOPS
