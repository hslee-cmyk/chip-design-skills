"""`ls_fields` -- 설계 40 §3.8-3('ls' 필드: 방향별 최대 전류 = DEC-65 β·σ·κ 규칙, 슬루 등가 용량 `ls.c_slew_farad`, driving_spec 이면 제약 행),
체크리스트 D-GB8a, 계약 10.0.

oracle (a) 손계산:
* c_slew(out) = 노드 out 에 한 단자가 닿은 용량 크기 합: Mp(cgd 2 fF, cdb 3 fF) + Mn(cgd 1 fF, cdb 4 fF) + CL 1 pF = 1.010 pF
  (Mn 의 cgs 5 fF 는 g-s 라 out 에 닿지 않는다).
* β 셀(바이어스) = 봉인 ID, σ 셀 = ID(VGS_max) -- VGS_max(경로 합 게이트 상한 − source DC)가 봉인 VGS 이하면 봉인 ID, κ 셀 = 미상(None).
* 슬루율 = 전류 / c_slew. 분해능: β 셀 = 부동소수 해상도 × I, σ 셀 = rel_tol × I.
* 피크 부하 여유 = 출력 노드 방향 전류 최솟값 − load_peak_amp.
"""
from __future__ import annotations

import sys
import types

import pytest

from gmid_engine.authoring import DrivingDecl
from gmid_engine.metrics import Capacitor, LsFields, LsNode, MosSmallSignal, SmallSignalCircuit, SsCircuit, ls_fields

from . import u7_hand as H

NETS = ("gnd", "vdd", "in", "vbp", "out", "x")


def _ss():
    i = {n: k for k, n in enumerate(NETS)}
    mos = (MosSmallSignal(i["out"], i["vbp"], i["vdd"], i["vdd"], 1e-4, 0.0, 1e-6, cgd=2e-15, cdb=3e-15, label="Mp"),
           MosSmallSignal(i["out"], i["in"], i["gnd"], i["gnd"], 3e-4, 0.0, 2e-6, cgs=5e-15, cgd=1e-15, cdb=4e-15, label="Mn"),
           MosSmallSignal(i["x"], i["in"], i["gnd"], i["gnd"], 1e-4, 0.0, 1e-6, cdb=1e-15, label="Mk"))
    return SsCircuit(NETS, SmallSignalCircuit(mos=mos, capacitors=(Capacitor(i["out"], i["gnd"], 1e-12, label="CL"),)), (), ("CL",),
                     ("gnd", "vbp", "vdd"), ("in",))


def _op(kind, current, vgs):
    return types.SimpleNamespace(kind=kind, current=current, vgs=vgs, vds=0.9, vsb=0.0, W=1e-6, L=1e-6, w_key=100)


OPS = {"Mp": _op("pmos", 20e-6, 0.7), "Mn": _op("nmos", 30e-6, 0.6), "Mk": _op("nmos", 5e-6, 0.6)}
VOLTS = {"gnd": 0.0, "vdd": 1.8, "in": 0.6, "out": 0.9, "x": 0.5, "vbp": 1.1}
BOUNDS = (("in", 0.3, 0.55), ("out", 0.2, 1.5), ("x", 0.1, 1.7))           # in 상한 0.55 < 봉인 VGS 0.6 -> σ 셀 = 봉인 ID


def _vs(dirs, poles=("out",)):
    return H.vstruct("t", {"in": 1.0}, ("out",), (), pole_nets=poles, directions=dirs)


OUT_DIR = ("out", "class_a", (("Mp", "beta"),), (("Mn", "sigma"),))


def test_slew_capacitance_and_direction_currents():
    got = ls_fields(_ss(), _vs((OUT_DIR,)), OPS, VOLTS, BOUNDS, None, {"Mn": 0.01, "Mp": 0.02, "Mk": 0.01})
    assert isinstance(got, LsFields)
    (node,) = got.nodes
    assert isinstance(node, LsNode) and node.net == "out"
    c = 2e-15 + 3e-15 + 1e-15 + 4e-15 + 1e-12
    assert node.c_slew_farad == pytest.approx(c, rel=1e-12)
    assert node.i_charge_a == pytest.approx(20e-6, rel=1e-15) and node.i_discharge_a == pytest.approx(30e-6, rel=1e-15)
    assert node.slew_charge_v_per_s == pytest.approx(20e-6 / c, rel=1e-12)
    assert node.slew_discharge_v_per_s == pytest.approx(30e-6 / c, rel=1e-12)
    assert node.i_charge_res_a == pytest.approx(sys.float_info.epsilon * 20e-6, rel=1e-12)       # β 셀: θ 전류
    assert node.i_discharge_res_a == pytest.approx(0.01 * 30e-6, rel=1e-12)
    assert sorted(node.sources) == [("charge", "Mp", "beta", pytest.approx(20e-6)), ("discharge", "Mn", "sigma", pytest.approx(30e-6))]
    assert got.load_peak_margin_a is None


def test_kappa_cell_makes_direction_unbounded():
    dirs = (("out", "class_a", (("Mp", "beta"),), (("Mn", "sigma"), ("Mk", "kappa"))),)
    (node,) = ls_fields(_ss(), _vs(dirs), OPS, VOLTS, BOUNDS, None, {}).nodes
    assert node.i_discharge_a is None and node.slew_discharge_v_per_s is None
    assert node.i_charge_a == pytest.approx(20e-6)


def test_no_supply_cells_or_no_direction_record():
    dirs = (("out", "none", (), (("Mn", "sigma"),)),)
    (node,) = ls_fields(_ss(), _vs(dirs, poles=("out", "x")), OPS, VOLTS, BOUNDS, None, {}).nodes     # x 는 방향 기록 없음 -> 대상 아님
    assert node.net == "out" and node.i_charge_a is None


def test_sigma_resolution_needs_tolerance():
    (node,) = ls_fields(_ss(), _vs((OUT_DIR,)), OPS, VOLTS, BOUNDS, None, {}).nodes
    assert node.i_discharge_a == pytest.approx(30e-6) and node.i_discharge_res_a is None


def test_load_peak_margin():
    drv = DrivingDecl(None, 15e-6, None)
    got = ls_fields(_ss(), _vs((OUT_DIR,)), OPS, VOLTS, BOUNDS, None, {"Mn": 0.01}, drv, ("out",))
    assert got.load_peak_margin_a == pytest.approx(20e-6 - 15e-6, rel=1e-12)
    assert ls_fields(_ss(), _vs((OUT_DIR,)), OPS, VOLTS, BOUNDS, None, {}, drv, ("x",)).load_peak_margin_a is None
