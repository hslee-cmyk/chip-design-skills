"""measure only: which run_harness attributes are read by tracked .py files (AST). python -B harness_attr_reads.py <repo> <rev> <out.json>
Aliases: `import run_harness as X`, `import run_harness`, `X = _import("run_harness")`/`importlib.import_module("run_harness")`,
`from run_harness import a, b`. Reads: X.<attr>, getattr(X, "<attr>")."""
import ast
import collections
import json
import subprocess
import sys

R, REV, OUT = sys.argv[1:4]
files = subprocess.run(["git", "-C", R, "ls-tree", "-r", "--name-only", REV], capture_output=True).stdout.decode().split("\n")
files = [f for f in files if f.endswith(".py")]
reads = collections.defaultdict(set)
from_imports = collections.defaultdict(set)
parse_err = []
for f in files:
    src = subprocess.run(["git", "-C", R, "show", "%s:%s" % (REV, f)], capture_output=True).stdout
    if b"run_harness" not in src:
        continue
    try:
        t = ast.parse(src.decode("utf-8"))
    except Exception as e:
        parse_err.append(f)
        continue
    aliases = set()
    for n in ast.walk(t):
        if isinstance(n, ast.Import):
            for a in n.names:
                if a.name == "run_harness":
                    aliases.add(a.asname or "run_harness")
        elif isinstance(n, ast.ImportFrom) and n.module == "run_harness":
            for a in n.names:
                from_imports[f].add(a.name)
        elif isinstance(n, ast.Assign) and isinstance(n.value, ast.Call) and n.value.args and \
                isinstance(n.value.args[0], ast.Constant) and n.value.args[0].value == "run_harness":
            for tg in n.targets:
                if isinstance(tg, ast.Name):
                    aliases.add(tg.id)
    for n in ast.walk(t):
        if isinstance(n, ast.Attribute) and isinstance(n.value, ast.Name) and n.value.id in aliases:
            reads[f].add(n.attr)
        elif isinstance(n, ast.Call) and isinstance(n.func, ast.Name) and n.func.id in ("getattr", "setattr", "hasattr") and \
                len(n.args) >= 2 and isinstance(n.args[0], ast.Name) and n.args[0].id in aliases and isinstance(n.args[1], ast.Constant):
            reads[f].add(n.args[1].value)
allattrs = collections.Counter(a for v in reads.values() for a in v)
res = {"rev": REV, "files_reading": {k: sorted(v) for k, v in sorted(reads.items())}, "from_imports": {k: sorted(v) for k, v in from_imports.items()},
       "attr_counts": dict(allattrs.most_common()), "parse_errors": parse_err}
json.dump(res, open(OUT, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
print(json.dumps({"n_files": len(reads), "attr_counts": res["attr_counts"], "from_imports": res["from_imports"]}, ensure_ascii=False))
