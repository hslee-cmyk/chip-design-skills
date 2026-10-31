"""`TopologyDoc` 와 선언 레코드 -- CONTRACT 2절(frozen·require_immutable·fp_of·from_declarations·connectivity_fp 불변식)."""
from __future__ import annotations

import dataclasses
import hashlib
import random

import pytest

from gmid_engine.authoring import (
    DcEdge,
    DeviceDecl,
    PassiveDecl,
    PortDecl,
    RailDeclaration,
    SourceDecl,
    TopologyDoc,
    load_topology,
)
from gmid_engine.core import fp_of, require_immutable

TAGS = ("device_roles", "symmetry", "sizing_roles", "compensation")


def _load(ah, tmp_path, doc, name="doc"):
    return load_topology(ah.write(tmp_path, doc, name))


@pytest.fixture
def base_doc(ah):
    return load_topology(str(ah.path("base_valid")))


# ---------- 불변성 ----------

def test_topology_doc_immutable_and_fingerprintable(base_doc):
    require_immutable(base_doc)
    assert fp_of(base_doc) == fp_of(base_doc)
    with pytest.raises(dataclasses.FrozenInstanceError):
        base_doc.name = "other"
    with pytest.raises(dataclasses.FrozenInstanceError):
        base_doc.connectivity_fp = "0" * 64


def test_field_types(base_doc):
    assert isinstance(base_doc.devices, tuple) and isinstance(base_doc.passives, tuple)
    assert isinstance(base_doc.sources, tuple) and isinstance(base_doc.ports, tuple)
    assert isinstance(base_doc.rails, frozenset)
    for x in base_doc.devices + base_doc.passives + base_doc.sources + base_doc.ports:
        require_immutable(x)
        attr = "net" if isinstance(x, PortDecl) else "name"
        with pytest.raises(dataclasses.FrozenInstanceError):
            setattr(x, attr, "zz")


@pytest.mark.parametrize("field,make", [
    ("devices", list), ("passives", list), ("sources", list), ("ports", list), ("rails", set),
])
def test_mutable_value_into_constructor_is_type_error(base_doc, field, make):
    with pytest.raises(TypeError):
        dataclasses.replace(base_doc, **{field: make(getattr(base_doc, field))})


def test_record_shapes():
    d = DeviceDecl("Qx", "nmos", "n_d", "n_g", "n_s")
    assert (d.name, d.kind, d.d, d.g, d.s, d.bulk) == ("Qx", "nmos", "n_d", "n_g", "n_s", None)
    p = PassiveDecl("Cx", "capacitor", ("n_a", "n_b"))
    assert (p.value_key, p.value) == (None, None)
    s = SourceDecl("Ix", "current_source", ("n_a", "n_b"), "value_amp", 1e-6)
    assert (s.terminals, s.value_key, s.value) == (("n_a", "n_b"), "value_amp", 1e-6)
    port = PortDecl("n_a", "input", "aux")
    assert (port.net, port.direction, port.role) == ("n_a", "input", "aux")
    assert RailDeclaration(frozenset({"r1"})).nets == frozenset({"r1"})
    e = DcEdge("Rx", "resistor", ("n_a", "n_b"))
    assert (e.element, e.element_kind, e.nets) == ("Rx", "resistor", ("n_a", "n_b"))


# ---------- from_declarations ----------

def test_from_declarations_sorts_and_matches_load(base_doc):
    rebuilt = TopologyDoc.from_declarations(
        base_doc.name, tuple(reversed(base_doc.devices)), tuple(reversed(base_doc.passives)),
        tuple(reversed(base_doc.sources)), base_doc.rails, tuple(reversed(base_doc.ports)), base_doc.file_sha256)
    assert rebuilt == base_doc
    assert [d.name for d in rebuilt.devices] == sorted(d.name for d in base_doc.devices)
    assert [p.net for p in rebuilt.ports] == sorted(p.net for p in base_doc.ports)


def test_file_sha256_not_in_fp(base_doc):
    other = TopologyDoc.from_declarations(base_doc.name, base_doc.devices, base_doc.passives, base_doc.sources,
                                          base_doc.rails, base_doc.ports, "f" * 64)
    assert other.connectivity_fp == base_doc.connectivity_fp
    assert other.file_sha256 != base_doc.file_sha256


def test_connectivity_fp_is_64_hex(base_doc):
    assert len(base_doc.connectivity_fp) == 64
    int(base_doc.connectivity_fp, 16)


# ---------- connectivity_fp 불변식 (파일 수준 변형) ----------

def _shuffle_everything(doc, seed):
    rnd = random.Random(seed)
    rnd.shuffle(doc["netlist"])
    rnd.shuffle(doc["passive_elements"])
    rnd.shuffle(doc["ideal_sources"])
    rnd.shuffle(doc["supply_nets"])
    items = list(doc["ports"].items())
    rnd.shuffle(items)
    doc["ports"] = dict(items)
    keys = list(doc.items())
    rnd.shuffle(keys)
    return dict(keys)


def test_fp_invariant_under_tags_comments_and_order(ah, tmp_path, base_doc):
    d = ah.base()
    for t in TAGS:
        del d[t]
    d["_note"] = "changed note"
    d["_extra_comment"] = {"anything": 1}
    ah.dev(d, "Mfx1")["_comment"] = "changed"
    ah.pas(d, "Rf")["_why"] = "added"
    d["ports"]["_comment"] = "changed"
    d = _shuffle_everything(d, 7)
    got = _load(ah, tmp_path, d)
    assert got.connectivity_fp == base_doc.connectivity_fp
    assert got.file_sha256 != base_doc.file_sha256
    assert got == dataclasses.replace(base_doc, file_sha256=got.file_sha256)


@pytest.mark.parametrize("seed", [1, 2, 3])
def test_fp_invariant_under_order_only(ah, tmp_path, base_doc, seed):
    got = _load(ah, tmp_path, _shuffle_everything(ah.base(), seed))
    assert got.connectivity_fp == base_doc.connectivity_fp


def test_fp_invariant_under_tag_value_change(ah, tmp_path, base_doc):
    d = ah.base()
    d["device_roles"] = {"Mfx1": "input_pair"}
    d["symmetry"] = None
    d["sizing_roles"] = {"x": 1}
    d["compensation"] = "miller"
    assert _load(ah, tmp_path, d).connectivity_fp == base_doc.connectivity_fp


def _m_net(ah, d):
    ah.dev(d, "Mfx4")["drain"] = "n_mid"


def _m_gate(ah, d):
    ah.dev(d, "Mfx2")["gate"] = "n_inp"


def _m_kind(ah, d):
    ah.dev(d, "Mfx1")["kind"] = "pmos"


def _m_bulk(ah, d):
    ah.dev(d, "Mfx2")["bulk"] = "rail_lo"


def _m_role(ah, d):
    d["ports"]["n_inp"]["role"] = "aux_input"


def _m_dir(ah, d):
    d["ports"]["n_mid"] = {"direction": "output", "role": "aux"}


def _m_rails(ah, d):
    d["supply_nets"].append("n_bias")


def _m_value(ah, d):
    ah.pas(d, "Rf")["value_ohm"] = 2000.0


def _m_value_key(ah, d):
    del ah.pas(d, "Cload")["value_farad"]


def _m_pkind(ah, d):
    ah.pas(d, "Cf")["kind"] = "inductor"


def _m_terms(ah, d):
    ah.pas(d, "Cf")["terminals"] = ["n_mid", "n_rzn"]


def _m_src_value(ah, d):
    d["ideal_sources"][0]["value_amp"] = 2e-05


def _m_name(ah, d):
    ah.dev(d, "Mfx4")["name"] = "Mfx5"


def _m_topology_name(ah, d):
    d["topology_name"] = "fx_other_amp"


CHANGES = [_m_net, _m_gate, _m_kind, _m_bulk, _m_role, _m_dir, _m_rails, _m_value, _m_value_key, _m_pkind,
           _m_terms, _m_src_value, _m_name]


@pytest.mark.parametrize("change", CHANGES, ids=[c.__name__ for c in CHANGES])
def test_fp_changes_with_one_connectivity_change(ah, tmp_path, base_doc, change):
    d = ah.base()
    change(ah, d)
    got = _load(ah, tmp_path, d)
    assert got.connectivity_fp != base_doc.connectivity_fp


def test_topology_name_kept_in_name(ah, tmp_path):
    d = ah.base()
    _m_topology_name(ah, d)
    assert _load(ah, tmp_path, d).name == "fx_other_amp"


def test_unread_passive_and_source_keys_not_in_fp(ah, tmp_path, base_doc):
    """3.6·3.7: value_from_spec·nulling_reference_device·implementable 은 읽지 않는다(투영에 없음)."""
    d = ah.base()
    ah.pas(d, "Cf")["value_from_spec"] = "Other_spec"
    ah.pas(d, "Rf")["nulling_reference_device"] = "Mfx3"
    d["ideal_sources"][0]["implementable"] = True
    assert _load(ah, tmp_path, d).connectivity_fp == base_doc.connectivity_fp


def test_file_sha256_is_bytes_hash(ah, base_doc):
    assert base_doc.file_sha256 == hashlib.sha256(ah.path("base_valid").read_bytes()).hexdigest()
