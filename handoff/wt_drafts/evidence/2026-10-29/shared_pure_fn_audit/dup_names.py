"""Functions (module top-level) whose name (leading '_' stripped) is defined in >=2 engine modules -- twin-implementation heuristic.
Usage: python dup_names.py <gmid_engine dir>  -> dup_names.tsv"""
import ast, os, sys, collections
ENG = sys.argv[1]
by = collections.defaultdict(list)
for root, dirs, fs in os.walk(ENG):
    dirs[:] = [d for d in dirs if d not in ("tests", "__pycache__")]
    for f in fs:
        if f.endswith(".py"):
            p = os.path.join(root, f)
            for n in ast.parse(open(p, encoding="utf-8").read()).body:
                if isinstance(n, ast.FunctionDef):
                    by[n.name.lstrip("_")].append(os.path.relpath(p, ENG).replace(os.sep, "/") + ":" + str(n.lineno))
with open("dup_names.tsv", "w", encoding="utf-8") as fh:
    for k in sorted(by):
        if len(by[k]) >= 2:
            fh.write(k + "\t" + ",".join(by[k]) + "\n")
print(sum(1 for k in by if len(by[k]) >= 2))
