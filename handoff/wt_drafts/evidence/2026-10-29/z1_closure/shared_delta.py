"""Δ 자리 판단용: Δ를 (점별)이 아니라 T-30 Δ_T처럼 (metric별 실행 변형 입력 하나)로 두면 front 점들이 동시에 닫히는가.
같은 회로(같은 CL)의 front 점 3개(gm/ID 10·14·20)에 '가장 어려운 점(g20)이 닫힌 Δ'를 공통으로 줘 oracle 여유를 잰다.
결과 append(shared_delta.jsonl).
"""
import json
import os

import z1_toy as z

HERE = os.path.dirname(os.path.abspath(__file__))
R = [json.loads(l) for l in open(os.path.join(HERE, "results.jsonl"), encoding="utf-8")]
OUT = os.path.join(HERE, "shared_delta.jsonl")
z1 = {r["case"]: r for r in R if r["kind"] == "closure" and r["aim"] == "secant" and r["res_rel"] == 0.01
      and r["metric"] == "GBW"}
for cl in ("1e-12", "1e-13", "3e-14"):
    hard = z1[f"gbw_cl{cl}_g20"]
    delta = hard["hist"][-1]["delta"]
    for g in ("10", "14", "20"):
        r = z1[f"gbw_cl{cl}_g{g}"]
        th = z.solve_gbw(r["theta0"], r["spec"] + delta)
        o = z.oracle(th, z.hand(th), f"shared_{cl}_{g}")
        rec = {"kind": "shared_delta", "cl": cl, "gmid1": g, "delta_rel": delta / r["spec"],
               "s_rel": (o["GBW"] - r["spec"]) / r["spec"], "x": th["I"], "x_z1_own": r["hist"][-1]["x"],
               "x_over_own_rel": th["I"] / r["hist"][-1]["x"] - 1}
        with open(OUT, "a", encoding="utf-8") as fo:
            fo.write(json.dumps(rec) + "\n")
        print(rec)
