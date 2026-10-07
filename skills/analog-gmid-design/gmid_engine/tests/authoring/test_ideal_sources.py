"""`source_declaration(doc) -> tuple[SourceDecl]` -- CONTRACT 3.7 (gate `ideal_sources`, where `ideal_sources`).
원소 공통 규칙은 test__two_terminal.py."""
from __future__ import annotations

import pytest

from gmid_engine.authoring import SourceDecl, source_declaration

VALUE_FIELDS = ("value_amp", "value_volt")


def _reject(ah, doc):
    exc, detail = ah.rejected(source_declaration, doc)
    assert detail["gate"] == "ideal_sources"
    return detail


def test_base_decls_match_json(ah):
    raw = ah.base()
    got = source_declaration(raw)
    assert all(isinstance(s, SourceDecl) for s in got)
    exp = set()
    for e in raw["ideal_sources"]:
        vk = next((k for k in VALUE_FIELDS if k in e), None)
        exp.add((e["name"], e["kind"], tuple(e["terminals"]), vk, e.get(vk) if vk else None))
    assert {(s.name, s.kind, s.terminals, s.value_key, s.value) for s in got} == exp


def test_missing_key_gives_empty(ah):
    d = ah.base()
    del d["ideal_sources"]
    assert source_declaration(d) == ()


@pytest.mark.parametrize("top", [[], "x", None])
def test_top_not_object(ah, top):
    assert ah.rules(_reject(ah, top)["hits"]) == ["top_not_object"]


@pytest.mark.parametrize("val", [{}, "Ib", None, 2])
def test_type(ah, val):
    d = ah.base()
    d["ideal_sources"] = val
    detail = _reject(ah, d)
    assert detail["where"] == "ideal_sources"
    assert ah.rules(detail["hits"]) == ["ideal_sources_type"]


def test_voltage_source_and_implementable(ah):
    d = ah.base()
    d["ideal_sources"].append({"name": "Vref", "kind": "voltage_source", "terminals": ["n_bias", "rail_lo"],
                               "value_volt": 0.6, "implementable": True})
    got = {s.name: s for s in source_declaration(d)}
    assert got["Vref"].kind == "voltage_source"
    assert (got["Vref"].value_key, got["Vref"].value) == ("value_volt", 0.6)


@pytest.mark.parametrize("key", ["value_ohm", "value_farad", "value_from_spec", "nulling_reference_device"])
def test_passive_only_keys_unknown(ah, key):
    d = ah.base()
    d["ideal_sources"][0][key] = 1
    hits = _reject(ah, d)["hits"]
    assert ah.rules(hits) == ["element_unknown_key"]
    assert "Ib" in hits[0].elements
