"""v52: ef911010 -> c19c4f17 plan files, per changed line char-level segments with context."""
import subprocess, difflib, sys
W = r"C:/Users/HSLEE/Documents/Todoc/fpga/wt/plan-v6386"
OUT = r"C:/Users/HSLEE/Documents/Todoc/fpga/wt/_drafts/evidence/2026-11-01/plan_v6386_v52/seg_out.txt"
A, B = "ef911010", "c19c4f17"
files = ["gain-budget-gmid-sizing", "graph-consumption", "headroom-chain", "offset-strategy", "offset-trim", "oracle-portability"]
CTX = int(sys.argv[1]) if len(sys.argv) > 1 else 120

def show(rev, path):
    return subprocess.run(["git", "-C", W, "show", f"{rev}:{path}"], capture_output=True).stdout.decode("utf-8")

with open(OUT, "w", encoding="utf-8") as f:
    for name in files:
        p = f"docs/01-plan/features/{name}.plan.md"
        a = show(A, p).split("\n"); b = show(B, p).split("\n")
        sm = difflib.SequenceMatcher(None, a, b, autojunk=False)
        for op, i1, i2, j1, j2 in sm.get_opcodes():
            if op == "equal":
                continue
            f.write(f"\n===== {name} {op} old {i1+1}-{i2} new {j1+1}-{j2}\n")
            if op == "replace" and (i2 - i1) == (j2 - j1):
                for k in range(i2 - i1):
                    x, y = a[i1 + k], b[j1 + k]
                    f.write(f"--- line old {i1+k+1} / new {j1+k+1} (len {len(x)}->{len(y)})\n")
                    cs = difflib.SequenceMatcher(None, x, y, autojunk=False)
                    for o2, p1, p2, q1, q2 in cs.get_opcodes():
                        if o2 == "equal":
                            continue
                        f.write(f"  [{o2}] ctx: ...{y[max(0,q1-CTX):q1]}\n")
                        f.write(f"     OLD: {x[p1:p2]}\n")
                        f.write(f"     NEW: {y[q1:q2]}\n")
                        f.write(f"     after: {y[q2:q2+CTX]}...\n")
            else:
                for k in range(i1, i2):
                    f.write(f"  - old {k+1}: {a[k][:3000]}\n")
                for k in range(j1, j2):
                    f.write(f"  + new {k+1}: {b[k][:6000]}\n")
print("ok")
