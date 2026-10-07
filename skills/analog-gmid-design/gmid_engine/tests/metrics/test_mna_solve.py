"""CONTRACT 3.6·I-1·I-3: solve_responses -- 계마다 pencil_roots 1회, 모든 계 근의 합집합으로 공유 격자 1개, ω = 0 은 DC 극한,
ω > 0 은 풀이, 재스탬프 0(격자가 바뀌어도), values[0] = DC 극한, 사유 모음. 결정론."""
import math

import numpy as np
import pytest

from gmid_engine.metrics import (
    Excitation,
    Resistor,
    Sense,
    SmallSignalCircuit,
    SystemResponse,
    build_mna,
    pencil_roots,
    solve_responses,
)

from .conftest import (
    EX2_CL,
    EX2_GDS,
    EX2_GM,
    EX2D,
    STAMP_FUNCS,
    closed_sc_loop_dc,
    codes,
    count_calls,
    ex1_rc,
    ex2_amp,
    ex2c_beta_cap,
    ex2d_sc_loop,
    ex3_miller,
    mos_t,
    ref_solve,
)


def test_shared_grid_union_of_roots():
    r_rc, r_amp = solve_responses((ex1_rc(), ex2_amp()))
    assert isinstance(r_rc, SystemResponse)
    exp = (0.0, 1e6, math.sqrt(1e6 * 1e7), 1e7)        # RC 극 1e6, CS 극 gds/CL = 1e7
    for r in (r_rc, r_amp):
        g = np.asarray(r.omegas)
        assert g.shape == (4,)
        assert g[0] == 0.0
        assert np.allclose(g, exp, rtol=1e-12, atol=0)
    assert np.array_equal(np.asarray(r_rc.omegas), np.asarray(r_amp.omegas))


def test_values_match_independent_mna():
    r_rc, r_amp = solve_responses((ex1_rc(), ex2_amp()))
    om = np.asarray(r_rc.omegas)
    v_rc = np.asarray(r_rc.values)[:, 0]        # 관측 1개: (k, r, m) 의 관측 행 0
    v_amp = np.asarray(r_amp.values)[:, 0]
    assert v_rc.shape == (4, 1) and v_amp.shape == (4, 2)
    for k, w in enumerate(om):
        if w == 0.0:
            continue
        assert v_rc[k, 0] == pytest.approx(1.0 / (1.0 + 1j * w * 1e-6), rel=1e-12)
        mos = (mos_t(2, 1, 0, 0, EX2_GM, 0.0, EX2_GDS),)
        cap = ((2, 0, EX2_CL),)
        assert v_amp[k, 0] == pytest.approx(ref_solve(mos=mos, cap=cap, volts={1: 1.0}, sense=(2, None), omega=w),
                                            rel=1e-12)
        assert v_amp[k, 1] == pytest.approx(ref_solve(mos=mos, cap=cap, volts={1: 0.0}, amps={2: 1.0}, sense=(2, None), omega=w),
                                            rel=1e-12)


def test_dc_row_is_dc_limit():
    (r,) = solve_responses((ex2_amp(),))
    v = np.asarray(r.values)[:, 0]
    assert v[0, 0] == pytest.approx(-100.0, rel=1e-12)
    assert v[0, 1] == pytest.approx(1e5, rel=1e-12)
    assert np.array_equal(np.asarray(r.dc)[0], v[0].real)


def test_cap_divider_flat_at_all_grid_points():
    (r,) = solve_responses((ex2c_beta_cap(),))
    v = np.asarray(r.values)[:, 0, 0]
    assert np.allclose(v, 0.25, rtol=1e-12, atol=0)
    assert v[-1] == pytest.approx(0.25, rel=1e-12)


def test_sc_loop_matches_independent_mna_and_injection_nan():
    (r,) = solve_responses((ex2d_sc_loop(),))
    v = np.asarray(r.values)[:, 0]
    om = np.asarray(r.omegas)
    assert v[0, 0] == pytest.approx(closed_sc_loop_dc(), rel=1e-12)
    assert math.isnan(v[0, 1].real) or math.isnan(v[0, 1].imag)
    assert "dc_charge_injection" in codes(r.undefined)
    p = EX2D
    mos = (mos_t(2, 3, 0, 0, p["gm"], 0.0, p["gds"]),)
    cap = ((2, 3, p["cf"]), (3, 1, p["cs"]), (2, 0, p["cl"]))
    # 값 대조는 조건수가 나쁘지 않은 ω(> 1 rad/s)에서만 한다 -- 격자 자체의 원점 근 처리는 아래 test 가 본다
    for k, w in enumerate(om):
        if w <= 1.0:
            continue
        assert v[k, 0] == pytest.approx(ref_solve(mos=mos, cap=cap, volts={1: 1.0}, sense=(2, None), omega=w), rel=1e-10)
        assert v[k, 1] == pytest.approx(ref_solve(mos=mos, cap=cap, volts={1: 0.0}, amps={3: 1.0}, sense=(2, None),
                                                omega=w), rel=1e-10)


def test_charge_mode_origin_pole_not_a_grid_breakpoint():
    # CONTRACT 3.4: 용량 전용 노드의 원점 극점(|s| = 0)은 격자 꺾임점에서 빠진다.
    # 예 2d 손계산: det(G + sC) = s·[gds(Cf+Cs) + gm·Cf + s((Cf+CL)(Cf+Cs) − Cf²)]
    #   -> 원점 극점 + |p| = (gds·(Cf+Cs) + gm·Cf)/((Cf+CL)(Cf+Cs) − Cf²), vin 열 영점 gm/Cf(+ 원점)
    p = EX2D
    pole = (p["gds"] * (p["cf"] + p["cs"]) + p["gm"] * p["cf"]) / ((p["cf"] + p["cl"]) * (p["cf"] + p["cs"]) - p["cf"] ** 2)
    zero = p["gm"] / p["cf"]
    (r,) = solve_responses((ex2d_sc_loop(),))
    exp = (0.0, pole, math.sqrt(pole * zero), zero)
    got = np.asarray(r.omegas)
    assert got.shape == (len(exp),), "grid %r" % (tuple(got),)
    assert np.allclose(got, exp, rtol=1e-9, atol=0)


def test_defect_system_values_nan_no_exception():
    ck = SmallSignalCircuit(resistors=(Resistor(1, 2, 1e3), Resistor(2, 0, 1e3)), ac_ground=(0,))
    s = build_mna(ck, (Excitation("v", voltages=((1, 1.0),)),), (Sense(5),))
    (r,) = solve_responses((s,))
    assert np.all(np.isnan(np.asarray(r.values).real))
    assert "isolated_node" in codes(r.undefined)


# ---------- I-1: 조립 1회, 격자가 바뀌어도 재조립 0 ----------

def test_no_restamp_and_one_root_call_per_system():
    systems = (ex1_rc(), ex2_amp(), ex3_miller())
    with count_calls(*STAMP_FUNCS, build_mna, pencil_roots) as n:
        solve_responses(systems)
    assert n["mos_stamps"] == 0 and n["two_terminal_stamps"] == 0 and n["build_mna"] == 0
    assert n["pencil_roots"] == len(systems)


def test_grid_change_triggers_no_reassembly():
    amp = ex2_amp()
    with count_calls(*STAMP_FUNCS, build_mna) as n:
        (a1,) = solve_responses((amp,))
        a2, _ = solve_responses((amp, ex1_rc_prebuilt))
        a3, _ = solve_responses((amp, miller_prebuilt))
    assert n == {"mos_stamps": 0, "two_terminal_stamps": 0, "build_mna": 0}
    grids = [tuple(np.asarray(r.omegas)) for r in (a1, a2, a3)]
    assert len(set(grids)) == 3                        # 격자는 실제로 바뀌었다
    for r in (a1, a2, a3):
        assert np.asarray(r.values)[0, 0, 0] == pytest.approx(-100.0, rel=1e-12)


ex1_rc_prebuilt = ex1_rc()
miller_prebuilt = ex3_miller()


# ---------- I-3: 결정론 ----------

def test_deterministic_bitwise():
    a = solve_responses((ex3_miller(), ex2d_sc_loop()))
    b = solve_responses((ex3_miller(), ex2d_sc_loop()))
    for x, y in zip(a, b):
        assert np.array_equal(np.asarray(x.omegas), np.asarray(y.omegas))
        assert np.array_equal(np.asarray(x.values), np.asarray(y.values), equal_nan=True)
        assert x.undefined == y.undefined
