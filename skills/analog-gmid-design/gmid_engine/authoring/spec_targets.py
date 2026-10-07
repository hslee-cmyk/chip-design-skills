"""보상 목표 `human.compensation_targets` (설계 design_spec_format 1.6, N3.15, F11, 원칙 3).

진입점: `compensation_target_declaration(raw) -> (tuple[(키, TargetDecl | SettlingDecl | PendingMark)] | None,
tuple[SchemaHit])` (키 이름순).

선택 섹션(없으면 `()`). 받는 키 = `TARGET_KEYS` + `settling`. **보상 함수 이름·회로 전용 인자 자리는 없다** -- GB5
일반 규칙(MOD5 `metrics/compensation.py`)이 S1v 극점 노드와 이 목표에서 보상 변수를 유도한다(그런 키는 `key_hits` 가
`circuit_specific_key` 로 거부). 부하 용량은 쓰지 않는다(요소 이름으로 `element_values` 참조).
* 목표(`gbw_target_hz`·`pm_target_deg`): `{"pending": <ID>}` / `{value | value_from_constraint | value_from_file, source}`
  -- 값 자리 규칙은 제약과 같다(`value_and_ref`, `type`, `ref_kind_mismatch`, 참조 안 옛 이름 `legacy_name`). 해석은
  `spec_refs`.
* `settling`: `{"pending": <ID>}` / `{total_s, linear_s, source}` -- 양의 유한 수, `linear_s <= total_s`
  (`settling_order`). 과도 metric 이 레지스트리에 없어 보상 목표로만 쓰이고 합격 판정 대상이 아니다(F11).
"""
from ._spec_fields import REF_KEYS, at, finite_number, is_pending, key_hits, pending_decision, value_slot
from .spec_model import PendingMark, SettlingDecl, TargetDecl
from .spec_sources import REFERENCE, source_declaration_checks
from .topology_model import SchemaHit

SECTION = "compensation_targets"
WHERE = "human.compensation_targets"
TARGET_KEYS = ("gbw_target_hz", "pm_target_deg")
SETTLING_KEY = "settling"


def _target(key, raw, where, hits):
    if is_pending(raw):
        return TargetDecl(key, None, decision=pending_decision(raw))
    if not isinstance(raw, dict):
        hits.append(SchemaHit("type", where, "목표는 객체여야 한다: " + type(raw).__name__))
        return None
    before = len(hits)
    hits.extend(key_hits(raw, ("value", "source") + REF_KEYS, where))
    source, source_hits = source_declaration_checks(raw.get("source"), where, SECTION)
    hits.extend(source_hits)
    value, ref = value_slot(raw, where, None if source is None else source.kind == REFERENCE, hits)
    if len(hits) != before:
        return None
    return TargetDecl(key, value, source, ref=ref)


def _settling(raw, where, hits):
    if is_pending(raw):
        return PendingMark(where, pending_decision(raw))
    if not isinstance(raw, dict):
        hits.append(SchemaHit("type", where, "settling 은 객체여야 한다: " + type(raw).__name__))
        return None
    before = len(hits)
    hits.extend(key_hits(raw, ("total_s", "linear_s", "source"), where))
    source, source_hits = source_declaration_checks(raw.get("source"), where, SECTION)
    hits.extend(source_hits)
    total = raw.get("total_s")
    linear = raw.get("linear_s")
    for name, value in (("total_s", total), ("linear_s", linear)):
        if not finite_number(value) or value <= 0:
            hits.append(SchemaHit("type", at(where, name), name + " 는 양의 유한 수여야 한다: " + repr(value)))
    if len(hits) == before and linear > total:
        hits.append(SchemaHit("settling_order", where, "linear_s 가 total_s 보다 길다: " + repr((linear, total))))
    if len(hits) != before:
        return None
    return SettlingDecl(float(total), float(linear), source)


def compensation_target_declaration(raw):
    if raw is None:
        return (), ()
    if not isinstance(raw, dict):
        return None, (SchemaHit("type", WHERE, "compensation_targets 는 객체여야 한다: " + type(raw).__name__),)
    hits = key_hits(raw, TARGET_KEYS + (SETTLING_KEY,), WHERE)
    out = []
    for key in sorted(raw):
        if key in TARGET_KEYS:
            decl = _target(key, raw[key], at(WHERE, key), hits)
        elif key == SETTLING_KEY:
            decl = _settling(raw[key], at(WHERE, key), hits)
        else:
            continue
        if decl is not None:
            out.append((key, decl))
    if hits:
        return None, tuple(hits)
    return tuple(out), ()
