"""`device_declaration(doc) -> tuple[DeviceDecl]` -- CONTRACT 3.4 (gate `devices`, where `netlist`)."""
from __future__ import annotations

import pytest

from gmid_engine.authoring import DeviceDecl, device_declaration


def _reject(ah, doc):
    exc, detail = ah.rejected(device_declaration, doc)
    assert detail["gate"] == "devices"
    return detail


def test_base_decls_match_json(ah):
    raw = ah.base()
    got = device_declaration(raw)
    assert all(isinstance(d, DeviceDecl) for d in got)
    exp = {(e["name"], e["kind"], e["drain"], e["gate"], e["source"], e.get("bulk")) for e in raw["netlist"]}
    assert {(d.name, d.kind, d.d, d.g, d.s, d.bulk) for d in got} == exp
    assert len(got) == len(raw["netlist"])


def test_bulk_defaults_to_none(ah):
    got = {d.name: d for d in device_declaration(ah.base())}
    assert got["Mfx1"].bulk is None and got["Mfx2"].bulk == "rail_hi"


def test_kind_unrestricted(ah):
    d = ah.base()
    ah.dev(d, "Mfx1")["kind"] = "npn_whatever"
    assert any(x.kind == "npn_whatever" for x in device_declaration(d))


@pytest.mark.parametrize("top", [[], "x", None])
def test_top_not_object(ah, top):
    assert ah.rules(_reject(ah, top)["hits"]) == ["top_not_object"]


def test_missing_netlist_single_hit(ah):
    d = ah.base()
    del d["netlist"]
    detail = _reject(ah, d)
    assert detail["where"] == "netlist"
    assert ah.rules(detail["hits"]) == ["missing_key"]


@pytest.mark.parametrize("val", [{}, "Mfx1", None, 3])
def test_netlist_type_single_hit(ah, val):
    d = ah.base()
    d["netlist"] = val
    detail = _reject(ah, d)
    assert detail["where"] == "netlist"
    assert ah.rules(detail["hits"]) == ["netlist_type"]


def test_element_type_each(ah):
    d = ah.base()
    d["netlist"] += ["Q9", 3, None, ["Q8"]]
    assert ah.rules(_reject(ah, d)["hits"]) == ["element_type"] * 4


@pytest.mark.parametrize("key", ["n_fingers", "w", "l", "Name", "terminals"])
def test_element_unknown_key(ah, key):
    d = ah.base()
    ah.dev(d, "Mfx3")[key] = 1
    hits = _reject(ah, d)["hits"]
    assert ah.rules(hits) == ["element_unknown_key"]
    assert "Mfx3" in hits[0].elements


def test_element_underscore_keys_ok(ah):
    d = ah.base()
    ah.dev(d, "Mfx3")["_anything"] = {"x": [1]}
    assert len(device_declaration(d)) == 4


@pytest.mark.parametrize("field", ["name", "kind", "drain", "gate", "source"])
@pytest.mark.parametrize("bad", ["<missing>", "", 3, None, ["n_x"]])
def test_element_field(ah, field, bad):
    d = ah.base()
    e = ah.dev(d, "Mfx4")
    if bad == "<missing>":
        del e[field]
    else:
        e[field] = bad
    assert ah.rules(_reject(ah, d)["hits"]) == ["element_field"]


@pytest.mark.parametrize("bad", ["", 0, None, ["rail_hi"]])
def test_bulk_present_but_bad(ah, bad):
    d = ah.base()
    ah.dev(d, "Mfx2")["bulk"] = bad
    assert ah.rules(_reject(ah, d)["hits"]) == ["element_field"]


def test_duplicate_names_not_checked_here(ah):
    d = ah.base()
    ah.dev(d, "Mfx2")["name"] = "Mfx1"
    assert [x.name for x in device_declaration(d)].count("Mfx1") == 2


def test_all_element_hits_in_doc_order(ah):
    d = ah.base()
    d["netlist"].reverse()  # Mfx4 Mfx3 Mfx2 Mfx1
    ah.dev(d, "Mfx4")["w"] = 1
    ah.dev(d, "Mfx2")["gate"] = ""
    ah.dev(d, "Mfx1")["n_fingers"] = 2
    hits = _reject(ah, d)["hits"]
    assert ah.rules(hits) == ["element_unknown_key", "element_field", "element_unknown_key"]
    assert "Mfx4" in hits[0].elements and "Mfx2" in hits[1].elements and "Mfx1" in hits[2].elements
