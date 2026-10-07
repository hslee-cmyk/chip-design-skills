"""`check_topology_schema(doc) -> tuple[SchemaHit]` -- CONTRACT 3.2 (빈 tuple = 통과), 상수 `SCHEMA_VERSION`·`IGNORED_TAG_KEYS`."""
from __future__ import annotations

import pytest

from gmid_engine.authoring import IGNORED_TAG_KEYS, SCHEMA_VERSION, SchemaHit, check_topology_schema

ACCEPTED = {"schema_version", "topology_name", "netlist", "supply_nets", "ports", "passive_elements",
            "ideal_sources", "linked_topology_files", "source"}
TAGS = {"device_roles", "symmetry", "sizing_roles", "compensation"}


def _rules(hits):
    return [h.rule for h in hits]


def test_constants():
    assert SCHEMA_VERSION == "2.0"
    assert set(IGNORED_TAG_KEYS) == TAGS and len(IGNORED_TAG_KEYS) == 4


def test_base_passes(ah):
    assert check_topology_schema(ah.base()) == ()


def test_minimal_doc_passes():
    """netlist 등 존재는 접근자 소관 -- 스키마는 schema_version·topology_name 만 요구."""
    assert check_topology_schema({"schema_version": "2.0", "topology_name": "fx_min"}) == ()


@pytest.mark.parametrize("top", [[], "x", 3, None, True])
def test_top_not_object_single_hit(top):
    hits = check_topology_schema(top)
    assert _rules(hits) == ["top_not_object"]
    assert all(isinstance(h, SchemaHit) for h in hits)


@pytest.mark.parametrize("key", ["schema_version", "topology_name"])
def test_missing_key(ah, key):
    d = ah.base()
    del d[key]
    assert _rules(check_topology_schema(d)) == ["missing_key"]


@pytest.mark.parametrize("key", ["netlist", "supply_nets", "ports", "passive_elements", "ideal_sources",
                                 "linked_topology_files", "source"])
def test_missing_accessor_keys_not_reported_here(ah, key):
    d = ah.base()
    del d[key]
    assert check_topology_schema(d) == ()


def test_unknown_key_each(ah):
    d = ah.base()
    d["widget_count"] = 1
    d["n_fingers"] = 2
    hits = check_topology_schema(d)
    assert _rules(hits) == ["unknown_key", "unknown_key"]


def test_underscore_keys_and_tags_accepted(ah):
    d = ah.base()
    for t in TAGS:
        d[t] = {"whatever": [1, {"x": None}]}
    d["_anything"] = [1, 2]
    d["_"] = None
    assert check_topology_schema(d) == ()
    for t in TAGS:
        del d[t]
    assert check_topology_schema(d) == ()


@pytest.mark.parametrize("val", ["1.0", "2", 2.0, None, ""])
def test_schema_version(ah, val):
    d = ah.base()
    d["schema_version"] = val
    assert _rules(check_topology_schema(d)) == ["schema_version"]


@pytest.mark.parametrize("val", ["", 3, None, ["fx"], {"a": 1}])
def test_topology_name(ah, val):
    d = ah.base()
    d["topology_name"] = val
    assert _rules(check_topology_schema(d)) == ["topology_name"]


@pytest.mark.parametrize("val", [5, [], {"a": "b"}, True])
def test_source_type(ah, val):
    d = ah.base()
    d["source"] = val
    assert _rules(check_topology_schema(d)) == ["source_type"]


@pytest.mark.parametrize("val", [None, "", "text"])
def test_source_string_or_null_ok(ah, val):
    d = ah.base()
    d["source"] = val
    assert check_topology_schema(d) == ()


def test_all_schema_hits_collected(ah):
    d = ah.base()
    d["schema_version"] = "9"
    d["topology_name"] = ""
    d["source"] = 1
    d["zzz"] = 0
    assert sorted(_rules(check_topology_schema(d))) == sorted(["schema_version", "topology_name", "source_type", "unknown_key"])


def test_accepted_key_set_exact(ah):
    """받는 키 전부 + 태그 4개가 있는 문서는 통과하고, 그 밖 이름(대소문자 변형 포함)은 unknown_key."""
    d = {k: None for k in ACCEPTED | TAGS}
    d["schema_version"] = "2.0"
    d["topology_name"] = "fx_all_keys"
    assert check_topology_schema(d) == ()
    d = ah.base()
    d["Netlist"] = []
    assert _rules(check_topology_schema(d)) == ["unknown_key"]
