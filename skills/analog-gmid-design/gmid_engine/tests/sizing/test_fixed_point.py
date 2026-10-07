"""`gauss_seidel(nodes, values, update, tolerance, width, devices=()) -> (values, (k, deltas, tol, K_max))` -- CONTRACT 5.5.

반복 k 마다 nodes 순서로 update(node, current) 를 바로 반영, Δk = 최대 |변화|, tol = tolerance(current), K_max = k_max(width, tol).
Δk ≤ tol 이면 반환. 아니면 stop = (k ≥ K_max); k ≥ 3 이고 Δk−1 > 0 이면 q = Δk/Δk−1, q < 1 이면
stop |= q^max(K_max − k, 0)·Δk/(1 − q) > tol. stop -> NonconvergentError(devices, margin = Δk/tol, detail nodes·iterations·
deltas·tol·k_max). 입력 values 불변. 기대값은 이 파일의 독립 재구현과 손계산.
"""
import math

import pytest

from gmid_engine.core import NonconvergentError
from gmid_engine.sizing import gauss_seidel


def ref(nodes, values, update, tolerance, width):
    cur = dict(values)
    deltas = []
    k = 0
    while True:
        k += 1
        d = 0.0
        for n in nodes:
            new = update(n, cur)
            d = max(d, abs(new - cur[n]))
            cur[n] = new
        deltas.append(d)
        tol = tolerance(cur)
        km = 1 if width <= tol else math.ceil(math.log2(width / tol))
        if d <= tol:
            return "ok", cur, (k, tuple(deltas), tol, km)
        stop = k >= km
        if k >= 3 and deltas[-2] > 0:
            q = d / deltas[-2]
            if q < 1:
                stop = stop or (q ** max(km - k, 0)) * d / (1 - q) > tol
        if stop:
            return "fail", cur, (k, tuple(deltas), tol, km)


def test_hand_contraction():
    vals = {"x": 0.0}
    out, (k, deltas, tol, km) = gauss_seidel(("x",), vals, lambda n, c: 0.5 * c["x"] + 1, lambda c: 1e-3, 4.0)
    # Δk = 2^−(k−1) -> 2^−10 ≤ 1e-3 at k = 11; K_max = ceil(log2 4000) = 12; 예측 2^−10 ≤ tol 이라 조기 정지 없음
    assert k == 11 and km == 12 and tol == 1e-3
    assert deltas == tuple(2.0 ** -(i) for i in range(11))
    assert out["x"] == 2.0 - 2.0 ** -10
    assert vals == {"x": 0.0}                                  # 입력 불변


def test_two_nodes_update_in_order_immediately():
    upd = {"a": lambda c: 0.5 * c["b"], "b": lambda c: 0.5 * c["a"] + 1.0}
    f = lambda n, c: upd[n](c)                                  # noqa: E731
    vals = {"a": 0.0, "b": 0.0}
    out, info = gauss_seidel(("a", "b"), vals, f, lambda c: 1e-9, 2.0)
    st, exp, exp_info = ref(("a", "b"), vals, f, lambda c: 1e-9, 2.0)
    assert st == "ok" and out == exp and info == exp_info
    # 첫 바퀴: a = 0.5·0 = 0, b = 0.5·0 + 1 = 1 (a 의 새 값을 바로 씀) -> Δ1 = 1
    assert info[1][0] == 1.0
    assert abs(out["a"] - 2 / 3) <= 1e-8 and abs(out["b"] - 4 / 3) <= 1e-8
    # 순서를 바꾸면 반복 경로가 달라진다(즉시 반영)
    _, info2 = gauss_seidel(("b", "a"), vals, f, lambda c: 1e-9, 2.0)
    assert info2[1] != info[1]


def test_oscillation_stops_at_kmax():
    with pytest.raises(NonconvergentError) as ei:
        gauss_seidel(("x",), {"x": 0.0}, lambda n, c: 1.0 - c["x"], lambda c: 0.01, 1.0, devices=("M2", "M1"))
    rec = ei.value.record
    d = dict(rec.detail)
    # K_max = ceil(log2 100) = 7, Δ 항상 1, q = 1 (조기 정지 없음) -> k = 7 에서 정지
    assert d["iterations"] == 7 and d["k_max"] == 7 and d["tol"] == 0.01
    assert tuple(d["deltas"]) == (1.0,) * 7
    assert tuple(d["nodes"]) == ("x",)
    assert rec.margin == pytest.approx(1.0 / 0.01)
    assert rec.devices == ("M1", "M2")


def test_slow_contraction_predicted_stop():
    """x ← 0.9x + 1, tol 1e-3, width 10: K_max 14, k = 3 에서 q = 0.9, 예측 0.9^11·0.81/0.1 = 2.54 > tol -> 정지."""
    with pytest.raises(NonconvergentError) as ei:
        gauss_seidel(("x",), {"x": 0.0}, lambda n, c: 0.9 * c["x"] + 1.0, lambda c: 1e-3, 10.0)
    d = dict(ei.value.record.detail)
    assert d["iterations"] == 3 and d["k_max"] == 14
    assert ei.value.record.margin == pytest.approx(0.81 / 1e-3)
    st, _, info = ref(("x",), {"x": 0.0}, lambda n, c: 0.9 * c["x"] + 1.0, lambda c: 1e-3, 10.0)
    assert st == "fail" and info[0] == 3


def test_tolerance_reevaluated_each_iteration():
    calls = []

    def tol(c):
        calls.append(dict(c))
        return 1e-3
    gauss_seidel(("x",), {"x": 0.0}, lambda n, c: 0.5 * c["x"] + 1, tol, 4.0)
    assert len(calls) == 11 and calls[0] == {"x": 1.0}


def test_already_converged_one_iteration():
    out, (k, deltas, tol, km) = gauss_seidel(("x",), {"x": 2.0}, lambda n, c: 0.5 * c["x"] + 1, lambda c: 1e-6, 1.0)
    assert k == 1 and deltas == (0.0,) and out == {"x": 2.0}
