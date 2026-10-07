"""`gmb` -- CONTRACT 4.1 표 [r5]: VS 칸 k = min(bisect_right(VS, vsb) − 1, len(VS) − 2),
gmb = −ID(점) · (ln IDu(VS[k+1]) − ln IDu(VS[k])) / (VS[k+1] − VS[k]), 세 값 모두 같은 (L, vgs, vds) 의 op_point(4.2 보간),
ID(점) = IDu·w_m/L. 폭 w_m 기준.
"""
import bisect
import math

import numpy as np
import pytest

from gmid_engine.lut import gmb

from .conftest import TOY_L, RefSlice, anchor_w, log_floor, r5_toy_lnid, rel_close, toy_slice_arrays


def test_contract_toy_row(toy_memo):
    v = gmb(toy_memo, "nmos", 100, 1e-6, 0.5, 0.5, 0.25)
    ID = 1e-7 * math.exp(8.55) * math.sqrt(0.5)
    hand = -ID * math.log(0.5) / 0.5
    assert rel_close(v, 5.064753e-4, 1e-6)
    assert rel_close(v, hand, 1e-12)


def test_toy_width_scaling_and_upper_vs_edge(toy_memo):
    # 폭 200 슬라이스는 ID 2 배 -> gmb 2 배(폭 w_m 기준 값)
    assert rel_close(gmb(toy_memo, "nmos", 200, 1e-6, 0.5, 0.5, 0.25),
                     2 * gmb(toy_memo, "nmos", 100, 1e-6, 0.5, 0.5, 0.25), 1e-12)
    # vsb = VS 끝값 0.5: k = len(VS) − 2 = 0, ID(점) = 0.5·1e-7·e^8.55
    v = gmb(toy_memo, "nmos", 100, 1e-6, 0.5, 0.5, 0.5)
    assert rel_close(v, -0.5 * 1e-7 * math.exp(8.55) * math.log(0.5) / 0.5, 1e-12)


@pytest.mark.parametrize("pt", [(2e-6, 0.7, 0.8, 0.1), (3e-6, 0.31, 0.66, 0.42), (1e-6, 0.95, 0.55, 0.0)])
def test_toy_offgrid_other_axes(toy_memo, pt):
    """[r5] VGS·VDS 격자 밖: ln ID 는 4.2 Hermite(r5 toy 에서 닫힌 식과 같다), VS 방향 기울기 = ln(0.5)/0.5."""
    L, vgs, vds, vsb = pt
    ID = math.exp(r5_toy_lnid(vgs, vds, vsb, L))
    hand = -ID * math.log(0.5) / 0.5
    assert rel_close(gmb(toy_memo, "nmos", 100, *pt), hand, 1e-12)
    # 독립 Hermite 구현으로 같은 식
    rs = RefSlice(toy_slice_arrays(1e-6))
    Lw = anchor_w(TOY_L.index(L))
    l0 = rs.op(Lw, L, vgs, vds, 0.0)["lnID"]
    l1 = rs.op(Lw, L, vgs, vds, 0.5)["lnID"]
    idp = math.exp(rs.op(Lw, L, vgs, vds, vsb)["lnID"])
    assert rel_close(gmb(toy_memo, "nmos", 100, *pt), -idp * (l1 - l0) / 0.5, 1e-12)


@pytest.mark.lut_realdata
def test_real_grid_points(real_memo, raw_slice):
    rng = np.random.default_rng(3)
    for kind, wk in (("nmos", 1000), ("pmos", 84)):
        z = raw_slice(kind, wk)
        VS = [float(x) for x in z["VS"]]
        lI = log_floor(z["ID"])[0]
        n = 0
        while n < 20:
            iL, iG, k, s = int(rng.integers(0, 12)), int(rng.integers(10, 49)), int(rng.integers(1, 49)), int(rng.integers(0, 10))
            if not np.all(z["ID"][iL, iG, k, :] > 0):
                continue
            vsb = VS[s]
            kk = min(bisect.bisect_right(VS, vsb) - 1, len(VS) - 2)
            hand = -float(z["ID"][iL, iG, k, s]) * (lI[iL, iG, k, kk + 1] - lI[iL, iG, k, kk]) / (VS[kk + 1] - VS[kk])
            got = gmb(real_memo, kind, wk, float(z["L"][iL]), float(z["VGS"][iG]), float(z["VDS"][k]), vsb)
            assert rel_close(got, hand, 1e-10), (kind, wk, iL, iG, k, s)
            n += 1


@pytest.mark.lut_realdata
def test_real_offgrid_matches_independent_hermite(real_memo, raw_slice):
    rng = np.random.default_rng(31)
    z = raw_slice("nmos", 1000)
    rs = RefSlice(z)
    VS = list(rs.grids[3])
    n = 0
    while n < 15:
        iL = int(rng.integers(0, 12))
        vgs, vds, vsb = float(rng.uniform(0.6, 1.79)), float(rng.uniform(0.1, 1.79)), float(rng.uniform(0, 1.79))
        L = rs.grids[0][iL]
        kk = min(bisect.bisect_right(VS, vsb) - 1, len(VS) - 2)
        Lw = anchor_w(iL)
        l0, l1 = rs.op(Lw, L, vgs, vds, VS[kk])["lnID"], rs.op(Lw, L, vgs, vds, VS[kk + 1])["lnID"]
        idp = math.exp(rs.op(Lw, L, vgs, vds, vsb)["lnID"])
        hand = -idp * (l1 - l0) / (VS[kk + 1] - VS[kk])
        assert rel_close(gmb(real_memo, "nmos", 1000, L, vgs, vds, vsb), hand, 1e-9)
        n += 1
