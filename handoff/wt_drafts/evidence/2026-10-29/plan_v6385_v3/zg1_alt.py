"""Q-ZG1 대안 손계산·LUT 실측 (검증 3 MJ3-1).
erfc 대표점: M19·M20 VSG 0.204 V(sky130 .op -- 검증 2 표), M21 VSG 0.40 V. pfet tt W 슬라이스 DC LUT, VDS = 0, VS = 0(bulk = source).
VSG 는 격자 두 점 사이 log gds 선형 보간(격자 0.0375 V). L 은 격자점만(같은 슬라이스) -- (마)의 '필요 L'만 log R 대 L 보간(추정, bin 넘음 표기).
면적: MOS = W·L, C_BAT = C / mim_cap_density(PDK 선언 sky130_pdk_decl.json 'mim_cap_density_f_per_m2' = 0.002 F/m² -- engine read_pdk_decl 값).
f_HP = 1/(2π R C), τ = R·C(DC 정착 시상수), GBW = erfc gbw_ss_hz 1.37 MHz.
결과 = zg1_alt.txt"""
import glob
import math
import numpy as np

D = "C:/Users/HSLEE/Documents/Todoc/fpga/lut_data/sky130_lut_v2/"
O = "C:/Users/HSLEE/Documents/Todoc/fpga/wt/_drafts/evidence/2026-10-29/plan_v6385_v3/zg1_alt.txt"
DENS = 0.002
GBW = 1.37e6
PTS = (("M19/M20", 0.204), ("M21", 0.40))
S = {}
for f in sorted(glob.glob(D + "sky130_fd_pr__pfet_01v8__tt__W*um_dc.npz")):
    d = np.load(f, allow_pickle=True)
    assert d["VDS"][0] == 0 and d["VS"][0] == 0
    S[float(d["W"])] = (d["L"], d["VGS"], d["GDS"])
Ws = sorted(S)


def R(W, li, vsg):
    L, V, G = S[W]
    k = int(np.searchsorted(V, vsg)) - 1
    a, b = math.log(G[li, k, 0, 0]), math.log(G[li, k + 1, 0, 0])
    t = (vsg - V[k]) / (V[k + 1] - V[k])
    return 1.0 / math.exp(a + t * (b - a))


def row(out, tag, name, W, Lm, r, C):
    fhp = 1 / (2 * math.pi * r * C)
    out.write("| %s | %s | %.3g | %.3g | %.3e | %.3g | %.3e | %.3e | %.3e | %.3g | %.3g |\n" % (
        tag, name, W * 1e6, Lm * 1e6, r, C * 1e12, fhp, fhp / GBW, r * C, W * Lm * 1e12, C / DENS * 1e12))


out = open(O, "w", encoding="utf-8")
out.write("source %s (pfet tt, VDS=0, VS=0); W slices um %s; L grid um %s\n\n" % (D, [round(w * 1e6, 3) for w in Ws], [round(x * 1e6, 3) for x in S[Ws[0]][0]]))
out.write("| 안 | 소자 | W um | L um | R Ohm | C_BAT pF | f_HP Hz | f_HP/GBW | tau s | MOS 면적 um2 | C_BAT 면적 um2 |\n|---|---|---|---|---|---|---|---|---|---|---|\n")
W0 = Ws[0]
L0 = S[W0][0]
for name, v in PTS:
    # (가)/(라) 면적 최소 귀결: W_min, L_min, C_BAT 상자 하한 / 상자 상한
    for C in (1e-13, 1e-11):
        row(out, "(가)·(라) 귀결 W_min·L_min", name, W0, L0[0], R(W0, 0, v), C)
    # (사) R 최대 기하: L = 정의역 최대, W = 그 L 에서 R 최대 슬라이스
    li = len(L0) - 1
    best = max(Ws, key=lambda w: R(w, li, v))
    for C in (1e-13, 1e-11):
        row(out, "(사) R 최대(L max, W argmax R)", name, best, S[best][0][li], R(best, li, v), C)
    row(out, "(사) 참고 W_min·L max", name, W0, L0[li], R(W0, li, v), 1e-13)
out.write("\n## (마) 대역 하한 f_low 선언 시 면적 최소 귀결(C_BAT = 상자 하한 0.1 pF, W = W_min, 필요 R = 1/(2π f_low C), L = log R 대 L 보간 -- 추정, bin 넘음). f_low 값은 사용자 몫 -- 아래 둘은 계산 예시일 뿐\n")
out.write("| 소자 | f_low Hz | 필요 R Ohm | 필요 L um | MOS 면적 um2 | tau s |\n|---|---|---|---|---|---|\n")
for name, v in PTS:
    lr = [math.log(R(W0, i, v)) for i in range(len(L0))]
    for fl in (1e3, 10.0):
        Rt = 1 / (2 * math.pi * fl * 1e-13)
        Lneed = None
        for k in range(len(L0) - 1):
            if lr[k] <= math.log(Rt) <= lr[k + 1]:
                t = (math.log(Rt) - lr[k]) / (lr[k + 1] - lr[k])
                Lneed = L0[k] + t * (L0[k + 1] - L0[k])
                break
        if lr[0] >= math.log(Rt):
            Lneed = L0[0]
        if Lneed is None:
            out.write("| %s | %.3g | %.3e | 정의역 밖(도달 불가) | - | - |\n" % (name, fl, Rt))
        else:
            out.write("| %s | %.3g | %.3e | %.3g | %.3g | %.3e |\n" % (name, fl, Rt, Lneed * 1e6, W0 * Lneed * 1e12, Rt * 1e-13))
out.close()
print(open(O, encoding="utf-8").read())
