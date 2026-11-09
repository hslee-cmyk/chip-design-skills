"""Extract segments from a plan line at ef911010 (validation 51). usage: seg.py <plan> <lineno> <len> <key1> [key2...] -> seg_out.txt (overwrite)"""
import subprocess, sys, os
W = r"C:/Users/HSLEE/Documents/Todoc/fpga/wt/plan-v6386"
OUT = os.path.dirname(os.path.abspath(__file__))
f, n, L = sys.argv[1], int(sys.argv[2]), int(sys.argv[3])
txt = subprocess.run(["git", "-C", W, "show", f"ef911010:docs/01-plan/features/{f}.plan.md"], capture_output=True, check=True).stdout.decode("utf-8")
ln = txt.split("\n")[n-1]
res = []
for key in sys.argv[4:]:
    i = ln.find(key)
    res.append(f"===== {f}:{n} key={key} pos={i}\n" + (ln[i:i+L] if i >= 0 else "(not found)"))
with open(os.path.join(OUT, "seg_out.txt"), "w", encoding="utf-8") as fh:
    fh.write("\n\n".join(res))
