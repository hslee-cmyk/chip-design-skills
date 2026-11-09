"""scratch (C:/g200): M-card move generator prototype -- measure only, NOT a role artifact.

    python -B gen_move.py <root (worktree checked out at base)> <plan.json computed at base> <card MOD file> [--report out.json]

Writes into the worktree (caller commits):
  * <card MOD file> = docstring + plan.mod_imports[card] (D-30; for MOD number >= 8 the import lines whose module is an
    N3.10 file with number >= 7 go to the file end -- design 30 D-22 (2)) + the assigned units' source bytes
    (decorator line .. end_lineno), in (source-file init order, original line) order.
  * every split file that loses units: unit lines removed; one re-export line per destination MOD
    `from <MOD stem> import <bound names sorted>` inserted right after the file's import head
    (D-22: stick_diagram's re-exports of MOD 8/9 at the file end).
Does not touch anything else. The gates (reachability = G1 proto) are imported from <root>/tools/gates.
"""
import ast
import json
import os
import sys

ROOT, PLAN, CARD = sys.argv[1:4]
REPORT = sys.argv[sys.argv.index("--report") + 1] if "--report" in sys.argv else None
A = "skills/analog-gmid-design/assets/"
sys.path.insert(0, os.path.join(ROOT, "tools", "gates"))
import import_layering as il  # noqa: E402
import reachability as rch    # noqa: E402

plan = json.load(open(PLAN, encoding="utf-8"))
modtab = il.mod_table(open(os.path.join(ROOT, "docs/01-plan/features/gain-budget-gmid-sizing.plan.md"), encoding="utf-8").read())
n310 = {s + ".py": k for s, k in modtab.items()}
k_card = n310[CARD]
KEEP = [x for x in sys.argv[sys.argv.index("--keep") + 1].split(",")] if "--keep" in sys.argv else ["audit_current_forced.py"]
INIT_ORDER = ["topology_library.py", "stick_diagram.py", "sizing_recipe.py", "design_report.py", "audit_current_forced.py"]


def rd(rel):
    with open(os.path.join(ROOT, rel), encoding="utf-8", newline="") as fh:
        return fh.read().replace("\r\n", "\n")


def wr(rel, text):
    with open(os.path.join(ROOT, rel), "w", encoding="utf-8", newline="") as fh:
        fh.write(text)


files = rch.read_tree(ROOT, "HEAD", rch.SOURCE_GLOBS)
idx = rch.SourceIndex({k: v for k, v in files.items() if rch._is_source(k)})
units = []          # (src file, key, node, bound)
for uid, a in plan["assignment"].items():
    if a["mod"] != CARD:
        continue
    f, key = uid.split("::", 1)
    key = key.split("#")[0]
    if f == CARD:
        continue
    m = idx.mod(A + f)
    hit = [(n, b) for (k, q, h, n, b) in m.units if (q if q else "<stmt:%s>" % h[:12]) == key
           or (k == "stmt" and ",".join(sorted(b)) == key)]
    if len(hit) != 1:
        sys.exit("unit not found uniquely: %s (%d)" % (uid, len(hit)))
    units.append((f, key, hit[0][0], hit[0][1]))
units.sort(key=lambda u: (INIT_ORDER.index(u[0]) if u[0] in INIT_ORDER else 99, (u[2].decorator_list[0].lineno if getattr(u[2], "decorator_list", None) else u[2].lineno)))


def span(n):
    a = n.decorator_list[0].lineno if getattr(n, "decorator_list", None) else n.lineno
    return a, n.end_lineno


src_lines = {f: rd(A + f).split("\n") for f in {u[0] for u in units}}
# ---- MOD file
head, tail = [], []
for line in plan["mod_imports"].get(CARD, []):
    mod = line.split()[1].split(".")[0]
    if k_card >= 8 and (mod + ".py") in n310 and n310[mod + ".py"] >= 7 and not line.startswith("from __future__"):
        tail.append(line)
    else:
        head.append(line)
out = list(head)   # no module docstring (M1-1 / W-3 default (ga))
for f, key, n, b in units:
    a, e = span(n)
    out.append("")
    out.append("")
    out += src_lines[f][a - 1:e]
if tail:
    out.append("")
    out.append("")
    out += tail
wr(A + CARD, "\n".join(out) + "\n")

# ---- split files
per_file = {}
for f, key, n, b in units:
    per_file.setdefault(f, []).append((n, b))
reexports = {}
for f, lst in per_file.items():
    text = rd(A + f)
    L = text.split("\n")
    tree = ast.parse(text)
    drop = set()
    names = set()
    for n, b in lst:
        a, e = span(n)
        drop |= set(range(a, e + 1))
        names |= set(b)
    # import head end: last top-level import before the first non-import, non-docstring statement
    # W-2: head block = consecutive import / from-import / sys.path.* expression statements after the docstring;
    # re-export goes right after the LAST import statement of that block (ACF: after `from stick_diagram import load_topology`)
    head_end = 0
    path_seen = False
    for i, n in enumerate(tree.body):
        if i == 0 and isinstance(n, ast.Expr) and isinstance(n.value, ast.Constant) and isinstance(n.value.value, str):
            continue
        if isinstance(n, (ast.Import, ast.ImportFrom)):
            head_end = n.end_lineno
            continue
        if (isinstance(n, ast.Expr) and isinstance(n.value, ast.Call) and isinstance(n.value.func, ast.Attribute)
                and ast.unparse(n.value.func).startswith("sys.path.")):
            path_seen = True
            continue
        break
    line = "from %s import %s" % (CARD[:-3], ", ".join(sorted(names)))
    if path_seen:
        line += "  # noqa: E402"
    reexports[f] = line
    at_end = (f in n310 and n310[f] == 7 and k_card > 7)
    gone_keys = {(n.lineno) for n, b in lst}
    remaining = [n for n in tree.body if not isinstance(n, (ast.Import, ast.ImportFrom)) and n.lineno not in gone_keys
                 and not (n is tree.body[0] and isinstance(n, ast.Expr))]
    if f not in n310 and f not in KEEP and not remaining:
        # complete shim (SHIM (b)): docstring + __future__ + all MOD re-export lines (existing ones kept) + the new one
        doc = L[:tree.body[0].end_lineno] if (tree.body and isinstance(tree.body[0], ast.Expr)) else []
        fut = [ast.unparse(n) for n in tree.body if isinstance(n, ast.ImportFrom) and n.module == "__future__"]
        old_re = [ast.unparse(n) for n in tree.body if isinstance(n, ast.ImportFrom) and n.level == 0 and n.module
                  and (n.module + ".py") in n310]
        NL = chr(10)
        wr(A + f, NL.join(doc + fut + old_re + [line]) + NL)
        reexports[f] = line + "  (complete shim)"
        continue
    newL = []
    for i, l in enumerate(L, 1):
        if i in drop:
            continue
        newL.append(l)
        if i == head_end and not at_end:
            newL.append(line)
    if at_end:
        while newL and newL[-1] == "":
            newL.pop()
        newL += ["", line, ""]
    wr(A + f, "\n".join(newL))
rep = {"card": CARD, "units": ["%s::%s" % (u[0], u[1]) for u in units], "mod_imports_head": head, "mod_imports_tail": tail,
       "reexports": reexports,
       "spans": ["%s:%d-%d %s" % (u[0], span(u[2])[0], span(u[2])[1], type(u[2]).__name__) for u in units],
       "n_defs_in_units": sum(sum(1 for x in ast.walk(u[2]) if isinstance(x, (ast.FunctionDef, ast.AsyncFunctionDef))) for u in units)}
if REPORT:
    json.dump(rep, open(REPORT, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
print(json.dumps(rep, ensure_ascii=False))
