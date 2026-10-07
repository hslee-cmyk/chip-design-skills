"""`port_declaration(doc, rails, known_nets) -> tuple[PortDecl]` -- CONTRACT 3.9 (gate `ports`, where `ports`), 5절 5."""
from __future__ import annotations

import pytest

from gmid_engine.authoring import PortDecl, RailDeclaration, port_declaration

RAILS = RailDeclaration(frozenset({"rail_hi", "rail_lo", "rail_ac"}))
KNOWN = frozenset({"n_inp", "n_outp", "n_mid", "n_bias", "n_rzn", "rail_hi", "rail_lo", "rail_ac"})


def _ok(doc, rails=RAILS, known=KNOWN):
    return port_declaration(doc, rails, known)


def _reject(ah, doc, rails=RAILS, known=KNOWN):
    exc, detail = ah.rejected(port_declaration, doc, rails, known)
    assert detail["gate"] == "ports"
    return detail


def test_base_matches_json(ah):
    raw = ah.base()
    got = _ok(raw)
    assert all(isinstance(p, PortDecl) for p in got)
    assert [(p.net, p.direction, p.role) for p in got] == sorted(
        (k, v["direction"], v["role"]) for k, v in raw["ports"].items() if not k.startswith("_"))


def test_sorted_by_net(ah):
    d = ah.base()
    d["ports"] = {"n_outp": d["ports"]["n_outp"], "n_mid": {"direction": "input", "role": "aux"},
                  "n_inp": d["ports"]["n_inp"]}
    assert [p.net for p in _ok(d)] == ["n_inp", "n_mid", "n_outp"]


@pytest.mark.parametrize("top", [[], "x", None])
def test_top_not_object(ah, top):
    assert ah.rules(_reject(ah, top)["hits"])[0] == "top_not_object"


def test_missing_key(ah):
    d = ah.base()
    del d["ports"]
    detail = _reject(ah, d)
    assert detail["where"] == "ports"
    assert ah.rules(detail["hits"])[0] == "missing_key"


@pytest.mark.parametrize("val", [["n_inp"], "n_inp", None, 1])
def test_ports_type(ah, val):
    d = ah.base()
    d["ports"] = val
    assert ah.rules(_reject(ah, d)["hits"])[0] == "ports_type"


@pytest.mark.parametrize("entry", ["input", 1, None, ["input", "x"]])
def test_port_entry_type(ah, entry):
    d = ah.base()
    d["ports"]["n_mid"] = entry
    hits = _reject(ah, d)["hits"]
    assert ah.rules(hits) == ["port_entry_type"]
    assert "n_mid" in hits[0].elements


def test_port_unknown_key(ah):
    d = ah.base()
    d["ports"]["n_mid"] = {"direction": "input", "role": "aux", "gain": 2, "_comment": "ok"}
    assert ah.rules(_reject(ah, d)["hits"]) == ["port_unknown_key"]


@pytest.mark.parametrize("val", ["bidir", "Input", "", None, 1, "<missing>"])
def test_port_direction(ah, val):
    d = ah.base()
    e = {"direction": val, "role": "aux"}
    if val == "<missing>":
        del e["direction"]
    d["ports"]["n_mid"] = e
    assert ah.rules(_reject(ah, d)["hits"]) == ["port_direction"]


@pytest.mark.parametrize("val", ["", None, 3, ["a"], "<missing>"])
def test_port_role(ah, val):
    d = ah.base()
    e = {"direction": "output", "role": val}
    if val == "<missing>":
        del e["role"]
    d["ports"]["n_mid"] = e
    assert ah.rules(_reject(ah, d)["hits"]) == ["port_role"]


def test_port_net_unknown_and_skipped_when_none(ah):
    d = ah.base()
    d["ports"]["n_ghost"] = {"direction": "input", "role": "aux"}
    hits = _reject(ah, d)["hits"]
    assert ah.rules(hits) == ["port_net_unknown"]
    assert "n_ghost" in hits[0].elements
    assert "n_ghost" in [p.net for p in port_declaration(d, RAILS, None)]


def test_port_on_rail_and_skipped_when_none(ah):
    d = ah.base()
    d["ports"]["rail_lo"] = {"direction": "output", "role": "aux"}
    hits = _reject(ah, d)["hits"]
    assert ah.rules(hits) == ["port_on_rail"]
    assert "rail_lo" in hits[0].elements
    assert "rail_lo" in [p.net for p in port_declaration(d, None, KNOWN)]


def test_both_net_checks_skipped(ah):
    d = ah.base()
    d["ports"]["n_ghost"] = {"direction": "input", "role": "aux"}
    d["ports"]["rail_lo"] = {"direction": "output", "role": "aux"}
    assert len(port_declaration(d, None, None)) == 4


def test_no_input_port(ah):
    d = ah.base()
    d["ports"]["n_inp"]["direction"] = "output"
    assert ah.rules(_reject(ah, d)["hits"]) == ["no_input_port"]


def test_no_output_port(ah):
    d = ah.base()
    d["ports"]["n_outp"]["direction"] = "input"
    assert ah.rules(_reject(ah, d)["hits"]) == ["no_output_port"]


def test_only_violating_input_counts_as_no_input(ah):
    """'위반 없는' input 이 0개면 no_input_port -- 유일한 input 이 role 위반이면 둘 다 낸다."""
    d = ah.base()
    d["ports"]["n_inp"]["role"] = ""
    rules = ah.rules(_reject(ah, d)["hits"])
    assert "port_role" in rules and "no_input_port" in rules
    d = ah.base()
    d["ports"]["rail_hi"] = {"direction": "input", "role": "aux"}
    d["ports"]["n_inp"]["role"] = 0
    rules = ah.rules(_reject(ah, d)["hits"])
    assert "no_input_port" in rules and "port_on_rail" in rules


def test_empty_ports_object_no_input_no_output(ah):
    d = ah.base()
    d["ports"] = {"_comment": "none"}
    assert sorted(ah.rules(_reject(ah, d)["hits"])) == ["no_input_port", "no_output_port"]


def test_underscore_key_is_not_port(ah):
    got = _ok(ah.base())
    assert all(not p.net.startswith("_") for p in got) and len(got) == 2


def test_all_hits_collected_doc_order(ah):
    d = ah.base()
    d["ports"]["n_mid"] = {"direction": "in", "role": "x"}
    d["ports"]["n_bias"] = {"direction": "input", "role": ""}
    d["ports"]["n_ghost"] = {"direction": "output", "role": "x"}
    hits = _reject(ah, d)["hits"]
    assert ah.rules(hits) == ["port_direction", "port_role", "port_net_unknown"]
