"""char_<k>.txt 에서 gm/ID 목표별 ID/W·VGS·VDSAT 표 -- char_gmid.log 에 append."""
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
lines = []
for k in "np":
    d = np.loadtxt(HERE / ("char_%s.txt" % k), skiprows=1)
    vg, idd, gm, vdsat, vth = d[:, 0], np.abs(d[:, 1]), np.abs(d[:, 2]), np.abs(d[:, 3]), d[:, 4]
    g = gm / np.maximum(idd, 1e-30)
    lines.append("%s vth(mid sweep)=%.4f" % (k, vth[200]))
    for t in (8, 10, 12, 15, 18, 20):
        m = g < t
        i = int(np.argmax(m)) if k == "n" else int(len(g) - 1 - np.argmax(m[::-1]))
        vgs = vg[i] if k == "n" else 1.8 - vg[i]
        lines.append(" gm/id=%g |vgs|=%.3f ID/W=%.4g A/um vdsat=%.4f" % (t, vgs, idd[i], vdsat[i]))
txt = "\n".join(lines) + "\n"
with open(HERE / "char_gmid.log", "ab") as f:
    f.write(txt.encode("utf-8"))
print(txt)
