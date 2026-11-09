"""Extract changed character spans between a4d87f1a and ef911010 per plan file (validation 51)."""
import subprocess, difflib, sys, re, os
W = r"C:/Users/HSLEE/Documents/Todoc/fpga/wt/plan-v6386"
OUT = os.path.dirname(os.path.abspath(__file__))
FILES = ["gain-budget-gmid-sizing", "graph-consumption", "headroom-chain", "offset-trim", "oracle-portability"]

def show(rev, path):
    return subprocess.run(["git", "-C", W, "show", f"{rev}:{path}"], capture_output=True, check=True).stdout.decode("utf-8")

for f in FILES:
    p = f"docs/01-plan/features/{f}.plan.md"
    a = show("a4d87f1a", p).split("\n")
    b = show("ef911010", p).split("\n")
    sm = difflib.SequenceMatcher(None, a, b, autojunk=False)
    lines = []
    for tag, i1, i2, j1, j2 in sm.get_opcodes():
        if tag == "equal":
            continue
        lines.append(f"=== {tag} old {i1+1}-{i2} new {j1+1}-{j2}")
        old = "\n".join(a[i1:i2]); new = "\n".join(b[j1:j2])
        if tag == "replace" and old and new:
            cm = difflib.SequenceMatcher(None, old, new, autojunk=False)
            for t, x1, x2, y1, y2 in cm.get_opcodes():
                if t == "equal":
                    continue
                ctx_b = new[max(0, y1-60):y1].replace("\n", "⏎")
                ctx_a = new[y2:y2+60].replace("\n", "⏎")
                lines.append(f"  [{t}] ...{ctx_b} <<-{old[x1:x2]}->> <<+{new[y1:y2]}+>> {ctx_a}...")
        else:
            if old:
                lines.append("  [-] " + old[:3000])
            if new:
                lines.append("  [+] " + new[:20000])
    with open(os.path.join(OUT, f"chunks_{f}.txt"), "w", encoding="utf-8") as fh:
        fh.write("\n".join(lines))
    print(f, len(a), len(b), sum(len(x) for x in lines))
