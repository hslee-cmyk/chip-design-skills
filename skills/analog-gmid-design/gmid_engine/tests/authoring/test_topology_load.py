"""`load_topology` -- CONTRACT 0절(실패 형식·not_evaluated), 1절(순서·일괄 거부·캐시 없음·OS 오류), 3절 위반 32종.

위반 32종 = 3.2~3.11 표의 rule 키(json_read 5종 제외, 그쪽은 test_json_read). 픽스처마다 위반 하나를 넣은
`fixtures/<gate>__<rule>.topology.json` 을 실제로 load 해 rule 키·rejected_gates·not_evaluated 를 확인한다.
"""
from __future__ import annotations

import glob
import hashlib
import json
from pathlib import Path

import pytest

from gmid_engine.authoring import TopologyDoc, load_topology
from gmid_engine.core import SchemaRejectedError

LIBRARY = Path(__file__).resolve().parents[3] / "assets" / "library"

# 0절 표의 not_evaluated 이름
NE_ELEMENTS = {"name_uniqueness", "ports.port_net_unknown", "hidden_rails"}   # devices·passives·ideal_sources 거부
NE_RAILS = {"ports.port_on_rail", "hidden_rails"}                               # rails 거부
NE_TOP = {"all_declarations"}

# (픽스처, 기대 rule 목록(정확) 또는 ("contains", rule), 계약에 이름이 있는 gate 또는 None, not_evaluated, elements 에 들어 있어야 할 이름)
CASES = [
    ("topology_schema__top_not_object", ["top_not_object"], "topology_schema", NE_TOP, ()),
    ("topology_schema__missing_key", ["missing_key"], "topology_schema", set(), ()),
    ("topology_schema__unknown_key", ["unknown_key"], "topology_schema", set(), ()),
    ("topology_schema__schema_version", ["schema_version"], "topology_schema", set(), ()),
    ("topology_schema__topology_name", ["topology_name"], "topology_schema", set(), ()),
    ("topology_schema__source_type", ["source_type"], "topology_schema", set(), ()),
    ("linked_files__linked_files_type", ["linked_files_type"], None, set(), ()),
    ("linked_files__linked_files_unsupported", ["linked_files_unsupported"], None, set(), ()),
    ("devices__missing_key", ["missing_key"], "devices", NE_ELEMENTS, ()),
    ("devices__netlist_type", ["netlist_type"], "devices", NE_ELEMENTS, ()),
    ("devices__element_type", ["element_type"], "devices", NE_ELEMENTS, ()),
    ("devices__element_unknown_key", ["element_unknown_key"], "devices", NE_ELEMENTS, ("Q1",)),
    ("devices__element_field", ["element_field"], "devices", NE_ELEMENTS, ("Q2",)),
    ("rails__missing_key", ["missing_key"], "rails", NE_RAILS, ()),
    ("rails__supply_nets_type", ["supply_nets_type"], "rails", NE_RAILS, ()),
    ("rails__supply_net_value", ["supply_net_value"], "rails", NE_RAILS, ()),
    ("rails__supply_net_duplicate", ["supply_net_duplicate"], "rails", NE_RAILS, ("rail_hi",)),
    ("passives__missing_key", ["missing_key"], "passives", NE_ELEMENTS, ()),
    ("passives__passive_elements_type", ["passive_elements_type"], "passives", NE_ELEMENTS, ()),
    ("passives__element_type", ["element_type"], "passives", NE_ELEMENTS, ()),
    ("passives__element_unknown_key", ["element_unknown_key"], "passives", NE_ELEMENTS, ("Cload",)),
    ("passives__element_field", ["element_field"], "passives", NE_ELEMENTS, ("Cf",)),
    ("passives__terminals", ["terminals"], "passives", NE_ELEMENTS, ("Cload",)),
    ("passives__element_value", ["element_value"], "passives", NE_ELEMENTS, ("Rf",)),
    ("ideal_sources__ideal_sources_type", ["ideal_sources_type"], "ideal_sources", NE_ELEMENTS, ()),
    ("name_uniqueness__name_duplicate", ["name_duplicate"], None, set(), ("Q4",)),
    ("name_uniqueness__name_case_collision", ["name_case_collision"], None, set(), ("Rf", "rf")),
    # ports missing_key / ports_type: 계약이 '그 hit 하나'라고 적지 않았다(no_input/no_output 동반 여부 미정) -> 포함만 본다
    ("ports__missing_key", ("contains", "missing_key"), "ports", set(), ()),
    ("ports__ports_type", ("contains", "ports_type"), "ports", set(), ()),
    ("ports__port_entry_type", ["port_entry_type"], "ports", set(), ("n_mid",)),
    ("ports__port_unknown_key", ["port_unknown_key"], "ports", set(), ("n_mid",)),
    ("ports__port_direction", ["port_direction"], "ports", set(), ("n_mid",)),
    ("ports__port_role", ["port_role"], "ports", set(), ("n_mid",)),
    ("ports__port_net_unknown", ["port_net_unknown"], "ports", set(), ("n_ghost",)),
    ("ports__port_on_rail", ["port_on_rail"], "ports", set(), ("rail_hi",)),
    ("ports__no_input_port", ["no_input_port"], "ports", set(), ()),
    ("ports__no_output_port", ["no_output_port"], "ports", set(), ()),
    ("hidden_rails__rail_not_connected", ["rail_not_connected"], None, set(), ("rail_mid",)),
    ("hidden_rails__hidden_rail", ["hidden_rail"], None, set(), ("Cload", "rail_ac")),
]

ALL_RULES_32 = {
    "top_not_object", "missing_key", "unknown_key", "schema_version", "topology_name", "source_type",
    "linked_files_type", "linked_files_unsupported",
    "netlist_type", "element_type", "element_unknown_key", "element_field",
    "supply_nets_type", "supply_net_value", "supply_net_duplicate",
    "passive_elements_type", "terminals", "element_value",
    "ideal_sources_type",
    "name_duplicate", "name_case_collision",
    "ports_type", "port_entry_type", "port_unknown_key", "port_direction", "port_role",
    "port_net_unknown", "port_on_rail", "no_input_port", "no_output_port",
    "rail_not_connected", "hidden_rail",
}


def test_cases_cover_all_32_rule_kinds():
    covered = set()
    for _, exp, *_ in CASES:
        covered.add(exp[1] if isinstance(exp, tuple) else exp[0])
    assert len(ALL_RULES_32) == 32
    assert covered == ALL_RULES_32


def test_every_case_fixture_exists_and_no_stray_fixture(ah):
    names = {c[0] for c in CASES} | {"base_valid", "multi__contract_example"}
    on_disk = {Path(p).name[: -len(".topology.json")] for p in glob.glob(str(ah.fixtures / "*.topology.json"))}
    assert on_disk == names


def _library_names():
    names = set()
    for f in LIBRARY.glob("*.topology.json"):
        if f.name.startswith("_"):
            continue
        d = json.loads(f.read_text(encoding="utf-8"))
        names.add(d["topology_name"])
        names.add(f.name.split(".")[0])
        for e in d["netlist"]:
            names.update(e[k] for k in ("name", "drain", "gate", "source", "bulk") if k in e)
        for e in d.get("passive_elements", []) + d.get("ideal_sources", []):
            names.add(e["name"])
            names.update(e["terminals"])
        names.update(k for k in d["ports"] if not k.startswith("_"))
        names.update(d["supply_nets"])
    return names


def _fixture_names(doc):
    out = set()
    if not isinstance(doc, dict):
        return out
    if isinstance(doc.get("topology_name"), str):
        out.add(doc["topology_name"])
    for key in ("netlist", "passive_elements", "ideal_sources"):
        for e in doc.get(key) or []:
            if isinstance(e, dict):
                out.update(v for k, v in e.items() if k in ("name", "drain", "gate", "source", "bulk") and isinstance(v, str))
                out.update(t for t in e.get("terminals", []) if isinstance(t, str))
    if isinstance(doc.get("ports"), dict):
        out.update(k for k in doc["ports"] if not k.startswith("_"))
    if isinstance(doc.get("supply_nets"), list):
        out.update(n for n in doc["supply_nets"] if isinstance(n, str))
    return out - {""}


def test_fixture_names_disjoint_from_library(ah):
    lib = _library_names()
    assert {"vdd", "gnd", "agnd", "two_stage_ota"} <= lib  # 집계가 실제로 이름을 모았다
    for p in ah.fixtures.glob("*.topology.json"):
        doc = json.loads(p.read_text(encoding="utf-8"))
        if isinstance(doc, list):
            doc = doc[0]
        assert not (_fixture_names(doc) & lib), (p.name, _fixture_names(doc) & lib)


def test_base_fixture_loads(ah):
    doc = load_topology(str(ah.path("base_valid")))
    assert isinstance(doc, TopologyDoc)


@pytest.mark.parametrize("case", CASES, ids=[c[0] for c in CASES])
def test_single_violation_fixture_rejected(ah, case):
    name, exp, gate, ne, elems = case
    path = str(ah.path(name))
    exc, detail = ah.rejected(load_topology, path)
    assert detail["gate"] == "topology_load"
    assert detail["where"] == path
    hits = detail["hits"]
    rules = ah.rules(hits)
    if isinstance(exp, tuple):
        assert exp[1] in rules, rules
        target = next(h for h in hits if h.rule == exp[1])
    else:
        assert rules == exp, [(h.rule, h.where, h.elements) for h in hits]
        target = hits[0]
    assert set(elems) <= set(target.elements), target
    rg = detail["rejected_gates"]
    assert isinstance(rg, tuple) and list(rg) == sorted(rg)
    if gate is not None:
        assert rg == (gate,)
    else:
        assert len(rg) == 1 and rg[0] not in {"topology_schema", "devices", "rails", "passives", "ideal_sources", "ports"}
    nev = detail["not_evaluated"]
    assert isinstance(nev, tuple) and len(nev) == len(set(nev))
    assert set(nev) == ne


def test_contract_example_all_violations_in_one_exception(ah):
    """1절 예: 미지 최상위 키 + n_fingers + supply_nets 중복 + 포트 direction·role -> 예외 1개, hits 5개, 게이트 순서."""
    path = str(ah.path("multi__contract_example"))
    exc, detail = ah.rejected(load_topology, path)
    hits = detail["hits"]
    assert len(hits) == 5
    # 게이트 순서(topology_schema -> devices -> rails -> ports), 게이트 안 문서 순서(n_mid 다음 n_rzn)
    assert ah.rules(hits) == ["unknown_key", "element_unknown_key", "supply_net_duplicate", "port_direction", "port_role"]
    assert "Q1" in hits[1].elements and "rail_lo" in hits[2].elements
    assert "n_mid" in hits[3].elements and "n_rzn" in hits[4].elements
    assert detail["rejected_gates"] == ("devices", "ports", "rails", "topology_schema")
    assert set(detail["not_evaluated"]) == NE_ELEMENTS | NE_RAILS


def test_hits_not_truncated(ah, tmp_path):
    doc = ah.base()
    bad = [5, "", 7.5, None, True, "", [], {}, 0, "", 3, ""]
    doc["supply_nets"] = ["rail_hi", "rail_lo", "rail_ac"] + bad
    exc, detail = ah.rejected(load_topology, ah.write(tmp_path, doc))
    assert ah.rules(detail["hits"]) == ["supply_net_value"] * len(bad)


def test_doc_order_inside_gate(ah, tmp_path):
    doc = ah.base()
    doc["netlist"].reverse()  # Q4, Q3, Q2, Q1
    ah.dev(doc, "Q1")["w"] = 1.0
    ah.dev(doc, "Q3")["n_fingers"] = 4
    exc, detail = ah.rejected(load_topology, ah.write(tmp_path, doc))
    hits = detail["hits"]
    assert ah.rules(hits) == ["element_unknown_key", "element_unknown_key"]
    assert "Q3" in hits[0].elements and "Q1" in hits[1].elements


def test_not_evaluated_empty_when_only_ports_and_schema_rejected(ah, tmp_path):
    doc = ah.base()
    doc["widget_count"] = 1
    doc["ports"]["n_mid"] = {"direction": "sideways", "role": "aux"}
    exc, detail = ah.rejected(load_topology, ah.write(tmp_path, doc))
    assert ah.rules(detail["hits"]) == ["unknown_key", "port_direction"]
    assert detail["rejected_gates"] == ("ports", "topology_schema")
    assert detail["not_evaluated"] == ()


def test_ports_format_checks_still_run_when_elements_rejected(ah, tmp_path):
    """0절: ports.port_net_unknown 만 빠지고 포트 형식 검사는 그대로 한다. port_on_rail 은 rails 가 살아 있으면 돈다."""
    doc = ah.base()
    ah.dev(doc, "Q2")["drain"] = 3                                      # devices 거부
    doc["ports"]["n_ghost"] = {"direction": "input", "role": "aux_input"}  # 넷 미지 -- 검사 안 됨
    doc["ports"]["rail_lo"] = {"direction": "output", "role": "aux_out"}   # 레일 위 포트 -- 검사됨
    doc["ports"]["n_mid"] = {"direction": "input", "role": 3}              # 형식 위반 -- 검사됨
    exc, detail = ah.rejected(load_topology, ah.write(tmp_path, doc))
    rules = ah.rules(detail["hits"])
    assert rules[0] == "element_field"
    assert "port_net_unknown" not in rules
    assert "port_on_rail" in rules and "port_role" in rules
    assert set(detail["not_evaluated"]) == NE_ELEMENTS


def test_sources_rejection_marks_not_evaluated(ah, tmp_path):
    doc = ah.base()
    doc["ideal_sources"][0]["value_volt"] = 1.0   # 값 필드 2개
    exc, detail = ah.rejected(load_topology, ah.write(tmp_path, doc))
    assert ah.rules(detail["hits"]) == ["element_value"]
    assert detail["rejected_gates"] == ("ideal_sources",)
    assert set(detail["not_evaluated"]) == NE_ELEMENTS


def test_json_level_violation_raised_as_json_read(ah, tmp_path):
    p = tmp_path / "bom.topology.json"
    p.write_bytes(b"\xef\xbb\xbf" + ah.path("base_valid").read_bytes())
    exc, detail = ah.rejected(load_topology, str(p))
    assert detail["gate"] == "json_read"
    assert ah.rules(detail["hits"]) == ["bom"]
    assert "rejected_gates" not in detail and "not_evaluated" not in detail


def test_missing_file_propagates_os_error(tmp_path):
    with pytest.raises(FileNotFoundError):
        load_topology(str(tmp_path / "nope.topology.json"))
    with pytest.raises(FileNotFoundError):
        load_topology(str(tmp_path / "nope.topology.json"))


def test_no_cache_reads_file_each_call(ah, tmp_path):
    doc = ah.base()
    path = ah.write(tmp_path, doc)
    first = load_topology(path)
    doc["netlist"][0]["kind"] = "pmos"
    ah.write(tmp_path, doc)
    second = load_topology(path)
    assert first.connectivity_fp != second.connectivity_fp
    assert second.file_sha256 == hashlib.sha256(Path(path).read_bytes()).hexdigest()
    doc["ports"]["n_mid"] = {"direction": "nowhere", "role": "x"}
    ah.write(tmp_path, doc)
    with pytest.raises(SchemaRejectedError):
        load_topology(path)


def test_pass_result_fields_from_fixture(ah):
    path = ah.path("base_valid")
    raw = ah.raw("base_valid")
    doc = load_topology(str(path))
    assert doc.name == raw["topology_name"]
    assert doc.file_sha256 == hashlib.sha256(path.read_bytes()).hexdigest()
    assert len(doc.connectivity_fp) == 64 and all(c in "0123456789abcdef" for c in doc.connectivity_fp.lower())
    assert [d.name for d in doc.devices] == sorted(e["name"] for e in raw["netlist"])
    assert [p.name for p in doc.passives] == sorted(e["name"] for e in raw["passive_elements"])
    assert [s.name for s in doc.sources] == sorted(e["name"] for e in raw["ideal_sources"])
    assert doc.rails == frozenset(raw["supply_nets"])
    assert [(p.net, p.direction, p.role) for p in doc.ports] == sorted(
        (k, v["direction"], v["role"]) for k, v in raw["ports"].items() if not k.startswith("_"))
