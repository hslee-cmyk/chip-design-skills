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
# [CM 2026-10-08] I-19: probe_dc_value(system, pairs, weights) -- 증강 pencil 의 s = 0 값 T(0). 섞이지 않은 절단에서 열 선택 방식
# T(0)(probe_factor samples[0])과 같다(상대 ≤ 차원·eps 규모 -> test_probe_loop 의 I12_REL 1e-14 와 같은 규약). 기대값: 폐형식 예 7
# T(0) = 25, 저항 되먹임(전도 전용) T(0) = gm/(gds + 1/(Rf + Rs))·Rs/(Rf + Rs) = 50/7, 예 7d(섞인 절단) = gm/gds = 100.
# (시그니처는 interface: inspect.signature 와 docstring 첫 단락 -- 소스 미열람.)
# =====================================================================================================================

from gmid_engine.metrics._helpers_pencil import probe_dc_value  # noqa: E402

from .conftest import EX7, EX7D, EX7D_CUT, ex7d_circuit, probe_cut  # noqa: E402

_I19_REL = 1e-14


def _resistive_circuit():
    p = EX7
    return circuit_of(((2, 3, 0, 0, p["gm"], 0.0, p["gds"]),), ((2, 3, 3e4), (3, 0, 1e4)), ((2, 0, p["cl"]),))


@pytest.mark.parametrize("case", ["ex7_charge_only", "resistive_conduction_only"])
def test_probe_dc_value_equals_column_selection_i19(case):
    p = EX7
    if case == "ex7_charge_only":
        ck, cuts, t0 = circuit_of(*ex7_parts()), EX7_CUT, closed_ex7()["t0"]
    else:
        ck, cuts = _resistive_circuit(), (("resistor", 0, "b"),)
        t0 = p["gm"] / (p["gds"] + 1.0 / 4e4) * 1e4 / 4e4
    cut, sysm, pf, _ = probe_cut(ck, cuts)
    v = probe_dc_value(sysm, cut.pairs, (1.0,))
    col = complex(pf.samples[0])
    assert v is not None
    assert abs(complex(v) - col) <= _I19_REL * abs(col), (v, col)
    assert abs(complex(v) - t0) <= _I19_REL * abs(t0), (v, t0)


def test_probe_dc_value_mixed_cut_i18():
    """섞인 절단(예 7d)에서 probe_dc_value = gm/gds = 100 = probe_factor samples[0](3.17: 섞이면 이 값을 쓴다)."""
    cut, sysm, pf, _ = probe_cut(ex7d_circuit(), EX7D_CUT)
    v = complex(probe_dc_value(sysm, cut.pairs, (1.0,)))
    assert abs(v - EX7D["gm"] / EX7D["gds"]) <= _I19_REL * 100.0
    assert v == complex(pf.samples[0])

