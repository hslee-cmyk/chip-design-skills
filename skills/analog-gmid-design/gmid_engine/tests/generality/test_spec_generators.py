"""spec 생성기·변형기(topogen `synthetic_spec`·`rename_spec`) 자체 확인 -- 하류 metamorphic test 의 입력이 의도대로인가.

oracle 종류 (a) -- 구성으로 정해지는 성질(spec JSON 직접 집계 대 공개 로더 `load_sizing_spec` 결과):
- `synthetic_spec`: SPEC_CONTRACT 1·2절 형식으로 hit 없이 로드되고, 원소 값 = topology 의 옛 값(2절 `element_value_conflict` 가 다른
  값을 거부하므로 같은 값이어야 한다), supplies = 준 값.
- `rename_spec`: 이름 치환한 topology 와 짝지어 hit 없이 로드되고, 로드 결과의 이름 자리(supplies·원소 값·feedback·circuit)가 치환표로
  옮겨지며 이름이 없는 섹션 지문(SECTION_GROUPS 중 search·spice_check·front_refilter·objective)은 같다(3절 지문 정의).
- 옮기지 못하는 이름 자리(선언 view·노드 목표·영역)는 조용히 두지 않고 `ValueError`(helper docstring 규칙).
"""
from __future__ import annotations

import copy
import json
from pathlib import Path

import pytest

from gmid_engine.authoring import load_sizing_spec
from gmid_engine.core import MetricSignature
from gmid_engine.metrics import metric_catalog

from .pipeline import CATALOG_GAPS, SYNTH_SUPPLIES
from .topogen import random_renaming, rename, rename_spec, synthetic_spec, synthetic_topologies

LIBRARY = Path(__file__).resolve().parents[3] / "assets" / "library"
# two_stage_ota_sf 는 value_from_file 로 two_stage_ota 파일을 같은 폴더에서 읽는다(SPEC_CONTRACT 0절) -- 치환 사본 폴더에 대상이
# 없어 이 test 의 단독 로드 대상에서 뺀다(참조 대상 이름은 이 회로의 치환표 밖이다).
LIB = ("common_gate_amplifier", "current_reuse_telescopic_ota", "folded_cascode", "ngcc_3stage_ff", "nmcnr_amplifier",
       "pushpull_follower_buffer", "sf_pushpull_output_opamp", "two_stage_ota")
NAMELESS_SECTIONS = ("search_fp", "spice_check_fp", "refilter_fp", "objective_fp")
SPEC_VALUE_KEY = {"capacitor": "value_farad", "resistor": "value_ohm", "current_source": "value_dc_amp",
                  "voltage_source": "value_dc_v"}             # SPEC_CONTRACT 2절 element_value_key 표
TOPO_VALUE_KEY = {"capacitor": "value_farad", "resistor": "value_ohm", "current_source": "value_amp",
                  "voltage_source": "value_volt"}             # authoring CONTRACT 3.6·3.7


def _catalog():
    cat = dict(metric_catalog())
    for name, sig in CATALOG_GAPS:
        cat.setdefault(name, MetricSignature(*sig))
    return cat


def _write_pair(tmp_path, doc, spec_fn):
    d = tmp_path / ("p%d" % len(list(tmp_path.iterdir())))
    d.mkdir()
    tp = d / (doc["topology_name"] + ".topology.json")
    tp.write_text(json.dumps(doc), encoding="utf-8")
    from gmid_engine.authoring import load_topology
    td = load_topology(str(tp))
    sp = d / (doc["topology_name"] + ".sizing_spec.json")
    sp.write_text(json.dumps(spec_fn(td.connectivity_fp)), encoding="utf-8")
    return td, load_sizing_spec(str(sp), td, _catalog())


@pytest.mark.parametrize("name", sorted(synthetic_topologies()))
def test_synthetic_spec_loads_with_topology_values(tmp_path, name):
    doc = synthetic_topologies()[name]
    cons = (("power_dc_w", "<=", 1.0),)          # 뷰 없는 metric(입력 포트 모양과 무관 -- syn_diffpair5 role 은 유도 뷰 밖)
    td, spec = _write_pair(tmp_path, doc, lambda fp: synthetic_spec(doc, fp, dict(SYNTH_SUPPLIES), cons))
    assert spec.circuit == name and spec.topology_fp == td.connectivity_fp
    assert dict(spec.supplies_v) == dict(SYNTH_SUPPLIES)
    expect = {e["name"]: e[TOPO_VALUE_KEY[e["kind"]]] for key in ("passive_elements", "ideal_sources") for e in doc[key]}
    got = {ev.name: ev.value for ev in spec.element_values}
    assert got == expect
    assert all(ev.mode == "value" for ev in spec.element_values)
    assert [c.metric for c in spec.constraints] == ["power_dc_w"]


@pytest.mark.parametrize("name", LIB)
def test_rename_spec_loads_and_maps_names(tmp_path, name):
    doc = json.loads((LIBRARY / (name + ".topology.json")).read_text(encoding="utf-8"))
    spec_json = json.loads((LIBRARY / (name + ".sizing_spec.json")).read_text(encoding="utf-8"))
    before = copy.deepcopy(spec_json)
    m = random_renaming(doc, 3)
    _, a = _write_pair(tmp_path, doc, lambda fp: rename_spec(spec_json, {}, fp))
    _, b = _write_pair(tmp_path, rename(doc, m), lambda fp: rename_spec(spec_json, m, fp))
    assert spec_json == before                                   # 입력을 바꾸지 않는다
    assert b.circuit == m[name]
    assert dict(b.supplies_v) == {m[k]: v for k, v in a.supplies_v}
    assert {(m[e.name], e.mode, e.value) for e in a.element_values} == {(e.name, e.mode, e.value) for e in b.element_values}
    ev_path = "human.element_values."                          # 결정 대기 표지 경로에 원소 이름이 든다(SPEC_CONTRACT 1절)
    mapped = sorted((ev_path + m[p.path[len(ev_path):]] if p.path.startswith(ev_path) else p.path, p.decision)
                    for p in a.pending)
    assert sorted((p.path, p.decision) for p in b.pending) == mapped
    assert len(b.constraints) == len(a.constraints)
    fa, fb = dict(a.section_fps), dict(b.section_fps)
    for s in NAMELESS_SECTIONS:
        assert fb[s] == fa[s], s
    if a.element_values:
        assert fb["elements_fp"] != fa["elements_fp"]            # 이름이 실제로 바뀌었다(공허하지 않음)


@pytest.mark.parametrize("where", ["view", "node_voltage_targets_v", "intended_region"])
def test_rename_spec_refuses_unmapped_name_slots(where):
    spec_json = json.loads((LIBRARY / "two_stage_ota.sizing_spec.json").read_text(encoding="utf-8"))
    if where == "view":
        spec_json["human"]["constraints"][0]["view"] = {"sense_p": "OUT", "sense_mode": "single_ended"}
    else:
        spec_json["human"][where] = {"values": {"OUT": 0.9}}
    with pytest.raises(ValueError):
        rename_spec(spec_json, {"OUT": "zz"}, "fp")
