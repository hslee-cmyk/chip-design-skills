"""`dc_tolerances(snapshot, lut)` -- CONTRACT 6절 tol 행: dc_tol_v = tol_v_table(kind, w_key).at(L, vds, "id_equivalent"),
dc_gm_bound = max(gm_id_curve(L, vds, vsb) 의 id·gm/id)·W/w_m.

기대값: toy LUT npz 배열에 lut 계약 5절 id_equivalent LOO 정의를 직접 적용(conftest `Oracle.tol_v`: VS 축 곡률 A·h² 를
gm/ID 최솟점으로 나눈 값 -- 모든 셀 같음), gm_bound 는 닫힌 식(VGS 격자 최대 1.8 V 의 GM).
"""
import math

import pytest

from gmid_engine.sizing import dc_tolerances

from .conftest import A, GMAX, Oracle, V0, mos_table, rel_close, run_blocks, theta_a, theta_c


def test_oracle_tol_hand_value():
    # 손계산: VS 간격 0.45 -> LOO 오차 A·h² = 0.10125, gm/ID 최소 = GMAX·exp(−1.8/V0)
    assert rel_close(Oracle.tol_v(), A * 0.45 ** 2 / (GMAX * math.exp(-1.8 / V0)), 1e-9)


@pytest.mark.parametrize("which", ["C", "A"])
def test_values(ctx_c, ctx_a, which):
    ctx, th = (ctx_c[2], theta_c()) if which == "C" else (ctx_a[2], theta_a())
    snap = run_blocks(ctx, th)
    out = dc_tolerances(snap, ctx.lut)
    tol = dict(out.column("device", "dc_tol_v"))
    gmb = dict(out.column("device", "dc_gm_bound"))
    mt = mos_table(snap)
    assert set(tol) == set(mt) == set(gmb)
    ops = dict(snap.column("device", "dc_op"))
    for m, (kind, *_rest) in mt.items():
        assert rel_close(tol[m], Oracle.tol_v(), 1e-9)
        op = ops[m]
        assert rel_close(gmb[m], Oracle.gm_bound(kind, op.L, op.vds, op.vsb, op.W), 1e-9)


def test_l_not_anchor_fails_before_tolerance(ctx_c):
    """L 이 앵커가 아니면 tol 셀에 닿기 전 좌표 역산에서 lut_query_failed(계속하지 않음)."""
    from gmid_engine.core import SealViolationError
    with pytest.raises(SealViolationError):
        run_blocks(ctx_c[2], theta_c(l1=1.7e-6))
