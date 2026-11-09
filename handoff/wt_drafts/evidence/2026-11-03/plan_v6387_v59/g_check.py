"""v59: independently check consistency G1~G3: q8 §3.2 ngcc block lower bounds vs start L, spec gain constraints count, P2521 (c) text, P1336 K-1 text."""
import re, json, glob, os, subprocess
E = r"C:/Users/HSLEE/Documents/Todoc/fpga/wt/_drafts/evidence/"
L = r"C:/Users/HSLEE/Documents/Todoc/fpga/chip-design-skills/skills/analog-gmid-design/assets/library/"
W = r"C:/Users/HSLEE/Documents/Todoc/fpga/wt/plan-v6387"
o = open(E + "2026-11-03/plan_v6387_v59/g_check_out.txt", "w", encoding="utf-8")
q = open(E + "2026-11-02/q8_target_gain_candidates.md", encoding="utf-8").read().split("\n")
for i, l in enumerate(q, 1):
    if re.search(r"0\.4092|0\.409|0\.4948|0\.495|M12|동치류 주인", l):
        o.write(f"[q8:{i}] {l[:500]}\n")
o.write("\n")
n = 0; files = sorted(glob.glob(L + "*.sizing_spec.json"))
for f in files:
    t = open(f, encoding="utf-8").read()
    has = bool(re.search(r'"gain_ss_db"', t))
    n += has
    o.write(f"{os.path.basename(f)} gain_ss_db mention: {has}\n")
o.write(f"count {n}/{len(files)}\n\n")
g = subprocess.run(["git", "-C", W, "show", "55fdfee0:docs/01-plan/features/gain-budget-gmid-sizing.plan.md"], capture_output=True).stdout.decode("utf-8").split("\n")
l = g[2520]; i = l.find("(c) **L 칸**"); o.write("P2521(c): " + l[i:i+520] + "\n\n")
o.write("P1336: " + g[1335][:420] + "\n\n")
o.write("P1312 K-1?: " + ("K-1 충돌은 O-215" in g[1311]).__str__() + "\n")
l = g[304]; o.write("P305 has 'L 하한': " + str("이득 L 하한" in l) + "\n")
o.close(); print("ok")
