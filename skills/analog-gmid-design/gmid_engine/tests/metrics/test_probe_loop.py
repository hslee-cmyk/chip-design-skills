"""CONTRACT 3.17·3.10·I-12~I-16·예 7/7b/7c: probe_factor -- 절단 회로 계 하나의 응답에서 Middlebrook 이중 주입
T = (Tv·Ti − 1)/(Tv + Ti + 2) 를 격자 위 samples·T 극점/영점·정의 불가 값으로 낸다.

기대값 출처(피검 함수 아님):
- 폐형식 되돌림 비(conftest `closed_ex7`·`closed_ex7b`, 이 파일 `_rr_resistive`).
- test 쪽 독립 Middlebrook 구현(conftest `ref_middlebrook`: 절단 회로를 직접 만들고 프로브 전압원·전류원을 MNA 에 넣어 두 실험).
- 손계산(예 7c·특이 예).
격자 위 원하는 ω 를 얻으려고 같은 solve_responses 에 RC 계(극점 = 원하는 ω)를 함께 넣는다(3.6 공유 격자 = 모든 계 근의 합집합).
"""
import math

import numpy as np
import pytest

from gmid_engine.metrics import (
    Capacitor,
    Excitation,
    Factor,
    LoopCut,
    MosSmallSignal,
    ProbeFactor,
    Resistor,
    Sense,
    SmallSignalCircuit,
    analyze_loop,
    build_mna,
    cut_circuit,
    metric_value,
    probe_factor,
    solve_responses,
)

from .conftest import (
    EX7,
    EX7_CUT,
    EX7B_CUTS,
    STAMP_FUNCS,
    TWO_PI,
    circuit_of,
    closed_ex7,
    closed_ex7b,
    codes,
    count_calls,
    ex2_amp,
    ex2_beta_res,
    ex2c_beta_cap,
    ex7_parts,
    ex7b_parts,
    ref_middlebrook,
)

EPS = np.finfo(float).eps
I12_REL = 1e-14          # I-12: '차원·eps 규모(실측 ≤ 3.3e-15)' -- 절단 계 미지수 3~4 개 × eps ≈ 1e-15, 여유 10배
METRIC_REL = 1e-12       # gain·UGF·PM: 5절 '상대오차 ≤ 6.3e-12'(예 7 실측 ≤ 3.3e-16)
FORCE_OMEGAS = (1e3, 1e6, 1e8, 1e9)   # 예 7 비교점(1e7 은 아래 ex2_amp 극점이 넣는다)


def _lc(cuts):
    return tuple(LoopCut(k, i, t) for k, i, t in cuts)


def _rc_pole(w0):
    """극점 −w0 하나인 RC 계(격자에 w0 를 넣기 위한 보조 계)."""
    ck = SmallSignalCircuit(resistors=(Resistor(1, 2, 1.0),), capacitors=(Capacitor(2, 0, 1.0 / w0),), ac_ground=(0,))
    return build_mna(ck, (Excitation("v", voltages=((1, 1.0),)),), (Sense(2),))


def _probe(parts, cuts, weights, extra=(), nm=None):
    """parts=(mos,res,cap) -> (cut, pf, extra responses). cut 회로 계 + extra 계를 한 번의 solve_responses 로."""
    ck = circuit_of(*parts, nm=nm)
    cut = cut_circuit(ck, _lc(cuts))
    s = build_mna(cut.circuit, cut.excitations, cut.senses)
    rs = solve_responses((s,) + tuple(extra))
    return cut, probe_factor(rs[0], cut.pairs, weights), rs[1:]


def _samples(pf):
    return np.asarray(pf.samples)


def _omegas(pf):
    return np.asarray(pf.response.omegas)


def _rel(a, b):
    return abs(a - b) / abs(b)


# =====================================================================================================================
# 예 7 -- 단일 절단, 용량 전용 절단 노드(전하 열 DC 극한), I-12
# =====================================================================================================================

def test_ex7_result_type_and_fields():
    cut, pf, _ = _probe(ex7_parts(), EX7_CUT, (1.0,))
    assert isinstance(pf, ProbeFactor)
    assert tuple(pf.pairs) == ((3, 4),) == tuple(cut.pairs)
    assert tuple(pf.weights) == (1.0,)
    assert _samples(pf).shape == _omegas(pf).shape
    assert pf.undefined == ()


def test_ex7_dc_charge_limit_exact():
    """n = 3, x = 4 모두 용량 전용 -> 전하 열 DC 해. T(0) = (gm/gds)·Cf/(Cf+Cs) = 25(정확), 근사 ω 없음."""
    _, pf, _ = _probe(ex7_parts(), EX7_CUT, (1.0,))
    om, t = _omegas(pf), _samples(pf)
    assert om[0] == 0.0
    assert abs(complex(t[0]) - 25.0) <= I12_REL * 25.0
    assert complex(t[0]).imag == 0.0


def test_ex7_grid_samples_match_closed_form_i12():
    """I-12: 격자 위 모든 ω(강제점 1e3·1e6·1e7·1e8·1e9 포함)에서 T 와 폐형식 상대오차 ≤ 차원·eps 규모."""
    ref = closed_ex7()
    _, pf, _ = _probe(ex7_parts(), EX7_CUT, (1.0,), extra=tuple(_rc_pole(w) for w in FORCE_OMEGAS) + (ex2_amp(),))
    om, t = _omegas(pf), _samples(pf)
    for w0 in FORCE_OMEGAS + (1e7,):
        assert np.min(np.abs(om - w0)) <= 1e-9 * w0, (w0, om)         # 강제점이 격자에 들어왔다
    worst = 0.0
    for w, v in zip(om, t):
        e = ref["t"](w) if w > 0 else ref["t0"]
        worst = max(worst, _rel(complex(v), e))
    assert worst <= I12_REL, worst


def test_ex7_grid_samples_match_independent_middlebrook():
    """test 쪽 독립 Middlebrook(프로브 전압원·전류원 두 실험)과 같은 식: ω > 0 격자 점마다 일치."""
    mos, res, cap = ex7_parts()
    _, pf, _ = _probe((mos, res, cap), EX7_CUT, (1.0,), extra=tuple(_rc_pole(w) for w in FORCE_OMEGAS))
    for w, v in zip(_omegas(pf), _samples(pf)):
        if w == 0.0:
            continue
        ref = ref_middlebrook(mos, res, cap, cuts=EX7_CUT, weights=(1.0,), omega=w)
        assert ref["pairs"] == ((3, 4),)
        assert _rel(complex(v), ref["T"]) <= 1e-12


def test_ex7_tv_ti_identity_by_independent_probe():
    """계약 예 7 의 Tv(0) = A0 + Cs/Cf = 103, Ti(0) = (A0+1)·Cf/Cs = 101/3 -- 독립 구현이 같은 Tv·Ti 를 내는지(오라클 자기 확인)
    그리고 그 둘의 조합이 T(0) = 25."""
    mos, res, cap = ex7_parts()
    ref = ref_middlebrook(mos, res, cap, cuts=EX7_CUT, weights=(1.0,), omega=1e-3)   # ω/ω_p ≈ 2e-10
    assert ref["Tv"].real == pytest.approx(103.0, rel=1e-9)
    assert ref["Ti"].real == pytest.approx(101.0 / 3.0, rel=1e-9)
    tv, ti = 103.0, 101.0 / 3.0
    assert (tv * ti - 1.0) / (tv + ti + 2.0) == pytest.approx(25.0, rel=1e-15)


def test_ex7_analyze_loop_metrics():
    """예 7 기대: gain 27.9588001734 dB, UGF = ω_p·√624/2π = 22718224.0239 Hz, PM = 180° − atan√624 = 92.292442776°."""
    ref = closed_ex7()
    assert ref["ugf_hz"] == pytest.approx(22718224.0239, rel=1e-11)       # 계약 숫자 = 폐형식
    assert ref["pm_deg"] == pytest.approx(92.292442776, rel=1e-11)
    _, pf, _ = _probe(ex7_parts(), EX7_CUT, (1.0,))
    la = analyze_loop((pf,))
    assert la.undefined == ()
    assert la.gain_db == pytest.approx(27.9588001734, rel=1e-11)
    assert la.gain_db == pytest.approx(ref["gain_db"], rel=METRIC_REL)
    assert la.ugf_hz == pytest.approx(ref["ugf_hz"], rel=METRIC_REL)
    assert la.phase_margin_deg == pytest.approx(ref["pm_deg"], rel=METRIC_REL)
    r = metric_value("pm_ss_deg", la)
    assert r.value == pytest.approx(ref["pm_deg"], rel=METRIC_REL) and r.undefined == ()


def _reconstruct(pf, t0, w):
    """poles·zeros 로 T(jω) 재구성: 원점 근은 같은 수로 상쇄돼야 하고(T(0) 유한), 나머지 T0·Π(1 − s/z)/Π(1 − s/p)."""
    p = [complex(x) for x in pf.poles]
    z = [complex(x) for x in pf.zeros]
    po = [x for x in p if x == 0j]
    zo = [x for x in z if x == 0j]
    assert len(po) == len(zo), (pf.poles, pf.zeros)
    s = 1j * w
    num = np.prod([1.0 - s / x for x in z if x != 0j]) if any(x != 0j for x in z) else 1.0
    den = np.prod([1.0 - s / x for x in p if x != 0j]) if any(x != 0j for x in p) else 1.0
    return t0 * num / den


def _single_pole_case(name):
    """(parts, cuts, weights, t0, ω_p) -- 모두 단일 극 T(s) = T0/(1 + s/ω_p) 인 경우(폐형식)."""
    p = EX7
    if name == "ex7":
        r = closed_ex7()
        return ex7_parts(), EX7_CUT, (1.0,), r["t0"], r["wp"]
    if name == "resistive":
        g2 = p["gds"] + 1.0 / (RF + RS)
        return _resistive_parts(), (("resistor", 0, "b"),), (1.0,), p["gm"] / g2 * RS / (RF + RS), g2 / p["cl"]
    mode = "dm" if name == "ex7b_dm" else "cm"
    r = closed_ex7b(mode)
    return ex7b_parts(), EX7B_CUTS, ((0.5, -0.5) if mode == "dm" else (0.5, 0.5)), r["t0"], r["wp"]


@pytest.mark.parametrize("name", ["ex7", "resistive", "ex7b_dm", "ex7b_cm"])
def test_poles_zeros_describe_t(name):
    """3.17 'T 의 poles·zeros'(상단 괄호용): −ω_p 가 극점에 있고, 근으로 재구성한 T 가 단일 극 폐형식과 같다
    (1e3~1e10 rad/s, 상쇄되는 극·영점 쌍은 허용 -- 재구성에서 서로 지워진다)."""
    parts, cuts, w, t0, wp = _single_pole_case(name)
    _, pf, _ = _probe(parts, cuts, w)
    assert min(abs(complex(p) + wp) for p in pf.poles) <= 1e-9 * wp, pf.poles
    assert all(complex(p).real <= 0.0 for p in pf.poles), pf.poles       # 안정 단일 극 T 에 우반면 극점 없음
    for om in np.geomspace(1e3, 1e10, 29):
        exp = t0 / (1.0 + 1j * om / wp)
        assert _rel(_reconstruct(pf, t0, om), exp) <= 1e-8, (om, pf.poles, pf.zeros)


# =====================================================================================================================
# 전도 절단 노드(전류 열 DC 해) -- 저항 되먹임 CS, Middlebrook = 되돌림 비 (I-12 의 '단일 제어원 루프')
# =====================================================================================================================

RF, RS = 3e4, 1e4


def _resistive_parts():
    p = EX7
    return ((2, 3, 0, 0, p["gm"], 0.0, p["gds"]),), ((2, 3, RF), (3, 0, RS)), ((2, 0, p["cl"]),)


def _rr_resistive(w):
    """gm 되돌림 비 손계산: 드레인 노드 임피던스 Z2 = 1/(gds + 1/(Rf+Rs) + sCL), T = gm·Z2·Rs/(Rf+Rs)."""
    p = EX7
    z2 = 1.0 / (p["gds"] + 1.0 / (RF + RS) + 1j * w * p["cl"])
    return p["gm"] * z2 * RS / (RF + RS)


def test_resistive_cut_current_column_dc_and_grid():
    """절단 노드 n = 3(Rs·gate), x = 4(Rf) 모두 전도 -> ω = 0 은 전류 열 DC 해. 격자 전체에서 되돌림 비 폐형식과 같다."""
    _, pf, _ = _probe(_resistive_parts(), (("resistor", 0, "b"),), (1.0,),
                      extra=tuple(_rc_pole(w) for w in FORCE_OMEGAS))
    assert pf.undefined == ()
    om, t = _omegas(pf), _samples(pf)
    assert om[0] == 0.0
    for w, v in zip(om, t):
        assert _rel(complex(v), _rr_resistive(w)) <= 1e-13, w


def test_resistive_cut_matches_independent_middlebrook_over_omega():
    mos, res, cap = _resistive_parts()
    _, pf, _ = _probe((mos, res, cap), (("resistor", 0, "b"),), (1.0,), extra=tuple(_rc_pole(w) for w in FORCE_OMEGAS))
    for w, v in zip(_omegas(pf), _samples(pf)):
        if w > 0:
            ref = ref_middlebrook(mos, res, cap, cuts=(("resistor", 0, "b"),), weights=(1.0,), omega=w)
            assert _rel(complex(v), ref["T"]) <= 1e-12
            assert _rel(ref["T"], _rr_resistive(w)) <= 1e-12        # 독립 구현도 되돌림 비와 같다


def test_resistive_cut_analyze_loop_closed_form():
    p = EX7
    g2 = p["gds"] + 1.0 / (RF + RS)
    t0 = p["gm"] / g2 * RS / (RF + RS)
    wp = g2 / p["cl"]
    _, pf, _ = _probe(_resistive_parts(), (("resistor", 0, "b"),), (1.0,))
    la = analyze_loop((pf,))
    assert la.dc_value == pytest.approx(t0, rel=1e-13)
    assert la.ugf_hz == pytest.approx(wp * math.sqrt(t0 * t0 - 1.0) / TWO_PI, rel=METRIC_REL)
    assert la.phase_margin_deg == pytest.approx(180.0 - math.degrees(math.atan(math.sqrt(t0 * t0 - 1.0))), rel=METRIC_REL)


# =====================================================================================================================
# 예 7b -- 차동 절단 2개, 가중이 모드를 고른다 (I-13)
# =====================================================================================================================

@pytest.mark.parametrize("weights,mode", [((0.5, -0.5), "dm"), ((1.0, -1.0), "dm"), ((-0.5, 0.5), "dm"),
                                          ((0.5, 0.5), "cm"), ((1.0, 1.0), "cm")])
def test_ex7b_weights_select_mode(weights, mode):
    ref = closed_ex7b(mode)
    assert ref["t0"] == pytest.approx({"dm": 5.0, "cm": 25.0}[mode], rel=1e-15)
    cut, pf, _ = _probe(ex7b_parts(), EX7B_CUTS, weights)
    assert tuple(cut.pairs) == ((3, 14), (13, 15))
    t0 = complex(_samples(pf)[0])
    assert abs(t0 - ref["t0"]) <= 1e-13 * ref["t0"], t0
    la = analyze_loop((pf,))
    assert la.undefined == ()
    assert la.ugf_hz == pytest.approx(ref["ugf_hz"], rel=METRIC_REL)
    assert la.phase_margin_deg == pytest.approx(ref["pm_deg"], rel=METRIC_REL)


def test_ex7b_common_scale_invariance_i13():
    """I-13: (½, −½) 와 (1, −1) 의 T 가 같다(공통 배율 불변) -- 격자 전체."""
    _, a, _ = _probe(ex7b_parts(), EX7B_CUTS, (0.5, -0.5))
    _, b, _ = _probe(ex7b_parts(), EX7B_CUTS, (1.0, -1.0))
    assert np.array_equal(_omegas(a), _omegas(b))
    assert np.allclose(_samples(a), _samples(b), rtol=1e-13, atol=0)
    _, c, _ = _probe(ex7b_parts(), EX7B_CUTS, (-3.0, 3.0))
    assert np.allclose(_samples(a), _samples(c), rtol=1e-13, atol=0)


@pytest.mark.parametrize("weights", [(0.5, -0.5), (0.5, 0.5), (1.0, -0.25)])
def test_ex7b_matches_independent_middlebrook(weights):
    mos, res, cap = ex7b_parts()
    _, pf, _ = _probe((mos, res, cap), EX7B_CUTS, weights, extra=tuple(_rc_pole(w) for w in FORCE_OMEGAS))
    for w, v in zip(_omegas(pf), _samples(pf)):
        if w > 0:
            ref = ref_middlebrook(mos, res, cap, cuts=EX7B_CUTS, weights=weights, omega=w)
            assert ref["pairs"] == ((3, 14), (13, 15))
            assert _rel(complex(v), ref["T"]) <= 1e-12, w


# =====================================================================================================================
# 예 7c -- 섞인 절단(정의 불가 값, M7), 특이 프로브(loop_probe_singular), 예외 0 (I-10)
# =====================================================================================================================

def test_ex7c_mixed_charge_is_value_not_exception():
    _, pf, _ = _probe(ex7_parts(cs_resistor=True), EX7_CUT, (1.0,))
    t = _samples(pf)
    assert np.isnan(complex(t[0]).real) or np.isnan(complex(t[0]).imag)
    assert "loop_cut_mixed_charge" in codes(pf.undefined)
    assert all(u.category == "definitional" for u in pf.undefined if u.code == "loop_cut_mixed_charge")
    assert np.all(np.isfinite(t[1:]))                         # ω > 0 은 전류 열로 정의된다
    la = analyze_loop((pf,))
    r = metric_value("pm_ss_deg", la)
    assert r.value is None
    assert len(r.undefined) == 1
    u = r.undefined[0]
    assert (u.quantity, u.code, u.category) == ("phase_margin_deg", "loop_cut_mixed_charge", "definitional")


def test_ex7c_positive_omega_matches_independent_middlebrook():
    mos, res, cap = ex7_parts(cs_resistor=True)
    _, pf, _ = _probe((mos, res, cap), EX7_CUT, (1.0,), extra=tuple(_rc_pole(w) for w in FORCE_OMEGAS))
    for w, v in zip(_omegas(pf), _samples(pf)):
        if w > 0:
            assert _rel(complex(v), ref_middlebrook(mos, res, cap, cuts=EX7_CUT, omega=w)["T"]) <= 1e-12


def _singular_parts():
    """M = Pᵀ·Z·P = 0 인 저항 회로(손계산). 절단 Rf(2,3) 의 b(노드 3) -> x = 6.
    +1 A at 3, −1 A at x: v3 = R3 = 2; MA(d=5,g=3,gm=1): v5 = −gmA·R5·v3 = −2; MB(d=2,g=5,gm=2): 노드 2 KCL
    gmB·v5 + v2/R2 + 1 = 0 -> v2 = 3; v_x = v2 − Rf·1 = 2 -> M = v3 − v_x = 0 (정확한 2진 값)."""
    mos = ((5, 3, 0, 0, 1.0, 0.0, 0.0), (2, 5, 0, 0, 2.0, 0.0, 0.0))
    res = ((2, 3, 1.0), (3, 0, 2.0), (5, 0, 1.0), (2, 0, 1.0))
    return mos, res, ()


def test_probe_singular_is_value_not_exception():
    _, pf, _ = _probe(_singular_parts(), (("resistor", 0, "b"),), (1.0,))
    assert tuple(pf.pairs) == ((3, 6),)
    t = _samples(pf)
    assert np.isnan(complex(t[0]).real) or np.isnan(complex(t[0]).imag)
    assert "loop_probe_singular" in codes(pf.undefined)
    assert all(u.category == "numeric" for u in pf.undefined if u.code == "loop_probe_singular")
    la = analyze_loop((pf,))
    r = metric_value("pm_ss_deg", la)
    assert r.value is None and "loop_probe_singular" in codes(r.undefined)


def test_undefined_paths_raise_nothing_i10():
    for parts, cuts in ((ex7_parts(cs_resistor=True), EX7_CUT), (_singular_parts(), (("resistor", 0, "b"),))):
        _, pf, _ = _probe(parts, cuts, (1.0,))
        la = analyze_loop((pf,))
        for name in ("gain_ss_db", "ugf_ss_hz", "gbw_ss_hz", "pm_ss_deg", "parasitic_pm_ss_deg"):
            r = metric_value(name, la)
            assert r.value is None and r.undefined


# =====================================================================================================================
# 입력 계약 위반(ValueError) -- 3.17 '열·관측 구조로 찾기, 정확히 하나씩, 절단 노드 미지수, weights 0 아닌 유한 실수'
# =====================================================================================================================

def _ex7_cut_response():
    cut = cut_circuit(circuit_of(*ex7_parts()), _lc(EX7_CUT))
    (r,) = solve_responses((build_mna(cut.circuit, cut.excitations, cut.senses),))
    return cut, r


@pytest.mark.parametrize("weights", [(0.0,), (math.nan,), (math.inf,)], ids=["zero", "nan", "inf"])
def test_bad_weight_values(weights):
    """3.17 'weights = 쌍마다 0 아닌 유한 실수' -- 값 위반은 ValueError(2절)."""
    cut, r = _ex7_cut_response()
    with pytest.raises(ValueError):
        probe_factor(r, cut.pairs, weights)


@pytest.mark.parametrize("weights", [(1.0, 1.0), ()], ids=["too_many", "empty"])
def test_weights_length_mismatch(weights):
    """쌍 수와 다른 가중 길이: 계약은 오류 형식을 적지 않았다(2절 형식 오류 TypeError / 값 ValueError) -- 둘 다 받는다."""
    cut, r = _ex7_cut_response()
    with pytest.raises((TypeError, ValueError)):
        probe_factor(r, cut.pairs, weights)


def test_response_without_probe_columns():
    """포트 전달 계(전압 열·전류 열, 전하 열 없음)에 절단 쌍을 걸면 프로브 열·관측이 없다 -> ValueError."""
    (r,) = solve_responses((ex2_amp(),))
    with pytest.raises(ValueError):
        probe_factor(r, ((2, 1),), (1.0,))


def test_pairs_not_in_cut_system():
    cut, r = _ex7_cut_response()
    with pytest.raises(ValueError):
        probe_factor(r, ((2, 4),), (1.0,))        # 노드 2 에는 프로브 열·관측이 없다


def test_duplicate_probe_column_rejected():
    """'v 에만 전류를 넣는 열 -- 정확히 하나씩, 아니면 ValueError': 같은 구조의 전류 열을 하나 더 둔 계."""
    ck = circuit_of(*ex7_parts())
    cut = cut_circuit(ck, _lc(EX7_CUT))
    ex = tuple(cut.excitations) + (Excitation("dup_current_3", currents=((3, 1.0),)),)
    (r,) = solve_responses((build_mna(cut.circuit, ex, cut.senses),))
    with pytest.raises(ValueError):
        probe_factor(r, cut.pairs, (1.0,))


# =====================================================================================================================
# I-14 조립 1회, 결정론(I-3), 재번호 불변(I-7), 격자 공유(3.17 '격자')
# =====================================================================================================================

def test_assembly_once_i14():
    ck = circuit_of(*ex7b_parts())
    with count_calls(*STAMP_FUNCS, build_mna) as n:
        cut = cut_circuit(ck, _lc(EX7B_CUTS))
        s = build_mna(cut.circuit, cut.excitations, cut.senses)
    assert n == {"mos_stamps": 2, "two_terminal_stamps": 7, "build_mna": 1}
    import numpy as _np
    assert _np.shape(s.BG) == (_np.shape(s.G)[0], 8) and _np.shape(s.sense_rows)[0] == 4    # 4k 열·2k 관측(k=2)
    with count_calls(*STAMP_FUNCS, build_mna) as n:
        (r,) = solve_responses((s,))
        pf = probe_factor(r, cut.pairs, (0.5, -0.5))
        analyze_loop((pf,))
    assert n == {"mos_stamps": 0, "two_terminal_stamps": 0, "build_mna": 0}


def test_deterministic_bitwise_i3():
    def run():
        _, pf, _ = _probe(ex7b_parts(), EX7B_CUTS, (0.5, -0.5))
        la = analyze_loop((pf,))
        return (np.asarray(pf.response.omegas).tobytes(), _samples(pf).tobytes(), tuple(pf.poles), tuple(pf.zeros),
                la.gain_db, la.ugf_hz, la.gbw_hz, la.phase_margin_deg)

    assert run() == run()


@pytest.mark.parametrize("parts,cuts,weights,nm", [
    (ex7_parts(), EX7_CUT, (1.0,), {0: 9, 2: 1, 3: 0}),
    (ex7_parts(), EX7_CUT, (1.0,), {0: 40, 2: 33, 3: 5}),
    (ex7b_parts(), EX7B_CUTS, (0.5, -0.5), {0: 21, 2: 4, 3: 30, 12: 2, 13: 1}),
], ids=["ex7_a", "ex7_b", "ex7b_dm"])
def test_node_renumbering_invariant_i7(parts, cuts, weights, nm):
    """I-7 은 metric 불변이다(격자 점 수는 계약 대상 아님 -- 실측: 예 7b 재번호에서 1 ulp 차 근이 격자 점 수를 바꾼다)."""
    _, base, _ = _probe(parts, cuts, weights)
    _, other, _ = _probe(parts, cuts, weights, nm=nm)
    assert complex(_samples(other)[0]) == pytest.approx(complex(_samples(base)[0]), rel=1e-13)
    a, b = analyze_loop((base,)), analyze_loop((other,))
    assert b.gain_db == pytest.approx(a.gain_db, rel=1e-12)
    assert b.gbw_hz == pytest.approx(a.gbw_hz, rel=1e-12)
    assert b.ugf_hz == pytest.approx(a.ugf_hz, rel=1e-12)
    assert b.phase_margin_deg == pytest.approx(a.phase_margin_deg, rel=1e-12)


def test_shared_grid_with_port_system():
    """루프 계와 포트 전달 계를 한 번의 solve_responses 로 -- 격자가 두 계 근의 합집합(ex2_amp 극점 1e7 이 들어온다)이고
    T 는 그 점에서도 폐형식."""
    ref = closed_ex7()
    _, pf, (ra,) = _probe(ex7_parts(), EX7_CUT, (1.0,), extra=(ex2_amp(),))
    assert np.array_equal(_omegas(pf), np.asarray(ra.omegas))
    om = _omegas(pf)
    k = int(np.argmin(np.abs(om - 1e7)))
    assert abs(om[k] - 1e7) <= 1e-9 * 1e7
    assert _rel(complex(_samples(pf)[k]), ref["t"](om[k])) <= I12_REL


def test_probe_and_factor_from_different_grids_rejected():
    """3.10: 인수는 같은 solve_responses 결과여야 한다(ProbeFactor 도 같은 공통 규약)."""
    _, pf, _ = _probe(ex7_parts(), EX7_CUT, (1.0,))
    (ra,) = solve_responses((ex2_beta_res(),))
    with pytest.raises(ValueError):
        analyze_loop((pf, Factor(ra, 0)))


# =====================================================================================================================
# I-15 (β = 1: pm_ss_deg = parasitic_pm_ss_deg 비트 동일), I-16 (A·β 무부하 곱 = 옛 정의 red)
# =====================================================================================================================

def test_beta_unity_pm_equals_parasitic_pm_i15():
    """β = 1: pm_ss_deg 의 인수 = 기본 포트 뷰 Factor 1개 -> 같은 MnaSystem 의 같은 Factor 로 두 metric 이 비트 동일.
    예 2 β = 1 폐형식 PM = 90.5729673449°."""
    (r,) = solve_responses((ex2_amp(),))
    la = analyze_loop((Factor(r, 0),))
    pm = metric_value("pm_ss_deg", la)
    ppm = metric_value("parasitic_pm_ss_deg", la)
    assert pm.value == ppm.value                                  # 비트 동일
    assert pm.value == pytest.approx(90.5729673449, rel=1e-10)


EX7_UNLOADED_UGF_HZ = 39756892.0418      # 계약 예 7 대조: A·β 무부하 곱(ω_p = gds/CL)


def _assert_is_pm_ss_definition(la):
    """pm_ss_deg 경로 판정(새 정의): UGF = Middlebrook 폐형식 22718224.0239 Hz."""
    ref = closed_ex7()
    assert la.ugf_hz == pytest.approx(ref["ugf_hz"], rel=METRIC_REL), la.ugf_hz


def test_new_definition_passes_i16():
    _, pf, _ = _probe(ex7_parts(), EX7_CUT, (1.0,))
    la = analyze_loop((pf,))
    _assert_is_pm_ss_definition(la)
    assert la.ugf_hz != pytest.approx(EX7_UNLOADED_UGF_HZ, rel=1e-3)
    assert EX7_UNLOADED_UGF_HZ / la.ugf_hz == pytest.approx(1.75, rel=1e-6)   # '1.75배'(ω_p 비 = 1.75pF/1pF)


def test_old_unloaded_product_is_red_i16():
    """I-16: 같은 소자의 A·β 무부하 인수 곱(예 2 A × 예 2c β)은 UGF 39756892.0418 Hz -- 위 pm_ss_deg 판정이 FAIL 해야 한다."""
    ra, rb = solve_responses((ex2_amp(), ex2c_beta_cap()))
    old = analyze_loop((Factor(ra, 0), Factor(rb, 0)))
    assert old.ugf_hz == pytest.approx(EX7_UNLOADED_UGF_HZ, rel=1e-10)
    with pytest.raises(AssertionError):
        _assert_is_pm_ss_definition(old)
    # PM 은 둘 다 단일 극이라 같다(92.29°) -- UGF 만 1.75배 다르다
    assert old.phase_margin_deg == pytest.approx(closed_ex7()["pm_deg"], rel=1e-10)
