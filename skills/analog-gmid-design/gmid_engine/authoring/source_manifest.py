"""출처 매니페스트 `source_manifest` 와 선언 개수 대조 (Q7, SYNTHESIS Q9 (iii), 2026-10-08 사용자 확인).

진입점: `check_source_manifest(doc, devices, passives) -> tuple[SchemaHit]` (빈 tuple = 통과 또는 키 없음).

선택 최상위 키 `source_manifest` = {figure: 비어 있지 않은 문자열(출처 그림·쪽), device_count: MOS 개수, passive_count: 수동소자 개수}.
키 집합은 정확히 이 셋(`_` 주석 키 제외). 개수는 bool 이 아닌 0 이상의 정수.
대조: device_count == netlist MOS 소자 수(`devices`), passive_count == `passive_elements` 수(이상원 제외). 키가 없으면 검사하지 않는다.
위반: `source_manifest_type`(객체 아님), `source_manifest_key`(키 집합 틀림), `source_manifest_figure`, `source_manifest_count`(정수 아님),
`source_manifest_mismatch`(개수 불일치 -- message·elements 에 선언값과 실제 개수를 둘 다 적는다).
connectivity 가 아니라 `connectivity_fp` 에 들어가지 않는다.
"""
from .topology_model import SchemaHit

SOURCE_MANIFEST_KEY = "source_manifest"
MANIFEST_KEYS = ("figure", "device_count", "passive_count")
COMMENT_PREFIX = "_"


def check_source_manifest(doc, devices, passives):
    if SOURCE_MANIFEST_KEY not in doc:
        return ()
    m = doc[SOURCE_MANIFEST_KEY]
    k = SOURCE_MANIFEST_KEY
    if not isinstance(m, dict):
        return (SchemaHit("source_manifest_type", k, "source_manifest 는 객체여야 한다: " + type(m).__name__),)
    keys = tuple(x for x in m if not x.startswith(COMMENT_PREFIX))
    if set(keys) != set(MANIFEST_KEYS):
        return (SchemaHit("source_manifest_key", k, "source_manifest 키는 정확히 " + repr(MANIFEST_KEYS) + " 여야 한다: "
                          + repr(tuple(sorted(keys)))),)
    hits = []
    if not isinstance(m["figure"], str) or not m["figure"]:
        hits.append(SchemaHit("source_manifest_figure", k + ".figure", "figure 는 비어 있지 않은 문자열이어야 한다: "
                              + repr(m["figure"])))
    actual = {"device_count": len(devices), "passive_count": len(passives)}
    for key in ("device_count", "passive_count"):
        v = m[key]
        if isinstance(v, bool) or not isinstance(v, int) or v < 0:
            hits.append(SchemaHit("source_manifest_count", k + "." + key, key + " 는 0 이상의 정수여야 한다: " + repr(v)))
        elif v != actual[key]:
            hits.append(SchemaHit("source_manifest_mismatch", k + "." + key,
                                  key + " 선언 " + str(v) + " 개 != 실제 " + str(actual[key]) + " 개"
                                  + "(" + ("netlist MOS" if key == "device_count" else "passive_elements") + ")"))
    return tuple(hits)
