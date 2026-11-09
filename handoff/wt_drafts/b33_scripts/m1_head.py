"""B33 개정 측정 1: HEAD 트리에서 변형별 V7 미도달·누수·V3 인벤토리·간선 단조성·시간.
    python -B m1_head.py <root(복제본)> <out.json>
결과는 변형마다 out.json(jsonl)에 append(중간 실패해도 남김)."""
import importlib.util
import json
import os
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT, OUT = sys.argv[1], sys.argv[2]
TESTS_PREFIX = "skills/analog-gmid-design/assets/tests/"
TESTS_TOOLS = "skills/analog-gmid-design/assets/tests/tools/"
import re


def load(variant):
    os.environ["RCH_VARIANT"] = variant
    spec = importlib.util.spec_from_file_location("rch_" + variant, os.path.join(HERE, "reachability_b33.py"))
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


def load_head_tool():
    spec = importlib.util.spec_from_file_location("rch_HEAD", os.path.join(ROOT, "tools/gates/reachability.py"))
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


def emit(obj):
    with open(OUT, "a", encoding="utf-8") as f:
        f.write(json.dumps(obj, ensure_ascii=False) + "\n")
    print(json.dumps(obj, ensure_ascii=False)[:600])


HEADTOOL = load_head_tool()
files = HEADTOOL.read_tree(ROOT, "HEAD", HEADTOOL.GRAPH_PREFIXES)
cfg = json.loads(HEADTOOL._git(ROOT, ["show", "HEAD:tools/gates/gate_config.json"]).decode("utf-8"))["reachability_roots"]
root_sets = {"union": sorted({r for v in cfg.values() for r in v if r.split("::")[0] in files})}
for k, v in cfg.items():
    root_sets[k] = sorted(r for r in v if r.split("::")[0] in files)

t0 = time.perf_counter()
h_nodes, h_edges = HEADTOOL.build_graph(files)
t_head = time.perf_counter() - t0
src_defs = sorted(n for n in h_nodes if HEADTOOL._is_source(n.split("::")[0]) and not n.endswith(("::<module>", "::__main__")))
test_nodes = [n for n in h_nodes if n.startswith(TESTS_PREFIX) and not n.startswith(TESTS_TOOLS)
              and re.search(r"::(Test[^.]*\.)?test[^.]*$", n)]
EXEMPT = ["skills/analog-gmid-design/assets/sizing_recipe.py::lut_conditions_from_npz", "workspaces/run_harness.py::derived_spec"]
emit({"what": "setup", "files": len(files), "src_defs": len(src_defs), "test_nodes": len(test_nodes), "roots": root_sets,
      "head_tool_build_graph_s": round(t_head, 3)})

results = {}
for variant in ("base", "draft", "nosuper", "fixed"):
    M = load(variant)
    t0 = time.perf_counter()
    nodes, edges = M.build_graph(files)
    tb = time.perf_counter() - t0
    assert nodes == h_nodes, "노드 집합이 HEAD 도구와 다르다"
    rec = {"what": "variant", "variant": variant, "build_graph_s": round(tb, 3),
           "binding_nodes": sum(1 for k in edges if "::=" in k)}
    if variant == "base":
        rec["edges_equal_head_tool"] = edges == h_edges
    for rs, roots in root_sets.items():
        for r3 in (False, True):
            seen = M.reach(edges, roots, M._source_node if r3 else None)
            un = [d for d in src_defs if d not in seen]
            key = "%s%s" % (rs, "+R3" if r3 else "")
            rec["unreached_" + key] = len(un)
            if rs == "union":
                rec["unreached_list_" + key] = un
                rec["nonsource_reached_" + key] = sum(1 for n in seen if "::=" not in n and not M._source_node(n))
                rec["exempt_reached_" + key] = [e for e in EXEMPT if e in seen]
    # V3 인벤토리
    t0 = time.perf_counter()
    src_set = set(src_defs)
    cnt = {d: 0 for d in src_defs}
    pairs = 0
    for t in test_nodes:
        r = M.reach(edges, [t])
        hit = r & src_set
        pairs += len(hit)
        for d in hit:
            cnt[d] += 1
    rec["v3_reach_all_tests_s"] = round(time.perf_counter() - t0, 3)
    rec["v3_pairs"] = pairs
    rec["v3_inventory0"] = sorted(d for d, c in cnt.items() if c == 0)
    rec["v3_inventory0_n"] = len(rec["v3_inventory0"])
    vals = sorted(cnt.values())
    rec["v3_median"] = vals[len(vals) // 2]
    rec["v3_sample"] = {k: cnt.get(k) for k in ("skills/analog-gmid-design/assets/sizing_recipe.py::SemiEmpiricalGmIdLUT.__init__",
                                                "skills/analog-gmid-design/assets/sizing_recipe.py::_metric_sum_current")}
    results[variant] = (nodes, edges, rec)
    emit(rec)

# 단조성: base 간선 ⊆ 변형 간선? 빠진 간선 분류
b_edges = results["base"][1]
for variant in ("draft", "nosuper", "fixed"):
    e = results[variant][1]
    missing = []
    for k, vs in b_edges.items():
        lost = vs - e.get(k, set())
        for x in lost:
            missing.append((k, x))
    dunder_targets = all(x.rsplit(".", 1)[-1].startswith("__") and x.endswith("__") for _, x in missing)
    # 제거로 도달이 줄어든 소스 def (R3 없는 같은 루트 비교: base 그래프 도달 - 변형 그래프 도달)
    lost_reach = {}
    for rs, roots in root_sets.items():
        sb = results["base"][0] and results["base"][2]
        bseen = results["base"][1]
        M = load(variant)
        s_base = M.reach(b_edges, roots)
        s_var = M.reach(e, roots)
        lost_reach[rs] = sorted(d for d in src_defs if d in s_base and d not in s_var)
    # 같은 질문을 R3 적용으로: base 그래프+R3 대비 변형+R3
    lost_r3 = {}
    for rs, roots in root_sets.items():
        M = load(variant)
        lost_r3[rs] = sorted(d for d in src_defs if d in M.reach(b_edges, roots, M._source_node)
                             and d not in M.reach(e, roots, M._source_node))
    emit({"what": "monotone", "variant": variant, "missing_old_edges": len(missing),
          "missing_all_dunder_targets": dunder_targets, "missing_sample": missing[:12],
          "missing_sources": sorted({k for k, _ in missing})[:20],
          "src_defs_lost_reach_noR3": lost_reach, "src_defs_lost_reach_R3": lost_r3})

# 변형 간 미도달 집합 차이(union+R3)
u = {v: set(results[v][2]["unreached_list_union+R3"]) for v in results}
emit({"what": "diff_unreached", "draft_minus_fixed": sorted(u["draft"] - u["fixed"]), "fixed_minus_draft": sorted(u["fixed"] - u["draft"]),
      "nosuper_vs_fixed": sorted(u["nosuper"] ^ u["fixed"])})
inv = {v: set(results[v][2]["v3_inventory0"]) for v in results}
emit({"what": "diff_inventory0", "fixed_minus_draft": sorted(inv["fixed"] - inv["draft"]),
      "fixed_minus_base": sorted(inv["fixed"] - inv["base"]), "draft_minus_fixed": sorted(inv["draft"] - inv["fixed"])})
