import sys, json, collections, numpy as np
sys.argv=[sys.argv[0]]
import measure as M
rows=[json.loads(l) for l in open("devices.jsonl",encoding="utf-8")]
sf=[r for r in rows if r["cls"]!="B"]
SHORT=[i for i,L in enumerate(M.LG) if L<=0.25e-6+1e-12]
def q(a):
    a=np.asarray(a,float); a=a[np.isfinite(a)]
    if a.size==0: return "-"
    p=np.quantile(a,[0,.5,.9,1]); return "min {:.3g} / med {:.3g} / p90 {:.3g} / max {:.3g} (n={})".format(*p,a.size)
# 그룹: (kind, vsb tuple, f_req) -> 소자 수
groups=collections.defaultdict(list)
for r in sf: groups[(r["kind"],tuple(r["vsb_idx"]),r["f_req"])].append(r)
pool={V:collections.defaultdict(list) for V in "ABC"}
for (kind,vi,f),devs in groups.items():
    li=list(range(18)); di=[i for i in range(49) if M.VD[i]>=0.3-1e-12]
    res=M.evaluate(kind,li,di,list(vi),f)
    n=len(devs)
    for V in "ABC":
        x=res[V]
        for tag,sel in (("all",slice(None)),("short",SHORT),("long",[i for i in range(18) if i not in SHORT])):
            ne=x["nonempty"][sel]
            for key in ("differ","left"):
                pool[V][(kind,tag,key)].append((x[key][sel]&ne).sum()*n)
            pool[V][(kind,tag,"nonempty")].append(ne.sum()*n)
            mat=(x["drel"][sel]>0.01)&ne
            pool[V][(kind,tag,"mat1")].append(mat.sum()*n)
            for key in ("dvgs","drel","dlnidu","dg"):
                pool[V][(kind,tag,key+"_mat")].append(np.repeat(x[key][sel][mat],n))
                pool[V][(kind,tag,key+"_diff")].append(np.repeat(x[key][sel][x["differ"][sel]&ne],n))
out=[]
for V in "ABC":
    for kind in "np":
        for tag in ("all","short","long"):
            g=lambda k: pool[V][(kind,tag,k)]
            ne=sum(g("nonempty")); 
            line=f"{V} {kind} {tag}: nonempty {ne} differ {sum(g('differ'))} ({100*sum(g('differ'))/max(ne,1):.1f}%) left {sum(g('left'))} mat(>1%) {sum(g('mat1'))} ({100*sum(g('mat1'))/max(ne,1):.1f}%)"
            out.append(line)
            for key in ("dvgs","drel","dlnidu","dg"):
                arr=np.concatenate(g(key+"_mat")) if g(key+"_mat") else np.array([])
                out.append(f"     mat {key}: {q(arr)}")
            for key in ("dvgs","drel","dlnidu"):
                arr=np.concatenate(g(key+"_diff")) if g(key+"_diff") else np.array([])
                out.append(f"     diff(any) {key}: {q(arr)}")
open("report_pooled.txt","w",encoding="utf-8").write("\n".join(out))
print("\n".join(out))
