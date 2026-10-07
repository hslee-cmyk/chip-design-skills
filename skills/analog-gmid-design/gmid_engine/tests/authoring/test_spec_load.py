"""`load_sizing_spec(path, topology, metric_catalog)` -- SPEC_CONTRACT 0절(진입점·순서·일괄 거부·not_evaluated·캐시 없음),
1절 결정 대기 표지 수집. 근거는 계약 문장과 픽스처 JSON 직접 집계(spec_*.py 소스 미열람)."""
from __future__ import annotations

import hashlib
import json

import pytest

from gmid_engine.authoring import PendingMark, SizingSpecDoc, load_sizing_spec, load_topology
from gmid_engine.core import MetricSignature, SchemaRejectedError, exit_code_for


def _pending_marks_in_json(obj):
    """JSON 직접 집계: 주석 밖 키가 `pending` 하나인 객체의 ID."""
    out = []
    if isinstance(obj, dict):
        keys = [k for k in obj if not k.startswith("_")]
        if keys == ["pending"]:
            return [obj["pending"]]
        for v in obj.values():
            out += _pending_marks_in_json(v)
    elif isinstance(obj, list):
        for v in obj:
            out += _pending_marks_in_json(v)
    return out


def test_base_fixture_loads(sc):
    doc = sc.load()
    assert isinstance(doc, SizingSpecDoc)
    assert doc.circuit == sc.spec["meta"]["circuit"]
    assert doc.topology_fp == sc.spec["meta"]["topology_fp"]
    assert doc.origin == sc.spec["meta"]["origin"]
    assert doc.file_sha256 == hashlib.sha256((sc.dir / "fx_spec_amp.sizing_spec.json").read_bytes()).hexdigest()


def test_pending_marks_pass_and_are_listed(sc):
    """1절: 표지는 로드를 통과하고 모두 `pending`(경로, ID)에 모인다(경로 정렬)."""
    doc = sc.load()
    want = sorted(_pending_marks_in_json(sc.spec))
    assert want == ["MOD5", "MOD9", "SP-91"]
    assert all(isinstance(p, PendingMark) for p in doc.pending)
    assert sorted(p.decision for p in doc.pending) == want
    paths = [p.path for p in doc.pending]
    assert paths == sorted(paths) and len(set(paths)) == len(paths)


def test_pending_in_every_accepting_slot_passes_and_listed(sc):
    """1절 '표지를 받는 자리' 전부에 표지를 놓아도 통과, 놓은 표지 수만큼 모인다(참조로 생기는 표지 제외 위해 참조 제거)."""
    h = sc.human
    h["input_dc"] = {"pending": "SP-2"}
    h["element_values"] = {k: {"pending": "SP-10"} for k in h["element_values"]}
    h["feedback"] = {"pending": "CI-10"}
    h["constraints"] = [
        {"metric": {"pending": "MOD5"}, "op": ">=", "value": 1.0,
         "source": {"kind": "user_spec", "record": "r", "decided": "2026-10-07"}},
        {"metric": "gain_ss_db", "op": ">=", "value": 1.0, "view": {"pending": "MOD5"},
         "source": {"kind": "user_spec", "record": "r", "decided": "2026-10-07"}},
    ]
    h["compensation_targets"] = {"gbw_target_hz": {"pending": "SP-5"}, "pm_target_deg": {"pending": "SP-3"},
                                 "settling": {"pending": "ET-1"}}
    h["node_voltage_targets_v"] = {"pending": "CI-15"}
    h["intended_region"] = {"pending": "CI-18"}
    h["objective"]["budgets"] = {"pending": "PA-1"}
    for sec in ("search", "spice_check", "front_refilter"):
        h[sec] = {k: {"pending": "U-45"} for k in h[sec]}
    doc = sc.load()
    want = sorted(_pending_marks_in_json(sc.spec))
    assert len(want) == 1 + 5 + 1 + 2 + 3 + 1 + 1 + 1 + 5 + 6 + 3
    assert sorted(p.decision for p in doc.pending) == want


@pytest.mark.parametrize("pid", ["SP-1", "AC-3", "CI-18", "PA-2", "ET-7", "U-45", "MOD5", "MOD10"])
def test_pending_id_formats_accepted(sc, pid):
    sc.human["input_dc"] = {"pending": pid}
    want = _pending_marks_in_json(sc.spec).count(pid)
    assert [p.decision for p in sc.load().pending].count(pid) == want >= 1


def test_contract_batch_one_exception_many_gates(sc):
    """여러 섹션 위반 -> SchemaRejectedError 한 번, hits 전부, rejected_gates 정렬, references 미평가."""
    h = sc.human
    h["supplies_v"]["values"]["rail_hi"] = "high"                     # supplies / supplies_value
    h["input_dc"] = {"net": "n_mid", "source": h["input_dc"]["source"]}  # input_dc / input_dc_net_not_rail
    h["element_values"]["Rfb"]["value_ohm"] = -1.0                    # elements / element_value
    sc.constraint("gain_ss_db")["op"] = "=="                           # constraints / op_value
    h["compensation_targets"]["settling"]["linear_s"] = 1e-07         # compensation_targets / settling_order
    h["node_voltage_targets_v"]["rail_hi"] = {"value_v": 1.0, "source": {"kind": "user_spec", "record": "r", "decided": "2026-10-07"}}  # node_targets
    h["intended_region"] = {"Qzz": {"region": "whatever_region", "source": {"kind": "user_spec", "record": "r", "decided": "2026-10-07"}}}
    h["search"]["search_method"]["value"] = "fast"                     # settings / search_method
    d = sc.reject()
    rules = sc.rules(d)
    for r in ("supplies_value", "input_dc_net_not_rail", "element_value", "op_value", "settling_order",
              "node_target_net", "intended_region_device", "search_method"):
        assert r in rules, rules
    assert set(d["rejected_gates"]) == {"supplies", "input_dc", "elements", "constraints", "compensation_targets",
                                        "node_targets", "intended_region", "settings"}
    assert set(d["not_evaluated"]) == {"references"}
    # 게이트 순서(0절 순서)대로 모인다
    order = ["supplies_value", "input_dc_net_not_rail", "element_value", "op_value", "settling_order",
             "node_target_net", "intended_region_device", "search_method"]
    pos = [rules.index(r) for r in order]
    assert pos == sorted(pos)


def test_hits_not_truncated(sc):
    h = sc.human
    for i in range(12):
        h["constraints"].append({"metric": "nope_metric_%d" % i, "op": ">=", "value": 1.0,
                                 "source": {"kind": "user_spec", "record": "r", "decided": "2026-10-07"}})
    d = sc.reject()
    assert sc.rules(d).count("metric_unknown") == 12


def test_not_evaluated_all_sections(sc):
    sc.spec["human"] = []
    d = sc.reject()
    assert "all_sections" in d["not_evaluated"]
    assert "spec_schema" in d["rejected_gates"]


def test_not_evaluated_topology_cross_checks_on_fp_mismatch(sc):
    """지문 불일치면 교차 검사(레일·원소 이름) 안 함 -- 교차 위반을 넣어도 그 hit 은 나오지 않는다. 섹션 형식은 본다."""
    sc.spec["meta"]["topology_fp"] = "0" * 64
    sc.human["supplies_v"]["values"]["rail_zz"] = 0.3        # 교차 검사 위반(넷 밖) -- 보지 않음
    sc.human["element_values"]["Rzz"] = sc.human["element_values"]["Rfb"]  # 교차(이름 밖) -- 보지 않음
    sc.constraint("gain_ss_db")["op"] = "=="                 # 형식 -- 본다
    d = sc.reject()
    rules = sc.rules(d)
    assert "topology_fp_mismatch" in rules and "op_value" in rules
    assert "supplies_net_extra" not in rules and "element_unknown" not in rules
    assert {"topology_cross_checks", "references"} <= set(d["not_evaluated"])


def test_references_evaluated_when_only_reference_violation(sc):
    sc.constraint("mirror_ratio_error_mv")["value_from_constraint"] = "power_dc_w"
    d = sc.reject()
    sc.only(d, "ref_unresolved", "references", not_evaluated=())


def test_missing_required_human_key_reported_once(sc):
    del sc.human["constraints"]
    d = sc.reject()
    assert sc.rules(d) == ["missing_key"]
    assert d["rejected_gates"] == ("spec_schema",)


@pytest.mark.parametrize("bad_topo", [None, "fx_spec_amp", {"name": "fx_spec_amp"}])
def test_topology_must_be_topology_doc(sc, bad_topo):
    path = sc.write_spec(sc.spec)
    with pytest.raises(TypeError):
        load_sizing_spec(path, bad_topo, {})


@pytest.mark.parametrize("bad_cat", [None, [("gain_ss_db", MetricSignature("dB", "ss", "transfer"))],
                                     {"gain_ss_db": ("dB", "ss", "transfer")}])
def test_catalog_must_be_mapping_of_signatures(sc, bad_cat):
    path = sc.write_spec(sc.spec)
    with pytest.raises(TypeError):
        load_sizing_spec(path, sc.topology(), bad_cat)


def test_empty_catalog_rejects_every_constraint_metric(sc):
    d = sc.reject(catalog={})
    named = [c for c in sc.human["constraints"] if isinstance(c["metric"], str)]
    named += sc.human["pending_constraints"]
    assert sc.rules(d).count("metric_unknown") >= len([c for c in sc.human["constraints"] if isinstance(c["metric"], str)])
    assert "constraints" in d["rejected_gates"]
    assert named  # 픽스처에 이름 있는 제약이 실제로 있다


def test_json_level_violation_passthrough(sc):
    p = sc.dir / "fx_spec_amp.sizing_spec.json"
    p.write_bytes(b"\xef\xbb\xbf" + json.dumps(sc.spec).encode("utf-8"))
    with pytest.raises(SchemaRejectedError) as ei:
        load_sizing_spec(str(p), sc.topology(), {})
    detail = dict(ei.value.record.detail)
    assert detail["gate"] == "json_read"
    assert [h.rule for h in detail["hits"]] == ["bom"]
    assert exit_code_for(ei.value) == 7


def test_duplicate_key_json_level(sc):
    p = sc.dir / "fx_spec_amp.sizing_spec.json"
    text = json.dumps(sc.spec).replace('"origin": "fixture"', '"origin": "fixture", "origin": "canonical"', 1)
    p.write_text(text, encoding="utf-8")
    with pytest.raises(SchemaRejectedError) as ei:
        load_sizing_spec(str(p), sc.topology(), {})
    assert dict(ei.value.record.detail)["gate"] == "json_read"


def test_missing_file_is_os_error(sc):
    with pytest.raises(FileNotFoundError):
        load_sizing_spec(str(sc.dir / "nope.sizing_spec.json"), sc.topology(), {})


def test_no_cache_and_deterministic(sc, catalog):
    path = sc.write_spec(sc.spec)
    topo = sc.topology()
    a = load_sizing_spec(path, topo, catalog)
    b = load_sizing_spec(path, topo, catalog)
    assert a.spec_fp == b.spec_fp and a == b
    sc.human["constraints"][0]["value"] = 41
    sc.write_spec(sc.spec)
    c = load_sizing_spec(path, topo, catalog)
    assert c.spec_fp != a.spec_fp


def test_referenced_file_change_seen_on_next_load(sc, catalog):
    """캐시 없음: 참조 대상 spec 을 고치면 다음 로드가 새 값을 본다."""
    first = sc.load()
    ref = sc.read_spec("fx_spec_ref")
    ref["human"]["constraints"][0]["value"] = 2e8
    sc.write_spec(ref, "fx_spec_ref")
    second = sc.load()
    ugf = [c for c in second.constraints if c.metric == "ugf_ss_hz"][0]
    assert ugf.value == 2e8
    assert first.spec_fp != second.spec_fp


def test_rejected_record_is_immutable(sc):
    from gmid_engine.core import require_immutable
    sc.spec["meta"]["schema_version"] = "4"
    path = sc.write_spec(sc.spec)
    with pytest.raises(SchemaRejectedError) as ei:
        load_sizing_spec(path, sc.topology(), {})
    require_immutable(ei.value.record)


def test_spec_fixture_names_disjoint_from_library(sc):
    """합성 회로 이름(회로·소자·넷·레일·포트)이 library 9회로 이름과 겹치지 않는다(JSON 직접 집계)."""
    from pathlib import Path

    def names(t):
        out = {t["topology_name"]}
        for e in t["netlist"]:
            out |= {e[k] for k in ("name", "drain", "gate", "source", "bulk") if k in e}
        for e in t.get("passive_elements", []) + t.get("ideal_sources", []):
            out |= {e["name"], *e["terminals"]}
        return out | set(t["supply_nets"]) | {k for k in t["ports"] if not k.startswith("_")}

    lib = Path(__file__).resolve().parents[3] / "assets" / "library"
    lib_names = set()
    for p in lib.glob("*.topology.json"):
        if not p.name.startswith("_"):
            lib_names |= names(json.loads(p.read_text(encoding="utf-8")))
    assert {"vdd", "gnd", "two_stage_ota"} <= lib_names
    for circuit in ("fx_spec_amp", "fx_spec_ref"):
        assert not (names(sc.read_topo(circuit)) & lib_names), circuit
