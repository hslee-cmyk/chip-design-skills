import ast, sys
OUT = open("C:/g204/out_tests.txt", "w", encoding="utf-8")
def pr(*a):
    s = " ".join(str(x) for x in a); print(s); OUT.write(s + "\n")
U = "C:/g204/base/skills/analog-gmid-design/assets/tests/"
ALL = ["estimate_area_budget","solve_diode_stack_current","derived_bounds_path","load_derived_bounds","check_multi_leaf_hub_parity","MultiLeafHubParityVerdict"]
import glob, os
for p in sorted(glob.glob(U + "**/*.py", recursive=True)):
    src = open(p, encoding="utf-8").read()
    try: t = ast.parse(src)
    except SyntaxError: continue
    rel = os.path.relpath(p, U).replace("\\", "/")
    for n in ast.walk(t):
        if isinstance(n, ast.ImportFrom):
            hit = [a.name for a in n.names if a.name in ALL]
            if hit: pr(rel, "import", n.lineno, hit)
    for n in t.body:
        if isinstance(n, (ast.FunctionDef, ast.ClassDef)):
            used = {x.id for x in ast.walk(n) if isinstance(x, ast.Name)} | {x.attr for x in ast.walk(n) if isinstance(x, ast.Attribute)}
            hit = [k for k in ALL if k in used]
            if hit:
                pr(rel, n.name, "%d-%d" % (n.lineno, n.end_lineno), hit, [ast.unparse(d) for d in n.decorator_list])
