"""검증2 독립 유도: class-AB 출력단 R_null 의 A-G 결합 용량 조건 h(inf).
모델(작성자·검증1 스크립트와 별개로 새로 세움): 노드 A(구동 끝), G(출력 소자 gate 중간 넷), B(출력 끝), X(R-Cc 사이 내부 노드).
- A: 입력 전류 i_in, g_A, C_A
- G: A와 컨덕턴스 g_f(부유 전류원 등가) + 결합 용량 C_AG, 접지로 g_G + C_G
- B: 소자1 gm1 (gate A), 소자2 gm2 (gate G) 전류 싱크, g_B, C_B
- 보상: A -R- X -Cc- B
두 경우: (1) 일반 C_AG, (2) MOS 결합 꼴(소스 팔로워: gate A, source G -> gm_f(vA - vG) + Cgs = C_AG).
출력: 분자 최고차 계수 = 0 이 되는 R.
"""
import json, sys
import sympy as sp

s, R = sp.symbols('s R', positive=True)
gA, CA, gf, CAG, gG, CG, gm1, gm2, gB, CB, Cc = sp.symbols('g_A C_A g_f C_AG g_G C_G gm1 gm2 g_B C_B C_c', positive=True)
vA, vG, vB, vX = sp.symbols('vA vG vB vX')
iin = sp.Symbol('i_in')

def solve(extra_gm_f=0):
    gmf = sp.Symbol('gm_f', positive=True) if extra_gm_f else 0
    eqs = [
        sp.Eq(iin, (gA + s*CA)*vA + (gf + s*CAG)*(vA - vG) + (vA - vX)/R),
        # G: KCL; 소스 팔로워면 gm_f(vA - vG) 가 G 로 들어옴
        sp.Eq(gmf*(vA - vG), (gG + s*CG)*vG + (gf + s*CAG)*(vG - vA)),
        sp.Eq(0, (vX - vA)/R + s*Cc*(vX - vB)),
        sp.Eq(0, gm1*vA + gm2*vG + (gB + s*CB)*vB + s*Cc*(vB - vX)),
    ]
    sol = sp.solve(eqs, [vA, vG, vB, vX], dict=True)[0]
    H = sp.together(sol[vB]/iin)
    num, den = sp.fraction(sp.simplify(H))
    P = sp.Poly(sp.expand(num), s)
    lead = sp.factor(P.coeffs()[0])
    Rn = sp.solve(sp.Eq(lead, 0), R)
    return P.degree(), lead, Rn

out = []
deg, lead, Rn = solve(0)
pred = 1/(gm1 + gm2*CAG/(CAG + CG))
ok = [sp.simplify(r - pred) == 0 for r in Rn]
out.append({'case': 'cap_coupled', 'deg': deg, 'lead': str(lead), 'R_null': [str(sp.simplify(r)) for r in Rn], 'matches_design_formula': ok})
deg0, lead0, Rn0 = deg, lead.subs(CAG, 0), [sp.simplify(r.subs(CAG, 0)) for r in Rn]
out.append({'case': 'cap_coupled_CAG0', 'R_null': [str(r) for r in Rn0], 'equals_1_over_gm1': [sp.simplify(r - 1/gm1) == 0 for r in Rn0]})
deg2, lead2, Rn2 = solve(1)
out.append({'case': 'source_follower_coupled(gm_f + Cgs=C_AG)', 'deg': deg2, 'R_null': [str(sp.simplify(r)) for r in Rn2], 'matches_design_formula': [sp.simplify(r - pred) == 0 for r in Rn2]})
with open(sys.argv[1], 'w', encoding='utf-8') as f:
    for o in out:
        f.write(json.dumps(o, ensure_ascii=False) + '\n')
for o in out:
    print(o)
