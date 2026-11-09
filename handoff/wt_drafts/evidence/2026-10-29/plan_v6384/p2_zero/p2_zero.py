"""plan v6.38.4 P2 실측 -- DEC-92 (3) '한계' 정정의 물리 결정자 재유도(계획 작성자 독립 정식화, sympy 기호).

모델 = current_reuse 출력단 한쪽(topology 연결: A = Vop1 (M16 gate, Rz1 끝), G = Vg15 (M15 gate), M = N_cc_rz1, B = Vom):
  M16 nmos g=A d=B ; M15 pmos g=G d=B ; 부유 전류원 M9a pmos s=G d=A · M9b nmos s=A d=G ; Rz1 A-M ; Cc1 M-B ;
  접지 용량 C_A, C_G, C_B ; A-G 결합 용량 C_AG(선언 커패시터 또는 기생 결합 -- 조건 실험).
전달 = A 노드 전류 주입 -> v_B. 영점 = 분자 다항식 근. R 문턱 = 분자 최고차 계수 부호가 바뀌는 R(= s -> inf 균형).
출력: out.jsonl (케이스마다 append).
"""
import json, os
import sympy as sp

OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "out.jsonl")
s = sp.symbols("s")
g16, g15, g9a, g9b = sp.symbols("g16 g15 g9a g9b", positive=True)
o9, oA, oG, oB = sp.symbols("o9 oA oG oB", positive=True)
CA, CG, CB, Cc, CAG, R = sp.symbols("CA CG CB Cc CAG R", positive=True)
A, G, M, B = 0, 1, 2, 3


def build(cag):
    Y = sp.zeros(4, 4)
    def adm(i, j, y):
        Y[i, i] += y
        if j is not None:
            Y[j, j] += y; Y[i, j] -= y; Y[j, i] -= y
    def vccs(out_node, gm, ctrl):          # 전류 gm*v_ctrl 이 out_node 에서 접지로 나감
        Y[out_node, ctrl] += gm
    def vccs_between(n_from, n_to, gm, ctrl):
        Y[n_from, ctrl] += gm; Y[n_to, ctrl] -= gm
    adm(A, None, oA + s * CA); adm(G, None, oG + s * CG); adm(B, None, oB + s * CB)
    adm(A, G, o9 + s * cag); adm(A, M, 1 / R); adm(M, B, s * Cc)
    vccs_between(G, A, g9a, G)             # M9a(pmos, s=G, gate=교류 접지): s->d 전류 = g9a*vG, G -> A
    vccs_between(G, A, -g9b, A)            # M9b(nmos, d=G, s=A, gate=교류 접지): d->s 전류 = -g9b*vA
    vccs(B, g16, A)                        # M16: g16*vA 가 B 에서 나감
    vccs(B, g15, G)                        # M15(pmos s=vdd): B 로 -g15*vG 들어옴 = B 에서 g15*vG 나감
    J = sp.Matrix([1, 0, 0, 0])
    YB = Y.copy(); YB[:, B] = J
    num = sp.numer(sp.together(YB.det()))
    return sp.Poly(sp.expand(num), s)


def emit(rec):
    with open(OUT, "a", encoding="utf-8") as fh:
        fh.write(json.dumps(rec, ensure_ascii=False, default=str) + "\n")
    print(json.dumps(rec, ensure_ascii=False, default=str)[:400])


if os.path.exists(OUT):
    os.remove(OUT)
for label, cag in (("CAG0", 0), ("CAG", CAG)):
    p = build(cag)
    lc = sp.factor(p.all_coeffs()[0])
    rn = [sp.simplify(r) for r in sp.solve(sp.Eq(lc, 0), R)]
    emit({"case": label, "num_degree": p.degree(), "lead_coeff": str(lc), "R_null": [str(r) for r in rn]})
    if label == "CAG":
        h = CAG / (CAG + CG)
        pred = 1 / (g16 + g15 * h)
        emit({"case": "CAG_check_vs_pred", "R_null_minus_pred": [str(sp.simplify(r - pred)) for r in rn],
              "limits": {"CAG->0": [str(sp.limit(r, CAG, 0)) for r in rn], "CG->0": [str(sp.limit(r, CG, 0)) for r in rn]}})

# 수치 점검: 일반형(AC 구동 Σgm) R = 1/(g16+k g15) 가 우반면 영점을 남기는가, R = 1/g16 은 없애는가 (C_AG = 0)
import itertools, math
p0 = build(0)
cnt = {"R_conn_rhp0": 0, "R_general_rhp_ge1": 0, "n": 0}
for g16v, g15v, CGv in itertools.product((50e-6, 200e-6, 800e-6), (50e-6, 200e-6, 800e-6), (20e-15, 200e-15, 2e-12)):
    base = {g9a: 20e-6, g9b: 20e-6, o9: 1e-7, oA: 1e-6, oG: 1e-6, oB: 2e-6, CA: 100e-15, CG: CGv, CB: 1e-12, Cc: 500e-15}
    k = 20e-6 / (20e-6)                       # 부유 전류원 전달비 근사 gm9b/gm9a
    for rname, Rv in (("conn", 1 / g16v), ("general", 1 / (g16v + k * g15v))):
        sub = dict(base); sub.update({g16: g16v, g15: g15v, R: Rv})
        coeffs = [complex(c) for c in sp.Poly(p0.as_expr().subs(sub), s).all_coeffs()]
        coeffs = [c.real for c in coeffs]
        while coeffs and abs(coeffs[0]) < 1e-300:
            coeffs.pop(0)
        import numpy as np
        roots = np.roots(coeffs) if len(coeffs) > 1 else []
        rhp = sum(1 for r in roots if r.real > 0 and abs(r) < 1e15)
        if rname == "conn" and rhp == 0:
            cnt["R_conn_rhp0"] += 1
        if rname == "general" and rhp >= 1:
            cnt["R_general_rhp_ge1"] += 1
    cnt["n"] += 1
emit({"case": "numeric_sweep_CAG0_Cgd0", **cnt})
