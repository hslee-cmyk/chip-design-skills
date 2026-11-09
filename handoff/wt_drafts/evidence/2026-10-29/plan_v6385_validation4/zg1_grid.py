"""검증 4 -- 보간 없이 격자점만: VSG 0.40/0.375/0.204 V, 슬라이스 W 마다 L 격자점의 R·면적. 목표 R 이상을 내는 최소 면적 (W, L) 대 W_min 최소 면적. 결과 = zg1_grid.txt"""
import glob, math
import numpy as np
D = "C:/Users/HSLEE/Documents/Todoc/fpga/lut_data/sky130_lut_v2/"
O = "C:/Users/HSLEE/Documents/Todoc/fpga/wt/_drafts/evidence/2026-10-29/plan_v6385_validation4/zg1_grid.txt"
S = {}
for f in sorted(glob.glob(D + "sky130_fd_pr__pfet_01v8__tt__W*um_dc.npz")):
    z = np.load(f, allow_pickle=True)
    S[float(z["W"])] = (np.asarray(z["L"], float), np.abs(np.asarray(z["VGS"], float)), np.abs(np.asarray(z["GDS"], float)))
Ws = sorted(S)
def R(Wk, li, v):
    L, V, G = S[Wk]; o = np.argsort(V)
    return 1/float(np.exp(np.interp(v, V[o], np.log(G[li, :, 0, 0][o]))))
with open(O, "w", encoding="utf-8") as out:
    for v in (0.204, 0.375, 0.40):
        pts = [(Wk*S[Wk][0][i], Wk, S[Wk][0][i], R(Wk, i, v)) for Wk in Ws for i in range(len(S[Wk][0]))]
        out.write("\n## VSG %.3f (격자점만, 보간 없음)\n| R 목표 | W_min 최소 면적 um2 (L) R | 전체 최소 면적 um2 (W, L) R | 차 |\n|---|---|---|---|\n" % v)
        for Rt in (1e9, 1e10, 3e10, 1e11, 1.592e11, 1e12):
            ok = [p for p in pts if p[3] >= Rt]
            a = [p for p in ok if p[1] == Ws[0]]
            if not ok:
                out.write("| %.3g | - | 도달 불가 | - |\n" % Rt); continue
            m = min(ok)
            if a:
                a = min(a)
                out.write("| %.3g | %.4g (%.3g) %.3e | %.4g (%.3g, %.3g) %.3e | %+.1f %% |\n" % (Rt, a[0]*1e12, a[2]*1e6, a[3], m[0]*1e12, m[1]*1e6, m[2]*1e6, m[3], (m[0]/a[0]-1)*100))
            else:
                out.write("| %.3g | W_min 도달 불가 | %.4g (%.3g, %.3g) %.3e | - |\n" % (Rt, m[0]*1e12, m[1]*1e6, m[2]*1e6, m[3]))
