"""v52: changed lines -- small lines full old/new; big lines merged changed windows (new text) + old pieces."""
import subprocess, difflib
W = r"C:/Users/HSLEE/Documents/Todoc/fpga/wt/plan-v6386"
OUT = r"C:/Users/HSLEE/Documents/Todoc/fpga/wt/_drafts/evidence/2026-11-02/plan_v6386_v57/win_out.txt"
A, B = "84e4ec99", "e71aa597"
files = ["gain-budget-gmid-sizing", "graph-consumption", "headroom-chain", "offset-strategy", "offset-trim", "oracle-portability"]
BIG = 0; CTX = 200

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
            pairs = []
            if op == "replace" and (i2 - i1) == (j2 - j1):
                pairs = [(a[i1 + k], b[j1 + k], i1 + k + 1, j1 + k + 1) for k in range(i2 - i1)]
            else:
                f.write(f"\n##### {name} {op} old {i1+1}-{i2} new {j1+1}-{j2}\n")
                for k in range(i1, i2):
                    f.write(f"OLD {k+1}: {a[k]}\n")
                for k in range(j1, j2):
                    f.write(f"NEW {k+1}: {b[k]}\n")
                continue
            for x, y, ol, nl in pairs:
                f.write(f"\n##### {name} old {ol} / new {nl}\n")
                if len(x) < BIG and len(y) < BIG:
                    f.write(f"OLD: {x}\nNEW: {y}\n")
                    continue
                cs = difflib.SequenceMatcher(None, x, y, autojunk=False)
                wins = []
                for o2, p1, p2, q1, q2 in cs.get_opcodes():
                    if o2 == "equal":
                        continue
                    lo, hi = max(0, q1 - CTX), min(len(y), q2 + CTX)
                    olo, ohi = max(0, p1 - CTX), min(len(x), p2 + CTX)
                    if wins and lo <= wins[-1][1]:
                        wins[-1][1] = max(wins[-1][1], hi); wins[-1][3] = max(wins[-1][3], ohi)
                    else:
                        wins.append([lo, hi, olo, ohi])
                for lo, hi, olo, ohi in wins:
                    f.write(f"  OLDWIN[{olo}:{ohi}]: {x[olo:ohi]}\n")
                    f.write(f"  NEWWIN[{lo}:{hi}]: {y[lo:hi]}\n\n")
print("ok")
