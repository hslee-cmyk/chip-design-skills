import common,time,sys
from common import *
c=sys.argv[1]
M=load(c); G=build_graph(M)
wl=wl_refine(G,{v:G.nodes[v]["base"] for v in G}); print(len(set(wl.values())),len(G),flush=True)
t=time.time(); orb,g=orbits(G,wl); print('orb',time.time()-t,len([x for x in g if len(x)>1]),flush=True)
t=time.time(); pos,lv=canon_positions(G,wl); print('canon',time.time()-t,lv,flush=True)
