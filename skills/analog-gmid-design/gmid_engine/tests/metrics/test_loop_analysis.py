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


# =====================================================================================================================
# PM 전제(CONTRACT 3.10 'PM 전제', 2절 표 `loop_open_rhp_poles`, I-17, 예 8·8a·8b).
# - 인수 poles 에 Re > 0 근 -> phase_margin_deg None + Undefined("phase_margin_deg", "loop_open_rhp_poles", "definitional",
#   (("rhp_poles", 근 tuple -- (|s|, 실부, 허부) 정렬), ("rhp_pole_count", 개수))). 교차·위상 사유보다 먼저.
# - phase_lag_rad·ugf_hz·gain_db·gbw_hz 는 그대로 값.
# - 우반면 근이 없으면 LoopAnalysis 전 필드·undefined 가 전제 도입 전과 비트 동일.
# 기대값: conftest 폐형식 closed_ex8·closed_ex8a(노드 방정식 소거 2차식 근) -- 아래에서 독립 MNA·독립 Middlebrook 과 먼저 대조.
# =====================================================================================================================

import dataclasses
import hashlib

from gmid_engine.metrics import Undefined, pencil_roots

from .conftest import (
    EX7_CUT,
    EX7B_CUTS,
    EX8,
    check_rhp_detail,
    circuit_of,
    closed_ex8,
    closed_ex8a,
    closed_ring_poles,
    ring_system,
    ex7_parts,
    ex7b_parts,
    ex8_parts,
    ex8_system,
    ex8a_parts,
    mos_t,
    pm_undefined,
    probe_of,
    ref_middlebrook,
    ref_solve,
)

ROOT_R = 1e-9          # 근 값 상대 허용(계약 실측: 예 8 극점 19999999.999999996 -- 상대 2e-16)
PM_RHP = "loop_open_rhp_poles"


def _rhp_detail(u):
    """Undefined.detail -> (rhp_poles, rhp_pole_count). 형식 전부는 conftest check_rhp_detail(3.10 'detail 형식(정확히)')."""
    roots = check_rhp_detail(u)
    return roots, dict(u.detail)["rhp_pole_count"]


def _assert_rhp(la, expected_roots):
    """phase_margin_deg None, PM 의 첫 사유 = loop_open_rhp_poles(definitional), detail 근 = 기대 근(정렬 순서).
    expected_roots 원소: 실수(허부 0) 또는 (re, im) 쌍."""
    assert la.phase_margin_deg is None
    pmu = pm_undefined(la)
    assert pmu, la.undefined
    u = pmu[0]
    assert isinstance(u, Undefined)
    assert (u.quantity, u.code, u.category) == ("phase_margin_deg", PM_RHP, "definitional")
    roots, count = _rhp_detail(u)
    assert count == len(roots) == len(expected_roots)
    for (re, im), exp in zip(roots, expected_roots):
        er, ei = exp if isinstance(exp, tuple) else (exp, 0.0)
        scale = math.hypot(er, ei)
        assert abs(re - er) <= ROOT_R * scale, ((re, im), exp)
        assert abs(im - ei) <= ROOT_R * scale, ((re, im), exp)
    return u


def _f3db_w(d):
    """|T| = |T0|/√2 교차(폐형식, brentq; 조밀 격자에서 교차 하나 확인)."""
    from scipy.optimize import brentq
    t, lvl = d["t"], abs(d["t0"]) / math.sqrt(2.0)
    grid = np.logspace(0, 13, 4001)
    f = np.array([abs(t(w)) - lvl for w in grid])
    assert int(np.count_nonzero(np.diff(np.sign(f)))) == 1
    return brentq(lambda w: abs(t(w)) - lvl, 1.0, 1e13, xtol=1e-9, rtol=1e-15, maxiter=500)


# ---------- 폐형식 자체의 독립 대조(입력 확인 -- 피검 아님) ----------

def test_ex8_closed_form_matches_independent_mna_and_contract_numbers():
    d = closed_ex8()
    mos, _, cap = ex8_parts()
    for w in (1e3, 1e6, 1e7, 2e7, 1e8, 1e9, 1e10):
        v = ref_solve(mos=tuple(mos_t(*m) for m in mos), cap=cap, volts={1: 1.0}, sense=(2, None), omega=w)
        assert abs(v - d["t"](w)) <= 1e-13 * abs(v)
    # 5절 예 8 숫자(계약 표기 자릿수 반 단위)
    assert d["poles"] == pytest.approx((-5e7, 2e7), rel=1e-14) and d["zero"] == pytest.approx(-1e7, rel=1e-14)
    assert d["t0"] == pytest.approx(10.0, rel=1e-14)
    assert abs(d["ugf_hz"] - 158931912.449) <= 5e-4
    assert abs(d["lag_rad"] - (-1.59078562547)) <= 5e-12
    assert abs(d["old_pm_deg"] - 271.145302449) <= 5e-10
    lo, hi = d["closed_loop"]
    assert hi == pytest.approx(9.812e8, rel=1e-3) and lo == pytest.approx(-1.121e7, rel=1e-3)   # 폐루프 불안정(기록 확인)


@pytest.mark.parametrize("gx2", [EX8["gx2"], EX8["gx2_8b"]], ids=["8a", "8b"])
def test_ex8a_closed_form_matches_independent_middlebrook(gx2):
    d = closed_ex8a(gx2)
    mos, _, cap = ex8a_parts(gx2)
    for w in (1e3, 1e5, 1e7, 3e7, 1e8, 1e9, 1e10):
        t = ref_middlebrook(mos=mos, cap=cap, cuts=EX7_CUT, omega=w)["T"]
        assert abs(t - d["t"](w)) <= 1e-13 * abs(t)


def test_ex8a_8b_closed_numbers_match_contract():
    a = closed_ex8a(EX8["gx2"])
    assert a["poles"][1] == pytest.approx(15481601.1727, abs=5e-5)
    assert abs(a["old_pm_deg"] - 274.443) <= 5e-4
    assert all(r < 0.0 for r in a["closed_loop"])                    # 폐루프 안정(예 8a 기록)
    assert sorted(a["closed_loop"]) == pytest.approx([-1.5889e8, -5.3945e6], rel=1e-4)
    b = closed_ex8a(EX8["gx2_8b"])
    assert b["poles"][1] == pytest.approx(43801205.4, abs=0.05)
    assert b["closed_loop"][1] == pytest.approx(8278492.15, abs=0.005)  # 공통 근 = 폐루프 우반면 극점
    assert abs(b["t0"]) == pytest.approx(0.5, rel=1e-14)


# ---------- 예 8: β = 1 Factor, 우반면 극점 1개 ----------

def test_ex8_pm_undefined_rhp_pole_measured_fields_kept():
    d = closed_ex8()
    _, sysm = ex8_system()
    (r,) = solve_responses((sysm,))
    f = Factor(r, 0)
    assert any(complex(p).real > 0 for p in f.poles)                 # 입력 확인: 인수 극점에 우반면 근
    la = analyze_loop((f,))
    u = _assert_rhp(la, (2e7,))
    assert len(pm_undefined(la)) == 1
    assert {x.quantity for x in la.undefined} == {"phase_margin_deg"}   # 다른 양은 정의됨
    assert dict(u.detail)["rhp_pole_count"] == 1
    # 측정량은 그대로(3.10)
    assert la.gain_db == pytest.approx(20.0, rel=1e-12)
    assert la.dc_value == pytest.approx(d["t0"], rel=1e-12)
    assert la.ugf_hz == pytest.approx(d["ugf_hz"], rel=R)
    assert la.phase_lag_rad == pytest.approx(d["lag_rad"], rel=R)
    assert la.gbw_hz == pytest.approx(d["t0"] * _f3db_w(d) / (2 * math.pi), rel=R)
    assert la.gbw_ugf_gap_hz == pytest.approx(la.gbw_hz - la.ugf_hz, rel=1e-9)


def test_ex8_node_renumbering_same_rhp_detail():
    nm = {0: 17, 1: 4, 2: 30, 5: 3}
    out = []
    for m in (None, nm):
        _, sysm = ex8_system(nm=m)
        (r,) = solve_responses((sysm,))
        la = analyze_loop((Factor(r, 0),))
        out.append((_assert_rhp(la, (2e7,)), la))
    (ua, la_a), (ub, la_b) = out
    (pa, ca), (pb, cb) = _rhp_detail(ua), _rhp_detail(ub)
    assert ca == cb == 1
    assert pa[0][0] == pytest.approx(pb[0][0], rel=1e-12) and abs(pa[0][1] - pb[0][1]) <= 1e-12 * abs(pa[0][0])
    assert la_a.ugf_hz == pytest.approx(la_b.ugf_hz, rel=R)


def test_ex8_detail_exact_stored_form():
    """3.10 '저장 순서는 (("rhp_pole_count", n), ("rhp_poles", ((re, im), …)))' -- 예 8 은 ((2e7, 0.0),)·1. complex 원소 없음."""
    _, sysm = ex8_system()
    (r,) = solve_responses((sysm,))
    u = pm_undefined(analyze_loop((Factor(r, 0),)))[0]
    (k0, n), (k1, roots) = u.detail
    assert (k0, k1, n, len(roots)) == ("rhp_pole_count", "rhp_poles", 1, 1)
    assert not any(isinstance(v, complex) for p in roots for v in p)
    assert roots[0][0] == pytest.approx(2e7, rel=ROOT_R) and abs(roots[0][1]) <= ROOT_R * 2e7
    assert hash(u.detail) == hash(u.detail)                          # 불변·해시 가능(블록 write 전제)


def test_conjugate_rhp_pair_two_entries_sorted():
    """3.10 '켤레 복소쌍은 두 원소(허부 + 와 −)', 정렬 (|s|, 실부, 허부) -> 같은 |s|·실부라 허부 − 가 먼저. 고리 폐형식 극점
    (−g − gm·c)/C 와 대조(폐형식은 아래 test 에서 독립 MNA 로 확인), 실극점은 좌반면이라 목록에 없다."""
    real_p, pair = closed_ring_poles()
    ck, sysm = ring_system()
    (r,) = solve_responses((sysm,))
    f = Factor(r, 0)
    got = sorted((complex(p).real, complex(p).imag) for p in f.poles)
    exp = sorted([(real_p, 0.0)] + list(pair))
    for g, e in zip(got, exp):                                       # 입력 확인: 계 극점 = 폐형식
        assert abs(g[0] - e[0]) <= 1e-9 * abs(complex(*e)) and abs(g[1] - e[1]) <= 1e-9 * abs(complex(*e))
    la = analyze_loop((f,))
    u = _assert_rhp(la, pair)
    roots = check_rhp_detail(u)
    assert len(roots) == 2 and roots[0][1] < 0.0 < roots[1][1]
    assert abs(roots[0][0] - roots[1][0]) <= 1e-9 * roots[0][0]


def test_ring_closed_form_matches_independent_mna():
    """입력 확인: 고리 H = −gm0(g + sC)²/((g + sC)³ + gm³)(분모 근 = closed_ring_poles) 를 독립 MNA(ref_solve)와 대조."""
    from .conftest import RING
    p = RING
    mos = (mos_t(2, 1, 0, 0, 1e-3, 0.0, 0.0), mos_t(3, 2, 0, 0, p["gm"], 0.0, p["gds"]),
           mos_t(4, 3, 0, 0, p["gm"], 0.0, p["gds"]), mos_t(2, 4, 0, 0, p["gm"], 0.0, p["gds"]))
    cap = ((2, 0, p["c"]), (3, 0, p["c"]), (4, 0, p["c"]))
    real_p, pair = closed_ring_poles()
    for w in (1e3, 1e6, 1e8, 1e10):
        y = p["gds"] + 1j * w * p["c"]
        h = -1e-3 * y * y / (y ** 3 + p["gm"] ** 3)
        v = ref_solve(mos=mos, cap=cap, volts={1: 1.0}, sense=(2, None), omega=w)
        assert abs(v - h) <= 1e-12 * abs(v)
    for re, im in ((real_p, 0.0),) + pair:                          # 분모 근 확인
        y = p["gds"] + complex(re, im) * p["c"]
        assert abs(y ** 3 + p["gm"] ** 3) <= 1e-12 * p["gm"] ** 3


def test_ex8_rhp_precondition_with_shared_grid():
    """다른 계와 격자를 공유해도(격자 점이 달라도) 판정은 인수 poles 로만 -- 같은 사유·같은 근."""
    _, sysm = ex8_system()
    r, _ = solve_responses((sysm, ex3_miller()))
    la = analyze_loop((Factor(r, 0),))
    _assert_rhp(la, (2e7,))
    assert la.ugf_hz == pytest.approx(closed_ex8()["ugf_hz"], rel=R)


def test_ex8_in_factor_product_rhp_from_any_factor():
    """인수 곱(예 2 기계): 우반면 극점은 인수 poles 의 합집합에서 센다 -- 예 8 계 × 저항 β(0.25)."""
    _, sysm = ex8_system()
    r, rb = solve_responses((sysm, ex2_beta_res()))
    la = analyze_loop((Factor(r, 0), Factor(rb, 0)))
    _assert_rhp(la, (2e7,))
    assert la.gain_db == pytest.approx(20.0 * math.log10(2.5), rel=1e-12)


def test_ex8_deterministic_bitwise():
    def run():
        _, sysm = ex8_system()
        (r,) = solve_responses((sysm,))
        return analyze_loop((Factor(r, 0),))
    assert _canon(run()) == _canon(run())


# ---------- 예 8a: ProbeFactor, 개루프 우반면·폐루프 안정 -> PM 그래도 정의 안 됨 ----------

def test_ex8a_probe_pm_undefined_closed_loop_stable_case():
    d = closed_ex8a(EX8["gx2"])
    _, pf, _ = probe_of(ex8a_parts(EX8["gx2"]), EX7_CUT)
    assert any(complex(p).real > 0 for p in pf.poles)                # 입력 확인
    la = analyze_loop((pf,))
    _assert_rhp(la, (d["poles"][1],))
    assert len(pm_undefined(la)) == 1
    assert la.gain_db == pytest.approx(20.0 * math.log10(abs(d["t0"])), rel=1e-12)
    assert la.ugf_hz == pytest.approx(d["ugf_hz"], rel=R)
    assert la.phase_lag_rad == pytest.approx(d["lag_rad"], rel=R)


def test_ex8a_closed_loop_poles_of_uncut_circuit_are_stable():
    """3.10 '폐루프 일관성(기록)': 절단 전 회로 계 극점 = 1 + T 의 근(+ 전하 모드 원점) -- 폐형식과 대조(기록 확인)."""
    mos, res, cap = ex8a_parts(EX8["gx2"])
    from gmid_engine.metrics import Excitation as _E, Sense as _S
    sysm = build_mna(circuit_of(mos, res, cap), (_E("q", charges=((3, 1.0),)),), (_S(2),))
    poles = sorted(complex(p).real for p in pencil_roots(sysm).poles)
    nz = [p for p in poles if p != 0.0]
    assert nz == pytest.approx(sorted(closed_ex8a(EX8["gx2"])["closed_loop"]), rel=1e-9)
    assert all(p <= 0.0 for p in poles)


# ---------- 예 8b: 공통 우반면 근 + |T(0)| < 1 -> 전제 위반이 교차 사유보다 먼저 ----------

def test_ex8b_rhp_precedes_crossing_reason_and_counts_common_root():
    b = closed_ex8a(EX8["gx2_8b"])
    _, pf, _ = probe_of(ex8a_parts(EX8["gx2_8b"]), EX7_CUT)
    la = analyze_loop((pf,))
    # 근 목록 = 상쇄 안 된 공통 근(= 폐루프 우반면 극점 8278492.15) + 실제 T 의 우반면 극점(43801205.4), |s| 오름차순
    _assert_rhp(la, (b["closed_loop"][1], b["poles"][1]))
    assert pm_undefined(la)[0].code == PM_RHP                        # 교차 사유(dc_not_above_level)보다 먼저
    by_q = {}
    for u in la.undefined:
        by_q.setdefault(u.quantity, []).append(u.code)
    assert by_q.get("ugf_hz", [None])[0] == "dc_not_above_level"     # UGF 는 그대로 교차 사유
    assert la.ugf_hz is None
    assert la.gain_db == pytest.approx(20.0 * math.log10(0.5), rel=1e-12)


# ---------- I-17 부정: 우반면 근이 없으면 전제 도입 전과 비트 동일 ----------

def _canon(x):
    """결과 레코드의 비트 단위 정규형(부동소수 = float.hex)."""
    if dataclasses.is_dataclass(x) and not isinstance(x, type):
        return (type(x).__name__,) + tuple((f.name, _canon(getattr(x, f.name))) for f in dataclasses.fields(x))
    if isinstance(x, (bool, np.bool_)):
        return bool(x)
    if isinstance(x, (int, np.integer)):
        return int(x)
    if isinstance(x, (float, np.floating)):
        return float(x).hex()
    if isinstance(x, (complex, np.complexfloating)):
        return ("c", float(x.real).hex(), float(x.imag).hex())
    if isinstance(x, np.ndarray):
        return ("nd", x.shape, tuple(_canon(v) for v in x.ravel()))
    if isinstance(x, (tuple, list)):
        return tuple(_canon(v) for v in x)
    if x is None or isinstance(x, str):
        return x
    return repr(x)


def _digest(la):
    return hashlib.sha256(repr(_canon(la)).encode("utf-8")).hexdigest()[:20]


def _no_rhp_cases():
    """우반면 극점 없는 예 1~7c(예 3 은 우반면 영점, 예 2c·7 은 원점 극점(전하 모드)이 있다 -- 문턱이 영점·원점을 세지 않음)."""
    def one(builder, col=0):
        (r,) = solve_responses((builder(),))
        return analyze_loop((Factor(r, col),))

    def two(a, b):
        ra, rb = solve_responses((a(), b()))
        return analyze_loop((Factor(ra, 0), Factor(rb, 0)))

    def probe(parts, cuts, w):
        return analyze_loop((probe_of(parts, cuts, w)[1],))

    return {
        "ex1": lambda: one(ex1_rc),
        "ex2_beta1": lambda: one(ex2_amp),
        "ex2_beta_res": lambda: two(ex2_amp, ex2_beta_res),
        "ex2c_beta_cap": lambda: two(ex2_amp, ex2c_beta_cap),
        "ex2b": lambda: one(ex2b_sf),
        "ex2d_vin": lambda: one(ex2d_sc_loop, 0),
        "ex2d_iinj": lambda: one(ex2d_sc_loop, 1),
        "ex3": lambda: one(ex3_miller),
        "ex3_no_cc": lambda: one(lambda: ex3_miller(with_cc=False)),
        "ex7": lambda: probe(ex7_parts(), EX7_CUT, (1.0,)),
        "ex7b_dm": lambda: probe(ex7b_parts(), EX7B_CUTS, (0.5, -0.5)),
        "ex7b_cm": lambda: probe(ex7b_parts(), EX7B_CUTS, (0.5, 0.5)),
        "ex7c": lambda: probe(ex7_parts(cs_resistor=True), EX7_CUT, (1.0,)),
    }


# 전제 도입 전 엔진(master 98d6cd2 -- 3.10 'PM 전제' 이전, 분해능 병합 뒤)의 analyze_loop 결과 정규형 지문. 생성: 그 커밋을
# git archive 로 풀어 이 파일의 _no_rhp_cases·_digest 를 그대로 돌렸다(I-17 의 '전제 도입 전'이 정의상 기준 -- 값 대조는 위 폐형식 test).
# (지문은 같은 numpy·LAPACK 빌드 기준 -- 빌드를 바꾸면 기준 커밋에서 다시 생성한다.)
PRE_PREMISE_DIGEST = {
    "ex1": "5342721041da011f665c", "ex2_beta1": "4fac3632eec4553ef52c", "ex2_beta_res": "f83777ee807930224d53",
    "ex2b": "fe8b9e0e2fd0487dfdae", "ex2c_beta_cap": "5f11fe2c121df94c3d6e", "ex2d_iinj": "6dd41659d7530a564eb1",
    "ex2d_vin": "98a40d23d75f686cbb63", "ex3": "d3ec485f6066073def4d", "ex3_no_cc": "fb793f5d9c0fb695267c",
    "ex7": "4f1743a451682ebed49e", "ex7b_cm": "86fa20031e16e85e0729", "ex7b_dm": "a70337dd27fd7d19c205",
    "ex7c": "c6a6ac62cb37b849c86d",
}


@pytest.mark.parametrize("name", sorted(_no_rhp_cases()))
def test_no_rhp_bit_identical_to_pre_premise_engine_i17(name):
    la = _no_rhp_cases()[name]()
    assert PM_RHP not in codes(la.undefined)
    assert name in PRE_PREMISE_DIGEST
    assert _digest(la) == PRE_PREMISE_DIGEST[name], name


def test_rhp_zero_and_origin_pole_do_not_trigger_precondition():
    """문턱(3.10): Re > 0 엄격, 극점만. 예 3 은 우반면 영점 +gm2/Cc 가 있어도 PM 값(폐형식), 예 2c 의 용량 전용 노드 원점 극점(0j)은
    우반면으로 세지 않는다(PM 폐형식 값)."""
    (r,) = solve_responses((ex3_miller(),))
    f = Factor(r, 0)
    assert any(complex(z).real > 0 for z in f.zeros) and all(complex(p).real <= 0 for p in f.poles)   # 입력 확인
    la = analyze_loop((f,))
    assert la.phase_margin_deg == pytest.approx(closed_miller()["pm_deg"], rel=R)
    ra, rc = solve_responses((ex2_amp(), ex2c_beta_cap()))
    fc = Factor(rc, 0)
    assert any(complex(p) == 0j for p in fc.poles)                    # 입력 확인: 원점 극점(정확히 0j, 3.4)
    la = analyze_loop((Factor(ra, 0), fc))
    assert la.phase_margin_deg == pytest.approx(closed_single_pole_loop(0.25)[3], rel=R)
    assert PM_RHP not in codes(la.undefined)
