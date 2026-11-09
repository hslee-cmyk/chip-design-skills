# 검증 41 -- 감사 o200_audit_k10 §0 M1~M3 독립 재현 (LUT v2 r2, resolve_lut_location 로만 위치 결정, 격자 원값, 보간 없음).
# 감사 스크립트(m_o200_k10.py)를 쓰지 않고 따로 짠다. 결과는 항목마다 v41_lut_repro.txt 에 append.
# 추가 판별(감사에 없는 것):
#   R1 ID 열만으로 잰 아문턱 기울기 n_ID = 1/(U_T * dlnID/dVGS)  (마디 0->1, 1->2) -- GM 열과 무관한 독립 n.
#   R2 '게이트 제어' 판별: ID = I_ch + I_leak(VGS 무관) 이면 gm/ID 가 VGS -> 0 에서 plateau 아래로 떨어진다 -> gm/ID(1)/gm/ID(0) 와
#      ID(0)/ID(1) 대 exp(-g*dV) 비교. (감사의 'dlnID/dVGS / (gm/ID)' 는 누설이 섞여도 1 이다 -- 두 양 모두 같은 ID 로 나뉨 -> 판별력 없음 확인)
#   R3 봉인 9 경계 VGS 의 tol_V 십진당 이동(곡선별 차), 닫힌 꼴 n*U_T*ln10 과 비교.
#   R4 nfet gm/ID 단조 감소 여부(마디 0 이 정의역 끝 정점인지), pfet 내부 정점의 상대차(소수 넷째 자리보다 정밀하게).
import json, os, sys, pathlib
import numpy as np
sys.dont_write_bytecode = True
ENG = pathlib.Path(r"C:/Users/HSLEE/Documents/Todoc/fpga/chip-design-skills/skills/analog-gmid-design")
sys.path.insert(0, str(ENG))
from gmid_engine.lut.data_location import resolve_lut_location  # noqa: E402
LOC = resolve_lut_location(str(ENG / "assets/lut_v2_location.json"), os.environ)
HERE = pathlib.Path(__file__).parent
OUT = HERE / "v41_lut_repro.txt"
OUT.write_text("", encoding="utf-8")


def P(*a):
    s = " ".join(str(x) for x in a)
    print(s)
    with open(OUT, "a", encoding="utf-8") as fh:
        fh.write(s + "\n")


def q(a, qs=(0, .1, .5, .9, 1)):
    a = np.asarray(a, float); a = a[np.isfinite(a)]
    return [float(f"{np.quantile(a, x):.6g}") for x in qs] if a.size else None


Z = np.load(LOC.cap_npz_path, allow_pickle=True)
VG, VD = Z["VGS"], Z["VDS"]
T = float(Z["temp_c"]) + 273.15
UT = 1.380649e-23 * T / 1.602176634e-19
dV = VG[1] - VG[0]
P(f"cap_npz = {LOC.cap_npz_path} (sha256 대조 resolve_lut_location 통과), T={T-273.15} C, U_T={UT*1e3:.4f} mV, dVGS={dV} V, VGS[0]={VG[0]}")
di = np.where(VD >= 0.3 - 1e-12)[0]
P("VDS >= 0.3 V 열", len(di), "/", len(VD), "; 분위 [0,.1,.5,.9,1]")
for k, kind in (("n", "nmos"), ("p", "pmos")):
    ID = np.moveaxis(Z["ID_" + k], 1, 3)[:, di]
    GM = np.moveaxis(Z["GM_" + k], 1, 3)[:, di]
    valid = (ID > 0) & (GM > 0)
    g = np.where(valid, GM / np.where(ID > 0, ID, 1), np.nan)
    g0, g1, g2 = g[..., 0], g[..., 1], g[..., 2]
    gmax = np.nanmax(g, -1)
    am = np.nanargmax(np.where(valid, g, -np.inf), -1)
    ok = valid[..., 0] & valid[..., 1] & valid[..., 2]
    P(f"\n== {kind}: curves {ok.size}, 마디 0..2 유효 {int(ok.sum())}")
    P("M1 gm/ID(0)", q(g0[ok]), "| g0/gmax", q((g0 / gmax)[ok]), "| n_eff=1/(U_T g0)", q((1 / (UT * g0))[ok]))
    s01 = (np.log(ID[..., 1]) - np.log(ID[..., 0])) / dV
    s12 = (np.log(ID[..., 2]) - np.log(ID[..., 1])) / dV
    P("R1 n_ID(0->1)=1/(U_T dlnID/dV) [ID 열만]", q((1 / (UT * s01))[ok]), "| n_ID(1->2)", q((1 / (UT * s12))[ok]))
    P("R1 아문턱 기울기 S(0->1) mV/dec", q((np.log(10) / s01 * 1e3)[ok]))
    P("M1 dlnID/dV(0->1) / gm/ID(0) (감사 판별식)", q((s01 / g0)[ok]), "| 사다리꼴 기준 dlnID/dV / ((g0+g1)/2)", q((s01 / (0.5 * (g0 + g1)))[ok]))
    # R2: 누설 혼입 판별 -- gm/ID(1)/gm/ID(0). 순수 지수면 1, VGS 무관 누설이 ID(0) 의 f 만큼 섞이면 g0 = g_ch (1-f) -> g1/g0 > 1.
    P("R2 gm/ID(1)/gm/ID(0)", q((g1 / g0)[ok]), "| gm/ID(2)/gm/ID(0)", q((g2 / g0)[ok]),
      "| g1/g0 > 1+1e-3 곡선 수", int(((g1 / g0) > 1 + 1e-3)[ok].sum()))
    # VDS 별 g0 최소: GIDL·접합 누설이면 높은 VDS 에서 g0 저하
    gv = [float(np.nanmin(np.where(ok, g0, np.nan)[:, j])) for j in range(len(di))]
    P("R2 VDS 열별 min gm/ID(0) (VDS 0.3 / 0.9 / 1.8)", round(gv[0], 3), round(gv[len(di) // 2], 3), round(gv[-1], 3))
    P("M1 정점 = 마디 0 비율", round(float((am == 0)[ok].mean()), 5), f"({int((am == 0)[ok].sum())}/{int(ok.sum())})")
    if k == "n":
        dec = np.all(np.diff(np.where(valid, g, np.nan), axis=-1)[..., :10] <= 0, -1)
        P("R4 nfet gm/ID 마디 0..10 단조 비증가 곡선 비율", round(float(dec[ok].mean()), 5))
    inner = ok & (am > 0)
    if inner.any():
        rel0 = ((gmax - g0) / gmax)[inner]
        P("R4 내부 정점 곡선", int(inner.sum()), "| 정점 VGS", q(VG[am][inner]), "| (gmax-g0)/gmax", q(rel0),
          "| 이것을 float64 eps 배로", q(rel0 / np.finfo(float).eps))
        for off in (-1, 1):
            jj = np.clip(am + off, 0, len(VG) - 1)[..., None]
            rel = ((gmax - np.take_along_axis(g, jj, -1)[..., 0]) / gmax)[inner]
            P(f"R4 정점{off:+d} 마디 상대차", q(rel))
    ioff = ID[..., 0][..., None]
    bvg = {}
    for tol in (1e-4, 1e-3, 1e-2):
        cond = valid & (GM * tol >= ioff)
        fi = np.where(cond.any(-1), np.argmax(cond, -1), -1)
        m = ok & (fi >= 0)
        j = np.maximum(fi, 0)[..., None]
        r = np.take_along_axis(np.log(ID / ioff), j, -1)[..., 0]
        gg = np.take_along_axis(g, j, -1)[..., 0]
        pred = -np.log(gg * tol)
        bvg[tol] = np.where(m, VG[np.maximum(fi, 0)], np.nan)
        P(f"M2 tol_V {tol*1e3:g} mV: 경계 ln(ID/I_off)", q(r[m]), "| 닫힌 꼴", q(pred[m]), "| 경계-닫힌 꼴 (격자 칸 g*dV 단위)",
          q(((r - pred) / (gg * dV))[m]), "| 경계 VGS", q(bvg[tol][m]), "| g_b/gmax", q((gg / gmax)[m]),
          "| 경계>마디0", round(float((fi[m] > 0).mean()), 5), "| 경계 없음", int((ok & (fi < 0)).sum()))
    for a, b in ((1e-4, 1e-3), (1e-3, 1e-2)):
        d = (bvg[a] - bvg[b])[ok]
        P(f"R3 경계 VGS 이동 tol {a*1e3:g}->{b*1e3:g} mV (mV)", q(d * 1e3), "| 닫힌 꼴 n_eff U_T ln10 (mV)", q((np.log(10) / g0 * 1e3)[ok]))
P("done")
