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


def test_it2c_conductance_matrix_bound_true_returns_pair_with_same_g():
    """oracle 대조: (손) [IT-2c T-L10 `g_bound`] interface: `bound=True` 면 `(g, g_bound)`, g 는 bound=False 와 같은 행렬(손 식 대조: 위
    test_conductance_matrix_one_mos_by_device_equation). g_bound 는 같은 모양·비음수·스탬프가 없는 행은 0, 연산 수 0 항목(gm 그대로)은 0,
    연산 수 k 항목은 (0, 2k·u·|g|] (u = 2^-53, 반올림 오차 상계 -- 정확한 식은 단언하지 않는다)."""
    u = 2.0 ** -53
    gm, gmb, gds = 1e-3, 2e-4, 1e-5
    ck = SmallSignalCircuit(mos=(MosSmallSignal(1, 2, 3, 0, gm, gmb, gds),))
    g0 = conductance_matrix(ck, 4)
    g, gb = conductance_matrix(ck, 4, bound=True)
    assert np.array_equal(g, g0) and gb.shape == g.shape and (gb >= 0).all()
    assert (gb[0, :] == 0).all() and (gb[2, :] == 0).all()                      # 행 0(b)·2(g) 에는 스탬프 없음
    assert gb[1, 2] == 0.0 and gb[1, 0] == 0.0 and gb[1, 1] == 0.0               # 입력 값 그대로 (덧셈 0회)
    for (r, c) in ((1, 3), (3, 3)):                                                # 덧셈 2회 항목
        assert 0.0 < gb[r, c] <= 4.0 * u * abs(g[r, c])
    r = SmallSignalCircuit(resistors=(Resistor(1, 2, 1e3),))
    gr, gbr = conductance_matrix(r, 3, bound=True)
    assert np.array_equal(gr, conductance_matrix(r, 3))
    for (a, b) in ((1, 1), (1, 2), (2, 1), (2, 2)):                                # 1/R 나눗셈 한 번
        assert 0.0 < gbr[a, b] <= 2.0 * u * abs(gr[a, b])
    assert (gbr[0, :] == 0).all() and (gbr[:, 0] == 0).all()
