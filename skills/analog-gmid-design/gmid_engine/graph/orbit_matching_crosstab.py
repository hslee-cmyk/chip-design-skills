"""궤도 ↔ matching 대조 표 (설계 40 §6-5 '불변식', 계획 DEC-97 (5), 사용자 결정 2026-10-08 '정준 라벨링 + 대칭 변수 묶음').

진입점: `orbit_matching_crosstab(s1) -> OrbitMatchingCrosstab`.

궤도와 matching 그룹 사이에는 포함 관계를 불변식으로 두지 않는다(비율 미러는 궤도가 아니고, 반회로 대응 궤도는 matching 그룹 하나가 아니다). 대신 이 표를 보고한다.
* 읽는 것: S1 대칭 블록 필드 `graph/s1: orbits`(원소 궤도), `graph/s1: matching_groups`, `device.element_class`. 다시 계산하지 않는다.
* `orbits` = MOS 궤도마다 (궤도 멤버 이름 tuple, 그 궤도가 걸친 matching 레코드 ((kind, 멤버), ...)) -- 궤도 멤버 이름순. 수동소자·이상원 궤도는 matching 대상이 아니므로 뺀다.
* `records` = matching 레코드마다 (kind, 멤버, 그 레코드의 MOS 멤버가 걸친 궤도 (궤도 멤버 tuple, ...)) -- 레코드 순서는 S1 그대로.
* 이름을 판정에 쓰지 않는다(이름은 표의 표시일 뿐이고 궤도 id 가 같은지만 본다).
"""
import dataclasses

from .s1_values import ELEMENT_MOS, GRAPH_KEY


@dataclasses.dataclass(frozen=True)
class OrbitMatchingCrosstab:
    """`orbits` = ((궤도 멤버 tuple, ((kind, 멤버 tuple), ...)), ...), `records` = ((kind, 멤버 tuple, (궤도 멤버 tuple, ...)), ...)."""

    orbits: tuple
    records: tuple


def orbit_matching_crosstab(s1):
    classes = dict(s1.column("device", "element_class"))
    orbit = {name: o for name, o in s1.value("graph", GRAPH_KEY, "orbits").devices if classes[name] == ELEMENT_MOS}
    members = {}
    for name, o in orbit.items():
        members.setdefault(o, []).append(name)
    label = {o: tuple(sorted(names)) for o, names in members.items()}
    groups = s1.value("graph", GRAPH_KEY, "matching_groups")
    records = tuple((g.kind, g.members, tuple(sorted({label[orbit[m]] for m in g.members if m in orbit}))) for g in groups)
    rows = tuple((label[o], tuple((g.kind, g.members) for g in groups if any(orbit.get(m) == o for m in g.members)))
                 for o in sorted(label, key=lambda o: label[o]))
    return OrbitMatchingCrosstab(rows, records)
