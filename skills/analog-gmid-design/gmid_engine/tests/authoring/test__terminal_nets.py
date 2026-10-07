"""공용 helper `_terminal_nets.py` -- 단자 넷 집합(CONTRACT 5절 2: hidden_rails·topology_load 가 쓴다).
단자 = MOS d/g/s/선언 bulk + 2단자 terminals(3.11 rail_not_connected 행). 비공개라 두 소비자로 확인한다:
`load_topology` 의 port_net_unknown(known_nets = 단자 넷 집합)과 `check_hidden_rails` 의 rail_not_connected."""
from __future__ import annotations

import pytest

from gmid_engine.authoring import DeviceDecl, PassiveDecl, RailDeclaration, SourceDecl, check_hidden_rails, load_topology


def _add_port(doc, net):
    doc["ports"][net] = {"direction": "input", "role": "aux_input"}


@pytest.mark.parametrize("place", ["drain", "gate", "source", "bulk", "passive", "source_elem"])
def test_port_on_each_terminal_kind_is_known(ah, tmp_path, place):
    d = ah.base()
    net = "n_probe"
    if place in ("drain", "gate", "source", "bulk"):
        d["netlist"].append({"name": "Q5", "kind": "nmos", "drain": "n_mid", "gate": "n_inp", "source": "rail_lo"})
        d["netlist"][-1][place] = net
    elif place == "passive":
        d["passive_elements"].append({"name": "Rp", "kind": "resistor", "terminals": [net, "n_mid"]})
    else:
        d["ideal_sources"].append({"name": "Ip", "kind": "current_source", "terminals": [net, "rail_lo"]})
    _add_port(d, net)
    doc = load_topology(ah.write(tmp_path, d))
    assert net in [p.net for p in doc.ports]


def test_port_on_tag_or_comment_only_net_is_unknown(ah, tmp_path):
    """태그·주석에만 적힌 이름은 단자가 아니다."""
    d = ah.base()
    d["symmetry"] = {"matching_pairs": [["n_tagonly", "Q1"]]}
    d["_note"] = "n_tagonly"
    _add_port(d, "n_tagonly")
    exc, detail = ah.rejected(load_topology, ah.write(tmp_path, d))
    assert [h.rule for h in detail["hits"]] == ["port_net_unknown"]


def test_rail_terminal_kinds_count_as_connected():
    devs = (DeviceDecl("Q1", "nmos", "r_d", "r_g", "r_s", "r_b"),)
    pas = (PassiveDecl("C1", "capacitor", ("r_d", "r_p")),)
    srcs = (SourceDecl("I1", "current_source", ("r_q", "r_s")),)
    rails = RailDeclaration(frozenset({"r_d", "r_g", "r_s", "r_b", "r_p", "r_q"}))
    assert check_hidden_rails(rails, devs, pas, srcs) == ()


def test_undeclared_bulk_is_not_a_terminal():
    """bulk 를 선언하지 않은 소자는 bulk 단자 넷을 만들지 않는다 -- 레일이 어디에도 없으면 rail_not_connected."""
    devs = (DeviceDecl("Q1", "nmos", "n_d", "n_g", "r_s"),)
    hits = check_hidden_rails(RailDeclaration(frozenset({"r_s", "r_sub"})), devs, (), ())
    assert [h.rule for h in hits] == ["rail_not_connected"] and "r_sub" in hits[0].elements
