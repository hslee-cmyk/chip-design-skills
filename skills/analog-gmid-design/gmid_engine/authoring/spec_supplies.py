"""전원 선언 `human.supplies_v` (설계 design_spec_format 1.6, DEC-60 (i), SP-1).

진입점: `supplies_declaration(raw, topology) -> (tuple[(넷, V)] | None, tuple[SchemaHit])` (넷 이름순).

모양: `{"values": {<레일 넷>: <V>}, "source": {...}}`(결정 대기 표지 불가 -- 9회로 전부 확정, 레일 전압 없이는 S1 bulk
기본 규칙이 돌지 않는다). 위반:
* `type` -- 객체가 아니거나 `values` 가 객체가 아니다. 받는 키 밖은 `_spec_fields.key_hits`. 출처는 `spec_sources`.
* `supplies_value` -- 값이 유한 수가 아니다(넷마다).
* `supplies_net_missing` / `supplies_net_extra` -- 넷 키 집합이 topology 레일 선언(`supply_nets`)과 다르다(빠진 넷·
  남는 넷 둘 다). `topology` 가 None 이면(meta 지문 불일치로 교차 검사를 돌리지 않음) 이 둘은 보지 않는다.
* `supplies_top_rail_ambiguous` -- 최고 전위 값을 가진 레일이 둘 이상(가장 높은 레일 유도 함수가 하나로 정해져야
  한다, DEC-60).
"""
from ._spec_fields import at, finite_number, key_hits
from .spec_sources import source_declaration_checks
from .topology_model import SchemaHit

SECTION = "supplies_v"
WHERE = "human.supplies_v"
KEYS = ("values", "source")


def supplies_declaration(raw, topology):
    if not isinstance(raw, dict):
        return None, (SchemaHit("type", WHERE, "supplies_v 는 {values, source} 객체여야 한다: " + type(raw).__name__),)
    hits = key_hits(raw, KEYS, WHERE)
    _source, source_hits = source_declaration_checks(raw.get("source"), WHERE, SECTION)
    hits.extend(source_hits)
    values = raw.get("values")
    if not isinstance(values, dict):
        hits.append(SchemaHit("type", at(WHERE, "values"), "supplies_v.values 는 객체(레일 넷 -> V)여야 한다: "
                              + type(values).__name__))
        return None, tuple(hits)
    pairs = []
    for net in values:
        if not finite_number(values[net]):
            hits.append(SchemaHit("supplies_value", at(at(WHERE, "values"), net),
                                  "레일 전압은 유한 수여야 한다: " + repr(values[net]), (net,)))
        else:
            pairs.append((net, float(values[net])))
    if topology is not None:
        for net in sorted(topology.rails - set(values)):
            hits.append(SchemaHit("supplies_net_missing", at(WHERE, "values"),
                                  "topology 레일 " + repr(net) + " 의 전압 선언이 없다(DEC-60 (i))", (net,)))
        for net in sorted(set(values) - topology.rails):
            hits.append(SchemaHit("supplies_net_extra", at(at(WHERE, "values"), net),
                                  "넷 " + repr(net) + " 은 topology 레일 선언(supply_nets)에 없다", (net,)))
    if pairs:
        top = max(v for _n, v in pairs)
        tops = tuple(n for n, v in pairs if v == top)
        if len(tops) > 1:
            hits.append(SchemaHit("supplies_top_rail_ambiguous", at(WHERE, "values"),
                                  "최고 전위 레일이 하나로 정해지지 않는다: " + repr(sorted(tops)), tops))
    if hits:
        return None, tuple(hits)
    return tuple(sorted(pairs)), ()
