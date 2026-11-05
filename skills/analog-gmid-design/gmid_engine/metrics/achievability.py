"""GB4 달성가능성 계산 블록 -- 탐색 전 달성 불가 판정을 S0 수준 필드 `graph/ach` 에 쓴다 (설계 41 §4, 40 §3.4·§2.4.8 v1.9.1 D2·D9, FR-8, D-GB4a~f·D-J2·D-J5;
단계 A5~A7).

진입점: `achievability`(`@compute_block`, writer `achievability`) -- `achievability(snapshot, spec, element_values, lut, count_budget)`.

* 스냅샷 = S0 수준 스냅샷(S1 + S1v 필드 + 커널 컨텍스트 블록 + `graph/kernel: search_domain·passive_area_decl`). 블록이 읽는 필드(`READS`): S1 소자·노드 열,
  graph 대칭 블록 `orbits`·`dc_colour`, 쓰기 계획 `dc_current_basis`, 커널 구조 파생 `fixed_values`·`l_ties`, S1v `views`·`l_classes`,
  탐색 정의역 `search_domain`(θ 전류 상자·자기동형 묶음·b_A -- `cur_rep`·`current_box`·`area_resolution_m2` 는 여기서 유도), 수동소자 면적 선언 `passive_area_decl`.
  extras: `spec` = `SizingSpecDoc`, `element_values` = ((원소, 선언값 | None), ...)(spec 파싱 `DcInputs.element_values`), `lut` = sizing `LutAccess`(LUT 손잡이),
  `count_budget` = 계수 예산 N_S(`search.count_budget`; metrics 가 search 보다 아래 층이라 파이프라인이 값을 만들어 넘긴다).
* writes `graph/ach`(key `ACH_KEY`): `curve_checks`, `gain_checks`(`GainCheck` | None -- 첫 전달 뷰), `area_bound`, `headroom_rows`(버퍼 창 제외), `buffer_window_report`,
  `warnings`, `reasons`(정지 근거), `verdict`(ok | infeasible), `dof`(구조 DOF만), `count_budget`, `local_inputs`(`LocalInputs` -- 출발 구간이 같은 필드를 읽는다).
  묶음 객체는 없다(v1.9.1 D2). 정지(`InfeasibleTargetError`, exit 3)는 이 블록이 아니라 부르는 쪽(파이프라인 단계 B)이 `reasons` 필드를 읽어 낸다.

**5개 계산을 같은 S0 입력으로 한 번씩 한다**(DAG 41 §0, 앞 단계 결과를 뒤가 읽지 않는다 -- r̂·A8 출발값 미사용):
1. `curve_checks` -- LUT 칸 분류 → 해법(41 §4.1).
2. `block_gain_bound` -- 주경로 블록(+ feedforward 묶음)별 gain 상한 A_i,max, 계수 예산 게이트(41 §4.2). 3. Σ 판정(41 §4.3): 모든 블록이 인증이고 Σ(A_i,max + b_i) < G 이면 정지.
   feedforward 가 있는 뷰는 20·log10(Π A_i,max + Σ_ff A_ff,max) + b < G (A_ff,max = (입력→탭 상한) × (FF 국소 격자 상한), 41 §1.12.2-6). 상한이 하나라도 미상이면 판정하지 않고 보고만.
4. `area_lower_bound` -- 인증된 면적 하한 A_lb > 예산 + b_A 이면 정지(`area_budget_below_lower_bound`, 41 §4.4).
5. `headroom_bound` -- 출력·입력·버퍼 창 상한(41 §4.6): 선언 제약의 대상 창이 인증되었고 상한 + 분해능 < 목표면 정지(`headroom_unattainable`); 선언 제약이 없는 창·입력 DC 대기는 보고만,
   버퍼 창은 `buffer_window_report`, 입력 창이 최단 L bin 에서만 열리면 경고 `icmr_window_short_l_bin`. 엣지 비용은 LUT 파생 `lut.derived(memo, "edge_costs", ...)`(LUT memo, 40 §2.4.6).
6. `dof_report` -- 구조 DOF(변수 = 비레일 노드 전압·MOS 반전 좌표·L 동치류·θ 전류·θ DC 저항, 등식 = MOS 소자 식·저항 강하·선언 노드 목표): 매칭 안 되는 등식이 있으면 정지(`overconstrained`).
인증되지 않은 값(미상)은 정지 근거로 쓰지 않고 `status`·`reason` 으로 남긴다 -- 조용히 통과하는 것이 아니라 '판정 안 함'이 보고에 드러난다.

한계(보고서 기록): 블록 gain 상한은 격자 곱 Π 가 N_S 를 넘으면 미상이다. 9회로 실측에서 Π 는 N_S(1.4e7)를 크게 넘어 거의 모든 블록이 미상이므로 `found_db`(좌표 상승 하한 추정)를 보고만 한다.
"""
import math

from gmid_engine.authoring import (
    INPUT_DIRECTION,
    OUTPUT_DIRECTION,
    ROLE_DIFFERENTIAL_OUTPUT_N,
    ROLE_DIFFERENTIAL_OUTPUT_P,
    UNTIE_ORBITS,
)
from gmid_engine.core import AMPLITUDE_DB_PER_DECADE, compute_block
from gmid_engine.graph import ELEMENT_MOS, ELEMENT_PASSIVE, GRAPH_KEY, S1V_KEY, STATUS_DERIVED, STATUS_RATIFIED
from gmid_engine.lut import derived
from gmid_engine.sizing import DC_KEY, KERNEL_KEY, REL_INPUT_POINT, THETA_CURRENT

from .achievability_types import (
    REASON_AREA,
    REASON_DOF,
    REASON_GAIN,
    ROLE_FF,
    ROLE_MAIN,
    STATUS_CERTIFIED,
    STATUS_UNKNOWN,
    VERDICT_INFEASIBLE,
    VERDICT_NO_TARGET,
    VERDICT_NOT_EXCLUDED,
    VERDICT_OK,
    VERDICT_UNDETERMINED,
    WINDOW_BUFFER,
    WINDOW_INPUT,
    WINDOW_OUTPUT,
    BlockBound,
    BlockSpec,
    GainCheck,
    LocalInputs,
)
from .area_lower_bound import area_lower_bound
from .block_gain_bound import block_gain_bound
from .block_gain_model import block_gain_model_of
from .block_param_tables import ParamTables
from .curve_checks import curve_checks
from .dof_report import STATUS_OVERCONSTRAINED, dof_report
from .headroom_bound import headroom_bound
from .s0_fields import ACH_KEY, ACH_WRITES, ACHIEVABILITY_WRITER

METRIC_GAIN = "gain_ss_db"
METRIC_AREA = "area_search_m2"
HEADROOM_METRICS = ("swing_out_v", "icmr_v", "icm_margin_v")
BLOCK_BUFFER = "buffer"
KIND_CAPACITOR = "capacitor"
KIND_RESISTOR = "resistor"
INPUT_NET = "net"
INPUT_VALUE = "value"


def _theta_currents(domain):
    """`SearchDomain` -> ({원소: (대표, 부호)}, {대표: (하한 A, 상한 A)}) -- 블록 국소 모델의 `cur_rep`·`current_box`(탐색 변수와 같은 자기동형 묶음).
    묶인 구성원은 (대표, ±1), 구조적 0 은 (None, 0)."""
    rep, box = {}, {}
    for variable in domain.variables:
        kind, key = variable.component
        if kind == THETA_CURRENT:
            box[key] = (math.exp(variable.lo), math.exp(variable.hi)) if variable.log else (variable.lo, variable.hi)
    negated = set(domain.negated)
    for head, members in domain.ties:
        if head[0] != THETA_CURRENT:
            continue
        for member in members:
            rep[member[1]] = (head[1], -1 if member in negated else 1)
    for zero in domain.zeros:
        if zero[0] == THETA_CURRENT:
            rep[zero[1]] = (None, 0)
    return rep, box


def _items(table):
    """사전 -> 키 순 (키, 값) tuple(필드 값 칸)."""
    return tuple(sorted(table.items()))


def _local_inputs(p, spec, element_values, lut, domain):
    """`LocalInputs` 필드 값(불변 tuple 칸) -- 투영 `p` 의 S1·대칭·쓰기 계획·S1v 필드, spec, LUT 와 정의역에서 한 번."""
    cls = dict(p.column("device", "element_class"))
    kind = dict(p.column("device", "kind"))
    pins = {name: dict(value) for name, value in p.column("device", "pins")}
    bulk = {name: res.net for name, res in p.column("device", "bulk") if cls.get(name) == ELEMENT_MOS}
    rails = frozenset(net for net, flag in p.column("node", "is_rail") if flag)
    orbit = dict(p.value("graph", GRAPH_KEY, "orbits").devices)
    search = spec.search if isinstance(spec.search, tuple) else ()
    untied = {name for name, _src in next((s.value for s in search if s.field == UNTIE_ORBITS and s.value), ())}
    free_orbits = {orbit[n] for n in untied if n in orbit}
    orbit_key = tuple((n, o if o not in free_orbits else ("untied", n)) for n, o in sorted(orbit.items()))
    l_label = {}
    for cls_ in dict(p.column("graph", "l_classes")).get(S1V_KEY, ()):
        if cls_.status in (STATUS_DERIVED, STATUS_RATIFIED):
            for member in cls_.members:
                l_label[member] = cls_.owner
    basis = p.value("graph", DC_KEY, "dc_current_basis")
    rows = tuple((name, tuple((t.source, t.num / t.den) for t in terms)) for name, terms in basis.rows)
    boxes = {}
    for bound in (next((s.value for s in search if s.field == "theta_bounds" and s.value), ())):
        boxes[bound.element] = (bound.kind, bound.lo, bound.hi)
    resistor_box = {name: (lo, hi) for name, (k, lo, hi) in boxes.items() if k == KIND_RESISTOR}
    slice_ = next(iter(sorted(lut.memo.lut.slice_map.items())))[1]
    attach = {}
    for name, pin_map in pins.items():
        if cls.get(name) == ELEMENT_MOS:
            ends = (pin_map["d"], pin_map["s"])
        elif cls.get(name) == ELEMENT_PASSIVE and kind[name] == KIND_RESISTOR:
            ends = (pin_map["t0"], pin_map["t1"])
        else:
            continue
        for net in ends:
            attach[net] = attach.get(net, 0) + 1
    cur_rep, current_box = _theta_currents(domain)
    return LocalInputs(_items(kind), tuple(p.column("device", "pins")), _items(cls), _items(bulk), rails, orbit_key,
                       _items(l_label), rows, tuple(basis.free), _items(dict(basis.fixed)), _items(cur_rep), _items(current_box),
                       _items(dict(element_values)), _items(resistor_box), tuple(sorted(lut.w_keys)),
                       tuple(tuple(float(x) for x in g) for g in slice_.grids), tuple(p.column("node", "dc_colour")),
                       tuple(p.column("device", "dc_colour")), _items(attach))


def _gain_target(spec):
    values = [float(d.value) for d in spec.judged_constraints if d.metric == METRIC_GAIN and d.op == ">=" and d.value is not None]
    return max(values) if values else None


def _others(view, nodes):
    """같은 뷰 남의 블록 노드 넷(자기 `nodes` 제외) 정렬 tuple -- 미지수 집합 U_b 의 고정 집합 F(설계 41 §2.5-1)."""
    return tuple(sorted({n for b in view.blocks for n in b.nodes} - set(nodes)))


def _block_spec(view, block, local):
    members = tuple(sorted(n for n, _role in block.roles if local.cls.get(n) == ELEMENT_MOS))
    passives = tuple(sorted(n for n, _role in block.roles if local.cls.get(n) == ELEMENT_PASSIVE))
    return BlockSpec(block.key, ROLE_MAIN, members, passives, tuple(block.inputs), tuple(block.outputs), frozenset(view.ac_ground),
                     tuple(view.excite), tuple(block.nodes), others=_others(view, block.nodes))


def _bound(local, tables, spec, budget, role=None):
    model, reason = block_gain_model_of(local, spec)
    if model is None:
        return BlockBound(spec.key, spec.role if role is None else role, STATUS_UNKNOWN, None, None, 0, (), (), reason, None,
                          spec.members, 0)
    return block_gain_bound(model, tables, budget, spec.members)


def _chain(view, blocks, bounds, colour):
    """뷰 입력 → 출력 합성 상한(선형 진폭): 넷별 값 = 그 넷을 출력으로 갖는 블록들 (A·최대 입력 값) 의 합. 반환 {넷: 값} (미상 블록이 있으면 None)."""
    if any(b.status != STATUS_CERTIFIED for b in bounds):
        return None
    value = {net: 1 for net, _w in view.excite}
    ordered = sorted(zip(blocks, bounds), key=lambda pair: (pair[0].stage, tuple(sorted(colour.get(n, -1) for n in pair[0].key)), pair[0].key))
    for _round in range(len(ordered) + 1):
        produced = {}
        for block, bound in ordered:
            ins = [value[n] for n in block.inputs if n in value]
            if not ins:
                continue
            db = bound.a_max_db
            lin = _amplitude(db) * max(ins)
            for net in block.outputs:
                produced[net] = produced.get(net, 0) + lin
        merged = {**{net: 1 for net, _w in view.excite}, **produced}
        if merged == value:
            break
        value = merged
    return value


def _amplitude(db):
    """dB -> 진폭비 (`_db` 의 역: 10^(dB/20) = exp(dB / 20 / log10(e)))."""
    return math.exp(db / AMPLITUDE_DB_PER_DECADE / math.log10(math.e))


def _db(lin):
    return AMPLITUDE_DB_PER_DECADE * math.log10(lin) if lin > 0 else -math.inf


def _gain(view, s1v_blocks, local, tables, spec, budget, target):
    specs = [_block_spec(view, b, local) for b in s1v_blocks]
    bounds = tuple(_bound(local, tables, sp, budget) for sp in specs)
    ff_bounds, ff_specs = [], []
    for f in view.feedforward:
        merge_block = next((b for b in s1v_blocks if f.merge in b.outputs), None)
        members = set(f.cells) | set(f.bias_cells) | set(f.load_cells)
        passives = set()
        if merge_block is not None:
            members |= {n for n, _r in merge_block.roles if local.cls.get(n) == ELEMENT_MOS}
            passives |= {n for n, _r in merge_block.roles if local.cls.get(n) == ELEMENT_PASSIVE}
        mos_members = tuple(sorted(n for n in members if local.cls.get(n) == ELEMENT_MOS))
        nodes = (set(merge_block.nodes) - set(merge_block.inputs) if merge_block is not None else set()) | {f.tap, f.merge}      # merge 블록 입력 넷은 이 경로에서 구동되지 않는 남의 블록 넷(others)
        nodes |= {local.pins[n][t] for n in mos_members for t in ("d", "s")}
        ff_spec = BlockSpec((f.id,), ROLE_FF, mos_members, tuple(sorted(passives)), (f.tap,), (f.merge,), frozenset(view.ac_ground),
                            ((f.tap, 1),), tuple(sorted(nodes)), drive=(f.tap,),
                            others=_others(view, nodes))
        ff_specs.append(ff_spec)
        ff_bounds.append(_bound(local, tables, ff_spec, budget))
    chain_pure = _chain(view, s1v_blocks, bounds, local.node_colour)
    sense = tuple(view.sense)
    found = [b.found_db for b in bounds]
    found_sum = None if any(f is None for f in found) else float(sum(found))
    n_unknown = sum(1 for b in bounds if b.status != STATUS_CERTIFIED) + sum(1 for b in ff_bounds if b.status != STATUS_CERTIFIED)
    sum_db = b_db = None
    if chain_pure is not None and all(b.status == STATUS_CERTIFIED for b in ff_bounds) and any(n in chain_pure for n in sense):
        total = max(chain_pure[n] for n in sense if n in chain_pure)
        for f, fb in zip(view.feedforward, ff_bounds):
            if f.tap not in chain_pure:
                total = None
                break
            total += _amplitude(fb.a_max_db) * chain_pure[f.tap]
        if total is not None:
            sum_db, b_db = _db(total), float(sum(b.b_db for b in bounds))      # 41 4.3: b_GB4 = 주경로 블록 b 의 합
    if target is None:
        verdict = VERDICT_NO_TARGET
    elif sum_db is None:
        verdict = VERDICT_UNDETERMINED
    else:
        verdict = VERDICT_INFEASIBLE if sum_db + b_db < target else VERDICT_NOT_EXCLUDED
    return GainCheck(view.id, bounds, tuple(ff_bounds), sum_db, b_db, target, verdict, n_unknown, found_sum)


def _area(p, spec, local, lut, passive_area, area_resolution_m2):
    basis = p.value("graph", DC_KEY, "dc_current_basis")
    mos_kind = {n: k for n, k in local.kind.items() if local.cls.get(n) == ELEMENT_MOS}
    unit = dict(passive_area.unit_area)
    excluded = set(passive_area.excluded)
    bounds = {e.element: e for e in (next((s.value for s in (spec.search if isinstance(spec.search, tuple) else ())
                                           if s.field == "theta_bounds" and s.value), ()))}
    caps = []
    for name in sorted(n for n, c in local.cls.items() if c == ELEMENT_PASSIVE and local.kind[n] == KIND_CAPACITOR):
        if name in excluded or name not in unit:
            continue
        value = local.element_value.get(name)
        c_min = value if value is not None else (bounds[name].lo if name in bounds else None)
        if c_min is not None:
            caps.append((name, float(c_min), unit[name]))
    budgets = [float(d.value) for d in spec.judged_constraints if d.metric == METRIC_AREA and d.op == "<=" and d.value is not None]
    rows = {name: tuple((t.source, t.num / t.den) for t in terms) for name, terms in basis.rows}
    return area_lower_bound(lut.memo.lut, mos_kind, rows, dict(basis.fixed), tuple(caps), min(budgets) if budgets else None,
                            area_resolution_m2)


def _headroom(p, spec, view, local, lut):
    mos_kinds = sorted({k for n, k in local.kind.items() if local.cls.get(n) == ELEMENT_MOS})
    edges = {k: derived(lut.memo, "edge_costs", k, local.w_keys[k]) for k in mos_kinds}
    supplies = dict(spec.supplies_v)
    rail_v = {r: supplies[r] for r in sorted(local.rails) if r in supplies}
    direction = dict(p.column("node", "port_direction"))
    role = dict(p.column("node", "port_role"))
    windows = [(WINDOW_INPUT, n) for n in sorted(direction) if direction[n] == INPUT_DIRECTION]
    windows += [(WINDOW_OUTPUT, n) for n in sorted(direction) if direction[n] == OUTPUT_DIRECTION]
    if view is not None:
        for b in view.blocks:
            if b.kind == BLOCK_BUFFER:
                windows += [(WINDOW_BUFFER, n) for n in sorted(b.inputs) if n not in view.ac_ground and n not in local.rails]
    differential = {ROLE_DIFFERENTIAL_OUTPUT_P, ROLE_DIFFERENTIAL_OUTPUT_N} <= {role[n] for n in direction if direction[n] == OUTPUT_DIRECTION}
    constraints = tuple((d.metric, d.op, float(d.value)) for d in spec.judged_constraints
                        if d.metric in HEADROOM_METRICS and d.value is not None)
    input_dc = None
    if spec.input_dc.mode == INPUT_NET and spec.input_dc.net in supplies:
        input_dc = supplies[spec.input_dc.net]
    elif spec.input_dc.mode == INPUT_VALUE:
        input_dc = spec.input_dc.value_v
    return headroom_bound(local, rail_v, edges, tuple(windows), constraints, input_dc, differential)


def _dof(p, local, element_values):
    basis = p.value("graph", DC_KEY, "dc_current_basis")
    rails = local.rails
    nets = [n for n, _flag in p.column("node", "is_rail") if n not in rails]
    owner = dict(p.value("graph", KERNEL_KEY, "l_ties"))

    # 입력 점(DEC-106): 짝 포트는 뿌리와 한 변수다(KVL ΔV = 0) -- 쓰기 계획 필드 `node.dc_writer` 의 input_point known 을 읽는다
    same_point = {n: w.known for n, w in p.column("node", "dc_writer") if w.relation == REL_INPUT_POINT and w.known is not None}

    def v(net):
        net = same_point.get(net, net)
        return () if net in rails else ("V:" + net,)

    variables = ["V:" + n for n in nets if n not in same_point]
    equations = {}
    free = set(basis.free)
    for name in sorted(n for n, c in local.cls.items() if c == ELEMENT_MOS):
        pins = local.pins[name]
        l_var = "L:" + owner.get(name, name)
        variables += ["u:" + name, l_var]
        equations["dev:" + name] = ("u:" + name, l_var) + v(pins["d"]) + v(pins["g"]) + v(pins["s"])
    variables += ["I:" + e for e in sorted(free)]
    declared = dict(element_values)
    rows = dict(basis.rows)
    for name in sorted(basis.resistors):
        pins = local.pins[name]
        currents = tuple("I:" + t.source for t in rows.get(name, ()) if t.source in free)
        theta_r = ("R:" + name,) if declared.get(name) is None else ()
        variables += list(theta_r)
        equations["res:" + name] = v(pins["t0"]) + v(pins["t1"]) + currents + theta_r
    for net, _volts in p.value("graph", KERNEL_KEY, "fixed_values"):
        equations["fix:" + net] = v(net)
    return dof_report(variables, equations)


def _reasons(gain, area, headroom_stops, dof):
    reasons = []
    if gain is not None and gain.verdict == VERDICT_INFEASIBLE:
        reasons.append((REASON_GAIN, (("sum_db", gain.sum_db), ("b_db", gain.b_db), ("target_db", gain.target_db))))
    if area.verdict == VERDICT_INFEASIBLE:
        reasons.append((REASON_AREA, (("a_lb_m2", area.a_lb_m2), ("budget_m2", area.budget_m2), ("b_a_m2", area.b_a_m2))))
    reasons.extend(headroom_stops)
    if dof.status == STATUS_OVERCONSTRAINED:
        reasons.append((REASON_DOF, (("unmatched_equations", dof.unmatched_equations), ("competing_pairs", dof.competing_pairs))))
    return tuple(reasons)


READS = (
    ("device", "element_class"), ("device", "kind"), ("device", "pins"), ("device", "bulk"), ("device", "dc_colour"),
    ("node", "is_rail"), ("node", "port_direction"), ("node", "port_role"), ("node", "dc_colour"), ("node", "dc_writer"),
    ("graph", "orbits"), ("graph", "dc_current_basis"), ("graph", "fixed_values"), ("graph", "l_ties"),
    ("graph", "views"), ("graph", "l_classes"), ("graph", "search_domain"), ("graph", "passive_area_decl"),
)


@compute_block(ACHIEVABILITY_WRITER, reads=READS, writes=ACH_WRITES)
def achievability(projection):
    spec, element_values, lut, count_budget = projection.extras
    p = projection
    domain = p.value("graph", KERNEL_KEY, "search_domain")
    passive_area = p.value("graph", KERNEL_KEY, "passive_area_decl")
    stored = _local_inputs(p, spec, element_values, lut, domain)
    local = stored.view
    curves = curve_checks(lut.memo.lut)
    views = dict(p.column("graph", "views")).get(S1V_KEY, ())
    view = next((v for v in views if v.kind == "transfer"), None)
    target = _gain_target(spec)
    gain = None
    if view is not None and view.blocks:
        tables = ParamTables(lut.memo, local.w_keys, local.grids)
        gain = _gain(view, view.blocks, local, tables, spec, count_budget, target)
    area = _area(p, spec, local, lut, passive_area, domain.area_resolution_m2)
    head = _headroom(p, spec, view, local, lut)
    dof = _dof(p, local, element_values)
    reasons = _reasons(gain, area, head.stops, dof)
    rows_main = tuple(r for r in head.rows if r.window_kind != WINDOW_BUFFER)
    buffers = tuple(r for r in head.rows if r.window_kind == WINDOW_BUFFER)
    values = {"curve_checks": curves, "gain_checks": gain, "area_bound": area, "headroom_rows": rows_main, "buffer_window_report": buffers,
              "warnings": head.warnings, "reasons": reasons, "verdict": VERDICT_INFEASIBLE if reasons else VERDICT_OK, "dof": dof,
              "count_budget": count_budget, "local_inputs": stored}
    return {("graph", name): {ACH_KEY: values[name]} for _kind, name in ACH_WRITES}


# [U13] 출발 구간의 이득 L 하한(`search.iv_gain_l`)이 U9 와 같은 블록 대상을 만들도록 공개한 이름(복제하지 않는다 -- 입력 묶음은 필드 `graph/ach: local_inputs`)
block_spec = _block_spec
