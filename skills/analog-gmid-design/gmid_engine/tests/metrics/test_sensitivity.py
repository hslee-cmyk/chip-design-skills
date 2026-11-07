"""`response_sensitivity` (한 계·한 ω 의 관측값·사후 오차와 LUT 파라미터·ω 에 대한 수반 1차 민감도) -- metrics CONTRACT 9.2.
(+ 9.6 R-2·R-6·R-7·R-8·R-9)

기대값: conftest `ref_system` -- 피검 함수와 독립인 numpy MNA(전체 노드 G·C 를 직접 세우고 고정 노드 소거, ω = 0 은 3.3 전하 보존
극한 식을 test 쪽에서 따로 세운다). ∂V/∂p 는 그 독립 MNA 를 파라미터마다 p(1 ± h) 로 다시 세워 푼 중심 차분(R-2, h = 1e-6).
회로: 예 3 Miller 변형(두 MOS 에 gmb·cgs·cgd·음의 cgb, source 축퇴로 gmb 가 의미 있음), 예 7 변형 절단 계(용량 전용 절단 노드,
음의 cgb), 예 2d(전하 주입 열).

허용치 유도:
- 차분 대 수반: R-2 의 상대 1e-6 + 차분 반올림 바닥. 두 번 푼 V± 의 반올림 오차(≈ n·eps·|V|, n = 미지수 수)가 폭 2h 로 나뉘어
  기울기x|p| 에 n·eps·|V|/h 로 들어간다(크기가 0 에 가까운 민감도 -- 예: source = bulk 인 gmb -- 에서 상대 비교가 무의미해지는 몫).
- 독립 MNA 대 엔진 값: 둘 다 후방 안정 풀이 -- 차 ≤ cond·n·eps. 이 작은 계의 cond 는 1e6 이하라 1e-9.
"""
from __future__ import annotations

import math

import numpy as np
import pytest

from gmid_engine.metrics import (
    Capacitor,
    Excitation,
    LoopCut,
    MosSmallSignal,
    ParameterSet,
    ResponseSensitivity,
    Sense,
    SmallSignalCircuit,
    build_mna,
    cut_circuit,
    lut_parameters,
    mos_stamps,
    response_sensitivity,
    solve_dc_limit,
    solve_point,
    two_terminal_stamps,
)

from .conftest import (
    EPS,
    EX2D,
    EX7V_CAP,
    EX7V_MOS,
    FD_H,
    FD_RTOL,
    MILLER_V_CAP,
    MILLER_V_COLS,
    MILLER_V_MOS,
    MILLER_V_RES,
    MILLER_V_SENSE,
    MOS_IX,
    central_diff,
    circuit12,
    codes,
    columns_of,
    count_calls,
    LUT_P,
    lut_params_of,
    miller_v_system,
    mos_t,
    ref_system,
    senses_of,
)

VALUE_RTOL = 1e-9
MILLER_EPS = (0.01, 0.03)
RENUM = {0: 17, 1: 4, 2: 30, 3: 8, 4: 11}


# ---------------------------------------------------------------- 계 생성

def _miller():
    ck, sysm = miller_v_system()
    ref = dict(mos=MILLER_V_MOS, res=MILLER_V_RES, cap=MILLER_V_CAP, ac_ground=(0,), columns=MILLER_V_COLS,
               senses=MILLER_V_SENSE)
    return ck, sysm, ref


def _ex7v_cut():
    """예 7 변형 절단 계: Cf(capacitors index 1) b 단자(노드 3) 절단 -> x = 4. 원래 회로의 ParameterSet 을 쓴다(9.2)."""
    ck = circuit12(EX7V_MOS, (), EX7V_CAP)
    cut = cut_circuit(ck, (LoopCut("capacitor", 1, "b"),))
    assert tuple(cut.pairs) == ((3, 4),)                 # 입력 확인(3.16)
    sysm = build_mna(cut.circuit, cut.excitations, cut.senses)
    cap = (EX7V_CAP[0], (2, 4, EX7V_CAP[1][2]), EX7V_CAP[2])          # test 쪽 절단 회로: Cf 의 b 단자 -> 4
    ref = dict(mos=EX7V_MOS, res=(), cap=cap, ac_ground=(0,), columns=columns_of(cut.excitations),
               senses=senses_of(cut.senses))
    return ck, sysm, ref


def _ex2d():
    p = EX2D
    mos = (mos_t(2, 3, 0, 0, p["gm"], 0.0, p["gds"]),)
    cap = ((2, 3, p["cf"]), (3, 1, p["cs"]), (2, 0, p["cl"]))
    ck = circuit12(mos, (), cap)
    sysm = build_mna(ck, (Excitation("vin", voltages=((1, 1.0),)), Excitation("iinj", currents=((3, 1.0),))), (Sense(2),))
    ref = dict(mos=mos, res=(), cap=cap, ac_ground=(0,), columns=({"v": {1: 1.0}, "i": {}, "q": {}},
                                                                  {"v": {}, "i": {3: 1.0}, "q": {}}), senses=((2, None),))
    return ck, sysm, ref


CASES = {"miller": (_miller, MILLER_EPS), "ex7v_cut": (_ex7v_cut, (0.02,)), "ex2d": (_ex2d, (0.02,))}
OMEGAS = {"miller": (0.0, 1e5, 3e7, 1e9), "ex7v_cut": (0.0, 1e6, 2e7, 1e9), "ex2d": (0.0, 1e6, 1e8)}


def _col_scale(V):
    """열마다 max_r |V[r, j]| 을 (r, m) 로 펼친 것(NaN 열은 0) -- 풀이 오차 한계가 열 노름 기준이라 원소 0 근처도 그 척도로 본다."""
    a = np.nan_to_num(np.abs(np.asarray(V)), nan=0.0)
    return np.broadcast_to(np.max(a, axis=0, keepdims=True), a.shape)


def _n_unknown(ref):
    return len({n for t in ref["mos"] for n in t[:4]} | {n for t in ref["res"] + ref["cap"] for n in t[:2]}) + 2


# ---------------------------------------------------------------- R-7: 값·오차 = solve_point / solve_dc_limit

@pytest.mark.parametrize("case", sorted(CASES))
def test_r7_values_errors_match_point_and_dc_limit(case):
    make, eps = CASES[case]
    ck, sysm, ref = make()
    ps = lut_parameters(ck, eps)
    for w in OMEGAS[case]:
        s = response_sensitivity(sysm, ps, w)
        assert isinstance(s, ResponseSensitivity)
        vals = np.asarray(s.values)
        if w == 0.0:
            dl = solve_dc_limit(sysm)
            assert np.array_equal(vals, np.asarray(dl.values), equal_nan=True)
        else:
            pt = solve_point(sysm, w)
            assert np.array_equal(vals, np.asarray(pt.values), equal_nan=True)
            assert np.array_equal(np.asarray(s.errors), np.asarray(pt.errors), equal_nan=True)
        # 독립 MNA 대조(값 자체)
        exp = ref_system(omega=w, **ref)
        fin = np.isfinite(exp)
        assert np.array_equal(fin, np.isfinite(vals))
        scale = _col_scale(exp)                          # 후방 안정 풀이의 오차 한계는 열 노름 기준
        assert np.all(np.abs(vals[fin] - exp[fin]) <= VALUE_RTOL * scale[fin])


# ---------------------------------------------------------------- R-2: 수반 미분 = 독립 MNA 중심 차분

def _check_dparam(s, ref, params, w):
    d = np.asarray(s.d_param)
    V = ref_system(omega=w, **ref)
    assert d.shape == (len(params),) + V.shape
    floor = _n_unknown(ref) * EPS / FD_H * _col_scale(V)
    for i, (k, name) in enumerate(params):
        p = ref["mos"][k][MOS_IX[name]]
        fd = central_diff(ref["mos"], k, name, lambda m: ref_system(**dict(ref, mos=m), omega=w))
        eng, exp = d[i] * p, fd * p
        fin = np.isfinite(V)
        assert np.array_equal(np.isfinite(eng), fin), (name, w)
        diff = np.abs(eng[fin] - exp[fin])
        tol = FD_RTOL * np.maximum(np.abs(eng[fin]), np.abs(exp[fin])) + floor[fin]
        assert np.all(diff <= tol), (k, name, w, eng, exp)


@pytest.mark.parametrize("case", sorted(CASES))
def test_r2_d_param_equals_central_difference(case):
    """∂V/∂p(LU 1회 + 수반) = 독립 MNA 를 파라미터마다 다시 세운 중심 차분 -- ω > 0 과 ω = 0(전하 보존 극한) 모두."""
    make, eps = CASES[case]
    ck, sysm, ref = make()
    ps = lut_parameters(ck, eps)
    assert tuple(ps.params) == lut_params_of(ref["mos"])
    for w in OMEGAS[case]:
        _check_dparam(response_sensitivity(sysm, ps, w), ref, ps.params, w)


def test_r2_miller_sensitivities_not_trivial():
    """입력 확인: Miller 변형 ω > 0 에서 단위 스탬프에 (미지수 행, 미지수 열) 항목이 있는 파라미터는 모두 ∂V/∂p ≠ 0 (M1 gmb 는
    source 축퇴, 음의 cgb 포함) -- 비교가 공허하지 않다. 그런 항목이 없는 파라미터(고정 노드 사이 -- M1 cgb: gate 구동·bulk 접지,
    M2 gmb: source = bulk)는 정확히 0."""
    ck, sysm, ref = _miller()
    ps = lut_parameters(ck, MILLER_EPS)
    d = np.asarray(response_sensitivity(sysm, ps, 3e7).d_param)
    fixed = {0, 1}
    n_live = 0
    for i, (k, name) in enumerate(ps.params):
        dev = ck.mos[k]
        kw = {nm: 0.0 for nm in ("gm", "gmb", "gds", "cgs", "cgd", "cgb", "cdb", "csb")}
        kw[name] = 1.0
        st = mos_stamps(MosSmallSignal(dev.d, dev.g, dev.s, dev.b, **kw))
        live = any(r not in fixed and c not in fixed for r, c, _ in st.g + st.c)
        n_live += live
        assert (np.all(np.abs(d[i]) > 0.0) if live else np.all(d[i] == 0.0)), (k, name)
    # [JC-1, A-167] 합계 상수 10(6열 시절)을 박지 않는다: 살아 있는 칸 수를 열 목록(conftest `lut_params_of` -- 입력 MOS 에서 값 ≠ 0 인 LUT_P 8열)에서 따로 센다.
    # 열 목록 갱신(cdb·csb 추가)을 따르는 기대 갱신이고 약화가 아니다(살아 있는/없는 칸 단언은 위 루프에서 칸마다 그대로).
    def _live(k, name):
        dev = ck.mos[k]
        kw = {nm: 0.0 for nm in LUT_P}
        kw[name] = 1.0
        st = mos_stamps(MosSmallSignal(dev.d, dev.g, dev.s, dev.b, **kw))
        return any(r not in fixed and c not in fixed for r, c, _ in st.g + st.c)
    assert n_live == sum(_live(k, name) for k, name in lut_params_of(ref["mos"]))
    assert n_live > 0


@pytest.mark.parametrize("case", ["miller", "ex7v_cut"])
def test_d_omega_equals_central_difference(case):
    """∂V/∂ω(ω > 0) = yᵀ·j(BC − C·x) -- 독립 MNA 의 ω 중심 차분과 같다. ω = 0 은 None."""
    make, eps = CASES[case]
    ck, sysm, ref = make()
    ps = lut_parameters(ck, eps)
    assert response_sensitivity(sysm, ps, 0.0).d_omega is None
    for w in OMEGAS[case][1:]:
        s = response_sensitivity(sysm, ps, w)
        V = ref_system(omega=w, **ref)
        wp, wm = w * (1.0 + FD_H), w * (1.0 - FD_H)
        fd = (ref_system(omega=wp, **ref) - ref_system(omega=wm, **ref)) / (wp - wm) * w
        eng = np.asarray(s.d_omega) * w
        tol = FD_RTOL * np.maximum(np.abs(eng), np.abs(fd)) + _n_unknown(ref) * EPS / FD_H * _col_scale(V)
        assert np.all(np.abs(eng - fd) <= tol), (w, eng, fd)


# ---------------------------------------------------------------- ω = 0 전하 주입 열·구조 결함

def test_dc_charge_injection_column_only():
    """9.2: ω = 0 의 전하 주입 열(예 2d iinj)은 값·민감도 NaN + dc_charge_injection, 다른 열(vin)은 유한·차분과 같다."""
    ck, sysm, ref = _ex2d()
    ps = lut_parameters(ck, (0.02,))
    s = response_sensitivity(sysm, ps, 0.0)
    v, d = np.asarray(s.values), np.asarray(s.d_param)
    assert np.all(np.isnan(v[:, 1])) and np.all(np.isnan(d[:, :, 1]))
    assert np.all(np.isfinite(v[:, 0])) and np.all(np.isfinite(d[:, :, 0]))
    assert "dc_charge_injection" in codes(s.undefined)


def test_negative_check_no_charge_injection_without_injected_current():
    """음성 대조: 전류 주입 없는 용량 전용 노드 계(예 2d vin 열만)는 dc_charge_injection 이 없다."""
    p = EX2D
    ck = circuit12((mos_t(2, 3, 0, 0, p["gm"], 0.0, p["gds"]),), (), ((2, 3, p["cf"]), (3, 1, p["cs"]), (2, 0, p["cl"])))
    sysm = build_mna(ck, (Excitation("vin", voltages=((1, 1.0),)),), (Sense(2),))
    s = response_sensitivity(sysm, lut_parameters(ck, (0.02,)), 0.0)
    assert "dc_charge_injection" not in codes(s.undefined)
    assert np.all(np.isfinite(np.asarray(s.values)))


@pytest.mark.parametrize("w", [0.0, 1e6])
def test_structural_defect_arrays_none(w):
    """9.2: 구조 결함(isolated_node) -> undefined = defects, 배열 None (예외 아님)."""
    ck = SmallSignalCircuit(mos=(MosSmallSignal(2, 1, 0, 0, 1e-3, 0.0, 1e-5),), capacitors=(Capacitor(2, 0, 1e-12),),
                            ac_ground=(0,))
    sysm = build_mna(ck, (Excitation("vin", voltages=((1, 1.0),)),), (Sense(2), Sense(7)))
    assert "isolated_node" in codes(sysm.defects)        # 입력 확인
    s = response_sensitivity(sysm, lut_parameters(ck, (0.02,)), w)
    assert s.values is None and s.d_param is None
    assert "isolated_node" in codes(s.undefined)


# ---------------------------------------------------------------- R-8: 입력 규약

def test_r8_other_circuit_parameter_set_value_error():
    """다른 회로의 ParameterSet(이 계에 없는 노드) -> ValueError(배선 결함)."""
    ck, sysm, _ = _miller()
    other = circuit12((mos_t(52, 51, 50, 50, 1e-3, 0.0, 1e-5),), (), ((52, 50, 1e-12),), ac_ground=(50,))
    with pytest.raises(ValueError):
        response_sensitivity(sysm, lut_parameters(other, (0.02,)), 1e6)


def test_r8_negative_check_cut_system_takes_original_parameter_set():
    """음성 대조: 같은 회로·절단 계(MOS 단자 그대로)의 원래 회로 ParameterSet 은 거부하지 않는다."""
    ck, sysm, _ = _ex7v_cut()
    assert isinstance(response_sensitivity(sysm, lut_parameters(ck, (0.02,)), 1e6), ResponseSensitivity)
    ck, sysm, _ = _miller()
    assert isinstance(response_sensitivity(sysm, lut_parameters(ck, MILLER_EPS), 1e6), ResponseSensitivity)


@pytest.mark.parametrize("bad", ["system", "parameters"])
def test_r8_type_errors(bad):
    ck, sysm, _ = _miller()
    ps = lut_parameters(ck, MILLER_EPS)
    with pytest.raises(TypeError):
        if bad == "system":
            response_sensitivity(ck, ps, 1e6)
        else:
            response_sensitivity(sysm, tuple(ps.params), 1e6)


@pytest.mark.parametrize("w", [-1.0, math.nan, math.inf])
def test_omega_value_errors(w):
    ck, sysm, _ = _miller()
    with pytest.raises(ValueError):
        response_sensitivity(sysm, lut_parameters(ck, MILLER_EPS), w)


# ---------------------------------------------------------------- R-9: 조립 0

def test_r9_no_stamp_or_assembly_calls():
    """response_sensitivity 동안 mos_stamps·two_terminal_stamps·build_mna 호출 0."""
    ck, sysm, _ = _ex7v_cut()
    ps = lut_parameters(ck, (0.02,))
    with count_calls(mos_stamps, two_terminal_stamps, build_mna) as n:
        for w in (0.0, 1e6, 1e9):
            response_sensitivity(sysm, ps, w)
    assert n == {"mos_stamps": 0, "two_terminal_stamps": 0, "build_mna": 0}


# ---------------------------------------------------------------- R-6: 노드 재번호

@pytest.mark.parametrize("w", [0.0, 3e7])
def test_r6_renumbering_invariance(w):
    """노드 번호만 바꾼 같은 회로 -> 값·∂V/∂p 같음(상대 ≤ 1e-12, R-6). 정확히 0 인 민감도(DC 에서 M1 source 전압 0 -> gmb 몫 0)는
    상대 비교가 무의미하므로 p 배 민감도를 풀이 반올림 바닥 n·eps·|V| 와 함께 본다."""
    ck, sysm = miller_v_system()
    ck2, sysm2 = miller_v_system(nm=RENUM)
    ps, ps2 = lut_parameters(ck, MILLER_EPS), lut_parameters(ck2, MILLER_EPS)
    a = response_sensitivity(sysm, ps, w)
    b = response_sensitivity(sysm2, ps2, w)
    va, vb = np.asarray(a.values), np.asarray(b.values)
    assert np.all(np.abs(va - vb) <= 1e-12 * np.maximum(np.abs(va), np.abs(vb)))
    p = np.array([MILLER_V_MOS[k][MOS_IX[nm]] for k, nm in ps.params])[:, None, None]
    x, y = np.asarray(a.d_param) * p, np.asarray(b.d_param) * p
    floor = 5 * EPS * np.abs(va)[None]                    # 미지수 5개
    assert np.all(np.abs(x - y) <= 1e-12 * np.maximum(np.abs(x), np.abs(y)) + floor)


def test_parameter_set_shape_and_unknown_field_types():
    """ResponseSensitivity 모양: values·errors (r, m), d_param (P, r, m)."""
    ck, sysm, ref = _ex7v_cut()
    ps = lut_parameters(ck, (0.02,))
    assert isinstance(ps, ParameterSet)
    s = response_sensitivity(sysm, ps, 1e7)
    r, m = len(ref["senses"]), len(ref["columns"])
    assert np.asarray(s.values).shape == (r, m) and np.asarray(s.errors).shape == (r, m)
    assert np.asarray(s.d_param).shape == (len(ps.params), r, m)
    assert np.all(np.asarray(s.errors) >= 0.0)
