"""입력 DC 선언 `human.input_dc` (설계 design_spec_format 1.6, F10, SP-2·G7-U2).

진입점: `input_dc_declaration(raw, topology, supplies) -> (InputDc | None, tuple[SchemaHit])`.

모양(정확히 하나): `{"pending": <ID>}` / `{"net": <레일 넷>, "source"}` / `{"value_v": V, "source"}` /
`{"engine": true, "source"}`(W4 자유 변수 -- 결과에 '요구 입력 공통모드'로 보고). 위반:
* `type` -- 객체가 아니거나, 값 키(`MODE_KEYS`)가 정확히 하나가 아니거나, 값 형식이 틀렸다(`net` 비문자열, `value_v`
  비유한 수, `engine` 이 true 아님). 받는 키 밖은 `key_hits`, 출처는 `spec_sources`.
* `input_dc_net_not_rail` -- `net` 이 topology 레일 선언 밖(`topology` 가 None 이면 보지 않음).
* `input_dc_out_of_rails` -- `value_v` 가 선언 레일 전압 범위 밖(`supplies` 가 None 이면 -- 전원 선언이 거부됨 -- 보지 않음).
"""
from ._spec_fields import at, finite_number, is_pending, key_hits, pending_decision
from .spec_model import InputDc
from .spec_sources import source_declaration_checks
from .topology_model import SchemaHit

SECTION = "input_dc"
WHERE = "human.input_dc"
MODE_KEYS = ("net", "value_v", "engine")


def input_dc_declaration(raw, topology, supplies):
    if is_pending(raw):
        return InputDc("pending", decision=pending_decision(raw)), ()
    if not isinstance(raw, dict):
        return None, (SchemaHit("type", WHERE, "input_dc 는 객체여야 한다: " + type(raw).__name__),)
    hits = key_hits(raw, MODE_KEYS + ("source",), WHERE)
    source, source_hits = source_declaration_checks(raw.get("source"), WHERE, SECTION)
    hits.extend(source_hits)
    present = tuple(k for k in MODE_KEYS if k in raw)
    if len(present) != 1:
        hits.append(SchemaHit("type", WHERE, "input_dc 는 " + repr(MODE_KEYS) + " 중 정확히 하나를 쓴다: "
                              + repr(present)))
        return None, tuple(hits)
    mode = present[0]
    value = raw[mode]
    if mode == "net":
        if not isinstance(value, str) or not value:
            hits.append(SchemaHit("type", at(WHERE, mode), "net 은 비어 있지 않은 문자열이어야 한다: " + repr(value)))
        elif topology is not None and value not in topology.rails:
            hits.append(SchemaHit("input_dc_net_not_rail", at(WHERE, mode),
                                  "입력 DC 넷 " + repr(value) + " 이 레일 선언(supply_nets)에 없다", (value,)))
        result = InputDc("net", net=value, source=source)
    elif mode == "value_v":
        if not finite_number(value):
            hits.append(SchemaHit("type", at(WHERE, mode), "value_v 는 유한 수여야 한다: " + repr(value)))
        elif supplies is not None:
            volts = tuple(v for _n, v in supplies)
            if not min(volts) <= value <= max(volts):
                hits.append(SchemaHit("input_dc_out_of_rails", at(WHERE, mode), "입력 DC " + repr(value)
                                      + " V 가 레일 전압 범위 [" + repr(min(volts)) + ", " + repr(max(volts)) + "] 밖"))
        result = InputDc("value", value_v=float(value) if finite_number(value) else None, source=source)
    else:
        if value is not True:
            hits.append(SchemaHit("type", at(WHERE, mode), "engine 은 true 만 받는다: " + repr(value)))
        result = InputDc("engine", source=source)
    if hits:
        return None, tuple(hits)
    return result, ()
