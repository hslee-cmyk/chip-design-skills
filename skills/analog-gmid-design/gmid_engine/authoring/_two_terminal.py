"""authoring 공용 helper -- 2단자 원소 목록(수동소자·이상원) 읽기. `passives.py`·`ideal_sources.py` 가 같이 쓴다.

`two_terminal_elements(raw, key, value_keys, ignored_keys, make) -> (원소 tuple, SchemaHit tuple)`:
원소마다 검사하고 걸린 곳을 모두 모은다. 위반 종류(규칙 키):
* `<key>_type` -- 목록이 list 가 아니다(이 경우 원소 검사 없음).
* `element_type` -- 원소가 객체가 아니다.
* `element_unknown_key` -- 받는 키(name·kind·terminals + value_keys + ignored_keys + `_` 주석) 밖.
* `element_field` -- name·kind 가 비어 있지 않은 문자열이 아니다.
* `terminals` -- terminals 가 list 가 아니거나, 원소 수가 `TWO_TERMINAL_NAMES` 수와 다르거나, 넷이 비어 있지 않은 문자열이
  아니거나, 두 넷이 같다.
* `element_value` -- 값 필드가 둘 이상이거나, 값이 null·유한 수(bool 제외)가 아니다.
`ignored_keys` 는 허용하되 읽지 않는다(선언 투영에 들어가지 않는다).
"""
import math

from .topology_model import TWO_TERMINAL_NAMES, SchemaHit

ELEMENT_KEYS = ("name", "kind", "terminals")
COMMENT_PREFIX = "_"


def two_terminal_elements(raw, key, value_keys, ignored_keys, make):
    if not isinstance(raw, list):
        return (), (SchemaHit(key + "_type", key, key + " 는 list 여야 한다: " + type(raw).__name__),)
    allowed = frozenset(ELEMENT_KEYS + tuple(value_keys) + tuple(ignored_keys))
    hits = []
    elements = []
    for index, item in enumerate(raw):
        where = key + "[" + str(index) + "]"
        if not isinstance(item, dict):
            hits.append(SchemaHit("element_type", where, key + " 원소가 객체가 아니다: " + type(item).__name__))
            continue
        label = item.get("name") if isinstance(item.get("name"), str) else where
        before = len(hits)
        for k in item:
            if not k.startswith(COMMENT_PREFIX) and k not in allowed:
                hits.append(SchemaHit("element_unknown_key", where + "." + k,
                                      key + " 원소 키 " + repr(k) + " 는 받지 않는다(받는 키 " + repr(sorted(allowed)) + ")",
                                      (label,)))
        for k in ("name", "kind"):
            if not isinstance(item.get(k), str) or not item.get(k):
                hits.append(SchemaHit("element_field", where + "." + k,
                                      k + " 는 비어 있지 않은 문자열이어야 한다: " + repr(item.get(k)), (label,)))
        terminals = item.get("terminals")
        nets_ok = (isinstance(terminals, list) and len(terminals) == len(TWO_TERMINAL_NAMES)
                   and all(isinstance(t, str) and t for t in terminals))
        if not nets_ok or len(set(terminals)) != len(terminals):
            hits.append(SchemaHit("terminals", where + ".terminals",
                                  "terminals 는 서로 다른 넷 문자열 " + str(len(TWO_TERMINAL_NAMES))
                                  + "개의 list 여야 한다: " + repr(terminals), (label,)))
        present = tuple(k for k in value_keys if k in item)
        value = item.get(present[0]) if present else None
        if len(present) > 1:
            hits.append(SchemaHit("element_value", where, "값 필드가 둘 이상이다: " + repr(present), (label,)))
        elif value is not None and (isinstance(value, bool) or not isinstance(value, (int, float))
                                    or not math.isfinite(value)):
            hits.append(SchemaHit("element_value", where + "." + present[0],
                                  "값은 null 또는 유한 수여야 한다: " + repr(value), (label,)))
        if len(hits) == before:
            elements.append(make(item["name"], item["kind"], tuple(terminals),
                                 present[0] if present else None, value))
    return tuple(sorted(elements, key=lambda x: x.name)), tuple(hits)
