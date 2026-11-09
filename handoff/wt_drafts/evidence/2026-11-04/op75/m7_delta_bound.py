# C-4 δ 유도 검증(시뮬레이터 호출 0). 결과 m7.jsonl
# 파일 값 v = V/√Hz, d 자리 반올림: |ln(v_r/v)| ≤ -ln(1-u), u = 0.5·10^(1-d) (m ∈ [1,10) 이라 상대 반 단위 ≤ u)
# S = v²: 점마다 |δ ln S| ≤ u_S = -2 ln(1-u)
# n̂ - n̂_앞 = -(ln S_N - ln S_{N-1})/Δ_N + (ln S_{N-1} - ln S_{N-2})/Δ_{N-1}
# 세 점 계수 절대값 합 = 1/Δ_N + (1/Δ_N + 1/Δ_{N-1}) + 1/Δ_{N-1} = 2(1/Δ_N + 1/Δ_{N-1})
# δ = 2 u_S (1/Δ_N + 1/Δ_{N-1}). 등간격이면 4 u_S/Δ ≈ 8u/Δ.  8 = 2(제곱) × 4(둘째 차분 계수 합 1+2+1)
import json, math, os
import numpy as np
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "m7.jsonl")
open(OUT, "w").close()


def w(o):
    with open(OUT, "a", encoding="utf-8") as f:
        f.write(json.dumps(o, ensure_ascii=False) + "\n")


def rs(x, d):
    return np.array([float(f"{v:.{d - 1}e}") for v in x])


rng = np.random.default_rng(0)
for d in (5, 7, 9):
    u = 0.5 * 10 ** (1 - d)
    us = -2 * math.log(1 - u)
    # (1) 임의 값: 참 값은 정확한 멱함수(참 둘째 차분 0), 반올림만 남김. 관측 최대 / 한계 ≤ 1 이어야 함
    for name, r2 in (("equal", 1.0), ("last_short", 0.37)):
        worst = 0.0
        for _ in range(200000):
            v0 = 10 ** rng.uniform(-9, -6)
            dl = 10 ** rng.uniform(-3, 0)
            dln = dl * r2
            f = np.array([1.0, math.exp(dl), math.exp(dl + dln)])
            v = v0 * f ** (-1.0)                       # S ∝ f^-2
            s = rs(v, d) ** 2
            g1 = -(math.log(s[1]) - math.log(s[0])) / dl
            g2 = -(math.log(s[2]) - math.log(s[1])) / dln
            delta = 2 * us * (1 / dln + 1 / dl)
            worst = max(worst, abs(g2 - g1) / delta)
        w({"kind": "random", "digits": d, "grid": name, "max_ratio_to_bound": worst})
    # (2) 한계가 실제로 닿는 꼴: 세 점 오차 부호 (+,-,+) 를 직접 넣음 -> 비 = 1 이어야 함(8 이 과하지 않음)
    dl = 0.1
    ln_s_err = np.array([us, -us, us])
    s = ln_s_err                                       # 참 ln S = 0 (평탄), 오차만
    g1 = -(s[1] - s[0]) / dl
    g2 = -(s[2] - s[1]) / dl
    w({"kind": "worst_case_sign", "digits": d, "ratio_to_bound": abs(g2 - g1) / (2 * us * (2 / dl)),
       "bound_over_8u_per_delta": (2 * us * (2 / dl)) / (8 * u / dl)})
