"""θ 성분의 자기동형 궤도 묶음 (사용자 결정 2026-10-08, CONTRACT 3.24).

진입점: `orbit_ties(dc_ctx, components, untied, symmetry=None) -> (대표 성분 tuple, ties)`.

* `components` = θ 스키마 성분 (종류, 키) 열.
* **θ 전류 성분**: 자기동형이 만드는 부호 묶음·구조적 0(`current_symmetry`) -- `symmetry` 를 안 주면 여기서 만든다. 묶인 구성원은 ties 에, 구조적 0 은 대표에서
  빠진다(탐색 변수가 아니다).
* **그 밖 성분**(ln_idu·L·y·저항·커패시터 값): 키가 원소(소자)면 graph `orbits.devices`, `y` 의 키가 넷이면 `orbits.nodes` 의 궤도 id 로 보아 같은 (종류, 궤도) 성분을 한
  변수로 묶는다(값은 같다). 대표 = 구조 색 `dc_colour`(1-WL 색 + 정준 위치, 정점마다 유일) 최소.
* `untied` = 묶지 않을 원소 이름 tuple(spec `search.untie_orbits`): 그 원소의 궤도는 묶지 않는다(검사는 `current_symmetry`: 원소 없음 `untie_element_unknown`,
  궤도가 원소 하나뿐 `untie_orbit_trivial`).
* 반환 `ties` = ((대표, (구성원, ...)), ...) 대표의 구조 색 순서. 구성원의 부호(−1)와 구조적 0 은 `current_symmetry` 의 `negated`·`zeros` 다.
"""
from gmid_engine.graph import GRAPH_KEY
from gmid_engine.sizing import THETA_CURRENT, THETA_Y

from .current_symmetry import current_symmetry


def _orbit_of(component, device_orbit, node_orbit):
    kind, key = component
    table = node_orbit if kind == THETA_Y else device_orbit
    if key in table:
        return ("n" if table is node_orbit else "e", table[key])
    return None


def orbit_ties(dc_ctx, components, untied, symmetry=None):
    symmetry = current_symmetry(dc_ctx, untied) if symmetry is None else symmetry
    orbits = dc_ctx.base.value("graph", GRAPH_KEY, "orbits")          # graph 대칭 블록 필드(40 §2.4.8)
    device_orbit, node_orbit = dict(orbits.devices), dict(orbits.nodes)
    colour = {**dict(dc_ctx.base.column("node", "dc_colour")), **dict(dc_ctx.base.column("device", "dc_colour"))}
    free = {device_orbit[name] for name in untied}
    dropped = {m for _rep, members in symmetry.ties for m in members} | set(symmetry.zeros)
    groups = {}
    for component in components:
        if component[0] == THETA_CURRENT:
            continue
        orbit = _orbit_of(component, device_orbit, node_orbit)
        key = (component[0], orbit)
        if orbit is None or (orbit[0] == "e" and orbit[1] in free):
            key = (component[0], None, component)          # 묶지 않는 성분은 자기 자신이 한 묶음
        groups.setdefault(key, []).append(component)
    reps = [c for c in components if c[0] == THETA_CURRENT and c not in dropped]
    ties = list(symmetry.ties)
    for members in groups.values():
        members.sort(key=lambda c: (colour.get(c[1], -1), c[1]))        # 대표 = 구조 색(정준 위치) 최소 -- 이름 치환에 불변
        reps.append(members[0])
        if len(members) > 1:
            ties.append((members[0], tuple(members[1:])))
    ties.sort(key=lambda t: (t[0][0], colour.get(t[0][1], -1), t[0][1]))
    return tuple(reps), tuple(ties)
