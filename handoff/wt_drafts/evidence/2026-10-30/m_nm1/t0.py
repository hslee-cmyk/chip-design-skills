import time,sys
import common
from common import *
for c in circuits():
    M=load(c); G=build_graph(M)
    init={v:G.nodes[v]["base"] for v in G}
    t=time.time(); wl=wl_refine(G,init); t1=time.time()-t
    t=time.time(); orb,groups=orbits(G,wl); t2=time.time()-t
    nont=[sorted(x[2:] for x in g) for g in groups if len(g)>1 and any(x.startswith("D:") for x in g)]
    t=time.time()
    try:
        pos,lv=canon_positions(G,wl); err=''
    except Exception as e:
        pos,lv,err=None,-1,str(e)
    t3=time.time()-t
    print(c,len(G),'wl',len(set(wl.values())),f'{t1:.1f}s orb {t2:.1f}s canon {t3:.1f}s leaves',lv,err)
    print('  nontriv dev orbits:',[g for g in nont if True][:12])
