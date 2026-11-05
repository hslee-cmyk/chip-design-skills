"""`structure.json` -- ratified 사실 로더 (설계 40 §3.2 보완 2, 계획 N3.3 'library/<name>.structure.json 스키마'와 status 전이 표).

진입점: `load_structure_facts(path, topology_fp, rule_fp, net_names=()) -> StructureFacts`.

파일 형식(계획 N3.3): `{schema_version, topology_hash, rule_hash, facts[{concept, subject, value, status, evidence{rule, nets}, approval_id}]}` 이고
**`ratified` 사실만** 담는다(엔진 유도 결과는 매 실행 재생성하므로 넣지 않는다).
* 파일이 없으면 사실 0(오류 아님 -- ratify 전).
* 형식 위반은 위반을 모두 모아 `SchemaRejectedError` 한 번(detail gate `structure_json`): 키 누락·알 수 없는 키·빈 문자열, `schema_version` 이 `STRUCTURE_SCHEMA_VERSION` 이
  아님, status 가 ratified 가 아님, **닫힌 어휘 밖 concept**(`CONCEPTS`, 규칙 `structure_concept_unknown`), concept 별 값 범위 위반(규칙 `structure_value_range`:
  `drive_kind` 는 voltage|current, `dc_role` 은 5개 값, `loop_role` 은 `LOOP_ROLES`, `feedforward_cell` 은 `<ff|ff_bias|ff_load>:<탭>-><merge>`, `matching_pair` 는
  이름 둘 이상의 JSON 배열 subject + 값 `branch_symmetric`, `ac_ground_exception` 은 비어 있지 않은 뷰 id, `l_owner` 는 이름 둘 이상의 정렬 JSON 배열 subject(동치류 멤버) +
  비어 있지 않은 소자 이름 값 -- 주인이 멤버인지·동치류가 엔진 유도와 같은지는 소비(`build_s1v`)가 `structure_fact_mismatch`·`structure_fact_orphan` 으로 대조),
  `dependent_member` 는 `l_owner` 와 같은 subject 꼴(관계 멤버 이름 정렬 JSON 배열) + 종속 소자 이름 값 -- 멤버인지·관계가 있는지는 소비(`dc_writer_plan`)가 `structure_fact_mismatch`·`structure_fact_orphan` 정지로 대조), `feedforward_cell` 사실이 있는데 `net_names` 중 하나가
  `->` 를 품어 값이 모호함(규칙 `structure_value_ambiguous`).
* `topology_hash` 가 현재 S1 지문의 `topology_fp` 와 다르거나 `rule_hash` 가 현재 `structure_rule_fp()` 와 다르면 **그 사실들을 적용하지 않고** 사실마다
  `structure_fact_stale`(review_needed)로 되돌린다(`ratified` -> `review_needed` 전이).
적용은 소비 코드가 한다(40 §3.2-3): `dc_role`·`matching_pair` 는 `build_s1`, 나머지(`l_owner` 포함 -- `l_equivalence_classes`)는 `build_s1v` 와 그 아래 파일.
"""
import dataclasses
import json
from pathlib import Path

from gmid_engine.authoring import SchemaHit
from gmid_engine.core import SchemaRejectedError

from .s1_values import ROLE_BIAS, ROLE_DIODE, ROLE_DIODE_COMPOSITE, ROLE_DIODE_COMPOSITE_CASCODE, ROLE_SIGNAL
from .s1v_values import (
    CONCEPT_AC_GROUND_EXCEPTION,
    CONCEPT_DC_ROLE,
    CONCEPT_DEPENDENT_MEMBER,
    CONCEPT_DRIVE_KIND,
    CONCEPT_FEEDFORWARD_CELL,
    CONCEPT_L_OWNER,
    CONCEPT_LOOP_ROLE,
    CONCEPT_MATCHING_PAIR,
    CONCEPT_STAGE_MEMBERS,
    CONCEPTS,
    DRIVE_CURRENT,
    DRIVE_VOLTAGE,
    F_STRUCTURE_STALE,
    FF_ARROW,
    FF_KINDS,
    FF_SEPARATOR,
    LOOP_ROLES,
    MATCH_PAIR_VALUE,
    SEVERITY_REVIEW,
    STRUCTURE_SCHEMA_VERSION,
    Finding,
    StructureFact,
)

GATE = "structure_json"
_TOP_KEYS = ("schema_version", "topology_hash", "rule_hash", "facts")
_FACT_KEYS = ("concept", "subject", "value", "status", "evidence", "approval_id")
_STATUS_RATIFIED = "ratified"


@dataclasses.dataclass(frozen=True)
class StructureFacts:
    """`facts` = 적용 가능한 ratified 사실(StructureFact), `findings` = 해시 불일치로 review_needed 로 되돌린 사실 기록."""

    facts: tuple
    findings: tuple


_DC_ROLES = (ROLE_SIGNAL, ROLE_BIAS, ROLE_DIODE, ROLE_DIODE_COMPOSITE, ROLE_DIODE_COMPOSITE_CASCODE)


def _pair_names(subject):
    try:
        names = json.loads(subject)
    except ValueError:
        return None
    ok = isinstance(names, list) and len(names) > 1 and all(isinstance(n, str) and n for n in names)
    return names if ok and len(set(names)) == len(names) else None


def _value_range_ok(concept, subject, value):
    """concept 별 값 범위(닫힌 어휘). `stage_members` 의 값은 소자 이름 공백 구분(자유 형식, 비어 있지 않음)이다."""
    if concept == CONCEPT_DRIVE_KIND:
        return value in (DRIVE_VOLTAGE, DRIVE_CURRENT)
    if concept == CONCEPT_DC_ROLE:
        return value in _DC_ROLES
    if concept == CONCEPT_LOOP_ROLE:
        return value in LOOP_ROLES
    if concept == CONCEPT_FEEDFORWARD_CELL:
        kind, separator, ends = value.partition(FF_SEPARATOR)
        tap, arrow, merge = ends.partition(FF_ARROW)
        return kind in FF_KINDS and bool(separator) and bool(arrow) and bool(tap) and bool(merge) and FF_ARROW not in merge
    if concept == CONCEPT_MATCHING_PAIR:
        return value == MATCH_PAIR_VALUE and _pair_names(subject) is not None
    if concept in (CONCEPT_L_OWNER, CONCEPT_DEPENDENT_MEMBER):
        names = _pair_names(subject)
        return names is not None and names == sorted(names)
    return concept in (CONCEPT_AC_GROUND_EXCEPTION, CONCEPT_STAGE_MEMBERS)


def _hits(raw, net_names):
    hits = []
    if not isinstance(raw, dict) or set(raw) != set(_TOP_KEYS):
        return [SchemaHit("structure_keys", GATE, "최상위 키는 정확히 " + repr(_TOP_KEYS) + " 여야 한다")]
    for key in ("schema_version", "topology_hash", "rule_hash"):
        if not isinstance(raw[key], str) or not raw[key]:
            hits.append(SchemaHit("structure_header", GATE + "." + key, key + " 는 비어 있지 않은 문자열이어야 한다"))
    if isinstance(raw["schema_version"], str) and raw["schema_version"] and raw["schema_version"] != STRUCTURE_SCHEMA_VERSION:
        hits.append(SchemaHit("structure_schema_version", GATE + ".schema_version",
                              "지원하는 schema_version 은 " + repr(STRUCTURE_SCHEMA_VERSION) + " 뿐이다: " + repr(raw["schema_version"])))
    if not isinstance(raw["facts"], list):
        return hits + [SchemaHit("structure_facts_type", GATE + ".facts", "facts 는 목록이어야 한다")]
    for i, fact in enumerate(raw["facts"]):
        where = GATE + ".facts[" + str(i) + "]"
        if not isinstance(fact, dict) or set(fact) != set(_FACT_KEYS):
            hits.append(SchemaHit("structure_fact_keys", where, "사실 키는 정확히 " + repr(_FACT_KEYS) + " 여야 한다"))
            continue
        for key in ("concept", "subject", "value", "approval_id"):
            if not isinstance(fact[key], str) or not fact[key]:
                hits.append(SchemaHit("structure_fact_value", where + "." + key, key + " 는 비어 있지 않은 문자열이어야 한다"))
        if fact["status"] != _STATUS_RATIFIED:
            hits.append(SchemaHit("structure_fact_status", where + ".status", "파일에는 ratified 사실만 둔다: " + repr(fact["status"])))
        strings = all(isinstance(fact[key], str) and fact[key] for key in ("concept", "subject", "value"))
        if strings and fact["concept"] not in CONCEPTS:
            hits.append(SchemaHit("structure_concept_unknown", where + ".concept",
                                  "알 수 없는 concept " + repr(fact["concept"]) + " (닫힌 어휘 " + repr(CONCEPTS) + ")"))
        elif strings and not _value_range_ok(fact["concept"], fact["subject"], fact["value"]):
            hits.append(SchemaHit("structure_value_range", where + ".value",
                                  fact["concept"] + " 의 값·대상이 어휘 밖이다: " + repr(fact["subject"]) + " -> " + repr(fact["value"])))
        elif strings and fact["concept"] == CONCEPT_FEEDFORWARD_CELL and any(FF_ARROW in net for net in net_names):
            hits.append(SchemaHit("structure_value_ambiguous", where + ".value",
                                  "topology 넷 이름에 " + repr(FF_ARROW) + " 가 있어 feedforward_cell 값을 해석할 수 없다"))
        evidence = fact["evidence"]
        if not isinstance(evidence, dict) or set(evidence) != {"rule", "nets"} or not isinstance(evidence["nets"], list):
            hits.append(SchemaHit("structure_fact_evidence", where + ".evidence", "evidence 는 {rule, nets[]} 여야 한다"))
    return hits


def load_structure_facts(path, topology_fp, rule_fp, net_names=()):
    target = Path(path)
    if not target.is_file():
        return StructureFacts((), ())
    try:
        raw = json.loads(target.read_text(encoding="utf-8"))
    except ValueError as exc:   # JSONDecodeError·UnicodeDecodeError 는 ValueError 하위 -- 읽을 수 없는 파일도 형식 위반이다
        raise SchemaRejectedError(detail={"gate": GATE, "where": str(target), "hits": (
            SchemaHit("structure_not_json", GATE, "JSON 으로 읽을 수 없다: " + str(exc)),)}) from exc
    hits = _hits(raw, tuple(net_names))
    if hits:
        raise SchemaRejectedError(detail={"gate": GATE, "where": str(target), "hits": tuple(hits)})
    facts = tuple(StructureFact(f["concept"], f["subject"], f["value"], f["approval_id"], tuple(f["evidence"]["nets"]))
                  for f in raw["facts"])
    if raw["topology_hash"] != topology_fp or raw["rule_hash"] != rule_fp:
        stale = tuple(Finding(F_STRUCTURE_STALE, SEVERITY_REVIEW, "", (f.subject,),
                              "ratified 사실 " + f.concept + " 이 현재 topology·규칙 지문과 맞지 않아 review_needed 로 되돌렸다(" + f.approval_id + ")",
                              ("N3.3",)) for f in facts)
        return StructureFacts((), stale)
    return StructureFacts(facts, ())
