"""`ls_constraint_rows` -- 설계 40 §3.8-3('driving_spec 이 선언되면 이 값들로 제약 행'), DEC-58·DEC-70, 체크리스트 D-GB8a, metrics CONTRACT 10.7.

행 정의(search ls_constraints 머리말 = 계약): 슬루 행 c = (I_max − SR·C)/s(s = 그 방향 전류 분해능), active = c ≤ 1, 이름 `ls:<net>:<방향>:slew_rate>=`;
피크 행 c = load_peak_margin_a / (출력 노드 전류 분해능 최대값), 이름 `ls:load_peak_amp>=`. 미상 전류·분해능 없음·보고 없음·봉인 안 됨은 행 없이 미측정.

oracle (a) 손계산: I 20 µA, SR 10 V/µs, C 1 pF -> I − SR·C = 20e-6 − 1e7·1e-12 = 10 µA, s 1 µA -> c = 10(비활성).
I 30 µA, s 0.5 µA -> c = (30e-6 − 10e-6)/0.5e-6 = 40. 피크: 여유 5 µA / max(1, 0.5) µA = 5.
"""
from __future__ import annotations

import pytest

from gmid_engine.authoring import DrivingDecl
from gmid_engine.metrics import REPORT_LS_FIELDS, MetricBundle
from gmid_engine.search.ls_constraints import ls_constraint_rows


def _bundle(nodes, margin=None, name=REPORT_LS_FIELDS):
    rep = (("view", "t"), ("load_peak_margin_a", margin), ("nodes", tuple(nodes)))
    return MetricBundle((), reports=((name, rep),))


NODE = ("out", 1e-12, 20e-6, 30e-6, 2e7, 3e7, 1e-6, 0.5e-6, ())


def test_slew_rows_hand_values():
    rows, unmeasured = ls_constraint_rows(_bundle((NODE,)), DrivingDecl(1e7, None, None))
    got = {r.name: (r.c, r.active) for r in rows}
    assert got == {"ls:out:charge:slew_rate>=": (pytest.approx(10.0, rel=1e-12), False),
                   "ls:out:discharge:slew_rate>=": (pytest.approx(40.0, rel=1e-12), False)}
    assert unmeasured == ()


def test_slew_row_active_when_close_or_violated():
    rows, _ = ls_constraint_rows(_bundle((NODE,)), DrivingDecl(3e7, None, None))      # SR·C = 30 µA
    got = {r.name: (r.c, r.active) for r in rows}
    assert got["ls:out:charge:slew_rate>=" ] == (pytest.approx(-10.0, rel=1e-12), True)
    assert got["ls:out:discharge:slew_rate>="] == (pytest.approx(0.0, abs=1e-9), True)


def test_peak_row():
    rows, unmeasured = ls_constraint_rows(_bundle((NODE,), margin=5e-6), DrivingDecl(None, 15e-6, None))
    assert [(r.name, r.c) for r in rows] == [("ls:load_peak_amp>=", pytest.approx(5.0, rel=1e-12))]
    assert unmeasured == ()


def test_unmeasured_reasons():
    drv = DrivingDecl(1e7, 15e-6, None)
    assert ls_constraint_rows(None, drv) == ((), (("slew_rate_v_per_s", ">=", "ss_requires_sealed_snapshot"),
                                                  ("load_peak_amp", ">=", "ss_requires_sealed_snapshot")))
    rows, un = ls_constraint_rows(MetricBundle(()), drv)
    assert rows == () and set(un) == {("slew_rate_v_per_s", ">=", "ls_fields_unavailable"), ("load_peak_amp", ">=", "ls_fields_unavailable")}
    kappa = ("out", 1e-12, None, 30e-6, None, 3e7, None, 0.5e-6, ())
    rows, un = ls_constraint_rows(_bundle((kappa,)), DrivingDecl(1e7, 15e-6, None))
    assert [r.name for r in rows] == ["ls:out:discharge:slew_rate>="]
    assert set(un) == {("slew_rate_v_per_s", ">=", "slew_current_unbounded"), ("load_peak_amp", ">=", "load_peak_current_unbounded")}
    nores = ("out", 1e-12, 20e-6, 30e-6, 2e7, 3e7, None, 0.0, ())
    rows, un = ls_constraint_rows(_bundle((nores,)), DrivingDecl(1e7, None, None))
    assert rows == () and un == (("slew_rate_v_per_s", ">=", "slew_resolution_undefined"),)


def test_no_driving_no_rows():
    assert ls_constraint_rows(_bundle((NODE,)), None) == ((), ())
    assert ls_constraint_rows(_bundle((NODE,)), DrivingDecl(None, None, 1e-3)) == ((), ())     # DC 부하 전류는 KCL 입력 -- 행 없음
