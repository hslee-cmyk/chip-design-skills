"""θ 상자 원소 교차 검사 -- `search.theta_bounds` 의 원소가 engine 값 저항·커패시터인지 (사용자 승인 2026-10-08 원소별 θ 상자,
search CONTRACT r10, DEC-92).

진입점: `theta_bound_declaration(search, elements, topology) -> (search | None, tuple[SchemaHit])`.

* `search` = `settings_declaration` 의 search 묶음(SettingValue tuple), `elements` = `element_value_declaration` 결과
  (`ElementValue` tuple), `topology` = TopologyDoc 또는 None(meta 지문 불일치 -- 교차 검사 안 함, search 그대로).
* `theta_bounds` 칸이 없으면 search 그대로. 있으면 원소마다: topology 수동소자이고 kind ∈ {resistor, capacitor}이며 spec 요소 값
  mode 가 `engine` 이어야 한다 -- 아니면 hit `theta_bound_element`(where `human.search.theta_bounds.<원소>`, elements = (원소,)).
* 통과하면 그 칸 값을 `ThetaBound(element, kind, lo, hi, source)` 이름순 tuple 로 바꾼 search 묶음을 돌려준다(kind 가 단위를 정한다:
  resistor Ω, capacitor F). 위반이 있으면 (None, hits).
"""
from ._spec_fields import at
from .spec_model import SettingValue, ThetaBound
from .topology_model import SchemaHit

_FIELD = "theta_bounds"
_KINDS = ("capacitor", "resistor")
_ENGINE = "engine"
_WHERE = at(at("human", "search"), _FIELD)


def theta_bound_declaration(search, elements, topology):
    if search is None or topology is None:
        return search, ()
    entry = next((s for s in search if s.field == _FIELD), None)
    if entry is None:
        return search, ()
    kinds = {p.name: p.kind for p in topology.passives}
    modes = {e.name: e.mode for e in (elements or ())}
    hits, bounds = [], []
    for name, lo, hi, source in entry.value:
        if kinds.get(name) not in _KINDS or modes.get(name) != _ENGINE:
            hits.append(SchemaHit("theta_bound_element", at(_WHERE, name),
                                  "θ 상자는 spec 값이 engine 인 저항·커패시터에만 둔다: " + repr(name)
                                  + " (kind " + repr(kinds.get(name)) + ", 값 mode " + repr(modes.get(name)) + ")", (name,)))
            continue
        bounds.append(ThetaBound(name, kinds[name], lo, hi, source))
    if hits:
        return None, tuple(hits)
    return tuple(SettingValue(_FIELD, tuple(bounds), entry.source) if s is entry else s for s in search), ()
