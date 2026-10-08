"""`_helpers_pencil.finite_eigs` (비공개) -- pencil 유한 고유값(`pencil_roots`·`probe_loop` 공용, CONTRACT 0절·3.4).
공개 경로(pencil_roots 극점·영점, ProbeFactor poles·zeros)로 확인한다: 무한 고유값은 빠지고(QZ 동차 좌표, 상수 없음),
원점 고유값은 정확히 0j, 남은 값은 유한 복소수. 기대값은 손계산 극점."""
import math

import numpy as np
import pytest

from gmid_engine.metrics import (
    Capacitor,
    Excitation,
    LoopCut,
    Resistor,
    Sense,
    SmallSignalCircuit,
    build_mna,
    cut_circuit,
    pencil_roots,
    probe_factor,
    solve_responses,
)

from .conftest import EX7_CUT, circuit_of, closed_ex7, ex2c_beta_cap, ex7_parts


def test_algebraic_node_infinite_eig_dropped():
    """R1(1,2), R2(2,3), C(3,0), 1 V at 1: 노드 2 는 용량 없음(C 행 0 -> 무한 고유값). 유한 극점 = −1/((R1+R2)·C) 하나."""
    r1, r2, c = 1e3, 2e3, 1e-9
    ck = SmallSignalCircuit(resistors=(Resistor(1, 2, r1), Resistor(2, 3, r2)), capacitors=(Capacitor(3, 0, c),),
                            ac_ground=(0,))
    s = build_mna(ck, (Excitation("v", voltages=((1, 1.0),)),), (Sense(3), Sense(2)))
    r = pencil_roots(s)
    assert len(r.poles) == 1
    assert complex(r.poles[0]) == pytest.approx(complex(-1.0 / ((r1 + r2) * c), 0.0), rel=1e-12)
    # 관측 2(행 1): V2/V1 = (R2 + 1/sC)/(R1 + R2 + 1/sC) -> 영점 −1/(R2·C)
    (z,) = r.zeros[1]
    assert len(z) == 1 and complex(z[0]) == pytest.approx(complex(-1.0 / (r2 * c), 0.0), rel=1e-12)
    assert tuple(r.zeros[0][0]) == ()                              # 관측 3: 영점 없음
    for x in tuple(r.poles) + tuple(z):
        assert math.isfinite(complex(x).real) and math.isfinite(complex(x).imag)


def test_charge_mode_origin_exact_zero():
    """3.4 원점 판정: 용량 전용 노드(예 2c 노드 3)는 아니지만 구동 노드 결합만 있는 계 -- 극점 = 정확히 0j 만."""
    r = pencil_roots(ex2c_beta_cap())
    assert all(complex(p) == 0j for p in r.poles)


def test_probe_factor_roots_finite_and_origin_exact():
    """ProbeFactor poles·zeros 도 같은 helper: 유한값만, 원점 근은 정확히 0j(근사 작은 |s| 아님), 지배 극점 −ω_p."""
    cut = cut_circuit(circuit_of(*ex7_parts()), tuple(LoopCut(*c) for c in EX7_CUT))
    (r,) = solve_responses((build_mna(cut.circuit, cut.excitations, cut.senses),))
    pf = probe_factor(r, cut.pairs, (1.0,))
    roots = [complex(x) for x in tuple(pf.poles) + tuple(pf.zeros)]
    assert all(np.isfinite(x.real) and np.isfinite(x.imag) for x in roots)
    small = [x for x in roots if x != 0j and abs(x) < 1.0]
    assert small == [], small                                          # 원점 근이 반올림 잡음으로 남지 않는다
    wp = closed_ex7()["wp"]
    assert min(abs(complex(p) + wp) for p in pf.poles) <= 1e-9 * wp


# =====================================================================================================================
# [CM 2026-10-08, 424eb5e 개정] I-19·`probe_pencil`(T 의 증강 pencil -- probe_loop 극점·영점 / 섞인 절단 T(0) 공용)을 공개 경로로:
# ProbeFactor samples[0](T(0))·poles 가 폐형식과 같다. 비공개 `_mixed_dc_value` 는 부르지 않는다(섞인 절단의 공개 결과 = 예 7d 100).
# 기대값(oracle (a) 손유도):
#   예 7   (용량 전용 절단) T(0) = (gm/gds)·Cf/(Cf+Cs) = 25, 극점 −gds/(CL + Cf·Cs/(Cf+Cs))
#   예 7f  (전도 전용) T = gm·(Rs/(Rf+Rs))/(gds + 1/(Rf+Rs) + sCL) -> T(0) = 100/3, 극점 −(gds + 1/(Rf+Rs))/CL = −1.5e7
#   저항 되먹임(Rf 3e4, Rs 1e4) T(0) = gm·(Rs/(Rf+Rs))/(gds + 1/(Rf+Rs)) = 50/7
#   예 7d  (섞인 절단) T(0) = gm/gds = 100, 극점 = 2차 분모 근(conftest closed_ex7d)
# 허용: T(0) 상대 ≤ 1e-14(I-19 '차원·eps' -- test_probe_loop 의 I12_REL 과 같은 규약), 극점 상대 ≤ 1e-9(3.17 근 정밀도 test 와 같음).
# =====================================================================================================================

from .conftest import EX7, EX7D, EX7D_CUT, closed_ex7d, ex7d_circuit, probe_cut  # noqa: E402

_REL_T0 = 1e-14
_RF, _RS = 1e5, 1e5


def _ex7f_circuit():
    p = EX7
    return circuit_of(((2, 3, 0, 0, p["gm"], 0.0, p["gds"]),), ((2, 3, _RF), (3, 0, _RS)), ((2, 0, p["cl"]),))


def _resistive_circuit():
    p = EX7
    return circuit_of(((2, 3, 0, 0, p["gm"], 0.0, p["gds"]),), ((2, 3, 3e4), (3, 0, 1e4)), ((2, 0, p["cl"]),))


def _cases():
    p = EX7
    g7f = p["gds"] + 1.0 / (_RF + _RS)
    return {
        "ex7": (circuit_of(*ex7_parts()), EX7_CUT, closed_ex7()["t0"], (-closed_ex7()["wp"],)),
        "ex7f": (_ex7f_circuit(), (("resistor", 0, "b"),), p["gm"] * _RS / (_RF + _RS) / g7f, (-g7f / p["cl"],)),
        "resistive": (_resistive_circuit(), (("resistor", 0, "b"),),
                      p["gm"] * 1e4 / 4e4 / (p["gds"] + 1.0 / 4e4), (-(p["gds"] + 1.0 / 4e4) / p["cl"],)),
        "ex7d": (ex7d_circuit(), EX7D_CUT, EX7D["gm"] / EX7D["gds"], closed_ex7d()["poles"]),
    }


def test_hand_t0_values_match_contract_numbers():
    """입력 확인: 손유도 T(0) 가 계약 숫자(예 7 25, 예 7f 100/3, 예 7d 100)와 저항 되먹임 50/7 이다."""
    c = _cases()
    assert c["ex7"][2] == pytest.approx(25.0, rel=1e-15)
    assert c["ex7f"][2] == pytest.approx(100.0 / 3.0, rel=1e-15)
    assert c["resistive"][2] == pytest.approx(50.0 / 7.0, rel=1e-15)
    assert c["ex7d"][2] == pytest.approx(100.0, rel=1e-15)


@pytest.mark.parametrize("case", ["ex7", "ex7f", "resistive", "ex7d"])
def test_probe_dc_value_public_t0_i19(case):
    """I-19(공개 경로): 섞이지 않은 절단(ex7 용량 전용, ex7f·resistive 전도 전용)과 섞인 절단(ex7d)의 samples[0] = 손유도 T(0),
    실수, 정의 불가 없음 -- analyze_loop dc_value 도 같다."""
    from gmid_engine.metrics import analyze_loop
    ck, cuts, t0, _ = _cases()[case]
    _, _, pf, _ = probe_cut(ck, cuts)
    v = complex(pf.samples[0])
    assert v.imag == 0.0
    assert abs(v - t0) <= _REL_T0 * abs(t0), (v, t0)
    assert pf.undefined == ()
    assert analyze_loop((pf,)).dc_value == pytest.approx(t0, rel=_REL_T0)


@pytest.mark.parametrize("case", ["ex7", "ex7f", "resistive", "ex7d"])
def test_probe_pencil_poles_public(case):
    """probe_pencil(공개 결과 ProbeFactor.poles): 손유도 극점이 모두 들어 있고 우반면 근 없음, 근은 유한 복소수."""
    ck, cuts, _, poles = _cases()[case]
    _, _, pf, _ = probe_cut(ck, cuts)
    got = [complex(x) for x in pf.poles]
    assert all(math.isfinite(z.real) and math.isfinite(z.imag) for z in got)
    assert all(z.real <= 0.0 for z in got)
    for p0 in poles:
        assert min(abs(z - p0) for z in got) <= 1e-9 * abs(p0), (p0, got)

