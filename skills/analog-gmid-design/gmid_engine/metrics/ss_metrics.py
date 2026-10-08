"""spec 뷰 -> 계 레코드 -> 소신호 제약 metric 계산 블록 (7a design 2.2·2.3·2.5·3.2·4.5 단계 5, metrics CONTRACT 7절 -- 배선 지점).

진입점: `metrics_ss`(`@compute_block`) -- `metrics_ss(snapshot, requests, passive_values)`.

* reads `device.{ss_dev, element_class, kind, pins, bulk}`, `node.{ac_ground_class, port_direction}`; extras
  `requests` = `MetricRequest` tuple(view_kind 가 있는 metric 만), `passive_values` = ((수동소자, 값), ...).
  writes `graph.metrics_ss`(key `METRICS_KEY`) = `MetricBundle`.
* 회로: `ss_circuit`(노드 인덱스 = S1 노드 이름 정렬 위치). 값 없는 수동소자가 있으면 계를 만들지 않고 모든 요청을 정의 불가
  `passive_value_undeclared`(definitional, detail elements)로 낸다 -- 회로 일부를 빼고 푸는 것은 다른 회로를 푸는 것이다.
* 뷰 -> 계(7a 2.2 L4·2.5·3.2, 설계 MOD5 3.3 '같은 뷰 = 같은 MnaSystem'):
  - 고정 넷 집합 F = 교류접지(레일 ∪ gate 전용 미구동) ∪ 입력 포트 ∪ 그 뷰의 전압 구동 넷. F 가 같은 뷰는 **한 계**를 쓴다
    (G·C 가 같고 여기 열만 다르다). 계의 교류접지 = F − 그 계 모든 열의 구동 넷(열에 없는 구동 넷은 그 열에서 0 V).
  - `port`(전달 기본)·`loop` unity(β = 1)·`transfer`(명시 ac_excite): 열 = 가중 전압 구동, 관측 = 감지 넷. 같은 (계, 열, 관측)
    은 `analyze_loop` 1회를 공유한다 -- β = 1 의 `pm_ss_deg` 와 기본 포트 뷰 `parasitic_pm_ss_deg` 는 같은 `LoopAnalysis`(I-15).
  - `loop` declared(β 루프): F = 교류접지 ∪ (입력 포트 − 절단 넷). 되먹임 소자의 절단 넷 쪽 단자를 `cut_circuit` 으로 떼고
    그 계 응답에서 `probe_factor`(가중 = 뷰 weights 를 절단 쌍 순서로) -> `analyze_loop`.
  - `sense`(출력 포트 뷰, DEC-66): 포트 전달 계(F = 교류접지 ∪ 입력 포트)에 감지 넷 단위 전류 열(단일 +1 / 차동 +1·−1) 하나 +
    그 관측 -> `output_resistance`.
  - `ratio`: num·den 두 열(같은 계), 관측이 같아야 한다(`response_ratio` 는 한 관측 행 -- 다르면 ValueError, 뷰 정의 결함).
  - `pending`: 계 없이 정의 불가 `view_pending`(definitional, detail decision).
  모든 계는 **한 번의** `solve_responses` 로 푼다(공유 격자 -- 루프 계와 포트 계가 함께, 7a 2.4 '격자').
* 값은 `metric_value`(레지스트리 필드 읽기 -- 예외 없음, 정의 불가는 `Undefined`). 묶음 `approximations` = ss_dev 의
  (cap, cap_model)·(gmb, gmb_model)·(junction, junction_model) -- 용량 의존 metric 이 근사·미정 위에 있음을 매 결과에 싣는다(M6).
* [NFR-5] 값마다 분해능 `MetricResult.resolution`(metrics CONTRACT 9절): `lut_parameters(회로, ss_dev 의 lut_rel_tol)` 한 번,
  분석 열쇠마다 `metric_resolutions` 한 번(같은 계·같은 ω 의 수반 풀이는 블록 안 memo 로 공유). 블록 안에서 계산하므로 입력이 같으면
  블록 재사용으로 다시 계산하지 않는다. 미정이면 None.
"""
import dataclasses

from gmid_engine.authoring import (BETA_DECLARED, INPUT_DIRECTION, ROLE_DIFFERENTIAL_OUTPUT_N, ROLE_DIFFERENTIAL_OUTPUT_P,
                                   SENSE_DIFFERENTIAL, ViewDecl, cm_partition)
from gmid_engine.core import compute_block
from gmid_engine.graph import ELEMENT_SOURCE
from gmid_engine.sizing import METRICS_KEY, METRICS_SS_WRITER

from .evaluate import metric_value
from .loop_analysis import analyze_loop
from .loop_cut import cut_circuit
from .lut_parameters import lut_parameters
from .mna_build import build_mna
from .mna_solve import solve_responses
from .mna_types import Factor, MetricResult, Undefined
from .probe_loop import probe_factor
from .ratio import response_ratio
from .records import (LOOP_CUT_KINDS, LOOP_CUT_MOS, LOOP_CUT_TERMINALS, Excitation, LoopCut,
                      Sense)
from .registry import metric_registry
from .resolution import metric_resolutions
from .rout import output_resistance
from .ss_circuit import ss_circuit
from .ss_types import MetricBundle, MetricRequest

READS = (
    ("device", "ss_dev"), ("device", "element_class"), ("device", "kind"), ("device", "pins"), ("device", "bulk"),
    ("node", "ac_ground_class"), ("node", "port_direction"), ("node", "port_role"), ("node", "is_rail"),
)
WRITES = (("graph", "metrics_ss"),)
UNIT = 1.0                                              # 단위 시험 전류(rout_ohm = 관측 / 이 값)
CODE_VIEW_PENDING = "view_pending"
CODE_PASSIVE_MISSING = "passive_value_undeclared"
CM_OUTPUT_MODE = "cm_output"                          # authoring ViewDecl.mode: 출력 포트 CM 주입 루프
CM_VIEW_KIND = "cm_loop"                              # 보고 전용 CM 루프가 읽는 metric = 레지스트리에서 이 view_kind 인 것
WARN_CM_UNCONSTRAINED = "cm_loop_unconstrained"
LEVEL_CODE = "dc_not_above_level"                     # find_crossing 사유: |T(0)| ≤ 레벨
GAIN_FIELD = "gain_db"                                # LoopAnalysis 필드(분해능 quantity 와 같은 이름)


def _undefined(request, code, detail):
    field = metric_registry()[request.metric].field
    return MetricResult(request.metric, None, (Undefined(field, code, "definitional", detail),))


def _slot(items, item):
    if item not in items:
        items.append(item)
    return items.index(item)


class _Ledger:
    """계 조립 장부(블록 호출 하나 안에서만 산다 -- 모듈 수준 상태가 아니다). 계 key: 전체 회로 계 = 고정 넷 frozenset,
    β 루프 계 = ("cut", 뷰 cuts)."""

    def __init__(self, ss, rail_nets=(), source_nets=()):
        self.ss = ss
        self.cm_ambiguity = None
        self.index = {net: i for i, net in enumerate(ss.nodes)}
        self.rails = frozenset(self.index[n] for n in rail_nets if n in self.index)       # 공급 레일 노드 ([CM] 구동자 분류용)
        self.source_nodes = frozenset(self.index[n] for n in source_nets if n in self.index)   # 이상원 단자 노드
        self.base = frozenset(ss.ground_nets) | frozenset(ss.input_nets)
        self.rows = {}

    def _entry(self, key, make):
        if key not in self.rows:
            self.rows[key] = make()
        return self.rows[key]

    def full(self, driven):
        key = frozenset(self.base | frozenset(driven))
        return key, self._entry(key, lambda: {"columns": [], "senses": [], "driven": set()})

    def column(self, entry, voltages=(), currents=()):
        entry["driven"].update(net for net, _ in voltages)
        return _slot(entry["columns"], (tuple(sorted(voltages)), tuple(sorted(currents))))

    def sense(self, entry, decl):
        return _slot(entry["senses"], (decl.sense_p, decl.sense_n))

    def cut(self, view):
        key = ("cut", view.cuts)
        nets = frozenset(net for _e, net in view.cuts)
        self._entry(key, lambda: {"cuts": view.cuts, "fixed": self.base - nets, "weights": dict(view.weights)})
        return key

    def cm_cuts(self, view):
        """[CM] 출력 포트 CM 절단(view mode `cm_output`): 구동자 MOS 의 출력 넷 쪽 channel 단자를 새 노드 x 로 옮긴다. 구동자 = 뷰 `cuts`((MOS 이름, 출력 넷), authoring
        `cm_partition` 결과·선언 반영) -- 비어 있으면(보고 전용 뷰 등) 같은 `cm_partition` 을 이 소신호 회로(MOS 라벨·수동소자·`self.rails` = 레일 ∪ 이상원 단자 넷)에서
        직접 부른다. 수동소자·gate·소비자 MOS 는 n 쪽에 남는다. 모호하면 `self.cm_ambiguity` 에 사유를 남기고 절단 ()."""
        index = self.index
        mos_by_label = {m.label: (position, m) for position, m in enumerate(self.ss.circuit.mos)}
        outputs = tuple(sorted(index[net] for net, _w in view.weights))
        self.cm_ambiguity = None
        if view.cuts:
            moved = [(name, index[net]) for name, net in view.cuts]
        else:
            part = cm_partition(
                outputs, tuple((m.label, m.d, m.g, m.s) for m in self.ss.circuit.mos),
                tuple((e.a, e.b) for e in self.ss.circuit.resistors + self.ss.circuit.capacitors), self.rails, None,
                self.source_nodes)
            if part.ambiguity is not None:
                self.cm_ambiguity = part.ambiguity
                return ()
            moved = [(name, index[net] if isinstance(net, str) else net) for name, net in part.drivers]
        cuts = []
        for name, net in moved:
            position, mos = mos_by_label[name]
            cuts.append(LoopCut(LOOP_CUT_MOS, position, "d" if mos.d == net else "s"))
        return tuple(cuts)

    def cm_cut(self, view):
        key = ("cm_output", tuple(net for net, _w in view.weights))
        self._entry(key, lambda: {"loop_cuts": self.cm_cuts(view), "fixed": self.base, "weights": dict(view.weights)})
        return key

    def solve(self):
        """모든 계 조립 1회씩 + 한 번의 solve_responses -> ({key: 응답}, {β 루프 key: (CutCircuit, 가중 tuple)})."""
        keys = tuple(self.rows)
        systems, cuts = [], {}
        for key in keys:
            entry = self.rows[key]
            if "cuts" in entry or "loop_cuts" in entry:
                cut = self._cut_circuit(entry)
                nets = {self.index[n]: n for n in entry["weights"]}
                cuts[key] = (cut, tuple(entry["weights"][nets[n]] for n, _x in cut.pairs))
                systems.append(build_mna(cut.circuit, cut.excitations, cut.senses))
                continue
            ground = tuple(sorted(self.index[n] for n in key - entry["driven"]))
            circuit = dataclasses.replace(self.ss.circuit, ac_ground=ground)
            columns = tuple(
                Excitation("c%d" % j, voltages=tuple((self.index[n], a) for n, a in v),
                           currents=tuple((self.index[n], a) for n, a in c))
                for j, (v, c) in enumerate(entry["columns"]))
            senses = tuple(Sense(self.index[p], None if q is None else self.index[q]) for p, q in entry["senses"])
            systems.append(build_mna(circuit, columns, senses))
        return dict(zip(keys, solve_responses(tuple(systems)))), cuts

    def _cut_circuit(self, entry):
        ss = self.ss
        circuit = dataclasses.replace(ss.circuit, ac_ground=tuple(sorted(self.index[n] for n in entry["fixed"])))
        pools = dict(zip(LOOP_CUT_KINDS, ((ss.resistors, circuit.resistors), (ss.capacitors, circuit.capacitors))))
        if "loop_cuts" in entry:
            return cut_circuit(circuit, entry["loop_cuts"])
        loop_cuts = []
        for element, net in entry["cuts"]:
            found = [(kind, names.index(element), elements) for kind, (names, elements) in pools.items() if element in names]
            if not found:
                raise ValueError("metrics_ss: 되먹임 소자 %r 가 소신호 저항·커패시터가 아니다" % (element,))
            kind, position, elements = found[0]
            first, second = LOOP_CUT_TERMINALS            # Resistor·Capacitor 의 단자 필드 이름(a = pins t0, b = t1)
            terminal = first if getattr(elements[position], first) == self.index[net] else second
            loop_cuts.append(LoopCut(kind, position, terminal))
        return cut_circuit(circuit, tuple(loop_cuts))


def _plan(request, ledger):
    """요청 하나 -> 분석 열쇠(같은 열쇠는 같은 분석 객체를 공유한다)."""
    view = request.view
    mode = view.mode
    if mode in ("port", "transfer") or (mode == "loop" and view.beta != BETA_DECLARED):
        pairs, decl = (view.transfer.ac_excite, view.transfer) if mode == "transfer" else (view.weights, view.sense)
        key, entry = ledger.full(net for net, _ in pairs)
        return ("loop", key, ledger.column(entry, voltages=pairs), ledger.sense(entry, decl))
    if mode == "loop":
        return ("probe", ledger.cut(view))
    if mode == CM_OUTPUT_MODE:
        return ("probe", ledger.cm_cut(view))
    if mode == "sense":
        decl = view.sense
        key, entry = ledger.full(())
        currents = ((decl.sense_p, UNIT),) + (((decl.sense_n, -UNIT),) if decl.sense_mode == SENSE_DIFFERENTIAL else ())
        return ("rout", key, ledger.column(entry, currents=currents), ledger.sense(entry, decl))
    if mode == "ratio":
        if (view.num.sense_p, view.num.sense_n) != (view.den.sense_p, view.den.sense_n):
            raise ValueError("metrics_ss: ratio 뷰의 num·den 관측이 다르다 -- 같은 계 한 관측 행의 응답비만 정의된다")
        key, entry = ledger.full(net for net, _ in view.num.ac_excite + view.den.ac_excite)
        num = ledger.column(entry, voltages=view.num.ac_excite)
        den = ledger.column(entry, voltages=view.den.ac_excite)
        return ("ratio", key, num, den, ledger.sense(entry, view.num))
    raise ValueError("metrics_ss: 소신호 뷰가 아닌 요청 %r" % (request,))


def _analysis(plan, responses, cuts):
    """분석 열쇠 -> (분석 결과, 분해능 출처 -- 루프: 인수 tuple, rout·ratio: 그 응답)."""
    kind, key = plan[0], plan[1]
    response = responses[key]
    if kind == "loop":
        factors = (Factor(response, plan[2], plan[3]),)
        return analyze_loop(factors), factors
    if kind == "probe":
        cut, weights = cuts[key]
        factors = (probe_factor(response, cut.pairs, weights),)
        return analyze_loop(factors), factors
    if kind == "rout":
        return output_resistance(response, plan[2], plan[3]), response
    return response_ratio(response, plan[2], plan[3], plan[4]), response


def _approximations(ss_values):
    found = set()
    for ss in ss_values:
        found.update((("cap", ss.cap_model), ("gmb", ss.gmb_model), ("junction", ss.junction_model)))
    return tuple(sorted(found))


def _plain(result, resolutions):
    """graph 필드 값으로 넣을 수 있게 값을 파이썬 float 로(numpy 스칼라 -> float, 지문 규칙 core 1절) + 그 필드의 분해능."""
    if result.value is None:
        # [CM] 루프 DC 이득이 레벨(1) 아래라 교차·PM 이 없는 경우: 이득 dB 의 분해능을 실어 준다(search 가 위반 크기를 dB 분해능 단위로 정규화)
        if any(u.code == LEVEL_CODE for u in result.undefined):
            found = next((r.value for r in resolutions if r.quantity == GAIN_FIELD), None)
            if found is not None:
                return MetricResult(result.name, None, result.undefined, float(found))
        return result
    field = metric_registry()[result.name].field
    found = next((r.value for r in resolutions if r.quantity == field), None)
    return MetricResult(result.name, float(result.value), result.undefined, None if found is None else float(found))


def _cm_report_view(roles):
    """선언된 차동 출력 포트 쌍(role p·n 각 하나)이 있으면 그 넷의 동일 부호 가중 뷰(`cm_output`), 아니면 None."""
    p = [net for net, role in roles if role == ROLE_DIFFERENTIAL_OUTPUT_P]
    n = [net for net, role in roles if role == ROLE_DIFFERENTIAL_OUTPUT_N]
    if len(p) != 1 or len(n) != 1:
        return None
    pair = sorted(p + n)
    return ViewDecl(CM_OUTPUT_MODE, weights=tuple((net, 1.0 / len(pair)) for net in pair))


def _cm_report(analysis, view, declared):
    """보고 전용 CM 루프 요약 ((키, 값) 정렬 tuple) 과 경고 tuple. 판정은 spec 선언만 따른다 -- 선언이 없고 T_cm(0) > 1(dB > 0)이면
    CM 루프가 있는데 안정성 제약이 없다는 경고 `cm_loop_unconstrained`."""
    pm = metric_value(next(n for n, m in metric_registry().items() if m.signature.view_kind == CM_VIEW_KIND), analysis)
    summary = (("break_nets", tuple(net for net, _w in view.weights)),
               ("dc_db", None if analysis.gain_db is None else float(analysis.gain_db)),
               ("pm_deg", None if pm.value is None else float(pm.value)),
               ("ugf_hz", None if analysis.ugf_hz is None else float(analysis.ugf_hz)),
               ("undefined", tuple(sorted({u.code for u in pm.undefined}))))
    warn = ()
    if not declared and analysis.gain_db is not None and analysis.gain_db > 0:
        warn = ((WARN_CM_UNCONSTRAINED, (("dc_db", float(analysis.gain_db)),)),)
    return (("cm_loop", summary),), warn


@compute_block(METRICS_SS_WRITER, reads=READS, writes=WRITES)
def metrics_ss(projection):
    requests, passive_values = projection.extras
    classes = dict(projection.column("device", "element_class"))
    kinds = dict(projection.column("device", "kind"))
    pins = dict(projection.column("device", "pins"))
    bulk = {m: b.net for m, b in projection.column("device", "bulk")}
    ss_values = dict(projection.column("device", "ss_dev"))
    ground = tuple(n for n, c in projection.column("node", "ac_ground_class") if c is not None)
    nodes = tuple(n for n, _c in projection.column("node", "ac_ground_class"))
    inputs = tuple(n for n, d in projection.column("node", "port_direction") if d == INPUT_DIRECTION)
    devices = tuple((name, classes[name], kinds[name], pins[name], bulk.get(name), ss_values.get(name))
                    for name in sorted(classes))
    ss = ss_circuit(nodes, ground, inputs, devices, passive_values)
    pending = {r: _undefined(r, CODE_VIEW_PENDING, (("decision", r.view.decision),))
               for r in requests if r.view.mode == "pending"}
    results = dict(pending)
    detail = ()
    reports = warnings = ()
    report_note = cm_view = None
    if ss.missing:
        detail = (("missing_passives", ss.missing),)
        results.update({r: _undefined(r, CODE_PASSIVE_MISSING, (("elements", ss.missing),))
                        for r in requests if r not in pending})
    else:
        rail_nets = {n for n, flag in projection.column("node", "is_rail") if flag}
        source_nets = {net for name in classes if classes[name] == ELEMENT_SOURCE for _t, net in pins[name]}
        ledger = _Ledger(ss, rail_nets, source_nets)
        plans = {r: _plan(r, ledger) for r in requests if r not in pending}
        declared_cm = next((r.view for r in requests if r.view.mode == CM_OUTPUT_MODE), None)
        cm_view = declared_cm or _cm_report_view(projection.column("node", "port_role"))
        report_plan = report_note = None
        if cm_view is not None:
            if ledger.cm_cuts(cm_view):
                report_plan = _plan(MetricRequest("", cm_view), ledger)
            elif ledger.cm_ambiguity is not None:
                report_note = ledger.cm_ambiguity
        if plans or report_plan is not None:
            responses, cuts = ledger.solve()
            parameters = lut_parameters(ss.circuit, tuple(ss_values[m.label].lut_rel_tol for m in ss.circuit.mos))
            memo = {}                                   # (id(계), ω) -> 수반 풀이 -- 이 블록 호출 안에서만 산다
            done = {}
            for request, plan in plans.items():
                if plan not in done:
                    analysis, source = _analysis(plan, responses, cuts)
                    done[plan] = (analysis, metric_resolutions(analysis, source, parameters, memo))
                analysis, resolutions = done[plan]
                results[request] = _plain(metric_value(request.metric, analysis), resolutions)
            if report_plan is not None:
                if report_plan not in done:
                    analysis, source = _analysis(report_plan, responses, cuts)
                    done[report_plan] = (analysis, metric_resolutions(analysis, source, parameters, memo))
                reports, warnings = _cm_report(done[report_plan][0], cm_view, declared_cm is not None)
            first = next(iter(responses.values()))
            detail = (("grid_points", len(first.omegas)), ("systems", len(responses)))
    if report_note is not None:       # [CM] 구동자·소비자 분류가 모호해 보고 전용 CM 루프를 만들지 못했다 -- 보고에 사유를 남긴다(경고 없음)
        reports = (("cm_loop", (("break_nets", tuple(net for net, _w in cm_view.weights)), ("undefined", ("cm_partition_ambiguous",)))),)
    bundle = MetricBundle(tuple((r, results[r]) for r in requests), _approximations(ss_values.values()), detail, reports,
                          warnings)
    return {("graph", "metrics_ss"): {METRICS_KEY: bundle}}
