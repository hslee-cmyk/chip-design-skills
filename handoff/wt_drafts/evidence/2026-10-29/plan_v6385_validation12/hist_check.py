"""validation 12: check history «원문» rows are verbatim substrings of older plan versions."""
import os, re
D = os.path.dirname(os.path.abspath(__file__))
D11 = os.path.join(os.path.dirname(D), "plan_v6385_validation11")
H = open(os.path.join(D, "hist_74e62d53.md"), encoding="utf-8").read().split("\n")
P = {"adb3686a": open(os.path.join(D, "plan_adb3686a.md"), encoding="utf-8").read(),
     "6a31bf1c": open(os.path.join(D11, "plan_6a31bf1c.md"), encoding="utf-8").read(),
     "74e62d53": open(os.path.join(D, "plan_74e62d53.md"), encoding="utf-8").read()}
out = open(os.path.join(D, "hist_check.txt"), "w", encoding="utf-8")
for ln in [1945] + list(range(1948, 1957)):
    row = H[ln-1]
    for m in re.finditer(r"«(.*?)»", row):
        q = m.group(1)
        parts = [p for p in re.split(r"\s*…\s*", q) if p]
        res = {k: all(p in v for p in parts) for k, v in P.items()}
        out.write(f"{ln}: len={len(q)} in_adb={res['adb3686a']} in_6a31={res['6a31bf1c']} in_new={res['74e62d53']} :: {q[:90]}\n")
        if not (res['adb3686a'] or res['6a31bf1c']):
            # find longest prefix present
            for k in ("adb3686a", "6a31bf1c"):
                lo, hi = 0, len(q)
                while lo < hi:
                    mid = (lo+hi+1)//2
                    if q[:mid] in P[k]: lo = mid
                    else: hi = mid-1
                out.write(f"   longest prefix in {k}: {lo} -> ...{q[max(0,lo-40):lo+40]!r}\n")
out.close()
