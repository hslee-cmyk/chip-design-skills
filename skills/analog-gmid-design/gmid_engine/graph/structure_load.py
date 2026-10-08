"""`structure.json` -- ratified 사실 로더 (설계 40 §3.2 보완 2, 계획 N3.3 'library/<name>.structure.json 스키마'와 status 전이 표).

진입점: `load_structure_facts(path, topology_fp, rule_fp) -> StructureFacts`.

파일 형식(계획 N3.3): `{schema_version, topology_hash, rule_hash, facts[{concept, subject, value, status, evidence{rule, nets}, approval_id}]}` 이고
**`ratified` 사실만** 담는다(엔진 유도 결과는 매 실행 재생성하므로 넣지 않는다).
* 파일이 없으면 사실 0(오류 아님 -- ratify 전).
* 형식 위반(키 누락·알 수 없는 키·status 가 ratified 가 아님·빈 문자열 등)은 위반을 모두 모아 `SchemaRejectedError` 한 번(detail gate `structure_json`).
* `topology_hash` 가 현재 S1 지문의 `topology_fp` 와 다르거나 `rule_hash` 가 현재 S1v 규칙 지문과 다르면 **그 사실들을 적용하지 않고** 사실마다
  `structure_fact_stale`(review_needed)로 되돌린다(`ratified` -> `review_needed` 전이).
적용은 `build_s1v` 가 한다: 개념 `drive_kind`(대상 = 넷 이름, 값 = voltage|current)는 구조로 가를 수 없는 구동 종류(열린 항목 J12-b)를 고정한다.
"""
import dataclasses
import json
from pathlib import Path

from gmid_engine.authoring import SchemaHit
from gmid_engine.core import SchemaRejectedError

from .s1v_values import F_STRUCTURE_STALE, SEVERITY_REVIEW, Finding, StructureFact

GATE = "structure_json"
_TOP_KEYS = ("schema_version", "topology_hash", "rule_hash", "facts")
_FACT_KEYS = ("concept", "subject", "value", "status", "evidence", "approval_id")
_STATUS_RATIFIED = "ratified"


@dataclasses.dataclass(frozen=True)
class StructureFacts:
    """`facts` = 적용 가능한 ratified 사실(StructureFact), `findings` = 해시 불일치로 review_needed 로 되돌린 사실 기록."""

    facts: tuple
    findings: tuple


def _hits(raw):
    hits = []
    if not isinstance(raw, dict) or set(raw) != set(_TOP_KEYS):
        return [SchemaHit("structure_keys", GATE, "최상위 키는 정확히 " + repr(_TOP_KEYS) + " 여야 한다")]
    for key in ("schema_version", "topology_hash", "rule_hash"):
        if not isinstance(raw[key], str) or not raw[key]:
            hits.append(SchemaHit("structure_header", GATE + "." + key, key + " 는 비어 있지 않은 문자열이어야 한다"))
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
        evidence = fact["evidence"]
        if not isinstance(evidence, dict) or set(evidence) != {"rule", "nets"} or not isinstance(evidence["nets"], list):
            hits.append(SchemaHit("structure_fact_evidence", where + ".evidence", "evidence 는 {rule, nets[]} 여야 한다"))
    return hits


def load_structure_facts(path, topology_fp, rule_fp):
    target = Path(path)
    if not target.is_file():
        return StructureFacts((), ())
    try:
        raw = json.loads(target.read_text(encoding="utf-8"))
    except ValueError as exc:   # JSONDecodeError·UnicodeDecodeError 는 ValueError 하위 -- 읽을 수 없는 파일도 형식 위반이다
        raise SchemaRejectedError(detail={"gate": GATE, "where": str(target), "hits": (
            SchemaHit("structure_not_json", GATE, "JSON 으로 읽을 수 없다: " + str(exc)),)}) from exc
    hits = _hits(raw)
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
