"""[U8 2026-10-09] `noise_transfer(system, row, a_nodes, b_nodes, omegas, *, column, parameters, with_omega)` -- as-built MNA 수반 (설계 41 §7.3 '전달',
metrics CONTRACT 10.1).

oracle:
* (b) 독립 노드 해석(conftest `ref_system`): 잡음원 k(노드 b_k 에서 a_k 로 흐르는 단위 전류 = a 에 +1, b 에 −1 주입)의 출력 전압 Z_k 와 전달 뷰
  H = v(out)/v(in) 을 직접 푼다. 파라미터·ω 미분은 그 독립 풀이의 중앙 차분.
* (d) 계약: ω 는 양의 유한 수(아니면 ValueError), 뷰 열이 없으면 H 없음, 파라미터 집합이 없으면 미분 없음.
"""
import math

import numpy as np
import pytest

from gmid_engine.metrics import noise_transfer

from .noise_cases import TWO_PI, Case, dev, setup_of

OMEGAS = TWO_PI * np.array([1.0, 3e4, 2e6, 7e7])
FD = 1e-6


def amp(gm1=1e-3, gds1=2e-6, cgd=20e-15):
    """M1 (out, in, s) + 소스 축퇴 Rs(s, gnd) + 부하 M2 (out, gnd, gnd) + RL·CL + cgs·cgd -- 전달이 주파수에 따라 변하는 손 회로."""
    return Case(mos=(("M1", "out", "in", "s", "gnd", gm1, gds1, 50e-15, cgd), ("M2", "out", "gnd", "gnd", "gnd", 4e-4, 1e-6)),
                res=(("Rs", "s", "gnd", 300.0), ("RL", "out", "gnd", 2e5)), cap=(("CL", "out", "gnd", 0.5e-12),))


def _setup(case):
    return setup_of(case, (dev("M1", a=1e-12, b=1e-16), dev("M2", a=1e-12, b=1e-16)), rel_tol=0.01)


def test_z_and_h_match_independent_nodal_solution():
    case = amp()
    s = _setup(case)
    src = s.sources
    tr = noise_transfer(s.system, 0, src.a, src.b, OMEGAS, column=0)
    assert tr.undefined == ()
    assert tr.z.shape == (OMEGAS.size, len(src.labels))
    inv = {i: n for n, i in case.ix.items()}
    for k, om in enumerate(OMEGAS):
        for n in range(len(src.labels)):
            expect = case.ref_z(inv[int(src.a[n])], inv[int(src.b[n])], om)
            assert abs(tr.z[k, n] - expect) <= 1e-9 * abs(expect) + 1e-30, (k, src.labels[n])
        h = case.ref_h(om)
        assert abs(tr.h[k] - h) <= 1e-9 * abs(h)


def test_no_column_no_h_and_no_parameters_no_derivative():
    s = _setup(amp())
    tr = noise_transfer(s.system, 0, s.sources.a, s.sources.b, OMEGAS)
    assert tr.h is None and tr.dz is None and tr.dh is None and tr.dz_dw is None


def _gm_param(s, mos_index):
    return next(p for p, (m, name) in enumerate(s.parameters.params) if (m, name) == (mos_index, "gm"))


def test_parameter_derivative_matches_central_difference():
    """∂Z_k/∂gm1 와 ∂H/∂gm1: 독립 풀이를 gm1(1 ± h) 로 두 번 풀어 중앙 차분. oracle (b)."""
    gm1 = 1e-3
    s = _setup(amp(gm1))
    src = s.sources
    tr = noise_transfer(s.system, 0, src.a, src.b, OMEGAS, column=0, parameters=s.parameters)
    p = _gm_param(s, 0)
    hi, lo = amp(gm1 * (1 + FD)), amp(gm1 * (1 - FD))
    inv = {i: n for n, i in hi.ix.items()}
    width = gm1 * (1 + FD) - gm1 * (1 - FD)
    for k, om in enumerate(OMEGAS):
        dh = (hi.ref_h(om) - lo.ref_h(om)) / width
        assert abs(tr.dh[k, p] - dh) <= 1e-5 * abs(dh)
        for n in range(len(src.labels)):
            a, b = inv[int(src.a[n])], inv[int(src.b[n])]
            dz = (hi.ref_z(a, b, om) - lo.ref_z(a, b, om)) / width
            assert abs(tr.dz[k, p, n] - dz) <= 1e-5 * abs(dz) + 1e-12 * abs(tr.z[k, n]) / gm1


def test_omega_derivative_matches_central_difference():
    case = amp()
    s = _setup(case)
    src = s.sources
    tr = noise_transfer(s.system, 0, src.a, src.b, OMEGAS, column=0, with_omega=True)
    inv = {i: n for n, i in case.ix.items()}
    for k, om in enumerate(OMEGAS):
        w2 = om * FD
        dh = (case.ref_h(om + w2) - case.ref_h(om - w2)) / (2 * w2)
        assert abs(tr.dh_dw[k] - dh) <= 1e-5 * abs(dh) + 1e-12 * abs(tr.h[k]) / om
        for n in range(len(src.labels)):
            a, b = inv[int(src.a[n])], inv[int(src.b[n])]
            dz = (case.ref_z(a, b, om + w2) - case.ref_z(a, b, om - w2)) / (2 * w2)
            assert abs(tr.dz_dw[k, n] - dz) <= 1e-5 * abs(dz) + 1e-12 * abs(tr.z[k, n]) / om


@pytest.mark.parametrize("bad", [[0.0], [-1.0], [math.inf], [float("nan")]])
def test_rejects_non_positive_or_non_finite_omega(bad):
    s = _setup(amp())
    with pytest.raises(ValueError):
        noise_transfer(s.system, 0, s.sources.a, s.sources.b, bad)


def test_singular_system_is_undefined_not_exception():
    """미지수 노드 x 가 MOS 게이트에만 닿고 용량도 없다 -> 계 특이. 예외 없이 값 None + 사유(계약 10.3 `singular_mna` 등). oracle (d)."""
    case = Case(mos=(("M1", "out", "x", "gnd", "gnd", 1e-3, 1e-5),), res=(("R", "in", "out", 1e4),))
    s = setup_of(case, (dev("M1", a=1e-12, b=1e-16),))
    tr = noise_transfer(s.system, 0, s.sources.a, s.sources.b, [TWO_PI])
    assert tr.z is None and tr.undefined
