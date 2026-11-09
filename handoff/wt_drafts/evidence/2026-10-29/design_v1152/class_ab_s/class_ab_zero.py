"""design v1.15.2 task C -- S 정의 일반형('AC로 같은 출력 노드를 구동하는 소자' 포함) 물리 판정용 절점식 계산.

모델 = current_reuse 출력단 한쪽(topology 연결 그대로: A=Vop1, G=Vg15, B=Vom, M=N_cc_rz1):
  M16 nmos g=A d=B s=gnd, M15 pmos g=G d=B s=vdd, M9a pmos s=G d=A g=bias, M9b nmos s=A d=G g=bias, M8 pmos d=G(전류원 gds8),
  Rz1: A-M, Cc1: M-B, C_A(A 노드), C_G(G 노드 = M15 Cgg 주항), C_B(부하), Cgd15(G-B), Cgd16(A-B).
입력 = A 로 들어가는 소신호 전류 i_in(첫 단 gm*vin). H(s) = v_B/i_in 의 분자 다항식을 sympy 로 정확히 구해
(1) 분자 최고차 계수 = 0 이 되는 R(영점이 무한대 -- R_null)을 정확식으로,
(2) R = 1/gm16(현행 S={M16}), R = 1/(gm16 + k0 gm15)(일반형, k0 = w->0 결합비)에서 영점 위치를 잰다.
결과는 케이스마다 class_ab_zero.out.jsonl 에 append.
상수 발명 없음: 계수는 무차원 비로 훑고(case_sweep 격자 = 비교용), 실제 값 범위는 LUT 실측(case_lut)으로 따로 잰다.
실행: C:/Python314/python.exe class_ab_zero.py [symbolic] [sweep] [lut]
"""
import json
import os
import sys

import numpy as np
import sympy as sp

OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "class_ab_zero.out.jsonl")
s = sp.symbols("s")
gm16, gm15, gm9a, gm9b, gds16, gds15, gds9a, gds9b, gds8, gA, gL = sp.symbols(
    "gm16 gm15 gm9a gm9b gds16 gds15 gds9a gds9b gds8 gA gL", positive=True)
CA, CG, CB, Cc, Cgd15, Cgd16, R = sp.symbols("CA CG CB Cc Cgd15 Cgd16 R", positive=True)
vA, vG, vB, vM, iin = sp.symbols("vA vG vB vM iin")

i9a = gm9a * vG + gds9a * (vG - vA)          # pmos M9a: source G -> drain A (G 를 떠나 A 로 들어감)
i9b = -gm9b * vA + gds9b * (vG - vA)         # nmos M9b: drain G -> source A (G 를 떠나 A 로 들어감)
eqA = (gA + s * CA) * vA - i9a - i9b + (vA - vM) / R + s * Cgd16 * (vA - vB) - iin
eqG = i9a + i9b + gds8 * vG + s * CG * vG + s * Cgd15 * (vG - vB)
eqM = (vM - vA) / R + s * Cc * (vM - vB)
eqB = ((gm16 * vA + gds16 * vB) + (gm15 * vG + gds15 * vB) + (gL + s * CB) * vB + s * Cc * (vB - vM)
       + s * Cgd15 * (vB - vG) + s * Cgd16 * (vB - vA))
sol = sp.solve([eqA, eqG, eqM, eqB], [vA, vG, vM, vB], dict=True)[0]
H = sp.together(sol[vB] / iin)
num, den = sp.fraction(sp.factor(H))
num = sp.expand(num)
k0 = (gm9b + gds9a + gds9b) / (gm9a + gds9a + gds9b + gds8)   # w->0, v_B = 0 에서 G 절점식이 주는 결합비 dvG/dvA


def emit(rec):
    with open(OUT, "a", encoding="utf-8") as fh:
        fh.write(json.dumps(rec, ensure_ascii=False, default=str) + "\n")
    print(json.dumps(rec, ensure_ascii=False, default=str)[:900])


def case_symbolic():
    sub0 = {Cgd15: 0, Cgd16: 0}
    num0 = sp.Poly(sp.expand(num.subs(sub0)), s)
    c0 = [sp.factor(c) for c in num0.all_coeffs()]
    rnull = sp.solve(sp.Eq(c0[0], 0), R)
    emit({"case": "symbolic_cgd0", "num_degree": num0.degree(), "num_coeffs_desc": [str(c) for c in c0],
          "R_null_exact": [str(sp.simplify(r)) for r in rnull], "k0_def": str(k0)})
    for r in rnull:
        emit({"case": "symbolic_limits", "R_null": str(sp.simplify(r)),
              "limit_CG_to_0": str(sp.simplify(sp.limit(r, CG, 0))),
              "limit_CG_to_inf": str(sp.simplify(sp.limit(r, CG, sp.oo)))})


_SYMS = (gm16, gm15, gm9a, gm9b, gds16, gds15, gds9a, gds9b, gds8, gA, gL, CA, CG, CB, Cc, Cgd15, Cgd16, R)
_COEFF_FNS = [sp.lambdify(_SYMS, c, "math") for c in sp.Poly(num, s).all_coeffs()]


def _zeros(vals, rv):
    args = [float(vals[x]) if x is not R else float(rv) for x in _SYMS]
    cs = [f(*args) for f in _COEFF_FNS]
    while cs and abs(cs[0]) == 0.0:
        cs = cs[1:]
    return [complex(z) for z in np.roots(cs)] if len(cs) > 1 else []


def _rnull(vals):
    e = sp.expand(num.subs(vals))
    deg = sp.Poly(e, s).degree()
    lead_coeff = sp.expand(e).coeff(s, deg)
    rs = [complex(x) for x in sp.solve(sp.Eq(lead_coeff, 0), R)]
    return [x.real for x in rs if abs(x.imag) < 1e-9 * max(1.0, abs(x.real)) and x.real > 0]


def case_sweep(cgd=False):
    g = 1e-3
    for r15 in (0.5, 1.0, 2.0):                 # gm15/gm16
        for f9 in (0.1, 0.3, 1.0):              # gm9a/gm16
            for b9 in (0.5, 1.0, 2.0):          # gm9b/gm9a
                for lam in (0.1, 0.3, 1.0, 3.0, 10.0, 100.0):   # w_G/w_z0
                    vals = {gm16: g, gm15: r15 * g, gm9a: f9 * g, gm9b: b9 * f9 * g,
                            gds16: g / 50, gds15: r15 * g / 50, gds9a: f9 * g / 50, gds9b: b9 * f9 * g / 50,
                            gds8: f9 * g / 50, gA: g / 500, gL: g / 100, CA: 0.1e-12, CB: 2e-12, Cc: 1e-12,
                            Cgd15: 0.0, Cgd16: 0.0}
                    k = float(k0.subs(vals))
                    wz0 = (g + k * r15 * g) / 1e-12
                    gG = float((gm9a + gds9a + gds9b + gds8).subs(vals))
                    vals[CG] = gG / (lam * wz0)
                    if cgd:
                        vals[Cgd15] = 0.1 * float(vals[CG])
                        vals[Cgd16] = 0.1 * float(vals[CG]) / r15
                    rc, rg = 1 / g, 1 / (g + k * r15 * g)
                    # R 를 로그 격자로 훑어 'R-제어 RHP 영점'이 사라지는 문턱 R* 를 잰다(R 가 클 때의 RHP 수 = 기준;
                    # Cgd16 feedthrough RHP 영점 gm16/Cgd16 은 R 와 무관하게 남으므로 기준 수에 포함된다)
                    grid = np.logspace(np.log10(0.05 / g), np.log10(5.0 / g), 401)
                    cnt = [sum(1 for z in _zeros(vals, float(rv)) if z.real > 0) for rv in grid]
                    base_cnt = cnt[-1]
                    rstar = next((float(grid[i]) for i in range(len(grid)) if all(c == base_cnt for c in cnt[i:])), None)
                    out = {"case": "sweep_cgd" if cgd else "sweep", "gm15_over_gm16": r15, "gm9a_over_gm16": f9,
                           "gm9b_over_gm9a": b9, "lambda_wG_over_wz0": lam, "k0": round(k, 4),
                           "R_current_S_x_gm16": rc * g, "R_general_x_gm16": round(rg * g, 4),
                           "R_null_x_gm16": [round(x * g, 4) for x in _rnull(vals)],
                           "R_star_x_gm16(grid 401, 0.05..5)": None if rstar is None else round(rstar * g, 4),
                           "rhp_count_large_R": base_cnt}
                    for name, rv in (("current_S", rc), ("general", rg)):
                        zs = _zeros(vals, rv)
                        out["rhp_" + name] = sum(1 for z in zs if z.real > 0)
                        out["zeros_" + name] = [[float("%.3g" % z.real), float("%.3g" % z.imag)] for z in zs]
                    emit(out)


def case_lut():
    """pfet(M15 kind) fT 와 λ 추정 재료: LUT 기준 폭 표에서 w_T = gm/cgg (sky130 LUT v2 r2, W 5 um, tt 27C)."""
    root = os.environ.get("GMID_LUT_V2_ROOT", "C:/Users/HSLEE/Documents/Todoc/fpga/lut_data/sky130_lut_v2")
    d = np.load(os.path.join(root, "sky130_nfet_pfet_lut_v2_r2.npz"), allow_pickle=True)
    from scipy.interpolate import RegularGridInterpolator as RGI
    Ls, VGS, VDS, VS = d["L"], d["VGS"], d["VDS"], d["VS"]
    for t in ("p", "n"):
        for L in (5e-7, 1e-6):
            i = int(np.argmin(abs(Ls - L)))
            fid = RGI((VGS, VDS, VS), np.log(np.maximum(d["ID_" + t][i], 1e-30)), bounds_error=False, fill_value=None)
            fgm = RGI((VGS, VDS, VS), d["GM_" + t][i], bounds_error=False, fill_value=None)
            fcg = RGI((VGS, VDS, VS), d["CGG_" + t][i], bounds_error=False, fill_value=None)
            for vgs in np.linspace(0.45, 1.2, 16):
                idv = float(np.exp(fid([[vgs, 0.9, 0.0]])[0]))
                gm = float(fgm([[vgs, 0.9, 0.0]])[0])
                cg = float(fcg([[vgs, 0.9, 0.0]])[0])
                if idv <= 0 or cg <= 0:
                    continue
                emit({"case": "lut_fT", "kind": t, "L_um": L * 1e6, "vgs": round(float(vgs), 3), "gm_id": round(gm / idv, 2),
                      "fT_GHz": round(gm / cg / (2 * np.pi) / 1e9, 3)})


if __name__ == "__main__":
    which = sys.argv[1:] or ["symbolic", "sweep"]
    if "symbolic" in which:
        case_symbolic()
    if "sweep" in which:
        case_sweep()
    if "sweep_cgd" in which:
        case_sweep(cgd=True)
    if "lut" in which:
        case_lut()
