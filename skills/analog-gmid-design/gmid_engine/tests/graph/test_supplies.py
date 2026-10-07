"""graph/supplies.py -- `supplies_declaration(supplies_v, rails)` (계약 2절) + build_s1 경유 거부(1절 '실패').

기대 hit 목록은 계약 2절 표·순서 문장에서 손으로 만든다.
"""
from __future__ import annotations

import math
from types import MappingProxyType

import pytest

from gmid_engine.authoring import SchemaHit
from gmid_engine.core import SchemaRejectedError, exit_code_for
from gmid_engine.graph import build_s1, supplies_declaration

RAILS3 = frozenset({"vdd", "vss", "agnd"})
RAILS2 = frozenset({"vdd", "gnd"})


def _reject(sv, rails):
    with pytest.raises(SchemaRejectedError) as ei:
        supplies_declaration(sv, rails)
    exc = ei.value
    assert exit_code_for(exc) == 7
    detail = dict(exc.record.detail)
    assert detail["gate"] == "supplies_v"
    assert detail["where"] == "supplies_v"
    hits = detail["hits"]
    assert isinstance(hits, tuple) and hits
    assert all(isinstance(h, SchemaHit) for h in hits)
    return [(h.rule, h.where, h.elements) for h in hits]


def test_none_passes_through():
    assert supplies_declaration(None, RAILS2) is None


def test_normalized_sorted_float_tuple():
    out = supplies_declaration({"vss": 0, "vdd": 1.8, "agnd": 0.9}, RAILS3)
    assert out == (("agnd", 0.9), ("vdd", 1.8), ("vss", 0.0))
    assert isinstance(out, tuple)
    assert all(type(v) is float for _, v in out)        # int -> float


def test_insertion_order_irrelevant_and_mapping_types_accepted():
    a = supplies_declaration({"gnd": 0.0, "vdd": 1.8}, RAILS2)
    b = supplies_declaration({"vdd": 1.8, "gnd": 0.0}, RAILS2)
    c = supplies_declaration(MappingProxyType({"vdd": 1.8, "gnd": 0}), RAILS2)
    assert a == b == c == (("gnd", 0.0), ("vdd", 1.8))


def test_negative_potentials_are_fine():
    assert supplies_declaration({"vdd": 0.9, "gnd": -0.9}, RAILS2) == (("gnd", -0.9), ("vdd", 0.9))


@pytest.mark.parametrize("sv", [[("vdd", 1.8), ("gnd", 0.0)], (("vdd", 1.8),), "vdd=1.8", 1.8, frozenset({"vdd"})])
def test_not_mapping_is_single_type_hit(sv):
    assert _reject(sv, RAILS2) == [("supplies_type", "supplies_v", ())]


def test_unknown_net_including_underscore_key():
    hits = _reject({"vdd": 1.8, "gnd": 0.0, "_comment": "note", "vddx": 3.3}, RAILS2)
    assert hits == [
        ("supplies_unknown_net", "supplies_v._comment", ("_comment",)),
        ("supplies_unknown_net", "supplies_v.vddx", ("vddx",)),
    ]


def test_non_string_key_is_unknown_net():
    hits = _reject({"vdd": 1.8, "gnd": 0.0, 7: 1.0}, RAILS2)
    assert [h[0] for h in hits] == ["supplies_unknown_net"]


@pytest.mark.parametrize("bad", [True, False, "1.8", None, float("nan"), float("inf"), -math.inf, (1.8,), 1 + 0j])
def test_bad_value(bad):
    hits = _reject({"vdd": bad, "gnd": 0.0}, RAILS2)
    assert hits == [("supplies_value", "supplies_v.vdd", ("vdd",))]


def test_missing_rails_in_rail_name_order():
    hits = _reject({"vdd": 1.8}, RAILS3)
    assert hits == [
        ("supplies_missing_rail", "supplies_v.agnd", ("agnd",)),
        ("supplies_missing_rail", "supplies_v.vss", ("vss",)),
    ]


def test_empty_mapping_misses_every_rail():
    hits = _reject({}, RAILS3)
    assert [h[1] for h in hits] == ["supplies_v.agnd", "supplies_v.vdd", "supplies_v.vss"]
    assert {h[0] for h in hits} == {"supplies_missing_rail"}


def test_all_violations_collected_in_contract_order():
    # 입력 넷 이름순(unknown_net·value 섞여서) -> 그 뒤 레일 이름순 missing_rail. 개수로 자르지 않는다.
    sv = {"zz": 1.0, "vdd": float("nan"), "aa": 2.0, "_c": "x", "agnd": True}
    hits = _reject(sv, RAILS3)
    assert hits == [
        ("supplies_unknown_net", "supplies_v._c", ("_c",)),
        ("supplies_unknown_net", "supplies_v.aa", ("aa",)),
        ("supplies_value", "supplies_v.agnd", ("agnd",)),
        ("supplies_value", "supplies_v.vdd", ("vdd",)),
        ("supplies_unknown_net", "supplies_v.zz", ("zz",)),
        ("supplies_missing_rail", "supplies_v.vss", ("vss",)),
    ]


def test_many_hits_not_truncated():
    sv = {"n%02d" % i: 1.0 for i in range(40)}
    hits = _reject(sv, RAILS2)
    assert len(hits) == 40 + 2
    assert [h[0] for h in hits[:40]] == ["supplies_unknown_net"] * 40
    assert [h[1] for h in hits[40:]] == ["supplies_v.gnd", "supplies_v.vdd"]


def test_build_s1_rejects_bad_supplies(gh):
    doc = gh.load_lib("common_gate_amplifier")
    for sv, rule in ((["vdd"], "supplies_type"), ({"vdd": 1.8}, "supplies_missing_rail"),
                     ({"vdd": 1.8, "gnd": 0.0, "vss": 0.0}, "supplies_unknown_net"),
                     ({"vdd": float("inf"), "gnd": 0.0}, "supplies_value")):
        with pytest.raises(SchemaRejectedError) as ei:
            build_s1(doc, sv)
        d = dict(ei.value.record.detail)
        assert d["gate"] == "supplies_v"
        assert [h.rule for h in d["hits"]] == [rule]


def test_library_supplies_are_accepted(gh):
    # 계약 7절 출처의 supplies_v 는 각 회로 레일 선언과 맞아 거부되지 않는다(test 쪽 집계로 기대값)
    for name in gh.SIX:
        sv = gh.supplies_for(name)
        doc = gh.load_lib(name)
        if sv is None:
            assert supplies_declaration(sv, doc.rails) is None
            continue
        assert set(sv) == set(gh.raw(name)["supply_nets"])
        assert supplies_declaration(sv, doc.rails) == tuple(sorted((k, float(v)) for k, v in sv.items()))
