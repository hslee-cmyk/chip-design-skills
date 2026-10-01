"""V3 준비(auditor, P9 순서 3): base 판 mutate_changed/reachability로 <rev> 트리의 정적 호출 그래프에서
stick_diagram.py::kcl_series_union 과 ::kcl_series_union.find 인벤토리를 구한다(mutate_changed.main과 같은 식).
사용: python -P v3_inv.py <root> <rev> <out.json>"""
import json, re, sys
import mutate_changed as mc, reachability as rch
root, rev, out = sys.argv[1:4]
head_files = rch.read_tree(root, rev, rch.GRAPH_PREFIXES)
nodes, edges = rch.build_graph(head_files)
test_nodes = [n for n in nodes if n.startswith(mc.TESTS_PREFIX) and not n.startswith(mc.TESTS_TOOLS)
              and re.search(r"::(Test[^.]*\.)?test[^.]*$", n)]
P = "skills/analog-gmid-design/assets/stick_diagram.py"
res = {"rev": rev, "n_test_nodes": len(test_nodes)}
for q in ("kcl_series_union", "kcl_series_union.find", "_kcl_and_matching_edges"):
    tgt = "%s::%s" % (P, q)
    inv = mc.inventory(edges, tgt, test_nodes)
    res[q] = {"target_in_graph": tgt in nodes, "n": len(inv), "tests": inv}
    print(q, "in_graph", tgt in nodes, "n", len(inv))
a, b = set(res["kcl_series_union"]["tests"]), set(res["kcl_series_union.find"]["tests"])
res["find_minus_ksu"] = len(b - a); res["ksu_minus_find"] = len(a - b)
res["new_test_in_ksu"] = sorted(t for t in a if "test_dup_kcl_edges" in t)
res["has_blob_reader_test"] = [t for t in b if "test_base_blob_reader_reads_the_base_tree" in t]
print("find-ksu", res["find_minus_ksu"], "ksu-find", res["ksu_minus_find"], "new in ksu", len(res["new_test_in_ksu"]), "blob_reader", res["has_blob_reader_test"])
json.dump(res, open(out, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
