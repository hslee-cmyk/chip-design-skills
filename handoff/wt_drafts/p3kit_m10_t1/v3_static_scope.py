"""measure only: V3 target/mutant counts without running tests (gate mutate_changed selection incl. G1 proto + card 35 scope).
    python -B v3_static_scope.py <root> <gates dir> <base> <head> <out.json>"""
import ast
import collections
import json
import subprocess
import sys

root, GC, base, head, out = sys.argv[1:6]
sys.path.insert(0, GC)
import mutate_changed as mc  # noqa: E402
import reachability as rch  # noqa: E402

diff = subprocess.run(["git", "-C", root, "diff", "--name-only", "--no-renames", "--diff-filter=AM", base, head],
                      capture_output=True).stdout.decode().split()
targets = [p for p in diff if p.endswith(".py") and rch._is_source(p)]
hf = rch.read_tree(root, head, rch.GRAPH_PREFIXES)
bf = rch.read_tree(root, base, rch.GRAPH_PREFIXES)
nodes, edges = rch.build_graph(hf)
test_nodes = [n for n in nodes if n.startswith(mc.TESTS_PREFIX) and not n.startswith(mc.TESTS_TOOLS)
              and __import__("re").search(r"::(Test[^.]*\.)?test[^.]*$", n)]
mv = None
if hasattr(rch, "moved_defs"):
    B = {k: v for k, v in bf.items() if rch._is_source(k)}
    Hh = {k: v for k, v in hf.items() if rch._is_source(k)}
    try:
        mv = rch.moved_defs(rch.SourceIndex(B), rch.SourceIndex(Hh))
    except Exception:
        mv = rch.moved_defs(B, Hh)
res = {"targets": targets, "defs": {}}
for p in targets:
    hs = hf[p]
    bs = bf.get(p)
    bdefs = dict(rch.iter_defs(ast.parse(bs))) if bs else {}
    for q, fn in mc.changed_defs(bs, hs):
        if mv is not None and hasattr(rch, "g1_excluded") and rch.g1_excluded(mv, p, q, fn):
            continue
        scope = mc._Scope(bdefs[q], fn) if q in bdefs else None
        ops = collections.Counter()
        tg = nt = 0
        lines_t = collections.Counter()
        for opname, npath, mfn in mc.mutants(fn, hs):
            if scope is not None and not scope.targets(opname, npath):
                nt += 1
                continue
            tg += 1
            ops[opname] += 1
        inv = mc.inventory(edges, "%s::%s" % (p, q), test_nodes)
        inv_files = collections.Counter(t.split("::")[0].rsplit("/", 1)[-1] for t in inv)
        res["defs"]["%s::%s" % (p, q)] = {"targeted": tg, "not_targeted": nt, "ops": dict(ops), "new_def": scope is None,
                                          "inventory_n": len(inv), "inventory_files": dict(inv_files.most_common()),
                                          "inventory_first": inv[:5]}
json.dump(res, open(out, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
print(json.dumps({k: {kk: vv for kk, vv in v.items() if kk not in ("inventory_first",)} for k, v in res["defs"].items()}, ensure_ascii=False))
