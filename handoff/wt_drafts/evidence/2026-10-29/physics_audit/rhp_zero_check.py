"""DEC-92 (3)/U-134 영점 식 점검 -- 2단 Miller + 직렬 Rz 소신호 모델(손계산 교과서 꼴).
node1: (G1+sC1)V1 + Y(V1-V2) = -gm1 Vin ; node2: (G2+sCL)V2 + Y(V2-V1) + gm2 V1 = 0, Y = sCc/(1+sRzCc).
영점: Y = gm2 -> z = 1/(Cc(1/gm2 - Rz)) (정확식). 상쇄값 R_c = (1+CL/Cc)/gm2 의 실제 p2 대비 오차를 C1/Cc 별로 잼.
결과 rhp_zero_check.out.jsonl append."""
import json, os
import numpy as np

OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "rhp_zero_check.out.jsonl")


def poles_zero(gm1, gm2, G1, G2, C1, CL, Cc, Rz):
    # 분모 다항식 (s 거듭제곱 내림차순): det of 2x2 times (1+sRzCc)
    # a = (G1+sC1)(1+sRzCc) + sCc ; b = -sCc ; c = gm2(1+sRzCc) - sCc ; d = (G2+sCL)(1+sRzCc) + sCc
    P = np.polynomial.polynomial
    one_r = [1, Rz * Cc]
    a = P.polyadd(P.polymul([G1, C1], one_r), [0, Cc])
    b = [0, -Cc]
    c = P.polysub(P.polymul([gm2], one_r), [0, Cc])
    d = P.polyadd(P.polymul([G2, CL], one_r), [0, Cc])
    den = P.polysub(P.polymul(a, d), P.polymul(b, c))  # 3차: (1+sRzCc) 인자 포함
    roots = P.polyroots(den)
    num_zero = None if abs(1 - gm2 * Rz) < 1e-15 else gm2 / (Cc * (1 - gm2 * Rz))
    return roots, num_zero


if __name__ == "__main__":
    gm2, gm1 = 100e-6, 20e-6
    G1, G2 = 1 / 5e6, 1 / 2e6
    CL, Cc = 3e-12, 1e-12
    for C1_over_Cc in (0.05, 0.2, 0.5, 1.0):
        C1 = C1_over_Cc * Cc
        Rc = (1 + CL / Cc) / gm2
        roots, z = poles_zero(gm1, gm2, G1, G2, C1, CL, Cc, Rc)
        mags = sorted(abs(r) for r in roots)
        # 영점 z(<0 = LHP) 와 가장 가까운 비주극점의 비
        nd = [r for r in roots if abs(r) > 10 * mags[0]]
        nearest = min(nd, key=lambda r: abs(abs(r) - abs(z)))
        rec = {"case": "rhp_zero", "C1_over_Cc": C1_over_Cc, "Rz_cancel_ohm": Rc, "zero_rad_s": z,
               "poles_rad_s": [complex(r).real for r in roots], "zero_over_nearest_pole": abs(z) / abs(nearest),
               "R_at_1_over_gm2": 1 / gm2, "zero_at_R0": -gm2 / Cc}
        with open(OUT, "a", encoding="utf-8") as fh:
            fh.write(json.dumps(rec, default=str) + "\n")
        print(json.dumps(rec, default=str))
