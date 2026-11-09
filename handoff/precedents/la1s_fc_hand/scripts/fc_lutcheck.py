"""LUT 슬라이스 값 대 SPICE 단일 손가락(같은 w_s·L·바이어스) 직접 대조 -- PMOS 좁은 폭 차이 원인 확인."""
import json, os, subprocess, sys
import lutlib as lt
import fc_spice as SP

cases = [("pmos", 0.42e-6, 1.0e-6, 1.353, 1.353, 0.0), ("pmos", 0.42e-6, 1.0e-6, 1.318, 1.318, 0.0),
         ("pmos", 1.0e-6, 1.0e-6, 1.318, 1.318, 0.0), ("pmos", 5.0e-6, 1.0e-6, 1.318, 1.318, 0.0),
         ("nmos", 1.0e-6, 0.5e-6, 0.65, 1.2, 0.186), ("pmos", 0.42e-6, 0.5e-6, 1.1, 0.4, 0.32)]
out = open(sys.argv[1], "w", encoding="utf-8")
for i, (k, w, L, vgs, vds, vs) in enumerate(cases):
    r = lt.dc(k, w, L, vgs, vds, vs)
    cell = SP.CELL[k]
    if k == "pmos":
        net = ["Vs s 0 dc 1.8", "Vg g 0 dc %.6g" % (1.8 - vgs), "Vd d 0 dc %.6g" % (1.8 - vds), "Vb b 0 dc %.6g" % (1.8 + vs)]
        # pmos: VS = |VSB| -> bulk above source
        net[3] = "Vb b 0 dc %.6g" % (1.8 + vs)
    else:
        net = ["Vs s 0 dc %.6g" % vs, "Vg g 0 dc %.6g" % (vs + vgs), "Vd d 0 dc %.6g" % (vs + vds), "Vb b 0 dc 0"]
    # 손가락 기하: LUT 생성 규칙이 쓴 ad/as 를 모르므로 두 경우(기하 없음 / 끝 칸 혼자) 모두
    txt = ["* lutcheck"] + SP.includes() + net + [
        "X1 d g s b sky130_fd_pr__%s l=%.6gu w=%.6gu nf=1" % (cell, L * 1e6, w * 1e6),
        ".control", "op", "print @m.x1.msky130_fd_pr__%s[id] @m.x1.msky130_fd_pr__%s[gm]" % (cell, cell), "quit", ".endc", ".end"]
    res = SP.run("\n".join(txt) + "\n", "../out/lutcheck", "c%d" % i)
    import re
    lg = open("../out/lutcheck/c%d.log" % i, encoding="utf-8").read()
    idv = re.search(r"\[id\]\s*=\s*([-+0-9.eE]+)", lg)
    gmv = re.search(r"\[gm\]\s*=\s*([-+0-9.eE]+)", lg)
    ids = abs(float(idv.group(1))) if idv else float("nan")
    gms = abs(float(gmv.group(1))) if gmv else float("nan")
    out.write("%s w %.2f L %.2f vgs %.3f vds %.3f vs %.3f | LUT ID %.4g gm/ID %.2f | SPICE ID %.4g gm/ID %.2f | ratio %.3f\n" % (
        k, w * 1e6, L * 1e6, vgs, vds, vs, r["ID"], r["gmid"], ids, gms / ids if ids else 0, ids / r["ID"] if r["ID"] else 0))
out.close()
