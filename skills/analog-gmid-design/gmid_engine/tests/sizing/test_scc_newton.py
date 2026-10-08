"""[r6] 다변수 SCC 감쇠 Newton -- `newton_solve`(CONTRACT 5.5b) 단위 test 와 `size_and_seal` 경유 통합 test(5.4 [r6], 8절, 10.4).

기준은 `gmid_engine/sizing/CONTRACT.md` r6 만 쓴다(`scc_newton.py`·`block_columns.py` 소스는 열람하지 않았다).
- 단위 test: 손으로 만든 잔차 함수(선형·비선형·특이·정의역 밖·선 탐색 실패·반복 상한)를 `newton_solve` 에 넣고, 기대값은 이 파일의
  독립 재구현(`ref_newton`, 5.5b 문장 그대로)과 손계산으로 만든다.
- 통합 test: conftest toy LUT(닫힌 식 `Oracle`) 위 손 회로 두 개.
  S (공통게이트 모양, W4–W4 선형 SCC): vin = y1·vout, vout = vin + y2·(1.8 − vin) -> 닫힌 해, Gauss-Seidel 수축비 = y1·(1 − y2).
  Q (diode 위 W4, q ≥ 1): z = y·x (창 [gnd, x]), x = z + VGS1(vds = x − z, vsb = z) -- body 효과로 dx/dz = 1 + (gmb/gm)/(1 + gds/gm)
  > 1 이라 y 가 1 에 가까우면 루프 이득 ≥ 1 (Gauss-Seidel 이 수축하지 않는다). 해는 θ 를 해에서 거꾸로 만들어 안다.
- 야코비안 열 공식(5.4 [r6] ∂VGS/∂VDS = −1/(gm/gds), ∂VGS/∂VSB = gmb/gm, 열 조립)은 이 파일의 독립 writer 함수(Oracle 닫힌 식)의
  중앙 차분과 대조한다. 허용오차는 toy 식에서 유도한다(아래 `_gds_interp_rel`).
"""
import bisect
import math

import numpy as np
import pytest
import scipy.linalg

from gmid_engine.core import NonconvergentError, SealViolationError
from gmid_engine.lut import gmb, op_point
from gmid_engine.sizing import (DC_KEY, REASON_NEWTON_CAP, REASON_NEWTON_LINE_SEARCH, REASON_NEWTON_SINGULAR,
                                REASON_NEWTON_START, REPORT_UNDEFINED, SCC_BISECTION, SCC_DIRECT, SCC_GAUSS_SEIDEL,
                                SCC_NEWTON, SccLog, newton_solve, size_and_seal)

from .conftest import (B, C, I0, LAM, TOY_VGS, TOY_VS, W_KEY, W_M, Oracle, build_ctx, detail, free_currents, mos,
                       new_access, node_voltages, r4_arrays, r4_ln_idu, r4_vds_floor, r4_vgs_of, topo, two, write_r4_lut)


def kmax_ref(width, tol):
    """5.6 독립 계산."""
    return 1 if width <= tol else math.ceil(math.log2(width / tol))


# ===========================================================================
# 1. newton_solve 단위 test (5.5b)
# ===========================================================================

def ref_newton(nodes, values, evaluate, tolerance, width):
    """5.5b 문장의 독립 재구현. -> ("ok", values, (k, norms, tol, K)) 또는 ("fail", reason, (k, norms, tol, K))."""
    cur = dict(values)
    first = evaluate(cur)
    if first is None:
        return "fail", REASON_NEWTON_START, (0, (), None, None)
    r, J = first
    norms = []
    k = 0
    while True:
        rinf = max(abs(v) for v in r)
        norms.append(rinf)
        tol = tolerance(cur)
        K = kmax_ref(width, tol)
        # [r7] 영 피벗 검사·걸음 풀이가 수렴 판정보다 먼저, 수렴 = ‖r‖∞ ≤ tol 이고 ‖Δ‖∞ ≤ tol(걸음은 적용하지 않음)
        lu, piv = scipy.linalg.lu_factor(np.array(J, dtype=float))
        if np.any(np.diag(lu) == 0.0):
            return "fail", REASON_NEWTON_SINGULAR, (k, tuple(norms), tol, K)
        d = scipy.linalg.lu_solve((lu, piv), -np.array(r, dtype=float))
        dinf = float(np.max(np.abs(d)))
        if rinf <= tol and dinf <= tol:
            return "ok", cur, (k, tuple(norms), tol, K)
        if k >= K:
            return "fail", REASON_NEWTON_CAP, (k, tuple(norms), tol, K)
        r2 = math.sqrt(sum(v * v for v in r))
        alpha = 1.0
        while True:
            trial = dict(cur)
            for i, n in enumerate(nodes):
                trial[n] = cur[n] + alpha * float(d[i])
            if all(trial[n] == cur[n] for n in nodes):
                return "fail", REASON_NEWTON_LINE_SEARCH, (k, tuple(norms), tol, K)
            ev = evaluate(trial)
            if ev is not None and math.sqrt(sum(v * v for v in ev[0])) < r2:
                cur = trial
                r, J = ev
                break
            alpha /= 2.0
            if alpha * dinf < tol:
                return "fail", REASON_NEWTON_LINE_SEARCH, (k, tuple(norms), tol, K)
        k += 1


def _fail(nodes, values, evaluate, tolerance, width, devices=("M1", "M2")):
    with pytest.raises(NonconvergentError) as ei:
        newton_solve(nodes, values, evaluate, tolerance, width, devices=devices)
    return ei.value.record, dict(ei.value.record.detail)


def _const(t):
    return lambda c: t


def test_linear_system_exact_in_one_step():
    """r = V − (A·V + c), J = I − A 상수 -> 한 걸음에 해(부동소수 오차 안). values 의 SCC 밖 키는 그대로 읽히고 보존된다."""
    A = ((0.2, 0.5), (-0.3, 0.1))
    nodes = ("a", "b")

    def ev(v):
        c = (v["fix"], 2.0)
        x = (v["a"], v["b"])
        r = tuple(x[i] - (A[i][0] * x[0] + A[i][1] * x[1] + c[i]) for i in range(2))
        return r, tuple(tuple((1.0 if i == j else 0.0) - A[i][j] for j in range(2)) for i in range(2))
    start = {"a": 0.0, "b": 0.0, "fix": 0.7}
    out, (k, norms, tol, K) = newton_solve(nodes, start, ev, _const(1e-9), 2.0)
    assert start == {"a": 0.0, "b": 0.0, "fix": 0.7}                       # 입력 불변
    exact = np.linalg.solve(np.eye(2) - np.array(A), np.array([0.7, 2.0]))
    assert dict(out)["fix"] == 0.7
    assert abs(dict(out)["a"] - exact[0]) <= 1e-12 and abs(dict(out)["b"] - exact[1]) <= 1e-12
    assert k == 1 and len(norms) == 2
    assert norms[0] == max(0.7, 2.0) and norms[1] <= 1e-12
    assert tol == 1e-9 and K == kmax_ref(2.0, 1e-9)


def test_already_within_tolerance_zero_steps():
    def ev(v):
        return (v["x"] - 1.0,), ((1.0,),)
    out, (k, norms, tol, K) = newton_solve(("x",), {"x": 1.0 + 1e-4}, ev, _const(1e-3), 1.0)
    assert k == 0 and len(norms) == 1 and abs(norms[0] - 1e-4) <= 1e-15 and dict(out)["x"] == 1.0 + 1e-4


def test_nonlinear_known_root():
    """원 a² + b² = 5 와 직선 a − b + 1 = 0 의 근 (1, 2). 반복 기록은 독립 재구현과 같고, 해 오차 ≤ ‖J⁻¹‖∞·‖r‖∞(1차)."""
    nodes = ("a", "b")

    def ev(v):
        a, b = v["a"], v["b"]
        return (a * a + b * b - 5.0, a - b + 1.0), ((2 * a, 2 * b), (1.0, -1.0))
    start = {"a": 1.5, "b": 2.5}
    tolf = _const(1e-10)
    out, info = newton_solve(nodes, start, ev, tolf, 4.0)
    st, exp_v, exp_info = ref_newton(nodes, start, ev, tolf, 4.0)
    assert st == "ok"
    assert info[0] == exp_info[0] and info[2:] == exp_info[2:]
    assert len(info[1]) == len(exp_info[1])
    for a, b in zip(info[1], exp_info[1]):
        assert abs(a - b) <= 1e-12 * max(1.0, abs(b))
    kappa = np.max(np.sum(np.abs(np.linalg.inv(np.array([[2.0, 4.0], [1.0, -1.0]]))), axis=1))
    assert abs(dict(out)["a"] - 1.0) <= 2 * kappa * info[1][-1] + 1e-15
    assert abs(dict(out)["b"] - 2.0) <= 2 * kappa * info[1][-1] + 1e-15
    assert info[1][-1] <= 1e-10 and info[0] >= 2


def test_damped_step_backtracks():
    """r = atan(x), x0 = 2: 완전 걸음은 |r| 를 키운다(전제 확인) -> α 를 반으로 줄여 받아야 한다. 기록 = 독립 재구현."""
    def ev(v):
        x = v["x"]
        return (math.atan(x),), ((1.0 / (1.0 + x * x),),)
    x0 = 2.0
    full = x0 - math.atan(x0) * (1 + x0 * x0)
    assert abs(math.atan(full)) > abs(math.atan(x0))                      # 전제: α = 1 은 거부된다
    tolf = _const(1e-12)
    out, info = newton_solve(("x",), {"x": x0}, ev, tolf, 4.0)
    st, exp_v, exp_info = ref_newton(("x",), {"x": x0}, ev, tolf, 4.0)
    assert st == "ok" and info[0] == exp_info[0]
    for a, b in zip(info[1], exp_info[1]):
        assert abs(a - b) <= 1e-12 * max(1.0, abs(b))
    assert abs(dict(out)["x"]) <= 2e-12                                    # atan 근 0, |x| ≤ |r|·(1 + x²)


@pytest.mark.parametrize("case", ["rank_one_2x2", "zero_derivative_1d"])
def test_singular_jacobian(case):
    """LU 대각에 0 -> newton_singular(반복 0, norms = 시작 ‖r‖∞, margin = ‖r‖∞/tol)."""
    if case == "rank_one_2x2":
        nodes, start = ("a", "b"), {"a": 0.0, "b": 0.0}

        def ev(v):
            s = v["a"] + v["b"] - 2.0
            return (s, s), ((1.0, 1.0), (1.0, 1.0))
        r0 = 2.0
    else:
        nodes, start = ("x",), {"x": 0.0}

        def ev(v):
            return (v["x"] ** 2 + 1.0,), ((2 * v["x"],),)
        r0 = 1.0
    rec, d = _fail(nodes, start, ev, _const(1e-3), 1.0)
    assert d["reason"] == REASON_NEWTON_SINGULAR == "newton_singular"
    assert d["iterations"] == 0 and tuple(d["norms"]) == (r0,)
    assert tuple(d["nodes"]) == nodes and d["tol"] == 1e-3 and d["k_max"] == kmax_ref(1.0, 1e-3)
    assert rec.margin == pytest.approx(r0 / 1e-3, rel=1e-12)
    assert rec.devices == ("M1", "M2")


def test_start_outside_domain():
    calls = []

    def ev(v):
        calls.append(dict(v))
        return None
    rec, d = _fail(("x", "y"), {"x": 0.3, "y": 0.4}, ev, _const(1e-3), 1.0)
    assert d["reason"] == REASON_NEWTON_START == "newton_start_outside_domain"
    assert d["iterations"] == 0 and tuple(d["norms"]) == () and rec.margin is None
    assert calls and calls[0]["x"] == 0.3 and calls[0]["y"] == 0.4


def test_line_search_domain_failure():
    """정의역 x ≥ 0.999, r = x(근 0 은 정의역 밖), J = 1 -> Δ = −1. α = 1 … 1/64 시험점은 모두 밖, α = 1/128 은
    α·‖Δ‖∞ = 0.0078 < tol 0.01 -> newton_line_search(α = 1/128 시험점 0.992 도 밖이라 판정 순서와 무관)."""
    def ev(v):
        x = v["x"]
        return None if x < 0.999 else ((x,), ((1.0,),))
    rec, d = _fail(("x",), {"x": 1.0}, ev, _const(0.01), 2.0)
    assert d["reason"] == REASON_NEWTON_LINE_SEARCH == "newton_line_search"
    assert d["iterations"] == 0 and tuple(d["norms"]) == (1.0,)
    assert rec.margin == pytest.approx(1.0 / 0.01, rel=1e-12)
    st, reason, info = ref_newton(("x",), {"x": 1.0}, ev, _const(0.01), 2.0)
    assert (st, reason) == ("fail", REASON_NEWTON_LINE_SEARCH)


def test_line_search_stops_at_float_resolution():
    """틀린 부호 야코비안(r = x, J = −1 -> Δ = +1: 모든 α 가 ‖r‖ 를 키운다), tol = 1e-200. α·‖Δ‖∞ < tol 까지 가면 α 를 ~665 번
    줄여야 하지만, 시험점 1 + α 가 부동소수로 1 과 같아지는 α(≈ 2^-53)에서 멈춰야 한다 -> 평가 수 < 200."""
    calls = [0]

    def ev(v):
        calls[0] += 1
        return (v["x"],), ((-1.0,),)
    rec, d = _fail(("x",), {"x": 1.0}, ev, _const(1e-200), 1.0)
    assert d["reason"] == REASON_NEWTON_LINE_SEARCH and d["iterations"] == 0
    assert 50 <= calls[0] < 200
    assert rec.margin == pytest.approx(1.0 / 1e-200, rel=1e-12)


def test_iteration_cap():
    """r = x³(근 0 에서 J = 0 이라 1차 수렴, 걸음마다 x·2/3), tol 0.01, width 0.04 -> K_max = 2.
    norms: 1, (2/3)³, (4/9)³ = 0.0878 > tol, k = 2 ≥ K_max -> newton_iteration_cap."""
    def ev(v):
        x = v["x"]
        return (x ** 3,), ((3 * x * x,),)
    rec, d = _fail(("x",), {"x": 1.0}, ev, _const(0.01), 0.04)
    assert d["reason"] == REASON_NEWTON_CAP == "newton_iteration_cap"
    assert d["iterations"] == 2 and d["k_max"] == 2 and d["tol"] == 0.01
    exp = (1.0, (2 / 3) ** 3, (4 / 9) ** 3)
    assert len(d["norms"]) == 3 and all(abs(a - b) <= 1e-15 for a, b in zip(d["norms"], exp))
    assert rec.margin == pytest.approx(exp[-1] / 0.01, rel=1e-12)


def test_tolerance_and_kmax_reevaluated_each_iteration():
    """tol = tolerance(current) 를 반복마다 다시 잰다: 시작점 tol 1e-3 이면 안 끝나고, 해에서 tol 0.5 -> 반환 tol·K_max 는 마지막 값."""
    seen = []

    def tolf(c):
        seen.append(dict(c))
        return 1e-3 if c["x"] > 0.5 else 0.5

    def ev(v):
        return (v["x"] - 0.25,), ((1.0,),)
    out, (k, norms, tol, K) = newton_solve(("x",), {"x": 1.0}, ev, tolf, 2.0)
    assert k == 1 and norms == (0.75, 0.0) and tol == 0.5 and K == kmax_ref(2.0, 0.5)
    assert [s["x"] for s in seen] == [1.0, 0.25]


def test_r7_small_residual_large_step_not_accepted():
    """[r7] 잔차만 작고 걸음이 큰 점은 받지 않는다: r = ε·(x − 1), J = ε(ε = 1e-4), 시작 x = 0 -> ‖r‖∞ = 1e-4 ≤ tol 1e-3
    이지만 Δ = 1 > tol -> 한 걸음 더 걸어 x = 1(r = 0, Δ = 0)에서 받는다(r6 규칙이면 k = 0, x = 0 -- 오차 1)."""
    eps = 1e-4

    def ev(v):
        return (eps * (v["x"] - 1.0),), ((eps,),)
    out, (k, norms, tol, K) = newton_solve(("x",), {"x": 0.0}, ev, _const(1e-3), 2.0)
    assert k == 1 and norms[0] == pytest.approx(1e-4, rel=1e-12) and norms[0] <= tol
    assert abs(dict(out)["x"] - 1.0) <= 1e-12
    st, cur, info = ref_newton(("x",), {"x": 0.0}, ev, _const(1e-3), 2.0)
    assert st == "ok" and info[0] == 1


def test_r7_accepted_point_is_current_not_stepped():
    """[r7] 받을 때 걸음은 적용하지 않는다(현재 점 반환): r = x − 1, 시작 1 + 5e-4, tol 1e-3 -> k = 0, x 그대로."""
    def ev(v):
        return (v["x"] - 1.0,), ((1.0,),)
    out, (k, norms, tol, K) = newton_solve(("x",), {"x": 1.0005}, ev, _const(1e-3), 2.0)
    assert k == 0 and dict(out)["x"] == 1.0005


def test_r7_singular_checked_before_acceptance():
    """[r7] 영 피벗 검사는 수렴 판정 전: 시작점 잔차 0 이어도 J 가 특이면 newton_singular(걸음을 풀 수 없으면 오차를 못 잰다)."""
    def ev(v):
        return (0.0, 0.0), ((1.0, 1.0), (1.0, 1.0))
    rec, d = _fail(("a", "b"), {"a": 1.0, "b": 1.0}, ev, _const(1e-3), 1.0)
    assert d["reason"] == REASON_NEWTON_SINGULAR and d["iterations"] == 0 and tuple(d["norms"]) == (0.0,)


# ===========================================================================
# 2. 야코비안 열 공식 vs 독립 writer 함수의 중앙 차분 (5.4 [r6] writer_grad)
# ===========================================================================

def _vgs(kind, T, vds, vsb):
    """Oracle 좌표 역산(정의역 밖 -> None)."""
    r = T - math.log(I0[kind]) - LAM * vds - Oracle.vs_term(vsb)
    disc = B * B - 2.0 * C * r
    if r < 0.0 or disc < 0.0:
        return None
    v = (B - math.sqrt(disc)) / C
    return v if v <= TOY_VGS[-1] else None


def writer_value(kind, rel, T, V, pins):
    """독립 writer 식(5.4): gate 쓰기 V(g) = V(s) + s·VGS, source 쓰기 V(s) = V(g) − s·VGS. VGS = 좌표 역산(Oracle 닫힌 식)."""
    d, g, s, b = pins
    sg = 1.0 if kind == "nmos" else -1.0
    v = _vgs(kind, T, sg * (V[d] - V[s]), sg * (V[s] - V[b]))
    return V[s] + sg * v if rel == "gate" else V[g] - sg * v


def formula_column(memo, kind, rel, T, V, pins, L=1e-6):
    """CONTRACT 5.4 [r6] 의 열: ∂VGS/∂VDS = −1/(gm/gds)(op_point.gm_gds), ∂VGS/∂VSB = gmb/gm(lut gmb, gm = gm_over_id·IDu·w_m/L),
    ∂g/∂V(known) += 1, (d) += σ·∂VGS/∂VDS, (s) += σ·(∂VGS/∂VSB − ∂VGS/∂VDS), (b) += −σ·∂VGS/∂VSB(같은 노드는 더함).
    반환 ({노드: 값}, ∂VGS/∂VDS)."""
    d, g, s, b = pins
    sg = 1.0 if kind == "nmos" else -1.0
    vds, vsb = sg * (V[d] - V[s]), sg * (V[s] - V[b])
    v = _vgs(kind, T, vds, vsb)
    op = op_point(memo, kind, W_KEY, L, v, vds, vsb)
    dvds = -1.0 / op.gm_gds
    gm = op.gm_over_id * op.IDu * W_M / L
    dvsb = gmb(memo, kind, W_KEY, L, v, vds, vsb) / gm
    sigma = 1.0 if rel == "gate" else -1.0
    known = s if rel == "gate" else g
    col = {}
    for node, val in ((known, 1.0), (d, sigma * dvds), (s, sigma * (dvsb - dvds)), (b, -sigma * dvsb)):
        col[node] = col.get(node, 0.0) + val
    return col, dvds


def _gds_interp_rel():
    """op_point 의 gm_gds = gm/ID·exp(lnID − lnGDS) 에서 lnGDS 는 모든 축 선형(lut 4.x). toy 의 lnGDS = lnID + ln LAM 은 VGS 에
    2차(−C·VGS²/2)라 VGS 칸(간격 h) 선형 보간 오차 ≤ C·h²/8 -> gds 상대 오차 ≤ exp(C·h²/8) − 1. VDS(1차)·VS(구간 선형) 보간은 정확."""
    h = max(TOY_VGS[i + 1] - TOY_VGS[i] for i in range(len(TOY_VGS) - 1))
    return math.expm1(C * h * h / 8.0)


JAC_CASES = {
    # (kind, rel, pins (d, g, s, b), V, 목표 VGS) -- vsb 는 VS 격자점에서 1e-3 이상 떨어뜨림(구간 선형 VS 항의 꺾임 회피)
    "nmos_gate": ("nmos", "gate", ("nd", "x", "ns", "gnd"), {"nd": 1.3, "ns": 0.35, "gnd": 0.0}, 0.62),
    "nmos_source": ("nmos", "source", ("nd", "ng", "x", "gnd"), {"nd": 1.5, "ng": 1.1, "x": 0.37, "gnd": 0.0}, 0.66),
    "pmos_gate": ("pmos", "gate", ("nd", "x", "ns", "vdd"), {"nd": 0.5, "ns": 1.55, "vdd": 1.8}, 0.71),
    "pmos_source": ("pmos", "source", ("nd", "ng", "x", "vdd"), {"nd": 0.2, "ng": 0.6, "x": 1.3, "vdd": 1.8}, 0.64),
    "nmos_diode_self": ("nmos", "gate", ("x", "x", "ns", "gnd"), {"x": 0.95, "ns": 0.3, "gnd": 0.0}, 0.6),
    "nmos_bulk_in_scc": ("nmos", "gate", ("nd", "x", "ns", "nb"), {"nd": 1.4, "ns": 0.8, "nb": 0.1}, 0.58),
}


@pytest.mark.parametrize("name", sorted(JAC_CASES))
def test_mos_jacobian_columns_vs_central_difference(toy_access, name):
    kind, rel, pins, V0, vgs_t = JAC_CASES[name]
    V = dict(V0)
    d, g, s, b = pins
    x = g if rel == "gate" else s
    V.setdefault(x, 0.9)
    sg = 1.0 if kind == "nmos" else -1.0
    vds, vsb = sg * (V[d] - V[s]), sg * (V[s] - V[b])
    assert min(abs(vsb - p) for p in TOY_VS) >= 1e-3                      # 전제: VS 칸 안
    T = Oracle.ln_idu(kind, vgs_t, vds, vsb)
    col, dvds = formula_column(toy_access.memo, kind, rel, T, V, pins)
    h = 1e-6
    rel_gds = _gds_interp_rel()
    for node in sorted(set(pins) | {x}):
        Vp, Vm = dict(V), dict(V)
        Vp[node] += h
        Vm[node] -= h
        fd = (writer_value(kind, rel, T, Vp, pins) - writer_value(kind, rel, T, Vm, pins)) / (2 * h)
        # 허용오차: gds 보간 상대 오차 × (그 열의 ∂VGS/∂VDS 계수 1) + 중앙 차분 반올림 eps·max|g|/h(≈ 4e-10) 의 여유
        n_dvds = (node == d) + (node == s)
        tol = n_dvds * abs(dvds) * rel_gds * 1.01 + 1e-9
        assert abs(col.get(node, 0.0) - fd) <= tol, (name, node, col.get(node, 0.0), fd, tol)


@pytest.mark.parametrize("name", ["nmos_bulk_in_scc", "pmos_source"])
def test_jacobian_tolerance_discriminates(toy_access, name):
    """판별력: 위 허용오차가 공식의 부호 오류(∂VGS/∂VSB 또는 ∂VGS/∂VDS 부호 반전, σ 누락)를 놓치지 않는다 -- 틀린 열은 FD 와의
    차가 허용오차보다 크다(gmb/gm ~ 0.05–0.4, gds/gm ~ 0.005 ≫ 허용오차 ~ 5e-7)."""
    kind, rel, pins, V0, vgs_t = JAC_CASES[name]
    d, g, s, b = pins
    V = dict(V0)
    sg = 1.0 if kind == "nmos" else -1.0
    vds, vsb = sg * (V[d] - V[s]), sg * (V[s] - V[b])
    T = Oracle.ln_idu(kind, vgs_t, vds, vsb)
    col, dvds = formula_column(toy_access.memo, kind, rel, T, V, pins)
    sigma = 1.0 if rel == "gate" else -1.0
    dvsb = -col[b] / sigma
    h = 1e-6
    rel_gds = _gds_interp_rel()

    def fd(node):
        Vp, Vm = dict(V), dict(V)
        Vp[node] += h
        Vm[node] -= h
        return (writer_value(kind, rel, T, Vp, pins) - writer_value(kind, rel, T, Vm, pins)) / (2 * h)
    tol_d = abs(dvds) * rel_gds * 1.01 + 1e-9
    assert abs(col[d] - fd(d)) <= tol_d
    wrong = {"vsb_sign_flipped": (b, sigma * dvsb), "vds_sign_flipped": (d, -sigma * dvds),
             "sigma_dropped": (d, dvds if sigma < 0 else -dvds)}
    for label, (node, val) in wrong.items():
        tol = (abs(dvds) * rel_gds * 1.01 if node == d else 0.0) + 1e-9
        assert abs(val - fd(node)) > tol, label


# ===========================================================================
# 3. size_and_seal 통합 -- 손 회로 S·Q (toy LUT)
# ===========================================================================

def circuit_s(reverse=False):
    """S: M1 nmos (vin, nb1, gnd) 전류원, M2 nmos (vout, nb2, vin) 공통게이트, M3 pmos (vout, pb, vdd) 부하.
    vin = 입력 포트(입력 DC 미선언 -> W4 input_common_mode), vout = drain 만(W4). SCC {vin, vout} 은 창만으로 결합(선형)."""
    net = [mos("M1", "nmos", "vin", "nb1", "gnd"), mos("M2", "nmos", "vout", "nb2", "vin"),
           mos("M3", "pmos", "vout", "pb", "vdd")]
    return topo("scc_s", net[::-1] if reverse else net,
                {"vin": ("input", "single_ended_input"), "vout": ("output", "single_ended_output")},
                bias=["nb1", "nb2", "pb"])                                  # nb1: M1 gate, nb2: M2 gate, pb: M3 gate


def circuit_q(reverse=False):
    """Q: M1 nmos diode (x, x, z)(bulk 기본 gnd -> vsb = z), M3 nmos (z, nb, gnd), M2 pmos (x, pb, vdd).
    z = 입력 포트 -> F 없는 성분 {x, z} 의 뿌리(W4, 창 lo = gnd, hi = V(x)), x = M1 의 vgs_gate(1변수: d = x)."""
    net = [mos("M1", "nmos", "x", "x", "z"), mos("M3", "nmos", "z", "nb", "gnd"), mos("M2", "pmos", "x", "pb", "vdd")]
    return topo("scc_q", net[::-1] if reverse else net,
                {"z": ("input", "single_ended_input"), "x": ("output", "single_ended_output")},
                bias=["nb", "pb"])                                          # nb: M3 gate, pb: M2 gate


def theta_s(ctx, y1, y2):
    vout = 1.8 * y2 / (1.0 - y1 * (1.0 - y2))
    vin = y1 * vout
    th = {("L", "M1"): 1e-6, ("L", "M2"): 1e-6, ("L", "M3"): 1e-6,
          ("ln_idu", "M1"): Oracle.ln_idu("nmos", 0.6, vin, 0.0),
          ("ln_idu", "M2"): Oracle.ln_idu("nmos", 0.7, vout - vin, vin),
          ("ln_idu", "M3"): Oracle.ln_idu("pmos", 0.7, 1.8 - vout, 0.0),
          ("y", "input_common_mode"): y1, ("y", "vout"): y2}
    th.update(free_currents(ctx, {"M1": 1e-5, "M2": 1e-5, "M3": 1e-5}))
    assert set(th) == set(ctx.schema.components)
    return th, (vin, vout)


def theta_q(ctx, y, z_star):
    """해 (z*, x* = z* + c), c = z*(1 − y)/y 가 정확히 나오는 θ: M1 목표 = Oracle ln IDu(VGS = c, VDS = c, VSB = z*)."""
    c = z_star * (1.0 - y) / y
    T = Oracle.ln_idu("nmos", c, c, z_star)
    x_star = z_star + c
    th = {("L", "M1"): 1e-6, ("L", "M2"): 1e-6, ("L", "M3"): 1e-6, ("ln_idu", "M1"): T,
          ("ln_idu", "M3"): Oracle.ln_idu("nmos", 0.6, z_star, 0.0),
          ("ln_idu", "M2"): Oracle.ln_idu("pmos", 0.7, 1.8 - x_star, 0.0), ("y", "input_common_mode"): y}
    th.update(free_currents(ctx, {"M1": 1e-5, "M2": 1e-5, "M3": 1e-5}))
    assert set(th) == set(ctx.schema.components)
    assert abs(_vgs("nmos", T, c, z_star) - c) <= 1e-12                   # 전제: 그 해가 writer 식의 고정점
    return th, (z_star, x_star), T


@pytest.fixture(scope="module")
def ctx_s(tmp_path_factory, toy_access):
    ctx = build_ctx(tmp_path_factory.mktemp("scc_s"), circuit_s(), toy_access)[2]
    w = dict(ctx.base.column("node", "dc_writer"))
    assert (w["vin"].relation, w["vin"].y_key) == ("free_window", "input_common_mode")
    assert (w["vout"].relation, w["vout"].y_key) == ("free_window", "vout")
    cyc = [e for e in ctx.base.value("graph", DC_KEY, "dc_scc_order") if e.cyclic]
    assert [e.nodes for e in cyc] == [("vin", "vout")]
    return ctx


@pytest.fixture(scope="module")
def ctx_q(tmp_path_factory, toy_access):
    ctx = build_ctx(tmp_path_factory.mktemp("scc_q"), circuit_q(), toy_access)[2]
    w = dict(ctx.base.column("node", "dc_writer"))
    assert (w["z"].relation, w["z"].y_key) == ("free_window", "input_common_mode")
    assert (w["x"].relation, w["x"].element, w["x"].known) == ("vgs_gate", "M1", "z")
    cyc = [e for e in ctx.base.value("graph", DC_KEY, "dc_scc_order") if e.cyclic]
    assert [e.nodes for e in cyc] == [("z", "x")]
    return ctx


def column_start(ctx, node):
    """5.4 시작값 1단계: 기둥 위치 비례 V(r1) + (V(r2) − V(r1))·position/length (계획 필드 dc_column_nbrs 를 입력으로 읽음)."""
    rails = dict(ctx.base.column("node", "dc_rail_v"))
    (nb,) = ctx.base.value("node", node, "dc_column_nbrs")
    r1, r2 = nb.rails
    return rails[r1] + (rails[r2] - rails[r1]) * nb.position / nb.length


def toy_tol():
    """toy 의 tol_V 셀: 모든 셀에서 VS 축 LOO 최댓값(Oracle.tol_v) -- writer·소자·VDS 와 무관한 상수."""
    return Oracle.tol_v()


def gs_ref(update, order, start, tol, width):
    """5.5 Gauss-Seidel 독립 재구현(Δ 열·정지). update(node, cur) -> 새 값. -> (st, cur, deltas)."""
    cur = dict(start)
    K = kmax_ref(width, tol)
    deltas = []
    k = 0
    while True:
        k += 1
        dk = 0.0
        for n in order:
            new = update(n, cur)
            dk = max(dk, abs(new - cur[n]))
            cur[n] = new
        deltas.append(dk)
        if dk == 0.0:                                                     # [r7] 정확한 고정점
            return "ok", cur, deltas
        stop = k >= K
        if k >= 3 and deltas[-2] > 0:
            q = dk / deltas[-2]
            if q < 1:
                m = max(1.0, q / (1.0 - q)) * dk                            # [r7] 노드전압 오차 상계
                if m <= tol:
                    return "ok", cur, deltas
                stop = stop or q ** max(K - k, 0) * m > tol
        if stop:
            return "stop", cur, deltas


def scc_log(snap, nodes):
    logs = [e for e in snap.value("graph", DC_KEY, "dc_scc_log") if tuple(e.nodes) == tuple(nodes)]
    assert len(logs) == 1
    assert isinstance(logs[0], SccLog)
    return logs[0]


# ---- S: 선형 W4–W4 SCC ----------------------------------------------------

def s_update(y1, y2):
    def upd(n, c):
        if n == "vin":                       # 창 [gnd, min(vdd, vout)] (M1 d 나감 -> lo gnd, M2 s 들어옴 -> hi vout)
            return 0.0 + y1 * (min(1.8, c["vout"]) - 0.0)
        return max(0.0, c["vin"]) + y2 * (1.8 - max(0.0, c["vin"]))   # 창 [vin, vdd]
    return upd


@pytest.mark.parametrize("y1,y2", [(0.98, 0.3), (0.95, 0.2)])
def test_slow_contraction_switches_to_newton(ctx_s, y1, y2):
    """경우 1(느린 수축): 측정 q = y1·(1 − y2) < 1 이지만 q^(K_max − k)·Δ/(1 − q) > tol -> Gauss-Seidel 정지 -> Newton.
    선형 SCC 라 Newton 한 걸음에 닫힌 해. fallback = ("gauss_seidel_stopped", q, GS Δ 열)."""
    th, (vin, vout) = theta_s(ctx_s, y1, y2)
    tol = toy_tol()
    start = {"vin": column_start(ctx_s, "vin"), "vout": column_start(ctx_s, "vout")}
    st, _, deltas = gs_ref(s_update(y1, y2), ("vin", "vout"), start, tol, 1.8)
    assert st == "stop" and len(deltas) == 3                              # 전제: k = 3 에서 예측 정지(독립 재구현)
    ev = size_and_seal(ctx_s, th)
    assert ev.report.status == REPORT_UNDEFINED                            # 봉인 7 만 undefined(toy 는 VDSAT 열 없음), 위반 없음
    log = scc_log(ev.snapshot, ("vin", "vout"))
    assert log.method == SCC_NEWTON == "newton"
    cause, q, gs_deltas = log.fallback
    assert cause == "gauss_seidel_stopped"
    assert len(gs_deltas) == len(deltas)
    assert all(abs(a - b) <= 1e-12 for a, b in zip(gs_deltas, deltas))
    assert q == gs_deltas[-1] / gs_deltas[-2] and abs(q - y1 * (1 - y2)) <= 1e-9 and q < 1
    # Newton: 시작점 (a) = 2단계 값(W4 그대로 = 1단계), 한 걸음, deltas = 반복마다 ‖r‖∞
    r0 = max(abs(start["vin"] - y1 * start["vout"]), abs(start["vout"] - (start["vin"] + y2 * (1.8 - start["vin"]))))
    assert log.iterations == 1 and len(log.deltas) == 2
    assert abs(log.deltas[0] - r0) <= 1e-12 and log.deltas[1] <= 1e-12
    assert log.tol == pytest.approx(tol, rel=1e-12) and log.k_max == kmax_ref(1.8, log.tol)
    V = node_voltages(ev.snapshot)
    assert abs(V["vin"] - vin) <= 1e-12 and abs(V["vout"] - vout) <= 1e-12


@pytest.mark.parametrize("y1,y2", [(0.6, 0.4), (0.9, 0.2)])
def test_contracting_gauss_seidel_does_not_run_newton(ctx_s, y1, y2):
    """Gauss-Seidel 이 수렴하고 strict 검증을 통과하면 Newton 은 돌지 않는다: method gauss_seidel, fallback None, 값·Δ 열 = GS
    (Newton 으로 다듬지 않는다). q = y1·(1 − y2) = 0.36(< 1/2, m = Δk)·0.72(≥ 1/2, m = q/(1−q)·Δk) -- [r7] 판정은 독립 재구현
    gs_ref 와 같은 바퀴에서 받고, 받은 점의 노드전압이 닫힌 해와 tol 안이다(오차 상계가 실제로 지켜짐)."""
    th, (vin, vout) = theta_s(ctx_s, y1, y2)
    tol = toy_tol()
    start = {"vin": column_start(ctx_s, "vin"), "vout": column_start(ctx_s, "vout")}
    st, cur, deltas = gs_ref(s_update(y1, y2), ("vin", "vout"), start, tol, 1.8)
    assert st == "ok" and len(deltas) >= 3
    q = deltas[-1] / deltas[-2]
    assert (q >= 0.5) == (y1 * (1 - y2) >= 0.5)
    if q >= 0.5:                                                           # 판별력: Δ ≤ tol 만 보는 r6 규칙이면 더 일찍 받았을 것
        assert any(d <= tol for d in deltas[:-1])
    ev = size_and_seal(ctx_s, th)
    log = scc_log(ev.snapshot, ("vin", "vout"))
    assert log.method == SCC_GAUSS_SEIDEL == "gauss_seidel" and log.fallback is None
    assert log.iterations == len(deltas) and all(abs(a - b) <= 1e-12 for a, b in zip(log.deltas, deltas))
    V = node_voltages(ev.snapshot)
    assert abs(V["vin"] - cur["vin"]) <= 1e-12 and abs(V["vout"] - cur["vout"]) <= 1e-12
    assert abs(V["vin"] - vin) > 1e-9                                     # 판별력: Newton 이 돌았다면 닫힌 해(1e-12)였을 것
    assert max(abs(V["vin"] - vin), abs(V["vout"] - vout)) <= tol          # [r7] 노드전압 오차 ≤ tol


def test_methods_direct_and_bisection(tmp_path, toy_access):
    """SccLog.method: 비순환 = direct, 크기 1 순환(1변수 diode 노드) = bisection, fallback None."""
    net = [mos("M1", "nmos", "nb", "nb", "gnd"), mos("M2", "nmos", "out", "nb", "gnd"), mos("M3", "pmos", "out", "in", "vdd")]
    doc = topo("scc_diode", net, {"in": ("input", "x"), "out": ("output", "y")},
               sources=[two("I1", "current_source", "vdd", "nb")])
    ctx = build_ctx(tmp_path, doc, toy_access, element_values=(("I1", 1e-5),))[2]
    th = {("L", "M1"): 1e-6, ("L", "M2"): 1e-6, ("L", "M3"): 1e-6, ("ln_idu", "M1"): Oracle.ln_idu("nmos", 0.6, 0.6, 0.0),
          ("ln_idu", "M3"): Oracle.ln_idu("pmos", 0.7, 1.35, 0.0), ("y", "out"): 0.25}
    th.update(free_currents(ctx, {"M1": 1e-5, "M2": 1e-5, "M3": 1e-5, "I1": 1e-5}))
    assert set(th) == set(ctx.schema.components)
    snap = size_and_seal(ctx, th).snapshot
    order = ctx.base.value("graph", DC_KEY, "dc_scc_order")
    logs = {tuple(e.nodes): e for e in snap.value("graph", DC_KEY, "dc_scc_log")}
    assert set(logs) == {tuple(e.nodes) for e in order}
    for e in order:
        lg = logs[tuple(e.nodes)]
        assert lg.fallback is None
        if not e.cyclic:
            assert lg.method == SCC_DIRECT == "direct"
        else:
            assert len(e.nodes) == 1 and lg.method == SCC_BISECTION == "bisection"
    assert logs[("nb",)].method == SCC_BISECTION


# ---- Q: Gauss-Seidel 이 수축하지 않는 SCC (q ≥ 1) --------------------------

def vs_slope(vsb):
    """lut gmb(GMBS 열 없음) 의 VS 칸 k = min(bisect_right(VS, vsb) − 1, len − 2) 위 toy VS 항 기울기."""
    k = min(bisect.bisect_right(TOY_VS, vsb) - 1, len(TOY_VS) - 2)
    return (Oracle.vs_term(TOY_VS[k + 1]) - Oracle.vs_term(TOY_VS[k])) / (TOY_VS[k + 1] - TOY_VS[k])


def q_residual(T, y, z, x):
    """Q 의 SCC 잔차 r = V − g(V)(1변수 x 도 식 그대로)와 J = I − ∂g/∂V(5.4 [r6] 열 공식, Oracle 미분). 정의역 밖 -> None."""
    v = _vgs("nmos", T, x - z, z)
    if v is None or x - z < 0.0:
        return None
    gz = 0.0 + y * (min(1.8, x) - 0.0)
    dgz_dx = y if x < 1.8 else 0.0             # hi 를 x 가 엄격히 낮출 때만 이웃 열(레일 끝이면 없음)
    gx = z + v
    gmid = B - C * v
    dvds = -LAM / gmid                         # −1/(gm/gds), toy gds/ID = LAM
    dvsb = -vs_slope(z) / gmid                 # gmb/gm
    # x = M1 gate 쓰기(σ = +1), known = s = z, d = x, b = gnd(레일)
    dgx_dz = 1.0 + (dvsb - dvds)
    dgx_dx = dvds
    r = np.array([z - gz, x - gx])
    J = np.array([[1.0, -dgz_dx], [-dgx_dz, 1.0 - dgx_dx]])
    return r, J, v


def x_root(T, z):
    """1변수 x: h(x) = x − (z + VGS(x − z, z)) 의 근(독립 bisection, 부동소수 끝까지). 근 없으면 None."""
    lo, hi = z, 1.8

    def h(x):
        # 5.4: 목표가 VGS 범위 아래면 VGS = −inf(h = +inf), 위면 +inf(h = −inf)
        r = T - math.log(I0["nmos"]) - LAM * (x - z) - Oracle.vs_term(z)
        if r < 0.0:
            return math.inf
        v = _vgs("nmos", T, x - z, z)
        return -math.inf if v is None else x - (z + v)
    if h(lo) * h(hi) > 0:
        return None
    for _ in range(200):
        mid = 0.5 * (lo + hi)
        if h(mid) > 0:
            hi = mid
        else:
            lo = mid
    return 0.5 * (lo + hi)


def newton_replica(T, y, start, tol, K):
    """5.5b 를 Q 잔차에 그대로(독립 재구현) -> (V, k, norms)."""
    V = np.array(start, dtype=float)
    norms = []
    k = 0
    while True:
        r, J, _ = q_residual(T, y, *V)
        norms.append(float(np.max(np.abs(r))))
        dlt = np.linalg.solve(J, -r)
        if norms[-1] <= tol and np.max(np.abs(dlt)) <= tol:               # [r7] 잔차와 온전한 걸음 둘 다 tol 안
            return V, k, norms
        assert k < K, "replica 상한"
        a = 1.0
        while True:
            t = V + a * dlt
            ev = q_residual(T, y, *t)
            if ev is not None and np.linalg.norm(ev[0]) < np.linalg.norm(r):
                V = t
                break
            a /= 2.0
            assert a * np.max(np.abs(dlt)) >= tol, "replica 선 탐색 실패"
        k += 1


@pytest.mark.parametrize("y,z_star", [(0.9, 1.0), (0.93, 0.8)])
def test_gauss_seidel_not_contracting_newton_converges(ctx_q, y, z_star):
    """경우 1(수축 안 함): 측정 q ≥ 1 이라 Gauss-Seidel 이 K_max 에서 정지 -> 같은 시작값에서 감쇠 Newton 이 수렴.
    확인: fallback(원인·q ≥ 1·GS Δ 열 = 독립 GS 재구현), method newton, Newton 기록(시작 ‖r‖∞, 반복 수 = 독립 Newton),
    반환 노드전압의 SCC 잔차를 이 test 의 writer 식으로 다시 잰 값 = 마지막 기록 ‖r‖∞ ≤ tol, 닫힌 해와의 차 ≤ κ·‖r‖∞.
    [r7] 받은 점에서 온전한 걸음 ‖Δ‖∞ ≤ tol 이고 닫힌 해와의 차도 tol 안(노드전압 오차 상계가 실제로 지켜짐) -- (0.93, 0.8) 은
    시작점 ‖r‖∞ ≈ 1.1e-2 ≤ tol 인데 해와 tol 넘게 떨어져 있어(전제 확인) 받지 않고 걷는다(r6 규칙이면 0 걸음에 받았을 것).
    [r8] 옛 구성 (0.99, 0.3)(나쁜 조건, 2 걸음)은 M1 VGS = c ≈ 3 mV 라 봉인 9 violated(margin ≈ 2.61) -- 그 거부는
    test_q_ill_conditioned_point_rejected_by_seal_9 가 확인하고, 여기서는 봉인 9 를 통과하는(이 파일 oracle 로 c ≥ 0.06 V,
    margin < 1) 구성으로 Newton 주장을 유지한다."""
    th, (zs, xs), T = theta_q(ctx_q, y, z_star)
    tol = toy_tol()
    K = kmax_ref(1.8, tol)
    z0 = column_start(ctx_q, "z")
    x0 = x_root(T, z0)
    assert x0 is not None                                                 # 전제: 2단계 시작값(1변수 투영 bisection)이 근을 가짐

    def upd(n, c):
        if n == "z":
            return y * min(1.8, c["x"])
        xr = x_root(T, c["z"])
        assert xr is not None
        return xr
    st, _, deltas = gs_ref(upd, ("z", "x"), {"z": z0, "x": x0}, tol, 1.8)
    assert st == "stop" and len(deltas) == K and deltas[-1] / deltas[-2] >= 1.0   # 전제: 독립 GS 도 q ≥ 1 로 K_max 정지

    ev = size_and_seal(ctx_q, th)
    assert ev.report.status == REPORT_UNDEFINED
    log = scc_log(ev.snapshot, ("z", "x"))
    assert log.method == SCC_NEWTON
    cause, q, gs_deltas = log.fallback
    assert cause == "gauss_seidel_stopped"
    assert q == gs_deltas[-1] / gs_deltas[-2] and q >= 1.0
    assert len(gs_deltas) == K
    # 엔진 1변수 bisection 은 마지막 구간 폭 ≤ tol 의 가운데 + writer 식 한 번 다듬기 -> x 오차 ≤ |∂g/∂x|·tol/2 = (LAM/gm_id)·tol/2.
    # gm_id ≥ B − C·VGS_max, VGS_max = 이 θ 의 궤적에서 쓰는 c ≤ 0.2(전제 확인). 한 바퀴 오차는 다음 바퀴로 루프 이득 q 배
    # 전파되므로 k 바퀴 뒤 ≤ eps_x·Σ q^i, Δ 차 ≤ 3·그 값(x 두 값 + z = y·x).
    vgs_max = 0.2
    assert all(q_residual(T, y, zz, x_root(T, zz))[2] <= vgs_max for zz in (z0, zs))
    eps_x = LAM / (B - C * vgs_max) * tol / 2.0
    qm = max(deltas[i + 1] / deltas[i] for i in range(len(deltas) - 1))
    for i, (a, b) in enumerate(zip(gs_deltas, deltas)):
        bound = 3.0 * eps_x * sum(qm ** j for j in range(i + 2))
        assert abs(a - b) <= bound, (i, a, b, bound)

    V_rep, k_rep, norms_rep = newton_replica(T, y, (z0, x0), tol, K)
    assert log.iterations == k_rep and len(log.deltas) == k_rep + 1
    assert abs(log.deltas[0] - norms_rep[0]) <= 2.0 * eps_x              # 시작점 x0 의 bisection 오차만큼
    # 첫 걸음 뒤 ‖r‖∞ 도 독립 Newton 과 같은 수준(엔진 J 간접 확인): 차이 원천 = 시작점 오차 eps_x, J 의 ∂VGS/∂VDS 항의 LUT gds 보간
    # 상대 오차(_gds_interp_rel, x 행 두 칸) -> 걸음 차 ≤ κ0·‖ΔJ‖·‖Δ‖ + (1 + κ0‖J0‖)·eps_x, 잔차 차 ≤ ‖J1‖·그 값.
    assert k_rep == {0.9: 1, 0.93: 1}[y]
    if norms_rep[0] <= tol:                                               # [r7] 판별력: 잔차만 작은 시작점은 받지 않는다
        assert max(abs(z0 - zs), abs(x0 - xs)) > tol and log.iterations >= 1
    assert y != 0.93 or norms_rep[0] <= tol                               # (0.93, 0.8) 이 그 경우임을 전제로 고정
    r0, J0, v0 = q_residual(T, y, z0, x0)
    step = np.linalg.solve(J0, -r0)
    kap0 = np.max(np.sum(np.abs(np.linalg.inv(J0)), axis=1))
    dJ = 2.0 * (LAM / (B - C * v0)) * _gds_interp_rel() * 1.01
    dV1 = kap0 * dJ * np.max(np.abs(step)) + (1.0 + kap0 * np.max(np.sum(np.abs(J0), axis=1))) * eps_x
    J1 = q_residual(T, y, *(np.array([z0, x0]) + step))[1]
    assert abs(log.deltas[1] - norms_rep[1]) <= np.max(np.sum(np.abs(J1), axis=1)) * dV1
    assert log.tol == pytest.approx(tol, rel=1e-12) and log.k_max == K
    V = node_voltages(ev.snapshot)
    r_eng, J_eng, _ = q_residual(T, y, V["z"], V["x"])
    rinf = float(np.max(np.abs(r_eng)))
    assert abs(rinf - log.deltas[-1]) <= 1e-10                            # 기록 ‖r‖∞ = 반환점에서 이 test 의 writer 식 잔차
    assert rinf <= log.tol
    # 닫힌 해와의 차: 같은 VS 칸 안(전제)에서 r(V) − r(V*) = J̄·(V − V*), J 는 gm_id(c) 로만 변해 거의 상수 -> κ = 두 끝 ‖J⁻¹‖∞ 최댓값
    # (여유 1.5 = 두 끝 사이 J 변화분)
    assert bisect.bisect_right(TOY_VS, V["z"]) == bisect.bisect_right(TOY_VS, zs)
    J_star = q_residual(T, y, zs, xs)[1]
    kappa = max(np.max(np.sum(np.abs(np.linalg.inv(Jm)), axis=1)) for Jm in (J_eng, J_star))
    assert abs(V["z"] - zs) <= 1.5 * kappa * rinf and abs(V["x"] - xs) <= 1.5 * kappa * rinf
    # [r7] 받은 점: 이 test 의 J 로 푼 온전한 걸음 ≤ tol, 닫힌 해와의 차 ≤ tol
    assert np.max(np.abs(np.linalg.solve(J_eng, -r_eng))) <= log.tol
    assert max(abs(V["z"] - zs), abs(V["x"] - xs)) <= log.tol
    assert max(abs(V["z"] - V_rep[0]), abs(V["x"] - V_rep[1])) <= log.tol
    # [r8] 봉인 9 통과 전제(이 파일 oracle -- 해에서 I_off/ID = exp(−f(c)), ε = (B − C·c)·tol_V)
    c = zs * (1.0 - y) / y
    assert math.exp(-Oracle.f(c)) / (Oracle.gm_id(c) * tol) < 1.0
    assert ev.report.items[8].item == 9 and ev.report.items[8].status == "pass"


def test_q_ill_conditioned_point_rejected_by_seal_9(ctx_q):
    """[r8] r7 의 나쁜 조건 구성 (y, z*) = (0.99, 0.3): DC 풀이(Newton)는 되지만 M1 VGS = c = z*(1 − y)/y ≈ 3 mV 라 VGS = 0 누설이
    ε·ID 보다 크다 -> 봉인 9 fail(devices ("M1",)) -> size_and_seal 은 SealViolationError(DcEvaluation 없음), 봉인 1~8 은 r7 과 같은
    판정(7 undefined -- toy 에 VDSAT 열 없음, 나머지 pass).
    기대 margin 은 평가 블록 4개 결과(dc_op·dc_tol_v = 블록 입력)에서 이 파일이 npz 식으로 다시 계산한 I_off/(gm_id·tol_V·ID), 그리고
    해에서의 닫힌 식 exp(−f(c))/((B − C·c)·tol_V)(≈ 2.61, 계약 10.6) 과 노드전압 오차 tol 이 주는 범위 안."""
    from gmid_engine.sizing import dc_seal_conduction, dc_tolerances, seal_dc
    from .conftest import eval_calls, resistances_of
    y, z_star = 0.99, 0.3
    th, (zs, xs), T = theta_q(ctx_q, y, z_star)
    tol = toy_tol()
    snap, calls = eval_calls(ctx_q, th)
    log = scc_log(snap, ("z", "x"))
    assert log.method == SCC_NEWTON                                       # 풀이 자체는 r7 그대로 Newton
    snap9 = dc_seal_conduction(dc_tolerances(snap, ctx_q.lut), ctx_q.lut)
    it9 = snap9.value("graph", DC_KEY, "dc_seal_9")
    assert it9.status == "fail" and it9.devices == ("M1",)
    op = snap.value("device", "M1", "dc_op")
    ln_off = math.log(I0["nmos"]) + LAM * op.vds + Oracle.vs_term(op.vsb)  # toy: VGS = 0 마디·VDS Hermite(1차 정확)·VS 선형
    i_off = math.exp(ln_off) * op.W / op.L
    eps = op.gm_id * tol
    m_exp = i_off / (eps * op.current)
    assert m_exp > 1.0 and abs(it9.margin - m_exp) <= 1e-9 * m_exp
    # 해에서의 닫힌 식과의 일치: ln margin 의 노드전압 민감도 ≤ 2·LAM + max|VS 기울기| + 2·C/(B − C·VGS) (VGS·VDS 는 두 노드 차,
    # VSB 는 한 노드) -> |Δ ln m| ≤ 그 값 × 노드 오차(≤ tol, 5.5b [r7])
    c = zs * (1.0 - y) / y
    m_star = math.exp(-Oracle.f(c)) / (Oracle.gm_id(c) * tol)
    sens = 2 * LAM + max(abs(vs_slope(v)) for v in TOY_VS[:-1]) + 2 * C / (B - C * 0.2)
    assert abs(math.log(it9.margin) - math.log(m_star)) <= sens * tol
    assert 2.5 < m_star < 2.7
    with pytest.raises(SealViolationError) as ei:
        seal_dc(snap, calls, ctx_q.lut, resistances_of(ctx_q, th), ())
    d = detail(ei.value)
    st = {x[0]: x[1] for x in d["items"]}
    assert len(st) == 9 and st[9] == "fail" and st[7] == "undefined"
    assert all(st[n] == "pass" for n in st if n not in (7, 9))
    assert d["item"] == 9 and ei.value.record.devices == ("M1",) and ei.value.record.margin == it9.margin
    with pytest.raises(SealViolationError) as ei2:
        size_and_seal(ctx_q, th)
    assert detail(ei2.value)["item"] == 9 and ei2.value.record.margin == it9.margin


def test_newton_failure_in_case_one_is_raised(ctx_q):
    """경우 1 에서 Newton 이 실패하면 그 NonconvergentError 를 그대로 낸다. y = 0.95, z* = 1.0: 시작 후보 (a)·(c) 의 z = 기둥 시작
    0.6 에서는 어떤 x 에서도 M1 목표가 VGS ≥ 0 으로 닿지 않는다(이 test 의 Oracle: 목표 − ln I0 − vs(0.6) < 0, LAM·vds ≥ 0 은 더
    줄일 뿐) -> newton_start_outside_domain(margin None, 반복 0, norms ())."""
    th, _, T = theta_q(ctx_q, 0.95, 1.0)
    z0 = column_start(ctx_q, "z")
    assert T - math.log(I0["nmos"]) - Oracle.vs_term(z0) < 0.0            # 전제
    with pytest.raises(NonconvergentError) as ei:
        size_and_seal(ctx_q, th)
    d = detail(ei.value)
    assert d["reason"] == REASON_NEWTON_START
    assert d["iterations"] == 0 and tuple(d["norms"]) == () and ei.value.record.margin is None
    assert tuple(d["nodes"]) == ("z", "x") and ei.value.record.devices == ("M1", "M2", "M3")


FLOOR_OFF = {"nmos": 1, "pmos": 4}           # r4 toy: nmos VDS 열 0 꺼짐 -> VDS 정의역 하한 0.25 V (5.4 [r4])


def test_r7_q_close_to_one_projection_not_accepted(ctx_q):
    """[r7] r6 에서 경우 2 를 만들던 구성(y = 0.99, z* = 0.7)은 이제 경우 1 이다: x 근이 없어 투영(현재 값 유지)되면 z ← 0.99·x 로
    Δ ≈ 6e-3 ≤ tol 이지만 q ≈ 0.99 -> m = 99·Δ > tol 이라 받지 않고 예측 정지 -> Newton(시작 후보 z = 0.6 은 정의역 밖)
    -> newton_start_outside_domain 이 그대로(SealViolationError 가 아님)."""
    th, _, T = theta_q(ctx_q, 0.99, 0.7)
    assert T - math.log(I0["nmos"]) - Oracle.vs_term(column_start(ctx_q, "z")) < 0.0   # 전제: z0 에서 정의역 밖
    with pytest.raises(NonconvergentError) as ei:
        size_and_seal(ctx_q, th)
    d = detail(ei.value)
    assert d["reason"] == REASON_NEWTON_START and ei.value.__cause__ is None


@pytest.fixture(scope="module")
def acc_floor(tmp_path_factory):
    return new_access(write_r4_lut(tmp_path_factory.mktemp("scc_floor"), off_cols=FLOOR_OFF))


def test_case_two_seal_violation_kept_with_newton_cause(tmp_path, acc_floor):
    """경우 2(5.4 [r6]): Gauss-Seidel 이 수렴 판정([r7] 오차 상계)을 통과한 뒤 strict 검증이 SealViolationError -> Newton 으로
    바꾸지만 Newton 도 실패 -> **GS 수렴점의 strict 검증 SealViolationError 를 그대로**, __cause__ = Newton 의 NonconvergentError.
    회로: MA nmos (y, x, gnd) 가 gate x 를 쓰고(VDS(MA) = V(y)), MB nmos (x, in, y, b = y) 가 y 를 쓴다(1변수), in = 입력 DC
    미선언 W4(창 = 레일). 해의 V(y) = V(in) − VGS(MB) ≈ 0.7 − 0.6 = 0.1 < VDS 하한 0.25 -> 반복 중엔 일시 이탈로 넘어가 수렴하지만
    strict 검증에서 MA 조회가 lut_curve_undefined. 정의역(V(y) ≥ 0.25) 안 해가 없으므로(아래 전제) Newton 도 수렴할 수 없다."""
    net = [mos("MA", "nmos", "y", "x", "gnd", "gnd"), mos("MB", "nmos", "x", "in", "y", "y")]
    src = [two("IX", "current_source", "vdd", "x"), two("IY", "current_source", "vdd", "y")]
    doc = topo("scc_floor_cycle", net, {"in": ("input", "x"), "y": ("output", "y")}, sources=src)
    ctx = build_ctx(tmp_path, doc, acc_floor)[2]
    cyc = [e for e in ctx.base.value("graph", DC_KEY, "dc_scc_order") if e.cyclic]
    assert [set(e.nodes) for e in cyc] == [{"x", "y"}]
    floor = r4_vds_floor(r4_arrays("nmos", off_cols=FLOOR_OFF["nmos"]))
    assert floor == 0.25
    vin = 0.7
    t_mb = r4_ln_idu("nmos", 0.6, 0.5, 0.0)
    th = {("L", "MA"): 1e-6, ("L", "MB"): 1e-6, ("ln_idu", "MA"): r4_ln_idu("nmos", 0.6, 0.25, 0.0),
          ("ln_idu", "MB"): t_mb, ("y", "input_common_mode"): vin / 1.8}
    th.update(free_currents(ctx, {"MA": 1e-5, "MB": 1e-5, "IX": 1e-5, "IY": 1e-5}))
    assert set(th) == set(ctx.schema.components)
    # 전제: VDS(MB) ∈ [0.25, 2.0](켜진 열) 어디서도 VGS(MB) > vin − 0.25 -> V(y) = vin − VGS < 하한: 정의역 안 해 없음
    assert all(r4_vgs_of("nmos", t_mb, 0.25 + 0.05 * i, 0.0) > vin - floor for i in range(36))
    with pytest.raises(SealViolationError) as ei:
        size_and_seal(ctx, th)
    e = ei.value
    d = detail(e)
    assert d["reason"] == "lut_query_failed" and d["lut_reason"] == "lut_curve_undefined"
    assert d["device_query"] == "vgs_of_coordinate" and e.record.devices == ("MA",)
    assert d["vds"] < floor and abs(d["vds"] - (vin - r4_vgs_of("nmos", t_mb, 0.5, 0.0))) <= 0.05
    cause = e.__cause__
    assert isinstance(cause, NonconvergentError)
    cd = detail(cause)
    assert cd["reason"] in (REASON_NEWTON_START, REASON_NEWTON_SINGULAR, REASON_NEWTON_LINE_SEARCH, REASON_NEWTON_CAP)
    assert set(cd["nodes"]) == {"x", "y"} and cause.record.devices == ("MA", "MB")


def test_newton_converged_then_strict_recheck_failure_raised(ctx_q):
    """'Newton 이 수렴하면 같은 strict 검증 바퀴를 다시 돌고 그 실패는 그대로 낸다'. y = 0.5, z* = 0.95 -> x* = 1.9 > vdd(레일 밖 해).
    SCC 잔차(writer 식 그대로, 레일 검사 없음)의 Newton 은 z = 0.5·1.8 = 0.9, x = 0.9 + c(0.9) > 1.8 로 수렴한다(독립 재구현으로
    확인) -> strict 검증의 1변수 x 구간 [z, 1.8](레일) 에 근이 없어 no_root_in_window(유한한 끝 h, margin = min|h|/tol). Newton
    은 성공했으므로 __cause__ 는 없다(경우 2 의 'Newton 도 실패' 규칙이 아니다)."""
    y = 0.5
    th, (zs, xs), T = theta_q(ctx_q, y, 0.95)
    tol = toy_tol()
    z0 = column_start(ctx_q, "z")
    x0 = x_root(T, z0)
    assert x0 is not None
    V_rep, k_rep, norms_rep = newton_replica(T, y, (z0, x0), tol, kmax_ref(1.8, tol))
    assert abs(V_rep[0] - 0.9) <= 2 * tol and V_rep[1] > 1.8               # 전제: Newton 은 레일 밖 x 로 수렴
    with pytest.raises(SealViolationError) as ei:
        size_and_seal(ctx_q, th)
    e = ei.value
    d = detail(e)
    assert e.__cause__ is None
    assert d["reason"] == "no_root_in_window" and d["node"] == "x" and e.record.devices == ("M1",)
    assert d["hi"] == 1.8 and abs(d["lo"] - 0.9) <= 1e-9 and d["item"] == 7
    z_at = d["lo"]

    def h(x):
        return x - (z_at + _vgs("nmos", T, x - z_at, z_at))
    assert abs(d["h_lo"] - h(z_at)) <= 1e-9 and abs(d["h_hi"] - h(1.8)) <= 1e-9
    assert d["h_lo"] < 0 and d["h_hi"] < 0                                # 같은 부호 -> 근 없음
    assert e.record.margin == pytest.approx(min(abs(d["h_lo"]), abs(d["h_hi"])) / tol, rel=1e-9)


# ---- 결정론 ---------------------------------------------------------------

@pytest.mark.parametrize("which", ["S", "Q"])
def test_newton_path_deterministic(tmp_path, toy_lut, which):
    """같은 θ 면 Newton 경로도 snapshot.fp·SccLog 가 같다 -- 새 LutMemo·netlist 순서 뒤집기·같은 ctx 재호출(9절)."""
    if which == "S":
        build, th_of = circuit_s, (lambda c: theta_s(c, 0.98, 0.3)[0])
    else:
        build, th_of = circuit_q, (lambda c: theta_q(c, 0.9, 1.0)[0])
    out = []
    for i, rev in enumerate((False, True, False)):
        sub = tmp_path / ("run%d" % i)
        sub.mkdir()
        ctx = build_ctx(sub, build(reverse=rev), new_access(toy_lut))[2]
        th = th_of(ctx)
        ev = size_and_seal(ctx, th)
        ev2 = size_and_seal(ctx, th)
        assert ev2.snapshot.fp == ev.snapshot.fp
        log = ev.snapshot.value("graph", DC_KEY, "dc_scc_log")
        assert any(lg.method == SCC_NEWTON for lg in log)
        out.append((ev.snapshot.fp, log, node_voltages(ev.snapshot)))
    assert out[0][0] == out[1][0] == out[2][0]
    assert out[0][1] == out[1][1] == out[2][1]
    assert out[0][2] == out[1][2]
