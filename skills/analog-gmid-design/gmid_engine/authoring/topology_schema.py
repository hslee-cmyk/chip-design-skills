"""topology 최상위 스키마 -- 키 화이트리스트·스키마 버전·이름 (설계 design_mod3_s1_graph 2.1 `topology_schema.py`).

진입점: `check_topology_schema(doc) -> tuple[SchemaHit]` (빈 tuple = 통과).

* 최상위 값은 JSON 객체여야 한다(`top_not_object`, 이 경우 나머지 검사는 하지 않는다).
* 이 파일이 존재를 요구하는 키: `REQUIRED_KEYS`(`missing_key`). `DECLARATION_KEYS`(netlist·supply_nets·ports·
  passive_elements)도 필수지만 존재·형식은 각자의 선언 접근자(devices·rails·ports·passives)가 판정한다(같은 위반을
  두 번 세지 않는다).
* 받는 키 = `REQUIRED_KEYS` + `DECLARATION_KEYS` + `OPTIONAL_KEYS` + `IGNORED_TAG_KEYS` + `_` 접두 주석 키.
  그 밖 키는 `unknown_key`. 태그 키(`IGNORED_TAG_KEYS`)는 허용하되 읽지 않는다(IC4 태그 없는 유도 -- 태그를 채우는
  경로도 두지 않는다).
* `schema_version` 은 `SCHEMA_VERSION` 문자열과 같아야 한다(`schema_version`).
* `topology_name` 은 비어 있지 않은 문자열(`topology_name`), `source` 는 있으면 문자열 또는 null(`source_type`).
netlist 원소의 키·형식은 `devices.py`(`device_declaration`)가 본다.
"""
from .topology_model import SchemaHit

SCHEMA_VERSION = "2.0"
REQUIRED_KEYS = ("schema_version", "topology_name")
DECLARATION_KEYS = ("netlist", "supply_nets", "ports", "passive_elements")
OPTIONAL_KEYS = ("ideal_sources", "linked_topology_files", "source", "bias_inputs", "source_manifest")
IGNORED_TAG_KEYS = ("device_roles", "symmetry", "sizing_roles", "compensation")
COMMENT_PREFIX = "_"


def check_topology_schema(doc):
    """최상위 키·버전·이름 위반을 모두 모아 돌려준다."""
    if not isinstance(doc, dict):
        return (SchemaHit("top_not_object", "$", "topology 최상위 값이 JSON 객체가 아니다: " + type(doc).__name__),)
    hits = []
    for key in REQUIRED_KEYS:
        if key not in doc:
            hits.append(SchemaHit("missing_key", key, "필수 최상위 키 " + repr(key) + " 가 없다"))
    allowed = frozenset(REQUIRED_KEYS + DECLARATION_KEYS + OPTIONAL_KEYS + IGNORED_TAG_KEYS)
    for key in doc:
        if not key.startswith(COMMENT_PREFIX) and key not in allowed:
            hits.append(SchemaHit("unknown_key", key, "알 수 없는 최상위 키 " + repr(key)
                                  + " (받는 키 밖 -- 주석이면 '_' 접두를 쓴다)"))
    if "schema_version" in doc and doc["schema_version"] != SCHEMA_VERSION:
        hits.append(SchemaHit("schema_version", "schema_version", "schema_version " + repr(doc["schema_version"])
                              + " -- " + repr(SCHEMA_VERSION) + " 만 받는다"))
    if "topology_name" in doc:
        name = doc["topology_name"]
        if not isinstance(name, str) or not name:
            hits.append(SchemaHit("topology_name", "topology_name",
                                  "topology_name 은 비어 있지 않은 문자열이어야 한다: " + repr(name)))
    if "source" in doc and doc["source"] is not None and not isinstance(doc["source"], str):
        hits.append(SchemaHit("source_type", "source", "source 는 문자열 또는 null 이어야 한다: "
                              + type(doc["source"]).__name__))
    return tuple(hits)
