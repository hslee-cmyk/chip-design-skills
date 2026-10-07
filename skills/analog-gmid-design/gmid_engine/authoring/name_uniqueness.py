"""원소 이름 유일성 IC3 (SD `check_topology_name_uniqueness` 이식 + 이상원 포함, 설계 design_mod3_s1_graph 2.1).

진입점: `check_name_uniqueness(devices, passives, sources) -> tuple[SchemaHit]`.

소자·수동소자·이상원 이름을 한 이름 공간으로 본다(옛 함수는 이상원을 빼고 수동소자끼리 중복도 보지 않았다):
* `name_duplicate` -- 같은 이름이 두 번 이상(어느 종류 사이든). 이름마다 하나, 겹친 종류를 메시지에 적는다.
* `name_case_collision` -- casefold 가 같은데 글자 그대로는 다른 이름 묶음(리포트·딕셔너리에서 서로 덮어쓰는 사고).
"""
from gmid_engine.core import sorted_items

from .topology_model import SchemaHit


def check_name_uniqueness(devices, passives, sources):
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
    by_fold = {}
    for name in owners:
        by_fold.setdefault(name.casefold(), set()).add(name)
    for _fold, names in sorted_items(by_fold):
        if len(names) > 1:
            hits.append(SchemaHit("name_case_collision", ", ".join(sorted(names)),
                                  "대소문자만 다른 원소 이름: " + repr(sorted(names)), tuple(names)))
    return tuple(hits)
