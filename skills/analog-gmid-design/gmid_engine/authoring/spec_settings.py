"""설정 섹션 `human.objective`·`search`·`spice_check`·`front_refilter` (설계 design_spec_format 1.6, DEC-34·73·75·77~80,
UD 8번·12번, F8).

진입점: `settings_declaration(human, metric_catalog) -> (sections | None, tuple[SchemaHit])`,
`sections` = (objective, search, spice_check, front_refilter).

* `objective` = `{"budgets": {"pending": <ID>} | {<목적 metric>: {"op": "<=", "value", "source"}}}`. 최소화 대상을 고르는
  키는 없다(축은 (전력, 면적) 고정, DEC-77 -- `minimize` 는 `circuit_specific_key`). 목적 metric 은 이름표에서
  `objective_axis` 가 있는 것만(`budget_metric_not_objective`), op 는 `<=`(`op_value`), 값은 양의 유한 수(`type`).
  빈 `budgets` = 예산 미선언(front 제시 후 정지).
* `search`: `SEARCH_FIELDS` 전부 필수(`missing_key`). 각 칸 `{"pending": <ID>}` 또는 `{"value", "source"}`.
  `wall_clock_budget_s`·`front_budget_s` = 양의 유한 수, `dof_rank_sample_count` = 양의 정수(`type`),
  `search_method` ∈ `SEARCH_METHODS`(`search_method`), `optional_stages` = {화이트리스트 이름: bool}
  (`optional_stage_unknown`, 값 bool 아님 `type`). 화이트리스트 = DEC-75 의 네 기능(이름은 이 파일이 정한 snake_case).
* `spice_check`·`front_refilter`: 필드 전부 필수, 각 칸 `{"pending": <ID>}` 또는 `{"rule": <규칙 이름>, "source"}`.
  규칙 이름은 닫힌 어휘(`SPICE_RULES`·`REFILTER_RULES`, 규칙 정의는 엔진·오라클 코드 한 곳) -- 수가 오면
  `numeric_in_rule_field`(상수 금지, WP-03), 어휘 밖 문자열은 `rule_name_unknown`. **끄는 키는 없다**.
출처 kind 는 설정 섹션만 `plan_rule` 을 받는다(`spec_sources`).
"""
from types import MappingProxyType

from ._spec_fields import COMMENT_PREFIX, at, finite_number, is_pending, key_hits, pending_decision
from .spec_model import ObjectiveBudget, PendingMark, RuleChoice, SettingValue
from .spec_sources import source_declaration_checks
from .topology_model import SchemaHit

SEARCH_FIELDS = ("wall_clock_budget_s", "front_budget_s", "search_method", "optional_stages", "dof_rank_sample_count")
SEARCH_METHODS = ("default", "precision")
OPTIONAL_STAGES = ("inner_block_dp", "middle_y_coordinate_descent", "threshold_bisection", "global_sample_budget_fill")
SPICE_RULES = MappingProxyType({
    "acceptance_rule": ("free_spec_and_all_saturated",),
    "saturation_rule": ("vds_ge_vdsat", "vds_ge_vdsat_plus_tol_v"),
    "node_compare_rule": ("record_only",),
    "device_compare_rule": ("record_only",),
    "forced_warn_rule": ("forced_device_diff_gt_lut_tolerance",),
    "front_points_rule": ("endpoints_and_budget_point", "all_front_points", "budget_point_only"),
})
REFILTER_RULES = MappingProxyType({
    "axis_rule": ("layout_floorplan_outline",),
    "tie_rule": ("manufacturing_grid_cell_area",),
    "cycle_cap_rule": ("k_max_n3_6",),
})
BUDGET_OP = "<="


def _section(human, name, hits):
    raw = human.get(name)
    where = at("human", name)
    if name not in human:
        return None, where  # 필수 키 누락은 spec_schema 의 missing_key 하나로 보고한다(두 번 세지 않음)
    if not isinstance(raw, dict):
        hits.append(SchemaHit("type", where, name + " 는 객체여야 한다: " + type(raw).__name__))
        return None, where
    return raw, where


def _objective(human, catalog, hits):
    raw, where = _section(human, "objective", hits)
    if raw is None:
        return None
    hits.extend(key_hits(raw, ("budgets",), where))
    budgets = raw.get("budgets")
    place = at(where, "budgets")
    if is_pending(budgets):
        return PendingMark(place, pending_decision(budgets))
    if not isinstance(budgets, dict):
        hits.append(SchemaHit("type", place, "budgets 는 객체(목적 metric -> 예산)여야 한다(미선언이면 {})"))
        return None
    out = []
    for metric in sorted(k for k in budgets if not k.startswith(COMMENT_PREFIX)):
        entry = budgets[metric]
        spot = at(place, metric)
        if not isinstance(entry, dict):
            hits.append(SchemaHit("type", spot, "예산은 {op, value, source} 객체여야 한다"))
            continue
        before = len(hits)
        hits.extend(key_hits(entry, ("op", "value", "source"), spot))
        source, source_hits = source_declaration_checks(entry.get("source"), spot, "objective")
        hits.extend(source_hits)
        signature = catalog.get(metric)
        if signature is None or signature.objective_axis is None:
            hits.append(SchemaHit("budget_metric_not_objective", spot,
                                  "예산 metric " + repr(metric) + " 이 이름표의 목적 축 metric 이 아니다(DEC-77)"))
        if entry.get("op") != BUDGET_OP:
            hits.append(SchemaHit("op_value", at(spot, "op"), "예산 op 는 " + repr(BUDGET_OP) + " 만: " + repr(entry.get("op"))))
        if not finite_number(entry.get("value")) or entry["value"] <= 0:
            hits.append(SchemaHit("type", at(spot, "value"), "예산 값은 양의 유한 수여야 한다"))
        if len(hits) == before:
            out.append(ObjectiveBudget(metric, BUDGET_OP, float(entry["value"]), source))
    return tuple(out)


def _search_value(field, raw, where, hits):
    if field == "search_method":
        if raw not in SEARCH_METHODS:
            hits.append(SchemaHit("search_method", where, "search_method 는 " + repr(SEARCH_METHODS) + " 중 하나: " + repr(raw)))
        return raw
    if field == "optional_stages":
        if not isinstance(raw, dict):
            hits.append(SchemaHit("type", where, "optional_stages 는 객체(기능 -> bool)여야 한다"))
            return None
        for name in raw:
            if name not in OPTIONAL_STAGES:
                hits.append(SchemaHit("optional_stage_unknown", at(where, name),
                                      "켤 수 있는 기능은 DEC-75 화이트리스트 " + repr(OPTIONAL_STAGES) + " 뿐: " + repr(name)))
            elif not isinstance(raw[name], bool):
                hits.append(SchemaHit("type", at(where, name), "optional_stages 값은 bool"))
        return tuple(sorted(raw.items()))
    if field == "dof_rank_sample_count":
        if isinstance(raw, bool) or not isinstance(raw, int) or raw < 1:
            hits.append(SchemaHit("type", where, "dof_rank_sample_count 는 양의 정수: " + repr(raw)))
        return raw
    if not finite_number(raw) or raw <= 0:
        hits.append(SchemaHit("type", where, field + " 는 양의 유한 수: " + repr(raw)))
        return None
    return float(raw)


def _search(human, hits):
    raw, where = _section(human, "search", hits)
    if raw is None:
        return None
    hits.extend(key_hits(raw, SEARCH_FIELDS, where))
    out = []
    for field in SEARCH_FIELDS:
        spot = at(where, field)
        if field not in raw:
            hits.append(SchemaHit("missing_key", spot, "search." + field + " 가 없다(미정이면 pending)"))
            continue
        entry = raw[field]
        if is_pending(entry):
            out.append(SettingValue(field, None, decision=pending_decision(entry)))
            continue
        if not isinstance(entry, dict):
            hits.append(SchemaHit("type", spot, "설정 칸은 {value, source} 객체여야 한다"))
            continue
        hits.extend(key_hits(entry, ("value", "source"), spot))
        source, source_hits = source_declaration_checks(entry.get("source"), spot, "search")
        hits.extend(source_hits)
        out.append(SettingValue(field, _search_value(field, entry.get("value"), at(spot, "value"), hits), source))
    return tuple(out)


def _rules(human, name, vocabulary, hits):
    raw, where = _section(human, name, hits)
    if raw is None:
        return None
    hits.extend(key_hits(raw, tuple(vocabulary), where))
    out = []
    for field in vocabulary:
        spot = at(where, field)
        if field not in raw:
            hits.append(SchemaHit("missing_key", spot, name + "." + field + " 가 없다(미정이면 pending)"))
            continue
        entry = raw[field]
        if is_pending(entry):
            out.append(RuleChoice(field, None, decision=pending_decision(entry)))
            continue
        if not isinstance(entry, dict):
            hits.append(SchemaHit("type", spot, "규칙 칸은 {rule, source} 객체여야 한다"))
            continue
        hits.extend(key_hits(entry, ("rule", "source"), spot))
        source, source_hits = source_declaration_checks(entry.get("source"), spot, name)
        hits.extend(source_hits)
        rule = entry.get("rule")
        if isinstance(rule, (int, float)):
            hits.append(SchemaHit("numeric_in_rule_field", at(spot, "rule"),
                                  "규칙 칸에 수 " + repr(rule) + " -- 숫자가 아니라 규칙 이름만 고른다(WP-03): "
                                  + repr(vocabulary[field])))
        elif rule not in vocabulary[field]:
            hits.append(SchemaHit("rule_name_unknown", at(spot, "rule"),
                                  field + " 규칙은 " + repr(vocabulary[field]) + " 중 하나: " + repr(rule)))
        out.append(RuleChoice(field, rule, source))
    return tuple(out)


def settings_declaration(human, metric_catalog):
    hits = []
    sections = (_objective(human, metric_catalog, hits), _search(human, hits),
                _rules(human, "spice_check", SPICE_RULES, hits), _rules(human, "front_refilter", REFILTER_RULES, hits))
    if hits:
        return None, tuple(hits)
    return sections, ()
