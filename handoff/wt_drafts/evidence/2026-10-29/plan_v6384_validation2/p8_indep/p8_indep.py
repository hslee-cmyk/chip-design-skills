"""검증 2 독립 재측정 -- 계획 v6.38.4 P8 (E) '모든 bin 양 끝 슬라이스 + 1/w 선형 보간, 오차 <= 같은 셀 tol_V id_equivalent'.
작성자 p8_density 와 다른 표본: L = 0.15·0.5·1.0·4.0 µm, VGS 0.3(약반전)·0.45·0.6·0.8, VDS 0.9·0.2, kind 2.
보간량 둘: ln IDu(작성자와 같음)와 IDu 자체(계획 문언 'DC 열 1/w 선형 보간'의 다른 읽기). 오차 단위 = |Δln ID|/(gm/ID) [V].
tol_V: 엔진 tol_v_table(기준 폭 슬라이스) 가장 가까운 L 앵커·VDS 셀 id_equivalent. 엔진 import·읽기만.
결과는 케이스마다 append: p8_indep.out.jsonl
"""
import json, os, re, subprocess, sys, math
import numpy as np
HERE = os.path.dirname(os.path.abspath(__file__)); OUT = os.path.join(HERE, "p8_indep.out.jsonl")
NG = "C:/ngspice/Spice64/bin/ngspice_con.exe"
SKILL = "C:/Users/HSLEE/Documents/Todoc/fpga/wt/integ-it12/skills/analog-gmid-design"
WMIN = 0.42


def edges(kind, L):
    t = open(f"C:/pdk/sky130_fd_pr/cells/{kind}_01v8/sky130_fd_pr__{kind}_01v8__tt.pm3.spice", encoding="utf-8", errors="replace").read()
    ws = set()
    for m in re.split(r'\n\.model\s+', t)[1:]:
        g = {k: float(re.search(r'\b' + k + r'\s*=\s*([0-9.eE+-]+)', m).group(1)) for k in ('lmin', 'lmax', 'wmin', 'wmax')}
        if g['lmin'] <= L * 1e-6 < g['lmax']:
            ws.add(round(g['wmin'] * 1e6, 4)); ws.add(round(g['wmax'] * 1e6, 4))
    return sorted(ws)


def run(kind, L, vgs, vds, ws, tag):
    inc = (f'.include "C:/pdk/sky130_fd_pr/models/parameters/lod.spice"\n.include "C:/pdk/sky130_fd_pr/cells/{kind}_01v8/sky130_fd_pr__{kind}_01v8__tt.pm3.spice"\n'
           f'.include "C:/pdk/sky130_fd_pr/cells/{kind}_01v8/sky130_fd_pr__{kind}_01v8__mismatch.corner.spice"\n')
    src = f"vs s 0 1.8\nvg g 0 {1.8 - vgs}\nvd d 0 {1.8 - vds}\n" if kind == "pfet" else f"vs s 0 0\nvg g 0 {vgs}\nvd d 0 {vds}\n"
    lines = [f"* indep {kind}", inc, src] + [f"x{i} d g s s sky130_fd_pr__{kind}_01v8 l={L}u w={w}u" for i, w in enumerate(ws)]
    ctl = [".control", "op"] + [f"echo R {i} $&@m.x{i}.msky130_fd_pr__{kind}_01v8[id] $&@m.x{i}.msky130_fd_pr__{kind}_01v8[gm]" for i in range(len(ws))] + ["quit", ".endc", ".end"]
    fn = os.path.join(HERE, f"c_{tag}.cir"); open(fn, "w").write("\n".join(lines + ctl) + "\n")
    o = subprocess.run([NG, "-b", fn], capture_output=True, text=True).stdout
    res = {}
    for l in o.splitlines():
        p = l.split()
        if len(p) == 4 and p[0] == "R":
            res[int(p[1])] = (abs(float(p[2])), abs(float(p[3])))
    return {w: (res[i][0] / (w * 1e-6), res[i][1] / res[i][0]) for i, w in enumerate(ws) if i in res}


def tol_tables():
    sys.path.insert(0, SKILL); sys.dont_write_bytecode = True
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
        out[kind] = (key, list(t.L_anchors), [float(v) for v in t.vds_grid],
                     [[(None if c.id_equivalent_v is None else float(c.id_equivalent_v)) for c in row] for row in t.cells])
    return out


TT = tol_tables()
open(OUT, "w").close()
for kind, tk in (("nfet", "nmos"), ("pfet", "pmos")):
    key, La, Vg, cells = TT[tk]
    for L in (0.15, 0.5, 1.0, 4.0):
        E = edges(kind, L)
        bins = [(a, b) for a, b in zip(E[:-1], E[1:]) if b <= 7.0 and b > WMIN]
        ws = set()
        plan = []
        for a, b in bins:
            lo = max(a, WMIN) if a < WMIN or (kind == "pfet" and a == E[0]) else round(a + 0.003, 5)
            if lo >= b:
                continue
            tests = sorted(set([round(float(x), 5) for x in 1.0 / np.linspace(1 / lo, 1 / b, 11)[1:-1]] + [round(float(x), 5) for x in np.linspace(lo, b, 11)[1:-1]]))
            plan.append((a, b, lo, tests)); ws.update([lo, b] + tests)
        ws = sorted(ws)
        li = int(np.argmin([abs(x - L * 1e-6) for x in La]))
        for vgs in (0.3, 0.45, 0.6, 0.8):
            for vds in (0.9, 0.2):
                d = run(kind, L, vgs, vds, ws, f"{kind}_{L}_{vgs}_{vds}")
                vi = int(np.argmin([abs(v - vds) for v in Vg])); tol = cells[li][vi]
                rows = []
                for a, b, lo, tests in plan:
                    if lo not in d or b not in d:
                        continue
                    x0, x1 = 1 / lo, 1 / b
                    e_ln, e_lin = 0.0, 0.0
                    for w in tests:
                        if w not in d:
                            continue
                        f = (1 / w - x0) / (x1 - x0)
                        yln = (1 - f) * math.log(d[lo][0]) + f * math.log(d[b][0])
                        ylin = (1 - f) * d[lo][0] + f * d[b][0]
                        gid = d[w][1]
                        e_ln = max(e_ln, abs(yln - math.log(d[w][0])) / gid)
                        e_lin = max(e_lin, abs(math.log(ylin) - math.log(d[w][0])) / gid)
                    rows.append({"bin": [a, b], "lo": lo, "err_ln_V": e_ln, "err_lin_V": e_lin, "end_ratio": d[lo][0] / d[b][0]})
                rec = {"kind": kind, "L_um": L, "L_anchor": La[li], "vgs": vgs, "vds": vds, "tol_vds": Vg[vi], "tolV": tol,
                       "max_err_ln_V": max(r["err_ln_V"] for r in rows), "max_err_lin_V": max(r["err_lin_V"] for r in rows),
                       "worst_bin": max(rows, key=lambda r: r["err_ln_V"])["bin"],
                       "n_bins": len(rows), "n_bins_over_tol_ln": sum(1 for r in rows if tol is not None and r["err_ln_V"] > tol), "bins": rows}
                open(OUT, "a", encoding="utf-8").write(json.dumps(rec) + "\n")
                print(kind, L, vgs, vds, "tol", None if tol is None else round(tol * 1e3, 2), "ln", round(rec["max_err_ln_V"] * 1e3, 2),
                      "lin", round(rec["max_err_lin_V"] * 1e3, 2), rec["worst_bin"], "over", rec["n_bins_over_tol_ln"], flush=True)
