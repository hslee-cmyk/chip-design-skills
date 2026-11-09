"""검증 2 독립 절점식 -- 계획 v6.38.4 DEC-92 (3) 새 정의(B AC 접지, G_m(inf) = sum gm (h_gate - h_source), h = n 기준 s->inf 전압비,
R_null = 1/G_m(inf))가 전달 분자 최고차 계수 = 0 조건과 같은지 세 구조에서 대조. 출력 p2_nodal.out.jsonl (케이스마다 append).
구조(연결은 library topology.json 그대로, 소자 값은 기호):
 TS  two_stage_ota  : A=O1 -Rz- X -Cc- B=OUT, S={M6}(gate A, source rail), M7 gate bias. 변형: X 기생 Cx, S 셀 Cgd(Cab).
 NM  nmcnr          : M=NodeM2 -Cm1- CM, S2 -Cm2- CM, CM -Rm- B=Vout, M301 gate S2. 변형: CM 기생 Cx, M–S2 직접 결합 Cx12.
 CR  current_reuse  : A=Vop1 -Rz1- X -Cc1- B=Vom, S={M16}(gate A); M15 gate Vg15, Vg15-A 결합(부유 전류원 채널 gf + Cf), Vg15 접지 Cg.
비교: (1) 분자 최고차 계수의 R 근 R_hi, (2) 정의식 R_def = 1/G_m(inf)(h 는 B 접지·gm 무시 용량망 s->inf 극한), 일치 여부.
"""
import json, os
import sympy as sp
HERE = os.path.dirname(os.path.abspath(__file__)); OUT = os.path.join(HERE, "p2_nodal.out.jsonl")
open(OUT, "w").close()
s = sp.symbols('s')


def solve_tf(nodes, eqs, out):
    sol = sp.solve(eqs, nodes, dict=True)[0]
    H = sp.together(sp.simplify(sol[out]))
    num, den = sp.fraction(H)
    return sp.Poly(sp.expand(num), s)


def rec(**k):
    open(OUT, "a", encoding="utf-8").write(json.dumps(k, ensure_ascii=False, default=str) + "\n"); print(json.dumps(k, ensure_ascii=False, default=str), flush=True)


vin = sp.symbols('vin', positive=True)
# ---- TS
gm1, gm6, gA, CA, gL, CL, Cc, R, Cx, Cab = sp.symbols('gm1 gm6 gA CA gL CL Cc R Cx Cab', positive=True)
for tag, cx, cab in (("TS", 0, 0), ("TS+Cx", Cx, 0), ("TS+Cab", 0, Cab)):
    vA, vX, vB = sp.symbols('vA vX vB')
    eqs = [sp.Eq(gm1 * vin, vA * (gA + s * CA) + (vA - vX) / R + s * cab * (vA - vB)),
           sp.Eq((vA - vX) / R, s * Cc * (vX - vB) + s * cx * vX),
           sp.Eq(-gm6 * vA + s * Cc * (vX - vB) + s * cab * (vA - vB), vB * (gL + s * CL))]
    P = solve_tf([vA, vX, vB], eqs, vB)
    lc = sp.factor(P.LC()); Rhi = sp.solve(sp.Eq(lc, 0), R)
    rec(case=tag, num_degree=P.degree(), leading_coeff=lc, R_hi=Rhi, R_def="1/gm6", match=[sp.simplify(r - 1 / gm6) == 0 for r in Rhi],
        num_coeffs=[sp.factor(c) for c in P.all_coeffs()])

# ---- NM
gm2, gm3, g1, C1, g2, CG, Cm1, Cm2, Rm, Cx12 = sp.symbols('gm2 gm3 g1 C1 g2 CG Cm1 Cm2 Rm Cx12', positive=True)
for tag, cx, c12 in (("NM", 0, 0), ("NM+Cx(CM)", Cx, 0), ("NM+Cx12(M-S2)", 0, Cx12)):
    vM, vS, vC, vB = sp.symbols('vM vS vC vB')
    eqs = [sp.Eq(gm1 * vin, vM * (g1 + s * C1) + s * Cm1 * (vM - vC) + s * c12 * (vM - vS)),
           sp.Eq(gm2 * vM, vS * (g2 + s * CG) + s * Cm2 * (vS - vC) + s * c12 * (vS - vM)),
           sp.Eq(s * Cm1 * (vM - vC) + s * Cm2 * (vS - vC), (vC - vB) / Rm + s * cx * vC),
           sp.Eq(-gm3 * vS + (vC - vB) / Rm, vB * (gL + s * CL))]
    P = solve_tf([vM, vS, vC, vB], eqs, vB)
    lc = sp.factor(P.LC()); Rhi = sp.solve(sp.Eq(lc, 0), Rm)
    m, g = sp.symbols('m g')   # 용량망 s->inf: v_CM = 1, B = 0, 노드 M·S2 KCL(용량만)
    hs = sp.solve([sp.Eq(m * C1 + (m - 1) * Cm1 + (m - g) * c12, 0), sp.Eq(g * CG + (g - 1) * Cm2 + (g - m) * c12, 0)], [m, g], dict=True)[0][g]
    Rdef = sp.simplify(1 / (gm3 * hs))
    rec(case=tag, num_degree=P.degree(), leading_coeff=lc, R_hi=Rhi, h_gate=sp.simplify(hs), R_def=Rdef,
        match=[sp.simplify(r - Rdef) == 0 for r in Rhi], R_S="1/gm3")

# ---- CR
gm16, gm15, gf, Cf, Cg, gg = sp.symbols('gm16 gm15 gf Cf Cg gg', positive=True)
vA, vX, vB, vG = sp.symbols('vA vX vB vG')
eqs = [sp.Eq(gm1 * vin, vA * (gA + s * CA) + (vA - vX) / R + (vA - vG) * (gf + s * Cf)),
       sp.Eq((vA - vX) / R, s * Cc * (vX - vB)),
       sp.Eq((vA - vG) * (gf + s * Cf), vG * (gg + s * Cg)),
       sp.Eq(-gm16 * vA - gm15 * vG + s * Cc * (vX - vB), vB * (gL + s * CL))]
P = solve_tf([vA, vX, vB, vG], eqs, vB)
lc = sp.factor(P.LC()); Rhi = sp.solve(sp.Eq(lc, 0), R)
Rdef = 1 / (gm16 + gm15 * Cf / (Cf + Cg))
rec(case="CR", num_degree=P.degree(), leading_coeff=lc, R_hi=Rhi, R_def=sp.simplify(Rdef), match=[sp.simplify(r - Rdef) == 0 for r in Rhi],
    note="상호 용량 모형에서 h = Cf/(Cf+Cg) in [0,1]; SPICE(BSIM) h = -0.027(검증 1 p2_hB0)")
