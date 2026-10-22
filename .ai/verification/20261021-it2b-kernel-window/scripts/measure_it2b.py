"""IT-2b 감사 측정 하네스(감사 전용 -- 엔진 소스를 고치지 않는다, 관찰 래퍼는 반환값을 바꾸지 않는다).

usage: python -I measure_it2b.py <repo_root> <side> <circuit> <set library|heldout> <out_dir> [--tag T] [--eval-budget 40] [--probes 6]

사슬(공개 API, IT-2a 감사 하네스와 같은 순서): run_stage_a -> run_stage_b(diagnostic) -> build_kernel_context -> build_search_context -> find_front(sctx, []).
칸:
- os: 출력 포트마다 엔진 `node.dc_output_structure` 값(필드가 없는 base 는 None), 정지면 StructureUnresolvedError detail(rule_branch·nets) 또는 단계 A 정지 사유.
  `out_in_fprime` = 출력 넷 ∈ F′(레일 ∪ 입력 DC 선언이면 입력 포트) -- writer_plan.py `reached = output in fixed` 첫 줄 발동 수. W3·입력 DC 선언(표 §1 대조용).
- kernel: `block_columns._solve_input_window` 호출마다(= dc_columns compute 마다) θ 지문, 뿌리, `_solve` 호출 수, 창 측정 호출 수(head `_measure`, base
  `_Circuit.input_windows`), head 반환 `_Kernel`(status·tol·measured.window), 마지막 override.
- evals: `search.kernel.evaluate` 반환마다 status·θ hex·snapshot(성공) 또는 partial 의 `node.dc_window` 항목(lo·hi·constraints·input_status·tol_v hex)·입력 포트 dc_v.
- seal: `search.kernel.size_and_seal` 호출마다 입력 뿌리 y 값·봉인 성공·실패 항목·slack_v(o103 하네스와 같은 계수 식).
- probes: 봉인된 y 있는 θ 앞 N 개에서 y = 0·1 끝점 재평가(봉인/항목 7 거부·slack_v).
- fd_steps: `fd_jacobian._steps` 반환의 y 성분 스텝(hex).
- front·block_counters(G-10).
결과: <out_dir>/<side+tag>/<circuit>.json, 진행은 <out_dir>/progress.txt 에 칸마다 append.
"""
import argparse
import dataclasses
import enum
import hashlib
import json
import math
import os
import sys
import time
from pathlib import Path


def J(x, depth=0):
    if depth > 40:
        return repr(x)
    if x is None or isinstance(x, (bool, int, str)):
        return x
    if isinstance(x, float):
        return x.hex()
    if isinstance(x, enum.Enum):
        return x.value
    if dataclasses.is_dataclass(x) and not isinstance(x, type):
        return {f.name: J(getattr(x, f.name), depth + 1) for f in dataclasses.fields(x)}
    if hasattr(x, "_asdict"):
        return {k: J(v, depth + 1) for k, v in x._asdict().items()}
    if isinstance(x, dict):
        return [[J(k, depth + 1), J(v, depth + 1)] for k, v in sorted(x.items(), key=lambda kv: repr(kv[0]))]
    if isinstance(x, (tuple, list)):
        return [J(v, depth + 1) for v in x]
    if isinstance(x, (set, frozenset)):
        return sorted((J(v, depth + 1) for v in x), key=repr)
    return repr(x)


def H(x):
    return hashlib.sha256(json.dumps(J(x), sort_keys=True, ensure_ascii=False).encode("utf-8")).hexdigest()[:16]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("repo"); ap.add_argument("side"); ap.add_argument("circuit"); ap.add_argument("set"); ap.add_argument("out")
    ap.add_argument("--tag", default=""); ap.add_argument("--eval-budget", type=int, default=40); ap.add_argument("--probes", type=int, default=6); ap.add_argument("--os-only", action="store_true")
    a_ = ap.parse_args()
    skill = Path(a_.repo) / "skills" / "analog-gmid-design"
    sys.path.insert(0, str(skill))
    sys.path.append("C:/Users/HSLEE/AppData/Roaming/Python/Python314/site-packages")
    out_root = Path(a_.out)
    side_dir = out_root / (a_.side + a_.tag)
    side_dir.mkdir(parents=True, exist_ok=True)
    rec = {"circuit": a_.circuit, "side": a_.side + a_.tag, "set": a_.set, "repo": str(a_.repo)}
    out_json = side_dir / (a_.circuit + ".json")

    def save():
        out_json.write_text(json.dumps(rec, ensure_ascii=False, sort_keys=True, indent=1), encoding="utf-8")

    def col(name, value):
        rec[name] = value
        save()
        with (out_root / "progress.txt").open("a", encoding="utf-8") as f:
            f.write("%s %s %s %s\n" % (time.strftime("%H:%M:%S"), a_.side + a_.tag, a_.circuit, name))

    import gmid_engine.search  # noqa: F401
    import gmid_engine.sizing.block_columns  # noqa: F401
    bc = sys.modules["gmid_engine.sizing.block_columns"]
    import gmid_engine.search.fd_jacobian  # noqa: F401
    fdj = sys.modules["gmid_engine.search.fd_jacobian"]
    skm = sys.modules["gmid_engine.search.kernel"]
    from gmid_engine.core import BoundedLRU, read_pdk_decl, fp_of, StructureUnresolvedError, CANDIDATE_FAILURE_CLASSES
    from gmid_engine.lut import LutMemo, LutSpec, load_lut_set, resolve_lut_location
    from gmid_engine.pipeline import run_stage_a, run_stage_b
    from gmid_engine.search import SearchSettings, build_search_context, find_front, open_run
    from gmid_engine.sizing import build_kernel_context, dc_inputs_from_spec, pre_layout_lut_access, THETA_Y
    from gmid_engine.authoring import INPUT_DIRECTION

    # ------------------------------------------------------------ 관찰 래퍼 (반환값 그대로)
    ST = {"kernel": [], "cur": None, "seal": [], "evals": [], "steps": [], "probe_src": [], "on": False}
    HEAD_KIND = hasattr(bc, "_measure")
    orig_siw, orig_solve = bc._solve_input_window, bc._solve
    orig_meas = getattr(bc, "_measure", None)
    orig_iw = bc._Circuit.input_windows

    def solve_w(c):
        R = ST["cur"]
        if R is not None:
            R["n_solve"] += 1
        return orig_solve(c)

    def meas_w(c, root, values):
        R = ST["cur"]
        r = orig_meas(c, root, values)
        if R is not None:
            R["n_measure"] += 1
            R["measures"].append(None if r is None else [J(r.window[0]), J(r.window[1])])
        return r

    def iw_w(self, values, roots):
        R = ST["cur"]
        if R is not None:
            R["n_input_windows"] += 1
        return orig_iw(self, values, roots)

    def siw_w(c):
        R = {"theta_fp": H(sorted(c.theta.items())), "roots": list(c.input_roots()), "n_solve": 0, "n_measure": 0, "n_input_windows": 0,
             "measures": []}
        prev = ST["cur"]
        ST["cur"] = R
        try:
            r = orig_siw(c)
        finally:
            ST["cur"] = prev
        if HEAD_KIND:
            R["status"] = r.status
            R["tol"] = J(r.tol)
            R["window"] = None if r.measured is None else [J(r.measured.window[0]), J(r.measured.window[1])]
        R["override"] = J(dict(c.override))
        if ST["on"]:
            ST["kernel"].append(R)
        return r

    bc._solve_input_window, bc._solve = siw_w, solve_w
    if HEAD_KIND:
        bc._measure = meas_w
    bc._Circuit.input_windows = iw_w

    orig_steps = fdj._steps

    def steps_w(sctx, variables, base):
        r = orig_steps(sctx, variables, base)
        if ST["on"]:
            ST["steps"].append([[J(v.component), J(h)] for v, h in zip(variables, r) if v.component[0] == THETA_Y])
        return r
    fdj._steps = steps_w

    INPUTS = set()
    orig_sas = skm.size_and_seal

    def info(exc):
        r = getattr(exc, "record", None)
        det = dict(r.detail) if r is not None and getattr(r, "detail", None) else None
        d = {"ok": False, "exc": type(exc).__name__}
        if isinstance(det, dict):
            d.update(item=det.get("item"), reason=det.get("reason"))
            idet = det.get("item_detail")
            if idet:
                d["slack_v"] = J(dict(idet).get("slack_v"))
        return d

    def sas_w(dc, theta, **kw):
        ys = {k[1]: v for k, v in dict(theta).items() if isinstance(k, tuple) and k[0] == THETA_Y and k[1] in INPUTS}
        try:
            ev = orig_sas(dc, theta, **kw)
        except CANDIDATE_FAILURE_CLASSES as exc:
            if ST["on"]:
                ST["seal"].append({"y": {k: J(v) for k, v in ys.items()}, **info(exc)})
            raise
        if ST["on"]:
            ST["seal"].append({"y": {k: J(v) for k, v in ys.items()}, "ok": True, "sealed": ev.sealed is not None})
            if ev.sealed is not None and ys and len(ST["probe_src"]) < a_.probes:
                ST["probe_src"].append((dc, dict(theta)))
        return ev
    skm.size_and_seal = sas_w

    def windows_of(snap):
        if snap is None:
            return None
        try:
            return [[n, J(w.lo), J(w.hi), w.constraints, getattr(w, "input_status", "<no field>"), J(getattr(w, "tol_v", "<no field>"))]
                    for n, w in snap.column("node", "dc_window")]
        except Exception as e:  # noqa: BLE001 -- 관찰 전용
            return "unreadable:" + type(e).__name__

    orig_eval = skm.evaluate

    def ev_w(*args, **kw):
        r = orig_eval(*args, **kw)
        if ST["on"]:
            snap = r.evaluation.snapshot if r.evaluation is not None else r.partial
            dcv = None
            if snap is not None:
                try:
                    v = dict(snap.column("node", "dc_v"))
                    dcv = {n: J(v[n]) for n in sorted(INPUTS) if n in v}
                except Exception:  # noqa: BLE001
                    dcv = "unreadable"
            ST["evals"].append({"status": r.status, "theta_hex": list(r.key.theta_hex), "cells": J(r.key.cells),
                                "from": "evaluation" if r.evaluation is not None else ("partial" if r.partial is not None else None),
                                "snapshot_fp": None if snap is None else snap.fp, "windows": windows_of(snap), "input_dc_v": dcv})
        return r
    for name, mod in list(sys.modules.items()):
        if name.startswith("gmid_engine") and getattr(mod, "evaluate", None) is orig_eval:
            setattr(mod, "evaluate", ev_w)

    # ------------------------------------------------------------ 입력
    DEVICE_KINDS = (("nfet_01v8", "nmos"), ("pfet_01v8", "pmos"))
    CAP_SUFFIX = (("nmos", "_n"), ("pmos", "_p"))
    loc = resolve_lut_location(str(skill / "assets" / "lut_v2_location.json"), os.environ)
    man = json.loads(Path(loc.manifest_path).read_text(encoding="utf-8"))
    kinds_map = dict(DEVICE_KINDS)
    mins = {}
    for e in man["slices"]:
        mins[kinds_map[e["device"]]] = min(e["w_um"] * 1e-6, mins.get(kinds_map[e["device"]], float("inf")))
    dm = BoundedLRU(16)
    pdk = read_pdk_decl(str(skill / "assets" / "sky130_pdk_decl.json"), dm)
    q = dict(pdk.quantities)
    grid = float(man.get("manufacturing_grid_m", 5e-9))
    lspec = LutSpec(grid, tuple(sorted(mins.items())), DEVICE_KINDS, CAP_SUFFIX,
                    noise_ef=(("nmos", q["noise_ef_nmos"].value_m), ("pmos", q["noise_ef_pmos"].value_m)))
    lut = load_lut_set(loc.manifest_path, loc.cap_npz_path, lspec, pdk_root=loc.pdk_root, verify_midpoints=loc.midpoints_path,
                       noise_npz=loc.noise_path, mismatch_npz=loc.mismatch_path)
    rule = read_pdk_decl(str(skill / "assets" / "sky130_lut_rule_decl.json"), dm)
    settings = SearchSettings(7200.0, a_.eval_budget, (1e2, 1e5), (("front_budget_s", "it2b audit"),), (1e-13, 1e-10))

    base_dir = skill / "assets" / a_.set
    work = side_dir / ("work_" + a_.circuit)
    work.mkdir(parents=True, exist_ok=True)
    donors, counters = open_run()
    t0 = time.perf_counter()
    a = run_stage_a(base_dir / (a_.circuit + ".topology.json"), base_dir / (a_.circuit + ".sizing_spec.json"), lut,
                    output_dir=work, donors=donors, counters=counters)
    rec["stage_a"] = {"status": a.status, "exit_code": a.exit_code,
                      "stop_reasons": J(a.report.get("stop_reasons") if isinstance(a.report, dict) else getattr(a.report, "stop_reasons", repr(type(a.report))))}
    save()
    if a.s1 is None or a.spec is None:
        col("os", {"stop": "stage_a_" + a.status, "stop_reasons": rec["stage_a"]["stop_reasons"]})
        return
    s1snap = a.s1.snapshot
    inputs_decl = dc_inputs_from_spec(a.spec)
    rails = sorted(n for n, r in s1snap.column("node", "is_rail") if r)
    pdir = dict(s1snap.column("node", "port_direction"))
    in_ports = sorted(n for n, d in pdir.items() if d == INPUT_DIRECTION)
    out_ports = sorted(n for n, d in pdir.items() if d == "output")
    INPUTS.update(in_ports)
    in_dc = inputs_decl.input_dc_v is not None
    fprime = set(rails) | (set(in_ports) if in_dc else set())
    kctx, stop = None, None
    b = None
    memo = LutMemo(lut, point=1 << 16, curve=1 << 14, root=1 << 16)
    if a.status == "ok":
        b = run_stage_b(a, memo, pdk, output_dir=work, diagnostic=True, settings=settings)
        rec["stage_b"] = {"status": b.status}
        try:
            kctx = build_kernel_context(b.s1, inputs_decl, pre_layout_lut_access(memo), donors=a.donors, counters=a.counters)
        except StructureUnresolvedError as e:
            rec_ = getattr(e, "record", None)
            stop = {"exc": type(e).__name__, "detail": J(getattr(rec_, "detail", None)), "devices": J(getattr(rec_, "devices", None)),
                    "repr": repr(e)[:400]}
    else:                                              # 단계 A 정지 -- 분류표 작성(de1_classify.py:41)과 같이 a.s1 로 쓰기 계획까지 시도(OS 칸 전용)
        try:
            kctx = build_kernel_context(a.s1, inputs_decl, pre_layout_lut_access(memo), donors=a.donors, counters=a.counters)
            stop = {"stage_a": a.status, "writer_plan": "ok"}
        except StructureUnresolvedError as e:
            rec_ = getattr(e, "record", None)
            stop = {"stage_a": a.status, "exc": type(e).__name__, "detail": J(getattr(rec_, "detail", None)),
                    "devices": J(getattr(rec_, "devices", None)), "repr": repr(e)[:400]}
    eng = None
    if kctx is not None:
        try:
            eng = dict(kctx.base.column("node", "dc_output_structure"))
        except Exception as e:  # noqa: BLE001 -- base 에는 필드가 없다
            eng = "absent:" + type(e).__name__
    col("os", {"outputs": out_ports, "inputs": in_ports, "rails": rails, "input_dc_declared": in_dc,
               "input_dc_v": J(inputs_decl.input_dc_v), "w3": J(sorted(n for n, _v in inputs_decl.node_targets)),
               "engine": J(eng) if not isinstance(eng, dict) else {o: eng.get(o) for o in out_ports},
               "engine_keys_not_outputs": sorted(set(eng) - set(out_ports)) if isinstance(eng, dict) else None,
               "out_in_fprime": [o for o in out_ports if o in fprime], "stop": stop})
    if a_.set != "library" or kctx is None or a.status != "ok" or a_.os_only:
        rec["wall_s"] = time.perf_counter() - t0
        save()
        return
    writers = dict(kctx.base.column("node", "dc_writer"))
    col("w4", {"roots": sorted([n, w.y_key, n in in_ports] for n, w in writers.items() if w.relation == "free_window")})
    sctx = build_search_context(kctx, a.spec, settings, None, pdk, rule, code_fp=a.code_fp)
    ST["on"] = True
    fr = find_front(sctx, [])
    probes = []
    for i, (dc, theta) in enumerate(ST["probe_src"]):
        ykeys = [k for k in theta if isinstance(k, tuple) and k[0] == THETA_Y and k[1] in INPUTS]
        for yv in (0.0, 1.0):
            th = dict(theta)
            for k in ykeys:
                th[k] = yv
            try:
                ev = orig_sas(dc, th)
                probes.append({"src": i, "y": yv, "ok": True, "sealed": ev.sealed is not None, "windows": windows_of(ev.snapshot)})
            except CANDIDATE_FAILURE_CLASSES as exc:
                probes.append({"src": i, "y": yv, **info(exc)})
    ST["on"] = False

    def pt(p):
        r = p.result
        return {"point_id": p.point_id, "status": r.status, "theta": [[list(k), float(v).hex()] for k, v in r.theta],
                "cells": list(r.key.cells), "power_w": float(r.objectives.power_w).hex(), "area_m2": float(r.objectives.area_m2).hex()}
    fronts = {"front": [pt(p) for p in fr.front], "pending": [pt(p) for p in fr.pending_front], "unmeasured": [pt(p) for p in fr.unmeasured_front]}
    col("front", {"n_front": len(fr.front), "n_pending": len(fr.pending_front), "n_unmeasured": len(fr.unmeasured_front), "front_fp": fp_of(fronts),
                  "fronts": fronts, "failed_eps": len(fr.failed_eps),
                  "perf": {k: v for k, v in fr.perf if isinstance(v, (int, float, str)) and k != "wall_s"}})
    col("kernel", ST["kernel"])
    col("evals", ST["evals"])
    seal = ST["seal"]
    ys = [v for c in seal for v in c["y"].values()]
    fy = [float.fromhex(v) for v in ys]
    col("seal", {"n_calls": len(seal), "n_with_y": sum(1 for c in seal if c["y"]),
                 "y_exact_0": sum(1 for v in fy if v == 0.0), "y_exact_1": sum(1 for v in fy if v == 1.0),
                 "y_near_end_1e-6": sum(1 for v in fy if min(v, 1 - v) <= 1e-6),
                 "fail_item7": sum(1 for c in seal if not c.get("ok") and c.get("item") == 7),
                 "fail_any": sum(1 for c in seal if not c.get("ok")),
                 "fail_item7_at_end": sum(1 for c in seal if not c.get("ok") and c.get("item") == 7
                                          and any(min(float.fromhex(v), 1 - float.fromhex(v)) <= 1e-6 for v in c["y"].values())),
                 "rows": seal})
    col("probes", probes)
    col("fd_steps", ST["steps"])
    pc = a.counters.snapshot()
    col("block_counters", {"rows": [[r.block, r.part, r.calls, r.reuses, r.grafts, r.replays, r.computes, r.recomputes_same_input] for r in pc.blocks],
                           "totals": J(pc.block_totals)})
    rec["wall_s"] = time.perf_counter() - t0
    save()


if __name__ == "__main__":
    main()
