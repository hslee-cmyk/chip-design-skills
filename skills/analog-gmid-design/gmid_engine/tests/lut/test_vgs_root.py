"""`vgs_for_gm_id` -- CONTRACT 3절·4절: gm_id_curve 격자 gm/ID 에서 분지(정점 이상) 가장 오른쪽 구간 선형 역보간,
해 없음 -> SealViolationError(lut_no_strong_inversion_root).

누설 분지 결함 회귀: 옛 엔진(로그 바닥 1e-18·1e-30 + 전 구간 가장 오른쪽 구간)이 정점 왼쪽 누설 분지 해를 내던 실제 사례를
npz 에서 골라 고정한다(tol_v_measurement.md 의 분지 점프 사례와 같은 곡선: pmos L 1 µm, VDS 0.525 V, VS 0.4 V).
"""
import math

import numpy as np
import pytest

from gmid_engine.core import SealViolationError
from gmid_engine.lut import vgs_for_gm_id

from .conftest import branch_solve_vgs, detail_of, interp4, legacy_solve_vgs, lin_interp, log_floor, rel_close


def test_contract_toy_rows(toy_memo):
    assert rel_close(vgs_for_gm_id(toy_memo, "nmos", 100, 15.0, 1e-6, 0.5, 0.0), 0.25, 1e-12)
    with pytest.raises(SealViolationError) as ei:
        vgs_for_gm_id(toy_memo, "nmos", 100, 25.0, 1e-6, 0.5, 0.0)
    det = detail_of(ei.value)
    assert det["reason"] == "lut_no_strong_inversion_root"
    assert det["peak_vgs"] == 0.0
    assert det["gm_id"] == 25.0 and det["L"] == 1e-6 and det["vds"] == 0.5 and det["vsb"] == 0.0
    assert det["kind"] == "nmos" and det["w_key"] == 100
    assert rel_close(det["branch_gm_id_max"], 20.0, 1e-12) and rel_close(det["branch_gm_id_min"], 4.0, 1e-12)


def test_toy_round_trip_and_below_branch(toy_memo):
    for t in (19.0, 12.5, 10.0, 7.0, 4.5):
        v = vgs_for_gm_id(toy_memo, "nmos", 100, t, 2e-6, 0.7, 0.3)
        assert rel_close(lin_interp((0.0, 0.5, 1.0), (20.0, 10.0, 4.0), v), t, 1e-12)
    with pytest.raises(SealViolationError):
        vgs_for_gm_id(toy_memo, "nmos", 100, 3.9, 1e-6, 0.5, 0.0)


def test_missing_width_keyerror(toy_memo):
    with pytest.raises(KeyError):
        vgs_for_gm_id(toy_memo, "nmos", 300, 15.0, 1e-6, 0.5, 0.0)


# ---------------------------------------------------------------------------
# 실데이터
# ---------------------------------------------------------------------------

LEAK = dict(kind="pmos", w_key=1000, L=1e-6, vds=0.525, vsb=0.4, target=2.0)


def _grid_index(axis, x):
    i = int(np.argmin(np.abs(axis - x)))
    assert math.isclose(axis[i], x, rel_tol=1e-9)
    return i


def _curves(z, iL, k, s):
    I, G = z["ID"][iL, :, k, s], z["GM"][iL, :, k, s]
    g_old = np.exp(np.log(np.clip(G, 1e-30, None)) - np.log(np.clip(I, 1e-18, None)))      # 옛 바닥
    lI, _ = log_floor(z["ID"])
    lG, _ = log_floor(z["GM"])
    g_new = np.exp(lG[iL, :, k, s] - lI[iL, :, k, s])                                     # 계약 1.4 바닥
    return g_old, g_new


@pytest.mark.lut_realdata
def test_leak_branch_regression_real(real_memo, raw_slice, raw_cap):
    z = raw_slice(LEAK["kind"], LEAK["w_key"])
    iL, k, s = _grid_index(z["L"], LEAK["L"]), _grid_index(z["VDS"], LEAK["vds"]), _grid_index(z["VS"], LEAK["vsb"])
    L, vds, vsb = float(z["L"][iL]), float(z["VDS"][k]), float(z["VS"][s])
    VGS = z["VGS"]
    g_old, g_new = _curves(z, iL, k, s)
    t = LEAK["target"]
    # 전제 1: 옛 엔진은 이 목표에서 정점 왼쪽(누설 분지) 해를 ValueError 없이 낸다
    old = legacy_solve_vgs(g_old, VGS, t)
    p_new = int(np.argmax(g_new))
    assert old < 0.2 and old < VGS[int(np.argmax(g_old))], old
    # 같은 곡선이 기준 LUT(옛 엔진 입력, VS 0.4 = index 2)에서도 같은 결함을 보인다
    Ir, Gr = raw_cap["ID_p"][iL, :, k, 2], raw_cap["GM_p"][iL, :, k, 2]
    g_ref_old = np.exp(np.log(np.clip(Gr, 1e-30, None)) - np.log(np.clip(Ir, 1e-18, None)))
    assert legacy_solve_vgs(g_ref_old, VGS, t) < 0.2
    # 전제 2: 정본 분지(정점 이상)에는 해가 없다
    assert branch_solve_vgs(g_new, VGS, t) is None
    assert t < g_new[p_new:].min()
    with pytest.raises(SealViolationError) as ei:
        vgs_for_gm_id(real_memo, LEAK["kind"], LEAK["w_key"], t, L, vds, vsb)
    det = detail_of(ei.value)
    assert det["reason"] == "lut_no_strong_inversion_root"
    assert det["peak_vgs"] == float(VGS[p_new])
    assert rel_close(det["branch_gm_id_min"], float(g_new[p_new:].min()), 1e-12)
    assert rel_close(det["branch_gm_id_max"], float(g_new[p_new:].max()), 1e-12)
    assert (det["kind"], det["w_key"], det["gm_id"]) == ("pmos", 1000, t)


@pytest.mark.lut_realdata
def test_legacy_bitwise_equal_when_legacy_root_in_branch_real(real_memo, raw_slice):
    z = raw_slice(LEAK["kind"], LEAK["w_key"])
    iL, k, s = _grid_index(z["L"], LEAK["L"]), _grid_index(z["VDS"], LEAK["vds"]), _grid_index(z["VS"], LEAK["vsb"])
    VGS = z["VGS"]
    g_old, g_new = _curves(z, iL, k, s)
    p = int(np.argmax(g_new))
    assert np.array_equal(g_old[p + 4:], g_new[p + 4:])    # 바닥 차이는 VGS ≈ 0 몇 점뿐
    n = 0
    for t in np.linspace(2.5, 30.0, 23):
        old = legacy_solve_vgs(g_old, VGS, float(t))
        if old > VGS[p + 4]:
            got = vgs_for_gm_id(real_memo, "pmos", 1000, float(t), float(z["L"][iL]), float(z["VDS"][k]), float(z["VS"][s]))
            assert got == old, t
            n += 1
    assert n >= 15


@pytest.mark.lut_realdata
def test_round_trip_against_independent_linear_interp(real_memo, raw_slice):
    """vgs_for_gm_id 결과를 npz 원자료의 단순 선형 보간으로 되돌리면 목표 gm/ID 가 나온다
    ([r2] L 은 앵커만, VDS·VS 는 격자점과 칸 안 모두)."""
    rng = np.random.default_rng(5)
    for kind, wk in (("nmos", 72), ("nmos", 1000), ("pmos", 1000), ("pmos", 1400)):
        z = raw_slice(kind, wk)
        lI, _ = log_floor(z["ID"])
        lG, _ = log_floor(z["GM"])
        grids = (z["L"], z["VGS"], z["VDS"], z["VS"])
        VGS = [float(v) for v in z["VGS"]]
        done = 0
        while done < 10:
            iL, k, s = int(rng.integers(0, 12)), int(rng.integers(4, 48)), int(rng.integers(0, 9))
            off_grid = done % 2 == 1
            L = float(z["L"][iL])
            vds, vsb = float(z["VDS"][k]), float(z["VS"][s])
            if off_grid:
                vds = float(z["VDS"][k] + 0.37 * (z["VDS"][k + 1] - z["VDS"][k]))
                vsb = float(z["VS"][s] + 0.61 * (z["VS"][s + 1] - z["VS"][s]))
            # 독립 곡선: VGS 격자마다 4축 다중선형(로그공간) -> gm/ID
            g = np.array([math.exp(interp4(grids, lG, (L, v, vds, vsb)) - interp4(grids, lI, (L, v, vds, vsb)))
                          for v in VGS])
            p = int(np.argmax(g))
            lo, hi = float(g[p:].min()), float(g[p])
            if hi - lo < 1.0:
                continue
            t = float(rng.uniform(lo + 0.05 * (hi - lo), hi - 0.05 * (hi - lo)))
            v = vgs_for_gm_id(real_memo, kind, wk, t, L, vds, vsb)
            assert v >= VGS[p]
            assert rel_close(lin_interp(VGS, g, v), t, 1e-9), (kind, wk, L, vds, vsb, t, v)
            exp_v = branch_solve_vgs(g, VGS, t)
            assert abs(v - exp_v) <= 1e-9
            done += 1
