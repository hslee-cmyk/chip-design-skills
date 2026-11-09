"""plan v6.38.4 검증 1 -- P2 독립 절점식(작성자 스크립트 미사용).
케이스:
 G  : 게이트 결합 꼴(S={M}, S 밖 c gate G가 A와 C_AG로 결합) -- 계획 식 R_null = 1/(gm + gm_c*h) 재현
 SRC: 반례 후보 -- S 셀 M(gate=A, drain=B)의 source X가 A와 Cgs로 결합(소스 축퇴, X에 R_deg·C_X)
 CGD: S 셀 자신의 A–B 직접 용량 C_AB(Cgd) -- 어떤 R에서도 우반면 영점이 남는지
 T  : nmcnr Structure 4 T 망(Cm1: v1–cm, Cm2: v2–cm, Rm: cm–vo) -- Rm = 1/gm3에서 최고차 계수 0인지(Leung),
      그리고 보상 망 밖 A–G 직접 용량 Cx(v1–v2)를 더하면 R_null이 어떻게 바뀌는지
출력: out.jsonl (케이스마다 append)
"""
import json, os, sympy as sp
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "out.jsonl")
open(OUT, "w").close()
def rec(d):
    with open(OUT, "a", encoding="utf-8") as f: f.write(json.dumps(d, ensure_ascii=False, default=str) + "\n")
s = sp.symbols('s')

def numer(eqs, unknowns, out):
    sol = sp.solve(eqs, unknowns, dict=True)[0]
    num, den = sp.fraction(sp.together(sp.simplify(sol[out])))
    return sp.Poly(sp.expand(num), s), sp.Poly(sp.expand(den), s)

def zeros_numeric(P, subs):
    c = [complex(sp.N(ci.subs(subs).subs({i:1}))) for ci in P.all_coeffs()]
    # strip leading ~0
    while len(c) > 1 and abs(c[0]) < 1e-60: c = c[1:]
    import numpy as np
    return [complex(z) for z in np.roots(c)] if len(c) > 1 else []

# ---------- G: gate coupling --------------------------------------------------
i, R, Cc, gm, gmc, CAG, CG, GA, CA, GB, CB = sp.symbols('i R Cc gm gmc CAG CG GA CA GB CB', positive=True)
vA, vG, vB, vn = sp.symbols('vA vG vB vn')
eqs = [
  sp.Eq(i, vA*(GA+s*CA) + (vA-vG)*s*CAG + (vA-vn)/R),
  sp.Eq(0, (vG-vA)*s*CAG + vG*s*CG),
  sp.Eq(0, (vn-vA)/R + (vn-vB)*s*Cc),
  sp.Eq(0, vB*(GB+s*CB) + (vB-vn)*s*Cc + gm*vA + gmc*vG),
]
N, D = numer(eqs, [vA, vG, vB, vn], vB)
top = sp.factor(N.all_coeffs()[0])
Rn = sp.solve(sp.Eq(top, 0), R)
pred = (CAG+CG)/(CAG*(gm+gmc)+CG*gm)
rec({"case": "G", "num_top_coeff": str(top), "R_null_solved": [str(sp.simplify(r)) for r in Rn],
     "matches_plan_formula": [bool(sp.simplify(r-pred) == 0) for r in Rn]})

# ---------- SRC: source-coupled S cell ----------------------------------------
Cgs, CX, Gdeg = sp.symbols('Cgs CX Gdeg', positive=True)
vX = sp.symbols('vX')
eqs = [
  sp.Eq(i, vA*(GA+s*CA) + (vA-vX)*s*Cgs + (vA-vn)/R),
  # node X: channel current gm*(vA-vX) flows drain->source into X (NMOS), Cgs to A, CX & Gdeg to ground
  sp.Eq(gm*(vA-vX) + (vA-vX)*s*Cgs, vX*(Gdeg+s*CX)),
  sp.Eq(0, (vn-vA)/R + (vn-vB)*s*Cc),
  sp.Eq(0, vB*(GB+s*CB) + (vB-vn)*s*Cc + gm*(vA-vX)),
]
N, D = numer(eqs, [vA, vX, vB, vn], vB)
top = sp.factor(N.all_coeffs()[0])
Rn = sp.solve(sp.Eq(top, 0), R)
R_S = 1/gm
rec({"case": "SRC", "num_degree": N.degree(), "num_top_coeff": str(top), "R_null_solved": [str(sp.simplify(r)) for r in Rn],
     "R_null_over_R_S": [str(sp.simplify(r/R_S)) for r in Rn]})
# numeric: zeros at R = R_S and R = R_null
vals = {gm: 500e-6, Cgs: 100e-15, CX: 100e-15, Gdeg: 1/2000, GA: 1e-6, CA: 200e-15, GB: 1e-5, CB: 1e-12, Cc: 450e-15}
for lab, Rv in (("R_S=1/gm", 1/500e-6), ("R_null", float(sp.N(Rn[0].subs(vals))) if Rn else None), ("1.2*R_null", 1.2*float(sp.N(Rn[0].subs(vals))) if Rn else None)):
    if Rv is None: continue
    z = zeros_numeric(N, {**vals, R: Rv})
    rec({"case": "SRC", "R": lab, "R_ohm": Rv, "zeros_rad_s": [str(x) for x in z], "n_rhp": sum(1 for x in z if x.real > 0)})

# ---------- CGD: S cell's own C_AB --------------------------------------------
CAB = sp.symbols('CAB', positive=True)
eqs = [
  sp.Eq(i, vA*(GA+s*CA) + (vA-vB)*s*CAB + (vA-vn)/R),
  sp.Eq(0, (vn-vA)/R + (vn-vB)*s*Cc),
  sp.Eq(0, vB*(GB+s*CB) + (vB-vn)*s*Cc + (vB-vA)*s*CAB + gm*vA),
]
N, D = numer(eqs, [vA, vB, vn], vB)
rec({"case": "CGD", "numerator": str(sp.factor(N.as_expr()))})
vals = {gm: 550e-6, CAB: 20e-15, GA: 1e-6, CA: 200e-15, GB: 1e-5, CB: 1e-12, Cc: 450e-15}
for k in (0.5, 1.0, 1.15, 2.0, 5.0):
    z = zeros_numeric(N, {**vals, R: k/550e-6})
    rec({"case": "CGD", "R_over_1_gm": k, "zeros_Hz": [str(x/(2*3.141592653589793)) for x in z], "n_rhp": sum(1 for x in z if x.real > 0)})

# ---------- T: nmcnr structure 4 ----------------------------------------------
g1, C1, G1, gm2, gmd, Cn, gm4, G2, C2, gm3, Go, CL, Cm1, Cm2, Rm, Cx = sp.symbols('g1 C1 G1 gm2 gmd Cn gm4 G2 C2 gm3 Go CL Cm1 Cm2 Rm Cx', positive=True)
v1, vc, v2, vo, vm, vin = sp.symbols('v1 vc v2 vo vm vin')
def tnet(with_cx):
    cx = Cx if with_cx else 0
    eqs = [
      sp.Eq(0, g1*vin + v1*(G1+s*C1) + (v1-vm)*s*Cm1 + (v1-v2)*s*cx),           # stage1 out (current g1*vin pulled)
      sp.Eq(0, -gm2*v1 + vc*(gmd+s*Cn)),                                          # M201 pmos: i into vc = -gm2*v1 -> vc*(gmd)= -gm2 v1 ... sign kept
      sp.Eq(0, gm4*vc + v2*(G2+s*C2) + (v2-vm)*s*Cm2 + (v2-v1)*s*cx),            # M204 sinks gm4*vc from v2
      sp.Eq(0, gm3*v2 + vo*(Go+s*CL) + (vo-vm)/Rm),                               # M301 sinks gm3*v2 from vo
      sp.Eq(0, (vm-v1)*s*Cm1 + (vm-v2)*s*Cm2 + (vm-vo)/Rm),
    ]
    return numer(eqs, [v1, vc, v2, vo, vm], vo)
for wc in (False, True):
    N, D = tnet(wc)
    cs = N.all_coeffs()
    top = sp.factor(cs[0])
    Rn = sp.solve(sp.Eq(top, 0), Rm)
    rec({"case": "T", "with_Cx": wc, "num_degree": N.degree(), "top_coeff": str(top),
         "Rm_null": [str(sp.simplify(r)) for r in Rn]})
