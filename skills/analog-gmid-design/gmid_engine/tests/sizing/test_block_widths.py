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


# ===============================================================================================================
# [card 20261104-hcs] S5 -- `device.dc_sat_v` = {MOS: SatBound}, writer = dc_op 와 같은 블록 dc_widths
# oracle (손) conftest 닫힌 식 `r4_vdsat_at`·`r4_tol_vdsat`(npz 열 직접) -- 동작점 좌표(L, vgs, vsb)는 같은 블록이 낸 dc_op 의 입력 칸.
# (식) card §2: 선언 없음·triode -> sat_threshold 값, off -> SatBound(None, None, "off_declared").
# ===============================================================================================================

def test_dc_sat_v_undeclared_devices_hold_the_lut_values_at_their_operating_points(ctx_r4c):
    from gmid_engine.lut import SatBound
    from .conftest import r4_tol_vdsat, r4_vdsat_at, theta_r4c
    snap = run_blocks(ctx_r4c, theta_r4c(), upto="widths")
    ops = dict(snap.column("device", "dc_op"))
    col = dict(snap.column("device", "dc_sat_v"))
    assert set(col) == set(ops) == {"M1", "M2"}
    for m, op in ops.items():
        sb = col[m]
        assert isinstance(sb, SatBound) and sb.reason is None
        assert rel_close(sb.vdsat_v, r4_vdsat_at(op.kind, op.L, op.vgs, op.vsb), 1e-12)
        assert rel_close(sb.tol_v, r4_tol_vdsat(op.kind), 1e-9)
        assert snap.field("device", m, "dc_sat_v").writer == snap.field("device", m, "dc_op").writer == "dc_widths"


def test_dc_sat_v_writer_is_dc_widths_in_the_authority_table():
    from gmid_engine.sizing import S2_WRITERS
    assert S2_WRITERS.writer_of("device", "dc_sat_v") == "dc_widths" == S2_WRITERS.writer_of("device", "dc_op")


def test_dc_sat_v_off_declared_has_reason_and_triode_has_the_lut_value(tmp_path):
    """한 회로: Moff(off 선언) + M1(triode 선언, V(out) = 0.18 < vdsat). off 만 사유 `off_declared`, triode 는 선언 없음과 같은 LUT 값."""
    from metrics.off_cases import build_case, circuit_a, off_entry, theta_from_schema, tri_entry
    from gmid_engine.lut import SatBound
    from .conftest import r4_tol_vdsat, r4_vdsat_at
    i, r = 1e-5, 1.62e5

    def th(ctx):
        return theta_from_schema(ctx, {"M1": ("nmos", 0.6, 1.8 - i * r, 0.0)}, {"R1": i, "M1": i}, {"R1": r})
    case = build_case(tmp_path, circuit_a([("Moff", "nmos", "out", "gnd", "gnd", "gnd")], name="hcs_s5"),
                      {"Moff": off_entry(), "M1": tri_entry()}, th)
    col = dict(case.ev.snapshot.column("device", "dc_sat_v"))
    op = dict(case.ev.snapshot.column("device", "dc_op"))["M1"]
    assert set(col) == {"M1", "Moff"}
    assert col["Moff"] == SatBound(None, None, "off_declared")
    assert col["M1"].reason is None
    assert rel_close(col["M1"].vdsat_v, r4_vdsat_at("nmos", op.L, op.vgs, op.vsb), 1e-12)
    assert rel_close(col["M1"].tol_v, r4_tol_vdsat("nmos"), 1e-9)
