"""독립 검증(design v1.15.2 §3.5 'S 일반형 판정') -- 작성자 스크립트와 별개 정식화.

current_reuse 출력단 한쪽(topology 연결 읽기: A=Vop1, G=Vg15, M=N_cc_rz1, B=Vom):
  M16 nmos g=A d=B s=gnd ; M15 pmos g=G d=B s=vdd ; M9a pmos s=G d=A ; M9b nmos s=A d=G ; M8 pmos d=G ;
  Rz1 A-M ; Cc1 M-B ; C_A, C_G, C_B 접지 용량.
정식화 = 노드 어드미턴스 행렬 Y(s) v = J (J = A 노드 전류 주입), v_B/i = Cramer 분자 det(Y_B) / det(Y).
추가 실험: A-G 용량 결합 C_AG(중간 gate 넷이 A와 용량으로 이어진 경우 -- 일반형 주장 조건 확인).
결과는 케이스마다 out.jsonl 에 append.
"""
import json
import os

import sympy as sp

OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "out.jsonl")
s = sp.symbols("s")
g16, g15, g9a, g9b, o16, o15, o9a, o9b, o8, gA, gL = sp.symbols("g16 g15 g9a g9b o16 o15 o9a o9b o8 gA gL", positive=True)
CA, CG, CB, Cc, CAG, R = sp.symbols("CA CG CB Cc CAG R", positive=True)


def emit(rec):
    with open(OUT, "a", encoding="utf-8") as fh:
        fh.write(json.dumps(rec, ensure_ascii=False, default=str) + "\n")
    print(json.dumps(rec, ensure_ascii=False, default=str)[:600])


# 노드 순서 A, G, M, B. 각 행 = 그 노드에서 '나가는' 전류의 계수(KCL: Y v = 주입).
# M9a pmos (s=G, d=A): 채널 전류 G->A = g9a*(vG - vgate=0) + o9a*(vG - vA)
# M9b nmos (d=G, s=A): 채널 전류 G->A = -g9b*(vA) ... nmos 전류 d->s = g9b*(vg - vs) + o9b*(vd - vs) = -g9b*vA + o9b*(vG - vA)
# M16 nmos (d=B, s=0): d->s = g16*vA + o16*vB ; M15 pmos (s=vdd, d=B): s->d 전류(B로 들어감) = g15*(0 - vG) + o15*(0 - vB)
Y = sp.zeros(4, 4)
A_, G_, M_, B_ = 0, 1, 2, 3
def add_adm(i, j, y):
    Y[i, i] += y
    if j is not None:
        Y[j, j] += y
        Y[i, j] -= y
        Y[j, i] -= y
def add_vccs(n_from, n_to, gm, ctrl):  # 전류 gm*v_ctrl 이 n_from 에서 나가 n_to 로 (None = 접지)
    if n_from is not None:
        Y[n_from, ctrl] += gm
    if n_to is not None:
        Y[n_to, ctrl] -= gm

add_adm(A_, None, gA + s * CA)
add_adm(G_, None, o8 + s * CG)
add_adm(B_, None, gL + s * CB + o16 + o15)
add_adm(A_, G_, o9a + o9b + s * CAG)
add_adm(A_, M_, 1 / R)
add_adm(M_, B_, s * Cc)
add_vccs(G_, A_, g9a, G_)     # M9a: g9a*vG, G -> A
add_vccs(G_, A_, -g9b, A_)    # M9b: -g9b*vA, G -> A
add_vccs(B_, None, g16, A_)   # M16: g16*vA 가 B 에서 나감
add_vccs(B_, None, g15, G_)   # M15: B 로 -g15*vG 들어옴 = B 에서 g15*vG 나감
J = sp.Matrix([1, 0, 0, 0])
YB = Y.copy()
YB[:, B_] = J
num = sp.expand(sp.together(YB.det() * R))  # R 분모 제거
numP = sp.Poly(sp.numer(sp.together(num)), s)


def lead_and_rnull(subs):
    p = sp.Poly(sp.expand(sp.numer(sp.together(num.subs(subs)))), s)
    lc = sp.factor(p.all_coeffs()[0])
    return p.degree(), lc, sp.solve(sp.Eq(lc, 0), R)


def main():
    deg, lc, rn = lead_and_rnull({CAG: 0})
    emit({"case": "indep_symbolic_CAG0", "num_degree": deg, "lead_coeff": str(lc), "R_null": [str(sp.simplify(r)) for r in rn]})
    deg, lc, rn = lead_and_rnull({})
    emit({"case": "indep_symbolic_CAG", "num_degree": deg, "lead_coeff": str(lc), "R_null": [str(sp.simplify(r)) for r in rn]})
    # 수치: 같은 무차원 격자에서 R=1/g16 과 R=1/(g16+k0 g15) 의 RHP 영점 수 (C_AG = 0), 그리고 C_AG = C_G 일 때 문턱
    import numpy as np
    g = 1e-3
    tot = {"cur_rhp0": 0, "gen_rhp1": 0, "n": 0}
    cag_rows = []
    f = sp.lambdify((g16, g15, g9a, g9b, o16, o15, o9a, o9b, o8, gA, gL, CA, CG, CB, Cc, CAG, R),
                    sp.Poly(sp.expand(sp.numer(sp.together(num))), s).all_coeffs(), "math")
    for r15 in (0.5, 1.0, 2.0):
        for f9 in (0.1, 0.3, 1.0):
            for b9 in (0.5, 1.0, 2.0):
                for lam in (0.1, 0.3, 1.0, 3.0, 10.0, 100.0):
                    v = dict(g16=g, g15=r15 * g, g9a=f9 * g, g9b=b9 * f9 * g, o16=g / 50, o15=r15 * g / 50, o9a=f9 * g / 50,
                             o9b=b9 * f9 * g / 50, o8=f9 * g / 50, gA=g / 500, gL=g / 100, CA=0.1e-12, CB=2e-12, Cc=1e-12)
                    k0 = (v["g9b"] + v["o9a"] + v["o9b"]) / (v["g9a"] + v["o9a"] + v["o9b"] + v["o8"])
                    wz0 = (g + k0 * r15 * g) / 1e-12
                    gG = v["g9a"] + v["o9a"] + v["o9b"] + v["o8"]
                    v["CG"] = gG / (lam * wz0)

                    def rhp(rv, cag):
                        cs = f(*(list(v[k] for k in ("g16", "g15", "g9a", "g9b", "o16", "o15", "o9a", "o9b", "o8", "gA", "gL", "CA", "CG", "CB", "Cc")) + [cag, rv]))
                        while cs and abs(cs[0]) < 1e-300:
                            cs = cs[1:]
                        return sum(1 for z in np.roots(cs) if z.real > 0) if len(cs) > 1 else 0
                    tot["n"] += 1
                    tot["cur_rhp0"] += int(rhp(1 / g, 0.0) == 0)
                    tot["gen_rhp1"] += int(rhp(1 / (g + k0 * r15 * g), 0.0) >= 1)
                    if lam in (1.0, 10.0) and f9 == 0.3 and b9 == 1.0:
                        cag = v["CG"]  # A-G 결합 용량 = C_G (가정 실험)
                        grid = np.logspace(np.log10(0.05 / g), np.log10(5.0 / g), 801)
                        cnt = [rhp(float(x), cag) for x in grid]
                        rstar = next((float(grid[i]) for i in range(len(grid)) if all(c == 0 for c in cnt[i:])), None)
                        h_inf = cag / (cag + v["CG"])
                        cag_rows.append({"gm15/gm16": r15, "lambda": lam, "CAG/CG": 1.0,
                                         "R_star_x_gm16": None if rstar is None else round(rstar * g, 4),
                                         "pred_1/(gm16+gm15*h_inf)_x_gm16": round(g / (g + r15 * g * h_inf), 4),
                                         "rhp_at_R=1/gm16": rhp(1 / g, cag)})
    emit({"case": "indep_sweep_162", **tot})
    for row in cag_rows:
        emit({"case": "indep_CAG_threshold", **row})


if __name__ == "__main__":
    main()
