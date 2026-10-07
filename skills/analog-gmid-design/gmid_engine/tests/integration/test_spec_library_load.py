"""9회로 교차 -- library 의 `<회로>.sizing_spec.json` 을 `load_sizing_spec` 에 실제로 건다 (authoring SPEC_CONTRACT 5절).

기대값: 계약 5절 표(제약 수·판정 수·pending 수, ID 별 합계)와 spec/topology JSON 직접 집계. 피검 함수로 기대값을 만들지 않는다.
이름표 = 5절 '픽스처 이름표'(단위·domain 은 이 test 가 정함).
"""
from __future__ import annotations

import json
from collections import Counter
from pathlib import Path

import pytest

from gmid_engine.authoring import load_sizing_spec, load_topology
from gmid_engine.core import MetricSignature as M

LIBRARY = Path(__file__).resolve().parents[3] / "assets" / "library"

CATALOG = {
    "gain_ss_db": M("dB", "ss", "transfer"),
    "ugf_ss_hz": M("Hz", "ss", "transfer"),
    "gbw_ss_hz": M("Hz", "ss", "transfer"),
    "pm_ss_deg": M("deg", "ss", "transfer"),
    "parasitic_pm_ss_deg": M("deg", "ss", "transfer"),
    "rout_ss_ohm": M("ohm", "ss", "transfer"),
    "ratio_ss_db": M("dB", "ss", "ratio"),
    "mismatch_sigma_mv": M("mV", "dc", "none"),
    "mirror_ratio_error_mv": M("mV", "dc", "none"),
    "power_dc_w": M("W", "dc", "none"),
    "area_search_m2": M("m2", "geom", "none"),
    "supply_current_dc": M("A", "dc", "none", "power"),
    "area_layout_m2": M("m2", "geom", "none", "area"),
}

# 5절 표: 회로 -> (제약 수, 판정 수, pending 표지 수)
TABLE = {
    "common_gate_amplifier": (0, 0, 6),
    "current_reuse_telescopic_ota": (8, 5, 15),
    "folded_cascode": (0, 0, 7),
    "ngcc_3stage_ff": (3, 2, 7),
    "nmcnr_amplifier": (2, 2, 6),
    "pushpull_follower_buffer": (1, 1, 5),
    "sf_pushpull_output_opamp": (3, 3, 6),
    "two_stage_ota": (2, 1, 7),
    "two_stage_ota_sf": (3, 2, 6),
}
ID_TOTALS = {"AC-3": 9, "PA-1": 9, "PA-2": 9, "CI-15": 9, "CI-18": 9, "SP-2": 7, "MOD5": 7, "SP-3": 2, "SP-10": 2,
             "CI-10": 1, "CI-17": 1}


def _spec(name):
    return json.loads((LIBRARY / (name + ".sizing_spec.json")).read_text(encoding="utf-8"))


def _load(name):
    topo = load_topology(str(LIBRARY / (name + ".topology.json")))
    return load_sizing_spec(str(LIBRARY / (name + ".sizing_spec.json")), topo, CATALOG)


def _markers(obj):
    """JSON 직접 집계: 주석 밖 키가 pending 하나인 객체의 ID."""
    if isinstance(obj, dict):
        keys = [k for k in obj if not k.startswith("_")]
        if keys == ["pending"]:
            return [obj["pending"]]
        return [x for v in obj.values() for x in _markers(v)]
    if isinstance(obj, list):
        return [x for v in obj for x in _markers(v)]
    return []


def _judged_from_json(name, metric_or_key, seen=()):
    """JSON 직접 집계로 판정 여부: user_spec True, pending_spice False, reference 는 대상 따라감, metric 결정 대기 False."""
    raw = _spec(name)["human"]
    cons = [c for c in raw["constraints"] if c.get("metric") == metric_or_key]
    if not cons:  # 보상 목표 등 판정 없는 대상
        return True
    return _judged_of(name, cons[0], seen)


def _judged_of(name, c, seen=()):
    if not isinstance(c["metric"], str):
        return False
    kind = c["source"]["kind"]
    if kind == "user_spec":
        return True
    if kind == "pending_spice":
        return False
    if "value_from_constraint" in c:
        return _judged_from_json(name, c["value_from_constraint"], seen + (name,))
    circuit, target = c["value_from_file"].split("#")
    return _judged_from_json(circuit, target, seen + (name,))


def test_library_has_nine_specs():
    names = sorted(p.name[: -len(".sizing_spec.json")] for p in LIBRARY.glob("*.sizing_spec.json"))
    assert names == sorted(TABLE)


@pytest.mark.parametrize("name", sorted(TABLE))
def test_spec_loads_and_matches_json(name):
    doc = _load(name)
    raw = _spec(name)
    assert doc.circuit == raw["meta"]["circuit"] == name
    assert doc.supplies_v == tuple(sorted((k, float(v)) for k, v in raw["human"]["supplies_v"]["values"].items()))
    topo = json.loads((LIBRARY / (name + ".topology.json")).read_text(encoding="utf-8"))
    assert {k for k, _ in doc.supplies_v} == set(topo["supply_nets"])
    assert [e.name for e in doc.element_values] == sorted(k for k in raw["human"]["element_values"] if not k.startswith("_"))
    assert {e.name for e in doc.element_values} == {e["name"] for e in topo.get("passive_elements", []) + topo.get("ideal_sources", [])}
    # 제약 수·판정 수 (JSON 집계 + 5절 표)
    n_cons, n_judged, n_pending = TABLE[name]
    assert len(doc.constraints) == len(raw["human"]["constraints"]) == n_cons
    want_judged = sum(_judged_of(name, c) for c in raw["human"]["constraints"])
    assert want_judged == n_judged
    assert [c.judged for c in doc.constraints] == [_judged_of(name, c) for c in raw["human"]["constraints"]]
    assert len(doc.judged_constraints) == n_judged


@pytest.mark.parametrize("name", sorted(TABLE))
def test_remaining_pending_equals_json_markers(name):
    doc = _load(name)
    want = sorted(_markers(_spec(name)))
    assert sorted(p.decision for p in doc.pending) == want
    assert len(want) == TABLE[name][2]


def test_pending_id_totals():
    json_total = Counter(x for name in TABLE for x in _markers(_spec(name)))
    doc_total = Counter(p.decision for name in TABLE for p in _load(name).pending)
    assert json_total == doc_total
    assert dict(json_total) == ID_TOTALS
    assert sum(ID_TOTALS.values()) == 65


@pytest.mark.parametrize("name", sorted(TABLE))
def test_spec_fp_deterministic(name):
    assert _load(name).spec_fp == _load(name).spec_fp


def test_cross_file_reference_value():
    """two_stage_ota_sf 의 value_from_file 참조가 two_stage_ota JSON 값으로 해석된다."""
    doc = _load("two_stage_ota_sf")
    base = _spec("two_stage_ota")["human"]
    gain = [c for c in doc.constraints if c.metric == "gain_ss_db"][0]
    assert gain.value == [c for c in base["constraints"] if c["metric"] == "gain_ss_db"][0]["value"]
    gbw = dict(doc.compensation_targets)["gbw_target_hz"]
    assert gbw.value == base["compensation_targets"]["gbw_target_hz"]["value"]


def test_every_spec_meta_fp_matches_topology():
    for name in TABLE:
        topo = load_topology(str(LIBRARY / (name + ".topology.json")))
        assert _spec(name)["meta"]["topology_fp"] == topo.connectivity_fp, name
