"""`metric_resolutions` (metric 분해능 -- LUT 불확실성 1차 최악 전파와 MNA 사후 오차의 최댓값) -- metrics CONTRACT 9.3·9.5.
(+ 9.6 R-1~R-6·R-8·R-9)

기대값 출처:
- 9.5 폐형식(이 파일에서 다시 계산): 예 7 + ε 0.02 의 gain·UGF·PM·GBW, 예 2 rout 2000 Ω, 예 6 ratio(MOS 없음 -> lut 0).
- R-2 차분: (a) Miller 변형(Factor) -- conftest 독립 MNA `ref_system` 을 파라미터마다 p(1 ± h) 로 다시 세워 gain·UGF(brentq)·GBW·PM(조밀
  격자 위상 언랩)을 test 쪽에서 계산한 중심 차분. (b) 예 7 변형 β 루프(ProbeFactor) -- 계약 R-2 문장 그대로 엔진 순방향 경로
  (`build_mna`·`solve_responses`·`probe_factor`·`analyze_loop`)를 다시 부른 차분 + UGF·PM 은 conftest 독립 Middlebrook
  (`ref_middlebrook`, 오라클 이중 주입 배치)의 차분으로도 대조.
- 기대 lut = Σ_p |∂q/∂p|·ε_owner·|p| (9.3 결합 규칙 -- 부호 독립 최악 선형).

허용치: R-1 폐형식 상대 1e-9, R-2 차분 상대 1e-6(계약), R-6 재번호 상대 1e-12(계약). R-3 의 'ε 두 배 -> 정확히 두 배' 는 Δp = ε·|p| 와
Σ|g|·Δp 가 모두 2 의 거듭제곱 배율에 대해 정확한 연산이라 비트 단위. 몫별 합(ε1, 0) + (0, ε2) 는 P 개 비음수 항 합의 재배열 오차
(P − 1)·eps 상대.
"""
from __future__ import annotations

import math

import numpy as np
import pytest
from scipy.optimize import brentq

from gmid_engine.metrics import (
    Excitation,
    Factor,
    LoopCut,
    ParameterSet,
    Resolution,
    ResponseSensitivity,
    Sense,
    analyze_loop,
    build_mna,
    cut_circuit,
    lut_parameters,
    metric_resolutions,
    mos_stamps,
    output_resistance,
    probe_factor,
    response_ratio,
    response_sensitivity,
    solve_responses,
    two_terminal_stamps,
)

from .conftest import (
    DB_PER_NEPER,
    EPS,
    EX7,
    EX8,
    EX7_CAP,
    EX7_MOS12,
    EX7V_CAP,
    EX7V_MOS,
    FD_RTOL,
    MILLER_V_CAP,
    MILLER_V_COLS,
    MILLER_V_MOS,
    MILLER_V_RES,
    MILLER_V_SENSE,
    MOS_IX,
    TWO_PI,
    FD_H,
    circuit12,
    count_calls,
    ex1_rc,
    ex6_ratio,
    miller_v_system,
    mos_t,
    perturbed,
    ref_middlebrook,
    ref_system,
)

R1_RTOL = 1e-9
R6_RTOL = 1e-12
LOOP_FIELDS = ("gain_db", "ugf_hz", "phase_margin_deg", "gbw_hz")
RENUM7 = {0: 17, 2: 30, 3: 8}


# ---------------------------------------------------------------- 분석 생성

def _loop(mos, cap, nm=None, weights=(1.0,)):
    """예 7 꼴 β 루프: Cf(capacitors index 1) b 단자 절단 -> ProbeFactor -> analyze_loop. 반환 (회로, 분석, 출처)."""
    ck = circuit12(mos, (), cap, (0,), nm)
    cut = cut_circuit(ck, (LoopCut("capacitor", 1, "b"),))
    (resp,) = solve_responses((build_mna(cut.circuit, cut.excitations, cut.senses),))
    pf = probe_factor(resp, cut.pairs, weights)
    return ck, analyze_loop((pf,)), (pf,)


def _miller(mos=MILLER_V_MOS, nm=None):
    ck, sysm = miller_v_system(mos, nm)
    (resp,) = solve_responses((sysm,))
    f = Factor(resp, 0, 0)
    return ck, analyze_loop((f,)), (f,)


def _ex2():
    ck = circuit12((mos_t(2, 1, 0, 0, 1e-3, 0.0, 1e-5),), (), ((2, 0, 1e-12),))
    sysm = build_mna(ck, (Excitation("vin", voltages=((1, 1.0),)), Excitation("iout", currents=((2, 1.0),))), (Sense(2),))
    (resp,) = solve_responses((sysm,))
    return ck, output_resistance(resp, 1), resp


def _by_q(res):
    return {r.quantity: r for r in res}


def closed_ex7_resolution(eps):
    """9.5 폐형식(예 7 + ε): T(s) = gm·β/(gds + s·Ceff). 반환 {필드: lut}."""
    gm, gds, cl, cf, cs = EX7["gm"], EX7["gds"], EX7["cl"], EX7["cf"], EX7["cs"]
    beta = cf / (cf + cs)
    ceff = cl + cf * cs / (cf + cs)
    t0 = gm * beta / gds
    ugf = math.sqrt((gm * beta) ** 2 - gds ** 2) / ceff / TWO_PI
    return {"gain_db": 2.0 * DB_PER_NEPER * eps,
            "ugf_hz": ugf * eps * (t0 * t0 + 1.0) / (t0 * t0 - 1.0),
            "phase_margin_deg": math.degrees(2.0 * eps / math.sqrt(t0 * t0 - 1.0)),
            "gbw_hz": eps * gm * beta / (TWO_PI * ceff)}


# ---------------------------------------------------------------- R-1: 예 7 폐형식

def test_r1_example7_closed_form():
    """예 7 + ε 0.02: 네 필드 lut = 9.5 폐형식(0.3474355855 dB, 455820.7769 Hz, 0.0917466739°, 454728.4088 Hz), value = lut,
    numeric ≤ lut(9.5: 수치 몫이 LUT 몫보다 작다)."""
    ck, la, src = _loop(EX7_MOS12, EX7_CAP)
    res = metric_resolutions(la, src, lut_parameters(ck, (0.02,)))
    assert all(isinstance(r, Resolution) for r in res)
    assert tuple(r.quantity for r in res) == LOOP_FIELDS
    exp = closed_ex7_resolution(0.02)
    # 계약에 적힌 값과 test 쪽 재계산이 같은지(입력 확인)
    for q, v, dec in (("gain_db", 0.3474355855, 10), ("ugf_hz", 455820.7769, 4), ("phase_margin_deg", 0.0917466739, 10),
                      ("gbw_hz", 454728.4088, 4)):
        assert abs(exp[q] - v) <= 0.5 * 10.0 ** -dec, (q, exp[q], v)       # 계약 표기 자릿수의 반 단위
    for r in res:
        assert abs(r.lut - exp[r.quantity]) <= R1_RTOL * exp[r.quantity], (r, exp[r.quantity])
        assert r.value == r.lut
        assert 0.0 <= r.numeric <= r.lut


def test_example2_rout_closed_form():
    """9.5 예 2 rout + ε 0.02: rout = 1/gds = 1e5 Ω(노드 1 은 구동 고정 노드라 gm 무관) -> lut = ε·rout = 2000 Ω."""
    ck, ro, resp = _ex2()
    (r,) = metric_resolutions(ro, resp, lut_parameters(ck, (0.02,)))
    assert r.quantity == "rout_ohm"
    assert abs(r.lut - 0.02 / 1e-5) <= R1_RTOL * 2000.0
    assert r.value == r.lut and 0.0 <= r.numeric <= r.lut


def test_example6_ratio_no_mos_lut_zero():
    """9.5 예 6(MOS 없음): params () -> lut = 0.0, value = numeric."""
    from gmid_engine.metrics import SmallSignalCircuit, Resistor
    ck = SmallSignalCircuit(resistors=(Resistor(1, 2, 1e3), Resistor(2, 3, 1e4)), ac_ground=(0,))
    (resp,) = solve_responses((ex6_ratio(),))
    rr = response_ratio(resp, 0, 1)
    (r,) = metric_resolutions(rr, resp, lut_parameters(ck, ()))
    assert r.quantity == "ratio_db" and r.lut == 0.0
    assert r.numeric >= 0.0 and r.value == r.numeric


# ---------------------------------------------------------------- R-5·R-4: 정의 불가·미정

def test_r5_undefined_fields_absent_example1():
    """예 1: ugf·pm 은 dc_not_above_level(값 None) -> 결과에 없다, gain·gbw 만(MOS 없음 -> lut 0)."""
    from gmid_engine.metrics import Capacitor, Resistor, SmallSignalCircuit
    ck = SmallSignalCircuit(resistors=(Resistor(1, 2, 1e3),), capacitors=(Capacitor(2, 0, 1e-9),), ac_ground=(0,))
    (resp,) = solve_responses((ex1_rc(),))
    f = Factor(resp, 0, 0)
    la = analyze_loop((f,))
    assert la.ugf_hz is None and la.phase_margin_deg is None          # 입력 확인
    res = metric_resolutions(la, (f,), lut_parameters(ck, ()))
    assert tuple(r.quantity for r in res) == ("gain_db", "gbw_hz")
    assert all(r.lut == 0.0 and r.value == r.numeric for r in res)


def _gain_lut_cross_pair(gx2, eps):
    """예 8·8a·8b 의 gain lut 폐형식(9.3 결합 규칙). T0 ∝ gm1·gds3/(gm2·gm3 − (gds1 + gds2)·gds3)(8a·8b 는 β 배 -- 용량은 LUT
    파라미터 아님). ∂ln|T0|/∂ln p 의 절댓값 합 = 1(gm1) + 3·k(gds3·gm2·gm3) + 2·(k − 1)/2(gds1·gds2), k = gm2·gm3/|D|,
    D = gm2·gm3 − 2·gds²(같은 gds). lut = D_dB·ε·합."""
    gds = EX8["gds"]
    dd = abs(gx2 - 2.0 * gds * gds)
    k = gx2 / dd
    s = 1.0 + 3.0 * k + 2.0 * (gds * gds / dd)
    return DB_PER_NEPER * eps * s


def test_r5_pm_undefined_by_rhp_precondition_absent_ex8():
    """3.10 PM 전제 + 9.3/R-5: 예 8 은 phase_margin_deg None(loop_open_rhp_poles) -> 분해능 결과에 PM 이 없다. 나머지 필드는 그대로
    (gain lut 폐형식: 합 1 + 3·1.2 + 2·0.1 = 4.8)."""
    from .conftest import closed_ex8, ex8_system
    ck, sysm = ex8_system()
    (resp,) = solve_responses((sysm,))
    f = Factor(resp, 0, 0)
    la = analyze_loop((f,))
    assert la.phase_margin_deg is None and la.ugf_hz is not None       # 입력 확인
    res = _by_q(metric_resolutions(la, (f,), lut_parameters(ck, (0.02, 0.02, 0.02))))
    assert tuple(res) == ("gain_db", "ugf_hz", "gbw_hz")
    g = _gain_lut_cross_pair(EX8["gx2"], 0.02)
    assert abs(g - DB_PER_NEPER * 0.02 * 4.8) <= 1e-12 * g              # 손계산 합 4.8
    assert abs(res["gain_db"].lut - g) <= R1_RTOL * g
    for r in res.values():
        assert r.value is not None and r.value == max(r.lut, r.numeric)
    assert closed_ex8()["ugf_hz"] == pytest.approx(la.ugf_hz, rel=1e-9)


@pytest.mark.parametrize("which", ["8a", "8b"])
def test_r5_pm_undefined_by_rhp_precondition_absent_probe(which):
    """예 8a(ProbeFactor, 폐루프 안정)·8b(|T0| 0.5 -> UGF 도 None): PM 분해능 없음, gain lut 폐형식(β 는 용량비 -- LUT 밖)."""
    from .conftest import EX7_CUT, ex8a_parts, probe_of, circuit_of
    gx2 = EX8["gx2"] if which == "8a" else EX8["gx2_8b"]
    parts = ex8a_parts(gx2)
    _, pf, _ = probe_of(parts, EX7_CUT)
    la = analyze_loop((pf,))
    assert la.phase_margin_deg is None                                 # 입력 확인
    res = _by_q(metric_resolutions(la, (pf,), lut_parameters(circuit_of(*parts), (0.02, 0.02, 0.02))))
    assert "phase_margin_deg" not in res
    assert ("ugf_hz" in res) == (which == "8a")
    g = _gain_lut_cross_pair(gx2, 0.02)
    assert abs(res["gain_db"].lut - g) <= R1_RTOL * g


def test_r4_undetermined_epsilon_value_none_numeric_kept():
    """ε None -> 모든 필드 value·lut None, numeric 은 값(ε 와 무관 -- ε 가 있을 때와 같다). 예외 0."""
    ck, la, src = _loop(EX7_MOS12, EX7_CAP)
    none = metric_resolutions(la, src, lut_parameters(ck, (None,)))
    some = metric_resolutions(la, src, lut_parameters(ck, (0.02,)))
    assert tuple(r.quantity for r in none) == LOOP_FIELDS
    for a, b in zip(none, some):
        assert a.value is None and a.lut is None
        assert a.numeric is not None and a.numeric == b.numeric


def test_r4_one_mos_undetermined_in_two():
    """두 MOS 중 하나만 None 이어도 value·lut None(R-4)."""
    ck, la, src = _miller()
    for r in metric_resolutions(la, src, lut_parameters(ck, (0.01, None))):
        assert r.value is None and r.lut is None and r.numeric is not None


def test_rout_undetermined():
    ck, ro, resp = _ex2()
    (r,) = metric_resolutions(ro, resp, lut_parameters(ck, (None,)))
    assert r.value is None and r.lut is None and r.numeric is not None


# ---------------------------------------------------------------- R-3: ε 선형·MOS 몫

@pytest.mark.parametrize("case", ["ex7", "miller", "rout"])
def test_r3_doubling_epsilon_doubles_resolution_exactly(case):
    if case == "ex7":
        ck, a, src = _loop(EX7_MOS12, EX7_CAP)
        e1, e2 = (0.02,), (0.04,)
    elif case == "miller":
        ck, a, src = _miller()
        e1, e2 = (0.01, 0.03), (0.02, 0.06)
    else:
        ck, a, src = _ex2()
        e1, e2 = (0.02,), (0.04,)
    r1 = metric_resolutions(a, src, lut_parameters(ck, e1))
    r2 = metric_resolutions(a, src, lut_parameters(ck, e2))
    assert len(r1) == len(r2) > 0
    for x, y in zip(r1, r2):
        assert x.quantity == y.quantity
        assert y.lut == 2.0 * x.lut, (x, y)
        assert y.numeric == x.numeric
        assert y.value == max(y.lut, y.numeric)


def test_r3_per_mos_share():
    """한 MOS 의 ε 만 바꾸면 그 MOS 몫만 바뀐다: lut(ε1, ε2) = lut(ε1, 0) + lut(0, ε2), lut(ε1, 2ε2) − lut(ε1, ε2) = lut(0, ε2)."""
    ck, a, src = _miller()
    P = 12

    def lut(e):
        return {r.quantity: r.lut for r in metric_resolutions(a, src, lut_parameters(ck, e))}

    both, m1, m2, both2 = lut((0.01, 0.03)), lut((0.01, 0.0)), lut((0.0, 0.03)), lut((0.01, 0.06))
    for q in both:
        assert m1[q] > 0.0 and m2[q] > 0.0
        assert abs(both[q] - (m1[q] + m2[q])) <= (P - 1) * EPS * both[q] * 2, q
        assert abs((both2[q] - both[q]) - m2[q]) <= (P - 1) * EPS * both2[q] * 4, q


# ---------------------------------------------------------------- R-2: 차분 대조

def _metrics_from_h(h, h0):
    """|H| 교차·위상 지연을 test 쪽에서 계산: gain = 20log|H0|, UGF·f3dB = brentq(첫 교차 칸), PM = 180° − 지연(조밀 격자 언랩)."""
    a0 = abs(h0)
    grid = np.logspace(0, 12, 12 * 40 + 1)

    def cross(level):
        prev = 0.0
        for w in grid:
            if abs(h(w)) <= level:
                lo = prev if prev > 0.0 else w / 10.0
                return brentq(lambda x: abs(h(x)) - level, lo, w, xtol=1e-300, rtol=4 * EPS, maxiter=500)
            prev = w
        raise AssertionError("no crossing")

    wu = cross(1.0)
    w3 = cross(a0 / math.sqrt(2.0))
    pts = np.concatenate(([0.0], grid[grid < wu], [wu]))
    ph = np.unwrap(np.array([math.atan2(z.imag, z.real) for z in [h0] + [h(w) for w in pts[1:]]]))
    lag = -(ph[-1] - ph[0])
    return {"gain_db": 20.0 * math.log10(a0), "ugf_hz": wu / TWO_PI, "phase_margin_deg": 180.0 - math.degrees(lag),
            "gbw_hz": a0 * w3 / TWO_PI}


def _miller_own(mos):
    def h(w):
        return ref_system(mos, MILLER_V_RES, MILLER_V_CAP, (0,), MILLER_V_COLS, MILLER_V_SENSE, w)[0, 0]
    return _metrics_from_h(h, h(0.0))


def _expected_lut(mos, eps, metric_fn, fields):
    """Σ_p |∂q/∂p|·ε_k·|p| -- ∂q/∂p = 중심 차분(파라미터마다 p(1 ± h) 로 다시 세워 푼다, 한 섭동당 모든 필드를 한 번에)."""
    out = {q: 0.0 for q in fields}
    for k, t in enumerate(mos):
        for name in ("gm", "gmb", "gds", "cgs", "cgd", "cgb"):
            p = t[MOS_IX[name]]
            if p == 0.0:
                continue
            pp, pm = p * (1.0 + FD_H), p * (1.0 - FD_H)
            hi, lo = metric_fn(perturbed(mos, k, name, 1.0 + FD_H)), metric_fn(perturbed(mos, k, name, 1.0 - FD_H))
            for q in fields:
                out[q] += abs((hi[q] - lo[q]) / (pp - pm)) * eps[k] * abs(p)
    return out


def test_r2_miller_variant_against_independent_mna():
    """Miller 변형(gmb·cgs·cgd·음의 cgb, 두 MOS 다른 ε): lut = 독립 MNA 중심 차분의 Σ|∂q/∂p|·Δp (상대 ≤ 1e-6).
    값 자체도 독립 계산과 같다(입력 확인)."""
    eps = (0.01, 0.03)
    ck, la, src = _miller()
    own = _miller_own(MILLER_V_MOS)
    for q in LOOP_FIELDS:
        assert abs(getattr(la, q) - own[q]) <= R1_RTOL * abs(own[q]), (q, getattr(la, q), own[q])
    res = _by_q(metric_resolutions(la, src, lut_parameters(ck, eps)))
    exp = _expected_lut(MILLER_V_MOS, eps, _miller_own, LOOP_FIELDS)
    for q in LOOP_FIELDS:
        assert abs(res[q].lut - exp[q]) <= FD_RTOL * exp[q], (q, res[q].lut, exp[q])
        assert res[q].value == res[q].lut and res[q].numeric <= res[q].lut


def _loop_engine(mos):
    _, la, _ = _loop(mos, EX7V_CAP)
    return {q: getattr(la, q) for q in LOOP_FIELDS}


def _mos_caps_as_capacitors(mos):
    """MOS 용량을 2단자 커패시터 tuple 로(독립 Middlebrook 입력) -- Cf 의 index 1 을 지키려고 원래 커패시터 뒤에 붙인다."""
    out = []
    for d, g, s, b, gm, gmb, gds, cgs, cgd, cgb, cdb, csb in mos:
        for a, bb, c in ((g, s, cgs), (g, d, cgd), (g, b, cgb), (d, b, cdb), (s, b, csb)):
            if c:
                out.append((a, bb, c))
    return tuple(out)


def _loop_own(mos):
    """독립 Middlebrook(ω > 0)으로 UGF·PM: T(0) 이 실수 양수라고 두고(가정이 틀리면 엔진 값과의 대조가
    깨진다), 작은 ω 에서 위상 ≈ 0 부터 언랩."""
    m7 = tuple(t[:7] for t in mos)
    cap = EX7V_CAP + _mos_caps_as_capacitors(mos)

    def t(w):
        return ref_middlebrook(m7, (), cap, (0,), (("capacitor", 1, "b"),), (1.0,), w)["T"]

    grid = np.logspace(0, 12, 12 * 40 + 1)
    prev = None
    for w in grid:
        if abs(t(w)) <= 1.0:
            wu = brentq(lambda x: abs(t(x)) - 1.0, prev, w, xtol=1e-300, rtol=4 * EPS, maxiter=500)
            break
        prev = w
    pts = np.concatenate((grid[grid < wu], [wu]))
    ph = np.unwrap(np.array([math.atan2(z.imag, z.real) for z in (t(w) for w in pts)]))
    return {"ugf_hz": wu / TWO_PI, "phase_margin_deg": 180.0 + math.degrees(ph[-1])}


def test_r2_beta_loop_variant_against_central_difference():
    """예 7 변형 β 루프(ProbeFactor, gmb·cgs·cgd·음의 cgb·cdb): lut = 엔진 순방향 경로를 파라미터마다 다시 부른 중심 차분(R-2 문장),
    UGF·PM 은 독립 Middlebrook 의 차분과도 같다(상대 ≤ 1e-6)."""
    eps = (0.02,)
    ck, la, src = _loop(EX7V_MOS, EX7V_CAP)
    own = _loop_own(EX7V_MOS)
    for q in ("ugf_hz", "phase_margin_deg"):
        assert abs(getattr(la, q) - own[q]) <= R1_RTOL * abs(own[q]), (q, getattr(la, q), own[q])
    res = _by_q(metric_resolutions(la, src, lut_parameters(ck, eps)))
    exp = _expected_lut(EX7V_MOS, eps, _loop_engine, LOOP_FIELDS)
    exp_own = _expected_lut(EX7V_MOS, eps, _loop_own, ("ugf_hz", "phase_margin_deg"))
    for q in LOOP_FIELDS:
        assert abs(res[q].lut - exp[q]) <= FD_RTOL * exp[q], (q, res[q].lut, exp[q])
        assert res[q].numeric <= res[q].lut
    for q in exp_own:
        assert abs(res[q].lut - exp_own[q]) <= FD_RTOL * exp_own[q], (q, res[q].lut, exp_own[q])


def test_r2_rout_against_central_difference():
    """rout(예 2 + 소자 용량·gmb 변형): lut = 독립 MNA DC 극한 rout 의 중심 차분 Σ|∂rout/∂p|·Δp."""
    mos = (mos_t(2, 1, 4, 0, 1e-3, 2e-4, 1e-5, cgs=0.2e-12, cgd=0.1e-12, cgb=-0.05e-12),)
    res_ = ((4, 0, 2e3),)
    cap = ((2, 0, 1e-12),)
    ck = circuit12(mos, res_, cap)
    sysm = build_mna(ck, (Excitation("vin", voltages=((1, 1.0),)), Excitation("iout", currents=((2, 1.0),))), (Sense(2),))
    (resp,) = solve_responses((sysm,))
    ro = output_resistance(resp, 1)
    cols = ({"v": {1: 1.0}, "i": {}, "q": {}}, {"v": {}, "i": {2: 1.0}, "q": {}})

    def rout(m):
        return {"rout_ohm": ref_system(m, res_, cap, (0,), cols, ((2, None),), 0.0)[0, 1].real}

    assert abs(ro.rout_ohm - rout(mos)["rout_ohm"]) <= R1_RTOL * ro.rout_ohm
    (r,) = metric_resolutions(ro, resp, lut_parameters(ck, (0.03,)))
    exp = _expected_lut(mos, (0.03,), rout, ("rout_ohm",))["rout_ohm"]
    assert abs(r.lut - exp) <= FD_RTOL * exp, (r.lut, exp)


# ---------------------------------------------------------------- R-6·R-8·R-9·memo

@pytest.mark.parametrize("case", ["ex7v", "miller"])
def test_r6_renumbering_invariance(case):
    if case == "ex7v":
        a = _loop(EX7V_MOS, EX7V_CAP)
        b = _loop(EX7V_MOS, EX7V_CAP, nm=dict(RENUM7))
        eps = (0.02,)
    else:
        a = _miller()
        b = _miller(nm={0: 17, 1: 4, 2: 30, 3: 8, 4: 11})
        eps = (0.01, 0.03)
    ra = metric_resolutions(a[1], a[2], lut_parameters(a[0], eps))
    rb = metric_resolutions(b[1], b[2], lut_parameters(b[0], eps))
    assert tuple(r.quantity for r in ra) == tuple(r.quantity for r in rb) == LOOP_FIELDS
    for x, y in zip(ra, rb):
        assert abs(x.lut - y.lut) <= R6_RTOL * max(x.lut, y.lut), (x, y)
        assert abs(x.value - y.value) <= R6_RTOL * max(x.value, y.value)


def test_r8_other_circuit_parameter_set_value_error():
    ck, la, src = _loop(EX7_MOS12, EX7_CAP)
    other = circuit12((mos_t(52, 51, 50, 50, 1e-3, 0.0, 1e-5),), (), ((52, 50, 1e-12),), ac_ground=(50,))
    with pytest.raises(ValueError):
        metric_resolutions(la, src, lut_parameters(other, (0.02,)))
    ck2, ro, resp = _ex2()
    with pytest.raises(ValueError):
        metric_resolutions(ro, resp, lut_parameters(other, (0.02,)))


@pytest.mark.parametrize("bad", ["analysis", "loop_source_response", "rout_source_tuple", "parameters"])
def test_r8_type_errors(bad):
    ck, la, src = _loop(EX7_MOS12, EX7_CAP)
    ck2, ro, resp = _ex2()
    ps, ps2 = lut_parameters(ck, (0.02,)), lut_parameters(ck2, (0.02,))
    with pytest.raises(TypeError):
        if bad == "analysis":
            metric_resolutions(resp, resp, ps2)
        elif bad == "loop_source_response":
            metric_resolutions(la, src[0].response, ps)
        elif bad == "rout_source_tuple":
            metric_resolutions(ro, (resp,), ps2)
        else:
            metric_resolutions(la, src, tuple(ps.params))


def test_r8_negative_check_matching_inputs_ok():
    ck, la, src = _loop(EX7_MOS12, EX7_CAP)
    assert len(metric_resolutions(la, src, lut_parameters(ck, (0.02,)))) == 4
    assert isinstance(lut_parameters(ck, (0.02,)), ParameterSet)


def test_r9_no_stamp_or_assembly_calls():
    """metric_resolutions 동안 mos_stamps·two_terminal_stamps·build_mna 호출 0(단위 스탬프는 lut_parameters 에서 1회)."""
    ck, la, src = _loop(EX7V_MOS, EX7V_CAP)
    ps = lut_parameters(ck, (0.02,))
    ck2, ro, resp = _ex2()
    ps2 = lut_parameters(ck2, (0.02,))
    with count_calls(mos_stamps, two_terminal_stamps, build_mna) as n:
        metric_resolutions(la, src, ps)
        metric_resolutions(ro, resp, ps2)
    assert n == {"mos_stamps": 0, "two_terminal_stamps": 0, "build_mna": 0}


def test_memo_shares_adjoint_solves():
    """9.3 memo: 부르는 쪽 dict((id(계), ω) -> ResponseSensitivity). 같은 memo 로 다시 부르면 response_sensitivity 호출 0, 결과 같음.
    memo 없이 부른 결과와도 같다."""
    ck, la, src = _loop(EX7V_MOS, EX7V_CAP)
    ps = lut_parameters(ck, (0.02,))
    memo = {}
    first = metric_resolutions(la, src, ps, memo)
    assert memo and all(isinstance(k, tuple) and len(k) == 2 and isinstance(v, ResponseSensitivity)
                        for k, v in memo.items())
    with count_calls(response_sensitivity) as n:
        again = metric_resolutions(la, src, ps, memo)
    assert n == {"response_sensitivity": 0}
    assert again == first
    assert metric_resolutions(la, src, ps) == first
