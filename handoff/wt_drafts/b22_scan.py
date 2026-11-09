"""Read-only: backtick identifiers in analog-gmid-design references/SKILL.md that have no def/class anywhere."""
import ast, glob, os, re
R = r"C:\Users\HSLEE\Documents\Todoc\fpga\chip-design-skills"
S = os.path.join(R, "skills", "analog-gmid-design")
A = os.path.join(S, "assets")
defs_engine, defs_tests, defs_other = {}, {}, {}
names_assigned = set()
for p in glob.glob(os.path.join(R, "skills", "**", "*.py"), recursive=True) + glob.glob(os.path.join(R, "workspaces", "*.py")):
    try:
        t = ast.parse(open(p, encoding="utf-8").read())
    except Exception:
        continue
    rel = os.path.relpath(p, R).replace("\\", "/")
    if os.path.dirname(p) == A or rel == "workspaces/run_harness.py":
        bucket = defs_engine
    elif rel.startswith("skills/analog-gmid-design/assets/tests/"):
        bucket = defs_tests
    else:
        bucket = defs_other
    for n in ast.walk(t):
        if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            bucket.setdefault(n.name, []).append(f"{rel}:{n.lineno}")
        elif isinstance(n, ast.Assign):
            for tg in n.targets:
                if isinstance(tg, ast.Name):
                    names_assigned.add(tg.id)
docs = glob.glob(os.path.join(S, "references", "**", "*.md"), recursive=True) + [os.path.join(S, "SKILL.md")]
pat = re.compile(r"`([A-Za-z_][A-Za-z0-9_\.]*)\(")  # `name(` call-form in backticks
pat_block = re.compile(r"\b([a-z_][a-z0-9_]{3,})\(")
rows = []
for d in docs:
    rel = os.path.relpath(d, R).replace("\\", "/")
    in_code = False
    for i, line in enumerate(open(d, encoding="utf-8", errors="replace"), 1):
        if line.strip().startswith("```"):
            in_code = not in_code
            continue
        cands = set(m.group(1).split(".")[-1] for m in pat.finditer(line))
        if in_code:
            cands |= set(m.group(1) for m in pat_block.finditer(line))
        for c in sorted(cands):
            if c in defs_engine:
                continue
            where = "tests:" + defs_tests[c][0] if c in defs_tests else ("other:" + defs_other[c][0] if c in defs_other else "NONE")
            rows.append((rel, i, c, where))
# filter builtins / common
import builtins
skip = set(dir(builtins)) | {"print", "len", "range", "np", "math", "json", "sqrt", "log", "exp", "atan", "abs"}
rows = [r for r in rows if r[2] not in skip]
out = [f"{r[0]}:{r[1]}\t{r[2]}\t{r[3]}" for r in rows]
open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "b22_scan.out.txt"), "w", encoding="utf-8").write("\n".join(out))
from collections import Counter
print(len(rows))
for (name, where), n in Counter((r[2], r[3]) for r in rows).most_common():
    print(n, name, where)
