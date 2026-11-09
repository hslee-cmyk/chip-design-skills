import sys, numpy as np, json
sys.argv=[sys.argv[0]]
import measure as M
li=list(range(18)); di=[i for i in range(49) if M.VD[i]>=0.3-1e-12]
out=open("byL.jsonl","w",encoding="utf-8")
for f in (None,1e6,1e7,3e7,1e8,3e8):
  for vname,vi in (("VSB0",[0]),("VSB>0",list(range(1,10)))):
    r=M.evaluate("p",li,di,vi,f)
    for V in ("B","C"):
        x=r[V]; ne=x["nonempty"]
        for l in range(18):
            n=int(ne[l].sum()); d=x["differ"][l]; s1=(x["drel"][l]>0.01)&ne[l]
            rec=dict(kind="p",f_req=f,vsb=vname,variant=V,L_um=float(M.LG[l]*1e6),n_nonempty=n,n_differ=int(d.sum()),n_gt1pct=int(s1.sum()),
                     dvgs_max=float(np.nanmax(np.where(d,x["dvgs"][l],np.nan))) if d.any() else None,
                     drel_max=float(np.nanmax(np.where(d,x["drel"][l],np.nan))) if d.any() else None)
            out.write(json.dumps(rec)+"\n")
out.close()
rows=[json.loads(l) for l in open("byL.jsonl")]
for f in (None,1e7,1e8):
  for vn in ("VSB0","VSB>0"):
    print("f_req",f,vn,"variant C: L(um): n_gt1pct/n_nonempty")
    print("  "+"  ".join(f"{r['L_um']:.3g}:{r['n_gt1pct']}/{r['n_nonempty']}" for r in rows if r["f_req"]==f and r["vsb"]==vn and r["variant"]=="C"))
