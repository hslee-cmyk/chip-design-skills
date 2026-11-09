import json, sys
sys.stdout.reconfigure(encoding='utf-8')
P = json.load(open('pooled_j1b.json'))
def row(key, cls, kind):
    d = P.get("|".join(map(str, key)) + f"|{cls}|{kind}")
    if not d: return None
    n = d['n']
    f = lambda q: "-" if q is None else "/".join(f"{x:.3g}" for x in q)
    return f"n={n} differ={d['n_differ']/n:.1%} >1:{d['n_dln_gt1']/n:.1%} >5:{d['n_dln_gt5']/n:.1%} dev={d['n_dev']} majdev={d['n_dev_majority_differ']} |dlnIDu|{f(d['abs_dlnidu_p50_p90_max'])} |dVGS|{f(d['abs_dvgs_p50_p90_max'])} |dg|{f(d['abs_dgm_id_p50_p90_max'])}"
for idc in ("1e-05",):
  for bud in ("none","full","share"):
    print(f"\n=== K10 ID={idc} bud={bud} tol=t1mV")
    for rule in ("ga","na"):
      for pair in ("D1-D2P","D1-D2","D2P-D2"):
        for cls in ("S","F"):
          for kind in ("n","p"):
            r = row(("K10",rule,pair,"t1mV",idc,bud),cls,kind)
            if r: print(rule,pair,cls,kind,r)
    print(f"--- K3 (na - ga) ID={idc} bud={bud}")
    for vt in ("D1@t1mV","D2P@t1mV","D2"):
        for cls in ("S","F"):
          for kind in ("n","p"):
            r = row(("K3","na-ga",vt,"-",idc,bud),cls,kind)
            if r: print(vt,cls,kind,r)
