"""θ 성분의 자기동형 궤도 묶음 (사용자 결정 2026-10-08, CONTRACT 3.24).

진입점: `orbit_ties(dc_ctx, components, untied) -> (대표 성분 tuple, ties)`.

* `components` = θ 스키마 성분 (종류, 키) 열. 키가 원소(소자)면 `device.dc_orbit`, `y` 의 키가 넷이면 `node.dc_orbit` 의 궤도 id 로 본다.
  같은 (종류, 궤도) 의 성분이 둘 이상이면 한 변수로 묶는다: 대표 = 구조 색 `dc_colour`(1-WL 색 + 정준 위치, 정점마다 유일) 최소, 나머지 = 묶인 성분.
* `untied` = 묶지 않을 원소 이름 tuple(spec `search.untie_orbits`): 그 원소의 궤도는 묶지 않는다. 궤도가 원소 하나뿐이면(묶을 것이 없다)
  `SchemaRejectedError`(gate `search_domain`, reason `untie_orbit_trivial`) -- 오타·무의미한 선언을 조용히 받지 않는다. 원소가 없으면
  `untie_element_unknown`.
* 반환 `ties` = ((대표, (구성원, ...)), ...) 대표의 정준 순서(성분 종류, 궤도 id)로 정렬.
"""
from gmid_engine.core import SchemaRejectedError
from gmid_engine.sizing import THETA_Y


def _orbit_of(component, device_orbit, node_orbit):
    kind, key = component
    table = node_orbit if kind == THETA_Y else device_orbit
    if key in table:
        return ("n" if table is node_orbit else "e", table[key])
    return None


def orbit_ties(dc_ctx, components, untied):
    device_orbit = dict(dc_ctx.base.column("device", "dc_orbit"))
    node_orbit = dict(dc_ctx.base.column("node", "dc_orbit"))
    colour = {**dict(dc_ctx.base.column("node", "dc_colour")), **dict(dc_ctx.base.column("device", "dc_colour"))}
    sizes = {}
    for o in device_orbit.values():
        sizes[o] = sizes.get(o, 0) + 1
    free = set()
    for name in untied:
        if name not in device_orbit:
            raise SchemaRejectedError(detail={"gate": "search_domain", "reason": "untie_element_unknown", "element": name})
        if sizes[device_orbit[name]] == 1:
            raise SchemaRejectedError(detail={"gate": "search_domain", "reason": "untie_orbit_trivial", "element": name})
        free.add(device_orbit[name])
    groups = {}
    for component in components:
        orbit = _orbit_of(component, device_orbit, node_orbit)
        key = (component[0], orbit)
        if orbit is None or (orbit[0] == "e" and orbit[1] in free):
            key = (component[0], None, component)          # 묶지 않는 성분은 자기 자신이 한 묶음
        groups.setdefault(key, []).append(component)
    reps, ties = [], []
    for members in groups.values():
        members.sort(key=lambda c: (colour.get(c[1], -1), c[1]))        # 대표 = 구조 색(정준 위치) 최소 -- 이름 치환에 불변
        reps.append(members[0])
        if len(members) > 1:
            ties.append((members[0], tuple(members[1:])))
    return tuple(reps), tuple(ties)
