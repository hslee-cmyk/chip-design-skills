"""Q-ZG1 (라) 근거: W 슬라이스 DC LUT(pfet W 0.42 um = W_min, tt) VDS=0·VS=0(bulk = source) 점 gds 의 L 의존.
f_HP = gds/(2 pi C_BAT), C_BAT 상자 [0.1 pF, 10 pF](DEC-105 (10)(a) '10번'), GBW = erfc_ota sizing_spec gbw_ss_hz 1.37 MHz.
결과 = zg1_L.txt"""
import math
import numpy as np

P = "C:/Users/HSLEE/Documents/Todoc/fpga/lut_data/sky130_lut_v2/sky130_fd_pr__pfet_01v8__tt__W0p4200um_dc.npz"
O = "C:/Users/HSLEE/Documents/Todoc/fpga/wt/_drafts/evidence/2026-10-29/plan_v6385_v3/zg1_L.txt"
d = np.load(P, allow_pickle=True)
GBW = 1.37e6
L = d["L"]; V = d["VGS"]; VD = d["VDS"]; VS = d["VS"]; G = d["GDS"]; GM = d["GM"]
assert VD[0] == 0.0 and VS[0] == 0.0
out = open(O, "w", encoding="utf-8")
out.write("source %s, VDS = 0, VS = 0\n" % P)
out.write("| L um | VSG V | gds S | gm S | R Ohm | f_HP 0.1pF Hz | f_HP 10pF Hz | f_HP(0.1pF)/GBW | C_BAT for f_HP = GBW/100 (pF) |\n|---|---|---|---|---|---|---|---|---|\n")
for li, l in enumerate(L):
    for vsg in (0.225, 0.3, 0.375, 0.45, 0.6):
        vi = int(np.argmin(abs(V - vsg)))
        g = float(G[li, vi, 0, 0])
        gm = float(GM[li, vi, 0, 0])
        if g <= 0:
            out.write("| %.3g | %.4g | %.3e | - |\n" % (l * 1e6, V[vi], g))
            continue
        f1 = g / (2 * math.pi * 1e-13)
        f10 = g / (2 * math.pi * 1e-11)
        creq = g / (2 * math.pi * GBW / 100) * 1e12
        out.write("| %.3g | %.4g | %.3e | %.1e | %.3e | %.3e | %.3e | %.2e | %.3g |\n" % (l * 1e6, V[vi], g, gm, 1 / g, f1, f10, f1 / GBW, creq))
out.close()
print(open(O, encoding="utf-8").read())
