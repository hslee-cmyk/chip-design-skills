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
from gmid_engine.sizing import METRICS_KEY, THETA_CURRENT, WfCell

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


# [FS-1 A-196 signature-misses-search] spec W19: 첫 시작점 wf = initial_wf(base) -- 가짜 sctx 의 `dc.base` 가 `graph/start: wf_start` 를 준다(interface §3.4 initial_wf).
# oracle (d: 구성): 칸 (M1,) 키 100 하나인 wf_start -> initial_wf 의 keys == (100,).
WF_CELLS = (WfCell(("M1",), 100),)


def _fake_base(cells=WF_CELLS):
    return types.SimpleNamespace(value=lambda kind, key, field: cells if (kind, key, field) == ("graph", "start", "wf_start") else None)


def _setup(monkeypatch, residuals, statuses=None, budget=None, cells=WF_CELLS):
    calls = []
    wfs = []
    statuses = statuses or ["sealed"] * len(residuals)

    def evaluate(sctx, point, cells, wf, *a, **kw):
        wfs.append(wf)
        k = len(calls)
        calls.append(dict(point))
        sctx.counters["kernel_calls"] += 1
        return types.SimpleNamespace(status=statuses[k], evaluation=types.SimpleNamespace(snapshot=_snap(residuals[k])))

    monkeypatch.setattr(RP, "evaluate", evaluate)
    monkeypatch.setattr(RP, "centre_start", lambda sctx: (VARS, dict(START), ("cells",), None))
    # [XRUN-F1 card C] 정지는 search_stop 기준 -> 가짜 sctx 는 interface 1절의 칸을 모두 갖는다(선언 실행, 시계 없음)
    sctx = types.SimpleNamespace(eval_budget=budget, eval_budget_source="declared", eval_times=[], deadline=None,
                                 domain=types.SimpleNamespace(variables=VARS), counters={"kernel_calls": 0},
                                 dc=types.SimpleNamespace(base=_fake_base(cells)))
    sctx.seen_wf = wfs
    return sctx, calls


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
    assert len(sctx.seen_wf) == 3 and all(w.keys == (100,) and w.cells_ref is WF_CELLS for w in sctx.seen_wf)   # [FS-1 W19] 표본 평가의 wf = initial_wf(base)


def test_wf_start_undefined_evaluates_nothing(monkeypatch):
    """[FS-1 A-196 W19·interface §3.4 S-B4/§6] `wf_start` 에 None 칸이 있으면 initial_wf = None -> 평가 0, 정지 사유 `start_undefined` (fail-closed). oracle (d): 구성 -- 칸 키 None 하나."""
    sctx, calls = _setup(monkeypatch, [0.2, 0.3, 0.4], cells=(WfCell(("M1",), None),))
    got = RP.residual_probe(sctx, 3)
    assert got.stop == "start_undefined" and got.evaluated == 0 and calls == [] and got.values == ()


def test_unsealed_points_skipped_and_trials_stop(monkeypatch):
    sctx, calls = _setup(monkeypatch, [0.2, 0.3, 0.4], statuses=["sealed", "failed", "failed"])
    got = RP.residual_probe(sctx, 3)
    assert got.values == (0.2,) and got.evaluated == 3 and got.stop == "trials"


def test_eval_budget_stop(monkeypatch):
    sctx, _calls = _setup(monkeypatch, [0.1] * 10, statuses=["failed"] * 10, budget=4)
    got = RP.residual_probe(sctx, 3)
    assert got.stop == "eval_budget" and got.evaluated == 4 and got.summary.count == 0 and got.summary.median_db is None


# [XRUN-F1 card C] interface card xrunf1c C6 (C-T8) -- residual_probe 의 정지는 search_stop 기준(탐색 예산).
# oracle: (손) 유도 실행(전이 뒤): D = 4 + R, R = 2 × 3(VARS 3개) = 6 -> 탐색 예산 = D − R = 4 -> 위 test_eval_budget_stop 과 같은 기대(평가 4).
def test_eval_budget_stop_derived_run_uses_d_minus_reserve(monkeypatch):
    sctx, _calls = _setup(monkeypatch, [0.1] * 10, statuses=["failed"] * 10, budget=4 + 2 * len(VARS))
    sctx.eval_budget_source = "derived_once:floor(B/median_t_eval)@n_evals=4"
    got = RP.residual_probe(sctx, 3)
    assert got.stop == "eval_budget" and got.evaluated == 4 and got.summary.count == 0
