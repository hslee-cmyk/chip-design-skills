"""MC metric(σ_in) oracle 1회 비용 실측: 표본 N개 = 표본마다 (파라미터 변경 + reset 재구성 + .op).
sky130 mismatch 변수(*_slope_spectre)는 전역 .param이라 소자별 독립 표본을 만들려면 소자별 사본이 필요하다 --
여기서는 '표본 1개 = alterparam + reset + op' 의 비용만 잰다(표본 값의 통계는 재지 않는다).
결과는 케이스마다 append.
"""
import json
import os
import subprocess
import time

import numpy as np

import z1_toy as z

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "mc_cost.jsonl")
th = {"L1": 5e-7, "L3": 5e-7, "gmid1": 12.0, "gmid3": 10.0, "I": 50e-6, "CL": 1e-12}
h = z.hand(th)

for n in (1, 50, 200):
    for mode in ("reset", "noreset"):
        p = os.path.join(z.TMP, f"mc_{mode}_{n}.cir")
        z.netlist(th, h, p)
        s = open(p).read()
        vals = " ".join(f"{v:.4f}" for v in np.random.default_rng(1).standard_normal(n))
        if mode == "reset":
            body = (f"foreach v {vals}\n alterparam sky130_fd_pr__nfet_01v8__vth0_slope_spectre = $v\n reset\n op\n"
                    f" echo vout $&v(out)\nend\n")
        else:
            body = f"foreach v {vals}\n alter Vcm dc = 0.9\n op\n echo vout $&v(out)\nend\n"
        ctl = ".control\nset noaskquit\n" + body + "quit\n.endc\n"
        s = s[:s.index(".control")] + ctl + ".end\n"
        open(p, "w").write(s)
        t0 = time.perf_counter()
        r = subprocess.run([z.NG, "-b", p], capture_output=True, text=True, timeout=600)
        dt = time.perf_counter() - t0
        nout = r.stdout.count("vout ")
        rec = {"kind": "mc_cost", "mode": mode, "n": n, "t_s": dt, "samples_out": nout}
        with open(OUT, "a", encoding="utf-8") as fo:
            fo.write(json.dumps(rec) + "\n")
        print(rec)
