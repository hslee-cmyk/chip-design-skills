"""레일 선언 접근자 `supply_nets` (B26-1 이식 -- gmid-light cb0ef86 `stick_diagram.rail_declaration`, DEC-60).

진입점: `rail_declaration(doc) -> RailDeclaration`.

거부(모두 모아 `SchemaRejectedError` 한 번, detail `gate="rails"`; 옛 함수의 `ValueError` 를 core 예외로 바꿨다):
* `missing_key` -- 최상위 `supply_nets` 가 없다(레일은 선언으로만 정한다, 넷 이름 집합으로 대신하지 않는다).
* `supply_nets_type` -- list 가 아니다.
* `supply_net_value` -- 원소가 비어 있지 않은 문자열이 아니다(원소마다 하나).
* `supply_net_duplicate` -- 같은 원소가 두 번 이상(중복 넷마다 하나).
빈 list `[]` 는 받는다(레일 없음이라는 명시 선언). 선언 밖 넷은 이름이 무엇이든 레일이 아니다.

여기서 보지 않는 것: 선언 넷이 실제 단자에 있는가·숨은 레일 후보(DEC-60 (iii)) -- `hidden_rails.py` 가 연결과 함께 본다.
"""
from ._rejection import reject, require_object
from .topology_model import RailDeclaration, SchemaHit

SUPPLY_KEY = "supply_nets"


def rail_declaration(doc):
    require_object("rails", doc)
    if SUPPLY_KEY not in doc:
        reject("rails", SUPPLY_KEY, (SchemaHit(
            "missing_key", SUPPLY_KEY,
            "최상위 supply_nets 가 없다 -- 레일은 supply_nets 선언으로만 정한다(DEC-60, 넷 이름으로 대신하지 않는다)"),))
    declared = doc[SUPPLY_KEY]
    if not isinstance(declared, list):
        reject("rails", SUPPLY_KEY, (SchemaHit(
            "supply_nets_type", SUPPLY_KEY, "supply_nets 는 list 여야 한다(DEC-60): " + type(declared).__name__),))
    hits = []
    seen = set()
    reported = set()
    for index, net in enumerate(declared):
        where = SUPPLY_KEY + "[" + str(index) + "]"
        if not isinstance(net, str) or not net:
            hits.append(SchemaHit("supply_net_value", where,
                                  "supply_nets 원소는 비어 있지 않은 문자열이어야 한다(DEC-60): " + repr(net)))
            continue
        if net in seen and net not in reported:
            hits.append(SchemaHit("supply_net_duplicate", where,
                                  "supply_nets 에 같은 원소가 중복돼 있다(DEC-60): " + repr(net), (net,)))
            reported.add(net)
        seen.add(net)
    if hits:
        reject("rails", SUPPLY_KEY, hits)
    return RailDeclaration(frozenset(declared))
