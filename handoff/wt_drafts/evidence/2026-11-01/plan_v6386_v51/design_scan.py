"""Scan design 40/41 (wt/design-v115 HEAD) for O-202~O-212 affected keywords; map hit -> nearest section heading (validation 51).
Output: design_scan_out.txt (per section: keyword counts) to compare with plan LA-1 follow-up table sections."""
import subprocess, re, os, collections
D = r"C:/Users/HSLEE/Documents/Todoc/fpga/wt/design-v115"
OUT = os.path.dirname(os.path.abspath(__file__))
FILES = {"40": "docs/02-design/features/gain-budget-gmid-sizing.40-engine.design.md",
         "41": "docs/02-design/features/gain-budget-gmid-sizing.41-gain-budget.design.md"}
KW = {"floor": r"dc_conduction_floor|conduction_floor", "off_cur": r"dc_off_current|off_current", "tolvdsat_margin": r"\+ ?tol_VDsat|VDSAT_?[a-z,]* \+ tol|VDsat \+ tol|tol_vdsat",
      "win_def": r"dc_window_def", "P7": r"반전 수준 하한|P-7", "gs": r"g = s|g=s", "Ioff": r"I_off", "R0": r"\bR0\b|전도 행|_conduction_rows",
      "stage2": r"stage2|2단계|둘째 단계|conduction_margin", "Von": r"V_on\b|off 유지", "eps": r"ε·ID|\(gm/ID\)·tol_V", "U69": r"U-69", "seal6tol": r"봉인 6", "J1": r"\bJ1\b"}
lines_out = []
for tag, p in FILES.items():
    txt = subprocess.run(["git", "-C", D, "show", f"HEAD:{p}"], capture_output=True, check=True).stdout.decode("utf-8")
    sec = "(top)"; agg = collections.OrderedDict()
    for i, ln in enumerate(txt.split("\n"), 1):
        m = re.match(r"^(#{2,5})\s+(.*)", ln)
        if m:
            sec = m.group(2)[:70]; continue
        for k, rx in KW.items():
            n = len(re.findall(rx, ln))
            if n:
                agg.setdefault(sec, collections.Counter())[k] += n
    lines_out.append(f"##### design {tag}")
    for s, c in agg.items():
        lines_out.append(f"{s}\t" + ", ".join(f"{k}={v}" for k, v in c.items()))
with open(os.path.join(OUT, "design_scan_out.txt"), "w", encoding="utf-8") as fh:
    fh.write("\n".join(lines_out))
