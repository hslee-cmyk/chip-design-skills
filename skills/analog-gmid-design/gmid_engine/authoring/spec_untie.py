"""θ 묶음 풀기 원소 교차 검사 -- `search.untie_orbits` 의 원소가 topology 소자·수동소자인지 (사용자 결정 2026-10-08, search CONTRACT 3.24).

진입점: `untie_declaration(search, topology) -> tuple[SchemaHit]`.

* `search` = `settings_declaration` 의 search 묶음(SettingValue tuple), `topology` = TopologyDoc 또는 None(meta 지문 불일치 -- 검사 안 함).
* `untie_orbits` 칸이 없으면 hit 없음. 있으면 원소마다 topology 의 MOS·수동소자 이름이어야 한다 -- 아니면 hit `untie_element`
  (where `human.search.untie_orbits.<원소>`, elements = (원소,)). 그 원소의 궤도에 구성원이 둘 이상인지는 그래프가 필요해 search 의
  `orbit_ties` 가 본다(`untie_orbit_trivial`).
"""
from ._spec_fields import at
from .topology_model import SchemaHit

_FIELD = "untie_orbits"
_WHERE = at(at("human", "search"), _FIELD)


def untie_declaration(search, topology):
    if search is None or topology is None:
        return ()
    entry = next((s for s in search if s.field == _FIELD), None)
    if entry is None:
        return ()
    known = {d.name for d in topology.devices} | {p.name for p in topology.passives}
    return tuple(SchemaHit("untie_element", at(_WHERE, name),
                           "묶음을 풀 원소는 topology 의 MOS·수동소자여야 한다: " + repr(name), (name,))
                 for name, _source in entry.value if name not in known)
