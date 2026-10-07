"""`seal_dc(snapshot, calls, lut, resistances, linear_devices) -> DcEvaluation` -- CONTRACT 6절.

순서 tol -> 1·2·3·6·7·8 -> 4(calls + 위 7개) -> 5 -> report. violated -> SealViolationError(devices = margin 최대 fail 항목의
devices, margin = 그 margin, detail = item·nodes·items((번호, 상태, margin) 8개)·item_detail). undefined ->
DcEvaluation(sealed=None). [r4] VDSAT 열이 없는 LUT(conftest 기본 toy)에서는 항목 7 이 undefined 라 SealedSnapshot 이 나오지
않고(음성 확인), 열이 있는 LUT(r4 toy)에서는 1~8 이 모두 pass 인 점이 SealedSnapshot 이 된다 -- 7 fail 이면 나오지 않는다(음성).
위반은 출력 필드를 자기 block_version 그대로 바꿔 넣어 만든다(입력 투영이 같아 봉인 4 는 pass 로 남는다).
"""
import dataclasses

import pytest

from gmid_engine.core import SealViolationError
from gmid_engine.sizing import DC_KEY, DcEvaluation, PathValue, SealReport, SealedSnapshot, seal_dc, size_and_seal

from .conftest import (eval_calls, node_voltages, resistances_of, tamper, theta_a, theta_c, theta_r4c)


def _seal(ctx, snap, calls, th, lin=()):
    return seal_dc(snap, calls, ctx.lut, resistances_of(ctx, th), tuple(lin))


def test_undefined_evaluation(ctx_c):
    ctx, th = ctx_c[2], theta_c()
    snap, calls = eval_calls(ctx, th)
    ev = _seal(ctx, snap, calls, th)
    assert isinstance(ev, DcEvaluation)
    assert ev.sealed is None
    assert isinstance(ev.report, SealReport) and ev.report.status == "undefined"
    assert [i.item for i in ev.report.items] == list(range(1, 9))
    assert ev.snapshot.value("graph", DC_KEY, "dc_seal_report") == ev.report
    for n in (1, 2, 3, 6, 7, 8):
        assert ev.snapshot.value("graph", DC_KEY, "dc_seal_%d" % n) == ev.report.items[n - 1]
    # 봉인 4 = calls 4개 + 봉인 계산 블록 7개(tol + 1·2·3·6·7·8)
    assert dict(ev.report.items[3].detail)["n_checked"] == len(calls) + 7


def test_linear_devices_reach_item7(ctx_c):
    ctx, th = ctx_c[2], theta_c()
    snap, calls = eval_calls(ctx, th)
    ev = _seal(ctx, snap, calls, th, ("M2",))
    assert ev.report.items[6].devices == ("M1",)


@pytest.mark.parametrize("y", [0.2, 0.5, 0.8])
@pytest.mark.parametrize("i2", [1e-6, 1e-5, 1e-4])
def test_never_sealed_snapshot(ctx_c, y, i2):
    """음성: 일관 DC 점이어도 항목 7 undefined -> SealedSnapshot 0."""
    ctx, th = ctx_c[2], theta_c(y=y, i2=i2)
    snap, calls = eval_calls(ctx, th)
    ev = _seal(ctx, snap, calls, th)
    assert ev.sealed is None and not isinstance(ev.sealed, SealedSnapshot)
    assert ev.report.status == "undefined"
    assert all(i.status == "pass" for i in ev.report.items if i.item != 7)


def test_violation_reports_worst_item(ctx_c):
    ctx, th = ctx_c[2], theta_c()
    snap, calls = eval_calls(ctx, th)
    v_in = node_voltages(snap)["in"]
    ops = dict(snap.column("device", "dc_op"))
    bad = tamper(snap, "dc_columns", "node", "dc_path_values", {"in": (PathValue(("vgs", "M1"), v_in + 0.5),)},
                 version=snap.block_version("dc_columns"))
    bad = tamper(bad, "dc_widths", "device", "dc_op",
                 {"M1": dataclasses.replace(ops["M1"], idu_forward=ops["M1"].idu_forward * 2.0)},
                 version=snap.block_version("dc_widths"))
    with pytest.raises(SealViolationError) as ei:
        _seal(ctx, bad, calls, th)
    rec = ei.value.record
    d = dict(rec.detail)
    items = d["items"]
    assert [x[0] for x in items] == list(range(1, 9))
    st = {x[0]: x[1] for x in items}
    assert st[1] == "fail" and st[2] == "fail" and st[4] == "pass" and st[7] == "undefined"
    margins = {x[0]: x[2] for x in items if x[1] == "fail"}
    worst = max(margins, key=margins.get)
    assert worst == 1                                   # 0.5/tol ≫ ln2/gm/tol
    assert d["item"] == 1
    assert rec.margin == margins[1]
    assert "in" in d["nodes"]
    assert "item_detail" in d


def test_violation_item6_devices(tmp_path, toy_access):
    from .conftest import Oracle, build_ctx, circuit_cs_res
    doc = circuit_cs_res(bulk_m1="out")
    doc["topology_name"] = "hand_seal_bulk"
    ctx = build_ctx(tmp_path, doc, toy_access)[2]
    th = {("L", "M1"): 1e-6, ("ln_idu", "M1"): Oracle.ln_idu("nmos", 0.6, 0.3, -0.3),
          ("current", "R1"): 1e-5, ("resistance", "R1"): 1.5e5}
    snap, calls = eval_calls(ctx, th)
    with pytest.raises(SealViolationError) as ei:
        _seal(ctx, snap, calls, th)
    assert dict(ei.value.record.detail)["item"] == 6
    assert ei.value.record.devices == ("M1",)


def test_circuit_a_undefined(ctx_a):
    ctx, th = ctx_a[2], theta_a()
    snap, calls = eval_calls(ctx, th)
    ev = _seal(ctx, snap, calls, th)
    assert ev.sealed is None and ev.report.status == "undefined"


# ---------------------------------------------------------------------------
# [r4] VDSAT 열이 있는 LUT -- SealedSnapshot (양성·음성)
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("y,v1,v2", [(0.5, 0.6, 0.7), (0.4, 0.8, 0.55)])
def test_sealed_snapshot_when_all_pass(ctx_r4c, y, v1, v2):
    """1~8 이 모두 pass -> REPORT_SEALED, DcEvaluation(sealed=SealedSnapshot(snapshot, report))."""
    th = theta_r4c(y=y, v1=v1, v2=v2)
    snap, calls = eval_calls(ctx_r4c, th)
    ev = _seal(ctx_r4c, snap, calls, th)
    assert [i.status for i in ev.report.items] == ["pass"] * 8
    assert ev.report.status == "sealed"
    assert isinstance(ev.sealed, SealedSnapshot)
    assert ev.sealed.report == ev.report
    assert ev.sealed.snapshot.fp == ev.snapshot.fp
    assert ev.snapshot.value("graph", DC_KEY, "dc_seal_report") == ev.report
    # size_and_seal 경로도 같다
    ev2 = size_and_seal(ctx_r4c, th)
    assert isinstance(ev2.sealed, SealedSnapshot) and ev2.report.status == "sealed"
    assert ev2.snapshot.fp == ev.snapshot.fp


@pytest.mark.parametrize("y,dev", [(0.1, "M1"), (0.9, "M2")])
def test_no_sealed_snapshot_when_item7_fails(ctx_r4c, y, dev):
    """음성: 다른 항목이 모두 pass 여도 봉인 7 fail -> violated -> SealViolationError(DcEvaluation 없음)."""
    th = theta_r4c(y=y)
    snap, calls = eval_calls(ctx_r4c, th)
    with pytest.raises(SealViolationError) as ei:
        _seal(ctx_r4c, snap, calls, th)
    rec = ei.value.record
    d = dict(rec.detail)
    st = {x[0]: x[1] for x in d["items"]}
    assert st[7] == "fail" and all(st[n] == "pass" for n in st if n != 7)
    assert d["item"] == 7 and rec.devices == (dev,)
    m7 = {x[0]: x[2] for x in d["items"]}[7]
    assert rec.margin == m7 and m7 > 1.0
    assert dict(d["item_detail"])["worst"] == dev
    with pytest.raises(SealViolationError):
        size_and_seal(ctx_r4c, th)


def test_linear_declared_failing_device_still_sealed(ctx_r4c):
    """봉인 7 행에서 빠지는 linear 선언 소자는 포화 위반이어도 봉인을 막지 않는다(음성의 반대쪽)."""
    th = theta_r4c(y=0.1)                                       # M1 VDS 0.18 < VDsat
    snap, calls = eval_calls(ctx_r4c, th)
    ev = _seal(ctx_r4c, snap, calls, th, ("M1",))
    assert ev.report.status == "sealed" and isinstance(ev.sealed, SealedSnapshot)
    assert dict(ev.report.items[6].detail)["n_checked"] == 1
