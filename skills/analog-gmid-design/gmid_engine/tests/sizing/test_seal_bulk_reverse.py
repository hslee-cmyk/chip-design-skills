"""봉인 6 `dc_seal_bulk_reverse(snapshot)` -- CONTRACT 6절: MOS 마다 max(0, −vsb, −(vds + vsb)) ≤ tol_v.

위반 회로: 회로 A 의 M1 bulk 를 out 에 선언 -> vsb = V(gnd) − V(out) < 0. toy LUT VS 축이 −0.45 를 포함해 LUT 조회는 통과하고
봉인 6 만 걸린다.
"""
import dataclasses

import pytest

from gmid_engine.core import SealViolationError
from gmid_engine.sizing import dc_seal_bulk_reverse, size_and_seal

from .conftest import (Oracle, assert_item, build_ctx, circuit_cs_res, judge_expect, rel_close, seal_item, tamper,
                       theta_a, theta_c, with_tol)


def rows_of(snap):
    ops = dict(snap.column("device", "dc_op"))
    tolv = dict(snap.column("device", "dc_tol_v"))
    return [(m, max(0.0, -ops[m].vsb, -(ops[m].vds + ops[m].vsb)), tolv[m], (m,), ()) for m in sorted(ops)]


def run(snap):
    return seal_item(dc_seal_bulk_reverse(snap), 6)


def test_pass_zero_magnitude(ctx_c):
    snap, _ = with_tol(ctx_c[2], theta_c())
    exp = judge_expect(rows_of(snap))
    item = run(snap)
    assert_item(item, exp, 6)
    assert item.magnitude == 0.0


@pytest.fixture
def ctx_bulk_out(tmp_path, toy_access):
    doc = circuit_cs_res(bulk_m1="out")
    doc["topology_name"] = "hand_cs_res_bulk_out"
    return build_ctx(tmp_path, doc, toy_access)[2]


def theta_bulk(vout):
    i, r = 1e-5, (1.8 - vout) / 1e-5
    return {("L", "M1"): 1e-6, ("ln_idu", "M1"): Oracle.ln_idu("nmos", 0.6, vout, -vout),
            ("current", "R1"): i, ("resistance", "R1"): r}


def test_fail_hand(ctx_bulk_out):
    snap, _ = with_tol(ctx_bulk_out, theta_bulk(0.3))
    exp = judge_expect(rows_of(snap))
    assert exp["status"] == "fail" and exp["devices"] == ("M1",)
    item = run(snap)
    assert_item(item, exp, 6)
    # 손계산: vsb = 0 − 0.3 = −0.3, vds = 0.3 -> max(0, 0.3, 0) = 0.3
    assert rel_close(item.magnitude, 0.3, 1e-9)
    assert rel_close(item.margin, 0.3 / Oracle.tol_v(), 1e-9)


def test_drain_below_bulk_term(ctx_c):
    """−(vds + vsb) 항: vds = 0.1, vsb = −0.2 로 바꾼 DeviceOp -> max(0, 0.2, 0.1) = 0.2."""
    snap, _ = with_tol(ctx_c[2], theta_c())
    op = dict(snap.column("device", "dc_op"))["M1"]
    s2 = tamper(snap, "dc_widths", "device", "dc_op", {"M1": dataclasses.replace(op, vds=0.05, vsb=0.1 - 0.2)})
    exp = judge_expect(rows_of(s2))
    assert_item(run(s2), exp, 6)
    assert rel_close(run(s2).magnitude, 0.1, 1e-9)
    s3 = tamper(snap, "dc_widths", "device", "dc_op", {"M1": dataclasses.replace(op, vds=-0.3, vsb=0.1)})
    assert rel_close(run(s3).magnitude, 0.2, 1e-9)                    # −(−0.3 + 0.1) = 0.2


def test_size_and_seal_raises_item6(ctx_bulk_out):
    with pytest.raises(SealViolationError) as ei:
        size_and_seal(ctx_bulk_out, theta_bulk(0.3))
    d = dict(ei.value.record.detail)
    assert d["item"] == 6
    assert ei.value.record.devices == ("M1",)
    assert rel_close(ei.value.record.margin, 0.3 / Oracle.tol_v(), 1e-9)


def test_small_reverse_within_tol_passes(ctx_bulk_out):
    """vsb = −0.02 (< tol_v 0.038) -> pass."""
    snap, _ = with_tol(ctx_bulk_out, theta_bulk(0.02))
    assert run(snap).status == "pass"
