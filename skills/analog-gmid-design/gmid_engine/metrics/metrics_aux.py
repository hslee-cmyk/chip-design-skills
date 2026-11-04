"""봉인 점 -> offset·미러비·스윙·ICMR·FF 비 metric + 블록 잔차 보고 계산 블록 (설계 40 §3.8, §3.8-8, 41 §2, 단위 U7).

진입점: `metrics_aux`(`@compute_block`) -- `metrics_aux(snapshot, requests, lut, mismatch, structure, targets, input_dc_v, linear_devices,
transfer_views, ugf_hz, driving)`.

* reads `graph.{ss_circuit, ss_nodal, matching_groups, matching_dispositions}`(조립된 소신호 회로·봉인점 노달 계 -- 조립 자리는 블록 `ss_circuit`·`ss_nodal` 하나씩, 이 블록은 다시
  조립하지 않는다), `device.{ss_dev, dc_op, dc_tol_v, kind, pins, dc_role, dc_colour}`, `node.{port_direction, port_role, dc_v, dc_rail_v}`. writes `graph.metrics_aux`(key `METRICS_KEY`) = `MetricBundle`.
* extras: `requests` = `MetricRequest` tuple(레지스트리 결과 형식이 `AUX_TYPES` 인 metric 만), `lut` = sizing `LutAccess`,
  `mismatch` = `MismatchSource`(또는 None -- offset·미러비는 `mismatch_source_missing`), `structure` = `MetricStructure`(또는 None -- offset_excess·FF·블록 잔차는 구조 입력 없음),
  `targets` = spec 노드 목표 ((넷, V), ...), `input_dc_v` = 선언 입력 DC 또는 None(SP-2 대기 -> 해의 y_icm), `linear_devices` = 선형 영역 선언 소자,
  `transfer_views` = 판정 제약의 전달 뷰 `ViewDecl` tuple(블록 잔차 보고가 짝을 찾는 뷰), `ugf_hz` = 같은 평가의 `ugf_ss_hz` 값(nqs_ratio 입력, 없으면 None),
  `driving` = spec `DrivingDecl` 또는 None(선언되면 `ls_fields` 슬루·방향별 전류 보고 -- 제약 행은 search 가 만든다).
* 회로: 필드 `graph.ss_circuit`(구조 색 정준 순서, 이름 치환 불변)과 `graph.ss_nodal`(offset·systematic·블록 잔차의 조립 자리 셋이 읽는 G·인수분해). 값 없는 수동소자가 있으면 모든 요청이 `passive_value_undeclared`.
* metric → 계산 함수 (정의·식은 각 파일 머리말):
  `offset_in_sigma_mv`·`offset_excess` → `offset_analysis`(σ 는 `device_sigmas`), `offset_sys_mv` → `offset_systematic`, `mirror_ratio_sigma_pct` → `mirror_ratio`,
  `swing_out_v`·`icmr_v`·`icm_margin_v` → `ls_swing`(채널 포화 `vdsat + tol_vdsat`), `ff_gm_ratio` → `ff_gm_ratio`. 같은 (함수, 뷰) 는 한 번만 부른다.
* 보고(`MetricBundle.reports`, 요청과 무관하게 구조 입력이 있으면 항상): 전달 뷰마다 `block_residual`(gain_residual_db·block_gain·ff_contrib·rout_residual_ohm, 41 §2.2),
  `nqs_ratio`(ugf 가 있을 때). metric 이 계산된 만큼 `offset_contrib`·`swing_icmr`·`mirror_ratio`·`ff_gm_ratio` 보고.
"""
from gmid_engine.authoring import (INPUT_DIRECTION, OUTPUT_DIRECTION, ROLE_DIFFERENTIAL_OUTPUT_N, ROLE_DIFFERENTIAL_OUTPUT_P)
from gmid_engine.core import SealViolationError, compute_block
from gmid_engine.graph import (DISPOSITION_BIAS_DISTRIBUTION, GRAPH_KEY, MATCH_MIRROR, MOS_TERMINAL_NAMES, NMOS)
from gmid_engine.lut import tol_vdsat_table, vdsat
from gmid_engine.sizing import METRICS_AUX_WRITER, METRICS_KEY

from .aux_types import (FfRatio, MirrorRatio, OffsetAnalysis, OffsetSystematic, SatDevice, SwingIcmr)
from .block_residual import block_residual
from .device_sigma import device_sigmas
from .evaluate import metric_value
from .ff_gm_ratio import ff_gm_ratio
from .ls_fields import ls_fields
from .ls_swing import ls_swing
from .mirror_ratio import mirror_ratio
from .mna_types import MetricResult, Undefined
from .nqs_ratio import nqs_ratio
from .offset_analysis import offset_analysis
from .offset_systematic import offset_systematic
from .registry import metric_registry
from .ss_circuit import CODE_PASSIVE_MISSING
from .ss_types import MetricBundle

READS = (
    ("graph", "ss_circuit"), ("graph", "ss_nodal"),
    ("device", "ss_dev"), ("device", "dc_op"), ("device", "dc_tol_v"), ("device", "kind"), ("device", "pins"),
    ("device", "dc_role"), ("device", "dc_colour"),
    ("node", "port_direction"), ("node", "port_role"), ("node", "dc_v"), ("node", "dc_rail_v"),
    ("graph", "matching_groups"), ("graph", "matching_dispositions"),
)
WRITES = (("graph", "metrics_aux"),)
AUX_TYPES = (OffsetAnalysis, OffsetSystematic, MirrorRatio, SwingIcmr, FfRatio)
REPORT_BLOCK_RESIDUAL = "block_residual"                    # 보고 이름(MetricBundle.reports): search 의 residual_probe·S3 기록이 읽는다
REPORT_LS_FIELDS = "ls_fields"                              # search 의 ls_constraint_rows 가 읽는다
CODE_MISMATCH_MISSING = "mismatch_source_missing"                 # ss_evaluate(mismatch=) 를 안 줬다(PDK mismatch 모델 없음)
CODE_MISMATCH_LUT = "mismatch_lut_missing"                      # LUT 에 그 kind 의 mismatch 감도 표(r1 파일)가 없다 -- 설계 41 §6.4-2b 의 mismatch_lut_missing
CODE_NO_STRUCTURE = "structure_unavailable"
CODE_NO_VIEW_STRUCTURE = "view_structure_unmatched"
# 결과 형식 -> 분해능 필드 (MetricResult.resolution 의 출처). swing·icmr·icm_margin 은 필드별로 갈리므로 이름으로 고른다.
RESOLUTION_FIELDS = (
    ("offset_in_sigma_mv", "resolution_mv"), ("offset_excess", "excess_resolution"), ("offset_sys_mv", "resolution_mv"),
    ("mirror_ratio_sigma_pct", "resolution_pct"), ("swing_out_v", "swing_resolution"), ("icmr_v", "icmr_resolution"),
    ("icm_margin_v", "margin_resolution"), ("ff_gm_ratio", "resolution"),
)


def _fail(request, code, detail=()):
    field = metric_registry()[request.metric].field
    return MetricResult(request.metric, None, (Undefined(field, code, "definitional", detail),))


def _result(request, source):
    plain = metric_value(request.metric, source)
    resolution = dict(RESOLUTION_FIELDS).get(request.metric)
    found = None if resolution is None else getattr(source, resolution)
    if plain.value is None:
        return plain
    return MetricResult(request.metric, float(plain.value), plain.undefined, None if found is None else float(found))


def _structure_of(structure, view):
    """뷰 선언(`ViewDecl`) -> 같은 여기·감지 넷 집합의 `ViewStruct` 또는 None."""
    if structure is None or view is None:
        return None
    pairs = view.transfer.ac_excite if getattr(view, "mode", None) == "transfer" else getattr(view, "weights", ())
    decl = view.transfer if getattr(view, "mode", None) == "transfer" else getattr(view, "sense", None)
    if decl is None:
        return None
    excite = frozenset(n for n, _w in pairs)
    sense = frozenset(n for n in (decl.sense_p, decl.sense_n) if n is not None)
    return next((v for v in structure.views if frozenset(n for n, _w in v.excite) == excite and frozenset(v.sense) == sense), None)


def _sat_devices(projection, lut, linear, canonical):
    """`SatDevice` tuple(정준 순서). VDSAT 열이 없는 LUT 이거나 tol 이 정해지지 않은 소자는 `sat_v` None(근사하지 않는다)."""
    kinds = dict(projection.column("device", "kind"))
    pins = dict(projection.column("device", "pins"))
    tols = dict(projection.column("device", "dc_tol_v"))
    rows = []
    for label, op in sorted(projection.column("device", "dc_op"), key=lambda r: canonical(r[0])):
        terminal = dict(pins[label])
        drain, gate, source = (terminal[t] for t in MOS_TERMINAL_NAMES)
        sat = sat_tol = None
        try:
            base = vdsat(lut.memo, op.kind, op.w_key, op.L, op.vgs, op.vds, op.vsb)
            sat_tol = tol_vdsat_table(lut.memo, op.kind, op.w_key).at(op.L, op.vds)
            sat = None if sat_tol is None else base + sat_tol
        except SealViolationError as exc:
            if dict(exc.record.detail).get("reason") != "lut_column_unavailable":
                raise
        rows.append(SatDevice(label, 1 if kinds[label] == NMOS else -1, drain, gate, source, op.vgs, sat, sat_tol,
                              tols.get(label), label in linear))
    return tuple(rows)


def _net_tolerance(projection):
    """{넷: 그 넷에 채널 단자가 닿은 MOS 의 tol_V 합(V)} -- DC 노드전압 허용오차의 보수적 상계(`offset_systematic` 분해능). tol_V 가 없는 소자가 닿으면 None."""
    tols = dict(projection.column("device", "dc_tol_v"))
    total = {}
    for label, pin_pairs in projection.column("device", "pins"):
        if label not in tols:
            continue
        terminal = dict(pin_pairs)
        for net in (terminal[MOS_TERMINAL_NAMES[0]], terminal[MOS_TERMINAL_NAMES[2]]):
            previous = total.get(net, 0.0)
            total[net] = None if previous is None or tols[label] is None else previous + tols[label]
    return total


def _tags(projection):
    """소자 -> matching 그룹 kind 표지(해석용)와 mirror 계열 그룹 ((표지, 멤버), ...)."""
    groups = projection.value("graph", GRAPH_KEY, "matching_groups")
    dispositions = projection.value("graph", GRAPH_KEY, "matching_dispositions")
    tag = {}
    for g in groups:
        for m in g.members:
            tag[m] = "+".join(sorted(set(filter(None, (tag.get(m, ""), g.kind)))))
    mirrors = tuple((g.evidence.rule, tuple(g.members)) for g in groups if g.kind == MATCH_MIRROR)
    mirrors += tuple((d.kind, tuple(d.members)) for d in dispositions if d.kind == DISPOSITION_BIAS_DISTRIBUTION)
    return tag, mirrors


@compute_block(METRICS_AUX_WRITER, reads=READS, writes=WRITES)
def metrics_aux(projection):
    (requests, lut, mismatch, structure, targets, input_dc_v, linear_devices, transfer_views, ugf_hz, driving) = projection.extras
    ss = projection.value("graph", METRICS_KEY, "ss_circuit")        # 조립 자리는 블록 `ss_circuit`·`ss_nodal` 하나씩 -- 여기서 다시 조립하지 않는다
    nodal = projection.value("graph", METRICS_KEY, "ss_nodal")        # 값 없는 수동소자가 있으면 아래서 먼저 끝나므로 이후에는 `NodalSystem`
    ss_values = dict(projection.column("device", "ss_dev"))
    device_orbit = dict(projection.column("device", "dc_colour"))
    canonical = lambda name: (device_orbit.get(name, -1), name)                  # noqa: E731
    results = {}
    reports = []
    if ss.missing:
        results = {r: _fail(r, CODE_PASSIVE_MISSING, (("elements", ss.missing),)) for r in requests}
        return {("graph", "metrics_aux"): {METRICS_KEY: MetricBundle(tuple((r, results[r]) for r in requests), (), (("missing_passives", ss.missing),), ())}}
    ops = dict(projection.column("device", "dc_op"))
    mos = tuple(m for m in ss.circuit.mos)
    rel_tols = {m.label: ss_values[m.label].lut_rel_tol for m in mos}
    node_v = {n: v for n, v in projection.column("node", "dc_rail_v") if v is not None}
    node_v.update(dict(projection.column("node", "dc_v")))
    tag, mirrors = _tags(projection)
    roles = tuple((m, role.role) for m, role in projection.column("device", "dc_role"))
    cache = {}

    def sigmas():
        if "sigma" not in cache:
            if mismatch is None:
                cache["sigma"] = None
            else:
                rows = tuple((m.label, ops[m.label].kind, ops[m.label].w_key, ops[m.label].L, ops[m.label].W, ops[m.label].vgs,
                              ops[m.label].vds, ops[m.label].vsb) for m in mos)
                cache["sigma"] = device_sigmas(lut, mismatch, rows)
        return cache["sigma"]

    def once(key, make):
        if key not in cache:
            cache[key] = make()
        return cache[key]

    for request in requests:
        name, view = request.metric, request.view
        vstruct = _structure_of(structure, view)
        if name in ("offset_in_sigma_mv", "offset_excess"):
            if sigmas() is None:
                results[request] = _fail(request, CODE_MISMATCH_MISSING if mismatch is None else CODE_MISMATCH_LUT)
                continue
            found = once(("offset", view), lambda: offset_analysis(ss, view, sigmas(), () if vstruct is None else vstruct.input_cells, rel_tols, tag, nodal=nodal))
            results[request] = _result(request, found)
            continue
        if name == "offset_sys_mv":
            found = once(("sys", view), lambda: offset_systematic(ss, view, tuple(node_v.items()), targets, _net_tolerance(projection), nodal=nodal))
            results[request] = _result(request, found)
            continue
        if name == "mirror_ratio_sigma_pct":
            if sigmas() is None:
                results[request] = _fail(request, CODE_MISMATCH_MISSING if mismatch is None else CODE_MISMATCH_LUT)
                continue
            gmid = tuple((m.label, ops[m.label].gm_id) for m in mos)
            found = once("mirror", lambda: mirror_ratio(mirrors, roles, gmid, sigmas()))
            results[request] = _result(request, found)
            continue
        if name in ("swing_out_v", "icmr_v", "icm_margin_v"):
            found = once("swing", lambda: _swing(projection, lut, linear_devices, canonical, node_v, input_dc_v))
            results[request] = _result(request, found)
            continue
        if name == "ff_gm_ratio":
            if vstruct is None:
                results[request] = _fail(request, CODE_NO_VIEW_STRUCTURE if structure is not None else CODE_NO_STRUCTURE)
                continue
            results[request] = _result(request, once(("ff", view), lambda: ff_gm_ratio(ss, vstruct, rel_tols)))
            continue
        raise KeyError("metrics_aux: 계산 함수가 없는 metric %r" % (name,))
    for view in transfer_views:
        vstruct = _structure_of(structure, view)
        if vstruct is not None and vstruct.ff and ("ff", view) not in cache:                  # FF 비는 front 점마다 보고(41 §1.12.2-5) -- 제약이 없어도
            cache[("ff", view)] = ff_gm_ratio(ss, vstruct)
        if vstruct is not None and ("residual", vstruct.id) not in cache:
            found = block_residual(ss, view, vstruct, nodal=nodal)
            cache[("residual", vstruct.id)] = found
            reports.append((REPORT_BLOCK_RESIDUAL, _residual_report(found)))
            nqs = nqs_ratio(tuple((m.label, m.gm, ss_values[m.label].cgg) for m in mos if m.label in vstruct.signal_devices), ugf_hz)
            reports.append(("nqs_ratio", (("view", vstruct.id), ("ratio", nqs.ratio), ("min_ft_hz", nqs.min_ft_hz), ("device", nqs.limiting_device),
                                          ("undefined", tuple(sorted(u.code for u in nqs.undefined))))))
            if driving is not None:
                swing = once("swing", lambda: _swing(projection, lut, linear_devices, canonical, node_v, input_dc_v))
                if swing.bounds:
                    outs = tuple(n for n, d in projection.column("node", "port_direction") if d == OUTPUT_DIRECTION)
                    fields = ls_fields(ss, vstruct, ops, node_v, swing.bounds, lut, rel_tols, driving, outs)
                    reports.append((REPORT_LS_FIELDS, _ls_report(vstruct.id, fields)))
    for key, found in sorted(((k, v) for k, v in cache.items() if isinstance(k, tuple) and k[0] == "offset"), key=lambda kv: repr(kv[0])):
        reports.append(("offset_contrib", (("a_dm", found.a_dm), ("contrib", tuple((c.device, c.share, c.variance_v2, c.sigma_vgs_v, c.z_ohm, c.matching)
                                                                                for c in found.contrib)))))
    if "swing" in cache:
        s = cache["swing"]
        reports.append(("swing_icmr", (("out_ranges", s.out_ranges), ("window", s.window), ("v_icm", s.v_icm), ("input_dc", s.input_dc),
                                       ("required_input_cm_v", s.required_input_cm_v))))
    if "mirror" in cache:
        reports.append(("mirror_ratio", (("groups", cache["mirror"].groups),)))
    for key in sorted((k for k in cache if isinstance(k, tuple) and k[0] == "ff"), key=repr):
        reports.append(("ff_gm_ratio", (("per_ff", cache[key].per_ff),)))
    bundle = MetricBundle(tuple((r, results[r]) for r in requests), (), (), tuple(reports))
    return {("graph", "metrics_aux"): {METRICS_KEY: bundle}}


def _swing(projection, lut, linear, canonical, node_v, input_dc_v):
    devices = _sat_devices(projection, lut, frozenset(linear), canonical)
    rails = tuple((n, v) for n, v in projection.column("node", "dc_rail_v") if v is not None)
    ports = projection.column("node", "port_direction")
    outputs = tuple(n for n, d in ports if d == OUTPUT_DIRECTION)
    inputs = tuple(n for n, d in ports if d == INPUT_DIRECTION)
    roles = dict(projection.column("node", "port_role"))
    diff = {roles.get(n) for n in outputs} == {ROLE_DIFFERENTIAL_OUTPUT_P, ROLE_DIFFERENTIAL_OUTPUT_N}
    return ls_swing(devices, rails, tuple(node_v.items()), outputs, inputs, diff, input_dc_v)


def _ls_report(view_id, fields):
    return (("view", view_id), ("load_peak_margin_a", fields.load_peak_margin_a),
            ("nodes", tuple((n.net, n.c_slew_farad, n.i_charge_a, n.i_discharge_a, n.slew_charge_v_per_s, n.slew_discharge_v_per_s,
                             n.i_charge_res_a, n.i_discharge_res_a, n.sources) for n in fields.nodes)))


def _residual_report(found):
    return (("view", found.view), ("gain_residual_db", found.gain_residual_db), ("full_gain_db", found.full_gain_db),
            ("decomposed_gain_db", found.decomposed_gain_db), ("rout_residual_ohm", found.rout_residual_ohm),
            ("solve_residual", found.solve_residual), ("read_devices", found.read_devices),
            ("block_gain", tuple((b.key, b.gain_db, b.zout_ohm, b.decomposed_only) for b in found.blocks)),
            ("ff_contrib", tuple((c.id, c.gain_db, c.sign) for c in found.ff_contrib)),
            ("undefined", tuple(sorted(u.code for u in found.undefined))))
