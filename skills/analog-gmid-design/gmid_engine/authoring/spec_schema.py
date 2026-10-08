"""spec 최상위 스키마 -- meta·human 닫힌 키 어휘, 스키마 버전, 결정 대기 표지 수집 (설계 design_spec_format 1.2·1.3·1.5·1.6).

진입점: `check_spec_schema(doc) -> (tuple[SchemaHit], tuple[PendingMark])`.

* 최상위 값은 객체(`top_not_object`, 이 경우 나머지 검사 없음). 받는 키 = `TOP_KEYS` + `_` 주석. 둘 다 필수(`missing_key`).
* `meta`: 받는 키 = `META_KEYS`(전부 필수). `schema_version` = `SPEC_SCHEMA_VERSION`(`schema_version`), `circuit`·
  `topology_fp` 는 비어 있지 않은 문자열(`type`), `origin` ∈ `META_ORIGINS`(`type`). topology 대조는 `spec_meta`.
* `human`: 받는 키 = `HUMAN_KEYS`, 그중 `HUMAN_REQUIRED` 필수. 키 판정은 `_spec_fields.key_hits`(옛 이름·회로 전용 키
  구분). 섹션 안 모양은 섹션 파일들이 본다.
* 결정 대기 표지: 문서 전체를 돌며 `{"pending": <ID>}` 를 모두 모으고(경로, ID), ID 가 `PENDING_ID_PATTERN`(결정
  목록 형식 `SP-n`·`AC-n`·`CI-n`·`PA-n`·`ET-n`·`U-nn`, 그리고 결정 주체가 설계 단위인 `MODn`)이 아니면
  `pending_id_format`. 표지가 놓여도 되는 자리인지는 섹션 파일이 판정한다(받지 않는 자리면 그 파일의 `type`).
"""
import re

from ._spec_fields import COMMENT_PREFIX, PENDING_KEY, at, is_pending, key_hits, pending_decision
from .spec_model import PendingMark
from .topology_model import SchemaHit

SPEC_SCHEMA_VERSION = "5"
TOP_KEYS = ("meta", "human")
META_KEYS = ("schema_version", "circuit", "topology_fp", "origin")
META_ORIGINS = ("canonical", "fixture")
HUMAN_REQUIRED = ("supplies_v", "input_dc", "element_values", "feedback", "constraints", "node_voltage_targets_v",
                  "intended_region", "objective", "search", "spice_check", "front_refilter")
# [U5 2026-10-08, 설계 40 §3.1] 선택 섹션 3개를 더했다: 블록 gain 고정 `gain_budget_db_override`, 출력 구동 `driving_spec`,
# 구조 계수 예산 `structure_count_budget`. 모양 검사는 각 선언 파일(스키마 버전은 그대로 -- 선택 키 추가라 기존 spec 이 유효하다).
HUMAN_OPTIONAL = ("pending_constraints", "compensation_targets", "gain_budget_db_override", "driving_spec",
                  "structure_count_budget")
HUMAN_KEYS = HUMAN_REQUIRED + HUMAN_OPTIONAL
PENDING_ID_PATTERN = re.compile(r"(?:SP|AC|CI|PA|ET)-[1-9][0-9]*|U-[0-9]{2}|MOD[1-9][0-9]*")


def _collect_pending(value, where, marks, hits):
    if is_pending(value):
        decision = pending_decision(value)
        if not isinstance(decision, str) or PENDING_ID_PATTERN.fullmatch(decision) is None:
            hits.append(SchemaHit("pending_id_format", at(where, PENDING_KEY),
                                  "결정 대기 ID 형식 밖: " + repr(decision) + " (SP-n·AC-n·CI-n·PA-n·ET-n·U-nn·MODn)"))
        else:
            marks.append(PendingMark(where, decision))
        return
    if isinstance(value, dict):
        for key in value:
            if not key.startswith(COMMENT_PREFIX):
                _collect_pending(value[key], at(where, key), marks, hits)
    elif isinstance(value, list):
        for index, item in enumerate(value):
            _collect_pending(item, at(where, index), marks, hits)


def check_spec_schema(doc):
    if not isinstance(doc, dict):
        return (SchemaHit("top_not_object", "$", "spec 최상위 값이 JSON 객체가 아니다: " + type(doc).__name__),), ()
    hits = key_hits(doc, TOP_KEYS, "")
    for key in TOP_KEYS:
        if key not in doc:
            hits.append(SchemaHit("missing_key", key, "필수 최상위 키 " + repr(key) + " 가 없다"))
        elif not isinstance(doc[key], dict):
            hits.append(SchemaHit("type", key, key + " 는 객체여야 한다: " + type(doc[key]).__name__))
    meta = doc.get("meta")
    if isinstance(meta, dict):
        hits.extend(key_hits(meta, META_KEYS, "meta"))
        for key in META_KEYS:
            if key not in meta:
                hits.append(SchemaHit("missing_key", at("meta", key), "필수 meta 키 " + repr(key) + " 가 없다"))
        if "schema_version" in meta and meta["schema_version"] != SPEC_SCHEMA_VERSION:
            hits.append(SchemaHit("schema_version", "meta.schema_version", "schema_version "
                                  + repr(meta["schema_version"]) + " -- " + repr(SPEC_SCHEMA_VERSION) + " 만 받는다"))
        for key in ("circuit", "topology_fp"):
            if key in meta and (not isinstance(meta[key], str) or not meta[key]):
                hits.append(SchemaHit("type", at("meta", key), key + " 는 비어 있지 않은 문자열이어야 한다: "
                                      + repr(meta[key])))
        if "origin" in meta and meta["origin"] not in META_ORIGINS:
            hits.append(SchemaHit("type", "meta.origin", "origin 은 " + repr(META_ORIGINS) + " 중 하나여야 한다: "
                                  + repr(meta["origin"])))
    human = doc.get("human")
    marks = []
    if isinstance(human, dict):
        hits.extend(key_hits(human, HUMAN_KEYS, "human"))
        for key in HUMAN_REQUIRED:
            if key not in human:
                hits.append(SchemaHit("missing_key", at("human", key), "필수 human 키 " + repr(key)
                                      + " 가 없다(값이 미정이면 {\"pending\": <결정 ID>}, 없음이면 빈 값으로 명시)"))
        _collect_pending(human, "human", marks, hits)
    return tuple(hits), tuple(marks)
