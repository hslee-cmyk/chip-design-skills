"""validation 12: check paths cited in plan lines changed in this edition (07964dfe..74e62d53)."""
import os, re, difflib, sys
D = os.path.dirname(os.path.abspath(__file__))
WT = "C:/Users/HSLEE/Documents/Todoc/fpga/wt"
ENG = WT + "/integ-it12/skills/analog-gmid-design/gmid_engine"
REPO = WT + "/plan-v6385"
A = open(os.path.join(D, "plan_07964dfe.md"), encoding="utf-8").read().split("\n")
B = open(os.path.join(D, "plan_74e62d53.md"), encoding="utf-8").read().split("\n")
sm = difflib.SequenceMatcher(None, A, B, autojunk=False)
changed = set()
for t, i1, i2, j1, j2 in sm.get_opcodes():
    if t != "equal":
        changed.update(range(j1, j2))
out = open(os.path.join(D, "refcheck.txt"), "w", encoding="utf-8")
out.write(f"changed plan lines: {len(changed)} -> {sorted(x+1 for x in changed)}\n")
seen = {}
for j in sorted(changed):
    l = B[j]
    for m in re.finditer(r"`?(wt/_drafts/[^`\s,;)]+)", l):
        p = m.group(1).rstrip("`.")
        seen.setdefault(("draft", p), set()).add(j+1)
    for m in re.finditer(r"`E/([A-Za-z0-9_/\.]+\.(?:py|md))(?::([0-9,\-· ]+))?", l):
        seen.setdefault(("eng", m.group(1)), set()).add(j+1)
    for m in re.finditer(r"`((?:search|metrics|sizing|authoring|pipeline|graph|core)/[A-Za-z0-9_]+\.py)", l):
        seen.setdefault(("eng", m.group(1)), set()).add(j+1)
for (k, p), lines in sorted(seen.items()):
    if k == "draft":
        full = WT + "/" + p[3:] if p.startswith("wt/") else p
        ok = os.path.exists(full)
    else:
        ok = os.path.exists(ENG + "/" + p)
    out.write(f"{'OK ' if ok else 'MISS'} {k} {p} lines {sorted(lines)}\n")
out.close()
