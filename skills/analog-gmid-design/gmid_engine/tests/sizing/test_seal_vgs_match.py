"""봉인 2 `dc_seal_vgs_match(snapshot)` -- CONTRACT 6절: MOS 마다 |ln idu_forward − ln_idu| / gm_id ≤ tol_v (dc_op.idu_forward
를 읽는다, 11절 6). judge 규칙은 conftest `judge_expect`."""
import dataclasses
import math

import pytest

from gmid_engine.sizing import dc_seal_vgs_match

from .conftest import assert_item, judge_expect, rel_close, seal_item, tamper, theta_a, theta_c, with_tol


def rows_of(snap):
    ops = dict(snap.column("device", "dc_op"))
    tolv = dict(snap.column("device", "dc_tol_v"))
    ln = dict(snap.column("device", "dc_ln_idu"))
    return [(m, abs(math.log(ops[m].idu_forward) - ln[m]) / ops[m].gm_id, tolv[m], (m,), ())
            for m in sorted(ops)]


def run(snap):
    return seal_item(dc_seal_vgs_match(snap), 2)


def scale_idu(snap, m, k):
    op = dict(snap.column("device", "dc_op"))[m]
    return tamper(snap, "dc_widths", "device", "dc_op", {m: dataclasses.replace(op, idu_forward=op.idu_forward * k)})


@pytest.mark.parametrize("which", ["C", "A"])
def test_pass(ctx_c, ctx_a, which):
    ctx, th = (ctx_c[2], theta_c()) if which == "C" else (ctx_a[2], theta_a())
    snap, _ = with_tol(ctx, th)
    exp = judge_expect(rows_of(snap))
    assert exp["status"] == "pass"
    assert_item(run(snap), exp, 2, atol=1e-12)


def test_fail_hand(ctx_c):
    snap, _ = with_tol(ctx_c[2], theta_c())
    bad = scale_idu(snap, "M1", 2.0)
    item = run(bad)
    exp = judge_expect(rows_of(bad))
    assert exp["status"] == "fail" and exp["devices"] == ("M1",)
    assert_item(item, exp, 2)
    gm = dict(snap.column("device", "dc_op"))["M1"].gm_id
    assert rel_close(item.magnitude, math.log(2.0) / gm, 1e-9)        # 손계산 ln2 / (gm/ID)


def test_within_tol_passes(ctx_c):
    snap, _ = with_tol(ctx_c[2], theta_c())
    gm = dict(snap.column("device", "dc_op"))["M1"].gm_id
    tol = dict(snap.column("device", "dc_tol_v"))["M1"]
    ok = scale_idu(snap, "M1", math.exp(0.9 * tol * gm))              # 0.9·tol
    assert run(ok).status == "pass"
    bad = scale_idu(snap, "M1", math.exp(1.1 * tol * gm))             # 1.1·tol
    assert run(bad).status == "fail"


def test_undefined_when_tol_none(ctx_c):
    snap, _ = with_tol(ctx_c[2], theta_c())
    s2 = tamper(snap, "dc_tolerances", "device", "dc_tol_v", {"M2": None})
    exp = judge_expect(rows_of(s2))
    assert exp["status"] == "undefined" and exp["devices"] == ("M2",)
    assert_item(run(s2), exp, 2)


def test_two_fails_worst_is_max_margin(ctx_c):
    snap, _ = with_tol(ctx_c[2], theta_c())
    bad = scale_idu(scale_idu(snap, "M1", 2.0), "M2", 20.0)
    exp = judge_expect(rows_of(bad))
    assert exp["devices"] == ("M1", "M2")
    assert_item(run(bad), exp, 2)
    assert dict(run(bad).detail)["worst"] == "M2"
