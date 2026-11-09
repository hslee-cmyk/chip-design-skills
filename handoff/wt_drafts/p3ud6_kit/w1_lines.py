"""measure only: W-1 -- in the three unit selftests at <rev>, list the shim-routed import line, the 7 names it binds that are not engine
definitions, any other module-level binding of those names, and their use count (AST).
    python -B w1_lines.py <repo> <rev> <out.json>"""
import ast
import collections
import json
import subprocess
import sys

REPO, REV, OUT = sys.argv[1:4]
U = "skills/analog-gmid-design/assets/tests/unit/"
CASES = {"test_selftest_topology_library.py": ("topology_library", {"math"}),
         "test_selftest_sizing_recipe.py": ("sizing_recipe", {"_dc_replace", "json", "math", "np", "nmcnr_predict_ac_response"}),
         "test_selftest_design_report.py": ("design_report", {"os"})}
res = {"rev": REV}
for f, (mod, names) in CASES.items():
    src = subprocess.run(["git", "-C", REPO, "show", "%s:%s%s" % (REV, U, f)], capture_output=True, check=True).stdout.decode("utf-8")
    t = ast.parse(src)
    shim_lines, other = [], []
    for n in t.body:
        if isinstance(n, ast.ImportFrom) and n.module == mod:
            hit = sorted(a.name for a in n.names if (a.asname or a.name) in names)
            shim_lines.append({"line": n.lineno, "names_total": len(n.names), "w1_names": hit})
        elif isinstance(n, (ast.Import, ast.ImportFrom)):
            for a in n.names:
                b = a.asname or a.name.split(".")[0]
                if b in names:
                    other.append({"line": n.lineno, "module": getattr(n, "module", None), "name": a.name, "asname": a.asname})
    uses = collections.Counter(x.id for x in ast.walk(t) if isinstance(x, ast.Name) and x.id in names)
    res[f] = {"engine_module": mod, "shim_import": shim_lines, "other_module_bindings": other, "uses": dict(uses)}
json.dump(res, open(OUT, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
print(json.dumps(res, ensure_ascii=False))
