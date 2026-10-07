"""`op_point` -- CONTRACT 4.1 표·4.2·7절 [r5]: L 장에서 축별 보간 1회(ln ID: VGS·VDS Hermite, VS·L 선형; gm/ID = ln ID 의 VGS 미분;
ln GDS·VTH 모든 축 선형), IDu = exp(lnID)·L/w_m, gm_gds = gm/ID·exp(lnID − lnGDS), gds_per_w = exp(lnGDS)/w_m, vth.
격자점에서는 npz 원값과 일치. 단조 위반 칸은 그 축 선형(실패 없음). 없는 폭 KeyError.
"""
import math

import numpy as np
import pytest

from gmid_engine.lut import OpPoint, op_point

from .conftest import log_floor, rel_close


def test_contract_toy_row(toy_memo):
    """CONTRACT 7.1: (1e-6, 0.25, 0.5, 0) -> IDu = 1e-7·e^4.675, gm/ID 17, gds_per_w 1e-8·e^4.3/1e-6, gm_gds 170·e^0.375."""
    for wk in (100, 200):
        op = op_point(toy_memo, "nmos", wk, 1e-6, 0.25, 0.5, 0.0)
        assert isinstance(op, OpPoint)
        assert rel_close(op.IDu, 1e-7 * math.exp(4.675), 1e-12)
        assert rel_close(op.IDu, 1.072326e-5, 1e-6)
        assert rel_close(op.gm_over_id, 17.0, 1e-12)
        assert rel_close(op.gds_per_w, 1e-8 * math.exp(4.3) / 1e-6, 1e-12)
        assert rel_close(op.gds_per_w, 0.7369979, 1e-6)
        assert rel_close(op.gm_gds, 170.0 * math.exp(0.375), 1e-12)
        assert rel_close(op.gm_gds, 247.3485, 1e-6)
        assert op.vth == pytest.approx(0.4, abs=1e-15)
    a = op_point(toy_memo, "nmos", 100, 1e-6, 0.25, 0.5, 0.0)
    b = op_point(toy_memo, "nmos", 200, 1e-6, 0.25, 0.5, 0.0)
    for f in ("IDu", "gm_over_id", "gm_gds", "gds_per_w", "vth"):
        assert math.isclose(getattr(a, f), getattr(b, f), rel_tol=1e-14), f


def test_contract_toy_row_offgrid_vds_vs(toy_memo):
    """CONTRACT 7.1: (2e-6, 0.7, 0.8, 0.3) -> IDu = 4.543835e-3, gm/ID 11.6 (VDS Hermite·VS 선형도 정확)."""
    op = op_point(toy_memo, "nmos", 100, 2e-6, 0.7, 0.8, 0.3)
    ID = 0.5 * 1e-7 * math.exp(14 - 2.94 + 0.08) * 0.5 ** 0.6
    assert rel_close(op.IDu, ID * 2e-6 / 1e-6, 1e-12)
    assert rel_close(op.IDu, 4.543835e-3, 1e-6)
    assert rel_close(op.gm_over_id, 11.6, 1e-12)


def test_toy_grid_points(toy_memo):
    # L = 2e-6, VGS 1.0, VDS 1.0, VS 0.5: ID = (1/2)·1e-7·e^(14 + 0.1)·0.5 -> IDu = ID·L/w
    op = op_point(toy_memo, "nmos", 100, 2e-6, 1.0, 1.0, 0.5)
    ID = 0.5 * 1e-7 * math.exp(14.1) * 0.5
    assert rel_close(op.IDu, ID * 2.0, 1e-12)
    assert rel_close(op.gm_over_id, 8.0, 1e-12)
    assert rel_close(op.gm_gds, 80.0, 1e-12)
    assert rel_close(op.gds_per_w, ID * 0.1 / 1e-6, 1e-12)


def test_inputs_converted_with_float(toy_memo):
    a = op_point(toy_memo, "nmos", 100, 1e-6, 1, 1, 0)
    b = op_point(toy_memo, "nmos", 100, 1e-6, 1.0, 1.0, 0.0)
    assert a == b


@pytest.mark.parametrize("kind,wk", [("nmos", 150), ("nmos", 0), ("pmos", 100)])
def test_missing_slice_keyerror(toy_memo, kind, wk):
    with pytest.raises(KeyError):
        op_point(toy_memo, kind, wk, 1e-6, 0.25, 0.5, 0.0)


@pytest.mark.lut_realdata
def test_real_grid_points_equal_npz(real_memo, raw_slice):
    rng = np.random.default_rng(1)
    for kind, wk in (("nmos", 72), ("nmos", 1000), ("nmos", 1400), ("pmos", 84), ("pmos", 1000), ("pmos", 1400)):
        z = raw_slice(kind, wk)
        W = float(z["W"])
        n = 0
        while n < 30:
            iL, iG, k, s = (int(rng.integers(0, d)) for d in z["ID"].shape)
            I, G, D = (float(z[x][iL, iG, k, s]) for x in ("ID", "GM", "GDS"))
            if not (I > 0 and G > 0 and D > 0):
                continue
            L = float(z["L"][iL])
            op = op_point(real_memo, kind, wk, L, float(z["VGS"][iG]), float(z["VDS"][k]), float(z["VS"][s]))
            assert rel_close(op.IDu, I * L / W, 1e-12), (kind, wk, iL, iG, k, s)
            assert rel_close(op.gm_over_id, G / I, 1e-12)
            assert rel_close(op.gm_gds, G / D, 1e-12)
            assert rel_close(op.gds_per_w, D / W, 1e-12)
            assert op.vth == float(z["VTH"][iL, iG, k, s])
            n += 1


@pytest.mark.lut_realdata
def test_real_zero_current_point_uses_array_floor(real_memo, raw_slice):
    z = raw_slice("nmos", 1000)
    zeros = np.argwhere(z["ID"] <= 0)
    assert len(zeros) > 0, "전제: 0 이하 ID 격자점이 있어야 한다"
    _, floor = log_floor(z["ID"])
    iL, iG, k, s = (int(x) for x in zeros[len(zeros) // 2])
    L = float(z["L"][iL])
    op = op_point(real_memo, "nmos", 1000, L, float(z["VGS"][iG]), float(z["VDS"][k]), float(z["VS"][s]))
    assert rel_close(op.IDu, floor * L / float(z["W"]), 1e-12)
