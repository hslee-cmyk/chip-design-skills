"""`dc_edges_unpruned(devices, passives, sources) -> tuple[DcEdge]` -- CONTRACT 3.10 (DEC-70 유일 정의, 원소 이름순)."""
from __future__ import annotations

from gmid_engine.authoring import (
    DC_CONDUCTING_PASSIVE_KINDS,
    DcEdge,
    DeviceDecl,
    PassiveDecl,
    SourceDecl,
    dc_edges_unpruned,
    device_declaration,
    passive_declaration,
    source_declaration,
)
from gmid_engine.core import require_immutable


def test_constant():
    assert tuple(DC_CONDUCTING_PASSIVE_KINDS) == ("resistor",)


def _expected_from_json(raw):
    """JSON 직접 집계: MOS (drain, source), resistor terminals, 이상원 terminals -- 이름순, nets 정렬."""
    out = []
    for e in raw["netlist"]:
        out.append((e["name"], tuple(sorted((e["drain"], e["source"])))))
    for e in raw["passive_elements"]:
        if e["kind"] == "resistor":
            out.append((e["name"], tuple(sorted(e["terminals"]))))
    for e in raw.get("ideal_sources", []):
        out.append((e["name"], tuple(sorted(e["terminals"]))))
    return sorted(out)


def test_base_edges(ah):
    raw = ah.base()
    edges = dc_edges_unpruned(device_declaration(raw), passive_declaration(raw), source_declaration(raw))
    assert all(isinstance(e, DcEdge) for e in edges)
    assert [(e.element, e.nets) for e in edges] == _expected_from_json(raw)
    # 손 확인: Cf·Cload(커패시터)·gate·bulk 는 엣지가 아님
    assert [e.element for e in edges] == ["Ib", "Mfx1", "Mfx2", "Mfx3", "Mfx4", "Rf"]
    assert all(isinstance(e.element_kind, str) for e in edges)
    for e in edges:
        require_immutable(e)


def test_non_resistor_passive_kinds_not_edges():
    devs = (DeviceDecl("Mfx1", "nmos", "n_b", "n_g", "n_a", "n_bulk"),)
    pas = (PassiveDecl("L1", "inductor", ("n_a", "n_c")), PassiveDecl("C1", "capacitor", ("n_a", "n_d")),
           PassiveDecl("R1", "resistor", ("n_e", "n_a"), "value_ohm", 5.0))
    srcs = (SourceDecl("V1", "voltage_source", ("n_f", "n_a"), "value_volt", 1.0),)
    edges = dc_edges_unpruned(devs, pas, srcs)
    assert [(e.element, e.nets) for e in edges] == [
        ("Mfx1", ("n_a", "n_b")), ("R1", ("n_a", "n_e")), ("V1", ("n_a", "n_f"))]


def test_any_device_kind_is_edge():
    devs = (DeviceDecl("Z9", "mystery", "n_x", "n_y", "n_z"),)
    assert [(e.element, e.nets) for e in dc_edges_unpruned(devs, (), ())] == [("Z9", ("n_x", "n_z"))]


def test_order_independent_of_input_order(ah):
    raw = ah.base()
    dv, pv, sv = device_declaration(raw), passive_declaration(raw), source_declaration(raw)
    a = dc_edges_unpruned(dv, pv, sv)
    b = dc_edges_unpruned(tuple(reversed(dv)), tuple(reversed(pv)), tuple(reversed(sv)))
    assert a == b


def test_empty():
    assert dc_edges_unpruned((), (), ()) == ()
