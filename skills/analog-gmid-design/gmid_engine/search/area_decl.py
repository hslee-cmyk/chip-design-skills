"""수동소자 면적 선언 -- 면적 축 `area_search_m2` 의 수동소자 항 입력 (사용자 결정 11, 2026-10-08).

진입점: `passive_area_decl(dc_ctx, spec, pdk_decl) -> PassiveAreaDecl`(S0 당 1회, `build_search_context` 가 부른다).

* 제외 = spec `element_values.<원소>.measurement_load == true` 인 수동소자(측정 부하 CL·RL -- 설계가 정하는 값이 아니다). 이름이
  아니라 spec 선언이 정한다.
* 단위 면적 = PDK 선언의 단위 면적 용량(`mim_cap_density_f_per_m2`)이 있고 소자 kind 가 커패시터면 1 / 면적 용량 [m²/F].
  저항은 PDK 에 단위 면적 선언이 없어 넣지 않는다(`passive_area_undeclared` 로 매 실행 보고 -- 조용히 0 으로 빠지지 않는다).
  PDK 선언에 그 quantity 가 없으면 커패시터도 넣지 않는다(같은 보고).
"""
from gmid_engine.core import SchemaRejectedError
from gmid_engine.graph import ELEMENT_PASSIVE
from gmid_engine.metrics import PassiveAreaDecl

CAP_DENSITY_QUANTITY = "mim_cap_density_f_per_m2"     # PDK 선언 이름(sky130_pdk_decl.json)
_CAPACITOR_KIND = "capacitor"


def _cap_density(pdk_decl):
    try:
        return pdk_decl.value(CAP_DENSITY_QUANTITY)
    except SchemaRejectedError as exc:
        if dict(exc.record.detail).get("reason") != "pdk_quantity_undeclared":
            raise
        return None


def passive_area_decl(dc_ctx, spec, pdk_decl):
    classes = dict(dc_ctx.base.column("device", "element_class"))
    kinds = dict(dc_ctx.base.column("device", "kind"))
    loads = frozenset(e.name for e in spec.element_values if e.measurement_load)
    density = _cap_density(pdk_decl)
    unit, excluded = [], []
    for name in sorted(n for n, c in classes.items() if c == ELEMENT_PASSIVE):
        if name in loads:
            excluded.append(name)
        elif density is not None and kinds[name] == _CAPACITOR_KIND:
            unit.append((name, 1.0 / density))
    return PassiveAreaDecl(tuple(unit), tuple(excluded))
