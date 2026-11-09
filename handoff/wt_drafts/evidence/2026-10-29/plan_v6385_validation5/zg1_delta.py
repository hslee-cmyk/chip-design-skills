"""검증 5 -- Q-ZG1 (δ) 문언대로 구현: C_c(θ) 주어짐 -> R_req = 1/(2π f_low C_c), 격자(W 슬라이스 x L 격자점)에서 R(W,L,VSG) >= R_req 중 W·L 최소
(동률 = R 큰 쪽, 다음 작은 W), 해 없음 = fail-closed. 그 다음 C_c를 상자 [0.1, 10] pF에서 촘촘히 훑어 총면적(MOS + C/밀도) 최소를 구하고
검증 4 zg1_total.txt 'W 자유' 열과 비교. 또 total(C) 계단 크기·국소 최소 수·fail-closed 구간을 잰다.
VSG 축만 보간(로그 gds 선형, 검증 4와 같은 R()), W·L은 격자점만. 밀도 0.002 F/m² = PDK 선언(검증 4 zg1_check.txt (1)).
결과 = zg1_delta.txt"""
import glob, math
import numpy as np
D = "C:/Users/HSLEE/Documents/Todoc/fpga/lut_data/sky130_lut_v2/"
O = "C:/Users/HSLEE/Documents/Todoc/fpga/wt/_drafts/evidence/2026-10-29/plan_v6385_validation5/zg1_delta.txt"
DENS = 0.002
S = {}
for f in sorted(glob.glob(D + "sky130_fd_pr__pfet_01v8__tt__W*um_dc.npz")):
    z = np.load(f, allow_pickle=True)
    S[float(z["W"])] = (np.asarray(z["L"], float), np.abs(np.asarray(z["VGS"], float)), np.abs(np.asarray(z["GDS"], float)))
Ws = sorted(S)


def R(Wk, li, v):
    L, V, G = S[Wk]
    o = np.argsort(V)
    return 1 / float(np.exp(np.interp(v, V[o], np.log(G[li, :, 0, 0][o]))))


def select(v, C, fl):
    rreq = 1 / (2 * math.pi * fl * C)
    cand = []
    for Wk in Ws:
        for i, L in enumerate(S[Wk][0]):
            r = R(Wk, i, v)
            if r >= rreq:
                cand.append((Wk * L, -r, Wk, L, r))
    if not cand:
        return None
    cand.sort()
    return cand[0]


out = open(O, "w", encoding="utf-8")
out.write("grid = %d W x %d L = %d points (pfet)\n" % (len(Ws), len(S[Ws[0]][0]), len(Ws) * len(S[Ws[0]][0])))
Cs = np.exp(np.linspace(math.log(1e-13), math.log(1e-11), 4001))
out.write("\n| 소자(VSG) | f_low | (δ) 총면적 최소 (W, L, C pF) um2 | 검증 4 W 자유 | C=0.1 pF에서 (δ) | fail-closed C 범위 | total(C) 국소 최소 수 | 최대 계단(MOS 면적 점프) um2 | MOS/총 at 최소 |\n|---|---|---|---|---|---|---|---|---|\n")
ref = {("M19/M20", 1e3): 50.08, ("M19/M20", 10.0): 50.18, ("M19/M20", 1.0): 50.32, ("M19/M20", 0.1): 50.84,
       ("M21", 1e3): 50.21, ("M21", 10.0): 52.48, ("M21", 1.0): 73.99, ("M21", 0.1): 320.3}
for name, v in (("M19/M20", 0.204), ("M21", 0.40)):
    for fl in (1e3, 10.0, 1.0, 0.1):
        tot = []
        for C in Cs:
            s = select(v, C, fl)
            tot.append(None if s is None else (s[0] + C / DENS, s[0], s[2], s[3], C))
        ok = [t for t in tot if t is not None]
        fail = [C for C, t in zip(Cs, tot) if t is None]
        best = min(ok)
        # 국소 최소: 유효 연속 구간에서 왼쪽·오른쪽보다 작은 점
        nloc = 0
        for k in range(1, len(tot) - 1):
            if tot[k] and tot[k - 1] and tot[k + 1] and tot[k][0] < tot[k - 1][0] and tot[k][0] <= tot[k + 1][0]:
                nloc += 1
        jumps = [abs(tot[k][1] - tot[k - 1][1]) for k in range(1, len(tot)) if tot[k] and tot[k - 1]]
        s01 = select(v, 1e-13, fl)
        s01s = "fail-closed" if s01 is None else "(%.3g, %.3g) MOS %.3g" % (s01[2] * 1e6, s01[3] * 1e6, s01[1] * 1e12 if False else s01[0] * 1e12)
        fr = "-" if not fail else "%.3g~%.3g pF" % (min(fail) * 1e12, max(fail) * 1e12)
        out.write("| %s(%.3f) | %g | (%.3g, %.3g, %.4g) %.4g | %.4g | %s | %s | %d | %.3g | %.0f %% |\n" % (
            name, v, fl, best[2] * 1e6, best[3] * 1e6, best[4] * 1e12, best[0] * 1e12, ref[(name, fl)], s01s, fr, nloc,
            max(jumps) * 1e12 if jumps else 0, 100 * best[1] / best[0]))
# M21 1 Hz total(C) 곡선 일부(계단 모양)
out.write("\n## M21 VSG 0.40, f_low 1 Hz: total(C) 표본(계단)\n| C pF | 선택 (W, L) | MOS um2 | 총 um2 |\n|---|---|---|---|\n")
for C in np.exp(np.linspace(math.log(0.09e-12 + 0.011e-12), math.log(0.5e-12), 25)):
    s = select(0.40, C, 1.0)
    out.write("| %.4g | %s | %s | %s |\n" % (C * 1e12, "fail" if s is None else "(%.3g, %.3g)" % (s[2] * 1e6, s[3] * 1e6),
                                            "-" if s is None else "%.3g" % (s[0] * 1e12), "-" if s is None else "%.4g" % (s[0] * 1e12 + C / DENS * 1e12)))
out.close()
