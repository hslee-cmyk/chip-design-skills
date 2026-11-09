"""검증 3 -- 계획 v6.38.4(9c45b431) DEC-92 (3) 새 문언을 문자 그대로 적용해 전달 분자 최고차 계수 근(R_hi)과 대조.
새 문언: n = R의 두 끝 가운데 s->inf에서 B 전위가 되지 않는 끝; h = s->inf 용량망(B AC 접지)에서 신호 주입 노드를 구동 노드로 두고
나머지 노드 KCL로 푼 전압비(v_term / v_n); B로 가는 가지 전류 = R 전류 x 가지 용량 분배 몫; 그것이 G_m(inf)*v_n 과 같아지는 R.
케이스(소자값 기호): TS, TS+Cx(가지 노드), TS-rev(A-C-X-R-B, X 기생), NM(T), NM+Cx(CM), NM+Cx12, CR, CR+Cx.
출력: p2_newdef.out.jsonl (케이스마다 append)."""
import json, os
import sympy as sp
HERE = os.path.dirname(os.path.abspath(__file__)); OUT = os.path.join(HERE, "p2_newdef.out.jsonl"); open(OUT, "w").close()
s = sp.symbols('s'); vin = sp.symbols('vin', positive=True)
def rec(**k):
    line = json.dumps(k, ensure_ascii=False, default=str); open(OUT, "a", encoding="utf-8").write(line + "\n"); print(line, flush=True)
def lead(nodes, eqs, out, Rsym):
    sol = sp.solve(eqs, nodes, dict=True)[0]
    num, den = sp.fraction(sp.together(sp.simplify(sol[out])))
    P = sp.Poly(sp.expand(num), s); lc = sp.factor(P.LC())
    return P.degree(), lc, sp.solve(sp.Eq(lc, 0), Rsym)
def chk(tag, Rhi, Rnew, note=""):
    rec(case=tag, R_hi=Rhi, R_newdef=sp.simplify(Rnew), match=[sp.simplify(r - Rnew) == 0 for r in Rhi], note=note)

gm1, gm6, gA, CA, gL, CL, Cc, R, Cx, Cab = sp.symbols('gm1 gm6 gA CA gL CL Cc R Cx Cab', positive=True)
# TS / TS+Cx : A -R- X -Cc- B
for tag, cx in (("TS", 0), ("TS+Cx", Cx)):
    vA, vX, vB = sp.symbols('vA vX vB')
    eqs = [sp.Eq(gm1*vin, vA*(gA+s*CA) + (vA-vX)/R),
           sp.Eq((vA-vX)/R, s*Cc*(vX-vB) + s*cx*vX),
           sp.Eq(-gm6*vA + s*Cc*(vX-vB), vB*(gL+s*CL))]
    d, lc, Rhi = lead([vA, vX, vB], eqs, vB, R)
    # 새 정의: 주입 노드 A 구동(=n), X 는 s->inf 에서 B 전위(0) -> n = A. h_gate(M6)=1. 가지 몫 = Cc/(Cc+cx)
    share = Cc/(Cc+cx); Rnew = share/(gm6*1)
    chk(tag, Rhi, Rnew)
# TS-rev : A -Cc- X -R- B, X 기생 Cx
vA, vX, vB = sp.symbols('vA vX vB')
eqs = [sp.Eq(gm1*vin, vA*(gA+s*CA) + s*Cc*(vA-vX)),
       sp.Eq(s*Cc*(vA-vX), (vX-vB)/R + s*Cx*vX),
       sp.Eq(-gm6*vA + (vX-vB)/R, vB*(gL+s*CL))]
d, lc, Rhi = lead([vA, vX, vB], eqs, vB, R)
# 새 정의: R 끝 = X, B. X 는 s->inf 에서 A 에 붙음(B 전위 아님) -> n = X. A 구동=1, v_X = Cc/(Cc+Cx). h_gate = vA/vX. 가지 몫 = 1(R 이 B 에 직접)
vXn = Cc/(Cc+Cx); Rnew = vXn/(gm6*1)   # R = v_n/(gm6 * v_gate)
chk("TS-rev(A-C-X-R-B,+Cx)", Rhi, Rnew, note="n=X")

# NM 계열
gm2, gm3, g1, C1, g2, CG, Cm1, Cm2, Rm, Cx12 = sp.symbols('gm2 gm3 g1 C1 g2 CG Cm1 Cm2 Rm Cx12', positive=True)
for tag, cx, c12 in (("NM", 0, 0), ("NM+Cx(CM)", Cx, 0), ("NM+Cx12", 0, Cx12), ("NM+Cx+Cx12", Cx, Cx12)):
    vM, vS, vC, vB = sp.symbols('vM vS vC vB')
    eqs = [sp.Eq(gm1*vin, vM*(g1+s*C1) + s*Cm1*(vM-vC) + s*c12*(vM-vS)),
           sp.Eq(gm2*vM, vS*(g2+s*CG) + s*Cm2*(vS-vC) + s*c12*(vS-vM)),
           sp.Eq(s*Cm1*(vM-vC) + s*Cm2*(vS-vC), (vC-vB)/Rm + s*cx*vC),
           sp.Eq(-gm3*vS + (vC-vB)/Rm, vB*(gL+s*CL))]
    d, lc, Rhi = lead([vM, vS, vC, vB], eqs, vB, Rm)
    # 새 정의: 주입 노드 M 구동(vM=1), CM·S2 용량 KCL, B=0. n = CM. 가지 몫 1(Rm 이 B 직결)
    c, g = sp.symbols('c g')
    sol = sp.solve([sp.Eq(Cm1*(c-1) + Cm2*(c-g) + cx*c, 0), sp.Eq(CG*g + Cm2*(g-c) + c12*(g-1), 0)], [c, g], dict=True)[0]
    Rnew = sol[c]/(gm3*sol[g])
    # 옛 정의(n 구동, M 수동) 비교
    m, g2_ = sp.symbols('m g2_')
    so = sp.solve([sp.Eq(m*C1 + (m-1)*Cm1 + (m-g2_)*c12, 0), sp.Eq(g2_*CG + (g2_-1)*Cm2 + (g2_-m)*c12, 0)], [m, g2_], dict=True)[0]
    Rold = 1/(gm3*so[g2_])
    chk(tag, Rhi, Rnew, note=f"old_def_match={[sp.simplify(r-Rold)==0 for r in Rhi]}")

# CR / CR+Cx : A -Rz1- X -Cc1- B, M16 gate A, M15 gate G(A 결합 gf+Cf, 접지 Cg)
gm16, gm15, gf, Cf, Cg, gg = sp.symbols('gm16 gm15 gf Cf Cg gg', positive=True)
for tag, cx in (("CR", 0), ("CR+Cx", Cx)):
    vA, vX, vB, vG = sp.symbols('vA vX vB vG')
    eqs = [sp.Eq(gm1*vin, vA*(gA+s*CA) + (vA-vX)/R + (vA-vG)*(gf+s*Cf)),
           sp.Eq((vA-vX)/R, s*Cc*(vX-vB) + s*cx*vX),
           sp.Eq((vA-vG)*(gf+s*Cf), vG*(gg+s*Cg)),
           sp.Eq(-gm16*vA - gm15*vG + s*Cc*(vX-vB), vB*(gL+s*CL))]
    d, lc, Rhi = lead([vA, vX, vB, vG], eqs, vB, R)
    h = Cf/(Cf+Cg); share = Cc/(Cc+cx); Rnew = share/(gm16 + gm15*h)
    chk(tag, Rhi, Rnew)
