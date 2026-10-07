"""`gmb` -- CONTRACT 4절: VS 칸 k = min(bisect_right(VS, vsb) − 1, len(VS) − 2),
gmb = −exp(lnID(점)) · (lnID(VS[k+1]) − lnID(VS[k])) / (VS[k+1] − VS[k]), 폭 w_m 기준.
"""
import bisect
import math

import numpy as np
import pytest

from gmid_engine.lut import gmb

from .conftest import TOY_L, TOY_VDS, TOY_VGS, TOY_VS, interp4, log_floor, rel_close, toy_slice_arrays


def test_contract_toy_row(toy_memo):
    v = gmb(toy_memo, "nmos", 100, 1e-6, 0.5, 0.5, 0.25)
    hand = -math.sqrt(1e-6 * 5e-7) * math.log(0.5) / 0.5
    assert rel_close(v, 9.80258e-7, 1e-5)
    assert rel_close(v, hand, 1e-12)


def test_toy_width_scaling_and_upper_vs_edge(toy_memo):
    # 폭 200 슬라이스는 ID 2 배 -> gmb 2 배(폭 w_m 기준 값)
    assert rel_close(gmb(toy_memo, "nmos", 200, 1e-6, 0.5, 0.5, 0.25),
                     2 * gmb(toy_memo, "nmos", 100, 1e-6, 0.5, 0.5, 0.25), 1e-12)
    # vsb = VS 끝값 0.5: k = len(VS) − 2 = 0, ID(점) = 5e-7
    v = gmb(toy_memo, "nmos", 100, 1e-6, 0.5, 0.5, 0.5)
    assert rel_close(v, -5e-7 * math.log(0.5) / 0.5, 1e-12)


def test_toy_offgrid_other_axes(toy_memo):
    a = toy_slice_arrays(1e-6)
    lI = log_floor(a["ID"])[0]
    grids = (TOY_L, TOY_VGS, TOY_VDS, TOY_VS)
    L, vgs, vds, vsb = 1.6e-6, 0.7, 0.8, 0.1
    d = (interp4(grids, lI, (L, vgs, vds, 0.5)) - interp4(grids, lI, (L, vgs, vds, 0.0))) / 0.5
    hand = -math.exp(interp4(grids, lI, (L, vgs, vds, vsb))) * d
    assert rel_close(gmb(toy_memo, "nmos", 100, L, vgs, vds, vsb), hand, 1e-12)


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
