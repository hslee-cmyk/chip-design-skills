"""`check_name_uniqueness(devices, passives, sources)` -- CONTRACT 3.8 (IC3, 이상원 포함). 반환은 SchemaHit tuple."""
from __future__ import annotations

from gmid_engine.authoring import DeviceDecl, PassiveDecl, SourceDecl, check_name_uniqueness


def D(name):
    return DeviceDecl(name, "nmos", "n_a", "n_b", "n_c")


def P(name):
    return PassiveDecl(name, "capacitor", ("n_a", "n_b"))


def S(name):
    return SourceDecl(name, "current_source", ("n_a", "n_c"))


def _hits(devs, pas, srcs):
    return check_name_uniqueness(tuple(devs), tuple(pas), tuple(srcs))


def test_unique_passes():
    assert _hits([D("Q1"), D("Q2")], [P("Ca")], [S("Ib")]) == ()


def test_empty_passes():
    assert _hits([], [], []) == ()


def test_duplicate_in_every_pairing():
    cases = [
        ([D("Q1"), D("Q1")], [], []),
        ([D("Q1")], [P("Q1")], []),
        ([D("Q1")], [], [S("Q1")]),
        ([], [P("Q1"), P("Q1")], []),
        ([], [P("Q1")], [S("Q1")]),
        ([], [], [S("Q1"), S("Q1")]),
    ]
    for devs, pas, srcs in cases:
        hits = _hits(devs, pas, srcs)
        assert [h.rule for h in hits] == ["name_duplicate"], (devs, pas, srcs)
        assert hits[0].elements == ("Q1",)


def test_duplicate_once_per_name():
    hits = _hits([D("Q1"), D("Q1"), D("Q2")], [P("Q1"), P("Q2")], [S("Q1")])
    assert sorted((h.rule, h.elements) for h in hits) == [("name_duplicate", ("Q1",)), ("name_duplicate", ("Q2",))]


def test_case_collision_group():
    hits = _hits([D("Qa")], [P("QA")], [S("qa")])
    assert [h.rule for h in hits] == ["name_case_collision"]
    assert hits[0].elements == ("QA", "Qa", "qa")


def test_case_collision_one_per_group():
    hits = _hits([D("Qa"), D("Rb")], [P("qa"), P("RB")], [])
    assert sorted((h.rule, h.elements) for h in hits) == [
        ("name_case_collision", ("Qa", "qa")), ("name_case_collision", ("RB", "Rb"))]


def test_casefold_not_lower():
    """casefold 기준: 'ß' 와 'ss' 는 casefold 가 같다."""
    hits = _hits([D("Qß")], [P("Qss")], [])
    assert [h.rule for h in hits] == ["name_case_collision"]
    assert hits[0].elements == tuple(sorted(("Qß", "Qss")))


def test_exact_duplicate_is_not_case_collision():
    hits = _hits([D("Q1"), D("Q1")], [], [])
    assert [h.rule for h in hits] == ["name_duplicate"]


def test_fixture_load(ah):
    from gmid_engine.authoring import load_topology
    exc, detail = ah.rejected(load_topology, str(ah.path("name_uniqueness__name_duplicate")))
    assert [(h.rule, h.elements) for h in detail["hits"]] == [("name_duplicate", ("Q4",))]
    exc, detail = ah.rejected(load_topology, str(ah.path("name_uniqueness__name_case_collision")))
    assert [(h.rule, h.elements) for h in detail["hits"]] == [("name_case_collision", ("Rf", "rf"))]
