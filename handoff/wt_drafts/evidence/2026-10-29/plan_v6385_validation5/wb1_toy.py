"""검증 5 -- WB-1 완료 (5) toy 기대값 ln(1 + r)/(gm/ID)가 LUT 소자에서 얼마나 맞는가.
차동쌍 + 전류 거울, 출력 = 봉인점 값 고정이면 두 입력 소자 전류 = I/2 그대로(꼬리·거울 고정), 그래서 W′ = (1 + r)·W 소자는
I_u(VGS0 − Δ) = I_u(VGS0)/(1 + r) 인 Δ만큼 VGS가 줄고 V_id = Δ (같은 소스 넷, 같은 VSB). 정확 Δ = LUT ln ID(VGS) 역산(같은 슬라이스·L·VDS·VS)
대 1차 ln(1 + r)/(gm/ID)(점의 gm/ID). 단위 폭 전류 I_u는 W에 비례한다고 둔다(같은 슬라이스 -- r ≪ bin 폭). 결과 = wb1_toy.txt"""
import glob
import numpy as np
D = "C:/Users/HSLEE/Documents/Todoc/fpga/lut_data/sky130_lut_v2/"
O = "C:/Users/HSLEE/Documents/Todoc/fpga/wt/_drafts/evidence/2026-10-29/plan_v6385_validation5/wb1_toy.txt"
out = open(O, "w", encoding="utf-8")
out.write("| 소자 | L um | VDS | gm/ID 목표 | VGS0 | gm/ID(점) | r | 정확 Δ mV | ln(1+r)/(gm/ID) mV | 차 mV | r/(gm/ID) mV |\n|---|---|---|---|---|---|---|---|---|---|---|\n")
for kind, fn in (("nfet", "sky130_fd_pr__nfet_01v8__tt__W1um_dc.npz"), ("pfet", "sky130_fd_pr__pfet_01v8__tt__W1um_dc.npz")):
    f = glob.glob(D + fn.replace("W1um", "W1*um"))[0]
    z = np.load(f, allow_pickle=True)
    Ls = np.asarray(z["L"], float); V = np.abs(np.asarray(z["VGS"], float)); VD = np.abs(np.asarray(z["VDS"], float))
    ID = np.abs(np.asarray(z["ID"], float))
    o = np.argsort(V); V = V[o]
    for li in (int(np.argmin(abs(Ls - 1e-6))), int(np.argmin(abs(Ls - 0.5e-6)))):
        kd = int(np.argmin(abs(VD - 0.6)))
        lnI = np.log(np.maximum(ID[li, :, kd, 0][o], 1e-30))
        vf = np.linspace(V[0], V[-1], 200001)
        lf = np.interp(vf, V, lnI)
        gmid = np.gradient(lf, vf)
        for g in (25.0, 20.0, 15.0, 10.0):
            ok = np.where((gmid <= g) & (vf > 0.05))[0]
            if len(ok) == 0:
                continue
            k = ok[0]
            v0 = vf[k]; g0 = gmid[k]
            for r in (0.01, 0.1, 0.37):
                tgt = lf[k] - np.log(1 + r)
                j = np.searchsorted(lf, tgt)
                d = v0 - vf[j]
                a = np.log(1 + r) / g0
                out.write("| %s | %.3g | %.2f | %g | %.4f | %.2f | %g | %.3f | %.3f | %+.3f | %.3f |\n" % (
                    kind, Ls[li] * 1e6, VD[kd], g, v0, g0, r, d * 1e3, a * 1e3, (a - d) * 1e3, r / g0 * 1e3))
out.close()
