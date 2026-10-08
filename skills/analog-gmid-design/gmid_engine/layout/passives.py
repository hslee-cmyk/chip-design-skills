"""MOD7 수동소자 면적 입력 -- 판정 축 면적의 수동소자 블록(MIM 커패시터·poly 저항)을 탐색 축과 같은 정본 식으로 만든다 (U12, D-LY4).

진입점: `passives_from_decl(area_decl, values) -> tuple[LayoutPassive]`.

`area_decl` = `metrics.PassiveAreaDecl`(search `passive_area_decl` 이 PDK 선언 MIM 밀도·poly 저항 양과 spec `measurement_load` 로 만든 것),
`values` = {수동소자 이름: 값(F 또는 Ω)}. 면적 = `metrics.PassiveArea.area_m2`(값 x 단위 면적 + 머리 면적) -- 탐색 축 `area_search` 와
같은 식 하나라 여기서 다시 쓰지 않는다. 단위 면적이 선언된 소자만 만든다(측정 부하·값 없는 소자·미선언 소자는 만들지 않는다 --
탐색 축과 같은 제외). 이름순 tuple.
"""
from gmid_engine.metrics import PassiveArea

from .contract_input import LayoutPassive


def passives_from_decl(area_decl, values):
    unit = dict(area_decl.unit_area)
    heads = dict(area_decl.head_area)
    out = []
    for name in sorted(unit):
        if name in area_decl.excluded or values.get(name) is None:
            continue
        out.append(LayoutPassive(name, PassiveArea(name, values[name], unit[name], heads.get(name, 0.0)).area_m2))
    return tuple(out)
