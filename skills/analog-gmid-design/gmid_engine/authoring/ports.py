"""포트 선언 접근자 `ports` (설계 design_mod3_s1_graph 2.1 `ports.py`, U-08, 기본 전달 뷰 P 341).

진입점: `port_declaration(doc, rails, known_nets) -> tuple[PortDecl]` (넷순).

`rails` = `RailDeclaration`, `known_nets` = 단자(MOS d/g/s/bulk, 수동소자·이상원 terminals)에 나타나는 넷 frozenset.
둘 중 하나가 None 이면(그 선언이 거부돼 판정 입력이 없음) 그것을 쓰는 검사(`port_on_rail` / `port_net_unknown`)만 하지
않는다 -- 호출자(`load_topology`)가 `not_evaluated` 에 남긴다. 나머지 형식 검사는 그대로 한다.
거부(모두 모아 `SchemaRejectedError` 한 번, detail `gate="ports"`):
* `missing_key` -- 최상위 `ports` 가 없다. `ports_type` -- JSON 객체(넷 -> 선언)가 아니다.
* `port_entry_type` -- 선언이 객체가 아니다. `port_unknown_key` -- 선언 키가 `PORT_KEYS` + `_` 주석 밖.
* `port_direction` -- direction 이 `DIRECTIONS` 밖. `port_role` -- role 이 비어 있지 않은 문자열이 아니다.
* `port_net_unknown` -- 넷이 어느 단자에도 없다. `port_on_rail` -- 넷이 레일 선언에 있다.
* `no_input_port` / `no_output_port` -- 유효한 input / output 포트가 하나도 없다.
`_` 로 시작하는 키(주석)는 포트가 아니다.
"""
from ._rejection import reject, require_object
from .topology_model import PortDecl, SchemaHit

PORTS_KEY = "ports"
PORT_KEYS = ("direction", "role")
INPUT_DIRECTION = "input"
OUTPUT_DIRECTION = "output"
DIRECTIONS = (INPUT_DIRECTION, OUTPUT_DIRECTION)
COMMENT_PREFIX = "_"


def port_declaration(doc, rails, known_nets):
    require_object("ports", doc)
    if PORTS_KEY not in doc:
        reject("ports", PORTS_KEY, (SchemaHit("missing_key", PORTS_KEY, "최상위 ports 가 없다(입력·출력 포트 선언 필수)"),))
    declared = doc[PORTS_KEY]
    if not isinstance(declared, dict):
        reject("ports", PORTS_KEY,
               (SchemaHit("ports_type", PORTS_KEY, "ports 는 객체(넷 -> 선언)여야 한다: " + type(declared).__name__),))
    hits = []
    ports = []
    for net in declared:
        if net.startswith(COMMENT_PREFIX):
            continue
        entry = declared[net]
        where = PORTS_KEY + "." + net
        if not isinstance(entry, dict):
            hits.append(SchemaHit("port_entry_type", where, "포트 선언이 객체가 아니다: " + type(entry).__name__, (net,)))
            continue
        before = len(hits)
        for key in entry:
            if not key.startswith(COMMENT_PREFIX) and key not in PORT_KEYS:
                hits.append(SchemaHit("port_unknown_key", where + "." + key,
                                      "포트 선언 키 " + repr(key) + " 는 받지 않는다(" + repr(PORT_KEYS) + " 만)", (net,)))
        if entry.get("direction") not in DIRECTIONS:
            hits.append(SchemaHit("port_direction", where + ".direction",
                                  "direction 은 " + repr(DIRECTIONS) + " 중 하나여야 한다: " + repr(entry.get("direction")),
                                  (net,)))
        if not isinstance(entry.get("role"), str) or not entry.get("role"):
            hits.append(SchemaHit("port_role", where + ".role",
                                  "role 은 비어 있지 않은 문자열이어야 한다: " + repr(entry.get("role")), (net,)))
        if known_nets is not None and net not in known_nets:
            hits.append(SchemaHit("port_net_unknown", where, "포트 넷 " + repr(net) + " 이 어느 단자에도 없다", (net,)))
        if rails is not None and net in rails.nets:
            hits.append(SchemaHit("port_on_rail", where, "포트 넷 " + repr(net) + " 이 레일 선언(supply_nets)에 있다",
                                  (net,)))
        if len(hits) == before:
            ports.append(PortDecl(net, entry["direction"], entry["role"]))
    for direction, rule in ((INPUT_DIRECTION, "no_input_port"), (OUTPUT_DIRECTION, "no_output_port")):
        if not any(p.direction == direction for p in ports):
            hits.append(SchemaHit(rule, PORTS_KEY, "유효한 " + direction + " 포트가 하나도 없다(기본 전달 뷰에 필요)"))
    if hits:
        reject("ports", PORTS_KEY, hits)
    return tuple(sorted(ports, key=lambda p: p.net))
