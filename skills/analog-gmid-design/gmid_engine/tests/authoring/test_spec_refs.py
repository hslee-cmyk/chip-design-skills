"""참조 해석 `value_from_constraint`·`value_from_file` (gate `references`) -- SPEC_CONTRACT 0절(value_from_file 대상·ref_cycle·
ref_unresolved·ref_file_rejected), 2절 ref_* 행, 3절(참조 대상 결정 대기 -> value None + value_decision, pending 에 ID)."""
from __future__ import annotations

US = {"kind": "user_spec", "record": "r", "decided": "2026-10-07"}
REF = {"kind": "reference"}


def _add(sc, **c):
    sc.human["constraints"].append(c)
    return c


def _ref_only(sc, rule):
    d = sc.reject()
    assert rule in sc.rules(d), sc.rules(d)
    assert d["rejected_gates"] == ("references",)
    assert d["not_evaluated"] == ()
    return d


def test_value_from_constraint_resolved(sc):
    doc = sc.load()
    got = {c.metric: c for c in doc.constraints if c.metric}
    raw = {c["metric"]: c for c in sc.human["constraints"] if isinstance(c["metric"], str)}
    assert got["parasitic_pm_ss_deg"].value == raw["pm_ss_deg"]["value"]
    assert got["mirror_ratio_error_mv"].value == raw["mismatch_sigma_mv"]["value"]


def test_value_from_file_resolved(sc):
    ref = sc.read_spec("fx_spec_ref")
    want = [c for c in ref["human"]["constraints"] if c["metric"] == "ugf_ss_hz"][0]["value"]
    got = [c for c in sc.load().constraints if c.metric == "ugf_ss_hz"][0]
    assert got.value == want and got.judged is True


def test_value_from_file_judged_follows_pending_spice_target(sc):
    _add(sc, metric="rout_ss_ohm", op="<=", value_from_file="fx_spec_ref#rout_ss_ohm", source=dict(REF))
    got = [c for c in sc.load().constraints if c.metric == "rout_ss_ohm"][0]
    ref = sc.read_spec("fx_spec_ref")
    assert [c for c in ref["human"]["constraints"] if c["metric"] == "rout_ss_ohm"][0]["source"]["kind"] == "pending_spice"
    assert got.judged is False


def test_chain_of_value_from_constraint(sc):
    """대상이 다시 참조면 따라간다: power_dc_w -> mirror_ratio_error_mv -> mismatch_sigma_mv."""
    _add(sc, metric="power_dc_w", op="<=", value_from_constraint="mirror_ratio_error_mv", source=dict(REF))
    got = [c for c in sc.load().constraints if c.metric == "power_dc_w"][0]
    assert got.value == sc.constraint("mismatch_sigma_mv")["value"]


def test_ref_to_pending_target_becomes_pending(sc):
    sc.human["compensation_targets"]["pm_target_deg"] = {"value_from_file": "fx_spec_ref#pm_target_deg", "source": dict(REF)}
    ref_id = sc.read_spec("fx_spec_ref")["human"]["compensation_targets"]["pm_target_deg"]["pending"]
    doc = sc.load()
    t = dict(doc.compensation_targets)["pm_target_deg"]
    assert t.value is None and t.decision == ref_id
    assert ref_id in [p.decision for p in doc.pending]


def test_constraint_ref_to_pending_metric_target_value(sc):
    """제약 참조 대상 값이 결정 대기 -> value None + value_decision, 그 ID 가 pending 에."""
    sc.human["constraints"] = [c for c in sc.human["constraints"] if c.get("metric") != "pm_ss_deg"]
    sc.human["compensation_targets"]["pm_target_deg"] = {"value": 60.0, "source": dict(US)}
    _add(sc, metric="pm_ss_deg", op=">=", value_from_file="fx_spec_ref#pm_target_deg", source=dict(REF))
    doc = sc.load()
    pm = [c for c in doc.constraints if c.metric == "pm_ss_deg"][0]
    assert pm.value is None and pm.value_decision == "SP-93"
    assert "SP-93" in [p.decision for p in doc.pending]


def test_ref_unresolved_constraint_name(sc):
    sc.constraint("mirror_ratio_error_mv")["value_from_constraint"] = "gbw_ss_hz"  # pending_constraints 에만 있음
    _ref_only(sc, "ref_unresolved")


def test_ref_unresolved_file_missing(sc):
    sc.constraint("ugf_ss_hz")["value_from_file"] = "fx_spec_nofile#ugf_ss_hz"
    _ref_only(sc, "ref_unresolved")


def test_ref_unresolved_bad_format(sc):
    sc.constraint("ugf_ss_hz")["value_from_file"] = "fx_spec_ref"
    _ref_only(sc, "ref_unresolved")


def test_ref_unresolved_name_not_in_target(sc):
    sc.constraint("ugf_ss_hz")["value_from_file"] = "fx_spec_ref#gain_ss_db"
    _ref_only(sc, "ref_unresolved")


def test_ref_ambiguous(sc):
    _add(sc, metric="mismatch_sigma_mv", op=">=", value=0.5, source=dict(US))
    _ref_only(sc, "ref_ambiguous")


def test_ref_cycle_in_file(sc):
    _add(sc, metric="power_dc_w", op="<=", value_from_constraint="area_search_m2", source=dict(REF))
    _add(sc, metric="area_search_m2", op="<=", value_from_constraint="power_dc_w", source=dict(REF))
    _ref_only(sc, "ref_cycle")


def test_ref_cycle_across_files(sc):
    ref = sc.read_spec("fx_spec_ref")
    ref["human"]["constraints"].append({"metric": "gain_ss_db", "op": ">=", "value_from_file": "fx_spec_amp#gain_ss_db",
                                        "source": dict(REF)})
    sc.write_spec(ref, "fx_spec_ref")
    d = sc.reject()
    # 순환은 대상 로드 사슬 안에서 잡힌다 -- 바깥에서 ref_cycle 그대로인지 ref_file_rejected(elements 에 ref_cycle)인지는
    # 계약이 정하지 않았다(0절 '사슬에 이미 있는 파일 = ref_cycle', '대상 로드 거부 = ref_file_rejected')
    assert "ref_cycle" in sc.rules(d) or any("ref_cycle" in h.elements for h in d["hits"]), d["hits"]
    assert d["rejected_gates"] == ("references",)


def test_ref_file_rejected_carries_target_rules(sc):
    ref = sc.read_spec("fx_spec_ref")
    ref["meta"]["schema_version"] = "4"
    sc.write_spec(ref, "fx_spec_ref")
    hit = sc.only(sc.reject(), "ref_file_rejected", "references", not_evaluated=())
    assert hit.elements == ("schema_version",)


def test_ref_file_rejected_on_target_topology_fp(sc):
    t = sc.read_topo("fx_spec_ref")
    t["netlist"][0]["kind"] = "pmos"
    sc.write_topo(t, "fx_spec_ref")
    hit = sc.only(sc.reject(), "ref_file_rejected", "references", not_evaluated=())
    assert "topology_fp_mismatch" in hit.elements


def test_ref_file_rejected_on_target_topology_load(sc):
    t = sc.read_topo("fx_spec_ref")
    del t["passive_elements"]
    sc.write_topo(t, "fx_spec_ref")
    d = sc.reject()
    assert sc.rules(d) == ["ref_file_rejected"] and d["rejected_gates"] == ("references",)


def test_no_reference_resolution_when_earlier_gate_rejected(sc):
    sc.constraint("ugf_ss_hz")["value_from_file"] = "fx_spec_nofile#ugf_ss_hz"
    sc.human["supplies_v"]["values"]["rail_lo"] = 1.2   # supplies_top_rail_ambiguous
    d = sc.reject()
    assert "ref_unresolved" not in sc.rules(d)
    assert "references" in d["not_evaluated"]

