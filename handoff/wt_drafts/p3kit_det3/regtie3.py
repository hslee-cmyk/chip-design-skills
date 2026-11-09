"""scratch: registry rows per name at a rev -- (e5)/(e6) counts. usage: python regtie3.py <repo> <rev> <gates dir> <move_plan_sim.py>"""
import importlib.util, json, re, subprocess, sys
repo, rev, gates, sim = sys.argv[1:5]
sys.path.insert(0, gates)
import import_layering as il
spec = importlib.util.spec_from_file_location("mps", sim); mps = importlib.util.module_from_spec(spec); spec.loader.exec_module(mps)
show = lambda p: subprocess.run(["git", "-C", repo, "show", "%s:%s" % (rev, p)], capture_output=True, check=True).stdout.decode("utf-8")
plan = show("docs/01-plan/features/gain-budget-gmid-sizing.plan.md")
reg = show("docs/03-analysis/gain-budget-gmid-sizing.function-registry.md")
n310 = {s: k for s, k in il.mod_table(plan).items()}
alias = {"optimizer": n310["theta_search"]}
IDENT = re.compile(r"[A-Za-z_][A-Za-z0-9_]*")
def cm(cell):
    out = set()
    for t in IDENT.findall(cell):
        if t in n310: out.add(n310[t])
        elif t.endswith(".py") and t[:-3] in n310: out.add(n310[t[:-3]])
        elif t in alias: out.add(alias[t])
    # also '<stem>.py' tokens: IDENT splits 'x.py' into 'x','py' -> stem match above
    return out
rows = mps.registry_rows(reg)
by = {}
for fc, dc in rows:
    toks = re.findall(r"`([^`]*)`", fc)
    if not toks: continue
    name = toks[0].strip().split(".")[0]
    if not IDENT.fullmatch(name): continue
    by.setdefault(name, []).append(cm(dc))
multi = {n: [sorted(m) for m in ms] for n, ms in by.items() if len(ms) > 1}
e5 = [n for n, ms in by.items() if len({min(m) for m in ms if len(m) == 1}) > 1]
a3multi = [n for n, ms in by.items() if sum(len(m) >= 2 for m in ms) > 1]
e6 = [n for n, ms in by.items() if len({min(m) for m in ms if len(m) >= 2}) > 1]
a3rows = sum(len(m) >= 2 for ms in by.values() for m in ms)
print(json.dumps({"rev": rev, "rows": len(rows), "names": len(by), "names_multi_row": {n: (len(v), sorted({tuple(x) for x in map(tuple, v)})) for n, v in multi.items()},
                  "e5_names": e5, "a3_rows": a3rows, "a3_multi_row_names": a3multi, "e6_names": e6}, ensure_ascii=False))
