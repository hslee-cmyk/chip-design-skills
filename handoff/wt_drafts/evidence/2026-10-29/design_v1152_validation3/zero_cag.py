# 검증 3 -- D40:1202 새 문장 '조건 밖이면 R0 = 1/Σ_S gm > R_null, 결과 = 유한 좌반면 영점' 독립 점검
# 모델(current_reuse 출력단 한쪽 꼴, topology 연결 그대로): 노드 A(=Vop1), G(=Vg15), B(=Vom), 보상 가지 중간 X(Rz-Cc).
# M16 nmos gate A drain B (gm1); M15 pmos gate G drain B (gm2); M9b nmos source A drain G gate 교류 접지 (gm9b, gds9);
# M9a pmos source G drain A gate 교류 접지 (gm9a, gds9); M8 전류원 G (gds8); C_AG = A-G 결합(Cds), C_G, C_A, C_L, g_A, g_L.
# 입력 = A에 전류 주입. 출력 v_B. 분자 다항식 근 = 영점. 매개는 무차원 비교 격자(상수 아님).
import sympy as sp, itertools, json, collections
import numpy as np

s = sp.symbols('s')


def zeros(p, R):
    gm1, gm2, gm9a, gm9b, gds9, gds8, gA, gL, CA, CG, CAG, CL, Cc = [p[k] for k in (
        'gm1', 'gm2', 'gm9a', 'gm9b', 'gds9', 'gds8', 'gA', 'gL', 'CA', 'CG', 'CAG', 'CL', 'Cc')]
    vA, vG, vB, vX = sp.symbols('vA vG vB vX')
    i_9b_AtoG = gm9b * vA + gds9 * (vA - vG)   # M9b(nmos, source A, drain G, gate 교류 접지): A->G 전류
    i_9a_GtoA = gm9a * vG + gds9 * (vG - vA)   # M9a(pmos, source G, drain A, gate 교류 접지): G->A 전류
    eqA = gA * vA + s * CA * vA + s * CAG * (vA - vG) + i_9b_AtoG - i_9a_GtoA + (vA - vX) / R - 1
    eqG = gds8 * vG + s * CG * vG + s * CAG * (vG - vA) - i_9b_AtoG + i_9a_GtoA
    eqX = (vX - vA) / R + s * Cc * (vX - vB)
    eqB = gL * vB + s * CL * vB + s * Cc * (vB - vX) + gm1 * vA + gm2 * vG
    sol = sp.solve([eqA, eqG, eqX, eqB], [vA, vG, vB, vX], dict=True)[0]
    num, _ = sp.fraction(sp.together(sol[vB]))
    c = sp.Poly(sp.expand(num), s).all_coeffs()
    c = [float(x) for x in c]
    while c and abs(c[0]) < 1e-12 * max(abs(x) for x in c):
        c = c[1:]
    return [complex(z) for z in np.roots(c)]


base = dict(gm1=1.0, gds9=0.02, gds8=0.02, gA=0.01, gL=0.01, CA=1.0, CL=5.0, Cc=1.0)
rows = []
for r2, r9, rG, hag in itertools.product((0.5, 1, 2), (0.1, 0.3, 1), (0.3, 1, 3), (0.0, 0.05, 0.2, 0.5)):
    p = dict(base, gm2=r2, gm9a=r9, gm9b=r9, CG=rG)
    p['CAG'] = hag * rG / (1 - hag)          # h(inf) = CAG/(CAG + CG) = hag
    Rnull = 1.0 / (p['gm1'] + p['gm2'] * hag)
    R0 = 1.0 / p['gm1']
    z0 = zeros(p, R0)
    zlo = zeros(p, Rnull * 0.999)
    pe = {k: sp.nsimplify(v) for k, v in p.items()}
    zex = zeros(pe, sp.Integer(1) / (pe['gm1'] + pe['gm2'] * sp.nsimplify(hag)))
    rows.append(dict(gm2=r2, gm9=r9, CG=rG, h_inf=hag, R0_over_Rnull=R0 / Rnull,
                     n_zero_R0=len(z0), rhp_R0=sum(z.real > 0 for z in z0), lhp_R0=sum(z.real < 0 for z in z0),
                     n_zero_exact_Rnull=len(zex), rhp_exact_Rnull=sum(z.real > 0 for z in zex),
                     rhp_below_Rnull=sum(z.real > 0 for z in zlo)))
with open('zero_cag.out.jsonl', 'w', encoding='utf-8') as f:
    for r in rows:
        f.write(json.dumps(r) + '\n')
for h in sorted({r['h_inf'] for r in rows}):
    sub = [r for r in rows if r['h_inf'] == h]
    print(json.dumps(dict(h_inf=h, n=len(sub),
                          n_zero_R0=dict(collections.Counter(r['n_zero_R0'] for r in sub)),
                          rhp_R0=dict(collections.Counter(r['rhp_R0'] for r in sub)),
                          n_zero_exact_Rnull=dict(collections.Counter(r['n_zero_exact_Rnull'] for r in sub)),
                          rhp_exact_Rnull=dict(collections.Counter(r['rhp_exact_Rnull'] for r in sub)),
                          rhp_below_Rnull=dict(collections.Counter(r['rhp_below_Rnull'] for r in sub)),
                          R0_over_Rnull=[min(r['R0_over_Rnull'] for r in sub), max(r['R0_over_Rnull'] for r in sub)])))
