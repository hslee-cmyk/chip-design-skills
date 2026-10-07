"""CONTRACT 3.3·I-11: solve_dc_limit -- ω → 0 극한(전하 보존). 용량 전용 노드는 C_F·x = BC_F, 주입 전류 열만 NaN +
dc_charge_injection, 특이면 모든 열 NaN + singular_dc_limit, defects 면 모든 열 NaN + 그 사유. 예외 없음."""
import math

import numpy as np
import pytest

from gmid_engine.metrics import (
    Capacitor,
    DcLimit,
    Excitation,
    MosSmallSignal,
    Resistor,
    Sense,
    SmallSignalCircuit,
    build_mna,
    solve_dc_limit,
)

from .conftest import closed_sc_loop_dc, codes, ex1_rc, ex2_amp, ex2b_sf, ex2c_beta_cap, ex2d_sc_loop, ex3_miller, ex6_ratio


def _v(d):
    return np.asarray(d.values)


def test_rc_dc_is_one():
    d = solve_dc_limit(ex1_rc())
    assert isinstance(d, DcLimit)
    assert _v(d)[0] == pytest.approx(1.0, rel=1e-12)
    assert d.undefined == ()


def test_cs_amp_dc_columns():
    d = solve_dc_limit(ex2_amp())
    # vin: −gm·ro = −100, iout: ro = 1e5
    assert _v(d)[0] == pytest.approx(-100.0, rel=1e-12)
    assert _v(d)[1] == pytest.approx(1e5, rel=1e-12)


def test_source_follower_dc_with_gmb():
    exp = 1e-3 / (1e-3 + 2e-4 + 1e-5 + 1e-4)
    assert exp == pytest.approx(0.763358779, rel=1e-9)
    assert _v(solve_dc_limit(ex2b_sf()))[0] == pytest.approx(exp, rel=1e-12)


def test_miller_dc_gain():
    # 부호: 두 반전단 -> +gm1R1·gm2R2
    assert _v(solve_dc_limit(ex3_miller()))[0] == pytest.approx(1e4, rel=1e-12)


def test_ratio_example_dc_columns():
    d = solve_dc_limit(ex6_ratio())
    assert _v(d)[0] == pytest.approx(10.0 / 11.0, rel=1e-12)
    assert _v(d)[1] == pytest.approx(1.0 / 11.0, rel=1e-12)


# ---------- 전하 보존 (I-11) ----------

@pytest.mark.parametrize("cf, cs", [(1e-12, 3e-12), (2e-12, 2e-12), (1e-13, 9.9e-12)])
def test_cap_divider_charge_conservation(cf, cs):
    d = solve_dc_limit(ex2c_beta_cap(cf=cf, cs=cs))
    assert _v(d)[0] == pytest.approx(cf / (cf + cs), rel=1e-12)
    assert d.undefined == ()


def test_sc_loop_dc_and_injection_column_only():
    d = solve_dc_limit(ex2d_sc_loop())
    exp = closed_sc_loop_dc()
    assert exp == pytest.approx(-300.0 / 104.0, rel=1e-12)
    assert _v(d)[0] == pytest.approx(exp, rel=1e-12)
    assert math.isnan(_v(d)[1])
    assert codes(d.undefined) == {"dc_charge_injection"}
    assert all(u.category == "definitional" for u in d.undefined)


def test_injection_into_charge_node_only_that_column():
    # 노드 3: Cf(2,3)·Cs(3,0) 만. 열 a = 1 V at 2(정상), 열 b = 노드 3 에 1 A(발산)
    ck = SmallSignalCircuit(capacitors=(Capacitor(2, 3, 1e-12), Capacitor(3, 0, 3e-12)), ac_ground=(0,))
    s = build_mna(ck, (Excitation("a", voltages=((2, 1.0),)), Excitation("b", currents=((3, 1.0),))), Sense(3))
    d = solve_dc_limit(s)
    assert _v(d)[0] == pytest.approx(0.25, rel=1e-12)
    assert math.isnan(_v(d)[1])
    assert codes(d.undefined) == {"dc_charge_injection"}


# ---------- 특이 / defects ----------

def test_singular_dc_limit_all_columns_nan():
    # 노드 2-3 저항 섬이 용량으로만 접지·구동에 이어진다: G 의 섬 블록이 특이, charge_nodes 없음
    ck = SmallSignalCircuit(
        resistors=(Resistor(2, 3, 1e3),),
        capacitors=(Capacitor(1, 2, 1e-12), Capacitor(3, 0, 1e-12)),
        ac_ground=(0,),
    )
    s = build_mna(ck, (Excitation("a", voltages=((1, 1.0),)), Excitation("b", voltages=((1, 2.0),))), Sense(3))
    assert tuple(s.charge_nodes) == ()
    d = solve_dc_limit(s)
    assert np.all(np.isnan(_v(d)))
    assert "singular_dc_limit" in codes(d.undefined)
    assert all(u.category == "structural" for u in d.undefined if u.code == "singular_dc_limit")


def test_defects_give_nan_with_reason():
    ck = SmallSignalCircuit(resistors=(Resistor(1, 2, 1e3), Resistor(2, 0, 1e3)), ac_ground=(0,))
    s = build_mna(ck, (Excitation("v", voltages=((1, 1.0),)),), Sense(5))
    d = solve_dc_limit(s)
    assert np.all(np.isnan(_v(d)))
    assert "isolated_node" in codes(d.undefined)
