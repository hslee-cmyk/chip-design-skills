"""`residual_probe` -- 설계 41 §2.4 단계 B1(표본 = dof_rank_sample_count 개의 준난수 θ, 봉인 통과 점에서 잔차, r̂ = 중앙값, r̂_spread = 최대 − 최소,
쓰임은 층 0 조합 순서뿐), 체크리스트 D-BM, metrics CONTRACT 10.7·10.9 (7).

평가 커널을 손 결과로 바꿔 끼워 표본 점·정지 규칙·집계만 본다. oracle (a):
* Halton(소수 기저, index 1 부터): 기저 2 -> 1/2, 1/4, 3/4; 기저 3 -> 1/3, 2/3, 1/9. 전류 성분은 시작점 값 그대로.
* 잔차 [0.2, −0.1, 0.4] -> 중앙값 0.2, spread 0.5.
"""
from __future__ import annotations

import math
import sys
import types

import pytest

from gmid_engine.metrics import REPORT_BLOCK_RESIDUAL, MetricBundle
from gmid_engine.sizing import METRICS_KEY, THETA_CURRENT

import gmid_engine.search.residual_probe  # noqa: E402,F401

RP = sys.modules["gmid_engine.search.residual_probe"]

VARS = (types.SimpleNamespace(component=("L", "M1"), log=False, lo=1.0, hi=3.0),
        types.SimpleNamespace(component=(THETA_CURRENT, "I1"), log=True, lo=-12.0, hi=-8.0),
        types.SimpleNamespace(component=("ln_idu", "M2"), log=True, lo=0.0, hi=math.log(9.0)))
START = {("L", "M1"): 2.0, (THETA_CURRENT, "I1"): 1e-5, ("ln_idu", "M2"): 1.0}


def _snap(residual):
    rep = (("gain_residual_db", residual),)
    bundle = MetricBundle((), reports=((REPORT_BLOCK_RESIDUAL, rep),))
    return types.SimpleNamespace(value=lambda kind, key, field: bundle)


def _setup(monkeypatch, residuals, statuses=None, budget=None):
    calls = []
    statuses = statuses or ["sealed"] * len(residuals)

    def evaluate(sctx, point, cells):
        k = len(calls)
        calls.append(dict(point))
        sctx.counters["kernel_calls"] += 1
        return types.SimpleNamespace(status=statuses[k], evaluation=types.SimpleNamespace(snapshot=_snap(residuals[k])))

    monkeypatch.setattr(RP, "evaluate", evaluate)
    monkeypatch.setattr(RP, "centre_start", lambda sctx: (VARS, dict(START), ("cells",), None))
    return types.SimpleNamespace(eval_budget=budget, counters={"kernel_calls": 0}), calls


def test_halton_points_and_summary(monkeypatch):
    sctx, calls = _setup(monkeypatch, [0.2, -0.1, 0.4])
    got = RP.residual_probe(sctx, 3)
    assert got.stop == "enough" and got.evaluated == 3 and got.values == (0.2, -0.1, 0.4)
    assert got.summary.median_db == pytest.approx(0.2) and got.summary.spread_db == pytest.approx(0.5) and got.summary.count == 3
    lin = [c[("L", "M1")] for c in calls]
    assert lin == pytest.approx([1.0 + 2.0 * h for h in (0.5, 0.25, 0.75)])           # 기저 2
    ln = [math.log(c[("ln_idu", "M2")]) for c in calls]
    assert ln == pytest.approx([math.log(9.0) * h for h in (1 / 3, 2 / 3, 1 / 9)])  # 기저 3, ln 좌표
    assert all(c[(THETA_CURRENT, "I1")] == 1e-5 for c in calls)                      # 전류는 시작점 값


def test_unsealed_points_skipped_and_trials_stop(monkeypatch):
    sctx, calls = _setup(monkeypatch, [0.2, 0.3, 0.4], statuses=["sealed", "failed", "failed"])
    got = RP.residual_probe(sctx, 3)
    assert got.values == (0.2,) and got.evaluated == 3 and got.stop == "trials"


def test_eval_budget_stop(monkeypatch):
    sctx, _calls = _setup(monkeypatch, [0.1] * 10, statuses=["failed"] * 10, budget=4)
    got = RP.residual_probe(sctx, 3)
    assert got.stop == "eval_budget" and got.evaluated == 4 and got.summary.count == 0 and got.summary.median_db is None
