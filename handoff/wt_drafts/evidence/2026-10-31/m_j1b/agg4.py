import json, sys
sys.stdout.reconfigure(encoding='utf-8')
P = json.load(open('pooled_j1b.json'))
IDS = ["1e-07","1e-06","1e-05","0.0001","0.001"]
def g(key,cls,kind):
    return P.get("|".join(map(str,key))+f"|{cls}|{kind}")
print("K10 D1-D2 (ga) differ% / p90 |dlnIDu| / max by ID, tol=t1mV")
for bud in ("none","full","share"):
  for cls in ("S","F"):
    for kind in ("n","p"):
      cells=[]
      for i in IDS:
        d=g(("K10","ga","D1-D2","t1mV",i,bud),cls,kind)
        cells.append(f"{d['n_differ']/d['n']:.1%}/{d['abs_dlnidu_p50_p90_max'][1]:.2g}/{d['abs_dlnidu_p50_p90_max'][2]:.2g}")
      print(bud,cls,kind," | ".join(cells))
print("K10 D1-D2P (ga)  pfet F max over IDs / tols")
for t in ("t0p1mV","t1mV","tLOO"):
  for bud in ("none","full"):
    for cls in ("S","F"):
      for kind in ("n","p"):
        cells=[]
        for i in IDS:
          d=g(("K10","ga","D1-D2P",t,i,bud),cls,kind)
          cells.append(f"{d['n_differ']/d['n']:.2%}/{d['abs_dlnidu_p50_p90_max'][2]:.2g}")
        print(t,bud,cls,kind," | ".join(cells))
print("K10 D2P-D2 (ga) across tol (none)")
for t in ("t0p1mV","t1mV","tLOO"):
    for cls in ("S","F"):
      for kind in ("n","p"):
        cells=[]
        for i in IDS[:1]+IDS[2:3]:
          d=g(("K10","ga","D2P-D2",t,i,"none"),cls,kind)
          cells.append(f"{d['n_differ']/d['n']:.1%}/{d['abs_dlnidu_p50_p90_max'][1]:.2g}/{d['abs_dvgs_p50_p90_max'][1]:.2g}")
        print(t,cls,kind," | ".join(cells))
print("K3 na-ga across variants(D2) differ% by ID/bud")
for vt in ("D1@t1mV","D2"):
 for bud in ("none","full","share"):
  for cls in ("S","F"):
    for kind in ("n","p"):
      cells=[]
      for i in IDS:
        d=g(("K3","na-ga",vt,"-",i,bud),cls,kind)
        cells.append(f"{d['n_differ']/d['n']:.1%}/{d['abs_dlnidu_p50_p90_max'][1]:.2g}/{d['abs_dlnidu_p50_p90_max'][2]:.2g}")
      print(vt,bud,cls,kind," | ".join(cells))
