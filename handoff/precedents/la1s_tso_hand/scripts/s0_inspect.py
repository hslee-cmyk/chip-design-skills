"""s0: LUT npz 구조와 PDK 선언 키를 확인한다(엔진 밖 사실 읽기)."""
import json, sys
import numpy as np

L = "C:/Users/HSLEE/Documents/Todoc/fpga/lut_data/sky130_lut_v2/"
R = "C:/Users/HSLEE/Documents/Todoc/fpga/chip-design-skills/skills/analog-gmid-design/assets/"
out = open(sys.argv[1], "w", encoding="utf-8")
for f in ["sky130_fd_pr__nfet_01v8__tt__W5p0000um_dc.npz", "sky130_nfet_pfet_lut_v2_r2.npz"]:
    d = np.load(L + f, allow_pickle=True)
    out.write("== %s\n" % f)
    for k in d.files:
        a = d[k]
        out.write("  %s %s %s %s\n" % (k, a.shape, a.dtype, (a.ravel()[:6] if a.size < 200 or a.ndim == 1 else "")))
pd = json.load(open(R + "sky130_pdk_decl.json", encoding="utf-8"))
def walk(o, p=""):
    if isinstance(o, dict):
        for k, v in o.items():
            walk(v, p + "/" + k)
    elif isinstance(o, list):
        out.write("%s = list[%d] %s\n" % (p, len(o), str(o)[:160]))
    else:
        out.write("%s = %s\n" % (p, str(o)[:160]))
walk(pd)
man = json.load(open(L + "manifest.json", encoding="utf-8"))
out.write("manifest keys %s\n" % list(man.keys()))
out.write(json.dumps(man, ensure_ascii=False)[:3000] + "\n")
out.close()
