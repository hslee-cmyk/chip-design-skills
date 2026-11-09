"""Z1 닫기 실측 케이스 구동. 결과는 z1_toy.append로 케이스마다 results.jsonl에 append."""
import numpy as np

import z1_toy as z

BASE = {"L1": 5e-7, "L3": 5e-7, "gmid1": 12.0, "gmid3": 10.0, "I": 50e-6, "CL": 1e-12}

GBW_CASES = []
for cl, spec in ((1e-12, 50e6), (1e-13, 300e6), (3e-14, 600e6)):
    for g in (10.0, 14.0, 20.0):
        GBW_CASES.append((f"gbw_cl{cl:.0e}_g{g:g}", dict(BASE, CL=cl, gmid1=g), spec))

A0_CASES = []
for L in (1.5e-7, 5e-7, 1e-6):
    th = dict(BASE, L1=L, L3=L)
    spec = round(z.hand(dict(th, gmid1=14.0))["A0"], 1)
    A0_CASES.append((f"a0_L{L*1e6:g}u", th, spec))

if __name__ == "__main__":
    for case, th, spec in GBW_CASES:
        for res in (0.01, 0.005):
            for aim in ("zero", "mid", "secant"):
                z.run_closure(case, th, "GBW", spec, res, aim)
    for case, th, spec in A0_CASES:
        for res in (0.01, 0.005):
            for aim in ("zero", "mid", "secant"):
                z.run_closure(case, th, "A0", spec, res, aim)
    # d(x) 곡선 -- 수렴 인자 κ
    z.run_curve("gbw_cl3e-14_g20", dict(BASE, CL=3e-14, gmid1=20.0), "GBW", list(np.geomspace(20e-6, 2000e-6, 9)))
    z.run_curve("gbw_cl3e-14_g10", dict(BASE, CL=3e-14, gmid1=10.0), "GBW", list(np.geomspace(20e-6, 400e-6, 7)))
    z.run_curve("gbw_cl1e-12_g12", dict(BASE, CL=1e-12, gmid1=12.0), "GBW", list(np.geomspace(20e-6, 400e-6, 7)))
    z.run_curve("a0_L0.15u", dict(BASE, L1=1.5e-7, L3=1.5e-7), "A0", [11.0, 13.0, 15.0, 17.0, 19.0, 21.0, 23.0])
    z.run_curve("a0_L1u", dict(BASE, L1=1e-6, L3=1e-6), "A0", [11.0, 13.0, 15.0, 17.0, 19.0, 21.0, 23.0])
