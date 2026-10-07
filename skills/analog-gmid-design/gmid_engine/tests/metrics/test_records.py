"""CONTRACT 1절·I-6: 입력 레코드는 생성 때 검사 -- 노드는 정수(문자열 TypeError), 값은 유한 실수, R·C > 0, 기본값 없음."""
import math

import pytest

from gmid_engine.metrics import (
    Capacitor,
    ChannelCurrent,
    CurrentSource,
    DcOperatingPoint,
    Excitation,
    GateArea,
    MosSmallSignal,
    PassiveArea,
    RailBias,
    Resistor,
    Sense,
    SmallSignalCircuit,
)

NAN, INF = math.nan, math.inf


def test_valid_records_construct():
    Resistor(1, 2, 1e3)
    Capacitor(2, 0, 1e-12)
    MosSmallSignal(2, 1, 0, 0, 1e-3, 0.0, 1e-5, cgs=1e-15, cgd=1e-16)
    Excitation("vin", voltages=((1, 1.0),), currents=((2, 1e-6),))
    Sense(2)
    Sense(2, 3)
    RailBias(10, 1.8)
    ChannelCurrent(5, 0, -1e-6)        # 부호 있는 전류 허용
    CurrentSource(10, 7, 5e-6)
    GateArea(1e-6, 1e-7)
    PassiveArea("cc", 1e-12, None)
    SmallSignalCircuit(resistors=(Resistor(1, 0, 1.0),), ac_ground=(0,))
    DcOperatingPoint(rails=(RailBias(0, 0.0),))


# ---------- I-6: 저항·용량 값 기본값 없음 ----------

def test_resistor_none_value_type_error():
    with pytest.raises(TypeError):
        Resistor(1, 2, None)


def test_resistor_missing_value_type_error():
    with pytest.raises(TypeError):
        Resistor(1, 2)


def test_capacitor_none_value_type_error():
    with pytest.raises(TypeError):
        Capacitor(1, 2, None)


@pytest.mark.parametrize("v", [0.0, 0, -1e3, NAN, INF, -INF])
def test_resistor_nonpositive_or_nonfinite_value_error(v):
    with pytest.raises(ValueError):
        Resistor(1, 2, v)


@pytest.mark.parametrize("v", [0.0, -1e-12, NAN, INF])
def test_capacitor_nonpositive_or_nonfinite_value_error(v):
    with pytest.raises(ValueError):
        Capacitor(1, 2, v)


# ---------- 노드는 정수 ----------

@pytest.mark.parametrize(
    "make",
    [
        lambda: Resistor("n1", 2, 1e3),
        lambda: Resistor(1, "out", 1e3),
        lambda: Capacitor("out", 0, 1e-12),
        lambda: MosSmallSignal("d", 1, 0, 0, 1e-3, 0.0, 1e-5),
        lambda: MosSmallSignal(2, 1, 0, "vss", 1e-3, 0.0, 1e-5),
        lambda: Sense("out"),
        lambda: Sense(2, "ref"),
        lambda: Excitation("vin", voltages=(("in", 1.0),)),
        lambda: Excitation("iin", currents=(("out", 1.0),)),
        lambda: SmallSignalCircuit(ac_ground=("gnd",)),
        lambda: RailBias("vdd", 1.8),
        lambda: ChannelCurrent("d", 0, 1e-6),
        lambda: CurrentSource(10, "x", 1e-6),
        lambda: DcOperatingPoint(rails=(RailBias(0, 0.0),), node_v=(("out", 0.5),)),
    ],
    ids=["R_a", "R_b", "C_a", "mos_d", "mos_b", "sense_pos", "sense_neg", "exc_v", "exc_i", "ac_ground",
         "rail", "channel", "source", "node_v"],
)
def test_string_node_type_error(make):
    with pytest.raises(TypeError):
        make()


# ---------- MOS 소신호 값 ----------

@pytest.mark.parametrize("field", ["gm", "gmb", "gds", "cgs", "cgd", "cgb", "cdb", "csb"])
def test_mos_negative_value_error(field):
    kw = dict(d=2, g=1, s=0, b=0, gm=1e-3, gmb=0.0, gds=1e-5)
    kw[field] = -1e-6 if field.startswith("g") else -1e-15
    with pytest.raises(ValueError):
        MosSmallSignal(**kw)


@pytest.mark.parametrize("field", ["gm", "gmb", "gds", "cgd"])
@pytest.mark.parametrize("bad", [NAN, INF])
def test_mos_nonfinite_value_error(field, bad):
    kw = dict(d=2, g=1, s=0, b=0, gm=1e-3, gmb=0.0, gds=1e-5)
    kw[field] = bad
    with pytest.raises(ValueError):
        MosSmallSignal(**kw)


def test_mos_zero_values_allowed():
    MosSmallSignal(2, 1, 0, 0, 0.0, 0.0, 0.0)


# ---------- 나머지 값 필드: 유한 실수 ----------

@pytest.mark.parametrize(
    "make",
    [
        lambda: Excitation("v", voltages=((1, NAN),)),
        lambda: Excitation("i", currents=((1, INF),)),
        lambda: RailBias(10, NAN),
        lambda: ChannelCurrent(5, 0, INF),
        lambda: CurrentSource(10, 7, NAN),
        lambda: GateArea(NAN, 1e-6),
        lambda: GateArea(1e-6, INF),
        lambda: PassiveArea("cc", NAN, 1.0),
        lambda: DcOperatingPoint(rails=(RailBias(0, 0.0),), node_v=((6, NAN),)),
    ],
    ids=["exc_v", "exc_i", "rail", "channel", "source", "gate_w", "gate_l", "passive", "node_v"],
)
def test_nonfinite_value_error(make):
    with pytest.raises(ValueError):
        make()
