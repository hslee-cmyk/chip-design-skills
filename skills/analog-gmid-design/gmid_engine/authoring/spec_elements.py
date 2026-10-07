"""요소 값 `human.element_values` 와 되먹임 선언 `human.feedback` (설계 design_spec_format 1.6, F4·F5·F12).

진입점: `element_value_declaration(raw_values, raw_feedback, topology)
         -> (tuple[ElementValue] | None, feedback | None, tuple[SchemaHit])`.

요소 값의 정본은 spec 이다(F5 확정 2026-10-07 -- topology 는 connectivity 만). topology 수동소자·이상원 **전부**를
선언해야 한다(F4, 생략 = 조용한 기본값이라 거부). 항목 모양(요소 이름 -> 하나):
`{"pending": <ID>}` / `{<값 키>: <수>, "source"}` / `{"engine": true, "source"}`(엔진이 계산하는 값 -- 사용자 결정 기록이
출처). 위반:
* `type` -- 객체가 아니거나, 값 키·engine 이 정확히 하나가 아니거나, 값이 유한 수가 아니거나, engine 이 true 아님.
* `element_value_key` -- 값 키가 요소 kind 와 맞지 않는다(`VALUE_KEY_BY_KIND`; 표 밖 kind 는 값 선언 불가 -- engine·
  pending 만).
* `element_value` -- 수동소자 값(`POSITIVE_KEYS`)이 0 이하.
* `element_unknown` / `element_undeclared` -- spec 이름이 topology 원소 밖 / topology 원소가 spec 에 없다.
* `element_value_conflict` -- topology 원소에 값 필드가 남아 있는데(F5 이관 전 옛 위치) spec 선언과 다르다(spec 이
  engine·pending 이거나 수가 다름 -- 수동소자·이상원 모두). 같은 값이 두 곳에 있는 동안 조용히 갈리지 않게 막는다(topology 값 필드 삭제는 topology
  정리 단계 몫).
`feedback` 모양: `{"pending": <ID>}` / `{"elements": [<수동소자 이름>…], "source"}`(빈 list = 되먹임 수동소자 없음 =
β=1 루프, UD 9번). `type`(형식·중복), `feedback_element_unknown`(topology 수동소자 밖). 루프 절단 위치(7a design 2.2 L2):
각 소자의 두 단자 중 입력 포트 넷에 물린 단자가 정확히 1개여야 한다 -- 0개 `feedback_element_not_on_input`(오라클 C14 막힘과
같은 조건), 2개 `feedback_cut_ambiguous`(두 입력 넷 사이 소자 -- 어느 쪽을 끊을지 정해지지 않는다).
`topology` 가 None 이면(meta 지문 불일치) 이름·kind 교차 검사를 하지 않는다(값 형식 검사만).
결과: 요소 값은 이름순, feedback 은 이름순 tuple 또는 `PendingMark`.
"""
from types import MappingProxyType

from ._feedback_cuts import input_terminal_nets
from ._spec_fields import COMMENT_PREFIX, at, finite_number, is_pending, key_hits, pending_decision
from .spec_model import ElementValue, PendingMark
from .spec_sources import source_declaration_checks
from .topology_model import SchemaHit

WHERE = "human.element_values"
FEEDBACK_WHERE = "human.feedback"
ENGINE_KEY = "engine"
VALUE_KEY_BY_KIND = MappingProxyType({
    "capacitor": "value_farad",
    "resistor": "value_ohm",
    "current_source": "value_dc_amp",
    "voltage_source": "value_dc_v",
})
VALUE_KEYS = tuple(sorted(VALUE_KEY_BY_KIND.values()))
POSITIVE_KEYS = ("value_farad", "value_ohm")


def _conflict(name, result, where, topo_values):
    # topology 에 옛 값이 남아 있으면 spec 은 같은 수여야 한다(engine·pending 도 어긋남 -- 값을 topology 에서 채우지 않는다).
    if topo_values is None or topo_values.get(name) is None:
        return []
    old = topo_values[name]
    if result is not None and result.mode == "value" and result.value == old:
        return []
    mode = result.mode if result is not None else "invalid"
    return [SchemaHit("element_value_conflict", where, "topology 원소 " + repr(name) + " 에 값 " + repr(old)
                      + " 이 남아 있는데 spec 선언(" + mode + ")과 다르다 -- 값 정본은 spec(F5)", (name,))]


def _element(name, entry, where, kinds, topo_values):
    if is_pending(entry):
        result = ElementValue(name, "pending", decision=pending_decision(entry))
        return result, _conflict(name, result, where, topo_values)
    if not isinstance(entry, dict):
        return None, [SchemaHit("type", where, "요소 값 선언은 객체여야 한다: " + type(entry).__name__, (name,))]
    hits = key_hits(entry, VALUE_KEYS + (ENGINE_KEY, "source"), where, (name,))
    source, source_hits = source_declaration_checks(entry.get("source"), where, "element_values")
    hits.extend(source_hits)
    present = tuple(k for k in VALUE_KEYS + (ENGINE_KEY,) if k in entry)
    if len(present) != 1:
        hits.append(SchemaHit("type", where, "값 키 하나 또는 engine 하나만 쓴다: " + repr(present), (name,)))
        return None, hits
    key = present[0]
    value = entry[key]
    kind = kinds.get(name) if kinds is not None else None
    if key == ENGINE_KEY:
        if value is not True:
            hits.append(SchemaHit("type", at(where, key), "engine 은 true 만 받는다: " + repr(value), (name,)))
        result = ElementValue(name, "engine", source=source)
    else:
        if not finite_number(value):
            hits.append(SchemaHit("type", at(where, key), "요소 값은 유한 수여야 한다: " + repr(value), (name,)))
        elif key in POSITIVE_KEYS and value <= 0:
            hits.append(SchemaHit("element_value", at(where, key), "수동소자 값은 양수여야 한다: " + repr(value), (name,)))
        if kinds is not None and name in kinds and VALUE_KEY_BY_KIND.get(kind) != key:
            hits.append(SchemaHit("element_value_key", at(where, key), "요소 " + repr(name) + " (kind " + repr(kind)
                                  + ") 의 값 키는 " + repr(VALUE_KEY_BY_KIND.get(kind)) + " 여야 한다: " + repr(key),
                                  (name,)))
        result = ElementValue(name, "value", key, float(value) if finite_number(value) else None, source)
    hits.extend(_conflict(name, result, where, topo_values))
    return result, hits


def _cut_hits(names, topology):
    hits = []
    where = at(FEEDBACK_WHERE, "elements")
    for index, name in enumerate(names):
        nets = input_terminal_nets(name, topology)
        if nets is None:
            continue
        if not nets:
            hits.append(SchemaHit("feedback_element_not_on_input", at(where, index), "되먹임 요소 " + repr(name)
                                  + " 의 단자가 입력 포트 넷에 물려 있지 않다 -- 루프를 끊을 단자가 없다(7a design 2.2 L2)",
                                  (name,)))
        elif len(nets) > 1:
            hits.append(SchemaHit("feedback_cut_ambiguous", at(where, index), "되먹임 요소 " + repr(name)
                                  + " 의 두 단자가 모두 입력 포트 넷 " + repr(nets) + " 에 물려 있다 -- 끊을 단자가 정해지지 않는다",
                                  (name,) + nets))
    return hits


def _feedback(raw, passive_names, topology):
    if is_pending(raw):
        return PendingMark(FEEDBACK_WHERE, pending_decision(raw)), []
    if not isinstance(raw, dict):
        return None, [SchemaHit("type", FEEDBACK_WHERE, "feedback 은 객체여야 한다: " + type(raw).__name__)]
    hits = key_hits(raw, ("elements", "source"), FEEDBACK_WHERE)
    _source, source_hits = source_declaration_checks(raw.get("source"), FEEDBACK_WHERE, "feedback")
    hits.extend(source_hits)
    names = raw.get("elements")
    if not isinstance(names, list) or not all(isinstance(n, str) and n for n in names) or len(set(names)) != len(names):
        hits.append(SchemaHit("type", at(FEEDBACK_WHERE, "elements"),
                              "feedback.elements 는 서로 다른 수동소자 이름 list 여야 한다: " + repr(names)))
        return None, hits
    if passive_names is not None:
        for index, name in enumerate(names):
            if name not in passive_names:
                hits.append(SchemaHit("feedback_element_unknown", at(at(FEEDBACK_WHERE, "elements"), index),
                                      "되먹임 요소 " + repr(name) + " 가 topology 수동소자에 없다", (name,)))
        hits.extend(_cut_hits(names, topology))
    return tuple(sorted(names)), hits


def element_value_declaration(raw_values, raw_feedback, topology):
    hits = []
    kinds = topo_values = passive_names = None
    if topology is not None:
        members = topology.passives + topology.sources
        kinds = {x.name: x.kind for x in members}
        topo_values = {x.name: x.value for x in members}
        passive_names = frozenset(x.name for x in topology.passives)
    elements = None
    if not isinstance(raw_values, dict):
        hits.append(SchemaHit("type", WHERE, "element_values 는 객체(요소 이름 -> 선언)여야 한다: "
                              + type(raw_values).__name__))
    else:
        declared = []
        for name in raw_values:
            if name.startswith(COMMENT_PREFIX):
                continue
            result, found = _element(name, raw_values[name], at(WHERE, name), kinds, topo_values)
            hits.extend(found)
            if result is not None:
                declared.append(result)
            if kinds is not None and name not in kinds:
                hits.append(SchemaHit("element_unknown", at(WHERE, name),
                                      "요소 " + repr(name) + " 가 topology 수동소자·이상원에 없다", (name,)))
        if kinds is not None:
            for name in sorted(set(kinds) - set(raw_values)):
                hits.append(SchemaHit("element_undeclared", WHERE, "topology 요소 " + repr(name)
                                      + " 의 값 선언이 없다(값 / engine / pending 중 하나로 적는다, F4)", (name,)))
        elements = tuple(sorted(declared, key=lambda x: x.name))
    feedback, found = _feedback(raw_feedback, passive_names, topology)
    hits.extend(found)
    if hits:
        return None, None, tuple(hits)
    return elements, feedback, ()
