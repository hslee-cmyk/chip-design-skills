"""Cross-module call scan for gmid_engine (read-only audit, 2026-10-29).

Usage: python scan_shared_calls.py <gmid_engine dir> <out dir>
Writes: calls.json (every resolved cross-module call site), shared.tsv (functions called from >=2 distinct modules).
"""
import ast
import json
import os
import sys
import importlib.util

ENG = sys.argv[1]
OUT = sys.argv[2]
PKG = "gmid_engine"


def modname(path):
    rel = os.path.relpath(path, os.path.dirname(ENG)).replace(os.sep, "/")
    rel = rel[:-3]
    if rel.endswith("/__init__"):
        rel = rel[: -len("/__init__")]
    return rel.replace("/", ".")


files = []
for root, dirs, fs in os.walk(ENG):
    dirs[:] = [d for d in dirs if d not in ("tests", "__pycache__")]
    for f in fs:
        if f.endswith(".py"):
            files.append(os.path.join(root, f))

# module map -> compute block per file
spec = importlib.util.spec_from_file_location("_mm", os.path.join(ENG, "_module_map.py"))
mm = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mm)
block_of = {}
for e in mm.MODULES:
    block_of[PKG + "." + e.path[:-3].replace("/", ".")] = e.compute_block

trees = {}
defs = {}  # module -> {name: lineno}
for p in files:
    m = modname(p)
    src = open(p, encoding="utf-8").read()
    t = ast.parse(src)
    trees[m] = (p, t)
    d = {}
    for node in t.body:
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            d[node.name] = node.lineno
    defs[m] = d


def resolve_from(m, node):
    # absolute module for ImportFrom
    if node.level == 0:
        return node.module
    parts = m.split(".")
    is_pkg = trees[m][0].endswith("__init__.py")
    base = parts if is_pkg else parts[:-1]
    base = base[: len(base) - (node.level - 1)]
    if node.module:
        base = base + node.module.split(".")
    return ".".join(base)


def follow(mod, name, depth=0):
    """Follow re-exports (e.g. package __init__) to the defining module."""
    if depth > 6 or mod not in trees:
        return None
    if name in defs.get(mod, {}):
        return (mod, name)
    for node in trees[mod][1].body:
        if isinstance(node, ast.ImportFrom):
            src = resolve_from(mod, node)
            for a in node.names:
                if (a.asname or a.name) == name:
                    r = follow(src, a.name, depth + 1)
                    if r:
                        return r
    return None


calls = []
for m, (p, t) in trees.items():
    name_map = {}  # local name -> (mod, fn)
    mod_alias = {}  # local name -> module
    for node in ast.walk(t):
        if isinstance(node, ast.ImportFrom):
            src = resolve_from(m, node)
            for a in node.names:
                local = a.asname or a.name
                cand = src + "." + a.name
                if cand in trees:
                    mod_alias[local] = cand
                    continue
                r = follow(src, a.name)
                if r:
                    name_map[local] = r
        elif isinstance(node, ast.Import):
            for a in node.names:
                if a.name in trees:
                    mod_alias[a.asname or a.name.split(".")[0]] = a.name

    # enclosing top-level function for each call
    def visit(node, encl):
        for child in ast.iter_child_nodes(node):
            e = encl
            if isinstance(child, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)) and encl is None:
                e = child.name
            if isinstance(child, ast.Call):
                tgt = None
                f = child.func
                if isinstance(f, ast.Name) and f.id in name_map:
                    tgt = name_map[f.id]
                elif isinstance(f, ast.Attribute) and isinstance(f.value, ast.Name) and f.value.id in mod_alias:
                    r = follow(mod_alias[f.value.id], f.attr)
                    if r:
                        tgt = r
                elif isinstance(f, ast.Name) and f.id in defs[m]:
                    tgt = (m, f.id)
                if tgt:
                    try:
                        args = ast.unparse(child)[:300]
                    except Exception:
                        args = "?"
                    calls.append({
                        "callee_mod": tgt[0], "callee": tgt[1],
                        "caller_mod": m, "caller_fn": e, "line": child.lineno,
                        "caller_block": block_of.get(m), "callee_block": block_of.get(tgt[0]),
                        "text": args,
                    })
            visit(child, e)

    visit(t, None)

os.makedirs(OUT, exist_ok=True)
json.dump(calls, open(os.path.join(OUT, "calls.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=0)

by = {}
for c in calls:
    if c["caller_mod"] == c["callee_mod"]:
        continue
    by.setdefault((c["callee_mod"], c["callee"]), []).append(c)
rows = []
for (cm, fn), cs in by.items():
    mods = sorted({c["caller_mod"] for c in cs})
    if len(mods) >= 2:
        rows.append((cm, fn, defs[cm].get(fn), len(mods), len(cs), mods))
rows.sort()
with open(os.path.join(OUT, "shared.tsv"), "w", encoding="utf-8") as fh:
    fh.write("callee_mod\tfn\tline\tn_caller_mods\tn_calls\tcaller_mods\n")
    for r in rows:
        fh.write("\t".join([r[0], r[1], str(r[2]), str(r[3]), str(r[4]), ",".join(x.replace(PKG + ".", "") for x in r[5])]) + "\n")
print("files", len(files), "calls", len(calls), "shared(>=2 caller mods)", len(rows))
cnt = {}
for r in rows:
    pk = r[0].split(".")[1]
    cnt[pk] = cnt.get(pk, 0) + 1
print(cnt)
