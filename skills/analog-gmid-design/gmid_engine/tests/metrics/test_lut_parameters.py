"""`lut_parameters` (LUT 에서 온 MOS 소신호 파라미터·Δp = ε·|p|·단위 스탬프 항목) -- metrics CONTRACT 9.1.

기대값 근거: 9.1 문장(파라미터 집합·Δp 식·필드 뜻·입력 규약), 9.5 예 7 + ε = 0.02, 3.1 MOS 스탬프 식(단위 스탬프 = 파라미터 p 만 1 로 둔
`MosSmallSignal` 의 `mos_stamps` 항목 -- 계약이 정본 재사용을 명시하므로 공개 `mos_stamps` 를 그 정의로 쓴다. 그 식 자체는
test_stamp_mos 가 따로 확인한다).
"""
from __future__ import annotations

import math
from collections import Counter

import numpy as np
import pytest

from gmid_engine.metrics import (
    LUT_PARAMETERS,
    Capacitor,
    MosSmallSignal,
    ParameterSet,
    Resistor,
    SmallSignalCircuit,
    lut_parameters,
    mos_stamps,
)

from .conftest import EX7_CAP, EX7_MOS12, LUT_P, MILLER_V_CAP, MILLER_V_MOS, MILLER_V_RES, MOS_IX, circuit12, lut_params_of

CAPS = ("cgs", "cgd", "cgb")


def _ex7():
    return circuit12(EX7_MOS12, (), EX7_CAP)


def _miller():
    return circuit12(MILLER_V_MOS, MILLER_V_RES, MILLER_V_CAP)


def test_lut_parameters_constant():
    """9.1: LUT 파라미터 = (gm, gmb, gds, cgs, cgd, cgb) -- 접합 cdb·csb 와 수동소자는 들지 않는다."""
    assert tuple(LUT_PARAMETERS) == LUT_P
    assert "cdb" not in LUT_PARAMETERS and "csb" not in LUT_PARAMETERS


def test_example7_params_and_delta():
    """9.5: 예 7 + ε 0.02 -> params ((0, gm), (0, gds)) (gmb·용량 0 은 빠진다), delta = ε·|p| = (2e-5, 2e-7)."""
    ps = lut_parameters(_ex7(), (0.02,))
    assert isinstance(ps, ParameterSet)
    assert tuple(ps.params) == ((0, "gm"), (0, "gds"))
    assert np.asarray(ps.delta).shape == (2,)
    # Δp = ε·|p| 한 번의 곱(IEEE 곱은 교환 법칙이 정확) -> 같은 곱과 비트 동일
    assert list(ps.delta) == [0.02 * 1e-3, 0.02 * 1e-5]
    assert tuple(ps.rel_tol) == (0.02,)
    assert tuple(ps.undetermined) == ()


def test_all_six_parameters_and_negative_capacitance_magnitude():
    """9.1: 값 ≠ 0 인 LUT 파라미터 전부(MOS 순번, LUT_PARAMETERS 순서), 용량은 부호 있는 값이라 Δp = ε·|p|(음의 cgb 도 양수 Δ).
    cdb·csb(≠ 0)는 파라미터가 아니다."""
    eps = (0.01, 0.03)
    ps = lut_parameters(_miller(), eps)
    exp = lut_params_of(MILLER_V_MOS)
    assert len(exp) == 12                                # 두 MOS x 6 (모두 ≠ 0) -- 입력 확인
    assert tuple(ps.params) == exp
    assert list(ps.delta) == [eps[k] * abs(MILLER_V_MOS[k][MOS_IX[nm]]) for k, nm in exp]
    cgb = [i for i, (k, nm) in enumerate(exp) if nm == "cgb"]
    assert all(MILLER_V_MOS[exp[i][0]][MOS_IX["cgb"]] < 0.0 for i in cgb)   # 입력 확인: 음의 cgb
    assert all(ps.delta[i] > 0.0 for i in cgb)


def _unit_entries(dev, name):
    """3.1 식의 단위 스탬프: 파라미터 name 만 1, 나머지 0 인 MosSmallSignal 의 mos_stamps 항목 (행, 열, 값, 용량 여부)."""
    kw = {nm: 0.0 for nm in ("gm", "gmb", "gds", "cgs", "cgd", "cgb", "cdb", "csb")}
    kw[name] = 1.0
    st = mos_stamps(MosSmallSignal(dev.d, dev.g, dev.s, dev.b, **kw))
    return Counter([(r, c, v, False) for r, c, v in st.g] + [(r, c, v, True) for r, c, v in st.c])


@pytest.mark.parametrize("which", ["ex7", "miller"])
def test_unit_stamps_are_mos_stamps_of_unit_parameter(which):
    """9.1: rows·cols·values·capacitive·owner = 파라미터 p 만 1 로 둔 MosSmallSignal 의 mos_stamps 항목(owner = params 위치)."""
    ck = _ex7() if which == "ex7" else _miller()
    eps = (0.02,) if which == "ex7" else (0.01, 0.03)
    ps = lut_parameters(ck, eps)
    rows, cols, vals = np.asarray(ps.rows), np.asarray(ps.cols), np.asarray(ps.values)
    capf, owner = np.asarray(ps.capacitive), np.asarray(ps.owner)
    assert rows.shape == cols.shape == vals.shape == capf.shape == owner.shape
    assert set(owner.tolist()) == set(range(len(ps.params)))
    for i, (k, name) in enumerate(ps.params):
        sel = owner == i
        got = Counter(zip(rows[sel].tolist(), cols[sel].tolist(), vals[sel].tolist(), [bool(x) for x in capf[sel]]))
        assert got == _unit_entries(ck.mos[k], name), (k, name)
        assert all(bool(x) == (name in CAPS) for x in capf[sel])


def test_epsilon_zero_and_none():
    """ε = 0 -> Δ 0(허용, 음수만 거부). None -> undetermined 에 그 MOS 순번(9.1 '미정')."""
    ps0 = lut_parameters(_miller(), (0.0, 0.03))
    for i, (k, _) in enumerate(ps0.params):
        assert (ps0.delta[i] == 0.0) if k == 0 else (ps0.delta[i] > 0.0)
    assert tuple(ps0.undetermined) == ()
    assert tuple(lut_parameters(_miller(), (None, 0.03)).undetermined) == (0,)
    assert tuple(lut_parameters(_miller(), (0.01, None)).undetermined) == (1,)
    assert tuple(lut_parameters(_ex7(), (None,)).undetermined) == (0,)


def test_rel_tol_normalized_tuple():
    """9.1 `rel_tol` = 정규화 tuple -- 정수 ε 도 실수로."""
    ps = lut_parameters(_ex7(), (1,))
    assert tuple(ps.rel_tol) == (1.0,) and isinstance(ps.rel_tol[0], float)
    assert list(ps.delta) == [1e-3, 1e-5]


def test_no_mos_circuit_empty():
    """MOS 없는 회로(예 6) -> params () (9.5 예 6)."""
    ck = SmallSignalCircuit(resistors=(Resistor(1, 2, 1e3), Resistor(2, 3, 1e4)), ac_ground=(0,))
    ps = lut_parameters(ck, ())
    assert tuple(ps.params) == () and np.asarray(ps.delta).shape == (0,)


def test_passives_not_parameters():
    """수동소자 값은 Δp 대상이 아니다(9.1)."""
    ck = SmallSignalCircuit(mos=(MosSmallSignal(2, 1, 0, 0, 1e-3, 0.0, 1e-5),), resistors=(Resistor(2, 0, 1e4),),
                            capacitors=(Capacitor(2, 0, 1e-12),), ac_ground=(0,))
    assert tuple(lut_parameters(ck, (0.05,)).params) == ((0, "gm"), (0, "gds"))


@pytest.mark.parametrize("bad", ["not_circuit", "list", "short", "long", "bool", "str"])
def test_type_errors(bad):
    """9.1 입력 규약: circuit 형식·rel_tol tuple 아님·길이 ≠ MOS 수·원소 bool·비수 -> TypeError."""
    ck = _ex7()
    args = {"not_circuit": (ck.mos, (0.02,)), "list": (ck, [0.02]), "short": (ck, ()), "long": (ck, (0.02, 0.02)),
            "bool": (ck, (True,)), "str": (ck, ("0.02",))}[bad]
    with pytest.raises(TypeError):
        lut_parameters(*args)


@pytest.mark.parametrize("bad", [-0.01, math.nan, math.inf, -math.inf])
def test_value_errors(bad):
    """9.1: 원소 음수·비유한 -> ValueError."""
    with pytest.raises(ValueError):
        lut_parameters(_ex7(), (bad,))


@pytest.mark.parametrize("ok", [0.0, 0.02, 1, None])
def test_negative_check_valid_inputs_do_not_raise(ok):
    """거부 게이트의 음성 대조 -- 유효한 ε 는 통과한다."""
    assert isinstance(lut_parameters(_ex7(), (ok,)), ParameterSet)
