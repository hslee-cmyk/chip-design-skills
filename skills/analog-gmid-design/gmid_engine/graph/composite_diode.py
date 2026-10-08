"""복합 diode (D1) -- 같은 DC 가지를 걸어 자기 gate 넷에 닿는 MOS (설계 41 §1.12.1, 40 §3.2-3).

진입점: `composite_diodes(projection) -> tuple[CompositeDiode]`  (S1 `device`·`node` 열만 읽는다 -- DC 역할 계산 블록 `s1_dc_roles` 가 부른다).

**DC 가지 걷기**(connectivity 만, 이름 없음): MOS X 의 gate 넷 g, drain 넷 d. 출발 w = d, 방금 들어온 단자 = X.drain.
* w == g 이면 성공 -- 지난 원소가 하나 이상이면 X 는 **복합 diode 소자**다(지난 원소 0 = gate == drain 단순 diode 는 기존 규칙 1).
* 아니면 w 가 (i) 레일·포트·이상원 단자 넷이 아니고 (ii) **DC 전류 단자**(MOS 채널 단자 d·s, DC 를 통하는 2단자 수동소자 단자; gate·커패시터 단자는 세지 않음)가
  정확히 둘이어야 한다. 그러면 방금 들어온 단자가 아닌 쪽 단자의 원소를 지나 그 반대쪽 넷으로 간다. 만족하지 않거나 이미 지난 넷·원소에 다시 오면 실패.
* 걸음 수는 원소 수를 넘지 않으므로 따로 상한을 두지 않는다.

**묶음**: X 와 걷기가 지난 원소(MOS·저항, 지나간 단순 diode 포함)가 한 묶음이고 원소를 공유하는 묶음은 합친다(union-find). 묶음 안에서 다른 복합 diode
소자의 걷기에 들지 않는 복합 diode 소자가 **기준**(`reference`), 나머지가 **캐스코드 기준 멤버**(`cascode_members`)다.
소비: `dc_roles`(규칙 1c, 같은 gate·source 묶음의 나머지 멤버가 바이어스 전류원으로 갈린다), `net_model`(복합 diode 단자 = 미러 입력·diode_load 셀·루프 (1.6)).
"""
import dataclasses

from gmid_engine.authoring import DC_CONDUCTING_PASSIVE_KINDS

from .s1_values import (
    ELEMENT_MOS,
    ELEMENT_PASSIVE,
    ELEMENT_SOURCE,
    MOS_DRAIN,
    MOS_GATE,
    MOS_SOURCE,
)
from .s1v_values import PAIR      # 직렬 노드의 DC 전류 단자 수(들어온 쪽, 나가는 쪽)


@dataclasses.dataclass(frozen=True)
class CompositeDiode:
    """묶음 하나. `members` = MOS·수동소자 이름순, `reference` = 기준 복합 diode 소자 이름순, `cascode_members` = 캐스코드 기준 멤버 이름순,
    `walk` = ((복합 diode 소자, 걷기가 지난 원소 tuple(지난 순서)), ...) 소자 이름순."""

    members: tuple
    reference: tuple
    cascode_members: tuple
    walk: tuple


def _dc_terminals(pins, kind, element_class):
    """넷 -> [(원소, 단자)] DC 전류 단자만 -- MOS d·s, DC 를 통하는 수동소자 양 단자. 반대 단자 표 {(원소, 단자): (넷, 반대 단자)} 를 함께 돌려준다."""
    at = {}
    other = {}
    for name, cls in element_class:
        if cls == ELEMENT_MOS:
            channel = dict(pins[name])
            ends = (MOS_DRAIN, MOS_SOURCE)
        elif cls == ELEMENT_PASSIVE and kind[name] in DC_CONDUCTING_PASSIVE_KINDS:
            channel = dict(pins[name])
            ends = tuple(channel)
        else:
            continue
        for end, opposite in zip(ends, reversed(ends)):
            at.setdefault(channel[end], []).append((name, end))
            other[(name, end)] = (channel[opposite], opposite)
    return at, other


def _walk(start, gate, fixed, at, other, entered):
    """성공하면 지난 원소 tuple, 실패하면 None. `entered` = 방금 들어온 (원소, 단자)."""
    path = []
    nets = {start}
    net = start
    while net != gate:
        terminals = at.get(net, ())
        if net in fixed or len(terminals) != len(PAIR):          # 레일·포트·이상원 넷이거나 DC 전류 단자가 둘이 아님
            return None
        leaving = [t for t in terminals if t != entered]
        if len(leaving) != 1 or leaving[0][0] in path:
            return None
        element, end = leaving[0]
        path.append(element)
        net, opposite = other[(element, end)]
        if net != gate and net in nets:
            return None
        nets.add(net)
        entered = (element, opposite)
    return tuple(path)


def composite_diodes(projection):
    element_class = tuple(projection.column("device", "element_class"))
    kind = dict(projection.column("device", "kind"))
    pins = dict(projection.column("device", "pins"))
    at, other = _dc_terminals(pins, kind, element_class)
    fixed = {net for net, flag in projection.column("node", "is_rail") if flag}
    fixed.update(net for net, direction in projection.column("node", "port_direction") if direction is not None)
    for name, cls in element_class:
        if cls == ELEMENT_SOURCE:
            fixed.update(net for _, net in pins[name])
    walks = {}
    for name, cls in element_class:
        if cls != ELEMENT_MOS:
            continue
        channel = dict(pins[name])
        path = _walk(channel[MOS_DRAIN], channel[MOS_GATE], fixed, at, other, (name, MOS_DRAIN))
        if path:
            walks[name] = path
    parent = {}

    def find(x):
        parent.setdefault(x, x)
        while parent[x] != x:
            parent[x] = parent[parent[x]]
            x = parent[x]
        return x

    for name, path in walks.items():
        for element in path:
            parent[find(element)] = find(name)
    groups = {}
    for name in walks:
        groups.setdefault(find(name), []).append(name)
    result = []
    for diodes in groups.values():
        walked = {e for d in diodes for e in walks[d]}
        reference = tuple(sorted(d for d in diodes if d not in walked))
        cascode = tuple(sorted(d for d in diodes if d in walked))
        if not reference:                 # 서로의 걷기에 드는 순환 -- 기준을 하나로 못 정하므로 모두 기준으로 둔다
            reference, cascode = cascode, ()
        result.append(CompositeDiode(tuple(sorted(set(diodes) | walked)), reference, cascode,
                                     tuple((d, walks[d]) for d in sorted(diodes))))
    return tuple(sorted(result, key=lambda c: c.members))
