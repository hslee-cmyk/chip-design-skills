"""`offset_systematic` -- 설계 40 §3.8-8 `offset_sys_mv`(계통 offset: 봉인 DC 동작점의 입력 차 0 출력 오차 / A_dm, 차동 = Vop − Vom,
단일 = 선언 출력 기준 DC, 없으면 `reference_undeclared`), 체크리스트 D-OF3, metrics CONTRACT 10.3.

oracle (a): A_dm 은 손 회로 폐형식(저항 부하 대칭 차동쌍 A = gm/(1/R + gds), 단일 CS A = −gm/(1/R + gds)), 노드 전압은 test 입력이다.
기준 수치(작성자 앵커 재유도): A = 1e-3/(1e-4 + 1e-5) = 9.0909, 오차 2 mV -> 2/9.0909 = 0.22 mV.
분해능 = (오차를 이루는 넷들의 허용오차 합)/|A_dm| (계약 10.3 문장).
"""
from __future__ import annotations

import pytest

from gmid_engine.authoring import ViewDecl
from gmid_engine.metrics import OffsetSystematic, offset_systematic

from . import u7_hand as H
from .conftest import codes

A_PAIR = 1e-3 / (1e-4 + 1e-5)


def _pair():
    nets, m, r, ground, inputs = H.diff_pair()
    return H.circuit(nets, m, r, ground, inputs)


def _cs():
    nets = ("gnd", "vdd", "in", "out")
    m = (H.mos("M1", "out", "in", "gnd", "gnd", 1e-3, 1e-5),)
    return H.circuit(nets, m, (H.res("R1", "vdd", "out", 1e4),), ("gnd", "vdd"), ("in",))


def test_differential_anchor():
    got = offset_systematic(_pair(), H.transfer({"ip": 0.5, "im": -0.5}, "op", "om"), (("op", 0.901), ("om", 0.899)), ())
    assert isinstance(got, OffsetSystematic) and got.undefined == ()
    assert got.a_dm == pytest.approx(A_PAIR, rel=1e-12)
    assert got.output_error_v == pytest.approx(0.002, rel=1e-9)
    assert got.sys_mv == pytest.approx(0.002 / A_PAIR * 1e3, rel=1e-9)
    assert got.sys_mv == pytest.approx(0.22, rel=1e-9)


def test_sign_kept_in_error_magnitude_in_value():
    got = offset_systematic(_pair(), H.transfer({"ip": 0.5, "im": -0.5}, "op", "om"), (("op", 0.899), ("om", 0.901)), ())
    assert got.output_error_v == pytest.approx(-0.002, rel=1e-9)
    assert got.sys_mv == pytest.approx(0.22, rel=1e-9)


def test_single_output_uses_declared_reference():
    got = offset_systematic(_cs(), H.transfer({"in": 1.0}, "out"), (("out", 0.95),), (("out", 0.9), ("other", 0.1)))
    a = -1e-3 / (1e-4 + 1e-5)
    assert got.a_dm == pytest.approx(a, rel=1e-12)
    assert got.output_error_v == pytest.approx(0.05, rel=1e-9)
    assert got.sys_mv == pytest.approx(0.05 / abs(a) * 1e3, rel=1e-9)


def test_single_output_without_reference_is_undeclared():
    got = offset_systematic(_cs(), H.transfer({"in": 1.0}, "out"), (("out", 0.95),), (("other", 0.1),))
    assert got.sys_mv is None and codes(got.undefined) == {"reference_undeclared"}


def test_other_undefined_codes():
    view = H.transfer({"ip": 0.5, "im": -0.5}, "op", "om")
    assert codes(offset_systematic(_pair(), ViewDecl("ratio"), (("op", 1.0), ("om", 1.0)), ()).undefined) == {"unsupported_view"}
    assert codes(offset_systematic(_pair(), view, (("op", 1.0),), ()).undefined) == {"output_dc_missing"}
    nets = ("gnd", "vdd", "in", "out")
    dead = H.circuit(nets, (H.mos("M1", "out", "in", "gnd", "gnd", 0.0, 1e-5),), (H.res("R1", "vdd", "out", 1e4),), ("gnd", "vdd"), ("in",))
    got = offset_systematic(dead, H.transfer({"in": 1.0}, "out"), (("out", 0.95),), (("out", 0.9),))
    assert codes(got.undefined) == {"gain_zero"} and got.sys_mv is None
    assert got.output_error_v == pytest.approx(0.05, rel=1e-12)


def test_resolution_is_net_tolerance_sum_over_gain():
    view = H.transfer({"ip": 0.5, "im": -0.5}, "op", "om")
    got = offset_systematic(_pair(), view, (("op", 0.901), ("om", 0.899)), (), {"op": 1e-3, "om": 2e-3})
    assert got.resolution_mv == pytest.approx(3e-3 / A_PAIR * 1e3, rel=1e-9)
    assert offset_systematic(_pair(), view, (("op", 0.901), ("om", 0.899)), (), {"op": 1e-3}).resolution_mv is None
    assert offset_systematic(_pair(), view, (("op", 0.901), ("om", 0.899)), ()).resolution_mv is None


def test_name_bijection_invariance():
    nets, m, r, ground, inputs = H.diff_pair()
    nmap = {"op": "zz", "om": "aa", "ip": "k1", "im": "k0", "t": "tt", "vdd": "p", "gnd": "q", "vb": "w"}
    nets2, m2, r2 = H.rename(nets, m, r, nmap, {"M1": "X", "M2": "Y", "M3": "Z", "R1": "S", "R2": "T"}, order_seed=3)
    ss2 = H.circuit(nets2, m2, r2, [nmap[g] for g in ground], [nmap[i] for i in inputs])
    a = offset_systematic(_pair(), H.transfer({"ip": 0.5, "im": -0.5}, "op", "om"), (("op", 0.901), ("om", 0.899)), ())
    b = offset_systematic(ss2, H.transfer({"k1": 0.5, "k0": -0.5}, "zz", "aa"), (("zz", 0.901), ("aa", 0.899)), ())
    assert b.sys_mv == pytest.approx(a.sys_mv, rel=1e-12) and b.a_dm == pytest.approx(a.a_dm, rel=1e-12)
