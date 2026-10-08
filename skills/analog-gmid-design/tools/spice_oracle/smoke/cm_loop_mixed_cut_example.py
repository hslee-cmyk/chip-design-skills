# -*- coding: utf-8 -*-
"""섞인 절단 예 7d -- 엔진 `probe_factor` 대 닫힌식 대 ngspice 선형 Middlebrook (metrics CONTRACT 3.17 'ω = 0 섞인 절단', 예 7d).

회로: CS 단 하나. MOS(d=2, g=3, s=0, b=0, gm, gds, cgs = Cg), CL(2-0), Rf(2-3). 노드 3 = gate(용량 전용) -- Rf 의 3 쪽 단자를 떼면
n = 3(용량 전용), x = 4(Rf 만, 전도) 로 섞인 절단이다(공통 모드 루프의 gate 쪽 절단과 같은 모양).
닫힌식(단일 제어원 루프의 되돌림 비): T(s) = gm / (gds + s(CL + Cg + gds·Rf·Cg) + s²·CL·Rf·Cg), T(0) = gm/gds.
사용: python cm_loop_mixed_cut_example.py [--ngspice EXE] -- 결과를 표준 출력에 낸다.
"""
import argparse
import math
import os
import subprocess
import sys
import tempfile

import numpy

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.abspath(os.path.join(HERE, "..", "..", "..")))
sys.path.insert(0, os.path.dirname(HERE))

from gmid_engine.metrics.loop_analysis import analyze_loop  # noqa: E402
from gmid_engine.metrics.loop_cut import cut_circuit  # noqa: E402
from gmid_engine.metrics.mna_build import build_mna  # noqa: E402
from gmid_engine.metrics.mna_solve import solve_responses  # noqa: E402
from gmid_engine.metrics.probe_loop import probe_factor  # noqa: E402
from gmid_engine.metrics.records import Capacitor, LoopCut, MosSmallSignal, Resistor, SmallSignalCircuit  # noqa: E402
from oracle_simulate import ac_measures, loop_gain  # noqa: E402

GM, GDS, CL, CG, RF = 1e-3, 1e-5, 1e-12, 1e-12, 1e5


def closed_form():
    a0, a1, a2 = GDS, CL + CG + GDS * RF * CG, CL * RF * CG
    t = lambda w: GM / (a0 + 1j * w * a1 - w * w * a2)  # noqa: E731
    lo, hi = 1e3, 1e12
    for _ in range(200):
        mid = math.sqrt(lo * hi)
        lo, hi = (mid, hi) if abs(t(mid)) > 1 else (lo, mid)
    wu = math.sqrt(lo * hi)
    return t, wu, 180 + math.degrees(numpy.angle(t(wu)))


def engine():
    mos = MosSmallSignal(d=2, g=3, s=0, b=0, gm=GM, gmb=0.0, gds=GDS, cgs=CG)
    circuit = SmallSignalCircuit((mos,), (Resistor(2, 3, RF),), (Capacitor(2, 0, CL),), ac_ground=(0,))
    cut = cut_circuit(circuit, (LoopCut("resistor", 0, "b"),))
    response = solve_responses((build_mna(cut.circuit, cut.excitations, cut.senses),))[0]
    factor = probe_factor(response, cut.pairs, (1.0,))
    return factor, analyze_loop((factor,)), response


def ngspice(exe):
    lines = ["* example 7d", f"Gm 2 0 3 0 {GM}", f"Gd 2 0 2 0 {GDS}", f"Cgs 3 0 {CG}", f"CL 2 0 {CL}", f"Rf 2 lbx {RF}",
             "Vlb 3 lbx DC 0 AC 1", "Ilb 0 3 DC 0 AC 0"]
    pre = os.path.join(tempfile.mkdtemp(), "ex7d")
    lines += [".control", "set noaskquit", "set wr_singlescale", "ac dec 40 1 1e10", f"wrdata {pre}.v.txt v(lbx) v(3)",
              "alter @vlb[acmag] = 0", "alter @ilb[acmag] = 1", "ac dec 40 1 1e10", f"wrdata {pre}.i.txt i(vlb) v(3)",
              "quit", ".endc", ".end"]
    with open(pre + ".cir", "w", encoding="utf-8") as fh:
        fh.write("\n".join(lines) + "\n")
    subprocess.run([exe, "-b", pre + ".cir"], capture_output=True)
    f, re_, im = loop_gain(pre + ".v.txt", pre + ".i.txt", [1])
    return numpy.asarray(f), numpy.asarray(re_) + 1j * numpy.asarray(im), ac_measures(f, re_, im)


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--ngspice", default="C:/ngspice/Spice64/bin/ngspice_con.exe")
    a = ap.parse_args(argv)
    t, wu, pm = closed_form()
    factor, analysis, response = engine()
    f, tn, measures = ngspice(a.ngspice)
    w = response.omegas
    on_grid = w > 0
    print("closed form : T(0) = %.12g, gain %.9g dB, UGF %.9g Hz, PM %.9g deg" % (GM / GDS, 20 * math.log10(GM / GDS), wu / 2 / math.pi, pm))
    print("engine      : T(0) = %.12g, gain %.9g dB, UGF %.9g Hz, PM %.9g deg" % (
        analysis.dc_value, analysis.gain_db, analysis.ugf_hz, analysis.phase_margin_deg))
    print("engine grid : max |T/T_closed - 1| (omega > 0) = %.3g (%d points)" % (
        numpy.max(abs(factor.samples[on_grid] / t(w[on_grid]) - 1)), int(on_grid.sum())))
    print("ngspice     : gain %.9g dB, UGF %.9g Hz, PM %.9g deg (data-log interpolation, 40 pts/dec)" % (
        measures["dc_gain_db"], measures["ugf_hz"], measures["pm_deg"]))
    print("ngspice vs closed form max |T/T_closed - 1| = %.3g" % numpy.max(abs(tn / t(2 * math.pi * f) - 1)))
    return 0


if __name__ == "__main__":
    sys.exit(main())
