"""CONTRACT 3.10·5절·I-1·I-2·I-3·I-4·I-7: analyze_loop -- gain·UGF·GBW·PM 을 한 번 계산. 예 1·2·2b·2c·3 의 폐형식과 대조,
격자 다른 인수 ValueError, NaN 표본은 모든 양 정의 불가(예외 아님), 관측 부호 무관, 노드 재번호·격자 변화 불변."""
import math

import numpy as np
import pytest

from gmid_engine.metrics import (
    Excitation,
    Factor,
    LoopAnalysis,
    MosSmallSignal,
    Capacitor,
    Sense,
    SmallSignalCircuit,
    analyze_loop,
    build_mna,
    solve_responses,
)

from .conftest import (
    EX2_CL,
    EX2_GDS,
    EX2_GM,
    RENUMBER,
    STAMP_FUNCS,
    closed_miller,
    closed_single_pole_loop,
    codes,
    count_calls,
    ex1_rc,
    ex2_amp,
    ex2_beta_res,
    ex2b_sf,
    ex2c_beta_cap,
    ex2d_sc_loop,
    ex3_miller,
)

R = 1e-9   # 상대 허용(CONTRACT 5절: 엔진·손계산 상대오차 ≤ 6.3e-12)


def _metrics(la):
    return (la.gain_db, la.ugf_hz, la.gbw_hz, la.phase_margin_deg)


# ---------- 예 1 ----------

def test_ex1_rc_gain_gbw_and_undefined_ugf_pm():
    (r,) = solve_responses((ex1_rc(),))
    la = analyze_loop((Factor(r, 0),))
    assert isinstance(la, LoopAnalysis)
    assert la.gain_db == pytest.approx(0.0, abs=1e-12)
    assert la.gbw_hz == pytest.approx(1.0 / (2 * math.pi * 1e3 * 1e-9), rel=R)
    assert la.gbw_hz == pytest.approx(159154.943, rel=1e-8)
    assert la.ugf_hz is None and la.phase_margin_deg is None
    assert "dc_not_above_level" in codes(la.undefined)
    by_q = {u.quantity: u.code for u in la.undefined}
    assert by_q.get("ugf_hz") == "dc_not_above_level"


# ---------- 예 2: β = 1, β = 0.25(저항), β = 0.25(용량, 2c) ----------

def test_ex2_beta_one():
    gain, ugf, gbw, pm = closed_single_pole_loop(1.0)
    assert (ugf, gbw, pm) == pytest.approx((159146985.146, 159154943.092, 90.5729673449), rel=R)
    ra, _ = solve_responses((ex2_amp(), ex2_beta_res()))
    la = analyze_loop((Factor(ra, 0),))
    assert la.gain_db == pytest.approx(40.0, rel=R)
    assert la.ugf_hz == pytest.approx(ugf, rel=R)
    assert la.gbw_hz == pytest.approx(gbw, rel=R)
    assert la.phase_margin_deg == pytest.approx(pm, rel=R)
    assert la.gbw_ugf_gap_hz == pytest.approx(gbw - ugf, rel=1e-6)
    assert la.undefined == ()


@pytest.mark.parametrize("beta_builder", [ex2_beta_res, ex2c_beta_cap], ids=["resistive", "capacitive_2c"])
def test_ex2_beta_quarter(beta_builder):
    gain, ugf, gbw, pm = closed_single_pole_loop(0.25)
    assert (gain, ugf, pm) == pytest.approx((27.9588001734, 39756892.0418, 92.292442776), rel=R)
    ra, rb = solve_responses((ex2_amp(), beta_builder()))
    la = analyze_loop((Factor(ra, 0), Factor(rb, 0)))
    assert abs(la.dc_value) == pytest.approx(25.0, rel=R)
    assert la.gain_db == pytest.approx(gain, rel=R)
    assert la.ugf_hz == pytest.approx(ugf, rel=R)
    assert la.gbw_hz == pytest.approx(gbw, rel=R)
    assert la.phase_margin_deg == pytest.approx(pm, rel=R)


def test_resistive_and_capacitive_beta_agree():
    ra, rr, rc = solve_responses((ex2_amp(), ex2_beta_res(), ex2c_beta_cap()))
    a = analyze_loop((Factor(ra, 0), Factor(rr, 0)))
    b = analyze_loop((Factor(ra, 0), Factor(rc, 0)))
    for x, y in zip(_metrics(a), _metrics(b)):
        assert x == pytest.approx(y, rel=R)


# ---------- 예 2b: gmb (I-4) ----------

def test_ex2b_source_follower_gmb():
    exp = 1e-3 / (1e-3 + 2e-4 + 1e-5 + 1e-4)
    exp0 = 1e-3 / (1e-3 + 0.0 + 1e-5 + 1e-4)
    assert (exp, exp0) == pytest.approx((0.763358779, 0.900900901), rel=1e-9)
    (r,) = solve_responses((ex2b_sf(),))
    (r0,) = solve_responses((ex2b_sf(gmb=0.0),))
    la, la0 = analyze_loop((Factor(r, 0),)), analyze_loop((Factor(r0, 0),))
    assert la.dc_value == pytest.approx(exp, rel=R)
    assert la.gain_db == pytest.approx(20.0 * math.log10(exp), rel=R)
    assert la0.dc_value == pytest.approx(exp0, rel=R)
    assert abs(la.gain_db - la0.gain_db) > 1.0          # gmb 를 빼면 값이 달라진다(옛 엔진 gmb 0건 결함)


# ---------- 예 3: 2극 Miller ----------

def test_ex3_miller():
    ref = closed_miller()
    assert ref["a1"] == pytest.approx(5.075e-5, rel=1e-12)
    assert ref["a2"] == pytest.approx(6.5e-14, rel=1e-12)
    assert (ref["ugf_hz"], ref["gbw_hz"], ref["pm_deg"]) == pytest.approx(
        (30592376.7006, 31361371.396, 70.6851677849), rel=R)
    (r,) = solve_responses((ex3_miller(),))
    la = analyze_loop((Factor(r, 0),))
    assert la.gain_db == pytest.approx(80.0, rel=R)
    assert la.ugf_hz == pytest.approx(ref["ugf_hz"], rel=R)
    assert la.gbw_hz == pytest.approx(ref["gbw_hz"], rel=R)
    assert la.phase_margin_deg == pytest.approx(ref["pm_deg"], rel=R)
    assert la.phase_lag_rad == pytest.approx(math.radians(180.0 - ref["pm_deg"]), rel=R)
    # 근사식(gm1/(2πCc) = 31.83 MHz, 69.92°)과는 다르다 -- 근사가 아니라 정확 해를 쓴다
    assert abs(la.ugf_hz - 1e-4 / (2 * math.pi * 0.5e-12)) > 1e5


def test_ex3_without_cc_coincident_poles():
    # Cc 없음: 두 극 모두 ωp = 1e7, K = 1e4 -> |T| = K/(1+(ω/ωp)²) = 1 에서 ω = ωp√(K−1), 지연 2·atan(√(K−1))
    (r,) = solve_responses((ex3_miller(with_cc=False),))
    la = analyze_loop((Factor(r, 0),))
    k, wp = 1e4, 1e7
    assert la.ugf_hz == pytest.approx(wp * math.sqrt(k - 1.0) / (2 * math.pi), rel=R)
    assert la.phase_margin_deg == pytest.approx(180.0 - 2.0 * math.degrees(math.atan(math.sqrt(k - 1.0))), rel=1e-7)
    assert abs(la.phase_margin_deg - closed_miller()["pm_deg"]) > 60.0


# ---------- 관측 부호 무관 ----------

def test_sense_sign_does_not_change_pm():
    ck = SmallSignalCircuit(mos=(MosSmallSignal(2, 1, 0, 0, EX2_GM, 0.0, EX2_GDS),),
                            capacitors=(Capacitor(2, 0, EX2_CL),), ac_ground=(0,))
    exc = (Excitation("vin", voltages=((1, 1.0),)),)
    pos = build_mna(ck, exc, (Sense(2),))
    neg = build_mna(ck, exc, (Sense(0, 2),))      # −v2
    rp, rn = solve_responses((pos, neg))
    a, b = analyze_loop((Factor(rp, 0),)), analyze_loop((Factor(rn, 0),))
    assert a.dc_value == pytest.approx(-b.dc_value, rel=R)
    for x, y in zip(_metrics(a), _metrics(b)):
        assert x == pytest.approx(y, rel=R)


# ---------- 입력 계약 / 정의 불가 ----------

def test_factors_from_different_grids_value_error():
    (ra,) = solve_responses((ex2_amp(),))
    (rm,) = solve_responses((ex3_miller(),))
    assert not np.array_equal(np.asarray(ra.omegas), np.asarray(rm.omegas))
    with pytest.raises(ValueError):
        analyze_loop((Factor(ra, 0), Factor(rm, 0)))


def test_nan_sample_makes_everything_undefined_without_exception():
    (r,) = solve_responses((ex2d_sc_loop(),))
    la = analyze_loop((Factor(r, 1),))         # iinj 열: DC 극한 NaN(dc_charge_injection)
    assert la.gain_db is None and la.ugf_hz is None and la.gbw_hz is None and la.phase_margin_deg is None
    assert "dc_charge_injection" in codes(la.undefined)


def test_sc_loop_closed_gain():
    (r,) = solve_responses((ex2d_sc_loop(),))
    la = analyze_loop((Factor(r, 0),))
    assert la.gain_db == pytest.approx(20.0 * math.log10(300.0 / 104.0), rel=R)


# ---------- I-1 / I-2 / I-3 / I-7 / 격자 불변 ----------

def test_no_restamp_during_analysis():
    ra, rb = solve_responses((ex2_amp(), ex2_beta_res()))
    with count_calls(*STAMP_FUNCS, build_mna) as n:
        analyze_loop((Factor(ra, 0), Factor(rb, 0)))
        analyze_loop((Factor(ra, 0),))
    assert n == {"mos_stamps": 0, "two_terminal_stamps": 0, "build_mna": 0}


def test_metrics_independent_of_shared_grid():
    (alone,) = solve_responses((ex3_miller(),))
    shared, _ = solve_responses((ex3_miller(), ex1_rc()))
    assert not np.array_equal(np.asarray(alone.omegas), np.asarray(shared.omegas))
    a, b = analyze_loop((Factor(alone, 0),)), analyze_loop((Factor(shared, 0),))
    for x, y in zip(_metrics(a), _metrics(b)):
        assert x == pytest.approx(y, rel=R)


def test_deterministic_bitwise():
    def run():
        (r,) = solve_responses((ex3_miller(),))
        return analyze_loop((Factor(r, 0),))
    a, b = run(), run()
    assert _metrics(a) == _metrics(b)
    assert a.gbw_ugf_gap_hz == b.gbw_ugf_gap_hz


def test_node_renumbering_invariant():
    (r1,) = solve_responses((ex3_miller(),))
    (r2,) = solve_responses((ex3_miller(nm=RENUMBER),))
    a, b = analyze_loop((Factor(r1, 0),)), analyze_loop((Factor(r2, 0),))
    for x, y in zip(_metrics(a), _metrics(b)):
        assert x == pytest.approx(y, rel=R)


def test_node_renumbering_invariant_beta_loop():
    ra, rb = solve_responses((ex2_amp(nm=RENUMBER), ex2c_beta_cap(nm=RENUMBER)))
    la = analyze_loop((Factor(ra, 0), Factor(rb, 0)))
    gain, ugf, gbw, pm = closed_single_pole_loop(0.25)
    assert (la.gain_db, la.ugf_hz, la.gbw_hz, la.phase_margin_deg) == pytest.approx((gain, ugf, gbw, pm), rel=R)
