"""출발 구간 읽기 묶음 (설계 41 §6 입력: S1·S1v·GB4 필드, spec, LUT; 40 §2.4.7 `StartContext` 행).

진입점: `start_view(projection, spec, inputs, pdk_decl, lut) -> StartView`(출발 구간 계산 블록 `start_intervals` 가 블록 호출 안에서 한 번).

* `projection` = 블록 투영 -- S1 소자·노드 열, graph 대칭 블록 `dc_colour`, 쓰기 계획 `dc_coord`·`dc_current_basis`, 커널 구조 파생 `graph/kernel: theta_schema·l_ties`,
  탐색 정의역 `graph/kernel: search_domain`(L 칸·θ 상자·W_min), 면적 선언 `passive_area_decl`, S1v `graph/s1v: views`, GB4 `graph/ach: gain_checks·local_inputs`(없으면 이득 L 하한이
  비활성 사유로 남는다). 블록이 선언한 필드만 읽는다(옛 `build_start_context(s1v, ach, kctx, ...)` 의 객체 입력을 대체 -- 사본 없음).
* `spec` = `SizingSpecDoc`, `inputs` = sizing `DcInputs`, `pdk_decl` = core `PdkDecl`, `lut` = sizing `LutAccess`.
* 목표 `gbw_hz`·`pm_deg` 는 spec `compensation_targets` 의 값을 먼저 읽고, 없으면 판정 제약 `gbw_ss_hz >= v`·`pm_ss_deg >= v` 의 값(여럿이면 가장 엄격한 것)을 쓴다.
  둘 다 없으면 None(속도 경계·매크로 목표 비활성, 41 §6.3).
* 면적 예산은 `area_search_m2 <= v` 중 가장 작은 v(결정 11). 전달 뷰 = 첫 `transfer` 뷰 중 블록이 있는 것(U9 `achievability` 와 같은 선택).
* 소자 순서는 구조 색 `dc_colour` 순(동률은 이름) -- 이름 치환이 합산 순서·결과에 영향을 주지 않게 한다.
* `points` 는 비어 있다(소자 동작점은 블록이 헤드룸 예산 뒤 정해 `dataclasses.replace` 로 채운다).
"""
import math

from gmid_engine.graph import ELEMENT_MOS, S1V_KEY
from gmid_engine.metrics import ACH_KEY, ParamTables, block_spec
from gmid_engine.sizing import DC_KEY, DEP_PARALLEL, KERNEL_KEY, THETA_L

from .current_box import current_box
from .start_values import SRC_GAIN_L, WHY_NO_CERT, WHY_NO_TARGET, DeviceInfo, GainInputs, StartView

_VIEW_TRANSFER = "transfer"
_KEY_GBW = "gbw_target_hz"
_KEY_PM = "pm_target_deg"
_METRIC_GBW = "gbw_ss_hz"
_METRIC_PM = "pm_ss_deg"
_METRIC_AREA = "area_search_m2"
_METRIC_GAIN = "gain_ss_db"
_CERTIFIED = "certified"      # U9 BlockBound.status (metrics/achievability_types.py STATUS_CERTIFIED; 공개 API 가 내보내지 않아 같은 문자열)
_FIELD_BOUNDS = "theta_bounds"


def _target(spec, key, metric):
    for name, decl in spec.compensation_targets:
        if name == key and getattr(decl, "value", None) is not None:
            return float(decl.value)
    values = [float(c.value) for c in spec.judged_constraints if c.metric == metric and c.op == ">=" and c.value is not None]
    return max(values) if values else None


def _gain_inputs(p, views, lut, constraints):
    """이득 L 하한(설계 41 §6.4-1)의 입력 묶음. 이득 제약이 없거나 A_i,max 가 하나라도 인증되지 않으면 (None, ((SRC_GAIN_L, 사유),)) -- 조용히 빠지지 않고 보고 표 비활성 사유로 간다(H3).
    목표 g_i = G·A_i,max/ΣA_max (dB). 입력 묶음은 GB4 필드 `graph/ach: local_inputs`(U9 와 같은 값), 블록 대상은 U9 와 같은 함수(`block_spec`)로 만든다."""
    if not any(m == _METRIC_GAIN and op == ">=" for m, op, _v in constraints):
        return None, ((SRC_GAIN_L, WHY_NO_TARGET),)
    gain = dict(p.column("graph", "gain_checks")).get(ACH_KEY)
    view = next((v for v in views if v.kind == _VIEW_TRANSFER), None)
    if gain is None or not gain.blocks or view is None or len(view.blocks) != len(gain.blocks) or any(b.status != _CERTIFIED for b in gain.blocks):
        return None, ((SRC_GAIN_L, WHY_NO_CERT),)
    local = p.value("graph", ACH_KEY, "local_inputs").view
    total = float(sum(b.a_max_db for b in gain.blocks))
    goal = max(float(v) for m, op, v in constraints if m == _METRIC_GAIN and op == ">=")
    blocks = tuple((block_spec(view, block, local), goal * bound.a_max_db / total) for block, bound in zip(view.blocks, gain.blocks))
    return GainInputs(local, ParamTables(lut.memo, local.grids, "upper", "max"), blocks), ()


def start_view(projection, spec, inputs, pdk_decl, lut):
    p = projection
    domain = p.value("graph", KERNEL_KEY, "search_domain")
    classes = dict(p.column("device", "element_class"))
    kinds = dict(p.column("device", "kind"))
    pins = {name: dict(value) for name, value in p.column("device", "pins")}
    bulk = {name: res.net for name, res in p.column("device", "bulk")}
    colour = dict(p.column("device", "dc_colour"))
    # L 주인: S1v L 동치류(`l_ties` 멤버 -> 주인)와 자기동형 궤도 묶음(`domain.ties` 멤버 -> 대표)을 차례로 따라간 θ L 성분의 소자 -- 같은 소자 L 은 한 변수다.
    rep_of = {member: rep for rep, members in domain.ties for member in members}
    class_owner = dict(p.value("graph", KERNEL_KEY, "l_ties"))
    owner = {}
    for name in classes:
        component = (THETA_L, class_owner.get(name, name))
        owner[name] = rep_of.get(component, component)[1]
    coord = dict(p.column("device", "dc_coord"))

    def group_root(name):
        seen = set()
        while coord[name].relation == DEP_PARALLEL and coord[name].partner in coord and name not in seen:
            seen.add(name)
            name = coord[name].partner
        return name

    devices = tuple(DeviceInfo(name, kinds[name], lut.memo.lut.cap_map[kinds[name]].w_key, pins[name]["d"], pins[name]["g"], pins[name]["s"], bulk.get(name),
                               owner.get(name, name), colour[name], group_root(name))
                    for name in sorted((n for n, c in classes.items() if c == ELEMENT_MOS and n in coord), key=lambda n: (colour[n], n)))      # 쓰기 계획이 연 MOS(`off` 선언 소자는 계획에 없다)
    rails = frozenset(net for net, flag in p.column("node", "is_rail") if flag)
    supplies = dict(spec.supplies_v)
    constraints = tuple((c.metric, c.op, float(c.value)) for c in spec.judged_constraints if c.metric is not None and c.value is not None)
    budgets = [value for metric, op, value in constraints if metric == _METRIC_AREA and op == "<="]
    views = dict(p.column("graph", "views")).get(S1V_KEY, ())
    transfer = next((v for v in views if v.kind == _VIEW_TRANSFER and v.blocks), None)
    search = spec.search if isinstance(spec.search, tuple) else ()
    bounds = next((s.value for s in search if s.field == _FIELD_BOUNDS and s.value), ())
    gain_inputs = _gain_inputs(p, views, lut, constraints)         # (GainInputs 또는 None, 비활성 사유)
    schema = p.value("graph", KERNEL_KEY, "theta_schema")
    return StartView(
        devices, {d.name: d for d in devices}, classes, kinds, pins, rails,
        {r: float(supplies[r]) for r in sorted(rails) if r in supplies}, dict(p.column("node", "dc_colour")), constraints,
        _target(spec, _KEY_GBW, _METRIC_GBW), _target(spec, _KEY_PM, _METRIC_PM), min(budgets) if budgets else None, transfer, owner,
        p.value("graph", DC_KEY, "dc_current_basis"), dict(inputs.element_values),
        {z.resistor: z for z in schema.zero_cancel}, dict(inputs.node_targets), inputs.input_dc_v,
        p.value("graph", KERNEL_KEY, "passive_area_decl"), {b.element: (b.lo, b.hi) for b in bounds}, dict(domain.l_cells),
        {n: d for n, d in p.column("node", "port_direction") if d is not None},
        {n: r for n, r in p.column("node", "port_role") if r is not None},
        {v.component: ((math.exp(v.lo), math.exp(v.hi)) if v.log else (v.lo, v.hi)) for v in domain.variables},
        {k: current_box(lut, k) for k in sorted({d.kind for d in devices})}, domain.w_min_m, pdk_decl, lut.memo, *gain_inputs, {})
