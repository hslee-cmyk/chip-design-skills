"""`check_hidden_rails(rails, devices, passives, sources)` -- CONTRACT 3.11 (DEC-60 (iii) + 선언 넷 존재, 공격 14 (b)).
반환은 SchemaHit tuple(빈 tuple = 통과)."""
from __future__ import annotations

from gmid_engine.authoring import (
    DeviceDecl,
    PassiveDecl,
    RailDeclaration,
    SourceDecl,
    check_hidden_rails,
    device_declaration,
    passive_declaration,
    rail_declaration,
    source_declaration,
)


def _run(raw):
    return check_hidden_rails(rail_declaration(raw), device_declaration(raw), passive_declaration(raw),
                              source_declaration(raw))


def R(*nets):
    return RailDeclaration(frozenset(nets))


def test_base_passes_resistor_connected_net(ah):
    """n_rzn 은 2단자 원소(Rf·Cf)에만 있지만 Rf -> Mfx3 로 rail_lo 에 DC 로 닿는다 -- 오거부 0."""
    assert _run(ah.base()) == ()


def test_attack_14b_drop_declared_rail(ah):
    d = ah.base()
    d["supply_nets"].remove("rail_ac")
    hits = _run(d)
    assert [(h.rule, h.elements) for h in hits] == [("hidden_rail", ("Cload", "rail_ac"))]


def test_rail_not_connected(ah):
    d = ah.base()
    d["supply_nets"].append("rail_mid")
    hits = _run(d)
    assert [h.rule for h in hits] == ["rail_not_connected"]
    assert "rail_mid" in hits[0].elements


def test_rail_on_bulk_only_is_connected():
    devs = (DeviceDecl("Mfx1", "nmos", "n_d", "n_g", "rail_lo", "rail_sub"),)
    assert check_hidden_rails(R("rail_lo", "rail_sub"), devs, (), ()) == ()


def test_rail_on_gate_only_is_connected():
    devs = (DeviceDecl("Mfx1", "nmos", "n_d", "rail_g", "rail_lo"),)
    assert check_hidden_rails(R("rail_lo", "rail_g"), devs, (), ()) == ()


def test_rail_on_source_terminal_only_is_connected():
    devs = (DeviceDecl("Mfx1", "nmos", "n_d", "n_g", "rail_lo"),)
    srcs = (SourceDecl("Ix", "current_source", ("rail_x", "n_d")),)
    assert check_hidden_rails(R("rail_lo", "rail_x"), devs, (), srcs) == ()


def test_capacitor_chain_hidden_both_nets():
    """C1(n_out-n_a) R1(n_a-n_b) C2(n_b-rail_lo): n_a·n_b 는 2단자 전용, 엣지 R1 은 둘끼리만 이어 레일에 안 닿는다."""
    devs = (DeviceDecl("Mfx1", "nmos", "n_out", "n_g", "rail_lo"),)
    pas = (PassiveDecl("C1", "capacitor", ("n_out", "n_a")), PassiveDecl("R1", "resistor", ("n_a", "n_b")),
           PassiveDecl("C2", "capacitor", ("n_b", "rail_lo")))
    hits = check_hidden_rails(R("rail_lo"), devs, pas, ())
    assert sorted((h.rule, h.elements) for h in hits) == [
        ("hidden_rail", ("C1", "R1", "n_a")), ("hidden_rail", ("C2", "R1", "n_b"))]


def test_resistor_to_mos_net_reaches_rail_through_mos_ds():
    devs = (DeviceDecl("Mfx1", "nmos", "n_out", "n_g", "rail_lo"),)
    pas = (PassiveDecl("C1", "capacitor", ("n_x", "n_g")), PassiveDecl("R1", "resistor", ("n_x", "n_out")))
    assert check_hidden_rails(R("rail_lo"), devs, pas, ()) == ()


def test_reach_through_ideal_source():
    devs = (DeviceDecl("Mfx1", "nmos", "n_out", "n_g", "rail_lo"),)
    pas = (PassiveDecl("C1", "capacitor", ("n_x", "n_out")),)
    srcs = (SourceDecl("Vx", "voltage_source", ("n_x", "rail_lo")),)
    assert check_hidden_rails(R("rail_lo"), devs, pas, srcs) == ()


def test_gate_does_not_conduct():
    """MOS gate 는 엣지가 아니다: R1 이 gate 전용 넷 n_g 에만 이어지면 n_x 는 레일에 못 닿는다."""
    devs = (DeviceDecl("Mfx1", "nmos", "n_out", "n_g", "rail_lo"),)
    pas = (PassiveDecl("R1", "resistor", ("n_x", "n_g")), PassiveDecl("C1", "capacitor", ("n_x", "n_out")))
    # n_g 는 MOS 단자라 hidden 대상 아님. n_x 는 2단자 전용이고 n_g 를 거쳐도 DC 경로가 레일로 이어지지 않는다.
    hits = check_hidden_rails(R("rail_lo"), devs, pas, ())
    assert [(h.rule, h.elements) for h in hits] == [("hidden_rail", ("C1", "R1", "n_x"))]


def test_inductor_does_not_conduct():
    devs = (DeviceDecl("Mfx1", "nmos", "n_out", "n_g", "rail_lo"),)
    pas = (PassiveDecl("L1", "inductor", ("n_x", "n_out")),)
    hits = check_hidden_rails(R("rail_lo"), devs, pas, ())
    assert [(h.rule, h.elements) for h in hits] == [("hidden_rail", ("L1", "n_x"))]


def test_declared_rail_on_capacitor_only_is_fine():
    devs = (DeviceDecl("Mfx1", "nmos", "n_out", "n_g", "rail_lo"),)
    pas = (PassiveDecl("C1", "capacitor", ("n_out", "rail_ac")),)
    assert check_hidden_rails(R("rail_lo", "rail_ac"), devs, pas, ()) == ()


def test_fixtures_through_load(ah):
    from gmid_engine.authoring import load_topology
    exc, detail = ah.rejected(load_topology, str(ah.path("hidden_rails__hidden_rail")))
    assert [(h.rule, h.elements) for h in detail["hits"]] == [("hidden_rail", ("Cload", "rail_ac"))]
    exc, detail = ah.rejected(load_topology, str(ah.path("hidden_rails__rail_not_connected")))
    assert [h.rule for h in detail["hits"]] == ["rail_not_connected"]
