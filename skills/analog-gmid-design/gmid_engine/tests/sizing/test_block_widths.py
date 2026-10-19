"""`dc_widths(snapshot, lut)` -- CONTRACT 5.7: MOS 마다 DeviceOp. vgs·vds·vsb = 노드전압 차의 크기(s = +1 nmos/−1 pmos),
op = op_point(노드 점), W = ID·L/exp(ln_idu), gm_id = op.gm_over_id, idu_forward = op.IDu, w_key = w_keys[kind].

기대값: toy LUT 닫힌 식(conftest Oracle) -- IDu = I0·exp(B·vgs + LAM·vds + vs항), gm/ID = B − C·vgs.
"""
import math

import pytest

from gmid_engine.sizing import DeviceOp, dc_widths

from .conftest import (W_KEY, Oracle, block_row, mos_table, node_voltages, rel_close, row_delta, run_blocks, run_of,
                       terminal_mag, theta_a, theta_c)


def check_ops(snap):
    V = node_voltages(snap)
    ops = dict(snap.column("device", "dc_op"))
    mt = mos_table(snap)
    assert set(ops) == set(mt)
    cur = dict(snap.column("device", "dc_current"))
    L = dict(snap.column("device", "dc_L"))
    ln = dict(snap.column("device", "dc_ln_idu"))
    for m, (kind, d, g, s, b) in mt.items():
        op = ops[m]
        assert isinstance(op, DeviceOp)
        vgs, vds, vsb = terminal_mag(kind, V, d, g, s, b)
        assert op.kind == kind and op.w_key == W_KEY
        assert abs(op.vgs - vgs) <= 1e-12 and abs(op.vds - vds) <= 1e-12 and abs(op.vsb - vsb) <= 1e-12
        assert op.current == cur[m] and op.L == L[m] and op.ln_idu == ln[m]
        assert rel_close(op.W, cur[m] * L[m] / math.exp(ln[m]), 1e-12)
        assert rel_close(op.idu_forward, math.exp(Oracle.ln_idu(kind, vgs, vds, vsb)), 1e-9)
        assert rel_close(op.gm_id, Oracle.gm_id(vgs), 1e-9)
        assert op.W > 0
    return ops


def test_circuit_c(ctx_c):
    th = theta_c()
    ops = check_ops(run_blocks(ctx_c[2], th))
    # 손계산: M1 vgs 0.6·vds 0.9·vsb 0, M2(pmos) vgs 0.7·vds 0.9·vsb 0; W = 1e-5·L/exp(x)
    assert abs(ops["M1"].vgs - 0.6) <= 1e-9 and abs(ops["M2"].vgs - 0.7) <= 1e-9
    assert abs(ops["M2"].vds - 0.9) <= 1e-12 and ops["M2"].vsb == 0.0
    assert rel_close(ops["M1"].W, 1e-5 * 1e-6 / math.exp(th[("ln_idu", "M1")]), 1e-12)
    assert rel_close(ops["M2"].W, 1e-5 * 2e-6 / math.exp(th[("ln_idu", "M2")]), 1e-12)
    # writer 는 forward IDu 가 좌표와 같다(toy LUT 의 VGS 축 로그선형 -> 역산 정확)
    assert rel_close(ops["M1"].idu_forward, math.exp(th[("ln_idu", "M1")]), 1e-9)


@pytest.mark.parametrize("i,r", [(1e-5, 9e4), (3e-6, 1e5)])
def test_circuit_a(ctx_a, i, r):
    ops = check_ops(run_blocks(ctx_a[2], theta_a(i=i, r=r)))
    assert abs(ops["M1"].vds - (1.8 - i * r)) <= 1e-12


def test_width_scales_with_current_only(ctx_c):
    a = dict(run_blocks(ctx_c[2], theta_c(i2=1e-5)).column("device", "dc_op"))
    b = dict(run_blocks(ctx_c[2], theta_c(i2=3e-5)).column("device", "dc_op"))
    for m in ("M1", "M2"):
        assert rel_close(b[m].W, 3 * a[m].W, 1e-12)
        assert (b[m].vgs, b[m].vds, b[m].gm_id) == (a[m].vgs, a[m].vds, a[m].gm_id)


def test_reads_no_unknown_fields(ctx_c):
    # oracle 대조: card B C4 판정 1·4 -- 실행 계수(C1) 행의 이 구간 증분 = 계산 1·재사용 1
    ctx = ctx_c[2]
    snap = run_blocks(ctx, theta_c(), upto="columns")
    before = block_row(ctx.counters, "dc_widths")
    out = dc_widths(snap, ctx.lut, **run_of(ctx))
    assert dc_widths(out, ctx.lut, **run_of(ctx)) is out
    assert row_delta(block_row(ctx.counters, "dc_widths"), before) == (2, 1, 0, 0, 1, 0)
