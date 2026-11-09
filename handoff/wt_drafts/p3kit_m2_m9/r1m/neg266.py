"""measure only (NOT a role artifact): review r1m probes for M-card drafts.
    python -B neg266.py <card stem> <variant>[,<variant>...] <scratch root> [<worktree>]
variants:
  HEAD      the normal merged head (no edit) -- contract 3 readings only
  COMOVE    a pure top-level function (no module-global loads, no decorator) assigned to another MOD is moved along
            (plan copy edited: its mod -> this card; regenerated from base with gen226)          [S-1]
  USERBACK  cache moves to the MOD as planned, its using function stays in its split file
            (plan copy edited: user's mod -> its own file; regenerated from base)                 [S-2]
  SHIMC     complete shim: delete the base `from stick_diagram import ...` re-export statement    [S-4]
  D22       MOD tail imports moved to the head (neg226 v_sd_head)                                 [S-3]
One JSON line per variant appended to <scratch>/out/neg266.jsonl."""
import ast
import builtins
import json
import os
import re
import subprocess
import sys
import time

CARD = sys.argv[1]
VARS = sys.argv[2].split(",")
SCR = sys.argv[3].rstrip("/")
W = sys.argv[4] if len(sys.argv) > 4 else SCR + "/ng_" + CARD
A = "skills/analog-gmid-design/assets/"
PY = "C:/Python314/python.exe"
K = SCR + "/kit"
GC = SCR + "/cache/tools/gates"
OUT = SCR + "/out/neg266.jsonl"
MP = ["--plan", "docs/01-plan/features/gain-budget-gmid-sizing.plan.md", "--registry",
      "docs/03-analysis/gain-budget-gmid-sizing.function-registry.md", "--split", "sizing_recipe.py", "stick_diagram.py",
      "topology_library.py", "design_report.py", "audit_current_forced.py", "--keep", "audit_current_forced.py",
      "--aliases", '{"optimizer": "theta_search.py"}']
ENV = dict(os.environ, TMP=SCR + "/tmp", TEMP=SCR + "/tmp", PYTHONIOENCODING="utf-8", MP_STMT_KEY="names",
           APPDATA="C:/Users/HSLEE/AppData/Roaming", HOME="C:/Users/HSLEE", MSYS_NO_PATHCONV="1")
rec = None
for l in open(SCR + "/out/chain.jsonl", encoding="utf-8"):
    r = json.loads(l)
    if r["card"] == CARD:
        rec = r
B, H = rec["base"], rec["head"]
MODF = A + CARD + ".py"
PJ = SCR + "/out/%s/plan_base.json" % CARD
plan = json.load(open(PJ, encoding="utf-8"))
EXPORTING = list((rec["gen"]["reexports"] or {}).keys())
COMPLETE = [f for f, v in (rec["gen"]["reexports"] or {}).items() if "complete shim" in v]
BUILTIN = set(dir(builtins))


def git(*a):
    r = subprocess.run(["git", "-C", W, "-c", "user.name=m", "-c", "user.email=m@x"] + list(a), capture_output=True, text=True, encoding="utf-8")
    if r.returncode:
        raise SystemExit("git %s: %s" % (a, r.stderr))
    return r.stdout.strip()


def rd(rel):
    return open(os.path.join(W, rel), encoding="utf-8", newline="").read().replace("\r\n", "\n")


def wr(rel, t):
    open(os.path.join(W, rel), "w", encoding="utf-8", newline="").write(t)


def free_globals(fn):
    bound, loads = set(), set()
    for n in ast.walk(fn):
        if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef, ast.Lambda)):
            a = n.args
            for x in a.posonlyargs + a.args + a.kwonlyargs + ([a.vararg] if a.vararg else []) + ([a.kwarg] if a.kwarg else []):
                bound.add(x.arg)
            if not isinstance(n, ast.Lambda) and n is not fn:
                bound.add(n.name)
        elif isinstance(n, ast.ClassDef):
            bound.add(n.name)
        elif isinstance(n, ast.Name):
            (bound if isinstance(n.ctx, (ast.Store, ast.Del)) else loads).add(n.id)
        elif isinstance(n, (ast.Import, ast.ImportFrom)):
            for al in n.names:
                bound.add((al.asname or al.name).split(".")[0])
        elif isinstance(n, ast.ExceptHandler) and n.name:
            bound.add(n.name)
    return sorted(loads - bound - BUILTIN)


def regen(edit_uid, new_mod):
    p2 = json.loads(json.dumps(plan))
    p2["assignment"][edit_uid]["mod"] = new_mod
    pj2 = SCR + "/out/%s/plan_edit_%s.json" % (CARD, re.sub(r"\W", "_", edit_uid))
    json.dump(p2, open(pj2, "w", encoding="utf-8"), ensure_ascii=False)
    git("checkout", "-q", "--detach", B)
    git("checkout", "-q", "--", ".")
    g = subprocess.run([PY, "-B", K + "/gen226.py", W, pj2, CARD + ".py"], capture_output=True, text=True, encoding="utf-8", env=ENV)
    if g.returncode:
        raise RuntimeError("gen: " + g.stderr[-300:])


def v_comove(want=None):
    pref = {"sizing_recipe.py": 0, "stick_diagram.py": 1, "topology_library.py": 2}
    cands = []
    for uid, v in plan["assignment"].items():
        f, key = uid.split("::", 1)
        if v["mod"] in (CARD + ".py", f) or v["rule"] == "A-K" or f not in pref:
            continue
        if not os.path.exists(os.path.join(W, A + f)):
            continue
        for n in ast.parse(rd(A + f)).body:
            if isinstance(n, ast.FunctionDef) and n.name == key and not n.decorator_list and not free_globals(n):
                cands.append((pref[f], n.lineno, uid, v))
    if not cands:
        raise RuntimeError("no candidate")
    cands.sort()
    if want:
        cands = [c for c in cands if c[2].split("::")[1] == want] or [(0, 0, "NONE::" + want, {})]
        if cands[0][2].startswith("NONE::"):
            raise RuntimeError("wanted %s is not a pure candidate" % want)
    _, _, uid, v = cands[0]
    regen(uid, CARD + ".py")
    return "%s (%s -> %s) moved along; pure candidates %s" % (uid, v["rule"], v["mod"], [c[2].split("::")[1] for c in cands][:6])


def v_userback(want=None):
    caches = [u for u, v in plan["assignment"].items() if v["mod"] == CARD + ".py" and "CACHE" in u.split("::")[1].upper()
              and not u.startswith(CARD + ".py::") and (want is None or u.split("::")[1] == want)]
    for cu in sorted(caches):
        f, cname = cu.split("::", 1)
        tree = ast.parse(git("show", "%s:%s" % (B, A + f)))
        users = []
        for n in tree.body:
            if isinstance(n, ast.FunctionDef) and any(isinstance(x, ast.Name) and x.id == cname for x in ast.walk(n)):
                uid = "%s::%s" % (f, n.name)
                if plan["assignment"].get(uid, {}).get("mod") == CARD + ".py":
                    users.append((n.lineno, uid))
        if users:
            users.sort()
            uid = users[0][1]
            regen(uid, f)
            return "%s moved to MOD, user %s stays in %s" % (cname, uid.split("::")[1], f)
    raise RuntimeError("no cache user")


def v_shimc():
    f = COMPLETE[0]
    t = rd(A + f)
    tree = ast.parse(t)
    L = t.split("\n")
    for n in tree.body:
        if isinstance(n, ast.ImportFrom) and n.module == "stick_diagram":
            wr(A + f, "\n".join(L[:n.lineno - 1] + L[n.end_lineno:]))
            return "%s: delete `from stick_diagram import ...` (lines %d-%d, %d names)" % (f, n.lineno, n.end_lineno, len(n.names))
    raise RuntimeError("no SD re-export in complete shim")


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


def v_d22():
    t = rd(MODF)
    L = t.split("\n")
    tail = [l for l in L if re.match(r"from (stick_diagram|sizing_layout_convergence|instance_report_builder) import ", l)]
    tail = [l for l in tail if not l.startswith("from %s " % CARD)]
    body = [l for l in L if l not in tail]
    t2 = "\n".join(body)
    L2 = t2.split("\n")
    L2.insert(mod_head_end(t2), "\n".join(tail))
    wr(MODF, "\n".join(L2))
    return "tail imports to head: %d" % len(tail)


FN = {"COMOVE": v_comove, "USERBACK": v_userback, "SHIMC": v_shimc, "D22": v_d22, "HEAD": None}
for name in VARS:
    t0 = time.time()
    git("checkout", "-q", "--detach", H)
    git("checkout", "-q", "--", ".")
    what = "normal merged head"
    arg = None
    if "=" in name:
        name, arg = name.split("=", 1)
    if FN[name]:
        try:
            what = FN[name](arg) if arg else FN[name]()
        except Exception as e:
            open(OUT, "a", encoding="utf-8").write(json.dumps({"card": CARD, "variant": name, "ERROR": repr(e)}) + "\n")
            print(name, "ERROR", e, flush=True)
            continue
        git("add", "-A", "skills")
        git("commit", "-q", "-m", "neg266 %s %s (measure only)" % (CARD, name))
    h = git("rev-parse", "HEAD")
    if name != "HEAD":
        r = subprocess.run([PY, "-B", K + "/move_plan_sim.py", "check", "--root", W, "--base", B, "--head", h, "--card", CARD + ".py"] + MP,
                           capture_output=True, text=True, encoding="utf-8", env=ENV)
        try:
            ck = json.loads([x for x in r.stdout.splitlines() if x.startswith("{")][0])
            fsum = {k: len(v) for k, v in ck["findings"].items() if v}
            fsample = {k: v[:2] for k, v in ck["findings"].items() if v}
        except Exception as e:
            fsum, fsample = {"ERROR": str(e) + r.stderr[-300:]}, {}
        cexit = r.returncode
    else:
        cexit, fsum, fsample = None, None, None
    c3 = subprocess.run([PY, "-B", K + "/c3.py", W, B, h, CARD, PJ, GC], capture_output=True, text=True, encoding="utf-8", env=ENV)
    try:
        c3j = json.loads(c3.stdout.strip().splitlines()[-1])
    except Exception:
        c3j = {"ERROR": c3.stderr[-400:]}
    ia = subprocess.run(["bash", "-c", 'PY="C:/Python314/python.exe -B"; GC=%s; source %s/mpargs.sh; source %s/import_any_fn.sh; import_any %s; echo "rc=$?"'
                         % (GC, K, K, W)], capture_output=True, text=True, encoding="utf-8", env=ENV)
    w2 = None
    if "audit_current_forced.py" in EXPORTING:
        code = ("import importlib.util;p=%r;s=importlib.util.spec_from_file_location('acf_probe',p);m=importlib.util.module_from_spec(s);"
                "s.loader.exec_module(m);print('ok')" % (W + "/" + A + "audit_current_forced.py"))
        p = subprocess.run([PY, "-B", "-c", code], cwd=SCR + "/tmp", capture_output=True, text=True, encoding="utf-8", env=ENV)
        w2 = "ok" if p.returncode == 0 else (p.stderr.strip().splitlines() or ["?"])[-1][:160]
    out = {"card": CARD, "variant": name, "what": what, "head": h, "check_exit": cexit, "check_findings": fsum, "check_sample": fsample,
           "c3": c3j, "import_any": [x for x in ia.stdout.splitlines() if x.startswith("IMPORT-ANY") or x.startswith("rc=")],
           "w2_foreign_load": w2, "sec": round(time.time() - t0, 1)}
    open(OUT, "a", encoding="utf-8").write(json.dumps(out, ensure_ascii=False) + "\n")
    print(json.dumps(out, ensure_ascii=False), flush=True)
git("checkout", "-q", "--detach", H)
git("checkout", "-q", "--", ".")
