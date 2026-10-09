"""출발 구간 입력 묶음 (설계 41 §6 입력: S1/S1v, spec, LUT 곡선, A6 상한표).

진입점: `build_start_context(s1v, ach, kctx, spec, pdk_decl, domain) -> StartContext`(S0 당 1회).

* `s1v` = `graph.build_s1v` 결과(단계 A; S1 은 `kctx.base` 가 담고 있다), `ach` = U9 `Achievability`(단계 B, 없으면 None -- 이득 L 하한이 비활성 사유로 남는다),
  `kctx` = `sizing.build_kernel_context` 결과(쓰기 계획·전류 기저·θ 스키마·L 동치류 `l_ties`), `spec` = `SizingSpecDoc`, `domain` = `search_domain` 결과(L 칸·θ 상자).
* 목표 `gbw_hz`·`pm_deg` 는 spec `compensation_targets` 의 값을 먼저 읽고, 없으면 판정 제약 `gbw_ss_hz >= v`·`pm_ss_deg >= v` 의 값(여럿이면 가장 엄격한 것)을 쓴다.
  둘 다 없으면 None(속도 경계·매크로 목표 비활성, 41 §6.3).
* 면적 예산은 `area_search_m2 <= v` 중 가장 작은 v(결정 11). 전달 뷰 = 첫 `transfer` 뷰 중 블록이 있는 것(U9 `achievability` 와 같은 선택).
* 소자 순서는 구조 색 `dc_colour` 순(동률은 이름) -- 이름 치환이 합산 순서·결과에 영향을 주지 않게 한다.
"""
import math

from gmid_engine.graph import ELEMENT_MOS
from gmid_engine.sizing import DC_KEY, DEP_PARALLEL, THETA_L

from .area_decl import passive_area_decl
from .current_box import current_box
from .iv_curves import CurveBook
from .start_values import DeviceInfo, StartContext

_VIEW_TRANSFER = "transfer"
_KEY_GBW = "gbw_target_hz"
_KEY_PM = "pm_target_deg"
_METRIC_GBW = "gbw_ss_hz"
_METRIC_PM = "pm_ss_deg"
_METRIC_AREA = "area_search_m2"
_FIELD_BOUNDS = "theta_bounds"


def _target(spec, key, metric):
    for name, decl in spec.compensation_targets:
        if name == key and getattr(decl, "value", None) is not None:
            return float(decl.value)
    values = [float(c.value) for c in spec.judged_constraints if c.metric == metric and c.op == ">=" and c.value is not None]
    return max(values) if values else None


def build_start_context(s1v, ach, kctx, spec, pdk_decl, domain):
    classes = dict(kctx.base.column("device", "element_class"))
    kinds = dict(kctx.base.column("device", "kind"))
    pins = {name: dict(value) for name, value in kctx.base.column("device", "pins")}
    bulk = {name: res.net for name, res in kctx.base.column("device", "bulk")}
    colour = dict(kctx.base.column("device", "dc_colour"))
    # L 주인: S1v L 동치류(`l_ties` 멤버 -> 주인)와 자기동형 궤도 묶음(`domain.ties` 멤버 -> 대표)을 차례로 따라간 θ L 성분의 소자 -- 같은 소자 L 은 한 변수다.
    rep_of = {member: rep for rep, members in domain.ties for member in members}
    class_owner = dict(kctx.l_ties)
    owner = {}
    for name in classes:
        component = (THETA_L, class_owner.get(name, name))
        owner[name] = rep_of.get(component, component)[1]
    w_keys = dict(kctx.lut.w_keys)
    coord = dict(kctx.base.column("device", "dc_coord"))

    def group_root(name):
        seen = set()
        while coord[name].relation == DEP_PARALLEL and coord[name].partner in coord and name not in seen:
            seen.add(name)
            name = coord[name].partner
        return name

    devices = tuple(DeviceInfo(name, kinds[name], w_keys[kinds[name]], pins[name]["d"], pins[name]["g"], pins[name]["s"], bulk.get(name),
                               owner.get(name, name), colour[name], group_root(name))
                    for name in sorted((n for n, c in classes.items() if c == ELEMENT_MOS), key=lambda n: (colour[n], n)))
    rails = frozenset(net for net, flag in kctx.base.column("node", "is_rail") if flag)
    supplies = dict(spec.supplies_v)
    constraints = tuple((c.metric, c.op, float(c.value)) for c in spec.judged_constraints if c.metric is not None and c.value is not None)
    budgets = [value for metric, op, value in constraints if metric == _METRIC_AREA and op == "<="]
    transfer = next((v for v in s1v.views if v.kind == _VIEW_TRANSFER and v.blocks), None)
    search = spec.search if isinstance(spec.search, tuple) else ()
    bounds = next((s.value for s in search if s.field == _FIELD_BOUNDS and s.value), ())
    return StartContext(
        CurveBook(kctx.lut.memo, w_keys), devices, {d.name: d for d in devices}, classes, kinds, pins, rails,
        {r: float(supplies[r]) for r in sorted(rails) if r in supplies}, dict(kctx.base.column("node", "dc_colour")), constraints,
        _target(spec, _KEY_GBW, _METRIC_GBW), _target(spec, _KEY_PM, _METRIC_PM), min(budgets) if budgets else None, transfer, owner,
        kctx.base.value("graph", DC_KEY, "dc_current_basis"), dict(kctx.inputs.element_values),
        {z.resistor: z for z in kctx.schema.zero_cancel}, dict(kctx.inputs.node_targets), kctx.inputs.input_dc_v,
        passive_area_decl(kctx, spec, pdk_decl), {b.element: (b.lo, b.hi) for b in bounds}, dict(domain.l_cells), ach,
        {n: d for n, d in kctx.base.column("node", "port_direction") if d is not None},
        {n: r for n, r in kctx.base.column("node", "port_role") if r is not None},
        {v.component: ((math.exp(v.lo), math.exp(v.hi)) if v.log else (v.lo, v.hi)) for v in domain.variables},
        {k: current_box(kctx.lut, k) for k in sorted({d.kind for d in devices})}, domain.w_min_m, pdk_decl, kctx.lut.memo, w_keys)

