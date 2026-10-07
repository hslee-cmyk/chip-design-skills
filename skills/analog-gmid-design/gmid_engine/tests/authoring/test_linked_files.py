"""`check_linked_files(doc)` -- CONTRACT 3.3 (DEC-76 안전망). 반환은 SchemaHit tuple(빈 tuple = 통과)로 읽었다
(0절 gate 목록에 이 함수가 없고, 1절이 '접근자 예외'만 잡는다고 적음)."""
from __future__ import annotations

import pytest

from gmid_engine.authoring import check_linked_files, load_topology


def test_absent_and_empty_pass(ah):
    d = ah.base()
    assert check_linked_files(d) == ()
    del d["linked_topology_files"]
    assert check_linked_files(d) == ()


@pytest.mark.parametrize("val", ["fx_other.topology.json", {"a": 1}, 3, None])
def test_not_list(ah, val):
    d = ah.base()
    d["linked_topology_files"] = val
    assert [h.rule for h in check_linked_files(d)] == ["linked_files_type"]


@pytest.mark.parametrize("val", [["fx_other.topology.json"], ["a.json", "b.json"], [""]])
def test_any_element_unsupported(ah, val):
    d = ah.base()
    d["linked_topology_files"] = val
    rules = [h.rule for h in check_linked_files(d)]
    assert rules and set(rules) == {"linked_files_unsupported"}


def test_load_rejects_instead_of_reading_entry_only(ah, tmp_path):
    """DEC-76: 진입 파일만 읽고 넘어가지 않는다 -- 연결 파일이 실제로 있어도 거부."""
    other = ah.base()
    other["topology_name"] = "fx_other"
    ah.write(tmp_path, other, "fx_other")
    d = ah.base()
    d["linked_topology_files"] = ["fx_other.topology.json"]
    exc, detail = ah.rejected(load_topology, ah.write(tmp_path, d))
    assert "linked_files_unsupported" in [h.rule for h in detail["hits"]]
