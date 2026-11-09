"""(c) e_m 가드 대 Z1 닫기 비교 (같은 toy). results.jsonl의 closure 기록을 읽고 가드 점만 새로 oracle로 잰다.

e_m 정의(DEC-72 꼴): (회로, metric)마다 |손계산 − oracle| 최대값, 측정점 = 같은 회로의 front 점들(여기서는 Δ = 0 첫 풀이 점).
'회로' = 같은 CL(부하가 spec이므로 CL이 다르면 다른 회로로 본다), front 점 = gm/ID 10·14·20 세 점.
가드: 엔진 판정 여유 > e_m  →  손계산 목표 = spec + e_m.  그 점을 oracle로 재서 여유 s°와 전류(전력)를 Z1 닫힌 점과 비교.
결과는 케이스마다 append.
"""
import json
import os
from collections import defaultdict

import z1_toy as z

HERE = os.path.dirname(os.path.abspath(__file__))
R = [json.loads(l) for l in open(os.path.join(HERE, "results.jsonl"), encoding="utf-8")]
OUT = os.path.join(HERE, "guard_vs_z1.jsonl")

# Z1 닫힌 점: secant, res 1 %
z1 = {(r["case"], r["metric"]): r for r in R if r["kind"] == "closure" and r["aim"] == "secant" and r["res_rel"] == 0.01}
groups = defaultdict(list)
for (case, metric), r in z1.items():
    key = (metric, case.split("_g")[0] if metric == "GBW" else case)  # A0: L마다 spec이 달라 회로 하나 = 점 하나
    groups[key].append(r)

for (metric, circ), rs in groups.items():
    h0 = [x["hist"][0] for x in rs]
    em = max(abs(x["hand"] - x["oracle"]) for x in h0)          # 원 단위
    for r in rs:
        spec = r["spec"]
        th = z.SOLVERS[metric](r["theta0"], spec + em)
        h = z.hand(th)
        o = z.oracle(th, h, f"guard_{r['case']}")
        last = r["hist"][-1]
        rec = {"kind": "guard_vs_z1", "metric": metric, "circuit": circ, "case": r["case"], "spec": spec,
               "e_m_rel": em / spec, "guard_oracle_s_rel": (o[metric] - spec) / spec,
               "guard_pass": o[metric] >= spec, "guard_x": th[z.XVAR[metric]],
               "z1_status": r["status"], "z1_oracle_runs": r["oracle_runs"], "z1_s_rel": last["s_rel"],
               "z1_x": last["x"], "x0": r["hist"][0]["x"],
               "guard_vs_z1_x_rel": (th[z.XVAR[metric]] - last["x"]) / last["x"],
               "z1_PM_deg": last["PM_deg"], "guard_PM_deg": o["PM_deg"], "t_s": o["t_s"]}
        with open(OUT, "a", encoding="utf-8") as fo:
            fo.write(json.dumps(rec, ensure_ascii=False) + "\n")
        print(f"{r['case']:22s} e_m {em/spec*100:6.2f}%  guard s° {rec['guard_oracle_s_rel']*100:7.2f}% "
              f"pass={rec['guard_pass']}  x_guard/x_z1-1 {rec['guard_vs_z1_x_rel']*100:7.2f}%  "
              f"z1 runs {r['oracle_runs']} s° {last['s_rel']*100:.2f}%  x0 {rec['x0']:.4g} x_z1 {last['x']:.4g}")
