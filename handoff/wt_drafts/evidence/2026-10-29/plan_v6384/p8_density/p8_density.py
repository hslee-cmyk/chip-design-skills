"""plan v6.38.4 P8 (E) 실측(검증 1 M-2·M-3) -- W 축 bin 안 1/w 선형 보간 오차를 LUT 자기 허용오차와 같은 단위로 재고, 그 오차를 만족하는
bin 안 슬라이스 수를 정한다. 엔진 import·읽기만, ngspice-46 sky130 tt.

허용 기준(상수 발명 없음): 엔진 LUT 운영 허용오차 tol_V의 `id_equivalent_v`(= |ln ID_보간 − ln ID| / (gm/ID) / 2^p, 운영 보간 축
VGS·VDS·VS·L의 leave-one-out -- lut/tolerance.py, 계획 N3.6·DEC-87 '같은 방법'). W 축 보간 오차를 같은 정의
|Δln IDu| / (gm/ID)로 재서(보간 칸 중앙 실측 -- Richardson 환산 불필요) 같은 (kind, L, VDS) 셀의 기준 폭 슬라이스 tol_V id_equivalent와 비교한다.
슬라이스 배치: bin마다 1/w 등간격 n점(n = 2 = 양 끝, 3, 5, 9) -- 등간격 9점 훑기 위에서 1/w 선형 보간, 나머지 점에서 오차.
경계 규약: ngspice는 경계를 아래 bin에 넣으므로 위 bin 아래 끝 표본 = a + 3 nm(검증 1 binsel), 첫 bin은 a.
출력: p8_density.out.jsonl
"""
import json, os, re, subprocess, sys, math
import numpy as np
HERE = os.path.dirname(os.path.abspath(__file__)); OUT = os.path.join(HERE, "p8_density.out.jsonl")
NG = "C:/ngspice/Spice64/bin/ngspice_con.exe"
SKILL = "C:/Users/HSLEE/Documents/Todoc/fpga/wt/integ-it12/skills/analog-gmid-design"


def edges(kind):
    t = open(f"C:/pdk/sky130_fd_pr/cells/{kind}_01v8/sky130_fd_pr__{kind}_01v8__tt.pm3.spice", encoding="utf-8", errors="replace").read()
    ws = set()
    for m in re.split(r'\n\.model\s+', t)[1:]:
        g = {k: float(re.search(r'\b' + k + r'\s*=\s*([0-9.eE+-]+)', m).group(1)) for k in ('lmin', 'lmax', 'wmin', 'wmax')}
        if g['lmin'] <= 0.15e-6 < g['lmax']:
            ws.add(round(g['wmin'] * 1e6, 4)); ws.add(round(g['wmax'] * 1e6, 4))
    return sorted(ws)


def run(kind, vgs, vds, ws, tag):
    inc = (f'.include "C:/pdk/sky130_fd_pr/models/parameters/lod.spice"\n.include "C:/pdk/sky130_fd_pr/cells/{kind}_01v8/sky130_fd_pr__{kind}_01v8__tt.pm3.spice"\n'
           f'.include "C:/pdk/sky130_fd_pr/cells/{kind}_01v8/sky130_fd_pr__{kind}_01v8__mismatch.corner.spice"\n')
    src = f"vs s 0 1.8\nvg g 0 {1.8 - vgs}\nvd d 0 {1.8 - vds}\n" if kind == "pfet" else f"vs s 0 0\nvg g 0 {vgs}\nvd d 0 {vds}\n"
    lines = [f"* density {kind}", inc, src] + [f"x{i} d g s s sky130_fd_pr__{kind}_01v8 l=0.15u w={w}u" for i, w in enumerate(ws)]
    ctl = [".control", "op"] + [f"echo R {i} $&@m.x{i}.msky130_fd_pr__{kind}_01v8[id] $&@m.x{i}.msky130_fd_pr__{kind}_01v8[gm]" for i in range(len(ws))] + ["quit", ".endc", ".end"]
    fn = os.path.join(HERE, f"d_{tag}.cir"); open(fn, "w").write("\n".join(lines + ctl) + "\n")
    o = subprocess.run([NG, "-b", fn], capture_output=True, text=True).stdout
    res = {}
    for l in o.splitlines():
        p = l.split()
        if len(p) == 4 and p[0] == "R":
            res[int(p[1])] = (abs(float(p[2])), abs(float(p[3])))
    return {round(w, 5): (res[i][0] / (w * 1e-6), res[i][1] / res[i][0]) for i, w in enumerate(ws) if i in res}


def tolv_cells():
    """기준 폭 슬라이스 tol_V id_equivalent: (kind) -> {vds: 셀 값} at L 앵커 0.15 µm."""
    sys.path.insert(0, SKILL); sys.path.append("C:/Users/HSLEE/AppData/Roaming/Python/Python314/site-packages")
    sys.dont_write_bytecode = True
    from gmid_engine.core import BoundedLRU, read_pdk_decl
    from gmid_engine.lut import LutMemo, LutSpec, load_lut_set, resolve_lut_location
    from gmid_engine.lut.tolerance import tol_v_table
    loc = resolve_lut_location(os.path.join(SKILL, "assets", "lut_v2_location.json"), os.environ)
    man = json.load(open(loc.manifest_path, encoding="utf-8"))
    kinds = {"nfet_01v8": "nmos", "pfet_01v8": "pmos"}; mins = {}
    for e in man["slices"]:
        mins[kinds[e["device"]]] = min(e["w_um"] * 1e-6, mins.get(kinds[e["device"]], float("inf")))
    pdk = read_pdk_decl(os.path.join(SKILL, "assets", "sky130_pdk_decl.json"), BoundedLRU(16)); q = dict(pdk.quantities)
    spec = LutSpec(float(man.get("manufacturing_grid_m", 5e-9)), tuple(sorted(mins.items())), (("nfet_01v8", "nmos"), ("pfet_01v8", "pmos")),
                   (("nmos", "_n"), ("pmos", "_p")), noise_ef=(("nmos", q["noise_ef_nmos"].value_m), ("pmos", q["noise_ef_pmos"].value_m)))
    lut = load_lut_set(loc.manifest_path, loc.cap_npz_path, spec, pdk_root=loc.pdk_root, verify_midpoints=loc.midpoints_path,
                       noise_npz=loc.noise_path, mismatch_npz=loc.mismatch_path)
    memo = LutMemo(lut, point=1 << 12, curve=1 << 10, root=1 << 12)
    out = {}
    for kind in ("nmos", "pmos"):
        key = round(lut.cap_map[kind].w_ref_m / lut.spec.manufacturing_grid_m)
        t = tol_v_table(memo, kind, key)
        i = int(np.argmin([abs(L - 0.15e-6) for L in t.L_anchors]))
        out[kind] = {"w_key": key, "L": t.L_anchors[i],
                     "cells": {round(float(v), 4): (None if c.id_equivalent_v is None else float(c.id_equivalent_v)) for v, c in zip(t.vds_grid, t.cells[i])}}
    return out


TOL = tolv_cells()
open(OUT, "w").close()
for kind, tk in (("pfet", "pmos"), ("nfet", "nmos")):
    E = edges(kind); Emin = E[0]; bins = [(a, b) for a, b in zip(E[:-1], E[1:]) if b <= 8]
    ws = set()
    for a, b in bins:
        lo = a if a == Emin else round(a + 0.003, 5)
        for x in np.linspace(lo, b, 17):
            ws.add(round(float(x), 5))
        for x in 1.0 / np.linspace(1 / lo, 1 / b, 9):
            ws.add(round(float(x), 5))
    ws = sorted(ws)
    for vgs, vds in ((0.45, 0.9), (0.6, 0.9), (0.8, 0.9), (0.6, 0.2), (1.0, 0.9)):
        d = run(kind, vgs, vds, ws, f"{kind}_{vgs}_{vds}")
        cells = TOL[tk]["cells"]; vk = min(cells, key=lambda v: abs(v - vds)); tol = cells[vk]
        rows = []
        for a, b in bins:
            lo = a if a == Emin else round(a + 0.003, 5)
            test = [w for w in d if lo <= w <= b]
            res = {}
            for n in (2, 3, 5, 9):
                nodes = [round(float(x), 5) for x in 1.0 / np.linspace(1 / lo, 1 / b, n)]
                nodes = [min(d, key=lambda w: abs(w - x)) for x in nodes]
                inv = np.array([1 / w for w in nodes]); y = np.array([math.log(d[w][0]) for w in nodes])
                order = np.argsort(inv); inv, y = inv[order], y[order]
                errs = []
                for w in test:
                    if w in nodes:
                        continue
                    yi = np.interp(1 / w, inv, y)
                    errs.append(abs(yi - math.log(d[w][0])) / d[w][1])        # V 단위(id_equivalent 정의)
                res[n] = max(errs) if errs else 0.0
            need = next((n for n in (2, 3, 5, 9) if tol is not None and res[n] <= tol), None)
            rows.append({"bin": [a, b], "err_v_by_n": res, "need_n": need})
        rec = {"kind": kind, "vgs_abs": vgs, "vds_abs": vds, "tolV_id_equivalent_ref_cell": tol, "tol_cell_vds": vk,
               "ref_w_key": TOL[tk]["w_key"], "L_anchor": TOL[tk]["L"], "bins": rows,
               "max_err_v_n2": max(r["err_v_by_n"][2] for r in rows), "bins_need_more_than_2": sum(1 for r in rows if r["need_n"] != 2),
               "bins_unmet_n9": sum(1 for r in rows if r["need_n"] is None)}
        open(OUT, "a", encoding="utf-8").write(json.dumps(rec) + "\n")
        print(kind, vgs, vds, "tolV", tol, "max_err_n2", rec["max_err_v_n2"], "bins>2", rec["bins_need_more_than_2"], "unmet", rec["bins_unmet_n9"], flush=True)
