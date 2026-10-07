"""CONTRACT 3.7: solve_point -- ω > 0 은 모든 열 풀이 + 사후 오차 errors[j], ω = 0 은 DC 극한, 영 피벗이면 NaN + singular_mna."""
import math

import numpy as np
import pytest

from gmid_engine.metrics import (
    Capacitor,
    Excitation,
    PointSolution,
    Resistor,
    Sense,
    SmallSignalCircuit,
    build_mna,
    solve_point,
)

from .conftest import EX3, STAMP_FUNCS, closed_miller, codes, count_calls, ex1_rc, ex2d_sc_loop, ex3_miller, mos_t, ref_solve


@pytest.mark.parametrize("w", [1e2, 1e6, 3.3e7, 1e10])
def test_rc_point(w):
    p = solve_point(ex1_rc(), w)
    assert isinstance(p, PointSolution)
    assert p.omega == w
    assert np.asarray(p.values)[0, 0] == pytest.approx(1.0 / (1.0 + 1j * w * 1e-6), rel=1e-12)
    e = np.asarray(p.errors)
    assert e.shape == (1, 1) and np.all(np.isfinite(e)) and np.all(e >= 0.0)     # (관측 행, 열)
    assert e[0, 0] <= 1e-12 * abs(np.asarray(p.values)[0, 0])
    assert p.undefined == ()


@pytest.mark.parametrize("w", [1e3, 1e5, 2e7, 7e8, 5e9])
def test_miller_point_matches_closed_form(w):
    ref = closed_miller()
    p = solve_point(ex3_miller(), w)
    assert np.asarray(p.values)[0, 0] == pytest.approx(ref["h"](w), rel=1e-10)


def test_miller_point_matches_independent_mna_after_renumber():
    q = EX3
    nm = {0: 9, 1: 7, 2: 3, 3: 1}
    s = ex3_miller(nm=nm)
    mos = (mos_t(3, 7, 9, 9, q["gm1"], 0.0, q["g1"]), mos_t(1, 3, 9, 9, q["gm2"], 0.0, q["g2"]))
    cap = ((3, 9, q["c1"]), (1, 9, q["cl"]), (3, 1, q["cc"]))
    w = 4.2e6
    exp = ref_solve(mos=mos, cap=cap, ac_ground=(9,), volts={7: 1.0}, sense=(1, None), omega=w)
    assert np.asarray(solve_point(s, w).values)[0, 0] == pytest.approx(exp, rel=1e-12)


def test_zero_omega_is_dc_limit():
    p = solve_point(ex2d_sc_loop(), 0.0)
    v = np.asarray(p.values)[0]
    assert v[0] == pytest.approx(-300.0 / 104.0, rel=1e-12)
    assert math.isnan(complex(v[1]).real)
    assert "dc_charge_injection" in codes(p.undefined)


def test_singular_point_nan_no_exception():
    # 노드 2-3 저항 섬(용량 없음): G + jωC 가 모든 ω 에서 특이(영 피벗)
    ck = SmallSignalCircuit(
        resistors=(Resistor(2, 3, 1e3), Resistor(1, 4, 1e3), Resistor(4, 0, 1e3)),
        capacitors=(Capacitor(4, 0, 1e-12),),
        ac_ground=(0,),
    )
    s = build_mna(ck, (Excitation("v", voltages=((1, 1.0),)),), (Sense(3),))
    assert s.defects == ()
    p = solve_point(s, 1e6)
    assert np.all(np.isnan(np.asarray(p.values).real))
    assert "singular_mna" in codes(p.undefined)
    assert all(u.category == "numeric" for u in p.undefined if u.code == "singular_mna")


def test_no_restamp():
    s = ex3_miller()
    with count_calls(*STAMP_FUNCS, build_mna) as n:
        for w in (1.0, 1e3, 1e6, 1e9):
            solve_point(s, w)
    assert n == {"mos_stamps": 0, "two_terminal_stamps": 0, "build_mna": 0}
