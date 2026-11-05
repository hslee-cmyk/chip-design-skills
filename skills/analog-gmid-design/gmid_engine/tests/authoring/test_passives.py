"""`passive_declaration(doc) -> tuple[PassiveDecl]` -- CONTRACT 3.6 (gate `passives`, where `passive_elements`).

`missing_key`(키 없음 거부)는 **CI-12 기본안(사용자 결정 대기)** 을 확인하는 test 다 -- 결정이 바뀌면 이 test 를 고친다.
원소 공통 규칙은 test__two_terminal.py 가 수동·이상원 양쪽에 건다.
"""
from __future__ import annotations

import pytest

from gmid_engine.authoring import PassiveDecl, TWO_TERMINAL_NAMES, passive_declaration

VALUE_FIELDS = ("value_ohm", "value_farad")


def _reject(ah, doc):
    exc, detail = ah.rejected(passive_declaration, doc)
    assert detail["gate"] == "passives"
    return detail


def test_base_decls_match_json(ah):
    raw = ah.base()
    got = passive_declaration(raw)
    assert all(isinstance(p, PassiveDecl) for p in got)
    exp = set()
    for e in raw["passive_elements"]:
        vk = next((k for k in VALUE_FIELDS if k in e), None)
        exp.add((e["name"], e["kind"], tuple(e["terminals"]), vk, e.get(vk) if vk else None))
    assert {(p.name, p.kind, p.terminals, p.value_key, p.value) for p in got} == exp


def test_terminals_keep_document_order(ah):
    d = ah.base()
    ah.pas(d, "Rf")["terminals"] = ["n_rzn", "n_outp"]
    got = {p.name: p for p in passive_declaration(d)}
    assert got["Rf"].terminals == ("n_rzn", "n_outp")
    assert len(got["Rf"].terminals) == len(TWO_TERMINAL_NAMES)


def test_missing_key_ci12_default_rejects(ah):
    """CI-12 기본안: passive_elements 키 없음을 [] 로 읽지 않고 missing_key 로 거부."""
    d = ah.base()
    del d["passive_elements"]
    detail = _reject(ah, d)
    assert detail["where"] == "passive_elements"
    assert ah.rules(detail["hits"]) == ["missing_key"]


def test_empty_list_accepted(ah):
    d = ah.base()
    d["passive_elements"] = []
    assert passive_declaration(d) == ()


@pytest.mark.parametrize("top", [[], "x", None])
def test_top_not_object(ah, top):
    assert ah.rules(_reject(ah, top)["hits"]) == ["top_not_object"]


@pytest.mark.parametrize("val", [{}, "Rf", None, 1])
def test_type(ah, val):
    d = ah.base()
    d["passive_elements"] = val
    assert ah.rules(_reject(ah, d)["hits"]) == ["passive_elements_type"]


def test_allowed_unread_keys_and_any_kind(ah):
    d = ah.base()
    ah.pas(d, "Rf")["nulling_reference_device"] = "Mfx3"
    ah.pas(d, "Cload")["value_from_spec"] = "C_spec"
    ah.pas(d, "Cf")["kind"] = "inductor"
    got = {p.name: p for p in passive_declaration(d)}
    assert got["Cf"].kind == "inductor"


@pytest.mark.parametrize("key", ["value_amp", "implementable", "w", "value"])
def test_unknown_key_includes_source_only_keys(ah, key):
    d = ah.base()
    ah.pas(d, "Cf")[key] = 1
    hits = _reject(ah, d)["hits"]
    assert ah.rules(hits) == ["element_unknown_key"]
    assert "Cf" in hits[0].elements


def test_value_absent_gives_none(ah):
    d = ah.base()
    for f in VALUE_FIELDS:
        ah.pas(d, "Rf").pop(f, None)
    got = {p.name: p for p in passive_declaration(d)}
    assert got["Rf"].value_key is None and got["Rf"].value is None


def test_value_null_is_kept(ah):
    got = {p.name: p for p in passive_declaration(ah.base())}
    assert got["Cload"].value_key == "value_farad" and got["Cload"].value is None
