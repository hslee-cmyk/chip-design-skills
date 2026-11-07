"""helper `_helpers_lut`(`terminal_voltages`·소자 슬라이스·`with_device`·`forward_point`·`tol_v_cell`) -- CONTRACT 5.4·5.7·6절.
helper 는 비공개라 공개 블록 결과로 확인한다:
- terminal_voltages: s = +1(nmos)/−1(pmos), vgs = s(V(g)−V(s)), vds = s(V(d)−V(s)), vsb = s(V(s)−V(b)).
- 소자 슬라이스(WB-1): DeviceOp.w_key = 그 소자 dc_finger 의 슬라이스 키(round(w_f_m / grid)).
- forward_point: idu_forward = op_point(노드 점).IDu (toy 닫힌 식).
- tol_v_cell: dc_tol_v = tol_v_table(kind, w_key).at(L, vds, "id_equivalent").
- with_device: LUT 실패를 SealViolationError(devices = 소자, reason lut_query_failed, lut_reason, device_query)로 감싼다.
"""
import math

import pytest

from gmid_engine.core import SealViolationError
from gmid_engine.lut import LutMemo, op_point, tol_v_table
from gmid_engine.sizing import LutAccess

from .conftest import (Oracle, W_KEY, build_ctx, circuit_cs_pmos_load, mos_table, new_access, node_voltages,
                       rel_close, run_blocks, theta_c, with_tol)


def test_terminal_voltage_signs(ctx_c):
    snap = run_blocks(ctx_c[2], theta_c(y=0.3))
    V = node_voltages(snap)
    ops = dict(snap.column("device", "dc_op"))
    # M1 nmos d=out g=in s=gnd b=gnd
    assert ops["M1"].vgs == V["in"] - V["gnd"] and ops["M1"].vds == V["out"] - V["gnd"]
    assert ops["M1"].vsb == V["gnd"] - V["gnd"]
    # M2 pmos d=out g=pb s=vdd b=vdd -> 부호 반전 크기
    assert ops["M2"].vgs == -(V["pb"] - V["vdd"]) and ops["M2"].vds == -(V["out"] - V["vdd"])
    assert ops["M2"].vgs > 0 and ops["M2"].vds > 0


def test_w_key_and_forward_point_match_lut(ctx_c):
    ctx = ctx_c[2]
    snap = run_blocks(ctx, theta_c())
    fing = dict(snap.column("device", "dc_finger"))
    for m, op in dict(snap.column("device", "dc_op")).items():
        # toy LUT 는 슬라이스가 하나(키 100)라 후보가 하나: DeviceOp.w_key 와 dc_finger 가 같은 슬라이스를 가리킨다
        assert op.w_key == W_KEY and fing[m].m == op.W / (W_KEY * 1e-8) and fing[m].residual == 0.0      # [FS-1 §4.2] 탐색 dc_finger = (W/w_f, 0.0)
        direct = op_point(ctx.lut.memo, op.kind, op.w_key, op.L, op.vgs, op.vds, op.vsb)
        assert op.idu_forward == direct.IDu and op.gm_id == direct.gm_over_id
        assert rel_close(op.idu_forward, math.exp(Oracle.ln_idu(op.kind, op.vgs, op.vds, op.vsb)), 1e-9)


def test_tol_v_cell_is_table_at(ctx_c):
    ctx = ctx_c[2]
    snap, _ = with_tol(ctx, theta_c())
    tolv = dict(snap.column("device", "dc_tol_v"))
    for m, op in dict(snap.column("device", "dc_op")).items():
        t = tol_v_table(ctx.lut.memo, op.kind, op.w_key).at(op.L, op.vds, "id_equivalent")
        assert tolv[m] == t
        assert rel_close(t, Oracle.tol_v(), 1e-9)


def test_lut_failure_wrapped_with_device(ctx_c):
    with pytest.raises(SealViolationError) as ei:
        run_blocks(ctx_c[2], theta_c(x2=Oracle.ln_idu("pmos", -0.5, 0.9, 0.0)))   # VGS < 0 -> 목표 밖
    d = dict(ei.value.record.detail)
    assert ei.value.record.devices == ("M2",)
    assert d["reason"] == "lut_query_failed"
    assert d["lut_reason"] in ("lut_target_out_of_range", "lut_target_non_monotonic")
    assert d["device_query"] == "vgs_of_coordinate"


def test_toy_lut_is_hermite_consistent(toy_lut):
    """입력 전제(lut r5 1.4·7절): toy 의 GM/ID·GDS/ID 가 ln ID 기울기와 맞아 Fritsch–Carlson 위반 칸 0 -- 위반 칸이 있으면
    역산이 거부돼 이 폴더의 닫힌 식 기대값이 성립하지 않는다."""
    from .conftest import TOY_L, TOY_VDS, TOY_VGS, TOY_VS
    n_vgs = len(TOY_L) * (len(TOY_VGS) - 1) * len(TOY_VDS) * len(TOY_VS)
    n_vds = len(TOY_L) * len(TOY_VGS) * (len(TOY_VDS) - 1) * len(TOY_VS)
    for sl in toy_lut.slice_map.values():
        # [r7] lut 1.4: hermite_fc 세 번째 항 ("VS", Hermite 칸 수, 위반 수) -- 이 toy 는 GMBS 열이 없어 VS Hermite 칸 0
        assert {a: (n, v) for a, n, v in sl.hermite_fc} == {"VDS": (n_vds, 0), "VGS": (n_vgs, 0), "VS": (0, 0)}
