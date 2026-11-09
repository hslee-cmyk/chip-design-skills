"""measure only (F1/TS6): does an F1-style caller rewrite of tests/tools/derive_achievable_bounds.py break
test_ts6_probe_relocate.py::test_moved_tool_matches_base_except_path_lines? Uses the test module's own judge
(assert_only_path_lines_changed, base_blob_text) from clone <root> (git objects of the clone; base 939f926 must exist).
Rewrite variants (both plausible F1 shapes, names measured from the tool):
  alias  -- `import sizing_recipe as sr` -> `import gmid_sizing_engine as sr` (one line)
  names  -- that line -> `from <MOD> import a, b` + every `sr.<name>` -> `<name>`
Also counts `sr.<name>` uses and their binding modules via the M1-base stand-in plan (argv[2] plan json).
    python -B ts6_f1_probe.py <clone root> <plan.json> <out.json>"""
import ast
import importlib.util
import json
import re
import sys

ROOT, PLAN, OUT = sys.argv[1:4]
A = ROOT + "/skills/analog-gmid-design/assets"
spec = importlib.util.spec_from_file_location("ts6pr", A + "/tests/contracts/test_ts6_probe_relocate.py")
m = importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)
cur = open(A + "/tests/tools/derive_achievable_bounds.py", encoding="utf-8").read()
base = m.base_blob_text("%s/%s" % (m._TESTS_REL, m._TOOL_NAME))
res = {"current_passes": None}
try:
    m.assert_only_path_lines_changed(base, cur, "current")
    res["current_passes"] = True
except AssertionError as e:
    res["current_passes"] = False
    res["current_err"] = str(e)[:300]
uses = sorted({n.attr for n in ast.walk(ast.parse(cur)) if isinstance(n, ast.Attribute)
               and isinstance(n.value, ast.Name) and n.value.id == "sr"})
asg = json.load(open(PLAN, encoding="utf-8"))["assignment"]
res["sr_attr_names"] = {u: (asg.get("sizing_recipe.py::" + u) or {}).get("mod") for u in uses}
res["sr_attr_lines"] = sum(1 for l in cur.splitlines() if re.search(r"\bsr\.", l))
variants = {"alias": cur.replace("import sizing_recipe as sr", "import gmid_sizing_engine as sr", 1)}
mods = sorted({v for v in res["sr_attr_names"].values() if v})
nv = cur.replace("import sizing_recipe as sr",
                 "\n".join("from %s import %s" % (md[:-3], ", ".join(sorted(k for k, v in res["sr_attr_names"].items() if v == md)))
                           for md in mods), 1)
nv = re.sub(r"\bsr\.([A-Za-z_][A-Za-z0-9_]*)", r"\1", nv)
variants["names"] = nv
for k, v in variants.items():
    try:
        m.assert_only_path_lines_changed(base, v, k)
        res[k] = "PASS"
    except AssertionError as e:
        res[k] = "FAIL: " + str(e).splitlines()[0][:200]
json.dump(res, open(OUT, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
print(json.dumps(res, ensure_ascii=False, indent=1))
