"""CONTRACT 3.4·I-5: pencil_roots -- 극점 = (G, −C) 유한 일반화 고유값, zeros[r][j] = 관측 행 r · 열 j 전달함수의 유한 영점,
(|s|, 실부, 허부) 정렬, defects 면 빈 근, 용량 전용 노드 -> 원점 극점."""
import pytest

from gmid_engine.metrics import (
    Excitation,
    Resistor,
    Roots,
    Sense,
    SmallSignalCircuit,
    build_mna,
    pencil_roots,
)

from .conftest import EX2_CL, EX2_GDS, closed_miller, ex1_rc, ex2_amp, ex2c_beta_cap, ex3_miller


def _sorted_ok(seq):
    keys = [(abs(z), z.real, z.imag) for z in seq]
    return keys == sorted(keys)


def test_rc_single_pole_no_zero():
    r = pencil_roots(ex1_rc())
    assert isinstance(r, Roots)
    assert len(r.poles) == 1
    assert complex(r.poles[0]) == pytest.approx(complex(-1e6, 0.0), rel=1e-12)
    assert len(r.zeros) == 1 and len(r.zeros[0]) == 1 and tuple(r.zeros[0][0]) == ()   # zeros[관측 행][열]


def test_cs_pole():
    r = pencil_roots(ex2_amp())
    assert len(r.poles) == 1
    assert complex(r.poles[0]) == pytest.approx(complex(-EX2_GDS / EX2_CL, 0.0), rel=1e-12)
    assert len(r.zeros[0]) == 2 and all(tuple(z) == () for z in r.zeros[0])


def test_miller_poles_and_rhp_zero():
    ref = closed_miller()
    assert ref["p1"] == pytest.approx(19704.9308, rel=1e-9)
    assert ref["p2"] == pytest.approx(780749525.838, rel=1e-9)
    r = pencil_roots(ex3_miller())
    assert len(r.poles) == 2
    assert _sorted_ok(r.poles)
    p1, p2 = (complex(p) for p in r.poles)
    assert p1.real < 0 and p2.real < 0
    assert abs(p1.imag) <= 1e-9 * abs(p1) and abs(p2.imag) <= 1e-9 * abs(p2)
    assert abs(p1) == pytest.approx(ref["p1"], rel=1e-9)
    assert abs(p2) == pytest.approx(ref["p2"], rel=1e-9)
    (zs,) = r.zeros[0]
    assert len(zs) == 1
    assert complex(zs[0]) == pytest.approx(complex(2e9, 0.0), rel=1e-9)   # +gm2/Cc, 우반면


def test_miller_cap_splits_poles():
    # I-5: Cc 없으면 1/(R1C1) = 1/(R2CL) = 1e7 rad/s 두 극점, Cc 가 p1 을 내리고 p2 를 올린다
    no_cc = [abs(complex(p)) for p in pencil_roots(ex3_miller(with_cc=False)).poles]
    assert len(no_cc) == 2
    for p in no_cc:
        assert p == pytest.approx(1e7, rel=1e-6)
    with_cc = [abs(complex(p)) for p in pencil_roots(ex3_miller()).poles]
    assert with_cc[0] < 1e5 and with_cc[1] > 1e8
    assert with_cc[1] / with_cc[0] > 1e4


def test_charge_node_gives_origin_pole():
    r = pencil_roots(ex2c_beta_cap())
    mags = [abs(complex(p)) for p in r.poles]
    assert mags and min(mags) == pytest.approx(0.0, abs=1e-6)
    assert _sorted_ok(r.poles)


def test_defects_give_empty_roots():
    ck = SmallSignalCircuit(resistors=(Resistor(1, 2, 1e3), Resistor(2, 0, 1e3)), ac_ground=(0,))
    s = build_mna(ck, (Excitation("v", voltages=((1, 1.0),)),), (Sense(5),))
    r = pencil_roots(s)
    assert tuple(r.poles) == ()
    assert all(tuple(z) == () for z in r.zeros[0])


def test_resistive_only_no_finite_roots():
    ck = SmallSignalCircuit(resistors=(Resistor(1, 2, 1e3), Resistor(2, 0, 1e3)), ac_ground=(0,))
    s = build_mna(ck, (Excitation("v", voltages=((1, 1.0),)),), (Sense(2),))
    r = pencil_roots(s)
    assert tuple(r.poles) == ()
    assert tuple(r.zeros[0][0]) == ()
