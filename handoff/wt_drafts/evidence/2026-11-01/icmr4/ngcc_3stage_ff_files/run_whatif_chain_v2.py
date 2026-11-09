"""what-if 사슬: TEMP structure.json(dc_role M8·M14 = signal, 승인 없음 표지)로 단계 A -> B -> 탐색(find_front)까지.
저장소 쓰기 0 -- structure.json 은 work_dir 에만 만든다(run_stage_a structure_path 인자). 엔진 소스 수정 0.
usage: python run_whatif_chain.py <work_dir> <log_file> [--eval-budget N] [--front-budget-s S]
"""
import argparse
import json
import os
import sys
import time
import traceback
from pathlib import Path

SKILL = Path(r"C:/Users/HSLEE/Documents/Todoc/fpga/chip-design-skills/skills/analog-gmid-design")
LIBRARY = SKILL / "assets" / "library"
CIRCUIT = "ngcc_3stage_ff"
DEVICE_KINDS = (("nfet_01v8", "nmos"), ("pfet_01v8", "pmos"))
CAP_SUFFIX = (("nmos", "_n"), ("pmos", "_p"))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("work")
    ap.add_argument("logf")
    ap.add_argument("--eval-budget", type=int, default=40)
    ap.add_argument("--front-budget-s", type=float, default=600.0)
    a_ = ap.parse_args()
    work, logf = Path(a_.work), Path(a_.logf)
    work.mkdir(parents=True, exist_ok=True)

    def log(msg):
        with open(logf, "a", encoding="utf-8") as f:
            f.write("%s [whatif] %s\n" % (time.strftime("%Y-%m-%d %H:%M:%S"), msg))

    sys.path.insert(0, str(SKILL))
    from gmid_engine.authoring import load_topology
    from gmid_engine.core import BoundedLRU, read_pdk_decl
    from gmid_engine.graph import structure_rule_fp
    from gmid_engine.lut import LutMemo, LutSpec, load_lut_set, resolve_lut_location
    from gmid_engine.pipeline import run_stage_a, run_stage_b
    from gmid_engine.search import SearchSettings, build_search_context, find_front, open_run
    from gmid_engine.sizing import build_kernel_context, dc_inputs_from_spec, pre_layout_lut_access

    topo = load_topology(str(LIBRARY / (CIRCUIT + ".topology.json")))
    st = {"schema_version": "1", "topology_hash": topo.connectivity_fp, "rule_hash": structure_rule_fp(), "facts": [
        {"concept": "dc_role", "subject": m, "value": "signal", "status": "ratified",
         "evidence": {"rule": "whatif: gate V1 = M2/M4 drain (stage-1 high-Z output)", "nets": ["V1", "gnd"]},
         "approval_id": "WHATIF-icmr4-not-user-approved"} for m in ("M8", "M14")]}
    sp = work / (CIRCUIT + ".structure.json")
    sp.write_text(json.dumps(st, ensure_ascii=False, indent=1), encoding="utf-8")
    log("structure.json(TEMP) = %s" % sp)

    loc = resolve_lut_location(str(SKILL / "assets" / "lut_v2_location.json"), os.environ)
    man = json.loads(Path(loc.manifest_path).read_text(encoding="utf-8"))
    kinds = dict(DEVICE_KINDS)
    mins = {}
    for e in man["slices"]:
        mins[kinds[e["device"]]] = min(e["w_um"] * 1e-6, mins.get(kinds[e["device"]], float("inf")))
    dm = BoundedLRU(16)
    pdk = read_pdk_decl(str(SKILL / "assets" / "sky130_pdk_decl.json"), dm)
    q = dict(pdk.quantities)
    grid = float(man.get("manufacturing_grid_m", 5e-9))
    spec = LutSpec(grid, tuple(sorted(mins.items())), DEVICE_KINDS, CAP_SUFFIX,
                   noise_ef=(("nmos", q["noise_ef_nmos"].value_m), ("pmos", q["noise_ef_pmos"].value_m)))
    lut = load_lut_set(loc.manifest_path, loc.cap_npz_path, spec, pdk_root=loc.pdk_root, verify_midpoints=loc.midpoints_path,
                       noise_npz=loc.noise_path, mismatch_npz=loc.mismatch_path)
    rule = read_pdk_decl(str(SKILL / "assets" / "sky130_lut_rule_decl.json"), dm)
    settings = SearchSettings(a_.front_budget_s, a_.eval_budget, (1e2, 1e5), (("front_budget_s", "icmr4 whatif"),), (1e-13, 1e-10))
    log("lut loaded")
    out = work / "out"
    donors, counters = open_run()
    a = run_stage_a(LIBRARY / (CIRCUIT + ".topology.json"), LIBRARY / (CIRCUIT + ".sizing_spec.json"), lut, output_dir=out,
                    donors=donors, counters=counters, structure_path=sp)
    ra = json.loads(Path(a.report_paths[0]).read_text(encoding="utf-8"))
    log("stage A status=%s exit=%s" % (a.status, a.exit_code))
    for k in ("stop_reasons", "review_needed", "applied_facts", "ff_ratio_candidates"):
        log("stage A %s = %s" % (k, json.dumps(ra.get(k), ensure_ascii=False)[:3000]))
    for v in ra.get("views") or []:
        log("stage A view %s" % json.dumps(v, ensure_ascii=False)[:2500])
    memo = LutMemo(lut, point=1 << 16, curve=1 << 14, root=1 << 16)
    b = run_stage_b(a, memo, pdk, output_dir=out, diagnostic=True, settings=settings)
    rb = json.loads(Path(b.report_paths[0]).read_text(encoding="utf-8"))
    log("stage B status=%s exit=%s stop=%s" % (b.status, b.exit_code, json.dumps(rb.get("stop_reasons"), ensure_ascii=False)))
    ach = rb.get("achievability") or {}
    log("stage B verdict=%s reasons=%s" % (ach.get("verdict"), json.dumps(ach.get("reasons"), ensure_ascii=False)[:2000]))
    if (a.status, b.status) != ("ok", "ok"):
        log("chain stops before search")
        return
    try:
        kctx = build_kernel_context(b.s1, dc_inputs_from_spec(a.spec), pre_layout_lut_access(memo), donors=a.donors, counters=a.counters)
        s3 = work / "s3"
        s3.mkdir(exist_ok=True)
        sctx = build_search_context(kctx, a.spec, settings, str(s3), pdk, rule, code_fp=a.code_fp)
        log("search context built")
        t0 = time.time()
        fr = find_front(sctx, [])
        log("find_front done %.1f s" % (time.time() - t0))
        for name in ("front", "pending", "unmeasured", "notes", "perf"):
            val = getattr(fr, name, None)
            log("find_front.%s = %s" % (name, repr(val)[:4000]))
        stat = {}
        for r in sorted(sctx.cache.values(), key=lambda r: r.seq):
            key = (getattr(r, "status", None), repr(getattr(r, "failure", None))[:300])
            stat[key] = stat.get(key, 0) + 1
        for (s, f), n in sorted(stat.items(), key=lambda x: -x[1])[:30]:
            log("eval status=%s n=%d failure=%s" % (s, n, f))
        viol = {}
        best = None
        for r in sorted(sctx.cache.values(), key=lambda r: r.seq):
            if r.status != "sealed":
                continue
            row = {c.name: c.c for c in r.constraints}
            bad = tuple(sorted(n for n, v in row.items() if v is not None and v > 0))
            und = tuple(sorted(n for n, v in row.items() if v is None))
            viol[(bad, und)] = viol.get((bad, und), 0) + 1
            nb = len(bad)
            if best is None or nb < best[0]:
                best = (nb, r.seq, row, repr(r.unmeasured)[:2500], repr(r.warnings)[:1500], repr(r.theta)[:1500])
        for (bad, und), n in sorted(viol.items(), key=lambda x: -x[1]):
            log("sealed n=%d violated(c>0)=%s undefined(c=None)=%s" % (n, bad, und))
        if best:
            log("best seq=%d nviol=%d constraints c=%s" % (best[1], best[0], best[2]))
            log("best unmeasured=%s" % best[3])
            log("best warnings=%s" % best[4])
            log("best theta=%s" % best[5])
    except Exception:
        log("search EXC\n" + traceback.format_exc())


if __name__ == "__main__":
    main()
