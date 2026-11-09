"""For each shared function, which compute-block entries (or non-block roots) reach each of its call sites.

Usage: python reach_roots.py <gmid_engine dir>   (reads calls.json/shared.tsv in cwd, writes reach.tsv)
Root = compute-block entry function (module map compute_block + entry_point) or a module function that
nothing in the engine calls (pipeline entries etc.). Class bodies are attributed to the class name.
Approximation: method calls via instances (obj.m()) are not resolved, so a site reached only through
such calls shows root '?(unresolved)'.
"""
import collections
import importlib.util
import json
import os
import sys

ENG = sys.argv[1]
spec = importlib.util.spec_from_file_location("_mm", os.path.join(ENG, "_module_map.py"))
mm = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mm)
block_entry = {}
for e in mm.MODULES:
    if e.compute_block:
        block_entry[("gmid_engine." + e.path[:-3].replace("/", "."), e.entry_point)] = e.compute_block

calls = json.load(open("calls.json", encoding="utf-8"))
callers_of = collections.defaultdict(set)  # callee node -> caller nodes
for c in calls:
    if c["caller_fn"] is None:
        continue
    callers_of[(c["callee_mod"], c["callee"])].add((c["caller_mod"], c["caller_fn"]))

memo = {}


def roots(node, stack=()):
    if node in memo:
        return memo[node]
    if node in block_entry:
        memo[node] = {"BLK:" + block_entry[node]}
        return memo[node]
    if node in stack:
        return set()
    ups = callers_of.get(node)
    if not ups:
        r = {"ROOT:" + node[0].replace("gmid_engine.", "") + "." + node[1]}
    else:
        r = set()
        for u in ups:
            r |= roots(u, stack + (node,))
        if not r:
            r = {"?(cycle)"}
    memo[node] = r
    return r


shared = []
for l in open("shared.tsv", encoding="utf-8").read().splitlines()[1:]:
    p = l.split("\t")
    shared.append((p[0], p[1]))

with open("reach.tsv", "w", encoding="utf-8") as fh:
    fh.write("fn\tsite\troots\n")
    for k in shared:
        for c in calls:
            if (c["callee_mod"], c["callee"]) != k or c["caller_mod"] == c["callee_mod"]:
                continue
            node = (c["caller_mod"], c["caller_fn"])
            r = roots(node) if c["caller_fn"] else {"MODULE-LEVEL"}
            fh.write("%s.%s\t%s:%d[%s]\t%s\n" % (k[0].replace("gmid_engine.", ""), k[1],
                     c["caller_mod"].replace("gmid_engine.", ""), c["line"], c["caller_fn"], ";".join(sorted(r))))
print("ok")
