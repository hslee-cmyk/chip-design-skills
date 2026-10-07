"""레일 전위 인자 `supplies_v` 정규화·검사 (사용자 확정 2026-10-07 1·6번, DEC-60 (i) 'spec 넷 키 = supply_nets').

진입점: `supplies_declaration(supplies_v, rails) -> tuple | None`.

* `supplies_v` 는 인자로만 받는다(회로 spec 로더는 아직 없다). topology 의 `_` 주석 키(`_declared_target_spec`)는
  엔진이 읽지 않는다.
* None -> None(bulk 기본 규칙을 적용하지 않는다 -> bulk = undetermined(needs_supplies_v)).
* 그 밖 -> 넷 이름순 ((넷, float 전위), ...) tuple.
* 거부(위반을 모두 모아 core `SchemaRejectedError` 한 번, detail gate = `supplies_v`):
  `supplies_type`(Mapping 아님), `supplies_value`(값이 bool 이거나 유한 실수가 아님, 넷마다),
  `supplies_missing_rail`(레일 선언 넷인데 전위 없음, 넷마다), `supplies_unknown_net`(레일 선언 밖 넷, 넷마다).
  전위를 레일 이름으로 짐작하지 않는다.
"""
import math
from collections.abc import Mapping
from numbers import Real

from gmid_engine.authoring import SchemaHit
from gmid_engine.core import SchemaRejectedError, sorted_items

GATE = "supplies_v"


def supplies_declaration(supplies_v, rails):
    if supplies_v is None:
        return None
    if not isinstance(supplies_v, Mapping):
        _reject((SchemaHit("supplies_type", GATE, "supplies_v 는 {레일 넷: 전위} 매핑이어야 한다: "
                           + type(supplies_v).__name__),))
    hits = []
    pairs = []
    for net, value in sorted_items(supplies_v, key=str):
        where = GATE + "." + str(net)
        if not isinstance(net, str) or net not in rails:
            hits.append(SchemaHit("supplies_unknown_net", where, "supplies_v 의 넷이 supply_nets 선언 밖이다",
                                  (str(net),)))
            continue
        if isinstance(value, bool) or not isinstance(value, Real) or not math.isfinite(value):
            hits.append(SchemaHit("supplies_value", where, "전위는 유한 실수여야 한다: " + repr(value), (net,)))
            continue
        pairs.append((net, float(value)))
    hits.extend(SchemaHit("supplies_missing_rail", GATE + "." + net, "레일 선언 넷의 전위가 없다", (net,))
                for net in sorted_items(rails) if net not in supplies_v)
    if hits:
        _reject(hits)
    return tuple(pairs)


def _reject(hits):
    raise SchemaRejectedError(detail={"gate": GATE, "where": GATE, "hits": tuple(hits)})
