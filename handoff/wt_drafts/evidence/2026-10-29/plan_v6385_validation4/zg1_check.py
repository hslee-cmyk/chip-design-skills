"""검증 4 독립 재현 -- Q-ZG1 (마)+(바) 근거 수치.
(1) PDK 선언 mim_cap_density_f_per_m2 를 엔진 read_pdk_decl 로 읽음(작성자 스크립트의 상수 0.002 대조).
(2) zg1_alt.txt 표본 재현(별도 구현: VSG 보간 = log gds 선형, 격자 두 점).
(3) erfc 대표 VSG(0.204·0.40 V)에서 같은 R 의 (W, L) 면적 최소 -- W_min 이 최소/3 % 안인지(L 보간 = log R 대 L, 슬라이스 안, bin 넘음 추정).
(4) f_HP/GBW 표(W_min·L_min, 0.1 pF) -- 'GBW 관문 영역 = VSG 0.6 V급' 문언 대조.
결과 = zg1_check.txt (케이스마다 append)."""
import glob
import math
import sys

import numpy as np

ROOT = "C:/Users/HSLEE/Documents/Todoc/fpga/wt/plan-v6385/skills/analog-gmid-design"
D = "C:/Users/HSLEE/Documents/Todoc/fpga/lut_data/sky130_lut_v2/"
O = "C:/Users/HSLEE/Documents/Todoc/fpga/wt/_drafts/evidence/2026-10-29/plan_v6385_validation4/zg1_check.txt"
open(O, "w", encoding="utf-8").close()


def w(s):
    with open(O, "a", encoding="utf-8") as f:
        f.write(s + "\n")


# (1) PDK
try:
    sys.path.insert(0, ROOT)
    from gmid_engine.core import BoundedLRU, read_pdk_decl
    from pathlib import Path
    d = read_pdk_decl(Path(ROOT) / "assets" / "sky130_pdk_decl.json", BoundedLRU(8))
    dens = d.value("mim_cap_density_f_per_m2")
    w("(1) read_pdk_decl mim_cap_density_f_per_m2 = %r F/m^2 -> 0.1 pF 면적 = %.4g um^2, min_finger_w_m = %r" % (
        dens, 1e-13 / dens * 1e12, d.value("min_finger_w_m")))
except Exception as e:  # 기록만 -- 아래 계산은 계속
    dens = None
    w("(1) read_pdk_decl 실패: %r" % (e,))

S = {}
for f in sorted(glob.glob(D + "sky130_fd_pr__pfet_01v8__tt__W*um_dc.npz")):
    z = np.load(f, allow_pickle=True)
    assert float(z["VDS"][0]) == 0.0 and float(z["VS"][0]) == 0.0
    S[float(z["W"])] = (np.asarray(z["L"], float), np.asarray(z["VGS"], float), np.asarray(z["GDS"], float))
Ws = sorted(S)


def gds(Wk, li, vsg):
    L, V, G = S[Wk]
    V = np.abs(V)
    order = np.argsort(V)
    Vs = V[order]
    g = np.abs(G[li, :, 0, 0])[order]
    return float(np.exp(np.interp(vsg, Vs, np.log(g))))


GBW = 1.37e6
w("\n(2) zg1_alt 재현 (R = 1/gds)")
w("| 소자 | VSG | W um | L um | R Ohm | f_HP@0.1pF/GBW | tau@0.1pF s | MOS um2 |")
w("|---|---|---|---|---|---|---|---|")
for name, v in (("M19/M20", 0.204), ("M21", 0.40)):
    for Wk, li in ((Ws[0], 0), (Ws[-1], -1), (Ws[0], -1)):
        L = S[Wk][0][li]
        R = 1 / gds(Wk, li, v)
        w("| %s | %.3f | %.3g | %.3g | %.4e | %.3e | %.4g | %.3g |" % (name, v, Wk * 1e6, L * 1e6, R, 1 / (2 * math.pi * R * 1e-13) / GBW, R * 1e-13, Wk * L * 1e12))
    # R 최대 W at L max
    li = -1
    best = max(Ws, key=lambda x: 1 / gds(x, li, v))
    w("| %s | R 최대 W at L max = %.3g um |" % (name, best * 1e6))

w("\n(3) 같은 R의 최소 면적 (W, L) -- erfc 대표 VSG; L은 슬라이스마다 log R 대 L 선형 보간(추정)")
w("| VSG | R 목표 | W_min 면적 um2 (L um) | 최소 면적 W um (L um) 면적 um2 | W_min 대비 |")
w("|---|---|---|---|---|")
for v in (0.204, 0.375, 0.40):
    for Rt in (1e7, 1e8, 1e9, 1.592e9, 1e10, 1e11, 1.592e11, 1e12):
        res = []
        for Wk in Ws:
            L = S[Wk][0]
            lr = np.array([math.log(1 / gds(Wk, i, v)) for i in range(len(L))])
            x = math.log(Rt)
            Ln = None
            if x <= lr[0]:
                Ln = None if x < lr[0] else L[0]
            for k in range(len(L) - 1):
                lo, hi = sorted((lr[k], lr[k + 1]))
                if lo <= x <= hi and lr[k + 1] != lr[k]:
                    Ln = L[k] + (x - lr[k]) / (lr[k + 1] - lr[k]) * (L[k + 1] - L[k])
                    break
            if Ln is not None:
                res.append((Wk * Ln, Wk, Ln))
        if not res:
            w("| %.3f | %.3g | 도달 불가 | - | - |" % (v, Rt))
            continue
        a0 = [r for r in res if r[1] == Ws[0]]
        m = min(res)
        if a0:
            w("| %.3f | %.3g | %.4g (%.3g) | %.3g (%.3g) %.4g | %+.1f %% |" % (v, Rt, a0[0][0] * 1e12, a0[0][2] * 1e6, m[1] * 1e6, m[2] * 1e6, m[0] * 1e12, (m[0] / a0[0][0] - 1) * 100))
        else:
            w("| %.3f | %.3g | W_min 도달 불가 | %.3g (%.3g) %.4g | - |" % (v, Rt, m[1] * 1e6, m[2] * 1e6, m[0] * 1e12))

w("\n(4) W_min·L_min, C_BAT 0.1 pF: f_HP/GBW 대 VSG")
for v in (0.204, 0.3, 0.375, 0.40, 0.45, 0.5, 0.6):
    R = 1 / gds(Ws[0], 0, v)
    w("VSG %.3f  R %.3e  f_HP/GBW %.3g" % (v, R, 1 / (2 * math.pi * R * 1e-13) / GBW))
