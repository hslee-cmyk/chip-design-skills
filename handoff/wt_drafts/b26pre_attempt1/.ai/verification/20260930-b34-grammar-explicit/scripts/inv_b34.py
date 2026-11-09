"""B34 순서 3 인벤토리 확인: base 판 게이트 함수(reachability.build_graph·mutate_changed.inventory)로
base(7243f28)·T(d504784) 트리 그래프의 4 def 인벤토리를 잰다. 도구 main과 같은 test_nodes 필터.
사용: PYTHONPATH=<캐시> python -P inv_b34.py <복제본> <out.json>"""
import json, re, sys
import mutate_changed as mc, reachability as rch

root, out = sys.argv[1:3]
SD = "skills/analog-gmid-design/assets/stick_diagram.py"
DEFS = ("_import_analog_grammar", "find_idiom_matches", "find_stack_edges", "audit_theta_root_direction")
res = {}
for label, rev in (("base", "7243f2846210c0dba62329acb77885f84a26ff76"), ("T", "d504784862151205c1d10d3efa263469e6f620ab")):
    hf = rch.read_tree(root, rev, rch.GRAPH_PREFIXES)
    nodes, edges = rch.build_graph(hf)
    tests = [n for n in nodes if n.startswith(mc.TESTS_PREFIX) and not n.startswith(mc.TESTS_TOOLS)
             and re.search(r"::(Test[^.]*\.)?test[^.]*$", n)]
    new_tests = sorted(t for t in tests if "test_b34_grammar_explicit.py::" in t)
    d = {"n_test_nodes": len(tests), "new_test_functions": new_tests, "defs": {}}
    for q in DEFS:
        inv = mc.inventory(edges, SD + "::" + q, tests)
        d["defs"][q] = {"n": len(inv), "b34": sorted(x.split("::", 1)[1] for x in inv if "test_b34_grammar_explicit.py::" in x),
                        "inventory": inv}
    res[label] = d
for q in DEFS:
    b, t = res["base"]["defs"][q], res["T"]["defs"][q]
    extra = sorted(set(t["inventory"]) - set(b["inventory"]))
    gone = sorted(set(b["inventory"]) - set(t["inventory"]))
    res.setdefault("delta", {})[q] = {"base": b["n"], "T": t["n"], "k": t["n"] - b["n"],
                                      "added_non_b34": [x for x in extra if "test_b34_grammar_explicit.py::" not in x],
                                      "removed": gone, "b34": t["b34"]}
with open(out, "w", encoding="utf-8") as fh:
    json.dump(res, fh, ensure_ascii=False, indent=1)
for q in DEFS:
    print(q, json.dumps({k: v for k, v in res["delta"][q].items()}, ensure_ascii=False))
print("new test functions in graph:", len(res["T"]["new_test_functions"]))
