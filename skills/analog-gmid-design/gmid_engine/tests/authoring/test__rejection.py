"""공용 helper `_rejection.py`(reject·require_object) -- CONTRACT 0절 실패 형식이 모든 거부에 공통인지.
비공개라 공개 접근자 전부(json_read·devices·rails·passives·ideal_sources·ports·topology_load)에서 같은 형식을 확인한다."""
from __future__ import annotations

import pytest

from gmid_engine.authoring import (
    SchemaHit,
    device_declaration,
    load_json_checked,
    load_topology,
    passive_declaration,
    port_declaration,
    rail_declaration,
    source_declaration,
)
from gmid_engine.core import SchemaRejectedError, exit_code_for, fp_of, require_immutable

ACCESSORS = [
    ("devices", "netlist", lambda doc: device_declaration(doc)),
    ("rails", "supply_nets", lambda doc: rail_declaration(doc)),
    ("passives", "passive_elements", lambda doc: passive_declaration(doc)),
    ("ideal_sources", "ideal_sources", lambda doc: source_declaration(doc)),
    ("ports", "ports", lambda doc: port_declaration(doc, None, None)),
]


@pytest.mark.parametrize("acc", ACCESSORS, ids=[a[0] for a in ACCESSORS])
def test_accessor_failure_shape(ah, acc):
    gate, key, call = acc
    d = ah.base()
    d[key] = 12345  # 모든 접근자에서 '형식 아님'
    exc, detail = ah.rejected(call, d)
    assert type(exc) is SchemaRejectedError
    assert exc.record.failure_class == SchemaRejectedError.failure_class
    assert detail["gate"] == gate
    assert detail["where"] == key
    assert all(isinstance(h, SchemaHit) for h in detail["hits"])
    assert "rejected_gates" not in detail and "not_evaluated" not in detail
    require_immutable(exc.record)
    fp_of(exc.record)


@pytest.mark.parametrize("acc", ACCESSORS, ids=[a[0] for a in ACCESSORS])
def test_accessor_require_object(ah, acc):
    gate, key, call = acc
    exc, detail = ah.rejected(call, ["not", "an", "object"])
    assert detail["gate"] == gate
    assert [h.rule for h in detail["hits"]] == ["top_not_object"]


def test_json_read_failure_shape(ah, tmp_path):
    p = tmp_path / "x.json"
    p.write_bytes(b"{")
    exc, detail = ah.rejected(load_json_checked, str(p), "where-label")
    assert detail["gate"] == "json_read"
    assert detail["where"] == "where-label"
    assert exit_code_for(exc) == 7


def test_topology_load_failure_shape(ah):
    path = str(ah.path("multi__contract_example"))
    exc, detail = ah.rejected(load_topology, path)
    assert detail["gate"] == "topology_load"
    assert set(detail) >= {"gate", "where", "hits", "rejected_gates", "not_evaluated"}
    require_immutable(exc.record)


def test_schema_hit_frozen_dataclass():
    h = SchemaHit("missing_key", "netlist", "msg")
    assert h.elements == ()
    with pytest.raises(AttributeError):
        h.rule = "x"
    require_immutable(SchemaHit("r", "w", "m", ("a", "b")))
