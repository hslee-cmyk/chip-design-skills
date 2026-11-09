"""Check whether removed plan text (a4d87f1a -> ef911010, spans >= 150 chars) is preserved verbatim in the plan's history file at ef911010 (validation 51).
Output: moved_check_out.txt -- per plan: removed spans count, found-in-history count, list of not-found span heads."""
import subprocess, difflib, os
W = r"C:/Users/HSLEE/Documents/Todoc/fpga/wt/plan-v6386"
OUT = os.path.dirname(os.path.abspath(__file__))
FILES = ["gain-budget-gmid-sizing", "graph-consumption", "headroom-chain", "offset-trim", "oracle-portability"]
def show(rev, p):
    return subprocess.run(["git", "-C", W, "show", f"{rev}:{p}"], capture_output=True, check=True).stdout.decode("utf-8")
res = []
for f in FILES:
    a = show("a4d87f1a", f"docs/01-plan/features/{f}.plan.md").split("\n")
    b = show("ef911010", f"docs/01-plan/features/{f}.plan.md").split("\n")
    h = show("ef911010", f"docs/01-plan/features/{f}.history.md")
    hn = "".join(h.split())
    sm = difflib.SequenceMatcher(None, a, b, autojunk=False)
    spans = []
    for t, i1, i2, j1, j2 in sm.get_opcodes():
        if t in ("replace", "delete"):
            old = "\n".join(a[i1:i2]); new = "\n".join(b[j1:j2])
            cm = difflib.SequenceMatcher(None, old, new, autojunk=False)
            for tt, x1, x2, y1, y2 in cm.get_opcodes():
                if tt in ("replace", "delete") and x2 - x1 >= 150:
                    spans.append((i1 + 1, old[x1:x2]))
    found = 0; miss = []
    for ln, s in spans:
        core = "".join(s.split())
        # test 3 probes (head/mid/tail 60 chars, whitespace-insensitive)
        probes = [core[:60], core[len(core)//2:len(core)//2+60], core[-60:]]
        if all(p in hn for p in probes):
            found += 1
        else:
            miss.append(f"  old line {ln}: {s[:160]!r}")
    res.append(f"{f}: removed spans>=150 = {len(spans)}, found in history = {found}, missing = {len(miss)}")
    res.extend(miss[:40])
with open(os.path.join(OUT, "moved_check_out.txt"), "w", encoding="utf-8") as fh:
    fh.write("\n".join(res))
