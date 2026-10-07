"""`dc_inputs_from_spec(spec) -> DcInputs` -- CONTRACT 1.1·1.2: 사람 선언 투영. 결정 대기 칸은 '미선언'으로 투영하고 막지
않는다(pending 에 기록만).

입력: library `*.sizing_spec.json` 을 authoring `load_sizing_spec` 으로 읽은 `SizingSpecDoc`(입력 생성용) + 그 필드를
`dataclasses.replace` 로 바꾼 변형. 기대값은 1.2 의 투영 규칙을 이 파일에서 따로 적용한다.
"""
import dataclasses

import pytest

from gmid_engine.authoring import (InputDc, PendingMark, RegionDecl, ElementValue, load_sizing_spec,
                                   load_topology)
from gmid_engine.sizing import DcInputs, dc_inputs_from_spec

from .conftest import LIBRARY, NINE, spec_catalog

CATALOG = spec_catalog()

_CACHE = {}


def spec_of(name):
    if name not in _CACHE:
        topo = load_topology(str(LIBRARY / (name + ".topology.json")))
        _CACHE[name] = load_sizing_spec(str(LIBRARY / (name + ".sizing_spec.json")), topo, CATALOG)
    return _CACHE[name]


def expected_projection(spec):
    """CONTRACT 1.2 규칙을 독립 적용."""
    idc = spec.input_dc
    if idc.mode == "net":
        input_dc_v = dict(spec.supplies_v)[idc.net]
    elif idc.mode == "value":
        input_dc_v = idc.value_v
    else:
        input_dc_v = None
    nt = spec.node_voltage_targets_v if isinstance(spec.node_voltage_targets_v, tuple) else ()
    ev = tuple((e.name, e.value if e.mode == "value" else None) for e in spec.element_values)
    lin = ()
    if isinstance(spec.intended_region, tuple):
        lin = tuple(sorted(r.device for r in spec.intended_region if r.region == "linear"))
    pend = tuple(sorted((p.path, p.decision) for p in spec.pending))
    return DcInputs(tuple(spec.supplies_v), input_dc_v, nt, ev, lin, pend)


@pytest.mark.parametrize("name", NINE)
def test_library_projection(name):
    spec = spec_of(name)
    got = dc_inputs_from_spec(spec)
    assert isinstance(got, DcInputs)
    assert got == expected_projection(spec)
    assert got.supplies_v == spec.supplies_v
    # 결정 대기 칸이 있어도 막지 않고 pending 에 모두 남긴다
    assert len(got.pending) == len(spec.pending)


def test_pending_not_blocking_and_recorded():
    spec = spec_of("two_stage_ota")
    assert spec.input_dc.mode == "pending"
    got = dc_inputs_from_spec(spec)
    assert got.input_dc_v is None
    assert got.node_targets == ()            # PendingMark -> ()
    assert ("human.input_dc", "SP-2") in got.pending
    assert list(got.pending) == sorted(got.pending)


def _base():
    return spec_of("two_stage_ota")


def test_input_dc_net_mode_reads_supply_value():
    spec = dataclasses.replace(_base(), input_dc=InputDc("net", "vdd", None, None, None))
    assert dc_inputs_from_spec(spec).input_dc_v == dict(spec.supplies_v)["vdd"]


def test_input_dc_value_mode():
    spec = dataclasses.replace(_base(), input_dc=InputDc("value", None, 0.75, None, None))
    assert dc_inputs_from_spec(spec).input_dc_v == 0.75


@pytest.mark.parametrize("mode", ["engine", "pending"])
def test_input_dc_engine_or_pending_is_none(mode):
    spec = dataclasses.replace(_base(), input_dc=InputDc(mode, None, None, None, "SP-2" if mode == "pending" else None))
    assert dc_inputs_from_spec(spec).input_dc_v is None


def test_node_targets_tuple_passed_through():
    nt = (("o1", 0.9), ("out", 0.8))
    spec = dataclasses.replace(_base(), node_voltage_targets_v=nt)
    assert dc_inputs_from_spec(spec).node_targets == nt


def test_node_targets_pending_or_none_is_empty():
    for v in (PendingMark("human.node_voltage_targets_v", "CI-15"), None):
        spec = dataclasses.replace(_base(), node_voltage_targets_v=v)
        assert dc_inputs_from_spec(spec).node_targets == ()


def test_element_values_value_vs_other_modes():
    evs = (ElementValue("CL", "value", "value_farad", 3e-12, None, None),
           ElementValue("Cc", "engine", None, None, None, None),
           ElementValue("Rz", "pending", None, None, None, "SP-9"))
    spec = dataclasses.replace(_base(), element_values=evs)
    assert dc_inputs_from_spec(spec).element_values == (("CL", 3e-12), ("Cc", None), ("Rz", None))


def test_linear_devices_from_intended_region_sorted():
    regions = (RegionDecl("M7", "linear", None), RegionDecl("M1", "saturation", None),
               RegionDecl("M3", "linear", None))
    spec = dataclasses.replace(_base(), intended_region=regions)
    assert dc_inputs_from_spec(spec).linear_devices == ("M3", "M7")


def test_linear_devices_pending_region_is_empty():
    spec = dataclasses.replace(_base(), intended_region=PendingMark("human.intended_region", "CI-18"))
    assert dc_inputs_from_spec(spec).linear_devices == ()


@pytest.mark.parametrize("bad", [None, {}, "spec", DcInputs((("gnd", 0.0),))])
def test_type_error_for_non_spec(bad):
    with pytest.raises(TypeError):
        dc_inputs_from_spec(bad)
