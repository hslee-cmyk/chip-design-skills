"""전원 선언 `human.supplies_v` (gate `supplies`) -- SPEC_CONTRACT 2절 supplies_* 행, 6절 11; 교차: supplies_v 키 = supply_nets."""
from __future__ import annotations

import pytest


def test_result_matches_json(sc):
    doc = sc.load()
    vals = sc.human["supplies_v"]["values"]
    assert doc.supplies_v == tuple(sorted((k, float(v)) for k, v in vals.items()))


def test_keys_equal_topology_supply_nets(sc):
    """JSON 교차 확인: 픽스처의 supplies_v 키 집합 = topology supply_nets."""
    assert set(sc.human["supplies_v"]["values"]) == set(sc.topo["supply_nets"])


@pytest.mark.parametrize("bad", ["1.2", None, True, [1.2]])
def test_supplies_value(sc, bad):
    sc.human["supplies_v"]["values"]["rail_hi"] = bad
    hit = sc.reject_only("supplies_value", "supplies")
    assert "rail_hi" in hit.elements or "rail_hi" in hit.where


def test_supplies_value_each_net(sc):
    sc.human["supplies_v"]["values"] = {"rail_hi": "a", "rail_lo": "b"}
    d = sc.reject()
    assert sc.rules(d) == ["supplies_value", "supplies_value"]


def test_net_missing(sc):
    del sc.human["supplies_v"]["values"]["rail_lo"]
    sc.reject_only("supplies_net_missing", "supplies")


def test_net_extra(sc):
    sc.human["supplies_v"]["values"]["n_mid"] = 0.5
    sc.reject_only("supplies_net_extra", "supplies")


def test_missing_and_extra_together(sc):
    vals = sc.human["supplies_v"]["values"]
    vals["rail_mid"] = vals.pop("rail_lo")
    d = sc.reject()
    assert sorted(sc.rules(d)) == ["supplies_net_extra", "supplies_net_missing"]


def test_top_rail_ambiguous(sc):
    sc.human["supplies_v"]["values"]["rail_lo"] = 1.2
    sc.reject_only("supplies_top_rail_ambiguous", "supplies")


def test_three_rails_one_top_ok(sc):
    t = sc.read_topo("fx_spec_amp")
    t["supply_nets"].append("rail_mid")
    t["passive_elements"].append({"name": "Cmd", "kind": "capacitor", "terminals": ["n_outp", "rail_mid"]})
    sc.write_topo(t)
    sc.resync_fp()
    sc.human["supplies_v"]["values"]["rail_mid"] = 0.6
    sc.human["element_values"]["Cmd"] = {"engine": True, "source": {"kind": "user_spec", "record": "r", "decided": "2026-10-07"}}
    sc.load()
    sc.human["supplies_v"]["values"]["rail_mid"] = 1.2
    sc.reject_only("supplies_top_rail_ambiguous", "supplies")


@pytest.mark.parametrize("raw", [[], "1.2", {"pending": "SP-1"}])
def test_section_type(sc, raw):
    """표지 불가 섹션(1절 '그 밖 자리 -> type'), 객체 아님 -> type."""
    sc.human["supplies_v"] = raw
    d = sc.reject()
    assert "type" in sc.rules(d)
    assert "supplies" in d["rejected_gates"]


def test_values_not_object(sc):
    sc.human["supplies_v"]["values"] = [["rail_hi", 1.2]]
    d = sc.reject()
    assert "type" in sc.rules(d)


def test_unknown_key(sc):
    sc.human["supplies_v"]["vdd_value"] = 1.2
    sc.reject_only("unknown_key", "supplies")


def test_source_required(sc):
    del sc.human["supplies_v"]["source"]
    sc.reject_only("source_missing", "supplies")
