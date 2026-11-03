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
from gmid_engine.metrics._helpers_dc import limit_matrix
from gmid_engine.metrics._helpers_nodal import capacitance_matrix, conductance_matrix, nodal_adjoint, nodal_factor, nodal_solve

from . import u7_hand as H


def _f(ck, size, fixed):
    """[NL-1] 전하 노드 없는 계의 인수분해: c = 영행렬(용량이 없는 계 -- 입력 생성, 기대값 아님)."""
    return nodal_factor(conductance_matrix(ck, size), fixed, c=np.zeros((size, size)))


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
    f = _f(ck, 3, {0, 1})
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
    f = _f(ss.circuit, len(nets), fixed)
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
    """[NL-1 C-8 뜻 교체] (a) gate 에만 닿은 노드(G 행 0)라도 어떤 G 열(드레인 행의 gm 항)에 항목이 있으면 0 V 로 둘 수 없다:
    같은 회로가 이제 lu is None, 정방향 (None, None). 이 노드는 floating 이 아니다(인자 없는 노드만 floating)."""
    ck = SmallSignalCircuit(mos=(MosSmallSignal(2, 3, 0, 0, 1e-3, 0.0, 1e-5),), resistors=(Resistor(1, 2, 1e4),))
    f = _f(ck, 4, {0, 1})
    unknown, lu, _piv, _coupling, floating, charge = f
    assert lu is None
    assert 3 not in floating and charge == ()
    assert nodal_solve(f, 4, {1: 1.0}) == (None, None)


def test_ub1_floating_means_no_entry_anywhere():
    """[NL-1 C-8] (a) 어떤 G 행·C 행·G 열·C 열 항목도 없는 비고정 노드(3)만 floating: 0 V, 나머지 해는 분압 그대로."""
    ck = SmallSignalCircuit(resistors=(Resistor(1, 2, 3e3), Resistor(2, 0, 1e3)))
    f = _f(ck, 4, {0, 1})
    unknown, lu, _piv, _coupling, floating, charge = f
    assert lu is not None and list(unknown) == [2]
    assert tuple(floating) == (3,) and tuple(charge) == ()
    v, _ = nodal_solve(f, 4, {1: 1.0})
    assert v[3] == 0.0
    assert v[2] == pytest.approx(0.25, rel=1e-14)                        # 분압 1k/(3k + 1k)


# ---------------------------------------------------------------- [NL-1] 전하 보존 행 (T-4a·T-4c·T-4e)
# T-4 회로(정수 노드): 0 gnd, 1 in(구동), 2 n(게이트 전용 용량 넷), 3 out, 4 vdd. C1(1-2), C2(2-0), M1(d 3, g 2, s 0, b 0, cgs·cgd·cgb), RL(4-3).
UB1 = dict(c1=2e-12, c2=3e-12, cgs=5e-13, cgd=2e-13, cgb=1e-13, gm=1e-3, gds=2e-5, rl=3e4)


def _ub1_circuit(p=UB1):
    return SmallSignalCircuit(
        mos=(MosSmallSignal(3, 2, 0, 0, p["gm"], 0.0, p["gds"], cgs=p["cgs"], cgd=p["cgd"], cgb=p["cgb"]),),
        resistors=(Resistor(4, 3, p["rl"]),),
        capacitors=(Capacitor(1, 2, p["c1"]), Capacitor(2, 0, p["c2"])), ac_ground=(0, 4))


def _ub1_hand_c(p=UB1):
    """(a) 용량 스탬프를 손으로: 용량 (a, b, c) -> C[a,a] += c, C[b,b] += c, C[a,b] −= c, C[b,a] −= c. MOS: cgs(g,s), cgd(g,d), cgb(g,b)."""
    c = np.zeros((5, 5))
    for a, b, v in ((1, 2, p["c1"]), (2, 0, p["c2"]), (2, 0, p["cgs"]), (2, 3, p["cgd"]), (2, 0, p["cgb"])):
        c[a, a] += v
        c[b, b] += v
        c[a, b] -= v
        c[b, a] -= v
    return c


def test_ub1_capacitance_matrix_by_stamps():
    """(a) MOS 5 용량(cgs·cgd·cgb·cdb·csb)과 `capacitors` 가 손으로 세운 C 와 같다."""
    assert np.array_equal(capacitance_matrix(_ub1_circuit(), 5), _ub1_hand_c())
    ck = SmallSignalCircuit(mos=(MosSmallSignal(1, 2, 3, 0, 1e-3, 0.0, 1e-5, cgs=1e-13, cgd=2e-13, cgb=3e-13, cdb=4e-13, csb=5e-13),))
    want = np.zeros((4, 4))
    for a, b, v in ((2, 3, 1e-13), (2, 1, 2e-13), (2, 0, 3e-13), (1, 0, 4e-13), (3, 0, 5e-13)):
        want[a, a] += v
        want[b, b] += v
        want[a, b] -= v
        want[b, a] -= v
    assert np.allclose(capacitance_matrix(ck, 4), want, rtol=0, atol=0)


def test_ub1_limit_matrix_replaces_only_charge_rows():
    """(a) `limit_matrix(g, c, charge)`: g 사본의 charge 행만 c 행으로, 원 g 는 그대로."""
    rng = np.random.default_rng(7)
    g = rng.uniform(1.0, 2.0, (4, 4))
    c = rng.uniform(3.0, 4.0, (4, 4))
    g0 = g.copy()
    got = limit_matrix(g, c, (1, 3))
    want = g0.copy()
    want[1, :] = c[1, :]
    want[3, :] = c[3, :]
    assert np.array_equal(got, want)
    assert np.array_equal(g, g0)


def test_ub1_charge_node_solution_matches_closed_form_and_dc_limit():
    """T-4a (a)+(b): 용량 분배 V(n) = C1/D, out = −gm·R'·C1/D (D = C1 + C2 + cgs + cgb + cgd(1 + gm·R'), R' = 1/(gds + G)).
    노달 풀이 == 독립 ω → 0 극한 풀이 `solve_dc_limit` == 폐형식."""
    from gmid_engine.metrics import Excitation, Sense, build_mna, solve_dc_limit
    p = UB1
    ck = _ub1_circuit()
    f = nodal_factor(conductance_matrix(ck, 5), {0, 1, 4}, c=_ub1_hand_c())
    unknown, lu, _piv, _coupling, floating, charge = f
    assert tuple(charge) == (2,) and lu is not None
    v, residual = nodal_solve(f, 5, {1: 1.0})
    rp = 1.0 / (p["gds"] + 1.0 / p["rl"])
    d = p["c1"] + p["c2"] + p["cgs"] + p["cgb"] + p["cgd"] * (1.0 + p["gm"] * rp)
    assert v[2] == pytest.approx(p["c1"] / d, rel=1e-10)
    assert v[3] == pytest.approx(-p["gm"] * rp * p["c1"] / d, rel=1e-10)
    dl = solve_dc_limit(build_mna(ck, (Excitation("vin", voltages=((1, 1.0),)),), (Sense(3),)))
    assert v[3] == pytest.approx(float(np.asarray(dl.values)[0][0]), rel=1e-9)


def test_ub1_charge_node_injection_and_adjoint():
    """T-4c (a): 전하 노드에 전류 주입 -> (None, None). 수반 z[charge] = NaN, 고정 노드 0, 다른 노드는 단위 주입 응답:
    out 에 단위 전류를 넣으면 v_n = cgd·v_out/(C1 + C2 + cgs + cgb + cgd) -> z[out] = 1/(gds + G + gm·cgd/Csum)."""
    p = UB1
    f = nodal_factor(conductance_matrix(_ub1_circuit(), 5), {0, 1, 4}, c=_ub1_hand_c())
    assert nodal_solve(f, 5, {1: 1.0}, {2: 1e-9}) == (None, None)
    sense = np.zeros(5)
    sense[3] = 1.0
    z = nodal_adjoint(f, 5, sense)
    assert np.isnan(z[2])
    assert z[0] == 0.0 and z[1] == 0.0 and z[4] == 0.0
    csum = p["c1"] + p["c2"] + p["cgs"] + p["cgb"] + p["cgd"]
    assert z[3] == pytest.approx(1.0 / (p["gds"] + 1.0 / p["rl"] + p["gm"] * p["cgd"] / csum), rel=1e-10)


def test_ub1_c_has_no_effect_without_charge_nodes():
    """T-4e (a): 전하 노드 없는 계(5T OTA)는 c = 0행렬과 임의 값에서 lu·coupling·해가 바이트 동일."""
    nets, m, r, ground, inputs = H.ota5()
    ss = H.circuit(nets, m, r, ground, inputs)
    n = len(nets)
    idx = {x: i for i, x in enumerate(nets)}
    fixed = {idx[x] for x in ground + inputs}
    g = conductance_matrix(ss.circuit, n)
    rng = np.random.default_rng(3)
    c_rand = rng.uniform(1e-15, 1e-12, (n, n))
    f0 = nodal_factor(g, fixed, c=np.zeros((n, n)))
    f1 = nodal_factor(g, fixed, c=c_rand)
    assert tuple(f0[5]) == () and tuple(f1[5]) == ()
    assert np.asarray(f0[1]).tobytes() == np.asarray(f1[1]).tobytes()
    assert np.asarray(f0[3]).tobytes() == np.asarray(f1[3]).tobytes()
    drive = {idx["ip"]: 0.5, idx["im"]: -0.5}
    v0, _ = nodal_solve(f0, n, drive)
    v1, _ = nodal_solve(f1, n, drive)
    assert np.asarray(v0).tobytes() == np.asarray(v1).tobytes()


def test_singular_returns_none():
    """(a) 미지수 두 노드가 서로만 잇는 저항(접지 경로 없음) -> 특이: 정방향 (None, None), 수반 None."""
    ck = SmallSignalCircuit(resistors=(Resistor(1, 2, 1e3),))
    f = _f(ck, 3, {0})
    assert nodal_solve(f, 3, {0: 1.0}) == (None, None)
    assert nodal_adjoint(f, 3, np.array([0.0, 1.0, 0.0])) is None


def test_no_unknowns_returns_drive():
    ck = SmallSignalCircuit(resistors=(Resistor(0, 1, 1e3),))
    f = _f(ck, 2, {0, 1})
    v, residual = nodal_solve(f, 2, {1: 0.3})
    assert list(v) == [0.0, 0.3] and residual == 0.0
    assert list(nodal_adjoint(f, 2, np.array([0.0, 1.0]))) == [0.0, 0.0]
