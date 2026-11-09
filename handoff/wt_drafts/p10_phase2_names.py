"""Read-only: Phase-2 deleted/moved engine names (P5 2a123ba, P5b 6612902, P6 1c5b920) and their
mentions in skills/analog-gmid-design/references/** + SKILL.md + skill-validation-prompt.md at HEAD.
Also records whether each name still has a def anywhere in A/*.py, run_harness.py, A/tests/tools/*.py."""
import ast, os, re, subprocess, sys, glob
R = r"C:\Users\HSLEE\Documents\Todoc\fpga\chip-design-skills"
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "p10_phase2_names.out.txt")
os.chdir(R)

def git(*a):
    return subprocess.run(["git", *a], capture_output=True, text=True, encoding="utf-8", errors="replace").stdout

def defs_of(src):
    names = set()
    try:
        t = ast.parse(src)
    except SyntaxError:
        return names
    for n in t.body:
        if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            names.add(n.name)
            if isinstance(n, ast.ClassDef):
                for m in n.body:
                    if isinstance(m, (ast.FunctionDef, ast.AsyncFunctionDef)):
                        names.add(f"{n.name}.{m.name}")
        elif isinstance(n, (ast.Assign, ast.AnnAssign)):
            tg = n.targets if isinstance(n, ast.Assign) else [n.target]
            for x in tg:
                if isinstance(x, ast.Name):
                    names.add(x.id)
    return names

lines = []
removed = {}
for tag, c in (("P5", "2a123ba"), ("P5b", "6612902"), ("P6", "1c5b920")):
    files = git("diff", "--name-only", f"{c}^", c).split()
    for f in files:
        if not f.endswith(".py"):
            continue
        before = git("show", f"{c}^:{f}")
        after = git("show", f"{c}:{f}")
        gone = defs_of(before) - defs_of(after)
        for g in sorted(gone):
            removed.setdefault(g, []).append(f"{tag}:{f}")
lines.append(f"removed/moved names across P5/P5b/P6: {len(removed)}")

now_defs = set()
for p in glob.glob("skills/analog-gmid-design/assets/*.py") + ["workspaces/run_harness.py"] + \
        glob.glob("skills/analog-gmid-design/assets/tests/tools/*.py"):
    with open(p, encoding="utf-8") as fh:
        d = defs_of(fh.read())
    now_defs |= {(x, p) for x in d}
def where_now(n):
    return sorted({p for x, p in now_defs if x == n})

docs = sorted(glob.glob("skills/analog-gmid-design/references/**/*.md", recursive=True)) + \
    ["skills/analog-gmid-design/SKILL.md", "skills/analog-gmid-design/skill-validation-prompt.md"]
texts = {}
for d in docs:
    with open(d, encoding="utf-8") as fh:
        texts[d] = fh.read().splitlines()

for n in sorted(removed):
    short = n.split(".")[-1]
    if short.startswith("__"):
        continue
    pat = re.compile(r"(?<![A-Za-z0-9_])" + re.escape(short) + r"(?![A-Za-z0-9_])")
    hits = []
    for d, L in texts.items():
        for i, l in enumerate(L, 1):
            if pat.search(l):
                hits.append(f"{d.replace('skills/analog-gmid-design/', '')}:{i}")
    lines.append(f"{n} | {','.join(removed[n])} | now_def={where_now(short) or where_now(n)} | doc_hits={len(hits)} {hits[:20]}")

with open(OUT, "w", encoding="utf-8") as fh:
    fh.write("\n".join(lines) + "\n")
print("\n".join(lines))
