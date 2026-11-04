"""의도 영역 선언 `human.intended_region` (설계 design_spec_format 1.6, CI-18, AC-1 (ii)).

진입점: `intended_region_declaration(raw, topology) -> (tuple[RegionDecl] | PendingMark | None, tuple[SchemaHit])`.

모양: `{"pending": <ID>}` / `{}`(전 소자 포화 검사의 명시 선언) / `{<소자>: {"region": <영역>, "source"}}`, 영역 ∈
`REGIONS` = (`REGION_TRIODE` = "triode", `REGION_OFF` = "off"). `triode` 는 sizing 공용 영역 판정(`judge_region`)이 포화 대신 선형을 기대하게 한다.
`off` 는 사이징에서 빠지는 꺼진 소자(O-221)이고 `w_m`·`l_m`(양수, 필수)과 `judged_by`(문자열 목록, 없음·빈 목록은 로드 통과 -- 정지는 O-h)를 가진다.
`w_m`·`l_m`·`judged_by` 는 `off` 에만 받는다(그 밖은 `type`). 위반: `type`(형식·어휘 밖 영역), `intended_region_device`(topology 소자 밖).
`topology` 가 None 이면 소자 교차 검사를 하지 않는다.
"""
from ._spec_fields import COMMENT_PREFIX, at, is_pending, key_hits, pending_decision
from .spec_model import PendingMark, RegionDecl
from .spec_sources import source_declaration_checks
from .topology_model import SchemaHit

SECTION = "intended_region"
WHERE = "human.intended_region"
REGION_TRIODE = "triode"                     # 선형 영역 의도 -- 사용자 어휘 정본(sizing `LINEAR_REGION` 이 이 값을 쓴다)
REGION_OFF = "off"                           # 꺼진 소자 선언(O-221, SF-1 로더 조각)
REGIONS = (REGION_TRIODE, REGION_OFF)
_OFF_ONLY_KEYS = ("w_m", "l_m", "judged_by")


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
        is_off = entry.get("region") == REGION_OFF
        hits.extend(key_hits(entry, ("region", "source") + _OFF_ONLY_KEYS, where, (name,)))
        source, source_hits = source_declaration_checks(entry.get("source"), where, SECTION)
        hits.extend(source_hits)
        if entry.get("region") not in REGIONS:
            hits.append(SchemaHit("type", at(where, "region"), "region 은 " + repr(REGIONS) + " 중 하나: "
                                  + repr(entry.get("region")), (name,)))
        elif is_off:
            decl, off_hits = _off_decl(name, entry, source, where)
            hits.extend(off_hits)
            if decl is not None:
                out.append(decl)
        else:
            for key in _OFF_ONLY_KEYS:
                if key in entry:
                    hits.append(SchemaHit("type", at(where, key), key + " 은 region 'off' 소자에만 받는다", (name,)))
            out.append(RegionDecl(name, entry["region"], source))
        if devices is not None and name not in devices:
            hits.append(SchemaHit("intended_region_device", where, "소자 " + repr(name) + " 가 topology 에 없다", (name,)))
    if hits:
        return None, tuple(hits)
    return tuple(sorted(out, key=lambda x: x.device)), ()


def _off_decl(name, entry, source, where):
    """`off` 항목 하나 -> (RegionDecl | None, hits). `w_m`·`l_m` 양의 수 필수, `judged_by` 선택(문자열 목록)."""
    hits = []
    sizes = []
    for key in ("w_m", "l_m"):
        v = entry.get(key)
        if isinstance(v, bool) or not isinstance(v, (int, float)) or not v > 0:
            hits.append(SchemaHit("type", at(where, key), key + " 은 양의 수여야 한다(off 소자): " + repr(v), (name,)))
        sizes.append(v)
    judged = entry.get("judged_by", [])
    if not isinstance(judged, list) or not all(isinstance(x, str) for x in judged):
        hits.append(SchemaHit("type", at(where, "judged_by"), "judged_by 는 문자열 목록이어야 한다: " + repr(judged), (name,)))
    if hits:
        return None, hits
    return RegionDecl(name, REGION_OFF, source, tuple(judged), float(sizes[0]), float(sizes[1])), ()
