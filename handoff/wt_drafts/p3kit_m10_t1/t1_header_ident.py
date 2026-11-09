"""measure only: for every name bound by >=2 different header statements in a generated T1 file, exec each statement
in isolation (after the file's sys.path set-up statements) and check the bound objects are identical (`is`).
    python -B -P t1_header_ident.py <root> <unit dir rel>"""
import ast
import os
import sys

root, rel = sys.argv[1:3]
U = os.path.join(root, rel)
A = os.path.abspath(os.path.join(U, "..", ".."))
sys.path.insert(0, A)
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(A))), "workspaces"))
sys.path.insert(0, os.path.join(A, "tests", "tools"))
sys.path.insert(0, U)
out = {}
for f in sorted(os.listdir(U)):
    if not (f.startswith("test_mod") or f == "_selftest_shared.py"):
        continue
    t = ast.parse(open(os.path.join(U, f), encoding="utf-8").read())
    binds = {}
    for n in t.body:
        if isinstance(n, (ast.Import, ast.ImportFrom)):
            for a in n.names:
                binds.setdefault(a.asname or a.name.split(".")[0], []).append(n)
    for nm, ns in binds.items():
        if len(ns) < 2:
            continue
        objs = []
        for n in ns:
            g = {"__file__": os.path.join(U, f)}
            exec(compile(ast.Module(body=[n], type_ignores=[]), f, "exec"), g)
            objs.append(g[nm])
        same = all(o is objs[0] for o in objs)
        out.setdefault(f, {})[nm] = same
bad = {f: [k for k, v in d.items() if not v] for f, d in out.items()}
print({f: len(d) for f, d in out.items()}, "NOT-IDENTICAL:", {f: v for f, v in bad.items() if v})
