"""노드전압 목표 `human.node_voltage_targets_v` (gate `node_targets`) -- SPEC_CONTRACT 2절 node_target_net 행."""
from __future__ import annotations

import pytest

US = {"kind": "user_spec", "record": "r", "decided": "2026-10-07"}


def _terminal_nets(topo):
    nets = {e[k] for e in topo["netlist"] for k in ("drain", "gate", "source", "bulk") if k in e}
    nets |= {t for e in topo["passive_elements"] + topo.get("ideal_sources", []) for t in e["terminals"]}
    return nets


def test_result(sc):
    raw = sc.human["node_voltage_targets_v"]
    assert sc.load().node_voltage_targets_v == tuple(sorted((k, v["value_v"]) for k, v in raw.items()))


def test_empty_and_pending(sc):
    sc.human["node_voltage_targets_v"] = {}
    assert sc.load().node_voltage_targets_v == ()
    sc.human["node_voltage_targets_v"] = {"pending": "CI-15"}
    assert sc.load().node_voltage_targets_v.decision == "CI-15"


def test_any_non_rail_terminal_net_ok(sc):
    nets = sorted(_terminal_nets(sc.topo) - set(sc.topo["supply_nets"]))
    assert "n_fbk" in nets and "n_vcm" in nets  # 2단자 원소에만 있는 넷도 단자 넷
    sc.human["node_voltage_targets_v"] = {n: {"value_v": 0.5, "source": dict(US)} for n in nets}
    assert len(sc.load().node_voltage_targets_v) == len(nets)


@pytest.mark.parametrize("net", ["rail_hi", "rail_lo", "n_ghost"])
def test_node_target_net(sc, net):
    sc.human["node_voltage_targets_v"][net] = {"value_v": 0.5, "source": dict(US)}
    sc.reject_only("node_target_net", "node_targets")


@pytest.mark.parametrize("raw", [{"value_v": "0.7", "source": US}, {"value_v": None, "source": US}, 0.7,
                                 {"source": US}])
def test_type(sc, raw):
    sc.human["node_voltage_targets_v"]["n_mid"] = raw
    d = sc.reject()
    assert sc.rules(d) == ["type"], sc.rules(d)
    assert d["rejected_gates"] == ("node_targets",)


def test_section_not_object(sc):
    sc.human["node_voltage_targets_v"] = [["n_mid", 0.7]]
    d = sc.reject()
    assert "type" in sc.rules(d) and d["rejected_gates"] == ("node_targets",)


def test_source_required(sc):
    del sc.human["node_voltage_targets_v"]["n_mid"]["source"]
    sc.reject_only("source_missing", "node_targets")
