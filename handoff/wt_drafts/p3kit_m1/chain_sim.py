"""scratch: simulate M2..M9 after the simulated M1 (clone C:/g200/s at m1head) with the same generator and judges.
Per card: plan at base -> gen_move -> commit -> check (sim) -> G1 moved_defs/V3 static -> IMPORT-ANY (every N3.10 + split module
first in a new process) -> import_layering. One JSON line per card to C:/g200/out/chain.jsonl (append, WP-11)."""
import json
import os
import subprocess
import sys
import time

S = "C:/g200/s"
A = "skills/analog-gmid-design/assets/"
PY = "C:/Python314/python.exe"
T = "C:/g200/tools"
OUT = "C:/g200/out/chain.jsonl"
MP = ["--plan", "docs/01-plan/features/gain-budget-gmid-sizing.plan.md", "--registry",
      "docs/03-analysis/gain-budget-gmid-sizing.function-registry.md", "--split", "sizing_recipe.py", "stick_diagram.py",
      "topology_library.py", "design_report.py", "audit_current_forced.py", "--keep", "audit_current_forced.py",
      "--aliases", '{"optimizer": "theta_search.py"}']
ENV = dict(os.environ, TMP="C:/g200/tmp", TEMP="C:/g200/tmp", PYTHONIOENCODING="utf-8", MP_STMT_KEY="hash",
           APPDATA="C:/Users/HSLEE/AppData/Roaming", HOME="C:/Users/HSLEE")
CARDS = sys.argv[1].split(",")
MODS = ["gmid_lut", "topology_authoring", "circuit_state_graph", "gmid_sizing_engine", "circuit_metrics", "theta_search",
        "stick_diagram", "sizing_layout_convergence", "instance_report_builder", "gmid_design_pipeline",
        "sizing_recipe", "topology_library", "design_report", "audit_current_forced"]


def git(*a):
    r = subprocess.run(["git", "-C", S, "-c", "user.name=m", "-c", "user.email=m@x"] + list(a),
                       capture_output=True, text=True, encoding="utf-8")
    if r.returncode:
        raise SystemExit("git %s: %s" % (a, r.stderr))
    return r.stdout.strip()


def run(args, **kw):
    return subprocess.run(args, capture_output=True, text=True, encoding="utf-8", env=ENV, **kw)


def first_json(s):
    for line in s.splitlines():
        if line.startswith("{"):
            return json.loads(line)
    return None


for card in CARDS:
    t0 = time.time()
    base = git("rev-parse", "HEAD")
    pr = run([PY, "-B", T + "/move_plan_sim.py", "plan", "--root", S, "--rev", "HEAD"] + MP)
    plan = first_json(pr.stdout)
    pj = "C:/g200/out/chain_plan_%s.json" % card
    json.dump(plan, open(pj, "w", encoding="utf-8"), ensure_ascii=False)
    pl_sum = {k: len(plan[k]) for k in ("upward", "cycles", "unassigned", "conflicts", "reg_mismatch", "import_time_high", "import_conflicts")}
    g = run([PY, "-B", T + "/gen_move.py", S, pj, card + ".py"])
    gen = first_json(g.stdout) or {"ERROR": g.stderr[-400:]}
    git("add", "-A", "skills")
    git("commit", "-q", "-m", "sim %s (measure only)" % card)
    head = git("rev-parse", "HEAD")
    ck = first_json(run([PY, "-B", T + "/move_plan_sim.py", "check", "--root", S, "--base", base, "--head", head,
                         "--card", card + ".py"] + MP).stdout) or {"findings": {"ERROR": ["no json"]}, "moved_units": {}, "moved_defs": {}}
    st = run([PY, "-B", "-c", (
        "import sys,json;sys.path.insert(0,%r);import reachability as rch, mutate_changed as mc;"
        "b={k:v for k,v in rch.read_tree(%r,%r,rch.GRAPH_PREFIXES).items() if rch._is_source(k)};"
        "h={k:v for k,v in rch.read_tree(%r,%r,rch.GRAPH_PREFIXES).items() if rch._is_source(k)};"
        "mv=rch.moved_defs(b,h);d=[];m=0;pre=0\n"
        "for p,s in h.items():\n"
        " if b.get(p)==s: continue\n"
        " for q,f in mc.changed_defs(b.get(p),s):\n"
        "  n=sum(1 for _ in mc.mutants(f,s)); pre+=n\n"
        "  if rch.g1_excluded(mv,p,q,f): continue\n"
        "  d.append(p.split('/')[-1]+'::'+q); m+=n\n"
        "print(json.dumps({'defs':d[:8],'n_defs':len(d),'mutants':m,'pre_g1_mutants':pre,'moved_defs':len(mv['defs']),"
        "'rejected':{k.split('/')[-1]:v for k,v in list(mv['rejected'].items())[:8]},'n_rejected':len(mv['rejected'])}))"
    ) % (S + "/tools/gates", S, base, S, head)])
    v3 = first_json(st.stdout) or {"ERROR": st.stderr[-300:]}
    imp = {}
    for m in MODS:
        if not os.path.exists(os.path.join(S, A, m + ".py")):
            continue
        p = run([PY, "-B", "-c", "import %s" % m], cwd=os.path.join(S, A))
        imp[m] = "ok" if p.returncode == 0 else (p.stderr.strip().splitlines() or ["?"])[-1][:200]
    il = first_json(run([PY, "-B", S + "/tools/gates/import_layering.py", "--root", S]).stdout) or {}
    rec = {"card": card, "base": base, "head": head, "plan": pl_sum, "units": len(gen.get("units", [])), "gen": gen,
           "check_verdict": ck.get("verdict"), "check_findings": {k: len(v) for k, v in ck["findings"].items() if v},
           "check_sample": {k: v[:3] for k, v in ck["findings"].items() if v},
           "moved_units": len(ck.get("moved_units", {})), "moved_defs": len(ck.get("moved_defs", {})), "v3_static": v3,
           "import_first": imp, "import_fail": {k: v for k, v in imp.items() if v != "ok"},
           "import_layering": {"present": il.get("present"), "n_findings": len(il.get("findings", []) or []),
                               "findings": (il.get("findings") or [])[:6]},
           "sec": round(time.time() - t0, 1)}
    with open(OUT, "a", encoding="utf-8") as fh:
        fh.write(json.dumps(rec, ensure_ascii=False) + "\n")
    print(json.dumps({k: rec[k] for k in ("card", "units", "plan", "check_verdict", "check_findings", "moved_units", "moved_defs",
                                           "import_fail", "sec")} | {"v3": {k: v3.get(k) for k in ("n_defs", "mutants", "pre_g1_mutants", "n_rejected")},
                                                                     "layer_findings": rec["import_layering"]["n_findings"]}, ensure_ascii=False), flush=True)
