"""v58: summarize resid58_out.txt -> per-line table and CAND text; also dump N6.14 scope 15 head, DEC-105 (1), LA-1a table row, (2)(a) for reading."""
import re, collections, subprocess
D = r"C:/Users/HSLEE/Documents/Todoc/fpga/wt/_drafts/evidence/2026-11-03/plan_v6387_v58/"
t = open(D + "resid58_out.txt", encoding="utf-8").read().split("\n\n")
c = collections.Counter(); cand = []
for b in t:
    m = re.match(r"\[(\w+)\] \[([^\]]+)\] <([^>]*)>", b)
    if not m: continue
    c[(m.group(1), m.group(2))] += 1
    if m.group(1) == "CAND": cand.append(b)
with open(D + "resid58_sum.txt", "w", encoding="utf-8") as o:
    for k, v in sorted(c.items()): o.write(f"{k[0]} {k[1]} n={v}\n")
    o.write("\n")
    seen = set()
    for b in cand:
        key = re.match(r"\[\w+\] \[([^\]]+)\]", b).group(1)
        if key in seen: continue
        seen.add(key); o.write(b[:760] + "\n\n")
W = r"C:/Users/HSLEE/Documents/Todoc/fpga/wt/plan-v6387"
g = subprocess.run(["git", "-C", W, "show", "106cd524:docs/01-plan/features/gain-budget-gmid-sizing.plan.md"], capture_output=True).stdout.decode("utf-8").split("\n")
open(D + "gb.md", "w", encoding="utf-8").write("\n".join(g))
with open(D + "dump.txt", "w", encoding="utf-8") as o:
    l = g[304]; i = l.find("**(1)"); o.write(f"P305 [{i}]: {l[max(0,i-100):i+3600]}\n\n")
    o.write(f"P1311: {g[1310]}\n\n")
    l = g[2520]; o.write(f"P2521: {l[:1100]}\n\n")
    for n in (1974,):
        l = g[n-1]; o.write(f"P{n}: {l[:2300]}\n\n")
print(len(cand))
