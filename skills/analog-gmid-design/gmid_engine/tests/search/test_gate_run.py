"""`run_sensitivity_gate` -- 설계 40 §3.8-2(감도 게이트: 분해 metric 이 **읽지 않는** 소자를 건드리는 θ 방향으로 섭동, 최종 해에서 돈다),
체크리스트 D-SG, metrics CONTRACT 10.7.

이 test 는 섭동 점 평가(fd_jacobian)를 손 결과로 바꿔 끼워 '어느 방향을 섭동하는가'와 '판정에 무엇을 넘기는가'만 본다.
oracle (a) 구성: 읽는 소자 {M1, M2}(블록 잔차 보고 read_devices). θ 변수와 그 영향 소자(손으로 정함):
  L:M1 -> {M1}(읽음, 건너뜀), current:I1 -> KCL 원뿔에서 원천 I1 을 항으로 갖는 MOS {M1, M3}(M1 읽음 -> 건너뜀),
  current:I2 -> {M3}(안 읽음 -> 섭동), ln_idu:M9 -> {M9}(섭동), y:vcm -> 모든 MOS(건너뜀).
  섭동 결과: current:I2 = 분해 그대로·MNA 0.4 dB 이동 -> 오류, ln_idu:M9 = 둘 다 그대로 -> 정상.
"""
from __future__ import annotations

import sys
import types

import pytest

from gmid_engine.metrics import REPORT_BLOCK_RESIDUAL, MetricBundle
from gmid_engine.sizing import METRICS_KEY, THETA_CURRENT, THETA_Y
from gmid_engine.search.gate_run import run_sensitivity_gate

GR = sys.modules["gmid_engine.search.gate_run"]


def _snapshot(dec, full, res=1e-13, read=("M1", "M2")):
    report = (("view", "t"), ("gain_residual_db", full - dec), ("full_gain_db", full), ("decomposed_gain_db", dec),
              ("rout_residual_ohm", None), ("solve_residual", res), ("read_devices", read), ("block_gain", ()), ("ff_contrib", ()),
              ("undefined", ()))
    bundle = MetricBundle((), reports=((REPORT_BLOCK_RESIDUAL, report),))

    def value(kind, key, field):
        assert (kind, key, field) == ("graph", METRICS_KEY, "metrics_aux")
        return bundle

    return types.SimpleNamespace(value=value, column=lambda kind, field: tuple((m, None) for m in ("M1", "M2", "M3", "M9")))


def _result(dec, full):
    return types.SimpleNamespace(evaluation=types.SimpleNamespace(snapshot=_snapshot(dec, full)), theta=THETA,
                                 key=types.SimpleNamespace(cells=("c",)))


VARS = tuple(types.SimpleNamespace(component=c, log=lg, lo=0.0, hi=10.0) for c, lg in (
    (("L", "M1"), False), ((THETA_CURRENT, "I1"), True), ((THETA_CURRENT, "I2"), True), (("ln_idu", "M9"), False),
    ((THETA_Y, "vcm"), False)))
THETA = {("L", "M1"): 1e-6, (THETA_CURRENT, "I1"): 1e-5, (THETA_CURRENT, "I2"): 2e-5, ("ln_idu", "M9"): -3.0, (THETA_Y, "vcm"): 0.9}
TERM = lambda src: types.SimpleNamespace(source=src)  # noqa: E731
SCTX = types.SimpleNamespace(domain=types.SimpleNamespace(variables=VARS),
                             dc=types.SimpleNamespace(schema=types.SimpleNamespace(
                                 current_cone=(("M1", (TERM("I1"),)), ("M3", (TERM("I1"), TERM("I2"))), ("M2", (TERM("I0"),))))))


def test_perturbs_only_unread_directions_and_flags_error(monkeypatch):
    seen = {}

    def fake(sctx, variables, x, base, cells, to_theta, origin, skip):
        seen["skip"] = set(skip)
        seen["x"] = list(x)
        out = []
        for i, v in enumerate(variables):
            if i in skip:
                out.append((base, 0.0))
            elif v.component == (THETA_CURRENT, "I2"):
                out.append((_result(60.0, 60.4), 0.01))
            else:
                out.append((_result(60.0, 60.0), 0.01))
        return out

    monkeypatch.setattr(GR, "fd_jacobian", fake)
    got = run_sensitivity_gate(SCTX, _result(60.0, 60.0))
    assert seen["skip"] == {0, 1, 4}                        # L:M1·current:I1(M1 포함)·y 는 읽는 소자를 건드린다
    assert seen["x"][1] == pytest.approx(__import__("math").log(1e-5))   # log 변수는 ln 좌표
    assert got.ok is False and got.errors == ("current:I2",)
    assert [c[0] for c in got.checks] == ["current:I2", "ln_idu:M9"]


def test_no_report_no_gate():
    base = types.SimpleNamespace(evaluation=types.SimpleNamespace(snapshot=types.SimpleNamespace(
        value=lambda *a: (_ for _ in ()).throw(KeyError("metrics_aux")))))
    assert run_sensitivity_gate(SCTX, base) is None
    assert run_sensitivity_gate(SCTX, types.SimpleNamespace(evaluation=None)) is None


def test_all_directions_read_no_gate(monkeypatch):
    monkeypatch.setattr(GR, "fd_jacobian", lambda *a, **k: pytest.fail("평가하면 안 된다"))
    base = _result(60.0, 60.0)
    base.evaluation.snapshot = _snapshot(60.0, 60.0, read=("M1", "M2", "M3", "M9"))
    assert run_sensitivity_gate(SCTX, base) is None
