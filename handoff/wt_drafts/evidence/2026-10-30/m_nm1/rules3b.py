# 정정: DEC-95(3) 문언 순서 ① diode -> ② GB5/뒤 stage(미측정) -> 궤도 대표 -> 정준 위치(마지막 키, wl 키 없음)
import random, collections
import common
from common import *
common.ROLEMODE="family"; rng=random.Random(5)
exec(open('rules3.py',encoding='utf-8').read().split("for c in circuits():")[0].split("rng = random.Random(11)")[1].replace('RES = OUT + f"/results_rules3_{common.ROLEMODE}.jsonl"',''))
RES=OUT+"/results_rules3b_family.jsonl"
def sel(M,pos,g):
    d=[x for x in g if M.mos[x]["d"]==M.mos[x]["g"]] or g
    return min(d,key=lambda x:pos["D:"+x])
tot=totm=tots=0; circ=0
for c in circuits():
    M=load(c);G,wl,orb,pos=an(M);gs=groups(M)
    multi=same=0
    for g in gs:
        d=[x for x in g if M.mos[x]["d"]==M.mos[x]["g"]] or g
        if len(d)>1:
            if len({orb["D:"+x] for x in d})>1: multi+=1
            else: same+=1
    dep=lambda M_,p_: frozenset("D:"+x for gg in groups(M_) for x in gg if x!=sel(M_,p_,gg))
    base=dep(M,pos); meta=[]
    for _ in range(3):
        pd,pn=random_rename(M,rng);inv={v:k for k,v in pd.items()}
        M2=M.rename(pd,pn);G2,wl2,o2,p2=an(M2);d2=dep(M2,p2);back=frozenset("D:"+inv[x[2:]] for x in d2)
        meta.append(dict(pos_identical=sorted(p2[x] for x in d2)==sorted(pos[x] for x in base),automorphic=sets_equivalent(G,wl,base,back)))
    append(RES,dict(circuit=c,groups=len(gs),multi_orbit_after_diode=multi,single_orbit_after_diode=same,meta=meta))
    print(c,len(gs),multi,same,[(m['pos_identical'],m['automorphic']) for m in meta]); tot+=len(gs);totm+=multi;tots+=same;circ+=multi>0
print(tot,totm,tots,circ)
