"""`_helpers_nodal` -- metrics CONTRACT 10.0: ω → 0 노달 풀이(용량 열린 회로, 전도 경로 있는 노드), LU 1회, 정방향·수반.

oracle:
* (a) 소자 방정식으로 손으로 세운 G(채널 전류 d->s = gm·v_gs + gmb·v_bs + gds·v_ds, 저항 (v_a − v_b)/R) -- 구성으로 정답이 정해진다.
* (a) 저항 분압·병렬 손계산.
* (b) 수반 z[n] = '노드 n 에 단위 전류를 넣은 정방향 풀이의 관측값' -- `u7_hand.ref_solve`(numpy 직접 풀이, 엔진 스탬프 미사용)로 주입마다 따로 푼다.
"""
from __future__ import annotations

import numpy as np
import pytest

from gmid_engine.metrics import Capacitor, MosSmallSignal, Resistor, SmallSignalCircuit
from gmid_engine.metrics._helpers_nodal import conductance_matrix, nodal_adjoint, nodal_factor, nodal_solve

from . import u7_hand as H


def test_conductance_matrix_one_mos_by_device_equation():
    """(a) MOS 하나(d 1, g 2, s 3, b 0): 채널 전류 i = gm(v2 − v3) + gmb(v0 − v3) + gds(v1 − v3) 가 d 에서 나가고 s 로 들어간다."""
    gm, gmb, gds = 1e-3, 2e-4, 1e-5
    g = conductance_matrix(SmallSignalCircuit(mos=(MosSmallSignal(1, 2, 3, 0, gm, gmb, gds),)), 4)
    want = np.zeros((4, 4))
    row = {2: gm, 0: gmb, 1: gds, 3: -(gm + gmb + gds)}
    for col, v in row.items():
        want[1, col] += v
        want[3, col] -= v
    assert np.array_equal(g, want)


def test_conductance_matrix_resistor_and_capacitor_open():
    """(a) 저항 R(1, 2) 의 G 와 용량은 DC 에서 열림(항목 없음)."""
    g = conductance_matrix(SmallSignalCircuit(resistors=(Resistor(1, 2, 1e3),), capacitors=(Capacitor(1, 0, 1e-12),)), 3)
    want = np.zeros((3, 3))
    want[1, 1] = want[2, 2] = 1e-3
    want[1, 2] = want[2, 1] = -1e-3
    assert np.array_equal(g, want)


def test_solve_divider_and_injection():
    """(a) 노드 1 = 1 V 구동, R1(1-2) 3k, R2(2-0) 1k: v2 = 1/4. 주입 1 mA at 2(구동 0): v2 = 1 mA·(3k ∥ 1k) = 0.75 V."""
    ck = SmallSignalCircuit(resistors=(Resistor(1, 2, 3e3), Resistor(2, 0, 1e3)))
    f = nodal_factor(conductance_matrix(ck, 3), {0, 1})
    v, residual = nodal_solve(f, 3, {1: 1.0})
    assert v[2] == pytest.approx(0.25, rel=1e-14)
    assert v[1] == 1.0 and v[0] == 0.0
    assert 0.0 <= residual <= 1e-14
    v2, _ = nodal_solve(f, 3, None, {2: 1e-3})
    assert v2[2] == pytest.approx(1e-3 * 750.0, rel=1e-14)


def test_adjoint_matches_per_node_forward_injection():
    """(b) 비대칭 G(5T OTA): z[n] = 노드 n 단위 주입 정방향 풀이의 출력 -- 주입마다 독립 numpy 풀이로 대조. 고정 노드 z = 0."""
    nets, m, r, ground, inputs = H.ota5()
    ss = H.circuit(nets, m, r, ground, inputs)
    idx = {n: i for i, n in enumerate(nets)}
    fixed = {idx[n] for n in ground + inputs}
    f = nodal_factor(conductance_matrix(ss.circuit, len(nets)), fixed)
    sense = np.zeros(len(nets))
    sense[idx["out"]] = 1.0
    z = nodal_adjoint(f, len(nets), sense)
    for net in nets:
        if idx[net] in fixed:
            assert z[idx[net]] == 0.0
            continue
        ref = H.ref_solve(m, r, {n: 0.0 for n in ground + inputs}, {net: 1.0})
        assert z[idx[net]] == pytest.approx(ref["out"], rel=1e-10), net


def test_floating_node_excluded_and_zero():
    """(a) gate 에만 닿은 노드(컨덕턴스 행 0)는 미지수에서 빠지고 전압 0, floating 목록에 든다."""
    ck = SmallSignalCircuit(mos=(MosSmallSignal(2, 3, 0, 0, 1e-3, 0.0, 1e-5),), resistors=(Resistor(1, 2, 1e4),))
    f = nodal_factor(conductance_matrix(ck, 4), {0, 1})
    unknown, _lu, _piv, _coupling, floating = f
    assert list(unknown) == [2]
    assert floating == (3,)
    v, _ = nodal_solve(f, 4, {1: 1.0})
    assert v[3] == 0.0
    assert v[2] == pytest.approx(1e-4 / (1e-4 + 1e-5), rel=1e-14)        # 분압 (1/R)/(1/R + gds)


def test_singular_returns_none():
    """(a) 미지수 두 노드가 서로만 잇는 저항(접지 경로 없음) -> 특이: 정방향 (None, None), 수반 None."""
    ck = SmallSignalCircuit(resistors=(Resistor(1, 2, 1e3),))
    f = nodal_factor(conductance_matrix(ck, 3), {0})
    assert nodal_solve(f, 3, {0: 1.0}) == (None, None)
    assert nodal_adjoint(f, 3, np.array([0.0, 1.0, 0.0])) is None


def test_no_unknowns_returns_drive():
    ck = SmallSignalCircuit(resistors=(Resistor(0, 1, 1e3),))
    f = nodal_factor(conductance_matrix(ck, 2), {0, 1})
    v, residual = nodal_solve(f, 2, {1: 0.3})
    assert list(v) == [0.0, 0.3] and residual == 0.0
    assert list(nodal_adjoint(f, 2, np.array([0.0, 1.0]))) == [0.0, 0.0]


def _gamma(m, u=2.0 ** -53):
    return m * u / (1.0 - m * u)


def test_it2c_conductance_matrix_bound_true_matches_hand_formula():
    """oracle 대조: (손) [IT-2c T-L10 `g_bound`, interface 빈칸 답 1·7] `conductance_matrix(circuit, n, bound=True) -> (g, g_bound)`, g 는 bound=False 와 같다
    (위 손 식 test 로 g 확인). E_ij = γ_{max(k−1,0)}·S_ij + C_ij + γ_{n+1}·|Ĝ_ij|, S = Σ|ĝ_s|, k = 항목의 스탬프 항 수, C = Σ γ_{c_s}|ĝ_s|,
    c_s = 스탬프 연산 수(MOS (d,s)·(s,s) 2, 그 밖 MOS 0, 저항 넷 각 1), γ_m = m·u/(1 − m·u), u = 2^-53, n = size.
    회로: MOS(d 1, g 2, s 3, b 0) + 저항 R(1, 3) -- (1,1)·(1,3)·(3,1)·(3,3) 항목은 스탬프 두 항(k = 2)이다. 손으로 세어 같은 float 연산으로 계산한 값과 비교(상대 1e-12)."""
    gm, gmb, gds, R = 1e-3, 2e-4, 1e-5, 1e3
    n = 4
    ck = SmallSignalCircuit(mos=(MosSmallSignal(1, 2, 3, 0, gm, gmb, gds),), resistors=(Resistor(1, 3, R),))
    g, gb = conductance_matrix(ck, n, bound=True)
    assert np.array_equal(g, conductance_matrix(ck, n))
    tot = gm + gmb + gds
    gr = 1.0 / R
    stamps = {}                                              # (i, j) -> [(값, 연산 수)] -- 스탬프 항 손 목록
    for (i, j, v, c) in ((1, 1, gds, 0), (1, 2, gm, 0), (1, 0, gmb, 0), (1, 3, -tot, 2),
                         (3, 1, -gds, 0), (3, 2, -gm, 0), (3, 0, -gmb, 0), (3, 3, tot, 2),
                         (1, 1, gr, 1), (1, 3, -gr, 1), (3, 1, -gr, 1), (3, 3, gr, 1)):
        stamps.setdefault((i, j), []).append((v, c))
    want = np.zeros((n, n))
    for (i, j), terms in stamps.items():
        S = sum(abs(v) for v, _ in terms)
        k = len(terms)
        C = sum(_gamma(c) * abs(v) for v, c in terms)
        Ghat = sum(v for v, _ in terms)
        want[i, j] = _gamma(max(k - 1, 0)) * S + C + _gamma(n + 1) * abs(Ghat)
    assert gb.shape == (n, n)
    for i in range(n):
        for j in range(n):
            assert abs(gb[i, j] - want[i, j]) <= 1e-12 * max(want[i, j], 1e-300), (i, j, gb[i, j], want[i, j])
    assert (gb[0, :] == 0).all() and (gb[2, :] == 0).all()   # 스탬프가 없는 행 0
