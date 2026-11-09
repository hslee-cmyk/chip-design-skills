"""v52: design(wt/design-v115 e957ba44) extra patterns not in author grep17; lists hits with section."""
import re, subprocess
W = r"C:/Users/HSLEE/Documents/Todoc/fpga/wt/design-v115"
OUT = r"C:/Users/HSLEE/Documents/Todoc/fpga/wt/_drafts/evidence/2026-11-01/plan_v6386_v52/design_extra_out.txt"
REV = "e957ba44"
files = ['gain-budget-gmid-sizing.40-engine.design.md', 'gain-budget-gmid-sizing.41-gain-budget.design.md',
         'gain-budget-gmid-sizing.42-gap-checklist.design.md', 'oracle-portability.design.md',
         'offset-trim.design.md', 'offset-strategy.design.md', 'gain-budget-gmid-sizing.00-common.design.md']
pats = {
  'cond_margin': r'전도 여유|전도 하한|ε·ID|ε = \(gm/ID\)|I_off ≤|conduction_margin|seal_conduction',
  'sat_margin': r'sat_margin|판정 여유|\+ ?tol_V\b',
  'off_region': r'intended_region.{0,40}off|`off` 선언',
}
head = subprocess.run(["git", "-C", W, "rev-parse", "--short", "HEAD"], capture_output=True, text=True).stdout.strip()
with open(OUT, "w", encoding="utf-8") as o:
    o.write(f"# HEAD {head}\n")
    for f in files:
        t = subprocess.run(["git", "-C", W, "show", f"{REV}:docs/02-design/features/{f}"], capture_output=True).stdout.decode("utf-8").split("\n")
        sec = ""
        for i, l in enumerate(t, 1):
            if l.startswith("#"):
                sec = l.strip("# ").strip()[:60]
            hit = [k for k, v in pats.items() if re.search(v, l)]
            if hit:
                m = re.search("|".join(pats[h] for h in hit), l)
                a = max(0, m.start() - 120)
                o.write(f"[{f[:28]}:{i} | {sec}] {','.join(hit)} :: {l[a:m.end()+160]}\n")
print("ok")
