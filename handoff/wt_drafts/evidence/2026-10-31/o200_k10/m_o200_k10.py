# O-200 K10 물리 측정 (읽기 전용; LUT v2 r2 격자 원값, 보간 없음). 결과는 항목마다 m_o200_k10.jsonl 에 append, 요약은 m_o200_k10.txt.
# M1 VGS=0 마디의 물리: gm/ID(0) 대 곡선 최댓값, n_eff = 1/(U_T gm/ID(0)) (약반전 채널 전류면 1~2 범위), VGS-|VTH| (BSIM VTH 열),
#    차분 d lnID/dVGS 대 gm/ID(0) (I_off 가 게이트가 제어하는 채널 지수 전류인지).
# M2 전도 여유 행(봉인 9 식 I_off <= (gm/ID) tol_V ID)이 S_d 를 자르는 경계: 그 경계 마디의 ln(ID/I_off), VGS, VGS-|VTH| -- tol_V 0.1 / 1 / 10 mV.
#    닫힌 꼴 기대: ln(ID/I_off) = -ln((gm/ID) tol_V)  => tol_V 십진 한 칸마다 ln 2.30 (VGS ~ n U_T ln10) 이동.
# M3 gm/ID 정점(argmax) 위치와 plateau 평탄도.
# M4 정보: EKV IC(VGS=0) -- IC 경계값(예: IC=1)을 고르는 순간 상수라 하한 후보로는 쓰지 않음, 분포만.
import json, pathlib, numpy as np
ENG = pathlib.Path(r"C:/Users/HSLEE/Documents/Todoc/fpga/chip-design-skills/skills/analog-gmid-design")
LOC = json.loads((ENG / "assets/lut_v2_location.json").read_text(encoding="utf-8"))
Z = np.load(pathlib.Path(LOC["root"]["default"]) / LOC["files"]["cap_npz"]["path"], allow_pickle=True)
LG, VG, VD, VS = Z["L"], Z["VGS"], Z["VDS"], Z["VS"]
T = float(Z["temp_c"]) + 273.15
UT = 1.380649e-23 * T / 1.602176634e-19
HERE = pathlib.Path(__file__).parent
out = open(HERE / "m_o200_k10.jsonl", "w", encoding="utf-8")
rep = open(HERE / "m_o200_k10.txt", "w", encoding="utf-8")


def P(*a):
    s = " ".join(str(x) for x in a)
    print(s)
    rep.write(s + "\n")
    rep.flush()


def q(a, qs=(0, .1, .5, .9, 1)):
    a = np.asarray(a, float)
    a = a[np.isfinite(a)]
    return [round(float(np.quantile(a, x)), 4) for x in qs] if a.size else None


P(f"LUT r2 temp {T-273.15} C, U_T = {UT*1e3:.3f} mV, VGS grid step {VG[1]-VG[0]} V, VDS>=0.3 V columns only; quantiles [0,.1,.5,.9,1]")
di = np.where(VD >= 0.3 - 1e-12)[0]
for k, kind in (("n", "nmos"), ("p", "pmos")):
    ID = np.moveaxis(Z["ID_" + k], 1, 3)[:, di]
    GM = np.moveaxis(Z["GM_" + k], 1, 3)[:, di]
    VTH = np.abs(np.moveaxis(Z["VTH_" + k], 1, 3)[:, di])
    valid = (ID > 0) & (GM > 0)
    g = np.where(valid, GM / np.where(ID > 0, ID, 1), np.nan)
    g0 = g[..., 0]
    gmax = np.nanmax(g, axis=-1)
    am = np.argmax(np.where(valid, g, -np.inf), axis=-1)
    ok = valid[..., 0]
    P(f"\n== {kind} curves {ok.size}, VGS=0 node valid {int(ok.sum())}")
    neff = 1.0 / (UT * g0)
    P("M1 gm/ID(VGS=0)", q(g0[ok]), "| g0/gmax", q((g0 / gmax)[ok]))
    P("M1 n_eff(VGS=0)=1/(U_T gm/ID)", q(neff[ok]), "| VGS-|VTH| at VGS=0 (V)", q((0 - VTH[..., 0])[ok]))
    P("M1 peak node == VGS 0 fraction", round(float((am == 0)[ok].mean()), 4))
    sl = (np.log(np.where(ID[..., 1] > 0, ID[..., 1], np.nan)) - np.log(np.where(ID[..., 0] > 0, ID[..., 0], np.nan))) / (VG[1] - VG[0])
    P("M1 finite-diff dlnID/dVGS(node0-1) / gm/ID(0)", q((sl / g0)[ok & valid[..., 1]]))
    ioff = ID[..., 0][..., None]
    for tol in (1e-4, 1e-3, 1e-2):
        cond = valid & (GM * tol >= ioff)
        fi = np.where(cond.any(-1), np.argmax(cond, -1), -1)
        m = ok & (fi >= 0)
        j = np.maximum(fi, 0)[..., None]
        r = np.take_along_axis(np.log(np.where(ID > 0, ID, np.nan) / ioff), j, -1)[..., 0]
        vg = VG[np.maximum(fi, 0)]
        vth = np.take_along_axis(VTH, j, -1)[..., 0]
        gg = np.take_along_axis(g, j, -1)[..., 0]
        pred = -np.log(gg * tol)
        P(f"M2 tol_V {tol*1e3:g} mV: boundary ln(ID/I_off)", q(r[m]), "| closed -ln(gm/ID*tol)", q(pred[m]),
          "| VGS", q(vg[m]), "| VGS-|VTH|", q((vg - vth)[m]), "| gm/ID at boundary / gmax", q((gg / gmax)[m]),
          "| frac cut (boundary>node0)", round(float((fi[m] > 0).mean()), 4), "| no-boundary curves", int((ok & (fi < 0)).sum()))
        out.write(json.dumps(dict(kind=kind, item="M2", tol_V=tol, lnratio=q(r[m]), closed=q(pred[m]), vgs=q(vg[m]), vov=q((vg - vth)[m]),
                                  g_over_gmax=q((gg / gmax)[m]), frac_cut=float((fi[m] > 0).mean()))) + "\n")
        out.flush()
    inner = ok & (am > 0)
    P("M3 interior peak (am>0) fraction", round(float(inner.mean()), 4), "| peak VGS", q(VG[am][inner]) if inner.any() else None)
    for off in (-2, -1, 1, 2):
        jj = np.clip(am + off, 0, len(VG) - 1)[..., None]
        rel = (gmax - np.take_along_axis(g, jj, -1)[..., 0]) / gmax
        P(f"M3 peak{off:+d} node rel diff (gmax-g)/gmax [am>0]", q(rel[inner]) if inner.any() else None)
    P("M3 node0 rel diff (gmax-g0)/gmax [am>0]", q(((gmax - g0) / gmax)[inner]) if inner.any() else None)
    n = 1.0 / (UT * gmax)
    qq = g0 * n * UT
    IC = (1 / qq - 0.5) ** 2 - 0.25
    P("M4 info EKV IC(VGS=0), n=1/(U_T max gm/ID)", q(IC[ok]), "| n", q(n[ok]))
    out.write(json.dumps(dict(kind=kind, item="M1M3M4", g0=q(g0[ok]), g0_over_gmax=q((g0 / gmax)[ok]), neff0=q(neff[ok]),
                              peak_at0=float((am == 0)[ok].mean()), IC0=q(IC[ok]))) + "\n")
    out.flush()
P("done")
