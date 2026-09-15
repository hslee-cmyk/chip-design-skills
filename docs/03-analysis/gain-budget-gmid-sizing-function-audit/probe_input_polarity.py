# -*- coding: utf-8 -*-
"""topology.json 넷리스트만으로 저주파 소신호 MNA를 풀어 입력 포트 -> 출력 부호를 잰다.

엔진 코드를 쓰지 않는 독립 계산이다. 소자마다 같은 gm/gds(값 무관, 부호만 본다)를 스탬프하고
레일(vdd, gnd, vss, agnd)과 게이트 전용 바이어스 넷은 교류접지, 여기 포트는 고정 전압으로 둔다.
단일 입력 여기(한 포트 +1 V, 다른 포트 0)와 차동 여기(+0.5/-0.5) 각각에서 출력 노드 전압 부호를 기록한다.
결과는 같은 폴더 probe_input_polarity.result.md에 케이스마다 append한다.
"""
import io
import json
import sys

import numpy as np

LIB = r"C:\Users\HSLEE\Documents\Todoc\fpga\chip-design-skills\skills\analog-gmid-design\assets\library"
OUT = r"C:\Users\HSLEE\AppData\Local\Temp\claude\C--Users-HSLEE-Documents-Todoc-fpga-chip-design-skills\5de35feb-8d61-4121-be1c-8a6ee517b4c3\scratchpad\sf\probe_input_polarity.result.md"
RAILS = {"vdd", "gnd", "vss", "agnd"}
GM, GDS = 1e-3, 1e-5


def solve(netlist, fixed):
    nodes = sorted({t[k] for t in netlist for k in ("drain", "gate", "source")} - set(fixed))
    idx = {n: i for i, n in enumerate(nodes)}
    n = len(nodes)
    G = np.zeros((n, n))
    b = np.zeros(n)

    def v_of(name):
        return ("fixed", fixed[name]) if name in fixed else ("var", idx[name])

    def add(row_node, col_node, val):
        # KCL 행 row_node에 col_node 전압 계수 val
        if row_node in fixed:
            return
        r = idx[row_node]
        kind, c = v_of(col_node)
        if kind == "var":
            G[r, c] += val
        else:
            b[r] -= val * c

    for t in netlist:
        d, g, s = t["drain"], t["gate"], t["source"]
        # nmos/pmos 모두 소신호 id(d->s) = gm*(vg - vs) + gds*(vd - vs)
        for node, sign in ((d, +1), (s, -1)):
            add(node, g, sign * GM)
            add(node, s, -sign * GM)
            add(node, d, sign * GDS)
            add(node, s, -sign * GDS)
    x = np.linalg.solve(G, b)
    return {nn: x[i] for nn, i in idx.items()}


def run(name, inp_p, inp_n, out_node, extra_fixed=()):
    d = json.load(open(LIB + "\\" + name + ".topology.json", encoding="utf-8"))
    net = d["netlist"]
    gate_only = {t["gate"] for t in net} - {t[k] for t in net for k in ("drain", "source")}
    lines = [f"\n## {name}\n", f"- 출력 노드: `{out_node}`, ports: {json.dumps({k: v.get('role') for k, v in d.get('ports', {}).items() if isinstance(v, dict)}, ensure_ascii=False)}\n"]
    cases = [("vin_p 단독 +1 V", {inp_p: 1.0, inp_n: 0.0}), ("vin_n 단독 +1 V", {inp_p: 0.0, inp_n: 1.0}),
             ("차동 vin_p=+0.5, vin_n=-0.5", {inp_p: 0.5, inp_n: -0.5})]
    for label, exc in cases:
        fixed = {r: 0.0 for r in RAILS}
        fixed.update({g: 0.0 for g in gate_only})
        fixed.update(exc)
        for f in extra_fixed:
            fixed[f] = 0.0
        v = solve(net, fixed)
        vo = v[out_node]
        lines.append(f"- {label}: v({out_node}) = {vo:+.4g} -> {'비반전(+)' if vo > 0 else '반전(-)'}\n")
    io.open(OUT, "a", encoding="utf-8").write("".join(lines))
    sys.stdout.write("".join(lines))


io.open(OUT, "a", encoding="utf-8").write("# 입력 극성 독립 MNA 측정 (gm=1mS, gds=10uS 균일, 부호만 판정)\n")
run("two_stage_ota", "vin_p", "vin_n", "OUT")
run("two_stage_ota_sf", "vin_p", "vin_n", "vout")
run("sf_pushpull_output_opamp", "vin_p", "vin_n", "vout")
