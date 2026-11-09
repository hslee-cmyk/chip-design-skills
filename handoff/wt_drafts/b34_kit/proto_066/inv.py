import re, sys
sys.path.insert(0, "C:/g136/gates/tools/gates")
import mutate_changed as mc, reachability as rch
for rev in ("16b94f1", "sim-K"):
    hf = rch.read_tree("C:/g136/repo", rev, rch.GRAPH_PREFIXES)
    nodes, edges = rch.build_graph(hf)
    tests = [n for n in nodes if n.startswith(mc.TESTS_PREFIX) and not n.startswith(mc.TESTS_TOOLS) and re.search(r"::(Test[^.]*\.)?test[^.]*$", n)]
    row = []
    for q in ("_import_analog_grammar", "find_idiom_matches", "find_stack_edges", "audit_theta_root_direction"):
        inv = mc.inventory(edges, "skills/analog-gmid-design/assets/stick_diagram.py::" + q, tests)
        row.append("%s=%d(b34 %s)" % (q, len(inv), sorted(x.split("::")[-1] for x in inv if "b34" in x)))
    print(rev, "\n  " + "\n  ".join(row))
