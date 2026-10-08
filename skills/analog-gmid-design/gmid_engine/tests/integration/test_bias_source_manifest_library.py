"""9회로 교차 -- `bias_inputs`(authoring CONTRACT 9절)와 `source_manifest`(10절)를 assets/library 원본에 실제로 건다.

oracle 두 가지를 함께 쓴다(서로 독립):
- (a) gate 전용 넷 집합 = topology JSON 에서 9절 정의 문장대로 test 가 직접 센 것(MOS gate 에만 있고 d/s/선언 bulk·
  수동·이상원 terminals·레일·포트 어디에도 없는 넷). MOS 수·passive_elements 수도 JSON 직접 집계.
- (d) 사용자 선언값: Q6 "Q6는 반영해"(2026-10-08) 목록 -- common_gate {VNBias1, VNBias2, VPBias1}, folded {bias3},
  ngcc {VBN, VBP}, nmcnr {VB1..VB5}, pushpull {VNB1, VPB1}, two_stage·two_stage_sf {bias}, current_reuse·sf_pushpull 없음.
  Q7 "Q7도 모두 맞아"(2026-10-08) 개수표 -- 9회로 (MOS, passive).
피검 함수(load_topology) 결과는 이 둘과 대조만 한다.
"""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from gmid_engine.authoring import load_topology
from gmid_engine.core import SchemaRejectedError

LIBRARY = Path(__file__).resolve().parents[3] / "assets" / "library"

# (d) 사용자 결정 Q6 (user_decisions.md 2026-10-08)
USER_BIAS_INPUTS = {
    "common_gate_amplifier": {"VNBias1", "VNBias2", "VPBias1"},
    "current_reuse_telescopic_ota": set(),
    "folded_cascode": {"bias3"},
    "ngcc_3stage_ff": {"VBN", "VBP"},
    "nmcnr_amplifier": {"VB1", "VB2", "VB3", "VB4", "VB5"},
    "pushpull_follower_buffer": {"VNB1", "VPB1"},
    "sf_pushpull_output_opamp": set(),
    "two_stage_ota": {"bias"},
    "two_stage_ota_sf": {"bias"},
}
# (d) 사용자 결정 Q7 (MOS 수, passive 수)
USER_MANIFEST_COUNTS = {
    "common_gate_amplifier": (3, 0),
    "current_reuse_telescopic_ota": (51, 12),
    "folded_cascode": (13, 1),
    "ngcc_3stage_ff": (16, 3),
    "nmcnr_amplifier": (15, 5),
    "pushpull_follower_buffer": (6, 1),
    "sf_pushpull_output_opamp": (22, 5),
    "two_stage_ota": (7, 3),
    "two_stage_ota_sf": (9, 2),
}
CIRCUITS = sorted(USER_BIAS_INPUTS)
WITH_BIAS = [c for c in CIRCUITS if USER_BIAS_INPUTS[c]]


def _raw(name):
    return json.loads((LIBRARY / (name + ".topology.json")).read_text(encoding="utf-8"))


def _write(tmp_path, doc, name):
    p = tmp_path / (name + ".topology.json")
    p.write_text(json.dumps(doc, indent=2, ensure_ascii=False), encoding="utf-8")
    return str(p)


def gate_only_nets(doc):
    """oracle (a): CONTRACT 9절 정의를 JSON 에서 직접 집계."""
    gates, other = set(), set()
    for e in doc["netlist"]:
        gates.add(e["gate"])
        other |= {e["drain"], e["source"]}
        if "bulk" in e:
            other.add(e["bulk"])
    for key in ("passive_elements", "ideal_sources"):
        for e in doc.get(key, []):
            other |= set(e["terminals"])
    other |= set(doc["supply_nets"])
    other |= {k for k in doc["ports"] if not k.startswith("_")}
    return gates - other


def _rejected(path):
    with pytest.raises(SchemaRejectedError) as ei:
        load_topology(path)
    return dict(ei.value.record.detail)


def test_library_set_is_nine():
    names = sorted(p.name[:-len(".topology.json")] for p in LIBRARY.glob("*.topology.json")
                   if not p.name.startswith("_"))
    assert names == CIRCUITS


@pytest.mark.parametrize("name", CIRCUITS)
def test_bias_inputs_equal_hand_derived_gate_only_set(name):
    doc = _raw(name)
    expected = gate_only_nets(doc)
    assert expected == USER_BIAS_INPUTS[name]          # 두 oracle 이 서로 맞다(Q6 목록 = 정의대로 센 것)
    td = load_topology(str(LIBRARY / (name + ".topology.json")))
    assert td.bias_inputs == tuple(sorted(expected))


@pytest.mark.parametrize("name", CIRCUITS)
def test_source_manifest_counts_match(name):
    doc = _raw(name)
    m = doc["source_manifest"]
    actual = (len(doc["netlist"]), len(doc["passive_elements"]))
    assert actual == USER_MANIFEST_COUNTS[name]
    assert (m["device_count"], m["passive_count"]) == USER_MANIFEST_COUNTS[name]
    assert isinstance(m["figure"], str) and m["figure"]
    load_topology(str(LIBRARY / (name + ".topology.json")))   # 통과


@pytest.mark.parametrize("name", WITH_BIAS)
def test_dropping_one_declared_net_rejected(tmp_path, name):
    """선언에서 이름순 첫 넷 하나를 빼면 그 넷만 gate_only_undeclared(9회로 실제 회로에서 게이트가 거부한다)."""
    doc = _raw(name)
    drop = sorted(doc["bias_inputs"])[0]
    doc["bias_inputs"] = [n for n in doc["bias_inputs"] if n != drop]
    detail = _rejected(_write(tmp_path, doc, name))
    assert detail["rejected_gates"] == ("bias_inputs",)
    assert [(h.rule, h.elements) for h in detail["hits"]] == [("gate_only_undeclared", (drop,))]


@pytest.mark.parametrize("name", CIRCUITS)
def test_declaring_a_port_net_rejected(tmp_path, name):
    """실제 포트 넷(이름순 첫 포트)을 bias_inputs 에 더하면 bias_input_not_gate_only 하나."""
    doc = _raw(name)
    port = sorted(k for k in doc["ports"] if not k.startswith("_"))[0]
    doc["bias_inputs"] = list(doc.get("bias_inputs", [])) + [port]
    detail = _rejected(_write(tmp_path, doc, name))
    assert [(h.rule, h.elements) for h in detail["hits"]] == [("bias_input_not_gate_only", (port,))]


@pytest.mark.parametrize("name", CIRCUITS)
@pytest.mark.parametrize("field", ["device_count", "passive_count"])
def test_manifest_off_by_one_rejected(tmp_path, name, field):
    doc = _raw(name)
    doc["source_manifest"][field] += 1
    detail = _rejected(_write(tmp_path, doc, name))
    assert detail["rejected_gates"] == ("source_manifest",)
    assert [h.rule for h in detail["hits"]] == ["source_manifest_mismatch"]


@pytest.mark.parametrize("name", CIRCUITS)
def test_new_keys_not_in_connectivity_fp(tmp_path, name):
    """source_manifest 를 지우고 bias_inputs 를 역순으로 써도 connectivity_fp 같다(9·10절)."""
    doc = _raw(name)
    base = load_topology(str(LIBRARY / (name + ".topology.json")))
    del doc["source_manifest"]
    if "bias_inputs" in doc:
        doc["bias_inputs"] = list(reversed(doc["bias_inputs"]))
    td = load_topology(_write(tmp_path, doc, name))
    assert td.connectivity_fp == base.connectivity_fp
    assert td.bias_inputs == base.bias_inputs
