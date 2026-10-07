"""`rail_declaration(doc) -> RailDeclaration` -- CONTRACT 3.5 (gate `rails`, where `supply_nets`, B26-1 이식)."""
from __future__ import annotations

import pytest

from gmid_engine.authoring import RailDeclaration, rail_declaration
from gmid_engine.core import require_immutable


def _reject(ah, doc):
    exc, detail = ah.rejected(rail_declaration, doc)
    assert detail["gate"] == "rails"
    return detail


def test_base(ah):
    raw = ah.base()
    got = rail_declaration(raw)
    assert isinstance(got, RailDeclaration)
    assert got.nets == frozenset(raw["supply_nets"])
    assert isinstance(got.nets, frozenset)
    require_immutable(got)


def test_empty_list_accepted(ah):
    d = ah.base()
    d["supply_nets"] = []
    assert rail_declaration(d).nets == frozenset()


def test_names_do_not_decide_rails(ah):
    """넷 이름으로 레일을 정하지 않는다 -- 'vdd'·'gnd' 같은 이름이 없어도, 아무 이름이어도 선언 그대로."""
    d = ah.base()
    d["supply_nets"] = ["zz_top", "Q"]
    assert rail_declaration(d).nets == frozenset({"zz_top", "Q"})


@pytest.mark.parametrize("top", [[], "x", None])
def test_top_not_object(ah, top):
    assert ah.rules(_reject(ah, top)["hits"]) == ["top_not_object"]


def test_missing_key(ah):
    d = ah.base()
    del d["supply_nets"]
    detail = _reject(ah, d)
    assert detail["where"] == "supply_nets"
    assert ah.rules(detail["hits"]) == ["missing_key"]


@pytest.mark.parametrize("val", ["rail_hi", {"rail_hi": 1}, None, 3])
def test_type(ah, val):
    d = ah.base()
    d["supply_nets"] = val
    assert ah.rules(_reject(ah, d)["hits"]) == ["supply_nets_type"]


def test_value_each_element(ah):
    d = ah.base()
    d["supply_nets"] = ["rail_hi", "", 3, None, ["rail_lo"], "rail_lo"]
    assert ah.rules(_reject(ah, d)["hits"]) == ["supply_net_value"] * 4


def test_duplicate_once_per_net(ah):
    d = ah.base()
    d["supply_nets"] = ["rail_hi", "rail_lo", "rail_hi", "rail_hi", "rail_lo", "rail_ac"]
    hits = _reject(ah, d)["hits"]
    assert ah.rules(hits) == ["supply_net_duplicate"] * 2
    assert {"rail_hi", "rail_lo"} == {n for h in hits for n in h.elements} & {"rail_hi", "rail_lo"}
    assert "rail_hi" in hits[0].elements and "rail_lo" in hits[1].elements
