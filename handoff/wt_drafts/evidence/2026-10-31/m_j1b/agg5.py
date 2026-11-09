import json, sys, collections
sys.stdout.reconfigure(encoding='utf-8')
recs = [json.loads(l) for l in open('devices_j1b.jsonl', encoding='utf-8')]
def ts_sig(c):
    t = c['ts']
    return json.dumps([t['lnidu'], t['vgs']])
print("== D2 (ga, none) leak majority by circuit (att, tol t1mV): circuit: S maj/N, F maj/N")
by = collections.defaultdict(lambda: collections.Counter())
for r in recs:
    c = r['combos']["D2|ga|ID1e-05|none"]
    n = c['att']['n']; lk = c['leak_att']['t1mV']
    by[r['circuit']][(r['cls'],'N')] += 1
    if n and lk >= 0.5*n: by[r['circuit']][(r['cls'],'maj')] += 1
for cname, o in sorted(by.items()):
    print(f"{cname:32s} S {o[('S','maj')]}/{o[('S','N')]}  F {o[('F','maj')]}/{o[('F','N')]}  budget={[r['budget_m2'] for r in recs if r['circuit']==cname][0]}")
for idc in ("1e-06","1e-05","0.0001"):
  for bud in ("full","share"):
    print(f"\n== ts signature differs (median/min/max of ln IDu or VGS), ID={idc}, bud={bud}: circuits (devices differ / budget-circuit devices), tol t1mV")
    cmp = [("D1-D2", "D1@t1mV|ga", "D2|ga"), ("D1-D2P", "D1@t1mV|ga", "D2P@t1mV|ga"), ("ga-na[D1]", "D1@t1mV|ga", "D1@t1mV|na"), ("ga-na[D2]", "D2|ga", "D2|na")]
    for name, a, b in cmp:
        o = collections.Counter(); per = collections.defaultdict(lambda: [0,0])
        for r in recs:
            if r['budget_m2'] is None: continue
            ca = r['combos'][f"{a}|ID{idc}|{bud}"]; cb = r['combos'][f"{b}|ID{idc}|{bud}"]
            d = ts_sig(ca) != ts_sig(cb)
            per[r['circuit']][1] += 1
            if d: per[r['circuit']][0] += 1; o[r['cls']] += 1
        print(name, f"S {o['S']}/16 F {o['F']}/32 |", "; ".join(f"{k}:{v[0]}/{v[1]}" for k,v in sorted(per.items()) if v[0]))
print("\n== att->ts median shift (ln IDu), D1@t1mV ga, bud=full, by ID (budget circuits): device median of (ts_med - att_med): S p50/max, F p50/max")
import numpy as np
for idc in ("1e-07","1e-06","1e-05","0.0001","0.001"):
    for cls in ("S","F"):
        v = [r['combos'][f"D1@t1mV|ga|ID{idc}|full"]['ts']['lnidu'][1] - r['combos'][f"D1@t1mV|ga|ID{idc}|full"]['att']['lnidu'][1] for r in recs if r['budget_m2'] and r['cls']==cls]
        print(idc, cls, f"n={len(v)} p50={np.median(v):.2f} p90={np.quantile(v,.9):.2f} max={max(v):.2f}")
print("\n== ts stats (gm/ID, VGS) D1@t1mV ga bud=full ID=1e-5: S/F medians over devices of per-device median")
for cls in ("S","F"):
    gm = [r['combos']["D1@t1mV|ga|ID1e-05|full"]['ts']['gm_id'][1] for r in recs if r['budget_m2'] and r['cls']==cls]
    vg = [r['combos']["D1@t1mV|ga|ID1e-05|full"]['ts']['vgs'][1] for r in recs if r['budget_m2'] and r['cls']==cls]
    w = [r['combos']["D1@t1mV|ga|ID1e-05|full"]['ts']['w_m'][1] for r in recs if r['budget_m2'] and r['cls']==cls]
    print(cls, "gm/ID med", np.median(gm), "VGS med", np.median(vg), "W med", np.median(w))
print("\n== S_d empty configs (sd_nonempty/n_cfg) by ID, D2 none: devices with sd_nonempty==0, and mean fraction")
for idc in ("1e-07","1e-06","1e-05","0.0001","0.001"):
    e = sum(1 for r in recs if r['combos'][f"D2|ga|ID{idc}|none"]['sd_nonempty']==0)
    fr = np.mean([r['combos'][f"D2|ga|ID{idc}|none"]['sd_nonempty']/r['n_cfg'] for r in recs])
    print(idc, "empty devices", e, "mean nonempty fraction", round(fr,3))
