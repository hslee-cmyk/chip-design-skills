"""B33 개정 측정 5: 계약 12 미리보기 -- 대상 def별 V3 인벤토리 크기(HEAD 트리, base 도구 vs 시제품 fixed/draft). test 실행 없음.
    python -B m5_inventory.py <root> <base reachability.py> <out.json>"""
import importlib.util
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT, BASEP, OUT = sys.argv[1:4]
A = "skills/analog-gmid-design/assets/"
TARGETS = [A + "sizing_recipe.py::lut_conditions_from_npz", "workspaces/run_harness.py::derived_spec",
           A + "sizing_recipe.py::width_from_id_density", A + "sizing_recipe.py::_build_theta_evaluator._evaluate",
           A + "sizing_recipe.py::compute_metric", A + "sizing_recipe.py::apply_theta_feed",
           A + "stick_diagram.py::kcl_series_union", A + "sizing_recipe.py::optimize_full_circuit_budget"]


def load(path, name, variant=None):
    if variant:
        os.environ["RCH_VARIANT"] = variant
    s = importlib.util.spec_from_file_location(name, path)
    m = importlib.util.module_from_spec(s)
    s.loader.exec_module(m)
    return m


B = load(BASEP, "b")
files = B.read_tree(ROOT, "HEAD", B.GRAPH_PREFIXES)
res = {}
for k, m in (("base", B), ("fixed", load(os.path.join(HERE, "reachability_b33.py"), "f", "fixed")),
             ("draft", load(os.path.join(HERE, "reachability_b33.py"), "d", "draft"))):
    nodes, edges = m.build_graph(files)
    tests = [n for n in nodes if n.startswith(A + "tests/") and not n.startswith(A + "tests/tools/")
             and re.search(r"::(Test[^.]*\.)?test[^.]*$", n)]
    reach = {t: m.reach(edges, [t]) for t in tests}
    res[k] = {t: (sum(1 for x in tests if t in reach[x]) if t in nodes else None) for t in TARGETS}
json.dump(res, open(OUT, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
for t in TARGETS:
    print(t.split("::")[-1], res["base"][t], res["fixed"][t], res["draft"][t])
