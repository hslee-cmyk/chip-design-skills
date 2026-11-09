# -*- coding: utf-8 -*-
"""셀별 tol_V와 그 셀 목표의 gm/ID로 finger_w_crit = MFG/(2 tol_V gm/ID)를 구해
PDK 최소 폭(bins.csv의 최소 W)과 비교한다. 지표 3가지(raw / branch 점프제외 / id_equiv) 각각.
실행: python tol_v_wcrit.py [targets.npz]"""
import csv
import os
import re
import sys

sys.dont_write_bytecode = True
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
TG = sys.argv[1] if len(sys.argv) > 1 else os.path.join(HERE, "out", "sky130_nfet_pfet_lut_sample.targets.npz")
TLEF = r"C:/pdk/sky130_fd_sc_hd/tech/sky130_fd_sc_hd.tlef"
BINS = {0: r"C:/pdk/sky130_fd_pr/cells/nfet_01v8/sky130_fd_pr__nfet_01v8.bins.csv",
        1: r"C:/pdk/sky130_fd_pr/cells/pfet_01v8/sky130_fd_pr__pfet_01v8.bins.csv"}
OUT = os.path.join(os.path.dirname(TG), "wcrit.txt")
open(OUT, "w", encoding="utf-8").close()


def emit(*p):
    s = " ".join(str(x) for x in p)
    print(s, flush=True)
    with open(OUT, "a", encoding="utf-8") as f:
        f.write(s + "\n")


mfg = float(re.search(r"MANUFACTURINGGRID\s+([0-9.eE+-]+)", open(TLEF, encoding="utf-8", errors="replace").read()).group(1))
wmin = {k: min(float(r["W"]) for r in csv.DictReader(open(p))) for k, p in BINS.items()}
emit("MFG=%g um, PDK bins 최소 W: nmos %.3g um, pmos %.3g um" % (mfg, wmin[0], wmin[1]))
t = np.load(TG)["targets"]
kind, iL, iV, g = t[:, 0].astype(int), t[:, 1].astype(int), t[:, 2].astype(int), t[:, 5]
for col, name in ((8, "raw"), (11, "branch"), (9, "id_equiv")):
    e = t[:, col]
    ok = ~np.isnan(e)
    cells = {}
    for n in np.flatnonzero(ok):
        key = (kind[n], iL[n], iV[n])
        c = cells.setdefault(key, [0.0, []])
        c[0] = max(c[0], e[n])
        c[1].append(g[n])
    rows = []
    for (k, l, v), (tv, gs) in cells.items():
        gs = np.array(gs)
        # 셀 안 각 목표 gm/ID에서의 crit; 셀 최댓값(가장 작은 gm/ID에서)
        crit = mfg / (2 * tv * gs)
        rows.append((k, crit.max(), (crit > wmin[k]).mean(), tv, gs.min()))
    rows = np.array(rows)
    for k in (0, 1):
        r = rows[rows[:, 0] == k]
        if len(r) == 0:
            continue
        nbad = (r[:, 1] > wmin[k]).sum()
        emit("[%s] %s: 셀 %d개 중 finger_w_crit > 최소W 인 셀 %d개; crit 최댓값 %.3g um (tol_V=%.2f mV, gm/ID_min=%.2f);"
             " 그런 셀 안에서 모순 목표 비율 평균 %.4f"
             % (name, "nmos" if k == 0 else "pmos", len(r), nbad, r[:, 1].max(),
                r[np.argmax(r[:, 1]), 3] * 1e3, r[np.argmax(r[:, 1]), 4],
                (r[r[:, 1] > wmin[k], 2].mean() if nbad else 0.0)))
    # 사이징 쓰는 gm/ID 하한별: 이 gm/ID 이상 목표만 볼 때 crit 최댓값
    for gmin in (1, 2, 3, 4, 5):
        m = ok & (g >= gmin)
        cmax = {}
        for n in np.flatnonzero(m):
            key = (kind[n], iL[n], iV[n])
            cmax[key] = max(cmax.get(key, 0), e[n])
        crit_worst = max(mfg / (2 * cells[key][0] * gmin) for key in cmax)
        emit("   [%s] gm/ID >= %g 만: crit 최댓값(셀 tol_V 최소 x gm/ID=%g) = %.3g um" % (name, gmin, gmin, crit_worst))
