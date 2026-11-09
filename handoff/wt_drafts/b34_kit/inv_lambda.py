import re, sys
CL = "C:/g123/repo"
sys.path.insert(0, CL + "/tools/gates")
import mutate_changed as mc, reachability as rch
head_files = rch.read_tree(CL, "sim-b34", rch.GRAPH_PREFIXES)
rel = "skills/analog-gmid-design/assets/tests/contracts/test_b34_v4probe.py"
head_files[rel] = open("C:/g123/seq_P2/" + rel, encoding="utf-8").read()
nodes, edges = rch.build_graph(head_files)
tests = [n for n in nodes if n.startswith(mc.TESTS_PREFIX) and not n.startswith(mc.TESTS_TOOLS) and re.search(r"::(Test[^.]*\.)?test[^.]*$", n)]
inv = mc.inventory(edges, "skills/analog-gmid-design/assets/stick_diagram.py::find_stack_edges", tests)
print(len(inv), sorted(x.split("::")[-1] for x in inv if "b34" in x))
