"""measure only (NOT a role artifact): M1..M9 chain on the M1-base stand-in (<scratch>/r, HEAD = current card base).
    python -B chain_lean.py <card>[,<card>...] <scratch root>
Per card: plan(base) -> gen226 -> commit -> check -> G1 static V3 -> IMPORT-ANY (design §10 bash fn verbatim) -> import_layering
-> E3b-form per exporting split file (base->head and base->base) -> W-2 ACF foreign-cwd load -> W-1 shim import reads.
One JSON line per card appended to <scratch>/out/chain.jsonl; full plan/check/gen JSON per card in <scratch>/out/<card>/."""
import json
import os
import subprocess
import sys
import time

SCR = sys.argv[2].rstrip("/")
S = SCR + "/r"
A = "skills/analog-gmid-design/assets/"
PY = "C:/Python314/python.exe"
K = SCR + "/kit"
O = SCR + "/out"
GC = SCR + "/cache/tools/gates"
MP = ["--plan", "docs/01-plan/features/gain-budget-gmid-sizing.plan.md", "--registry",
      "docs/03-analysis/gain-budget-gmid-sizing.function-registry.md", "--split", "sizing_recipe.py", "stick_diagram.py",
      "topology_library.py", "design_report.py", "audit_current_forced.py", "--keep", "audit_current_forced.py",
      "--aliases", '{"optimizer": "theta_search.py"}']
ENV = dict(os.environ, TMP=SCR + "/tmp", TEMP=SCR + "/tmp", PYTHONIOENCODING="utf-8", MP_STMT_KEY="names",
           APPDATA="C:/Users/HSLEE/AppData/Roaming", HOME="C:/Users/HSLEE", MSYS_NO_PATHCONV="1")
EXCL = r'^(\.ai/verification/|docs/03-analysis/gain-budget-gmid-sizing-function-audit/probe_stage_partition\.py$)'
CARDS = sys.argv[1].split(",")
SPLIT_STEMS = ["sizing_recipe", "stick_diagram", "topology_library", "design_report", "audit_current_forced"]


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
    d = os.path.join(O, card)
    os.makedirs(d, exist_ok=True)
    base = git("rev-parse", "HEAD")
    pr = run([PY, "-B", K + "/move_plan_sim.py", "plan", "--root", S, "--rev", "HEAD"] + MP)
    plan = first_json(pr.stdout)
    pj = d + "/plan_base.json"
    json.dump(plan, open(pj, "w", encoding="utf-8"), ensure_ascii=False)
    pl_sum = {k: len(plan[k]) for k in ("upward", "cycles", "unassigned", "conflicts", "reg_mismatch", "import_time_high", "import_conflicts")}
    rules = {}
    for uid, v in plan["assignment"].items():
        if v["mod"] == card + ".py" and not uid.startswith(card + ".py::"):
            rules[uid] = v["rule"]
    g = run([PY, "-B", K + "/gen226.py", S, pj, card + ".py"])
    gen = first_json(g.stdout) or {"ERROR": g.stderr[-600:]}
    json.dump(gen, open(d + "/gen.json", "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    git("add", "-A", "skills")
    git("commit", "-q", "-m", "sim %s (measure only)" % card)
    head = git("rev-parse", "HEAD")
    tc = time.time()
    cr = run([PY, "-B", K + "/move_plan_sim.py", "check", "--root", S, "--base", base, "--head", head, "--card", card + ".py"] + MP)
    ck = first_json(cr.stdout) or {"findings": {"ERROR": [cr.stderr[-400:]]}, "moved_units": {}, "moved_defs": {}}
    json.dump(ck, open(d + "/check.json", "w", encoding="utf-8"), ensure_ascii=False)
    t_check = round(time.time() - tc, 1)
    v3={};ia_out=[];il={};e3b={};w2=None;w1=''
    rec = {"card": card, "base": base, "head": head, "plan": pl_sum, "assigned": len(rules), "rules": rules,
           "units": len(gen.get("units", [])), "gen": {k: gen.get(k) for k in ("mod_imports_head", "mod_imports_tail", "reexports", "spans", "n_defs_in_units")},
           "gen_error": gen.get("ERROR"),
           "check_verdict": ck.get("verdict"), "check_findings": {k: len(v) for k, v in ck["findings"].items() if v},
           "check_sample": {k: v[:3] for k, v in ck["findings"].items() if v}, "t_check": t_check,
           "moved_units": len(ck.get("moved_units", {})), "moved_defs": len(ck.get("moved_defs", {})), "v3_static": v3,
           "import_any": ia_out, "import_layering": {"present": il.get("present"), "n_findings": len(il.get("findings", []) or []),
                                                    "findings": (il.get("findings") or [])[:6]},
           "e3b": e3b, "w2_acf_foreign_load": w2, "w1_shim_reads": w1, "sec": round(time.time() - t0, 1)}
    with open(O + "/chain.jsonl", "a", encoding="utf-8") as fh:
        fh.write(json.dumps(rec, ensure_ascii=False) + "\n")
    print(json.dumps({k: rec[k] for k in ("card", "units", "assigned", "plan", "check_findings", "moved_units", "moved_defs", "import_any",
                                           "w2_acf_foreign_load", "sec")} | {"v3": v3, "layer": rec["import_layering"]["n_findings"],
                                                                          "e3b": {m: (v["fail_head"], v["fail_bb"], len(v["new_fail"])) for m, v in e3b.items()}},
                     ensure_ascii=False), flush=True)
