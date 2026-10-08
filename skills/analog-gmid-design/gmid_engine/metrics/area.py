"""탐색 축 면적 (설계 design_mod1_lut_mod5_mna 3.4 `area_search_m2`, 계획 DEC-79 (a)).

진입점: `area_search`.

`area_search_m2` = Σ W·L(게이트) + 선언 수동소자 면적(값 × PDK 선언 단위 면적 + 소자마다 한 번 더하는 머리 면적, U-36·Q9). 단위 면적 선언이 없는 수동소자는
그 항을 0 으로 두고 label 을 `passive_area_undeclared` 에 남긴다(매 실행 보고 -- 조용히 빠지지 않는다).
"""
from .mna_types import AreaSearch
from .records import GateArea, PassiveArea


def area_search(gates, passives):
    """`GateArea` tuple, `PassiveArea` tuple -> `AreaSearch`."""
    if not isinstance(gates, tuple) or not isinstance(passives, tuple):
        raise TypeError("area_search 는 GateArea tuple, PassiveArea tuple 을 받는다")
    for g in gates:
        if not isinstance(g, GateArea):
            raise TypeError("area_search: gates 원소는 GateArea 여야 한다: %r" % (g,))
    for p in passives:
        if not isinstance(p, PassiveArea):
            raise TypeError("area_search: passives 원소는 PassiveArea 여야 한다: %r" % (p,))
    gate_area = sum(g.w_m * g.l_m for g in gates)
    passive_area = sum(p.value * p.area_per_unit_m2 + p.head_area_m2 for p in passives if p.area_per_unit_m2 is not None)
    undeclared = tuple(sorted(p.label for p in passives if p.area_per_unit_m2 is None))
    return AreaSearch(
        area_search_m2=gate_area + passive_area,
        gate_area_m2=gate_area,
        passive_area_m2=passive_area,
        passive_area_undeclared=undeclared,
    )
