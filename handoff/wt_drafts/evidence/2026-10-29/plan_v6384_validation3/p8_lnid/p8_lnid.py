"""검증 3 -- P8 (2) 보간량 ln ID 대 ID 선형 독립 재측정(검증 2 표본과 다른 점). L 0.25·2.0 µm, VGS 0.35·0.55·0.7, VDS 0.5, nfet·pfet.
bin = 그 L 의 PDK 모델 bin W 경계(pm3 파싱), 끝점 = max(a, W_min) 또는 a + 제조 격자 5 nm(계획 v6.38.4 문언), 위 끝 b; 내부 시험점 = 1/w 등분 9점 + w 등분 9점.
오차 = |Δln ID|/(gm/ID)[V]. 출력 p8_lnid.out.jsonl (케이스마다 append)."""
import json, os, re, subprocess, math
import numpy as np
HERE = os.path.dirname(os.path.abspath(__file__)); OUT = os.path.join(HERE, "p8_lnid.out.jsonl"); open(OUT, "w").close()
NG = "C:/ngspice/Spice64/bin/ngspice_con.exe"; WMIN = 0.42; GRID = 0.005
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
    lines = [f"* lnid {kind}", inc, src] + [f"x{i} d g s s sky130_fd_pr__{kind}_01v8 l={L}u w={w}u" for i, w in enumerate(ws)]
    ctl = [".control", "op"] + [f"echo R {i} $&@m.x{i}.msky130_fd_pr__{kind}_01v8[id] $&@m.x{i}.msky130_fd_pr__{kind}_01v8[gm]" for i in range(len(ws))] + ["quit", ".endc", ".end"]
    fn = os.path.join(HERE, f"c_{tag}.cir"); open(fn, "w").write("\n".join(lines + ctl) + "\n")
    o = subprocess.run([NG, "-b", fn], capture_output=True, text=True).stdout
    res = {}
    for l in o.splitlines():
        p = l.split()
        if len(p) == 4 and p[0] == "R": res[int(p[1])] = (abs(float(p[2])), abs(float(p[3])))
    return {w: (res[i][0] / (w * 1e-6), res[i][1] / res[i][0]) for i, w in enumerate(ws) if i in res}
for kind in ("nfet", "pfet"):
    for L in (0.25, 2.0):
        E = edges(kind, L); plan = []; ws = set()
        for a, b in zip(E[:-1], E[1:]):
            if b <= WMIN or b > 7.0: continue
            lo = max(a, WMIN) if (a < WMIN or a == E[0]) else round(a + GRID, 4)
            if lo >= b: continue
            t = sorted(set([round(float(x), 4) for x in 1.0 / np.linspace(1 / lo, 1 / b, 11)[1:-1]] + [round(float(x), 4) for x in np.linspace(lo, b, 11)[1:-1]]))
            plan.append((a, b, lo, t)); ws.update([lo, b] + t)
        ws = sorted(ws)
        for vgs in (0.35, 0.55, 0.7):
            vds = 0.5; d = run(kind, L, vgs, vds, ws, f"{kind}_{L}_{vgs}")
            rows = []
            for a, b, lo, tests in plan:
                x0, x1 = 1 / lo, 1 / b; eln = elin = 0.0
                for w in tests:
                    f = (1 / w - x0) / (x1 - x0)
                    yln = (1 - f) * math.log(d[lo][0]) + f * math.log(d[b][0]); ylin = (1 - f) * d[lo][0] + f * d[b][0]
                    gid = d[w][1]
                    eln = max(eln, abs(yln - math.log(d[w][0])) / gid); elin = max(elin, abs(math.log(ylin) - math.log(d[w][0])) / gid)
                rows.append({"bin": [a, b], "lo": lo, "err_ln_V": eln, "err_lin_V": elin})
            rec = {"kind": kind, "L_um": L, "vgs": vgs, "vds": vds, "n_bins": len(rows), "max_ln_mV": 1e3 * max(r["err_ln_V"] for r in rows),
                   "max_lin_mV": 1e3 * max(r["err_lin_V"] for r in rows), "bins_ln_better": sum(r["err_ln_V"] < r["err_lin_V"] for r in rows), "bins": rows}
            open(OUT, "a", encoding="utf-8").write(json.dumps(rec) + "\n")
            print(kind, L, vgs, "ln %.2f lin %.2f ln_better %d/%d" % (rec["max_ln_mV"], rec["max_lin_mV"], rec["bins_ln_better"], len(rows)), flush=True)
