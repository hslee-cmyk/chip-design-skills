"""measure only: structure of unit/test_selftest_*.py at a rev in repo R. python -B ts_struct.py <repo> <rev> <out.json>"""
import ast
import collections
import json
import subprocess
import sys

R, REV, OUT = sys.argv[1:4]
U = "skills/analog-gmid-design/assets/tests/unit/"
res = {}
for m in ["sizing_recipe", "stick_diagram", "design_report", "topology_library"]:
    p = U + "test_selftest_%s.py" % m
    src = subprocess.run(["git", "-C", R, "show", "%s:%s" % (REV, p)], capture_output=True).stdout.decode("utf-8")
    t = ast.parse(src)
    kinds = collections.Counter()
    tests, fix, helpers, classes, assigns = [], [], [], [], []
    for n in t.body:
        if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef)):
            isfix = any("fixture" in ast.unparse(d) for d in n.decorator_list)
            if n.name.startswith("test"):
                tests.append(n.name)
            elif isfix:
                fix.append(n.name)
            else:
                helpers.append(n.name)
        elif isinstance(n, ast.ClassDef):
            classes.append(n.name)
        else:
            kinds[type(n).__name__] += 1
            if isinstance(n, (ast.Assign, ast.AnnAssign)):
                assigns.append(ast.unparse(n)[:80])
    res[m] = {"lines": len(src.splitlines()), "tests": len(tests), "fixtures": fix, "helpers": helpers, "classes": classes,
              "stmts": dict(kinds), "assigns": assigns,
              "dup_tests": [k for k, v in collections.Counter(tests).items() if v > 1], "test_names": tests}
allnames = collections.Counter(n for v in res.values() for n in v["test_names"])
res["_cross_file_dup_test_names"] = sorted(k for k, v in allnames.items() if v > 1)
allfix = collections.Counter(n for k, v in res.items() if not k.startswith("_") for n in v["fixtures"] + v["helpers"])
res["_cross_file_dup_fixture_helper_names"] = sorted(k for k, v in allfix.items() if v > 1)
json.dump(res, open(OUT, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
for k, v in res.items():
    if k.startswith("_"):
        print(k, v)
    else:
        print(k, {kk: (vv if not isinstance(vv, list) or len(vv) < 12 else "%d items" % len(vv)) for kk, vv in v.items() if kk != "test_names"})
