"""검증 4 -- (마) 선언 f_low에서 MOS + C_BAT 총면적 최소: W = W_min 고정 대 W 자유(슬라이스 12개), L = 격자점(보간 없음), C_BAT = max(0.1 pF, 1/(2π f_low R)) <= 10 pF.
f_HP = 1/(2π R C) <= f_low (C_X 무시 -- 손계산 꼴 그대로). 밀도 = PDK 선언 0.002 F/m²(zg1_check.txt (1) 엔진 read_pdk_decl 값). 결과 = zg1_total.txt"""
import glob, math
import numpy as np
D = "C:/Users/HSLEE/Documents/Todoc/fpga/lut_data/sky130_lut_v2/"
O = "C:/Users/HSLEE/Documents/Todoc/fpga/wt/_drafts/evidence/2026-10-29/plan_v6385_validation4/zg1_total.txt"
DENS = 0.002
S = {}
for f in sorted(glob.glob(D + "sky130_fd_pr__pfet_01v8__tt__W*um_dc.npz")):
    z = np.load(f, allow_pickle=True)
    S[float(z["W"])] = (np.asarray(z["L"], float), np.abs(np.asarray(z["VGS"], float)), np.abs(np.asarray(z["GDS"], float)))
Ws = sorted(S)
def R(Wk, li, v):
    L, V, G = S[Wk]; o = np.argsort(V)
    return 1/float(np.exp(np.interp(v, V[o], np.log(G[li, :, 0, 0][o]))))
with open(O, "w", encoding="utf-8") as out:
    out.write("| 소자(VSG) | f_low Hz | W_min 고정: (L um, C pF) 총면적 um2 | W 자유: (W um, L um, C pF) 총면적 um2 | 차 |\n|---|---|---|---|---|\n")
    for name, v in (("M19/M20", 0.204), ("M21", 0.40)):
        for fl in (1e3, 10.0, 1.0, 0.1):
            best = {}
            for Wk in Ws:
                for i, L in enumerate(S[Wk][0]):
                    r = R(Wk, i, v)
                    C = max(1e-13, 1 / (2 * math.pi * fl * r))
                    if C > 1e-11:
                        continue
                    a = Wk * L + C / DENS
                    key = "min" if Wk == Ws[0] else "other"
                    for k in (key, "all"):
                        if k not in best or a < best[k][0]:
                            best[k] = (a, Wk, L, C)
            if "all" not in best:
                out.write("| %s(%.3f) | %g | 도달 불가 | 도달 불가 | - |\n" % (name, v, fl)); continue
            a0 = best.get("min"); a1 = best["all"]
            s0 = "도달 불가" if a0 is None else "(%.3g, %.3g) %.4g" % (a0[2]*1e6, a0[3]*1e12, a0[0]*1e12)
            d = "-" if a0 is None else "%+.1f %%" % ((a1[0]/a0[0]-1)*100)
            out.write("| %s(%.3f) | %g | %s | (%.3g, %.3g, %.3g) %.4g | %s |\n" % (name, v, fl, s0, a1[1]*1e6, a1[2]*1e6, a1[3]*1e12, a1[0]*1e12, d))
