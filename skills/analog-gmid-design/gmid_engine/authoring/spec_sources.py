"""출처 객체 `source` 검사 (설계 design_spec_format 1.4, 원칙 1 '값마다 출처').

진입점: `source_declaration_checks(raw, where, section) -> (SpecSource | None, tuple[SchemaHit])`.

* `raw` 가 없으면(None) `source_missing`. 객체가 아니면 `type`.
* `kind` ∈ `SOURCE_KINDS`. 논문 계열 kind(`PAPER_KINDS`)는 `paper_source_not_adopted`(논문 값을 확정값으로 몰래 쓰는
  길을 막는다 -- 채택된 논문 값은 `user_spec` + `origin: paper` + `record` 로만 들어온다). 옛 kind `pending_7a` 는
  `legacy_name`(F2 개명). 그 밖은 `source_kind_unknown`.
* 섹션별 허용 kind(`ALLOWED_KINDS`): `plan_rule` 은 설정 섹션(search·spice_check·front_refilter)에만, `pending_spice`
  는 constraints 에만, `reference` 는 constraints·compensation_targets 에만. 밖이면 `source_kind_not_allowed_here`.
* 부필드: `user_spec` -- `record`(비어 있지 않은 문자열)·`decided`(YYYY-MM-DD) 필수(`source_record_missing`),
  `origin` 은 있으면 `ORIGINS` 원소(`source_origin`), `origin` 이 `CITED_ORIGINS` 면 `citation` 필수
  (`citation_missing`). `pending_spice` -- `record` 필수. `plan_rule` -- `plan_id` 필수(`source_record_missing`).
  `reference` -- 부필드 없음. 받는 키 밖은 `_spec_fields.key_hits`.
"""
import re
from types import MappingProxyType

from ._spec_fields import at, key_hits
from .spec_model import SpecSource
from .topology_model import SchemaHit

USER_SPEC = "user_spec"
PENDING_SPICE = "pending_spice"
REFERENCE = "reference"
PLAN_RULE = "plan_rule"
SOURCE_KINDS = (USER_SPEC, PENDING_SPICE, REFERENCE, PLAN_RULE)
PAPER_KINDS = ("paper", "paper_reference", "literature", "drawing")
LEGACY_KINDS = ("pending_7a",)
ORIGINS = ("user", "paper", "drawing", "lecture", "legacy_harness")
CITED_ORIGINS = ("paper", "drawing", "lecture")
SOURCE_KEYS = ("kind", "record", "decided", "origin", "citation", "plan_id")
DATE_PATTERN = re.compile(r"\d{4}-\d{2}-\d{2}")

ALLOWED_KINDS = MappingProxyType({
    "supplies_v": (USER_SPEC,),
    "input_dc": (USER_SPEC,),
    "element_values": (USER_SPEC,),
    "feedback": (USER_SPEC,),
    "constraints": (USER_SPEC, PENDING_SPICE, REFERENCE),
    "compensation_targets": (USER_SPEC, REFERENCE),
    "node_voltage_targets_v": (USER_SPEC,),
    "intended_region": (USER_SPEC,),
    "objective": (USER_SPEC,),
    "search": (USER_SPEC, PLAN_RULE),
    "search_untie": (USER_SPEC,),
    "spice_check": (USER_SPEC, PLAN_RULE),
    "front_refilter": (USER_SPEC, PLAN_RULE),
})


def _nonempty_str(value):
    return isinstance(value, str) and bool(value.strip())


def source_declaration_checks(raw, where, section):
    """`section` 은 `ALLOWED_KINDS` 의 키(human 섹션 이름)."""
    place = at(where, "source")
    if raw is None:
        return None, (SchemaHit("source_missing", place, "출처 객체 source 가 없다 -- 모든 선언에 필수(U-35, 설계 1.4)"),)
    if not isinstance(raw, dict):
        return None, (SchemaHit("type", place, "source 는 객체여야 한다: " + type(raw).__name__),)
    hits = key_hits(raw, SOURCE_KEYS, place)
    kind = raw.get("kind")
    if kind in PAPER_KINDS:
        hits.append(SchemaHit("paper_source_not_adopted", at(place, "kind"),
                              "출처 kind " + repr(kind) + " 는 받지 않는다 -- 채택된 논문·도면 값은 kind user_spec + origin + "
                              "record(사용자 채택 기록)로만 들어온다(원칙 1, WP-04)"))
        return None, tuple(hits)
    if kind in LEGACY_KINDS:
        hits.append(SchemaHit("legacy_name", at(place, "kind"), "옛 출처 kind " + repr(kind) + " -- pending_spice 로 쓴다(F2)"))
        return None, tuple(hits)
    if kind not in SOURCE_KINDS:
        hits.append(SchemaHit("source_kind_unknown", at(place, "kind"),
                              "출처 kind 는 " + repr(SOURCE_KINDS) + " 중 하나여야 한다: " + repr(kind)))
        return None, tuple(hits)
    if kind not in ALLOWED_KINDS[section]:
        hits.append(SchemaHit("source_kind_not_allowed_here", at(place, "kind"),
                              "섹션 " + repr(section) + " 에는 출처 kind " + repr(ALLOWED_KINDS[section])
                              + " 만 쓴다: " + repr(kind)))
    origin = raw.get("origin")
    if kind == USER_SPEC:
        if not _nonempty_str(raw.get("record")):
            hits.append(SchemaHit("source_record_missing", at(place, "record"),
                                  "user_spec 은 사용자 결정 기록 위치·원문 record 가 필수다"))
        decided = raw.get("decided")
        if not isinstance(decided, str) or DATE_PATTERN.fullmatch(decided) is None:
            hits.append(SchemaHit("source_record_missing", at(place, "decided"),
                                  "user_spec 은 결정 날짜 decided(YYYY-MM-DD)가 필수다: " + repr(decided)))
        if origin is not None and origin not in ORIGINS:
            hits.append(SchemaHit("source_origin", at(place, "origin"),
                                  "origin 은 " + repr(ORIGINS) + " 중 하나여야 한다: " + repr(origin)))
        if origin in CITED_ORIGINS and not _nonempty_str(raw.get("citation")):
            hits.append(SchemaHit("citation_missing", at(place, "citation"),
                                  "origin " + repr(origin) + " 이면 citation(문헌·도면 위치)이 필수다"))
    elif kind == PENDING_SPICE:
        if not _nonempty_str(raw.get("record")):
            hits.append(SchemaHit("source_record_missing", at(place, "record"), "pending_spice 는 record 가 필수다"))
    elif kind == PLAN_RULE:
        if not _nonempty_str(raw.get("plan_id")):
            hits.append(SchemaHit("source_record_missing", at(place, "plan_id"),
                                  "plan_rule 은 계획서 규칙 ID plan_id 가 필수다"))
    if hits:
        return None, tuple(hits)
    return SpecSource(kind, origin, raw.get("record"), raw.get("citation"), raw.get("decided"),
                      raw.get("plan_id")), ()
