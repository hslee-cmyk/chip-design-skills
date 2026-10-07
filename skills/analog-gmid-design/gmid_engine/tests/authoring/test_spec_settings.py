"""설정 섹션 `objective`·`search`·`spice_check`·`front_refilter` (gate `settings`) -- SPEC_CONTRACT 2절 settings 행·규칙 어휘,
6절 6(numeric_in_rule_field 는 settings 가 낸다)·10(optional_stages 이름)."""
from __future__ import annotations

import pytest

US = {"kind": "user_spec", "record": "r", "decided": "2026-10-07"}
PR = {"kind": "plan_rule", "plan_id": "DEC-1"}
SEARCH_FIELDS = ("wall_clock_budget_s", "front_budget_s", "search_method", "optional_stages", "dof_rank_sample_count")
SPICE_RULES = {
    "acceptance_rule": ("free_spec_and_all_saturated",),
    "saturation_rule": ("vds_ge_vdsat", "vds_ge_vdsat_plus_tol_v"),
    "node_compare_rule": ("record_only",),
    "device_compare_rule": ("record_only",),
    "forced_warn_rule": ("forced_device_diff_gt_lut_tolerance",),
    "front_points_rule": ("endpoints_and_budget_point", "all_front_points", "budget_point_only"),
}
REFILTER_RULES = {
    "axis_rule": ("layout_floorplan_outline",),
    "tie_rule": ("manufacturing_grid_cell_area",),
    "cycle_cap_rule": ("k_max_n3_6",),
}
OPTIONAL_STAGES = ("inner_block_dp", "middle_y_coordinate_descent", "threshold_bisection", "global_sample_budget_fill")


def test_fixture_covers_all_fields(sc):
    assert tuple(sc.human["search"]) == SEARCH_FIELDS
    assert set(sc.human["spice_check"]) == set(SPICE_RULES)
    assert set(sc.human["front_refilter"]) == set(REFILTER_RULES)


def test_results(sc):
    doc = sc.load()
    s = {v.field: v.value for v in doc.search}
    for f in ("wall_clock_budget_s", "front_budget_s", "search_method", "dof_rank_sample_count"):
        assert s[f] == sc.human["search"][f]["value"]
    assert dict(s["optional_stages"]) == sc.human["search"]["optional_stages"]["value"]
    assert {r.field: r.rule for r in doc.spice_check} == {k: v["rule"] for k, v in sc.human["spice_check"].items()}
    assert {r.field: r.rule for r in doc.front_refilter} == {k: v["rule"] for k, v in sc.human["front_refilter"].items()}
    assert [(b.metric, b.op, b.value) for b in doc.objective] == [
        (m, b["op"], b["value"]) for m, b in sorted(sc.human["objective"]["budgets"].items())]


@pytest.mark.parametrize("sec,rules", [("spice_check", SPICE_RULES), ("front_refilter", REFILTER_RULES)])
def test_every_rule_name_in_vocab_accepted(sc, sec, rules):
    for field, names in rules.items():
        for name in names:
            sc.human[sec][field]["rule"] = name
            sc.load()


@pytest.mark.parametrize("sec,field", [(s, f) for s in ("spice_check",) for f in SPICE_RULES]
                         + [("front_refilter", f) for f in REFILTER_RULES])
def test_numeric_in_rule_field(sc, sec, field):
    sc.human[sec][field]["rule"] = 0.05
    sc.reject_only("numeric_in_rule_field", "settings")


@pytest.mark.parametrize("sec,field", [("spice_check", "saturation_rule"), ("front_refilter", "tie_rule")])
def test_numeric_int_in_rule_field(sc, sec, field):
    sc.human[sec][field]["rule"] = 3
    sc.reject_only("numeric_in_rule_field", "settings")


@pytest.mark.parametrize("sec,field,name", [
    ("spice_check", "saturation_rule", "vds_ge_vdsat_plus_50mv"),
    ("spice_check", "acceptance_rule", "record_only"),            # 다른 칸의 어휘
    ("front_refilter", "axis_rule", "off"),
    ("front_refilter", "cycle_cap_rule", "k_max_n3_6 "),
])
def test_rule_name_unknown(sc, sec, field, name):
    sc.human[sec][field]["rule"] = name
    sc.reject_only("rule_name_unknown", "settings")


@pytest.mark.parametrize("sec,field", [("spice_check", "acceptance_rule"), ("front_refilter", "axis_rule"),
                                       ("search", "search_method")])
def test_missing_field(sc, sec, field):
    del sc.human[sec][field]
    sc.reject_only("missing_key", "settings")


def test_no_off_switch(sc):
    """끄는 키는 없다 -- enabled 같은 키는 받지 않는다."""
    sc.human["spice_check"]["enabled"] = {"rule": "record_only", "source": dict(US)}
    d = sc.reject()
    assert sc.rules(d) in (["unknown_key"], ["legacy_name"]) and d["rejected_gates"] == ("settings",)


@pytest.mark.parametrize("m", ["default", "precision"])
def test_search_method_ok(sc, m):
    sc.human["search"]["search_method"]["value"] = m
    sc.load()


@pytest.mark.parametrize("m", ["fast", "Default", ""])
def test_search_method(sc, m):
    sc.human["search"]["search_method"]["value"] = m
    sc.reject_only("search_method", "settings")


def test_all_optional_stages_ok(sc):
    sc.human["search"]["optional_stages"]["value"] = {k: True for k in OPTIONAL_STAGES}
    sc.load()


@pytest.mark.parametrize("name", ["inner_dp", "threshold-bisection", "global_sample_budget"])
def test_optional_stage_unknown(sc, name):
    sc.human["search"]["optional_stages"]["value"] = {name: True}
    sc.reject_only("optional_stage_unknown", "settings")


@pytest.mark.parametrize("field,val", [
    ("optional_stages", {"threshold_bisection": 1}),
    ("optional_stages", ["threshold_bisection"]),
    ("wall_clock_budget_s", 0), ("wall_clock_budget_s", -5), ("wall_clock_budget_s", "300"),
    ("front_budget_s", 0.0),
    ("dof_rank_sample_count", 2.5), ("dof_rank_sample_count", 0), ("dof_rank_sample_count", True),
])
def test_search_value_type(sc, field, val):
    sc.human["search"][field]["value"] = val
    sc.reject_only("type", "settings")


def test_budget_metric_not_objective(sc):
    sc.human["objective"]["budgets"]["gain_ss_db"] = {"op": "<=", "value": 1.0, "source": dict(US)}
    sc.reject_only("budget_metric_not_objective", "settings")


def test_budget_metric_not_in_catalog(sc):
    sc.human["objective"]["budgets"]["area_unknown_m2"] = {"op": "<=", "value": 1.0, "source": dict(US)}
    sc.reject_only("budget_metric_not_objective", "settings")


def test_area_budget_ok(sc):
    sc.human["objective"]["budgets"]["area_layout_m2"] = {"op": "<=", "value": 1e-9, "source": dict(US)}
    assert len(sc.load().objective) == 2


@pytest.mark.parametrize("op", [">=", "<", "=="])
def test_budget_op(sc, op):
    sc.human["objective"]["budgets"]["supply_current_dc"]["op"] = op
    sc.reject_only("op_value", "settings")


@pytest.mark.parametrize("v", [0.0, -1.0, "1e-3", None])
def test_budget_value_type(sc, v):
    sc.human["objective"]["budgets"]["supply_current_dc"]["value"] = v
    sc.reject_only("type", "settings")


def test_empty_budgets_ok(sc):
    sc.human["objective"]["budgets"] = {}
    assert sc.load().objective == ()


def test_minimize_is_circuit_specific(sc):
    sc.human["objective"]["minimize"] = "power"
    sc.reject_only("circuit_specific_key", "settings")


def test_plan_rule_only_in_settings(sc):
    """plan_rule 은 search·spice_check·front_refilter 에서만 -- objective 예산에는 불가."""
    sc.human["objective"]["budgets"]["supply_current_dc"]["source"] = dict(PR)
    sc.reject_only("source_kind_not_allowed_here", "settings")


@pytest.mark.parametrize("sec,field", [("search", "wall_clock_budget_s"), ("spice_check", "tie_rule")])
def test_reference_not_allowed_in_settings(sc, sec, field):
    if field == "tie_rule":
        sec = "front_refilter"
    sc.human[sec][field]["source"] = {"kind": "reference"}
    sc.reject_only("source_kind_not_allowed_here", "settings")


def test_all_settings_hits_collected(sc):
    sc.human["search"]["search_method"]["value"] = "fast"
    sc.human["spice_check"]["saturation_rule"]["rule"] = 0.1
    sc.human["front_refilter"]["axis_rule"]["rule"] = "bbox"
    d = sc.reject()
    assert sorted(sc.rules(d)) == sorted(["search_method", "numeric_in_rule_field", "rule_name_unknown"])
    assert d["rejected_gates"] == ("settings",)
