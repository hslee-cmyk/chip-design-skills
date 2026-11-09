"""Print design 40/41 keyword hits (with +-220 chars) in sections NOT listed in plan LA-1 follow-up table (validation 51). -> design_hits_out.txt"""
import subprocess, re, os
D = r"C:/Users/HSLEE/Documents/Todoc/fpga/wt/design-v115"
OUT = os.path.dirname(os.path.abspath(__file__))
FILES = {"40": "docs/02-design/features/gain-budget-gmid-sizing.40-engine.design.md",
         "41": "docs/02-design/features/gain-budget-gmid-sizing.41-gain-budget.design.md"}
LISTED = {"40": ("2.4.8", "3.7 ", "3.8 ", "3.10.4", "11."), "41": ("4.6", "4.7", "5.12.8", "6. ", "6.2", "6.7")}
RX = re.compile(r"dc_conduction_floor|conduction_floor|dc_off_current|off_current|\+ ?tol_VDsat|VDsat \+ tol|VDSAT_?[a-z,]* \+ tol|tol_vdsat|dc_window_def|반전 수준 하한|P-7|g = s|I_off|\bR0\b|전도 행|stage2|2단계|conduction_margin|ε·ID|\(gm/ID\)·tol_V|U-69|봉인 6|\bJ1\b")
res = []
for tag, p in FILES.items():
    txt = subprocess.run(["git", "-C", D, "show", f"HEAD:{p}"], capture_output=True, check=True).stdout.decode("utf-8")
    sec = "(top)"
    for i, ln in enumerate(txt.split("\n"), 1):
        m = re.match(r"^(#{2,5})\s+(.*)", ln)
        if m:
            sec = m.group(2); continue
        if sec.startswith(LISTED[tag]):
            continue
        for mm in RX.finditer(ln):
            s, e = mm.start(), mm.end()
            res.append(f"[d{tag}:{i} §{sec[:40]}] <{mm.group(0)}> ...{ln[max(0,s-220):e+220]}...")
with open(os.path.join(OUT, "design_hits_out.txt"), "w", encoding="utf-8") as fh:
    fh.write("\n".join(res))
print(len(res))
