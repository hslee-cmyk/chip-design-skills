"""measure only (W-1): which tracked .py files read, through a future complete shim (TL, SR, DR), a name that the shim
module binds only by an import statement (stdlib/3rd-party or another split file) -- SHIM (b) leaves only docstring,
re-export lines (names moved FROM that file) and __future__, so such names vanish at the card that makes the file a
complete shim. Reads git tree at <rev> of clone <root>. Output JSON (argv[3]) + summary to stdout.
    python -B shim_import_reads.py <root> <rev> <out.json>"""
import ast
import json
import subprocess
import sys

ROOT, REV, OUT = sys.argv[1:4]
A = "skills/analog-gmid-design/assets/"
SHIMS = {"topology_library": "M4", "sizing_recipe": "M8", "design_report": "M9"}


def git(*a):
    return subprocess.run(["git", "-C", ROOT] + list(a), capture_output=True, check=True).stdout.decode("utf-8")


files = [f for f in git("ls-tree", "-r", "--name-only", REV).splitlines() if f.endswith(".py")]


def src(f):
    return git("show", "%s:%s" % (REV, f))


# import-only bindings per shim module (top level, incl. inside top-level try/if)
import_bound = {}
for m in SHIMS:
    t = ast.parse(src(A + m + ".py"))
    defs, imps = set(), {}
    for n in ast.walk(t):
        pass
    for n in t.body:
        stack = [n]
        while stack:
            x = stack.pop()
            if isinstance(x, (ast.Import, ast.ImportFrom)):
                for al in x.names:
                    nm = (al.asname or al.name).split(".")[0]
                    imps[nm] = ("from %s" % x.module) if isinstance(x, ast.ImportFrom) else "import"
            elif isinstance(x, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
                defs.add(x.name)
            elif isinstance(x, (ast.Assign, ast.AnnAssign, ast.AugAssign)):
                for tg in (x.targets if isinstance(x, ast.Assign) else [x.target]):
                    for nn in ast.walk(tg):
                        if isinstance(nn, ast.Name):
                            defs.add(nn.id)
            elif isinstance(x, (ast.If, ast.Try)):
                stack.extend(getattr(x, "body", []) + getattr(x, "orelse", []) + getattr(x, "finalbody", []))
                for h in getattr(x, "handlers", []):
                    stack.extend(h.body)
    import_bound[m] = {k: v for k, v in imps.items() if k not in defs}

hits = []
for f in files:
    try:
        t = ast.parse(src(f))
    except SyntaxError:
        continue
    aliases = {}
    for n in ast.walk(t):
        if isinstance(n, ast.ImportFrom) and n.module in SHIMS and n.level == 0:
            for al in n.names:
                if al.name in import_bound[n.module]:
                    hits.append({"file": f, "line": n.lineno, "module": n.module, "name": al.name,
                                 "bound_by": import_bound[n.module][al.name], "card": SHIMS[n.module], "how": "from-import"})
        elif isinstance(n, ast.Import):
            for al in n.names:
                if al.name in SHIMS:
                    aliases[al.asname or al.name] = al.name
    if aliases:
        for n in ast.walk(t):
            if isinstance(n, ast.Attribute) and isinstance(n.value, ast.Name) and n.value.id in aliases:
                m = aliases[n.value.id]
                if n.attr in import_bound[m]:
                    hits.append({"file": f, "line": n.lineno, "module": m, "name": n.attr,
                                 "bound_by": import_bound[m][n.attr], "card": SHIMS[m], "how": "attribute"})
json.dump({"rev": REV, "import_bound_counts": {m: len(v) for m, v in import_bound.items()}, "hits": hits},
          open(OUT, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
by = {}
for h in hits:
    by.setdefault((h["card"], h["module"], h["file"]), []).append("%s(%d,%s)" % (h["name"], h["line"], h["bound_by"]))
for k in sorted(by):
    print(k[0], k[1], k[2], sorted(set(by[k])))
print("hits", len(hits), "files", len({h["file"] for h in hits}))
