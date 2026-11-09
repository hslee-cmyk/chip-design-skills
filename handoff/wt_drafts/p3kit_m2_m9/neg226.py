"""measure only (NOT a role artifact): rejection self-check of the simulated M-card judges, generic per card.
    python -B neg226.py <card stem>      (reads base/head from C:/g226/out/chain.jsonl; works in worktree C:/g226/ng)
Each variant: start from card head, edit, commit (detached), run check (sim) + G1 static V3 + IMPORT-ANY (+ W-2 foreign load).
Appends one JSON line per variant to C:/g226/out/neg.jsonl."""
import ast
import json
import os
import re
import subprocess
import sys
import time

CARD = sys.argv[1]
W = "C:/g226/ng_" + CARD
A = "skills/analog-gmid-design/assets/"
PY = "C:/Python314/python.exe"
K = "C:/g226/kit"
GC = "C:/g226/cache/tools/gates"
OUT = "C:/g226/out/neg.jsonl"
MP = ["--plan", "docs/01-plan/features/gain-budget-gmid-sizing.plan.md", "--registry",
      "docs/03-analysis/gain-budget-gmid-sizing.function-registry.md", "--split", "sizing_recipe.py", "stick_diagram.py",
      "topology_library.py", "design_report.py", "audit_current_forced.py", "--keep", "audit_current_forced.py",
      "--aliases", '{"optimizer": "theta_search.py"}']
ENV = dict(os.environ, TMP="C:/g226/tmp", TEMP="C:/g226/tmp", PYTHONIOENCODING="utf-8", MP_STMT_KEY="names",
           APPDATA="C:/Users/HSLEE/AppData/Roaming", HOME="C:/Users/HSLEE", MSYS_NO_PATHCONV="1")
rec = None
for l in open("C:/g226/out/chain.jsonl", encoding="utf-8"):
    r = json.loads(l)
    if r["card"] == CARD:
        rec = r
B, H = rec["base"], rec["head"]
MODF = A + CARD + ".py"
plan = json.load(open("C:/g226/out/%s/plan_base.json" % CARD, encoding="utf-8"))
COMPLETE = [f for f, v in (rec["gen"]["reexports"] or {}).items() if "complete shim" in v]
EXPORTING = list((rec["gen"]["reexports"] or {}).keys())


def git(*a):
    r = subprocess.run(["git", "-C", W, "-c", "user.name=m", "-c", "user.email=m@x"] + list(a), capture_output=True, text=True, encoding="utf-8")
    if r.returncode:
        raise SystemExit("git %s: %s" % (a, r.stderr))
    return r.stdout.strip()


def rd(rel):
    return open(os.path.join(W, rel), encoding="utf-8", newline="").read().replace("\r\n", "\n")


def wr(rel, t):
    open(os.path.join(W, rel), "w", encoding="utf-8", newline="").write(t)


def reexport_line_of(f):
    t = rd(A + f)
    for line in t.split("\n"):
        if line.startswith("from %s import " % CARD):
            return t, line
    return t, None


def v_edit_body():
    t = rd(MODF)
    tree = ast.parse(t)
    L = t.split("\n")
    for n in ast.walk(tree):
        if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef)):
            for c in ast.walk(n):
                if isinstance(c, ast.Constant) and type(c.value) is int and c.lineno == c.end_lineno and c.lineno > n.body[0].lineno:
                    line = L[c.lineno - 1]
                    seg = line[c.col_offset:c.end_col_offset]
                    if seg.isdigit():
                        L[c.lineno - 1] = line[:c.col_offset] + str(int(seg) + 1) + line[c.end_col_offset:]
                        wr(MODF, "\n".join(L))
                        return "%s:%d in %s" % (CARD, c.lineno, n.name)
    raise RuntimeError("no int constant")


def v_drop_reexport():
    f = EXPORTING[0]
    t, line = reexport_line_of(f)
    names = line.split(" import ", 1)[1].split("  #")[0].split(", ")
    if len(names) > 1:
        new = line.replace(names[0] + ", ", "", 1)
    else:
        new = ""
    wr(A + f, t.replace(line + "\n", (new + "\n") if new else "", 1))
    return "%s drop %s" % (f, names[0])


def mod_head_end(t):
    tree = ast.parse(t)
    end = 0
    for i, n in enumerate(tree.body):
        if i == 0 and isinstance(n, ast.Expr) and isinstance(n.value, ast.Constant) and isinstance(n.value.value, str):
            end = n.end_lineno
            continue
        if isinstance(n, (ast.Import, ast.ImportFrom)):
            end = n.end_lineno
            continue
        break
    return end


def insert_after_head(t, new):
    L = t.split("\n")
    e = mod_head_end(t)
    L.insert(e, new)
    return "\n".join(L)


def v_import_shim():
    wr(MODF, insert_after_head(rd(MODF), "import sizing_recipe"))
    return "import sizing_recipe"


def v_dup_import():
    t = rd(MODF)
    tree = ast.parse(t)
    for n in tree.body:
        if isinstance(n, (ast.Import, ast.ImportFrom)) and not (isinstance(n, ast.ImportFrom) and n.module == "__future__"):
            line = t.split("\n")[n.lineno - 1]
            if n.lineno == n.end_lineno:
                wr(MODF, t.replace(line + "\n", line + "\n" + line + "\n", 1))
                return line
    raise RuntimeError("no import")


def v_no_future():
    t = rd(MODF)
    t2 = t.replace("from __future__ import annotations\n", "", 1)
    assert t2 != t
    wr(MODF, t2)
    return "-future"


def v_extra_unit():
    # a top-level function still in a split file, assigned to a different MOD (not A-K, no decorator)
    pref = {"sizing_recipe.py": 0, "stick_diagram.py": 1, "topology_library.py": 2}   # same-__future__ split files first (v2)
    for uid, v in sorted(plan["assignment"].items(), key=lambda kv: (pref.get(kv[0].split("::", 1)[0], 9), kv[0])):
        f, key = uid.split("::", 1)
        if v["mod"] in (CARD + ".py", f) or v["rule"] == "A-K" or f not in pref:
            continue
        if not os.path.exists(os.path.join(W, A + f)):
            continue
        t = rd(A + f)
        tree = ast.parse(t)
        for n in tree.body:
            if isinstance(n, ast.FunctionDef) and n.name == key and not n.decorator_list:
                L = t.split("\n")
                seg = L[n.lineno - 1:n.end_lineno]
                rest = L[:n.lineno - 1] + L[n.end_lineno:]
                rest = "\n".join(rest)
                rest = insert_after_head(rest, "from %s import %s" % (CARD, key)) if f != "stick_diagram.py" else rest + "\nfrom %s import %s\n" % (CARD, key)
                wr(A + f, rest)
                wr(MODF, rd(MODF).rstrip("\n") + "\n\n\n" + "\n".join(seg) + "\n")
                return "%s (%s -> %s)" % (uid, v["rule"], v["mod"])
    raise RuntimeError("no candidate")


def v_docstring():
    wr(MODF, '"""MOD file docstring."""\n' + rd(MODF))
    return "docstring"


def v_w2_acf():
    f = "audit_current_forced.py"
    t, line = reexport_line_of(f)
    t2 = t.replace(line + "\n", "", 1)
    t2 = t2.replace("sys.path.insert(", line + "\nsys.path.insert(", 1)
    wr(A + f, t2)
    return "ACF re-export before sys.path.insert"


def v_shim_logic():
    f = COMPLETE[0]
    wr(A + f, rd(A + f).rstrip("\n") + "\n_SHIM_FLAG = 1\n")
    return "%s + _SHIM_FLAG = 1" % f


def v_sd_head():
    t = rd(MODF)
    L = t.split("\n")
    tail = [l for l in L if re.match(r"from (stick_diagram|sizing_layout_convergence|instance_report_builder) import ", l)]
    tail = [l for l in tail if not l.startswith("from %s " % CARD)]
    body = [l for l in L if l not in tail]
    t2 = insert_after_head("\n".join(body), "\n".join(tail))
    wr(MODF, t2)
    return "tail imports to head: %d" % len(tail)


def v_cache_only():
    t = rd(MODF)
    tree = ast.parse(t)
    L = t.split("\n")
    for n in tree.body:
        if isinstance(n, ast.AnnAssign) and isinstance(n.target, ast.Name) and "CACHE" in n.target.id.upper():
            name = n.target.id
            stmt = L[n.lineno - 1:n.end_lineno]
            wr(MODF, "\n".join(L[:n.lineno - 1] + L[n.end_lineno:]))
            f = "sizing_recipe.py"
            st, line = reexport_line_of(f)
            if line is None:
                raise RuntimeError("no reexport in SR")
            new = line.replace(name + ", ", "").replace(", " + name, "")
            wr(A + f, st.replace(line + "\n", new + "\n" + "\n".join(stmt) + "\n", 1))
            return "%s stays in SR, user moved" % name
    raise RuntimeError("no cache")


VAR = [("R-1 edit-body", v_edit_body), ("R-2 drop-reexport", v_drop_reexport), ("R-3 import-shim", v_import_shim),
       ("R-4 dup-import", v_dup_import), ("R-5 no-future", v_no_future), ("R-6 extra-unit", v_extra_unit), ("R-7 docstring", v_docstring)]
if "audit_current_forced.py" in EXPORTING:
    VAR.append(("R-W2 acf-before-path", v_w2_acf))
if COMPLETE:
    VAR.append(("R-SHIM complete-shim-logic", v_shim_logic))
if CARD in ("sizing_layout_convergence", "instance_report_builder"):
    VAR.append(("R-D22 tail-imports-to-head", v_sd_head))
if CARD in ("gmid_sizing_engine", "sizing_layout_convergence"):
    VAR.append(("R-CACHE cache-split", v_cache_only))
only = sys.argv[2].split(",") if len(sys.argv) > 2 else None
for name, fn in VAR:
    if only and name.split()[0] not in only:
        continue
    git("checkout", "-q", "--detach", H)
    git("checkout", "-q", "--", ".")
    t0 = time.time()
    try:
        what = fn()
    except Exception as e:
        open(OUT, "a", encoding="utf-8").write(json.dumps({"card": CARD, "variant": name, "ERROR": repr(e)}) + "\n")
        print(name, "ERROR", e, flush=True)
        continue
    git("add", "-A", "skills")
    git("commit", "-q", "-m", "neg %s %s (measure only)" % (CARD, name))
    h = git("rev-parse", "HEAD")
    r = subprocess.run([PY, "-B", K + "/move_plan_sim.py", "check", "--root", W, "--base", B, "--head", h, "--card", CARD + ".py"] + MP,
                       capture_output=True, text=True, encoding="utf-8", env=ENV)
    try:
        ck = json.loads([x for x in r.stdout.splitlines() if x.startswith("{")][0])
        fsum = {k: len(v) for k, v in ck["findings"].items() if v}
    except Exception as e:
        fsum = {"ERROR": str(e) + r.stderr[-300:]}
    st = subprocess.run([PY, "-B", "-c", (
        "import sys,json;sys.path.insert(0,%r);import reachability as rch, mutate_changed as mc;"
        "b={k:v for k,v in rch.read_tree(%r,%r,rch.GRAPH_PREFIXES).items() if rch._is_source(k)};"
        "h={k:v for k,v in rch.read_tree(%r,%r,rch.GRAPH_PREFIXES).items() if rch._is_source(k)};"
        "mv=rch.moved_defs(b,h);d=[];m=0\n"
        "for p,s in h.items():\n"
        " if b.get(p)==s: continue\n"
        " for q,f in mc.changed_defs(b.get(p),s):\n"
        "  if rch.g1_excluded(mv,p,q,f): continue\n"
        "  d.append(p.split('/')[-1]+'::'+q); m+=sum(1 for _ in mc.mutants(f,s))\n"
        "print(json.dumps({'n_defs':len(d),'mutants':m,'n_rejected':len(mv['rejected'])}))"
    ) % (GC, W, B, W, h)], capture_output=True, text=True, encoding="utf-8", env=ENV)
    try:
        v3 = json.loads(st.stdout.splitlines()[-1])
    except Exception:
        v3 = {"ERROR": st.stderr[-300:]}
    ia = subprocess.run(["bash", "-c", 'PY="C:/Python314/python.exe -B"; GC=%s; source %s/mpargs.sh; source %s/import_any_fn.sh; import_any %s; echo "rc=$?"'
                         % (GC, K, K, W)], capture_output=True, text=True, encoding="utf-8", env=ENV)
    w2 = None
    if "audit_current_forced.py" in EXPORTING:
        code = ("import importlib.util;p=%r;s=importlib.util.spec_from_file_location('acf_probe',p);m=importlib.util.module_from_spec(s);"
                "s.loader.exec_module(m);print('ok')" % (W + "/" + A + "audit_current_forced.py"))
        p = subprocess.run([PY, "-B", "-c", code], cwd="C:/g226/tmp", capture_output=True, text=True, encoding="utf-8", env=ENV)
        w2 = "ok" if p.returncode == 0 else (p.stderr.strip().splitlines() or ["?"])[-1][:160]
    out = {"card": CARD, "variant": name, "what": what, "head": h, "check_exit": r.returncode, "check_findings": fsum, "v3_static_g1": v3,
           "import_any": [x for x in ia.stdout.splitlines() if x.startswith("IMPORT-ANY") or x.startswith("rc=")], "w2_foreign_load": w2,
           "sec": round(time.time() - t0, 1)}
    open(OUT, "a", encoding="utf-8").write(json.dumps(out, ensure_ascii=False) + "\n")
    print(json.dumps(out, ensure_ascii=False), flush=True)
git("checkout", "-q", "--detach", H)
git("checkout", "-q", "--", ".")
