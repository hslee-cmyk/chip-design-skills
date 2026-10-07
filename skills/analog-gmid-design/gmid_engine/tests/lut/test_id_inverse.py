"""`gm_id_for_target` -- CONTRACT 4절: Q = id_vals·W/w_m(current) 또는 id_vals·gm_id_vals·W/w_m(gm),
분지 index p 부터 Q 가 엄격히 증가하는 첫 구간 [p, e] 에서 ln Q 를 VGS 에 대해 선형으로 풀어 vgs.
gm_id = op_point(vgs).gm_over_id, id_a = IDu·W/L, gm_s = gm_id·id_a. 범위 밖 / 단조 구간 밖 실패, 인자 오류 ValueError.
"""
import math

import numpy as np
import pytest

from gmid_engine.core import SealViolationError
from gmid_engine.lut import TargetSolution, gm_id_for_target

from .conftest import detail_of, interp4, log_floor, rel_close


def _solve(m, **kw):
    return gm_id_for_target(m, "nmos", 100, 1e-6, 0.5, 0.0, **kw)


def test_contract_toy_row(toy_memo):
    r = _solve(toy_memo, W=2e-6, current=2e-6)
    assert isinstance(r, TargetSolution)
    assert rel_close(r.vgs, 0.5, 1e-12)
    assert rel_close(r.gm_id, 10.0, 1e-12)
    assert rel_close(r.id_a, 2e-6, 1e-12)
    assert rel_close(r.gm_s, 2e-5, 1e-12)


def test_toy_current_log_linear_midpoint(toy_memo):
    t = math.sqrt(2e-7 * 2e-6)                     # Q = (2e-7, 2e-6, 2e-5) 의 [0,1] 기하 중점 -> VGS 0.25
    r = _solve(toy_memo, W=2e-6, current=t)
    assert rel_close(r.vgs, 0.25, 1e-12)
    assert rel_close(r.gm_id, math.sqrt(200.0), 1e-12)
    assert rel_close(r.id_a, t, 1e-12)
    assert rel_close(r.gm_s, r.gm_id * r.id_a, 1e-15)


def test_toy_gm_target(toy_memo):
    # gm: Q = ID·gm/ID·W/w = (4e-6, 2e-5, 8e-5)
    r = _solve(toy_memo, W=2e-6, gm=2e-5)
    assert rel_close(r.vgs, 0.5, 1e-12) and rel_close(r.gm_s, 2e-5, 1e-12)
    t = math.sqrt(2e-5 * 8e-5)
    r = _solve(toy_memo, W=2e-6, gm=t)
    assert rel_close(r.vgs, 0.75, 1e-12)
    assert rel_close(r.gm_s, t, 1e-12)


@pytest.mark.parametrize("kw,quantity", [
    (dict(W=2e-6, current=1e-4), "current"),
    (dict(W=2e-6, current=1e-7), "current"),
    (dict(W=2e-6, gm=1.0), "gm"),
])
def test_out_of_range(toy_memo, kw, quantity):
    with pytest.raises(SealViolationError) as ei:
        _solve(toy_memo, **kw)
    det = detail_of(ei.value)
    assert det["reason"] == "lut_target_out_of_range"
    for key in ("quantity", "target", "W", "L", "vds", "vsb", "kind", "w_key", "branch_min", "branch_max",
                "monotone_lo", "monotone_hi"):
        assert key in det, key
    assert det["quantity"] == quantity
    if quantity == "current":
        assert rel_close(det["branch_min"], 2e-7, 1e-12) and rel_close(det["branch_max"], 2e-5, 1e-12)


@pytest.mark.parametrize("kw", [
    dict(W=1e-6),
    dict(W=1e-6, gm=1e-5, current=1e-6),
    dict(W=0.0, current=1e-6),
    dict(W=-1e-6, current=1e-6),
])
def test_bad_arguments_valueerror(toy_memo, kw):
    with pytest.raises(ValueError) as ei:
        _solve(toy_memo, **kw)
    assert not isinstance(ei.value, SealViolationError)


def test_non_monotonic_vs_out_of_range(curve_lut):
    # 정점 index 0, Q(current, W = w) = (1e-7, 1e-6, 5e-8): 단조 구간 [0, 1], 분지 범위 [5e-8, 1e-6]
    memo, _ = curve_lut((0.0, 0.5, 1.0), (1e-7, 1e-6, 5e-8), (20.0, 10.0, 4.0))
    with pytest.raises(SealViolationError) as ei:
        gm_id_for_target(memo, "nmos", 100, 1e-6, 0.5, 0.0, W=1e-6, current=7e-8)
    det = detail_of(ei.value)
    assert det["reason"] == "lut_target_non_monotonic"
    assert rel_close(det["monotone_lo"], 1e-7, 1e-12) and rel_close(det["monotone_hi"], 1e-6, 1e-12)
    assert rel_close(det["branch_min"], 5e-8, 1e-12) and rel_close(det["branch_max"], 1e-6, 1e-12)
    for t in (3e-8, 2e-6):
        with pytest.raises(SealViolationError) as ei:
            gm_id_for_target(memo, "nmos", 100, 1e-6, 0.5, 0.0, W=1e-6, current=t)
        assert detail_of(ei.value)["reason"] == "lut_target_out_of_range"
    # 단조 구간 안 목표는 푼다
    r = gm_id_for_target(memo, "nmos", 100, 1e-6, 0.5, 0.0, W=1e-6, current=math.sqrt(1e-13))
    assert rel_close(r.vgs, 0.25, 1e-12)


def test_root_memo_region(toy_memo):
    a = _solve(toy_memo, W=2e-6, current=2e-6)
    b = _solve(toy_memo, W=2e-6, current=2e-6)
    assert a is b
    st = dict(toy_memo.stats())["root"]
    assert st.misses == 1 and st.hits == 1


@pytest.mark.lut_realdata
@pytest.mark.parametrize("quantity", ["current", "gm"])
def test_real_round_trip(real_memo, raw_slice, quantity):
    rng = np.random.default_rng(21 if quantity == "current" else 22)
    for kind, wk in (("nmos", 1000), ("pmos", 84)):
        z = raw_slice(kind, wk)
        grids = (z["L"], z["VGS"], z["VDS"], z["VS"])
        lI, lG = log_floor(z["ID"])[0], log_floor(z["GM"])[0]
        w = float(z["W"])
        VGS = z["VGS"]
        done = 0
        while done < 8:
            iL, k, s = int(rng.integers(0, 12)), int(rng.integers(4, 49)), int(rng.integers(0, 10))
            I, G = z["ID"][iL, :, k, s], z["GM"][iL, :, k, s]
            if not (np.all(I > 0) and np.all(G > 0)):
                continue
            g = np.exp(lG[iL, :, k, s] - lI[iL, :, k, s])
            p = int(np.argmax(g))
            W = float(rng.uniform(0.5e-6, 20e-6))
            lnQ = (lI[iL, :, k, s] if quantity == "current" else lG[iL, :, k, s]) + math.log(W / w)
            e = p
            while e + 1 < len(lnQ) and math.exp(lnQ[e + 1]) > math.exp(lnQ[e]):
                e += 1
            if e == p:
                continue
            j = int(rng.integers(p, e))
            lt = 0.5 * (lnQ[j] + lnQ[j + 1])
            t = math.exp(lt)
            vgs_hand = VGS[j] + (lt - lnQ[j]) / (lnQ[j + 1] - lnQ[j]) * (VGS[j + 1] - VGS[j])
            L, vds, vsb = float(z["L"][iL]), float(z["VDS"][k]), float(z["VS"][s])
            r = gm_id_for_target(real_memo, kind, wk, L, vds, vsb, W=W, **{quantity: t})
            assert abs(r.vgs - vgs_hand) <= 1e-9, (kind, wk, iL, k, s, j)
            pt = (L, r.vgs, vds, vsb)
            li, lg = interp4(grids, lI, pt), interp4(grids, lG, pt)
            assert rel_close(r.gm_id, math.exp(lg - li), 1e-9)
            assert rel_close(r.id_a, math.exp(li) * W / w, 1e-9)
            got = r.id_a if quantity == "current" else r.gm_s
            assert rel_close(got, t, 1e-9), "왕복: 목표 %s 로 되돌아오지 않는다" % quantity
            done += 1
