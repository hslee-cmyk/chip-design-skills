"""의도 영역 선언 `human.intended_region` (설계 design_spec_format 1.6, CI-18, AC-1 (ii)).

진입점: `intended_region_declaration(raw, topology) -> (tuple[RegionDecl] | PendingMark | None, tuple[SchemaHit])`.

모양: `{"pending": <ID>}` / `{}`(전 소자 포화 검사의 명시 선언) / `{<소자>: {"region": <영역>, "source"}}`, 영역 ∈
`REGIONS`. 위반: `type`(형식·어휘 밖 영역), `intended_region_device`(topology 소자 밖). `topology` 가 None 이면 소자
교차 검사를 하지 않는다.
"""
from ._spec_fields import COMMENT_PREFIX, at, is_pending, key_hits, pending_decision
from .spec_model import PendingMark, RegionDecl
from .spec_sources import source_declaration_checks
from .topology_model import SchemaHit

SECTION = "intended_region"
WHERE = "human.intended_region"
REGIONS = ("triode",)


def intended_region_declaration(raw, topology):
    if is_pending(raw):
        return PendingMark(WHERE, pending_decision(raw)), ()
    if not isinstance(raw, dict):
        return None, (SchemaHit("type", WHERE, "intended_region 은 객체(소자 -> 선언)여야 한다: " + type(raw).__name__),)
    devices = frozenset(x.name for x in topology.devices) if topology is not None else None
    hits = []
    out = []
    for name in raw:
        if name.startswith(COMMENT_PREFIX):
            continue
        where = at(WHERE, name)
        entry = raw[name]
        if not isinstance(entry, dict):
            hits.append(SchemaHit("type", where, "영역 선언은 {region, source} 객체여야 한다", (name,)))
            continue
        hits.extend(key_hits(entry, ("region", "source"), where, (name,)))
        source, source_hits = source_declaration_checks(entry.get("source"), where, SECTION)
        hits.extend(source_hits)
        if entry.get("region") not in REGIONS:
            hits.append(SchemaHit("type", at(where, "region"), "region 은 " + repr(REGIONS) + " 중 하나: "
                                  + repr(entry.get("region")), (name,)))
        else:
            out.append(RegionDecl(name, entry["region"], source))
        if devices is not None and name not in devices:
            hits.append(SchemaHit("intended_region_device", where, "소자 " + repr(name) + " 가 topology 에 없다", (name,)))
    if hits:
        return None, tuple(hits)
    return tuple(sorted(out, key=lambda x: x.device)), ()
