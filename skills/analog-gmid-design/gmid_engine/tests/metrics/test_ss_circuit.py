"""`ss_circuit`(S2 열 -> 정수 인덱스 SmallSignalCircuit) -- metrics CONTRACT 7.3 (+ 1절 Q7 부호 있는 용량).

기대값은 계약 문장(노드 = nodes 위치, MOS -> MosSmallSignal(d, g, s, b, ...), 수동소자 값 있으면 스탬프·없으면 missing,
이상 전류원 개방, 그 밖 원소 거부)을 손으로 옮긴 것이다.
"""
from __future__ import annotations

import pytest

from gmid_engine.core import StructureUnresolvedError
from gmid_engine.metrics import Capacitor, MosSmallSignal, Resistor, SsCircuit, SmallSignalCircuit, ss_circuit

from .conftest import hand_ss

NODES = ("gnd", "in", "out", "vdd", "x")            # 위치 = 인덱스: gnd 0, in 1, out 2, vdd 3, x 4
MOS_PINS = (("d", "out"), ("g", "in"), ("s", "gnd"))


def _mos(name="M1", pins=MOS_PINS, bulk="gnd", ss="default", kind="nmos"):
    if ss == "default":
        ss = hand_ss(1e-3, 1e-5, gmb=2e-4, cgs=3e-15, cgd=-4e-16, cgb=-2.03e-16, cdb=5e-16, csb=6e-16)
    return (name, "mos", kind, pins, bulk, ss)


def _two(name, cls, kind, a, b):
    return (name, cls, kind, (("t0", a), ("t1", b)), None, None)


BASE = (
    _mos(),
    _mos("M2", (("d", "out"), ("g", "x"), ("s", "vdd")), "vdd", hand_ss(2e-3, 2e-5), "pmos"),
    _two("R1", "passive", "resistor", "vdd", "x"),
    _two("CL", "passive", "capacitor", "out", "gnd"),
    _two("Cf", "passive", "capacitor", "out", "in"),
    _two("I1", "ideal_source", "current_source", "vdd", "x"),
)
VALUES = (("CL", 1e-12), ("Cf", 5e-13), ("R1", 1e5))


def _call(devices=BASE, values=VALUES, ground=("vdd", "gnd"), inputs=("in",)):
    return ss_circuit(NODES, ground, inputs, devices, values)


def test_mos_record_from_columns():
    """MOS -> MosSmallSignal(d, g, s, b, gm, gmb, gds, cgs, cgd, cgb, cdb, csb, label=이름), b = bulk 넷 인덱스."""
    res = _call()
    assert isinstance(res, SsCircuit) and isinstance(res.circuit, SmallSignalCircuit)
    m1, m2 = res.circuit.mos
    ss = BASE[0][5]
    assert (m1.d, m1.g, m1.s, m1.b, m1.label) == (2, 1, 0, 0, "M1")
    assert (m1.gm, m1.gmb, m1.gds) == (ss.gm, ss.gmb, ss.gds)
    assert (m1.cgs, m1.cgd, m1.cgb, m1.cdb, m1.csb) == (ss.cgs, ss.cgd, ss.cgb, ss.cdb, ss.csb)
    assert (m2.d, m2.g, m2.s, m2.b, m2.label) == (2, 4, 3, 3, "M2")


def test_negative_caps_stamped_as_is():
    """Q7 결정 (a): LUT v2 의 음의 용량(예: nmcnr cgb −2.03e-16 F)은 거부·절댓값 없이 그대로 MosSmallSignal 에 실린다."""
    m1 = _call().circuit.mos[0]
    assert m1.cgb == -2.03e-16 and m1.cgd == -4e-16


def test_passives_with_values_and_order():
    """값 있는 수동소자 -> Resistor/Capacitor(t0, t1, 값, label). resistors·capacitors = 회로 원소 순서의 이름."""
    res = _call()
    c = res.circuit
    assert c.resistors == (Resistor(3, 4, 1e5, label="R1"),)
    assert c.capacitors == (Capacitor(2, 0, 1e-12, label="CL"), Capacitor(2, 1, 5e-13, label="Cf"))
    assert res.resistors == ("R1",)
    assert res.capacitors == ("CL", "Cf")
    assert res.missing == ()


def test_ideal_current_source_is_open():
    """이상 전류원: 스탬프 없음(소신호 개방) -- 저항·커패시터·MOS 어디에도 안 나타나고 missing 에도 없다."""
    res = _call()
    labels = {e.label for e in res.circuit.mos + res.circuit.resistors + res.circuit.capacitors}
    assert "I1" not in labels and "I1" not in res.missing


def test_missing_passive_values_recorded():
    """값 없는 수동소자는 스탬프하지 않고 missing 에(이름순) -- 예외 없음."""
    res = _call(values=(("CL", 1e-12),))
    assert res.missing == ("Cf", "R1")
    assert res.circuit.resistors == () and res.circuit.capacitors == (Capacitor(2, 0, 1e-12, label="CL"),)
    # resistors·capacitors 이름 목록에 값 없는 소자가 드는지는 계약(7.3)이 정하지 않아 확인하지 않는다(보고 항목)


def test_ground_input_sorted_and_ac_ground_empty():
    """`circuit.ac_ground == ()`(뷰가 정한다), ground_nets·input_nets 정렬."""
    res = _call(ground=("vdd", "gnd"), inputs=("in",))
    assert res.circuit.ac_ground == ()
    assert res.ground_nets == ("gnd", "vdd")
    assert res.input_nets == ("in",)
    assert res.nodes == NODES


@pytest.mark.parametrize("case", ["voltage_source", "bulk_none", "ss_none", "other_passive_kind"])
def test_unsupported_element_rejected(case):
    """이상 전압원·다른 수동 kind·bulk None·SsDevice None -> StructureUnresolvedError(unsupported_rule_branch, ss_element_kind)."""
    devices = list(BASE)
    if case == "voltage_source":
        bad = _two("V1", "ideal_source", "voltage_source", "x", "gnd")
        devices.append(bad)
    elif case == "bulk_none":
        bad = _mos(bulk=None)
        devices[0] = bad
    elif case == "ss_none":
        bad = _mos(ss=None)
        devices[0] = bad
    else:
        bad = _two("L1", "passive", "inductor", "x", "gnd")
        devices.append(bad)
    with pytest.raises(StructureUnresolvedError) as ei:
        _call(tuple(devices))
    rec = ei.value.record
    det = dict(rec.detail)
    assert det["reason"] == "unsupported_rule_branch"
    assert det["rule_branch"] == "ss_element_kind"
    assert bad[0] in rec.devices


def test_negative_check_base_is_accepted():
    """위 거부 test 의 대조: 같은 원소 목록에서 문제 원소만 없으면 예외가 없다."""
    _call(BASE)
    _call(BASE + (_two("I2", "ideal_source", "current_source", "x", "gnd"),))


# ---------------------------------------------------------------- [IT-2c T-RN] 지원 밖 원소 -- `ss_circuit_field` 직접 호출 (interface 빈칸 답 5)
# 지원 밖 kind 는 S1 `s1_dc_conduction` 이 먼저 정지시켜 파이프라인으로는 닿지 않으므로, 봉인 toy 스냅샷의 열을 손으로 바꿔 블록을 직접 부른다.
# oracle: (독립) 기존 `ss_circuit` 거부 사례(위 test_unsupported_element_rejected)와 같은 계약 -- reason unsupported_rule_branch, rule_branch ss_element_kind, 그 소자 이름.

def _sealed_ss_snapshot(tmp):
    from gmid_engine.metrics import ss_evaluate
    from gmid_engine.sizing import SealedSnapshot
    from .test_ss_evaluate import build, theta
    spec, ctx, ev, js = build(tmp)
    return ss_evaluate(SealedSnapshot(ev.snapshot, ev.report), ctx, theta(), spec.constraints, ("vdd",), junction=js).snapshot


def _tamper(snap, field, name, value, version):
    from .conftest import hand_write
    col = dict(snap.column("device", field))
    col[name] = value
    return hand_write(snap, "device", field, col, version=version)


def _field_call(snap):
    from gmid_engine.metrics.ss_circuit import ss_circuit_field
    from .conftest import fresh_run
    return ss_circuit_field(snap, **fresh_run())


def test_it2c_rn_control_untouched_snapshot_is_accepted(tmp_path):
    """oracle 대조: (독립) T-RN 대조 -- 열을 바꾸지 않은 봉인 스냅샷은 블록이 거부하지 않는다."""
    _field_call(_sealed_ss_snapshot(tmp_path))


@pytest.mark.parametrize("case", ["voltage_source", "inductor", "bulk_none"])
def test_it2c_rn_unsupported_element_rejected_by_ss_circuit_field(tmp_path, case):
    snap = _sealed_ss_snapshot(tmp_path)
    if case == "voltage_source":
        snap = _tamper(snap, "element_class", "R1", "ideal_source", "t_rn_cls")
        snap = _tamper(snap, "kind", "R1", "voltage_source", "t_rn_kind")
        bad = "R1"
    elif case == "inductor":
        snap = _tamper(snap, "kind", "R1", "inductor", "t_rn_kind")
        bad = "R1"
    else:
        snap = _tamper(snap, "bulk", "M1", None, "t_rn_bulk")
        bad = "M1"
    with pytest.raises(StructureUnresolvedError) as ei:
        _field_call(snap)
    rec = ei.value.record
    det = dict(rec.detail)
    assert det["reason"] == "unsupported_rule_branch" and det["rule_branch"] == "ss_element_kind"
    assert bad in rec.devices
