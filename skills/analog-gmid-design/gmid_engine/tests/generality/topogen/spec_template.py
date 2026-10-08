"""합성 회로용 사이징 spec JSON(dict) -- authoring SPEC_CONTRACT 1절 형식의 최소 선언.

- 수동소자·이상원 값은 topology 의 옛 값 필드를 그대로 옮긴다(SPEC_CONTRACT 2절 `element_value_conflict`: 다른 값이면 거부되므로
  같은 값). 값 키는 2절 `element_value_key` 표(capacitor -> value_farad, resistor -> value_ohm, current_source -> value_dc_amp,
  voltage_source -> value_dc_v), topology 쪽 키는 authoring CONTRACT 3.6·3.7(value_ohm, value_farad, value_amp, value_volt).
- 입력 DC = mode engine(엔진이 W4 창에서 고른다), feedback = [](β = 1), 노드 목표·영역 = 미선언({}), 예산 미선언.
- constraints = (metric, op, value) 목록, view 는 적지 않는다(유도 뷰, SPEC_CONTRACT 3절). 값은 test 가 정한 입력이다.
- 출처 문구는 test fixture 표시(kind user_spec / plan_rule, 1절 출처 표).
엔진을 import 하지 않는 순수 dict 조작이다(지문 `topology_fp` 는 호출자가 준다).
"""
from __future__ import annotations

SCHEMA_VERSION = "5"
FIXTURE_SOURCE = {"kind": "user_spec", "record": "generality test fixture (synthetic circuit)", "decided": "2026-10-08"}
SPEC_VALUE_KEY = (("capacitor", "value_farad"), ("resistor", "value_ohm"), ("current_source", "value_dc_amp"),
                  ("voltage_source", "value_dc_v"))
TOPOLOGY_VALUE_KEYS = ("value_ohm", "value_farad", "value_amp", "value_volt")
TWO_TERMINAL_LISTS = ("passive_elements", "ideal_sources")
SEARCH_FIELDS = (("wall_clock_budget_s", 300, "DEC-34"), ("front_budget_s", 60, "DEC-34"),
                 ("search_method", "default", "DEC-73"), ("optional_stages", {}, "DEC-75"),
                 ("dof_rank_sample_count", 10, "N3.7"))
SPICE_RULES = (("acceptance_rule", "free_spec_and_all_saturated"), ("saturation_rule", "vds_ge_vdsat"),
               ("node_compare_rule", "record_only"), ("device_compare_rule", "record_only"),
               ("forced_warn_rule", "forced_device_diff_gt_lut_tolerance"), ("front_points_rule", "all_front_points"))
REFILTER_RULES = (("axis_rule", "layout_floorplan_outline"), ("tie_rule", "manufacturing_grid_cell_area"),
                  ("cycle_cap_rule", "k_max_n3_6"))


def synthetic_spec(doc, topology_fp, supplies_v, constraints=()):
    """topology dict 에 맞는 spec dict. supplies_v = {레일: V}, constraints = ((metric, op, value), ...)."""
    spec_key = dict(SPEC_VALUE_KEY)
    elements = {}
    for key in TWO_TERMINAL_LISTS:
        for e in doc.get(key, []):
            old = [k for k in TOPOLOGY_VALUE_KEYS if k in e]
            if len(old) != 1:
                raise ValueError("synthetic_spec: %s 의 값 필드가 하나가 아니다: %r" % (e["name"], old))
            elements[e["name"]] = {spec_key[e["kind"]]: e[old[0]], "source": dict(FIXTURE_SOURCE)}
    plan = lambda pid: {"kind": "plan_rule", "plan_id": pid}  # noqa: E731
    return {
        "meta": {"schema_version": SCHEMA_VERSION, "circuit": doc["topology_name"], "topology_fp": topology_fp,
                 "origin": "fixture"},
        "human": {
            "supplies_v": {"values": dict(supplies_v), "source": dict(FIXTURE_SOURCE)},
            "input_dc": {"engine": True, "source": dict(FIXTURE_SOURCE)},
            "element_values": elements,
            "feedback": {"elements": [], "source": dict(FIXTURE_SOURCE)},
            "constraints": [{"metric": m, "op": op, "value": v, "source": dict(FIXTURE_SOURCE)} for m, op, v in constraints],
            "node_voltage_targets_v": {},
            "intended_region": {},
            "objective": {"budgets": {}},
            "search": {k: {"value": v, "source": plan(pid)} for k, v, pid in SEARCH_FIELDS},
            "spice_check": {k: {"rule": r, "source": dict(FIXTURE_SOURCE)} for k, r in SPICE_RULES},
            "front_refilter": {k: {"rule": r, "source": dict(FIXTURE_SOURCE)} for k, r in REFILTER_RULES},
        },
    }
