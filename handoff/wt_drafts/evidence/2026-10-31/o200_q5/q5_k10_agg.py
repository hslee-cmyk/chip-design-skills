# q5_k10_lut.jsonl 집계 -> q5_k10_agg.txt (변형·규칙·ID·예산별 pool, S/F × nfet/pfet).
import json, pathlib
import numpy as np
HERE = pathlib.Path(__file__).parent
rows = [json.loads(l) for l in (HERE / "q5_k10_lut.jsonl").read_text(encoding="utf-8").splitlines()]
out = []
p = lambda s: out.append(s)
tc = np.array([r["tol_cell_mV"] for r in rows], float)
tr = np.array([r["tol_over_vds"] for r in rows], float)
p(f"소자 {len(rows)} (S {sum(r['cls']=='S' for r in rows)}, F {sum(r['cls']=='F' for r in rows)})")
p(f"설정별 tol 셀값 mV [min,med,p90,max] 소자 분포: min-of-min {tc[:,0].min():.3f}, med-of-med {np.median(tc[:,1]):.3f}, max-of-p90 {tc[:,2].max():.3f}, max-of-max {tc[:,3].max():.3f}")
p(f"tol/VDS(V_part=VDS) : med-of-med {np.median(tr[:,1]):.2e}, max-of-max {tr[:,3].max():.2e}")
keys = sorted(rows[0]["combos"]) if rows else []
allk = sorted({k for r in rows for k in r["combos"]})
for var in ("P2", "D2P"):
    for rule in ("ga", "na"):
        for idc in ("1e-07", "1e-06", "1e-05", "0.0001", "0.001"):
            for b in ("none", "full", "share"):
                k = f"{var}|{rule}|ID{idc}|{b}"
                sel = [(r, r["combos"][k]) for r in rows if k in r["combos"]]
                if not sel:
                    continue
                line = [f"{k:28s} N={len(sel):3d}"]
                for cls in ("S", "F"):
                    for kind in ("n", "p"):
                        ss = [c for r, c in sel if r["cls"] == cls and r["kind"] == kind]
                        if not ss:
                            continue
                        cfg = sum(c["n_cfg"] for c in ss); ne = sum(c["sd_nonempty_noTol"] for c in ss)
                        emp = sum(c["sd_emptied"] for c in ss); bandset = sum(c["n_set_band_nodes"] for c in ss)
                        both = sum(c["ts_both"] for c in ss); dif = sum(c["ts_differ"] for c in ss); lost = sum(c["ts_lost"] for c in ss)
                        ndev = sum(c["ts_differ"] > 0 for c in ss)
                        dmax = max([c["dlnidu"][3] for c in ss if c["dlnidu"]] or [0.0]); vmax = max([c["dvgs"][3] for c in ss if c["dvgs"]] or [0.0])
                        line.append(f"{cls}{kind[0]}(n{len(ss)}): S_d비빔 {ne}/{cfg} 띠설정 {bandset} 비게됨 {emp} t*바뀜 {dif}/{both}(소자 {ndev}) t*잃음 {lost} |dlnIDu|max {dmax:.3f} |dVGS|max {vmax:.4f}")
                p(" | ".join(line))
(HERE / "q5_k10_agg.txt").write_bytes(("\n".join(out) + "\n").encode("utf-8"))
print("\n".join(out[:3])); print(len(out))
