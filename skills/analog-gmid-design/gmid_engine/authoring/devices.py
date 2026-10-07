"""netlist MOS 소자 선언 접근자 (설계 design_mod3_s1_graph 2.1 -- `topology_schema.py` 의 netlist 원소 검사를 맡는다).

진입점: `device_declaration(doc) -> tuple[DeviceDecl]` (이름순).

거부(모두 모아 `SchemaRejectedError` 한 번, detail `gate="devices"`):
* `missing_key` -- 최상위 `netlist` 가 없다. `netlist_type` -- list 가 아니다.
* `element_type` -- 원소가 JSON 객체가 아니다.
* `element_unknown_key` -- 원소 키가 `DEVICE_KEYS` + `_` 주석 키 밖(`n_fingers`·`w` 같은 사이징 산출물 포함).
* `element_field` -- `REQUIRED_DEVICE_KEYS` 중 빠졌거나 비어 있지 않은 문자열이 아니다. `bulk` 는 있으면 비어 있지 않은
  문자열(없으면 선언 없음 -- 기본 규칙은 graph 몫, DEC-61).
kind 값은 제한하지 않는다(nmos·pmos 밖 kind 는 graph 가 기록만 한다, DEC-59·61). 이름 중복은 `name_uniqueness.py`.
"""
from ._rejection import reject, require_object
from .topology_model import DeviceDecl, SchemaHit

NETLIST_KEY = "netlist"
REQUIRED_DEVICE_KEYS = ("name", "kind", "drain", "gate", "source")
OPTIONAL_DEVICE_KEYS = ("bulk",)
DEVICE_KEYS = REQUIRED_DEVICE_KEYS + OPTIONAL_DEVICE_KEYS
COMMENT_PREFIX = "_"


def device_declaration(doc):
    require_object("devices", doc)
    if NETLIST_KEY not in doc:
        reject("devices", NETLIST_KEY, (SchemaHit("missing_key", NETLIST_KEY, "최상위 netlist 가 없다"),))
    netlist = doc[NETLIST_KEY]
    if not isinstance(netlist, list):
        reject("devices", NETLIST_KEY,
               (SchemaHit("netlist_type", NETLIST_KEY, "netlist 는 list 여야 한다: " + type(netlist).__name__),))
    hits = []
    devices = []
    for index, raw in enumerate(netlist):
        where = NETLIST_KEY + "[" + str(index) + "]"
        if not isinstance(raw, dict):
            hits.append(SchemaHit("element_type", where, "netlist 원소가 객체가 아니다: " + type(raw).__name__))
            continue
        label = raw.get("name") if isinstance(raw.get("name"), str) else where
        bad = False
        for key in sorted(raw):
            if not key.startswith(COMMENT_PREFIX) and key not in DEVICE_KEYS:
                hits.append(SchemaHit("element_unknown_key", where + "." + key,
                                      "netlist 원소 키 " + repr(key) + " 는 받지 않는다(연결 키 " + repr(DEVICE_KEYS)
                                      + " 만 -- 사이징 산출물은 topology 에 두지 않는다)", (label,)))
                bad = True
        for key in REQUIRED_DEVICE_KEYS:
            value = raw.get(key)
            if not isinstance(value, str) or not value:
                hits.append(SchemaHit("element_field", where + "." + key,
                                      key + " 는 비어 있지 않은 문자열이어야 한다: " + repr(value), (label,)))
                bad = True
        bulk = raw.get("bulk")
        if "bulk" in raw and (not isinstance(bulk, str) or not bulk):
            hits.append(SchemaHit("element_field", where + ".bulk",
                                  "bulk 는 있으면 비어 있지 않은 문자열이어야 한다: " + repr(bulk), (label,)))
            bad = True
        if not bad:
            devices.append(DeviceDecl(raw["name"], raw["kind"], raw["drain"], raw["gate"], raw["source"], bulk))
    if hits:
        reject("devices", NETLIST_KEY, hits)
    return tuple(sorted(devices, key=lambda x: x.name))
