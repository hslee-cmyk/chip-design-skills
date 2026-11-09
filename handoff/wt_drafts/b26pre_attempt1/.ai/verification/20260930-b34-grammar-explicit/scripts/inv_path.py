"""T 그래프에서 새 test 노드의 직접 간선과, 대상 def까지의 최단 경로(BFS)를 보인다(인벤토리 k 원인 확인)."""
import collections, sys
import reachability as rch

root, rev = sys.argv[1:3]
hf = rch.read_tree(root, rev, rch.GRAPH_PREFIXES)
nodes, edges = rch.build_graph(hf)
P = "skills/analog-gmid-design/assets/tests/contracts/test_b34_grammar_explicit.py::"
SD = "skills/analog-gmid-design/assets/stick_diagram.py::"
print("edges type:", type(edges).__name__)
adj = edges if isinstance(edges, dict) else None
if adj is None:
    adj = collections.defaultdict(set)
    for a, b in edges:
        adj[a].add(b)
for t in ("test_b34_c5_import_without_grammar_succeeds", "test_b34_c4_search_path_inserted_first_once",
          "test_b34_c6_theta_without_findings", "test_b34_c5_no_gate_devices_unchanged"):
    src = P + t
    print("==", t, "direct:", sorted(adj.get(src, ())))
    for q in ("_import_analog_grammar", "find_stack_edges", "find_idiom_matches", "audit_theta_root_direction"):
        goal = SD + q
        prev = {src: None}
        dq = collections.deque([src])
        while dq:
            u = dq.popleft()
            if u == goal:
                break
            for v in adj.get(u, ()):
                if v not in prev:
                    prev[v] = u
                    dq.append(v)
        if goal in prev:
            path, u = [], goal
            while u is not None:
                path.append(u)
                u = prev[u]
            print("  ->", q, ":", " => ".join(reversed(path)))
        else:
            print("  ->", q, ": unreachable")
