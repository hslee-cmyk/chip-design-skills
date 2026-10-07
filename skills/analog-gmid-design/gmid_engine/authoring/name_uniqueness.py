"""원소 이름 유일성 IC3 (SD `check_topology_name_uniqueness` 이식 + 이상원 포함, 설계 design_mod3_s1_graph 2.1)
+ 넷 이름 대소문자 충돌(reference_review G4-09·G5-10, FSM 155행 '0번 net 이름 대소문자 스캔').

진입점: `check_name_uniqueness(devices, passives, sources, supply_nets=(), port_nets=()) -> tuple[SchemaHit]`.

소자·수동소자·이상원 이름을 한 이름 공간으로 본다(옛 함수는 이상원을 빼고 수동소자끼리 중복도 보지 않았다):
* `name_duplicate` -- 같은 이름이 두 번 이상(어느 종류 사이든). 이름마다 하나, 겹친 종류를 메시지에 적는다.
* `name_case_collision` -- casefold 가 같은데 글자 그대로는 다른 이름 묶음(리포트·딕셔너리에서 서로 덮어쓰는 사고).

넷 이름은 원소 이름과 다른 이름 공간이다(원소 이름과 넷 이름이 casefold 로 같아도 위반 아님):
* `net_case_collision` -- MOS d/g/s/선언 bulk, 수동소자·이상원 terminals, `supply_nets` 문자열, `ports` 키를 합친 넷
  이름 집합에서 casefold 가 같고 글자는 다른 묶음마다 하나. 자동 통일하지 않는다(사람이 원본을 고친다). 레일 별칭
  예외도 없다(엔진에 별칭 개념이 없다). 오라클 C4('대소문자만 다른 두 넷' 막힘)와 같은 판정을 로드 단계에서 한다.
`supply_nets`·`port_nets` 는 넷 이름 문자열 iterable 이다(호출자가 원본 선언에서 문자열만 넘긴다 -- 그 선언이 다른
게이트에서 거부돼도 이 검사는 돈다).
hits 순서: 원소 위반(`name_duplicate` 이름순, `name_case_collision` casefold 순) 다음 `net_case_collision` casefold 순.
"""
from gmid_engine.core import sorted_items

from ._terminal_nets import mos_terminal_nets, two_terminal_nets
from .topology_model import SchemaHit


def _case_groups(names):
    by_fold = {}
    for name in names:
        by_fold.setdefault(name.casefold(), set()).add(name)
    return [group for _fold, group in sorted_items(by_fold) if len(group) > 1]


def check_name_uniqueness(devices, passives, sources, supply_nets=(), port_nets=()):
    owners = {}
    for group, items in (("netlist", devices), ("passive_elements", passives), ("ideal_sources", sources)):
        for item in items:
            owners.setdefault(item.name, []).append(group)
    hits = []
    for name, groups in sorted_items(owners):
        if len(groups) > 1:
            hits.append(SchemaHit("name_duplicate", name,
                                  "원소 이름 " + repr(name) + " 이 " + str(len(groups)) + "번 나온다(" + ", ".join(groups) + ")",
                                  (name,)))
    for names in _case_groups(owners):
        hits.append(SchemaHit("name_case_collision", ", ".join(sorted(names)),
                              "대소문자만 다른 원소 이름: " + repr(sorted(names)), tuple(names)))
    nets = (mos_terminal_nets(devices) | two_terminal_nets(tuple(passives) + tuple(sources))
            | frozenset(supply_nets) | frozenset(port_nets))
    for names in _case_groups(nets):
        hits.append(SchemaHit("net_case_collision", ", ".join(sorted(names)),
                              "대소문자만 다른 넷 이름(자동 통일 없음 -- 원본을 고칠 것): " + repr(sorted(names)),
                              tuple(names)))
    return tuple(hits)
