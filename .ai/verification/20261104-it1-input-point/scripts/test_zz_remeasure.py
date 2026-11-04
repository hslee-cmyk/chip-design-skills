"""기준선 재측정(판정자, 격리 복제본, 커밋 안 함). 회로 하나 = 프로세스 하나. 기존 test 의 _run·_sha·키 목록 그대로."""
import dataclasses
import json
import os

from test_s0_layer_9circuits import BASELINE, _run, _sha, _value_fps, env  # noqa: F401

CIRCUIT = os.environ["RM_CIRCUIT"]
OUT = os.environ["RM_OUT"]
RECORD_KEYS = {"schema_fp": ("kernel", "theta_schema"), "fixed_values_fp": ("kernel", "fixed_values"),
               "resistor_values_fp": ("kernel", "resistor_values"), "l_ties_fp": ("kernel", "l_ties"),
               "search_domain_fp": ("kernel", "search_domain"),
               "mismatch_source_fp": ("kernel", "mismatch_source"), "passive_area_decl_fp": ("kernel", "passive_area_decl"),
               "model_error_fp": ("kernel", "model_error"), "metric_structure_fp": ("s1v", "metric_structure"),
               "noise_input_cells_fp": ("s1v", "noise_input_cells")}
START_KEYS = (("rungs", "ladder_fp"), ("conflicts", "conflicts_fp"), ("inactive", "inactive_fp"), ("macro", "macro_fp"),
              ("records", "records_fp"), ("area_est_m2", "area_est_m2_fp"), ("area_fraction", "area_fraction_fp"),
              ("uncovered", "uncovered_fp"))


def test_remeasure(env):  # noqa: F811
    want = BASELINE[CIRCUIT]
    run = _run(env, CIRCUIT)
    f, s = run.first, run.second
    new = json.loads(json.dumps(want))
    new["status"] = f.status
    diff = []
    if f.status != want["status"]:
        diff.append("status %r -> %r" % (want["status"], f.status))
    for k, sha in want["stage_a_sha"].items():
        v = _sha(f.report_a.get(k))
        new["stage_a_sha"][k] = v
        if v != sha:
            diff.append("stage_a." + k)
    for k, sha in want["stage_b_sha"].items():
        v = _sha(f.report_b.get(k))
        new["stage_b_sha"][k] = v
        if v != sha:
            diff.append("stage_b." + k)
    ach = f.report_b.get("achievability") or {}
    for k, sha in want["achievability_sha"].items():
        v = _sha(ach.get(k))
        new["achievability_sha"][k] = v
        if v != sha:
            diff.append("achievability." + k)
    cause = {"dof": ach.get("dof")}
    if f.base is not None and "start" in want:
        base = f.base
        for device, fp in want["start"]["row_fp"].items():
            got = base.field("device", device, "start.row")
            v = None if got is None else got.value_fp
            new["start"]["row_fp"][device] = v
            if v != fp:
                diff.append("device %s start.row" % device)
        for field, key in START_KEYS:
            got = base.field("graph", "start", field)
            v = None if got is None else got.value_fp
            new["start"][key] = v
            if v != want["start"][key]:
                diff.append("graph/start: " + field)
        for key, (record, field) in RECORD_KEYS.items():
            if key not in want["kernel"]:
                continue
            got = base.field("graph", record, field)
            v = None if got is None else got.value_fp
            new["kernel"][key] = v
            if v != want["kernel"][key]:
                diff.append("graph/%s: %s" % (record, field))
        cause["theta"] = sorted(map(list, base.value("graph", "kernel", "theta_schema").components))
        dom = base.value("graph", "kernel", "search_domain")
        cause["domain_vars"] = [str(getattr(v, "component", v)) for v in getattr(dom, "variables", ())]
        cause["domain_ties"] = str(getattr(dom, "ties", ""))[:800]
        cause["rungs"] = str(base.value("graph", "start", "rungs"))[:6000]
        from gmid_engine.core import fp_of as _f
        rr = base.value("graph", "start", "rungs")
        cause["rung_vfp"] = base.field("graph", "start", "rungs").value_fp
        cause["rung_fps"] = [[_f(r.t), _f(r.theta), _f(r.cells), _f(r.current_ref), [type(x[1]).__name__ for x in r.theta][:3], str(r.current_ref)[:300]] for r in rr] if isinstance(rr, tuple) else type(rr).__name__
        cause["dc_coord"] = {m: (c.role, c.relation, c.partner) for m, c in base.column("device", "dc_coord")}
        cause["inputs"] = {n: (w.tier, w.relation, w.known, w.y_key) for n, w in base.column("node", "dc_writer") if n in dict(base.column("node", "port_direction")) and dict(base.column("node", "port_direction"))[n] == "input"}
        V_second_same = _value_fps(f.base) == _value_fps(s.base)
    else:
        V_second_same = None
    rec = {"circuit": CIRCUIT, "status": f.status, "diff": diff, "bit_same_a": f.bytes_a == s.bytes_a, "bit_same_b": f.bytes_b == s.bytes_b,
           "s0_fp_same": V_second_same, "new": new, "cause": cause}
    with open(OUT, "wb") as fh:
        fh.write(json.dumps(rec, ensure_ascii=False, default=str).encode("utf-8"))
