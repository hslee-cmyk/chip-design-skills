import json, collections
rows=[json.loads(l) for l in open("devices.jsonl",encoding="utf-8")]
sf=[r for r in rows if r["cls"]!="B"]
res=[]
for r in sf:
    d=dict(circuit=r["circuit"],dev=r["dev"],kind=r["kind"],cls=r["cls"],f_req=r["f_req"])
    for V in "ABC":
        pl=r["perL"][V]
        mat=[x["L_um"] for x in pl if x["n_gt1pct"]>0]
        anyd=[x["L_um"] for x in pl if x["n_differ"]>0]
        left=[x["L_um"] for x in pl if x["n_left"]>0]
        d[V]=dict(n_anchor=sum(1 for x in pl if x["n_nonempty"]>0),mat_L=mat,diff_L=anyd,left_L=left,
                  drel_max=max([x["drel_max"] or 0 for x in pl]),dvgs_max=max([x["dvgs_max"] or 0 for x in pl]),dlnidu_max=max([x["dlnidu_max"] or 0 for x in pl]),
                  dg_max=max([x["dg_max"] or 0 for x in pl]))
    res.append(d)
json.dump(res,open("device_level.json","w",encoding="utf-8"),ensure_ascii=False)
for V in "ABC":
    print(V,"devices with material(>1%) at >=1 L anchor:",sum(1 for d in res if d[V]["mat_L"]),
      " only short L(<=0.25):",sum(1 for d in res if d[V]["mat_L"] and max(d[V]["mat_L"])<=0.25+1e-9),
      " max material L histogram:",collections.Counter(max(d[V]["mat_L"]) for d in res if d[V]["mat_L"]))
    print("   strict diff any:",sum(1 for d in res if d[V]["diff_L"]),"strict left any:",sum(1 for d in res if d[V]["left_L"]),
      "by kind material:",collections.Counter(d["kind"] for d in res if d[V]["mat_L"]))
    dm=[d for d in res if d[V]["mat_L"]]
    import numpy as np
    for k in ("drel_max","dvgs_max","dlnidu_max","dg_max"):
        a=np.array([d[V][k] for d in dm]); print("   worst-case",k,np.round(np.quantile(a,[0,.5,.9,1]),4) if len(a) else None)
# per circuit
print("per circuit (N S/F devices; pfet; C material):")
c=collections.defaultdict(lambda:[0,0,0,0,0])
for d in res:
    x=c[d["circuit"]]; x[0]+=1; x[1]+= d["kind"]=="p"; x[2]+= bool(d["C"]["mat_L"]); x[3]+= bool(d["B"]["left_L"]); x[4]+= bool(d["B"]["mat_L"])
for k,v in c.items(): print(k,v)
